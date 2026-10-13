# CLI reference

One command per pipeline stage, plus three that only report. Every command accepts
`--help`, and every command that prints a table accepts `--json` to print the same
values as a document.

```
benchproofer catalog     what this installation has
benchproofer doctor      and what it can actually run
benchproofer ingest      upstream rows -> frozen tasks
benchproofer formalize   frozen tasks -> bundles
benchproofer audit       bundles -> an independent review of each
benchproofer repair      findings -> bundles edited to address them
benchproofer check       bundles -> verdicts
benchproofer run         the whole loop, in one command
benchproofer report      verdicts -> what holds up
benchproofer smoke       prove the installation works
```

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the command did what it was asked |
| 1 | Benchproofer could not do its job: bad settings, missing plugin, broken bundle |
| 2 | the command line was wrong |
| 3 | Benchproofer worked, and the result did not meet the bar `--strict` set |

A bundle the gates reject is a result, not a failure, and so is a task whose drafting
gave up without producing an artifact: `benchproofer check` over a corpus of rejected
bundles exits 0, because Benchproofer did exactly what it was asked. Add `--strict` when you
want the process to fail on anything short of certification, which is what separates
"benchproofer broke" from "the specifications did not hold up" in continuous
integration.

## Shared options

| option | applies to | meaning |
| --- | --- | --- |
| `--bundle-root DIR` | every stage | where bundles are read and written; default `bundles/` |
| `--cache-dir DIR` | ingest, formalize, run, smoke | where datasets and checkouts are cached |
| `--offline` | ingest, formalize, check, run, smoke | refuse network access; use only cached inputs |
| `--json` | all | print a document instead of a table |
| `--limit N`, `-n` | ingest, formalize, check, run | take the first N tasks |
| `--id TASK_ID` | ingest, formalize, check, run | select one task id; repeatable |
| `--backend NAME`, `-b` | formalize, audit, repair, check, run, report | which formalization to work on |
| `--level static\|oracle\|audited` | repair, check, run, report | how much evidence to require |
| `--concurrency N`, `-j` | formalize, audit, repair, check, run | tasks worked on at once |
| `--provider NAME`, `--model ID` | formalize, audit, run; `--model` also repair | which language model drafts |
| `--record` | formalize, audit, repair, run | write a cassette per language-model exchange, holding the request and the reply, and each agent session's request (system prompt, prompt, tools, budget) under `<cassette dir>/sessions/` |
| `--verbose`, `-v` | all | show progress; repeat for debug |
| `--quiet`, `-q` | all | errors only |
| `--version` | Benchproofer itself | print the version and exit |

`--verbose` and `--quiet` go before the subcommand: `benchproofer -v check my-suite`.
`benchproofer --version` names no subcommand; the version it prints is the one stamped into
every verdict, so a `manifest.json` can be matched to the Benchproofer version that wrote
it.

## `catalog`

```bash
benchproofer catalog                # every registry
benchproofer catalog backends       # one of them
benchproofer catalog gates --json
```

Takes `all`, `benchmarks`, `backends`, `oracles`, `gates`, `providers`, or `sessions`. This
is a listing of what is registered, not of what works; `doctor` is the one that probes.

## `doctor`

```bash
benchproofer doctor
benchproofer doctor --json
benchproofer doctor --provider anthropic --model claude-opus-5
benchproofer doctor --strict        # exit non-zero unless a backend and the provider are ready
```

Prints the Benchproofer version and judge digest, the resolved settings with every path made
absolute, and one row per backend, oracle, and model provider saying whether it can run
here. A component that cannot prints the command that would fix it.

`--provider` and `--model` report on the run you are about to make rather than on the
configured default. This matters because a provider's credential can follow from the
model id: `claude-opus-5` needs `ANTHROPIC_API_KEY`, while `us.anthropic.claude-opus-5`
names a Bedrock profile and needs `AWS_REGION` instead.

Run this first on a new machine, and again after installing a toolchain.

## `ingest`

```bash
benchproofer ingest humaneval --limit 20
benchproofer ingest jsonl --extra source=examples/tasks.jsonl --extra name=demo
benchproofer ingest swebench-verified --id astropy__astropy-12907
```

| option | meaning |
| --- | --- |
| `--extra KEY=VALUE` | adapter-specific option; repeatable |
| `--refresh` | overwrite inputs that are already frozen, even where bundles exist |

Writes `task.json` and, when the golden patch is given as a diff, `reference.patch`. Frozen
inputs are never rewritten without `--refresh`, so re-running this command cannot change
the task an existing bundle was judged against.

## `formalize`

```bash
benchproofer formalize my-suite --backend dafny --provider anthropic
```

| option | meaning |
| --- | --- |
| `--provider NAME` | model provider for the drafting stage |
| `--model ID` | provider-specific model identifier |
| `--record` | write a cassette for every language-model exchange, holding the request and the reply, and each agent session's request under `<cassette dir>/sessions/`, named by the session id Claude Code keeps its transcript under |
| `--rebuild` | draft again even where a solution file already exists |

Reads the tasks `ingest` froze, so it needs no network for a benchmark whose adapter
does. Without `--rebuild`, a task that already has a solution file is left alone, which
is what makes an interrupted run resumable.

The solution -- the specification and the implementation -- is drafted by an agent session
(`session`; one that reaches a model does not run under `--offline`),
as `verified-swebench`'s author drafts it. It works in a workspace laid out as a repair
session's is: a new bundle holding the task, whose solution file holds the backend's
template, a copy of the repository at the base commit with the benchmark's test patch
applied, or the files the benchmark's tests run with written in, so each test reads as the benchmark
runs it, the files the golden patch touches as they read after it (`fixed/`), the `tools` script a
review auditor has, and `scratch/` for its own files. It is told what to read before it writes
-- the statement, the golden patch, every FAIL_TO_PASS test and every PASS_TO_PASS test the
test patch adds or edits in full, the PASS_TO_PASS tests that call a function the fix
changes, and the callees the changed code calls -- and runs the checker until it accepts the
file or the budget, `draft_turns` turns and `draft_timeout_s` seconds, ends; its tools and
limits are those of every [agent session](#agent-sessions). Only the solution file and the
session's report are read back; the pre-fix implementation, the property-based test suite,
`correspondence.md`, `conformance.py` and `axioms.py` are drafted against the file by
requests once the checker accepts it, and the `Not modeled` and `Outside the bridge` sections
of `correspondence.md` start from what the report says the specification leaves out. A file
the checker refuses goes to the proof session below; one it still refuses has nothing drafted
beside it, and goes to repair, which writes those files. A session that fails after it wrote
the file has drafted it; one that left the template ends the task. Without a session nothing is drafted:
the task is reported as an error saying what to install, and the command exits 1. `--record`
writes the session's request under `<cassette dir>/sessions/`, and the manifest records it
under `provenance.formalization.session`, as a repair session is recorded.

A task whose drafting gave up is listed as unfinished and the command still exits 0: the
bundle is incomplete, which is a result. A task that could not be attempted at all, with
no agent session or no provider configured say, is Benchproofer failing, and exits 1.

Under a backend whose files contain their proofs (Lean, Velvet, Nagini), a file the checker
rejected is handed to an agent session when one is available and `prove_agent` is on, as
`verified-swebench`'s proof agent writes proofs. The session gets a copy of the bundle and
the `tools` script a review auditor has, and may edit the `proof` region where the file has
one, plus the proof annotations a backend keeps inside `impl` (under Velvet, `invariant`,
`decreasing` and `done_with`; under Nagini, `Invariant`, `Assert`, `Fold` and `Unfold`). Its
request says what the file claims, and so what reporting `fail` means: the file's own
claim, which is false where the implementation does not meet the specification; an
admissibility probe's claims, false where the specification does not admit the input; or a
refutation witness, false where the implementation meets the specification at its input.
Its system prompt says how proofs are written under its checker: tactics under Lean and
Velvet, proof annotations under Nagini. Its budget is `prove_turns` turns and
`prove_timeout_s` seconds, and its tools and limits are those of every
[agent session](#agent-sessions). What it wrote replaces the file only when the
specification and implementation are the ones it was given, it uses none of the backend's
banned tokens, the checker accepts it, and the proof is closed; otherwise the file is kept
as it was, and the drafting log (`notes.md`) says why.

Three stages consult a language model (this one, `audit`, and `repair`), and no gate ever
does, so a corpus can be re-judged by anyone with no credential at all.

## `audit`

```bash
benchproofer audit my-suite --backend falsifier --audit-model claude-sonnet-5
benchproofer audit my-suite --id coin-change --again
```

| option | meaning |
| --- | --- |
| `--audit-model ID` | the language model that reviews; use a different one from `--model` |
| `--again` | ask every auditor even where a current review exists, adding to what is on record |

Asks an independent reviewer to attack each bundle: wrong implementations the
specification might accept, correct ones it might rule out, and a judgment on each of the
three questions no program can decide. The review is written into `audit/` and judged by
the seven `audit.*` gates; nothing here decides anything, because every submission is re-run
and every judgment is reported only while it is current. See
[Audited gates](gates.md#audited-gates).

A review is made of auditors, each asked on its own:
- `attack`, for the wrong and the correct implementations;
- `fuzz`, for one program per callee the specification assumes;
- one auditor for each judged question: `faithfulness`, `equivalence` and `disclosure`;
- `validation`, the attack validation auditor, for a ruling on each attack and control that
  cannot be determined by execution.

Only the auditors whose last reply no longer describes the bundle are asked. `attack` is
asked when the specification changed; `fuzz` when an unchanged callee has no fuzzer written
against the assumption as it now stands; the auditor of a judged question when its judgment
is missing or stale; `validation` when the last verdicts of `audit.spec_completeness` and
`audit.spec_soundness` list attacks or controls that cannot be determined by execution and that
it has not ruled on, and `attack` is not due. It rules on what the gates made of submissions
they have run, so `audit` asks it last, as `run` does (see [`run`](#run)): after the other
auditors, `audit.spec_completeness` and `audit.spec_soundness` judge what is on record, and it
is asked where they list an attack or a control it has not ruled on, those of the submissions
filed in the same call included. A bundle whose review still describes it is left alone, so
running this twice does not spend a budget twice. `--again` asks every auditor, the attack
validation auditor last in the same way. While the specification `attack` last read stands,
what it files is added to what is on record; once a repair changed that specification, what it
files replaces the earlier submissions, which are not re-run, and it is shown each earlier
attack with what the gates ruled and the repair's entry for it, to write the weaknesses again
first.

Each auditor is an agent session (`session`) on the reviewing language model, as
`verified-swebench` reviews. Without a session nothing is reviewed: each bundle is reported
as an error saying what to install, and the command exits 1. Each session gets a workspace
of its own:
- a copy of the bundle;
- a copy of the repository at the task's base commit, and the benchmark's tests under
  `tests/`: the test patch, which the repository copy does not have applied, and any file the
  benchmark runs its tests with;
- a `tools` script. It runs the bundle's checker (`verify`), the gate a submission is judged
  by (`try --as attack|control`), the gate a fuzzer is judged by (`fuzz`), and a program
  where the benchmark's tests run, with the golden patch applied (`run`).

The disclosure auditor reads blind: its workspace holds the specification a solver is shown
and the task statement, and nothing else. The attack validation auditor's copy of the bundle
keeps the review and what the gates made of it, and its workspace holds the statement as
`statement.md`; its prompt lists each attack or control it rules on with its files and what the
gates established, beside the faithfulness auditor's coverage table when one is current. Each
session, the attack validation auditor's included, has a budget of `review_turns` turns and
`review_timeout_s` seconds and the tools and limits of every [agent session](#agent-sessions).
One that stops without submitting is taken up once more and asked for its review, as a drafting
session is asked for its report: a verdict it did not finish checking is `uncertain`, unless
what it ran already shows a defect. The attack and fuzz auditors submit the files they wrote; a
judged auditor submits its verdict and its findings, and what it checked and found clean apart
from them (`checked`), which is recorded with the judgment and is not handed to a repair. The
attack validation auditor submits one ruling per attack or control it is shown, each naming the
input and the sentence of the statement, the test or the obligation it rests on; it is recorded
with the digests of the specification, the implementation, the submission's files and what its
witness test cites, and counts while they still match (see
[`audit.spec_completeness`](gates.md#auditspec_completeness)). The attack auditor also names
each defect it showed by running code that no attack of its shows (`defects`): the function
`conformance.py` compares and the input as a Python tuple literal. One without both is not
filed; one filed stays on record while the specification it attacked stands, and its input is
handed to every run of `conformance.py` (`evidence/conformance-witnesses.json`), so `run`
judges `impl.conformance` again after the review that filed it. Each file is read back and
filed only when:
- it contains the shipped specification;
- it is not a repeat;
- it is inside the session's workspace.

An auditor whose last judgment found fault is shown what it found, each
finding with the repair's entry for it. Where the repair declined a finding with evidence,
the auditor withdraws the finding if the evidence holds and keeps it, saying why, if not; a
finding the repair neither resolved nor declined stays open until the specification
addresses it.
The faithfulness auditor is also shown what the review found in the rounds `run` has kept of
the bundle, the first sentence of each finding, and a finding of its own that asks for what
one of those called too strict, or the reverse, says so and decides which is right against
the fixed code and the tests.

Without `--audit-model` the review is written by the drafting language model, which
`audit.independence` reports as a self-review rather than as an independent one.

## `repair`

```bash
benchproofer repair my-suite --level audited
benchproofer repair my-suite --level oracle --id coin-change
```

Reads each bundle's recorded verdicts and repairs it to address what they found. The level
decides which gates are checked, so pass the level the bundles were judged at.

The review on record is left as it was. A repair that changes the specification makes the
attack auditor due again, and the next review attacks the repaired specification afresh,
writing again first each earlier attack the gates ruled a weakness, so a repair cannot address
one finding by moving the weakness. A judgment expires when what it read
changed -- the specification a solver sees, for disclosure; that view with its comments
masked, the pre-fix implementations under `twins/`, and the type bridge in
`correspondence.md` and `conformance.py`, for faithfulness; the masked view, the
implementation, `correspondence.md`, `conformance.py` and `axioms.py`, for equivalence --
which is what makes the bundle ask to be reviewed again.
A repair that changed only a proof expires none of them. Verdicts are left in
`manifest.json` until the next judgment replaces them, but the evidence of each one whose
recorded inputs the repair changed is removed from `evidence/`, as is evidence no verdict
names, so the review that comes before the next judgment does not read a log of a
`conformance.py`, an `axioms.py` or a solution the repair replaced. The inputs on record
for `conformance.py` (`conformance-witnesses.json`) are kept whatever changed.

The repair is an agent session (`session`), as `verified-swebench` repairs. Without a
session nothing is repaired: the bundle is reported as an error saying what to install. It
gets a workspace of its own:
- its prompt, as `brief.md`, to read again once its context has been compacted;
- a copy of the bundle, laid out so Benchproofer's own `check` runs on it, through a
  `check` script that runs every gate a program decides, at level `oracle` whatever level it
  is given, on a copy laid out as `--as-submitted` lays one out (below);
- every round of this run, each the bundle as that round judged it, with the verdicts it
  reached, and a `round.md` saying what produced it -- drafting, a repair with the gates it
  addressed and its report, or the review asked again -- and listing every finding of each
  gate that did not pass. Its prompt follows the findings it addresses with what each round
  before found and what the repair after that round did, the first sentence of each;
- the task;
- a copy of the repository at the task's base commit, laid out as drafting's is: the
  files the benchmark's tests run with written into it and the benchmark's test patch
  applied, kept beside it as `tests.patch`, so the FAIL_TO_PASS tests and the PASS_TO_PASS tests
  the test patch adds or edits read as the benchmark runs them;
- the files each auditor left in its `scratch/`, under `review/<auditor>/scratch/`, which
  the auditor's findings cite;
- the `tools` script a review auditor has;
- a `scratch/` directory of its own, so that nothing it writes reaches the project directory
  a backend's checker shares with every other session on the machine.

Its prompt gives the rules of each file beside the solution that the bundle lacks or that the
findings are about, by the gate that found them or a finding naming the file: the rules the
request drafting that file is given, from the same rules files (`formalize/templates/*-rules.md`,
`core/templates/conformance-rules.md` and the grounding protocol). It asks for each file the
bundle lacks, and says that Benchproofer does not update the copy of the implementation in
`conformance.py` or the declarations `axioms.py` quotes: where it changes the implementation
or the `axioms` region, it changes them. Each finding of an attack it is briefed with names
the attack's file under `audit/`, its claim and what the gates ruled.

Its tools and limits are those of every [agent session](#agent-sessions). Its budget is
`repair_turns` turns and `repair_timeout_s` seconds, which its prompt states: a session told
nothing about its clock spends it waiting to be re-invoked, which nothing does. It edits the
bundle as it stands: every file the author wrote is its to change, and nothing is drafted
after it, so a file it leaves missing fails its gate and the bundle goes to the next repair.
What it wrote is read back into the repaired bundle:
- the solution file;
- the pre-fix implementation and the property-based test suite, spliced into the repaired
  specification, or as it left them where they do not splice into it or their index cannot
  be read, for their gates to judge. What it removed stays removed: `spec.discriminates`
  fails a bundle with no pre-fix implementation, and `spec.strength.battery` one missing a
  case its last verdict judged and did not find defective as a case;
- `correspondence.md`;
- `conformance.py` and `axioms.py`, which their gates run again as it left them,
  `conformance.py` on every input on record as well as on its own draws. The rules of
  `conformance.py` name the functions inputs are on record for, since it is handed them
  under those names.

Nothing it wrote under `audit/` or `evidence/`, or to `manifest.json`, is read back, and
nothing it wrote is put to the checker on the way in: the gates judge it. The repair record
(`provenance.repairs` in `manifest.json`) says which files it edited.

A repair that excludes inputs the specification admitted before -- through a precondition,
an `Outside the bridge` entry or a change to `conformance.py` that stops drawing or comparing
them -- is neither refused nor taken on its report's word: the gates judge what it left.
`impl.conformance` hands `conformance.py` every input on record and fails a bundle whose
program declares one a run drew inadmissible without naming an `Outside the bridge` entry,
and the equivalence auditor holds each precondition and entry a repair added to the domain
rule. An entry of one of the three kinds `Outside the bridge` is for (`audit.equivalence` in
[gates](gates.md) lists them) is not a narrowing.
A `conformance.py` or `axioms.py` the session changed is taken as it left it, whatever
verdict it was addressing: their gates run them again, and the next review is shown what
changed in them. The repair record keeps the report, and the numbered findings the session was
briefed with. A finding is numbered by its gate's place in the order the gates run, and a
finding a gate lists beneath its summary after it (`12.1`, `12.2`, in the order the gate
lists them, an auditor's own findings first), so the brief, the round's `round.md` and the
auditors that read the report's entries number it alike. Its report has an entry for each
finding, with its outcome -- `resolved`, `not a defect` or `not reached` -- and the
counterexample, the evidence or what it established, which the auditors are shown whole;
the brief says which auditor reads which entries. The next
session is briefed with the gates holding the findings it did not reach first: one it found
no defect is the review's to judge. A session whose work
was not taken leaves no round
of its own, since the bundle is not judged again, so the record also keeps what it left of
the specification, `correspondence.md`, `conformance.py` and `axioms.py`, as a diff. The
next session's brief opens with each such session just before it: why its work was not
taken, what its report says and says it excluded, and that diff.

A session that stops without filing a report is taken up once more and asked for one, under
a small budget of its own, since only the report says what it did about each finding. What
one that still files none left is taken as above, and the gates judge it.

A verdict that finds a case of the property-based test suite or the pre-fix implementation
defective as a case goes to the session like every other, which has the checker at hand to
fix it. Its prompt says, as `verified-swebench`'s does, that a finding about a case is
resolved by fixing the case, never the specification, and, under a checker that needs a
refutation witness, that a case it rewrites to be rejected needs its witness again.

A repair addresses the verdicts that go to the repair, as
[Where a verdict goes](gates.md#where-a-verdict-goes) lists them. A bundle with none, such as
one held up only by a missing toolchain or by benchmark tests that cannot run here, is
reported as having nothing to repair. That is not the same as being sound. A bundle holding
a verdict that table has no row for is reported as an error, and the others are repaired.

## `check`

```bash
benchproofer check my-suite
benchproofer check my-suite --level oracle
benchproofer check my-suite --level audited
benchproofer check my-suite --only spec.verifies --only spec.strength.mutation
benchproofer check my-suite --waive spec.no_leakage
benchproofer check my-suite --skip-certified -j 8
```

| option | meaning |
| --- | --- |
| `--only GATE` | run only this gate; repeatable |
| `--waive GATE` | record this gate's failures as waived rather than as failures |
| `--skip-certified` | leave bundles that already certify alone |
| `--rejudge` | judge everything again; the default |
| `--strict` | exit 3 unless every selected bundle is certified |
| `--as-submitted` | judge a copy of each bundle laid out as Benchproofer lays out the bundle a repair leaves |

`--as-submitted` splices the pre-fix implementation and every case of the property-based
test suite into the solution the bundle ships and records the regions and digests again
before judging, which is what Benchproofer does with the bundle a repair leaves. It is for
judging a bundle that is still being edited -- a repair session's own `check` runs this way
-- so that an edit not yet spliced into every case does not read as a specification that
differs from the shipped one.
`conformance.py` and `axioms.py` are judged as they are: the copy of the implementation one
holds and the declarations the other quotes are the editor's to keep in step. A rationale in
a case's index that differs from the one the bundle gave it is kept with its case. The copies go under a sibling of the bundle root and
hold the verdicts; the bundles are left as they are. It prints a line as it starts each gate
and each run of `conformance.py`, and then, for each required gate, its status, its summary
whole and where its evidence is, or that this check did not run it; the review's gates are
listed as ones it does not judge.

`--only` adds to a bundle's verdicts rather than replacing them: the verdicts of gates that
did not run this time are kept, with the stamps they already had. That is how a fixed gate
is re-run over a large corpus without paying for the rest.

Judging writes no artifact and consults no language model, so anyone can re-judge a corpus
they did not build.

## `run`

```bash
benchproofer run humaneval --backend dafny --provider anthropic --limit 20 --report reports/
benchproofer run swebench-verified --backend falsifier --level oracle --limit 5
benchproofer run humaneval --level audited --model claude-opus-5 --audit-model claude-sonnet-5
```

Every stage in one command, with the union of their options plus `--report DIR` to write
`report.json` and `report.md` at the end. One task's failure never stops the others, and no
task is worked on twice. A stage that could not reach a language model or start a session
at all ends that task with an `error`, keeping the bundle as it was last judged: an expired
credential is the environment's fault, and further repair attempts would fail the same way
while reading afterwards as a bundle no repair could help.

At every level this is the whole loop: draft, judge, repair, judge again, until each
bundle certifies or `max_repairs` repair attempts are spent. The solution is a session's,
every other file of a first draft one request once the checker accepts the solution, and
what the checker or a gate objects to, a missing file included, is the repair's to fix. Below `--level audited` each attempt runs every gate at once, and nothing is
reviewed, since nothing below `audited` requires a review.
At `--level audited` each attempt runs the gates a program decides first, and reviews the
bundle, then runs the gates that read the review, only when none of those goes to the
repair or holds the review ([Where a verdict goes](gates.md#where-a-verdict-goes)), as
`verified-swebench` orders its gates: a bundle a gate already rejects is repaired before it
is reviewed, and the repair addresses only what that attempt's gates found. Within the
review, the attack validation auditor is asked last: `audit.spec_completeness` and
`audit.spec_soundness` judge what is on record first, and it is asked only where they list an
attack or a control that cannot be determined by execution and that it has not ruled on. The
gates that read the review then judge those two again with its rulings, reading what their
first run recorded of each submission (`evidence/audit-outcomes.json`) rather than running the
benchmark's tests on it twice, and `impl.conformance` is judged again with them where the
review filed a defect's input. A verdict of a gate that reads the review is reported as `stale`
once a file it recorded reading has changed, rather than as what it said about the bundle
before. An auditor that showed too little is asked again about the unchanged bundle before
anything is repaired, once per state of the bundle, and that spends none of `max_repairs`;
[Where a verdict goes](gates.md#where-a-verdict-goes) says when.

A repair that leaves the bundle worse is not rolled back. The next repair sees every
earlier round of the run: what produced it, what its gates found, and what the repair after
it did. Nothing a repair does is undone, as [`repair`](#repair) describes: its work is not
taken only when the solution file it left cannot be read or it changed nothing a repair may
change. What it removed stays removed. A pre-fix implementation it deleted fails
`spec.discriminates`, and a case of the property-based test suite it deleted that the last
`spec.strength.battery` verdict did not find defective as a case fails that gate; either
failure sends the bundle to the next repair, which writes it back.
Every attempt spends one of `max_repairs`, a session
whose work was not taken or that changed nothing included, such as one that reported
`BLOCKED` without editing, so a task runs at most `max_repairs` repair sessions. After an
attempt that left the bundle as it was, the next one repairs again without judging the
unchanged bundle.

At `--level oracle` and above, each task's golden patch goes through the task's own tests
before anything is drafted for it (`oracle.reference_resolves`, the paper's resolution
check). A task whose golden patch fails them is `dropped`: nothing is drafted, reviewed or
repaired, and the report counts it separately from `rejected`.

## `report`

```bash
benchproofer report
benchproofer report my-suite --level oracle
benchproofer report --out reports/     # report.json and report.md
benchproofer report --rows 50          # list more unfinished bundles
```

Reads each bundle's `manifest.json` and runs nothing: no gate, no verifier, no language
model. Every bundle is classified by the same `classify` the gates' own consumers use, so a
report cannot disagree with `check` about what is certified.

Unfinished bundles are listed with the gates that objected, and undecided verdicts are
counted in their own column rather than folded into a rate. `report.md` and `report.json`
also list, per bundle, each correct case of the property-based test suite whose own proof
the checker rejected (`spec.strength.battery` records them, a proof session's attempt
included), since there the checker, not the specification, fell short.

## `smoke`

```bash
benchproofer smoke                     # the offline suite, 24 cases
benchproofer smoke --list              # suites, groups, and case ids
benchproofer smoke benchmarks --slow   # every adapter, real rows
benchproofer smoke gates.waiver        # one case
benchproofer smoke all --slow -j 4 --report reports/
```

| option | meaning |
| --- | --- |
| `--slow` | also select and run the cases that take minutes, such as one that downloads a dataset or builds a container |
| `--workspace DIR` | where cases build their bundles; contents are replaced per run |
| `--strict` | exit 3 if any case was skipped rather than run |
| `--list` | list the suites, groups, and cases, and run nothing |

The argument selects a suite, a group, or one case id, in that order. See
[Smoke suite](smoke.md).

## Agent sessions

Drafting the solution, the proof, the repair and each review auditor are agent sessions
(`session`); the one that ships, `claude-code`, runs Claude Code through the Claude Agent
SDK, and another coding agent's command-line tool, such as Codex CLI or Kiro CLI, can take
its place ([Bring your own agent](guides/bring-your-own-agent.md)). Every session works in a workspace of its own, laid out as the command's section above
describes, and is held to the same limits:

- **Tools.** It has the built-in tools its stage gives it and no others: the disclosure
  auditor, which reads blind, has `Read`, `Grep` and `Glob`; every other session has those,
  `Bash`, `Write`, `Edit` and `TodoWrite`. None has a web tool. Background tasks are off, so
  every command runs in the foreground, and one still running after `oracle_timeout_s`
  seconds, or the session's own budget where that is shorter, is stopped.
- **What it may read.** A tool call that names a path is refused unless the path is under
  the session's workspace; the toolchains the run's checkers use, which are the Python
  environment and the interpreter it was made from, `toolchain_dir`, the Lean toolchains
  (`ELAN_HOME`, or `~/.elan`) and the Lake workspace `BENCHPROOFER_LEAN_WORKSPACE` or
  `BENCHPROOFER_VELVET` names; the directory where Claude Code saves a tool output of this
  session's too long to show, and not the transcripts of the other sessions started in the
  same workspace beside it; or `/usr`, `/lib*`, `/bin`, `/etc`, `/proc` and `/dev`. Benchproofer's own package, and a process's directory under `/proc`, are refused
  even there. `Read`, `Grep` and `Glob` are judged by their path arguments, and `Bash` by
  each word of the command that reads as a path, taken from the directory the command runs
  in or one it changes into, with `~` and the session's variables spelled out and symlinks
  followed. A shell pattern is judged by the directory it searches, so a search from `/`, or
  from a directory that holds other workspaces, is refused, and so are `locate` and a `cd`
  that names no directory, which goes home. A path under a top-level directory this machine
  does not have, such as a container's `/app`, names nothing here and is let through.
- **What it may write.** Its file tools write only what its stage names (the solution file
  for drafting and for a proof, the copy of the bundle for a repair), its `scratch/`
  directory and its temporary directory. Its shell is limited only by what it may read, and
  only the files its stage asks for are read back.
- **Its environment.** The shell is `/bin/bash`; `TMPDIR` names `tmp/` in the workspace;
  `PYTHONPATH` and every `BENCHPROOFER_*` variable are empty. The `tools` and `check`
  scripts in the workspace read the run's settings, its module path and its own `TMPDIR`
  from a file under the cache directory (`environments/`), which the session may not read,
  so a script shows neither where Benchproofer is installed nor how the run is set. The
  file sets every setting but the ones that reach a model, which it leaves to the provider
  that refuses every request, so a session cannot reach a model through a script.

The prompt of every session but the disclosure auditor's describes these tools and limits
in the same words, from `core/templates/tools-rules.md`, with this run's time limits and the
time the session started and is stopped: among them, that a program is sent alone, without
the rest of the workspace, where the benchmark's tests ran, how to set up what the
repository's tests set up, and how to keep a call that may not end from taking the whole
time limit.

The read check reads the text of each call, not what a program does once it runs: the body
of a here-document, which is a program's input, and a path a program builds as it runs,
such as a Python `open` of a name it joins or decodes, are not seen. So it keeps a session
from reaching another run's work by a path it names or a search, and is not a sandbox; what
a session's work counts for is decided by the gates, which re-run every file it hands over.
The toolchain directories are readable whole, so point `BENCHPROOFER_LEAN_WORKSPACE` and
`BENCHPROOFER_VELVET` at a Lake workspace that holds only its `lakefile`, `lean-toolchain`,
`lake-manifest.json` and `.lake`, not one where another tool keeps its own files beside
them.

## Settings

Every setting can come from three places, in increasing precedence: a
`benchproofer.toml` in the working directory, a `BENCHPROOFER_*` environment variable,
and a command-line option.

```toml
# benchproofer.toml
[benchproofer]
bundle_root = "corpus"
provider = "anthropic"
model = "claude-opus-5"
verify_timeout_s = 600
mutation_limit = 24
concurrency = 8
```

```bash
export BENCHPROOFER_BUNDLE_ROOT=/data/corpus
export BENCHPROOFER_OFFLINE=1
```

`benchproofer doctor` prints the resolved values, which is the quickest way to find out
which of the three won.

| setting | default | what it controls |
| --- | --- | --- |
| `bundle_root` | `bundles` | where bundles are read and written |
| `cache_dir` | the user cache directory | datasets, checkouts, and gate scratch space |
| `toolchain_dir` | `.toolchains` | where `scripts/install/*.sh` put verifiers |
| `provider` | `null` | model provider for drafting |
| `model` | empty | provider-specific model id |
| `audit_model` | empty | language model the review stage uses; unset means the drafting language model reviews its own work |
| `cassette_dir` | `cassettes` | where `--record` writes what the run asks of its language models |
| `verify_timeout_s` | 300 | how long a checker gets to reason about one file |
| `oracle_timeout_s` | 3600 | budget per run of the benchmark's tests |
| `harness_timeout_s` | 1800 | budget of one run of a drafted `conformance.py` or `axioms.py`; `conformance.py` draws inputs for two thirds of it |
| `max_output_tokens` | 32768 | response budget per language-model request, reasoning included |
| `concurrency` | 4 | tasks formalized or judged at once |
| `offline` | false | refuse network access |
| `mutation_limit` | 16 | mutants per bundle, each costing one checker invocation |
| `conformance_inputs` | 100000 | inputs a bundle's `conformance.py` aims to compare; a target, not a floor: `impl.conformance` (the paper's conformance gate) passes an agreement over fewer, records how many were compared, and says in its summary that the run fell short of the target |
| `audit_attacks` | 5 | wrong implementations a review is asked for |
| `audit_min_attacks` | 5 | attacks that must be decided before surviving them counts as evidence; one the attack validation auditor left without a ruling after it was asked again is not decided |
| `audit_controls` | 3 | correct implementations, written differently, a review is asked for |
| `audit_min_controls` | 1 | of those, how many the specification must accept, each shown correct |
| `max_repairs` | 5 | repair sessions `run` runs on one bundle, at every level, each one spent whether its work was taken or not; an auditor asked again spends none of it ([Where a verdict goes](gates.md#where-a-verdict-goes)) |
| `session` | `claude-code` | agent session the drafting, proof, repair and review use; see [Bring your own agent](guides/bring-your-own-agent.md) |
| `session_model` | empty | model the drafting, proof and repair sessions run on; unset means the drafting model. The review sessions run on `audit_model` |
| `draft_turns` | 200 | turns the session drafting the solution may take |
| `draft_timeout_s` | 3600 | seconds the session drafting the solution may take |
| `repair_turns` | 200 | turns one repair session may take |
| `repair_timeout_s` | 9000 | seconds one repair session may take |
| `review_turns` | 200 | turns one review session may take, the attack validation auditor's included |
| `review_timeout_s` | 10800 | seconds one review session may take, the attack validation auditor's included |
| `prove_agent` | true | under a backend whose files contain their proofs, hand a drafted file the checker rejected to an agent session that writes its proof |
| `prove_turns` | 200 | turns one proof session may take |
| `prove_timeout_s` | 3600 | seconds one proof session may take |

`verify_timeout_s` is time to reason, not wall clock. A backend that starts a JVM or
loads a library the size of Mathlib declares what that costs, and the budget is added on
top of it, so raising the setting buys checking time on every backend rather than paying
for the slowest one's startup. `benchproofer catalog backends --json` reports what each
one declares as `startup_s`.

Five overrides are read directly from the environment rather than from settings, because
they name a path rather than configure a run: `BENCHPROOFER_DAFNY`, `BENCHPROOFER_LEAN`
and `BENCHPROOFER_NAGINI` each name an executable, and `BENCHPROOFER_VELVET` and
`BENCHPROOFER_LEAN_WORKSPACE` each name a built Lean workspace, the one Velvet is checked
in and one `lean4` elaborates in, importing its packages. See
[Backends](backends.md#finding-the-executable).
