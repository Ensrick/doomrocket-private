# Development TEST quickstart

**Warlock Engineer TEST v0.1.85-dev is published and verified.**
Verification completed 2026-10-11 01:13 UTC; the [release record](https://github.com/Ensrick/doomrocket-private/releases/tag/v0.1.85-dev)
binds [the reviewed source](https://github.com/Ensrick/doomrocket-private/commit/95388a6a05298ebf2ef08caae7b181a01aab7ca4).
Publication supplies the build for testing; it does not establish its in-game result.

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

The six current TEST checks are:

- [#3 hose](https://github.com/Ensrick/doomrocket-private/issues/3): firmer resting curve while retaining natural flex; visibility and physics are already accepted.
- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): whether close shots clear the floor and reach the aimed point.
- [#15 crystal flame](https://github.com/Ensrick/doomrocket-private/issues/15): whether the flame fits the crystal and changing its command values visibly changes size.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): whether the weapon remains aligned during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): whether Into the Nest arena Stormvermin waves spawn on Cataclysm.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): whether living-enemy sounds stop on death during ordinary play; the report is rare, so absence in a short session is not final proof.

Follow the latest steps in the issue you choose; there is no requirement to
complete all six in one session. Full sound-cue work #5 needs Arnaud's new
masters, and alpha crash #34 needs crash evidence; neither is a repeat TEST
acceptance assignment.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARLOCK ENGINEER TEST — SOLO QUICKSTART

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warlock Engineer TEST.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.85-dev in the matching new log.
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
