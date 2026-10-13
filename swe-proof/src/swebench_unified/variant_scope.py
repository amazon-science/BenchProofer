# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Variant admissibility: what a G-PBT case may change, beyond same_spec.

`markers.same_spec` compares SPEC VIEWS, and the spec view *elides* the impl
region (all backends) plus, for the lean backend, the whole `proof` region —
including the `theorem correct_<name>` statement. Elision is right for the
consumer projection but it leaves the elided text unconstrained, so
`same_spec` alone admits variants that neuter the very obligation the case is
supposed to test:

    -- proof-start
    theorem correct_direct_sum : True := trivial     -- passes same_spec!
    -- proof-end

Paired with a deliberately wrong impl, that file elaborates cleanly. For an
`expect="verify"` case (soundness / admissibility) the verifier then says
"verified" for a reason that has nothing to do with the spec, and G-PBT
records a pass. That is a false SOUND: the strongest possible failure mode
for a benchmark whose whole claim is "verified implies correct".

The same shape exists on nagini: the impl region is elided, so an injected
`@ContractOnly` stub (an *assumed* postcondition, never verified) also
survives same_spec.

So a variant is admissible only if, in addition to same_spec:

1. **The obligation is preserved.** Lean: every `theorem correct_<name>`
   present in the frozen source must still be present with a byte-identical
   STATEMENT (everything up to the proof-introducing `:=`); the tactic body
   may differ freely, since a variant legitimately reproves. Velvet: the
   obligation is the `method ... require ... ensures` header, which lives in
   the spec view and is already covered by same_spec, but the
   `prove_correct <name>` headers must still all be present.
2. **No new assumption-bearing declarations appear anywhere.** No `axiom`,
   no `sorry`/`sorryAx`/`admit`, no `native_decide`, and on nagini no new
   `@ContractOnly`, beyond what the frozen source already had. These can
   discharge an obligation without proving anything.
3. **No new top-level `theorem`/`lemma` beyond the frozen set.** A variant
   proves the SAME obligations; a brand-new theorem is either dead weight or
   a redefinition shadowing the real one.

Rule 2's ban is on *new* items only: whatever the frozen bundle legitimately
declares (declared callee axioms, `Classical.choice` usage) stays legal, so
this never rejects a bundle that G-HYGIENE already accepts.

This module is deliberately lexical and cheap: it runs before the verifier,
so a malformed variant costs no `lake` build. It is a NECESSARY condition,
not a sufficient one — G-PBT still runs the real checker.
"""
from __future__ import annotations

import re

from .backends.base import LanguageTables
from .markers import parse_regions, same_spec

# ---------------------------------------------------------------------------
# lexing helpers
# ---------------------------------------------------------------------------

# `theorem correct_foo ... := by` — the statement is everything before `:=`.
_LEAN_CORRECT_RE = re.compile(r"^[ \t]*theorem[ \t]+(correct_[A-Za-z0-9_']+)", re.MULTILINE)
_LEAN_DECL_RE = re.compile(r"^[ \t]*(?:@\[[^\]]*\][ \t]*)?(theorem|lemma)[ \t]+"
                           r"([A-Za-z0-9_']+)", re.MULTILINE)
_LEAN_AXIOM_RE = re.compile(r"^[ \t]*axiom[ \t]+([A-Za-z0-9_']+)", re.MULTILINE)
_PROVE_CORRECT_RE = re.compile(r"^[ \t]*prove_correct[ \t]+([A-Za-z0-9_']+)", re.MULTILINE)
_CONTRACT_ONLY_RE = re.compile(r"^[ \t]*@ContractOnly[ \t]*$", re.MULTILINE)

# Tokens that let a proof/impl assume rather than establish. Checked as a
# delta against the frozen source so a bundle's own legal usage is untouched.
# Matched on IDENTIFIER boundaries: a plain substring count reports `admit`
# inside `admit_parser` / `instance_admits_namespace` (both occur in real
# bundles) and would reject a legitimate case.
_ASSUMPTION_TOKENS = ("sorry", "sorryAx", "admit", "native_decide",
                      "Assume", "Refute")
_TOKEN_RES = {t: re.compile(rf"(?<![A-Za-z0-9_']){re.escape(t)}(?![A-Za-z0-9_'])")
              for t in _ASSUMPTION_TOKENS}


# ---------------------------------------------------------------------------
# flavor dispatch
# ---------------------------------------------------------------------------

# Every rule in this module is written against ONE flavor's syntax, and the
# result of the screen is a list of problems whose EMPTINESS means admissible.
# So a flavor with no rule has to raise: falling off the end of a dispatch
# returns `[]`, a verdict of "nothing evades here" from a screen that never
# looked. Listing a flavor here is the promise that the rules below cover its way
# of discharging a proof obligation (docs/adding_a_backend.md).
_KNOWN_FLAVORS = ("lean", "python", "ears")

# Flavors whose spec language has no declaration form that can carry an
# assumption, so the empty set is the right ANSWER rather than a missing branch:
# python (nagini) has no `axiom`/`theorem`/`lemma` at all — its assumption
# surface is `@ContractOnly`, screened separately below — and an ears
# requirements document is prose with no declarations.
_FLAVORS_WITHOUT_DECLARATIONS = ("python", "ears")


def _unknown_flavor(flavor: str, what: str) -> ValueError:
    """The error every dispatch below raises instead of defaulting."""
    return ValueError(
        f"unknown language flavor {flavor!r}: variant_scope has no {what} for it "
        f"(known: {', '.join(_KNOWN_FLAVORS)}). Add a branch in "
        "swebench_unified.variant_scope — or, if the flavor has no such "
        "construct, list it in _FLAVORS_WITHOUT_DECLARATIONS / _KNOWN_FLAVORS. "
        "Defaulting instead would report every same-spec rival as ADMISSIBLE "
        "with no rule having run.")


def _strip_lean_comments(src: str) -> str:
    """Blank out `--` line comments and `/- ... -/` blocks, preserving line
    structure so line-anchored regexes keep working."""
    out = re.sub(r"/-.*?-/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), src,
                 flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", out)


def _strip_python_comments(src: str) -> str:
    return re.sub(r"#[^\n]*", "", src)


def _strip_comments(src: str, tables: LanguageTables) -> str:
    # Reached only for a flavor `unsound_evasions` has already accepted. `#` is
    # the python flavor's comment; for ears (prose, no code comments) the same
    # pass only drops `#`-led text, which is conservative for a token delta.
    return (_strip_lean_comments(src) if tables.flavor == "lean"
            else _strip_python_comments(src))


def lean_obligations(src: str) -> dict[str, str]:
    """`correct_<name>` -> its STATEMENT text (declaration head up to the
    proof-introducing `:=`), whitespace-normalized.

    Comments are stripped first so a variant may re-comment its proof freely;
    whitespace is collapsed so reindentation is not a spurious difference.
    """
    clean = _strip_lean_comments(src)
    out: dict[str, str] = {}
    for m in _LEAN_CORRECT_RE.finditer(clean):
        rest = clean[m.end():]
        cut = rest.find(":=")
        stmt = rest if cut < 0 else rest[:cut]
        out[m.group(1)] = " ".join(stmt.split())
    return out


def _decl_names(src: str, tables: LanguageTables) -> set[str]:
    if tables.flavor == "lean":
        return {m.group(2) for m in _LEAN_DECL_RE.finditer(_strip_lean_comments(src))}
    if tables.flavor in _FLAVORS_WITHOUT_DECLARATIONS:
        return set()
    raise _unknown_flavor(tables.flavor, "theorem/lemma scan")


def _axiom_names(src: str, tables: LanguageTables) -> set[str]:
    if tables.flavor == "lean":
        return set(_LEAN_AXIOM_RE.findall(_strip_lean_comments(src)))
    if tables.flavor in _FLAVORS_WITHOUT_DECLARATIONS:
        return set()
    raise _unknown_flavor(tables.flavor, "axiom scan")


def _token_counts(src: str, tables: LanguageTables) -> dict[str, int]:
    clean = _strip_comments(src, tables)
    return {t: len(_TOKEN_RES[t].findall(clean)) for t in _ASSUMPTION_TOKENS}


# ---------------------------------------------------------------------------
# the check
# ---------------------------------------------------------------------------

def unsound_evasions(frozen: str, variant: str, tables) -> list[str]:
    """Reasons a same-spec rival would VERIFY without having been checked.

    The subset of the variant rules that is about soundness rather than about
    scope: a rival that drops the proof obligation, or assumes a new axiom, or
    reaches for `sorry`, gets a verifier exit code it did not earn, and every
    reader of that exit code draws the opposite of the truth -- a falsification
    battery concludes the spec is too strong, an audit concludes it admits a wrong
    implementation and is too weak.

    Split out from `variant_problems` because the two callers differ on ONE rule.
    A battery variant may not declare a new theorem or lemma (it must reprove the
    same obligations, so a new declaration is scope creep), but an audit attack
    is an independent implementation and may legitimately need a helper lemma.
    Applying that rule to an attack would retire it as inadmissible and record a
    weakness search that did not happen.

    Raises ValueError on a flavor with no rules here: an empty return means
    ADMISSIBLE, so falling through the dispatch would report every rival of that
    flavor's bundles sound without a rule having run.
    """
    t = tables if isinstance(tables, LanguageTables) else tables.language
    if t.flavor not in _KNOWN_FLAVORS:
        raise _unknown_flavor(t.flavor, "obligation/assumption rules")
    problems: list[str] = []

    # (1) obligations preserved. python and ears add nothing here, deliberately:
    # nagini's obligation IS the Requires/Ensures pair, which lives in the spec
    # view and so is already covered by same_spec, and an ears requirements
    # document has no obligation to restate. That is a checked emptiness, not the
    # unchecked emptiness an unknown flavor would have got above.
    if t.flavor == "lean":
        if "proof" in t.region_names:
            f_obl, v_obl = lean_obligations(frozen), lean_obligations(variant)
            for name, stmt in f_obl.items():
                if name not in v_obl:
                    problems.append(f"obligation `theorem {name}` is missing")
                elif v_obl[name] != stmt:
                    problems.append(
                        f"obligation `theorem {name}` statement was rewritten "
                        "(only the tactic body may differ)")
        else:
            f_pc = set(_PROVE_CORRECT_RE.findall(_strip_lean_comments(frozen)))
            v_pc = set(_PROVE_CORRECT_RE.findall(_strip_lean_comments(variant)))
            for name in sorted(f_pc - v_pc):
                problems.append(f"obligation `prove_correct {name}` is missing")

    # (2) no NEW assumption-bearing declarations
    f_ax, v_ax = _axiom_names(frozen, t), _axiom_names(variant, t)
    new_ax = sorted(v_ax - f_ax)
    if new_ax:
        problems.append(f"declares new axiom(s) {new_ax} (assumed, never proved)")

    f_tok, v_tok = _token_counts(frozen, t), _token_counts(variant, t)
    for tok in _ASSUMPTION_TOKENS:
        if v_tok[tok] > f_tok[tok]:
            problems.append(f"introduces assumption token {tok!r} "
                            f"({f_tok[tok]} -> {v_tok[tok]})")

    if t.flavor == "python":
        f_co = len(_CONTRACT_ONLY_RE.findall(_strip_python_comments(frozen)))
        v_co = len(_CONTRACT_ONLY_RE.findall(_strip_python_comments(variant)))
        if v_co > f_co:
            problems.append(f"introduces @ContractOnly stub(s) ({f_co} -> {v_co}): "
                            "an assumed postcondition is never verified")

    return problems


def variant_problems(frozen: str, variant: str, tables) -> list[str]:
    """Reasons `variant` is not an admissible same-spec variant of `frozen`.

    Empty list = admissible. Each string names the evasion concretely so a
    G-PBT MALFORMED-TESTS detail is actionable.
    """
    t = tables if isinstance(tables, LanguageTables) else tables.language
    problems: list[str] = []

    if not same_spec(frozen, variant, t):
        problems.append("spec view differs (same_spec failed)")

    problems += unsound_evasions(frozen, variant, t)

    # (3) no new theorem/lemma declarations
    new_decls = sorted(_decl_names(variant, t) - _decl_names(frozen, t))
    if new_decls:
        problems.append(f"declares new theorem/lemma {new_decls}: a variant "
                        "reproves the SAME obligations")

    return problems


def is_admissible_variant(frozen: str, variant: str, tables) -> bool:
    return not variant_problems(frozen, variant, tables)


def frozen_self_check(frozen: str, tables) -> list[str]:
    """`variant_problems(frozen, frozen)` must be empty — a sanity check that
    the rules never reject a bundle's own solution (used by tests and by the
    port tooling before it trusts a bundle)."""
    return variant_problems(frozen, frozen, tables)


def impl_region_only(frozen: str, variant: str, tables) -> bool:
    """True if `variant` differs from `frozen` ONLY inside impl regions.

    Stricter than variant_problems and NOT required (lean soundness positives
    legitimately reprove, touching the proof region), but useful to report:
    a case satisfying it is trivially attributable to the impl.
    """
    t = tables if isinstance(tables, LanguageTables) else tables.language
    fl, vl = frozen.splitlines(), variant.splitlines()
    spans = parse_regions(frozen, t).get("impl")
    if not spans or len(fl) != len(vl):
        return False
    inside = {i for lo, hi in spans for i in range(lo, hi - 1)}
    return all(a == b for i, (a, b) in enumerate(zip(fl, vl)) if i not in inside)
