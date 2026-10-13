"""properties.py — G-PBT falsification battery for django__django-15104 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct fieldDefsIgnoringRelationTargets`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the subject it names — here the
``witness_reference`` impl, not the frozen solution; see WITNESS SUBJECT).

DEFENDED SURFACE (one contracted method):

  fieldDefsIgnoringRelationTargets (fields : List FieldDef)
      return (out : Except Unit (List (List (String × Int))))
    ensures out = Except.ok (viewAll fields)            -- the WHOLE pin (C1)

Each element of ``fields`` is one field's canonicalized definition reduced to
the two facts the comparison view distinguishes: whether the field references
another model (``relational : Bool``) and its keyword bindings (``kwargs``, each
a name paired with an opaque identity token for its value). The method assembles
the comparison view of the whole collection; it ALWAYS succeeds (the success
constructor ``Except.ok``) and yields, in order, the per-field view: a
relational field has its relation-target binding (the entry keyed ``"to"``)
elided, a non-relational field is carried unchanged. The pure region pins the
whole outcome as a total function of the method's own input:

  dropTarget kw       = kw.filter (·.1 ≠ "to")
  fieldView f         = if f.relational then dropTarget f.kwargs else f.kwargs
  viewAll []          = []
  viewAll (f :: fs)   = fieldView f :: viewAll fs

so C1 (``out = Except.ok (viewAll fields)``) is the sole impl-constraining
clause and it is GROUNDED: ``viewAll``/``fieldView``/``dropTarget`` are
transparent ``def``s over the method's own argument (the ``axioms`` region is
empty; there is NO opaque answer-key oracle), so pinning ``out = Except.ok
(viewAll fields)`` cannot be satisfied by a wrong echo — it forces the correct
per-field elision, in order, wrapped in the success constructor, for the whole
list. C1 pins FIVE independent things about the output, each attacked by some
rival below:

  * (D) DEFINEDNESS — the outcome is the SUCCESS constructor ``Except.ok``, NEVER
        the failure constructor ``Except.error``, for EVERY input — INCLUDING a
        relational field carrying no ``"to"`` binding at all. This is the exact
        behaviour the change under test turns on: the pre-change removal
        signalled failure on that shape (it raised), the post-change removal is a
        no-op there. The discriminator bites on a relational field whose kwargs
        omit ``"to"``.
  * (R+) RELATIONAL ARM — a relational field's ``"to"`` binding IS elided.
  * (R−) NON-RELATIONAL ARM — a non-relational field is carried UNCHANGED, so its
        ``"to"`` binding (if any) SURVIVES.
  * (C) NO COLLATERAL LOSS — ONLY the ``"to"`` binding is elided; every other
        binding is preserved with its value.
  * (O) ORDER — the per-field views appear in the SAME order as the input
        collection (``viewAll`` is front-recursive). Observable only at a
        collection of two or more fields whose views differ, so it is the one
        aspect no single-field witness can reach; attacked by
        rival-order-reversed.

The sole input binder ``fields`` is free (no ``require`` clause) and the
post-image must hold for EVERY value; the reject witnesses vary it across the
``relational`` split (fields where it is true and false) and the ``kwargs``
shape (with ``"to"`` present, with ``"to"`` absent, with an extra binding), and
the collection LENGTH (one field, and a two-field collection for order).

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case accounting
in the footer):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling makes it MANDATORY:
    its ``rival-frame-mutate-input`` keeps the correct removal but first WRITES
    back into the read-only input mapping held at a fractional heap permission
    (``Acc(dict_pred(kwargs),1/2)``) and is rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: ``fields`` is an immutable
    value, this bundle declares no ``mut`` binder on any parameter, and there is
    no heap, aliasing, or permission system to subvert. There is no read-only
    input to overwrite, so the class is vacuous. No substitute probe is
    fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the nagini sibling
    records. The post-image C1 is ``Except.ok (viewAll fields)``, a transparent
    fold over the method's own argument; there is no opaque answer key to echo.
    The honest cheapest CORRECT impl (``return Except.ok (viewAll fields)``) is
    carried as a POSITIVE control instead — it doubles as proof the spec is not
    echo-vulnerable, since any impl that keeps ``"to"`` on a relational field,
    strips it from a non-relational field, drops a second binding, or reports
    failure fails ``out = Except.ok (viewAll fields)``.
  * PARTIAL-DOMAIN / CONTROL-FLOW / VALUE — the whole reject surface, all against
    C1. A rival can drop ``"to"`` UNCONDITIONALLY (collapsing the relational
    fork, so a non-relational field loses it), never drop it (so a relational
    field keeps it), drop a second binding too (collateral loss), or report
    failure on the ``"to"``-absent relational shape (the pre-change removal).
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS ON THIS BUNDLE. C1's carrier is fully TRANSPARENT
(``viewAll``/``fieldView``/``dropTarget``/``FieldDef`` are concrete
``def``/``structure``; the ``axioms`` region is empty), so the postcondition is
decidable at concrete inputs. Each rival is written LOOP-FREE (a ``fields.map`` /
``fields.any`` over the whole list), so its extracted program
``fieldDefsIgnoringRelationTargetsExec`` — the ``NonDetT``-run of the impl —
REDUCES fully under ``decide`` at a concrete input. The result carrier ``Except
Unit _`` needs a decidable equality the extractor does not synthesize on its own,
so each witness derives it first via ``deriving instance DecidableEq for Except``
— an instance, not an assumption (no ``axiom`` / ``sorry`` / ``native_decide``),
appended to BOTH files the check builds, so the reference impl still rejects the
witness.
Each witness states, at one concrete input,

    (match fieldDefsIgnoringRelationTargetsExec <input> with
       | DivM.res r => r | _ => Except.error ())
        ≠ Except.ok (viewAll <input>)

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator sees.

WITNESS SUBJECT — the second half of the discrimination check (AUDIT-CORRECTED).
The frozen solution CANNOT serve as the subject the witness is refuted against,
and an earlier revision of this file wrongly claimed that it could ("gold's
``…Exec`` stays stuck, so ``decide`` cannot close the ``≠`` — exactly the
discrimination the gate requires"). That reasoning is backwards. Gold's body is
the backward ``while`` fold, whose ``…Exec`` the kernel does not reduce, so a
``decide`` against it reports

    Tactic `decide` failed ... because its `Decidable` instance instDecidableNot
    did not reduce to `isTrue` or `isFalse`

for EVERY claim regardless of truth — the STUCK-REDUCTION failure mode. A build
that failed because the kernel never evaluated the claim attests to no
refutation, and its exit code discriminates nothing: the exact same error appears
for a TRUE claim about gold. Measured on all four original reject cases (gold
exit 1, every one by stuck reduction).

So every reject case names an explicit ``witness_reference``: the loop-free
correct impl ``return Except.ok (viewAll fields)`` (``_M_DIRECT``, also carried as
the pos-control-direct positive). Its ``…Exec`` DOES reduce, so the same witness
against it fails with

    Tactic `decide` proved that the proposition ... is false

— a SEMANTIC refutation of the concrete claim, which is the evidence the gate's
second half is supposed to collect. This is sound for the reason the gate states:
an impl the verifier ACCEPTS cannot violate its own spec, so a genuine "the spec
is violated at this input" statement must fail there; and the gate independently
checks the reference shares the frozen spec and verifies before trusting it.
Naming it explicitly (rather than leaning on the gate's stuck-reduction fallback
search) makes the recorded ``witness_subject`` deterministic.

No witness binds a hypothesis (every input is a concrete ``FieldDef`` literal
that decides C1), so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque). Every witness was rebuilt with
``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0), and FAILS
against the reference impl (exit 1) by ``decide`` proving the claim FALSE.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares no consumed
``axiom`` and no deep-model reference (mapping.md §3: the relational test and the
canonicalized kwargs are FREE inputs, R not A, checked by G-CONF; the removal is
modeled DEEPLY as ``dropTarget``, an A-reference to no library callee). The
nagini sibling's three axiom-soundness/containment probes over the real Python
primitives are G-AX's job (axiom_check.py / mapping.md), and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15104"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let mut result : List (List (String × Int)) := []\n"
    "    let mut i := fields.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
    "      invariant result = viewAll (fields.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let f := fields[i - 1]!\n"
    "      result := fieldView f :: result\n"
    "      i := i - 1\n"
    "    return Except.ok result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct fieldDefsIgnoringRelationTargets by\n"
    "  loom_solve\n"
    "  rw [viewAll_drop_step fields i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for loop-free correct reshapes,
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble + builder. C1's carrier is transparent, so a witness
# ---- extracts the executable program and refutes C1 directly on the
# ---- transparent `viewAll`. Each rival is loop-free so its `…Exec` reduces
# ---- under `decide`; gold's `while`-loop `…Exec` stays stuck. The `Except`
# ---- result carrier needs a decidable equality the extractor does not
# ---- synthesize, so each witness derives the instance first (an instance, NOT
# ---- an assumption: no axiom/sorry/native_decide, and it is appended to BOTH
# ---- files, so gold still rejects the witness). Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_PRELUDE = (
    "extract_program_for fieldDefsIgnoringRelationTargets\n"
    "deriving instance DecidableEq for Except\n\n"
)


def _witness(inp):
    return (
        _PRELUDE +
        "example :\n"
        "    (match fieldDefsIgnoringRelationTargetsExec "
        f"({inp}) with | DivM.res r => r | _ => Except.error ())\n"
        f"     ≠ Except.ok (viewAll ({inp})) := by\n"
        "  decide\n"
    )


# ---- The loop-free CORRECT impl, carried BOTH as the pos-control-direct
# ---- positive AND as the explicit `witness_reference` every reject case names.
# ---- AUDIT REPAIR (see footer, WITNESS SUBJECT): the frozen impl CANNOT serve
# ---- as the witnesses' second subject. Its `…Exec` is the backward `while`
# ---- fold, which the kernel does not reduce, so a `decide` against it is STUCK
# ---- ("did not reduce to `isTrue` or `isFalse`") for EVERY claim regardless of
# ---- truth — an exit code that discriminates nothing. Measured on all four
# ---- reject cases. Against THIS impl the same `decide` genuinely evaluates and
# ---- reports "proved that the proposition ... is false" — a SEMANTIC refutation
# ---- of the concrete claim. So each reject case names it explicitly rather than
# ---- leaning on the gate's stuck-reduction fallback, which makes the recorded
# ---- witness_subject deterministic instead of a search order. The gate checks
# ---- the reference shares the frozen spec and VERIFIES before trusting it.
_M_DIRECT = _impl_reproved(
    "    return Except.ok (viewAll fields)",
    "prove_correct fieldDefsIgnoringRelationTargets by\n  loom_solve")


# Concrete `FieldDef` literals used by the witnesses. Each exercises a distinct
# (relational, kwargs-shape) point of C1.
#   _F_NONREL_TO : a NON-relational field carrying a "to" binding — its "to" must
#                  SURVIVE (attacked by the unconditional-drop rival).
#   _F_REL_TO    : a relational field carrying a "to" binding — its "to" must be
#                  ELIDED (attacked by the never-drop rival).
#   _F_REL_TO_X  : a relational field carrying "to" AND a second binding "x" —
#                  only "to" is elided, "x" preserved (attacked by drop-extra).
#   _F_REL_NOTO  : a relational field carrying NO "to" binding — must still
#                  SUCCEED (attacked by the prepatch failure rival).
_F_NONREL_TO = '{ relational := false, kwargs := [("to", (1:Int))] }'
_F_REL_TO = '{ relational := true, kwargs := [("to", (1:Int))] }'
_F_REL_TO_X = '{ relational := true, kwargs := [("to", (1:Int)), ("x", (2:Int))] }'
_F_REL_NOTO = '{ relational := true, kwargs := [("x", (2:Int))] }'

# AUDIT ADDITION — a TWO-field input whose two per-field views DIFFER, so the
# ORDER of the assembled list is observable. Every other witness in this battery
# uses a single-element list, at which C1's "in order, for the whole list" aspect
# is unfalsifiable (a one-element list is its own reverse). Used by
# rival-order-reversed.
_F_TWO_ORDERED = f"{_F_REL_TO}, {{ relational := false, kwargs := [(\"x\", (2:Int))] }}"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole comparison view DIRECTLY via the transparent
        # fold, no per-field loop. C1 is literally `out = Except.ok (viewAll
        # fields)`, so this is the cheapest HONEST correct impl — and, since
        # `viewAll fields` is GROUNDED in the argument (not an opaque answer key),
        # it doubles as proof the spec is not echo-vulnerable (any impl that
        # mishandles the relational fork, drops a non-target binding, or reports
        # failure fails `out = Except.ok (viewAll fields)`). The loop is gone, so
        # the frozen proof's backward-fold step is unneeded and the residual goal
        # closes under `loom_solve` alone.
        "module": _M_DIRECT,
        "rationale": (
            "the post-image `Except.ok (viewAll fields)` is GROUNDED in the input "
            "(a total front-recursive fold over the method's own argument, no "
            "opaque answer key), so `return Except.ok (viewAll fields)` is the "
            "honest cheapest CORRECT impl; C1 is literally `out = Except.ok "
            "(viewAll fields)`, so it MUST verify, else C1 is SPEC-TOO-STRONG. "
            "Ports the nagini pos-branch-reorder / echo-attempt spirit: the "
            "cheapest impl satisfying the grounded pin, showing the spec is not "
            "echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-local-view",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-field
        # comparison view to a typed local `v` before prepending it. Same value
        # flow (`v = fieldView f`), different control shape; the frozen proof
        # still closes unchanged (the loop invariant and step lemma are
        # untouched).
        "module": _impl(
            "    let mut result : List (List (String × Int)) := []\n"
            "    let mut i := fields.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
            "      invariant result = viewAll (fields.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let f := fields[i - 1]!\n"
            "      let v := fieldView f\n"
            "      result := v :: result\n"
            "      i := i - 1\n"
            "    return Except.ok result"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the per-field "
            "comparison view to a typed local before prepending it) must verify; "
            "the value flow is unchanged (`v = fieldView f`) so C1 still "
            "discharges and the frozen loop proof closes as-is. Ports the nagini "
            "pos-local-reshape: if it fails => SPEC-TOO-STRONG (over-fit to the "
            "inline-prepend code form)."
        ),
    },
    {
        # AUDIT REPAIR — RESTORED. The port DROPPED this case (as
        # "pos-guard-present") claiming its residual goal "needs a NEW
        # filter-idempotence lemma that `loom_solve`/`simp_all` do not close" and
        # that landing it would require weakening the obligation. That is a
        # TOOLING claim, and it is wrong: the goal is closable INSIDE the elided
        # `prove_correct` tactic body, with no helper lemma, no new `theorem`, and
        # no change to the obligation — by list induction plus
        # `List.filter_eq_self` on the guard's negative branch. Built and it
        # elaborates (exit 0). A dropped positive is a real coverage gap here,
        # because this is the ONLY case that exercises the removal MECHANISM
        # rather than its result: it drops the target binding via a
        # present-only narrow removal, which is behaviourally correct precisely
        # BECAUSE eliding an absent binding is a no-op.
        "id": "pos-guard-present",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    return Except.ok (fields.map (fun f => if f.relational then "
            "(if f.kwargs.any (fun p => p.1 == targetKey) then dropTarget f.kwargs "
            "else f.kwargs) else f.kwargs))",
            "prove_correct fieldDefsIgnoringRelationTargets by\n"
            "  loom_solve\n"
            "  congr 1\n"
            "  induction fields with\n"
            "  | nil => rfl\n"
            "  | cons f fs ih =>\n"
            "    rw [List.map_cons, viewAll_cons, ih]\n"
            "    congr 1\n"
            "    by_cases hr : f.relational = true\n"
            "    · simp only [hr, if_true, fieldView]\n"
            "      by_cases hx : (f.kwargs.any fun p => p.1 == targetKey) = true\n"
            "      · simp [hx]\n"
            "      · simp only [hx, if_false, Bool.false_eq_true, dropTarget]\n"
            "        symm\n"
            "        rw [List.filter_eq_self]\n"
            "        simp only [List.any_eq_true, not_exists] at hx\n"
            "        intro p hp\n"
            "        simp only [bne_iff_ne, ne_eq]\n"
            "        intro he\n"
            "        exact hx p ⟨hp, by simp [he]⟩\n"
            "    · simp only [Bool.not_eq_true] at hr\n"
            "      simp [hr, fieldView]"),
        "rationale": (
            "PARTIAL-DOMAIN TRAP carried as a POSITIVE: on a relational field, "
            "elide the relation-target binding only when it is PRESENT (a narrow "
            "present-only removal), else carry the field unchanged. This is "
            "BEHAVIOURALLY CORRECT — on the `\"to\"`-absent relational shape, "
            "carrying the field unchanged already equals `dropTarget f.kwargs`, "
            "since eliding an absent binding is a no-op — so it MUST verify. It is "
            "the only case that documents that C1 constrains the RESULT, not the "
            "MECHANISM of removal: a rival must not be rejected merely for "
            "guarding its removal. Ports the nagini pos-guard-present. If it "
            "FAILS => SPEC-TOO-STRONG (over-fit to the unconditional-removal form, "
            "which would wrongly reject a faithful guarded real patch)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-reads. That case established
    # that the read-only fractional half-permission `Acc(dict_pred(kwargs),1/2)`
    # admits the membership observation a normal F2P-shaped input needs. This
    # method carries NO `require` clause (the pre-conditions region is empty) and
    # no heap permission, so the classic "the precondition admits a normal input"
    # probe is vacuous. Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is jointly SATISFIABLE by a gold-shaped
    # computation. The frozen impl discharging the ensures IS that witness. MUST
    # verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the routine is total over every "
            "field collection; the gold impl discharging the ensures is the "
            "admissibility witness that the post-image `out = Except.ok (viewAll "
            "fields)` is satisfiable (the success constructor is reachable for "
            "every input, including a relational field lacking `\"to\"`). "
            "Near-trivial precisely because the precondition is empty. Re-aimed "
            "from the nagini admiss-reads, whose read-only fractional-permission "
            "half has no counterpart on this referentially-transparent, "
            "precondition-free carrier. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = Except.ok
    # (viewAll fields)`); the input binder `fields` is varied across the
    # `relational` split and the `kwargs` shape.
    # =====================================================================
    {
        "id": "rival-always-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW (R−): elide the "to" binding UNCONDITIONALLY, ignoring the
        # relational fork (map dropTarget over every field). Correct on the
        # relational arm but on a NON-relational field it strips "to" too.
        "module": _impl(
            "    return Except.ok (fields.map (fun f => dropTarget f.kwargs))"),
        "refinement": (
            "eliding the relation-target binding UNCONDITIONALLY is a real patch "
            "that placed the removal OUTSIDE the relational guard, so it strips "
            "the target binding from non-relational fields' canonicalized "
            "bindings too. A non-relational field could legitimately carry a "
            "binding the comparison must preserve; stripping a binding the "
            "comparison relies on for non-relational fields corrupts rename "
            "detection for those fields and breaks the P2P deconstruction-equality "
            "tests, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = Except.ok (viewAll fields)`) on the "
            "NON-RELATIONAL ARM (R−): `fieldView` carries a non-relational field "
            "UNCHANGED, so a rival that elides `\"to\"` from it diverges from the "
            "post-image whenever a non-relational field carries `\"to\"`. Refuted "
            "at a single NON-relational field carrying `\"to\"`. If it verified => "
            "SPEC-TOO-WEAK (the non-relational arm is unpinned)."
        ),
        "witness": _witness(f"[{_F_NONREL_TO}]"),
        "witness_reference": _M_DIRECT,
    },
    {
        "id": "rival-never-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW (R+, the dual): carry EVERY field unchanged (never elide),
        # the "deleted the removal line" rival. Correct on the non-relational arm
        # but on a relational field it KEEPS "to".
        "module": _impl(
            "    return Except.ok (fields.map (fun f => f.kwargs))"),
        "refinement": (
            "carrying every field unchanged is the 'deleted the removal line' "
            "rival — its faithful real patch simply OMITS the target-binding "
            "removal. On a relational field carrying the target binding it keeps "
            "it, so two relational fields pointing at DIFFERENT targets no longer "
            "compare equal in the comparison view; rename detection then fails to "
            "detect a renamed model used in a relation, failing the renamed-model "
            "P2P tests. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = Except.ok (viewAll fields)`) on the RELATIONAL "
            "ARM (R+): `fieldView` elides `\"to\"` from a relational field, so a "
            "rival that carries it unchanged diverges from the post-image whenever "
            "a relational field carries `\"to\"`. Refuted at a single relational "
            "field carrying `\"to\"` — a DISTINCT point from rival-always-drop "
            "(which flips `relational` to false), varying the `relational` binder "
            "across both branch directions. If it verified => SPEC-TOO-WEAK (the "
            "relational arm's removal is unpinned)."
        ),
        "witness": _witness(f"[{_F_REL_TO}]"),
        "witness_reference": _M_DIRECT,
    },
    {
        "id": "rival-drop-extra",
        "kind": "uniqueness",
        "expect": "reject",
        # COLLATERAL LOSS (C): on a relational field elide "to" AND a second,
        # NON-target binding "x". On a relational field carrying "x", that binding
        # is LOST.
        "module": _impl(
            "    return Except.ok (fields.map (fun f => "
            "if f.relational then (dropTarget f.kwargs).filter (fun p => p.1 != \"x\") "
            "else f.kwargs))"),
        "refinement": (
            "eliding a second, non-target binding is a real patch that removes one "
            "binding too many — stripping an attribute the comparison must keep. "
            "Two relational fields that differ ONLY in that second binding would "
            "then wrongly compare equal, mis-detecting a rename and producing the "
            "wrong migration; it breaks the relation-rename P2P tests. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = Except.ok (viewAll fields)`) on NO COLLATERAL "
            "LOSS (C): `dropTarget` elides ONLY the `\"to\"` binding, so a rival "
            "that also removes a second binding diverges from the post-image on "
            "any relational field carrying that binding. Refuted at a relational "
            "field carrying both `\"to\"` and `\"x\"` — a distinct point (a "
            "two-binding relational field) that abuses the kwargs shape rather "
            "than the relational fork. Pins that ONLY the target binding is "
            "elided. If it verified => SPEC-TOO-WEAK (collateral loss admitted)."
        ),
        "witness": _witness(f"[{_F_REL_TO_X}]"),
        "witness_reference": _M_DIRECT,
    },
    {
        "id": "rival-prepatch-fail",
        "kind": "uniqueness",
        "expect": "reject",
        # DEFINEDNESS (D) — the PRE-PATCH bug. Report FAILURE (Except.error) when
        # a relational field carries no "to" binding, else the correct view. This
        # is the pre-change removal (Solution_prepatch.lean's skeleton): the
        # target-binding removal REQUIRES the binding present and signals failure
        # when it is absent — the reported KeyError shape.
        "module": _impl(
            "    return (if fields.any (fun f => f.relational && "
            "!(f.kwargs.any (fun p => p.1 == targetKey))) "
            "then Except.error () else Except.ok (viewAll fields))"),
        "refinement": (
            "this IS the pre-change behaviour: the relation-target elision is an "
            "UNCONDITIONAL removal that REQUIRES the target binding present and "
            "signals failure (raises) when it is absent. A relational field "
            "carrying no explicit target binding — the reported issue (a custom "
            "foreign key that hardcodes its target and removes it from its own "
            "canonicalized bindings) — therefore makes the routine fail instead of "
            "yielding its remaining bindings. Its faithful real patch is the "
            "unpatched repo line, which raises on exactly that shape; the failing "
            "test builds precisely that field and expects the autodetector to NOT "
            "crash, so it stays FAILING and does NOT resolve — the precise change "
            "the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECT from C1 (`out = Except.ok (viewAll fields)`) on DEFINEDNESS "
            "(D): the clause pins the SUCCESS constructor `Except.ok` for EVERY "
            "input, and this rival returns the failure constructor `Except.error` "
            "on a relational field lacking `\"to\"`, so `out ≠ Except.ok (viewAll "
            "fields)` there. Refuted at a relational field whose kwargs OMIT "
            "`\"to\"` — a distinct point from rival-never-drop (relational WITH "
            "`\"to\"`), the `\"to\"`-absent sub-domain that is exactly the "
            "reported bug. If it verified => SPEC-TOO-WEAK (the totality the "
            "change introduces is not enforced — the spec would admit the crashing "
            "pre-change removal)."
        ),
        "witness": _witness(f"[{_F_REL_NOTO}]"),
        "witness_reference": _M_DIRECT,
    },
    {
        # AUDIT ADDITION — ORDER (the unattacked half of C1). Every pre-existing
        # rival is refuted at a SINGLE-field input, at which C1's "in order, for
        # the whole list" aspect is unfalsifiable: a one-element list is its own
        # reverse, and a per-field-correct impl that assembles the collection
        # BACKWARDS agrees with the post-image on every one-element input. This
        # rival computes the per-field view CORRECTLY for every field and gets
        # only the assembly order wrong, so it is refutable only at a multi-field
        # input whose per-field views differ — the point no other witness reaches.
        "id": "rival-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_reproved(
            "    return Except.ok ((fields.map fieldView).reverse)",
            "prove_correct fieldDefsIgnoringRelationTargets by\n  loom_solve"),
        "refinement": (
            "assembling the comparison views in REVERSE is a real patch that "
            "prepends each per-field view to the accumulator while walking the "
            "collection FORWARDS (the classic accumulate-and-forget-to-reverse "
            "slip). Every per-field view is correct, but the assembled collection "
            "is ordered backwards. The comparison view is consumed POSITIONALLY — "
            "field i of one model's view is compared against field i of the "
            "other's — so a reversed collection mis-aligns every field against a "
            "different field for any model with two or more fields, making "
            "unrelated fields compare as changed and identical ones as differing. "
            "Rename detection then produces spurious and wrong migrations, "
            "breaking the multi-field comparison tests. Does NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = Except.ok (viewAll fields)`) on ORDER: "
            "`viewAll` is front-recursive, so the post-image pins the per-field "
            "views in the SAME order as the input collection, and a rival that "
            "reverses the assembly diverges from it on any collection whose "
            "per-field views are not palindromic. Refuted at a TWO-field input "
            "(a relational field carrying `\"to\"` followed by a non-relational "
            "field carrying `\"x\"`), whose two views differ — the first "
            "multi-field point in this battery, and the only one at which order "
            "is observable at all. If it verified => SPEC-TOO-WEAK (C1 would pin "
            "the MULTISET of per-field views rather than the ordered collection, "
            "admitting an impl that scrambles the comparison view's alignment)."
        ),
        "witness": _witness(f"[{_F_TWO_ORDERED}]"),
        "witness_reference": _M_DIRECT,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                 -> here                        disposition
#   -----------------------------------------------------------------------
#   pos-branch-reorder          -> pos-control-direct          RE-EXPRESSED
#   pos-local-reshape           -> pos-control-local-view      PORTED
#   pos-guard-present           -> pos-guard-present           PORTED (restored)
#   admiss-reads                -> admiss-gold-total            RE-AIMED
#   rival-frame-mutate-input    -> (none)                      VACUOUS
#   rival-prepatch-del          -> rival-prepatch-fail         PORTED
#   rival-always-drop           -> rival-always-drop           PORTED
#   rival-never-drop            -> rival-never-drop            PORTED
#   rival-drop-extra-key        -> rival-drop-extra            PORTED
#   (no nagini source)          -> rival-order-reversed        AUDIT ADDITION
#   AXIOM_TESTS (3)             -> (none)                      DROPPED (G-AX lane)
#
# 9 velvet SPEC cases: 3 soundness, 1 admissibility, 5 uniqueness. EVERY nagini
# SPEC case that is expressible on this carrier is now ported (the only nagini
# omission is rival-frame-mutate-input, vacuous for want of a heap), and the
# reject lane carries one rival with no nagini counterpart, aimed at the ORDER
# aspect of C1 that the whole-list carrier introduces and the per-field nagini
# carrier could not have.
#
# CARRIER NARROWING. The nagini sibling models the PER-FIELD body
#   `reduce_to_relation_agnostic(kwargs, is_relation)` on a `Dict[int,int]`
#   carrier under a fractional heap permission, with the relational fork exposed
#   IN the impl region (`if is_relation: ...`). This bundle models the WHOLE
#   routine `fieldDefsIgnoringRelationTargets (fields : List FieldDef)` — the
#   relational fork lives in the PURE `fieldView` def, and the impl region is a
#   backward `while` fold assembling the per-field views. So the nagini per-field
#   control-flow rivals become per-field VALUE rivals over the whole-list carrier,
#   each a loop-free `fields.map`/`fields.any` refuted at a single-field input.
#   The whole-list carrier also ADDS an aspect the per-field nagini carrier does
#   not have — the ORDER of the assembled collection — which is why the reject
#   lane carries one rival (rival-order-reversed) with no nagini counterpart.
# RE-EXPRESSED (pos-branch-reorder -> pos-control-direct): the nagini positive
#   swaps the source order of the two mutually-exclusive relational arms IN the
#   impl. On this carrier the fork is in the pure `fieldView`, not the impl, so
#   there is no impl-region branch to reorder; the cheapest structurally-different
#   correct impl is `return Except.ok (viewAll fields)` — the same argument (the
#   grounded pin is satisfiable only by the real per-field elision; no wrong echo
#   verifies) expressed as a loop-free correct impl.
# PORTED (1 positive, pos-local-reshape -> pos-control-local-view): the nagini
#   positive binds the relation-agnostic result to a typed local before returning;
#   here the analogue binds the per-field view `v := fieldView f` in the loop body
#   before prepending. Same value flow, different control shape; the frozen loop
#   proof closes unchanged.
# PORTED, RESTORED BY AUDIT (pos-guard-present): the nagini partial-domain-trap
#   POSITIVE (drop the target only when present, via a narrow present-only
#   removal, else carry unchanged — behaviourally CORRECT). An earlier revision
#   DROPPED it, claiming its residual goal "needs a NEW filter-idempotence lemma
#   (`¬ kw.any (·.1 = "to") → dropTarget kw = kw`) that `loom_solve`/`simp_all`
#   do not close" and that the guide forbids adding a helper lemma to land a
#   positive. The premise was true and the conclusion did not follow: the fact IS
#   needed, but it does not need to be a NEW top-level lemma — it is provable
#   INLINE inside the elided `prove_correct` tactic body, where `variant_scope`
#   permits arbitrary tactics, by list induction plus `List.filter_eq_self` on the
#   guard's negative branch. No helper lemma, no new `theorem`/`lemma`, no
#   weakened obligation, byte-identical spec view. Rebuilt: exit 0. This was a
#   TOOLING claim, not a carrier limit, so the drop was a real coverage gap — and
#   the gap mattered, because this is the ONLY case that pins that C1 constrains
#   the RESULT of the elision rather than its MECHANISM. pos-control-direct does
#   NOT cover that: it delegates wholesale to `viewAll`, so it never exhibits a
#   removal guarded on the binding's presence, which is the shape a faithful real
#   patch could plausibly take and which the spec must therefore not reject.
# RE-AIMED (admiss-reads -> admiss-gold-total): the nagini case establishes the
#   fractional half-permission admits a normal input's membership read. This
#   method has NO `require` and no heap permission, so that probe is degenerate
#   (every input is in-domain); re-aimed at the residual total-domain risk
#   (post-image joint satisfiability, incl. that the success constructor is
#   reachable on the `\"to\"`-absent relational shape), witnessed by the frozen
#   impl discharging the ensures. Near-trivial by construction, and recorded as
#   such: its module IS the frozen file, so it re-attests G-VERIFY rather than
#   probing an independent property. It is kept because a precondition-free
#   method still owes the satisfiability check, not because it is a strong case.
# VACUOUS (rival-frame-mutate-input): MANDATORY on nagini because `kwargs` is held
#   at `Acc(dict_pred(kwargs),1/2)` read-only and a write-back must be rejected for
#   insufficient permission. Lean/Velvet are referentially transparent: `fields`
#   is an immutable value, no `mut` binder, no heap, no aliasing, no permission
#   system. There is no read-only input to overwrite. No substitute fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the nagini file's three axiom-soundness/containment
#   probes over the real Python primitives (dict.pop / del) are G-AX's job. This
#   bundle declares no consumed axiom and no deep-model reference (mapping.md §3:
#   the relational test and canonicalized kwargs are FREE inputs, the removal is
#   modeled deeply as `dropTarget`); the G-PBT gate ignores AXIOM_TESTS anyway.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause is C1
#   (`out = Except.ok (viewAll fields)`), pinning FOUR independent things, each
#   attacked:
#     * DEFINEDNESS (D, the success constructor on EVERY input incl. the
#         `\"to\"`-absent relational shape): rival-prepatch-fail.
#     * RELATIONAL ARM (R+, a relational field's `\"to\"` is elided):
#         rival-never-drop.
#     * NON-RELATIONAL ARM (R−, a non-relational field is carried unchanged):
#         rival-always-drop.
#     * NO COLLATERAL LOSS (C, only `\"to\"` is elided): rival-drop-extra.
#     * ORDER (O, the views appear in the input collection's order):
#         rival-order-reversed (the only multi-field point).
#   The sole input binder `fields` is varied across FIVE distinct points:
#     [nonrel field with "to"]        — relational=false, "to" present;
#     [rel field with "to"]           — relational=true,  "to" present;
#     [rel field with "to" and "x"]   — relational=true,  two bindings;
#     [rel field with no "to"]        — relational=true,  "to" absent;
#     [rel-with-"to", nonrel-with-"x"] — TWO fields, differing views (order).
#   Both values of the `relational` binder are exercised, and the `kwargs` binder
#   is varied across "to"-present / "to"-absent / extra-binding shapes, and the
#   collection LENGTH across one and two fields. No binder value is held fixed by
#   every witness. All three positives and the admissibility case defend C1 (all
#   discharge on gold).
#
# WITNESS MECHANICS: C1's carrier is transparent (`viewAll`/`fieldView`/
#   `dropTarget`/`FieldDef` concrete, `axioms` region empty). Every witness
#   extracts the executable program and refutes C1 directly against `viewAll`:
#   each rival is loop-free (`fields.map`/`fields.any`) so its `…Exec` reduces
#   under `decide`. Gold's backward-`while` `…Exec` does NOT reduce, so a `decide`
#   against gold is STUCK for every claim regardless of truth and discriminates
#   nothing — which is why every reject case names an explicit `witness_reference`
#   (the loop-free correct `_M_DIRECT`) as the refutation subject instead. See
#   WITNESS SUBJECT in the module docstring. The `Except` result carrier's
#   `DecidableEq` is derived inside the witness (an instance appended to both
#   files, no axiom/sorry/native_decide), so the reference still rejects it. No
#   witness binds a hypothesis, so no consistency probe is needed. All five
#   rebuilt with scripts/lean_verify.sh: rival build exit 0, reference build exit
#   1 with `decide` proving the claim FALSE (a semantic refutation).
AXIOM_TESTS = []
