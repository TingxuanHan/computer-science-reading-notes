from pathlib import Path
from collections import deque
from functools import lru_cache
import contextlib
import copy
import hashlib
import io
import itertools
import json
import math
import random
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ["2.1-引论.md", "2.2-线性表.md", "2.3-树.md",
         "2.4-多重链接结构.md", "2.5-动态存储分配.md", "2.6-历史和文献.md"]
SUMMARIES = [
    "从节点、字段、链接和入口建立信息结构的基本语言，用待办事项表说明地址与内容、空链接、赋值顺序和不变式，并用 Python 检查头部插入、悬空链接和意外循环。",
    "把栈、队列、顺序分配、链接分配、循环表、双向链表与数组串起来，说明操作代价依赖已知条件；提供循环队列和稀疏多项式合并示例，检查满空状态与更新规则。",
    "从二叉树定义出发，串联三种遍历、穿线、左孩子右兄弟表示、Catalan 数与内外通路长度，再解释共享列表、引用计数和可达性回收，明确树与一般引用图的区别。",
    "沿原书的层次数据与限定名称解析应用，解释父子、兄弟、同名链如何叠加；用 Python 演示候选枚举、祖先限定与歧义检查，讨论多条访问路径的一致性维护。",
    "从空闲总量足够却无法分配的例子出发，解释首先适合、最好适合、分割与合并、边界标记和伙伴系统，用区间分配器演示碎片，并说明百分之五十规则的模型前提。",
    "依原书回顾顺序表、链接、列表处理语言、树与内存管理的发展背景，区分概念、术语和实现的历史证据，整理文献检索入口，并用六个问题复盘第二章。",
]
PAGES = ["222-226", "227-292", "293-398", "399-408", "409-428", "429-435"]
EXPECTED_OUTPUTS = [
    "['写摘要', '校对公式', '检查代码']\n['确定范围', '写摘要', '校对公式', '检查代码']",
    "A\n['B', 'C', 'D']\n['B', 'C', 'D']\n[(2, 7), (1, 2)]",
    "A B D C E\nB D A E C\nD B E C A\n(5, 6, 16)\n[3, 4, 5]",
    "True\nTrue\n2\n[]",
    "[(0, 8), (16, 16)]\ntotal free = 24, largest block = 16\n16 [(0, 8), (28, 4)]\n[(0, 32)]",
    "",
]
report = {"source": "User supplied TAOCP Volume 1 third edition Chinese PDF (2002)",
          "articles": [], "checks": {}}
envs = []
for filename, expected in zip(FILES, EXPECTED_OUTPUTS):
    source = (ROOT / '第1卷-基本算法/第02章-信息结构' / filename).read_text(encoding="utf-8")
    title, body = source.split("\n", 1)
    body = body.lstrip("\n").rstrip() + "\n"
    assert source.count("```") % 2 == 0 and source.count("$$") % 2 == 0
    assert "TODO" not in source and "待补" not in source
    blocks = re.findall(r"```python\n(.*?)\n```", source, re.S)
    env = {}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        for i, code in enumerate(blocks):
            exec(compile(code, f"{filename}:block-{i + 1}", "exec"), env)
    assert output.getvalue().strip() == expected, (filename, output.getvalue())
    envs.append(env)
    report["articles"].append({"filename": filename, "title": title.removeprefix("# "),
        "body_characters": len(body), "python_blocks": len(blocks),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "example_output": output.getvalue().strip()})


def raises(error, fn, *args):
    try:
        fn(*args)
    except error:
        return
    raise AssertionError((error, args))


# Linked sequences: compare with a plain value sequence; reject corrupt links.
prepend, walk = envs[0]["prepend"], envs[0]["walk"]
rng = random.Random(20261023)
nodes, head, expected = {}, None, []
ids = list(range(100))
rng.shuffle(ids)
for i in ids:
    head = prepend(nodes, head, i, i * i)
    expected.insert(0, i * i)
    assert walk(nodes, head) == expected
before = copy.deepcopy(nodes)
raises(ValueError, prepend, nodes, head, ids[0], "duplicate")
raises(ValueError, prepend, nodes, 10000, 10001, "bad head")
assert nodes == before
raises(ValueError, walk, {0: {"value": 1, "next": 0}}, 0)
raises(ValueError, walk, {0: {"value": 1, "next": 4}}, 0)
assert walk({}, None) == []
report["checks"]["linked_sequences"] = {"insertions": 100, "invalid_cases": 4, "empty": True}

# Ring queues: independent deque oracle, including full/empty and None payloads.
RingQueue = envs[1]["RingQueue"]
queue_steps = 0
for capacity in range(1, 5):
    for ops in itertools.product(("put", "get"), repeat=8):
        q, ref = RingQueue(capacity), deque()
        for step, op in enumerate(ops):
            before = (q.data[:], q.head, q.size)
            if op == "put":
                value = None if step % 3 == 0 else step
                if len(ref) == capacity:
                    raises(OverflowError, q.put, value)
                    assert (q.data, q.head, q.size) == before
                else:
                    q.put(value)
                    ref.append(value)
            elif ref:
                assert q.get() == ref.popleft()
            else:
                raises(IndexError, q.get)
                assert (q.data, q.head, q.size) == before
            assert q.values() == list(ref)
            assert 0 <= q.head < capacity and q.size == len(ref)
            queue_steps += 1
for bad in (0, -1, True, 1.5):
    raises(ValueError, RingQueue, bad)
report["checks"]["ring_queue"] = {"operation_steps": queue_steps, "invalid_capacities": 4}

# Sparse polynomial sums: independent coefficient-vector and evaluation oracles.
add_sparse = envs[1]["add_sparse"]
vectors = list(itertools.product((-1, 0, 1), repeat=4))
for a in vectors:
    for b in vectors:
        pa = [(i, a[i]) for i in range(3, -1, -1) if a[i]]
        pb = [(i, b[i]) for i in range(3, -1, -1) if b[i]]
        got = add_sparse(pa, pb)
        want = [(i, a[i] + b[i]) for i in range(3, -1, -1) if a[i] + b[i]]
        assert got == want
        for x in (-2, 0, 3):
            assert sum(c * x**e for e, c in got) == sum((a[i] + b[i]) * x**i for i in range(4))
report["checks"]["sparse_polynomials"] = {"coefficient_pairs": len(vectors)**2, "evaluation_points_each": 3}

# Enumerate every binary tree shape through eight nodes; use recursive traversal oracle.
@lru_cache(None)
def shapes(n):
    if n == 0:
        return (None,)
    return tuple((left, right) for k in range(n)
                 for left in shapes(k) for right in shapes(n - k - 1))


def label(shape, counter):
    if shape is None:
        return None
    value = next(counter)
    return (value, label(shape[0], counter), label(shape[1], counter))


def recursive_orders(tree):
    if tree is None:
        return [], [], []
    v, l, r = tree
    lp, li, lo = recursive_orders(l)
    rp, ri, ro = recursive_orders(r)
    return [v] + lp + rp, li + [v] + ri, lo + ro + [v]


def depths(tree, depth=0):
    if tree is None:
        return [], [depth]
    li, le = depths(tree[1], depth + 1)
    ri, re_ = depths(tree[2], depth + 1)
    return [depth] + li + ri, le + re_


tree_count = 0
for n in range(9):
    assert len(shapes(n)) == math.comb(2*n, n) // (n+1)
    for shape in shapes(n):
        t = label(shape, itertools.count())
        assert envs[2]["traversals"](t) == recursive_orders(t)
        internals, externals = depths(t)
        result = envs[2]["path_lengths"](t)
        assert result == (n, sum(internals), sum(externals))
        assert len(externals) == n + 1 and result[2] == result[1] + 2*n
        tree_count += 1
report["checks"]["binary_trees"] = {"all_shapes_through_8_nodes": tree_count,
    "checked": ["three_orders", "Catalan_count", "external_nodes", "E_equals_I_plus_2n"]}

# Exhaustive directed graphs on three nodes and every root subset; fixed-point oracle.
unreachable = envs[2]["unreachable"]
graph_cases = 0
for edge_bits in range(1 << 9):
    graph = {i: [j for j in range(3) if edge_bits & (1 << (3*i+j))] for i in range(3)}
    for root_bits in range(8):
        roots = [i for i in range(3) if root_bits & (1 << i)]
        reach = set(roots)
        while True:
            expanded = reach | {v for u in reach for v in graph[u]}
            if expanded == reach:
                break
            reach = expanded
        assert unreachable(graph, roots + [None]) == set(graph) - reach
        graph_cases += 1
raises(ValueError, unreachable, {0: [7]}, [0])
raises(ValueError, unreachable, {0: []}, [7])
report["checks"]["reachability"] = {"exhaustive_graph_root_cases": graph_cases, "invalid_reachable_links": 2}

# Qualified names: compare indexed search with a full scan and ancestor subsequences.
DataTable = envs[3]["DataTable"]
table = DataTable()
for i in range(100):
    table.add(rng.choice("ABCD"), None if i == 0 or rng.randrange(5) == 0 else rng.randrange(i))
for parent in range(100):
    want = [i for i, node in enumerate(table.nodes) if node["parent"] == parent]
    got, p = [], table.nodes[parent]["child"]
    while p is not None:
        assert p not in got
        got.append(p)
        p = table.nodes[p]["sib"]
    assert got == want
query_count = 0
for name in "ABCDX":
    for qlen in range(4):
        for qualifiers in itertools.product("ABCDX", repeat=qlen):
            want = []
            for i, node in enumerate(table.nodes):
                if node["name"] != name:
                    continue
                chain, p = [], node["parent"]
                while p is not None:
                    chain.append(table.nodes[p]["name"])
                    p = table.nodes[p]["parent"]
                if any(tuple(chain[j] for j in indices) == qualifiers
                       for indices in itertools.combinations(range(len(chain)), qlen)):
                    want.append(i)
            got = table.candidates(name, qualifiers)
            assert got == want[::-1]
            if not want:
                raises(LookupError, table.resolve, name, qualifiers)
            elif len(want) > 1:
                raises(ValueError, table.resolve, name, qualifiers)
            else:
                assert table.resolve(name, qualifiers) == want[0]
            query_count += 1
before = copy.deepcopy(table.__dict__)
for bad in (-1, 100, 0.5, True):
    raises(ValueError, table.add, "BAD", bad)
assert table.__dict__ == before
report["checks"]["qualified_names"] = {"nodes": 100, "queries": query_count,
    "child_chains": 100, "invalid_parents": 4}

# Allocator reference: unit occupancy array, independent maximal free-run reconstruction.
Arena = envs[4]["Arena"]


def free_runs(cells):
    runs = []
    for unused, group in itertools.groupby(enumerate(cells), key=lambda item: item[1] is None):
        indices = [i for i, _ in group]
        if unused:
            runs.append((indices[0], len(indices)))
    return runs


allocator_steps = 0
for policy in ("first", "best"):
    for capacity in (1, 7, 32, 97):
        pool, cells = Arena(capacity), [None] * capacity
        allocations = {}
        for step in range(1000):
            if allocations and rng.random() < 0.43:
                p = rng.choice(list(allocations))
                n = allocations.pop(p)
                pool.release(p)
                cells[p:p+n] = [None] * n
            else:
                n = rng.randrange(1, capacity + 4)
                eligible = [(p, length) for p, length in free_runs(cells) if length >= n]
                if not eligible:
                    before = copy.deepcopy(pool.__dict__)
                    raises(MemoryError, pool.allocate, n, policy)
                    assert pool.__dict__ == before
                else:
                    p, _ = eligible[0] if policy == "first" else min(eligible, key=lambda item: (item[1], item[0]))
                    assert pool.allocate(n, policy) == p
                    assert all(c is None for c in cells[p:p+n])
                    cells[p:p+n] = [step] * n
                    allocations[p] = n
            assert pool.free_blocks == free_runs(cells)
            assert pool.live == allocations
            assert sum(pool.live.values()) + sum(n for _, n in pool.free_blocks) == capacity
            allocator_steps += 1
        for p in list(allocations):
            pool.release(p)
        assert pool.free_blocks == [(0, capacity)] and not pool.live
for bad in (0, -1, True, 1.5):
    raises(ValueError, Arena, bad)
pool = Arena(8)
for bad in (0, -1, True, 1.5):
    raises(ValueError, pool.allocate, bad)
raises(ValueError, pool.allocate, 1, "unknown")
p = pool.allocate(3)
raises(ValueError, pool.release, p+1)
pool.release(p)
raises(ValueError, pool.release, p)
assert pool.free_blocks == [(0, 8)]
report["checks"]["interval_allocator"] = {"operation_steps": allocator_steps,
    "invalid_cases": 11, "full_coalescence_cases": 8}

buddy_cases = 0
for m in range(1, 11):
    for k in range(m):
        size = 1 << k
        for p in range(0, 1 << m, size):
            buddy = p ^ size
            assert 0 <= buddy < (1 << m) and buddy % size == 0
            assert (buddy ^ size) == p and abs(buddy-p) == size
            assert min(p, buddy) % (2*size) == 0
            buddy_cases += 1
assert (8 ^ 8) != 16
report["checks"]["buddy_addresses"] = {"aligned_pairs_checked": buddy_cases}
report["checks"]["history"] = {"method": "visual source check of supplied book pages 429-435",
    "primary_papers_individually_read": False, "no_runtime_code": True}
report["all_passed"] = True
(ROOT / "verification/taocp-chapter2-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


report['all_passed'] = True
(ROOT / 'verification/taocp-chapter2-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 2: passed')
