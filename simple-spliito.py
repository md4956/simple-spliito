EPSILON = 0.0001
# The exact search doubles in cost with every extra person
MAX_EXACT_PEOPLE = 18


def split_into_groups(amounts):
    """Split amounts into as many groups summing to zero as possible.

    A group of k people settles in k - 1 payments, so the most groups gives
    the fewest payments. Returns the groups as lists of indexes into amounts.
    """
    n = len(amounts)
    size = 1 << n
    totals = [0.0] * size  # sum of the amounts in each subset
    counts = [0] * size    # most zero-sum groups the subset can be built from
    removed = [0] * size   # index to remove to reach the best smaller subset

    for mask in range(1, size):
        best = -1
        for i in range(n):
            if mask & (1 << i):
                rest = mask ^ (1 << i)
                totals[mask] = totals[rest] + amounts[i]
                if counts[rest] > best:
                    best = counts[rest]
                    removed[mask] = i
        counts[mask] = best + (abs(totals[mask]) < EPSILON)

    groups = []
    group = []
    mask = size - 1
    while mask:
        i = removed[mask]
        group.append(i)
        mask ^= 1 << i
        if abs(totals[mask]) < EPSILON:
            groups.append(group)
            group = []
    return groups


def settle(balances):
    """Return the (payer, receiver, amount) payments that settle the balances."""
    people = [k for k, v in balances.items() if abs(v) >= EPSILON]
    if len(people) > MAX_EXACT_PEOPLE:
        print(f"Note: more than {MAX_EXACT_PEOPLE} people to settle, so the fewest payments isn't guaranteed.")
        groups = [people]
    else:
        groups = [[people[i] for i in group] for group in split_into_groups([balances[p] for p in people])]

    transactions = []
    for group in groups:
        debtors = {k: balances[k] for k in group if balances[k] > 0}
        creditors = {k: balances[k] for k in group if balances[k] < 0}

        while debtors and creditors:
            debtor = max(debtors.items(), key=lambda x: x[1])[0]
            creditor = min(creditors.items(), key=lambda x: x[1])[0]
            transfer = min(debtors[debtor], abs(creditors[creditor]))

            transactions.append((creditor, debtor, transfer))
            debtors[debtor] -= transfer
            creditors[creditor] += transfer

            if debtors[debtor] < EPSILON:
                del debtors[debtor]
            if creditors[creditor] > -EPSILON:
                del creditors[creditor]
    return transactions


def print_report(balances, transactions, unit, label):
    """Print one report.

    unit is the currency code, or '' for plain numbers. It is added after each amount.
    label is the name shown in each heading, or '' when there is nothing to add.
    """
    from collections import defaultdict

    suffix = f" {unit}" if unit else ""
    heading_suffix = f" - {label}" if label else ""
    people_word = "person" if len(balances) == 1 else "people"
    payment_word = "payment" if len(transactions) == 1 else "payments"
    print(f"SUMMARY{heading_suffix}: {len(balances)} {people_word}, {len(transactions)} {payment_word}\n")

    print(f"BALANCES{heading_suffix}\n")
    for person, balance in sorted(balances.items(), key=lambda x: -x[1]):
        if abs(balance) < 0.005:
            print(f"{person} is settled")
        elif balance > 0:
            print(f"{person} gets {balance:,.2f}{suffix}")
        else:
            print(f"{person} owes {-balance:,.2f}{suffix}")

    total = sum(balances.values())
    if abs(total) < 0.005:
        print(f"\nTOTAL{heading_suffix}: 0.00 (balances add up to zero, so every payment is accounted for)")
    else:
        print(f"\nTOTAL{heading_suffix}: {total:,.2f} (should be 0.00, so the script has a calculation bug)")

    print(f"\nPAYMENTS{heading_suffix}\n")
    if not transactions:
        print("Everyone is settled.")
        return

    by_payer = defaultdict(list)
    for payer, receiver, amount in transactions:
        by_payer[payer].append((receiver, amount))
    paid = {payer: sum(amount for _, amount in items) for payer, items in by_payer.items()}
    single = sorted((p for p in by_payer if len(by_payer[p]) == 1), key=lambda p: -paid[p])
    multi = sorted((p for p in by_payer if len(by_payer[p]) > 1), key=lambda p: -paid[p])

    # One block for everyone who pays once, then one block per person who pays several times
    blocks = ([single] if single else []) + [[payer] for payer in multi]
    for index, block in enumerate(blocks):
        if index:
            print()
        for payer in block:
            for receiver, amount in sorted(by_payer[payer], key=lambda x: -x[1]):
                print(f"{payer} pays {receiver} {amount:,.2f}{suffix}")


def main():
    import math
    import sys
    from collections import defaultdict

    if len(sys.argv) != 2:
        print("Usage: python3 simple-spliito.py expenses.txt (or expenses.md)")
        sys.exit(1)

    filename = sys.argv[1]
    balances = defaultdict(lambda: defaultdict(float))  # currency -> person -> balance
    currency = ''
    title = ''

    try:
        # utf-8-sig skips the byte-order mark some editors add at the start of the file
        with open(filename, 'r', encoding='utf-8-sig') as file:
            for index, raw_line in enumerate(file):
                if index == 0 and raw_line.lstrip().startswith('#'):
                    title = raw_line.lstrip()[1:].strip()
                head, comment_start, _ = raw_line.partition('#')
                line = head.strip()
                if comment_start and head[-1:] not in ('', ' ', '\t'):
                    print(f"Warning: '#' right after a name starts a comment: {raw_line.strip()}")
                if not line:
                    continue
                if line.startswith('@'):
                    codes = line[1:].split()
                    if len(codes) > 1:
                        print(f"Invalid currency: {line}")
                        continue
                    currency = codes[0] if codes else ''
                    continue

                parts = line.split()
                if len(parts) < 3:
                    print(f"Invalid line: {line}")
                    continue
                payer = parts[0]
                try:
                    amount = float(parts[1])
                    if not math.isfinite(amount):
                        raise ValueError
                except ValueError:
                    print(f"Invalid amount: {parts[1]} in line: {line}")
                    continue
                related_to = [p for p in ','.join(parts[2:]).split(',') if p]

                if not related_to:
                    print(f"Invalid related_to list in line: {line}")
                    continue

                names = [payer, *related_to]
                if any('*' in name or '~' in name for name in names):
                    print(f"Error: '*' and '~' are not allowed in names: {line}")
                    sys.exit(1)
                if any('_' in name for name in names):
                    print(f"Warning: '_' in a name can turn text italic in messengers: {line}")

                share = amount / len(related_to)
                balances[currency][payer] += amount
                for person in related_to:
                    balances[currency][person] -= share

    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    if title:
        if any(char in title for char in '_*~'):
            print(f"Warning: '_', '*' and '~' in the title can change how messengers show it: {title}")
        print(f"{title}\n")

    # Plain-number expenses come first, then each currency in the order it first appears
    groups = balances.items() or [('', defaultdict(float))]
    multiple = len(groups) > 1
    for index, (unit, person_balances) in enumerate(groups):
        if index and multiple:
            print("\n-----\n")
        label = unit or ('NO CURRENCY' if multiple else '')
        print_report(person_balances, settle(person_balances), unit, label)
    print()


if __name__ == "__main__":
    main()
