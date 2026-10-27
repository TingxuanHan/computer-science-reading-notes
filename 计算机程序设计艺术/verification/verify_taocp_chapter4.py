"""Run all Chapter 4 examples and independent mathematical checks."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
from bisect import bisect_left
import contextlib
import hashlib
import io
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ['4.1-定位计数系统.md', '4.2-浮点算术.md', '4.3-多精度算术.md',
         '4.4-进制转换.md', '4.5-有理算术.md', '4.6-多项式算术.md', '4.7-幂级数的操作.md']
PAGES = ['175-192', '192-239', '239-289', '289-299', '299-380', '380-480', '480-491']
SUMMARIES = [
    '从位权与数字范围出发，解释定点数、补码、负进制、平衡三进制和混合进制的运算规则。用编码与独立解码验证数值不变，并说明字长、溢出与进位各自的含义。',
    '推导浮点间距和最近舍入误差界，区分输入误差、单次舍入与相消放大。以精确分数模拟十进制有效数字，展示结合律失效与居中取偶，再梳理原书双精度实现和首位数字分布。',
    '把大整数拆成数字块，证明进位与乘法中间值的范围，解释长除法估商及修正、中国剩余恢复和Karatsuba分治。提供经典乘法、单块除法及模恢复代码，并与完整整数运算交叉核验。',
    '统一解释整数与小数的四种基本转换方法，证明有限展开取决于最简分母能否整除基数幂。用精确余数识别循环节，再通过分数公式反向恢复，讨论舍入、进位和转换成本。',
    '推导交叉约分乘法与分数加法的简化约分公式，连接欧几里得算法、贝祖系数、连分数和斐波那契最坏情形。区分gcd、因子分解与素性判定，附规范分数和小整数分解实现。',
    '从系数域和规范表示出发，连接多项式长除法、首一gcd、重因子和有限域分解。解释二进制求幂、加法链与Horner求值，使用有理数系数验证商余恒等式及导数递推。',
    '以模x的N次方解释有限项精度，推导幂级数除法、牛顿求逆的精度翻倍和指数递推。区分乘法逆元、复合反演与迭代，用斐波那契数、阶乘倒数和卡特兰数核验精确系数。',
]
EXPECTED = [
    '[1, 1, 0, 1, 1, 1]\n[1, 0, -1]\n-13\n-128',
    '0 1\n1/2000 0\n31/25\n63/50',
    '4001620161\n1031 16\n173',
    '[4, 3]\n[0, 0, 1] []\n[0] [0, 0, 1, 1]\n[0, 8] [3]',
    '(15, 4)\n(67, 44)\n2 -9 47 2\n[2, 2, 2, 3, 3, 5]',
    "['-1', '1', '1'] ['3']\n8 10\n['-1', '1']\n32768 6",
    "['1', '1', '2', '3', '5', '8', '13', '21']\n['1', '1', '1/2', '1/6', '1/24', '1/120']\n['0', '1', '1', '2', '5', '14', '42']",
]
report = {'articles': [], 'checks': {}}
envs = []
for name, expected in zip(FILES, EXPECTED):
    source = (ROOT / '第2卷-半数值算法/第04章-算术' / name).read_text(encoding='utf-8')
    heading, body = source.split('\n', 1)
    body = body.lstrip('\n').rstrip() + '\n'
    assert len(heading.removeprefix('# ')) <= 100
    assert source.count('```') % 2 == 0 and source.count('$$') % 2 == 0
    assert not any(term in source for term in ('TODO', '待补'))
    blocks = re.findall(r'```python\n(.*?)\n```', source, re.S)
    outputs = re.findall(r'```text\n(.*?)\n```', source, re.S)
    assert len(blocks) == len(outputs) == 1 and outputs[0] == expected
    env, stdout = {}, io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(blocks[0], name + ':python', 'exec'), env)
    assert stdout.getvalue().strip() == expected, (name, stdout.getvalue())
    envs.append(env)
    report['articles'].append({'filename': name, 'title': heading.removeprefix('# '),
        'body_characters': len(body), 'python_blocks': len(blocks),
        'sha256': hashlib.sha256(body.encode()).hexdigest(), 'example_output': expected})


def raises(kind, fn, *args):
    try:
        fn(*args)
    except kind:
        return
    raise AssertionError((fn.__name__, args, kind))


rng = random.Random(20261024)
e = envs[0]
encoding_cases = 0
for base in range(-7, -1):
    for n in range(-1000, 1001):
        ds = e['negabase'](n, base)
        assert all(0 <= d < -base for d in ds)
        assert len(ds) == 1 or ds[0] != 0
        assert sum(d * base ** i for i, d in enumerate(ds[::-1])) == n
        encoding_cases += 1
for p in range(1, 8):
    values = {sum(d * 3 ** i for i, d in enumerate(ds)) for ds in product((-1, 0, 1), repeat=p)}
    assert values == set(range(-(3**p - 1)//2, (3**p - 1)//2 + 1))
    for n in values:
        ds = e['balanced3'](n)
        assert len(ds) <= p and all(d in (-1, 0, 1) for d in ds)
        assert sum(d * 3 ** i for i, d in enumerate(ds[::-1])) == n
for width in range(1, 13):
    for raw in range(1 << width):
        value = e['signed_word'](raw, width)
        assert -(1 << (width - 1)) <= value < (1 << (width - 1))
        assert value % (1 << width) == raw
raises(ValueError, e['negabase'], 1, -1)
raises(ValueError, e['signed_word'], 256, 8)
report['checks']['representations'] = {'negative_base_cases': encoding_cases, 'balanced_widths': 7, 'signed_widths': 12}

# Independent nearest representable value, found by sorted-grid lookup.
rounder = envs[1]['round_decimal']
round_cases = 0
for p in (1, 2, 3):
    grid = {F(c) * F(10) ** exponent: c % 2 for exponent in range(-8, 7)
            for c in range(10**(p-1), 10**p)}
    values = sorted(grid)
    samples = [F(rng.randrange(1, 2000000), rng.randrange(1, 10000)) for _ in range(1500)]
    samples += [(values[i] + values[i+1]) / 2 for i in range(0, len(values)-1, 17)]
    for x in samples:
        pos = bisect_left(values, x)
        candidates = values[max(0, pos-1):pos+1]
        nearest = min(candidates, key=lambda z: abs(z-x))
        if len(candidates) == 2 and abs(candidates[0]-x) == abs(candidates[1]-x):
            spacing = candidates[1]-candidates[0]
            nearest = next(z for z in candidates if (z/spacing).denominator == 1
                           and (z/spacing).numerator % 2 == 0)
        assert rounder(x, p) == nearest
        assert rounder(-x, p) == -nearest
        assert abs((nearest-x)/x) <= F(1, 2) * F(10)**(1-p)
        round_cases += 2
raises(ValueError, rounder, F(1), 0)
report['checks']['rounding'] = {'grid_oracles': round_cases, 'precisions': [1, 2, 3]}

e = envs[2]
multiply_cases = 0
for base in (2, 3, 10, 256, 1000, 65536):
    for _ in range(350):
        u, v = rng.randrange(base**rng.randrange(1, 20)), rng.randrange(base**rng.randrange(1, 20))
        ud, vd = e['split'](u, base), e['split'](v, base)
        w = e['multiply'](ud, vd, base)
        assert e['join'](w, base) == u*v
        assert all(0 <= d < base for d in w)
        d = rng.randrange(1, base)
        q, r = e['divide_digit'](ud, d, base)
        assert (e['join'](q, base), r) == divmod(u, d)
        multiply_cases += 1
    for length in (1, 2, 10, 40):
        u = base**length-1
        assert e['join'](e['multiply'](e['split'](u, base), e['split'](u, base), base), base) == u*u
for n in range(385):
    assert e['restore']([n % m for m in (5, 7, 11)], [5, 7, 11]) == n
trial_cases = 0
for base in range(2, 9):
    for v in range((base//2)*base, base*base):
        for u in range(base*v):
            estimate = (u//base) // (v//base)
            actual = u//v
            assert actual <= estimate <= actual+2
            trial_cases += 1
raises(ValueError, e['restore'], [0, 0], [4, 6])
raises(ValueError, e['divide_digit'], [1], 0)
report['checks']['multi_precision'] = {'product_and_division_cases': multiply_cases,
    'crt_full_range': 385, 'normalized_trial_quotient_cases': trial_cases}

e = envs[3]
fraction_cases = 0
for base in range(2, 13):
    for n in range(0, 2000, 7):
        ds = e['write_digits'](n, base)
        assert sum(d*base**i for i,d in enumerate(ds[::-1])) == n
        assert e['read_digits'](ds, base) == n
    for q in range(1, 65):
        for p in range(q):
            pre, cycle = e['fraction_digits'](p, q, base)
            assert e['restore_fraction'](pre, cycle, base) == F(p, q)
            denominator = F(p, q).denominator
            while (g := math.gcd(denominator, base)) > 1:
                denominator //= g
            assert (not cycle) == (denominator == 1)
            if cycle:
                assert pow(base, len(cycle), denominator) == 1
                assert all(pow(base, k, denominator) != 1 for k in range(1, len(cycle)))
            fraction_cases += 1
raises(ValueError, e['read_digits'], [1, 0, 2], 2)
raises(ValueError, e['fraction_digits'], 1, 0, 2)
report['checks']['base_conversion'] = {'rational_round_trips_and_periods': fraction_cases, 'bases': 11}

e = envs[4]
for _ in range(4000):
    a,c = rng.randrange(-10**15,10**15), rng.randrange(-10**15,10**15)
    b,d = rng.randrange(1,10**12), rng.randrange(1,10**12)
    for fn, expected in [('add', F(a,b)+F(c,d)), ('multiply', F(a,b)*F(c,d))]:
        n,q = e[fn]((a,b),(c,d))
        assert q > 0 and math.gcd(n,q) == 1 and F(n,q) == expected
for a in range(-50,51):
    for b in range(-50,51):
        g,x,y = e['extended_gcd'](a,b)
        assert g == math.gcd(a,b) == a*x+b*y
for n in range(1,3001):
    factors = e['factor'](n)
    assert math.prod(factors) == n and factors == sorted(factors)
    assert all(all(p % d for d in range(2, math.isqrt(p)+1)) for p in factors)
assert e['add']((7,15),(-7,15)) == (0,1)
assert e['rational'](0,-9) == (0,1)
raises(ZeroDivisionError, e['rational'], 1, 0)
raises(ValueError, e['factor'], 0)
report['checks']['rational_arithmetic'] = {'fraction_oracles': 8000, 'bezout_pairs': 10201, 'factorizations': 3000}


def convolution(a,b):
    c = [F(0)] * (len(a)+len(b)-1)
    for i,ai in enumerate(a):
        for j,bj in enumerate(b):
            c[i+j] += ai*bj
    return c


def explicit_value(a,x):
    return sum(c*x**i for i,c in enumerate(a))


e = envs[5]
for _ in range(600):
    a = e['poly']([F(rng.randrange(-9,10),rng.randrange(1,8)) for _ in range(rng.randrange(1,10))])
    b = e['poly']([F(rng.randrange(-9,10),rng.randrange(1,8)) for _ in range(rng.randrange(1,7))])
    if b == [0]:
        b = [F(1)]
    q,r = e['divide'](a,b)
    rebuilt = convolution(b,q)
    rebuilt += [F(0)] * max(0,len(r)-len(rebuilt))
    for i,c in enumerate(r):
        rebuilt[i] += c
    assert e['poly'](rebuilt) == a
    assert r == [0] or len(r)<len(b)
    g = e['poly_gcd'](a,b)
    assert g[-1] == 1
    assert e['divide'](a,g)[1] == [0] and e['divide'](b,g)[1] == [0]
    x = F(rng.randrange(-7,8),rng.randrange(1,5))
    value, derivative = e['value_and_derivative'](a,x)
    assert value == explicit_value(a,x)
    assert derivative == sum(i*a[i]*x**(i-1) for i in range(1,len(a)))
for n in range(1,300):
    value,count = e['power'](3,n)
    assert value == pow(3,n)
    assert count == n.bit_length()+n.bit_count()-2
assert e['poly_gcd']([0],[0]) == [0]
raises(ZeroDivisionError, e['divide'], [1], [0])
report['checks']['polynomial_arithmetic'] = {'division_gcd_value_cases': 600, 'power_cases': 299}

e = envs[6]
series_cases = 0
for n in range(1,25):
    for _ in range(10):
        a = [F(rng.randrange(-4,5),rng.randrange(1,5)) for _ in range(n)]
        if not a[0]:
            a[0] = F(2,3)
        g = e['inverse'](a,n)
        assert convolution(a,g)[:n] == [1]+[0]*(n-1)
        # Sequential recurrence is independent of the Newton iteration.
        oracle = [1/a[0]]
        for k in range(1,n):
            oracle.append(-sum(a[j]*oracle[k-j] for j in range(1,k+1))/a[0])
        assert g == oracle
        f = list(a)
        f[0] = F(0)
        exp = e['exponential'](f,n)
        # Definition exp(f) = sum f**k/k!, truncated; f[0]=0.
        term, expected = [F(1)]+[F(0)]*(n-1), [F(1)]+[F(0)]*(n-1)
        for k in range(1,n):
            term = convolution(term,f)[:n]
            expected = [v+t/math.factorial(k) for v,t in zip(expected,term)]
        assert exp == expected
        series_cases += 1
    r = e['inverse_of_x_minus_x2'](n)
    assert r == [F(0)]+[F(math.comb(2*k-2,k-1),k) for k in range(1,n)]
raises(ZeroDivisionError, e['inverse'], [0,1], 4)
raises(ValueError, e['exponential'], [1], 3)
report['checks']['formal_series'] = {'newton_and_exp_oracles': series_cases, 'catalan_prefixes': 24}

report['all_passed'] = True

report['all_passed'] = True
(ROOT / 'verification/taocp-chapter4-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 4: passed')
