"""Execute every article example and independently audit important claims."""
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO
from itertools import combinations, product
from math import comb, factorial, gcd, isqrt, lcm, prod
from pathlib import Path
from random import Random
import json
import re

ROOT = Path(__file__).resolve().parents[1]
report = {"chapter": 4, "examples": [], "independent_checks": []}

for path in sorted((ROOT / "第04章-数论").glob("4.1.*.md")):
    text = path.read_text(encoding="utf-8")
    assert "图灵社区会员" not in text and "专享" not in text
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert text.count("$$") % 2 == 0
    assert text.count("```") % 2 == 0
    assert "参考：" in text and "专栏目录" in text
    blocks = re.findall(r"```python\n(.*?)\n```", text, re.S)
    assert blocks
    for i, code in enumerate(blocks, 1):
        output = StringIO()
        with redirect_stdout(output):
            exec(compile(code, str(path), "exec"), {})
        report["examples"].append({"file": path.name, "block": i,
                                   "result": "passed", "output": output.getvalue().strip()})

def checked(name, cases):
    report["independent_checks"].append({"name": name, "cases": cases, "result": "passed"})

def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]

def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))

for n in range(1, 101):
    left = sum(k*k + 3*d for d in divisors(n) for k in divisors(d))
    right = sum(k*k + 3*k*ell for k in divisors(n) for ell in divisors(n//k))
    assert left == right
checked("Divisor-chain double-sum bijection", 100)

for a in range(1, 81):
    for b in range(1, 81):
        assert gcd(a,b)*lcm(a,b) == a*b
checked("Gcd and lcm product identity", 6400)

for n in range(1, 61):
    assert n**n <= factorial(n)**2
    assert factorial(n)**2 * 4**n <= (n+1)**(2*n)
for n in range(41):
    for k in range(n+1):
        for p in [2,3,5,7]:
            def vp(x):
                result=0
                while x % p == 0:
                    result+=1
                    x//=p
                return result
            assert vp(comb(n,k)) == vp(factorial(n))-vp(factorial(k))-vp(factorial(n-k))
checked("Factorial bounds and binomial prime exponents", 60 + 861*4)

levels = [(0,1),(1,0)]
for _ in range(7):
    new=[]
    for (a,b),(c,d) in zip(levels, levels[1:]):
        assert b*c-a*d == 1
        assert gcd(a+c,b+d) == 1
        new.extend([(a,b),(a+c,b+d)])
    levels = new + [levels[-1]]
assert len(set(levels)) == len(levels)
for N in range(1, 41):
    farey=sorted({Fraction(a,b) for b in range(1,N+1) for a in range(b+1)})
    for x,y in zip(farey,farey[1:]):
        a,b,c,d=x.numerator,x.denominator,y.numerator,y.denominator
        assert b*c-a*d == 1 and b+d>N
checked("Stern-Brocot invariants and Farey neighbors", 7+40)

for m in range(1,31):
    for c in range(-8,9):
        for delta in range(-30,31):
            assert ((c*delta)%m==0) == (delta%(m//gcd(c,m))==0)
checked("Congruence cancellation including zero and negative factors",30*17*61)

for m in range(1,13):
    for n in range(1,13):
        for a in range(m):
            for b in range(n):
                solutions=[x for x in range(lcm(m,n)) if x%m==a and x%n==b]
                assert len(solutions) == int((a-b)%gcd(m,n)==0)
checked("Noncoprime CRT compatibility and uniqueness", sum(range(1,13))**2)

for m in range(1,501):
    n=m
    power2=0
    while n%2==0:
        n//=2
        power2+=1
    odd_count=0
    p=3
    while p*p<=n:
        if n%p==0:
            odd_count+=1
            while n%p==0:
                n//=p
        p+=2
    odd_count+=int(n>1)
    predicted=2**odd_count * (1 if power2<2 else 2 if power2==2 else 4)
    assert predicted == sum((x*x-1)%m==0 for x in range(m))
checked("Square roots of unity for every modulus 1 to 500",500)

rng=Random(20261022)
f=[0]+[rng.randint(-100,100) for _ in range(200)]
g=[0]+[sum(f[d] for d in divisors(n)) for n in range(1,201)]
mu=[0]*201
mu[1]=1
for n in range(2,201):
    mu[n]=-sum(mu[d] for d in divisors(n) if d<n)
for n in range(1,201):
    assert sum(mu[d]*g[n//d] for d in divisors(n))==f[n]
    phi=sum(gcd(a,n)==1 for a in range(n))
    if n>1:
        for a in range(-10,11):
            if gcd(a,n)==1:
                assert pow(a,phi,n)==1
checked("Mobius inversion for a nonmultiplicative random function and Euler theorem",200)

for p in [2,3,5,7]:
    for j in range(1,5):
        for a in range(-10,11):
            assert (pow(a,p**j,p**j)-pow(a,p**(j-1),p**j)) % (p**j)==0
checked("Prime-power congruence used for necklace integrality",4*4*21)

assert len(report["examples"]) == 9
report["status"]="passed"
report["scope"]="Exact finite checks complement the articles' proofs; they do not replace general arguments."
(ROOT/"verification"/"chapter4-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
