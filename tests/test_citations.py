from app.rag.citations import extract_citations


def test_extract_citations_splits_valid_and_invalid_numbers() -> None:
    valid, invalid = extract_citations("结论 [1][3]，另一个说法 [5]，重复 [1]。", 3)

    assert valid == [1, 3]
    assert invalid == [5]


def test_extract_citations_handles_missing_citations() -> None:
    assert extract_citations("没有引用。", 3) == ([], [])
