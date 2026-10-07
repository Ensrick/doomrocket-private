# Development TEST quickstart

[v0.1.82-dev is published](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
It adds the kill-feed portrait frame, ready for a visual check under
[#30](https://github.com/Ensrick/doomrocket-private/issues/30). v0.1.81-dev applied the #33 balance plan, so [#33](https://github.com/Ensrick/doomrocket-private/issues/33)
and the longer aim in [#16](https://github.com/Ensrick/doomrocket-private/issues/16) are ready for
a solo check: report how the 2 s aim, the knockback and contact detonation feel.
The Dutch Spice arena fix [#35](https://github.com/Ensrick/doomrocket-private/issues/35)
(v0.1.80-dev) and the hose rest shape [#3](https://github.com/Ensrick/doomrocket-private/issues/3)
also await written verdicts. Hand/weapon sway remains open under
[#28](https://github.com/Ensrick/doomrocket-private/issues/28).
See [current status](../PROJECT_STATUS.md) and the latest issue instructions.

Use this short path for an issue labeled `ready-for-testing`:

```text
WARLOCK ENGINEER TEST — SOLO QUICKSTART

Setup
[ ] Refresh the TEST Workshop item 3794172730 and restart Vermintide 2.
[ ] Launch the Modded Realm. Load Vermintide Mod Framework above Warlock Engineer TEST.
[ ] Enable the TEST item only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.82-dev in your new console log.
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
[crystal flame #15](https://github.com/Ensrick/doomrocket-private/issues/15), or
[hand/weapon sway #28](https://github.com/Ensrick/doomrocket-private/issues/28)
on v0.1.82-dev. Their issue records name the engineering needed to unblock them.

Known hose limits: at most eight nearby hoses within 40 m are simulated, and
there is no body, wall, or self-collision. A clean log does not override a
tester's visual report. Issue attachments and logs are public; review them
before uploading.

Maintainer readback: `py -3 tools/analyze_hose_log.py <log> --expected-version 0.1.82-dev`.
The analyzer reports controller activity, not visible pixels; retain the log
and written observation together.
