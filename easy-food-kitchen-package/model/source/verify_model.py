"""Geometry/export regression checks. Run after build_model.py; needs only numpy."""
import json
from pathlib import Path
import struct

import numpy as np
import build_model as b


def check_layout(model):
    floor = [i for i in model.items if i['cat'] not in ('under', 'overhead')]
    for i, a in enumerate(floor):
        assert -1e-6 <= a['x0'] < a['x1'] <= b.W + 1e-6, a
        assert -1e-6 <= a['y0'] < a['y1'] <= b.D + 1e-6, a
        for other in floor[i + 1:]:
            overlap = (min(a['x1'], other['x1']) - max(a['x0'], other['x0']) > 0.005 and
                       min(a['y1'], other['y1']) - max(a['y0'], other['y0']) > 0.005)
            assert not overlap, (model.name, a['code'], other['code'])
    triangles = 0
    for node in model.nodes:
        for mat, (pos, normals, uv, indices) in node.geo.items():
            assert len(pos) == len(normals) == len(uv), (node.name, mat)
            assert np.isfinite(pos).all() and np.isfinite(normals).all(), (node.name, mat)
            assert len(indices) % 3 == 0 and 0 <= min(indices) <= max(indices) < len(pos)
            triangles += len(indices) // 3
        # Details must not consume the working aisle. Service top intentionally runs into sill.
        if node.code in {'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E09', 'E10', 'E12', 'E13', 'E14'}:
            item = next(i for i in floor if i['code'] == node.code)
            pts = np.concatenate([g[0] for g in node.geo.values()])
            for axis, letter in enumerate('xy'):
                assert pts[:, axis].min() >= item[letter + '0'] - 1e-5, (node.code, letter, 'min')
                assert pts[:, axis].max() <= item[letter + '1'] + 1e-5, (node.code, letter, 'max')
    return triangles


def check_export(variant):
    path = Path(b.PKG) / 'model' / f'easy-food-kitchen-{variant}.glb'
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and length == len(data)
    size, kind = struct.unpack_from('<I4s', data, 12)
    assert kind == b'JSON'
    gltf = json.loads(data[20:20 + size])
    assert gltf['extras']['site'] == b.SITE
    assert all('uri' not in i for i in gltf['images']), 'GLB must embed its textures'
    for m in gltf['materials']:
        if m['name'] in b.METALS:
            assert 'metallicRoughnessTexture' in m['pbrMetallicRoughness']
            assert 'normalTexture' in m
    for node in gltf['nodes']:
        extras = node['extras']
        if extras.get('code'):
            assert extras.get('label_ar') and len(extras['anchor']) == 3
    for v in gltf['bufferViews']:
        assert v.get('byteOffset', 0) % 4 == 0
        assert v.get('byteOffset', 0) + v['byteLength'] <= gltf['buffers'][0]['byteLength']
    obj = path.with_suffix('.obj').read_text()
    counts = {prefix: sum(line.startswith(prefix) for line in obj.splitlines()) for prefix in ('v ', 'vt ', 'vn ', 'f ')}
    assert counts['v '] == counts['vt '] == counts['vn '] > 0, counts
    expected = sum(gltf['accessors'][p['indices']]['count'] // 3 for mesh in gltf['meshes'] for p in mesh['primitives'])
    assert counts['f '] == expected, (counts, expected)
    assert all(len(v.split('/')) == 3 for line in obj.splitlines() if line.startswith('f ') for v in line.split()[1:])
    print(f'{variant}: GLB/PBR, Arabic labels, buffer ranges and OBJ normal/face parity OK')


if __name__ == '__main__':
    original = b.SITE.copy()
    try:
        for width in (2.45, 2.60, 2.79, 2.95):
            b.configure_site(W=width)
            assert b.SITE['win_x1'] == round(width - b.SITE['front_right_inset'], 3)
            for builder in (b.layout_A, b.layout_B):
                m = builder()
                count = check_layout(m)
                print(f'W={width:.2f} {m.name}: {count:,} triangles; geometry, mesh footprints and layout clearances OK')
    finally:
        b.configure_site(**original)
    for variant in ('A', 'B'):
        check_export(variant)
