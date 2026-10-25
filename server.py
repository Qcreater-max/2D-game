"""
游戏服务器（单端口：HTTP 静态文件 + WebSocket）

- 同一个端口（默认 8080）：普通 HTTP 请求返回 index.html / *.js，/ws 升级为 WebSocket。
  只有白名单里的文件可访问，源码和 .git 不会暴露。/healthz 用于存活检查。
- 每个 WebSocket 连接拥有独立的 GameEngine（各玩各的），游戏循环固定 60 帧/秒。
- 公开部署的保护：总人数上限、单 IP 连接上限、消息大小上限、输入限流、
  慢客户端丢帧、可选的 Origin 白名单。服务本身没有账号认证。

默认只监听 127.0.0.1。公开部署时放在 Caddy / nginx 之后（见 deploy/），
或显式传入 --host 0.0.0.0 直接对外。
"""
import argparse
import asyncio
import json
import mimetypes
import os
import time
import traceback
from http import HTTPStatus

import websockets

from game_data import INPUT_KEYS, TICK_RATE, parse_aim
from game_engine import GameEngine

ROOT = os.path.dirname(os.path.abspath(__file__))
WS_PATH = '/ws'
STATIC_FILES = {'/': 'index.html', '/index.html': 'index.html'}
STATIC_FILES.update({'/' + n: n for n in ('client.js', 'sprites.js', 'render.js', 'render_world.js', 'ui.js')})

MAX_MSG_BYTES = 1024            # 客户端消息只有按键和坐标，1KB 足够
MSG_RATE, MSG_BURST = 120.0, 60.0   # 每连接每秒最多处理 120 条消息，允许 60 条突发
SEND_BUFFER_LIMIT = 256 * 1024  # 客户端收不过来时，积压超过这个值就丢弃状态帧

# 关闭码：1013 服务器已满，1008 违反策略（单 IP 连接过多）。client.js 按这两个码调整重连间隔。
CLOSE_FULL, CLOSE_POLICY = 1013, 1008


class Settings:
    max_players = 8
    max_per_ip = 3
    trust_proxy = False


settings = Settings()
sessions = {}         # websocket -> Session


def dumps(obj):
    return json.dumps(obj, separators=(',', ':'))


# ============== 会话：一个连接 = 一局独立的游戏 ==============
class Session:
    def __init__(self, ws, ip):
        self.ws, self.ip = ws, ip
        self.engine = GameEngine()
        self.keys = {k: False for k in INPUT_KEYS}
        self.keys['aim'] = None
        self.last_seq = None          # 已发给该客户端的关卡序号；None 表示还没发过
        self.want_level = False
        self.tokens, self.stamp = MSG_BURST, time.monotonic()

    def allow(self, now):
        """令牌桶限流：超出速率的消息直接丢弃。"""
        self.tokens = min(MSG_BURST, self.tokens + (now - self.stamp) * MSG_RATE)
        self.stamp = now
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True

    def handle(self, raw, now=None):
        """处理一条客户端消息，更新按键状态。非法内容一律忽略。"""
        if not self.allow(time.monotonic() if now is None else now):
            return
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError):
            return
        if not isinstance(data, dict):
            return
        if data.get('need_level'):
            self.want_level = True
            return
        for k in INPUT_KEYS:
            if k in data:
                self.keys[k] = bool(data[k])
        if 'aim' in data:
            self.keys['aim'] = parse_aim(data['aim']) if data['aim'] is not None else None


def client_ip(ws):
    if settings.trust_proxy:
        fwd = ws.request_headers.get('X-Forwarded-For')
        if fwd:
            return fwd.split(',')[-1].strip()    # 反向代理追加的是最后一项，前面的可被客户端伪造
    addr = ws.remote_address
    return addr[0] if addr else '?'


# ============== HTTP 静态文件（挂在 WebSocket 同一端口上） ==============
async def process_request(path, request_headers):
    route = path.split('?', 1)[0]
    if route == WS_PATH:
        return None                                  # 交给 WebSocket 握手
    if route == '/healthz':
        return HTTPStatus.OK, [('Content-Type', 'text/plain')], b'ok\n'
    name = STATIC_FILES.get(route)
    if name is None:
        return HTTPStatus.NOT_FOUND, [('Content-Type', 'text/plain')], b'not found\n'
    try:
        with open(os.path.join(ROOT, name), 'rb') as f:
            body = f.read()
    except OSError:
        return HTTPStatus.NOT_FOUND, [('Content-Type', 'text/plain')], b'not found\n'
    ctype = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    return HTTPStatus.OK, [
        ('Content-Type', ctype + '; charset=utf-8'),
        ('Cache-Control', 'no-store'),
        ('X-Content-Type-Options', 'nosniff'),
    ], body


# ============== WebSocket ==============
async def handler(websocket):
    ip = client_ip(websocket)
    if len(sessions) >= settings.max_players:
        await websocket.close(CLOSE_FULL, 'server full')
        return
    if sum(1 for s in sessions.values() if s.ip == ip) >= settings.max_per_ip:
        await websocket.close(CLOSE_POLICY, 'too many connections')
        return
    session = Session(websocket, ip)
    sessions[websocket] = session
    print('[WS] 已连接 %s（在线 %d）' % (ip, len(sessions)))
    try:
        async for msg in websocket:
            session.handle(msg)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        sessions.pop(websocket, None)
        print('[WS] 已断开 %s（在线 %d）' % (ip, len(sessions)))


def push(ws, text, droppable=True):
    """非阻塞发送。客户端接收太慢时丢弃状态帧，避免服务器内存被积压的数据撑大。"""
    transport = ws.transport
    if transport is None:
        return
    if droppable and transport.get_write_buffer_size() > SEND_BUFFER_LIMIT:
        return
    websockets.broadcast([ws], text)


def step_session(s):
    s.engine.tick(s.keys)
    if s.last_seq != s.engine.level_seq or s.want_level:
        push(s.ws, dumps(s.engine.level_message()), droppable=False)
        s.last_seq, s.want_level = s.engine.level_seq, False
    push(s.ws, dumps(s.engine.get_state()))


async def game_loop():
    dt = 1.0 / TICK_RATE
    next_t = time.perf_counter()
    while True:
        for s in list(sessions.values()):
            try:
                step_session(s)
            except Exception:
                # 一个玩家的引擎出错，不能拖垮其他人：记录后断开这个连接
                traceback.print_exc()
                sessions.pop(s.ws, None)
                asyncio.ensure_future(s.ws.close(1011, 'internal error'))
        next_t += dt
        delay = next_t - time.perf_counter()
        if delay < -0.25:           # 机器卡顿后不要疯狂补帧
            next_t = time.perf_counter()
            delay = 0
        await asyncio.sleep(max(0.0, delay))


async def serve(host, port, origins):
    async with websockets.serve(
            handler, host, port, process_request=process_request,
            max_size=MAX_MSG_BYTES, ping_interval=20, ping_timeout=20, origins=origins):
        print('[服务器] http://%s:%d/  （WebSocket: %s）' % (host, port, WS_PATH))
        await game_loop()


def main():
    ap = argparse.ArgumentParser(description='像素勇士服务器')
    ap.add_argument('--host', default='127.0.0.1', help='监听地址，默认仅本机；直接对外用 0.0.0.0')
    ap.add_argument('--port', type=int, default=8080, help='HTTP 和 WebSocket 共用的端口')
    ap.add_argument('--max-players', type=int, default=Settings.max_players, help='同时在线人数上限')
    ap.add_argument('--max-per-ip', type=int, default=Settings.max_per_ip, help='单个 IP 的连接数上限')
    ap.add_argument('--trust-proxy', action='store_true',
                    help='位于单层反向代理之后时使用，按 X-Forwarded-For 最后一项识别客户端 IP')
    ap.add_argument('--allowed-origin', action='append', metavar='ORIGIN',
                    help='允许发起 WebSocket 的页面来源，如 https://game.example.com，可重复；默认不检查')
    args = ap.parse_args()

    settings.max_players, settings.max_per_ip = args.max_players, args.max_per_ip
    settings.trust_proxy = args.trust_proxy
    if args.host not in ('127.0.0.1', 'localhost', '::1'):
        print('[警告] 正在监听 %s，服务没有认证，网络内的任何人都能连接。公开部署建议放在 HTTPS 反向代理之后。'
              % args.host)
    try:
        asyncio.run(serve(args.host, args.port, args.allowed_origin))
    except KeyboardInterrupt:
        print('\n[服务器] 已停止')


if __name__ == '__main__':
    main()
