// Browser and Node port of simple-spliito.py. Keep it in step with the script:
// tests/test_web_port.py runs both on the same inputs and compares the output.
(function () {
  const EPSILON = 0.0001;
  // The exact search doubles in cost with every extra person
  const MAX_EXACT_PEOPLE = 18;
  // The numbers Python's float() accepts, with optional underscores between digits
  const NUMBER = /^[+-]?(\d+(_\d+)*\.?(\d+(_\d+)*)?|\.\d+(_\d+)*)([eE][+-]?\d+(_\d+)*)?$/;

  function splitIntoGroups(amounts) {
    const n = amounts.length;
    const size = 1 << n;
    const totals = new Float64Array(size);  // sum of the amounts in each subset
    const counts = new Int32Array(size);    // most zero-sum groups the subset can be built from
    const removed = new Int32Array(size);   // index to remove to reach the best smaller subset

    for (let mask = 1; mask < size; mask++) {
      let best = -1;
      for (let i = 0; i < n; i++) {
        if (mask & (1 << i)) {
          const rest = mask ^ (1 << i);
          totals[mask] = totals[rest] + amounts[i];
          if (counts[rest] > best) {
            best = counts[rest];
            removed[mask] = i;
          }
        }
      }
      counts[mask] = best + (Math.abs(totals[mask]) < EPSILON ? 1 : 0);
    }

    const groups = [];
    let group = [];
    let mask = size - 1;
    while (mask) {
      const i = removed[mask];
      group.push(i);
      mask ^= 1 << i;
      if (Math.abs(totals[mask]) < EPSILON) {
        groups.push(group);
        group = [];
      }
    }
    return groups;
  }

  // First key with the best value, the same choice Python's max() and min() make
  function pickFirst(map, better) {
    let best;
    for (const [key, value] of map) {
      if (best === undefined || better(value, map.get(best))) best = key;
    }
    return best;
  }

  // Returns [payer, receiver, amount] payments that settle the balances
  function settle(balances, print) {
    const people = [...balances.keys()].filter((k) => Math.abs(balances.get(k)) >= EPSILON);
    let groups;
    if (people.length > MAX_EXACT_PEOPLE) {
      print(`Note: more than ${MAX_EXACT_PEOPLE} people to settle, so the fewest payments isn't guaranteed.`);
      groups = [people];
    } else {
      groups = splitIntoGroups(people.map((p) => balances.get(p))).map((g) => g.map((i) => people[i]));
    }

    const transactions = [];
    for (const group of groups) {
      const debtors = new Map(group.filter((k) => balances.get(k) > 0).map((k) => [k, balances.get(k)]));
      const creditors = new Map(group.filter((k) => balances.get(k) < 0).map((k) => [k, balances.get(k)]));

      while (debtors.size && creditors.size) {
        const debtor = pickFirst(debtors, (a, b) => a > b);
        const creditor = pickFirst(creditors, (a, b) => a < b);
        const transfer = Math.min(debtors.get(debtor), Math.abs(creditors.get(creditor)));
        transactions.push([creditor, debtor, transfer]);
        debtors.set(debtor, debtors.get(debtor) - transfer);
        creditors.set(creditor, creditors.get(creditor) + transfer);

        if (debtors.get(debtor) < EPSILON) debtors.delete(debtor);
        if (creditors.get(creditor) > -EPSILON) creditors.delete(creditor);
      }
    }
    return transactions;
  }

  // Same result as Python's f"{x:,.2f}": the exact binary value, rounding ties to the even cent
  function money(x) {
    const [whole, fraction] = Math.abs(x).toFixed(30).split('.');
    let cents = BigInt(whole + fraction.slice(0, 2));
    const rest = fraction.slice(2);
    const roundUp = rest[0] > '5' || (rest[0] === '5' && (/[1-9]/.test(rest.slice(1)) || cents % 2n === 1n));
    if (roundUp) cents += 1n;
    const digits = cents.toString().padStart(3, '0');
    const grouped = digits.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return (x < 0 ? '-' : '') + grouped + '.' + digits.slice(-2);
  }

  function printReport(balances, transactions, unit, label, print) {
    const suffix = unit ? ` ${unit}` : '';
    const headingSuffix = label ? ` - ${label}` : '';
    const peopleWord = balances.size === 1 ? 'person' : 'people';
    const paymentWord = transactions.length === 1 ? 'payment' : 'payments';
    print(`SUMMARY${headingSuffix}: ${balances.size} ${peopleWord}, ${transactions.length} ${paymentWord}\n`);

    print(`BALANCES${headingSuffix}\n`);
    for (const [person, balance] of [...balances].sort((a, b) => b[1] - a[1])) {
      if (Math.abs(balance) < 0.005) print(`${person} is settled`);
      else if (balance > 0) print(`${person} gets ${money(balance)}${suffix}`);
      else print(`${person} owes ${money(-balance)}${suffix}`);
    }

    const total = [...balances.values()].reduce((sum, value) => sum + value, 0);
    if (Math.abs(total) < 0.005) {
      print(`\nTOTAL${headingSuffix}: 0.00 (balances add up to zero, so every payment is accounted for)`);
    } else {
      print(`\nTOTAL${headingSuffix}: ${money(total)} (should be 0.00, so the script has a calculation bug)`);
    }

    print(`\nPAYMENTS${headingSuffix}\n`);
    if (!transactions.length) {
      print('Everyone is settled.');
      return;
    }

    const byPayer = new Map();
    for (const [payer, receiver, amount] of transactions) {
      if (!byPayer.has(payer)) byPayer.set(payer, []);
      byPayer.get(payer).push([receiver, amount]);
    }
    const paid = new Map([...byPayer].map(([payer, items]) => [payer, items.reduce((sum, [, amount]) => sum + amount, 0)]));
    const byPaid = (a, b) => paid.get(b) - paid.get(a);
    const payers = [...byPayer.keys()];
    const single = payers.filter((p) => byPayer.get(p).length === 1).sort(byPaid);
    const multi = payers.filter((p) => byPayer.get(p).length > 1).sort(byPaid);

    // One block for everyone who pays once, then one block per person who pays several times
    const blocks = [...(single.length ? [single] : []), ...multi.map((payer) => [payer])];
    blocks.forEach((block, index) => {
      if (index) print();
      for (const payer of block) {
        for (const [receiver, amount] of [...byPayer.get(payer)].sort((a, b) => b[1] - a[1])) {
          print(`${payer} pays ${receiver} ${money(amount)}${suffix}`);
        }
      }
    });
  }

  // Returns { text, ok, expenses }: the same stdout the script prints, false where the script exits
  // with an error, and how many expense lines were read
  function run(text) {
    let out = '';
    const print = (s = '') => {
      out += s + '\n';
    };
    const balances = new Map();  // currency -> Map(person -> balance)
    let currency = '';
    let title = '';
    let expenses = 0;

    const lines = text.replace(/^﻿/, '').split(/\r\n|\r|\n/);
    for (let index = 0; index < lines.length; index++) {
      const rawLine = lines[index];
      if (index === 0 && rawLine.trimStart().startsWith('#')) title = rawLine.trimStart().slice(1).trim();
      const hashAt = rawLine.indexOf('#');
      const head = hashAt === -1 ? rawLine : rawLine.slice(0, hashAt);
      const line = head.trim();
      if (hashAt !== -1 && !['', ' ', '\t'].includes(head.slice(-1))) {
        print(`Warning: '#' right after a name starts a comment: ${rawLine.trim()}`);
      }
      if (!line) continue;

      if (line.startsWith('@')) {
        const codes = line.slice(1).split(/\s+/).filter(Boolean);
        if (codes.length > 1) {
          print(`Invalid currency: ${line}`);
          continue;
        }
        currency = codes[0] || '';
        continue;
      }

      const parts = line.split(/\s+/);
      if (parts.length < 3) {
        print(`Invalid line: ${line}`);
        continue;
      }
      const payer = parts[0];
      const amount = NUMBER.test(parts[1]) ? parseFloat(parts[1].replace(/_/g, '')) : NaN;
      if (!Number.isFinite(amount)) {
        print(`Invalid amount: ${parts[1]} in line: ${line}`);
        continue;
      }
      const relatedTo = parts.slice(2).join(',').split(',').filter(Boolean);
      if (!relatedTo.length) {
        print(`Invalid related_to list in line: ${line}`);
        continue;
      }

      const names = [payer, ...relatedTo];
      if (names.some((name) => name.includes('*') || name.includes('~'))) {
        print(`Error: '*' and '~' are not allowed in names: ${line}`);
        return { text: out, ok: false, expenses };
      }
      if (names.some((name) => name.includes('_'))) {
        print(`Warning: '_' in a name can turn text italic in messengers: ${line}`);
      }

      expenses++;
      const share = amount / relatedTo.length;
      if (!balances.has(currency)) balances.set(currency, new Map());
      const current = balances.get(currency);
      current.set(payer, (current.get(payer) || 0) + amount);
      for (const person of relatedTo) current.set(person, (current.get(person) || 0) - share);
    }

    if (title) {
      if ([...title].some((char) => '_*~'.includes(char))) {
        print(`Warning: '_', '*' and '~' in the title can change how messengers show it: ${title}`);
      }
      print(`${title}\n`);
    }

    // Plain-number expenses come first, then each currency in the order it first appears
    const groups = balances.size ? [...balances] : [['', new Map()]];
    const multiple = groups.length > 1;
    groups.forEach(([unit, personBalances], index) => {
      if (index && multiple) print('\n-----\n');
      const label = unit || (multiple ? 'NO CURRENCY' : '');
      const transactions = settle(personBalances, print);
      printReport(personBalances, transactions, unit, label, print);
    });
    print();
    return { text: out, ok: true, expenses };
  }

  const Spliito = { run };
  if (typeof module !== 'undefined') module.exports = Spliito;
  else globalThis.Spliito = Spliito;
})();
