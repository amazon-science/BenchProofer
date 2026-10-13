# Architecture

Benchproofer is a pipeline of six stages over six kinds of plugin. Nothing in the
pipeline knows which benchmark, verifier, oracle, language model or agent session is in
use, which is what makes adding one an addition rather than an edit.

## The six plugin kinds

| kind | the question it is for | entry-point group |
| --- | --- | --- |
| benchmark | what are the tasks, and how are they pinned | `benchproofer.benchmarks` |
| backend | does this file satisfy its own specification | `benchproofer.backends` |
| oracle | does this candidate solve the benchmark's task | `benchproofer.oracles` |
| gate | is this bundle sound in one specific way | `benchproofer.gates` |
| provider | which language model drafts the artifacts, and which reviews them | `benchproofer.providers` |
| session | which agent session drafts the solution, proves it, repairs the bundle, and reviews it | `benchproofer.sessions` |

Every one is discovered through `importlib.metadata`, and the built-in components are
declared in this project's own `pyproject.toml` under those same groups. There is no
internal list of "real" components that a third-party package has to be added to.

```python
from benchproofer.registries import BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS, SESSIONS

BACKENDS.names()          # every backend visible in this installation
BACKENDS.get("dafny")     # resolved and cached
BACKENDS.register("mine", MyBackend)   # in-process, shadows an entry point
```

`register` exists for tests and for embedding. Ordinary installations never need it.

## The six stages

```
ingest      upstream rows        ->  task.json, reference.patch   (frozen)
formalize   task + backend       ->  solution, twins/, rivals/, correspondence.md,
                                     conformance.py, axioms.py
audit       bundle + reviewer    ->  submissions, fuzzers, rulings and judgments, in audit/
check       bundle + gates       ->  one verdict per gate, in manifest.json
repair      bundle + findings    ->  the same artifacts, edited in place
report      manifest verdicts    ->  certified / rejected / incomplete / dropped
```

`audit` and `repair` are the two stages a bundle may visit more than once. `run` is that
loop at every level, bounded by `max_repairs`: it judges a bundle, repairs what the gates
found, and judges it again; at `--level audited` each round also reviews the bundle, once
none of the gates a program decides holds it back. A repair expires the judgments of what
it changed -- each judgment records the digests of what it read -- so the bundle has to be
reviewed again before it can certify. Only the auditors that read what changed are asked
again. A repair that leaves the bundle worse is not rolled back; the next repair addresses
what it broke. Nothing is drafted after a repair either: a file it leaves missing, or a first
draft the checker refused left without, fails its gate and goes to the next. So does a
pre-fix implementation the repair deleted, and a case of the property-based test suite it
deleted unless the last `spec.strength.battery` verdict found that case defective. A
finding that a case of the property-based test suite is defective as a
case -- unreadable, not keeping the shipped specification, using a construct the solution
file does not (`sorry`, an axiom, a directive) or proving a claim of its own, or correct
with a proof the checker rejected -- is resolved by fixing the case, never the
specification, since none of them says anything about the specification.

Each stage is a function in `benchproofer.pipeline` or one of its modules, and each writes
its result to disk before the next one reads it:

```python
from benchproofer.pipeline import adjudicate, build, collect, execute, ingest
from benchproofer.pipeline.audit import audit
from benchproofer.pipeline.repair import repair
```

`execute` is the loop the CLI uses. The stages underneath it are public because a
project that wants its own loop, its own order, or its own concurrency should not have
to reimplement them.

Three properties follow from this shape rather than from discipline:

* **A run is resumable.** The bundle on disk is the state of the work, so an
  interrupted run restarted picks up where the artifacts say it stopped.
* **Judging is repeatable by a stranger.** `check` consults no language model and writes
  no artifact, so anyone can re-judge someone else's corpus and compare verdicts.
* **One task's failure is local.** A task that raises is recorded as an error on that
  bundle and the loop continues.

## Where the honesty rules live

The interesting parts of the design are all in one direction: making absence of
evidence impossible to mistake for evidence.

| rule | enforced in |
| --- | --- |
| a crashed gate is an error, never a finding | `gates/base.py`, `Gate.run` |
| every verdict carries the judge digest and Benchproofer version that produced it | `gates/base.py`, `Gate._stamp` |
| a bounded refuter that found nothing is undecided, not a pass | `gates/base.py`, `Gate.weakness` |
| a variant is only evidence if the shipped implementation verifies | `gates/base.py`, `Gate.needs_verified_base` |
| "the checker gave no verdict" is not "the checker said no" | `backends/base.py`, `CheckResult` |
| a mutant the checker could not read, or refused, is not counted | `gates/mutation.py` |
| a mutant can never weaken the contract it is judged against | `core/markers.py`, `core/mutation.py` |
| certification is decided in exactly one place | `core/verdict.py`, `classify` |
| so is where a verdict that does not pass goes: repair, ask again, hold the review, or stop | `pipeline/route.py`, `ROUTES` |
| a language model is never consulted on the path that produces a verdict | `llm/base.py`, and the absence of any provider import under `gates/` |
| a reviewer's claim about a submission is re-run, never believed | `gates/audit.py`, `_rerun` |
| what a specification assumes of a callee is put to the callee itself | `gates/axioms.py`, `core/axioms.py` |
| a judgment expires when what it was read from changes | `core/bundle.py`, `Judgment.stale`; `core/readings.py` |
| a ruling on what no run decides counts only with its input and what it rests on, while what it was reached from is unchanged | `core/bundle.py`, `Ruling`; `gates/audit.py`, `_validated` |
| the benchmark's tests run once on a submission, however often the gates read it | `gates/audit.py`, `_recorded` |
| a defect a reviewer files is an input `conformance.py` compares, not a claim another auditor decides | `audit/agents.py`, `_defects`; `pipeline/audit.py`, `write_audit`; `gates/conformance.py`, `_unreplayed` |
| a gate that could not measure never overwrites one that did | `pipeline/adjudicate.py`, `_standing` |
| a review by the language model that drafted the bundle is not an independent one | `gates/audit.py`, `IndependenceGate` |

`Gate.run` is a template method and is documented as one: subclasses implement
`judge`, and the stamping, waiver handling, and exception trapping are not theirs to
override.

## Package map

```
src/benchproofer/
    core/         the vocabulary: tasks, bundles, markers, mutation, verdicts, registry,
                  and the rules files the drafting, the repair and the review prompts
                  all include
    benchmarks/   one adapter per upstream dataset, plus pinned download and checkout
    formalize/    the drafting session: prompts, material budgets, extraction, repair
    audit/        the review: one agent session per auditor, the tools a session runs, and
                  what is kept of it
    backends/     one adapter per checker
    oracles/      the benchmark's own correctness check, plus test-log readers
    gates/        one module per gate, all subclassing Gate
    pipeline/     ingest, build, audit, adjudicate, route, repair, report, and the loop
                  over them
    llm/          providers, agent sessions, recording
    smoke/        the installation check, its case catalog, and the fixture corpus
    cli/          one module per command, plus shared options and rendering
    util/         digests, atomic writes, subprocess with timeouts, patch reading
```

Dependencies point inward. `core` reaches only for `util` and `errors`; the layers above
it reach for an interface and a registry name, never for a concrete component. The
pipeline, the gates, and the CLI name no particular verifier and no particular dataset;
the only place that does is the smoke case catalog, whose job is to name them.

## Three things kept deliberately apart

**A backend is not an oracle.** A backend decides whether an implementation meets a
specification. An oracle decides whether a change satisfies the benchmark. Keeping them
separate is what lets `impl.conformance`, the paper's conformance gate, compare the two
verdicts, which is the only check that a verified artifact is about the task the
benchmark actually poses.

**Drafting is not judging.** The formalization session runs the checker constantly, as
feedback, and none of those results become verdicts. Verdicts come from gates, which
re-run the checker over the artifacts as they were finally written. A session that
lied about what it produced therefore changes nothing about the outcome.

**Reviewing is not judging either.** A review session writes down what a reviewer
submitted and concluded, and that is all it does. The gates re-run every submission and
report a judgment only while the files it was reached from are unchanged, so a review is
evidence about a bundle rather than a verdict on one. Where the runs cannot tell right from
wrong, the attack validation auditor's ruling decides a submission, and only one that names
the input and what of the task it rests on; `pipeline/audit.py` asks that auditor, for `run`
and `benchproofer audit` alike, after the two gates that re-run submissions have judged what the
review filed. A defect the attack auditor
shows by running code is not a judgment either: its input is handed to `conformance.py`, and
`impl.conformance` decides it.

## Extending

The guides walk through four of the kinds: [add a benchmark](guides/add-a-benchmark.md),
[add a backend](guides/add-a-backend.md), [add a gate](guides/add-a-gate.md),
[bring your own model](guides/bring-your-own-model.md).
