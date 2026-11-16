#!/usr/bin/env python3
"""Assemble ../viewer/viewer.html as ONE self-contained file (model data + viewer code inlined).

Run after build_model.py:   python make_viewer.py [path/to/viewer.bundle.js]
A single file is needed because some preview panes do not load sibling .js files.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
VW = os.path.join(HERE, '..', 'viewer')
bundle_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'viewer.bundle.js')
tpl = open(os.path.join(HERE, 'viewer.template.html'), encoding='utf-8').read()
data = open(os.path.join(VW, 'model-data.js'), encoding='utf-8').read()
bundle = open(bundle_path, encoding='utf-8').read()
esc = lambda js: js.replace('</script', '<\\/script').replace('<!--', '<\\!--')
html = tpl.replace('/*__DATA__*/', esc(data), 1)
i = html.index('/*__BUNDLE__*/')
html = html[:i] + esc(bundle) + html[i + len('/*__BUNDLE__*/'):]
out = os.path.join(VW, 'viewer.html')
open(out, 'w', encoding='utf-8').write(html)
print('viewer.html', round(os.path.getsize(out) / 1e6, 2), 'MB')
