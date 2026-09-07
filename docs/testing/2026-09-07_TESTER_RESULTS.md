# September 7 portrait and reload status

## Latest issue #12 capture

[Crunch's comment](https://github.com/Ensrick/doomrocket-private/issues/12#issuecomment-5565397001)
reports that the Engineer still reloads twice. The attached
[console log](https://github.com/user-attachments/files/31897280/console-2026-09-07-05.08.13-d1ce76d7-9edd-48d0-9e0e-225a35ff2f3b.log)
loads **v0.1.63-dev at line 1160**, not the pending v0.1.64 fix. Steam still
reported v0.1.63 when this report was triaged. The September 5 upload had
failed before publication, so this is not evidence that the new fix failed.

- Host role at line 2356; no remote-client gameplay capture.
- 21 shove starts and 21 applied impacts, with 19 close-range launch
  rejections and one in-progress abort.
- Three paired attack notification starts/ends; two launch and two impact
  audio records.
- Normal shutdown at line 3244; no previous fatal/assertion/stale-vector
  signatures. No v0.1.64 reload lifecycle telemetry is present.

The report continues to support the known #12 defect in v0.1.63. Keep #12 open
for the first matching-version test of the fix. It adds host shove coverage,
not new multiplayer or death-audio acceptance. No additional behavior patch
is justified by this old-version capture alone.

## Combined candidate

Keep **v0.1.64-dev** because it has not been published or tagged. Add the
provided 60x70 portrait to that pending reload fix; the behavior code is
unchanged from the reviewed implementation. See the
[portrait pipeline](../WARLOCK_PORTRAIT_PIPELINE.md) for source provenance,
asset wiring, and visible acceptance steps.

The combined package needs its own clean build and full release checks; the
September 5 package hashes are historical and must not be used for this
portrait update. Publication remains pending until Steam verifies the actual
new content, not merely a successful local build.
