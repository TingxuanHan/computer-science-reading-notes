"""Original executable examples for TAOCP 7.1.2 (Python 3.10+)."""
from itertools import product


def truth(n, f):
    # Bit k represents x_i = (k >> i) & 1.
    return sum(int(bool(f(*((k >> i) & 1 for i in range(n))))) << k
               for k in range(1 << n))


def gate(op, a, b, mask):
    # op's bit 2*a+b is the binary gate's output.
    terms = (~a & ~b, ~a & b, a & ~b, a & b)
    out = 0
    for k, term in enumerate(terms):
        if (op >> k) & 1:
            out |= term
    return out & mask


def possible_in_two_gates(n, target):
    mask = (1 << (1 << n)) - 1
    base = {0, mask}
    for i in range(n):
        base.add(truth(n, lambda *xs, i=i: xs[i]))
    one = {gate(op, a, b, mask)
           for a in base for b in base for op in range(16)}
    if target in base | one:
        return True
    for first in one:
        available = base | {first}
        for a, b in product(available, repeat=2):
            for op in range(16):
                if gate(op, a, b, mask) == target:
                    return True
    return False


def exact_two(a, b, c, d):
    t1 = a ^ c
    t2 = a ^ b
    t3 = c ^ d
    t4 = t1 | t2
    t5 = t2 ^ t3
    return t4 & (1 ^ t5)


def full_adder(a, b, c):
    t = a ^ b
    s = t ^ c
    u = t & c
    v = a & b
    return s, u | v


def column_types(n, f, z_indices):
    """Return Y coordinates, Z coordinates, column representatives, labels."""
    z_indices = tuple(z_indices)
    assert len(set(z_indices)) == len(z_indices)
    assert all(0 <= i < n for i in z_indices)
    y_indices = tuple(i for i in range(n) if i not in z_indices)
    types, labels = [], []
    for z in range(1 << len(z_indices)):
        column = []
        for y in range(1 << len(y_indices)):
            xs = [0] * n
            for k, i in enumerate(z_indices):
                xs[i] = (z >> k) & 1
            for k, i in enumerate(y_indices):
                xs[i] = (y >> k) & 1
            column.append(int(bool(f(*xs))))
        column = tuple(column)
        if column not in types:
            types.append(column)
        labels.append(types.index(column))
    return y_indices, z_indices, types, labels


def one_bit_partial_decomposition(columns):
    """None denotes a don't-care. Return coloring/completions or None."""
    assert columns and len({len(c) for c in columns}) == 1
    graph = [[] for _ in columns]
    for i in range(len(columns)):
        for j in range(i):
            conflict = any(a is not None and b is not None and a != b
                           for a, b in zip(columns[i], columns[j]))
            if conflict:
                graph[i].append(j)
                graph[j].append(i)
    colors = [None] * len(columns)
    for start in range(len(columns)):
        if colors[start] is not None:
            continue
        colors[start] = 0
        stack = [start]
        while stack:
            i = stack.pop()
            for j in graph[i]:
                if colors[j] is None:
                    colors[j] = colors[i] ^ 1
                    stack.append(j)
                elif colors[j] == colors[i]:
                    return None
    representatives = []
    for color in (0, 1):
        merged = []
        for row in range(len(columns[0])):
            specified = {columns[i][row] for i in range(len(columns))
                         if colors[i] == color and columns[i][row] is not None}
            assert len(specified) <= 1
            merged.append(next(iter(specified), 0))
        representatives.append(tuple(merged))
    return colors, representatives


if __name__ == '__main__':
    mux = truth(3, lambda s, a, b: a if s == 0 else b)
    assert not possible_in_two_gates(3, mux)
    assert mux == truth(3, lambda s, a, b: a ^ (s & (a ^ b)))
    for xs in product((0, 1), repeat=4):
        assert exact_two(*xs) == (sum(xs) == 2)
    for xs in product((0, 1), repeat=3):
        s, c = full_adder(*xs)
        assert s + 2 * c == sum(xs)
    _, _, types, labels = column_types(
        3, lambda y, z0, z1: y ^ (z0 & z1), (1, 2))
    assert len(types) == 2 and labels == [0, 0, 0, 1]
    print('mux: 3 gates are sufficient; 0/1/2 gates are impossible')
    print('exact-two: 16 cases; full adder: 8 cases; decomposition: passed')
