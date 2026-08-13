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
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 0
            ExpectedText = 'OK'
        }
        @{
            Name = 'incomplete trace without stop record'
            Log = 'missing_stop_fail.log'
            ExpectedExit = 1
            ExpectedText = 'missing stop record'
        }
        @{
            Name = 'trace with missing checkpoint'
            Log = 'checkpoint_gap_fail.log'
            ExpectedExit = 1
            ExpectedText = 'missing required checkpoint_ms value(s): 500'
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
            Name = 'v0.1.51 pre-monitor sleep freeze regression'
            Log = 'v0151_premonitor_sleep_freeze_fail.log'
            ExpectedExit = 1
            ExpectedText = 'hips_delta=0.533 m exceeds 0.25 m'
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

    # Runtime-schema mutations start from the passing v0.1.52 trace. Keeping
    # geometry and timing stable isolates counter/banner failures from the
    # historical deformation fixtures above.
    AnalyzerMutations = @(
        @{
            Name = 'pre-monitor sleep suppression'
            Source = 'structured_pass.log'
            Search = 'elapsed_ms=250 pose_writes=31 sleep_skips=0'
            Replace = 'elapsed_ms=250 pose_writes=31 sleep_skips=1'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'sleep_skips=1, expected 0 during the pre-monitor window'
        }
        @{
            Name = 'pose writes stalled between checkpoints'
            Source = 'structured_pass.log'
            Search = 'elapsed_ms=250 pose_writes=31 sleep_skips=0'
            Replace = 'elapsed_ms=250 pose_writes=13 sleep_skips=0'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'pose_writes=13 did not increase'
        }
        @{
            Name = 'callback completed without pose write'
            Source = 'structured_pass.log'
            Search = 'callbacks=601 pose_writes=601 sleep_skips=0'
            Replace = 'callbacks=601 pose_writes=600 sleep_skips=0'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'every pre-monitor callback must write the pose'
        }
        @{
            Name = 'sample pose counter omitted'
            Source = 'structured_pass.log'
            Search = 'elapsed_ms=250 pose_writes=31 sleep_skips=0'
            Replace = 'elapsed_ms=250 sleep_skips=0'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'sample missing pose_writes'
        }
        @{
            Name = 'sample sleep counter omitted'
            Source = 'structured_pass.log'
            Search = 'elapsed_ms=250 pose_writes=31 sleep_skips=0'
            Replace = 'elapsed_ms=250 pose_writes=31'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'sample missing sleep_skips'
        }
        @{
            Name = 'stop pose counter omitted'
            Source = 'structured_pass.log'
            Search = 'callbacks=601 pose_writes=601 sleep_skips=0'
            Replace = 'callbacks=601 sleep_skips=0'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'stop missing pose_writes'
        }
        @{
            Name = 'stop sleep counter omitted'
            Source = 'structured_pass.log'
            Search = 'callbacks=601 pose_writes=601 sleep_skips=0'
            Replace = 'callbacks=601 pose_writes=601'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'stop missing sleep_skips'
        }
        @{
            Name = 'stale build version banner'
            Source = 'structured_pass.log'
            Search = '[doomrocket:LOAD] v0.1.52-dev'
            Replace = '[doomrocket:LOAD] v0.1.51-dev'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'version banner mismatch: expected v0.1.52-dev, found v0.1.51-dev'
        }
        @{
            Name = 'missing build version banner'
            Source = 'structured_pass.log'
            Search = '[doomrocket:LOAD] v0.1.52-dev'
            Replace = '[unrelated:LOAD] v0.1.52-dev'
            Arguments = @('--expected-version', '0.1.52-dev')
            ExpectedExit = 1
            ExpectedText = 'expected [doomrocket:LOAD] v0.1.52-dev banner, found none'
        }
    )
}
