/* ============================================================
 * 客户端：采集按键 → 发给服务器 → 接收状态 → 绘制
 * 游戏规则全部在 Python 后端（game_engine.py），这里只负责输入和显示。
 *
 * 按键（每个功能只绑定一类键，互不冲突）：
 *   移动 A/D 或 ←/→      跳跃 W/↑/空格      下穿平台 S/↓ + 跳跃
 *   攻击 J 或鼠标左键     互动 E（宝箱 / 铁匠 / 传送门）
 *   背包 I      战绩 Tab/C      返回/关闭 Esc
 *   菜单与面板中：↑↓ 选择，←→ 切页，Enter/空格/J 确认
 * ============================================================ */

// W/H、WEAK_MULT/RESIST_MULT、WEAPONS、ARMORS、ELEMENTS 已由 engine_data.js 用 const 声明。
// 所有 <script> 共用同一个全局词法作用域，这里再声明一次会直接抛
// "Identifier 'W' has already been declared"，导致整个 client.js 不执行、页面一直停在"连接中"。
const ENEMY_INFO = {};   // 怪物图鉴：只有客户端需要，由下发的 catalog 填充
function applyCatalog(c) {
  if (!c) return;
  // catalog 里的武器/盔甲数组是副本；离线模式下 elements 就是 ELEMENTS 本身，
  // 不能"先清空再赋值"，否则会把数据源一起清掉。
  WEAPONS.length = 0; WEAPONS.push(...c.weapons);
  ARMORS.length = 0; ARMORS.push(...c.armors);
  if (c.elements !== ELEMENTS) {
    Object.keys(ELEMENTS).forEach(k => delete ELEMENTS[k]);
    Object.assign(ELEMENTS, c.elements);
  }
  Object.keys(ENEMY_INFO).forEach(k => delete ENEMY_INFO[k]); Object.assign(ENEMY_INFO, c.enemies);
}

// ---- 输入 ----
const KEYS = ['left', 'right', 'up', 'down', 'jump', 'attack', 'interact', 'confirm', 'inv', 'stats', 'escape'];
const input = {};
KEYS.forEach(k => input[k] = false);

// 键盘 code → 触发的逻辑按键
const KEYMAP = {
  KeyA: ['left'], ArrowLeft: ['left'],
  KeyD: ['right'], ArrowRight: ['right'],
  KeyW: ['up', 'jump'], ArrowUp: ['up', 'jump'],
  KeyS: ['down'], ArrowDown: ['down'],
  Space: ['jump', 'confirm'],
  Enter: ['confirm'], NumpadEnter: ['confirm'],
  KeyJ: ['attack'],
  KeyE: ['interact'],
  KeyI: ['inv'],
  Tab: ['stats'], KeyC: ['stats'],
  Escape: ['escape'],
};
const heldCodes = new Set();

function recompute() {
  KEYS.forEach(k => input[k] = false);
  heldCodes.forEach(c => (KEYMAP[c] || []).forEach(k => input[k] = true));
  touchHeld.forEach(k => input[k] = true);
  if (mouseAttack) input.attack = true;
  sendInput();
}
input.aim = null;     // 鼠标瞄准位置 [x, y]，不瞄准时为 null

window.addEventListener('keydown', e => {
  if (!KEYMAP[e.code]) return;
  e.preventDefault();
  if (e.repeat) return;
  heldCodes.add(e.code);
  recompute();
});
window.addEventListener('keyup', e => {
  if (!KEYMAP[e.code]) return;
  e.preventDefault();
  heldCodes.delete(e.code);
  recompute();
});
window.addEventListener('blur', () => { heldCodes.clear(); touchHeld.clear(); mouseAttack = false; input.aim = null; recompute(); });

// 鼠标左键攻击（只响应画布，避免点触屏按钮时误触）。
// 按住期间持续上报鼠标在画面里的位置，服务端据此决定远程武器的发射方向；
// 画布被 CSS 缩放过，所以要按显示尺寸换算回 960x540 的游戏坐标。
let mouseAttack = false;
let mouse = null;         // 鼠标当前的游戏坐标 {x, y}，用来画准星
const gameCanvas = document.getElementById('game');

function mousePos(e) {
  const r = gameCanvas.getBoundingClientRect();
  return { x: (e.clientX - r.left) * (W / r.width), y: (e.clientY - r.top) * (H / r.height) };
}
function sendAim() {
  // 只在按住左键时才瞄准；松开后发送 null，让角色回到"按朝向发射"
  input.aim = mouseAttack && mouse ? [Math.round(mouse.x), Math.round(mouse.y)] : null;
  sendInput();
}
gameCanvas.addEventListener('mousedown', e => {
  if (e.button !== 0) return;
  mouse = mousePos(e); mouseAttack = true; recompute(); sendAim();
});
window.addEventListener('mousemove', e => {
  mouse = mousePos(e);
  if (mouseAttack && performance.now() - lastAimSend > 30) { lastAimSend = performance.now(); sendAim(); }
});
let lastAimSend = 0;
window.addEventListener('mouseup', e => {
  if (e.button === 0 && mouseAttack) { mouseAttack = false; recompute(); sendAim(); }
});
gameCanvas.addEventListener('contextmenu', e => e.preventDefault());

// 触屏按钮
// 有些安卓浏览器会谎报 (hover: none)/(pointer: coarse)，所以再用 JS 兜一层：
// 只要设备有触摸能力就显示虚拟按键、隐藏键盘提示文字。
window.IS_TOUCH = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
if (window.IS_TOUCH) document.body.classList.add('touch');
const touchHeld = new Set();
function bindBtn(id, ...keys) {
  const el = document.getElementById(id);
  if (!el) return;
  const on = e => { e.preventDefault(); keys.forEach(k => touchHeld.add(k)); recompute(); };
  const off = e => { e.preventDefault(); keys.forEach(k => touchHeld.delete(k)); recompute(); };
  ['touchstart', 'mousedown'].forEach(t => el.addEventListener(t, on, { passive: false }));
  ['touchend', 'touchcancel', 'mouseup', 'mouseleave'].forEach(t => el.addEventListener(t, off, { passive: false }));
}
bindBtn('dp-left', 'left'); bindBtn('dp-right', 'right');
bindBtn('dp-up', 'up'); bindBtn('dp-down', 'down');
bindBtn('bt-jump', 'jump', 'confirm'); bindBtn('bt-atk', 'attack');
bindBtn('bt-act', 'interact'); bindBtn('bt-inv', 'inv'); bindBtn('bt-stats', 'stats');

// ---- WebSocket ----
let ws = null;
let state = null;        // 最新动态状态
let level = null;        // 当前关卡的静态数据（平台、传送门、铁匠铺）
const connStatus = document.getElementById('connStatus');

function sendInput() {
  if (window.OFFLINE) return;               // 离线模式：本地引擎直接读取 input，不需要发送
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(input));
}

function connect() {
  // WebSocket 与页面同源同端口，路径 /ws；经 HTTPS 反向代理访问时自动使用 wss
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
  ws.onopen = () => {
    connStatus.textContent = '● 已连接';
    connStatus.style.color = '#80ff80';
    sendInput();
  };
  ws.onmessage = ev => {
    let m;
    try { m = JSON.parse(ev.data); } catch (_) { return; }
    if (m.t === 'level') { applyCatalog(m.catalog); level = m; resetFx(); }
    else if (m.t === 'state') {
      if (!level || level.seq !== m.seq) { ws.send(JSON.stringify({ need_level: true })); return; }
      state = m;
    }
  };
  ws.onclose = ev => {
    state = null;
    connStatus.style.color = '#ff8080';
    // 1013 = 服务器已满，1008 = 同一网络连接过多：放慢重连，别反复冲击服务器
    let delay = 1500;
    if (ev.code === 1013) { connStatus.textContent = '● 服务器已满，稍后自动重试...'; delay = 10000; }
    else if (ev.code === 1008) { connStatus.textContent = '● 当前网络连接数过多，稍后重试...'; delay = 10000; }
    else connStatus.textContent = '● 已断开，重连中...';
    setTimeout(connect, delay);
  };
}
// 默认离线运行（与 offline.js 的判定一致）：只有显式 ?online=1 才连服务器。
// 之前用 !window.OFFLINE 判断是无效的——offline.js 在 client.js 之后才加载。
if (new URLSearchParams(location.search).has('online')) connect();

// ---- 主循环 ----
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
ctx.imageSmoothingEnabled = false;

function fitCanvas() {
  // 手机浏览器地址栏收起/展开时 innerHeight 不可靠，优先用 visualViewport
  const vv = window.visualViewport;
  const vw = vv ? vv.width : window.innerWidth;
  const vh = vv ? vv.height : window.innerHeight;
  const s = Math.min(vw / W, vh / H);
  canvas.style.width = Math.floor(W * s) + 'px';
  canvas.style.height = Math.floor(H * s) + 'px';
}
window.addEventListener('resize', fitCanvas);
window.addEventListener('orientationchange', fitCanvas);
if (window.visualViewport) window.visualViewport.addEventListener('resize', fitCanvas);
fitCanvas();

function frame() {
  if (window.OFFLINE) return;               // 离线模式：由 offline.js 用自己的循环绘制
  try {
    if (state && level) { drawFrame(state, level); drawCrosshair(state); }
    else drawConnecting();
  } catch (err) {
    // 绘制出错时不要让循环停掉，并把错误显示出来方便排查
    console.error(err);
    ctx.restore();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = 'rgba(0,0,0,0.85)'; ctx.fillRect(0, 0, W, 60);
    ctx.fillStyle = '#ff6060'; ctx.font = '13px monospace'; ctx.textAlign = 'left';
    ctx.fillText('渲染错误: ' + (err && err.stack ? err.stack.split('\n').slice(0, 2).join(' | ') : err), 10, 24);
  }
  requestAnimationFrame(frame);
}
frame();
