from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from lilrae import __version__
from lilrae.cli import build_parser, main

ROOT = Path(__file__).resolve().parents[1]


def test_public_package_and_cli_have_one_identity() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert project["name"] == "lilrae"
    assert project["scripts"] == {"lilrae": "lilrae.cli:main"}
    assert project["dependencies"] == ["raes==3.3.0"]
    assert project["requires-python"] == ">=3.11"
    assert "Programming Language :: Python :: 3.11" in project["classifiers"]
    assert "Programming Language :: Python :: 3.12" in project["classifiers"]
    assert __version__


def test_cli_reports_the_distribution_version_without_backend_claims() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lilrae.cli", "--version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"lilrae {__version__}"
    assert "backend" not in result.stdout.lower()


def test_cli_help_exposes_no_execution_surface() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lilrae.cli", "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "reference backend" not in result.stdout.lower()
    for unsupported_command in ("run", "start", "provision", "execute"):
        assert unsupported_command not in result.stdout.lower().split()


def test_cli_entrypoint_help_and_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert build_parser().prog == "lilrae"
    main([])
    assert "Inspect the installed LilRAE distribution." in capsys.readouterr().out

    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"lilrae {__version__}"
