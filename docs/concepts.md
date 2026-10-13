# Concepts

## Task

A **task** is one benchmark item, normalized: a statement, the files it starts from,
the golden patch (as a patch or as whole files), and an `OracleSpec` describing how the
benchmark itself decides whether a candidate solves it.

Tasks are frozen. `benchproofer ingest` writes `task.json` under the bundle root and
never rewrites it unless `--refresh` is given, so the input a bundle was judged against
cannot change under it. A task's digest covers its content and deliberately excludes
free-form metadata, so annotating a task does not invalidate the bundles built from it.

## Bundle

A **bundle** is one task formalized in one backend. Its path is fixed at four levels,
which is what makes a corpus enumerable:

```
<bundle root>/<benchmark>/<task-slug>/<backend>/
```

`task.json` and `reference.patch` sit one level up, shared by every backend, so two
formalizations of the same task cannot end up with different inputs.

Inside a bundle:

| artifact | what it is |
| --- | --- |
| `solution.<ext>` | the specification and the implementation, in marker regions |
| `twins/` | the pre-fix implementation (the code before the fix, written in the specification's language) under the same specification, and `index.toml` recording its refutation witness where the checker needs one |
| `rivals/` | the property-based test suite, and `index.toml` declaring what each case claims |
| `correspondence.md` | how the implementation corresponds to the golden patch: the repository function each modeled function represents, with the type bridge (`Symbols`); each operation of the implementation mapped to the one the golden patch performs in its place, with its kind (`Operations`); what the fix changes that the specification does not model (`Not modeled`); the inputs the model's domain leaves out (`Outside the bridge`); and, where a repair took the result of an unchanged callee as an input, as only a repair may and only for a callee this run's rounds list, each such callee with its call site and reason (`Callee results taken as inputs`) |
| `conformance.py` | a program comparing the implementation with the repository's own code |
| `axioms.py` | a program that puts what the specification assumes of a callee to the callee itself |
| `notes.md` | the drafting log, the drafting session's own account, for a reviewer |
| `audit/` | what an independent review submitted and concluded, and `index.toml` recording it. `audit/notes.md` is each auditor's own account, where a count is that auditor's scratch program's rather than the bundle's `conformance.py`'s |
| `evidence/` | whatever a gate wrote to support its verdict |
| `manifest.json` | digests, provenance, and one verdict per gate |

Each entry in `twins/index.toml` and `rivals/index.toml` says what its case expected, what
the checker **found** of it -- `refute`, or `verify: unproved` for a correct case a proof
session could not close -- and the **digest** of the file it was written about. A session
that edits a case's file does not rewrite the rationale, so the digest is what says whether
the rationale still describes the case the bundle ships; where it does not, what is read in
its place says so rather than the rationale for a file that is gone.

## Marker regions

One file holds the whole formalization, split into named regions:

```python
# benchproofer:begin spec
...
# benchproofer:end spec
```

The regions are `axioms`, `helpers`, `spec`, `impl`, and `proof`; `spec` and `impl` are
required. `axioms` is where the file says what unchanged callees compute, by a definition
that models one or an axiom that assumes it, which is the only place such a thing is
allowed to be and the reason a proof about realistic code can be stated at all; see
[`spec.axioms_grounded`](gates.md#specaxioms_grounded), part of the paper's axiom-soundness
gate. A fix that changes several functions is modelled as several, each with its own
contract and body: the regions of one function (`spec`, `impl`, `proof`) repeat, numbered
from the second (`spec.2`, `impl.2`), while `axioms` and `helpers` appear once. Everything
below that speaks of "the `impl` region" means every one of them. Regions make three things
mechanical:

* the **spec view**, what a solver is shown: the file with `impl` and `proof` elided, so
  two implementations can be compared under an identical specification;
* **`same_spec`**, which compares spec-view digests, so a gate can prove that a rival
  it just checked was judged by the same specification and not a weakened one;
* **substitution**, which is how a mutant, the pre-fix implementation, a rival, or a
  review's submission is checked: only the elided regions are replaced, and everything
  else is byte-identical.

A **variant** of a solution is a copy of the solution file with some regions replaced, and
those elided regions are what it owns. The implementation is the obvious one; the proof is
the one that is easy to get wrong. Where the proof is a declaration of its own, such as
Lean's `theorem` or Velvet's `prove_correct`, it was written against the reference
implementation, and a checker replaying it against someone else's rejects the file because
the proof is missing a step. Read as a verdict on the specification, that rejection is a
finding the bundle does not have, so a variant writes its own proof. What it
may not do is choose its own claim, which is the same exploit from the other side:
`theorem nothing : True := by trivial` elaborates, so a variant free to state that would
be accepted while establishing nothing about the specification. A variant therefore has
to restate a claim the solution file states, and how it establishes the claim is its own
business.

## The pre-fix implementation and rivals

The **pre-fix implementation** is the task's own code before the fix, written in the
specification's language, under the bundle's specification. A specification that the buggy
code already satisfies says nothing about the task, so the pre-fix implementation has to
be refuted.

A **rival** is an implementation in the property-based test suite, labeled with the verdict
it should receive: a correct one must verify, a buggy one must be rejected. The suite
declares in advance what each case claims:

| kind | expects | catches |
| --- | --- | --- |
| `uniqueness` | `refute` | a specification too weak to notice a wrong implementation |
| `soundness` | `verify` | a specification that pins down one implementation rather than the behavior |
| `admissibility` | `verify` | a precondition so strong that the inputs the task exercises are excluded |

Both directions matter. A specification nothing can satisfy is as useless as one
everything satisfies, and only the cases expected to verify can tell them apart. The
declared expectation is part of the manifest, so a case whose direction contradicts its
kind is rejected when the property-based test suite is read rather than reinterpreted
later.

Each case asks a question no other case asks. One that contains the shipped
implementation, the pre-fix implementation, or another case is set aside, because what the
checker says about it is about that other file. The suite is judged on the rest, and a
repair rewrites the case only when no case among the rest asks its question.

The third row is not a rival. An `admissibility` case is the *reference* implementation
with a probe added — a probe being assertions that show the specification holding at
concrete inputs the task itself exercises — and it is the only case that can find a
vacuous specification. No rival can: every rival is judged against the same precondition,
so if that precondition admits nothing the task is about, all of them are excluded
together and the suite reports that every case behaved as claimed. The kind is asked for
only where a probe's assertions are discharged rather than searched for, which is under a
prover. One probe takes its inputs from the FAIL_TO_PASS tests. The model's domain has to
admit what the PASS_TO_PASS tests hand a function the fix changes too, so a second probe is
drafted where a PASS_TO_PASS test the test patch adds or edits exists, or another one whose
own code calls a function the fix changes, by its name, as `name(...)` or `obj.name(...)`.
It is shown those tests whole, takes its inputs from them, and is judged and proved as the
first one is.

Where the probe goes is the checker's to say, since in the wrong place the checker rejects
it for a reason that is not the specification. Under Nagini it is a function of its own at
the top level: inside the specified method, a call to it is a recursive call, which Nagini
rejects on the termination measure whatever the precondition admits. A language model asked
for a function after the reference implementation's body writes it after the `impl`
region's end line, so that is where the drafter asks for it, and the splice moves a
top-level function written there to the end of an implementation region that closes its
definition at the top level of the file: inside the region, so the spec view is untouched,
and still a function of the module. For a region inside a class that goes on past it, that
is another implementation region, since a function there would cut the class short. Nothing
else a reply writes outside its regions reaches the file, for a probe or for any other
variant, because every line there is part of the spec view.

Under Lean and Velvet a `refute` case comes with one thing more: a **witness**, a claim
proved at one concrete input that the rival violates the specification. There the proof
script is tuned to the reference implementation's form, so a rival that is merely
rewritten is rejected exactly as a wrong one is, and the rejection on its own does not show
that the specification, rather than the rival's own proof, is what rejects it. The witness
has to hold of the rival and fail against the reference implementation; a case without one
is an error rather than a pass.

## Review

A **review** is one adversarial reading of a bundle by someone who did not draft it. It
is what the top of the ladder rests on, because two things about a formalization cannot be
decided by a program: whether the specification is strong enough to be worth proving
anything about, and whether it describes the task it claims to.

A review files five kinds of thing, and the difference matters:

| what | how Benchproofer treats it |
| --- | --- |
| a **submission**, one implementation | re-run: spliced under the shipped specification for the checker, put through the bundle's own `conformance.py` in place of the drafter's implementation, an attack's equivalent patch put to the benchmark's tests, and a witness test filed with it run where those tests run |
| a **fuzzer**, a program aimed at one callee the specification assumes | re-run in the benchmark's environment, and read for a disagreement it observed |
| a **judgment**, a conclusion about one question with what it was read from | reported, for as long as every file it was reached from is unchanged |
| a **ruling** of the attack validation auditor on a submission that cannot be determined by execution, naming the input and the sentence of the statement, the test or the obligation it rests on | read by the gate that judges the submission (`audit.spec_completeness` for an attack, `audit.spec_soundness` for a control), for as long as the specification, the implementation, the submission's files and what its witness test cites are unchanged; one naming no input or nothing it rests on is no ruling |
| a **defect**, an input the specification admits on which, the attack auditor shows by running code, it promises what the repository does not do | filed only with a function `conformance.py` compares and its arguments as a Python tuple literal, kept on record while the specification it was found against stands, and handed to every run of `conformance.py`, where a disagreement on it fails `impl.conformance` |

Nothing a reviewer claims about a submission or a fuzzer is taken on trust; the claim is
recorded and Benchproofer asks the checker, the benchmark's tests, and the callee itself. A
submission is labelled `weakness` (meant to be wrong, so the specification should refute it)
or `control` (meant to be correct, so the specification should accept it), but the label only says
which question the reviewer aimed at. Either one can decide either question, because what
the checker and the benchmark's tests say does not depend on the intent.

The review runs the checker itself, once per submission, before filing it. Not to judge
the submission, which is a gate's job, but because some of the checker's verdicts say
nothing about the specification. A file the checker could not read decided nothing at all,
and neither did one its translator crashed on at a line the checker's output names: the
construct at that line is the reviewer's to write another way. A crash nothing places in
the file, like a search that ran out of time, is left for the gates to report as
undecided. Under a prover, a file it read and could not prove is ambiguous: what a prover
needs before it will accept an implementation, the invariant a loop does not state or the
lemma nobody called, is written in the regions a variant owns, so it is the reviewer's to
supply, and a missing proof looks exactly like a specification that rules out the
implementation.
Under a falsifier a refutation is a counterexample, so an attack it refutes is decided; but
a refuted control is a finding only if the input it was refuted on is one the task allows,
rather than one on which the reviewer's own implementation computes a wrong result. In each
of those cases the reviewer, which runs the gate a submission is judged by in its own
workspace, sees the checker's own output before it submits, and what it submits is what
gets filed. A reviewer that stands behind its implementation submits it unchanged, which is
the right response when the specification really is what rules it out; a control a prover
still refuses after the reviewer wrote the proof it could is filed as unproved, with what
the reviewer tried, and is a gap the attack validation auditor rules on (see
[`audit.spec_soundness`](gates.md#auditspec_soundness)).

Some submissions no run decides, and those are what the **attack validation auditor** rules
on, once the gates have re-run the review's submissions: an attack the checker accepts whose
equivalent patch the benchmark's tests pass, which nothing showed equal to the reference
implementation (does the behaviour it changes belong to what the task requires?); such an
attack whose witness test passes on the fixed code and fails with its patch (does what the test
cites ask for the behaviour it checks?); an attack
shown equal to the reference implementation whose patch the tests reject (is the model at
fault, or the patch?); and a control the checker refuses that nothing showed correct and
refused by the specification (is it correct, and does the specification refuse it, or a
proof it lacks?). While one has no ruling, the gate that judges it is undecided and the
auditor is asked again; one it still leaves without a ruling after that is discarded,
counting neither way.

Judgments cover the three questions in `AuditRole` (`faithfulness`, `equivalence`,
`disclosure`), each carrying `sound`, `unsound`, or `uncertain`, the findings behind it,
and the digests of what the reviewer read. Whether the specification is strong enough is
deliberately not among them: that one a reviewer addresses by submitting an implementation.

`benchproofer audit` leaves a bundle that already carries a current review alone, and
`--again` adds to what is on record while the specification it attacked stands. A repair
that changes the specification makes the attack auditor due again, and that review is
fresh: its submissions replace the earlier ones, which are not re-run, and it writes again
first each earlier attack the gates ruled a weakness, unless the repair showed it was not a
defect.

## Levels

| level | evidence |
| --- | --- |
| `static` | everything decidable from the bundle plus a verifier |
| `oracle` | additionally, the benchmark's own tests, which usually means a container |
| `audited` | additionally, an independent adversarial review that still describes the bundle |

Each required set contains the one below it, so a higher certification means strictly
more. `--level oracle` adds the three gates that connect the verified artifact to the task
the benchmark actually poses and to the callees it assumes; `--level audited` adds the
seven that report a review. Some benchmarks have no tests to run at all; their oracle
reports `unavailable`, and a bundle can then be certified only at `static`.

## Verdicts

A gate records one `Verdict`, with the digest of the gate that produced it, the version
of Benchproofer that ran it, the digests of the artifacts it read, and any evidence file it
wrote. There are six statuses:

| status | meaning | favorable |
| --- | --- | --- |
| `pass` | the gate judged the bundle favorably | yes |
| `fail` | the gate found something wrong | no |
| `waived` | it failed and a human accepted it, on the record | yes |
| `skip` | the gate declined to judge; see the skip reason | only `not_applicable` |
| `timeout` | the check did not finish inside its budget | no |
| `error` | the gate crashed, which says nothing about the bundle | no |

A skip carries a reason, and only one of them is compatible with certification:

| skip reason | meaning |
| --- | --- |
| `not_applicable` | there is nothing here to check, by construction |
| `artifact_absent` | there is no bundle, or no review, for the gate to read; a file the bundle lacks is a `fail` of the gate that needs it, which a repair addresses |
| `toolchain_absent` | the verifier is not installed here |
| `oracle_unavailable` | the benchmark's tests cannot run here |
| `inconclusive` | the check ran and does not support the conclusion, as when a bounded refuter found nothing |

`inconclusive` is the reason the rest of the verdicts can be trusted. A falsifier that
found no counterexample has not shown there is none, so recording it as a pass would
turn a budget into a proof.

## Outcomes

`classify` is the only place that turns a bundle's verdicts into a conclusion:

| outcome | when |
| --- | --- |
| `certified` | every required gate is favorable |
| `rejected` | at least one required gate failed |
| `incomplete` | nothing failed, and something was not decided, never ran, or is `stale`: a verdict of a gate that reads the review, about files the bundle no longer has |
| `dropped` | a required gate about the task itself failed (`adjudicate.DISQUALIFYING`) |

A dropped task is one whose golden patch does not pass the benchmark's own tests here
(`oracle.reference_resolves`, the paper's resolution check). It says nothing about anything
drafted for the task and no artifact could fix it, so the task is set aside rather than
rejected, and it outranks every other finding. Failure outranks absence, so a bundle with
one real finding is reported as rejected rather than as unfinished. Everything else that is
not favorable leaves the bundle incomplete, including a gate that crashed: a defect in
Benchproofer is never recorded as a defect in the artifacts.

## What to expect from a run

`audited` is the level a benchmark ships at, and a specification drafted in one attempt
rarely survives seventeen gates. That is Benchproofer working rather than failing: what the
run is worth is that the report names which gate objected and why, and that the loop then
acts on it.

Nothing about that is meant to be driven by hand. `run` judges the bundle, reviews it once
no gate a program decides has found what a repair addresses or holds the review back,
repairs it to address whichever gate reported the finding, and judges and reviews it again,
until it certifies or the budget runs out. Below `audited` the loop is the same without the
review: judge, repair, judge again. A rejected bundle at the end of that is one the loop could not fix
inside what it was given, not a prompt to go and repair it yourself.

`max_repairs` bounds that loop and is what to raise when a corpus is worth finishing. Each
repair attempt costs a judgement of the whole bundle, and a review when it gets that far,
so it trades money for yield directly, and a bundle rejected at the end of it is one the
loop ran out of room on. Every attempt counts against it, one whose session's work was
discarded or changed nothing included, and the next repair is told why that work was not
taken and what it was.

Two things bound the yield from outside the loop. Every gate that consults the benchmark's
own correctness check inherits its strength, and a check too weak to decide the question
makes those gates decline instead of guess: declining costs yield and is the correct
direction to err in. And a run interrupted partway is not lost work: with
`--skip-certified`, a bundle that already certifies is not judged again, so a second pass,
or a larger budget, is spent only on the bundles still short.

The unit of work is the corpus rather than the task. A rejected bundle costs the compute
that produced it and never reaches the benchmark, which is what the gates are for; a
certified one carries on disk every verdict that admitted it. So the number to watch is how
many bundles certify per unit of budget, and `static` and `oracle` earn their place as the
cheap way to find that out: they call the same gates without paying for a review, so a
corpus can be sized and debugged under them before it is put to the level it will ship at.

## What certification does not claim

`certified` says every required gate judged this bundle favorably, and it is worth what
those gates can see. Three limits are worth naming here rather than leaving a reader to
find them:

* **The benchmark's tests bound it.** Every gate that consults the benchmark's own
  correctness check inherits that check's strength, in whichever direction that gate errs;
  see [Oracle gates](gates.md#oracle-gates).
* **The assumptions bound it.** A specification may assume a callee instead of modeling
  it, and the proof then holds modulo those assumptions. `spec.axioms_grounded` and
  `audit.axiom_soundness` put each one to the real callee, which is testing and not
  proving, and `audit.equivalence` holds each to a callee the golden patch does not change:
  between them, the paper's axiom-soundness gate.
* **A review is a sample.** The strength gates report what was submitted and survived,
  never that nothing could have been found. `audit_min_attacks` is how large the sample
  has to be before surviving it counts as evidence at all.

What is left is narrower than "this task is solved" and more useful: an implementation
this checker accepts under this specification behaves like the golden patch on
everything the gates put to it, and each of those verdicts is on disk with the output it
came from, so a reader who doubts one can re-run it.
