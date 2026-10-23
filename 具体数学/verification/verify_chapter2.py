"""Execute article examples and independently check finite identities exactly."""
from contextlib import redirect_stdout
from fractions import Fraction as F
from io import StringIO
from itertools import product
from pathlib import Path
from random import Random
import json
import re

ROOT = Path(__file__).resolve().parents[1]
report = {"chapter": 2, "examples": [], "independent_checks": []}

for path in sorted((ROOT / "第02章-和式").glob("2.1.*.md")):
    text = path.read_text(encoding="utf-8")
    assert "图灵社区会员" not in text
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert text.count("$$") % 2 == 0, path
    blocks = re.findall(r"```python\n(.*?)\n```", text, re.S)
    assert blocks, path
    for i, code in enumerate(blocks, 1):
        output = StringIO()
        with redirect_stdout(output):
            exec(compile(code, str(path), "exec"), {})
        report["examples"].append({"file": path.name, "block": i,
                                   "result": "passed", "output": output.getvalue().strip()})

def check_group(name, count):
    report["independent_checks"].append({"name": name, "cases": count, "result": "passed"})

for p, q in product([False, True], repeat=2):
    assert int(p or q) == int(p) + int(q) - int(p) * int(q)
    assert int(p and q) == int(p) * int(q)
check_group("Iverson truth tables", 4)

rng = Random(20261022)
for _ in range(50):
    x0 = F(rng.randrange(-5, 6))
    direct, prod_p, increment = x0, F(1), F(0)
    for n in range(1, 21):
        p = F(rng.choice([-3, -2, -1, 1, 2, 3]), rng.randrange(1, 5))
        q = F(rng.randrange(-5, 6), rng.randrange(1, 5))
        direct = p * direct + q
        prod_p *= p
        increment += q / prod_p
        assert direct == prod_p * (x0 + increment)
check_group("Nonconstant signed recurrence coefficients", 1000)

for _ in range(100):
    a, b, c, d = [F(rng.randrange(-9, 10), 3) for _ in range(4)]
    r = a
    for n in range(21):
        if n:
            r += b + c * n + d * n * n
        closed = a + b*n + c*F(n*(n+1), 2) + d*F(n*(n+1)*(2*n+1), 6)
        assert r == closed
check_group("Repertoire with independent parameters", 2100)

for n in range(16):
    a = [rng.randrange(-10, 11) for _ in range(n)]
    b = [rng.randrange(-10, 11) for _ in range(n)]
    upper = sum(a[j]*a[k] for j in range(n) for k in range(j,n))
    strict = sum(a[j]*a[k] for j in range(n) for k in range(j+1,n))
    assert 2*upper == sum(a)**2 + sum(x*x for x in a)
    assert 2*strict == sum(a)**2 - sum(x*x for x in a)
    pairs = sum((a[k]-a[j])*(b[k]-b[j]) for j in range(n) for k in range(j+1,n))
    assert pairs == n*sum(x*y for x,y in zip(a,b))-sum(a)*sum(b)
    rows = {(j,k) for j in range(1,n+1) for k in range(1,j+1)}
    cols = {(j,k) for k in range(1,n+1) for j in range(k,n+1)}
    assert rows == cols and len(rows) == n*(n+1)//2
check_group("Triangular index sets and symmetric sums", 16)

def harmonic(n):
    return sum((F(1,k) for k in range(1,n+1)), F(0))

for n in range(41):
    assert sum(k*harmonic(k) for k in range(n)) == F(n*(n-1),2)*(harmonic(n)-F(1,2))
    u = lambda k: k*k+2*k-3
    v = lambda k: F(2**k)
    lhs = sum(u(k)*(v(k+1)-v(k)) for k in range(n))
    rhs = u(n)*v(n)-u(0)*v(0)-sum(v(k+1)*(u(k+1)-u(k)) for k in range(n))
    assert lhs == rhs
check_group("Summation by parts and weighted harmonic sums", 41)

for r,s in product([F(-2,3),F(0),F(1,4)], repeat=2):
    for m,n in [(0,0),(1,7),(5,3),(8,8)]:
        rect = sum(r**j*s**k for j in range(m+1) for k in range(n+1))
        exact = (1-r**(m+1))/(1-r)*(1-s**(n+1))/(1-s)
        assert rect == exact
for m in range(1,51):
    reordered = sum(F(1,2*j-1) for j in range(1,2*m+1))-sum(F(1,2*j) for j in range(1,m+1))
    assert reordered == harmonic(4*m)-harmonic(2*m)/2-harmonic(m)/2
check_group("Finite identities supporting infinite series arguments", 86)

assert len(report["examples"]) == 7
report["status"] = "passed"
report["scope"] = "Exact finite checks complement, but do not replace, proofs of convergence and identities."
(ROOT / "verification" / "chapter2-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
