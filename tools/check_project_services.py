#!/usr/bin/env python3
"""Check cross-service identity and repository workflow invariants."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from .policy_common import Finding, load_repository_policy

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION_LITERAL = re.compile(r'^__version__\s*=\s*"([^"]+)"\s*$', re.MULTILINE)
FORBIDDEN_PUBLICATION = (
    "gh-action-pypi-publish",
    "id-token: write",
    "twine upload",
    "uv publish",
)


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data: dict[str, Any] = tomllib.load(handle)
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain an object")
    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    if True in data and "on" not in data:
        data["on"] = data.pop(True)
    return data


def _properties(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _iter_uses(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "uses" and isinstance(item, str):
                yield item
            yield from _iter_uses(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_uses(item)


def _is_sha_pinned(action: str) -> bool:
    if action.startswith("./") or action.startswith("docker://"):
        return True
    _separator, marker, reference = action.rpartition("@")
    return bool(marker and FULL_SHA.fullmatch(reference))


def _workflow_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    ci_path = root / ".github/workflows/ci.yml"
    trusted_pr_path = root / ".github/workflows/pr-metadata-policy.yml"
    release_path = root / ".github/workflows/release-please.yml"
    try:
        ci = _load_yaml(ci_path)
        trusted_pr = _load_yaml(trusted_pr_path)
        release = _load_yaml(release_path)
    except (OSError, ValueError, yaml.YAMLError):
        return [
            Finding(
                "WORKFLOW-SHAPE",
                ".github/workflows",
                "CI, trusted PR policy, and release workflows must be valid mappings",
            )
        ]

    ci_jobs = ci.get("jobs", {})
    required_jobs = {"verify", "sonar"}
    if not isinstance(ci_jobs, dict) or not required_jobs.issubset(ci_jobs):
        findings.append(
            Finding(
                "WORKFLOW-REQUIRED-GATE",
                ".github/workflows/ci.yml",
                "CI must define verify and sonar jobs",
            )
        )

    verify_job = ci_jobs.get("verify", {}) if isinstance(ci_jobs, dict) else {}
    strategy = verify_job.get("strategy", {}) if isinstance(verify_job, dict) else {}
    matrix = strategy.get("matrix", {}) if isinstance(strategy, dict) else {}
    python_versions = set(matrix.get("python-version", [])) if isinstance(matrix, dict) else set()
    if verify_job.get(
        "name"
    ) != "Verify (Python ${{ matrix.python-version }})" or python_versions != {"3.11", "3.12"}:
        findings.append(
            Finding(
                "WORKFLOW-PYTHON-MATRIX",
                ".github/workflows/ci.yml",
                "CI must verify the supported Python 3.11 and 3.12 versions",
            )
        )

    trusted_jobs = trusted_pr.get("jobs", {})
    trusted_job_names = (
        {job.get("name") for job in trusted_jobs.values() if isinstance(job, dict)}
        if isinstance(trusted_jobs, dict)
        else set()
    )
    trusted_text = trusted_pr_path.read_text(encoding="utf-8")
    trusted_markers = (
        "actions/checkout@" not in trusted_text,
        "release-please--branches--main--components--lilrae" in trusted_text,
        'pr.user.login === "github-actions[bot]"' in trusted_text,
        ('const required = ["Verify (Python 3.11)", "Verify (Python 3.12)", "Sonar"]')
        in trusted_text,
    )
    if trusted_job_names != {"PR Gate", "PR title"} or not all(trusted_markers):
        findings.append(
            Finding(
                "WORKFLOW-TRUSTED-PR-GATE",
                ".github/workflows/pr-metadata-policy.yml",
                "PR metadata and aggregate checks must run from trusted base-branch code",
            )
        )

    pull_request = ci.get("on", {}).get("pull_request", {})
    branches = set(pull_request.get("branches", [])) if isinstance(pull_request, dict) else set()
    if branches != {"dev", "main"}:
        findings.append(
            Finding(
                "WORKFLOW-PR-TARGETS",
                ".github/workflows/ci.yml",
                "CI pull-request targets must be exactly dev and main",
            )
        )

    pull_request_target = trusted_pr.get("on", {}).get("pull_request_target", {})
    trusted_branches = (
        set(pull_request_target.get("branches", []))
        if isinstance(pull_request_target, dict)
        else set()
    )
    if trusted_branches != {"dev", "main"}:
        findings.append(
            Finding(
                "WORKFLOW-PR-TARGETS",
                ".github/workflows/pr-metadata-policy.yml",
                "trusted PR policy targets must be exactly dev and main",
            )
        )

    release_push = release.get("on", {}).get("push", {})
    release_branches = (
        set(release_push.get("branches", [])) if isinstance(release_push, dict) else set()
    )
    if release_branches != {"main"}:
        findings.append(
            Finding(
                "RELEASE-BRANCH",
                ".github/workflows/release-please.yml",
                "Release Please must run only after main changes",
            )
        )
    release_text = release_path.read_text(encoding="utf-8").lower()
    if any(token in release_text for token in FORBIDDEN_PUBLICATION) or "publish" in release.get(
        "jobs", {}
    ):
        findings.append(
            Finding(
                "RELEASE-PUBLICATION",
                ".github/workflows/release-please.yml",
                "the backend-empty baseline must not publish a package",
            )
        )

    for path, workflow in (
        (ci_path, ci),
        (trusted_pr_path, trusted_pr),
        (release_path, release),
    ):
        findings.extend(
            [
                Finding(
                    "WORKFLOW-ACTION-PIN",
                    path.relative_to(root).as_posix(),
                    "third-party actions must use a full commit SHA",
                )
                for action in _iter_uses(workflow)
                if not _is_sha_pinned(action)
            ]
        )
    return findings


def _identity_findings(root: Path, policy: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    identity = policy["identity"]
    sonar_identity = policy["services"]["sonar"]
    try:
        project = _load_toml(root / "pyproject.toml")["project"]
        ground_control = _load_yaml(root / ".ground-control.yaml")
        sonar = _properties(root / "sonar-project.properties")
        release = _load_json(root / "release-please-config.json")
        manifest = _load_json(root / ".release-please-manifest.json")
        version_text = (root / "src/lilrae/_version.py").read_text(encoding="utf-8")
    except (KeyError, OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError):
        return [
            Finding(
                "SERVICE-SHAPE",
                ".",
                "project service configuration must be structurally readable",
            )
        ]

    expected_script = {str(identity["cli"]): f"{identity['import_package']}.cli:main"}
    service_checks: list[bool] = [
        project.get("name") == identity["distribution"],
        project.get("scripts") == expected_script,
        ground_control.get("project") == identity["ground_control_project"],
        ground_control.get("github_repo") == identity["github_repository"],
        ground_control.get("workflow", {}).get("base_branch") == "dev",
        ground_control.get("workflow", {}).get("completion_command") is not None,
        ground_control.get("workflow", {}).get("policy_command") == "make policy",
        sonar.get("sonar.projectKey") == sonar_identity["project_key"],
        sonar.get("sonar.organization") == sonar_identity["organization"],
    ]
    release_package = release.get("packages", {}).get(".", {})
    service_checks.extend(
        [
            release_package.get("package-name") == identity["distribution"],
            release.get("include-component-in-tag") is False,
        ]
    )
    if not all(service_checks):
        findings.append(
            Finding(
                "SERVICE-IDENTITY",
                ".",
                "package, GitHub, Ground Control, Sonar, and release identities must agree",
            )
        )

    match = VERSION_LITERAL.search(version_text)
    version = match.group(1) if match else None
    extra_files = release_package.get("extra-files", [])
    if (
        version is None
        or manifest.get(".") != version
        or {"type": "generic", "path": "src/lilrae/_version.py"} not in extra_files
    ):
        findings.append(
            Finding(
                "RELEASE-VERSION",
                "release-please-config.json",
                "Release Please state and the single package version source must agree",
            )
        )
    return findings


def _documentation_findings(root: Path) -> list[Finding]:
    required = {
        "README.md": {"authority boundary", "backend execution boundary"},
        "SECURITY.md": {"backend execution boundary"},
        "SUPPORT.md": {"backend execution boundary"},
    }
    findings: list[Finding] = []
    for relative, headings in required.items():
        try:
            content = (root / relative).read_text(encoding="utf-8")
        except OSError:
            content = ""
        actual = {
            line.lstrip("#").strip().casefold()
            for line in content.splitlines()
            if line.startswith("#")
        }
        if not headings.issubset(actual):
            findings.append(
                Finding(
                    "DOC-BOUNDARY",
                    relative,
                    "required authority and execution-boundary sections must remain explicit",
                )
            )
    return findings


def check_project_services(root: Path) -> list[Finding]:
    try:
        policy = load_repository_policy(root)
        policy["identity"]
        policy["services"]["sonar"]
    except (KeyError, OSError, TypeError, ValueError, tomllib.TOMLDecodeError):
        return [
            Finding(
                "SERVICE-POLICY-SHAPE",
                "policy/repository.toml",
                "service identity policy must be complete",
            )
        ]
    findings = _identity_findings(root, policy)
    findings.extend(_workflow_findings(root))
    findings.extend(_documentation_findings(root))
    return sorted(set(findings))


def main() -> int:
    findings = check_project_services(ROOT)
    if findings:
        print("project services: FAIL", file=sys.stderr)
        for finding in findings:
            print(
                f"  {finding.rule_id} {finding.path}: {finding.message}",
                file=sys.stderr,
            )
        return 1
    print("project services: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
