"""Discover, parse and merge Web of Science export files."""

from __future__ import annotations

import glob
import os
from typing import Iterable, List, Sequence, Union

import pandas as pd

from .parser import parse_wos_file

__all__ = [
    "looks_like_wos",
    "find_wos_files",
    "merge_wos_files",
    "deduplicate",
]

# How many lines to sniff when deciding whether a file is a WoS export.
_SNIFF_LINES = 40


def looks_like_wos(filepath: str) -> bool:
    """Return ``True`` if ``filepath`` looks like a WoS field-tagged export.

    The check is cheap and content-based: it reads the first few dozen lines
    and looks for the hallmarks of the WoS plain-text format — the ``FN``/``VR``
    header, a ``PT`` record-type tag, or an ``ER`` end-of-record marker. This
    lets the tool find exports no matter what they are named (``savedrecs.txt``,
    ``savedrecs (1).txt``, ``wos_batch3.txt``, ...), so you never have to spell
    out a glob pattern.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as handle:
            for index, raw_line in enumerate(handle):
                if index >= _SNIFF_LINES:
                    break
                line = raw_line.rstrip("\r\n")
                if line.startswith(("FN ", "VR ", "PT ")) or line.strip() == "ER":
                    return True
    except OSError:
        return False
    return False


def find_wos_files(
    inputs: Union[str, Sequence[str]],
    pattern: str | None = None,
    recursive: bool = True,
) -> List[str]:
    """Collect Web of Science export files from one or more paths.

    This is designed to "just work": point it at a folder and it finds every
    WoS export inside it, however deep and whatever the files are called.

    Parameters
    ----------
    inputs:
        A single path or a list of paths. Each path may be either:

        * a **file** — used directly, and
        * a **directory** — searched for WoS exports.

    pattern:
        Optional filename glob (e.g. ``"save*"`` or ``"*.txt"``). When given,
        only matching files inside a directory are considered. When ``None``
        (the default), files are detected automatically by their content via
        :func:`looks_like_wos`.
    recursive:
        When ``True`` (default), directories are searched at any depth. When
        ``False``, only the directory's immediate children are considered.

    Returns
    -------
    list of str
        A sorted, de-duplicated list of file paths.
    """
    if isinstance(inputs, str):
        inputs = [inputs]

    found: List[str] = []
    for path in inputs:
        if os.path.isfile(path):
            found.append(path)
        elif os.path.isdir(path):
            found.extend(_search_directory(path, pattern, recursive))
        # Silently ignore paths that do not exist here; the CLI validates and
        # reports them so library callers can decide for themselves.

    # Normalise and de-duplicate while preserving a stable, sorted order.
    unique = {os.path.normpath(p) for p in found}
    return sorted(unique)


def _search_directory(directory: str, pattern: str | None, recursive: bool) -> List[str]:
    """Return candidate WoS files inside a single directory."""
    if pattern:
        glob_pattern = os.path.join(directory, "**", pattern) if recursive else os.path.join(directory, pattern)
        candidates = glob.glob(glob_pattern, recursive=recursive)
        return [p for p in candidates if os.path.isfile(p)]

    # No pattern: walk the tree and keep files that look like WoS exports.
    results: List[str] = []
    if recursive:
        for root, _dirs, files in os.walk(directory):
            for name in files:
                full = os.path.join(root, name)
                if looks_like_wos(full):
                    results.append(full)
    else:
        for name in os.listdir(directory):
            full = os.path.join(directory, name)
            if os.path.isfile(full) and looks_like_wos(full):
                results.append(full)
    return results


def deduplicate(
    df: pd.DataFrame,
    title_col: str = "TI",
    doi_col: str = "DI",
) -> pd.DataFrame:
    """Drop duplicate records by title and by DOI.

    Records are de-duplicated first on the title column (keeping the first
    occurrence) and then on the DOI column, where rows whose DOI is a repeat
    of an earlier non-empty DOI are removed. Missing DOIs are never treated as
    duplicates of one another. Columns absent from ``df`` are skipped.
    """
    if title_col in df.columns:
        df = df.drop_duplicates(subset=[title_col])
    if doi_col in df.columns:
        df = df[~(df[doi_col].notna() & df[doi_col].duplicated())]
    return df


def merge_wos_files(files: Iterable[str]) -> pd.DataFrame:
    """Parse and concatenate every WoS file in ``files`` into one DataFrame.

    Files that fail to read are reported and skipped so that a single
    malformed file does not abort the whole merge.
    """
    frames: List[pd.DataFrame] = []
    for path in files:
        try:
            frame = parse_wos_file(path)
        except OSError as exc:
            print(f"Warning: could not read {path!r}: {exc}")
            continue
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)
