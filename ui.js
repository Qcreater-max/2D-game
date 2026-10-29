/* 界面层：HUD、菜单、商店 / 背包 / 战绩面板、死亡与通关画面、关卡标题与淡入淡出 */

function txt(s, x, y, color, font, align) {
  ctx.font = font || '14px monospace'; ctx.textAlign = align || 'left';
  ctx.fillStyle = '#000'; ctx.fillText(s, x + 1, y + 1);
  ctx.fillStyle = color || '#fff'; ctx.fillText(s, x, y);
  ctx.textAlign = 'left';
}

function panelBox(x, y, w, h, border) {
  ctx.fillStyle = 'rgba(10,8,24,0.94)'; ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = border; ctx.lineWidth = 3; ctx.strokeRect(x + 1.5, y + 1.5, w - 3, h - 3);
  ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1; ctx.strokeRect(x + 6.5, y + 6.5, w - 13, h - 13);
}

function dim(a) { ctx.fillStyle = 'rgba(0,0,0,' + a + ')'; ctx.fillRect(0, 0, W, H); }

function drawUI(s, lv) {
  const g = s.game, p = s.player;
  if (g.state === 'menu') { drawMenu(g); return; }
  drawHUD(s);
  if (g.flash > 0) { ctx.fillStyle = 'rgba(255,220,90,' + (g.flash / 60) + ')'; ctx.fillRect(0, 0, W, H); }
  if (g.introT > 0) drawIntro(g);
  if (g.msgT > 0) drawMsg(g);
  if (g.panel === 'shop') drawShop(g, p);
  else if (g.panel === 'inv') drawInv(g, p);
  else if (g.panel === 'stats') drawStats(g, p);
  if (g.fade > 0) dim(Math.min(1, g.fade));
  if (g.state === 'dead') drawDead(g, p);
  if (g.state === 'win') drawWin(g, p);
}

// ---------- HUD ----------
function drawHUD(s) {
  const g = s.game, p = s.player;
  panelBox(8, 8, 252, 98, '#4a4a78');
  txt('Lv.' + p.level, 20, 30, '#ffe040', 'bold 14px monospace');
  ctx.fillStyle = '#000'; ctx.fillRect(64, 18, 186, 14);
  const hpRatio = Math.max(0, p.hp / p.maxHp);
  ctx.fillStyle = hpRatio > 0.3 ? '#d02828' : (g.time >> 3) % 2 ? '#ff6060' : '#d02828';
  ctx.fillRect(65, 19, 184 * hpRatio, 12);
  txt(p.hp + '/' + p.maxHp, 157, 30, '#fff', '11px monospace', 'center');
  ctx.fillStyle = '#000'; ctx.fillRect(64, 36, 186, 6);
  ctx.fillStyle = '#3a90ff'; ctx.fillRect(65, 37, 184 * Math.min(1, p.exp / p.expNext), 4);
  txt('$ ' + p.gold, 20, 62, '#ffd84a', 'bold 13px monospace');
  const w = WEAPONS[p.weapon], a = ARMORS[p.armor];
  elemBadge(24, 78, w.elem);
  txt(w.name + '  伤害 ' + w.dmg, 36, 82, '#d8d8ff', '12px monospace');
  txt('盔甲 ' + a.name + '  减伤 ' + a.reduce + '%', 20, 98, '#d8d8ff', '12px monospace');

  // 右上：关卡与目标
  const left = g.enemiesLeft;
  panelBox(W - 232, 8, 224, 54, '#4a4a78');
  txt(g.levelName, W - 120, 28, g.depth > 0 ? '#c0a070' : '#80c0ff', 'bold 13px monospace', 'center');
  let goal, goalColor = left > 0 ? '#ffd0d0' : '#90ff90';
  if (g.mode === 'endless') {
    goal = g.waveBreak > 0 ? '下一波即将到来…' : '剩余敌人 ' + left;
    if (g.waveBreak > 0) goalColor = '#ffe080';
  } else if (g.state === 'boss') goal = '击败暗影巫师';
  else if (g.depth > 0) { goal = g.state.startsWith('secret_') ? '打开宝箱后从左侧离开' : '探索地下，找到左边的梯子返回'; goalColor = '#e0d0b0'; }
  else goal = left > 0 ? '剩余敌人 ' + left + ' / ' + g.enemiesTotal : '敌人已清除，前往传送门 →';
  txt(goal, W - 120, 50, goalColor, '12px monospace', 'center');
  if (g.inPoison) { ctx.fillStyle = 'rgba(120,220,60,0.12)'; ctx.fillRect(0, 0, W, H); }   // 泡在毒沼里：画面泛绿

  // Boss 血条
  if (s.boss) {
    const bw = 380, bx = W / 2 - bw / 2, hp = s.boss.hp / s.boss.maxHp;
    ctx.fillStyle = '#000'; ctx.fillRect(bx - 3, 17, bw + 6, 20);
    ctx.fillStyle = s.boss.enraged ? '#e02060' : '#8a30d0'; ctx.fillRect(bx, 20, bw * hp, 14);
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.strokeRect(bx - 2.5, 17.5, bw + 5, 19);
    txt('暗影巫师' + (s.boss.enraged ? '  · 狂暴' : ''), W / 2, 50, '#e8c0ff', 'bold 12px monospace', 'center');
  }
  if (!window.IS_TOUCH) txt('A/D 移动  W/空格 跳  J 攻击  E 互动  I 背包  Tab 战绩', 12, H - 10, 'rgba(255,255,255,0.65)', '11px monospace');
  if (s.card) drawMonsterCard(s.card, W - 232, 68);
}

// ---------- 元素徽标 / 怪物卡片 ----------
function elemInfo(k) { return ELEMENTS[k] || { name: '无', short: '-', color: '#888' }; }

// 小圆徽标：圆底 + 单字，颜色区分元素
function elemBadge(cx, cy, k, r) {
  const e = elemInfo(k); r = r || 7;
  ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(cx, cy, r + 1, 0, 7); ctx.fill();
  ctx.fillStyle = e.color; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill();
  ctx.fillStyle = '#101018'; ctx.font = 'bold ' + (r + 3) + 'px monospace'; ctx.textAlign = 'center';
  ctx.fillText(e.short, cx, cy + (r - 3)); ctx.textAlign = 'left';
}

// 一行"标签 + 徽标 + 文字"；k 为 null 时显示"无"
function elemRow(x, y, label, k, extra) {
  txt(label, x, y, '#9a9ab4', '12px monospace');
  if (k) {
    elemBadge(x + 52, y - 4, k, 7);
    txt(elemInfo(k).name + (extra || ''), x + 66, y, elemInfo(k).color, 'bold 12px monospace');
  } else {
    txt('无', x + 46, y, '#6a6a80', '12px monospace');
  }
}

// 怪物卡片：新怪物第一次入镜时弹出，从右侧滑入、结束前淡出
function drawMonsterCard(card, x, y) {
  const info = ENEMY_INFO[card.type]; if (!info) return;
  const age = card.total - card.t;
  const slide = Math.min(1, age / 14), fade = Math.min(1, card.t / 30);
  ctx.save();
  ctx.globalAlpha = fade;
  ctx.translate((1 - slide) * 240, 0);
  const w = 224, h = 156;
  panelBox(x, y, w, h, info.boss ? '#c040ff' : '#e0b040');
  txt(info.boss ? '首领' : '新怪物', x + 12, y + 20, info.boss ? '#e8a0ff' : '#ffd070', 'bold 11px monospace');
  txt(info.name, x + w - 12, y + 22, '#ffffff', 'bold 17px monospace', 'right');
  // 怪物小图：用当前真实精灵，保证和场景里一致
  const spr = enemySprite({ type: card.type, dir: 1, mode: 'idle', modeT: 0 }, 0);
  if (spr) {
    const sc = Math.min(1.4, 46 / Math.max(spr.width, spr.height));
    ctx.drawImage(spr, x + 14, y + 34 + (46 - spr.height * sc) / 2, spr.width * sc, spr.height * sc);
  }
  // 生命 / 防御
  txt('生命', x + 70, y + 50, '#9a9ab4', '12px monospace');
  txt(String(info.hp), x + 104, y + 50, '#ff8a8a', 'bold 13px monospace');
  txt('防御', x + 70, y + 70, '#9a9ab4', '12px monospace');
  txt(String(info.def), x + 104, y + 70, '#a8c8ff', 'bold 13px monospace');
  const wk = Math.round((WEAK_MULT - 1) * 100), rs = Math.round((1 - RESIST_MULT) * 100);
  elemRow(x + 14, y + 98, '弱点', info.weak, ' +' + wk + '%');
  elemRow(x + 14, y + 116, '抗性', info.resist, ' -' + rs + '%');
  elemRow(x + 120, y + 70, '攻击', info.atk);
  txt(info.desc, x + 14, y + 142, '#e8e8c8', '11px monospace');
  ctx.restore();
}

function drawIntro(g) {
  const a = Math.min(1, g.introT / 40, (200 - g.introT) / 20);
  ctx.globalAlpha = Math.max(0, a);
  ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(0, 150, W, 90);
  txt(g.title, W / 2, 192, '#ffe040', 'bold 30px monospace', 'center');
  txt(g.hint, W / 2, 222, '#e8e8ff', '14px monospace', 'center');
  ctx.globalAlpha = 1;
}

function drawMsg(g) {
  ctx.font = 'bold 16px monospace';
  const w = ctx.measureText(g.msg).width + 40;
  ctx.globalAlpha = Math.min(1, g.msgT / 15);
  ctx.fillStyle = 'rgba(0,0,0,0.7)'; ctx.fillRect(W / 2 - w / 2, 256, w, 34);
  ctx.strokeStyle = '#ffe040'; ctx.lineWidth = 1; ctx.strokeRect(W / 2 - w / 2 + 0.5, 256.5, w - 1, 33);
  txt(g.msg, W / 2, 279, '#ffe040', 'bold 16px monospace', 'center');
  ctx.globalAlpha = 1;
}

// ---------- 菜单 ----------
function drawMenu(g) {
  const grd = ctx.createLinearGradient(0, 0, 0, H);
  grd.addColorStop(0, '#0a0620'); grd.addColorStop(1, '#2a1038');
  ctx.fillStyle = grd; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 70; i++) {
    ctx.globalAlpha = 0.3 + 0.7 * Math.abs(Math.sin(g.time * 0.03 + i));
    ctx.fillStyle = '#fff'; ctx.fillRect((i * 131) % W, (i * 71) % 330, 2, 2);
  }
  ctx.globalAlpha = 1;
  const bob = Math.sin(g.time * 0.05) * 4;
  txt('像素勇士', W / 2, 150 + bob, '#ffe040', 'bold 68px monospace', 'center');
  txt('暗影征途', W / 2, 196 + bob, '#c0a060', 'bold 24px monospace', 'center');
  // 模式选择：上下 / 左右切换，确认开始
  const modes = [
    { name: '冒险模式', desc: '6 关 + 地下洞穴 + 隐藏房间', color: '#ffe040' },
    { name: '无尽挑战', desc: '一波接一波，看你能撑几波', color: '#ff8a5a' },
  ];
  modes.forEach((m, i) => {
    const sel = g.menuIdx === i, bx = W / 2 - 250 + i * 260, by = 236, bw = 240, bh = 74;
    ctx.fillStyle = sel ? 'rgba(70,50,110,0.95)' : 'rgba(30,24,50,0.8)'; ctx.fillRect(bx, by, bw, bh);
    ctx.strokeStyle = sel ? m.color : '#4a4a78'; ctx.lineWidth = sel ? 3 : 1; ctx.strokeRect(bx + 0.5, by + 0.5, bw - 1, bh - 1);
    txt((sel ? '▶ ' : '  ') + m.name, bx + 14, by + 28, sel ? m.color : '#9a9ab4', 'bold 18px monospace');
    txt(m.desc, bx + 14, by + 52, sel ? '#e8e8ff' : '#7a7a96', '11px monospace');
    if (i === 1 && g.bestWave > 0) txt('最高 ' + g.bestWave + ' 波', bx + bw - 12, by + 28, '#ffd0a0', '12px monospace', 'right');
  });
  if ((g.time >> 5) % 2 === 0) txt('← →  选择模式      空格 / Enter / J  开始', W / 2, 340, '#ffffff', 'bold 15px monospace', 'center');
  panelBox(W / 2 - 250, 362, 500, 150, '#4a4a78');
  const rows = [['A D / ← →', '移动'], ['W / ↑ / 空格', '跳跃（S + 跳 下穿平台）'], ['J / 鼠标左键', '攻击（远程武器朝鼠标发射）'],
                ['E', '开宝箱 / 铁匠铺 / 传送门'], ['按住 S + E', '进入脚下的地洞'], ['I  /  Tab', '背包  /  战绩']];
  rows.forEach((r, i) => {
    txt(r[0], W / 2 - 220, 390 + i * 20, '#ffd84a', 'bold 13px monospace');
    txt(r[1], W / 2 - 60, 390 + i * 20, '#e0e0ff', '13px monospace');
  });
}

// ---------- 商店 / 背包 ----------
function itemRow(x, y, w, item, selected, color, left, right, rightColor) {
  ctx.fillStyle = selected ? '#4a3070' : 'rgba(255,255,255,0.05)'; ctx.fillRect(x, y - 18, w, 32);
  if (selected) { ctx.strokeStyle = '#ffe040'; ctx.lineWidth = 2; ctx.strokeRect(x + 1, y - 17, w - 2, 30); }
  ctx.fillStyle = item.color; ctx.fillRect(x + 8, y - 8, 14, 14);
  ctx.strokeStyle = '#000'; ctx.lineWidth = 1; ctx.strokeRect(x + 8.5, y - 7.5, 13, 13);
  if (item.elem && item.elem !== 'phys') elemBadge(x + 28, y - 11, item.elem, 6);   // 武器元素角标
  txt(left, x + 38, y + 4, color, 'bold 14px monospace');
  txt(right, x + w - 12, y + 4, rightColor, '13px monospace', 'right');
}

// 抗性一行：只列出非 0 的项，正数绿色（抗），负数红色（怕）
function resistList(x, y, res) {
  const keys = ['fire', 'ice', 'thunder'].filter(k => res && res[k]);
  if (!keys.length) { txt('无元素抗性', x, y, '#6a6a80', '12px monospace'); return; }
  keys.forEach((k, i) => {
    const v = res[k], cx = x + i * 92;
    elemBadge(cx + 6, y - 4, k, 6);
    txt((v > 0 ? '抗' : '怕') + Math.abs(v) + '%', cx + 18, y, v > 0 ? '#80e090' : '#ff8080', 'bold 12px monospace');
  });
}

// 选中物品的详情区。cur 是当前已装备的同类物品，用于显示差值
function itemDetail(x, y, w, item, isWeapon, cur) {
  panelBox(x, y, w, 76, '#3a3a60');
  const diff = (a, b, fmt) => { const d = a - b; return d === 0 ? '' : '  (' + (d > 0 ? '+' : '') + (fmt ? fmt(d) : d) + ')'; };
  if (isWeapon) {
    const dps = (v => v.dmg * 60 / v.cd), c = cur || item;
    txt('伤害 ' + item.dmg + diff(item.dmg, c.dmg), x + 14, y + 22, '#fff', '12px monospace');
    txt('秒伤 ' + dps(item).toFixed(1) + diff(dps(item), dps(c), d => d.toFixed(1)), x + 14, y + 40, '#ffd070', '12px monospace');
    txt('射程 ' + item.range + (item.type === 'ranged' ? '  远程' : '  近战') + (item.heavy ? '  · 重击(破盾)' : ''), x + 14, y + 58, '#c8c8e0', '12px monospace');
    const e = elemInfo(item.elem);
    elemBadge(x + 250, y + 18, item.elem, 7);
    txt(e.name + '属性', x + 264, y + 22, e.color, 'bold 13px monospace');
    const fx = { phys: '无元素加成', fire: '命中后灼烧 3 秒，伤害持续', ice: '命中后减速 2 秒（首领免疫）', thunder: '电弧跳向附近敌人，无视盾卫格挡' }[item.elem];
    txt(fx, x + 250, y + 44, '#d8d8f0', '12px monospace');
    txt('怪物弱点元素 +50% 伤害，抗性 -50%', x + 250, y + 62, '#8a8aa8', '11px monospace');
  } else {
    const c = cur || item;
    txt('减伤 ' + item.reduce + '%' + diff(item.reduce, c.reduce, d => d + '%'), x + 14, y + 24, '#fff', '13px monospace');
    txt('元素抗性（正数为抗，负数为怕）', x + 14, y + 46, '#9a9ab4', '12px monospace');
    resistList(x + 14, y + 66, item.res);
    txt('当前: ' + (c.name), x + w - 14, y + 24, '#8a8aa8', '12px monospace', 'right');
  }
}

function drawShop(g, p) {
  dim(0.7);
  const bx = W / 2 - 280, by = 20, bw = 560, bh = 500;
  panelBox(bx, by, bw, bh, '#ffe040');
  txt('铁匠铺', bx + 24, by + 38, '#ffe040', 'bold 22px monospace');
  txt('金币 ' + p.gold, bx + bw - 24, by + 38, '#ffd84a', 'bold 16px monospace', 'right');
  ['武器', '盔甲'].forEach((n, i) => txt((g.panelTab === i ? '▶ ' : '  ') + n, bx + 24 + i * 110, by + 74, g.panelTab === i ? '#ffe040' : '#8888a0', 'bold 16px monospace'));
  const list = g.panelTab === 0 ? WEAPONS : ARMORS;
  const owned = g.panelTab === 0 ? p.ownedWeapons : p.ownedArmors;
  const eq = g.panelTab === 0 ? p.weapon : p.armor;
  const rowH = 30, top = by + 100;
  list.forEach((it, i) => {
    const has = owned.includes(i), on = eq === i;
    const stat = g.panelTab === 0
      ? it.name + '  伤' + it.dmg + ' 速' + (60 / it.cd).toFixed(1) + '/s'
      : it.name + '  减伤 ' + it.reduce + '%';
    const right = on ? '已装备' : has ? '已拥有' : it.price + ' 金' + (p.gold >= it.price ? '' : '（不足）');
    itemRow(bx + 20, top + i * rowH + 18, bw - 40, it, g.panelIdx === i, on ? '#80ff80' : has ? '#a0c0ff' : '#fff',
            stat, right, on ? '#80ff80' : has ? '#a0c0ff' : (p.gold >= it.price ? '#ffd84a' : '#ff8080'));
  });
  const sel = list[g.panelIdx];
  if (sel) itemDetail(bx + 20, by + bh - 116, bw - 40, sel, g.panelTab === 0, list[eq]);
  txt('← → 页签   ↑ ↓ 选择   空格 / Enter / J 购买或装备   E / Esc 关闭', bx + bw / 2, by + bh - 14, '#b0b0c8', '12px monospace', 'center');
}

function drawInv(g, p) {
  dim(0.7);
  const bx = W / 2 - 260, by = 30, bw = 520, bh = 480;
  panelBox(bx, by, bw, bh, '#80c0ff');
  txt('背包', bx + 24, by + 38, '#80c0ff', 'bold 22px monospace');
  txt('Lv.' + p.level + '   HP ' + p.hp + '/' + p.maxHp + '   金币 ' + p.gold, bx + bw - 24, by + 38, '#fff', '14px monospace', 'right');
  ['武器', '盔甲'].forEach((n, i) => txt((g.panelTab === i ? '▶ ' : '  ') + n, bx + 24 + i * 110, by + 74, g.panelTab === i ? '#80c0ff' : '#8888a0', 'bold 16px monospace'));
  const ids = g.panelTab === 0 ? p.ownedWeapons : p.ownedArmors;
  const list = g.panelTab === 0 ? WEAPONS : ARMORS;
  const eq = g.panelTab === 0 ? p.weapon : p.armor;
  const rowH = 30, top = by + 100;
  ids.forEach((id, i) => {
    const it = list[id], on = eq === id;
    const stat = g.panelTab === 0 ? it.name + '  伤' + it.dmg + ' 速' + (60 / it.cd).toFixed(1) + '/s' : it.name + '  减伤 ' + it.reduce + '%';
    itemRow(bx + 20, top + i * rowH + 18, bw - 40, it, g.panelIdx === i, on ? '#80ff80' : '#fff', stat, on ? '已装备' : '确认装备', on ? '#80ff80' : '#a0c0ff');
  });
  const selId = ids[g.panelIdx];
  if (selId !== undefined) itemDetail(bx + 20, by + bh - 116, bw - 40, list[selId], g.panelTab === 0, list[eq]);
  txt('← → 页签   ↑ ↓ 选择   空格 / Enter / J 装备   I / Esc 关闭', bx + bw / 2, by + bh - 14, '#b0b0c8', '12px monospace', 'center');
}

function drawStats(g, p) {
  dim(0.75);
  const bx = W / 2 - 240, by = 60, bw = 480, bh = 420;
  panelBox(bx, by, bw, bh, '#ffd84a');
  txt('战绩', W / 2, by + 44, '#ffd84a', 'bold 26px monospace', 'center');
  const sec = Math.floor(g.playTime / 60);
  const t = String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0');
  const rows = [['当前关卡', g.levelName, '#80c0ff'], ['角色等级', 'Lv.' + p.level, '#80ff80'],
    ['击杀敌人', g.kills + ' 只', '#ff8080'], ['累计伤害', g.totalDamage, '#ffaa40'],
    ['获得金币', g.goldEarned, '#ffd84a'], ['游戏时长', t, '#a0e0ff'],
    ['打碎木箱', g.crates + ' 个', '#d0a060'], ['发现隐藏房间', g.secretsFound + ' 个', '#ffe080'],
    ['武器', WEAPONS[p.weapon].name, '#c0e060'], ['盔甲', ARMORS[p.armor].name, '#b0c0d0']];
  rows.forEach((r, i) => {
    txt(r[0], bx + 50, by + 90 + i * 29, '#a0a0b8', '15px monospace');
    txt(String(r[1]), bx + bw - 50, by + 90 + i * 29, r[2], 'bold 15px monospace', 'right');
  });
  txt('Tab / C / Esc 关闭', W / 2, by + bh - 20, '#b0b0c8', '12px monospace', 'center');
}

// ---------- 结束画面 ----------
function drawDead(g, p) {
  const a = Math.min(0.9, g.endT / 30);
  dim(a); ctx.fillStyle = 'rgba(80,0,0,' + a * 0.5 + ')'; ctx.fillRect(0, 0, W, H);
  txt('你倒下了', W / 2, 220, '#ff4040', 'bold 60px monospace', 'center');
  txt(g.deadReason, W / 2, 262, '#ffaaaa', '18px monospace', 'center');
  txt('已击杀 ' + g.kills + ' 只敌人 · 等级 Lv.' + p.level, W / 2, 296, '#d0d0d0', '14px monospace', 'center');
  if (g.mode === 'endless') {
    txt('本次坚持到第 ' + g.wave + ' 波   历史最高第 ' + Math.max(g.bestWave, g.wave - 1) + ' 波', W / 2, 322, '#ffd0a0', 'bold 15px monospace', 'center');
    if (g.endT > 45) txt('空格 / Enter / J  返回主菜单', W / 2, 372, '#ffffff', 'bold 16px monospace', 'center');
    return;
  }
  if (g.endT > 45) {
    txt('空格 / Enter / J  重新挑战本关（保留装备与等级）', W / 2, 350, '#ffffff', 'bold 16px monospace', 'center');
    txt('Esc  返回主菜单', W / 2, 378, '#a0a0b0', '14px monospace', 'center');
  }
}

function drawWin(g, p) {
  dim(0.9);
  for (let i = 0; i < 48; i++) {
    const a = i / 48 * Math.PI * 2 + g.time * 0.01, r = 120 + Math.sin(g.time * 0.05 + i) * 40;
    ctx.fillStyle = 'rgba(255,216,74,' + (0.35 + Math.sin(i) * 0.2) + ')';
    ctx.fillRect(W / 2 + Math.cos(a) * r, 250 + Math.sin(a) * r * 0.6, 4, 4);
  }
  txt('通关！', W / 2, 190, '#ffe040', 'bold 66px monospace', 'center');
  txt('暗影巫师已被击败，王国重归平静', W / 2, 238, '#ffffff', '20px monospace', 'center');
  const sec = Math.floor(g.playTime / 60);
  txt('最终等级 Lv.' + p.level + '   击杀 ' + g.kills + '   用时 ' + String(Math.floor(sec / 60)).padStart(2, '0') + ':' + String(sec % 60).padStart(2, '0'),
      W / 2, 282, '#d8d8ff', '16px monospace', 'center');
  if (g.endT > 45) txt('空格 / Enter / J  返回主菜单', W / 2, 340, '#ffffff', 'bold 16px monospace', 'center');
}
