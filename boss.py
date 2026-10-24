"""暗影巫师 Boss：悬浮弹幕 → 蓄力 → 砸地（冲击波）→ 硬直（输出窗口）。"""
import math
from game_data import GROUND_Y


class BossMixin:
    def ai_wizard(self, e, p):
        enraged = e['hp'] < e['maxHp'] * 0.5
        e['dir'] = 1 if p['x'] > e['x'] else -1
        e['modeT'] += 1
        if e['mode'] == 'idle':
            e['mode'], e['modeT'] = 'hover', 0
        mode = e['mode']

        if mode == 'hover':
            dx = p['x'] - e['x']
            e['vy'] = (150 + math.sin(e['aiT'] * 0.04) * 40 - e['y']) * 0.05
            if abs(dx) > 300:
                e['vx'] = e['dir'] * 1.0
            elif abs(dx) < 170:
                e['vx'] = -e['dir'] * 0.8
            else:
                e['vx'] = 0
            interval = 70 if enraged else 100
            if e['modeT'] % interval == 0:
                self.boss_volley(e, p, 5 if enraged else 3)
            if e['modeT'] >= interval * 4:
                e['mode'], e['modeT'] = 'windup', 0
        elif mode == 'windup':
            e['vx'] = max(-3.0, min(3.0, (p['x'] - e['x']) * 0.08))
            e['vy'] = -0.5
            if e['modeT'] >= 45:
                e['mode'], e['modeT'] = 'fall', 0
        elif mode == 'fall':
            e['vx'], e['vy'] = 0, 11
            if e['y'] + e['h'] >= GROUND_Y - 0.5:
                self.boss_slam(e, enraged)
                e['mode'], e['modeT'] = 'stun', 0
        elif mode == 'stun':
            e['vx'] = e['vy'] = 0
            if e['modeT'] >= (80 if enraged else 110):
                e['mode'], e['modeT'] = 'hover', 0

    def boss_volley(self, e, p, n):
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2
        base = math.atan2(p['y'] + p['h'] / 2 - cy, p['x'] + p['w'] / 2 - cx)
        for i in range(n):
            a = base + (i - (n - 1) / 2.0) * 0.22
            self.enemy_shot(e, 'fireball', math.cos(a) * 3.6, math.sin(a) * 3.6,
                            14, 14, 140, '#ff4020', y=cy)

    def boss_slam(self, e, enraged):
        e['y'] = GROUND_Y - e['h']
        self.game['shake'] = 12
        cx = e['x'] + e['w'] / 2
        self.add_particles(cx, GROUND_Y, 30, '#c040ff', 5)
        speeds = (3.4, 5.0) if enraged else (3.4,)
        for sp in speeds:
            for d in (-1, 1):
                self.enemy_shot(e, 'wave', d * sp, 0, 26, 28, 400, '#c040ff', y=GROUND_Y - 14)
                self.enemyProj[-1]['x'] = cx
