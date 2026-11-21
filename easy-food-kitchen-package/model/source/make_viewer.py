#!/usr/bin/env python3
"""Build the quick network viewer plus the original self-contained offline viewer.

Run after build_model.py and npm run build:viewer:
    python make_viewer.py [path/to/viewer.bundle.js]

viewer.html: small HTML, embedded Three.js bundle and metadata, lazy external GLB files.
viewer-offline.html: complete single-file viewer with both embedded models.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VW = os.path.join(HERE, '..', 'viewer')
bundle_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'viewer.bundle.js')

with open(os.path.join(HERE, 'viewer.template.html'), encoding='utf-8') as f:
    template = f.read()
with open(os.path.join(VW, 'model-data.js'), encoding='utf-8') as f:
    full_data = f.read()
with open(bundle_path, encoding='utf-8') as f:
    bundle = f.read()

prefix = 'window.EASYFOOD_MODELS = '
if not full_data.startswith(prefix):
    raise ValueError('Unexpected model-data.js format')
data = json.loads(full_data[len(prefix):].strip().removesuffix(';'))
metadata = {key: {k: v for k, v in model.items() if k != 'glb'}
            for key, model in data.items()}
for key in ('A', 'B'):
    if key not in metadata or not metadata[key].get('site') or not metadata[key].get('stations'):
        raise ValueError(f'Missing metadata for layout {key}')
    if not os.path.isfile(os.path.join(VW, '..', f'easy-food-kitchen-{key}.glb')):
        raise FileNotFoundError(f'Missing GLB for layout {key}')
lite_data = 'window.EASYFOOD_META = ' + json.dumps(metadata, ensure_ascii=False, separators=(',', ':')) + ';'

def escape_script(js):
    return js.replace('</script', '<\\/script').replace('<!--', '<\\!--')

def write_viewer(filename, payload):
    html = template.replace('/*__DATA__*/', escape_script(payload), 1)
    html = html.replace('/*__BUNDLE__*/', escape_script(bundle), 1)
    if '/*__DATA__*/' in html or '/*__BUNDLE__*/' in html:
        raise ValueError('Unfilled viewer template placeholders')
    output = os.path.join(VW, filename)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'{filename}: {os.path.getsize(output) / 1e6:.2f} MB')

write_viewer('viewer.html', lite_data)
write_viewer('viewer-offline.html', full_data)
