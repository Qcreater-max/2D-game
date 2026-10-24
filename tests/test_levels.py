"""第 2 期：关卡可达性、危险物、移动平台、木箱、地洞、隐藏房间、返回栈、无尽模式。"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine import GameEngine
from game_data import (INPUT_KEYS, GROUND_Y, LEVEL_ORDER, LEVEL_NAMES, LEVEL_CLEAR_EXP, HAZARD_DEFS,
                       ENEMY_DEFS, WEAPONS, ARMORS, MODES, JUMP_V, GRAVITY, MOVE_SPEED)
from levels import LEVEL_DATA, load_level, build_data, is_sub


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d['aim'] = None
    d.update(k)
    return d


def started(mode='adventure'):
    e = GameEngine(seed=21)
    e.game['menuIdx'] = MODES.index(mode)
    e.tick(K(confirm=True))
    e.tick(K())
    return e


def goto(e, name, x=60.0):
    e.load(name, spawn_x=x)
    e.game['state'] = name
    e.enemies = []
    e.seen, e.card, e.card_q = set(), None, []
    e.player['hp'] = e.player['maxHp'] = 9999
    return e


def run(e, n, **keys):
    for _ in range(n):
        e.tick(K(**keys))


# ---------------------------------------------------------------- 静态数据
class LevelDataTests(unittest.TestCase):
    def test_level_order_is_consistent(self):
        self.assertEqual(len(LEVEL_ORDER), len(LEVEL_NAMES))
        for name in LEVEL_ORDER:
            self.assertIn(name, LEVEL_DATA)
        for name in LEVEL_ORDER[:-1]:
            self.assertIn(name, LEVEL_CLEAR_EXP)
            self.assertIsNotNone(LEVEL_DATA[name]['portalX'], '%s 缺少传送门' % name)
        self.assertIsNone(LEVEL_DATA[LEVEL_ORDER[-1]]['portalX'])

    def test_every_level_loads(self):
        names = list(LEVEL_DATA) + ['secret_forest_0', 'secret_swamp_0', 'secret_crypt_0']
        for n in names:
            d = load_level(n)
            self.assertGreater(d['mapW'], 0, n)
            json.dumps(d['platforms'])

    def test_enemy_types_and_chest_ids_are_valid(self):
        for name, d in LEVEL_DATA.items():
            for spec in d['enemies']:
                self.assertIn(spec[0], ENEMY_DEFS, '%s: %s' % (name, spec))
            for x, sy, (kind, val) in d['chests']:
                self.assertIn(kind, ('gold', 'weapon', 'armor'))
                if kind == 'weapon':
                    self.assertLess(val, len(WEAPONS), name)
                if kind == 'armor':
                    self.assertLess(val, len(ARMORS), name)
            for x, hp, (kind, val) in d.get('secrets', []):
                if kind == 'weapon':
                    self.assertLess(val, len(WEAPONS), name)
                if kind == 'armor':
                    self.assertLess(val, len(ARMORS), name)

    def test_holes_point_to_existing_sublevels(self):
        for name, d in LEVEL_DATA.items():
            for x, to in d.get('holes', []):
                self.assertIn(to, LEVEL_DATA, '%s 的地洞指向不存在的 %s' % (name, to))
                self.assertTrue(is_sub(to))
                self.assertIsNotNone(LEVEL_DATA[to].get('back'), '%s 缺少返回出口' % to)

    def test_sublevels_have_no_portal_or_smith(self):
        for name, d in LEVEL_DATA.items():
            if is_sub(name):
                self.assertIsNone(d['portalX'])

    def test_everything_inside_map_bounds(self):
        for name in list(LEVEL_DATA):
            d = LEVEL_DATA[name]
            W_ = d['mapW']
            for a, b in d['ground']:
                self.assertTrue(0 <= a < b <= W_, '%s ground %s' % (name, (a, b)))
            for key in ('chests', 'crates'):
                for item in d.get(key, []):
                    self.assertTrue(0 <= item[0] <= W_, '%s %s %s' % (name, key, item))
            for spec in d['enemies']:
                self.assertTrue(0 <= spec[1] <= W_, '%s enemy %s' % (name, spec))
            for k in ('smithX', 'portalX'):
                if d.get(k) is not None:
                    self.assertTrue(0 <= d[k] <= W_, '%s %s' % (name, k))

    def test_ground_spawns_are_on_solid_ground(self):
        """陆地怪物不能刷在深坑上，会直接掉下去。"""
        for name, d in LEVEL_DATA.items():
            for spec in d['enemies']:
                t, x = spec[0], spec[1]
                if ENEMY_DEFS[t].get('fly') or len(spec) > 2:
                    continue
                self.assertTrue(any(a <= x <= b for a, b in d['ground']), '%s: %s 刷在深坑上' % (name, spec))

    def test_chests_and_crates_sit_on_a_surface(self):
        for name, d in LEVEL_DATA.items():
            surfaces = [(a, b, GROUND_Y) for a, b in d['ground']] + [(x, x + w, y) for x, y, w in d['plats']]
            surfaces += [(x - amp, x + w + amp, y) for x, y, w, amp, _ in d.get('movers', [])]
            for key in ('chests', 'crates'):
                for item in d.get(key, []):
                    x, sy = item[0], item[1]
                    ok = any(a - 1 <= x <= b + 1 and sy == y for a, b, y in surfaces)
                    self.assertTrue(ok, '%s: %s %s 悬在空中' % (name, key, item))

    def test_hazards_only_on_ground(self):
        for name, d in LEVEL_DATA.items():
            for kind, x, w in d.get('hazards', []):
                self.assertIn(kind, HAZARD_DEFS)
                self.assertGreater(w, 0)


# ---------------------------------------------------------------- 可达性
def simulate_jump_reach():
    """用真实物理参数算出单次跳跃的最大高度和最远水平距离。"""
    vy, y, peak = JUMP_V, 0.0, 0.0
    t = 0
    while True:
        vy += GRAVITY
        y += vy
        t += 1
        peak = min(peak, y)
        if y >= 0 and vy > 0:
            break
    return -peak, t * MOVE_SPEED


class ReachabilityTests(unittest.TestCase):
    def setUp(self):
        self.max_h, self.max_d = simulate_jump_reach()

    def test_jump_numbers_match_documentation(self):
        self.assertGreater(self.max_h, 120)
        self.assertGreater(self.max_d, 100)

    def test_every_pit_is_jumpable(self):
        # 起跳点留 20 像素余量：玩家不会正好在边缘起跳
        for name, d in LEVEL_DATA.items():
            g = d['ground']
            for (a1, b1), (a2, b2) in zip(g, g[1:]):
                gap = a2 - b1
                self.assertLessEqual(gap, self.max_d - 10, '%s 的坑 %s 太宽（%d > %.0f）' % (name, (b1, a2), gap, self.max_d))

    def test_every_platform_is_reachable_from_something(self):
        """每块平台，要么高度够得着地面，要么够得着另一块能到达的平台（逐层向上）。"""
        for name, d in LEVEL_DATA.items():
            surfaces = [(a, b, GROUND_Y) for a, b in d['ground']]
            plats = [(x, x + w, y) for x, y, w in d['plats']]
            plats += [(x - amp, x + w + amp, y) for x, y, w, amp, _ in d.get('movers', [])]
            reached = list(surfaces)
            changed = True
            while changed:
                changed = False
                for p in plats:
                    if p in reached:
                        continue
                    for s in reached:
                        dy = s[2] - p[2]                       # 目标比起点高多少
                        gap = max(0, max(p[0] - s[1], s[0] - p[1]))   # 水平空隙
                        if dy <= self.max_h - 10 and gap <= self.max_d - 20:
                            reached.append(p)
                            changed = True
                            break
            unreachable = [p for p in plats if p not in reached]
            self.assertEqual(unreachable, [], '%s 有够不着的平台: %s' % (name, unreachable))

    def test_platform_vertical_steps_are_not_too_tall(self):
        for name, d in LEVEL_DATA.items():
            for x, y, w in d['plats']:
                self.assertLessEqual(GROUND_Y - y, 260, '%s 平台 %s 太高' % (name, (x, y)))

    def test_portal_and_smith_reachable_on_ground(self):
        for name, d in LEVEL_DATA.items():
            for k in ('portalX', 'smithX'):
                x = d.get(k)
                if x is not None:
                    self.assertTrue(any(a <= x <= b for a, b in d['ground']), '%s 的 %s 在坑里' % (name, k))

    def test_hazards_do_not_block_the_only_path(self):
        """危险物只放在深坑边或地面上，且两侧都留有落脚点（不能把一整段地面全铺满）。"""
        for name, d in LEVEL_DATA.items():
            for a, b in d['ground']:
                covered = sum(w for k, x, w in d.get('hazards', []) if a <= x < b)
                self.assertLess(covered, (b - a) * 0.6, '%s 地面 %s 被危险物占得太满' % (name, (a, b)))


# ---------------------------------------------------------------- 危险物
class HazardTests(unittest.TestCase):
    def place(self, e, kind):
        e.hazards = [{'kind': kind, 'x': 300, 'y': GROUND_Y - 6, 'w': 120, 'h': 40}]
        p = e.player
        p['x'], p['y'] = 340.0, float(GROUND_Y - p['h'] - 1)
        p['hp'] = p['maxHp'] = 100
        p['armor'] = 0

    def test_spikes_hurt_and_bounce(self):
        e = goto(started(), 'forest')
        self.place(e, 'spikes')
        run(e, 3)
        self.assertLess(e.player['hp'], 100)
        self.assertLess(e.player['vy'], 0 + 1, '被弹起')

    def test_spikes_have_cooldown(self):
        e = goto(started(), 'forest')
        self.place(e, 'spikes')
        run(e, 4)
        hp = e.player['hp']
        run(e, 5)
        self.assertGreaterEqual(hp - e.player['hp'], 0)
        self.assertGreater(e.player['hp'], 100 - 3 * int(100 * HAZARD_DEFS['spikes']['pct']), '短时间内不应被连续扣多次')

    def test_lava_resisted_by_fire_armor(self):
        e1, e2 = goto(started(), 'forest'), goto(started(), 'forest')
        self.place(e1, 'lava')
        self.place(e2, 'lava')
        e2.player['armor'] = 5                         # 熔岩甲 火抗 50%
        run(e1, 3)
        run(e2, 3)
        self.assertLess(100 - e2.player['hp'], 100 - e1.player['hp'])

    def test_poison_ticks_repeatedly_without_bounce(self):
        e = goto(started(), 'forest')
        self.place(e, 'poison')
        run(e, 130)
        self.assertLess(e.player['hp'], 100 - 2 * int(100 * HAZARD_DEFS['poison']['pct']) + 1)
        self.assertTrue(e.player['inPoison'])

    def test_airborne_player_is_not_hurt(self):
        e = goto(started(), 'forest')
        self.place(e, 'spikes')
        e.player['y'] = 200.0
        e.player['vy'] = 0
        run(e, 2)
        self.assertEqual(e.player['hp'], 100)

    def test_hazard_can_kill_with_clear_reason(self):
        e = goto(started(), 'forest')
        self.place(e, 'lava')
        e.player['hp'] = 1
        run(e, 3)
        self.assertEqual(e.game['state'], 'dead')
        self.assertIn('岩浆', e.game['deadReason'])


# ---------------------------------------------------------------- 移动平台
class MoverTests(unittest.TestCase):
    def test_platform_moves_back_and_forth(self):
        e = goto(started(), 'lava')
        pl = e.movers[0]['plat']
        xs = []
        for _ in range(400):
            e.tick(K())
            xs.append(pl['x'])
        self.assertGreater(max(xs) - min(xs), e.movers[0]['amp'] * 1.5)

    def test_player_rides_the_platform(self):
        e = goto(started(), 'lava')
        m = e.movers[0]
        pl = m['plat']
        e.platforms = [pl]                                   # 只留这一块，排除地面的影响
        e.hazards = []
        p = e.player
        p['x'], p['y'] = pl['x'] + 30, pl['y'] - p['h'] - 0.5
        run(e, 3)
        self.assertTrue(p['onGround'])
        x0, px0 = pl['x'], p['x']
        run(e, 45)
        moved_plat, moved_player = pl['x'] - x0, p['x'] - px0
        self.assertGreater(abs(moved_plat), 5)
        self.assertAlmostEqual(moved_player, moved_plat, delta=3.0, msg='站在平台上应随平台移动')

    def test_player_stays_when_not_on_platform(self):
        e = goto(started(), 'lava')
        p = e.player
        e.hazards = []
        p['x'] = 100.0
        run(e, 60)
        self.assertAlmostEqual(p['x'], 100.0, delta=0.5)

    def test_movers_not_in_static_level_message_but_in_state(self):
        e = goto(started(), 'lava')
        self.assertTrue(all(not pl.get('mover') for pl in e.level_message()['platforms']))
        self.assertEqual(len(e.get_state()['movers']), len(LEVEL_DATA['lava']['movers']))


# ---------------------------------------------------------------- 木箱
class CrateTests(unittest.TestCase):
    def test_melee_breaks_crate_in_two_hits(self):
        e = goto(started(), 'forest')
        c = e.crates[0]
        p = e.player
        p['x'], p['y'] = c['x'] - 30.0, float(GROUND_Y - p['h'] - 1)
        p['facing'] = 1
        p['weapon'] = 1
        e.player_attack()
        self.assertEqual(c['hp'], 1)
        p['atkCD'] = 0
        e.player_attack()
        self.assertLessEqual(c['hp'], 0)
        self.assertEqual(e.game['crates'], 1)

    def test_arrow_breaks_crate(self):
        e = goto(started(), 'forest')
        c = e.crates[0]
        c['hp'] = 1
        p = e.player
        p['x'], p['y'] = c['x'] - 150.0, float(GROUND_Y - p['h'] - 1)
        p['facing'] = 1
        p['weapon'] = 3
        e.aim = None
        e.player_attack()
        run(e, 40)
        self.assertLessEqual(c['hp'], 0)

    def test_broken_crate_disappears_from_state(self):
        e = goto(started(), 'forest')
        n = len(e.get_state()['crates'])
        e.crates[0]['hp'] = 0
        self.assertEqual(len(e.get_state()['crates']), n - 1)


# ---------------------------------------------------------------- 隐藏房间
class SecretTests(unittest.TestCase):
    def setUp(self):
        self.e = goto(started(), 'forest')
        self.s = self.e.secrets[0]
        p = self.e.player
        p['x'], p['y'] = self.s['x'] - 50.0, float(GROUND_Y - p['h'] - 1)
        p['facing'] = 1
        p['weapon'] = 1

    def hit(self):
        self.e.player['atkCD'] = 0
        self.e.player_attack()

    def test_wall_needs_several_hits(self):
        for i in range(self.s['maxHp'] - 1):
            self.hit()
        self.assertFalse(self.s['open'])
        self.hit()
        self.assertTrue(self.s['open'])
        self.assertEqual(self.e.game['secretsFound'], 1)

    def test_prompt_hints_at_cracked_wall_then_door(self):
        self.assertIn('裂缝', self.e.prompt()['text'])
        for _ in range(self.s['maxHp']):
            self.hit()
        self.e.player['x'] = self.s['x'] - 10.0
        self.assertIn('隐藏房间', self.e.prompt()['text'])

    def test_enter_room_contains_chest_and_exit(self):
        for _ in range(self.s['maxHp']):
            self.hit()
        self.e.player['x'] = self.s['x'] - 10.0
        run(self.e, 1, interact=True)
        run(self.e, 1)
        run(self.e, 70)
        self.assertTrue(self.e.game['state'].startswith('secret_'))
        self.assertEqual(len(self.e.chests), 1)
        self.assertIsNotNone(self.e.backX)

    def test_walk_in_and_open_the_chest_for_every_secret_room(self):
        """真实流程：破墙 → 进门 → 从出生点走到宝箱 → 按 E 拿到奖励。宝箱不能放在要爬的平台上。"""
        for lvl in ('forest', 'swamp', 'crypt'):
            e = goto(started(), lvl)
            e.hazards = []
            s, p = e.secrets[0], e.player
            p['x'], p['y'], p['facing'], p['weapon'] = s['x'] - 50.0, float(GROUND_Y - 31), 1, 1
            for _ in range(s['maxHp']):
                p['atkCD'] = 0
                e.player_attack()
            p['x'] = s['x'] - 10.0
            run(e, 1, interact=True)
            run(e, 80)
            self.assertTrue(e.game['state'].startswith('secret_'), lvl)
            c = e.chests[0]
            for _ in range(400):
                if abs(p['x'] + p['w'] / 2 - (c['x'] + c['w'] / 2)) <= 14:
                    break
                run(e, 1, right=True)
            run(e, 1, interact=True)
            self.assertTrue(c['opened'], '%s 的隐藏房间宝箱打不开' % lvl)
            kind, val = c['give']
            owned = p['ownedWeapons'] if kind == 'weapon' else p['ownedArmors']
            self.assertIn(val, owned)

    def test_secret_room_reward_matches_definition(self):
        d = build_data('secret_forest_0')
        _, _, give = LEVEL_DATA['forest']['secrets'][0]
        self.assertEqual(d['chests'][0][2], give)


# ---------------------------------------------------------------- 地洞与返回栈
class DescentTests(unittest.TestCase):
    def dive(self, e):
        hole = e.holes[0]
        p = e.player
        p['x'], p['y'] = hole['x'] - 11.0, float(GROUND_Y - p['h'] - 1)
        run(e, 2, down=True)
        run(e, 1, down=True, interact=True)
        run(e, 80)

    def test_needs_down_plus_interact(self):
        e = goto(started(), 'forest')
        hole = e.holes[0]
        e.player['x'], e.player['y'] = hole['x'] - 11.0, float(GROUND_Y - e.player['h'] - 1)
        run(e, 2)
        run(e, 1, interact=True)                      # 只按 E
        run(e, 80)
        self.assertEqual(e.game['state'], 'forest')

    def test_dive_enters_sublevel(self):
        e = goto(started(), 'forest')
        self.dive(e)
        self.assertEqual(e.game['state'], 'sub_root')
        self.assertEqual(len(e.return_stack), 1)
        self.assertEqual(e.game['theme'], 'cave')

    def test_return_restores_position_and_world_state(self):
        e = goto(started(), 'forest')
        e.chests[0]['opened'] = True
        e.crates[0]['hp'] = 0
        hole_x = e.holes[0]['x']
        self.dive(e)
        run(e, 1)
        e.player['x'] = e.backX - 10.0
        run(e, 1, interact=True)
        run(e, 80)
        self.assertEqual(e.game['state'], 'forest')
        self.assertTrue(e.chests[0]['opened'], '地表宝箱的状态应保留')
        self.assertEqual(e.crates[0]['hp'], 0, '木箱的状态应保留')
        self.assertAlmostEqual(e.player['x'] + e.player['w'] / 2, hole_x, delta=15)
        self.assertEqual(e.return_stack, [])

    def test_sublevel_loot_persists_across_visit_only_in_stack(self):
        """子关卡本身每次进入都是全新的（宝箱重置）：这是设计选择，用测试把它固定下来。"""
        e = goto(started(), 'forest')
        self.dive(e)
        e.chests[0]['opened'] = True
        e.player['x'] = e.backX - 10.0
        run(e, 1, interact=True)
        run(e, 80)
        self.dive(e)
        self.assertFalse(e.chests[0]['opened'])

    def test_dying_underground_restarts_main_level(self):
        e = goto(started(), 'forest')
        self.dive(e)
        e.player['hp'] = 0
        e.player_die('test')
        run(e, 60)
        run(e, 1, confirm=True)
        self.assertEqual(e.game['state'], 'forest')
        self.assertEqual(e.return_stack, [])

    def test_menu_clears_stack(self):
        e = goto(started(), 'forest')
        self.dive(e)
        e.to_menu()
        self.assertEqual(e.return_stack, [])
        self.assertEqual(e.game['state'], 'menu')

    def test_underground_has_no_portal_forward(self):
        e = goto(started(), 'forest')
        self.dive(e)
        self.assertIsNone(e.portalX)
        e.enemies = []
        run(e, 30)
        self.assertEqual(e.game['state'], 'sub_root')

    def test_back_prompt_and_hint(self):
        e = goto(started(), 'forest')
        self.dive(e)
        e.player['x'] = e.backX - 10.0
        self.assertIn('返回', e.prompt()['text'])

    def test_every_sublevel_is_enterable_and_runs(self):
        for name in [n for n in LEVEL_DATA if n.startswith('sub_')]:
            e = goto(started(), 'forest')
            e.return_stack.append({'level': 'forest', 'x': 100.0, 'chests': e.chests, 'enemies': e.enemies,
                                   'crates': e.crates, 'secrets': e.secrets, 'coins': [], 'hazards': e.hazards,
                                   'holes': e.holes})
            e.load(name)
            e.game['state'] = name
            run(e, 120)
            json.dumps(e.get_state())


# ---------------------------------------------------------------- 主线流程
class ProgressionTests(unittest.TestCase):
    def test_full_chain_through_portals(self):
        e = goto(started(), 'forest')
        seen = [e.game['state']]
        for _ in range(len(LEVEL_ORDER) - 1):
            e.enemies = []
            e.player['x'] = e.portalX - 100.0
            e.player['y'] = float(GROUND_Y - e.player['h'] - 1)
            e.player['hp'] = e.player['maxHp'] = 9999
            run(e, 120, right=True)
            seen.append(e.game['state'])
            e.hazards = []
        self.assertEqual(seen, LEVEL_ORDER)

    def test_clearing_gives_bonus_exp_each_level(self):
        e = goto(started(), 'swamp')
        e.player['x'] = e.portalX - 100.0
        exp0, lvl0 = e.player['exp'], e.player['level']
        run(e, 120, right=True)
        self.assertEqual(e.game['state'], 'crypt')
        self.assertTrue(e.player['exp'] > exp0 or e.player['level'] > lvl0)

    def test_hud_title_for_all_states(self):
        e = started()
        for name in list(LEVEL_DATA):
            goto(e, name)
            self.assertTrue(e.level_title())
            json.dumps(e.get_state())


# ---------------------------------------------------------------- 无尽模式
class EndlessTests(unittest.TestCase):
    def test_menu_selects_mode(self):
        e = GameEngine(seed=1)
        self.assertEqual(e.game['state'], 'menu')
        run(e, 1, down=True)
        self.assertEqual(e.game['menuIdx'], 1)
        run(e, 1)
        run(e, 1, confirm=True)
        self.assertEqual(e.game['mode'], 'endless')
        self.assertEqual(e.game['state'], 'arena')

    def test_menu_wraps_and_default_is_adventure(self):
        e = GameEngine(seed=1)
        run(e, 1, up=True)
        self.assertEqual(e.game['menuIdx'], len(MODES) - 1)
        run(e, 1)
        run(e, 1, down=True)
        self.assertEqual(e.game['menuIdx'], 0)
        run(e, 1)
        run(e, 1, confirm=True)
        self.assertEqual(e.game['mode'], 'adventure')
        self.assertEqual(e.game['state'], 'forest')

    def test_first_wave_spawns_and_has_no_portal(self):
        e = started('endless')
        self.assertEqual(e.game['wave'], 1)
        self.assertGreater(e.remaining_enemies(), 0)
        self.assertIsNone(e.portalX)

    def test_waves_get_harder(self):
        e = started('endless')
        counts = [e.remaining_enemies()]
        for _ in range(3):
            for en in e.enemies:
                en['alive'] = False
                en['dying'] = 0
            e.enemies = []
            run(e, 200)
            counts.append(e.remaining_enemies())
        self.assertGreater(counts[-1], counts[0])
        self.assertEqual(e.game['wave'], 4)

    def test_wave_bonus_and_best_wave(self):
        e = started('endless')
        gold = e.player['gold']
        for en in e.enemies:
            en['alive'] = False
            en['dying'] = 0
        e.enemies = []
        run(e, 8)                                   # 开局的卡片 / 提示会占几帧，等够再检查
        self.assertGreater(e.player['gold'], gold)
        self.assertEqual(e.game['bestWave'], 1)

    def test_wave_size_is_capped(self):
        e = started('endless')
        e.game['wave'] = 99
        e.enemies = []
        e.spawn_wave()
        self.assertLessEqual(len(e.enemies), 14)

    def test_late_waves_include_tougher_enemies(self):
        e = started('endless')
        self.assertNotIn('shield', e.endless_enemy_pool(1))
        self.assertIn('shield', e.endless_enemy_pool(8))

    def test_death_in_endless_returns_to_menu(self):
        e = started('endless')
        e.player_die('test')
        run(e, 60)
        run(e, 1, confirm=True)
        self.assertEqual(e.game['state'], 'menu')

    def test_adventure_after_endless_is_clean(self):
        e = started('endless')
        e.to_menu()
        e.game['menuIdx'] = 0
        run(e, 1)
        run(e, 1, confirm=True)
        self.assertEqual(e.game['state'], 'forest')
        self.assertEqual(e.game['wave'], 0)


if __name__ == '__main__':
    unittest.main()
