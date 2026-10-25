/* 游戏静态数据与常量（由 Python game_data.py 移植而来，数值保持一致）。 */
const W = 960, H = 540, TICK_RATE = 60;

const INPUT_KEYS = ['left', 'right', 'up', 'down', 'jump', 'attack',
  'interact', 'confirm', 'inv', 'stats', 'escape'];

const PIT_DAMAGE_PCT = 0.15;
const SAFE_FALL = 130;
const FALL_PCT_PER_PX = 0.0016;
const FALL_MAX_PCT = 0.45;

const GRAVITY = 0.45;
const JUMP_V = -10.8;
const MOVE_SPEED = 2.4;
const MAX_FALL = 14;
const GROUND_Y = 480;

const LEVEL_ORDER = ['forest', 'swamp', 'crypt', 'lava', 'fortress', 'boss'];
const LEVEL_NAMES = ['森林入门', '幽暗沼泽', '骷髅地穴', '熔岩洞窟', '暗影要塞', '暗影巫师'];
const LEVEL_CLEAR_EXP = { forest: 50, swamp: 70, crypt: 100, lava: 130, fortress: 160 };

const HAZARD_DEFS = {
  spikes: { pct: 0.12, elem: 'phys', name: '尖刺' },
  lava: { pct: 0.20, elem: 'fire', name: '岩浆' },
  poison: { pct: 0.04, elem: 'phys', name: '毒沼', tick: 40 },
};
const HAZARD_KNOCK = 6.5;
const CRATE_DROPS = [0.55, 0.25];
const ENDLESS_WAVE_BREAK = 150;
const MODES = ['adventure', 'endless'];

const ELEMENTS = {
  phys: { name: '物理', short: '物', color: '#d8d8e0' },
  fire: { name: '火', short: '火', color: '#ff7a30' },
  ice: { name: '冰', short: '冰', color: '#7ad8ff' },
  thunder: { name: '雷', short: '雷', color: '#ffe040' },
};
const WEAK_MULT = 1.5, RESIST_MULT = 0.5;
const MIN_DMG_RATIO = 0.3;
const BURN_FRAMES = 180, BURN_TICK = 30;
const SLOW_FRAMES = 120, SLOW_FACTOR = 0.5;
const CHAIN_RANGE = 110, CHAIN_RATIO = 0.5;
const CARD_FRAMES = 420;

const WEAPONS = [
  { name: '木剑', type: 'melee', style: 'sword', elem: 'phys', dmg: 8, cd: 22, range: 42, color: '#a06030', price: 0 },
  { name: '铁剑', type: 'melee', style: 'sword', elem: 'phys', dmg: 14, cd: 20, range: 46, color: '#c8c8d0', price: 60 },
  { name: '战斧', type: 'melee', style: 'axe', elem: 'phys', dmg: 26, cd: 34, range: 50, color: '#9090a0', price: 150, heavy: true },
  { name: '长弓', type: 'ranged', style: 'bow', elem: 'phys', dmg: 18, cd: 26, range: 280, color: '#c0e060', price: 220, projSpeed: 9 },
  { name: '火焰杖', type: 'ranged', style: 'staff', elem: 'fire', dmg: 30, cd: 30, range: 300, color: '#ff6020', price: 420, projSpeed: 7, heavy: true },
  { name: '烈焰剑', type: 'melee', style: 'sword', elem: 'fire', dmg: 16, cd: 21, range: 46, color: '#ff8a3a', price: 200 },
  { name: '冰霜剑', type: 'melee', style: 'sword', elem: 'ice', dmg: 15, cd: 20, range: 46, color: '#8adfff', price: 200 },
  { name: '雷霆矛', type: 'melee', style: 'spear', elem: 'thunder', dmg: 20, cd: 27, range: 64, color: '#ffe84a', price: 320 },
];

const ARMORS = [
  { name: '布衣', reduce: 0, color: '#8a7050', price: 0, res: {} },
  { name: '皮甲', reduce: 10, color: '#7a5030', price: 40, res: { ice: 15 } },
  { name: '铁甲', reduce: 20, color: '#9090a0', price: 110, res: { fire: 10, thunder: -15 } },
  { name: '钢甲', reduce: 30, color: '#b0c0d0', price: 240, res: { fire: 15, ice: 20, thunder: -10 } },
  { name: '皇家盔甲', reduce: 40, color: '#ffe060', price: 480, res: { fire: 25, ice: 25, thunder: 25 } },
  { name: '熔岩甲', reduce: 25, color: '#d05a28', price: 300, res: { fire: 50, ice: -25 } },
];

const ENEMY_DEFS = {
  slime: { name: '史莱姆', hp: 18, w: 24, h: 18, dmg: 4, exp: 8, gold: 6, color: '#60d060', def: 0, weak: 'fire', resist: null, atk: 'phys', desc: '软绵绵地跳着巡逻，怕火。' },
  goblin: { name: '哥布林', hp: 34, w: 22, h: 28, dmg: 6, exp: 15, gold: 12, color: '#50a050', def: 1, weak: 'thunder', resist: null, atk: 'phys', desc: '发现你会追击并跳跃，怕雷击。' },
  skeleton: { name: '骷髅兵', hp: 48, w: 22, h: 30, dmg: 9, exp: 22, gold: 22, color: '#e0e0c0', def: 3, weak: 'fire', resist: 'ice', atk: 'phys', desc: '保持距离投掷骨头，注意走位。' },
  bat: { name: '寒霜蝠', hp: 24, w: 22, h: 16, dmg: 6, exp: 18, gold: 14, color: '#8040a0', fly: true, def: 0, weak: 'fire', resist: 'ice', atk: 'ice', desc: '盘旋后俯冲撕咬，带着寒气。' },
  wizard: { name: '暗影巫师', hp: 350, w: 36, h: 44, dmg: 14, exp: 200, gold: 300, color: '#8020c0', fly: true, def: 4, weak: 'ice', resist: 'fire', atk: 'fire', desc: '砸地后会硬直，那是输出机会。' },
  archer: { name: '绿衣弓手', hp: 30, w: 22, h: 30, dmg: 8, exp: 20, gold: 18, color: '#3a8a5a', def: 1, weak: 'ice', resist: null, atk: 'phys', desc: '抛物线射箭，别在远处硬拼。' },
  bomber: { name: '自爆虫', hp: 16, w: 22, h: 18, dmg: 18, exp: 16, gold: 14, color: '#e05030', def: 0, weak: 'ice', resist: 'fire', atk: 'fire', desc: '靠近就点燃引信，远远击杀最安全。' },
  boar: { name: '野猪', hp: 60, w: 34, h: 24, dmg: 12, exp: 24, gold: 24, color: '#8a5a3a', def: 3, weak: 'ice', resist: 'thunder', atk: 'phys', desc: '低头蓄力后直线冲撞，撞墙会眩晕。' },
  shield: { name: '盾卫', hp: 70, w: 24, h: 32, dmg: 10, exp: 28, gold: 28, color: '#4a5a8a', def: 6, weak: 'thunder', resist: 'ice', atk: 'phys', desc: '正面挡普通攻击：绕背、重武器或雷电。' },
};

const HITSTOP_HIT = 2, HITSTOP_CRIT = 5, HITSTOP_HURT = 3;
const BOMB_RADIUS = 76, BOMB_ENEMY_DMG = 36;
const MAX_FX = 40;
const MAX_PARTICLES = 300;

const PHYS_COLOR = '#ff6060';

function parse_aim(v) {
  if (!Array.isArray(v) || v.length !== 2) return null;
  const out = [];
  for (const n of v) {
    if (typeof n === 'boolean' || (typeof n !== 'number')) return null;
    if (!isFinite(n)) return null;
    out.push(n);
  }
  return [Math.max(0, Math.min(W, out[0])), Math.max(0, Math.min(H, out[1]))];
}

function weapon_power(index) {
  const w = WEAPONS[index];
  return w.dmg * 60.0 / w.cd;
}

function build_catalog() {
  const enemies = {};
  for (const t of Object.keys(ENEMY_DEFS)) {
    const d = ENEMY_DEFS[t];
    enemies[t] = { name: d.name, hp: d.hp, def: d.def, weak: d.weak, resist: d.resist, atk: d.atk, desc: d.desc, boss: t === 'wizard' };
  }
  return { elements: ELEMENTS, weapons: WEAPONS.map(w => ({ ...w })), armors: ARMORS.map(a => ({ ...a })), enemies };
}

const CATALOG = build_catalog();
