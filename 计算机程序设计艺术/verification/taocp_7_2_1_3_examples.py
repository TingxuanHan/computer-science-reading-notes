from itertools import combinations
from math import comb


def lex_combinations(n, k):
    if n < 0 or not 0 <= k <= n:
        raise ValueError('require 0 <= k <= n')
    a = list(range(k))
    while True:
        yield tuple(a)
        j = k - 1
        while j >= 0 and a[j] == n - k + j:
            j -= 1
        if j < 0:
            return
        a[j] += 1
        for i in range(j + 1, k):
            a[i] = a[i - 1] + 1


def colex_rank(a):
    if any(x < 0 for x in a) or any(x >= y for x, y in zip(a, a[1:])):
        raise ValueError('expected strictly increasing nonnegative entries')
    return sum(comb(x, i) for i, x in enumerate(a, 1))


def colex_unrank(n, k, r):
    if n < 0 or not 0 <= k <= n or not 0 <= r < comb(n, k):
        raise ValueError('invalid n, k or rank')
    a, x = [0] * k, n - 1
    for i in range(k, 0, -1):
        while comb(x, i) > r:
            x -= 1
        a[i - 1] = x
        r -= comb(x, i)
        x -= 1
    return tuple(a)


def fixed_weight_gray(n, k):
    if n < 0 or not 0 <= k <= n:
        raise ValueError('require 0 <= k <= n')

    def walk(width, weight, reverse=False):
        if weight == 0:
            yield 0
        elif weight == width:
            yield (1 << width) - 1
        elif not reverse:
            yield from walk(width - 1, weight)
            for x in walk(width - 1, weight - 1, True):
                yield (1 << (width - 1)) | x
        else:
            for x in walk(width - 1, weight - 1):
                yield (1 << (width - 1)) | x
            yield from walk(width - 1, weight, True)
    yield from walk(n, k)


def verify():
    count = 0
    for n in range(11):
        for k in range(n + 1):
            want = list(combinations(range(n), k))
            assert list(lex_combinations(n, k)) == want
            ordered = sorted(want, key=lambda a: tuple(reversed(a)))
            for r, a in enumerate(ordered):
                assert colex_rank(a) == r
                assert colex_unrank(n, k, r) == a
            gray = list(fixed_weight_gray(n, k))
            assert len(gray) == len(set(gray)) == comb(n, k)
            assert set(gray) == {sum(1 << i for i in a) for a in want}
            assert all((a ^ b).bit_count() == 2 for a, b in zip(gray, gray[1:]))
            count += len(want)
    return {'combinations_checked': count, 'max_n': 10}


if __name__ == '__main__':
    print(verify())
