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

## Combined build

The combined build retained **v0.1.64-dev** because the earlier candidate had
not been published or tagged. It adds the provided 60x70 portrait to the
pending reload fix; the behavior code is
unchanged from the reviewed implementation. See the
[portrait pipeline](../WARLOCK_PORTRAIT_PIPELINE.md) for source provenance,
asset wiring, and visible acceptance steps.

The combined package passed its own clean build and full release checks. The
September 5 package hashes are historical and must not be used for this
portrait update. Publication was subsequently verified as recorded below.

## Validated build

Source commit `d714e888ed4e852d86701ea5aabd09983fc040b6` passed GitHub source
validation. The non-uploading release wrapper completed clean SDK compilation,
all five verified material splices, **150 Python package tests**, and the
PowerShell ragdoll regressions. The new compiled portrait check passes and
rejects the previous stale atlas. No reload behavior code was changed by the
portrait work. Native appearance and reload acceptance still need playtesting.

Package total: **95,349,849 bytes**. These hashes identify the published
September 7 package, not the old September 5 candidate:

| File in `bundleV2` | Bytes | SHA-256 |
| --- | ---: | --- |
| `209fb8c3c0a8c3a4.mod_bundle` | 1,021,841 | `B242782BC46EA2646616D9D25A51F87701C49B989537B347B6E1B7D0BED801EC` |
| `4e6a9317aab221e1.mod_bundle` | 7,258 | `5C7BF2F4DD484FFA20EA5971068037E1B5DB1B5EB25530DFE664209532FF1DA8` |
| `ac226cc769a897ae.mod_bundle` | 61,867,105 | `3205D2D321779633D10940DA1172AE79FD1F68918EE85BD9FC080C515E46D067` |
| `doomrocket.mod` | 470 | `DBF17C3E8ED109834BBCF56E4BDF7700BFF937E6B699FD63D7E11E571F3165D2` |
| `f5283f9585ea8355.mod_bundle` | 32,453,175 | `A3FA4DBBF3F7000E36C47EBFAE5F970B67B998958B8CE3A5FAA74463A2835F8F` |

At the end of the portrait build, the Steam process and stale recorded PID
were unchanged from the failed September 5 uploader session. The user was
asked to normally exit/relaunch Steam; no upload was attempted during that
build turn. Do not restart Steam or edit its registry without the user's
direction.

At the user's subsequent request, an upload-only retry on September 7 at
12:08 CDT again exited with `0xc0000005` at `ugc_tool.exe` offset `0x4169`.
Steam still reported v0.1.63, handle `6015138325193005907`, 95,645,866 bytes.
The five local package hashes above were unchanged and the preflight passed.

VT2 is absent from the current Steam library's installed-app list, but the
SDK and uploader remain present. [Valve's SteamAPI_Init requirements](https://partner.steamgames.com/doc/api/steam_api#SteamAPI_Init)
specify a running client, resolvable App ID, matching Windows user/elevation,
and the active account's license; they do not list game installation as a
requirement. The uploader's working directory contains App ID 552500. Steam
and the shell use the same Windows user/session and both have Medium integrity
(`0x2000`), ruling out the checked elevation mismatch. Current Steam license
state and the exact cause of the failed initialization remain unverified.
Do not trigger a large game reinstall based only on the missing manifest.

## Verified publication — 2026-09-07 17:47:44 UTC

The user explicitly authorized restarting Steam and completing the upload.
Steam exited through its normal `-shutdown` command and relaunched with
`-silent`; no forced process termination, game installation, registry edit, or
DLL replacement was performed. The new client signed in normally, and its
recorded process ID matched the running client. This restart resolved the
observed uploader failure; it does not establish why the prior client session
became inconsistent.

The unchanged, hash-verified package was uploaded using the guarded VMB
upload-only command. The uploader completed successfully, and Steam's
published-file API independently confirmed:

- Item `3794172730`, title `Warprocket Bombardier TEST v0.1.64-dev`.
- New content handle **`1532641586336614793`**.
- Exact content size **95,349,849 bytes**, matching the local package.
- Public visibility, unchanged white-on-black TEST thumbnail, development
  warning, VMF requirement, issue chooser, and the new portrait description.

Public item `3771657344` remains v0.1.55-alpha, handle `6702297514175948321`,
92,589,521 bytes. No public-alpha upload was made.

Record this publication with one matching lightweight `v0.1.64-dev` tag and
GitHub prerelease at the publication-record commit. Issue #12 remains open
for host/client visual results against the now-published v0.1.64 load marker.
