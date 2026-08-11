# Warlock ragdoll regression fixtures

These are mutation tests, not examples of supported implementation. Each bad
Lua fixture isolates one failure that previously shipped; the positive fixture
describes the current untested candidate contract. `fixtures.psd1` is the
executable manifest.

Engine-resource and Lua mutations must end in `.fixture.txt`, never their real
Stingray extension. VMB scans the entire mod root, including `tools/`; a
literal fixture such as `custom_physx.state_machine` is treated as a shipping
asset and can crash the compiler before package generation, while a `.lua`
fixture can silently enter the shipping scripts bundle.

| Historical failure | Static rule | Runtime evidence required |
|---|---|---|
| Custom PhysX solver explosion / FPS collapse | `WR-RAG-001`: no custom `.physx`, ragdoll state, or outfit actor release | `custom_actors=0`; `wall_gap_ms <= 250` |
| Per-bone scene-link stick figure | `WR-RAG-002`: root-only inventory link; no runtime `World.link_unit` / `unlink_unit` | `parent_mismatch=0`; bounded probe ratios |
| Full-pose/scale sky stretch | `WR-RAG-003`: no full-pose write, scale write, or raw carrier-local position copy | `hips_drift <= 0.25 m`; zero scale/non-hips translation mutations; ratios `<= 2x` |
| v0.1.48 custom corpse disappearance | `WR-RAG-004`: do not disable, hide, or destroy the death outfit | `outfit_alive=true` at every begin/sample checkpoint |
| v0.1.49 ratling corpse substitution | `WR-RAG-005`: never reveal the native carrier; positively hide it with the audited 24-mesh fallback | `carrier_reveals=0`; `carrier_reveal` is an immediate failure |

The candidate-only rules add:

- `WR-RAG-006`: the custom ASM stays enabled and death switches bone mode to
  `ignore`. An active-driver registry observes both `World.update_animations`
  paths, queues exactly once only when that world equals `Unit.world(owner)`,
  and applies once in `AnimationSystem.add_safe_animation_callback()`. A safe
  callback must never requeue itself because callbacks are globally drained.
- `WR-RAG-007`: rigid source handoff/current matrices compute
  `inverse(source0) * source`, apply that delta to `target0`, then convert the
  desired target world pose by `inverse(target_parent_world)`. Child writes are
  rotation-only; translation is limited to hips.
- `WR-RAG-008`: every ragdoll format has `phase`, unique `id`, and `source`, and
  the source defines begin/sample/stop records.

Run both source mutations and the production contract:

```powershell
./tools/tests/Test-WarlockRagdollRegressions.ps1
```

Analyze a runtime capture separately:

```powershell
py -3 ./tools/analyze_warlock_ragdoll_log.py C:\path\to\console.log
```

A passing trace has at least three samples through the 5000 ms checkpoint,
monotonic lifetime, matching `id=<source>-<digits>` / `source=unit|husk`, no
visibility or hierarchy incidents, root delta at most 0.25 m, hips drift at
most 0.25 m, deformation ratios at most 2x, and no callback gap above 250 ms.
Video is still required to prove the visible corpse is the Warlock model.
