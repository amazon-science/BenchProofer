# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Nagini backend.

Nagini verifies annotated Python against Viper, so an accepting verdict is a proof
that the implementation meets its contract for every input, not a report about the
inputs that were tried. Contracts are ordinary Python calls, which keeps a
specification readable by anyone who can read the task::

    def index_of(xs: List[int], target: int) -> int:
        Requires(Acc(list_pred(xs), 1/2))
        Ensures(Acc(list_pred(xs), 1/2))
        Ensures(Result() >= 0 ==> xs[Result()] == target)

The executable is found through `BENCHPROOFER_NAGINI`, then the repository-local
toolchain directory, then `PATH`. ``scripts/install/nagini.sh`` builds a pinned install
in an environment of its own, since Nagini pins its own mypy and Z3 and needs a JVM for
Viper; the JVM and solver inside it are named explicitly, so an unrelated ``Z3_EXE``
cannot change what a verdict was produced by.
"""

from __future__ import annotations

import os
import re
import tokenize
from pathlib import Path
from typing import ClassVar

from ..config import settings
from ..core.markers import ELIDED_REGIONS, kind, mask_comments, parse, python_tokens, wrap
from ..core.plugin import Availability
from ..util.proc import run
from ..util.toolchain import absent, find_tool, probe_version
from .base import Backend, BackendKind, CheckResult
from .support import crash_location, crashed, first_error

__all__ = ["NaginiBackend"]

_INSTALL = "bash scripts/install/nagini.sh"
#: Nagini prints exactly one of these once it has run the verifier.
_VERIFIED = "Verification successful"
_REFUTED = "Verification failed"
#: Printed instead of a verdict when the file never reached the verifier: a syntax
#: error, a missing type annotation, or a construct Viper has no encoding for.
_MALFORMED = re.compile(r"Translation failed|contains inconsistencies")
#: The encodings Nagini's `--float-encoding` accepts. Without one, floating-point
#: operations are uninterpreted, so a specification that states anything about a float
#: result is refuted whatever the implementation does.
FLOAT_ENCODINGS: tuple[str, ...] = ("real", "ieee32")
#: How a file asks for one, on a line of its own outside every region. The encoding is
#: part of what the specification means, so it lives in the file every variant shares
#: rather than in a setting.
_FLOAT_DIRECTIVE = re.compile(
    r"^\s*#\s*benchproofer:float-encoding\s+(?P<value>\S+)\s*$", re.MULTILINE
)
#: Run by Nagini's own interpreter in place of its launcher; see `_launcher`.
_DRIVER = Path(__file__).with_name("_nagini_driver.py")
#: A comment that tells mypy to ignore a line, in every spelling mypy reads, with the
#: error codes it names, if any.
_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore\b(?P<codes>\[[^\]]*\])?")
#: The error codes a `# type: ignore` may name here; see `NaginiBackend.problems`.
_IGNORABLE = frozenset({"has-type"})
#: Nagini has no ``--version`` flag, so the install is asked what it holds.
_VERSION = ("-c", "import importlib.metadata as m; print(m.version('nagini'))")


class NaginiBackend(Backend):
    """Verify an annotated Python module against the contracts it declares."""

    name: ClassVar[str] = "nagini"
    language: ClassVar[str] = "Python (Nagini)"
    extension: ClassVar[str] = ".py"
    comment: ClassVar[str] = "#"
    kind: ClassVar[BackendKind] = BackendKind.PROVER
    proof_carrying: ClassVar[bool] = True
    #: Starting a JVM and translating to Viper, measured on the pinned toolchain.
    startup_s: ClassVar[float] = 20.0
    summary: ClassVar[str] = "Nagini verification of annotated Python on Viper"
    #: `Assume` takes a fact for granted; `Refute` claims something is *not* provable,
    #: which no model of a task has a use for. `# type: ignore` is reported by `problems`,
    #: since one spelling of it is allowed.
    banned_tokens: ClassVar[tuple[str, ...]] = ("Assume(", "Refute(")
    #: A `@ContractOnly` function has a contract and no body, which Viper takes on trust.
    #: The bare name also matches a qualified spelling.
    assumption_tokens: ClassVar[tuple[str, ...]] = ("ContractOnly",)
    #: A string is a value to Nagini, never a contract.
    inert_strings: ClassVar[bool] = True
    #: `MustTerminate` in the entry contract makes `Ensures` a claim about every run, not
    #: only those that return; `spec.hygiene` fails a spec region without it.
    termination_tokens: ClassVar[tuple[str, ...]] = ("MustTerminate",)
    #: A solution is a closed module: the contract library, and type names.
    allowed_imports: ClassVar[tuple[str, ...]] = ("typing", "nagini_contracts")
    #: The contracts, loop annotations and specification decorators. An
    #: `Invariant(Forall(...))` with its triggers runs over several lines, which is why the
    #: view that drops them counts brackets rather than lines.
    annotation_tokens: ClassVar[tuple[str, ...]] = (
        "Requires(",
        "Ensures(",
        "Exsures(",
        "Invariant(",
        "Assert(",
        "Fold(",
        "Unfold(",
        "@Pure",
        "@ContractOnly",
        "@Predicate",
        "@GhostReturns",
    )
    #: Viper's own values, which `nagini_contracts` exposes to Python but no interpreter
    #: in a task's image implements. Annotations are not listed, since a Python copy
    #: drops them and leaves runnable code. Each is matched as a name
    #: (`core.differential.provenance`).
    foreign_tokens: ClassVar[tuple[str, ...]] = ("PSeq", "PSet", "PMap", "ToSeq")
    #: A loop's invariants, the assertions that state a fact the next step needs, and the
    #: folding of predicates are the proof, written inside the method body; what the body
    #: computes is the rest.
    proof_annotations: ClassVar[tuple[str, ...]] = ("Invariant", "Assert", "Fold", "Unfold")
    #: A probe `Assert`s what the postcondition promises of each call (`probe_placement`).
    probe_claims: ClassVar[tuple[str, ...]] = ("Assert",)
    #: Nagini's errors read `solution.py:12:8:12:30: error: ...`, and Viper places each at
    #: the construct that failed: an `Ensures`, an `Invariant`, an `Assert`, a call.
    refusal_site: ClassVar[str] = r"^\s*\S+?\.py:(?P<line>\d+):\d+(?::\d+:\d+)?: error:"
    refused_cases: ClassVar[tuple[str, ...]] = (
        "**Malformed `# type:` comment.** A type comment attaches only to an "
        "assignment/with/for target -- never to a bare `return []`, and the text must be "
        "exactly `# type: T` with no trailing parenthetical. Bind a typed local first "
        "(`empty = []  # type: List[int]`, then `return empty`). A name gets one type "
        "comment, on its first assignment: a second one is a redefinition (`no-redef`).",
        "**Forward-append against a front-recursive `@Pure` fold.** Needs an "
        "`f(a+b)==f(a)+f(b)` lemma the verifier will not discharge on its own. Prefer a "
        "branch reorder or a local-variable reshape over flipping the loop's direction.",
    )
    #: The implementation region is the specified method's body, so a probe there calls
    #: the method from inside itself, which Nagini refuses on the method's `MustTerminate`
    #: measure ("Obligation leak check failed") before consulting the precondition. A
    #: function of its own after the body carries no obligation, so the call is judged on
    #: the precondition alone; `verified-swebench`'s `pbt_author.md` asks for a self-call
    #: instead. It is asked for after the `end impl` line, where a model writes one, and
    #: `variant.assemble` carries it into the region.
    probe_placement: ClassVar[str] = (
        "* Put the probe **after** the reference implementation's body, as a function of\n"
        "  its own at the top level: `def admissibility_probe() -> None:`, with no\n"
        "  contract, calling the specified function at literal inputs and `Assert`-ing\n"
        "  what its postcondition promises of each result. Write it after the `end impl`\n"
        "  line, in the same fenced block: Benchproofer moves a top-level function\n"
        "  written there into the `impl` region, which is what the checker reads. Nagini\n"
        "  checks every function in the file, so it is reached. Not inside the specified\n"
        "  function: a call there is a recursive call, and Nagini refuses it on the\n"
        "  termination measure whatever the specification says."
    )

    def executable(self) -> Path | None:
        """Locate the Nagini launcher."""
        return find_tool("nagini", toolchain_dir=settings().toolchain_dir)

    def availability(self) -> Availability:
        """Report whether Nagini can run here."""
        executable = self.executable()
        if executable is None:
            return Availability.missing(
                absent("nagini", toolchain_dir=settings().toolchain_dir), hint=_INSTALL
            )
        probe = probe_version(_interpreter(executable), _VERSION)
        if not probe.answered:
            return Availability.missing(
                f"nagini at {executable} reported no version: {probe.said}", hint=_INSTALL
            )
        if "JAVA_HOME" not in _environment(executable) and not os.environ.get("JAVA_HOME"):
            return Availability.missing(
                "nagini is installed but Viper has no JVM to run on: no JDK inside the "
                "install and no JAVA_HOME set",
                hint=_INSTALL,
            )
        return Availability.ok(version=probe.version, detail=str(executable))

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        """Verify one annotated module."""
        executable = self.executable()
        if executable is None:
            return CheckResult.unknown(absent("nagini", toolchain_dir=settings().toolchain_dir))

        workdir.mkdir(parents=True, exist_ok=True)
        path = workdir / self.solution_filename()
        path.write_text(source, encoding="utf-8")

        encoding = float_encoding(source)
        if encoding is not None and encoding not in FLOAT_ENCODINGS:
            return CheckResult.malformed(
                f"the file asks for float encoding {encoding!r}; Nagini has "
                + " and ".join(repr(value) for value in FLOAT_ENCODINGS)
            )
        flags = ("--float-encoding", encoding) if encoding else ()
        # In the scratch directory, where mypy, which Nagini runs first, leaves its cache.
        result = run(
            (*_launcher(executable), "--ide-mode", *flags, path.name),
            cwd=workdir,
            env=_environment(executable),
            timeout_s=timeout_s,
        )
        output = result.output

        if result.timed_out:
            return CheckResult.unknown(
                f"no verdict within {timeout_s:.0f}s",
                duration_s=result.duration_s,
                output=result.tail(),
                timed_out=True,
            )
        if _VERIFIED in output:
            return CheckResult.ok(
                "all obligations discharged",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if _MALFORMED.search(output):
            return CheckResult.malformed(
                first_error(output, "error:"),
                duration_s=result.duration_s,
                output=result.tail(),
            )
        if _REFUTED in output:
            return CheckResult.no(
                first_error(output, "error:"),
                duration_s=result.duration_s,
                output=result.tail(),
            )
        # Last, so that a verdict Nagini printed before dying is still the verdict.
        crash = crashed(output)
        if crash is None:
            return CheckResult.unknown(
                f"nagini exited {result.returncode} without a verdict",
                duration_s=result.duration_s,
                output=result.tail(),
            )
        # The line the driver printed ahead of the traceback is the only position in the
        # file the output has, and the tail may have cut it off.
        where = crash_location(output)
        tail = result.tail()
        return CheckResult.unknown(
            f"nagini crashed: {crash}" + (f"; {where}" if where else ""),
            duration_s=result.duration_s,
            output=f"{where}\n{tail}" if where and where not in tail else tail,
        )

    def template(self) -> str:
        """A contract-carrying function whose body lives in its own region.

        The signature and its `Requires`/`Ensures` calls are the specification and the
        statements that follow are the implementation, so a mutant or a rival never
        reaches the contract it is judged against, and the spec view still parses.

        The postcondition is relational -- what the result is bigger than, and which input it
        is -- rather than an equation against a term. A drafter copies this shape, and an
        equation against a term the view defines is a specification a wrong implementation
        satisfies by returning that term (`audit.no_disclosure`).
        """
        header = (
            "from nagini_contracts.contracts import *\n"
            "from nagini_contracts.obligations import MustTerminate"
        )
        spec = wrap(
            self.comment,
            "spec",
            "def larger(a: int, b: int) -> int:\n"
            "    Requires(MustTerminate(2))\n"
            "    Ensures(Result() >= a and Result() >= b)\n"
            "    Ensures(Result() == a or Result() == b)",
        )
        impl = wrap(
            self.comment,
            "impl",
            "    gap = a - b\n    if gap >= 1:\n        return a\n    return b",
        )
        return f"{header}\n\n{spec}\n{impl}\n"

    def escapes(self) -> tuple[str, ...]:
        """The banned and assumption tokens, and a `# type: ignore` a variant writes.

        A variant has no use for one it did not inherit: a rival's implementation is
        typed as the reference implementation is, so a type error silenced there is one the
        translation would otherwise have refused.
        """
        return (*super().escapes(), "# type: ignore")

    def problems(self, source: str) -> list[str]:
        """What `spec.hygiene` reports about the file's type-check silencers and floats.

        A `# type: ignore`, in any spelling mypy reads, silences the type check the
        translation is built on. The one allowed is `# type: ignore[has-type]`, for a name
        whose type mypy cannot determine where it is read, such as an attribute a contract
        of `__init__` reads before the body assigns it, which hides no error.

        A float encoding is reported when Nagini lacks it, when the file declares two, when
        the file uses no `float`, since a declaration nothing honors is a false promise
        about how the specification reads floats, and when it sits inside a region a
        variant rewrites, where a rival could be judged under another encoding.
        """
        problems = [
            f"{written!r} at line {number} silences the type check the translation is "
            "built on; the one allowed is `# type: ignore[has-type]`, for a name whose "
            "type mypy cannot determine where it is read"
            for number, written in _silencers(source)
        ]
        found = list(_FLOAT_DIRECTIVE.finditer(source))
        if not found:
            return problems
        value = found[0].group("value")
        if value not in FLOAT_ENCODINGS:
            problems.append(f"float encoding {value!r} is not one Nagini has")
        if len({match.group("value") for match in found}) > 1:
            problems.append("the file declares more than one float encoding")
        if not re.search(r"\bfloat\b", mask_comments(source, self.comment)):
            problems.append(f"the file declares float encoding {value!r} but uses no float")
        regions = parse(source, self.comment, required=())
        elided = [region for name, region in regions.items() if kind(name) in ELIDED_REGIONS]
        lines = {match.group(0).strip() for match in found}
        if any(line in region.text for region in elided for line in lines):
            problems.append(
                "the float-encoding line sits inside a region a variant (a copy of the "
                "solution file with some regions replaced) rewrites, so a rival could be "
                "judged under another encoding than the solution file"
            )
        return problems

    def guidance(self) -> str:
        """Nagini-specific instructions for the formalization stage."""
        return (
            "Write one self-contained Python module that imports Nagini's contracts "
            "with `from nagini_contracts.contracts import *` and its termination "
            "obligation with `from nagini_contracts.obligations import MustTerminate`. "
            "The spec region holds the entry function's def line and its "
            "Requires/Ensures calls and nothing else; the impl region holds the "
            "statements of that body, including whatever Invariant calls the proof "
            "needs. Each further function the fix changes is a def of its own in the "
            "same shape, in regions numbered from 2 (`spec.2` over its def line and "
            "contract, `impl.2` over its body), with its own termination obligation. "
            "The number in `MustTerminate` is a level, not a measure: `2` unless the "
            "function calls another obligated one, whose level must be strictly lower. "
            "Helper functions, predicates and lemmas go in the helpers region, "
            "and an unchanged callee's model or its @ContractOnly axiom goes in the axioms "
            "region. "
            "The entry contract must include `Requires(MustTerminate(2))`, because "
            "Nagini's postconditions otherwise hold only of the runs that return: "
            "every loop in the body then needs an `Invariant(MustTerminate(<bound>))` "
            "whose bound strictly decreases and stays positive, such as "
            "`Invariant(MustTerminate(n - i + 1))`. Level 2 rather than 1 leaves room "
            "beneath it for a helper's own obligation and for the sequence constructor "
            "a body calls. "
            "Annotate every parameter and return type: Nagini rejects a module in "
            "which any type is unknown. Give a local its `# type:` comment once, on its "
            "first assignment: a second one on the same name is a redefinition the type "
            "check refuses before Nagini reads a contract (`no-redef`). "
            "Write no `# type: ignore`, which silences the type check the translation is "
            "built on; the one allowed is `# type: ignore[has-type]`, on a line where the "
            "type check cannot determine the type of a name it reads (`has-type`). "
            "Model a sequence as `PSeq` and a set as `PSet`, "
            "pure values that need no permission predicate and that nothing can modify, "
            "so an obligation written over one says what the caller passed. Build an "
            "empty one from a value of its element type: `PSeq(x).take(0)`, or "
            "`s.take(0)` for a sequence `s` of that type at hand, is the empty sequence, "
            "and `PSet(x) - PSet(x)` the empty set. Those stand anywhere -- a return, a "
            "comparison, a contract, and the body of a `@Pure` function, which has no "
            "locals once it has a `Decreases` (below). Never write `PSeq[T]()`, which "
            "Nagini rejects in a `@Pure` function (`purity.violated`) and a method body "
            "does not know is empty, and never `return PSet()` or a bare `PSeq()` "
            "anywhere but a typed local: Nagini cannot tell its element type and refuses "
            "the file "
            "(`generic.constructor.without.type`). In a method body a typed local, "
            "`PSeq()` under a `# type: PSeq[int]` comment, is the empty one too. Bind a "
            "concatenation to a typed local before wrapping it, `joined = a + b  # type: "
            "PSeq[int]` and then `rows + PSeq(joined)` -- or, in a `@Pure` function, "
            "call a `@Pure` helper that returns `a + b` -- since `rows + PSeq(a + b)` "
            "over a sequence of sequences crashes the translator. However it was built, "
            "say a sequence is empty with `len(s) == 0` -- `PSeq(v)` is a "
            "singleton and `+` concatenates, and a loop that appends with "
            "`out = out + PSeq(v)` then has to assert the new length, the new element, "
            "and that the earlier elements equal the value before the append, or its "
            "invariant is not preserved. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §0.5.
            "Where the behavior is about storage -- the fixed code modifies an argument in "
            "place, or keeps a copy that must not share storage with one -- state "
            "ownership per location, with permissions on a `List`, a `Dict` or a class "
            "whose fields are the locations, never through the result's Python type. An "
            "argument the operation does not modify is required and ensured at a "
            "fractional permission, `Acc(list_pred(xs), 1/2)`, and only one it genuinely "
            "modifies at full permission, with the post-state stated exactly against "
            "`Old(xs[i])`: a full-permission argument it only reads lets a wrong "
            "implementation overwrite it and still verify. A copy is ensured at full "
            "permission at every level the caller can still write -- its container and "
            "the location of each element -- so, with the argument keeping its ensured "
            "share, a result that shares any of those locations does not verify. The "
            "permission goes in an `Invariant` ahead of every invariant that reads the "
            "container, `len(xs)` included. "
            "Every `s = s + PSeq(v)` is an append that needs its own assertions, in a loop "
            "or not -- one after the loop included, or what was proved of `s` before it is "
            "lost: bind the old value first (`last = s  # type: PSeq[int]`), and after the "
            "append assert `len(s) == len(last) + 1`, `s[len(last)] == v`, and "
            "`Forall(int, lambda k: (Implies(0 <= k and k < len(last), s[k] == last[k]), "
            "[[s[k]]]))`. "
            "Give every `Forall` an explicit trigger, as in `Forall(int, lambda k: "
            "(Implies(0 <= k and k < len(xs), xs[k] == 0), [[xs[k]]]))`, and keep index "
            "arithmetic linear: a bound or an index that multiplies or divides two "
            "variables is nonlinear integer arithmetic, which the solver does not come "
            "back from, so a matrix is a `PSeq` of rows rather than one flat `PSeq` of "
            "length `rows * cols`. A file that times out establishes nothing at all. "
            "Do not use Assume or Refute. "
            "A `@Pure` function whose `Ensures` calls the function itself needs a "
            "`Decreases(...)` clause, or Viper refuses the file as inconsistent; put it "
            "after the function's `Requires` calls and before its first `Ensures`, which "
            "is the only place Nagini accepts one (`invalid.contract.position`). "
            "A `@Pure` function with a `Decreases` clause has no local variables: "
            "Nagini cannot track the measure through a local assignment, even `c = s[0]`, and "
            "reports that the function might not terminate. Write its body as `if` and "
            "`return`, each value spelled out where it is used. Every `@Pure` function "
            "it calls needs a `Decreases` of its own too -- `Decreases(0)` for one that "
            "does not recurse -- or the call fails the same check. A `@Pure` function "
            "states its termination with `Decreases`, never with `MustTerminate`, which "
            "Nagini refuses there (`invalid.contract.position`). "
            "Write every contract in the order Requires, Decreases, Ensures, Exsures, "
            "with each `Exsures` after every `Ensures`: an `Ensures` after an `Exsures` "
            "is refused the same way. Give each exception class one `Exsures`, its "
            "conditions disjoined -- `Exsures(NotADigit, c < 48 or c > 57)` -- since two "
            "for the same class are conjoined, and a raise that meets one fails the other. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §3.
            "Index recursion over a sequence does not unfold on its own. For a `@Pure` "
            "`f(s, n)` defined through `f(s, n - 1)`, Nagini refutes the step "
            "`f(s, i + 1) == g(s[i], f(s, i))` until the body instance is asserted with "
            "the argument spelled `(i + 1) - 1` -- "
            "`Assert(f(s, i + 1) == g(s[(i + 1) - 1], f(s, (i + 1) - 1)))` -- and then "
            "proves it, so a loop whose invariant is `acc == f(s, i)` asserts that "
            "before it updates `acc`. A lemma, a `@Pure` function that returns `True`, "
            "proves its `Ensures` only where one unfolding of the functions it names "
            "is enough to prove it: write none whose `Ensures` needs induction, and drop a "
            "postcondition the others already imply rather than prove it. A function that "
            "builds a collection returns a `List`, and its contract speaks of what it "
            "returns through `ToSeq`, each side built from the inputs it was given: "
            "`Ensures(ToSeq(Result()) == ToSeq(xs) + ToSeq(ys))`, built in a loop that "
            "appends, whose invariant relates it to the input's own prefix, "
            "`ToSeq(acc) == ToSeq(xs).take(i)`, asserting "
            "`ToSeq(xs).take(i + 1).take(i) == ToSeq(xs).take(i)` and "
            "`ToSeq(xs).take(i + 1)[i] == ToSeq(xs)[i]` before the update and "
            "`ToSeq(xs).take(len(xs)) == ToSeq(xs)` after the loop. Sequence folds use "
            "front-recursion: a fold specification like "
            "`escaped(s) == entity(s[0]) + escaped(s.drop(1))`, a front-recursive `@Pure` "
            "function over `PSeq` stated as `Ensures(ToSeq(Result()) == "
            "escaped(ToSeq(xs)))`, gives one unfolding per loop step and verifies, paired "
            "with a matching loop in the implementation, one that runs from the end and "
            "puts each element in front: its invariant is `ToSeq(acc) == "
            "escaped(ToSeq(xs).drop(i))`, asserting `ToSeq(xs).drop(i - 1)[0] == xs[i - 1]` "
            "and `ToSeq(xs).drop(i - 1).drop(1) == ToSeq(xs).drop(i)` before the update "
            "and `ToSeq(xs).drop(0) == ToSeq(xs)` after the loop. This is the pattern for a "
            "result that is the per-element expansion of the input, and such a fold is the "
            "specification where it defines a notion the task uses -- what is kept, what is "
            "dropped, in which order -- rather than the steps the fix adds. Do not state the "
            "result as a membership `Forall` over a recursive definition, which does not "
            "prove without induction. "
            "Return from each branch rather than first assigning a result "
            "that every path then reassigns: nothing can observe that first value, so "
            "each change to it is a mutant no specification refutes. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §2.
            "A contract may call only `@Pure` functions: any other call inside a "
            "`Requires` or an `Ensures` is `purity.violated`. So an axiom a contract uses "
            "is `@Pure @ContractOnly`, and where one changed function's contract speaks "
            "of what another changed function returns, both speak of a `@Pure` predicate "
            "that *relates* that function's inputs to its result -- the callee's "
            "`Ensures(folded(ToSeq(xs), Result()))` -- rather than calling the callee, and "
            "rather than a `@Pure` function computing the result, which the callee then "
            "satisfies by returning it. "
            "`==` on a value typed `Optional[...]` is a call to its `__eq__`, whose "
            "precondition is that the value is not `None`, so Nagini refuses it "
            '("The precondition of Result() == ... might not hold"). Test `is None` '
            "first and put a value known not to be `None` on the left: "
            "`Implies(v is not None, Result() is not None and Result() == f(v))`, with "
            "`Implies(v is None, Result() is None)` beside it. Give a "
            "local a loop assigns its first value before the outermost loop, not inside a "
            "nested one: Nagini adds a type invariant for it that then does not hold on "
            "entry. "
            # From `verified-swebench`'s `prompts/nagini/eval_mode_3.md`, step (2), and
            # `spec_guide.md` §2, its `str` row.
            "Write the model at whatever abstraction lets you state it cleanly -- "
            "strings as code-point lists, opaque handles, int-scaled values. A `str` the "
            "fix reads or changes the text of is a `PSeq[int]` of code points (`str` "
            "indexing crashes Nagini), each a Unicode scalar value, 0 to 0x10FFFF outside "
            "0xD800 to 0xDFFF: the precondition requires that of each string the model takes "
            "as input, so the model admits no lone surrogate, which no UTF-8 text, Python "
            "source included, can hold. An opaque handle represents a string only where "
            "neither the fix nor the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test "
            "patch adds or edits depend on its text, and two values those tests can tell "
            "apart -- a label and the key derived from it -- never share one. A mapping whose "
            "keys or values the fix reads or those tests check is modeled with its keys and "
            "its values, as two `PSeq`s of one length, say, and not with its values alone. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §3. What is modeled
            # and what is an axiom is the rule `Backend.callees` gives beside this guidance.
            "A model of an unchanged callee is a `@Pure` function with a body. An axiom "
            "that says nothing of its result, so that the golden patch's own body cannot be "
            "proved, is the specification's defect, not a proof the implementation lacks. An "
            "axiom that returns a value is `@Pure @ContractOnly`. One whose "
            "behavior is an effect -- a file it writes, a record it appends to -- is a "
            "`@ContractOnly` method whose `Ensures` states what it changes against "
            "`Old(...)`, so a body that skips the call or makes it twice is seen, and never "
            "a field the implementation sets itself. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §2, its float rows.
            "A `float` where precision IS the behavior is a real Python `float` under an "
            "encoding -- `real`, or `ieee32` for bit-level behavior -- declared on a line "
            "of its own before the first region: `# benchproofer:float-encoding real`. "
            "Do NOT fake it with an int. Interpreted floats are OFF by default (the "
            "'Floating point operations are uninterpreted' warning), so a naive float "
            "specification vacuously fails without that line. "
            # From `verified-swebench`'s `prompts/nagini/spec_guide.md` §2, its raise row.
            "Where the repository raises on an input the precondition would admit -- "
            "the changed function itself or a callee -- either model the raise, with a "
            "user-defined exception class and `Exsures` (an `Exsures` naming a builtin "
            "exception crashes the translator), or write a precondition that excludes "
            "that input: one that admits it promises a result the repository never "
            "returns there, and the conformance check draws it. "
            "Say that a call never returns normally with `Ensures(False)` beside its "
            "`Exsures`, and that a function raises on some inputs with an `Ensures` that "
            "is false on them: an `Exsures` alone says what holds if it raises, and a body "
            "that returns there instead still verifies. Every `Ensures` is vacuous on a run "
            "that raises, so an `Exsures` that depends only on state the body itself can "
            "write -- a field it holds full permission to -- lets a body that sets that "
            "state and raises verify: state its condition over the inputs, or over what an "
            "axiom returns. "
            # From `verified-swebench`'s `prompts/nagini/eval_mode_8.md`, step (3).
            "Do not axiomatize the behavior the fix itself introduces: an axiom represents "
            "its callee exactly as the directive names it, so filtering or mapping "
            "the fix applies to what the callee returns is spelled out in the impl, not "
            "folded into the axiom, which would assume the fix correct. Declare no axiom "
            "for `builtins.bool`: what `bool()` returns is each type's own `__bool__`, so "
            "such an axiom claims something of every type, and a reviewer's fuzzer tries "
            "them; state what the call the changed code makes returns, on the type that "
            "reaches it."
        )


def _launcher(executable: Path) -> tuple[str, ...]:
    """The command that runs Nagini: through `_nagini_driver` where its interpreter is known.

    The driver has to run in Nagini's own environment, so a Nagini found without its
    interpreter beside it runs as it is, and the errors the driver reports stay crashes.
    """
    interpreter = _interpreter(executable)
    if interpreter.is_file():
        return (str(interpreter), str(_DRIVER))
    return (str(executable),)


def _interpreter(executable: Path) -> Path:
    """The Python that owns a Nagini install.

    Nagini is a package, not a standalone binary, so what identifies the version is
    the environment its launcher belongs to.
    """
    return executable.parent / "python"


def _environment(executable: Path) -> dict[str, str]:
    """The JVM and solver that belong to this install, when it carries its own.

    An install built by ``scripts/install/nagini.sh`` holds both, and naming them keeps a
    verdict from depending on the machine's `JAVA_HOME` or `Z3_EXE`. A Nagini found
    anywhere else is left to its environment.
    """
    home = executable.parent.parent
    found: dict[str, str] = {}
    if (home / "lib" / "jvm" / "bin" / "java").is_file():
        found["JAVA_HOME"] = str(home / "lib" / "jvm")
    if (home / "bin" / "z3").is_file():
        found["Z3_EXE"] = str(home / "bin" / "z3")
    return found


def float_encoding(source: str) -> str | None:
    """The float encoding a Nagini file declares, or None when it declares none."""
    found = _FLOAT_DIRECTIVE.search(source)
    return found.group("value") if found else None


def _silencers(source: str) -> list[tuple[int, str]]:
    """Each `# type: ignore` comment that names anything but `_IGNORABLE`, by line.

    Read off the comments Python's tokenizer finds, so one inside a string literal is
    text; source the tokenizer refuses is read line by line, which errs towards reporting.
    """
    tokens = python_tokens(source)
    comments = (
        [(token.start[0], token.string) for token in tokens if token.type == tokenize.COMMENT]
        if tokens is not None
        else list(enumerate(source.splitlines(), start=1))
    )
    found: list[tuple[int, str]] = []
    for number, text in comments:
        for match in _TYPE_IGNORE.finditer(text):
            codes = match.group("codes")
            named = {code.strip() for code in codes[1:-1].split(",")} if codes else set()
            if not named or not named <= _IGNORABLE:
                found.append((number, match.group(0)))
    return found
