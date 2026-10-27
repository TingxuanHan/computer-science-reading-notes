from itertools import product
from math import prod


def mixed_tuples(radices):
    m = tuple(radices)
    if any(v < 1 for v in m):
        raise ValueError('radices must be positive')
    a = [0] * len(m)
    while True:
        yield tuple(a)
        j = len(a) - 1
        while j >= 0 and a[j] == m[j] - 1:
            a[j] = 0
            j -= 1
        if j < 0:
            return
        a[j] += 1


def rank_tuple(a, m):
    if len(a) != len(m) or any(b < 1 or not 0 <= x < b for x, b in zip(a, m)):
        raise ValueError('invalid tuple')
    r = 0
    for x, base in zip(a, m):
        r = r * base + x
    return r


def unrank_tuple(r, m):
    if any(b < 1 for b in m) or not 0 <= r < prod(m):
        raise ValueError('invalid rank or radix')
    a = [0] * len(m)
    for j in range(len(m) - 1, -1, -1):
        r, a[j] = divmod(r, m[j])
    return tuple(a)


def gray_focus(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    a = [0] * n                 # index 0 is the low bit
    focus = list(range(n + 1))
    while True:
        yield tuple(a)
        j = focus[0]
        focus[0] = 0
        if j == n:
            return
        focus[j] = focus[j + 1]
        focus[j + 1] = j + 1
        a[j] ^= 1


def inverse_gray(g):
    b = 0
    while g:
        b ^= g
        g >>= 1
    return b


def de_bruijn(k, n):
    if k < 1 or n < 1:
        raise ValueError('k and n must be positive')
    a, answer = [0] * (n + 1), []

    def visit(t, period):
        if t > n:
            if n % period == 0:
                answer.extend(a[1:period + 1])
            return
        a[t] = a[t - period]
        visit(t + 1, period)
        for digit in range(a[t - period] + 1, k):
            a[t] = digit
            visit(t + 1, t)
    visit(1, 1)
    return tuple(answer)


def verify():
    tuple_cases = 0
    for n in range(5):
        for m in product(range(1, 4), repeat=n):
            got = list(mixed_tuples(m))
            assert got == list(product(*(range(b) for b in m)))
            for r, a in enumerate(got):
                assert rank_tuple(a, m) == r
                assert unrank_tuple(r, m) == a
                tuple_cases += 1
    for n in range(11):
        rows = list(gray_focus(n))
        words = [sum(bit << j for j, bit in enumerate(a)) for a in rows]
        assert words == [r ^ (r >> 1) for r in range(1 << n)]
        assert len(set(words)) == 1 << n
        assert all((x ^ y).bit_count() == 1 for x, y in zip(words, words[1:]))
        assert all(inverse_gray(g) == r for r, g in enumerate(words))
    for k in range(1, 4):
        for n in range(1, 6):
            cycle = de_bruijn(k, n)
            windows = {tuple(cycle[(i + j) % len(cycle)] for j in range(n))
                       for i in range(len(cycle))}
            assert len(cycle) == k ** n
            assert windows == set(product(range(k), repeat=n))
    return {'tuple_rank_roundtrips': tuple_cases, 'gray_max_n': 10,
            'de_bruijn_cases': 15}


if __name__ == '__main__':
    print(verify())
