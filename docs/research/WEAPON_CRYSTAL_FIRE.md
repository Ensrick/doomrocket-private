# Under-barrel crystal flame: issue #15

Investigation 2026-09-12. **No flame is enabled by this work.**

The actual crystal is present in the accepted launcher. Read-only Blender
inspection of Crunch's SHA-pinned scene identifies the faceted, 75-vertex
component **1858–1932** under the muzzle. Component 1933–1981 is its mounting
socket, not the crystal; the unrelated component 3259–3307 is beneath the main
chamber. No new locator, mesh replacement or guessed muzzle offset is needed.

The same indices survive in the shipping 3,308-vertex launcher FBX. The
[measured fixture](../../tools/fixtures/warlock_crystal_anchor.json) retains the
crystal centroid, tip cluster, mounting-cap landmark, dimensions and right-handed
frame. `tools/tests/test_doomrocket_crystal_anchor.py` checks the real FBX hash,
coordinates, exact connected component and frame. Generated highlighted views
are in ignored `.build/issue15_crystal/{side,underside}.png`.

The frame is in engine root metres, **not native node-local coordinates**.
The accepted compiled `pRocketLauncher` node (index 7) has scale 100. A future
effect must convert through its verified inverse rest world transform, then
link to that live mesh node; do not apply a posed hand-bone inverse or normalize
away scale compensation. The linked unit must be the exact current inventory
launcher, not a dropped replacement.

## Effect selection remains unresolved

The installed native `fx/wpnfx_warp_fire_nozzle` resource is a candidate, not an
accepted match to the reference. Its resource hash appears at byte 1900 in the
Warpfire package table (`resource_packages/breeds/skaven_warpfire_thrower`;
3,837 bytes). Decoding identifies one continuously emitting billboard cloud,
capacity 10, a +X velocity cone at 3.5–4.5 m/s, and a 0.1 m spawn sphere.
SHA-256: `da0400ae2f2fb959096c5af5015f65b0e925e46d28348b18c1439c7571e94db3`.
The resource lifetime is 1,410,065,408 seconds, effectively persistent for a
game session. Its material/curve appearance has **not** been visually verified.

`fx/wpnfx_warp_fire_flames` is also in that package (resource hash at byte 1932),
but the current particle reader encounters unsupported initializer data.
`fx/skaven_torch_warpfire_01` has a three-cloud persistent effect but is not in
that breed package. Neither effect's name proves correct size or appearance.
No native bytes were copied into the mod and no guessed effect was enabled.

Next: inspect candidate effects in an isolated in-game visual test, select the
small green flame appropriate to the reference, then give it independent linked
particle ownership following the tested smoke lifecycle: one effect per live
owner/current launcher on each peer, no re-creation per frame, stop before
death/drop/inventory teardown, and forget before world release. Keep #15 open
until visible placement, persistence and host/client cleanup are accepted.
