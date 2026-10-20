# Development TEST quickstart

**TEST testing is suspended on [#65](https://github.com/Ensrick/doomrocket-private/issues/65).**

Crunch's matching v0.1.93-dev log confirms a repeatable ordinary-spawn crash in
native animation-layer diagnostics. No rehearsal activation is required by the
report. Do not run the old #53 rehearsal or regular Warlock checks while this
hold remains.

v0.1.94-dev is an unpublished source candidate. Before handing over a new runtime
build, engineering must silently launch the actual installed candidate in its
supported background/windowless mode and record startup/menu progress, errors,
timeout and relevant loading/memory results. No local game manifest `552500`,
executables or bundles are present; the installed SDK fails before oracle Lua
boot. Installed-candidate launch verification and handoff therefore remain
pending. A successful compile or VMB upload cannot replace this gate. Crunch is
not being asked to perform the candidate's first launch.

**Historical publication: Warlock Engineer TEST v0.1.93-dev.**
Verification completed 2026-10-17 02:08:24 UTC (96,168,463 bytes; content handle
`2064919069194644398`); the [release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.93-dev)
binds [the reviewed source](https://github.com/Ensrick/doomrocket-private/commit/c1e7c00162e468962862cf155850c86889be5051)
([PR #63](https://github.com/Ensrick/doomrocket-private/pull/63)).
This records delivery only. The later #65 crash suspends its testing instructions.

Published v0.1.93-dev adds a specific opt-in controller rehearsal
for #53. Its verified publication is recorded in [project status](../PROJECT_STATUS.md);
the [new-spawn command and probe instructions](ANIMATION_AUTHORING.md#v0193-dev-runnable-native-controller-rehearsal) are historical and suspended.
It uses existing stock animation and does not establish a Blender-export or
localized garment pass. Ordinary play on v0.1.92-dev cannot run that new check.

Published v0.1.92-dev repairs the offline animation evidence checker and retains
v0.1.91-dev gameplay and assets. No extra visual test or recording is required
for the checker fix; ordinary flame feedback remains pending. Native authored
playback had no active profile in v0.1.92-dev; the later v0.1.93-dev rehearsal is suspended. Existing
v0.1.91-dev sessions and written reports remain useful for the unchanged flame,
audio, hose and aiming behavior. No retest is needed solely for this checker
maintenance update.

Published v0.1.91-dev adds a
small native pickup-torch candidate at the crystal and optimizes repeated
skeleton checks in the separately staged authored-animation path. Issue #15
needs a written verdict on visible size, colour, attachment and
cleanup during ordinary play. Do not repeat the retired size-command experiment.
The full authored integration in #53 still needs its staged profile and native
runtime validation; normal default Workshop gameplay cannot exercise it.

Published v0.1.90-dev includes the temporary gem-flame omission, 30% quieter
custom sounds and small hose adjustment prepared for the unpublished
v0.1.89-dev. It adds guarded aiming, bounded facing diagnostics and animation
parent-frame fixes. The authored integration remains separately staged; the
default package has no active custom profile. Public alpha is unchanged.

The [TEST Workshop item](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730)
still contains the published v0.1.93-dev build with the reported crash. Follow
the hold in [current status](../PROJECT_STATUS.md). A candidate in source is not
evidence of publication, successful launch or readiness.

Crunch accepted the five-change balance plan in v0.1.84-dev
([#33](https://github.com/Ensrick/doomrocket-private/issues/33#issuecomment-6101970608)),
including the movable camera during the flailing throw and the contact/velocity
impact fix. Do not ask him to repeat that completed acceptance. The Dutch Spice
arena fix [#35](https://github.com/Ensrick/doomrocket-private/issues/35) awaits an
arena-wave verdict; its earlier acceptance plan uses Cataclysm while Dutch
Spice's separate Legend breed-name typo remains. Hose [#3](https://github.com/Ensrick/doomrocket-private/issues/3)
awaits a verdict on the firmer resting curve, with visibility and physics already
accepted. These checks remain held on #65.

The seven earlier ordinary-play TEST checks below are **held on #65**:

- [#3 hose](https://github.com/Ensrick/doomrocket-private/issues/3): firmer resting curve while retaining natural flex; visibility and physics are already accepted.
- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): whether close shots clear the floor and reach the aimed point.
- [#15 crystal flame](https://github.com/Ensrick/doomrocket-private/issues/15): whether the small native torch's visible size, colour and attachment suit the crystal and it disappears on death, drop and map change. Green colour is unverified; do not use the retired size command.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): whether the weapon remains aligned during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): whether Into the Nest arena Stormvermin waves spawn on Cataclysm.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): whether living-enemy sounds stop on death during ordinary play; the report is rare, so absence in a short session is not final proof.
- [#55 facing](https://github.com/Ensrick/doomrocket-private/issues/55): ordinary-play observations after the aim guards; if a mismatch is noticed while playing with friends, describe the phase and retain available matching logs. No arranged multiplayer session is required.

Do not resume these steps until the hold is cleared. Existing written verdicts
remain evidence; no size-command rerun is requested. The 30% audio reduction in
#5 is published, with its remaining loudness/cleanup check also held. The full
sound-cue pass still needs artist selection/trigger for the two aiming
candidates, plus flight/reload sources. Alpha crash #34 needs crash evidence.
Native animation #53 remains blocked on the crash fix, installed-candidate
launch verification and later native/custom-export acceptance.

Facing diagnostics in #55 record `stage=aim_update`; they do not establish
post-animation facing agreement. Existing written observations remain evidence.
No organised multiplayer session or video is required. Head readability #56
remains an artist decision.

Arnaud's [latest #35 attachment](https://github.com/Ensrick/doomrocket-private/issues/35#issuecomment-6158706396)
loads v0.1.88-dev and records PlayFab HTTP 500/error 1110 during title-state
startup, followed by the backend popup and an orderly exit. It has no
arena-specific stack or verdict. v0.1.90-dev does not target that backend
failure; the Dutch Spice arena check remains open.

The following v0.1.93-dev checklist is **historical and suspended**. It is kept
for interpreting earlier reports, not as a new test assignment. Future checks
need fresh version-specific instructions after engineering clears the launch
gate, publication and issue-specific hold:

```text
HISTORICAL v0.1.93-dev SOLO CHECKLIST - SUSPENDED ON #65

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warlock Engineer TEST.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.93-dev in the matching new log.
[ ] If the version differs, stop and report the mismatch.

Test and report
[ ] Pick a ready-for-testing issue and follow its latest, issue-specific steps.
[ ] Note what you actually saw or heard, including the action and whether it repeated.
[ ] Attach the matching complete console log from:
    %APPDATA%\Fatshark\Vermintide 2\console_logs\
[ ] For a crash, include the GUID and Crashify link if available.
[ ] Add the result to the issue: https://github.com/Ensrick/doomrocket-private/issues
```

A written observation and its matching log are enough. No recording, second
player, or coordinated lobby test is required. If a bug appears while playing
with friends, report it normally; the process does not require arranging that
session in advance.

An issue marked `blocked` names a missing prerequisite such as engineering,
publication, source assets, or crash evidence. Resolve that prerequisite before
asking for an acceptance test it prevents. An issue marked
`ready-for-testing` requires installed-candidate launch verification, verified
publication and a concrete remaining question. Older labels do not override the
#65 hold. Do not re-run accepted steps after a newer written verdict.

[Alpha crash #34](https://github.com/Ensrick/doomrocket-private/issues/34) needs a
crash-bearing log or GUID from the reported alpha version, rather than another
TEST acceptance check. [Public corpse wake/cleanup #2](https://github.com/Ensrick/doomrocket-public/issues/2)
uses public item 3771657344 and its own current alpha banner; do not enable both
channels to perform that check.

Known hose limits: at most eight nearby hoses within 40 m are simulated, and
there is no body, wall, or self-collision. A clean log does not override a
tester's visual report. Issue attachments and logs are public; review them
before uploading.

Maintainer readback: `py -3 tools/analyze_hose_log.py <log> --expected-version <loaded-version>`.
The analyzer reports controller activity, not visible pixels; retain the log
and written observation together.
