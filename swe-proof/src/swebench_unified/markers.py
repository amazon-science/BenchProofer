# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Marker-region parsing and the consumer spec-view projection, dispatching on
the backend's LanguageTables (docs/architecture.md §2).

Regions are `<comment> <name>-start` / `<name>-end` line-comment pairs, legal
names from `tables.region_names`. Lean flavor: `imports-end` is a lone
sentinel, not a paired region; the lean backend has a `proof` region while
velvet's proofs are `prove_correct <name> by` blocks instead.

The **spec view** (what consumers see) replaces the impl regions (and the
nested invariants / proof regions / prove_correct bodies) with an elision
placeholder: signatures, contracts, axioms, pure helpers pass through; impl
and proof do not.

Entry points take LanguageTables (or the Backend) and dispatch on flavor, so a
new language is a table plus a `_<flavor>_*` helper set rather than a change
here.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .backends.base import LanguageTables

ELISION_IMPL = "implementation elided — supplied by the consumer"
ELISION_PROOF = "proof elided — supplied by the consumer"


def _tables(tables) -> LanguageTables:
    """Accept a LanguageTables or a Backend carrying one; fail loudly on
    anything else."""
    lang = getattr(tables, "language", None)
    if isinstance(lang, LanguageTables):
        return lang
    if isinstance(tables, LanguageTables):
        return tables
    raise TypeError(
        f"expected LanguageTables or a Backend carrying one, got {type(tables).__name__}")


def _marker_res(tables: LanguageTables) -> tuple[re.Pattern, re.Pattern]:
    c = re.escape(tables.comment_line)
    return (re.compile(rf"^(\s*){c}\s*([a-z-]+)-start\s*$"),
            re.compile(rf"^(\s*){c}\s*([a-z-]+)-end\s*$"))


@dataclass
class Regions:
    spans: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def get(self, name: str) -> list[tuple[int, int]]:
        return self.spans.get(name, [])

    @property
    def ok(self) -> bool:
        return not self.errors

    def covers(self, name: str, lineno: int) -> bool:
        return any(lo <= lineno <= hi for lo, hi in self.spans.get(name, []))


# ---------------------------------------------------------------------------
# parse_regions
# ---------------------------------------------------------------------------

def _python_parse_regions(src: str, tables: LanguageTables) -> Regions:
    """Python flavor (nagini model.py). Unknown region names are errors (both
    -start and -end); the -end marker's indent must match its -start."""
    region_names = tables.region_names
    start_re, end_re = _marker_res(tables)
    out = Regions()
    stack: list[tuple[str, int, str]] = []
    for i, line in enumerate(src.splitlines(), start=1):
        ms, me = start_re.match(line), end_re.match(line)
        if ms:
            indent, name = ms.group(1), ms.group(2)
            if name not in region_names:
                out.errors.append(f"line {i}: unknown region '{name}-start'")
            stack.append((name, i, indent))
        elif me:
            indent, name = me.group(1), me.group(2)
            if name not in region_names:
                out.errors.append(f"line {i}: unknown region '{name}-end'")
                continue
            if not stack:
                out.errors.append(f"line {i}: '{name}-end' with no open region")
                continue
            open_name, open_line, open_indent = stack.pop()
            if open_name != name:
                out.errors.append(
                    f"line {i}: '{name}-end' closes '{open_name}-start' (line {open_line})")
                continue
            if indent != open_indent:
                out.errors.append(
                    f"line {i}: '{name}-end' indent != its '{name}-start' (line {open_line})")
            out.spans.setdefault(name, []).append((open_line, i))
    for name, line, _ in stack:
        out.errors.append(f"line {line}: '{name}-start' never closed")
    # axioms/pure are module-level singletons; per-function regions REPEAT
    # (one set per implemented function — multi-site changes).
    for name in ("axioms", "pure"):
        if len(out.spans.get(name, [])) > 1:
            out.errors.append(f"region '{name}' appears more than once")
    # every contracted function needs a matching pre/post pair.
    if (out.spans.get("impl") and
            len(out.spans.get("pre-conditions", [])) != len(out.spans.get("post-conditions", []))):
        out.errors.append("pre-conditions / post-conditions region counts differ")
    for name in out.spans:
        out.spans[name].sort()
    return out


def _lean_parse_regions(src: str, tables: LanguageTables) -> Regions:
    """Lean flavor (velvet + lean). Unknown -end names are lone sentinels
    (`imports-end`), ignored quietly; no indent check.

    Count checks are keyed on the region table: with a `proof` region (lean),
    post-conditions/impl/proof counts must agree per modeled function and
    pre-conditions is optional (preconditions live in the `correct_<name>`
    binder). Without one (velvet), pre/post must pair as in python flavor."""
    region_names = tables.region_names
    start_re, end_re = _marker_res(tables)
    out = Regions()
    stack: list[tuple[str, int, str]] = []
    for i, line in enumerate(src.splitlines(), start=1):
        ms, me = start_re.match(line), end_re.match(line)
        if ms:
            indent, name = ms.group(1), ms.group(2)
            if name not in region_names:
                out.errors.append(f"line {i}: unknown region '{name}-start'")
            stack.append((name, i, indent))
        elif me:
            indent, name = me.group(1), me.group(2)
            if name not in region_names:
                continue  # lone sentinel (`imports-end` etc.)
            if not stack:
                out.errors.append(f"line {i}: '{name}-end' with no open region")
                continue
            open_name, open_line, open_indent = stack.pop()
            if open_name != name:
                out.errors.append(
                    f"line {i}: '{name}-end' closes '{open_name}-start' (line {open_line})")
                continue
            out.spans.setdefault(name, []).append((open_line, i))
    for name, line, _ in stack:
        out.errors.append(f"line {line}: '{name}-start' never closed")
    # axioms/pure are singletons; per-method regions may repeat (multi-site).
    for name in ("axioms", "pure"):
        if len(out.spans.get(name, [])) > 1:
            out.errors.append(f"region '{name}' appears more than once")
    if "proof" in region_names:
        if out.spans.get("impl"):
            n_impl = len(out.spans["impl"])
            n_post = len(out.spans.get("post-conditions", []))
            if n_post and n_post != n_impl:
                out.errors.append("post-conditions / impl region counts differ")
            n_proof = len(out.spans.get("proof", []))
            if n_proof and n_proof != n_impl:
                out.errors.append("impl / proof region counts differ")
            n_pre = len(out.spans.get("pre-conditions", []))
            if n_pre and n_pre > n_impl:
                out.errors.append("more pre-conditions regions than impl regions")
    else:
        if (out.spans.get("impl") and
                len(out.spans.get("pre-conditions", []))
                != len(out.spans.get("post-conditions", []))):
            out.errors.append("pre-conditions / post-conditions region counts differ")
    for name in out.spans:
        out.spans[name].sort()
    return out


def parse_regions(src: str, tables) -> Regions:
    t = _tables(tables)
    if t.flavor == "python":
        return _python_parse_regions(src, t)
    if t.flavor == "lean":
        return _lean_parse_regions(src, t)
    if t.flavor == "ears":
        # Natural-language requirements: no marker regions exist by design.
        return Regions()
    raise ValueError(f"unknown language flavor {t.flavor!r}")


def region_text(src: str, name: str, tables) -> str:
    lines = src.splitlines()
    chunks = []
    for lo, hi in parse_regions(src, tables).get(name):
        chunks.append("\n".join(lines[lo:hi - 1]))  # exclude marker lines
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# spec_view
# ---------------------------------------------------------------------------

def _python_spec_view(src: str, tables: LanguageTables) -> str:
    """model.py with every impl region (nested invariants included) replaced
    by an elision placeholder. Deterministic + idempotent."""
    c = tables.comment_line
    regions = _python_parse_regions(src, tables)
    impl_spans = regions.get("impl")
    if not impl_spans:
        return src
    lines = src.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    span_by_start = {lo: hi for lo, hi in impl_spans}
    while i < n:
        lineno = i + 1
        if lineno in span_by_start:
            hi = span_by_start[lineno]
            m = re.match(r"^(\s*)", lines[i])
            indent = m.group(1) if m else "    "
            out.append(f"{indent}{c} impl-start")
            out.append(f"{indent}...  {c} {ELISION_IMPL}")
            out.append(f"{indent}{c} impl-end")
            i = hi
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out) + ("\n" if src.endswith("\n") else "")


_PROVE_RE = re.compile(r"^(\s*)prove_correct\b")


def _elide_prove_correct(lines: list[str], comment: str) -> list[str]:
    """(Velvet.) Elide each `prove_correct <name> by` body: everything after
    the header line up to the next non-indented line."""
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        m = _PROVE_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        # keep the header (obligation signature), elide the tactic body
        out.append(lines[i])
        out.append(m.group(1) + f"  {comment} {ELISION_PROOF}")
        i += 1
        while i < n:
            ln = lines[i]
            if ln and not ln[0].isspace() and not ln.lstrip().startswith(comment):
                break
            i += 1
    return out


def _lean_spec_view(src: str, tables: LanguageTables) -> str:
    """Solution.lean spec view, keyed on the region table. Lean backend
    (`proof` region): impl AND proof regions collapse to placeholders — the
    whole `proof` region including the `theorem correct_<name>` header, which
    would only echo symbols the spec view already shows. Velvet: impl regions
    collapse and `prove_correct` bodies are elided (header kept — it is the
    obligation signature). Deterministic + idempotent."""
    c = tables.comment_line
    regions = _lean_parse_regions(src, tables)
    lines = src.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    if "proof" in tables.region_names:
        elision = {"impl": ELISION_IMPL, "proof": ELISION_PROOF}
        span_by_start: dict[int, str] = {}
        span_end: dict[int, int] = {}
        for name in ("impl", "proof"):
            for lo, hi in regions.get(name):
                span_by_start[lo] = name
                span_end[lo] = hi
        while i < n:
            lineno = i + 1
            if lineno in span_by_start:
                name = span_by_start[lineno]
                hi = span_end[lineno]
                m = re.match(r"^(\s*)", lines[i])
                indent = m.group(1) if m else ""
                out.append(f"{indent}{c} {name}-start")
                out.append(f"{indent}{c} {elision[name]}")
                out.append(f"{indent}{c} {name}-end")
                i = hi
            else:
                out.append(lines[i])
                i += 1
    else:
        span_by_start = {lo: hi for lo, hi in regions.get("impl")}
        while i < n:
            lineno = i + 1
            if lineno in span_by_start:
                hi = span_by_start[lineno]
                m = re.match(r"^(\s*)", lines[i])
                indent = m.group(1) if m else "    "
                out.append(f"{indent}{c} impl-start")
                out.append(f"{indent}{c} {ELISION_IMPL}")
                out.append(f"{indent}{c} impl-end")
                i = hi
            else:
                out.append(lines[i])
                i += 1
        out = _elide_prove_correct(out, c)
    return "\n".join(out) + ("\n" if src.endswith("\n") else "")


def spec_view(src: str, tables) -> str:
    t = _tables(tables)
    if t.flavor == "python":
        return _python_spec_view(src, t)
    if t.flavor == "lean":
        return _lean_spec_view(src, t)
    if t.flavor == "ears":
        # The whole requirements document IS the spec — nothing to elide, so
        # spec_view is the identity and same_spec degrades to normalized
        # whole-file equality (via spec_signature).
        return src
    raise ValueError(f"unknown language flavor {t.flavor!r}")


# ---------------------------------------------------------------------------
# derived views (identical across flavors)
# ---------------------------------------------------------------------------

def spec_signature(src: str, tables) -> str:
    """Canonical string of everything constituting the SPEC (spec_view minus
    blank lines). Equal signatures = identical specification, making 'same
    spec, different impl' enforceable and contract changes detectable."""
    view = spec_view(src, tables)
    return "\n".join(ln.rstrip() for ln in view.splitlines() if ln.strip())


def same_spec(a: str, b: str, tables) -> bool:
    return spec_signature(a, tables) == spec_signature(b, tables)


def region_hashes(src: str, tables) -> dict[str, str]:
    t = _tables(tables)
    out: dict[str, str] = {}
    for name in t.region_names:
        txt = region_text(src, name, t)
        if txt:
            out[name] = hashlib.sha256(txt.encode()).hexdigest()
    out["spec_view"] = hashlib.sha256(spec_view(src, t).encode()).hexdigest()
    return out
