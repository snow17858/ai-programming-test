from pathlib import Path
import pytest

from load_scores import load_scores


def write_csv(tmp_path: Path, filename: str, content: str) -> Path:
    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8-sig", newline="")
    return file_path


def test_normal_scores(tmp_path: Path):
    csv_path = write_csv(
        tmp_path,
        "scores.csv",
        "name,score\n김하나,88\n이둘,95\n",
    )
    kept, skipped = load_scores(csv_path)
    assert kept == [("김하나", 88), ("이둘", 95)]
    assert skipped == []


def test_empty_lines_ignored_without_skip_record(tmp_path: Path):
    csv_path = write_csv(
        tmp_path,
        "empty_lines.csv",
        "name,score\n\n김하나,80\n   \n박셋,90\n",
    )
    kept, skipped = load_scores(csv_path)
    assert kept == [("김하나", 80), ("박셋", 90)]
    assert skipped == []


def test_quoted_name_with_comma(tmp_path: Path):
    csv_path = write_csv(
        tmp_path,
        "comma_name.csv",
        'name,score\n"홍,길동",77\n',
    )
    kept, skipped = load_scores(csv_path)
    assert kept == [("홍,길동", 77)]
    assert skipped == []


def test_duplicate_names_kept_both(tmp_path: Path):
    csv_path = write_csv(
        tmp_path,
        "dup.csv",
        "name,score\n김철수,70\n김철수,85\n",
    )
    kept, skipped = load_scores(csv_path)
    assert kept == [("김철수", 70), ("김철수", 85)]
    assert skipped == []


def test_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_scores("does_not_exist_12345.csv")


def test_header_only_returns_empty_lists(tmp_path: Path):
    csv_path = write_csv(tmp_path, "header_only.csv", "name,score\n")
    kept, skipped = load_scores(csv_path)
    assert kept == []
    assert skipped == []


def test_invalid_rows_recorded_in_skipped(tmp_path: Path):
    csv_path = write_csv(
        tmp_path,
        "invalid_rows.csv",
        "name,score\n"
        "만점자,100\n"
        "영점자,0\n"
        "열부족\n"
        "열과다,50,extra\n"
        " ,50\n"
        "빈점수,\n"
        "문자점수,abc\n"
        "음수점수,-1\n"
        "초과점수,101\n",
    )
    kept, skipped = load_scores(csv_path)
    assert kept == [("만점자", 100), ("영점자", 0)]
    assert skipped == [
        (4, "열부족", "열 개수가 2가 아님"),
        (5, "열과다,50,extra", "열 개수가 2가 아님"),
        (6, " ,50", "이름이 비어 있음"),
        (7, "빈점수,", "점수가 비어 있음"),
        (8, "문자점수,abc", "점수가 정수가 아님"),
        (9, "음수점수,-1", "점수가 0~100 밖"),
        (10, "초과점수,101", "점수가 0~100 밖"),
    ]


@pytest.mark.parametrize(
    "score_text,expected_valid,expected_reason",
    [
        ("-1", False, "점수가 0~100 밖"),
        ("0", True, None),
        ("1", True, None),
        ("99", True, None),
        ("100", True, None),
        ("101", False, "점수가 0~100 밖"),
        ("", False, "점수가 비어 있음"),
        ("abc", False, "점수가 정수가 아님"),
    ],
)
def test_score_boundaries_and_edge_cases(tmp_path: Path, score_text, expected_valid, expected_reason):
    csv_path = write_csv(tmp_path, "boundary.csv", f"name,score\n테스트,{score_text}\n")
    kept, skipped = load_scores(csv_path)
    if expected_valid:
        assert kept == [("테스트", int(score_text))]
        assert skipped == []
    else:
        assert kept == []
        assert len(skipped) == 1
        assert skipped[0][2] == expected_reason