# Native pose oracle status

The isolated harness compiles with the installed VT2 SDK. Native playback is
**unverified and blocked during SDK runtime initialization**. The November 14
toolchain route fixes the earlier compiler-entrypoint mistake but crashes
before oracle Lua starts. There are no successful native pose receipts.

## November 14 entrypoint investigation

A fresh installation audit found Vermintide 2 installed in
`C:\Program Files (x86)\Steam\steamapps\common\Warhammer Vermintide 2`:
manifest `552500`, StateFlags `4`, build `25901688`, with DX11 and DX12
executables. The earlier absence below is historical. Installation alone does
not establish a supported windowless game/oracle entrypoint; no game or Steam
session was launched, restarted or modified during this investigation.

Read-only inspection of the exact installed SDK executable, SHA-256
`721bc354a520510ea270147c57230c87cc7e07d93f78ca1a0763d5bdb74137de`,
showed that its default compile flag is enabled and its `--no-compile` handler
is inside the `--toolchain` branch. The standalone flag sequence used in
October did not select that branch. An owned toolchain directory containing
`settings/ToolChainConfiguration.config` supplies `ProjectIndex`, `Projects`,
`SourceDirectory`, `DataDirectoryBase` and `SourceRepositoryPath`. Its actual
JSON parse and runtime selection were then verified, rather than inferred
only from strings in the binary.

The runner now has an explicit **`-UseToolchainRuntime`** option for that exact
audited SDK signature. It generates a BOM-free configuration inside each
owned lane, checks the probe paths, records the configuration hash, and parses
the supported suppression/window flags before the toolchain configuration.
The default known-hash guard still rejects the failed standalone route;
`-CompileOnly` remains available. The option is not an arbitrary guard bypass
and does not count as native acceptance. Use a new dedicated probe and a
bounded timeout for any justified future investigation; repeating the current
initialization failure is not a required animator test.

The November 14 proof used a historical frozen 97-frame diagnostic, not the
upcoming artist revision. Its thin owned source mapped the original unit and
material inputs read-only. Compilation passed in 38.0 seconds, with peak
working set 2,508,652,544 bytes. The first runtime attempt (PID `48008`, start
`2026-11-14T06:39:11.487058Z`) skipped the compiler, initialized the SDK plugin
loader, then exited with **`0xC0000005`** after 2.420 seconds; peak working set
was 75,636,736 bytes. No oracle start/completion marker or `Unit` capture was
produced, and the historical source files and capture destination remained
unchanged.

One additional owned `DEBUG_ONLY_THIS_PROCESS` observation (PID `7804`, start
`2026-11-14T06:49:31.372096Z`) reproduced the failure in 2.315 seconds, with
peak working set 75,698,176 bytes. The initial loader breakpoint was continued.
The access violation was first-chance and then unhandled, writing address
`0x24` at `ntdll.dll+0x1a12d`. Recorded stack-address candidates and matching
SDK instruction/constant readback point to the internal `operator delete`
guard in `override_new.cpp:101` (`Don't use new!`) and assertion reporting.
These are **not a formally unwound call stack** and do not prove which plugin
or caller first violated the allocator policy. The final logged DLL load,
Wwise, is not enough to assign it responsibility. No engine checks or binary
instructions were disabled or patched, and no further runtime attempt followed.

Evidence is under
`.build/rig_feedback_20261114/integration/native_entrypoint_audit/`: the owned
configuration, source and compiled provenance, `runtime_probe/candidate/`
process/log receipts, `debug_result.json`, `windows_error_event.json`, and
`wer_summary.json`. Windows Error Reporting retained metadata but no dump.
**Native `Unit` pose samples remain zero.** This startup failure does not
establish a problem in an artist animation or provide a rendered game verdict.

## Historical October entrypoint evidence

The v0.1.93-dev TEST candidate adds a separate passive in-game observation path:
`/warlock_animation_rehearsal on` selects a compiled stock-clip rehearsal only
for new outfits, and `/warlock_animation_probe on` observes clocks and a bounded
matrix subset after presentation. See [the authoring guide](../../docs/ANIMATION_AUTHORING.md#v0193-dev-runnable-native-controller-rehearsal).
This does not run this oracle, provide fixed-frame captures, or establish
Blender-export/garment acceptance. Do not paste the standalone oracle into the
game: it owns its own world and application shutdown.

On 2026-10-11 at 02:21:45 UTC, SDK executable SHA-256
`721bc354a520510ea270147c57230c87cc7e07d93f78ca1a0763d5bdb74137de`
was launched with `--no-rendering --disable-default-window
--suppress-messagebox --no-compile --data-dir <isolated data>
--ini native_pose_oracle --default-console-log-path <isolated file>`.
It entered the compiler and failed with:

> Error checking prerequisistes: Source directory '' for compile does not exist.

No boot callback, `ANIMATION_ORACLE_STARTED`, `ANIMATION_ORACLE_COMPLETE`, or
`Unit` pose output appeared. The installed SDK contains one engine executable;
its own `compile_streamable_resources.bat` also invokes that executable without
`--compile`. Generic Stingray runtime flags and Lua APIs present in the binary
do not establish an accessible playback entrypoint in this VT2 mod-tools build.
The runner still refuses that standalone route for this known executable
hash by default. The separate November toolchain opt-in above does not reuse
this failed invocation as evidence of native playback.

The October 20 read-only installation audit found one configured Steam library,
`C:\Program Files (x86)\Steam`, in both `steamapps/libraryfolders.vdf` and
`config/libraryfolders.vdf`. It has no `appmanifest_552500.acf`; the residual
`common/Warhammer Vermintide 2` directory contains only configuration, chroma,
and launcher-log files, without game executables or bundles. The installed SDK
still has the failed executable hash above. No new process was launched during
that audit. Under the launch-verification requirement, a new runtime handoff
remains pending before game startup; compilation and API-double tests do not
satisfy that stage.

The standalone oracle now starts both its initial and replacement crossfades
on zero-based layer `0`, after checking that its own spawned unit is alive,
has an animation state machine, and reports exactly one layer. The packed
`animation_get_state` return count distinguishes zero layers from one layer
whose current state is nil; the latter can start frozen playback. Every sample
also checks these prerequisites before seeking. Executable Lua-double tests
exercise both crossfades, absent/multiple layers and teardown while preserving
the frozen speed, seek times and matrix convention. These are engineering
checks, not evidence that the blocked native runtime has executed these APIs.

Ignored diagnostic evidence is under
`.build/animation_native_pose_oracle/clip_00/candidate/`:
`compiler.stdout.log`, `runtime.stdout.log`, `runtime.stderr.log`,
`runtime.console.log`, `runtime.process.json`, and `runtime_expected.json`.
The process receipt identifies the owned PID, executable hash, arguments,
start time, project directory, and timeout. No game was installed or deployed,
no Workshop operation occurred, and no viewport was created.

## Intended contract, pending an accessible runtime

`native_pose_oracle.lua` uses frozen direct animation seeking after disabling
the diagnostic animation state machine. It calls `World.update_animations` at
an explicit fixed timestep and `World.update_scene(0)`. Each local/world pose
is copied into numeric 4x4 rows immediately; native temporary math counters are
restored after every bone. Matrices preserve native units, scale wrappers, and
hierarchy. Native x/y/z/translation rows are transposed into conventional
column-vector affine matrices; no interpolation or metre rescaling occurs.
Root mode is `ignore`, with `animation_wanted_root_pose` recorded separately.

Diagnostic mode requests all 138 bone names at every authored frame: the
corrected 97-frame clip and continuous 589-frame clip use index/60 seconds.
Compatibility mode requests the seven reserved bones plus `j_hips`, across all
13 adapted clips at their manifest-declared rates. Staging accepts only bounded
1/2/4 refinements of the audited 60/240 fps bases: 60/120/240 fps for ordinary
clips and 240/480/960 fps for death/staggers. The final 4× calibration plans
12,045 authored samples at 240/960 fps. Candidate and reference sidecar hashes
are read separately from their staged bytes. This remains a capture plan, not
a native acceptance result.

Receipts must bind body FBX, animation FBX/sidecar, author manifest, staged
oracle script, compiled unit/animation resources, and SDK executable hashes.
The validator checks exact indices/times, complete bone names, finite matrices,
unique node indices, a completion marker, and unchanged compiled resources.
Those checks validate a capture, not visual or in-game acceptance.

The [Unit API](https://help.autodesk.com/cloudhelp/ENU/Stingray-Help/lua_ref/obj_stingray_Unit.html)
documents frozen seeking, disabled state-machine control, and final-pose
retention. The SDK's stock LUT generator supplies the boot-script/package
pattern. Neither source proves this particular executable can run the harness.

## Isolated compilation

`Invoke-AnimationRuntimeProbe.ps1 -CompileOnly` can stage and compile the
prototype with frozen FBX/body/manifest inputs. Use a dedicated `ProbeRoot`
below the repository `.build`. `-CompatibilityOnly -AdaptedClips <directory>`
stages the 13 existing clips; `-IncludeReference` also compiles the original
body/reference lane. This mode does not run native playback or produce a pass
receipt for poses. Compile/runtime attempts are bounded and only a verified
process created by this runner may be stopped.

Existing decoded animation checks must retain their stated evaluator evidence
and limitations; this failed bootstrap cannot strengthen them to actual
`Unit` playback or game acceptance.
