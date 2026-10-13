# Gates

A gate is one question about one bundle, decided by running something rather than by
reading a claim. Every registered gate runs, including third-party ones, because a
recorded verdict is worth having. Certification depends on a fixed required set, so
"certified" means the same thing in every report.

`benchproofer catalog gates` lists the gates in your installation with the rationale
each one states for itself.

## Execution order

Cheap and structural first, so a malformed bundle is reported as malformed before a
verifier spends minutes on it:

```
artifact.integrity -> spec.hygiene -> spec.no_leakage -> spec.verifies
  -> spec.discriminates -> spec.strength.mutation -> spec.strength.battery
  -> impl.conformance -> spec.axioms_grounded
  -> oracle.reference_resolves -> audit.independence -> audit.faithfulness
  -> audit.equivalence -> audit.no_disclosure -> audit.axiom_soundness
  -> audit.spec_completeness -> audit.spec_soundness
```

Every gate is asked at every level, and one whose own level is above the run's records that
it does not apply (`Gate.applies`); the level decides which ones certification depends on.
`impl.conformance`, `oracle.reference_resolves`, and `spec.axioms_grounded` are required
from `--level oracle`, and the seven `audit.*` gates from `--level audited`. At
`--level audited`, `run` asks the gates that read the review only about a bundle none of
whose other verdicts goes to the repair or holds the review
([Where a verdict goes](#where-a-verdict-goes)).

## What the gates are between them

Read down the middle column and the set is an argument in seven parts, which is roughly
the order in which a formalization goes wrong:

| the question | gates |
| --- | --- |
| is the artifact the one that was judged | `artifact.integrity` (the task-identity check) |
| is the specification honest about what it proves | `spec.hygiene` (the hygiene check), `spec.no_leakage` and `audit.no_disclosure` (the leakage gate, mechanical and adversarial) |
| does it hold of the implementation | `spec.verifies` (the verification check) |
| is it strong enough | `spec.discriminates` (the discrimination check), `spec.strength.mutation` (the mutation check), `spec.strength.battery` (property-based falsification), `audit.spec_completeness` (the completeness gate) |
| is it weak enough to admit a correct implementation | `spec.strength.battery`, `audit.spec_soundness` (the soundness gate) |
| is it about the task the benchmark poses | `impl.conformance` (the conformance gate), `oracle.reference_resolves` (the resolution check), `audit.faithfulness`, `audit.equivalence` (the equivalence gate) |
| is what it assumes of the world true of the world | `spec.axioms_grounded` and `audit.axiom_soundness` (the axiom-soundness gate), with `audit.equivalence` for its check that each callee the `axioms` region names is unchanged |

The names in parentheses are the SWE-Proof paper's. Strength runs in two directions on
purpose. A specification nothing satisfies refutes every attack and is worthless; one
everything satisfies accepts every correct implementation and is worthless too. Each
direction has a mechanical gate that generates its own evidence and an audited gate that
asks a reviewer for it. The last row works the same way, and it is the row that decides how
much a proof about realistic code is worth: everything below it is conditional on the
assumptions being true.

## Static gates

### `artifact.integrity`

The paper's task-identity check. The bundle is internally consistent and nothing
recorded earlier has changed since. Every other gate reads the same files, so a bundle
that fails here makes the rest of the verdicts in `manifest.json` meaningless rather than
merely incomplete: a solution edited after it was judged, malformed marker regions, or a
property-based test suite naming files the bundle does not ship.

### `spec.hygiene`

The paper's hygiene check. The shape of the solution file, checked before anything
expensive is asked of it: the regions the backend requires are present and non-empty, the
specification claims that the implementation returns, no construct discharges an obligation by assertion (`sorry`, `assume`, and their equivalents),
a proof the checker merely replays is a proof about this file, whatever the file assumes of
the outside world sits in the `axioms` region and names the callee it represents, and the
file imports nothing that would let it reach outside itself. Comment text is masked before
scanning, so a solution may discuss `sorry` in prose without failing. What matters is what
the checker reads. Where the checker reads nothing inside a string literal -- Nagini, and
the Hypothesis falsifier, declare this as `inert_strings` -- string literals are masked as
well, found by Python's tokenizer, so a module docstring saying the file consumes no
`@ContractOnly` axiom is not an assumption, and one naming `MustTerminate` is not a claim.
Under CrossHair a docstring is where the contracts are written, so there it is scanned like
code. A directive comment such as `# type: ignore` is matched against the comments as
written either way, since masking is what would hide it.

The termination requirement applies only to a backend whose accepting verdict would
otherwise cover part of a run: under Nagini, `Ensures` holds of the runs that reach the
return, so a method whose loop never exits satisfies every postcondition it declares, and
a `Requires(MustTerminate(...))` obligation is what turns that into a claim about every
run, as `verified-swebench`'s Nagini guide requires. Each spec region is asked for it,
since one function's claim does not cover another's runs. Every other backend here checks
termination itself, so the check asks nothing of its specification. Which token would do
it is the backend's to declare, not this gate's to assume; see
[Backends](backends.md#nagini).

The requirement that a proof be about this file applies to a checker whose accepting
verdict means the file elaborated. Under Lean, `lean solution.lean` exits zero on a file
whose only theorem is `theorem nothing : True := by trivial`, and nothing in the language
ties that declaration to the two regions it is supposed to be about, so a bundle shipping
it would get an accepting verdict that says nothing whatever about the implementation.
The gate therefore requires the `proof` region to state a claim, in one of the words the
backend names, and requires the statement of that claim to name what the `spec` and `impl`
regions declare. A supporting lemma may be about anything; one claim about this file is
what is wanted. Under Dafny or Nagini the obligation is attached to the method itself, so
the backend names no such word and the check asks nothing. What this cannot see is a claim
that names both regions and says too little about them, such as one asserting the property
at a single input; `spec.strength.mutation` is what catches that.

A backend may add a rule of its own that no shared table expresses (`Backend.problems`).
Velvet's is about what the method returns. Where this checker rejects a case, only a
witness shows that the specification, rather than the case's own proof, is what rejects
it, and a witness there is a claim about the derived tester decided by reduction at one
concrete input. Over a result typed `Float`, a real or a rational there is no such claim
to write -- the kernel reduces equality on none of them -- so every wrong case would come
back `unproved`, and no claim proved at one input could show, for the property-based test
suite or for `spec.discriminates`, that the specification is what rejects a case. The gate
says so of the file, since the way out is another type to represent the value: an integer
scaled to the precision the task's own tests check, with the bounds that make that
faithful.

Assuming something about a callee is not banned, because a realistic task calls things
nobody is going to verify; what is banned is assuming it invisibly. A construct that
represents an unchanged callee, `{:axiom}` in Dafny or `axiom` in Lean, belongs in the
`axioms` region, which the specification view keeps, and it has to declare which callee
it represents so that `spec.axioms_grounded` can put that callee to the benchmark's own
environment. Anywhere else, it assumes what the file is supposed to establish. A
definition that models an unchanged callee sits there too, under its
`benchproofer:models <callee>` line.

### `spec.no_leakage`

The specification says what a correct solution achieves rather than restating how the
golden patch does it. A specification that embeds the golden patch makes the formalized
task solvable by reading its own statement. This is the mechanical half of the paper's
leakage gate; `audit.no_disclosure` is the adversarial half.

The screen runs over the **spec view** -- what a solver is actually shown -- and it is
five rules, each about a different way a view gives the edit away:

| rule | what it catches |
| --- | --- |
| `L1` | a diff marker, or a line the golden patch or the benchmark's test patch changes, reproduced in the view |
| `L2` | a path the golden patch touches, or the dotted module that path spells |
| `L3` | a function or class the golden patch touches, named in a comment or docstring |
| `L4` | an identifier in the view embedding such a name; a word in a string literal is not one |
| `L5` | prose narrating the change: *bug*, *fix*, *patched*, *previously*, *off-by-one* |

Everything is judged against the **task statement the solver also reads**. A line of
either patch, a path or a symbol the statement already says verbatim is not a leak,
because it is already public -- an issue that quotes the failing call or the message the
fix must print gives the solver that text; one the statement does not say is a leak
however ordinary it looks. There is nothing else to screen against -- a task carries a
statement and no separate hint text -- so the gate cannot excuse an identifier by
consulting something the solver never sees.

Four things are deliberately *not* findings, because each collides with a specification
that did nothing wrong: the signature and docstring the task hands out, which a
specification is expected to quote; a fragment or a name that localizes nothing, such as a
bare `) -> bool:`, the opening of a `def __init__(` split across lines, or the `POST` method
every web handler class defines; a region sentinel or a directive Benchproofer reads, such
as the `benchproofer:axiom <callee>` line an axiom has to carry, which may spell out the
patched module in naming the callee; and a narration word in its ordinary sense -- the
patch part of a version, a quantity held fixed, a value previously computed in the same run,
an off-by-one a specification rules out. "The fixed code", "previously returned" and "after
the patch" are still findings. A diff marker is a
hunk header, a `diff --git` or `index` line, or a `--- ` line followed by a `+++ ` line,
not a banner comment drawn with dashes. And a name counts as one the golden patch touches
when the fix defines, deletes or edits it, not when it is only the function `git` writes
above a hunk that changes the code next to it: which function or class a changed line sits
in is read at drafting from the Python source of its file in the task's working copy,
before the fix for a line the fix removes and after it for a line it adds, and kept in the
bundle's `manifest.json` (`provenance.changed`), so the gate reads no repository. A bundle without
that record -- drafted before it was kept, by another tool, or where the files could not be
had -- has the names the diff gives, as `verified-swebench` reads a patch: each `def` or
`class` name in a hunk header, which is `git`'s guess at the definition the hunk is in, and
each on a changed line. A line of the test patch whose text the repository had before the
fix -- in the code around either patch's hunks, with the lines they remove, or in the files
the task starts from, compared without whitespace or quotation marks -- is not screened: a
test that only re-wraps a message the code already printed gives nothing away.

A benchmark that states its solution as whole files rather than as a diff is screened
the same way, with what the golden patch *adds* standing in for the changed lines. That
matters most there: a single-module task is where quoting the golden patch is easiest.

The screen is mechanical, so it is a floor rather than an argument. It catches a view
that *reproduces* the fix and cannot catch one that describes the fix in its own words.
`audit.no_disclosure` is what asks an adversarial reader to reconstruct the solution
from the view, and a bundle needs both.

Read the evidence before treating a failure as a finding. `evidence/leakage.txt` names
the rule and the exact text for every hit, and the two questions worth asking of it are
whether the collision is a coincidence the guards above should have covered, and whether
the statement really does not already say the symbol. A recurring false positive is a
policy question for `NONDISTINCTIVE` in `benchproofer.core.leakage`, not a threshold to
turn down.

### `spec.verifies`

The paper's verification check, and the bundle's central claim: the shipped implementation
satisfies the shipped specification, as decided by the backend's checker. A rejection is a
failure of the bundle. A checker that reached no verdict, whether it timed out, crashed, or
gave up, is recorded as undecided, because a loaded machine must not be able to turn a
sound artifact into a finding. It is still the file's to address, so a repair is shown it.
Where Nagini's translator crashed, the verdict names the line and column of the construct
it was translating, since the traceback it died with names only its own code.

### `spec.discriminates`

The paper's discrimination check: the specification tells the fix from the bug. The pre-fix
implementation (the code before the fix, written in the specification's language) is
checked in the same solution file in place of the reference implementation: same
specification, byte for byte. The checker must reject it. If it does not, the specification
is satisfied by the bug the task is about. This is the cheapest check that a specification
is about the right thing, and the only one that uses the benchmark's own notion of what was
broken.

The drafting stage lets the pre-fix implementation write what every other
[variant](concepts.md#marker-regions) owns: every implementation region the solution file
has -- `impl`, and `impl.2` and on where it models several functions, since the pre-fix
difference sits in whichever of them the fix changed -- and the proof of them where the
file has one. A pre-fix implementation that could not touch the proof would ship the
solution file's, which is a script tuned to the fixed implementation and stops closing over
the pre-fix one whether or not the specification tells the two programs apart.

Under a checker where only a refutation witness, a claim proved at one input, shows that
the specification, rather than the file's own proof, is what rejects a file
(`Backend.witness_required`, currently Lean 4 and Velvet), that holds for the pre-fix
implementation too: the checker reports whether the file elaborates, the pre-fix
implementation's file writes its own proof, and a script that stops closing over the
pre-fix implementation is rejected just as one reshaping a *correct* implementation would
be. So there the pre-fix implementation comes with a refutation witness, as a case of the
property-based test suite that expects `refute` does: a claim, proved at one concrete input
-- the inputs of the task's FAIL_TO_PASS tests are where the drafter is told to look -- that
the code before the fix violates the specification. The drafting stage asks for it with the pre-fix
implementation, screens it as it screens a rival's, and hands one whose proof does not
close to a proof session (an agent session asked to prove a correct case of the suite, or
its witness) with its statement held as written. It is recorded beside the pre-fix
implementation in `twins/index.toml`, with what that session reported. A pre-fix
implementation whose own proof reaches for a tactic the solution file does not use -- a
`sorry`, since no honest proof of the code before the fix closes -- is a file the gate
would reject unread, so the drafting stage puts the solution file's proof back in its
place: the witness, not the proof, is what shows that the specification is what rejects it.
A case of the suite meant to be rejected is treated the same way; one meant to verify keeps
what it wrote.

A witness assumes nothing: it is a claim at one concrete input, and the gate, like the
drafting stage, refuses a witness that binds a hypothesis or a value. The request names each
declaration of the `axioms` region under a `benchproofer:axiom` line: no proof evaluates one
at an input and no hypothesis may fix it, so a witness can use only what the region states of
it, and where no refutation follows from that, the drafter is told no admissible witness
exists. A witness these screens refuse is not handed to a proof session, which could not make
it one the gate admits.

The gate builds the witness twice, each time appended to a copy of the file with its proof
regions taken out, so no script of the bundle's stands between the claim and its verdict:
against the pre-fix implementation, where it has to hold, and against the reference
implementation, where it has to fail. Only a rejection both builds bear out is the
specification's. The witness is asked of a pre-fix implementation the checker reached no
verdict on too, since the builds leave out its own proof, which is what may have run out of
budget. A pre-fix implementation with no witness, or with one whose build does
not go through against it or that holds of the reference implementation too, leaves the
question undecided: the verdict is an error, which is not certifiable, and names why for
each pre-fix implementation, with the proof session's record where one ran, as
`spec.strength.battery` names it for a case of the suite that expects `refute`. A build that
did not go through is reported as what it was: one the checker could not read -- an
unknown tactic, a `decide` over a type with no instance -- never asked whether the claim
holds, and one that failed inside the pre-fix implementation itself says nothing about the
claim at all. Only the third kind is the claim itself not going through, and the checker's
verdict alone does not separate a false claim there from a proof that is missing a step.

A verdict names the first category that has a case, because that is the one whose status
says the most, and it names the others it found beside it. A repair told about one category
spends its repair attempt on that one and the attempt after is told about the next, one
attempt per category; told about all of them, one repair can address them all. `defects`
in the verdict's details is each category with its cases. `spec.strength.battery` reports
the same way. It is not a pass, because nothing but the rejection would then stand behind
the one check here that uses the benchmark's own notion of what was broken, and any
reshaping produces that rejection. A repair addresses it as it addresses a case of the
property-based test suite whose witness does not show that the specification is what
rejects it: by fixing the pre-fix implementation or its witness, never the specification.
`evidence/discriminates.txt` has each pre-fix
implementation's outcome, and, for one where no claim proved at one input shows that the
specification, rather than its own proof, is what rejects it (`unattributed`), why. Under a
checker that needs no witness, the pre-fix implementation comes with none, and a rejection
of a file the checker could read is read as it always was.

A task whose fix replaces nothing -- one that only adds a file -- has no pre-fix state to
write in the specification's language, so no pre-fix implementation is drafted and the gate
is not applicable. The gate and the drafting stage decide that by the same predicate. A
bundle for any other task that has no pre-fix implementation fails the gate, so that a repair
writes one: nothing else does once the first draft is written.

The pre-fix implementation is held to the rules every other
[variant](concepts.md#marker-regions) is held to -- it keeps the shipped specification,
uses no construct the solution file does not (`sorry`, an axiom, a directive), and proves
no claim of its own -- since one whose implementation assumes what it should compute is
accepted whatever the specification says, and reading that as a specification the bug
satisfies would report a defect the bundle does not have. The bundle ships the pre-fix
implementation, so one that breaks those rules is a failure here rather than a case set
aside.

### `spec.strength.mutation`

The paper's mutation check. Corrupt one token of the implementation and ask the checker
again. A specification worth verifying against accepts no corruption that computes
something else, and one that accepts such a corruption fails the gate. These rules keep
the verdict honest:

* only the implementation region is mutated, so a mutant can never weaken the contract
  it is judged against;
* a mutant the checker could not read is not a program -- `+` turned into `-` over a
  sequence is the common one -- so it leaves the sample, and when every mutant is one the
  gate is not applicable rather than failed;
* a mutant the checker refuses is not counted, under every checker: the refusal can be the
  proof the file carries -- a mutant gets no new proof -- or the language catching the
  corruption, rather than the specification, so it says nothing about the specification's
  strength. The gate's summary says how many were refused, and that they are not counted;
* a mutant the checker could not decide is not counted either, since a timeout is not
  evidence of specification strength;
* a mutant the checker accepts that is not shown equal to the shipped implementation
  survives, and any survivor fails the gate as too weak, named in the verdict. Under a
  bounded refuter that is not a finding: a surviving mutant may simply have outlasted the
  search budget, so the verdict is undecided.

A mutant the checker accepts is not always a defect: a corruption can yield an equivalent
program, which no specification can reject -- an edit to an initial value that every path
overwrites is the usual one. So under a prover each one and the shipped implementation are
executed on the same drawn inputs, and one that returns what the shipped implementation
returns on every admissible input drawn is set aside as `equivalent`, and named in the
verdict. One that cannot be run to compare -- it assumes a callee, or takes a type nothing
draws -- survives. Under a bounded refuter nothing is set aside, since there the
specification is itself a set of properties run on drawn inputs. Where the checker proves
the specification admits one result per input (the lemma
[`spec.strength.battery`](#specstrengthbattery) asks for, computed once per bundle), every
accepted mutant is equivalent without being run: it satisfies the specification at every
admissible input, and there is one result it could return there.

`evidence/mutation.txt` records every mutant whole: its id and operator, the line number,
the full line before and after, what the checker said, and what running it showed.

Since refusals are not counted, a pass says only that every one-token corruption the
specification accepts was shown to compute what the shipped implementation computes. It
is a floor, not an argument;
[`spec.strength.battery`](#specstrengthbattery) is where the argument is made, because a
rival writes its own proof.

### `spec.strength.battery`

The paper's property-based falsification. Mutation is a floor; the property-based test
suite is an argument. Each rival is an implementation in the property-based test suite,
labeled with the verdict it should receive: a correct one must verify, a buggy one must be
rejected. It is hand-written and shipped with the outcome its author claims the checker
will produce, and the finding is a rival that behaves otherwise. A rival writes every
region the spec view elides, which where the checker replays a proof means the proof as
well as the implementation: a rival rejected because the solution file's proof no longer
replays would otherwise read as a specification that pins one implementation down. A suite
that attacks in only one direction is not a property-based test suite, so a bundle with no
suite, or with no case of a kind the backend asks for -- no uniqueness case, or none expected
to verify -- fails the gate without a case being run, and a repair writes what is missing.
Each verdict records the cases it judged (`rivals`), and a suite that has lost one the verdict
did not find defective as a case -- under `drifted`, `not_evidence`, `set_aside`, `unproved`,
`unattributed`, `malformed` or `undecided` -- fails the gate before any case runs, whoever
removed it (`removed`): a defective case may leave the suite, and any other is part of what
the specification was measured by. A verdict that judged no suite, its toolchain absent, the
solution unverified or the index unreadable, records the cases the verdict before it left
the suite bound to keep.

The uniqueness kind has a second way to be decided. Where the specification is a total
function of its inputs there is no wrong implementation it admits, so there is no rival to
write, and a drafter asked for one produces a defective case. The gate asks the checker
instead, in a scratch of its own: it generates the statement from the specification --
`for all inputs, two results the specification admits are equal`, over a Lean predicate or
over the conditions Velvet's `prove_postcondition_decidable_for` decides for a method
(`core.echo.determines`) -- and offers the bundle's own claims before a fixed list of
tactics. A specification of several functions has a predicate or a method for each, and
gets one conjunct each; of several Lean predicates, those a claim of the proof region
concludes are the specification, and the rest are its helpers and the preconditions a claim
takes as hypotheses. The bundle does not state the lemma, and is asked for one only where
the tactics fail and the lemma would decide an attack
([`audit.spec_completeness`](#auditspec_completeness)); nothing rests on what it is named. Where it is proved, the kind's question is decided for every input rather than for
the one a rival would have picked, and so is a drafted uniqueness case for which no witness
shows that the specification, rather than the case's own proof, is what rejects it: that
case is recorded rather than erroring the property-based test suite. It decides the
uniqueness kind alone -- a specification no result satisfies is deterministic vacuously,
which is the admissibility kind's question -- and the mutation gate uses the same result
about the same file.

The suite's breadth is the number of questions it asks, not the number of files it
ships, so a case that contains another adds nothing to the gate's result: the shipped
implementation, the pre-fix implementation whose rejection `spec.discriminates` already
asks for, or an earlier case. The comparison is over the implementation regions with
comments and layout dropped, under every checker; a uniqueness case is compared by behavior
as well, executed on the same drawn inputs as the pre-fix implementation and the other
uniqueness cases where the files run, and proved equal to them where the checker proves,
since a second copy with one assertion added asks nothing new and a textual comparison
would pass it. A repeat is set aside: named in the verdict and in `evidence/battery.txt`
with what it repeats, not checked, and the suite judged on the cases that remain. Those
fail it for the repeat only by leaving a kind without a case -- the determinism lemma
decides a uniqueness kind left empty this way, as it decides one never drafted -- and then
a repair rewrites the set-aside cases and leaves the specification alone. A drafted case
whose text repeats another file is not written into the bundle at all where its kind keeps
another case, so a first draft ships no case that asks nothing of its own; one a repair
leaves is written as it left it, and set aside here.

A proof the rival writes can be missing a step, and then the checker rejects a correct
rival exactly as it would one the specification forbids. Under a prover, a rejected
soundness rival and the shipped implementation are therefore first executed on the same
drawn inputs. When the rival returns what the shipped implementation returns on every
admissible input drawn, it is correct whatever the checker said, and the gate reports it
as `unproved` -- correct, but the checker rejected a step of its own proof -- rather than
as a specification too strong, with the checker's first error as its reason. It is still a
failure, but a repair treats it as a defect of the case: it fixes the case and leaves the
specification alone.

Where running the two cannot decide it, where the checker placed the rejection still can
(`Backend.refusal_site`). Under Nagini, a rejection wholly inside the rival's own
implementation -- a loop invariant, an assertion, a permission -- is a step of its proof.
Under Lean and Velvet, whose checker replays the proof the rival writes, a rejection inside
the rival's own regions is its script not closing, which a specification too strong to
admit it would also produce; the two are read alike, as a case to prove, and the
too-strong question is left to the control the review has to show the checker accepting,
as `verified-swebench` leaves it to its positive control. A rejected admissibility probe
that running cannot decide is read the same way there, as a probe to prove; under Nagini a
rejection inside the probe is a call the precondition rules out, which is the
precondition's finding. One Lean rejection is neither: an error inside the rival's
implementation region is its definition not elaborating, since Lean elaborates definitions
before any proof of them. That rival is not an implementation at all, so a repair
rewrites it, because its implementation does not elaborate, and it is never recorded as a
correct case whose own proof the checker rejected.

Fixing it in a repair is the remedy only while nobody has tried to prove it. Every case the
checker has to accept -- a soundness control and an admissibility probe alike -- goes to a
proof session at drafting, which reads the diagnostics, edits the proof and runs the checker
until it closes or its budget runs out. For a probe that means the proof of each assertion
inside `impl`, since that is where a probe's assertions go; what each of them *states* is
held word for word, so the session closes the probe's goals rather than asserting something
else. It may add claims of its own, such as a Nagini `Assert` stating a fact the next step
needs. A case that reaches the gate with a failed session behind it has already had the
attempt a repair would ask for, so it is recorded as a **`gap`**: the case is correct, the
checker rejected its own proof, and that is evidence the bundle lacks rather than a finding
about the specification. The case is named in the verdict and in `evidence/battery.txt`
with what the session reported, and its kind is still treated as asked, since the case was
drafted and only its proof is missing. The run report lists every such case, and every
`unproved` one, per bundle, whatever the verdict is about.

The same holds the other way round for a uniqueness case the specification accepts. One
that contains the shipped implementation, comments and layout aside, is a repeat, set aside
without being checked. Under a prover, one that returns what the shipped implementation
returns on every input drawn has missed its bug. Neither is a wrong implementation, so
neither is a weakness of the specification, and a repair rewrites the second. It does
the same for a case the checker reached no verdict on: the solution file verified within
the same budget, so what costs too much is the case's own proof. Under a checker that needs
a witness, a case expecting `refute` that the checker reached no verdict on is first asked its
witness, whose builds leave that proof out.

`evidence/battery.txt` records every case whole: its file, its kind and expectation, what
the checker said and its full output, and what running it showed.

## Oracle gates

These need the benchmark's own correctness check, which for some benchmarks means a
container. They run at `--level oracle`.

Whatever a gate concludes from the benchmark's tests is bounded by what those tests are.
Where they are a handful of asserts, a wrong program the asserts happen to pass is a
correct one as far as anything here can tell, and the two audited strength gates inherit
that in opposite directions: `audit.spec_completeness` never files an attack whose
wrongness the tests do not notice, so it is too lenient, while `audit.spec_soundness`
files a control the specification was right to rule out, so it is too severe.
`benchproofer catalog benchmarks` reports which oracle runs each benchmark's tests and
`oracle.reference_resolves` reports whether they ran; neither can tell you the tests are
thorough.

### `impl.conformance`

The paper's conformance gate. Verification establishes that the implementation meets the
specification. This gate establishes the other half: that the implementation does what the
repository's own code does. Without it a bundle proves only that two documents agree with
each other.

The check is a differential comparison, not a test run. `conformance.py` is the one
artifact that makes it: a program that runs in the task's own environment against the
tree with the golden patch applied, imports the real function the fix leaves behind,
compares first the inputs the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds
or edits build (it is drafted with the benchmark's tests,
as the specification is), then draws more, calls the verified implementation on the
corresponding ones, and reports what it covered:

```
benchproofer:compared astropy.modeling.separable._cstack 100000 random matrices
benchproofer:disagrees astropy.modeling.separable._cstack ([[1]], [[1]]) -> the
    repository returns [[1, 0], [0, 1]], the implementation returns [[1]]
```

The program carries the implementation rather than importing it, and the implementation is not
written into the tree. Writing it to the file whose function it corresponds to would overwrite
the function being compared against, leaving the program comparing the implementation with
itself. It is drafted with what `correspondence.md` lists under `Outside the bridge`:
`conformance.py` does not compare on the inputs an `Outside the bridge` entry of the third kind
names, on which the fixed function runs only what the golden patch leaves as it was, and
skipping exactly those inputs is not a narrowing of what the specification admits. For each
such input it draws or is handed, it prints its `excluded` or `inadmissible` line with
`Outside the bridge:` and that entry, quoted as `correspondence.md` writes it, for the reason.
The gate keeps those lines (`outside` in its details), and the equivalence review is shown them
and traces each through the function before the fix and after it, as it checks the entry. A
callee the specification assumes is called for real. A callee whose result the model takes as
an input is called by the repository side alone, as the changed code calls it, to the real
callee or to the stub the repository's own tests put in its place, and the copy of the
implementation is handed what each call returned, in the order the calls were made.

**The comparison.** `conformance.py` converts what the implementation returned, raised or
left changed into the repository's own types and compares there, exactly, on everything
the specification states: the container, the element types, an array's dtype, shape and
mask, the exception class. Converting the repository's result into the specification's
types instead would drop whatever the specification has no field for, so a patch that
changes only that would be one `conformance.py` never sees. What the specification
deliberately leaves out is named in the docstring of `conformance.py` and left out of the
comparison, where review reads it.

**Inputs put back.** After each disagreement `conformance.py` also prints the arguments
the implementation was called with, as a Python tuple literal:

```
benchproofer:witness astropy.modeling.separable._cstack ([[1]], [[1]])
```

The gate keeps each such input in `evidence/conformance-witnesses.json`, together with who
found it and the specification it was found under. The input of each defect the attack
auditor files joins them (`audit.spec_completeness`): an input the specification admits on
which, the auditor says, it promises what the repository does not do. Neither the author nor
a repair session may write that file.

Every later run of `conformance.py`, whichever one the bundle ships, is handed all of
these inputs: Benchproofer defines `BENCHPROOFER_REPLAY`, a dict from function to argument
tuples, ahead of the program's own code. `conformance.py` compares them first and reports
`benchproofer:rechecked <function> <count>`, the count being how many of the tuples handed
to it were compared. An input the preconditions do not admit is reported instead as
`benchproofer:inadmissible <function> <position>: <why>`.

A run that leaves an input neither compared nor declared inadmissible is undecided. So is
a run that declares inadmissible an input a run of `conformance.py` drew, whichever
specification was in force when it drew it: that run built the value the way the
repository's own callers build it, so the run has to say what the two sides do on it, or
why it could not compare it (`unbuildable`, `refused` or `copy-raised`). Only an input whose
declaration names an `Outside the bridge` entry, as above, may be declined, and a defect's
input, which no run drew: a precondition that does not admit it shows the defect is not one. The
verdict
names, under `not_rechecked` in its details, each function a run fell short on. This is what
keeps a disagreement found once in force after `conformance.py` is redrafted, which a seed
alone cannot do, and what keeps a precondition narrowed around a disagreement from burying
the input that shows it.

**What "carries the implementation" means.** Where the backend's language is the
repository's own, `conformance.py` must contain the `impl` region verbatim -- with two
things taken out first, because neither can appear in a program Python runs:

* the backend's **annotations**. Nagini's `Requires`, `Ensures` and `Invariant` are
  what the checker reasons about and are not defined in the task's image, so the Python
  copy of the implementation in `conformance.py` deletes them. A multi-line annotation goes
  whole, brackets counted.
* **comments**. That copy may say the same thing in its own words, or say nothing. That
  holds of a comment trailing a line of code as much as of a comment line: Nagini's
  `self.width = width  # type: int` is carried by `self.width = width`, and a
  `conformance.py` that writes a comment of its own after a line still carries it.
  Comments are told from code by Python's tokenizer, so a `#` inside a string literal is
  code and is compared. A docstring is prose in the same way, so `conformance.py` is not
  held to one either, though it stays in the runnable form, since a function's body can be
  nothing but its docstring.

A block whose only statements were annotations -- an `else:` that holds one `Assert` --
would be left empty, which Python refuses to compile, so it gets a `pass` where its first
annotation stood, at that annotation's indentation. `conformance.py` carries the `pass`
like any other line of the implementation, and a reviewer's submission spliced into
`conformance.py` gets the same, so the program it runs in compiles.

Each backend declares its annotations as `annotation_tokens`. Holding `conformance.py` to
a copy of the region *as written* would demand a file the checker's own language rules
out, which is a contradiction in the gate reported as a defect in the bundle. Nothing
rewrites the copy after a repair: a repair that changes the implementation changes the copy,
and this check holds the copy it leaves to the implementation it leaves.

**Provenance.** The verdict records how far the compared program is from the one the
checker accepted: `direct`, where the implementation runs as it was written, or
`transliterated`, where a translation runs instead. A transliterated verdict tests the
implementation *as translated*, which is the weakest link in the guarantee, so it is
recorded rather than pooled with the direct ones. Two things force a translation: a
language the repository cannot execute at all (Lean, Velvet), and a language that is the
repository's own except for the values it borrows from its verifier -- Nagini is Python,
but `PSeq` is a Viper sequence and no interpreter in the image has one, so an
implementation returning a `PSeq` has no verbatim Python copy, only a translation. Those
names are each backend's `foreign_tokens`, and the verbatim rule applies only where a
verbatim copy is possible. For a backend whose solution file is not Python, Lean and Velvet
among them, the request asks for a port into Python made line by line, keeping the model's
structure, each line ending in a comment naming the line of the model it ports, so that a
reviewer can check the port against the model. A function
`conformance.py` reports `skipped` in a line written out in it, naming the function as the
specification does, is not compared, and its body need not be copied into it.

**Findings.** A `conformance.py` that reports a disagreement; one that fails without
naming a disagreement (a program that does not run in the task's environment establishes
nothing); one that does not carry the implementation where it could have; one that ran and
compared nothing; and the tautology of comparing the implementation with a second copy of
the fix rather than with the repository's code, which shows as a reported function that
**names no module the program imports**, so there was nothing to call. `conformance_inputs`
is a target, not a floor: a run that agrees over fewer inputs passes, its summary saying it
fell short of the number aimed at, with `compared_inputs` and `target_inputs` in its details,
since agreement over a few thousand inputs is worth less than over a hundred thousand.

**A note, not a finding.** The same `conformance.py` and the same inputs are run once more
against the task's base commit, as `spec.discriminates` asks of the pre-fix
implementation. A disagreement there shows the comparison depends on the fix, and so does
a run that cannot get that far: code the program reaches only once the fix is applied is
code the fix adds. A `conformance.py` that agrees with the code before the fix too has
reached no value the fix changes, and would agree with an implementation of the unfixed
function as readily as with this one. The gate passes on its other checks and records that
in its summary and details (`undiscriminating`): the evidence `conformance.py` gives does
not cover the change. The review's equivalence auditor is shown the note, and judges whether
the repository side of `conformance.py` calls the code the fix changes
([`audit.equivalence`](#auditequivalence)). The second run is last, after everything else
holds, so a bundle pays for it once and only when it passes.

A bundle with no `conformance.py` fails the gate, so that a repair writes one.

**Trouble that is not a finding.** Four more protocol lines report that part of the
comparison did not happen, and each leaves the gate undecided rather than failing or
passing it:

```
benchproofer:skipped change.Ledger.watch: needs a message broker the image does not have
benchproofer:refused change.Ledger.debit [cents=-1]: ValueError: an amount is never negative
```

`skipped` names a part of the implementation `conformance.py` did not compare, and why: a
function nothing in the task's environment can call. It is not for a function that is
merely awkward to reach: a method is reached by constructing its object, and a function
that takes a callable or passes a value through to one is compared by building it around a
stub in that callable's place.

The other three name an input the specification admits that `conformance.py` did not
compare, each by what stopped it. `conformance.py` builds the repository's side of each
input in a step of its own, before the call, which is what keeps these apart from the
function raising: a raise inside the call is the function's behaviour and is compared like
a return, so it is a disagreement when the implementation does otherwise.

* `unbuildable`: `conformance.py` could not build the value in the repository's own
  representation -- the encoding has no image for it -- which is a defect of
  `conformance.py`;
* `refused`: the repository refuses the value: built the way its own callers build it, its
  constructor or validator raises. That is a finding about the specification's domain,
  which admits an input the repository does not have, and what resolves it narrows nothing
  the specification admits: an entry under `Outside the bridge` naming them as values the
  repository never has, with `conformance.py` building each input from a repository value
  made the way the repository's callers make one, or, in a first draft, a model whose types
  have no such values;
* `copy-raised`: the Python copy of the implementation in `conformance.py` raised. The
  verified implementation raises nothing its specification does not declare, so such a
  raise is the copy's defect, most often a Python class written to replace a verifier type
  such as `PSeq` that lacks an operation.

The gate gives one verdict for these lines, quotes them, and counts the inputs it did not
compare by reason in its summary (`blocked_by` in its details), with what resolves each, so
a repair reads which reasons it has. A `benchproofer:blocked` line, which names no reason,
is read and counted the same way, as one that gives none. A value the specification's
preconditions exclude is no such input. A `conformance.py` that draws one and sets it
aside, because the preconditions exclude it, says so with `benchproofer:excluded <input>:
<the line of the specification stating the precondition>`, and the gate counts it as not
compared unless that line is one of the specification it judges. An input not compared is
reported before a part declared `skipped`, and a disagreement outranks both.

A line that starts with `benchproofer:` and has none of these shapes -- a function named
with a description and spaces in it, a count written in words, a word the protocol does not
have -- is one no reader parses, and, passed over, it would be lost: a comparison over any
number of inputs printed that way reads as none, and a disagreement as agreement. So the
gate quotes it as printed, beside the shape the protocol gives a line of its kind (every
shape, when the word is not one the protocol has), and is undecided. It is reported after a
disagreement and ahead of everything else, all of which read the report as though it were
whole. A submission put through `conformance.py` by the review's auditors is left undecided
on such a line for the same reason, with the line named in its row.

The drafting stage runs `conformance.py` once where this gate will, and sends it back once,
in the conversation that wrote it, when the run establishes nothing (a `conformance.py`
this gate objects to after that is the repair session's to fix): a crash, a run its time
budget cut short, nothing compared, a comparison with a name no module it imports defines,
or a line no reader parses, quoted with its shape. A part declared `skipped` is sent back
asking for a bridge to it; a redraft that declares it again is believed and left to this
gate. A `skipped` line printed because an import failed, or by a program that failed having
compared nothing, is sent back as the crash it is. A disagreement, and an input it could
not compare, are never sent back, and are this gate's to weigh: asked about one, a language
model can address it by no longer drawing the input it was found on.

**Which function.** The drafting prompts list the functions the golden patch defines or
edits, not one it touches only in its comments, docstring or layout, the module-level and
class-level names it binds or edits the value of (a table it adds an entry to, an attribute
it adds to a class), and the benchmark's own `symbols` list (`core.sites`). A function is
edited when a changed line sits in it, read from the Python source of the file in the
task's working copy: before the fix for a line the fix removes, after it for a line it
adds. That reading, of the golden patch and of the test patch, is made once at drafting and
kept in the bundle's `manifest.json`; a repair, the review and the leakage gate read it from
there, and a bundle without it is read off the diff, as the leakage gate's section says. The
specification models one of them, or a function the golden patch changes on the path from
it, under a type abstraction: `conformance.py` then constructs the object, stubs what it
touches, and bridges each simplification back, writing the mapping in its docstring. What
the model's parameters and result may be is the drafting rule
(`formalize/templates/sites.md`) -- what the function reads at entry, and what the
FAIL_TO_PASS tests check -- so a value the fix itself computes cannot enter as an input.
This follows `verified-swebench`'s `conformance_check.py`, which "bridges any type
simplifications from mapping.md ... and diffs the shadow against the patched repo
function", the shadow being the Python copy of the implementation. The list is not checked
against the functions `conformance.py` reports comparing. Whether the comparison depends on
the fix is what the run against the base commit, above, notes.

Agreement over any number of inputs does not establish fidelity; one disagreement
refutes it. `audit.equivalence` is the other half of this boundary, and it is the half
that reads the correspondence rather than running it.

### `spec.axioms_grounded`

A proof about realistic code is a proof modulo its assumptions. A task that parses JSON,
opens a socket, or calls into another subsystem of its own repository cannot be verified
at all unless some callees are assumed rather than modeled, and the proof is then worth
exactly what those models are worth. This gate, with `audit.axiom_soundness` the paper's
axiom-soundness gate, is what keeps the qualifier from being silent: whatever the
specification assumes is put to the callee itself, in the environment the benchmark's own
tests run in. An assumption is *grounded* when `axioms.py` has checked it against the real
callee there.

Which callee may be assumed is one rule, which every prompt that states it includes from
`core/templates/callee-rules.md`. A callee the changed code calls is unchanged when the fix
does not change its behavior, whether the code before the fix made the call or the golden
patch adds it; type annotations, a renamed attribute or variable, a helper inlined into it,
the same function bound under a new module or name, layout, comments and docstrings do not
change it. An unchanged callee is modeled, by a short definition computing what it computes,
when the checker can state that exactly on the inputs the changed code gives it; otherwise
it is an axiom the model calls with the call's arguments, with the weakest contract under
which the golden patch's own calls to it verify. Either way its result is never a parameter.
A function the golden patch adds, or a callee whose behavior it changes, is neither: that is
the operation the task is about, and it is modeled in the implementation. What of the
process's own state the benchmark's tests set between calls, such as an option, is an input
of the call, which the model takes as a parameter.

That rule is relaxed only for a callee whose definition or axiom, written as the rule asks,
failed twice, as Benchproofer's code decides from this run's rounds (`core.rounds.eligible`),
never a language model: in two rounds with a repair between them, `audit.axiom_soundness`
refuted the callee's axiom or definition, or `spec.verifies` did not pass and the checker
reported an error on a line of its declaration in the `axioms` region. Two rounds judged with
the same number of repairs on record, as a round that asks an auditor again about an unchanged
bundle is, count once. A timeout of the whole check, such as Nagini's, names no line and counts
for no callee; and a fuzzer's refutation counts the same whatever it shows, since its `refuted`
line is free text and nothing in it tells a program that two calls with the same arguments
returned different results. The repair's brief and the prompts of the equivalence and
faithfulness auditors list each such callee with those rounds and the lines the fuzzer or the
checker printed about it, and the rule for taking its result as an input
(`core/templates/inputs-rules.md`); a prompt that lists none
states the rule above alone. For a listed callee, the result of a call may be an input of the
model, as `verified-swebench`'s models take one, for one of two reasons: its result can differ
between two calls with the same arguments, because it depends on something outside the
process (a server or device it talks to, a subprocess it runs, the clock, randomness), or the
checker cannot state it within its limits, such as a recursive type Nagini cannot express.
Such an input meets four conditions. It is the result of an unchanged callee's call whose
arguments the fix leaves as they were: a function the golden patch adds, a callee it changes,
code inside a changed function (a branch or guard of it included) and the result of a call
whose arguments the golden patch adds, changes or computes are never inputs, since the input
would then hold what the fix computes. Its reason holds. The model's domain admits every value
the callee returns on the inputs the benchmark's tests and the statement hand the changed
code, `conformance.py` hands the implementation the real callee's result (the repository side
makes the call, to the callee or to the stub the repository's own tests use), and each call's
result is an input of its own, in the order the calls are made. And the model states each such
call as an output, the arguments of each call in the order the calls are made (or, for each
element the changed code goes through, whether it made the call and with which arguments),
and an obligation states them, since an implementation that made the call with other
arguments would otherwise read the same input and meet every obligation; `conformance.py`
compares them with the arguments the repository side's call was made with. Each such callee
is listed in `correspondence.md` under `Callee results taken as inputs`, with its call site and
its reason, and the run report lists it per bundle under the same heading; it fails no gate. Whether a call's
arguments are ones the golden patch changes is left to the equivalence auditor: the list is
per callee, while the condition is per call, and a call whose arguments the fix computes on
an earlier line shows nothing on the line of the call.

An assumption is declared on one line of the `axioms` region, in the backend's comment
token, naming the callee it represents:

```python
# benchproofer:axiom json.loads
```

A definition that models an unchanged callee is declared on the line above it,
`# benchproofer:models posixpath.normpath`, and `axioms.py` compares the two on the inputs
the changed code can give the callee.

The bundle then ships `axioms.py`, which exercises the real callee against the model and
reports what it covered:

```
benchproofer:grounded json.loads 200 inputs drawn from the model's domain
benchproofer:refuted json.loads loads('1 ') is 1, the model says malformed
```

`axioms.py` is always Python, because it runs where the benchmark's tests run rather
than where the checker does; when the solution is Python too, it must carry every
declaration line of the `axioms` region in order, so that what it exercises is the model
the checker was given and not a second one. A line may be carried as code or quoted
behind `#`, and quoting is usually the only choice: an assumption is a contract with no
body, written in names from the verifier's library, which the task's image does not
have. The region's prose is not part of what has to be carried: its comment lines,
including the `benchproofer:axiom` directives, a comment trailing a declaration line, and
its docstrings, which say what a declaration means and are often all the body a
`@ContractOnly` function has. The drafting stage writes the quotation itself, after the
program the language model wrote, unless the program already carries the lines; a repair
that changes the region changes the quotation too, since nothing rewrites it after the
repair session. A verdict that finds a line missing names the first one. An `axioms.py` for a callee the task's own
fix introduces asks for the patched tree on a line of its own, since at the base commit
that callee does not exist:

```python
# benchproofer:axioms apply-fix
```

The gate runs `axioms.py` with a recording of every function the run calls, put ahead of
the program's own statements on a line the program already has, so the lines a traceback
names are the program's own. As the run ends, the recording prints for each callee whether
its code ran, looked up among the modules the run imported:

```
benchproofer:calls json.loads no its code never ran
```

A callee whose module is a file of the repository the run never imported did not run
either. Whether a callee ran cannot be told when it is not Python code, when its path names
no module the run imported and no file of the repository, or when the run started another
process; the verdict says which, and does not count it against the bundle.

Five outcomes are findings: an assumption no `axioms.py` checks, an `axioms.py` that
reports a disagreement, one that fails without naming one (a program that does not run in
the task's environment establishes nothing), one that exits zero without exercising
something the specification assumes, and one that reports a callee grounded without
calling it, which checked the model against a copy of the callee. A `refuted` line is a
counterexample rather than a shortfall of a search, so unlike a surviving mutant it is a
failure under a falsifier exactly as much as under a prover. The verdict quotes the first
few `refuted` lines as `witnesses`, and `evidence/axioms-refuted.txt` holds all of them,
since which input refuted an assumption, and what each side did on it, is what a repair
has to reason from.

A bundle whose `axioms` region names a callee and that ships no `axioms.py` fails the gate,
whether or not the solution verifies: drafting writes `axioms.py` only beside a file the
checker accepts, and a repair writes it otherwise, so a repair that adds the assumption its
proof needs writes the program that checks it too. Whether the golden patch changes a callee
the `axioms` region names is `audit.equivalence`'s question.

Passing is a floor rather than an argument: an `axioms.py` written by whoever wrote the
assumption tends to exercise what the assumption already covers. That is what
`audit.axiom_soundness` is for.

### `oracle.reference_resolves`

The paper's resolution check: the golden patch passes the benchmark's tests. This gate
judges the original benchmark's reproduction code, not the bundle: a missing image, an
unapplied test patch, or a test id that no longer exists makes every conclusion drawn from
those tests void, including a favorable conformance verdict. It costs one run of the
benchmark's tests per task, which is why it is a gate of its own rather than a precondition
buried inside another one. The result is recorded, with the output that produced it. A
golden patch that does not resolve is run again, up to three times in all, and resolving on
any attempt is enough, as it is for `verified-swebench`'s G-RESOLVE: a test that races on a
loaded host does not make the reproduction code misconfigured. Nothing a draft or a repair
writes is among its inputs, so a pass or a failure recorded from the same `task.json` and
`reference.patch` by the same gate code is kept as it is: the tests run once per task, not
once per round, and again only for a task whose frozen files or the gate code changed.

A failure drops the task (`dropped`, not `rejected`): it is a check on the task, not on
anything shipped for it. `run` asks it first, of the frozen task alone, so a dropped task is
never drafted, reviewed or repaired. A judgment that finds it failing later ends the loop.
An error, a timeout or an unavailable oracle measured nothing and drops nothing.

## Audited gates

Whether a specification is strong enough to be worth proving anything about, and whether
it describes the task it claims to, are questions a program cannot pose to itself. These
seven gates report what an independent review concluded, and they run at
`--level audited`. `benchproofer audit` produces the review; see
[Review](concepts.md#review) for what it writes and [the CLI reference](cli.md#audit) for
how to run it.

None of them takes a reviewer's word for anything a program can check instead. The two
strength gates re-run every implementation a review submitted, through the checker and
through the benchmark's tests, and read the attack validation auditor's ruling only on a
submission that cannot be determined by execution; the three judgment gates report a conclusion
only while every file it was reached from still has the digest it had when the reviewer read
it. So a review is evidence, not a verdict, and an out-of-date review is neither.

Every auditor is told that an input, a patch or a witness that breaks a language contract is
no evidence either way, which the gates count neither for nor against the specification: a
conversion or a comparison overridden to raise; a value built to defeat a
precondition rather than to satisfy it, such as a subclass whose comparison satisfies
`n >= 0` while it holds a negative value, which disagrees with how the precondition is
written rather than with what the specification or an assumption says; private state of a
library object written; an object's hash changed while it is a key. The code the benchmark
ships is entitled to assume those hold, and under a Python backend any assumption at all
could be refuted that way, which would fail every bundle for the same reason and none of
them for the task.

### `audit.independence`

The review was not written by whoever drafted the bundle. A language model asked to
review its own work restates its own opinion of it, which is not a second look at anything.
The manifest records who drafted the artifacts and who reviewed them; when the two match,
this is a self-review and the gate says so.

Pass `--audit-model` so the review comes from a different language model than `--model`.

### `audit.spec_completeness`

The paper's completeness gate, the too-weak direction: can anyone write an implementation
this specification accepts and the benchmark's own tests reject? Such a specification
certifies nothing, because a solver could satisfy it without solving the task.

The reviewer is asked for wrong implementations, called attacks, and each is re-run twice
over. The regions the reviewer wrote are spliced into the solution file and the checker is
asked; then the bundle's own `conformance.py` is run with the reviewer's implementation in
place of the drafter's, and what the repository's code makes of it is read off the same
`disagrees` lines `impl.conformance` reads. A submission the checker accepts *and* the
repository disagrees with is the finding. Neither result alone is one, which is why both
are needed.

Substituting into the bundle's own `conformance.py` is what makes the two results
comparable: how inputs are drawn and how the repository is reached stay byte-identical, so
the only thing that varies between the drafter's implementation and the reviewer's is the
implementation. It is also the only instrument that can ask the question at all. Running
the benchmark's test suite over a tree with the submission's one file replaced fails on the
absence of the rest of the fix, for every submission alike -- and since a submission the
checker accepts and the benchmark's tests reject *is* this gate's finding, that failure
would not merely lose information, it would manufacture a finding against every
specification that accepted anything.

An attack the checker accepts is then ruled by one rule, over what the programs found when they
ran it and the reference implementation on the same drawn inputs, and ran its patch. Where
`conformance.py` with the attack's code in it prints a `disagrees` line, the attack succeeds
whatever its patch does: its implementation is wrong, and the specification too weak. Where a
run showed it equal to the reference implementation -- the two files agree on 100 or more
admissible inputs drawn, or on every admissible input of a finite domain, with every line the
attack changes run, under Lean and Velvet the checker proves them equal, or `conformance.py`
agrees over the inputs it compared and the two files, executed on the same drawn inputs, did
nothing different -- the attack fails, its implementation correct, and counts toward the gate's
result: the specification accepted that behavior in its own implementation, and
`verified-swebench` also counts such an attack, its implementation correct and equivalent to
the golden patch, toward its five. Otherwise its patch decides, as `verified-swebench` decides every attack: the attack
succeeds where the benchmark's tests reject its patch, its implementation wrong. Where they pass
it, the attack cannot be determined by execution, and the attack validation auditor rules on it
(below), with or without a witness test. That holds, too, of an attack the two files differ
on when executed on the same drawn inputs: the specification may leave out a behavior the
statement does not ask for and that neither the FAIL_TO_PASS tests nor the PASS_TO_PASS tests
the test patch adds or edits check, so a difference the tests do not see is a question about
the task, not a weakness by itself. Executing the two
on the same drawn inputs is no evidence either way on fewer admissible inputs than that, a
parameter type nothing draws, a callee stated as an axiom, a file reaching outside a closed
module, a run that did not finish, or a changed line no draw reached, and a Lean or Velvet
attack with no equality proof is shown equal by nothing; `conformance.py`, where it can run the
attack, or else its patch, decides those.

The two Nagini files are executed on the same drawn inputs as Python, contracts rewritten -- a
`Requires` that fails marks an input as inadmissible, everything else a reader reads is dropped
-- over inputs drawn from the specified functions' annotations, integers taken from the
literals the files use. An argument of a class the model defines is built by that class's own
constructor from drawn arguments, and each field the class declares is then set to a drawn
value of its type: the precondition is the domain, and any state it admits is an admissible
input to two implementations of one specification, whether or not the constructor builds it.
Each file gets an equal copy, and two objects are the same where their classes and fields are.
Where every parameter takes its values from its type's whole range -- `bool`, `None`, an
`Optional` of one, an object whose constructor's parameters and fields are all such -- every
combination is run, the enumeration is the domain rather than a sample of it, and agreement on
all its admissible inputs decides the question however few they are; a pool that samples its
type, as integers, strings and sequences do, needs the 100. A model may define and call special
methods; what leads out of the module -- `__import__`, `__globals__`, `__builtins__`,
`__subclasses__`, a frame -- is what keeps a file from being run. A name or an operation the
run does not provide, which a file the checker accepted cannot lack, keeps the file from being
run, which is no evidence either way. That run, and the proof, come first, and `conformance.py`
is not asked about an attack they show equal: it compares model values with repository ones, so
of an attack equal to the reference implementation it would say what `impl.conformance` says.

Under Lean and Velvet the two files cannot be executed on the same drawn inputs, so the same
question is proved instead (`core.echo`), and an attack the checker accepted is equal to the
reference implementation if either proof closes. The first: the specification admits one result
per input -- a determinism lemma the checker accepts, over each Lean predicate or over the
postcondition Velvet's `prove_postcondition_decidable_for` decides for each method, offering
the bundle's own lemma before general tactics -- and the attack states every claim the solution
file states about its implementation, so its acceptance means it returns the reference
implementation's result wherever the specification speaks. It is asked once per bundle. The
second: the attack's implementation regions are elaborated in a namespace of their own beside
the solution file, whose proofs are taken out, and the checker proves each function both define
-- for a Velvet method, the executable `extract_program_for` derives -- equal to the reference
implementation's, by a fixed list of tactics each of which has to close the goal, resting on no
axiom beyond Lean's own. A region holding a command that changes how the file is read
(`set_option`, `macro`, a namespace closed) is not put beside the solution file. Where an
attack is a weakness under Lean, the checker could not prove the specification admits one
result per input, and the attack proves the solution file's claims, the verdict names the
determinism lemma, one conjunct per predicate: a repair that states and proves it in the proof
region makes the attack equal to the reference implementation, since the probe offers the
bundle's claims first.

Every attack files its equivalent patch, the golden patch with the attack's change
made in it, and the benchmark's tests are run on it unless `conformance.py` told the attack
apart from the repository.
Because it carries the whole fix, the tests fail only where the attack does. A rejected
patch is run again, three times in all, and resolving on any attempt is enough, as it is for
`oracle.reference_resolves`; a patch that makes the fix's own change resolves by definition
and is not run at all. The patch is the reviewer's account of what the implementation is,
and everything that would make the result about something else leaves the attack undecided
instead, with that reason: no patch, a reply that is not a unified diff, a patch that does
not apply or that fails every PASS_TO_PASS test, and a benchmark whose tests do not pass
its own fix here (read off `oracle.reference_resolves`). The patch of an attack shown equal
that the tests reject is a repository change the specification cannot tell from the fix,
unless the patch changes something the attack does not: such an attack cannot be determined by
execution either, and the attack validation auditor rules on it.

An attack whose patch the tests pass may be filed with a witness test, as `verified-swebench`'s
auditors report only what a run decides: a Python program Benchproofer runs where
the benchmark's tests run, once on the fixed code and once with the attack's equivalent patch
applied in place of the golden patch (`Program.patch`). It has to pass the first time and fail
the second, and it cites, in a field of its own (`cites`), the sentence of the statement, the
FAIL_TO_PASS test, or the PASS_TO_PASS test the test patch adds or edits that it checks. When it
passes the first time, fails the second and cites something, the attack cannot be determined by
execution: no program checks that what the test cites asks for what it checks, so the attack
validation auditor rules on that (below), and what it is shown lists the test and both runs'
results. A witness test that fails on the fixed code, passes with the patch too, or cites
nothing is evidence of nothing, which the ruling says, and the attack is judged as though it
had none. It is not run for an attack a program or the tests already decided. `./tools try`
runs it the same way, and names the attack it leaves to that auditor.

A bundle whose `conformance.py` does not mark the implementation it carries leaves a
runnable submission undecided, since there is nowhere to put it.

The attack auditor files, beside its attacks, each defect it showed by running code that no
attack of its shows: an input the specification admits on which it promises what the
repository does not do (`defects` in `audit/index.toml`). A defect names a function
`conformance.py` compares, as the last `impl.conformance` verdict lists them, and its input as
the arguments that function is called with, a Python tuple literal; one without both is not
filed. Its input joins those `conformance.py` is handed on every run (`impl.conformance`,
above), and the round that filed it judges `impl.conformance` again beside the gates that read
the review, so a disagreement on it fails that gate as one on a drawn input does.

Each attack or control that cannot be determined by execution is a question about the task or
about a proof, and the attack validation auditor, a session of its own on the reviewer's
language model, rules on each once the gates have re-run the review's submissions:

- of an attack whose patch the tests pass, whether the behavior it changes belongs to what the
  task requires, which it does when the statement asks for it or a FAIL_TO_PASS test, or a
  PASS_TO_PASS test the test patch adds or edits, checks it (the attack then succeeds;
  otherwise it fails);
- of such an attack whose witness test passes on the fixed code and fails with its patch,
  whether what the test cites asks for the behavior the test checks: a value returned, an
  exception raised or an effect on state (the attack then succeeds; otherwise it fails). A
  sentence asks only for what it states, one naming a quality goal, such as performance,
  compatibility, robustness or clean code, asks for no behavior, and a test id asks for what
  that test asserts, on its inputs or on others of the same kind;
- of an attack shown equal whose patch the tests reject, whether the model is at fault, so that
  the specification accepts a patch the tests reject (the attack succeeds), or the patch (it
  fails). A patch that fails only because a test of the benchmark's replaces, on the object
  itself, a method whose model the attack computes instead of calling it is the patch's
  fault: such a test checks which call the code makes, and the attack shows a call the model
  does not represent, not a wrong result. Every auditor is told so, so that the attack
  auditor does not file such an attack.

A ruling counts only when it names the input and the sentence of the statement, the test or the
obligation it rests on (for an attack with a witness test, the input the test runs with the
behavior it checks there, and what the test cites), and only while the specification (its
axioms included), the implementation, the submission's files and what its witness test cites
read as they did when it was reached (`reads` in `audit/index.toml`, as
`core.readings.ruling_reads` names them). While an attack or a control that cannot be
determined by execution has no ruling that counts, the gate is undecided, listing it under
`unruled`, and the auditor is asked about it (again, once per state of the bundle; see [Where a
verdict goes](#where-a-verdict-goes)). One the auditor still leaves without a ruling after it
was asked again is discarded: it counts neither way, and the gate decides from what is left.
The ruling and what it rests on go into what the gates ruled of the submission (`rulings`),
which the repair and the next review read.

Each submission's row is recorded with a digest of what it was computed from (its files, the
solution file, `conformance.py`, the task, the golden patch and the recorded
`oracle.reference_resolves` verdict) in `evidence/audit-outcomes.json`, and a later judgment by
the same gate code of the same files reads the row instead of running the submission again, so
the benchmark's tests run once on a submission whatever rulings are added beside it. A row the
checker reached no verdict on, or an accepted attack the benchmark's tests established nothing
about, is run again.

A patch the tests reject is reported with whether it fails a FAIL_TO_PASS or a PASS_TO_PASS
test, as `verified-swebench` reports it to its repairs:
one failing a FAIL_TO_PASS test does not fix the bug, and one passing all of those and
failing a PASS_TO_PASS test fixes it and breaks a property the fix preserves, which is what
the repaired specification then has to state.

The gate passes when enough attacks have been decided and none of them broke the
specification; `audit_min_attacks` sets how many. An attack decided by the attack validation
auditor's ruling counts, and a discarded one does not. Falling short is recorded as undecided,
not as a pass: a specification nobody managed to attack has not been tested.

### `audit.spec_soundness`

The paper's soundness gate, the too-strong direction, and it needs its own submissions
because attacks cannot show it. A specification that refutes everything survives every
attack and is useless: it demands something the task never asked for, so the only way to
satisfy it is to write the one implementation its author had in mind.

The reviewer is asked for correct implementations written differently from the shipped
one, called controls. Each is judged by the bundle's `conformance.py` with the control's code
in place of the shipped implementation, and never by the benchmark's tests: a control the
checker refutes and `conformance.py` finds to agree with the fixed code is the finding. The
gate passes when the specification admits `audit_min_controls` of them (one by default; the
reviewer is asked for `audit_controls`, three by default). A control that cannot
run as written, or that `conformance.py` cannot decide, is admitted on the checker's
acceptance alone, the rule `verified-swebench` holds a positive control to; rejected by the
checker, it is left undecided rather than put to the benchmark as a patch, since the patch
that resolves is the golden patch and would turn any rejection into a finding. The
attack auditor's rules for controls say the same.

Under a prover a refused control is either the specification ruling it out or a proof it
lacks, and neither the checker's verdict nor the line its error names says which: Nagini
reports a missing loop invariant at the postcondition it fails to establish. So the attack
auditor proves each control before it files it, as `verified-swebench`'s audit asks of its
positive control: a structurally different but correct control must verify. The auditor runs
the checker on it and writes the proof the checker needs, in its own session and budget,
and files one it still cannot get accepted as unproved, saying in its claim what it tried.
A control the prover refuses is then a gap, one that cannot be determined by execution, named
in the verdict (`rulings`) and shown with the auditor's claim to the attack validation auditor,
who rules on whether it is correct and whether the specification is what refuses it. Correct
and refused by the specification fails the gate. Correct and refused for a proof it lacks is
unproved: it counts neither way, and is listed under `unproved` and in the run report beside
the property-based test suite's correct cases refused on their own proof. Not correct, it is
discarded. So is a control a falsifier refuted that nothing could run against the repository,
which the same auditor rules on. The specification is what refuses a control where the open
goal is about what an axiom returns and the axiom says nothing that decides it: no body can
supply that proof, the golden patch's included. `verified-swebench` likewise never counts a
positive control that does not verify as a too-strong finding. While a control has no ruling
the gate is undecided, as for an attack.

Under Lean 4 and Velvet, where a refusal needs a refutation witness to say anything
(`witness_required`), a refused control may be filed with one: a claim proved at one concrete
input that the specification refuses what the control returns there, checked as the
property-based test suite checks the witness of a case that expects `refute`
(`spec.strength.battery`): it has to hold of the control and
fail against the reference implementation. With it goes a witness test, run once where the
benchmark's tests run with the golden patch applied, which passes only where the fixed code
returns at that input what the control returns there. When the checker proves the witness and
the run agrees, the specification refuses a correct implementation, and the gate fails. Short
of either, the control is a gap as before, with what fell short in its entry under `rulings`.

The two gates read the same re-run rows for opposite questions. An attack the checker
accepts and the benchmark's tests pass does not admit the specification, as
`verified-swebench`'s positive control has to be a file of its own: it may still break a
behavior the task requires, which the attack validation auditor rules on. A refuted attack is the specification holding, as in
`verified-swebench`; a correct implementation the specification refuses is a control's
question, and the review files one as a control.

A submission the checker gave no verdict on is set aside by both, since there is no
verdict to weigh, and named in the census either verdict carries. A timeout or a solver
that gave up is a fact about the search rather than about the specification: counted as a
refutation it would credit the specification with defeating an attack nobody ran, and
report a control the prover merely could not finish as a correct implementation the
specification rules out.

Both directions depend on a distinction a prover does not draw for you: an implementation
it rejected because the specification rules that implementation out, and one it rejected
because the proof it needs was never written. Read as the first, the second is an
over-constrained specification to one gate and an attack the specification survived to the
other, and only one of those errs on the safe side. A falsifier draws that distinction, and
leaves another: a control it refutes on a concrete input is a finding only if the input is
one the task allows, which is not something a reviewer can tell without seeing it. So each
reviewer runs the gate a submission is judged by, and sees the checker's own output, before
it submits anything; see [Review](concepts.md#review).

Five things are screened out before the checker is asked, so a reviewer cannot inflate
their own evidence: a submission whose file cannot be read, one aimed at a specification
the bundle no longer ships, one that reaches for a construct the solution file does not
(`assume`, `sorry`, a directive that turns the checker off), one that proves a claim of its
own instead of the solution file's, since then what the checker said is not about this
specification, and one whose implementation repeats another's, or the shipped one, once
comments, indentation and blank lines are left out. Each is set aside with a reason rather
than counted toward the gate's result.

The submissions on record are the review of the specification as it stands. While it
stands they are re-run each time the gates judge the bundle, and an attack auditor asked again
adds to them. A repair that changes the specification makes the attack auditor due again, as
`verified-swebench` audits a repaired specification afresh: its earlier submissions are not
re-run, and the two gates judge what this review files. The auditor is shown each earlier
attack's claim with what the gates ruled (`rulings` in either verdict's details) and the
repair's entry for it, and writes again first each one the gates ruled a weakness, against the
specification as it now stands, unless the repair's entry for it shows with evidence that it was
not a defect; then it writes new attacks up to the number asked for. The earlier
submissions' files stay in the archive of the round that judged them.

### `audit.faithfulness`

Does the specification describe *this* task: nothing the task requires left out, nothing
it never asked for demanded? This is the question the rest of the ladder cannot reach. A
specification can be verified, strong, internally consistent, and about something else.

The task is taken as the golden patch resolves it: the repository with the fix applied is
what the specification is judged against, since that is the code the tests vouch for, so a
restriction the statement names and the fix never checks is not missing from a
specification that leaves it out. What is judged is behavior, in the functions the fix
changes, including in one the bundle does not model; documentation, configuration and
changelog entries the fix also adds are not, and neither is a function it touches only in
its layout, its comments or its docstring, which Benchproofer tells from the diff's code
before listing the functions the fix changes, as `core.sites` does, for the reviewer. A function whose only change
is a refactor keeping its behavior is checked only where undoing the refactor fails one of
the benchmark's tests. A behavior on inputs for which the fixed function runs only what the
golden patch leaves as it was, and which neither the FAIL_TO_PASS tests nor the PASS_TO_PASS
tests the test patch adds or edits check, is not checked either: an
`Outside the bridge` entry of the third kind naming those inputs accounts for it, checked as
`audit.equivalence` checks one (below). These are the reviewer's rules and not the gate's. A finding has to
name the input on which the specification and the fixed code come apart.

Correct means what the benchmark means by correct: the benchmark's tests report the task
resolved, the PASS_TO_PASS tests included. A row of the coverage table is checked against
fewer, as in `verified-swebench`: the FAIL_TO_PASS tests, and the PASS_TO_PASS tests the
task's own test patch adds or edits, which the reviewer is shown with the fix itself. Which
test a changed line of the test patch sits in, and in which class, is read from the test
file's source as the drafting list's functions are. A test the test patch adds or edits that
the benchmark lists as neither judges no fix, and is not among them. A PASS_TO_PASS test the
test patch leaves alone holds the specification through attacks instead: an implementation
the specification accepts that breaks one is too weak (`audit.spec_completeness`), and the
patch of an attack shown equal to the reference implementation that breaks one is the
attack validation auditor's to rule on (also there). An attack reaches only the inputs the
specification admits, so the model's domain admits every input on which a function the fix
changes returns normally and which the benchmark's tests, the PASS_TO_PASS tests included,
or the statement hand it. A precondition, a parameter type or a parameter fixed to a
constant that leaves out such an input is a finding, the reviewer's to make, unless an
`Outside the bridge` entry of one of the three kinds `audit.equivalence` lists (below) names
it. The specification must state a change the issue statement asks for, even when none of
those tests checks it; leaving it out is a finding, the reviewer's to make. A behavior none
of those tests checks and the statement does not ask for -- a message's wording, a branch no
test reaches -- is incidental, and a specification that leaves it out of its obligations is
not unfaithful. One that pins it, so that a correct patch without it is refused, demands
more than the task does: the specification admits the golden patch's behavior there without
demanding it.

The reviewer's verdict comes with a coverage table: one row per behavior, with the test that
checks it and the line of the specification that states it. An obligation states a tested
behavior when it is about the value the test checks, or about what the changed function
returns, raises or modifies when code the golden patch does not change computes that value
from it, and then only with a frame -- the function changes nothing else that code reads --
and only if the model's types tell apart every two effects that code treats differently. A
clause about a proxy -- a flag, an emptied cache, a local the function computes on the way --
whose link to what the test checks lives in `correspondence.md` or in `conformance.py` does
not state the behavior (`core/templates/frame-rules.md`, which the drafting session and the
repair are shown as well). The verdict decides, as in
`verified-swebench`, where the evidence beside a judgment never turns a pass into a failure.
The table goes into the verdict's details, and a repair is shown its rows that name a test
and no obligation. The reviewer also names, for each FAIL_TO_PASS test, every value its
assertions compare and the obligation that states each, where a compared value no
obligation states is a finding, and says what the bundle's pre-fix implementation returns
on the input the test builds: one that already passes the test does not have the bug, and
that is a finding. A test that fails on the code before the
fix only because it uses a name the golden patch adds, or only because the fixed code returns
the same content in another Python type the model's types do not represent, is set aside
from that check and still counts for coverage.

The question is scope alone, as in the SWE-Proof paper: every behavior the FAIL_TO_PASS tests
and the PASS_TO_PASS tests the test patch adds or edits check, and every change the statement
asks for, has an obligation, and nothing beyond those is demanded. The auditor rules on no
submission: an attack or a control that cannot be determined by execution is the attack
validation auditor's to rule on (`audit.spec_completeness`, `audit.spec_soundness`), and a
defect the attack auditor shows by running code is an input handed to `conformance.py`
(`impl.conformance`). The auditor's `unsound` fails the gate.

### `audit.equivalence`

The paper's equivalence gate. Is the shipped implementation a translation of the golden
patch, rather than a program that resembles it? The benchmark's tests vouch for the golden
patch; if the verified implementation computes something else, every later verdict is
about a different task. Each function of the implementation is compared with the function
of the fixed code it is a translation of; a changed function the bundle does not model is
`audit.faithfulness`'s question. A reviewed bundle with no `correspondence.md`, the claim the
judgment checks, fails the gate whatever the judgment, so that a repair writes it.

The reviewer's verdict decides, as in `verified-swebench`, whose panels' evidence fields
never turn a pass into a failure. The reviewer sets the implementation's operations against
the golden patch's one by one, each as one of the kinds below, and the rows go into the
verdict's details as what it rests on. Only these kinds leave behavior alone, and the
reviewer is told that one operation of any other kind, `changed`, makes the verdict
`unsound`:

| operation | what it covers |
| --- | --- |
| `identical` | the same concrete operation, under other names or another loop shape, computing the same values in the same order |
| `refinement` | the same operation over a refined type, or state the code reads taken as a parameter, or a part of a result, or a call of a listed callee whose result the model takes as an input (see below), with `correspondence.md` saying how it maps |
| `modeled` | a call of an unchanged callee computed by a definition the `axioms` region holds under its `benchproofer:models <callee>` line, which `axioms.py` and an independent fuzzer put to the real callee as they put an axiom; a definition anywhere else or without that line, or one representing a function the golden patch adds or changes, is `changed` |
| `axiom` | a call of an unchanged callee (which callee is unchanged, and whether it is modeled or an axiom, is the rule [`spec.axioms_grounded`](#specaxioms_grounded) states), represented by an assumption that states only what the callee really does; a callee's result the model takes as a parameter is not an `axiom`, and its row is `changed` where that rule does not allow it. An assumption for a callee the golden patch changes is `changed`, and behavior decides that: the call reaches code the golden patch adds or edits, and on some input the call can pass its result differs from what the call reached before the fix. |
| `unchanged` | behavior the fix leaves as it was, which the implementation leaves out or abstracts and `correspondence.md` lists under `Not modeled`, compared in one environment |
| `unbridged` | the operation does what the golden patch does on every input the type bridge covers, and differs only on inputs listed under `Outside the bridge` |

The auditor is shown which callees the `axioms` region has a `benchproofer:models` line for,
read off the solution file, or that it has none, so that it sets each `modeled` row against
the lines that are there.

Where this run's rounds list a callee whose result a repair may take as an input (see
[`spec.axioms_grounded`](#specaxioms_grounded)), the auditor is shown the list, with the rounds
that put each callee on it and the lines the fuzzer or the checker printed about it, and the
four conditions. It checks each callee `correspondence.md` lists under `Callee results taken as
inputs`, and any other parameter that holds a callee's result: an input holding the result of a
callee the list does not name is a finding, and so is one that breaks a condition, above all
code inside a changed function, a branch or guard of it included, the result of a call whose
arguments the golden patch adds, changes or computes, or a call whose arguments no output
states. Either makes the verdict `unsound`; an
input that meets every condition is a `refinement` row. With no callee listed, every parameter
that holds a callee's result is `changed`.

The type bridge is how each of the specification's types maps onto the repository's values,
written in `correspondence.md`. An `unbridged` row is preserving only where `correspondence.md`
declares those inputs in its `## Outside the bridge` section: Lean's `Option` has one value for
a key that is absent and for a key present with the value `None`, and the bundle may declare
that once rather than fail this auditor's judgment on it. A precondition, an
`Outside the bridge` entry or a skip in `conformance.py` that shuts out an input the
specification admitted before, or one the model's domain has to admit, is a narrowing. The
section is for three kinds of input, and no other: a value the model's types admit that the
repository never has where the modeled function is called; a repository value the bridge reads
as another, where no FAIL_TO_PASS test, no PASS_TO_PASS test the test patch adds or edits, and
no sentence of the issue tells the two apart, and the golden patch returns on both or raises on
both; and an input on which the fixed function runs only what the golden patch leaves as it
was: it returns or raises before any changed line, or it tests a condition the golden patch
adds, finds it false, and goes on into a branch the patch leaves as it was, which the entry
names. A behavior one of those tests checks is never left out that way. The auditor checks each
entry: merging an input the golden patch returns on with one it raises on is a narrowing, and
an entry of the third kind stands only if one input it names, traced through the function
before the fix and after it, runs the same lines on both, apart from the false test of a
condition the golden patch adds. An input the model's domain leaves out is not set aside as
`unchanged` where one of the benchmark's tests, a PASS_TO_PASS test included, hands it to a
function the fix changes, which returns normally on it and runs there code the golden patch
changes, beyond the false test of a condition it adds: with no entry naming it, that is a
finding, as under `audit.faithfulness`. A changed operation marked `unbridged` that
`correspondence.md` does not declare is `changed`.

The auditor is also shown what repairs changed in the specification and under `Outside the
bridge` since the bundle was drafted, as a diff against what `manifest.json` recorded then
(`provenance.drafted`). A precondition or an entry a repair added that excludes anything
but the three kinds `Outside the bridge` is for is a narrowing, and the judgment is
`unsound`: that is how a narrowing a repair makes is caught where no program catches it.
None of the three kinds is a narrowing, the third included, and
neither is a change that widens the domain -- an input case added, a precondition dropped, a
parameter type that admits every value it admitted and more.

Anything else is an operation that does something the golden patch does not, and one is
enough for the reviewer to give the verdict `unsound`. The reviewer runs every call it compares in one
environment, the one the benchmark's tests run the fixed code in: one thread of one process,
on that platform, under one working directory, time zone, locale, set of environment
variables and file system, changing none of these between two calls. State the benchmark's
tests set between calls -- an option set through a `set_options` context manager, a setting a
test overrides -- is an input of the call: the model takes it as a parameter, and a program
may set it between calls the way the tests do. Three kinds of difference are set aside, as
programs the task never runs: one that shows only when that environment changes between two
calls, or only on another platform; one that shows only in a state of the environment the
benchmark's tests never build, such as a FIFO where a file is read, an executable that never
exits or a configuration the tests always set left unset; and one that shows only through
what earlier calls in the same process left behind, such as a library exception raised only
the first time a value is asked about, unless a FAIL_TO_PASS test or a PASS_TO_PASS test the
test patch adds or edits reaches it. The fuzz auditor is told the same, in the same words. An
`axiom` correspondence carries the assumption with it, so it is worth what the two axiom gates
find that assumption to be worth.

Three checks of the bundle's programs are the equivalence auditor's, since no gate makes them.
`conformance.py` compares the implementation against the real patched repository function,
and its repository side is trusted code: a disagreement between that side and the
implementation fails `impl.conformance`, and nothing mechanically checks that it is the
repository's code. So for each function the golden patch changes that the specification
models, the repository side of `conformance.py` must call the repository's code -- the
function, or the repository's code that runs it -- and a copy of that code written into
`conformance.py`, or a comparison that would agree with the code before the fix on what the
fix changes, is a finding, quoted, with the verdict `unsound`. The auditor is shown the note
`impl.conformance` records when `conformance.py` agrees with the code before the fix as well
(`undiscriminating`). Where `conformance.py` compares a Python port of the implementation
(`transliterated`: a Lean or Velvet implementation, or one using the checker's own values),
the auditor checks the port line by line against the implementation, a line that does not do
what its line does being a finding. And a repair may change `conformance.py` and
`axioms.py`, which the gates run again: the auditor is shown what changed in them since the
last round, and asked whether a change makes a program compare less than the specification
needs -- fewer inputs or narrower ones, a weaker comparison, a function newly skipped --
which is a finding.

### `audit.no_disclosure`

Could a solver recover an implementation by reading the specification? `spec.no_leakage`
asks the textual version of this question and catches a specification that copies the
golden patch; this one, the adversarial half of the paper's leakage gate, catches the
specification that gives away the implementation without quoting it: a chain of
obligations that determines a result step by step, say.

The reviewer reads a solver's view: the specification with the implementation and the proof
elided, the task statement, and the code as it stood before the fix. That last is what a
solver already has in front of it, so what it already contains -- a name, a helper, a case
split, a constant, a sequence of steps -- discloses nothing; what can be handed over is what
the fix adds.

A verifier's language often has one way to define a result: a pure function, usually
recursive, that can be run. The reviewer is told that such a helper is the specification
when what it defines is a notion the task uses, and that a helper the proof needs is not
disclosure either. What is disclosure is a helper that builds the result the way a body
would, or that simulates a loop by passing its partial results from step to step. What
the comments around a helper call it does not decide which it is.

A finding names what it points at, as one of five constructs: `loop` (a sequence of steps,
a fold, or a helper passing partial results along), `intermediate` (a structure only one
algorithm would have), `table` (outputs listed for particular inputs), `literal` (the
result as a constant), or `oracle` (the result equated to a term the view itself defines),
and quotes the line of the specification it rests on. That a specification's steps can be
copied into code, or that its proof closes by `rfl`, is not a finding on its own: a
specification that states its result as a function of the input -- a case split naming
the result in each case -- can be copied into code by construction, whether its conditions
are stated over the inputs or over an assumption's value, and whether the split is written
inline or as a helper the result is equated to. A helper that computes its value, a loop, a
fold or a sum, is `oracle` when the result is equated to it. The reviewer's verdict
decides, as in `verified-swebench`, whose leakage panel names the leaking line beside it.
This is stricter than
`verified-swebench`, whose question is only whether the specification leaks the
golden patch beyond the task statement: a specification an implementation can be read
off discloses it here even when nothing in it goes beyond the statement.

Some tasks have no specification that can pass it. Where the golden patch is a one-line
expression, the property that pins its result down is the expression, so specification
and implementation coincide and a solver reading one has the other. That is a fact about
the task rather than a defect in the bundle, and it is why Benchproofer is aimed at
repository-scale work: a specification of a change to a large program can say what the
change has to achieve without containing it.

### `audit.axiom_soundness`

The adversarial half of the paper's axiom-soundness gate: the argument behind
`spec.axioms_grounded`, and it stands to that gate exactly as `audit.spec_completeness`
stands to `spec.strength.battery`: the bundle's own evidence first, then someone else's
attempt to break it. The reviewer is asked for fuzzers, one program per unchanged callee,
written to look for an input on which the real callee does something the model does not;
a definition under a `benchproofer:models` line is attacked as an assumption is.
Each is re-run in the benchmark's environment and read through the same protocol, so a
refutation is a disagreement that was observed rather than a claim in a review.

An assumption no fuzzer attacked leaves the gate undecided rather than passing: the floor
is not the argument. A fuzzer that fails without naming a disagreement is set aside with
its reason instead of counted toward the gate's result, because a reviewer's program
crashing on its own bug is not a callee behaving otherwise, and treating it as one would
make a finding out of the reviewer's defect. A fuzzer may leave its callee implicit only
when the specification assumes exactly one thing, where there is nothing else it could be
about. A refuting verdict quotes the first few `refuted` lines of each fuzzer as
`witnesses`, so that one fuzzer's many lines do not hide another's finding, and
`evidence/fuzz-refuted.txt` holds every one, each under the fuzzer that printed it.

The paper's axiom-soundness gate also confirms that each axiomatized function is genuinely
unchanged. Here that half is the equivalence gate's (`audit.equivalence`): an assumption
about a function the golden patch changes takes the fixed behaviour as given, so the proof
assumes the fix, and a fuzzer run against the fixed code agrees with it. The equivalence
auditor reads the golden patch operation by operation and rules an `axiom` row for such a
callee `changed`, by what the callee does rather than by whether the patch touches its text;
this gate keeps the other half, that an assumption states only what the callee really does.

What the fuzzer may pass the callee is bounded by the inputs the specification's
precondition admits, reaching the callee the way the call site derives its arguments, and the
reviewer is told so: a value built to defeat the precondition breaks a language contract
([Audited gates](#audited-gates)). Each input is of the type the call site declares, by its
annotation, its docstring or the interface the statement gives; an input of another type is
used only where a call site in the repository, or a FAIL_TO_PASS test or a PASS_TO_PASS test
the test patch adds or edits, passes one, and `bool` and `float` are not `int` for this. The
interpreter's own limits are not inputs either: the limit on the digits of an int converted
to a str, the recursion depth, memory running out, an int too large for a float. What still
refutes an assumption is a raise the real callee makes on an admitted input of the declared
type where the assumption says it returns, as `verified-swebench`'s guide says of an
assumption that a callee always returns normally. A call that does not return at all, running
without end or longer than any of the benchmark's tests waits, refutes nothing where the
changed function then does not return either: that input is outside the model's domain, which
admits only inputs on which the changed function returns normally.

The fuzzer is also told to call the callee as the task's code calls it, holding fixed
everything that call site fixes, the other arguments the call passes among them, and to run
every call in the one environment `audit.equivalence` describes, starting no thread and no
second process and leaving the recursion limit as it is, and to set state the benchmark's
tests set between calls the way the tests do, since it is an input of the call. A disagreement
found with other arguments, from another thread or process, with the world changed between
the calls, in a state of the environment the tests never build, or only through what earlier
calls left behind, is about a program the task never runs.

### Judgments expire

Every judgment records what it was reached from. When one of those changes, the gate
reports the judgment as undecided rather than applying it, because a stale judgment is not
a weaker judgment, it is a judgment about a different bundle. A repair therefore costs a
fresh review of what it changed, and `benchproofer audit` re-reviews exactly those bundles.
The fresh review of a question is shown what the last one found, each finding with the
repair's entry for it. The repair may decline a finding, its report's entry for it saying
`not a defect` with its evidence; the review judges that evidence, withdrawing the finding if
it holds and keeping it, with why it does not hold, if not. A finding the repair neither
resolved nor declined stays open. The attack auditor, once a repair changed the specification,
writes again each attack the gates ruled a weakness unless the repair's entry for the finding
that names it shows it was no defect; the faithfulness and equivalence auditors are shown each of
their findings with the repair's entry; the fuzz and disclosure auditors read none.

What a judgment reads is finer than a file where the solution is concerned
(`core/readings.py`). Disclosure reads the specification a solver sees, the spec view,
comments included, since a comment can give the fix away. Faithfulness reads the same view
with its comments masked (a Lean docstring is a comment), the pre-fix implementations under
`twins/`, since the auditor says what each returns on the input a test builds, and the type
bridge in `correspondence.md` and `conformance.py`, since whether a clause states what a test
checks can rest on how the bridge reads the repository's values. Equivalence reads the masked
view and the implementation, comments and layout aside, along with `correspondence.md`, the
golden patch, and `conformance.py` and `axioms.py`, whose port and whose changes since the last
round it checks (`audit.equivalence`). So a repair that rewrites a proof leaves every judgment
current, one that rewrites only a comment in the specification expires only disclosure, one
that rewrites only the implementation or only `axioms.py` expires only equivalence, and one
that rewrites only `conformance.py` expires faithfulness and equivalence.

A gate that could not measure does not overwrite one that did. When a gate crashes, runs
out of time, or finds its toolchain or oracle missing, and `manifest.json` holds a pass or
a failure the same gate code reached from the same inputs, that verdict stands, and the
attempt is recorded under `remeasured` in its details.

The same applies to submissions: one aimed at a specification the bundle no longer ships
shows nothing about the one it does, so the two strength gates set it aside.

## Where a verdict goes

`run` and `repair` send each verdict of a required gate that does not pass one of four ways,
read off one table (`benchproofer.pipeline.route`) by its status, its skip reason, and the
one detail beside them that changes where it goes:

| status | skip reason | detail, or gate | goes to |
| --- | --- | --- | --- |
| `fail`, `error`, `timeout` | | | the repair |
| `skip` | `inconclusive` | | the repair |
| `skip` | `inconclusive` | `required`, `stale` | its auditor, asked again |
| `skip` | `inconclusive` | `unruled` | the attack validation auditor, asked (again) |
| `skip` | `toolchain_absent`, `oracle_unavailable` | | holding the review |
| `error` | | `traceback` | nowhere |
| `skip` | `artifact_absent` | | nowhere |
| any but a missing toolchain or oracle | | `oracle.reference_resolves` | nowhere |

The repair addresses a finding, an undecided verdict a repair can address, and an error or a
timeout of the checker or a program on one of the bundle's own files, since what stopped it
is in the file and a repair can say it another way. A file of the bundle a gate needs and
does not find is a failure of that gate, and goes to the repair, since nothing else writes it
once the first draft is written. A missing toolchain or oracle holds the
review back, since the review needs it too, and no repair addresses it. A gate's own crash,
which `Gate.run` records with its traceback, a bundle or a review that is not there to read,
and a check of the task itself go nowhere, and do not hold the review back: holding it for them
would end the task with its budget unspent. Once `oracle.reference_resolves` fails, the task
is dropped and none of its verdicts goes anywhere. A verdict the table has no row for, such
as a failure carrying a traceback, is a defect of the gate that recorded it, and raises.

An auditor is asked again, before any repair, about the unchanged bundle when it showed
too little: `audit.spec_completeness` or `audit.spec_soundness` decided fewer attacks or
controls than the run asks for (`required`), or a judgment is stale (`stale`); and the attack
validation auditor is asked when `audit.spec_completeness` or `audit.spec_soundness` lists
attacks or controls that cannot be determined by execution and that it has not ruled on
(`unruled`). A repair would be told to correct what nothing showed wrong. The auditor that fell
short is asked, and the attack validation auditor is shown the attacks and controls its gates
list. Each question, the gate with the attacks or controls it lists, is asked once per state of
the bundle: asked the same question of the same files, the auditor would fall short the same
way, round after round. The attack validation auditor is first asked within the review that
filed what it rules on, and so is asked once more at most; an attack or a control it still
leaves without a ruling is discarded by its gate. One listed after the auditor last reported
makes it a new question, and so does a repair that changes the bundle. Asking again spends none
of `max_repairs`, so an auditor is asked even when the budget is spent, and the round that asks
it runs only the gates that read the review, with `impl.conformance` where the review filed a
defect's input. A finding beside the shortfall waits for the review asked again, so the repair
that follows addresses both; with nothing beside it, an auditor that fell short again ends the
task.

## Waivers

A failure can be accepted, on the record:

```bash
benchproofer check my-suite --waive spec.no_leakage
```

The verdict is stored as `waived` rather than as `pass`, with the gate's own finding
still attached, so a reader can see both what was found and that someone accepted it. A
waiver is never implicit and never retroactive: it applies to the run that passed the
flag.

## Writing a gate

See [Add a gate](guides/add-a-gate.md). The one rule that matters more than the rest:
report absence as absence. `self.undecided(...)` for a check that could not run,
`self.errored(...)` for a crash in your own code, and `self.failed(...)` only when you
have evidence that the bundle is wrong.
