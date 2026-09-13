# September 12 TEST candidate — v0.1.67-dev

**Publication pending verification.** This records implemented candidate work,
not a claim that Steam has updated or that in-game tests have passed.
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

Publication/content-handle verification and actual game-session results must
be recorded separately after they occur; none is claimed by this candidate note.
