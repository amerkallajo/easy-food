"""Scene dressing for the Easy Food model: props, wall / ceiling fixtures and street context.

Called from build_model.layout_A() / layout_B() as  details.dress(m, variant, globals()).
Nothing here changes an equipment footprint, the schedule (m.items) or any dimension in SITE:
every object is decoration placed relative to the schedule so it follows a re-survey.
All objects live in un-coded nodes, so the footprint checks in verify_model.py still apply
only to the equipment itself.

ASSUMED / illustrative: neighbouring facades, upper floors, the parked car, the scooter, wall
sockets, the gas pipe route, light fittings. They are context, not survey.
"""
import math

# name: (sRGB rgb, alpha, metallic, roughness, texture)
EXTRA_MATS = {
    'kraft': ((0.80, 0.66, 0.47), 1, 0, 0.85, None),
    'led': ((1.0, 0.97, 0.90), 1, 0, 0.4, None),
    'led_orange': ((1.0, 0.55, 0.12), 1, 0, 0.4, None),
    'screen': ((0.06, 0.16, 0.13), 1, 0, 0.2, None),
    'gas_yellow': ((0.93, 0.74, 0.10), 1, 0.2, 0.45, None),
    'win_dark': ((0.10, 0.13, 0.16), 1, 0.4, 0.08, None),
    'nb_cream': ((0.90, 0.88, 0.82), 1, 0, 0.8, None),
    'nb_blue': ((0.13, 0.30, 0.62), 1, 0, 0.5, None),
    'car_paint': ((0.78, 0.80, 0.82), 1, 0.7, 0.28, None),
    'rubber': ((0.035, 0.035, 0.04), 1, 0, 0.9, None),
    'soil': ((0.26, 0.21, 0.16), 1, 0, 0.95, None),
    'facade': ((0.74, 0.71, 0.65), 1, 0, 0.9, None),
    'trim': ((0.60, 0.58, 0.54), 1, 0, 0.85, None),
}
# linear RGB emissive factors written into the GLB so any glTF viewer shows lit fittings
EMISSIVE = {'led': (1.0, 0.93, 0.80), 'led_orange': (1.0, 0.30, 0.02), 'screen': (0.02, 0.22, 0.14), 'display': (0.05, 0.60, 0.45)}


def _item(m, code):
    return next((i for i in m.items if i['code'] == code and i['cat'] not in ('under', 'overhead')), None)


def _fp(i):
    return (i['x0'], i['y0'], i['x1'], i['y1'])


def dress(m, variant, g):
    SITE, W, D, H = g['SITE'], g['W'], g['D'], g['H']
    interior(m, variant, g, SITE, W, D, H)
    shopfront(m, variant, g, SITE, W, D, H)
    street(m, variant, g, SITE, W, D, H)


# ----------------------------------------------------------------------------------------------
def interior(m, variant, g, SITE, W, D, H):
    top_box, top_cyl, unit_point, ulen, udepth = g['top_box'], g['top_cyl'], g['unit_point'], g['ulen'], g['udepth']

    def side_of(i):
        if i['y1'] > D - 0.02 and (i['x1'] - i['x0']) > (i['y1'] - i['y0']): return 'B'
        return 'R' if i['x1'] > W - 0.02 else 'L' if i['x0'] < 0.02 else 'B'

    p = m.node('equip/props', 'equip')

    def bowls(fp, s, u, d, z, n=5):
        for k in range(n):
            top_cyl(p, 'kraft', fp, s, u, d, z + k * 0.014, z + k * 0.014 + 0.062, 0.052, seg=16, r_top=0.074)

    it = _item(m, 'E02')                      # packing bench: bowls, lids, bags, label printer
    if it:
        fp, s = _fp(it), side_of(it); L = ulen(fp, s)
        bowls(fp, s, 0.13, 0.46, 0.90); bowls(fp, s, 0.30, 0.46, 0.90, 3)
        for k in range(6):
            top_cyl(p, 'poly', fp, s, 0.13, 0.26, 0.90 + k * 0.006, 0.905 + k * 0.006, 0.076, seg=16)
        for k in range(2):
            top_box(p, 'kraft', fp, s, L - 0.20 + k * 0.085, L - 0.125 + k * 0.085, 0.36, 0.52, 0.90, 1.14)
        top_box(p, 'black', fp, s, L - 0.21, L - 0.07, 0.10, 0.24, 0.90, 0.99)
        top_box(p, 'poly', fp, s, L - 0.19, L - 0.09, 0.095, 0.10, 0.955, 0.985)

    it = _item(m, 'E03')                      # prep counter: squeeze bottles, ticket rail, bowls
    if it:
        fp, s = _fp(it), side_of(it); L = ulen(fp, s); z = 0.90 + 0.44
        for k, col in enumerate(['f_white', 'f_red', 'f_yellow', 'f_green', 'f_white']):
            u = 0.14 + k * 0.105
            top_cyl(p, col, fp, s, u, 0.52, z, z + 0.15, 0.027, seg=12)
            top_cyl(p, 'poly', fp, s, u, 0.52, z + 0.15, z + 0.165, 0.020, seg=12)
            top_cyl(p, col, fp, s, u, 0.52, z + 0.165, z + 0.205, 0.011, seg=8, r_top=0.004)
        top_box(p, 'steel_edge', fp, s, 0.10, L - 0.10, 0.316, 0.328, z - 0.045, z - 0.025)
        for k in range(3):
            u = 0.20 + k * 0.26
            top_box(p, 'poly', fp, s, u, u + 0.075, 0.318, 0.320, z - 0.19 - k % 2 * 0.03, z - 0.04)
        bowls(fp, s, L - 0.14, 0.16, 0.922, 4)
        # order screen on the wall above the counter
        if s == 'R':
            c = (it['y0'] + it['y1']) / 2
            k = m.node('fixtures/order-screen', 'wall_right')
            k.rounded_box('black', W - 0.035, c - 0.30, 1.62, W - 0.004, c + 0.30, 1.98, radius=0.008)
            k.box('screen', W - 0.037, c - 0.28, 1.64, W - 0.035, c + 0.28, 1.96)
            k.box('lime', W - 0.038, c - 0.28, 1.915, W - 0.037, c + 0.28, 1.96)
            for r in range(4):
                k.box('led', W - 0.038, c - 0.25, 1.86 - r * 0.055, W - 0.037, c + 0.05 - (r % 2) * 0.09, 1.875 - r * 0.055)

    it = _item(m, 'E05')                      # griddle: turner + oil bottle
    if it:
        fp, s = _fp(it), side_of(it)
        p.tube('black', unit_point(fp, s, 0.52, 0.05, 0.895), unit_point(fp, s, 0.47, 0.24, 0.892), 0.011, seg=8)
        top_box(p, 'steel_edge', fp, s, 0.42, 0.50, 0.24, 0.34, 0.882, 0.886)
        top_cyl(p, 'f_yellow', fp, s, 0.07, 0.045, 0.86, 1.02, 0.024, seg=10)
        top_cyl(p, 'poly', fp, s, 0.07, 0.045, 1.02, 1.05, 0.010, seg=8)

    it = _item(m, 'E07')                      # rice cookers: lid knobs, handles, control panel
    if it:
        fp, s = _fp(it), side_of(it); L = ulen(fp, s)
        for d in (0.20, 0.52):
            top_cyl(p, 'black', fp, s, L / 2, d, 0.89, 0.925, 0.028, seg=12)
            for du in (-0.185, 0.185):
                top_box(p, 'black', fp, s, L / 2 + du - 0.012, L / 2 + du + 0.012, d - 0.04, d + 0.04, 0.78, 0.805)
        top_box(p, 'black', fp, s, L / 2 - 0.055, L / 2 + 0.055, 0.022, 0.034, 0.62, 0.71)
        top_box(p, 'led_orange', fp, s, L / 2 - 0.035, L / 2 - 0.02, 0.019, 0.022, 0.68, 0.695)

    it = _item(m, 'E09')                      # rear prep: salad bowl + knife on the raw board
    if it:
        fp, s = _fp(it), side_of(it); L = ulen(fp, s)
        top_cyl(p, 'steel_edge', fp, s, L - 0.22, 0.30, 0.915, 0.985, 0.075, seg=18, r_top=0.115)
        p.ellipsoid('f_green', unit_point(fp, s, L - 0.22, 0.30, 0.985), (0.10, 0.10, 0.03), seg=12, rings=5)
        p.tube('black', unit_point(fp, s, L - 0.62, 0.20, 0.925), unit_point(fp, s, L - 0.52, 0.22, 0.925), 0.011, seg=8)
        top_box(p, 'steel_edge', fp, s, L - 0.52, L - 0.36, 0.205, 0.245, 0.918, 0.921)

    it = _item(m, 'E10')                      # wash sink: pans and tubs on the drying shelf
    if it:
        fp, s = _fp(it), side_of(it); L = ulen(fp, s); Dp = udepth(fp, s)
        top_box(p, 'steel_edge', fp, s, 0.08, 0.40, Dp - 0.27, Dp - 0.04, 1.57, 1.635)
        top_box(p, 'steel', fp, s, 0.10, 0.38, Dp - 0.25, Dp - 0.06, 1.635, 1.70)
        for k in range(3):
            top_box(p, 'poly', fp, s, 0.44, 0.56 - k * 0.005, Dp - 0.25, Dp - 0.06, 1.57 + k * 0.05, 1.615 + k * 0.05)

    it = _item(m, 'E01')                      # service counter: card reader, sanitiser, number stand
    if it:
        x0, y0 = it['x0'], it['y0']
        p.rounded_box('black', x0 + 0.60, y0 + 0.06, 0.90, x0 + 0.68, y0 + 0.21, 0.935, radius=0.008)
        p.box('screen', x0 + 0.61, y0 + 0.13, 0.935, x0 + 0.67, y0 + 0.20, 0.936)
        p.cyl('poly', x0 + 0.80, y0 + 0.36, 0.90, 1.03, 0.03, seg=12)
        p.cyl('forest', x0 + 0.80, y0 + 0.36, 1.03, 1.06, 0.014, seg=8)
        p.tube('forest', (x0 + 0.80, y0 + 0.36, 1.06), (x0 + 0.80, y0 + 0.31, 1.06), 0.006, seg=6)

    if variant == 'A':                        # pedal-bin lids and pedals
        for bx0, by0, bx1, by1, bz in ((1.66, 0.06, 2.02, 0.42, 0.62), (1.36, 4.58, 1.71, 4.98, 0.74)):
            p.rounded_box('forest', bx0 - 0.005, by0 - 0.005, bz, bx1 + 0.005, by1 + 0.005, bz + 0.035, radius=0.012)
            p.box('steel_edge', (bx0 + bx1) / 2 - 0.05, by1, bz - 0.56, (bx0 + bx1) / 2 + 0.05, by1 + 0.035, bz - 0.545)

    # ---- fire point by the staff door: extinguisher fittings, fire blanket ----
    p.cyl('black', 0.08, 0.90, 1.35, 1.40, 0.022, seg=10)
    p.tube('black', (0.08, 0.90, 1.39), (0.14, 0.90, 1.43), 0.008, seg=6)
    p.tube('black', (0.115, 0.92, 1.38), (0.125, 0.94, 1.10), 0.007, seg=6)
    p.box('steel_dark', 0.0, 0.86, 1.12, 0.012, 0.94, 1.20)
    p.rounded_box('red', 0.0, 0.45, 1.45, 0.035, 0.63, 1.76, radius=0.008)
    p.box('poly', 0.036, 0.49, 1.56, 0.037, 0.59, 1.70)

    # ---- split AC: louvre slot, vane, status LED ----
    ac = _ac(m)
    if ac:
        ax1, ay0, ay1, az0, az1 = ac
        p.box('gasket', ax1 - 0.06, ay0 + 0.04, az0 - 0.002, ax1 + 0.002, ay1 - 0.04, az0 + 0.045)
        p.box('white', ax1 - 0.03, ay0 + 0.05, az0 + 0.008, ax1 + 0.03, ay1 - 0.05, az0 + 0.016)
        p.box('display', ax1, ay1 - 0.16, az1 - 0.10, ax1 + 0.002, ay1 - 0.10, az1 - 0.085)

    # ---- walls: brand band at the tile line, coved skirting, sockets ----
    for layer, box in (('wall_left', (0, 0, 0.007, D)), ('wall_right', (W - 0.007, 0, W, D)), ('wall_back', (0, D - 0.007, W, D))):
        n = m.node('fixtures/band-' + layer, layer)
        n.box('forest', box[0], box[1], 2.10, box[2], box[3], 2.17)
        n.box('lime', box[0], box[1], 2.17, box[2], box[3], 2.182)
        sk = dict(wall_left=(0, 0, 0.012, D), wall_right=(W - 0.012, 0, W, D), wall_back=(0, D - 0.012, W, D))[layer]
        n.box('steel_dark', sk[0], sk[1], 0, sk[2], sk[3], 0.10)
    s = m.node('fixtures/sockets', 'wall_right')
    for y in (0.80, 1.72, 2.60, 4.27):
        s.rounded_box('white', W - 0.014, y - 0.075, 1.09, W, y + 0.075, 1.18, radius=0.006)
        for dy in (-0.035, 0.035):
            s.box('gasket', W - 0.0155, y + dy - 0.018, 1.115, W - 0.014, y + dy + 0.018, 1.155)

    # ---- back wall: magnetic knife strip over the prep table ----
    kx = SITE['wc_w'] + 0.82
    if kx + 0.46 < W - 0.05:
        k = m.node('fixtures/knife-strip', 'wall_back')
        k.box('black', kx, D - 0.022, 1.27, kx + 0.46, D - 0.007, 1.305)
        for i, ln in enumerate((0.20, 0.17, 0.14, 0.11)):
            x = kx + 0.06 + i * 0.105
            k.box('steel_edge', x, D - 0.026, 1.29 - ln, x + 0.034, D - 0.022, 1.30)
            k.rounded_box('black', x + 0.004, D - 0.034, 1.30, x + 0.030, D - 0.020, 1.40, radius=0.006)

    # ---- gas line (layout A only: B has no acceptable cylinder position) ----
    if variant == 'A':
        gp = m.node('mep/gas-pipe', 'mep')
        x, z = W - 0.028, 1.075
        gp.tube('gas_yellow', (x, 0.30, 0.80), (x, 0.30, z), 0.011, seg=8)
        gp.tube('gas_yellow', (x, 0.30, z), (x, 4.30, z), 0.011, seg=8)
        for code in ('E05', 'E06', 'E07'):
            it = _item(m, code)
            if it:
                y = (it['y0'] + it['y1']) / 2
                gp.tube('gas_yellow', (x, y, z), (x, y, 0.82), 0.009, seg=8)
        gp.cyl('steel_edge', x, 0.62, z - 0.03, z + 0.03, 0.022, seg=10)
        gp.tube('red', (x, 0.62, z + 0.03), (x - 0.02, 0.70, z + 0.05), 0.009, seg=6)

    # ---- ceiling: LED panels over the aisle (hidden with the ceiling in cutaways) ----
    c = m.node('fixtures/led-panels', 'ceiling')
    cx = (0.70 + W - 0.70) / 2
    for y0, y1 in ((0.50, 1.70), (2.05, 3.25), (3.60, 4.80)):
        c.box('steel_edge', cx - 0.17, y0 - 0.02, H - 0.03, cx + 0.17, y1 + 0.02, H)
        c.box('led', cx - 0.15, y0, H - 0.034, cx + 0.15, y1, H - 0.03)

    # ---- floor: drain grate and entrance mat ----
    f = m.node('fixtures/floor', 'shell')
    dx, dy = cx + 0.25, SITE['wc_y0'] + 0.55
    f.box('steel_edge', dx - 0.09, dy - 0.09, 0.0, dx + 0.09, dy + 0.09, 0.004)
    for i in range(5):
        f.box('gasket', dx - 0.07, dy - 0.066 + i * 0.03, 0.004, dx + 0.07, dy - 0.054 + i * 0.03, 0.005)
    f.rounded_box('rubber', 0.14, 0.10, 0.0, 0.92, 0.62, 0.012, radius=0.005)


def _ac(m):
    for i in m.items:
        if i['code'] == 'E17':
            return i['x1'], i['y0'], i['y1'], i['h'], i['h'] + 0.30
    return None


# ----------------------------------------------------------------------------------------------
def shopfront(m, variant, g, SITE, W, D, H):
    t = SITE['wall_t']; tt = SITE['transom_top']
    ox0, ox1 = SITE['open_x0'], SITE['open_x1']
    dx0, dx1 = SITE['door_x0'], SITE['door_x1']
    sz0, sz1 = tt + 0.32, tt + 1.10
    n = m.node('front/trim', 'front')
    # fascia: metal edge trim, LED downlights, blade-sign brackets
    for z0, z1 in ((sz0 - 0.03, sz0), (sz1, sz1 + 0.03)):
        n.box('steel_edge', -t - 0.06, -t - 0.175, z0, W + t + 0.06, -t, z1)
    for x in (-t - 0.06, W + t + 0.045):
        n.box('steel_edge', x, -t - 0.175, sz0, x + 0.015, -t, sz1)
    for i in range(4):
        n.cyl('led', 0.3 + i * 0.66, -t - 0.08, sz0 - 0.034, sz0 - 0.03, 0.045, seg=14)
    for z in (2.36, 2.70):
        n.tube('steel_dark', (W + t - 0.02, -t, z), (W + t - 0.02, -t - 0.20, z), 0.012, seg=8)
    # shutter guide rails and bottom bar
    for x in (ox0 - 0.035, ox1 - 0.015):
        n.box('alu', x, -t - 0.075, 0.0, x + 0.05, -t - 0.02, tt)
    n.box('alu', ox0, -t - 0.07, tt - 0.035, ox1, -t - 0.03, tt + 0.02)
    # door: safety manifestation bands, kick plate, closer
    for z in (1.02, 1.50):
        n.box('lime', dx0 + 0.05, -0.108, z, dx1 - 0.05, -0.104, z + 0.03)
    n.box('steel_edge', dx0 + 0.045, -0.123, 0.055, dx1 - 0.045, -0.119, 0.26)
    n.rounded_box('steel_dark', dx0 + 0.10, -0.068, SITE['head'] - 0.09, dx0 + 0.36, -0.03, SITE['head'] - 0.03, radius=0.008)
    n.tube('steel_edge', (dx0 + 0.34, -0.05, SITE['head'] - 0.06), (dx0 + 0.62, -0.068, SITE['head'] - 0.02), 0.007, seg=6)
    # pier lights either side of the opening
    for x in (-t / 2 + 0.02, W + t / 2 - 0.02):
        n.rounded_box('steel_dark', x - 0.05, -t - 0.07, 2.02, x + 0.05, -t, 2.24, radius=0.01)
        n.box('led', x - 0.035, -t - 0.072, 2.03, x + 0.035, -t - 0.07, 2.10)


# ----------------------------------------------------------------------------------------------
def street(m, variant, g, SITE, W, D, H):
    t, st, sw = SITE['wall_t'], SITE['step'], SITE['sidewalk']
    g0 = -st                                   # sidewalk level
    far = 7.2                                  # how far the context extends either side
    s = m.node('site/extension', 'site')
    for xa, xb in ((-far, -3.2), (W + 3.2, W + far)):
        s.box('pave', xa, -t - sw, g0 - 0.12, xb, -t, g0)
        s.box('stone', xa, -t - sw - 0.15, g0 - 0.12, xb, -t - sw, g0)
    road = g0 - 0.13
    s.box('asphalt', -far, -t - sw - 7.5, road - 0.12, W + far, -t - sw - 2.0, road)
    for xa, xb in ((-far, -3.2), (W + 3.2, W + far)):
        s.box('asphalt', xa, -t - sw - 2.0, road - 0.12, xb, -t - sw - 0.15, road)
    x = -far + 0.4
    while x < W + far - 1.6:                   # lane line
        s.box('white', x, -t - sw - 4.05, road, x + 1.5, -t - sw - 3.93, road + 0.004)
        x += 3.0
    # tree pits + fuller crowns
    tr = m.node('site/trees', 'site')
    for tx in (-2.3, W + 4.6):
        ty = -t - sw + 0.45
        tr.box('soil', tx - 0.5, ty - 0.42, g0, tx + 0.5, ty + 0.42, g0 + 0.012)
        for a, b in ((tx - 0.52, tx - 0.5), (tx + 0.5, tx + 0.52)):
            tr.box('stone', a, ty - 0.44, g0, b, ty + 0.44, g0 + 0.03)
        if tx > 0:
            tr.cyl('trunk', tx, ty, g0, 3.2, 0.20, seg=12, r_top=0.14)
            tr.sphere('leaf', tx, ty, 3.9, 1.0, seg=12, rings=8)
        for ox, oy, oz, r in ((0.75, 0.2, 3.5, 0.72), (-0.7, -0.25, 3.6, 0.78), (0.1, 0.55, 4.5, 0.74), (-0.2, -0.6, 4.35, 0.66), (0.3, -0.1, 4.9, 0.6)):
            tr.sphere('leaf', tx + ox, ty + oy, oz, r, seg=10, rings=6)

    c = m.node('site/buildings', 'context')
    top = 10.6
    # facades continuing either side and above (ASSUMED massing)
    for xa, xb in ((-far, -3.2), (W + 3.2, W + far)):
        c.box('facade', xa, -t, g0, xb, 0.3, 4.2)
        c.box('shutter', xa + 0.3, -t - 0.03, g0, xb - 0.3, -t, 2.6)
        c.box('nb_cream', xa + 0.2, -t - 0.12, 2.75, xb - 0.2, -t, 3.5)
    c.box('facade', -far, -t, 4.2, -3.2, 0.3, top); c.box('facade', W + 3.2, -t, 4.2, W + far, 0.3, top)
    c.box('facade', -3.2, -t, 6.2, W + 3.2, 0.3, top)
    for z in (4.2, 7.25):                      # string courses
        c.box('trim', -far, -t - 0.07, z - 0.06, W + far, -t, z + 0.08)
    c.box('trim', -far, -t - 0.12, top - 0.18, W + far, 0.3, top)
    xw = -far + 0.55
    k = 0
    while xw + 1.15 < W + far:
        for level, z0 in enumerate((4.85, 7.85)):
            clash_ac = level == 0 and xw < 1.6 and xw + 1.15 > 0.5
            if not clash_ac:
                c.box('win_dark', xw, -t - 0.012, z0, xw + 1.15, -t + 0.01, z0 + 1.40)
                for a, b in ((xw - 0.05, xw), (xw + 1.15, xw + 1.20), (xw + 0.55, xw + 0.60)):
                    c.box('nb_cream', a, -t - 0.04, z0 - 0.05, b, -t, z0 + 1.45)
                c.box('nb_cream', xw - 0.05, -t - 0.04, z0 + 1.40, xw + 1.20, -t, z0 + 1.47)
                c.box('trim', xw - 0.10, -t - 0.10, z0 - 0.09, xw + 1.25, -t, z0 - 0.03)
                c.box('shutter', xw, -t - 0.03, z0 + 1.05 if (k + level) % 3 == 0 else z0 + 1.28, xw + 1.15, -t - 0.012, z0 + 1.40)
            if level == 0 and k % 2 == 1 and not clash_ac:       # balcony with railing
                bz = z0 - 0.16
                c.box('trim', xw - 0.20, -t - 0.75, bz - 0.12, xw + 1.35, -t, bz)
                c.tube('steel_dark', (xw - 0.18, -t - 0.72, bz + 0.95), (xw + 1.33, -t - 0.72, bz + 0.95), 0.018, seg=6)
                for a in (xw - 0.18, xw + 1.33):
                    c.tube('steel_dark', (a, -t - 0.72, bz + 0.95), (a, -t, bz + 0.95), 0.018, seg=6)
                for j in range(13):
                    bx = xw - 0.18 + j * 1.51 / 12
                    c.tube('steel_dark', (bx, -t - 0.72, bz), (bx, -t - 0.72, bz + 0.95), 0.009, seg=5)
            if level == 1 and k % 3 == 0:                        # more condensers
                c.rounded_box('white', xw + 0.2, -t - 0.32, z0 - 0.75, xw + 1.0, -t, z0 - 0.2, radius=0.02)
                c.tube('gasket', (xw + 0.6, -t - 0.321, z0 - 0.475), (xw + 0.6, -t - 0.326, z0 - 0.475), 0.21, seg=18)
        xw += 1.95; k += 1
    # condenser above the shop: grille detail on the existing unit
    for i in range(6):
        c.box('gasket', 0.66, -t - 0.354, 4.52 + i * 0.085, 1.44, -t - 0.35, 4.55 + i * 0.085)
    # left neighbour (menswear): fascia, window frame and a flat window display
    c.box('nb_cream', -3.05, -t - 0.16, 2.72, -0.33, -t, 3.52)
    c.rounded_box('nb_blue', -2.80, -t - 0.185, 2.93, -0.58, -t - 0.16, 3.31, radius=0.012)
    c.box('nb_cream', -2.70, -t - 0.19, 3.08, -0.68, -t - 0.185, 3.16)
    for a, b in ((-2.95, -2.90), (-0.45, -0.40), (-1.32, -1.27)):
        c.box('alu', a, -t - 0.05, 0.0, b, -t, 2.45)
    c.box('alu', -2.95, -t - 0.05, 2.40, -0.40, -t, 2.45)
    c.box('stone', -2.95, -t - 0.06, g0, -0.40, -t, 0.0)
    c.box('nb_cream', -2.88, -t - 0.012, 0.02, -1.34, -t - 0.004, 2.38)
    for i, col in enumerate(('cloth_a', 'ink', 'cloth_a')):
        mx = -2.62 + i * 0.5
        c.rounded_box(col, mx - 0.17, -t - 0.018, 1.05, mx + 0.17, -t - 0.012, 1.72, radius=0.003)
        c.rounded_box('ink' if col != 'ink' else 'cloth_a', mx - 0.13, -t - 0.018, 0.25, mx + 0.13, -t - 0.012, 1.05, radius=0.003)
    c.box('red', -2.85, -t - 0.024, 1.95, -1.40, -t - 0.02, 2.22)
    # right neighbour (closed): fascia + shutter rails
    c.box('trim', W + t + 0.10, -t - 0.12, 2.72, W + 3.05, -t, 3.45)
    for a in (W + t + 0.11, W + 3.0):
        c.box('alu', a, -t - 0.06, g0, a + 0.05, -t, 2.62)

    # parked car at the kerb, to the right (illustrative)
    v = m.node('site/car', 'context')
    cx0, cx1 = W + 1.6, W + 5.8
    cy1 = -t - sw - 0.45; cy0 = cy1 - 1.78
    v.rounded_box('car_paint', cx0, cy0, road + 0.22, cx1, cy1, road + 0.86, radius=0.16, segments=4)
    v.rounded_box('car_paint', cx0 + 0.95, cy0 + 0.10, road + 0.80, cx1 - 0.85, cy1 - 0.10, road + 1.44, radius=0.22, segments=4)
    v.rounded_box('win_dark', cx0 + 1.02, cy0 + 0.085, road + 0.90, cx1 - 0.95, cy1 - 0.085, road + 1.34, radius=0.12, segments=3)
    v.rounded_box('win_dark', cx0 + 0.93, cy0 + 0.16, road + 0.92, cx1 - 0.83, cy1 - 0.16, road + 1.33, radius=0.14, segments=3)
    for wx in (cx0 + 0.78, cx1 - 0.82):
        v.tube('rubber', (wx, cy0 - 0.01, road + 0.32), (wx, cy1 + 0.01, road + 0.32), 0.32, seg=20)
        for yy, d in ((cy0 - 0.012, -1), (cy1 + 0.012, 1)):
            v.tube('steel_edge', (wx, yy, road + 0.32), (wx, yy + 0.008 * d, road + 0.32), 0.19, seg=14)
    for yy in (cy0 + 0.18, cy1 - 0.42):
        v.rounded_box('led', cx0 - 0.012, yy, road + 0.60, cx0 + 0.02, yy + 0.24, road + 0.70, radius=0.01)
        v.rounded_box('red', cx1 - 0.02, yy, road + 0.62, cx1 + 0.012, yy + 0.24, road + 0.72, radius=0.01)
    v.box('rubber', cx0 - 0.03, cy0 + 0.1, road + 0.24, cx0 + 0.05, cy1 - 0.1, road + 0.40)
    v.box('rubber', cx1 - 0.05, cy0 + 0.1, road + 0.24, cx1 + 0.03, cy1 - 0.1, road + 0.40)

    if variant == 'A':                         # delivery scooter under the rider's box
        sc = m.node('site/scooter', 'people_out')
        y = -t - 3.15
        for wx in (2.62, 3.62):
            sc.tube('rubber', (wx, y - 0.045, g0 + 0.21), (wx, y + 0.045, g0 + 0.21), 0.21, seg=16)
            sc.tube('steel_edge', (wx, y - 0.05, g0 + 0.21), (wx, y + 0.05, g0 + 0.21), 0.09, seg=10)
        sc.rounded_box('forest', 2.80, y - 0.11, g0 + 0.22, 3.50, y + 0.11, g0 + 0.34, radius=0.03)
        sc.rounded_box('forest', 3.10, y - 0.13, g0 + 0.30, 3.70, y + 0.13, g0 + 0.66, radius=0.06)
        sc.rounded_box('black', 3.02, y - 0.12, g0 + 0.66, 3.52, y + 0.12, g0 + 0.74, radius=0.03)
        sc.rounded_box('forest', 2.66, y - 0.10, g0 + 0.30, 2.84, y + 0.10, g0 + 0.92, radius=0.05)
        sc.tube('steel_dark', (2.62, y, g0 + 0.21), (2.76, y, g0 + 1.02), 0.02, seg=8)
        sc.tube('rubber', (2.76, y - 0.28, g0 + 1.03), (2.76, y + 0.28, g0 + 1.03), 0.016, seg=8)
        sc.cyl('led', 2.68, y, g0 + 0.80, g0 + 0.88, 0.05, seg=10)
        for a in (3.10, 3.40):
            sc.tube('steel_dark', (a, y, g0 + 0.74), (a, y, g0 + 1.0), 0.012, seg=6)
        sc.box('lime', 3.05, y - 0.101, g0 + 1.12, 3.45, y - 0.099, g0 + 1.30)
