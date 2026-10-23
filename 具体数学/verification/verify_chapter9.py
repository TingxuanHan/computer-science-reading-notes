"""Check article examples and independent identities, not prove asymptotic limits."""
from contextlib import redirect_stdout
from decimal import Decimal as D, localcontext
from fractions import Fraction as Q
from io import StringIO
from math import comb, factorial
from pathlib import Path
import hashlib
from datetime import datetime, timedelta, timezone
import json
import re

ROOT = Path(__file__).resolve().parents[1]
report = {"chapter": 9, "date": datetime.now(timezone(timedelta(hours=8))).date().isoformat(), "examples": [], "independent_checks": [],
          "scope": "Finite exact and high-precision checks supplement the proofs in the articles."}
files = sorted((ROOT / "第09章-渐近式").glob("9.1.*.md"))
assert len(files) == 6
for path in files:
    source = path.read_text(encoding="utf-8")
    assert source.count("$$") % 2 == 0 and source.count("```") % 2 == 0
    assert "参考：" in source and "专栏目录" in source
    assert not any(w in source for w in ("图灵社区会员", "专享", "ChenyangGao", "TODO", "待补"))
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", source)
    code = re.findall(r"```python\n(.*?)\n```", source, re.S)
    assert len(code) == 1
    output = StringIO()
    with redirect_stdout(output):
        exec(compile(code[0], str(path), "exec"), {})
    report["examples"].append({"file": path.name, "result": "passed",
                              "sha256": hashlib.sha256(source.encode()).hexdigest(),
                              "output": output.getvalue().strip()})

def check(name, cases, kind="exact"):
    report["independent_checks"].append(
        {"name": name, "cases": cases, "kind": kind, "result": "passed"})

# Independently reconstruct Bernoulli numbers and polynomial Euler summation.
B = [Q(1)]
for m in range(1, 14):
    B.append(-sum(comb(m+1, j)*B[j] for j in range(m))/(m+1))
count = 0
for degree in range(11):
    for a in range(-3, 4):
        for length in range(0, 11):
            b = a + length
            value = Q(b**(degree+1)-a**(degree+1), degree+1)
            for r in range(1, degree+2):
                d = r-1
                derivative = Q(factorial(degree), factorial(degree-d))
                value += B[r]/factorial(r)*derivative*(b**(degree-d)-a**(degree-d))
            assert value == sum(k**degree for k in range(a, b))
            count += 1
check("Euler summation for monomials including negative endpoints and empty intervals", count)

# g_n: recurrence against independently multiplying formal exponential factors.
N = 24
g = [Q(1)]
for n in range(1, N+1):
    g.append(sum(g[k]/(n-k) for k in range(n))/n)
coeff = [Q(1)] + [Q(0)]*N
for k in range(1, N+1):
    out = [Q(0)]*(N+1)
    for j in range(N//k+1):
        factor = Q(1, k**(2*j)*factorial(j))
        for r in range(N-k*j+1):
            out[r+k*j] += coeff[r]*factor
    coeff = out
assert g == coeff
assert all(Q(1,n*n) <= g[n] <= 1 for n in range(1, N+1))
check("Bootstrap recurrence versus formal exponential coefficient convolution", N+1)

# Power-sum closed forms and the collected n^-1 ... n^-6 coefficients.
count = 0
for n in range(1, 81):
    power_sums = [Q(n), Q(n*(n+1),2), Q(n**3,3)+Q(n*n,2)+Q(n,6),
                  Q(n**4,4)+Q(n**3,2)+Q(n*n,4),
                  Q(n**5,5)+Q(n**4,2)+Q(n**3,3)-Q(n,30),
                  Q(n**6,6)+Q(n**5,2)+Q(5*n**4,12)-Q(n*n,12)]
    assert power_sums == [sum(k**j for k in range(1,n+1)) for j in range(6)]
    polynomial = sum((-1)**j*power_sums[j]/n**(2*j+2) for j in range(6))
    collected = Q(1,n)-Q(1,2*n*n)-Q(1,6*n**3)+Q(1,4*n**4)-Q(2,15*n**5)+Q(1,12*n**6)
    discarded = -Q(1,6*n**7)-Q(5,12*n**8)-Q(1,30*n**9)+Q(1,12*n**10)
    assert polynomial-collected == discarded
    count += 7
check("Six power sums and all terms discarded from the displayed finite-sum approximation", count)

with localcontext() as ctx:
    ctx.prec = 75
    pi = D("3.141592653589793238462643383279502884197169399375105820974944592307816406286")
    gamma = D("0.577215664901532860606512090082402431042159335939923598805767234884867726778")
    for n in [1,2,3,5,10,20,50,100,250,1000]:
        d = D(n)
        H = sum(D(1)/k for k in range(1,n+1))
        error = H-d.ln()-gamma-1/(2*d)+1/(12*d*d)-1/(120*d**4)
        assert -1/(252*d**6)<error<0
        error = D(factorial(n)).ln()-(d+D(".5"))*d.ln()+d-(2*pi).ln()/2-1/(12*d)+1/(360*d**3)
        assert 0<error<1/(1260*d**5)
    check("Harmonic and log-factorial remainder signs and explicit next-term bounds", 20, "75_digit_finite_check")
    # Gaussian series: direct finite sum with a rigorous positive tail bound.
    for n in [1,2,5,10]:
        d = D(n)
        K = 80
        gaussian = 1+2*sum((-D(k*k)/d).exp() for k in range(1,K+1))
        tail = 2*(-D((K+1)**2)/d).exp()/(1-(-D(2*K+3)/d).exp())
        residual = gaussian/(pi*d).sqrt()-1
        lead = 2*(-pi*pi*d).exp()
        second = 2*(-4*pi*pi*d).exp()
        assert residual > 0
        # Check the stronger theta expansion at scales safely above precision noise.
        assert abs(residual-lead) <= 3*second + D("1e-70") + tail
    check("Gaussian sum against quoted leading exponential correction with explicit truncation tail", 4, "75_digit_finite_check")

report["result"] = "passed"
report["independent_case_count"] = sum(r["cases"] for r in report["independent_checks"])
(ROOT / "verification" / "chapter9-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"result": "passed", "article_examples": len(files),
                  "independent_cases": report["independent_case_count"]}, ensure_ascii=False))
