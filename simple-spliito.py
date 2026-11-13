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


def main():
    import math
    import sys
    from collections import defaultdict

    if len(sys.argv) != 2:
        print("Usage: python3 simple-spliito.py expenses.txt")
        sys.exit(1)

    filename = sys.argv[1]
    balances = defaultdict(float)
    transactions = []

    try:
        with open(filename, 'r') as file:
            for raw_line in file:
                head, comment_start, _ = raw_line.partition('#')
                line = head.strip()
                if comment_start and head[-1:] not in ('', ' ', '\t'):
                    print(f"Warning: '#' right after a name starts a comment: {raw_line.strip()}")
                if not line:
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
                related_str = parts[2:]
                related_to = [p for p in ','.join(related_str).split(',') if p]

                if not related_to:
                    print(f"Invalid related_to list in line: {line}")
                    continue

                names = [payer, *related_to]
                if any('*' in name or '~' in name for name in names):
                    print(f"Error: '*' and '~' are not allowed in names: {line}")
                    sys.exit(1)
                if any('_' in name for name in names):
                    print(f"Warning: '_' in a name can turn text italic in messengers: {line}")

                n = len(related_to)
                share = amount / n

                balances[payer] += amount
                for person in related_to:
                    balances[person] -= share

    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    # Calculate settlements
    people = [k for k, v in balances.items() if abs(v) >= EPSILON]
    if len(people) > MAX_EXACT_PEOPLE:
        print(f"Note: more than {MAX_EXACT_PEOPLE} people to settle, so the fewest payments isn't guaranteed.")
        groups = [people]
    else:
        groups = [[people[i] for i in group] for group in split_into_groups([balances[p] for p in people])]

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

    # Output the results
    people_word = "person" if len(balances) == 1 else "people"
    payment_word = "payment" if len(transactions) == 1 else "payments"
    print(f"SUMMARY: {len(balances)} {people_word}, {len(transactions)} {payment_word}\n")

    print("BALANCES")
    for person, balance in sorted(balances.items(), key=lambda x: -x[1]):
        if abs(balance) < 0.005:
            print(f"{person} is settled")
        elif balance > 0:
            print(f"{person} gets {balance:,.2f}")
        else:
            print(f"{person} owes {-balance:,.2f}")

    total = sum(balances.values())
    if abs(total) < 0.005:
        print("\nTOTAL: 0.00 (balances add up to zero, so every payment is accounted for)")
    else:
        print(f"\nTOTAL: {total:,.2f} (should be 0.00, so the script has a calculation bug)")

    print("\nPAYMENTS")
    if not transactions:
        print("Everyone is settled.")
    by_payer = defaultdict(list)
    for payer, receiver, amount in transactions:
        by_payer[payer].append((receiver, amount))
    paid = {payer: sum(amount for _, amount in items) for payer, items in by_payer.items()}
    single = sorted((p for p in by_payer if len(by_payer[p]) == 1), key=lambda p: -paid[p])
    multi = sorted((p for p in by_payer if len(by_payer[p]) > 1), key=lambda p: -paid[p])
    for index, block in enumerate(b for b in (single, multi) if b):
        if index:
            print()
        for payer in block:
            for receiver, amount in sorted(by_payer[payer], key=lambda x: -x[1]):
                print(f"{payer} pays {receiver} {amount:,.2f}")
    print()

if __name__ == "__main__":
    main()
