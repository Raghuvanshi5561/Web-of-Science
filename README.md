# wos-merge

Parse [Web of Science](https://www.webofscience.com/) (WoS) plain-text export
files and merge them into a single, de-duplicated CSV.

When you export records from Web of Science in several batches (WoS caps each
export, so a large query becomes many `savedrecs.txt` files spread across
folders), this tool reads every export, combines them, removes duplicate
records by title and DOI, and writes one tidy CSV you can load into pandas,
Excel, or a reference manager.

## Features

- **Point-and-go file discovery** — just give it a folder and it finds every
  WoS export inside, at any depth, no matter what the files are named. It
  recognizes exports by their content, so you never have to write a glob.
- Accepts **multiple folders and/or individual files** in one command.
- A **`--list` preview** shows exactly which files will be merged before you
  commit to writing anything.
- Parses the WoS field-tagged plain-text format (two-letter tags such as `TI`,
  `AU`, `SO`, `DI`), including multi-line continuation values.
- De-duplicates by title (`TI`) and by DOI (`DI`).
- Cross-platform (Windows, macOS, Linux) — no hard-coded paths.
- Usable from the command line or as a small Python library.

## Installation

Clone the repository and install it (a virtual environment is recommended):

```bash
git clone https://github.com/your-username/wos-merge.git
cd wos-merge
pip install .
```

Or install just the dependency and run from source:

```bash
pip install -r requirements.txt
```

## Usage

### Command line

```bash
wos-merge /path/to/Data_Aditya_Sir
```

This searches the folder (and every sub-folder) for Web of Science exports,
automatically recognizing them by their content, merges them, de-duplicates,
and writes `Merge_WOS.csv` inside the folder.

If you installed from source without the console script, the equivalent is:

```bash
python -m wos_merge /path/to/Data_Aditya_Sir
```

Common options:

```bash
# Preview which files would be merged, without writing anything
wos-merge ./exports --list

# Merge several folders and/or individual files at once
wos-merge ./batch1 ./batch2 extra_export.txt

# Choose where the merged CSV goes
wos-merge ./exports -o merged.csv

# Only look at a folder's top level (don't search sub-folders)
wos-merge ./exports --no-recursive

# Restrict to files whose name matches a glob, if you prefer
wos-merge ./exports --pattern "save*"

# Keep duplicates
wos-merge ./exports --no-dedup
```

Run `wos-merge --help` for the full list of options.

### As a library

```python
from wos_merge import find_wos_files, merge_wos_files, deduplicate

files = find_wos_files("exports")          # auto-detects WoS files recursively
df = merge_wos_files(files)
df = deduplicate(df)                        # drop duplicate titles and DOIs
df.to_csv("Merge_WOS.csv", index=False)

# You can also pass several paths, or an explicit glob:
files = find_wos_files(["batch1", "batch2", "extra.txt"])
files = find_wos_files("exports", pattern="save*", recursive=False)
```

## Input format

A WoS plain-text export is a series of records, each a block of `TAG value`
lines terminated by `ER`:

```
FN Clarivate Analytics Web of Science
VR 1.0
PT J
AU Doe, J
   Smith, A
TI A study of something interesting
SO JOURNAL OF EXAMPLES
DI 10.1000/example.doi
ER

PT J
...
ER
EF
```

Each record becomes one row; each tag becomes a column. Repeated tags within a
record are joined with `"; "`.

## Development

```bash
pip install -r requirements.txt
python -m pytest        # if you add tests under tests/
```

## License

Released under the [MIT License](LICENSE).
