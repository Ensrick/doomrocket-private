# Changelog

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
