#!/usr/bin/env python3
"""Focused negative controls for portfolio-checker input boundaries."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


def fixture_directory(root: Path):
    return tempfile.TemporaryDirectory(
        prefix="portfolio-check-regression-",
        dir=root / ".portfolio",
    )


def check_collision_control() -> bool:
    with tempfile.TemporaryDirectory(prefix="autovant-portfolio-collision-") as temp_root:
        root = Path(temp_root)
        portfolio_dir = root / ".portfolio"
        docs_dir = root / "docs"
        portfolio_dir.mkdir()
        docs_dir.mkdir()
        legacy_manifest = portfolio_dir / ".portfolio-check-regression.json"
        legacy_evidence = docs_dir / ".portfolio-check-regression-evidence.md"
        manifest_bytes = b"preserve pre-existing manifest fixture\n"
        evidence_bytes = b"preserve pre-existing evidence fixture\n"
        legacy_manifest.write_bytes(manifest_bytes)
        legacy_evidence.write_bytes(evidence_bytes)

        with fixture_directory(root) as fixture_path:
            fixture = Path(fixture_path)
            (fixture / "manifest.json").write_bytes(b"owned fixture manifest\n")
            (fixture / "evidence.md").write_bytes(b"owned fixture evidence\n")

        if legacy_manifest.read_bytes() != manifest_bytes or legacy_evidence.read_bytes() != evidence_bytes:
            print("FAIL: temporary fixtures changed pre-existing fixed-path files")
            return False

    print("PASS: fixture collision leaves pre-existing files byte-identical")
    return True


def run_minimal_fixture(checker_source: Path, readme_text: str, include_agents: bool):
    with tempfile.TemporaryDirectory(prefix="autovant-portfolio-check-negative-") as temp_root:
        root = Path(temp_root)
        scripts_dir = root / "scripts"
        (root / ".portfolio").mkdir()
        scripts_dir.mkdir()
        checker = scripts_dir / "portfolio_check.py"
        shutil.copyfile(checker_source, checker)
        (root / ".portfolio/project.yaml").write_text("{}\n", encoding="utf-8")
        (root / "README.md").write_text(readme_text, encoding="utf-8")
        if include_agents:
            (root / "AGENTS.md").write_text("# Disposable checker fixture\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(checker)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )


def check_machine_path_controls(checker: Path) -> bool:
    for path_text in (
        "C:/Program Files/Synthetic/private-note.txt",
        r"C:\Program Files\Synthetic\private-note.txt",
    ):
        result = run_minimal_fixture(checker, f"# Fixture\n\n{path_text}\n", include_agents=True)
        output = result.stdout + result.stderr
        expected = "README.md: machine-specific absolute path found"
        if result.returncode != 1 or expected not in output or "Traceback" in output:
            print(f"FAIL: machine-specific path rejected: {path_text}")
            print(f"exit={result.returncode}\n{output}", end="")
            return False
        print(f"PASS: machine-specific path rejected: {path_text}")
    return True


def check_missing_agents_control(checker: Path) -> bool:
    result = run_minimal_fixture(checker, "# Fixture\n", include_agents=False)
    output = result.stdout + result.stderr
    expected = "AGENTS: file does not exist: AGENTS.md"
    if result.returncode != 1 or expected not in output or "Traceback" in output:
        print("FAIL: missing AGENTS.md was not rejected cleanly")
        print(f"exit={result.returncode}\n{output}", end="")
        return False
    print("PASS: missing AGENTS.md rejected without touching the author tree")
    return True


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.pop("GIT_OPTIONAL_LOCKS", None)
    return subprocess.run(
        ["git", "-c", "core.untrackedCache=false", "-C", str(root), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def make_index_fixture(root: Path, checker_source: Path) -> Path:
    (root / "scripts").mkdir(parents=True)
    (root / ".portfolio").mkdir()
    (root / "docs").mkdir()
    checker = root / "scripts/portfolio_check.py"
    shutil.copyfile(checker_source, checker)

    readme_text = "# Index probe fixture\n\nA synthetic fixture claim.\n"
    (root / "README.md").write_text(readme_text, encoding="utf-8")
    (root / "AGENTS.md").write_text("# Disposable checker fixture\n", encoding="utf-8")
    (root / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (root / "docs/demo.md").write_text("# Demo\n", encoding="utf-8")
    (root / "docs/evidence.md").write_text(
        "# Evidence ledger\n\n"
        "| Claim ID | Exact published claim | Status | Evidence references | Evidence and limit |\n"
        "|---|---|---|---|---|\n"
        "| index-fixture | A synthetic fixture claim. | partially_verified | README.md | Temporary fixture only. |\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "project": "Index probe fixture",
        "level": "supporting",
        "summary": "A disposable checker regression fixture.",
        "source_base": "origin/main@" + "0" * 40,
        "revision_scope": "Synthetic files only.",
        "supported_environment": {"runtime": "Python", "package_manager": "Not applicable"},
        "commands": {
            "run": None,
            "run_status": "No application runtime in this fixture.",
            "test": None,
            "test_status": "No application test suite in this fixture.",
            "demo": None,
            "demo_status": "No runnable demo in this fixture.",
            "demo_instructions": "docs/demo.md",
        },
        "readme_sections": [],
        "architecture": "docs/architecture.md",
        "evidence": "docs/evidence.md",
        "demo": "docs/demo.md",
        "claims": [
            {
                "id": "index-fixture",
                "text": "A synthetic fixture claim.",
                "status": "partially_verified",
                "evidence": [
                    {"ref": "README.md", "class": "secondary", "scope": "Disposable fixture."}
                ],
                "proof_limit": "Temporary checker fixture only.",
            }
        ],
        "limitations": ["Temporary checker fixture only."],
    }
    manifest_path = root / ".portfolio/project.yaml"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for args in (
        ("init", "--quiet"),
        ("config", "user.name", "Portfolio checker regression"),
        ("config", "user.email", "portfolio-check@example.invalid"),
        ("add", "--all"),
        ("commit", "--quiet", "-m", "initial index fixture"),
    ):
        result = run_git(root, *args)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    base_commit = run_git(root, "rev-parse", "HEAD").stdout.strip()
    manifest["source_base"] = f"origin/main@{base_commit}"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for args in (
        ("add", ".portfolio/project.yaml"),
        ("commit", "--quiet", "-m", "bind index fixture source"),
    ):
        result = run_git(root, *args)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)

    os.utime(root / "README.md", (946684800, 946684800))
    return checker


def index_hash(root: Path) -> str:
    return hashlib.sha256((root / ".git/index").read_bytes()).hexdigest()


def check_read_only_git_control(checker_source: Path) -> bool:
    try:
        with tempfile.TemporaryDirectory(prefix="autovant-portfolio-index-probe-") as temp_root:
            root = Path(temp_root)
            control = root / "control"
            candidate = root / "candidate"
            control.mkdir()
            candidate.mkdir()
            checker = make_index_fixture(candidate, checker_source)
            make_index_fixture(control, checker_source)

            control_before = index_hash(control)
            control_result = run_git(control, "status", "--porcelain")
            control_after = index_hash(control)
            if control_result.returncode or control_before == control_after:
                print("FAIL: stale-stat control did not demonstrate an optional index refresh")
                print(control_result.stdout + control_result.stderr, end="")
                return False

            candidate_before = index_hash(candidate)
            env = os.environ.copy()
            env.pop("GIT_OPTIONAL_LOCKS", None)
            result = subprocess.run(
                [sys.executable, str(checker)],
                cwd=candidate,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            output = result.stdout + result.stderr
            candidate_after = index_hash(candidate)
            if (
                result.returncode != 0
                or "PORTFOLIO CHECK: READY WITH WARNINGS" not in output
                or "Traceback" in output
                or candidate_before != candidate_after
                or (candidate / "README.md").read_text(encoding="utf-8")
                != "# Index probe fixture\n\nA synthetic fixture claim.\n"
            ):
                print("FAIL: default checker refreshed the index or failed its disposable fixture")
                print(f"exit={result.returncode}\nindex_before={candidate_before}\nindex_after={candidate_after}\n{output}")
                return False
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: read-only Git index fixture: {exc}")
        return False

    print(
        "PASS: default checker preserves stale-stat index "
        f"{candidate_before[:12]} (plain git status refreshed {control_before[:12]} to {control_after[:12]})"
    )
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checker = Path(__file__).with_name("portfolio_check.py")
    with tempfile.TemporaryDirectory(prefix="portfolio-check-") as temp_dir:
        manifest = Path(temp_dir) / "external-manifest.json"
        manifest.write_text(json.dumps({}), encoding="utf-8")
        try:
            manifest.resolve().relative_to(root)
        except ValueError:
            pass
        else:
            print("FAIL: regression manifest is not outside the repository")
            return 1

        result = subprocess.run(
            [sys.executable, str(checker), "--manifest", str(manifest)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = result.stdout + result.stderr
        if (
            result.returncode != 1
            or "manifest path must be inside the repository" not in output
            or "Traceback" in output
        ):
            print("FAIL: external manifest was not rejected cleanly")
            print(output, end="")
            return 1
        print("PASS: external manifest rejected with exit 1 and no traceback")

    if not check_collision_control():
        return 1
    if not check_machine_path_controls(checker):
        return 1
    if not check_missing_agents_control(checker):
        return 1
    if not check_read_only_git_control(checker):
        return 1

    manifest_source = json.loads((root / ".portfolio/project.yaml").read_text(encoding="utf-8"))
    evidence_source = (root / manifest_source["evidence"]).read_text(encoding="utf-8")
    claim_id = "autovant-career-impact"

    def change_ledger_cell(text: str, column: int, value: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith(f"| {claim_id} |"):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                cells[column] = value
                lines[index] = "| " + " | ".join(cells) + " |"
                return "\n".join(lines) + "\n"
        raise ValueError(f"missing ledger row: {claim_id}")

    with fixture_directory(root) as fixture_path:
        fixture = Path(fixture_path)
        temp_manifest = fixture / "manifest.json"
        temp_evidence = fixture / "evidence.md"
        evidence_ref = temp_evidence.relative_to(root).as_posix()

        malformed = deepcopy(manifest_source)
        malformed["schema_version"] = True
        temp_manifest.write_text(json.dumps(malformed), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(checker), "--manifest", str(temp_manifest)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = result.stdout + result.stderr
        if result.returncode != 1 or "schema_version must be 1" not in output or "Traceback" in output:
            print("FAIL: boolean schema_version was not rejected")
            print(f"exit={result.returncode}\n{output}", end="")
            return 1
        print("PASS: boolean schema_version rejected")

        def run_case(label: str, manifest_data: dict, evidence_text: str, expected: str) -> bool:
            manifest_data["evidence"] = evidence_ref
            temp_manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
            temp_evidence.write_text(evidence_text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(checker), "--manifest", str(temp_manifest)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            output = result.stdout + result.stderr
            if result.returncode != 1 or expected not in output or "Traceback" in output:
                print(f"FAIL: {label}")
                print(f"exit={result.returncode}\n{output}", end="")
                return False
            print(f"PASS: {label}")
            return True

        career_index = next(i for i, claim in enumerate(manifest_source["claims"]) if claim["id"] == claim_id)
        cases = [
            (
                "same-row status mismatch rejected",
                deepcopy(manifest_source),
                change_ledger_cell(evidence_source, 2, "verified"),
                f"{claim_id}: evidence ledger status does not match the manifest",
            ),
            (
                "same-row exact-text mismatch rejected",
                deepcopy(manifest_source),
                evidence_source,
                f"{claim_id}: evidence ledger claim text does not match the manifest",
            ),
            (
                "same-row evidence-reference mismatch rejected",
                deepcopy(manifest_source),
                evidence_source,
                f"{claim_id}: evidence ledger references do not match the manifest",
            ),
            (
                "undeclared ledger claim ID rejected",
                deepcopy(manifest_source),
                evidence_source.rstrip()
                + "\n| undeclared-ledger-claim | Synthetic undeclared claim. | partially_verified | README.md | Regression fixture only. |\n",
                "undeclared-ledger-claim: evidence ledger claim ID is not declared in the manifest",
            ),
            (
                "duplicate declared claim ID rejected",
                deepcopy(manifest_source),
                evidence_source,
                f"duplicate claim id: {claim_id}",
            ),
        ]
        cases[1][1]["claims"][career_index]["text"] += " (changed)"
        cases[2][1]["claims"][career_index]["evidence"][0]["ref"] = "LICENSE.md"
        cases[4][1]["claims"].append(deepcopy(cases[4][1]["claims"][career_index]))
        for label, manifest_data, evidence_text, expected in cases:
            if not run_case(label, manifest_data, evidence_text, expected):
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
