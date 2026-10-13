# Re-author the artifact a mechanical gate refuted — {iid} ({bk})

Gate `{gate}` FAILED on this bundle. It ran the artifact against the real
repository code and recorded a concrete disagreement. Close the disagreement by
making the artifact model what the real code does.

## The evidence you are starting from

The gate's own recorded report, in `{root}/{iid}/{bk}/meta.json` under
`gates.{gate}`:

```bash
{python} -c "import json,sys; \
  g=json.load(open('{root}/{iid}/{bk}/meta.json'))['gates']['{gate}']; \
  print(g.get('detail','')); print(json.dumps(g.get('data',{{}}), indent=2)[:4000])"
```

Read it before anything else. It is the specification of your work. What to look
for, depending on the gate:

* **G-CONF** shadows the model against the real patched callee over a large
  sampled input space. The report carries `disagreements` out of `checked`, and
  usually `kinds` / `classes` breaking them down by shape, a `finding` sentence
  naming the divergent clause, a `seed`, and a `bridge_fault` or
  `attributed_to` field saying whether the fault was localised to the model or
  to the type bridge. The class counts tell you whether one clause is wrong on a
  whole family of inputs or a corner case leaks through.
* **G-AX** asserts that the axioms the model ASSUMES actually hold of the real
  code. A failure means the model is built on something false: the traceback
  names the assertion and usually prints the witness. The axiom is the defect,
  along with whatever the model concluded from it.
* **G-VERIFY** means the solution does not verify against its own spec.
* **G-MUT** means a mutant of the solution still satisfies the spec, so the spec
  does not pin the behavior the mutation changed.

## Reproduce the disagreement first

Do not edit anything until you have seen the failure yourself and can name a
single concrete input on which the model and the real function differ. The
report's `seed` makes the shadow reproducible:

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} --gates {gate} -- {iid}
```

A repair aimed at a summary statistic rather than a witness usually moves the
count without closing the class.

## Read before editing

1. `{root}/{iid}/{bk}/mapping.md` §1 — the repo symbol (file:line at
   base_commit) and §2 the type bridge. **The real function is the ground
   truth.** Read it at the base commit, then read the gold patch: together they
   are what the model must agree with.
2. `{root}/{iid}/{bk}/refinement.md` — the obligations this bundle claims.
3. `{root}/{iid}/instance.json` — the gold `patch` and the public
   `problem_statement` (which bounds what you may say without leaking).
4. The check script the gate runs (`conformance_check.py` / `axiom_check.py`) —
   to understand what is being compared, NOT to change what it compares.

The question to answer before you write anything: *on the witness input, what
does the real patched function actually compute, and which clause of the model
says otherwise?*

## Files to edit

The spec region is SHARED. Every one of these must end up with the same spec:

{spec_files}

`properties.py` embeds the frozen solution text as anchors and asserts them at
import, so an edit that misses it fails immediately with an assertion error.
Update the anchors to the new text; do NOT weaken or delete reject cases to
accommodate the change.

## What you may not do

* **Do not edit the oracle to agree with the artifact.** The check script and
  its generators are the measurement. Narrowing the generator, shrinking the
  input count, special-casing a witness, or deleting a failing assertion all
  produce a green stamp that means nothing. If and only if you conclude the
  fault is really in the type bridge or in the check script's own comparison
  logic, you may fix that — and then you must name the mis-encoding and show
  the model was right about the real behavior all along. Set
  `oracle_unchanged: false` and justify it.
* **Do not narrow the model's domain** so the diverging inputs become
  inadmissible. That shrinks the claim instead of correcting it, and it usually
  excludes the very behavior the gold patch changed.
* **Do not leak the fix.** State what the function computes, not what changed.

## Verify — the gates decide, not you

```bash
# 1. the failing gate must now pass, with zero disagreements:
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} --gates {gate} -- {iid}
# 2. every static gate, including G-DIFF (twins spec-identical) and G-PBT:
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} --static-only {iid}
# 3. the remaining docker gates (G-RESOLVE: the GOLD patch still resolves):
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} \
    --gates G-RESOLVE G-CONF G-AX -- {iid}
```

The checks that make the re-authoring real, and whose results you must state:

* **The gate's disagreement count is 0**, not merely lower.
* **The prepatch twin still FAILS.** If the buggy code satisfies the artifact
  now, the spec no longer captures the fix. Check this explicitly.
* **G-PBT still passes** and no reject case was weakened, so the repair did not
  make correct alternative implementations fail.

## Rules

* Put scratch under a private `mktemp -d /tmp/mech.XXXXXX`. Never write to the
  bundle except the files above; never to the repo root. G-INTEGRITY fails a
  cell with a stray file.
* Never search from `/` — a tree-wide `find` can block for minutes. Search from
  the repo root or `{root}/{iid}`.
* Run NO git command that writes (`add`, `commit`, `checkout`, `stash`,
  `restore`, `reset`, `clean`). Use `git show HEAD:<path>` to read a committed
  version.
* Do not edit `patch.diff`, `instance.json`, or any `verdict.md`.

## Report

* the witness input, what the real function computes on it (cite file:line at
  base_commit), and which clause of the artifact said otherwise
* what you changed and why that is the real behavior rather than a workaround
* whether you touched the oracle at all, and if so the mis-encoding that
  justified it
* the gate's disagreement count before and after (after must be 0)
* the prepatch twin's result (must still fail) and the G-PBT line
* the exact gate lines the commands printed
* `REPAIRED` if every gate is green, `NO-REPAIR-NEEDED` plus the evidence that
  the gate's report was not a real refutation, or `BLOCKED` plus the concrete
  inputs and precisely what resisted
