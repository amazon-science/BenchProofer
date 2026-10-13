"""properties.py — G-PBT falsification battery for django__django-12276 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct useRequiredAttribute`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies).
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a Bool carrier). A rendered control
decides whether to advertise a required-style marker, given whether the form
already carries an existing value for the field:

  useRequiredAttribute (hasInitial : Bool) return (out : Bool)
      ensures out = (inheritedRequiredDecision hasInitial && !hasInitial)

``inheritedRequiredDecision : Bool → Bool`` is an ``opaque`` free function with
NO constraining ``axiom`` — nothing is claimed about which value the inherited
base decision produces, only that it is a deterministic function of ``hasInitial``
(mapping.md §3: it is an UNCHANGED inherited routine the operation refines but
never replaces, so the weakest sufficient contract asserts nothing about its
return; directives 7/8). The method has NO ``require`` clause; the input domain
is total. ONE input binder, ``hasInitial``.

CARRIER NOTE — TRANSPARENT vs OPAQUE sub-domains. The post-image is the
conjunction of an OPAQUE conjunct (``inheritedRequiredDecision hasInitial``) and
a TRANSPARENT one (``!hasInitial``). That split governs the whole battery:

  * at ``hasInitial = true``  the post-image is ``X && false = false`` — fully
    transparent; the opaque conjunct is irrelevant, and a rival that returns
    anything other than ``false`` here is refutable WITHOUT knowing ``X``;
  * at ``hasInitial = false`` the post-image is ``X && true = X =
    inheritedRequiredDecision false`` — the opaque conjunct alone; a rival that
    returns a value ≠ that opaque atom is refutable only by CONDITIONING on the
    carrier (state the refutation at a point described by a satisfiable
    hypothesis about the opaque term — the technique that makes the opaque
    sub-domain attackable at all; see the reject cases).

So the reject lane is NON-EMPTY and attacks BOTH sub-domains: the transparent
suppression at ``hasInitial = true`` (decidably, and by conditioning for the
pre-patch bug) and the opaque decision at ``hasInitial = false`` (by
conditioning). The witnesses drive ``hasInitial`` to BOTH values (pts = 2), so
the sole binder is varied rather than pinned.

REFINEMENT GROUND-TRUTH (what makes a reject a TRUE verify-does-not-imply-resolve
break, not a resolve-preserving artifact). The failing tests exercise ONLY a
visible (non-hidden) file control, for which the inherited base decision is
ALWAYS the "permit" value regardless of the existing-value flag; so the
harness-observable behaviour on the F2P domain collapses to ``!hasInitial``. A
rival is a genuine break iff its faithful real patch would still get
``!hasInitial`` WRONG on that domain:

  * a rival that MISHANDLES the suppression (returns the wrong thing when an
    existing value IS present, or a constant that breaks the no-value case) fails
    the F2P tests → a real break → MUST reject;
  * a rival that gets ``!hasInitial`` right on the visible-control domain but
    mishandles ONLY the (never-reached) hidden sub-domain still RESOLVES the F2P
    → resolve-preserving artifact → DROPPED (rejecting it would be a break in the
    wrong direction; see the DROPPED footer for the XOR and drop-inherited
    rivals, which agree with gold on the entire F2P domain).

ADVERSARIAL READ of the sibling (nagini) classes on this carrier:

  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (decide the existing-value case first; or read
    both conjuncts into typed locals and combine them in the opposite operand
    order) must still verify against the byte-identical obligation, else the spec
    is SPEC-TOO-STRONG on the shape of the impl. Both reshapes are PROPOSITIONALLY
    equal to the frozen return but NOT definitionally so, and the frozen
    ``loom_solve`` script still closes the obligation (both verified out-of-band
    with real builds). The distinction matters and is measured, not assumed: an
    earlier revision of this file called both reshapes "definitionally the frozen
    return", and a standalone ``rfl`` on each equation FAILS (``Tactic `rfl`
    failed: … !b && inheritedRequiredDecision b … is not definitionally equal to
    … inheritedRequiredDecision b && !b``, and likewise for the branch form).
    Each needs CASE ANALYSIS on the sole binder (``cases b <;> simp``, EXIT 0).
    So these positives are not restatements the elaborator absorbs for free — the
    obligation is genuinely re-discharged at a shape the frozen script was not
    written for, which is exactly what a soundness control has to do to be worth
    a build.

  * ADMISSIBILITY — APPLIES, and is LANDED (``admiss-f2p-nondegenerate``). The
    method has NO ``require`` clause, so the sibling's "a freshly built
    F2P-shaped control satisfies the half-permission precondition, and the
    self-call goes through" probe has nothing to admit. That is NOT a reason to
    drop the lane: the analogue on a total carrier is the obligation being
    UNSATISFIABLE or DEGENERATE at exactly an F2P-shaped input, which a positive
    that discharges the obligation AT those concrete inputs — by evaluation, as
    an in-region ``assert``, before closing the frozen obligation verbatim —
    tests directly. An earlier revision of this file called the lane vacuous on
    the ground that an assert "could only pin the trivial transparent half or an
    un-decidable statement about the opaque atom". That was wrong on the second
    half: the opaque conjunct is attackable the same way the reject lane attacks
    it — by CONDITIONING (``inheritedRequiredDecision false = true →  …``), which
    needs no tactic to decide the opaque term. So both F2P-shaped points are
    assertable, and so is their NON-COLLAPSE. See the case.

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    this class MANDATORY (its sharpest rival overwrites the read-only control
    field held at a fractional heap permission to make the post-image trivially
    hold). This backend is referentially transparent: there is no heap, no
    aliasing, and this bundle declares NO ``mut`` binder — ``hasInitial`` is an
    immutable value with no heap footprint. There is no read-only field to
    overwrite and no substitute probe to build. Not fabricated (porting map: this
    class is vacuous on a referentially-transparent backend).

  * DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A. The opaque ``inheritedRequiredDecision`` is a
    fixed function OF the method input (directive 8), not a free answer-key in a
    separate ``axiom`` region a wrong impl could echo; and it is CONJOINED with a
    transparent term, so the only impl satisfying the clause IS the grounded
    computation.

  * UNIQUENESS / SPEC-TOO-WEAK rivals — EXPRESSIBLE (this is the load-bearing
    finding of the port). See the three reject cases: the pre-patch bug (drop the
    suppression conjunct) and two constant rivals, each refuted at a concrete
    input, together attacking both sub-domains and varying the sole binder.

AXIOM lane: the sibling's ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's
job, and here there is no ``axiom`` at all (the inherited decision is an
``opaque`` free function with nothing asserted to validate; mapping.md §3 records
the G-AX skip). This gate ignores ``AXIOM_TESTS`` regardless. See the footer.
"""
from pathlib import Path

INSTANCE = "django__django-12276"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen return, verbatim (the single code line
# ---- strictly inside useRequiredAttribute's -- impl-start / -- impl-end). It
# ---- lies wholly inside the elided impl region and is unique in Solution.lean
# ---- (both facts asserted at load by _swap), so every variant's edit never
# ---- touches the spec regions (axioms/pure/pre/post + the method signature and
# ---- the `ensures`).
_IMPL = "    return (inheritedRequiredDecision hasInitial && !hasInitial)"
assert _BASE.count(_IMPL) == 1, "useRequiredAttribute impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY useRequiredAttribute's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble. The frozen `prove_correct` block is stripped by the gate
# ---- before the witness is appended, so the witness states the refutation
# ---- directly against the extracted `VelvetM Bool` program: `(useRequiredAttribute
# ---- b).run` is `DivM.res (<impl result at b>)`, and the witness asserts it
# ---- differs from `DivM.res (<the post-image at b>)`. Elaborates against a rival
# ---- whose impl-result diverges from the post-image at `b`, and FAILS on gold
# ---- (whose impl-result IS the post-image). No `sorry`/`admit`/`native_decide`.


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps the `ensures` clause
    # and the frozen `prove_correct useRequiredAttribute by loom_solve` script;
    # the reshape is PROPOSITIONALLY equal to the frozen return (NOT definitionally
    # — `rfl` fails on both equations, measured out-of-band; each needs case
    # analysis on the sole binder), so the script closes the byte-identical
    # obligation only by doing real work (both verified with real builds).
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: decide the existing-value case FIRST (present -> suppress the
        # marker), else fall through to the inherited base decision. Semantically
        # identical to the gold conjunction — the two branches ARE the two
        # sub-domains of `X && !hasInitial` — but a different control-flow shape.
        # (Sibling: pos-control-reorder.)
        "module": _impl(
            "    if hasInitial then\n"
            "      return false\n"
            "    else\n"
            "      return inheritedRequiredDecision hasInitial"),
        "rationale": "structurally different CORRECT impl (decide on the "
                     "existing-value flag first, else defer to the inherited base "
                     "decision). Each branch computes the post-image on its "
                     "sub-domain (`hasInitial` true -> `X && !true = false`; false "
                     "-> `X && !false = X`), so `out = inheritedRequiredDecision "
                     "hasInitial && !hasInitial` still discharges under the frozen "
                     "`loom_solve`. If it FAILS => SPEC-TOO-STRONG (a faithful "
                     "correct impl of a different shape rejected).",
    },
    {
        "id": "pos-locals-commuted",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: read both conjuncts into typed locals and combine them in the
        # OPPOSITE operand order. Boolean `&&` is commutative on total bools, so
        # this equals the gold result; a second independent positive witness of a
        # different shape (let-binding + commuted conjunction).
        # (Sibling: pos-control-locals.)
        "module": _impl(
            "    let g : Bool := inheritedRequiredDecision hasInitial\n"
            "    let absent : Bool := !hasInitial\n"
            "    return (absent && g)"),
        "rationale": "structurally different CORRECT impl: bind the inherited "
                     "decision and the absence flag to typed locals and combine "
                     "them in the opposite operand order. `&&` is commutative on "
                     "total bools, so this is PROPOSITIONALLY equal to the frozen "
                     "return — but NOT definitionally: a standalone `rfl` on "
                     "`(!b && X b) = (X b && !b)` FAILS (`is not definitionally "
                     "equal to`, measured), and closing it needs `cases b <;> simp`. "
                     "So `out = inheritedRequiredDecision hasInitial && !hasInitial` "
                     "still discharges under the frozen `loom_solve`, but only via "
                     "real case analysis on the sole binder. Exercises a "
                     "second reshape (let-binding + commuted conjunction). If it "
                     "FAILS => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). No method here carries a `require`
    # clause, so "a normal input satisfies the precondition" is vacuously true and
    # is NOT what this case tests. The total-carrier analogue is that the
    # obligation is UNSATISFIABLE or DEGENERATE at an F2P-shaped input — a spec no
    # impl can meet, or one that collapses the two interesting inputs to a single
    # answer, reads exactly like a spec every impl meets. This case discharges the
    # post-image AT both F2P-shaped points as an in-region `assert`, keeping the
    # frozen return and the frozen `loom_solve` so the method's own obligation
    # still closes and the assert is LIVE.
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # Both F2P-shaped inputs, and their non-collapse:
        #   * existing value present  -> the post-image evaluates to `false`
        #     outright (transparent; needs no knowledge of the opaque atom);
        #   * no existing value, inherited decision permits (the visible-control
        #     case the failing tests use) -> the post-image is `true`, stated by
        #     CONDITIONING on the opaque atom so no tactic has to decide it;
        #   * and on that same sub-domain the two points DISAGREE, so the
        #     obligation does not degenerate to one constant answer.
        "module": _impl(
            "    assert (with_name_prefix `adm\n"
            "      ((inheritedRequiredDecision true && !true) = false ∧\n"
            "       (inheritedRequiredDecision false = true →\n"
            "         ((inheritedRequiredDecision false && !false) = true ∧\n"
            "          (inheritedRequiredDecision false && !false) ≠\n"
            "            (inheritedRequiredDecision true && !true)))))\n"
            + _IMPL),
        "rationale": "the post-image is SATISFIABLE and NON-DEGENERATE at exactly "
                     "the F2P-shaped inputs. With an existing value present it "
                     "evaluates to `false` unconditionally (the transparent half); "
                     "with no existing value and the inherited decision permitting "
                     "— the visible-control case the failing tests exercise — it is "
                     "`true`, and those two answers DIFFER, so the obligation does "
                     "not collapse the two inputs to one constant. The opaque "
                     "conjunct is reached by CONDITIONING rather than by deciding "
                     "it, the same technique the reject witnesses use. The assert "
                     "is live: replacing either clause with a false one "
                     "(`… && !true) = true`, or the disequality flipped to an "
                     "equality) leaves `unsolved goals` naming the assert, "
                     "measured out-of-band. The impl and proof script are the "
                     "frozen ones, so C1 still discharges. If the assert FAILS => "
                     "PRECOND-TOO-STRONG (a degenerate / unsatisfiable obligation "
                     "at an input the harness actually drives). "
                     "(Sibling: admiss-novalue, re-aimed at the total-domain "
                     "analogue.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. The three rivals attack
    # BOTH sub-domains and drive the sole binder `hasInitial` to BOTH values
    # (pts = 2): the transparent suppression at `hasInitial = true` (weak-drop-
    # suppression, weak-const-true) and the opaque decision at `hasInitial =
    # false` (weak-const-false).
    # =====================================================================
    {
        "id": "weak-drop-suppression",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH bug verbatim: drop the `&& !hasInitial` suppression and
        # return only the inherited base decision. Correct on the entire
        # `hasInitial = false` sub-domain (where the post-image IS the inherited
        # decision), but WRONG whenever an existing value is present: returns the
        # inherited "permit" value where the spec pins `false`. (Sibling:
        # partial-drop-value.)
        "module": _impl("    return inheritedRequiredDecision hasInitial"),
        "refinement": "this is exactly the pre-patch state (the operation defers "
                      "ONLY to the inherited base decision, with no suppression "
                      "when an existing value is present). Its faithful real patch "
                      "is the empty change — precisely the state the failing tests "
                      "fail on: with an existing value present on a visible control "
                      "the inherited decision permits the marker, but the tests "
                      "require the marker be SUPPRESSED (advertise nothing when a "
                      "value is already carried). It would NOT resolve — a "
                      "verifying rival is a genuine verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from `out = inheritedRequiredDecision hasInitial && "
                     "!hasInitial`: at `hasInitial = true` the post-image is `X && "
                     "false = false`, but the rival returns `X`. This is the "
                     "TRANSPARENT sub-domain, yet the rival's answer is the opaque "
                     "`X`, so the refutation is stated at `hasInitial = true` under "
                     "the satisfiable single hypothesis `inheritedRequiredDecision "
                     "true ≠ false` (the inherited decision permits — its normal "
                     "value on a visible control): the rival's `X` then differs "
                     "from the required `false`, while gold returns `false` and "
                     "cannot meet the disequality. If it VERIFIES => SPEC-TOO-WEAK "
                     "(the suppression conjunct unpinned).",
        "witness":
            "example (h : inheritedRequiredDecision true ≠ false) :\n"
            "    (useRequiredAttribute true).run\n"
            "      ≠ DivM.res (inheritedRequiredDecision true && !true) := by\n"
            "  simp only [useRequiredAttribute]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  simp at h1\n"
            "  exact h h1\n",
    },
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant `false`: never advertise the marker. Correct on the entire
        # `hasInitial = true` sub-domain (where the post-image is `false` too), but
        # WRONG at `hasInitial = false` whenever the inherited decision permits:
        # the spec pins the inherited value, the rival returns `false`. (Sibling:
        # supporting-const-false.)
        "module": _impl("    return false"),
        "refinement": "a faithful real patch that never advertises the marker "
                      "makes EVERY such control non-required, so the no-existing-"
                      "value case on a visible control (which must advertise the "
                      "marker) stays RED: the failing tests require the marker "
                      "PRESENT when no value is carried. It would NOT resolve — a "
                      "verifying constant rival is a genuine "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from `out = inheritedRequiredDecision hasInitial && "
                     "!hasInitial`: at `hasInitial = false` the post-image is `X && "
                     "true = X = inheritedRequiredDecision false`, but the rival "
                     "returns `false`. This is the OPAQUE sub-domain, so the "
                     "refutation is conditioned on the satisfiable single "
                     "hypothesis `inheritedRequiredDecision false ≠ false` (the "
                     "inherited decision permits — its normal value on a visible "
                     "control): the rival's `false` then differs from the required "
                     "`X`, while gold returns `X` and cannot meet the disequality. "
                     "Refuted at `hasInitial = false` — a DISTINCT input from the "
                     "other rivals (which are witnessed at `true`) — so the sole "
                     "binder is varied. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness":
            "example (h : inheritedRequiredDecision false ≠ false) :\n"
            "    (useRequiredAttribute false).run\n"
            "      ≠ DivM.res (inheritedRequiredDecision false && !false) := by\n"
            "  simp only [useRequiredAttribute]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  simp at h1\n"
            "  exact h h1\n",
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant `true`: always advertise the marker. WRONG at `hasInitial =
        # true` where the post-image is transparently `false` — refutable with NO
        # conditioning (a decidable clash on the transparent sub-domain), a
        # different failure shape from weak-drop-suppression (which returns the
        # opaque `X` at the same input). Supporting near-miss.
        "module": _impl("    return true"),
        "refinement": "a faithful real patch that always advertises the marker "
                      "leaves it PRESENT even when an existing value is carried on "
                      "a visible control, exactly the behaviour the failing tests "
                      "forbid (the marker must be suppressed once a value is "
                      "present). It would NOT resolve.",
        "rationale": "REJECT from `out = inheritedRequiredDecision hasInitial && "
                     "!hasInitial`: at `hasInitial = true` the post-image is "
                     "transparently `false`, but the rival returns `true`. This is "
                     "the TRANSPARENT sub-domain, so the refutation needs NO "
                     "conditioning — `(useRequiredAttribute true).run` computes to "
                     "`DivM.res true` while the post-image reduces to `DivM.res "
                     "false`, a decidable clash. Distinct from weak-drop-"
                     "suppression, which returns the OPAQUE `X` at the same input "
                     "(the two fail for different reasons at `hasInitial = true`). "
                     "If it VERIFIES => SPEC-TOO-WEAK.",
        "witness":
            "example :\n"
            "    (useRequiredAttribute true).run\n"
            "      ≠ DivM.res (inheritedRequiredDecision true && !true) := by\n"
            "  simp only [useRequiredAttribute, Bool.not_true, Bool.and_false,\n"
            "             NonDetT.run, pure]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  exact Bool.noConfusion h1\n",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 4
# uniqueness/partial-domain rivals) plus 2 AXIOM_TESTS. Every one is accounted
# for. The sibling contracts `requires_value(control, value_present)` over a
# heap `control` held at a fractional read-only permission, with a
# @Pure/@ContractOnly oracle `generic_requires_value(control.hidden)`. This
# bundle contracts ONE method `useRequiredAttribute (hasInitial : Bool)`, pinning
# `out = inheritedRequiredDecision hasInitial && !hasInitial` for an OPAQUE free
# function with no axiom, no precondition, and no termination clause. The two
# surfaces model the SAME behaviour (advertise the marker only when the inherited
# base decision permits AND no existing value is carried); the sibling's
# `control.hidden` facet is refined away — the inherited decision is deferred to
# opaquely as a function of the SINGLE modeled input `hasInitial` (mapping.md
# §2-3), because the fix uses the control only through that decision and the
# existing-value flag.
#
#   sibling case              kind            -> here
#   -------------------------------------------------------------------------
#   pos-control-reorder       soundness       -> pos-branch-reorder        PORTED
#   pos-control-locals        soundness       -> pos-locals-commuted        PORTED
#   admiss-novalue            admissibility   -> admiss-f2p-nondegenerate    PORTED
#   frame-mut-write-hidden    uniqueness      -> (none)                     VACUOUS
#   partial-drop-value        uniqueness      -> weak-drop-suppression      PORTED
#   supporting-const-false    uniqueness      -> weak-const-false           PORTED
#   partial-drop-generic      uniqueness      -> (none)                     DROPPED (resolve-preserving)
#   partial-xor               uniqueness      -> (none)                     DROPPED (resolve-preserving)
#   (added, transparent clash)uniqueness      -> weak-const-true            ADDED
#   ax-sound-generic_...      axiom           -> (none)                     G-AX / no axiom
#   ax-cover-generic_...      axiom           -> (none)                     G-AX / no axiom
#
# 5 ported (2 soundness, 1 admissibility, 2 uniqueness) + 1 added uniqueness =
# 6 velvet cases.
#
# PORTED — soundness (2): pos-control-reorder -> pos-branch-reorder (decide the
#   existing-value case first, else defer to the inherited decision — the two
#   branches ARE the two sub-domains of `X && !hasInitial`). pos-control-locals ->
#   pos-locals-commuted (bind both conjuncts to typed locals, combine in the
#   opposite operand order — `&&` commutes on total bools). Both build against the
#   frozen `loom_solve` (real builds, EXIT 0).
# PORTED — uniqueness (2): partial-drop-value -> weak-drop-suppression (the
#   pre-patch bug: drop the `&& !hasInitial` suppression, return the inherited
#   decision). Refuted at `hasInitial = true` by conditioning on
#   `inheritedRequiredDecision true ≠ false` (its normal permit value on a visible
#   control) — its answer is the OPAQUE atom, so conditioning is required.
#   supporting-const-false -> weak-const-false (return `false`). Refuted at
#   `hasInitial = false` by conditioning on `inheritedRequiredDecision false ≠
#   false` — the OPAQUE sub-domain. Both witnesses verified out-of-band: each
#   ELABORATES against its rival (EXIT 0) and FAILS on gold (EXIT 1); each single
#   hypothesis is satisfiable (the consistency probe cannot derive `False` from a
#   lone assumption about one opaque term).
# ADDED — uniqueness (1): weak-const-true (return `true`). Attacks the same
#   TRANSPARENT sub-domain as weak-drop-suppression (`hasInitial = true`, where the
#   post-image is `false`) but with a DECIDABLE clash needing NO conditioning, and
#   for a different reason (a constant `true` vs the opaque `X`). It is the
#   sibling's partial-xor's honest, refutable analogue on the F2P-relevant
#   sub-domain: a rival that leaves the marker present when a value is carried.
#   Verified out-of-band (rival EXIT 0, gold EXIT 1).
# PORTED — admissibility (1): admiss-novalue relied on the sibling's fractional
#   read-only precondition `Acc(control.hidden, 1/2)` admitting a freshly built
#   F2P-shaped control and the self-call going through. No method here has a
#   `require` clause (pre-conditions region empty), so the precondition half is
#   vacuous — but the LANE is not, and an earlier revision of this file wrongly
#   dropped it on that ground. Re-aimed at the total-carrier analogue
#   (admiss-f2p-nondegenerate): the obligation must be SATISFIABLE and
#   NON-DEGENERATE at the F2P-shaped inputs, discharged as an in-region assert at
#   both points — the existing-value point by evaluation, the no-value point by
#   CONDITIONING on the opaque atom (so nothing has to decide an opaque term, the
#   same technique the reject witnesses use) — plus their non-collapse. Verified
#   out-of-band (EXIT 0) with both clauses shown LIVE: a false variant of either
#   leaves `unsolved goals` naming the assert (EXIT 1).
# VACUOUS — frame/permission-mutation (1): frame-mut-write-hidden writes to the
#   read-only `control.hidden` held at a fractional permission to make the
#   post-image trivially hold, rejected by Nagini for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent, has no heap and no aliasing, and this
#   bundle declares NO `mut` binder — no read-only field to overwrite and no
#   substitute probe. The `control.hidden` facet is not even modeled here (the
#   inherited decision is opaque in `hasInitial`, mapping.md §2). No substitute
#   fabricated (porting map: vacuous on a referentially-transparent backend).
# DROPPED — uniqueness (2), recorded not silently omitted. Both agree with gold on
#   the ENTIRE F2P domain (a visible control, for which the inherited base decision
#   always permits), so their faithful real patches STILL RESOLVE — rejecting them
#   would be a verify-does-not-imply-resolve break in the WRONG direction:
#     * partial-drop-generic (`return !hasInitial`): equals the post-image whenever
#       the inherited decision permits (`X && !hasInitial = !hasInitial` when
#       X = true). It diverges from gold ONLY on the hidden sub-domain
#       (inherited decision = "deny"), which the F2P tests never exercise (they use
#       a visible file control). It COULD be refuted by conditioning at
#       (hasInitial = false, inheritedRequiredDecision false = false): there gold
#       returns `false` while the rival returns `!false = true`. BUT its faithful
#       real patch (drop the inherited conjunct, suppress only on the existing-value
#       flag) still RESOLVES the F2P, because the inherited base decision is
#       constantly "permit" on the visible control the tests use, so the observable
#       behaviour (`!hasInitial`) is unchanged. A
#       refutable-but-resolve-preserving rival is an artifact of the carrier
#       discretising a distinction the real behaviour is invariant under, NOT
#       evidence of SPEC-TOO-WEAK. DROPPED.
#     * partial-xor (`return X != hasInitial`): agrees with the gold conjunction on
#       three of the four (X, hasInitial) corners and diverges only at
#       (X = false, hasInitial = true) — the hidden-with-value corner, again never
#       reached by the F2P tests (visible control => X = permit). Its real patch
#       preserves the observable `!hasInitial` behaviour on the F2P domain and
#       still resolves. DROPPED for the same resolve-preserving reason. (The honest,
#       F2P-relevant slice of "leave the marker present when a value is carried" is
#       instead attacked by weak-const-true, whose real patch genuinely fails.)
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job, and this bundle declares
#   NO axiom — the inherited decision is an `opaque` free function with nothing
#   asserted about its value to validate (mapping.md §3 records the G-AX skip).
#   This gate ignores AXIOM_TESTS regardless.
#
# COVERAGE. The single post-image clause `out = inheritedRequiredDecision
# hasInitial && !hasInitial` is DEFENDED (both soundness positives bear on it) and
# ATTACKED on BOTH sub-domains: the TRANSPARENT suppression at `hasInitial = true`
# (weak-drop-suppression via conditioning, weak-const-true decidably) and the
# OPAQUE inherited decision at `hasInitial = false` (weak-const-false via
# conditioning). The sole input binder `hasInitial` is VARIED by the reject
# witnesses (true for weak-drop-suppression / weak-const-true; false for
# weak-const-false; pts = 2), so the battery demonstrates the spec's dependence on
# the input at both values rather than pinning it. The reject lane is NON-EMPTY,
# so SPEC-TOO-WEAK is detectable; the soundness lane makes SPEC-TOO-STRONG
# detectable; and admiss-f2p-nondegenerate makes PRECOND-TOO-STRONG detectable in
# its total-carrier form (obligation degenerate/unsatisfiable at an F2P-shaped
# input), so all THREE directions this gate exists to test are covered.
#
# AUDIT ADDENDUM (independent re-derivation, real builds, all out-of-band in
# /tmp). Attack D — 6 NEW wrong impls beyond the shipped rivals: pinning the
# opaque argument to `true`, an extra conjunct, branch-swap on the opaque
# decision, `inheritedRequiredDecision (!hasInitial)`, and a both-branches-defer
# rival ALL rejected (EXIT 1) => no spec hole found. One candidate,
# `return (inheritedRequiredDecision false && !hasInitial)`, VERIFIED (EXIT 0) —
# investigated and it is NOT a hole but a CORRECT reshape: `(inheritedRequired
# Decision false && !b) = (inheritedRequiredDecision b && !b)` for every `b`
# (proved standalone, EXIT 0), since at `b = true` both sides are `false` and at
# `b = false` the arguments coincide. The carrier genuinely cannot distinguish
# them, so it belongs in the soundness lane, not the reject lane. Attack E — 5 NEW
# correct reshapes (if-on-the-opaque-decision, `Bool.and` prefix form, `decide` of
# the Prop conjunction, branch-with-literals, `cond`) ALL verified (EXIT 0) => the
# spec is not too strong on impl shape.
#
# SECOND AUDIT ADDENDUM (independent re-derivation by a later auditor; 44 real
# builds, all scratch out-of-band in /tmp; nothing below is inherited from the
# addendum above, every exit code was observed fresh).
#
# ATTACK A — statement integrity. Byte-diffed all 6 variants against the frozen
#   Solution.lean. Every delta lies strictly inside the `-- impl-start` /
#   `-- impl-end` region (line 49, plus the admissibility case's inserted assert
#   at 49-54). Signature, `ensures`, and the `prove_correct useRequiredAttribute
#   by loom_solve` script are byte-identical in all 6; variant_problems=[] for
#   all 6, and impl_region_only=True for the three rivals.
#
# ATTACK B — all 3 witnesses rebuilt with the gate's OWN witness_file /
#   consistency_probe machinery: rival EXIT 0, gold EXIT 1 for all three; the two
#   conditioned witnesses' probes EXIT 1, each leaving `h : inheritedRequired
#   Decision <b> = true ⊢ False` unsolved, i.e. the lone hypothesis is satisfiable
#   and no witness proves its refutation from a contradiction. weak-const-true
#   binds nothing, so consistency_probe() correctly returns None.
#
# ATTACK B′ — the FORGERY pair, run two independent ways because all three
#   gold_signatures are type/application mismatches rather than plain evaluations.
#     (a) TYPE-REVEAL (`exact (h1 : Nat)`, so Lean prints h1's real type). The
#         errors DIFFER across sides, which is the evidence:
#           weak-drop-suppression  gold `h1 has type True`  | rival `h1 has type
#                                  inheritedRequiredDecision true = false`
#           weak-const-false       gold `True`              | rival `inheritedRequired
#                                  Decision false = false`
#           weak-const-true        gold `h1 has type false = false` (a TRUE
#                                  equation) | rival `true = false` (a FALSE one)
#         `has type True` means `simp` PROVED the equation for gold; a concrete
#         open equation means it did not.
#     (b) MIRROR (stronger than a bare claim-flip, and the reason it was run: the
#         flip-claim pair with only `simp only [useRequiredAttribute]` leaves BOTH
#         sides at EXIT 1, so its exit codes alone carry nothing — only its goals
#         differ, `pure false` vs `pure (inheritedRequiredDecision true)` etc.).
#         The mirror asserts the OPPOSITE of each witness — that the impl IS
#         correct at the witness's own input — with a body strong enough to close
#         it (`simp only [useRequiredAttribute]; first | rfl | (simp; rfl) | …`).
#         Result: gold EXIT 0 and rival EXIT 1 for all three, EXACTLY INVERTING
#         the witness pattern. So each gold-side exit code tracks the CLAIM and
#         not the tactic: flipping the claim flips the verdict on both subjects.
#         No case is hollow.
#
# ATTACK C — observable wrongness on THIS carrier, read off each rival's own
#   `prove_correct` failure goal (not argued): weak-drop-suppression leaves
#   `⊢ inheritedRequiredDecision hasInitial = (inheritedRequiredDecision hasInitial
#   && !hasInitial)`, weak-const-false `⊢ false = (…)`, weak-const-true
#   `⊢ true = (…)`. None is definitionally equal to gold, so no rival is a mere
#   reshape and none is vacuous.
#
# ATTACK D — 10 further NEW wrong impls, none of them in the battery or in the
#   addendum above: `&& hasInitial` (suppression inverted), `return hasInitial`,
#   `|| hasInitial`, full negation, XOR, `!hasInitial`, branch-arms swapped,
#   `if hasInitial then false else true`, `!(inheritedRequiredDecision hasInitial)
#   && !hasInitial`, and `inheritedRequiredDecision (!hasInitial) && !hasInitial`
#   — ALL rejected (EXIT 1), each with an `unsolved goals` naming `ensures_1`.
#   => no spec hole. Two further candidates aimed at the opaque ARGUMENT position
#   VERIFIED — `inheritedRequiredDecision (hasInitial && hasInitial)` and
#   `inheritedRequiredDecision (hasInitial || false)` — and both are reshapes, not
#   holes, for the reason the addendum above gives for its own verifying
#   candidate: the argument is propositionally equal to `hasInitial` for every
#   `b`, proved standalone (EXIT 0). Filed here rather than as spec holes.
#
# ATTACK E — 8 further NEW correct reshapes: `match` on the binder, De Morgan
#   double-negation, an idempotent extra conjunct, `decide (hasInitial = false)`
#   as the second conjunct, `Bool.and` prefix form, a trailing `&& true`, and
#   let-then-plain-`if` — ALL verified (EXIT 0) => the spec is not too strong.
#   ONE reshape failed and it is a FRONT-END limit, not a spec hole: a DEPENDENT
#   `if h : hasInitial then …` yields `Failed to parse an assertion without
#   names: WPGen (if h : hasInitial = true then …)`. Demonstrated to be about the
#   dependent binder and not the returned value, by building the same dependent
#   `if` with the FROZEN return verbatim in BOTH arms — it fails identically
#   (EXIT 1, byte-same message shape). So the spec rejects nothing here; the
#   velvet assertion front-end cannot express a dependent `if` in an impl region
#   at all. Recorded as a TOOLING observation for the backend, not a spec finding.
#
# ATTACK F — the admissibility case's liveness re-derived independently, THREE
#   ways, all EXIT 1 with `unsolved goals` in a goal named `case «adm_1: …»`:
#   flipping clause 1 to `= true`; flipping the non-collapse `≠` to `=`; and
#   REPLACING THE CONDITIONING HYPOTHESIS with `True` (which demands the opaque
#   atom be `true` unconditionally — correctly unprovable). The third is the one
#   that shows the conditioning is load-bearing rather than decorative: the assert
#   is discharged BECAUSE it conditions, not because the prover ignores it.
#
# PROSE REPAIR made by this audit. Three passages claimed both soundness
#   positives are "definitionally the frozen return". That is FALSE on this
#   carrier and it mattered, because a definitionally-equal positive is a
#   restatement the elaborator absorbs for free — i.e. exactly the "neutered
#   positive" an audit is supposed to catch. Measured: a standalone `rfl` on
#   `(!b && X b) = (X b && !b)` FAILS with `is not definitionally equal to`, and
#   so does the branch form `(if b then false else X b) = (X b && !b)`; both need
#   `cases b <;> simp` (EXIT 0). The positives are therefore STRONGER than the
#   prose claimed — they force real case analysis at a shape the frozen script was
#   not written for — so the three passages now say `propositionally, not
#   definitionally` and cite the failing `rfl`. No case dict changed; the
#   correction is to the claim, not to what is tested.
#
# COVERAGE (re-run): obl=1 cases=6 (+3/-3) binders=1 pts=2-2, ok, 0 findings. The
#   binder variation is meaningful rather than two spellings of one point: at
#   `hasInitial = true` the post-image is transparently `false` and two rivals are
#   refuted there for DIFFERENT reasons (the opaque atom vs a constant `true`),
#   while at `hasInitial = false` the post-image IS the opaque atom and only
#   weak-const-false attacks it. Both values change the spec's verdict.
#
# NOT re-derived, by instruction: the divergence lane (closed by this bundle's
#   `total` semantics, which reject a diverging rival; the prose above records the
#   measured builds and no further builds were spent on it).
AXIOM_TESTS = []
