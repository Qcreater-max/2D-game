"""生成《像素勇士:暗影征途》演示文稿。

用法: python build_ppt.py
截图放在 shots/ 目录下(见 SHOT_NAMES),缺失的图会显示占位框,补图后重新运行即可。
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, 'shots')
OUT = os.path.join(HERE, '像素勇士_暗影征途.pptx')
FONT = 'Microsoft YaHei'
BG, PANEL = RGBColor(0x0b, 0x0b, 0x16), RGBColor(0x1a, 0x1a, 0x2e)
GOLD, TEXT, DIM = RGBColor(0xff, 0xd8, 0x4a), RGBColor(0xe8, 0xe8, 0xff), RGBColor(0x90, 0x90, 0xb8)
RED, BLUE, GREEN, PURPLE = (RGBColor(0xff, 0x7a, 0x30), RGBColor(0x7a, 0xd8, 0xff),
                            RGBColor(0x60, 0xd0, 0x60), RGBColor(0xc0, 0x40, 0xff))

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)


def tb(slide, x, y, w, h, lines, size=18, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
       anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    for i, ln in enumerate([lines] if isinstance(lines, str) else lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.space_after = align, Pt(6)
        r = p.add_run()
        r.text = ln
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, FONT
    return box


def rect(slide, x, y, w, h, fill=PANEL, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.06
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb, s.line.width = line, Pt(1.5)
    s.shadow.inherit = False
    return s


def new_slide(title, sub=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    rect(s, 0.6, 0.55, 0.12, 0.7, fill=GOLD)
    tb(s, 0.9, 0.4, 11.5, 0.8, title, size=34, color=GOLD, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if sub:
        tb(s, 0.9, 1.1, 11.5, 0.5, sub, size=16, color=DIM)
    return s


def shot(slide, name, x, y, w, h, caption=None):
    """放一张截图;文件不存在就画占位框,提示该放什么文件。"""
    path = os.path.join(SHOTS, name)
    if os.path.exists(path):
        slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    else:
        rect(slide, x, y, w, h, fill=RGBColor(0x14, 0x14, 0x24), line=DIM)
        tb(slide, x, y, w, h, ['[ 截图占位 ]', 'shots/' + name], size=14, color=DIM,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if caption:
        tb(slide, x, y + h + 0.05, w, 0.4, caption, size=12, color=DIM, align=PP_ALIGN.CENTER)


def card(slide, x, y, w, h, head, body, accent=GOLD, size=14):
    rect(slide, x, y, w, h)
    rect(slide, x, y, 0.08, h, fill=accent)
    tb(slide, x + 0.25, y + 0.12, w - 0.4, 0.5, head, size=17, color=accent, bold=True)
    tb(slide, x + 0.25, y + 0.62, w - 0.4, h - 0.7, body, size=size)


# ---------- 1 封面 ----------
s = prs.slides.add_slide(prs.slide_layouts[6])
s.background.fill.solid()
s.background.fill.fore_color.rgb = BG
shot(s, '01_menu.png', 6.9, 1.6, 5.8, 3.26)
tb(s, 0.8, 1.7, 6, 1.2, '像素勇士', size=60, color=GOLD, bold=True)
tb(s, 0.8, 2.9, 6, 0.8, '暗影征途', size=36, color=TEXT, bold=True)
tb(s, 0.8, 3.9, 6, 1.2, ['一个运行在浏览器里的', '服务端权威 2D 像素动作游戏'], size=18, color=DIM)
tb(s, 0.8, 6.3, 8, 0.5, 'Python · WebSocket · HTML5 Canvas · AI 辅助开发', size=14, color=DIM)

# ---------- 2 游戏构思 ----------
s = new_slide('游戏构思', '做一款上手快、有策略深度、打开浏览器就能玩的动作游戏')
card(s, 0.6, 1.9, 4.0, 4.6, '设计目标', [
    '· 零安装:浏览器打开即玩',
    '· 手感优先:命中停顿、震屏、',
    '  跳跃缓冲,打击有重量',
    '· 策略而非数值堆叠:',
    '  元素克制决定怎么打',
    '· 一局之内有探索、有惊喜',
], GOLD)
card(s, 4.8, 1.9, 4.0, 4.6, '玩法骨架', [
    '· 冒险模式:5 个主线关 + 首领',
    '· 无尽模式:一波接一波,',
    '  比谁撑得久',
    '· 地洞与隐藏房间:',
    '  偏离主线的奖励',
    '· 铁匠铺:金币换装备,',
    '  形成成长循环',
], BLUE)
card(s, 9.0, 1.9, 3.8, 4.6, '内容规模', [
    '· 8 种武器 · 6 种盔甲',
    '· 9 种敌人(含首领)',
    '· 4 种元素 · 3 种危险物',
    '· 2 个地下关 + 动态隐藏房间',
    '· 约 150 个自动化测试',
], GREEN)

# ---------- 3 核心玩法 ----------
s = new_slide('核心玩法', '移动、攻击、元素克制,三件事构成每一场战斗')
shot(s, '02_combat.png', 0.6, 1.8, 7.4, 4.16, '战斗画面:多种敌人同时出现,左上角为敌人资料卡片')
card(s, 8.3, 1.8, 4.4, 1.55, '操作', [
    'A/D 移动  W/空格 跳跃  J/左键 攻击',
    'E 互动  I 背包  Tab 战绩',
], GOLD, 13)
card(s, 8.3, 3.5, 4.4, 1.55, '鼠标瞄准', [
    '远程武器按住左键,朝鼠标方向发射,',
    '角色同时转向鼠标一侧',
], BLUE, 13)
card(s, 8.3, 5.2, 4.4, 1.55, '成长', [
    '击杀得经验与金币 → 升级加生命与攻击',
    '→ 铁匠铺买装备 → 挑战更强的关卡',
], GREEN, 13)

# ---------- 4 元素与敌人 ----------
s = new_slide('元素克制与敌人设计', '每种敌人都要求不同的打法,而不是更高的数字')
rows = [
    ('火', RED, '灼烧 3 秒,持续掉血', '史莱姆、骷髅、蝙蝠怕火'),
    ('冰', BLUE, '减速 2 秒,首领免疫', '弓手、自爆虫、野猪怕冰'),
    ('雷', RGBColor(0xff, 0xe0, 0x40), '电弧跳向附近敌人,无视格挡', '哥布林、盾卫怕雷'),
]
for i, (n, c, eff, weak) in enumerate(rows):
    y = 1.9 + i * 1.05
    rect(s, 0.6, y, 6.2, 0.9)
    rect(s, 0.6, y, 0.9, 0.9, fill=c)
    tb(s, 0.6, y, 0.9, 0.9, n, size=28, color=BG, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, 1.65, y + 0.06, 5.1, 0.4, eff, size=15, bold=True, color=c)
    tb(s, 1.65, y + 0.47, 5.1, 0.4, weak, size=13, color=DIM)
card(s, 0.6, 5.15, 6.2, 1.6, '伤害公式', [
    '元素倍率(弱点 ×1.5 / 抗性 ×0.5) → 暴击 ×2 → 眩晕 ×1.5',
    '→ 减去防御,但不低于 30%',
], GOLD, 13)
card(s, 7.1, 1.9, 5.6, 4.85, '有行为的敌人', [
    '盾卫:正面挡普通攻击,需绕背、重击或用雷',
    '自爆虫:靠近点引信,被击杀也会爆,可连锁',
    '野猪:蓄力直线冲撞,撞墙眩晕,此时受伤加成',
    '弓手:保持距离抛物线射箭,被贴近会后撤',
    '骷髅:远距离投骨,压迫走位',
    '蝙蝠:盘旋后俯冲,带冰元素',
    '',
    '同一个房间里混合出现,玩家需要实时判断',
    '先处理谁、用哪把武器。',
], PURPLE, 14)

# ---------- 5 高光片段 ----------
s = new_slide('高光片段', '游戏里最有代表性的几个瞬间')
cells = [
    ('03_lava.png', '熔岩洞窟:移动平台带着你跨越岩浆'),
    ('04_swamp.png', '幽暗沼泽:毒沼与野猪冲锋'),
    ('05_secret.png', '裂墙:攻击后露出隐藏房间入口'),
    ('06_boss.png', '暗影巫师:砸地后的硬直是输出窗口'),
]
for i, (f, cap) in enumerate(cells):
    x, y = 1.2 + (i % 2) * 5.9, 1.75 + (i // 2) * 2.95
    shot(s, f, x, y, 4.4, 2.475, cap)     # 16:9

# ---------- 6 探索与惊喜 ----------
s = new_slide('探索与惊喜', '主线之外,给愿意多看一眼的玩家额外奖励')
shot(s, '07_cave.png', 0.6, 1.8, 6.0, 3.38, '地洞:按住 S 再按 E 进入地下子关卡')
card(s, 6.9, 1.8, 5.8, 1.5, '地洞与子关卡', [
    '进入时把当前关卡压栈,返回后宝箱、怪物、',
    '木箱状态全部保留,不会刷新重来',
], BLUE, 13)
card(s, 6.9, 3.45, 5.8, 1.5, '可疑裂墙', [
    '攻击数次后破开,进入隐藏房间,',
    '里面是一个稀有装备宝箱',
], GOLD, 13)
card(s, 6.9, 5.1, 5.8, 1.5, '木箱与危险物', [
    '木箱掉金币或回血;尖刺、岩浆、毒沼',
    '考验走位,熔岩甲能让岩浆变成优势',
], GREEN, 13)
tb(s, 0.6, 5.5, 6.0, 1.2, ['游戏提示会在玩家靠近时出现,', '不需要读说明书也能发现这些机制。'],
   size=14, color=DIM)

# ---------- 7 无尽模式 ----------
s = new_slide('无尽模式', '一屏宽的竞技场,敌人从两侧涌入')
shot(s, '08_endless.png', 0.6, 1.8, 7.0, 3.94, '竞技场:中央有铁匠铺,可以随时补给')
card(s, 7.9, 1.8, 4.8, 4.5, '波次规则', [
    '· 每波数量 = min(14, 3 + 波数 × 2)',
    '· 第 2 波加入弓手、自爆虫',
    '· 第 4 波加入野猪、骷髅',
    '· 第 6 波加入盾卫、蝙蝠',
    '· 每波生命 +12%,金币 +5%',
    '· 清波奖励金币并回复 25% 生命',
    '· 死亡即结束,记录最高波数',
], PURPLE, 15)

# ---------- 8 技术架构 ----------
s = new_slide('技术架构:服务端权威', '所有规则在 Python 后端,浏览器只负责采集按键和绘制')
rect(s, 0.6, 1.9, 3.6, 2.2, line=BLUE)
tb(s, 0.6, 2.0, 3.6, 0.5, '浏览器', size=20, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
tb(s, 0.8, 2.6, 3.2, 1.5, ['client.js 采集输入', 'render.js / ui.js 绘制', 'Canvas 960×540 像素风'],
   size=14, align=PP_ALIGN.CENTER)
rect(s, 9.1, 1.9, 3.6, 2.2, line=GOLD)
tb(s, 9.1, 2.0, 3.6, 0.5, 'Python 服务器', size=20, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
tb(s, 9.3, 2.6, 3.2, 1.5, ['每连接一个 GameEngine', '60 帧/秒固定循环', '物理 · 战斗 · AI · 关卡'],
   size=14, align=PP_ALIGN.CENTER)
tb(s, 4.2, 2.15, 4.9, 0.5, '按键 / 鼠标瞄准  →', size=15, color=TEXT, align=PP_ALIGN.CENTER)
tb(s, 4.2, 2.95, 4.9, 0.5, '←  每帧完整状态 (JSON)', size=15, color=TEXT, align=PP_ALIGN.CENTER)
tb(s, 4.2, 3.55, 4.9, 0.4, 'WebSocket  /ws', size=12, color=DIM, align=PP_ALIGN.CENTER)
card(s, 0.6, 4.4, 4.0, 2.3, '为什么服务端权威', [
    '客户端只上报"按了什么键",',
    '无法改伤害、速度、血量,',
    '从架构上杜绝作弊。',
], GOLD, 14)
card(s, 4.75, 4.4, 4.0, 2.3, '引擎 = 4 个 Mixin', [
    'combat 战斗 · enemies 敌人 AI',
    'boss 首领 · world 世界机制',
    '数值全部集中在 game_data.py',
], BLUE, 14)
card(s, 8.9, 4.4, 3.8, 2.3, '前端零框架', [
    '纯 Canvas,无构建步骤。',
    '武器 / 盔甲 / 图鉴由服务器',
    '下发,前端不重复维护。',
], GREEN, 14)

# ---------- 9 技术难点 (1) ----------
s = new_slide('技术难点(1):手感', '"能玩"和"好玩"之间,差的是这些细节')
card(s, 0.6, 1.8, 6.0, 2.4, '服务端算输入边沿', [
    '菜单、背包这类"按一下"的操作,由服务端',
    '对比上一帧自己判断"刚按下",客户端不用',
    '定时发脉冲,避免重复触发和丢键。',
], GOLD, 14)
card(s, 6.8, 1.8, 5.9, 2.4, '跳跃宽容度', [
    '起跳前 6 帧的输入缓冲 + 离地后 6 帧',
    '的宽限(coyote time),松开按键可提前',
    '结束上升来控制跳跃高度。',
], BLUE, 14)
card(s, 0.6, 4.4, 6.0, 2.35, '命中停顿不吞输入', [
    '命中时世界暂停几帧让打击有重量,',
    '但暂停期间刚按下的跳跃会被缓存,',
    '不会因为停顿而"吃键"。',
], GREEN, 14)
card(s, 6.8, 4.4, 5.9, 2.35, '摔伤按"落差"算', [
    '记录离地后到达的最高点,而不是下落时间。',
    '起跳再落回原地不算摔伤;摔伤不致死,',
    '换关传送时重置,避免带着旧落差落地。',
], PURPLE, 14)

# ---------- 10 技术难点 (2) ----------
s = new_slide('技术难点(2):关卡与状态', '让规则在复杂场景下依然自洽')
card(s, 0.6, 1.8, 6.0, 2.4, '关卡栈与状态保留', [
    '进地洞、隐藏房间前把当前关卡压栈,',
    '返回时恢复宝箱、怪物、木箱状态。',
    '子关卡内死亡则清空栈,回到主线关卡。',
], GOLD, 14)
card(s, 6.8, 1.8, 5.9, 2.4, '关卡可达性自动检查', [
    '平台间距按跳跃上限设计(最高约 124,',
    '水平约 115 像素),关卡测试自动验证',
    '平台间距与宝箱位置都在能力范围内。',
], BLUE, 14)
card(s, 0.6, 4.4, 6.0, 2.35, '移动平台带人', [
    '平台沿 x 做正弦摆动,记录每帧位移,',
    '站在上面的玩家被同步带走,',
    '落脚状态每帧重新判定。',
], GREEN, 14)
card(s, 6.8, 4.4, 5.9, 2.35, '静态与动态数据分离', [
    '地形等静态数据只在换关时发一次,',
    '每帧只发变化的内容;带关卡序号 seq,',
    '不一致时客户端自动请求重发。',
], PURPLE, 14)

# ---------- 11 技术难点 (3) ----------
s = new_slide('技术难点(3):从单机到公开可用', '把一个本地玩具变成能放上互联网的服务')
card(s, 0.6, 1.8, 6.0, 2.4, '从共享一局到各玩各的', [
    '原先所有连接的按键合并后控制同一个角色,',
    '公开后陌生人会互相干扰。改为每个连接',
    '一个独立 GameEngine,出错只断开该玩家。',
], GOLD, 14)
card(s, 6.8, 1.8, 5.9, 2.4, '防滥用', [
    '在线人数与单 IP 连接数上限、消息 1KB 上限、',
    '令牌桶限流(每秒 120 条)、慢客户端丢帧、',
    '可选 Origin 白名单。',
], BLUE, 14)
card(s, 0.6, 4.4, 6.0, 2.35, '输入校验', [
    '瞄准坐标拒绝 NaN、Infinity、超大整数;',
    '弹速由服务端按武器决定,',
    '客户端无法通过伪造向量加速子弹。',
], GREEN, 14)
card(s, 6.8, 4.4, 5.9, 2.35, '单端口 + 反向代理', [
    'HTTP 与 WebSocket 合并到同一端口(/ws),',
    '放在 Caddy 之后自动 HTTPS;静态文件白名单,',
    '源码和 .git 不会暴露。',
], PURPLE, 14)

# ---------- 12 AI 辅助过程 ----------
s = new_slide('AI 辅助开发过程', '以"让游戏能公开访问"这一轮为例,展示人与 AI 如何协作')
steps = [
    ('1', '读懂项目', '先通读后端、前端、数据与关卡,\n再给出架构概览,而不是直接动手', GOLD),
    ('2', '指出风险', '发现"所有人共用一局"和"无防护",\n先说明问题再让用户选方案', RED),
    ('3', '实现', '重写服务器为单端口 + 每人一局,\n加限流与人数上限,配套部署脚本', BLUE),
    ('4', '验证', '安装 Python 跑 150 个测试,\n用真实 WebSocket 连接做冒烟测试', GREEN),
    ('5', '文档与交付', '生成 README、部署配置,\n提交到新分支并推送', PURPLE),
]
for i, (n, h, b, c) in enumerate(steps):
    x = 0.6 + i * 2.5
    rect(s, x, 1.9, 2.3, 3.0)
    rect(s, x, 1.9, 2.3, 0.1, fill=c)
    tb(s, x, 2.05, 2.3, 0.7, n, size=30, color=c, bold=True, align=PP_ALIGN.CENTER)
    tb(s, x, 2.75, 2.3, 0.5, h, size=17, color=TEXT, bold=True, align=PP_ALIGN.CENTER)
    tb(s, x + 0.12, 3.3, 2.06, 1.6, b.split('\n'), size=12, color=DIM, align=PP_ALIGN.CENTER)
card(s, 0.6, 5.15, 6.0, 1.6, 'AI 做对的地方', [
    '· 先读代码再下结论,改动前先问用户选型',
    '· 用测试和真实连接验证,而不是只写不跑',
], GREEN, 13)
card(s, 6.8, 5.15, 5.9, 1.6, '人把关的地方', [
    '· 公开方式、是否每人独立一局由用户决定',
    '· 联网、安装软件等操作需要用户授权',
], GOLD, 13)

# ---------- 13 AI 协作的真实经验 ----------
s = new_slide('AI 协作中的真实经验', '过程并不总是一帆风顺,这些才是有价值的部分')
card(s, 0.6, 1.8, 6.0, 2.4, '测试发现了 AI 自己的错', [
    '新写的会话测试第一次跑有 3 个失败,',
    '原因是测试里假时钟没对齐,不是服务器问题。',
    '有测试兜底,错误当场暴露而不是上线后。',
], GOLD, 14)
card(s, 6.8, 1.8, 5.9, 2.4, '先分清"我的问题"和"原有问题"', [
    '一个关卡测试一直失败,AI 用 git stash 回到',
    '原始代码重跑,确认它改动前就失败,',
    '没有把它算在自己头上,也没有悄悄掩盖。',
], BLUE, 14)
card(s, 0.6, 4.4, 6.0, 2.35, '验证要验对地方', [
    '第一次"独立会话"冒烟测试读到的是队列里的',
    '旧状态帧,结论不可信。AI 发现后改为读取',
    '最新帧再测,才确认两个玩家互不影响。',
], GREEN, 14)
card(s, 6.8, 4.4, 5.9, 2.35, '如实报告没验证的部分', [
    '没开浏览器看画面、没压测并发、没在真实',
    '服务器上跑部署脚本:这些都明确写进了',
    '总结和 README,而不是含糊带过。',
], PURPLE, 14)

# ---------- 14 创新点 ----------
s = new_slide('创新点')
items = [
    ('服务端权威的浏览器动作游戏', '零安装、不可作弊,前端只有渲染,规则完全在后端', GOLD),
    ('元素克制 × 敌人行为', '弱点、抗性、格挡、眩晕叠加,同屏混合敌人逼玩家实时决策', RED),
    ('可保留状态的多层探索', '地洞与隐藏房间用关卡栈实现,返回后世界状态原样保留', BLUE),
    ('自动化保证关卡可玩', '用测试校验平台间距与跳跃能力,改关卡数值时自动报警', GREEN),
    ('数据驱动的内容扩展', '关卡、武器、敌人都是声明式数据,图鉴由服务器下发给前端', PURPLE),
    ('AI 全程参与并可验证', '读码、实现、测试、文档、提交一条龙,每一步都有可复查的产物', GOLD),
]
for i, (h, b, c) in enumerate(items):
    x, y = 0.6 + (i % 2) * 6.2, 1.6 + (i // 2) * 1.75
    rect(s, x, y, 6.0, 1.55)
    rect(s, x, y, 0.08, 1.55, fill=c)
    tb(s, x + 0.25, y + 0.1, 5.6, 0.5, h, size=17, color=c, bold=True)
    tb(s, x + 0.25, y + 0.68, 5.6, 0.85, b, size=13)

# ---------- 15 总结 ----------
s = new_slide('总结与展望')
card(s, 0.6, 1.6, 6.0, 2.6, '已完成', [
    '· 6 个主线关卡 + 无尽模式 + 地下探索',
    '· 8 武器 / 6 盔甲 / 9 敌人 / 4 元素',
    '· 每人独立一局的公开服务,含防滥用',
    '· 完整 README、部署脚本、自动化测试',
], GREEN, 15)
card(s, 6.8, 1.6, 5.9, 2.6, '诚实的局限', [
    '· 有 1 个关卡测试原本就失败,尚未修复',
    '· 单机并发上限没有压测过',
    '· 部署脚本未在真实服务器上验证',
    '· 服务没有账号认证',
], RED, 15)
card(s, 0.6, 4.4, 12.1, 2.3, '下一步', [
    '· 修复落差过大的关卡平台        · 压测并发,调整人数上限',
    '· 增加账号与排行榜(无尽模式最高波数)        · 更多武器、关卡与敌人',
], GOLD, 15)
tb(s, 0.6, 6.85, 12, 0.4, '仓库:github.com/Qcreater-max/demo(分支 feature/public-deploy)', size=12, color=DIM)

prs.save(OUT)
print('已生成:', OUT)
missing = [f for f in ('01_menu', '02_combat', '03_lava', '04_swamp', '05_secret', '06_boss', '07_cave', '08_endless')
           if not os.path.exists(os.path.join(SHOTS, f + '.png'))]
print('缺少的截图:', ', '.join(f + '.png' for f in missing) if missing else '无')
