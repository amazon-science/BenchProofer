# Add a benchmark

An adapter owns one dataset. It fetches the rows, pins what it fetched, and turns each
row into a `Task`. Nothing downstream knows which benchmark a task came from, so a new
benchmark is a new adapter and never a new code path.

Before writing one, check whether you need to. A file of task objects needs no code at
all:

```bash
benchproofer ingest jsonl --extra source=my-tasks.jsonl --extra name=my-suite
```

See [Benchmarks](../benchmarks.md#your-own-tasks) for that format. Write an adapter when
the rows live somewhere else, when normalizing them takes real work, or when you want
other people to reach your dataset by name.

## The interface

Two methods are required and one is worth writing:

| method | returns |
| --- | --- |
| `info()` | what is this dataset, who published it, which oracle judges it |
| `load(request)` | the tasks, in a stable order |
| `availability()` | can this adapter load anything on this machine |

```python
from collections.abc import Iterator
from typing import ClassVar

from benchproofer.benchmarks.base import Benchmark, BenchmarkInfo, LoadRequest
from benchproofer.core.plugin import Availability
from benchproofer.core.task import OracleSpec, Reference, SourceFile, Task, TaskContext
from benchproofer.util.digest import digest_json


class MyBenchmark(Benchmark):
    """One dataset, normalized."""

    name: ClassVar[str] = "my-suite"

    def info(self) -> BenchmarkInfo:
        return BenchmarkInfo(
            name=self.name,
            title="My Suite",
            summary="What the tasks are, in one sentence.",
            license="CC-BY-NC-4.0",
            oracle="inline-tests",
            size=120,
            remote=True,
        )

    def availability(self) -> Availability:
        return Availability.ok()

    def load(self, request: LoadRequest) -> Iterator[Task]:
        rows = self._rows(request)
        return self.take((self._task(row) for row in rows), request)
```

`self.take(...)` applies the request's filters, so you do not implement selection
yourself. `LoadRequest` carries `ids`, `limit`, `offline`, `cache_dir`, and the
`--extra key=value` pairs as `extras`.

Selection is deterministic on purpose: `ids` wins, then `limit` takes the first tasks in
your order. There is no sampling, because a subset that changes between runs cannot be
compared between runs. Yield in a fixed order and the rest follows.

## Normalizing a row

`Task` is the shape everything downstream reads. Four fields carry the weight:

| field | what it holds |
| --- | --- |
| `statement` | the task as the benchmark poses it, verbatim where possible |
| `context` | the code under specification: inline `files`, or a `repository` |
| `reference` | the benchmark's own solution, the golden patch: a `patch`, `files`, or an `answer` |
| `oracle` | how to decide mechanically whether a candidate solved it |

A row that ships a module and a test program is the simplest case:

```python
def _task(self, row: dict[str, object]) -> Task:
    return Task(
        benchmark=self.name,
        task_id=str(row["id"]),
        statement=str(row["prompt"]),
        context=TaskContext(
            files=(SourceFile(path="solution.py", content=str(row["stub"])),),
            entry_points=(str(row["entry_point"]),),
        ),
        reference=Reference(
            files=(SourceFile(path="solution.py", content=str(row["solution"])),)
        ),
        oracle=OracleSpec(kind="inline-tests", tests=(str(row["tests"]),), timeout_s=60),
        metadata={"dataset": self.spec.pin},
        source_digest=digest_json(row),
    )
```

Two of those lines matter more than they look:

* **`reference`** is what `spec.discriminates` (the paper's discrimination check) and
  `oracle.reference_resolves` (the resolution check) need. A task with no golden patch
  can still be formalized, but two gates have nothing to work with, so the bundle cannot
  be certified.
* **`source_digest`** pins the upstream row this normalization came from. It is what lets
  `artifact.integrity` (the paper's task-identity check) notice that a dataset changed
  after a bundle was built. `digest_json(row)` over the raw row is the usual choice.

Put anything you did not model into `metadata`. It is excluded from `Task.digest()`, so
annotating a task later does not invalidate the bundles built from it.

## Pinning the data

`DatasetSpec` names a Hugging Face dataset repository by commit, and optionally by
SHA-256 per file:

```python
from benchproofer.benchmarks.dataset import DatasetSpec, fetch, read_rows

spec = DatasetSpec(
    repo_id="openai/openai_humaneval",
    revision="7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544",
    files=("openai_humaneval/test-00000-of-00001.parquet",),
    license="MIT",
    url="https://huggingface.co/datasets/openai/openai_humaneval",
    digests={
        "openai_humaneval/test-00000-of-00001.parquet": (
            "sha256:2f2871a15fbc95b6c683043359f4ed8e144c5a1c4f24f25f66bc51f598dfcfb6"
        )
    },
)
```

A branch name is not a pin. With `digests` set, `fetch()` refuses a copy whose bytes
disagree with the pin rather than building bundles from it. Downloads land in the run's
cache directory, and `--offline` refuses to perform any, which is why `load()` has to
pass `request.offline` through:

```python
paths = fetch(spec, request.cache_dir, offline=request.offline)
rows = (row for path in paths for row in read_rows(path))
```

`read_rows` handles Parquet and JSON Lines. Subclassing `HubBenchmark` gives you the
fetch-and-normalize loop and leaves you writing only `info()` and `normalize(row,
index)`; it is worth reading `benchproofer/benchmarks/builtin.py` for the four shapes
already covered there.

Data that is not on the Hub is not a problem: `quixbugs.py` checks out a git repository
at a pinned commit, and a local adapter can read whatever it likes. The rule is the
pin, not the transport.

## Choosing the oracle

`info().oracle` names the registered oracle your tasks are judged by, and every task
should agree with it. Pick the weakest one that actually decides the task:

| oracle | for |
| --- | --- |
| `inline-tests` | a module plus a test program, run in a subprocess |
| `pytest` | a project whose suite runs on this machine |
| `answer` | a task whose answer is a value, not a program |
| `docker` | a repository that needs its own image |
| `none` | no mechanical check, which caps the run at `--level static` |

## Registering it

Declare the entry point in your own package. Nothing in Benchproofer is edited:

```toml
[project.entry-points."benchproofer.benchmarks"]
my-suite = "my_package.benchmark:MyBenchmark"
```

The value may be a class, a zero-argument factory, or an instance. Install with
`pip install -e .` and it appears:

```bash
benchproofer catalog benchmarks
benchproofer ingest my-suite --limit 2
```

## What you get for free

The smoke suite builds its benchmark cases from the registry, so installing your adapter
adds a case for it:

```bash
benchproofer smoke benchmarks
```

That case ingests two tasks and checks the contract rather than the data: the adapter
agrees with its own catalog entry, every task names a registered oracle, ships the
benchmark's own solution, carries a `source_digest`, and survives being frozen and read
back. Ingesting your own file with `--limit 2` and reading `task.json` is the same check
by hand.

## Checklist

* `info()` names itself, has a title and a summary, and names a registered oracle.
* Tasks come out in a stable order, and `take()` does the filtering.
* Remote data is pinned by revision, and by digest where the host allows it.
* `load()` honors `request.offline` instead of reaching the network anyway.
* Every task carries a `source_digest` and the benchmark's own solution.
* `benchproofer smoke benchmarks` passes with your adapter installed.

`examples/plugin/` in the repository is a working adapter in about eighty lines, shipping
its rows instead of downloading them so that it runs anywhere.
