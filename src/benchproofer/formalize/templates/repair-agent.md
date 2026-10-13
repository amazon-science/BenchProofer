# Repair the formalization of $task

This brief is also in `$brief` in your workspace. Read it there again whenever you are not sure
what it asks, and after a long stretch of work: your report is judged by the rules in it.

${refused}These gates did not pass. Each numbered line is one finding. A gate keeps its number,
its place in the order the gates run, so the numbers need not follow one another. Where a gate
lists findings of its own beneath its line, they are numbered after it, `(12.1)`, `(12.2)`, in
the order its reviewer numbered them, so a finding that mentions "finding 2" means `(12.2)`;
that gate's own line is their summary, resolved through them.$first

$failing

${history}## What you have

Everything is under `$workspace`, and the paths below are relative to it:

* `$bundle/` is the bundle as it stands. `$solution` is the file you repair. `manifest.json`
  holds the verdicts the last round reached (`verdicts`) and the repair record
  (`provenance.repairs`), one entry per earlier repair, and `evidence/` what each of those
  gates ran and printed. `./check`, below, writes its own verdicts and evidence into a copy
  of the bundle and prints where; read a fresh result there, not here.$audit $beside
  `notes.md` is the drafting log.
* `$task_file` is the task: its statement and the golden patch.
* `$rounds/` holds each round of this run, oldest first, one directory each: the bundle as
  that round judged it, with the verdicts it reached in `manifest.json` and their
  evidence, and `round.md`, which says what produced that bundle and lists every finding of
  each gate that did not pass, numbered as above.
* `$repository/` is the repository at the task's base commit, a copy of your own. ${tests_state}**The
  real function is the ground truth.** Read it at the base commit, then read the golden patch
  in `$task_file`: together they are what the specification must agree with.
$review* `$scratch/` is yours: put every file of your own there.

$tests

Do not read the source of Benchproofer, which judges this bundle, or its prompts: they
cannot tell you what is true of the real function. Everything you need is listed above.
Nothing from another run or another tool belongs in this repair.

## Reproduce the finding first

Read each failed verdict and the evidence behind it before anything else: they are the
specification of your work. Do not edit anything until you can name a concrete input,
implementation or finding on which the specification and the real function part ways. To
see what the real function does on an input, write a program in `$scratch/` that calls it and
prints what it returns or raises, and run it with `./tools run`, where the benchmark's tests
run, with the golden patch applied.

## Find the weakness, not one example

The input or wrong implementation a finding shows you is one witness of a weakness. The next
review writes attacks of its own against the specification you leave, and a repair that
closes only the witness it was shown is refuted by the next one the same weakness admits. Before
writing an obligation, work out why the specification could not tell the witness from the
real function:

1. **List what the specification observes**: every value its postconditions constrain, and
   every value it mentions only in a precondition or not at all. A wrong implementation the
   specification accepts differs from the real function only in the second list.
2. **Find what the golden patch changes among them.** What does it change in what the
   function returns, raises or modifies, and is that change visible at all in the first
   list?
3. **If it is not, the model is the defect, and no postcondition can fix it.** Three shapes
   recur. A helper the specification leaves unconstrained -- a free boolean the
   implementation may choose, a flag nothing pins -- lets the witness pick the value that
   makes any obligation about it vacuous. A helper whose only postcondition makes it the
   identity, its result equal to its argument, hides the change: the witness can differ
   from the real function on exactly what the fix changes and still satisfy every
   obligation. In either case give that helper the property its counterpart in the
   repository has, so the change becomes visible, and only then state the obligation that
   pins it. A parameter that holds what an unchanged callee computes is addressed as the
   rule for callees the fix does not change, in the system prompt, says.
4. **Then ask what else the same weakness admits.** If your obligation is the only thing
   between the specification and a second wrong implementation of the same shape, you have
   shut out one wrong implementation the weakness admits, not the weakness.
$earlier
${inputs_rules}## Run the gates yourself

$tools_rules

Judge the bundle with every gate a program decides, as the next round will, like this:

```bash
$check
```

That costs minutes: it puts each mutant and each case of the property-based test suite to
the checker and runs `conformance.py` and `axioms.py` where the benchmark's tests run, and
the conformance gate runs `conformance.py` twice when the first run passes: once against the
tree with the golden patch applied, and again against the base commit, to see that it tells
the fixed code from the code before the fix. Give a run of `./check` room for both. Run it
before you report. For one gate, give the script that gate's `--only` alone (`--only
spec.verifies` is the checker on `$solution`), as often as you like.

The checker $checked. A file it cannot finish in its time is not a repair: simplify the
model, don't pile on annotations. Put a file of your own to it with `./tools verify`. For an
attack you address, write its implementation regions into a copy of the solution you leave, in
`$scratch/`, and put that copy to `./tools try` as an attack, with its equivalent patch where
it has one: the checker should now reject it.

What `./check` judges is a copy laid out as Benchproofer lays out the bundle you leave: the
pre-fix implementations and the cases of the property-based test suite you left, spliced into
the specification you left, and the regions and digests recorded again. So it asks what the
gates will ask of your work afterwards, and not whether an edit has been spliced into every
case yet. `conformance.py` and `axioms.py` it judges as you leave them, as the gates will. A
case of the property-based test suite whose rationale you rewrite in its `index.toml` keeps
the rationale you wrote; one whose file you rewrite and whose rationale you leave is recorded
as rewritten, since the old rationale was about the old file.

## Whether it fails a FAIL_TO_PASS or a PASS_TO_PASS test

An implementation the specification accepts that the benchmark's tests reject is one of two
findings, and they need opposite repairs. The verdict says which you have, because it names
the two test sets apart:

* **It fails a FAIL_TO_PASS test.** It does not fix the reported bug, and the
  specification does not force the fix: find the value the fix changes and state it.
* **It passes every FAIL_TO_PASS test and fails a PASS_TO_PASS test.** It fixes the bug
  and breaks something that used to work. The fix is already stated, so stating it more
  strongly changes nothing: the implementation still satisfies it, and the repair attempt is
  spent. What the specification is missing is the behavior the patch destroyed, a property
  the function had before the fix and still has after it. The named test is the pointer:
  read it, see which property of the function it asserts, and state that as an obligation.
  It is usually a preservation claim -- an ordering, a key that must survive, a field left
  alone, an input that must still raise -- rather than anything about the bug.

If it fails both, the specification is missing both, and stating only one leaves it
accepted.

## A mutant the checker accepts

The mutation check (`spec.strength.mutation`) changes one token of the implementation at a
time and puts each mutant to the checker; `evidence/mutation.txt` has each one whole. A mutant
the checker accepts asks one of two things. If it computes something else on an input the
specification admits, the specification is too weak there: state the property the mutant
breaks. If it computes the same as the implementation on every admitted input, no
specification can reject it, and the check sets it aside once it has run the two on the same
drawn inputs and seen them agree. It cannot run them where a file assumes a callee in its
`axioms` region, or is in a language that does not run here: then write the line the mutant
changes so that a change to that token alters the result.

## A finding about a case of the property-based test suite or the pre-fix implementation

Not every finding is about the specification. A verdict of property-based falsification
(`spec.strength.battery`) or of discrimination (`spec.discriminates`) can find a case of the
property-based test suite, or the pre-fix implementation, defective as a case: one the
checker could not read, one that does not keep the shipped specification, one that uses a
construct the solution file does not (`sorry`, an axiom, a directive) or repeats another of
the bundle's files, a correct case refused on a step of its own proof, one the checker
reached no verdict on, or a rejected case for which no refutation witness shows that the
specification, rather than the case's own proof, is what rejects it. What the checker said of
such a case is not evidence about the specification, so a finding about a case is resolved by
fixing the case, never the specification. If a case seems to prove the specification wrong,
that is a finding to report, not a licence to change it.

A correct case of the property-based test suite that the checker refused is almost always a gap
in its own proof, not in the specification: read the checker's output and fix the case, and if
you find no proof inside its own regions that uses only what the solution file uses, say
exactly what you tried. The known classes:

$classes

An admissibility case of the property-based test suite keeps the solution file's implementation
line for line, with only its probe statements added, and the gate refuses one whose
implementation differs; and it keeps its inputs: they are the question. Moving them to inputs
the precondition obviously admits decides a question nobody asked.
$witness
## What you may change

Every file the author wrote, and you keep them in step with each other. What you leave is
what the gates judge, spliced into your specification as it stands, and nothing is drafted
after you finish: a file the bundle needs that you leave missing fails its gate.$lacking

* `$bundle/$solution`: the specification, the implementation, the helpers, the axioms.
  The implementation must still be proved correct under the repaired specification.
* `twins/` and `rivals/` (with `rivals/index.toml`$twins_index): the pre-fix implementation and
  the property-based test suite. They are spliced into your specification afterwards, so write
  only their own regions. A case of the property-based test suite may be rewritten; it may be
  removed only if the verdict of property-based falsification (`spec.strength.battery`) found
  it defective as a case, and that gate fails a suite missing any other case it last judged.
  The pre-fix implementation may be rewritten but not removed: discrimination
  (`spec.discriminates`) fails a bundle that has none.
* `correspondence.md`: keep it describing the implementation you leave.
* `conformance.py` and `axioms.py`: keep them in step with what you change, and correct them
  where one is wrong. Their gates run what you leave, `conformance.py` on every input on
  record as well as on its own draws, and the next review is shown what you changed in them.
  $kept
* Nothing else: not `audit/`, `evidence/` or `manifest.json`, which the review and the gates
  write, and nothing in the task or the repository. Write nothing into the checker's own
  project directory and delete nothing from it; other sessions are working in it at the same
  time as you.

${artifacts}## What you may not do

No change that silences a check without fixing the defect, as the system prompt describes,
and nothing that gives away the implementation. Besides:

* Do not weaken an obligation to make a finding go away, and do not remove one no finding
  objected to.
* Do not narrow what the specification admits: no precondition, `Outside the bridge` entry or
  change to `conformance.py` that shuts out inputs it admitted before, whatever the reason,
  the repository raising on them included, and whatever the drafting guidance allows a first
  draft. Where the repository raises, state that it raises, or what it does; where it
  returns, state what it returns. An entry of one of the three kinds below is not a
  narrowing, and neither is `conformance.py` skipping, with a line naming the entry, the
  inputs an entry of the third kind names.
  Nor is a change that widens the domain -- an input case added, a precondition dropped, a
  parameter type that admits every value it admitted and more: it shuts out nothing, and it is
  how a finding that the domain leaves out inputs the benchmark's tests hand a function the fix
  changes is resolved. Report every input you exclude: a narrowing shrinks the claim instead of
  correcting it. The conformance gate hands `conformance.py` every input on record and fails a
  bundle whose program declares one a run drew inadmissible without naming an `Outside the
  bridge` entry, and the next review holds every precondition and entry a repair added to the
  domain rule of the system prompt.
* Run no git command that writes.

$outside_rules

## Report

You have $budget, and no more: at that point the session is stopped wherever it is. Spend it
roughly so -- read the failed verdicts, their evidence and the real function, then diagnose,
then edit, then run the checker -- and if you have not run the checker by the time half of it
is gone you are on the path that runs out of time. What a session that stops without a
report left is kept as it left it, and the gates judge it as they judge any repair. Out of time
with the repair unfinished, report `BLOCKED` and say what you did not reach, which is the
honest and more useful outcome.

Call the submit tool once:

* the status: `REPAIRED` when you changed the bundle to resolve the findings, `NO-REPAIR-NEEDED`
  when you changed nothing because no finding is a defect, or `BLOCKED`. A finding you cannot
  close does not excuse the others: `BLOCKED` is for the findings left after you resolved
  every one you could;
* two sentences saying what you changed and why;
* one entry for each numbered finding above, with its outcome. `resolved`: your change
  resolves it; give the counterexample it addresses (an input, a wrong implementation, or the
  line the finding quotes) and what the real function does on it, citing file and line.
  `not a defect`: you established that it is none and changed nothing for it; give the
  evidence, an input and what the real function does on it, or the line of the task or the
  specification that shows it, citing file and line. `not reached`: you did not get to it or
  could not close it; say what you established about it. The next repair is shown the ones
  you did not reach first;
* each input you excluded that the specification admitted before, with where: a
  precondition, an `Outside the bridge` entry, `conformance.py`;
* the last lines the checker printed on your solution file, from `./tools verify` or
  `./check --only spec.verifies`.

The next review is shown each entry's text, and for a finding you found no defect that text
is all the evidence it has: it withdraws the finding only if the evidence holds. Each auditor
reads them so:

* the attack auditor, once you change the specification, writes again each attack the gates
  ruled a weakness, unless your entry for the finding that names the attack shows it was no
  defect;
* the faithfulness and equivalence auditors are shown each of their own findings with your
  entry for it;
* the fuzz auditor reads none of them: it keeps a fuzzer while the `axioms` region the fuzzer
  was written against stands, and writes a new one once you change that region;
* the disclosure auditor reads none of them.
