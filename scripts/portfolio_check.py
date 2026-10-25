#!/usr/bin/env python3
"""Read-only checker for the repository's JSON-compatible YAML portfolio manifest."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

STATUSES = {"verified", "partially_verified", "unverified"}
PRIMARY = {"source", "test", "artifact", "source-inventory"}
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
                ["git", "-c", "core.untrackedCache=false", "-C", str(root), *args],
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
    ledger_rows: dict[str, list[list[str]]] = {}
    for line in evidence_doc.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] != "Claim ID":
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
            fail(f"{claim_id}: verified claims need primary evidence")
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
        if not isinstance(claim.get("proof_limit"), str) or not claim["proof_limit"].strip():
            fail(f"{claim_id}: proof_limit is required")
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
