# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Anti-leakage screen (G-LEAK) for the consumer spec view, dispatching on
LanguageTables (docs/architecture.md §2, §5).

The spec view must not reveal the gold edit. Rules (each backend's
`prompts/<backend>/spec_guide.md` §0.6): no gold-diff line reproduced, no diff
markers, no patched file path, no spec-view identifier echoing a patched repo
symbol, no bug/fix narration. Leakage is judged against the SOLVER-VISIBLE
problem_statement ONLY, never hints_text: a term that appears only in the hints
is not something the solver can see, so screening against it would excuse an
identifier that does leak.

Flavors: python — AST identifiers, tokenize comments/strings, full diff-marker
set, trivial gold signature fragments excluded; lean — lightweight lexing for
identifiers/comments, "--- " excluded from diff markers because Lean line
comments start with `--`.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field

from unidiff import PatchSet

from .backends.base import LanguageTables
from .markers import _marker_res, _tables, spec_view

_NARRATION = (
    "bug", "buggy", "fix", "fixed", "fixes", "patch", "patched", "pre-patch",
    "prepatch", "post-patch", "postpatch", "regression", "previously",
    "incorrectly", "wrong", "broken", "off-by-one", "off by one",
)
_NARRATION_RE = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(w) for w in _NARRATION) + r")(?![\w-])",
    re.IGNORECASE)
_PY_DIFF_MARKERS = ("@@", "diff --git", "+++ ", "--- ", "\nindex ")
# "--- " excluded: Lean line comments start with "--".
_LEAN_DIFF_MARKERS = ("@@", "diff --git", "+++ ", "\nindex ")
_LEAN_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")


@dataclass
class LeakageReport:
    hard_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.hard_failures


def _normalize_code(s: str) -> str:
    return re.sub(r"\s+", "", s)


# Def/class names that are non-distinctive — they localize no edit, so a
# spec-view identifier or changed-line collision with one of them is a lexer
# false positive, not a leak. Shared by the symbol-collision check
# (_patch_changed_symbols) AND the changed-line check (_is_trivial_code_fragment)
# so both gates stay locked to one policy.
_COMMON_NONDISTINCTIVE = {"__init__", "__new__", "__call__", "__eq__", "__ne__",
                          "main", "self"}

# Content-free fragments a multi-line gold signature can emit as changed lines
# (e.g. a bare ") -> bool:"): they collide with any spec function sharing the
# return type, so they don't count as a reproduced gold line. (python only.)
_TRIVIAL_RETURN_RE = re.compile(r"^\)+->[A-Za-z_][\w\[\],.]*:?$")
# The bare opener of a multi-line method signature (`def <name>(`) whose name is
# non-distinctive per _COMMON_NONDISTINCTIVE (e.g. `def __init__(`). When a gold
# hunk and a spec model both split such a signature across lines, the bare
# `def __init__(` prefix collides even though it carries no edit-localization —
# a lexer false positive. Tied to the SAME allowlist as the symbol check so a
# distinctive dunder (e.g. `__reduce_ex__`) is NOT exempted.
_BARE_DEF_HEAD_RE = re.compile(r"^def([A-Za-z_][A-Za-z0-9_]*)\($")


def _is_trivial_code_fragment(cn: str) -> bool:
    if _TRIVIAL_RETURN_RE.match(cn):
        return True
    m = _BARE_DEF_HEAD_RE.match(cn)
    return bool(m and m.group(1) in _COMMON_NONDISTINCTIVE)


def _patch_changed_files(patch: str) -> list[str]:
    files = []
    for f in PatchSet(patch):
        for p in (f.source_file, f.target_file):
            if p and p != "/dev/null":
                files.append(p[2:] if p[:2] in ("a/", "b/") else p)
    return files


def _patch_changed_lines(patch: str) -> list[str]:
    out = []
    for f in PatchSet(patch):
        for hunk in f:
            for line in hunk:
                if line.is_added or line.is_removed:
                    s = line.value.strip()
                    if s:
                        out.append(s)
    return out


def _patch_changed_symbols(patch: str) -> set[str]:
    """Distinctive def/class names the patch touches, underscore-stripped,
    len>=4 — a spec-view identifier embedding one leaks edit-localization."""
    names: set[str] = set()
    defclass = re.compile(r"(?<![\w])(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")
    # (?<![\w]) so prose like "Subclass that ..." in a comment cannot match its
    # "class that" tail and screen an English word as a leaked symbol.
    for f in PatchSet(patch):
        for hunk in f:
            for m in defclass.finditer(getattr(hunk, "section_header", "") or ""):
                names.add(m.group(1))
            for line in hunk:
                if line.is_added or line.is_removed:
                    for m in defclass.finditer(line.value):
                        names.add(m.group(1))
    out = set()
    for n in names:
        if n in _COMMON_NONDISTINCTIVE:
            continue
        s = n.strip("_")
        if len(s) >= 4:
            out.add(s)
    return out


# ---------------------------------------------------------------------------
# python flavor lexing (nagini model.py)
# ---------------------------------------------------------------------------

def _py_comment_and_string_text(src: str) -> list[tuple[int, str]]:
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                out.append((tok.start[0], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        for i, line in enumerate(src.splitlines(), 1):
            if "#" in line:
                out.append((i, line[line.index("#"):]))
    return out


def _py_spec_view_identifiers(src: str) -> set[str]:
    names: set[str] = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
            for a in node.args.args + node.args.kwonlyargs:
                names.add(a.arg)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names


# ---------------------------------------------------------------------------
# lean flavor lexing (velvet + lean Solution.lean)
# ---------------------------------------------------------------------------

def _lean_strip_comments_collect(src: str) -> tuple[str, list[tuple[int, str]]]:
    """Return (code-without-comments, [(lineno, comment_text)]) for Lean
    source (`--` line comments, possibly-nested `/- -/` blocks)."""
    comments: list[tuple[int, str]] = []
    code_chars: list[str] = []
    i, n = 0, len(src)
    line = 1
    depth = 0
    block_start_line = 0
    block_buf: list[str] = []
    while i < n:
        ch = src[i]
        two = src[i:i + 2]
        if depth > 0:
            if two == "/-":
                depth += 1
                block_buf.append(two)
                i += 2
                continue
            if two == "-/":
                depth -= 1
                block_buf.append(two)
                i += 2
                if depth == 0:
                    comments.append((block_start_line, "".join(block_buf)))
                    block_buf = []
                continue
            if ch == "\n":
                line += 1
            block_buf.append(ch)
            i += 1
            continue
        if two == "/-":
            depth = 1
            block_start_line = line
            block_buf = [two]
            i += 2
            continue
        if two == "--":
            j = src.find("\n", i)
            if j == -1:
                j = n
            comments.append((line, src[i:j]))
            i = j
            continue
        if ch == "\n":
            line += 1
        code_chars.append(ch)
        i += 1
    return "".join(code_chars), comments


def _lean_spec_view_identifiers(code_no_comments: str) -> set[str]:
    return set(_LEAN_IDENT_RE.findall(code_no_comments))


# ---------------------------------------------------------------------------
# ears flavor (requirements.md — test-leak oriented)
# ---------------------------------------------------------------------------

def _patch_new_symbols(patch: str) -> set[str]:
    """Def/class names INTRODUCED by the patch (added lines only, minus names
    that already existed in removed lines / hunk section headers). For a
    natural-language spec, naming the touched function is legitimate and
    expected (the generator is told to localize); only names the FIX invents
    leak the edit."""
    defclass = re.compile(r"(?<![\w])(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")
    # (?<![\w]) so prose like "Subclass that ..." in a comment cannot match its
    # "class that" tail and screen an English word as a leaked symbol.
    added: set[str] = set()
    existing: set[str] = set()
    for f in PatchSet(patch):
        for hunk in f:
            for m in defclass.finditer(getattr(hunk, "section_header", "") or ""):
                existing.add(m.group(1))
            for line in hunk:
                names = {m.group(1) for m in defclass.finditer(line.value)}
                if line.is_added:
                    added |= names
                elif line.is_removed or line.is_context:
                    existing |= names
    out = set()
    for n in added - existing:
        if n in _COMMON_NONDISTINCTIVE:
            continue
        if len(n.strip("_")) >= 4:
            out.add(n)
    return out


_IDS_KWARG_RE = re.compile(r"\bids\s*=\s*[\[\(]([^\]\)]*)", re.DOTALL)
_STR_LIT_RE = re.compile(r"""["']([^"']{4,})["']""")


def _test_param_ids(test_patch: str) -> set[str]:
    """Explicit pytest parametrization ids introduced by the test patch: string
    literals inside an `ids=[...]` kwarg on ADDED lines. Deliberately narrow —
    parametrize ARGVALUES are often legitimate behavioral values a requirements
    document must be free to state; only the explicit id labels are
    test-identity, never behavior."""
    added = "\n".join(ln for ln in _patch_changed_lines(test_patch)
                      if ln)  # changed_lines already strips +/- context
    out: set[str] = set()
    for m in _IDS_KWARG_RE.finditer(added):
        out |= {s for s in _STR_LIT_RE.findall(m.group(1))}
    return out


def _ears_screen(doc: str, gold_patch: str, test_patch: str,
                 problem_statement: str) -> LeakageReport:
    """The whole requirements.md is the spec view (nothing elided). The screen
    is TEST-leak oriented (the ears generator's hard rule: never quote test
    code, test file paths, test names, or parametrization ids) plus the
    gold-edit checks that still apply to prose: no verbatim gold/test code
    lines, no diff markers, no fix-invented identifiers. Repo-symbol mentions
    and narration are NOT banned — an EARS document legitimately names the
    modules/functions involved and describes the problem."""
    rep = LeakageReport()
    doc_norm = _normalize_code(doc)
    problem = problem_statement or ""
    problem_norm = _normalize_code(problem)
    problem_l = problem.lower()

    # markdown uses `---` horizontal rules, so use the lean marker set
    # (excludes "--- "); quoting a diff in a requirements doc is a leak.
    for marker in _LEAN_DIFF_MARKERS:
        if marker in doc:
            rep.hard_failures.append(f"L1: diff marker {marker!r} in requirements.md")

    def _word_in_doc(sym: str) -> bool:
        return re.search(rf"(?<![\w]){re.escape(sym)}(?![\w])", doc,
                         re.IGNORECASE) is not None

    # verbatim code lines reproduced (gold + tests), unless the issue itself
    # already shows that line (public); len>=16 normalized — prose does not
    # normalize-match code by accident at that length.
    for label, patch in (("gold-patch", gold_patch), ("test-patch", test_patch)):
        if not patch:
            continue
        try:
            changed = _patch_changed_lines(patch)
        except Exception:  # unparseable patch text — nothing to screen against
            continue
        for cl in changed:
            cn = _normalize_code(cl)
            if len(cn) >= 16 and cn in doc_norm and cn not in problem_norm:
                rep.hard_failures.append(
                    f"L1: {label} line reproduced in requirements.md: {cl[:90]!r}")

    if test_patch:
        try:
            test_files = _patch_changed_files(test_patch)
            test_syms = _patch_changed_symbols(test_patch)
        except Exception:
            test_files, test_syms = [], set()
        for path in test_files:
            if path and path in doc:
                rep.hard_failures.append(
                    f"L2: test file path {path!r} named in requirements.md")
        for sym in sorted(test_syms):
            if sym.lower() in problem_l:
                continue  # already public via the issue
            if _word_in_doc(sym):
                rep.hard_failures.append(
                    f"L4: hidden-test symbol {sym!r} named in requirements.md "
                    f"— translate what the test checks into a behavioral "
                    f"requirement instead")
        try:
            param_ids = _test_param_ids(test_patch)
        except Exception:
            param_ids = set()
        for pid in sorted(param_ids):
            if pid.lower() in problem_l:
                continue
            if _word_in_doc(pid):
                rep.hard_failures.append(
                    f"L4: pytest parametrization id {pid!r} named in "
                    f"requirements.md — an id labels a test case, not a "
                    f"behavior")

    for sym in sorted(_patch_new_symbols(gold_patch)):
        if sym.lower() in problem_l:
            continue
        if _word_in_doc(sym):
            rep.hard_failures.append(
                f"L5: fix-introduced identifier {sym!r} named in "
                f"requirements.md — describe the behavior, not the edit")
    return rep


# ---------------------------------------------------------------------------
# a relaxation may not instruct the reviewer who judges it
# ---------------------------------------------------------------------------

# Each pattern is a directive aimed at the ROLE, not a claim about the instance:
# it tells the reviewer which label to record rather than giving it something to
# check. Matching a directive rather than a topic is what keeps this narrow --
# "the panel re-derived the unavoidability argument" is a fact about what
# happened and must survive, while "the honest recording is NO-LEAKAGE" is the
# document deciding the panel's verdict for it.
_REVIEWER_DIRECTED = (
    ("addresses-the-reviewer",
     re.compile(r"\((?:for|addressed to) the [^)]{0,40}"
                r"(?:auditor|reviewer|panel)[^)]{0,40}\)", re.I)),
    ("prescribes-the-verdict",
     re.compile(r"the (?:honest|correct) recording is\b", re.I)),
    ("prescribes-the-verdict",
     re.compile(r"\bsubmit \S{2,20} only (?:for|if|when)\b", re.I)),
    ("recording-convention",
     re.compile(r"^\W*(?:panel )?recording convention\b", re.I | re.M)),
)


def reviewer_directed(doc: str) -> list[str]:
    """Rules `doc` breaks by instructing the role that reviews it.

    A relaxation is honored on the strength of an argument a READER can check:
    the problem_statement and the gold edit disagree, so a faithful spec has to
    name the discriminator. A document that also tells the leakage panel which
    verdict to submit is asking to be graded by the party it is arguing with,
    and the whole weight of `verify ⟹ correct` on a relaxed cell rests on that
    panel having judged the argument independently. Whatever the pipeline needs
    its auditor to know about recording belongs in the auditor's prompt, where
    it is the harness defining its own labels; in the bundle it is the artifact
    steering its reviewer.

    Returns rule names (deduplicated, in pattern order), empty for a clean doc.
    """
    hits: list[str] = []
    for rule, pat in _REVIEWER_DIRECTED:
        if pat.search(doc or "") and rule not in hits:
            hits.append(rule)
    return hits


# ---------------------------------------------------------------------------
# the screen
# ---------------------------------------------------------------------------

def _is_region_marker(text: str, tables: LanguageTables) -> bool:
    """True iff `text` is exactly one of the mandatory CLEVER region-delimiter
    lines (`-- post-conditions-start`, `-- impl-end`, …) — matched against the
    SAME `_marker_res` grammar and `tables.region_names` vocabulary that
    `parse_regions` uses, so this stays in lock-step with the region table and
    cannot drift. A marker with trailing narration (`-- impl-start foo`) fails
    the `\\s*$` anchor and is NOT treated as a marker (its narration is scanned)."""
    start_re, end_re = _marker_res(tables)
    m = start_re.match(text) or end_re.match(text)
    return bool(m) and m.group(2) in tables.region_names


def _drop_region_markers(
        comments: list[tuple[int, str]], tables: LanguageTables
) -> list[tuple[int, str]]:
    """Region-marker lines are STRUCTURAL syntax — the spec-view projection
    itself emits them — not authored prose. Their fixed vocabulary
    (post/pure/impl/proof/…) is not under the author's control, so a patched
    repo symbol colliding with a marker keyword (e.g. a web.py `def POST` vs the
    `post-conditions` marker) is a lexer false positive, not a leak. Exclude
    only exact region-marker lines from the scanned comment set."""
    return [(ln, txt) for ln, txt in comments
            if not _is_region_marker(txt, tables)]


def screen(solution_src: str, tables, gold_patch: str,
           problem_statement: str = "", test_patch: str = "") -> LeakageReport:
    """Mechanical anti-leakage screen on a solution source's spec view.
    `gold_patch` / `problem_statement` come from the frozen instance row.
    `test_patch` is consulted by the ears flavor only (its screen is test-leak
    oriented); the formal flavors ignore it."""
    t = _tables(tables)
    if t.flavor == "ears":
        return _ears_screen(solution_src, gold_patch, test_patch,
                            problem_statement)
    rep = LeakageReport()
    view = spec_view(solution_src, t)
    view_norm = _normalize_code(view)

    if t.flavor == "python":
        diff_markers = _PY_DIFF_MARKERS
        idents = _py_spec_view_identifiers(view)
        comments = _py_comment_and_string_text(view)
        skip_trivial = True
    elif t.flavor == "lean":
        diff_markers = _LEAN_DIFF_MARKERS
        code_no_comments, comments = _lean_strip_comments_collect(view)
        idents = _lean_spec_view_identifiers(code_no_comments)
        skip_trivial = False
    else:
        raise ValueError(f"unknown language flavor {t.flavor!r}")

    comments = _drop_region_markers(comments, t)

    for marker in diff_markers:
        if marker in view:
            rep.hard_failures.append(f"L1: diff marker {marker!r} in spec view")

    for cl in _patch_changed_lines(gold_patch):
        cn = _normalize_code(cl)
        if skip_trivial and _is_trivial_code_fragment(cn):  # see _TRIVIAL_RETURN_RE
            continue
        if len(cn) >= 8 and cn in view_norm:
            rep.hard_failures.append(f"L1: gold-patch line reproduced: {cl!r}")

    for path in _patch_changed_files(gold_patch):
        if path and path in view:
            rep.hard_failures.append(f"L2: patched file path {path!r} in spec view")
        if path.endswith(".py"):
            dotted = path[:-3].replace("/", ".")
            if dotted.count(".") >= 2 and dotted in view:
                rep.hard_failures.append(f"L2: patched module path {dotted!r} in spec view")

    # Judge against the SOLVER-VISIBLE problem_statement ONLY — never
    # hints_text (not public to the consumer; echoing it leaks).
    problem = (problem_statement or "").lower()
    comment_text = "\n".join(txt for _, txt in comments).lower()
    for sym in sorted(_patch_changed_symbols(gold_patch)):
        sl = sym.lower()
        if sl in problem:
            continue  # already public via the task
        # (a) identifier embeds the patched symbol
        for ident in idents:
            if sl in ident.lower():
                rep.hard_failures.append(
                    f"L2/L5: spec-view identifier {ident!r} embeds patched repo "
                    f"symbol {sym!r} (not in problem statement) — rename it")
                break
        # (b) patched symbol named verbatim in a spec-view comment/docstring
        if re.search(rf"(?<![\w]){re.escape(sl)}(?![\w])", comment_text):
            rep.hard_failures.append(
                f"L2/L3: spec-view comment/docstring names patched repo symbol "
                f"{sym!r} (not in problem statement) — describe behavior, not the edit")

    for lineno, text in comments:
        m = _NARRATION_RE.search(text)
        if m:
            rep.hard_failures.append(
                f"L3: narration '{m.group(1)}' in spec-view comment/string "
                f"(line {lineno}): {text.strip()[:80]!r}")
    return rep
