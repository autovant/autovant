#!/usr/bin/env python3
"""Read-only checker for the repository's JSON-compatible YAML portfolio manifest."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

STATUSES = {"verified", "partially_verified", "unverified"}
PRIMARY = {"source", "test", "source-inventory"}
PLACEHOLDER = re.compile(
    r"\b(?:TODO|TBD|FIXME|YOUR_NAME|REPLACE_ME)\b|\[(?:add|insert|replace)\b|<your\b", re.I
)
MACHINE_PATH = re.compile(r"(?i)(?:\b[a-z]:[\\/]|/(?:users|home|root)/|/mnt/c/)")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML = re.compile(r"\b(src|srcset)\s*=\s*['\"]([^'\"]+)['\"]", re.I)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=root / ".portfolio/project.yaml")
    manifest_path = parser.parse_args().manifest.resolve()
    try:
        manifest_path.relative_to(root)
    except ValueError:
        print("ERROR: manifest path must be inside the repository")
        print("PORTFOLIO CHECK: BLOCKED - manifest path outside repository")
        return 1
    errors: list[str] = []
    warnings: list[str] = []

    def fail(message: str) -> None:
        errors.append(message)

    def local_file(value: object, label: str) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            fail(f"{label}: expected a repository-relative path")
            return None
        path = (root / value.split("#", 1)[0]).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            fail(f"{label}: path escapes the repository: {value}")
            return None
        if not path.is_file():
            fail(f"{label}: file does not exist: {value}")
            return None
        return path

    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                [
                    "git", "--no-optional-locks", "-c", "core.untrackedCache=false",
                    "-C", str(root), *args,
                ],
                capture_output=True, text=True,
                timeout=5, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"manifest is missing or invalid JSON-compatible YAML: {exc}")
        data = {}
    if not isinstance(data, dict):
        fail("manifest root must be an object")
        data = {}

    required = {
        "schema_version", "project", "level", "summary", "source_base",
        "revision_scope", "supported_environment", "commands", "readme_sections",
        "architecture", "evidence", "demo", "claims", "limitations",
    }
    missing = sorted(required - data.keys())
    if missing:
        fail("manifest missing fields: " + ", ".join(missing))
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        fail("schema_version must be 1")
    for key in ("project", "summary", "revision_scope"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            fail(f"{key} must be a non-empty string")
    base = data.get("source_base")
    match = re.fullmatch(r"origin/main@([0-9a-f]{40})", base) if isinstance(base, str) else None
    if not match:
        fail("source_base must bind to origin/main@<40-character commit SHA>")
    elif git("cat-file", "-e", f"{match.group(1)}^{{commit}}") is None:
        fail("source_base commit is absent from the local Git object database")

    local_file("AGENTS.md", "AGENTS")
    readme = local_file("README.md", "README")
    doc_paths = {key: local_file(data.get(key), key) for key in ("architecture", "evidence", "demo")}
    if readme:
        sections = data.get("readme_sections")
        if not isinstance(sections, list):
            fail("readme_sections must be a list")
        else:
            text = readme.read_text(encoding="utf-8")
            for heading in sections:
                if not isinstance(heading, str) or f"## {heading}" not in text:
                    fail(f"README missing required section: {heading}")

    commands = data.get("commands")
    if not isinstance(commands, dict):
        fail("commands must be an object")
        commands = {}
    for name in ("run", "test", "demo"):
        cmd = commands.get(name)
        if cmd is None:
            reason = commands.get(f"{name}_status")
            if not isinstance(reason, str) or not reason.strip():
                fail(f"{name} is null without a stated reason")
            continue
        if not isinstance(cmd, dict) or not isinstance(cmd.get("command"), str):
            fail(f"{name} must define a command or be explicitly null")
            continue
        source = local_file(cmd.get("file"), f"{name} command")
        if not source or not isinstance(cmd.get("script"), str):
            fail(f"{name} needs a command source and package script")
            continue
        try:
            package = json.loads(source.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            fail(f"{name} command source must be valid JSON")
            continue
        script = cmd["script"]
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        if script not in scripts:
            fail(f"{name} refers to missing package script: {script}")
        else:
            expected = "npm test" if script == "test" else f"npm run {script}"
            if cmd["command"] != expected:
                fail(f"{name} command mismatch: expected {expected}")
        if cmd.get("instructions"):
            local_file(cmd["instructions"], f"{name} instructions")
    if commands.get("demo") is None:
        local_file(commands.get("demo_instructions"), "demo instructions")

    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        fail("claims must be a non-empty list")
        claims = []
    evidence_doc = doc_paths["evidence"].read_text(encoding="utf-8") if doc_paths["evidence"] else ""
    ledger_header = [
        "Claim ID", "Exact published claim", "Status", "Evidence references", "Evidence and limit",
    ]

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

    def strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
        def is_escaped_backtick(index: int) -> bool:
            backslashes = 0
            index -= 1
            while index >= 0 and line[index] == "\\":
                backslashes += 1
                index -= 1
            return backslashes % 2 == 1

        visible: list[str] = []
        cursor = 0
        while cursor < len(line):
            if in_comment:
                closing = line.find("-->", cursor)
                if closing < 0:
                    return "".join(visible), True
                cursor = closing + 3
                in_comment = False
                continue

            opening = line.find("<!--", cursor)
            code_start = line.find("`", cursor)
            while code_start >= 0 and is_escaped_backtick(code_start):
                escaped_run_end = code_start
                while escaped_run_end < len(line) and line[escaped_run_end] == "`":
                    escaped_run_end += 1
                code_start = (
                    code_start + 1
                    if code_start + 1 < escaped_run_end
                    else line.find("`", escaped_run_end)
                )
            if code_start >= 0 and (opening < 0 or code_start < opening):
                visible.append(line[cursor:code_start])
                run_end = code_start
                while run_end < len(line) and line[run_end] == "`":
                    run_end += 1
                run_length = run_end - code_start
                code_end = line.find("`", run_end)
                matching_end = None
                while code_end >= 0:
                    candidate_end = code_end
                    while candidate_end < len(line) and line[candidate_end] == "`":
                        candidate_end += 1
                    if candidate_end - code_end == run_length:
                        matching_end = candidate_end
                        break
                    code_end = line.find("`", candidate_end)
                if matching_end is None:
                    visible.append(line[code_start:run_end])
                    cursor = run_end
                else:
                    visible.append(line[code_start:matching_end])
                    cursor = matching_end
                continue
            if opening < 0:
                visible.append(line[cursor:])
                return "".join(visible), False
            visible.append(line[cursor:opening])
            cursor = opening + 4
            in_comment = True
        return "".join(visible), in_comment

    ledger_rows: dict[str, list[list[str]]] = {}
    fence: tuple[str, int] | None = None
    in_html_comment = False
    in_ledger_section = False
    saw_ledger_section = False
    header_found = False
    table_started = False
    table_ended = False
    ledger_width = len(ledger_header)
    for raw_line in evidence_doc.splitlines():
        if (
            fence is None
            and not in_html_comment
            and (raw_line.startswith("    ") or raw_line.startswith("\t"))
        ):
            continue
        raw_fence_match = re.match(r"^(`{3,}|~{3,})", raw_line.strip())
        if fence is None and raw_fence_match and not in_html_comment:
            line = raw_line
        elif fence is None:
            line, in_html_comment = strip_html_comments(raw_line, in_html_comment)
        else:
            line = raw_line
        if line.startswith("    ") or line.startswith("\t"):
            continue
        stripped = line.strip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                if table_started:
                    table_ended = True
                elif header_found:
                    fail("evidence ledger header must be followed by a separator row")
                    table_ended = True
                fence = (marker[0], len(marker))
            elif (
                marker[0] == fence[0]
                and len(marker) >= fence[1]
                and re.fullmatch(rf"{re.escape(fence[0])}{{{fence[1]},}}", stripped)
            ):
                fence = None
            continue
        if fence is not None:
            continue
        if re.match(r"^#\s", stripped):
            if re.fullmatch(r"#\s+Evidence ledger\s*#*", stripped):
                if saw_ledger_section:
                    fail("evidence document contains more than one Evidence ledger section")
                else:
                    saw_ledger_section = True
                    in_ledger_section = True
            elif in_ledger_section:
                in_ledger_section = False
            continue
        if not in_ledger_section:
            continue
        if not stripped:
            if header_found and not table_started:
                fail("evidence ledger header must be followed by a separator row")
                table_ended = True
            elif table_started:
                table_ended = True
            continue
        cells = ledger_cells(stripped)
        if table_ended:
            if cells == ledger_header:
                fail("evidence ledger contains more than one ledger table")
            continue
        if not header_found:
            if cells == ledger_header:
                header_found = True
            continue
        if not table_started:
            if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
                if len(cells) != ledger_width:
                    fail(f"evidence ledger separator must contain exactly {ledger_width} cells")
                table_started = True
            else:
                fail("evidence ledger header must be followed by a separator row")
                table_ended = True
            continue
        if "|" not in stripped:
            table_ended = True
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            fail("evidence ledger contains an unexpected separator row")
            continue
        if len(cells) != ledger_width:
            fail(f"evidence ledger row must contain exactly {ledger_width} cells")
            continue
        ledger_rows.setdefault(cells[0], []).append(cells)
    ids: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            fail("each claim must be an object")
            continue
        claim_id, exact, status = claim.get("id"), claim.get("text"), claim.get("status")
        if not isinstance(claim_id, str) or not claim_id.strip():
            fail("claim is missing a stable id")
            continue
        if claim_id in ids:
            fail(f"duplicate claim id: {claim_id}")
        ids.add(claim_id)
        if not isinstance(exact, str) or not exact.strip():
            fail(f"{claim_id}: exact claim text is required")
            exact = ""
        if not isinstance(status, str) or status not in STATUSES:
            fail(f"{claim_id}: invalid status {status!r}")
        elif status != "verified":
            warnings.append(f"{claim_id}: status is {status}")
        refs = claim.get("evidence")
        if not isinstance(refs, list):
            fail(f"{claim_id}: evidence must be a list")
            refs = []
        classes = set()
        for ref in refs:
            if not isinstance(ref, dict):
                fail(f"{claim_id}: evidence references must be objects")
                continue
            local_file(ref.get("ref"), f"{claim_id} evidence")
            if isinstance(ref.get("class"), str):
                classes.add(ref["class"])
            if not isinstance(ref.get("scope"), str) or not ref["scope"].strip():
                fail(f"{claim_id}: evidence scope is required")
        if status == "verified" and not classes.intersection(PRIMARY):
            fail(f"{claim_id}: verified claims need source, test, or source-inventory evidence")
        rows = ledger_rows.get(claim_id, [])
        if len(rows) != 1:
            fail(f"{claim_id}: evidence ledger must contain exactly one claim row")
        else:
            row = rows[0]
            if row[1] != exact:
                fail(f"{claim_id}: evidence ledger claim text does not match the manifest")
            if row[2] != status:
                fail(f"{claim_id}: evidence ledger status does not match the manifest")
            expected_refs = [
                ref["ref"] for ref in refs
                if isinstance(ref, dict) and isinstance(ref.get("ref"), str)
            ]
            if row[3] != "; ".join(expected_refs):
                fail(f"{claim_id}: evidence ledger references do not match the manifest")
            proof_limit = claim.get("proof_limit")
            if isinstance(proof_limit, str) and proof_limit and proof_limit not in row[4]:
                fail(f"{claim_id}: evidence ledger proof limit does not match the manifest")
        if not isinstance(claim.get("proof_limit"), str) or not claim["proof_limit"].strip():
            fail(f"{claim_id}: proof_limit is required")
    for ledger_id in ledger_rows.keys() - ids:
        fail(f"{ledger_id}: evidence ledger claim ID is not declared in the manifest")
    if not isinstance(data.get("limitations"), list) or not data["limitations"]:
        fail("limitations must be a non-empty list")

    public = [root / "README.md", manifest_path]
    public += [p for p in (root / "LICENSE.md", root / "LICENSE") if p.is_file()]
    for folder in ("docs", "case-studies"):
        directory = root / folder
        if directory.is_dir():
            public.extend(directory.rglob("*.md"))
    for path in public:
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            fail(f"public document path escapes repository: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        label = path.resolve().relative_to(root)
        if PLACEHOLDER.search(text):
            fail(f"{label}: placeholder text found")
        if MACHINE_PATH.search(text):
            fail(f"{label}: machine-specific absolute path found")
        for target in LINK.findall(text):
            check_link(root, path, target, fail)
        for kind, value in HTML.findall(text):
            for target in value.split(",") if kind.lower() == "srcset" else [value]:
                check_link(root, path, target.strip().split()[0] if target.strip() else "", fail)

    head = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain", "--untracked-files=normal")
    if head is None or dirty is None:
        fail("could not read Git HEAD and dirty state")
    elif dirty:
        warnings.append("working tree is dirty; readiness requires a committed candidate")
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    if head:
        print(f"Git HEAD: {head}")
    state = "BLOCKED" if errors else ("READY WITH WARNINGS" if warnings else "READY")
    print(f"PORTFOLIO CHECK: {state} - {data.get('project', 'unknown project')}")
    return 1 if errors else 0


def check_link(root: Path, source: Path, target: str, fail) -> None:
    if not target or target.startswith("#") or re.match(r"(?i)^(?:https?:|mailto:|data:|tel:)", target):
        return
    local = target.split("#", 1)[0].split("?", 1)[0]
    if not local:
        return
    path = (source.parent / local).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        fail(f"{source.relative_to(root)}: local link escapes repository: {target}")
        return
    if not path.exists():
        fail(f"{source.relative_to(root)}: broken local link: {target}")


if __name__ == "__main__":
    sys.exit(main())
