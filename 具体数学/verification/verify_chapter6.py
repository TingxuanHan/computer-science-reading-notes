"""Execute published examples and independently check chapter 6 identities."""
from contextlib import redirect_stdout
from decimal import Decimal, localcontext
from fractions import Fraction as Q
from functools import lru_cache
from io import StringIO
from itertools import product
from math import comb, factorial, prod
from pathlib import Path
from random import Random
import hashlib
from datetime import datetime, timedelta, timezone
import json
import re

ROOT = Path(__file__).resolve().parents[1]
report = {"chapter":6,"date":datetime.now(timezone(timedelta(hours=8))).date().isoformat(),"examples":[],"independent_checks":[]}
files = sorted((ROOT / "第06章-特殊的数").glob("6.1.*.md"))
assert len(files) == 7
for path in files:
    source = path.read_text(encoding="utf-8")
    assert source.count("$$") % 2 == 0 and source.count("```") % 2 == 0
    assert "参考：" in source and "专栏目录" in source
    assert not any(w in source for w in ("图灵社区会员","专享","ChenyangGao"))
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", source)
    blocks = re.findall(r"```python\n(.*?)\n```",source,re.S)
    assert len(blocks) == 1
    output = StringIO()
    with redirect_stdout(output):
        exec(compile(blocks[0],str(path),"exec"),{})
    report["examples"].append({"file":path.name,"result":"passed",
        "output":output.getvalue().strip(),"sha256":hashlib.sha256(source.encode()).hexdigest()})

def check(name,cases,kind="exact"):
    report["independent_checks"].append({"name":name,"cases":cases,"kind":kind,"result":"passed"})

@lru_cache(None)
def stirling(n,k,first=False):
    if n == 0:
        return int(k == 0)
    if k <= 0 or k > n:
        return 0
    return stirling(n-1,k-1,first)+(n-1 if first else k)*stirling(n-1,k,first)

def fall(x,k):
    return prod((x-i for i in range(k)),start=Q(1))

def generalized_binomial(x,k):
    return fall(x,k)/factorial(k)

samples = [Q(-7,3),Q(-1),Q(0),Q(1,2),Q(2),Q(11,2)]
for n in range(11):
    for x in samples:
        assert x**n == sum(stirling(n,k)*fall(x,k) for k in range(n+1))
        assert fall(x,n) == sum((-1)**(n-k)*stirling(n,k,True)*x**k for k in range(n+1))
        assert prod((x+i for i in range(n)),start=Q(1)) == sum(stirling(n,k,True)*x**k for k in range(n+1))
    for m in range(n+1):
        assert sum(stirling(n,k)*(-1)**(k-m)*stirling(k,m,True) for k in range(m,n+1)) == int(n==m)
        assert sum((-1)**(n-k)*stirling(n,k,True)*stirling(k,m) for k in range(m,n+1)) == int(n==m)
        assert factorial(m)*stirling(n,m) == sum((-1)**(m-j)*comb(m,j)*j**n for j in range(m+1))
check("Stirling bases at rational points, inverse matrices, and surjection formula",11*6*3+66*3)

row=[1]
for n in range(1,11):
    old=row
    row=[(k+1)*(old[k] if k<len(old) else 0)+(n-k)*(old[k-1] if k else 0) for k in range(n)]
    assert row == row[::-1] and sum(row)==factorial(n)
    for k in range(n):
        explicit=sum((-1)**j*comb(n+1,j)*(k+1-j)**n for j in range(k+1))
        assert row[k] == explicit
    for x in samples:
        assert x**n == sum(row[k]*generalized_binomial(x+k,n) for k in range(n))
    for N in range(21):
        assert sum(x**n for x in range(1,N+1)) == sum(row[k]*comb(N+k+1,n+1) for k in range(n))
check("Eulerian explicit formula, symmetry, rational Worpitzky and power sums",55+20+60+210)

H=[Q(0)]
for n in range(1,1001):
    H.append(H[-1]+Q(1,n))
with localcontext() as ctx:
    ctx.prec=60
    gamma=Decimal("0.577215664901532860606512090082402431042159335939923598805767")
    for n in [1,2,3,10,30,100,300,1000]:
        actual=Decimal(H[n].numerator)/Decimal(H[n].denominator)
        d=Decimal(n)
        residual=actual-d.ln()-gamma-1/(2*d)+1/(12*d*d)
        assert Decimal(0)<residual<1/(120*d**4)
check("Quoted harmonic remainder bound at 60 decimal precision",8,"high_precision_finite_check")

for n in range(1,31):
    for degree in range(7):
        direct=sum(k**degree*H[k] for k in range(n))
        expanded=sum(stirling(degree,j)*factorial(j)*comb(n,j+1)*(H[n]-Q(1,j+1)) for j in range(degree+1))
        assert direct == expanded
    strict=sum(H[k-1]/k for k in range(1,n+1))
    assert 2*strict == H[n]**2-sum(Q(1,k*k) for k in range(1,n+1))
    value=sum(Q((-1)**(k-1)*comb(n,k)*(n-k)**n,k) for k in range(1,n+1))
    assert value == n**n*(H[n]-1)
check("Polynomial-weighted harmonic sums, strict triangle, and original U_n",270)

B=[Q(1)]
for m in range(1,21):
    B.append(-sum(comb(m+1,j)*B[j] for j in range(m))/(m+1))
def power_sum_poly(m,x):
    return sum(comb(m+1,j)*B[j]*x**(m+1-j) for j in range(m+1))/(m+1)
for m in range(21):
    for x in samples:
        assert power_sum_poly(m,x+1)-power_sum_poly(m,x)==x**m
    assert power_sum_poly(m,0)==0
# Coefficients of derivatives of tan, computed as integer polynomials.
P=[0,1]
for order in range(1,20):
    derivative=[(i+1)*P[i+1] for i in range(len(P)-1)]
    new=[0]*(len(derivative)+2)
    for i,a in enumerate(derivative):
        new[i]+=a
        new[i+2]+=a
    P=new
    if order%2:
        r=(order+1)//2
        predicted=(-1)**(r-1)*Q(2**(2*r)*(2**(2*r)-1),2*r)*B[2*r]
        assert P[0] == predicted and predicted.denominator==1
check("Bernoulli polynomial differences and independent tangent derivatives",21*7+10)

F=[0,1]
for _ in range(101):
    F.append(F[-1]+F[-2])
for n in range(1,100):
    assert F[n+1]*F[n-1]-F[n]**2 == (-1)**n
    for m in range(1,51):
        assert F[m+n if m+n<len(F) else 0] == F[m]*F[n+1]+F[m-1]*F[n] if m+n<len(F) else True
for n in range(3,13):
    for m in range(1,101):
        assert (F[m] % F[n] == 0) == (m % n == 0)
        assert (F[m] % (F[n]**2) == 0) == (m % (n*F[n]) == 0)
# All valid nonadjacent bit strings for F2 through F15: no duplicate totals.
totals=[]
for bits in product((0,1),repeat=14):
    if not any(a and b for a,b in zip(bits,bits[1:])):
        totals.append(sum(b*F[k+2] for k,b in enumerate(bits)))
assert len(set(totals))==len(totals)
assert sorted(totals)==list(range(F[16]))
check("Fibonacci determinant, addition, divisibility, and exhaustive Zeckendorf representations",len(totals)+2000+99)

def K(xs):
    a,b=0,1
    for x in xs:
        a,b=b,x*b+a
    return b

def edge_matching_sum(xs):
    # Enumerate subsets of edges of a path, rejecting overlapping dimers.
    value=0
    for edges in product((0,1),repeat=max(0,len(xs)-1)):
        if any(a and b for a,b in zip(edges,edges[1:])):
            continue
        occupied={i+j for i,e in enumerate(edges) if e for j in (0,1)}
        value+=prod(x for i,x in enumerate(xs) if i not in occupied)
    return value

rng=Random(20261022)
count=0
for length in range(9):
    for _ in range(30):
        xs=[rng.randint(-4,5) for _ in range(length)]
        assert K(xs)==edge_matching_sum(xs)
        for cut in range(1,length):
            assert K(xs)==K(xs[:cut])*K(xs[cut:])+K(xs[:cut-1])*K(xs[cut+1:])
        if length>=2:
            matrix=[[1,0],[0,1]]
            for x in xs:
                matrix=[[r[0]*x+r[1],r[0]] for r in matrix]
            assert matrix==[[K(xs),K(xs[:-1])],[K(xs[1:]),K(xs[1:-1])]]
        count+=1
for n in range(16):
    for z in [Q(-2),Q(0),Q(1,2),Q(1),Q(3)]:
        assert K([z]*n)==sum(comb(n-j,j)*z**(n-2*j) for j in range(n//2+1))
check("Continuant edge-match enumeration, split identities, matrix product, and uniform variables",count+80)

report["status"]="passed"
report["scope"]="Finite exact and high-precision checks supplement the articles' general proofs; infinite-series and asymptotic claims are not proved by these checks."
(ROOT / "verification" / "chapter6-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
