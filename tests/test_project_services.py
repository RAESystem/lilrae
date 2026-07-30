from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.check_project_services as project_services
from tests.test_repo_policy import POLICY
from tools.check_project_services import check_project_services


def _service_repository(tmp_path: Path) -> Path:
    files: dict[str, str] = {
        "policy/repository.toml": POLICY,
        "pyproject.toml": """
[project]
name = "lilrae"
dynamic = ["version"]
dependencies = ["raes==3.0.0"]
[project.scripts]
lilrae = "lilrae.cli:main"
[tool.hatch.version]
path = "src/lilrae/_version.py"
""",
        "src/lilrae/_version.py": '__version__ = "0.0.0"\n',
        ".ground-control.yaml": """
schema_version: 1
project: lilrae
github_repo: RAESystem/lilrae
workflow:
  base_branch: dev
  completion_command: make verify
  policy_command: make policy
""",
        "sonar-project.properties": """
sonar.projectKey=CONFIRMED_LILRAE_KEY
sonar.organization=confirmed-org
""",
        "release-please-config.json": json.dumps(
            {
                "include-component-in-tag": False,
                "packages": {
                    ".": {
                        "release-type": "python",
                        "package-name": "lilrae",
                        "extra-files": [{"type": "generic", "path": "src/lilrae/_version.py"}],
                    }
                },
            }
        ),
        ".release-please-manifest.json": '{".": "0.0.0"}\n',
        ".github/workflows/release-please.yml": """
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  release-please:
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: googleapis/release-please-action@0123456789012345678901234567890123456789
""",
        ".github/workflows/ci.yml": """
on:
  pull_request:
    branches: [dev, main]
permissions:
  contents: read
jobs:
  verify: {runs-on: ubuntu-latest}
  sonar: {runs-on: ubuntu-latest}
""",
        ".github/workflows/pr-metadata-policy.yml": """
on:
  pull_request_target:
    branches: [dev, main]
permissions:
  checks: read
  contents: read
  pull-requests: read
jobs:
  pr-policy:
    name: PR Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@0123456789012345678901234567890123456789
        with:
          script: |
            const required = ["Verify", "Sonar"];
            const release = "release-please--branches--main--components--lilrae";
            const author = pr.user.login === "github-actions[bot]";
  pr-title:
    name: PR title
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@0123456789012345678901234567890123456789
""",
        "README.md": "# LilRAE\n\n## Authority boundary\n\n## Backend execution boundary\n",
        "SECURITY.md": "# Security\n\n## Backend execution boundary\n",
        "SUPPORT.md": "# Support\n\n## Backend execution boundary\n",
    }
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return tmp_path


def _rule_ids(root: Path) -> set[str]:
    return {finding.rule_id for finding in check_project_services(root)}


def test_consistent_services_and_publication_disabled_pass(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)

    assert check_project_services(root) == []


def test_sonar_identity_drift_fails(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    (root / "sonar-project.properties").write_text(
        "sonar.projectKey=wrong\nsonar.organization=confirmed-org\n",
        encoding="utf-8",
    )

    assert "SERVICE-IDENTITY" in _rule_ids(root)


def test_publication_job_fails_while_backend_is_empty(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    release = root / ".github/workflows/release-please.yml"
    release.write_text(
        release.read_text(encoding="utf-8")
        + "\n  publish:\n    steps:\n      - uses: pypa/gh-action-pypi-publish@"
        + "0123456789012345678901234567890123456789\n",
        encoding="utf-8",
    )

    assert "RELEASE-PUBLICATION" in _rule_ids(root)


def test_unpinned_workflow_action_fails(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    trusted = root / ".github/workflows/pr-metadata-policy.yml"
    trusted.write_text(
        trusted.read_text(encoding="utf-8").replace(
            "actions/github-script@0123456789012345678901234567890123456789",
            "actions/github-script@v8",
            1,
        ),
        encoding="utf-8",
    )

    assert "WORKFLOW-ACTION-PIN" in _rule_ids(root)


def test_release_manifest_version_drift_fails(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    (root / ".release-please-manifest.json").write_text(
        '{".": "1.0.0"}\n',
        encoding="utf-8",
    )

    assert "RELEASE-VERSION" in _rule_ids(root)


def test_required_aggregate_gate_is_structural(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    trusted = root / ".github/workflows/pr-metadata-policy.yml"
    trusted.write_text(
        trusted.read_text(encoding="utf-8").replace(
            '            const required = ["Verify", "Sonar"];\n',
            "",
        ),
        encoding="utf-8",
    )

    assert "WORKFLOW-TRUSTED-PR-GATE" in _rule_ids(root)


def test_security_and_support_name_execution_boundary(tmp_path: Path) -> None:
    root = _service_repository(tmp_path)
    (root / "SECURITY.md").write_text("# Security\n", encoding="utf-8")

    assert "DOC-BOUNDARY" in _rule_ids(root)


def test_project_services_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _service_repository(tmp_path)
    monkeypatch.setattr(project_services, "ROOT", root)
    assert project_services.main() == 0
    assert "OK" in capsys.readouterr().out

    (root / "SUPPORT.md").write_text("# Support\n", encoding="utf-8")
    assert project_services.main() == 1
    assert "DOC-BOUNDARY" in capsys.readouterr().err


def test_malformed_service_policy_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "policy").mkdir()
    (tmp_path / "policy/repository.toml").write_text("schema_version = 2\n", encoding="utf-8")

    assert check_project_services(tmp_path)[0].rule_id == "SERVICE-POLICY-SHAPE"
