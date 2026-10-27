from fractions import Fraction
from itertools import permutations


def queens(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    cols, down, up, path = set(), set(), set(), []
    profile = [0] * (n + 1)
    answers = []

    def visit(row):
        profile[row] += 1
        if row == n:
            answers.append(tuple(path))
            return
        for col in range(n):
            if col in cols or row - col in down or row + col in up:
                continue
            cols.add(col)
            down.add(row - col)
            up.add(row + col)
            path.append(col)
            try:
                visit(row + 1)
            finally:
                path.pop()
                up.remove(row + col)
                down.remove(row - col)
                cols.remove(col)
    visit(0)
    assert not cols and not down and not up and not path
    return answers, profile


def queens_bit_count(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    mask = (1 << n) - 1

    def visit(cols, left, right):
        if cols == mask:
            return 1
        available = mask & ~(cols | left | right)
        total = 0
        while available:
            bit = available & -available
            available ^= bit
            total += visit(cols | bit, ((left | bit) << 1) & mask, (right | bit) >> 1)
        return total
    return visit(0, 0, 0)


def exact_path_estimate(tree):
    # tree[node] is a tuple of children; absence means a leaf.
    def paths(node, probability, weight, estimate):
        children = tree.get(node, ())
        if not children:
            return probability * estimate
        b = len(children)
        return sum(paths(child, probability / b, weight * b, estimate + weight * b)
                   for child in children)
    return paths('root', Fraction(1), 1, 1)


def verify():
    known = [1, 1, 0, 0, 2, 10, 4, 40, 92]
    for n in range(9):
        rows, profile = queens(n)
        brute = {a for a in permutations(range(n))
                 if len({i - a[i] for i in range(n)}) == n
                 and len({i + a[i] for i in range(n)}) == n}
        assert len(rows) == len(set(rows)) == known[n] == queens_bit_count(n)
        assert set(rows) == brute
        assert profile[-1] == len(rows)
    tree = {'root': ('a', 'b'), 'a': ('c', 'd', 'e'), 'b': ('f',), 'd': ('g', 'h')}
    assert exact_path_estimate(tree) == 9
    return {'queens_counts': known, 'n8_profile': queens(8)[1],
            'path_estimator_exact_expectation': str(exact_path_estimate(tree))}


if __name__ == '__main__':
    print(verify())
