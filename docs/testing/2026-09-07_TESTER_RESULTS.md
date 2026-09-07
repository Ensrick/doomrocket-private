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

The combined package passed its own clean build and full release checks. The
September 5 package hashes are historical and must not be used for this
portrait update. Publication remains pending until Steam verifies the actual
new content, not merely a successful local build.

## Validated build, not yet published

Source commit `d714e888ed4e852d86701ea5aabd09983fc040b6` passed GitHub source
validation. The non-uploading release wrapper completed clean SDK compilation,
all five verified material splices, **150 Python package tests**, and the
PowerShell ragdoll regressions. The new compiled portrait check passes and
rejects the previous stale atlas. No reload behavior code was changed by the
portrait work. Native appearance and reload acceptance still need playtesting.

Package total: **95,349,849 bytes**. These hashes identify the ready-to-upload
September 7 package, not the old September 5 candidate:

| File in `bundleV2` | Bytes | SHA-256 |
| --- | ---: | --- |
| `209fb8c3c0a8c3a4.mod_bundle` | 1,021,841 | `B242782BC46EA2646616D9D25A51F87701C49B989537B347B6E1B7D0BED801EC` |
| `4e6a9317aab221e1.mod_bundle` | 7,258 | `5C7BF2F4DD484FFA20EA5971068037E1B5DB1B5EB25530DFE664209532FF1DA8` |
| `ac226cc769a897ae.mod_bundle` | 61,867,105 | `3205D2D321779633D10940DA1172AE79FD1F68918EE85BD9FC080C515E46D067` |
| `doomrocket.mod` | 470 | `DBF17C3E8ED109834BBCF56E4BDF7700BFF937E6B699FD63D7E11E571F3165D2` |
| `f5283f9585ea8355.mod_bundle` | 32,453,175 | `A3FA4DBBF3F7000E36C47EBFAE5F970B67B998958B8CE3A5FAA74463A2835F8F` |

The Steam process and stale recorded PID were unchanged from the failed
September 5 uploader session. The user was asked to normally exit/relaunch
Steam; another identical crash-prone upload was not attempted while that
state remained unchanged. Do not restart Steam or edit its registry without
the user's direction.

After the restart, verify these package hashes and use the upload-only VMB
command in `docs/RELEASE_CHANNELS.md`. Verify the live item title, public
visibility, warning, thumbnail, updated content handle, and exact byte count.
Only then record the publication commit, create the matching lightweight
v0.1.64-dev tag/prerelease, and tell Crunch to start the new test.
