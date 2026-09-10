# Development TEST quickstart

September 10 hold: v0.1.66-dev chimney smoke is an **unpublished source
candidate**. TEST still serves v0.1.65-dev, which has the confirmed relocation
crash [#14](https://github.com/Ensrick/doomrocket-private/issues/14). Do not
assign a smoke or relocation playtest until a corrected TEST build is explicitly
published. The future smoke matrix is in
[backpack research](research/BACKPACK_HOSE_AND_SMOKE.md#runtime-smoke-acceptance).

Copy the block below into Discord when assigning a playtest.

```text
WARPROCKET BOMBARDIER TEST — QUICKSTART

Setup
[ ] Wait for confirmation that the assigned candidate was actually published.
[ ] Fully restart Steam and Vermintide after the Workshop update.
[ ] Launch the Modded Realm.
[ ] Load Vermintide Mod Framework above Warprocket Bombardier.
[ ] Enable TEST item 3794172730 only; disable public item 3771657344.
[ ] Confirm the exact [doomrocket:LOAD] banner in the new console log.
[ ] If the version differs from the assigned build, stop and report the mismatch.
[ ] Record whether you are host, remote client, or solo.

Test
[ ] Follow the steps in the assigned GitHub issue exactly.
[ ] Say what you visibly saw/heard and whether it happened every time.
[ ] For rockets, count explosions and confirm the physical rocket disappears.
[ ] For multiplayer, collect logs from both host and remote client when possible.

Evidence
[ ] Attach the complete matching file from:
    %APPDATA%\Fatshark\Vermintide 2\console_logs\
[ ] For a crash, include the GUID and Crashify link.
[ ] Add a continuous video for visual/physics/audio timing problems if practical.
[ ] Report at: https://github.com/Ensrick/doomrocket-private/issues/new/choose
```

Logs and issue attachments are public. Review them before uploading. A passing
source test or clean-looking log does not substitute for visible in-game results.
