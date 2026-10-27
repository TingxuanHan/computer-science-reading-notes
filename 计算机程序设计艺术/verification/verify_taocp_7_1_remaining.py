import json
import random
from fractions import Fraction
from itertools import product, combinations
from pathlib import Path
import taocp_7_1_2_examples as e2
import taocp_7_1_3_examples as e3
from taocp_7_1_4_examples import BDD, ZDD


def save(section, checks):
    out = {'section': section, 'date': '2026-10-27', 'status': 'passed', 'checks': checks}
    (Path(__file__).resolve().parent / f'taocp-{section}-report.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False))


def verify2():
    for op, a, b in product(range(16), repeat=3):
        want = sum(((op >> (2 * ((a >> k) & 1) + ((b >> k) & 1))) & 1) << k
                   for k in range(4))
        assert e2.gate(op, a, b, 15) == want
    mux = e2.truth(3, lambda s, a, b: b if s else a)
    assert not e2.possible_in_two_gates(3, mux)
    assert mux == e2.truth(3, lambda s, a, b: a ^ (s & (a ^ b)))
    for bits in product((0, 1), repeat=4):
        assert e2.exact_two(*bits) == (sum(bits) == 2)
    for bits in product((0, 1), repeat=3):
        s, c = e2.full_adder(*bits)
        assert s + 2 * c == sum(bits)
    decompositions = 0
    for table in range(256):
        f = lambda *xs, t=table: (t >> sum(v << k for k, v in enumerate(xs))) & 1
        for size in (1, 2):
            for zs in combinations(range(3), size):
                ys, zs, types, labels = e2.column_types(3, f, zs)
                for xs in product((0, 1), repeat=3):
                    y = sum(xs[i] << k for k, i in enumerate(ys))
                    z = sum(xs[i] << k for k, i in enumerate(zs))
                    assert types[labels[z]][y] == f(*xs)
                columns = [types[i] for i in labels]
                possible = any(all(columns[i] == columns[j]
                                   for i in range(len(columns)) for j in range(i)
                                   if colors[i] == colors[j])
                               for colors in product((0, 1), repeat=len(columns)))
                assert possible == (len(types) <= 2)
                decompositions += 1
    partial_cases = 0
    for values in product((None, 0, 1), repeat=8):
        cols = [values[k:k+2] for k in range(0, 8, 2)]
        result = e2.one_bit_partial_decomposition(cols)
        possible = any(all(not (colors[i] == colors[j] and
                               any(a is not None and b is not None and a != b
                                   for a, b in zip(cols[i], cols[j])))
                           for i in range(4) for j in range(i))
                       for colors in product((0, 1), repeat=4))
        assert (result is not None) == possible
        if result:
            colors, reps = result
            assert all(v is None or v == reps[colors[i]][j]
                       for i, col in enumerate(cols) for j, v in enumerate(col))
        partial_cases += 1
    save('7.1.2', {'binary_gate_truth_checks': 4096, 'mux_minimum_gates': 3,
                  'exact_two_assignments': 16, 'full_adder_assignments': 8,
                  'complete_decompositions': decompositions,
                  'partial_column_tables': partial_cases})


def verify3():
    rng = random.Random(713)
    for x in range(65536):
        assert e3.popcount64(x) == x.bit_count()
        assert e3.reverse_bits(x, 16) == int(f'{x:016b}'[::-1], 2)
        assert e3.ctz(x, 16) == next((i for i in range(16) if x & (1 << i)), 16)
        expected = sum(128 << (8 * k) for k in range(2) if (x >> (8 * k)) & 255 == 0)
        assert bool(e3.zero_byte_flags(x, 16)) == bool(expected)
        assert e3.exact_zero_byte_flags(x, 16) == expected
    assert e3.zero_byte_flags(0x0100, 16) == 0x8080
    for x, m in product(range(256), repeat=2):
        bits = [i for i in range(8) if (m >> i) & 1]
        assert e3.extract_bits(x, m) == sum(((x >> i) & 1) << j for j, i in enumerate(bits))
    for a, b in product(range(256), repeat=2):
        x = a * e3.L64
        y = b * e3.L64
        assert e3.add_bytes64(x, y) == ((a + b) & 255) * e3.L64
    samples = [1 << i for i in range(64)] + [rng.getrandbits(64) for _ in range(2000)]
    for x in samples:
        assert e3.popcount64(x) == x.bit_count()
        assert e3.reverse_bits(x, 64) == int(f'{x:064b}'[::-1], 2)
        t = sum(((x >> (8*r+c)) & 1) << (8*c+r) for r in range(8) for c in range(8))
        assert e3.transpose8(x) == t
        y = rng.getrandbits(64)
        want = sum((((x >> (8*k) & 255) + (y >> (8*k) & 255)) & 255) << (8*k)
                   for k in range(8))
        assert e3.add_bytes64(x, y) == want
        for s in (0, 1):
            assert e3.select_word(s, x, y) == (y if s else x)
    edges = [(i, j) for i in range(4) for j in range(4) if i != j]
    for graph in range(1 << len(edges)):
        rows = [0] * 4
        for k, (i, j) in enumerate(edges):
            if (graph >> k) & 1:
                rows[i] |= 1 << j
        for start in range(16):
            visited = {i for i in range(4) if (start >> i) & 1}
            queue = list(visited)
            for v in queue:
                for u in range(4):
                    if rows[v] & (1 << u) and u not in visited:
                        visited.add(u)
                        queue.append(u)
            assert e3.reachable(rows, start) == sum(1 << i for i in visited)
    save('7.1.3', {'all_16_bit_words': 65536, 'all_8_bit_extract_masks': 65536,
                  'all_byte_add_pairs': 65536, 'full_width_matrix_and_word_cases': len(samples),
                  'four_vertex_graph_start_pairs': 65536, 'zero_byte_counterexample_verified': True})


def verify4():
    b = BDD((0, 1, 2))
    assignments = [dict(enumerate(xs)) for xs in product((0, 1), repeat=3)]
    roots = []
    for table in range(256):
        f = lambda a, t=table: (t >> (a[0] * 4 + a[1] * 2 + a[2])) & 1
        u = b.build(f)
        roots.append(u)
        assert b.count(u) == table.bit_count()
        for a in assignments:
            assert b.evaluate(u, a) == f(a)
        for vals in product((None, 0, 1), repeat=3):
            fixed = {i: v for i, v in enumerate(vals) if v is not None}
            r = b.restrict(u, fixed)
            for a in assignments:
                assert b.evaluate(r, a) == f(a | fixed)
        for v in range(3):
            for universal in (False, True):
                r = b.quantify(u, v, universal)
                for a in assignments:
                    values = [f(a | {v: k}) for k in (0, 1)]
                    assert b.evaluate(r, a) == (all(values) if universal else any(values))
        ps = {0: Fraction(1, 3), 1: Fraction(2, 5), 2: Fraction(3, 7)}
        want = Fraction(0)
        for a in assignments:
            p = Fraction(1)
            for v in range(3):
                p *= ps[v] if a[v] else 1 - ps[v]
            want += p * f(a)
        assert b.probability(u, ps) == want
    assert len(set(roots)) == 256
    c = BDD((0, 1))
    funcs = [c.build(lambda a, t=t: (t >> (2*a[0]+a[1])) & 1) for t in range(16)]
    for op, t, s in product(range(16), repeat=3):
        u = c.apply(op, funcs[t], funcs[s])
        expected = sum(((op >> (2*((t >> k)&1)+((s >> k)&1)))&1) << k for k in range(4))
        assert u == funcs[expected]
    equality_sizes = []
    for n in range(1, 9):
        xs, ys = [f'x{i}' for i in range(n)], [f'y{i}' for i in range(n)]
        sizes = []
        for order in (sum(zip(xs, ys), ()), tuple(xs + ys)):
            m = BDD(order)
            u = m.build(lambda a: all(a[x] == a[y] for x, y in zip(xs, ys)))
            assert m.count(u) == 1 << n
            sizes.append(m.nonterminals(u))
        assert sizes == [3*n, 3*(1 << n)-3]
        equality_sizes.append([n] + sizes)
    subsets = [frozenset(i for i in range(3) if (mask >> i) & 1) for mask in range(8)]
    for f in range(256):
        family = frozenset(subsets[k] for k in range(8) if (f >> k) & 1)
        z = ZDD()
        u = z.build(family)
        def decode(u):
            if u == 0:
                return frozenset()
            if u == 1:
                return frozenset((frozenset(),))
            v, lo, hi = z.nodes[u]
            return decode(lo) | frozenset(s | {v} for s in decode(hi))
        assert decode(u) == family
        assert z.count(u) == len(family)
    save('7.1.4', {'all_three_variable_functions': 256, 'restriction_cases': 256*27,
                  'quantification_cases': 256*3*2, 'exact_probability_cases': 256,
                  'all_two_variable_binary_compositions': 4096,
                  'equality_nonterminal_sizes': equality_sizes, 'all_three_element_set_families': 256})


if __name__ == '__main__':
    verify2()
    verify3()
    verify4()
