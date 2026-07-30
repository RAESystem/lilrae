#!/usr/bin/env python3
"""Validate LilRAE's dev-first pull-request routing."""

from __future__ import annotations

import argparse

RELEASE_PLEASE_BRANCH = "release-please--branches--main--components--lilrae"
RELEASE_PLEASE_AUTHOR = "github-actions[bot]"


def validate_pr_route(
    *,
    base: str,
    head: str,
    same_repository: bool,
    author: str,
) -> list[str]:
    """Return validation errors for a proposed pull-request route."""
    error: str | None = None
    if base == "dev":
        pass
    elif base != "main":
        error = f"pull requests must target dev or main, not {base!r}"
    elif not same_repository:
        error = "promotion and release pull requests must originate in RAESystem/lilrae"
    elif head == "dev":
        pass
    elif head != RELEASE_PLEASE_BRANCH or author != RELEASE_PLEASE_AUTHOR:
        error = "main accepts only dev promotion or the reviewed Release Please branch"
    return [error] if error else []


def main() -> int:
    """Validate pull-request route arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--same-repository", choices=("true", "false"), required=True)
    parser.add_argument("--author", required=True)
    args = parser.parse_args()
    errors = validate_pr_route(
        base=args.base,
        head=args.head,
        same_repository=args.same_repository == "true",
        author=args.author,
    )
    if errors:
        parser.error("; ".join(errors))
    print("pull-request route: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
