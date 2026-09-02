# Release channels

Warprocket Bombardier uses two public channels with separate worktrees,
repositories, Workshop items, thumbnails, and release guards.

| Channel | Local worktree | GitHub / branch | Steam Workshop | Required title |
| --- | --- | --- | --- | --- |
| Public alpha | `C:\Users\danjo\source\repos\doomrocket-public` | `Ensrick/doomrocket-public` / `main` | `3771657344` | `Warprocket Bombardier v<version>-alpha` |
| Development TEST | `C:\Users\danjo\source\repos\doomrocket` | `Ensrick/doomrocket-private` / `private-copy` | `3794172730` | `Warprocket Bombardier TEST v<version>-dev` |

The TEST item must remain public, start its description with a prominent
instability warning, and use `item_preview_test.png`. Both packages retain the
same internal mod identity, so never enable them together; every lobby member
must use the same channel and exact version.

## Development publication procedure

```powershell
$vmbExe = 'C:\Users\danjo\source\repos\vmb-launcher-baseline-056-20260726\bin\Release\net9.0-windows\win-x64\publish\VMBLauncher.exe'
$devCfg = 'C:\Users\danjo\source\repos\_doomrocket_vmb\vmblauncher.settings.json'

py -3 tools/check_repository.py --channel development
& $vmbExe build doomrocket --clean --config $devCfg
powershell -NoProfile -ExecutionPolicy Bypass -File tools\splice_warlock_materials.ps1 -UseVerifiedCache
powershell -NoProfile -ExecutionPolicy Bypass -File tools\Test-WarlockPipeline.ps1
& $vmbExe deploy doomrocket --no-remote --config $devCfg
& $vmbExe upload doomrocket --allow-public --config $devCfg
```

Afterward, verify the live Workshop title, public visibility, warning,
ManifestID/time, and content size. Confirm the TEST thumbnail is still present.
Never use `vmblauncher all`; it has no material-splice checkpoint.

Promotion is a deliberate second change: only runtime-accepted commits are
ported into the public-alpha worktree, retested there, and uploaded to item
`3771657344` using that repository's procedure.
