from itertools import combinations, product
from random import Random


def satisfies(clauses, model):
    return all(any(model[abs(lit)] == (lit > 0) for lit in clause) for clause in clauses)


def dpll(raw):
    raw = [tuple(c) for c in raw]
    if any(lit == 0 for c in raw for lit in c):
        raise ValueError('literal 0 is not allowed')
    variables = {abs(lit) for c in raw for lit in c}
    clauses = []
    for c in raw:
        c = frozenset(c)
        if not any(-lit in c for lit in c):
            clauses.append(c)           # tautologies can be discarded

    def assign(formula, literal):
        return [c - {-literal} for c in formula if literal not in c]

    def search(formula, model):
        while True:
            if any(not c for c in formula):
                return None
            if not formula:
                return model
            unit = next((next(iter(c)) for c in formula if len(c) == 1), None)
            if unit is None:
                break
            variable, value = abs(unit), unit > 0
            if variable in model and model[variable] != value:
                return None
            model = model | {variable: value}
            formula = assign(formula, unit)
        clause = min(formula, key=lambda c: (len(c), tuple(sorted(c))))
        literal = min(clause, key=lambda x: (abs(x), x < 0))
        for choice in (literal, -literal):
            result = search(assign(formula, choice), model | {abs(choice): choice > 0})
            if result is not None:
                return result
        return None

    result = search(clauses, {})
    if result is not None:
        result = {v: result.get(v, False) for v in variables}
        assert satisfies(raw, result)
    return result


def exactly_one(literals):
    literals = tuple(literals)
    return [literals] + [(-a, -b) for a, b in combinations(literals, 2)]


def coloring_cnf(vertices, edges, colors):
    def variable(v, color):
        return v * colors + color + 1
    clauses = []
    for v in range(vertices):
        clauses.extend(exactly_one(variable(v, c) for c in range(colors)))
    for u, v in edges:
        for c in range(colors):
            clauses.append((-variable(u, c), -variable(v, c)))
    return clauses


def brute(clauses):
    variables = sorted({abs(lit) for c in clauses for lit in c})
    for values in product((False, True), repeat=len(variables)):
        model = dict(zip(variables, values))
        if satisfies(clauses, model):
            return model
    return None


def verify():
    atoms = [tuple(sign * (i + 1) for i, sign in enumerate(signs) if sign)
             for signs in product((-1, 0, 1), repeat=3)]
    checked = 0
    for size in range(4):
        for formula in combinations(atoms, size):
            got = dpll(formula)
            assert (got is None) == (brute(formula) is None)
            if got is not None:
                assert satisfies(formula, got)
            checked += 1
    rng = Random(7222)
    for _ in range(200):
        formula = [tuple(rng.choice((-1, 1)) * rng.randint(1, 6) for _ in range(rng.randint(0, 5)))
                   for _ in range(rng.randint(0, 12))]
        assert (dpll(formula) is None) == (brute(formula) is None)
    triangle = [(0, 1), (1, 2), (2, 0)]
    assert dpll(coloring_cnf(3, triangle, 2)) is None
    assert dpll(coloring_cnf(3, triangle, 3)) is not None
    assert dpll([]) == {} and dpll([()]) is None
    assert dpll([(1, -1)]) is not None
    and_gate = [(-3, 1), (-3, 2), (3, -1, -2)]
    for a, b, z in product((False, True), repeat=3):
        assert satisfies(and_gate, {1: a, 2: b, 3: z}) == (z == (a and b))
    return {'exhaustive_cnf_instances': checked, 'random_cnf_instances': 200,
            'encoding_tests': ['triangle coloring', 'AND gate', 'empty cases']}


if __name__ == '__main__':
    print(verify())
