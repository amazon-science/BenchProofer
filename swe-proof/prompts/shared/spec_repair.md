# Strengthen the spec that admitted a wrong implementation — {iid} ({bk})

A previous adversarial audit found at least one attack that VERIFIES against
this bundle's spec but whose faithful patch does NOT resolve the instance. The
spec is therefore too weak: it admits an implementation that is wrong. Close the
hole.

## Read this part first: what separates a repair that lands from one that does not

Your repair is judged by a FRESH adversarial audit, authored from scratch against
whatever spec you leave on disk. You have a free preview of that exact judgment
(`self_audit.py`, below). Across past repair steps on this corpus:

* almost all of them edited a spec file, so landing an edit is not the hard part;
* few ever ran a single adversary check against their own new spec;
* **almost none ran the preview judge.** The rest submitted, and the fresh audit
  refuted most of them later, with the reasoning discarded.

So the failure mode of this task is not a wrong diagnosis. It is a plausible
clause submitted without being attacked. Two rules follow, and they are the two
rules on this page that decide whether your work survives:

1. **Do not report `REPAIRED` without the `self_audit.py` output in your report.**
   It is the same prompt, the same attack floor, and the same derivation the
   driver will run. Skipping it just means receiving the refutation later.
2. **Do not read the harness source.** `src/swebench_unified/**`, `scripts/**`
   and `prompts/**` are the graders, and they cannot tell you what is true of the
   real function. Steps that burn their clock in there reach their first
   verifier call far later than the ones that finish. Everything you need is the
   bundle, the repo worktree, and `instance.json`.

A rough budget for the hours you have: about 30 minutes reading the bundle and
the real function, then the diagnosis, then the edit, then attacks, then the
preview judge. If you have not run a verifier early in your budget you are on
the trajectory that times out.

## The evidence you are starting from

`{root}/{iid}/{bk}/verdict.md` is the audit record. In it:

* Each attack is rendered with its FULL SOURCE and an outcome label. Find the
  ones labelled `WEAK:` or `BROKEN:` — those are the counterexamples.
* The positive control is a correct implementation that MUST keep verifying
  after your repair. If your new clause breaks it, the clause is too strong.
* `Prepatch bug re-encoded as an attack` tells you whether the original bug is
  among the attacks.

The failing attack is EVIDENCE of your work, not the definition of it. After the
repair it must NOT verify, and it must fail because it is wrong, not because it
was excluded — but that is the floor, not the bar.

## What judges your repair: a fresh audit, not this attack

When you are done, the driver does not re-run the attack you were shown. It runs
a NEW adversarial audit (G-EQ and three G-PANEL roles) whose attacks are
authored from scratch against your new spec text. That is deliberate: re-running
the old attack only asks whether you pattern-matched it.

This is where repairs die. Measured over past repair attempts: the single most
common outcome was a repair that landed, passed every static gate, closed the
shown attack, and was then refuted by a fresh attack the same hole admitted. Roughly
half again failed a panel role instead — the new clause was true of the gold
implementation but not of the real callee (UNFAITHFUL), or it narrated the edit
(LEAKAGE).

So the shown attack is one witness of a hole. Repair the HOLE.

## First: which half of "correct" did the attack break?

`does not resolve` is two different verdicts, and they need opposite repairs. The
recorded note says which one you have, because it reports the two test sets
separately:

* **`FAIL_TO_PASS fails`** — the attack does not fix the reported bug, yet it
  verifies. The spec fails to FORCE the fix, and everything below applies as
  written: find the observable the patch's delta lives in and pin it.
* **`PASS_TO_PASS fails`, with `FAIL_TO_PASS 1/1 pass`** — the attack DOES fix
  the reported bug and breaks something else that used to work. A substantial
  minority of weakness findings are this shape, and some are both.
  Here the delta is already pinned, so strengthening the fix clause changes
  nothing: the attack satisfies it and keeps verifying, and the attempt is spent.
  What the spec is missing is the behavior the attack DESTROYED — an invariant
  the function had before the patch and still has after it. The named
  `PASS_TO_PASS` test is the pointer: read that test, see which property of the
  function it asserts, and state THAT as an obligation. It is usually a
  preservation claim (an ordering, a key that must survive, an untouched field, a
  case that must still raise) rather than anything about the bug.

So read the note's two counts before you form a diagnosis. If both sets fail, the
spec is missing both a fix clause and a preservation clause, and closing only one
leaves the attack verifying.

## Find the hole, not the attack

Before writing a clause, work out why the spec could not tell the attack apart,
in these terms:

1. **List what the spec observes.** Every value the postconditions constrain,
   plus every value they mention only in a precondition or not at all. The
   attack lives entirely inside the second list.
2. **Locate the patch's delta among them.** What does the gold patch change
   about the function's observable behavior? Now check: is that delta visible at
   all in list 1?
3. **If it is not, the model is the defect, and no postcondition can fix it.**
   Two shapes recur. A helper the spec models as unconstrained — a free boolean
   the implementation may choose, a flag nothing pins — lets the attack pick the
   value that makes any clause about it vacuous. A helper whose only
   postcondition makes it the identity (`Result() == x`, `f x = x`) makes the
   delta value-invisible: the attack can differ from the real function on
   exactly the thing the patch fixed and still satisfy every clause. The repair
   in both cases is to give that helper the postcondition its real counterpart
   actually satisfies, so the delta becomes observable, and only then to state
   the clause that pins it.
4. **Then ask what else the same hole admits.** If your clause is the only thing
   standing between the spec and a second wrong implementation of the same
   shape, you have not closed the hole; you have closed one path through it.

## Read before editing

1. `{root}/{iid}/{bk}/refinement.md` — the obligations this bundle claims.
2. `{root}/{iid}/{bk}/mapping.md` §1 — the repo symbol (file:line at
   base_commit) and §2 the type bridge. The real function is the ground truth
   for what is TRUE; read it at the base commit and read the gold patch.
3. `{root}/{iid}/instance.json` — the gold `patch`, and the public
   `problem_statement` (which bounds what you may say without leaking).
4. The attack source in verdict.md — to see exactly which behavior the current
   postconditions fail to pin down.

The question to answer before you write anything: *what is true of the real
patched function, false of this attack, and stated as behavior rather than as
code?* That clause is the repair.

## Files to edit

The spec region is SHARED. Every one of these must end up with the same spec:

{spec_files}

`properties.py` embeds the frozen solution text as anchors and asserts them at
import, so a spec edit that misses it will fail immediately with an assertion
error. Update the anchors to the new text; do NOT weaken or delete reject cases
to accommodate the change.

## Be your own adversary — this is the step that decides the outcome

You have the same tool the audit uses. It takes a candidate wrong
implementation, checks it carries your spec unchanged, and checks whether it
verifies:

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.adversary weakness {bk} {iid} /tmp/<scratch>/atk_1.<ext>
```

`CANDIDATE-COUNTEREXAMPLE` means the spec still admits a wrong implementation
and your repair is not finished. `NOT-A-COUNTEREXAMPLE: attack does not verify`
is the result you want on every one. (`NOT-A-COUNTEREXAMPLE: attack changed the
spec` means your attack file is invalid, not that the spec is strong — fix the
attack and re-run.)

Write at least FOUR new attacks of your own, none of them the one from
verdict.md, and drawn from different families so they probe the hole rather than
the same path:

* the shown attack's shape, mutated to whatever the new clause now permits;
* partial-domain: correct on the inputs the clause pins, wrong elsewhere in the
  precondition's domain;
* boundary: empty, singleton, zero, negative, or the aliased/same-object case;
* ungrounded-oracle echo: return a value derived from the arguments in a way
  that satisfies every clause without doing the work — this is what catches a
  clause that is a tautology under the current model;
* control-flow-effect: right value, wrong effect (an order, a mutation, an
  exception path) if the spec claims anything about effects.

Attack checks are independent, so run up to three concurrently as background
jobs. Iterate: any CANDIDATE means back to "Find the hole". Do not report until
a full round of four produces no candidate. You have hours of budget; the
repairs that survived the fresh audit spent close to twice the wall time of the
ones that did not.

### Then run the judge yourself, once

Your four attacks are a proxy for the audit. You can run the audit instead. This
launches the REAL weakness auditor — the same prompt, the same attack floor, the
same re-derivation that scores G-EQ and G-PANEL-1 — against your repaired spec,
and records nothing: your cell's `meta.json` is not touched whatever it finds, so
this cannot damage the bundle and cannot pre-empt the driver's own audit.

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} scripts/self_audit.py {iid} {bk} --timeout 2400
```

It prints `G-EQ = PASS|FAIL` and `G-PANEL-1 = PASS|FAIL`, the per-attack labels,
and the path to the attack sources it wrote — which it keeps, so a FAIL names a
file you can read. A FAIL here is the refutation you would otherwise have
received hours later with your reasoning discarded: go back to "Find the hole"
with that attack, close it, and re-run this.

Run it after your own four attacks are clean, and budget for TWO rounds. It costs
an auditor's full run, roughly 40 minutes, and you have hours — so a FAIL on the
first round is not the end of the attempt. It is the refutation arriving while you
can still do something about it. Read the attack it names, close the hole it came
through, and run it again.

That second round is the whole point. On this corpus, about half of all repair
attempts ended as `audit-fail`: an edit that landed, passed every static gate,
and was refuted by exactly this audit hours later, with the diagnosis discarded
and the cell handed to another agent starting from nothing. Every one of those was a first round whose result nobody was still
around to use.

Stop after the second round whatever it says — a third would spend the clock you
need for the report, and a FAIL you understand is worth more than a third roll. If
it prints `INCONCLUSIVE`, the role reached no verdict: that says nothing about your
spec, so do not read it as a pass, and do not re-run it hoping for a different
answer. Report what it printed either way — including `INCONCLUSIVE`, which the
driver reads as untested rather than as a failure.

Two panel roles also re-run, and they fail repairs that over-reach:

* **faithfulness.** Your clause must be true of the REAL callee on every input
  the precondition admits, not just on the gold path. Read the branches your
  clause now constrains, and read them in the RIGHT tree: the worktree you are
  given is at `base_commit`, which is the code the instance fixes, so for the
  modelled function the reference is that worktree with `patch.diff` applied.
  Checking against the base version instead is the most expensive mistake
  available here, because the two differ on exactly the behavior your clause is
  about: you write a clause that is true of the buggy function, the faithfulness
  role checks it against the patched one, and the repair comes back UNFAITHFUL.
  Base commit is the right reference only for callees the gold patch does not
  touch (what the axioms model).
* **leakage.** The clause states behavior. It must not name the patched file,
  reproduce a line of the diff, or say anything about the fix that the public
  `problem_statement` does not already say.

## Verify — the gates decide, not you

Run these in order, and do not stop until each is green (or you have concluded
no repair was needed and can prove it):

```bash
# 1. the attack must now FAIL to verify, and the positive control must still verify.
#    Extract them from verdict.md into a scratch dir first (mktemp -d).
# 2. every static gate, including G-DIFF (twins spec-identical) and G-PBT:
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} --static-only {iid}
# 3. the docker gates (G-RESOLVE must still pass: the GOLD patch still resolves):
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
  {python} -m swebench_unified.cli gates --backend {bk} \
    --gates G-RESOLVE G-CONF G-AX -- {iid}
```

The three checks that make a repair real, and that you must state the result of:

* **The attack no longer verifies.** Otherwise the hole is still open.
* **The prepatch twin still FAILS.** If the buggy code satisfies your new spec,
  the spec does not capture the fix. Check this explicitly.
* **The positive control still verifies** and G-PBT still passes. Otherwise you
  over-fitted to the gold implementation and correct alternatives now fail.

## Rules

* Put scratch under a private `mktemp -d /tmp/repair.XXXXXX`. Never write to the
  bundle except the spec files above; never to the repo root. G-INTEGRITY fails
  a cell with a stray file.
* Never search from `/` — a tree-wide `find` can block for minutes. Search from
  the repo root or `{root}/{iid}`.
* Run NO git command that writes (`add`, `commit`, `checkout`, `stash`,
  `restore`, `reset`, `clean`). Use `git show HEAD:<path>` to read a committed
  version.
* Do not edit `patch.diff`, `instance.json`, or any `verdict.md`.
* Never weaken a precondition's domain to dodge the attack, and never add a
  clause that mentions the attack rather than the behavior.

## Report

* the hole, in the terms of "Find the hole": which observable the spec left free
  or modeled away, and how your edit made the patch's delta observable
* the clause you added, and why it is TRUE of the real patched function (cite
  file:line) and FALSE of the attack
* your OWN attacks: for each, its family, its path, and the `adversary weakness`
  line it printed. A report with no self-authored attacks is incomplete
* the `self_audit.py` lines it printed for G-EQ and G-PANEL-1, or why you did not
  reach that step
* the attack's verify result after the repair (must not verify)
* the prepatch twin's result (must still fail)
* the positive control's result and the G-PBT line (must still pass)
* the exact static-gate and docker-gate lines the commands printed
* `REPAIRED` if every gate is green AND you have pasted the `self_audit.py`
  output above. A `REPAIRED` without it is a guess about the verdict rather than a
  reading of it, and the driver is about to derive that verdict anyway; report
  `BLOCKED` and say you ran out of budget before the preview, which is the honest
  and more useful outcome. `NO-REPAIR-NEEDED` plus the evidence that the attack
  was not a real counterexample, or `BLOCKED` plus precisely what resisted and
  what you tried
