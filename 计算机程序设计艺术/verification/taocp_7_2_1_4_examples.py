from functools import lru_cache


def partitions(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    path = []

    def visit(left, ceiling):
        if left == 0:
            yield tuple(path)
            return
        for x in range(min(left, ceiling), 0, -1):
            path.append(x)
            yield from visit(left - x, x)
            path.pop()
    yield from visit(n, n)


@lru_cache(None)
def p_bounded(n, m):
    if n == 0:
        return 1
    if n < 0 or m == 0:
        return 0
    if m > n:
        return p_bounded(n, n)
    return p_bounded(n, m - 1) + p_bounded(n - m, m)


@lru_cache(None)
def p_exact(n, k):
    if n == 0:
        return int(k == 0)
    if n < 0 or k <= 0:
        return 0
    return p_exact(n - 1, k - 1) + p_exact(n - k, k)


def conjugate(a):
    return tuple(sum(x >= j for x in a) for j in range(1, a[0] + 1)) if a else ()


def euler_partition_counts(limit):
    values = [1] + [0] * limit
    for n in range(1, limit + 1):
        k = 1
        while k * (3 * k - 1) // 2 <= n:
            sign = 1 if k % 2 else -1
            for g in (k * (3 * k - 1) // 2, k * (3 * k + 1) // 2):
                if g <= n:
                    values[n] += sign * values[n - g]
            k += 1
    return values


def verify():
    count = 0
    expected = euler_partition_counts(40)
    for n in range(41):
        assert p_bounded(n, n) == expected[n]
        assert sum(p_exact(n, k) for k in range(n + 1)) == expected[n]
        if n > 18:
            continue
        rows = list(partitions(n))
        assert len(rows) == len(set(rows)) == expected[n]
        assert rows == sorted(rows, reverse=True)
        for a in rows:
            assert sum(a) == n and all(x > 0 for x in a)
            assert all(x >= y for x, y in zip(a, a[1:]))
            assert conjugate(conjugate(a)) == a
        for k in range(n + 1):
            assert sum(len(a) == k for a in rows) == p_exact(n, k)
        assert sum(all(x % 2 for x in a) for a in rows) == sum(len(a) == len(set(a)) for a in rows)
        count += len(rows)
    return {'partitions_enumerated': count, 'counts_checked_through': 40}


if __name__ == '__main__':
    print(verify())
