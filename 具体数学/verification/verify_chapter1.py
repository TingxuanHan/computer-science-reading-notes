"""Run the code printed in the three notes and check it independently."""

from collections import deque
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO
from itertools import product
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT = {"date": datetime.now(timezone(timedelta(hours=8))).date().isoformat(), "checks": []}


def load_note(prefix):
    paths = list((ROOT / "第01章-递归问题").glob(prefix + "-*.md"))
    assert len(paths) == 1
    path = paths[0]
    text = path.read_text(encoding="utf-8")
    namespace = {}
    output = StringIO()
    with redirect_stdout(output):
        for block in re.findall(r"```python\n(.*?)\n```", text, re.S):
            exec(compile(block, path.name, "exec"), namespace)
    REPORT["checks"].append({
        "note": path.name,
        "printed_code": "passed",
        "output": output.getvalue().strip(),
        "characters": len(text),
    })
    assert text.count("```") % 2 == 0
    assert sum(line.strip() == "$$" for line in text.splitlines()) % 2 == 0
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert "C:\\Users" not in text
    return namespace


def shortest_hanoi(n):
    # Disk 0 is the smallest; each tuple entry stores its peg.
    start = (0,) * n
    target = (2,) * n
    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        state, distance = queue.popleft()
        if state == target:
            return distance
        top = {}
        for disk, peg in enumerate(state):
            top.setdefault(peg, disk)
        for source, disk in top.items():
            for destination in range(3):
                if destination == source:
                    continue
                if destination in top and top[destination] < disk:
                    continue
                moved = list(state)
                moved[disk] = destination
                following = tuple(moved)
                if following not in visited:
                    visited.add(following)
                    queue.append((following, distance + 1))
    raise AssertionError("No solution")


hanoi = load_note("1.1.1")["hanoi"]
for n in range(9):
    pegs = {"A": list(range(n, 0, -1)), "B": [], "C": []}
    moves = list(hanoi(n))
    for disk, source, destination in moves:
        assert pegs[source] and pegs[source][-1] == disk
        assert not pegs[destination] or pegs[destination][-1] > disk
        pegs[destination].append(pegs[source].pop())
    assert pegs == {"A": [], "B": [], "C": list(range(n, 0, -1))}
    assert len(moves) == 2**n - 1
for n in range(7):
    assert shortest_hanoi(n) == 2**n - 1
REPORT["checks"].append({"hanoi": "legal moves n=0..8; independent shortest-path search n=0..6 passed"})

max_regions = load_note("1.1.2")["max_regions"]
regions = 1
for n in range(1, 31):
    # Explicit general-position family y = m*x + m*m.
    intersections = set()
    for previous in range(1, n):
        x = Fraction(previous * previous - n * n, n - previous)
        y = n * x + n * n
        intersections.add((x, y))
    assert len(intersections) == n - 1
    regions += len(intersections) + 1
    assert regions == max_regions(n)
assert max_regions(0) == 1
REPORT["checks"].append({"lines": "explicit general-position intersections and region increments n=0..30 passed"})

josephus = load_note("1.1.3")
simulate = josephus["josephus_simulation"]
formula = josephus["josephus_two"]
for n in range(1, 501):
    assert formula(n) == simulate(n)
    binary = bin(n)[2:]
    assert formula(n) == int(binary[1:] + binary[0], 2)
    value = n
    while formula(value) != value:
        value = formula(value)
    assert value == (1 << n.bit_count()) - 1
for q in range(1, 100):
    p = 1 << q
    assert formula(p) == 1
    assert formula(p - 1) == p - 1
    assert formula(p + 1) == 3
REPORT["checks"].append({"josephus": "simulation n=1..500, bit rotation, fixed points, and power-of-two boundaries q=1..99 passed"})

parameter_cases = 0
for alpha, beta, gamma in product((-3, 0, 1, 5), repeat=3):
    values = {1: alpha}
    for n in range(2, 201):
        values[n] = 2 * values[n // 2] + (gamma if n % 2 else beta)
    for n, value in values.items():
        p = 1 << (n.bit_length() - 1)
        remainder = n - p
        assert value == p * alpha + (p - 1 - remainder) * beta + remainder * gamma
    parameter_cases += 1
REPORT["checks"].append({"repertoire": f"{parameter_cases} parameter triples, n=1..200 passed"})

alpha = {1: 2, 2: 4}
beta = {0: 1, 1: -2, 2: 3}
def radix_recurrence(n):
    if n < 3:
        return alpha[n]
    quotient, remainder = divmod(n, 3)
    return 5 * radix_recurrence(quotient) + beta[remainder]

def radix_digits(n):
    digits = []
    while n:
        n, digit = divmod(n, 3)
        digits.append(digit)
    value = alpha[digits.pop()]
    for digit in reversed(digits):
        value = 5 * value + beta[digit]
    return value

for n in range(1, 501):
    assert radix_recurrence(n) == radix_digits(n)
assert radix_recurrence(19) == 103
REPORT["checks"].append({"radix": "recurrence versus digit evaluation n=1..500; f(19)=103 passed"})

REPORT["result"] = "passed"
out = ROOT / "verification" / "chapter1-report.json"
out.write_text(json.dumps(REPORT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(REPORT, ensure_ascii=False, indent=2))
