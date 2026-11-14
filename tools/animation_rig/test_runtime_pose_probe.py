"""Bounded compatibility staging guards; these do not exercise engine playback."""
import unittest
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from runtime_pose_probe import compatibility_timeline


class CompatibilityStagingGuards(unittest.TestCase):
    def clip(self,name,rate,count=1600):
        return {'clip':name,'sample_fps':rate,'independent_roundtrip':{'sample_count':count}}
    def test_final_960_death_plan(self):
        rate,count=compatibility_timeline(self.clip('death_shot.fbx',960))
        self.assertEqual(rate,960)
        self.assertAlmostEqual((count-1)/rate,1.665625)
    def test_final_240_ordinary_plan(self):
        self.assertEqual(compatibility_timeline(self.clip('combat_idle.fbx',240)),(240,1600))
    def test_more_than_fourfold_rate_rejected(self):
        for name,rate in [('combat_idle.fbx',480),('death_shot.fbx',1920),('stagger_fwd.fbx',720)]:
            with self.assertRaises(ValueError): compatibility_timeline(self.clip(name,rate))
    def test_unbounded_or_boolean_count_rejected(self):
        for count in (10001,True,1):
            with self.assertRaises(ValueError): compatibility_timeline(self.clip('death_shot.fbx',960,count))


@unittest.skipUnless(os.name == 'nt', 'The native SDK runner is Windows-only')
class RuntimeToolchainGuards(unittest.TestCase):
    """Execute the actual PowerShell functions, without starting any SDK process."""
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        temporary_root = root / '.build' / 'runtime_toolchain_guard_tests'
        temporary_root.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix='owned-', dir=temporary_root)
        cls.addClassCleanup(cls.temporary.cleanup)
        probe = Path(cls.temporary.name)
        runner = Path(__file__).with_name('Invoke-AnimationRuntimeProbe.ps1')
        def literal(value):
            return "'" + str(value).replace("'", "''") + "'"
        script = probe / 'guards.ps1'
        script.write_text("\n".join([
            "$ErrorActionPreference='Stop'; Set-StrictMode -Version Latest",
            f"$repoRoot={literal(root)}; $PythonExecutable={literal(sys.executable)}; $pythonPrefix=@()",
            f"$guard={literal(root/'tools/hose_lab/compile_paths.py')}",
            f"$probe={literal(probe)}; $lane=Join-Path $probe 'candidate'",
            "$null=New-Item -ItemType Directory -Path (Join-Path $lane 'source') -Force",
            "$tokens=$null; $errors=$null",
            f"$ast=[Management.Automation.Language.Parser]::ParseFile({literal(runner)},[ref]$tokens,[ref]$errors)",
            "if($errors.Count){throw 'Runner failed PowerShell parse'}",
            "$wanted=@('Resolve-RepoPath','Assert-ProbePaths','Quote-ProcessArgument','Assert-NativeRuntimeRoute','New-OwnedRuntimeToolchain','Get-NativeRuntimeArguments')",
            "$functions=$ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -in $wanted},$true)",
            "if($functions.Count -ne $wanted.Count){throw 'Missing actual runner function'}",
            "foreach($function in $functions){Invoke-Expression $function.Extent.Text}",
            "$known='721bc354a520510ea270147c57230c87cc7e07d93f78ca1a0763d5bdb74137de'; $other='f'*64",
            "$results=[ordered]@{}",
            "try{Assert-NativeRuntimeRoute $known $false $false; $results.known_legacy_rejected=$false}catch{$results.known_legacy_rejected=$true}",
            "Assert-NativeRuntimeRoute $known $true $false; $results.compile_only_allowed=$true",
            "Assert-NativeRuntimeRoute $known $false $true; $results.exact_optin_allowed=$true",
            "try{Assert-NativeRuntimeRoute $other $false $true; $results.unknown_optin_rejected=$false}catch{$results.unknown_optin_rejected=$true}",
            "Assert-NativeRuntimeRoute $other $false $false; $results.other_legacy_unchanged=$true",
            "try{Assert-NativeRuntimeRoute $known $true $true; $results.compile_only_optin_rejected=$false}catch{$results.compile_only_optin_rejected=$true}",
            "$route=New-OwnedRuntimeToolchain $probe $lane 'C:\\Approved SDK'",
            "$bytes=[IO.File]::ReadAllBytes($route.config); $json=[IO.File]::ReadAllText($route.config)|ConvertFrom-Json",
            "$results.owned_bomfree_config=($bytes[0] -eq 123 -and $json.ProjectIndex -eq 0 -and @($json.Projects).Count -eq 1 -and $json.Projects[0].SourceDirectory -eq (Join-Path $lane 'source') -and $route.config_sha256 -ceq (Get-FileHash -LiteralPath $route.config -Algorithm SHA256).Hash.ToLowerInvariant())",
            "$args=@(Get-NativeRuntimeArguments $lane (Join-Path $lane 'data') $route)",
            "$results.headless_order=($args[0] -ceq '--suppress-messagebox' -and $args[1] -ceq '--no-rendering' -and $args[2] -ceq '--disable-default-window' -and $args[3] -ceq '--toolchain' -and $args[5] -ceq '--no-compile')",
            "try{New-OwnedRuntimeToolchain $probe $repoRoot 'C:\\Approved SDK'; $results.outside_probe_rejected=$false}catch{$results.outside_probe_rejected=$true}",
            "try{Quote-ProcessArgument ('bad'+[char]34+'path');$results.quote_rejected=$false}catch{$results.quote_rejected=$true}",
            "$results|ConvertTo-Json -Compress",
        ]) + "\n", encoding='utf-8')
        environment = os.environ.copy()
        # A PS 7 parent can supply only its own module path to Windows PS 5.
        # Add the compatible built-in modules in this test child only.
        windows_modules = str(Path(os.environ.get('WINDIR', r'C:\Windows')) /
                              'System32/WindowsPowerShell/v1.0/Modules')
        inherited_modules = environment.get('PSModulePath', '')
        if windows_modules.casefold() not in inherited_modules.casefold().split(';'):
            environment['PSModulePath'] = inherited_modules + (';' if inherited_modules else '') + windows_modules
        completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, env=environment)
        if completed.returncode:
            raise RuntimeError(completed.stdout + completed.stderr)
        cls.results = json.loads(completed.stdout)

    def test_failed_legacy_route_remains_guarded(self):
        self.assertTrue(self.results['known_legacy_rejected'])
    def test_compile_only_remains_available(self):
        self.assertTrue(self.results['compile_only_allowed'])
    def test_optin_requires_exact_audited_signature(self):
        self.assertTrue(self.results['exact_optin_allowed'])
        self.assertTrue(self.results['unknown_optin_rejected'])
    def test_compile_only_cannot_masquerade_as_runtime_optin(self):
        self.assertTrue(self.results['compile_only_optin_rejected'])
    def test_unrelated_sdk_guard_behavior_is_unchanged(self):
        self.assertTrue(self.results['other_legacy_unchanged'])
    def test_owned_config_has_a_content_fingerprint_and_no_bom(self):
        self.assertTrue(self.results['owned_bomfree_config'])
    def test_suppression_and_window_flags_precede_config_parsing(self):
        self.assertTrue(self.results['headless_order'])
    def test_path_escape_and_quoted_arguments_are_rejected(self):
        self.assertTrue(self.results['outside_probe_rejected'])
        self.assertTrue(self.results['quote_rejected'])


if __name__=='__main__':
    unittest.main()
