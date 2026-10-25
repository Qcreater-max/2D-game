/* 离线游戏引擎（由 Python game_engine.py / combat.py / world.py / enemies.py / boss.py / physics.py 移植而来）。

   对外接口与服务器一致：
     const e = new GameEngine(seed);
     e.tick(input);                 // input: { left:false, right:true, jump:false, aim:[x,y]|null, ... }
     const level = e.level_message();   // 换关时取一次
     const state = e.get_state();       // 每帧取一次
   渲染层（render.js / ui.js）直接消费这两个对象，无需改动。 */

// ---------- 物理 ----------
function rects_overlap(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}
function has_ground_at(platforms, px, py) {
  for (const pl of platforms) {
    if (pl.x <= px && px < pl.x + pl.w && pl.y <= py && py <= pl.y + pl.h) return true;
  }
  return false;
}
function in_solid(platforms, px, py) {
  for (const pl of platforms) {
    if (pl.type === 'ground' && pl.x <= px && px <= pl.x + pl.w && pl.y <= py && py <= pl.y + pl.h) return true;
  }
  return false;
}
function move_body(b, platforms, drop) {
  b.x += b.vx;
  b.hitWall = false;
  for (const pl of platforms) {
    if (pl.type === 'ground' && rects_overlap(b, pl)) {
      if (b.vx > 0) b.x = pl.x - b.w;
      else if (b.vx < 0) b.x = pl.x + pl.w;
      b.hitWall = true;
    }
  }
  const prev_bottom = b.y + b.h;
  b.y += b.vy;
  b.onGround = false;
  let landed = null;
  for (const pl of platforms) {
    if (!rects_overlap(b, pl)) continue;
    if (pl.type === 'ground') {
      if (b.vy > 0) {
        b.y = pl.y - b.h; b.vy = 0; b.onGround = true; landed = pl;
      } else if (b.vy < 0) {
        b.y = pl.y + pl.h; b.vy = 0;
      }
    } else if (b.vy >= 0 && !drop && prev_bottom <= pl.y + 1) {
      b.y = pl.y - b.h; b.vy = 0; b.onGround = true; landed = pl;
    }
  }
  return landed;
}

const END_SCREEN_DELAY = 45;
const PORTAL_W = 48, PORTAL_H = 80;
const TOUCH_TYPES = ['slime', 'goblin', 'bat', 'bomber', 'boar'];
const r1 = v => Math.round(v * 10) / 10;
const max = Math.max, min = Math.min, floor = Math.floor, round = Math.round, abs = Math.abs;
const hypot = (a, b) => Math.hypot(a, b);
const rnd = () => Math.random();

class GameEngine {
  constructor(seed) {
    this.rng = new Random(seed == null ? 1 : seed);
    this.reset();
  }

  // ============== 初始化 ==============
  reset() {
    this.game = {
      state: 'menu', level: 0, camX: 0.0, time: 0, playTime: 0,
      flash: 0, shake: 0.0, msg: '', msgT: 0, introT: 0, fade: 0.0,
      hitstop: 0, hurtFlash: 0,
      panel: null, panelTab: 0, panelIdx: 0,
      deadReason: '', endT: 0, lastLevel: 'forest',
      kills: 0, totalDamage: 0, goldEarned: 0,
      title: '', hint: '', theme: 'forest',
      mode: 'adventure', menuIdx: 0,
      wave: 0, waveBreak: 0, bestWave: 0,
      crates: 0, secretsFound: 0, holesEntered: 0,
    };
    this.return_stack = [];
    this.prev = {}; INPUT_KEYS.forEach(k => this.prev[k] = false);
    this.aim = null;
    this.trans = null;
    this.win_timer = 0;
    this.level_seq = 0;
    this.seen = new Set(); this.card = null; this.card_q = [];
    this.new_player();
    this.load('forest');
    this.game.state = 'menu';
    this.game.introT = 0;
  }

  new_player() {
    this.player = {
      x: 60.0, y: 0.0, w: 22, h: 30, vx: 0.0, vy: 0.0,
      onGround: false, hitWall: false, standing: null, facing: 1,
      hp: 100, maxHp: 100, level: 1, exp: 0, expNext: 30, gold: 0,
      weapon: 0, armor: 0, atkCD: 0, hurtCD: 0, attackAnim: 0,
      ownedWeapons: new Set([0]), ownedArmors: new Set([0]),
      coyote: 0, jbuf: 0, dropT: 0, kbV: 0.0, lunge: 0.0, safe: [60.0, 0.0],
      standingOn: null, inPoison: false, airTop: 0.0,
    };
  }

  new_game(mode) {
    mode = mode || 'adventure';
    this.new_player();
    const g = this.game;
    Object.assign(g, { kills: 0, totalDamage: 0, goldEarned: 0, playTime: 0, flash: 0, mode,
      crates: 0, secretsFound: 0, holesEntered: 0, wave: 0, waveBreak: 0 });
    this.win_timer = 0;
    this.trans = null;
    this.return_stack = [];
    this.seen = new Set(); this.card = null; this.card_q = [];
    if (mode === 'endless') {
      this.load('arena');
      g.wave = 1;
      this.spawn_wave();
    } else {
      this.load('forest');
    }
  }

  load(name, spawn_x) {
    const d = load_level(name);
    const g = this.game, p = this.player;
    this.platforms = d.platforms; this.mapW = d.mapW;
    this.movers = d.movers;
    this.smithX = d.smithX; this.portalX = d.portalX; this.backX = d.back;
    this.portal = (d.portalX == null) ? null :
      { x: d.portalX - PORTAL_W / 2, y: GROUND_Y - PORTAL_H, w: PORTAL_W, h: PORTAL_H };
    this.chests = d.chests;
    this.hazards = d.hazards; this.crates = d.crates;
    this.holes = d.holes; this.secrets = d.secrets;
    this.enemies = d.spawns.map(s => this.make_enemy(s[0], s[1], s[2]));
    this.enemies_total = this.enemies.length;
    this.projectiles = []; this.enemyProj = [];
    this.card = null; this.card_q = [];
    this.particles = []; this.coins = []; this.texts = []; this.fx = [];
    g.hitstop = 0;
    const sx = (spawn_x == null) ? 60.0 : Number(spawn_x);
    Object.assign(p, { x: sx, y: Number(GROUND_Y - p.h - 1), vx: 0.0, vy: 0.0, kbV: 0.0, lunge: 0.0,
      onGround: true, coyote: 0, jbuf: 0, dropT: 0, atkCD: 0, hurtCD: 0, standingOn: null, inPoison: false });
    p.safe = [p.x, p.y];
    p.airTop = p.y;
    Object.assign(g, { state: name, title: d.title, hint: d.hint, theme: d.theme,
      introT: 200, panel: null, camX: max(0, min(this.mapW - W, sx - W / 2)) });
    if (LEVEL_ORDER.includes(name)) {
      g.lastLevel = name;
      g.level = LEVEL_ORDER.indexOf(name);
    }
    this.level_seq += 1;
  }

  // ============== 输入 ==============
  read_input(inp) {
    const held = {}, edge = {};
    for (const k of INPUT_KEYS) {
      held[k] = !!inp[k];
      edge[k] = held[k] && !this.prev[k];
    }
    this.prev = held;
    this.aim = (inp.aim === undefined || inp.aim === null) ? null : parse_aim(inp.aim);
    return [held, edge];
  }

  // ============== 主循环 ==============
  tick(inp) {
    const [held, edge] = this.read_input(inp);
    const g = this.game;
    g.time += 1;
    for (const k of ['msgT', 'introT', 'flash', 'hurtFlash']) {
      if (g[k] > 0) g[k] -= 1;
    }
    if (g.shake > 0) g.shake = g.shake > 0.3 ? g.shake * 0.85 : 0.0;

    const st = g.state;
    if (st === 'menu') {
      const n = MODES.length;
      if (edge.up || edge.left) g.menuIdx = (g.menuIdx - 1 + n) % n;
      if (edge.down || edge.right) g.menuIdx = (g.menuIdx + 1) % n;
      if (edge.confirm || edge.attack) this.new_game(MODES[g.menuIdx]);
    } else if (st === 'win' || st === 'dead') {
      g.endT += 1;
      if (g.endT > END_SCREEN_DELAY) {
        if (edge.confirm || edge.attack) {
          if (st === 'dead' && g.mode === 'adventure') this.retry_level();
          else this.to_menu();
        } else if (edge.escape) this.to_menu();
      }
    } else {
      this.tick_play(held, edge);
    }
    this.update_particles();
  }

  tick_play(held, edge) {
    const g = this.game;
    if (this.trans) {
      this.advance_transition();
    } else if (g.panel) {
      this.tick_panel(edge);
    } else {
      if (edge.inv) this.open_panel('inv');
      else if (edge.stats) this.open_panel('stats');
      else if (edge.interact) this.do_interact();
      if (g.panel == null && !this.trans) this.step_world(held, edge);
    }
  }

  step_world(held, edge) {
    const g = this.game;
    if (g.hitstop > 0) {
      g.hitstop -= 1;
      if (edge.jump) this.player.jbuf = 6;
      return;
    }
    g.playTime += 1;
    this.update_movers();
    this.update_player(held, edge);
    if (g.state === 'dead') return;
    this.update_hazards();
    if (g.state === 'dead') return;
    this.update_enemies();
    this.update_projectiles();
    this.update_pickups();
    this.update_cards();
    if (g.mode === 'endless') this.update_endless();
    else this.check_portal();
    const p = this.player;
    const target = max(0, min(this.mapW - W, p.x + p.w / 2 - W / 2));
    g.camX += (target - g.camX) * 0.18;
    if (this.win_timer) {
      this.win_timer -= 1;
      if (this.win_timer === 0) { g.state = 'win'; g.endT = 0; g.panel = null; }
    }
  }

  level_title() {
    const g = this.game;
    if (LEVEL_ORDER.includes(g.state)) return LEVEL_NAMES[g.level];
    if (g.mode === 'endless') return '无尽挑战  第 ' + g.wave + ' 波';
    return g.title.split('  ').slice(-1)[0];
  }

  update_cards() {
    const cam = this.game.camX;
    for (const e of this.enemies) {
      if (e.alive && !this.seen.has(e.type) && cam - 40 < e.x && e.x < cam + W + 40) {
        this.seen.add(e.type);
        this.card_q.push(e.type);
      }
    }
    if (this.card) {
      this.card.t -= this.card_q.length ? 2 : 1;
      if (this.card.t <= 0) this.card = null;
    }
    if (!this.card && this.card_q.length) {
      this.card = { type: this.card_q.shift(), t: CARD_FRAMES };
    }
  }

  to_menu() {
    this.return_stack = [];
    this.trans = null;
    this.game.mode = 'adventure';
    this.load('forest');
    this.game.state = 'menu';
    this.game.introT = 0;
  }

  retry_level() {
    this.player.hp = this.player.maxHp;
    this.win_timer = 0;
    this.return_stack = [];
    this.load(this.game.lastLevel);
    this.show_msg('重新挑战', 60);
  }

  // ============== 玩家 ==============
  update_player(held, edge) {
    const p = this.player;
    const mv = (held.right ? 1 : 0) - (held.left ? 1 : 0);
    const aim = this.aim_vector();
    if (aim && abs(aim[0]) > 0.15 && held.attack) {
      p.facing = aim[0] > 0 ? 1 : -1;
    } else if (mv) p.facing = mv;
    p.vx = mv * MOVE_SPEED + p.kbV + p.lunge;
    p.kbV = abs(p.kbV) > 0.3 ? p.kbV * 0.8 : 0.0;
    p.lunge = abs(p.lunge) > 0.2 ? p.lunge * 0.6 : 0.0;

    if (edge.jump) p.jbuf = 6;
    else if (p.jbuf > 0) p.jbuf -= 1;
    if (p.onGround) p.coyote = 6;
    else if (p.coyote > 0) p.coyote -= 1;
    if (p.jbuf > 0 && p.coyote > 0) {
      if (held.down && p.standing === 'plat') p.dropT = 12;
      else p.vy = JUMP_V;
      p.jbuf = 0; p.coyote = 0; p.onGround = false;
    } else if (!held.jump && p.vy < -3.5) p.vy = -3.5;

    p.vy = min(MAX_FALL, p.vy + GRAVITY);
    const drop = p.dropT > 0;
    if (drop) p.dropT -= 1;
    const landed = move_body(p, this.platforms, drop);
    p.standing = landed ? landed.type : null;
    p.standingOn = (landed && landed.mover) ? landed : null;
    if (landed) this.check_fall_damage();
    else p.airTop = min(p.airTop, p.y);
    p.x = max(0, min(this.mapW - p.w, p.x));
    if (landed && landed.w >= 80) {
      const sx = max(landed.x + 14, min(p.x, landed.x + landed.w - p.w - 14));
      p.safe = [sx, landed.y - p.h - 0.01];
    }

    if (p.y > H + 60) { this.fall_into_pit(); return; }
    for (const k of ['atkCD', 'attackAnim', 'hurtCD']) if (p[k] > 0) p[k] -= 1;
    if (held.attack && p.atkCD <= 0) this.player_attack();
  }

  fall_distance() {
    const p = this.player;
    return max(0.0, p.y - p.airTop);
  }

  check_fall_damage() {
    const p = this.player;
    const fall = this.fall_distance();
    p.airTop = p.y;
    if (fall <= SAFE_FALL) return;
    const pct = min(FALL_MAX_PCT, (fall - SAFE_FALL) * FALL_PCT_PER_PX);
    const dmg = max(1, Math.trunc(p.maxHp * pct));
    p.hp = max(1, p.hp - dmg);
    p.hurtCD = max(p.hurtCD, 30);
    p.kbV = 0.0; p.lunge = 0.0;
    const cx = p.x + p.w / 2, feet = p.y + p.h;
    this.game.shake = max(this.game.shake, 4 + min(8.0, dmg * 0.4));
    this.game.hurtFlash = 6;
    this.hitstop(3);
    this.add_text(p.x - 6, p.y - 8, '摔伤 -' + dmg, '#ffb060', 16);
    this.add_particles(cx, feet, 12, '#c8b890', 4);
    this.add_fx('ring', cx, feet - 2, { life: 14, color: '#c8b890' });
  }

  fall_into_pit() {
    const p = this.player;
    const dmg = max(1, Math.trunc(p.maxHp * PIT_DAMAGE_PCT));
    p.hp -= dmg;
    if (p.hp <= 0) { this.player_die('坠入深渊...'); return; }
    p.x = p.safe[0]; p.y = p.safe[1];
    p.airTop = p.y;
    p.vx = 0; p.vy = 0; p.kbV = 0;
    p.hurtCD = 90;
    this.game.shake = 8;
    this.add_text(p.x, p.y - 8, '坠落 -' + dmg, '#ff6060', 16);
    this.show_msg('掉进深坑！已送回安全位置', 80);
  }

  // ============== 子弹 / 拾取物 ==============
  update_projectiles() {
    for (const pr of this.projectiles) {
      pr.x += pr.vx; pr.y += pr.vy; pr.life -= 1;
      if (in_solid(this.platforms, pr.x, pr.y)) {
        pr.life = 0;
        this.add_particles(pr.x, pr.y, 4, pr.color, 2);
      }
      if (pr.kind === 'fire') this.add_particles(pr.x, pr.y, 1, '#ff8020', 1);
      const box = { x: pr.x - 5, y: pr.y - 5, w: 10, h: 10 };
      if (pr.life > 0 && (this.hit_crates(box) || this.hit_secrets(box))) { pr.life = 0; continue; }
      for (const e of this.enemies) {
        if (e.alive && rects_overlap(box, e)) {
          this.damage_enemy(e, pr.dmg, pr.vx > 0 ? 1 : -1, pr.heavy || false, pr.elem || 'phys');
          pr.life = 0;
          break;
        }
      }
    }
    this.projectiles = this.projectiles.filter(pr => pr.life > 0 && pr.x > -50 && pr.x < this.mapW + 50);

    const p = this.player;
    for (const pr of this.enemyProj) {
      pr.x += pr.vx; pr.y += pr.vy; pr.life -= 1;
      if (pr.grav) {
        pr.vy += pr.grav;
        if (has_ground_at(this.platforms, pr.x, pr.y)) pr.life = 0;
      }
      if (pr.kind === 'fireball') this.add_particles(pr.x, pr.y, 1, '#ff4020', 1.5);
      const box = { x: pr.x - pr.w / 2, y: pr.y - pr.h / 2, w: pr.w, h: pr.h };
      if (p.hurtCD <= 0 && rects_overlap(box, p)) {
        this.damage_player(pr.dmg, pr.x, pr.elem || 'phys');
        pr.life = 0;
      }
    }
    this.enemyProj = this.enemyProj.filter(pr => pr.life > 0 && pr.x > -60 && pr.x < this.mapW + 60 && pr.y > -60 && pr.y < H + 60);
  }

  update_pickups() {
    const p = this.player;
    const pcx = p.x + p.w / 2, pcy = p.y + p.h / 2;
    for (const c of this.coins) {
      c.t += 1;
      const dx = pcx - c.x, dy = pcy - c.y;
      const dist = hypot(dx, dy) || 1;
      if (c.t > 20 && dist < 90) {
        c.x += dx / dist * 4;
        c.y += dy / dist * 4;
      } else {
        const prev_y = c.y;
        c.vy = min(8, c.vy + 0.3);
        c.x += c.vx; c.y += c.vy;
        for (const pl of this.platforms) {
          if (pl.x <= c.x && c.x <= pl.x + pl.w && prev_y <= pl.y && pl.y <= c.y + 6) {
            c.y = pl.y - 6; c.vy = 0; c.vx = c.vx * 0.5;
          }
        }
      }
      if (abs(dx) < 24 && abs(dy) < 30) { this.collect(c); c.dead = true; }
      else if (c.t > 900 || c.y > H + 50) c.dead = true;
    }
    this.coins = this.coins.filter(c => !c.dead);
  }

  collect(c) {
    const p = this.player;
    if (c.kind === 'heart') {
      p.hp = min(p.maxHp, p.hp + c.amt);
      this.add_text(c.x, c.y - 6, '+' + c.amt + ' HP', '#60ff60', 13);
    } else {
      p.gold += c.amt;
      this.game.goldEarned += c.amt;
      this.add_text(c.x, c.y - 6, '+' + c.amt, '#ffd84a', 12);
    }
  }

  // ============== 互动 ==============
  remaining_enemies() {
    let n = 0;
    for (const e of this.enemies) if (e.alive) n += 1;
    return n;
  }

  near_portal(reach) {
    if (this.portalX == null) return false;
    return abs(this.player.x + this.player.w / 2 - this.portalX) < reach;
  }

  interact_target() {
    const p = this.player;
    const pcx = p.x + p.w / 2;
    const probe = { x: p.x - 8, y: p.y - 8, w: p.w + 16, h: p.h + 16 };
    for (const c of this.chests) if (!c.opened && rects_overlap(probe, c)) return ['chest', c];
    if (this.near_back()) return ['back', null];
    const door = this.near_secret_door();
    if (door) return ['secret', door];
    const hole = this.near_hole();
    if (hole && this.prev.down) return ['hole', hole];
    if (this.smithX != null && abs(pcx - this.smithX) < 70) return ['smith', null];
    if (this.near_portal(55)) return ['portal', null];
    return null;
  }

  do_interact() {
    const t = this.interact_target();
    if (!t) return;
    const kind = t[0];
    if (kind === 'chest') this.open_chest(t[1]);
    else if (kind === 'smith') { this.game.panel = 'shop'; this.game.panelTab = 0; this.game.panelIdx = 0; }
    else if (kind === 'hole') { this.game.holesEntered += 1; this.enter_sub(t[1].to, 'dive'); }
    else if (kind === 'secret') { this.game.secretRooms = (this.game.secretRooms || 0) + 1; this.enter_sub('secret_' + this.game.state + '_' + t[1].idx, 'door'); }
    else if (kind === 'back') this.leave_sub();
    else this.start_transition();
  }

  check_portal() {
    if (!this.trans && this.remaining_enemies() === 0 && this.near_portal(28) && this.game.state !== 'dead') {
      this.start_transition();
    }
  }

  start_transition(to, kind) {
    to = to || null; kind = kind || 'next';
    const cur = this.game.state;
    if (to == null) {
      if (!LEVEL_ORDER.includes(cur) || LEVEL_ORDER.indexOf(cur) + 1 >= LEVEL_ORDER.length) return;
      to = LEVEL_ORDER[LEVEL_ORDER.indexOf(cur) + 1];
    }
    this.trans = { t: 0, from: cur, to, kind, clear: kind === 'next' && this.remaining_enemies() === 0 };
  }

  open_chest(c) {
    c.opened = true;
    const p = this.player;
    this.add_particles(c.x + c.w / 2, c.y + c.h / 2, 25, '#ffd84a', 4);
    const [kind, val] = c.give;
    if (kind === 'gold') {
      p.gold += val;
      this.game.goldEarned += val;
      this.show_msg('获得 ' + val + ' 金币', 80);
    } else if (kind === 'weapon') {
      if (p.ownedWeapons.has(val)) { p.gold += 30; this.show_msg('已有 ' + WEAPONS[val].name + '，换成 30 金币', 90); }
      else {
        p.ownedWeapons.add(val);
        const better = weapon_power(val) > weapon_power(p.weapon);
        if (better) p.weapon = val;
        this.show_msg('获得武器：' + WEAPONS[val].name + '（' + (better ? '已装备' : '已放入背包') + '）', 110);
      }
    } else {
      if (p.ownedArmors.has(val)) { p.gold += 30; this.show_msg('已有 ' + ARMORS[val].name + '，换成 30 金币', 90); }
      else {
        p.ownedArmors.add(val);
        const better = ARMORS[val].reduce > ARMORS[p.armor].reduce;
        if (better) p.armor = val;
        this.show_msg('获得盔甲：' + ARMORS[val].name + '（' + (better ? '已装备' : '已放入背包') + '）', 110);
      }
    }
  }

  // ============== 关卡切换 ==============
  advance_transition() {
    const t = this.trans, g = this.game;
    t.t += 1;
    if (t.t === 30) this.finish_transition();
    if (t.t >= 60) { this.trans = null; g.fade = 0.0; }
    else g.fade = t.t <= 30 ? t.t / 30.0 : (60 - t.t) / 30.0;
  }

  finish_transition() {
    const t = this.trans, p = this.player;
    if (t.kind === 'back') {
      const saved = this.return_stack.pop();
      this.load(saved.level, saved.x);
      this.chests = saved.chests; this.enemies = saved.enemies; this.crates = saved.crates;
      this.secrets = saved.secrets; this.hazards = saved.hazards; this.holes = saved.holes;
      this.enemies_total = max(this.enemies_total, this.enemies.filter(e => e.alive).length);
      this.game.introT = 0;
      return;
    }
    this.load(t.to);
    if (t.kind === 'dive' || t.kind === 'door') { this.game.introT = 160; return; }
    p.hp = min(p.maxHp, p.hp + Math.trunc(p.maxHp * 0.3));
    if (t.clear) {
      const bonus = LEVEL_CLEAR_EXP[t.from];
      this.gain_exp(bonus);
      this.show_msg('全部敌人已清除，额外经验 +' + bonus, 130);
    }
  }

  // ============== 面板 ==============
  open_panel(name) {
    const g = this.game, p = this.player;
    g.panel = name; g.panelTab = 0; g.panelIdx = 0;
    if (name === 'inv') g.panelIdx = this.owned_list(0).indexOf(p.weapon);
  }

  owned_list(tab) {
    const p = this.player;
    const s = tab === 0 ? p.ownedWeapons : p.ownedArmors;
    return Array.from(s).sort((a, b) => a - b);
  }

  tick_panel(edge) {
    const g = this.game, panel = g.panel;
    if (edge.escape || (panel === 'shop' && edge.interact)) { g.panel = null; return; }
    if (panel === 'inv' || panel === 'stats') {
      if (edge.inv) { if (panel === 'inv') g.panel = null; else this.open_panel('inv'); return; }
      if (edge.stats) { if (panel === 'stats') g.panel = null; else this.open_panel('stats'); return; }
    }
    if (panel === 'stats') return;
    if (edge.left || edge.right) { g.panelTab = edge.left ? 0 : 1; g.panelIdx = 0; }
    const n = panel === 'shop' ? (g.panelTab === 0 ? WEAPONS.length : ARMORS.length) : this.owned_list(g.panelTab).length;
    if (edge.up) g.panelIdx = max(0, g.panelIdx - 1);
    if (edge.down) g.panelIdx = min(n - 1, g.panelIdx + 1);
    if (edge.confirm || edge.attack) {
      if (panel === 'shop') this.buy_item(g.panelTab, g.panelIdx);
      else this.equip(g.panelTab, this.owned_list(g.panelTab)[g.panelIdx]);
    }
  }

  equip(tab, idx) {
    const p = this.player;
    if (tab === 0) { p.weapon = idx; this.show_msg('已装备 ' + WEAPONS[idx].name, 60); }
    else { p.armor = idx; this.show_msg('已装备 ' + ARMORS[idx].name, 60); }
  }

  buy_item(tab, idx) {
    const p = this.player;
    const table = tab === 0 ? WEAPONS : ARMORS;
    const owned = tab === 0 ? p.ownedWeapons : p.ownedArmors;
    const item = table[idx];
    if (owned.has(idx)) this.equip(tab, idx);
    else if (p.gold >= item.price) {
      p.gold -= item.price;
      owned.add(idx);
      this.equip(tab, idx);
      this.show_msg('购买并装备 ' + item.name, 80);
      this.add_particles(p.x + p.w / 2, p.y, 15, item.color, 3);
    } else this.show_msg('金币不足，还差 ' + (item.price - p.gold), 70);
  }

  // ============== 粒子 / 飘字 ==============
  update_particles() {
    for (const q of this.particles) { q.x += q.vx; q.y += q.vy; q.vy += 0.15; q.life -= 1; }
    this.particles = this.particles.filter(q => q.life > 0);
    this.update_fx();
    for (const t of this.texts) { t.y += t.vy; t.t -= 1; }
    this.texts = this.texts.filter(t => t.t > 0);
  }

  // ============== 状态序列化 ==============
  level_message() {
    const static_ = this.platforms.filter(pl => !pl.mover);
    return { t: 'level', seq: this.level_seq, mapW: this.mapW, platforms: static_,
      smithX: this.smithX, portal: this.portal, hazards: this.hazards, backX: this.backX,
      theme: this.game.theme, catalog: CATALOG };
  }

  prompt() {
    const g = this.game;
    if (g.panel || this.trans || ['menu', 'dead', 'win'].includes(g.state)) return null;
    const p = this.player;
    const pcx = p.x + p.w / 2;
    const t = this.interact_target();
    if (t == null) {
      const hole = this.near_hole();
      if (hole) return { x: hole.x, y: GROUND_Y - 60, text: '按住 S 再按 E 进入地洞' };
      for (const s of this.secrets) {
        if (!s.open && abs(pcx - s.x) < 70) return { x: s.x, y: GROUND_Y - 110, text: '这面墙有裂缝…攻击它试试' };
      }
      return null;
    }
    const kind = t[0];
    if (kind === 'chest') { const c = t[1]; return { x: c.x + c.w / 2, y: c.y - 14, text: '按 E 开启宝箱' }; }
    if (kind === 'smith') return { x: this.smithX, y: 322, text: '按 E 进入铁匠铺' };
    if (kind === 'hole') return { x: t[1].x, y: GROUND_Y - 60, text: '按 E 进入地洞' };
    if (kind === 'secret') return { x: t[1].x, y: GROUND_Y - 110, text: '按 E 进入隐藏房间' };
    if (kind === 'back') return { x: this.backX, y: GROUND_Y - 110, text: '按 E 返回地面' };
    const left = this.remaining_enemies();
    const text = left === 0 ? '进入下一关' : '还有 ' + left + ' 只敌人，按 E 强行进入';
    return { x: this.portalX, y: GROUND_Y - PORTAL_H - 26, text };
  }

  get_state() {
    const g = this.game, p = this.player;
    let boss = null;
    for (const e of this.enemies) if (e.boss && e.alive) { boss = e; break; }
    return {
      t: 'state',
      seq: this.level_seq,
      game: {
        state: g.state, level: g.level, levelName: this.level_title(),
        camX: r1(g.camX), time: g.time, playTime: g.playTime,
        msg: g.msg, msgT: g.msgT, introT: g.introT, title: g.title, hint: g.hint,
        flash: g.flash, shake: r1(g.shake), fade: r1(g.fade),
        hitstop: g.hitstop, hurtFlash: g.hurtFlash,
        panel: g.panel, panelTab: g.panelTab, panelIdx: g.panelIdx,
        deadReason: g.deadReason, endT: g.endT,
        kills: g.kills, totalDamage: g.totalDamage, goldEarned: g.goldEarned,
        enemiesLeft: this.remaining_enemies(), enemiesTotal: this.enemies_total,
        theme: g.theme, mode: g.mode, menuIdx: g.menuIdx,
        wave: g.wave, waveBreak: g.waveBreak, bestWave: g.bestWave,
        depth: this.return_stack.length, inPoison: p.inPoison,
        crates: g.crates, secretsFound: g.secretsFound,
      },
      player: {
        x: r1(p.x), y: r1(p.y), w: p.w, h: p.h, vx: r1(p.vx), vy: r1(p.vy),
        onGround: p.onGround, facing: p.facing, hp: p.hp, maxHp: p.maxHp, level: p.level,
        exp: p.exp, expNext: p.expNext, gold: p.gold, weapon: p.weapon, armor: p.armor,
        hurtCD: p.hurtCD, attackAnim: p.attackAnim, atkCD: p.atkCD, aim: this.aim_angle(),
        fallDanger: this.fall_distance() > SAFE_FALL,
        ownedWeapons: Array.from(p.ownedWeapons).sort((a, b) => a - b),
        ownedArmors: Array.from(p.ownedArmors).sort((a, b) => a - b),
      },
      enemies: this.enemies.map(e => ({
        type: e.type, x: r1(e.x), y: r1(e.y), w: e.w, h: e.h, hp: e.hp, maxHp: e.maxHp,
        dir: e.dir, color: e.color, hurtT: e.hurtT, alive: e.alive, dying: e.dying,
        mode: e.mode, modeT: e.modeT, boss: e.boss, fly: e.fly, burn: e.burn, slow: e.slow, weak: e.weak,
      })),
      card: this.card ? { type: this.card.type, t: this.card.t, total: CARD_FRAMES } : null,
      boss: boss ? { hp: boss.hp, maxHp: boss.maxHp, mode: boss.mode, enraged: boss.hp < boss.maxHp * 0.5 } : null,
      projectiles: this.projectiles.map(q => ({ x: r1(q.x), y: r1(q.y), vx: r1(q.vx), vy: r1(q.vy), kind: q.kind, color: q.color })),
      enemyProj: this.enemyProj.map(q => ({ x: r1(q.x), y: r1(q.y), w: q.w, h: q.h, vx: r1(q.vx), vy: r1(q.vy), kind: q.kind, color: q.color })),
      particles: this.particles.map(q => [r1(q.x), r1(q.y), q.size, Math.trunc(q.life), q.color]),
      coins: this.coins.map(c => ({ x: r1(c.x), y: r1(c.y), kind: c.kind, t: c.t })),
      chests: this.chests.map(c => ({ x: c.x, y: c.y, w: c.w, h: c.h, opened: c.opened })),
      movers: this.movers.map(m => ({ x: r1(m.plat.x), y: m.plat.y, w: m.plat.w, h: m.plat.h })),
      crates: this.crates.filter(c => c.hp > 0).map(c => ({ x: c.x, y: c.y, w: c.w, h: c.h, hp: c.hp })),
      holes: this.holes.map(h => ({ x: h.x })),
      secrets: this.secrets.map(s => ({ x: s.x, hp: s.hp, maxHp: s.maxHp, open: s.open })),
      texts: this.texts.map(t => ({ x: r1(t.x), y: r1(t.y), txt: t.txt, color: t.color, size: t.size, t: t.t })),
      fx: this.fx,
      prompt: this.prompt(),
    };
  }

  // ============== 战斗:特效 ==============
  add_text(x, y, txt, color, size) {
    size = size || 16;
    this.texts.push({ x, y, txt, color, size, t: 60, vy: -1.2 });
  }

  add_particles(x, y, n, color, spd) {
    spd = spd || 3;
    for (let i = 0; i < n; i++) {
      if (this.particles.length >= MAX_PARTICLES) return;
      const a = rnd() * Math.PI * 2, s = rnd() * spd + 1;
      this.particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 1,
        life: 30 + rnd() * 20, color, size: 2 + Math.floor(rnd() * 3) });
    }
  }

  show_msg(text, frames) { this.game.msg = text; this.game.msgT = frames || 90; }
  hitstop(frames) { this.game.hitstop = max(this.game.hitstop, frames); }

  add_fx(kind, x, y, kw) {
    kw = kw || {};
    if (this.fx.length >= MAX_FX) this.fx.shift();
    const fx = { kind, x: r1(x), y: r1(y), t: 0, ...kw };
    this.fx.push(fx);
  }

  add_blast(x, y, radius) {
    this.add_fx('blast', x, y, { r: radius, life: 22 });
    this.add_particles(x, y, 36, '#ff9030', 8);
    this.add_particles(x, y, 16, '#ffe080', 5);
    this.game.shake = max(this.game.shake, 10);
    this.hitstop(4);
  }

  update_fx() {
    for (const f of this.fx) f.t += 1;
    this.fx = this.fx.filter(f => f.t < (f.life || 12));
  }

  // ============== 战斗:数值 ==============
  atk_mul() { return 1 + 0.06 * (this.player.level - 1); }

  gain_exp(n) {
    const p = this.player;
    p.exp += n;
    while (p.exp >= p.expNext) {
      p.exp -= p.expNext;
      p.level += 1;
      p.expNext = Math.trunc(p.expNext * 1.45);
      p.maxHp += 15;
      p.hp = p.maxHp;
      this.game.flash = 30;
      this.add_particles(p.x + p.w / 2, p.y + p.h / 2, 50, '#ffd84a', 7);
      this.add_text(p.x - 10, p.y - 10, 'LEVEL UP!', '#ffe040', 22);
      this.show_msg('升级！生命上限+15，攻击力提升，生命已回满', 120);
    }
  }

  aim_vector() {
    if (this.aim == null) return null;
    const p = this.player;
    const ox = p.x + p.w / 2, oy = p.y + p.h / 2 - 4;
    const dx = this.aim[0] + this.game.camX - ox;
    const dy = this.aim[1] - oy;
    const d = hypot(dx, dy);
    if (d < 6) return null;
    return [dx / d, dy / d];
  }

  aim_angle() {
    const v = this.aim_vector();
    return v == null ? null : round(Math.atan2(v[1], v[0]) * 100) / 100;
  }

  player_attack() {
    const p = this.player;
    const w = WEAPONS[p.weapon];
    p.atkCD = w.cd; p.attackAnim = 12;
    const dmg = Math.round(w.dmg * this.atk_mul());
    const elem = w.elem;
    if (w.type === 'melee') {
      const hx = p.facing > 0 ? p.x + p.w : p.x - w.range;
      const box = { x: hx, y: p.y - 4, w: w.range, h: p.h + 8 };
      let hit = false;
      for (const e of this.enemies) {
        if (e.alive && rects_overlap(box, e)) {
          this.damage_enemy(e, dmg, p.facing, w.heavy || false, elem);
          hit = true;
        }
      }
      hit = this.hit_crates(box) || hit;
      hit = this.hit_secrets(box) || hit;
      p.lunge = p.facing * (hit ? 3.0 : 1.6);
      if (hit) this.game.shake = max(this.game.shake, 3);
    } else {
      const speed = w.projSpeed;
      const av = this.aim_vector();
      const ux = av ? av[0] : (p.facing > 0 ? 1 : -1), uy = av ? av[1] : 0.0;
      this.projectiles.push({
        x: p.x + p.w / 2 + ux * 16, y: p.y + p.h / 2 - 4 + uy * 16,
        vx: ux * speed, vy: uy * speed, dmg, life: w.range / speed,
        color: w.color, heavy: w.heavy || false, elem, kind: elem === 'fire' ? 'fire' : 'arrow',
      });
    }
  }

  // ============== 战斗:伤害结算 ==============
  blocked_by_shield(e, kdir, elem, pierce) {
    return (e.type === 'shield' && e.mode !== 'stun' && kdir !== 0 && kdir === -e.dir && elem !== 'thunder' && !pierce);
  }

  calc_damage(e, dmg, elem, crit, stunned) {
    let mult = 1.0, tag = null;
    if (e.weak === elem) { mult = WEAK_MULT; tag = 'weak'; }
    else if (e.resist === elem) { mult = RESIST_MULT; tag = 'resist'; }
    const pre = dmg * mult * (crit ? 2 : 1) * (stunned ? 1.5 : 1);
    const final = max(pre * MIN_DMG_RATIO, pre - e.def);
    return [max(1, Math.round(final)), tag];
  }

  damage_enemy(e, dmg, kdir, heavy, elem, opts) {
    kdir = kdir || 0; heavy = heavy || false; elem = elem || 'phys';
    opts = opts || {};
    const chain = opts.chain !== false, dot = !!opts.dot, pierce = !!opts.pierce, silent_crit = !!opts.silent_crit;
    const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
    const ecol = ELEMENTS[elem].color;
    if (!pierce && this.blocked_by_shield(e, kdir, elem)) {
      if (heavy) {
        e.mode = 'stun'; e.modeT = 0;
        this.add_fx('ring', cx - kdir * 8, cy, { life: 14, color: '#ffe080' });
        this.add_text(e.x, e.y - 10, '破盾！', '#ffe080', 16);
        this.game.shake = max(this.game.shake, 6);
        this.hitstop(HITSTOP_CRIT);
      } else {
        e.kb = kdir * 1.5;
        this.add_fx('spark', cx - kdir * 10, cy, { life: 8, dir: -kdir, color: '#bcd0ff' });
        this.add_text(e.x, e.y - 6, '格挡', '#9ab0e0', 13);
        this.hitstop(1);
        return;
      }
    }
    const crit = !silent_crit && this.rng.random() < 0.1;
    const [final, tag] = this.calc_damage(e, dmg, elem, crit, e.mode === 'stun');
    e.hp -= final;
    e.hurtT = 8;
    if (kdir && !e.boss) e.kb = kdir * (crit ? 6.0 : 4.5);
    this.game.totalDamage += final;
    let label = (crit ? '暴击 ' : '') + (tag === 'weak' ? '弱点 ' : tag === 'resist' ? '抗性 ' : '') + '-' + final;
    const color = elem !== 'phys' ? ecol : (crit ? '#ffd040' : PHYS_COLOR);
    const size = (crit || tag === 'weak') ? 18 : (dot ? 12 : 14);
    this.add_text(e.x, e.y - 4, label, color, size);
    this.add_particles(cx, cy, 5, elem === 'phys' ? e.color : ecol, 3);
    if (!dot) {
      if (kdir || crit) {
        this.add_fx('spark', cx, cy, { life: 9, dir: kdir || 1, color: elem !== 'phys' ? ecol : '#fff4c0', big: crit });
        const stop = crit ? HITSTOP_CRIT : (tag === 'weak' ? HITSTOP_HIT + 1 : HITSTOP_HIT);
        this.hitstop(stop);
        if (crit) this.game.shake = max(this.game.shake, 7);
      }
      if (crit || tag === 'weak') this.add_fx('ring', cx, cy, { life: 14, color: elem !== 'phys' ? ecol : '#ffd040' });
    }
    if (e.hp <= 0) this.kill_enemy(e);
    else if (!dot) this.apply_status(e, elem, dmg);
    if (elem === 'thunder' && chain && !dot) this.chain_lightning(e, dmg);
  }

  apply_status(e, elem, base_dmg) {
    if (elem === 'fire' && e.resist !== 'fire') {
      if (e.burn <= 0) this.add_text(e.x, e.y - 22, '燃烧', ELEMENTS.fire.color, 12);
      e.burn = BURN_FRAMES;
      e.burnDmg = max(2, Math.trunc(base_dmg * 0.2));
    } else if (elem === 'ice' && !e.boss && e.resist !== 'ice') {
      if (e.slow <= 0) this.add_text(e.x, e.y - 22, '减速', ELEMENTS.ice.color, 12);
      e.slow = SLOW_FRAMES;
    }
  }

  chain_lightning(src, base_dmg) {
    const cx = src.x + src.w / 2, cy = src.y + src.h / 2;
    let best = null, best_d = CHAIN_RANGE;
    for (const o of this.enemies) {
      if (o === src || !o.alive) continue;
      const d = hypot(o.x + o.w / 2 - cx, o.y + o.h / 2 - cy);
      if (d < best_d) { best = o; best_d = d; }
    }
    if (best == null) return;
    this.add_fx('bolt', cx, cy, { x2: r1(best.x + best.w / 2), y2: r1(best.y + best.h / 2), life: 10 });
    this.damage_enemy(best, max(1, Math.trunc(base_dmg * CHAIN_RATIO)), 0, false, 'thunder', { silent_crit: true, chain: false });
  }

  kill_enemy(e) {
    e.alive = false; e.dying = 18; e.hp = 0; e.burn = 0; e.slow = 0;
    if (e.type === 'bomber' && !e.exploded) this.explode(e);
    const g = this.game, p = this.player;
    g.kills += 1;
    g.goldEarned += e.gold;
    p.gold += e.gold;
    this.gain_exp(e.exp);
    const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
    this.add_text(e.x, e.y - 12, '+' + e.gold + '金', '#ffd84a', 12);
    this.add_particles(cx, cy, 20, e.color, 5);
    const r = this.rng.random();
    if (r < 0.15) this.spawn_drop(cx, cy, 'heart', 15);
    else if (r < 0.40) this.spawn_drop(cx, cy, 'gold', 3 + Math.floor(this.rng.random() * 4));
    if (e.boss) {
      this.win_timer = 150;
      this.enemyProj = [];
      this.add_particles(cx, cy, 80, '#c040ff', 9);
    }
  }

  spawn_drop(x, y, kind, amt) {
    this.coins.push({ kind, amt, x, y, t: 0, vx: (this.rng.random() - 0.5) * 2, vy: -4 });
  }

  damage_player(dmg, from_x, elem) {
    const p = this.player;
    if (p.hurtCD > 0 || this.trans || this.win_timer) return;
    from_x = from_x || null; elem = elem || 'phys';
    const armor = ARMORS[p.armor];
    const res = armor.res[elem] || 0;
    const real = max(1, Math.round(dmg * (1 - armor.reduce / 100.0) * (1 - res / 100.0)));
    p.hp -= real;
    p.hurtCD = 50;
    if (from_x != null) {
      p.kbV = p.x + p.w / 2 > from_x ? 5.0 : -5.0;
      p.vy = min(p.vy, -3.5);
    }
    this.game.shake = max(this.game.shake, 7);
    this.game.hurtFlash = 8;
    this.hitstop(HITSTOP_HURT);
    const tag = res > 0 ? ' 抗性' : (res < 0 ? ' 易伤' : '');
    this.add_text(p.x, p.y - 6, '-' + real + tag, elem !== 'phys' ? ELEMENTS[elem].color : '#ff4040', 16);
    this.add_particles(p.x + p.w / 2, p.y + p.h / 2, 8, elem !== 'phys' ? ELEMENTS[elem].color : '#ff4040', 3);
    this.add_fx('ring', p.x + p.w / 2, p.y + p.h / 2, { life: 12, color: elem !== 'phys' ? ELEMENTS[elem].color : '#ff6060' });
    if (p.hp <= 0) this.player_die('你被击败了');
  }

  player_die(reason) {
    this.player.hp = 0;
    const g = this.game;
    g.deadReason = reason; g.endT = 0; g.panel = null;
    g.state = 'dead';
    this.trans = null;
  }

  // ============== 世界机制 ==============
  update_movers() {
    const t = this.game.playTime;
    const p = this.player;
    for (const m of this.movers) {
      const pl = m.plat;
      const nx = m.x0 + Math.sin(t * 2 * Math.PI / m.period) * m.amp;
      const dx = nx - pl.x;
      pl.x = nx;
      pl.dx = dx;
      if (p.standingOn === pl) p.x += dx;
    }
  }

  update_hazards() {
    const p = this.player;
    const body = { x: p.x + 3, y: p.y + p.h - 10, w: p.w - 6, h: 10 };
    let in_poison = false;
    for (const h of this.hazards) {
      const box = { x: h.x, y: h.y, w: h.w, h: h.h };
      if (!rects_overlap(body, box)) continue;
      const d = HAZARD_DEFS[h.kind];
      if (h.kind === 'poison') {
        in_poison = true;
        if (this.game.playTime % d.tick === 0) this.hurt_by_hazard(d, false);
      } else if (p.hurtCD <= 0) this.hurt_by_hazard(d, true);
    }
    p.inPoison = in_poison;
  }

  hurt_by_hazard(d, knock) {
    const p = this.player;
    const dmg = max(1, Math.trunc(p.maxHp * d.pct));
    const armor = ARMORS[p.armor];
    const res = armor.res[d.elem] || 0;
    const real = max(1, Math.round(dmg * (1 - res / 100.0)));
    p.hp -= real;
    p.hurtCD = knock ? 40 : p.hurtCD;
    const col = d.elem !== 'phys' ? ELEMENTS[d.elem].color : '#c0ff80';
    this.add_text(p.x, p.y - 6, '-' + real + ' ' + d.name, col, 14);
    this.add_particles(p.x + p.w / 2, p.y + p.h, 6, col, 3);
    if (knock) {
      p.vy = -HAZARD_KNOCK;
      this.game.shake = max(this.game.shake, 6);
      this.game.hurtFlash = 6;
      this.hitstop(3);
    }
    if (p.hp <= 0) this.player_die('倒在了' + d.name + '里');
  }

  hit_crates(box) {
    let hit = false;
    for (const c of this.crates) {
      if (c.hp > 0 && rects_overlap(box, c)) {
        c.hp -= 1;
        hit = true;
        const cx = c.x + c.w / 2, cy = c.y + c.h / 2;
        this.add_particles(cx, cy, 6, '#a07030', 3);
        if (c.hp <= 0) this.break_crate(c, cx, cy);
      }
    }
    return hit;
  }

  break_crate(c, cx, cy) {
    this.add_particles(cx, cy, 16, '#8a5a28', 4);
    const r = this.rng.random();
    if (r < CRATE_DROPS[0]) this.spawn_drop(cx, cy, 'gold', 4 + Math.floor(this.rng.random() * 6));
    else if (r < CRATE_DROPS[0] + CRATE_DROPS[1]) this.spawn_drop(cx, cy, 'heart', 12);
    this.game.crates = (this.game.crates || 0) + 1;
  }

  hit_secrets(box, dmg_hint) {
    for (const s of this.secrets) {
      if (s.open) continue;
      const wall = { x: s.x - 16, y: GROUND_Y - 90, w: 32, h: 90 };
      if (rects_overlap(box, wall)) {
        s.hp -= 1;
        this.add_particles(s.x, GROUND_Y - 45, 8, '#a89888', 3);
        this.add_fx('ring', s.x, GROUND_Y - 45, { life: 10, color: '#cdbba8' });
        this.game.shake = max(this.game.shake, 3);
        if (s.hp <= 0) {
          s.open = true;
          this.add_particles(s.x, GROUND_Y - 45, 30, '#a89888', 6);
          this.add_text(s.x - 30, GROUND_Y - 100, '墙裂开了！', '#ffe040', 18);
          this.show_msg('墙后面有一个隐藏的入口', 100);
          this.game.secretsFound = (this.game.secretsFound || 0) + 1;
        }
        return true;
      }
    }
    return false;
  }

  near_hole() {
    const pcx = this.player.x + this.player.w / 2;
    for (const h of this.holes) if (abs(pcx - h.x) < 36) return h;
    return null;
  }

  near_secret_door() {
    const pcx = this.player.x + this.player.w / 2;
    for (const s of this.secrets) if (s.open && abs(pcx - s.x) < 36) return s;
    return null;
  }

  near_back() {
    if (this.backX == null) return false;
    return abs(this.player.x + this.player.w / 2 - this.backX) < 50;
  }

  enter_sub(name, kind) {
    const p = this.player;
    const cur = this.game.state;
    this.return_stack.push({ level: cur, x: p.x, chests: this.chests, enemies: this.enemies,
      crates: this.crates, secrets: this.secrets, coins: this.coins, hazards: this.hazards, holes: this.holes });
    this.start_transition(name, kind);
  }

  leave_sub() {
    this.start_transition(this.return_stack[this.return_stack.length - 1].level, 'back');
  }

  endless_enemy_pool(wave) {
    const pool = ['slime', 'goblin'];
    if (wave >= 2) pool.push('archer', 'bomber');
    if (wave >= 4) pool.push('boar', 'skeleton');
    if (wave >= 6) pool.push('shield', 'bat');
    return pool;
  }

  spawn_wave() {
    const g = this.game;
    const wave = g.wave;
    const n = min(14, 3 + wave * 2);
    const pool = this.endless_enemy_pool(wave);
    const mul_hp = 1 + 0.12 * (wave - 1);
    const spawns = [];
    for (let i = 0; i < n; i++) {
      const t = this.rng.choice(pool);
      const x = this.rng.choice([60, 140, 760, 840]) + this.rng.randint(-20, 20);
      const d = ENEMY_DEFS[t];
      const y = d.fly ? 120 : GROUND_Y - d.h - 1;
      const en = this.make_enemy(t, x, y);
      en.hp = en.maxHp = Math.trunc(en.maxHp * mul_hp);
      en.gold = Math.trunc(en.gold * (1 + 0.05 * wave));
      this.enemies.push(en);
      spawns.push(t);
    }
    this.enemies_total = this.enemies.filter(e => e.alive).length;
    g.waveBreak = 0;
    this.show_msg('第 ' + wave + ' 波  敌人 ' + n + ' 只', 120);
  }

  update_endless() {
    const g = this.game;
    if (this.remaining_enemies() > 0) return;
    g.waveBreak += 1;
    if (g.waveBreak === 1) {
      g.bestWave = max(g.bestWave || 0, g.wave);
      const p = this.player;
      const bonus = 20 + g.wave * 8;
      p.gold += bonus;
      g.goldEarned += bonus;
      p.hp = min(p.maxHp, p.hp + Math.trunc(p.maxHp * 0.25));
      this.add_text(p.x - 20, p.y - 20, '第' + g.wave + '波完成 +' + bonus, '#ffe040', 16);
    }
    if (g.waveBreak >= ENDLESS_WAVE_BREAK) { g.wave += 1; this.spawn_wave(); }
  }

  // ============== 敌人与首领 ==============
  make_enemy(etype, x, y) {
    const d = ENEMY_DEFS[etype];
    return {
      type: etype, x: Number(x), y: Number(y), vx: 0.0, vy: 0.0,
      w: d.w, h: d.h, hp: d.hp, maxHp: d.hp, dmg: d.dmg, exp: d.exp, gold: d.gold, color: d.color,
      fly: !!d.fly, boss: etype === 'wizard', dir: -1, atkCD: 60, hurtT: 0, dying: 0, alive: true,
      onGround: false, hitWall: false, aiT: this.rng.randint(0, 60), homeX: Number(x),
      kb: 0.0, mode: 'idle', modeT: 0, def: d.def, weak: d.weak, resist: d.resist, atkElem: d.atk,
      burn: 0, burnDmg: 0, slow: 0,
    };
  }

  update_enemies() {
    const p = this.player;
    for (const e of this.enemies) {
      if (!e.alive) { e.dying -= 1; continue; }
      e.aiT += 1;
      e.hurtT = max(0, e.hurtT - 1);
      if (e.burn > 0) {
        e.burn -= 1;
        if (e.burn % BURN_TICK === 0) {
          this.damage_enemy(e, e.burnDmg, 0, false, 'fire', { silent_crit: true, dot: true });
          if (!e.alive) continue;
        }
      }
      if (e.slow > 0) e.slow -= 1;
      this['ai_' + e.type](e, p);
      this.move_enemy(e);
      const touching = TOUCH_TYPES.includes(e.type) || (e.type === 'wizard' && e.mode === 'fall');
      if (e.alive && touching && rects_overlap(p, e)) this.damage_player(e.dmg, e.x + e.w / 2, e.atkElem);
    }
    this.enemies = this.enemies.filter(e => e.alive || e.dying > 0);
  }

  move_enemy(e) {
    const ai_vx = e.vx, ai_vy = e.vy;
    const f = e.slow > 0 ? SLOW_FACTOR : 1.0;
    e.vx = ai_vx * f + e.kb;
    e.kb = abs(e.kb) > 0.2 ? e.kb * 0.8 : 0.0;
    if (e.fly) {
      e.hitWall = false;
      e.x += e.vx;
      e.y = max(30, min(GROUND_Y - e.h, e.y + ai_vy * f));
    } else {
      e.vy = min(MAX_FALL, e.vy + GRAVITY);
      move_body(e, this.platforms);
    }
    e.vx = ai_vx;
    if (e.x < 0 || e.x + e.w > this.mapW) {
      e.x = max(0, min(this.mapW - e.w, e.x));
      e.hitWall = true;
    }
    if (e.y > H + 100) { e.alive = false; e.dying = 0; }
  }

  can_step(e, d) {
    const ax = d > 0 ? e.x + e.w + 4 : e.x - 4;
    return has_ground_at(this.platforms, ax, e.y + e.h + 6);
  }

  patrol(e, speed, radius) {
    const off = e.x - e.homeX;
    if (abs(off) > radius) e.dir = off > 0 ? -1 : 1;
    else if (e.hitWall || (e.onGround && !this.can_step(e, e.dir))) e.dir = -e.dir;
    e.vx = e.dir * speed;
  }

  enemy_shot(e, kind, vx, vy, w, h, life, color, y, elem) {
    if (y == null) y = e.y + 10;
    elem = elem || { fireball: 'fire', wave: 'thunder' }[kind] || e.atkElem;
    this.enemyProj.push({ kind, x: e.x + e.w / 2, y, vx, vy, w, h, dmg: e.dmg, life, color, elem });
  }

  ai_slime(e, p) {
    this.patrol(e, 0.7, 120);
    if (e.onGround && e.aiT % 70 === 0) e.vy = -5.5;
  }

  ai_goblin(e, p) {
    const dx = p.x - e.x, dy = p.y - e.y;
    e.atkCD -= 1;
    if (abs(dx) < 280 && abs(dy) < 130) {
      e.dir = dx > 0 ? 1 : -1;
      const safe = !e.onGround || this.can_step(e, e.dir);
      e.vx = (safe && abs(dx) > 6) ? e.dir * 1.5 : 0;
      const wants_jump = e.hitWall || (dy < -50 && abs(dx) < 70);
      if (e.onGround && wants_jump && e.atkCD <= 0) { e.vy = -8.5; e.atkCD = 45; }
    } else this.patrol(e, 0.6, 90);
  }

  ai_skeleton(e, p) {
    const dx = p.x - e.x;
    e.atkCD -= 1;
    if (abs(dx) >= 420) { this.patrol(e, 0.5, 100); return; }
    e.dir = dx > 0 ? 1 : -1;
    let want = abs(dx) > 210 ? e.dir : (abs(dx) < 110 ? -e.dir : 0);
    if (want && e.onGround && !this.can_step(e, want)) want = 0;
    e.vx = want * 0.9;
    if (abs(dx) < 340 && abs(p.y - e.y) < 90 && e.atkCD <= 0) {
      e.atkCD = 120;
      this.enemy_shot(e, 'bone', e.dir * 3.2, 0, 10, 6, 110, '#e0e0c0');
    }
  }

  ai_bat(e, p) {
    const px = p.x + p.w / 2, py = p.y + p.h / 2;
    if (e.mode === 'dive') {
      e.modeT -= 1;
      if (e.modeT <= 0) { e.mode = 'idle'; e.atkCD = 90; }
    } else {
      const tx = px + Math.sin(e.aiT * 0.03) * 140, ty = py - 95;
      const d = hypot(tx - e.x, ty - e.y) || 1;
      e.vx = (tx - e.x) / d * 1.6; e.vy = (ty - e.y) / d * 1.6;
      e.atkCD -= 1;
      if (e.atkCD <= 0 && abs(px - e.x) < 320) {
        const d2 = hypot(px - e.x, py - e.y) || 1;
        e.vx = (px - e.x) / d2 * 3.4; e.vy = (py - e.y) / d2 * 3.4;
        e.mode = 'dive'; e.modeT = 36;
      }
    }
    e.dir = e.vx >= 0 ? 1 : -1;
  }

  ai_archer(e, p) {
    const dx = p.x - e.x;
    e.atkCD -= 1;
    if (abs(dx) > 520) { this.patrol(e, 0.5, 80); return; }
    e.dir = dx > 0 ? 1 : -1;
    let want = 0;
    if (abs(dx) < 200) want = -e.dir;
    else if (abs(dx) > 330) want = e.dir;
    if (want && e.onGround && !this.can_step(e, want)) want = 0;
    e.vx = want * 1.1;
    if (abs(dx) < 140 && e.onGround && e.aiT % 90 === 0) e.vy = -7;
    if (e.atkCD <= 0 && abs(dx) < 460 && e.onGround) {
      e.atkCD = 105;
      const t = max(25.0, min(60.0, abs(dx) / 5.0));
      const vy = -(0.12 * t) / 2 + (p.y - e.y) / t;
      this.enemy_shot(e, 'arrow', e.dir * abs(dx) / t, vy, 14, 5, Math.trunc(t) + 30, '#c8a060', e.y + 8);
      this.enemyProj[this.enemyProj.length - 1].grav = 0.12;
    }
  }

  ai_bomber(e, p) {
    const dx = p.x - e.x;
    const dist = hypot(dx, p.y - e.y);
    e.dir = dx > 0 ? 1 : -1;
    if (e.mode === 'fuse') {
      e.modeT += 1;
      e.vx = e.dir * 0.5;
      if (e.modeT >= 45) this.explode(e);
      return;
    }
    if (dist < 420) {
      const safe = !e.onGround || this.can_step(e, e.dir);
      e.vx = safe ? e.dir * 1.7 : 0;
      if (e.hitWall && e.onGround) e.vy = -7;
    } else this.patrol(e, 0.6, 80);
    if (dist < 70) { e.mode = 'fuse'; e.modeT = 0; }
  }

  ai_boar(e, p) {
    const dx = p.x - e.x, dy = abs(p.y - e.y);
    e.modeT += 1;
    const mode = e.mode;
    if (mode === 'charge') {
      e.vx = e.dir * 5.2;
      if (e.hitWall || e.modeT > 70 || (e.onGround && !this.can_step(e, e.dir))) {
        if (e.hitWall) this.game.shake = max(this.game.shake, 5);
        e.mode = 'stun'; e.modeT = 0;
      }
      return;
    }
    if (mode === 'windup') { e.vx = 0; if (e.modeT >= 40) { e.mode = 'charge'; e.modeT = 0; } return; }
    if (mode === 'stun') { e.vx = 0; if (e.modeT >= 70) { e.mode = 'idle'; e.modeT = 0; e.atkCD = 60; } return; }
    e.atkCD -= 1;
    if (abs(dx) < 380 && dy < 70) {
      e.dir = dx > 0 ? 1 : -1;
      e.vx = e.dir * 0.8;
      if (e.atkCD <= 0 && abs(dx) > 90) { e.mode = 'windup'; e.modeT = 0; }
    } else this.patrol(e, 0.5, 100);
  }

  ai_shield(e, p) {
    const dx = p.x - e.x;
    e.atkCD -= 1;
    if (e.mode === 'bash') {
      e.modeT += 1;
      e.vx = 0;
      if (e.modeT === 14) {
        const reach = { x: e.dir < 0 ? e.x - 14 : e.x + e.w - 4, y: e.y, w: 18, h: e.h };
        if (rects_overlap(reach, p)) this.damage_player(e.dmg, e.x + e.w / 2);
      }
      if (e.modeT >= 30) { e.mode = 'idle'; e.modeT = 0; e.atkCD = 70; }
      return;
    }
    if (e.mode === 'stun') {
      e.modeT += 1; e.vx = 0;
      if (e.modeT >= 60) { e.mode = 'idle'; e.modeT = 0; }
      return;
    }
    if (abs(dx) < 360) {
      e.dir = dx > 0 ? 1 : -1;
      const safe = !e.onGround || this.can_step(e, e.dir);
      e.vx = (safe && abs(dx) > 40) ? e.dir * 0.7 : 0;
      if (abs(dx) < 54 && e.atkCD <= 0) { e.mode = 'bash'; e.modeT = 0; }
    } else this.patrol(e, 0.4, 60);
  }

  explode(e) {
    if (e.exploded) return;
    e.exploded = true;
    const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
    this.add_blast(cx, cy, BOMB_RADIUS);
    const p = this.player;
    if (hypot(p.x + p.w / 2 - cx, p.y + p.h / 2 - cy) < BOMB_RADIUS) this.damage_player(e.dmg, cx, 'fire');
    if (e.alive) { e.alive = false; e.dying = 6; e.hp = 0; }
    for (const o of this.enemies) {
      if (o === e || !o.alive) continue;
      if (hypot(o.x + o.w / 2 - cx, o.y + o.h / 2 - cy) < BOMB_RADIUS) {
        this.damage_enemy(o, BOMB_ENEMY_DMG, o.x > cx ? 1 : -1, false, 'fire', { silent_crit: true, pierce: true });
      }
    }
  }

  ai_wizard(e, p) {
    const enraged = e.hp < e.maxHp * 0.5;
    e.dir = p.x > e.x ? 1 : -1;
    e.modeT += 1;
    if (e.mode === 'idle') { e.mode = 'hover'; e.modeT = 0; }
    const mode = e.mode;
    if (mode === 'hover') {
      const dx = p.x - e.x;
      e.vy = (150 + Math.sin(e.aiT * 0.04) * 40 - e.y) * 0.05;
      if (abs(dx) > 300) e.vx = e.dir * 1.0;
      else if (abs(dx) < 170) e.vx = -e.dir * 0.8;
      else e.vx = 0;
      const interval = enraged ? 70 : 100;
      if (e.modeT % interval === 0) this.boss_volley(e, p, enraged ? 5 : 3);
      if (e.modeT >= interval * 4) { e.mode = 'windup'; e.modeT = 0; }
    } else if (mode === 'windup') {
      e.vx = max(-3.0, min(3.0, (p.x - e.x) * 0.08));
      e.vy = -0.5;
      if (e.modeT >= 45) { e.mode = 'fall'; e.modeT = 0; }
    } else if (mode === 'fall') {
      e.vx = 0; e.vy = 11;
      if (e.y + e.h >= GROUND_Y - 0.5) {
        this.boss_slam(e, enraged);
        e.mode = 'stun'; e.modeT = 0;
      }
    } else if (mode === 'stun') {
      e.vx = 0; e.vy = 0;
      if (e.modeT >= (enraged ? 80 : 110)) { e.mode = 'hover'; e.modeT = 0; }
    }
  }

  boss_volley(e, p, n) {
    const cx = e.x + e.w / 2, cy = e.y + e.h / 2;
    const base = Math.atan2(p.y + p.h / 2 - cy, p.x + p.w / 2 - cx);
    for (let i = 0; i < n; i++) {
      const a = base + (i - (n - 1) / 2.0) * 0.22;
      this.enemy_shot(e, 'fireball', Math.cos(a) * 3.6, Math.sin(a) * 3.6, 14, 14, 140, '#ff4020', cy);
    }
  }

  boss_slam(e, enraged) {
    e.y = GROUND_Y - e.h;
    this.game.shake = 12;
    const cx = e.x + e.w / 2;
    this.add_particles(cx, GROUND_Y, 30, '#c040ff', 5);
    const speeds = enraged ? [3.4, 5.0] : [3.4];
    for (const sp of speeds) {
      for (const d of [-1, 1]) {
        this.enemy_shot(e, 'wave', d * sp, 0, 26, 28, 400, '#c040ff', GROUND_Y - 14);
        this.enemyProj[this.enemyProj.length - 1].x = cx;
      }
    }
  }
}
