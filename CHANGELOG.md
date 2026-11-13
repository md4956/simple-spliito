# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow [Semantic Versioning](https://semver.org/). Versions before 1.0.0 may change behavior in a minor release.

## [1.0.0] - 2026-11-14

First stable release. Its behavior matches 0.9.0, plus the changelog and a download link in the README. From this version on, changing the input format or the output format needs a major version bump.

### Added
- This changelog, and a link to the latest release in the README.

## [0.9.0] - 2026-11-14

### Added
- Currency sections: a line starting with `@` sets the currency for the expenses after it. Each currency gets its own summary, balances, total and payments, with every heading naming the currency and a `-----` line between sections. Single-currency files have no separator. Plain-number expenses in a multi-currency file are labelled `NO CURRENCY`.
- A title: a comment on the first line of the file becomes the title.
- Warnings for `_`, `*` and `~` in the title. The title is still printed as typed.
- A test suite (`python3 -m unittest discover -s tests`), including a check of the settlement against an exact solver on random cases.

### Fixed
- Files saved with a byte-order mark at the start are read correctly.

## [0.8.0] - 2026-11-13

### Added
- Inline comments: `#` starts a comment anywhere on a line. A `#` directly after a name, such as `mia#2`, triggers a warning.
- A total check line under the balances, showing that the balances add up to zero.
- Plain-text output for messengers and narrow screens: no alignment, one payment per line, upper-case headings, a summary line, and thousands separators.

### Changed
- Balances show `gets` and `owes` instead of signed numbers, sorted largest first.
- Payments are grouped by payer. People who pay once come first, then one block per person who pays several times.

## [0.7.0] - 2026-11-13

### Added
- Fewest payments: the settlement uses the minimum number of payments for up to 18 people with a balance. Above that, a faster method runs and the script prints a note.
- Rejects `*` and `~` in names with an error, and warns about `_`.

### Fixed
- `nan`, `inf`, `Infinity` and out-of-range amounts such as `1e999` are rejected. They used to corrupt balances or hang the script.
- A space after a comma no longer creates an empty name.
- A line with only a comma after the amount is reported as an invalid list of people.

## [0.6.1] - 2026-11-06

### Changed
- Renamed the script to `simple-spliito.py` to match the repository name, and fixed the usage message.

## [0.6.0] - 2026-11-05

### Added
- Lines starting with `#` are comments.
- A README and a full-feature example file.

## [0.5.0] - 2026-11-05

The first version kept in this repository: `spliter` v0.5, a command-line tool that settles shared expenses from a text file. Versions 0.1 to 0.4 were developed locally before the repository was created, and their history isn't here.
