# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-HYGIENE — static scan: markers, spec_view idempotency, import allowlist,
banned tokens, region hashes — plus per-backend extras, each one a way that
backend's language admits an artifact the shared checks would pass.
nagini: AST-level checks, @ContractOnly confined to axioms region, declared
float-encoding actually used, full-permission advisory (warning only).
velvet: comment-stripped scan; required termination set_option. lean:
comment-stripped scan for divergence-admitting constructs, correct_<name>
present + clean `#print axioms`; mode="feedback" (proof still
`by sorry` pre-P1.5) skips the sorry ban and closure check (allow_sorry).
"""
from __future__ import annotations

import ast
import re

from ..markers import parse_regions, region_hashes, spec_view
from .base import Bundle, GateResult
from ._lean_axioms import check_proof_axioms, correct_theorem_names

name = "G-HYGIENE"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution",)

# Regions a bundle must declare at least once. A backend appears here with the
# regions its spec form cannot be meaningful without.
_REQUIRED_REGIONS = {
    "nagini": ("pre-conditions", "post-conditions", "impl"),
    "velvet": ("impl",),
    "lean": ("post-conditions", "impl", "proof"),
}

_LEAN_BLOCK_COMMENT = re.compile(r"/-.*?-/", re.DOTALL)
_LEAN_LINE_COMMENT = re.compile(r"--[^\n]*")


def _strip_lean_comments(src: str) -> str:
    """Blank out Lean comments preserving newlines, so English prose in a comment
    is not mistaken for code (and line numbers still line up)."""
    src = _LEAN_BLOCK_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), src)
    return _LEAN_LINE_COMMENT.sub("", src)


# Flavors with a linter below. An unknown one raises rather than falling through
# to any of them: each branch is written against one language's comment syntax,
# divergence tokens and axiom screen, so borrowing a branch would enforce rules
# that say nothing about the new flavor (docs/adding_a_backend.md).
_FLAVOR_LINTERS = ("python", "ears", "lean")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    src = bundle.solution_src()
    if not src:
        return GateResult(name, "error", f"{bundle.solution.name} missing or empty")
    flavor = bundle.backend.language.flavor
    if flavor == "python":
        return _run_python(bundle, src)
    if flavor == "ears":
        return _run_ears(bundle, src)
    if flavor == "lean":
        return _run_lean(bundle, src, mode)
    raise ValueError(
        f"unknown language flavor {flavor!r} (backend {bundle.backend.name!r}): "
        f"G-HYGIENE has no linter for it (known: {', '.join(_FLAVOR_LINTERS)}). "
        f"Add a _run_{flavor}() beside the others and an entry in "
        "_REQUIRED_REGIONS for the backend; reusing another flavor's linter would "
        "enforce rules written for a different language.")


# ears flavor (requirements.md) — the EARS structural lint plus provenance:
# the bundle must record what sources the spec author consulted.

def _run_ears(bundle: Bundle, src: str) -> GateResult:
    from ..ears_lint import analyze
    rep = analyze(src)
    problems = list(rep.problems)
    sources = bundle.meta().get("spec_sources")
    if not (isinstance(sources, list) and sources):
        problems.append("meta.json has no non-empty `spec_sources` list "
                        "(what the spec author consulted: issue / hidden_tests"
                        " / formal sibling spec)")
    data = {"region_hashes": region_hashes(src, bundle.backend.language),
            "n_requirements": rep.n_requirements,
            "n_criteria": rep.n_criteria,
            "n_triggered": rep.n_triggered}
    detail = "; ".join(problems) or (
        f"EARS structure clean: {rep.n_requirements} requirement(s), "
        f"{rep.n_criteria} criteria ({rep.n_triggered} triggered); "
        f"spec_sources recorded")
    return GateResult(name, "pass" if not problems else "fail", detail, data)


# python flavor (nagini)

def _import_roots(tree: ast.AST) -> set[str]:
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                roots.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def _banned_calls(tree: ast.AST, banned_names: set[str]) -> set[str]:
    return {n.func.id for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in banned_names}


def _contractonly_linenos(tree: ast.AST) -> list[int]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dname = dec.id if isinstance(dec, ast.Name) else (
                    dec.attr if isinstance(dec, ast.Attribute) else None)
                if dname == "ContractOnly":
                    out.append(node.lineno)
    return out


def _full_perm_warnings(tree: ast.AST) -> list[str]:
    """Full-permission read-only param advisory (SPEC_GUIDE directive 5)."""
    warns = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = {a.arg for a in node.args.args + node.args.kwonlyargs}
        for call in ast.walk(node):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "Requires"):
                continue
            for acc in ast.walk(call):
                if not (isinstance(acc, ast.Call) and isinstance(acc.func, ast.Name)
                        and acc.func.id == "Acc" and len(acc.args) == 1):
                    continue
                pred = acc.args[0]
                if (isinstance(pred, ast.Call) and isinstance(pred.func, ast.Name)
                        and pred.func.id in ("list_pred", "dict_pred", "set_pred")
                        and len(pred.args) == 1 and isinstance(pred.args[0], ast.Name)
                        and pred.args[0].id in params):
                    p = pred.args[0].id
                    msg = (f"param '{p}' of {node.name}() at FULL {pred.func.id} "
                           f"permission — if read-only use Acc(...,1/2) (directive 5)")
                    if msg not in warns:
                        warns.append(msg)
    return warns


def _run_python(bundle: Bundle, src: str) -> GateResult:
    tables = bundle.backend.language
    problems = []
    regions = parse_regions(src, tables)
    if not regions.ok:
        problems += [f"marker: {e}" for e in regions.errors]
    for req in _REQUIRED_REGIONS["nagini"]:
        if not regions.get(req):
            problems.append(f"missing region '{req}'")
    if spec_view(spec_view(src, tables), tables) != spec_view(src, tables):
        problems.append("spec_view not idempotent (marker rot)")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return GateResult(name, "fail", f"{bundle.solution.name} does not parse: {e}")
    bad = _import_roots(tree) - set(tables.import_allowlist)
    if bad:
        problems.append(f"imports outside allowlist: {sorted(bad)}")
    # python banned_tokens are call spellings ("Assume("): match as AST calls,
    # not substrings, so a name inside a comment or string cannot fail a bundle.
    banned_names = {t.rstrip("(").strip() for t in tables.banned_tokens}
    banned = _banned_calls(tree, banned_names)
    if banned:
        problems.append(f"banned calls: {sorted(banned)}")
    for ln in _contractonly_linenos(tree):
        if not regions.covers("axioms", ln):
            problems.append(f"@ContractOnly at line {ln} outside axioms region")
    # float_encoding declared but no `float` in the model = stale knob. It is a
    # promise to a consumer about how the spec reads floats, so a declaration
    # nothing honors is worse than no declaration.
    fe = bundle.float_encoding()
    if fe and not re.search(r"\bfloat\b", src):
        problems.append(
            f"meta.json declares float_encoding={fe!r} but model.py uses no float")
    warns = _full_perm_warnings(tree)
    data: dict = {"region_hashes": region_hashes(src, tables)}
    if warns:
        data["frame_warnings"] = warns
    detail = "; ".join(problems) or "imports/markers/regions clean"
    if warns and not problems:
        detail += "  [advisory] " + " || ".join(warns)
    return GateResult(name, "pass" if not problems else "fail", detail, data)


# lean flavor (velvet + lean)

_TERM_OPT = re.compile(
    r'set_option\s+loom\.semantics\.termination\s+"(?P<v>[A-Za-z]+)"')
# `open A B C` opens every namespace on the line, so PartialCorrectness can
# arrive as a trailing name rather than the first one.
_OPEN_PARTIAL = re.compile(r"^\s*open\b[^\n]*\bPartialCorrectness\b", re.M)
_LINTER_OFF = re.compile(r"set_option\s+loom\.linter\.errors\s+false")


def _velvet_termination_problems(code: str) -> list[str]:
    """Reasons this velvet source does not claim TOTAL correctness.

    Under partial correctness a postcondition is claimed only of TERMINATING
    runs, so an implementation that never terminates satisfies every `ensures`
    vacuously: it verifies, and its faithful patch hangs the test it was meant
    to fix. That is `verify` not implying `resolve`, which is the one property
    the benchmark exists to measure, and no property test can reach it because
    the spec itself is what admits the diverging rival.

    Three separate lines have to agree, because the guarantee is split across
    them and each half is silent about the other:

    * the OPTION VALUE decides whether a `decreasing` clause is REQUIRED. It is
      what the `decreasing` elaborator reads.
    * the effective NAMESPACE decides whether that clause is CHECKED. The
      partial scope's loop rule takes the measure and discards it, so under a
      contrary `open` a `decreasing` clause elaborates, type-checks, and proves
      nothing.
    * the LINTER FLAG decides whether the missing-clause error is an error.

    So `"total"` plus a later `open PartialCorrectness` is the trap this exists
    to catch: the clause is mandatory, the clause is ignored, and nothing warns. A
    non-terminating loop whose invariants discharge everything else then verifies
    silently, where the same bytes under the total scope fail on `decreasing_1`.

    Checking only that the option is PRESENT misses every one of the three, and
    each is a one-token edit that leaves G-VERIFY passing -- passing precisely
    BECAUSE the diverging rival now satisfies the spec -- and leaves G-DIFF passing
    too, since the prepatch twins carry the same spec region and flip with it.
    """
    problems = []
    m = _TERM_OPT.search(code)
    if m is None:
        if "loom.semantics.termination" not in code:
            problems.append("missing set_option loom.semantics.termination")
        else:
            problems.append("loom.semantics.termination is not a quoted value")
    elif m.group("v") != "total":
        problems.append("loom.semantics.termination is "
                        f'"{m.group("v")}", not "total"')
    if (p := _OPEN_PARTIAL.search(code)) is not None:
        problems.append("opens PartialCorrectness, which discards the "
                        f"decreasing measure: {p.group(0).strip()!r}")
    if _LINTER_OFF.search(code):
        problems.append("set_option loom.linter.errors false disables the "
                        "missing-decreasing-measure error")
    return problems


# Constructs that let a lean bundle name a function Lean's termination checker
# never proves total. Most reuse the identifier-boundary rule of the shared
# banned-token scan, whose lookbehind excludes a preceding `.` so that a total
# library function such as `Nat.repeat` is not caught by the bare token. `Loop`
# is the deliberate exception: the shape to reject is `Lean.Loop.mk`, whose
# `Loop` FOLLOWS a dot, so its lookbehind is dot-permissive. Every lookahead
# also excludes `'`, which keeps the `repeat'` tactic legal.
_LEAN_DIVERGENCE: tuple[tuple[str, re.Pattern[str] | None, str], ...] = (
    ("partial", re.compile(r"(?<![\w.])partial(?![\w])"),
     "marks a definition whose termination Lean is told not to check"),
    ("partial_fixpoint", re.compile(r"(?<![\w.])partial_fixpoint(?![\w])"),
     "admits a recursion as a fixpoint that may be defined nowhere"),
    ("while", re.compile(r"(?<![\w.])while(?![\w'])"),
     "`do` notation for `Lean.Loop.forIn`, an iteration with no measure"),
    ("repeat", re.compile(r"(?<![\w.])repeat(?![\w'])"),
     "the same unbounded `Lean.Loop` iteration under a second surface token"),
    ("Loop", re.compile(r"(?<!\w)Loop(?![\w'])"),
     "the unbounded loop type itself, as in `for _ in Lean.Loop.mk do`"),
    ("implemented_by", None,
     "keeps the logical body the proof reads and swaps the compiled one"),
)


def _lean_termination_problems(code: str) -> list[str]:
    """Constructs that let a lean bundle prove its postcondition of a computation
    that never produces a value.

    `theorem correct_f : problem_spec_f (implementation_f x) x` claims something
    about the VALUE that `implementation_f x` denotes. What makes that claim a
    guarantee that anything is COMPUTED is Lean's own termination checker: a
    recursive definition with no decreasing argument is rejected outright, so
    every function a bundle can otherwise define is total and the theorem says
    what it looks like it says. Each construct below switches that checker off,
    and then `verify` stops implying `resolve`: the bundle passes every gate, and
    the patch transliterated from it spins forever on the test it was written to
    fix. No property test can reach this, because what admits the diverging rival
    is the spec artifact itself rather than the behaviour it describes.

    The hole is easy to miss because the divergence does not have to be OBSERVED
    to be shipped. In the identity monad `bind` is application, so a loop whose
    result is discarded beta-reduces away and a proof about the returned value
    closes unchanged -- and `#print axioms` stays clean either way, so the axiom
    screen cannot catch any of this. Four things about the token set follow from
    that, and none of them is guessable from the names alone:

    * `while` in a `do` block is a macro for `Lean.Loop.forIn`, an opaque constant
      requiring no measure that no one has proved total.
    * `repeat` is the same macro under a second surface token, so a ban on `while`
      alone misses it.
    * `for _ in Lean.Loop.mk do ...` contains neither `while` nor `repeat`, which
      is why the loop TYPE has to be named too. Only `for x in xs` over a finite
      container stays legal.
    * `partial_fixpoint` needs a rule of its own, because the identifier rule for
      `partial` does not match it: the underscore after `partial` is a word
      character.

    The control is that same recursion with no `partial` marker, which Lean itself
    REJECTS ("fail to show termination") -- the guarantee the ban restores.

    `implemented_by` is listed with them although it is not a loop. It leaves the
    logical body the frozen proof closes over intact and swaps the body that is
    compiled, so the function that is proved correct and the function that runs
    are two different functions: the same failure one step further along, and
    also the only way safe code can reach an `unsafe` definition.

    `termination_by` and `decreasing_by` are deliberately left legal: they SUPPLY
    the proof the checker asks for, which is the opposite of evading it. So is the
    `repeat'` tactic, and so are ordinary identifiers that merely contain `Loop`
    (`LoopState`, `innerLoop`, `runLoop`); see `_LEAN_DIVERGENCE` for the pattern
    rules that admit them. Comments are stripped before the scan, so prose naming
    a banned token is not a finding.

    This screen is for the lean flavor only. A velvet `while` is a different
    construct: it carries `invariant` / `done_with` / `decreasing` clauses and is
    discharged by the total-correctness loop rule, so velvet closes the same hole
    through `_velvet_termination_problems` instead.
    """
    problems = []
    for token, rx, why in _LEAN_DIVERGENCE:
        if (token in code) if rx is None else rx.search(code):
            problems.append(f"{token!r} admits a non-terminating "
                            f"implementation: {why}")
    return problems


def _run_lean(bundle: Bundle, src: str, mode: str) -> GateResult:
    tables = bundle.backend.language
    backend = bundle.backend.name
    # feedback leniency: lean backend only, whose proof region legitimately
    # holds `by sorry` before P1.5.
    allow_sorry = (backend == "lean" and mode == "feedback")
    problems = []
    regions = parse_regions(src, tables)
    if not regions.ok:
        problems += [f"marker: {e}" for e in regions.errors]
    required = _REQUIRED_REGIONS.get(backend)
    if required is None:
        # A backend added to this flavor without a required-region entry: say so,
        # rather than raising KeyError from inside a gate run. Not defaulted to
        # the empty tuple, which would pass a bundle declaring no spec region.
        raise ValueError(
            f"backend {backend!r} has no _REQUIRED_REGIONS entry, so G-HYGIENE "
            "cannot say which marker regions its spec form needs (entries: "
            f"{', '.join(sorted(_REQUIRED_REGIONS))}). Add one.")
    for req in required:
        if not regions.get(req):
            problems.append(f"missing region '{req}'")
    if spec_view(spec_view(src, tables), tables) != spec_view(src, tables):
        problems.append("spec_view not idempotent (marker rot)")
    # imports/banned tokens are scanned on comment-stripped code: a banned name
    # discussed in a comment is not a use of it.
    code = _strip_lean_comments(src)
    for m in re.finditer(r"^\s*import\s+([A-Za-z_][\w.]*)", code, re.MULTILINE):
        root = m.group(1).split(".")[0]
        if root not in tables.import_allowlist:
            problems.append(f"import outside allowlist: {m.group(1)}")
    banned = tables.banned_tokens
    if allow_sorry:
        banned = tuple(t for t in banned if t not in ("sorry", "sorryAx"))
    for tok in banned:
        stripped = tok.strip()
        if stripped.isidentifier():
            hit = re.search(rf"(?<![\w.]){re.escape(stripped)}(?![\w])", code)
        else:
            hit = stripped in code
        if hit:
            problems.append(f"banned token present: {stripped!r}")
    data: dict = {"region_hashes": region_hashes(src, tables)}
    if backend == "velvet":
        # `code` (comments stripped), not `src`: a doc comment that describes
        # this very trap must not fail the bundle that documents it.
        problems += _velvet_termination_problems(code)
        detail = "; ".join(problems) or "imports/markers/regions/solver-flags clean"
        return GateResult(name, "pass" if not problems else "fail", detail, data)
    # lean: no divergence-admitting construct (on `code`, comments stripped, so a
    # doc comment describing the trap does not fail the bundle documenting it);
    # correct_<name> present; #print axioms clean (skipped in feedback).
    problems += _lean_termination_problems(code)
    if not correct_theorem_names(src, tables):
        problems.append("no `theorem correct_<name>` present")
    elif regions.get("proof") and not problems and not allow_sorry:
        ax_ok, ax_detail, ax_data = check_proof_axioms(bundle, src,
                                                       bundle.verify_timeout())
        if ax_data.get("no_verdict"):
            # The re-elaboration never reported, so the proof was not found open
            # -- nothing about this bundle was established either way.
            return GateResult(name, "error", f"axiom check: {ax_detail}", data)
        if not ax_ok:
            problems.append(f"axiom check: {ax_detail}")
    detail = "; ".join(problems) or "imports/markers/regions/axioms clean"
    return GateResult(name, "pass" if not problems else "fail", detail, data)
