# September 5 tester results

All three new captures load `v0.1.63-dev` and run as host. Crunch's observations
and the matching logs confirm the previous fixes on that peer. No remote-client
gameplay capture was supplied; the startup `peer=client` impact configuration
message precedes hosting and does not establish multiplayer coverage.

| Issue | Reporter observation and log evidence | Acceptance scope |
| --- | --- | --- |
| [#9 career switching](https://github.com/Ensrick/doomrocket-private/issues/9#issuecomment-5549946502) | Initial player selection followed by 38 career changes; 42 ordered attack notification starts and 42 matching ends; two ends correctly handle destroyed victims; no orphan repairs | Host reproduction passes; remote-client validation remains |
| [#10 combat speech after death](https://github.com/Ensrick/doomrocket-private/issues/10#issuecomment-5549995256) | 16 active barks stopped, each followed within two log lines by successful death playback; variants 01–05 covered; 20 death events with nonzero playing IDs | Host audio behavior passes; remote-client validation remains |
| [#11 repeat shoves and close-range firing](https://github.com/Ensrick/doomrocket-private/issues/11#issuecomment-5550076986) | 35 consecutive successful shoves over about 4m19s with no launch audio during that sequence; 34 close-range launch rejections and one abort; ranged fire resumes afterward | Host repetition and launch exclusion pass; new reload problem tracked in #12 |

## Source captures and locations

- [Career-switch log](https://github.com/user-attachments/files/31859024/console-2026-09-05-06.11.33-2b7d59c1-7be3-4820-8a01-db4957a35134.log): load banner at line 1164; deleted-victim cleanup at 4018 and 7673. The notification balance never exceeds one active victim and is zero at shutdown. There are also 28 safe `no_live_target` rejections.
- [Voice log](https://github.com/user-attachments/files/31859108/console-2026-09-05-06.23.38-f89c5e85-9a32-4296-9e15-bd96e6942842.log): banner at 1157; examples of stop then death playback at 3306/3308, 3358/3360 and 3872/3873. Two additional death-time barks had already finished.
- [Shove log](https://github.com/user-attachments/files/31859280/console-2026-09-05-06.33.13-05ce4c22-17a8-4652-8ffa-9d2534ed5eb2.log): banner at 1151; successful sequence from 06:34:36.419 to 06:38:54.327; launch resumes at line 3077, 06:38:59.914. One earlier shove was interrupted by death before its impact timer, explaining 36 starts versus 35 impacts.

All three sessions shut down normally. None contains the previous fatal
assertion, native access violation, script crash or stale-vector signature.
Unrelated mods report startup or unload hook errors; the captures are not
universally free of error messages.

## Remaining reload defect

[Issue #12](https://github.com/Ensrick/doomrocket-private/issues/12) separates
Crunch's new visual report from the successful shove regression. Interrupting
the ranged sequence restarts it from its first child; the reload action used
to start its animation and 3–5 second timer even when a completed load remained.

The v0.1.64 candidate preserves completed ammunition on the unit blackboard.
The loaded mesh and its peer notification become active together at reload
completion, rather than exposing the mesh during the final second of an
unfinished reload. Shoves may already interrupt reload or aim through the
existing selector. An unfinished reload still restarts, and a completed one
survives the interruption. Only an actual shot consumes the load.

A loaded enemy waits inside the shove envelope while the kick cools down.
This also avoids retrying the ranged sequence every AI update after removing
the unwanted reload delay. The higher-priority shove remains available, and
leaving the close-range envelope returns the enemy to its ranged sequence.

The cooldown, knockback force and aiming timing retain their current values.
Crunch's suggestions for stronger knockback and relocation remain recorded in
#12 for a deliberate balance follow-up.

## Executable regression evidence

`tools/tests/test_doomrocket_reload_lifecycle.py` executes the production Lua
actions and selector predicates in Lua 5.1 with stubbed engine I/O. All nine
tests pass, covering loaded and partial reload interruptions, initial aiming,
successful versus rejected shots, callback freshness, lost targets, and the
close-range waiting branch. The completed-reload/shove test fails when only
the reload implementation is replaced in memory with the v0.1.63 source, and
passes with v0.1.64. This establishes a regression test for the reported defect;
it does not simulate the game's animation graph, physics, or peer rendering.

## Explosion and wider acceptance limits

These sessions contain 62 launch audio records and 63 impact dispatch records,
with no recurrence of the fatal signatures from #7/#8. The extra impact in the
voice test follows an enemy death and precedes a separate-position airborne
impact. This is consistent with separate death-warhead and projectile routes;
it does not independently prove duplication.

The dispatch telemetry lacks projectile identifiers, and these reports do not
visually certify the complete impact matrix. Keep #7/#8 open until ground and
player impacts, shot-down rockets, attacker death, projectile removal, repeated
rocket stress and host/client replication are explicitly verified. Do not infer
one explosion or damage event per rocket from the aggregate counts.
