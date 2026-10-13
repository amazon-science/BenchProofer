# Cross-backend port lane — shared agent instructions (2026-08-18)

You are a construction agent porting ONE benchmark-pro cell to a target formal
backend, for a task that is already green on the other backends. Your cell and
target are given in your task message. Working dir: /home/ubuntu/verified-swebench.

## Environment — non-negotiable

- Always export BOTH `SBU_BENCHMARK=swe_bench_pro_python` and
  `SBU_BENCHMARK_DIR=benchmark-pro`, plus `SBN_VERIFY_TIMEOUT=900` and
  `SBU_PBT_VERIFY_TIMEOUT=900` (set all four; different gates read different knobs).
- Also export `SBU_MUTATION_WORKERS=1` and `SBU_PBT_WORKERS=1` for every gate
  run: many construction agents run concurrently, and an unbounded G-MUT fans
  out ~390 Z3 processes per cell.
- Python: `.venv/bin/python` with `PYTHONPATH=src` (or `sys.path.insert(0,'src')`).
- nagini verification needs the Python 3.9 verifier env — see
  `experiments/pro2026/setup_verifier_env.sh` and `scripts/nagini_verify.sh`.
  The 300s cap in nagini_verify.sh lies under load; SBN_VERIFY_TIMEOUT=900.
- Docker needs `sg docker -c ...`; the codebase's `docker_exec` handles it.
- Run ALL verifier/container invocations SERIALLY — one at a time. A slow
  verification recorded as failure is a manufactured defect.
- Kill stray processes by explicit PID only; `pkill -f` matches your own shell.

## Hard rules

1. **`build_one --force` is BANNED.** It overwrites BLOCKED.md with a stub,
   destroying multi-page analyses. All BLOCKED.md files are already backed up at
   `experiments/pro2026/blocked_backups/xport_20260818/`, but do not rely on that.
2. Edit ONLY files under `benchmark-pro/<iid>/<target>/` (and /tmp or
   experiments/pro2026/xport_work/<short-iid>/ scratch). Never touch
   `instance.json`, `patch.diff`, or any sibling backend directory.
3. If the cell has a BLOCKED.md, READ IT FIRST. It is a principled refusal by a
   previous agent. You are testing whether it is wrong. Do not delete it until
   you hold a demonstrated pair (defined below). If your work confirms the
   refusal, UPDATE it with your evidence instead.
4. `run_gates(..., record=True)` only on your own cell, only for mechanical
   gates, only after your artifacts are final. Agentic gates (G-EQ, G-PANEL-*)
   are re-derived later by a separate audit fleet — do not fake or hand-stamp them.
5. **nagini↔lean ports historically FAILED when transliterated.** If your
   source sibling is lean and target nagini (or vice versa), re-derive the
   specification from the task's case analysis (problem statement + gold patch
   + sibling's SEMANTIC content), never by translating syntax.

## The bar: a demonstrated pair

Your port succeeds only if you produce, and measure, BOTH legs:
- a **gold-shaped implementation** (mirrors the gold patch's behavior) that
  VERIFIES against your spec, and
- the **prepatch implementation** (the buggy pre-fix behavior) that FAILS
  verification against the same spec.
Record the exact commands and outputs. A spec that cannot separate the two is
not a port, it is decoration. A reference demonstration lives at
`experiments/pro2026/overturn_c616e54a/` (nagini) — study its shape.

## Process

1. Read the task: `benchmark-pro/<iid>/instance.json` (problem_statement),
   `patch.diff`, and every green sibling bundle (`<iid>/<sibling>/`).
2. Find a strict-green TEMPLATE cell of the TARGET backend (ideally same repo
   family) to learn the full file inventory a green cell carries: spec
   artifact(s), meta.json gate blob, PBT battery + manifest, result.json, etc.
   `experiments/pro2026/green_status.py` / `src/swebench_unified/green_check.py`
   tell you what green requires; `src/swebench_unified/backends/<target>.py`
   tells you how the backend checks/verifies.
3. Construct the spec artifacts from the siblings' semantic content (respecting
   rule 5). Then build the demonstrated pair and measure it (serially).
4. Port/author the PBT battery for the target backend (see
   `docs/pro-pbt-plan.md` and green siblings' batteries): the battery must pass
   on gold behavior and kill the prepatch implementation. Self-check it.
5. Run the mechanical gates read-only first (`record=False`), fix what fails,
   and only then record: G-VERIFY, G-DIFF, G-GOLD, G-LEAK, G-HYGIENE,
   G-INTEGRITY, G-CONF, G-AX, G-MUT, G-PBT (whichever apply to the backend —
   check `applies_to` in each gate module). Every failure you cannot fix must
   be reproduced serially at calm load before you believe it.
6. If the port is fundamentally impossible because of a specific backend
   feature (not merely hard): write a precise report of the wall — the exact
   spec obligation that cannot be expressed/verified, with the failing minimal
   example — update BLOCKED.md with it, and return outcome IMPOSSIBLE.

## Return value (final message = raw JSON, no prose)

{"iid": "...", "target": "...",
 "outcome": "CONSTRUCTED" | "IMPOSSIBLE" | "FAILED",
 "files": ["<paths written>"],
 "pair": {"gold_shaped": "<command + verdict>", "prepatch": "<command + verdict>"},
 "pbt": "<battery self-check result>",
 "gates": {"<gate>": "<status + 1-line detail>"},
 "notes": "<walls hit, caveats, anything the auditor must know>"}
