"""Execute the five authored examples and independent finite checks."""
from pathlib import Path
from itertools import permutations, product
from collections import Counter
from fractions import Fraction
import contextlib
import hashlib
import io
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ['5.1-排列的组合性质.md', '5.2-内部排序.md', '5.3-最优排序.md',
         '5.4-外部排序.md', '5.5-小结历史和文献目录.md']
PAGES = ['9-68', '68-170', '170-233', '234-355', '355-365']
SUMMARIES = [
    '从反序表的可逆构造出发，推导逆序数分布与均值方差，连接多重集合计数、路段的欧拉数递推、图表对及对合。用小规模排列枚举检查表示转换和组合恒等式。',
    '按插入、交换、选择、合并和分布梳理内部排序，区分比较次数、移动量、空间与稳定性。推导插入右移数与逆序的关系，提供稳定插入、合并和基数排序实现。',
    '用比较决策树推导排序下界，说明信息量下界与可实现构造的区别；连接合并、选择和固定排序网络。通过0—1原理与穷举验证四输入网络，并用配对法同时寻找最小值和最大值。',
    '从初始路段、多路合并和缓冲预算推导外部排序的趟数与简化I/O成本，解释替代选择及磁带调度。用受限候选集合模拟路段生成与分趟合并，明确模拟与真正外存程序的边界。',
    '把全章方法接回输入结构与成本模型，解释怎样阅读MIX排序性能表。用比较和写入计数展示实现差异，并依据原书梳理穿孔卡片、存储程序、缓冲及分析模型的发展线索。',
]
EXPECTED = [
    '[1, 2, 0, 0] 3\n[3, 1, 4, 2]\n([[1, 2], [3, 4]], [[1, 3], [2, 4]])\n[1, 11, 11, 1]',
    "[(4, 'B'), (4, 'E'), (13, 'D'), (21, 'A'), (21, 'C')] 9 6\nTrue True",
    '5 5 16 24\n(0, 1, 0, 1)\n(1, 9, 7)',
    '[[3, 7, 8], [1, 2, 4, 5, 6, 9], [0]]\n3 [3, 2, 1]\n[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]\n3 2',
    'ordered (7, 7) (28, 0)\n0 (7, 28)\n4 (35, 28)\nreversed (28, 35) (28, 8)\n0 (28, 28)\n4 (168, 60)',
]
report = {'articles': [], 'checks': {}}
envs = []
for filename, expected in zip(FILES, EXPECTED):
    source = (ROOT / '第3卷-排序与查找/第05章-排序'/filename).read_text(encoding='utf-8')
    title, body = source.split('\n', 1)
    title = title.removeprefix('# ')
    body = body.lstrip('\n').rstrip() + '\n'
    assert 5 <= len(title) <= 100
    assert source.count('```') % 2 == 0 and source.count('$$') % 2 == 0
    assert not any(x in source for x in ('TODO', '待补'))
    blocks = re.findall(r'```python\n(.*?)\n```', source, re.S)
    outputs = re.findall(r'```text\n(.*?)\n```', source, re.S)
    assert len(blocks) == len(outputs) == 1 and outputs[0] == expected
    scope, stdout = {}, io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(blocks[0], filename+':python', 'exec'), scope)
    assert stdout.getvalue().strip() == expected, (filename, stdout.getvalue())
    envs.append(scope)
    report['articles'].append({'filename':filename, 'title':title,
        'body_characters':len(body), 'python_blocks':1,
        'sha256':hashlib.sha256(body.encode()).hexdigest(), 'example_output':expected})

def inversions(a):
    return sum(a[i] > a[j] for i in range(len(a)) for j in range(i+1, len(a)))

def raises(kind, function, *args):
    try:
        function(*args)
    except kind:
        return
    raise AssertionError((function.__name__, args, kind))

def is_tableau(t, n):
    assert sorted(x for row in t for x in row) == list(range(1, n+1))
    assert all(len(t[i]) >= len(t[i+1]) for i in range(len(t)-1))
    assert all(all(a < b for a,b in zip(row,row[1:])) for row in t)
    assert all(t[r-1][c] < t[r][c] for r in range(1,len(t)) for c in range(len(t[r])))

e = envs[0]
permutation_cases = 0
t_prev, t_now = 1, 1
involution_counts = [1, 1]
for n in range(2,8):
    t_prev,t_now = t_now,t_now+(n-1)*t_prev
    involution_counts.append(t_now)
for n in range(8):
    inv_hist, desc_hist, distinct_pairs = Counter(),Counter(),set()
    involutions = 0
    for a in permutations(range(1,n+1)):
        b = e['inversion_table'](a)
        assert e['restore'](b) == list(a)
        inv = inversions(a)
        assert sum(b) == inv
        inv_hist[inv] += 1
        desc_hist[sum(x > y for x,y in zip(a,a[1:]))] += 1
        p,q = e['tableaux'](a)
        is_tableau(p,n); is_tableau(q,n)
        assert list(map(len,p)) == list(map(len,q))
        inverse = [a.index(j)+1 for j in range(1,n+1)]
        assert e['tableaux'](inverse) == (q,p)
        assert (p == q) == (list(a) == inverse)
        involutions += p == q
        distinct_pairs.add((tuple(map(tuple,p)),tuple(map(tuple,q))))
        permutation_cases += 1
    assert len(distinct_pairs) == math.factorial(n)
    assert involutions == involution_counts[n]
    assert e['eulerian_row'](n) == [desc_hist[k] for k in range(max(n,1))]
    total = math.factorial(n)
    mean = sum(Fraction(k*v,total) for k,v in inv_hist.items())
    variance = sum(Fraction(v,total)*(k-mean)**2 for k,v in inv_hist.items())
    assert mean == Fraction(n*(n-1),4)
    assert variance == Fraction(n*(n-1)*(2*n+5),72)
    poly = [1]
    for width in range(1,n+1):
        new = [0]*(len(poly)+width-1)
        for i,c in enumerate(poly):
            for j in range(width): new[i+j] += c
        poly = new
    assert poly == [inv_hist[k] for k in range(len(poly))]
multiset_cases = 0
for counts in [(2,1,1),(2,2,1),(3,2),(2,2,2)]:
    a = [i for i,c in enumerate(counts) for _ in range(c)]
    arrangements = set(permutations(a))
    expected_count = math.factorial(len(a))//math.prod(math.factorial(c) for c in counts)
    assert len(arrangements) == expected_count
    assert Fraction(sum(map(inversions,arrangements)),len(arrangements)) == Fraction(len(a)**2-sum(c*c for c in counts),4)
    multiset_cases += len(arrangements)
raises(ValueError,e['restore'],[2,0])
raises(ValueError,e['inversion_table'],[1,1])
report['checks']['permutations'] = {'permutation_cases':permutation_cases,'multiset_arrangements':multiset_cases,'tableau_inverse_and_bijection':True,'exact_moments_and_eulerian_rows':True}

e = envs[1]
stable_cases = 0
for n in range(8):
    for keys in product(range(3),repeat=n):
        records = list(zip(keys,range(n)))
        expected = sorted(records,key=lambda x:x[0])
        actual,c,shifts = e['insertion'](records)
        inv = inversions(keys)
        assert actual == expected and shifts == inv
        assert inv <= c <= inv+max(n-1,0)
        assert e['merge_sort'](records) == expected
        for base in (2,3,10): assert e['radix_sort'](records,base) == expected
        stable_cases += 1
rng = random.Random(20261025)
for _ in range(400):
    keys = [rng.randrange(100000) for _ in range(rng.randrange(100))]
    records = list(zip(keys,range(len(keys))))
    expected = sorted(records,key=lambda x:x[0])
    assert e['merge_sort'](records) == e['insertion'](records)[0] == expected
    assert e['radix_sort'](records,16) == expected
raises(ValueError,e['radix_sort'],[(-1,'bad')])
raises(ValueError,e['radix_sort'],[],1)
class CountKey(int):
    comparisons = 0
    def __le__(self, other):
        CountKey.comparisons += 1
        return int(self) <= int(other)
merge_permutation_cases = 0
for n in range(1,8):
    maximum = 0
    for a in permutations(range(n)):
        CountKey.comparisons = 0
        e['merge_sort']([(CountKey(x),x) for x in a])
        maximum = max(maximum,CountKey.comparisons)
        merge_permutation_cases += 1
    ceil_log = (n-1).bit_length()
    assert maximum == n*ceil_log-2**ceil_log+1
report['checks']['internal_sorting'] = {'exhaustive_stability_cases':stable_cases,'random_large_key_cases':400,'merge_worst_case_permutations':merge_permutation_cases}

e = envs[2]
network_cases = 0
for a in product(range(-2,3),repeat=4):
    assert e['network_sort'](a,e['NETWORK4']) == sorted(a)
    network_cases += 1
minmax_cases = 0
for n in range(1,8):
    for a in product(range(3),repeat=n):
        lo,hi,c = e['pair_minmax'](a)
        assert (lo,hi) == (min(a),max(a))
        assert c == (3*n+1)//2-2
        minmax_cases += 1
raises(ValueError,e['pair_minmax'],[])
assert e['network_sort']((0,1,0,1),e['NETWORK4'][:-1]) != [0,0,1,1]
report['checks']['optimal_sorting'] = {'network_inputs_with_duplicates':network_cases,'paired_minmax_inputs':minmax_cases,'removed_comparator_counterexample':True}

e = envs[3]
external_cases = 0
for n in range(8):
    for a in product(range(3),repeat=n):
        for capacity in range(1,5):
            runs,peak = e['replacement_runs'](a,capacity)
            assert peak <= capacity
            assert Counter(x for run in runs for x in run) == Counter(a)
            assert all(run == sorted(run) for run in runs)
            assert all(len(run) >= capacity for run in runs[:-1])
            for fan in (2,3):
                actual,levels = e['merge_passes'](runs,fan)
                assert actual == sorted(a)
                assert len(levels)-1 == e['required_passes'](len(runs),fan)
            external_cases += 1
for n in range(1,65):
    for capacity in (1,2,5,16,65):
        ascending,_ = e['replacement_runs'](range(n),capacity)
        descending,_ = e['replacement_runs'](range(n-1,-1,-1),capacity)
        assert ascending == [list(range(n))]
        assert len(descending) == (n+capacity-1)//capacity
for run_count in range(1001):
    for fan in (2,3,4,7):
        t = e['required_passes'](run_count,fan)
        assert (t == 0 and run_count <= 1) or (fan**(t-1) < run_count <= fan**t)
raises(ValueError,e['replacement_runs'],[],0)
raises(ValueError,e['merge_passes'],[[2,1]],2)
raises(ValueError,e['merge_passes'],[],1)
report['checks']['external_sorting'] = {'replacement_and_merge_cases':external_cases,'monotone_capacity_pairs':320,'integer_pass_bounds':4004,'scope':'Logical simulation; no physical I/O performance measured'}

e = envs[4]
metric_cases = 0
for n in range(8):
    for a in permutations(range(n)):
        left,ci,wi = e['insertion_metrics'](a)
        right,cs,ws = e['selection_metrics'](a)
        assert left == right == list(range(n))
        assert wi == inversions(a)+max(n-1,0)
        assert cs == n*(n-1)//2 and ws % 2 == 0 and ws <= 2*max(n-1,0)
        metric_cases += 1
report['checks']['cost_model'] = {'exact_count_permutations':metric_cases,'scope':'Declared comparison and list-slot assignment counts, not wall-clock benchmarks'}
report['all_passed'] = True

report['all_passed'] = True
(ROOT / 'verification/taocp-chapter5-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 5: passed')
