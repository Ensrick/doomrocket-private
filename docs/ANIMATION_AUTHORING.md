# Warlock Engineer animation authoring

This rig lets Arnaud animate the existing Warlock Engineer model in Blender
5.2. It provides body-part control curves, arm and leg FK/IK, finger curl and
spread, foot rolls, forearm twist, bounded stretch and squash, backpack offsets,
and localized coat and belt corrections. The user's October 10, 2026 request
explicitly authorizes engineering to prepare this animation rig. It does not
transfer responsibility for new character art, models, or sound masters.

The authoring files are candidates outside the repository. The localized body
and diagnostic clips are separate from the playable package. Public alpha
v0.1.59-alpha remains unchanged; [project status](https://github.com/Ensrick/doomrocket-private/blob/private-copy/PROJECT_STATUS.md) records
the current TEST publication. Blender behavior, FBX roundtrip, SDK compilation,
and an in-game visual verdict are separate checks. Read the generated reports
for their actual results; this guide does not claim native playback or an
in-game pass.

## Current transition candidate

The v0.1.91-dev source candidate reduces duplicate skeleton validation during a
legacy-target blend. A callback-scoped token shares the read-side check between
the grip and outfit builders; full validation remains at entry and before any
helper pose write. Events, re-entry, failures and teardown invalidate the scope.
Custom targets receive no legacy corrections. All original animation tracks,
transition durations, scene updates and steady-state safety checks are retained.
The 138-bone actual-Lua work probe measures 5,383 calls rather than 6,204 per
active legacy frame (13.23% fewer); it measures neither native time nor memory
allocation. The default playable manifest remains empty, so the existing staged
diagnostic route is required to test custom/native transitions. The earlier
measurements below retain their original source and version scope.

Fresh v0.1.91 production-Lua validation uses the current compositor, grip and
outfit modules with the newly staged manifest against thirteen historical
decoded SDK specimens. All 3,276 ordinary/interrupted poses pass: 452,088 bone
and 115,675,560 weighted-vertex comparisons, with maximum skin error 5.448
micrometres against a 2 mm bound. The 234 pure-authored zero-write checks and
1,638 authored-helper checks also pass. The ignored report
`.build/animator_rig/snapshot_blend_numeric_v91.json` has SHA-256
`100685cdf64cdfbd90dc7baa23bec8206515c83af0c498fcadc5bb4afcdbd8bd`.
This is fresh evaluation by the current Lua, with zero new native-game captures;
it does not reclassify the historical decoded inputs as current engine evidence.

v0.1.87-dev replaces immediate mixed cuts with the `snapshot-blend-v1` bridge
described below. The final compositor passes 36 executable Lua regressions;
the ownership controller passes 68, with an independent runtime safety review.

| Current check | Result and scope |
| --- | --- |
| Isolated staging | 74 checks using actual Windows short-path aliases; three reviewed 43-file overlay routes pass. |
| Contract rejection guards | Nineteen package membership/format/path cases, twenty compiled Lua table cases, and thirteen numerical reference/receipt-inventory cases pass. |
| Actual Lua mixed poses | All thirteen legacy numerical specimens, 3,276 poses (1,638 ordinary and 1,638 interrupted), 452,088 bone comparisons, and 115,675,560 weighted vertex comparisons. Maximum head error 0.687 micrometres, axis-probe error 1.550 micrometres, and skin error 5.448 micrometres, below the unchanged 2 mm gate. |
| Authored track ownership | 234 pure-authored zero-write checks and 1,638 checks that an authored helper receives no legacy bone writes pass. |
| Legacy Lua equivalence | Old/current Lua match all 24,077 historical poses: 3,322,626 float32 local matrices are byte-identical. The fresh SDK bridge also proves the 2,192,102-byte scene/skin/bind/actor prefix, compiled bones, and all thirteen original animations exact. The prior 850,158,870 skin comparisons and 1.410 mm maximum are inherited through that complete identity proof, with zero new legacy weighted evaluations. |
| Final SDK/package | Fresh isolated compilation and decoded package proof pass: 21 probe root-package members include all 16 required type/resource pairs and 12 graph-referenced animation resources. The compiled Lua manifest matches all 924 literal entries and the 138 ordered bones. All 154 visible durations remain exact; all 154 helper edges are zero. All thirteen original compiled animations retain all 138 tracks byte for byte. |
| Native playback / game | Zero native `Unit` captures; event clock reset, hidden-mesh evaluation, and rendered appearance still need a written in-game verdict. |

The mixed-pose report is `snapshot_blend_numeric_v87.json`, SHA-256
`4e9971f8b17b2936e7b2f2dc319784a45b90e17c0a7c63bcf0034f200df75e8a`.
It executes the actual compositor and legacy builders against independent
float32 API doubles, with decoded SDK Hermite target samples injected at the
selected phases and independently advanced API-double clocks. Its real staged
custom route is the frozen continuous diagnostic in `base/idle`, using the
idle/shoot-loop event fixture. The thirteen original clips supply numerical
endpoints; death and stagger specimens are not authored state registrations.
This checks composition fidelity and ownership, not native clocks or whether
these poses look natural. Each new artist clip still needs its own verified
FBX/SDK integration and in-game verdict.

The final probe is `animation_sdk_snapshot_blend_package_final_probe`.
Its `compiled_animation_contract.json` has SHA-256
`f5e05957fe468dd6e9016f25f44a40a7d0d7e94e7230bde11283b61f2d4e6083`;
`compiled_package_closure.json` has SHA-256
`ec1bf04769885b41cabff3f68765e94399906027893e306a1b4a27d622cd5370`.
The latter proves actual package membership and decodes the compiled Lua literal
manifest without executing or modifying it.
`legacy_equivalence_v87_final_sdk.json`, SHA-256
`e0c90fd3622da20cfe0e7649a89b717bd67387997c1e07db9916dc77734cad17`,
binds the complete legacy pose identity to this fresh SDK's exact compiled
scene/skin/bind/bone/clip lane. The separate final acceptance verifier must also
join and recheck the report/source/compiled identities before release.

## Earlier authoring and SDK results, October 11, 2026 UTC

These results belong to the frozen v0.1.86-dev integration handoff. They support
the unchanged rig, exporter, and original animation payloads; they do not
establish acceptance of the v0.1.87-dev snapshot compositor or hidden sampler.
Read the new handoff's source-bound reports for its current results. The final
sampler/package and legacy compiled-lane checks pass; native playback remains
pending.

| Check | Result and scope |
| --- | --- |
| Blender controls | 68/68 behavior checks; neutral skin differs from the approved body by at most 5.70 micrometres. |
| Animator panel | 39/39 checks; worst pose-preserving FK/IK switch error 0.342 mm. |
| Continuous motion | 19/19 checks across 589 frames and 81,282 evaluated bones; all nine authored pose markers match exactly. |
| Independent FBX import | Both 97-frame and 589-frame exports pass; maximum joint/axis-probe error under 3.2 micrometres. |
| Portable package | 17/17 checks using adjacent references and the final exporter; source files remain unchanged. |
| Decoded SDK deformation | The 97-frame and 589-frame diagnostics stay below 0.991 mm across 3,425,070 and 20,797,590 weighted vertex comparisons respectively. These sample authored frames. |
| Continuous between-key motion | 588 halfway poses, 81,144 bone comparisons against raw FBX scalar TRS and its full hierarchy; maximum joint error 0.443 mm and 0.1 m axis-probe error 0.603 mm, below the 2 mm gate. No midpoint skin or native `Unit` samples are claimed. |
| Original thirteen clips, SDK | All thirteen compiled animation payloads match the shipping reference byte for byte, including all 138 tracks. All original FBX and sidecar files remain exact. |
| Blender weapon preview | Neutral, maximum stretch, and maximum squash preserve rigid launcher dimensions within 0.18 micrometres and match the SDK rotation convention. All 138 GAME bones, skin data, and both existing action payloads remain unchanged. |
| Runtime pose ownership, v0.1.86-dev | Executable Lua tests cover authored body/accessory ownership, immediate mixed transitions, rigid weapon following, aim policy, inventory teardown, and legacy restoration. These do not validate the new snapshot blend. |
| Full legacy outfit audit | All thirteen clips: 24,077 actual-Lua/float32 decoded poses and 850,158,870 weighted vertex comparisons; maximum skin error 1.410 mm, below the fixed 2 mm gate. Every original compiled track remains exact. |
| Native playback / game | No native `Unit` poses captured; no game installed or in-game verdict obtained. |

The existing 138-bone names, hierarchy, binds, geometry, UVs, normals, and
materials are preserved. Cloth/belt controls use the explicitly recorded
localized weight candidate. Opening the rig gives Arnaud an animation workspace;
it does not install that candidate into the game.

## Open and animate

The local handoff folder is
`D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig_Blends_2026-10-11`.
Use this updated handoff for new work. The previous
`WarlockEngineer_AnimationRig_Integration_2026-10-11` folder and ZIP, and the
earlier `WarlockEngineer_AnimationRig` package, remain frozen as historical
evidence. The complete updated ZIP, `START_HERE.md`, and verification receipt
will accompany the canonical v0.1.87-dev GitHub release after verified
publication and download verification. Project status records the actual
delivery; this candidate guide does not claim that it has happened.
Open `WarlockEngineer_AnimationRig.blend`, select `WARLOCK_CTRL`, and enter
Pose Mode. Animate the visible curves. Keep the scene at 60 fps and save a
separate working copy for each animation.

The controls and their drivers work with Blender Python auto-execution
disabled. The optional panel adds selection, reset, keying, pose-preserving
FK/IK switching, and verified FBX export:

1. In Blender's Text Editor, open the supplied `warlock_rig_ui.py` and choose
   **Run Script**. The reviewed script registers the panel; opening the blend
   does not execute embedded scripts.
2. Return to the 3D View, enter Pose Mode on `WARLOCK_CTRL`, and press **N**.
   Open the **Warlock** tab.
3. Alternatively, install `warlock_rig_ui.py` as a legacy add-on through
   Preferences > Add-ons > Install from Disk, then enable **Warlock Engineer
   Animator Controls**. Keep `export_animation.py` beside the script and the
   supplied `reference` folder beside that exporter. The panel also checks the
   open blend's folder for its adjacent exporter when the package moves.

Use **Select control group** to find the relevant handles. **Key selected**
keys selected control transforms and numeric custom properties. **Reset
selected** and **Reset all** restore the rig's stored neutral defaults. They
leave existing animation keys in place; with auto-key enabled, they key the
reset pose at the current frame.

| Group | Controls and use |
| --- | --- |
| Body | `root`, `torso`, `hips`, `chest`, and spine FK controls position the body. |
| Arms FK / Legs FK | Rotate the joint curves for an articulated pose. |
| Arms IK / Legs IK | Move hand/foot targets; move pole controls to choose elbow/knee direction. Leg controls include heel and toe handles. |
| Fingers | `CTRL-hand-settings-left/right` exposes overall `curl`, `spread`, and `curl_thumb/index/middle/ring/pinky`. Individual segment curves provide overrides. |
| Twist | `CTRL-forearm-twist-left/right` rotates about local Y. `auto_twist` shares wrist twist with the existing forearm roll joint, from 0 to 1; the default is 0.5. |
| Stretch and squash | `CTRL-shape-*` curves expose `length` and `volume` independently for spine, tail, each arm, and each upper leg. |
| Face / Tail | Existing head, neck, jaw, ear, nose, selected eyelid/eyebrow, and tail channels have controls. This is not a new facial deformation system. |
| Accessories | The backpack box (`ORG-j_backpack`) offsets the existing backpack. The weapon attachment box (`ORG-j_leftweaponattach`) adjusts its existing attachment frame. |
| Cloth | `CTRL-coat-left/right` adjusts the selected lower coat regions. These controls require the corrective-weight candidate body. |
| Belt corrections | `CTRL-belt-front/left/right/back-left/back-right` provides translation corrections around the waist. Rotation and scale are locked. |

For each limb, **0 means IK and 1 means FK**. Choose **Use IK** or **Use FK**
to match the current evaluated pose before changing mode. Moving the blend
slider directly does not perform this matching and can change the pose. The
switch operation checks the resulting game-bone pose; if the requested pose
cannot be represented, it reports the failure and restores the controls.
With auto-key enabled, the switch keys the matched controls and switch value.

For foot roll, keep the leg in IK and use its heel control and toe control.
These are the saved Rigify pivot mechanisms, not a new scalar roll property.
Move the foot target for placement and the pole for knee direction. Test both
feet through heel lift, toe bend, and a grounded crouch before finishing a walk
or jump clip.

`length` ranges from **0.75 to 1.35**, with a neutral value of 1. `volume`
ranges from **0 to 1**, with a default of 0.5. A value of 0 leaves transverse
thickness unchanged; 1 applies full local scale compensation. This is a
controlled scale relationship, not a guarantee of constant visible mesh
volume. Animate these properties, rather than scaling the armature object.

Coat controls adjust existing geometry through two existing skeleton channels;
five existing channels serve the belt corrections. They are animator offsets,
not a cloth simulation. The backpack is an independently weighted rigid
accessory. The launcher/warhead is a posing reference that follows the hand
attachment and is excluded from body and animation exports. This rig does not
replace the mod's runtime hose physics or attachment logic.

## Export an animation

Save the working blend, set the intended frame range, and choose **Export
verified animation FBX** in the panel. Select a destination in an authoring
folder outside every `units` directory. The exporter writes a clip `.fbx`, its
`.animation` sidecar, and an `.export.json` report. A successful report means
the exported clip passed its stated FBX checks. It is not a publication or
in-game result.

The exporter samples the evaluated `WARLOCK_GAME` pose at 60 fps, creates an
isolated export copy, and writes exactly the 138 shipping skeleton channels.
It preserves the shipping bone names, order, rest transforms, parents, object
wrappers, and the calibrated `aim_target` helper. Forward is **-Y** and up is
**Z**. It exports a single baked take with no curve simplification or added
leaf bones. Control curves, solver bones, meshes, constraints, drivers, and
the launcher reference do not leave the animation exporter.

A fresh FBX import must reproduce every sampled joint head and three axis
probes within 50 micrometres. This checks orientation and scale as well as
position. Non-finite transforms, non-positive scale, nonrepresentable local
shear, a changed skeleton, or a changed approved reference reject the export.
The report also records the source blend hash and whether unsaved edits were
present when exporting. The input blend is not saved by the exporter.

Use the supplied exporter. Ordinary **Export All**, **Apply Pose as Rest**,
automatic bone reorientation, and applying armature object transforms bypass
the reviewed bind/rest contract. Keep the original `WARLOCK_GAME` bones and
the approved source references intact.

## How the authoring scene preserves the game skeleton

`build_rig.py` starts from the audited saved Rigify control scene,
`WarlockEngineer_DoomRocket_Rigify_ControlsReady.blend`. The builder requires
its pinned SHA-256. It retains the existing control/solver rig and widgets,
removes donor objects and embedded generated UI text, clears actions and NLA
tracks while retaining solver drivers, and resets the controls. It does not
regenerate a game skeleton from a metarig or use the original mixed donor
scene as an export source.

The actual body comes from the shipping
`units/warlock_bombardier/warlock_bombardier_3p.fbx`: one 29,123-vertex mesh and
exactly 138 bones. `WARLOCK_CTRL` drives rest-calibrated world outputs.
`WARLOCK_LOCAL_REFERENCE` resolves those outputs through a copy of the original
hierarchy. `WARLOCK_GAME` receives the resulting local transforms and explicit
local stretch/squash. This world-to-local bridge preserves the shipping rest
axes and scale wrappers. Copying donor local transforms directly would
reintroduce the hierarchy and scale failures recorded in
[the model pipeline](WARLOCK_MODEL_PIPELINE.md).

The output bridge takes only the solver's world position and rotation. Rigify
can introduce world scale and shear during ordinary torso motion; carrying
those into the game hierarchy would make some poses impossible to export.
Calibration uses the inverse of the evaluated neutral rig's rigid transform,
so the bridge restores the exact shipping joint axes in neutral. Anatomical
stretch and squash come separately from each `CTRL-shape-*` control as explicit
local game-bone scale. This keeps those requested controls while removing
implicit solver scale from the world bridge.

All authoring control and mechanism bones are nondeforming. Twist uses the
existing forearm roll bones and swing/twist decomposition; no new weighted
game bones are added. The game armature is hidden during normal animation so
the animator works through the controls rather than editing its bind data.

The optional `--correct-accessories` profile changes weights on **1,776
existing vertices** using **seven previously unused existing channels**:
`j_whip_parent`, `j_whip_dynamic`, and `j_loot_sack_component1` through `5`.
Its masks cover the lower coat, waist belt, and front buckle/trim. Geometry,
topology, normals, UVs, materials, rest transforms, hierarchy, and weights
outside the masks remain unchanged. Each vertex retains at most four positive,
normalized influences. The selected rigid thigh plates, underlying trousers,
body, limbs, and backpack are excluded.

**This profile requires the candidate body and its runtime registration.**
Animation clips alone cannot make coat/belt controls deform the shipping skin.
`export_body.py` changes only the audited weight records in the approved FBX;
geometry and the game skeleton stay unchanged.

The original thirteen clips are preserved exactly. During legacy playback,
`doomrocket_outfit_correction.lua` places the seven newly weighted channels
relative to the freshly evaluated hips, after native grip updates. It restores
their existing scale and resolves the complete parent hierarchy before writing.
The same correction follows the existing corpse handoff after its pose update.
During authored playback, these corrections stop so Arnaud's coat and belt
tracks retain ownership. For a mixed transition, correction applies to the
pure incoming legacy sample before it is mixed with the displayed snapshot;
it never overwrites an incoming authored sample or the composed visible pose.
No legacy FBX resampling is needed.

## Rebuild and run the behavior tests

Run these commands from the development repository. Keep outputs outside
production `units`; the scripts reject those destinations. The saved seed and
generated blend remain external authoring assets and must not be committed.

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = git rev-parse --show-toplevel # run inside the development checkout
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$toolRoot = Join-Path $repoRoot 'tools\animation_rig'
$authoringRoot = Join-Path $repoRoot '.build\animator_rig_rebuild' # choose a fresh directory
$rigSeed = 'D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_DoomRocket_Rigify_ControlsReady.blend'
$rigFile = Join-Path $authoringRoot 'WarlockEngineer_AnimationRig.blend'
$reviewRoot = Join-Path $repoRoot '.build\animator_rig\review'
Set-Location -LiteralPath $repoRoot

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'build_rig.py') -- `
    --controls $rigSeed --output $authoringRoot --correct-accessories
if ($LASTEXITCODE -ne 0) { throw 'Rig build failed.' }

& $blenderExe --background --disable-autoexec $rigFile --python-exit-code 1 `
    --python (Join-Path $toolRoot 'test_rig_blender.py') -- `
    --output (Join-Path $authoringRoot 'validation') --render
if ($LASTEXITCODE -ne 0) { throw 'Rig behavior checks failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'test_ui_blender.py') -- `
    --rig $rigFile --output (Join-Path $authoringRoot 'validation\rig_ui_report.json')
if ($LASTEXITCODE -ne 0) { throw 'Animator panel checks failed.' }
```

The behavior tests inspect evaluated bones and weighted vertices, not merely
the presence of curve handles. They cover the neutral shipping shape, root
motion without a double transform, FK/IK limb response, heel/toe response,
finger curl/spread, automatic/manual twist, backpack isolation, every coat and
belt correction, stretch/squash boundaries, combined rotation and scaling,
and return to neutral. The UI checks cover pose-preserving switches on all
four limbs, pole modes, visible selection, reset/keying, rollback after a
failed snap, auto-key, and exporter resolution after moving the package.

The behavior test writes `validation/rig_behavior_report.json`, diagnostic
samples, and a separate `WarlockEngineer_Rig_Diagnostic.blend`. With `--render`,
it renders neutral, crouch, FK reach, IK reach, foot rolls, fingers/twist,
stretch/squash, backpack/coat/belt, and neutral-return poses. Review the images
alongside the measurements. A diagnostic action exercises controls; it is not
an artist-approved finished animation.

The frozen diagnostic has nine marked poses at frames 1, 13, 25, through 97.
After inserting all keys, the test compares every marker with its captured
pre-key pose using the full 138-bone matrices and evaluated skin. It also
requires the first and last poses to match the shipping neutral. Keep this
step-action stress case; its abrupt jumps are a separate interpolation test.

Create the separate continuous diagnostic from that frozen scene:

```powershell
$frozenDiagnosticRig = Join-Path $authoringRoot 'WarlockEngineer_Rig_Diagnostic.blend'
$continuousValidation = Join-Path $authoringRoot 'validation-continuous'
$continuousRig = Join-Path $authoringRoot 'WarlockEngineer_Rig_Continuous.blend'

& $blenderExe --background --disable-autoexec $frozenDiagnosticRig --python-exit-code 1 `
    --python (Join-Path $toolRoot 'test_rig_blender.py') -- `
    --output $continuousValidation --continuous
if ($LASTEXITCODE -ne 0) { throw 'Continuous diagnostic checks failed.' }
```

This makes a 589-frame action at 60 fps: each original pose is held for twelve
frames, with sixty-frame transitions between poses. The original 97-frame
blend is hash-checked and left untouched. All nine new markers must reproduce
the frozen bone matrices and evaluated skin; the start and return must remain
neutral. Every frame is checked for finite bones and skin, bounded positive
scale, exportable local transforms, rigid solver outputs, and bounded visible
vertex/joint movement. Read `validation-continuous/continuous_behavior_report.json`
and `continuous_samples.json`. A passing Blender report still requires the
separate FBX and SDK checks below.

## Export the candidate body and diagnostic clips

Continue in the same PowerShell session:

```powershell
$candidateBody = Join-Path $reviewRoot 'warlock_candidate_body.fbx'
$diagnosticRig = Join-Path $authoringRoot 'WarlockEngineer_Rig_Diagnostic.blend'
$diagnosticClip = Join-Path $reviewRoot 'warlock_rig_diagnostic.fbx'
$continuousClip = Join-Path $reviewRoot 'warlock_rig_continuous.fbx'

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_body.py') -- `
    --rig $rigFile --output $candidateBody
if ($LASTEXITCODE -ne 0) { throw 'Candidate body export failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_animation.py') -- `
    --rig $diagnosticRig --output $diagnosticClip --start 1 --end 97
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic animation export failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_animation.py') -- `
    --rig $continuousRig --output $continuousClip --start 1 --end 589
if ($LASTEXITCODE -ne 0) { throw 'Continuous animation export failed.' }
```

Check the candidate body's `.body-export.json` and each diagnostic clip's
`.export.json`. Keep `accessory_bind_offsets.json` and `rig_manifest.json`
with the body. Keep the original thirteen shipping FBXs and their sidecars
unchanged; do not substitute the historical adapted set.

New authored clips use this exact legacy VT2 `.animation` sidecar:

```sjson
bones = "units/warlock_bombardier/warlock_bombardier_3p"

tolerance = {
    "" = [ 0 0 0 false false false ]
}
```

The first three slots are position, rotation, and scale curve-fitting
tolerances. Exactly zero selects the installed compiler's source-key copy
path; a tiny positive value still invokes adaptive fitting. The last three
slots separately disable position, rotation, and scale packing. A four-slot
array ending in one `false` disables only position packing and leaves rotation
packing enabled by default. The exporter checks the actual staged sidecar
bytes and records its hash and six settings in the export receipt. This
prototype prioritizes fidelity; any later compression optimization needs its
own comparison before replacing it. Existing shipping sidecars retain their
original compression settings and bytes.

## Portable handoff

The animator package needs the blend, manifest, UI script, exporter, and
approved reference files together. Copy the reviewed tools and references
after building; do not commit the copied FBX, blends, renders, or archive.

```powershell
$referenceRoot = Join-Path $authoringRoot 'reference'
New-Item -ItemType Directory -Path $referenceRoot -Force | Out-Null
foreach ($fileName in @('warlock_rig_ui.py', 'export_animation.py', 'export_body.py',
        'accessory_weights.py', 'test_rig_blender.py', 'test_ui_blender.py')) {
    Copy-Item -LiteralPath (Join-Path $toolRoot $fileName) -Destination $authoringRoot -Force
}
Copy-Item -LiteralPath (Join-Path $repoRoot 'units\warlock_bombardier\warlock_bombardier_3p.fbx') `
    -Destination (Join-Path $referenceRoot 'shipping_body.fbx') -Force
Copy-Item -LiteralPath (Join-Path $repoRoot 'units\warlock_bombardier\warlock_bombardier_3p.bones') `
    -Destination (Join-Path $referenceRoot 'game.bones') -Force
Copy-Item -LiteralPath (Join-Path $repoRoot 'docs\ANIMATION_AUTHORING.md') `
    -Destination $authoringRoot -Force
```

The adjacent `reference/shipping_body.fbx` and `reference/game.bones` make the
exporters independent of this workstation's repository path. Keep them as
approved references. To test portability, copy the handoff folder to a fresh
location and run its UI test and diagnostic export with the adjacent tools.
Compare the new export report against the approved skeleton and pose checks.
Use Blender 5.2 for this handoff; another Blender version requires a new
behavior, UI, and FBX roundtrip run.

## Stage Arnaud's clip without replacing existing tracks

Run this step from the development repository, using a verified exported clip
and its adjacent `.animation` and `.export.json`. The plan creator calculates
and validates the source hashes; no manual hash inventory is required.

```powershell
$handoff = 'D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig_Blends_2026-10-11'
$clip = 'D:\Game Mods\Vermintide 2 modding\Projects\3D\ArnaudAnimations\warlock_idle.fbx'
$plan = '.build\animator_rig\arnaud_idle_plan.json'
$overlay = '.build\animation_integration_arnaud_idle'

py -3 tools/animation_rig/stage_integration.py --create-plan $plan `
    --rig-manifest (Join-Path $handoff 'rig_manifest.json') `
    --clip $clip --clip-id arnaud_idle --state base/idle `
    --body (Join-Path $handoff 'validation\warlock_candidate_body.fbx') `
    --offsets (Join-Path $handoff 'accessory_bind_offsets.json') `
    --enable-localized-profile
if ($LASTEXITCODE -ne 0) { throw 'Integration plan rejected.' }

py -3 tools/animation_rig/stage_integration.py --plan $plan --output $overlay `
    --enable-localized-profile
if ($LASTEXITCODE -ne 0) { throw 'Integration staging rejected.' }
```

Both the plan and overlay must be new paths. Use another name for a later
revision. Omit `--body`, `--offsets`, and `--enable-localized-profile` from both
steps when using the shipping body without localized coat/belt controls.
Repeat `--state` to use one clip in several compatible existing states.
Separate clips can be recorded in a reviewed JSON plan; each needs its own
verified export receipt and unique resource path.

The stage tool writes a separate overlay under `.build`, containing a new
authored animation resource, selected state bindings, the candidate body when
requested, a generated sampler ASM, and a matching trusted Lua manifest. It
copies all thirteen original FBXs and thirteen sidecars without modification.
Only selected clip/speed/aim bindings change in the visible ASM; all 154 original
transition blend times and all other state fields remain unchanged. The
sampler uses the same skeleton, states, and resources with zero internal blend
times. The overlay also copies and hash-binds the canonical
`resource_packages/doomrocket/doomrocket.package`, including its
`state_machine = [ "units/*" ]` entry. The sampler is selected dynamically by
Lua, so its presence as a compiled file or a Unit dependency alone does not
prove that the loaded mod package includes it. It rejects mixed skeleton/rest
contracts, stale hashes,
incomplete export evidence, unrecognized states, and existing output paths.
The current integration schema supports the existing single-layer graph and
its direct event transitions; it is not a general ASM replacement tool.

Strict authored ownership is the default. The grip bridge no longer copies
the native carrier's twelve upper-body bones over an authored pose. The
launcher instead follows the outfit's authored attachment, hand, and barrel
frames at rigid scale. The Blender launcher reference uses the same normalized
rotation convention, including stretched poses. During a mixed transition the
launcher follows the composed visible outfit. Legacy native links return after
the bridge finishes in legacy playback. Drop, unwield, and death release the follower
while preserving its current placement.

Authored states retain their recorded playback speed and accessories. Their
visible aim constraint is removed so it cannot rotate Arnaud's authored pose
after evaluation. An explicit `--aim-policy gameplay` keeps the existing
visible gameplay aim constraint instead; use that option deliberately for a
clip designed to accept it. The carrier's gameplay aiming and rocket launch
logic continue in both modes.

Gameplay movement remains controlled by the native AI. Author walk/run clips
in place and match their cadence to the intended movement speed; this graph
retains `root_driving = "ignore"` rather than replacing AI movement with root motion.

The ownership controller starts protection before dispatching an animation
event, protects the composed pose for the entire mixed transition, and
protects an unknown delivered event until a known state is restored. Unit
profile markers must match the staged manifest. Missing or invalid registration
fails closed rather than permitting a legacy writer to overwrite a custom pose.

The native inventory extension initializes before health on both units and
husks. Profile registration and initial animation events are retained during
that setup; pose and playback writers remain disabled until health is active.
Death, outfit replacement, and world teardown invalidate ownership.

Generated profiles now record
`cross_owner_transition_policy = "snapshot-blend-v1"` and the sampler resource
`units/warlock_bombardier/warlock_bombardier_3p/presentation_sampler`.
All 154 visible edges retain their original blend times. The sampler runs on
a hidden clone of the existing outfit with the same 138-bone skeleton; its
internal transitions have zero blend times so it evaluates the pure incoming
state. It adds no new mesh asset, game bone, or artist animation resource.

At a mixed authored/legacy edge, the compositor snapshots all 138 local poses
from the last corrected displayed outfit. It interpolates local position and
scale, and uses normalized shortest-path quaternion interpolation for rotation,
toward the moving incoming sample over the original duration. A legacy incoming
sample receives the existing twelve grip and seven localized outfit corrections
before mixing. An authored incoming sample receives neither. A transition
interrupted by another event starts from the currently displayed composition,
rather than either unmixed endpoint. Ordinary transitions within one owner
continue using the visible ASM's native blending. The policy applies to both
body profiles; localized correction requires its matching body and registration.

The outgoing pose is frozen during this bridge. This is a continuous presentation
blend toward an advancing incoming state, not an exact reproduction of a native
ASM that continues advancing both outgoing and incoming states. Arnaud should
still match endpoints and cadence for natural motion. Current tests must check
the compositor and corrected endpoints together; retaining an original duration
alone does not establish acceptable deformation.

The v0.1.86-dev handoff used immediate mixed cuts. An earlier diagnostic model
of an uncorrected native mix measured up to 178.9 mm of belt error and 102.7 mm
of hand error across thirteen clips using compiled geometry and actual Lua
endpoints. Those historical results explain why legacy correction must happen
before mixing. They are not measurements of the new compositor or native poses.

The helper's initial speed baseline matches the visible locomotion baseline.
Finite pauses and hitches invalidate the movement derivative and restart the
clock check from the observed target playhead, rather than permanently blocking
an otherwise valid transition. Invalid frame time, owner/root transforms, aim
targets, or pose data stop composition before those values reach native setters.
Gameplay aim accepts the existing matrix target only after finite axis and
translation checks. Native temporaries are consumed in the current frame.

Before spawning the helper, runtime checks the sampler's loaded availability
with `Application.can_get("state_machine", ...)`. Both its `default` and
`shadow_caster` mesh slots are hidden. Each entry handles Lua API failures
independently, and logs each stop reason once with the state/event, helper and visible
clocks, frame time, rate, and expected clock. Before handing the visible pose
back to native playback, the helper and visible destination clocks and clip
lengths must agree within the bounded clock tolerance. This guards against stale
or out-of-phase targets; it does not measure native blend weights or establish
that invisible meshes animate in the installed game.

Authored death-state replacement is currently rejected. Death uses the existing
native carrier/physics handoff, with the original death track preserved and the
localized outfit correction applied afterward. A new custom death playback
mode would require a separate reviewed implementation.

## Compile and check the staged integration

The SDK runner compiles staged and reference sources in isolated directories.
It checks the compiled Unit's actual profile markers, its own-skeleton visible
and sampler ASMs, every state resource and aim binding, authored deformation,
and all thirteen original compiled clips. The integration contract requires
all 154 visible transition times to match the original graph and all sampler
transition times to be zero, with matching state bindings and skeletons.
The compiled sampler must also be present in the canonical mod package's actual
resource inventory; a loose compiled resource or source glob alone is not that
membership proof. Require `compiled_package_closure.json` to pass its loaded
Unit/controller/clip membership checks and the compiled companion Lua's full
literal-manifest comparison, including bone order and state policies.
It refuses unsafe paths and concurrent SDK compilers.

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass `
    -File tools/animation_rig/Invoke-AnimationProbe.ps1 `
    -AnimationFbx $clip `
    -BodyFbx (Join-Path $handoff 'validation\warlock_candidate_body.fbx') `
    -ExportManifest ([IO.Path]::ChangeExtension($clip, '.export.json')) `
    -SkinProfile (Join-Path $handoff 'rig_manifest.json') `
    -OriginalLegacyClips -IntegrationOverlay $overlay -MidpointMotion `
    -ProbeRoot '.build\animation_sdk_arnaud_idle'
if ($LASTEXITCODE -ne 0) { throw 'Staged SDK contract failed.' }

py -3 tools/animation_rig/verify_runtime_outfit.py `
    --probe-root .build/animation_sdk_arnaud_idle `
    --animation-manifest (Join-Path $overlay 'integration_manifest.json') `
    --skin --post-grip
if ($LASTEXITCODE -ne 0) { throw 'Legacy outfit/runtime contract failed.' }
```

For a stock-body integration, use the shipping body FBX and omit `-SkinProfile`
and the localized runtime verifier. The runtime verifier executes the actual
Lua correction and grip modules against independent float32 engine API doubles,
using binary-decoded SDK scene poses. It checks dense keys and halfway samples,
all seven corrected bones and the weighted skin, while requiring every other
bone's local pose to remain exact. These are numerical runtime checks, not
captured native `Unit` playback or an in-game visual verdict.

The generated `compiled_animation_contract.json` must pass its diagnostic,
`original_clip_compatibility`, and `compiled_integration` results. Require all
thirteen original compiled payloads and all 138 tracks to match the shipping
reference exactly. With the localized profile, also require the complete
thirteen-clip `legacy_runtime_contract.json` to pass the unchanged 2 mm gate.
A selected single-clip investigation cannot satisfy that acceptance condition.
An existing complete skin report can be inherited only with a complete
old/current actual-Lua pose equivalence report and a fresh compiled-lane bridge:
all 24,077 local poses, the compiled geometry/skin/binds and bones, every original
animation payload, and the decoder/skin functions must match exactly. Record
that as inherited skin evidence with zero new weighted evaluations, rather than
claiming to have repeated the earlier 850,158,870 vertex comparisons. Without
that complete identity proof, require a fresh full skin audit.
That legacy audit verifies corrected endpoints, not the new mixed presentation.
Also require current sampler and executable compositor regressions, plus the
separate numerical blend report, bound to the actual reviewed runtime modules,
compiled sources, and manifest. The v0.1.86-dev receipts remain historical;
they cannot substitute for a current-source blend result.
The diagnostic blend verifier uses its pinned continuous idle fixture and
injected decoded target samples; it is not a general command that accepts every
Arnaud clip or a native playback capture. Keep that reported scope when using
its algorithm-fidelity evidence for a new integration.

Successful staging and SDK checks produce a reviewable candidate. Integration
into production must include the reviewed body, new authored resource/sidecar,
selected visible ASM changes, generated sampler ASM, Unit markers, and matching
Lua manifest together, with the reviewed canonical resource package. Follow
the full [model pipeline](WARLOCK_MODEL_PIPELINE.md) and canonical
[VMB release process](RELEASE_CHANNELS.md) for build and publication. The stage
and probe tools do not deploy or upload. Keep artist masters, donor references,
probe outputs, renders, and handoff archives outside committed source.

After a reviewed TEST release, a solo written verdict should cover the authored
state entering/exiting, interrupted transitions, launcher placement,
coat/belt/backpack response, same-owner blends, and return to legacy behavior
including death. Confirm that the hidden sampler still evaluates animation
while all its meshes are invisible; offline tests cannot establish that engine
behavior or native event clock reset and phase agreement at release. These
checks require a separately reviewed authored integration with
its matching Unit, helper ASM, body, and manifest. The default Workshop package
has no active custom profile and cannot exercise the mixed compositor. Use the
matching build log to
diagnose a failure. No recording or second-player test is required. The game is
not installed on this host, so native playback and visual acceptance are pending.
The guarded capture prototype and evidence are described in
[NATIVE_POSE_ORACLE.md](../tools/animation_rig/NATIVE_POSE_ORACLE.md).

## Historical conversion failure

The earlier `adapt_existing_clips.py` experiment is retained for reproducibility,
not used by the integration workflow above. It rewrote seven dormant tracks and
preserved 131 other source tracks. Its dense 240/960 Hz FBX corrections passed
their source checks, but the SDK resampled the legacy scenes at 30 Hz. Six clips
failed the fixed 2 mm gate; death reached 24.827 mm between retained keys.
Changing only death's scene rate to 120 fps altered all 131 other compiled
tracks and failed at 73.355 mm. Those adapted clips remain unsuitable for use.

The current runtime correction avoids that resampling boundary while retaining
all 138 original compiled tracks. Both failed receipts remain historical
evidence; do not copy their adapted clips into an integration overlay or the
operative handoff. The SDK comparisons use the binary-verified four-key Hermite
evaluator with quaternion normalization, rather than linear vectors and SLERP.
Compiled comparisons and native playback remain distinct forms of evidence.

## Research behind the implementation

Stingray enters a destination state immediately while the outgoing pose can
remain visible throughout the blend. Authored ownership therefore protects the
full transition duration. The snapshot compositor described above deliberately
uses a frozen displayed outgoing pose instead of the native advancing outgoing
state. Constraints apply after animation evaluation and
can reorient an authored pose; strict authored states therefore remove the
visible aim constraint, while gameplay aim is an explicit option.
[Stingray transitions](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/animation/animation_controllers/transitions.html),
[Stingray constraints](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/animation/animation_controllers/constraints.html)

Stingray loads resources through package definitions, including resources
selected dynamically from Lua. The canonical package therefore explicitly
includes the sampler resource type; SDK acceptance must inspect the compiled
package inventory as well as the compiled controller.
[Stingray resource package definitions](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/managing_content/loading_unloading/defining_packages.html)

Blender's bone custom shapes provide viewport handles without changing the
deform skeleton. Their display transforms and bone-size setting explain why
the builder uses body-part widget geometry and explicit shape sizing.
[Blender 5.2 PoseBone API](https://docs.blender.org/api/5.2/bpy.types.PoseBone.html)

IK affects a chain and evaluates after other constraints on the affected
bones. Separate solver/output chains avoid relying on constraint stack order
for corrections after IK.
[Blender IK constraint manual](https://docs.blender.org/manual/id/5.0/animation/constraints/tracking/ik_solver.html)

Swing/twist channel decomposition extracts axial twist independently of swing.
Driver local space includes constraint effects while excluding parenting and
rest transforms; transform space excludes constraints too. The forearm twist
uses those distinctions explicitly.
[Blender driver rotation modes](https://docs.blender.org/api/dev/bpy_types_enum_items/driver_target_rotation_mode_items.html),
[Blender 5.2 DriverTarget API](https://docs.blender.org/api/5.2/bpy.types.DriverTarget.html)

Combining rotation and nonuniform scale can create shear. The local bridge
and export reconstruction check make this an executable boundary rather than
assuming every visible Blender transform can be stored in a game clip.
[Blender 5.2 Copy Transforms API](https://docs.blender.org/api/5.2/bpy.types.CopyTransformsConstraint.html)

Visual baking records the final result of constraints and drivers. The
supplied exporter implements that principle by sampling evaluated game-bone
transforms onto an isolated export copy, then importing the FBX independently.
[Blender 5.2 Bake Action documentation](https://docs.blender.org/manual/ko/5.2/editors/nla/editing/strip.html)

Autodesk's Maya FBX documentation describes baking unsupported constraints,
sampling at the host scene's frame rate, and checking quaternion conversion.
Those principles support an evaluated bake and independent import; its UI
settings are not a replacement for this Blender exporter.
[Maya 2026 FBX export options](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Interoperability/files/GUID-FE8DBEAA-C2DD-43B3-9933-4BA4CDDEAA89.htm)

Stingray documents curve fitting and value packing as separate sources of
animation error. Its engine curves differ from DCC curves, and errors can
accumulate through a joint hierarchy, making hand and foot placement useful
checks. The historical documentation's 30 Hz export description is not a
measurement of this VT2 compiler or this 60 fps FBX.
[Stingray animation compression](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/animation/animation_compression.html),
[Stingray animation clip properties](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/stingray_help/animation/anim_clip_properties.html)

The six-slot sidecar and current Hermite interpretation were checked in the
installed `stingray_win64_dev_x64.exe`, SHA-256
`721BC354A520510EA270147C57230C87CC7E07D93F78CA1A0763D5BDB74137DE`.
The legacy tolerance parser reads slots 0–5 at virtual addresses
`0x14062cce3`–`0x14062d195`. Runtime
`InterleavedAnimationEvaluator::position`, `::rotation`, and `::scale` call the
same Hermite primitives as the compiler at `0x1407a4a54`, `0x1407a5104`, and
`0x1407a5317`. This is local binary evidence, rather than a guessed schema or
a claim based solely on old documentation. The engine author's earlier
description explains implicit derivatives and midpoint fitting.
[Niklas Frykholm's BitSquid animation article](https://bitsquid.blogspot.com/2009/11/bitsquid-low-level-animation-system.html)

The scene-rate conversion was also traced in that SDK binary. The helper at
`0x140940900` calls FBX `GetTimeMode` and `GetFrameRate`; its caller at
`0x140939db4` passes that rate to `ResetPivotSetAndConvertAnimation`, with key
reduction disabled. The installed Blender 5.2 `fbx_utils.py` maps enum 6 to
30 fps, enum 3 to 60 fps, and enum 1 to 120 fps. The native diagnostic key times
confirm the 60 fps grid, while the legacy candidate retains a 30 fps grid.
No per-bone sampling-rate setting was established.

These sources describe Blender behavior. The shipping skeleton, skin masks,
runtime limits, and acceptance tolerances come from the Warlock source,
installed SDK evidence, and executable checks, not from a generic rigging
tutorial.
