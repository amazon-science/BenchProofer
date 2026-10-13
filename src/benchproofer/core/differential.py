# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`conformance.py`, which compares the verified implementation with the repository.

Verification shows the implementation meets the specification; `conformance.py` shows the
implementation is about the repository's code. `conformance.py` holds a
Python copy of the implementation, draws inputs, calls both the function the fix
leaves in the repository and the copy, and prints what it covered::

    benchproofer:compared pkg.geometry.area 100000 random rectangles
    benchproofer:disagrees pkg.geometry.area ((0, 2),) -> the repository returns 0,
        the implementation returns 2

Exit zero means every comparison agreed. A `disagrees` line is an observed counterexample,
a finding under a falsifier as much as under a prover. An `unbuildable`, `refused` or
`copy-raised` line names an input the program did not compare, by why -- it could not build
the value, the repository refuses the value, or the program's copy of the implementation
raised -- and a `skipped` line a part of the implementation it did not compare; either leaves
the comparison undecided. A `benchproofer:` line in none of the protocol's shapes is reported as
`unparsed`, since skipping it would read a comparison as none and a disagreement as
agreement.

`conformance.py` runs against the tree with the golden patch applied, because the function
under comparison is the one the fix produces. It holds the Python copy instead of writing it
into the tree, where it would overwrite that function; where the backend's language is the
repository's, what it carries is the implementation region with the checker's annotations taken
out, not a second implementation that happens to agree. Each reported function is named by its
dotted path, whose module has to appear in the program (`ungrounded`), so a `conformance.py`
cannot compare the implementation with its own paraphrase of the repository.

The rules `conformance.py` is written to are the shared rules file `conformance-rules.md`,
which the conformance request and a repair session are both given (`protocol_for`); the
readers of each line live here, beside the shape each is asked for in (`SHAPES`).
"""

from __future__ import annotations

import ast
import builtins
import re
import symtable
import tokenize
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..errors import MarkerError
from .markers import joined, named, parse, python_tokens
from .prompts import SHARED
from .runnable import contains_lines, executable_view, uncarried

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = [
    "ALIASES",
    "BLOCKED",
    "COMMENT",
    "DEADLINE_SHARE",
    "DIRECT",
    "HARNESS",
    "REGION",
    "REPLAY",
    "SHAPES",
    "TRANSLITERATED",
    "WITNESSES",
    "Comparison",
    "answered",
    "arguments",
    "blocked",
    "carried",
    "clipped",
    "compared",
    "comparisons",
    "disagreements",
    "excluded",
    "executables",
    "inadmissible",
    "inserted",
    "invented",
    "lacking",
    "names_entry",
    "protocol_for",
    "provenance",
    "replayed",
    "runs_as_written",
    "runs_in",
    "seed",
    "shapes_for",
    "skipped_regions",
    "substituted",
    "unbound",
    "uncopied",
    "ungrounded",
    "unparsed",
    "unsupported",
    "with_replay",
    "witnessed",
    "witnesses",
]

#: The file a bundle's `conformance.py` ships as. Always Python, because it runs
#: where the benchmark's tests run.
HARNESS = "conformance.py"

#: `conformance.py` ran the verified implementation itself.
DIRECT = "direct"
#: `conformance.py` ran a translation of it, a weaker claim recorded apart from direct ones.
TRANSLITERATED = "transliterated"

#: The comment token of a `conformance.py`'s region sentinels.
COMMENT = "#"
#: The region a `conformance.py` carries the implementation in, named as the solution file names
#: its implementation regions (`impl`, `impl.2`, ...). Marking it lets any implementation
#: of the same functions, such as a reviewer's submission, be substituted in.
REGION = "impl"

#: The share of the oracle's budget a `conformance.py` may spend drawing inputs. The rest starts
#: the container, applies the fix and imports the repository, and a `conformance.py` the oracle
#: kills mid-run reports nothing.
DEADLINE_SHARE = 2 / 3

#: How many report lines a verdict quotes, and how many characters of each.
WITNESSES = 3
WITNESS_CHARS = 400

#: The module-level name the tool binds ahead of a `conformance.py`'s code (`with_replay`) to
#: the inputs to compare again, so an input found once is put to every later run.
REPLAY = "BENCHPROOFER_REPLAY"

#: The word of the line naming an input the program did not compare, with the reason.
BLOCKED = "blocked"
#: Words read as `BLOCKED`, each naming one of its reasons in place of the word: a line
#: `benchproofer:refused <the input>: <the error>` is read as a `blocked` line.
ALIASES: dict[str, str] = {
    "unbuildable": BLOCKED,
    "refused": BLOCKED,
    "copy-raised": BLOCKED,
}

_COMPARED = re.compile(
    r"^\s*benchproofer:compared\s+(?P<symbol>\S+)\s+(?P<inputs>\d+)\b",
    re.MULTILINE,
)
_DISAGREES = re.compile(r"^\s*benchproofer:disagrees\s+(?P<symbol>\S+).*$", re.MULTILINE)
_SEED = re.compile(r"^\s*benchproofer:seed\s+(?P<seed>\S+)", re.MULTILINE)
_UNSUPPORTED = re.compile(r"^\s*benchproofer:skipped\s+(?P<what>.+?)\s*$", re.MULTILINE)
_BLOCKED = re.compile(
    rf"^\s*benchproofer:(?:{'|'.join(map(re.escape, (BLOCKED, *ALIASES)))})\s+\S.*$",
    re.MULTILINE,
)
_EXCLUDED = re.compile(r"^\s*benchproofer:excluded\s+\S.*$", re.MULTILINE)
_WITNESS = re.compile(
    r"^\s*benchproofer:witness\s+(?P<symbol>\S+)\s+(?P<arguments>\S.*?)\s*$", re.MULTILINE
)
_REPLAYED = re.compile(
    r"^\s*benchproofer:rechecked\s+(?P<symbol>\S+)\s+(?P<inputs>\d+)\b", re.MULTILINE
)
_INADMISSIBLE = re.compile(
    r"^\s*benchproofer:inadmissible\s+(?P<symbol>\S+)\s+(?P<position>\d+)\b.*$",
    re.MULTILINE,
)
#: What the reason on an `excluded` or `inadmissible` line starts with for an input an
#: `Outside the bridge` entry names, as `conformance-rules.md` asks for it.
ANSWERED_BY = "Outside the bridge:"
#: How many words of an `Outside the bridge` entry such a reason has to quote to name it.
_ENTRY_WORDS = 5
#: What every protocol line starts with.
_PREFIX = "benchproofer:"
#: Any line starting with the prefix, with the word after it captured.
_PROTOCOL_LINE = re.compile(
    rf"^\s*(?P<prefix>{_PREFIX})(?P<word>[\w-]*).*$",
    re.MULTILINE,
)
#: Every pattern a protocol line is read by (see `unparsed`).
_READERS = (
    _COMPARED,
    _DISAGREES,
    _SEED,
    _UNSUPPORTED,
    _BLOCKED,
    _EXCLUDED,
    _WITNESS,
    _REPLAYED,
    _INADMISSIBLE,
)
_IMPORT_FROM = re.compile(
    r"^\s*from\s+(?P<module>[\w.]+)\s+import\s+(?P<names>[^#\n]+)", re.MULTILINE
)
#: A star import, which binds every public name of the module it names.
_STAR = re.compile(r"^\s*from\s+(?P<module>[\w.]+)\s+import\s+\*", re.MULTILINE)

#: Each protocol line's shape, keyed by the word after the prefix, exactly as the rules file
#: `conformance-rules.md` asks for it. Quoted back beside a line no reader parses.
SHAPES: dict[str, str] = {
    "compared": "benchproofer:compared <function> <how many inputs> <how they were drawn>",
    "disagrees": (
        "benchproofer:disagrees <function> <the input, what the repository did, what the "
        "implementation did>"
    ),
    "seed": "benchproofer:seed <the seed>",
    **{
        word: f"benchproofer:{word} <function> <the input>: <the error>"
        for word in ("unbuildable", "refused", "copy-raised")
    },
    "excluded": (
        "benchproofer:excluded <the input>: <the line of the specification stating the "
        "precondition>"
    ),
    "skipped": "benchproofer:skipped <the function>: <why>",
    "witness": "benchproofer:witness <function> <the arguments, as a Python tuple literal>",
    "rechecked": (
        "benchproofer:rechecked <function> <how many of the tuples handed to this file "
        "were compared>"
    ),
    "inadmissible": (
        "benchproofer:inadmissible <function> <its position in the list, from 0>: <why>"
    ),
}


def protocol_for(inputs: int, seconds: float = 600, *, ported: bool = False) -> str:
    """The rules `conformance.py` is held to, quoting this run's target and deadline.

    The shared rules file `conformance-rules.md`, which the conformance request and a repair
    session are both given.

    Args:
        inputs: How many inputs to aim at, from `conformance_inputs`.
        seconds: How long `conformance.py` may spend drawing them (`DEADLINE_SHARE`).
        ported: Whether the implementation is not Python, so `conformance.py` runs a port of it
            (`conformance-port.md`) rather than a copy (`conformance-copy.md`).
    """
    return SHARED.render(
        "conformance-rules",
        inputs=f"{max(1, inputs):,}",
        seconds=f"{max(1, int(seconds)):,}",
        copy=SHARED.render("conformance-port" if ported else "conformance-copy").rstrip(),
    ).rstrip()


@dataclass(frozen=True, slots=True)
class Comparison:
    """One function a run of `conformance.py` compared, and over how many inputs."""

    symbol: str
    inputs: int


def comparisons(output: str) -> tuple[Comparison, ...]:
    """What a run of `conformance.py` reported comparing, in order.

    A function compared in several passes, such as boundary inputs then generated ones,
    is counted once per pass.
    """
    return tuple(
        Comparison(symbol=match.group("symbol"), inputs=int(match.group("inputs")))
        for match in _COMPARED.finditer(output)
    )


def compared(output: str) -> int:
    """How many inputs a run of `conformance.py` reported comparing, over every function."""
    return sum(item.inputs for item in comparisons(output))


def seed(output: str) -> str:
    """The seed a `conformance.py` run reported drawing its inputs from, or "" if none.

    Recorded on the verdict rather than required: it makes a disagreement reproducible,
    but a run without one still shows agreement over the inputs it drew.
    """
    found = _SEED.search(output)
    return found.group("seed") if found else ""


def invented(harness: str, known: str, *, tree: Path | None = None) -> tuple[str, ...]:
    """Names `conformance.py` imports out of the repository that the task never mentions.

    Decidable before anything runs, and the usual way a `conformance.py` is dead on arrival: it
    imports a tidy function the specification was written around, while the repository
    keeps that logic inline. Only modules of the repository are judged, those whose dotted
    path the task ships or the tree has as a file, so `from random import randint` is not.
    A name may also come in through the module's star imports (`_starred`).

    Args:
        harness: The program to read imports from.
        known: Everything the task ships, as text (`material.citable`), with the files
            the fix touches after it.
        tree: The repository's working copy, when there is one. Then a module is read
            from the tree, and a module under the repository's own package that names no
            file there is itself invented.
    """
    unknown: list[str] = []
    for match in _IMPORT_FROM.finditer(harness):
        module = match.group("module")
        source = _module(tree, module) if tree is not None else None
        if source is None and not _shipped(module, known):
            if tree is not None and _packaged(tree, module):
                unknown.append(module)
            continue
        for name in _imported(match.group("names")):
            pattern = rf"\b{re.escape(name)}\b"
            if re.search(pattern, known) or (source and re.search(pattern, source)):
                continue
            # `from package import module` names a file, not something the package defines.
            if tree is not None and _module(tree, f"{module}.{name}") is not None:
                continue
            if tree is not None and source is not None and _starred(tree, module, pattern):
                continue
            unknown.append(f"{module}.{name}")
    return tuple(dict.fromkeys(unknown))


def _module(tree: Path, module: str) -> str | None:
    """The source of the file ``module`` names in ``tree``, or None when there is none."""
    path = _module_file(tree, module)
    return None if path is None else path.read_text(encoding="utf-8", errors="replace")


def _module_file(tree: Path, module: str) -> Path | None:
    """The file ``module`` names in ``tree``, or None when there is none."""
    path = tree / module.replace(".", "/")
    for candidate in (path.with_suffix(".py"), path / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _starred(tree: Path, module: str, pattern: str) -> bool:
    """Whether a name may come into ``module`` through its star imports, followed through.

    A star import out of a module the tree has no file for, such as the standard library
    or a dependency, may bring in anything, so it counts as bringing the name.
    """
    seen = {module}
    pending = [module]
    while pending:
        current = pending.pop()
        path = _module_file(tree, current)
        if path is None:
            return True
        text = path.read_text(encoding="utf-8", errors="replace")
        if current != module and re.search(pattern, text):
            return True
        for star in _STAR.finditer(text):
            target = _absolute(
                current, star.group("module"), package=path.name == "__init__.py"
            )
            if target not in seen:
                seen.add(target)
                pending.append(target)
    return False


def _absolute(module: str, target: str, *, package: bool) -> str:
    """The module a `from target import` in ``module`` names, relative dots resolved.

    ``package`` says ``module`` is a package's `__init__.py`, whose own name is the
    package one dot names.
    """
    level = len(target) - len(target.lstrip("."))
    if not level:
        return target
    parts = module.split(".")
    if not package:
        parts = parts[:-1]
    parts = parts[: max(0, len(parts) - (level - 1))]
    rest = target[level:]
    return ".".join([*parts, rest] if rest else parts)


def _packaged(tree: Path, module: str) -> bool:
    """Whether ``module`` is a dotted name under a top-level package of the repository."""
    top = module.split(".", 1)[0]
    return "." in module and (tree / top / "__init__.py").is_file()


def _shipped(module: str, known: str) -> bool:
    """Whether the task ships a file at the path ``module`` spells."""
    path = module.replace(".", "/")
    return f"{path}.py" in known or f"{path}/" in known


def _imported(clause: str) -> tuple[str, ...]:
    """The names an import clause binds, ignoring aliases and a trailing comment."""
    names = []
    for part in clause.replace("(", "").replace(")", "").split(","):
        name = part.strip().split(" as ")[0].strip()
        if name and name != "*":
            names.append(name)
    return tuple(names)


def unsupported(output: str) -> tuple[str, ...]:
    """What a run of `conformance.py` declared it could not compare.

    A declared gap is an explicit skip, so a `conformance.py` that compares only the part it can
    execute and exits zero is not read as agreement about the whole implementation.
    """
    return tuple(match.group("what").strip() for match in _UNSUPPORTED.finditer(output))


def blocked(output: str) -> tuple[str, ...]:
    """The inputs a run of conformance.py reported it did not compare, each line as printed.

    Neither a disagreement nor silently skipped, each leaves the comparison undecided, and
    its reason says why: the program could not build the value, the repository refuses it,
    or the program's copy of the implementation raised. A line in a word of `ALIASES` is
    read as one of these.
    """
    return tuple(match.group(0).strip() for match in _BLOCKED.finditer(output))


def answered(output: str) -> tuple[str, ...]:
    """The `excluded` and `inadmissible` lines a run printed with `ANSWERED_BY`, in order."""
    found = sorted(
        (match.start(), match.group(0).strip())
        for pattern in (_EXCLUDED, _INADMISSIBLE)
        for match in pattern.finditer(output)
    )
    return tuple(line for _, line in found if ANSWERED_BY in line)


def names_entry(line: str, entries: str) -> bool:
    """Whether ``line`` names one of ``entries`` after `ANSWERED_BY`.

    What follows the words has to be `_ENTRY_WORDS` or more of what ``entries`` says, the
    `Outside the bridge` section `gates.audit.entries_under` reads, whitespace aside and
    with a bullet, a quotation mark or a backtick around it taken off.
    """
    _, found, quoted = line.partition(ANSWERED_BY)
    quoted = " ".join(quoted.split()).strip("*-`'\" ")
    return (
        bool(found)
        and len(re.findall(r"\w+", quoted)) >= _ENTRY_WORDS
        and quoted in " ".join(entries.split())
    )


def excluded(output: str) -> tuple[str, ...]:
    """The inputs a `conformance.py` run set aside as a precondition excludes, as printed.

    Each names the line of the specification stating that precondition, which the gate
    looks for in the specification it judges.
    """
    return tuple(match.group(0).strip() for match in _EXCLUDED.finditer(output))


def unparsed(output: str) -> tuple[str, ...]:
    """The lines a `conformance.py` run printed for the protocol that no reader of it parses.

    A `benchproofer:` line in a shape no reader knows, such as a function name with spaces
    or a count in words, would otherwise be lost, reading a comparison as none and a
    disagreement as agreement. Returned as printed, to be quoted back verbatim. A line
    counts as read when a reader's match over the whole output begins at its prefix, so
    this and the readers cannot disagree about a line.
    """
    read = {
        match.start() + match.group(0).index(_PREFIX)
        for pattern in _READERS
        for match in pattern.finditer(output)
    }
    return tuple(
        match.group(0).strip()
        for match in _PROTOCOL_LINE.finditer(output)
        if match.start("prefix") not in read
    )


def shapes_for(line: str) -> tuple[str, ...]:
    """The shape the protocol gives ``line``, by the word after its prefix.

    A `BLOCKED` line has the shapes of the words that name its reason (`ALIASES`). Every
    shape when the protocol has no such word, since the line could be meant as any.
    """
    found = _PROTOCOL_LINE.match(line)
    word = found.group("word") if found else ""
    if word == BLOCKED:
        return tuple(SHAPES[alias] for alias in ALIASES)
    return (SHAPES[word],) if word in SHAPES else tuple(SHAPES.values())


def provenance(extension: str, impl: str = "", foreign: Sequence[str] = ()) -> str:
    """How far the comparison is from the implementation the checker accepted.

    `DIRECT` when `conformance.py` can carry the implementation with its annotations taken out;
    `TRANSLITERATED` when it has to carry a translation, because the repository cannot run
    the backend's language, or because a Python implementation uses the verifier's own
    values (Nagini's `PSeq`), which deleting contracts does not make runnable.

    Args:
        extension: The backend's solution-file extension.
        impl: The implementation region, for a backend whose language is Python.
        foreign: The backend's `foreign_tokens`.
    """
    if extension != ".py":
        return TRANSLITERATED
    return TRANSLITERATED if _names_any(impl, foreign) else DIRECT


def _names_any(source: str, foreign: Sequence[str]) -> bool:
    """Whether Python ``source`` uses one of ``foreign`` as a name in its code.

    Read off the tokenizer's NAME tokens, so spacing does not matter and comments (a
    Nagini ``# type: PSeq[int]``) and string literals do not count. A token is matched by
    the identifier it starts with (`ToSeq(` names `ToSeq`). Source the tokenizer refuses
    is searched as text, which errs towards a match.
    """
    tokens = python_tokens(source)
    if tokens is None:
        return any(token in source for token in foreign)
    used = {token.string for token in tokens if token.type == tokenize.NAME}
    return any(
        (found := _IDENTIFIER.match(token)) is not None and found.group() in used
        for token in foreign
    )


#: The identifier a foreign token starts with.
_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def executables(source: str, backend: Backend) -> dict[str, str]:
    """Each implementation region of a solution file with its annotations taken out.

    Keyed by region name, as the regions of `conformance.py` that carry them are.

    Raises:
        MarkerError: The file has no readable marker regions.
    """
    regions = parse(source, backend.comment)
    return {
        name: executable_view(regions[name].text, backend.annotation_tokens, backend.comment)
        for name in named(regions, REGION)
    }


def runs_as_written(source: str, backend: Backend) -> bool:
    """Whether every implementation region runs once its annotations are taken out.

    A submission that does is spliced into the bundle's `conformance.py`; one that does not
    (Lean, or Nagini returning a `PSeq`) can only be put to the benchmark as a repository patch.
    """
    try:
        bodies = executables(source, backend)
    except MarkerError:
        return False
    return bool(bodies) and all(
        provenance(backend.extension, body, backend.foreign_tokens) == DIRECT
        for body in bodies.values()
    )


def runs_in(harness: str | None, source: str, backend: Backend) -> bool:
    """`runs_as_written`, and `conformance.py` binds every name the implementation reads.

    A submission may call a solution-file helper the shipped implementation never used,
    and `conformance.py` carries only what the shipped one needs.
    """
    if not runs_as_written(source, backend):
        return False
    if harness is None:
        return True
    return not unbound(harness, executables(source, backend))


def unbound(harness: str, runnable: dict[str, str]) -> tuple[str, ...]:
    """Names the implementation reads that `conformance.py`, with it spliced in, never binds.

    Read off the spliced program's symbol table: globals a function reads that no
    module-level statement assigns or imports and that are not builtins, limited to names
    the implementation uses. A program with a star import, or that does not compile,
    reports nothing, since what it binds cannot be told.
    """
    spliced = substituted(harness, runnable)
    if spliced is None:
        return ()
    try:
        top = symtable.symtable(spliced, HARNESS, "exec")
        used = {
            node.id
            for body in runnable.values()
            for node in ast.walk(ast.parse(_as_function(body)))
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }
    except SyntaxError:
        return ()
    if "*" in spliced and re.search(r"^\s*from\s+\S+\s+import\s+\*", spliced, re.MULTILINE):
        return ()
    bound = {
        symbol.get_name()
        for symbol in top.get_symbols()
        if symbol.is_assigned() or symbol.is_imported()
    }
    free: set[str] = set()
    pending = list(top.get_children())
    while pending:
        table = pending.pop()
        pending.extend(table.get_children())
        free.update(
            symbol.get_name()
            for symbol in table.get_symbols()
            if symbol.is_global() and symbol.is_referenced()
        )
    return tuple(
        sorted(
            name
            for name in free & used
            if name not in bound and not hasattr(builtins, name) and name not in _MODULE_NAMES
        )
    )


#: Names every module has bound without assigning them.
_MODULE_NAMES = frozenset({"__file__", "__name__", "__doc__", "__spec__", "__loader__"})


def _as_function(body: str) -> str:
    """A function body, however it is indented, as a module the parser accepts."""
    lines = [line for line in body.splitlines() if line.strip()]
    depth = min((len(line) - len(line.lstrip()) for line in lines), default=0)
    return (
        "def _body():\n" + "\n".join("    " + line[depth:] for line in lines) + "\n    pass\n"
    )


def carried(harness: str) -> str | None:
    """The runnable implementation a `conformance.py` marks in its `impl` regions, or None.

    A marked `conformance.py` is one a reviewer's submission can be substituted into, so the
    submission is judged by the bundle's own comparison with only the implementation
    changed. A `conformance.py` that marks none is not defective, only not substitutable.
    """
    try:
        regions = parse(harness, COMMENT, required=())
    except MarkerError:
        return None
    return joined(regions, REGION) if named(regions, REGION) else None


def uncopied(
    harness: str, bodies: Mapping[str, str], *, skipped: Sequence[str] = ()
) -> tuple[str, str] | None:
    """Which `impl` region a `conformance.py` does not carry verbatim, and the line it lacks.

    Where the implementation runs as written, `impl.conformance` holds `conformance.py` to
    carrying each region's runnable form (`executables`), in order, in the regions it marks
    or, where it marks none, in the file. Naming the line spares a reader a diff. A region
    in ``skipped``, whose function the program reports it does not compare
    (`skipped_regions`), need not be carried.

    Returns:
        ``(region, line)`` for the first region not carried, the line stripped and ""
        when the region has no line of code to carry; None when every region is carried.
    """
    marked = carried(harness)
    whole = marked if marked is not None else harness
    for name, body in bodies.items():
        if name not in skipped and not contains_lines(whole, body):
            return name, uncarried(whole, body)
    return None


def skipped_regions(program: str, solution: str, comment: str) -> tuple[str, ...]:
    """The implementation regions whose function ``program`` reports, as written, as skipped.

    A region's function is the one its `spec` region, or the region itself, defines first
    (`spec.2` and `impl.2` for `impl.2`). The program reports it in a
    `benchproofer:skipped <the function>: <why>` line written out in its source, where
    `<the function>` is the region's name, or that function's name, alone, after a dotted
    path or with `shadow_` before it. Read off the source, so that the verbatim check made
    before any run can tell: an f-string is read as well where what it puts in is a
    module-level name bound to a string.
    """
    try:
        regions = parse(solution, comment, required=())
    except MarkerError:
        return ()
    functions: dict[str, set[str]] = {}
    for name in named(regions, REGION):
        suffix = name[len(REGION) :]
        functions[name] = {
            found.group(1)
            for region in (f"spec{suffix}", name)
            if region in regions
            for found in [_DEFINED.search(regions[region].text)]
            if found is not None
        }
    reported = set()
    for what in _reported_skips(program):
        first = what.split()[0].strip("`'\":,()") if what.split() else ""
        reported.add(first)
        reported.add(first.rsplit(".", 1)[-1].removeprefix("shadow_"))
    return tuple(
        name for name, defined in functions.items() if name in reported or defined & reported
    )


#: The name a region's first definition gives its function.
_DEFINED = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.MULTILINE)


def _reported_skips(program: str) -> list[str]:
    """What each `skipped` line written out in ``program``'s strings says it did not compare."""
    try:
        tree = ast.parse(program)
    except SyntaxError:
        return []
    bound = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    texts: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            texts.append(node.value)
        elif isinstance(node, ast.JoinedStr):
            texts.append(
                "".join(
                    str(value.value)
                    if isinstance(value, ast.Constant)
                    else bound.get(value.value.id, "\0")
                    if isinstance(value, ast.FormattedValue)
                    and isinstance(value.value, ast.Name)
                    else "\0"
                    for value in node.values
                )
            )
    return [match.group("what") for text in texts for match in _UNSUPPORTED.finditer(text)]


def lacking(missing: tuple[str, str]) -> str:
    """Say what `uncopied` found, as the clause that ends an objection to a `conformance.py`."""
    region, line = missing
    where = (
        f"the first line of the `{region}` region it lacks is `{line}`"
        if line
        else f"the `{region}` region has no line of code for it to contain"
    )
    return (
        f"{where}. The region holds that code exactly as written; a name it calls that "
        f"{HARNESS} defines under another name, such as another modeled function's shadow, is "
        "bound to that name outside the region rather than renamed inside it"
    )


def substituted(harness: str, runnable: dict[str, str]) -> str | None:
    """`harness` with the implementation it carries replaced by ``runnable``.

    ``runnable`` holds one body per implementation region, as `executables` returns them.
    None when `conformance.py` does not mark exactly those regions, since a body with nowhere
    to go, or a region still holding the drafter's code, would compare something other
    than the submission. Each body is re-indented to the region it replaces, since the
    `conformance.py`'s `def` and the solution's need not sit at the same depth.
    """
    try:
        regions = parse(harness, COMMENT, required=())
    except MarkerError:
        return None
    if not runnable or set(named(regions, REGION)) != set(runnable):
        return None
    lines = harness.splitlines()
    # From the last region up, so the line numbers of the ones above stay what they were.
    for name in sorted(runnable, key=lambda name: regions[name].start, reverse=True):
        region = regions[name]
        body = _reindented(runnable[name].strip("\n"), _indent(region.text))
        lines = lines[: region.start] + body + lines[region.end :]
    return "\n".join(lines).rstrip("\n") + "\n"


def _indent(block: str) -> int:
    """The indentation every line of ``block`` shares."""
    widths = [len(line) - len(line.lstrip()) for line in block.splitlines() if line.strip()]
    return min(widths) if widths else 0


def _reindented(block: str, depth: int) -> list[str]:
    """``block``'s lines, shifted so that its shallowest line sits at ``depth``."""
    shift = depth - _indent(block)
    return [
        (" " * shift + line if shift > 0 else line[-shift:]) if line.strip() else line
        for line in block.splitlines()
    ]


def ungrounded(output: str, harness: str) -> tuple[str, ...]:
    """The functions a run reported comparing that do not name repository code.

    Against a `conformance.py` that reimplements the behavior it should compare against, which
    agrees by construction. A genuine comparison names the function by its dotted path,
    and that path's module appears in the program. This does not show the repository's
    code ran, so it is a floor; the review is the argument.
    """
    reported = dict.fromkeys(item.symbol for item in comparisons(output))
    return tuple(symbol for symbol in reported if not _grounded(symbol, harness))


def _grounded(symbol: str, harness: str) -> bool:
    """Whether the module ``symbol`` is reached through appears in `conformance.py`.

    A method `package.module.Class.method` also counts when `package.module` and `Class`
    both appear, since a `conformance.py` imports the class out of its module.
    """
    if "." not in symbol:
        return False
    owner, _ = symbol.rsplit(".", 1)
    if owner in harness:
        return True
    if "." not in owner:
        return False
    module, cls = owner.rsplit(".", 1)
    return module in harness and re.search(rf"\b{re.escape(cls)}\b", harness) is not None


def disagreements(output: str) -> tuple[str, ...]:
    """The functions a run of `conformance.py` reported a disagreement on."""
    return tuple(dict.fromkeys(match.group("symbol") for match in _DISAGREES.finditer(output)))


def witnesses(output: str) -> tuple[int, tuple[str, ...]]:
    """How many disagreements a `conformance.py` run reported, and the first few as printed.

    Each line names the input and what each side did on it, which is what a repair reasons
    from; a long line is clipped rather than dropped.
    """
    lines = [match.group(0).strip() for match in _DISAGREES.finditer(output)]
    return len(lines), clipped(lines)


def arguments(text: str) -> str | None:
    """An argument tuple as the protocol prints it, spelled as the `repr` of its value.

    None when ``text`` is not a tuple literal `ast.literal_eval` reads back, since nothing else
    can be put to a `conformance.py` again. One spelling means one input printed two ways is
    stored once.
    """
    try:
        value = ast.literal_eval(text.strip())
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    return repr(value) if isinstance(value, tuple) else None


def witnessed(output: str) -> dict[str, tuple[str, ...]]:
    """The argument tuples a run of `conformance.py` printed `witness` lines for, by function.

    In the order printed, once each, and only those `arguments` reads back.
    """
    found: dict[str, list[str]] = {}
    for match in _WITNESS.finditer(output):
        kept = arguments(match.group("arguments"))
        if kept is not None and kept not in found.setdefault(match.group("symbol"), []):
            found[match.group("symbol")].append(kept)
    return {symbol: tuple(items) for symbol, items in found.items() if items}


def replayed(output: str) -> dict[str, int]:
    """How many tuples handed to it a `conformance.py` run reported comparing, by function."""
    counts: dict[str, int] = {}
    for match in _REPLAYED.finditer(output):
        symbol = match.group("symbol")
        counts[symbol] = counts.get(symbol, 0) + int(match.group("inputs"))
    return counts


def inadmissible(output: str) -> dict[str, dict[int, str]]:
    """The tuples a `conformance.py` run declared inadmissible, by function and position."""
    found: dict[str, dict[int, str]] = {}
    for match in _INADMISSIBLE.finditer(output):
        found.setdefault(match.group("symbol"), {})[int(match.group("position"))] = match.group(
            0
        ).strip()
    return found


def with_replay(harness: str, inputs: Mapping[str, Sequence[str]]) -> str:
    """`harness` as it is run with ``inputs`` to compare again.

    The inputs are assigned to `REPLAY` ahead of the program's own statements
    (`inserted`). Unchanged when there is nothing to hand it.
    """
    kept = {symbol: list(items) for symbol, items in inputs.items() if items}
    if not kept:
        return harness
    table = (
        "{"
        + ", ".join(f"{symbol!r}: [{', '.join(items)}]" for symbol, items in kept.items())
        + "}"
    )
    return inserted(harness, f"{REPLAY} = {table}")


def inserted(program: str, code: str) -> str:
    """``program`` with the one-line statement ``code`` run ahead of its own statements.

    After the module's docstring and its `from __future__` imports, which Python requires
    first, and on a line the program already has, so that each line a traceback names is
    the program's line as written: joined by `;` after the last of those, or ahead of the
    first statement when that is a simple one; on a line of its own, before it, only when
    the program opens with a compound statement. Unchanged when the program does not
    parse, since then the run fails on its own error.
    """
    try:
        body = ast.parse(program).body
    except SyntaxError:
        return program
    head: ast.stmt | None = None
    for number, node in enumerate(body):
        docstring = (
            number == 0
            and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        future = isinstance(node, ast.ImportFrom) and node.module == "__future__"
        if not (docstring or future):
            break
        head = node
    lines = program.splitlines(keepends=True)
    if head is not None:
        index = (head.end_lineno or head.lineno) - 1
        cut = _column(lines[index], head.end_col_offset or 0)
        lines[index] = f"{lines[index][:cut]}; {code}{lines[index][cut:]}"
        return "".join(lines)
    first = body[0] if body else None
    if first is None:
        return f"{program.rstrip()}\n{code}\n".lstrip("\n")
    # A compound statement, which holds others, is one no statement is joined ahead of.
    if not hasattr(first, "body") and not hasattr(first, "cases"):
        index = first.lineno - 1
        cut = _column(lines[index], first.col_offset)
        lines[index] = f"{lines[index][:cut]}{code}; {lines[index][cut:]}"
        return "".join(lines)
    decorators = getattr(first, "decorator_list", [])
    index = min([first.lineno, *(decorator.lineno for decorator in decorators)]) - 1
    return "".join([*lines[:index], f"{code}\n", *lines[index:]])


def _column(line: str, offset: int) -> int:
    """Where in ``line`` the UTF-8 byte ``offset`` the parser reports falls, in characters."""
    return len(line.encode()[:offset].decode(errors="ignore"))


def clipped(lines: Sequence[str], limit: int = WITNESSES) -> tuple[str, ...]:
    """The first ``limit`` of a run's report lines, each clipped to what a verdict quotes.

    Used for every kind of report line a verdict or a repair quotes.
    """
    return tuple(
        line if len(line) <= WITNESS_CHARS else f"{line[:WITNESS_CHARS]} ..."
        for line in lines[:limit]
    )
