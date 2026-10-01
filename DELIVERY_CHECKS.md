# Delivery verification

Checked on 1 October 2026 using CPython 3.13.7 on Windows 11.

- All 25 supplied benchmark/shared-library files match their original SHA-256 hashes.
- The delivered adapter passed 24 correctness tests. These include collision,
  arrival, congestion, and scoring contracts; 12 small planner fixtures; and
  1,536 low-level reservation comparisons with the original space-time A*.
- The original self-check passed on both cases.
- The full public harness at normal budgets produced valid paths on 9/9 cases,
  rejected zero candidates, preserved every instance, and completed within
  every budget.
- The selected adapter's first-case two-run replay matched exact scored outputs.
- Final baseline costs were reached on 9/9 cases; final references on 6/9.
  The measured practice score is 58.467/100. Full checkpoint targets remain
  unmet; see [BENCHMARKS.md](BENCHMARKS.md).
- The offline demo was inspected in a browser: stepping the legal detour works,
  the invalid swap reports a conflict, and the saved 50-robot plan reaches all
  goals without a displayed final conflict. The independent validator is the
  authority for legality.

Repeat the file/evidence checks from this folder:

```text
python tools/verify_upstream.py
python tools/verify_results.py
python -m unittest discover -s tests -v
```

The measured run is evidence for the included public cases and exact adapter
hash. Runtime and checkpoint outcomes may differ on another run or machine.
The organizer's unseen judging suite has not been tested.
