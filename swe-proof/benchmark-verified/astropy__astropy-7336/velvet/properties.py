"""properties.py — G-PBT falsification battery for astropy__astropy-7336 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over two binders):

  processReturn (annot : Annot) (ret : RetVal)   ensures out = processReturnSpec annot ret

The post-processing tail routes on the declared result annotation:
  * ``.absent``    (no annotation)          -> the result is handed back UNCHANGED;
  * ``.nullAnnot`` (the null sentinel)      -> the result is handed back UNCHANGED;
  * ``.target u``  (a genuine unit target)  -> the result is re-expressed in ``u``
    via the unchanged re-expression callee ``coerceUnit``.

``processReturnSpec`` is modelled DEEPLY (a concrete ``def`` in the ``pure``
region; the ``axioms`` region is EMPTY), so there is no opaque answer-key an
impl could echo. The single load-bearing clause ``out = processReturnSpec annot
ret`` pins BOTH the routing decision (which annotation shape re-expresses vs
passes through) AND the value produced on each route.

CARRIER NOTE — what is decidable here. ``coerceUnit`` on a ``.quantity`` source
consults ``compatible`` / ``unitKind``, which are OPAQUE (their value-by-value
identity is pinned against the real units only by G-AX). So a concrete point on
the quantity-re-expression success path does NOT reduce under kernel ``decide``.
The points that DO reduce are (a) any annotation shape at ``ret = .null`` — the
re-expression callee is defined by cases and ``coerceUnit .null u`` reduces to
the ``noConvertOp`` failure — and (b) any passthrough route (``.absent`` /
``.nullAnnot``) at any concrete ``ret``, where the spec demands ``Except.ok ret``
verbatim. Every reject witness below lives on one of those decidable points; a
rival whose only divergence would sit inside the opaque re-expression region is
therefore NOT discriminable on this carrier and is reported dropped in the
footer rather than shipped with a witness that never fired.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The nagini sibling writes back into
    a half-permission input to prove the read-only frame holds. Lean and Velvet
    are referentially transparent and this method declares NO ``mut`` binder, so
    there is no read-only input to overwrite and no substitute probe to build.
    Reported N/A in the footer, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. ``processReturnSpec`` is a total, fully unfolded
    function of the method's own arguments; there is no opaque answer-key to
    echo. The positive controls are honest cheapest-reshape variants.
  * ROUTING / VALUE — the main class. Each rival either misroutes one annotation
    shape or fabricates the wrong value on a route, refuted at the smallest
    decidable point that exposes it.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery
(``extract_program_for`` / ``derive_tester_for``): ``processReturnTester annot
ret = false`` says the extracted program's result violates the postcondition at
that concrete input. It is checked in a file whose ``prove_correct`` block has
been stripped, so no tactic script can mask the verdict.
``prove_postcondition_decidable_for`` needs equality of the report carrier
``Except ConvErr RetVal`` to be decidable, so the preamble derives that instance
first — an instance, not an assumption (no ``axiom`` / ``sorry`` /
``native_decide``), and the frozen solution rejects every witness all the same
(on each witness point the frozen impl SATISFIES the postcondition, so its
tester returns ``true`` and ``= false`` fails against gold — the discriminator).

WITNESS PLACEMENT. The two binders are moved across the reject witnesses so the
battery probes four distinct input points rather than pinning either binder:
  annot takes { .nullAnnot, .target, .absent } and ret takes { .null, .quantity }
across the four rivals — {(.nullAnnot,.null), (.target,.null), (.absent,.null),
(.nullAnnot,.quantity)}. A rival that mishandled only a binder every witness
held constant would slip through; moving both binders is what closes that hole.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the re-expression
callee is modelled deeply and validated == the real callee by G-AX /
axiom_check.py). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7336"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen routing block, verbatim (inside -- impl-start / -- impl-end).
# ---- Full-replacement positives swap THIS whole block; the value-line rivals
# ---- swap only the single `let out := ...` line or one match arm. Every anchor
# ---- lies wholly inside the impl region and is unique (asserted at load). ----
_ANNOTATED_BLOCK = (
    "    let annotated : Bool :=\n"
    "      match annot with\n"
    "      | .absent    => false\n"
    "      | .nullAnnot => false\n"
    "      | .target _  => true\n"
    "    let out := if annotated then coerceUnit ret (annotTarget annot) "
    "else Except.ok ret"
)
assert _ANNOTATED_BLOCK in _BASE, "gold routing block drifted from Solution.lean"

_OUT_LINE = (
    "    let out := if annotated then coerceUnit ret (annotTarget annot) "
    "else Except.ok ret"
)
assert _BASE.count(_OUT_LINE) == 1, "out-line anchor not unique"

_NULLANNOT_ARM = "      | .nullAnnot => false\n"
assert _BASE.count(_NULLANNOT_ARM) == 1, "nullAnnot-arm anchor not unique"

_ANNOTATED_HEAD = "    let annotated : Bool :=\n"
assert _BASE.count(_ANNOTATED_HEAD) == 1, "annotated-head anchor not unique"

# ---- the frozen proof block. A tactic body is elided from the consumer spec
# ---- view, so a positive control may retune it without touching the spec or
# ---- dropping the obligation. Unique in the file. ----
_PROVE = "prove_correct processReturn by\n  loom_solve\n"
assert _BASE.count(_PROVE) == 1, "frozen proof block drifted from Solution.lean"


# ---- witness preamble: reach the method contract through Velvet's tester.
# ---- Except-carrier equality is derived as an instance (not assumed). ----
_PREAMBLE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for processReturn\n"
    "prove_precondition_decidable_for processReturn\n"
    "prove_postcondition_decidable_for processReturn\n"
    "derive_tester_for processReturn\n\n"
)


def _wit(example):
    return _PREAMBLE + example


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
# that MUST verify. If a faithful correct impl cannot verify, the spec is
# SPEC-TOO-STRONG. Each keeps the obligation and reshapes only the executable
# surface + its (elided) proof body.
# ===========================================================================

# Direct match on the annotation, no intermediate `annotated` boolean and no
# `annotTarget` indirection: the `.target` arm binds the unit and re-expresses
# in it directly, both other arms pass through. Same routing and same value on
# every shape as gold; the proof folds the reordered match back to the spec.
_POS_DIRECT_BODY = (
    "    let out : Except ConvErr RetVal :=\n"
    "      match annot with\n"
    "      | .target u  => coerceUnit ret u\n"
    "      | .absent    => Except.ok ret\n"
    "      | .nullAnnot => Except.ok ret"
)
# Local reshape: collapse the two pass-through arms into a wildcard and rename
# the classifier local. `isTarget` is true on exactly the `.target` shape, so
# the route choice and each route's value are unchanged; the reshaped classifier
# match is split back open with one `cases annot`.
_POS_LOCAL_BODY = (
    "    let isTarget : Bool :=\n"
    "      match annot with\n"
    "      | .target _  => true\n"
    "      | _          => false\n"
    "    let out := if isTarget then coerceUnit ret (annotTarget annot) "
    "else Except.ok ret"
)
_POS_LOCAL_PROVE = (
    "prove_correct processReturn by\n"
    "  loom_solve\n"
    "  cases annot <;> rfl\n"
)

# ===========================================================================
# ADMISSIBILITY (re-aimed) — this method has NO `require` clause, so the nagini
# "a normal F2P-shaped input satisfies the precondition" probe is VACUOUS:
# nothing could exclude an in-domain input. Re-aimed at the residual risk on a
# total domain — that the post-image is UNSATISFIABLE / DEGENERATE at the
# interesting point (a spec no impl can meet reads exactly like a spec every
# impl meets). The case discharges a live in-region assert that the post-image
# demands the result UNCHANGED on the two pass-through shapes at F2P-shaped
# points (a null result under the null sentinel, a genuine result under no
# annotation). The impl is kept verbatim, so the method's own obligation still
# discharges; the assert is live (a false claim leaves an unsolved goal).
# ===========================================================================
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `assert\n"
    "      (processReturnSpec .nullAnnot .null = Except.ok .null ∧\n"
    "       processReturnSpec .absent (.quantity 3) = Except.ok (.quantity 3)))\n"
    "    let annotated : Bool :=\n"
)
_ADMISS_PROVE = (
    "prove_correct processReturn by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | exact ⟨rfl, rfl⟩\n"
    "    | rfl\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    {
        "id": "pos-direct-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ANNOTATED_BLOCK, _POS_DIRECT_BODY),
        "rationale": "matching the annotation directly (target arm re-expresses, "
                     "both other arms pass through) sends each shape down the SAME "
                     "route with the SAME value as gold, so `out = processReturnSpec "
                     "annot ret` holds on every shape and the frozen proof closes. "
                     "A correct reshape must verify, else SPEC-TOO-STRONG on match "
                     "order.",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _ANNOTATED_BLOCK, _POS_LOCAL_BODY),
                        _PROVE, _POS_LOCAL_PROVE),
        "rationale": "collapsing the two pass-through arms into a wildcard and "
                     "renaming the classifier local leaves the route choice "
                     "(re-express iff `.target`) and each route's value unchanged, "
                     "so `out = processReturnSpec annot ret` still holds; the "
                     "reshaped classifier match is split back open with one "
                     "`cases annot`. A correct reshape must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY (re-aimed)
    # =====================================================================
    {
        "id": "admiss-passthrough-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _ANNOTATED_HEAD, _ADMISS_ASSERT),
                        _PROVE, _ADMISS_PROVE),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "pass-through points: under the null sentinel a null result "
                     "must be handed back as `Except.ok .null`, and under no "
                     "annotation a genuine result must be handed back UNCHANGED "
                     "(`Except.ok (.quantity 3)`) — never re-expressed. The "
                     "in-region assert must discharge (else the obligation is "
                     "unsatisfiable at the interesting point); the impl is kept "
                     "verbatim so `out = processReturnSpec annot ret` discharges "
                     "as well. Re-aimed from the nagini precondition-admits probe "
                     "(vacuous: no `require` clause).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # decidable input and the argument that its faithful real counterpart would
    # NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-always-convert",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch bug: the null-sentinel annotation is treated like a
        # genuine target, so a null-annotated result is fed to the re-expression
        # callee — which is undefined on the null value and fails.
        "module": _swap(_BASE, _NULLANNOT_ARM, "      | .nullAnnot => true\n"),
        "refinement": "this is the pre-patch routing exactly: the guard fires the "
                      "re-expression branch on every non-absent annotation, "
                      "INCLUDING the null sentinel. A callable declared to yield "
                      "no value (a constructor annotated to return the null "
                      "sentinel) then has the re-expression op invoked on its null "
                      "result, which raises — the crash the issue reports. The "
                      "failing test drives exactly that callable and asserts its "
                      "result IS the null value; the pre-patch routing raises "
                      "instead, so a faithful counterpart does NOT resolve.",
        "rationale": "REJECT from `out = processReturnSpec annot ret`: on "
                     "`.nullAnnot` the spec passes the result through "
                     "(`Except.ok ret`), but the rival routes it to the "
                     "re-expression callee; at `ret = .null` that yields the "
                     "`noConvertOp` failure where the spec demands `Except.ok "
                     ".null`. This is the G-DIFF discriminator. Refuted at "
                     "(.nullAnnot, .null), the null-sentinel routing point.",
        "witness": _wit(
            "example : processReturnTester Annot.nullAnnot RetVal.null = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-never-convert",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the re-expression entirely: hands every result back unchanged,
        # even under a genuine unit target.
        "module": _swap(_BASE, _OUT_LINE, "    let out := Except.ok ret"),
        "refinement": "a counterpart that returned the wrapped result unchanged "
                      "for every annotation would never re-express a genuine unit "
                      "target: a function declared to return one unit, handed a "
                      "value in a different unit of the same kind, would keep the "
                      "source unit. The failing/regression tests that pin the "
                      "returned unit to the declared target then observe the wrong "
                      "unit, so a faithful counterpart does NOT resolve.",
        "rationale": "REJECT from `out = processReturnSpec annot ret`: on "
                     "`.target u` the spec demands `coerceUnit ret u`, but the "
                     "rival returns `Except.ok ret`; at `ret = .null` the spec "
                     "yields the `noConvertOp` failure while the rival returns "
                     "`Except.ok .null`. Refuted at (.target, .null), moving the "
                     "annotation binder onto the genuine-target shape.",
        "witness": _wit(
            "example : processReturnTester (Annot.target 5) RetVal.null = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-fabricate-nonnull-on-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # On the pass-through route, fabricate a genuine (non-null) result
        # instead of handing back the actual result. The value-visible analogue
        # of "the result is no longer the null value" — the exact F2P assertion.
        "module": _swap(_BASE, _OUT_LINE,
                        "    let out := if annotated then coerceUnit ret "
                        "(annotTarget annot) else Except.ok (RetVal.quantity 0)"),
        "refinement": "a counterpart that, on the pass-through route, returned a "
                      "fabricated non-null object instead of the wrapped result "
                      "would break a callable declared to yield no value: the "
                      "failing test asserts the result IS the null value, but the "
                      "patched wrapper would yield a fabricated object. So the "
                      "counterpart does NOT resolve the F2P.",
        "rationale": "REJECT from `out = processReturnSpec annot ret`: on the "
                     "pass-through shapes the spec pins `out = Except.ok ret`, but "
                     "the rival returns `Except.ok (.quantity 0)`; at "
                     "(.absent, .null) the spec demands `Except.ok .null` and the "
                     "rival yields a fabricated quantity. Refuted at (.absent, "
                     ".null), moving the annotation binder onto the no-annotation "
                     "shape — the value-abstraction analogue of the F2P "
                     "`result is None`.",
        "witness": _wit(
            "example : processReturnTester Annot.absent RetVal.null = false "
            ":= by\n  decide\n"),
    },
    {
        "id": "weak-drop-value-on-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Dual near-miss: on the pass-through route, drop the actual result to
        # the null value. Correct on a null result, wrong on a genuine one —
        # so its separating input is a QUANTITY, which moves the `ret` binder
        # off the null value every other rival holds it at.
        "module": _swap(_BASE, _OUT_LINE,
                        "    let out := if annotated then coerceUnit ret "
                        "(annotTarget annot) else Except.ok RetVal.null"),
        "refinement": "a counterpart that, on the pass-through route, discarded "
                      "the wrapped result and returned the null value would break "
                      "a callable with no annotation that yields a genuine result: "
                      "the regression tests that observe that result (its unit) "
                      "would instead see the null value, which has no unit. So the "
                      "counterpart does NOT resolve.",
        "rationale": "REJECT from `out = processReturnSpec annot ret`: on the "
                     "pass-through shapes the spec pins `out = Except.ok ret`, but "
                     "the rival returns `Except.ok .null`; at (.nullAnnot, "
                     ".quantity 7) the spec demands `Except.ok (.quantity 7)` and "
                     "the rival drops it to the null value. Refuted at a QUANTITY "
                     "result — the only reject witness that moves the `ret` binder "
                     "off `.null`, so the battery probes the result binder's "
                     "dependence.",
        "witness": _wit(
            "example : processReturnTester Annot.nullAnnot (RetVal.quantity 7) "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals — one of them frame-mutation).
# This bundle models the SAME behaviour (route on the declared result annotation
# and produce the routed outcome) as ONE method with one obligation.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-branch-reorder            -> pos-direct-match
#                                            + pos-local-reshape           PORTED
#   admissibility-readonly-retval         -> admiss-passthrough-nondegenerate
#                                                                          RE-AIMED
#   frame-mutation-write-ret-unit         -> (none)                        VACUOUS
#   always-convert-prepatch-bug           -> weak-always-convert           PORTED
#   always-passthrough-never-convert      -> weak-never-convert            PORTED
#   wrong-unit-on-convert                 -> (none)                        DROPPED
#   control-flow-notnone-on-passthrough   -> weak-fabricate-nonnull-on-passthrough
#                                                                          PORTED
#   (added for `ret`-binder coverage)     -> weak-drop-value-on-passthrough  ADDED
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (branch reorder + local staging). It is carried by TWO honest reshape
#   positives: pos-direct-match (route by a direct annotation match, dropping the
#   intermediate boolean and the target-extractor) and pos-local-reshape
#   (collapse the pass-through arms into a wildcard, rename the classifier). Both
#   are correct on every (annot, ret) and both verify; the structural-difference
#   intent is preserved.
# PORTED (rivals): always-convert IS the pre-patch bug (route the null-sentinel
#   annotation to the re-expression callee) and the G-DIFF discriminator;
#   never-convert drops the re-expression on a genuine target;
#   fabricate-nonnull-on-passthrough is the value-abstraction analogue of the
#   nagini control-flow rival (the result is no longer the null value — the F2P
#   assertion). Each is refuted at the smallest DECIDABLE point exposing it.
# ADDED (1): weak-drop-value-on-passthrough. The dual of the fabricate rival;
#   its separating input is a QUANTITY result, so it is the one reject witness
#   that moves the `ret` binder off `.null`. Without it every reject witness
#   would hold `ret = .null`, and a rival mishandling only a genuine result
#   would slip through.
# DROPPED (wrong-unit-on-convert): the sibling's rival keeps the routing correct
#   but returns the SOURCE unit instead of the target on the re-expression
#   branch. On this carrier the unit-stamp lives ENTIRELY inside the OPAQUE
#   re-expression region (`coerceUnit` on a `.quantity` source consults the
#   opaque `compatible`/`unitKind`), which does NOT reduce under kernel `decide`
#   — so no discriminating witness exists for it distinct from never-convert
#   (both collapse to "hand the result back" on the only decidable points). The
#   distinction the sibling draws is not observable on this abstraction, so the
#   rival is dropped rather than shipped with a witness that never fires. The
#   target-branch value clause is instead attacked by weak-never-convert at
#   (.target, .null).
# VACUOUS (frame-mutation): the sibling writes back to the half-permission input
#   to prove the read-only frame holds. This backend is referentially
#   transparent and the method declares NO `mut` binder, so there is no read-only
#   input to overwrite and no substitute probe to build. Not fabricated.
#
# WITNESS DISTINCTNESS. Four distinct input points:
#   (.nullAnnot, .null)      weak-always-convert          (null-sentinel misroute)
#   (.target,    .null)      weak-never-convert           (genuine-target no-op)
#   (.absent,    .null)      weak-fabricate-nonnull        (passthrough fabricates)
#   (.nullAnnot, .quantity)  weak-drop-value               (passthrough drops value)
# annot ranges over { .nullAnnot, .target, .absent }; ret over { .null, .quantity }.
# The two `.nullAnnot` witnesses fail for DIFFERENT reasons against DIFFERENT
# sub-behaviours (misroute-to-convert vs drop-the-value on passthrough) and at
# DIFFERENT `ret`, so they are distinct predicates, not one attack written twice.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the re-expression callee is
# modelled deeply (no `axiom` in this bundle) and validated == the real callee by
# axiom_check.py.
AXIOM_TESTS = []
