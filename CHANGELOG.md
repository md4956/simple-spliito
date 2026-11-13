# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow [Semantic Versioning](https://semver.org/). While the major version is 0, breaking changes can happen in any minor release.

## [0.1.0] - 2026-11-14

First release.

### Added
- Settles balances with the fewest possible payments. The exact search covers up to 18 people with a balance to settle, and above that a faster method prints a note.
- Currency sections: a line starting with `@` sets the currency for the expenses after it. Each currency gets its own summary, balances, total and payments, separated by a `-----` line.
- Title: a comment on the first line of the file becomes the title.
- Inline comments: `#` starts a comment anywhere on a line.
- A total check line that shows the balances add up to zero.
- A summary line with the number of people and payments.
- Thousands separators in amounts.
- Plain-text output with no alignment, so it reads correctly when pasted into messengers or viewed on narrow screens.
- Warnings for `_` in names and in the title, and for `#` directly after a name. An error for `*` or `~` in names.
- A test suite (`python3 -m unittest discover -s tests`), including an exact-minimum check on random cases.

### Changed
- Balances show `gets` and `owes` instead of signed numbers, and are sorted largest first.
- Payments are grouped: people who pay once come first, then one block per person who pays several times.

### Fixed
- `nan`, `inf`, `Infinity` and out-of-range amounts such as `1e999` are rejected. They used to corrupt balances or hang the script.
- A space after a comma no longer creates an empty name.
- A line with only a comma after the amount is reported as an invalid list of people.
- Files saved with a byte-order mark at the start are read correctly.
