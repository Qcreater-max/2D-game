"""敌人工厂与通用 AI（巫师 Boss 见 boss.py）。"""
import math
from game_data import (ENEMY_DEFS, GRAVITY, MAX_FALL, GROUND_Y, H,
                       BOMB_RADIUS, BOMB_ENEMY_DMG, SLOW_FACTOR, BURN_TICK)
from physics import has_ground_at, move_body, rects_overlap

TOUCH_TYPES = ('slime', 'goblin', 'bat', 'bomber', 'boar')


class EnemyMixin:
    def make_enemy(self, etype, x, y):
        d = ENEMY_DEFS[etype]
        return {
            'type': etype, 'x': float(x), 'y': float(y), 'vx': 0.0, 'vy': 0.0,
            'w': d['w'], 'h': d['h'], 'hp': d['hp'], 'maxHp': d['hp'],
            'dmg': d['dmg'], 'exp': d['exp'], 'gold': d['gold'], 'color': d['color'],
            'fly': d.get('fly', False), 'boss': etype == 'wizard',
            'dir': -1, 'atkCD': 60, 'hurtT': 0, 'dying': 0, 'alive': True,
            'onGround': False, 'hitWall': False, 'aiT': self.rng.randint(0, 60),
            'homeX': float(x), 'kb': 0.0, 'mode': 'idle', 'modeT': 0,
            'def': d['def'], 'weak': d['weak'], 'resist': d['resist'], 'atkElem': d['atk'],
            'burn': 0, 'burnDmg': 0, 'slow': 0,
        }

    def update_enemies(self):
        p = self.player
        for e in self.enemies:
            if not e['alive']:
                e['dying'] -= 1
                continue
            e['aiT'] += 1
            e['hurtT'] = max(0, e['hurtT'] - 1)
            if e['burn'] > 0:                       # 灼烧：每 BURN_TICK 帧掉一次血
                e['burn'] -= 1
                if e['burn'] % BURN_TICK == 0:
                    self.damage_enemy(e, e['burnDmg'], 0, elem='fire', silent_crit=True, dot=True)
                    if not e['alive']:
                        continue
            if e['slow'] > 0:
                e['slow'] -= 1
            getattr(self, 'ai_' + e['type'])(e, p)
            self.move_enemy(e)
            touching = e['type'] in TOUCH_TYPES or (e['type'] == 'wizard' and e['mode'] == 'fall')
            if e['alive'] and touching and rects_overlap(p, e):
                self.damage_player(e['dmg'], e['x'] + e['w'] / 2, elem=e['atkElem'])
        self.enemies = [e for e in self.enemies if e['alive'] or e['dying'] > 0]

    def move_enemy(self, e):
        # AI 设定的速度（蝙蝠俯冲等会跨帧保持）不能被减速 / 击退污染，所以先存下来，移动完再还原
        ai_vx, ai_vy = e['vx'], e['vy']
        f = SLOW_FACTOR if e['slow'] > 0 else 1.0
        e['vx'] = ai_vx * f + e['kb']
        e['kb'] = e['kb'] * 0.8 if abs(e['kb']) > 0.2 else 0.0
        if e['fly']:
            e['hitWall'] = False
            e['x'] += e['vx']
            e['y'] = max(30, min(GROUND_Y - e['h'], e['y'] + ai_vy * f))
        else:
            e['vy'] = min(MAX_FALL, e['vy'] + GRAVITY)
            move_body(e, self.platforms)
        e['vx'] = ai_vx
        if e['x'] < 0 or e['x'] + e['w'] > self.mapW:
            e['x'] = max(0, min(self.mapW - e['w'], e['x']))
            e['hitWall'] = True
        if e['y'] > H + 100:
            e['alive'] = False
            e['dying'] = 0

    def can_step(self, e, d):
        """前方是否还有地面，用于避免敌人自己走下悬崖。"""
        ax = e['x'] + e['w'] + 4 if d > 0 else e['x'] - 4
        return has_ground_at(self.platforms, ax, e['y'] + e['h'] + 6)

    def patrol(self, e, speed, radius):
        off = e['x'] - e['homeX']
        if abs(off) > radius:
            e['dir'] = -1 if off > 0 else 1
        elif e['hitWall'] or (e['onGround'] and not self.can_step(e, e['dir'])):
            e['dir'] = -e['dir']
        e['vx'] = e['dir'] * speed

    def enemy_shot(self, e, kind, vx, vy, w, h, life, color, y=None, elem=None):
        # 巫师的火球是火，冲击波是雷；其余沿用怪物自己的攻击元素
        elem = elem or {'fireball': 'fire', 'wave': 'thunder'}.get(kind, e['atkElem'])
        self.enemyProj.append({
            'kind': kind, 'x': e['x'] + e['w'] / 2, 'y': e['y'] + 10 if y is None else y,
            'vx': vx, 'vy': vy, 'w': w, 'h': h, 'dmg': e['dmg'], 'life': life, 'color': color,
            'elem': elem,
        })

    # ---------- 各类敌人 ----------
    def ai_slime(self, e, p):
        self.patrol(e, 0.7, 120)
        if e['onGround'] and e['aiT'] % 70 == 0:
            e['vy'] = -5.5

    def ai_goblin(self, e, p):
        dx, dy = p['x'] - e['x'], p['y'] - e['y']
        e['atkCD'] -= 1
        if abs(dx) < 280 and abs(dy) < 130:
            e['dir'] = 1 if dx > 0 else -1
            safe = (not e['onGround']) or self.can_step(e, e['dir'])
            e['vx'] = e['dir'] * 1.5 if safe and abs(dx) > 6 else 0
            wants_jump = e['hitWall'] or (dy < -50 and abs(dx) < 70)
            if e['onGround'] and wants_jump and e['atkCD'] <= 0:
                e['vy'] = -8.5
                e['atkCD'] = 45
        else:
            self.patrol(e, 0.6, 90)

    def ai_skeleton(self, e, p):
        dx = p['x'] - e['x']
        e['atkCD'] -= 1
        if abs(dx) >= 420:
            self.patrol(e, 0.5, 100)
            return
        e['dir'] = 1 if dx > 0 else -1
        want = e['dir'] if abs(dx) > 210 else (-e['dir'] if abs(dx) < 110 else 0)
        if want and e['onGround'] and not self.can_step(e, want):
            want = 0
        e['vx'] = want * 0.9
        if abs(dx) < 340 and abs(p['y'] - e['y']) < 90 and e['atkCD'] <= 0:
            e['atkCD'] = 120
            self.enemy_shot(e, 'bone', e['dir'] * 3.2, 0, 10, 6, 110, '#e0e0c0')

    def ai_bat(self, e, p):
        px, py = p['x'] + p['w'] / 2, p['y'] + p['h'] / 2
        if e['mode'] == 'dive':
            e['modeT'] -= 1
            if e['modeT'] <= 0:
                e['mode'], e['atkCD'] = 'idle', 90
        else:
            tx, ty = px + math.sin(e['aiT'] * 0.03) * 140, py - 95
            d = math.hypot(tx - e['x'], ty - e['y']) or 1
            e['vx'], e['vy'] = (tx - e['x']) / d * 1.6, (ty - e['y']) / d * 1.6
            e['atkCD'] -= 1
            if e['atkCD'] <= 0 and abs(px - e['x']) < 320:
                d = math.hypot(px - e['x'], py - e['y']) or 1
                e['vx'], e['vy'] = (px - e['x']) / d * 3.4, (py - e['y']) / d * 3.4
                e['mode'], e['modeT'] = 'dive', 36
        e['dir'] = 1 if e['vx'] >= 0 else -1

    def ai_archer(self, e, p):
        """保持 200~330 像素的距离；站稳后抛物线射箭，玩家贴近时后撤并起跳拉开。"""
        dx = p['x'] - e['x']
        e['atkCD'] -= 1
        if abs(dx) > 520:
            self.patrol(e, 0.5, 80)
            return
        e['dir'] = 1 if dx > 0 else -1
        want = 0
        if abs(dx) < 200:
            want = -e['dir']
        elif abs(dx) > 330:
            want = e['dir']
        if want and e['onGround'] and not self.can_step(e, want):
            want = 0
        e['vx'] = want * 1.1
        if abs(dx) < 140 and e['onGround'] and e['aiT'] % 90 == 0:
            e['vy'] = -7
        if e['atkCD'] <= 0 and abs(dx) < 460 and e['onGround']:
            e['atkCD'] = 105
            # 抛物线：按水平距离估算飞行时间，反推出初始竖直速度（箭受重力 0.12 影响）
            t = max(25.0, min(60.0, abs(dx) / 5.0))
            vy = -(0.12 * t) / 2 + (p['y'] - e['y']) / t
            self.enemy_shot(e, 'arrow', e['dir'] * abs(dx) / t, vy, 14, 5, int(t) + 30, '#c8a060', y=e['y'] + 8)
            self.enemyProj[-1]['grav'] = 0.12

    def ai_bomber(self, e, p):
        """追击玩家；进入 70 像素后点燃引信，闪烁 45 帧后爆炸。"""
        dx = p['x'] - e['x']
        dist = math.hypot(dx, p['y'] - e['y'])
        e['dir'] = 1 if dx > 0 else -1
        if e['mode'] == 'fuse':
            e['modeT'] += 1
            e['vx'] = e['dir'] * 0.5
            if e['modeT'] >= 45:
                self.explode(e)
            return
        if dist < 420:
            safe = (not e['onGround']) or self.can_step(e, e['dir'])
            e['vx'] = e['dir'] * 1.7 if safe else 0
            if e['hitWall'] and e['onGround']:
                e['vy'] = -7
        else:
            self.patrol(e, 0.6, 80)
        if dist < 70:
            e['mode'], e['modeT'] = 'fuse', 0

    def ai_boar(self, e, p):
        """发现玩家后低头蓄力，然后沿直线冲撞；撞墙或冲到尽头会眩晕，眩晕时受伤加成。"""
        dx = p['x'] - e['x']
        dy = abs(p['y'] - e['y'])
        e['modeT'] += 1
        mode = e['mode']
        if mode == 'charge':
            e['vx'] = e['dir'] * 5.2
            if e['hitWall'] or e['modeT'] > 70 or (e['onGround'] and not self.can_step(e, e['dir'])):
                if e['hitWall']:
                    self.game['shake'] = max(self.game['shake'], 5)
                e['mode'], e['modeT'] = 'stun', 0
            return
        if mode == 'windup':
            e['vx'] = 0
            if e['modeT'] >= 40:
                e['mode'], e['modeT'] = 'charge', 0
            return
        if mode == 'stun':
            e['vx'] = 0
            if e['modeT'] >= 70:
                e['mode'], e['modeT'], e['atkCD'] = 'idle', 0, 60
            return
        e['atkCD'] -= 1
        if abs(dx) < 380 and dy < 70:
            e['dir'] = 1 if dx > 0 else -1
            e['vx'] = e['dir'] * 0.8
            if e['atkCD'] <= 0 and abs(dx) > 90:
                e['mode'], e['modeT'] = 'windup', 0
        else:
            self.patrol(e, 0.5, 100)

    def ai_shield(self, e, p):
        """缓慢逼近并始终面朝玩家，正面受到的普通攻击会被挡下；近身后用盾猛击。"""
        dx = p['x'] - e['x']
        e['atkCD'] -= 1
        if e['mode'] == 'bash':
            e['modeT'] += 1
            e['vx'] = 0
            if e['modeT'] == 14:
                reach = {'x': e['x'] - 14 if e['dir'] < 0 else e['x'] + e['w'] - 4,
                         'y': e['y'], 'w': 18, 'h': e['h']}
                if rects_overlap(reach, p):
                    self.damage_player(e['dmg'], e['x'] + e['w'] / 2)
            if e['modeT'] >= 30:
                e['mode'], e['modeT'], e['atkCD'] = 'idle', 0, 70
            return
        if e['mode'] == 'stun':        # 盾被打破后的硬直
            e['modeT'] += 1
            e['vx'] = 0
            if e['modeT'] >= 60:
                e['mode'], e['modeT'] = 'idle', 0
            return
        if abs(dx) < 360:
            e['dir'] = 1 if dx > 0 else -1
            safe = (not e['onGround']) or self.can_step(e, e['dir'])
            e['vx'] = e['dir'] * 0.7 if safe and abs(dx) > 40 else 0
            if abs(dx) < 54 and e['atkCD'] <= 0:
                e['mode'], e['modeT'] = 'bash', 0
        else:
            self.patrol(e, 0.4, 60)

    # ---------- 爆炸 ----------
    def explode(self, e):
        """自爆虫爆炸：范围内玩家受伤，其他敌人受固定伤害（可连锁引爆）。"""
        if e.get('exploded'):
            return
        e['exploded'] = True
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2
        self.add_blast(cx, cy, BOMB_RADIUS)
        p = self.player
        if math.hypot(p['x'] + p['w'] / 2 - cx, p['y'] + p['h'] / 2 - cy) < BOMB_RADIUS:
            self.damage_player(e['dmg'], cx, elem='fire')
        if e['alive']:
            e['alive'], e['dying'], e['hp'] = False, 6, 0
        for o in self.enemies:
            if o is e or not o['alive']:
                continue
            if math.hypot(o['x'] + o['w'] / 2 - cx, o['y'] + o['h'] / 2 - cy) < BOMB_RADIUS:
                # 爆炸无视盾卫的格挡；火焰会让被炸到的敌人燃烧
                self.damage_enemy(o, BOMB_ENEMY_DMG, 1 if o['x'] > cx else -1, silent_crit=True,
                                  elem='fire', pierce=True)
