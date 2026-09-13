# Regression for standalone commit paths: mutable files cannot replace commit proof.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../ship/publication-snapshot.ps1')
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('warlock-publication-layout-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($fixture) | Out-Null
function Invoke-FixtureGit([string[]]$Arguments) {
    $output = & git -C $fixture @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Fixture git failed: $Arguments" }
    return $output
}
try {
    $files = @{
        'itemV2.cfg' = 'published_id = 3794172730L; preview = "item_preview_test.png"; visibility = "public";'
        'item_preview_test.png' = 'fixture-preview'
        'doomrocket.mod' = 'fixture-descriptor'
        'scripts/mods/doomrocket/doomrocket.lua' = 'local MOD_VERSION = "0.1.68-dev"'
        'bundleV2/doomrocket.mod' = 'fixture-descriptor'
        'bundleV2/ac226cc769a897ae.mod_bundle' = 'fixture-bundle'
    }
    foreach ($entry in $files.GetEnumerator()) {
        $path = Join-Path $fixture $entry.Key
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
        [IO.File]::WriteAllText($path, $entry.Value, [Text.UTF8Encoding]::new($false))
    }
    $null = Invoke-FixtureGit @('init', '--quiet')
    $null = Invoke-FixtureGit @('config', 'user.name', 'Publication fixture')
    $null = Invoke-FixtureGit @('config', 'user.email', 'fixture@example.invalid')
    $null = Invoke-FixtureGit @('add', '.')
    $null = Invoke-FixtureGit @('commit', '--quiet', '-m', 'Standalone fixture')
    $commit = (Invoke-FixtureGit @('rev-parse', 'HEAD')).Trim()
    [IO.File]::WriteAllText((Join-Path $fixture 'itemV2.cfg'), 'published_id = 3771657344L;')
    [IO.File]::WriteAllText((Join-Path $fixture 'bundleV2/ac226cc769a897ae.mod_bundle'), 'replacement')
    $snapshot = Get-PublicationCommitSnapshot -RepoRoot $fixture -SourceCommit $commit -Mod doomrocket
    if ($snapshot.PublishedId -cne '3794172730' -or $snapshot.Version -cne '0.1.68-dev' -or $snapshot.BundleFiles.Count -ne 2 -or $snapshot.PreviewFile.Path -cne 'item_preview_test.png') { throw 'Standalone commit identity was not preserved.' }
    $bundle = @($snapshot.BundleFiles | Where-Object Path -eq 'ac226cc769a897ae.mod_bundle')[0]
    if ([Text.Encoding]::UTF8.GetString($bundle.Bytes) -cne 'fixture-bundle') { throw 'Mutable bundle replaced committed bytes.' }
    $rejected = $false
    try { $null = Get-WarlockModPrefix 'other_mod' } catch { $rejected = $true }
    if (-not $rejected) { throw 'Foreign mod was accepted by standalone layout.' }
    Write-Host '[publication-layout] OK - root commit identity and bytes survive worktree replacement'
} finally {
    Remove-VtBuildTemporaryDirectory -Path $fixture -ExpectedPrefix 'warlock-publication-layout-'
}
