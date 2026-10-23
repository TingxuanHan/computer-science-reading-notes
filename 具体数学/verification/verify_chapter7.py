"""Exact checks supporting (not replacing proofs in) the chapter 7 articles."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import combinations, permutations
from math import comb, factorial, gcd
from functools import lru_cache
from contextlib import redirect_stdout
import io
import json
import re

ROOT = Path(__file__).resolve().parents[1]
counts = {}
examples = []
def check(group, actual, expected):
    assert actual == expected, (group, actual, expected)
    counts[group] = counts.get(group, 0) + 1

for path in sorted((ROOT / "第07章-生成函数").glob("7.1.*.md")):
    source = path.read_text(encoding="utf-8")
    code = re.findall(r"```python\n(.*?)```", source, re.S)
    assert len(code) == 1
    capture = io.StringIO()
    with redirect_stdout(capture):
        exec(compile(code[0], str(path), "exec"), {})
    examples.append({"file":path.name,"status":"passed","stdout":capture.getvalue().strip()})
    assert "专享" not in source and "@qq" not in source
    assert source.count("$$") % 2 == 0

def mul(a, b, N):
    out = [Q(0)] * (N + 1)
    for i, x in enumerate(a[:N+1]):
        for j, y in enumerate(b[:N+1-i]):
            out[i+j] += x*y
    return out

def inv(a, N):
    assert a[0]
    out = [1 / Q(a[0])]
    for n in range(1, N+1):
        out.append(-sum(a[k]*out[n-k] for k in range(1,min(n,len(a)-1)+1))/a[0])
    return out

def binom(r, k):
    result = Q(1)
    for j in range(k):
        result *= (r-j) / Q(j+1)
    return result

def fpower(a, r, N):
    assert a[0] == 1
    delta = list(a) + [Q(0)] * max(0, N+1-len(a))
    delta[0] = 0
    term = [Q(1)] + [Q(0)]*N
    out = list(term)
    for k in range(1, N+1):
        term = mul(term, delta, N)
        c = binom(r, k)
        out = [x+c*y for x,y in zip(out,term)]
    return out

def fexp(a, N):
    assert a[0] == 0
    out = [Q(1)]
    for n in range(1, N+1):
        out.append(sum(k*a[k]*out[n-k] for k in range(1,n+1))/n)
    return out

# Coin-count vector enumeration is independent of the dynamic-programming loop.
coins = [1,5,10,25,50]
@lru_cache(None)
def coin_tuples(n, index=0):
    if index == len(coins)-1:
        return int(n % coins[index] == 0)
    return sum(coin_tuples(n-k*coins[index],index+1)
               for k in range(n//coins[index]+1))
ways = [1]+[0]*1000
for d in coins:
    for n in range(d,len(ways)):
        ways[n] += ways[n-d]
for n in range(201):
    check("coin_tuple_enumeration",ways[n],coin_tuples(n))
A = [1]
for d in coins:
    factor = [int(j%d==0) for j in range(51-d)]
    A = mul(A,factor,len(A)+len(factor)-2)
check("coin_numerator",[A[i] for i in [0,50,100,150]],[1,45,52,2])
for n in range(1001):
    q,r = divmod(n,50)
    value = sum(A[r+50*j]*comb(q-j+4,4)
                for j in range(q+1) if r+50*j<len(A))
    check("coin_all_residues",value,ways[n])

# Binomial sums and independent bitmask search, including empty rectangles.
@lru_cache(None)
def grid(height,width,mask=0):
    if mask == (1<<(height*width))-1:
        return 1
    i = next(i for i in range(height*width) if not mask & (1<<i))
    row,col=divmod(i,width)
    total=0
    for r,c in [(row+1,col),(row,col+1)]:
        if r<height and c<width:
            j=r*width+c
            if not mask&(1<<j):
                total += grid(height,width,mask|(1<<i)|(1<<j))
    return total
U=mul([1,0,-1],inv([1,0,-4,0,1],12),12)
for n in range(11):
    check("domino_2_by_n",grid(2,n),sum(comb(n-j,j) for j in range(n//2+1)))
    check("domino_3_by_n",grid(3,n),U[n])

F=[0,1]
for _ in range(300):
    F.append(F[-1]+F[-2])
for n in range(101):
    check("fibonacci_convolution",5*sum(F[k]*F[n-k] for k in range(n+1)),
          2*n*F[n+1]-(n+1)*F[n])
for m in range(1,10):
    generated=mul([0,F[m]],inv([1,-(F[m-1]+F[m+1]),(-1)**m],25),25)
    for n in range(26):
        check("fibonacci_subsequence",generated[n],F[m*n])

# Trees in fan graphs: brute-force edge selection and connectivity test.
def tree_count(vertices, edges):
    total=0
    for selected in combinations(edges,vertices-1):
        p=list(range(vertices))
        def find(x):
            while p[x]!=x:
                x=p[x]
            return x
        for u,v in selected:
            u,v=find(u),find(v)
            if u==v:
                break
            p[u]=v
        else:
            total+=1
    return total
for n in range(1,9):
    edges=[(0,k) for k in range(1,n+1)]+[(k,k+1) for k in range(1,n)]
    check("fan_spanning_trees",tree_count(n+1,edges),F[2*n])

N=14
S=[[0]*(N+1) for _ in range(N+1)]
C=[[0]*(N+1) for _ in range(N+1)]
S[0][0]=C[0][0]=1
for n in range(1,N+1):
    for k in range(1,n+1):
        S[n][k]=k*S[n-1][k]+S[n-1][k-1]
        C[n][k]=(n-1)*C[n-1][k]+C[n-1][k-1]
expminus=[Q(0)]+[Q(1,factorial(n)) for n in range(1,N+1)]
logarithm=[Q(0)]+[Q(1,n) for n in range(1,N+1)]
sp=cp=[Q(1)]+[Q(0)]*N
for k in range(N+1):
    if k:
        sp=mul(sp,expminus,N)
        cp=mul(cp,logarithm,N)
    for n in range(N+1):
        check("stirling_second_egf",sp[n]*factorial(n)/factorial(k),S[n][k])
        check("stirling_first_egf",cp[n]*factorial(n)/factorial(k),C[n][k])

# Eulerian bivariate generating function against direct permutation counts.
euler=[]
for n in range(8):
    row=[0]*max(n,1)
    for p in permutations(range(n)):
        row[sum(p[i]>p[i+1] for i in range(n-1))]+=1
    euler.append(row)
for u in [Q(-2),Q(0),Q(1,2),Q(2),Q(3)]:
    denominator=[(u-1)**n/Q(factorial(n)) for n in range(8)]
    denominator[0]-=u
    coefficients=[(1-u)*x for x in inv(denominator,7)]
    for n in range(8):
        check("eulerian_egf",coefficients[n]*factorial(n),
              sum(a*u**k for k,a in enumerate(euler[n])))

H=[Q(0)]
for n in range(1,81):
    H.append(H[-1]+Q(1,n))
for n in range(51):
    for m in range(n+1):
        lhs=sum(Q(comb(k,m),n-k) for k in range(m,n))
        check("harmonic_convolution",lhs,comb(n,m)*(H[n]-H[m]))

# Generalized B and E series: solve defining equations by coefficient iteration.
N=10
for t in [Q(-1),Q(0),Q(1,2),Q(1),Q(2),Q(3)]:
    B=E=[Q(1)]+[Q(0)]*N
    for _ in range(N):
        B=[Q(1)]+fpower(B,t,N)[:N]
        inner=[Q(0)]+fpower(E,t,N)[:N]
        E=fexp(inner,N)
    for r in [Q(-2),Q(0),Q(1,2),Q(1),Q(3)]:
        b=fpower(B,r,N)
        e=fpower(E,r,N)
        for n in range(1,N+1):
            check("generalized_binomial",b[n],r/n*binom(t*n+r-1,n-1))
            check("generalized_exponential",e[n],r*(t*n+r)**(n-1)/factorial(n))

# Check the cycle lemma by enumeration of positions, including periodic words.
for m in range(2,5):
    for n in range(5):
        for r in range(1,4):
            length=m*n+r
            good=0
            for negatives in combinations(range(length),n):
                word=[1]*length
                for j in negatives:
                    word[j]=1-m
                prefix=0
                positive=True
                for x in word:
                    prefix+=x
                    positive &= prefix>0
                good+=positive
            check("raney_positive_words",good,Q(r*comb(length,n),length))

# Bernoulli numbers from formal inversion, checked against their recurrence.
N=12
bernoulli=inv([Q(1,factorial(n+1)) for n in range(N+1)],N)
bernoulli=[x*factorial(n) for n,x in enumerate(bernoulli)]
for m in range(1,N+1):
    check("bernoulli_inverse",sum(comb(m+1,j)*bernoulli[j] for j in range(m+1)),0)

# Mobius from squarefree factorization, phi from direct coprimality.
def mu(n):
    distinct=[]
    for p in range(2,n+1):
        if n%p==0 and all(p%d for d in range(2,int(p**0.5)+1)):
            if n%(p*p)==0:
                return 0
            distinct.append(p)
    return (-1)**len(distinct)
M=[0]+[mu(n) for n in range(1,101)]
P=[0]+[sum(gcd(k,n)==1 for k in range(1,n+1)) for n in range(1,101)]
for n in range(1,101):
    ds=[d for d in range(1,n+1) if n%d==0]
    check("dirichlet_mu_unit",sum(M[d] for d in ds),int(n==1))
    check("dirichlet_phi_identity",sum(M[d]*(n//d) for d in ds),P[n])
    for m in range(1,100//n+1):
        if gcd(m,n)==1:
            check("multiplicativity_mu",M[m*n],M[m]*M[n])
            check("multiplicativity_phi",P[m*n],P[m]*P[n])

report={"chapter":7,"status":"passed","python_examples":examples,
        "independent_exact_checks":counts,"total_independent_checks":sum(counts.values()),
        "limitations":"Finite exact checks supplement, not replace, the general proofs and convergence conditions in the articles."}
(ROOT/"verification/chapter7-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"examples":len(examples),"checks":sum(counts.values()),"status":"passed"}))
