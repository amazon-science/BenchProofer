# Benchproofer

Benchproofer turns a real-world benchmark into a formally verified one. It reads the
tasks of an existing benchmark, formalizes each task into a specification and an
implementation that a verifier checks, has each formalization attacked by someone who
did not write it, and then adjudicates the result with gates that run independently of
whoever produced it.

The design has one commitment behind it: **no self-report is evidence**. A formalization
session can claim anything, and so can a reviewer; only a recorded verdict from a gate
counts as evidence, and a gate that could not decide says so instead of passing.

## Where to start

| you want to | read |
| --- | --- |
| install it and see it work | [Quickstart](quickstart.md) |
| know what a bundle, a level, and an outcome are | [Concepts](concepts.md) |
| follow one task through drafting, the checks, the review and repair | [Workflow](workflow.md) |
| know what "certified" rules out | [Gates](gates.md) |
| use your own tasks | [Benchmarks](benchmarks.md) |
| use another verifier | [Backends](backends.md) |
| check an installation | [Smoke suite](smoke.md) |
| reproduce someone's corpus | [Reproducibility](reproducibility.md) |
| look up a command | [CLI reference](cli.md) |
| add a component | the [guides](guides/add-a-benchmark.md) |

## The shape of a run

```
ingest      upstream rows              ->  frozen tasks under the bundle root
formalize   a task and a backend       ->  a bundle of artifacts
audit       a bundle                   ->  an adversarial review of it, on the record
check       a bundle and the gates     ->  verdicts in the bundle's manifest.json
repair      a bundle and its verdicts  ->  the bundle edited to address them
report      every bundle's verdicts    ->  what holds up and what does not
```

Each stage is a command, and each stage reads what the previous one wrote. Ingestion
freezes its inputs so that a bundle cannot be re-judged against a task that changed
under it. Three stages consult a language model (drafting, reviewing, and repairing),
and the loop between the last three runs until a bundle certifies or the repair budget is
spent. Judging is the only stage that produces verdicts, and it needs no language model,
so anyone can re-run it.
