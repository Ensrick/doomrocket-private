# Development TEST quickstart

[v0.1.79-dev is published](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
Crunch already confirmed that the hose is visible and has physics on v0.1.77-dev.
The new build strengthens its resting curve while retaining motion, so [#3](https://github.com/Ensrick/doomrocket-private/issues/3)
is ready for a written visual verdict. The hand/weapon sway mismatch remains
an accepted failure under [#28](https://github.com/Ensrick/doomrocket-private/issues/28);
this build logs diagnostics but does not claim a fix.
See [current status](../PROJECT_STATUS.md) and the latest issue instructions.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARLOCK ENGINEER TEST — SOLO QUICKSTART

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warlock Engineer TEST.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.79-dev in your new console log.
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

Do not retest blocked [sound pass #5](https://github.com/Ensrick/doomrocket-private/issues/5),
[near-range ground shots #6](https://github.com/Ensrick/doomrocket-private/issues/6),
[crystal flame #15](https://github.com/Ensrick/doomrocket-private/issues/15),
[hand/weapon sway #28](https://github.com/Ensrick/doomrocket-private/issues/28), or
[portrait frame #30](https://github.com/Ensrick/doomrocket-private/issues/30)
on v0.1.79-dev. Their issue records name the engineering needed to unblock them.

Known hose limits: at most eight nearby hoses within 40 m are simulated, and
there is no body, wall, or self-collision. A clean log does not override a
tester's visual report. Issue attachments and logs are public; review them
before uploading.

Maintainer readback: `py -3 tools/analyze_hose_log.py <log> --expected-version 0.1.79-dev`.
The analyzer reports controller activity, not visible pixels; retain the log
and written observation together.
