#!/usr/bin/env python3
"""Read-only repository hygiene checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from .policy_common import Finding, relative_path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 500 * 1024
IGNORED_PREFIXES = (
    ".codex/",
    ".git/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "build/",
    "dist/",
)
IGNORED_FILES = {".env", ".mcp.json"}
MERGE_MARKERS = ("<" * 7 + " ", "=" * 7 + "\n", ">" * 7 + " ")
PRIVATE_KEY_MARKERS = (
    "-----BEGIN " + "PRIVATE KEY-----",
    "-----BEGIN " + "RSA PRIVATE KEY-----",
    "-----BEGIN " + "EC PRIVATE KEY-----",
    "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
)


def _repository_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        git = shutil.which("git")
        if git is None:
            return []
        result = subprocess.run(  # noqa: S603 - resolved git binary and fixed arguments
            [
                git,
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return sorted(root / entry for entry in result.stdout.decode().split("\0") if entry)
    return sorted(path for path in root.rglob("*") if path.is_file())


def _ignored(relative: str) -> bool:
    return relative in IGNORED_FILES or any(
        relative.startswith(prefix) for prefix in IGNORED_PREFIXES
    )


def check_hygiene(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in _repository_files(root):
        relative = relative_path(root, path)
        if _ignored(relative):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            findings.append(Finding("HYGIENE-READ", relative, "repository file must be readable"))
            continue
        if len(data) > MAX_FILE_BYTES:
            findings.append(
                Finding("HYGIENE-LARGE-FILE", relative, "repository file exceeds 500 KiB")
            )
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if text and not text.endswith("\n"):
            findings.append(Finding("HYGIENE-EOF", relative, "text files must end with a newline"))
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            findings.append(
                Finding(
                    "HYGIENE-WHITESPACE", relative, "text files must not have trailing whitespace"
                )
            )
        if any(marker in text for marker in MERGE_MARKERS):
            findings.append(
                Finding("HYGIENE-MERGE", relative, "merge-conflict markers are forbidden")
            )
        if any(marker in text for marker in PRIVATE_KEY_MARKERS):
            findings.append(
                Finding(
                    "HYGIENE-PRIVATE-KEY",
                    relative,
                    "private-key material is forbidden in repository files",
                )
            )
        try:
            if path.suffix == ".json":
                json.loads(text)
            elif path.suffix in {".yaml", ".yml"}:
                yaml.safe_load(text)
        except (json.JSONDecodeError, yaml.YAMLError):
            findings.append(
                Finding(
                    "HYGIENE-JSON" if path.suffix == ".json" else "HYGIENE-YAML",
                    relative,
                    "structured data must parse",
                )
            )
    return sorted(set(findings))


def main() -> int:
    findings = check_hygiene(ROOT)
    if findings:
        print("repository hygiene: FAIL", file=sys.stderr)
        for finding in findings:
            print(
                f"  {finding.rule_id} {finding.path}: {finding.message}",
                file=sys.stderr,
            )
        return 1
    print("repository hygiene: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
