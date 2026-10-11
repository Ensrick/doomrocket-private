# Visible gait and launcher grip investigation

The September 16 report describes foot sliding and hands separating from the
launcher. Written observations establish those failures; the checks below do
not replace an in-game result.

## Confirmed causes

The hidden native Ratling carrier drives the weapon attachments. The visible
Warlock is a root-linked outfit with its own state machine and retargeted clips.
Animation events were mirrored, but gait speed and procedural aim were absent
from the visible controller.

- `move_fwd` selected a fixed-speed `combat_run` clip. The native
  `move_fwd_run` event was absent, so the visible model could retain an older
  animation while the carrier moved.
- Walk and run clip durations match the native donors (5 seconds and
  approximately 3.666667 seconds). A frame-rate conversion error was not found.
- Translation compression was too coarse for the rig's 100x wrapper. All four
  sampled own clips (idle/run/shoot/reload) retained only one hips end key,
  whereas the native clips had 34/115/224/24 positional keys. Source FBXs still
  contain the full motion. The old 0.01 local position tolerance corresponds to
  1 m at the wrapper; 0.00001 targets 1 mm without changing rotation tolerance.
- The launcher mesh, projectile, body and sampled animation FBXs matched the
  accepted v0.1.55 assets before this work. The weapon's rigid root axes,
  attachment nodes, semantic grip and muzzle direction still passed their
  source and compiled checks. An arbitrary mesh rotation is not warranted.
- The native controller aims through a constraint on `aim_target`, with direct
  mask weights `j_spine = 0.5`, `j_spine1 = 1.0`. The visible controller had no
  such constraint, so the carrier moved the launcher without that adjustment
  reaching the visible hands.
- The custom aim helper's axes match the donor, but its old root-relative
  position is `(0, 3, 1.25)` metres instead of approximately `(0.1, 5, 0.6)`.
  The resulting spine-to-reference rays differ by approximately 8-10 degrees
  in sampled poses. Inspection of the installed SDK's type-1 aim implementation
  confirms it uses reference **position**, so adding the constraint also
  requires calibrating that helper.

## Candidate implementation and checks

The visible model now accepts distinct walk/run events and derives its gait
rate from actual horizontal displacement before its world's animation pass.
Native breed speeds supply the initial calibration: 1.9 m/s walk, 4 m/s run.
Pause, teleport, deletion, death, freeze/unfreeze and world release are covered.

The helper's constant translation is calibrated separately from the deforming
bone curves; the latter retain their source motion under the tighter compile
tolerance. The aim target follows the existing owner/husk network path. Each
outfit first
checks the named constraint exists, then resolves its own index. No carrier
variable/constraint index or state machine is forwarded to the custom skeleton.
An isolated SDK compile verified the authored mask, target and constraint on
the exact 138-bone skeleton: its reference bone is 137, whereas the donor's is 1.
The production bundle verifier checks these bindings and state activation.

### Compression versus resampling

The first fresh build showed that SDK resampling needs a separate error bound
from position fitting. Observed output times lie on dyadic subdivisions (for
example, 128 intervals over the 3.666667-second run), with adaptive thinning.
Those sample values match the source, but interpolation across a sharp original key can
miss that key. No supported sample-rate override was established.

The guard checks at most 1 mm error at each retained compiled position sample,
and also checks the entire piecewise-linear source/compiled curves at every
breakpoint: at most 10 mm for ordinary/death clips and 20 mm for stagger clips.
The first fresh results range up to 7.15 mm and 19.05 mm respectively; they are
not a claim of 1 mm fidelity everywhere. The old endpoint-only output fails by
82.6 mm idle, 192.5 mm run and 218.4 mm shoot-start. The fixture regression
continues to reject that motion loss. Crunch's later written report confirms
the grip still diverges in game; [issue #28](https://github.com/Ensrick/doomrocket-private/issues/28)
tracks the engineering fix.

The launcher keeps its accepted native attachment/drop path. The visible body
keeps its own animation controller and existing death handoff. Source and
compiled checks can establish reference data and safe ownership; full two-hand
contact through movement, firing and reload has not been achieved. The current
launcher follows hidden-carrier attachment nodes while the visible hands follow
a separate outfit animation. The cause of their animated relative motion needs
same-frame diagnosis before changing either transform. A static weapon rotation
is not established as the fix. No scheduled multiplayer test is required.

## October 10 follow-up: v0.1.85-dev candidate

Crunch's matching v0.1.84-dev log attached to [issue #33](https://github.com/Ensrick/doomrocket-private/issues/33)
contains five probe arming records and 600 hand/launcher samples. Excluding the
first 0.5 seconds, the measured left-hand gap is a median 10.1 cm while walking,
12.9 cm while running, and 32.3 cm during `attack_shoot_align`; idle is 0.51 cm
and wind-up start 0.86 cm. The launcher handle, root and barrel follow their
native attachment nodes exactly. Unmirrored `jump_down`, `jump_down_land`,
`jump_up_5m` and `jump_down_1m` events account for larger gaps, up to 1.81 m.
This supports the independently advancing visible-controller diagnosis, rather
than an arbitrary mesh rotation. The old probe ran before scene composition,
however, so its cached world transforms are not by themselves proof of the
final rendered displacement. The written visual failure remains accepted.

The candidate adds a bounded **twelve-joint upper-body pose transfer**: spine,
shoulders, arms, forearms, hands and forearm rolls. After the native world's
animation evaluation, its safe callback first composes the carrier, outfit and
weapon with `World.update_unit`. It reads native rigid world positions and
rotations, preserves the custom uniform world scale, and converts each result
through the current custom parent hierarchy. All candidate matrices, parent
inverses, orthogonality and existing local scales are validated before any
rotation or position write. The outfit is composed again afterward. Matched
compiled clips establish the shared deform-bone world bases and the custom
100x ancestor; native local positions and animated scale are never copied.

The accepted rigid weapon export, root-only inventory links, lower-body gait,
own animation state machine and death transfer remain in place. The driver
stops before death, inventory freeze/destruction or world release. The probe
independently composes all three units before measurement and now reports
`stage=post_unit_update` plus `alignment=active` or a concrete skipped-state
reason. This separates the current-frame final hand gap from the old cache
boundary. Eight executable regressions reconstruct world poses after the
actual Lua writes, including a rotated/translated 100x parent, phase/aim
differences, native scale rejection, invalid matrices and teardown. They do
not establish visual acceptance.

The candidate **does not solve unsupported jump animation**. The custom
controller has no corresponding authored jump clips. It skips the transfer
when an event cannot be mirrored, rather than dragging only the upper torso
onto a jumping native pelvis. Those event/clip bindings need Arnaud's asset
work; no new art, model or animation assets were authored in this pass.
Ordinary idle, walk/run, turn, aim, fire and reload grip behavior is ready for
a written solo verdict after publication. Issue #28 remains open until that
verdict, and retains this explicit jump limitation.
