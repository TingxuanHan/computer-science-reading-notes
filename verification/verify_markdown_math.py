"""Audit both books' formulas, optionally including GitHub's Markdown API.

The API renders text without modifying a repository. It uses the user's local
gh login. Cached HTML stays in the ignored .math-cache directory.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BOOKS = ('具体数学', '计算机程序设计艺术')
CONTEXT = 'TingxuanHan/computer-science-reading-notes'
# Observed in GitHub's math-renderer asset on 2026-10-28. This is a platform
# compatibility list, not a claim that these commands are invalid LaTeX.
BLOCKED = ('DeclareMathOperator', 'DeclarePairedDelimiters', 'renewtagform',
    'newtagform', 'colorbox', 'fcolorbox', 'hphantom', 'vphantom', 'phantom',
    'operatorname', 'Newextarrow', 'definecolor', 'mathchoice', 'unicode', 'mmlToken')
TOKEN = re.compile(
    r'(?P<fence>^(?P<ticks>`{3,}|~{3,})(?P<lang>[^\n]*)\n(?P<body>.*?)^(?P=ticks)[ \t]*$)'
    r'|(?P<display>(?<!\\)\$\$(?P<display_tex>.*?)\$\$)'
    r'|(?P<protected>\$`(?P<protected_tex>[^`\n]+)`\$)'
    r'|(?P<code>(?P<backticks>`+)(?!`)[^\n]*?(?P=backticks)(?!`))'
    r'|(?P<inline>(?<![\\$])\$(?![\s$])(?P<inline_tex>(?:\\.|[^$\n])+?)(?<!\\)\$(?!\$))',
    re.M | re.S)


@dataclass
class Formula:
    start: int
    end: int
    tex: str
    display: bool
    protected: bool
    line: int


def formulas(text):
    items = []
    for match in TOKEN.finditer(text):
        if match.group('fence') is not None:
            if match.group('lang').strip() != 'math':
                continue
            tex, display, protected = match.group('body').strip(), True, True
        elif match.group('display') is not None:
            tex, display, protected = match.group('display_tex').strip(), True, False
        elif match.group('protected') is not None:
            tex, display, protected = match.group('protected_tex'), False, True
        elif match.group('inline') is not None:
            tex, display, protected = match.group('inline_tex'), False, False
        else:
            continue
        items.append(Formula(match.start(), match.end(), tex, display, protected,
                             text.count('\n', 0, match.start()) + 1))
    return items


def normalize(tex):
    return re.sub(r'\s+', '', tex)


def github_compatible_math(text, indices=None):
    """Protect selected expressions from Markdown and keep operator spacing.

    With no selection, normalize every formula when importing new notes.
    Existing code blocks and inline code are left byte-for-byte unchanged.
    """
    items = formulas(text)
    for index in reversed(range(len(items))):
        if indices is not None and index not in indices:
            continue
        formula = items[index]
        tex = re.sub(r'\\operatorname\{([^{}]+)\}',
            lambda m: r'\mathop{\mathrm{' + m[1] + r'}}\nolimits ', formula.tex)
        tex = re.sub(r'\\nolimits(?=[A-Za-z])', lambda _: r'\nolimits ', tex)
        # The live renderer reparses its text as HTML. Explicit math commands
        # cannot be mistaken for an opening HTML tag, even before a letter.
        tex = tex.replace('<', r'\lt ')
        if formula.display:
            # GitHub's GFM API appends a backslash to an escaped line ending,
            # even in a math fence. Keep the row break explicit.
            tex = re.sub(r'(?<!\\)(\\{1,2})\n',
                lambda m: r'\\[0pt]' + '\n' if len(m[1]) == 2 else '\\ ', tex)
        replacement = '```math\n' + tex + '\n```' if formula.display else '$`' + tex + '`$'
        text = text[:formula.start] + replacement + text[formula.end:]
    return text


class ClientText(HTMLParser):
    """Match the renderer's createHTMLDocument(...).body.textContent step."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class MathHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'math-renderer':
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'math-renderer' and self.current is not None:
            # GitHub parses the text as HTML again before tex2mml. A raw '<'
            # followed by a letter can be swallowed as an HTML tag here.
            decoded = ClientText()
            decoded.feed('<html><body>' + ''.join(self.current) + '</body></html>')
            decoded.close()
            text = ''.join(decoded.parts).strip()
            text = re.sub(r'^\${1,2}|\${1,2}$', '', text).strip()
            self.items.append(text)
            self.current = None


def github_render(text):
    digest = hashlib.sha256((CONTEXT + '\n' + text).encode()).hexdigest()
    cache = HERE / '.math-cache' / (digest + '.html')
    if cache.exists():
        html = cache.read_text(encoding='utf-8')
    else:
        payload = json.dumps({'text': text, 'mode': 'gfm', 'context': CONTEXT})
        process = subprocess.run(['gh', 'api', 'markdown', '--input', '-'],
            input=payload.encode(), capture_output=True, timeout=90)
        if process.returncode:
            raise RuntimeError(process.stderr.decode('utf-8', 'replace')[:1500])
        html = process.stdout.decode('utf-8')
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(html, encoding='utf-8')
    parsed = MathHTML()
    parsed.feed(html)
    return parsed.items


def note_paths():
    return [path for book in BOOKS for path in sorted((REPO / book).rglob('*.md'))]


def audit(use_github=False, output=None):
    records, all_formulas = [], []
    for path in note_paths():
        text = path.read_text(encoding='utf-8')
        items = formulas(text)
        relative = path.relative_to(REPO).as_posix()
        record = {'path': relative, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
                  'formula_count': len(items), 'issues': []}
        if '$' in TOKEN.sub('', text):
            record['issues'].append({'kind': 'unparsed_dollar',
                'message': 'A dollar sign outside code was not recognized as a complete formula.'})
        if sum(f.tex.count('{') + 1 for f in items) > 2000:
            record['issues'].append({'kind': 'github_complexity_limit'})
        for index, formula in enumerate(items):
            ident = f'{relative}:{index}'
            all_formulas.append({'id': ident, 'tex': formula.tex, 'display': formula.display})
            blocked = [name for name in BLOCKED if '\\' + name in formula.tex]
            if blocked:
                record['issues'].append({'index': index, 'line': formula.line,
                    'kind': 'blocked_macro', 'macros': blocked})
        record['_text'], record['_formulas'] = text, items
        records.append(record)

    process = subprocess.run(['node', str(HERE / 'check_mathjax.cjs')],
        input=json.dumps(all_formulas).encode(), capture_output=True, timeout=180)
    if process.returncode:
        raise RuntimeError(process.stderr.decode('utf-8', 'replace')[:2000])
    checked = json.loads(process.stdout)
    by_path = {r['path']: r for r in records}
    for result in checked['results']:
        if result['status'] == 'failed':
            path, index = result['id'].rsplit(':', 1)
            record = by_path[path]
            record['issues'].append({'index': int(index),
                'line': record['_formulas'][int(index)].line,
                'kind': 'tex_parse', 'error': result['error']})

    if use_github:
        def check(record):
            try:
                actual = github_render(record['_text'])
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                record['issues'].append({'kind': 'github_request_failed',
                    'message': str(error)[:1500]})
                print(f"GitHub {record['path']}: request failed; rerun to retry", flush=True)
                return
            expected = record['_formulas']
            if len(actual) != len(expected):
                record['issues'].append({'kind': 'formula_count',
                    'expected': len(expected), 'actual': len(actual)})
            alignment = SequenceMatcher(a=[normalize(f.tex) for f in expected],
                                        b=[normalize(t) for t in actual], autojunk=False)
            for tag, start, end, other_start, other_end in alignment.get_opcodes():
                if tag == 'equal':
                    continue
                if tag == 'insert':
                    record['issues'].append({'kind': 'unexpected_formula',
                        'rendered': actual[other_start:other_end]})
                    continue
                for index in range(start, end):
                    formula = expected[index]
                    record['issues'].append({'index': index, 'line': formula.line,
                        'kind': 'formula_missing' if tag == 'delete' else 'markdown_changed_tex',
                        'source': formula.tex, 'rendered': actual[other_start:other_end]})
            record['github_formula_count'] = len(actual)
            print(f"GitHub {record['path']}: {len(actual)} formulas; {len(record['issues'])} issues", flush=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(check, records))

    for record in records:
        del record['_text'], record['_formulas']
    report = {'checked_at': datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
        'timezone': 'Asia/Shanghai',
        'github_renderer_asset': 'https://github.githubassets.com/assets/chunk-lazy-element-math-renderer-d9906def89b0b710.js',
        'github_mathjax_asset': 'https://github.githubassets.com/assets/chunk-52e-0bb288a2e09ef5ab.js',
        'mathjax_version': checked['version'], 'github_markdown_checked': use_github,
        'github_client_html_decode_checked': use_github,
        'markdown_files': len(records), 'formulas': len(all_formulas),
        'issues': sum(len(r['issues']) for r in records),
        'all_passed': all(not r['issues'] for r in records), 'files': records,
        'limitations': 'Checks rendering syntax and Markdown preservation, not the validity of every mathematical proof.'}
    if output:
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--github', action='store_true', help='Check complete documents through the GitHub Markdown API')
    parser.add_argument('--output', type=Path, default=HERE / 'math-report.json')
    args = parser.parse_args()
    raise SystemExit(0 if audit(args.github, args.output)['all_passed'] else 1)
