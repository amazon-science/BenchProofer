# Smoke suite

The smoke suite asks one question: what can this installation actually do? Not "do
the unit tests pass", which is a question about the source, but "does this machine
ingest that benchmark, does that verifier accept its own template, does the pipeline
produce the verdicts it claims to".

```bash
bash scripts/smoke.sh              # offline: no network, no container, no API key
bash scripts/smoke.sh benchmarks   # ingest a sample of every registered benchmark
bash scripts/smoke.sh oracles      # every correctness oracle, SWE-bench included
bash scripts/smoke.sh all          # everything; what this machine cannot run is skipped
bash scripts/smoke.sh ci           # offline, and a skipped case is a failure
```

The script only picks arguments for `benchproofer smoke`, so anything the command
supports works through it:

```bash
bash scripts/smoke.sh all --jobs 8 --json
benchproofer smoke gates.tampered
benchproofer smoke benchmarks.swebench-verified --slow
```

Each profile writes `smoke.json` and `smoke.md` under `smoke-out/<profile>/`.

## What the offline suite covers

Twenty-four cases, a few minutes, no network, no container runtime, and no language-model
credentials. A case joins this suite by declaring what it needs, not by being added to a
list: it is hermetic when it is not slow and needs neither the network nor a container.

| group | cases | what they establish |
| --- | --- | --- |
| `registry` | 2 | every declared plugin imports and reports its own name; the required gates are registered and their levels agree |
| `backends` | 6 | each backend verifies its own template and rejects a mutant of it |
| `benchmarks` | 1 | the `jsonl` adapter produces tasks that satisfy the task contract |
| `oracles` | 3 | the inline-test and answer oracles accept the golden patch and reject the pre-fix state; a benchmark with no oracle never reports a candidate as correct |
| `gates` | 6 | four fixture bundles are judged as they should be, a waiver is recorded as a waiver, and a tampered bundle loses its certification |
| `pipeline` | 2 | a corpus is judged, reported, and not judged twice; a formalization session writes back its artifacts byte for byte |
| `review` | 4 | a reviewed bundle certifies at the audited level; rewriting a reviewed specification expires the review of it; a bundle that fails review is repaired, reviewed again, and certified; a model of an unchanged callee survives an independent fuzzer |

The six `gates` cases are the ones worth reading, because they are the suite's evidence
that adjudication discriminates. Four fixture bundles ship with Benchproofer:

| fixture | what it is | expected outcome |
| --- | --- | --- |
| `coin-change-sound` | a sound formalization | certified, every required gate favorable at `--level oracle` |
| `coin-change-weak` | a specification too weak to reject the bug the task is about | not certified: `spec.discriminates` (the discrimination check) and `spec.strength.battery` (property-based falsification) object |
| `running-total-leaky` | a specification that restates the golden patch | not certified: `spec.no_leakage` (the mechanical half of the paper's leakage gate) objects |
| `safe-join-assumed` | a specification that models a standard-library callee in its `axioms` region | certified, with `spec.axioms_grounded` (part of the paper's axiom-soundness gate) reporting what `axioms.py` put to the real callee |

A suite that only ever judged sound artifacts would prove nothing. These two defective
bundles are what shows the gates fire, and the `tampered` case shows that editing a
bundle after it was judged takes its certification away.

`pipeline.build` covers the drafting stage on two scripts that reach no model: a session, `scripted`, that writes the fixture's solution file into its workspace
and submits the report a drafting session submits, and a provider that replies to each later
request with the artifact the fixture already ships. Neither is a mock: extraction,
splicing, checking, repair, and the manifest all run exactly as they do against a real
language model. What the case asserts is that drafting wrote back the artifacts it was
given, byte for byte.

## Why review is in the offline suite

The seven [audited gates](gates.md#audited-gates) are the ones a program cannot decide for
itself, which makes them the easiest to leave untested, and the ones a bundle's
certification finally rests on. So the `review` cases run the auditors and the repair
session on the same scripted session, from a fixture that also declares what a reviewer
concludes, and `tests/unit/test_smoke_catalog.py` asserts that every one of them is
hermetic:

| case | what it establishes |
| --- | --- |
| `review.certified` | a bundle whose review found nothing reaches `certified` at `--level audited`, with every submission re-run and every judgment current |
| `review.stale` | splicing a different specification into a reviewed bundle turns all three judgment gates and both strength gates undecided, naming the file that changed, while `audit.independence` still holds |
| `review.loop` | a bundle whose specification is too weak is rejected by review, repaired, reviewed again, and certified, the re-review attacking the repaired specification afresh, shown the attacks filed before it |
| `review.assumed` | a specification that models a callee is certified only once the bundle's own `axioms.py` and a reviewer's independent fuzzer have both put that callee to the benchmark's environment |

`review.loop` is the round trip that matters, because it is where a repair could quietly
address one finding by dropping another. The case asserts that the re-review's attack auditor
is shown each attack the first review filed, with the gates' ruling that it is a weakness,
and that the certification rests on the re-review's own submissions, the earlier ones no
longer on record.

## What `--slow` adds

| group | cases | needs |
| --- | --- | --- |
| `benchmarks` | 7 more, one per public adapter | network, and `git` for QuixBugs |
| `oracles` | `oracles.pytest`, `oracles.docker` | network, pytest, a container runtime |
| `backends` | `backends.velvet` | the workspace `scripts/install/velvet.sh` builds |

`oracles.docker` judges a real SWE-bench Verified instance in its own image and
`oracles.pytest` judges a QuixBugs task with the project's own tests. These are the cases
that show Benchproofer works on the benchmarks people care about, and they are the
slowest by a wide margin: the first run builds or pulls a container image.

A backend is slow here when it says so, `Backend.slow`, which today means `velvet`: each
of its invocations elaborates against Mathlib, and the case runs several of them. It
needs nothing but this machine, so `benchproofer smoke --slow` runs it: the offline suite
leaves a slow case out of a quick run rather than out of the suite.

## Requirements, probed before anything runs

A case declares what it needs as strings, and every distinct requirement is probed once
before the run starts:

| requirement | means |
| --- | --- |
| `network` | the run is allowed to reach the network |
| `docker` | a container runtime the docker oracle can drive |
| `tool:<name>` | an executable on the path, such as `git` |
| `module:<name>` | an importable Python module |
| `backend:<name>` | a registered backend whose checker runs here |
| `benchmark:<name>` | a registered benchmark adapter that can load here |
| `oracle:<name>` | a registered oracle that can run here |
| `provider:<name>` | a registered model provider that is configured |

Probing up front is what lets the report say what this machine offered, rather than
leaving each case to discover the same missing toolchain on its own.

## Four outcomes, kept apart

| outcome | meaning |
| --- | --- |
| `passed` | Benchproofer did what the case requires |
| `failed` | Benchproofer did something else, and the message says what |
| `skipped` | this machine does not meet a requirement the case declared |
| `error` | the case itself fell over, which is a defect in the suite |

Collapsing these is how a suite starts reporting green for work it never did, so the
summary prints all four:

```
# Benchproofer smoke run: offline

- cases: 25
- passed: 25
- failed: 0
- skipped: 0
- error: 0
- wall clock: 154.0s
```

A run is sound when nothing failed and nothing errored. What it *covered* is a separate
number, which is why `--strict` exists: it exits 3 if any case was skipped, and it is
what `scripts/smoke.sh ci` uses. On a machine with `make toolchains` installed, the
offline profile under `--strict` is a full pass over everything that does not need the
network.

Each case also gets its own bundle root, so an assertion about a bundle is an assertion
about the bundle that case built. The dataset cache is shared, because re-downloading a
benchmark per case would make the suite unusable.

## Adding a case

Cases live in `src/benchproofer/smoke/cases/`, one module per group. A case is a
function plus a declaration of what it needs and what it establishes; adding a group is
a new module plus one entry in `_MODULES` in `smoke/suites.py`. `benchproofer smoke
--list` shows the result, and `tests/unit/test_smoke_catalog.py` checks that every case
is reachable and that its declared requirements are ones the prober understands.

## Smoke suite and test suite

They ask different questions and both are part of `make check`:

| | asks |
| --- | --- |
| `pytest` | is the source correct, on any machine, with nothing installed |
| `benchproofer smoke` | is this installation, on this machine, able to do the work |

A pull request needs the first. A new deployment, a new machine, or a new toolchain
version needs the second.
