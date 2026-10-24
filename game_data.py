"""游戏静态数据：物理参数、元素、武器、盔甲、敌人、关卡顺序。

前端的武器 / 盔甲 / 怪物资料不再手写一份，而是由服务器通过 CATALOG 下发（见文件末尾）。
"""

import math

W, H = 960, 540
TICK_RATE = 60

# 客户端可发送的按键（按下 / 松开）。服务端自己做"刚按下"的边沿检测，
# 所以菜单、背包等一次性操作不需要客户端定时脉冲。
INPUT_KEYS = ('left', 'right', 'up', 'down', 'jump', 'attack',
              'interact', 'confirm', 'inv', 'stats', 'escape')
PIT_DAMAGE_PCT = 0.15   # 掉坑扣最大生命的比例，之后回到最近的安全地面

# 摔伤：按"离地后到达的最高点 → 落地点"的落差计算，所以起跳再落回原地不算（单次跳跃最高约 124）。
# 落差超过 SAFE_FALL 的部分，每像素扣最大生命的 FALL_PCT_PER_PX，最多扣 FALL_MAX_PCT。
# 摔伤不会致死（最低剩 1 点生命），也不受盔甲减伤影响。
SAFE_FALL = 130
FALL_PCT_PER_PX = 0.0016
FALL_MAX_PCT = 0.45

# 物理参数（单位：像素 / 帧）
GRAVITY = 0.45
JUMP_V = -10.8
MOVE_SPEED = 2.4
MAX_FALL = 14
GROUND_Y = 480

STATES = {
    'MENU': 'menu', 'FOREST': 'forest', 'CRYPT': 'crypt',
    'BOSS': 'boss', 'WIN': 'win', 'DEAD': 'dead',
}
LEVEL_ORDER = ['forest', 'swamp', 'crypt', 'lava', 'fortress', 'boss']
LEVEL_NAMES = ['森林入门', '幽暗沼泽', '骷髅地穴', '熔岩洞窟', '暗影要塞', '暗影巫师']
LEVEL_CLEAR_EXP = {'forest': 50, 'swamp': 70, 'crypt': 100, 'lava': 130, 'fortress': 160}

# 危险物：接触伤害（占最大生命的百分比）、伤害元素、再次受伤前的无敌帧
HAZARD_DEFS = {
    'spikes': {'pct': 0.12, 'elem': 'phys',  'name': '尖刺'},
    'lava':   {'pct': 0.20, 'elem': 'fire',  'name': '岩浆'},
    'poison': {'pct': 0.04, 'elem': 'phys',  'name': '毒沼', 'tick': 40},   # 持续掉血，每 tick 帧一次
}
HAZARD_KNOCK = 6.5          # 被尖刺 / 岩浆弹开的竖直速度
CRATE_DROPS = (0.55, 0.25)  # 木箱：掉金币 / 掉回血 的概率，其余为空
ENDLESS_WAVE_BREAK = 150    # 无尽模式：两波之间的间隔（帧）
MODES = ('adventure', 'endless')

# ---------- 元素 ----------
ELEMENTS = {
    'phys':    {'name': '物理', 'short': '物', 'color': '#d8d8e0'},
    'fire':    {'name': '火',   'short': '火', 'color': '#ff7a30'},
    'ice':     {'name': '冰',   'short': '冰', 'color': '#7ad8ff'},
    'thunder': {'name': '雷',   'short': '雷', 'color': '#ffe040'},
}
WEAK_MULT, RESIST_MULT = 1.5, 0.5   # 命中弱点 / 抗性元素的伤害倍率
MIN_DMG_RATIO = 0.3                 # 防御再高，也至少打出 30% 的伤害
BURN_FRAMES, BURN_TICK = 180, 30    # 火：灼烧 3 秒，每 0.5 秒一跳（每跳 = 命中伤害的 20%，至少 2）
SLOW_FRAMES, SLOW_FACTOR = 120, 0.5 # 冰：减速 2 秒，移速减半（首领免疫）
CHAIN_RANGE, CHAIN_RATIO = 110, 0.5 # 雷：电弧跳到 110 像素内最近的敌人，造成 50% 伤害；雷无视盾卫的格挡
CARD_FRAMES = 420                   # 新怪物卡片显示时长（7 秒）

# 武器：elem 是元素，style 决定客户端画法，heavy 表示重击（能打破盾卫格挡）
# cd 为攻击冷却（帧），range 为攻击距离（像素）
WEAPONS = [
    {'name': '木剑',   'type': 'melee',  'style': 'sword', 'elem': 'phys',    'dmg': 8,  'cd': 22, 'range': 42,  'color': '#a06030', 'price': 0},
    {'name': '铁剑',   'type': 'melee',  'style': 'sword', 'elem': 'phys',    'dmg': 14, 'cd': 20, 'range': 46,  'color': '#c8c8d0', 'price': 60},
    {'name': '战斧',   'type': 'melee',  'style': 'axe',   'elem': 'phys',    'dmg': 26, 'cd': 34, 'range': 50,  'color': '#9090a0', 'price': 150, 'heavy': True},
    {'name': '长弓',   'type': 'ranged', 'style': 'bow',   'elem': 'phys',    'dmg': 18, 'cd': 26, 'range': 280, 'color': '#c0e060', 'price': 220, 'projSpeed': 9},
    {'name': '火焰杖', 'type': 'ranged', 'style': 'staff', 'elem': 'fire',    'dmg': 30, 'cd': 30, 'range': 300, 'color': '#ff6020', 'price': 420, 'projSpeed': 7, 'heavy': True},
    {'name': '烈焰剑', 'type': 'melee',  'style': 'sword', 'elem': 'fire',    'dmg': 16, 'cd': 21, 'range': 46,  'color': '#ff8a3a', 'price': 200},
    {'name': '冰霜剑', 'type': 'melee',  'style': 'sword', 'elem': 'ice',     'dmg': 15, 'cd': 20, 'range': 46,  'color': '#8adfff', 'price': 200},
    {'name': '雷霆矛', 'type': 'melee',  'style': 'spear', 'elem': 'thunder', 'dmg': 20, 'cd': 27, 'range': 64,  'color': '#ffe84a', 'price': 320},
]

# 盔甲：reduce 是对所有伤害的百分比减免；res 是额外的元素抗性（百分比，负数表示易伤）
ARMORS = [
    {'name': '布衣',     'reduce': 0,  'color': '#8a7050', 'price': 0,   'res': {}},
    {'name': '皮甲',     'reduce': 10, 'color': '#7a5030', 'price': 40,  'res': {'ice': 15}},
    {'name': '铁甲',     'reduce': 20, 'color': '#9090a0', 'price': 110, 'res': {'fire': 10, 'thunder': -15}},
    {'name': '钢甲',     'reduce': 30, 'color': '#b0c0d0', 'price': 240, 'res': {'fire': 15, 'ice': 20, 'thunder': -10}},
    {'name': '皇家盔甲', 'reduce': 40, 'color': '#ffe060', 'price': 480, 'res': {'fire': 25, 'ice': 25, 'thunder': 25}},
    {'name': '熔岩甲',   'reduce': 25, 'color': '#d05a28', 'price': 300, 'res': {'fire': 50, 'ice': -25}},
]

# 敌人：def 是固定减伤，weak / resist 是弱点 / 抗性元素，atk 是攻击元素
ENEMY_DEFS = {
    'slime':    {'name': '史莱姆', 'hp': 18,  'w': 24, 'h': 18, 'dmg': 4,  'exp': 8,   'gold': 6,   'color': '#60d060',
                 'def': 0, 'weak': 'fire',    'resist': None,      'atk': 'phys',
                 'desc': '软绵绵地跳着巡逻，怕火。'},
    'goblin':   {'name': '哥布林', 'hp': 34,  'w': 22, 'h': 28, 'dmg': 6,  'exp': 15,  'gold': 12,  'color': '#50a050',
                 'def': 1, 'weak': 'thunder', 'resist': None,      'atk': 'phys',
                 'desc': '发现你会追击并跳跃，怕雷击。'},
    'skeleton': {'name': '骷髅兵', 'hp': 48,  'w': 22, 'h': 30, 'dmg': 9,  'exp': 22,  'gold': 22,  'color': '#e0e0c0',
                 'def': 3, 'weak': 'fire',    'resist': 'ice',    'atk': 'phys',
                 'desc': '保持距离投掷骨头，注意走位。'},
    'bat':      {'name': '寒霜蝠', 'hp': 24,  'w': 22, 'h': 16, 'dmg': 6,  'exp': 18,  'gold': 14,  'color': '#8040a0', 'fly': True,
                 'def': 0, 'weak': 'fire',    'resist': 'ice',    'atk': 'ice',
                 'desc': '盘旋后俯冲撕咬，带着寒气。'},
    'wizard':   {'name': '暗影巫师', 'hp': 350, 'w': 36, 'h': 44, 'dmg': 14, 'exp': 200, 'gold': 300, 'color': '#8020c0', 'fly': True,
                 'def': 4, 'weak': 'ice',     'resist': 'fire',   'atk': 'fire',
                 'desc': '砸地后会硬直，那是输出机会。'},
    # 远程：与玩家保持距离，抛物线射箭
    'archer':   {'name': '绿衣弓手', 'hp': 30, 'w': 22, 'h': 30, 'dmg': 8,  'exp': 20,  'gold': 18,  'color': '#3a8a5a',
                 'def': 1, 'weak': 'ice',     'resist': None,      'atk': 'phys',
                 'desc': '抛物线射箭，别在远处硬拼。'},
    # 自爆：追上来后点燃引信，爆炸伤害玩家和周围敌人；被击杀也会爆
    'bomber':   {'name': '自爆虫', 'hp': 16,  'w': 22, 'h': 18, 'dmg': 18, 'exp': 16,  'gold': 14,  'color': '#e05030',
                 'def': 0, 'weak': 'ice',     'resist': 'fire',   'atk': 'fire',
                 'desc': '靠近就点燃引信，远远击杀最安全。'},
    # 冲锋：蓄力后直线冲撞，撞墙会眩晕
    'boar':     {'name': '野猪', 'hp': 60,  'w': 34, 'h': 24, 'dmg': 12, 'exp': 24,  'gold': 24,  'color': '#8a5a3a',
                 'def': 3, 'weak': 'ice',     'resist': 'thunder', 'atk': 'phys',
                 'desc': '低头蓄力后直线冲撞，撞墙会眩晕。'},
    # 盾卫：正面格挡普通攻击，需绕背或使用重击武器
    'shield':   {'name': '盾卫', 'hp': 70,  'w': 24, 'h': 32, 'dmg': 10, 'exp': 28,  'gold': 28,  'color': '#4a5a8a',
                 'def': 6, 'weak': 'thunder', 'resist': 'ice',    'atk': 'phys',
                 'desc': '正面挡普通攻击：绕背、重武器或雷电。'},
}

# 特效 / 手感参数
HITSTOP_HIT, HITSTOP_CRIT, HITSTOP_HURT = 2, 5, 3   # 命中停顿帧数
BOMB_RADIUS, BOMB_ENEMY_DMG = 76, 36
MAX_FX = 40


def parse_aim(v):
    """校验客户端上报的鼠标位置（画面坐标，[x, y]）。不合法返回 None，合法则夹到画面范围内。

    注意：Python 的 json 默认接受 NaN / Infinity，还允许任意大的整数，
    所以要显式检查 isfinite，并处理 float() 的 OverflowError。
    """
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return None
    out = []
    for n in v:
        if isinstance(n, bool) or not isinstance(n, (int, float)):
            return None
        try:
            f = float(n)
        except (OverflowError, ValueError):
            return None
        if not math.isfinite(f):
            return None
        out.append(f)
    return (max(0.0, min(float(W), out[0])), max(0.0, min(float(H), out[1])))


def weapon_power(index):
    """按每秒伤害估算武器强度，用于判断宝箱武器是否值得自动装备。"""
    w = WEAPONS[index]
    return w['dmg'] * 60.0 / w['cd']


def build_catalog():
    """前端需要的资料目录：元素、武器、盔甲、怪物图鉴。"""
    enemies = {}
    for t, d in ENEMY_DEFS.items():
        enemies[t] = {'name': d['name'], 'hp': d['hp'], 'def': d['def'], 'weak': d['weak'],
                      'resist': d['resist'], 'atk': d['atk'], 'desc': d['desc'], 'boss': t == 'wizard'}
    return {'elements': ELEMENTS, 'weapons': [dict(w) for w in WEAPONS],
            'armors': [dict(a) for a in ARMORS], 'enemies': enemies}


CATALOG = build_catalog()
