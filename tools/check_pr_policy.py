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
    if base == "dev":
        return []
    if base != "main":
        return [f"pull requests must target dev or main, not {base!r}"]
    if not same_repository:
        return ["promotion and release pull requests must originate in RAESystem/lilrae"]
    if head == "dev":
        return []
    if head == RELEASE_PLEASE_BRANCH and author == RELEASE_PLEASE_AUTHOR:
        return []
    return ["main accepts only dev promotion or the reviewed Release Please branch"]


def main() -> int:
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
