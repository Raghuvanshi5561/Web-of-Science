"""Parsing utilities for Web of Science (WoS) plain-text export files.

A WoS "plain text" / "tab-delimited" field-tagged export looks like this::

    FN Clarivate Analytics Web of Science
    VR 1.0
    PT J
    AU Doe, J
       Smith, A
    TI A study of something interesting
    SO JOURNAL OF EXAMPLES
    DI 10.1000/example.doi
    ...
    ER

    PT J
    ...
    ER
    EF

Each record is a block of ``TAG value`` lines terminated by an ``ER`` line.
A two-letter tag starts in column 1 and is followed by a space in column 3.
Lines that are indented (they begin with spaces) are *continuation* lines
that belong to the most recently seen tag.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

__all__ = ["parse_wos_file"]

# File-level header/footer tags that are not part of any record.
_SKIP_TAGS = {"FN", "VR", "EF"}


def parse_wos_file(filepath: str) -> pd.DataFrame:
    """Parse a single WoS field-tagged export file into a DataFrame.

    Each row of the returned DataFrame is one WoS record and each column is a
    two-letter WoS field tag (``TI``, ``AU``, ``DI``, ...). When a tag appears
    more than once in a record its values are joined with ``"; "``.

    Parameters
    ----------
    filepath:
        Path to a WoS plain-text export file (for example ``savedrecs.txt``).

    Returns
    -------
    pandas.DataFrame
        One row per record; columns are the tags found in the file.
    """
    records: List[Dict[str, str]] = []
    record: Dict[str, str] = {}
    current_tag: str | None = None

    # ``utf-8-sig`` transparently strips a leading BOM if one is present.
    with open(filepath, "r", encoding="utf-8-sig") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\r\n")

            # End of one record.
            if line.strip() == "ER":
                if record:
                    records.append(record)
                record = {}
                current_tag = None
                continue

            # Blank separator line.
            if not line.strip():
                continue

            tag = line[:2]

            # File-level header/footer information, not record data.
            if tag in _SKIP_TAGS:
                continue

            # Continuation line: begins with whitespace, so it extends the
            # value of the most recently seen tag.
            if tag.strip() == "":
                value = line.strip()
                if current_tag and value:
                    record[current_tag] += " " + value
                continue

            # A proper field line has a space in the third column.
            if len(line) >= 3 and line[2] == " ":
                value = line[3:].strip()
                current_tag = tag
                if tag in record:
                    record[tag] += "; " + value
                else:
                    record[tag] = value

    # A final record not terminated by ER (rare, but be forgiving).
    if record:
        records.append(record)

    return pd.DataFrame(records)
