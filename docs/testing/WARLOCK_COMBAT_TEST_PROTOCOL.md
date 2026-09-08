# Warprocket Bombardier combat regression protocol

This protocol protects the v0.1.56 survivability and close-range shove
contracts. Run the offline gate before every deploy, then complete the short
host/client matrix in-game. A source-only test cannot prove the live damage
pipeline, animation callbacks, or networked player status transition.

## Offline gate

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Test-WarlockPipeline.ps1
```

The combat contract suite verifies all of the following:

- the Bombardier retains the native Ratling carrier and its physics-coupled
  hit zones;
- maximum health is cloned from the live Stormvermin breed table rather than
  copied as a second set of numeric constants;
- the general armor category is explicitly inherited from Stormvermin, with
  no per-hit-zone or primary-armor override;
- the close shove is the first branch inside the existing attack-pattern root,
  ahead of the ranged sequence, while the hand-written generated selector
  retains its matching root-child layout;
- the shove evaluates the native Stormvermin spline boundaries directly rather
  than depending on the `BTUtilityNode` used by the Stormvermin tree but absent
  from the Ratling-derived Doomrocket tree;
- shove impact can occur only once, uses the same zero-damage push semantics
  as Stormvermin, and cleans up correctly when completed or interrupted;
- the shove uses an event already supported by both the carrier and custom
  visual path. It must not use `attack_push` or the callback-driven vanilla
  `BTStormVerminPushAction`, because the Ratling carrier has no compatible
  Stormvermin push clip/callback contract.

## Health baseline

For the current game patch, the Stormvermin health table resolves as follows.
These numbers are an observation for manual verification; runtime code derives
from `Breeds.skaven_storm_vermin.max_health` so a future game rebalance remains
in parity automatically.

| Difficulty | Expected maximum health |
| --- | ---: |
| Recruit | 16 |
| Veteran | 24 |
| Champion | 35.25 |
| Legend | 52.75 |
| Cataclysm 1 | 86.5 |
| Cataclysm 2 | 102.5 |
| Cataclysm 3 | 118.5 |

The underlying game table contains two initial 16-health steps before the
Veteran step, plus a versus step of 24. Do not shift the difficulty indexes
when checking the live health extension.

## In-game survivability check

Use an unmodded official difficulty profile and disable balance mods that
replace breed health or armor. On the host, spawn one Stormvermin and one
Warprocket Bombardier. For each relevant difficulty:

1. Read or damage-probe both maximum-health values. They must be identical.
2. Strike both in the torso with the same non-armor-piercing attack at the same
   power level and without crit/headshot/proc buffs.
3. Confirm both use armor category 2 and produce the same armored damage result.
4. Repeat one headshot to ensure the retained Ratling hit-zone carrier still
   resolves the head correctly.

Record the exact weapon, power, difficulty, displayed damage, and whether the
hit was a crit. A statement such as “felt unarmored” is not sufficient evidence
because the Ratling donor already used armor category 2 before this change.

## Close-range shove check

Test on open, level ground with one Bombardier and no other enemies:

1. Stay beyond 1.8 metres for at least ten seconds. The Bombardier must not
   shove and must continue its ranged behavior.
2. Approach inside 1.8 metres while upright and moving away at less than
   1.5 m/s. These are the native utility spline boundaries and are evaluated as
   strict thresholds. The log must contain `phase=shove_selected` followed by
   `phase=shove_begin`; their absence means the action was not selected.
3. Confirm the existing `attack_shoot_align` visual starts, impact occurs once
   between 0.6 and 0.8 seconds, and the action ends between 1.2 and 1.5 seconds.
4. Confirm the shove deals zero health damage, applies the `sv_push` response,
   and pushes forward at speed 7 with a cap of 8.
5. Remain in range. The inherited shove cooldown keeps it unavailable for
   7.5 seconds; v0.1.64 host captures show repeated selections just after that
   boundary. During that cooldown it may reposition, but it must not
   launch a rocket while the target remains inside 1.8 metres. The log should
   show `reason=target_too_close`; after the cooldown it must shove again if the
   target remains eligible.
6. Repeat while stepping behind the Bombardier before impact. No push should be
   applied because impact revalidates range and facing.
7. Repeat while dodging out of range, becoming downed, and killing/staggering
   the Bombardier during wind-up. Each interruption must leave navigation and
   attack-token state usable; there must be no stuck action or repeated impact.
8. Repeat once with a remote client as the target. The server remains the shove
   authority, while the client must observe the same networked pushed status.

## Reload interruption and resumption (#12)

Verify the announced build's load marker (v0.1.65-dev for the reposition
candidate) and use one Bombardier on open ground.

1. On a fresh spawn, interrupt its first aim with a shove. Step away and confirm
   it resumes aiming with the original loaded rocket, without a reload cycle.
2. Let it fire and complete a reload. Approach for a shove and remain close for
   at least two cooldowns. Each shove must retain the loaded rocket; no reload
   animation or repeated reload visibility update should occur between kicks.
3. Step back outside 1.8 m. It must aim and fire that retained rocket, then
   perform one genuine reload before the next shot.
4. Separately interrupt a reload early and during its final second. An
   unfinished load must restart after the shove and cannot fire immediately.
   The rocket appears and is synced to peers only when reloading completes.
5. Repeat with stagger, death, and a career switch during reload. No stale
   callback, deleted target access, free shot, or stuck navigation may result.
6. Repeat as a remote client while the host runs AI. Compare the visible
   loaded/empty weapon on both peers and attach both complete logs.

The selector can interrupt both reload and aiming; no new aim-only restriction
or stronger knockback is part of this fix. The existing shove cooldown and
force remain the baseline for any later balance changes.

## Reposition after a shove

The September 8 follow-up, [issue #13](https://github.com/Ensrick/doomrocket-private/issues/13), targets the idle period between kicks by moving
the Engineer to create space. It must preserve the 7.5-second shove cooldown;
reducing the cooldown or increasing shove force is not the selected change.
This section defines acceptance for the candidate, not a publication or
runtime-pass claim. Record the exact announced candidate version from its
`[doomrocket:LOAD]` banner; v0.1.64 is the baseline, not evidence that the new
movement is present. See the [audited baseline](2026-09-08_TESTER_RESULTS.md).

Use one Bombardier, record video alongside the complete console log, and run
these cases on host and with a remote client as the target:

1. **Open ground:** finish a reload, approach for a successful shove, and watch
   the follow-up movement. It should create navigable space rather than stand
   idle through the cooldown. Once there is enough separation, it should
   resume aiming and fire the retained rocket without an extra reload.
2. **Persistent close target:** follow the Engineer during its movement and
   stay inside 1.8 m. It must not fire into the player at point-blank range,
   shorten the 7.5-second kick cooldown, or apply another impact from the same
   shove. A later eligible shove must still work after the cooldown.
3. **Walls and corners:** place a wall behind it, then repeat near a corner,
   ledge, and narrow doorway. It must use a reachable route without passing
   through geometry, walking off a ledge, teleporting, or getting permanently
   stuck. If one direction is blocked, any chosen alternative must remain
   reachable and preserve the launch-distance guard.
4. **No navigable escape:** surround it with blocking geometry or use a
   position with no reachable retreat route. Failing to find space must end
   or bound the attempt cleanly. It must remain able to shove when eligible
   and resume ranged behavior once the player provides space; there must be
   no endless movement action, path-request loop, or point-blank fallback shot.
5. **Moving target:** move sideways, cross behind it, pursue it, and then
   retreat while it is repositioning. It must respond to current target
   positions without oscillating forever, following a stale target, or firing
   based only on the separation that existed when movement began.
6. **Loaded rocket retention:** stay close for several shove/movement cycles
   after a completed reload. There must be no new reload animation, duplicate
   reload visibility update, lost rocket, or free extra shot. After one real
   shot, a genuine reload must again be required.
7. **Unfinished reload:** interrupt reloading early and during its final
   second with a shove. Repositioning must not mark that unfinished load as
   complete or allow immediate firing. It must subsequently finish a real
   reload before shooting. Also interrupt the first aim after a fresh spawn:
   preserving that original loaded rocket must still work.
8. **Interruptions and target loss:** stagger or kill the Engineer during
   movement; separately down, remove, or career-switch its target. Movement
   and attack state must clean up without a stuck navigation override,
   post-death movement, deleted-unit access, or unpaired bot-attack
   notification. Recovery and later attacks must remain possible when alive.
9. **Host/client agreement:** compare movement, loaded/empty weapon state,
   kick timing and push response, and rocket firing on both peers. Only the
   host should decide the action. Capture both complete logs with matching
   version banners and label which view each recording shows.

Record blocked-route outcomes as well as successful retreats. Preserve the
existing armor/health, ragdoll, death-audio, career-switch, and explosion
regressions; this movement test does not replace their acceptance checks.

## Career-switch notification regression

Issue #9 reproduced after repeated Keep career changes because destruction of
the old player unit caused the launch action to skip its paired bot-group
`ranged_attack_ended` call. The next launch then asserted that the same
Bombardier was attacking two victims.

1. Spawn one Bombardier, let it begin aiming, and switch career before it fires.
2. Repeat at least ten times with the same living Bombardier, including switches
   during align, ready, firing, and reload states.
3. Repeat with one dead and one living Bombardier present.
4. Require a matching `status=ended` record for every
   `phase=bot_attack_notification status=started` record. An ended record may
   legitimately say `target_alive=false` after the switch.
5. Fail on `already attacking another victim`, any assertion, or a permanently
   stuck bot-threat state. A `status=repaired_stale` record is acceptable once
   after a development hot reload, but not during an ordinary fresh-game run.

## Pass criteria

- Bombardier and Stormvermin maximum health match at every tested difficulty.
- Torso armor behavior matches Stormvermin and the head hit zone remains valid.
- Every eligible close approach yields at most one zero-damage shove.
- Cooldown, facing, range, downed-target, and interruption gates all work.
- The Bombardier never fires inside the 1.8-metre shove envelope and resumes
  ranged behavior only after the target leaves it.
- Repeated career switches leave every bot attack notification paired.
- Host and client logs contain no script error, assertion, missing animation
  event, stuck behavior node, or repeated shove impact for one action.
