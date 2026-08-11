# Source-policy checks for the Warlock Bombardier death handoff.
#
# This file deliberately separates permanent safety rules (the historical
# failure classes) from the current candidate contract. Mutation fixtures use
# the safety rules in isolation; the shipping pipeline enables both.

Set-StrictMode -Version Latest

function Get-LuaLongBracket {
    param(
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][int]$Index
    )

    if ($Index -ge $Text.Length -or $Text[$Index] -ne '[') {
        return $null
    }

    $cursor = $Index + 1
    while ($cursor -lt $Text.Length -and $Text[$cursor] -eq '=') {
        $cursor++
    }

    if ($cursor -ge $Text.Length -or $Text[$cursor] -ne '[') {
        return $null
    }

    $equals = $cursor - $Index - 1
    [pscustomobject]@{
        OpenEnd = $cursor + 1
        Close = ']' + ('=' * $equals) + ']'
    }
}

function Add-BlankedLuaSegment {
    param(
        [Parameter(Mandatory)][System.Text.StringBuilder]$Builder,
        [Parameter(Mandatory)][string]$Text,
        [Parameter(Mandatory)][int]$Start,
        [Parameter(Mandatory)][int]$End
    )

    for ($i = $Start; $i -lt $End; $i++) {
        $char = $Text[$i]
        if ($char -eq "`r" -or $char -eq "`n") {
            [void]$Builder.Append($char)
        } else {
            [void]$Builder.Append(' ')
        }
    }
}

function ConvertFrom-LuaSource {
    <#
    .SYNOPSIS
    Removes Lua comments and, optionally, strings while preserving line breaks.

    .DESCRIPTION
    Raw regexes against hooks.lua previously matched comments describing a
    forbidden API and could therefore pass or fail for the wrong reason. This
    small lexer understands line comments, long-bracket comments/strings, and
    quoted strings well enough for source-policy checks without adding a parser
    dependency to the build machine.
    #>
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [switch]$StripStrings
    )

    $builder = [System.Text.StringBuilder]::new($Text.Length)
    $i = 0

    while ($i -lt $Text.Length) {
        # Line or long-bracket comment.
        if ($i + 1 -lt $Text.Length -and $Text[$i] -eq '-' -and $Text[$i + 1] -eq '-') {
            $long = $null
            if ($i + 2 -lt $Text.Length) {
                $long = Get-LuaLongBracket -Text $Text -Index ($i + 2)
            }

            if ($long) {
                $closeAt = $Text.IndexOf($long.Close, $long.OpenEnd, [System.StringComparison]::Ordinal)
                $end = if ($closeAt -ge 0) { $closeAt + $long.Close.Length } else { $Text.Length }
                Add-BlankedLuaSegment -Builder $builder -Text $Text -Start $i -End $end
                $i = $end
                continue
            }

            $end = $i + 2
            while ($end -lt $Text.Length -and $Text[$end] -ne "`r" -and $Text[$end] -ne "`n") {
                $end++
            }
            Add-BlankedLuaSegment -Builder $builder -Text $Text -Start $i -End $end
            $i = $end
            continue
        }

        # Single- or double-quoted string.
        if ($Text[$i] -eq "'" -or $Text[$i] -eq '"') {
            $quote = $Text[$i]
            $end = $i + 1
            while ($end -lt $Text.Length) {
                if ($Text[$end] -eq '\') {
                    $end = [Math]::Min($end + 2, $Text.Length)
                    continue
                }
                if ($Text[$end] -eq $quote) {
                    $end++
                    break
                }
                $end++
            }

            if ($StripStrings) {
                Add-BlankedLuaSegment -Builder $builder -Text $Text -Start $i -End $end
            } else {
                [void]$builder.Append($Text.Substring($i, $end - $i))
            }
            $i = $end
            continue
        }

        # Long-bracket string.
        if ($Text[$i] -eq '[') {
            $long = Get-LuaLongBracket -Text $Text -Index $i
            if ($long) {
                $closeAt = $Text.IndexOf($long.Close, $long.OpenEnd, [System.StringComparison]::Ordinal)
                $end = if ($closeAt -ge 0) { $closeAt + $long.Close.Length } else { $Text.Length }
                if ($StripStrings) {
                    Add-BlankedLuaSegment -Builder $builder -Text $Text -Start $i -End $end
                } else {
                    [void]$builder.Append($Text.Substring($i, $end - $i))
                }
                $i = $end
                continue
            }
        }

        [void]$builder.Append($Text[$i])
        $i++
    }

    $builder.ToString()
}

function Add-WarlockPolicyViolation {
    param(
        [Parameter(Mandatory)][AllowEmptyCollection()][System.Collections.Generic.List[object]]$Violations,
        [Parameter(Mandatory)][string]$Id,
        [Parameter(Mandatory)][string]$Message,
        [string]$Evidence = ''
    )

    [void]$Violations.Add([pscustomobject]@{
        Id = $Id
        Message = $Message
        Evidence = $Evidence
    })
}

function Test-WarlockRagdollPolicy {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$HooksText,
        [AllowEmptyString()][string]$StateMachineText = '',
        [AllowEmptyString()][string]$InventoryText = '',
        [bool]$PhysxExists = $false,
        [switch]$RequireCandidateContract
    )

    $violations = [System.Collections.Generic.List[object]]::new()
    $hooksWithStrings = ConvertFrom-LuaSource -Text $HooksText
    $hooksTokens = ConvertFrom-LuaSource -Text $HooksText -StripStrings
    $stateMachineCode = ConvertFrom-LuaSource -Text $StateMachineText
    $inventoryCode = ConvertFrom-LuaSource -Text $InventoryText

    $deathMatch = [regex]::Match(
        $hooksTokens,
        '(?s)(?:local\s+WARLOCK_RAGDOLL_SAMPLE_TIMES_MS\b|mod\._prepare_warlock_death\s*=\s*function\b).*?(?=\n\s*mod\._apply_warlock_child_materials\s*=|\z)'
    )
    $deathTokens = if ($deathMatch.Success) { $deathMatch.Value } else { $hooksTokens }

    $deathWithStringsMatch = [regex]::Match(
        $hooksWithStrings,
        '(?s)(?:local\s+WARLOCK_RAGDOLL_SAMPLE_TIMES_MS\b|mod\._prepare_warlock_death\s*=\s*function\b).*?(?=\n\s*mod\._apply_warlock_child_materials\s*=|\z)'
    )
    $deathWithStrings = if ($deathWithStringsMatch.Success) { $deathWithStringsMatch.Value } else { $hooksWithStrings }

    # WR-RAG-001: custom outfit physics must never return. The source layout
    # check is duplicated in Test-WarlockPipeline so either entry point fails.
    if ($PhysxExists) {
        Add-WarlockPolicyViolation $violations 'WR-RAG-001' `
            'custom Warlock .physx scene is present' 'warlock_bombardier_3p.physx'
    }
    if ($stateMachineCode -match '(?m)^\s*ragdolls\s*=' -or
            $stateMachineCode -match 'state_type\s*=\s*["'']ragdoll["'']') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-001' `
            'custom state machine contains a ragdoll configuration/state'
    }
    if ($hooksTokens -match 'Unit\.(?:find_actor|actor)\s*\(\s*outfit_unit' -or
            $deathTokens -match 'Actor\.set_kinematic\s*\([^\r\n]*\bfalse\b') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-001' `
            'custom outfit participates in actor physics'
    }

    # WR-RAG-002: World.link_unit resets child local transforms. Independently
    # linking bones destroyed this Blender unit's hierarchy in v0.1.44.
    if ($hooksTokens -match 'World\.(?:link_unit|unlink_unit)\s*\(') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-002' `
            'death/runtime code directly links or unlinks Warlock scene nodes'
    }
    if ($InventoryText.Length -gt 0) {
        $rootBlock = [regex]::Match(
            $inventoryCode,
            '(?s)AttachmentNodeLinking\.doomrocket_warlock_root\s*=\s*\{(.*?)\n\s*\}'
        )
        $rootAssignment = $inventoryCode -match `
            'bombadier_curiass\.attachment_node_linking\s*=\s*AttachmentNodeLinking\.doomrocket_warlock_root'
        $targetCount = if ($rootBlock.Success) {
            [regex]::Matches($rootBlock.Groups[1].Value, '\btarget\s*=').Count
        } else { 0 }
        $correctRoot = $rootBlock.Success -and
            $rootBlock.Groups[1].Value -match '\btarget\s*=\s*0' -and
            $rootBlock.Groups[1].Value -match '\bsource\s*=\s*["'']root_point["'']' -and
            $targetCount -eq 1
        if (-not $rootAssignment -or -not $correctRoot) {
            Add-WarlockPolicyViolation $violations 'WR-RAG-002' `
                'Warlock outfit attachment is not the single root_point-only link'
        }
    }

    # WR-RAG-003: never transfer a carrier matrix/scale or source-local hips
    # position. The candidate calibrates in world space and maps the desired
    # world hips position through the inverse target-parent pose.
    if ($deathTokens -match 'Unit\.set_local_pose\s*\(') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-003' `
            'death handoff writes a full local pose (translation/scale stretch class)'
    }
    if ($deathTokens -match 'Unit\.set_local_scale\s*\(') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-003' `
            'death handoff writes outfit scale'
    }
    if ($deathTokens -match '(?s)Unit\.set_local_position\s*\(\s*outfit_unit.*?Unit\.local_position\s*\(\s*owner_unit') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-003' `
            'death handoff directly copies carrier-local translation'
    }

    # WR-RAG-004: disabling the outfit ASM made the skinned renderable vanish
    # in v0.1.48. Destruction/hiding is likewise forbidden in the death lane.
    if ($deathTokens -match 'disable_animation_state_machine\s*\(\s*outfit_unit') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-004' `
            'death handoff disables the custom outfit animation state machine'
    }
    if ($deathTokens -match 'set_unit_visibility\s*\(\s*outfit_unit\s*,\s*false' -or
            $deathTokens -match 'mark_for_deletion\s*\(\s*outfit_unit' -or
            $deathTokens -match '(?:World\.)?destroy_unit\s*\([^\r\n]*outfit_unit') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-004' `
            'death handoff hides or destroys the custom outfit'
    }

    # WR-RAG-005: the native ratling is a hidden physics carrier, never a
    # visual fallback. v0.1.49 intentionally revealed all 24 meshes.
    if ($hooksTokens -match '\bset_warlock_donor_mesh_visibility\b' -or
            $deathTokens -match 'Unit\.set_mesh_visibility\s*\(\s*(?:owner_unit|driver\.owner)\s*,[^\r\n]*\btrue\b') {
        Add-WarlockPolicyViolation $violations 'WR-RAG-005' `
            'death handoff can reveal native carrier meshes'
    }

    if ($RequireCandidateContract) {
        # WR-RAG-006: the current safe lane is evaluated after animation and
        # prevents the outfit ASM from overwriting the calibrated pose.
        if ($hooksTokens -notmatch 'Unit\.enable_animation_state_machine\s*\(\s*outfit_unit\s*\)' -or
                $deathWithStrings -notmatch 'Unit\.set_animation_bone_mode\s*\(\s*outfit_unit\s*,\s*["'']ignore["'']\s*\)') {
            Add-WarlockPolicyViolation $violations 'WR-RAG-006' `
                'candidate does not keep the outfit ASM enabled and hand death bones to ignore mode'
        }
        $callbackMatch = [regex]::Match(
            $hooksTokens,
            '(?s)animation_system\s*:\s*add_safe_animation_callback\s*\(\s*function\s*\([^\)]*\)(?<body>(?:(?!\bend\s*\)).)*)\bend\s*\)'
        )
        $callbackBody = if ($callbackMatch.Success) {
            $callbackMatch.Groups['body'].Value
        } else { '' }
        $queueCallCount = [regex]::Matches(
            $hooksTokens, '(?<!function\s)\bqueue_warlock_death_pose\s*\(\s*driver\s*\)'
        ).Count
        $hasOwnerWorldGate =
            $hooksTokens -match '(?:Unit\.world\s*\(\s*(?:driver\.)?owner(?:_unit)?\s*\)\s*==\s*world|world\s*==\s*Unit\.world\s*\(\s*(?:driver\.)?owner(?:_unit)?\s*\))'
        $hasWorldAnimationHooks =
            $hooksTokens -match 'mod\s*:\s*hook_safe\s*\(\s*World\s*,' -and
            $hooksWithStrings -match '["'']update_animations["'']' -and
            $hooksWithStrings -match '["'']update_animations_with_callback["'']'
        $hasOnceGuard =
            $hooksTokens -match 'driver\.callback_pending\s*=\s*true' -and
            $callbackBody -match 'driver\.callback_pending\s*=\s*false'
        $hasWorldGatedCallback =
            $hooksTokens -match '_warlock_active_death_drivers' -and
            $hasWorldAnimationHooks -and
            $hasOwnerWorldGate -and
            $hasOnceGuard -and
            $callbackBody -match 'apply_warlock_death_pose\s*\(\s*driver\s*\)' -and
            $callbackBody -notmatch 'queue_warlock_death_pose\s*\(' -and
            $queueCallCount -eq 1
        if (-not $hasWorldGatedCallback) {
            Add-WarlockPolicyViolation $violations 'WR-RAG-006' `
                'candidate lacks once-per-owner-world animation gating or self-requeues its safe callback'
        }

        # WR-RAG-007: audited row-vector matrix transfer. Source handoff/current
        # poses are rigid (scale-free); their delta is applied to the calibrated
        # target handoff world pose, then converted through inverse target-parent
        # world pose. Only rotation plus the hips translation are written.
        $hasRigidWorldCalibration =
            $deathTokens -match 'Matrix4x4\.from_quaternion_position\s*\(' -and
            $deathTokens -match 'Matrix4x4Box\s*\(' -and
            $deathTokens -match 'source_world_at_handoff' -and
            $deathTokens -match 'target_world_at_handoff'
        $hasCachedSourceInverse =
            $deathTokens -match '(?s)source_world_inverse_at_handoff\s*=\s*Matrix4x4Box\s*\(\s*Matrix4x4\.inverse\s*\(\s*source_world_at_handoff\s*\)\s*\)'
        $hasSourceDelta =
            ($deathTokens -match '(?s)source_delta\s*=\s*Matrix4x4\.multiply\s*\(\s*Matrix4x4\.inverse\s*\(\s*pair\.source_world_at_handoff.*?source_world\s*\)' -or
                ($hasCachedSourceInverse -and
                    $deathTokens -match '(?s)source_delta\s*=\s*Matrix4x4\.multiply\s*\(\s*pair\.source_world_inverse_at_handoff.*?source_world\s*\)')) -and
            $deathTokens -match '(?s)Matrix4x4\.multiply\s*\(\s*pair\.target_world_at_handoff.*?source_delta\s*\)'
        $localPositionWriteCount = [regex]::Matches(
            $deathTokens, 'Unit\.set_local_position\s*\('
        ).Count
        $hasInlineParentInverse =
            $deathTokens -match '(?s)desired_local\s*=\s*Matrix4x4\.multiply\s*\(\s*desired_worlds?\[?[^,]*,\s*Matrix4x4\.inverse\s*\(\s*parent_world\s*\)\s*\)'
        $hasCachedParentInverse =
            $deathTokens -match 'parent_inverse\s*=\s*Matrix4x4\.inverse\s*\(\s*parent_world\s*\)' -and
            $deathTokens -match '(?s)desired_local\s*=\s*Matrix4x4\.multiply\s*\(\s*desired_worlds?\[?[^,]*,\s*parent_inverse\s*\)'
        $hasInverseParentLocal =
            ($hasInlineParentInverse -or $hasCachedParentInverse) -and
            $deathTokens -match '(?s)Unit\.set_local_rotation\s*\([^\)]*Matrix4x4\.rotation\s*\(\s*desired_local\s*\)' -and
            $deathTokens -match '(?s)if\s+pair\.is_hips\s+then\s*Unit\.set_local_position\s*\([^\)]*Matrix4x4\.translation\s*\(\s*desired_local\s*\)' -and
            $localPositionWriteCount -eq 1
        if (-not $hasRigidWorldCalibration -or -not $hasSourceDelta -or -not $hasInverseParentLocal) {
            Add-WarlockPolicyViolation $violations 'WR-RAG-007' `
                'candidate lacks the rigid handoff-delta / inverse-parent local transfer'
        }

        # WR-RAG-008: every runtime format string must be correlatable. Looking
        # for one keyed line is insufficient: v0.1.49 had many unkeyed sample
        # records, and one newly keyed warning could otherwise mask them.
        $quotedStrings = [regex]::Matches(
            $hooksWithStrings,
            '(?s)(["''])(?:\\.|(?!\1).)*\1'
        ) | ForEach-Object { $_.Value }
        $ragdollFormats = @($quotedStrings | Where-Object { $_ -match '\[doomrocket:RAGDOLL\]' })
        $hasUnkeyedFormat = @($ragdollFormats | Where-Object {
                $_ -notmatch '\bphase=' -or $_ -notmatch '\bid=' -or $_ -notmatch '\bsource='
            }).Count -gt 0
        $hasCorePhases = @('begin', 'sample', 'stop') | ForEach-Object {
            $phase = $_
            @($ragdollFormats | Where-Object { $_ -match "\bphase=$phase\b" }).Count -gt 0
        }
        $sampleFormats = @($ragdollFormats | Where-Object { $_ -match '\bphase=sample\b' })
        $requiredSampleFields = @(
            'checkpoint_ms', 'elapsed_ms', 'wall_gap_ms', 'owner_alive', 'outfit_alive',
            'nodes', 'custom_actors', 'carrier_reveals', 'parent_mismatch', 'root_delta',
            'hips_delta', 'hips_drift', 'scale_mutations', 'nonhips_translation_mutations',
            'bounds_ratio', 'max_bone_radius_ratio'
        )
        $missingSampleFields = @($requiredSampleFields | Where-Object {
                $field = $_
                -not @($sampleFormats | Where-Object { $_ -match "\b$field=" }).Count
            })
        if ($ragdollFormats.Count -eq 0 -or $hasUnkeyedFormat -or
                $hasCorePhases -contains $false -or $missingSampleFields.Count -gt 0) {
            Add-WarlockPolicyViolation $violations 'WR-RAG-008' `
                'ragdoll formats lack correlation, core phases, or required sample diagnostics'
        }

        $hasCarrierMeshFallback =
            $hooksTokens -match '(?s)if\s+not\s+counted\s+or\s+not\s+num_meshes\s+or\s+num_meshes\s*<=\s*0\s+then\s*num_meshes\s*=\s*24'
        if ($hooksTokens -notmatch '(?:Unit\.set_mesh_visibility\s*\(\s*|pcall\s*\(\s*Unit\.set_mesh_visibility\s*,\s*)(?:owner_unit|unit|driver\.owner)\s*,[^\r\n]*\bfalse\b' -or
                -not $hasCarrierMeshFallback) {
            Add-WarlockPolicyViolation $violations 'WR-RAG-005' `
                'candidate does not hide every carrier mesh with the audited 24-mesh fallback'
        }
    }

    @($violations)
}
