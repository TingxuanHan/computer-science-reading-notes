from functools import lru_cache
from itertools import product


def set_partitions_rgs(n, blocks=None):
    if n < 0 or (blocks is not None and not 0 <= blocks <= n):
        raise ValueError('invalid n or block count')
    a = []

    def visit(k):
        remaining = n - len(a)
        if blocks is not None and (k > blocks or k + remaining < blocks):
            return
        if remaining == 0:
            yield tuple(a)
            return
        for label in range(k + 1):
            a.append(label)
            yield from visit(max(k, label + 1))
            a.pop()
    yield from visit(0)


@lru_cache(None)
def completions(remaining, blocks):
    if remaining == 0:
        return 1
    return blocks * completions(remaining - 1, blocks) + completions(remaining - 1, blocks + 1)


def rgs_unrank(n, r):
    if n < 0 or not 0 <= r < completions(n, 0):
        raise ValueError('invalid n or rank')
    result, k = [], 0
    for i in range(n):
        for label in range(k + 1):
            next_k = max(k, label + 1)
            size = completions(n - i - 1, next_k)
            if r < size:
                result.append(label)
                k = next_k
                break
            r -= size
    return tuple(result)


def stirling_row(n):
    row = [1]
    for _ in range(n):
        new = [0] * (len(row) + 1)
        for k in range(1, len(new)):
            new[k] = row[k - 1] + (k * row[k] if k < len(row) else 0)
        row = new
    return row


def canonical_labels(a):
    names = {}
    result = []
    for x in a:
        if x not in names:
            names[x] = len(names)
        result.append(names[x])
    return tuple(result)


def verify():
    total = 0
    for n in range(8):
        rows = list(set_partitions_rgs(n))
        counts = stirling_row(n)
        assert len(rows) == len(set(rows)) == sum(counts) == completions(n, 0)
        assert rows == sorted(rows)
        for k in range(n + 1):
            assert len(list(set_partitions_rgs(n, k))) == counts[k]
        for rank, a in enumerate(rows):
            assert rgs_unrank(n, rank) == a
            assert canonical_labels(a) == a
        if n <= 5:
            brute = {canonical_labels(a) for a in product(range(n), repeat=n)}
            assert set(rows) == brute
        total += len(rows)
    return {'set_partitions_checked': total, 'brute_force_max_n': 5}


if __name__ == '__main__':
    print(verify())
