"""Reads CHANGELOG.md for the release workflow and the tests.

    python3 scripts/release.py latest         print the newest version, such as 3.0.0
    python3 scripts/release.py notes 3.0.0    print the changelog notes for one version
"""

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$", re.MULTILINE)


def sections(text=None):
    """Return (version, date, notes) for each release, in the order the changelog lists them."""
    if text is None:
        text = CHANGELOG.read_text(encoding="utf-8")
    matches = list(HEADING.finditer(text))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result.append((match.group(1), match.group(2), text[match.end():end].strip()))
    return result


def latest():
    """The newest version, which is the one with the highest number, not the first listed."""
    return max((version for version, _, _ in sections()), key=lambda v: tuple(map(int, v.split("."))))


def notes(version):
    for listed, _, body in sections():
        if listed == version:
            return body
    raise SystemExit(f"No changelog section for {version}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["latest"]:
        print(latest())
    elif sys.argv[1:2] == ["notes"] and len(sys.argv) == 3:
        print(notes(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
