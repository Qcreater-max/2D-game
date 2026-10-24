/* 像素精灵：用字符画定义，启动时预渲染为离屏画布（每个精灵像素放大 2 倍） */
const PX = 2;
const spriteCache = {};

function makeSprite(rows, pal, flip) {
  const w = Math.max(...rows.map(r => r.length)), h = rows.length;
  const c = document.createElement('canvas');
  c.width = w * PX; c.height = h * PX;
  const g = c.getContext('2d');
  rows.forEach((r, y) => {
    for (let i = 0; i < r.length; i++) {
      const col = pal[r[i]];
      if (!col) continue;
      g.fillStyle = col;
      g.fillRect((flip ? w - 1 - i : i) * PX, y * PX, PX, PX);
    }
  });
  return c;
}

function cached(key, rows, pal, flip) {
  const k = key + (flip ? ':f' : '');
  return spriteCache[k] || (spriteCache[k] = makeSprite(rows, pal, flip));
}

function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const f = v => Math.max(0, Math.min(255, v + amt));
  return '#' + ((1 << 24) + (f(n >> 16) << 16) + (f((n >> 8) & 255) << 8) + f(n & 255)).toString(16).slice(1);
}

// ---------- 玩家（朝右，12x16）----------
const P_TOP = [
  '...hhhhhh...',
  '..hhhhhhhh..',
  '..hhhssssh..',
  '..hhsssesh..',
  '...ssssss...',
  '....ssss....',
  '..lAAAAAAa..',
  '.AlAAAAAAaA.',
  '.AlAAAAAAaA.',
  '.sAkkggkkAs.',
  '..aAAAAAAa..',
  '..pppppppp..',
];
const P_LEGS = {
  idle: ['..ppp..ppp..', '..ppp..ppp..', '..bbb..bbb..', '..bbbb.bbbb.'],
  walkA: ['..ppp..ppp..', '...ppp.ppp..', '...bbb..bb..', '..bbbb..bbb.'],
  walkB: ['..ppp..ppp..', '..ppp.ppp...', '..bb..bbb...', '.bbb..bbbb..'],
  jump: ['..pppppppp..', '..ppp..ppp..', '..bbb..bbb..', '............'],
};

function playerSprite(armor, frame, facing) {
  const base = ARMORS[armor].color;
  const pal = {
    h: '#5a3418', s: '#f0c090', e: '#201010', A: base, a: shade(base, -40), l: shade(base, 35),
    k: '#3a2818', g: '#e0b030', p: '#4a3a6a', b: '#3a2010',
  };
  return cached('pl' + armor + frame, P_TOP.concat(P_LEGS[frame]), pal, facing < 0);
}

// ---------- 敌人 ----------
const SLIME = [
  '....hhgggg....', '..hhhggggggg..', '.hhgggggggggg.', '.gggwwgggwwggg',
  '.gggwkgggwkggg', 'gggggggggggggg', 'gggggggkkggggg', 'GgggggggggggGg',
  '.GGgggggggggGG', '..GGGGGGGGGG..',
];
const SLIME_SQUASH = [
  '..............', '..............', '....hhgggg....', '.hhhgggggggg..',
  'hhgwwgggwwggg.', 'ggwwkgggwkgggg', 'gggggggkkgggggg', 'GgggggggggggGG',
  'GGGgggggggGGGG', '.GGGGGGGGGGGG.',
];
const GOBLIN = [
  '.gg......gg.', '..gggggggg..', '..gyyggyyg..', '..gkyggkyg..', '..gggwggwgg.',
  '...gggggg...', '..ccccccccn.', '.gccCccCccgn', '.gccccccccg.', '..ccCCCCcc..',
  '..cccccccc..', '..GG....GG..', '.gGg....gGg.', '.kkk....kkk.',
];
const SKELETON = [
  '...wwwwww...', '..wwwwwwww..', '..wkrwwkrw..', '..wwwwwwww..', '...wkwkwk...',
  '....wwww....', '..wWwwwwWw..', '.w.wkwwkw.w.', '.w.wwwwww.w.', '.w.wkwwkw.w.',
  '...wwwwww...', '...ww..ww...', '...w....w...', '...w....w...', '..ww....ww..',
];
const BAT_UP = [
  'w..............w', 'ww....b..b....ww', 'www..bbbbbb..www', '.wwwbbbbbbbbwww.',
  '..wwbrbbbbrbww..', '...wwbbwwbbww...', '....wbbbbbbw....', '.....b....b.....',
];
const BAT_DOWN = [
  '......b..b......', '.....bbbbbb.....', '....brbbbbrb....', 'wwwwbbbbbbbbwwww',
  '.wwwwbwwwwbwwww.', '..www.bbbb.www..', '...w........w...', '................',
];
const WIZARD = [
  '........hh........', '.......hhhh.......', '......hhhhhh......', '.....hhhhhhhh.....',
  '....hhhhggghhhh...', '..hhhhhhhhhhhhhh..', '......ssssss......', '.....sskrskrss....',
  '.....ssssssss.....', '......sWWWWs......', '....rrrrrrrrrr....', '...rrRrrrrrrRrr...',
  '..rrRrrrggrrrRrr..', '..rrRrrrggrrrRrr..', '..rrrrrrggrrrrrr..', '.rrRrrrrrrrrrrRrr.',
  '.rrrrrrrrrrrrrrrr.', '.rrRrrrrrrrrrRrrr.', 'rrrrrrrrrrrrrrrrrr', 'rRrrrrrrrrrrrrrRrr',
  'rrrrrrrrrrrrrrrrrr', '.RRRRRRRRRRRRRRRR.',
];
const CHEST_CLOSED = [
  '..bbbbbbbbbb..', '.bBBBBBBBBBBb.', 'bBBBBBBBBBBBBb', 'bbbbbbggbbbbbb',
  'bBBBBBgkgBBBBb', 'bBBBBBBBBBBBBb', 'bBBBBBBBBBBBBb', 'bbbbbbbbbbbbbb',
];
const CHEST_OPEN = [
  '.bb........bb.', 'bBBb......bBBb', '.bbbbbbbbbbbb.', 'bbbbbbbbbbbbbb',
  'bddddddddddddb', 'bddgggddgggddb', 'bBBBBBBBBBBBBb', 'bbbbbbbbbbbbbb',
];
const ARCHER = [
  '...hhhhhh...', '..hhhhhhhh..', '..hhsssshh..', '..hssesses..', '...ssssss...',
  '..gggggggg..', '.sgggbbgggs.', '.sgggbbggg..', '..gggggggg..', '..gg.bb.gg..',
  '..bb....bb..', '.bbb....bbb.',
];
const BOMBER = [
  '.......y......', '......yo......', '.....kkk......', '..rrrrrrrrrr..', '.rrrOOrrOOrrr.',
  'rrrrOkrrOkrrrr', 'rrrrrrrrrrrrrr', 'rrrrrwwwwrrrrr', '.rrrrrrrrrrrr.', '..rr.rrrr.rr..',
];
const BOAR = [
  '.........bb.......', '......bbbbbbb.....', '...bbbbbbbbbbbb...', '..bbbbbbbbbbbbbbw.',
  '.bbbbbbbbbbbbbbbew', '.bbbbbbbbbbbbbbbbbw', 'bbBbbbbbbbbbbbbbbb.', 'bbbbbbbbbbbbbbbbbb.',
  '.bbbbbbbbbbbbbbbb..', '..kk..kk....kk..kk', '..kk..kk....kk..kk',
];
const SHIELDER = [
  '...iiiiiii..', '..iiiiiiiii.', '..iikkssskk.', '..iissssssi.', '...iiiiiii..',
  '.nnnbbbbbbs.', 'nNNnbbbbbbs.', 'nNnnbbbbbb..', 'nNNnbbbbbb..', 'nNNnbbbbbb..',
  '.nnn.bbbb...', '.....bbbb...', '.....kk.kk..', '....kkk.kkk.',
];
const HEART = ['.rr.rr.', 'rRrrrrr', 'rrrrrrr', '.rrrrr.', '..rrr..', '...r...'];
const COIN = ['.gggg.', 'ggyygg', 'gyggyg', 'gyggyg', 'ggyygg', '.gggg.'];

const PAL = {
  g: '#60d060', G: '#388838', h: '#a0f0a0', w: '#f4f4e8', W: '#b8b49c', k: '#101018',
  y: '#ffe040', c: '#8a5a2a', C: '#5a3a18', n: '#c0c8d0', r: '#ff4020', R: '#a01018', s: '#c8a0e8',
  b: '#6a4020', B: '#a07030', d: '#2a1810',
};
function pal(over) { return Object.assign({}, PAL, over); }

function enemySprite(e, time) {
  const f = e.dir < 0;
  switch (e.type) {
    case 'slime': {
      const sq = Math.floor(time / 18) % 2;
      return cached('slime' + sq, sq ? SLIME_SQUASH : SLIME, PAL, false);
    }
    case 'goblin': return cached('gob', GOBLIN, pal({ g: '#58a838', G: '#386828' }), f);
    case 'skeleton': return cached('skel', SKELETON, pal({ w: '#e8e4cc' }), f);
    case 'bat': {
      const up = Math.floor(time / 6) % 2;
      return cached('bat' + up, up ? BAT_UP : BAT_DOWN, pal({ w: '#5a2878', b: '#8040a0' }), false);
    }
    case 'archer': return cached('arch', ARCHER, pal({ h: '#2a6a3a', g: '#3a8a5a', s: '#e8c8a0', b: '#6a4020' }), f);
    case 'bomber': {
      // 引信燃烧时红白交替闪烁，越接近爆炸越快
      const fast = e.mode === 'fuse' ? (e.modeT > 28 ? 2 : 4) : 99999;
      const hot = e.mode === 'fuse' && Math.floor(time / fast) % 2 === 0;
      return cached('bomb' + (hot ? 'h' : ''), BOMBER,
        pal(hot ? { r: '#fff0d0', O: '#ffa030', k: '#202020', w: '#ff4020', y: '#fff060', o: '#ff8020' }
                : { r: '#e05030', O: '#fff0a0', k: '#201010', w: '#f8d8a0', y: '#ffd040', o: '#ff8020' }), false);
    }
    case 'boar': {
      const charging = e.mode === 'charge' || e.mode === 'windup';
      return cached('boar' + (e.mode === 'stun' ? 's' : charging ? 'c' : ''), BOAR,
        pal({ b: e.mode === 'stun' ? '#a09090' : charging ? '#b05a30' : '#8a5a3a', B: '#5a3a20', w: '#f4f0d8', e: '#ff3020', k: '#2a1a10' }), f);
    }
    // 盾画在精灵左侧（默认朝左），所以朝右时才翻转
    case 'shield': return cached('shd' + (e.mode === 'stun' ? 's' : ''), SHIELDER,
      pal({ i: '#6a7aaa', k: '#101018', s: '#e8c8a0', n: '#c8d0e0', N: '#8a98b8', b: e.mode === 'stun' ? '#6a5050' : '#4a5a8a' }), !f);
    case 'wizard': {
      const rage = e.mode === 'windup' || e.mode === 'fall';
      return cached('wiz' + (rage ? 'r' : ''), WIZARD,
        pal({ h: rage ? '#b02050' : '#4a1070', g: '#ffd040', r: rage ? '#7a1050' : '#3a0860', R: '#240440' }), f);
    }
  }
  return null;
}

const itemSprites = () => ({
  heart: cached('heart', HEART, PAL), coin: cached('coin', COIN, PAL),
  chest: cached('chest0', CHEST_CLOSED, PAL), chestOpen: cached('chest1', CHEST_OPEN, PAL),
});
