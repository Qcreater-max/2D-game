"""碰撞与移动：实心地面 + 可从下方跳上的单向平台。"""


def rects_overlap(a, b):
    return (a['x'] < b['x'] + b['w'] and a['x'] + a['w'] > b['x'] and
            a['y'] < b['y'] + b['h'] and a['y'] + a['h'] > b['y'])


def has_ground_at(platforms, px, py):
    """点 (px, py) 是否落在某个平台内，用于敌人的悬崖边缘检测。"""
    for pl in platforms:
        if pl['x'] <= px < pl['x'] + pl['w'] and pl['y'] <= py <= pl['y'] + pl['h']:
            return True
    return False


def in_solid(platforms, px, py):
    """点 (px, py) 是否落在实心地面里（单向平台不算，弹道可以从旁边穿过）。"""
    for pl in platforms:
        if pl['type'] == 'ground' and pl['x'] <= px <= pl['x'] + pl['w'] and pl['y'] <= py <= pl['y'] + pl['h']:
            return True
    return False


def move_body(b, platforms, drop=False):
    """按 b['vx'] / b['vy'] 移动并处理碰撞，返回落脚的平台（没落地则返回 None）。

    - type == 'ground'：四面实心
    - type == 'plat'：单向平台，只能从上方落上去，可从下方穿过；drop=True 时暂时穿过
    """
    b['x'] += b['vx']
    b['hitWall'] = False
    for pl in platforms:
        if pl['type'] == 'ground' and rects_overlap(b, pl):
            if b['vx'] > 0:
                b['x'] = pl['x'] - b['w']
            elif b['vx'] < 0:
                b['x'] = pl['x'] + pl['w']
            b['hitWall'] = True

    prev_bottom = b['y'] + b['h']
    b['y'] += b['vy']
    b['onGround'] = False
    landed = None
    for pl in platforms:
        if not rects_overlap(b, pl):
            continue
        if pl['type'] == 'ground':
            if b['vy'] > 0:
                b['y'] = pl['y'] - b['h']
                b['vy'] = 0
                b['onGround'] = True
                landed = pl
            elif b['vy'] < 0:
                b['y'] = pl['y'] + pl['h']
                b['vy'] = 0
        elif b['vy'] >= 0 and not drop and prev_bottom <= pl['y'] + 1:
            b['y'] = pl['y'] - b['h']
            b['vy'] = 0
            b['onGround'] = True
            landed = pl
    return landed
