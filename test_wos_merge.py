"""Basic tests for wos_merge, runnable with pytest."""

import os

from wos_merge import (
    deduplicate,
    find_wos_files,
    looks_like_wos,
    merge_wos_files,
    parse_wos_file,
)

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")
BATCH1 = os.path.join(EXAMPLES, "batch1", "savedrecs.txt")


def test_parse_single_file():
    df = parse_wos_file(BATCH1)
    assert len(df) == 2
    # Continuation line should be folded into the title.
    assert "broadband widgets" in df.iloc[1]["TI"]
    # Multiple authors arrive as continuation lines, folded with a space.
    assert df.iloc[0]["AU"] == "Doe, J Smith, A"


def test_looks_like_wos(tmp_path):
    assert looks_like_wos(BATCH1) is True
    not_wos = tmp_path / "notes.txt"
    not_wos.write_text("just some random text\nno tags here\n")
    assert looks_like_wos(str(not_wos)) is False


def test_auto_detect_by_content():
    # No pattern needed: point at the folder and it finds both exports.
    files = find_wos_files(EXAMPLES)
    assert len(files) == 2
    df = merge_wos_files(files)
    assert len(df) == 4  # two records per file


def test_accepts_multiple_paths():
    files = find_wos_files(
        [os.path.join(EXAMPLES, "batch1"), os.path.join(EXAMPLES, "batch2")]
    )
    assert len(files) == 2


def test_accepts_individual_file():
    files = find_wos_files(BATCH1)
    assert files == [os.path.normpath(BATCH1)]


def test_pattern_override():
    files = find_wos_files(EXAMPLES, pattern="save*")
    assert len(files) == 2


def test_deduplicate_by_doi_and_title():
    df = deduplicate(merge_wos_files(find_wos_files(EXAMPLES)))
    # The duplicated record (example.0002) should be collapsed to one.
    assert len(df) == 3
    assert df["DI"].is_unique
