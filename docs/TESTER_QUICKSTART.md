# Development TEST quickstart

**Warlock Engineer TEST v0.1.88-dev is published and verified.**
Verification completed 2026-10-12 00:46 UTC; the [release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.88-dev)
binds [the reviewed source](https://github.com/Ensrick/doomrocket-private/commit/d9282f8799b7b53ad99e2cd48fcf164a2fadee29).
Publication supplies the build for testing; it does not establish its in-game result.

v0.1.90-dev is the queued candidate. It retains the temporary gem-flame omission,
30% quieter custom sounds and small hose adjustment from v0.1.89-dev, and adds
guarded aiming, bounded facing diagnostics and animation parent-frame fixes.
The user has held publication; neither candidate is available on Workshop.
Use current status for the verified version; do not test unpublished changes.

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

The five current published TEST checks are:

- [#3 hose](https://github.com/Ensrick/doomrocket-private/issues/3): firmer resting curve while retaining natural flex; visibility and physics are already accepted.
- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): whether close shots clear the floor and reach the aimed point.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): whether the weapon remains aligned during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): whether Into the Nest arena Stormvermin waves spawn on Cataclysm.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): whether living-enemy sounds stop on death during ordinary play; the report is rare, so absence in a short session is not final proof.

Follow the latest steps in the issue you choose; there is no requirement to
complete all five in one session. The rejected flame (#15) needs a suitable
small effect; no size-command rerun is requested. Full sound-cue work #5 has two
aiming candidates awaiting artist selection/trigger, while flight/reload sources
are still absent. Alpha crash #34 needs crash evidence; none is a repeat TEST
acceptance assignment.

Facing report #55 has guarded aim handling and bounded diagnostics in the queued
candidate. If a mismatch is noticed during ordinary play after publication,
describe the phase and attach existing matching logs. No organised multiplayer
session or video is required. Head readability #56 remains an artist decision.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARLOCK ENGINEER TEST — SOLO QUICKSTART

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warlock Engineer TEST.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.88-dev in the matching new log.
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
