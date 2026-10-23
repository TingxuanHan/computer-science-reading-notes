"""Execute all article examples and independently check sensitive boundaries."""
import contextlib
import io
import json
import re
from collections import Counter
from fractions import Fraction
from math import floor, ceil, isqrt, gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reports = []
namespaces = {}
for path in sorted((ROOT / "第03章-整值函数").glob("3.1.*.md")):
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"图灵社区会员|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    assert text.count("$$") % 2 == 0
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    assert len(blocks) == 1
    namespace = {}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(blocks[0], str(path), "exec"), namespace)
    namespaces[path.name.split("-", 1)[0]] = namespace
    reports.append({"source": str(path.relative_to(ROOT)), "python_blocks_passed": len(blocks),
                    "output": output.getvalue().strip()})

checks = Counter()
xs = [Fraction(p, 6) for p in range(-30, 31)]
for a in xs:
    for b in xs:
        if a > b:
            continue
        candidates = range(-6, 7)
        counts = [sum(a <= k <= b for k in candidates), sum(a <= k < b for k in candidates),
                  sum(a < k <= b for k in candidates), sum(a < k < b for k in candidates)]
        formulas = [max(0, floor(b) - ceil(a) + 1), max(0, ceil(b) - ceil(a)),
                    max(0, floor(b) - floor(a)), max(0, ceil(b) - floor(a) - 1)]
        assert counts == formulas
        checks["integer_interval_boundaries"] += 1

def sqrt_floor_fraction(x):
    return isqrt(x.numerator // x.denominator)

def sqrt_ceil_fraction(x):
    r = sqrt_floor_fraction(x)
    return r if r * r == x else r + 1

for p in range(501):
    x = Fraction(p, 7)
    assert isqrt(floor(x)) == sqrt_floor_fraction(x)
    assert sqrt_ceil_fraction(Fraction(ceil(x))) == sqrt_ceil_fraction(x)
    m = sqrt_floor_fraction(x)
    mixed_fails = sqrt_ceil_fraction(Fraction(floor(x))) != sqrt_ceil_fraction(x)
    assert mixed_fails == (m * m < x < m * m + 1)
    checks["nested_roots_and_counterexample_domain"] += 1

for x in xs:
    for a in range(-3, 4):
        for b in range(1, 8):
            assert floor((x + a) / b) == floor(Fraction(floor(x) + a, b))
            assert ceil((x + a) / b) == ceil(Fraction(ceil(x) + a, b))
            checks["nested_integer_division"] += 1

icbrt = namespaces["3.1.2"]["icbrt"]
for k in [1, 2, 10, 101, 10**6, 10**20]:
    assert icbrt(k**3 - 1) == k - 1
    assert icbrt(k**3) == k
    assert icbrt(k**3 + 1) == k
    checks["large_cube_boundaries"] += 3

josephus = namespaces["3.1.3"]["josephus_by_ceiling"]
for n in range(1, 61):
    for q in range(2, 16):
        people = list(range(1, n + 1))
        position = 0
        while len(people) > 1:
            position = (position + q - 1) % len(people)
            people.pop(position)
        assert josephus(n, q) == people[0]
        checks["josephus_independent_elimination"] += 1

partition = namespaces["3.1.4"]["balanced_ranges"]
for n in range(80):
    for m in range(1, 15):
        remaining = n
        sizes = []
        for groups_left in range(m, 0, -1):
            size = (remaining + groups_left - 1) // groups_left
            sizes.append(size)
            remaining -= size
        assert remaining == 0
        assert sizes == [len(g) for g in partition(n, m)]
        checks["sequential_partition_invariant"] += 1

for m in range(1, 41):
    for n in range(-40, 41):
        d = gcd(m, n)
        actual = Counter(n * k % m for k in range(m))
        expected = Counter({r: d for r in range(0, m, d)})
        assert actual == expected
        checks["residue_values_and_multiplicity"] += 1

result = {"status": "passed", "articles": reports,
          "independent_checks": dict(checks), "independent_check_count": sum(checks.values()),
          "scope": "Finite exact checks supplement the general proofs in the notes; no numerical proof of equidistribution is claimed."}
target = ROOT / "verification" / "chapter3-report.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
