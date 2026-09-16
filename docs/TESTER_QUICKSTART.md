# Development TEST quickstart

Current candidate: **v0.1.73-dev** diagnoses the invisible hose reported after
v0.1.72-dev resolved the spawn assertion. The visibility cause is still unknown.
Physics and the existing safety guards remain enabled and unchanged.
**Wait for explicit Workshop publication confirmation.**
[Candidate scope and acceptance](testing/2026-09-12_TEST_CANDIDATE.md).

Copy the block below into Discord when assigning a playtest.

```text
WARPROCKET BOMBARDIER TEST — QUICKSTART

Setup
[ ] Wait for confirmation that the assigned candidate was actually published.
[ ] Use the verified local deploy, or refresh the Workshop subscription; restart Vermintide 2.
[ ] Launch the Modded Realm.
[ ] Load Vermintide Mod Framework above Warprocket Bombardier.
[ ] Enable TEST item 3794172730 only; disable public item 3771657344.
[ ] Confirm [doomrocket:LOAD] v0.1.73-dev in the new console log on every peer.
[ ] If the version differs from the assigned build, stop and report the mismatch.
[ ] Record whether you are host, remote client, or solo.

Test
[ ] Diagnostic priority: spawn one Engineer, observe for at least ten seconds,
    move/turn around him, then kill him. Attach the full log even if the hose
    stays invisible. It should now identify the blocked stage or completed writes.
[ ] Spawn a loaded Engineer repeatedly: no animation-blender assertion or Lua error.
[ ] Hose: inspect both ends while idle, turning, aiming, firing, reloading and stowed.
    It should keep its general shape and wiggle, not become a loose hanging rope.
[ ] Death/drop: kill both a loaded and an unloaded Engineer; hose should disappear.
    Body ragdoll and loaded launcher/warhead must remain stable.
[ ] Kick/reposition: repeat close-range shoves, then let him relocate and resume fire.
    No crash, duplicated reload, or point-blank rocket.
[ ] Aim: after reloading, he should track/aim for at least one second before firing.
[ ] Smoke: one plume from the actual chimney, following motion and stopping on death.
[ ] Repeat with a remote client, a late join, several Engineers and a map transition.
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

Known limits: at most eight nearby hoses within 40 m are shown/simulated.
There is no hose collision with walls, bodies or itself; it may clip. No flame
has been added to the under-barrel crystal (#15).

Logs and issue attachments are public. Review them before uploading. A passing
source test or clean-looking log does not substitute for visible in-game results.

Maintainer readback: `py -3 tools/analyze_hose_log.py <log> --expected-version 0.1.73-dev`.
The analyzer reports controller evidence; completed pose writes alone do not
prove visible rendering. Retain the log and Crunch's visual observation together.
