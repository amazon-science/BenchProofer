# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Unchanged callees, and the program that grounds them.

A realistic task calls code nobody is going to verify: the standard library, a socket,
another subsystem of the repository. A specification models such a callee where its
checker can state exactly what it computes, and otherwise *assumes* it, and the proof
then holds exactly as far as the model or the assumption does, so each is declared and
then grounded. The declaration is one line of the `axioms` region naming the callee,
`models` on a model's definition::

    # benchproofer:axiom json.loads
    # benchproofer:models posixpath.normpath

The grounding is `axioms.py`, a program the bundle ships that runs in the benchmark's own
environment, exercises the real callee against the model, and says what it covered::

    benchproofer:grounded json.loads 200 inputs drawn from the model's domain
    benchproofer:refuted json.loads loads('1 ') is 1, the model says malformed

Exit zero means every model agreed with its callee. A `refuted` line is a counterexample
observed at run time, which is evidence under any backend. What the program reports is
held to what it ran: Benchproofer records the functions the run calls (`with_calls`) and
reads, for each callee, whether its code ran::

    benchproofer:calls json.loads no its code never ran

The program runs against the base tree, or against the fixed one when an unchanged callee is
defined in a file the fix changes (`against_reference`) or when it asks to on a line of its
own::

    # benchproofer:axioms apply-fix

The rules live here rather than in the gate, because the stage that writes an `axioms.py` and
the gate that judges one have to agree on them exactly.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from ..errors import MarkerError
from ..util.patch import touched_paths
from .differential import inserted
from .markers import BINDS, declarations, parse
from .runnable import quotes_lines

__all__ = [
    "AFTER_REFERENCE",
    "APPLY_FIX",
    "DIRECTIVE",
    "HARNESS",
    "PROTOCOL",
    "QUOTED",
    "Assumption",
    "after_reference",
    "against_reference",
    "axiom_names",
    "callees",
    "calls",
    "declared",
    "declared_in",
    "directive_line",
    "grounded",
    "in_changed_file",
    "refutations",
    "refuted_lines",
    "with_calls",
    "with_declarations",
]

#: The name a bundle's `axioms.py` ships under. Always Python, since it runs where
#: the benchmark's tests run rather than where the checker does.
HARNESS = "axioms.py"

#: An axiom's directive, or a model's.
DIRECTIVE = re.compile(
    r"^\s*(?P<comment>\S{1,4})\s*benchproofer:(?:(?P<modeled>models)|axiom)\s+"
    r"(?P<callee>\S+)\s*$",
)
_GROUNDED = re.compile(r"^\s*benchproofer:grounded\s+(?P<callee>\S+)", re.MULTILINE)
_REFUTED = re.compile(r"^\s*benchproofer:refuted\s+(?P<callee>\S+)", re.MULTILINE)
_REFUTATION = re.compile(r"^\s*benchproofer:refuted\s+\S+.*$", re.MULTILINE)
_CALLS = re.compile(
    r"^benchproofer:calls\s+(?P<callee>\S+)\s+(?P<word>yes|no|unknown)\b[ \t]*(?P<why>.*)$",
    re.MULTILINE,
)
#: The word after `benchproofer:axioms` that asks for the fixed tree.
APPLY_FIX = "apply-fix"
_AFTER_REFERENCE = re.compile(
    rf"^\s*#\s*benchproofer:axioms\s+{re.escape(APPLY_FIX)}\s*$", re.MULTILINE
)

#: What an `axioms.py` has to print, injected verbatim into the prompts that ask for one so
#: that what is requested and what is checked cannot drift apart.
PROTOCOL = """\
Print one line for each callee you exercised:

    benchproofer:grounded <callee> <how many inputs, and how they were drawn>

and one line for each disagreement you found:

    benchproofer:refuted <callee> <the input, what the callee did, what the model says>

Exit zero when every model agreed with the callee it models, and non-zero when any
did not. Print nothing else on a line that starts with `benchproofer:`."""

#: What a prompt tells an `axioms.py` author about the tree the program runs against, for a
#: benchmark whose solution is a patch: elsewhere the tree already holds every callee.
AFTER_REFERENCE = """\
The program runs against the task's tree as the benchmark ships it, before the fix,
unless an unchanged callee is defined in a file the fix changes: the base commit is the
reference only for callees the patch does not touch, so then Benchproofer applies the
golden patch first. If the program needs the fix for anything else -- a callee that only
exists once the fix is applied -- say so on a line of its own and Benchproofer applies
the patch as well:

    # benchproofer:axioms apply-fix"""


@dataclass(frozen=True, slots=True)
class Assumption:
    """One unchanged callee a solution file assumes or models."""

    callee: str
    line: int
    #: Whether the directive is `models`: a definition computing what the callee computes.
    modeled: bool = False


def directive_line(comment: str, callee: str, *, modeled: bool = False) -> str:
    """Render the declaration that ``callee`` is assumed, or modeled."""
    word = "models" if modeled else "axiom"
    return f"{comment} benchproofer:{word} {callee}"


def declared(text: str, comment: str) -> tuple[Assumption, ...]:
    """The assumptions ``text`` declares, in order.

    Callers pass the body of the `axioms` region; a declaration anywhere else is what
    `spec.hygiene` reports.
    """
    found: list[Assumption] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = DIRECTIVE.match(line)
        if match is not None and match.group("comment") == comment:
            found.append(
                Assumption(
                    callee=match.group("callee"),
                    line=number,
                    modeled=match.group("modeled") is not None,
                )
            )
    return tuple(found)


def declared_in(solution: str, comment: str) -> tuple[Assumption, ...]:
    """What ``solution``'s `axioms` region declares (`declared`), empty when it has none.

    Empty, too, when the file's markers cannot be read, which `spec.hygiene` reports.
    """
    try:
        region = parse(solution, comment).get("axioms")
    except MarkerError:
        return ()
    return declared(region.text, comment) if region is not None else ()


def axiom_names(text: str, comment: str) -> set[str]:
    """The names ``text`` declares under an `axiom` directive, before the next directive.

    ``text`` is the body of the `axioms` region, where the declarations a directive marks
    follow it. The checker takes each on trust and cannot evaluate it, and no refutation
    witness may assume a value of it either.
    """
    marked: list[str] = []
    keep = False
    for line in text.splitlines():
        match = DIRECTIVE.match(line)
        if match is not None and match.group("comment") == comment:
            keep = match.group("modeled") is None
        elif keep:
            marked.append(line)
    return declarations("\n".join(marked), comment, opens=BINDS)


def callees(assumptions: tuple[Assumption, ...]) -> tuple[str, ...]:
    """The distinct callees of ``assumptions``, in first-declared order."""
    return tuple(dict.fromkeys(assumption.callee for assumption in assumptions))


def grounded(output: str) -> tuple[str, ...]:
    """The callees a run of `axioms.py` reported as exercised."""
    return tuple(dict.fromkeys(match.group("callee") for match in _GROUNDED.finditer(output)))


def refutations(output: str) -> tuple[str, ...]:
    """The callees a run of `axioms.py` reported as disagreeing with their model."""
    return tuple(dict.fromkeys(match.group("callee") for match in _REFUTED.finditer(output)))


def refuted_lines(output: str) -> tuple[str, ...]:
    """Every refutation a run of `axioms.py` reported, whole, in the order printed.

    Unlike `refutations`, these say on what input and what each side did, which a repair
    needs to tell which part of the assumption is false and whether the program called the
    callee the way the task does.
    """
    return tuple(match.group(0).strip() for match in _REFUTATION.finditer(output))


#: The heading of the declarations Benchproofer quotes into an `axioms.py`.
QUOTED = """\
The declarations of the solution's `axioms` region, which this program grounds, quoted
by Benchproofer so that the model it checks is on record as the one the checker was given."""


def with_declarations(harness: str, region: str, comment: str) -> str:
    """``harness`` with the declarations of ``region`` quoted at its end, unless it has them.

    `spec.axioms_grounded` requires an `axioms.py` to carry every declaration line of the
    region, as code or quoted, which ties the program to the model the checker was given. A
    model asked to copy them reflows them, so the tool writes the quotation itself, after the
    program so that the line numbers its output reports are still the lines the model wrote.

    A quotation the tool wrote of another region is taken out first. A repair that retypes
    an assumption under the same callee leaves `axioms.py` quoting declarations the solution
    no longer has, and kept beside the new ones they would put on record a model the checker
    was never given.
    """
    lines = [*QUOTED.splitlines(), "", *region.strip("\n").splitlines()]
    quoted = "\n".join(f"{comment} {line}".rstrip() for line in lines)
    if quoted in harness:
        return harness
    bare = _unquoted(harness, comment)
    if quotes_lines(bare, region, comment):
        return bare
    return f"{bare.rstrip()}\n\n\n{quoted}\n"


def _unquoted(harness: str, comment: str) -> str:
    """``harness`` less the quotation `with_declarations` wrote: its heading and what follows.

    The quotation is a run of comment lines opening with the heading, so it ends at the
    first line that is not a comment.
    """
    heading = f"{comment} {QUOTED.splitlines()[0]}"
    lines = harness.splitlines()
    if heading not in lines:
        return harness
    start = lines.index(heading)
    end = start
    while end < len(lines) and lines[end].startswith(comment):
        end += 1
    return "\n".join([*lines[:start], *lines[end:]]).rstrip() + "\n"


def after_reference(harness: str) -> bool:
    """True when an `axioms.py` asks to run against the tree with the fix applied."""
    return _AFTER_REFERENCE.search(harness) is not None


def against_reference(harness: str, assumed: Sequence[str], patch: str) -> bool:
    """Whether a grounding program runs against the tree with the golden patch applied.

    When it asks to (`after_reference`), or when an unchanged callee is defined in a file the
    fix changes: at the base commit that callee is the code before the fix, and a program
    exercising it runs into the task's own defect and reports a disagreement no model
    claimed. Whether the fix changes the callee itself is the equivalence auditor's
    separate question.
    """
    return after_reference(harness) or any(in_changed_file(callee, patch) for callee in assumed)


def in_changed_file(callee: str, patch: str) -> bool:
    """Whether ``callee``'s dotted path leads into a Python file ``patch`` writes.

    A prefix of the path read as a module names a file the patch touches, at its root or
    under a directory the package sits in (`src/`, `lib/`): `a.b.c.f` leads into `a/b/c.py`,
    and into `a/b/__init__.py` too.
    """
    parts = callee.split(".")
    modules = ["/".join(parts[:end]) for end in range(1, len(parts) + 1)]
    for path in touched_paths(patch, source_only=True):
        if not path.endswith(".py"):
            continue
        stem = path.removesuffix(".py").removesuffix("/__init__")
        if any(stem == module or stem.endswith(f"/{module}") for module in modules):
            return True
    return False


#: The program Benchproofer runs ahead of `axioms.py`'s own statements, which
#: records the code objects of every function the run calls and, as the run ends, prints
#: for each callee whether one of its own ran. Written for any Python 3 the task's image
#: has. A callee is looked up only among the modules the run imported, so reading it
#: imports nothing; its file in the repository, under the root or `src/` or `lib/`, tells
#: a module the run never imported from a path that names none. `CALLEES` stands for the
#: tuple of callees asked about.
_RECORDER = """\
def _benchproofer_calls(callees):
    import atexit, builtins, os, sys, threading
    root = os.getcwd()
    seen = set()

    def trace(frame, event, arg):
        seen.add(frame.f_code)

    sys.settrace(trace)
    threading.settrace(trace)

    def walk(found, names):
        for name in names:
            found = getattr(found, name, None)
            if found is None:
                return None
        return found

    def codes(found, depth):
        if found is None or depth > 6:
            return []
        if isinstance(found, type):
            return codes(getattr(found, "__init__", None), depth + 1) + codes(
                getattr(found, "__new__", None), depth + 1)
        code = getattr(found, "__code__", None)
        if code is not None:
            return [code] + codes(getattr(found, "__wrapped__", None), depth + 1)
        for name in ("__func__", "fget", "func", "__wrapped__", "__call__"):
            inner = getattr(found, name, None)
            if inner is not None and inner is not found:
                return codes(inner, depth + 1)
        return []

    def files(parts):
        found = []
        for end in range(len(parts), 0, -1):
            for base in ("", "src", "lib"):
                stem = os.path.join(root, base, *parts[:end])
                for path in (stem + ".py", os.path.join(stem, "__init__.py")):
                    if os.path.isfile(path):
                        found.append((path, end))
        return found

    def loaded(parts, starts, end, path):
        for start in starts:
            if ".".join(parts[start:end]) in sys.modules:
                return sys.modules[".".join(parts[start:end])]
        for value in list(sys.modules.values()):
            where = getattr(value, "__file__", None)
            if where and os.path.realpath(where) == os.path.realpath(path):
                return value
        return None

    def judged(callee):
        parts = callee.split(".")
        starts = [0, 1] if parts[0] in ("src", "lib") else [0]
        places = files(parts)
        module = None
        if places:
            path, end = places[0]
            module, rest = loaded(parts, starts, end, path), parts[end:]
            if module is None:
                return "no", "the run never imported %s, which defines it" % (
                    os.path.relpath(path, root))
        for start in starts:
            for end in range(len(parts), start, -1):
                if module is None and ".".join(parts[start:end]) in sys.modules:
                    module, rest = sys.modules[".".join(parts[start:end])], parts[end:]
        if module is None and hasattr(builtins, parts[0]):
            module, rest = builtins, parts
        if module is None:
            return "unknown", ("no module of its path was imported, and none is a file of "
                               "the repository")
        found = walk(module, rest)
        if found is None:
            return "unknown", "%s has no %s when the run ends" % (
                module.__name__, ".".join(rest))
        ran = codes(found, 0)
        if not ran and isinstance(found, type):
            return "unknown", "it is a class whose construction runs no Python code of its own"
        if not ran:
            return "unknown", "it is not Python code, whose calls are not recorded"
        if any(code in seen for code in ran):
            return "yes", ""
        if any(code.co_filename.endswith(("subprocess.py", "popen_fork.py",
                                          "popen_spawn_posix.py", "popen_forkserver.py"))
               for code in seen):
            return "unknown", "the run started another process, where it may have run"
        return "no", "its code never ran"

    def report():
        sys.settrace(None)
        threading.settrace(None)
        for callee in callees:
            try:
                word, why = judged(callee)
            except Exception as error:
                word, why = "unknown", "looking it up failed: %r" % (error,)
            try:
                sys.stdout.write(("benchproofer:calls %s %s %s" % (callee, word, why)).rstrip()
                                 + "\\n")
                sys.stdout.flush()
            except Exception:
                pass

    atexit.register(report)


_benchproofer_calls(CALLEES)
del _benchproofer_calls
"""


def with_calls(program: str, callees: Sequence[str]) -> str:
    """``program`` as `spec.axioms_grounded` runs it: recording whether it calls ``callees``.

    The recording is run ahead of the program's own statements, on a line the program
    already has (`differential.inserted`), so the lines its traceback names are its own.
    Unchanged when there is no callee to ask about.
    """
    if not callees:
        return program
    recorder = _RECORDER.replace("(CALLEES)", f"({tuple(callees)!r})")
    return inserted(program, f"exec({recorder!r})")


def calls(output: str) -> dict[str, tuple[str, str]]:
    """Whether a run recorded by `with_calls` called each callee, and why not if it did not.

    ``yes``, ``no`` or ``unknown`` for each callee, with the reason for the last two; the
    last line printed for a callee is the one read, which is the recording's own, printed
    as the run ends.
    """
    return {
        match.group("callee"): (match.group("word"), match.group("why").strip())
        for match in _CALLS.finditer(output)
    }
