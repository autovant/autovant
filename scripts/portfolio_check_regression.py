#!/usr/bin/env python3
"""Focused negative controls for portfolio-checker input boundaries."""

import json
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
        ]
        cases[1][1]["claims"][career_index]["text"] += " (changed)"
        cases[2][1]["claims"][career_index]["evidence"][0]["ref"] = "LICENSE.md"
        for label, manifest_data, evidence_text, expected in cases:
            if not run_case(label, manifest_data, evidence_text, expected):
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
