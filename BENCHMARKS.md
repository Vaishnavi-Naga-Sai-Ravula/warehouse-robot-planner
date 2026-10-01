# Benchmarks: targets and actual measured results

The delivered adapter produced valid plans on **9/9** public cases, reached the published final baseline on **9/9**, and matched or beat the organizer final reference on **6/9**. It reached the reference at all four scoring checkpoints on **0/9** cases.

Its measured public practice score was **58.467/100**. The default first-instance replay check was **stable**. These are measurements of this exact file on the included public suite; they do not establish hidden-case performance or global optimality.

## Exact final costs

All costs below are authoritative integer units. Divide by 1,000,000 for the displayed decimal cost. A smaller number is better; a reference target is reached only when our cost is no larger than its exact integer value.

| Public case | Robots | Budget (s) | First valid (s) | Baseline | Reference target | Our final cost | Reference reached? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| w01-aisles-small | 50 | 8.17 | 0.031 | 934500 | 915323 | 918388 | no |
| w02-maze | 60 | 9.00 | 0.0168 | 996555 | 978191 | 971588 | yes |
| w03-open-packed | 110 | 13.17 | 0.0973 | 926515 | 917716 | 919202 | no |
| w04-open-opposing | 100 | 12.33 | 0.6958 | 970188 | 952885 | 938206 | yes |
| w05-mixed-packed | 100 | 12.33 | 1.6377 | 1125654 | 967061 | 939320 | yes |
| w06-maze-irregular | 80 | 10.67 | 0.0479 | 1029606 | 1005172 | 1001781 | yes |
| w07-maze-irregular-b | 80 | 10.67 | 0.0335 | 1001848 | 993046 | 982692 | yes |
| w08-aisles-xl | 210 | 21.50 | 0.4651 | 989951 | 952300 | 960588 | no |
| w09-open-xxl | 280 | 27.33 | 1.3776 | 960270 | 932607 | 925535 | yes |

## Timing matters as much as the final plan

The checkpoints occur at 1%, 10%, 50%, and 100% of each case budget, with weights 30%, 30%, 20%, and 20%. A plan must finish independent validation before the checkpoint to count. There is no scored deadline grace. Missing the first checkpoint loses up to 30% of that instance score even if the final plan beats the reference.

| Case | Cost at 1% | Cost at 10% | Cost at 50% | Cost at 100% | Weighted instance score |
|---|---:|---:|---:|---:|---:|
| w01-aisles-small | 940718 | 926007 | 919176 | 918388 | 0.5226 |
| w02-maze | 990073 | 977285 | 971588 | 971588 | 0.8544 |
| w03-open-packed | 959713 | 928655 | 920005 | 919202 | 0.3559 |
| w04-open-opposing | missing | 947187 | 940584 | 938206 | 0.7000 |
| w05-mixed-packed | missing | missing | 945919 | 939320 | 0.4000 |
| w06-maze-irregular | 1080126 | 1016129 | 1006316 | 1001781 | 0.5921 |
| w07-maze-irregular-b | 995191 | 993860 | 985872 | 982692 | 0.9244 |
| w08-aisles-xl | missing | 992636 | 987468 | 960588 | 0.2858 |
| w09-open-xxl | missing | 942618 | 928860 | 925535 | 0.6186 |

## How the score is calculated

For a valid checkpoint cost `c`, baseline `B`, and reference `R`:

```text
checkpoint_score = clip(0.25 + 0.75 * (B - c) / (B - R), 0, 1)
```

The baseline gives 0.25 and the reference gives 1.00. A missing candidate gives 0. This repository does not specify a universal pass mark. The reference anchors were generated using the best of a prioritized planner and an LNS planner at **15 times the contestant budget**.

The quality component uses the mean instance score (70 points); robustness uses the mean shifted-instance score (30 points). A family whose mean is below 0.25 halves the robustness component. A whole family with no valid output halves both components. The result is multiplied by `0.7 + 0.3 * engineering_score`.

Engineering score combines replay stability (40%), fraction of accepted candidates (30%), preserving the input instance (20%), and staying within the budget (10%). The replay compares exact checkpoint-cost arrays and final cost. A fixed random seed alone does not guarantee this when work is bounded by wall-clock time.

- Quality mean: 0.5838
- Robustness mean: 0.5868
- Engineering score: 1.0; multiplier: 1.0000
- Shifted cases: 6
- Family below-baseline penalty: False
- Families with no valid output: []
- Accepted/rejected candidates: 266/0
- All runs within budget: True
- All instances preserved: True

## Evidence and reproduction

[public_report.json](benchmarks/public_report.json) contains raw integer checkpoint and final costs, objective components, candidate counts, first-valid timestamps, replay evidence, saved paths, environment details, and the adapter SHA-256.

Adapter SHA-256: `08a5abe9c16626d713552a75d1ce0f29d790695b668dd90cd326dbdeb5b0cfa9`.

The report was produced with the original, unchanged `harness.run_one`, validator, and `metrics.score_suite`, using normal budgets and the default first-case replay. The additional host-side utility only retains the raw records and plans. It is outside the submitted adapter.

Run the ordinary unchanged CLI from `bench-warehouse/`:

```text
python self_check.py --adapter adapters.myteam:Planner
python run.py --adapter adapters.myteam:Planner --out ../benchmarks/local_report.json
```

Or reproduce the report with raw costs and saved plans from the project root:

```text
python tools/benchmark_with_plans.py --out benchmarks/local_detailed_report.json
python tools/verify_upstream.py
```

Runtime and early checkpoint costs can vary with CPU load, interpreter, machine, and operating system. Run without a debugger and avoid concurrent heavy work. The report is evidence from one full local run plus the original two-run replay check, rather than a statistical performance guarantee.

## What remains to improve

A reference miss in the table is an unmet target. A final reference match does not recover earlier missed checkpoints. Reaching 100/100 would require sufficiently good plans at every checkpoint, clean engineering results, and no family penalties. The delivered method is incomplete prioritized planning with local repair; some unseen feasible problems may defeat it.

Useful next experiments are faster first-plan construction, improved parking priorities, more coordinated repairs for dense bottlenecks, and held-out repeated-run comparisons. Any changes require rerunning the unchanged benchmark and reporting the new file hash. Never edit targets, clocks, the validator, or scoring state to improve a reported result.

Sources: [original problem and rules](https://github.com/Vaishnavi-Naga-Sai-Ravula/PHASE_2/blob/main/warehouse-robot-planner/bench-warehouse/README.md), [public reference anchors](https://github.com/Vaishnavi-Naga-Sai-Ravula/PHASE_2/blob/main/warehouse-robot-planner/bench-warehouse/public_reference.json), and the included unchanged `benchkit/` implementation.
