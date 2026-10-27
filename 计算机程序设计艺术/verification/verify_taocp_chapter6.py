"""Execute authored examples and check search semantics against independent models."""
from pathlib import Path
from itertools import permutations, product, combinations, combinations_with_replacement
from fractions import Fraction as F
from functools import lru_cache
from bisect import bisect_left
import contextlib
import hashlib
import io
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "6.1-顺序查找.md", "6.2-通过键码比较进行查找.md", "6.3-数字查找.md",
    "6.4-散列.md", "6.5-利用辅助键码的查找.md",
]
PAGES = ["369-380", "380-458", "458-478", "478-520", "521-543"]
SUMMARIES = [
    "从成功与失败查找的比较次数出发，推导按访问概率排序、自组织表的稳态成本和变长记录的概率长度比规则。用可运行程序核对哨兵、移到表头及不同成本模型。",
    "串联二分边界、二叉查找树、最优树动态规划、AVL旋转与B树页面高度界，区分平均概率模型和最坏结构保证。提供可运行的二分查找与AVL插入代码。",
    "解释Trie的前缀共享、终止标记、键长成本和空间取舍，区分数字查找树与Patricia的候选确认。实现支持空键、None值、前缀枚举及安全删除的字符Trie。",
    "从散列函数与冲突处理出发，解释线性探测的聚集、双重散列的覆盖条件和删除标记。实现固定容量散列表，验证满表、回绕、更新、删除及重建边界。",
    "把多条件查询写成集合运算，连接倒排表、位图、组合索引与多维检索。推导叠加编码和Bloom过滤器的候选筛选逻辑，用程序验证误报后的精确确认。",
]
EXPECTED = [
    "(-1, 3) (-1, 4)\n5/3 7/3\n['B', 'A', 'C'] 35/6 14/3\n(2, True) [7, 4, 9]",
    "[10, 20, 30, 40, 50, 60] 3\nTrue False\n1 3",
    "[('car', None), ('cart', 4), ('cat', 3)]\nFalse True 0\n[('cart', 4)]",
    "3 five TEN fifteen\nNone 0\nfull\n5 TEN 0",
    "[0, 3]\n[0, 3]\n[0]\n([0, 1], [0])",
]
report = {"articles": [], "checks": {}, "random_seed": 61025}
envs = []
for filename, expected in zip(FILES, EXPECTED):
    source = (ROOT / '第3卷-排序与查找/第06章-查找' / filename).read_text(encoding="utf-8")
    first, body = source.split("\n", 1)
    title = first.removeprefix("# ")
    body = body.lstrip("\n").rstrip() + "\n"
    assert 5 <= len(title) <= 100
    assert source.count("```") % 2 == 0 and source.count("$$") % 2 == 0
    assert not any(x in source for x in ("TODO", "待补"))
    blocks = re.findall(r"```python\n(.*?)\n```", source, re.S)
    outputs = re.findall(r"```text\n(.*?)\n```", source, re.S)
    assert len(blocks) == len(outputs) == 1 and outputs[0] == expected
    scope, stdout = {}, io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exec(compile(blocks[0], filename + ":python", "exec"), scope)
    assert stdout.getvalue().strip() == expected, (filename, stdout.getvalue())
    envs.append(scope)
    report["articles"].append({
        "filename": filename, "title": title, "body_characters": len(body),
        "python_blocks": len(blocks), "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "example_output": expected,
    })


def raises(kind, function, *args):
    try:
        function(*args)
    except kind:
        return
    raise AssertionError((function, args, kind))


# 6.1: first-match semantics, expected-cost optimality, exact stationary MTF model.
e = envs[0]
linear_cases = 0
for n in range(7):
    for values in product(range(3), repeat=n):
        a = list(values)
        for key in range(-1, 4):
            found = next((i for i, x in enumerate(a) if x == key), -1)
            ordinary = len(a) if found < 0 else found + 1
            sentinel = len(a) + 1 if found < 0 else found + 1
            assert e["linear_find"](a, key) == (found, ordinary)
            assert e["sentinel_find"](a, key) == (found, sentinel)
            changed = a.copy()
            assert e["move_to_front"](changed, key) == (ordinary, found >= 0)
            expected = a if found < 0 else [a[found]] + a[:found] + a[found+1:]
            assert changed == expected
            assert a == list(values)
            linear_cases += 1
ordering_cases = 0
for weights, lengths in [
    ([3, 2, 1], [5, 1, 2]), ([1, 1, 1, 1], [1, 4, 2, 3]),
    ([9, 1, 2, 7, 3], [4, 8, 1, 2, 6]), ([1], [12]),
    ([0, 3, 1, 2], [1, 2, 3, 4]),
]:
    p = {i: F(w, sum(weights)) for i, w in enumerate(weights)}
    length = dict(enumerate(lengths))
    arrangements = list(permutations(p))
    optimal = sorted(p, key=p.get, reverse=True)
    ratio = sorted(p, key=lambda k: p[k] / length[k], reverse=True)
    assert e["expected_cost"](optimal, p) == min(e["expected_cost"](x, p) for x in arrangements)
    assert e["expected_cost"](ratio, p, length) == min(
        e["expected_cost"](x, p, length) for x in arrangements)
    ordering_cases += len(arrangements)
stationary_cases = 0
for weights in ([1], [3, 1], [3, 2, 1], [2, 2, 1, 1], [9, 1, 2, 7, 3]):
    p = tuple(F(w, sum(weights)) for w in weights)
    distribution = {}
    for order in permutations(range(len(p))):
        remaining, probability = F(1), F(1)
        for i in order:
            probability *= p[i] / remaining
            remaining -= p[i]
        distribution[order] = probability
    assert sum(distribution.values()) == 1
    incoming = {order: F(0) for order in distribution}
    cost = F(0)
    for order, probability in distribution.items():
        for i, request_probability in enumerate(p):
            after = (i,) + tuple(j for j in order if j != i)
            incoming[after] += probability * request_probability
            cost += probability * request_probability * (order.index(i) + 1)
    assert incoming == distribution
    formula = 1 + 2 * sum((p[i]*p[j]/(p[i]+p[j])
                          for i in range(len(p)) for j in range(i+1, len(p))), F(0))
    opt = sum((i+1)*v for i, v in enumerate(sorted(p, reverse=True)))
    assert cost == formula and cost <= 2*opt - 1
    stationary_cases += len(distribution)
report["checks"]["6.1"] = {
    "first_match_cases": linear_cases, "orderings_compared": ordering_cases,
    "exact_stationary_states": stationary_cases,
    "stationary_balance_and_mtf_formula": True,
    "variable_length_exchange_rule": True,
}


# 6.2: every small insertion order, bisect oracle, exhaustive shapes for optimal BST.
e = envs[1]


def check_avl(v, low=-math.inf, high=math.inf):
    if v is None:
        return 0, []
    assert low < v.key < high
    lh, left = check_avl(v.left, low, v.key)
    rh, right = check_avl(v.right, v.key, high)
    assert abs(lh-rh) <= 1
    assert v.height == 1 + max(lh, rh)
    return v.height, left + [v.key] + right


avl_orders = avl_insertions = 0
for n in range(8):
    for order in permutations(range(n)):
        root, model = None, set()
        for key in order:
            root = e["insert"](root, key)
            model.add(key)
            assert check_avl(root)[1] == sorted(model)
            root = e["insert"](root, key)
            assert check_avl(root)[1] == sorted(model)
            avl_insertions += 2
        assert list(e["inorder"](root)) == sorted(model)
        assert all(e["contains"](root, k) == (k in model) for k in range(-1, n+1))
        avl_orders += 1
rng = random.Random(report["random_seed"])
long_orders = [list(range(2000)), list(range(2000))[::-1]]
shuffled = list(range(2000))
rng.shuffle(shuffled)
long_orders.append(shuffled)
for order in long_orders:
    root = None
    for i, key in enumerate(order):
        root = e["insert"](root, key)
        if i % 100 == 0:
            check_avl(root)
    assert check_avl(root)[1] == list(range(2000))
binary_cases = 0
for n in range(11):
    for a in combinations_with_replacement(range(4), n):
        for key in range(-1, 6):
            i = e["lower_bound"](a, key)
            assert i == bisect_left(a, key)
            assert all(x < key for x in a[:i]) and all(x >= key for x in a[i:])
            binary_cases += 1


@lru_cache(None)
def shapes(lo, hi):
    if lo == hi:
        return (None,)
    return tuple((k, l, r) for k in range(lo, hi)
                 for l in shapes(lo, k) for r in shapes(k+1, hi))


def weighted_cost(tree, p, q, lo, depth=0):
    if tree is None:
        return q[lo] * depth
    k, left, right = tree
    return (p[k] * (depth + 1)
            + weighted_cost(left, p, q, lo, depth+1)
            + weighted_cost(right, p, q, k+1, depth+1))


optimal_cases = 0
for n in range(7):
    for trial in range(12):
        p = [rng.randrange(5) for _ in range(n)]
        q = [rng.randrange(5) for _ in range(n+1)]
        c = [[0]*(n+1) for _ in range(n+1)]
        for width in range(1, n+1):
            for i in range(n-width+1):
                j = i + width
                w = sum(p[i:j]) + sum(q[i:j+1])
                c[i][j] = w + min(c[i][k] + c[k+1][j] for k in range(i, j))
        assert c[0][n] == min(weighted_cost(t, p, q, 0) for t in shapes(0, n))
        optimal_cases += 1
random_bst_orders = 0
for n in range(1, 7):
    successful, unsuccessful = 0, 0
    for order in permutations(range(n)):
        root = None
        for key in order:
            if root is None:
                root = [key, None, None]
                continue
            node = root
            while True:
                side = 1 if key < node[0] else 2
                if node[side] is None:
                    node[side] = [key, None, None]
                    break
                node = node[side]

        def depths(node, depth=0):
            if node is None:
                return 0, depth
            ls, lu = depths(node[1], depth+1)
            rs, ru = depths(node[2], depth+1)
            return depth+1+ls+rs, lu+ru

        sc, uc = depths(root)
        successful += sc
        unsuccessful += uc
        random_bst_orders += 1
    hn = sum((F(1, i) for i in range(1, n+1)), F(0))
    assert F(successful, math.factorial(n)*n) == 2*(1+F(1, n))*hn-3
    assert F(unsuccessful, math.factorial(n)*(n+1)) == 2*(hn+F(1, n+1))-2
report["checks"]["6.2"] = {
    "avl_insertion_orders": avl_orders, "avl_small_insertions_including_duplicates": avl_insertions,
    "long_avl_orders": 3, "long_order_length": 2000, "lower_bound_cases": binary_cases,
    "optimal_bst_weights_vs_all_shapes": optimal_cases, "random_bst_orders": random_bst_orders,
}


# 6.3: map semantics and prefix results checked against direct scanning.
e = envs[2]
trie, model = e["Trie"](), {}
keys = ["", "a", "ab", "abc", "b", "ba", "算法", "算术", "算", "é", "e\u0301", "x"*1500]
prefixes = ["", "a", "ab", "b", "算", "算法", "x"*1499, "missing"]
trie_operations = prefix_cases = 0
for step in range(5000):
    key = rng.choice(keys)
    operation = rng.randrange(3)
    if operation == 0:
        value = None if step % 5 == 0 else step
        trie.put(key, value)
        model[key] = value
    elif operation == 1:
        if key in model:
            trie.remove(key)
            del model[key]
        else:
            raises(KeyError, trie.remove, key)
    else:
        if key in model:
            assert trie.get(key) == model[key]
        else:
            raises(KeyError, trie.get, key)
    assert (key in trie) == (key in model)
    for prefix in prefixes:
        expected = sorted((k, v) for k, v in model.items() if k.startswith(prefix))
        assert list(trie.with_prefix(prefix)) == expected
        prefix_cases += 1
    trie_operations += 1
for key in list(model):
    trie.remove(key)
assert not trie.root.children and not trie.root.terminal
report["checks"]["6.3"] = {
    "mixed_operations": trie_operations, "prefix_scan_comparisons": prefix_cases,
    "empty_key_none_unicode_long_prefix_and_pruning": True,
}


# 6.4: exhaustive short collisions and random operations against a capacity-aware dict.
e = envs[3]


def check_map(table, model):
    live = [entry for entry in table.slots
            if entry is not e["EMPTY"] and entry is not e["DELETED"]]
    assert len(live) == len(dict(live)) == len(table) == len(model)
    assert dict(live) == model
    assert table.deleted == sum(entry is e["DELETED"] for entry in table.slots)
    for key in range(-3, 16):
        if key in model:
            assert table[key] == model[key]
        else:
            raises(KeyError, table.__getitem__, key)


def map_step(table, model, op, key, value):
    if op == "put":
        if key not in model and len(model) == len(table.slots):
            raises(OverflowError, table.__setitem__, key, value)
        else:
            table[key] = value
            model[key] = value
    elif key in model:
        del table[key]
        del model[key]
    else:
        raises(KeyError, table.__delitem__, key)
    check_map(table, model)


trace_count = 0
actions = list(product(("put", "del"), (0, 3, 6)))
for trace in product(actions, repeat=5):
    table, model = e["LinearMap"](3), {}
    for step, (op, key) in enumerate(trace):
        map_step(table, model, op, key, None if step % 2 else step)
    trace_count += 1
random_operations = 0
for capacity in (1, 2, 5, 7, 11):
    table, model = e["LinearMap"](capacity), {}
    for step in range(4000):
        map_step(table, model, rng.choice(("put", "put", "del")),
                 rng.randrange(-3, 16), None if step % 7 == 0 else step)
        if step % 101 == 0:
            table = table.rebuild(capacity)
            check_map(table, model)
            assert table.deleted == 0
        random_operations += 1
table = e["LinearMap"](3)
for key in (2, 5, 8):
    table[key] = key
for key in (2, 5, 8):
    del table[key]
assert table.deleted == 3
raises(KeyError, table.__getitem__, 11)
table[11] = None
assert table[11] is None and table.deleted == 2
for bad in (0, -1, True, 1.5):
    raises(ValueError, e["LinearMap"], bad)
raises(TypeError, table.__setitem__, "x", 1)
probe_cases = 0
for m in range(1, 31):
    for stride in range(m):
        visited = {(j*stride) % m for j in range(m)}
        assert len(visited) == m // math.gcd(m, stride)
        probe_cases += 1
for alpha, success, failure in [
    (F(1, 2), F(3, 2), F(5, 2)),
    (F(4, 5), F(3), F(13)),
    (F(9, 10), F(11, 2), F(101, 2)),
]:
    assert (1+1/(1-alpha))/2 == success
    assert (1+1/(1-alpha)**2)/2 == failure
report["checks"]["6.4"] = {
    "exhaustive_five_operation_collision_traces": trace_count,
    "random_operations": random_operations, "double_hash_period_cases": probe_cases,
    "full_table_all_tombstones_wraparound_update_rebuild": True,
    "linear_probe_table_arithmetic": True,
}


# 6.5: exact scan oracle, explicit finite universe, signatures cannot drop true answers.
e = envs[4]
terms = [("area", "east"), ("area", "west"), ("lang", "Python"),
         ("lang", "Rust"), ("year", 2024), ("year", 2099), ("absent", None)]
condition_sets = [()] + [(t,) for t in terms] + list(combinations(terms, 2))
query_cases = 0


def matches(record, term):
    field, value = term
    return field in record and record[field] == value


datasets = [{}, e["records"], {k:v for k,v in e["records"].items() if k != 3},
            {0: {"x": None}, 12: {}, 29: {"area": "east"}}]
for _ in range(8):
    data = {}
    for rid in range(9):
        fields = {"area": rng.choice(("east", "west")), "lang": rng.choice(("Python", "Rust")),
                  "year": rng.choice((2023, 2024, 2025))}
        if rng.random() < .25:
            del fields["lang"]
        if rng.random() < .8:
            data[rid] = fields
    datasets.append(data)
for records in datasets:
    postings, bitmaps, active = e["build_indexes"](records)
    assert set(e["bit_ids"](active)) == set(records)
    for positive in condition_sets:
        expected_positive = {rid for rid,r in records.items()
                             if all(matches(r,t) for t in positive)}
        assert e["intersect"](postings, positive, records) == expected_positive
        for negative in condition_sets:
            expected = {rid for rid in expected_positive
                        if all(not matches(records[rid],t) for t in negative)}
            bits = e["bitmap_query"](bitmaps, positive, negative, active)
            assert set(e["bit_ids"](bits)) == expected
            query_cases += 1
raises(ValueError, list, e["bit_ids"](-1))
attributes = ("A", "B", "C")
subsets = [set(c) for n in range(4) for c in combinations(attributes, n)]
documents = dict(enumerate(subsets))
signature_cases = 0
for bitcodes in product(range(8), repeat=3):
    codes = dict(zip(attributes, bitcodes))
    for required in subsets:
        candidates, confirmed = e["filter_then_confirm"](documents, required, codes)
        expected = sorted(rid for rid, a in documents.items() if required <= a)
        assert set(expected) <= set(candidates)
        assert confirmed == expected
        signature_cases += 1
bloom_approximation = (1-math.exp(-7/10))**7
assert .0081 < bloom_approximation < .0083
report["checks"]["6.5"] = {
    "boolean_queries_vs_scan": query_cases, "signature_code_query_combinations": signature_cases,
    "empty_universe_missing_fields_sparse_ids_none_deleted_record": True,
    "no_false_negatives_for_positive_signatures": True,
    "bloom_approximation_10_bits_per_key_k7": bloom_approximation,
}


report['all_passed'] = True
(ROOT / 'verification/taocp-chapter6-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 6: passed')
