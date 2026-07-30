"""Canonical verification graph for LilRAE."""

from __future__ import annotations

import ast
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import nox

ROOT = Path(__file__).resolve().parent
NOX = "nox[uv]==2026.4.10"

nox.options.default_venv_backend = "none"
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["verify"]


def _run(session: nox.Session, *args: str, env: dict[str, str] | None = None) -> None:
    session.run(*args, external=True, env=env)


def _uv(session: nox.Session, *args: str) -> None:
    _run(session, "uv", "run", "--frozen", *args)


def _hygiene(session: nox.Session) -> None:
    _uv(session, "python", "-m", "tools.check_hygiene")


def _policy(session: nox.Session) -> None:
    _uv(session, "python", "-m", "tools.check_repo_policy")
    _uv(session, "python", "-m", "tools.check_project_services")


def _lint(session: nox.Session) -> None:
    _uv(session, "ruff", "format", "--check", ".")
    _uv(session, "ruff", "check", ".")


def _typecheck(session: nox.Session) -> None:
    _uv(session, "mypy")


def _tests(session: nox.Session) -> None:
    _uv(session, "coverage", "erase")
    _uv(session, "coverage", "run", "-m", "pytest")
    _uv(session, "coverage", "xml")
    _uv(session, "coverage", "report")


def _artifact_members(archive: Path) -> set[str]:
    if archive.suffix == ".whl":
        with zipfile.ZipFile(archive) as wheel:
            return set(wheel.namelist())
    with tarfile.open(archive) as source:
        return set(source.getnames())


def _canonical_version() -> str:
    tree = ast.parse((ROOT / "src/lilrae/_version.py").read_text(encoding="utf-8"))
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            continue
        value = ast.literal_eval(statement.value)
        if isinstance(value, str):
            return value
    raise ValueError("src/lilrae/_version.py must define a literal __version__")


def _build_smoke(session: nox.Session) -> None:
    temporary = Path(tempfile.mkdtemp(prefix="artifacts-", dir=session.create_tmp()))
    source_dist = temporary / "source"
    wheel_dist = temporary / "wheel"
    source_dist.mkdir()
    wheel_dist.mkdir()
    expected_version = _canonical_version()

    _uv(session, "python", "-c", "import hatchling")
    _run(
        session,
        "uv",
        "build",
        "--offline",
        "--no-build-isolation",
        "--sdist",
        "--out-dir",
        str(source_dist),
        str(ROOT),
    )
    source_archives = sorted(source_dist.glob("lilrae-*.tar.gz"))
    if len(source_archives) != 1:
        session.error(f"expected one source distribution, found {source_archives}")
    source_archive = source_archives[0]
    _run(
        session,
        "uv",
        "build",
        "--offline",
        "--no-build-isolation",
        "--wheel",
        "--out-dir",
        str(wheel_dist),
        str(source_archive),
    )
    wheels = sorted(wheel_dist.glob("lilrae-*.whl"))
    if len(wheels) != 1:
        session.error(f"expected one wheel, found {wheels}")
    wheel = wheels[0]

    source_members = _artifact_members(source_archive)
    wheel_members = _artifact_members(wheel)
    required_source_suffixes = {
        "/LICENSE",
        "/README.md",
        "/policy/repository.toml",
        "/src/lilrae/cli.py",
        "/tools/check_repo_policy.py",
    }
    missing_source = [
        suffix
        for suffix in required_source_suffixes
        if not any(member.endswith(suffix) for member in source_members)
    ]
    if missing_source:
        session.error(f"source distribution is missing: {missing_source}")
    required_wheel = {"lilrae/__init__.py", "lilrae/cli.py", "lilrae/py.typed"}
    if not required_wheel.issubset(wheel_members):
        session.error(f"wheel is missing: {sorted(required_wheel - wheel_members)}")
    if any("backend" in member.casefold() for member in wheel_members):
        session.error("backend-bearing modules are forbidden in the baseline wheel")

    environment = temporary / "environment"
    runtime_requirements = temporary / "runtime-requirements.txt"
    _run(
        session,
        "uv",
        "export",
        "--quiet",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--output-file",
        str(runtime_requirements),
    )
    _run(session, "uv", "venv", "--python", "3.11", str(environment))
    interpreter = (
        environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    ).absolute()
    command = (environment / ("Scripts/lilrae.exe" if os.name == "nt" else "bin/lilrae")).absolute()
    _run(
        session,
        "uv",
        "pip",
        "install",
        "--python",
        str(interpreter),
        "--no-deps",
        "--requirement",
        str(runtime_requirements),
    )
    _run(
        session,
        "uv",
        "pip",
        "install",
        "--offline",
        "--python",
        str(interpreter),
        "--no-deps",
        str(wheel),
    )

    clean_environment = os.environ.copy()
    clean_environment.pop("PYTHONPATH", None)
    clean_environment["PYTHONSAFEPATH"] = "1"
    clean_environment["EXPECTED_LILRAE_VERSION"] = expected_version
    with session.chdir(temporary):
        _run(
            session,
            str(interpreter),
            "-I",
            "-c",
            (
                "import importlib.metadata as metadata, os; import lilrae; "
                "assert metadata.version('lilrae') == lilrae.__version__ "
                "== os.environ['EXPECTED_LILRAE_VERSION']"
            ),
            env=clean_environment,
        )
        _run(session, str(command), "--help", env=clean_environment)
        _run(session, str(command), "--version", env=clean_environment)


@nox.session
def hygiene(session: nox.Session) -> None:
    _hygiene(session)


@nox.session
def policy(session: nox.Session) -> None:
    _policy(session)


@nox.session
def lint(session: nox.Session) -> None:
    _lint(session)


@nox.session
def typecheck(session: nox.Session) -> None:
    _typecheck(session)


@nox.session
def tests(session: nox.Session) -> None:
    _tests(session)


@nox.session(name="build-smoke")
def build_smoke(session: nox.Session) -> None:
    _build_smoke(session)


@nox.session
def verify(session: nox.Session) -> None:
    _hygiene(session)
    _policy(session)
    _lint(session)
    _typecheck(session)
    _tests(session)
    _build_smoke(session)


@nox.session(name="pr-policy")
def pr_policy(session: nox.Session) -> None:
    _uv(session, "python", "tools/check_pr_policy.py", *session.posargs)


@nox.session(name="hook-pre-commit")
def hook_pre_commit(session: nox.Session) -> None:
    _hygiene(session)
    _policy(session)
    _lint(session)


@nox.session(name="hook-pre-push")
def hook_pre_push(session: nox.Session) -> None:
    _hygiene(session)
    _policy(session)
    _lint(session)
    _typecheck(session)
    _tests(session)
    _build_smoke(session)


if __name__ == "__main__":
    sys.exit(f"Run with: uv tool run --from '{NOX}' nox")
