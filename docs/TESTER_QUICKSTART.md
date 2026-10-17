# Development TEST quickstart

**Warlock Engineer TEST v0.1.93-dev is published and verified.**
Verification completed 2026-10-17 02:08:24 UTC (96,168,463 bytes; content handle
`2064919069194644398`); the [release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.93-dev)
binds [the reviewed source](https://github.com/Ensrick/doomrocket-private/commit/c1e7c00162e468962862cf155850c86889be5051)
([PR #63](https://github.com/Ensrick/doomrocket-private/pull/63)).
Publication supplies the build for testing; it does not establish its in-game result.

Published v0.1.93-dev adds a specific opt-in controller rehearsal
for #53. Its verified publication is recorded in [project status](../PROJECT_STATUS.md);
use the [new-spawn command and bounded probe instructions](ANIMATION_AUTHORING.md#v0193-dev-runnable-native-controller-rehearsal).
It uses existing stock animation and does not establish a Blender-export or
localized garment pass. Ordinary play on v0.1.92-dev cannot run that new check.

Published v0.1.92-dev repairs the offline animation evidence checker and retains
v0.1.91-dev gameplay and assets. No extra visual test or recording is required
for the checker fix; ordinary flame feedback remains pending. Native authored
playback had no active profile in v0.1.92-dev; use the v0.1.93-dev rehearsal above. Existing
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

Use the verified [TEST Workshop build](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730)
named in [current status](../PROJECT_STATUS.md) and the issue's latest test
instructions. A candidate in source is not evidence that it has been published.

Crunch accepted the five-change balance plan in v0.1.84-dev
([#33](https://github.com/Ensrick/doomrocket-private/issues/33#issuecomment-6101970608)),
including the movable camera during the flailing throw and the contact/velocity
impact fix. Do not ask him to repeat that completed acceptance. The Dutch Spice
arena fix [#35](https://github.com/Ensrick/doomrocket-private/issues/35) awaits an
arena-wave verdict; test it on Cataclysm while Dutch Spice's separate Legend
breed-name typo remains. Hose [#3](https://github.com/Ensrick/doomrocket-private/issues/3)
awaits a verdict on the firmer resting curve, with visibility and physics already
accepted. Follow each issue's current instructions for other work.

The seven current published TEST checks are:

- [#3 hose](https://github.com/Ensrick/doomrocket-private/issues/3): firmer resting curve while retaining natural flex; visibility and physics are already accepted.
- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): whether close shots clear the floor and reach the aimed point.
- [#15 crystal flame](https://github.com/Ensrick/doomrocket-private/issues/15): whether the small native torch's visible size, colour and attachment suit the crystal and it disappears on death, drop and map change. Green colour is unverified; do not use the retired size command.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): whether the weapon remains aligned during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): whether Into the Nest arena Stormvermin waves spawn on Cataclysm.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): whether living-enemy sounds stop on death during ordinary play; the report is rare, so absence in a short session is not final proof.
- [#55 facing](https://github.com/Ensrick/doomrocket-private/issues/55): ordinary-play observations after the aim guards; if a mismatch is noticed while playing with friends, describe the phase and retain available matching logs. No arranged multiplayer session is required.

Follow the latest steps in the issue you choose; there is no requirement to
complete all seven in one session. No size-command rerun is requested. The 30% audio reduction in #5
is live and can receive an ordinary written loudness/cleanup verdict. The full
sound-cue pass still needs artist selection/trigger for the two aiming
candidates, plus flight/reload sources. Alpha crash #34 needs crash evidence.
Staged native animation #53 remains blocked because the default package cannot
exercise its authored sampler. None is a repeat unavailable acceptance assignment.

Facing diagnostics in #55 record `stage=aim_update`; they do not establish
post-animation facing agreement. Existing written observations remain evidence.
No organised multiplayer session or video is required. Head readability #56
remains an artist decision.

Arnaud's [latest #35 attachment](https://github.com/Ensrick/doomrocket-private/issues/35#issuecomment-6158706396)
loads v0.1.88-dev and records PlayFab HTTP 500/error 1110 during title-state
startup, followed by the backend popup and an orderly exit. It has no
arena-specific stack or verdict. v0.1.90-dev does not target that backend
failure; the Dutch Spice arena check remains open.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARLOCK ENGINEER TEST — SOLO QUICKSTART

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
`ready-for-testing` names a verified published build and a concrete remaining
question. Do not re-run old acceptance steps after a newer written verdict.

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
