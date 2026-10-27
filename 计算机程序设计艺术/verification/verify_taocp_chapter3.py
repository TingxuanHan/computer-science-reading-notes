"""Execute the six original posts and check their mathematical examples."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from itertools import product
import contextlib
import hashlib
import io
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ["3.1-引言.md", "3.2-生成一致随机数.md", "3.3-统计检验.md",
         "3.4-其它类型的随机量.md", "3.5-什么是随机序列.md", "3.6-小结.md"]
PAGES = ["1-8", "8-35", "35-104", "104-131", "131-163", "163-174"]
SUMMARIES = [
    "从随机数的应用、分布与独立性出发，解释确定性程序为何仍能用于模拟，以及有限状态为何必然进入循环。用平方取中法的短循环和精确平衡的比特串说明周期、频数与随机性不能混同。",
    "推导线性同余递推，解释满周期条件、二进制低位的短周期和效能；用仿射变换复合实现快速跳步，避免错误使用模逆元，再梳理延迟递推、移位异或、逆同余和组合方法。",
    "从卡方与KS统计量出发，说明频数检验、相邻组合和理论检验各自能说明什么。用精确算术展示一维完全平衡却存在强依赖的序列，并解释谱检验所研究的格与平行平面结构。",
    "解释有限整数映射的取模偏差、拒绝采样、累计概率和逆分布函数，推导指数与正态转换，再证明Fisher-Yates洗牌和水库抽样的公平性，配可注入选择路径的Python实现。",
    "沿原书讨论等分布、多维块频率、子序列选择、可计算性和有限序列描述长度。用八位循环展示短模式全部平衡仍可完全预测，区分无限序列性质、有限检验与计算资源受限的不可区分性。",
    "把生成器、输出映射、分布转换与应用调用连成完整流程，解释模乘溢出、检查点重放、并行流分配和应用验证。以原书素数模参数写出可核对的教学实现，收束第三章。",
]
EXPECTED = [
    "[6100, 2100, 4100, 8100] 0 4\n([1000, 0], 1, 1)",
    "True 16\n[0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]\n5",
    "0\n[0, 200, 0, 0] 600\n('1/8', '1/8')",
    "5\n['B', 'A', 'C']\n['C', 'E']\n0.346574",
    "1 2 4 4\n2 4 2 2\n3 8 1 1\n4 8 0 1\nperiod-8 predictor: 64 / 64",
    "[48271, 182605794, 1291394886]\nTrue\n8",
]
SOURCE = "sources/taocp/计算机程序设计艺术（第2卷）半数值算法.pdf"
report = {"source": SOURCE, "edition": "Volume 2, third edition, Chinese, 2002",
          "articles": [], "checks": {}}
envs = []
for name, expected in zip(FILES, EXPECTED):
    source = (ROOT / '第2卷-半数值算法/第03章-随机数' / name).read_text(encoding="utf-8")
    heading, body = source.split("\n", 1)
    body = body.lstrip("\n").rstrip() + "\n"
    assert len(heading.removeprefix("# ")) <= 100
    assert source.count("```") % 2 == 0 and source.count("$$") % 2 == 0
    assert not any(term in source for term in ("TODO", "待补", "—", "–"))
    code_blocks = re.findall(r"```python\n(.*?)\n```", source, re.S)
    env, output = {}, io.StringIO()
    with contextlib.redirect_stdout(output):
        for index, code in enumerate(code_blocks, 1):
            exec(compile(code, f"{name}:python-{index}", "exec"), env)
    assert output.getvalue().strip() == expected, (name, output.getvalue())
    envs.append(env)
    report["articles"].append({
        "filename": name, "title": heading.removeprefix("# "),
        "body_characters": len(body), "python_blocks": len(code_blocks),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "example_output": expected,
    })


def raises(kind, func, *args):
    try:
        func(*args)
    except kind:
        return
    raise AssertionError((func.__name__, args, kind))


# Validate middle-square arithmetic independently of digit slicing.
middle, orbit = envs[0]["middle_square4"], envs[0]["orbit"]
for seed in range(10000):
    assert middle(seed) == (seed * seed // 100) % 10000
    states, mu, period = orbit(seed, middle, 10000)
    assert len(states) == len(set(states)) == mu + period
    assert middle(states[-1]) == states[mu]
    assert all(middle(a) == b for a, b in zip(states, states[1:]))
for seed in range(0, 10000, 97):
    slow, fast = middle(seed), middle(middle(seed))
    while slow != fast:
        slow, fast = middle(slow), middle(middle(fast))
    mu, slow = 0, seed
    while slow != fast:
        slow, fast = middle(slow), middle(fast)
        mu += 1
    period, fast = 1, middle(slow)
    while slow != fast:
        fast = middle(fast)
        period += 1
    assert orbit(seed, middle, 10000)[1:] == (mu, period)
raises(ValueError, middle, -1)
raises(ValueError, middle, 10000)
raises(ValueError, orbit, 0, middle, 0)
raises(ValueError, orbit, 6100, middle, 3)
report["checks"]["middle_square"] = {"all_states": 10000, "floyd_oracles": 104}

# Exhaustive small-modulus comparison against direct state traversal.
full, jump = envs[1]["full_period"], envs[1]["jump"]
lcg_cases = 0
for m in range(2, 19):
    for a in range(m):
        for c in range(m):
            condition = full(a, c, m)
            for seed in range(m):
                seen, x = set(), seed
                while x not in seen:
                    seen.add(x)
                    x = (a * x + c) % m
                assert (len(seen) == m and x == seed) == condition
                lcg_cases += 1
rng = random.Random(20261023)
for _ in range(5000):
    m = rng.randrange(2, 1000)
    a, c, seed = (rng.randrange(m) for _ in range(3))
    k = rng.randrange(250)
    x = seed
    for _ in range(k):
        x = (a * x + c) % m
    assert jump(seed, a, c, m, k) == x
    left, right = rng.randrange(10**20), rng.randrange(10**20)
    assert jump(seed, a, c, m, left + right) == jump(
        jump(seed, a, c, m, left), a, c, m, right)
for args in [(0, 1, 1, 1, 2), (0, 1, 1, 16, -1)]:
    raises(ValueError, jump, *args)
report["checks"]["lcg"] = {"exhaustive_parameter_seed_cases": lcg_cases,
    "iterative_jump_oracles": 5000, "large_step_composition_cases": 5000}

# Exact rational statistics; KS oracle evaluates both sides of each jump.
chi, ks = envs[2]["chi_uniform"], envs[2]["ks_uniform"]
for _ in range(1000):
    k = rng.randrange(2, 15)
    counts = [rng.randrange(1, 30) for _ in range(k)]
    total = sum(counts)
    assert chi(counts) == Fraction(k * sum(x*x for x in counts), total) - total
    xs = [Fraction(rng.randrange(100), 100) for _ in range(rng.randrange(1, 20))]
    points = sorted(set(xs))
    plus = max(Fraction(sum(x <= p for x in xs), len(xs)) - p for p in points)
    minus = max(p - Fraction(sum(x < p for x in xs), len(xs)) for p in points)
    assert ks(xs) == (plus, minus)
for counts in ([], [0, 0], [-1, 1], [0.5, 1.5]):
    raises(ValueError, chi, counts)
for xs in ([], [Fraction(-1, 2)], [1]):
    raises(ValueError, ks, xs)
report["checks"]["statistics"] = {"chi_exact_oracles": 1000, "ks_jump_oracles": 1000,
    "pathological_pair_chi_square": 600, "p_values_claimed": False}

# Rejection mapping: every accepted residue has the same number of preimages.
reject = envs[3]["randbelow_reject"]
shuffle, reservoir = envs[3]["shuffle"], envs[3]["reservoir"]
mapping_cases = 0
for source_size in range(1, 65):
    for n in range(1, source_size + 1):
        limit = source_size - source_size % n
        counts = Counter(reject(n, lambda r=r: r, source_size) for r in range(limit))
        assert set(counts) == set(range(n))
        assert set(counts.values()) == {limit // n}
        if limit < source_size:
            seq = iter(list(range(limit, source_size)) + [limit - 1])
            assert reject(n, lambda: next(seq), source_size) == n - 1
        mapping_cases += 1
shuffle_paths = 0
for n in range(8):
    counts = Counter()
    for path in product(*(range(i) for i in range(n, 1, -1))):
        choices = iter(path)
        result = shuffle(range(n), lambda bound: next(choices))
        counts[tuple(result)] += 1
        shuffle_paths += 1
    assert len(counts) == math.factorial(n)
    assert set(counts.values()) == {1}
reservoir_paths = 0
for n in range(8):
    for k in range(n + 1):
        counts = Counter()
        paths = product(*(range(t) for t in range(k + 1, n + 1))) if k else [()]
        for path in paths:
            choices = iter(path)
            result = reservoir(range(n), k, lambda bound: next(choices))
            assert len(result) == len(set(result)) == k
            counts[tuple(sorted(result))] += 1
            reservoir_paths += 1
        assert len(counts) == math.comb(n, k)
        assert len(set(counts.values())) == 1
exp_from_u = envs[3]["exponential_from_u"]
for u in [0, 1e-15, 1e-8, 0.1, 0.5, 0.9, math.nextafter(1, 0)]:
    for rate in [0.1, 1, 2, 100000]:
        x = exp_from_u(u, rate)
        assert math.isclose(-math.expm1(-rate * x), u, abs_tol=1e-15)
raises(ValueError, reject, 0, lambda: 0, 16)
raises(ValueError, reject, 17, lambda: 0, 16)
raises(ValueError, reject, 2, lambda: 16, 16)
raises(ValueError, shuffle, "AB", lambda n: n)
raises(ValueError, reservoir, "AB", 3, lambda n: 0)
raises(ValueError, reservoir, "AB", -1, lambda n: 0)
raises(ValueError, reservoir, "ABCD", 2, lambda n: n)
for u, rate in [(1, 1), (-0.1, 1), (0.5, 0), (math.nan, 1), (0.5, math.inf)]:
    raises(ValueError, exp_from_u, u, rate)
report["checks"]["transformations"] = {
    "exact_rejection_mappings": mapping_cases, "shuffle_paths": shuffle_paths,
    "shuffle_max_n": 7, "reservoir_paths": reservoir_paths, "reservoir_max_n": 7,
    "exponential_cdf_round_trips": 28}

# Rotating or complementing the cycle preserves the short-window example.
cyclic = envs[4]["cyclic_counts"]
word = "00010111"
for shift in range(8):
    rotated = word[shift:] + word[:shift]
    for w in [rotated, rotated.translate(str.maketrans("01", "10"))]:
        for k in range(1, 4):
            counts = cyclic(w, k)
            assert len(counts) == 2**k
            assert set(counts.values()) == {8 // 2**k}
        assert len(cyclic(w, 4)) == 8
assert all(word[i % 8] == "0" for i in range(0, 80, 8))
raises(ValueError, cyclic, "", 1)
raises(ValueError, cyclic, "012", 1)
raises(ValueError, cyclic, "01", 0)
report["checks"]["finite_sequence"] = {"rotations_and_complements": 16,
    "all_three_bit_words": 8, "four_bit_words_present": 8, "period": 8}

# Schrage-style arithmetic against Python's exact multiplication.
Replay = envs[5]["ReplayLCG"]
g, x = Replay(1), 1
for _ in range(100000):
    x = Replay.A * x % Replay.M
    assert g.next_int() == x
seeds = [1, Replay.M - 1, Replay.Q - 1, Replay.Q, Replay.Q + 1]
seeds += [rng.randrange(1, Replay.M) for _ in range(10000)]
for seed in seeds:
    assert Replay(seed).next_int() == Replay.A * seed % Replay.M
for steps in [0, 1, 2, 99, 1000]:
    g = Replay(123456)
    for _ in range(steps):
        g.next_int()
    saved = g.checkpoint()
    suffix = [g.next_int() for _ in range(100)]
    restored = Replay.restore(saved)
    assert suffix == [restored.next_int() for _ in range(100)]
    assert g.checkpoint() == restored.checkpoint()
    assert saved["draws"] == steps
for seed in [0, -1, Replay.M, 1.5, True, None]:
    raises(ValueError, Replay, seed)
for data in [{"algorithm": "wrong", "state": 1, "draws": 0},
             {"algorithm": Replay.NAME, "state": 0, "draws": 0},
             {"algorithm": Replay.NAME, "state": 1, "draws": -1}]:
    raises(ValueError, Replay.restore, data)
g = Replay(1)
assert all(0 < g.uniform() < 1 for _ in range(1000))
assert g.draws == 1000
report["checks"]["replay"] = {"consecutive_modular_oracles": 100000,
    "single_step_seed_oracles": len(seeds), "checkpoint_round_trips": 5}

report["all_passed"] = True

report['all_passed'] = True
(ROOT / 'verification/taocp-chapter3-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 3: passed')
