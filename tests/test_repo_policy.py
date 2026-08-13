from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import tools.check_repo_policy as repo_policy
from tools.check_repo_policy import check_repository

POLICY = """
schema_version = 1

[identity]
distribution = "lilrae"
import_package = "lilrae"
cli = "lilrae"
github_repository = "RAESystem/lilrae"
ground_control_project = "lilrae"
release_tag_format = "vX.Y.Z"

[raes]
distribution = "raes"
version = "3.3.0"
public_imports = [
  "raes_contracts",
  "raes_backend_protocols",
  "raes_conformance",
]
allowed_registries = ["https://pypi.org/simple"]

[services.sonar]
project_key = "CONFIRMED_LILRAE_KEY"
organization = "confirmed-org"

[scan]
exclude = [".git/", ".venv/", "build/", "dist/"]
forbidden_contract_roots = ["contracts/", "schemas/"]
"""

PYPROJECT = """
[project]
name = "lilrae"
version = "0.0.0"
dependencies = ["raes==3.3.0"]
"""

LOCK = """
version = 1
revision = 3

[[package]]
name = "raes"
version = "3.3.0"
source = { registry = "https://pypi.org/simple" }
"""


def _repository(tmp_path: Path, source: str = "import raes_contracts\n") -> Path:
    (tmp_path / "policy").mkdir()
    (tmp_path / "policy/repository.toml").write_text(POLICY, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (tmp_path / "uv.lock").write_text(LOCK, encoding="utf-8")
    (tmp_path / "src/lilrae").mkdir(parents=True)
    (tmp_path / "src/lilrae/example.py").write_text(source, encoding="utf-8")
    return tmp_path


def _rule_ids(root: Path) -> set[str]:
    return {finding.rule_id for finding in check_repository(root)}


def test_public_released_raes_dependency_is_allowed(tmp_path: Path) -> None:
    assert check_repository(_repository(tmp_path)) == []


@pytest.mark.parametrize(
    ("source", "rule_id"),
    [
        ("from raes_contracts._private import value\n", "RAES-IMPORT-PRIVATE"),
        ("import raes_reference_backend\n", "RAES-IMPORT-NONPUBLIC"),
        (
            "from implementations.python.packages.raes_contracts import value\n",
            "RAES-IMPORT-SOURCE",
        ),
        (
            'import importlib\nimportlib.import_module("raes_contracts._private")\n',
            "RAES-IMPORT-PRIVATE",
        ),
        (
            'import sys\nsys.path.insert(0, "../rae/implementations/python")\n',
            "RAES-PATH-MUTATION",
        ),
        (
            "import importlib.util\n"
            'importlib.util.spec_from_file_location("raes", "../rae/x.py")\n',
            "RAES-FILE-LOAD",
        ),
        (
            "import importlib.machinery\n"
            'importlib.machinery.SourceFileLoader("raes", "../rae/x.py")\n',
            "RAES-FILE-LOAD",
        ),
        (
            'import os\nos.putenv("PYTHONPATH", "../rae/implementations/python")\n',
            "RAES-PATH-MUTATION",
        ),
        (
            'import os\nos.environ["PYTHONPATH"] = "../rae/implementations/python"\n',
            "RAES-PATH-MUTATION",
        ),
    ],
)
def test_forbidden_import_and_loader_shapes_fail(tmp_path: Path, source: str, rule_id: str) -> None:
    assert rule_id in _rule_ids(_repository(tmp_path, source))


@pytest.mark.parametrize(
    "override",
    [
        'raes = { path = "../rae", editable = true }',
        'raes = { git = "https://github.com/RAESystem/rae.git" }',
        "raes = { workspace = true }",
    ],
)
def test_raes_source_overrides_fail(tmp_path: Path, override: str) -> None:
    root = _repository(tmp_path)
    (root / "pyproject.toml").write_text(
        PYPROJECT + "\n[tool.uv.sources]\n" + override + "\n",
        encoding="utf-8",
    )

    assert "RAES-DEPENDENCY-SOURCE" in _rule_ids(root)


def test_plain_raes_version_mismatch_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "pyproject.toml").write_text(
        PYPROJECT.replace("raes==3.3.0", "raes==2.0.0"),
        encoding="utf-8",
    )

    assert "RAES-DEPENDENCY-PIN" in _rule_ids(root)


def test_direct_url_dependency_fails_without_leaking_url_details(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "lilrae"
            version = "0.0.0"
            dependencies = [
              "raes @ https://alice:secret@example.invalid/rae.whl?token=value",
            ]
            """
        ),
        encoding="utf-8",
    )

    findings = check_repository(root)
    rendered = "\n".join(finding.message for finding in findings)
    assert "RAES-DEPENDENCY-SOURCE" in {finding.rule_id for finding in findings}
    assert "alice" not in rendered
    assert "secret" not in rendered
    assert "token=" not in rendered


def test_non_registry_lock_source_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "uv.lock").write_text(
        LOCK.replace(
            'source = { registry = "https://pypi.org/simple" }',
            'source = { git = "https://github.com/RAESystem/rae.git" }',
        ),
        encoding="utf-8",
    )

    assert "RAES-LOCK-SOURCE" in _rule_ids(root)


def test_wrong_raes_lock_version_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "uv.lock").write_text(
        LOCK.replace('version = "3.3.0"', 'version = "2.0.0"'),
        encoding="utf-8",
    )

    assert "RAES-LOCK-PIN" in _rule_ids(root)


def test_copied_raes_contract_tree_fails(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "contracts").mkdir()
    (root / "contracts/backend.json").write_text("{}\n", encoding="utf-8")

    assert "RAES-CONTRACT-COPY" in _rule_ids(root)


def test_non_python_configuration_cannot_add_raes_pythonpath(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / ".github/workflows").mkdir(parents=True)
    (root / ".github/workflows/ci.yml").write_text(
        'env:\n  PYTHONPATH: "../rae/implementations/python"\n',
        encoding="utf-8",
    )

    assert "RAES-CONFIG-SOURCE" in _rule_ids(root)


def test_repository_policy_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _repository(tmp_path)
    monkeypatch.setattr(repo_policy, "ROOT", root)
    assert repo_policy.main() == 0
    assert "OK" in capsys.readouterr().out

    (root / "src/lilrae/example.py").write_text(
        "import raes_reference_backend\n",
        encoding="utf-8",
    )
    assert repo_policy.main() == 1
    assert "RAES-IMPORT-NONPUBLIC" in capsys.readouterr().err


def test_malformed_policy_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "policy").mkdir()
    (tmp_path / "policy/repository.toml").write_text("schema_version = 2\n", encoding="utf-8")

    assert check_repository(tmp_path)[0].rule_id == "RAES-POLICY-SHAPE"
