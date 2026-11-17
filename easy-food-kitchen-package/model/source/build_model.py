#!/usr/bin/env python3
"""
Easy Food - Al Brazil St, Damascus - parametric shop + kitchen model.

Single source of truth for geometry. Edit the numbers in SITE and the
equipment lists in layout_A()/layout_B(), then run:

    python build_model.py

Outputs (relative to the package root):
    model/easy-food-kitchen-A.glb / -B.glb      portable 3D (glTF binary)
    model/easy-food-kitchen-A.obj + .mtl        editable mesh (Blender, SketchUp, 3ds Max...)
    model/layout-A.json / layout-B.json         equipment footprints (metres)
    model/viewer/model-data.js                  data for the offline viewer
    plans/layout-A.svg / layout-B.svg           dimensioned 2D plans (1:25 at A3)

Coordinates (metres):  x = across the shop, 0 at the LEFT wall as seen from the street
                       y = depth, 0 at the inside face of the shopfront, +y towards the back
                       z = up, 0 at the interior finished floor
STATUS OF NUMBERS:  see SITE below - 'supplied', 'photo-estimate' or 'ASSUMED'.
"""
import base64, json, math, os, struct, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, '..', '..'))
TEX = os.path.join(HERE, 'textures')

# --------------------------------------------------------------------------------------
SITE = dict(
    W=2.79,          # confirmed by owner 16 Nov 2026 (iPhone Measure reading; tape-check before fabrication)
    D=5.06,          # supplied by owner, matches screenshot
    H=3.00,          # ASSUMED clear height - not measured
    wall_t=0.20,     # ASSUMED
    open_x0=0.10, front_right_inset=0.10,  # photo-estimate: opening derived from clear width minus pier insets
    door_x0=0.10, door_x1=0.95,   # photo-estimate: existing hinged glass door, left, opens inward
    win_x0=1.00,                  # photo-estimate: existing fixed glazing -> new service window
    sill=0.90,                    # design: counter/sill height above interior floor
    head=2.05,                    # photo-estimate: door / window head
    transom_top=2.55,             # photo-estimate
    step=0.15,                    # photo-estimate: one stone step up from the sidewalk
    sidewalk=4.00,                # ASSUMED sidewalk depth to kerb - measure
    wc_w=1.20, wc_d=1.60,         # ASSUMED OUTER envelope; owner confirms rear-left WC must remain
    wc_wall=0.10, wc_door=0.85,   # ASSUMED structural opening, ~0.70 clear after folded stack / jambs
    wc_access_min=0.80,           # design allowance, not a statutory minimum
)
def configure_site(**measurements):
    """Recompute derived dimensions after editing SITE or trying a survey width."""
    global W, D, H
    SITE.update(measurements)
    W, D, H = SITE['W'], SITE['D'], SITE['H']
    SITE['open_x1'] = SITE['win_x1'] = round(W - SITE['front_right_inset'], 3)
    SITE['wc_y0'] = round(D - SITE['wc_d'], 3)


configure_site()

HEX = dict(forest='#146B45', lime='#DDF45B', cream='#FFF8EA', ink='#17251C')


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# name: (sRGB rgb, alpha, metallic, roughness, texture or None)
MATS = {
    'steel': ((0.80, 0.81, 0.82), 1, 0.95, 0.30, None),
    'steel_edge': ((0.84, 0.85, 0.86), 1, 1, 0.19, None),
    'gasket': ((0.045, 0.055, 0.050), 1, 0, 0.88, None),
    'display': ((0.25, 0.80, 0.66), 1, 0, 0.25, None),
    'fold_panel': (hexrgb(HEX['cream']), 1, 0, 0.55, None),
    'steel_dark': ((0.36, 0.37, 0.39), 1, 0.6, 0.5, None),
    'white': ((0.95, 0.95, 0.93), 1, 0, 0.55, None),
    'tile': ((0.86, 0.88, 0.87), 1, 0, 0.35, None),
    'paint': (hexrgb(HEX['cream']), 1, 0, 0.8, None),
    'forest': (hexrgb(HEX['forest']), 1, 0, 0.6, None),
    'lime': (hexrgb(HEX['lime']), 1, 0, 0.6, None),
    'ink': (hexrgb(HEX['ink']), 1, 0, 0.6, None),
    'floor': ((0.50, 0.52, 0.52), 1, 0, 0.75, None),
    'glass': ((0.72, 0.88, 0.90), 0.22, 0, 0.08, None),
    'black': ((0.07, 0.07, 0.08), 1, 0, 0.6, None),
    'alu': ((0.70, 0.71, 0.72), 1, 0.7, 0.45, None),
    'carton': ((0.72, 0.56, 0.38), 1, 0, 0.85, None),
    'poly': ((0.97, 0.97, 0.95), 1, 0, 0.5, None),
    'pave': ((0.71, 0.70, 0.67), 1, 0, 0.9, None),
    'asphalt': ((0.26, 0.26, 0.27), 1, 0, 0.95, None),
    'stone': ((0.21, 0.21, 0.23), 1, 0, 0.6, None),
    'context': ((0.80, 0.79, 0.76), 1, 0, 0.9, None),
    'shutter': ((0.74, 0.74, 0.72), 1, 0.3, 0.6, None),
    'skin': ((0.84, 0.67, 0.54), 1, 0, 0.7, None),
    'cloth_staff': (hexrgb(HEX['forest']), 1, 0, 0.8, None),
    'cloth_a': ((0.25, 0.33, 0.52), 1, 0, 0.8, None),
    'cloth_b': ((0.62, 0.30, 0.25), 1, 0, 0.8, None),
    'cloth_c': ((0.86, 0.72, 0.25), 1, 0, 0.8, None),
    'red': ((0.80, 0.10, 0.10), 1, 0, 0.5, None),
    'trunk': ((0.36, 0.28, 0.22), 1, 0, 0.9, None),
    'leaf': ((0.25, 0.45, 0.24), 1, 0, 0.9, None),
    'f_green': ((0.33, 0.62, 0.25), 1, 0, 0.8, None),
    'f_red': ((0.80, 0.22, 0.16), 1, 0, 0.8, None),
    'f_yellow': ((0.93, 0.78, 0.25), 1, 0, 0.8, None),
    'f_white': ((0.96, 0.94, 0.88), 1, 0, 0.8, None),
    'f_brown': ((0.55, 0.36, 0.22), 1, 0, 0.8, None),
    'f_purple': ((0.50, 0.20, 0.42), 1, 0, 0.8, None),
    'flow_raw': ((0.10, 0.42, 0.90), 1, 0, 0.6, None),
    'flow_rte': ((0.96, 0.52, 0.10), 1, 0, 0.6, None),
    't_sign': ((1, 1, 1), 1, 0, 0.6, 'sign_fascia.png'),
    't_order': ((1, 1, 1), 1, 0, 0.6, 'label_order.png'),
    't_collect': ((1, 1, 1), 1, 0, 0.6, 'label_collect.png'),
    't_apron': ((1, 1, 1), 1, 0, 0.6, 'apron.png'),
    't_menu': ((1, 1, 1), 1, 0, 0.6, 'menu_board.png'),
    't_blade': ((1, 1, 1), 1, 0, 0.6, 'blade.png'),
}


import details  # scene dressing: props, fixtures, street context (decoration only)
MATS.update(details.EXTRA_MATS)


# --------------------------------------------------------------------------------------
class Node:
    def __init__(self, name, layer, label=None, code=None, anchor=None, label_ar=None):
        self.name, self.layer, self.label, self.code, self.anchor, self.label_ar = name, layer, label, code, anchor, label_ar
        self.geo = {}   # material -> [pos list, normal list, uv list, index list]

    def _g(self, mat):
        return self.geo.setdefault(mat, [[], [], [], []])

    def _face(self, mat, n, pts, uvs=None):
        P, N, U, I = self._g(mat)
        b = len(P)
        P.extend(pts)
        N.extend([n] * len(pts))
        U.extend(uvs if uvs else [(0.0, 0.0)] * len(pts))
        for k in range(1, len(pts) - 1):
            I.extend([b, b + k, b + k + 1])

    def box(self, mat, x0, y0, z0, x1, y1, z1):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if z1 < z0: z0, z1 = z1, z0
        f = self._face
        f(mat, (1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])
        f(mat, (-1, 0, 0), [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)])
        f(mat, (0, 1, 0), [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)])
        f(mat, (0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)])
        f(mat, (0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        f(mat, (0, 0, -1), [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)])
        return self

    def cyl(self, mat, cx, cy, z0, z1, r, seg=20, r_top=None):
        rt = r if r_top is None else r_top
        ring = [(math.cos(2 * math.pi * i / seg), math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        for i in range(seg):
            a, b = ring[i], ring[(i + 1) % seg]
            n = np.array(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (r - rt) / (z1 - z0)))
            n = tuple(n / np.linalg.norm(n))
            self._face(mat, n, [(cx + a[0] * r, cy + a[1] * r, z0), (cx + b[0] * r, cy + b[1] * r, z0),
                                (cx + b[0] * rt, cy + b[1] * rt, z1), (cx + a[0] * rt, cy + a[1] * rt, z1)])
        self._face(mat, (0, 0, 1), [(cx + c * rt, cy + s * rt, z1) for c, s in ring])
        self._face(mat, (0, 0, -1), [(cx + c * r, cy + s * r, z0) for c, s in reversed(ring)])
        return self

    def rounded_box(self, mat, x0, y0, z0, x1, y1, z1, radius=0.008, segments=3):
        """A filleted solid with smooth corner normals, kept inside the supplied bounds."""
        lo, hi = np.minimum((x0, y0, z0), (x1, y1, z1)), np.maximum((x0, y0, z0), (x1, y1, z1))
        half, centre = (hi - lo) / 2, (hi + lo) / 2
        r = min(radius, float(min(half)) * 0.95)
        core = half - r
        axes = [np.concatenate((np.linspace(-h, -c, segments + 1), np.linspace(c, h, segments + 1))) for h, c in zip(half, core)]
        for axis in range(3):
            u, v = (axis + 1) % 3, (axis + 2) % 3
            for sign in (-1, 1):
                for i in range(len(axes[u]) - 1):
                    for j in range(len(axes[v]) - 1):
                        pts, normals = [], []
                        corners = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                        if sign < 0: corners.reverse()
                        for a, b in corners:
                            p = np.zeros(3); p[axis] = sign * half[axis]; p[u] = axes[u][a]; p[v] = axes[v][b]
                            c = np.clip(p, -core, core)
                            normal = (p - c) / np.linalg.norm(p - c)
                            pts.append(tuple(centre + c + normal * r)); normals.append(tuple(normal))
                        P, N, U, I = self._g(mat); base = len(P)
                        P.extend(pts); N.extend(normals); U.extend([(0.0, 0.0)] * 4)
                        I.extend([base, base + 1, base + 2, base, base + 2, base + 3])
        return self

    def tube(self, mat, a, b, radius=0.012, seg=10, r_end=None):
        """Tube between arbitrary endpoints (handles, taps and posed limbs)."""
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        direction = b - a; length = np.linalg.norm(direction); direction /= length
        ref = np.array((0, 0, 1) if abs(direction[2]) < 0.9 else (0, 1, 0))
        u = np.cross(direction, ref); u /= np.linalg.norm(u); v = np.cross(direction, u)
        rt = radius if r_end is None else r_end
        ring = [u * math.cos(i * math.tau / seg) + v * math.sin(i * math.tau / seg) for i in range(seg)]
        for i in range(seg):
            na, nb = ring[i], ring[(i + 1) % seg]
            normal = (na + nb) / 2 + direction * (radius - rt) / length
            normal /= np.linalg.norm(normal)
            self._face(mat, tuple(normal), [tuple(a + na * radius), tuple(a + nb * radius), tuple(b + nb * rt), tuple(b + na * rt)])
        self._face(mat, tuple(direction), [tuple(b + q * rt) for q in ring])
        self._face(mat, tuple(-direction), [tuple(a + q * radius) for q in reversed(ring)])
        return self

    def ellipsoid(self, mat, centre, radii, seg=12, rings=8):
        start = len(self._g(mat)[0])
        self.sphere(mat, 0, 0, 0, 1, seg, rings)
        P, N, _, _ = self._g(mat)
        for i in range(start, len(P)):
            P[i] = tuple(centre[k] + P[i][k] * radii[k] for k in range(3))
            normal = np.array([N[i][k] / radii[k] for k in range(3)])
            N[i] = tuple(normal / np.linalg.norm(normal))
        return self

    def sphere(self, mat, cx, cy, cz, r, seg=14, rings=8):
        def p(i, j):
            th = math.pi * j / rings
            ph = 2 * math.pi * i / seg
            n = (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
            return n
        for j in range(rings):
            for i in range(seg):
                ns = [p(i, j + 1), p(i + 1, j + 1), p(i + 1, j), p(i, j)]
                pts = [(cx + n[0] * r, cy + n[1] * r, cz + n[2] * r) for n in ns]
                n = tuple(sum(q[k] for q in ns) / 4 for k in range(3))
                self._face(mat, n, pts)
        return self

    def quad(self, mat, bl, br, tr, tl):
        """textured quad; corners bottom-left, bottom-right, top-right, top-left as seen by the viewer"""
        a, b, c = np.array(bl), np.array(br), np.array(tl)
        n = np.cross(b - a, c - a)
        n = tuple(n / np.linalg.norm(n))
        self._face(mat, n, [bl, br, tr, tl], [(0, 1), (1, 1), (1, 0), (0, 0)])
        return self

    def arrow(self, mat, x, y, dx, dy, size=0.16, z0=0.012, z1=0.03):
        L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
        px, py = -dy, dx
        tip = (x + dx * size, y + dy * size)
        a = (x + px * size * 0.7, y + py * size * 0.7)
        b = (x - px * size * 0.7, y - py * size * 0.7)
        self._face(mat, (0, 0, 1), [(a[0], a[1], z1), (b[0], b[1], z1), (tip[0], tip[1], z1)])
        return self


class Model:
    def __init__(self, name):
        self.name = name
        self.nodes = []
        self.items = []     # equipment schedule entries for plans / json

    def node(self, name, layer, **kw):
        n = Node(name, layer, **kw)
        self.nodes.append(n)
        return n


# ---- helpers that place things relative to the wall a unit backs onto ------------------
# side: 'R' backs onto right wall (front faces -x), 'L' left wall (+x), 'B' back wall (-y), 'F' front wall (+y)
def ulen(fp, side):
    x0, y0, x1, y1 = fp
    return (y1 - y0) if side in 'RL' else (x1 - x0)


def udepth(fp, side):
    x0, y0, x1, y1 = fp
    return (x1 - x0) if side in 'RL' else (y1 - y0)


def top_box(n, mat, fp, side, u0, u1, d0, d1, z0, z1):
    """u along the unit length, d = distance back from the front edge"""
    x0, y0, x1, y1 = fp
    if side == 'R': n.box(mat, x0 + d0, y0 + u0, z0, x0 + d1, y0 + u1, z1)
    elif side == 'L': n.box(mat, x1 - d1, y0 + u0, z0, x1 - d0, y0 + u1, z1)
    elif side == 'B': n.box(mat, x0 + u0, y0 + d0, z0, x0 + u1, y0 + d1, z1)
    else: n.box(mat, x0 + u0, y1 - d1, z0, x0 + u1, y1 - d0, z1)


def unit_point(fp, side, u, d, z):
    x0, y0, x1, y1 = fp
    if side == 'R': return (x0 + d, y0 + u, z)
    if side == 'L': return (x1 - d, y0 + u, z)
    if side == 'B': return (x0 + u, y0 + d, z)
    return (x0 + u, y1 - d, z)


def top_round(n, mat, fp, side, u0, u1, d0, d1, z0, z1, radius=0.008):
    n.rounded_box(mat, *unit_point(fp, side, u0, d0, z0), *unit_point(fp, side, u1, d1, z1), radius=radius)


def pull(n, fp, side, u, z0, z1, d=0.012):
    # All projections stay INSIDE the equipment footprint; d is measured from the front.
    for z in (z0, z1):
        n.tube('steel_edge', unit_point(fp, side, u, d, z), unit_point(fp, side, u, d + 0.031, z), 0.009)
    n.tube('steel_edge', unit_point(fp, side, u, d, z0), unit_point(fp, side, u, d, z1), 0.012)


def feet(n, fp, h=0.15):
    x0, y0, x1, y1 = fp
    for x in (x0 + 0.055, x1 - 0.055):
        for y in (y0 + 0.055, y1 - 0.055):
            n.cyl('gasket', x, y, 0, 0.018, 0.027, seg=12)
            n.cyl('steel_dark', x, y, 0.018, 0.055, 0.019, seg=12)
            n.cyl('steel_edge', x, y, 0.055, h + 0.025, 0.022, seg=12)


def face_box(n, mat, fp, side, u0, u1, z0, z1, t=0.012):
    top_box(n, mat, fp, side, u0, u1, -t, 0, z0, z1)


def top_cyl(n, mat, fp, side, u, d, z0, z1, r, **kw):
    x0, y0, x1, y1 = fp
    if side == 'R': n.cyl(mat, x0 + d, y0 + u, z0, z1, r, **kw)
    elif side == 'L': n.cyl(mat, x1 - d, y0 + u, z0, z1, r, **kw)
    elif side == 'B': n.cyl(mat, x0 + u, y0 + d, z0, z1, r, **kw)
    else: n.cyl(mat, x0 + u, y1 - d, z0, z1, r, **kw)


def open_table(n, fp, h=0.90, shelf=True, mat='steel', top=True):
    x0, y0, x1, y1 = fp
    if top: n.rounded_box(mat, x0, y0, h - 0.04, x1, y1, h, radius=0.010)
    feet(n, fp)
    for lx in (x0 + 0.03, x1 - 0.07):
        for ly in (y0 + 0.03, y1 - 0.07):
            n.rounded_box(mat, lx, ly, 0.15, lx + 0.04, ly + 0.04, h - 0.04, radius=0.004, segments=2)
    if shelf:
        n.rounded_box(mat, x0 + 0.03, y0 + 0.03, 0.15, x1 - 0.03, y1 - 0.03, 0.175, radius=0.005)


def cabinet(n, fp, side, h=0.90, doors=2, mat='steel'):
    L, dp = ulen(fp, side), udepth(fp, side)
    feet(n, fp)
    top_round(n, mat, fp, side, 0.008, L - 0.008, 0.075, dp - 0.008, 0.15, h - 0.045)
    top_round(n, 'steel_edge', fp, side, 0, L, 0, dp, h - 0.045, h, radius=0.009)
    top_box(n, 'gasket', fp, side, 0.018, L - 0.018, 0.068, 0.078, 0.172, h - 0.064)
    for i in range(doors):
        u0 = L * i / doors + (0.018 if i == 0 else 0.003)
        u1 = L * (i + 1) / doors - (0.018 if i == doors - 1 else 0.003)
        top_round(n, mat, fp, side, u0, u1, 0.040, 0.070, 0.183, h - 0.075, radius=0.006)
        pull(n, fp, side, u1 - 0.052, h - 0.36, h - 0.16)


def fridge(n, fp, side, h=2.0):
    L, dp = ulen(fp, side), udepth(fp, side)
    feet(n, fp, 0.13)
    top_round(n, 'steel', fp, side, 0.006, L - 0.006, 0.075, dp - 0.005, 0.13, h, radius=0.014)
    top_round(n, 'gasket', fp, side, 0.025, L - 0.025, 0.064, 0.078, 0.155, h - 0.275, radius=0.008)
    top_round(n, 'steel', fp, side, 0.035, L - 0.035, 0.035, 0.068, 0.167, h - 0.286, radius=0.009)
    pull(n, fp, side, L - 0.107, 0.93, 1.39)
    for z in (0.32, 1.52):
        top_round(n, 'steel_edge', fp, side, 0.028, 0.052, 0.028, 0.060, z, z + 0.065, radius=0.004)
    top_round(n, 'steel_dark', fp, side, 0.025, L - 0.025, 0.040, 0.077, h - 0.255, h - 0.027)
    for j in range(7):
        top_box(n, 'gasket', fp, side, 0.05, L - 0.22, 0.037, 0.041, h - 0.227 + j * 0.024, h - 0.218 + j * 0.024)
    top_round(n, 'black', fp, side, L - 0.185, L - 0.047, 0.031, 0.041, h - 0.19, h - 0.085, radius=0.004)
    # Seven-segment-like digital temperature indicator; no external font dependency.
    for u in (L - 0.15, L - 0.112):
        for zz in (h - 0.163, h - 0.138, h - 0.113):
            top_box(n, 'display', fp, side, u, u + 0.023, 0.029, 0.031, zz, zz + 0.003)
        top_box(n, 'display', fp, side, u + 0.020, u + 0.023, 0.029, 0.031, h - 0.160, h - 0.113)


def saladette(n, fp, side, h=0.90):
    L = ulen(fp, side); Dp = udepth(fp, side)
    cabinet(n, fp, side, h, doors=max(2, round(L / 0.47)))
    top_round(n, 'poly', fp, side, 0.03, L - 0.03, 0.02, 0.30, h, h + 0.022)
    top_round(n, 'steel', fp, side, 0, L, 0.33, Dp, h, h + 0.13)
    foods = ['f_green', 'f_red', 'f_yellow', 'f_white', 'f_purple', 'f_green', 'f_brown', 'f_red']
    k = max(3, int((L - 0.06) / 0.18))
    for i in range(k):
        u0 = 0.03 + (L - 0.06) * i / k + 0.01
        u1 = 0.03 + (L - 0.06) * (i + 1) / k - 0.01
        top_round(n, 'steel_edge', fp, side, u0, u1, 0.35, Dp - 0.025, h + 0.13, h + 0.142, radius=0.005)
        top_round(n, foods[i % len(foods)], fp, side, u0 + 0.009, u1 - 0.009, 0.36, Dp - 0.035, h + 0.142, h + 0.145, radius=0.003)
        for j in range(6):
            top_cyl(n, foods[i % len(foods)], fp, side, (u0 + u1) / 2 + (j % 2 - 0.5) * 0.04,
                    0.40 + (j // 2) * 0.08, h + 0.144, h + 0.155, 0.018, seg=7)
    top_box(n, 'glass', fp, side, 0, L, 0.33, 0.34, h + 0.13, h + 0.42)             # sneeze guard
    top_round(n, 'steel_edge', fp, side, 0, L, 0.33, Dp, h + 0.42, h + 0.44)
    for u in (0.025, L - 0.025):
        top_cyl(n, 'steel_edge', fp, side, u, 0.34, h + 0.13, h + 0.42, 0.012)


def bain_marie(n, fp, side, h=0.90):
    L = ulen(fp, side); Dp = udepth(fp, side)
    cabinet(n, fp, side, h - 0.02, doors=1)
    top_box(n, 'steel', fp, side, 0, L, 0, Dp, h - 0.02, h + 0.02)
    for i in range(2):
        for j in range(2):
            u0 = 0.04 + (L - 0.08) * i / 2 + 0.01; u1 = 0.04 + (L - 0.08) * (i + 1) / 2 - 0.01
            d0 = 0.06 + (Dp - 0.12) * j / 2 + 0.01; d1 = 0.06 + (Dp - 0.12) * (j + 1) / 2 - 0.01
            top_round(n, 'steel_edge', fp, side, u0, u1, d0, d1, h + 0.02, h + 0.038, radius=0.006)
            top_round(n, 'steel', fp, side, u0 + 0.009, u1 - 0.009, d0 + 0.009, d1 - 0.009, h + 0.038, h + 0.042, radius=0.003)
            top_cyl(n, 'black', fp, side, (u0 + u1) / 2, (d0 + d1) / 2, h + 0.035, h + 0.06, 0.018)
    for i in range(2):
        knob(n, fp, side, 0.13 + i * 0.14, h - 0.11)


def griddle(n, fp, side, h=0.90):
    x0, y0, x1, y1 = fp
    L = ulen(fp, side); Dp = udepth(fp, side)
    open_table(n, fp, 0.60)
    n.rounded_box('steel', x0 + 0.01, y0 + 0.01, 0.60, x1 - 0.01, y1 - 0.01, h - 0.04, radius=0.012)
    top_round(n, 'steel_dark', fp, side, 0.03, L - 0.03, 0.08, Dp - 0.06, h - 0.04, h - 0.02)
    top_box(n, 'steel', fp, side, 0.01, L - 0.01, Dp - 0.05, Dp - 0.02, h - 0.04, h + 0.10)  # rear splash
    top_box(n, 'steel', fp, side, 0.01, 0.03, 0.08, Dp - 0.02, h - 0.04, h + 0.06)
    top_box(n, 'steel', fp, side, L - 0.03, L - 0.01, 0.08, Dp - 0.02, h - 0.04, h + 0.06)
    for i in range(2):
        knob(n, fp, side, 0.15 + i * 0.3, 0.735)
    top_round(n, 'gasket', fp, side, 0.07, L - 0.07, 0.012, 0.020, 0.635, 0.677, radius=0.004)
    top_round(n, 'steel_edge', fp, side, 0.11, L - 0.11, 0.004, 0.015, 0.646, 0.663, radius=0.004)
    for i, m in enumerate(['f_brown', 'f_brown', 'f_yellow', 'f_brown']):                # food on the plate
        top_box(n, m, fp, side, 0.08 + i * 0.12, 0.17 + i * 0.12, 0.22, 0.36, h - 0.02, h - 0.005)


def gas_range(n, fp, side, h=0.90):
    x0, y0, x1, y1 = fp
    L = ulen(fp, side); Dp = udepth(fp, side)
    open_table(n, fp, 0.60)
    n.rounded_box('steel', x0 + 0.01, y0 + 0.01, 0.60, x1 - 0.01, y1 - 0.01, h - 0.05, radius=0.012)
    for i, d in enumerate((0.20, 0.50)):
        top_cyl(n, 'black', fp, side, L / 2, d, h - 0.05, h - 0.02, 0.12)
    top_cyl(n, 'steel', fp, side, L / 2, 0.50, h - 0.02, h + 0.22, 0.15)                 # pasta / sauce pot
    top_cyl(n, 'steel_edge', fp, side, L / 2, 0.50, h + 0.22, h + 0.232, 0.153)
    top_cyl(n, 'black', fp, side, L / 2, 0.50, h + 0.232, h + 0.252, 0.03)
    for u in (L / 2 - 0.19, L / 2 + 0.19):
        n.tube('steel_edge', unit_point(fp, side, u, 0.43, h + 0.13), unit_point(fp, side, u, 0.57, h + 0.13), 0.012)
    top_cyl(n, 'steel_dark', fp, side, L / 2, 0.20, h - 0.02, h + 0.05, 0.14)            # saute pan
    for i in range(2):
        knob(n, fp, side, 0.15 + i * 0.3, 0.735)


def knob(n, fp, side, u, z):
    n.tube('steel_edge', unit_point(fp, side, u, 0.035, z), unit_point(fp, side, u, 0.020, z), 0.033, seg=16)
    n.tube('black', unit_point(fp, side, u, 0.021, z), unit_point(fp, side, u, 0.001, z), 0.025, seg=16)
    top_box(n, 'white', fp, side, u - 0.002, u + 0.002, 0, 0.002, z + 0.010, z + 0.022)


def sink_deck(n, fp, side, holes, h=0.90, d0=0.07, d1=None, drop=0.18):
    """Split the top around actual bowl openings instead of painting dark rectangles on it."""
    L, dp = ulen(fp, side), udepth(fp, side)
    d1 = dp - 0.12 if d1 is None else d1
    for da, db in ((0, d0), (d1, dp)):
        top_round(n, 'steel_edge', fp, side, 0, L, da, db, h - 0.035, h, radius=0.006)
    start = 0
    for u0, u1 in holes:
        top_round(n, 'steel_edge', fp, side, start, u0, d0, d1, h - 0.035, h, radius=0.005)
        for a, b, c, d in ((u0, u0 + 0.009, d0, d1), (u1 - 0.009, u1, d0, d1),
                            (u0, u1, d0, d0 + 0.009), (u0, u1, d1 - 0.009, d1)):
            top_round(n, 'steel', fp, side, a, b, c, d, h - drop, h - 0.003, radius=0.003)
        top_round(n, 'steel_dark', fp, side, u0 + 0.009, u1 - 0.009, d0 + 0.009, d1 - 0.009, h - drop, h - drop + 0.01)
        top_cyl(n, 'steel_edge', fp, side, (u0 + u1) / 2, (d0 + d1) / 2, h - drop + 0.01, h - drop + 0.013, 0.027)
        top_cyl(n, 'gasket', fp, side, (u0 + u1) / 2, (d0 + d1) / 2, h - drop + 0.013, h - drop + 0.014, 0.012)
        start = u1
    top_round(n, 'steel_edge', fp, side, start, L, d0, d1, h - 0.035, h, radius=0.005)


def prep_table(n, fp, side):
    open_table(n, fp, top=False)
    sink_deck(n, fp, side, [(0.10, 0.50)], d0=0.08, d1=0.48)
    tap(n, fp, side, 0.30, 0.54, 0.90, 0.28)


def tap(n, fp, side, u, d, z, height=0.32):
    # A swept swan-neck tap, including a downward spout.
    pts = [(u, d, z), (u, d, z + height * 0.70)]
    for j in range(9):
        a = math.pi * j / 8
        pts.append((u, d - 0.09 + 0.09 * math.cos(a), z + height * 0.70 + 0.09 * math.sin(a)))
    pts.append((u, d - 0.18, z + height * 0.53))
    for a, b in zip(pts, pts[1:]):
        if a != b: n.tube('steel_edge', unit_point(fp, side, *a), unit_point(fp, side, *b), 0.011, seg=10)


def rice_bench(n, fp, side):
    L = ulen(fp, side); Dp = udepth(fp, side)
    open_table(n, fp, 0.55)
    top_cyl(n, 'white', fp, side, L * 0.5, 0.20, 0.55, 0.86, 0.17)
    top_cyl(n, 'steel', fp, side, L * 0.5, 0.20, 0.86, 0.89, 0.17, r_top=0.10)
    top_cyl(n, 'white', fp, side, L * 0.5, 0.52, 0.55, 0.86, 0.17)
    top_cyl(n, 'steel', fp, side, L * 0.5, 0.52, 0.86, 0.89, 0.17, r_top=0.10)


def sink2(n, fp, side, h=0.90):
    L = ulen(fp, side); Dp = udepth(fp, side)
    open_table(n, fp, h, top=False)
    holes = []
    for i in range(2):
        u0 = 0.06 + (L - 0.12) * i / 2 + 0.02; u1 = 0.06 + (L - 0.12) * (i + 1) / 2 - 0.02
        holes.append((u0, u1))
    sink_deck(n, fp, side, holes, h)
    top_box(n, 'steel', fp, side, 0, L, Dp - 0.02, Dp, h, h + 0.30)                       # splashback
    tap(n, fp, side, L / 2, Dp - 0.08, h)
    top_box(n, 'steel', fp, side, 0.05, L - 0.05, Dp - 0.30, Dp, 1.55, 1.57)              # drying shelf
    top_box(n, 'white', fp, side, L - 0.42, L - 0.07, Dp - 0.28, Dp, 1.85, 2.30)          # water heater


def basin(n, fp, side):
    L = ulen(fp, side); Dp = udepth(fp, side)
    sink_deck(n, fp, side, [(0.045, L - 0.045)], 0.86, d0=0.045, d1=Dp - 0.075, drop=0.15)
    tap(n, fp, side, L / 2, Dp - 0.04, 0.86, 0.20)
    top_box(n, 'steel', fp, side, 0.02, L - 0.02, Dp - 0.015, Dp, 0.86, 1.25)
    top_box(n, 'white', fp, side, L / 2 - 0.06, L / 2 + 0.06, Dp - 0.10, Dp, 1.35, 1.55)   # soap / towel
    top_round(n, 'steel_dark', fp, side, 0.10, L - 0.10, 0.002, 0.012, 0.40, 0.55)


def shelving(n, fp, h=2.0, tiers=5, goods=True):
    x0, y0, x1, y1 = fp
    for lx in (x0, x1 - 0.03):
        for ly in (y0, y1 - 0.03):
            n.box('alu', lx, ly, 0, lx + 0.03, ly + 0.03, h)
    for i in range(tiers):
        z = 0.15 + (h - 0.25) * i / (tiers - 1)
        n.box('steel', x0, y0, z, x1, y1, z + 0.025)
        if goods and i < tiers - 1:
            m = ['carton', 'f_white', 'carton', 'f_yellow'][i % 4]
            n.box(m, x0 + 0.05, y0 + 0.05, z + 0.025, x1 - 0.06, y0 + (y1 - y0) * 0.55, z + 0.30)
            n.box('carton', x0 + 0.05, y0 + (y1 - y0) * 0.6, z + 0.025, x1 - 0.06, y1 - 0.05, z + 0.24)


def person(n, x, y, cloth, z=0.0, hgt=1.70, facing=0, working=False):
    p = Node('figure', 'people')
    staff = cloth == 'cloth_staff'
    shirt = 'poly' if staff else cloth
    for sign in (-1, 1):
        hip = (sign * 0.082, 0, 0.88)
        knee = (sign * 0.090, -0.012, 0.49)
        ankle = (sign * 0.095, 0.0, 0.10)
        p.tube('ink', hip, knee, 0.071, seg=10, r_end=0.052)
        p.tube('ink', knee, ankle, 0.052, seg=10, r_end=0.038)
        p.rounded_box('black', sign * 0.095 - 0.052, -0.12, 0, sign * 0.095 + 0.052, 0.065, 0.095, radius=0.025, segments=2)
    # Tailored hips, waist, shoulders and collar.
    levels = [(0.84, 0.145, 0.086), (1.00, 0.145, 0.090), (1.29, 0.202, 0.105), (1.39, 0.123, 0.082)]
    for (za, wa, da), (zb, wb, db) in zip(levels, levels[1:]):
        for i in range(12):
            a, b = math.tau * i / 12, math.tau * (i + 1) / 12
            pts = [(wa * math.cos(a), da * math.sin(a), za), (wa * math.cos(b), da * math.sin(b), za),
                   (wb * math.cos(b), db * math.sin(b), zb), (wb * math.cos(a), db * math.sin(a), zb)]
            norm = np.cross(np.subtract(pts[1], pts[0]), np.subtract(pts[3], pts[0])); norm /= np.linalg.norm(norm)
            p._face(shirt, tuple(norm), pts)
    p.ellipsoid(shirt, (0, 0, 1.355), (0.125, 0.082, 0.05), rings=4)
    p.cyl('skin', 0, 0, 1.385, 1.49, 0.047, seg=10)
    p.ellipsoid('skin', (0, -0.007, 1.565), (0.088, 0.094, 0.123))
    p.ellipsoid('ink', (0, 0.006, 1.636), (0.089, 0.090, 0.060), rings=5)
    p.ellipsoid('skin', (0, -0.099, 1.565), (0.018, 0.022, 0.027), seg=8, rings=4)
    for sign in (-1, 1):
        p.ellipsoid('skin', (sign * 0.088, 0, 1.56), (0.018, 0.023, 0.032), seg=8, rings=5)
        shoulder = (sign * 0.184, 0, 1.285)
        elbow = (sign * 0.240, -0.025 if working else 0.005, 1.055)
        wrist = (sign * 0.205, -0.215 if working else -0.045, 1.025 if working else 0.85)
        p.ellipsoid(shirt, shoulder, (0.072, 0.074, 0.082), seg=10, rings=5)
        p.tube(shirt, shoulder, elbow, 0.068, seg=10, r_end=0.045)
        p.tube('skin', elbow, wrist, 0.043, seg=10, r_end=0.029)
        p.ellipsoid('skin', wrist, (0.034, 0.034, 0.054), seg=8, rings=5)
    if staff:
        p.quad('cloth_staff', (-0.10, -0.108, 1.02), (0.10, -0.108, 1.02), (0.105, -0.111, 1.32), (-0.105, -0.111, 1.32))
        p.quad('cloth_staff', (-0.165, -0.105, 0.67), (0.165, -0.105, 0.67), (0.145, -0.111, 1.04), (-0.145, -0.111, 1.04))
        for xx in (-0.085, 0.085):
            p.tube('cloth_staff', (xx, -0.106, 1.30), (xx * 0.8, -0.067, 1.39), 0.012, seg=6)
        p.box('forest', -0.15, -0.116, 1.01, 0.15, -0.109, 1.04)
        p.quad('forest', (-0.07, -0.118, 0.83), (0.07, -0.118, 0.83), (0.07, -0.118, 0.94), (-0.07, -0.118, 0.94))
        p.box('lime', -0.065, -0.122, 0.929, 0.065, -0.119, 0.936)
        p.ellipsoid('cloth_staff', (0, 0.009, 1.66), (0.092, 0.097, 0.039), rings=4)
        p.box('lime', -0.045, -0.122, 1.21, 0.045, -0.117, 1.225)
    s = hgt / 1.70; co, si = math.cos(facing), math.sin(facing)
    for mat, (pos, normals, uv, indices) in p.geo.items():
        P, N, U, I = n._g(mat); base = len(P)
        P.extend([(x + s * (co * a - si * b), y + s * (si * a + co * b), z + s * c) for a, b, c in pos])
        N.extend([(co * a - si * b, si * a + co * b, c) for a, b, c in normals])
        U.extend(uv); I.extend([base + i for i in indices])


# --------------------------------------------------------------------------------------
def build_shell(m, variant):
    t = SITE['wall_t']; st = SITE['step']; sw = SITE['sidewalk']
    f = m.node('shell/floor', 'shell'); f.box('floor', 0, 0, -0.05, W, D, 0)
    for nm, x0, x1 in (('wall_left', -t, 0), ('wall_right', W, W + t)):
        n = m.node('shell/' + nm, nm)
        n.box('tile', x0, -0.0, 0, x1, D + t, 2.10)
        n.box('paint', x0, -0.0, 2.10, x1, D + t, H)
    n = m.node('shell/wall_back', 'wall_back')
    n.box('tile', 0, D, 0, W, D + t, 2.10); n.box('paint', 0, D, 2.10, W, D + t, H)
    n = m.node('shell/ceiling', 'ceiling'); n.box('paint', -t, -t, H, W + t, D + t, H + 0.15)

    # ---------- shopfront (y from -wall_t to 0) ----------
    fr = m.node('front/structure', 'front')
    ox0, ox1 = SITE['open_x0'], SITE['open_x1']
    fr.box('stone', -t, -t, -st, ox0, 0, H)            # left pier
    fr.box('stone', ox1, -t, -st, W + t, 0, H)         # right pier
    fr.box('stone', ox0, -t, SITE['transom_top'], ox1, 0, H)   # lintel / shutter zone
    fr.box('shutter', ox0 - 0.03, -t - 0.10, SITE['transom_top'], ox1 + 0.03, -t, SITE['transom_top'] + 0.30)  # shutter box
    fr.box('stone', -0.0, -t - 0.30, -st, W, -t, 0)     # stone step / threshold (observed)
    fr.box('stone', ox0, -t, -st, ox1, 0, 0)

    g = m.node('front/glazing', 'front')
    dx0, dx1, wx0, wx1 = SITE['door_x0'], SITE['door_x1'], SITE['win_x0'], SITE['win_x1']
    hd, sill, tt = SITE['head'], SITE['sill'], SITE['transom_top']
    yg0, yg1 = -0.12, -0.07
    # door frame + leaf (existing hinged glass door, shown closed)
    for x in (dx0, dx1 - 0.04):
        g.box('alu', x, yg0, 0, x + 0.04, yg1, hd)
    g.box('alu', dx0, yg0, hd, dx1, yg1, hd + 0.05)
    for xx in (dx0 + 0.035, dx1 - 0.046):
        g.box('gasket', xx, yg0 + 0.011, 0.05, xx + 0.011, yg1 - 0.011, hd)
    g.box('glass', dx0 + 0.04, yg0 + 0.015, 0.05, dx1 - 0.04, yg1 - 0.015, hd)
    g.box('alu', dx0 + 0.04, yg0, 0, dx1 - 0.04, yg1, 0.05)
    for yy in (yg0 - 0.045, yg1 + 0.045):
        for zz in (0.98, 1.23):
            g.tube('steel_edge', (dx1 - 0.095, yy, zz), (dx1 - 0.095, (yg0 + yg1) / 2, zz), 0.009)
        g.tube('steel_edge', (dx1 - 0.095, yy, 0.98), (dx1 - 0.095, yy, 1.23), 0.012)
    # mullion between door and window
    g.box('alu', dx1, yg0, 0, wx0, yg1, tt)
    # transom: fresh-air louvre over the door, exhaust louvre at the far right, glass between
    ex0 = W - 0.65
    hb = round(W - 0.75, 2)      # layout B: right edge of the single hatch
    g.box('alu', dx0, yg0, tt - 0.04, wx1, yg1, tt)
    lv = m.node('front/louvres', 'front')
    for i in range(7):
        z = hd + 0.09 + i * 0.055
        lv.box('alu', dx0 + 0.04, yg0 - 0.01, z, dx1 - 0.02, yg1, z + 0.02)       # make-up air
        lv.box('steel_dark', ex0, yg0 - 0.01, z, wx1 - 0.02, yg1, z + 0.02)      # kitchen exhaust
    lv.box('black', dx0 + 0.04, yg1 - 0.01, hd + 0.06, dx1 - 0.02, yg1, tt - 0.04)
    lv.box('black', ex0, yg1 - 0.01, hd + 0.06, wx1 - 0.02, yg1, tt - 0.04)
    g.box('glass', wx0, yg0 + 0.015, hd + 0.05, ex0 - 0.03, yg1 - 0.015, tt - 0.04)
    g.box('alu', ex0 - 0.03, yg0, hd + 0.05, ex0, yg1, tt - 0.04)
    # service window
    wmid = (wx0 + wx1) / 2
    win_l, win_r = (wx0, wx1) if variant == 'A' else (wx0, hb)
    g.box('alu', wx0, yg0, hd, wx1, yg1, hd + 0.05)
    g.box('alu', wx1 - 0.04, yg0, 0, wx1, yg1, tt)
    if variant == 'A':
        g.box('alu', wmid - 0.02, yg0, sill, wmid + 0.02, yg1, hd)
        g.box('glass', wmid + 0.02, yg0 + 0.03, sill + 0.55, wx1 - 0.04, yg1 - 0.005, hd)   # collect sash (shown half open)
        g.box('glass', wx0, yg0 + 0.005, sill + 0.55, wmid - 0.02, yg1 - 0.03, hd)          # order sash (half open)
    else:
        g.box('alu', hb, yg0, 0, hb + 0.04, yg1, hd)
        g.box('glass', wx0, yg0 + 0.005, sill + 0.55, hb, yg1 - 0.03, hd)                 # single hatch
        g.box('glass', hb + 0.04, yg0 + 0.015, 0.05, wx1 - 0.04, yg1 - 0.015, hd)                # fixed show-glass at the grill
    spans = [(wx0 + 0.018, wmid - 0.025, yg0 + 0.005), (wmid + 0.025, wx1 - 0.045, yg0 + 0.030)] if variant == 'A' else [(wx0 + 0.018, hb - 0.015, yg0 + 0.005)]
    for a, b, yy in spans:
        for zz in (sill + 0.535, hd - 0.015):
            g.rounded_box('alu', a, yy - 0.010, zz, b, yy + 0.012, zz + 0.025, radius=0.004)
        for xx in (a, b - 0.018):
            g.rounded_box('alu', xx, yy - 0.010, sill + 0.55, xx + 0.018, yy + 0.012, hd, radius=0.003)
        g.rounded_box('steel_edge', (a + b) / 2 - 0.065, yy - 0.023, sill + 0.575, (a + b) / 2 + 0.065, yy - 0.009, sill + 0.590, radius=0.004)
    for zz in (sill + 0.008, hd + 0.002):
        g.box('gasket', win_l, yg0 - 0.008, zz, win_r, yg1, zz + 0.006)
    ap = m.node('front/apron', 'front')
    ap.box('forest', win_l, yg0, 0, win_r, yg1 + 0.05, sill - 0.04)
    ap.quad('t_apron', (win_l, yg0 - 0.003, 0.0), (win_r, yg0 - 0.003, 0.0),
            (win_r, yg0 - 0.003, sill - 0.04), (win_l, yg0 - 0.003, sill - 0.04))
    # outside shelf / ledge (replaces the existing fold-out shelf)
    ap.rounded_box('paint', win_l - 0.02, -t - 0.22, sill - 0.04, win_r + 0.02, 0.0, sill, radius=0.012)
    ap.box('steel_edge', win_l, -t - 0.222, sill - 0.047, win_r, -t - 0.208, sill - 0.040)
    # window labels on the head rail
    lab = m.node('front/labels', 'front')
    zl0, zl1 = hd - 0.19, hd - 0.01
    if variant == 'A':
        lab.quad('t_order', (wx0 + 0.02, yg0 - 0.006, zl0), (wmid - 0.03, yg0 - 0.006, zl0), (wmid - 0.03, yg0 - 0.006, zl1), (wx0 + 0.02, yg0 - 0.006, zl1))
        lab.quad('t_collect', (wmid + 0.03, yg0 - 0.006, zl0), (wx1 - 0.05, yg0 - 0.006, zl0), (wx1 - 0.05, yg0 - 0.006, zl1), (wmid + 0.03, yg0 - 0.006, zl1))
    else:
        lab.quad('t_order', (wx0 + 0.02, yg0 - 0.006, zl0), (hb - 0.01, yg0 - 0.006, zl0), (hb - 0.01, yg0 - 0.006, zl1), (wx0 + 0.02, yg0 - 0.006, zl1))

    # ---------- fascia sign, blade sign, menu board ----------
    s = m.node('front/sign', 'front')
    sz0, sz1 = SITE['transom_top'] + 0.32, SITE['transom_top'] + 1.10
    s.box('forest', -t - 0.05, -t - 0.16, sz0, W + t + 0.05, -t, sz1)
    s.quad('t_sign', (-t - 0.05, -t - 0.163, sz0), (W + t + 0.05, -t - 0.163, sz0), (W + t + 0.05, -t - 0.163, sz1), (-t - 0.05, -t - 0.163, sz1))
    s.box('lime', W + t - 0.04, -t - 0.62, 2.30, W + t, -t - 0.16, 2.76)              # blade sign (projecting)
    s.quad('t_blade', (W + t - 0.043, -t - 0.62, 2.30), (W + t - 0.043, -t - 0.16, 2.30), (W + t - 0.043, -t - 0.16, 2.76), (W + t - 0.043, -t - 0.62, 2.76))
    s.quad('t_blade', (W + t + 0.003, -t - 0.16, 2.30), (W + t + 0.003, -t - 0.62, 2.30), (W + t + 0.003, -t - 0.62, 2.76), (W + t + 0.003, -t - 0.16, 2.76))
    s.box('ink', ox1 + 0.02, -t - 0.03, 0.75, W + t - 0.02, -t, 1.95)                 # menu board on the right pier
    s.quad('t_menu', (ox1 + 0.03, -t - 0.033, 0.77), (W + t - 0.03, -t - 0.033, 0.77), (W + t - 0.03, -t - 0.033, 1.93), (ox1 + 0.03, -t - 0.033, 1.93))
    for i in range(4):                                                                 # fascia downlights (existing pattern)
        s.cyl('white', 0.3 + i * 0.66, -t - 0.08, sz0 - 0.02, sz0, 0.06, seg=12)

    # ---------- street context ----------
    c = m.node('site/sidewalk', 'site')
    c.box('pave', -3.2, -t - sw, -st - 0.12, W + 3.2, -t, -st)
    c.box('stone', -3.2, -t - sw - 0.15, -st - 0.12, W + 3.2, -t - sw, -st + 0.0)
    c.box('asphalt', -3.2, -t - sw - 2.0, -st - 0.25, W + 3.2, -t - sw - 0.15, -st - 0.13)
    c.cyl('steel_dark', 0.95, -t - 0.85, -st, -st + 0.012, 0.30, seg=24)               # manhole cover (observed)
    tr = m.node('site/tree', 'site')
    tr.cyl('trunk', -2.3, -t - sw + 0.45, -st, 3.2, 0.22, seg=12, r_top=0.16)
    tr.sphere('leaf', -2.3, -t - sw + 0.45, 3.9, 1.05, seg=12, rings=8)
    cx = m.node('site/neighbours', 'context')
    cx.box('context', -3.2, -t, -st, -t, 0.3, 4.2)       # Alnawras menswear (left)
    cx.box('glass', -2.9, -t - 0.02, 0.0, -0.45, -t, 2.4)
    cx.box('context', W + t, -t, -st, W + 3.2, 0.3, 4.2)  # closed shutter (right)
    cx.box('shutter', W + t + 0.15, -t - 0.03, -st, W + 3.0, -t, 2.6)
    cx.box('context', -3.2, -t, 4.2, W + 3.2, 0.3, 6.2)   # building above
    cx.box('white', 0.6, -t - 0.35, 4.45, 1.5, -t, 5.05)  # AC condenser on the facade (ASSUMED position)
    # queue markings on the sidewalk
    q = m.node('site/queue_marks', 'site')
    if variant == 'A':
        for i in range(3):
            q.box('lime', 1.20, -t - 0.75 - i * 0.80, -st, 1.55, -t - 0.70 - i * 0.80, -st + 0.006)
        q.box('forest', wmid + 0.12, -t - 0.75, -st, wmid + 0.72, -t - 0.70, -st + 0.006)
    else:
        for i in range(3):
            q.box('lime', 1.25, -t - 0.75 - i * 0.80, -st, 1.60, -t - 0.70 - i * 0.80, -st + 0.006)


def people(m, variant, staff):
    t = SITE['wall_t']; st = SITE['step']
    p = m.node('people/staff', 'people_in')
    for i, (x, y) in enumerate(staff):
        facing = 0 if i == 0 else math.pi / 2
        person(p, x, y, 'cloth_staff', facing=facing, working=True)
    o = m.node('people/customers', 'people_out')
    if variant == 'A':
        person(o, 1.38, -t - 0.72, 'cloth_a', z=-st, facing=math.pi, working=True)
        person(o, 1.38, -t - 1.55, 'cloth_b', z=-st, hgt=1.62, facing=math.pi * 0.95)
        person(o, (SITE['win_x0'] + SITE['win_x1']) / 2 + 0.42, -t - 0.72, 'cloth_c', z=-st, hgt=1.66, facing=math.pi, working=True)
        person(o, 3.25, -t - 2.9, 'cloth_b', z=-st)       # delivery rider waiting kerb-side
        o.box('forest', 3.05, -t - 3.25, -st + 1.0, 3.45, -t - 3.05, -st + 1.42)   # rider's box
    else:
        person(o, 1.42, -t - 0.72, 'cloth_a', z=-st, facing=math.pi, working=True)
        person(o, 1.42, -t - 1.55, 'cloth_b', z=-st, hgt=1.62, facing=math.pi)
        person(o, 1.42, -t - 2.35, 'cloth_c', z=-st, hgt=1.66, facing=math.pi)


# --------------------------------------------------------------------------------------
def add(m, code, name, fp, side, builder, cat, h=0.90, note='', ar=None, **kw):
    n = m.node(f'equip/{code} {name}', 'equip', label=name, code=code, label_ar=ar,
               anchor=((fp[0] + fp[2]) / 2, (fp[1] + fp[3]) / 2, h + 0.05))
    builder(n, fp, side, **kw) if side else builder(n, fp, **kw)
    m.items.append(dict(code=code, name=name, x0=fp[0], y0=fp[1], x1=fp[2], y1=fp[3], h=h, cat=cat, note=note))
    return n


def wall_shelf(m, name, fp, z, tiers=1):
    n = m.node('equip/' + name, 'shelves')
    for i in range(tiers):
        n.box('steel', fp[0], fp[1], z + i * 0.38, fp[2], fp[3], z + i * 0.38 + 0.02)
        n.box('carton', fp[0] + 0.03, fp[1] + 0.05, z + i * 0.38 + 0.02, fp[2] - 0.03, min(fp[3] - 0.05, fp[1] + 0.45), z + i * 0.38 + 0.22)
    return n


def service_counter(n, fp, variant):
    x0, y0, x1, y1 = fp
    n.rounded_box('paint', x0, y0 - 0.07, 0.86, x1, y1, 0.90, radius=0.012)
    for lx in (x0 + 0.02, x1 - 0.06):
        n.box('steel', lx, y1 - 0.06, 0, lx + 0.04, y1 - 0.02, 0.86)
    # POS tablet + printer at the order side
    n.box('black', x0 + 0.22, y0 + 0.16, 0.90, x0 + 0.50, y0 + 0.20, 1.12)
    n.box('steel_dark', x0 + 0.30, y0 + 0.14, 0.90, x0 + 0.42, y0 + 0.26, 0.92)
    n.box('white', x0 + 0.04, y0 + 0.22, 0.90, x0 + 0.18, y0 + 0.40, 1.02)
    if variant == 'A':                                              # bagged orders waiting at the collect side
        for i in range(2):
            n.box('carton', x0 + 0.95 + i * 0.27, y0 + 0.08, 0.90, x0 + 1.15 + i * 0.27, y0 + 0.24, 1.16)


def hood(m, fp, duct, fan):
    n = m.node('mep/hood', 'mep', label='Extraction hood', label_ar='شفّاط (هود)', code='E08', anchor=((fp[0] + fp[2]) / 2, (fp[1] + fp[3]) / 2, 2.2))
    x0, y0, x1, y1 = fp
    n.rounded_box('steel', x0, y0, 2.05, x1, y1, 2.40, radius=0.010)
    n.box('gasket', x0 + 0.025, y0 + 0.025, 2.045, x1 - 0.025, y1 - 0.025, 2.051)
    for a, b, c, d in ((x0, x0 + 0.032, y0, y1), (x1 - 0.032, x1, y0, y1),
                        (x0, x1, y0, y0 + 0.032), (x0, x1, y1 - 0.032, y1)):
        n.rounded_box('steel_edge', a, c, 1.95, b, d, 2.055, radius=0.008)
    count = max(2, round((y1 - y0) / 0.45))
    for i in range(count):
        a = y0 + 0.055 + (y1 - y0 - 0.11) * i / count
        b = y0 + 0.055 + (y1 - y0 - 0.11) * (i + 1) / count - 0.016
        n.box('steel_dark', x0 + 0.12, a, 2.038, x1 - 0.055, b, 2.043)
        for yy in (a, b - 0.012):
            n.tube('steel_edge', (x0 + 0.12, yy, 1.99), (x1 - 0.06, yy, 2.04), 0.009)
        for j in range(9):
            xx = x0 + 0.135 + j * (x1 - x0 - 0.22) / 9
            zz = 1.985 + (xx - x0 - 0.12) * 0.045
            # Folded channels face downward into the capture recess.
            n.quad('steel_edge', (xx, b - 0.01, zz + 0.014), (xx + 0.022, b - 0.01, zz),
                   (xx + 0.022, a + 0.01, zz), (xx, a + 0.01, zz + 0.014))
            n.quad('steel_edge', (xx + 0.022, b - 0.01, zz), (xx + 0.044, b - 0.01, zz + 0.014),
                   (xx + 0.044, a + 0.01, zz + 0.014), (xx + 0.022, a + 0.01, zz))
        n.tube('steel_edge', (x0 + 0.11, (a + b) / 2 - 0.04, 1.98), (x0 + 0.11, (a + b) / 2 + 0.04, 1.98), 0.007)
    d = m.node('mep/duct', 'mep')
    for b in duct:
        d.rounded_box('alu', *b, radius=0.008)
        xa, ya, za, xb, yb, zb = b
        if yb - ya > 1:
            for j in range(1, math.ceil((yb - ya) / 0.7)):
                yy = ya + j * 0.7
                d.box('steel_edge', xa - 0.005, yy, za - 0.005, xb + 0.005, yy + 0.018, zb + 0.005)
            for yy in (ya + 0.2, yb - 0.2):
                d.tube('steel_dark', (xa - 0.018, yy, za), (xa - 0.018, yy, H), 0.006)
    if fan:
        d.rounded_box('steel_dark', *fan, radius=0.018)
    return n


def flow_path(m, raw_pts, rte_pts):
    n = m.node('flow/paths', 'flow')
    for mat, pts in (('flow_raw', raw_pts), ('flow_rte', rte_pts)):
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            wdt = 0.035
            if abs(ax - bx) < 1e-6:
                n.box(mat, ax - wdt, min(ay, by) - wdt, 0.004, ax + wdt, max(ay, by) + wdt, 0.012)
            else:
                n.box(mat, min(ax, bx) - wdt, ay - wdt, 0.004, max(ax, bx) + wdt, ay + wdt, 0.012)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            n.arrow(mat, mx - (bx - ax) * 0.0, my, bx - ax, by - ay, size=0.13, z1=0.02)
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        n.arrow(mat, bx, by, bx - ax, by - ay, size=0.16, z1=0.02)


def retained_wc(m):
    """Retain the owner-confirmed rear-left toilet; its envelope is still provisional."""
    x, y, t = SITE['wc_w'], SITE['wc_y0'], SITE['wc_wall']
    if W - 0.70 - x < SITE['wc_access_min'] - 1e-6:
        raise ValueError('WC access below design allowance: revise equipment / survey width')
    a = y + t + 0.015
    b = a + SITE['wc_door']
    m.rooms = [dict(code='WC', name='Retained toilet / accordion door', label_ar='حمّام محفوظ / باب أكورديون',
                    x0=0, y0=y, x1=x, y1=D, status='location confirmed; envelope, partitions and opening ASSUMED',
                    door=dict(side='right', y0=a, y1=b, type='accordion', assumed=True), access=W - 0.70 - x)]
    low = m.node('wc/partitions-low', 'wc', code='WC', label='Retained WC - size assumed', label_ar='حمّام محفوظ - المقاس افتراضي', anchor=(x / 2, y + 0.7, 1.35))
    upper = m.node('wc/partitions-upper', 'wc_upper')
    for node, z0, z1 in ((low, 0, 1.12), (upper, 1.12, H)):
        node.box('tile', 0, y, z0, x, y + t, z1)
        for u, v in ((y + t, a), (b, D)):
            node.box('tile', x - t, u, z0, x, v, z1)
    upper.box('paint', x - t, a, 2.05, x, b, H)
    low.box('floor', 0, y + t, 0.002, x - t, D, 0.012)
    door = m.node('wc/accordion-door', 'wc')
    for yy in (a, b - 0.018):
        door.box('alu', x - t - 0.005, yy, 0, x + 0.005, yy + 0.018, 2.05)
    door.box('alu', x - t, a, 2.035, x, b, 2.065)
    # Shown folded inside the opening: no hinged sweep consumes the aisle.
    for i in range(8):
        yy = a + 0.018 + i * 0.011
        xx = x - 0.045 if i % 2 else x - 0.095
        door.quad('fold_panel', (xx, yy, 0.035), (x - 0.07, yy + 0.011, 0.035),
                  (x - 0.07, yy + 0.011, 2.01), (xx, yy, 2.01))
    door.tube('steel_edge', (x - 0.02, a + 0.12, 0.88), (x - 0.02, a + 0.12, 1.11), 0.010)
    fixtures = m.node('wc/toilet-and-basin', 'wc')
    cx, cy = x * 0.46, D - 0.45
    fixtures.rounded_box('white', cx - 0.22, D - 0.18, 0.43, cx + 0.22, D - 0.035, 0.84, radius=0.04)
    fixtures.cyl('white', cx, cy + 0.04, 0.02, 0.33, 0.12, seg=18)
    fixtures.ellipsoid('white', (cx, cy, 0.28), (0.20, 0.28, 0.15))
    fixtures.ellipsoid('steel_dark', (cx, cy - 0.025, 0.442), (0.15, 0.22, 0.014))
    # Elliptical seat ring, open in the middle.
    for i in range(28):
        aa, bb = math.tau * i / 28, math.tau * (i + 1) / 28
        fixtures.tube('white', (cx + 0.18 * math.cos(aa), cy - 0.025 + 0.25 * math.sin(aa), 0.45),
                      (cx + 0.18 * math.cos(bb), cy - 0.025 + 0.25 * math.sin(bb), 0.45), 0.024, seg=6)
    fixtures.cyl('steel_edge', cx, D - 0.105, 0.84, 0.849, 0.025)
    basin(fixtures, (0.01, y + 0.15, 0.34, y + 0.48), 'L')
    vent = m.node('wc/separate-extract-placeholder', 'wc_upper')
    vent.box('white', 0.32, D - 0.035, 2.42, 0.57, D, 2.67)
    for i in range(5): vent.box('gasket', 0.35, D - 0.038, 2.45 + i * 0.038, 0.54, D - 0.034, 2.462 + i * 0.038)


def compact_left_bank(m):
    # Two narrower upright units free enough wall length for the wash sink before the WC.
    add(m, 'E14', 'Hand-wash basin', (0, 0.90, 0.40, 1.30), 'L', basin, 'wash', h=0.86, ar='مغسلة أيدي')
    add(m, 'E13', 'Compact chiller A (raw / dairy)', (0, 1.35, 0.70, 1.95), 'L', fridge, 'cold', h=2.0, ar='برّاد مدمج A (نيء / ألبان)')
    add(m, 'E12', 'Compact chiller B (veg / ready)', (0, 1.95, 0.70, 2.55), 'L', fridge, 'cold', h=2.0, ar='برّاد مدمج B (خضار / جاهز)')
    wy = SITE['wc_y0']
    add(m, 'E10', 'Compact 2-bowl wash sink', (0, wy - 0.90, 0.60, wy), 'L', sink2, 'wash', ar='مجلى بحوضين قبل الحمّام')
    fp = (0, 1.35, 0.32, 2.55)
    n = m.node('equip/E11 closed dry storage', 'shelves', code='E11', label='High dry-storage cupboard', label_ar='خزانة مواد جافة علوية', anchor=(0.18, 2.0, 2.55))
    n.rounded_box('forest', *fp[:2], 2.12, *fp[2:], 2.55)
    for yy in (1.65, 2.24): n.box('lime', 0.321, yy, 2.26, 0.329, yy + 0.08, 2.30)
    m.items.append(dict(code='E11', name='High dry-storage cupboard', x0=0, y0=1.35, x1=0.32, y1=2.55, h=2.12, cat='overhead', note='closed storage above compact chillers; capacity by supplier'))


def wc_rear_prep(m):
    fp = (SITE['wc_w'], D - 0.60, W, D)
    n = add(m, 'E09', 'Short prep table + produce sink', fp, 'B', prep_table, 'prep', ar='تحضير + حوض خضار يمين الحمّام')
    length = ulen(fp, 'B')
    top_box(n, 'steel', fp, 'B', 0.59, 0.61, 0, 0.60, 0.90, 1.15)
    top_round(n, 'f_red', fp, 'B', 0.70, length - 0.07, 0.10, 0.45, 0.90, 0.915, radius=0.004)
    wall_shelf(m, 'E21 shelf over prep', (SITE['wc_w'] + 0.04, D - 0.28, W - 0.05, D), 1.50, 2)


def layout_A():
    m = Model('A')
    build_shell(m, 'A')
    R = round(W - 0.70, 2)          # front edge of the right-hand line
    add(m, 'E01', 'Service counter + POS', (1.00, 0.0, W, 0.50), None, lambda n, fp: service_counter(n, fp, 'A'), 'service', ar='كاونتر الخدمة + الكاشير')
    add(m, 'E02', 'Packing bench', (R, 0.50, W, 1.10), 'R', cabinet, 'service', ar='طاولة التعبئة')
    add(m, 'E03', 'Refrigerated prep counter', (R, 1.10, W, 2.30), 'R', saladette, 'cold', ar='برّاد تحضير (سلطات)')
    add(m, 'E04', 'Bain-marie (hot hold)', (R, 2.30, W, 2.86), 'R', bain_marie, 'hot', ar='بان ماري (حفظ ساخن)')
    add(m, 'E05', 'Gas griddle', (R, 2.86, W, 3.46), 'R', griddle, 'hot', ar='شوّاية مسطّحة (غاز)')
    add(m, 'E06', '2-burner range', (R, 3.46, W, 4.06), 'R', gas_range, 'hot', ar='موقد غاز بعينين')
    add(m, 'E07', 'Rice cookers', (R, 4.06, W, 4.46), 'R', rice_bench, 'hot', h=0.55, ar='طناجر الرز')
    hood(m, (R - 0.12, 2.76, W, 4.46),
         duct=[(W - 0.40, 3.6, 2.40, W - 0.05, 3.9, 2.70), (W - 0.38, 0.02, 2.62, W - 0.03, 3.9, 2.90)],
         fan=(W - 0.48, 0.05, 2.45, W, 0.60, 2.95))
    m.items.append(dict(code='E08', name='Hood 1.70 x 0.82 + duct + fan (overhead)', x0=R - 0.12, y0=2.76, x1=W, y1=4.46, h=1.95, cat='overhead', note='duct at ceiling along right wall to facade louvre'))
    retained_wc(m)
    compact_left_bank(m)
    wc_rear_prep(m)
    lx0, lx1 = round(W - 0.65, 2), round(W - 0.04, 2)
    n = m.node('equip/E15 LPG locker', 'equip', label='LPG locker (outside access)', label_ar='خزانة الغاز (تُفتح من الخارج)', code='E15', anchor=((lx0 + lx1) / 2, 0.25, 0.8))
    n.box('steel_dark', lx0, 0.0, 0.0, lx1, 0.45, 0.80)
    n.cyl('red', lx0 + 0.17, 0.22, 0.02, 0.62, 0.13, seg=14); n.cyl('red', lx0 + 0.45, 0.22, 0.02, 0.62, 0.13, seg=14)
    m.items.append(dict(code='E15', name='LPG locker (2 cyl., outside access)', x0=lx0, y0=0.0, x1=lx1, y1=0.45, h=0.8, cat='under', note='under counter, sealed to interior'))
    n = m.node('equip/E16 Inverter + battery', 'equip', label='Inverter + battery', label_ar='إنفرتر + بطارية', code='E16', anchor=(1.3, 0.25, 0.8))
    n.box('white', 1.03, 0.04, 0.05, 1.58, 0.42, 0.80)
    m.items.append(dict(code='E16', name='Inverter + LiFePO4 battery', x0=1.03, y0=0.04, x1=1.58, y1=0.42, h=0.8, cat='under', note='under counter'))
    n = m.node('equip/E19 Waste bins', 'equip')
    n.box('ink', 1.66, 0.06, 0, 2.02, 0.42, 0.62); n.box('ink', 1.36, 4.58, 0.18, 1.71, 4.98, 0.74)
    m.items.append(dict(code='E19', name='Pedal bin', x0=1.66, y0=0.06, x1=2.02, y1=0.42, h=0.62, cat='under', note=''))
    m.items.append(dict(code='E19', name='Pedal bin', x0=1.36, y0=4.58, x1=1.71, y1=4.98, h=0.74, cat='under', note=''))
    n = m.node('equip/E17 Split AC', 'equip'); n.box('white', 0.0, 0.95, 2.60, 0.22, 1.85, 2.90)
    m.items.append(dict(code='E17', name='Split AC (high level)', x0=0.0, y0=0.95, x1=0.22, y1=1.85, h=2.60, cat='overhead', note=''))
    wall_shelf(m, 'E21 shelf over packing', (W - 0.32, 0.55, W, 1.08), 1.50, 2)
    n = m.node('equip/E20 High storage shelf', 'highshelf'); n.box('steel', 0.02, 0.25, 2.28, 1.85, 0.95, 2.31)
    for i in range(4):
        n.box('carton', 0.08 + i * 0.44, 0.30, 2.31, 0.46 + i * 0.44, 0.90, 2.72)
    m.items.append(dict(code='E20', name='High-level packaging shelf (2.28 m)', x0=0.02, y0=0.25, x1=1.85, y1=0.95, h=2.28, cat='overhead', note=''))
    n = m.node('equip/E23 Fire extinguisher', 'equip'); n.cyl('red', 0.08, 0.90, 0.9, 1.35, 0.06, seg=12)
    n = m.node('equip/DB Electrical board', 'equip'); n.box('white', W - 0.04, 0.60, 1.95, W, 1.00, 2.45)
    sx = round(R - 0.34, 2)
    staff = [(1.48, 0.82), (sx, 1.90), (sx, 3.25)]
    people(m, 'A', staff)
    flow_path(m,
              raw_pts=[(0.55, 0.45), (0.98, 0.45), (0.98, 2.90), (1.62, 2.90), (1.62, 4.20)],
              rte_pts=[(R - 0.18, 3.25), (1.42, 3.25), (1.42, 2.40), (1.42, 1.60), (1.42, 0.62)])
    rx = W - 0.35
    m.stations = [  # numbered workflow labels (x, y, z, English, Arabic)
        (0.50, 0.25, 1.2, '1 Receiving (staff door)', '1 الاستلام (باب الموظفين)'),
        (0.35, 2.10, 2.1, '2 Cold + dry storage', '2 التخزين المبرّد والجاف'),
        (1.78, 4.76, 1.2, '3 Wash + raw prep', '3 الغسل وتحضير النيء'),
        (rx, 3.50, 1.3, '4 Cook (griddle / range / rice)', '4 الطهي (شوّاية / موقد / رز)'),
        (rx, 2.56, 1.3, '5 Hot hold', '5 الحفظ الساخن'), (rx, 1.75, 1.5, '6 Assemble', '6 تجميع الطلب'),
        (rx, 0.80, 1.3, '7 Pack + label', '7 التعبئة والملصق'),
        ((1.0 + W) / 2 + 0.4, -0.05, 1.25, '8 Hand-off', '8 التسليم'),
    ]
    m.staff = staff
    details.dress(m, 'A', globals())
    return m


def layout_B():
    m = Model('B')
    build_shell(m, 'B')
    R = round(W - 0.70, 2)
    hb = round(W - 0.75, 2)
    add(m, 'E01', 'Service counter + POS', (1.00, 0.0, hb + 0.02, 0.50), None, lambda n, fp: service_counter(n, fp, 'B'), 'service', ar='كاونتر الخدمة + الكاشير')
    add(m, 'E05', 'Griddle (behind show-glass)', (R, 0.08, W, 0.68), 'R', griddle, 'hot', ar='شوّاية مسطّحة (خلف زجاج العرض)')
    add(m, 'E06', '2-burner range', (R, 0.68, W, 1.28), 'R', gas_range, 'hot', ar='موقد بعينين')
    add(m, 'E07', 'Rice cookers', (R, 1.28, W, 1.68), 'R', rice_bench, 'hot', h=0.55, ar='طناجر الرز')
    add(m, 'E04', 'Bain-marie (hot hold)', (R, 1.72, W, 2.28), 'R', bain_marie, 'hot', ar='بان ماري (حفظ ساخن)')
    hood(m, (R - 0.12, 0.02, W, 1.95), duct=[(W - 0.50, 0.02, 2.40, W - 0.05, 0.50, 2.55)], fan=None)
    m.items.append(dict(code='E08', name='Hood 1.9 x 0.82, duct < 1 m (overhead)', x0=R - 0.12, y0=0.02, x1=W, y1=1.95, h=1.95, cat='overhead', note=''))
    retained_wc(m)
    compact_left_bank(m)
    wc_rear_prep(m)
    add(m, 'E03', 'Compact refrigerated prep counter', (R, 2.30, W, 3.50), 'R', saladette, 'cold', ar='برّاد تحضير مدمج')
    add(m, 'E02', 'Packing bench', (R, 3.52, W, 4.12), 'R', cabinet, 'service', ar='طاولة التعبئة')
    n = m.node('equip/E16 Inverter + battery', 'equip'); n.box('white', 1.03, 0.04, 0.05, 1.58, 0.42, 0.80)
    m.items.append(dict(code='E16', name='Inverter + LiFePO4 battery', x0=1.03, y0=0.04, x1=1.58, y1=0.42, h=0.8, cat='under', note='under counter'))
    n = m.node('equip/E17 Split AC', 'equip'); n.box('white', 0.0, 0.95, 2.60, 0.22, 1.85, 2.90)
    m.items.append(dict(code='E17', name='Split AC (high level)', x0=0.0, y0=0.95, x1=0.22, y1=1.85, h=2.60, cat='overhead', note=''))
    staff = [(1.45, 0.80), (round(R - 0.34, 2), 1.35), (round(R - 0.34, 2), 2.90)]
    people(m, 'B', staff)
    flow_path(m,
              raw_pts=[(0.55, 0.45), (1.00, 0.45), (1.00, 2.90), (1.65, 2.90), (1.65, 4.20)],
              rte_pts=[(R - 0.18, 4.20), (R - 0.18, 2.20), (R - 0.18, 1.00), (1.25, 1.00), (1.25, 2.60)])
    rx = W - 0.35
    m.stations = [
        (0.50, 0.25, 1.2, '1 Receiving', '1 الاستلام'), (0.35, 1.95, 2.1, '2 Compact cold storage', '2 التخزين المبرّد المدمج'),
        (1.78, 4.76, 1.2, '3 Wash + raw prep', '3 الغسل وتحضير النيء'), (rx, 0.95, 1.3, '4 Cook at the front', '4 الطهي عند الواجهة'),
        (rx, 2.18, 1.3, '5 Hot hold', '5 الحفظ الساخن'), (rx, 2.90, 1.5, '6 Assemble', '6 تجميع الطلب'),
        (rx, 3.80, 1.3, '7 Pack (return to front hatch)', '7 التعبئة والعودة للواجهة'), ((1.0 + hb) / 2, -0.05, 1.25, '8 Single hatch: order + collect', '8 نافذة واحدة: طلب + استلام'),
    ]
    m.staff = staff
    details.dress(m, 'B', globals())
    return m


# --------------------------------------------------------------------------------------
def to_gl(p):       # z-up (x,y,z) -> glTF y-up
    return (p[0], p[2], -p[1])


METALS = {'steel', 'steel_edge', 'steel_dark', 'alu'}


def make_metal_textures():
    """Deterministic glTF packed roughness (G) / metalness (B) and subtle brush normals."""
    os.makedirs(TEX, exist_ok=True)
    rng = np.random.default_rng(27)
    n = 256
    grain = rng.normal(0, 1, (n, 1)) * 0.75 + rng.normal(0, 0.25, (n, n))
    packed = np.empty((n, n, 3), dtype=np.uint8)
    packed[:, :, 0] = 255
    packed[:, :, 1] = np.clip(230 + grain * 8, 205, 250).astype(np.uint8)
    packed[:, :, 2] = 250
    normal = np.empty_like(packed)
    normal[:, :, 0] = 128
    normal[:, :, 1] = np.clip(128 + grain * 3, 116, 140).astype(np.uint8)
    normal[:, :, 2] = 255

    def png(name, pixels):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
        rows = b''.join(b'\0' + row.tobytes() for row in pixels)
        data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 2, 0, 0, 0))
        data += chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b'')
        with open(os.path.join(TEX, name), 'wb') as fh: fh.write(data)
    png('steel-metal-rough.png', packed)
    png('steel-normal.png', normal)


def metal_uv(pos, normals):
    # Project each quad using its dominant average normal; keep UV derivatives continuous
    # over fillets so normal maps do not reveal a diagonal seam through curved corners.
    result = []
    for start in range(0, len(pos), 4):
        pts, ns = pos[start:start + 4], normals[start:start + 4]
        axis = int(np.argmax(np.abs(np.mean(ns, axis=0))))
        result.extend([(p[1] if axis == 0 else p[0], p[1] if axis == 2 else p[2]) for p in pts])
    return [(u / 0.35, v / 0.35) for u, v in result]


def write_glb(m, path):
    buf = bytearray()
    views, accs, meshes, nodes, images, textures, materials = [], [], [], [], [], [], []
    mat_index = {}
    texture_index = {}

    def push(data, target=None):
        while len(buf) % 4: buf.append(0)
        off = len(buf); buf.extend(data)
        v = dict(buffer=0, byteOffset=off, byteLength=len(data))
        if target: v['target'] = target
        views.append(v)
        return len(views) - 1

    def texture(filename):
        if filename not in texture_index:
            with open(os.path.join(TEX, filename), 'rb') as fh: bv = push(fh.read())
            images.append(dict(bufferView=bv, mimeType='image/png', name=filename))
            textures.append(dict(source=len(images) - 1, sampler=0))
            texture_index[filename] = len(textures) - 1
        return texture_index[filename]

    def mat(name):
        if name in mat_index: return mat_index[name]
        rgb, a, metal, rough, tex = MATS[name]
        pbr = dict(baseColorFactor=[lin(rgb[0]), lin(rgb[1]), lin(rgb[2]), a], metallicFactor=metal, roughnessFactor=rough)
        md = dict(name=name, pbrMetallicRoughness=pbr, doubleSided=bool(tex) or a < 1 or name in {'cloth_staff', 'fold_panel'})
        if name in METALS:
            pbr['metallicRoughnessTexture'] = dict(index=texture('steel-metal-rough.png'))
            md['normalTexture'] = dict(index=texture('steel-normal.png'), scale=0.22)
        if a < 1: md['alphaMode'] = 'BLEND'
        if name in details.EMISSIVE: md['emissiveFactor'] = list(details.EMISSIVE[name])
        if tex:
            pbr['baseColorTexture'] = dict(index=texture(tex))
        materials.append(md)
        mat_index[name] = len(materials) - 1
        return mat_index[name]

    for n in m.nodes:
        prims = []
        for mname, (P, N, U, I) in n.geo.items():
            if not I: continue
            pos = np.array([to_gl(p) for p in P], dtype=np.float32)
            nor = np.array([to_gl(q) for q in N], dtype=np.float32)
            ln = np.linalg.norm(nor, axis=1, keepdims=True); ln[ln == 0] = 1; nor = (nor / ln).astype(np.float32)
            uv = np.array(metal_uv(P, N) if mname in METALS else U, dtype=np.float32)
            idx = np.array(I, dtype=np.uint32)
            a = {}
            for key, arr, typ in (('POSITION', pos, 'VEC3'), ('NORMAL', nor, 'VEC3'), ('TEXCOORD_0', uv, 'VEC2')):
                bv = push(arr.tobytes(), 34962)
                acc = dict(bufferView=bv, componentType=5126, count=len(arr), type=typ)
                if key == 'POSITION':
                    acc['min'] = [float(v) for v in pos.min(0)]; acc['max'] = [float(v) for v in pos.max(0)]
                accs.append(acc); a[key] = len(accs) - 1
            bv = push(idx.tobytes(), 34963)
            accs.append(dict(bufferView=bv, componentType=5125, count=len(idx), type='SCALAR'))
            prims.append(dict(attributes=a, indices=len(accs) - 1, material=mat(mname)))
        if not prims: continue
        meshes.append(dict(name=n.name, primitives=prims))
        extras = dict(layer=n.layer)
        if n.label: extras.update(label=n.label, label_ar=n.label_ar or n.label, code=n.code, anchor=list(to_gl(n.anchor)))
        nodes.append(dict(name=n.name, mesh=len(meshes) - 1, extras=extras))
    gltf = dict(asset=dict(version='2.0', generator='easy-food build_model.py'),
                scene=0, scenes=[dict(name='EasyFood-' + m.name, nodes=list(range(len(nodes))))],
                nodes=nodes, meshes=meshes, materials=materials, accessors=accs, bufferViews=views,
                buffers=[dict(byteLength=len(buf))],
                extras=dict(units='metres', site=SITE, rooms=m.rooms, note='Concept model. Width 2.79 m and depth 5.06 m supplied by owner; height, wall thickness, sidewalk depth ASSUMED; shopfront from photos.'))
    if images:
        gltf.update(images=images, textures=textures, samplers=[dict(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)])
    while len(buf) % 4: buf.append(0)
    js = json.dumps(gltf, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(buf)))
        fh.write(struct.pack('<I4s', len(js), b'JSON')); fh.write(js)
        fh.write(struct.pack('<I4s', len(buf), b'BIN\x00')); fh.write(buf)
    return len(nodes)


def write_obj(m, path):
    base = os.path.splitext(os.path.basename(path))[0]
    with open(os.path.splitext(path)[0] + '.mtl', 'w') as fh:
        for k, (rgb, a, metal, rough, tex) in MATS.items():
            fh.write(f'newmtl {k}\nKd {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f}\nd {a}\n')
            fh.write(f'Pr {rough}\nPm {metal}\n')
            if tex: fh.write(f'map_Kd source/textures/{tex}\n')
            fh.write('\n')
    with open(path, 'w') as fh:
        fh.write(f'# Easy Food kitchen layout {m.name} - metres, Y-up\nmtllib {base}.mtl\n')
        vo = 1
        for n in m.nodes:
            fh.write(f'o {n.name.replace(" ", "_")}\n')
            for mname, (P, N, U, I) in n.geo.items():
                if not I: continue
                for p in P:
                    g = to_gl(p); fh.write(f'v {g[0]:.4f} {g[1]:.4f} {g[2]:.4f}\n')
                for u in (metal_uv(P, N) if mname in METALS else U):
                    fh.write(f'vt {u[0]:.3f} {1 - u[1]:.3f}\n')
                for normal in N:
                    normal = np.array(to_gl(normal), dtype=float); normal /= np.linalg.norm(normal)
                    fh.write(f'vn {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n')
                fh.write(f'usemtl {mname}\n')
                for i in range(0, len(I), 3):
                    a, b, c = I[i] + vo, I[i + 1] + vo, I[i + 2] + vo
                    fh.write(f'f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n')
                vo += len(P)


# --------------------------------------------------------------------------------------
CAT = dict(service=('#FFF8EA', '#146B45'), cold=('#D9ECF7', '#2C6E91'), hot=('#FBDCCB', '#B4491C'),
           prep=('#E4F2D8', '#3F7D2A'), wash=('#DDE3F5', '#3B4C97'), store=('#F1E6CF', '#8A6A2A'),
           under=('none', '#555'), overhead=('none', '#999'))


def write_svg(m, path, title, subtitle, notes):
    S = 150.0                      # px per metre
    t = SITE['wall_t']; sw = 2.6   # sidewalk depth shown
    padL, padT = 250, 190
    Wpx = int(padL + (W + 2 * t) * S + 640); Hpx = int(padT + (D + 2 * t + sw) * S + 150)

    def X(x): return padL + (x + t) * S
    def Y(y): return padT + (D + t - y) * S       # back wall at the top, street at the bottom

    o = []
    A = o.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wpx}" height="{Hpx}" viewBox="0 0 {Wpx} {Hpx}" font-family="Segoe UI, Arial, sans-serif">')
    A('<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z" fill="#17251C"/></marker>'
      '<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#d8d8d4"/><line x1="0" y1="0" x2="0" y2="8" stroke="#8a8a86" stroke-width="2"/></pattern></defs>')
    A(f'<rect width="{Wpx}" height="{Hpx}" fill="#ffffff"/>')
    A(f'<text x="40" y="52" font-size="30" font-weight="700" fill="#146B45">{title}</text>')
    A(f'<text x="40" y="84" font-size="17" fill="#17251C">{subtitle}</text>')
    # sidewalk
    A(f'<rect x="{X(-t) - 200}" y="{Y(-t)}" width="{(W + 2 * t) * S + 400}" height="{sw * S}" fill="#f1f0ec"/>')
    A(f'<text x="{X(-t) - 190}" y="{Y(-t) + sw * S - 14}" font-size="15" fill="#777">SIDEWALK (public) - depth to kerb NOT measured - Al Brazil St beyond (street side is approx. EAST, from map pin)</text>')
    # walls
    A(f'<rect x="{X(-t)}" y="{Y(D + t)}" width="{(W + 2 * t) * S}" height="{t * S}" fill="url(#hatch)" stroke="#333"/>')
    A(f'<rect x="{X(-t)}" y="{Y(D)}" width="{t * S}" height="{(D + t) * S}" fill="url(#hatch)" stroke="#333"/>')
    A(f'<rect x="{X(W)}" y="{Y(D)}" width="{t * S}" height="{(D + t) * S}" fill="url(#hatch)" stroke="#333"/>')
    A(f'<rect x="{X(0)}" y="{Y(D)}" width="{W * S}" height="{D * S}" fill="#fafaf7" stroke="#333" stroke-width="1"/>')
    # front piers + threshold
    for a, b in ((-t, SITE['open_x0']), (SITE['open_x1'], W + t)):
        A(f'<rect x="{X(a)}" y="{Y(0)}" width="{(b - a) * S}" height="{t * S}" fill="url(#hatch)" stroke="#333"/>')
    A(f'<rect x="{X(0)}" y="{Y(-t)}" width="{W * S}" height="{0.30 * S}" fill="#cfcfcb" stroke="#666"/>')
    A(f'<text x="{X(0.05)}" y="{Y(-t) + 0.30 * S - 8}" font-size="13" fill="#444">stone step, about +0.15 m (photo estimate)</text>')
    # door + swing
    dx0, dx1 = SITE['door_x0'], SITE['door_x1']; r = (dx1 - dx0) * S
    A(f'<line x1="{X(dx0)}" y1="{Y(-0.1)}" x2="{X(dx0)}" y2="{Y(-0.1) - r}" stroke="#146B45" stroke-width="4"/>')
    A(f'<path d="M {X(dx1)} {Y(-0.1)} A {r} {r} 0 0 0 {X(dx0)} {Y(-0.1) - r}" fill="none" stroke="#146B45" stroke-dasharray="6 5" stroke-width="1.5"/>')
    A(f'<text x="{X(dx0) + 12}" y="{Y(0.42)}" font-size="13" fill="#146B45">staff door</text><text x="{X(dx0) + 12}" y="{Y(0.42) + 16}" font-size="13" fill="#146B45">0.85 opens in</text>')
    # window
    wx0 = SITE['win_x0']; wx1 = SITE['win_x1'] if m.name == 'A' else round(W - 0.75, 2)
    A(f'<rect x="{X(wx0)}" y="{Y(-0.07)}" width="{(wx1 - wx0) * S}" height="{0.07 * S}" fill="#9ed3e0" stroke="#146B45" stroke-width="2"/>')
    if m.name == 'B':
        A(f'<rect x="{X(wx1 + 0.04)}" y="{Y(-0.07)}" width="{(SITE["win_x1"] - 0.04 - wx1 - 0.04) * S}" height="{0.07 * S}" fill="#cfe8ee" stroke="#555"/>')
    # Retained WC: outer reservation, partitions, folded door and recognisable fixtures.
    wx, wy, wt = SITE['wc_w'], SITE['wc_y0'], SITE['wc_wall']
    da, db = wy + wt + 0.015, wy + wt + 0.015 + SITE['wc_door']
    A(f'<rect x="{X(0)}" y="{Y(D)}" width="{wx*S}" height="{(D-wy)*S}" fill="#FFF8EA" stroke="#146B45" stroke-width="2"/>')
    for a0, b0, a1, b1 in ((0, wy, wx, wy+wt), (wx-wt, wy+wt, wx, da), (wx-wt, db, wx, D)):
        A(f'<rect x="{X(a0)}" y="{Y(b1)}" width="{(a1-a0)*S}" height="{(b1-b0)*S}" fill="url(#hatch)" stroke="#146B45"/>')
    cx, cy = wx*0.46, D-0.45
    A(f'<ellipse cx="{X(cx)}" cy="{Y(cy)}" rx="{0.18*S}" ry="{0.25*S}" fill="white" stroke="#777" stroke-width="2"/>')
    A(f'<ellipse cx="{X(cx)}" cy="{Y(cy)}" rx="{0.12*S}" ry="{0.18*S}" fill="#d8e1df"/>')
    A(f'<rect x="{X(cx-0.22)}" y="{Y(D-0.035)}" width="{0.44*S}" height="{0.145*S}" rx="4" fill="white" stroke="#777"/>')
    for i in range(8):
        xx = wx - (0.025 if i % 2 else 0.09)
        A(f'<line x1="{X(xx)}" y1="{Y(da+0.018+i*0.011)}" x2="{X(wx-0.06)}" y2="{Y(da+0.029+i*0.011)}" stroke="#146B45" stroke-width="2"/>')
    A(f'<text x="{X(wx/2)}" y="{Y(wy+0.64)}" text-anchor="middle" font-size="17" font-weight="700" fill="#146B45">WC / حمّام</text>')
    A(f'<text x="{X(wx/2)}" y="{Y(wy+0.46)}" text-anchor="middle" font-size="11" fill="#555">{wx:.2f} x {SITE["wc_d"]:.2f} m OUTER (ASSUMED)</text>')
    A(f'<text x="{X(wx+0.05)}" y="{Y((da+db)/2)}" font-size="11" fill="#146B45">accordion</text>')
    # equipment
    for it in m.items:
        fill, stroke = CAT[it['cat']]
        x, y, w, h = X(it['x0']), Y(it['y1']), (it['x1'] - it['x0']) * S, (it['y1'] - it['y0']) * S
        dash = ' stroke-dasharray="7 5"' if it['cat'] in ('under', 'overhead') else ''
        A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>')
        if it['cat'] not in ('overhead',):
            fs = 15 if it['cat'] != 'under' else 12
            tx, ty = (x + 16, y + 16) if it['code'] == 'E01' else (x + w / 2, y + h / 2 + 5)
            A(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="{fs}" font-weight="700" text-anchor="middle" fill="{stroke}">{it["code"]}</text>')
        elif it['code'] == 'E08':
            A(f'<text x="{x + w - 6:.1f}" y="{y + 16:.1f}" font-size="12" text-anchor="end" fill="#777">E08 hood over</text>')
    # staff positions
    for i, (sx, sy) in enumerate(m.staff):
        A(f'<circle cx="{X(sx)}" cy="{Y(sy)}" r="{0.2 * S}" fill="none" stroke="#146B45" stroke-width="2" stroke-dasharray="3 4"/>'
          f'<text x="{X(sx)}" y="{Y(sy) + 5}" font-size="14" font-weight="700" text-anchor="middle" fill="#146B45">S{i + 1}</text>')
    # exterior positions
    if m.name == 'A':
        ext = [(1.38, -0.92, '1 ORDER + PAY', '#146B45'), ((SITE['win_x0'] + SITE['win_x1']) / 2 + 0.42, -0.92, '2 COLLECT', '#B4491C')]
        A(f'<text x="{X(W + 0.1)}" y="{Y(-1.05)}" font-size="13" fill="#555">riders wait kerb-side,</text><text x="{X(W + 0.1)}" y="{Y(-1.05) + 16}" font-size="13" fill="#555">called by order number</text>')
        A(f'<text x="{X(-0.9)}" y="{Y(-2.25)}" font-size="13" fill="#555">order queue: 3 floor marks straight out from window 1, then along own frontage; keep 1.5 m clear for pedestrians</text>')
    else:
        ext = [(1.42, -0.92, '1 ORDER + COLLECT', '#146B45')]
    for ex, ey, tx, col in ext:
        A(f'<circle cx="{X(ex)}" cy="{Y(ey)}" r="{0.22 * S}" fill="{col}" fill-opacity="0.15" stroke="{col}" stroke-width="2"/>')
        A(f'<text x="{X(ex)}" y="{Y(ey) + 0.42 * S}" font-size="14" font-weight="700" text-anchor="middle" fill="{col}">{tx}</text>')
    A(f'<circle cx="{X(0.95)}" cy="{Y(-t - 0.85)}" r="{0.30 * S}" fill="none" stroke="#888" stroke-width="2"/><text x="{X(0.62)}" y="{Y(-t - 0.85) + 4}" font-size="11" text-anchor="middle" fill="#666">manhole</text>')

    # dimensions
    def dim_h(x0, x1, y, label, off=0):
        yy = Y(y) + off
        A(f'<line x1="{X(x0)}" y1="{yy}" x2="{X(x1)}" y2="{yy}" stroke="#17251C" stroke-width="1.3" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{(X(x0) + X(x1)) / 2}" y="{yy - 6}" font-size="14" font-weight="600" text-anchor="middle" fill="#17251C">{label}</text>')

    def dim_v(y0, y1, x, label, off=0):
        xx = X(x) + off
        A(f'<line x1="{xx}" y1="{Y(y0)}" x2="{xx}" y2="{Y(y1)}" stroke="#17251C" stroke-width="1.3" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        A(f'<text x="{xx - 8}" y="{(Y(y0) + Y(y1)) / 2}" font-size="14" font-weight="600" text-anchor="middle" fill="#17251C" transform="rotate(-90 {xx - 8} {(Y(y0) + Y(y1)) / 2})">{label}</text>')

    dim_h(0, W, D + t, f'{W:.2f} m clear width (owner-confirmed phone measurement)', off=-22)
    dim_v(0, D, -t, f'{D:.2f} m clear depth (owner)', off=-34)
    R = W - 0.70
    if m.name == 'A':
        dim_h(0.70, R, 1.95, f'aisle {R - 0.70:.2f}', off=0)
        dim_h(SITE['wc_w'], R, 4.10, f'WC access {R - SITE["wc_w"]:.2f}', off=0)
        dim_h(0.40, R, 1.12, f'{R - 0.40:.2f}', off=0)
        for a0, a1 in ((0.50, 1.10), (1.10, 2.30), (2.30, 2.86), (2.86, 3.46), (3.46, 4.06), (4.06, 4.46)):
            dim_v(a0, a1, W, f'{a1 - a0:.2f}', off=t * S + 22)
    else:
        dim_h(0.70, R, 2.30, f'aisle {R - 0.70:.2f}', off=0)
        dim_h(SITE['wc_w'], R, 4.20, f'WC access {R - SITE["wc_w"]:.2f}', off=0)
        dim_h(0.40, R, 1.12, f'{R - 0.40:.2f}', off=0)
    dim_h(SITE['open_x0'], SITE['open_x1'], -t - 0.30, 'shopfront opening about 2.6 (photo estimate - measure)', off=46)
    dim_h(dx0, dx1, -t - 0.30, '0.85', off=20)
    dim_h(wx0, wx1, -t - 0.30, f'{wx1 - wx0:.2f} window', off=20)

    # legend
    lx = X(W + t) + 110; ly = padT + 10
    A(f'<text x="{lx}" y="{ly}" font-size="18" font-weight="700" fill="#146B45">Equipment key</text>')
    seen = set(); k = 0
    for it in m.items:
        key = (it['code'], it['name'])
        if key in seen: continue
        seen.add(key); k += 1
        fill, stroke = CAT[it['cat']]
        yy = ly + 8 + k * 30
        A(f'<rect x="{lx}" y="{yy - 15}" width="20" height="20" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        A(f'<text x="{lx + 30}" y="{yy}" font-size="14" fill="#17251C"><tspan font-weight="700">{it["code"]}</tspan>  {it["name"].replace("&", "&amp;").replace("<", "&lt;")}  <tspan fill="#777">{it["x1"] - it["x0"]:.2f} x {it["y1"] - it["y0"]:.2f}</tspan></text>')
    yy = ly + 8 + (k + 2) * 30
    for i, ln in enumerate(notes):
        A(f'<text x="{lx}" y="{yy + i * 21}" font-size="13.5" fill="{"#B4491C" if ln.startswith("!") else "#333"}">{ln.lstrip("!")}</text>')
    # scale bar
    sy = Hpx - 60
    A(f'<line x1="{X(0)}" y1="{sy}" x2="{X(2)}" y2="{sy}" stroke="#17251C" stroke-width="3"/>')
    for i in range(3):
        A(f'<line x1="{X(i)}" y1="{sy - 7}" x2="{X(i)}" y2="{sy + 7}" stroke="#17251C" stroke-width="2"/><text x="{X(i)}" y="{sy + 24}" font-size="13" text-anchor="middle">{i} m</text>')
    A(f'<text x="{X(2) + 30}" y="{sy + 5}" font-size="13" fill="#555">Scale 150 px = 1 m. CONCEPT LAYOUT - not an approved construction, gas, electrical, ventilation or food-safety drawing.</text>')
    A('</svg>')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(o))


# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    make_metal_textures()
    os.makedirs(os.path.join(PKG, 'model', 'viewer'), exist_ok=True)
    os.makedirs(os.path.join(PKG, 'plans'), exist_ok=True)
    data = {}
    common = ['S1-S3 = staff working positions at peak.',
              'Dashed = under-counter or overhead items.',
              'Width 2.79 m as confirmed by the owner (phone measurement);',
              'tape-check at front, middle and back before fabrication.',
              'WC retained inside rear-left corner (owner-confirmed).',
              '!WC 1.20 x 1.60 m OUTER envelope / door are ASSUMED.',
              '!Accordion door requested; hygiene separation needs design.',
              '!Water / drain / power / gas points are ASSUMED, not surveyed.']
    for m, title, sub, notes in (
            (layout_A(), 'Easy Food - Layout A (selected): back-to-front line',
             'Retained rear-left WC; compact cold + wash left, cook / assembly right; two-sash service.',
             ['Flow: door - storage (E13/E12/E11) - wash + prep (E10/E09)', '- cook (E05-E07) - hot hold (E04) - assemble (E03)', '- pack (E02) - collect sash (E01).', ''] + common),
            (layout_B(), 'Easy Food - Layout B (alternative): cook at the front',
             'Retained rear-left WC; front cooking, assembly / packing on right, single service hatch.',
             ['Shortest duct, but one 1.04 m hatch, heat at the customer,', 'packing at the rear requires a return trip to the hatch; no', 'acceptable LPG locker position (implies electric cooking).', ''] + common)):
        glb = os.path.join(PKG, 'model', f'easy-food-kitchen-{m.name}.glb')
        cnt = write_glb(m, glb)
        write_obj(m, os.path.join(PKG, 'model', f'easy-food-kitchen-{m.name}.obj'))
        write_svg(m, os.path.join(PKG, 'plans', f'layout-{m.name}.svg'), title, sub, notes)
        with open(os.path.join(PKG, 'model', f'layout-{m.name}.json'), 'w', encoding='utf-8') as fh:
            json.dump(dict(site=SITE, units='metres', equipment=m.items, staff_positions=m.staff, rooms=m.rooms), fh, indent=1, ensure_ascii=False)
        with open(glb, 'rb') as fh:
            data[m.name] = dict(site=SITE, glb=base64.b64encode(fh.read()).decode(), stations=[[*to_gl(s[:3]), s[3], s[4]] for s in m.stations])
        print(f'layout {m.name}: {cnt} nodes, {os.path.getsize(glb) / 1024:.0f} kB, {len(m.items)} schedule items')
        # overlap check on floor-standing items
        fl = [i for i in m.items if i['cat'] not in ('under', 'overhead')]
        for i in range(len(fl)):
            for j in range(i + 1, len(fl)):
                a, b = fl[i], fl[j]
                if min(a['x1'], b['x1']) - max(a['x0'], b['x0']) > 0.005 and min(a['y1'], b['y1']) - max(a['y0'], b['y0']) > 0.005:
                    raise ValueError(f"Floor equipment overlap: {a['code']} / {b['code']}")
            a = fl[i]
            if a['x0'] < -1e-6 or a['x1'] > W + 1e-6 or a['y0'] < -1e-6 or a['y1'] > D + 1e-6:
                raise ValueError(f"Equipment outside room: {a['code']}")
    with open(os.path.join(PKG, 'model', 'viewer', 'model-data.js'), 'w') as fh:
        fh.write('window.EASYFOOD_MODELS = ' + json.dumps(data) + ';\n')
    print('done')
