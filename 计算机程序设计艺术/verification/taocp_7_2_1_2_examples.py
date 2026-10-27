from itertools import permutations
from math import factorial


def lex_permutations(items):
    a = sorted(items)
    while True:
        yield tuple(a)
        j = len(a) - 2
        while j >= 0 and a[j] >= a[j + 1]:
            j -= 1
        if j < 0:
            return
        k = len(a) - 1
        while a[k] <= a[j]:
            k -= 1
        a[j], a[k] = a[k], a[j]
        a[j + 1:] = reversed(a[j + 1:])


def rank_permutation(a):
    n = len(a)
    if sorted(a) != list(range(n)):
        raise ValueError('expected a permutation of range(n)')
    pool, r = list(range(n)), 0
    for i, value in enumerate(a):
        j = pool.index(value)
        r += j * factorial(n - i - 1)
        pool.pop(j)
    return r


def unrank_permutation(n, r):
    if n < 0 or not 0 <= r < factorial(n):
        raise ValueError('invalid n or rank')
    pool, a = list(range(n)), []
    for width in range(n, 0, -1):
        j, r = divmod(r, factorial(width - 1))
        a.append(pool.pop(j))
    return tuple(a)


def adjacent_permutations(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    a, direction = list(range(n)), [-1] * n
    while True:
        yield tuple(a)
        mobile = [(v, i) for i, v in enumerate(a)
                  if 0 <= i + direction[v] < n and v > a[i + direction[v]]]
        if not mobile:
            return
        value, i = max(mobile)
        j = i + direction[value]
        a[i], a[j] = a[j], a[i]
        for v in range(value + 1, n):
            direction[v] *= -1


def verify():
    tested = 0
    for n in range(8):
        want = list(permutations(range(n)))
        got = list(lex_permutations(range(n)))
        assert got == want
        for r, a in enumerate(got):
            assert rank_permutation(a) == r
            assert unrank_permutation(n, r) == a
        adjacent = list(adjacent_permutations(n))
        assert len(adjacent) == len(set(adjacent)) == factorial(n)
        assert set(adjacent) == set(want)
        for a, b in zip(adjacent, adjacent[1:]):
            diff = [i for i in range(n) if a[i] != b[i]]
            assert len(diff) == 2 and diff[1] == diff[0] + 1
            i, j = diff
            assert a[i] == b[j] and a[j] == b[i]
        tested += len(want)
    for items in [[], [2], [1, 1, 2], [0, 0, 1, 1, 2], [3, 3, 3]]:
        assert list(lex_permutations(items)) == sorted(set(permutations(items)))
    return {'distinct_permutations_checked': tested, 'multiset_cases': 5}


if __name__ == '__main__':
    print(verify())
