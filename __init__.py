"""wos_merge: parse and merge Web of Science export files into one CSV."""

from .merge import deduplicate, find_wos_files, looks_like_wos, merge_wos_files
from .parser import parse_wos_file

__version__ = "0.1.0"

__all__ = [
    "parse_wos_file",
    "looks_like_wos",
    "find_wos_files",
    "merge_wos_files",
    "deduplicate",
    "__version__",
]
