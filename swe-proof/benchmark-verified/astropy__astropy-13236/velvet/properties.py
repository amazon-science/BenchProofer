"""properties.py — G-PBT falsification battery for astropy__astropy-13236 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical header) and swaps
in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over two read-only inputs).

  classifyColumn (input tableIsMasked)
      ensures out = classify input tableIsMasked                          -- master
      ensures (input = .structuredPlain ∧ tableIsMasked = false)
                → out = .columnKind                                       -- C2
      ensures input = .structuredMasked → out = .maskedColumnKind         -- C3
      ensures input = .alreadyMixin → out = .mixinKind                    -- C4
      ensures (out = .mixinKind) → (input = .alreadyMixin)                -- C5

A value offered to a table as a new column is CLASSIFIED into a column-class
kind by its shape (``input : InputShape``) and the host table's masked-ness
(``tableIsMasked : Bool``). The desired behaviour: a value already a mixin
column is the ONLY value kept as a mixin column (C4 + C5); a mask-carrying value
becomes a masked column so its mask is preserved, whatever the table (the
``structuredMasked`` / ``plainMasked`` arms); every other value — an existing
ordinary column, a multi-field structured array, or any other plain array — is
classified PURELY by the table's masked-ness (masked column in a masked table,
ordinary column otherwise). In particular a multi-field structured array is
classified by the same rule as any other array of its masked-ness — it is NOT
singled out for the mixin class (C2 + C5). ``classify`` is a total, fully
unfolded function of the method's own two arguments; both inputs are FREE (no
``require`` clause, no ``mut`` binder), which is what makes the partial-domain
rivals below refutable at a concrete point.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the nagini
    sibling because a by-value/by-reference input may carry a fractional heap
    permission an impl can overwrite. This backend is referentially transparent,
    there is no heap and no aliasing, and this bundle declares no ``mut`` binder
    at all — so there is no read-only input to overwrite and no substitute probe
    to fabricate. Reported as an omission, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``classify`` is a total, fully
    unfolded function of the method's own arguments (``classify`` is a concrete
    ``def`` in the ``pure`` region; the ``axioms`` region declares NO ``axiom`` —
    there is no opaque answer key to echo). So there is no WRONG echo to build;
    the positive controls are honest cheapest-reshape controls instead.
  * PARTIAL-DOMAIN / VALUE — the heart of this surface. A rival right on part of
    the shape domain but diverting a sub-domain into the wrong column kind (a
    structured array — masked, unmasked, or both — into the mixin kind; a value
    that carries a mask classified by the table instead of preserved; an existing
    mixin value classified by the table instead of kept).
  * FREE-INPUT PRESERVATION — the post-image carries TWO free inputs (the value's
    shape and the table's masked-ness). A rival can get one shape's classification
    right and still misclassify another, so the reject witnesses move BOTH binders
    off any fixed value.

WITNESS PLACEMENT. Rivals do not share a refutation point unless they fail there
for the same reason. The five reject witnesses sit at five DISTINCT input points
and between them move both binders off any fixed value: ``input`` takes four
distinct shapes (structuredPlain, structuredMasked, alreadyMixin, plainMasked)
and ``tableIsMasked`` takes both ``false`` and ``true``. The two structured-only
near-misses are refuted at MIRROR masked-ness points (the masked-only rival at a
masked structured value, the unmasked-only rival at an unmasked structured value)
so neither pins the table's masked-ness input.

AXIOM lane: DROPPED. The axiom lane is G-AX's job and the gate ignores
``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom`` (the classification
is modeled deeply as ``classify``; ``meta.json`` axioms == []), so there is
nothing in that lane for this spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13236"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the gold impl body: a single anchor lying wholly inside the impl region
# ---- and unique in the file (both facts asserted at load by _swap). The
# ---- `classify` def in the `pure` region uses a different `| .case, arg =>`
# ---- syntax, so this `match input with` / `return result` block is unique. ----
_IMPL_GOLD = (
    "    let result : ColumnKind :=\n"
    "      match input with\n"
    "      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind\n"
    "      | .alreadyMixin     => .mixinKind\n"
    "      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind\n"
    "      | .structuredMasked => .maskedColumnKind\n"
    "      | .plainMasked      => .maskedColumnKind\n"
    "      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind\n"
    "    return result"
)
assert _IMPL_GOLD in _BASE, "impl anchor drift: classifyColumn body not verbatim"

# ---- the frozen proof body (tactic script only; elided from the spec view, so
# ---- a positive control that reshapes the impl or an admissibility case that
# ---- adds an in-region assert may retune it without touching the spec or the
# ---- `prove_correct` header). ----
_PROOF_GOLD = (
    "prove_correct classifyColumn by\n"
    "  loom_solve\n"
    "  cases input <;> cases tableIsMasked <;> simp_all [classify]"
)
assert _PROOF_GOLD in _BASE, "proof anchor drift"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `classifyColumnTester args = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. Every argument is a concrete constructor literal so
# ---- `decide` reduces fully (both carriers derive DecidableEq). ----
_TESTER = (
    "extract_program_for classifyColumn\n"
    "prove_precondition_decidable_for classifyColumn\n"
    "prove_postcondition_decidable_for classifyColumn\n"
    "derive_tester_for classifyColumn\n\n"
)


def _rival_impl(sp, sm, am):
    """Build a rival impl body varying the structuredPlain / structuredMasked /
    alreadyMixin arms; all other arms stay the frozen gold arms."""
    return (
        "    let result : ColumnKind :=\n"
        "      match input with\n"
        "      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind\n"
        "      | .alreadyMixin     => " + am + "\n"
        "      | .structuredPlain  => " + sp + "\n"
        "      | .structuredMasked => " + sm + "\n"
        "      | .plainMasked      => .maskedColumnKind\n"
        "      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind\n"
        "    return result"
    )


_GOLD_SP = "if tableIsMasked then .maskedColumnKind else .columnKind"
_GOLD_SM = ".maskedColumnKind"
_GOLD_AM = ".mixinKind"
_BY_TABLE = "if tableIsMasked then .maskedColumnKind else .columnKind"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof
    # script (the post-image is a point-wise equality that `cases input <;>
    # cases tableIsMasked <;> simp_all [classify]` closes regardless of the
    # executable arm order).
    # =====================================================================
    {
        "id": "pos-grouped-wildcard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the three arms that classify purely by the table's masked-ness
        # are collapsed into one grouped `_` wildcard, the three intrinsic-kind
        # arms kept explicit. Same value on every shape.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let result : ColumnKind :=\n"
            "      match input with\n"
            "      | .alreadyMixin     => .mixinKind\n"
            "      | .structuredMasked => .maskedColumnKind\n"
            "      | .plainMasked      => .maskedColumnKind\n"
            "      | _                 => if tableIsMasked then .maskedColumnKind else .columnKind\n"
            "    return result"),
        "rationale": "collapsing the three by-table-masked-ness arms into one "
                     "grouped wildcard classifies every shape to the SAME kind as "
                     "the frozen dispatch, so `out = classify input tableIsMasked` "
                     "and all four discriminating clauses still hold; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG on arm grouping.",
    },
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: permute the match arms (the three intrinsic-kind arms first,
        # the by-table arms last). A `match` is order-independent on disjoint
        # constructors, so the returned value is unchanged on every shape.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "    let result : ColumnKind :=\n"
            "      match input with\n"
            "      | .alreadyMixin     => .mixinKind\n"
            "      | .structuredMasked => .maskedColumnKind\n"
            "      | .plainMasked      => .maskedColumnKind\n"
            "      | .alreadyColumn    => if tableIsMasked then .maskedColumnKind else .columnKind\n"
            "      | .structuredPlain  => if tableIsMasked then .maskedColumnKind else .columnKind\n"
            "      | .plainOther       => if tableIsMasked then .maskedColumnKind else .columnKind\n"
            "    return result"),
        "rationale": "permuting the match arms over disjoint constructors leaves "
                     "the classification of every shape unchanged, so the "
                     "post-image is unchanged; a correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — no method here has a `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous: nothing
    # could exclude an F2P-shaped input. The residual admissibility risk on a
    # total domain is that the post-image is UNSATISFIABLE / DEGENERATE at the
    # interesting point — a spec no impl can meet reads exactly like a spec every
    # impl meets. This case discharges an in-region `assert`, at concrete
    # F2P-shaped points, that the classification is NON-DEGENERATE: an unmasked
    # structured value is an ordinary column (and, crucially, NOT the mixin kind),
    # a masked structured value is a masked column. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the proof body is
    # retuned only to clear the extra assert goal by `decide` (allowed — the
    # tactic body is elided from the spec view). The assert is live, not
    # decoration: a false claim about the same points leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-classification-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                "    assert (with_name_prefix `admiss\n"
                "      (classify .structuredPlain false = .columnKind\n"
                "        ∧ classify .structuredMasked true = .maskedColumnKind\n"
                "        ∧ classify .structuredPlain false ≠ .mixinKind))\n"
                + _IMPL_GOLD),
            _PROOF_GOLD,
            "prove_correct classifyColumn by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (cases input <;> cases tableIsMasked <;> simp_all [classify])"),
        "rationale": "the post-image is satisfiable AND non-degenerate at concrete "
                     "F2P-shaped points: an unmasked structured value classifies to "
                     "the ordinary column kind (and is NOT diverted to the mixin "
                     "kind), a masked structured value classifies to the masked "
                     "column kind — the two behaviours the failing tests demand. "
                     "The in-region assert must discharge (else the obligation is "
                     "unsatisfiable/degenerate at the interesting point); the impl "
                     "is kept verbatim so `out = classify input tableIsMasked` "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-structured-to-mixin",
        "kind": "uniqueness",
        "expect": "reject",
        # Diverts EVERY multi-field structured value (masked or unmasked) into the
        # mixin kind — the pre-image classification the fix removes.
        "module": _swap(_BASE, _IMPL_GOLD,
                        _rival_impl(".mixinKind", ".mixinKind", _GOLD_AM)),
        "refinement": "this is the pre-image classification: a multi-field "
                      "structured value is singled out and wrapped in the mixin "
                      "kind. The failing tests add exactly such values and assert "
                      "the unmasked one becomes an ORDINARY column and the masked "
                      "one a MASKED column with its per-field mask preserved; a "
                      "faithful counterpart that keeps diverting structured values "
                      "to the mixin kind reproduces the pre-image behaviour, so "
                      "both tests still fail. It does NOT resolve.",
        "rationale": "REJECT from the master clause `out = classify input "
                     "tableIsMasked`, from C2 (unmasked structured → column kind), "
                     "C3 (masked structured → masked column), AND C5 (only an "
                     "already-mixin value may be the mixin kind); this rival "
                     "returns the mixin kind for structured values. Refuted at an "
                     "unmasked structured value (C2's exact antecedent).",
        "witness": _TESTER +
                   "example : classifyColumnTester .structuredPlain false = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "weak-masked-structured-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: diverts ONLY the masked structured value to the mixin kind,
        # leaving the unmasked structured value correct.
        "module": _swap(_BASE, _IMPL_GOLD,
                        _rival_impl(_GOLD_SP, ".mixinKind", _GOLD_AM)),
        "refinement": "diverts only the MASKED structured value to the mixin kind. "
                      "Its faithful counterpart keeps the structured-value "
                      "diversion guarded to the masked case: a masked structured "
                      "value would still be wrapped as a mixin, failing the test "
                      "that requires a masked column with the per-field mask "
                      "preserved. It does NOT resolve. (It classifies the unmasked "
                      "structured value correctly, so it is a genuine "
                      "partial-domain rival, right on the unmasked half.)",
        "rationale": "REJECT from C3 (masked structured → masked column) and C5; "
                     "this rival returns the mixin kind there. Refuted at a masked "
                     "structured value in a MASKED table — the MIRROR of the "
                     "unmasked-only rival, so neither near-miss pins the "
                     "table-masked-ness input.",
        "witness": _TESTER +
                   "example : classifyColumnTester .structuredMasked true = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "weak-unmasked-structured-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Complementary near-miss: diverts ONLY the unmasked structured value to
        # the mixin kind, leaving the masked structured value correct.
        "module": _swap(_BASE, _IMPL_GOLD,
                        _rival_impl(".mixinKind", _GOLD_SM, _GOLD_AM)),
        "refinement": "the complementary half: diverts only the UNMASKED "
                      "structured value to the mixin kind. Its faithful "
                      "counterpart keeps the diversion guarded to the unmasked "
                      "case: an unmasked structured value would still be wrapped "
                      "as a mixin, failing the test that requires an ordinary "
                      "column. It does NOT resolve. (It classifies the masked "
                      "structured value correctly — partial-domain, right on the "
                      "masked half.)",
        "rationale": "REJECT from the master clause and C5; this rival returns the "
                     "mixin kind for an unmasked structured value. Refuted at an "
                     "unmasked structured value in a MASKED table — the mirror of "
                     "the masked-only rival, so the table-masked-ness binder is "
                     "moved between the two near-misses.",
        "witness": _TESTER +
                   "example : classifyColumnTester .structuredPlain true = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "weak-mixin-classified-by-table",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C4 / the alreadyMixin binder: an existing mixin value is
        # classified by the table's masked-ness instead of being kept a mixin.
        "module": _swap(_BASE, _IMPL_GOLD,
                        _rival_impl(_GOLD_SP, _GOLD_SM, _BY_TABLE)),
        "refinement": "an existing mixin value is (wrongly) classified by the "
                      "table's masked-ness rather than kept a mixin. Its faithful "
                      "counterpart alters the UNCHANGED already-a-mixin path so a "
                      "value that is already a valid mixin column is re-wrapped as "
                      "an ordinary/masked column — diverging from the pass-through "
                      "behaviour the mixin-preservation test relies on. It does NOT "
                      "resolve those pass-to-pass tests (and re-wraps the "
                      "structured value explicitly viewed as a mixin, too).",
        "rationale": "REJECT from C4 (already-mixin value → mixin kind): the rival "
                     "returns the ordinary column kind for an already-mixin value "
                     "in an unmasked table. This is the only rival that moves the "
                     "`input` binder to the already-mixin shape, so C4's antecedent "
                     "is the sole binder value it probes.",
        "witness": _TESTER +
                   "example : classifyColumnTester .alreadyMixin false = false "
                   ":= by\n  decide\n",
    },
    {
        "id": "weak-mask-not-preserved",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the mask-preservation arm / the plainMasked binder: a
        # mask-carrying (non-structured) value is classified by the table's
        # masked-ness instead of always becoming a masked column.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            _IMPL_GOLD.replace(
                "      | .plainMasked      => .maskedColumnKind\n",
                "      | .plainMasked      => if tableIsMasked then .maskedColumnKind else .columnKind\n")),
        "refinement": "a mask-carrying value in an UNMASKED table is classified as "
                      "an ordinary column, dropping the mask, instead of always "
                      "becoming a masked column. Its faithful counterpart alters "
                      "the UNCHANGED masked-array branch (which exists precisely so "
                      "a mask-carrying value is preserved even in an unmasked "
                      "table) to defer to the table's class — diverging from the "
                      "real behaviour and from the pass-to-pass masking tests that "
                      "rely on it. It does NOT resolve those tests.",
        "rationale": "REJECT from the master clause `out = classify input "
                     "tableIsMasked`: a mask-carrying value classifies to the "
                     "masked column kind for ANY table, and the rival returns the "
                     "ordinary column kind in an unmasked table. This is the only "
                     "rival that moves the `input` binder to the plainMasked shape.",
        "witness": _TESTER +
                   "example : classifyColumnTester .plainMasked false = false "
                   ":= by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals) over a 9-boolean decision
# procedure `select_column_kind`. This bundle models the SAME classification as
# ONE method `classifyColumn` whose two inputs (`input : InputShape`,
# `tableIsMasked : Bool`) are the faithful carrier of the sibling's booleans
# reduced to the disjoint distinctions the selection reacts to (mapping.md §2).
#
#   sibling case                             -> here
#   -----------------------------------------------------------------------
#   pos-control-reshaped-cascade             -> pos-grouped-wildcard        PORTED
#                                               + pos-arm-reorder           ADDED
#   admiss-f2p-unmasked-structured           -> admiss-classification-...   RE-AIMED
#   weak-prepatch-structured-override        -> weak-structured-to-mixin    PORTED
#   weak-masked-structured-only-override     -> weak-masked-structured-only PORTED
#   weak-unmasked-structured-only-override   -> weak-unmasked-structured-... PORTED
#   weak-branch-order-flip                   -> (none)                      OMITTED (carrier)
#   weak-dropped-masked-sequence-branch      -> weak-mask-not-preserved     PORTED (re-aimed)
#                                               + weak-mixin-classified-...  ADDED
#
# RE-AIMED (admissibility): the sibling establishes that a normal F2P-shaped
#   input satisfies the precondition (`Requires` domain facts). This backend has
#   no `require` clause, so nothing could exclude an F2P-shaped input — that probe
#   is vacuous. It is re-aimed at the residual admissibility risk on a total
#   domain: that the post-image is UNSATISFIABLE / DEGENERATE at the interesting
#   point. The case discharges an in-region assert that an unmasked structured
#   value classifies to the ordinary column kind (and NOT the mixin kind) and a
#   masked structured value to the masked column kind — the two behaviours the
#   failing tests demand.
#
# OMITTED (1): weak-branch-order-flip. The sibling swaps the `is_masked` and
#   `data0_is_mixin` (sequence-of-mixins) guards. The `data0_is_mixin` branch —
#   a sequence WHOSE ELEMENTS are mixins — is explicitly OUT OF THIS BUNDLE'S
#   MODELED SCOPE (mapping.md §2: sequences-of-mixins are among the cases the
#   issue/tests never reach and are not modeled; `InputShape` has no constructor
#   for it). With no modeled sequence-of-mixins shape there is no sub-domain on
#   which this order flip diverges, so no discriminating witness could exist on
#   this carrier. Omitted because the class collapses under carrier narrowing,
#   not because it was hard; no substitute fabricated.
#
# PORTED (re-aimed): weak-dropped-masked-sequence-branch. The sibling drops the
#   dtype-less masked-sequence branch so a mask-carrying value falls through to
#   the plain column kind. This carrier models mask-preservation on the
#   `plainMasked` shape (a mask-carrying value must become a masked column for ANY
#   table); the port `weak-mask-not-preserved` classifies that shape by the
#   table's masked-ness instead, the same divergence.
#
# ADDED (2): pos-arm-reorder (a second cheapest-reshape positive control, over the
#   match-arm order, sharing the frozen proof) and weak-mixin-classified-by-table
#   (attacks C4 — an already-mixin value must be kept a mixin — and is the only
#   rival that moves the `input` binder to the already-mixin shape; its faithful
#   counterpart re-wraps a value that is already a valid mixin column, breaking
#   the pass-to-pass mixin-preservation tests, so it does NOT resolve).
#
# COVERAGE. Independent post-image clauses attacked: master (every rival), C2 =
#   unmasked structured → column (weak-structured-to-mixin), C3 = masked
#   structured → masked column (weak-structured-to-mixin, weak-masked-structured-
#   only), C4 = already-mixin → mixin (weak-mixin-classified-by-table), C5 = only
#   already-mixin may be the mixin kind (the three structured rivals). Binders
#   moved by the reject witnesses: `input` ∈ {structuredPlain, structuredMasked,
#   alreadyMixin, plainMasked} (4 shapes); `tableIsMasked` ∈ {false, true}. Five
#   distinct input points, pts = 5. The two structured-only near-misses sit at
#   MIRROR masked-ness points so neither pins `tableIsMasked`.
#
# FRAME-MUTATION: VACUOUS. The sibling notes this class is already vacuous there
#   (all inputs by-value, no Acc permission). On this referentially-transparent
#   backend with no heap, no aliasing and no `mut` binder it is doubly vacuous —
#   no read-only input to overwrite, no substitute probe. Not fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle consumes no
#   `axiom` (the classification is modeled deeply as `classify`; meta.json
#   axioms == [], deep_model_references == []), so there is nothing here for this
#   gate to probe.
AXIOM_TESTS = []
