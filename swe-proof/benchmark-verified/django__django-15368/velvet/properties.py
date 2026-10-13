"""properties.py — G-PBT falsification battery for django__django-15368 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct routeOperands`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a finite list of per-element
values). The single obligation is

    routeOperands (attrs : List AttrVal)   ensures out = wrapPlan attrs

with ``wrapPlan`` mapping, element by element and in order,
``wrapPlan (a :: rest) = (! a.isDbExpr) :: wrapPlan rest``: each element carries
TWO independent classification bits, ``isDbExpr`` and ``strictMatch``, and the
routing bit for that element is ``! isDbExpr`` — a value is routed as a literal
operand exactly when it is NOT a database-side expression; a database-side
expression is applied directly so it resolves on its own. ``attrs`` is the sole
input binder. The load-bearing content is that the decision keys on the
``isDbExpr`` bit ALONE — never on the coarser ``strictMatch`` bit, which is
strictly narrower (an element may be a genuine database-side expression yet not
be recognised by the coarser bit). The pre-image keyed on ``strictMatch`` and so
mis-routed exactly the values that carry ``isDbExpr = true, strictMatch = false``.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``AttrVal`` is a ``structure`` deriving ``DecidableEq``, and ``wrapPlan`` is a
concrete front-recursive ``def`` in the ``pure`` region (the ``axioms`` region
declares nothing). So each rival's violation reduces to a decidable equality of
concrete ``List Bool`` values, and a ``decide`` witness at a small literal input
discriminates. The reject lane is fully expressible on this carrier — no
NO-REJECT-LANE collapse.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the per-element routing bit bound to a local)
    must still verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries NO ``require`` clause (the
    pre-conditions region is empty), so the sibling's "a normal F2P-shaped input
    satisfies the precondition" probe is degenerate here (every input is
    in-domain). It is re-aimed at the residual total-domain risk — that the
    post-image is DEGENERATE at the interesting point — via an in-region assert
    pinning BOTH branches of the per-element decision at the F2P-shaped point (a
    database-side expression that the coarser bit misses -> applied directly; a
    plain datum -> routed as a literal). The impl is kept verbatim so the
    method's own obligation still discharges.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    TWO mandatory frame-mutation probes (a write to the read-only ``resolvable``
    input, and one to the read-only ``in_family`` input) because a read-only
    input there is held at a fractional heap permission an impl can overwrite.
    Lean and Velvet are referentially transparent: ``attrs`` is an immutable
    value (declared read-only, not ``mut``), there is no heap and no aliasing —
    so there is no read-only input to overwrite and no substitute probe to build.
    Not fabricated (reported as an omission in the footer); the sibling's "inputs
    are not mutated" obligation is structurally guaranteed by the ABSENCE of
    ``mut``.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. ``wrapPlan``
    is a total, fully-unfolded function of the method's OWN input — there is no
    opaque answer key to echo (evaluating ``wrapPlan`` IS the correct answer), so
    there is no wrong echo to build. The honest cheapest reshapes stand in as the
    ``pos-*`` controls.
  * PARTIAL-DOMAIN / VALUE — APPLIES and is the heart of the port. The pre-image
    (decide on the coarser ``strictMatch`` bit) is correct wherever the two bits
    agree and wrong exactly on the ``isDbExpr = true, strictMatch = false``
    sub-domain (the F2P discriminator); the inverted decision is the catastrophic
    opposite; the last-element mask attacks the tail of the per-index pin; and a
    reversed traversal attacks the ORDER clause the list carrier introduces.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches it through Velvet's own tester
machinery: ``routeOperandsTester <attrs> = false`` says the extracted program's
result violates the postcondition at that concrete input, checked in a file
whose ``prove_correct`` block has been stripped (no tactic script can mask the
verdict). There is no ``require`` clause, so the precondition is ``True`` and
decides trivially. The frozen program contains a ``while`` loop, whose fixpoint
does not reduce under the kernel's ``decide``; every reject rival is reshaped
into a LOOP-FREE closed form, so ITS tester ``decide``s while the SAME witness
applied to the loop-bearing frozen solution cannot reduce and so fails to
elaborate. The discrimination is thus structural, not a tactic-tuning artifact.
(Verified out of band with ``scripts/lean_verify.sh``: each witness builds green
against its rival and red against the frozen solution.) No ``sorry`` / ``admit``
/ ``native_decide`` / ``axiom``.
"""
from pathlib import Path

INSTANCE = "django__django-15368"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the per-element values. Reject rivals replace this with a loop-free closed
# form (so their tester reduces under `decide`).
_IMPL = """    let mut result : List Bool := []
    let mut i := attrs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ attrs.length
      invariant result = wrapPlan (attrs.drop i)
      done_with i = 0
      decreasing i
    do
      let a := attrs[i - 1]!
      result := (! a.isDbExpr) :: result
      i := i - 1
    return result"""
assert _BASE.count(_IMPL) == 1, "routeOperands impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let a := attrs[i - 1]!
      result := (! a.isDbExpr) :: result
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut result : List Bool := []"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this to a bare `loom_solve`; the tactic body is
# elided from the spec view, so this is a proof reshape, not a spec change.
_PROOF = """prove_correct routeOperands by
  loom_solve
  rw [wrapPlan_drop_step attrs i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `routeOperandsTester <attrs> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for routeOperands\n"
    "prove_precondition_decidable_for routeOperands\n"
    "prove_postcondition_decidable_for routeOperands\n"
    "derive_tester_for routeOperands\n\n"
)


def _witness(attrs_literal):
    return _TESTER + f"example : routeOperandsTester {attrs_literal} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = wrapPlan attrs`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same routing plan; the loop-specific proof
        # is retuned to a bare `loom_solve` since the impl now matches the
        # post-image syntactically.
        "module": _swap(
            _swap(_BASE, _IMPL, "    return (wrapPlan attrs)"),
            _PROOF, "prove_correct routeOperands by\n  loom_solve"),
        "rationale": "a loop-free impl that returns the routing plan directly must "
                     "satisfy `out = wrapPlan attrs`; a correct reshape of the "
                     "modeled behaviour verifying is exactly what SPEC-TOO-STRONG "
                     "would deny. Exercises the obligation from a maximally "
                     "different (loop-free) control-flow shape. (Sibling: "
                     "pos-control-collapsed-branch.)",
    },
    {
        "id": "pos-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-element routing bit to a local `b` inside the
        # loop instead of prepending the expression directly. Same value flow;
        # the loop and the front-recursive invariant are unchanged, so the frozen
        # proof still closes untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let a := attrs[i - 1]!\n"
            "      let b : Bool := ! a.isDbExpr\n"
            "      result := b :: result\n"
            "      i := i - 1"),
        "rationale": "binding the per-element routing bit to a local before "
                     "prepending it computes the same plan element-for-element, "
                     "with the loop and invariant unchanged, so the frozen proof "
                     "closes and `out = wrapPlan attrs` still holds; a correct "
                     "reshape must verify, else SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-rename-local.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so the domain is
    # total; the sibling's "a normal F2P-shaped input satisfies the
    # precondition" probe is degenerate (every input is in-domain). The residual
    # risk on this transparent, total-domain carrier is that the post-image is
    # DEGENERATE at the interesting point — a routing plan that never actually
    # applied a database-side expression directly while wrapping a plain datum
    # would read like a live one. This case discharges an in-region assert
    # pinning BOTH branches of the per-element decision at the F2P-shaped point:
    # a value that IS a database-side expression yet is missed by the coarser bit
    # (isDbExpr = true, strictMatch = false) is applied directly (`false`); a
    # plain datum (isDbExpr = false) is routed as a literal (`true`). The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim leaves an unsolved goal), and
    # the proof's alternation gains one `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `assert\n"
                "      (wrapPlan [{ isDbExpr := true, strictMatch := false }] = [false] ∧\n"
                "       wrapPlan [{ isDbExpr := false, strictMatch := false }] = [true]))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct routeOperands by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [wrapPlan_drop_step attrs i (by omega) (by omega)]; simp_all)"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: it demands a database-side expression that "
                     "the coarser bit misses (isDbExpr = true, strictMatch = false) "
                     "be applied directly (`false`) and a plain datum "
                     "(isDbExpr = false) be routed as a literal (`true`) — the two "
                     "branches of the per-element decision. The in-region assert "
                     "must discharge (else the obligation is degenerate); the impl "
                     "is kept verbatim so `out = wrapPlan attrs` still verifies. "
                     "(Sibling: admiss-self-call, re-aimed.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-decide-on-strictmatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminator (the pre-image). Route on the COARSER `strictMatch`
        # bit instead of `isDbExpr`. Correct on every element where the two bits
        # agree (a plain datum: both false; a recognised expression: both true),
        # WRONG exactly on the isDbExpr = true, strictMatch = false sub-domain —
        # a genuine database-side expression the coarser bit does not recognise.
        "module": _swap(
            _BASE, _IMPL,
            "    return (attrs.map (fun a => ! a.strictMatch))"),
        "refinement": "this is the literal pre-image: keying the routing decision "
                      "on the coarser classification bit instead of the "
                      "database-side-expression property. A value that IS a "
                      "database-side expression yet is not recognised by the coarser "
                      "bit gets routed as a literal operand, so its surface form is "
                      "frozen instead of resolving on the database side — exactly the "
                      "defect the failing test exhibits (the reported value stored as "
                      "its literal text rather than resolving to the referenced "
                      "column). It would NOT resolve (G-DIFF).",
        "rationale": "REJECT from `out = wrapPlan attrs`: on the "
                     "isDbExpr = true, strictMatch = false sub-domain the post-image "
                     "demands `! isDbExpr = false` (apply directly) while the rival "
                     "yields `! strictMatch = true` (route as literal). Refuted at a "
                     "one-element list whose element realises the strict gap — the "
                     "precise cell the F2P exercises.",
        "witness": _witness(
            "[{ isDbExpr := true, strictMatch := false }]"),
    },
    {
        "id": "weak-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # The catastrophic inversion: route as a literal iff the value IS a
        # database-side expression (the exact opposite of the spec). Wrong on
        # every non-empty batch: wraps expressions (freezing their surface form)
        # and applies plain data directly (emitting a raw datum where a bound
        # literal is required).
        "module": _swap(
            _BASE, _IMPL,
            "    return (attrs.map (fun a => a.isDbExpr))"),
        "refinement": "inverting the routing decision routes every database-side "
                      "expression as a literal (freezing its surface form) and "
                      "applies every plain datum directly (emitting a raw datum "
                      "where a bound literal is required). Both the F2P (an "
                      "expression stored as its literal text) and every pre-existing "
                      "test carrying plain data would fail. It would NOT resolve.",
        "rationale": "REJECT from `out = wrapPlan attrs`: the post-image pins each "
                     "bit to `! isDbExpr`, and the rival yields `isDbExpr`, so the "
                     "two disagree on every element. Refuted at a one-element list "
                     "with a plain datum (isDbExpr = false): gold demands `true`, the "
                     "rival yields `false`. Supporting near-miss carrying the "
                     "catastrophic-inversion refinement. (Sibling: "
                     "weak-inverted-decision.)",
        "witness": _witness(
            "[{ isDbExpr := false, strictMatch := false }]"),
    },
    {
        "id": "weak-last-element-false",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, the tail: route every element correctly EXCEPT force
        # the LAST output bit to `false` unconditionally. Correct on every batch
        # whose last value is a database-side expression; wrong whenever the last
        # value is a plain datum that must be routed as a literal (`true`).
        "module": _swap(
            _BASE, _IMPL,
            "    return ((attrs.map (fun a => ! a.isDbExpr)).dropLast ++ [false])"),
        "refinement": "forcing the last routing bit to `false` applies the final "
                      "value directly even when it is a plain datum that must be "
                      "routed as a literal, so for a batch whose last value is plain "
                      "data the emitted per-row operand is a raw datum where a bound "
                      "literal is required — diverging from the gold output for that "
                      "object; the pre-existing tests with a plain-data last value "
                      "would fail. It would NOT resolve.",
        "rationale": "REJECT from `out = wrapPlan attrs`: `wrapPlan` pins the last "
                     "position to `! isDbExpr` of the last element; forcing `false` "
                     "there mismatches whenever that element has isDbExpr = false. "
                     "Refuted at a two-element list whose last value is a plain datum "
                     "(gold `[false, true]`, rival `[false, false]`) — the only "
                     "reject varying `attrs.length` at the tail. (Sibling: "
                     "weak-last-element-false.)",
        "witness": _witness(
            "[{ isDbExpr := true, strictMatch := true }, "
            "{ isDbExpr := false, strictMatch := false }]"),
    },
    {
        "id": "weak-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # Route every element correctly but emit the plan in REVERSED order.
        # Every per-element decision is right; only the traversal order is wrong
        # — a clause that exists here because the carrier is a LIST of values
        # (the sibling's per-cell fold pins each index, so reversal breaks the
        # per-index correspondence). Refuted only on a list of length >= 2.
        "module": _swap(
            _BASE, _IMPL,
            "    return ((attrs.map (fun a => ! a.isDbExpr)).reverse)"),
        "refinement": "a counterpart that routed each value correctly but associated "
                      "the routing bits with the wrong values (reversed traversal) "
                      "would apply each per-row conditional to a different object's "
                      "value; the tests assert each row is routed by ITS OWN value. "
                      "It would NOT resolve.",
        "rationale": "REJECT from `out = wrapPlan attrs`: `wrapPlan` fixes the "
                     "per-index correspondence, and reversing it disagrees on any "
                     "list of length >= 2 whose routed bits differ. Refuted at a "
                     "two-element list mixing a database-side expression and a plain "
                     "datum (gold `[false, true]`, rival `[true, false]`), so the "
                     "traversal-order clause the list carrier introduces is attacked. "
                     "(ADDED for the list carrier.)",
        "witness": _witness(
            "[{ isDbExpr := true, strictMatch := false }, "
            "{ isDbExpr := false, strictMatch := true }]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 2 mandatory frame-mutation rivals, 3
# partial-domain uniqueness rivals) plus 1 AXIOM_TESTS entry. The sibling
# contracts `build_wrap_flags(in_family, resolvable)` over TWO read-only
# List[bool] inputs held at fractional heap permission, with the routing plan
# built by a verified backward `while` loop over `resolvable`. This bundle
# contracts one method, `routeOperands`, over a single `List AttrVal` whose
# elements carry the same two classification bits (`isDbExpr` <- resolvable,
# `strictMatch` <- in_family) with a deep front-recursive `wrapPlan` fold and no
# axioms. The two surfaces model the SAME per-element decision (route as literal
# iff NOT a database-side expression, keyed on `isDbExpr`, never `strictMatch`),
# so the value/partial-domain rivals port near-1:1 with two carrier consequences:
# both frame-mutation rivals are vacuous here, and the list carrier ADDS a
# traversal-order clause the sibling's fold pins implicitly.
#
#   sibling case                  kind          -> here                       disposition
#   -----------------------------------------------------------------------------------
#   pos-control-collapsed-branch  soundness     -> pos-closed-form            PORTED
#   pos-control-rename-local      soundness     -> pos-letbind                PORTED
#   admiss-self-call              admissibility -> admiss-grounded            RE-AIMED
#   frame-mutate-resolvable       uniqueness    -> (none)                     VACUOUS
#   frame-mutate-in-family        uniqueness    -> (none)                     VACUOUS
#   weak-decide-on-in-family      uniqueness    -> weak-decide-on-strictmatch PORTED
#   weak-last-element-false       uniqueness    -> weak-last-element-false    PORTED
#   weak-inverted-decision        uniqueness    -> weak-inverted-decision     PORTED
#   (—)                           uniqueness    -> weak-reversed              ADDED
#   ax-ref-wrap-flags-predicate   axiom         -> (none)                     G-AX
#
# PORTED (positives): the sibling's two honest reshapes (collapse the if/else
#   into a computed bool; rename the decision local) become the closest reshapes
#   on this carrier — a loop-free closed form returning the plan directly
#   (pos-closed-form, proof retuned to a bare `loom_solve`) and a loop-preserving
#   let-bind of the routing bit (pos-letbind, frozen proof unchanged). The
#   sibling's gold used an explicit if/else; this bundle's gold already computes
#   the bit as `! a.isDbExpr`, so the branch-collapse spirit is carried by the
#   let-bind. Two maximally-different shapes defend against SPEC-TOO-STRONG on
#   both the loop-free and loop-bearing forms.
# RE-AIMED (admiss-self-call -> admiss-grounded): the sibling's admissibility
#   case builds an F2P-shaped input and self-calls to show the half-permission
#   precondition (equal lengths; in_family[i] ==> resolvable[i]) is met. This
#   backend's method has NO `require` clause and no permission surface, so that
#   probe is degenerate (every input is in-domain). It is re-aimed at the
#   residual total-domain risk — a degenerate post-image — via a live in-region
#   assert pinning BOTH branches of the per-element decision (apply-directly on
#   the strict-gap expression, route-as-literal on a plain datum) at the F2P cell.
# VACUOUS (both frame-mutation probes): the sibling's MANDATORY probes overwrite
#   an input held at half heap permission (`resolvable[j] = True`,
#   `in_family[j] = False`) and are rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent, there is no heap, no aliasing, and this
#   bundle declares no `mut` binder on `attrs`, so there is no read-only input to
#   overwrite and no substitute probe exists. Not fabricated (spec_guide
#   directive 5: the frame obligation here is discharged by the ABSENCE of a
#   `mut`, which the frozen spec already encodes).
# PORTED (the three value rivals): weak-decide-on-in-family ports directly to
#   weak-decide-on-strictmatch (the literal pre-image, refuted on the strict-gap
#   sub-domain isDbExpr = true, strictMatch = false — the F2P cell).
#   weak-inverted-decision ports directly (the catastrophic inversion, refuted at
#   a plain datum). weak-last-element-false ports directly (force the tail bit
#   false, refuted at a two-element list with a plain-data last value).
# ADDED (weak-reversed): the list carrier makes the traversal-ORDER clause
#   attackable directly. `wrapPlan` fixes the per-index correspondence between an
#   input value and its routing bit; a rival that routes each element correctly
#   but reverses the plan is refutable only on a length >= 2 list. This both
#   closes the order clause and is the sole reject varying `attrs.length` beyond
#   one.
# AXIOM_TESTS (1): dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   the R type bijection — isDbExpr/strictMatch == the real predicates, and
#   `! isDbExpr` == the real post-patch routing decision); the classification is
#   modeled deeply here as the pure `wrapPlan` fold with no consumed axiom (the
#   axioms region is empty), and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `attrs : List AttrVal`, whose elements carry `isDbExpr` and `strictMatch`, and
#   one top-level clause, `out = wrapPlan attrs`, which internally pins each
#   position to `! isDbExpr`. The four reject witnesses probe four DISTINCT input
#   points (pts=4):
#     attrs        : len 1 (strict-gap), len 1 (plain datum), len 2 (tail),
#                    len 2 (order)  — `attrs.length` over 1 and 2, never fixed.
#     isDbExpr     : true (strict-gap / order elt 0 / tail elt 0) and
#                    false (inverted / tail elt 1 / order elt 1) — both values.
#     strictMatch  : false (strict-gap / inverted / order elt 0) and
#                    true (tail elt 0 / order elt 1) — both values, and
#                    weak-decide-on-strictmatch DEPENDS on it diverging from
#                    isDbExpr (its whole divergence is reading strictMatch where
#                    the spec reads isDbExpr), so the decoy bit is genuinely abused
#                    rather than held fixed.
#   Both directions of the per-element decision are attacked (apply-directly vs
#   route-as-literal), the tail position is masked, and the per-index traversal
#   order is attacked, so no rival that mishandled only a fixed-value binder could
#   slip through. The near-miss (weak-decide-on-strictmatch) is separated from the
#   exact-inversion rival: at the strict-gap point the inversion also fails, but
#   at the plain-datum point the strictmatch rival AGREES with gold, so each
#   carries its own separating input.
AXIOM_TESTS = []
