# Reporting TEST-build bugs

Use the [development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose)
and select the gameplay/presentation, crash, or balance/design form.

Before reporting:

1. Fully restart Steam and Vermintide after the Workshop update.
2. Launch the Modded Realm with
   [Vermintide Mod Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=1369573612)
   enabled above Warprocket Bombardier.
3. Enable TEST item `3794172730` only; disable public item `3771657344`.
4. Confirm the exact `[doomrocket:LOAD]` banner in the reproducing log.
5. Record whether you were host, remote client, or solo and whether every lobby
   member used the same build.

Attach the complete matching file from
`%APPDATA%\Fatshark\Vermintide 2\console_logs\`. Raw `.log`, `.txt`, `.zip`, and
`.gz` files are accepted up to GitHub's attachment limit. Do not paste hundreds
of kilobytes into the issue body. For a crash, also include the crash GUID and
Crashify link. For visual, physics, or audio timing problems, a short continuous
video is useful.

Issues and attachments are public. Review the log before uploading it.
