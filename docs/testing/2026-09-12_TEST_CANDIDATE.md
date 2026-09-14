# September 12 TEST candidate — v0.1.67-dev

**Built and validated; upload failed.** Steam still serves v0.1.65-dev.
This is not a claim that Steam has updated or that in-game tests have passed.
TEST item: [3794172730](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
Public alpha v0.1.56-alpha is unchanged; never enable both versions together.

## Included

- **#3: actual hose runtime.** Crunch's hose is a separate actor-free skin with
  29 controls. Springs retain its authored curve while allowing inertial motion;
  it is not a loose gravity rope. Both ends follow the current backpack/launcher.
- **#4: chimney smoke.** The native Warpfire smoke loop attaches at the measured
  chimney rim, with independent ownership and cleanup.
- **#14: relocation lookup correction.** `fire_rocket` and `reposition` are
  registered in the real two-way `NetworkLookup.bt_action_names` before use.
  Breed action names are explicit. The previous missing-key failure is covered
  by executable lookup tests, but the reported game reproduction still needs
  both host and client verification.
- **#16: readable aim.** Alignment lasts at least **1.0 second** before the
  firing animation begins; tracking continues during that time. Large turns may
  take longer. Target switches restart the telegraph and stale firing callbacks
  are cleared. This is not an extra pause inserted after the firing sound.

**Not included:** #15 crystal flame. The real under-barrel crystal and its frame
have been measured, but a visually suitable particle has not been accepted.
See [the crystal investigation](../research/WEAPON_CRYSTAL_FIRE.md).

## Hose policy and limits

The 28 unequal intervals total **2.32380619 m**. Shape stiffness is 100 s^-2,
restoring acceleration is capped at 40 m/s², and velocity damping is 5 s^-1.
Initialization uses the authored shape; gravity and motion then deflect it.
As it approaches full extension, the preferred curvature relaxes smoothly;
segment rest lengths are never changed to fit an impossible span.

Only the nearest **eight** eligible hoses within **40 m** are active on each
viewing peer. This is cosmetic and does not network forces or hose particles.
Static rest-bound culling is disabled for these bounded cosmetics so deformation
does not rely on an unverified automatic update of the imported mesh bounds.
There is **no wall, body or self-collision**. The hose is removed before death,
inventory drop/freeze, and teardown; it does not tether the corpse to the
dropped weapon. Existing body/weapon FBXs, actors and textures are preserved.

## Short acceptance checklist

After publication is confirmed, restart the game and verify
`[doomrocket:LOAD] v0.1.67-dev` on **every peer**. Follow
[the setup quickstart](../TESTER_QUICKSTART.md).

1. **Placement and feel:** inspect idle, walk, turn, aim, reload and wield/stow.
   Both hose ends remain attached; its general shape is retained with a little
   secondary motion, not a limp loop. Check both host and remote-client views.
   Crunch should confirm the inferred lower-grip inlet.
2. **Death and drop:** kill loaded and unloaded Engineers. Hose and chimney
   smoke disappear before the established ragdoll/drop behavior; no floating
   warhead, stretched corpse, explosive physics or orphan hose.
3. **Combat:** provoke repeated close-range kicks and repositioning, then let
   him reload and fire. No #14 crash, extra completed reload, lost kick impact,
   point-blank rocket, or firing before the one-second aiming floor.
4. **Smoke:** one native-scale plume begins inside the actual chimney lip,
   follows movement, persists while alive, and ends on death/removal.
5. **Lifecycle and load:** repeat spawn/kill, late join, pause/resume and map
   transition. Test several Engineers; note performance and expected distance/
   eight-hose culling. Never treat this cosmetic cap as a spawn limit.

Attach complete matching **host and client logs**, crash GUID/link if relevant,
and a continuous short clip for motion/aim timing. Logs are public: review them
before attaching. Report on [the relevant issue](https://github.com/Ensrick/doomrocket-private/issues),
keeping #3/#4/#14/#16 open until their visible, version-matched checks pass.

## Evidence boundary

The production dynamics suite passes twelve cases using the actual rig/profile:
authored zero-gravity rest shape, sag/damping, motion-then-hold at 30/60/144 FPS,
rigid and independent endpoint rotations, compressed/coincident and near-taut
configurations, invalid input, and reset behavior. It rejects unexpected
hide/reset loops and shows no steady-state table growth in the numeric modules.
Twenty-one existing solver regressions also pass against the production solver.

The measured stationary deflection is approximately **11 cm** under gravity.
In the motion/hold fixture, motion continues after the endpoint stops and then
settles. A 20-hose Lua physics-plus-frame benchmark measured approximately
7.4 ms mean / 11 ms maximum per 60 Hz frame; it excludes native bone writes,
rendering and other mod work. That is why the runtime uses a smaller budget.

Source/compiled asset tests additionally check the separate rig, unchanged
body/weapon, native skinned material binding, and exact scale conversion.
The [implementation record](../research/HOSE_RIG_AND_PHYSICS.md) retains details
and the separate September 10 **offline** lab evidence. Automated results do
not establish visual acceptance or native engine safety.

## Build validation and blocked upload

Built source commit `84d42f991c9e5826bc0d153a7b70e031f3f4889b` using the clean,
committed release wrapper on September 12. SDK compilation, all six verified
native material splices, **320 Python tests**, and the PowerShell ragdoll
regressions passed. The new hose tests include 15 source/compiled-asset checks,
12 dynamics cases, 44 actual-controller/lifecycle checks and four independent
local-to-world pose reconstruction cases. [Clean-environment source CI passed](https://github.com/Ensrick/doomrocket-private/actions/runs/34734238660).

The first compile exposed duplicate weapon texture dependencies in the hose's
SDK placeholder. Removing those placeholder dependencies fixed the package;
the existing exact-once tests were not relaxed. Runtime texture bindings still
come from the hash-verified native splice. The final rebuilt package passed
the changed-Lua freshness gates too.

The uploader then failed with `0xc0000005` at **ugc_tool.exe+0x4169** at
21:58:59 CDT. This is the same previously inspected Steam-interface fault as
September 5/8, not a game crash. Read-only diagnostics found live Steam PID
28180, but HKCU Steam ActiveProcess PID/user were zero. This establishes an
inconsistent recorded session; it does not prove the cause or current token
integrity. No Steam restart, registry edit, DLL replacement or reinstall was
performed in this turn.

Steam's API still reports TEST **v0.1.65-dev**, handle `8123257090222204359`,
95,350,820 bytes. No v0.1.67 tag or prerelease is created before verified
publication. Public alpha remains **v0.1.56-alpha**, handle
`1428725673095257484`, 92,596,852 bytes; its checkout and item were not changed.

**Workflow correction, September 13:** the former instruction to use a
separate interactive retry is superseded by the user's explicit direction to
copy and follow Vermintide 2 Tweaker's working process. See
[the release guide](../RELEASE_CHANNELS.md). Preserve the measured failure and
validated hashes as historical evidence; do not turn the September 12 session
observation into an ongoing Steam blocker. The later September 13 retry
transcript has no completed publication result.

Validated local package, **96,545,268 bytes** total:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `209fb8c3c0a8c3a4.mod_bundle` | 1,021,841 | `B242782BC46EA2646616D9D25A51F87701C49B989537B347B6E1B7D0BED801EC` |
| `4e6a9317aab221e1.mod_bundle` | 7,258 | `5C7BF2F4DD484FFA20EA5971068037E1B5DB1B5EB25530DFE664209532FF1DA8` |
| `ac226cc769a897ae.mod_bundle` | 62,726,587 | `59F8ABE733E67B0863A065B3FD989A2945355A3B14E7581F9B7474FEE26F8D93` |
| `doomrocket.mod` | 470 | `DBF17C3E8ED109834BBCF56E4BDF7700BFF937E6B699FD63D7E11E571F3165D2` |
| `e7852992f40eb619.mod_bundle` | 304,489 | `E1A04E500F8255EBEDCAFFB4E35E829ADBD99EBF46C2B8B4CD89D26DCA4735E2` |
| `f5283f9585ea8355.mod_bundle` | 32,484,623 | `263DE6994ABF8B6E6D5920D7B4D312DE293E5393AA5C4E626374EB5C1BB211F3` |

No matching in-game session has run for this candidate. Keep the runtime
issues open until their visible host/client checks pass.

## Publication verified: TEST v0.1.71-dev (2026-09-14)

The candidate above shipped unchanged as **v0.1.71-dev** (0.1.68 through 0.1.70
were built or allocated but never reached Steam; see `CHANGELOG.md`).

| Evidence | Value |
| --- | --- |
| Source commit | `ce88c4ea0680dece5a4ca6b91b1c971d544962c3` (PR #19, squash) |
| Steam `workshop_log.txt` | `[2026-09-14 01:57:17] Upload starting for workshop item 3794172730`; `[01:57:31] Uploaded new content ( ManifestID 447865338390972850 )`; `Upload finished ... : OK` |
| Steam metadata (adapter check) | title `Warprocket Bombardier TEST v0.1.71-dev`, visibility public, `file_size` 96240779, `hcontent_file` 447865338390972850, `time_updated` 1789369051 |
| Verified at | 2026-09-14T06:57:32Z (`.build/publication/verified-publication.json`) |
| GitHub prerelease | `v0.1.71-dev` on Ensrick/doomrocket-private with `doomrocket-0.1.71-dev.zip` and the hosted publication receipt |

Not proven: any in-game behavior. The acceptance checklist above still applies,
now against the `[doomrocket:LOAD] v0.1.71-dev` banner.
