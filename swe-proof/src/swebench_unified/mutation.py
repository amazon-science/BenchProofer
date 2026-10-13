# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""First-order mutation of the impl region (G-MUT — a sanity check, NOT a
correctness proof; docs/architecture.md §5), dispatching on LanguageTables.

Mutates ONLY the impl region (never spec/proof/invariants), one token per
mutant. A surviving mutant (still verifies) means the spec is too weak there.
G-MUT is a floor, not a ceiling: assignment-only impls yield few mutants, and
lean-flavor proof-search incompleteness means a mutant may fail to verify for
reasons unrelated to incorrectness; G-PANEL is the real spec-strength check.

Flavors: python — tokenize scan, verifier-directive lines excluded,
stride-sampled to the cap; lean — regex scan per line, comment/invariant/
decreasing/done_with lines excluded, first-`cap` mutants. Each flavor's
exclusions are the lines a mutation could not make incorrect, so a mutant
landing there would be noise rather than evidence -- see _PY_DIRECTIVE for what
that noise measured on this corpus before the python flavor enforced it.
"""
from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass

from .backends.base import LanguageTables
from .markers import _tables, parse_regions

# ---- python flavor operator tables ----------------------------------------
_PY_OP = {"+": ["-"], "-": ["+"], "*": ["//"], "//": ["*"],
          "<": ["<=", ">"], "<=": ["<", "=="], ">": [">=", "<"], ">=": [">", "=="],
          "==": ["!="], "!=": ["=="]}
_PY_KW = {"and": ["or"], "or": ["and"], "True": ["False"], "False": ["True"]}

# ---- lean flavor operator tables --------------------------------------------
_LEAN_OP = {
    "+": ["-"], "-": ["+"], "*": ["/"], "/": ["*"],
    "<": ["≤", ">"], "≤": ["<", "="], ">": ["≥", "<"], "≥": [">", "="],
    "<=": ["<", "=="], ">=": [">", "=="],
    "=": ["≠"], "==": ["!="], "≠": ["="], "!=": ["=="],
    "∧": ["∨"], "∨": ["∧"], "&&": ["||"], "||": ["&&"],
    "++": [" "],  # drop a concat
}
_LEAN_KW = {"true": ["false"], "false": ["true"], "True": ["False"], "False": ["True"]}
_LEAN_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+|≤|≥|≠|∧|∨|\+\+|<=|>=|==|!=|&&|\|\||[-+*/<>=]")


@dataclass
class Mutant:
    index: int
    lineno: int
    description: str
    source: str


def _impl_only_linenos(src: str, tables: LanguageTables) -> set[int]:
    """1-based line numbers eligible for mutation: inside an impl region
    (marker lines excluded), outside any invariants region."""
    regions = parse_regions(src, tables)
    keep: set[int] = set()
    for lo, hi in regions.get("impl"):
        keep.update(range(lo + 1, hi))  # exclude marker lines
    for lo, hi in regions.get("invariants"):
        for ln in range(lo, hi + 1):
            keep.discard(ln)
    return keep


# ---------------------------------------------------------------------------
# python flavor (nagini model.py)
# ---------------------------------------------------------------------------

def _py_is_int_literal(t: str) -> bool:
    try:
        int(t)
        return True
    except ValueError:
        return False


def _py_candidates(src: str, allowed: set[int]):
    readline = io.BytesIO(src.encode()).readline
    for tok in tokenize.tokenize(readline):
        if tok.start[0] not in allowed or tok.start[0] != tok.end[0]:
            continue
        t = tok.string
        if tok.type == tokenize.OP and t in _PY_OP:
            yield (tok.start[0], tok.start[1], tok.end[1], t, _PY_OP[t])
        elif tok.type == tokenize.NAME and t in _PY_KW:
            yield (tok.start[0], tok.start[1], tok.end[1], t, _PY_KW[t])
        elif tok.type == tokenize.NUMBER and _py_is_int_literal(t):
            n = int(t)
            yield (tok.start[0], tok.start[1], tok.end[1], t, [str(n + 1), str(n - 1)])


# Nagini statements that direct the VERIFIER rather than compute anything: a
# proof hint, a permission fold, a loop invariant. Mutating one cannot make an
# implementation incorrect, which is the property this whole gate is asking
# about, so a mutant landing there is noise in both directions:
#
#   killed    -- the mutated hint became unprovable, so the mutant dies for a
#               reason that has nothing to do with the spec. That is a FREE KILL
#               padding the rate, and the padding is not small: 1732 of this
#               corpus's mutants are of this kind, and on five cells every
#               single mutant was, so G-MUT's pass rested on no behavioural
#               evidence at all.
#   survivor  -- the mutated hint still happened to be provable, and the gate
#               reports "the spec admits a wrong implementation" about a program
#               whose behaviour is identical to the gold's.
#   no verdict-- the solver grinds on an obligation the impl never needed, and
#               the cell reds on a cap. Six of the seven undecided mutants that
#               held pylint-6386 red were mutated `Assert`s.
#
# The module has claimed this exclusion since it was written ("never spec/proof/
# invariants", and "each flavor's exclusions are the lines a mutation could not
# make incorrect"), and the lean flavor implements it by line kind below. The
# python flavor only ever implemented the INVARIANTS half of it, and only
# through `# invariants-begin/end` markers -- so on a bundle whose invariants sit
# outside a marked region the exclusion silently did not apply, which is how
# pylint-4604 came to have eight `Invariant(...)` mutants. Matching on the
# statement keyword needs no markers and cannot be defeated by their absence.
_PY_DIRECTIVE = re.compile(
    r"\s*(Assert|Assume|Invariant|Fold|Unfold|Refute|Requires|Ensures)\s*\(")


def _py_directive_linenos(src: str) -> set[int]:
    """1-based lines whose statement directs the verifier and computes nothing.

    A directive's arguments may span lines, so the continuation lines are
    excluded too: they hold the same tokens for the same reason, and a mutant on
    the second line of a two-line `Assert` is no more evidence than one on the
    first. Continuation is detected by paren depth rather than by indentation,
    since a wrapped invariant is often indented past its own keyword.
    """
    out: set[int] = set()
    depth = 0
    for lineno, line in enumerate(src.splitlines(), start=1):
        if depth > 0 or _PY_DIRECTIVE.match(line):
            out.add(lineno)
            # Comments and string literals are not tracked: a paren inside
            # either would misalign the depth. Neither appears inside a Nagini
            # contract call in this corpus, and the failure mode is bounded --
            # a stray depth excludes lines, which loses mutants rather than
            # admitting bad ones.
            code = line.split("#", 1)[0]
            depth += code.count("(") - code.count(")")
            depth = max(0, depth)
    return out


def _py_splice(src: str, lineno: int, c0: int, c1: int, new: str) -> str:
    lines = src.splitlines(keepends=True)
    line = lines[lineno - 1]
    nl = ""
    if line.endswith("\r\n"):
        body, nl = line[:-2], "\r\n"
    elif line.endswith("\n"):
        body, nl = line[:-1], "\n"
    else:
        body = line
    lines[lineno - 1] = body[:c0] + new + body[c1:] + nl
    return "".join(lines)


def _python_generate_mutants(src: str, tables: LanguageTables, cap: int) -> list[Mutant]:
    allowed = _impl_only_linenos(src, tables) - _py_directive_linenos(src)
    raw = []
    for ln, c0, c1, text, repls in _py_candidates(src, allowed):
        for r in repls:
            raw.append((ln, c0, c1, text, r))
    raw.sort(key=lambda t: (t[0], t[1], t[4]))
    if cap and len(raw) > cap:
        stride = len(raw) / cap
        raw = [raw[int(i * stride)] for i in range(cap)]
    out = []
    for i, (ln, c0, c1, text, r) in enumerate(raw):
        m = _py_splice(src, ln, c0, c1, r)
        if m != src:
            out.append(Mutant(i, ln, f"line {ln}: '{text}' -> '{r}'", m))
    return out


# ---------------------------------------------------------------------------
# lean flavor (velvet + lean Solution.lean)
# ---------------------------------------------------------------------------

def _lean_comment_linenos(src: str) -> set[int]:
    """1-based line numbers wholly inside a Lean comment (block/doc/module
    comments incl. nesting, plus whole-line `--`) — mutating these is a
    text-only no-op that always "survives"."""
    lines = src.splitlines()
    comment: set[int] = set()
    depth = 0
    for lineno, line in enumerate(lines, start=1):
        if depth > 0:
            comment.add(lineno)
        i = 0
        n = len(line)
        line_had_code = depth == 0
        while i < n - 1:
            two = line[i:i + 2]
            if depth == 0 and two == "--":
                break  # rest of line is a line comment
            if two == "/-":
                depth += 1
                comment.add(lineno)
                i += 2
                continue
            if two == "-/" and depth > 0:
                depth -= 1
                i += 2
                continue
            i += 1
        _ = line_had_code
    return comment


def _lean_is_int_literal(t: str) -> bool:
    return t.isdigit()


def _lean_generate_mutants(src: str, tables: LanguageTables, cap: int) -> list[Mutant]:
    lines = src.splitlines()
    # never mutate comment lines: prose-only mutants trivially "survive" —
    # a false spec-weakness signal.
    allowed = _impl_only_linenos(src, tables) - _lean_comment_linenos(src)
    mutants: list[Mutant] = []
    idx = 0
    for lineno in sorted(allowed):
        if lineno > len(lines):
            continue
        line = lines[lineno - 1]
        stripped = line.strip()
        # skip spec-ish clause lines
        if stripped.startswith(("invariant", "done_with", "decreasing", "--")):
            continue
        for m in _LEAN_TOKEN_RE.finditer(line):
            tok = m.group(0)
            repls: list[str] = []
            if tok in _LEAN_OP:
                repls = _LEAN_OP[tok]
            elif tok in _LEAN_KW:
                repls = _LEAN_KW[tok]
            elif _lean_is_int_literal(tok):
                n = int(tok)
                repls = [str(n + 1)] + ([str(n - 1)] if n > 0 else [])
            for r in repls:
                new_line = line[:m.start()] + r + line[m.end():]
                if new_line == line:
                    continue
                new_lines = list(lines)
                new_lines[lineno - 1] = new_line
                desc = f"L{lineno}: {tok!r}->{r!r} ({stripped[:40]})"
                mutants.append(Mutant(idx, lineno, desc, "\n".join(new_lines) +
                                      ("\n" if src.endswith("\n") else "")))
                idx += 1
                if len(mutants) >= cap:
                    return mutants
    return mutants


def generate_mutants(src: str, tables, cap: int = 20) -> list[Mutant]:
    t = _tables(tables)
    if t.flavor == "python":
        return _python_generate_mutants(src, t, cap)
    if t.flavor == "lean":
        return _lean_generate_mutants(src, t, cap)
    raise ValueError(f"unknown language flavor {t.flavor!r}")
