"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23412 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct renderDashPattern`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  renderDashPattern (phase : Int) (onoff : List Int) return (out : List Int)
    ensures out = phase :: onoff            <-- LOAD-BEARING (full construction)
    ensures out.head? = some phase          <-- THE discriminator (head = phase)
    ensures out.tail = onoff                <-- on/off sequence carried verbatim
    ensures out.length = onoff.length + 1   <-- exact length

The render-time dash pattern handed to the drawing back end must be the shape's
OWN pattern: the head is the stored phase EXACTLY (never dropped to zero) and
the tail is the stored on/off sequence, element for element, in order. The two
input binders are ``phase`` (the scalar offset) and ``onoff`` (the on/off
ink-length sequence); every clause above is a function of both, and the result
must be produced from them and not from any masked or constant substitute.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter is
    an immutable value (this bundle declares no ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer.)
  * HEAD-DROPPED-TO-ZERO — APPLIES, and is the headline SPEC-TOO-WEAK probe:
    seed the head with the literal ``0`` instead of the stored ``phase``. Agrees
    with the post-image only where ``phase = 0``, so it is refutable at any
    nonzero phase — exactly the sub-domain the failing test pins (it compares a
    nonzero-offset shape against a zero-offset shape whose on/off sequence is
    rearranged to be visually equivalent).
  * PARTIAL-DOMAIN / VALUE — APPLIES: a rival right on part of the input domain
    but diverging on a sub-domain (a one-shorter truncation dropping the last
    on/off element; a constant-tail substitute masking the on/off passthrough).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``phase :: onoff``,
    a value built ENTIRELY from the two inputs, fully unfolded; there is no
    opaque answer-key term to echo. The cheapest correct impl simply constructs
    it, which the positive controls cover honestly.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input, checked in a file
whose obligation has been stripped so no tactic script can mask the verdict. The
three witnesses sit at three DISTINCT input points and vary BOTH binders:
``phase`` ranges over 6, 2, 5 (all nonzero — the head-dropped rival AGREES with
gold at phase 0, so a discriminating witness for it MUST use a nonzero phase),
and ``onoff`` ranges over ``[6, 6]``, ``[7, 8, 9]`` and ``[1, 2]`` (distinct
lengths and contents). So no rival is refuted at a binder value another rival
holds fixed, and the manifest demonstrates the post-image's dependence on each
binder rather than its value at a single pinned point.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23412"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap). The
# ---- 4-space-indented `return` form does not occur in the `ensures` clauses,
# ---- so this anchors surgery strictly to the executable body.
_A_IMPL = "    return phase :: onoff\n"

# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `renderDashPatternTester phase onoff = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("\n"
            "extract_program_for renderDashPattern\n"
            "prove_precondition_decidable_for renderDashPattern\n"
            "prove_postcondition_decidable_for renderDashPattern\n"
            "derive_tester_for renderDashPattern\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the contract is point-wise, so the reproof stays a
    # `loom_solve` away from the frozen script (verified during authoring).
    # =====================================================================
    {
        "id": "pos-control-head-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the phase into a named local `head` and construct the
        # result from it — a different impl shape from gold's inline
        # `phase :: onoff`. Observationally identical for every input.
        "module": _swap(
            _BASE, _A_IMPL,
            "    let head : Int := phase\n"
            "    return head :: onoff\n"),
        "rationale": "binding the phase into a named local and prepending it "
                     "computes `phase :: onoff` unchanged, so every clause "
                     "(`out = phase :: onoff`, head?, tail, length) still holds; "
                     "a correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "construction's shape.",
    },
    {
        "id": "pos-control-append-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the result as a singleton-head list appended to the
        # on/off sequence (`[phase] ++ onoff`) rather than a cons. Same value.
        "module": _swap(
            _BASE, _A_IMPL,
            "    return [phase] ++ onoff\n"),
        "rationale": "`[phase] ++ onoff` is definitionally `phase :: onoff`, so "
                     "the post-image is unchanged and the reshape must verify "
                     "(else SPEC-TOO-STRONG on the head/tail split form).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares no `require`, so the "a normal input
    # satisfies the precondition" probe is trivial and not where the risk sits.
    # The residual admissibility risk on this surface is that the post-image is
    # UNSATISFIABLE or DEGENERATE at the interesting point — a spec no impl can
    # meet reads exactly like one every impl meets. This case discharges an
    # in-region `assert` pinning the post-image's value at the F2P-shaped input
    # (a nonzero phase 6 with on/off sequence [6, 6]): the head is the phase
    # exactly and the length is one longer than the on/off sequence. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim leaves an unsolved goal —
    # verified during authoring by mutating the pinned value and observing the
    # build fail).
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _A_IMPL,
            "    assert (with_name_prefix `assert\n"
            "      ((6 :: [6, 6] : List Int).head? = some 6 ∧\n"
            "       (6 :: [6, 6] : List Int).length = ([6, 6] : List Int).length + 1))\n"
            "    return phase :: onoff\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input: for a nonzero phase 6 with on/off "
                     "sequence [6, 6] it demands the head be exactly 6 and the "
                     "length be one longer than the on/off sequence. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable / PRECOND-TOO-STRONG); the impl is kept "
                     "verbatim so the method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-head-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Seed the head with the literal 0 instead of the stored phase. Agrees
        # with the post-image only when phase = 0.
        "module": _swap(_BASE, _A_IMPL,
                        "    return 0 :: onoff\n"),
        "refinement": "a counterpart that hands the back end a head fixed at zero "
                      "renders every shape with offset 0 regardless of its stored "
                      "offset. For the failing scenario a shape with a nonzero "
                      "offset would render identically to a zero-offset shape "
                      "rather than with the offset's phase shift, so the "
                      "image-equality assertion would see different images and the "
                      "test would NOT resolve — this IS the pre-fix behavior.",
        "rationale": "REJECT from `out.head? = some phase` (and `out = phase :: "
                     "onoff`): with the head fixed at 0 the result is `0 :: onoff` "
                     "where the post-image demands `phase :: onoff`, failing on "
                     "every nonzero phase. Verifying would be SPEC-TOO-WEAK on the "
                     "offset-passthrough behavior. Refuted at a nonzero phase (the "
                     "sub-domain on which a zero-head impl is observably wrong; a "
                     "zero-phase input would not discriminate it).",
        "witness": _tester(
            "example : renderDashPatternTester 6 [6, 6] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-drop-last-onoff",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepend the phase but drop the LAST element of the on/off sequence.
        # Correct on an empty on/off sequence; one element short otherwise.
        "module": _swap(_BASE, _A_IMPL,
                        "    return phase :: onoff.dropLast\n"),
        "refinement": "a counterpart that hands the back end the on/off sequence "
                      "with its last ink length dropped renders every nonempty "
                      "sequence one segment short, producing a visibly different "
                      "dashing from the reference pattern; the image-equality "
                      "assertion fails and the test would NOT resolve. (It agrees "
                      "on the empty/solid case, so it is a true partial-domain "
                      "miss on the nonempty sub-domain.)",
        "rationale": "REJECT from `out.length = onoff.length + 1` and `out.tail = "
                     "onoff`: dropping the last on/off element makes the result "
                     "one element short and its tail a strict prefix of the stored "
                     "sequence on every nonempty input. Verifying would be "
                     "SPEC-TOO-WEAK on the exact-length and passthrough clauses. "
                     "Refuted at a longer on/off sequence distinct from the other "
                     "rivals' inputs.",
        "witness": _tester(
            "example : renderDashPatternTester 2 [7, 8, 9] = false := by\n"
            "  decide\n"),
    },
    {
        "id": "weak-tail-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepend the correct phase but fill the tail with the phase value
        # instead of copying the on/off sequence. Head and length correct;
        # tail masked. On the exact F2P input (phase 6, onoff [6, 6]) the
        # corrupted tail [6, 6] coincides with the real one (6 == the element
        # value), so the F2P test alone is BLIND to this corruption — only the
        # spec's verbatim on/off-passthrough clause catches it, which is exactly
        # the value the uniqueness lane adds over the test.
        "module": _swap(_BASE, _A_IMPL,
                        "    return phase :: (onoff.map (fun _ => phase))\n"),
        "refinement": "a counterpart that fills every ink length with the offset "
                      "value rather than copying the stored on/off sequence hands "
                      "the back end a corrupted dash pattern on any shape whose "
                      "on/off sequence is not a constant run of the offset; the "
                      "equivalence the failing test asserts against the reference "
                      "pattern would break, so the test would NOT resolve.",
        "rationale": "REJECT from `out.tail = onoff` (and `out = phase :: onoff`): "
                     "the head (phase) and length (onoff.length + 1) are both "
                     "correct, so only the on/off-passthrough clause catches the "
                     "masked tail. Verifying would be SPEC-TOO-WEAK on the on/off "
                     "passthrough. Refuted at a short on/off sequence whose "
                     "elements differ from the phase, distinct from the other "
                     "rivals' inputs.",
        "witness": _tester(
            "example : renderDashPatternTester 5 [1, 2] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 3 uniqueness rivals). This bundle
# models the same purely-functional core — a single method `renderDashPattern`
# constructing the render-time dash pattern from the stored phase and on/off
# sequence. The value surface carries across intact; the permission surface does
# not exist here. Every sibling case is accounted for below.
#
#   sibling case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-local-reshape           -> pos-control-head-local          PORTED
#                                          (+ pos-control-append-form ADDED)
#   admissibility-readonly-onoff        -> admiss-postimage-nondegenerate  RE-AIMED
#   frame-mutation-write-onoff          -> (none)                          VACUOUS
#   head-zero-prepatch-offset-dropped   -> weak-head-zero                  PORTED
#   drop-last-onoff-element             -> weak-drop-last-onoff            PORTED
#   tail-constant-onoff-passthrough     -> weak-tail-constant              PORTED
#
# 4 ported, 1 re-aimed, 1 vacuous; 1 positive control added.
#
# VACUOUS (frame-mutation-write-onoff): the sibling's mandatory frame-mutation
#   rival writes back into the read-only on/off input, which carries only a
#   fractional heap permission, and is rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, this bundle declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. No substitute is fabricated (per the
#   porting map, this class is legitimately dropped here rather than replaced).
# RE-AIMED (admissibility): the sibling's case re-derives that the
#   half-permission on/off input is usable and reaches a normal return. There is
#   no permission and no `require` here, so that probe is trivial. It is
#   re-aimed at the residual admissibility risk on this surface — that the
#   post-image is unsatisfiable or degenerate at the interesting point — by
#   discharging an in-region assert pinning the post-image's value at the
#   F2P-shaped input (nonzero phase 6, on/off [6, 6]).
# ADDED (1): pos-control-append-form — a second, structurally-different correct
#   impl (`[phase] ++ onoff` rather than a cons), so the soundness surface is
#   defended by two distinct reshapes.
#
# BINDER / CLAUSE COVERAGE. The four `ensures` clauses are attacked across three
#   distinct sub-domains: the head/offset-passthrough clause (`out.head? = some
#   phase`, the load-bearing behavior) by weak-head-zero; the exact-length
#   clause (`out.length = onoff.length + 1`) and the tail-prefix by
#   weak-drop-last-onoff; and the on/off-passthrough clause (`out.tail = onoff`)
#   with head and length held correct by weak-tail-constant. Refuted at three
#   DISTINCT input points (pts=3). BOTH binders are varied: `phase` over 6, 2, 5
#   (all nonzero — the head-zero rival agrees with gold at phase 0, so its
#   witness must use a nonzero phase), `onoff` over [6, 6], [7, 8, 9], [1, 2]
#   (distinct lengths and contents). No rival is refuted at a binder value
#   another rival holds fixed.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless. This bundle has no axiomatized callee: the render-
#   time dash pattern is a pure construction from the values the shape already
#   holds, modeled deeply (mapping.md §3 records no axiom, no A-reference).
AXIOM_TESTS = []
