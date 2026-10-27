"""Execute article examples, then compare algorithms with independent small oracles."""
from contextlib import redirect_stdout
from io import StringIO
from itertools import product, combinations
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "第4卷-组合算法/第07章-组合查找/7.1.1-布尔基础.md"
body = NOTE.read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)\n```", body, re.S)
assert len(blocks) == 3
namespace = {}
output = StringIO()
with redirect_stdout(output):
    for i, block in enumerate(blocks):
        exec(compile(block, f"article-block-{i + 1}", "exec"), namespace)


def powerset(items):
    for bits in product((False, True), repeat=len(items)):
        yield [x for x, selected in zip(items, bits) if selected]


def cnf_models(n, clauses):
    return [v for v in product((0, 1), repeat=n)
            if all(any(v[abs(lit) - 1] == int(lit > 0) for lit in c)
                   for c in clauses)]


def horn_models(n, rules):
    return [v for v in product((0, 1), repeat=n)
            if all(not all(v[p] for p in premises)
                   or (head is not None and v[head])
                   for premises, head in rules)]


horn_cases = 0
sat_cases = 0
for n in range(3):
    # Exclude tautological heads already in the premises.
    premise_sets = [tuple(i for i, b in enumerate(bits) if b)
                    for bits in product((0, 1), repeat=n)]
    possible_rules = [(p, h) for p in premise_sets for h in [None] + list(range(n))
                      if h is None or h not in p]
    for rules in powerset(possible_rules):
        models = horn_models(n, rules)
        actual = namespace["horn_model"](n, rules)
        assert (actual is None) == (not models), (n, rules, actual, models)
        if models:
            least = {i for i in range(n) if all(v[i] for v in models)}
            assert actual == least
            assert tuple(int(i in actual) for i in range(n)) in models
        horn_cases += 1

    literals = [i for i in range(-n, n + 1) if i]
    possible_clauses = [()] + [(lit,) for lit in literals] + list(combinations(literals, 2))
    for clauses in powerset(possible_clauses):
        models = cnf_models(n, clauses)
        actual = namespace["two_sat"](n, clauses)
        assert (actual is None) == (not models), (n, clauses, actual, models)
        if actual is not None:
            assert tuple(actual) in models
        sat_cases += 1

# Input normalization, duplicate literals/premises, unsupported formula shapes.
assert namespace["horn_model"](2, [((), 0), ((0, 0), 1)]) == {0, 1}
assert namespace["horn_model"](2, [((0,), 0)]) == set()
assert namespace["two_sat"](1, [(1, 1)]) == [1]
assert namespace["two_sat"](1, [(1, -1)]) is not None
for n, clauses in [(1, [(0,)]), (1, [(2,)]), (2, [(1, 2, -1)])]:
    try:
        namespace["two_sat"](n, clauses)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid literal/clause not rejected")

# Large chain checks the explicit DFS stack, without enumerating assignments.
chain_n = 2500
chain = [(1,)] + [(-i, i + 1) for i in range(1, chain_n)]
assert namespace["two_sat"](chain_n, chain) == [1] * chain_n
assert namespace["two_sat"](chain_n, chain + [(-chain_n,)]) is None

# Independent expression checks, including ordinary addition vs XOR.
for s, a, b in product((0, 1), repeat=3):
    f = a if s == 0 else b
    assert f == ((1 - s) & a) | (s & b)
    assert f == (s | a) & ((1 - s) | b)
    assert f == a ^ (s & a) ^ (s & b)
    assert f == (((1 - s) & a) | (s & b) | (a & b))
for x, y, z in product((0, 1), repeat=3):
    nand = lambda a, b: 1 - (a & b)
    assert nand(x, x) == 1 - x
    assert nand(nand(x, y), nand(x, y)) == (x & y)
    assert nand(nand(x, x), nand(y, y)) == (x | y)
    assert (x | (y & z)) == ((x | y) & (x | z))
    assert (x & (y ^ z)) == ((x & y) ^ (x & z))

def interval(u, v):
    return {w for w in range(8)
            if (u ^ w).bit_count() + (w ^ v).bit_count() == (u ^ v).bit_count()}

median_cases = 0
for x, y, z in product(range(8), repeat=3):
    assert interval(x, y) & interval(y, z) & interval(z, x) == {(x & y) | (y & z) | (x & z)}
    median_cases += 1
assert interval(0, 6) & interval(6, 5) & interval(5, 0) == {4}

# Classify every 3-input Boolean function directly by its semantic definition.
counts = dict(all=0, self_dual=0, monotone=0, monotone_self_dual=0,
              horn_closed=0, majority_closed=0, symmetric=0, canalizing=0)
for code in range(256):
    f = [(code >> x) & 1 for x in range(8)]
    on = [x for x in range(8) if f[x]]
    sd = all(f[x] == 1 - f[x ^ 7] for x in range(8))
    mono = all(f[x] <= f[y] for x in range(8) for y in range(8) if x & y == x)
    counts["all"] += 1
    counts["self_dual"] += sd
    counts["monotone"] += mono
    counts["monotone_self_dual"] += sd and mono
    counts["horn_closed"] += all(f[x & y] for x in on for y in on)
    counts["majority_closed"] += all(f[(x & y) | (y & z) | (x & z)]
                                      for x in on for y in on for z in on)
    counts["symmetric"] += all(f[x] == f[y] for x in range(8) for y in range(8)
                               if x.bit_count() == y.bit_count())
    counts["canalizing"] += any(len({f[x] for x in range(8) if (x >> k) & 1 == b}) == 1
                                for k in range(3) for b in (0, 1))
assert counts == dict(all=256, self_dual=16, monotone=20, monotone_self_dual=4,
                     horn_closed=122, majority_closed=166, symmetric=16, canalizing=120)

report = {
    "status": "passed",
    "date": "2026-10-26",
    "section": "7.1.1",
    "note": str(NOTE),
    "note_sha256": hashlib.sha256(body.encode()).hexdigest(),
    "article_python_blocks": len(blocks),
    "article_stdout": output.getvalue().splitlines(),
    "all_functions_n_0_to_3": namespace["checked"],
    "exhaustive_horn_formulas_n_0_to_2": horn_cases,
    "exhaustive_2cnf_formulas_n_0_to_2": sat_cases,
    "explicit_stack_chain_variables": chain_n,
    "cube_median_triples": median_cases,
    "three_variable_class_counts": counts,
    "source_checked": {"chinese_book_body": "274-302", "pdf_body": "285-313",
                       "chinese_book_exercises": "303-320", "pdf_exercises": "314-331"},
    "limits": "Finite exhaustive checks and examples; no claim of all exercise solutions, general minimum DNF solver, or median-label algorithm H implementation."
}
dest = ROOT / "verification/taocp-7.1.1-report.json"
dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
