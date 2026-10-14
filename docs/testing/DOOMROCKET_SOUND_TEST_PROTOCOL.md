# Doomrocket sound test protocol

This is the acceptance gate for the custom Doomrocket sound bank. The candidate
contains twelve approved assets: the living Bombardier's backpack loop, the
launcher shot, a ground-body plus air-crack pair played together for every
rocket detonation, six combat-voice variants (five spoken barks and one laugh),
and two death takes. Passing offline checks proves the bank is present and wired;
it does not prove spatialisation, occlusion, replication, variation, or cleanup
inside Vermintide 2.

Published TEST v0.1.90-dev includes the requested 30% amplitude reduction from
v0.1.88-dev. For a new loudness or cleanup observation, confirm
`[doomrocket:LOAD] v0.1.90-dev` and give a written verdict from normal play.
Publication does not establish perceived loudness or complete the full cue pass.

Arnaud supplied two experimental `TargetLocked` aiming WAVs on October 9. Both
are valid markerless mono 16-bit PCM at 44.1 kHz: the first is 3.139 s, the `_02`
take is 3.202 s. They await his choice and intended trigger (target acquisition
or pre-fire/wind-up); neither activates in the shipping bank. The `_02` SHA-256
is `3f03f3453ba9819d18483fdce3e3afaf38775687a4e6d7742961666a66728af9`.
Rocket flight-loop and insertion/latch sources are still absent. None of the
twelve active masters provides those cues; the shot transient must not be
repurposed as an infinite flight loop. Issue #5 remains open for that work.
The combat pool currently begins at the replicated
projectile-launch boundary and is limited to one bark per five seconds for each
Bombardier, preventing a three-rocket volley from stacking three lines. The
recordings are temporary pending a better capture environment. Any inherited
Ratling death vocal or Warpfire projectile hiss is a regression. The native
Warpfire-backpack explosion is the deliberate crash-safe impact fallback while
the custom bank is unavailable; it is acceptable only when the log also says
`phase=impact_config status=fallback`.

## v0.1.59 runtime failure through the v0.1.62 registration candidate

Two complete tester logs from 2026-09-01 established the actual failure rather
than relying on offline inference:

- `v0.1.59-dev` loaded `wwise/doomrocket`, but `Wwise.has_event` returned false
  for every attempted custom event: backpack, launch, impact, combat voice, and
  death voice. The inherited Globadier/Ratling-family death sound was the only
  audible result.
- Both rocket impacts crashed inside `wwise_pluginw64_release`. The Lua stack
  was `WwiseWorld.make_auto_source` -> `WwiseUtils.make_position_auto_source`
  -> `DamageUtils.create_explosion` -> `ProjectileRocket.rocket_explode`, with
  `wwise_world=nil`.
- The cause was a direct mod call to `DamageUtils.create_explosion` using
  `Unit.world(projectile)`. That Stingray world handle was not registered with
  `Managers.world`, so the audio branch could not resolve a Wwise world.

`v0.1.61-dev` extended the v0.1.60 containment independently of custom-audio success:

1. Loaded-warhead death explosions call the game-owned
   `AreaDamageSystem:create_explosion` from the engine's death phase. Projectile
   impacts detected in VMF's `mod.update` instead send exactly one native
   `rpc_create_explosion` request to the server; its handler performs the
   authoritative explosion in the safe network phase and owns client
   replication.
2. The explosion template used the custom impact event only when
   `Wwise.has_event` confirmed it registered; otherwise every peer selected the
   known native Warpfire impact event.
3. Every direct custom unit-audio path resolves and validates
   `Managers.world:world("level_world")` and its Wwise world before calling
   `WwiseUtils`. A missing world fails silent with telemetry rather than
   crossing into the native plugin with nil.
4. The package includes the Wwise 2018.1 `Init` bank omitted by v0.1.59.
   Its SHA-256 is pinned and it is byte-identical to the Init product shipped
   by two independent, working VT2 custom-audio mods. This is a sound-fix
   candidate, not proof: only a new game log showing `status=played` proves the
   Doomrocket events registered.

Issue #10's v0.1.61 log then showed that every custom event was deliberately
skipped after the bank loaded because `Wwise.has_event` stayed false. No native
bank-load error appeared. This proved the runtime was never attempting the
bank's HIRC events, so silence was not evidence that the bank rejected them.

`v0.1.62-dev` addresses both remaining registration variables:

1. Both Wwise dependencies now reference the unique
   `wwise/doomrocket_project` metadata resource. The old generic
   `wwise/project` name was shared with the base game and other custom-audio
   mods, creating an avoidable resource-collision risk.
2. HIRC attenuation and Sound objects are followed by Action/Event groups in
   the exact ordering observed in independently working VT2 Wwise 2018 banks.
3. A loadable, successfully loaded bank is allowed to dispatch its event even
   when the metadata-only `Wwise.has_event` query is stale. The query remains
   diagnostic; it is no longer a mute switch. A missing bank or audio runtime
   still selects the native impact fallback.
4. Unit event telemetry reports `status=played` only for a non-zero Wwise
   playing ID. `status=trigger_rejected` is a real runtime failure and must be
   included in the report.

### Issue #8: repeated explosion containment

Crunch's issue #8 log exposed a second, independent failure in the projectile
lifecycle. The same moving rocket requested 113 impact sounds and produced 111
`DamageUtils.create_explosion` errors over roughly eight seconds. The engine
exception reported `unit_position = [Stale Vector3]`: projectile collision was
being evaluated from VMF's `mod.update`, not an engine damage-system phase in
which `POSITION_LOOKUP` is safe to consume. It escaped
`AreaDamageSystem:create_explosion` before the old function reached either
`mark_for_deletion` or `self.exploded = true`, so the next frame treated the
same physics object as a fresh impact.

The required ordering is now an explicit contract:

1. Reject non-authoritative or already-terminal calls.
2. Set `self.exploded = true` so every later update or callback is a no-op.
3. Snapshot the live actor's final position and rotation.
4. Queue the projectile unit for deletion, retaining its `mod.projectiles`
   entry until the existing deletion hook calls `destroy` to clean up its
   particle and actor.
5. Only then emit impact telemetry and one server-directed native explosion
   RPC. The projectile must never call `AreaDamageSystem` directly or send a
   client explosion RPC.

This makes explosion a one-way, idempotent transition even if an engine/audio
callback raises or synchronously re-enters the extension. `destroy` preserves
the terminal flag rather than re-arming a retained Lua object.

## Reproducible bank build

The VT2 SDK does not include the historical Wwise 2018.1 authoring application
or Fatshark's Wwise exporter. The deliberately small bank is therefore built
from documented version-132 structures by
`tools/build_doomrocket_wwise_bank.py`; the main bank does not copy donor media
or donor HIRC objects. The builder also emits the pinned, standard Wwise 2018.1
Init product described above. The twelve hash-pinned masters under
`audio_src/doomrocket/` are the source of truth, never whichever similarly
named files remain in Downloads.

Rebuild from the repository root with:

```powershell
py -3 tools/build_doomrocket_wwise_bank.py `
  --source-dir audio_src/doomrocket `
  --repo-root .
```

This rewrites the main bank, the Wwise `Init` prerequisite, their four
Stingray metadata/dependency products, and
`wwise/doomrocket.bank_manifest.json`. For the current approved masters, the
wrapped bank SHA-256 is
`7f7fded74e853f8fee6227b9291e6e4eae31123c527e341d61f12a59367258af`.
Published TEST v0.1.90-dev retains the packaging change prepared for the
unpublished v0.1.89-dev: signed 16-bit PCM is scaled by 4949/10000
(approximately -6.11 dB from the masters). This is 70% of v0.1.88-dev's
707/1000 amplitude, about 3.10 dB additional attenuation for the requested 30%
reduction. Use the current published LOAD banner for in-game observations. The
approved masters and their source hashes remain unchanged; sample counts,
event timing and the spatial attenuation curves are preserved. The manifest
records both master and reduced-playback PCM hashes.
The offline gate below performs a clean-room rebuild in a temporary directory
and requires every generated byte to match. If Crunch supplies a replacement
asset, update the approved source hash and expected bank evidence deliberately;
do not bypass this comparison.

## Offline gate

From the repository root, run:

```powershell
py -3 tools/tests/test_doomrocket_sound_contract.py
py -3 tools/tests/test_doomrocket_audio_lifecycle.py
py -3 tools/tests/test_doomrocket_projectile_lifecycle.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-WarlockPipeline.ps1
git diff --check
```

The focused test rejects a candidate unless:

- the package actively includes `wwise/*`;
- the main and Init banks, both dependency descriptions, bank metadata, and
  project metadata all
  exist, use VT2's observed Wwise 2018.1/version-132 bank format, and expose
  the same twelve `Play/Stop_enemy_doomrocket_*` events;
- the runtime loads `wwise/doomrocket`;
- launch, backpack, combat-voice, and death-voice paths no longer call borrowed
  Warpfire or Ratling death events; the replicated impact alone has one
  explicitly gated native fallback;
- one authority-selected combat variant is carried through the existing launch
  RPC and played at the Bombardier's head on every peer, with a per-enemy
  cooldown and no immediate repeat;
- both unit and husk death reactions select one custom death take, suppress
  hot-join playback, and explicitly disable the inherited Ratling death event;
- a projectile sends exactly one server-directed native `rpc_create_explosion`
  request, with no direct `AreaDamageSystem`/`DamageUtils` call and no client
  RPC; the loaded-warhead death path deliberately retains exactly one direct
  authoritative `AreaDamageSystem` call from its safe engine phase;
- a projectile claims its terminal flag and queues deletion before any
  fallible impact callback; repeated or re-entrant calls are no-ops, the
  deletion hook can still find it for cleanup, and `destroy` cannot clear the
  terminal flag;
- no custom-audio helper passes `Unit.world(...)` into `WwiseUtils`; the
  managed level world and its Wwise world must both exist first;
- the backpack retains its exact playing ID and every mod/level teardown
  reaches an idempotent audio cleanup path;
- when source WAVs are retained under `audio_src/doomrocket/` or `wwise/`,
  they are the twelve approved mono 44.1 kHz/16-bit files, contain no `smpl` chunks,
  and match the recorded handoff hashes.
- when `bundleV2` exists, it contains exactly one compiled main bank, Init
  bank, matching dependency for each, and project-metadata resource; both
  compiled banks' raw bytes must equal their authored products exactly, and
  the compiled event metadata must retain the backpack's `Infinite` flag and
  all eleven one-shot flags.

### Bank-version evidence

The version gate comes from two independent artifacts; it is not a successful
parser guess. The current VT2 SDK `bin/plugins/wwise_pluginw64_dev.dll`
(SHA-256
`4A1EB054BC5E631EE75302F2CA61636F4BF4FC8648585722BF701BEAEA78DC08`)
contains the little-endian XOR word `0x9211BCAC` at file offsets `0x15026` and
`0x1510F`. The native Ratling bank and the proven Pusfume and Loremasters'
Armoury custom banks all store `0x9211BC28` in the first BKHD generator field.
The recovered generator version is therefore:

```text
0x9211BC28 XOR 0x9211BCAC = 0x00000084 = 132
```

The test independently requires the proven stored word and this XOR result.
Merely forcing a third-party parser to interpret the bank as version 132 or
134 is not accepted as evidence.

## Publication gate

Use the canonical VMB release adapter documented in [RELEASE_CHANNELS.md](../RELEASE_CHANNELS.md).
It owns the clean build, required material splice, validation, reviewed build
receipt and verified TEST upload. A source change or successful local test is
not evidence that a Workshop candidate is published. Restart after its update
and verify the exact new `[doomrocket:LOAD]` banner before giving a verdict.

## October 10 candidate: lingering sound after death (#44)

Crunch's October 9 v0.1.84-dev Fort report is accepted: non-death sounds remained
after enemies died three times, audible to everyone present. The server log
shows loop stop-event posts and voice cleanup, but the old `status=complete`
message did not verify that the original loop had ended. It also printed a
unit-resource identity shared by all Engineer instances.

The candidate stops backpack, active combat bark and launcher-shot playing IDs
before death/inventory teardown. Death voices and independent projectile impacts
retain their own lifetimes. The frame fallback checks the native health
extension, since a retained corpse still satisfies `Unit.alive`. Retired owners
reject late spawn/launch callbacks. World release stops owned audio before the
native release and forgets retained IDs before they can become stale.

Stop requests remain tracked until a later `WwiseWorld.is_playing` query confirms
silence, with retries if needed. The API is used by vanilla's `dialogue_system`
and `corruptor_beam_extension`; its actual audible result still needs the
published candidate's in-game verdict. Unique local `owner_id` and `playing_id`
values now allow pairing individual starts and stops.

- `status=stop_requested method=playing_id`: request sent; silence is not yet confirmed.
- `status=stopped`: a later query observed that playing ID ended.
- `status=still_playing`: retries exceeded the first second; a real unresolved cleanup failure.
- `status=world_gone`: native world is no longer registered; its stale handle was not queried.

## Solo acceptance steps

A solo test is sufficient. Accept written observations and use the matching
console log for diagnosis. No recording, second player, remote-client session,
or extra player coordination is required. Reports from ordinary play with
friends are useful when they arise naturally, without creating another gate.

1. In a quiet area, approach one living Engineer from about 30 m, 15 m and 5 m,
   then circle him and briefly place a solid wall between him and the listener.
   Report whether backpack, voice, launch and impact volume now fits nearby
   native enemies and whether sound follows its source with plausible attenuation.
2. Let him fire three times. Require one launch per rocket and at most one
   combat bark per Engineer every five seconds. Ground and shot-down detonations
   should each produce one impact, with both custom explosion layers.
3. Kill an Engineer while idle, during aim, immediately after launch and while
   speaking. Living machinery and speech must stop; exactly one death take may
   finish. An already airborne rocket must still detonate normally. Logs should
   pair `backpack_start` / `backpack_stop` by playing ID and show confirmed
   `status=stopped` for any sounds still playing at death.
4. Spawn/kill several Engineers and continue ordinary play, including Fort when
   convenient. After their deaths, no loop should remain at a corpse or spawn
   point. State explicitly whether the rare lingering sound recurs, and retain
   the complete log; a clean short test does not establish rare-bug acceptance.
5. Leave and re-enter a level, then repeat one spawn/fire/kill cycle. Require no
   stale playing-ID/native-world error and working audio on the new Engineer.

Report the exact loaded banner, what was heard, any persistent sound's rough
location/time, and whether volume still needs adjustment. Existing written
observations are evidence; logs supplement them instead of overruling them.

Full sound-pass acceptance (#5) remains blocked by the aiming take/trigger
decision and absent flight/reload assets. Cleanup and volume feedback on
published TEST v0.1.90-dev are independent actionable checks, not a claim that
the full pass is finished.
