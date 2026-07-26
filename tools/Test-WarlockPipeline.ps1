# Static validation for the Warlock Bombardier pipeline. Run after
# splice_warlock_materials.ps1, before deploy/upload. Exits non-zero on any
# violation of the invariants in docs/WARLOCK_MODEL_PIPELINE.md.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$failures = New-Object System.Collections.Generic.List[string]

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { $failures.Add($Message) }
}

# --- Source layout invariants ----------------------------------------------

$unitDir = Join-Path $repoRoot "units\warlock_bombardier"
foreach ($required in @(
        "warlock_bombardier_3p.fbx", "warlock_bombardier_3p.unit",
        "warlock_bombardier_3p.bones", "warlock_bombardier_3p.dcc_asset",
        "warlock_bombardier_3p.state_machine",
        "anims\warlock_idle.fbx", "anims\warlock_idle.animation")) {
    Assert-True (Test-Path (Join-Path $unitDir $required)) "missing unit source: $required"
}

$unitText = Get-Content (Join-Path $unitDir "warlock_bombardier_3p.unit") -Raw
Assert-True ($unitText -match 'animation_state_machine\s*=\s*"units/warlock_bombardier/warlock_bombardier_3p"') `
    ".unit must reference its OWN state machine (v0.1.24: vanilla SMs on a mod skeleton are an uncatchable AnimationBlender crash)"

$smText = Get-Content (Join-Path $unitDir "warlock_bombardier_3p.state_machine") -Raw
Assert-True ($smText -match 'bones\s*=\s*"units/warlock_bombardier/warlock_bombardier_3p"') `
    ".state_machine bones key must be the unit's own path"

# Every animation referenced by the state machine must exist as clip + recipe
# and every .animation recipe must target the unit's own skeleton.
foreach ($match in [regex]::Matches($smText, '"units/warlock_bombardier/anims/([^"]+)"')) {
    $clip = $match.Groups[1].Value
    Assert-True (Test-Path (Join-Path $unitDir "anims\$clip.fbx")) "state machine references missing clip FBX: $clip"
    Assert-True (Test-Path (Join-Path $unitDir "anims\$clip.animation")) "state machine references missing .animation recipe: $clip"
}
foreach ($recipe in (Get-ChildItem (Join-Path $unitDir "anims") -Filter *.animation)) {
    $recipeText = Get-Content $recipe.FullName -Raw
    Assert-True ($recipeText -match 'bones\s*=\s*"units/warlock_bombardier/warlock_bombardier_3p"') `
        "$($recipe.Name): bones key must be the unit's own path"
}

# --- Package layout invariants (v0.1.16 boot-crash class) -------------------

$modFile = Get-Content (Join-Path $repoRoot "doomrocket.mod") -Raw
Assert-True ($modFile -notmatch 'warlock_child') `
    "doomrocket.mod must NOT boot-load the child package (spliced children crash PatchedResourcePackage::flush)"

$mainPackage = Get-Content (Join-Path $repoRoot "resource_packages\doomrocket\doomrocket.package") -Raw
Assert-True ($mainPackage -notmatch 'child_materials') `
    "main package must NOT list child_materials (boot-crash class)"

$childPackage = Join-Path $repoRoot "resource_packages\doomrocket\warlock_child.package"
Assert-True (Test-Path $childPackage) "missing warlock_child.package"
$childMaterials = @("wb_armor_child", "wb_backpack_child", "wb_skin_child", "wb_fur_child", "wb_whiskers_child")
if (Test-Path $childPackage) {
    $childText = Get-Content $childPackage -Raw
    foreach ($name in $childMaterials) {
        Assert-True ($childText -match [regex]::Escape("child_materials/warlock_bombardier/$name")) `
            "warlock_child.package missing $name"
        Assert-True (Test-Path (Join-Path $repoRoot "child_materials\warlock_bombardier\$name.material")) `
            "missing child material source: $name.material"
    }
}

# --- Runtime wiring invariants ---------------------------------------------

$hooks = Get-Content (Join-Path $repoRoot "scripts\mods\doomrocket\utils\hooks.lua") -Raw
Assert-True ($hooks -notmatch '(?m)^\s*(?:local\s+swapped\s*=\s*)?(?:pcall\()?\s*(?:Unit\.)?set_animation_state_machine\(outfit_unit') `
    "hooks.lua must not point the outfit at a foreign state machine (v0.1.24 AnimationBlender crash)"
foreach ($call in @(
        'Unit\.set_animation_bone_mode\(outfit_unit,\s*"transform"\)',
        'Unit\.set_bones_lod\(outfit_unit,\s*0\)',
        'Unit\.enable_animation_state_machine\(outfit_unit\)',
        'mod\._apply_warlock_child_materials\(outfit_unit\)')) {
    Assert-True ($hooks -match $call) "hooks.lua warlock branch missing required call: $call"
}

$doomrocketLua = Get-Content (Join-Path $repoRoot "scripts\mods\doomrocket\doomrocket.lua") -Raw
Assert-True ($doomrocketLua -match 'chr_third_person_mesh') `
    "doomrocket.lua must force-load the Globadier donor package (spliced children reference its aux textures)"

# Slot names in the runtime swap table must exactly match the .unit materials block.
$slotNames = [regex]::Matches($unitText, '(?m)^\s*(\w+)\s*=\s*"materials/warlock_bombardier/') | ForEach-Object { $_.Groups[1].Value }
foreach ($slot in $slotNames) {
    Assert-True ($hooks -match "$slot\s*=\s*`"child_materials/warlock_bombardier/") `
        "hooks.lua WARLOCK_SLOT_MATERIALS missing slot '$slot' from the .unit materials block"
}
Assert-True ($slotNames.Count -eq 5) "expected 5 material slots in .unit, found $($slotNames.Count)"

# --- Built bundle invariants (only when bundles exist) ----------------------

$bundleRoot = Join-Path $repoRoot "bundleV2"
$childBundle = Join-Path $bundleRoot "f5283f9585ea8355.mod_bundle"
if (Test-Path $childBundle) {
    # Spliced payload sizes: 3x768 (globadier) + 256 (fur) + 128 (laurel).
    # The SDK-compiled child materials are ~22 KB sources -> 185/321 KB payloads,
    # so tiny record sizes prove the splice actually ran on this bundle.
    $spliceTool = Join-Path $PSScriptRoot "splice_bundle_resource.py"
    $expected = @{ "wb_armor_child" = 768; "wb_backpack_child" = 768; "wb_skin_child" = 768;
                   "wb_fur_child" = 256; "wb_whiskers_child" = 128 }
    foreach ($name in $expected.Keys) {
        # Dry-run output: "<bundle>: splicing (material, <hash>) <current> -> <new> bytes"
        $probe = & py -3 $spliceTool $childBundle --type material `
            --name "child_materials/warlock_bombardier/$name" `
            --payload $spliceTool --dry-run 2>&1 | Out-String
        Assert-True ($probe -match '\)\s+(\d+)\s+->\s+\d+\s+bytes' -and [int]$Matches[1] -eq $expected[$name]) `
            "child bundle: $name is not spliced to $($expected[$name]) B (probe said: $($probe.Trim() -replace '\s+', ' '))"
    }
} else {
    Write-Host "[test] bundleV2 child bundle absent - skipping built-bundle checks (source-only run)"
}

# --- Verdict ----------------------------------------------------------------

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) { Write-Host "[test] FAIL: $failure" -ForegroundColor Red }
    throw "Test-WarlockPipeline: $($failures.Count) failure(s)"
}
Write-Host "[test] OK - warlock pipeline invariants hold"
