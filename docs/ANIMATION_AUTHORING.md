# Warlock Engineer animation authoring

This rig lets Arnaud animate the existing Warlock Engineer model in Blender
5.2. It provides body-part control curves, arm and leg FK/IK, finger curl and
spread, foot rolls, forearm twist, bounded stretch and squash, backpack offsets,
and localized coat and belt corrections. The user's October 10, 2026 request
explicitly authorizes engineering to prepare this animation rig. It does not
transfer responsibility for new character art, models, or sound masters.

The authoring files are candidates outside the repository. They do not change
the published TEST v0.1.85-dev or public alpha v0.1.59-alpha. Blender behavior,
FBX roundtrip, SDK compilation, and an in-game visual verdict are separate
checks. Read the generated reports for their actual results; this guide does
not claim native playback or an in-game pass.

## Measured authoring and SDK results, October 11, 2026 UTC

| Check | Result and scope |
| --- | --- |
| Blender controls | 68/68 behavior checks; neutral skin differs from the approved body by at most 5.70 micrometres. |
| Animator panel | 39/39 checks; worst pose-preserving FK/IK switch error 0.342 mm. |
| Continuous motion | 19/19 checks across 589 frames and 81,282 evaluated bones; all nine authored pose markers match exactly. |
| Independent FBX import | Both 97-frame and 589-frame exports pass; maximum joint/axis-probe error under 3.2 micrometres. |
| Portable package | 17/17 checks using adjacent references and the final exporter; source files remain unchanged. |
| Decoded SDK deformation | The 97-frame and 589-frame diagnostics stay below 0.991 mm across 3,425,070 and 20,797,590 weighted vertex comparisons respectively. These sample authored frames. |
| Continuous between-key motion | 588 halfway poses, 81,144 bone comparisons against raw FBX scalar TRS and its full hierarchy; maximum joint error 0.443 mm and 0.1 m axis-probe error 0.603 mm, below the 2 mm gate. No midpoint skin or native `Unit` samples are claimed. |
| Existing thirteen clips, FBX | All thirteen pass 1,662,210 bone comparisons. The 131 untouched tracks have zero pose error; the seven calibrated tracks stay within 2.253 micrometres at keys and 0.301 mm between keys. |
| Existing thirteen clips, SDK | The current calibrated candidate fails the 2 mm gate on run, run-start, shoot-loop, death and both staggers. All 131 other compiled tracks remain exact; the largest correction error is 24.827 mm between retained SDK keys. This weight profile is blocked from integration. |
| Native playback / game | No native `Unit` poses captured; no game installed or in-game verdict obtained. |

The existing 138-bone names, hierarchy, binds, geometry, UVs, normals, and
materials are preserved. Cloth/belt controls use the explicitly recorded
localized weight candidate. Opening the rig gives Arnaud an animation workspace;
it does not install that candidate into the game.

## Open and animate

The local handoff folder is
`D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig`.
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

**This profile requires a candidate body FBX and matching clips together.**
Animation clips alone cannot make new coat/belt controls deform the current
shipping skin. `export_body.py` patches only the audited weight records in the
original shipping FBX and independently checks the resulting body. It does
not replace geometry or rewrite the game skeleton.

The original thirteen clips contain tracks on those newly weighted channels.
`adapt_existing_clips.py` rewrites only those seven dormant tracks so they
follow the pelvis through the correct rest offsets. All other encoded
property payloads, IDs, connections, defaults, binds, geometry, skin data, and
the aim helper remain unchanged. The source-FBX bootstrap receives independent
roundtrip checks at 60 samples/second, or 240 for fast death/stagger clips,
plus probes between corrective keys. The final SDK-calibrated set uses the
240/960 Hz refinement described below. Do not combine the corrective-weight
body with the original thirteen clips: their old dormant motion can move the
newly weighted coat and belt incorrectly.

## Rebuild and run the behavior tests

Run these commands from the development repository. Keep outputs outside
production `units`; the scripts reject those destinations. The saved seed and
generated blend remain external authoring assets and must not be committed.

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = 'C:\Users\danjo\source\repos\doomrocket'
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$toolRoot = Join-Path $repoRoot 'tools\animation_rig'
$authoringRoot = 'D:\Game Mods\Vermintide 2 modding\Projects\3D\WarlockEngineer_AnimationRig'
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

## Export the candidate body, legacy clips, and diagnostic clip

Continue in the same PowerShell session:

```powershell
$candidateBody = Join-Path $reviewRoot 'warlock_candidate_body.fbx'
$adaptedClips = Join-Path $reviewRoot 'adapted_clips'
$diagnosticRig = Join-Path $authoringRoot 'WarlockEngineer_Rig_Diagnostic.blend'
$diagnosticClip = Join-Path $reviewRoot 'warlock_rig_diagnostic.fbx'
$continuousClip = Join-Path $reviewRoot 'warlock_rig_continuous.fbx'

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_body.py') -- `
    --rig $rigFile --output $candidateBody
if ($LASTEXITCODE -ne 0) { throw 'Candidate body export failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'adapt_existing_clips.py') -- `
    --clips-root (Join-Path $repoRoot 'units\warlock_bombardier\anims') `
    --output $adaptedClips
if ($LASTEXITCODE -ne 0) { throw 'Legacy clip adaptation failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_animation.py') -- `
    --rig $diagnosticRig --output $diagnosticClip --start 1 --end 97
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic animation export failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'export_animation.py') -- `
    --rig $continuousRig --output $continuousClip --start 1 --end 589
if ($LASTEXITCODE -ne 0) { throw 'Continuous animation export failed.' }
```

Check the candidate body's `.body-export.json`, the diagnostic clip's
`.export.json`, and `adapted_clips/adapted-clips.json`. The legacy adaptation
summary must report `all_thirteen_adapted: true`; a selected single-clip probe
does not satisfy that condition. Keep all thirteen adapted FBX files and their
sidecars with the candidate body for later integration.

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
own comparison before replacing it. Initial source-FBX adapters retain their
shipping sidecars. The final SDK-calibrated adapters retain the original
default policy and add exact-name lossless overrides for only the seven
corrective channels, as described below.

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

## Isolated SDK check and eventual mod integration

The SDK runner compiles candidate and reference sources in an isolated probe
directory, then decodes their compiled skeleton, body, animation, skin weights,
and aim controller. It validates SDK-weighted vertex samples against the
authoring samples. It also refuses unsafe probe paths and concurrent SDK
compiler processes. The compiler defaults to the installed Vermintide 2 SDK.

```powershell
& powershell -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $toolRoot 'Invoke-AnimationProbe.ps1') `
    -AnimationFbx $continuousClip -BodyFbx $candidateBody `
    -ExportManifest ([IO.Path]::ChangeExtension($continuousClip, '.export.json')) `
    -SkinProfile (Join-Path $authoringRoot 'rig_manifest.json') `
    -AdaptedClips $adaptedClips `
    -MidpointMotion `
    -ProbeRoot '.build\animation_sdk_probe'
if ($LASTEXITCODE -ne 0) {
    $bootstrapReport = Get-Content -LiteralPath (Join-Path $repoRoot `
        '.build\animation_sdk_probe\compiled_animation_contract.json') -Raw | ConvertFrom-Json
    $unexpectedErrors = @($bootstrapReport.adapted_clip_compatibility.fidelity_errors | `
        Where-Object { $_ -notmatch 'SDK hip-follow correction exceeds 2 mm' })
    if ($bootstrapReport.diagnostic_status -ne 'sdk-compiled-and-decoded' -or `
        -not $bootstrapReport.adapted_clip_compatibility.all_thirteen_compiled -or `
        $unexpectedErrors.Count) { throw 'SDK bootstrap failed outside legacy corrective fitting.' }
    Write-Output 'Raw legacy adapters failed corrective fitting; continue with calibrated targets below.'
}
```

The report is `.build/animation_sdk_probe/compiled_animation_contract.json`.
When corrective weights are included, require `all_thirteen_compiled` in its
legacy-clip compatibility result. This compares the 131 unmodified native
tracks with separately compiled shipping clips and checks the seven corrective
channels. A diagnostic-only pass does not cover the existing animation set.
This runner does not deploy or upload. It is an isolated authoring check,
separate from the canonical [release process](RELEASE_CHANNELS.md). No game is
installed on the authoring host, so in-game acceptance requires the published
tester's written verdict after an explicitly reviewed integration and release.

The first source-FBX adapters are calibration-bootstrap inputs and can fail the
seven-channel SDK gate because the
shipping pelvis and corrective curves are fitted independently. In the initial
probe this reached 16.95 mm. A source-FBX hip-follow pass alone is insufficient.
Keep that failed comparison as evidence; require its diagnostic result to pass
and its thirteen unmodified-track checks to succeed before calibrating.

Generate corrective local targets from the separately compiled shipping lane,
then build the final candidate set. The targets bind the SDK executable,
compiled unit and clips, original FBX/sidecars, and skeleton hashes. They use the
binary-verified evaluator and include both key times and midpoints. This does
not claim captured native poses. Target generation requires the hash-bound,
successful shipping-reference lane even though the raw candidate's seven-track
audit failed. The preceding bootstrap guard also requires the diagnostic and
all thirteen unmodified-track checks; target generation alone is not that gate.
This bootstrap exception does not waive the final acceptance gate.

```powershell
$nativeTargets = Join-Path $repoRoot '.build\animator_rig\sdk_hip_targets_dense4.json'
$calibratedClips = Join-Path $repoRoot '.build\animator_rig\adapted_native_clips'
py -3 (Join-Path $toolRoot 'verify_compiled_animation.py') `
    --probe-root '.build\animation_sdk_probe' --export-shipping-targets $nativeTargets `
    --target-sample-multiplier 4
if ($LASTEXITCODE -ne 0) { throw 'Shipping target provenance check failed.' }

& $blenderExe --background --factory-startup --disable-autoexec --python-exit-code 1 `
    --python (Join-Path $toolRoot 'adapt_existing_clips.py') -- `
    --output $calibratedClips --native-targets $nativeTargets
if ($LASTEXITCODE -ne 0) { throw 'Calibrated legacy adaptation failed.' }

& powershell -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $toolRoot 'Invoke-AnimationProbe.ps1') `
    -AnimationFbx $continuousClip -BodyFbx $candidateBody `
    -ExportManifest ([IO.Path]::ChangeExtension($continuousClip, '.export.json')) `
    -SkinProfile (Join-Path $authoringRoot 'rig_manifest.json') `
    -AdaptedClips $calibratedClips -MidpointMotion `
    -ProbeRoot '.build\animation_sdk_calibrated_probe'
if ($LASTEXITCODE -ne 0) { throw 'Final calibrated SDK contract failed.' }
```

Exact quoted bone names select the seven overrides in the legacy tolerance
dictionary. The final gate checks that all 131 other compiled tracks remain
identical, all seven corrective tracks are unpacked, and pelvis-follow head
and axis errors remain below 2 mm at frames and midpoints. Use this calibrated
set with the candidate body only after its compiled compatibility report passes;
the current candidate does not pass. The earlier source-only set is also
unsuitable for integration.
The calibrated target set samples ordinary clips at 240 Hz and fast death/
stagger clips at 960 Hz, with independent half-key checks. The extra density
preserves the 0.5 mm FBX-local gate rather than relaxing it; original timing and
all unreserved source curves remain unchanged. This source-FBX result does not
remove the compiled sampling failure described below.

The thirteen original FBXs retain scene `TimeMode = 6` and
`CustomFrameRate = 30`. The SDK samples them at 30 Hz before fitting and packing,
discarding the added 240/960 Hz correction keys. At the retained SDK keys the
calibrated candidate's maximum head error is 1.134 micrometres and its 0.1 m
axis-probe error is 1.692 micrometres. Between those keys, six clips exceed the
unchanged 2 mm gate. Death reaches 24.827 mm. More source keys cannot resolve a
scene-rate bottleneck. The diagnostic FBXs declare 60 fps and retain that
sampling grid; their passing measurements above cover those diagnostic clips.

A single isolated death-clip experiment changed only the two scene-rate
scalars to supported 120 fps, preserving all other FBX bytes. The SDK retained
261 native times instead of 66, but all 131 other compiled track dictionaries
changed. The old shipping-parent calibration also became invalid, reaching
73.355 mm in that experiment. It fails the same compatibility contract; it is
not a replacement candidate. No additional rate experiments or tolerance
relaxations followed. Until a compatible conversion is established or a
separately reviewed matching animation set exists, keep the corrective-weight
body and thirteen candidate clips out of production. Arnaud can use the Blender
controls now; the authoring package does not resolve this engine boundary.

Compiled key times are not evidence of a fixed importer rate. Adaptive curve
fitting can insert interval midpoints, producing apparent 25 ms spacing in a
1.6-second diagnostic clip. Both diagnostic FBX scenes remain 60 fps. The installed SDK's compiler and
runtime use the same four-key, time-weighted Hermite evaluator; position and
scale interpolate as vectors, while quaternion components interpolate and
are normalized. Linear vectors plus SLERP do not reproduce that evaluator.
Compiled-data checks must use the matching interpolation, retain the stated
2 mm weighted-deformation gate, and distinguish exact-key fidelity from
between-key motion. A step-action discontinuity and a continuous motion are
different test cases; neither may be reported as passing before its report
actually passes.

These are decoded compiled-data comparisons, not captured `Unit` playback.
The installed mod-tools executable entered compiler prerequisites even with
`--no-compile` and a boot INI; it produced no Lua boot marker or native pose
samples. The guarded native capture prototype and exact evidence are described
in [NATIVE_POSE_ORACLE.md](../tools/animation_rig/NATIVE_POSE_ORACLE.md).
Native playback remains unverified until an accessible runtime is available.

Before integrating authored arm clips, reconcile the v0.1.85 grip alignment
module: it writes twelve upper-body game joints after outfit animation
evaluation. It would overwrite authored arm/hand poses during its supported
events. This rig does not resolve that runtime ownership conflict. Preserve
the own-skeleton state machine, native carrier, weapon links, calibrated aim
helper, corpse handoff, and hose physics during that follow-up.
The five belt channels descend from `j_spine` and `j_spine1`, which that module
also writes. Their isolated SDK hip-follow result must be checked again after
the runtime pose owners are reconciled; the coat channels descend from hips.

An eventual corrective-weight integration must include the reviewed candidate
body and all thirteen adapted legacy clips, plus any separately reviewed new
clips. It must pass the full existing Warlock asset pipeline and the canonical
VMB release gates. Keep authoring masters, reference/donor payloads, SDK probe
outputs, renders, and handoff archives outside committed source.

## Research behind the implementation

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
