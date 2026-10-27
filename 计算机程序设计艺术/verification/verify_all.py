"""Verify the packaged notes, printed examples, and independent checks."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote, urlsplit
import argparse
import hashlib
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
REPO = BOOK.parent
TIMEOUT_SECONDS = 180


def python_blocks(text):
    return re.findall(r'^```python\s*\n(.*?)^```\s*$', text, re.M | re.S)


def verify_note(relative_path):
    path = BOOK / relative_path
    text = path.read_text(encoding='utf-8')
    namespace = {'__name__': '__main__'}
    output = StringIO()
    blocks = python_blocks(text)
    contextual_checks = {}
    with redirect_stdout(output):
        for index, code in enumerate(blocks, 1):
            if path.name.startswith('7.1.3-') and index == 1:
                # The prose introduces x and i before this single expression.
                expression = compile(code.strip(), f'{relative_path}:python-1', 'eval')
                for x in range(1 << 16):
                    bits = f'{x:016b}'[::-1]
                    for i in range(16):
                        assert eval(expression, {'x': x, 'i': i}) == int(bits[i])
                contextual_checks['bit_selection_cases'] = (1 << 16) * 16
                continue
            if path.name.startswith('7.1.3-') and index == 2:
                # Check the two-bit lanes after the first SWAR counting step.
                statement = compile(code, f'{relative_path}:python-2', 'exec')
                for x in range(1 << 16):
                    state = {'x': x}
                    exec(statement, state)
                    expected = sum(((x >> (2 * i)) & 3).bit_count() << (2 * i) for i in range(8))
                    assert state['x'] == expected
                contextual_checks['swar_first_step_inputs'] = 1 << 16
                continue
            exec(compile(code, f'{relative_path}:python-{index}', 'exec'), namespace)
    print(json.dumps({'path': relative_path, 'python_blocks': len(blocks),
                      'status': 'passed', 'code_status': 'passed' if blocks else 'not_applicable',
                      'contextual_checks': contextual_checks,
                      'output': output.getvalue().strip()}, ensure_ascii=False))


def verify_layout(catalog):
    seen_sections, seen_paths = set(), set()
    standalone_count = 0
    for note in catalog['notes']:
        assert note['section'] not in seen_sections
        assert note['path'] not in seen_paths
        seen_sections.add(note['section'])
        seen_paths.add(note['path'])
        path = BOOK / note['path']
        text = path.read_text(encoding='utf-8')
        assert hashlib.sha256(text.encode('utf-8')).hexdigest() == note['sha256'], note['path']
        assert text.splitlines()[0].removeprefix('# ') == note['title']
        assert len(python_blocks(text)) == note['python_blocks']
        assert text.count('```') % 2 == 0, note['path']
        assert text.count('$$') % 2 == 0, note['path']
        if 'standalone_example' in note:
            code = (BOOK / note['standalone_example']).read_text(encoding='utf-8').strip()
            assert code in text, note['path']
            standalone_count += 1
    assert len(seen_paths) == catalog['note_count'] == 51
    assert sum(n['python_blocks'] for n in catalog['notes']) == 61
    linked_files = 0
    for path in [REPO / 'README.md', *sorted(BOOK.rglob('*.md'))]:
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'^```.*?^```\s*$', '', text, flags=re.M | re.S)
        text = re.sub(r'\$\$.*?\$\$', '', text, flags=re.S)
        text = re.sub(r'(?<!\\)\$[^$\n]*\$', '', text)
        for link in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', text):
            destination = urlsplit(link.strip('<>'))
            if destination.scheme or destination.netloc or not destination.path:
                continue
            target = (path.parent / unquote(destination.path)).resolve()
            assert target.is_relative_to(REPO.resolve()), (str(path), link)
            assert target.exists(), (str(path), link)
            linked_files += 1
    return {'note_count': len(seen_paths), 'local_links_checked': linked_files,
            'standalone_examples_matched': standalone_count, 'note_hashes_match': True}


def run_process(arguments):
    started = perf_counter()
    try:
        process = subprocess.run([sys.executable, '-X', 'utf8', *arguments],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=TIMEOUT_SECONDS, cwd=BOOK)
        return process.returncode == 0, process.stdout, process.stderr, round(perf_counter() - started, 3)
    except subprocess.TimeoutExpired:
        return False, '', f'Exceeded {TIMEOUT_SECONDS} seconds', round(perf_counter() - started, 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--note', help='Internal single-note check, relative to the book folder')
    args = parser.parse_args()
    if args.note:
        verify_note(args.note)
        return 0

    catalog = json.loads((BOOK / 'catalog.json').read_text(encoding='utf-8'))
    layout = verify_layout(catalog)
    print(f"Layout: passed; notes: {layout['note_count']}; local links: {layout['local_links_checked']}", flush=True)
    results = []
    for note in catalog['notes']:
        passed, output, error, seconds = run_process([str(Path(__file__).resolve()), '--note', note['path']])
        result = {'section': note['section'], 'path': note['path'],
                  'status': 'passed' if passed else 'failed', 'seconds': seconds}
        if passed:
            result.update(json.loads(output))
        else:
            result.update(stdout=output, stderr=error)
        results.append(result)
        print(f"Note {note['section']}: {result['status']}", flush=True)

    scripts = [f'verify_taocp_chapter{i}.py' for i in range(1, 8)]
    scripts += ['verify_taocp_7_1_1.py', 'verify_taocp_7_1_remaining.py', 'verify_taocp_mpr.py']
    extended = []
    for name in scripts:
        passed, output, error, seconds = run_process([str(HERE / name)])
        result = {'script': name, 'status': 'passed' if passed else 'failed', 'seconds': seconds}
        if not passed:
            result.update(stdout=output, stderr=error)
        extended.append(result)
        print(f"Extended {name}: {result['status']}", flush=True)
        if not passed:
            print(error, file=sys.stderr)

    all_passed = all(r['status'] == 'passed' for r in results + extended)
    summary = {'verified_at': datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
        'timezone': 'Asia/Shanghai', 'python_version': sys.version.split()[0], 'all_passed': all_passed,
        'note_count': len(results), 'python_blocks': sum(n['python_blocks'] for n in catalog['notes']),
        'layout': layout, 'notes': results, 'extended_checks': extended,
        'limitations': 'Finite checks reproduce examples and detect errors; they do not replace mathematical proofs.'}
    (HERE / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"All passed: {all_passed}; notes: {len(results)}; Python blocks: {summary['python_blocks']}", flush=True)
    return 0 if all_passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
