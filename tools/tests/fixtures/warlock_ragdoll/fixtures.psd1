@{
    Cases = @(
        @{
            Name = 'custom PhysX solver explosion'
            Hooks = 'custom_physx.lua.fixture.txt'
            # The .fixture.txt suffix is intentional. VMB scans the whole mod
            # root and would compile a literal .state_machine test mutation.
            StateMachine = 'custom_physx.state_machine.fixture.txt'
            PhysxExists = $true
            ExpectedRules = @('WR-RAG-001')
        }
        @{
            Name = 'per-bone scene-link stick figure'
            Hooks = 'per_bone_scene_link.lua.fixture.txt'
            ExpectedRules = @('WR-RAG-002')
        }
        @{
            Name = 'full-pose and scale sky stretch'
            Hooks = 'full_pose_copy.lua.fixture.txt'
            ExpectedRules = @('WR-RAG-003')
        }
        @{
            Name = 'v0.1.48 outfit disappearance'
            Hooks = 'outfit_asm_disabled.lua.fixture.txt'
            ExpectedRules = @('WR-RAG-004')
        }
        @{
            Name = 'v0.1.49 native carrier corpse substitution'
            Hooks = 'carrier_underlay.lua.fixture.txt'
            ExpectedRules = @('WR-RAG-005')
        }
        @{
            Name = 'forbidden API names in comments and strings only'
            Hooks = 'comments_are_not_code.lua.fixture.txt'
            ExpectedRules = @()
        }
    )

    CandidateContract = 'candidate_contract_pass.lua.fixture.txt'

    AnalyzerCases = @(
        @{
            Name = 'structured five-second stable trace'
            Log = 'structured_pass.log'
            ExpectedExit = 0
            ExpectedText = 'OK'
        }
        @{
            Name = 'solver freeze telemetry'
            Log = 'fps_collapse_fail.log'
            ExpectedExit = 1
            ExpectedText = 'wall_gap_ms=1000 exceeds 250 ms'
        }
        @{
            Name = 'scene-parent mismatch telemetry'
            Log = 'stick_figure_fail.log'
            ExpectedExit = 1
            ExpectedText = 'parent_mismatch=1, expected 0'
        }
        @{
            Name = 'sky-stretch telemetry'
            Log = 'sky_stretch_fail.log'
            ExpectedExit = 1
            ExpectedText = 'hips_drift=0.251 m exceeds 0.25 m'
        }
        @{
            Name = 'outfit disappearance telemetry'
            Log = 'disappearance_fail.log'
            ExpectedExit = 1
            ExpectedText = 'custom corpse disappeared'
        }
        @{
            Name = 'native carrier substitution telemetry'
            Log = 'carrier_substitution_fail.log'
            ExpectedExit = 1
            ExpectedText = 'carrier_visible=true'
        }
        @{
            Name = 'id/source collision telemetry'
            Log = 'id_source_collision_fail.log'
            ExpectedExit = 1
            ExpectedText = 'changed source'
        }
        @{
            Name = 'v0.1.49 legacy uncorrelated telemetry'
            Log = 'v0149_legacy_fail.log'
            ExpectedExit = 1
            ExpectedText = 'telemetry missing phase, id'
        }
    )
}
