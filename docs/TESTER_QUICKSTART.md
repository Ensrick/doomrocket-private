# Development TEST quickstart

[v0.1.77-dev is published](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
Crunch has already confirmed that its hose is visible and has physics, and
reported that the rest shape is too soft. The hand/weapon sway mismatch is also
an accepted visual failure. Both need engineering and a **new published TEST
build** before another acceptance test; do not repeat them on v0.1.77-dev.
See [current status](../PROJECT_STATUS.md) and the latest issue instructions.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARPROCKET BOMBARDIER TEST — SOLO QUICKSTART

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warprocket Bombardier.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.77-dev in your new console log.
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

Do not retest currently blocked [hose rest shape #3](https://github.com/Ensrick/doomrocket-private/issues/3),
[sound pass #5](https://github.com/Ensrick/doomrocket-private/issues/5),
[crystal flame #15](https://github.com/Ensrick/doomrocket-private/issues/15), or
[hand/weapon sway #28](https://github.com/Ensrick/doomrocket-private/issues/28)
on v0.1.77-dev. Their issue records name the engineering needed to unblock
them. A future published build can ask for specific visual checks of a firmer
but still moving hose and a launcher that stays in the Engineer's hands.

Known hose limits: at most eight nearby hoses within 40 m are simulated, and
there is no body, wall, or self-collision. A clean log does not override a
tester's visual report. Issue attachments and logs are public; review them
before uploading.

Maintainer readback: `py -3 tools/analyze_hose_log.py <log> --expected-version 0.1.77-dev`.
The analyzer reports controller activity, not visible pixels; retain the log
and written observation together.
