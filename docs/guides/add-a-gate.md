# Add a gate

A gate is one question about one bundle, decided by running something rather than by
reading a claim. You implement `judge`; the base class handles the rest, and the rest is
what the verdicts in `manifest.json` depend on.

## The smallest complete gate

```python
from typing import ClassVar

from benchproofer.core import markers
from benchproofer.core.verdict import Level, SkipReason, Verdict
from benchproofer.errors import BenchproofError
from benchproofer.gates.base import Gate, GateContext

UNFINISHED = ("TODO", "FIXME", "XXX", "placeholder")


class NoTodoGate(Gate):
    """The specification region contains no unfinished-work marker."""

    id: ClassVar[str] = "spec.no_todo"
    title: ClassVar[str] = "Specification has no unfinished-work markers"
    rationale: ClassVar[str] = (
        "A specification that still says TODO was not finished, and a verifier "
        "cannot tell the difference between a contract and a note to self."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def judge(self, context: GateContext) -> Verdict:
        try:
            regions = markers.parse(context.solution, context.backend.comment)
        except BenchproofError as exc:
            return self.undecided(SkipReason.ARTIFACT_ABSENT, f"unreadable solution: {exc}")

        spec = regions["spec"].text
        found = [marker for marker in UNFINISHED if marker in spec]
        if found:
            return self.failed(
                f"the specification still contains {', '.join(found)}", markers=found
            )
        return self.passed("no unfinished-work markers in the specification")
```

That is the whole file in `examples/plugin/`, and it is deliberately trivial: what the
example is about is the shape, not the check.

| declaration | used for |
| --- | --- |
| `id` | the registry name, the key in `manifest.json`, and `--only` / `--waive` |
| `title` | the column heading in reports |
| `rationale` | what this gate would catch, shown by `benchproofer catalog gates` |
| `level` | `Level.ORACLE` if you need to run the benchmark's own tests |
| `sources` | bundle-relative artifacts whose digests are recorded on the verdict |

Write `rationale` as what the gate catches, not what it checks. A reader deciding whether
to trust a corpus is asking what was ruled out.

## Report absence as absence

The verdict constructors exist so that the record distinguishes cases a boolean cannot:

| constructor | status | means |
| --- | --- | --- |
| `self.passed(...)` | `pass` | the check ran and the bundle is fine |
| `self.failed(...)` | `fail` | the check ran and the bundle is wrong |
| `self.undecided(reason, ...)` | `skip` | the check did not run, and here is the reason |
| `self.timed_out(...)` | `timeout` | the check ran out of budget |
| `self.errored(...)` | `error` | your own code broke |
| `self.weakness(context, ...)` | depends | the specification admits something it should not |

`self.failed` is a claim about the artifact. Use it only when the finding is established
from what you read. Everything you are unsure about is `self.undecided` with a
`SkipReason`:

| reason | for |
| --- | --- |
| `NOT_APPLICABLE` | this question does not arise for this task |
| `ARTIFACT_ABSENT` | the file you needed cannot be read, which no repair is sent for; a file the author's bundle should ship and lacks is a failure instead, which the repair writes |
| `TOOLCHAIN_ABSENT` | the verifier or tool you needed is not installed |
| `ORACLE_UNAVAILABLE` | the benchmark's own check cannot run here |
| `INCONCLUSIVE` | the check ran, and its result does not support the conclusion |

Only `NOT_APPLICABLE` is compatible with certification. The rest make the bundle
`incomplete`, which is the honest outcome for a question nobody decided.

Two conveniences on top of that:

* **`self.weakness(context, ...)`** reports that the checker accepted something it should
  have rejected. Under a prover that is a proof of weakness and becomes a `fail`; under
  a falsifier it becomes `INCONCLUSIVE`, because no counterexample within a budget is not
  a demonstration that none exists. Use it instead of `self.failed` whenever your finding
  is "the checker did not reject this".
* **`self.needs_verified_base(context)`** returns a skip verdict when the shipped
  implementation does not itself verify, and `None` otherwise. Any gate that corrupts or
  swaps the implementation and reads the rejection as strength has to call it first:
  if the shipped implementation is rejected, every variant of it is too, and the
  measurement would report strength that was never demonstrated.

```python
        blocked = self.needs_verified_base(context)
        if blocked is not None:
            return blocked
```

You never write `self.errored` in the normal path. `Gate.run` traps any exception and
records it as `error`, because a crashed gate is Benchproofer's problem and filing it as
a finding would put Benchproofer's defect on the artifact's record. Raise `GateError`
when your check cannot be performed and you have nothing useful to say about why.

## What the context gives you

`GateContext` is everything a gate may look at. It reaches for nothing global, so a
caller can judge a bundle with another backend instance or a stub oracle.

| member | is |
| --- | --- |
| `context.bundle` | the bundle: `solution()`, `twins()`, `battery()`, `write_evidence()` |
| `context.task` | the frozen task, loaded once |
| `context.solution` | the solution file, read once |
| `context.backend` | the backend, for `comment`, `same_spec()`, `kind` |
| `context.check(source, slot)` | run the checker over a variant, in a scratch dir |
| `context.base_check()` | the checker's verdict about the shipped solution, cached |
| `context.oracle()` | the oracle the task declares |
| `context.settings` | budgets and thresholds |

Use `context.base_check()` rather than checking the solution yourself. It is shared
across gates, so the verifier runs once for all of them instead of once each.

Write anything a reviewer would want to re-read with `context.bundle.write_evidence(...)`
and list the returned path under `evidence=[...]`. A verdict that says a mutant survived
is worth more when the file next to it says which mutants there were.

## Register it

```toml
[project.entry-points."benchproofer.gates"]
"spec.no_todo" = "my_package.gate:NoTodoGate"
```

```bash
pip install -e .
benchproofer catalog gates
benchproofer check my-suite --only spec.no_todo
```

Every registered gate runs on every bundle `benchproofer check` visits, and its verdict
is recorded and reported. It does not join the required set: that set is fixed in
`benchproofer/pipeline/adjudicate.py`, so "certified" means the same thing in a corpus
with your gate installed as in one without it. Reports show your verdict; certification
ignores it.

If your gate belongs in the required set, that is a change to Benchproofer rather than a
plugin. Open an issue first: the argument to make is that a bundle passing the current
seventeen gates can still be unsound in the way your gate catches.

## Test it

Two kinds of test are worth writing, and neither needs a language model:

* **A bundle it should reject**, so you know the gate can fail. A gate that passes
  everything is worse than no gate, and this is the test people skip.
* **A bundle whose artifact is missing**, so you know the absence is reported as
  `skip` with a reason rather than as a pass.

The packaged fixtures give you a real bundle to judge, with no network and no language
model. Stage one, edit the region you care about, and run the gate over it:

```python
from pathlib import Path

from benchproofer.config import Settings
from benchproofer.core import markers
from benchproofer.core.verdict import Status
from benchproofer.gates.base import GateContext
from benchproofer.registries import BACKENDS
from benchproofer.smoke import fixtures
from benchproofer.util.fsio import write_text

from my_package.gate import NoTodoGate


def _context(tmp_path: Path) -> GateContext:
    settings = Settings(
        bundle_root=tmp_path / "bundles", cache_dir=tmp_path / "cache", offline=True
    )
    target = fixtures.fixture("coin-change-sound")
    task = fixtures.tasks(settings)[target.task_id]
    return GateContext(
        bundle=fixtures.stage(target, task, settings),
        backend=BACKENDS.get(target.backend),
        settings=settings,
    )


def test_passes_a_finished_specification(tmp_path: Path) -> None:
    verdict = NoTodoGate().run(_context(tmp_path))
    assert verdict.status is Status.PASS
    assert verdict.judge_digest and verdict.tool_version


def test_reports_an_unfinished_specification(tmp_path: Path) -> None:
    context = _context(tmp_path)
    unfinished = markers.replace_region(
        context.bundle.solution(),
        context.backend.comment,
        "spec",
        "# TODO: state the postcondition",
    )
    write_text(context.bundle.solution_path, unfinished)

    # A context caches the file it read, so judge the edited bundle through a fresh one.
    edited = GateContext(
        bundle=context.bundle, backend=context.backend, settings=context.settings
    )
    verdict = NoTodoGate().run(edited)
    assert verdict.status is Status.FAIL
    assert "TODO" in verdict.summary
```

Call `run()` rather than `judge()`. It is the recorded path: it stamps the judge digest
and the Benchproofer version, applies waivers, and traps exceptions, so a test through
`run()` exercises what `manifest.json` will actually contain.

The `gates` smoke group judges the three packaged fixture bundles, one certified, one
incomplete, one rejected, and checks that no gate errored and that every verdict carries
a judge digest. Your gate is included in that once installed:

```bash
benchproofer smoke gates
```

## Checklist

* `id` is dotted, stable, and namespaced by what it judges.
* `rationale` says what is caught, in one sentence.
* Every path returns a verdict: no exception escapes on purpose, no `None`.
* `self.failed` only where the finding is established; otherwise `undecided` with a
  reason.
* A finding of the form "the checker accepted this" goes through `self.weakness`.
* A gate that measures strength calls `needs_verified_base` first.
* `sources` names the artifacts you read, so the verdict records their digests.
* There is a test proving the gate can fail.
