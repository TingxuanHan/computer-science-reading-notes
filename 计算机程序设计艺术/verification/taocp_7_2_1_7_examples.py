from functools import lru_cache
from itertools import combinations, permutations, product
from math import comb


@lru_cache(None)
def rhythms(duration):
    if duration == 0:
        return ((),)
    if duration < 0:
        return ()
    return tuple((beat,) + tail for beat in (1, 2) for tail in rhythms(duration - beat))


def bell(n):
    b = [1]
    for i in range(1, n + 1):
        b.append(sum(comb(i - 1, j) * b[i - 1 - j] for j in range(i)))
    return b[n]


def verify():
    assert len(list(product((0, 1), repeat=6))) == 64
    fib = [0, 1]
    for _ in range(10):
        fib.append(fib[-1] + fib[-2])
    for n in range(11):
        rows = rhythms(n)
        assert len(rows) == len(set(rows)) == fib[n + 1]
        assert all(sum(a) == n for a in rows)
    assert len(set(permutations((0, 0, 1, 1)))) == 6
    assert len(list(combinations(range(5), 3))) == 10
    assert bell(5) == 52
    assert comb(8, 4) // 5 == 14
    return {'binary_patterns': 64, 'rhythm_duration_7': len(rhythms(7)),
            'bell_5': bell(5), 'catalan_4': 14,
            'scope': 'mathematical checks, not historical evidence'}


if __name__ == '__main__':
    print(verify())
