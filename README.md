# Warehouse Robot Planner

A complete development and presentation folder for the PHASE_2 warehouse
robot planning problem. The planner produces collision-free paths and improves
them within the supplied time budget. It uses classical AI search and local
optimization; it does not train a neural network.

**Begin with [START_HERE.md](START_HERE.md).** Open this entire folder in VS Code.

- [Exact benchmark targets and measured results](BENCHMARKS.md)
- [Beginner algorithm explanation](docs/FOUNDATIONS.md)
- [A small worked example](docs/WORKED_EXAMPLE.md)
- [Actual code walkthrough](docs/CODE_WALKTHROUGH.md)
- [Five-minute presentation](docs/FIVE_MINUTE_SCRIPT.md)
- [Professor questions and answers](docs/PROFESSOR_QA.md)
- [Offline interactive robot demonstration](demo.html)
- [Original problem statement](bench-warehouse/README.md)
- [Source provenance and integrity](UPSTREAM.md)

From `bench-warehouse/`:

```text
python self_check.py --adapter adapters.myteam:Planner
python run.py --adapter adapters.myteam:Planner --out ../benchmarks/local_report.json
```

From this folder:

```text
python -m unittest discover -s tests -v
python tools/verify_upstream.py
python tools/verify_results.py
python tools/make_demo.py
```

The benchmark and shared `benchkit/` files are included unchanged. Additional
guides, tests, reports, and tools support development and explanation. The
competition contract asks for **one readable adapter file**:
`bench-warehouse/adapters/myteam.py`, class `Planner`. The helper tools are not
part of that adapter and are never imported by it.

The measured public results are local practice evidence. Read the results and
limitations before making claims about benchmark attainment, hidden judging,
optimality, or completeness.

Original source: [PHASE_2 warehouse-robot-planner](https://github.com/Vaishnavi-Naga-Sai-Ravula/PHASE_2/tree/main/warehouse-robot-planner).
