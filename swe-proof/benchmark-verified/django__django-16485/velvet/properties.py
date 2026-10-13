"""properties.py — G-PBT falsification battery for django__django-16485 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct numericDisplay`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

This is a PORT of the nagini sibling battery, re-expressed against this
backend's carrier. The nagini surface contracts a value-builder that
MATERIALIZES the whole rendered character sequence (sign, each digit, the
separator, each fractional zero) and pins ToSeq(Result()) to a grounded oracle
`rendered`. This bundle narrows the modeled behavior to the ROUTINE'S ONE
DECISION: which of two pre-computed renderings to emit. The two renderings are
UNCHANGED sub-results of the surrounding code, taken as read-only method inputs
(`intView` / `fracView`) whose character content is NOT on this carrier — so the
nagini rivals that attack the internal content of a rendering (a dropped
separator, a constant digit, a mis-filled fractional field) have no counterpart
here and are omitted for that reason, recorded in the accounting below.

DEFENDED SURFACE (one contracted method over FOUR read-only inputs, no
``require`` clause — the admitted domain is total).

  numericDisplay (isWhole p intView fracView)
        ensures out = (if isWhole = true ∧ p ≤ 0 then intView else fracView)

ONE method, ONE top-level post-image clause: a two-way selection. Its
sub-structure is a guard `isWhole = true ∧ p ≤ 0` and two arms (`intView` on the
true side, `fracView` on the false side). All four inputs are FREE: the
post-image must hold for every value each takes, which is what makes the rivals
below refutable at a concrete point.

CARRIER NOTE — FULLY TRANSPARENT. Unlike siblings whose spec routes through an
``opaque`` leaf, every input here is a concrete decidable value (`Bool`, `Int`,
`List Char`), and the post-image is a plain ``if``-selection over them. So every
reject witness reaches the post-image through Velvet's tester machinery
(`numericDisplayTester args = false`) at fully concrete literals and closes by
``decide`` — no conditioning on an opaque carrier is needed, and no clause is
blocked from a direct witness.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a pass-by-reference input can carry a fractional heap permission an
    impl overwrites. This backend is referentially transparent, has no heap and
    no aliasing, and this bundle declares no ``mut`` binder — there is no
    read-only input to overwrite and no substitute probe to fabricate. (The
    sibling itself records this class as N/A: all its inputs are pass-by-value
    primitives.)
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    ``if``-selection over the method's own arguments; there is no ``axiom`` and
    no ``opaque`` answer-key to echo (the ``axioms`` region is empty). So there
    is no WRONG echo to build; the positive controls are honest cheapest-reshape
    controls, mirroring the sibling's grounded-oracle framing.
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the domain but
    diverging on a sub-domain (the boundary class {isWhole ∧ p == 0}; the
    off-integral sub-domain; either arm returned unconditionally).
  * FREE-INPUT PRESERVATION — APPLIES: the post-image's decision depends on all
    four free inputs. A rival can get the shape right and still mishandle the
    guard (isWhole conjunct, the p ≤ 0 boundary) or return the wrong arm, so each
    is attacked on its own so its witness sits at a point the others do not
    probe.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The four reject witnesses sit at four DISTINCT input points
and between them move all four binders off any fixed value: ``isWhole`` takes
both true and false; ``p`` takes negative, zero, and positive; ``intView`` and
``fracView`` each take two distinct values, and the arm-selection rivals make the
result genuinely depend on each (see the coverage note at the foot).

AXIOM lane: this bundle consumes NO ``axiom`` (``axioms`` region empty;
meta.json axioms == [], deep_model_references == []). There is no
axiom-soundness obligation for this gate to probe, and the gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16485"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- (between -- impl-start / -- impl-end) and unique in the file. Both facts
# ---- are asserted at load by _swap. ----
_IMPL_GOLD = (
    "    if isWhole = true ∧ p ≤ 0 then\n"
    "      return intView\n"
    "    else\n"
    "      return fracView"
)
assert _IMPL_GOLD in _BASE and _BASE.count(_IMPL_GOLD) == 1, "impl anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- positive control that reshapes the impl keeps this verbatim (the
# ---- post-image is a decidable selection, so no reshape here needs a new
# ---- lemma), and the admissibility case's in-region assert is discharged by
# ---- the same `loom_solve`. ----
_PROOF_GOLD = "prove_correct numericDisplay by\n  loom_solve"
assert _PROOF_GOLD in _BASE and _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester
# ---- machinery: `numericDisplayTester args = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped by
# ---- the gate, so no tactic script can mask the verdict. Every argument is a
# ---- concrete literal (Bool, Int, List Char), so `decide` reduces the whole
# ---- selection without touching any abstract term. ----
_TESTER = (
    "extract_program_for numericDisplay\n"
    "prove_precondition_decidable_for numericDisplay\n"
    "prove_postcondition_decidable_for numericDisplay\n"
    "derive_tester_for numericDisplay\n\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof script.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Invert the guard so the fractional-rendering case is the `if`
        # (predicate `¬(isWhole = true ∧ p ≤ 0)`) and the integer-rendering case
        # is the `else`. The two regimes are mutually exclusive + exhaustive, so
        # this returns identical values.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    if ¬(isWhole = true ∧ p ≤ 0) then\n"
            "      return fracView\n"
            "    else\n"
            "      return intView"),
        "rationale": "structurally-different CORRECT impl: invert the regime "
                     "guard so the fractional case is the `if` and the integer "
                     "case the `else`. The two arms are mutually exclusive + "
                     "exhaustive, so `out = (if isWhole = true ∧ p ≤ 0 then "
                     "intView else fracView)` still holds; if a faithful "
                     "reordering cannot verify => SPEC-TOO-STRONG. Ports the "
                     "sibling pos-branch-reorder.",
    },
    {
        "id": "pos-bare-local",
        "kind": "soundness",
        "expect": "verify",
        # Hoist the regime predicate into a typed boolean local `bare` and
        # branch on it. Identical control flow + values.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let bare : Bool := isWhole = true ∧ p ≤ 0\n"
            "    if bare = true then\n"
            "      return intView\n"
            "    else\n"
            "      return fracView"),
        "rationale": "local-variable reshape: hoist the regime predicate into a "
                     "typed boolean local `bare = (isWhole = true ∧ p ≤ 0)` and "
                     "branch on it. Identical control flow + values; the honest "
                     "cheapest impl that does the work (the post-image is a "
                     "grounded selection over the inputs, so it doubles as the "
                     "grounded-oracle positive control). If it cannot verify => "
                     "SPEC-TOO-STRONG. Ports the sibling pos-bare-local.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous. Re-aimed at the
    # residual admissibility risk on a total domain: that the post-image is
    # DEGENERATE at the interesting point (a spec no impl can meet reads like a
    # spec every impl meets). This case discharges an in-region `assert`, at the
    # exact F2P-shaped input {isWhole=true, p=0}, that the selection is
    # NON-DEGENERATE: the guard fires the integer arm there, and the two arms are
    # distinguishable (a concrete `intView` ≠ `fracView` witness value). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges, and the frozen proof body (`loom_solve`) clears the extra
    # assert goal too — the assert is live (a false claim leaves `⊢ False`), not
    # decoration.
    # =====================================================================
    {
        "id": "admiss-f2p-zero",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    assert (with_name_prefix `admiss\n"
            "      ((if true = true ∧ (0 : Int) ≤ 0 then ['0'] else ['x']) = ['0']))\n"
            + _IMPL_GOLD),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input {isWhole=true, p=0} (the whole-value / "
                     "zero-requested-digits case the issue reports): the guard "
                     "`true = true ∧ 0 ≤ 0` fires the INTEGER arm, and the arms "
                     "are distinguishable there (`['0'] ≠ ['x']`), so the "
                     "selection genuinely discriminates the case the fix targets. "
                     "The in-region assert must discharge (else a degenerate "
                     "obligation); the impl is kept verbatim so the ensures "
                     "clause discharges too. Re-aims the sibling admiss-f2p-zero "
                     "(which asserts the grounded oracle routes {0,True,0} to the "
                     "bare integer) to this backend's selection carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "uniq-prepatch-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG (== Solution_prepatch.lean). Revert the guard to the pre-patch
        # `p < 0`. On the boundary class {isWhole=true ∧ p==0} this takes the
        # else arm and returns the fractional rendering where the post-image
        # demands the integer rendering.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    if isWhole = true ∧ p < 0 then\n"
            "      return intView\n"
            "    else\n"
            "      return fracView"),
        "refinement": "this IS the pre-patch behaviour: the real dispatch guard "
                      "routes a whole value asked for zero fractional digits into "
                      "the fractional-rendering branch. That branch computes a "
                      "precision of zero and constructs a decimal context with "
                      "precision zero, which the standard decimal library rejects "
                      "with a valid-range error — the exact crash the issue "
                      "reports, and the sole failing test asserts is fixed (a "
                      "whole value shown with zero fractional digits renders as "
                      "the bare integer). The faithful counterpart (the unchanged "
                      "`p < 0` guard) does NOT resolve the failing test.",
        "rationale": "REJECT from `out = (if isWhole = true ∧ p ≤ 0 then intView "
                     "else fracView)`: on {isWhole=true ∧ p==0} the post-image "
                     "selects `intView` but the rival's guard `p < 0` is false, "
                     "so it returns `fracView`. The single changed boundary token "
                     "`<` vs `≤` is exactly what the post-image senses. Refuted at "
                     "{isWhole=true, p=0, intView=['0'], fracView=['x']}, the "
                     "boundary point.",
        "witness": _TESTER +
                   "example : numericDisplayTester true 0 ['0'] ['x'] = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "uniq-drop-iswhole",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `isWhole` conjunct from the guard (`if p ≤ 0`). Now a
        # non-whole value at p ≤ 0 (isWhole=false, p ≤ 0) takes the integer arm
        # and returns `intView`, but the post-image selects `fracView`.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    if p ≤ 0 then\n"
            "      return intView\n"
            "    else\n"
            "      return fracView"),
        "refinement": "dropping the whole-value conjunct routes a NON-whole value "
                      "at a non-positive requested-digit count into the integer "
                      "rendering. The passing tests pin non-whole values at "
                      "negative requested-digit counts to KEEP their fractional "
                      "digits (e.g. a value with a fractional part shown with a "
                      "small negative count rounds to that many fractional "
                      "places, not to the bare integer). A counterpart guarding "
                      "on the count alone would render those as bare integers, "
                      "failing those assertions; it does NOT resolve.",
        "rationale": "REJECT from the post-image: on {isWhole=false ∧ p ≤ 0} the "
                     "post-image selects `fracView`, but the rival returns "
                     "`intView`. The `isWhole` conjunct in the guard is "
                     "load-bearing. Refuted at {isWhole=false, p=0, "
                     "intView=['a'], fracView=['b']} — the only witness that "
                     "moves the `isWhole` binder to false. Ports the sibling "
                     "uniq-drop-fraczero.",
        "witness": _TESTER +
                   "example : numericDisplayTester false 0 ['a'] ['b'] = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "uniq-always-fracview",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the fractional rendering unconditionally (corrupt the true arm).
        # On the whole-value / non-positive-count sub-domain the post-image
        # selects the integer rendering, so this diverges there. Attacks the
        # INTEGER-arm selection and makes the result depend on `intView`.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    if isWhole = true ∧ p ≤ 0 then\n"
            "      return fracView\n"
            "    else\n"
            "      return fracView"),
        "refinement": "emitting the fractional rendering unconditionally is a "
                      "counterpart that never selects the integer rendering — so "
                      "the whole-value / zero-count case still goes through the "
                      "crash-prone fractional branch and the failing test is not "
                      "fixed; it does NOT resolve.",
        "rationale": "REJECT from the post-image: on {isWhole=true ∧ p ≤ 0} the "
                     "post-image selects `intView`, but the rival returns "
                     "`fracView`. Refuted at {isWhole=true, p=-2, intView=['a'], "
                     "fracView=['b']}: the post-image reads `intView=['a']`, the "
                     "rival emits `fracView=['b']`. This is the witness that "
                     "moves `p` to a strictly negative value and makes the result "
                     "genuinely depend on `intView` (the integer arm). Re-aims "
                     "the sibling's integer-rendering content rivals "
                     "(uniq-const-zero-bare) to this backend's arm-selection "
                     "carrier, on which the rendering content is not modeled.",
        "witness": _TESTER +
                   "example : numericDisplayTester true (-2) ['a'] ['b'] = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "uniq-always-intview",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the integer rendering unconditionally (corrupt the false arm).
        # On the fractional sub-domain (not whole, or positive count) the
        # post-image selects the fractional rendering, so this diverges there.
        # Attacks the FRACTIONAL-arm selection and makes the result depend on
        # `fracView`.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    if isWhole = true ∧ p ≤ 0 then\n"
            "      return intView\n"
            "    else\n"
            "      return intView"),
        "refinement": "emitting the integer rendering unconditionally is a "
                      "counterpart that never selects the fractional rendering — "
                      "so a value asked for a positive count of fractional digits "
                      "(e.g. shown with three fractional places) renders as its "
                      "bare integer instead, failing the passing tests that pin "
                      "the fractional output; it does NOT resolve.",
        "rationale": "REJECT from the post-image: on the fractional sub-domain "
                     "(here p > 0) the post-image selects `fracView`, but the "
                     "rival returns `intView`. Refuted at {isWhole=true, p=3, "
                     "intView=['a'], fracView=['b']}: the post-image reads "
                     "`fracView=['b']`, the rival emits `intView=['a']`. This is "
                     "the witness that moves `p` to a strictly positive value and "
                     "makes the result genuinely depend on `fracView` (the "
                     "fractional arm). Re-aims the sibling's separator/fill "
                     "content rivals (uniq-drop-separator / uniq-wrong-frac-fill) "
                     "to this backend's arm-selection carrier.",
        "witness": _TESTER +
                   "example : numericDisplayTester true 3 ['a'] ['b'] = false "
                   ":= by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals + 1 documented-but-excluded
# near-miss) against ONE contracted value-builder `format_value` that
# MATERIALIZES the whole rendered character sequence and pins it to a grounded
# oracle `rendered`. This bundle NARROWS the modeled behavior to the routine's
# ONE decision — which of two pre-computed renderings to emit — with the two
# renderings taken as read-only method inputs whose character content is NOT on
# this carrier. So the sibling's content-attacking rivals collapse: each is
# re-aimed at the arm SELECTION or omitted as off-carrier.
#
#   sibling case            -> here
#   ------------------------------------------------------------------
#   pos-branch-reorder      -> pos-branch-reorder        PORTED
#   pos-bare-local          -> pos-bare-local            PORTED
#   admiss-f2p-zero         -> admiss-f2p-zero           RE-AIMED (selection non-degeneracy)
#   uniq-prepatch-guard     -> uniq-prepatch-guard       PORTED (the core bug)
#   uniq-drop-fraczero      -> uniq-drop-iswhole         PORTED
#   uniq-drop-separator     -> uniq-always-intview       RE-AIMED (content off-carrier)
#   uniq-const-zero-bare    -> uniq-always-fracview      RE-AIMED (content off-carrier)
#   uniq-wrong-frac-fill    -> (folded into uniq-always-intview) OMITTED (content off-carrier)
#   (frame-mutation)        -> (none)                    VACUOUS
#
# 4 ported/re-aimed positives+admiss, 4 reject rivals; 2 nagini cases omitted.
#
# RE-AIMED (admiss-f2p-zero): the sibling injects an in-impl assert that the
#   grounded oracle routes the F2P input {int_value=0, frac_zero=True, p=0} to
#   the bare-integer rendering. This backend has no grounded oracle to route (the
#   two renderings are opaque inputs) and no `require` clause, so the probe is
#   re-aimed at the residual total-domain risk: that the SELECTION is degenerate
#   at that point. The in-region assert pins that at {isWhole=true, p=0} the
#   guard fires the integer arm and the arms are distinguishable.
# RE-AIMED (uniq-drop-separator, uniq-const-zero-bare): the sibling rivals attack
#   the INTERNAL CHARACTER CONTENT of a rendering — a dropped '.' separator, a
#   constant '0' digit. This bundle models the two renderings as opaque read-only
#   inputs (`intView` / `fracView`), so their content is off-carrier and no rival
#   can mutate it. The load-bearing residue on this carrier is the SELECTION of
#   the wrong rendering, which uniq-always-intview / uniq-always-fracview attack:
#   returning the integer rendering where the fractional one is demanded (and vice
#   versa) is exactly the whole-message divergence those sibling rivals produce,
#   witnessed at the arm boundary rather than at a character index.
# OMITTED (uniq-wrong-frac-fill): the sibling itself flags this as a SUPPORTING
#   near-miss whose rejection is attributable to an A-reference skeleton's
#   over-pin of the fractional-fill content, NOT a primary verify-does-not-resolve
#   break. That content is entirely off this carrier (the fractional rendering is
#   an opaque input), so there is no counterpart to build; its selection-level
#   spirit is already covered by uniq-always-intview. Dropped, not faked.
# VACUOUS (frame-mutation): the #1 sibling class is N/A even in nagini here (all
#   inputs pass-by-value). On this referentially transparent backend with no
#   `mut` binder there is likewise no read-only input to overwrite and no
#   substitute probe. Not fabricated.
#
# COVERAGE. Binders moved by the reject witnesses: isWhole {true, false};
#   p {-2, 0, 3} (negative / zero / positive — the boundary token the fix turns
#   on is p, and it is varied across its sign); intView {['0'], ['a']};
#   fracView {['x'], ['b']}. The arm-selection rivals make the result genuinely
#   depend on intView (uniq-always-fracview: gold reads intView, rival reads
#   fracView) and on fracView (uniq-always-intview: gold reads fracView, rival
#   reads intView), so both view binders are discriminated, not merely present.
#   pts = 4 distinct input points. The ONE top-level clause (the if-selection) is
#   attacked at its guard (uniq-prepatch-guard hits the p ≤ 0 boundary;
#   uniq-drop-iswhole hits the isWhole conjunct) and at both arms
#   (uniq-always-fracview / uniq-always-intview). No sub-term is left unattacked.
#
# AXIOM_TESTS: dropped. This bundle consumes no `axiom` and declares no
#   A-reference (meta.json axioms == [], deep_model_references == []); G-AX is a
#   skip. Nothing here for this gate to probe, and it ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
