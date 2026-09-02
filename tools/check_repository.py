#!/usr/bin/env python3
"""Fast repository checks that do not require the VT2 SDK or compiled bundles."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def cfg_value(text: str, key: str) -> str:
    match = re.search(
        rf'^\s*{re.escape(key)}\s*=\s*(?:"([^"]*)"|(\d+)L?)\s*;',
        text,
        re.MULTILINE,
    )
    if not match:
        raise ValueError(f"itemV2.cfg is missing {key!r}")
    return match.group(1) if match.group(1) is not None else match.group(2)


def loaded_version() -> str:
    match = re.search(
        r'local\s+MOD_VERSION\s*=\s*"([^"]+)"',
        read("scripts/mods/doomrocket/doomrocket.lua"),
    )
    if not match:
        raise ValueError("doomrocket.lua is missing the MOD_VERSION constant")
    return match.group(1)


def tracked_generated_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "bundleV2", ".build", "*.mod_bundle", "*.processed"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def check_issue_forms(failures: list[str], version: str) -> None:
    template_dir = ROOT / ".github" / "ISSUE_TEMPLATE"
    config_path = template_dir / "config.yml"
    if not config_path.is_file():
        failures.append("missing issue chooser config.yml")
        return
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config.get("blank_issues_enabled") is not False:
        failures.append("development reports must use structured forms, not blank issues")

    expected = {
        "bug_report.yml": "Development gameplay or presentation bug",
        "crash_report.yml": "Development crash report",
        "feedback.yml": "Development balance or design feedback",
    }
    for filename, expected_name in expected.items():
        path = template_dir / filename
        if not path.is_file():
            failures.append(f"missing development issue form: {filename}")
            continue
        source = path.read_text(encoding="utf-8")
        form = yaml.safe_load(source)
        if form.get("name") != expected_name:
            failures.append(f"{filename}: unexpected chooser name")
        if not form.get("description") or not isinstance(form.get("body"), list):
            failures.append(f"{filename}: name, description, and body are required")
            continue
        ids = [entry.get("id") for entry in form["body"] if entry.get("id")]
        if len(ids) != len(set(ids)):
            failures.append(f"{filename}: field ids must be unique")
        if filename in {"bug_report.yml", "crash_report.yml"}:
            uploads = [entry for entry in form["body"] if entry.get("type") == "upload"]
            log_uploads = [
                entry
                for entry in uploads
                if ".log" in entry.get("validations", {}).get("accept", "")
            ]
            if not log_uploads:
                failures.append(f"{filename}: must explicitly accept a .log upload")
            elif log_uploads[0].get("validations", {}).get("required") is not True:
                failures.append(f"{filename}: console log upload must be required")
            if f"v{version}" not in source:
                failures.append(f"{filename}: loaded-banner guidance must name v{version}")


def check_local_vmb_target(failures: list[str]) -> None:
    junction = ROOT.parent / "_doomrocket_vmb" / "doomrocket"
    if junction.exists() and junction.resolve() != ROOT.resolve():
        failures.append(
            "local VMB project junction does not resolve to this development worktree"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", choices=("development",), required=True)
    parser.parse_args()

    failures: list[str] = []
    try:
        cfg = read("itemV2.cfg")
        version = loaded_version()
        title = cfg_value(cfg, "title")
        workshop_id = cfg_value(cfg, "published_id")
        visibility = cfg_value(cfg, "visibility")
        preview = cfg_value(cfg, "preview")
    except (OSError, ValueError) as exc:
        print(f"[repository-check] FAIL - {exc}")
        return 1

    if title != "Warprocket Bombardier TEST v" + version:
        failures.append("Workshop title and Lua MOD_VERSION are out of sync")
    if workshop_id != "3794172730":
        failures.append("development channel must target Workshop item 3794172730")
    if visibility != "public":
        failures.append("development Workshop item must remain public")
    if preview != "item_preview_test.png":
        failures.append("development channel must use item_preview_test.png")
    if not version.endswith("-dev"):
        failures.append("development version must use the -dev suffix")

    for required in (
        "DEVELOPMENT TEST BUILD",
        "unstable development version",
        "Do not enable it together with the public",
        "1369573612",
        "Modded Realm",
        "doomrocket-private/issues/new/choose",
        f"[doomrocket:LOAD] v{version}",
    ):
        if required not in cfg:
            failures.append(f"development Workshop description is missing: {required}")

    for required_file in (
        "AGENTS.md",
        "README.md",
        "PROJECT_STATUS.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "docs/BUG_REPORTING.md",
        "docs/RELEASE_CHANNELS.md",
        "docs/TESTER_QUICKSTART.md",
        "tools/Invoke-DoomrocketRelease.ps1",
    ):
        if not (ROOT / required_file).is_file():
            failures.append(f"missing development guidance: {required_file}")

    check_issue_forms(failures, version)
    check_local_vmb_target(failures)

    generated = tracked_generated_files()
    if generated:
        failures.append("generated/game-derived files are tracked: " + ", ".join(generated))

    if failures:
        print("[repository-check] FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"[repository-check] OK - development v{version}, Workshop {workshop_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
