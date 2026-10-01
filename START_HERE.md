# Start here: Warehouse Robot Planner

This folder contains the complete public problem bundle, a one-file planner,
benchmark targets and measured reports, correctness tests, and teaching notes.
Open the **whole `Warehouse-Robot-Planner` folder** in VS Code so that the
shared `benchkit/` directory remains next to `bench-warehouse/`.

## What you must solve

Every robot has a fixed start and goal on a grid containing shelves/walls.
Return one path per robot, in robot-index order. A path starts at time 0;
each later entry is the cell occupied after one move or wait.

- Move north, south, east, or west, or wait in the same cell.
- Never occupy a blocked or out-of-grid cell.
- Never let two robots occupy one cell at the same time.
- Never let two robots swap across the same edge in one step.
- Robots remain at their goals after finishing.
- Complete every path within the supplied horizon.

Lower cost is better. The objective combines the last robot's arrival
(makespan), all arrival times added together (sum of costs), and pairs of
distinct robots sharing designated corridor cells (congestion).

Read `bench-warehouse/README.md` for the exact original statement. Read
`docs/FOUNDATIONS.md` to learn the concepts before examining the implementation.

## Run in VS Code

The project uses only Python's standard library. It was developed with Python
3.13. Select your Python interpreter in VS Code; no API keys or model downloads
are required.

Open **Terminal → New Terminal**, then:

```text
cd bench-warehouse
python self_check.py --adapter adapters.myteam:Planner
python run.py --adapter adapters.myteam:Planner --out ../benchmarks/local_report.json
```

The self-check tests two smaller cases. The full run evaluates nine public
cases at the normal budgets and includes the original replay check. A full run
takes about 2.5 minutes plus generation overhead. Avoid running it under a
debugger or alongside other CPU-heavy work because early checkpoints matter.
The included measured report is separate from `local_report.json` so you can
keep the evidence and compare a fresh run.

If `python` is unavailable on Windows but `py` works, substitute `py` in these
commands. **Terminal → Run Task** provides shortcuts for the check, benchmark,
tests, and demo.

From the project root, run:

```text
python -m unittest discover -s tests -v
python tools/make_demo.py
```

Open `demo.html` in a browser. It works offline and includes a small teaching
example plus a real public-case plan. The intentionally invalid swap example
is educational; it is not output submitted by the planner.

## Read the folder in this order

1. `docs/FOUNDATIONS.md`: grids, graphs, BFS, A*, time and collisions, LNS,
   objective, worked examples, and limits.
2. `demo.html`: step through a swap and a legal detour.
3. `docs/CODE_WALKTHROUGH.md`: follow the actual planner functions.
4. `BENCHMARKS.md`: exact targets, measured results, and scoring.
5. `docs/FIVE_MINUTE_SCRIPT.md`: rehearse a concise presentation.
6. `docs/PROFESSOR_QA.md`: prepare for questions about optimality,
   completeness, complexity, reproducibility, and real deployment.

You should be able to explain what a state is, why waiting is needed, how each
conflict is prevented, why parking order matters, how a group is repaired,
and how the independent validator decides cost. If you cannot explain a
component yet, use the worked example and walkthrough before presenting it.

## Files and their purpose

| Location | Purpose |
|---|---|
| `bench-warehouse/adapters/myteam.py` | The single submitted algorithm file; class `Planner` |
| `bench-warehouse/adapter.py` | Original interface and public planning helpers |
| `bench-warehouse/data.py` | Original instance generator; the adapter does not recover its witness |
| `bench-warehouse/validator.py` | Independent movement, collision, arrival, and objective checks |
| `bench-warehouse/public_reference.json` | Exact public scoring targets; not read by the adapter |
| `bench-warehouse/run.py`, `self_check.py` | Original public evaluation entry points |
| `benchkit/` | Original timing, scoring, loading, reporting, and resource-limit code |
| `benchmarks/` | Measured reports and visual demonstration data |
| `tests/` | Small correctness checks, separate from the submission |
| `docs/` | Learning notes, code explanation, speech, and questions |
| `tools/make_demo.py` | Optional demonstration utility; not imported by the adapter |
| `.vscode/` | Editor task shortcuts |
| `UPSTREAM.md`, `upstream/` | Source provenance, integrity notes, and original rules |

All original benchmark files are preserved unchanged. The root README,
guides, tests, reports, and demo are additional materials. A local result is
not an official event result, and a reference match is not a proof of optimum.

## Upload to GitHub

The local delivery folder is prepared as a Git repository on branch
`codex/warehouse-robot-planner`. The downloadable ZIP contains source and
reports without `.git/` or Python cache files. If you extract the ZIP, first
initialize a repository through VS Code's **Source Control** view.

For a new repository, open Source Control and choose the available
**Publish Branch/Publish to GitHub** action, sign in, and choose your repository
name and visibility. Review the tracked files before publishing. For an
existing empty repository, add its own remote URL and push this branch:

```text
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin codex/warehouse-robot-planner
```

For that workflow, create the empty remote without an initial README,
`.gitignore`, or license, since this folder already contains a commit. You can
choose a different branch name before publishing if your event requires it.

If submitting into the given PHASE_2 repository, the algorithm belongs at
`warehouse-robot-planner/bench-warehouse/adapters/myteam.py`. Keep the original
surrounding benchmark layout. Follow the organizers' exact registration and
upload procedure rather than assuming a new GitHub repository completes entry.

**The stated competition submission is exactly one readable Python adapter
file.** Keep the complete folder for development, reproducible checking, and
presentation. Submit `myteam.py`, class `Planner`, when that is what the
organizers request. Do not submit modified clocks, anchors, validators, or
benchmark code. AI coding assistance is allowed; explain its use honestly.

Source: [original problem and contract](https://github.com/Vaishnavi-Naga-Sai-Ravula/PHASE_2/blob/main/warehouse-robot-planner/bench-warehouse/README.md).
GitHub workflow: [official import guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
