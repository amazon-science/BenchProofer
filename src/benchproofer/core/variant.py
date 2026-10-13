# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Whether a variant of a solution is admissible as evidence about its specification.

A mutant, a rival, and a review's attack are the same kind of object: a solution file
offered as evidence about the specification another file ships. A variant writes the
regions the spec view elides -- the implementation and, where the checker replays one, its
proof -- and is admissible when three conditions hold:

* It carries that specification (`Backend.same_spec`). The spec view elides only those
  regions, so equal views mean identical axioms, helpers, obligations and region layout.
* It does not weaken what the checker had to establish. A file reaching for `assume`,
  `sorry` or a directive that turns the checker off is accepted without the specification
  being reasoned about, so neither its acceptance nor its rejection is evidence.
* Where the proof is a declaration of its own, it restates a claim the solution file
  states: `theorem nothing : True := by trivial` elaborates and establishes nothing.

Escape hatches are counted against the solution file: one it already contains is
`spec.hygiene`'s question about the bundle, not a new one in the variant.
"""

from __future__ import annotations

import ast
import difflib
import io
import re
import sys
import tempfile
import tokenize
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ..errors import BenchproofError
from ..util.digest import digest_text
from ..util.proc import run
from . import extract, markers
from .runnable import executable_view

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = [
    "Answer",
    "Ran",
    "Scope",
    "assemble",
    "coincides",
    "fingerprint",
    "owned",
    "probe_holds",
    "probe_problem",
    "probe_rule",
    "refused_inside",
    "refused_within",
    "restates",
    "rule",
    "run_beside",
    "scope",
    "set_apart",
]


@dataclass(frozen=True, slots=True)
class Scope:
    """Whether one variant is admissible evidence, and why not when it is not."""

    admissible: bool
    reason: str = ""
    #: The reason in a few words, for the row of a table that lists the variant.
    label: str = ""

    def __bool__(self) -> bool:
        return self.admissible


def owned(solution: str, backend: Backend) -> tuple[str, ...]:
    """The regions a variant of ``solution`` writes: the implementation and any proof of it.

    A checker replaying the solution file's proof refuses a reshaped implementation for want of
    a step, which says nothing about the specification.

    Raises:
        MarkerError: ``solution`` has no readable marker regions.
    """
    present = markers.parse(solution, backend.comment)
    return tuple(name for name in present if markers.kind(name) in markers.ELIDED_REGIONS)


def refused_inside(source: str, said: str, backend: Backend) -> bool:
    """Whether every refusal the checker placed in ``source`` lies in what the variant owns.

    ``said`` is the checker's output, read with the backend's `refusal_site`. Such a checker
    places a failed obligation at the clause stating it, so a refusal inside the variant's
    own regions is a step of its proof -- a loop invariant, an assertion, a permission, a
    callee's precondition -- and no clause of the specification failed. False where the
    backend has no `refusal_site`, the checker placed no refusal, or any lies outside.
    """
    if not backend.refusal_site:
        return False
    lines = [
        int(found.group("line"))
        for found in re.finditer(backend.refusal_site, said, re.MULTILINE)
    ]
    try:
        regions = markers.parse(source, backend.comment)
        mine = [regions[name] for name in owned(source, backend)]
    except BenchproofError:
        return False
    return bool(lines) and all(
        any(region.start < line <= region.end for region in mine) for line in lines
    )


def refused_within(source: str, said: str, backend: Backend) -> list[int]:
    """The lines `refused_inside` reads that lie in ``source``'s owned `impl` regions."""
    if not backend.refusal_site:
        return []
    try:
        regions = markers.parse(source, backend.comment)
        mine = [
            regions[name] for name in owned(source, backend) if markers.kind(name) == "impl"
        ]
    except BenchproofError:
        return []
    return sorted(
        {
            line
            for found in re.finditer(backend.refusal_site, said, re.MULTILINE)
            if any(
                region.start < (line := int(found.group("line"))) <= region.end
                for region in mine
            )
        }
    )


def rule(allowed: Sequence[str]) -> str:
    """The prompt bullets saying which regions of a solution a model may write.

    Every template that asks for a variant renders these, so none drifts from another or
    from what `assemble` accepts.
    """
    bullet = _splice_bullet(allowed)
    if not any(markers.kind(name) == "proof" for name in allowed):
        return bullet
    return (
        f"{bullet}\n"
        "* The proof is yours as much as the implementation is. The proof in the solution\n"
        "  file was written for the reference implementation, and if you leave it alone\n"
        "  the checker will reject your file because its proof is missing a step -- which\n"
        "  says nothing about the specification. Restate the claim the solution file\n"
        "  states, word for word; how you establish it is up to you, but it has to be an\n"
        "  attempt. A placeholder that closes any goal (`sorry`, `admit`) gets the file\n"
        "  discarded as proving nothing, even where the rival is wrong and no proof of it\n"
        "  can close: there, write the proof you would write if it were right, and let the\n"
        "  checker say where it fails."
    )


def probe_rule(allowed: Sequence[str], placement: str) -> str:
    """`rule` for a case that *adds* to the solution file rather than rewriting it.

    An admissibility probe keeps the reference implementation, so the solution file's proof
    still closes and is not the language model's to rewrite. Where in the allowed regions
    the probe goes is the backend's ``placement``, since the wrong place is refused for a
    reason unrelated to the specification; it may be the line after a region's end, from
    where `assemble` carries a top-level declaration into the region.
    """
    return (
        f"{_splice_bullet(allowed)}\n"
        "* Keep the reference implementation character for character, and keep the\n"
        "  solution file's proof of it: you are adding a probe beside them, not replacing\n"
        "  them. A file that rewrites the implementation is a different case, and\n"
        "  Benchproofer rejects it as one.\n"
        f"{placement}"
    )


def _splice_bullet(allowed: Sequence[str]) -> str:
    """The bullet `rule` and `probe_rule` open with: which regions to write."""
    names = _listed(allowed)
    plural = "regions" if len(allowed) > 1 else "region"
    return (
        f"* Write the {names} {plural}, sentinel comments included, and leave every\n"
        "  other region of the file exactly as it is: Benchproofer splices what you write\n"
        "  into the solution file, so your file keeps the shipped specification."
    )


def probe_problem(accepted: str, source: str, backend: Backend) -> str:
    """Why an admissibility case is a rival rather than a probe, or "" when it is one.

    Two textual conditions. It carries the reference implementation **verbatim**, since the
    question is whether the specification admits the task's inputs for the implementation
    that shipped; a rewritten one is a soundness case. And it adds something, since the
    solution file unchanged is what `spec.verifies` already checked. Whether its inputs are
    the ones the task exercises is left to `spec.faithfulness`.
    """
    comment = backend.comment
    before, after = markers.parse(accepted, comment), markers.parse(source, comment)
    if backend.probe_statement:
        return _stated_problem(accepted, source, before, after, backend)
    rewritten = [
        name
        for name in markers.named(before, "impl")
        if before[name].text.strip()
        and (name not in after or before[name].text.strip() not in after[name].text)
    ]
    if rewritten:
        return _REWRITES
    if source.strip() == accepted.strip():
        return "it is the solution file unchanged, which adds no obligation to discharge"
    return ""


def _stated_problem(
    accepted: str,
    source: str,
    before: dict[str, markers.Region],
    after: dict[str, markers.Region],
    backend: Backend,
) -> str:
    """`probe_problem` for a backend whose probes are statements inside the implementation.

    The same two conditions: with its `probe_statement`s set apart, each implementation
    region reads as the reference implementation's line for line, and it adds at least one.
    """
    comment = backend.comment
    opener = (backend.probe_statement,)
    added: list[str] = []
    for name in markers.named(before, "impl"):
        if name not in after:
            return _REWRITES
        rest, had = set_apart(before[name].text, opener)
        rest_after, has = set_apart(after[name].text, opener)
        if _code_lines(rest, comment) != _code_lines(rest_after, comment):
            return _REWRITES
        added.extend(block for block in has if block not in had)
    if source.strip() == accepted.strip() or not added:
        return "it is the solution file unchanged, which adds no obligation to discharge"
    return ""


#: Why a probe that changed the reference implementation is not one.
_REWRITES = (
    "it rewrites the reference implementation instead of probing it, so what the "
    "checker says is about another implementation; that is a soundness case"
)


def _code_lines(code: str, comment: str) -> list[str]:
    """``code``'s lines of code, comments and trailing space aside."""
    masked = markers.mask_comments(code, comment)
    return [line.rstrip() for line in masked.splitlines() if line.strip()]


def set_apart(code: str, openers: Sequence[str]) -> tuple[str, list[str]]:
    """``code`` without the statements that open with ``openers``, and those statements.

    A statement takes the line that opens with one of the words and every following line
    indented deeper than it, which is how Lean reads a clause that wraps.
    """
    kept: list[str] = []
    blocks: list[str] = []
    depth: int | None = None
    for line in code.splitlines():
        indent = len(line) - len(line.lstrip())
        if depth is not None and (not line.strip() or indent > depth):
            if line.strip():
                blocks[-1] += "\n" + line
            continue
        depth = None
        if any(re.match(rf"{re.escape(word)}\b", line.strip()) for word in openers):
            depth = indent
            blocks.append(line)
            continue
        kept.append(line)
    return "\n".join(kept), blocks


#: What a file run directly gets in place of the contract library: Python's own `Assert`,
#: the exception an unmet precondition raises, Viper's pure sequences and sets, and the
#: quantifiers. A quantifier over `int` ranges over `_BOUND` either side of zero, exact for
#: the few literals and short sequences a probe uses but not for every integer, so a direct
#: run only ever moves a refusal from the specification to the case and never passes one.
#: Anything else the library has is undefined, so a file reaching for it is not run.
_PRELUDE = """\
def Assert(condition, *_):
    if not condition:
        raise AssertionError


class _Unmet(Exception):
    pass


class PSeq(tuple):
    def __new__(cls, *items):
        return super().__new__(cls, items)

    def __class_getitem__(cls, _):
        return cls

    def __add__(self, other):
        return PSeq(*tuple(self), *tuple(other))

    def __getitem__(self, index):
        if isinstance(index, slice) or index < 0:
            raise IndexError(index)
        return tuple.__getitem__(self, index)

    def take(self, until):
        return PSeq(*tuple(self)[:until])

    def drop(self, until):
        return PSeq(*tuple(self)[until:])

    def update(self, index, value):
        items = list(self)
        items[index] = value
        return PSeq(*items)


class PSet(frozenset):
    def __new__(cls, *items):
        return super().__new__(cls, items)

    def __class_getitem__(cls, _):
        return cls

    def __add__(self, other):
        return PSet(*self, *other)

    def __sub__(self, other):
        return PSet(*frozenset.__sub__(self, other))


def ToSeq(items):
    return PSeq(*items)


def _holds(answer):
    return answer[0] if isinstance(answer, tuple) else answer


def _domain(domain):
    return range(-_BOUND, _BOUND) if domain is int else domain


def Forall(domain, predicate):
    return all(_holds(predicate(item)) for item in _domain(domain))


def Exists(domain, predicate):
    return any(_holds(predicate(item)) for item in _domain(domain))


_BOUND = 512
"""
#: What calls each probe and says so once every one of them has returned.
_RUNNER = """
for _name in {probes!r}:
    globals()[_name]()
print("benchproofer:probe-held")
"""
#: What a file must be free of to be run here: it is a model's code, run on the tool's
#: machine, and a closed module -- the contract library, `typing`, its own classes and
#: functions -- has no use for any of these. They reach outside the module: the builtins
#: that run or fetch code by name, file and console access, the operating system, and the
#: attributes that lead from an object to a module's globals, the interpreter's classes, a
#: code object or a running frame. A special method a class defines or calls, such as
#: `__init__` or `__lt__`, and `__class__` are the module's own.
_UNSAFE = re.compile(
    r"\b(?:eval|exec|compile|open|input|breakpoint|getattr|setattr|globals|locals|vars)\s*\(|"
    r"\b__(?:import|builtins|globals|subclasses|bases?|mro|code|closure|dict|getattribute|"
    r"self|traceback|loader|spec|reduce(?:_ex)?)__\b|"
    r"\b(?:tb|f|gi|cr|ag)_(?:frame|back|globals|locals|builtins|code)\b|"
    r"\b(?:os|sys|subprocess|socket|shutil|pathlib)\b"
)
_CONTRACT_IMPORT = re.compile(r"^\s*(?:from|import)\s+nagini_contracts\b")


def probe_holds(accepted: str, source: str, backend: Backend) -> bool:
    """Whether an admissibility probe, when executed, holds of the reference implementation.

    A probe that holds -- every call admitted, every assertion met -- and that the checker
    still refuses asserts what the postcondition does not promise, or leaves out a step the
    checker needs, such as unfolding a recursive definition: a case to draft again, not a
    precondition refusing the input. Each function's preconditions are checked as it is
    called (`_Probed`), so a probe that holds is one whose every call the specification
    admits.

    False too where it cannot be decided here: a file in another language, one assuming a
    callee, one reaching outside a closed module (`_UNSAFE`), and one with no probe.
    """
    if backend.extension != ".py":
        return False
    if _assumes(source, backend) or _UNSAFE.search(
        markers.mask_comments(source, backend.comment)
    ):
        return False
    try:
        probes = _probes(accepted, source)
    except SyntaxError:
        return False
    if not probes:
        return False
    annotations = tuple(
        name for name in backend.annotation_tokens if name not in ("Assert(", "Requires(")
    )
    body = "\n".join(
        line
        for line in executable_view(source, annotations, backend.comment).splitlines()
        if not _CONTRACT_IMPORT.match(line)
    )
    try:
        body = ast.unparse(ast.fix_missing_locations(_Probed().visit(ast.parse(body))))
    except SyntaxError:
        return False
    module = _PRELUDE + body + "\n" + _RUNNER.format(probes=probes)
    with tempfile.TemporaryDirectory(prefix="benchproofer-probe-") as scratch:
        path = Path(scratch) / "probe.py"
        path.write_text(module, encoding="utf-8")
        result = run(
            (sys.executable, "-I", str(path)),
            cwd=Path(scratch),
            timeout_s=30,
            inherit_env=False,
        )
    return not result.timed_out and "benchproofer:probe-held" in result.output


def _assumes(source: str, backend: Backend) -> bool:
    """Whether a file's `axioms` region holds code, which running it could not honor."""
    region = markers.parse(source, backend.comment).get("axioms")
    return region is not None and bool(
        markers.mask_comments(region.text, backend.comment).strip()
    )


class _Implication(ast.NodeTransformer):
    """Contract expressions rewritten so that Python evaluates them the way Viper does.

    `Implies(a, b)` becomes `not a or b`, so the right-hand side -- often an index the left
    bounds -- is evaluated only when the left holds. A quantifier's triggers are dropped:
    Viper never evaluates them, and Python would, at every point of the domain.
    """

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        name = node.func.id if isinstance(node.func, ast.Name) else ""
        if name in ("Forall", "Exists") and len(node.args) == 2:
            predicate = node.args[1]
            if (
                isinstance(predicate, ast.Lambda)
                and isinstance(predicate.body, ast.Tuple)
                and len(predicate.body.elts) == 2
            ):
                predicate.body = predicate.body.elts[0]
        if name == "Implies" and len(node.args) == 2:
            condition, then = node.args
            return ast.BoolOp(
                op=ast.Or(), values=[ast.UnaryOp(op=ast.Not(), operand=condition), then]
            )
        return node


def _probes(accepted: str, source: str) -> list[str]:
    """The functions a variant adds at the top level that take no arguments."""
    before = {
        node.name for node in ast.parse(accepted).body if isinstance(node, ast.FunctionDef)
    }
    return [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
        and node.name not in before
        and not (node.args.args or node.args.posonlyargs or node.args.kwonlyargs)
    ]


#: Admissible inputs `run_beside` draws for each specified function, and the fewest it
#: needs before agreement says anything. Both files verified against one specification, so
#: each call terminates quickly; a precondition too narrow for random draws to meet leaves
#: the question undecided.
_DRAWS = 2000
_ENOUGH = 100
#: The most combinations `run_beside` runs every one of instead of drawing, when each
#: parameter takes its values from a finite pool -- integers, booleans and strings,
#: optional or in a tuple, and objects built from them. A branch taken at one combination
#: of a few integers is one uniform draws seldom reach.
_EXHAUSTIVE = 250_000
#: How deeply objects of the file's classes are built inside one another. One deeper than
#: this is drawn as None where its type is `Optional`; otherwise a field of its type keeps
#: the value its constructor gave it, and a constructor's argument of its type is not drawn.
_DEPTH = 3
#: Contract statements a direct run leaves out: what the checker proves rather than
#: what the code computes.
_READER_ONLY = frozenset(
    {
        "Ensures",
        "Exsures",
        "Invariant",
        "Assert",
        "Fold",
        "Unfold",
        "Decreases",
        "Open",
        "Close",
    }
)
#: Permission and termination terms a precondition may hold, which a direct run reads as
#: granted: the checker has already established them of each file.
_GRANTED = frozenset(
    {"MustTerminate", "Acc", "Rd", "Wildcard", "list_pred", "dict_pred", "set_pred"}
)
#: What executes the two files on the same drawn inputs, after `_PRELUDE`. Inputs are drawn from
#: each specified function's annotations with a fixed seed: integers from small ones and the
#: literals either file uses and their neighbours, since a model's values are codes -- tags,
#: code points -- a uniform draw would never hit; strings likewise from the files' literals. An
#: argument whose type is a class the file defines is drawn as a recipe (`_Build`): its
#: constructor, drawn arguments for the constructor's parameters, and a drawn value for each
#: field the class declares, built in each file with that file's own class, so that each side
#: gets an equal copy and neither sees the other's object.
_COINCIDE = """
import itertools as _itertools
import random as _random
import re as _re
import sys as _sys


def _load(code, filename):
    namespace = {{"PSeq": PSeq, "PSet": PSet, "ToSeq": ToSeq, "Forall": Forall,
                  "Exists": Exists, "_Unmet": _Unmet, "__name__": filename}}
    exec(compile(code, filename, "exec"), namespace)
    return namespace


class _Build:
    def __init__(self, name, args, fields):
        self.name, self.args, self.fields = name, args, fields

    def __repr__(self):
        built = self.name + "(" + ", ".join(repr(arg) for arg in self.args) + ")"
        if not self.fields:
            return built
        return built + "{{" + ", ".join(k + "=" + repr(v) for k, v in self.fields) + "}}"


_ran = set()


def _tracer(frame, event, arg):
    if frame.f_code.co_filename != "<variant>":
        return None
    if event == "line":
        _ran.add(frame.f_lineno)
    return _tracer


def _drawer(text, rng, depth=0):
    text = text.strip()
    if text in _CLASSES:
        if depth >= _DEPTH:
            return None
        params, fields = _CLASSES[text]
        parts = [_drawer(part, rng, depth + 1) for part in params]
        if None in parts:
            return None
        # A field of a type nothing draws keeps the value its constructor gave it.
        drawn = [(name, _drawer(kind, rng, depth + 1)) for name, kind in fields]
        drawn = [(name, draw) for name, draw in drawn if draw is not None]
        return lambda: _Build(
            text, [part() for part in parts], [(name, draw()) for name, draw in drawn]
        )
    if text == "int":
        return lambda: rng.choice(_POOL)
    if text == "bool":
        return lambda: rng.random() < 0.5
    if text == "None":
        return lambda: None
    if text == "str":
        return lambda: rng.choice(_STRINGS)
    match = _re.fullmatch(r"Optional\\[(.*)\\]", text)
    if match is not None:
        inner = _drawer(match.group(1), rng, depth)
        if inner is None:
            # A class of the file's nested deeper than the bound is drawn as absent.
            deep = depth >= _DEPTH and match.group(1).strip() in _CLASSES
            return (lambda: None) if deep else None
        return lambda: None if rng.random() < 0.25 else inner()
    match = _re.fullmatch(r"[Tt]uple\\[(.*)\\]", text)
    if match is not None:
        parts = [_drawer(part, rng, depth) for part in _split(match.group(1))]
        if not parts or None in parts:
            return None
        return lambda: tuple(part() for part in parts)
    match = _re.fullmatch(r"(PSeq|PSet|List|Set)\\[(.*)\\]", text)
    if match is None:
        return None
    inner = _drawer(match.group(2), rng, depth)
    if inner is None:
        return None
    make = {{"PSeq": lambda items: PSeq(*items), "PSet": lambda items: PSet(*items),
             "List": list, "Set": set}}[match.group(1)]
    return lambda: make([inner() for _ in range(rng.choice((0, 1, 2, 3, 3, 4, 5, 6)))])


def _values(text, depth=0):
    text = text.strip()
    if text in _CLASSES:
        if depth >= _DEPTH:
            return None
        params, fields = _CLASSES[text]
        parts = [_values(part, depth + 1) for part in [*params, *(k for _, k in fields)]]
        if None in parts or _size(parts) > _EXHAUSTIVE:
            return None
        names, cut = [name for name, _ in fields], len(params)
        return [
            _Build(text, list(values[:cut]), list(zip(names, values[cut:])))
            for values in _itertools.product(*parts)
        ]
    if text == "int":
        return list(_POOL)
    if text == "bool":
        return [False, True]
    if text == "None":
        return [None]
    if text == "str":
        return list(_STRINGS)
    match = _re.fullmatch(r"Optional\\[(.*)\\]", text)
    if match is not None:
        inner = _values(match.group(1), depth)
        return None if inner is None else [None] + inner
    match = _re.fullmatch(r"[Tt]uple\\[(.*)\\]", text)
    if match is not None:
        parts = [_values(part, depth) for part in _split(match.group(1))]
        if not parts or None in parts or _size(parts) > _EXHAUSTIVE:
            return None
        return [tuple(values) for values in _itertools.product(*parts)]
    return None


def _entire(text, depth=0):
    text = text.strip()
    if text in _CLASSES:
        params, fields = _CLASSES[text]
        kinds = [*params, *(kind for _, kind in fields)]
        return depth < _DEPTH and all(_entire(kind, depth + 1) for kind in kinds)
    if text in ("bool", "None"):
        return True
    match = _re.fullmatch(r"Optional\\[(.*)\\]", text)
    return match is not None and _entire(match.group(1), depth)


def _size(pools):
    size = 1
    for pool in pools:
        size *= len(pool)
    return size


def _split(text):
    parts, depth, start = [], 0, 0
    for index, char in enumerate(text):
        depth += (char == "[") - (char == "]")
        if char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return [part for part in parts if part.strip()]


def _made(value, namespace):
    if isinstance(value, _Build):
        made = namespace.get(value.name)
        if not isinstance(made, type):
            raise NameError(value.name)
        built = made(*[_made(arg, namespace) for arg in value.args])
        for field, item in value.fields:
            setattr(built, field, _made(item, namespace))
        return built
    if isinstance(value, list):
        return [_made(item, namespace) for item in value]
    if isinstance(value, set):
        return {{_made(item, namespace) for item in value}}
    if isinstance(value, (PSeq, PSet)):
        return type(value)(*[_made(item, namespace) for item in value])
    if isinstance(value, tuple):
        return tuple(_made(item, namespace) for item in value)
    return value


def _shape(value, path=()):
    if isinstance(value, list):
        return (list, tuple(_shape(item, path) for item in value))
    if isinstance(value, tuple):
        return tuple(_shape(item, path) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_shape(item, path) for item in value)
    if isinstance(value, dict):
        return (dict, frozenset((_shape(k, path), _shape(v, path)) for k, v in value.items()))
    if type(value).__module__ not in ("<accepted>", "<variant>"):
        return value
    # An object of a class the file defines is its class's name and its fields.
    if id(value) in path:
        return (object, type(value).__name__)
    path = (*path, id(value))
    fields = sorted(vars(value).items())
    return (object, type(value).__name__, tuple((k, _shape(v, path)) for k, v in fields))


def _call(namespace, name, drawn):
    args = None
    try:
        args = [_made(arg, namespace) for arg in drawn]
        answer = ("returned", namespace[name](*args))
    except _Unmet:
        return None
    except (NameError, AttributeError, TypeError) as error:
        print("benchproofer:coincide unsupported", name, type(error).__name__)
        raise SystemExit(0)
    except RecursionError:
        answer = ("raised", "RecursionError")
    except Exception as error:
        if args is None:
            # An object its own constructor will not build is not an input.
            return None
        answer = ("raised", type(error).__name__)
    return _shape((answer, args))


_POOL = {pool!r}
_STRINGS = {strings!r}
_EXHAUSTIVE = {exhaustive!r}
_CLASSES = {classes!r}
_DEPTH = {depth!r}
_CHANGED = set({changed!r})
_accepted = _load({accepted!r}, "<accepted>")
_variant = _load({variant!r}, "<variant>")
_rng = _random.Random(0)
_agreed = []
_finite = []
_short = []
for _name, _types in {entries!r}:
    _draws = [_drawer(text, _rng) for text in _types]
    for _text, _draw in zip(_types, _draws):
        if _draw is None:
            print("benchproofer:coincide undrawn", _name, _text or "-")
            raise SystemExit(0)
    _pools = [_values(text) for text in _types]
    _exhaustive = None not in _pools and _size(_pools) <= _EXHAUSTIVE
    if _exhaustive:
        _inputs = (list(values) for values in _itertools.product(*_pools))
    else:
        _inputs = ([draw() for draw in _draws] for _ in range({draws}))
    _count = 0
    for _args in _inputs:
        _left = _call(_accepted, _name, _args)
        if _left is None:
            continue
        _count += 1
        _tracing = not _CHANGED <= _ran
        if _tracing:
            _sys.settrace(_tracer)
        try:
            _right = _call(_variant, _name, _args)
        finally:
            if _tracing:
                _sys.settrace(None)
        if _left != _right:
            _shown = ", ".join(repr(arg) for arg in _args)
            print("benchproofer:coincide differs", f"{{_name}}({{_shown[:200]}})")
            raise SystemExit(0)
    # Where every combination was run, as large a share of them admissible as the draws
    # would have needed to meet enough admissible inputs -- unless each pool is its type's
    # whole range, so that every admissible input of the domain was run.
    _whole = _exhaustive and _count > 0 and all(_entire(text) for text in _types)
    if _whole:
        _finite.append((_count, _name))
    elif _exhaustive and _count * {draws} < {enough} * _size(_pools):
        _short.append((_count, _name))
    elif not _exhaustive and _count < {enough}:
        _short.append((_count, _name))
    else:
        _agreed.append((_count, _name))
if _short:
    print("benchproofer:coincide few", *min(_short))
else:
    print("benchproofer:coincide agreed", min(_agreed)[0] if _agreed else 0)
    if _finite:
        _total = sum(count for count, _ in _finite)
        print("benchproofer:coincide finite", _total, *(name for _, name in _finite))
print("benchproofer:coincide unreached", sorted(_CHANGED - _ran))
"""

#: What running a variant and the reference implementation on the same drawn inputs found: an
#: input on which the two do different things, agreement on enough admissible inputs with every
#: line the variant changes run, or neither.
Answer = Literal["differs", "agreed", "not run"]


@dataclass(frozen=True, slots=True)
class Ran:
    """What running a variant and the reference implementation on one draw found, and why."""

    answer: Answer
    #: A sentence saying what was found, or why nothing was.
    why: str


def run_beside(accepted: str, source: str, backend: Backend) -> Ran:
    """Run a variant and the reference implementation on the same drawn inputs.

    Both files run as Python (`_direct`) on inputs drawn from the specified functions'
    annotations, keeping those the shared precondition admits, and are compared on what
    each returns or raises and leaves in what it was passed; a pool of at most
    `_EXHAUSTIVE` combinations is run whole. Integers are drawn from small ones and the
    literals either file uses, with their neighbours, and strings likewise. An object of a
    class the file defines is built by that class's constructor from drawn arguments for
    its annotated parameters, and then each field the class declares is set to a drawn
    value of its type (`_classes`), so that it may be in any state the function's
    precondition admits, which decides whether it is kept, as for any other argument. Two
    such objects are the same where their classes' names and their fields are.

    Returns:
        ``differs`` where an input told the two apart; ``agreed`` where every admissible
        input drawn agreed, at least `_ENOUGH` for each function -- or, for a function
        every one of whose parameters is drawn from its type's whole range (`bool`, `None`,
        an `Optional` of one, an object whose constructor's parameters and fields are all
        such), every admissible input of that finite domain -- and every line the variant
        changes ran; ``not run`` otherwise: another language, a file that assumes a callee
        (an `axioms` region holding code, or a `@ContractOnly` decorator in its code) or
        reaches outside a closed module (`_UNSAFE`), a parameter type nothing draws, a name
        or an operation the run does not provide, fewer admissible inputs than that, a
        changed line no draw reached, or a run that did not finish. Each comes with a
        sentence saying what was found.
    """
    if backend.extension != ".py":
        return Ran("not run", f"files in {backend.language} cannot be run here")
    for text in (accepted, source):
        code = markers.mask_comments(markers.mask_strings(text), backend.comment)
        if _assumes(text, backend) or "@ContractOnly" in code:
            return Ran("not run", "a file assumes a callee, which running it cannot honor")
        if _UNSAFE.search(markers.mask_comments(text, backend.comment)):
            return Ran("not run", "a file reaches for something a closed module has no use for")
    try:
        entries = _entries(accepted, backend)
        classes = _classes(accepted)
        programs = [_direct(text) for text in (accepted, source)]
        pool = sorted(_literals(accepted, source) | set(range(-2, 11)))
        strings = sorted(_strings(accepted, source) | {"", " ", "0", "a", "ab", "A b"})
    except SyntaxError:
        return Ran("not run", "a file does not parse as Python")
    if not entries:
        return Ran("not run", "the specification names no function to call")
    module = _PRELUDE + _COINCIDE.format(
        pool=pool,
        strings=strings,
        accepted=programs[0],
        variant=programs[1],
        entries=entries,
        draws=_DRAWS,
        exhaustive=_EXHAUSTIVE,
        classes=classes,
        depth=_DEPTH,
        enough=_ENOUGH,
        changed=_changed(*programs),
    )
    with tempfile.TemporaryDirectory(prefix="benchproofer-coincide-") as scratch:
        path = Path(scratch) / "coincide.py"
        path.write_text(module, encoding="utf-8")
        result = run(
            (sys.executable, "-I", str(path)),
            cwd=Path(scratch),
            timeout_s=60,
            inherit_env=False,
        )
    return _read(result.output, timed_out=result.timed_out, names=[n for n, _ in entries])


def _read(output: str, *, timed_out: bool, names: Sequence[str]) -> Ran:
    """What one run of `_COINCIDE` printed, as `run_beside` reports it."""
    said = {
        found.group(1): found.group(2)
        for found in re.finditer(r"^benchproofer:coincide (\w+) ?(.*)$", output, re.MULTILINE)
    }
    if "differs" in said:
        return Ran(
            "differs",
            "executed beside the reference implementation on the same drawn inputs, it does "
            f"something else on `{said['differs']}`",
        )
    if "undrawn" in said:
        name, _, kind = said["undrawn"].partition(" ")
        return Ran("not run", f"nothing draws an argument of type `{kind}` for `{name}`")
    if "unsupported" in said:
        name, _, error = said["unsupported"].partition(" ")
        return Ran(
            "not run",
            f"running `{name}` raised {error}: the run does not provide a name or an "
            "operation the files use",
        )
    if timed_out:
        return Ran("not run", "the run did not finish")
    if "unreached" not in said:
        return Ran("not run", "the run stopped before it compared anything")
    if said["unreached"] != "[]":
        # A changed line that no draw ran is a difference nobody looked at.
        return Ran("not run", "a line it changes was not reached by any input drawn")
    if "few" in said:
        count, _, name = said["few"].partition(" ")
        return Ran(
            "not run",
            "executed beside the reference implementation on the same drawn inputs, it "
            "returns what the reference implementation returns on every admissible input "
            f"drawn for `{name}`, but only {int(count):,} of them were admissible, too few to "
            "decide whether the two compute the same",
        )
    count, *whole = said.get("finite", "0").split()
    drawn = [name for name in names if name not in whole]
    found: list[str] = []
    if drawn:
        found.append(
            f"on every one of {int(said['agreed']):,} or more admissible input(s) drawn for "
            f"{_listed(drawn)}"
        )
    if whole:
        found.append(
            f"on all {int(count):,} admissible inputs of a finite domain for {_listed(whole)}"
        )
    return Ran(
        "agreed",
        "executed on the same drawn inputs, it returns what the reference implementation "
        f"returns {', and '.join(found)}",
    )


def coincides(accepted: str, source: str, backend: Backend) -> str:
    """Whether a variant computes what the reference implementation computes, when executed.

    The sentence `run_beside` gives where the two agreed, or "" where an input told them
    apart or the run could not decide it.
    """
    ran = run_beside(accepted, source, backend)
    return ran.why if ran.answer == "agreed" else ""


class _Direct(_Implication):
    """A Nagini file rewritten to run as Python, keeping its preconditions.

    A `Requires` raises `_Unmet` when it fails, so a refused input is skipped rather than
    run; other contract statements are dropped, permission and termination terms read as
    true, `Old(x)` as `x`, and decorators go.
    """

    #: The contract statements dropped: those the checker proves rather than runs.
    dropped: frozenset[str] = _READER_ONLY

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.decorator_list = []
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.AST | None:
        self.generic_visit(node)
        call = node.value
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
            return node
        if call.func.id in self.dropped:
            return None
        if call.func.id == "Requires" and call.args:
            unmet = ast.Raise(exc=ast.Call(ast.Name("_Unmet", ast.Load()), [], []))
            return ast.If(
                test=ast.UnaryOp(op=ast.Not(), operand=call.args[0]), body=[unmet], orelse=[]
            )
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        rewritten = super().visit_Call(node)
        if not isinstance(rewritten, ast.Call) or not isinstance(rewritten.func, ast.Name):
            return rewritten
        if rewritten.func.id in _GRANTED:
            return ast.Constant(True)
        if rewritten.func.id == "Old" and len(rewritten.args) == 1:
            return rewritten.args[0]
        return rewritten


class _Probed(_Direct):
    """A variant rewritten to run its probes: `_Direct`, keeping each `Assert` it makes."""

    dropped = _READER_ONLY - {"Assert"}


def _direct(source: str) -> str:
    """``source`` as Python that runs without the contract library; see `_Direct`."""
    kept = "\n".join(line for line in source.splitlines() if not _CONTRACT_IMPORT.match(line))
    tree = _Direct().visit(ast.parse(kept))
    for node in ast.walk(tree):
        # A block whose only statements were contracts would be left empty.
        body = getattr(node, "body", None)
        if isinstance(body, list) and not body:
            body.append(ast.Pass())
    return ast.unparse(ast.fix_missing_locations(tree))


#: Lines that never report being run, because Python runs the statement they introduce
#: rather than the line itself.
_SILENT = re.compile(r"^\s*(?:else|try|finally)\s*:\s*$")


def _changed(accepted: str, variant: str) -> list[int]:
    """The lines of ``variant``, by number, that differ from ``accepted``.

    A deleted line is stood for by the line now in its place or, where that is blank and so
    never run, by the last line of code before it.
    """
    before, after = accepted.splitlines(), variant.splitlines()
    lines: set[int] = set()
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, _, _, start, end in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            lines.update(range(start + 1, end + 1))
        elif tag == "delete":
            standing = min(start + 1, len(after))
            while standing > 1 and not after[standing - 1].strip():
                standing -= 1
            lines.add(standing)
    return sorted(
        number
        for number in lines
        if 0 < number <= len(after)
        and after[number - 1].strip()
        and not _SILENT.match(after[number - 1])
    )


def _entries(accepted: str, backend: Backend) -> list[tuple[str, list[str]]]:
    """Each specified function, with its parameters' annotations as written."""
    regions = markers.parse(accepted, backend.comment)
    named = [
        found.group(1)
        for name, region in regions.items()
        if markers.kind(name) == "spec"
        and (found := re.search(r"^\s*def\s+(\w+)", region.text, re.MULTILINE))
    ]
    defined = {
        node.name: node
        for node in ast.parse(accepted).body
        if isinstance(node, ast.FunctionDef)
    }
    return [
        (
            name,
            [_annotation(arg.annotation) for arg in defined[name].args.args],
        )
        for name in named
        if name in defined
    ]


def _annotation(node: ast.expr | None) -> str:
    """A parameter's annotation as written, with the quotes around it or a part dropped."""
    if node is None:
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.replace(" ", "")
    return re.sub(r"[\s'\"]", "", ast.unparse(node))


def _classes(source: str) -> dict[str, tuple[list[str], list[tuple[str, str]]]]:
    """Each class a file defines at its top level, with its constructor's and fields' types.

    The parameters are those of its own `__init__` after `self`, as `_annotation` reads
    them; a class without one is built with no arguments. A field is declared by an
    annotation in the class body, or in `__init__` by an assignment to an attribute of
    `self` that carries an annotation or a type comment; the first declaration of each
    counts.
    """
    try:
        tree = ast.parse(source, type_comments=True)
    except SyntaxError:
        tree = ast.parse(source)
    found: dict[str, tuple[list[str], list[tuple[str, str]]]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        init = next(
            (
                item
                for item in node.body
                if isinstance(item, ast.FunctionDef) and item.name == "__init__"
            ),
            None,
        )
        params = [*init.args.posonlyargs, *init.args.args] if init is not None else []
        fields: dict[str, str] = {}
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields.setdefault(item.target.id, _annotation(item.annotation))
        for step in ast.walk(init) if init is not None and params else ():
            target: ast.expr
            if isinstance(step, ast.AnnAssign):
                target, kind = step.target, _annotation(step.annotation)
            elif isinstance(step, ast.Assign) and len(step.targets) == 1 and step.type_comment:
                target = step.targets[0]
                kind = re.sub(r"[\s'\"]", "", step.type_comment.split("#")[0])
            else:
                continue
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == params[0].arg
            ):
                fields.setdefault(target.attr, kind)
        found[node.name] = (
            [_annotation(param.annotation) for param in params[1:]],
            list(fields.items()),
        )
    return found


def _literals(*sources: str) -> set[int]:
    """Every integer literal the files use, with its neighbours."""
    found: set[int] = set()
    for source in sources:
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                found.update((node.value - 1, node.value, node.value + 1))
    return found


def _strings(*sources: str) -> set[str]:
    """Every short string literal the files use, docstrings aside."""
    found: set[str] = set()
    for source in sources:
        for node in ast.walk(ast.parse(source)):
            if (
                isinstance(node, ast.Constant)
                and type(node.value) is str
                and len(node.value) <= 40
                and "\n" not in node.value
            ):
                found.add(node.value)
    return found


def _listed(names: Sequence[str]) -> str:
    quoted = [f"`{name}`" for name in names]
    return (
        " and ".join(quoted)
        if len(quoted) < 3
        else f"{', '.join(quoted[:-1])} and {quoted[-1]}"
    )


def assemble(
    solution: str,
    reply: str,
    backend: Backend,
    *,
    allowed: Sequence[str],
    probe: bool = False,
    witnessed: bool = False,
) -> str:
    """Build a whole solution file from the regions ``reply`` wrote.

    Every region the reply did not write is ``solution``'s, unchanged. What the reply wrote
    outside its regions is dropped: the spec view keeps every line there, so a variant may
    put nothing in the file but the regions it was offered.

    ``probe``, for an admissibility case, makes one exception: a declaration written at the
    top level after an implementation region -- a Python function, or what the backend's
    `probe_opener` opens -- is carried into a region (`_carried`). ``witnessed`` says the
    reply was asked for a refutation witness after its regions, which is not one of them.

    Raises:
        BenchproofError: The reply carries no region the caller asked for, writes one it
            was not offered, or produces a file that cannot be read back.
    """
    source = solution
    written = _written(reply, backend, allowed, accepted=solution, witnessed=witnessed)
    for name, body in written.items():
        source = markers.replace_region(source, backend.comment, name, body)
    if probe and _opener(backend) is not None:
        try:
            fragment = _reopened(extract.regions(reply), backend.comment, allowed)
        except BenchproofError:
            fragment = ""
        if fragment:
            regions = markers.parse(source, backend.comment)
            for name, functions in _carried(source, fragment, backend, allowed).items():
                body = regions[name].text.rstrip()
                source = markers.replace_region(
                    source, backend.comment, name, f"{body}\n\n\n{functions}"
                )
    # A body that carried sentinels of its own would leave the file unreadable here.
    markers.parse(source, backend.comment)
    return source


#: The line that opens a function definition at the top level of a Python file.
_TOP_DEF = re.compile(r"(?:async\s+)?def\s+(\w+)")


def _opener(backend: Backend) -> re.Pattern[str] | None:
    """The opening line of a declaration `_carried` takes, or None when it takes none."""
    if backend.extension == ".py":
        return _TOP_DEF
    return re.compile(backend.probe_opener) if backend.probe_opener else None


def _carried(
    source: str, fragment: str, backend: Backend, allowed: Sequence[str]
) -> dict[str, str]:
    """The declarations a probe wrote after an implementation region, and where each goes.

    ``source`` is the file they would be carried into. What is carried is a declaration
    whose name, if any, ``source`` does not bind, written unindented after an impl region's
    closing sentinel and outside every region: under Python a `def` with its decorators and
    every line indented under it, elsewhere what the backend's `probe_opener` opens, such as
    a Lean `example`.

    It goes at the end of an implementation region: outside every region the spec view
    would keep it and the case would fail `Backend.same_spec`, while inside one the case
    owns it and it is still a declaration of the module's own -- for Nagini, a function
    whose call to the specified one is judged on the precondition, not as a recursive call.
    That holds only of a region ending at the top level of the file, since an unindented
    `def` would cut short a definition that goes on past the region. So the region it was
    written after takes it if that one ends at the top level, else the file's last
    implementation region that does; with none, it is dropped.

    Returns:
        The text carried into each implementation region, by region name.

    Raises:
        MarkerError: ``source`` or ``fragment`` has no readable marker regions.
    """
    comment = backend.comment
    written = markers.parse(fragment, comment, required=())
    lines = fragment.splitlines()
    within: dict[int, str] = {
        index: name
        for name, region in written.items()
        for index in range(region.start - 1, region.end + 1)
    }
    # The lines outside every region, in runs broken by the regions between them, each
    # run with the implementation region whose closing sentinel it last followed.
    runs: list[tuple[str, list[str]]] = []
    following, broken = "", True
    for index, line in enumerate(lines):
        name = within.get(index)
        if name is not None:
            broken = True
            if index == written[name].end and markers.kind(name) == "impl":
                following = name
            continue
        if not following:
            continue
        if broken:
            runs.append((following, []))
            broken = False
        runs[-1][1].append(line)

    opener = _opener(backend) or _TOP_DEF
    bound = (
        _defined(source, comment)
        if backend.extension == ".py"
        else markers.declarations(source, comment, opens=markers.BINDS)
    )
    functions: list[tuple[str, str]] = []
    for followed, stretch in runs:
        for statement in _statements(stretch, comment):
            first = next(
                (
                    line
                    for line in statement
                    if _coded(line, comment) and not line[:1].isspace() and line[:1] != "@"
                ),
                "",
            )
            found = opener.match(first)
            if found is not None and (found.group(1) or "") not in bound:
                kept = list(statement)
                while kept and not _coded(kept[-1], comment):
                    kept.pop()
                functions.append((followed, "\n".join(kept)))

    regions = markers.parse(source, comment)
    fits = [
        name
        for name in reversed(tuple(regions))
        if markers.kind(name) == "impl"
        and name in allowed
        and _ends_at_top_level(source, regions[name], comment)
    ]
    placed: dict[str, list[str]] = {}
    for followed, text in functions:
        target = followed if followed in fits else (fits[0] if fits else "")
        if target:
            placed.setdefault(target, []).append(text)
    return {name: "\n\n\n".join(texts) for name, texts in placed.items()}


def _defined(source: str, comment: str) -> set[str]:
    """The functions ``source`` defines at its top level, as `_probes` reads a file.

    A file Python cannot parse is read by its `def` lines, which errs towards a name being
    taken, so the function is left where the reply wrote it.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return markers.declarations(source, comment, opens=("def",))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _statements(lines: Sequence[str], comment: str) -> list[list[str]]:
    """A run of Python lines split into its top-level statements, in order.

    A statement opens at an unindented line of code and takes every following line that is
    indented, blank, or only a comment; a decorator and the `def` after it are one
    statement, and what precedes the first unindented line of code is one of its own.
    """
    statements: list[list[str]] = [[]]
    decorating = False
    for line in lines:
        if _coded(line, comment) and not line[:1].isspace():
            if not decorating:
                statements.append([])
            decorating = line[:1] == "@"
        statements[-1].append(line)
    return [statement for statement in statements if statement]


def _ends_at_top_level(source: str, region: markers.Region, comment: str) -> bool:
    """Whether nothing indented follows ``region``'s closing sentinel in ``source``.

    The first line of code after the sentinel decides it; blank lines and comments, the
    sentinels among them, belong to no block.
    """
    for line in source.splitlines()[region.end + 1 :]:
        if _coded(line, comment):
            return not line[:1].isspace()
    return True


def _coded(line: str, comment: str) -> bool:
    """Whether ``line`` holds code, rather than nothing or only a comment."""
    return bool(markers.mask_comments(line, comment).strip())


def scope(solution: str, variant: str, backend: Backend) -> Scope:
    """Decide whether ``variant`` says anything about ``solution``'s specification.

    Sharing the specification is the caller's check (`Backend.same_spec`); this one reads
    what that leaves open, the regions the spec view elides.
    """
    try:
        accepted, offered = _elided(solution, backend), _elided(variant, backend)
    except BenchproofError as exc:
        return Scope(False, f"its marker regions cannot be read: {exc}", "unreadable")

    # Assumption tokens count as banned ones: an assumption belongs in the shared `axioms`
    # region, and one in an implementation assumes what it was supposed to establish.
    escapes = backend.escapes()
    strings = backend.inert_strings
    introduced = set(
        markers.occurrences(offered, backend.comment, escapes, strings=strings)
    ) - set(markers.occurrences(accepted, backend.comment, escapes, strings=strings))
    if introduced:
        listed = ", ".join(repr(token) for token in sorted(introduced))
        return Scope(
            False,
            f"it reaches for {listed}, which the solution file does not: that discharges "
            "an obligation instead of meeting it",
            "uses a construct the solution file does not",
        )

    stated = markers.claims(accepted, backend.comment, backend.proof_tokens)
    if stated and not set(stated) & set(
        markers.claims(offered, backend.comment, backend.proof_tokens)
    ):
        return Scope(
            False,
            "it proves a claim of its own rather than one the solution file states, so "
            f"the checker's verdict is not about {stated[0][:60]!r}",
            "proves a claim of its own",
        )
    return Scope(True)


def fingerprint(impl: str, backend: Backend) -> str:
    """Identify an implementation by its code, for telling one variant from another.

    ``impl`` is the text of a file's implementation regions (`markers.joined`). Comments,
    indentation and blank lines are left out, since two implementations differing only
    there compute the same thing.
    """
    lines = [line.strip() for line in _uncommented(impl, backend).split("\n")]
    return digest_text("\n".join(line for line in lines if line))


def restates(accepted: str, source: str, backend: Backend) -> bool:
    """Whether a variant's implementation is the reference one, comments and layout aside.

    False when either file cannot be read or has no implementation to compare.
    """
    try:
        before = markers.joined(markers.parse(accepted, backend.comment), "impl")
        after = markers.joined(markers.parse(source, backend.comment), "impl")
    except BenchproofError:
        return False
    if not before.strip() or not after.strip():
        return False
    return fingerprint(before, backend) == fingerprint(after, backend)


def _uncommented(code: str, backend: Backend) -> str:
    """``code`` with its comments taken off the lines they end.

    Python's are found by its tokenizer, so a ``#`` inside a string literal stays code.
    Another language's comments, and Python the tokenizer refuses, are masked by
    `markers.mask_comments`.
    """
    if backend.extension != ".py":
        return markers.mask_comments(code, backend.comment)
    lines = code.split("\n")
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.COMMENT:
                row, column = token.start
                lines[row - 1] = lines[row - 1][:column]
    except (tokenize.TokenError, SyntaxError):
        return markers.mask_comments(code, backend.comment)
    return "\n".join(lines)


def _reopened(fragment: str, comment: str, allowed: Sequence[str]) -> str:
    """``fragment`` with an opening sentinel added where it closes a region nothing opened.

    A reply often writes a region's body and closing sentinel alone. The body is then the
    lines above the close that no other region claims, so the marker is added rather than
    a round spent asking for it. Only for a region the reply was offered, and only where
    the result reads back: a fragment that parses, or whose markers are unbalanced some
    other way, is returned as it came, for the parse to report.
    """
    try:
        markers.parse(fragment, comment, required=())
    except BenchproofError:
        pass
    else:
        return fragment
    lines = fragment.splitlines()
    for name in allowed:
        begin, end = markers.begin_marker(comment, name), markers.end_marker(comment, name)
        marked = [line.strip() for line in lines]
        if end not in marked or begin in marked:
            continue
        closes = marked.index(end)
        sentinels = [
            index
            for index, line in enumerate(marked[:closes])
            if markers.is_marker(line, comment)
        ]
        at = sentinels[-1] + 1 if sentinels else 0
        lines.insert(at, begin)
    repaired = "\n".join(lines)
    try:
        markers.parse(repaired, comment, required=())
    except BenchproofError:
        return fragment
    return repaired


def _written(
    reply: str,
    backend: Backend,
    allowed: Sequence[str],
    *,
    accepted: str = "",
    witnessed: bool = False,
) -> dict[str, str]:
    """Read the region bodies out of a reply, keyed by region name.

    A reply owning one region need not mark it; when a refutation witness was asked for
    after it (``witnessed``), the region is the block before the witness. One owning more
    must mark them, and is rejected otherwise so the caller's retry can ask for sentinels;
    half a pair is completed (`_reopened`). A region it was not offered, written exactly
    as ``accepted`` has it, is a quotation and left alone.

    Raises:
        BenchproofError: The reply is not the shape that was asked for.
    """
    try:
        fragment = extract.regions(reply)
    except BenchproofError:
        if len(allowed) != 1:
            raise
        return {allowed[0]: extract.code(reply, witnessed=witnessed)}

    found = markers.parse(
        _reopened(fragment, backend.comment, allowed), backend.comment, required=()
    )
    shipped = markers.parse(accepted, backend.comment, required=()) if accepted else {}
    extra = [
        name
        for name in found
        if name not in allowed
        and not (name in shipped and found[name].text.strip() == shipped[name].text.strip())
    ]
    if extra:
        listed = ", ".join(repr(name) for name in extra)
        raise BenchproofError(f"the reply rewrites region(s) it was not offered: {listed}")
    written = {name: found[name].text for name in allowed if name in found}
    if not written:
        raise BenchproofError(
            f"the reply contains none of the region(s) that were asked for: "
            f"{', '.join(repr(name) for name in allowed)}"
        )
    return written


def _elided(source: str, backend: Backend) -> str:
    """The text of the regions the spec view elides, which is a variant's to write.

    Raises:
        MarkerError: The file has no readable marker regions.
    """
    regions = markers.parse(source, backend.comment)
    return "\n".join(
        region.text
        for name, region in regions.items()
        if markers.kind(name) in markers.ELIDED_REGIONS
    )
