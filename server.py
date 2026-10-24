"""
游戏服务器
- HTTP（默认 8080）：只提供 index.html / client.js，不暴露源码和 .git
- WebSocket（默认 8081）：广播游戏状态、接收按键

游戏循环独立于连接，固定 60 帧/秒；多个浏览器同时连接时共用同一局游戏，
不会再因为连接数增加而加速。

默认只监听本机 127.0.0.1。服务没有任何认证，如需局域网联机请显式传入
--host 0.0.0.0，并确认网络可信。
"""
import argparse
import asyncio
import json
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

import websockets

from game_data import INPUT_KEYS, TICK_RATE, parse_aim
from game_engine import GameEngine

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FILES = {'/': 'index.html', '/index.html': 'index.html'}
STATIC_FILES.update({'/' + n: n for n in ('client.js', 'sprites.js', 'render.js', 'render_world.js', 'ui.js')})

engine = GameEngine()
clients = {}          # websocket -> 该连接当前的按键状态


# ============== HTTP 静态文件服务 ==============
class StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        name = STATIC_FILES.get(path.split('?', 1)[0])
        return os.path.join(ROOT, name) if name else os.path.join(ROOT, '__not_found__')

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def run_http(host, port):
    httpd = HTTPServer((host, port), StaticHandler)
    print('[HTTP] 静态文件服务已启动: http://%s:%d/' % (host, port))
    httpd.serve_forever()


# ============== WebSocket ==============
def merged_input():
    """多个连接的按键取并集。"""
    out = {k: False for k in INPUT_KEYS}
    out['aim'] = None
    for keys in clients.values():
        for k in INPUT_KEYS:
            out[k] = out[k] or keys.get(k, False)
        if keys.get('aim') is not None:      # 瞄准是坐标，没法取并集：取最后一个在瞄准的连接
            out['aim'] = keys['aim']
    return out


async def handler(websocket):
    print('[WS] 客户端已连接: %s' % (websocket.remote_address,))
    keys = {}
    clients[websocket] = keys
    try:
        await websocket.send(json.dumps(engine.level_message(), separators=(',', ':')))
        async for msg in websocket:
            try:
                data = json.loads(msg)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            if data.get('need_level'):
                await websocket.send(json.dumps(engine.level_message(), separators=(',', ':')))
                continue
            for k in INPUT_KEYS:
                if k in data:
                    keys[k] = bool(data[k])
            if 'aim' in data:
                keys['aim'] = parse_aim(data['aim']) if data['aim'] is not None else None
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.pop(websocket, None)
        print('[WS] 客户端已断开: %s' % (websocket.remote_address,))


async def game_loop():
    dt = 1.0 / TICK_RATE
    next_t = time.perf_counter()
    last_seq = engine.level_seq
    while True:
        engine.tick(merged_input())
        if clients:
            if engine.level_seq != last_seq:
                websockets.broadcast(set(clients), json.dumps(engine.level_message(), separators=(',', ':')))
            websockets.broadcast(set(clients), json.dumps(engine.get_state(), separators=(',', ':')))
        last_seq = engine.level_seq
        next_t += dt
        delay = next_t - time.perf_counter()
        if delay < -0.25:           # 机器卡顿后不要疯狂补帧
            next_t = time.perf_counter()
            delay = 0
        await asyncio.sleep(max(0.0, delay))


async def ws_main(host, port):
    async with websockets.serve(handler, host, port):
        print('[WS]   游戏 WebSocket 已启动: ws://%s:%d' % (host, port))
        await game_loop()


def main():
    ap = argparse.ArgumentParser(description='像素勇士服务器')
    ap.add_argument('--host', default='127.0.0.1', help='监听地址，默认仅本机；局域网联机用 0.0.0.0（无认证）')
    ap.add_argument('--http-port', type=int, default=8080)
    ap.add_argument('--ws-port', type=int, default=8081)
    args = ap.parse_args()

    if args.host not in ('127.0.0.1', 'localhost', '::1'):
        print('[警告] 正在监听 %s，服务没有认证，同一网络内的任何人都能连接。' % args.host)
    threading.Thread(target=run_http, args=(args.host, args.http_port), daemon=True).start()
    try:
        asyncio.run(ws_main(args.host, args.ws_port))
    except KeyboardInterrupt:
        print('\n[服务器] 已停止')


if __name__ == '__main__':
    main()
