"""Run all examples, independent finite checks, and a symbolic certificate check."""
from contextlib import redirect_stdout
from fractions import Fraction as F
from io import StringIO
from itertools import combinations
from math import comb, factorial, prod
from pathlib import Path
from random import Random
import json
import re

ROOT=Path(__file__).resolve().parents[1]
report={"chapter":5,"examples":[],"independent_checks":[]}
def checked(name,cases,kind="exact_finite_check"):
    report["independent_checks"].append({"name":name,"cases":cases,"kind":kind,"result":"passed"})

for path in sorted((ROOT / "第05章-二项式系数").glob("5.1.*.md")):
    text=path.read_text(encoding="utf-8")
    assert "图灵社区会员" not in text and "专享" not in text
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",text)
    assert text.count("$$")%2==0 and text.count("```")%2==0
    assert "参考：" in text and "专栏目录" in text
    blocks=re.findall(r"```python\n(.*?)\n```",text,re.S)
    assert len(blocks)==1
    for i,code in enumerate(blocks,1):
        output=StringIO()
        with redirect_stdout(output):
            exec(compile(code,str(path),"exec"),{})
        report["examples"].append({"file":path.name,"block":i,
            "result":"passed","output":output.getvalue().strip(),"characters":len(text)})

def C(a,k):
    return F(0) if k<0 else prod((F(a-j,j+1) for j in range(k)),start=F(1))
def rising(a,k):
    return prod((a+j for j in range(k)),start=F(1))

# Independently count subsets classified by their second-smallest element.
count=0
for m in range(1,11):
    for r in range(m):
        by_second={k:0 for k in range(m+1)}
        for subset in combinations(range(m+1),r+2):
            by_second[subset[1]]+=1
        for k in range(m-r+1):
            assert by_second[k]==k*comb(m-k,r)
        assert sum(by_second.values())==comb(m+1,r+2)
        count+=1
checked("Weighted sum by explicit subset enumeration",count)

# Random polynomials: alternating differences detect degree and leading coefficient.
rng=Random(20261022)
for n in range(13):
    for trial in range(10):
        coefficients=[rng.randint(-20,20) for _ in range(n+1)]
        lhs=sum((-1)**k*comb(n,k)*sum(a*k**j for j,a in enumerate(coefficients)) for k in range(n+1))
        assert lhs==(-1)**n*factorial(n)*coefficients[-1]
checked("Finite differences of random polynomials",130)

# Coefficients of the quadratic transformation, by direct series composition.
for a,b in [(F(1,3),F(2,5)),(F(-3,2),F(7,3)),(F(2),F(3))]:
    c=a+b+F(1,2)
    for n in range(31):
        lhs=rising(2*a,n)*rising(2*b,n)/(rising(c,n)*factorial(n))
        rhs=sum(rising(a,k)*rising(b,k)/(rising(c,k)*factorial(k))*4**k
                *(-1)**(n-k)*comb(k,n-k) for k in range((n+1)//2,n+1))
        assert lhs==rhs
checked("Quadratic hypergeometric transformation by exact coefficient composition",93)

# Generate B_t from its functional equation for integer t, compare powers B_t^r.
N=16
def convolution(a,b):
    out=[F(0)]*N
    for i,x in enumerate(a):
        for j,y in enumerate(b[:N-i]):
            out[i+j]+=x*y
    return out
def power(a,r):
    out=[F(1)]+[F(0)]*(N-1)
    for _ in range(r): out=convolution(out,a)
    return out
for t in range(5):
    b=[F(1)]+[F(0)]*(N-1)
    for _ in range(N):
        bt=power(b,t)
        b=[F(1)]+bt[:N-1]
    for r in range(5):
        br=power(b,r)
        assert br[0]==1
        for n in range(1,N):
            assert br[n]==F(r,n)*C(t*n+r-1,n-1)
checked("Generalized binomial coefficients against functional-equation iteration",5*5*(N-1))

# Symbolic bivariate polynomial arithmetic, not numerical sampling.
class Poly:
    def __init__(self,terms):
        self.terms={ij:F(v) for ij,v in terms.items() if v}
    @staticmethod
    def of(x):
        return x if isinstance(x,Poly) else Poly({(0,0):F(x)})
    def __add__(self,other):
        out=self.terms.copy()
        for ij,v in self.of(other).terms.items(): out[ij]=out.get(ij,0)+v
        return Poly(out)
    __radd__=__add__
    def __neg__(self): return Poly({ij:-v for ij,v in self.terms.items()})
    def __sub__(self,other): return self+-self.of(other)
    def __rsub__(self,other): return self.of(other)+-self
    def __mul__(self,other):
        out={}
        for (i,j),v in self.terms.items():
            for (a,b),w in self.of(other).terms.items():
                ij=(i+a,j+b)
                out[ij]=out.get(ij,0)+v*w
        return Poly(out)
    __rmul__=__mul__
    def __pow__(self,p):
        out=self.of(1)
        for _ in range(p): out=out*self
        return out
n=Poly({(1,0):1}); k=Poly({(0,1):1})
def s(n,k): return (2*n+3)*(8*k*k-12*k-16*(n+1)*(n+2))
left=(n+1)**3*(n+1-k)**2*(n+2-k)**2
left-=(2*n+3)*(17*n*n+51*n+39)*(n+1+k)**2*(n+2-k)**2
left+=(n+2)**3*(n+1+k)**2*(n+2+k)**2
right=(n+k+1)**2*(n+2-k)**2*s(n,k+1)-k**4*s(n,k)
assert not (left-right).terms
checked("Apery certificate after common-factor removal: every polynomial coefficient is zero",1,
        "symbolic_bivariate_polynomial_identity")

assert len(report["examples"])==8
report["status"]="passed"
report["scope"]="All article examples executed. Finite tests complement proofs; the Apery certificate also has an exact symbolic polynomial check."
(ROOT/"verification"/"chapter5-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
