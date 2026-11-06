# Development TEST quickstart

The current verified Workshop TEST is **v0.1.98-dev**. Crunch accepted the
v0.1.94-dev ordinary-spawn crash fix [#65](https://github.com/Ensrick/doomrocket-private/issues/65);
that issue is closed and needs no repeat acceptance check.

[Project status](../PROJECT_STATUS.md) records verified canonical VMB publication
for [TEST item 3794172730](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
Crunch's November 4 log confirms v0.1.97-dev. Flame colour/size and hose sway
are accepted. Verified v0.1.98-dev supplies W-shape and shipping legacy traversal
candidates for written in-game verdicts.
The v0.1.95-dev upload failed metadata validation; its GitHub release is not a
verified Workshop update. Its historical build record is not a current test target.

The user clarified on October 20 that the local launch rule does not apply to
this Warlock publication-only TEST release because the game is absent here.
Crunch's in-game feedback remains the runtime check. No local deployment,
local game launch, alpha promotion or in-game acceptance is claimed by a build.

## Current v0.1.98-dev follow-up

1. Refresh the TEST subscription and restart Vermintide 2 in the Modded Realm.
   Enable Vermintide Mod Framework above TEST; disable public item 3771657344.
2. Confirm `[doomrocket:LOAD] v0.1.98-dev` in the new console log. If it differs,
   report the mismatch before judging these changes.
3. [#69 first-spawn loading](https://github.com/Ensrick/doomrocket-private/issues/69):
   spawn one Warlock and say whether you notice a hitch, then attach the log. The
   log has the timing, so nothing else is needed. The v0.1.96-dev log measured a
   216 ms blocking material-package load on the first spawn; this build requests
   it asynchronously when the level world and required donors are ready.

[#15 flame colour and size](https://github.com/Ensrick/doomrocket-private/issues/15#issuecomment-6624849555)
and [#3 hose sway](https://github.com/Ensrick/doomrocket-private/issues/3#issuecomment-6624724867)
are accepted and need no repeated acceptance check. On v0.1.98-dev, describe
whether the hose retains its W-shaped resting bends during walking and stopping
(#3), and whether the visible body and weapon follow ordinary vaults/landings
and return naturally to walking or aiming (#53). The current sway settings are
retained. This traversal check applies to the shipping legacy profile; it does
not accept custom-export playback, localized outfits or the native oracle. The existing written reports and log are sufficient;
no repeated failure demonstration or recording is requested.

There is no requirement to complete all issues in one session or repeat
already accepted behavior. Written observations and matching logs suffice.

- [#6 rocket clearance](https://github.com/Ensrick/doomrocket-private/issues/6): close shots clearing the floor and reaching the aimed point.
- [#28 launcher/hand alignment](https://github.com/Ensrick/doomrocket-private/issues/28): grip during ordinary movement, aim and reload.
- [#35 Dutch Spice arena](https://github.com/Ensrick/doomrocket-private/issues/35): Into the Nest Stormvermin waves on Cataclysm. Dutch Spice's separate Legend breed-name typo is not fixed here.
- [#44 lingering audio](https://github.com/Ensrick/doomrocket-private/issues/44): sounds stopping at death. Absence in a short session does not disprove a rare fault.
- [#55 facing](https://github.com/Ensrick/doomrocket-private/issues/55): ordinary written observations. If it naturally happens with friends, retain available matching logs; no arranged lobby is required.

[#53](https://github.com/Ensrick/doomrocket-private/issues/53) has a separate,
optional [new-spawn controller rehearsal and passive probe](ANIMATION_AUTHORING.md#v0194-dev-runnable-native-controller-rehearsal).
It uses existing stock idle and does not establish final Blender-export or
localized outfit acceptance. The accepted #65 spawn fix needs no repeat gate.
Original clips, tracks, visible transitions and custom-pose ownership remain
preserved. Crunch's November 4 follow-up supplies the matching v0.1.97-dev log
for the accepted vaulting failure: `jump_up_5m` and `jump_down_land` are unsupported
by the visible outfit. v0.1.97-dev has no vaulting fix. The v0.1.98-dev traversal
candidate is published for its scoped written verdict; the optional idle
rehearsal does not establish traversal or custom-export acceptance.

Crunch heard the lower voice volume in v0.1.94-dev (#5). Further ordinary-play
loudness/cleanup observations remain useful; no new volume reduction is included
in v0.1.97-dev. The full sound pass remains blocked on artist take/trigger selection
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
