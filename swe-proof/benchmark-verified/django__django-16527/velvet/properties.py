"""properties.py — G-PBT falsification battery for django__django-16527 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method over five independent boolean inputs:

  showSaveAsNew (isPopup hasAddPermission hasChangePermission change saveAs : Bool)
      ensures result = (!isPopup && hasAddPermission && change && saveAs)

The single top-level ensures clause is an EXACT boolean equality: a
biconditional pinning the result on all 2^5 assignments. Any impl whose value
differs from the formula on even one assignment must be rejected. There is no
``require`` clause, so the admitted domain is total. Four of the five inputs
appear positively in the formula; ``hasChangePermission`` is observed but does
NOT appear — it exists so that an impl gating on the wrong permission is
expressible against this identical spec and diverges exactly where the two
permissions disagree.

The load-bearing decision is which permission gates the affordance: the ADD
permission ALONE. A viewer holding only the EDIT permission must NOT see the
create-a-new-object shortcut, since that shortcut creates a fresh object.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini
    because an input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter
    is an immutable ``Bool`` value (no ``mut`` binder in this bundle), there is
    no heap and no aliasing, so there is no read-only input to mutate and no
    substitute probe to build. Reported as vacuous, not fabricated (footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    boolean function of the method's own arguments (the ``axioms`` region
    declares nothing and there is no ``pure`` helper); there is no opaque
    answer key to echo. Any impl satisfying ``result = <formula>`` IS the
    formula. Instead we carry honest cheapest-reshape POSITIVE CONTROLS.
  * CONTROL-FLOW-EFFECT — N/A. Pure total boolean query, no exception, no side
    effect, no early-return path distinguishable from the returned value.
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the 2^5 cube but
    diverging on a sub-domain (gating on the wrong permission; on either
    permission; on neither; flipping the popup / edit-page / opt-in operand).
    Each is refuted at a concrete assignment, and the assignments jointly move
    every input binder across both of its values.

WITNESS PLACEMENT. Rivals do not share a refutation point. Where one rival is a
near-miss of another, its witness sits on the sub-domain that SEPARATES them so
its rationale's sub-domain claim is machine-checked, not asserted:
``weak-add-or-change`` is a near-miss of ``weak-prepatch-edit-perm`` (they
diverge from the spec on overlapping inputs), so ``weak-prepatch-edit-perm`` is
refuted at a point where the ADD permission is present (there the OR-gate rival
agrees with the frozen solution and only the edit-gate rival is wrong).

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the affordance
is a pure boolean combination modeled deeply). The gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16527"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region. It is a single contiguous line wholly inside the
# ---- one `-- impl-start` / `-- impl-end` region and unique in Solution.lean
# ---- (both facts asserted at load by _swap). --------------------------------
_GOLD_IMPL = "    return (!isPopup && hasAddPermission && change && saveAs)"

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `showSaveAsNewTester <args> = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped,
# ---- so no tactic script can mask the verdict. Every input is a `Bool`
# ---- literal, so each witness closes by `decide` with no extra instance.
# ---- Tester argument order matches the method signature:
# ----   isPopup  hasAddPermission  hasChangePermission  change  saveAs
_M = "showSaveAsNew"
_TESTER = (f"extract_program_for {_M}\n"
           f"prove_precondition_decidable_for {_M}\n"
           f"prove_postcondition_decidable_for {_M}\n"
           f"derive_tester_for {_M}\n\n")


def _witness(args):
    return (_TESTER +
            f"example : {_M}Tester {args} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify; else the exact-equality post-image is SPEC-TOO-STRONG.
    # Each keeps the obligation and only reshapes the executable surface; the
    # contract pins a single boolean VALUE over immutable inputs, so no
    # induction is needed and the frozen `loom_solve` still discharges it.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the four conjuncts reordered. `&&` is commutative and
        # associative, and the post pins the boolean VALUE not the term order,
        # so this computes the identical result on every one of the 2^5 inputs.
        "module": _impl(
            "    return (change && saveAs && hasAddPermission && !isPopup)"),
        "rationale": "a correct reshape (the four conjuncts reordered) computes "
                     "the identical boolean on every assignment and adds no new "
                     "proof obligation, so the single equality clause still "
                     "discharges under the frozen `loom_solve`; else "
                     "SPEC-TOO-STRONG on impl shape. `&&` is commutative/"
                     "associative — no lemma needed.",
    },
    {
        "id": "pos-control-ite-echo",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same value via an explicit if-then-else returning the two
        # boolean literals. Observationally the formula, computed by branching.
        "module": _impl(
            "    if (!isPopup && hasAddPermission && change && saveAs) "
            "then return true else return false"),
        "rationale": "an if-then-else that returns `true` exactly on the formula "
                     "and `false` otherwise is observationally `= <formula>` on "
                     "every input, so it must verify against the biconditional "
                     "post-image; a correct branch-reshape that could not verify "
                     "would be SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude any
    # input). Re-aimed at the residual admissibility risk on a total domain:
    # that the post-image is UNSATISFIABLE / degenerate at the interesting
    # point. This case discharges an in-region `assert` pinning the post-image
    # at BOTH discriminating shapes — a normal (non-popup) edit page with the
    # opt-in on, once with the ADD permission present (the affordance MUST show)
    # and once with only the EDIT permission (it MUST hide). The impl is kept
    # verbatim so the method's own obligation still discharges; the assert is
    # live, not decoration — a false claim about the same points leaves an
    # unsolved goal (verified: a mirror assert claiming the hide case shows
    # fails to elaborate).
    # =====================================================================
    {
        "id": "admiss-add-vs-edit-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `assert\n"
            "      (((!false && true && true && true) = true) ∧\n"
            "       ((!false && false && true && true) = false)))\n"
            + _GOLD_IMPL),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "decisive shapes: on a normal edit page with the opt-in on, "
                     "the formula demands the affordance be SHOWN when the ADD "
                     "permission is held and HIDDEN when only the edit permission "
                     "is held. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / PRECOND-TOO-STRONG); the impl "
                     "is verbatim so the equality clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. The six witnesses probe
    # six distinct assignments that jointly vary all five input binders.
    # =====================================================================
    {
        "id": "weak-prepatch-edit-perm",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: gate on the EDIT permission instead of the ADD
        # permission. Diverges from the formula on every input where the two
        # permissions disagree.
        "module": _impl(
            "    return (!isPopup && hasChangePermission && change && saveAs)"),
        "refinement": "the faithful real counterpart keeps the affordance gated "
                      "on the EDIT permission, so a viewer holding only the edit "
                      "right is still shown the create-a-new-object shortcut. The "
                      "failing test that constructs exactly such a viewer on a "
                      "normal edit page with the opt-in on, and asserts the "
                      "shortcut is HIDDEN, still observes it shown. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the biconditional `result = (!isPopup && "
                     "hasAddPermission && change && saveAs)`: with the ADD "
                     "permission PRESENT and the edit permission ABSENT the "
                     "post-image demands `true` but the edit-gated impl yields "
                     "`false`. Refuted at (isPopup=F, add=T, edit=F, change=T, "
                     "saveAs=T) — a point where the ADD permission is present, so "
                     "the OR-gate near-miss (weak-add-or-change) AGREES with the "
                     "frozen solution there and this rival is the sole diverger; "
                     "that is what separates the two rivals' witnesses.",
        "witness": _witness("false true false true true"),
    },
    {
        "id": "weak-add-or-change",
        "kind": "uniqueness",
        "expect": "reject",
        # 'Either permission counts': gate on (add || edit). Equals the formula
        # whenever the ADD permission is present; admits the edit-only viewer
        # (add=F, edit=T) where the formula is false. Near-miss of the pre-fix
        # bug, refuted on the complementary sub-domain.
        "module": _impl(
            "    return (!isPopup && (hasAddPermission || hasChangePermission) "
            "&& change && saveAs)"),
        "refinement": "the faithful real counterpart gates on EITHER permission. "
                      "Checking the ADD permission ALONE is what the fix "
                      "requires; an either-permission gate still shows the "
                      "shortcut to the edit-only viewer (add=F, edit=T), so the "
                      "failing test that asserts it HIDDEN for that viewer still "
                      "observes it shown. It would NOT resolve.",
        "rationale": "REJECT from the biconditional: at (isPopup=F, add=F, "
                     "edit=T, change=T, saveAs=T) the impl yields `true` (the "
                     "edit disjunct fires) while the formula (keyed on the ADD "
                     "permission) yields `false`. Refuted at the edit-only "
                     "sub-domain the pre-fix rival's witness does not probe.",
        "witness": _witness("false false true true true"),
    },
    {
        "id": "weak-drop-add-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the permission gate entirely (regression to no permission
        # check). Agrees with the formula wherever the ADD permission is present;
        # diverges (true vs false) on any non-popup edit page with the opt-in on
        # that lacks the ADD permission.
        "module": _impl("    return (!isPopup && change && saveAs)"),
        "refinement": "the faithful real counterpart drops the permission gate "
                      "altogether, re-opening the very hole the fix closes: a "
                      "viewer with NEITHER the add nor the edit permission is "
                      "shown the create-a-new-object shortcut. The failing test "
                      "asserting the shortcut is HIDDEN for a viewer without the "
                      "ADD permission still observes it shown. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the biconditional: at (isPopup=F, add=F, "
                     "edit=F, change=T, saveAs=T) the impl yields `true` while "
                     "the formula yields `false` (the missing ADD permission "
                     "kills it). Refuted with NEITHER permission held — a third "
                     "distinct assignment of the two permission binders, "
                     "complementary to both permission-gate rivals above.",
        "witness": _witness("false false false true true"),
    },
    {
        "id": "weak-flip-popup-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption: gate on `isPopup` rather than `!isPopup`,
        # exposing the shortcut only in popups and withholding it on real edit
        # pages.
        "module": _impl(
            "    return (isPopup && hasAddPermission && change && saveAs)"),
        "refinement": "the faithful real counterpart gates on the popup flag "
                      "rather than its negation, so the shortcut appears only in "
                      "popup requests. The failing test runs an add-and-edit "
                      "viewer on a NORMAL (non-popup) edit page and expects the "
                      "shortcut SHOWN; this impl hides it there. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the biconditional: at (isPopup=T, add=T, "
                     "edit=T, change=T, saveAs=T) the impl yields `true` while "
                     "the formula (which requires a non-popup request) yields "
                     "`false`. Refuted at isPopup=T — the only witness that "
                     "moves the popup binder off `false`.",
        "witness": _witness("true true true true true"),
    },
    {
        "id": "weak-flip-editpage-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption on the edit-page operand: gate on `!change`
        # rather than `change`, exposing the shortcut on add pages and hiding it
        # on the edit view. Built to move the `change` binder, which every other
        # rival holds at `true`.
        "module": _impl(
            "    return (!isPopup && hasAddPermission && !change && saveAs)"),
        "refinement": "the faithful real counterpart gates on the negation of "
                      "the edit-view flag, so the shortcut is offered on an add "
                      "page and withheld on the edit view of an existing object "
                      "— where a duplicate-as-new only makes sense. The failing "
                      "test runs on the edit view (change=True) and expects the "
                      "shortcut SHOWN for an add-permitted viewer; this impl "
                      "hides it there. It would NOT resolve.",
        "rationale": "REJECT from the biconditional: at (isPopup=F, add=T, "
                     "edit=F, change=F, saveAs=T) the impl yields `true` (its "
                     "`!change` operand fires) while the formula (which requires "
                     "the edit view) yields `false`. Refuted at change=F — the "
                     "only witness that moves the edit-view binder off `true`.",
        "witness": _witness("false true false false true"),
    },
    {
        "id": "weak-flip-optin-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Single-operand corruption on the opt-in operand: gate on `!saveAs`
        # rather than `saveAs`, exposing the shortcut for admins that did NOT opt
        # in and hiding it for those that did. Built to move the `saveAs` binder,
        # which every other rival holds at `true`.
        "module": _impl(
            "    return (!isPopup && hasAddPermission && change && !saveAs)"),
        "refinement": "the faithful real counterpart gates on the negation of "
                      "the duplicate-as-new opt-in, so the shortcut is offered "
                      "exactly for admins that did NOT enable it. The failing "
                      "test enables the opt-in (save_as=True) and expects the "
                      "shortcut SHOWN for an add-permitted viewer; this impl "
                      "hides it there. It would NOT resolve.",
        "rationale": "REJECT from the biconditional: at (isPopup=F, add=T, "
                     "edit=F, change=T, saveAs=F) the impl yields `true` (its "
                     "`!saveAs` operand fires) while the formula (which requires "
                     "the opt-in) yields `false`. Refuted at saveAs=F — the only "
                     "witness that moves the opt-in binder off `true`.",
        "witness": _witness("false true false true false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals; frame-mutation is recorded
# N/A there, not shipped). The sibling contracts one function
# (`save_as_new_visible`) over five booleans; this bundle contracts the same
# one method (`showSaveAsNew`) over the same five booleans, so the carrier is a
# near-identity and every sibling case maps directly.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-control-reorder           -> pos-control-reorder             PORTED
#   pos-control-cheapest-inline   -> pos-control-ite-echo            RE-EXPRESSED
#   admiss-f2p-shaped             -> admiss-add-vs-edit-shape        RE-AIMED
#   weak-prepatch-may-change      -> weak-prepatch-edit-perm         PORTED
#   weak-add-or-change            -> weak-add-or-change              PORTED
#   weak-drop-add-conjunct        -> weak-drop-add-conjunct          PORTED
#   weak-flip-popup-gate          -> weak-flip-popup-gate            PORTED
#   (sibling frame-mutation note) -> (none)                          VACUOUS
#
# 5 ported, 1 re-expressed, 1 re-aimed, 1 vacuous.
#
# RE-EXPRESSED (soundness): the sibling's cheapest-inline positive returns the
#   formula inline with no local binding. Velvet's frozen impl ALREADY returns
#   the formula inline, so a byte-for-byte "inline return" reshape would be the
#   gold impl itself (not a structurally different control). It is re-expressed
#   as an explicit if-then-else echo — a genuinely different control shape that
#   is still observationally the formula — preserving the "cheapest honest
#   positive control" ARGUMENT while making the reshape non-trivial.
# RE-AIMED (admissibility): the sibling asserts, via a caller, that a normal
#   F2P-shaped input verifies the pre/postcondition. No method here has a
#   `require` clause, so the "admits a normal input" reading is vacuous; the
#   case is re-aimed at proving the post-image is satisfiable and NON-degenerate
#   at the two discriminating shapes (add-permitted -> shown; edit-only ->
#   hidden). The in-region assert is discharged symbolically against concrete
#   literals under the frozen `loom_solve` (verified: a mirror assert claiming
#   the hide case shows leaves an unsolved goal, so the assert is load-bearing).
# FRAME-MUTATION: VACUOUS here. This backend is referentially transparent, has
#   no heap and no aliasing, and this bundle declares NO `mut` binder — there is
#   no read-only input to overwrite and no substitute probe to build. No case
#   fabricated (matching, and strengthening, the sibling's own N/A note).
#
# ADDED (2, no sibling counterpart): weak-flip-editpage-gate and
#   weak-flip-optin-gate. The sibling's rivals all hold `change` and `save_as`
#   fixed at True (they only ever diverge from the formula there), so the
#   sibling battery never moves those two binders. Each added rival is a
#   single-operand corruption of one of those operands (`change` -> `!change`,
#   `saveAs` -> `!saveAs`), refuted at the assignment that moves that binder off
#   `true`. Each is a real divergence from the biconditional with a
#   machine-checked witness, and each carries the refinement argument for why
#   its faithful counterpart would still leave the failing test failing (both
#   F2P viewers run on the edit view with the opt-in on, so a flipped gate hides
#   the shortcut where the test expects it shown).
#
# BINDER / POINT COVERAGE. The six reject witnesses probe six distinct inputs
#   (isPopup, add, edit, change, saveAs):
#     (F, T, F, T, T)   weak-prepatch-edit-perm
#     (F, F, T, T, T)   weak-add-or-change
#     (F, F, F, T, T)   weak-drop-add-conjunct
#     (T, T, T, T, T)   weak-flip-popup-gate
#     (F, T, F, F, T)   weak-flip-editpage-gate
#     (F, T, F, T, F)   weak-flip-optin-gate
#   so isPopup is varied over F/T, hasAddPermission over T/F,
#   hasChangePermission over F/T, change over T/F, and saveAs over T/F. No input
#   binder is pinned across the battery, and the single top-level biconditional
#   clause is attacked on every one of its five operands and defended by the two
#   positive controls and the admissibility case.
#
# WITNESS DISTINCTNESS. weak-add-or-change is a near-miss of
#   weak-prepatch-edit-perm: both diverge from the formula on inputs where the
#   permissions disagree. So weak-prepatch-edit-perm is refuted at
#   (isPopup=F, add=T, edit=F, ...) — the ADD permission PRESENT — where the
#   OR-gate rival AGREES with the frozen solution (verified) and only the
#   edit-gate rival is wrong; weak-add-or-change is refuted at the mirror
#   (add=F, edit=T). Every other witness sits at a point no other rival is wrong
#   at, so no witness is shared.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
