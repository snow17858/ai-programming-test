from pathlib import Path
import pytest

from load_scores import load_scores


def make_csv(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_scores("non_existent_file_xyz.csv")


def test_header_only_returns_empty_tuple(tmp_path: Path):
    p = make_csv(tmp_path, "only_header.csv", "name,score\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert skipped == []


def test_normal_entries(tmp_path: Path):
    p = make_csv(tmp_path, "normal.csv", "name,score\nAlice,90\nBob,75\n")
    kept, skipped = load_scores(p)
    assert kept == [("Alice", 90), ("Bob", 75)]
    assert skipped == []


def test_duplicate_names_are_both_kept(tmp_path: Path):
    p = make_csv(tmp_path, "dup.csv", "name,score\nLee,60\nLee,80\n")
    kept, skipped = load_scores(p)
    assert kept == [("Lee", 60), ("Lee", 80)]
    assert skipped == []


@pytest.mark.parametrize(
    "line,expected_line_no",
    [
        ("OnlyOneCol", 2),
        ("A,10,extra", 2),
        (",50", 2),
        ("   ,50", 2),
        ("Alice,", 2),
        ("Alice,abc", 2),
        ("Alice,12.5", 2),
        ("Alice,-1", 2),
        ("Alice,101", 2),
    ],
)
def test_invalid_rows_are_skipped_with_record(tmp_path: Path, line: str, expected_line_no: int):
    p = make_csv(tmp_path, "bad.csv", f"name,score\n{line}\n")
    kept, skipped = load_scores(p)
    assert kept == []
    assert len(skipped) == 1
    line_no, raw_line, reason = skipped[0]
    assert line_no == expected_line_no
    assert isinstance(raw_line, str) and len(raw_line) > 0
    assert isinstance(reason, str) and len(reason) > 0


@pytest.mark.parametrize("score_val,is_valid", [
    (-1, False),
    (0, True),
    (1, True),
    (99, True),
    (100, True),
    (101, False),
])
def test_score_boundaries(tmp_path: Path, score_val: int, is_valid: bool):
    p = make_csv(tmp_path, "bounds.csv", f"name,score\nUser,{score_val}\n")
    kept, skipped = load_scores(p)
    if is_valid:
        assert kept == [("User", score_val)]
        assert skipped == []
    else:
        assert kept == []
        assert len(skipped) == 1