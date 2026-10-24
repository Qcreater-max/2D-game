"""战斗：玩家攻击、伤害结算、元素与状态、击杀掉落、升级、特效。"""
import math
from game_data import (
    WEAPONS, ARMORS, ELEMENTS, MAX_FX, HITSTOP_HIT, HITSTOP_CRIT, HITSTOP_HURT,
    WEAK_MULT, RESIST_MULT, MIN_DMG_RATIO, BURN_FRAMES, SLOW_FRAMES, CHAIN_RANGE, CHAIN_RATIO,
)
from physics import rects_overlap

MAX_PARTICLES = 300
PHYS_COLOR = '#ff6060'


class CombatMixin:
    # ---------- 特效 ----------
    def add_text(self, x, y, txt, color, size=16):
        self.texts.append({'x': x, 'y': y, 'txt': txt, 'color': color, 'size': size, 't': 60, 'vy': -1.2})

    def add_particles(self, x, y, n, color, spd=3):
        for _ in range(n):
            if len(self.particles) >= MAX_PARTICLES:
                return
            a = self.rng.random() * math.pi * 2
            s = self.rng.random() * spd + 1
            self.particles.append({'x': x, 'y': y, 'vx': math.cos(a) * s, 'vy': math.sin(a) * s - 1,
                                   'life': 30 + self.rng.random() * 20, 'color': color,
                                   'size': 2 + int(self.rng.random() * 3)})

    def show_msg(self, text, frames=90):
        self.game['msg'], self.game['msgT'] = text, frames

    def hitstop(self, frames):
        """命中停顿：世界暂停几帧，让打击有重量感。取较大值，避免叠加成卡顿。"""
        self.game['hitstop'] = max(self.game['hitstop'], frames)

    def add_fx(self, kind, x, y, **kw):
        """一次性视觉特效（火花、冲击环、爆炸、电弧），客户端按 kind 绘制。"""
        if len(self.fx) >= MAX_FX:
            self.fx.pop(0)
        fx = {'kind': kind, 'x': round(x, 1), 'y': round(y, 1), 't': 0}
        fx.update(kw)
        self.fx.append(fx)

    def add_blast(self, x, y, radius):
        self.add_fx('blast', x, y, r=radius, life=22)
        self.add_particles(x, y, 36, '#ff9030', 8)
        self.add_particles(x, y, 16, '#ffe080', 5)
        self.game['shake'] = max(self.game['shake'], 10)
        self.hitstop(4)

    def update_fx(self):
        for f in self.fx:
            f['t'] += 1
        self.fx = [f for f in self.fx if f['t'] < f.get('life', 12)]

    # ---------- 数值 ----------
    def atk_mul(self):
        return 1 + 0.06 * (self.player['level'] - 1)

    def gain_exp(self, n):
        p = self.player
        p['exp'] += n
        while p['exp'] >= p['expNext']:
            p['exp'] -= p['expNext']
            p['level'] += 1
            p['expNext'] = int(p['expNext'] * 1.45)
            p['maxHp'] += 15
            p['hp'] = p['maxHp']
            self.game['flash'] = 30
            self.add_particles(p['x'] + p['w'] / 2, p['y'] + p['h'] / 2, 50, '#ffd84a', 7)
            self.add_text(p['x'] - 10, p['y'] - 10, 'LEVEL UP!', '#ffe040', 22)
            self.show_msg('升级！生命上限+15，攻击力提升，生命已回满', 120)

    # ---------- 玩家攻击 ----------
    def aim_vector(self):
        """鼠标瞄准方向（单位向量）。没有瞄准、或鼠标离角色太近时返回 None，此时沿用朝向。

        客户端只上报鼠标在画面里的位置；这里用服务端自己的镜头位置换算成世界坐标，
        再归一化，所以弹速只由武器决定，客户端无法通过伪造向量改变速度。
        """
        if self.aim is None:
            return None
        p = self.player
        ox, oy = p['x'] + p['w'] / 2, p['y'] + p['h'] / 2 - 4
        dx = self.aim[0] + self.game['camX'] - ox
        dy = self.aim[1] - oy
        d = math.hypot(dx, dy)
        if d < 6:
            return None
        return dx / d, dy / d

    def aim_angle(self):
        """当前瞄准角度（弧度，保留两位小数），没有瞄准时为 None。用于让手持武器指向鼠标。"""
        v = self.aim_vector()
        return None if v is None else round(math.atan2(v[1], v[0]), 2)

    def player_attack(self):
        p = self.player
        w = WEAPONS[p['weapon']]
        p['atkCD'], p['attackAnim'] = w['cd'], 12
        dmg = int(round(w['dmg'] * self.atk_mul()))
        elem = w['elem']
        if w['type'] == 'melee':
            hx = p['x'] + p['w'] if p['facing'] > 0 else p['x'] - w['range']
            box = {'x': hx, 'y': p['y'] - 4, 'w': w['range'], 'h': p['h'] + 8}
            hit = False
            for e in self.enemies:
                if e['alive'] and rects_overlap(box, e):
                    self.damage_enemy(e, dmg, p['facing'], heavy=w.get('heavy', False), elem=elem)
                    hit = True
            hit = self.hit_crates(box) or hit                  # 木箱和裂墙也吃近战
            hit = self.hit_secrets(box) or hit
            p['lunge'] = p['facing'] * (3.0 if hit else 1.6)   # 出招时身体前冲一点
            if hit:
                self.game['shake'] = max(self.game['shake'], 3)
        else:
            speed = w['projSpeed']
            ux, uy = self.aim_vector() or (float(p['facing']), 0.0)
            self.projectiles.append({
                'x': p['x'] + p['w'] / 2 + ux * 16, 'y': p['y'] + p['h'] / 2 - 4 + uy * 16,
                'vx': ux * speed, 'vy': uy * speed, 'dmg': dmg, 'life': w['range'] / speed,
                'color': w['color'], 'heavy': w.get('heavy', False), 'elem': elem,
                'kind': 'fire' if elem == 'fire' else 'arrow'})

    # ---------- 伤害结算 ----------
    def blocked_by_shield(self, e, kdir, elem='phys', pierce=False):
        """盾卫面朝玩家时，来自正面的攻击会被挡下。雷电和爆炸无视格挡；kdir 为 0 表示无方向。"""
        return (e['type'] == 'shield' and e['mode'] != 'stun' and kdir != 0 and kdir == -e['dir']
                and elem != 'thunder' and not pierce)

    def calc_damage(self, e, dmg, elem, crit, stunned):
        """顺序：元素倍率 → 暴击 → 眩晕加成 → 防御（固定减伤，但不低于 30%）。返回 (伤害, 'weak'/'resist'/None)。"""
        mult, tag = 1.0, None
        if e['weak'] == elem:
            mult, tag = WEAK_MULT, 'weak'
        elif e['resist'] == elem:
            mult, tag = RESIST_MULT, 'resist'
        pre = dmg * mult * (2 if crit else 1) * (1.5 if stunned else 1)
        final = max(pre * MIN_DMG_RATIO, pre - e['def'])
        return max(1, int(round(final))), tag

    def damage_enemy(self, e, dmg, kdir=0, heavy=False, silent_crit=False,
                     elem='phys', chain=True, dot=False, pierce=False):
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2
        ecol = ELEMENTS[elem]['color']
        if not pierce and self.blocked_by_shield(e, kdir, elem):
            if heavy:                       # 重击打破格挡，盾卫进入硬直
                e['mode'], e['modeT'] = 'stun', 0
                self.add_fx('ring', cx - kdir * 8, cy, life=14, color='#ffe080')
                self.add_text(e['x'], e['y'] - 10, '破盾！', '#ffe080', 16)
                self.game['shake'] = max(self.game['shake'], 6)
                self.hitstop(HITSTOP_CRIT)
            else:
                e['kb'] = kdir * 1.5
                self.add_fx('spark', cx - kdir * 10, cy, life=8, dir=-kdir, color='#bcd0ff')
                self.add_text(e['x'], e['y'] - 6, '格挡', '#9ab0e0', 13)
                self.hitstop(1)
                return
        crit = (not silent_crit) and self.rng.random() < 0.1
        final, tag = self.calc_damage(e, dmg, elem, crit, e['mode'] == 'stun')
        e['hp'] -= final
        e['hurtT'] = 8
        if kdir and not e['boss']:
            e['kb'] = kdir * (6.0 if crit else 4.5)
        self.game['totalDamage'] += final
        label = ('暴击 ' if crit else '') + ('弱点 ' if tag == 'weak' else '抗性 ' if tag == 'resist' else '') \
            + '-%d' % final
        color = ecol if elem != 'phys' else ('#ffd040' if crit else PHYS_COLOR)
        size = 18 if (crit or tag == 'weak') else (12 if dot else 14)
        self.add_text(e['x'], e['y'] - 4, label, color, size)
        self.add_particles(cx, cy, 5, e['color'] if elem == 'phys' else ecol, 3)
        if not dot:
            if kdir or crit:                # 命中火花 + 停顿；爆炸、电弧（无方向）不触发
                self.add_fx('spark', cx, cy, life=9, dir=kdir or 1,
                            color=ecol if elem != 'phys' else '#fff4c0', big=crit)
                stop = HITSTOP_CRIT if crit else (HITSTOP_HIT + 1 if tag == 'weak' else HITSTOP_HIT)
                self.hitstop(stop)
                if crit:
                    self.game['shake'] = max(self.game['shake'], 7)
            if crit or tag == 'weak':
                self.add_fx('ring', cx, cy, life=14, color=ecol if elem != 'phys' else '#ffd040')
        if e['hp'] <= 0:
            self.kill_enemy(e)
        elif not dot:
            self.apply_status(e, elem, dmg)
        if elem == 'thunder' and chain and not dot:
            self.chain_lightning(e, dmg)

    def apply_status(self, e, elem, base_dmg):
        """火：灼烧持续掉血；冰：减速。抗性元素和首领（对冰）免疫。"""
        if elem == 'fire' and e['resist'] != 'fire':
            if e['burn'] <= 0:
                self.add_text(e['x'], e['y'] - 22, '燃烧', ELEMENTS['fire']['color'], 12)
            e['burn'] = BURN_FRAMES
            e['burnDmg'] = max(2, int(base_dmg * 0.2))
        elif elem == 'ice' and not e['boss'] and e['resist'] != 'ice':
            if e['slow'] <= 0:
                self.add_text(e['x'], e['y'] - 22, '减速', ELEMENTS['ice']['color'], 12)
            e['slow'] = SLOW_FRAMES

    def chain_lightning(self, src, base_dmg):
        """电弧跳向最近的另一个敌人，只跳一次，避免连锁失控。"""
        cx, cy = src['x'] + src['w'] / 2, src['y'] + src['h'] / 2
        best, best_d = None, CHAIN_RANGE
        for o in self.enemies:
            if o is src or not o['alive']:
                continue
            d = math.hypot(o['x'] + o['w'] / 2 - cx, o['y'] + o['h'] / 2 - cy)
            if d < best_d:
                best, best_d = o, d
        if best is None:
            return
        self.add_fx('bolt', cx, cy, x2=round(best['x'] + best['w'] / 2, 1),
                    y2=round(best['y'] + best['h'] / 2, 1), life=10)
        self.damage_enemy(best, max(1, int(base_dmg * CHAIN_RATIO)), 0, elem='thunder',
                          silent_crit=True, chain=False)

    def kill_enemy(self, e):
        e['alive'], e['dying'], e['hp'] = False, 18, 0
        e['burn'] = e['slow'] = 0
        if e['type'] == 'bomber' and not e.get('exploded'):
            self.explode(e)                 # 被击杀会提前引爆
        g, p = self.game, self.player
        g['kills'] += 1
        g['goldEarned'] += e['gold']
        p['gold'] += e['gold']
        self.gain_exp(e['exp'])
        cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2
        self.add_text(e['x'], e['y'] - 12, '+%d金' % e['gold'], '#ffd84a', 12)
        self.add_particles(cx, cy, 20, e['color'], 5)
        r = self.rng.random()
        if r < 0.15:
            self.spawn_drop(cx, cy, 'heart', 15)
        elif r < 0.40:
            self.spawn_drop(cx, cy, 'gold', 3 + int(self.rng.random() * 4))
        if e['boss']:
            self.win_timer = 150
            self.enemyProj = []
            self.add_particles(cx, cy, 80, '#c040ff', 9)

    def spawn_drop(self, x, y, kind, amt):
        self.coins.append({'kind': kind, 'amt': amt, 'x': x, 'y': y, 't': 0,
                           'vx': (self.rng.random() - 0.5) * 2, 'vy': -4})

    def damage_player(self, dmg, from_x=None, elem='phys'):
        p = self.player
        if p['hurtCD'] > 0 or self.trans or self.win_timer:
            return
        armor = ARMORS[p['armor']]
        res = armor.get('res', {}).get(elem, 0)
        real = max(1, int(round(dmg * (1 - armor['reduce'] / 100.0) * (1 - res / 100.0))))
        p['hp'] -= real
        p['hurtCD'] = 50
        if from_x is not None:
            p['kbV'] = 5.0 if p['x'] + p['w'] / 2 > from_x else -5.0
            p['vy'] = min(p['vy'], -3.5)
        self.game['shake'] = max(self.game['shake'], 7)
        self.game['hurtFlash'] = 8
        self.hitstop(HITSTOP_HURT)
        tag = ' 抗性' if res > 0 else (' 易伤' if res < 0 else '')
        self.add_text(p['x'], p['y'] - 6, '-%d%s' % (real, tag),
                      ELEMENTS[elem]['color'] if elem != 'phys' else '#ff4040', 16)
        self.add_particles(p['x'] + p['w'] / 2, p['y'] + p['h'] / 2, 8,
                           ELEMENTS[elem]['color'] if elem != 'phys' else '#ff4040', 3)
        self.add_fx('ring', p['x'] + p['w'] / 2, p['y'] + p['h'] / 2, life=12,
                    color=ELEMENTS[elem]['color'] if elem != 'phys' else '#ff6060')
        if p['hp'] <= 0:
            self.player_die('你被击败了')

    def player_die(self, reason):
        self.player['hp'] = 0
        g = self.game
        g['deadReason'], g['endT'], g['panel'] = reason, 0, None
        g['state'] = 'dead'
        self.trans = None
