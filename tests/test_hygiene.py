from __future__ import annotations

from pathlib import Path

import pytest

import tools.check_hygiene as hygiene
from tools.check_hygiene import check_hygiene


def _rule_ids(root: Path) -> set[str]:
    return {finding.rule_id for finding in check_hygiene(root)}


def test_clean_text_yaml_and_json_pass(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("clean\n", encoding="utf-8")
    (tmp_path / "file.yml").write_text("key: value\n", encoding="utf-8")
    (tmp_path / "file.json").write_text('{"key": "value"}\n', encoding="utf-8")

    assert check_hygiene(tmp_path) == []


def test_text_hygiene_failures_are_reported(tmp_path: Path) -> None:
    content = "trailing \n" + "<" * 7 + " branch\n"
    (tmp_path / "file.txt").write_text(content, encoding="utf-8")

    assert {"HYGIENE-WHITESPACE", "HYGIENE-MERGE"} <= _rule_ids(tmp_path)


def test_missing_final_newline_is_reported(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("missing", encoding="utf-8")

    assert "HYGIENE-EOF" in _rule_ids(tmp_path)


def test_invalid_structured_files_are_reported(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{\n", encoding="utf-8")
    (tmp_path / "bad.yaml").write_text("key: [\n", encoding="utf-8")

    assert {"HYGIENE-JSON", "HYGIENE-YAML"} <= _rule_ids(tmp_path)


def test_private_key_material_is_reported_without_content(tmp_path: Path) -> None:
    (tmp_path / "key.txt").write_text(
        "-----BEGIN " + "PRIVATE KEY-----\nnot-a-real-key\n",
        encoding="utf-8",
    )

    findings = check_hygiene(tmp_path)
    assert "HYGIENE-PRIVATE-KEY" in {finding.rule_id for finding in findings}
    assert "not-a-real-key" not in "\n".join(finding.message for finding in findings)


def test_large_and_binary_files_are_bounded(tmp_path: Path) -> None:
    (tmp_path / "large.bin").write_bytes(b"\0" + b"x" * (501 * 1024))

    assert "HYGIENE-LARGE-FILE" in _rule_ids(tmp_path)


def test_hygiene_cli_reports_success_and_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "clean.txt").write_text("clean\n", encoding="utf-8")
    monkeypatch.setattr(hygiene, "ROOT", tmp_path)
    assert hygiene.main() == 0
    assert "OK" in capsys.readouterr().out

    (tmp_path / "bad.txt").write_text("bad", encoding="utf-8")
    assert hygiene.main() == 1
    captured = capsys.readouterr()
    assert "HYGIENE-EOF" in captured.err
