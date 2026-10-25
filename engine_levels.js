/* 关卡数据（由 Python levels.py 移植而来）。 */

const HINT_MOVE = 'A/D 移动   W/空格 跳跃   J 攻击   E 互动';

const LEVEL_DATA = {
  forest: {
    mapW: 2600, theme: 'forest', title: '第一关  森林入门', hint: HINT_MOVE,
    ground: [[0, 600], [680, 1260], [1340, 1900], [1980, 2600]],
    plats: [[200, 400, 110], [380, 330, 110], [700, 400, 100], [880, 330, 110],
            [1060, 400, 100], [1400, 400, 100], [1580, 330, 110], [1760, 260, 100],
            [2060, 400, 100], [2230, 330, 110]],
    enemies: [['slime', 450], ['goblin', 780], ['slime', 900], ['bomber', 1100],
              ['boar', 1500], ['slime', 1650], ['goblin', 1750], ['bomber', 2100],
              ['archer', 2250], ['boar', 2350]],
    chests: [[420, 330, ['gold', 30]], [920, 330, ['armor', 1]],
             [1790, 260, ['weapon', 1]], [2260, 330, ['gold', 50]]],
    crates: [[300, GROUND_Y], [1180, GROUND_Y], [2000, GROUND_Y]],
    holes: [[1000, 'sub_root']],
    secrets: [[1620, 3, ['weapon', 6]]],
    smithX: 2400, portalX: 2520,
  },
  swamp: {
    mapW: 2900, theme: 'swamp', title: '第二关  幽暗沼泽', hint: '毒沼会持续掉血，沿着平台走；野猪冲锋时可以跳过它',
    ground: [[0, 520], [610, 1000], [1090, 1500], [1590, 2050], [2140, 2900]],
    plats: [[180, 400, 100], [350, 330, 100], [540, 400, 90], [640, 330, 90], [700, 400, 100],
            [1100, 380, 100], [1280, 320, 100], [1620, 400, 100], [1800, 340, 100],
            [1990, 400, 90], [2090, 330, 90], [2200, 400, 100], [2400, 400, 90], [2490, 330, 100]],
    enemies: [['slime', 400], ['bomber', 700], ['archer', 900], ['boar', 1200],
              ['goblin', 1400], ['archer', 1700], ['bomber', 1850], ['slime', 2300],
              ['boar', 2500], ['shield', 2650]],
    hazards: [['poison', 520, 90], ['poison', 1000, 90], ['poison', 1500, 90], ['poison', 2050, 90]],
    chests: [[380, 330, ['gold', 50]], [670, 330, ['armor', 2]],
             [1310, 320, ['weapon', 6]], [2120, 330, ['gold', 70]], [2520, 330, ['weapon', 2]]],
    crates: [[250, GROUND_Y], [850, GROUND_Y], [1700, GROUND_Y], [2350, GROUND_Y]],
    holes: [[780, 'sub_mine']],
    secrets: [[1960, 3, ['armor', 3]]],
    smithX: 2780, portalX: 2850,
  },
  crypt: {
    mapW: 2800, theme: 'crypt', title: '第三关  骷髅地穴', hint: '骷髅会远程投骨，蝙蝠会俯冲，盾卫要绕背或用重武器',
    ground: [[0, 520], [610, 1150], [1240, 1800], [1900, 2400], [2490, 2800]],
    plats: [[200, 400, 100], [370, 330, 100], [540, 260, 100], [700, 400, 100],
            [870, 330, 100], [1040, 400, 100], [1300, 400, 100], [1470, 330, 100],
            [1640, 260, 100], [1960, 400, 100], [2130, 330, 100]],
    enemies: [['skeleton', 400], ['bat', 650, 200], ['shield', 800], ['archer', 1000],
              ['bomber', 1300], ['bat', 1250, 180], ['shield', 1550], ['skeleton', 1700],
              ['bat', 1900, 200], ['archer', 2050], ['bomber', 2250], ['shield', 2300],
              ['bat', 2450, 180]],
    chests: [[400, 330, ['gold', 60]], [570, 260, ['weapon', 5]], [900, 330, ['armor', 2]],
             [1330, 400, ['gold', 80]], [1670, 260, ['weapon', 3]], [2160, 330, ['armor', 3]]],
    hazards: [['spikes', 520, 90], ['spikes', 1150, 90]],
    crates: [[330, GROUND_Y], [1400, GROUND_Y], [2100, GROUND_Y]],
    secrets: [[1180, 4, ['weapon', 7]]],
    smithX: 2620, portalX: 2730,
  },
  lava: {
    mapW: 3000, theme: 'lava', title: '第四关  熔岩洞窟', hint: '岩浆一碰就掉血；移动平台会带着你走，注意站稳',
    ground: [[0, 500], [600, 900], [1000, 1260], [1360, 1700], [1800, 2100], [2200, 3000]],
    plats: [[160, 400, 110], [330, 330, 100], [700, 380, 100], [1100, 380, 100], [1450, 380, 100],
            [1900, 380, 100], [2300, 320, 100], [2480, 260, 100]],
    movers: [[520, 400, 70, 40, 180], [920, 400, 70, 40, 200], [1280, 400, 70, 40, 160],
             [1720, 400, 70, 40, 170], [2120, 400, 70, 40, 190]],
    enemies: [['bomber', 380], ['boar', 700], ['archer', 800], ['bat', 1100, 200], ['shield', 1450],
              ['bomber', 1600], ['archer', 1900], ['boar', 2300], ['bat', 2400, 200], ['shield', 2700]],
    hazards: [['lava', 500, 100], ['lava', 900, 100], ['lava', 1260, 100],
              ['lava', 1700, 100], ['lava', 2100, 100]],
    chests: [[360, 330, ['gold', 90]], [730, 380, ['armor', 5]], [1130, 380, ['weapon', 4]],
             [2510, 260, ['gold', 120]]],
    crates: [[460, GROUND_Y], [1500, GROUND_Y], [2600, GROUND_Y]],
    smithX: 2850, portalX: 2930,
  },
  fortress: {
    mapW: 3000, theme: 'fortress', title: '第五关  暗影要塞', hint: '最后的防线：盾卫、弓手和自爆虫会配合出现',
    ground: [[0, 700], [790, 1500], [1590, 2300], [2390, 3000]],
    plats: [[250, 400, 110], [450, 340, 100], [850, 400, 100], [1000, 340, 100], [1150, 280, 100],
            [1650, 400, 100], [1800, 340, 100], [2050, 400, 100],
            [2450, 400, 100], [2600, 340, 100], [2750, 280, 100]],
    enemies: [['shield', 500], ['archer', 600], ['bomber', 900], ['shield', 1100], ['archer', 1300],
              ['boar', 1700], ['bomber', 1850], ['skeleton', 2000], ['shield', 2150],
              ['archer', 2500], ['bomber', 2650], ['shield', 2800]],
    hazards: [['spikes', 700, 90], ['spikes', 1500, 90], ['spikes', 2300, 90]],
    chests: [[480, 340, ['gold', 100]], [1180, 280, ['armor', 4]], [1830, 340, ['weapon', 7]],
             [2780, 280, ['gold', 150]]],
    crates: [[350, GROUND_Y], [1000, GROUND_Y], [1800, GROUND_Y], [2500, GROUND_Y]],
    smithX: 2880, portalX: 2940,
  },
  boss: {
    mapW: 960, theme: 'boss', title: '最终关  暗影巫师', hint: '巫师落地时是输出机会，冲击波可以跳过去',
    ground: [[0, 960]],
    plats: [[150, 400, 120], [690, 400, 120], [420, 370, 120]],
    enemies: [['wizard', 700, 150]],
    chests: [],
    smithX: 70, portalX: null,
  },
  sub_root: {
    mapW: 1500, theme: 'cave', back: 120, title: '地下  树根洞穴', hint: '地下藏着额外的宝箱。走到左边的梯子按 E 返回地面',
    ground: [[0, 500], [590, 1000], [1090, 1500]],
    plats: [[220, 390, 100], [400, 330, 90], [700, 390, 100], [820, 340, 90], [910, 290, 90],
            [1180, 390, 100], [1330, 330, 90]],
    enemies: [['slime', 300], ['bat', 700, 220], ['goblin', 850], ['bomber', 1200]],
    hazards: [['spikes', 500, 90], ['spikes', 1000, 90]],
    chests: [[430, 330, ['gold', 80]], [940, 290, ['armor', 2]], [1360, 330, ['weapon', 5]]],
    crates: [[650, GROUND_Y], [1250, GROUND_Y]],
    smithX: null, portalX: null,
  },
  sub_mine: {
    mapW: 1700, theme: 'cave', back: 120, title: '地下  废弃矿坑', hint: '矿坑里有更强的怪物，也有更好的奖励',
    ground: [[0, 450], [540, 900], [990, 1300], [1390, 1700]],
    plats: [[200, 400, 100], [350, 330, 90], [600, 400, 100], [770, 330, 90], [1040, 400, 100], [1200, 330, 90], [1450, 400, 100], [1580, 320, 90]],
    enemies: [['skeleton', 300], ['shield', 650], ['bat', 800, 220], ['archer', 1100], ['boar', 1500], ['bomber', 1620]],
    hazards: [['spikes', 450, 90], ['spikes', 900, 90], ['spikes', 1300, 90]],
    chests: [[380, 330, ['gold', 100]], [800, 330, ['weapon', 6]], [1230, 330, ['armor', 3]], [1600, 320, ['gold', 140]]],
    crates: [[400, GROUND_Y], [1100, GROUND_Y]],
    smithX: null, portalX: null,
  },
};

LEVEL_DATA['arena'] = {
  mapW: 960, theme: 'arena', title: '无尽挑战', hint: '一波接一波的敌人。撑得越久，成绩越高',
  ground: [[0, 960]],
  plats: [[120, 400, 130], [710, 400, 130], [330, 400, 80], [550, 400, 80], [415, 330, 130]],
  enemies: [], chests: [], crates: [[480, GROUND_Y]],
  smithX: 480, portalX: null,
};

const SECRET_ROOM = {
  mapW: 700, theme: 'secret', back: 90, title: '隐藏房间', hint: '你发现了秘密！打开宝箱，然后从左边出去',
  ground: [[0, 700]], plats: [], enemies: [], hazards: [], crates: [],
  smithX: null, portalX: null,
};

function is_sub(name) { return name.startsWith('sub_') || name.startsWith('secret_'); }

function build_data(name) {
  if (name in LEVEL_DATA) return LEVEL_DATA[name];
  if (name.startsWith('secret_')) {
    const parts = name.split('_');   // ['secret', parent, idx]
    const parent = parts[1], idx = parseInt(parts[2], 10);
    const [x, hp, give] = LEVEL_DATA[parent].secrets[idx];
    const d = { ...SECRET_ROOM };
    d.chests = [[340, GROUND_Y, give]];
    return d;
  }
  throw new Error('unknown level: ' + name);
}

function load_level(name) {
  const d = build_data(name);
  const platforms = d.ground.map(([a, b]) => ({ x: a, y: GROUND_Y, w: b - a, h: 60, type: 'ground' }));
  for (const [x, y, w] of d.plats) platforms.push({ x, y, w, h: 16, type: 'plat' });
  const movers = [];
  for (const [x, y, w, amp, period] of (d.movers || [])) {
    const pl = { x: x, y: y, w: w, h: 16, type: 'plat', mover: true };
    movers.push({ plat: pl, x0: x, amp: amp, period: period });
    platforms.push(pl);
  }
  const spawns = [];
  for (const spec of d.enemies) {
    const etype = spec[0], x = spec[1];
    const y = spec.length > 2 ? spec[2] : GROUND_Y - ENEMY_DEFS[etype].h - 1;
    spawns.push([etype, x, y]);
  }
  const chests = d.chests.map(([x, sy, give]) => ({ x, y: sy - 28, w: 28, h: 28, opened: false, give }));
  const hazards = (d.hazards || []).map(([k, x, w]) => ({ kind: k, x, y: GROUND_Y - 6, w, h: 40 }));
  const crates = (d.crates || []).map(([x, sy]) => ({ x: x - 14, y: sy - 28, w: 28, h: 28, hp: 2 }));
  const holes = (d.holes || []).map(([x, to]) => ({ x, to }));
  const secrets = (d.secrets || []).map(([x, hp], i) => ({ x, hp, maxHp: hp, idx: i, open: false }));
  return {
    mapW: d.mapW, title: d.title, hint: d.hint, theme: d.theme || 'forest',
    platforms, movers, spawns, chests, hazards, crates, holes, secrets,
    back: d.back, smithX: d.smithX, portalX: d.portalX,
  };
}
