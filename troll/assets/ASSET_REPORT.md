# Nature asset report: first candidates

**Status of every asset below: CANDIDATE - AWAITING USER APPROVAL.** Nothing here is approved for
series use. Per troll/CLAUDE.md, approval is recorded in `ASSET_APPROVALS.md`, which this session did not
touch.

- Blender: **4.2.3 LTS** (hash 0e22e4fcea03, built 2024-10-14), official linux-x64 build, checksum verified,
  installed in `/opt/blender` (outside the repo). Rendering: Cycles CPU, 64 samples with adaptive
  sampling and OpenImageDenoise, AgX view. EEVEE cannot run in this container because libEGL is missing.
- Units: 1 Blender unit = 1 m. Exports are in metres (FBX unit scale 1 m, Y-up). **Project scale is
  4 studs = 1 m** (troll/CLAUDE.md). Roblox's importer "Meter" option assumes 1 stud = 0.28 m
  (about 3.57 studs/m), so the model must be scaled by 4 / 3.57 = 1.12 after import, or imported with
  scale factor 4 in stud units. Please decide which convention to standardise on.

## Regenerate (one command)

```
BLENDER=/opt/blender/blender bash troll/assets/blender/build_all.sh
```

This runs `gen_spruce.py`, `gen_pine.py` and `gen_boulder.py`. Each one builds its textures, LOD
meshes, FBX+GLB, stats JSON (`blender/stats/`), renders and a small `.blend` (`blender/blend/`, kept only
if under 20 MB; all are well under). It is deterministic per seed. One asset alone:
`blender -b -P troll/assets/blender/scripts/gen_spruce.py -- --only spruce_b [--no-render]`.
Build time is about 1.5-2.5 min per tree and about 1.5 min per boulder on 4 CPU cores.

## What exists vs. NOT PRODUCED

| Asset | Status |
|---|---|
| spruce_a / spruce_b / spruce_c | Produced (LOD0, LOD1, LOD2, LOD2_billboard; renders) |
| pine_a / pine_b / pine_c | Produced (LOD0, LOD1, LOD2, LOD2_billboard; renders) |
| boulder_050 / boulder_150 / boulder_400 | Produced (LOD0, LOD1, LOD2; renders) |
| birch_lowland, birch_mountain | **NOT PRODUCED.** `scripts/gen_birch.py` is written but has never been run. The birch leaf and bark texture builders were only tested outside the repo |
| Line-up render (all assets, overcast sky) | **NOT PRODUCED.** `studio.overcast_lighting()` exists but no line-up script was run |

## Roblox constraints (checked against the exported meshes)

- Each Blender object becomes one MeshPart. Trees export 2 MeshParts per LOD (Bark, Foliage), because a
  SurfaceAppearance carries one texture set. LOD2_billboard is 1 MeshPart.
- Largest single MeshPart: 7,468 tris (spruce_c LOD0 foliage). This is far under the 20,000 limit.
- Tree LOD0 totals are at or under 10,000 tris, LOD1 under 2,500 and LOD2 under 500. The billboard is 4 tris.
  Boulder LOD0 = 1,500, LOD1 = 500, LOD2 = 150.
- Mobile = LOD1/LOD2 with the 512 px textures in `textures/<species>/mobile/`.
- Foliage needs `MeshPart.DoubleSided = true` and SurfaceAppearance AlphaMode Transparency or Overlay.
  Alpha is in the ColorMap's alpha channel. A separate `*_alpha.png` is also provided. The GLB uses alphaMode MASK, cutoff 0.35.
- Maps per material: `*_albedo.png` (ColorMap, sRGB, RGBA for foliage), `*_normal.png` (NormalMap,
  OpenGL +Y), `*_rough.png` (RoughnessMap), `*_metalness.png` (64 px, all 0). All are at most 1024x1024.
- The FBX references textures by relative path (not embedded; the path was not re-checked in an importer). The GLB embeds them.

## Textures (generated procedurally with numpy, not photos)

| Set | Files (1024 px; 512 px copies in `mobile/`) | Size on disk |
|---|---|---|
| spruce | bark atlas (left half = lower trunk, right half = upper/branches) albedo/normal/rough; foliage atlas (left = flat spray, right = hanging comb spray) albedo RGBA/normal/rough/alpha; metalness; 3 x impostor (512 only) | 11 MB |
| pine | bark atlas (grey fissured lower / orange flaky upper); foliage atlas (shoot brushes / fan); metalness; 3 x impostor | 8 MB |
| boulder | per boulder baked albedo/normal/rough (Cycles selected-to-active from a 82k-328k-face sculpt) | 11 MB |

Total `troll/assets` is about 137 MB (export 94 MB, mostly GLBs with embedded textures; textures 30 MB;
renders 8.5 MB; blends + scripts 4.9 MB). This is under the 150 MB cap but close, so dropping
embedded textures from the GLBs is the obvious saving.

## Per-asset, per-LOD numbers

Values come from `blender/stats/<asset>.json`. Height and width are the mesh bounding box (cards
included). "Render verts" counts unique vertex + UV + normal combinations. FBX/GLB sizes are listed per file.

### Trees
### pine_a

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 21.09 | 9.78×9.07 | 8954 | Bark 2898, Foliage 6056 | 11215 / 11215 | 1024 | 971 KB | 6529 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 21.04 | 10.27×9.61 | 2500 | Bark 520, Foliage 1980 | 4380 / 4380 | 512 | 352 KB | 1923 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 20.96 | 12.19×12.21 | 500 | Bark 64, Foliage 436 | 922 / 922 | 512 | 88 KB | 1749 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 22.95 | 11.47×11.47 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 287 KB | CANDIDATE - AWAITING USER APPROVAL |

### pine_b

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 17.8 | 8.14×10.93 | 7627 | Bark 2483, Foliage 5144 | 9558 / 9558 | 1024 | 833 KB | 6444 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 17.8 | 8.37×11.19 | 2500 | Bark 444, Foliage 2056 | 4472 / 4472 | 512 | 359 KB | 1927 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 17.55 | 11.11×13.93 | 500 | Bark 56, Foliage 444 | 933 / 933 | 512 | 88 KB | 1749 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 25.74 | 12.87×12.87 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 205 KB | CANDIDATE - AWAITING USER APPROVAL |

### pine_c

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 22.47 | 10.68×9.02 | 8145 | Bark 2797, Foliage 5348 | 10079 / 10079 | 1024 | 879 KB | 6471 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 22.47 | 11.09×9.38 | 2500 | Bark 496, Foliage 2004 | 4408 / 4408 | 512 | 354 KB | 1924 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 22.47 | 11.92×12.1 | 500 | Bark 56, Foliage 444 | 933 / 933 | 512 | 88 KB | 1749 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 25.73 | 12.87×12.87 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 212 KB | CANDIDATE - AWAITING USER APPROVAL |

### spruce_a

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 28.96 | 10.76×10.29 | 9160 | Bark 2512, Foliage 6648 | 14920 / 14920 | 1024 | 1189 KB | 8270 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 29.7 | 12.86×12.41 | 2500 | Bark 626, Foliage 1874 | 4276 / 4276 | 512 | 345 KB | 2380 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 30.39 | 15.56×14.64 | 500 | Bark 80, Foliage 420 | 900 / 900 | 512 | 87 KB | 2210 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 27.15 | 13.58×13.58 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 560 KB | CANDIDATE - AWAITING USER APPROVAL |

### spruce_b

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 23.11 | 7.42×6.9 | 9752 | Bark 2544, Foliage 7208 | 13035 / 13035 | 1024 | 1110 KB | 8185 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 23.11 | 8.84×8.24 | 2500 | Bark 636, Foliage 1864 | 4272 / 4272 | 512 | 346 KB | 2380 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 23.11 | 10.56×11.23 | 500 | Bark 72, Foliage 428 | 911 / 911 | 512 | 87 KB | 2210 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 24.03 | 12.02×12.02 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 415 KB | CANDIDATE - AWAITING USER APPROVAL |

### spruce_c

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 29.48 | 9.65×9.03 | 10000 | Bark 2532, Foliage 7468 | 15545 / 15545 | 1024 | 1258 KB | 8305 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 29.86 | 11.78×11.09 | 2500 | Bark 630, Foliage 1870 | 4260 / 4260 | 512 | 345 KB | 2379 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 30.67 | 14.51×13.78 | 500 | Bark 88, Foliage 412 | 889 / 889 | 512 | 86 KB | 2209 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2_billboard | 29.23 | 14.62×14.62 | 4 | Billboard 4 | 8 / 8 | 512 | 21 KB | 516 KB | CANDIDATE - AWAITING USER APPROVAL |

### Boulders
Nominal sizes are 0.5, 1.5 and 4 m. Actual longest axis: 0.48, 1.28 and 3.75 m. About 6 % of the height is buried below z = 0.

### boulder_050

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.25 | 0.48×0.41 | 1500 | LOD0 1500 | 752 / 1341 | 1024 | 121 KB | 2579 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 0.25 | 0.48×0.41 | 500 | LOD1 500 | 252 / 553 | 512 | 58 KB | 831 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 0.25 | 0.47×0.41 | 150 | LOD2 150 | 77 / 220 | 512 | 34 KB | 813 KB | CANDIDATE - AWAITING USER APPROVAL |

### boulder_150

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.78 | 1.28×1.01 | 1500 | LOD0 1500 | 752 / 1230 | 1024 | 117 KB | 2994 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 0.79 | 1.28×1.01 | 500 | LOD1 500 | 252 / 511 | 512 | 57 KB | 920 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 0.77 | 1.3×1.0 | 150 | LOD2 150 | 77 / 189 | 512 | 33 KB | 902 KB | CANDIDATE - AWAITING USER APPROVAL |

### boulder_400

| LOD | Height m | Width X×Y m | Tris (total) | Tris per MeshPart | Verts (Blender / render) | Tex px | FBX | GLB | Status |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2.22 | 3.75×3.18 | 1500 | LOD0 1500 | 752 / 1366 | 1024 | 122 KB | 3409 KB | CANDIDATE - AWAITING USER APPROVAL |
| 1 | 2.24 | 3.75×3.17 | 500 | LOD1 500 | 252 / 575 | 512 | 59 KB | 1017 KB | CANDIDATE - AWAITING USER APPROVAL |
| 2 | 2.23 | 3.76×3.2 | 150 | LOD2 150 | 77 / 219 | 512 | 34 KB | 998 KB | CANDIDATE - AWAITING USER APPROVAL |


## Renders (all opened and inspected)

`renders/<asset>.png` (1280x720): 3 panels for trees (two turntable angles and a base close-up)
and 2 panels for boulders, with a 1.8 m mannequin. `renders/<asset>_lods.png` shows LOD0 | LOD1 |
LOD2 | billboard side by side (rendered for spruce_a, pine_a and all boulders).

| Render | My judgement |
|---|---|
| spruce_a, spruce_b, spruce_c | **Acceptable silhouette.** Dense dark narrow cone with drooping lower branches; the variants differ (open-grown to the ground, raised crown base, taller and gappy). Weak spots: in close-up the hanging "comb" cards read as repeated leaf-shaped blobs, the crown is somewhat columnar and narrower than the Oslo reference, and the lighting looks flat and dark. |
| spruce_a_lods | LOD0/LOD1 fine. The 500-tri LOD2 is sparse with the trunk visible. The billboard holds the silhouette best at distance but reads darker. |
| pine_a, pine_b, pine_c | **Weak.** Bark split and long clear bole are right, but the crowns are too sparse and spiky with thin fishbone limbs, like young lanky pines. They lack the dense, flat-topped, heavy-limbed clumps in the references. Variants differ mainly in height, lean and crown proportions. |
| pine_a_lods | LOD1 OK. LOD2 (500 tris) is blotchy. The billboard is OK. |
| boulder_150, boulder_400 | **Acceptable.** Rounded erratic shape, grey granite with lichen and moss on top, plausible scale next to the figure. Lichen patches are fairly uniform and the shape is a bit lumpy. |
| boulder_050 | Acceptable but small in frame (only 0.25 m tall). |
| boulder_*_lods | LOD1 and LOD2 keep the shape. LOD2 at 150 tris is visibly faceted. |

Nothing here is photorealistic. The renders use simple studio light, the foliage has no
translucency, card intersections show in close-ups, and the bark uses repeating tiles.

## Known flaws / TODO before approval
1. Pine crowns need about 2x foliage mass, bigger clumps and thicker crooked limbs. A tweak was tried, then
   reverted because it was not rebuilt. The script on disk matches the exported pines.
2. Birch (2 forms) and the overcast line-up render have not been produced.
3. Spruce comb cards: the pendulous spray texture is too leaf-shaped. It needs a curtain-of-shoots texture.
4. Tree LOD2 (500-tri cards) is poor. The billboard alternative (`*_LOD2_billboard`) is better from ground
   level but fails from high viewpoints.
5. Bark/foliage textures are shared per species, so the 3 variants of a species share a texture set.
6. Spruce LOD1/LOD2 bounding heights exceed LOD0 by up to about 1.5 m because up-scaled cards stick out past the top.
7. Not yet imported into Roblox Studio. The import, DoubleSided and AlphaMode behaviour and the stud
   scale (point above) are unverified.
