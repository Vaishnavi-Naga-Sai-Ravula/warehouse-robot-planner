# Provenance and benchmark integrity

Original project: [Warehouse Robot Planner](https://github.com/Vaishnavi-Naga-Sai-Ravula/PHASE_2/tree/main/warehouse-robot-planner).

Retrieved on 1 October 2026 from commit
`9a6f94fb5f2b89fb1c4969cf360c67ee0064a495`.

All original files in `bench-warehouse/` and `benchkit/` are included **without
changes**. Their original SHA-256 hashes are recorded in
`upstream/source_manifest.json`. The repository-wide rules are preserved in
`upstream/PHASE2_RULES.md`.

The new solution is `bench-warehouse/adapters/myteam.py`, class `Planner`.
Its Git attribute preserves its exact bytes, including line endings, so the
submitted file hash remains identical to the measured report after a clone.
It uses ordinary graph search, the documented instance fields, and the
submission callback. It does not access public reference files, generator
witnesses, instance identifiers, profiles, seeds, evaluator internals, files,
networks, or subprocesses.

The additional guides, tests, demo builder, and reports are development and
presentation materials. Their file access is outside the submitted adapter;
none of them is imported by the adapter. The organizers require the exact
single readable adapter file, not a modified benchmark or demo utility.

The original Windows guards already work; no evaluator patch was required.
On native Windows, unsupported POSIX hard alarm/address-space restrictions
are skipped by the original runner. Late-candidate rejection still applies.
The solver bounds its own search and stops with a safety margin.

The executable scoring uses baseline = 0.25 and a 70/30 quality/robustness
split, with an engineering multiplier. A few supplied comments contain older
values; the original code and current problem README are authoritative.

Local reports are public practice estimates. Official grading uses the
organizers' environment and may include unseen instances or seeds. No local
measurement certifies the hidden score or mathematical global optimality.
