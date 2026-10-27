"""Verify the MPR post with exact small probability spaces and independent oracles."""
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction as F
from hashlib import sha256
from io import StringIO
from itertools import product
from math import exp
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / '第4卷-组合算法/MPR-数学准备再探.md'
text = NOTE.read_text(encoding='utf-8')
blocks = re.findall(r'```python\n(.*?)```', text, re.S)
assert len(blocks) == 1
capture = StringIO()
namespace = {}
with redirect_stdout(capture):
    exec(compile(blocks[0], str(NOTE), 'exec'), namespace)

cases = prefix_cases = bounded_difference_cases = tail_cases = 0
for m in range(2, 6):
    for n in range(0, 7):
        rows = list(product(range(m), repeat=n))
        vals = [m-len(set(row)) for row in rows]
        distribution = Counter(vals)
        # Independent occupancy-count recurrence, no named ball assignments.
        counts = {m: 1}
        for _ in range(n):
            nxt = defaultdict(int)
            for e, count in counts.items():
                nxt[e] += count * (m-e)
                if e:
                    nxt[e-1] += count * e
            counts = dict(nxt)
        assert {k:v for k,v in counts.items() if v} == dict(distribution)
        mean = sum((F(k*v, len(rows)) for k,v in distribution.items()), F(0))
        second = sum((F(k*k*v, len(rows)) for k,v in distribution.items()), F(0))
        positive = F(sum(v for k,v in distribution.items() if k>0), len(rows))
        assert mean == m * F(m-1,m)**n
        assert second == mean + m*(m-1)*F(m-2,m)**n
        assert mean**2 <= second
        assert mean**2/second <= positive <= min(F(1),mean)
        for t in [F(k,2) for k in range(1,2*m+1)]:
            actual = F(sum(abs(q-mean)>=t for q in vals),len(rows))
            assert actual <= min(F(1),(second-mean**2)/t**2)
            if n:
                assert float(actual) <= min(1,2*exp(-2*float(t*t)/n))+1e-12
            tail_cases += 1
        cases += 1
        if n<=4:
            for i in range(n+1):
                groups = defaultdict(list)
                for row,q in zip(rows,vals):
                    groups[row[:i]].append(q)
                for prefix, possible in groups.items():
                    exact = F(sum(possible),len(possible))
                    predicted = (m-len(set(prefix)))*F(m-1,m)**(n-i)
                    assert exact == predicted
                    prefix_cases += 1
            for row,q in zip(rows,vals):
                for i in range(n):
                    for b in range(m):
                        changed=row[:i]+(b,)+row[i+1:]
                        assert abs((m-len(set(changed)))-q)<=1
                        bounded_difference_cases += 1

# Every joint distribution on three indicators with integer weights 0..2.
# Ross requires no independence. Compare to actual event probability.
ross_cases = 0
patterns = list(product([0,1], repeat=3))
for weights in product(range(3), repeat=len(patterns)):
    total=sum(weights)
    if total == 0:
        continue
    actual = F(sum(w for bits,w in zip(patterns,weights) if any(bits)), total)
    lower=F(0)
    for j in range(3):
        on_weight=sum(w for bits,w in zip(patterns,weights) if bits[j])
        if on_weight:
            cond_mean=F(sum(sum(bits)*w for bits,w in zip(patterns,weights) if bits[j]),on_weight)
            lower+=F(on_weight,total)/cond_mean
    assert lower<=actual
    ross_cases+=1

# Pólya's one-step conditional identity, asymmetric initial states included.
polya_cases=0
for r in range(1,21):
    for b in range(1,21):
        assert F(r,r+b)*F(r+1,r+b+1)+F(b,r+b)*F(r,r+b+1)==F(r,r+b)
        polya_cases+=1

# Bounded optional stopping of a fair walk, and a path-maximum inequality.
stop_cases=0
for n in range(1,10):
    walks=list(product([-1,1],repeat=n))
    for boundary in range(1,5):
        terminal=[]
        crossed=0
        for steps in walks:
            s=0
            peak=0
            stopped=None
            for step in steps:
                s+=step
                peak=max(peak,s*s)
                if stopped is None and s>=boundary:
                    stopped=s
            terminal.append(s if stopped is None else stopped)
            crossed+=peak>=boundary*boundary
        assert sum(terminal)==0
        assert F(crossed,len(walks))<=F(n,boundary*boundary)
        stop_cases+=1

body=text.split('\n',1)[1].lstrip('\n')
report={
 'status':'passed', 'note':str(NOTE), 'python_blocks_executed':len(blocks),
 'example_stdout':capture.getvalue(), 'occupancy_distribution_cases':cases,
 'conditional_means_by_independent_grouping':prefix_cases,
 'single_coordinate_change_checks':bounded_difference_cases,
 'tail_checks':tail_cases, 'ross_joint_distributions':ross_cases,
 'polya_states':polya_cases, 'bounded_stopping_and_maximum_cases':stop_cases,
 'body_characters':len(body), 'body_sha256':sha256(body.encode()).hexdigest(),
 'limitation':'Finite exact checks support the derivations; they do not prove the general inequalities.'
}
(ROOT/'verification/taocp-mpr-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
