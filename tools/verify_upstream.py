"""Verify the included original benchmark files against the download manifest."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    entries = json.loads((root / 'upstream' / 'source_manifest.json').read_text(encoding='utf-8-sig'))
    failures = []
    for entry in entries:
        path = root / entry['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != entry['original_sha256'].lower():
            failures.append(entry['path'])
    if failures:
        print('Original files changed or missing:')
        for name in failures:
            print('  ' + name)
        raise SystemExit(1)
    print(f'PASS: all {len(entries)} original benchmark files are unchanged.')


if __name__ == '__main__':
    main()
