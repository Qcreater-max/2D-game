"""为截图生成某个场景的状态快照,写入本目录的 state.js(不改动仓库里的 tests/harness_state.js)。

用法: python make_state.py <场景>
场景: menu combat lava swamp secret boss cave endless
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.dirname(os.path.dirname(HERE))      # 仓库根目录(presentation/harness 的上两级)
sys.path.insert(0, DEMO)
sys.path.insert(0, os.path.join(DEMO, 'tests'))

import make_snapshot as ms
from game_data import GROUND_Y


def boss():
    e = ms.fresh()
    e.load('boss')
    e.game['state'] = 'boss'
    e.game['introT'] = 0
    ms.stand(e, 300)
    e.player['weapon'] = 5
    e.player['ownedWeapons'] |= {5}
    e.player['attackAnim'] = 6
    e.game['camX'] = 0.0
    w = e.enemies[0]
    w['hp'] = int(w['maxHp'] * 0.6)
    w['mode'], w['modeT'] = 'stun', 20
    w['x'], w['y'] = 520.0, float(GROUND_Y - w['h'])
    e.add_fx('ring', w['x'] + 18, GROUND_Y - 6, life=40, color='#c040ff')
    for f in e.fx:
        f['t'] = 5
    return e


def endless():
    e = ms.fresh(1)
    e.game['introT'] = 0
    e.game['camX'] = 0.0
    e.card = None
    e.player['x'] = 430.0
    e.player['weapon'] = 5
    e.player['ownedWeapons'] |= {5}
    return e


SCENES = dict(ms.SCENES)
SCENES['boss'] = boss
SCENES['endless'] = endless

if __name__ == '__main__':
    name = sys.argv[1]
    e = SCENES[name]()
    snap = {'state': e.get_state(), 'level': e.level_message()}
    with open(os.path.join(HERE, 'state.js'), 'w', encoding='utf-8') as fh:
        fh.write('const SNAPSHOT = ' + json.dumps(snap) + ';\n')
    print('ok', name)
