from functools import lru_cache
from itertools import product
from math import comb


def dyck_words(n):
    if n < 0:
        raise ValueError('n must be nonnegative')
    path = []

    def visit(opened, closed):
        if closed == n:
            yield ''.join(path)
            return
        if opened < n:
            path.append('(')
            yield from visit(opened + 1, closed)
            path.pop()
        if closed < opened:
            path.append(')')
            yield from visit(opened, closed + 1)
            path.pop()
    yield from visit(0, 0)


def decode_binary(word):
    def parse(pos):
        if pos == len(word) or word[pos] == ')':
            return None, pos
        left, pos = parse(pos + 1)
        if pos >= len(word) or word[pos] != ')':
            raise ValueError('unbalanced word')
        right, pos = parse(pos + 1)
        return (left, right), pos
    if any(x not in '()' for x in word):
        raise ValueError('invalid symbol')
    tree, end = parse(0)
    if end != len(word):
        raise ValueError('unbalanced word')
    return tree


def encode_binary(tree):
    if tree is None:
        return ''
    left, right = tree
    return '(' + encode_binary(left) + ')' + encode_binary(right)


@lru_cache(None)
def suffix_count(opens_left, balance):
    if opens_left == 0:
        return 1
    return suffix_count(opens_left - 1, balance + 1) + (suffix_count(opens_left, balance - 1) if balance else 0)


def dyck_unrank(n, rank):
    if n < 0 or not 0 <= rank < suffix_count(n, 0):
        raise ValueError('invalid n or rank')
    a, left, balance = [], n, 0
    while left or balance:
        first = suffix_count(left - 1, balance + 1) if left else 0
        if rank < first:
            a.append('(')
            left -= 1
            balance += 1
        else:
            rank -= first
            if balance == 0:
                raise AssertionError('invalid completion count')
            a.append(')')
            balance -= 1
    return ''.join(a)


def valid_word(word):
    balance = 0
    for x in word:
        balance += 1 if x == '(' else -1
        if balance < 0:
            return False
    return balance == 0


def verify():
    total = 0
    for n in range(9):
        rows = list(dyck_words(n))
        catalan = comb(2 * n, n) // (n + 1)
        assert len(rows) == len(set(rows)) == catalan == suffix_count(n, 0)
        assert rows == sorted(rows)
        assert len({decode_binary(w) for w in rows}) == catalan
        for rank, w in enumerate(rows):
            assert valid_word(w)
            assert encode_binary(decode_binary(w)) == w
            assert dyck_unrank(n, rank) == w
        if n <= 6:
            brute = {''.join(w) for w in product('()', repeat=2 * n) if valid_word(w)}
            assert set(rows) == brute
        total += len(rows)
    return {'tree_shapes_checked': total, 'max_n': 8}


if __name__ == '__main__':
    print(verify())
