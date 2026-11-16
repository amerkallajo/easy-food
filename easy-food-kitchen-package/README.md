# Easy Food - Al Brazil St, Damascus: takeaway kitchen package

Prepared 16 November 2026 for the planned takeover of the MarCoffee shop (G78R+3PH, Al Brazil, Damascus) in January 2027.

## Verdict: proceed with specific changes

The site suits a small healthy takeaway, and a three-person kitchen fits the room. Before spending on equipment, settle three things: whether a kitchen exhaust is allowed at the street facade, whether bowls sell at about 525 SYP, and where the toilet sits.

- **Break-even:** about 56-63 orders a day with market rent and your own pay counted (32 a day on cash costs alone).
- **Worth the investment at:** about 100 orders a day, which pays back roughly $25,000 in about a year.
- **Kitchen capacity:** about 35-50 orders an hour at peak with three staff, 120-180 a day.
- **Investment:** about $17,000-34,000 including 15% contingency.
- **Name:** Easy Food, in Arabic إيزي فود, with the line أكلك الصحي، بكل بساطة.

All money figures are estimates built on stated assumptions; see document 4.

## Read in this order

| # | Document | What it answers |
|---|---|---|
| 1 | [Site inventory](docs/01-site-inventory.md) | What the photos prove, what was supplied, what is assumed, what is missing |
| 2 | [Feasibility assessment](docs/02-feasibility-assessment.md) | Location, competitors, constraints, verdict, cheap tests, sources |
| 3 | [Name and brand](docs/03-brand-name.md) | Easy Food versus EZ Food, Arabic presentation, what "healthy" must mean |
| 4 | [Menu, operation, economics](docs/04-menu-operations-economics.md) | Launch menu, staffing, capacity, unit economics, break-even, payback |
| 5 | [Layouts and equipment](docs/05-kitchen-layouts-equipment.md) | Two layouts compared, the selected one, full equipment schedule |
| 6 | [Budget, checklist, open items](docs/06-budget-checklist-open-items.md) | Budget ranges, phased checklist, measurements and decisions still needed |

## Drawings and model

| File | What it is |
|---|---|
| `plans/layout-A.png` / `.svg` | Dimensioned plan, selected layout |
| `plans/layout-B.png` / `.svg` | Dimensioned plan, alternative |
| `plans/flow-A.png` | Staff positions and food flow |
| `renders/ar/` and `renders/en/` | The same ten views with **Arabic** or English annotations |
| `renders/ar/01-A-cutaway-3d.png` | Cutaway 3D with equipment labels |
| `02-A-top-down-cutaway.png` | Top-down 3D |
| `03-A-interior-from-door.png`, `04-A-interior-from-back.png` | Interior views |
| `05-A-exterior-signage-order-collect.png` | Exterior with signage, order and collect windows |
| `06-A-staff-and-food-flow.png` | Flow view |
| `07-B-...`, `08-B-...` | Alternative layout |
| `09-A-equipment-detail.png`, `10-A-hood-filters-detail.png` | Close views of the doors, handles, worktops and hood baffle filters |
| `model/easy-food-kitchen-A.glb`, `-B.glb` | Portable 3D model (opens in Windows 3D Viewer, Blender, any glTF viewer) |
| `model/easy-food-kitchen-A.obj` + `.mtl`, `-B` | Mesh for Blender, SketchUp, 3ds Max |
| `model/viewer/viewer.html` | **Double-click to orbit the model in a browser**, offline. One self-contained file. Buttons switch views, layers, layout A/B and Arabic/English labels |
| `model/layout-A.json`, `-B.json` | Equipment footprints in metres |
| `model/source/build_model.py` | **Editable source.** Change dimensions or equipment, run it, and the GLB, OBJ, JSON and SVG plans are regenerated together |

### Regenerating after the site survey

Install the pinned viewer tools once with `npm ci` in `model/source`. Python needs `numpy`; rendering uses the installed Google Chrome. Signage PNGs are already supplied.

```
cd model/source
python build_model.py          # GLB, OBJ, JSON, SVG plans, viewer data  (needs numpy)
node make_textures.cjs         # only if signage artwork changes
npm run build:viewer           # rebuild bundle after viewer.src.js changes
python make_viewer.py          # rebuilds the single-file viewer.html
python verify_model.py         # mesh bounds, nearby widths, GLB/PBR validation
node render.cjs                # ten PNG renders in each language, plans and flow image
npm run verify:viewer          # offline controls, languages, layouts, mobile and console
```

`make_viewer.py` needs `viewer.bundle.js` in `model/source/` (a copy is kept there). `npm run build:viewer` builds it using the pinned Three.js 0.170.0 and esbuild dependencies in this folder. The delivered viewer still opens offline with no installation.

### 3D detail revision, 16 November 2026

Equipment now has filleted edges, recessed doors and gaskets, tubular handles, adjustable feet, chiller ventilation grilles and controls. Sinks have open bowls and drains. The hood has a capture recess, baffle filter panels, a rolled lip and duct seams. Low-poly figures have separate limbs, shoulders and heads; staff wear forest aprons over cream shirts. Shopfront sashes have frames, seals and pulls.

The GLB embeds packed metalness/roughness and subtle brushed normal maps. The viewer adds soft strip lighting and environment reflections. OBJ includes smooth vertex normals and material roughness/metalness values; appearance depends on the importing application's material support. See [model revision and verification](docs/07-model-detail-revision.md).

Width remains controlled by `SITE['W']`; the right-hand equipment line and right edge of the shopfront follow it. Verification covers both layouts at 2.45, 2.60, 2.79 and 2.95 m. This is a geometric check, not a fabrication tolerance or an operational approval.

## What is measured and what is not

- **Supplied by you:** depth 5.06 m, width 2.79 m (confirmed 16 Nov 2026; replaces the earlier 2.60 m). Both are phone measurements; tape-check before fabrication.
- **Estimated from photographs:** shopfront opening, door and glazing widths, step height, manhole position.
- **Assumed:** ceiling height 3.00 m, wall thickness, sidewalk depth, every water, drain, power and gas point, the exhaust route, and that the toilet lies outside the 5.06 m rectangle.
- The 3D model is geometry built from those numbers. It is a concept model, not a survey. Finishes and signage are proposals. No AI-generated images are used.
- The layouts are concept layouts, not approved construction, ventilation, electrical, gas or food-safety drawings.

## Two answers that would change the design

1. Where is the toilet, and is it inside the 5.06 m?
2. Is there any rear shaft or window, or must the kitchen exhaust leave through the shopfront?
