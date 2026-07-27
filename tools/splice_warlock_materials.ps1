# Splice game-compiled child materials over the compiled
# child_materials/warlock_bombardier/wb_*_child resources in the built
# doomrocket bundle. MUST run after every `VMBLauncher build` and before
# deploy/upload.
#
# Why: the mod SDK cannot compile the character-skinning shader permutation -
# SDK-authored character materials always render the skin rigid and dark
# (vt2-pusfume issue #6, NATIVE_CHARACTER_MILESTONE.md). The proven fix is
# replacing each compiled child-material payload with the game's own compiled
# child (a slim binding table: parent shader hash + texture ids + variables),
# patched to reference this mod's texture resources.
#
# CRITICAL LAYOUT RULE (v0.1.16 boot-crash lesson): spliced children must NOT
# live in the boot-flushed main package. They ride in
# resource_packages/doomrocket/warlock_child.package, which is absent from
# doomrocket.mod's packages list and is loaded at runtime via
# mod:load_package AFTER the Globadier donor package is resident. The five
# materials/warlock_bombardier/wb_* boot materials stay SDK-compiled; the
# runtime swaps each slot to the child via Unit.set_material (hooks.lua).
#
# Donors (Pusfume-proven):
#   opaque (armor/backpack/skin) <- Globadier dark-pact mtr_outfit child, 768 B
#   fur                          <- native Skaven mtr_fur_1bit_climate, 256 B
#   whiskers/alpha cards         <- Laurel feather child, 128 B
#
# Donor payloads derive from Fatshark game data: they are built under .build\
# and must never be committed.

param(
    [string]$GameBundleDir = "C:\Program Files (x86)\Steam\steamapps\common\Warhammer Vermintide 2\bundle",
    [string]$UnpackerExe = "C:\Tools\vt2_bundle_unpacker\target\release\unpacker.exe",
    [string]$UnpackerDict = "C:\Users\danjo\source\repos\vt2_bundle_unpacker\dictionary.csv"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$bundleRoot = Join-Path $repoRoot "bundleV2"
$buildDir = Join-Path $repoRoot ".build\splice"
$makeTool = Join-Path $PSScriptRoot "make_spliced_child.py"
$spliceTool = Join-Path $PSScriptRoot "splice_bundle_resource.py"

New-Item -ItemType Directory -Force $buildDir | Out-Null

function Invoke-Py {
    param([string[]]$Arguments)
    & py -3 @Arguments 2>&1 | ForEach-Object { "  $_" }
    if ($LASTEXITCODE -ne 0) { throw "python tool failed: $($Arguments -join ' ')" }
}

# --- 1. Extract donor payloads from the installed game ---------------------

$donors = @(
    @{ Key = "globadier"; Bundle = "7a8e617a32277fc4"; Include = "*90BDF3BAC6F81BA8*"; File = "90BDF3BAC6F81BA8.material" },
    @{ Key = "laurel";    Bundle = "95865e5dbaf202e3"; Include = "*C70B1AAD3B363E24*"; File = "C70B1AAD3B363E24.material" },
    @{ Key = "fur";       Bundle = "6766ece9a8417e33"; Include = "*mtr_fur_1bit_climate*"; File = "units_beings_enemies_mtr_fur_1bit_climate.material" }
)
foreach ($donor in $donors) {
    $dir = Join-Path $buildDir $donor.Key
    New-Item -ItemType Directory -Force $dir | Out-Null
    & $UnpackerExe --dict $UnpackerDict extract (Join-Path $GameBundleDir $donor.Bundle) $dir --flatten --include $donor.Include 2>&1 | Out-Null
    if (-not (Test-Path (Join-Path $dir $donor.File))) {
        throw "donor extraction failed: $($donor.Key) -> $($donor.File)"
    }
    Write-Host "[splice] extracted donor $($donor.Key)"
}
$globadierPayload = Join-Path $buildDir "globadier\90BDF3BAC6F81BA8.material"
$laurelPayload = Join-Path $buildDir "laurel\C70B1AAD3B363E24.material"
$furPayload = Join-Path $buildDir "fur\units_beings_enemies_mtr_fur_1bit_climate.material"

# --- 2. Build patched payloads ---------------------------------------------
# Texture ids = murmur64 of extensionless resource paths.
# Globadier channels: texture_map_02af90f8=diffuse, 27b67fd2=emissive,
# 8bf37d8e=normal+gloss-in-alpha. Variable C985395A is the donor's warpstone
# emissive_color [14.2, 25.3, 2].
# v0.1.41 texture pass (Crunch's masters, blend-verified wiring): armor has NO
# emissive (E_01 is pure black - donor black kept, variable zeroed); the
# BACKPACK is the emissive slot (E_02 warpstone glow -> wb_backpack_e, variable
# restored); skin now ships the vanilla body normal (gloss = skin MASE.A)
# instead of the flat stub.

$opaque = @(
    @{ Name = "wb_armor";    Df = "300FD46C61FB7091"; Nm = "DD7D6050A52FBF6D"; Em = "45FFAEEF53695A86"; EmVar = "0,0,0" },
    @{ Name = "wb_backpack"; Df = "C4D517C71806AE3B"; Nm = "38DFFF0C6905532F"; Em = "4F71D9C786EFF4D3"; EmVar = "8,8,8" },
    @{ Name = "wb_skin";     Df = "B42E3663823A42B7"; Nm = "DF22A46A364470F8"; Em = "45FFAEEF53695A86"; EmVar = "0,0,0" }
)
foreach ($mat in $opaque) {
    Write-Host "[splice] payload $($mat.Name)_child (globadier opaque donor)"
    Invoke-Py @($makeTool,
        "--extracted", $globadierPayload,
        "--resource", "child_materials/warlock_bombardier/$($mat.Name)_child",
        "--expect-size", "768", "--expect-parent", "3D25339231384C80",
        "--map", "DD74D8319F514D96=$($mat.Df)",
        "--map", "E334A8CB6BCB5E6D=$($mat.Nm)",
        "--map", "45FFAEEF53695A86=$($mat.Em)",
        "--set-variable", "C985395A=$($mat.EmVar)",
        "--expect-texture", "texture_map_02af90f8=$($mat.Df)",
        "--expect-texture", "texture_map_27b67fd2=$($mat.Em)",
        "--expect-texture", "texture_map_8bf37d8e=$($mat.Nm)",
        "--out", (Join-Path $buildDir "$($mat.Name)_child.payload"))
}

Write-Host "[splice] payload wb_whiskers_child (laurel alpha-card donor)"
Invoke-Py @($makeTool,
    "--extracted", $laurelPayload,
    "--resource", "child_materials/warlock_bombardier/wb_whiskers_child",
    "--expect-size", "128", "--expect-parent", "F85B289742D5D69A",
    "--map", "C9CF19C214612D75=C02CF6B03A57BA9A",
    "--map", "CDA03B9B0226037A=643B3C4BBA851928",
    "--map", "D3FD8377A3DE498A=3784C666E3B8724B",
    "--expect-texture", "texture_map_c0ba2942=C02CF6B03A57BA9A",
    "--expect-texture", "texture_map_59cd86b9=643B3C4BBA851928",
    "--expect-texture", "texture_map_b788717c=3784C666E3B8724B",
    "--out", (Join-Path $buildDir "wb_whiskers_child.payload"))

# Fur keeps every donor texture id: the donor references the exact vanilla fur
# maps this design wants; skaven levels keep them resident. Self-map = no-op.
Write-Host "[splice] payload wb_fur_child (native skaven fur donor, unpatched)"
Invoke-Py @($makeTool,
    "--extracted", $furPayload,
    "--resource", "child_materials/warlock_bombardier/wb_fur_child",
    "--expect-size", "256", "--expect-parent", "7B55B884FAFA2B12",
    "--map", "1916CFCA6ED85BFD=1916CFCA6ED85BFD",
    "--expect-texture", "texture_map_5e198820=1916CFCA6ED85BFD",
    "--out", (Join-Path $buildDir "wb_fur_child.payload"))

# --- 3. Splice each payload into exactly one built bundle ------------------

$materials = @("wb_armor", "wb_backpack", "wb_skin", "wb_whiskers", "wb_fur")
foreach ($mat in $materials) {
    $payload = Join-Path $buildDir "${mat}_child.payload"
    $resource = "child_materials/warlock_bombardier/${mat}_child"
    $splicedInto = @()
    foreach ($bundleFile in (Get-ChildItem -LiteralPath $bundleRoot -Filter *.mod_bundle -File)) {
        & py -3 $spliceTool $bundleFile.FullName --type material --name $resource --payload $payload --dry-run *> $null
        if ($LASTEXITCODE -eq 0) {
            Invoke-Py @($spliceTool, $bundleFile.FullName,
                "--type", "material", "--name", $resource, "--payload", $payload)
            $splicedInto += $bundleFile.Name
        }
    }
    if ($splicedInto.Count -ne 1) {
        throw "expected $resource in exactly 1 bundle, spliced into $($splicedInto.Count)"
    }
    Write-Host "[splice] $resource -> $($splicedInto[0])"
}

Write-Host "[splice] OK - 5 warlock child materials carry game bindings"
