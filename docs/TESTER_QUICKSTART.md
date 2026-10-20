# Development TEST quickstart

v0.1.94-dev addresses the repeatable ordinary-spawn crash in
[#65](https://github.com/Ensrick/doomrocket-private/issues/65). Use it only after
[project status](../PROJECT_STATUS.md) records verified canonical VMB publication
for [TEST item 3794172730](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
An uploaded source commit alone is not a Workshop update. v0.1.93-dev is the
known crashing build; do not repeat its old instructions.

The user clarified on October 20 that the local launch rule does not apply to
this Warlock publication-only TEST release because the game is absent here.
Crunch's in-game feedback remains the runtime check. No local deployment,
local game launch, alpha promotion or in-game acceptance is claimed by a build.

## First check: ordinary spawning (#65)

1. Refresh the TEST subscription and restart Vermintide 2 in the Modded Realm.
   Enable Vermintide Mod Framework above TEST; disable public item 3771657344.
2. Confirm `[doomrocket:LOAD] v0.1.94-dev` in the new console log. If it differs,
   stop and report the mismatch.
3. In a fresh keep, leave the animation rehearsal and probe off (their defaults).
   Spawn a Warlock through Creature Spawner, matching the reported crash trigger.
4. Report whether spawning succeeds. If it crashes, attach the complete matching
   log and GUID/Crashify link; a written result is enough.

After that works, other ordinary-play checks can resume. There is no requirement
to complete all issues in one session or repeat already accepted behavior.

- [#3 hose](https://github.com/Ensrick/doomrocket-private/issues/3): slight resting-curve adjustment while retaining natural flex. Visibility and secondary physics are already accepted.
- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): close shots clearing the floor and reaching the aimed point.
- [#15 crystal flame](https://github.com/Ensrick/doomrocket-private/issues/15): small native torch size, colour, attachment and cleanup. Do not repeat the retired size-command experiment.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): grip during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): Into the Nest Stormvermin waves on Cataclysm. Dutch Spice's separate Legend breed-name typo is not fixed here.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): sounds stopping at death. Absence in a short session does not disprove a rare fault.
- [#55 facing](https://github.com/Ensrick/doomrocket-private/issues/55): ordinary written observations. If it naturally happens with friends, retain available matching logs; no arranged lobby is required.

[#53](https://github.com/Ensrick/doomrocket-private/issues/53) has a separate,
optional [new-spawn controller rehearsal and passive probe](ANIMATION_AUTHORING.md#v0194-dev-runnable-native-controller-rehearsal).
Run it after the ordinary-spawn check. It uses existing stock idle and does not
establish final Blender-export or localized outfit acceptance. Original clips,
tracks, visible transitions and custom-pose ownership remain preserved.

The 30% quieter audio in #5 can receive ordinary written loudness/cleanup
feedback. Its full sound pass remains blocked on artist take/trigger selection
and flight/reload sources. Head readability #56 remains an artist decision.
Crunch's accepted #33 balance plan and #30 portrait verdict need no repeat test.

## Report a result

State what you saw or heard, the action, and whether it repeated. Attach the
complete matching log where relevant from:

```text
%APPDATA%\Fatshark\Vermintide 2\console_logs\
```

For a crash, add its GUID/Crashify link. A written observation and matching log
suffice; no video, recording, second player or coordinated lobby is requested.
Facing diagnostics record `stage=aim_update`, not post-animation agreement.

`testing` + `ready-for-testing` means a verified published candidate and a
concrete remaining question, not an accepted fix. `blocked` names a prerequisite
that prevents that test. These states are mutually exclusive. Existing accepted
written observations remain evidence after a new release.

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
