# Contributing

Thanks for helping develop Warprocket Bombardier. This repository is the public
TEST line; stable-player reports belong in
[`doomrocket-public`](https://github.com/Ensrick/doomrocket-public/issues/new/choose).

## Players and testers

Use the issue chooser rather than a blank issue. For crashes, attach the
original console log plus the crash GUID/Crashify link. For visual or audio
problems, add a short continuous video when practical. Follow
[`docs/TESTER_QUICKSTART.md`](docs/TESTER_QUICKSTART.md) so the report proves the
exact loaded build and network role.

## Code and documentation

1. Start from an issue when possible and keep one behavioral change per pull
   request.
2. Preserve Lua 5.1 compatibility and explicitly reason about host/client
   ownership and engine update phase.
3. Add a focused regression test for a bug fix.
4. Never treat source tests, an SDK build, or a clean log as visible runtime
   acceptance.
5. Do not commit generated bundles, tester logs, raw authoring assets, Wwise
   output, or game-derived payloads.
6. Keep version, Workshop title/description, issue forms, and status docs in
   sync.

Run before opening a pull request:

```powershell
py -3 tools/check_repository.py --channel development
py -3 tools/tests/test_doomrocket_projectile_lifecycle.py
py -3 tools/tests/test_doomrocket_sound_contract.py
py -3 tools/tests/test_doomrocket_ballistic_aim.py
py -3 tools/tests/test_warlock_combat_contract.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/tests/Test-WarlockRagdollRegressions.ps1
```

Before a Workshop upload, also complete the clean SDK build, verified material
splice, full pipeline, and post-upload verification in
[`docs/RELEASE_CHANNELS.md`](docs/RELEASE_CHANNELS.md).

## Issue-label policy

Labels describe separate dimensions and may be combined deliberately:

- kind: `bug`, `enhancement`, `documentation`, or `question`;
- channel: `dev-test` here and `public-alpha` in the player repository;
- evidence/workflow: `needs-triage`, `needs-info`, `confirmed`, and `testing`;
- impact/priority: `crash` and `release-blocker`.

New issue forms add `needs-triage`. Remove it as soon as the report is reviewed;
add `confirmed` only with reproducible evidence, and add `testing` while a fix
or feature awaits in-game acceptance. `confirmed` and `testing` can coexist:
one records the evidence and the other records the current work phase. Reserve
`crash` for an application crash or assertion and `release-blocker` for work
that must pass before the TEST line can be promoted. Closed dedicated
validation tasks may use only the channel plus `testing` labels.
