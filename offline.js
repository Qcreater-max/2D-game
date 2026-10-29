/* 离线模式：在浏览器里直接运行本地游戏引擎（engine.js），不需要服务器。
   默认启用（地址带 ?online=1 时改用原来的 WebSocket 联网模式）。
   复用 client.js 采集好的全局 input、render.js 的 drawFrame，以及画布与准星。 */

(function () {
  if (new URLSearchParams(location.search).has('online')) {
    window.OFFLINE = false;
    return;                       // 联网模式：让 client.js 自己去连服务器
  }
  window.OFFLINE = true;

  const engine = new GameEngine(1);
  let level = engine.level_message();
  applyCatalog(level.catalog);          // 填充武器/盔甲/元素/图鉴，UI 和卡片要用
  let state = engine.get_state();

  const conn = document.getElementById('connStatus');
  conn.textContent = '● 本地运行（离线）';
  conn.style.color = '#ffe080';

  // 退出本局：回到主菜单，丢掉当前进度（游戏循环继续跑，只是状态回到 menu）
  window.exitGame = function () {
    engine.to_menu();
    if (window.resetInput) window.resetInput();
  };

  // ---- 菜单：直接点模式卡片 ----
  // 卡片坐标和 ui.js 的 drawMenu 保持一致（逻辑分辨率 960x540）。
  const MENU_CARDS = [[230, 236, 240, 74], [490, 236, 240, 74]];
  const menuCanvas = document.getElementById('game');

  function menuCardAt(clientX, clientY) {
    const r = menuCanvas.getBoundingClientRect();
    const x = (clientX - r.left) * (960 / r.width);
    const y = (clientY - r.top) * (540 / r.height);
    for (let i = 0; i < MENU_CARDS.length; i++) {
      const c = MENU_CARDS[i];
      if (x >= c[0] && x <= c[0] + c[2] && y >= c[1] && y <= c[1] + c[3]) return i;
    }
    return -1;
  }
  function onMenuTap(e) {
    if (engine.game.state !== 'menu') return;
    const t = e.changedTouches ? e.changedTouches[0] : e;
    const i = menuCardAt(t.clientX, t.clientY);
    if (i < 0) return;
    engine.game.menuIdx = i;
    engine.new_game(MODES[i]);
  }
  menuCanvas.addEventListener('touchstart', onMenuTap, { passive: true });
  menuCanvas.addEventListener('mousedown', onMenuTap);

  // 固定 60 帧时间步长，与服务器的逻辑帧率一致
  const STEP = 1000 / 60;
  let last = performance.now(), acc = 0;

  function loop(now) {
    acc += now - last;
    last = now;
    if (acc > 250) acc = 250;                 // 切后台回来不要疯狂补帧
    while (acc >= STEP) {
      engine.tick(input);
      if (engine.level_seq !== level.seq) level = engine.level_message();
      acc -= STEP;
    }
    state = engine.get_state();
    try {
      drawFrame(state, level);
      if (typeof drawCrosshair === 'function') drawCrosshair(state);
    } catch (err) {
      console.error(err);
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
