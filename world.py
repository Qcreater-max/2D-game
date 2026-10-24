"""世界机制：危险物、移动平台、木箱、地洞与子关卡、隐藏房间、模式（冒险 / 无尽）。"""
import math

from game_data import (
    GROUND_Y, H, W, HAZARD_DEFS, HAZARD_KNOCK, CRATE_DROPS, ENDLESS_WAVE_BREAK, ELEMENTS,
)
from levels import is_sub
from physics import rects_overlap


class WorldMixin:
    # ---------- 移动平台 ----------
    def update_movers(self):
        """移动平台沿 x 做正弦摆动。记录每帧位移 dx，玩家站在上面时被带着走。"""
        t = self.game['playTime']
        p = self.player
        for m in self.movers:
            pl = m['plat']
            nx = m['x0'] + math.sin(t * 2 * math.pi / m['period']) * m['amp']
            dx = nx - pl['x']
            pl['x'] = nx
            pl['dx'] = dx
            # 玩家脚踩在这块平台上（上一帧落地且水平范围重叠）
            if p['standingOn'] is pl:
                p['x'] += dx
        # 站台状态每帧在 update_player 里重新判定

    # ---------- 危险物 ----------
    def update_hazards(self):
        p = self.player
        body = {'x': p['x'] + 3, 'y': p['y'] + p['h'] - 10, 'w': p['w'] - 6, 'h': 10}   # 只看脚部
        in_poison = False
        for h in self.hazards:
            box = {'x': h['x'], 'y': h['y'], 'w': h['w'], 'h': h['h']}
            if not rects_overlap(body, box):
                continue
            d = HAZARD_DEFS[h['kind']]
            if h['kind'] == 'poison':
                in_poison = True
                if self.game['playTime'] % d['tick'] == 0:
                    self.hurt_by_hazard(d, knock=False)
            elif p['hurtCD'] <= 0:
                self.hurt_by_hazard(d, knock=True)
        p['inPoison'] = in_poison

    def hurt_by_hazard(self, d, knock):
        p = self.player
        dmg = max(1, int(p['maxHp'] * d['pct']))
        # 危险物不受盔甲的百分比减伤影响，但元素抗性仍然生效（熔岩甲能泡岩浆的好处）
        from game_data import ARMORS
        res = ARMORS[p['armor']].get('res', {}).get(d['elem'], 0)
        real = max(1, int(round(dmg * (1 - res / 100.0))))
        p['hp'] -= real
        p['hurtCD'] = 40 if knock else p['hurtCD']
        col = ELEMENTS[d['elem']]['color'] if d['elem'] != 'phys' else '#c0ff80'
        self.add_text(p['x'], p['y'] - 6, '-%d %s' % (real, d['name']), col, 14)
        self.add_particles(p['x'] + p['w'] / 2, p['y'] + p['h'], 6, col, 3)
        if knock:
            p['vy'] = -HAZARD_KNOCK
            self.game['shake'] = max(self.game['shake'], 6)
            self.game['hurtFlash'] = 6
            self.hitstop(3)
        if p['hp'] <= 0:
            self.player_die('倒在了%s里' % d['name'])

    # ---------- 木箱 ----------
    def hit_crates(self, box):
        """玩家的近战范围 / 弹体打到木箱。返回是否命中。"""
        hit = False
        for c in self.crates:
            if c['hp'] > 0 and rects_overlap(box, c):
                c['hp'] -= 1
                hit = True
                cx, cy = c['x'] + c['w'] / 2, c['y'] + c['h'] / 2
                self.add_particles(cx, cy, 6, '#a07030', 3)
                if c['hp'] <= 0:
                    self.break_crate(c, cx, cy)
        return hit

    def break_crate(self, c, cx, cy):
        self.add_particles(cx, cy, 16, '#8a5a28', 4)
        r = self.rng.random()
        if r < CRATE_DROPS[0]:
            self.spawn_drop(cx, cy, 'gold', 4 + int(self.rng.random() * 6))
        elif r < CRATE_DROPS[0] + CRATE_DROPS[1]:
            self.spawn_drop(cx, cy, 'heart', 12)
        self.game['crates'] = self.game.get('crates', 0) + 1

    # ---------- 隐藏房间 ----------
    def hit_secrets(self, box, dmg_hint=1):
        """攻击"可疑裂墙"：命中几次后破开，墙消失，露出通往隐藏房间的入口。"""
        for s in self.secrets:
            if s['open']:
                continue
            wall = {'x': s['x'] - 16, 'y': GROUND_Y - 90, 'w': 32, 'h': 90}
            if rects_overlap(box, wall):
                s['hp'] -= 1
                self.add_particles(s['x'], GROUND_Y - 45, 8, '#a89888', 3)
                self.add_fx('ring', s['x'], GROUND_Y - 45, life=10, color='#cdbba8')
                self.game['shake'] = max(self.game['shake'], 3)
                if s['hp'] <= 0:
                    s['open'] = True
                    self.add_particles(s['x'], GROUND_Y - 45, 30, '#a89888', 6)
                    self.add_text(s['x'] - 30, GROUND_Y - 100, '墙裂开了！', '#ffe040', 18)
                    self.show_msg('墙后面有一个隐藏的入口', 100)
                    self.game['secretsFound'] = self.game.get('secretsFound', 0) + 1
                return True
        return False

    # ---------- 地洞 / 隐藏房间入口 / 返回 ----------
    def near_hole(self):
        pcx = self.player['x'] + self.player['w'] / 2
        for h in self.holes:
            if abs(pcx - h['x']) < 36:
                return h
        return None

    def near_secret_door(self):
        pcx = self.player['x'] + self.player['w'] / 2
        for s in self.secrets:
            if s['open'] and abs(pcx - s['x']) < 36:
                return s
        return None

    def near_back(self):
        if self.backX is None:
            return False
        return abs(self.player['x'] + self.player['w'] / 2 - self.backX) < 50

    def enter_sub(self, name, kind):
        """进入子关卡 / 隐藏房间前，把当前关卡的位置压栈；返回时回到原地。"""
        p = self.player
        cur = self.game['state']
        self.return_stack.append({'level': cur, 'x': p['x'], 'chests': self.chests, 'enemies': self.enemies,
                                  'crates': self.crates, 'secrets': self.secrets, 'coins': self.coins,
                                  'hazards': self.hazards, 'holes': self.holes})
        self.start_transition(to=name, kind=kind)

    def leave_sub(self):
        self.start_transition(to=self.return_stack[-1]['level'], kind='back')

    # ---------- 无尽模式 ----------
    def endless_enemy_pool(self, wave):
        pool = ['slime', 'goblin']
        if wave >= 2:
            pool += ['archer', 'bomber']
        if wave >= 4:
            pool += ['boar', 'skeleton']
        if wave >= 6:
            pool += ['shield', 'bat']
        return pool

    def spawn_wave(self):
        g = self.game
        wave = g['wave']
        n = min(14, 3 + wave * 2)
        pool = self.endless_enemy_pool(wave)
        mul_hp = 1 + 0.12 * (wave - 1)
        spawns = []
        for i in range(n):
            t = self.rng.choice(pool)
            x = self.rng.choice([60, 140, 760, 840]) + self.rng.randint(-20, 20)
            from game_data import ENEMY_DEFS
            d = ENEMY_DEFS[t]
            y = 120 if d.get('fly') else GROUND_Y - d['h'] - 1
            en = self.make_enemy(t, x, y)
            en['hp'] = en['maxHp'] = int(en['maxHp'] * mul_hp)
            en['gold'] = int(en['gold'] * (1 + 0.05 * wave))
            self.enemies.append(en)
            spawns.append(t)
        self.enemies_total = len([e for e in self.enemies if e['alive']])
        g['waveBreak'] = 0
        self.show_msg('第 %d 波  敌人 %d 只' % (wave, n), 120)

    def update_endless(self):
        g = self.game
        if self.remaining_enemies() > 0:
            return
        g['waveBreak'] += 1
        if g['waveBreak'] == 1:
            g['bestWave'] = max(g.get('bestWave', 0), g['wave'])
            p = self.player
            bonus = 20 + g['wave'] * 8
            p['gold'] += bonus
            g['goldEarned'] += bonus
            p['hp'] = min(p['maxHp'], p['hp'] + int(p['maxHp'] * 0.25))
            self.add_text(p['x'] - 20, p['y'] - 20, '第%d波完成 +%d' % (g['wave'], bonus), '#ffe040', 16)
        if g['waveBreak'] >= ENDLESS_WAVE_BREAK:
            g['wave'] += 1
            self.spawn_wave()
