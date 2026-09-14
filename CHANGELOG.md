# Changelog

## v0.1.71-dev - reissue of the unpublished v0.1.68-dev TEST candidate

- Same runtime content as v0.1.68-dev (semi-rigid hose, chimney smoke, #14
  lookup correction, #16 aiming floor). v0.1.68-dev was built and hosted but
  never reached Steam: its build receipt had captured the SDK's tool-only
  `e7852992f40eb619.mod_bundle` (the Stingray LUT-generator sidecar), which
  clean builds emit nondeterministically, so the publication snapshot could not
  reproduce the receipt's output set. v0.1.69-dev was allocated and burned by
  the claim broker during the renumbering; v0.1.70-dev was burned when its claim
  had to be re-taken under an explicit session identity (see below).
- `tools/mod-inventory.psd1` now carries the same `BuildArtifactExclusions`
  policy as vermintide-2-tweaker, so build normalization strips that sidecar by
  exact name and SHA-256 before any receipt or parity comparison.
- `tools/ship/ship.ps1` waits the upstream 300 seconds for the machine-global
  VMB transaction lease instead of 60 seconds; concurrent Tweaker builds on the
  same machine no longer fail the ship with lock contention.
- Standalone layout lesson: VMB Launcher derives the claim owner from the VMB
  project root (`_doomrocket_vmb`), while the copied `claim.ps1` derives it
  from this repository path when no session variable is set, so the launcher's
  claim gate refused the upload with two different `worktree:` owners. The
  adapter now fails closed unless `VT2_SHIP_SESSION_ID` (or a Claude/Codex
  session id) is set, and it must be set before `claim.ps1`, BuildOnly and the
  ship alike.
- `docs/RELEASE_CHANNELS.md` documents the verified preflight: PowerShell host,
  approved launcher path, claim identity, Steamworks registration recovery, and
  the sidecar policy. No gameplay change; host/client acceptance remains open.

## v0.1.68-dev - standalone TEST publication candidate

- Includes the unpublished semi-rigid hose, chimney smoke, relocation action
  registration fix (#14), and one-second aiming floor (#16) from v0.1.67.
- Adapts the working Tweaker headless ship transaction to this standalone
  repository, with committed build receipts, hosted QA, exact package proof
  and item-specific upload verification. No game installation or deployment
  is claimed. Host/client gameplay and visual acceptance remain pending.


## v0.1.66-dev — unpublished development candidate

- Adds a cosmetic prototype using native Warpfire backpack smoke at the measured
  Warlock chimney lip, with scale-correct linking and owned emitter cleanup.
- Preserves all body/weapon geometry, bones, weights, materials, animations and
  physics. No hose is appended to the rigid launcher.
- Researches native Warpfire two-endpoint hose deformation and separate native
  dangling-chain references under issues #3/#4; actual hose physics remains open.
- Adds anchor provenance/matrix and executable particle-lifecycle regressions.

This candidate is **not on Workshop**. The existing v0.1.65 relocation crash
[#14](https://github.com/Ensrick/doomrocket-private/issues/14) remains unresolved
and must be handled before another TEST publication. Smoke appearance and
host/client acceptance are pending. Public alpha v0.1.56-alpha is unchanged.
See [hose/smoke research and test plan](docs/research/BACKPACK_HOSE_AND_SMOKE.md).

## v0.1.65-dev — 2026-09-08

Published development TEST build; repositioning awaits runtime acceptance.

Workshop item `3794172730`, content handle `8123257090222204359`,
95,350,820 bytes, verified 2026-09-08 15:38:48 UTC.

- Address the close-range idle gap with a bounded reposition after a kick
  ([#13](https://github.com/Ensrick/doomrocket-private/issues/13)), preserving
  the kick cooldown, native shove force, and 1.8 m launch exclusion.
- Keep ammunition independent of movement and retain the v0.1.64 reload fix.
- Record Crunch's matching v0.1.64 host confirmation and the remaining
  multiplayer, final-second interruption, and portrait checks.

## v0.1.64-dev — 2026-09-07

Published development TEST build; new reload behavior awaits runtime acceptance.

Workshop item `3794172730`, content handle `1532641586336614793`,
95,349,849 bytes, verified 2026-09-07 17:47:44 UTC.

- Replace the old kill-feed image with Crunch's supplied 60x70 Engineer
  portrait, preserving its pixels and the existing atlas/runtime identity.
- Add a reproducible portrait atlas builder and source/compiled regression
  checks. The supplied 110x130 portrait is not wired into the kill feed.
- Preserve a completed rocket load across shoves instead of replaying the
  reload animation after every kick (issue #12, reported in #11).
- Wait with the loaded rocket while a close player remains inside the shove
  envelope, then resume aiming when the player steps away.
- Retain the existing shove cooldown, force, damage, and aiming timing.
- Record the v0.1.63 host confirmations: repeated career switching no longer
  reproduces #9, combat barks stop on death (#10), and repeat shoves block
  point-blank launches (#11). Remote-client verification remains open.

## v0.1.63-dev — 2026-09-03

- Pair bot-group ranged-attack start/end notifications even when career switching destroys the original player unit, preventing the one-victim assertion in issue #9.
- Reject and abort Doomrocket launches inside the 1.8 m Stormvermin shove envelope, so the shove cooldown cannot fall through into a point-blank self-hit from issue #11.
- Track combat-voice playing IDs and stop an active bark before the custom death take, addressing the remaining audio behavior reported in issue #10.

## v0.1.62-dev — 2026-09-03

Development TEST candidate; runtime acceptance pending.

Published to Workshop item `3794172730` as content handle
`3137123372436099113`. Source, compiled-resource, upload, and remote metadata
gates pass; in-game acceptance is still required.

- Rejects a nil or deleted player target before launch initialization, fixing
  the issue #9 career-switch crash at `Unit.local_position`.
- Guards bot-attack notifications, clears stale reload targets, and makes an
  invalid launch frame fail back to the selector without touching the
  destroyed unit.
- Evaluates the Stormvermin shove's 1.8 m distance, 1.5 m/s movement, and
  7.5-second cooldown boundaries directly in the Ratling selector, fixing the
  never-selected shove reported in issue #11.
- Gives the custom Wwise project metadata a Doomrocket-specific resource name,
  eliminating the collision risk of the generic `wwise/project` resource.
- Reorders HIRC Action/Event records to match working Wwise 2018 VT2 banks and
  dispatches loaded-bank events when `Wwise.has_event` is a metadata false
  negative, with playing-ID telemetry to prove runtime acceptance.
- Adds regression contracts for stale career targets, deterministic shove
  selection, unique metadata, authoring-compatible HIRC order, and direct
  custom-event dispatch.

## v0.1.61-dev — 2026-09-02

Development TEST candidate; runtime acceptance pending.

Published to Workshop item `3794172730` as content handle
`8534772704831302808`. Source and compiled gates pass; in-game acceptance is
still required.

- Makes projectile detonation an early-guarded, one-way lifecycle transition.
- Queues projectile deletion before fallible impact callbacks.
- Routes the authoritative explosion request into the engine-managed phase to
  avoid the stale-position failure seen in issue #8.
- Adds source regressions for one-shot dispatch, re-entry, missing-unit/actor
  races, and deferred cleanup.
- Adds project re-entry documentation, tester instructions, structured issue
  forms, release-channel guards, and CI source validation.

Do not promote this candidate to the public alpha until its runtime matrix passes.
