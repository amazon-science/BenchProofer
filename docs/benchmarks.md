# Benchmarks

An adapter owns one upstream dataset. It fetches the rows, pins what it fetched, and
normalizes each row into a `Task`. Nothing downstream knows which benchmark a task came
from, which is what makes Benchproofer general: a new benchmark is a new adapter, not a
new code path.

```bash
benchproofer catalog benchmarks          # the table below, for your installation
benchproofer catalog benchmarks --json   # with licenses, URLs, and pins
```

## What ships

| adapter | tasks | shape of a task | oracle | license |
| --- | --- | --- | --- | --- |
| `swebench-verified` | 500 | repository at a commit, test patch, two test lists | container | see the dataset card |
| `swebench-lite` | 300 | the same, smaller | container | see the dataset card |
| `swebench-pro` | 266 | the same, over repositories held back from training | container | see the dataset card |
| `bigcodebench` | 1140 | stub composing third-party libraries, unittest suite | inline tests | Apache-2.0 |
| `humaneval` | 164 | function stub with a docstring, `check()` routine | inline tests | MIT |
| `mbpp` | 500 | prose statement and assertions, no stub | inline tests | CC-BY-4.0 |
| `gsm8k` | 1319 | arithmetic word problem, numeric answer | answer | MIT |
| `quixbugs` | 40 | one-line defect, with the pre-fix version alongside | pytest | MIT |
| `jsonl` | your file | whatever you write | declared per task | yours |

Sources: SWE-bench Verified and Lite, Jimenez et al., *SWE-bench* (2024); SWE-bench Pro,
Scale AI (2025); BigCodeBench, Zhuo et al. (2024); HumanEval, Chen et al., *Evaluating Large
Language Models Trained on Code* (2021); MBPP, Austin et al., *Program Synthesis with Large
Language Models* (2021); GSM8K, Cobbe et al., *Training Verifiers to Solve Math Word
Problems* (2021); QuixBugs, Lin et al. (2017).

Four shapes, one pipeline. A stub plus a test program, a statement plus assertions, a
question plus a number, and a repository plus a container are all `Task` objects by the
time anything else sees them.

GSM8K is in that list on purpose. A tool that can only formalize programming benchmarks
is not general, and an arithmetic word problem formalized as an obligation over integers
is the smallest case that shows the machinery does not assume a program.

`swebench-pro` reaches part of its upstream dataset on purpose. Those 731 instances span
eleven repositories in four languages; the 266 offered here are the Python ones, whose
suites the container oracle can drive and whose reports it can read. The Go and
JavaScript instances report through runners no reader here understands. An Ansible
instance that required an integration test would need a runner other than the unit one
its siblings use, and would be skipped too. Skipping a row is better than misreading it:
an oracle that cannot read its own report returns "undecided" for every candidate.

## Which one to start with

QuixBugs, if you are bringing up a backend. Each task is small enough for a checker to
handle, and it ships the pre-fix implementation alongside the fixed one, so every bundle
gets its real pre-fix implementation for `spec.discriminates` (the paper's discrimination
check) without anyone hand-writing one.

HumanEval, if you want the shortest path to a certified bundle: 164 self-contained
functions, an inline test oracle that needs no container, and statements short enough
that a specification is a few lines.

SWE-bench, if you want to know whether the corpus says anything about real software. Its
tasks are repository changes, its oracle is the project's own test suite in a container,
and it is where `impl.conformance`, the paper's conformance gate, earns its place.

## Ingesting

```bash
benchproofer ingest humaneval --limit 20
benchproofer ingest swebench-verified --id astropy__astropy-12907
benchproofer ingest mbpp --limit 5 --offline    # cached rows only
```

Selection is deterministic. `--id` wins, then `--limit` takes the first tasks in the
adapter's own stable order. There is no sampling flag, because a benchmark subset that
changes between runs cannot be compared between runs.

Ingestion freezes what it read: `task.json` under `<bundle root>/<benchmark>/<slug>/`,
plus `reference.patch` when the golden patch is a diff. Neither is rewritten without
`--refresh`, so a bundle judged last week cannot acquire a different statement this week.

## Pinning

A dataset is named by repository *and* revision, never by a branch, and every file is
checked against a recorded SHA-256 after download:

```python
DatasetSpec(
    repo_id="openai/openai_humaneval",
    revision="7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544",
    files=("openai_humaneval/test-00000-of-00001.parquet",),
    digests={...},
)
```

QuixBugs is published as a Git repository rather than a dataset file, so it is fetched
as a checkout pinned to a commit, verified against it, and reused without touching the
network afterwards.

Downloads land in the cache directory, which `benchproofer doctor` prints. A second run
over the same benchmark performs no network access at all, and `--offline` turns a cache
miss into an error rather than a download.

## Your own tasks

The `jsonl` adapter reads a local file, so a benchmark that is unpublished, proprietary,
or unable to leave a network runs through the same commands as a public one:

```bash
benchproofer ingest jsonl --extra source=my-tasks.jsonl --extra name=my-suite
```

| `--extra` | meaning |
| --- | --- |
| `source` (or `path`) | the JSON Lines file to read; required |
| `name` | the suite tasks are filed under; defaults to the file's stem |

A row may name its own `benchmark`, which wins over `name`, so one file can hold tasks
of several suites. Ingestion reports the names it filed tasks under, and those are what
`formalize`, `check`, and `report` take.

One JSON object per line, with the fields of `Task`. Only `task_id` and `statement` are
required:

```json
{"task_id": "coin-change", "statement": "Return the fewest US coins that make an amount.", "oracle": {"kind": "inline-tests", "tests": ["assert impl(30) == (1, 0, 1, 0)\n"]}}
```

A richer row can include the starting files, the golden patch (here as whole files), and
the oracle specification:

```json
{
  "task_id": "running-total",
  "statement": "Return the running totals of a list of integers.",
  "context": {"files": [{"path": "totals.py", "content": "def totals(xs):\n    ...\n"}]},
  "reference": {"files": [{"path": "totals.py", "content": "def totals(xs):\n    out = []\n    acc = 0\n    for x in xs:\n        acc += x\n        out.append(acc)\n    return out\n"}]},
  "oracle": {"kind": "inline-tests", "tests": ["assert totals([1, 2, 3]) == [1, 3, 6]\n"]}
}
```

`examples/tasks.jsonl` is a working file of three tasks; the [quickstart](quickstart.md)
runs it end to end.

## Oracles

An oracle decides the benchmark's own question: does this candidate solve the task? It is
what `impl.conformance` and `oracle.reference_resolves` (the paper's resolution check)
consult, and it is separate from the verification backend on purpose. A backend decides
whether an implementation meets a specification; an oracle decides whether a change
satisfies the benchmark. Comparing the two verdicts is what makes a specification
auditable rather than merely plausible.

| oracle | how it decides | needs |
| --- | --- | --- |
| `inline-tests` | runs the task's own test program in a child process | nothing |
| `pytest` | runs pytest over the task's test files | pytest |
| `answer` | compares a literal answer with the benchmark's own | nothing |
| `docker` | applies the patch and runs the tests in the task's image | Docker |
| `none` | declines; there is no mechanical check for this benchmark | nothing |

Two details matter for reading a report:

* Judging is per test, not per exit code. An oracle that looked only at the exit status
  could not tell "the fix works" from "an unrelated test in the same file was already
  failing", so the built-in oracles read the runner's own report. A task names the log
  format its runner produces.
* An oracle that cannot run here reports `oracle_unavailable`, and the bundle is
  `incomplete` at `--level oracle` rather than rejected. `none` is the same story by
  construction: a benchmark with no mechanical check never reports a candidate as
  correct, so such a corpus is certifiable at `static` only.

The container oracle runs with networking off unless the task declares
`oracle.network`, because a suite that reaches a live service decides a different
question on every run. When tests then fail in a way that looks like a blocked
connection, the oracle says so rather than reporting the candidate as wrong.

## Adding an adapter

One class, one `load` method, one entry point, and a pin. See
[Add a benchmark](guides/add-a-benchmark.md).
