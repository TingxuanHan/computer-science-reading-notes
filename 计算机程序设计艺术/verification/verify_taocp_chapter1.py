from pathlib import Path
import contextlib
import hashlib
import io
import itertools
import json
import math
import re
from collections import Counter
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]
NOTE_DIR = ROOT / '第1卷-基本算法/第01章-基本概念'
FILES = [
    "1.1-算法.md", "1.2-数学准备.md", "1.3-MIX.md",
    "1.4-某些基本程序设计技术.md",
]
report = {"source": "TAOCP Volume 1, third edition, supplied 2002 Chinese PDF",
          "articles": [], "checks": {}}
spaces = []
for filename in FILES:
    source = (NOTE_DIR / filename).read_text(encoding="utf-8")
    title, body = source.split("\n", 1)
    body = body.lstrip("\n").rstrip() + "\n"
    blocks = re.findall(r"```python\n(.*?)\n```", source, flags=re.S)
    env = {}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        for index, block in enumerate(blocks):
            exec(compile(block, f"{filename}:python-{index + 1}", "exec"), env)
    spaces.append(env)
    assert source.count("```") % 2 == 0
    assert source.count("$$") % 2 == 0
    assert "TODO" not in source
    report["articles"].append({
        "filename": filename, "title": title.removeprefix("# "),
        "body_characters": len(body), "python_blocks": len(blocks),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "example_output": output.getvalue().strip(),
    })

# Euclid: independent library reference, per-step invariants, invalid inputs.
euclid = spaces[0]["euclid_trace"]
for m in range(1, 129):
    for n in range(1, 129):
        answer, rows = euclid(m, n)
        assert answer == math.gcd(m, n)
        for a, b, q, r in rows:
            assert a == q * b + r and 0 <= r < b
            assert math.gcd(a, b) == answer
for args, error in [((0, 1), ValueError), ((1, 0), ValueError),
                    ((-1, 2), ValueError), ((1.5, 2), TypeError),
                    ((True, 2), TypeError), (("1", 2), TypeError)]:
    try:
        euclid(*args)
    except error:
        pass
    else:
        raise AssertionError(args)
report["checks"]["euclid"] = {"positive_pairs": 16384, "invalid_inputs": 6}

# Maximum: exact whole distribution against the generating-function recurrence.
maximum = spaces[1]["maximum_with_count"]
poly = [Fraction(1)]
permutation_count = 0
for n in range(1, 8):
    if n > 1:
        nxt = [Fraction(0)] * n
        for k, coefficient in enumerate(poly):
            nxt[k] += Fraction(n - 1, n) * coefficient
            nxt[k + 1] += Fraction(1, n) * coefficient
        poly = nxt
    distribution = Counter()
    for p in itertools.permutations(range(n)):
        value, position, updates = maximum(p)
        assert value == n - 1 and p[position] == n - 1
        distribution[updates] += 1
        permutation_count += 1
    assert [Fraction(distribution[k], math.factorial(n)) for k in range(n)] == poly
duplicate_count = 0
for n in range(1, 7):
    for xs in itertools.product(range(3), repeat=n):
        m, j, _ = maximum(xs)
        assert m == max(xs)
        assert j == max(k for k, x in enumerate(xs) if x == m)
        duplicate_count += 1
report["checks"]["maximum"] = {"permutations": permutation_count,
    "duplicate_value_arrays": duplicate_count, "exact_distribution_mean_variance": True}

# Field semantics: arithmetic extraction provides an independent load oracle.
load = spaces[2]["load_field"]
store = spaces[2]["store_field"]
field_count = 0
for base in (64, 100):
    for sign in (-1, 1):
        for digits in ((1, 2, 3, 4, 5), (base-1,) * 5, (0,) * 5):
            magnitude = sum(d * base ** (4-i) for i, d in enumerate(digits))
            word = (sign, digits)
            register = (-sign, (9, 8, 7, 6, 5))
            for left in range(6):
                for right in range(left, 6):
                    count = right - max(1, left) + 1
                    expected_value = (magnitude // base ** (5-right)) % base ** count
                    loaded_sign, loaded_digits = load(word, left, right)
                    loaded_value = sum(d * base ** (4-i) for i, d in enumerate(loaded_digits))
                    assert loaded_value == expected_value
                    assert loaded_sign == (sign if left == 0 else 1)
                    saved_sign, saved_digits = store(word, register, left, right)
                    assert saved_sign == (register[0] if left == 0 else sign)
                    for pos in range(1, 6):
                        if max(1, left) <= pos <= right:
                            assert saved_digits[pos-1] == register[1][5-count+pos-max(1,left)]
                        else:
                            assert saved_digits[pos-1] == digits[pos-1]
                    field_count += 1
report["checks"]["mix_fields"] = {"word_field_cases": field_count,
    "bases": [64, 100], "negative_zero_preserved": load((-1,(0,)*5),0,0)[0] == -1}

# Parse and execute ONLY the instructions used in the article's own MIXAL example.
# This is a restricted semantic check, not a complete MIX assembler/emulator.
source = (NOTE_DIR / FILES[2]).read_text(encoding="utf-8")
assembly = next(b for b in re.findall(r"```text\n(.*?)\n```", source, re.S)
                if b.startswith("N       EQU"))
labels, statements = {}, []
location = 0
def expr(text):
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if "-" in text:
        head, tail = text.split("-", 1)
        return labels[head] - int(tail)
    return labels[text]
for line in assembly.splitlines():
    fields = line.split()
    if line[0].isspace():
        label = None
    else:
        label = fields.pop(0)
    op = fields.pop(0)
    arg = fields[0] if fields else ""
    if op == "EQU":
        labels[label] = expr(arg)
    elif op == "ORIG":
        location = expr(arg)
        if label:
            labels[label] = location
    elif op == "END":
        entry = expr(arg)
    else:
        if label:
            labels[label] = location
        statements.append((location, op, arg))
        location += 1
memory = {p: expr(a) for p, op, a in statements if op == "CON"}
code = {p: (op, a) for p, op, a in statements if op != "CON"}
pc, accumulator, index1, instructions, addresses = entry, 0, 0, 0, []
while True:
    op, arg = code[pc]
    pc += 1
    instructions += 1
    if op == "ENTA": accumulator = expr(arg)
    elif op == "ENT1": index1 = expr(arg)
    elif op == "ADD":
        address, index = arg.split(",")
        assert index == "1"
        address = expr(address) + index1
        addresses.append(address)
        accumulator += memory[address]
    elif op == "DEC1": index1 -= expr(arg)
    elif op == "J1P":
        if index1 > 0: pc = expr(arg)
    elif op == "STA": memory[expr(arg)] = accumulator
    elif op == "HLT": break
    else: raise AssertionError(op)
    assert instructions < 100
assert memory[labels["SUM"]] == 14 and instructions == 19
assert addresses == [1004, 1003, 1002, 1001, 1000]
report["checks"]["mixal_example"] = {"method": "restricted instruction semantic interpreter",
    "result": 14, "executed_instructions": instructions, "effective_addresses": addresses,
    "full_mix_emulator_used": False}

gather = spaces[2]["gather_by_cycles"]
cycle_count = 0
for n in range(8):
    values = list(range(n))
    for p in itertools.permutations(range(n)):
        assert gather(values, p) == [values[i] for i in p]
        cycle_count += 1
report["checks"]["permutation_cycles"] = {"permutations_including_empty": cycle_count}

parse = spaces[3]["integers_from_chunks"]
totals = spaces[3]["running_totals"]
text = "12 3 45 -2"
partition_count = 0
for mask in range(1 << (len(text)-1)):
    parts, start = [], 0
    for i in range(1, len(text)):
        if mask & (1 << (i-1)):
            parts.append(text[start:i]); start = i
    parts.append(text[start:])
    assert list(parse(parts)) == [12, 3, 45, -2]
    assert list(totals(parse(parts))) == [12, 15, 60, 58]
    partition_count += 1
assert list(parse(["", " ", "\t"])) == []
run = spaces[3]["run_stack_program"]
vm_count = 0
for a, b, c in itertools.product(range(-3,4), repeat=3):
    p = [("PUSH",a),("PUSH",b),("ADD",None),("PUSH",c),("MUL",None),("HALT",None)]
    result, trace = run(p)
    assert result == (a+b)*c and trace[2] == (2,"ADD",(a,b))
    vm_count += 1
invalid_programs = [[], [("ADD",None)], [("HALT",None)], [("WHAT",None)],
                    [("PUSH",1)], [("PUSH",True),("HALT",None)],
                    [("PUSH",1),("PUSH",2),("HALT",None)]]
for p in invalid_programs:
    try: run(p)
    except ValueError: pass
    else: raise AssertionError(p)
timing_count = 0
for blocks, read_time, compute_time in itertools.product(range(1,21), range(1,11), range(1,11)):
    input_end, compute_end = 0, 0
    buffer_free = [0,0]
    for k in range(blocks):
        buffer = k % 2
        input_end = max(input_end, buffer_free[buffer]) + read_time
        compute_end = max(compute_end, input_end) + compute_time
        buffer_free[buffer] = compute_end
    assert compute_end == read_time + compute_time + (blocks-1)*max(read_time,compute_time)
    timing_count += 1
report["checks"]["program_organization"] = {"all_chunk_partitions": partition_count,
    "stack_programs": vm_count, "invalid_stack_programs": len(invalid_programs),
    "double_buffer_schedules": timing_count}
report["all_passed"] = True
path = ROOT / "verification" / "taocp-chapter1-report.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))

report['all_passed'] = True
(ROOT / 'verification/taocp-chapter1-report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Chapter 1: passed')
