#!/usr/bin/env python3
"""Enforce LilRAE's released-only RAES dependency boundary."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .policy_common import Finding, load_repository_policy, relative_path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT_NAME = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
PYTHONPATH_ASSIGNMENT = re.compile(r"PYTHONPATH\s*:", re.IGNORECASE)
CONFIG_SOURCE_PATTERNS = (
    re.compile(r"(?:^|[\"'\s])\.\./rae(?:/|[\"'\s]|$)", re.IGNORECASE),
    re.compile(r"implementations/python", re.IGNORECASE),
    re.compile(r"packages/raes[_/-]", re.IGNORECASE),
    re.compile(r"git\+https?://[^\s\"']*/rae(?:\.git)?", re.IGNORECASE),
)
CONFIG_SUFFIXES = {".bash", ".sh", ".yaml", ".yml"}
PYPROJECT_PATH = "pyproject.toml"
UV_LOCK_PATH = "uv.lock"


def _repository_files(root: Path) -> list[Path]:
    """Return version-controlled and unignored files without walking tool environments."""
    git = shutil.which("git")
    if git is None:
        return [path for path in root.rglob("*") if path.is_file()]
    result = subprocess.run(  # noqa: S603 - executable is resolved by shutil.which
        [git, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return [
            root / relative.decode("utf-8", errors="surrogateescape")
            for relative in result.stdout.split(b"\0")
            if relative
        ]
    return [path for path in root.rglob("*") if path.is_file()]


def _normalise_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _constant_string(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self, path: str, public_imports: set[str]) -> None:
        self.path = path
        self.public_imports = public_imports
        self.findings: list[Finding] = []

    def _add(self, rule_id: str, line: int, message: str) -> None:
        self.findings.append(Finding(rule_id, f"{self.path}:{line}", message))

    def _check_module(
        self,
        module: str,
        line: int,
        imported_names: Iterable[str] = (),
    ) -> None:
        parts = module.split(".")
        root = parts[0]
        if root == "implementations" or (
            root in {"packages", "src"} and any(part.startswith("raes") for part in parts)
        ):
            self._add(
                "RAES-IMPORT-SOURCE",
                line,
                "RAES imports must not address an upstream repository layout",
            )
            return
        if not root.startswith("raes"):
            return
        if any(part.startswith("_") for part in parts) or any(
            name.startswith("_") for name in imported_names
        ):
            self._add(
                "RAES-IMPORT-PRIVATE",
                line,
                "RAES imports must use an explicitly declared public surface",
            )
            return
        if module not in self.public_imports:
            self._add(
                "RAES-IMPORT-NONPUBLIC",
                line,
                "RAES imports must match an explicitly declared public module",
            )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._check_module(node.module, node.lineno, (alias.name for alias in node.names))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        called = _dotted_name(node.func)
        if called in {"sys.path.append", "sys.path.extend", "sys.path.insert"}:
            self._add(
                "RAES-PATH-MUTATION",
                node.lineno,
                "module search paths must not be mutated",
            )
        if called in {
            "importlib.util.spec_from_file_location",
            "importlib.machinery.SourceFileLoader",
        }:
            self._add(
                "RAES-FILE-LOAD",
                node.lineno,
                "source files must not be loaded as RAES modules",
            )
        if called in {"importlib.import_module", "__import__"} and node.args:
            module = _constant_string(node.args[0])
            if module:
                self._check_module(module, node.lineno)
        if called == "os.putenv" and node.args and _constant_string(node.args[0]) == "PYTHONPATH":
            self._add(
                "RAES-PATH-MUTATION",
                node.lineno,
                "PYTHONPATH must not be mutated",
            )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and _dotted_name(target.value) == "os.environ"
                and _constant_string(target.slice) == "PYTHONPATH"
            ):
                self._add(
                    "RAES-PATH-MUTATION",
                    node.lineno,
                    "PYTHONPATH must not be mutated",
                )
        self.generic_visit(node)


def _is_excluded(relative: str, exclusions: tuple[str, ...]) -> bool:
    return any(
        relative == prefix.rstrip("/") or relative.startswith(prefix) for prefix in exclusions
    )


def _python_findings(
    root: Path,
    public_imports: set[str],
    exclusions: tuple[str, ...],
) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(
        candidate for candidate in _repository_files(root) if candidate.suffix == ".py"
    ):
        relative = relative_path(root, path)
        if _is_excluded(relative, exclusions):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError):
            findings.append(
                Finding(
                    "RAES-PYTHON-PARSE", relative, "Python source must parse for policy inspection"
                )
            )
            continue
        visitor = _ImportVisitor(relative, public_imports)
        visitor.visit(tree)
        findings.extend(visitor.findings)
    return findings


def _dependency_findings(root: Path, policy: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    raes = policy["raes"]
    distribution = _normalise_distribution(str(raes["distribution"]))
    expected = f"{distribution}=={raes['version']}"
    try:
        with (root / PYPROJECT_PATH).open("rb") as handle:
            project_file = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return [
            Finding(
                "RAES-MANIFEST-SHAPE",
                PYPROJECT_PATH,
                "project metadata must be valid TOML",
            )
        ]

    requirements: list[str] = []
    project = project_file.get("project", {})
    requirements.extend(str(item) for item in project.get("dependencies", []))
    for items in project.get("optional-dependencies", {}).values():
        requirements.extend(str(item) for item in items)
    for items in project_file.get("dependency-groups", {}).values():
        requirements.extend(str(item) for item in items)

    raes_requirements = [
        item
        for item in requirements
        if (match := REQUIREMENT_NAME.match(item))
        and _normalise_distribution(match.group(1)) == distribution
    ]
    if raes_requirements != [expected]:
        source_shape = any("@" in item or "://" in item for item in raes_requirements)
        findings.append(
            Finding(
                "RAES-DEPENDENCY-SOURCE" if source_shape else "RAES-DEPENDENCY-PIN",
                PYPROJECT_PATH,
                "RAES must appear once as the exact released registry dependency",
            )
        )

    sources = project_file.get("tool", {}).get("uv", {}).get("sources", {})
    if any(_normalise_distribution(str(name)) == distribution for name in sources):
        findings.append(
            Finding(
                "RAES-DEPENDENCY-SOURCE",
                PYPROJECT_PATH,
                "RAES source overrides are forbidden",
            )
        )

    try:
        with (root / UV_LOCK_PATH).open("rb") as handle:
            lock = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        findings.append(
            Finding("RAES-LOCK-SHAPE", UV_LOCK_PATH, "resolver lock data must be valid TOML")
        )
        return findings

    packages = [
        package
        for package in lock.get("package", [])
        if _normalise_distribution(str(package.get("name", ""))) == distribution
    ]
    allowed_registries = set(map(str, raes["allowed_registries"]))
    if len(packages) != 1 or str(packages[0].get("version")) != str(raes["version"]):
        findings.append(
            Finding(
                "RAES-LOCK-PIN",
                UV_LOCK_PATH,
                "the lock must contain exactly the declared RAES release",
            )
        )
    elif packages[0].get("source") != {"registry": next(iter(allowed_registries))} and (
        not isinstance(packages[0].get("source"), dict)
        or set(packages[0]["source"]) != {"registry"}
        or packages[0]["source"].get("registry") not in allowed_registries
    ):
        findings.append(
            Finding(
                "RAES-LOCK-SOURCE",
                UV_LOCK_PATH,
                "the locked RAES artifact must come from an approved registry",
            )
        )
    return findings


def _has_raes_pythonpath(content: str) -> bool:
    for line in content.splitlines():
        code = line.partition("#")[0]
        if PYTHONPATH_ASSIGNMENT.search(code) and "rae" in code.casefold():
            return True
    return False


def _configuration_findings(
    root: Path,
    exclusions: tuple[str, ...],
) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(_repository_files(root)):
        relative = relative_path(root, path)
        if _is_excluded(relative, exclusions) or path.suffix.lower() not in CONFIG_SUFFIXES:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if _has_raes_pythonpath(content) or any(
            pattern.search(content) for pattern in CONFIG_SOURCE_PATTERNS
        ):
            findings.append(
                Finding(
                    "RAES-CONFIG-SOURCE",
                    relative,
                    "configuration must not make a RAES checkout part of execution",
                )
            )
    return findings


def _contract_copy_findings(
    root: Path,
    forbidden_roots: tuple[str, ...],
    exclusions: tuple[str, ...],
) -> list[Finding]:
    for path in sorted(_repository_files(root)):
        relative = relative_path(root, path)
        if _is_excluded(relative, exclusions):
            continue
        if any(relative.startswith(prefix) for prefix in forbidden_roots):
            return [
                Finding(
                    "RAES-CONTRACT-COPY",
                    relative,
                    "portable RAES contracts must be resolved from the installed distribution",
                )
            ]
    return []


def check_repository(root: Path) -> list[Finding]:
    try:
        policy = load_repository_policy(root)
        scan = policy["scan"]
        exclusions = tuple(map(str, scan["exclude"]))
        public_imports = set(map(str, policy["raes"]["public_imports"]))
        forbidden_roots = tuple(map(str, scan["forbidden_contract_roots"]))
    except (KeyError, OSError, TypeError, ValueError):
        return [
            Finding(
                "RAES-POLICY-SHAPE",
                "policy/repository.toml",
                "repository policy must be a complete schema-version-1 declaration",
            )
        ]

    findings = _dependency_findings(root, policy)
    findings.extend(_python_findings(root, public_imports, exclusions))
    findings.extend(_configuration_findings(root, exclusions))
    findings.extend(_contract_copy_findings(root, forbidden_roots, exclusions))
    return sorted(set(findings))


def main() -> int:
    findings = check_repository(ROOT)
    if findings:
        print("repository policy: FAIL", file=sys.stderr)
        for finding in findings:
            print(
                f"  {finding.rule_id} {finding.path}: {finding.message}",
                file=sys.stderr,
            )
        return 1
    print("repository policy: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
