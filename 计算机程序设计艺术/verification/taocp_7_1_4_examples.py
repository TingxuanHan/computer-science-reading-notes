"""Small educational ROBDD/ZDD managers; no complement edges or GC."""
from functools import cache
from itertools import product


class BDD:
    def __init__(self, order):
        self.order = tuple(order)
        assert len(set(self.order)) == len(self.order)
        self.n = len(self.order)
        self.rank = {v: i for i, v in enumerate(self.order)}
        self.nodes = [None, None]  # terminal false / true
        self.unique = {}
        self.memo = {}

    def level(self, u):
        return self.n if u < 2 else self.nodes[u][0]

    def mk(self, level, lo, hi):
        assert 0 <= level < self.n
        assert level < self.level(lo) and level < self.level(hi)
        if lo == hi:
            return lo
        key = (level, lo, hi)
        if key not in self.unique:
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def var(self, name):
        return self.mk(self.rank[name], 0, 1)

    def build(self, f):
        # Enumerates all assignments: suitable only as a small-input oracle.
        def visit(i, assignment):
            if i == self.n:
                return int(bool(f(assignment)))
            v = self.order[i]
            assignment[v] = 0
            lo = visit(i + 1, assignment)
            assignment[v] = 1
            hi = visit(i + 1, assignment)
            del assignment[v]
            return self.mk(i, lo, hi)
        return visit(0, {})

    def evaluate(self, u, assignment):
        while u >= 2:
            i, lo, hi = self.nodes[u]
            u = hi if assignment[self.order[i]] else lo
        return u

    def apply(self, op, u, v):
        # op bit 2*a+b specifies the result on Boolean arguments a,b.
        assert 0 <= op < 16
        key = (op, u, v)
        if key in self.memo:
            return self.memo[key]
        if u < 2 and v < 2:
            return (op >> (2 * u + v)) & 1
        i = min(self.level(u), self.level(v))
        ul, uh = self.nodes[u][1:] if self.level(u) == i else (u, u)
        vl, vh = self.nodes[v][1:] if self.level(v) == i else (v, v)
        result = self.mk(i, self.apply(op, ul, vl), self.apply(op, uh, vh))
        self.memo[key] = result
        return result

    def restrict(self, root, fixed):
        assert all(v in self.rank and b in (0, 1) for v, b in fixed.items())
        @cache
        def visit(u):
            if u < 2:
                return u
            i, lo, hi = self.nodes[u]
            v = self.order[i]
            if v in fixed:
                return visit(hi if fixed[v] else lo)
            return self.mk(i, visit(lo), visit(hi))
        return visit(root)

    def quantify(self, root, variable, universal=False):
        lo = self.restrict(root, {variable: 0})
        hi = self.restrict(root, {variable: 1})
        return self.apply(0b1000 if universal else 0b1110, lo, hi)

    def count(self, root):
        @cache
        def below(u):
            if u < 2:
                return u
            i, lo, hi = self.nodes[u]
            return ((1 << (self.level(lo) - i - 1)) * below(lo)
                    + (1 << (self.level(hi) - i - 1)) * below(hi))
        return (1 << self.level(root)) * below(root)

    def probability(self, root, probabilities):
        assert all(0 <= probabilities[v] <= 1 for v in self.order)
        @cache
        def visit(u):
            if u < 2:
                return u
            i, lo, hi = self.nodes[u]
            p = probabilities[self.order[i]]
            return (1 - p) * visit(lo) + p * visit(hi)
        return visit(root)

    def nonterminals(self, root):
        seen = set()
        def visit(u):
            if u < 2 or u in seen:
                return
            seen.add(u)
            _, lo, hi = self.nodes[u]
            visit(lo)
            visit(hi)
        visit(root)
        return len(seen)


class ZDD:
    def __init__(self):
        self.nodes = [None, None]  # empty family / family containing empty set
        self.unique = {}

    def mk(self, element, lo, hi):
        if hi == 0:
            return lo
        key = (element, lo, hi)
        if key not in self.unique:
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def build(self, family):
        family = frozenset(frozenset(s) for s in family)
        @cache
        def visit(f):
            if not f:
                return 0
            elements = set().union(*f)
            if not elements:
                return 1
            v = min(elements)
            lo = visit(frozenset(s for s in f if v not in s))
            hi = visit(frozenset(s - {v} for s in f if v in s))
            return self.mk(v, lo, hi)
        return visit(family)

    def count(self, root):
        @cache
        def visit(u):
            if u < 2:
                return u
            _, lo, hi = self.nodes[u]
            return visit(lo) + visit(hi)
        return visit(root)


if __name__ == '__main__':
    b = BDD(('s', 'a', 'b'))
    s, a, v = (b.var(x) for x in b.order)
    mux = b.apply(6, a, b.apply(8, s, b.apply(6, a, v)))
    direct = b.build(lambda x: x['b'] if x['s'] else x['a'])
    assert mux == direct and b.count(mux) == 4
    assert b.restrict(mux, {'s': 0}) == a
    assert b.quantify(mux, 's') == b.apply(14, a, v)
    assert b.probability(mux, dict.fromkeys(b.order, 0.5)) == 0.5
    for n in (2, 4, 6):
        xs, ys = [f'x{i}' for i in range(n)], [f'y{i}' for i in range(n)]
        sizes = []
        for order in (sum(zip(xs, ys), ()), tuple(xs + ys)):
            manager = BDD(order)
            root = manager.build(lambda a: all(a[x] == a[y] for x, y in zip(xs, ys)))
            assert manager.count(root) == 1 << n
            sizes.append(manager.nonterminals(root))
        print('equality pairs / interleaved / grouped:', n, *sizes)
    z = ZDD()
    root = z.build([set(), {1}, {1, 3}])
    assert z.count(root) == 3
    print('BDD construction, Apply, restriction, quantification, counting: passed')
