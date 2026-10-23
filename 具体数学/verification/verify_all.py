"""Run the existing chapter checks with the current Python interpreter."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import subprocess
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent


def main():
    results = []
    for chapter in range(1, 10):
        script = HERE / f"verify_chapter{chapter}.py"
        started = perf_counter()
        process = subprocess.run(
            [sys.executable, "-X", "utf8", str(script)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        passed = process.returncode == 0
        results.append({
            "chapter": chapter,
            "result": "passed" if passed else "failed",
            "seconds": round(perf_counter() - started, 3),
        })
        print(f"Chapter {chapter}: {results[-1]['result']} ({results[-1]['seconds']}s)", flush=True)
        if not passed:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
    all_passed = all(item["result"] == "passed" for item in results)
    summary = {
        "verified_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "python_version": sys.version.split()[0],
        "note_count": len(list(HERE.parent.glob("第*章-*/*.1.*.md"))),
        "all_passed": all_passed,
        "chapters": results,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"All passed: {all_passed}; notes: {summary['note_count']}", flush=True)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
