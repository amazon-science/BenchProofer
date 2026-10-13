# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Refutation witnesses: making a G-PBT *rejection* attributable to the spec.

A `kind="uniqueness"` case claims "this wrong impl shares the frozen spec and
the spec REJECTS it". The gate's evidence is that the verifier said no. On
nagini that is nearly the whole story: Viper discharges the postcondition
automatically, so "did not verify" really does mean "the contract does not
hold for this impl" (modulo SMT incompleteness).

On the tactic-proof backends it is not. The frozen proof script is tuned to
the frozen impl's syntactic form (`intro a b; rfl` and its relatives), and a
rival's entire purpose is to change that form. So a rival that is
**observationally equal to gold** also fails to build:

    -- gold                        -- rival: commuted `&&`, still correct
    return (a.rest == b.rest) && (a.code == b.code)
    return (a.code == b.code) && (a.rest == b.rest)   -- `rfl` no longer closes

Both that rival and a genuinely wrong one (drop the `code` conjunct) exit 1
with the same `Tactic 'rfl' failed`. The gate cannot tell them apart, so it
would record "rejected as expected" either way and report SOUND, attesting to
spec strength it never tested. Because tactic breakage is the DEFAULT outcome of
reshaping an impl, essentially every ported reject case would pass vacuously.

So each reject case carries its own oracle: a **witness**, a Lean snippet
proving the rival violates the spec at one CONCRETE input. It is checked in a
file where the frozen obligations have been removed, so no tactic script can
interfere, and it must satisfy both halves:

  1. it ELABORATES against the rival  -> the rival provably contradicts the
     spec somewhere, so the rejection is attributable to the spec and not to
     a tactic gap;
  2. it FAILS against the frozen solution -> the witness is a real
     discriminator, not a tautology. `example : True := trivial` elaborates
     against the rival too; requiring it to fail on gold is what rules that
     out (gold satisfies the spec at every input, so a genuine "the spec is
     violated here" statement cannot hold of it).

Together those give a machine-checked counterexample per reject case, at a cost
of two extra builds.

Nagini is exempt: it has no tactic script to break, and its existing reject
cases predate this requirement. Their witness status is recorded rather than
enforced, so the residual gap stays visible.
"""
from __future__ import annotations

import re

from .backends.base import LanguageTables
from .markers import parse_regions
from .variant_scope import _strip_lean_comments

# `prove_correct <name> by` / `prove_correct? <name> by` — the velvet
# obligation. The tactic body is everything indented under the header.
_PROVE_CORRECT_HEADER = re.compile(r"^[ \t]*prove_correct[?]?[ \t]+\S+")

# ...except that the command's own clauses may sit at COLUMN 0. Lean is
# whitespace-insensitive here, so a `prove_correct` may be written
#
#     prove_correct assignColumnForms
#     termination_by sizeOf conds
#     decreasing_by
#       all_goals omega
#     by
#       loom_solve
#
# and all of it is one command. Only these keywords can continue it; anything
# else at column 0 starts a new declaration.
_PROVE_CORRECT_CONT = re.compile(r"^(?:termination_by|decreasing_by|by)\b")

# `#print axioms correct_foo`, `#check`, `#eval`, ... — top-level DIAGNOSTIC
# commands. Lean's `#` commands are all diagnostics, so they are only ever
# reporting on the file; none contributes to what a witness asserts.
_HASH_COMMAND = re.compile(r"^#[A-Za-z_]")

WITNESS_REQUIRED = ("velvet", "lean")

# Every way a witness could assume its own conclusion. `axiom`/`opaque`/
# `partial` (and the `unsafe`/`extern` escape hatches) introduce a term with no
# proof; `sorry`/`admit`/`sorryAx` close any goal; `native_decide` trusts the
# compiler, which would also make the witness hold of gold. Matched on
# IDENTIFIER boundaries, since `admit` occurs inside real identifiers such as
# `admit_parser`.
_WITNESS_BANNED = ("sorry", "sorryAx", "admit", "native_decide", "axiom",
                   "opaque", "unsafe", "extern", "implemented_by")
_WITNESS_BANNED_RES = {
    t: re.compile(rf"(?<![A-Za-z0-9_']){re.escape(t)}(?![A-Za-z0-9_'])")
    for t in _WITNESS_BANNED}


def _tables(tables) -> LanguageTables:
    return tables if isinstance(tables, LanguageTables) else tables.language


def _strip_proof_regions(src: str, t: LanguageTables) -> str:
    """Drop the contents of every `proof` region, markers kept (lean)."""
    lines = src.splitlines()
    spans = parse_regions(src, t).get("proof")
    if not spans:
        return src
    drop = {i for lo, hi in spans for i in range(lo, hi - 1)}
    return "\n".join(ln for i, ln in enumerate(lines) if i not in drop) + "\n"


def _strip_prove_correct(src: str) -> str:
    """Drop every `prove_correct <name> by <tactics>` block (velvet).

    The block runs from its header to the next line that starts a new
    declaration: blank and indented lines are the command's `tacticSeq`, and so
    are the command's own clauses (`termination_by` / `decreasing_by` / `by`)
    even when they are written at column 0, which Lean permits.

    Stopping at the first column-0 line regardless of what it says leaves those
    clauses ORPHANED, and the witness file then fails to parse for BOTH builds --
    so the gate records `witness-unproven`, an inconclusive outcome, for a witness
    it never tried. Fail-safe (the rival build is the half that must succeed) but
    it blocks honest cells.
    """
    out: list[str] = []
    skipping = False
    for ln in src.splitlines():
        if _PROVE_CORRECT_HEADER.match(ln):
            skipping = True
            continue
        if skipping:
            if (not ln.strip() or ln[:1] in (" ", "\t")
                    or _PROVE_CORRECT_CONT.match(ln)):
                continue
            skipping = False
        out.append(ln)
    return "\n".join(out) + "\n"


def _strip_hash_commands(src: str) -> str:
    """Drop top-level `#...` diagnostic commands.

    They have to go with the obligations they report on. A bundle may close with
    `#print axioms correct_<name>` -- a real integrity check in the frozen file,
    but the theorem it names lives INSIDE the proof region, so once that region is
    emptied the command references a constant that no longer exists. The build
    then fails on `Unknown constant` and the gate reads that as "the witness does
    not hold of the rival": `witness-unproven` on a witness never actually tried.
    Fail-safe (an error breaks the RIVAL build, the half that must succeed, so it
    cannot mint a false SOUND) but it blocks honest cells.
    """
    return "\n".join(ln for ln in src.splitlines()
                     if not _HASH_COMMAND.match(ln)) + "\n"


def witness_file(src: str, witness: str, tables) -> str:
    """`src` with its proof obligations removed and `witness` appended.

    Removing the obligations is what makes the witness build a clean signal:
    the frozen tactic script would otherwise fail for the rival (that is the
    whole problem) and its error would mask the witness's own verdict. Anything
    else that only makes sense in the presence of those obligations goes too;
    see `_strip_hash_commands`.
    """
    t = _tables(tables)
    if t.flavor != "lean":
        raise ValueError(f"witness_file is lean-flavored only, got {t.flavor!r}")
    body = (_strip_proof_regions(src, t) if "proof" in t.region_names
            else _strip_prove_correct(src))
    return _strip_hash_commands(body).rstrip() + "\n\n" + witness.strip() + "\n"


_WITNESS_HEAD = re.compile(
    r"^[ \t]*(?:example|theorem[ \t]+\S+|lemma[ \t]+\S+)", re.M)

# Tactics that decide the common contradictions: linear arithmetic over an
# opaque atom (`f x = 0` with `f x = 1`), a decidable literal clash, and
# `simp_all`'s congruence closure. Incomplete on purpose — see
# `consistency_probe`.
_CONSISTENCY_TACTIC = "  first | omega | simp_all | decide | (simp_all; omega)\n"


def _binders_at(w: str, start: int) -> str:
    """The bracketed binder groups running from `start`, as written."""
    i, n = start, len(w)
    end = i
    while i < n:
        while i < n and w[i] in " \t\n":
            i += 1
        if i >= n or w[i] not in "({[":
            break
        depth, j = 0, i
        while j < n:
            if w[j] in "([{":
                depth += 1
            elif w[j] in ")]}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth:
            break
        i = end = j + 1
    return w[start:end].strip()


def all_witness_head_binders(witness: object) -> list[str]:
    """The binder groups of EVERY declaration in the witness that binds any.

    A witness may declare more than one thing — a helper lemma it then applies,
    or a `#check` scaffold — and the refutation is not always the first. Reading
    only the first head is a hole: one harmless leading `theorem harmless :
    (1:Nat) = 1 := rfl` ahead of a conditioned refutation makes the probe read ""
    and vanish, re-opening exactly the prove-it-from-a-contradiction forgery it
    exists to catch.
    """
    if not isinstance(witness, str):
        return []
    w = _strip_lean_comments(witness)
    out = []
    for m in _WITNESS_HEAD.finditer(w):
        if b := _binders_at(w, m.end()):
            out.append(b)
    return out


def witness_head_binders(witness: object) -> str:
    """The binder groups the witness's FIRST `example`/`theorem` head declares.

    `example (call : Int) (h : f call = 0) : ...` -> `(call : Int) (h : f call = 0)`.
    Returns "" when that head binds nothing, which is the common case: a reject
    witness normally states its refutation at literal inputs, and conditioning is
    reached for only where the carrier forces it.

    `consistency_probe` uses `all_witness_head_binders` instead; this stays as
    the single-declaration accessor.
    """
    if not isinstance(witness, str):
        return ""
    w = _strip_lean_comments(witness)
    m = _WITNESS_HEAD.search(w)
    return _binders_at(w, m.end()) if m else ""


def consistency_probe(witness: object) -> str | None:
    """`example <the witness's own binders> : False := by ...`, or None.

    A witness may have to CONDITION on the carrier instead of computing it. When
    the spec is stated over an `opaque` callee, no literal input decides
    anything, so the refutation is stated at a point described by hypothesis:

        example (h : valueHash 5 ≠ 0) :
            choiceValueHashExec 5 ≠ DivM.res (valueHash 5) := by ...

    That is the technique that makes an opaque carrier attackable at all, and it
    is sound as long as the hypotheses can jointly HOLD. If they cannot, the
    witness proves its refutation from a contradiction, the "counterexample
    input" does not exist, and the case attributes nothing to the spec:

        example (h1 : valueHash 5 = 0) (h2 : valueHash 5 = 1) : ...

    That forgery ELABORATES against the rival and FAILS on gold, so it clears both
    halves of the discrimination check. The vacuity half cannot catch it either:
    the contradiction lets the script prove the goal for the rival's impl
    specifically, so gold still fails.

    So a witness that binds anything is additionally asked to show its own
    assumptions are satisfiable, by trying to derive `False` from them alone. A
    probe that SUCCEEDS is the forgery. Incomplete in the safe direction: a
    contradiction these tactics miss is recorded as consistent, so the check
    never fails an honest witness for being hard to decide.

    EVERY binding declaration is probed, not just the first (see
    `all_witness_head_binders`). All the probes go in one file, so the cost stays
    a single build however many declarations bind — and any one of them deriving
    `False` fails the case: a refutation resting on a helper proven from a
    contradiction is no better than one resting on a contradiction directly.

    None when nothing binds: there are no assumptions to be inconsistent, and
    the case costs no extra build.
    """
    groups = all_witness_head_binders(witness)
    if not groups:
        return None
    return "\n".join(f"example {b} : False := by\n{_CONSISTENCY_TACTIC}"
                     for b in groups)


# Every declaration form that introduces a NAME at the top level. Broader than
# variant_scope's theorem/lemma scan: an impl-region helper `def` is an
# admissible thing for a variant to add, and it is exactly what a witness must
# not be stated over.
_LEAN_DECL_ANY = re.compile(
    r"^[ \t]*(?:@\[[^\]]*\][ \t]*)*"
    r"(?:private[ \t]+|protected[ \t]+|noncomputable[ \t]+|partial[ \t]+"
    r"|unsafe[ \t]+|scoped[ \t]+|local[ \t]+)*"
    r"(?:theorem|lemma|def|abbrev|instance|structure|inductive|class|opaque"
    r"|axiom)[ \t]+([A-Za-z_][A-Za-z0-9_.'!?]*)", re.M)


def _declared_names(src: str) -> set[str]:
    return set(_LEAN_DECL_ANY.findall(_strip_lean_comments(src)))


def witness_scope_problems(frozen: str, variant: str, witness: object) -> list[str]:
    """Reasons the witness is stated outside the vocabulary gold and rival SHARE.

    The two-build check reads "gold's build failed" as "gold satisfies the spec
    here". That inference holds only if both builds were asking the same
    question. A rival may legitimately add an impl-region helper — `same_spec`
    elides the impl region and `variant_scope` bans only new theorems/axioms —
    and a witness stated over that helper then passes both halves while saying
    nothing:

        def rivalOnlyMarker : Nat := 0          -- in the rival's impl region
        example : rivalOnlyMarker = 0 := rfl    -- the "witness"

    The rival builds and gold does not, but gold's failure is an unknown name, not
    a satisfied spec: the witness is a tautology about a definition gold does not
    have, and it would be recorded as a refutation.

    So a witness may not reference any name the variant declares and the frozen
    solution does not. Names the witness itself brings into scope are fine: the
    velvet testers (`extract_program_for` -> `<name>Exec`, `derive_tester_for`
    -> `<name>Tester`) come from directives inside the witness, which is
    appended to BOTH files, so they exist on both sides by construction.

    The mirror case needs no rule: a witness referencing something only GOLD has
    breaks the RIVAL build, which is the half that must succeed, so it already
    lands as `witness-unproven`.
    """
    if not isinstance(witness, str) or not witness.strip():
        return []
    variant_only = _declared_names(variant) - _declared_names(frozen)
    if not variant_only:
        return []
    w = _strip_lean_comments(witness)
    # A name the witness DECLARES for itself is its own, even if the variant
    # happens to declare one too -- the witness's copy shadows nothing, it is
    # simply present in both builds.
    own = _declared_names(witness)
    hits = sorted(n for n in variant_only - own
                  if re.search(rf"(?<![A-Za-z0-9_.']){re.escape(n)}"
                               r"(?![A-Za-z0-9_'])", w))
    if not hits:
        return []
    return [f"witness references {hits} — declared by the variant but not by "
            "the frozen solution, so its failure on gold would be an unknown "
            "name rather than a satisfied spec"]


# The frozen spec's own names: the lean predicate, and the velvet method whose
# obligation `prove_correct` discharges.
_SPEC_PREDICATE = re.compile(r"\b(problem_spec_[A-Za-z0-9_']+)")
_PROVE_CORRECT_NAME = re.compile(r"^[ \t]*prove_correct[?]?[ \t]+(\S+)", re.M)
# Velvet states its refutations over a spec-DERIVED decision procedure rather
# than over the obligation directly: `derive_tester_for m` builds `mTester` from
# m's own require/ensures, and `extract_program_for m` builds `mExec`. Both are
# generated FROM the frozen clauses, so a claim about them is a claim about the
# spec; the directives are inside the witness and appended to both files, so the
# names exist on both sides by construction.
_WITNESS_DERIVES = re.compile(
    r"^[ \t]*(?:derive_tester_for|extract_program_for)[ \t]+(\S+)", re.M)
# `by`, as a standalone token: everything after the LAST one is tactic script,
# and what a witness ASSERTS is everything before it. Not `:=` — that also
# separates structure-instance fields inside a binder type.
_TACTIC_START = re.compile(r"(?<![A-Za-z0-9_'])by(?![A-Za-z0-9_'])")


def _statement_of(witness: str) -> str:
    """The witness minus its tactic script."""
    ms = list(_TACTIC_START.finditer(witness))
    return witness[:ms[-1].start()] if ms else witness


def _mentions(name: str, text: str) -> bool:
    return bool(re.search(rf"(?<![A-Za-z0-9_.']){re.escape(name)}"
                          r"(?![A-Za-z0-9_'])", text))


def witness_anchor_problems(frozen: str, witness: object) -> list[str]:
    """Reasons the witness does not state a claim ABOUT THE SPEC.

    The two-build check establishes that a claim holds of the rival and fails of
    gold. That is a claim about a DIFFERENCE between two implementations, and a
    difference is not a violation: `example : implementationCount 3 = 5 := by
    decide` holds of a rival, fails of gold, uses no banned token, declares an
    `example` and references no variant-only name, on a spec that may be perfectly
    strong. "Differs from gold" is exactly the inference the witness rule exists
    to replace, re-entered one level up.

    So the witness's STATEMENT (not its tactic body, where an `unfold
    problem_spec_x` is routine) must mention the frozen spec: the
    `problem_spec_*` predicate on lean, or on velvet the method whose obligation
    is frozen — including via `derive_tester_for`/`extract_program_for`, which
    generate a decision procedure FROM that method's own require/ensures.

    Padding a difference claim with a true conjunct about the predicate would
    clear a purely lexical check like this one. That is a narrower hole and it is
    not silent: the conjunct has to elaborate on both sides, so it shows up in the
    case's own witness text for an auditor to read.
    """
    if not isinstance(witness, str) or not witness.strip():
        return []
    anchors = set(_SPEC_PREDICATE.findall(frozen))
    anchors |= set(_PROVE_CORRECT_NAME.findall(frozen))
    if not anchors:
        # No recognizable spec anchor in the frozen file (a backend or shape this
        # does not model). Silence beats a false MALFORMED on every case.
        return []
    for m in _WITNESS_DERIVES.findall(witness):
        anchors |= {m + "Tester", m + "Exec"}
    st = _strip_lean_comments(_statement_of(witness))
    if any(_mentions(a, st) for a in anchors):
        return []
    return ["witness states no claim about the frozen spec: its statement "
            f"mentions none of {sorted(anchors)[:6]}, so proving it of the rival "
            "and failing it on gold shows the two impls DIFFER, not that the "
            "rival violates the spec"]


def witness_problems(witness: object) -> list[str]:
    """Cheap shape check on a witness, before any build.

    Bans every form that lets a witness ASSUME its conclusion instead of
    establishing it. `axiom cheat : <the refutation> ... := cheat` elaborates
    against anything, so without this a witness could assert exactly what it is
    supposed to prove. That particular forgery is self-limiting — it elaborates
    against gold too, so the discrimination half records `witness-vacuous`
    (inconclusive -> MALFORMED-TESTS) rather than a pass — but a regex that costs
    nothing is a better place to catch it than a later build. Comments are
    stripped first so a witness may explain in prose why it does NOT reach for
    these.
    """
    if not isinstance(witness, str) or not witness.strip():
        return ["no 'witness' snippet"]
    w = _strip_lean_comments(witness)
    for tok in _WITNESS_BANNED:
        if _WITNESS_BANNED_RES[tok].search(w):
            return [f"witness uses {tok!r}: it would elaborate regardless"]
    if not re.search(r"^\s*(example|theorem|lemma)\b", w, re.MULTILINE):
        return ["witness declares no `example`/`theorem`/`lemma` to check"]
    return []
