# Smoke fixtures

Four tiny tasks and four hand-written bundles. They ship with the package so the
smoke suite can exercise the whole pipeline on a machine with no network, no
container runtime, and no model provider.

## `tasks.jsonl`

Four tasks in the shape the `jsonl` benchmark adapter reads, so ingesting them
exercises the same code path a user's own benchmark takes:

| task id | shape | oracle |
| --- | --- | --- |
| `coin-change` | a repair task: a buggy file plus the fixed one | `inline-tests` |
| `running-total` | a synthesis task: a stub plus the completed file | `inline-tests` |
| `orchard-yield` | a question with one numeric answer, and no code at all | `answer` |
| `safe-join` | a repair task whose fix leans on a standard-library callee | `inline-tests` |

It is one JSON object per line, which is compact rather than readable; use
`jq . tasks.jsonl` to read it.

## `bundles/`

Each directory is a formalization of one of those tasks, written by hand, with a
`fixture.toml` that states the outcome adjudication must reach. The suite compares
that claim against what the gates actually decide, so a fixture is a test of the
gates and the gates are a test of the fixture.

| bundle | task | outcome | what it demonstrates |
| --- | --- | --- | --- |
| `coin-change-sound` | `coin-change` | `certified` | every gate passing on a sound formalization |
| `coin-change-weak` | `coin-change` | `incomplete` | a specification too weak to reject the bug it is about |
| `running-total-leaky` | `running-total` | `rejected` | a specification that restates the golden patch |
| `safe-join-assumed` | `safe-join` | `certified` | an unchanged callee modeled in the axioms region, grounded against the real one |

The two defective bundles are the interesting ones. `coin-change-weak` is
recorded as incomplete rather than rejected because its backend is a falsifier: a
falsifier that fails to refute a wrong implementation has not shown the
specification is weak, only that it did not find a counterexample, and Benchproofer
never converts that into a finding.

`safe-join-assumed` is the one that needs the benchmark's own environment to say
anything. Its `axioms` region contains a model of `posixpath.normpath` and declares
that the model represents the callee, `axioms.py` puts the two side by side where the
task's tests run, and the review in its `fixture.toml` writes a fuzzer that attacks
the same model from inputs the bundle's own `axioms.py` never draws.

No bundle ships a `manifest.json`. It is written by the run that judges
the bundle, so the fixtures cannot carry a stale digest or a verdict nobody
recomputed.
