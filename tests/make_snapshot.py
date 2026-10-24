"""生成渲染测试用的状态快照，写入 harness_state.js。

用法: python tests/make_snapshot.py [场景]
场景: combat（默认，第 1 期的怪物和特效）| lava | swamp | cave | secret | menu | endless
然后用无头浏览器打开 tests/render_harness.html 截图。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from game_engine import GameEngine
from game_data import INPUT_KEYS, GROUND_Y


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d['aim'] = None
    d.update(k)
    return d


def fresh(mode_idx=0):
    e = GameEngine(seed=3)
    e.game['menuIdx'] = mode_idx
    e.tick(K(confirm=True))
    e.tick(K())
    return e


def stand(e, x):
    p = e.player
    p['x'], p['y'] = float(x), float(GROUND_Y - p['h'] - 1)
    e.game['camX'] = max(0.0, min(e.mapW - 960, x - 480))


def put(e, etype, x, **kw):
    en = e.make_enemy(etype, x, GROUND_Y - e.make_enemy(etype, 0, 0)['h'] - 1)
    en.update(kw)
    e.enemies.append(en)
    return en


def combat():
    e = fresh()
    e.load('crypt')
    e.game['state'] = 'crypt'
    e.game['introT'] = 0
    e.enemies = []
    stand(e, 200)
    e.camX = 0
    p = e.player
    p['weapon'] = 5
    p['ownedWeapons'] |= {1, 2, 4, 5, 6, 7}
    p['ownedArmors'] |= {1, 2, 5}
    p['armor'], p['gold'], p['attackAnim'], p['facing'] = 2, 260, 7, 1
    put(e, 'archer', 330)
    put(e, 'bomber', 400, mode='fuse', modeT=40)
    put(e, 'boar', 470, mode='windup', modeT=20, dir=-1)
    put(e, 'shield', 580, dir=-1)
    put(e, 'shield', 650, dir=1, mode='stun')
    put(e, 'skeleton', 740, dir=-1, burn=120)
    put(e, 'boar', 810, dir=-1, slow=90)
    e.enemyProj.append({'kind': 'arrow', 'x': 520, 'y': 400, 'vx': 5.0, 'vy': 1.2, 'w': 14, 'h': 5,
                        'dmg': 8, 'life': 40, 'color': '#c8a060', 'elem': 'phys'})
    e.add_fx('spark', 260, 440, life=40, dir=1, color='#fff4c0', big=True)
    e.add_fx('ring', 300, 440, life=40, color='#ffd040')
    e.add_fx('blast', 880, 420, life=40, r=76)
    e.add_fx('bolt', 740, 450, x2=810.0, y2=455.0, life=40)
    for f in e.fx:
        f['t'] = 6
    e.card = {'type': 'shield', 't': 380}
    e.game['hurtFlash'] = 4
    e.game['camX'] = 0.0
    return e


def lava():
    e = fresh()
    e.load('lava')
    e.game['state'] = 'lava'
    e.game['introT'] = 0
    e.enemies = []
    stand(e, 420)
    put(e, 'archer', 700)
    put(e, 'bomber', 800)
    e.game['camX'] = 300.0
    for m in e.movers:                      # 把移动平台摆到不同相位，画面更有代表性
        m['plat']['x'] = m['x0'] + m['amp'] * 0.6
    e.player['x'] = 590.0
    return e


def swamp():
    e = fresh()
    e.load('swamp')
    e.game['state'] = 'swamp'
    e.game['introT'] = 0
    e.enemies = []
    stand(e, 540)
    e.player['x'] = 548.0
    e.player['y'] = float(GROUND_Y - e.player['h'] - 1)
    put(e, 'boar', 800)
    put(e, 'archer', 900)
    e.game['camX'] = 300.0
    e.game['time'] = 400
    return e


def cave():
    e = fresh()
    e.load('sub_root')
    e.game['state'] = 'sub_root'
    e.return_stack.append({'level': 'forest'})
    e.game['introT'] = 0
    e.enemies = []
    stand(e, 220)
    e.game['camX'] = 0.0
    put(e, 'slime', 330)
    put(e, 'goblin', 560)
    return e


def secret():
    e = fresh()
    e.load('forest')
    e.game['state'] = 'forest'
    e.game['introT'] = 0
    e.enemies = []
    s = e.secrets[0]
    s['hp'] = 1                               # 裂缝已经很深
    stand(e, s['x'] - 90)
    e.game['camX'] = s['x'] - 480.0
    e.crates[0]['hp'] = 1
    return e


def menu():
    e = GameEngine(seed=3)
    e.game['menuIdx'] = 1
    e.game['bestWave'] = 7
    e.game['time'] = 40
    return e


def endless():
    e = fresh(1)
    e.game['introT'] = 0
    e.game['camX'] = 0.0
    e.card = None
    return e


SCENES = {'combat': combat, 'lava': lava, 'swamp': swamp, 'cave': cave, 'secret': secret,
          'menu': menu, 'endless': endless}

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'combat'
    e = SCENES[name]()
    e.update_cards() if name != 'combat' and e.card is None and False else None
    snap = {'state': e.get_state(), 'level': e.level_message()}
    with open(os.path.join(HERE, 'harness_state.js'), 'w', encoding='utf-8') as fh:
        fh.write('const SNAPSHOT = ' + json.dumps(snap) + ';\n')
    print('snapshot [%s]: state=%s theme=%s, %d enemies, %d hazards' % (
        name, snap['state']['game']['state'], snap['state']['game']['theme'],
        len(snap['state']['enemies']), len(snap['level']['hazards'])))
