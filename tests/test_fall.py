"""摔伤：按"离地后最高点 → 落地点"的落差计算。"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine import GameEngine
from game_data import INPUT_KEYS, GROUND_Y, SAFE_FALL, FALL_PCT_PER_PX, FALL_MAX_PCT, JUMP_V, GRAVITY, MAX_FALL
from levels import LEVEL_DATA


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d['aim'] = None
    d.update(k)
    return d


def new_engine(level='forest', clean=True):
    """clean=True 时清掉所有平台，只留一块宽地面：关卡里的平台会半路接住下落的玩家，干扰测量。"""
    e = GameEngine(seed=9)
    e.tick(K(confirm=True))
    e.tick(K())
    e.load(level)
    e.game['state'] = level
    e.enemies = []
    e.hazards = []
    e.crates = []
    e.movers = []
    if clean:
        e.platforms = [{'x': 0, 'y': GROUND_Y, 'w': 2000, 'h': 60, 'type': 'ground'}]
    return e


def run(e, n, **keys):
    for _ in range(n):
        e.tick(K(**keys))


def drop_from(e, height, x=400.0):
    """把玩家放在地面上方 height 像素处，让他自由落体直到落地。返回 (损失的生命, 落地后的 y)。"""
    p = e.player
    p['hp'] = p['maxHp'] = 100
    p['x'], p['y'], p['vy'], p['vx'], p['kbV'] = x, float(GROUND_Y - p['h'] - height), 0.0, 0.0, 0.0
    p['onGround'] = False
    p['airTop'] = p['y']
    hp0 = p['hp']
    for _ in range(400):
        e.tick(K())
        if p['onGround']:
            break
    run(e, 2)
    return hp0 - p['hp']


class FallDamageTests(unittest.TestCase):
    def test_short_drop_is_safe(self):
        self.assertEqual(drop_from(new_engine(), 80), 0)

    def test_drop_at_threshold_is_safe(self):
        self.assertEqual(drop_from(new_engine(), SAFE_FALL - 5), 0)

    def test_high_drop_hurts(self):
        self.assertGreater(drop_from(new_engine(), 260), 0)

    def test_damage_grows_with_height(self):
        a, b, c = (drop_from(new_engine(), h) for h in (180, 260, 340))
        self.assertLess(a, b)
        self.assertLess(b, c)

    def test_damage_matches_formula(self):
        e = new_engine()
        lost = drop_from(e, 300)
        # 落地时的落差略大于出生高度（重力积分以整帧为步长），公式只验证数量级和上界
        expected = int(100 * min(FALL_MAX_PCT, (300 - SAFE_FALL) * FALL_PCT_PER_PX))
        self.assertAlmostEqual(lost, expected, delta=6)

    def test_damage_is_capped(self):
        lost = drop_from(new_engine(), 2000)
        self.assertLessEqual(lost, int(100 * FALL_MAX_PCT))

    def test_fall_never_kills(self):
        e = new_engine()
        p = e.player
        p['maxHp'], p['hp'] = 100, 3
        p['x'], p['y'], p['vy'] = 400.0, float(GROUND_Y - 30 - 400), 0.0
        p['airTop'] = p['y']
        for _ in range(400):
            e.tick(K())
            if p['onGround']:
                break
        run(e, 2)
        self.assertEqual(p['hp'], 1)
        self.assertNotEqual(e.game['state'], 'dead')

    def test_armor_percent_reduction_does_not_apply(self):
        a, b = new_engine(), new_engine()
        b.player['armor'] = 4                          # 皇家盔甲，减伤 40%
        la = drop_from(a, 300)
        b.player['armor'] = 4
        lb = drop_from(b, 300)
        self.assertEqual(la, lb)


class NormalMovementIsUnaffectedTests(unittest.TestCase):
    def test_jump_and_land_in_place_does_not_hurt(self):
        e = new_engine()
        p = e.player
        p['hp'] = p['maxHp'] = 100
        p['x'], p['y'] = 300.0, float(GROUND_Y - p['h'] - 1)
        run(e, 5)
        for _ in range(15):
            run(e, 1, jump=True)
        run(e, 80)
        self.assertEqual(p['hp'], 100)

    def test_walking_off_a_plain_ledge_is_safe(self):
        e = new_engine()
        e.platforms.append({'x': 300, 'y': 400, 'w': 100, 'h': 16, 'type': 'plat'})
        p = e.player
        p['hp'] = p['maxHp'] = 100
        p['x'], p['y'] = 380.0, float(400 - p['h'] - 0.5)
        run(e, 80, right=True)
        self.assertEqual(p['hp'], 100)

    def test_jumping_up_a_platform_then_down_is_safe(self):
        """跳上 80 高的平台再跳下来：上升高度不应被误算成下落高度。"""
        e = new_engine()
        e.platforms.append({'x': 300, 'y': 400, 'w': 120, 'h': 16, 'type': 'plat'})
        p = e.player
        p['hp'] = p['maxHp'] = 100
        p['x'], p['y'] = 340.0, float(GROUND_Y - p['h'] - 1)
        run(e, 3)
        run(e, 14, jump=True)
        run(e, 60)
        run(e, 60, left=True)
        self.assertEqual(p['hp'], 100)

    def test_walking_on_flat_ground_never_hurts(self):
        e = new_engine('forest', clean=False)
        p = e.player
        p['hp'] = p['maxHp'] = 9999
        p['x'] = 60.0
        run(e, 90, right=True)                 # 只走起点这一段平地，不会遇到深坑
        self.assertEqual(p['hp'], 9999)

    def walk_off_real_platform(self, x, y):
        """在森林真实地形里，站到平台 (x, y) 上向右走下来，返回损失的生命。"""
        e = new_engine('forest', clean=False)
        p = e.player
        p['hp'] = p['maxHp'] = 9999
        p['x'], p['y'], p['vy'] = x + 20.0, float(y - p['h'] - 0.5), 0.0
        p['onGround'] = True
        p['airTop'] = p['y']
        run(e, 60, right=True)
        run(e, 80)
        return 9999 - p['hp']

    def test_real_level_low_platform_walk_off_is_safe(self):
        """森林里 (200, 400) 的平台比地面高 80，没超过安全落差，走下来不应摔伤。"""
        self.assertLessEqual(GROUND_Y - 400, SAFE_FALL)
        self.assertEqual(self.walk_off_real_platform(200, 400), 0)

    def test_real_level_high_platform_walk_off_hurts_but_is_bounded(self):
        """森林里 (380, 330) 的平台比地面高 150，超过安全落差：按公式摔伤，但不致死、不超过上限。

        之前这条测试假设"所有平台都不到安全高度"，与关卡数据不符：多数关卡都有 140~220 高的平台。
        """
        drop = GROUND_Y - 330
        self.assertGreater(drop, SAFE_FALL)
        lost = self.walk_off_real_platform(380, 330)
        expected = (drop - SAFE_FALL) * FALL_PCT_PER_PX * 9999
        self.assertGreater(lost, 0)
        self.assertAlmostEqual(lost, expected, delta=expected * 0.1 + 2)    # 落差有 1~2 像素的取整误差
        self.assertLessEqual(lost, int(9999 * FALL_MAX_PCT))


class ResetTests(unittest.TestCase):
    def test_level_load_clears_fall_height(self):
        e = new_engine()
        p = e.player
        p['y'], p['airTop'] = 100.0, -500.0
        e.load('crypt')
        self.assertEqual(p['airTop'], p['y'])
        self.assertEqual(e.fall_distance(), 0)

    def test_pit_respawn_does_not_double_penalise(self):
        e = new_engine('forest', clean=False)             # 需要真实的深坑
        p = e.player
        p['hp'] = p['maxHp'] = 100
        p['x'], p['y'] = 650.0, 400.0                     # 森林 600~680 是深坑
        p['airTop'] = -300.0                              # 假设之前爬得很高
        for _ in range(200):
            e.tick(K())
            if p['hp'] < 100 and p['onGround']:
                break
        run(e, 5)
        lost = 100 - p['hp']
        self.assertLessEqual(lost, int(100 * 0.15) + 1, '掉坑只应扣掉坑的伤害，不能再叠加摔伤')

    def test_knockback_upwards_counts_as_height(self):
        """被尖刺弹起时是离地后的新最高点；落回原地不应摔伤。"""
        e = new_engine()
        p = e.player
        p['hp'] = p['maxHp'] = 100
        p['x'], p['y'] = 300.0, float(GROUND_Y - p['h'] - 1)
        run(e, 3)
        p['vy'] = -6.5
        run(e, 80)
        self.assertEqual(p['hp'], 100)


class StateTests(unittest.TestCase):
    def test_fall_danger_flag_in_state(self):
        e = new_engine()
        p = e.player
        p['x'], p['y'], p['vy'] = 400.0, float(GROUND_Y - 30 - 400), 0.0
        p['airTop'] = p['y']
        flags = []
        for _ in range(60):
            e.tick(K())
            flags.append(e.get_state()['player']['fallDanger'])
        self.assertIn(True, flags)
        self.assertFalse(flags[0])

    def test_state_serialises(self):
        e = new_engine()
        json.dumps(e.get_state())


class LevelDesignTests(unittest.TestCase):
    def test_standing_on_any_platform_and_walking_off_is_never_fatal(self):
        """没有任何一块平台高到走下来会摔死（摔伤有上限，且不致死，这里只检查落差不会超过上限公式的意图）。"""
        for name, d in LEVEL_DATA.items():
            for x, y, w in d['plats']:
                self.assertLessEqual(GROUND_Y - y, 300, '%s: 平台 %s 太高' % (name, (x, y)))


if __name__ == '__main__':
    unittest.main()
