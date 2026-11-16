# 3D model detail revision — 16 November 2026

**Historical revision:** the later [retained-WC revision](08-retained-wc-revision.md) supersedes the original footprint, equipment sizes and width checks below.

The model uses the owner's 2.79 × 5.06 m clear dimensions. The 3.00 m ceiling remains assumed. Layout A is selected; layout B remains an alternative.

## Changes

- Rounded equipment casings and worktops, recessed door faces and gaskets, narrower door reveals, tubular pulls, hinges and adjustable feet.
- Chiller compressor grilles and temperature indicators; rounded controls, pan rims and sneeze-guard posts.
- Open wash/produce/hand-basin bowls with drains and curved taps.
- Hood capture recess, rolled lip, downward-facing folded baffle filters and removal handles; duct joints and hanger rods.
- Proportioned low-poly people with separate heads, shoulders, arms, hands, legs and shoes. Staff wear forest aprons, cream shirts and green caps; working figures face their stations.
- Service sash frames, seals and pulls, two-sided door handles and a rounded outside ledge. The wider exterior camera includes the delivery rider.
- Deterministic steel metalness/roughness and brush normal maps embedded in both GLBs. Soft rectangular lighting and offline reflection cards improve the viewer's steel highlights.
- Two additional camera presets and renders: equipment details (09) and hood filters (10). Both presets adapt to layout B's equipment positions.

All geometry remains in `model/source/build_model.py`. The viewer does not substitute equipment meshes. OBJ exports now include vertex normals and PBR material values; GLB carries the complete embedded PBR maps. OBJ material interpretation varies by importer.

## Rebuilding

See the README commands. `model/source/package-lock.json` pins the viewer/render tools. The delivered single-file viewer requires no installation or network access. Signage textures are supplied; regenerating signage also needs the adjacent green brand asset folder.

Edit `SITE['W']` after a tape survey. `configure_site()` derives the shopfront's right edge and the equipment line from the width. No new site measurements were inferred during this revision.

## Verification

- Geometry and floor-equipment overlap/bounds checks at widths **2.45, 2.60, 2.79 and 2.95 m**, for both layouts. Detailed appliance meshes stay inside their schedule footprints, including handles and controls.
- Equipment schedules, dimensions and staff station coordinates compared with the captured original source: identical for A and B.
- GLB headers, embedded PBR textures, Arabic equipment metadata and buffer bounds checked. OBJ vertex/UV/normal counts and triangle counts checked against GLB.
- Offline Chrome checks cover all eight camera presets, A → B → A switching, Arabic/English, equipment labels, layer toggles and a 390 × 844 mobile viewport. Browser checks reject console errors/warnings and external network dependencies.
- Twenty annotated 1920 × 1200 renders: ten Arabic and ten English; regenerated plan PNGs and the flow image. Interior, exterior, flow, equipment and hood views visually inspected.
- Repeatable checks: `python verify_model.py`, `npm run verify:viewer`. Run output is saved in `renders/review/`; the pre-revision interior and exterior captures are in `renders/review/before/`.

This remains a concept model. Figures are static, doors are shown closed and fine appliance details are generic design proposals, not manufacturer fabrication models. Width sensitivity checks establish geometric fit only. Site survey and professional service design are still required as stated in the main documents.
