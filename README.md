# Easy Food

Easy Food project in Damascus: the kitchen concept, interactive 3D model, planning documents, and visual identity.

- **Live website:** https://amerkallajo.github.io/easy-food/
- **Interactive kitchen:** https://amerkallajo.github.io/easy-food/easy-food-kitchen-package/model/viewer/viewer.html
- **Green visual identity:** https://amerkallajo.github.io/easy-food/easy-food-identity-v2-green/

## Project files

- [`easy-food-kitchen-package/`](easy-food-kitchen-package/README.md): planning documents, drawings, Arabic/English renders, GLB/OBJ exports, editable source and a self-contained 3D viewer.
- [`easy-food-identity-v2-green/`](easy-food-identity-v2-green/README.md): current green identity, local fonts and their licenses, logos, PDF guide and editable templates.
- [`easy-food-identity-v1/`](easy-food-identity-v1/README.md): earlier identity retained as an archive.
- The two identity ZIP files are the original delivered download packages.
- `index.html` + `assets/`: the homepage. `assets/site.css` and `assets/site.js` hold its styles and interactions; `assets/img/` has WebP display copies of the concept images, plans and identity boards (the originals stay in place and open in the page's preview); `assets/fonts/` has WOFF2 versions of the identity package's Cairo and Manrope with their OFL licenses. Rebuild these with `python assets/tools/build_home_assets.py` (needs Pillow and fontTools).

The kitchen is a concept model, with provisional dimensions and services. It is not an approved construction drawing. Identity mockups are conceptual applications rather than production dielines. See the package READMEs for assumptions and instructions.

## Run locally

No build is required to view the published project. From this directory:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/. The kitchen viewer also works directly from its HTML file offline. For model regeneration, see the kitchen package README.

## Publishing

GitHub Pages serves the repository root from `main`; `.nojekyll` keeps the existing static files intact. Push updates to `main` and wait for the Pages deployment to finish. A previous known-good commit can be restored with a normal revert and push.

Local tool state, installed dependencies, browser screenshots, credentials and original site-survey photos in `refrence/` are excluded from publication.
