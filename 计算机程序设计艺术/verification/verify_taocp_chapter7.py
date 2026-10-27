"""Check original Chapter 7 examples against independent finite oracles."""
from pathlib import Path
from itertools import product, permutations, combinations, combinations_with_replacement
from functools import lru_cache
import contextlib
import hashlib
import io
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ['7.1-0和1.md', '7.2-生成所有可能性.md']
SUMMARIES = [
    '从真值表和Shannon展开出发，连接布尔求值、位集合与约简有序二叉判定图。用Python核对位操作、BDD求值和满足赋值计数，比较变量顺序导致的空间差异。',
    '串起元组、排列、组合、整数分划、集合分划和树的生成，再进入回溯、精确覆盖与SAT。推导不重不漏和安全剪枝的依据，提供可运行代码并说明旧分册的覆盖范围。',
]
report = {'chapter': 7, 'random_seed': 71026, 'articles': [], 'checks': {},
          'scope': 'Provided fascicles: 7.1 and 7.2 through 7.2.2.2; not the entire continuing Chapter 7.'}
envs = []
for filename in FILES:
    source = (ROOT / '第4卷-组合算法/第07章-组合查找' / filename).read_text(encoding='utf-8')
    title, body = source.split('\n', 1)
    title = title.removeprefix('# ')
    body = body.lstrip('\n').rstrip() + '\n'
    assert 5 <= len(title) <= 100
    assert source.count('```') % 2 == 0 and source.count('$$') % 2 == 0
    assert not any(x in source for x in ('TODO', '待补', '\ufffd'))
    blocks = re.findall(r'```python\n(.*?)\n```', source, re.S)
    expected = re.findall(r'```text\n(.*?)\n```', source, re.S)
    assert len(blocks) == len(expected) > 0
    scopes, outputs = [], []
    for j, (code, output) in enumerate(zip(blocks, expected)):
        ns, out = {}, io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(code, f'{filename}:block{j}', 'exec'), ns)
        assert out.getvalue().strip() == output, (filename, j, out.getvalue(), output)
        scopes.append(ns)
        outputs.append(output)
    envs.extend(scopes)
    report['articles'].append({'filename': filename, 'title': title,
        'body_characters': len(body), 'python_blocks': len(blocks),
        'sha256': hashlib.sha256(body.encode()).hexdigest(), 'example_outputs': outputs})


def raises(fun, *args):
    try:
        list(fun(*args))
    except ValueError:
        return
    raise AssertionError((fun, args))


bits, enum, search, sat = envs
for s in range(1 << 16):
    expected = [i for i, char in enumerate(reversed(bin(s)[2:])) if char == '1']
    assert list(bits['set_bits'](s)) == expected
for s in range(256):
    got = list(bits['submasks'](s))
    expected = [x for x in range(256) if set(bits['set_bits'](x)) <= set(bits['set_bits'](s))]
    assert sorted(got) == expected and len(got) == len(set(got))
    assert ((~s) & 255) == sum(1 << i for i in range(8) if i not in set(bits['set_bits'](s)))
raises(bits['set_bits'], -1)
raises(bits['submasks'], -1)
for s, a, b in product(range(2), repeat=3):
    assert ((s & a) | ((1 - s) & b)) == (b ^ (s & (a ^ b)))
report['checks']['bit_masks'] = {'masks_for_set_bits': 65536, 'submask_universes': 256,
                               'finite_complements': 256, 'mux_assignments': 8}

build, value, count = (bits[k] for k in ('build_bdd', 'bdd_value', 'bdd_count'))
bdd_cases = 0
for n in range(4):
    inputs = list(product(range(2), repeat=n))
    for truth in range(1 << (1 << n)):
        fn = lambda a, t=truth, n=n: (t >> sum(a[i] << i for i in range(n))) & 1
        for order in permutations(range(n)):
            bdd = build(order, fn)
            root, nodes, order = bdd
            wanted = []
            for row in inputs:
                a = dict(enumerate(row))
                assert value(bdd, a) == fn(a)
                wanted.append(fn(a))
            assert count(bdd) == sum(wanted)
            assert len(nodes) == len(set(nodes.values()))
            for level, low, high in nodes.values():
                assert low != high
                assert all(child < 2 or nodes[child][0] > level for child in (low, high))
            bdd_cases += 1
order_profiles = []
for m in range(1, 7):
    equal = lambda a, m=m: all(a[i] == a[m + i] for i in range(m))
    interleaved = tuple(x for i in range(m) for x in (i, m + i))
    good, bad = build(interleaved, equal), build(range(2 * m), equal)
    assert count(good) == count(bad) == 2 ** m
    assert len(good[1]) == 3 * m and len(bad[1]) == 3 * (2 ** m - 1)
    order_profiles.append([m, len(good[1]), len(bad[1]), count(good)])
report['checks']['bdd'] = {'all_truth_tables_and_orders_n_le_3': bdd_cases,
                         'equality_order_profiles_m_good_bad_models': order_profiles}

gray_sizes = []
for n in range(11):
    g = [i ^ (i >> 1) for i in range(1 << n)]
    assert set(g) == set(range(1 << n))
    assert all(bin(a ^ b).count('1') == 1 for a, b in zip(g, g[1:]))
    if n:
        assert bin(g[-1] ^ g[0]).count('1') == 1
    gray_sizes.append(len(g))
perm_cases = 0
for n in range(8):
    for p in combinations_with_replacement(range(3), n):
        got = list(enum['permutations_lex'](p))
        assert got == sorted(set(permutations(p)))
        perm_cases += 1
    assert list(enum['permutations_lex'](range(n))) == list(permutations(range(n)))
comb_cases = 0
for n in range(11):
    for k in range(n + 3):
        assert list(enum['combinations_lex'](n, k)) == list(combinations(range(n), k))
        comb_cases += 1

# Integer partitions: independently enumerate ordered compositions and normalize.
def composition_partitions(n):
    if n == 0:
        return {()}
    result = set()
    for cuts in product((False, True), repeat=n - 1):
        parts, width = [], 1
        for cut in cuts:
            if cut:
                parts.append(width)
                width = 1
            else:
                width += 1
        parts.append(width)
        result.add(tuple(sorted(parts, reverse=True)))
    return result

dp = [1] + [0] * 20
for part in range(1, 21):
    for n in range(part, 21):
        dp[n] += dp[n - part]
for n in range(21):
    got = list(enum['integer_partitions'](n))
    assert len(got) == len(set(got)) == dp[n]
    assert all(sum(p) == n and p == tuple(sorted(p, reverse=True)) and all(x > 0 for x in p) for p in got)
    if n <= 10:
        assert set(got) == composition_partitions(n)


def canonical(labels):
    names = {}
    return tuple(names.setdefault(v, len(names)) for v in labels)


@lru_cache(None)
def stirling(n, k):
    if n == 0:
        return int(k == 0)
    if k <= 0 or k > n:
        return 0
    return k * stirling(n - 1, k) + stirling(n - 1, k - 1)

for n in range(8):
    got = list(enum['set_partitions_rgs'](n))
    assert len(got) == len(set(got)) == sum(stirling(n, k) for k in range(n + 1))
    assert all(canonical(p) == p for p in got)
    if n <= 5:
        expected = {canonical(p) for p in product(range(n), repeat=n)}
        assert set(got) == expected
for n in range(8):
    got = list(enum['parentheses'](n))
    expected = set()
    for word in product('()', repeat=2 * n):
        balance = 0
        for char in word:
            balance += 1 if char == '(' else -1
            if balance < 0:
                break
        else:
            if balance == 0:
                expected.add(''.join(word))
    assert len(got) == len(set(got)) == math.comb(2 * n, n) // (n + 1)
    assert set(got) == expected
for name in ('integer_partitions', 'set_partitions_rgs', 'parentheses'):
    raises(enum[name], -1)
raises(enum['combinations_lex'], -1, 0)
raises(enum['combinations_lex'], 2, -1)
report['checks']['enumerators'] = {'gray_n': [0, 10], 'multiset_permutation_inputs': perm_cases,
    'distinct_permutation_n': [0, 7], 'combination_cases': comb_cases,
    'integer_partition_n_counted': [0, 20], 'integer_partition_n_composition_oracle': [0, 10],
    'set_partition_n': [0, 7], 'set_partition_n_assignment_oracle': [0, 5],
    'parentheses_n_exhaustive': [0, 7]}

queen_counts = []
for n in range(10):
    expected = sum(len({r + c for r, c in enumerate(p)}) == n and
                   len({r - c for r, c in enumerate(p)}) == n for p in permutations(range(n)))
    actual = search['queens_count'](n)
    assert actual == expected
    queen_counts.append(actual)
randomizer = random.Random(71026)
cover_cases = 0
for _ in range(350):
    n, k = randomizer.randrange(1, 7), randomizer.randrange(9)
    rows = [{i for i in range(n) if mask & (1 << i)}
            for mask in [randomizer.randrange(1, 1 << n) for _ in range(k)]]
    got = list(search['exact_covers'](range(n), rows))
    actual = [tuple(sorted(answer)) for answer in got]
    expected = set()
    for length in range(k + 1):
        for selected in combinations(range(k), length):
            if all(sum(c in rows[i] for i in selected) == 1 for c in range(n)):
                expected.add(selected)
    assert len(actual) == len(set(actual))
    assert set(actual) == expected
    cover_cases += 1
assert list(search['exact_covers']([], [])) == [()]
assert list(search['exact_covers']([0], [])) == []
raises(search['exact_covers'], [0], [set()])
raises(search['exact_covers'], [0], [{1}])
report['checks']['backtracking'] = {'queen_n_0_to_9_against_permutations': queen_counts,
    'exact_cover_random_cases_against_all_row_subsets': cover_cases,
    'empty_universe_and_invalid_rows': 'passed'}


def sat_oracle(clauses):
    variables = sorted({abs(lit) for c in clauses for lit in c})
    for row in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, row))
        if all(any(assignment[abs(lit)] == (lit > 0) for lit in c) for c in clauses):
            return assignment
    return None


def check_sat(clauses):
    expected = sat_oracle(clauses)
    actual = sat['solve_sat'](clauses)
    assert (actual is None) == (expected is None)
    if actual is not None:
        assert all(any(actual[abs(lit)] == (lit > 0) for lit in c) for c in clauses)


# All formulas made from all non-tautological clauses over two variables.
clause_pool = [tuple(sign * (i + 1) for i, sign in enumerate(signs) if sign)
               for signs in product((-1, 0, 1), repeat=2)]
for subset in range(1 << len(clause_pool)):
    check_sat([c for i, c in enumerate(clause_pool) if subset & (1 << i)])
for _ in range(700):
    n = randomizer.randrange(1, 6)
    clauses = [tuple(randomizer.choice((-1, 1)) * randomizer.randrange(1, n + 1)
                     for _ in range(randomizer.randrange(5)))
               for _ in range(randomizer.randrange(11))]
    check_sat(clauses)
for a, b, y in product((False, True), repeat=3):
    cnf = ((not y) or a) and ((not y) or b) and (y or (not a) or (not b))
    assert cnf == (y == (a and b))
report['checks']['sat'] = {'all_two_variable_non_tautological_formulas': 512,
    'random_formulas_with_duplicates_tautologies_empty_clauses': 700,
    'tseytin_and_gate_assignments': 8, 'returned_witness_checked': True}
report['result'] = 'passed'
(ROOT / 'verification/taocp-chapter7-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


report['all_passed'] = True
(ROOT / 'verification/taocp-chapter7-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 7: passed')
