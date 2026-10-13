# Repair the spec defect a review role found — {iid} ({bk})

Failing role(s): **{roles}**

`G-PANEL-2` = the spec is UNFAITHFUL: it predicts something the real repo callee
does not do. `G-PANEL-3` = the spec LEAKS the fix's discriminating behavior.

**Do not read the harness source.** `src/swebench_unified/**`, `scripts/**` and
`prompts/**` are the graders, and they cannot tell you what the real callee does.
Steps that burn their clock in there reach their first verifier call far later
than the ones that finish. Your ground truth is the repo worktree, the bundle,
and `instance.json`. Budget roughly 30 minutes of reading before you reproduce
the witness; if no verifier has run early in your budget you are on the
trajectory that times out.

## The evidence you are starting from

`{root}/{iid}/{bk}/verdict.md` holds the reviewer's finding under the role's
section: the **machine verdict** names the witness input, the model's output and
the real callee's output, plus how each was obtained. Start by REPRODUCING it.
A repair aimed at a divergence you have not reproduced is a guess.

**The reviewer may have already written the fix.** These roles are asked to show
that a defect is real, and the cheapest proof is often a repaired spec: a scratch
file that adds the missing guard or leg, verifies, and still rejects the prepatch
twin. When the verdict names such a file or quotes the clause it added, that is
your starting point, not something to re-derive — a reviewer who demonstrated the
edit has already paid for the part of this work that is hardest to redo. It is
still a claim to CHECK rather than trust: the scratch file is gone, so
re-transcribe the clause into the spec files yourself and put it through the gates
below. Its discrimination argument is the part to re-run, because a clause that
makes the real callee verify can also make the buggy twin verify.

Also read:

1. `{root}/{iid}/{bk}/mapping.md` §1 — the repo symbol (file:line at
   base_commit) and §2 the type bridge. §1 is the ground truth for what the
   callee does; §2 is how its values correspond to the model's. A divergence is
   sometimes in the BRIDGE rather than in the model.
2. `{root}/{iid}/{bk}/refinement.md` — the obligations this bundle claims.
3. `{root}/{iid}/instance.json` — the gold `patch` and the public
   `problem_statement`. The problem statement is the leakage baseline: it bounds
   what the spec may disclose. `hints_text` and the tests are NOT part of it.
4. For leakage: every file in the spec view, looking for the discriminator.

Run the real function. The repo is available at the base commit through the
instance's container image, and the reviewer's verdict says how it reproduced
the witness — reuse that route.

The question to answer before you write anything, for faithfulness: *on the
reviewer's witness, what does the real callee return, and what is the smallest
change to the model that makes it predict that on the whole class the witness
belongs to?* For leakage: *which line of the spec view could a solver not have
written from the problem statement alone, and how is the same obligation stated
without it?*

## Fix the class, not the witness

Your repair is judged by a FRESH review: four roles, re-run against your new
spec, each free to pick its own witness. Measured over past repair attempts,
that is where these repairs die, in two ways.

**The same defect, a different witness.** A faithfulness divergence is almost
never one input's accident; it is a branch of the real callee the model does not
model. So after reproducing the reviewer's witness, find the BRANCH it exercises
in the real function and shadow the repaired model against the real callee
across the whole domain: each branch, each early return, the empty and singleton
and zero and negative cases, and the type-bridge edges (`None`, aliasing, mixed
types) where §2 of mapping.md does the converting. At least eight inputs,
chosen to hit different branches rather than eight of the same shape. State the
pairs you compared. `G-CONF` is the mechanized form of this check and is the
gate most likely to catch what you missed, so run it — but run your own spread
first, because it is faster to iterate than the container is.

**A missing leg, not a missing branch.** The witness's own branch is the shallow
version of this defect, and closing it is what lets the next reviewer find the
deep one. Two shapes account for the repeat findings measured on repaired cells,
and neither is reachable by spreading inputs over the witness's class:

* *The model folds in a helper and keeps only part of it.* A model that says
  "copies the identity attributes" may be modelling one of the callee's two
  passes, where the real routine walks a per-attribute table and THEN applies a
  second, whole-container overlay that can overwrite what the first pass wrote.
  Every input in the world hits both passes, so no spread of witnesses exposes
  it; only reading the helper does. Note that the helper is usually code the
  patch does not touch, and may be in the standard library — faithfulness is to
  what the patched line actually calls, transitively, not to the patch's diff.
  So enumerate the callee's contract as STEPS and consulted tables, and check
  your model has a leg for each one. Name the steps in your report.
* *The model collapses two real callees into one.* When the real code dispatches
  on an arm to a DIFFERENT function, the model needs that function's behavior,
  not the nearest approximation to it. A formatter that is identity-on-str is
  right for one arm's inputs and wrong for a container arm that joins its
  elements instead. Follow each arm to the function it actually reaches and say
  which model expression stands for which.

Both are found by reading, so read the callee and every helper it dispatches to
before you decide what the smallest change is.

**A realignment that opens a hole.** Making the model agree with the real callee
usually means relaxing something, and a relaxed postcondition can start admitting
wrong implementations — which the fresh `G-EQ` and `G-PANEL-1` roles then find,
turning one failing role into three. The same applies to de-leaking: a
discriminating clause removed for leakage was also doing work. So before
reporting, be the adversary yourself on the repaired spec:

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.adversary weakness {bk} {iid} /tmp/<scratch>/atk_1.<ext>
```

Beyond re-checking the audit's own attacks, write at least two NEW ones aimed at
whatever your edit relaxed: an implementation that is correct exactly where your
new clause still pins the value and wrong where it no longer does, and an
ungrounded-oracle echo that derives its result from the arguments without doing
the work. `CANDIDATE-COUNTEREXAMPLE` on either means the realignment went too
far and the model needs to say something else instead, not less.

### Then let the weakness auditor try, once

Your two attacks are a proxy for the roles that judge a relaxation. You can run
the role instead. This launches the REAL weakness auditor against your repaired
spec and records nothing — your cell's `meta.json` is untouched whatever it finds,
so it cannot damage the bundle and cannot pre-empt the driver's own audit:

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} scripts/self_audit.py {iid} {bk} --timeout 2400
```

It prints `G-EQ = PASS|FAIL` and `G-PANEL-1 = PASS|FAIL` and keeps the attack
files, so a FAIL names a file you can read. This is the check that catches the
failure mode above — one failing role turning into three — and it is worth its
budget for exactly that reason: almost no past repair ran it, and a repair
submitted without it is refuted later with the reasoning discarded.

Budget for TWO rounds. It costs roughly 40 minutes and you have hours, so a FAIL
on the first is the refutation arriving while you can still act on it: read the
attack it names, close the hole, run it again. Stop after the second whatever it
says. `INCONCLUSIVE` means the role reached no verdict, which is not a pass;
report what it printed either way.

## Files to edit

The spec region is SHARED. Every one of these must end up with the same spec:

{spec_files}

`properties.py` embeds the frozen solution text as anchors and asserts them at
import, so an edit that misses it fails immediately with an assertion error.
Update the anchors to the new text; do NOT weaken or delete reject cases to
accommodate the change. If the model's function changed, the battery's expected
values for the affected inputs change with it — recompute them from the REAL
callee, not from the old model.

## Verify — the gates decide, not you

```bash
# every static gate, including G-DIFF (twins spec-identical), G-GOLD and G-PBT:
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} --static-only {iid}
# the docker gates (G-CONF is the mechanized faithfulness check — it shadows the
# model against the real callee on many inputs, so it is the gate most likely to
# catch an incomplete realignment):
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} \
    --gates G-RESOLVE G-CONF G-AX -- {iid}
```

The checks that make a repair real, and whose results you must state:

* **The witness now agrees.** The repaired model, evaluated on the reviewer's
  witness input, produces the real callee's output. Show both values.
* **The prepatch twin still FAILS.** If the buggy code satisfies the repaired
  spec, the spec no longer captures the fix. Check this explicitly.
* **The spec still rejects wrong implementations.** The audit already built
  attacks against this cell; they are in verdict.md with their source. Re-check
  at least the two most on-point ones: they must still fail to verify. This is
  what separates realigning the spec from weakening it.
* **G-PBT and G-GOLD still pass** — otherwise you over-fitted and correct
  alternative implementations now fail.

## Rules

* Put scratch under a private `mktemp -d /tmp/panel.XXXXXX`. Never write to the
  bundle except the spec files above; never to the repo root. G-INTEGRITY fails
  a cell with a stray file.
* Never search from `/` — a tree-wide `find` can block for minutes. Search from
  the repo root or `{root}/{iid}`.
* Run NO git command that writes (`add`, `commit`, `checkout`, `stash`,
  `restore`, `reset`, `clean`). Use `git show HEAD:<path>` to read a committed
  version.
* Do not edit `patch.diff`, `instance.json`, or any `verdict.md`.

## Report

* the witness, the real callee's output on it, and the repaired model's output
* the input class the divergence belonged to, and the spread you shadowed: the
  inputs, the real callee's value and the model's value on each, and which branch
  each one exercises. A report with only the reviewer's witness is incomplete
* what you changed and why it is the real callee's behavior (cite file:line at
  base_commit) — or, for leakage, the line that leaked and how the obligation
  survives without it
* the prepatch twin's result (must still fail)
* the two attacks you re-checked and the new ones you wrote against whatever your
  edit relaxed, with their `adversary weakness` lines (none may be a candidate)
* the `self_audit.py` lines it printed for G-EQ and G-PANEL-1, or why you did not
  reach that step
* the exact static-gate and docker-gate lines the commands printed
* `REPAIRED` if every gate is green AND the `self_audit.py` output is above. A
  `REPAIRED` without it is a guess about a verdict the driver is about to derive;
  report `BLOCKED` and say you ran out of budget before the preview, which is
  honest and more useful. `NO-REPAIR-NEEDED` plus the run that shows the model and
  the real callee agree on the reviewer's witness, or `BLOCKED` plus precisely
  what resisted and what you tried
