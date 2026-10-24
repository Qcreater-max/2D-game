/* 第 2 期的世界元素：危险物、移动平台、木箱、地洞、隐藏裂墙、返回梯子、主题氛围 */

// ---------- 危险物 ----------
function drawHazards(list, g) {
  for (const h of list) {
    if (h.x + h.w < g.camX - 20 || h.x > g.camX + W + 20) continue;
    const t = g.time;
    if (h.kind === 'spikes') {
      ctx.fillStyle = '#2a2a38'; ctx.fillRect(h.x, h.y + 4, h.w, 8);
      const n = Math.floor(h.w / 14);
      for (let i = 0; i < n; i++) {
        const bx = h.x + 2 + i * (h.w - 4) / n, bw = (h.w - 4) / n - 2;
        ctx.fillStyle = '#b8bcc8'; ctx.beginPath(); ctx.moveTo(bx, h.y + 6); ctx.lineTo(bx + bw / 2, h.y - 12); ctx.lineTo(bx + bw, h.y + 6); ctx.fill();
        ctx.fillStyle = '#eef0f8'; ctx.beginPath(); ctx.moveTo(bx + bw * 0.3, h.y + 4); ctx.lineTo(bx + bw / 2, h.y - 12); ctx.lineTo(bx + bw * 0.5, h.y + 4); ctx.fill();
      }
    } else if (h.kind === 'lava') {
      const top = h.y + 6;
      const grd = ctx.createLinearGradient(0, top, 0, top + 80);
      grd.addColorStop(0, '#ffd040'); grd.addColorStop(0.2, '#ff7020'); grd.addColorStop(1, '#a01808');
      ctx.fillStyle = grd; ctx.fillRect(h.x, top, h.w, H);
      ctx.fillStyle = '#ffe880';                                       // 表面起伏的波浪线
      for (let x = h.x; x < h.x + h.w; x += 10) ctx.fillRect(x, top - 2 + Math.sin((x + t * 2) * 0.12) * 3, 8, 3);
      for (let i = 0; i < 4; i++) {                                    // 冒泡
        const bx = h.x + ((i * 53 + t * 0.6) % h.w), by = top + 4 + ((i * 29 + t * 0.9) % 30);
        ctx.fillStyle = 'rgba(255,230,120,0.7)'; ctx.fillRect(Math.round(bx), Math.round(by), 3, 3);
      }
      const glow = ctx.createLinearGradient(0, top - 50, 0, top);      // 岩浆照亮周围
      glow.addColorStop(0, 'rgba(255,100,20,0)'); glow.addColorStop(1, 'rgba(255,100,20,0.35)');
      ctx.fillStyle = glow; ctx.fillRect(h.x - 8, top - 50, h.w + 16, 50);
    } else if (h.kind === 'poison') {
      const top = h.y + 8;
      ctx.fillStyle = '#3a5a22'; ctx.fillRect(h.x, top, h.w, H);
      ctx.fillStyle = 'rgba(120,220,60,0.55)'; ctx.fillRect(h.x, top, h.w, H);
      ctx.fillStyle = '#b8f060';
      for (let x = h.x; x < h.x + h.w; x += 12) ctx.fillRect(x, top - 1 + Math.sin((x + t * 1.5) * 0.15) * 2, 9, 3);
      for (let i = 0; i < 3; i++) {
        const ph = ((t * 0.8 + i * 23) % 40) / 40, bx = h.x + 12 + (i * 31) % (h.w - 24);
        ctx.strokeStyle = 'rgba(210,255,140,' + (1 - ph) + ')'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(bx, top - ph * 14, 2 + ph * 2, 0, 7); ctx.stroke();
      }
    }
  }
}

// ---------- 移动平台 ----------
function drawMovers(list, g, t) {
  for (const m of list) {
    ctx.fillStyle = t.plat; ctx.fillRect(m.x, m.y, m.w, m.h);
    ctx.fillStyle = t.platHi; ctx.fillRect(m.x, m.y, m.w, 4);
    ctx.fillStyle = '#e0c060';                                         // 两端的黄色铆钉，区别于静态平台
    ctx.fillRect(m.x + 3, m.y + 6, 4, 4); ctx.fillRect(m.x + m.w - 7, m.y + 6, 4, 4);
    ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(m.x, m.y + m.h - 3, m.w, 3);
    ctx.fillStyle = 'rgba(255,230,120,0.5)';                           // 箭头暗示它会左右移动
    const cx = m.x + m.w / 2;
    ctx.beginPath(); ctx.moveTo(cx - 10, m.y + 8); ctx.lineTo(cx - 5, m.y + 5); ctx.lineTo(cx - 5, m.y + 11); ctx.fill();
    ctx.beginPath(); ctx.moveTo(cx + 10, m.y + 8); ctx.lineTo(cx + 5, m.y + 5); ctx.lineTo(cx + 5, m.y + 11); ctx.fill();
  }
}

// ---------- 木箱 ----------
function drawCrates(list) {
  for (const c of list) {
    ctx.fillStyle = '#8a5a28'; ctx.fillRect(c.x, c.y, c.w, c.h);
    ctx.fillStyle = '#b07a3a'; ctx.fillRect(c.x + 2, c.y + 2, c.w - 4, c.h - 4);
    ctx.fillStyle = '#6a4018';
    ctx.fillRect(c.x, c.y + c.h / 2 - 1, c.w, 3);
    ctx.fillRect(c.x + c.w / 2 - 1, c.y, 3, c.h);
    ctx.fillStyle = '#3a2008';
    ctx.fillRect(c.x, c.y, 3, 3); ctx.fillRect(c.x + c.w - 3, c.y, 3, 3);
    ctx.fillRect(c.x, c.y + c.h - 3, 3, 3); ctx.fillRect(c.x + c.w - 3, c.y + c.h - 3, 3, 3);
    if (c.hp < 2) {                                                    // 受过一击：画裂纹
      ctx.strokeStyle = '#2a1404'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(c.x + 6, c.y + 3); ctx.lineTo(c.x + 12, c.y + 13); ctx.lineTo(c.x + 8, c.y + 22); ctx.stroke();
    }
  }
}

// ---------- 地洞入口 ----------
function drawHoles(list, g) {
  for (const h of list) {
    if (h.x < g.camX - 60 || h.x > g.camX + W + 60) continue;
    const y = 480;
    ctx.fillStyle = '#0a0806'; ctx.beginPath(); ctx.ellipse(h.x, y + 2, 30, 9, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#000'; ctx.beginPath(); ctx.ellipse(h.x, y + 3, 24, 6, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = '#5a4a38'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(h.x, y + 2, 30, 9, 0, 0, 7); ctx.stroke();
    const bob = Math.sin(g.time * 0.1) * 3;                            // 向下的小箭头，轻轻浮动
    ctx.fillStyle = 'rgba(255,224,64,0.85)';
    ctx.beginPath(); ctx.moveTo(h.x - 7, y - 26 + bob); ctx.lineTo(h.x + 7, y - 26 + bob); ctx.lineTo(h.x, y - 14 + bob); ctx.fill();
  }
}

// ---------- 隐藏房间的"可疑裂墙" ----------
function drawSecrets(list, g) {
  for (const s of list) {
    if (s.x < g.camX - 60 || s.x > g.camX + W + 60) continue;
    const x = s.x - 16, y = 480 - 90;
    if (s.open) {                                                      // 墙已破开：露出一道发光的门洞
      ctx.fillStyle = '#000'; ctx.fillRect(x + 2, y + 10, 28, 80);
      const pulse = 0.5 + 0.3 * Math.sin(g.time * 0.1);
      ctx.fillStyle = 'rgba(255,224,120,' + pulse + ')'; ctx.fillRect(x + 8, y + 18, 16, 72);
      ctx.fillStyle = '#6a5a40'; ctx.fillRect(x, y, 32, 12);
      ctx.fillRect(x, y, 4, 90); ctx.fillRect(x + 28, y, 4, 90);
      continue;
    }
    const dmg = 1 - s.hp / s.maxHp;
    ctx.fillStyle = '#7a6e62'; ctx.fillRect(x, y, 32, 90);
    ctx.fillStyle = '#948878'; ctx.fillRect(x + 2, y + 2, 28, 86);
    ctx.fillStyle = '#5a5046';
    for (let r = 0; r < 6; r++) ctx.fillRect(x, y + 14 + r * 15, 32, 2);
    ctx.strokeStyle = '#2a241e'; ctx.lineWidth = 2;                    // 裂缝，受击越多越长
    const len = 30 + dmg * 50;
    ctx.beginPath(); ctx.moveTo(x + 14, y + 12); ctx.lineTo(x + 18, y + 12 + len * 0.35);
    ctx.lineTo(x + 11, y + 12 + len * 0.65); ctx.lineTo(x + 17, y + 12 + len); ctx.stroke();
    if ((g.time >> 4) % 4 === 0) { ctx.fillStyle = 'rgba(255,224,120,0.8)'; ctx.fillRect(x + 22, y + 30, 3, 3); }
  }
}

// ---------- 子关卡返回地面的梯子 ----------
function drawBackLadder(x, g) {
  if (x == null) return;
  ctx.fillStyle = '#6a4a28';
  ctx.fillRect(x - 12, 380, 4, 100); ctx.fillRect(x + 8, 380, 4, 100);
  for (let y = 388; y < 476; y += 14) ctx.fillRect(x - 12, y, 24, 3);
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.fillRect(x - 40, 340, 80, 140);   // 头顶透下来的光
  ctx.fillStyle = '#ffe040'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'center';
  ctx.fillText('↑ 地面', x, 370 + Math.sin(g.time * 0.1) * 2); ctx.textAlign = 'left';
}

// ---------- 主题氛围：沼泽雾气、熔岩火星、洞穴水滴、竞技场火把、要塞月光 ----------
function drawThemeAtmosphere(g, t) {
  const tm = g.time, cam = g.camX;
  if (t.deco === 'swamp') {
    ctx.fillStyle = 'rgba(190,220,170,0.10)';
    for (let i = 0; i < 6; i++) {
      const x = ((i * 190 - cam * 0.5 + tm * 0.3) % (W + 300) + W + 300) % (W + 300) - 150;
      ctx.fillRect(x, 330 + (i % 3) * 40, 260, 26);
    }
    ctx.fillStyle = 'rgba(220,255,140,0.8)';                           // 萤火虫
    for (let i = 0; i < 14; i++) {
      ctx.globalAlpha = 0.4 + 0.6 * Math.abs(Math.sin(tm * 0.04 + i * 1.7));
      ctx.fillRect(Math.round((i * 131 - cam * 0.3 + Math.sin(tm * 0.02 + i) * 30 + W * 3) % W), 200 + (i * 37) % 200, 2, 2);
    }
    ctx.globalAlpha = 1;
  } else if (t.deco === 'lava') {
    for (let i = 0; i < 26; i++) {                                     // 向上飘的火星
      const ph = ((tm * (0.6 + (i % 5) * 0.15) + i * 41) % 260) / 260;
      ctx.globalAlpha = 1 - ph;
      ctx.fillStyle = i % 3 ? '#ff9030' : '#ffd860';
      ctx.fillRect(Math.round((i * 97 + Math.sin(tm * 0.03 + i) * 14 - cam * 0.4 + W * 3) % W), Math.round(540 - ph * 460), 2, 2);
    }
    ctx.globalAlpha = 1;
    const glow = ctx.createLinearGradient(0, H - 160, 0, H);
    glow.addColorStop(0, 'rgba(255,90,20,0)'); glow.addColorStop(1, 'rgba(255,90,20,0.25)');
    ctx.fillStyle = glow; ctx.fillRect(0, H - 160, W, 160);
  } else if (t.deco === 'cave') {
    ctx.fillStyle = 'rgba(150,200,255,0.8)';                           // 滴水
    for (let i = 0; i < 5; i++) {
      const ph = ((tm * 0.9 + i * 53) % 90) / 90;
      if (ph > 0.55) continue;
      ctx.fillRect(Math.round((i * 211 - cam * 0.6 + W * 3) % W), Math.round(ph * 520), 2, 5);
    }
    const vg = ctx.createRadialGradient(W / 2, H / 2, 160, W / 2, H / 2, 560);   // 暗角，营造压抑感
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  } else if (t.deco === 'secret') {
    ctx.fillStyle = 'rgba(255,224,120,0.9)';
    for (let i = 0; i < 24; i++) {
      ctx.globalAlpha = 0.3 + 0.7 * Math.abs(Math.sin(tm * 0.05 + i));
      ctx.fillRect((i * 127 + tm * 0.2) % W, (i * 71 + Math.sin(tm * 0.02 + i) * 20 + 540) % 440, 2, 2);
    }
    ctx.globalAlpha = 1;
  } else if (t.deco === 'arena') {
    for (const x of [90, 480, 870]) {                                  // 火把
      const f = (tm >> 2) % 3;
      ctx.fillStyle = '#4a3220'; ctx.fillRect(x - 3, 300, 6, 40);
      ctx.fillStyle = ['#ff8020', '#ffb030', '#ff6010'][f]; ctx.fillRect(x - 6, 286 - f * 2, 12, 16 + f * 2);
      ctx.fillStyle = 'rgba(255,170,60,0.12)'; ctx.beginPath(); ctx.arc(x, 300, 70, 0, 7); ctx.fill();
    }
  } else if (t.deco === 'fortress') {
    ctx.fillStyle = 'rgba(160,160,220,0.07)';                          // 斜射进来的月光
    for (let i = 0; i < 4; i++) {
      const x = i * 260 - ((cam * 0.5) % 260);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 70, 0); ctx.lineTo(x + 20, H); ctx.lineTo(x - 50, H); ctx.fill();
    }
  }
}
