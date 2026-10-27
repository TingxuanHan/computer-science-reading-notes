from itertools import combinations, product
from random import Random


class DLX:
    def __init__(self, ncols, rows, primary=None):
        if ncols < 0:
            raise ValueError('negative column count')
        primary = set(range(ncols)) if primary is None else set(primary)
        if not primary <= set(range(ncols)):
            raise ValueError('invalid primary column')
        n = ncols + 1             # header 0 is the root
        self.L, self.R = list(range(n)), list(range(n))
        self.U, self.D = list(range(n)), list(range(n))
        self.C, self.row = list(range(n)), [-1] * n
        self.size = [0] * n
        tail = 0
        for col in sorted(primary):
            h = col + 1
            self.L[h], self.R[h] = tail, 0
            self.R[tail], self.L[0] = h, h
            tail = h
        for rid, raw in enumerate(rows):
            values = list(raw)
            if not values or len(values) != len(set(values)) or any(c < 0 or c >= ncols for c in values):
                raise ValueError('rows must contain distinct valid columns')
            if not set(values) & primary:
                raise ValueError('this interface requires a primary item in every row')
            nodes = []
            for col in values:
                h, x = col + 1, len(self.L)
                self.L.append(x); self.R.append(x)
                self.U.append(self.U[h]); self.D.append(h)
                self.C.append(h); self.row.append(rid)
                self.D[self.U[h]] = x
                self.U[h] = x
                self.size[h] += 1
                nodes.append(x)
            for j, x in enumerate(nodes):
                self.L[x], self.R[x] = nodes[j - 1], nodes[(j + 1) % len(nodes)]

    def cover(self, c):
        self.R[self.L[c]] = self.R[c]
        self.L[self.R[c]] = self.L[c]
        i = self.D[c]
        while i != c:
            j = self.R[i]
            while j != i:
                self.D[self.U[j]] = self.D[j]
                self.U[self.D[j]] = self.U[j]
                self.size[self.C[j]] -= 1
                j = self.R[j]
            i = self.D[i]

    def uncover(self, c):
        i = self.U[c]
        while i != c:
            j = self.L[i]
            while j != i:
                self.size[self.C[j]] += 1
                self.D[self.U[j]] = j
                self.U[self.D[j]] = j
                j = self.L[j]
            i = self.U[i]
        self.R[self.L[c]] = c
        self.L[self.R[c]] = c

    def snapshot(self):
        return tuple(tuple(a) for a in (self.L, self.R, self.U, self.D, self.size))

    def solve(self):
        answers, path = [], []

        def search():
            if self.R[0] == 0:
                answers.append(tuple(path))
                return
            c, j = self.R[0], self.R[0]
            while j:
                if self.size[j] < self.size[c]:
                    c = j
                j = self.R[j]
            self.cover(c)
            r = self.D[c]
            while r != c:
                path.append(self.row[r])
                j = self.R[r]
                while j != r:
                    self.cover(self.C[j])
                    j = self.R[j]
                search()
                j = self.L[r]
                while j != r:
                    self.uncover(self.C[j])
                    j = self.L[j]
                path.pop()
                r = self.D[r]
            self.uncover(c)
        before = self.snapshot()
        search()
        assert self.snapshot() == before
        return answers


def brute(ncols, rows, primary):
    answers = set()
    for selected in product((0, 1), repeat=len(rows)):
        counts = [sum(use and c in row for use, row in zip(selected, rows)) for c in range(ncols)]
        if all(counts[c] == 1 for c in primary) and all(v <= 1 for v in counts):
            answers.add(tuple(i for i, use in enumerate(selected) if use))
    return answers


def verify():
    rng = Random(721)
    cases = 0
    for ncols in range(1, 6):
        for _ in range(40):
            primary = set(range(rng.randint(1, ncols)))
            options = [a for k in range(1, ncols + 1) for a in combinations(range(ncols), k)
                       if set(a) & primary]
            rows = [rng.choice(options) for _ in range(rng.randrange(9))]
            dlx = DLX(ncols, rows, primary)
            got = {tuple(sorted(a)) for a in dlx.solve()}
            assert got == brute(ncols, rows, primary)
            assert got == {tuple(sorted(a)) for a in dlx.solve()}
            cases += 1
    assert DLX(0, []).solve() == [()]
    rows = [(0, 1), (2, 3), (0, 2), (1, 3), (0,), (1, 2, 3)]
    assert {tuple(sorted(a)) for a in DLX(4, rows).solve()} == {(0, 1), (2, 3), (4, 5)}
    return {'random_exact_cover_cases': cases, 'state_restoration': 'verified twice per case'}


if __name__ == '__main__':
    print(verify())
