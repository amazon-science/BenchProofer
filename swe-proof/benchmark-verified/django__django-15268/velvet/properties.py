"""properties.py — G-PBT falsification battery for django__django-15268 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside a
``-- impl-start`` / ``-- impl-end`` region — which the consumer spec view elides
— is changed, so ``markers.same_spec`` holds and every ``prove_correct <name>``
obligation survives with a byte-identical header) and swaps in a candidate
implementation, checked by the real verifier. ``expect="verify"`` passes iff
(in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (three contracted methods; the last calls the first two, so the
proof of each caller applies the callee's ``_correct`` fact directly):

  reorderableBase (selfName : Nat) (other : OtherOp) return (result : Bool)
    ensures result = (!affectsModel selfName other)                    [B]

  reorderableTogether (selfName : Nat) (selfKind : TogetherKind)
                      (other : OtherOp) return (result : Bool)
    ensures result = ((!affectsModel selfName other) ||
                      (isTogetherOp other && !sameKind selfKind other)) [T]

  optimizeAgainst (selfName : Nat) (selfKind : TogetherKind)
                  (other : OtherOp) return (result : OptimizeOutcome)
    ensures result = (if mergeable selfName selfKind other then .merge
                      else if ((!affectsModel selfName other) ||
                               (isTogetherOp other && !sameKind selfKind other))
                           then .reorderable else .blocked)             [O]

The load-bearing behavioural delta is the WIDENING in clause T: a specialised
independence test is independent not only of a neighbour that does not touch its
model, but ALSO of a touching neighbour that is a together-option operation of a
DIFFERENT flavour on the same model. That widening is what lets a four-step
remove/re-add sequence collapse to two operations (the F2P observable). Clause O
threads that widened test through the full three-way verdict, and clause B is
the pre-existing baseline the widening extends.

GROUNDED, NOT ECHO. Every post-image is a TRANSPARENT total ``def`` over the
method's own inputs (``affectsModel`` / ``isTogetherOp`` / ``sameKind`` /
``mergeable``, all pattern matches over the input carrier). The ``axioms`` region
is empty; ``OtherOp`` / ``TogetherKind`` / ``OptimizeOutcome`` all derive
``DecidableEq``. There is NO opaque answer-key to echo: a wrong impl cannot
verify by restating an oracle, it must reproduce the decision at every input.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's two mandatory
    frame probes (``frame-mutate-other-kind``, ``frame-mutate-between-kind``)
    write through a read-only fractional-permission reference and are rejected
    for INSUFFICIENT PERMISSION. Lean/Velvet are referentially transparent:
    ``selfName`` / ``selfKind`` / ``other`` are immutable values, no ``mut``
    binder, no heap, no aliasing, no permission system. There is no read-only
    input to overwrite and no substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack (see GROUNDED above). The nagini
    ``pos-control-ct-direct`` (``return alter_commutes_through(...)``) becomes
    the honest grounded positive controls below — the cheapest correct impls,
    which double as proof the spec is not echo-vulnerable.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, one rival per clause and
    per sub-domain the widening turns on (see the uniqueness section).
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. Every frozen impl region
    is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
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

REPROOF NOTE. Three cases (`pos-control-base-match`, `admiss-f2p-selfcall`, and
— unchanged — none of the rejects) re-derive a `prove_correct` TACTIC body via
``_reprove``. That is admissible and is not a weakening: the obligation's
STATEMENT is the ``method ... ensures`` header, which lives in the spec view and
is pinned byte-for-byte by ``markers.same_spec``, and ``variant_scope`` requires
every ``prove_correct <name>`` header to survive. Only the tactic text changes,
which is exactly what a variant that reshapes an impl legitimately needs: the
frozen ``loom_solve`` is tuned to the frozen impl's form, so a correct reshape
that ``loom_solve`` alone cannot close is a TACTIC gap, not a spec hole, and
recording it as a reject would falsely attest to spec strength. Both reproofs
were landed with real builds (exit 0).

CARRIER NOTE — refutes at CONCRETE literals (no conditioning). Every modeled
type is fully transparent and decidable, so each reject witness reaches the
method contract through Velvet's own tester machinery
(``<name>Tester args = false``) at concrete literal inputs and closes by
``decide`` — no hypothesis about an opaque term is bound, so no witness binds
anything and the gate's consistency probe is a no-op. The frozen solution
reduces under ``decide`` too; each witness FAILS against gold purely because gold
SATISFIES the spec at that input (the tester returns ``true``, so ``... = false``
is provably false). Checked in a file whose ``prove_correct`` blocks are
stripped, so no tactic script can mask the verdict. Every reject witness below
was run against BOTH the rival (elaborates, exit 0) and the frozen solution
(fails, exit 1) with two real ``lean_verify.sh`` builds.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle has NO axioms
(meta.json axioms == [], deep_model_references == []); every unchanged callee
fact is carried as a free input on ``OtherOp.generic``. G-AX is N/A and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15268"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors — each is the WHOLE frozen impl body (text strictly
# between a method's `-- impl-start` / `-- impl-end`). Each lies wholly inside
# one impl region and is unique in Solution.lean (both asserted at load below),
# so every variant's edit is confined to the elided impl region: same_spec holds
# and every `prove_correct <name>` header survives byte-identically.
# ---------------------------------------------------------------------------
_RB_IMPL = (
    "    return !affectsModel selfName other\n"
)
_RT_IMPL = (
    "    let base ← reorderableBase selfName other\n"
    "    return base || (isTogetherOp other && !sameKind selfKind other)\n"
)
_OA_IMPL = (
    "    let canReorder ← reorderableTogether selfName selfKind other\n"
    "    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge\n"
    "             else (if canReorder then OptimizeOutcome.reorderable\n"
    "                   else OptimizeOutcome.blocked)\n"
    "    return r\n"
)

for _a in (_RB_IMPL, _RT_IMPL, _OA_IMPL):
    assert _BASE.count(_a) == 1, f"impl anchor drifted from expected text: {_a!r}"


def _rb(body):
    return _swap(_BASE, _RB_IMPL, body)


def _rt(body):
    return _swap(_BASE, _RT_IMPL, body)


def _oa(body):
    return _swap(_BASE, _OA_IMPL, body)


# ---- proof-body surgery. A variant that reshapes an impl may legitimately need
# ---- to REPROVE the same obligation: `variant_scope` requires every
# ---- `prove_correct <name>` header to survive (and the `ensures` header lives in
# ---- the spec view, so `same_spec` pins the STATEMENT byte-for-byte), while the
# ---- tactic body may differ. Only the tactic text after the header is replaced,
# ---- so the obligation being discharged is unchanged; a case that needs this is
# ---- noted as such in its rationale.
def _reprove(src, name, tactics):
    old = f"prove_correct {name} by\n  loom_solve\n"
    return _swap(src, old, f"prove_correct {name} by\n{tactics}")


# ---- witness builder. Reaches a method's contract through Velvet's tester
# ---- machinery: `<name>Tester args = false` says the extracted program's result
# ---- violates that method's postcondition at the concrete input. Checked in a
# ---- file whose `prove_correct` blocks are stripped; closes by `decide` on the
# ---- transparent carrier. Binds nothing (literal inputs), so the gate's
# ---- consistency probe is a no-op.
def _witness(method, tester_call):
    return (
        f"extract_program_for {method}\n"
        f"prove_precondition_decidable_for {method}\n"
        f"prove_postcondition_decidable_for {method}\n"
        f"derive_tester_for {method}\n\n"
        f"example : {tester_call} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (each reproved by the frozen `prove_correct ... by
    # loom_solve` body, which is generic over the impl shape). If a faithful
    # correct impl cannot verify, the clause is SPEC-TOO-STRONG. Each verified
    # out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-control-base-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape of the baseline test: stage the touch-decision through a typed
        # local before negating it. Same value flow, different control shape.
        "module": _rb(
            "    let a := affectsModel selfName other\n"
            "    return !a\n"),
        "rationale": (
            "structurally different CORRECT reshape of the baseline independence "
            "test: bind the touch-decision to a local, then negate. The value flow "
            "is unchanged, so clause B still discharges and the frozen proof closes "
            "unchanged. Must verify, else clause B is SPEC-TOO-STRONG (over-fit to "
            "the inline-negation spelling). Re-expresses the nagini "
            "pos-control-ct-reshape at the baseline function."
        ),
    },
    {
        "id": "pos-control-together-direct",
        "kind": "soundness",
        "expect": "verify",
        # The specialised test written DIRECTLY as its grounded post-image over
        # the inputs, bypassing the call to the baseline method. Since the
        # post-image is grounded (not an opaque answer key), this is the honest
        # cheapest CORRECT impl and doubles as proof the spec is not
        # echo-vulnerable (any wrong decision fails clause T).
        "module": _rt(
            "    return (!affectsModel selfName other) || "
            "(isTogetherOp other && !sameKind selfKind other)\n"),
        "rationale": (
            "the post-image of clause T is GROUNDED in the inputs (a boolean over "
            "the transparent affectsModel/isTogetherOp/sameKind, no opaque answer "
            "key), so returning it directly is the honest cheapest CORRECT impl; "
            "clause T is literally that expression, so it MUST verify, else "
            "SPEC-TOO-STRONG. Re-expresses the nagini pos-control-ct-direct: the "
            "cheapest grounded impl, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-optimize-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape of the three-way verdict: split the nested if/else into an outer
        # merge branch that returns early and an inner reorderable/blocked branch,
        # rather than a single `let r := ...`. Same value flow; verifies via the
        # callee-under-spec fact for reorderableTogether.
        "module": _oa(
            "    let canReorder ← reorderableTogether selfName selfKind other\n"
            "    if mergeable selfName selfKind other then\n"
            "      return OptimizeOutcome.merge\n"
            "    else\n"
            "      return (if canReorder then OptimizeOutcome.reorderable "
            "else OptimizeOutcome.blocked)\n"),
        "rationale": (
            "structurally different CORRECT reshape of the three-way verdict: an "
            "outer merge branch with an early return and an inner reorderable/"
            "blocked branch, instead of one bound local. Same value flow, so "
            "clause O still discharges (via the reorderableTogether callee-under-"
            "spec fact) and the frozen proof closes unchanged. Must verify, else "
            "SPEC-TOO-STRONG. Re-expresses the nagini pos-control-pc-reshape at the "
            "verdict-threading function."
        ),
    },

    {
        "id": "pos-control-base-match",
        "kind": "soundness",
        "expect": "verify",
        # The baseline test written as a full MATCH over the input carrier, one
        # arm per constructor, instead of one call to the transparent decision.
        # Extensionally identical at every input; a genuinely different shape (the
        # case split is in the impl rather than inside the decision it calls).
        "module": _reprove(
            _rb(
                "    match other with\n"
                "    | OtherOp.together n _ => return !(n == selfName)\n"
                "    | OtherOp.deleteModel _ => return false\n"
                "    | OtherOp.generic r _ => return !r\n"),
            "reorderableBase",
            "  loom_solve <;> subst_vars <;> simp [affectsModel]\n"),
        "rationale": (
            "CORRECT reshape of the baseline independence test that moves the case "
            "split into the impl: one arm per constructor of the input carrier, each "
            "returning the arm's own answer, rather than one call to the transparent "
            "decision. Extensionally identical at every input, but a strictly "
            "different shape from pos-control-base-local (which keeps the single call "
            "and only stages it through a local) — so this probes clause B for "
            "over-fitting to the CALL form rather than merely to the "
            "inline-negation spelling. The `prove_correct reorderableBase` tactic "
            "body is re-derived (statement byte-identical; the frozen `loom_solve` "
            "leaves one goal per constructor arm, closed by "
            "`subst_vars <;> simp [affectsModel]`) — admissible, since a variant "
            "reproves the same obligation. Must verify, else clause B is "
            "SPEC-TOO-STRONG (over-fit to the impl's control shape)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — PORTED from the nagini admiss-selfcall, which made a SELF-CALL
    # on a fresh F2P-shaped input pair and asserted the result. Its
    # read-only-fractional-permission half has no counterpart here (no heap, no
    # `mut` binder), but the SELF-CALL half ports directly and is what makes the
    # case non-trivial: the variant calls the widened decision at the CONCRETE
    # F2P-shaped point (a together-option operation on model 7, flavour `unique`,
    # against a same-model DIFFERENT-flavour together neighbour) and threads that
    # call's result into the returned verdict. The obligation then closes only if
    # the widened decision is TRUE at that point — i.e. only if the sub-domain the
    # four-step collapse depends on is actually inhabited by the spec. So a
    # verdict-level `ensures` that held only vacuously, or a widening that the
    # spec admitted nowhere, would make this case FAIL. Ran: exit 0.
    # =====================================================================
    {
        "id": "admiss-f2p-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        # `probe` is the widened decision evaluated at the F2P-shaped point; the
        # returned verdict is `canReorder && probe`, which equals the frozen
        # verdict ONLY IF `probe` is true there. If the F2P sub-domain were empty
        # under the spec, `probe` would be false and this would not verify.
        "module": _reprove(
            _oa(
                "    let probe ← reorderableTogether 7 TogetherKind.unique\n"
                "                  (OtherOp.together 7 TogetherKind.index)\n"
                "    let canReorder ← reorderableTogether selfName selfKind other\n"
                "    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge\n"
                "             else (if canReorder && probe then OptimizeOutcome.reorderable\n"
                "                   else OptimizeOutcome.blocked)\n"
                "    return r\n"),
            "optimizeAgainst",
            "  loom_solve\n"
            "  all_goals (rw [show (!sameKind TogetherKind.unique "
            "(OtherOp.together 7 TogetherKind.index)) = true from by decide] at *)\n"
            "  all_goals simp_all [affectsModel, isTogetherOp, sameKind, mergeable]\n"),
        "rationale": (
            "no method carries a `require`, so the classic precondition-admissibility "
            "probe is vacuous; ported from the nagini admiss-selfcall via its "
            "SELF-CALL half instead. The variant evaluates the widened decision at "
            "the concrete F2P-shaped point (model 7, flavour `unique`, neighbour = a "
            "same-model DIFFERENT-flavour together operation) and conjoins that "
            "result into the returned verdict, so the verdict obligation discharges "
            "ONLY IF the widened decision is genuinely TRUE at that point. That makes "
            "the case sensitive to a spec whose widening clause is satisfiable "
            "nowhere (or whose verdict clause holds only vacuously) — either would "
            "show up as a FAILURE here, which the frozen impl alone could not detect. "
            "The `prove_correct optimizeAgainst` tactic body is re-derived (the "
            "obligation STATEMENT is byte-identical; the frozen `loom_solve` alone "
            "does not reduce the literal-flavour BEq at the probe point) — a variant "
            "reproving the same obligation is admissible by design. Else "
            "SPEC-UNSATISFIABLE / F2P-SUB-DOMAIN-EMPTY."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the F2P. Witnesses vary selfName, selfKind and
    # the OtherOp constructor across distinct points so no binder is pinned.
    # =====================================================================
    {
        "id": "weak-base-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Baseline test inverted: report reorderable exactly when the neighbour
        # DOES touch the model. Wrong at every input; refuted on a non-touching
        # together neighbour where gold reorders and this blocks.
        "module": _rb("    return affectsModel selfName other\n"),
        "refinement": (
            "an inverted baseline test would let an operation advance past exactly "
            "the neighbours that touch its model and block on the independent ones "
            "— it would reduce migrations across dependent operations and refuse to "
            "reduce independent ones, corrupting the operation list wholesale. The "
            "F2P optimizer/autodetector invariants (which depend on the baseline "
            "independence being correct) would fail, so a faithful real patch of "
            "this shape does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause B (`result = !affectsModel selfName other`): the "
            "rival returns `affectsModel ...`, the exact negation of the spec, so "
            "it diverges wherever affectsModel is decided either way. Refuted at "
            "selfName=7 against a same-model together neighbour (together 7 unique), "
            "where the neighbour touches the model so the spec forces "
            "`!affectsModel` = `!(7==7)` = `false` while the rival returns "
            "`affectsModel` = `true`. If it verified => SPEC-TOO-WEAK (the baseline "
            "decision would be unpinned)."
        ),
        "witness": _witness(
            "reorderableBase",
            "reorderableBaseTester 7 (OtherOp.together 7 TogetherKind.unique)"),
    },
    {
        "id": "weak-base-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Baseline test always reorderable: ignore the neighbour entirely. Correct
        # only on non-touching neighbours; WRONG on any touching one. Refuted on a
        # delete-model neighbour (which conservatively touches every model, so the
        # spec forces `false`), a DISTINCT binder value and OtherOp constructor
        # from weak-base-inverted.
        "module": _rb("    return true\n"),
        "refinement": (
            "a baseline test unconditionally returning reorderable would advance "
            "an operation past a delete of its own model and past every dependent "
            "neighbour — it would reorder migrations across hard dependencies, "
            "corrupting the operation list. The F2P optimizer/autodetector "
            "invariants that rely on the baseline blocking dependent operations "
            "would fail, so a faithful real patch of this shape does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause B (`result = !affectsModel selfName other`): on a "
            "delete-model neighbour `affectsModel` is conservatively `true` (a "
            "deleted model may reference any other), so the spec forces `false`, "
            "but this rival returns `true`. Refuted at selfName=4, "
            "other=deleteModel 9 — a DISTINCT input point and OtherOp constructor "
            "from weak-base-inverted (a together neighbour at selfName=7), so B's "
            "binders selfName and the `other` constructor are both varied. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "reorderableBase",
            "reorderableBaseTester 4 (OtherOp.deleteModel 9)"),
    },
    {
        "id": "weak-base-rule-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour of the specialised test: drop the different-
        # flavour widening, so it collapses to the baseline test. Correct on every
        # non-touching neighbour and on a same-flavour neighbour, but WRONG on the
        # same-model DIFFERENT-flavour case clause T newly allows.
        "module": _rt(
            "    let base ← reorderableBase selfName other\n"
            "    return base\n"),
        "refinement": (
            "this is exactly the pre-patch specialised test (== Solution_prepatch): "
            "the different-flavour widening is absent, so a together-option "
            "operation never advances past a same-model neighbour of a different "
            "flavour. The four-step remove/re-add sequence on the two flavours is "
            "then NOT reduced, and the F2P autodetector tests (which now expect the "
            "collapsed two-operation sequence) FAIL — verify-not-resolve. Ports the "
            "nagini weak-base-rule-only."
        ),
        "rationale": (
            "REJECT from clause T: on a same-model DIFFERENT-flavour neighbour "
            "(together, model 0, flavour = the OTHER of selfKind) the spec forces "
            "`true` (the widening) while base-only returns `!affectsModel` = "
            "`!(0==0)` = `false`. Refuted at selfName=0, selfKind=index, "
            "other=together 0 unique. If it verified => SPEC-TOO-WEAK (the widening "
            "would be unenforced)."
        ),
        "witness": _witness(
            "reorderableTogether",
            "reorderableTogetherTester 0 TogetherKind.index "
            "(OtherOp.together 0 TogetherKind.unique)"),
    },
    {
        "id": "weak-overpermissive-samekind",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-permissive: advance past ANY together-option neighbour, dropping
        # the different-flavour guard. Correct on a different-flavour neighbour
        # (the F2P case) but WRONG on a same-model SAME-flavour neighbour, which
        # clause T must keep blocking.
        "module": _rt(
            "    let base ← reorderableBase selfName other\n"
            "    return base || (isTogetherOp other)\n"),
        "refinement": (
            "dropping the different-flavour guard lets a together-option operation "
            "advance past a SAME-flavour neighbour on the same model. A faithful "
            "patch of this shape would reduce e.g. two same-flavour AlterTogether "
            "passes on one model that are ordering-sensitive and must NOT be "
            "commuted, corrupting the migration and failing the PASS_TO_PASS "
            "optimizer/autodetector invariants — verify-not-resolve. Ports the "
            "nagini weak-overpermissive-samefamily."
        ),
        "rationale": (
            "REJECT from clause T: on a same-model SAME-flavour together neighbour "
            "the spec forces `!affectsModel || (isTogetherOp && !sameKind)` = "
            "`false || (true && false)` = `false`, but this rival returns "
            "`false || isTogetherOp` = `true`. Refuted at selfName=1, "
            "selfKind=unique, other=together 1 unique — a DISTINCT point (same "
            "flavour) from weak-base-rule-only (different flavour), so the "
            "selfKind/other binders are varied. If it verified => SPEC-TOO-WEAK "
            "(same-flavour neighbours would wrongly reorder)."
        ),
        "witness": _witness(
            "reorderableTogether",
            "reorderableTogetherTester 1 TogetherKind.unique "
            "(OtherOp.together 1 TogetherKind.unique)"),
    },
    {
        "id": "weak-together-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Maximal over-collapse of the specialised test: always reorderable,
        # ignoring the inputs. The cheapest spec-too-weak attack. Correct only
        # where the answer is `true`; WRONG on any blocking neighbour.
        "module": _rt(
            "    let base ← reorderableBase selfName other\n"
            "    return true\n"),
        "refinement": (
            "always-reorderable is the maximal over-collapse: a specialised test "
            "unconditionally returning True would advance a together-option "
            "operation past every neighbour, including a generic operation that "
            "references the model (a real dependency) and ordering-sensitive "
            "same-flavour passes, reordering across dependencies and breaking the "
            "F2P autodetector/optimizer invariants — verify-not-resolve. Ports the "
            "nagini weak-ct-constant-true."
        ),
        "rationale": (
            "cheap supporting near-miss (constant). REJECT from clause T: on a "
            "generic neighbour that touches the model (refsSelf=true) and is not a "
            "together-op, the spec forces `!true || (false && ...)` = `false`, but "
            "this returns `true`. Refuted at selfName=2, selfKind=index, "
            "other=generic true false — a THIRD OtherOp constructor (generic, not "
            "together), so the `other` binder is varied across all three arms. If "
            "it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "reorderableTogether",
            "reorderableTogetherTester 2 TogetherKind.index "
            "(OtherOp.generic true false)"),
    },
    {
        "id": "weak-optimize-no-merge",
        "kind": "uniqueness",
        "expect": "reject",
        # The three-way verdict drops the merge branch: report reorderable/blocked
        # from the independence test alone, never merge. Correct wherever the pair
        # does not collapse, but WRONG on a same-model same-flavour together
        # neighbour, which must merge (collapse to one operation).
        "module": _oa(
            "    let canReorder ← reorderableTogether selfName selfKind other\n"
            "    return (if canReorder then OptimizeOutcome.reorderable "
            "else OptimizeOutcome.blocked)\n"),
        "refinement": (
            "dropping the merge branch means a together-option operation never "
            "collapses with a same-flavour neighbour (or a delete) on its model "
            "into a single operation; it would at best be blocked. A faithful patch "
            "of this shape would leave the redundant remove/re-add pair as two "
            "operations where the optimizer must fuse them to one, so the F2P "
            "collapse observable is not produced — verify-not-resolve. Re-expresses "
            "the merge-branch coverage the nagini pair-collapse rivals exercise."
        ),
        "rationale": (
            "REJECT from clause O: on a same-model SAME-flavour together neighbour "
            "`mergeable` is true, so the spec forces `.merge`, but this rival "
            "(dropping the merge branch) returns `.blocked` (canReorder is false "
            "there). Refuted at selfName=5, selfKind=index, other=together 5 index. "
            "If it verified => SPEC-TOO-WEAK (the collapse-to-one verdict would be "
            "unpinned)."
        ),
        "witness": _witness(
            "optimizeAgainst",
            "optimizeAgainstTester 5 TogetherKind.index "
            "(OtherOp.together 5 TogetherKind.index)"),
    },
    {
        "id": "weak-optimize-reorder-baseonly",
        "kind": "uniqueness",
        "expect": "reject",
        # The three-way verdict threads the BASELINE independence test into the
        # reorderable branch instead of the specialised (widened) one. This is the
        # pre-patch verdict at the top level: merge branch intact, but the
        # different-flavour widening is absent from the reorderable test.
        "module": _oa(
            "    let canReorder ← reorderableTogether selfName selfKind other\n"
            "    let r := if mergeable selfName selfKind other then OptimizeOutcome.merge\n"
            "             else (if (!affectsModel selfName other) then OptimizeOutcome.reorderable\n"
            "                   else OptimizeOutcome.blocked)\n"
            "    return r\n"),
        "refinement": (
            "threading the baseline test (not the widened specialised test) into "
            "the reorderable branch reproduces the pre-patch top-level verdict: a "
            "together-option operation is blocked against a same-model different-"
            "flavour neighbour instead of reorderable. The four-step sequence is "
            "then not collapsed and the F2P autodetector tests FAIL — "
            "verify-not-resolve. This is the top-level manifestation of the same "
            "widening the nagini weak-base-rule-only attacks at the decision "
            "function."
        ),
        "rationale": (
            "REJECT from clause O: on a same-model DIFFERENT-flavour together "
            "neighbour, `mergeable` is false (different flavour) and the spec's "
            "reorderable test is `!affectsModel || (isTogetherOp && !sameKind)` = "
            "`false || (true && true)` = `true` => `.reorderable`, but this rival's "
            "baseline-only test `!affectsModel` = `false` => `.blocked`. Refuted at "
            "selfName=3, selfKind=unique, other=together 3 index. If it verified => "
            "SPEC-TOO-WEAK (the widening would be unenforced at the verdict level)."
        ),
        "witness": _witness(
            "optimizeAgainst",
            "optimizeAgainstTester 3 TogetherKind.unique "
            "(OtherOp.together 3 TogetherKind.index)"),
    },
    {
        "id": "weak-optimize-merge-drops-elidable",
        "kind": "uniqueness",
        "expect": "reject",
        # The merge branch keeps its together/delete arms but DENIES the collapse
        # for an elidable generic neighbour: the pair-collapses-because-the-
        # neighbour-may-be-silently-dropped arm of `mergeable`, which no other
        # rival touches (every existing merge attack lands on a together or a
        # delete). Correct on every non-generic neighbour and on a non-elidable
        # generic; WRONG exactly on an elidable one.
        "module": _oa(
            "    let canReorder ← reorderableTogether selfName selfKind other\n"
            "    let m := match other with\n"
            "             | OtherOp.generic _ _ => false\n"
            "             | o => mergeable selfName selfKind o\n"
            "    let r := if m then OptimizeOutcome.merge\n"
            "             else (if canReorder then OptimizeOutcome.reorderable\n"
            "                   else OptimizeOutcome.blocked)\n"
            "    return r\n"),
        "refinement": (
            "denying the collapse for an elidable neighbour means a pair whose "
            "neighbour the optimizer is entitled to drop silently stays two "
            "operations instead of one. A faithful patch of this shape would leave "
            "an elidable neighbour in place and, worse, report the pair BLOCKED "
            "wherever that neighbour also touches the model — under-reducing "
            "sequences the optimizer is required to reduce and failing the "
            "PASS_TO_PASS optimizer invariants. Verify-not-resolve. Attacks the arm "
            "of the collapse decision the ported nagini rivals leave untouched."
        ),
        "rationale": (
            "REJECT from clause O's merge branch: on a generic neighbour that is "
            "marked elidable, `mergeable` is `true` (the neighbour may be dropped, "
            "collapsing the pair to my operation alone), so the spec forces "
            "`.merge`; this rival forces the generic arm to `false` and, since the "
            "neighbour also touches the model here, returns `.blocked`. Refuted at "
            "selfName=6, selfKind=unique, other=generic true true — the "
            "elidable-generic point, which no other reject case reaches. If it "
            "verified => SPEC-TOO-WEAK (the elidable-collapse arm would be "
            "unpinned)."
        ),
        "witness": _witness(
            "optimizeAgainst",
            "optimizeAgainstTester 6 TogetherKind.unique "
            "(OtherOp.generic true true)"),
    },
    {
        "id": "weak-optimize-merge-delete-anyname",
        "kind": "uniqueness",
        "expect": "reject",
        # The merge branch drops the model-identity check on its delete arm:
        # collapse with a delete of ANY model, not just mine. This is the exact
        # asymmetry the carrier makes subtle — the reorder test treats a delete as
        # touching EVERY model, while the collapse decision keys on identity — so a
        # rival that conflates the two is correct on a delete of MY model and wrong
        # on a delete of any other. No existing rival varies the delete's name.
        "module": _oa(
            "    let canReorder ← reorderableTogether selfName selfKind other\n"
            "    let m := match other with\n"
            "             | OtherOp.deleteModel _ => true\n"
            "             | o => mergeable selfName selfKind o\n"
            "    let r := if m then OptimizeOutcome.merge\n"
            "             else (if canReorder then OptimizeOutcome.reorderable\n"
            "                   else OptimizeOutcome.blocked)\n"
            "    return r\n"),
        "refinement": (
            "collapsing with a delete of an UNRELATED model discards an operation "
            "that must survive: the two operations concern different models, so the "
            "pair does not reduce to one at all (it is a hard boundary — a deleted "
            "model may reference any other through its relations). A faithful patch "
            "of this shape would silently drop or supersede operations across "
            "unrelated models, corrupting the migration and failing the PASS_TO_PASS "
            "optimizer invariants. Verify-not-resolve. Probes the identity check the "
            "collapse decision keeps but the reorder test deliberately does not."
        ),
        "rationale": (
            "REJECT from clause O's merge branch: on a delete-model neighbour naming "
            "a DIFFERENT model, `mergeable` is `false` (its delete arm is "
            "`name == selfName`) while `affectsModel` is still `true` (a delete "
            "conservatively touches every model) and the neighbour is not a "
            "together-op, so the spec forces `.blocked`; this rival returns `.merge`. "
            "Refuted at selfName=8, selfKind=index, other=deleteModel 2 — a delete of "
            "a different model, a point no other reject case reaches (weak-base-"
            "const-true uses a delete only at clause B). If it verified => "
            "SPEC-TOO-WEAK (the collapse decision's model-identity check would be "
            "unpinned, and it would be conflated with the touches-every-model "
            "reorder test)."
        ),
        "witness": _witness(
            "optimizeAgainst",
            "optimizeAgainstTester 8 TogetherKind.index "
            "(OtherOp.deleteModel 2)"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts TWO functions (commutes_through,
# pair_collapses_through) over a fractional-permission carrier and ships 4
# positives + 6 uniqueness rivals + an empty AXIOM lane. This velvet bundle
# models the purely-functional core as THREE decidable methods over a
# transparent inductive carrier: reorderableBase (clause B, the baseline),
# reorderableTogether (clause T, the WIDENED specialised test — the behavioural
# delta), and optimizeAgainst (clause O, the three-way verdict threading T).
# nagini's commutes_through maps to reorderableTogether; pair_collapses_through's
# optimizer-observable maps into optimizeAgainst's verdict; the baseline B is an
# extra transparent obligation this carrier exposes.
#
#   nagini case                       -> here
#   -----------------------------------------------------------------------
#   pos-control-ct-reshape            -> pos-control-base-local          RE-EXPRESSED
#                                     -> pos-control-base-match          RE-EXPRESSED (2nd shape)
#   pos-control-ct-direct             -> pos-control-together-direct     RE-EXPRESSED
#   pos-control-pc-reshape            -> pos-control-optimize-reshape    RE-EXPRESSED
#   admiss-selfcall                   -> admiss-f2p-selfcall             PORTED (self-call half)
#   frame-mutate-other-kind           -> (none)                         VACUOUS
#   frame-mutate-between-kind         -> (none)                         VACUOUS
#   weak-base-rule-only               -> weak-base-rule-only            PORTED
#   weak-overpermissive-samefamily    -> weak-overpermissive-samekind   PORTED
#   weak-ct-constant-true             -> weak-together-const-true       PORTED
#   weak-pc-overpermissive            -> weak-optimize-no-merge / weak-optimize-reorder-baseonly  RE-EXPRESSED
#   (new, baseline obligation)        -> weak-base-inverted, weak-base-const-true  ADDED
#   (new, collapse-decision arms)     -> weak-optimize-merge-drops-elidable,
#                                        weak-optimize-merge-delete-anyname        ADDED
#   AXIOM_TESTS ([])                  -> (none)                         DROPPED (empty; G-AX lane)
#
# 14 velvet SPEC cases: 4 soundness, 1 admissibility, 9 uniqueness.
#
# RE-EXPRESSED (4 positives): the nagini positives reshape the two decision
#   bodies (branch-reorder, direct grounded return, framing-assert reshape). On
#   this carrier the counterparts are a local-staged baseline (pos-control-base-
#   local), a constructor-match baseline whose case split moves INTO the impl
#   (pos-control-base-match — a genuinely different control shape, not just a
#   different spelling of the same call), the direct grounded specialised test
#   (pos-control-together-direct, = the nagini ct-direct honest control), and a
#   merge/reorder branch split of the verdict (pos-control-optimize-reshape). All
#   four verify (real builds); pos-control-base-match re-derives its tactic body
#   (see REPROOF NOTE) because the frozen `loom_solve` is tuned to the frozen
#   impl's single-call form — a tactic gap, not a spec hole.
# PORTED (admiss-selfcall -> admiss-f2p-selfcall): the nagini case had two halves.
#   Its read-only fractional-permission half has no counterpart here (no heap, no
#   `mut` binder, no permission system). Its SELF-CALL half ports directly and is
#   what carries the content: the variant CALLS the widened decision at the
#   concrete F2P-shaped point (model 7, `unique`, against a same-model
#   different-flavour together neighbour) and conjoins the result into the
#   returned verdict, so the obligation closes only if the widening is genuinely
#   TRUE at that point. A spec whose widening clause were satisfiable nowhere, or
#   whose verdict clause held only vacuously, would FAIL this case — which the
#   frozen impl (the earlier, near-trivial form of this case) could not detect.
#   Landed with a re-derived tactic body (real build, exit 0).
# PORTED (3): weak-base-rule-only (drop the widening — the pre-patch specialised
#   test; == Solution_prepatch's reorderableTogether body), weak-overpermissive-
#   samekind (drop the different-flavour guard), weak-together-const-true (always
#   reorderable). Each carries its nagini refinement (pre-patch / over-permissive
#   same-flavour / maximal over-collapse all fail the F2P), now backed by a
#   machine-checked witness.
# RE-EXPRESSED (weak-pc-overpermissive -> weak-optimize-no-merge +
#   weak-optimize-reorder-baseonly): the nagini pair-collapse over-permissive
#   rival attacks the optimizer observable. On this carrier that observable is
#   folded into optimizeAgainst's three-way verdict, so it is attacked TWO ways:
#   dropping the merge branch (the pair never collapses to one op) and threading
#   the un-widened baseline test into the reorderable branch (the pre-patch
#   top-level verdict). Both are real divergences with machine-checked witnesses.
# ADDED (weak-optimize-merge-drops-elidable, weak-optimize-merge-delete-anyname):
#   the COLLAPSE decision `mergeable` has three arms, and the ported nagini rivals
#   attack only the together arm — nagini's carrier folded the other two into its
#   Requires, so there was nothing to port for them. Both are attacked here.
#   Dropping the elidable-generic arm (the pair collapses because the optimizer may
#   silently drop the neighbour) is refuted at other=generic true true; dropping the
#   model-identity check on the delete arm is refuted at other=deleteModel 2 against
#   selfName=8 — the point that separates the collapse decision's identity check
#   from the reorder test's deliberately conservative touches-EVERY-model answer, an
#   asymmetry no other case exercises. Both are real divergences, each with a
#   machine-checked witness (rival exit 0 / frozen exit 1, semantic refutation).
# ADDED (weak-base-inverted, weak-base-const-true): the baseline obligation B has
#   no nagini counterpart (nagini did not contract the baseline separately), so it
#   is defended (pos-control-base-local) and attacked TWO ways here — the negated
#   baseline (weak-base-inverted, at a together neighbour) and the constant-true
#   baseline (weak-base-const-true, at a delete-model neighbour) — so B's binders
#   selfName and the `other` constructor are varied across its rivals. Real
#   divergences with machine-checked witnesses, completing the attack surface on
#   the third obligation this carrier exposes.
# FRAME-MUTATION (2 nagini rivals): VACUOUS. Both write through a read-only
#   fractional-permission reference and are rejected for insufficient permission.
#   Velvet is referentially transparent, all inputs immutable, no `mut` binder,
#   no heap, no aliasing, no permission system. No read-only input to overwrite;
#   no substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# DROPPED (AXIOM_TESTS): empty in the nagini sibling (no @ContractOnly axiom;
#   meta.axioms == []). Nothing to port, and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. Every obligation is DEFENDED and ATTACKED:
#   B (pos-control-base-local, pos-control-base-match / weak-base-inverted,
#   weak-base-const-true), T (pos-control-together-direct / weak-base-rule-only,
#   weak-overpermissive-samekind, weak-together-const-true), O (pos-control-
#   optimize-reshape + admiss-f2p-selfcall / weak-optimize-no-merge,
#   weak-optimize-reorder-baseonly, weak-optimize-merge-drops-elidable,
#   weak-optimize-merge-delete-anyname). The independent clause parts of T are each
#   attacked: the baseline disjunct (weak-base-inverted at B, weak-together-const-
#   true on a touching generic), the widening disjunct (weak-base-rule-only), and
#   the different-flavour guard (weak-overpermissive-samekind). O is attacked in
#   both of its structural parts AND in each arm of its collapse decision: the
#   reorderable-test threading (weak-optimize-reorder-baseonly), the merge branch as
#   a whole (weak-optimize-no-merge), the elidable-generic collapse arm
#   (weak-optimize-merge-drops-elidable), and the delete arm's model-identity check
#   (weak-optimize-merge-delete-anyname).
#     The binders are varied across the NINE reject witnesses:
#   selfName ∈ {7,0,1,2,5,3,6,8}, selfKind ∈ {unique, index} (both values used),
#   and the `other` binder spans ALL THREE OtherOp constructors at MULTIPLE points
#   each — together (same-flavour and different-flavour, same model), deleteModel
#   (MY model via the merge rivals' spec side, and a DIFFERENT model), and generic
#   (touching/non-elidable, and touching/elidable). Nine DISTINCT input points; no
#   binder is held at one value by every witness, and each varied value changes the
#   spec's verdict at that point (not two spellings of one point).
#     Every witness was SEEN to discriminate with two real builds: it ELABORATES
#   against its rival (exit 0) and FAILS against the frozen solution (exit 1) with
#   a SEMANTIC refutation — the failure text is `decide` proving the tester-equals-
#   false proposition is itself false, i.e. gold SATISFIES the spec there. Not an
#   unknown identifier, not a type error, not a stuck reduction, not a timeout.
AXIOM_TESTS = []
