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
2. Approach inside approximately 1.8 metres while visible, upright, and moving
   away at less than approximately 1.5 m/s. The native utility splines reach
   zero at the exact boundary values, so treat them as strict thresholds.
3. Confirm the existing `attack_shoot_align` visual starts, impact occurs once
   between 0.6 and 0.8 seconds, and the action ends between 1.2 and 1.5 seconds.
4. Confirm the shove deals zero health damage, applies the `sv_push` response,
   and pushes forward at speed 7 with a cap of 8.
5. Remain in range. Native Stormvermin utility keeps the shove unavailable for
   7.5 seconds and ramps it in just after that (roughly an eight-second minimum
   observed interval). It must resume navigation/ranged behavior after the
   action ends.
6. Repeat while stepping behind the Bombardier before impact. No push should be
   applied because impact revalidates range and facing.
7. Repeat while dodging out of range, becoming downed, and killing/staggering
   the Bombardier during wind-up. Each interruption must leave navigation and
   attack-token state usable; there must be no stuck action or repeated impact.
8. Repeat once with a remote client as the target. The server remains the shove
   authority, while the client must observe the same networked pushed status.

## Pass criteria

- Bombardier and Stormvermin maximum health match at every tested difficulty.
- Torso armor behavior matches Stormvermin and the head hit zone remains valid.
- Every eligible close approach yields at most one zero-damage shove.
- Cooldown, facing, range, downed-target, and interruption gates all work.
- The Bombardier returns to its ranged behavior after the shove.
- Host and client logs contain no script error, assertion, missing animation
  event, stuck behavior node, or repeated shove impact for one action.
