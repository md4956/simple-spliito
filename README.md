# simple-spliito

A small command-line tool for splitting shared expenses. You give it a text file listing who paid what and who it was for. It prints each person's balance and a short list of payments that settles everyone up.

> Hobby project, still under development.

## Requirements

Python 3. No external packages.

## Usage

```bash
python3 simple-splitter.py example-expenses.txt
```

## Input format

One expense per line:

```
<payer> <amount> <person> <person> ...
```

- The amount is split equally between everyone listed after it.
- People can be separated by spaces, commas, or both: `nik 640.5 nik eva tom,ivy`.
- The payer only gets a share if they list themselves: `lia 1250 lia nik sam ben` includes lia, while `tom 415 max` means tom paid the whole amount for max.
- A line with only the payer and amount for themselves (`ivy 297 ivy`) has no effect on anyone's balance.
- Naming someone twice gives them two shares: `sam 900 sam ana ana lia` splits the amount into four parts, and ana owes two of them.
- Decimal amounts work (`362.75`).
- Blank lines are ignored.
- Lines starting with `#` are comments and are ignored silently.
- Any other line that doesn't match the format is skipped, and the script prints a short message for it (`Invalid line: ...` or `Invalid amount: ...`). Watch out for plain-text notes whose second word is a number, such as `Notes: 100 euros total`, because those are read as an expense.

See [`example-expenses.txt`](example-expenses.txt) for a file that uses all of this.

## Output

```
Balances:      # negative means should pay, and positive means should receive
lia: 712.50
nik: 46.96
sam: 1816.58
ben: -842.33
eva: 246.54
tom: -247.79
ivy: -931.79
max: -834.67
joe: 730.67
ana: -696.67

Settlements:
tom to sam: 247.79
ana to sam: 696.67
max to sam: 834.67
ben to joe: 730.67
ben to lia: 111.67
ivy to lia: 600.83
ivy to eva: 246.54
ivy to nik: 46.96
ivy to sam: 37.46
```

`tom to sam: 247.79` means tom pays sam 247.79.

## Limitations

- Splits are always equal (apart from naming someone more than once).
- Names are case-sensitive.
- Comments only work as whole lines starting with `#`, not after an expense on the same line.
- The settlement list isn't guaranteed to use the fewest possible payments.
- Amounts are plain floats, shown rounded to two decimals.
