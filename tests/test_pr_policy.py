from __future__ import annotations

import pytest

import tools.check_pr_policy as pr_policy
from tools.check_pr_policy import validate_pr_route


@pytest.mark.parametrize(
    ("base", "head", "author"),
    [
        ("dev", "2-establish-repository-baseline", "contributor"),
        ("dev", "main", "contributor"),
        ("main", "dev", "contributor"),
        (
            "main",
            "release-please--branches--main--components--lilrae",
            "github-actions[bot]",
        ),
    ],
)
def test_allowed_pr_routes(base: str, head: str, author: str) -> None:
    assert (
        validate_pr_route(
            base=base,
            head=head,
            same_repository=True,
            author=author,
        )
        == []
    )


@pytest.mark.parametrize(
    ("base", "head", "same_repository", "author"),
    [
        ("main", "feature-direct-to-main", True, "contributor"),
        ("main", "dev", False, "contributor"),
        (
            "main",
            "release-please--branches--main--components--lilrae",
            False,
            "github-actions[bot]",
        ),
        (
            "main",
            "release-please--branches--main--components--lilrae",
            True,
            "contributor",
        ),
        ("other", "feature", True, "contributor"),
    ],
)
def test_disallowed_pr_routes(
    base: str,
    head: str,
    same_repository: bool,
    author: str,
) -> None:
    assert validate_pr_route(
        base=base,
        head=head,
        same_repository=same_repository,
        author=author,
    )


def test_pr_policy_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "check-pr-policy",
            "--base",
            "main",
            "--head",
            "dev",
            "--same-repository",
            "true",
            "--author",
            "contributor",
        ],
    )
    assert pr_policy.main() == 0
    assert "OK" in capsys.readouterr().out

    monkeypatch.setattr(
        "sys.argv",
        [
            "check-pr-policy",
            "--base",
            "main",
            "--head",
            "feature",
            "--same-repository",
            "true",
            "--author",
            "contributor",
        ],
    )
    with pytest.raises(SystemExit) as exit_info:
        pr_policy.main()
    assert exit_info.value.code == 2
