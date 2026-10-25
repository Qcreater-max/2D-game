/* 世界渲染：背景、地形、实体、特效 */

const THEMES = {
  forest: { deco: 'forest', sky: ['#6ec6f0', '#bfe8ff', '#e8f6d0'], far: '#7ab070', mid: '#4a8a48', near: '#2f6a34', layer: 'tree',
            top: '#5cb040', topHi: '#86d060', dirt: '#6a4426', dirtDk: '#4a2e18', plat: '#8a6030', platHi: '#b88848' },
  swamp:  { deco: 'swamp', sky: ['#3a5a48', '#6a8a6a', '#a0b488'], far: '#3a5a46', mid: '#2c4a3a', near: '#1e3a2e', layer: 'tree',
            top: '#5a7a38', topHi: '#7a9a4a', dirt: '#4a3a24', dirtDk: '#33291a', plat: '#6a5a34', platHi: '#8a7a48' },
  crypt:  { deco: 'crypt', sky: ['#0c0820', '#1c1236', '#33204e'], far: '#2a1f48', mid: '#1c1434', near: '#120c24', layer: 'pillar',
            top: '#6a6090', topHi: '#8a80b0', dirt: '#3a3058', dirtDk: '#262040', plat: '#5a5080', platHi: '#8078a8' },
  lava:   { deco: 'lava', sky: ['#2a0a06', '#5a1a0a', '#8a3410'], far: '#4a1608', mid: '#3a1006', near: '#2a0a04', layer: 'pillar',
            top: '#8a5a3a', topHi: '#b0804a', dirt: '#4a2a1c', dirtDk: '#321a10', plat: '#7a4a30', platHi: '#a87048' },
  fortress: { deco: 'fortress', sky: ['#10101c', '#22223a', '#3a3a58'], far: '#26263c', mid: '#1a1a2c', near: '#10101c', layer: 'pillar',
            top: '#7a7a9a', topHi: '#9a9ac0', dirt: '#3c3c58', dirtDk: '#282840', plat: '#60608a', platHi: '#8888b0' },
  boss:   { deco: 'boss', sky: ['#12020a', '#2a0614', '#4a1020'], far: '#3a0c1c', mid: '#280814', near: '#1a040c', layer: 'pillar',
            top: '#6a3050', topHi: '#904868', dirt: '#3a1830', dirtDk: '#280e20', plat: '#6a3a5a', platHi: '#9a5a80' },
  cave:   { deco: 'cave', sky: ['#0a0a10', '#14141c', '#1c1c28'], far: '#1c1c2a', mid: '#14141f', near: '#0e0e16', layer: 'stalag',
            top: '#6a6048', topHi: '#8a7e5c', dirt: '#3a3426', dirtDk: '#262218', plat: '#5a5038', platHi: '#7a6e4c' },
  secret: { deco: 'secret', sky: ['#1a1030', '#2a1a48', '#3c2660'], far: '#2a1c48', mid: '#20143a', near: '#160e2a', layer: 'pillar',
            top: '#a08a4a', topHi: '#d8c070', dirt: '#4a3a5c', dirtDk: '#32283f', plat: '#8a7240', platHi: '#c0a860' },
  arena:  { deco: 'arena', sky: ['#1a0e14', '#3a1620', '#5a2430'], far: '#40181e', mid: '#2e1016', near: '#1e0a0e', layer: 'pillar',
            top: '#8a7058', topHi: '#b09474', dirt: '#4a3828', dirtDk: '#322418', plat: '#7a6048', platHi: '#a08868' },
};

const fx = { trail: [], shotTrail: new Map(), lastTime: -1 };
function resetFx() { fx.trail = []; fx.shotTrail.clear(); }

// 刀光拖尾：每个新逻辑帧记录武器尖端位置，最多保留 9 个点，随时间渐隐
function pushTrail(tip) {
  fx.trail.push(tip);
  if (fx.trail.length > 9) fx.trail.shift();
}

function theme(g) { return THEMES[g.theme] || THEMES.forest; }

function drawFrame(s, lv) {
  const g = s.game, t = theme(g);
  ctx.save();
  ctx.clearRect(0, 0, W, H);
  drawBackground(g, t);
  const sh = g.shake;
  const ox = sh ? (Math.random() - 0.5) * sh : 0, oy = sh ? (Math.random() - 0.5) * sh : 0;
  ctx.translate(Math.round(-g.camX + ox), Math.round(oy));

  drawTerrain(lv.platforms, g, t);
  drawMovers(s.movers || [], g, t);
  drawHazards(lv.hazards || [], g);
  drawHoles(s.holes || [], g);
  drawSecrets(s.secrets || [], g);
  drawBackLadder(lv.backX, g);
  drawSmith(lv.smithX, g);
  drawPortal(lv.portal, g, s.game.enemiesLeft === 0);
  drawCrates(s.crates || []);
  drawChests(s.chests);
  drawCoins(s.coins);
  drawEnemies(s.enemies, g);
  drawPlayer(s.player, g);
  drawSwordTrail(s.player, g);
  drawShots(s.projectiles, s.enemyProj, g);
  drawParticles(s.particles);
  drawFxList(s.fx || []);
  drawFloatTexts(s.texts);
  if (s.prompt) drawPrompt(s.prompt);
  ctx.restore();

  // 受击时整屏泛红，暴击/爆炸时的冲击感由服务端的 shake + hitstop 提供
  if (g.hurtFlash > 0) { ctx.fillStyle = 'rgba(255,40,40,' + (g.hurtFlash / 8 * 0.28) + ')'; ctx.fillRect(0, 0, W, H); }
  drawUI(s, lv);
}

function drawConnecting() {
  ctx.fillStyle = '#07070c'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#80c0ff'; ctx.font = '18px monospace'; ctx.textAlign = 'center';
  ctx.fillText('正在连接游戏服务器…', W / 2, H / 2);
  ctx.textAlign = 'left';
}

// ---------- 背景（三层视差）----------
function drawBackground(g, t) {
  const grd = ctx.createLinearGradient(0, 0, 0, H);
  grd.addColorStop(0, t.sky[0]); grd.addColorStop(0.55, t.sky[1]); grd.addColorStop(1, t.sky[2]);
  ctx.fillStyle = grd; ctx.fillRect(0, 0, W, H);
  const cam = g.camX, tm = g.time;

  if (t.deco === 'forest') {
    ctx.fillStyle = '#fff6b0'; ctx.beginPath(); ctx.arc(820, 90, 34, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,246,176,0.25)'; ctx.beginPath(); ctx.arc(820, 90, 54, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    for (let i = 0; i < 6; i++) {
      const cx = ((i * 260 - cam * 0.1 + tm * 0.15) % (W + 260) + W + 260) % (W + 260) - 130;
      pixelCloud(cx, 60 + (i % 3) * 36);
    }
  } else if (t.deco === 'crypt' || t.deco === 'fortress') {
    for (let i = 0; i < 50; i++) {
      const x = (i * 97 - cam * 0.04 + W * 4) % W, y = (i * 53) % 260;
      ctx.globalAlpha = 0.35 + 0.65 * Math.abs(Math.sin(tm * 0.03 + i));
      ctx.fillStyle = '#fff'; ctx.fillRect(Math.round(x), y, 2, 2);
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#d8d8f0'; ctx.beginPath(); ctx.arc(780, 84, 30, 0, 7); ctx.fill();
    ctx.fillStyle = '#1c1236'; ctx.beginPath(); ctx.arc(794, 76, 27, 0, 7); ctx.fill();
  } else {
    for (let i = 0; i < 5; i++) {
      const nx = (i * 220 + Math.sin(tm * 0.01 + i) * 40) % W, ny = 70 + (i % 3) * 70;
      const ng = ctx.createRadialGradient(nx, ny, 0, nx, ny, 110);
      ng.addColorStop(0, 'rgba(180,30,70,0.35)'); ng.addColorStop(1, 'rgba(180,30,70,0)');
      ctx.fillStyle = ng; ctx.fillRect(nx - 110, ny - 110, 220, 220);
    }
  }

  layer(cam * 0.2, 240, 280, t.far, 'hill');
  layer(cam * 0.4, 170, 340, t.mid, t.layer);
  layer(cam * 0.65, 120, 400, t.near, t.layer);
  drawThemeAtmosphere(g, t);
}

function layer(off, step, base, color, kind) {
  ctx.fillStyle = color;
  const start = Math.floor(off / step) - 1;
  for (let i = start; i < start + W / step + 3; i++) {
    const x = Math.round(i * step - off), v = ((i * 2654435761) >>> 0) % 100 / 100;
    if (kind === 'hill') {
      ctx.beginPath(); ctx.moveTo(x - step * 0.2, base + 140);
      ctx.lineTo(x + step * 0.5, base - 40 - v * 60); ctx.lineTo(x + step * 1.2, base + 140); ctx.fill();
    } else if (kind === 'tree') {
      const h = 90 + v * 70;
      ctx.fillRect(x + 20, base + 140 - h, 14, h);
      ctx.beginPath(); ctx.moveTo(x - 10, base + 140 - h + 30); ctx.lineTo(x + 27, base + 140 - h - 50);
      ctx.lineTo(x + 64, base + 140 - h + 30); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x - 4, base + 140 - h + 62); ctx.lineTo(x + 27, base + 140 - h - 14);
      ctx.lineTo(x + 58, base + 140 - h + 62); ctx.fill();
    } else if (kind === 'stalag') {
      const h = 60 + v * 90;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 36, 0); ctx.lineTo(x + 18, h * 0.9); ctx.fill();       // 垂下的钟乳石
      ctx.beginPath(); ctx.moveTo(x + 10, base + 140); ctx.lineTo(x + 30, base + 140 - h * 0.7); ctx.lineTo(x + 50, base + 140); ctx.fill();
    } else {
      const h = 120 + v * 90;
      ctx.fillRect(x + 10, base + 140 - h, 30, h); ctx.fillRect(x + 4, base + 140 - h, 42, 8);
    }
  }
}

function pixelCloud(x, y) {
  ctx.fillRect(x - 30, y, 60, 14); ctx.fillRect(x - 18, y - 10, 36, 12); ctx.fillRect(x - 6, y - 18, 22, 10);
}

// ---------- 地形 ----------
function drawTerrain(platforms, g, t) {
  for (const p of platforms) {
    if (p.x + p.w < g.camX - 20 || p.x > g.camX + W + 20) continue;
    if (p.type === 'ground') {
      ctx.fillStyle = t.dirt; ctx.fillRect(p.x, p.y, p.w, H - p.y + 10);
      ctx.fillStyle = t.dirtDk;
      for (let bx = Math.floor(p.x / 32) * 32; bx < p.x + p.w; bx += 32) {
        for (let by = p.y + 10, r = 0; by < H; by += 16, r++) {
          const x0 = bx + (r % 2 ? 16 : 0);
          ctx.fillRect(Math.max(p.x, x0), by + 14, Math.min(32, p.x + p.w - x0), 2);
          if (x0 >= p.x && x0 < p.x + p.w) ctx.fillRect(x0, by, 2, 14);
        }
      }
      ctx.fillStyle = t.top; ctx.fillRect(p.x, p.y, p.w, 10);
      ctx.fillStyle = t.topHi; ctx.fillRect(p.x, p.y, p.w, 3);
      for (let x = p.x; x < p.x + p.w; x += 12) ctx.fillRect(x + (x * 7 % 5), p.y + 10, 3, 4 + (x * 13 % 4));
      // 边缘阴影，让深坑边界一目了然
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(p.x, p.y + 10, 4, H); ctx.fillRect(p.x + p.w - 4, p.y + 10, 4, H);
    } else {
      ctx.fillStyle = t.plat; ctx.fillRect(p.x, p.y, p.w, p.h);
      ctx.fillStyle = t.platHi; ctx.fillRect(p.x, p.y, p.w, 4);
      ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(p.x, p.y + p.h - 3, p.w, 3);
      for (let x = p.x + 20; x < p.x + p.w - 4; x += 20) ctx.fillRect(x, p.y + 4, 2, p.h - 7);
    }
  }
  // 深坑底部：幽暗的光
}

// ---------- 铁匠铺 ----------
// 静态部分（石基、木墙、屋顶、招牌、铁砧）只画一次缓存起来；炉火、烟、火星每帧叠加。
// 缓存坐标：x 相对铁匠铺中心，y 沿用游戏里的绝对值（缓存顶部 = 330）。
let smithCache = null;
function smithStatic() {
  if (smithCache) return smithCache;
  const cv = document.createElement('canvas');
  cv.width = 160; cv.height = 160;
  const c = cv.getContext('2d');
  c.imageSmoothingEnabled = false;
  c.translate(80, -330);
  const R = (col, x, y, w, h) => { c.fillStyle = col; c.fillRect(x, y, w, h); };

  R('rgba(0,0,0,0.22)', -52, 480, 104, 3);                       // 地面投影

  // 烟囱：先画，屋顶会盖住它的下半截
  R('#6a6a78', 16, 336, 12, 46); R('#85859a', 16, 336, 3, 46);
  for (let y = 344; y < 376; y += 8) R('#55556a', 16, y, 12, 1);
  R('#4a4a58', 14, 332, 16, 5); R('#2a2a34', 17, 333, 10, 2);

  // 石基
  R('#6a6a78', -40, 464, 80, 16); R('#85859a', -40, 464, 80, 2); R('#55556a', -40, 471, 80, 1);
  for (let r = 0; r < 2; r++) for (let bx = -40 + (r ? 8 : 0); bx < 40; bx += 16) R('#55556a', bx, 464 + r * 8, 1, 8);

  // 木墙 + 立柱 + 底梁
  R('#7a5230', -36, 396, 72, 68);
  for (let bx = -36; bx < 36; bx += 8) { R('#5a3a20', bx, 396, 1, 68); R('#8c623a', bx + 1, 396, 1, 68); }
  R('#3a2412', -38, 394, 6, 70); R('#3a2412', 32, 394, 6, 70); R('#3a2412', -38, 460, 76, 4);

  // 屋顶：一排排阶梯状瓦片，左边受光、右边背光
  for (let i = 0; i < 14; i++) {
    const y = 344 + i * 4, half = Math.round(6 + i * 3.1);
    R(i % 2 ? '#922a24' : '#a8322a', -half, y, half * 2, 4);
    R('#6e1e1a', -half, y + 3, half * 2, 1);
    for (let sx = -half + 5 + (i % 2) * 5; sx < half - 3; sx += 10) R('#6e1e1a', sx, y, 1, 3);
    R('#d05a48', -half, y, 2, 3); R('#5a1614', half - 2, y, 2, 4);
  }
  R('#6a1c18', -7, 341, 14, 4); R('#4a1010', -48, 396, 96, 4);   // 屋脊、檐口
  R('rgba(0,0,0,0.3)', -36, 400, 72, 4);                          // 屋檐投在墙上的阴影

  // 门洞（炉火的光从里面透出来，动态部分负责画）
  R('#1a0e06', -10, 424, 20, 40); R('#3a2412', -12, 422, 24, 3);
  R('#3a2412', -12, 422, 3, 42); R('#3a2412', 9, 422, 3, 42);

  // 窗：木框 + 十字窗棂
  R('#3a2412', -32, 430, 14, 14); R('#ffcf70', -30, 432, 10, 10);
  R('#3a2412', -26, 432, 2, 10); R('#3a2412', -30, 436, 10, 2);

  // 招牌：铁链吊着的木牌，字用 canvas 文字画一次
  R('#2a2a34', -26, 396, 1, 6); R('#2a2a34', 25, 396, 1, 6);
  R('#3a2412', -30, 402, 60, 16); R('#a06a34', -28, 404, 56, 12); R('#c48848', -28, 404, 56, 2);
  c.fillStyle = '#2a1608'; c.font = 'bold 11px monospace'; c.textAlign = 'center';
  c.fillText('铁匠铺', 0, 415);
  c.textAlign = 'left';

  // 门外右侧：铁砧 + 树墩，铁砧上放一把锤子
  R('#6a4a2a', 40, 462, 14, 18); R('#85603a', 40, 462, 14, 3); R('#4a3018', 40, 477, 14, 3);
  R('#2e2e3a', 38, 452, 24, 6); R('#4a4a5a', 38, 452, 24, 2); R('#2e2e3a', 42, 458, 14, 4);
  R('#2e2e3a', 33, 452, 6, 3);
  R('#8a5a2a', 48, 444, 2, 8); R('#6a6a78', 45, 441, 8, 4);

  // 门外左侧：水桶和一堆刀剑
  R('#4a3018', -62, 466, 12, 14); R('#6a4a2a', -62, 466, 12, 2); R('#2a5a8a', -61, 468, 10, 3);
  R('#2a1608', -62, 471, 12, 1); R('#2a1608', -62, 476, 12, 1);
  R('#b0b0c0', -48, 448, 2, 32); R('#d8d8e8', -48, 448, 1, 30); R('#5a3a20', -50, 468, 6, 2);
  R('#b0b0c0', -44, 452, 2, 28); R('#5a3a20', -46, 468, 6, 2);

  smithCache = cv;
  return cv;
}

function drawSmith(x, g) {
  if (x == null) return;
  const t = g.time;
  const cx = Math.round(x);
  const R = (col, rx, ry, w, h) => { ctx.fillStyle = col; ctx.fillRect(cx + rx, ry, w, h); };

  // 炉火的暖光
  const pulse = 0.5 + 0.5 * Math.sin(t * 0.18);
  const glow = ctx.createRadialGradient(cx, 446, 4, cx, 446, 74);
  glow.addColorStop(0, `rgba(255,150,40,${0.26 + pulse * 0.1})`);
  glow.addColorStop(1, 'rgba(255,120,30,0)');
  ctx.fillStyle = glow; ctx.fillRect(cx - 80, 380, 160, 130);

  ctx.drawImage(smithStatic(), cx - 80, 330);

  // 门里的炉火：三层火苗随时间摆动
  const f = (t >> 2) % 3, f2 = ((t >> 3) + 1) % 3;
  R('#5a1c08', -8, 452, 16, 12);
  R(['#ff8020', '#ffb030', '#ff6010'][f], -7, 446 - f * 2, 5, 18 + f * 2);
  R(['#ffb030', '#ff6010', '#ff8020'][f2], 0, 444 - f2 * 2, 6, 20 + f2 * 2);
  R('#ffe890', -3, 454, 5, 8 + (f ^ f2));
  R('rgba(255,170,60,0.55)', -10, 424, 20, 2);        // 门楣下被映红

  // 窗里的光轻微闪烁
  R(`rgba(255,200,100,${0.25 + pulse * 0.2})`, -30, 432, 10, 10);

  // 烟囱冒烟：几团灰烟慢慢上升、变大、变淡
  for (let i = 0; i < 4; i++) {
    const age = ((t * 0.5 + i * 24) % 96) / 96;
    const sx = cx + 22 + Math.sin(age * 5 + i) * 5 + age * 10;
    const sy = 330 - age * 56, r = 3 + age * 7;
    ctx.fillStyle = `rgba(190,190,205,${0.42 * (1 - age)})`;
    ctx.beginPath(); ctx.arc(sx, sy, r, 0, 7); ctx.fill();
  }

  // 偶尔迸出的火星
  for (let i = 0; i < 3; i++) {
    const age = ((t * 0.9 + i * 31) % 50) / 50;
    const sx = cx + (i - 1) * 6 + Math.sin(i * 4 + age * 6) * 4;
    const sy = 440 - age * 36 + age * age * 14;
    ctx.fillStyle = `rgba(255,${190 - i * 30},70,${1 - age})`;
    ctx.fillRect(Math.round(sx), Math.round(sy), 2, 2);
  }
}

function drawPortal(pt, g, open) {
  if (!pt) return;
  const cx = pt.x + pt.w / 2, cy = pt.y + pt.h / 2, tm = g.time * 0.08;
  const col = open ? '120,200,255' : '150,100,200';
  for (let i = 3; i >= 0; i--) {
    ctx.fillStyle = `rgba(${col},${(open ? 0.16 : 0.08) - i * 0.03})`;
    ctx.beginPath(); ctx.ellipse(cx, cy, pt.w / 2 + 6 + i * 7, pt.h / 2 + 6 + i * 9, 0, 0, 7); ctx.fill();
  }
  ctx.fillStyle = '#3a2a5a'; ctx.fillRect(pt.x - 6, pt.y - 6, pt.w + 12, pt.h + 6);
  ctx.fillStyle = '#5a4a8a'; ctx.fillRect(pt.x - 6, pt.y - 6, pt.w + 12, 4);
  const grd = ctx.createLinearGradient(0, pt.y, 0, pt.y + pt.h);
  grd.addColorStop(0, open ? '#60d0ff' : '#7050a0'); grd.addColorStop(1, open ? '#2060c0' : '#382060');
  ctx.fillStyle = grd; ctx.fillRect(pt.x, pt.y, pt.w, pt.h);
  ctx.fillStyle = open ? 'rgba(255,255,255,0.55)' : 'rgba(200,170,255,0.35)';
  for (let i = 0; i < 5; i++) ctx.fillRect(pt.x + 4 + ((i * 11 + g.time) % (pt.w - 8)), pt.y + ((i * 23 + g.time * 1.5) % pt.h), 3, 8);
  ctx.fillStyle = open ? '#fff' : '#cbb'; ctx.beginPath();
  ctx.arc(cx, cy + Math.sin(tm) * 8, 5 + Math.sin(tm * 2) * 1.5, 0, 7); ctx.fill();
}

// ---------- 实体 ----------
function drawChests(chests) {
  const sp = itemSprites();
  for (const c of chests) {
    const img = c.opened ? sp.chestOpen : sp.chest;
    ctx.drawImage(img, c.x, c.y + c.h - img.height, img.width, img.height);
  }
}

function drawCoins(coins) {
  const sp = itemSprites();
  for (const c of coins) {
    const img = c.kind === 'heart' ? sp.heart : sp.coin;
    const bob = Math.sin(c.t * 0.15) * 2;
    ctx.drawImage(img, Math.round(c.x - img.width / 2), Math.round(c.y - img.height / 2 + bob));
  }
}

function drawEnemies(list, g) {
  for (const e of list) {
    ctx.save();
    if (!e.alive) ctx.globalAlpha = Math.max(0, e.dying / 18);
    else if (e.hurtT > 0) ctx.globalAlpha = 0.55;
    const spr = enemySprite(e, g.time);
    if (e.type === 'wizard') wizardAura(e, g);
    if (spr) {
      const dx = Math.round(e.x + e.w / 2 - spr.width / 2), dy = Math.round(e.y + e.h - spr.height);
      ctx.drawImage(spr, dx, dy);
    }
    ctx.restore();
    if (e.alive) drawStatusFx(e, g);
    if (e.alive && !e.boss && e.hp < e.maxHp) {
      ctx.fillStyle = '#000'; ctx.fillRect(e.x - 2, e.y - 10, e.w + 4, 5);
      ctx.fillStyle = '#e03030'; ctx.fillRect(e.x - 1, e.y - 9, (e.w + 2) * e.hp / e.maxHp, 3);
      if (e.weak && ELEMENTS[e.weak]) elemBadge(e.x + e.w + 8, e.y - 7, e.weak, 4);   // 血条旁：弱点元素
    }
    if (e.alive && e.type === 'wizard' && e.mode === 'stun') {
      ctx.fillStyle = '#ffe040'; ctx.font = 'bold 13px monospace'; ctx.textAlign = 'center';
      ctx.fillText('★ 输出机会 ★', e.x + e.w / 2, e.y - 18); ctx.textAlign = 'left';
    }
  }
}

function wizardAura(e, g) {
  const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
  const hot = e.mode === 'windup' || e.mode === 'fall';
  const r = ctx.createRadialGradient(cx, cy, 8, cx, cy, hot ? 80 : 62);
  r.addColorStop(0, hot ? 'rgba(255,60,90,0.45)' : 'rgba(150,50,220,0.35)'); r.addColorStop(1, 'rgba(150,50,220,0)');
  ctx.fillStyle = r; ctx.fillRect(cx - 90, cy - 90, 180, 180);
}

function weaponLen(w) { return w.style === 'axe' ? 24 : w.style === 'spear' ? 30 : 20; }

function drawPlayer(p, g) {
  ctx.save();
  if (p.hurtCD > 0 && (p.hurtCD >> 2) % 2 === 0) ctx.globalAlpha = 0.4;
  const moving = Math.abs(p.vx) > 0.5 && p.onGround;
  const frame = !p.onGround ? 'jump' : moving ? ((g.time >> 3) % 2 ? 'walkA' : 'walkB') : 'idle';
  const spr = playerSprite(p.armor, frame, p.facing);
  const dx = Math.round(p.x + p.w / 2 - spr.width / 2), dy = Math.round(p.y + p.h - spr.height);
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.beginPath(); ctx.ellipse(p.x + p.w / 2, p.y + p.h + 1, 11, 3, 0, 0, 7); ctx.fill();
  ctx.drawImage(spr, dx, dy);
  drawWeapon(p, dx, dy);
  if (p.fallDanger) {                              // 落得太高，落地会摔伤：头顶闪一个感叹号
    ctx.globalAlpha = 0.6 + 0.4 * Math.sin(performance.now() / 70);
    ctx.fillStyle = '#000'; ctx.fillRect(Math.round(p.x + p.w / 2) - 3, dy - 22, 7, 16);
    ctx.fillStyle = '#ffb060'; ctx.fillRect(Math.round(p.x + p.w / 2) - 2, dy - 21, 5, 10);
    ctx.fillRect(Math.round(p.x + p.w / 2) - 2, dy - 8, 5, 3);
  }
  ctx.restore();
}

function drawWeapon(p, dx, dy) {
  const w = WEAPONS[p.weapon], f = p.facing;
  const hx = f > 0 ? dx + 19 : dx + 5, hy = dy + 19;
  ctx.save();
  if (w.type === 'melee') {
    const prog = p.attackAnim > 0 ? 1 - p.attackAnim / 12 : -1;
    const ang = prog < 0 ? -0.9 : -1.6 + prog * 3.0;
    ctx.translate(hx, hy); ctx.scale(f, 1); ctx.rotate(ang);
    const len = weaponLen(w);
    const ec = ELEMENTS[w.elem] ? ELEMENTS[w.elem].color : '#fff';
    if (w.elem !== 'phys') {                        // 元素武器：刃身外一圈柔光，随时间脉动
      ctx.globalAlpha = 0.28 + 0.12 * Math.sin(performance.now() / 120);
      ctx.fillStyle = ec; ctx.fillRect(-2, -5, len + 6, 10);
      ctx.globalAlpha = 1;
    }
    if (w.style === 'axe') {
      ctx.fillStyle = '#6a4020'; ctx.fillRect(0, -1, len, 3);
      ctx.fillStyle = w.color; ctx.fillRect(len - 9, -9, 9, 9); ctx.fillRect(len - 3, 2, 3, 1);
    } else if (w.style === 'spear') {
      ctx.fillStyle = '#6a4020'; ctx.fillRect(-4, -1, len - 4, 3);
      ctx.fillStyle = w.color;
      ctx.beginPath(); ctx.moveTo(len - 6, -4); ctx.lineTo(len + 8, 0.5); ctx.lineTo(len - 6, 5); ctx.fill();
      ctx.fillStyle = '#fff8c0'; ctx.fillRect(len - 4, -1, 6, 2);
    } else {                                        // sword
      ctx.fillStyle = w.color; ctx.fillRect(2, -2, len, 4);
      ctx.fillStyle = '#fff'; ctx.fillRect(4, -2, len - 6, 1);
      ctx.fillStyle = '#c0a060'; ctx.fillRect(-1, -4, 3, 8);
      ctx.fillStyle = '#4a2a10'; ctx.fillRect(-5, -1, 4, 3);
    }
    if (prog >= 0) {                               // 挥砍弧光，元素武器带元素色
      ctx.rotate(-ang);
      ctx.strokeStyle = w.elem === 'phys' ? 'rgba(255,255,255,0.55)' : ec; ctx.lineWidth = 3;
      ctx.globalAlpha = 0.7;
      ctx.beginPath(); ctx.arc(0, 0, len + 6, -1.7, ang); ctx.stroke();
      ctx.globalAlpha = 1;
    }
  } else {
    ctx.translate(hx + f * 4, hy); ctx.scale(f, 1);
    // 瞄准角是世界角度；面朝左时画布被水平翻转，角度要取镜像（π - a）才能指对方向
    const aimed = p.aim !== null && p.aim !== undefined;
    const rot = aimed ? (f > 0 ? p.aim : Math.PI - p.aim) : 0;
    if (w.style === 'bow') {                       // 长弓
      ctx.rotate(rot);
      ctx.strokeStyle = w.color; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(0, 0, 12, -1.2, 1.2); ctx.stroke();
      ctx.strokeStyle = '#ddd'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(6, -11); ctx.lineTo(p.attackAnim > 0 ? -4 : 6, 0); ctx.lineTo(6, 11); ctx.stroke();
    } else {                                       // 火焰杖：平时竖直拄着，瞄准时端平指向鼠标
      ctx.rotate(aimed ? rot + Math.PI / 2 : 0);   // 杖身默认朝上（-y），转 +90° 后杖头朝 +x
      ctx.fillStyle = '#6a4020'; ctx.fillRect(-2, -14, 3, 30);
      ctx.fillStyle = w.color; ctx.beginPath(); ctx.arc(0, -16, 5 + (p.attackAnim > 0 ? 2 : 0), 0, 7); ctx.fill();
      ctx.fillStyle = '#ffe060'; ctx.beginPath(); ctx.arc(0, -16, 2.5, 0, 7); ctx.fill();
    }
  }
  ctx.restore();
}

function drawShots(mine, theirs, g) {
  for (const p of mine) {
    const d = Math.sign(p.vx) || 1;
    if (p.kind === 'fire') {
      ctx.fillStyle = 'rgba(255,120,30,0.35)'; ctx.beginPath(); ctx.arc(p.x, p.y, 11, 0, 7); ctx.fill();
      ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x, p.y, 7, 0, 7); ctx.fill();
      ctx.fillStyle = '#ffe060'; ctx.beginPath(); ctx.arc(p.x, p.y, 3.5, 0, 7); ctx.fill();
    } else {
      // 玩家的箭：朝向跟随速度向量，斜射时箭头也是斜的
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(Math.atan2(p.vy || 0, p.vx || 1));
      ctx.fillStyle = '#8a6a40'; ctx.fillRect(-9, -1, 16, 2);
      ctx.fillStyle = p.color; ctx.fillRect(7, -3, 5, 6);
      ctx.fillStyle = '#ddd'; ctx.fillRect(-11, -3, 4, 2); ctx.fillRect(-11, 1, 4, 2);
      ctx.restore();
    }
  }
  for (const p of theirs) {
    if (p.kind === 'fireball') {
      ctx.fillStyle = 'rgba(255,60,30,0.35)'; ctx.beginPath(); ctx.arc(p.x, p.y, 13, 0, 7); ctx.fill();
      ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(p.x, p.y, 8, 0, 7); ctx.fill();
      ctx.fillStyle = '#ffe060'; ctx.beginPath(); ctx.arc(p.x, p.y, 4, 0, 7); ctx.fill();
    } else if (p.kind === 'wave') {
      const h = p.h, w = p.w, wob = Math.sin(g.time * 0.4) * 3;
      ctx.fillStyle = 'rgba(192,64,255,0.35)'; ctx.fillRect(p.x - w / 2 - 4, p.y - h / 2 - 4, w + 8, h + 8);
      ctx.fillStyle = p.color;
      ctx.beginPath(); ctx.moveTo(p.x - w / 2, p.y + h / 2); ctx.lineTo(p.x + Math.sign(p.vx) * wob, p.y - h / 2 - 6);
      ctx.lineTo(p.x + w / 2, p.y + h / 2); ctx.fill();
      ctx.fillStyle = '#f0c0ff'; ctx.fillRect(p.x - 3, p.y - 4, 6, h / 2);
    } else if (p.kind === 'arrow') {                 // 弓手的抛物线箭：朝向跟随速度方向
      const ang = Math.atan2(p.vy || 0, p.vx || 1);
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(ang);
      ctx.fillStyle = '#8a6a40'; ctx.fillRect(-8, -1, 14, 2);
      ctx.fillStyle = '#d8d8e0'; ctx.fillRect(6, -2, 4, 4);
      ctx.fillStyle = '#c05040'; ctx.fillRect(-9, -2, 3, 4);
      ctx.restore();
    } else {
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(g.time * 0.4);
      ctx.fillStyle = p.color; ctx.fillRect(-6, -2, 12, 4); ctx.fillRect(-8, -4, 4, 8); ctx.fillRect(4, -4, 4, 8);
      ctx.restore();
    }
  }
}

function drawParticles(list) {
  for (const q of list) {
    ctx.globalAlpha = Math.min(1, q[3] / 25);
    ctx.fillStyle = q[4]; ctx.fillRect(Math.round(q[0]), Math.round(q[1]), q[2], q[2]);
  }
  ctx.globalAlpha = 1;
}

function drawFloatTexts(list) {
  ctx.textAlign = 'center';
  for (const t of list) {
    ctx.globalAlpha = Math.min(1, t.t / 25);
    ctx.font = 'bold ' + t.size + 'px monospace';
    ctx.fillStyle = '#000'; ctx.fillText(t.txt, t.x + 1, t.y + 1);
    ctx.fillStyle = t.color; ctx.fillText(t.txt, t.x, t.y);
  }
  ctx.globalAlpha = 1; ctx.textAlign = 'left';
}

function drawPrompt(pr) {
  ctx.font = 'bold 13px monospace';
  const w = ctx.measureText(pr.text).width + 20;
  const bob = Math.sin(performance.now() / 220) * 2;
  ctx.fillStyle = 'rgba(0,0,0,0.72)'; ctx.fillRect(Math.round(pr.x - w / 2), Math.round(pr.y - 16 + bob), w, 24);
  ctx.strokeStyle = '#ffe040'; ctx.lineWidth = 1; ctx.strokeRect(Math.round(pr.x - w / 2) + 0.5, Math.round(pr.y - 16 + bob) + 0.5, w - 1, 23);
  ctx.fillStyle = '#ffe040'; ctx.textAlign = 'center'; ctx.fillText(pr.text, pr.x, pr.y + 1 + bob); ctx.textAlign = 'left';
}

// ---------- 刀光拖尾 ----------
function drawSwordTrail(p, g) {
  const w = WEAPONS[p.weapon];
  const swinging = w.type === 'melee' && p.attackAnim > 0;
  // 只在逻辑帧推进时记录（hit-stop 期间 time 不变也无妨：重复点会被忽略）
  if (swinging) {
    const f = p.facing, prog = 1 - p.attackAnim / 12;
    const ang = -1.6 + prog * 3.0;
    const len = weaponLen(w) + 8;
    const ox = Math.round(p.x + p.w / 2) + (f > 0 ? 8 : -8), oy = Math.round(p.y) + 19 - 2;
    const last = fx.trail[fx.trail.length - 1];
    const tip = { x: ox + f * Math.cos(ang) * len, y: oy + Math.sin(ang) * len, ox, oy, a: 1 };
    if (!last || last.x !== tip.x || last.y !== tip.y) pushTrail(tip);
  } else if (fx.trail.length) {
    fx.trail.shift();                      // 挥完后拖尾逐点消失
  }
  if (fx.trail.length < 2) return;
  const col = { phys: w.style === 'axe' ? '200,210,230' : '255,255,255',
                fire: '255,150,60', ice: '140,220,255', thunder: '255,235,90' }[w.elem] || '255,255,255';
  for (let i = 1; i < fx.trail.length; i++) {
    const a = fx.trail[i - 1], b = fx.trail[i], k = i / fx.trail.length;
    ctx.fillStyle = 'rgba(' + col + ',' + (0.55 * k) + ')';
    ctx.beginPath();
    ctx.moveTo(a.ox, a.oy); ctx.lineTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.lineTo(b.ox, b.oy);
    ctx.closePath(); ctx.fill();
  }
}

// ---------- 一次性特效：火花、冲击环、爆炸 ----------
function drawFxList(list) {
  for (const f of list) {
    const k = f.t / (f.life || 12);               // 0 → 1
    if (f.kind === 'spark') {
      const n = f.big ? 9 : 6, len = (f.big ? 26 : 16) * (1 - k * 0.4), a = 1 - k;
      ctx.strokeStyle = f.color || '#fff4c0'; ctx.lineWidth = f.big ? 3 : 2; ctx.globalAlpha = a;
      for (let i = 0; i < n; i++) {
        const ang = (i / n) * Math.PI * 2 + (f.dir > 0 ? 0 : 0.4);
        const r0 = 4 + k * 14, r1 = r0 + len * (0.5 + (i % 3) * 0.25);
        ctx.beginPath();
        ctx.moveTo(f.x + Math.cos(ang) * r0, f.y + Math.sin(ang) * r0);
        ctx.lineTo(f.x + Math.cos(ang) * r1, f.y + Math.sin(ang) * r1);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    } else if (f.kind === 'ring') {
      ctx.strokeStyle = f.color || '#fff'; ctx.lineWidth = 3 * (1 - k) + 1; ctx.globalAlpha = 1 - k;
      ctx.beginPath(); ctx.arc(f.x, f.y, 6 + k * 34, 0, 7); ctx.stroke();
      ctx.globalAlpha = 1;
    } else if (f.kind === 'bolt') {
      drawBolt(f);
    } else if (f.kind === 'blast') {
      const r = f.r * (0.35 + 0.65 * Math.min(1, k * 2.2));
      const g = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, r);
      g.addColorStop(0, 'rgba(255,250,200,' + (0.95 * (1 - k)) + ')');
      g.addColorStop(0.45, 'rgba(255,150,40,' + (0.75 * (1 - k)) + ')');
      g.addColorStop(1, 'rgba(255,60,20,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(f.x, f.y, r, 0, 7); ctx.fill();
      ctx.strokeStyle = 'rgba(255,230,160,' + (1 - k) + ')'; ctx.lineWidth = 4 * (1 - k) + 1;
      ctx.beginPath(); ctx.arc(f.x, f.y, f.r * (0.5 + k * 0.6), 0, 7); ctx.stroke();
    }
  }
}

// ---------- 状态效果：燃烧的火苗、冰冻的冰晶 ----------
function drawStatusFx(e, g) {
  const cx = e.x + e.w / 2;
  if (e.burn > 0) {
    for (let i = 0; i < 3; i++) {
      const ph = (g.time * 0.18 + i * 2.1) % 3, fx0 = cx + (i - 1) * (e.w / 3.2);
      const y = e.y + e.h - ph * (e.h / 2.4), a = 1 - ph / 3;
      ctx.globalAlpha = a;
      ctx.fillStyle = '#ff6a20'; ctx.fillRect(Math.round(fx0 - 2), Math.round(y), 4, 6);
      ctx.fillStyle = '#ffd050'; ctx.fillRect(Math.round(fx0 - 1), Math.round(y + 2), 2, 4);
    }
    ctx.globalAlpha = 1;
  }
  if (e.slow > 0) {
    ctx.fillStyle = 'rgba(120,210,255,0.28)'; ctx.fillRect(e.x - 1, e.y - 1, e.w + 2, e.h + 2);
    ctx.fillStyle = '#d8f4ff';
    for (let i = 0; i < 3; i++) {
      const px = e.x + 3 + i * (e.w - 8) / 2, py = e.y + 2 + ((i * 7) % (e.h - 6));
      ctx.fillRect(Math.round(px), Math.round(py), 3, 3);
    }
  }
}

// 电弧：两点之间画一条锯齿闪电，每帧抖动
function drawBolt(f) {
  const k = f.t / (f.life || 10);
  const dx = f.x2 - f.x, dy = f.y2 - f.y, n = 6, nx = -dy, ny = dx, nl = Math.hypot(nx, ny) || 1;
  const pts = [[f.x, f.y]];
  for (let i = 1; i < n; i++) {
    const j = ((i * 37 + f.t * 53) % 21 - 10) * 0.9;
    pts.push([f.x + dx * i / n + nx / nl * j, f.y + dy * i / n + ny / nl * j]);
  }
  pts.push([f.x2, f.y2]);
  ctx.globalAlpha = 1 - k;
  for (const [w, c] of [[5, 'rgba(255,230,80,0.4)'], [2, '#fffbd0']]) {
    ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath();
    pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

// ---------- 准星：只在手持远程武器时显示 ----------
// 瞄准线从角色画到鼠标，让玩家看清弹道方向；按住左键时线变亮。
function drawCrosshair(s) {
  if (typeof mouse === 'undefined' || !mouse) return;
  const g = s.game;
  if (g.panel || g.state === 'menu' || g.state === 'dead' || g.state === 'win') return;
  const w = WEAPONS[s.player.weapon];
  if (!w || w.type !== 'ranged') return;
  const active = mouseAttack;
  const mx = mouse.x, my = mouse.y;
  const ox = s.player.x + s.player.w / 2 - g.camX, oy = s.player.y + s.player.h / 2 - 4;
  const ec = ELEMENTS[w.elem] ? ELEMENTS[w.elem].color : '#fff';
  ctx.save();
  ctx.setLineDash([5, 7]);
  ctx.strokeStyle = active ? ec : 'rgba(255,255,255,0.25)'; ctx.lineWidth = 1.5;
  ctx.globalAlpha = active ? 0.8 : 1;
  ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(mx, my); ctx.stroke();
  ctx.setLineDash([]); ctx.globalAlpha = 1;
  ctx.strokeStyle = '#000'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.arc(mx, my, 9, 0, 7); ctx.moveTo(mx - 15, my); ctx.lineTo(mx - 5, my);
  ctx.moveTo(mx + 5, my); ctx.lineTo(mx + 15, my); ctx.moveTo(mx, my - 15); ctx.lineTo(mx, my - 5);
  ctx.moveTo(mx, my + 5); ctx.lineTo(mx, my + 15); ctx.stroke();
  ctx.strokeStyle = active ? ec : '#fff'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(mx, my, 9, 0, 7); ctx.moveTo(mx - 15, my); ctx.lineTo(mx - 5, my);
  ctx.moveTo(mx + 5, my); ctx.lineTo(mx + 15, my); ctx.moveTo(mx, my - 15); ctx.lineTo(mx, my - 5);
  ctx.moveTo(mx, my + 5); ctx.lineTo(mx, my + 15); ctx.stroke();
  ctx.restore();
}
