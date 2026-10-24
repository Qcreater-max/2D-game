"""元素、防御、状态效果、装备抗性、怪物卡片。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine import GameEngine
from game_data import (INPUT_KEYS, GROUND_Y, ENEMY_DEFS, WEAPONS, ARMORS, ELEMENTS, CATALOG,
                       WEAK_MULT, RESIST_MULT, MIN_DMG_RATIO, BURN_FRAMES, SLOW_FACTOR)


def K(**k):
    d = {x: False for x in INPUT_KEYS}
    d.update(k)
    return d


def new_engine(level='forest'):
    e = GameEngine(seed=11)
    e.tick(K(confirm=True))
    e.tick(K())
    e.load(level)
    e.enemies = []
    # 开局那一帧已经让关卡自带的怪物入镜并记入 seen；清空后，测试自己摆的怪才算"第一次出现"
    e.seen, e.card, e.card_q = set(), None, []
    e.player['x'], e.player['y'] = 300.0, float(GROUND_Y - e.player['h'] - 1)
    return e


def spawn(e, etype, x):
    en = e.make_enemy(etype, x, GROUND_Y - ENEMY_DEFS[etype]['h'] - 1)
    en['atkCD'] = 9999
    e.enemies.append(en)
    return en


def run(e, n, **keys):
    for _ in range(n):
        e.tick(K(**keys))


class DamageFormulaTests(unittest.TestCase):
    def test_weakness_multiplier(self):
        e = new_engine()
        s = spawn(e, 'slime', 800)                      # 弱火，防御 0
        dmg, tag = e.calc_damage(s, 20, 'fire', False, False)
        self.assertEqual((dmg, tag), (int(20 * WEAK_MULT), 'weak'))

    def test_resist_multiplier(self):
        e = new_engine()
        sk = spawn(e, 'skeleton', 800)                  # 抗冰，防御 3
        dmg, tag = e.calc_damage(sk, 20, 'ice', False, False)
        self.assertEqual(tag, 'resist')
        self.assertEqual(dmg, int(round(max(20 * RESIST_MULT * MIN_DMG_RATIO, 20 * RESIST_MULT - sk['def']))))

    def test_defense_subtracts_flat(self):
        e = new_engine()
        sk = spawn(e, 'skeleton', 800)
        dmg, _ = e.calc_damage(sk, 20, 'phys', False, False)
        self.assertEqual(dmg, 20 - sk['def'])

    def test_damage_never_below_minimum_ratio(self):
        e = new_engine()
        sh = spawn(e, 'shield', 800)                    # 防御 6
        dmg, _ = e.calc_damage(sh, 8, 'phys', False, False)
        self.assertEqual(dmg, int(round(8 * MIN_DMG_RATIO)))   # 8-6=2 < 2.4，按保底
        self.assertGreaterEqual(dmg, 1)

    def test_crit_applies_before_defense(self):
        e = new_engine()
        sk = spawn(e, 'skeleton', 800)
        dmg, _ = e.calc_damage(sk, 10, 'phys', True, False)
        self.assertEqual(dmg, 10 * 2 - sk['def'])

    def test_all_enemy_defs_reference_valid_elements(self):
        for t, d in ENEMY_DEFS.items():
            for k in ('weak', 'resist', 'atk'):
                v = d[k]
                self.assertTrue(v is None or v in ELEMENTS, '%s.%s=%r' % (t, k, v))
            self.assertNotEqual(d['weak'], d['resist'], t)

    def test_all_weapons_have_valid_element_and_style(self):
        for w in WEAPONS:
            self.assertIn(w['elem'], ELEMENTS)
            self.assertIn(w['style'], ('sword', 'axe', 'bow', 'staff', 'spear'))


class StatusTests(unittest.TestCase):
    def test_fire_applies_burn_that_ticks(self):
        e = new_engine()
        s = spawn(e, 'goblin', 800)                     # 不抗火
        e.damage_enemy(s, 10, 1, silent_crit=True, elem='fire')
        self.assertGreater(s['burn'], 0)
        hp = s['hp']
        run(e, 65)
        self.assertLess(s['hp'], hp, '灼烧应持续掉血')

    def test_burn_expires(self):
        e = new_engine()
        s = spawn(e, 'goblin', 800)
        s['hp'] = s['maxHp'] = 9999
        e.damage_enemy(s, 10, 1, silent_crit=True, elem='fire')
        run(e, BURN_FRAMES + 5)
        self.assertEqual(s['burn'], 0)

    def test_fire_resistant_enemy_does_not_burn(self):
        e = new_engine()
        b = spawn(e, 'bomber', 800)                     # 抗火
        b['hp'] = 999
        e.damage_enemy(b, 10, 1, silent_crit=True, elem='fire')
        self.assertEqual(b['burn'], 0)

    def test_ice_slows_movement(self):
        e = new_engine()
        e.player['x'] = 800.0                           # 玩家在追击范围内（距离 200），两只都会追过来
        a = spawn(e, 'goblin', 1000)
        b = spawn(e, 'goblin', 1000)
        b['slow'] = 120
        for en in (a, b):
            en['hp'] = en['maxHp'] = 9999
        x0 = a['x']
        run(e, 40)
        moved_a, moved_b = abs(a['x'] - x0), abs(b['x'] - x0)
        self.assertGreater(moved_a, 30, '正常的哥布林应在追击')
        self.assertAlmostEqual(moved_b, moved_a * SLOW_FACTOR, delta=2.0)

    def test_boss_immune_to_slow(self):
        e = new_engine('boss')
        e.enemies = []
        w = e.make_enemy('wizard', 600, 150)
        e.enemies.append(w)
        e.damage_enemy(w, 10, 1, silent_crit=True, elem='ice')
        self.assertEqual(w['slow'], 0)

    def test_slow_does_not_corrupt_ai_velocity(self):
        """减速不能把 AI 设定的速度永久改小：冰冻结束后蝙蝠俯冲速度应恢复。"""
        e = new_engine('crypt')
        e.enemies = []
        bat = e.make_enemy('bat', 500, 200)
        bat['mode'], bat['modeT'] = 'dive', 30
        bat['vx'], bat['vy'] = 3.4, 0.0
        bat['slow'] = 10
        e.enemies.append(bat)
        e.move_enemy(bat)
        self.assertEqual(bat['vx'], 3.4)

    def test_thunder_chains_once(self):
        e = new_engine()
        a = spawn(e, 'goblin', 700)
        b = spawn(e, 'goblin', 760)
        c = spawn(e, 'goblin', 820)
        for en in (a, b, c):
            en['hp'] = en['maxHp'] = 500
        e.damage_enemy(a, 20, 1, silent_crit=True, elem='thunder')
        self.assertLess(b['hp'], 500, '最近的敌人应被电弧击中')
        self.assertEqual(c['hp'], 500, '电弧只跳一次')
        self.assertTrue(any(f['kind'] == 'bolt' for f in e.fx))

    def test_thunder_ignores_shield_block(self):
        e = new_engine()
        sh = spawn(e, 'shield', 700)
        sh['dir'] = -1
        hp = sh['hp']
        e.damage_enemy(sh, 20, 1, silent_crit=True, elem='thunder')
        self.assertLess(sh['hp'], hp)

    def test_blast_pierces_shield_and_burns(self):
        e = new_engine()
        e.player['x'] = 100.0
        b = spawn(e, 'bomber', 700)
        sh = spawn(e, 'shield', 730)
        sh['dir'] = -1
        sh['hp'] = sh['maxHp'] = 500
        e.explode(b)
        self.assertLess(sh['hp'], 500)
        self.assertGreater(sh['burn'], 0)


class ArmorTests(unittest.TestCase):
    def test_resistance_reduces_elemental_damage(self):
        e = new_engine()
        e.player['armor'] = 5                           # 熔岩甲 火抗 50
        e.damage_player(20, 0, elem='fire')
        fire_loss = 100 - e.player['hp']
        e2 = new_engine()
        e2.player['armor'] = 5
        e2.damage_player(20, 0, elem='phys')
        phys_loss = 100 - e2.player['hp']
        self.assertLess(fire_loss, phys_loss)

    def test_negative_resistance_increases_damage(self):
        e = new_engine()
        e.player['armor'] = 2                           # 铁甲 雷 -15
        e.damage_player(20, 0, elem='thunder')
        e2 = new_engine()
        e2.player['armor'] = 2
        e2.damage_player(20, 0, elem='phys')
        self.assertGreater(100 - e.player['hp'], 100 - e2.player['hp'])

    def test_enemy_attack_elements_reach_player(self):
        e = new_engine('crypt')
        e.enemies = []
        bat = e.make_enemy('bat', e.player['x'], e.player['y'])
        e.enemies.append(bat)
        e.player['armor'] = 0
        bat['atkCD'] = 9999
        run(e, 2)
        floaters = [t['txt'] for t in e.texts]
        self.assertTrue(any(t.startswith('-') for t in floaters))


class WeaponElementTests(unittest.TestCase):
    def test_weapon_element_used_in_melee(self):
        e = new_engine()
        e.player['weapon'] = 5                          # 烈焰剑
        e.player['ownedWeapons'].add(5)
        s = spawn(e, 'goblin', int(e.player['x']) + 30)
        s['hp'] = s['maxHp'] = 500
        e.player_attack()
        self.assertGreater(s['burn'], 0)

    def test_fire_staff_projectile_carries_element(self):
        e = new_engine()
        e.player['weapon'] = 4
        e.player_attack()
        self.assertEqual(e.projectiles[0]['elem'], 'fire')
        self.assertEqual(e.projectiles[0]['kind'], 'fire')

    def test_bow_is_physical(self):
        e = new_engine()
        e.player['weapon'] = 3
        e.player_attack()
        self.assertEqual(e.projectiles[0]['elem'], 'phys')


class CardTests(unittest.TestCase):
    def test_card_appears_for_new_enemy_in_view(self):
        e = new_engine()
        spawn(e, 'slime', 500)
        run(e, 2)
        self.assertIsNotNone(e.card)
        self.assertEqual(e.card['type'], 'slime')

    def test_card_not_repeated_for_same_type(self):
        e = new_engine()
        spawn(e, 'slime', 500)
        run(e, 2)
        e.card = None
        spawn(e, 'slime', 560)
        run(e, 2)
        self.assertIsNone(e.card)

    def test_offscreen_enemy_does_not_trigger_card(self):
        e = new_engine()
        spawn(e, 'slime', 2000)
        run(e, 2)
        self.assertIsNone(e.card)

    def test_cards_queue_and_expire(self):
        e = new_engine()
        e.player['hp'] = e.player['maxHp'] = 9999       # 哥布林会追击，别让玩家中途死亡
        spawn(e, 'slime', 500)
        spawn(e, 'goblin', 560)
        run(e, 2)
        self.assertEqual(e.card['type'], 'slime')
        self.assertEqual(e.card_q, ['goblin'])
        run(e, 600)
        self.assertNotEqual(e.card and e.card['type'], 'slime')

    def test_seen_resets_on_new_game(self):
        e = new_engine()
        spawn(e, 'slime', 500)
        run(e, 2)
        e.to_menu()
        e.tick(K(confirm=True))
        self.assertEqual(e.seen, set())

    def test_catalog_contains_all_enemies_and_is_serialisable(self):
        import json
        json.dumps(CATALOG)
        self.assertEqual(set(CATALOG['enemies']), set(ENEMY_DEFS))
        for t, d in CATALOG['enemies'].items():
            for k in ('name', 'hp', 'def', 'weak', 'atk', 'desc'):
                self.assertIn(k, d)

    def test_level_message_carries_catalog(self):
        e = new_engine()
        self.assertIn('catalog', e.level_message())


if __name__ == '__main__':
    unittest.main()
