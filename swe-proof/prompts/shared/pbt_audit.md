# G-PBT battery AUDIT — {iid} ({backend_name})

The ported battery for this cell records **G-PBT=pass :: SOUND**. Decide whether
that SOUND is EARNED, case by case, and repair it if it is not.

- Battery under audit: `{root}/{iid}/{backend_name}/properties.py`
- Frozen solution (you may NOT edit): `{root}/{iid}/{backend_name}/{solution_filename}`
- Design document the port came from: `{root}/{iid}/nagini/properties.py`
- Recorded verdict + per-case outcomes: `{root}/{iid}/{backend_name}/meta.json`, gate `G-PBT`
- Symbol/type bijection: `{root}/{iid}/{backend_name}/mapping.md`
- Real behavior, F2P, gold patch: `{root}/{iid}/instance.json`
- Binding rules for this backend: `prompts/{backend_name}/spec_guide.md`

## Why a recorded SOUND is not enough

The gate re-runs every case and confirms it behaved as DECLARED: `expect="verify"`
cases verified, `expect="reject"` cases did not. Three things it cannot see:

1. **Whether a rival is actually wrong.** On a tactic-proof backend the frozen
   proof script is tuned to the frozen impl's syntactic form, so a merely
   RESHAPED correct rival fails to build identically to a WRONG one — both
   `Tactic 'rfl' failed`. The `witness` requirement exists to close this, so
   audit the witnesses, not the outcomes.
2. **Whether a positive was reproven or neutered.** `variant_scope` blocks the
   crude evasions (`sorry`, a new `axiom`, a changed statement), but a positive
   whose impl is trivially the frozen one, or whose "different shape" is
   definitionally equal, tests nothing while passing honestly.
3. **Whether the prose is true.** Nothing mechanically checks that a
   `rationale` names the clause it claims, that a `refinement` argument holds,
   or that an omission recorded as inexpressible really is.

## The attacks that have found real defects here

Run these; they are not hypothetical. Each one caught something in the pilots.

**A. Statement integrity.** Extract every `theorem correct_*` statement (lean) /
`prove_correct` header (velvet) from every case's `module` and diff it against
the frozen file byte-for-byte. A case that reformats a statement while keeping
it logically equal still passes `same_spec`, and the reformatting is where a
weakened hypothesis hides.

**B. Witness discrimination, re-derived.** For every `expect="reject"` case,
build its witness twice yourself: against the rival (must succeed) and against
the frozen solution (must FAIL). Then read the gold-side failure: it must be a
SEMANTIC refutation of the concrete claim, not a missing identifier, a type
error, an unfolding failure, or a timeout. A witness that fails on gold for a
syntactic reason is not a discriminator, and the gate cannot tell the difference.

Each passing reject case now records the gold-side error it actually got, as
`gold_signature` in `meta.json`. Read those first — they say where to aim.

**B′. The FORGERY test — mandatory for any case whose `gold_signature` is not a
plain evaluation.** Reading an error and judging it "semantic" is not enough;
this has been wrong twice, in both directions. Do the two-line experiment
instead. A gold-side error is admissible evidence only if it CHANGES when the
claim changes, so build a second file that differs from the witness ONLY in what
it claims, and compare:

* **Flip the claim.** Assert the OPPOSITE of the witness (drop the `¬`, or swap
  `≠` for `=`) and build that against the frozen solution. If it fails with the
  byte-identical error, gold's exit code carried no information about the claim
  and the case is hollow — the gate would have recorded `rejected` for a witness
  asserting gold is CORRECT there.
* **Or reveal the type.** When the error is an application/type mismatch, replace
  the final `exact hv h2.symm`-style step with a deliberate type error on the
  hypothesis, e.g. `exact (h2 : Nat)`, and build it on each side. Lean then prints
  the hypothesis's REAL type. `has type True` means `simp` PROVED the equation for
  that impl; a concrete equation like `1.0 = v` means it did not. That pair is a
  genuine refutation. This is how the two largest signature classes in the corpus
  (`Application type mismatch … has type True`, `Invalid field symm … True.symm`)
  were established as real rather than hollow.

Report both builds' exit codes and the first error line of each in
`witnesses_rebuilt`, under `forgery_exit` and `forgery_error`. "It looks
semantic" is not a finding either way; the two errors are.

A hollow case is a defect you must FIX, not merely report: land a witness whose
failure tracks the claim (state the refutation over a computable projection, add
`decide +kernel` rewrites for the blocked steps, or give the case a
`witness_reference` — a VERIFYING impl of the same spec that does reduce). Only
if no such witness exists is the cell `CORRUPT`.

**C. Is the rival wrong, or just different?** For each reject case, ask whether
its impl differs from the frozen one OBSERVABLY, on this carrier. `Nat`
truncation, `Option` collapsing, list coercions, and clamps that are
definitionally equal are the usual traps: nagini kept a distinction this
carrier does not. If the rival is observably identical to gold, the case is
vacuous and must be dropped with a written reason.

**D. Tuned wrong impls (SPEC-TOO-WEAK probe).** Write NEW wrong implementations
the battery does not contain, aimed at whatever the existing rivals leave
unattacked, and check whether any of them VERIFIES against the frozen spec. One
that verifies is a genuine spec hole: report it as a finding on the SPEC, do not
patch it away. Use `scripts/pbt_coverage.py` to see which binders and clauses
are least probed and aim there.

**E. Correct reshapes (SPEC-TOO-STRONG probe).** Write NEW correct
implementations with a different shape and check they can be proven. Any
faithful correct impl the spec REJECTS is a soundness hole in the spec. Prefer
reshapes whose proof stays near the frozen one; if you cannot close a proof,
say so and mark it uncertain rather than claiming a hole.

**F. Omission re-derivation.** For each nagini case the port dropped, decide
independently whether it is inexpressible here. Give a per-case verdict. "The
carrier collapses this distinction" is a real reason and must be demonstrated;
"the proof was hard" is not, and is a finding.

One omission is measurably systematic, so check it explicitly: **the whole
`admissibility` lane.** 494 of the 500 nagini batteries carry an admissibility
positive. That lane is what detects PRECOND-TOO-STRONG, so dropping it silently
removes one of the three directions this gate exists to test. If this battery has no `kind="admissibility"` case,
either land one or state the demonstrated reason it is vacuous here. The reason
is NOT "the frozen obligation has no precondition": the analogue on a total
carrier is the obligation being unsatisfiable at exactly an F2P-shaped input,
which a positive that discharges the obligation at that concrete input — by
evaluation, as a `have`, before closing the frozen obligation verbatim — tests
directly. Sibling cells that already carry one show the shape.

Two reasons look like the first and are actually the second. Both are wrong:

* **"The carrier is opaque, so no witness can be built."** Wrong. Nothing has to
  PROVE an opaque guard: the witness states its refutation at a point described
  by HYPOTHESIS, and the gate's consistency probe then confirms
  the hypotheses are satisfiable — which an opaque term makes easy, since no
  tactic can derive `False` from `f v ≠ g v`. If the port dropped a rival for
  this reason, try to land it yourself before agreeing.

* **"The tactic I need is unavailable."** Check it. `decide` reduces the
  `Decidable` instance rather than computing, so it gets stuck on arithmetic that
  is decidable by other means: on `Rat`, `decide`/`simp`/`rfl`/`ring_nf` all fail
  and `norm_num` is unknown, but `simp [Rat.mul_def, Rat.normalize]` closes
  `(3 : Rat) * 4 = 12`.

A rival the port could not land for a TOOLING reason (a file the surgery leaves
uncompilable, an error whose text is not about the spec) is neither: it is a bug
to report. Say so with the error text.

**F′. The divergence lane, against the semantics the bundle actually sets.** Read
the frozen solution's `set_option loom.semantics.termination` line before judging
this class, because the two settings invert the correct disposition and a battery
written under one is wrong under the other:

* **`"total"`** — the verifier discharges a termination obligation, so a rival
  whose loop carries no decreasing measure is genuinely REJECTED. A battery that
  records this class as a known hole, or as vacuous, is now UNDERPORTED: the case
  is shippable and belongs in the reject lane. Add it (the nagini sibling's
  `diverge-*` / `nonterm-*` case is the design document), or say concretely why
  this bundle's carrier admits no diverging impl.
* **`"partial"`** — a non-terminating impl verifies vacuously, so no witness can
  refute it and there is nothing to ship. The disposition is "known hole", not
  "vacuous class": a vacuous class says the battery is complete, a hole says the
  spec is not. Do not spend builds re-measuring it.

**G. Coverage claims.** Run the coverage reporter. It is advisory, so a clean
report is not a pass — check that where it says a binder varies, the variation
is MEANINGFUL (values that actually change the spec's verdict) and not two
spellings of the same point.

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR={root} \
  python scripts/pbt_coverage.py --backend {backend_name} --instances {iid}
```

## Tools

Build any file with `scripts/lean_verify.sh <file>`; exit 0 is a successful
elaboration.

Put every scratch file under `/tmp` — never inside the bundle, and never
anywhere in the repository, including the repo root. Use a private directory,
e.g. `mktemp -d /tmp/pbt_audit.XXXXXX`, and do not create one named after the
instance in the working directory. G-INTEGRITY allowlists bundle contents, so a
stray probe file is a gate failure on a cell that was otherwise clean; a scratch
directory in the repo root can end up in the released artifacts. This applies to
every intermediate you write, including rival
modules, witness files, and build logs.

Never search from `/`. A tree-wide `find` can block for minutes on a large
repository. Search from the repo root with `Grep`/`Glob`, or scope a `find` to
the bundle root, `src/`, `scripts/`, or
`prompts/`. Everything you need is under one of those.

Do not run any git command that WRITES: no `checkout`, `stash`, `restore`,
`reset`, `clean`, `add`, `commit`. A tree-wide git operation can discard work
outside your cell. Read-only inspection (`git log`, `git show`,
`git diff -- <path>`) is fine — but prefer `git show HEAD:<path>` over anything
that touches the index, since a concurrent `git diff` can hold `index.lock`.

Re-run the real gate after any edit, and report ITS verdict, not yours:

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR={root} \
  python scripts/pbt_gate.py --backend {backend_name} {iid}
```

The mechanical scope check alone (`--validate-only`) is fast and has no
verifier; use it as your inner loop while editing, but it does not decide
anything about discrimination.

## What you may and may not change

- **May**: `properties.py` — fix a bad case, drop a vacuous one with a written
  reason, add a rival that closes a gap you found, correct a false rationale.
- **May not**: `{solution_filename}`, `meta.json` (the gate stamps it),
  `instance.json`, or anything under another instance. A defect in the FROZEN
  SPEC is a finding to escalate with the exact input that exposes it — a spec
  change must re-clear equivalence and leakage gates outside this lane.

Keep leak discipline in anything you write: `properties.py` ships. Do not quote
gold-patch lines, name the patched file/function, or narrate the bug-to-fix
mechanism. G-LEAK does not screen this file, so it is on you.

## Verdict

`SHIP` — every case earns its outcome, or does after your repairs.
`REPAIRED` — you found and fixed defects; the gate re-ran and still records pass.
`CORRUPT` — a defect you could not fix without touching the frozen artifact.
`SPEC-DEFECT` — attack D or E found a real hole in the frozen spec.

For every case, give an explicit per-case verdict. A case you did not
investigate is `unexamined`; do not silently fold it into a clean summary.
Report the exit codes you actually observed for each witness you rebuilt.

## The payload

Submit `pbt_audit` with these fields, under these names. The re-run gate
re-derives the pass/fail, so what this payload is FOR is the part no gate can
recover: which cases you examined and on what evidence. Prose in `notes` is
truncated and not machine-readable, so evidence that belongs in a field must go
in that field.

```
verdict              SHIP | REPAIRED | CORRUPT | SPEC-DEFECT
cases                [{{id, verdict, evidence}}] — one per case in SPEC_TESTS,
                     `unexamined` allowed, never implied
witnesses_rebuilt    [{{id, rival_exit, gold_exit, probe_exit, forgery_exit,
                     forgery_error}}] for every reject case whose builds you
                     re-ran. The forgery pair (attack B′) is required for any
                     case whose `gold_signature` is not a plain evaluation;
                     `forgery_error` is the first error line the flipped-claim
                     or type-revealing build printed.
attacks_tried        [{{id, kind, outcome}}] — your NEW rivals and reshapes
                     (attacks D and E), including the ones that failed
spec_holes           [] unless you found a hole in the FROZEN spec. A hole is
                     {{input, clause, why}}. Do NOT write prose here to say you
                     found none — an empty list says that, and a sentence
                     beginning "none ..." reads as a finding.
omissions_reviewed   [{{nagini_case, verdict, evidence}}] — one entry per nagini
                     case the port dropped (attack F). `verdict` is
                     `inexpressible` or `expressible` (the latter is a finding:
                     say what would land it). This is a LIST, not a paragraph
                     in `notes`.
edited               true if you changed properties.py
regate_verdict       the re-run gate's recorded verdict
notes                anything that has no field above
```
