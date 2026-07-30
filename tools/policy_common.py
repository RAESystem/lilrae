from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, order=True)
class Finding:
    rule_id: str
    path: str
    message: str


def load_repository_policy(root: Path) -> dict[str, Any]:
    path = root / "policy/repository.toml"
    with path.open("rb") as handle:
        policy: dict[str, Any] = tomllib.load(handle)
    if policy.get("schema_version") != 1:
        raise ValueError("policy/repository.toml must use schema_version = 1")
    return policy


def relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
