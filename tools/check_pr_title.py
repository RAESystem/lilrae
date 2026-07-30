#!/usr/bin/env python3
"""Validate Conventional Commit pull-request titles."""

from __future__ import annotations

import argparse
import re

TITLE = re.compile(
    r"^(added|build|changed|chore|ci|deprecated|docs|feat|fix|perf|refactor|"
    r"removed|revert|security|test)(\([a-z0-9][a-z0-9-]*\))?: [a-z0-9].+$"
)
ATTRIBUTION = re.compile(
    r"(codex|claude|openai|anthropic|generated[- ]by|co-authored-by|\bai[- ]generated\b)",
    re.IGNORECASE,
)


def validate_title(title: str) -> str | None:
    """Return a validation error for a non-conforming pull-request title."""
    if ATTRIBUTION.search(title):
        return "pull-request titles must not contain tool or generated-by attribution"
    if not TITLE.fullmatch(title):
        return "use a Conventional Commit type and a lowercase subject"
    return None


def main() -> int:
    """Validate a pull-request title supplied on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    args = parser.parse_args()
    error = validate_title(args.title)
    if error:
        parser.error(error)
    print("pull-request title: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
