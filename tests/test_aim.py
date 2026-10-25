"""鼠标瞄准：弹道方向、速度归一化、输入校验、斜射撞地、近战不受影响。"""
import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine import GameEngine
from game_data import INPUT_KEYS, GROUND_Y, WEAPONS, parse_aim, W, H


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d['aim'] = None
    d.update(k)
    return d


def new_engine(weapon=3):
    e = GameEngine(seed=5)
    e.tick(K(confirm=True))
    e.tick(K())
    e.load('forest')
    e.enemies = []
    p = e.player
    p['x'], p['y'] = 300.0, float(GROUND_Y - p['h'] - 1)
    p['weapon'] = weapon
    p['ownedWeapons'].add(weapon)
    e.game['camX'] = 0.0
    return e


def center(e):
    p = e.player
    return p['x'] + p['w'] / 2, p['y'] + p['h'] / 2 - 4


def fire(e, aim, **extra):
    e.aim = aim
    e.player_attack()
    return e.projectiles[-1]


class AimDirectionTests(unittest.TestCase):
    def test_shoots_toward_mouse_up_right(self):
        e = new_engine()
        cx, cy = center(e)
        pr = fire(e, (cx + 100, cy - 100))
        self.assertGreater(pr['vx'], 0)
        self.assertLess(pr['vy'], 0)
        self.assertAlmostEqual(abs(pr['vx']), abs(pr['vy']), places=5)     # 45°

    def test_shoots_toward_mouse_left(self):
        e = new_engine()
        cx, cy = center(e)
        pr = fire(e, (cx - 200, cy))
        self.assertLess(pr['vx'], 0)
        self.assertAlmostEqual(pr['vy'], 0.0, places=5)

    def test_straight_down(self):
        e = new_engine()
        cx, cy = center(e)
        pr = fire(e, (cx, cy + 200))
        self.assertAlmostEqual(pr['vx'], 0.0, places=5)
        self.assertGreater(pr['vy'], 0)

    def test_speed_is_weapon_speed_regardless_of_distance(self):
        for dist in (10, 80, 500, 900):
            e = new_engine()
            cx, cy = center(e)
            pr = fire(e, (min(W, cx + dist), cy - dist * 0.3))
            self.assertAlmostEqual(math.hypot(pr['vx'], pr['vy']), WEAPONS[3]['projSpeed'], places=5)

    def test_no_aim_uses_facing(self):
        e = new_engine()
        e.player['facing'] = -1
        e.aim = None
        e.player_attack()
        pr = e.projectiles[-1]
        self.assertLess(pr['vx'], 0)
        self.assertEqual(pr['vy'], 0)

    def test_mouse_on_top_of_player_falls_back_to_facing(self):
        e = new_engine()
        e.player['facing'] = 1
        cx, cy = center(e)
        pr = fire(e, (cx + 2, cy + 2))                 # 太近，方向不稳定
        self.assertGreater(pr['vx'], 0)
        self.assertEqual(pr['vy'], 0)

    def test_camera_offset_is_applied(self):
        """鼠标是画面坐标，必须加上镜头位置才是世界坐标。"""
        e = new_engine()
        e.player['x'] = 1500.0
        e.game['camX'] = 1100.0
        cx, cy = center(e)
        # 画面里鼠标在角色正右方：画面x = 世界x - camX + 100
        pr = fire(e, (cx - e.game['camX'] + 100, cy))
        self.assertGreater(pr['vx'], 0)
        self.assertAlmostEqual(pr['vy'], 0.0, places=5)

    def test_fire_staff_also_aims_and_keeps_element(self):
        e = new_engine(weapon=4)
        cx, cy = center(e)
        pr = fire(e, (cx + 60, cy - 60))
        self.assertEqual(pr['elem'], 'fire')
        self.assertLess(pr['vy'], 0)

    def test_aim_angle_exposed_for_rendering(self):
        e = new_engine()
        cx, cy = center(e)
        e.aim = (cx + 100, cy)
        self.assertAlmostEqual(e.aim_angle(), 0.0, places=2)
        e.aim = (cx, cy + 100)
        self.assertAlmostEqual(e.aim_angle(), round(math.pi / 2, 2), places=2)
        e.aim = None
        self.assertIsNone(e.aim_angle())


class MeleeUnaffectedTests(unittest.TestCase):
    def test_melee_ignores_aim_and_uses_facing(self):
        e = new_engine(weapon=1)
        e.player['facing'] = 1
        cx, cy = center(e)
        en = e.make_enemy('goblin', int(cx) + 30, GROUND_Y - 29)
        en['hp'] = en['maxHp'] = 500
        e.enemies.append(en)
        e.aim = (cx - 300, cy)                          # 鼠标在左边，但近战仍按朝向打右边
        e.player_attack()
        self.assertLess(en['hp'], 500)
        self.assertEqual(e.projectiles, [])


class FacingTests(unittest.TestCase):
    def test_attacking_with_mouse_turns_player_toward_mouse(self):
        e = new_engine()
        e.player['facing'] = 1
        cx, cy = center(e)
        e.tick(K(attack=True, aim=[int(cx - 150), int(cy)]))
        self.assertEqual(e.player['facing'], -1)

    def test_keyboard_facing_unchanged_without_mouse(self):
        e = new_engine()
        e.tick(K(left=True))
        self.assertEqual(e.player['facing'], -1)

    def test_mostly_vertical_aim_keeps_facing(self):
        e = new_engine()
        e.player['facing'] = 1
        cx, cy = center(e)
        e.tick(K(attack=True, aim=[int(cx - 5), int(cy - 200)]))     # 几乎正上方
        self.assertEqual(e.player['facing'], 1)


class ProjectileCollisionTests(unittest.TestCase):
    def test_arrow_stops_in_ground(self):
        e = new_engine()
        cx, cy = center(e)
        fire(e, (cx + 60, cy + 120))                    # 斜向下射
        for _ in range(60):
            e.tick(K())
        self.assertEqual(e.projectiles, [], '斜射向地面的箭应在地面消失')

    def test_arrow_passes_through_one_way_platform(self):
        from physics import in_solid
        e = new_engine()
        e.platforms.append({'x': 500, 'y': 400, 'w': 100, 'h': 16, 'type': 'plat'})
        self.assertFalse(in_solid(e.platforms, 550, 408))

    def test_diagonal_arrow_can_hit_enemy_above(self):
        e = new_engine()
        cx, cy = center(e)
        en = e.make_enemy('bat', int(cx) + 120, int(cy) - 120)
        en['hp'] = en['maxHp'] = 500
        e.enemies.append(en)
        e.ai_bat = lambda *a: None                      # 蝙蝠会向玩家下沉，这里让它悬停，只测命中
        en['vx'] = en['vy'] = 0.0
        fire(e, (cx + 120 + 11, cy - 120 + 8))          # 瞄准蝙蝠中心
        for _ in range(40):
            e.tick(K())
            if en['hp'] < 500:
                break
        self.assertLess(en['hp'], 500)


class ParseAimTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_aim([10, 20]), (10.0, 20.0))
        self.assertEqual(parse_aim((10.5, 20.5)), (10.5, 20.5))

    def test_clamped_to_screen(self):
        self.assertEqual(parse_aim([-500, 99999]), (0.0, float(H)))
        self.assertEqual(parse_aim([99999, -1]), (float(W), 0.0))

    def test_rejects_wrong_shapes_and_types(self):
        for bad in (None, 5, 'ab', {}, [], [1], [1, 2, 3], ['1', '2'], [None, 1], [True, False], [[1], [2]], {'x': 1}):
            self.assertIsNone(parse_aim(bad), repr(bad))

    def test_rejects_nan_and_infinity(self):
        for bad in ([float('nan'), 1], [1, float('inf')], [float('-inf'), 0]):
            self.assertIsNone(parse_aim(bad), repr(bad))

    def test_json_nan_and_infinity_literals(self):
        """Python 的 json 默认会解析 NaN / Infinity，必须在校验里拦住。"""
        for text in ('{"aim": [NaN, 1]}', '{"aim": [Infinity, 1]}', '{"aim": [-Infinity, 1]}'):
            self.assertIsNone(parse_aim(json.loads(text)['aim']), text)

    def test_huge_integer_does_not_crash(self):
        """10**400 转 float 会抛 OverflowError。"""
        self.assertIsNone(parse_aim([10 ** 400, 1]))
        self.assertIsNone(parse_aim(json.loads('{"aim": [1' + '0' * 400 + ', 1]}')['aim']))

    def test_engine_survives_garbage_aim(self):
        e = new_engine()
        for bad in ([float('nan'), 1], 'x', [1], {'a': 1}, [10 ** 400, 0], None, True):
            e.tick(K(attack=True, aim=bad))
        json.dumps(e.get_state())

    def test_state_serialises_with_aim(self):
        e = new_engine()
        cx, cy = center(e)
        e.tick(K(attack=True, aim=[int(cx + 50), int(cy)]))
        s = json.dumps(e.get_state())
        self.assertIn('"aim"', s)


class ServerSessionTests(unittest.TestCase):
    def make(self):
        import server
        s = server.Session(object(), '127.0.0.1')
        s.stamp = 0.0           # 测试用假时钟从 0 开始,和 handle(now=...) 对齐
        return s

    def test_sessions_are_independent(self):
        a, b = self.make(), self.make()
        a.handle(json.dumps({'attack': True, 'aim': [10, 20]}), now=0.0)
        self.assertTrue(a.keys['attack'])
        self.assertEqual(a.keys['aim'], (10.0, 20.0))
        self.assertFalse(b.keys['attack'])
        self.assertIsNone(b.keys['aim'])
        self.assertIsNot(a.engine, b.engine)

    def test_aim_null_clears_and_garbage_is_ignored(self):
        s = self.make()
        s.handle(json.dumps({'aim': [10, 20]}), now=0.0)
        s.handle(json.dumps({'aim': None}), now=0.0)
        self.assertIsNone(s.keys['aim'])
        for bad in ('not json', '[1,2]', '"x"', '{"aim": [NaN, 1]}', '[' * 5000):
            s.handle(bad, now=0.0)
        self.assertIsNone(s.keys['aim'])

    def test_need_level_sets_flag(self):
        s = self.make()
        s.handle(json.dumps({'need_level': True}), now=0.0)
        self.assertTrue(s.want_level)

    def test_rate_limit_drops_flood_then_recovers(self):
        import server
        s = self.make()
        for _ in range(int(server.MSG_BURST) + 50):
            s.handle(json.dumps({'left': True}), now=0.0)
        s.handle(json.dumps({'left': False}), now=0.0)
        self.assertTrue(s.keys['left'])             # 令牌耗尽后，这条被丢弃
        s.handle(json.dumps({'left': False}), now=1.0)
        self.assertFalse(s.keys['left'])            # 过了一秒令牌补充，恢复处理


if __name__ == '__main__':
    unittest.main()
