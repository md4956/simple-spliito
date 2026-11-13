# simple-spliito

A small command-line tool for splitting shared expenses. You give it a text file listing who paid what and who it was for. It prints each person's balance and the fewest payments that settle everyone up.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Usage

```bash
python3 simple-spliito.py example-expenses.txt
```

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

- The amount is split equally between everyone listed after it.
- People can be separated by spaces, commas, or both: `nik 640.5 nik eva tom,ivy` and `nik 640.5 nik, eva, tom, ivy` mean the same thing.
- The payer only gets a share if they list themselves: `lia 1250 lia nik sam ben` includes lia, while `tom 415 max` means tom paid the whole amount for max.
- A line with only the payer and amount for themselves (`ivy 297 ivy`) has no effect on anyone's balance.
- Naming someone twice gives them two shares: `sam 900 sam ana ana lia` splits the amount into four parts, and ana owes two of them.
- Names can contain numbers, so repeated people can be `mia1 mia2 mia3`. Names can't contain `#`.
- Decimal amounts work (`362.75`).
- Blank lines are ignored.
- `#` starts a comment, and everything after it on that line is ignored. A comment can take a whole line or follow an expense: `dan 210 mia1 mia2 mia3 # mias are cousins`.
- A `#` directly after a name, like `mia#2`, still starts a comment, so the script prints a `Warning:` line and the name is read as `mia`.
- Amounts that aren't finite numbers (`nan`, `inf`, `1e999`) are rejected as invalid.
- Any other line that doesn't match the format is skipped, and the script prints a short message for it (`Invalid line: ...`, `Invalid amount: ...` or `Invalid related_to list ...`). Watch out for plain-text notes whose second word is a number, such as `Notes: 100 euros total`, because those are read as an expense.

See [`example-expenses.txt`](example-expenses.txt) for a file that uses all of this.

## Output

```
Balances:      # negative means should pay, and positive means should receive
  sam  1816.58
  joe   730.67
  lia   712.50
  eva   246.54
  nik    46.96
  tom  -247.79
  ana  -696.67
  max  -834.67
  ben  -842.33
  ivy  -931.79

Settlements:
ivy pays:
  → sam  931.79
ben pays:
  → sam  842.33
max pays:
  → joe  730.67
  → nik   46.96
  → sam   42.46
  → lia   14.58
ana pays:
  → lia  696.67
tom pays:
  → eva  246.54
  → lia    1.25
```

Balances are sorted from largest to smallest. Settlements are grouped by the person who pays, so `ivy pays: → sam 931.79` means ivy pays sam 931.79. If nothing is owed, the settlements section says `Everyone is settled.`

## Limitations

- Splits are always equal (apart from naming someone more than once).
- Names are case-sensitive.
- The fewest payments are only guaranteed for up to 18 people with a balance to settle. Above that, the exact search would take too long, so the script prints a note and uses a faster method that may list extra payments.
- Amounts are plain floats, shown rounded to two decimals.
