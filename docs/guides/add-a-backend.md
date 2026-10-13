# Add a backend

A backend is a thin adapter around one checker. It decides exactly one question, "does
this file satisfy its own specification", and declares enough about itself that the rest
of Benchproofer can treat the verdict correctly.

Everything else has a working default. A backend that wraps a command-line verifier is
usually under a hundred lines; `benchproofer/backends/smt.py` is the shortest one that
ships.

## Declare what you are

```python
from pathlib import Path
from typing import ClassVar

from benchproofer.backends.base import Backend, BackendKind, CheckResult


class MyBackend(Backend):
    """Verify a Whatever program against the contracts it declares."""

    name: ClassVar[str] = "whatever"
    language: ClassVar[str] = "Whatever"
    extension: ClassVar[str] = ".wtv"
    comment: ClassVar[str] = "--"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    proof_carrying: ClassVar[bool] = False
    summary: ClassVar[str] = "the Whatever verifier, 2.x"
    banned_tokens: ClassVar[tuple[str, ...]] = ("assume ", "trust_me")
    assumption_tokens: ClassVar[tuple[str, ...]] = ("opaque ",)
```

| declaration | why Benchproofer needs it |
| --- | --- |
| `comment` | marker sentinels are written with your line-comment token |
| `extension` | names the solution file, so `solution.wtv` is found |
| `kind` | whether acceptance is a proof or a failed search |
| `proof_carrying` | whether the file contains a proof the checker replays |
| `banned_tokens` | constructs that discharge an obligation without establishing it |
| `assumption_tokens` | constructs that represent a callee nobody is going to verify |
| `inert_strings` | whether the checker reads nothing inside a Python string literal |
| `proof_tokens` | words that introduce the claim a replayed proof proves |
| `allowed_imports` | what a solution may reference; empty means unrestricted |

`kind` is the one to get right. Under `PROVER`, a checker accepting a wrong
implementation is a demonstration that the specification is too weak, and gates report it
as a finding. Under `FALSIFIER`, the same observation only means no counterexample turned
up inside the budget, and the same gates record it as undecided. Declaring a bounded
search as a prover manufactures findings out of a slow machine. See
[Backends](../backends.md#provers-and-falsifiers-are-not-interchangeable).

`banned_tokens` is where you list your language's escape hatches: Dafny's `assume`,
Lean's `sorry`, an SMT script asserting a contradiction. `spec.hygiene` (the paper's
hygiene check) masks comment text before scanning, so a solution may discuss `sorry` in
prose and still pass. What matters is what the checker reads. A Python backend whose
checker ignores docstrings and reads a string only as a value sets `inert_strings`, and
string literals are then masked too; leave it off if a string can be something the
checker reads, as CrossHair's docstring contracts are.

`assumption_tokens` is the other list, and the difference is not a matter of severity. An
escape hatch discharges an obligation the file was supposed to establish, and is banned
outright. An assumption represents a callee nobody is going to verify -- a system call,
another subsystem, the standard library -- which is what makes verifying realistic code
possible at all. So Dafny's `{:axiom}` and Lean's `axiom` go here rather than above:
`spec.hygiene` allows them inside the `axioms` region, where they have to name the callee
they represent, and `spec.axioms_grounded`, part of the paper's axiom-soundness gate,
then runs the bundle's `axioms.py` against that callee in the benchmark's own
environment. Leave the tuple empty if your language has no such construct; a backend
whose specifications are ordinary code, like the Python ones, writes the model itself in
the `axioms` region and needs no token for it.

`proof_tokens` matters if your checker reports whether the file elaborated rather than
whether a named method met its contract. Lean is the example: `lean solution.lean` exits
zero on a file whose only theorem is `theorem nothing : True := by trivial`, and every
gate downstream would read that exit code as a proof about the implementation. So list the
words that introduce a claim -- `theorem`, `lemma`, Velvet's `prove_correct` -- and
`spec.hygiene` then requires the `proof` region to state one and requires its statement to
name what the `spec` and `impl` regions declare. Leave the tuple empty if your checker
attaches the obligation to the method itself, as Dafny and Nagini do, where there is no
separate claim to get wrong.

`allowed_imports` is worth filling in if your checker reads a language with a package
index behind it. `spec.hygiene` rejects a solution that imports anything else, and the
drafting session is told the list in the same breath as the way around it, so a task
whose golden patch reaches for the clock or a source of randomness is formalized by
assuming that callee rather than by a redraft attempt the gate was always going to
reject.

## Implement `check`

One method, three outcomes, and the third is the one that keeps Benchproofer honest:

```python
    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        result = run((str(executable), "verify", str(path)), cwd=workdir, timeout_s=timeout_s + 30)

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if _PARSE_ERROR.search(result.output):
            return CheckResult.malformed(_first_error(result.output), output=result.tail())
        if _ACCEPTED.search(result.output):
            return CheckResult.ok("obligations discharged", output=result.tail())
        if _REJECTED.search(result.output):
            return CheckResult.no(_first_error(result.output), output=result.tail())
        return CheckResult.unknown(f"verifier exited {result.returncode}", output=result.tail())
```

| constructor | means | when |
| --- | --- | --- |
| `CheckResult.ok` | verified | the checker accepted the file |
| `CheckResult.no` | refuted | the checker reasoned about it and rejected it |
| `CheckResult.malformed` | refuted, not well formed | rejected before reasoning: a syntax or resolution error |
| `CheckResult.unknown` | undecided | a timeout, a crash, a solver that gave up, or output you cannot classify |

Three rules follow from that table:

* **Never map an unrecognized outcome to `no`.** `unknown` is not a synonym for refuted.
  A gate that reads a rejection as evidence of specification strength would otherwise
  count a crashed solver as a proof, which is how load on a machine turns into apparent
  defects in artifacts.
* **Distinguish malformed from refuted.** A file the checker could not parse says nothing
  about the specification, so `spec.strength.mutation` (the mutation check) sets such
  mutants aside as not programs, and its verdict is not applicable when every mutant is
  one. It can only do that if you say so.
* **Set `timed_out` when you time out.** It is what separates "the checker said no" from
  "the checker gave no verdict" in the record.

Do not raise on a missing executable either. `CheckResult.unknown("whatever not found")`
is right: the gate then reports that nothing was decided, rather than crashing the run.

`benchproofer.util.proc.run` handles the process side, including killing a hung process
group and clipping unbounded output. `result.tail()` is the excerpt to attach: whatever
you put in `CheckResult.output` is what `spec.verifies` (the paper's verification check)
writes to `evidence/verifies.log`, so a reviewer sees the checker's own words rather than
your summary of them.

## Find your executable

Never hard-code a path. Ask by name and you get, in order: an explicit override, the
repository-local toolchain directory, then `PATH`.

```python
from benchproofer.config import settings
from benchproofer.util.toolchain import find_tool, probe_version


    def executable(self) -> Path | None:
        return find_tool("whatever", toolchain_dir=settings().toolchain_dir)

    def availability(self) -> Availability:
        executable = self.executable()
        if executable is None:
            return Availability.missing(
                "whatever not found", hint="bash scripts/install/whatever.sh"
            )
        return Availability.ok(version=probe_version(executable), detail=str(executable))
```

`find_tool("whatever")` reads `BENCHPROOFER_WHATEVER` for the override, so users get one
without your writing any code for it. The precedence exists so that a checkout with
pinned toolchains is not silently judged by whatever version happens to be on the
machine.

`hint` is printed by `benchproofer doctor`, so make it the exact command that installs
the missing piece.

## Write a template that verifies

`template()` returns a minimal, correct solution file for your language, with a `spec`
region and an `impl` region. It is not decoration: the smoke suite verifies it, mutates
it, and requires the checker to reject at least one mutant. Docs and scaffolding use it
too.

```python
    def template(self) -> str:
        spec = wrap(self.comment, "spec", "...the contract...")
        impl = wrap(self.comment, "impl", "...the body...")
        return f"{spec}\n{impl}\n"
```

Split the file so that the `spec` region holds the contract and nothing else, and the
`impl` region holds only the body. That split is what makes a mutant or a rival unable
to reach the contract it is being judged against, and it is what makes the spec view a
valid declaration on its own. Look at the Dafny template for a worked example: signature
plus `requires`/`ensures` in `spec`, the block that follows in `impl`.

`guidance()` returns instructions injected into the drafting and repair prompts, and into
the auditors that write programs for the checker: attacks, controls and fuzzers. State
the region split, where helpers go, and which constructs are banned. Without it a
language model will write your language the way it writes every other one. The auditors
that judge a role do not get it: they judge by the review's own rules, which are the same
for every backend, so an idiom the drafter was given never becomes a standard the bundle
is held to.

## Register and check it

```toml
[project.entry-points."benchproofer.backends"]
whatever = "my_package.backend:MyBackend"
```

```bash
pip install -e .
benchproofer doctor
benchproofer smoke backends
```

The smoke suite builds its backend cases from the registry, so yours is covered as soon
as it is installed. The case asks the two questions that matter about a checker: does it
accept a correct implementation of your own template, and does it reject a mutant of it.
The second is the one a smoke test usually forgets. A misconfigured toolchain very often
accepts everything, and a suite that only checks the happy path calls that a pass.

Then formalize something real:

```bash
benchproofer ingest humaneval --limit 1
benchproofer formalize humaneval --backend whatever --provider anthropic
benchproofer check humaneval
```

## Checklist

* `kind` reflects what acceptance actually establishes.
* Unclassifiable output, timeouts, and a missing executable all return `unknown`.
* A file the checker could not read returns `malformed`, not `no`.
* `banned_tokens` lists every construct that discharges an obligation by assertion, and
  `assumption_tokens` every construct that represents an unverified callee.
* `proof_tokens` is non-empty if acceptance means the file elaborated rather than that a
  named method met its contract.
* `template()` verifies, and mutating its `impl` region gets a rejection.
* `availability()` gives a hint that names the install command.
* `benchproofer smoke backends` passes.
