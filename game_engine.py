"""
游戏核心逻辑引擎。

所有规则（物理、战斗、AI、关卡流程）都在后端；前端只负责渲染和采集按键。
模块划分：
  game_data.py  常量与数值表        physics.py  碰撞与移动
  levels.py     关卡数据            combat.py   战斗、伤害、升级
  enemies.py    敌人与通用 AI       boss.py     暗影巫师
  world.py      危险物、移动平台、木箱、地洞、隐藏房间、无尽模式
"""
import math
import random

from game_data import (
    W, H, GRAVITY, JUMP_V, MOVE_SPEED, MAX_FALL, GROUND_Y, INPUT_KEYS, PIT_DAMAGE_PCT,
    SAFE_FALL, FALL_PCT_PER_PX, FALL_MAX_PCT,
    LEVEL_ORDER, LEVEL_NAMES, LEVEL_CLEAR_EXP, WEAPONS, ARMORS, weapon_power,
    CATALOG, CARD_FRAMES, parse_aim, MODES,
)
from levels import load_level, is_sub
from physics import move_body, rects_overlap, has_ground_at, in_solid
from combat import CombatMixin
from enemies import EnemyMixin
from boss import BossMixin
from world import WorldMixin

END_SCREEN_DELAY = 45   # 死亡 / 通关画面里，防止误触的输入延迟（帧）
PORTAL_W, PORTAL_H = 48, 80


def r1(v):
    return round(v, 1)


class GameEngine(CombatMixin, EnemyMixin, BossMixin, WorldMixin):
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.reset()

    # ============== 初始化 ==============
    def reset(self):
        self.game = {
            'state': 'menu', 'level': 0, 'camX': 0.0, 'time': 0, 'playTime': 0,
            'flash': 0, 'shake': 0.0, 'msg': '', 'msgT': 0, 'introT': 0, 'fade': 0.0,
            'hitstop': 0, 'hurtFlash': 0,
            'panel': None, 'panelTab': 0, 'panelIdx': 0,
            'deadReason': '', 'endT': 0, 'lastLevel': 'forest',
            'kills': 0, 'totalDamage': 0, 'goldEarned': 0,
            'title': '', 'hint': '', 'theme': 'forest',
            'mode': 'adventure', 'menuIdx': 0,
            'wave': 0, 'waveBreak': 0, 'bestWave': 0,
            'crates': 0, 'secretsFound': 0, 'holesEntered': 0,
        }
        self.return_stack = []
        self.prev = {k: False for k in INPUT_KEYS}
        self.aim = None
        self.trans = None
        self.win_timer = 0
        self.level_seq = 0
        self.seen, self.card, self.card_q = set(), None, []
        self.new_player()
        self.load('forest')
        self.game['state'] = 'menu'
        self.game['introT'] = 0

    def new_player(self):
        self.player = {
            'x': 60.0, 'y': 0.0, 'w': 22, 'h': 30, 'vx': 0.0, 'vy': 0.0,
            'onGround': False, 'hitWall': False, 'standing': None, 'facing': 1,
            'hp': 100, 'maxHp': 100, 'level': 1, 'exp': 0, 'expNext': 30, 'gold': 0,
            'weapon': 0, 'armor': 0, 'atkCD': 0, 'hurtCD': 0, 'attackAnim': 0,
            'ownedWeapons': {0}, 'ownedArmors': {0},
            'coyote': 0, 'jbuf': 0, 'dropT': 0, 'kbV': 0.0, 'lunge': 0.0, 'safe': (60.0, 0.0),
            'standingOn': None, 'inPoison': False, 'airTop': 0.0,
        }

    def new_game(self, mode='adventure'):
        self.new_player()
        self.game.update(kills=0, totalDamage=0, goldEarned=0, playTime=0, flash=0, mode=mode,
                         crates=0, secretsFound=0, holesEntered=0, wave=0, waveBreak=0)
        self.win_timer = 0
        self.trans = None
        self.return_stack = []
        self.seen, self.card, self.card_q = set(), None, []
        if mode == 'endless':
            self.load('arena')
            self.game['wave'] = 1
            self.spawn_wave()
        else:
            self.load('forest')

    def load(self, name, spawn_x=None):
        d = load_level(name)
        g, p = self.game, self.player
        self.platforms, self.mapW = d['platforms'], d['mapW']
        self.movers = d['movers']
        self.smithX, self.portalX, self.backX = d['smithX'], d['portalX'], d['back']
        self.portal = None if d['portalX'] is None else {
            'x': d['portalX'] - PORTAL_W // 2, 'y': GROUND_Y - PORTAL_H, 'w': PORTAL_W, 'h': PORTAL_H}
        self.chests = d['chests']
        self.hazards, self.crates = d['hazards'], d['crates']
        self.holes, self.secrets = d['holes'], d['secrets']
        self.enemies = [self.make_enemy(*s) for s in d['spawns']]
        self.enemies_total = len(self.enemies)
        self.projectiles, self.enemyProj = [], []
        self.card, self.card_q = None, []
        self.particles, self.coins, self.texts, self.fx = [], [], [], []
        g['hitstop'] = 0
        sx = 60.0 if spawn_x is None else float(spawn_x)
        p.update(x=sx, y=float(GROUND_Y - p['h'] - 1), vx=0.0, vy=0.0, kbV=0.0, lunge=0.0,
                 onGround=True, coyote=0, jbuf=0, dropT=0, atkCD=0, hurtCD=0,
                 standingOn=None, inPoison=False)
        p['safe'] = (p['x'], p['y'])
        p['airTop'] = p['y']                 # 换关是传送，不能带着上一关的落差去落地
        g.update(state=name, title=d['title'], hint=d['hint'], theme=d['theme'],
                 introT=200, panel=None, camX=max(0.0, min(self.mapW - W, sx - W / 2)))
        if name in LEVEL_ORDER:
            g['lastLevel'] = name
            g['level'] = LEVEL_ORDER.index(name)
        self.level_seq += 1

    # ============== 输入 ==============
    def read_input(self, inp):
        held = {k: bool(inp.get(k)) for k in INPUT_KEYS}
        edge = {k: held[k] and not self.prev[k] for k in INPUT_KEYS}
        self.prev = held
        # 鼠标瞄准：只有"鼠标正在瞄准"时才有值（客户端松开左键就不再上报）
        self.aim = parse_aim(inp.get('aim')) if inp.get('aim') is not None else None
        return held, edge

    # ============== 主循环 ==============
    def tick(self, inp):
        """推进一帧。inp 为按键状态字典（按住为 True），本方法不会修改它。"""
        held, edge = self.read_input(inp)
        g = self.game
        g['time'] += 1
        for k in ('msgT', 'introT', 'flash', 'hurtFlash'):
            if g[k] > 0:
                g[k] -= 1
        if g['shake'] > 0:
            g['shake'] = g['shake'] * 0.85 if g['shake'] > 0.3 else 0.0

        st = g['state']
        if st == 'menu':
            n = len(MODES)
            if edge['up'] or edge['left']:
                g['menuIdx'] = (g['menuIdx'] - 1) % n
            if edge['down'] or edge['right']:
                g['menuIdx'] = (g['menuIdx'] + 1) % n
            if edge['confirm'] or edge['attack']:
                self.new_game(MODES[g['menuIdx']])
        elif st in ('win', 'dead'):
            g['endT'] += 1
            if g['endT'] > END_SCREEN_DELAY:
                if edge['confirm'] or edge['attack']:
                    # 无尽模式死亡就是结束，回主菜单；冒险模式重新挑战本关
                    if st == 'dead' and g['mode'] == 'adventure':
                        self.retry_level()
                    else:
                        self.to_menu()
                elif edge['escape']:
                    self.to_menu()
        else:
            self.tick_play(held, edge)
        self.update_particles()

    def tick_play(self, held, edge):
        g = self.game
        if self.trans:
            self.advance_transition()
        elif g['panel']:
            self.tick_panel(edge)
        else:
            if edge['inv']:
                self.open_panel('inv')
            elif edge['stats']:
                self.open_panel('stats')
            elif edge['interact']:
                self.do_interact()
            if g['panel'] is None and not self.trans:
                self.step_world(held, edge)

    def step_world(self, held, edge):
        g = self.game
        if g['hitstop'] > 0:                 # 命中停顿：世界定格，但不吞掉刚按下的跳跃
            g['hitstop'] -= 1
            if edge['jump']:
                self.player['jbuf'] = 6
            return
        g['playTime'] += 1
        self.update_movers()
        self.update_player(held, edge)
        if g['state'] == 'dead':
            return
        self.update_hazards()
        if g['state'] == 'dead':
            return
        self.update_enemies()
        self.update_projectiles()
        self.update_pickups()
        self.update_cards()
        if g['mode'] == 'endless':
            self.update_endless()
        else:
            self.check_portal()
        p = self.player
        target = max(0, min(self.mapW - W, p['x'] + p['w'] / 2 - W / 2))
        g['camX'] += (target - g['camX']) * 0.18
        if self.win_timer:
            self.win_timer -= 1
            if self.win_timer == 0:
                g['state'], g['endT'], g['panel'] = 'win', 0, None

    def level_title(self):
        """HUD 上显示的关卡名：子关卡和竞技场用自己的标题，主线用 LEVEL_NAMES。"""
        g = self.game
        if g['state'] in LEVEL_ORDER:
            return LEVEL_NAMES[g['level']]
        if g['mode'] == 'endless':
            return '无尽挑战  第 %d 波' % g['wave']
        return g['title'].split('  ', 1)[-1]

    def update_cards(self):
        """怪物图鉴卡片：某种怪物第一次进入视野时弹出，多个同时出现就排队依次显示。"""
        cam = self.game['camX']
        for e in self.enemies:
            if e['alive'] and e['type'] not in self.seen and cam - 40 < e['x'] < cam + W + 40:
                self.seen.add(e['type'])
                self.card_q.append(e['type'])
        if self.card:
            # 后面还有排队的卡片时，当前这张缩短显示，避免一直占着屏幕
            self.card['t'] -= 2 if self.card_q else 1
            if self.card['t'] <= 0:
                self.card = None
        if not self.card and self.card_q:
            self.card = {'type': self.card_q.pop(0), 't': CARD_FRAMES}

    def to_menu(self):
        self.return_stack = []
        self.trans = None
        self.game['mode'] = 'adventure'
        self.load('forest')
        self.game['state'] = 'menu'
        self.game['introT'] = 0

    def retry_level(self):
        """死亡后重来：回到当前主线关卡的起点（在子关卡里死亡也回主线关卡，且清空返回栈）。"""
        self.player['hp'] = self.player['maxHp']
        self.win_timer = 0
        self.return_stack = []
        self.load(self.game['lastLevel'])
        self.show_msg('重新挑战', 60)

    # ============== 玩家 ==============
    def update_player(self, held, edge):
        p = self.player
        mv = (1 if held['right'] else 0) - (1 if held['left'] else 0)
        aim = self.aim_vector()
        if aim and abs(aim[0]) > 0.15 and held['attack']:
            p['facing'] = 1 if aim[0] > 0 else -1       # 鼠标攻击时，角色转向鼠标一侧
        elif mv:
            p['facing'] = mv
        p['vx'] = mv * MOVE_SPEED + p['kbV'] + p['lunge']
        p['kbV'] = p['kbV'] * 0.8 if abs(p['kbV']) > 0.3 else 0.0
        p['lunge'] = p['lunge'] * 0.6 if abs(p['lunge']) > 0.2 else 0.0

        # 跳跃：提前输入缓冲 + 离地宽限，手感更宽容；站在平台上按住 S 再跳可穿下平台
        if edge['jump']:
            p['jbuf'] = 6
        elif p['jbuf'] > 0:
            p['jbuf'] -= 1
        if p['onGround']:
            p['coyote'] = 6
        elif p['coyote'] > 0:
            p['coyote'] -= 1
        if p['jbuf'] > 0 and p['coyote'] > 0:
            if held['down'] and p['standing'] == 'plat':
                p['dropT'] = 12
            else:
                p['vy'] = JUMP_V
            p['jbuf'] = p['coyote'] = 0
            p['onGround'] = False
        elif not held['jump'] and p['vy'] < -3.5:
            p['vy'] = -3.5      # 松开按键提前结束上升，可控制跳跃高度

        p['vy'] = min(MAX_FALL, p['vy'] + GRAVITY)
        drop = p['dropT'] > 0
        if drop:
            p['dropT'] -= 1
        landed = move_body(p, self.platforms, drop)
        p['standing'] = landed['type'] if landed else None
        p['standingOn'] = landed if landed and landed.get('mover') else None   # 下一帧 update_movers 带着走
        if landed:
            self.check_fall_damage()
        else:
            p['airTop'] = min(p['airTop'], p['y'])     # 空中记录到达过的最高点（跳起、被弹起都算）
        p['x'] = max(0, min(self.mapW - p['w'], p['x']))
        if landed and landed['w'] >= 80:
            sx = max(landed['x'] + 14, min(p['x'], landed['x'] + landed['w'] - p['w'] - 14))
            p['safe'] = (sx, landed['y'] - p['h'] - 0.01)

        if p['y'] > H + 60:
            self.fall_into_pit()
            return
        for k in ('atkCD', 'attackAnim', 'hurtCD'):
            if p[k] > 0:
                p[k] -= 1
        if held['attack'] and p['atkCD'] <= 0:
            self.player_attack()

    def fall_distance(self):
        """从离地后到达的最高点到现在的落差（像素）。站在地面上时为 0。"""
        p = self.player
        return max(0.0, p['y'] - p['airTop'])

    def check_fall_damage(self):
        """落地瞬间调用：落差超过安全高度就摔伤。不会致死，无视盔甲的百分比减伤。"""
        p = self.player
        fall = self.fall_distance()
        p['airTop'] = p['y']
        if fall <= SAFE_FALL:
            return
        pct = min(FALL_MAX_PCT, (fall - SAFE_FALL) * FALL_PCT_PER_PX)
        dmg = max(1, int(p['maxHp'] * pct))
        p['hp'] = max(1, p['hp'] - dmg)               # 摔伤最多把人摔到只剩 1 点生命
        p['hurtCD'] = max(p['hurtCD'], 30)
        p['kbV'] = p['lunge'] = 0.0
        cx, feet = p['x'] + p['w'] / 2, p['y'] + p['h']
        self.game['shake'] = max(self.game['shake'], 4 + min(8.0, dmg * 0.4))
        self.game['hurtFlash'] = 6
        self.hitstop(3)
        self.add_text(p['x'] - 6, p['y'] - 8, '摔伤 -%d' % dmg, '#ffb060', 16)
        self.add_particles(cx, feet, 12, '#c8b890', 4)          # 扬起一圈尘土
        self.add_fx('ring', cx, feet - 2, life=14, color='#c8b890')

    def fall_into_pit(self):
        p = self.player
        dmg = max(1, int(p['maxHp'] * PIT_DAMAGE_PCT))
        p['hp'] -= dmg
        if p['hp'] <= 0:
            self.player_die('坠入深渊...')
            return
        p['x'], p['y'] = p['safe']
        p['airTop'] = p['y']                 # 已经按掉坑算过伤害，传送回去不再重复摔伤
        p['vx'] = p['vy'] = p['kbV'] = 0.0
        p['hurtCD'] = 90
        self.game['shake'] = 8
        self.add_text(p['x'], p['y'] - 8, '坠落 -%d' % dmg, '#ff6060', 16)
        self.show_msg('掉进深坑！已送回安全位置', 80)

    # ============== 子弹 / 拾取物 ==============
    def update_projectiles(self):
        for pr in self.projectiles:
            pr['x'] += pr['vx']
            pr['y'] += pr['vy']
            pr['life'] -= 1
            if in_solid(self.platforms, pr['x'], pr['y']):      # 斜射时会打到地面，别穿过去
                pr['life'] = 0
                self.add_particles(pr['x'], pr['y'], 4, pr['color'], 2)
            if pr['kind'] == 'fire':
                self.add_particles(pr['x'], pr['y'], 1, '#ff8020', 1)
            box = {'x': pr['x'] - 5, 'y': pr['y'] - 5, 'w': 10, 'h': 10}
            if pr['life'] > 0 and (self.hit_crates(box) or self.hit_secrets(box)):   # 远程武器也能打碎
                pr['life'] = 0
                continue
            for e in self.enemies:
                if e['alive'] and rects_overlap(box, e):
                    self.damage_enemy(e, pr['dmg'], 1 if pr['vx'] > 0 else -1,
                                      heavy=pr.get('heavy', False), elem=pr.get('elem', 'phys'))
                    pr['life'] = 0
                    break
        self.projectiles = [pr for pr in self.projectiles
                            if pr['life'] > 0 and -50 < pr['x'] < self.mapW + 50]

        p = self.player
        for pr in self.enemyProj:
            pr['x'] += pr['vx']
            pr['y'] += pr['vy']
            pr['life'] -= 1
            if pr.get('grav'):                       # 抛物线箭：受重力，落地消失
                pr['vy'] += pr['grav']
                if has_ground_at(self.platforms, pr['x'], pr['y']):
                    pr['life'] = 0
            if pr['kind'] == 'fireball':
                self.add_particles(pr['x'], pr['y'], 1, '#ff4020', 1.5)
            box = {'x': pr['x'] - pr['w'] / 2, 'y': pr['y'] - pr['h'] / 2, 'w': pr['w'], 'h': pr['h']}
            if p['hurtCD'] <= 0 and rects_overlap(box, p):
                self.damage_player(pr['dmg'], pr['x'], elem=pr.get('elem', 'phys'))
                pr['life'] = 0
        self.enemyProj = [pr for pr in self.enemyProj
                          if pr['life'] > 0 and -60 < pr['x'] < self.mapW + 60 and -60 < pr['y'] < H + 60]

    def update_pickups(self):
        p = self.player
        pcx, pcy = p['x'] + p['w'] / 2, p['y'] + p['h'] / 2
        for c in self.coins:
            c['t'] += 1
            dx, dy = pcx - c['x'], pcy - c['y']
            dist = math.hypot(dx, dy) or 1
            if c['t'] > 20 and dist < 90:        # 靠近时被吸向玩家
                c['x'] += dx / dist * 4
                c['y'] += dy / dist * 4
            else:
                prev_y = c['y']
                c['vy'] = min(8, c['vy'] + 0.3)
                c['x'] += c['vx']
                c['y'] += c['vy']
                for pl in self.platforms:
                    if pl['x'] <= c['x'] <= pl['x'] + pl['w'] and prev_y <= pl['y'] <= c['y'] + 6:
                        c['y'], c['vy'], c['vx'] = pl['y'] - 6, 0, c['vx'] * 0.5
            if abs(dx) < 24 and abs(dy) < 30:
                self.collect(c)
                c['dead'] = True
            elif c['t'] > 900 or c['y'] > H + 50:
                c['dead'] = True
        self.coins = [c for c in self.coins if not c.get('dead')]

    def collect(self, c):
        p = self.player
        if c['kind'] == 'heart':
            p['hp'] = min(p['maxHp'], p['hp'] + c['amt'])
            self.add_text(c['x'], c['y'] - 6, '+%d HP' % c['amt'], '#60ff60', 13)
        else:
            p['gold'] += c['amt']
            self.game['goldEarned'] += c['amt']
            self.add_text(c['x'], c['y'] - 6, '+%d' % c['amt'], '#ffd84a', 12)

    # ============== 互动：宝箱 / 铁匠 / 传送门 ==============
    def remaining_enemies(self):
        return sum(1 for e in self.enemies if e['alive'])

    def near_portal(self, reach):
        if self.portalX is None:
            return False
        return abs(self.player['x'] + self.player['w'] / 2 - self.portalX) < reach

    def interact_target(self):
        p = self.player
        pcx = p['x'] + p['w'] / 2
        probe = {'x': p['x'] - 8, 'y': p['y'] - 8, 'w': p['w'] + 16, 'h': p['h'] + 16}
        for c in self.chests:
            if not c['opened'] and rects_overlap(probe, c):
                return ('chest', c)
        if self.near_back():
            return ('back', None)
        door = self.near_secret_door()
        if door:
            return ('secret', door)
        # 地洞需要 S + E：站在洞口上方时才算（避免普通的 E 误入）
        hole = self.near_hole()
        if hole and self.prev['down']:
            return ('hole', hole)
        if self.smithX is not None and abs(pcx - self.smithX) < 70:
            return ('smith', None)
        if self.near_portal(55):
            return ('portal', None)
        return None

    def do_interact(self):
        t = self.interact_target()
        if not t:
            return
        kind = t[0]
        if kind == 'chest':
            self.open_chest(t[1])
        elif kind == 'smith':
            self.game.update(panel='shop', panelTab=0, panelIdx=0)
        elif kind == 'hole':
            self.game['holesEntered'] += 1
            self.enter_sub(t[1]['to'], 'dive')
        elif kind == 'secret':
            self.game['secretRooms'] = self.game.get('secretRooms', 0) + 1
            self.enter_sub('secret_%s_%d' % (self.game['state'], t[1]['idx']), 'door')
        elif kind == 'back':
            self.leave_sub()
        else:
            self.start_transition()

    def check_portal(self):
        """清完全部敌人后，走进传送门就会自动进入下一关；还有敌人时需要按 E 强行进入。"""
        if not self.trans and self.remaining_enemies() == 0 and self.near_portal(28) \
                and self.game['state'] != 'dead':
            self.start_transition()

    def start_transition(self, to=None, kind='next'):
        """kind: next 前进到下一主线关 / dive 进入地洞 / door 进入隐藏房间 / back 返回上层。"""
        cur = self.game['state']
        if to is None:
            if cur not in LEVEL_ORDER or LEVEL_ORDER.index(cur) + 1 >= len(LEVEL_ORDER):
                return
            to = LEVEL_ORDER[LEVEL_ORDER.index(cur) + 1]
        self.trans = {'t': 0, 'from': cur, 'to': to, 'kind': kind,
                      'clear': kind == 'next' and self.remaining_enemies() == 0}

    def open_chest(self, c):
        c['opened'] = True
        p = self.player
        self.add_particles(c['x'] + c['w'] / 2, c['y'] + c['h'] / 2, 25, '#ffd84a', 4)
        kind, val = c['give']
        if kind == 'gold':
            p['gold'] += val
            self.game['goldEarned'] += val
            self.show_msg('获得 %d 金币' % val, 80)
        elif kind == 'weapon':
            if val in p['ownedWeapons']:
                p['gold'] += 30
                self.show_msg('已有 %s，换成 30 金币' % WEAPONS[val]['name'], 90)
            else:
                p['ownedWeapons'].add(val)
                better = weapon_power(val) > weapon_power(p['weapon'])
                if better:
                    p['weapon'] = val
                self.show_msg('获得武器：%s（%s）' % (WEAPONS[val]['name'], '已装备' if better else '已放入背包'), 110)
        else:
            if val in p['ownedArmors']:
                p['gold'] += 30
                self.show_msg('已有 %s，换成 30 金币' % ARMORS[val]['name'], 90)
            else:
                p['ownedArmors'].add(val)
                better = ARMORS[val]['reduce'] > ARMORS[p['armor']]['reduce']
                if better:
                    p['armor'] = val
                self.show_msg('获得盔甲：%s（%s）' % (ARMORS[val]['name'], '已装备' if better else '已放入背包'), 110)

    # ============== 关卡切换 ==============
    def advance_transition(self):
        t = self.trans
        g = self.game
        t['t'] += 1
        if t['t'] == 30:
            self.finish_transition()
        if t['t'] >= 60:
            self.trans = None
            g['fade'] = 0.0
        else:
            g['fade'] = t['t'] / 30.0 if t['t'] <= 30 else (60 - t['t']) / 30.0

    def finish_transition(self):
        t, p = self.trans, self.player
        kind = t['kind']
        if kind == 'back':
            # 返回地面：恢复进入前的关卡状态（宝箱开没开、怪物死没死、木箱碎没碎都保留）
            saved = self.return_stack.pop()
            self.load(saved['level'], spawn_x=saved['x'])
            self.chests, self.enemies, self.crates = saved['chests'], saved['enemies'], saved['crates']
            self.secrets, self.hazards, self.holes = saved['secrets'], saved['hazards'], saved['holes']
            self.enemies_total = max(self.enemies_total, len([e for e in self.enemies if e['alive']]))
            self.game['introT'] = 0
            return
        self.load(t['to'])
        if kind in ('dive', 'door'):
            self.game['introT'] = 160
            return
        p['hp'] = min(p['maxHp'], p['hp'] + int(p['maxHp'] * 0.3))
        if t['clear']:
            bonus = LEVEL_CLEAR_EXP[t['from']]
            self.gain_exp(bonus)
            self.show_msg('全部敌人已清除，额外经验 +%d' % bonus, 130)

    # ============== 面板：商店 / 背包 / 战绩 ==============
    def open_panel(self, name):
        g, p = self.game, self.player
        g['panel'], g['panelTab'], g['panelIdx'] = name, 0, 0
        if name == 'inv':
            g['panelIdx'] = self.owned_list(0).index(p['weapon'])

    def owned_list(self, tab):
        p = self.player
        return sorted(p['ownedWeapons'] if tab == 0 else p['ownedArmors'])

    def tick_panel(self, edge):
        g = self.game
        panel = g['panel']
        if edge['escape'] or (panel == 'shop' and edge['interact']):
            g['panel'] = None
            return
        if panel in ('inv', 'stats'):
            if edge['inv']:
                if panel == 'inv':
                    g['panel'] = None
                else:
                    self.open_panel('inv')
                return
            if edge['stats']:
                if panel == 'stats':
                    g['panel'] = None
                else:
                    self.open_panel('stats')
                return
        if panel == 'stats':
            return

        if edge['left'] or edge['right']:
            g['panelTab'] = 0 if edge['left'] else 1
            g['panelIdx'] = 0
        if panel == 'shop':
            n = len(WEAPONS) if g['panelTab'] == 0 else len(ARMORS)
        else:
            n = len(self.owned_list(g['panelTab']))
        if edge['up']:
            g['panelIdx'] = max(0, g['panelIdx'] - 1)
        if edge['down']:
            g['panelIdx'] = min(n - 1, g['panelIdx'] + 1)
        if edge['confirm'] or edge['attack']:
            if panel == 'shop':
                self.buy_item(g['panelTab'], g['panelIdx'])
            else:
                self.equip(g['panelTab'], self.owned_list(g['panelTab'])[g['panelIdx']])

    def equip(self, tab, idx):
        p = self.player
        if tab == 0:
            p['weapon'] = idx
            self.show_msg('已装备 ' + WEAPONS[idx]['name'], 60)
        else:
            p['armor'] = idx
            self.show_msg('已装备 ' + ARMORS[idx]['name'], 60)

    def buy_item(self, tab, idx):
        p = self.player
        table, owned = (WEAPONS, p['ownedWeapons']) if tab == 0 else (ARMORS, p['ownedArmors'])
        item = table[idx]
        if idx in owned:
            self.equip(tab, idx)
        elif p['gold'] >= item['price']:
            p['gold'] -= item['price']
            owned.add(idx)
            self.equip(tab, idx)
            self.show_msg('购买并装备 ' + item['name'], 80)
            self.add_particles(p['x'] + p['w'] / 2, p['y'], 15, item['color'], 3)
        else:
            self.show_msg('金币不足，还差 %d' % (item['price'] - p['gold']), 70)

    # ============== 粒子 / 飘字 ==============
    def update_particles(self):
        for q in self.particles:
            q['x'] += q['vx']
            q['y'] += q['vy']
            q['vy'] += 0.15
            q['life'] -= 1
        self.particles = [q for q in self.particles if q['life'] > 0]
        self.update_fx()
        for t in self.texts:
            t['y'] += t['vy']
            t['t'] -= 1
        self.texts = [t for t in self.texts if t['t'] > 0]

    # ============== 状态序列化 ==============
    def level_message(self):
        """关卡内不会变化的数据，只在换关时发送一次。"""
        # 移动平台的位置每帧都在变，放在 state 里；这里的 platforms 只给静态的
        static = [pl for pl in self.platforms if not pl.get('mover')]
        return {'t': 'level', 'seq': self.level_seq, 'mapW': self.mapW,
                'platforms': static, 'smithX': self.smithX, 'portal': self.portal,
                'hazards': self.hazards, 'backX': self.backX, 'theme': self.game['theme'],
                'catalog': CATALOG}

    def prompt(self):
        g = self.game
        if g['panel'] or self.trans or g['state'] in ('menu', 'dead', 'win'):
            return None
        p = self.player
        pcx = p['x'] + p['w'] / 2
        # 地洞和隐藏墙即使没满足触发条件，也要在附近给出提示，否则玩家不知道有这个机制
        t = self.interact_target()
        if t is None:
            hole = self.near_hole()
            if hole:
                return {'x': hole['x'], 'y': GROUND_Y - 60, 'text': '按住 S 再按 E 进入地洞'}
            for s in self.secrets:
                if not s['open'] and abs(pcx - s['x']) < 70:
                    return {'x': s['x'], 'y': GROUND_Y - 110, 'text': '这面墙有裂缝…攻击它试试'}
            return None
        kind = t[0]
        if kind == 'chest':
            c = t[1]
            return {'x': c['x'] + c['w'] / 2, 'y': c['y'] - 14, 'text': '按 E 开启宝箱'}
        if kind == 'smith':
            return {'x': self.smithX, 'y': 322, 'text': '按 E 进入铁匠铺'}
        if kind == 'hole':
            return {'x': t[1]['x'], 'y': GROUND_Y - 60, 'text': '按 E 进入地洞'}
        if kind == 'secret':
            return {'x': t[1]['x'], 'y': GROUND_Y - 110, 'text': '按 E 进入隐藏房间'}
        if kind == 'back':
            return {'x': self.backX, 'y': GROUND_Y - 110, 'text': '按 E 返回地面'}
        left = self.remaining_enemies()
        text = '进入下一关' if left == 0 else '还有 %d 只敌人，按 E 强行进入' % left
        return {'x': self.portalX, 'y': GROUND_Y - PORTAL_H - 26, 'text': text}

    def get_state(self):
        g, p = self.game, self.player
        boss = next((e for e in self.enemies if e['boss'] and e['alive']), None)
        return {
            't': 'state',
            'seq': self.level_seq,
            'game': {
                'state': g['state'], 'level': g['level'], 'levelName': self.level_title(),
                'camX': r1(g['camX']), 'time': g['time'], 'playTime': g['playTime'],
                'msg': g['msg'], 'msgT': g['msgT'], 'introT': g['introT'],
                'title': g['title'], 'hint': g['hint'],
                'flash': g['flash'], 'shake': r1(g['shake']), 'fade': r1(g['fade']),
                'hitstop': g['hitstop'], 'hurtFlash': g['hurtFlash'],
                'panel': g['panel'], 'panelTab': g['panelTab'], 'panelIdx': g['panelIdx'],
                'deadReason': g['deadReason'], 'endT': g['endT'],
                'kills': g['kills'], 'totalDamage': g['totalDamage'], 'goldEarned': g['goldEarned'],
                'enemiesLeft': self.remaining_enemies(), 'enemiesTotal': self.enemies_total,
                'theme': g['theme'], 'mode': g['mode'], 'menuIdx': g['menuIdx'],
                'wave': g['wave'], 'waveBreak': g['waveBreak'], 'bestWave': g['bestWave'],
                'depth': len(self.return_stack), 'inPoison': self.player['inPoison'],
                'crates': g['crates'], 'secretsFound': g['secretsFound'],
            },
            'player': {
                'x': r1(p['x']), 'y': r1(p['y']), 'w': p['w'], 'h': p['h'],
                'vx': r1(p['vx']), 'vy': r1(p['vy']), 'onGround': p['onGround'], 'facing': p['facing'],
                'hp': p['hp'], 'maxHp': p['maxHp'], 'level': p['level'],
                'exp': p['exp'], 'expNext': p['expNext'], 'gold': p['gold'],
                'weapon': p['weapon'], 'armor': p['armor'],
                'hurtCD': p['hurtCD'], 'attackAnim': p['attackAnim'], 'atkCD': p['atkCD'],
                'aim': self.aim_angle(),
                'fallDanger': self.fall_distance() > SAFE_FALL,     # 已经落得够高，落地会受伤
                'ownedWeapons': sorted(p['ownedWeapons']), 'ownedArmors': sorted(p['ownedArmors']),
            },
            'enemies': [{
                'type': e['type'], 'x': r1(e['x']), 'y': r1(e['y']), 'w': e['w'], 'h': e['h'],
                'hp': e['hp'], 'maxHp': e['maxHp'], 'dir': e['dir'], 'color': e['color'],
                'hurtT': e['hurtT'], 'alive': e['alive'], 'dying': e['dying'],
                'mode': e['mode'], 'modeT': e['modeT'], 'boss': e['boss'], 'fly': e['fly'],
                'burn': e['burn'], 'slow': e['slow'], 'weak': e['weak'],
            } for e in self.enemies],
            'card': None if not self.card else {'type': self.card['type'], 't': self.card['t'],
                                                'total': CARD_FRAMES},
            'boss': None if not boss else {
                'hp': boss['hp'], 'maxHp': boss['maxHp'], 'mode': boss['mode'],
                'enraged': boss['hp'] < boss['maxHp'] * 0.5},
            'projectiles': [{'x': r1(q['x']), 'y': r1(q['y']), 'vx': r1(q['vx']), 'vy': r1(q['vy']),
                             'kind': q['kind'], 'color': q['color']} for q in self.projectiles],
            'enemyProj': [{'x': r1(q['x']), 'y': r1(q['y']), 'w': q['w'], 'h': q['h'],
                           'vx': r1(q['vx']), 'vy': r1(q['vy']), 'kind': q['kind'], 'color': q['color']}
                          for q in self.enemyProj],
            'particles': [[r1(q['x']), r1(q['y']), q['size'], int(q['life']), q['color']]
                          for q in self.particles],
            'coins': [{'x': r1(c['x']), 'y': r1(c['y']), 'kind': c['kind'], 't': c['t']} for c in self.coins],
            'chests': [{'x': c['x'], 'y': c['y'], 'w': c['w'], 'h': c['h'], 'opened': c['opened']}
                       for c in self.chests],
            'movers': [{'x': r1(m['plat']['x']), 'y': m['plat']['y'], 'w': m['plat']['w'], 'h': m['plat']['h']}
                       for m in self.movers],
            'crates': [{'x': c['x'], 'y': c['y'], 'w': c['w'], 'h': c['h'], 'hp': c['hp']}
                       for c in self.crates if c['hp'] > 0],
            'holes': [{'x': h['x']} for h in self.holes],
            'secrets': [{'x': s['x'], 'hp': s['hp'], 'maxHp': s['maxHp'], 'open': s['open']}
                        for s in self.secrets],
            'texts': [{'x': r1(t['x']), 'y': r1(t['y']), 'txt': t['txt'], 'color': t['color'],
                       'size': t['size'], 't': t['t']} for t in self.texts],
            'fx': self.fx,
            'prompt': self.prompt(),
        }
