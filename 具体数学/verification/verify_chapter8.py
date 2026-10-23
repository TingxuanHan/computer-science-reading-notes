"""Execute the examples and independently check chapter 8 probability claims."""
from collections import Counter
from contextlib import redirect_stdout
from fractions import Fraction as Q
from io import StringIO
from itertools import permutations, product
from math import comb, factorial
from pathlib import Path
import hashlib
from datetime import datetime, timedelta, timezone
import json
import re

ROOT = Path(__file__).resolve().parents[1]
report = {"chapter": 8, "date": datetime.now(timezone(timedelta(hours=8))).date().isoformat(), "examples": [], "independent_checks": []}
environments = []
paths = sorted((ROOT / "第08章-离散概率").glob("8.1.*.md"))
assert len(paths) == 5
for path in paths:
    text = path.read_text(encoding="utf-8")
    assert text.count("$$") % 2 == 0
    assert text.count("```") % 2 == 0
    assert "参考：" in text and "专栏目录" in text
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert not any(word in text for word in ("专享", "图灵社区会员", "ChenyangGao"))
    code = re.findall(r"```python\n(.*?)\n```", text, re.S)
    assert len(code) == 1
    stdout, environment = StringIO(), {}
    with redirect_stdout(stdout):
        exec(compile(code[0], str(path), "exec"), environment)
    environments.append(environment)
    report["examples"].append({
        "file": path.name, "result": "passed", "stdout": stdout.getvalue().strip(),
        "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
    })

def record(name, cases, detail):
    report["independent_checks"].append({
        "name": name, "cases": cases, "kind": "exact_rational",
        "detail": detail, "result": "passed",
    })

def moments(distribution):
    assert sum(distribution.values()) == 1
    mean = sum(x * p for x, p in distribution.items())
    return mean, sum(x * x * p for x, p in distribution.items()) - mean * mean

# Exact affine variance, covariance counterexample, and Chebyshev at support thresholds.
count = 0
for weights in product(range(1, 4), repeat=3):
    d = {x: Q(w, sum(weights)) for x, w in zip((-2, 1, 4), weights)}
    mu, var = moments(d)
    for a, b in ((-3, 4), (Q(1, 3), -2), (0, 8)):
        shifted = {}
        for x, p in d.items():
            shifted[a * x + b] = shifted.get(a * x + b, Q(0)) + p
        mu2, var2 = moments(shifted)
        assert (mu2, var2) == (a * mu + b, a * a * var)
        count += 1
    for threshold in [Q(1, 2), Q(1), Q(2), Q(3), Q(7)]:
        tail = sum(p for x, p in d.items() if abs(x - mu) >= threshold)
        assert tail <= var / threshold**2
        count += 1
record("Affine variance and Chebyshev on nonuniform discrete distributions", count,
       "Enumerate 27 weighted three-point distributions, including exact threshold endpoints.")

# Sample variance unbiasedness with weighted independent samples.
count = 0
base = {0: Q(1, 6), 2: Q(1, 3), 5: Q(1, 2)}
mu, var = moments(base)
for n in range(2, 6):
    mean_mean = mean_var = var_mean = Q(0)
    for sample in product(base, repeat=n):
        prob = Q(1)
        for x in sample:
            prob *= base[x]
        average = Q(sum(sample), n)
        sample_var = sum((x - average)**2 for x in sample) / (n - 1)
        mean_mean += prob * average
        mean_var += prob * sample_var
        var_mean += prob * (average - mu)**2
        count += 1
    assert (mean_mean, mean_var, var_mean) == (mu, var, var / n)
record("Weighted sample means and unbiased variance", count,
       "Enumerate all independent samples of lengths 2 to 5 from a nonuniform population.")

# PGF derivatives at z=1 are checked through factorial moments from raw permutations.
count = 0
for n in range(8):
    values = [sum(i == v for i, v in enumerate(perm))
              for perm in permutations(range(n))]
    for r in range(n + 3):
        total = 0
        for value in values:
            falling = 1
            for j in range(r):
                falling *= value - j
            total += falling
        assert Q(total, factorial(n)) == int(r <= n)
        count += 1
for n in range(1, 25):
    d = {k: Q(1, n) for k in range(n)}
    assert moments(d) == (Q(n - 1, 2), Q(n*n - 1, 12))
    count += 1
record("Fixed-point factorial moments and uniform PGFs", count,
       "Raw permutation enumeration checks all factorial moments through order n+2.")

def solve(matrix, rhs):
    """Exact Gaussian elimination, independent of closed-form overlap formulas."""
    a = [[Q(x) for x in row] + [Q(y)] for row, y in zip(matrix, rhs)]
    n = len(a)
    for col in range(n):
        pivot = next(i for i in range(col, n) if a[i][col])
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [x / scale for x in a[col]]
        for row in range(n):
            if row != col:
                scale = a[row][col]
                a[row] = [x - scale*y for x, y in zip(a[row], a[col])]
    return [row[-1] for row in a]

def transient_matrix(patterns, p):
    prefixes = sorted({pat[:k] for pat in patterns for k in range(len(pat))},
                      key=lambda s: (len(s), s))
    transient = [[Q(0)] * len(prefixes) for _ in prefixes]
    wins = [[Q(0)] * len(patterns) for _ in prefixes]
    for i, prefix in enumerate(prefixes):
        for char, prob in (("H", p), ("T", 1-p)):
            word = prefix + char
            completed = [j for j, pat in enumerate(patterns) if word.endswith(pat)]
            if completed:
                assert len(completed) == 1
                wins[i][completed[0]] += prob
            else:
                suffix = max((s for s in prefixes if word.endswith(s)), key=len)
                transient[i][prefixes.index(suffix)] += prob
    return transient, wins

def waiting_moments(pattern, p):
    transition, _ = transient_matrix([pattern], p)
    n = len(transition)
    matrix = [[int(i == j) - transition[i][j] for j in range(n)] for i in range(n)]
    e = solve(matrix, [1] * n)
    second = solve(matrix, [1 + 2*sum(t*x for t, x in zip(row, e))
                            for row in transition])
    return e[0], second[0] - e[0]**2

pattern_formula = environments[3]["pattern_moments"]
count = 0
for length in range(1, 7):
    for chars in product("HT", repeat=length):
        pattern = "".join(chars)
        for p in (Q(1, 3), Q(1, 2), Q(2, 3)):
            assert waiting_moments(pattern, p) == pattern_formula(pattern, p)
            count += 1
record("Arbitrary-pattern means and variances", count,
       "Solve independent prefix-state linear systems for every H/T pattern of lengths 1 to 6, at three biases.")

def overlap(a, b):
    return sum(2**k for k in range(1, min(len(a), len(b))+1) if a[-k:] == b[:k])

count = 0
patterns = ["".join(x) for x in product("HT", repeat=3)]
for a, b in permutations(patterns, 2):
    transition, wins = transient_matrix([a, b], Q(1, 2))
    n = len(transition)
    matrix = [[int(i == j)-transition[i][j] for j in range(n)] for i in range(n)]
    win = solve(matrix, [row[0] for row in wins])[0]
    num = overlap(b, b)-overlap(b, a)
    den = overlap(a, a)-overlap(a, b)
    assert win == Q(num, num+den)
    if (a, b) == ("HHT", "HTT"):
        assert win == Q(2, 3)
    count += 1
record("Two-pattern race probability", count,
       "Independent absorbing-state equations check Conway ratios for all ordered distinct pairs of length 3.")

# Weighted searches and time costs: enumerate actual chains, not collision recurrence.
count = 0
for m in range(1, 5):
    for n in range(5):
        failed = Counter()
        for hashes in product(range(m), repeat=n):
            chains = [[] for _ in range(m)]
            for key, bucket in enumerate(hashes):
                chains[bucket].append(key)
            for chain in chains:
                failed[len(chain)] += Q(1, m**(n+1))
        mean, var = moments(failed)
        assert (mean, var) == (Q(n, m), Q(n*(m-1), m*m))
        r = failed[0]
        assert r == Q(m-1, m)**n
        times = Counter()
        for probes, prob in failed.items():
            times[2+3*probes+5*(probes == 0)] += prob
        assert moments(times) == (2+3*mean+5*r, 9*var+25*r*(1-r)-30*mean*r)
        count += 1
        if n == 0:
            continue
        for weights in ([Q(1, n)]*n,
                        [Q(2*k, n*(n+1)) for k in range(1, n+1)]):
            d, averages = Counter(), Counter()
            within = Q(0)
            for hashes in product(range(m), repeat=n):
                chains = [[] for _ in range(m)]
                for key, bucket in enumerate(hashes):
                    chains[bucket].append(key)
                costs = [chains[hashes[k]].index(k)+1 for k in range(n)]
                local = Counter()
                for c, w in zip(costs, weights):
                    local[c] += w
                    d[c] += w / m**n
                local_mean, local_var = moments(local)
                averages[local_mean] += Q(1, m**n)
                within += local_var / m**n
            mean_k = sum(k*w for k, w in enumerate(weights))
            var_k = sum(k*k*w for k, w in enumerate(weights)) - mean_k**2
            assert moments(d) == (1+mean_k/m, Q(m-1, m*m)*mean_k+var_k/m**2)
            va = Q(m-1, m*m)*sum(k*w*w for k, w in enumerate(weights))
            assert moments(averages)[1] == va
            assert moments(d)[1] == va + within
            count += 1
record("Weighted hashing queries, conditional variance, and runtime branches", count,
       "Enumerate actual chain contents, including empty tables, one bucket and nonuniform query weights.")

report["status"] = "passed"
report["independent_case_total"] = sum(x["cases"] for x in report["independent_checks"])
report["scope"] = ("Exact finite enumeration and independent linear algebra supplement the articles' "
                   "general derivations. Finite checks do not replace proofs of limits or moment existence.")
out = ROOT / "verification" / "chapter8-report.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
