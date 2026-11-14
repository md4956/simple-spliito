# simple-spliito

A small tool for splitting shared expenses. You write down who paid what and who it was for in a text file (`.txt` or `.md`). It prints the fewest payments that settle everyone up, and each person's balance.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Web version (phone and desktop)

The same tool runs as a web page: **https://md4956.github.io/simple-spliito/** (the `docs` folder, published with GitHub Pages). Nothing is sent to a server.

1. Paste your expenses into the box, or tap **Load .txt or .md**. You can also drop a file anywhere on the page.
2. Tap **Calculate**. Ctrl+Enter or ⌘+Enter works too.
3. Read the report, or tap **Copy report** to paste it into a messenger.

**Download** saves the expenses as a `.txt` or `.md` file, matching the file you loaded. The page works offline after the first visit. To keep it on the home screen, use "Add to Home Screen" in Safari or Chrome.

The page shows the same report as the script. How to write the expenses is explained in [Quick start](#quick-start) and [Input format](#input-format).

## Quick start

Download `simple-spliito.py` from the [latest release](https://github.com/md4956/simple-spliito/releases/latest), or clone the repo.

Save this as `dinner.txt` (or `dinner.md`, which works the same way):

```
# Dinner
ana 60 ana ben cy
ben 30 ben cy
```

Run it:

```bash
python3 simple-spliito.py dinner.txt
```

To run the tests (they only use the Python standard library):

```bash
python3 -m unittest discover -s tests
```

The web page has browser tests (layout, input, buttons, page loading, output text and files, offline). They need Node.js 22 or newer and Chrome; set `CHROME_PATH` if Chrome is not in a standard place:

```bash
node --test tests/web/
```

You get:

```
Dinner

PAYMENTS
cy pays ana 35.00
ben pays ana 5.00

BALANCES
ana gets 40.00
ben owes 5.00
cy owes 35.00

3 people, 2 payments, total 0.00
```

- The first line of the file becomes the title.
- **PAYMENTS** is the answer. `cy pays ana 35.00` means cy should pay ana 35.00. The two payments settle everyone.
- **BALANCES** shows what each person gets or owes. `ana gets 40.00` means ana should receive 40.00.

That's all you need for most trips. The rest of this page covers the other features.

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

The amount is split equally between the people listed after it. The payer only gets a share if they list themselves. So `ana 60 ana ben cy` splits 60 three ways and includes ana, while `tom 415 max` means tom paid the whole amount for max.

Other rules:

- **File type:** only `.txt` and `.md` files are accepted, and any other file (including one without an extension) stops with `Unsupported file type`. `.txt` and `.md` files are read the same way. In a `.md` file, don't use Markdown syntax for expenses: a list bullet (`- ana 60 ana ben`) or a code fence (```` ``` ````) is read as plain text, so the line is skipped and listed under WARNINGS.
- **Names** can be separated by spaces, commas or both: `nik 640.5 nik eva tom,ivy` and `nik 640.5 nik, eva, tom, ivy` mean the same thing.
- **Repeated names** get more shares. `sam 900 sam ana ana lia` splits 900 into four parts, and ana owes two of them. Numbers are allowed in names, so `mia1 mia2 mia3` are three people.
- **Decimals** work: `362.75`. Amounts that aren't finite numbers (`nan`, `inf`, `1e999`) are rejected.
- **Comments:** `#` starts a comment, and everything after it on that line is ignored. A comment can take a whole line or follow an expense: `dan 210 mia1 mia2 mia3 # mias are cousins`.
- **Blank lines** are ignored.
- **Names can't contain `#`, `*` or `~`.** A `*` or `~` stops with an error, and no report is printed. A `_` is allowed, but it gets a warning, because messengers can turn the text between two underscores into italics.
- **A `#` directly after a name**, like `mia#2`, still starts a comment. It gets a warning, and the name is read as `mia`.
- **The title** comes from a comment on the first line of the file. `# Weekend trip` at the top makes `Weekend trip` the title. If the first line isn't a comment, there's no title.
- **Currencies** are covered below.
- **Other lines** that don't match the format are skipped and listed under WARNINGS. Watch out for plain-text notes whose second word is a number, such as `Notes: 100 euros total`, because those are read as an expense.
- **No expenses at all** (an empty file, or only lines that couldn't be read) prints a short guide on how to write one, instead of an empty report.

## Currencies

A line starting with `@` sets the currency for the expenses after it:

- `@EUR` switches to euros.
- `@` on its own switches back to plain numbers.

If a file uses more than one currency, the report has a section for each one. Each section's heading names its currency, such as `PAYMENTS (EUR)`, and every amount shows it too. A single currency has no divider. The script never converts between currencies, so each section settles on its own.

```
# Trip, two currencies
@EUR
nik 50 nik eva
ana 30 ana eva
@
bob 40 bob cy
```

```
Trip, two currencies

PAYMENTS (EUR)
eva pays nik 25.00 EUR
eva pays ana 15.00 EUR

BALANCES (EUR)
nik gets 25.00 EUR
ana gets 15.00 EUR
eva owes 40.00 EUR

3 people, 2 payments, total 0.00 EUR

PAYMENTS (NO CURRENCY)
cy pays bob 20.00

BALANCES (NO CURRENCY)
bob gets 20.00
cy owes 20.00

2 people, 1 payment, total 0.00
```

Expenses before the first `@` line, and after an `@` line with nothing after it, use plain numbers. Plain numbers always come last, under the `NO CURRENCY` heading.

## Full example

[`example-expenses.txt`](example-expenses.txt) uses every input feature. [`example-expenses.md`](example-expenses.md) is the same file as Markdown:

```bash
python3 simple-spliito.py example-expenses.txt
```

```
Weekend trip expenses

PAYMENTS
ivy pays sam 931.79
ben pays sam 842.33
ana pays lia 696.67
max pays joe 730.67
max pays nik 46.96
max pays sam 42.46
max pays lia 14.58
tom pays eva 246.54
tom pays lia 1.25

BALANCES
sam gets 1,816.58
joe gets 730.67
lia gets 712.50
eva gets 246.54
nik gets 46.96
tom owes 247.79
ana owes 696.67
max owes 834.67
ben owes 842.33
ivy owes 931.79

10 people, 9 payments, total 0.00
```

How to read the output:

- **PAYMENTS** comes first, one payment per line. Read this section first: it's enough to settle the trip. People who pay only once are listed first, sorted by amount. Then each person who pays several times, also sorted by amount, so their payments are next to each other.
- If nothing is owed, the payments section says `Everyone is settled.`
- **BALANCES** lists everyone, largest first. `gets` means the person should receive money, and `owes` means they should pay. A person with nothing to settle shows `is settled`.
- The last line gives the number of people and payments, and the total. The total should always be `0.00`, because every expense takes money from the people who share it and gives it to the payer. If it isn't, the script has a calculation bug, not a problem with your input.
- **WARNINGS**, when there are any, comes last. It lists the lines that were skipped and the notes about names and the title, each with the line it refers to.

The output is plain text with short lines and no decoration, so it reads the same when pasted into a messenger or viewed on a narrow phone screen. The web page, the file and the command line all print this same format.

The format is versioned. This README describes version 3.0.0 (see the [changelog](CHANGELOG.md)).

## Versions and releases

Each version in [CHANGELOG.md](CHANGELOG.md) has a [GitHub release](https://github.com/md4956/simple-spliito/releases) with `simple-spliito.py` attached. The newest version is marked as the latest release, and that's the one the download link above points to.

Releases are automatic. When a change that adds a version is merged to `main`, the release workflow (`.github/workflows/release.yml`) creates that version's release, with its CHANGELOG section as the notes. Pushes that don't add a version create nothing.

To publish a new version, in the same pull request:

1. Add a CHANGELOG section with the new version and today's date, above the previous one.
2. Update the "This README describes version" line above to the new version.
3. Merge to `main`. The tests check that steps 1 and 2 agree.

## Limitations

- Splits are always equal, apart from naming someone more than once.
- Names are case-sensitive.
- The fewest payments are only guaranteed for up to 18 people with a balance to settle. Above that, the exact search would take too long, so the script adds a note to WARNINGS and uses a faster method that may list extra payments.
- Amounts are plain floats, shown rounded to two decimals with thousands separators (`1,816.58`).
- The script doesn't convert between currencies.
