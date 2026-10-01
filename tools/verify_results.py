"""Check that the included evidence matches this adapter and its saved plans.

This is an offline development utility, outside the competition adapter.
It does not rerun the timed benchmark or predict hidden-case performance.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'bench-warehouse'))
import _paths  # noqa: F401
import data
import validator


def main():
    report = json.loads((ROOT / 'benchmarks' / 'public_report.json').read_text())
    adapter = ROOT / 'bench-warehouse' / 'adapters' / 'myteam.py'
    current_hash = hashlib.sha256(adapter.read_bytes()).hexdigest()
    if current_hash != report['adapter_sha256']:
        raise SystemExit('Adapter changed: the included performance report no longer matches it.')
    records = {item['instance']: item for item in report['records']}
    checked = 0
    for item in data.public_instances():
        record = records[item.name]
        plan = report['plans'][item.name]
        cost, reason = validator.evaluate(item, plan)
        if reason is not None or cost != record['final_cost']:
            raise SystemExit(f'{item.name}: saved plan/report mismatch: {cost}, {reason}')
        checked += 1
    print(f'PASS: adapter hash matches; all {checked} saved plans are valid and match exact report costs.')


if __name__ == '__main__':
    main()
