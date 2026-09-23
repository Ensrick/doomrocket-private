# Contributing

Build, deployment and upload follow the user's September 13 direction to use
[Vermintide 2 Tweaker's working method](docs/RELEASE_CHANNELS.md), whose exact
source documentation and scripts are copied into this repository. Older release
commands in historical records are not operational instructions.

Thanks for helping develop Warprocket Bombardier. This repository is the public
TEST line; stable-player reports belong in
[`doomrocket-public`](https://github.com/Ensrick/doomrocket-public/issues/new/choose).

## Players and testers

Use the issue chooser rather than a blank issue. For crashes, attach the
original console log plus the crash GUID/Crashify link. For visual or audio
problems, describe what you saw or heard; no recording is needed. Follow
[`docs/TESTER_QUICKSTART.md`](docs/TESTER_QUICKSTART.md) to identify the exact
loaded build. Solo play is sufficient for ordinary issue acceptance.

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
py -3 tools/tests/test_doomrocket_reload_lifecycle.py
py -3 tools/tests/test_doomrocket_portrait_pipeline.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/tests/Test-WarlockRagdollRegressions.ps1
```

Install `requirements-dev.txt` first. The reload lifecycle tests execute the
production actions in Lua 5.1 through [Lupa](https://pypi.org/project/lupa/),
with engine I/O stubbed; animation and multiplayer results still require
the game.

For portrait updates, follow [`docs/WARLOCK_PORTRAIT_PIPELINE.md`](docs/WARLOCK_PORTRAIT_PIPELINE.md).
Replacing the standalone PNG alone does not replace the compiled atlas.

Before a Workshop upload, also complete the clean SDK build, verified material
splice, full pipeline, and post-upload verification in
[`docs/RELEASE_CHANNELS.md`](docs/RELEASE_CHANNELS.md).

## Issue-label policy

Labels describe separate dimensions and may be combined deliberately:

- kind: `bug`, `enhancement`, `documentation`, or `question`;
- channel: `dev-test` here and `public-alpha` in the player repository;
- evidence/workflow: `needs-triage`, `needs-info`, `confirmed`, `blocked`,
  `ready-for-testing`, and `testing`;
- impact/priority: `crash` and `release-blocker`.

New issue forms add `needs-triage`. Remove it as soon as the report is reviewed;
add `confirmed` when the tester's observation or other evidence establishes the
problem. Use `blocked` when implementation or a decision is needed before
another useful test. Use both `ready-for-testing` and `testing` when the current
published build has a concrete playtest question. These two states are mutually
exclusive; remove all three status labels when closing an issue. `confirmed`
can coexist with either open state because it describes evidence, not work
phase. Reserve `crash` for an application crash or assertion and
`release-blocker` for work that must pass before the TEST line can be promoted.
Do not create a standing two-player test gate; a tester can report multiplayer
behavior when it naturally arises.
