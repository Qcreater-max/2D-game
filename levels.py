"""关卡数据。

主线关卡（LEVEL_ORDER 里的）和地下子关卡（'sub_' 开头，通过地洞进入）共用同一套格式：

ground  ：地面区段 (起点x, 终点x)，之间的空隙是深坑
plats   ：单向平台 (x, y, 宽)
enemies ：(类型, x[, y])，缺省 y 时落在地面上
chests  ：(x, 所在表面的 y, 内容)，内容为 ('gold', 数量) / ('weapon', 序号) / ('armor', 序号)
smithX / portalX：铁匠铺与传送门的 x 坐标（None 表示没有）
theme   ：渲染主题，见 render.js 的 THEMES

以下字段可选：
hazards ：危险物 (种类, x, 宽)，种类 spikes / lava / poison，站在地面上，接触掉血
movers  ：移动平台 (x, y, 宽, 沿x摆动的幅度, 周期帧数)，会带着站在上面的玩家一起走
crates  ：可破坏木箱 (x, 所在表面的 y)，打碎后掉落金币或回血
holes   ：地洞入口 (x, 子关卡名)，站在上面按 S + E 进入
secrets ：隐藏房间 (x, 墙的血量, 房间内宝箱 give)，攻击"可疑裂墙"数次后破开
back    ：仅子关卡有，返回地面的出口 x

平台间距按玩家的跳跃能力设计：单次跳跃最高约 130 像素，
满速跳过的水平距离约 115 像素（最宽的坑为 100 像素）。
改动数值或关卡后，请重新检查这两个上限（tests/test_levels.py 会自动检查）。
"""
from game_data import GROUND_Y, ENEMY_DEFS

HINT_MOVE = 'A/D 移动   W/空格 跳跃   J 攻击   E 互动'

LEVEL_DATA = {
    # ------------------------------------------------------------ 1 森林
    'forest': {
        'mapW': 2600, 'theme': 'forest',
        'title': '第一关  森林入门', 'hint': HINT_MOVE,
        'ground': [(0, 600), (680, 1260), (1340, 1900), (1980, 2600)],
        'plats': [
            (200, 400, 110), (380, 330, 110), (700, 400, 100), (880, 330, 110),
            (1060, 400, 100), (1400, 400, 100), (1580, 330, 110), (1760, 260, 100),
            (2060, 400, 100), (2230, 330, 110),
        ],
        'enemies': [
            ('slime', 450), ('goblin', 780), ('slime', 900), ('bomber', 1100),
            ('boar', 1500), ('slime', 1650), ('goblin', 1750), ('bomber', 2100),
            ('archer', 2250), ('boar', 2350),
        ],
        'chests': [
            (420, 330, ('gold', 30)), (920, 330, ('armor', 1)),
            (1790, 260, ('weapon', 1)), (2260, 330, ('gold', 50)),
        ],
        'crates': [(300, GROUND_Y), (1180, GROUND_Y), (2000, GROUND_Y)],
        'holes': [(1000, 'sub_root')],
        'secrets': [(1620, 3, ('weapon', 6))],
        'smithX': 2400, 'portalX': 2520,
    },
    # ------------------------------------------------------------ 2 沼泽
    'swamp': {
        'mapW': 2900, 'theme': 'swamp',
        'title': '第二关  幽暗沼泽', 'hint': '毒沼会持续掉血，沿着平台走；野猪冲锋时可以跳过它',
        'ground': [(0, 520), (610, 1000), (1090, 1500), (1590, 2050), (2140, 2900)],
        # 平台最高比地面高 150（跳跃上限 124），所以高处都做成"先踩中间一级"的台阶
        'plats': [
            (180, 400, 100), (350, 330, 100), (540, 400, 90), (640, 330, 90), (700, 400, 100),
            (1100, 380, 100), (1280, 320, 100), (1620, 400, 100), (1800, 340, 100),
            (1990, 400, 90), (2090, 330, 90), (2200, 400, 100), (2400, 400, 90), (2490, 330, 100),
        ],
        'enemies': [
            ('slime', 400), ('bomber', 700), ('archer', 900), ('boar', 1200),
            ('goblin', 1400), ('archer', 1700), ('bomber', 1850), ('slime', 2300),
            ('boar', 2500), ('shield', 2650),
        ],
        'hazards': [('poison', 520, 90), ('poison', 1000, 90), ('poison', 1500, 90), ('poison', 2050, 90)],
        'chests': [
            (380, 330, ('gold', 50)), (670, 330, ('armor', 2)),
            (1310, 320, ('weapon', 6)), (2120, 330, ('gold', 70)), (2520, 330, ('weapon', 2)),
        ],
        'crates': [(250, GROUND_Y), (850, GROUND_Y), (1700, GROUND_Y), (2350, GROUND_Y)],
        'holes': [(780, 'sub_mine')],
        'secrets': [(1960, 3, ('armor', 3))],
        'smithX': 2780, 'portalX': 2850,
    },
    # ------------------------------------------------------------ 3 骷髅地穴
    'crypt': {
        'mapW': 2800, 'theme': 'crypt',
        'title': '第三关  骷髅地穴', 'hint': '骷髅会远程投骨，蝙蝠会俯冲，盾卫要绕背或用重武器',
        'ground': [(0, 520), (610, 1150), (1240, 1800), (1900, 2400), (2490, 2800)],
        'plats': [
            (200, 400, 100), (370, 330, 100), (540, 260, 100), (700, 400, 100),
            (870, 330, 100), (1040, 400, 100), (1300, 400, 100), (1470, 330, 100),
            (1640, 260, 100), (1960, 400, 100), (2130, 330, 100),
        ],
        'enemies': [
            ('skeleton', 400), ('bat', 650, 200), ('shield', 800), ('archer', 1000),
            ('bomber', 1300), ('bat', 1250, 180), ('shield', 1550), ('skeleton', 1700),
            ('bat', 1900, 200), ('archer', 2050), ('bomber', 2250), ('shield', 2300),
            ('bat', 2450, 180),
        ],
        'chests': [
            (400, 330, ('gold', 60)), (570, 260, ('weapon', 5)), (900, 330, ('armor', 2)),
            (1330, 400, ('gold', 80)), (1670, 260, ('weapon', 3)), (2160, 330, ('armor', 3)),
        ],
        'hazards': [('spikes', 520, 90), ('spikes', 1150, 90)],
        'crates': [(330, GROUND_Y), (1400, GROUND_Y), (2100, GROUND_Y)],
        'secrets': [(1180, 4, ('weapon', 7))],
        'smithX': 2620, 'portalX': 2730,
    },
    # ------------------------------------------------------------ 4 熔岩洞
    'lava': {
        'mapW': 3000, 'theme': 'lava',
        'title': '第四关  熔岩洞窟', 'hint': '岩浆一碰就掉血；移动平台会带着你走，注意站稳',
        # 每个岩浆坑都不超过 100 像素，不依赖移动平台也能直接跳过；
        # 移动平台是额外的捷径，通向坑上方的宝箱。
        'ground': [(0, 500), (600, 900), (1000, 1260), (1360, 1700), (1800, 2100), (2200, 3000)],
        'plats': [
            (160, 400, 110), (330, 330, 100),
            (700, 380, 100), (1100, 380, 100), (1450, 380, 100),
            (1900, 380, 100), (2300, 320, 100), (2480, 260, 100),
        ],
        'movers': [(520, 400, 70, 40, 180), (920, 400, 70, 40, 200), (1280, 400, 70, 40, 160),
                   (1720, 400, 70, 40, 170), (2120, 400, 70, 40, 190)],
        'enemies': [
            ('bomber', 380), ('boar', 700), ('archer', 800), ('bat', 1100, 200), ('shield', 1450),
            ('bomber', 1600), ('archer', 1900), ('boar', 2300), ('bat', 2400, 200), ('shield', 2700),
        ],
        'hazards': [('lava', 500, 100), ('lava', 900, 100), ('lava', 1260, 100),
                    ('lava', 1700, 100), ('lava', 2100, 100)],
        'chests': [
            (360, 330, ('gold', 90)), (730, 380, ('armor', 5)), (1130, 380, ('weapon', 4)),
            (2510, 260, ('gold', 120)),
        ],
        'crates': [(460, GROUND_Y), (1500, GROUND_Y), (2600, GROUND_Y)],
        'smithX': 2850, 'portalX': 2930,
    },
    # ------------------------------------------------------------ 5 暗影要塞
    'fortress': {
        'mapW': 3000, 'theme': 'fortress',
        'title': '第五关  暗影要塞', 'hint': '最后的防线：盾卫、弓手和自爆虫会配合出现',
        'ground': [(0, 700), (790, 1500), (1590, 2300), (2390, 3000)],
        # 每级台阶比下一级低不超过 80，保证一次跳跃就能上去
        'plats': [
            (250, 400, 110), (450, 340, 100), (850, 400, 100), (1000, 340, 100), (1150, 280, 100),
            (1650, 400, 100), (1800, 340, 100), (2050, 400, 100),
            (2450, 400, 100), (2600, 340, 100), (2750, 280, 100),
        ],
        'enemies': [
            ('shield', 500), ('archer', 600), ('bomber', 900), ('shield', 1100), ('archer', 1300),
            ('boar', 1700), ('bomber', 1850), ('skeleton', 2000), ('shield', 2150),
            ('archer', 2500), ('bomber', 2650), ('shield', 2800),
        ],
        'hazards': [('spikes', 700, 90), ('spikes', 1500, 90), ('spikes', 2300, 90)],
        'chests': [
            (480, 340, ('gold', 100)), (1180, 280, ('armor', 4)), (1830, 340, ('weapon', 7)),
            (2780, 280, ('gold', 150)),
        ],
        'crates': [(350, GROUND_Y), (1000, GROUND_Y), (1800, GROUND_Y), (2500, GROUND_Y)],
        'smithX': 2880, 'portalX': 2940,
    },
    # ------------------------------------------------------------ 6 Boss
    'boss': {
        'mapW': 960, 'theme': 'boss',
        'title': '最终关  暗影巫师', 'hint': '巫师落地时是输出机会，冲击波可以跳过去',
        'ground': [(0, 960)],
        # 中间那块以前高 180，一次跳不上去；降到 370，和两侧平台形成可以逐级爬上去的三角
        'plats': [(150, 400, 120), (690, 400, 120), (420, 370, 120)],
        'enemies': [('wizard', 700, 150)],
        'chests': [],
        'smithX': 70, 'portalX': None,
    },

    # ================================================== 地下子关卡（通过地洞进入）
    'sub_root': {
        'mapW': 1500, 'theme': 'cave', 'back': 120,
        'title': '地下  树根洞穴', 'hint': '地下藏着额外的宝箱。走到左边的梯子按 E 返回地面',
        'ground': [(0, 500), (590, 1000), (1090, 1500)],
        'plats': [(220, 390, 100), (400, 330, 90), (700, 390, 100), (820, 340, 90), (910, 290, 90),
                  (1180, 390, 100), (1330, 330, 90)],
        'enemies': [('slime', 300), ('bat', 700, 220), ('goblin', 850), ('bomber', 1200)],
        'hazards': [('spikes', 500, 90), ('spikes', 1000, 90)],
        'chests': [(430, 330, ('gold', 80)), (940, 290, ('armor', 2)), (1360, 330, ('weapon', 5))],
        'crates': [(650, GROUND_Y), (1250, GROUND_Y)],
        'smithX': None, 'portalX': None,
    },
    'sub_mine': {
        'mapW': 1700, 'theme': 'cave', 'back': 120,
        'title': '地下  废弃矿坑', 'hint': '矿坑里有更强的怪物，也有更好的奖励',
        'ground': [(0, 450), (540, 900), (990, 1300), (1390, 1700)],
        'plats': [(200, 400, 100), (350, 330, 90), (600, 400, 100), (770, 330, 90), (1040, 400, 100), (1200, 330, 90), (1450, 400, 100), (1580, 320, 90)],
        'enemies': [('skeleton', 300), ('shield', 650), ('bat', 800, 220), ('archer', 1100), ('boar', 1500), ('bomber', 1620)],
        'hazards': [('spikes', 450, 90), ('spikes', 900, 90), ('spikes', 1300, 90)],
        'chests': [(380, 330, ('gold', 100)), (800, 330, ('weapon', 6)), (1230, 330, ('armor', 3)), (1600, 320, ('gold', 140))],
        'crates': [(400, GROUND_Y), (1100, GROUND_Y)],
        'smithX': None, 'portalX': None,
    },
}

# 无尽模式竞技场：一屏宽的平地加三块平台，怪物从两侧涌入
LEVEL_DATA['arena'] = {
    'mapW': 960, 'theme': 'arena',
    'title': '无尽挑战', 'hint': '一波接一波的敌人。撑得越久，成绩越高',
    'ground': [(0, 960)],
    # 中间平台比地面高 120，测试留的安全余量是 114，所以先从左右两块 80 高的踏脚台阶上去
    'plats': [(120, 400, 130), (710, 400, 130), (330, 400, 80), (550, 400, 80), (415, 330, 130)],
    'enemies': [], 'chests': [], 'crates': [(480, GROUND_Y)],
    'smithX': 480, 'portalX': None,
}

# 隐藏房间内部：一间小屋，只有一个宝箱，出口在左边
SECRET_ROOM = {
    'mapW': 700, 'theme': 'secret', 'back': 90,
    'title': '隐藏房间', 'hint': '你发现了秘密！打开宝箱，然后从左边出去',
    'ground': [(0, 700)], 'plats': [],
    'enemies': [], 'hazards': [], 'crates': [],
    'smithX': None, 'portalX': None,
}


def is_sub(name):
    return name.startswith('sub_') or name.startswith('secret_')


def build_data(name):
    """返回关卡原始数据；隐藏房间按父关卡的 secrets 条目动态生成（name 形如 secret_<父关>_<序号>）。"""
    if name in LEVEL_DATA:
        return LEVEL_DATA[name]
    if name.startswith('secret_'):
        _, parent, idx = name.split('_', 2)
        x, hp, give = LEVEL_DATA[parent]['secrets'][int(idx)]
        d = dict(SECRET_ROOM)
        d['chests'] = [(340, GROUND_Y, give)]        # 放在地面，进门走几步就能开，不用爬
        return d
    raise KeyError(name)


def load_level(name):
    """返回关卡的全新副本（平台、敌人出生点、宝箱、危险物等）。"""
    d = build_data(name)
    platforms = [{'x': a, 'y': GROUND_Y, 'w': b - a, 'h': 60, 'type': 'ground'}
                 for a, b in d['ground']]
    platforms += [{'x': x, 'y': y, 'w': w, 'h': 16, 'type': 'plat'}
                  for x, y, w in d['plats']]
    movers = []
    for x, y, w, amp, period in d.get('movers', []):
        pl = {'x': float(x), 'y': y, 'w': w, 'h': 16, 'type': 'plat', 'mover': True}
        movers.append({'plat': pl, 'x0': x, 'amp': amp, 'period': period})
        platforms.append(pl)
    spawns = []
    for spec in d['enemies']:
        etype, x = spec[0], spec[1]
        y = spec[2] if len(spec) > 2 else GROUND_Y - ENEMY_DEFS[etype]['h'] - 1
        spawns.append((etype, x, y))
    chests = [{'x': x, 'y': sy - 28, 'w': 28, 'h': 28, 'opened': False, 'give': give}
              for x, sy, give in d['chests']]
    hazards = [{'kind': k, 'x': x, 'y': GROUND_Y - 6, 'w': w, 'h': 40}
               for k, x, w in d.get('hazards', [])]
    crates = [{'x': x - 14, 'y': sy - 28, 'w': 28, 'h': 28, 'hp': 2} for x, sy in d.get('crates', [])]
    holes = [{'x': x, 'to': to} for x, to in d.get('holes', [])]
    secrets = [{'x': x, 'hp': hp, 'maxHp': hp, 'idx': i, 'open': False}
               for i, (x, hp, give) in enumerate(d.get('secrets', []))]
    return {
        'mapW': d['mapW'], 'title': d['title'], 'hint': d['hint'], 'theme': d.get('theme', 'forest'),
        'platforms': platforms, 'movers': movers, 'spawns': spawns, 'chests': chests,
        'hazards': hazards, 'crates': crates, 'holes': holes, 'secrets': secrets,
        'back': d.get('back'),
        'smithX': d['smithX'], 'portalX': d['portalX'],
    }
