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

Verified preflight facts (host, launcher, claim identity, Steamworks registration
recovery, lease contention, SDK sidecar policy) live in
`docs/RELEASE_CHANNELS.md` under "Verified preflight"; read them before any
build or publication attempt.

## Identity and boundaries

- Canonical GitHub repository: `Ensrick/doomrocket-private`, remote `private`.
- Local branch: `private-copy`.
- Steam Workshop item: `3794172730`.
- Required title shape: `Warlock Engineer TEST v<version>-dev`.
- Public-alpha worktree: `C:\Users\danjo\source\repos\doomrocket-public`.
- Public Workshop item: `3771657344`; do not edit or upload it from here.

Despite the historical repository name, this repository and its TEST Workshop
item are public. The word `private` identifies the development remote only.
The `origin` remote is dalo_kraff's historical upstream and is fetch-only for
this maintenance line. Push development work only to `private`.

## Asset authorship boundary

New art, 3D models, animation clips, audio masters, and other new source assets
belong to Arnaud. Do not invent or author replacement assets to unblock an issue.

Engineering may fix code, adjust packaging of already-approved assets, and
reuse or modify effects already present in the game. Preserve the approved
artist masters when adjusting their packaging. When a fix needs a new source
asset, name that missing asset in the issue and keep it blocked until Arnaud
supplies it.

The user's October 10, 2026 instruction explicitly authorizes engineering to
prepare the existing Warlock model for Arnaud to animate: control curves,
FK/IK, native twist, stretch/squash, and localized cloth/accessory corrections.
The reproducible tools and diagnostic poses are documented in
`docs/ANIMATION_AUTHORING.md`. Preserve artist masters and the shipping skeleton;
keep generated `.blend`/FBX handoff assets outside Git. This exception does not
authorize replacement art or a new production animation set. Authoring and SDK
checks do not establish an in-game pass or authorize alpha promotion.

## Start every session

1. Read `PROJECT_STATUS.md` and the relevant GitHub issue.
2. Run `git status --short --branch`; preserve unrelated local changes.
3. Confirm `itemV2.cfg` targets `3794172730`, uses the TEST thumbnail, remains
   public, and contains the instability warning.
4. Treat GitHub Issues as the live backlog. Do not create a competing TODO list.
5. Run `py -3 tools/check_repository.py --channel development` before a commit.

## Publication-only TEST exception, October 20, 2026

- The user explicitly ruled that the local launch requirement does not apply
  here because Vermintide 2 is not installed, and authorized uploading
  v0.1.94-dev to TEST for Crunch to test. The October 23 request authorizes
  the next TEST with the first-spawn, gem flame and hose fixes. Use canonical
  VMB publication-only mode; retain source plus receipt authority, hosted QA
  and fresh transaction verification. This scoped ruling supersedes the earlier
  October 20 handoff hold. No local or remote game deployment or alpha promotion
  is authorized.
- Crunch accepted the ordinary-spawn fix on published v0.1.94-dev;
  [#65](https://github.com/Ensrick/doomrocket-private/issues/65) is closed. Do not
  repeat that accepted check as a mandatory gate. The v0.1.95-dev source
  candidate addresses first-spawn loading [#69](https://github.com/Ensrick/doomrocket-private/issues/69),
  green/smaller gem flame #15 and reduced hose flapping #3. Retain the last
  verified publication record until a fresh upload is verified, then set concrete
  remaining tests and accurate ready-for-testing/testing labels. Preserve
  existing tracks, custom poses and secondary hose physics.
- No local manifest `552500`, game executable or game bundles are available;
  the installed SDK oracle fails before Lua boot. Record this coverage limit.
  Publication and offline checks establish no native startup, animation or
  visual pass. Accept Crunch's written runtime feedback and matching logs.
  Preserve current sessions and resource guards; do not invent launch flags,
  use GUI automation or install the game to satisfy an exempted local check.
- Historical receipts and artist-rig links retain their original scope.

## Build environment hygiene

Keep temporary build settings in a copied child environment. If a PowerShell
caller changes process `$env:` values, save and restore them in `try/finally`;
never persist build settings, edit global PATH, dot-source a build launcher, or
install build-only tools globally. Reuse compatible existing caches. Before every
`dotnet` invocation with an isolated `DOTNET_CLI_HOME`, explicitly set
`DOTNET_ADD_GLOBAL_TOOLS_TO_PATH=false` and
`DOTNET_GENERATE_ASPNET_CERTIFICATE=false` in that child environment. Preserve
user/machine environment values and types; never restore a stale whole PATH.

## Evidence and release rules

- Accept a tester's written report of what they saw or heard as the runtime
  observation. A reported missing hose is a failure even when offline checks
  pass. Do not request videos or recordings; use matching console logs to
  investigate the cause, not to dispute the tester's observation.
- Static tests and a successful SDK build are not in-game acceptance. Accept
  the tester's written visual or audio verdict and use a matching build log
  where it helps diagnose behavior. A solo report is sufficient; multiplayer
  testing is not a standing acceptance gate.
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
source before hosted QA and merge. Use publication-only mode under the user's
October 20 exception because the game is not installed. Verified publication
authorizes the TEST handoff; it does not establish native runtime acceptance.

See `docs/RELEASE_CHANNELS.md`, `CONTRIBUTING.md`, and
`docs/TESTER_QUICKSTART.md` for the human workflows.
