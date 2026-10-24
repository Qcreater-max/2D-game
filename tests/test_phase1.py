"""第 1 期：新怪物 AI、命中停顿、格挡/破盾、爆炸连锁。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine import GameEngine
from game_data import INPUT_KEYS, GROUND_Y


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d.update(k)
    return d


def new_engine(level='forest'):
    e = GameEngine(seed=7)
    e.tick(K(confirm=True))
    e.tick(K())
    e.load(level)
    e.enemies = []
    e.player['x'], e.player['y'] = 400.0, float(GROUND_Y - e.player['h'] - 1)
    return e


def spawn(e, etype, x):
    on_ground = any(p['type'] == 'ground' and p['x'] <= x <= p['x'] + p['w'] for p in e.platforms)
    assert on_ground, '测试摆位错误：x=%s 不在地面上（是深坑）' % x
    en = e.make_enemy(etype, x, GROUND_Y - e.make_enemy(etype, 0, 0)['h'] - 1)
    en['atkCD'] = 0
    e.enemies.append(en)
    return en


def run(e, n, **keys):
    for _ in range(n):
        e.tick(K(**keys))


class ArcherTests(unittest.TestCase):
    def test_keeps_distance_and_shoots_arc(self):
        e = new_engine()
        a = spawn(e, 'archer', 520)
        run(e, 200)
        self.assertGreater(abs(a['x'] - e.player['x']), 150, '弓手应与玩家保持距离')
        shots = [p for p in e.enemyProj if p['kind'] == 'arrow']
        self.assertTrue(shots or e.player['hp'] < 100 or a['atkCD'] > 0, '弓手应已射出过箭')

    def test_arrow_follows_parabola(self):
        e = new_engine()
        e.player['x'] = 300.0
        spawn(e, 'archer', 540)            # 森林 600~680 是深坑，别放在坑里
        for _ in range(60):
            e.tick(K())
            if any(p['kind'] == 'arrow' for p in e.enemyProj):
                break
        arrow = next(p for p in e.enemyProj if p['kind'] == 'arrow')
        vy0 = arrow['vy']
        run(e, 5)
        self.assertGreater(arrow['vy'], vy0, '箭受重力，竖直速度应增大')


class BomberTests(unittest.TestCase):
    def test_fuse_then_explode_hurts_player(self):
        e = new_engine()
        b = spawn(e, 'bomber', 440)
        hp = e.player['hp']
        run(e, 120)
        self.assertFalse(b['alive'], '自爆虫应已爆炸')
        self.assertLess(e.player['hp'], hp, '玩家在范围内应受伤')

    def test_killed_bomber_chains_to_neighbours(self):
        e = new_engine()
        e.player['x'] = 100.0
        b = spawn(e, 'bomber', 700)
        near = spawn(e, 'slime', 730)
        far = spawn(e, 'slime', 1100)
        far_hp, near_hp = far['hp'], near['hp']
        e.damage_enemy(b, 999, 1)
        self.assertLess(near['hp'], near_hp, '爆炸范围内的敌人应受伤')
        self.assertEqual(far['hp'], far_hp, '范围外的敌人不受影响')

    def test_explodes_only_once(self):
        e = new_engine()
        b = spawn(e, 'bomber', 440)
        e.damage_enemy(b, 999, 1)
        hp = e.player['hp']
        e.explode(b)
        self.assertEqual(e.player['hp'], hp)


class BoarTests(unittest.TestCase):
    def test_windup_charge_then_stun(self):
        e = new_engine()
        b = spawn(e, 'boar', 800)
        modes = set()
        for _ in range(400):
            e.tick(K())
            modes.add(b['mode'])
        self.assertTrue({'windup', 'charge'} <= modes, '野猪应蓄力并冲锋: %s' % modes)

    def test_stun_takes_bonus_damage(self):
        e = new_engine()
        b = spawn(e, 'boar', 800)
        b['mode'] = 'stun'
        hp = b['hp']
        e.damage_enemy(b, 10, 1, silent_crit=True)
        # 10 * 1.5（眩晕加成）= 15，再减去野猪 3 点防御
        self.assertEqual(hp - b['hp'], 15 - b['def'])


class ShieldTests(unittest.TestCase):
    def test_front_attack_is_blocked(self):
        e = new_engine()
        s = spawn(e, 'shield', 440)
        s['dir'] = -1                      # 面向左，玩家在左侧
        hp = s['hp']
        e.damage_enemy(s, 20, 1)           # 玩家从左向右攻击 -> 正面
        self.assertEqual(s['hp'], hp)

    def test_back_attack_hits(self):
        e = new_engine()
        s = spawn(e, 'shield', 440)
        s['dir'] = 1                       # 面向右，玩家从左侧攻击 -> 背面
        hp = s['hp']
        e.damage_enemy(s, 20, 1, silent_crit=True)
        self.assertLess(s['hp'], hp)

    def test_heavy_weapon_breaks_shield(self):
        e = new_engine()
        s = spawn(e, 'shield', 440)
        s['dir'] = -1
        e.damage_enemy(s, 20, 1, heavy=True)
        self.assertEqual(s['mode'], 'stun')

    def test_stunned_shield_can_be_hit(self):
        e = new_engine()
        s = spawn(e, 'shield', 440)
        s['dir'] = -1
        s['mode'] = 'stun'
        hp = s['hp']
        e.damage_enemy(s, 20, 1, silent_crit=True)
        self.assertLess(s['hp'], hp)

    def test_explosion_ignores_shield(self):
        e = new_engine()
        s = spawn(e, 'shield', 440)
        hp = s['hp']
        e.damage_enemy(s, 20, 0, silent_crit=True)
        self.assertLess(s['hp'], hp)


class FeelTests(unittest.TestCase):
    def test_hit_triggers_hitstop_and_fx(self):
        e = new_engine()
        en = spawn(e, 'goblin', 440)
        e.damage_enemy(en, 5, 1, silent_crit=True)
        self.assertGreater(e.game['hitstop'], 0)
        self.assertTrue(any(f['kind'] == 'spark' for f in e.fx))

    def test_hitstop_freezes_world_then_resumes(self):
        e = new_engine()
        en = spawn(e, 'goblin', 800)
        e.game['hitstop'] = 4
        x0 = en['x']
        run(e, 3)
        self.assertEqual(en['x'], x0, '停顿期间敌人不应移动')
        run(e, 6)
        self.assertNotEqual(en['x'], x0, '停顿结束后恢复')

    def test_jump_pressed_during_hitstop_is_not_lost(self):
        e = new_engine()
        run(e, 5)
        e.game['hitstop'] = 3
        e.tick(K(jump=True))               # 在停顿中按下跳跃
        run(e, 8, jump=True)
        self.assertLess(e.player['y'], GROUND_Y - e.player['h'] - 1 - 1, '玩家应已起跳')

    def test_hitstop_cannot_stack_forever(self):
        e = new_engine()
        for _ in range(50):
            e.hitstop(3)
        self.assertLessEqual(e.game['hitstop'], 5)

    def test_fx_list_is_bounded(self):
        e = new_engine()
        for _ in range(500):
            e.add_fx('spark', 0, 0)
        self.assertLessEqual(len(e.fx), 40)

    def test_player_hurt_sets_flash(self):
        e = new_engine()
        e.damage_player(10, 0)
        self.assertGreater(e.game['hurtFlash'], 0)
        self.assertGreater(e.game['hitstop'], 0)


class LevelContentTests(unittest.TestCase):
    def test_levels_contain_new_enemy_types(self):
        from levels import LEVEL_DATA
        seen = {s[0] for lv in LEVEL_DATA.values() for s in lv['enemies']}
        self.assertTrue({'archer', 'bomber', 'boar', 'shield'} <= seen)

    def test_all_levels_load_and_serialise(self):
        import json
        e = new_engine()
        for name in ('forest', 'crypt', 'boss'):
            e.load(name)
            e.game['state'] = name
            run(e, 120)
            json.dumps(e.get_state())


if __name__ == '__main__':
    unittest.main()
