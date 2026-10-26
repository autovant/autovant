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

    readme_text = "## Fixture section\n\nA synthetic fixture claim.\n"
    (root / "README.md").write_text(readme_text, encoding="utf-8")
    (root / "AGENTS.md").write_text("# Disposable checker fixture\n", encoding="utf-8")
    (root / "docs/architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (root / "docs/demo.md").write_text("# Demo\n", encoding="utf-8")
    (root / "docs/evidence.md").write_text(
        "# Evidence ledger\n\n"
        "| Claim ID | Exact published claim | Status | Evidence references | Evidence and limit |\n"
        "|---|---|---|---|---|\n"
        "| index-fixture | A synthetic fixture claim. | partially_verified | README.md | Temporary fixture only. Proof limit: Temporary checker fixture only. |\n",
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
        "readme_sections": ["Fixture section"],
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
                != "## Fixture section\n\nA synthetic fixture claim.\n"
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


def check_readme_section_controls(checker_source: Path) -> bool:
    cases = (
        (
            "visible H2 README section accepted",
            "## Fixture section\n",
            ["Fixture section"],
            None,
        ),
        (
            "fenced README heading cannot satisfy a required section",
            "```markdown\n## Fixture section\n```\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "list-item fenced README heading cannot satisfy a required section",
            "- ```markdown\n  ## Fixture section\n  ```\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "ordered-list nested fenced README heading cannot satisfy a required section",
            "1. ~~~markdown\n   ## Fixture section\n   ~~~\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "commented README heading cannot satisfy a required section",
            "<!--\n## Fixture section\n-->\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "same-line HTML comment heading cannot satisfy a required section",
            "<!-- ## Fixture section -->\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "raw HTML block heading cannot satisfy a required section",
            "<div hidden>\n## Fixture section\n</div>\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "pre-block README heading cannot satisfy a required section",
            "<pre>\n\n## Fixture section\n</pre>\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "script-block README heading cannot satisfy a required section",
            "<script>\n\n## Fixture section\n</script>\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "style-block README heading cannot satisfy a required section",
            "<style>\n\n## Fixture section\n</style>\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "textarea-block README heading cannot satisfy a required section",
            "<textarea>\n\n## Fixture section\n</textarea>\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "standalone type-7 picture block heading cannot satisfy a required section",
            "<picture>\n## Fixture section\n\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "visible H2 after a closed pre block is accepted",
            "<pre>\nexample\n</pre>\n## Fixture section\n",
            ["Fixture section"],
            None,
        ),
        (
            "visible H2 after a closed textarea block is accepted",
            "<textarea>\nexample\n</textarea>\n## Fixture section\n",
            ["Fixture section"],
            None,
        ),
        (
            "visible H2 after a type-7 blank-line terminator is accepted",
            "<picture>\n## Hidden fixture title\n\n## Fixture section\n",
            ["Fixture section"],
            None,
        ),
        (
            "H3 README heading cannot satisfy a required H2 section",
            "### Fixture section\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "unspaced closing hashes cannot alter a required H2 title",
            "## Fixture section###\n",
            ["Fixture section"],
            "README missing required section: Fixture section",
        ),
        (
            "empty README section list is rejected",
            "## Fixture section\n",
            [],
            "readme_sections must be a non-empty list",
        ),
    )
    all_passed = True
    try:
        for label, readme_text, sections, expected_error in cases:
            with tempfile.TemporaryDirectory(prefix="autovant-readme-sections-") as temp_root:
                root = Path(temp_root)
                checker = make_index_fixture(root, checker_source)
                manifest_path = root / ".portfolio/project.yaml"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["readme_sections"] = sections
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                (root / "README.md").write_text(readme_text, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(checker)],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                output = result.stdout + result.stderr
                if expected_error is None:
                    valid = result.returncode == 0 and "PORTFOLIO CHECK: READY" in output
                else:
                    valid = result.returncode == 1 and expected_error in output
                if not valid or "Traceback" in output:
                    print(f"FAIL: {label}")
                    print(f"exit={result.returncode}\n{output}", end="")
                    all_passed = False
                else:
                    print(f"PASS: {label}")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: README section fixture: {exc}")
        return False
    return all_passed


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
    if not check_readme_section_controls(checker):
        return 1

    manifest_source = json.loads((root / ".portfolio/project.yaml").read_text(encoding="utf-8"))
    evidence_source = (root / manifest_source["evidence"]).read_text(encoding="utf-8")
    claim_id = "autovant-career-impact"

    def ledger_cells(line: str) -> list[str]:
        text = line.strip()
        if text.startswith("|"):
            text = text[1:]
        if text.endswith("|"):
            text = text[:-1]
        cells: list[str] = []
        cell: list[str] = []
        escaped = False
        for character in text:
            if character == "|" and not escaped:
                cells.append("".join(cell).strip().replace("\\|", "|"))
                cell = []
            else:
                cell.append(character)
            escaped = character == "\\" and not escaped
        cells.append("".join(cell).strip().replace("\\|", "|"))
        return cells

    def change_ledger_cells(
        text: str,
        changes: dict[int, str],
        target_id: str = claim_id,
    ) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if ledger_cells(line)[0] == target_id:
                cells = ledger_cells(line)
                for column, value in changes.items():
                    cells[column] = value
                lines[index] = "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"
                return "\n".join(lines) + "\n"
        raise ValueError(f"missing ledger row: {target_id}")

    def change_ledger_cell(
        text: str,
        column: int,
        value: str,
        target_id: str = claim_id,
    ) -> str:
        return change_ledger_cells(text, {column: value}, target_id)

    def check_prominent_readme_claim_ids() -> bool:
        expected = {
            "autovant-graphforge-capabilities":
                "Visually author, run, inspect and export stateful LangGraph workflows.",
            "autovant-graphforge-human-interrupt":
                "GraphForge: a real LangGraph run paused at a human-review gate, with the reviewer editing the dispatch note before resuming.",
            "autovant-relay-workflow":
                "local Windows dictation and meeting notes, with on-device speech recognition first and cloud cleanup only when allowed.",
            "autovant-enterprise-automation-workflows":
                "Blue Prism artifact review and release building, no-admin OCR, and document extraction that routes low-confidence documents to a person.",
        }
        readme_text = (root / "README.md").read_text(encoding="utf-8")
        claims_by_id = {
            claim.get("id"): claim
            for claim in manifest_source["claims"]
            if isinstance(claim, dict)
        }
        missing = [
            claim_id
            for claim_id, text in expected.items()
            if text not in readme_text
            or claim_id not in claims_by_id
            or claims_by_id[claim_id].get("text") != text
            or claims_by_id[claim_id].get("status") != "partially_verified"
        ]
        if missing:
            print(
                "FAIL: prominent README behavior claims need stable, partially verified IDs: "
                + ", ".join(missing)
            )
            return False
        print("PASS: prominent README behavior claims have stable, partially verified IDs")
        return True

    def find_ledger_row(text: str, target_id: str) -> str:
        for line in text.splitlines():
            cells = ledger_cells(line)
            if len(cells) == 5 and cells[0] == target_id:
                return line
        raise ValueError(f"missing ledger row: {target_id}")

    def insert_ledger_row(text: str, after_id: str, row: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            cells = ledger_cells(line)
            if len(cells) == 5 and cells[0] == after_id:
                lines.insert(index + 1, row)
                return "\n".join(lines) + "\n"
        raise ValueError(f"missing ledger row: {after_id}")

    def insert_ledger_rows_after(text: str, after_id: str, rows: list[str]) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            cells = ledger_cells(line)
            if len(cells) == 5 and cells[0] == after_id:
                lines[index + 1:index + 1] = rows
                return "\n".join(lines) + "\n"
        raise ValueError(f"missing ledger row: {after_id}")

    def remove_ledger_row(text: str, target_id: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            cells = ledger_cells(line)
            if len(cells) == 5 and cells[0] == target_id:
                del lines[index]
                return "\n".join(lines) + "\n"
        raise ValueError(f"missing ledger row: {target_id}")

    def remove_outer_pipes_from_ledger(text: str) -> str:
        lines = text.splitlines()
        in_ledger = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not in_ledger:
                cells = ledger_cells(line)
                if len(cells) == 5 and cells[0] == "Claim ID":
                    in_ledger = True
            if in_ledger:
                if not stripped or "|" not in stripped:
                    break
                lines[index] = stripped.strip("|").strip()
        return "\n".join(lines) + "\n"

    readme_claim_coverage_passed = check_prominent_readme_claim_ids()

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

        def run_case(
            label: str,
            manifest_data: dict,
            evidence_text: str,
            expected: str | tuple[str, ...] | None,
            forbidden: tuple[str, ...] = (),
        ) -> bool:
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
            if expected is None:
                valid = (
                    result.returncode == 0
                    and f"WARNING: {claim_id}: status is partially_verified" in output
                )
            else:
                expected_messages = expected if isinstance(expected, tuple) else (expected,)
                valid = result.returncode == 1 and all(message in output for message in expected_messages)
            if not valid or any(marker in output for marker in forbidden) or "Traceback" in output:
                print(f"FAIL: {label}")
                print(f"exit={result.returncode}\n{output}", end="")
                return False
            print(f"PASS: {label}")
            return True

        career_index = next(i for i, claim in enumerate(manifest_source["claims"]) if claim["id"] == claim_id)
        graphforge_claim_id = "autovant-graphforge-tests"
        graphforge_claim_index = next(
            i for i, claim in enumerate(manifest_source["claims"])
            if claim["id"] == graphforge_claim_id
        )
        target_row = find_ledger_row(evidence_source, claim_id)
        unwrapped_target_row = target_row.strip().strip("|").strip()
        unknown_claim_row = (
            "undeclared-ledger-claim | Synthetic undeclared claim. | partially_verified "
            "| README.md | Regression fixture only."
        )
        missing_claim_evidence = remove_ledger_row(evidence_source, claim_id)
        fenced_substitute = (
            missing_claim_evidence.rstrip()
            + f"\n\n```markdown\n{target_row}\n```\n"
        )
        unrelated_substitute = (
            missing_claim_evidence.rstrip()
            + "\n\n## Unrelated fixture table\n\n"
            + "| Claim ID | Example claim | Status | References | Limit |\n"
            + "| --- | --- | --- | --- | --- |\n"
            + target_row
            + "\n"
        )
        ledger_header_row = next(line for line in evidence_source.splitlines() if line.startswith("| Claim ID |"))
        ledger_table_lines: list[str] = []
        in_ledger_table = False
        for line in evidence_source.splitlines():
            if not in_ledger_table and line == ledger_header_row:
                in_ledger_table = True
            if in_ledger_table:
                if not line.strip() or "|" not in line:
                    break
                ledger_table_lines.append(line)
        empty_canonical_ledger = evidence_source
        for claim in manifest_source["claims"]:
            empty_canonical_ledger = remove_ledger_row(empty_canonical_ledger, claim["id"])
        exact_header_decoy = (
            "# Unrelated fixture examples\n\n"
            + "\n".join(ledger_table_lines) + "\n\n"
            + empty_canonical_ledger
        )
        commented_ledger_decoy = (
            "<!--\n# Evidence ledger\n\n"
            + "\n".join(ledger_table_lines)
            + "\n-->\n"
        )
        same_line_commented_ledger_decoy = (
            "<!-- hidden --># Evidence ledger\n\n"
            + "\n".join(ledger_table_lines)
            + "\n"
        )
        unmatched_backtick_comment_decoy = "`\n" + commented_ledger_decoy
        escaped_backtick_comment_decoy = (
            "\\`<!-- `\n# Evidence ledger\n\n"
            + "\n".join(ledger_table_lines)
            + "\n-->\n"
        )
        indented_table = "\n".join("    " + line for line in ledger_table_lines)
        empty_lines = empty_canonical_ledger.splitlines()
        canonical_header_index = empty_lines.index(ledger_header_row)
        indented_lines = ["## Unrelated indented code table", "", *indented_table.splitlines(), ""]
        empty_lines[canonical_header_index:canonical_header_index] = indented_lines
        indented_code_decoy = "\n".join(empty_lines) + "\n"
        trailing_fence_close_decoy = (
            "```markdown\n"
            "``` trailing text is not a closing fence\n"
            "# Evidence ledger\n\n"
            + "\n".join(ledger_table_lines)
            + "\n```\n"
        )
        last_claim_cells = ledger_cells(ledger_table_lines[-1])
        last_claim_cells[4] += " Inline-code example: `<!--`"
        last_claim_row = "| " + " | ".join(
            cell.replace("|", "\\|") for cell in last_claim_cells
        ) + " |"
        inline_comment_decoy = evidence_source.replace(ledger_table_lines[-1], last_claim_row, 1)
        inline_comment_decoy = insert_ledger_rows_after(
            inline_comment_decoy,
            last_claim_cells[0],
            ["| undeclared-after-inline-code | Synthetic undeclared claim. | partially_verified | README.md | Regression fixture only. |"],
        ) + "\n-->\n"
        second_ledger_section_decoy = (
            evidence_source.rstrip()
            + "\n\n# Intervening supplemental section\n\nSynthetic section text.\n"
            + "\n# Evidence ledger\n\n"
            + "\n".join(ledger_table_lines[:2])
            + "\n| undeclared-after-second-section | Synthetic undeclared claim. | partially_verified | README.md | Regression fixture only. |\n"
        )
        second_ledger_table = evidence_source.rstrip() + "\n\n" + "\n".join(ledger_table_lines) + "\n"
        raw_html_ledger_table = "\n".join(ledger_table_lines)
        raw_html_ledger_decoys = [
            (
                f"ledger inside raw <{tag}> block cannot substitute for visible ledger",
                f"<{tag}>\n# Evidence ledger\n{raw_html_ledger_table}\n</{tag}>\n",
            )
            for tag in ("pre", "script", "style", "textarea")
        ]
        raw_html_ledger_decoys.extend(
            [
                (
                    "ledger inside type-6 div block cannot substitute for visible ledger",
                    "<div hidden>\n# Evidence ledger\n"
                    + raw_html_ledger_table
                    + "\n</div>\n\n",
                ),
                (
                    "ledger inside type-7 picture block cannot substitute for visible ledger",
                    "<picture>\n# Evidence ledger\n"
                    + raw_html_ledger_table
                    + "\n</picture>\n\n",
                ),
            ]
        )
        separator_line = next(line for line in evidence_source.splitlines() if line.startswith("|---"))
        short_separator = evidence_source.replace(separator_line, "|---|---|---|---|", 1)
        malformed_then_unknown = insert_ledger_rows_after(
            evidence_source,
            claim_id,
            [
                "| malformed-ledger-row | only | three |",
                "undeclared-after-malformed | Synthetic undeclared claim. | partially_verified "
                "| README.md | Regression fixture only.",
            ],
        )
        proof_limit_mismatch = change_ledger_cell(
            evidence_source, 4, "Regression fixture omits the manifest proof limit."
        )
        duplicate_manifest = deepcopy(manifest_source)
        duplicate_manifest["claims"].append(deepcopy(duplicate_manifest["claims"][career_index]))
        def missing_evidence_case(extension: str, escaped_pipe_before_path: bool = False) -> tuple[dict, str]:
            manifest = deepcopy(manifest_source)
            claim = manifest["claims"][career_index]
            claim["evidence"][0]["ref"] = f"scripts/missing-evidence{extension}"
            changes = {3: "; ".join(reference["ref"] for reference in claim["evidence"])}
            if escaped_pipe_before_path:
                claim["text"] += " | escaped-pipe path fixture"
                changes[1] = claim["text"]
            return manifest, change_ledger_cells(evidence_source, changes)

        missing_ps_manifest, missing_ps_evidence = missing_evidence_case(".ps1")
        missing_xml_manifest, missing_xml_evidence = missing_evidence_case(".xml")
        missing_exe_manifest, missing_exe_evidence = missing_evidence_case(".exe")
        missing_zip_manifest, missing_zip_evidence = missing_evidence_case(".zip")
        missing_exe_pipe_manifest, missing_exe_pipe_evidence = missing_evidence_case(
            ".exe", escaped_pipe_before_path=True
        )
        screenshot_verified_manifest = deepcopy(manifest_source)
        screenshot_verified_claim = screenshot_verified_manifest["claims"][graphforge_claim_index]
        screenshot_ref = next(
            ref for ref in screenshot_verified_claim["evidence"] if ref["class"] == "artifact"
        )
        screenshot_verified_claim["status"] = "verified"
        screenshot_verified_claim["evidence"] = [deepcopy(screenshot_ref)]
        screenshot_verified_evidence = change_ledger_cells(
            evidence_source,
            {2: "verified", 3: screenshot_ref["ref"]},
            graphforge_claim_id,
        )
        missing_path_forbidden = (
            f"{claim_id}: evidence ledger must contain exactly one claim row",
            f"{claim_id}: evidence ledger claim text does not match the manifest",
            f"{claim_id}: evidence ledger references do not match the manifest",
        )
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
                "screenshot alone cannot verify a test-count claim",
                screenshot_verified_manifest,
                screenshot_verified_evidence,
                f"{graphforge_claim_id}: verified claims need source, test, or source-inventory evidence",
            ),
            (
                "undeclared ledger claim ID rejected",
                deepcopy(manifest_source),
                insert_ledger_row(
                    evidence_source,
                    claim_id,
                    "| undeclared-ledger-claim | Synthetic undeclared claim. | partially_verified | README.md | Regression fixture only. |",
                ),
                "undeclared-ledger-claim: evidence ledger claim ID is not declared in the manifest",
            ),
            (
                "unwrapped undeclared ledger claim ID rejected",
                deepcopy(manifest_source),
                insert_ledger_row(evidence_source, claim_id, unknown_claim_row),
                "undeclared-ledger-claim: evidence ledger claim ID is not declared in the manifest",
            ),
            (
                "duplicate evidence ledger row rejected",
                deepcopy(manifest_source),
                insert_ledger_row(evidence_source, claim_id, unwrapped_target_row),
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "duplicate declared claim ID rejected",
                duplicate_manifest,
                evidence_source,
                f"duplicate claim id: {claim_id}",
            ),
            (
                "fenced row cannot substitute for the ledger row",
                deepcopy(manifest_source),
                fenced_substitute,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "unrelated table row cannot substitute for the ledger row",
                deepcopy(manifest_source),
                unrelated_substitute,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "escaped pipe in ledger cell accepted",
                deepcopy(manifest_source),
                change_ledger_cell(
                    evidence_source,
                    4,
                    "Regression fixture contains | a literal pipe. Proof limit: "
                    + manifest_source["claims"][career_index]["proof_limit"],
                ),
                None,
            ),
            (
                "exact-header table before the ledger section cannot substitute for a row",
                deepcopy(manifest_source),
                exact_header_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "indented code table cannot substitute for the ledger table",
                deepcopy(manifest_source),
                indented_code_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "commented heading and table cannot substitute for the ledger",
                deepcopy(manifest_source),
                commented_ledger_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "same-line comment cannot supply the canonical ledger heading",
                deepcopy(manifest_source),
                same_line_commented_ledger_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "fence close marker with trailing text cannot expose a code table",
                deepcopy(manifest_source),
                trailing_fence_close_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "inline-code comment marker cannot hide a later undeclared ledger row",
                deepcopy(manifest_source),
                inline_comment_decoy,
                "undeclared-after-inline-code: evidence ledger claim ID is not declared in the manifest",
            ),
            (
                "unmatched backtick cannot expose a commented ledger",
                deepcopy(manifest_source),
                unmatched_backtick_comment_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "escaped backtick cannot expose a commented ledger",
                deepcopy(manifest_source),
                escaped_backtick_comment_decoy,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            ),
            (
                "second canonical ledger section after an intervening heading is rejected",
                deepcopy(manifest_source),
                second_ledger_section_decoy,
                "evidence document contains more than one Evidence ledger section",
            ),
            (
                "second ledger table after a blank is rejected",
                deepcopy(manifest_source),
                second_ledger_table,
                "evidence ledger contains more than one ledger table",
            ),
            (
                "short ledger separator rejected",
                deepcopy(manifest_source),
                short_separator,
                "evidence ledger separator must contain exactly 5 cells",
            ),
            (
                "malformed row does not hide a later undeclared ID",
                deepcopy(manifest_source),
                malformed_then_unknown,
                (
                    "evidence ledger row must contain exactly 5 cells",
                    "undeclared-after-malformed: evidence ledger claim ID is not declared in the manifest",
                ),
            ),
            (
                "ledger proof limit must match the manifest",
                deepcopy(manifest_source),
                proof_limit_mismatch,
                f"{claim_id}: evidence ledger proof limit does not match the manifest",
            ),
            (
                "missing PowerShell evidence path rejected",
                missing_ps_manifest,
                missing_ps_evidence,
                f"{claim_id} evidence: file does not exist: scripts/missing-evidence.ps1",
                missing_path_forbidden,
            ),
            (
                "missing XML evidence path rejected",
                missing_xml_manifest,
                missing_xml_evidence,
                f"{claim_id} evidence: file does not exist: scripts/missing-evidence.xml",
                missing_path_forbidden,
            ),
            (
                "missing executable evidence path rejected",
                missing_exe_manifest,
                missing_exe_evidence,
                f"{claim_id} evidence: file does not exist: scripts/missing-evidence.exe",
                missing_path_forbidden,
            ),
            (
                "missing archive evidence path rejected",
                missing_zip_manifest,
                missing_zip_evidence,
                f"{claim_id} evidence: file does not exist: scripts/missing-evidence.zip",
                missing_path_forbidden,
            ),
            (
                "escaped pipe before missing evidence path is parsed",
                missing_exe_pipe_manifest,
                missing_exe_pipe_evidence,
                f"{claim_id} evidence: file does not exist: scripts/missing-evidence.exe",
                missing_path_forbidden,
            ),
        ]
        cases.extend(
            (
                label,
                deepcopy(manifest_source),
                hidden_ledger,
                f"{claim_id}: evidence ledger must contain exactly one claim row",
            )
            for label, hidden_ledger in raw_html_ledger_decoys
        )
        cases[1][1]["claims"][career_index]["text"] += " (changed)"
        cases[2][1]["claims"][career_index]["evidence"][0]["ref"] = "LICENSE.md"
        cases_passed = True
        for case in cases:
            label, manifest_data, evidence_text, expected = case[:4]
            forbidden = case[4] if len(case) == 5 else ()
            if not run_case(label, manifest_data, evidence_text, expected, forbidden):
                cases_passed = False
        if not cases_passed or not readme_claim_coverage_passed:
            return 1
        if not run_case(
            "valid all-unwrapped GFM ledger accepted",
            deepcopy(manifest_source),
            remove_outer_pipes_from_ledger(evidence_source),
            None,
        ):
            return 1
        if not run_case(
            "indented code comment marker does not hide the canonical ledger",
            deepcopy(manifest_source),
            "    <!-- example source comment\n\n" + evidence_source,
            None,
        ):
            return 1
        if not run_case(
            "visible ledger after a type-6 HTML block remains accepted",
            deepcopy(manifest_source),
            "<div hidden>\n# Hidden fixture ledger\n\n</div>\n\n" + evidence_source,
            None,
        ):
            return 1
        if not run_case(
            "visible ledger after a closed type-1 HTML block remains accepted",
            deepcopy(manifest_source),
            "<textarea>\nHidden fixture text\n</textarea>\n\n" + evidence_source,
            None,
        ):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
