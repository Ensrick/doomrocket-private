[CmdletBinding()]
param(
    [string]$RepoRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$FixtureOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$failures = [System.Collections.Generic.List[string]]::new()
$policyPath = Join-Path $RepoRoot 'tools\lib\WarlockRagdollPolicy.ps1'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\warlock_ragdoll'
$manifestPath = Join-Path $fixtureRoot 'fixtures.psd1'
$analyzerPath = Join-Path $RepoRoot 'tools\analyze_warlock_ragdoll_log.py'
$retargetMathTestPath = Join-Path $PSScriptRoot 'test_warlock_retarget_math.py'
$forbiddenFixtureAssetExtensions = @(
    '.animation', '.bones', '.dcc_asset', '.flow', '.lua', '.material', '.package',
    '.physx', '.shader_source', '.state_machine', '.texture', '.unit'
)

function Add-TestFailure {
    param([Parameter(Mandatory)][string]$Message)
    [void]$script:failures.Add($Message)
}

function Get-CaseText {
    param(
        [Parameter(Mandatory)][hashtable]$Case,
        [Parameter(Mandatory)][string]$Key
    )
    if (-not $Case.ContainsKey($Key) -or -not $Case[$Key]) {
        return ''
    }
    $path = Join-Path $fixtureRoot $Case[$Key]
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-TestFailure "fixture '$($Case.Name)' is missing $Key file: $path"
        return ''
    }
    Get-Content -LiteralPath $path -Raw
}

function Assert-RuleSet {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Violations,
        [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$ExpectedRules
    )
    $actual = @($Violations | ForEach-Object Id | Sort-Object -Unique)
    $expected = @($ExpectedRules | Sort-Object -Unique)
    $difference = @(Compare-Object -ReferenceObject $expected -DifferenceObject $actual)
    if ($difference.Count -gt 0) {
        $rendered = if ($actual.Count) { $actual -join ', ' } else { '<none>' }
        Add-TestFailure "$Name returned rules [$rendered], expected [$($expected -join ', ')]"
    }
}

if (-not (Test-Path -LiteralPath $policyPath -PathType Leaf)) {
    throw "ragdoll policy module missing: $policyPath"
}
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "ragdoll fixture manifest missing: $manifestPath"
}
if (-not (Test-Path -LiteralPath $analyzerPath -PathType Leaf)) {
    throw "ragdoll log analyzer missing: $analyzerPath"
}
if (-not (Test-Path -LiteralPath $retargetMathTestPath -PathType Leaf)) {
    throw "retarget math regression missing: $retargetMathTestPath"
}

. $policyPath
$manifest = Import-PowerShellDataFile -LiteralPath $manifestPath

# VMB discovers compilable resources anywhere below the mod root, including
# tools/tests. A mutation fixture with a real Stingray extension becomes build
# input; the deliberately-invalid custom PhysX fixture caused the toolchain to
# assert while compiling it. Fixtures must use an inert suffix such as
# .state_machine.fixture.txt.
$shippingNamedFixtures = @(Get-ChildItem -LiteralPath $fixtureRoot -Recurse -File |
    Where-Object { $forbiddenFixtureAssetExtensions -contains $_.Extension.ToLowerInvariant() })
foreach ($fixture in $shippingNamedFixtures) {
    Add-TestFailure "fixture uses compilable Stingray extension: $($fixture.FullName)"
}

foreach ($case in $manifest.Cases) {
    $hooksText = Get-CaseText -Case $case -Key 'Hooks'
    $stateMachineText = Get-CaseText -Case $case -Key 'StateMachine'
    $inventoryText = Get-CaseText -Case $case -Key 'Inventory'
    $physxExists = $case.ContainsKey('PhysxExists') -and [bool]$case.PhysxExists
    $violations = @(Test-WarlockRagdollPolicy `
        -HooksText $hooksText `
        -StateMachineText $stateMachineText `
        -InventoryText $inventoryText `
        -PhysxExists $physxExists)
    Assert-RuleSet -Name "mutation '$($case.Name)'" `
        -Violations $violations -ExpectedRules @($case.ExpectedRules)
}

# A positive synthetic contract guards against a policy that merely rejects
# everything. It describes the same world-calibrated, post-animation transfer
# required from production without coupling to unrelated hooks.lua structure.
$candidatePath = Join-Path $fixtureRoot $manifest.CandidateContract
$candidateText = Get-Content -LiteralPath $candidatePath -Raw
$candidateViolations = @(Test-WarlockRagdollPolicy `
    -HooksText $candidateText -RequireCandidateContract)
Assert-RuleSet -Name 'positive candidate contract fixture' `
    -Violations $candidateViolations -ExpectedRules @()

$contractMutations = @(
    @{
        Name = 'living ASM disabled'
        Text = $candidateText.Replace(
            'Unit.enable_animation_state_machine(outfit_unit)',
            'Unit.disable_animation_state_machine(outfit_unit)')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'death bone mode left in transform'
        Text = $candidateText.Replace(
            'Unit.set_animation_bone_mode(outfit_unit, "ignore")',
            'Unit.set_animation_bone_mode(outfit_unit, "transform")')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'pose applied before post-animation callback'
        Text = $candidateText.Replace(
            'animation_system:add_safe_animation_callback',
            'animation_system:add_animation_callback')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'callback omitted for alternate animation update path'
        Text = $candidateText.Replace(
            '"update_animations_with_callback"',
            '"unrelated_world_method"')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'callback queued for a different world'
        Text = $candidateText.Replace(
            'Unit.world(owner) == world',
            'Unit.world(owner) ~= world')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'safe callback self-requeues'
        Text = $candidateText.Replace(
            '            apply_warlock_death_pose(driver)',
            "            apply_warlock_death_pose(driver)`n            queue_warlock_death_pose(driver)")
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'per-frame enqueue guard removed'
        Text = $candidateText.Replace(
            'driver.callback_pending = true',
            'driver.callback_pending = nil')
        ExpectedRules = @('WR-RAG-006')
    }
    @{
        Name = 'inverse-parent conversion removed'
        Text = $candidateText.Replace('Matrix4x4.inverse(', 'Matrix4x4.copy(')
        ExpectedRules = @('WR-RAG-007')
    }
    @{
        Name = 'non-hips translation writer added'
        Text = $candidateText.Replace(
            'if pair.is_hips then',
            "Unit.set_local_position(driver.outfit, pair.target, Vector3.zero())`n        if pair.is_hips then")
        ExpectedRules = @('WR-RAG-007')
    }
    @{
        Name = 'telemetry correlation keys removed'
        Text = $candidateText.Replace('id=%s source=%s', 'driver=%s lane=%s')
        ExpectedRules = @('WR-RAG-008')
    }
    @{
        Name = 'performance telemetry field removed'
        Text = $candidateText.Replace('wall_gap_ms=%.1f', 'callback_gap=%.1f')
        ExpectedRules = @('WR-RAG-008')
    }
    @{
        Name = 'native carrier meshes revealed'
        Text = $candidateText.Replace(
            'Unit.set_mesh_visibility(owner_unit, mesh_index, false, "default")',
            'Unit.set_mesh_visibility(owner_unit, mesh_index, true, "default")')
        ExpectedRules = @('WR-RAG-005')
    }
    @{
        Name = 'obsolete 17-mesh carrier fallback'
        Text = $candidateText.Replace('num_meshes = 24', 'num_meshes = 17')
        ExpectedRules = @('WR-RAG-005')
    }
)
foreach ($mutation in $contractMutations) {
    $violations = @(Test-WarlockRagdollPolicy `
        -HooksText $mutation.Text -RequireCandidateContract)
    Assert-RuleSet -Name "contract mutation '$($mutation.Name)'" `
        -Violations $violations -ExpectedRules @($mutation.ExpectedRules)
}

if (-not $FixtureOnly) {
    $hooksPath = Join-Path $RepoRoot 'scripts\mods\doomrocket\utils\hooks.lua'
    $stateMachinePath = Join-Path $RepoRoot 'units\warlock_bombardier\warlock_bombardier_3p.state_machine'
    $inventoryPath = Join-Path $RepoRoot 'scripts\mods\doomrocket\breeds\skaven_doomrocket_inventory.lua'
    $physxPath = Join-Path $RepoRoot 'units\warlock_bombardier\warlock_bombardier_3p.physx'
    $productionViolations = @(Test-WarlockRagdollPolicy `
        -HooksText (Get-Content -LiteralPath $hooksPath -Raw) `
        -StateMachineText (Get-Content -LiteralPath $stateMachinePath -Raw) `
        -InventoryText (Get-Content -LiteralPath $inventoryPath -Raw) `
        -PhysxExists (Test-Path -LiteralPath $physxPath) `
        -RequireCandidateContract)
    foreach ($violation in $productionViolations) {
        Add-TestFailure "production $($violation.Id): $($violation.Message)"
    }
}

$python = Get-Command py -ErrorAction SilentlyContinue
$pythonPrefix = @('-3')
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    $pythonPrefix = @()
}
if (-not $python) {
    Add-TestFailure 'Python 3 is required to run ragdoll telemetry regressions'
} else {
    $nativePreference = Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
    $oldNativePreference = if ($nativePreference) { $nativePreference.Value } else { $null }
    $PSNativeCommandUseErrorActionPreference = $false
    try {
        $mathOutput = (& $python.Source @pythonPrefix $retargetMathTestPath 2>&1 | Out-String).Trim()
        $mathExitCode = $LASTEXITCODE
        if ($mathExitCode -ne 0) {
            Add-TestFailure "offline retarget math tests exited ${mathExitCode}: $mathOutput"
        }

        foreach ($case in $manifest.AnalyzerCases) {
            $logPath = Join-Path $fixtureRoot $case.Log
            $output = (& $python.Source @pythonPrefix $analyzerPath $logPath 2>&1 | Out-String).Trim()
            $exitCode = $LASTEXITCODE
            if ($exitCode -ne [int]$case.ExpectedExit) {
                Add-TestFailure "analyzer '$($case.Name)' exited $exitCode, expected $($case.ExpectedExit): $output"
            }
            if ($output -notmatch [regex]::Escape([string]$case.ExpectedText)) {
                Add-TestFailure "analyzer '$($case.Name)' output omitted '$($case.ExpectedText)': $output"
            }
        }
    } finally {
        if ($nativePreference) {
            $PSNativeCommandUseErrorActionPreference = $oldNativePreference
        } else {
            Remove-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
        }
    }
}

if ($failures.Count -gt 0) {
    foreach ($failure in $failures) {
        Write-Host "[ragdoll-test] FAIL: $failure" -ForegroundColor Red
    }
    throw "Test-WarlockRagdollRegressions: $($failures.Count) failure(s)"
}

$scope = if ($FixtureOnly) { 'fixture and analyzer' } else { 'fixture, analyzer, and production' }
Write-Host "[ragdoll-test] OK - $scope regressions hold"
