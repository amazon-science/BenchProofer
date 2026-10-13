# Architecture: the construction loop and the gate suite

This document describes what the pipeline builds, how it builds it, and why the
gate suite has the shape it does. It is the reference for the other three docs:
[reproducing.md](reproducing.md) (run it), [adapting_a_benchmark.md](adapting_a_benchmark.md)
(point it at a different benchmark), [adding_a_backend.md](adding_a_backend.md)
(teach it a new verification language).

## 1. The artifact and the claim

The input is a software-engineering benchmark whose rows each carry an issue, a
repository at a pinned commit, a reference (gold) patch, and a hidden test set
that decides whether a candidate patch resolves the issue. The output is a
**verified twin** of each row: a formal specification of the behavior the issue
asks for, a machine-checked implementation satisfying it, and a set of
refutation artifacts that make the pair falsifiable.

One (instance, backend) pair produces one **bundle**. The bundle asserts a
biconditional:

    verify(impl, spec)  ==>  resolve(patch)          the spec is strong enough
    resolve(patch)      ==>  verify(impl, spec)      the spec is not too strong

Both directions can fail, and they fail differently. A spec that accepts a
wrong implementation (SPEC-TOO-WEAK) breaks the first: a solver can satisfy the
formal obligation and still not fix the issue, so a verified answer is not a
correct one. A spec that rejects a correct implementation (SPEC-TOO-STRONG, or
its precondition variant PRECOND-TOO-STRONG) breaks the second: the instance is
unsolvable by a faithful patch that happens to take a different shape, so the
measurement understates the solver. Every gate in the suite exists to attack one
of those two directions, or to protect the inputs the attacks depend on.

Because the claim is about a *relationship* between artifacts, none of it can be
established by the party that produced them. The pipeline therefore never treats
a producing agent's self-report as evidence. Every "ok" in a bundle comes from a
mechanical re-check performed after the fact by code that does not write the
bundle. That single rule explains most of the structure below.

## 2. The bundle on disk

```
<root>/<instance_id>/                 immutable inputs, shared by all backends
  instance.json                       the frozen dataset row, verbatim
  patch.diff                          the reference patch
<root>/<instance_id>/<backend>/       one constructed bundle
  <solution file>                     spec + implementation (+ proof, if the
                                      backend has one), in marker regions
  <solution>_prepatch*.<ext>          pre-fix twins: identical spec, buggy impl
  <solution>_gold.<ext>               optional gold-faithful impl
  refinement.md                       op-by-op map from impl to patch.diff
  mapping.md                          formal symbol to repo symbol binding
  axiom_check.py                      runtime soundness probe for the axioms
  conformance_check.py                differential probe: impl versus real repo
  properties.py                       adversarial spec-strength battery
  pbt_result.json                     that battery's per-case outcomes
  meta.json                           gate verdicts + modeling metadata
  result.json                         construction outcome, when a driver wrote one
  verdict.md                          human-readable audit record
  RELAXED_LEAKAGE.md                  a reviewed leakage relaxation, if any
  BLOCKED.md                          why no bundle exists (terminal, by design)
```

`<root>` defaults to `benchmark/` and is set by `--benchmark-dir` or
`SBU_BENCHMARK_DIR`, so several benchmarks can be constructed side by side in one
checkout.

Grouping by instance first and backend second is deliberate: the formalizations
of one row sit next to each other, which is what a reviewer comparing them needs,
and the two immutable inputs are frozen once at the instance level instead of
being copied per backend where they could drift apart.

The **marker regions** are the load-bearing convention. The solution file is
divided by line-comment sentinels (`axioms`, `pure`, `pre-conditions`,
`post-conditions`, `invariants`, `impl`, and for proof-carrying backends
`proof`), and almost everything downstream is defined in terms of them:

* the **spec view** is the projection that keeps signatures, contracts, axioms
  and pure helpers and elides the implementation and proof bodies. It is what a
  consumer of the benchmark is shown, what the anti-leakage gate certifies, and
  what defines when two files "share a spec".
* `same_spec(a, b)` compares spec views, so an adversarial variant of the
  solution provably differs only where it is allowed to.
* mutation operates only inside the impl region, so a mutant never edits the
  contract it is being judged against.
* region hashes recorded in `meta.json` make a later edit to a frozen artifact
  detectable.

## 3. The construction loop

One driver builds one (instance, backend) cell. The phases are ordered so that
every expensive or nondeterministic step is bracketed by a cheap mechanical
judgment.

**P0 prepare.** Freeze the dataset row into `instance.json` and the reference
patch into `patch.diff` at the instance root, stamp the bundle's provenance, and
materialize a throwaway worktree of the repository at `base_commit`. Freezing
first is what makes the integrity gate meaningful later: the row the bundle was
built against is a committed artifact, not something re-fetched at judgment time.
The worktree lives outside the repository and is removed on every exit path,
including a signal from a driver's per-instance wall clock, because a corpus-wide
build that leaks worktrees exhausts the filesystem's inode budget long before it
runs out of disk.

**P1 construct.** A construction agent writes the specification and the
implementation into the bundle directory. Each round ends with two mechanical
checks: an *elaborate check* (the backend's checker must accept the file; for a
proof-carrying backend, "only the proof obligations remain open" is an accepted
intermediate state, keyed on the checker's exit code rather than on parsing its
output) and the CONSTRUCT gate subset, run in feedback mode. Failures are fed
back to the agent verbatim as counterexamples for up to `max_rounds` iterations.
Two properties of this loop matter:

* The feedback-mode gate results are **not recorded**. A verdict written into
  `meta.json` is a claim about a finished artifact; a verdict about a
  half-written one would be indistinguishable from it afterwards.
* The refine prompt instructs the agent to fix the counterexample and never to
  weaken a contract to make a gate pass. The gates cannot tell those apart in
  general, which is why the escape hatch is a *principled block*: an agent that
  cannot specify an instance inside its language's fragment writes `BLOCKED.md`
  explaining the wall it hit, and that is a valid terminal outcome. A weakened
  spec is not.

**P1.5 prove** (proof-carrying backends only). A separate proof driver closes
the obligations left open in P1. It is a distinct phase, not part of the
verification gate, for three reasons: a gate that searches for proofs is
nondeterministic, it mutates the artifact it is supposed to judge, and it
inverts the dependency direction (gates would depend on construction). After the
proof phase the verification gate re-judges the committed file mechanically, and
only that re-check can produce "ok". A self-reported success whose re-check fails
is treated as a plain retry.

**P1.8 author battery** (optional). One agent authors the adversarial
spec-strength battery (`properties.py`) against the now-frozen solution. It runs
after the construct-and-prove loop has closed, and before the recorded sweep below
judges it, because a battery is written *about* a specific frozen spec; authoring it
earlier would let the battery and the spec co-evolve, which is the one thing a
falsification battery must not do.

**P1.6 static sweep.** Every static gate, strict mode, recorded. This is the
first point at which the bundle's `meta.json` acquires real verdicts.

**P1.7 Docker gates.** The three gates that execute real repository code in the
instance's container image, run only if the static sweep is clean. Ordering is
purely economic: a container run costs orders of magnitude more than a lexical
scan, and a bundle that fails a static gate will not survive a Docker one.

**P2 audit** (optional). Three adversarial agents attack the finished bundle.
Their outputs are re-derived mechanically (section 6).

The driver writes `result.json` with `final_status` in `ok | blocked | timeout`,
where a gate `fail` or `error` maps to `blocked`. It is resumable: an
already-green cell is skipped unless forced, a principled block is terminal and
its `BLOCKED.md` is never clobbered, and a cell that becomes green has any stale
`BLOCKED.md` removed. The `--all` driver fans this out one subprocess per instance
so a fatal error cannot poison siblings, with a per-instance wall clock, and it
shuffles the instance list under a fixed seed so that any *prefix* of a run is a
uniform random sample of the benchmark. A partial run is therefore reportable,
which matters because full runs are long.

## 4. The gate framework

A gate is a pure, read-only judgment about a committed bundle. There are 13 gate
modules, one file each, and the registry's import order is the canonical
execution order (static first, Docker last):

| class | count | gates |
|---|---|---|
| static (mechanical) | 8 | G-VERIFY, G-DIFF, G-GOLD, G-MUT, G-PBT, G-INTEGRITY, G-HYGIENE, G-LEAK |
| Docker (mechanical) | 3 | G-RESOLVE, G-CONF, G-AX |
| agentic | 2 | G-EQ, G-PANEL |

The 11 mechanical gates are what `ALL_GATES` names and what the gates CLI runs by
default. The 2 agentic gates *read* verdicts that the P2 audit stage recorded;
running an audit agent is construction work, never gate work, for the same reason
the proof agent is not inside the verification gate.

Framework invariants, all of which exist because the suite is meant to be re-run
later by someone who did not build the bundle:

* **Not applicable is an explicit, stamped skip.** When a gate does not apply to
  a backend, the runner records a skip with a reason rather than leaving the key
  absent. A missing verdict and an inapplicable gate are different facts, and
  collapsing them would let an unjudged bundle read as a judged one.
* **`mode` is recorded.** Construction-time leniency is an explicit
  `mode="feedback"` argument, written into the result, so one gate name never
  silently means two different things.
* **Statuses are `pass | fail | skip | relaxed | error | timeout`**, and `ok` is
  `pass`, `skip`, or `relaxed`. `error` and `timeout` are deliberately not
  failures: they say the gate could not decide, which must not be recorded as a
  judgment that the artifact is defective.
* **Every verdict is stamped** with a UTC timestamp, a code version, and a
  `harness_digest`: a hash over the sources that actually reach a verdict (the
  gates package plus the variant-admissibility and witness modules). A version
  string derived from the working tree is not usable as provenance here, because
  a tree in which drivers are writing artifacts is dirty essentially always. The
  digest changes exactly when the judge changes, which is the question a consumer
  of a released bundle is asking.
* **Recording is atomic.** `meta.json` is written to a pid-suffixed temporary
  file and renamed, because a corpus-wide run has many gate processes writing
  while classifiers and the next gate run are reading, and a plain
  truncate-then-write lets a reader observe a bundle with no verdicts at all.
* **A harness error never overwrites a verdict.** An exception escaping a gate
  body is a bug in the judge, not a finding about the bundle. The caller still
  sees `error` and still treats the cell as unfinished, but the recorded verdict
  survives.
* **Operator knobs survive re-runs.** Per-cell timeout overrides and the audit
  record fields are preserved across re-recording, since the agentic gates read
  their own verdict back out of that record.

## 5. What each gate checks, and why it exists

### Static

**G-VERIFY** the committed solution passes the backend's checker. This is the
weakest gate in the suite and the one most easily mistaken for the whole claim:
it says the implementation satisfies the spec, and says nothing whatever about
whether the spec describes the issue. Everything else in the suite exists
because G-VERIFY is not enough. For a proof-carrying backend it additionally
requires that each obligation is genuinely closed rather than merely elaborating.

**G-DIFF** every pre-fix twin *fails* verification under the byte-identical
spec. This is the discriminating-power check: it establishes that the spec can
tell the buggy behavior from the fixed behavior. A spec that both the pre-patch
and the post-patch implementation satisfy has not captured the issue at all, and
G-VERIFY alone would happily pass it.

**G-GOLD** the gold-faithful implementation verifies and the pre-patch twins
still fail. When the bundle ships no separate gold-faithful file, the shipped
solution *is* that implementation and the gate reduces to G-VERIFY plus G-DIFF.
It is kept as its own gate because the reduction is a property of the current
bundle shape, not of the pipeline.

**G-MUT** first-order mutants of the impl region are killed at or above a
per-backend rate. This is a spec-tightness *floor*, not a correctness proof, and
it is important not to over-read it. Mutants are generated one token at a time
inside the impl region only. An assignment-heavy implementation yields few
mutants; on a proof-carrying backend a mutant may fail for reasons unrelated to
incorrectness, since the frozen tactic script is tuned to the frozen impl's
shape. G-MUT catches a grossly under-constrained postcondition cheaply. The real
spec-strength checks are G-PBT and G-PANEL.

**G-PBT** hand-authored adversarial variants from the bundle's battery behave as
declared. This is the only gate that attacks spec strength in *both* directions.
Each case is a full solution-file variant that must share the frozen spec and
stay inside the admissible variant scope; the verifier's accept or reject is
compared against the case's declared expectation:

| kind | expectation | a violation means |
|---|---|---|
| `uniqueness` | reject | SPEC-TOO-WEAK: a wrong impl verifies |
| `soundness` | verify | SPEC-TOO-STRONG: a correct impl is rejected |
| `admissibility` | verify | PRECOND-TOO-STRONG: a normal input is refused |

Contracts are not runtime-executable (static verifier markers on the imperative
side, propositions on the proof side), so the only available oracle for a spec
variant is the verifier itself. The complementary runtime lane, fuzzing the
axioms against the real callee, is G-AX and is deliberately not duplicated here.

**G-INTEGRITY** `instance.json` is equal to the frozen dataset row, the row's
reference patch is non-empty, and the instance root and bundle directory contain
only allowlisted entries. The first half prevents the quietest possible failure:
a bundle built against a row that has since changed, or against a row that was
edited to be easier. The second half is an additions-only discipline. An
allowlist rather than a denylist means an artifact a gate cannot read has no
business existing in a released bundle, so a file that *looks* load-bearing but
is dead fails the gate instead of misleading a reader.

**G-HYGIENE** the static scan: markers parse, the spec view is idempotent under
re-projection, imports are within the backend allowlist, no banned token appears,
region hashes are recorded, plus per-backend requirements (the obligation is
actually stated; the axiom mechanism is confined to the axioms region; declared
encoding knobs are actually used; for a natural-language backend, the document is
well-formed and its consulted sources are recorded). Banned tokens are the
central point: `sorry`, `admit`, `native_decide` and their analogs discharge an
obligation without proving anything, and an assumption facility used outside the
axioms region is an unchecked postcondition wearing a spec's clothes.

**G-LEAK** the spec view does not reveal the fix. A consumer who is handed the
spec must not be handed the answer with it: no reproduced diff line, no diff
markers, no patched file path, no spec-view identifier echoing a patched repo
symbol, no narration of the bug or its fix. Two design choices matter. Leakage is
judged against the *solver-visible* problem statement only and never against any
auxiliary hints field, because a term that appears only in hints is a term the
solver does not have, so echoing it leaks. And a documented, reviewed relaxation
is honored even when the lexical screen passes: a semantic leak that a reviewer
accepted (because the behavior genuinely cannot be specified without naming the
symbol) is recorded as `relaxed`, and the gate must not overwrite that with a
misleading "screen clean" pass.

### Docker

These three run real repository code inside the instance's official container
image. They are the only construction-time steps that do.

**G-RESOLVE** `patch.diff` resolves the instance under the benchmark's own
correctness oracle, with the hidden tests unchanged. This is the anchor of the
whole construction: it is what makes "resolve" a fact about the row rather than
an opinion about the bundle. Two policies are worth naming. A resolve verdict is
content-addressed by the patch, because a harness that caches per-instance
reports will otherwise short-circuit and hand back a verdict computed for a
different patch. And a run that never *completed* (a timeout, an image pull
failure, a container the daemon refused) is a failed measurement, not a verdict:
it is retried and reported as incomplete, never as "did not resolve". Conflating
the two is how host load turns into apparent defects in artifacts.

**G-CONF** differential conformance: an executable shadow of the formal
implementation is compared against the real patched repository function over a
large fuzzed input set with a pinned seed. This gate exists because verification
says nothing about the gap between the formal model and the code it claims to
model. The shadow and the oracle are different programs: a simplified
implementation over modeled types versus the full real codebase. They can
disagree on edge cases, on lossy type modeling, or on a restructuring that was
not behavior-preserving, and any disagreement is a mechanical fidelity
counterexample. The gate **refutes** fidelity and never proves it.

How the shadow is obtained is the backend's business, and the difference is the
most important trust distinction in the pipeline. When the specification language
is the repository's own language, the shadow is the impl region with contracts
stripped, run directly: there is no transliteration gap. When the specification
language is not executable (axioms have no bodies, method bodies target a
verification monad, real-number types are noncomputable), the shadow is an
agent-written transliteration, which is the least-trustworthy link in the chain.
The gate records which provenance it used, so a consumer can weight it.

An implementation with no directly executable content is an explicit skip with a
reason, and the weight of the fidelity claim shifts onto G-AX and the audit
gates. A shadow that reports constructs it cannot model is likewise an explicit
skip, never a silent pass.

**G-AX** axiom soundness: for each axiom standing in for an unchanged callee, the
bundle's probe generates inputs satisfying the axiom's precondition, calls the
*real* callee, and asserts the axiom's postcondition holds of every observation.
Axioms are the pipeline's assumption surface. An unsound one is strictly worse
than a missing proof, because it discharges obligations while being false. Since
axioms model *unchanged* callees, the probe runs at `base_commit` by default,
with an opt-in for the patched tree where a bundle legitimately needs it.

### Agentic

The mechanical gates are all refuters with a fixed search space: mutation
operators, a manifest of authored cases, a fuzzer's input distribution. The two
agentic gates are where an open-ended adversary attacks the bundle. Their outputs
are never trusted as verdicts; see section 6.

**G-EQ** refinement-fidelity attack. The auditor hunts for an implementation that
shares the frozen spec, verifies, and whose faithful real patch does *not*
resolve the instance. That triple is a machine-checked witness that verification
does not imply correctness for this bundle. Because G-CONF has already
mechanically probed the type-refinement and identity legs of the refinement
relation, this attack concentrates on the axiom legs, where no mechanical
refuter reaches.

**G-PANEL** a blind attacker panel with three roles, recorded as three separate
verdicts:

| role | attacks |
|---|---|
| G-PANEL-1 | spec too weak: any same-spec implementation that verifies |
| G-PANEL-2 | faithfulness: does the model actually model *this* repository behavior |
| G-PANEL-3 | leakage: does the spec view give the fix away |

Roles 1 and the G-EQ attack share one agent, since they perform identical attack
work and differ only in how the resulting facts are scored. Roles 2 and 3 are
judgment roles: there is no executable oracle for "the modeling boundary is
wrong", so those verdicts are evidence-gated rather than machine-derived. The
commonest genuine faithfulness defect is a wrong modeling *boundary*, and the
repair is to correct the model, not to tighten it until the complaint goes away.

## 6. Making an adversarial audit into evidence

An audit whose verdict is the auditor's opinion is worth nothing, so every
audit claim is re-derived from the submitted artifacts by code the auditor does
not control.

For the mechanized roles the substrate is small and total. For a
verifier-backed backend it answers two questions about an attack file: does it
share the frozen spec view, and does the verifier accept it. A file that shares
the spec and verifies is only a **candidate**; it becomes a finding only when the
auditor's corresponding refined patch is run through the real oracle and does
*not* resolve. A candidate whose patch does resolve is a correct alternative
implementation, an echo of the reference solution rather than a spec weakness,
and must not fail the gate. For a backend with no verifier at all, the same role
is played by executable probes: standalone scripts encoding behavior a cited
requirement mandates, run inside the instance image against the patched tree, the
base tree, or an alternative patch. A probe that fails on the patched tree is a
violation candidate; an alternative patch that satisfies every probe yet does not
resolve is a too-weak finding; and a positive control must fail at base and hold
when patched, which is the discriminating-power check transposed.

Four further rules make the derivation hard to game:

* **The floor.** A clean pass requires a minimum number of distinct attacks, a
  reproduction of the known pre-patch bug, and a structurally different positive
  control that verifies. Absent any of those, the verdict is INCONCLUSIVE and
  fails closed. "I looked and found nothing" is not a pass unless the search is
  demonstrably capable of finding something.
* **Attack paths are canonicalized and deduplicated**, so the floor cannot be met
  by listing one file under several spellings.
* **The floor counts admissible attacks, not submitted files.** Two kinds of file
  are excluded, because neither is evidence about the specification under audit.
  One changed the spec, so it asks a different question. The other kept the spec
  but would take its exit code by assuming rather than establishing: it drops the
  proof obligation, asserts a new axiom, reaches for a proof-eliding tactic, or
  stubs a contract out. Both are recorded as "not a counterexample" rather than as
  rejections, since the verifier never ruled on them and a tally of rejections the
  specification never performed is exactly the false confidence the floor exists
  to prevent. The same screen keeps such a file from being promoted to a
  candidate, which would accuse a sound specification of admitting an
  implementation nothing ever checked.
* **Verifier timeouts and incomplete oracle runs are inconclusive**, never
  "does not verify" and never "did not resolve". Treating a failed measurement as
  a negative result would let load on the machine mask a real weakness.

An audit that cannot decide is retried, and the derivation is memoized per
(instance, patch) since resolving is a pure function of that pair. The result is
written both into `meta.json` and into an inspectable `verdict.md` that lists
each attack with the outcome the runner derived for it, so the record can be
audited without re-running anything.

One asymmetry is deliberate: the leakage role defers to an accepted leakage
relaxation. If a reviewer already accepted a semantic leak, a fresh leakage
finding for the same reason is not a new defect, and it is recorded as a pass
with a note rather than as a failure.

## 7. Spec-strength machinery

The G-PBT battery and the audit both rely on a shared notion of "a variant that
differs only where it is allowed to". Getting that notion wrong is the strongest
possible failure mode for this benchmark, because it produces a bundle that reads
as certified while nothing was tested. Four mechanisms close four distinct holes.

**Admissible variant scope.** `same_spec` compares spec *views*, and the spec
view elides the impl and proof regions. Elision is right for the consumer
projection, but it leaves the elided text unconstrained: a variant may neuter the
very obligation the case is meant to test (restate the theorem as something
trivially true, or inject an assumed postcondition) and still pass `same_spec`.
Paired with a deliberately wrong implementation, that variant elaborates
cleanly, and as a positive case it records a pass for a reason unrelated to the
spec. Admissibility therefore additionally requires that every obligation
survives with a byte-identical statement (the tactic body may differ freely,
since a variant legitimately reproves), that no new assumption-bearing
declaration appears anywhere, and that no new top-level theorem is introduced.
The ban is on *new* items only, so it never rejects what G-HYGIENE already
accepts. The check is lexical and cheap, so a malformed variant costs no verifier
build; it is a necessary condition, not a sufficient one.

**Refutation witnesses.** On a backend where the verifier discharges the
postcondition automatically, "did not verify" really is a statement about the
spec. On a tactic-proof backend it is not: the frozen proof script is tuned to
the frozen implementation's syntactic form, so a *reshaped but still correct*
rival fails exactly as a wrong one does, with the same tactic error. Since
breaking the tactic script is the default outcome of reshaping an implementation
at all, essentially every reject case would pass vacuously. Each reject case on
such a backend therefore carries a **witness**: a snippet, checked in a file with
the frozen obligations stripped so no tactic script can interfere, that must
(1) elaborate against the rival, making the rejection attributable to the spec,
and (2) *fail* against the frozen solution, proving the witness is a real
discriminator rather than a tautology. A witness that does not hold of the rival
is unproven; one that also holds of the reference is vacuous.

**The consistency probe.** A witness may condition on an opaque term rather than
compute with it, and once it can bind hypotheses it can bind contradictory ones.
A witness whose hypotheses are inconsistent elaborates against the rival and
fails on the reference, satisfying both halves above, while recording a
refutation at an input that does not exist. Any witness that binds hypotheses
therefore gets a third build attempting to derive falsity from its own binders;
a probe that *succeeds* identifies the forgery. The probe is incomplete in the
safe direction, so an honest witness is never failed for being hard to decide,
and it costs nothing for the majority of witnesses, which bind nothing.

**A reject lane is mandatory.** A battery consisting only of positive cases
cannot certify a spec: SPEC-TOO-WEAK is detectable only by a rival that verifies,
so with no rivals the strongest available finding is unreachable and "every case
behaved as expected" degenerates to "every correct implementation verified". Such
a battery reads as unresolved, not as sound.

Note what an *opaque* carrier does and does not prevent. A term with no
computable value still quantifies, so a refutation can be stated at a point
described by hypothesis rather than at a literal: "whenever the callee's result
differs from this constant, the rival's answer differs from the spec's". That
claim covers the rival's entire wrong sub-domain, which is strictly more than any
single literal input could say. Opacity is therefore rarely a real reason a
reject lane is inexpressible.

All four of these surface as a gate **error**, not a fail. They say the battery
cannot decide the question, not that the spec is defective, and recording those
as the same outcome would tell the next operator to discard a manifest that may
be perfectly sound. For the same reason, a battery whose failing cases all timed
out reads as timed-out rather than malformed: it was never judged, and the right
response is a larger budget, not a rewrite.

### The battery contract

The manifest is a Python file the gate executes, exposing `SPEC_TESTS`: a list of
cases, each with

* `id`: unique string,
* `kind`: `uniqueness` | `soundness` | `admissibility`,
* `expect`: `"verify"` or `"reject"`, coherent with `kind`,
* `module`: the **full** solution-file source of the variant, sharing the frozen
  spec byte for byte,
* `rationale`: prose saying what this case falsifies if it fires.

Enforced mechanically, with a violation reading as a gate error and never as a
silent pass: every `module` must satisfy `same_spec` against the frozen solution
and stay inside the admissible variant scope; an unknown `kind`, an incoherent
`expect`, or a missing `module` is malformed; and cases must be cheap enough to
verify that a timeout is not the normal outcome.

The authoring convention is worth preserving verbatim in any port. A manifest
reads the frozen solution from disk into a `_BASE` string and derives each
variant with a swap helper that *asserts each anchor exists and is unique*.
Every variant then provably edits only the intended region, and, more
importantly, the manifest fails loudly the moment the frozen solution changes
underneath it, instead of silently testing a spec that no longer exists.

One naming artefact of the corpus is worth knowing before you read a manifest.
492 of the 500 verified `nagini/properties.py` docstrings name their runner
`swebench_nagini.pbt`, the module in the predecessor repository this nagini round
was first constructed in. In this repository the runner is
`swebench_unified.gates.pbt`, and it is the only thing that ever executes a
manifest. The stale names are left as written on purpose: the G-PBT stamp records
`manifest_sha256` over the manifest bytes and `check_stamp_freshness.py` requires
it to reproduce from disk, so editing a docstring would invalidate 492 current
verdicts and buy nothing a reader could not get from this paragraph.

Finally, case-count parity with a sibling formalization is the wrong target. Two
formalizations of one row may model different numbers of functions, so most cases
attached to one do not transfer. What replaces parity is coverage *of the modeled
surface*: every obligation both defended and attacked, every input binder varied
across the reject witnesses, every independent postcondition clause attacked by
some rival.

## 8. When is a cell done

A cell is **green** iff, reading only `meta.json`:

* every static and Docker gate is recorded with status `pass`, `skip`, or
  `relaxed`. A *missing* stamp is not green: the pipeline does not vouch for
  unrecorded work.
* the audit is complete: all three panel roles recorded, plus G-EQ.
* the gates whose skip has a "not constructed yet" meaning carry a **real**
  verdict. A conformance skip that means "no probe script exists", a battery skip
  that means "no manifest exists", and a benchmark-capability skip that means
  "this oracle was never wired up" are all *absences of judgment*. They are
  recorded as skips rather than failures (a failure would conflate them with a
  real disagreement), which is exactly why the green classifier has to exclude
  them explicitly.

The classifier reads `meta.json` and nothing else: never a log line, never an
agent's self-report, never a driver's summary file. That is the same rule as
everywhere else in the pipeline, applied to the last step.

`scripts/green_check.py` is that classifier, one line per cell, and it is the only
authority for the word: anything that re-derives greenness will eventually disagree
with it, and it will disagree about the cells being repaired -- one side reporting
"already done" while the other keeps spending. So the predicate itself is a
library, `swebench_unified.greenness`, and every consumer imports it: this script,
the review site's badges, and each repair driver. The gate list it requires comes
from the gate registry, so a newly registered gate is required without an edit
here. Greenness is necessary but not sufficient for releasing a corpus, because
a green stamp can be *stale* -- describing a spec that has since been edited -- or
supported by a battery that no longer imports. `scripts/release_gate.py` conjoins
the green census with those checks (stamp freshness, audit freshness and
completeness, battery integrity, battery-verdict strictness, stale failure
records, record hygiene) and treats
a cell it could not measure as a failure rather than a pass; exit 0 is the release
criterion, and section 7 of [reproducing.md](reproducing.md) describes each check.
Several of them exist because of the limits section 9 sets out next.

## 9. Known limits of the guarantee

The suite is a set of refuters. It is worth being explicit about what it does not
establish.

* **A spec hole makes a battery case behave correctly.** When a wrong rival
  verifies, that observation *is* the hole, and a well-formed battery records it
  as a documented case rather than shipping it as a reject case that would fail
  the gate. So G-PBT rightly passes such a cell and the finding has to travel out
  of band. Finding spec holes is the audit's job, and repairing one means editing
  a frozen artifact, which re-opens every gate that judged it.
* **Partial-correctness semantics admit a diverging implementation.** If the
  postcondition is only claimed of terminating runs, an implementation that never
  terminates satisfies every postcondition vacuously and verifies, while its
  faithful patch hangs the hidden test and does not resolve. That is a direct
  break of the property the benchmark measures, and it is a property of the
  chosen semantics, not of any one bundle. Under a total-correctness reading the
  verifier instead demands a measure on every loop and discharges a goal that it
  strictly decreases, so the diverging rival is rejected and the class becomes an
  ordinary reject case rather than a hole. The practical caution is to confirm
  that the semantics you believe you selected is the one actually in force: where
  the choice is made by a scoped declaration, a later declaration in the same file
  can re-open the weaker scope and win, and the artifact then reads as total while
  verifying under partial. Measure the semantics with a rival, never by reading
  the option.
* **Two measurement traps** recur whenever a rival is spliced into a frozen
  solution programmatically. Keeping the frozen proof tail makes tactic breakage
  look like a spec rejection, so a probe must reduce the proof to its minimal
  form before concluding anything. And a nonzero exit with *no output* is a
  killed build, not a rejection; on a machine running near its limits that is the
  common case, and reading it as a rejection manufactures evidence.
* **G-MUT and the fuzzers have fixed search spaces.** They are floors. The
  open-ended checks are G-PBT and the audit, and both are bounded by the
  adversary's imagination.
* **A transliterated conformance shadow is trusted code.** G-CONF refutes
  fidelity between the shadow and the repository; nothing mechanically refutes
  the gap between the shadow and the formal artifact it transliterates. That gap
  is what the faithfulness panel role exists to attack, and it is the reason the
  gate records shadow provenance.
* **A verdict without `sources` cannot be checked for freshness.** Each gate
  declares the bundle files its verdict depends on, and the stamp carries a digest
  of exactly those, so a later reader can decide mechanically whether the record
  still describes the bytes on disk. A record that carries no digests -- because it
  predates the field, or because it was written by a judge that did not declare its
  inputs -- says when it was measured but not *what* it measured, and no timestamp
  recovers that. `scripts/check_stamp_freshness.py` recomputes the digests
  and reports such a record as UNVERIFIABLE rather than as fine, because "we
  cannot check this one" and "this one is current" are different claims and only
  the first is true. Run it against any corpus you receive: it separates the
  records that demonstrably describe the shipped bytes, the ones that
  demonstrably do not, and the ones that cannot say. Only the second kind is a
  defect, and re-running the named gates on those cells clears it.
* **Repairing a spec invalidates the audit that judged it, and not every
  invalidation is re-measured.** An audit verdict is evidence about the spec view
  the reviewer attacked. Some later edits preserve it deductively: adding a proof
  obligation can only reject more implementations, so every rival the audited
  spec rejected is still rejected, and the recorded verdict still holds of the
  stronger spec. Other edits move what the reviewer was reasoning about, and for
  those the only honest instrument is a fresh reviewer, because replaying the
  retained battery cannot work -- its positive control is the solution *as of the
  audit*, so against a moved spec the replay reads as "the attack changed the
  spec" and fails closed. Where a verdict is carried by the strengthening
  argument rather than by a fresh measurement, that is a deduction and not an
  observation. `scripts/audit_freshness.py` names the cells it applies to and
  `scripts/audit_refresh.py` re-runs the stage over them, so a consumer who wants
  the observation rather than the deduction can take it.
