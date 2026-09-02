# Repository instructions

This checkout is the experimental **development TEST** line. These instructions
apply to human maintainers and AI coding agents.

## Identity and boundaries

- Canonical GitHub repository: `Ensrick/doomrocket-private`, remote `private`.
- Local branch: `private-copy`.
- Steam Workshop item: `3794172730`.
- Required title shape: `Warprocket Bombardier TEST v<version>-dev`.
- Public-alpha worktree: `C:\Users\danjo\source\repos\doomrocket-public`.
- Public Workshop item: `3771657344`; do not edit or upload it from here.

Despite the historical repository name, this repository and its TEST Workshop
item are public. The word `private` identifies the development remote only.
The `origin` remote is dalo_kraff's historical upstream and is fetch-only for
this maintenance line. Push development work only to `private`.

## Start every session

1. Read `PROJECT_STATUS.md` and the relevant GitHub issue.
2. Run `git status --short --branch`; preserve unrelated local changes.
3. Confirm `itemV2.cfg` targets `3794172730`, uses the TEST thumbnail, remains
   public, and contains the instability warning.
4. Treat GitHub Issues as the live backlog. Do not create a competing TODO list.
5. Run `py -3 tools/check_repository.py --channel development` before a commit.

## Evidence and release rules

- Static tests and a successful SDK build are not in-game acceptance. Keep a
  runtime issue open until a matching host/client log and visible test pass.
- Never promote experimental work to `doomrocket-public` implicitly.
- Never commit `bundleV2`, `.build`, `.mod_bundle`, downloaded logs, Wwise
  authoring output, or game-derived donor payloads.
- Never use `vmblauncher all`; it uploads before the required material splice.
- Build order is clean build, verified material splice, full pipeline, optional
  local deploy, TEST upload, then Steam metadata/content verification.
- Both Workshop builds share the same internal mod identity. Never enable them
  together, and every multiplayer participant must use the same exact build.

Full pre-upload gate:

```powershell
py -3 tools/check_repository.py --channel development
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-WarlockPipeline.ps1
```

See `docs/RELEASE_CHANNELS.md`, `CONTRIBUTING.md`, and
`docs/TESTER_QUICKSTART.md` for the human workflows.
