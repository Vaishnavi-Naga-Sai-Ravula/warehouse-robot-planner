"""Use the original evaluator and scoring, retaining exact costs and demo paths.

This host-side utility is not the submitted adapter. No benchmark module is
modified. The regular bench-warehouse/run.py remains available unchanged.
"""
import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'bench-warehouse'))
import _paths  # noqa: F401
import data
import harness
import metrics
from adapters.myteam import Planner
from benchkit.runner import scored_output_stability


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='benchmarks/local_detailed_report.json')
    args = parser.parse_args()
    anchors = metrics.load_anchors(str(ROOT / 'bench-warehouse' / 'public_reference.json'))
    instances = data.public_instances()
    records, plans = [], {}
    for item in instances:
        budget = data.budget_for(item)
        print(f'Running {item.name}: {item.n_robots} robots, {budget:.2f}s', flush=True)
        planner = Planner()
        # The original harness creates the solver before starting the clock.
        # This factory simply returns the same new object so its final plan
        # can be retained after the run; the submitted adapter is unchanged.
        record = harness.run_one(item, lambda: planner, budget_s=budget, capture_detail=True)
        records.append(record)
        plans[item.name] = getattr(planner, 'best', None)
        reference = anchors[item.name]['reference_cost_units']
        print(f'  final={record.final_cost}; reference={reference}; '
              f'first valid={record.sink.get("first_valid_at_s")}; '
              f'within budget={record.within_budget}', flush=True)
    print(f'Replay check on {instances[0].name}', flush=True)
    # Exactly the same two runs and comparison used by check_determinism;
    # retaining their raw records makes checkpoint timing differences visible.
    replay_first = harness.run_one(instances[0], Planner)
    replay_second = harness.run_one(instances[0], Planner)
    stable, replay_detail = scored_output_stability(replay_first, replay_second)
    result = metrics.score_suite(records, anchors, deterministic=stable)
    adapter_path = ROOT / 'bench-warehouse' / 'adapters' / 'myteam.py'
    report = {
        'benchmark': 'warehouse-robot-planner', 'adapter': 'adapters.myteam:Planner',
        'adapter_sha256': hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
        'tested_on': '2026-10-01', 'budget_scale': 1.0,
        'environment': {'python': platform.python_version(),
                        'implementation': platform.python_implementation(),
                        'platform': platform.platform(),
                        'generated_at': datetime.now(timezone.utc).isoformat()},
        'generator_schema': data.SCHEMA_VERSION,
        'method': 'Original unmodified harness.run_one and metrics.score_suite, '
                  'normal budgets, default first-instance replay; additional raw records and paths.',
        'result': result, 'records': [asdict(record) for record in records],
        'replay': {'stable': stable, 'first_stream': replay_first.stream_digest,
                   'second_stream': replay_second.stream_digest,
                   'comparison': replay_detail,
                   'first_record': asdict(replay_first),
                   'second_record': asdict(replay_second)},
        'plans': plans,
        'notice': 'Local public practice estimate, not official hidden judging or an optimality proof.'
    }
    destination = ROOT / args.out
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(metrics.format_summary(result), flush=True)
    print(f'Points: {result["points"]}; replay stable={stable}', flush=True)
    print(f'Saved {destination}', flush=True)


if __name__ == '__main__':
    main()
