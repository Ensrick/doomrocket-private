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
        "warlock_bombardier_3p.state_machine")) {
    Assert-True (Test-Path (Join-Path $unitDir $required)) "missing unit source: $required"
}
# Clip coverage is checked dynamically below: every animation the state
# machine references must exist as .fbx + .animation.

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

# --- Ragdoll invariants (v0.1.44) -------------------------------------------
# v0.1.40-43 proved the custom PhysX scene can be activated internally by the
# outfit state machine before Lua can reassert kinematic mode. It must not be
# compiled at all. The visible outfit follows the hidden vanilla owner's
# authored death/ragdoll through the pre-event bone bridge.
$physxPath = Join-Path $unitDir "warlock_bombardier_3p.physx"
Assert-True (-not (Test-Path $physxPath)) `
    "custom .physx must stay absent (v0.1.40-43 world-physics explosion class)"
Assert-True ($smText -notmatch '(?m)^ragdolls\s*=') `
    ".state_machine must not declare a custom ragdolls block"
Assert-True ($smText -notmatch 'state_type\s*=\s*"ragdoll"') `
    ".state_machine must not contain a custom ragdoll state"

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
        'mod\._apply_warlock_child_materials\(outfit_unit\)')) {
    Assert-True ($hooks -match $call) "hooks.lua warlock branch missing required call: $call"
}
Assert-True ($hooks -match 'Application\.can_get\("material",\s*material_path\)') `
    "runtime material swap must verify each spliced child material is resident"
Assert-True ($hooks -match 'Application\.can_get\("texture",\s*texture_path\)') `
    "runtime material diagnostics must verify custom texture residency"
Assert-True ($hooks -notmatch 'Actor\.set_kinematic\(actor,\s*false\)') `
    "custom warlock actors must never be released (v0.1.42 solver-explosion class)"
Assert-True ($hooks -notmatch 'Unit\.(?:find_actor|actor)\(outfit_unit') `
    "custom outfit must not participate in actor physics at all"
Assert-True ($hooks -match 'AttachmentNodeLinking\.doomrocket_warlock_bridge') `
    "death handoff must use the pruned vanilla Skaven bone bridge"
Assert-True ($hooks -notmatch 'World\.unlink_unit\(world,\s*outfit_unit\)') `
    "death handoff must preserve the living root-only attachment"
Assert-True ($hooks -notmatch 'World\.link_unit\(world,\s*outfit_unit,\s*target_index,\s*owner_unit,\s*source_index\)') `
    "death handoff must not independently link outfit bones (v0.1.44 stick-figure class)"
Assert-True ($hooks -match 'Unit\.set_local_pose\(outfit_unit,\s*pair\.target') `
    "death driver must write carrier poses into the intact outfit hierarchy"
Assert-True ($hooks -match 'Unit\.local_pose\(owner_unit,\s*pair\.source\)') `
    "death driver must read local poses from the vanilla carrier"

$deathReactions = Get-Content (Join-Path $repoRoot "scripts\mods\doomrocket\extensions\death_reactions.lua") -Raw
Assert-True ([regex]::Matches($deathReactions, 'mod\._prepare_warlock_death\(').Count -eq 2) `
    "doomrocket death reaction must prepare the vanilla carrier for both unit and husk"
Assert-True ([regex]::Matches($deathReactions,
        '(?s)start = function \([^)]+\)\s*local warlock_pose_driver = mod\._prepare_warlock_death\([^)]+\)\s*local data, result = ai_default_(?:unit|husk)_start').Count -eq 2) `
    "vanilla carrier handoff must happen before ai_default_*_start emits the owner death event"
Assert-True ([regex]::Matches($deathReactions, 'mod\._update_warlock_death_pose\(data\)').Count -eq 2) `
    "server and husk corpse updates must continuously copy the carrier pose"
Assert-True ($deathReactions -notmatch 'mod\._(?:schedule|update)_warlock_ragdoll') `
    "delayed custom-ragdoll handoff must not return"
# Exactly one driving mode IN THE WARLOCK BRANCH (the plague monk branch also
# calls disable, so scope the check): bridge (disable ASM, bridge linking, no
# mirror registration) or self-ASM (enable + idle, root linking).
$warlockBranchText = [regex]::Match($hooks, '(?s)elseif outfit_unit_name == "units/warlock_bombardier/warlock_bombardier_3p" then(.*?)\r?\n\s*elseif').Groups[1].Value
Assert-True ($warlockBranchText.Length -gt 0) "could not extract the warlock branch from hooks.lua"
$hasDisable = $warlockBranchText -match 'Unit\.disable_animation_state_machine\(outfit_unit\)'
$hasEnable = $warlockBranchText -match 'Unit\.enable_animation_state_machine\(outfit_unit\)'
Assert-True ($hasDisable -xor $hasEnable) `
    "warlock branch must use exactly one driving mode (disable-ASM bridge or enable-ASM self-anim)"

# v0.1.27 crash class: firing an animation event into a DISABLED state machine
# is an engine assert - bridge mode must not register for event mirroring.
if ($hasDisable) {
    Assert-True ($warlockBranchText -notmatch '_warlock_outfits\[unit\]\s*=') `
        "bridge mode (disabled ASM) must not register the outfit in mod._warlock_outfits (v0.1.27 crash class)"
}

# v0.1.27: the unit compiles on Dalo's 97-bone skeleton; every bridge TARGET
# must exist on the unit (missing target = uncatchable Unit.node fatal at
# vanilla link time). The WARLOCK_UNIT_BONES whitelist in the inventory lua
# must exactly match the shipped .bones list.
$bonesText = Get-Content (Join-Path $unitDir "warlock_bombardier_3p.bones") -Raw
$bonesList = [regex]::Matches($bonesText, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
$invText = Get-Content (Join-Path $repoRoot "scripts\mods\doomrocket\breeds\skaven_doomrocket_inventory.lua") -Raw
$whitelistBlock = [regex]::Match($invText, '(?s)local WARLOCK_UNIT_BONES = \{(.*?)\}').Groups[1].Value
$whitelist = [regex]::Matches($whitelistBlock, '\["([^"]+)"\]') | ForEach-Object { $_.Groups[1].Value }
Assert-True ($whitelist.Count -eq $bonesList.Count) `
    "WARLOCK_UNIT_BONES count $($whitelist.Count) != .bones count $($bonesList.Count)"
$diff = Compare-Object $whitelist $bonesList
Assert-True (-not $diff) "WARLOCK_UNIT_BONES diverges from .bones: $(($diff | ForEach-Object InputObject) -join ', ')"
# Linking table must match the driving mode: bridge mode drives per-bone
# through the filtered bridge; self-ASM mode must root-link only (per-bone
# links would fight the enabled state machine).
if ($hasDisable) {
    Assert-True ($invText -match 'bombadier_curiass\.attachment_node_linking = AttachmentNodeLinking\.doomrocket_warlock_bridge') `
        "bridge driving mode requires the filtered doomrocket_warlock_bridge linking"
} else {
    Assert-True ($invText -match 'bombadier_curiass\.attachment_node_linking = AttachmentNodeLinking\.doomrocket_warlock_root') `
        "self-ASM driving mode requires root-only linking"
}

# v0.1.25 crash class: variable/constraint indices are only meaningful within
# one compiled state machine; forwarding a raw index to a unit on a different
# SM is an engine assert pcall cannot catch. Only name-based event mirroring
# (gated on Unit.has_animation_event) is safe.
Assert-True ($hooks -notmatch 'mod:hook\(Unit,\s*"animation_set_variable"') `
    "hooks.lua must not mirror animation_set_variable by raw index (v0.1.25 crash class)"
Assert-True ($hooks -notmatch 'mod:hook\(Unit,\s*"animation_set_constraint_target"') `
    "hooks.lua must not mirror animation_set_constraint_target by raw index (v0.1.25 crash class)"

# v0.1.27 crash class check moved below the driving-mode extraction: bridge
# mode (warlock branch disables its ASM) must not register for mirroring.

$doomrocketLua = Get-Content (Join-Path $repoRoot "scripts\mods\doomrocket\doomrocket.lua") -Raw
Assert-True ($doomrocketLua -match 'chr_third_person_mesh') `
    "doomrocket.lua must force-load the Globadier donor package (spliced children reference its aux textures)"

# Slot names in the runtime swap table must exactly match the .unit materials block.
$slotNames = [regex]::Matches($unitText, '(?m)^\s*(\w+)\s*=\s*"materials/warlock_bombardier/') | ForEach-Object { $_.Groups[1].Value }
foreach ($slot in $slotNames) {
    Assert-True ($hooks -match "`"$slot`"\s*,\s*`"child_materials/warlock_bombardier/") `
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
