# Changelog

## v0.1.61-dev — 2026-09-02

Development TEST candidate; runtime acceptance pending.

- Makes projectile detonation an early-guarded, one-way lifecycle transition.
- Queues projectile deletion before fallible impact callbacks.
- Routes the authoritative explosion request into the engine-managed phase to
  avoid the stale-position failure seen in issue #8.
- Adds source regressions for one-shot dispatch, re-entry, missing-unit/actor
  races, and deferred cleanup.
- Adds project re-entry documentation, tester instructions, structured issue
  forms, release-channel guards, and CI source validation.

Do not promote this candidate to the public alpha until its runtime matrix passes.
