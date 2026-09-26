# Reporting TEST-build bugs

Use the [development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose)
and select the gameplay/presentation, crash, or balance/design form.

Before reporting:

1. Use the verified local deploy, or refresh the Workshop subscription; restart Vermintide 2.
2. Launch the Modded Realm with
   [Vermintide Mod Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=1369573612)
   enabled above Warlock Engineer TEST.
3. Enable TEST item `3794172730` only; disable public item `3771657344`.
4. Confirm the exact `[doomrocket:LOAD]` banner in the reproducing log.
5. If you were playing with others, identify your network role and confirm
   everyone used the same build. Solo reports need no second player.

Attach the complete matching file from
`%APPDATA%\Fatshark\Vermintide 2\console_logs\`. Raw `.log`, `.txt`, `.zip`, and
`.gz` files are accepted up to GitHub's attachment limit. Do not paste hundreds
of kilobytes into the issue body. For a crash, also include the crash GUID and
Crashify link. For visual, physics, or audio timing problems, describe what you
saw or heard. Your observation is sufficient to report a failure; no video or
recording is needed. Logs help investigate the cause.

Issues and attachments are public. Review the log before uploading it.
