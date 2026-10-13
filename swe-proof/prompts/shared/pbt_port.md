# G-PBT battery PORT — {iid}: {src_backend} → {backend_name}

This instance already has a validated G-PBT battery for the **{src_backend}** backend, at
`{root}/{iid}/{src_backend}/properties.py`. Your job: author
`{root}/{iid}/{backend_name}/properties.py` by **porting** it. Every variant you write is a full
copy of the frozen `{root}/{iid}/{backend_name}/{solution_filename}`.

Read `prompts/shared/pbt_author.md` first — every rule there (deliverable shape, editable regions,
the `_swap` region-surgery discipline, the six proof-gap failure classes, and the two mandatory
self-checks) binds you unchanged. This file only says what is different about a PORT.

## Why this is a port and not a re-derivation

The {src_backend} battery already did the expensive part: it worked out, from this task's gold patch
and F2P tests, **which weakness classes this task's behaviour actually admits** and what each
rival's refinement argument is. That analysis is language-independent and you should reuse it
verbatim where it applies. What you re-derive is only the **expression** of each case in
{backend_name}.

Concretely:
1. Read the source battery end to end, including its module docstring. The docstring names the
   DISCRIMINATORS the spec defends — that list is your case plan.
2. Read this backend's frozen solution file. Locate the clause that carries each discriminator here.
   The two specs model the same behaviour but not necessarily with the same decomposition: a single
   nagini `Ensures` may become one conjunct of a lean `problem_spec_*`, or an equality against a
   `pure`-region definition in velvet. `{root}/{iid}/{backend_name}/mapping.md` is the symbol/type
   bijection: the source rivals are stated over the SOURCE carrier, and it says what they become.
3. Re-express each source case against THIS spec's clauses. Keep the source case's `id` where
   the case survives, so the three backends' batteries are diffable cell by cell.
4. Carry over each rival's `refinement` argument — it is about the real patch and the real F2P
   tests, so it does not change between backends. Re-word only if this backend's model makes a
   different aspect load-bearing. Carry the ARGUMENT, never the prose: text naming the source
   backend's own machinery (nagini's `PSeq`, `Acc(x,1/2)`, `Requires`) means nothing here.

## What does NOT port — check each of these explicitly

Porting mechanically is the documented way to get this wrong. For every case you drop, say why in
`assessment`; a case dropped because it was hard to PROVE is a finding to report, not an omission.

- **Frame / permission mutation.** nagini's MANDATORY frame-mutation rival attacks
  Viper's permission system (a store through `Acc(x, 1/2)` must fail for
  insufficient permission). lean and velvet inputs are immutable values: no frame,
  no permission, nothing to mutate. The case is not expressible. Drop it; do not
  invent an analogue.
- **Termination / divergence — OUT OF SCOPE for velvet and lean. Do not author a
  divergence rival, even when you can make one verify.** This is a settled lane
  disposition, not a judgement call, and it is the one rule agents get wrong here:
  a velvet file that declares `set_option loom.semantics.termination "partial"` is
  making a deliberate, G-HYGIENE-checked statement that its proof obligation is
  PARTIAL correctness. A rival that loops forever therefore verifies *by the
  declared semantics*. Reporting that as SPEC-TOO-WEAK does not expose a defect in
  this cell's postcondition — it restates the `set_option` line, and it would
  "flag" every one of the 135 pro velvet cells set to `partial` identically. It is
  also inconsistent with the standard the benchmark already ships to: the
  500-bundle verified round passed G-PBT 500/500 without ever counting divergence
  as a finding.
  Measured 2026-08-17: 9 of the first 12 velvet SPEC-TOO-WEAK verdicts were
  divergence-only, and all 9 were `termination "partial"` cells — i.e. the entire
  signal was this one class.
  So: no `rival-diverge`, `rival-nonterminating`, `rival-nonprogress-loop`,
  `rival-hang-*`, `rival-vacuous-exit-*`. If nagini's battery had such a rival,
  DROP it and say so in `assessment`. (nagini keeps the class because Viper's
  `MustTerminate` is a real, per-function obligation there that a spec can carry or
  omit — 50 of 238 pro nagini specs carry it. Velvet's setting is file-global and
  already declared, so there is nothing per-cell to discover.)
  Attack what the postcondition says about VALUES, ORDER, DOMAIN and ERROR
  CHANNELS instead — that is where a real velvet weakness lives.
- **Payload cases.** If the source spec pins an error message and this one models
  the error as a contentless signal (or vice versa), the wrong-payload rival exists
  in exactly one of the two batteries. That is a real modelling difference, not an
  omission — record it.
- **Axiom cases.** Check this bundle's `meta.json`. Many velvet/lean pro bundles
  have `axioms: []`, in which case there is nothing to port and `AXIOM_TESTS = []`
  regardless of what the source battery had. Never invent axiom cases for an empty
  axioms region.

## What ports well

The spec lane transfers almost completely. Uniqueness rivals that encode a WRONG BEHAVIOUR
(accept-unknown, swapped mapping, over-rejection, partial-domain, ungrounded-oracle echo) are
behavioural claims and re-express directly. So do soundness positive controls, though their PROOFS
do not: expect to write a new tactic body for every restructured positive control (failure class 3
in `pbt_author.md` — this is where nearly all first-try failures land). Admissibility positives port
too, even where the target obligation has no explicit precondition (`pbt_author.md` says what to
state instead); almost every source battery carries one, so a port that ships none is usually a
dropped case rather than a vacuous class.

velvet ↔ lean port freely: they share the Lean v4.24.0 workspace and the same `same_spec`
discipline, so a rival impl is a `Solution.lean` variant either way. nagini → {{velvet,lean}} is
a port of the CASES but a re-derivation of the LANGUAGE — do not expect source text to survive.

## Case-count parity with the source is NOT the target

Lean-family bundles model only the purely functional core and typically carry exactly ONE obligation
(`theorem correct_*` on lean, `prove_correct` on velvet) where the {src_backend} sibling contracts
five or more functions, so most source cases attached to an unmodeled behaviour have no counterpart
at all. A port shipping 3 cases against a source battery's 17 is usually CORRECT — that is carrier
narrowing, and chasing parity would push you to fabricate rivals for behaviours this bundle does not
model. What replaces parity is coverage of the surface it DOES model: every obligation **defended**
(>=1 `expect="verify"`) and **attacked** (>=1 `expect="reject"`); every independent top-level clause
of the postcondition attacked by some rival; and every INPUT BINDER **varied** by the reject
witnesses — a binder every witness holds at one value is one no rival was built to abuse, so a rival
mishandling only that input would verify unnoticed. Two rivals may share a witness only if they
really fail at the same input for the same reason.

### A battery with no reject case at all is a gate ERROR

`NO-REJECT-LANE`. Not a fail — nothing says the spec is defective — but not a pass either:
SPEC-TOO-WEAK is detectable ONLY by a rival that verifies, so with zero rivals "every case behaved
as expected" collapses into "every correct impl verified", and the gate refuses to spell that
SOUND. It looks unavoidable when the carrier is largely OPAQUE (`opaque` callees with no constraining
axiom, so `decide` sticks on the opaque term), and **that conclusion has been reached before and been
wrong every time**. Assume the lane is expressible until you have tried, in order: condition on the
carrier instead of computing it (below); attack what IS transparent (lengths, ordering, container
shape, which branch fires, how the opaque results are COMBINED); attack the argument rather than the
result (`f a ≠ f b` is not a theorem, but `xs.map f ≠ (xs.reverse).map f` often is, for a concrete
non-symmetric `xs`); and widen the input, since an opaque callee under a LIST or `Option` leaves the
traversal and the `none` handling transparent. Only if all four fail: do NOT fabricate a rival and do
NOT ship positives-only. Say so in `assessment` with the exact term that blocks refutation and let
the cell surface as an unresolved gate error — a known gap, where a hollow SOUND would be a corrupt
benchmark.

### Conditioning on the carrier

An opaque term has no VALUE you can compute with, but it is still a term you can QUANTIFY over.
State the refutation at a point described by hypothesis:

```lean
example (h : valueHash 5 ≠ 0) : choiceValueHashExec 5 ≠ DivM.res (valueHash 5) := by
  unfold choiceValueHashExec choiceValueHash; simp [NonDetT.run, pure]; omega
```

Against a rival returning the constant `0` this elaborates; against gold `omega` fails for want of a
counterexample. Its claim — *whenever the callee's result differs from the constant, the rival's
answer differs from the spec's* — is exactly the sub-domain where the rival is wrong.

Such a witness gets a third check: the gate tries to derive `False` from your binders alone, because
**an inconsistent hypothesis proves anything**. Binders that cannot both hold (`h1 : valueHash 5 = 0`
with `h2 : valueHash 5 = 1`) let you `rw [h2]; decide` — elaborating against the rival, failing on
gold, attributing nothing to the spec. That is `witness-inconsistent` and forces MALFORMED-TESTS, so
keep assumptions as weak as the refutation needs: two hypotheses about the SAME opaque term are the
shape to re-read before shipping.

## Manifest contract: the two keys a port adds

`SPEC_TESTS`, its per-case keys (`id`, `kind`, `expect`, `module`, `rationale`, `refinement`) and
the `_BASE`/`_swap` drift discipline are `pbt_author.md`'s and bind unchanged. A port to a
tactic-proof backend adds two:

- `witness` — REQUIRED on every `expect="reject"` case (see below). A battery ported from a
  verifier-oracle backend like nagini has no counterpart to copy, and this is what sinks most ports.
- `witness_reference` — OPTIONAL, and only for cells where the frozen impl cannot decide anything:
  a correct variant source for the witness to be refuted against instead of gold. See "When the
  FROZEN impl is what will not reduce".

Every case is checked by `variant_scope.variant_problems` BEFORE the verifier runs; a violation is
MALFORMED-TESTS (a gate error), not a finding. Beyond `same_spec`: **the obligation survives** — on
lean every `theorem correct_<name>` still present with a byte-identical STATEMENT, only the tactic
body changing; on velvet every `prove_correct <name>` header still there — and **nothing is
assumed**: no new `axiom`, `sorry`, `admit`, `native_decide`, no new `theorem`/`lemma` beyond the
frozen set. Both exist because the spec view ELIDES the impl and proof regions: `same_spec` alone
would accept `theorem correct_X : True := trivial`, which elaborates cleanly and would record a
G-PBT pass having nothing to do with the spec. If you cannot close a positive's proof honestly,
**drop the case and report it** — a dropped positive is a known gap, a faked one is corrupt.

## The witness: why every reject case needs one here

A reject case on nagini can rely on the verifier: Viper discharges the postcondition itself, so
"did not verify" means the contract does not hold. On a tactic-proof backend that inference is
INVALID. The frozen proof script is tuned to the frozen impl's syntactic form (`intro a b; rfl`
is the commonest shape), and reshaping the impl is exactly what a rival does — so a merely
RESHAPED impl fails to build identically to a WRONG one:

    return (a.rest == b.rest) && (a.code == b.code)    -- gold: `rfl` closes
    return (a.code == b.code) && (a.rest == b.rest)    -- correct, commuted: FAILS
    return (a.rest == b.rest)                          -- wrong, drops a conjunct: FAILS

All three end in `Tactic 'rfl' failed`: tactic breakage is the DEFAULT outcome of reshaping an
impl, so essentially EVERY reject case would otherwise pass vacuously — a battery attesting to
spec strength while testing nothing. So each reject case carries a `witness`: a Lean snippet
proving the rival violates the spec at one CONCRETE input, checked in a file where the frozen
obligations have been removed (so no tactic script can interfere), which must (1) ELABORATE against
the rival and (2) FAIL against the frozen solution. Half 2 is what makes it a discriminator:
`example : 1 = 1 := rfl` passes half 1 trivially.

**lean** — state the spec predicate directly at a concrete input:

```lean
example : ¬ problem_spec_f {{ code := some "A" }} (implementation_f {{ code := some "A" }}) := by
  unfold problem_spec_f implementation_f; decide
```

**velvet** — the spec is a `method` contract, not a bare predicate, so use Velvet's own tester
machinery to reach it:

```lean
extract_program_for constraintsEqual
prove_precondition_decidable_for constraintsEqual
prove_postcondition_decidable_for constraintsEqual
derive_tester_for constraintsEqual
example : constraintsEqualTester true (some "A".toList) (some "B".toList) = false := by decide
```

Prefer a `decide`-able input: concrete literals, small values, no opaque terms; when the carrier
will not compute, condition on it instead (above). `sorry`, `admit` and `native_decide` are rejected
outright — they would make the witness elaborate against gold too, defeating both halves at once.

If you cannot construct a discriminating witness even by conditioning, that rival is **not actually
wrong on this backend's carrier** (its abstraction may collapse a distinction the source carrier
kept): drop it and say so in `assessment`, and never ship a reject case whose witness you have not
seen discriminate. A witness that fails for a TOOLING reason is different, and is no licence to ship
a thinner battery: report it with the error text so the tooling gets fixed instead.

### When `decide` gets stuck on a literal

`decide` reduces the `Decidable` instance, which is not the same as computing the value, so it can
fail on arithmetic you would expect to be trivial. Do not read that as "this input is not
decidable" — unfold the operation for `simp` instead. On `Rat`, where `decide`, `simp`, `rfl` and
`ring_nf` all fail and `norm_num` is not even a known tactic in the workspace,
`example : (3 : Rat) * 4 = 12 := by decide` sticks at `(Rat.mul 3 4).num` while
`by simp [Rat.mul_def, Rat.normalize]` closes it. The pattern generalizes: find the
`_def`/unfolding lemma for the operation and the normalizer it produces, and hand both to `simp`.

### When the FROZEN impl is what will not reduce (`witness-undecided`)

Half 2 asks the witness to FAIL against the frozen solution, which is evidence only if the frozen
side *decided* something. When the frozen impl keeps a `while` loop it does not: under
`loom.semantics.choice "demonic"` the loop's fixpoint elaborates through `Classical.choice`, which
the kernel cannot unfold, so `decide` against it is stuck for **every** claim, true or false — the
real witness, its exact opposite, and a trivially true claim alike, all with the identical `did not
reduce to isTrue or isFalse`. The frozen-side exit code then carries no information, and a forged
witness asserting the rival is *correct* would clear both halves, so the gate reports
`witness-undecided` and refuses the case.

**The loop is not the only thing that can block reduction.** A whole reject set has been stuck
alongside a *loop-free* impl, where the blocker was `Rat.inv`: it does not reduce in the kernel, so
**any `Rat` division stalls whatever encloses it** however the control flow is written. Find out
which term is actually stuck before reaching for a loop-free reference — build a trivially true
claim about the impl and see whether it decides. The reference has to be **kernel-reducible**;
loop-freeness is only one way to fail that. Ways out, in order of preference:

1. **State the refutation over a computable projection** — a claim whose reduction does not go
   through the loop (a sum, a length, a single coordinate).
2. **Supply the blocked steps as kernel-decided rewrites.** `decide +kernel` settles individual
   arithmetic facts even where `simp` cannot: `simp [Rat.div_def, Rat.mul_def, Rat.normalize,
   Rat.inv]` does **not** close these, but
   `simp only [show ((1:Rat) + 3) / 2 = 2 by decide +kernel, …]; decide +kernel` does.
3. **Give the case a `witness_reference`** — a full variant source (`_swap` the frozen loop body
   for the value computed directly) that *does* reduce and implements the frozen spec CORRECTLY.
   The gate refutes the witness against that instead of against gold, after checking the reference
   shares the frozen spec and **verifies**; an impl that failed everything would refute every
   witness, so an unverified one is rejected (`witness-reference-invalid`). Pair it with an
   `expect="verify"` case carrying the same source, so the battery records that loop-freeness is
   not what any rival is being rejected for. One reference serves the whole battery.

## Backend mechanics

**lean** — the variant is a complete `{solution_filename}`; a positive with a different impl shape
needs a proof that closes for the NEW impl, reproved inside `-- proof-start` / `-- proof-end`.
Prefer shapes whose proof stays close to the frozen one (branch reorder, `let`-inlining, an
equivalent arithmetic form) where `decide`/`simp`/`omega`/`grind` may suffice; a shape needing a
genuinely new lemma is the expensive mistake, since each case is a real `lake` build.

**velvet** — the variant is a complete `{solution_filename}` (the `method`/`require`/`ensures`
triple). Proofs are discharged by `loom_solve`, so a correct positive usually needs no proof
authoring; keep the `prove_correct` block as-is.

## Comments: no leakage

`properties.py` is part of the released bundle. G-LEAK is lexical: do not quote gold-patch lines,
name the patched file/function/symbol, or narrate the bug→fix mechanism. Describe behaviour
abstractly, exactly as the frozen spec does.

## Self-validate before you finish

The rule is `pbt_author.md`'s unchanged: every case must pass `same_spec`, and every case must be RUN
until its actual result matches its declared `expect` — a port is not finished while any case's
outcome is unobserved. Use this repo's own entry points; do not invent a verifier path.

```bash
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR={root} \
  python scripts/pbt_gate.py --backend {backend_name} {iid} --validate-only
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR={root} \
  python scripts/pbt_gate.py --backend {backend_name} {iid} --no-record
SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR={root} \
  python scripts/pbt_coverage.py --backend {backend_name} --instances {iid}
```

The first is the mechanical scope check: no verifier, fast, every case must report `scope-ok` — but
it checks witness SHAPE only. The second runs the real builds and prints each case's outcome beside
its `expect`; iterate until none disagrees (`pbt_author.md` says how to read a disagreement). Check
a witness yourself with `scripts/lean_verify.sh`: it must build against the rival and fail against
the frozen solution. The third is coverage, which the gate does NOT check — a two-case manifest
passes G-PBT exactly as loudly as a twelve-case one. It reports per-obligation and per-binder
coverage plus `pts=`, the number of distinct input points your reject witnesses probe; `pts=1` means
every rival is refuted at the SAME input, so the battery says nothing about the spec's dependence on
any binder. Each finding is a rival to add or a witness to move to a more discriminating input; one
you judge not applicable belongs in `assessment`.

Put every scratch file in `/tmp` — never inside the bundle, and never in the repo root.
G-INTEGRITY allowlists bundle contents, so a stray probe file fails the gate on a cell that was
otherwise clean, and a scratch directory in the repo root can end up in the released artifacts.

Do not run any git command that WRITES: no `checkout`, `stash`, `restore`, `reset`, `clean`, `add`,
`commit` — a tree-wide git operation can discard work outside your cell, and other cells are
mid-write at the same time. Read-only inspection (`git log`, `git show`, `git diff -- <path>`) is
fine; to see a file's pre-existing state, read the {src_backend} sibling or use
`git show HEAD:<path>`, never a checkout.

Then submit the `pbt_author` payload: `status`, `n_spec_cases`, `case_classes`, `assessment`
(which source cases ported, which were dropped and why, which needed a new tactic body, any
positive dropped because its proof would not close, and any suspected finding), `notes`. Report
the recorded gate verdict, never a self-assessment.
