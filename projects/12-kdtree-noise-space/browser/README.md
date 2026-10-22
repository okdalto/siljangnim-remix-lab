# KD-tree × Simplex noise — four executable studies

Run `python3 -m http.server 8774 --bind 127.0.0.1 --directory projects/12-kdtree-noise-space/browser` from the repository, then open http://127.0.0.1:8774/ . All dependencies are vendored; no model API or credentials are used.

1. 2D median KD-tree with x/y alternating cuts. Click to choose a query point. Exact nearest-neighbor branch-and-bound searches the currently shown depth, reporting actual distance evaluations and pruned rectangles.
2. 4,096 2D samples distributed by rejection sampling near the zero contour of Simplex noise. Full continuous field and KD partition are rendered side by side. Leaf color samples the field at the region center.
3. 8,192 genuine 3D points, sampled using noise3D(x,y,z). Median cuts cycle x/y/z, partitioning [-1,1]^3. Cells near the zero isosurface are kept by their center values; these are discrete selected cells, not a reconstructed smooth or guaranteed connected surface. The cut control clips cell bounds along z, rather than merely hiding a front image. Show-all reveals the complete partition.
4. The same selected cells render as cuboids, thin center plates (orientation id modulo 3), or edges. Switching styles preserves seed, noise, cutoff and cells. Drag to rotate, wheel to zoom.

The KD implementation in core.mjs is authored for this study, not borrowed from SciPy/static-kdtree. It is actual median binary spatial partitioning, not Octree, random subdivision, photo extrusion or height-map terrain. The noise implementation is the unmodified simplex-noise.js 4.0.3 (MIT) by Jonas Wagner. Rendering uses Three.js r170 (MIT). Both licenses are in vendor/.

Validation: `node projects/12-kdtree-noise-space/browser/verify.mjs`. Tests check point containment, matching child boundaries, every axis, total volume at each depth 0–10 and 440 exact nearest-neighbor queries against brute force across 2D/3D. Browser inspection covers four tabs, depth, cutaway and three material styles. This folder preserves the original standalone static studies. The parent project.md provides the animated Siljangnim port; see ../README.md.
