# Repository instructions

This checkout is the experimental **development TEST** line. These instructions
apply to human maintainers and AI coding agents.


## Build, deploy and upload authority - user ruling, September 13, 2026

Use the working Vermintide 2 Tweaker method exactly. Read
`docs/RELEASE_CHANNELS.md` and the byte-for-byte upstream copy in
`docs/upstream/vermintide-2-tweaker/PROJECT_STANDARDS.md`, section 6.6.
This ruling supersedes older Warlock release/retry instructions below or in
historical records. Do not invent a separate uploader, use the v0.5.6 baseline
as a fallback, create an interactive launcher fork, or add a routine Steam
restart requirement. The canonical workflow is headless and verifies the actual
Workshop transaction and deployment hashes.

The unchanged upstream snapshot retains Tweaker's original bindings. The
operational adapter is `tools/ship/ship.ps1`, with standalone repository paths
and explicit TEST identity. Keep the Warlock material splice and full asset
pipeline at the build-validation boundary before recording the build receipt.

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
- The release tag and hosted receipt bind the reviewed source commit on the
  live default branch. After verified publication, record its content handle
  and byte size without moving the tag to a later documentation commit.
- Both Workshop builds share the same internal mod identity. Never enable them
  together, and every multiplayer participant must use the same exact build.

Full pre-upload gate:

```powershell
py -3 tools/check_repository.py --channel development
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Test-WarlockPipeline.ps1
```

`tools/Invoke-DoomrocketRelease.ps1` delegates to the canonical standalone
adapter. Generated bundles stay ignored; commit `.build-receipt.json` with
source before hosted QA and merge. This release uses publication-only mode
because the game is not installed; no deployment or game acceptance is claimed.

See `docs/RELEASE_CHANNELS.md`, `CONTRIBUTING.md`, and
`docs/TESTER_QUICKSTART.md` for the human workflows.
