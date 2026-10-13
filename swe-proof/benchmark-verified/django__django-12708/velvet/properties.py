"""properties.py — G-PBT falsification battery for django__django-12708 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives with a byte-identical statement)
and swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method selecting a sublist of the constraints
defined on a target column set — each constraint carries two boolean flags, does
it provide an index and does it enforce uniqueness — and returning, in order,
exactly the constraints that are selectable for removal of a composite index):

  selectIndexConstraints (cs : List Constraint) return (out : List Constraint)
    ensures out = selected cs

The single load-bearing clause pins the WHOLE returned list, element-wise and in
order, to ``selected cs`` — a fully-unfolded front-recursive ``def`` in the
``pure`` region that keeps a constraint exactly when ``keep c`` holds, where
``keep c = c.isIndex && !c.isUnique``. ``selected``/``keep`` are grounded
``def``s (no opaque answer key), so pinning ``out = selected cs`` IS the work;
there is no wrong echo that verifies.

The per-element predicate ``keep`` reads BOTH boolean fields: a constraint is
kept iff it is an index AND is NOT a uniqueness constraint. The discriminating
sub-domain is a co-located index-backed uniqueness constraint
(``isIndex = true, isUnique = true``): it must be DROPPED (it is left untouched),
while a plain index (``isIndex = true, isUnique = false``) must be KEPT. The
rivals below attack each half of ``keep`` and the list traversal, and their
witnesses move both boolean binders across ``{true, false}`` and the list length
across ``{1, 2}`` — so no field of the carrier is left pinned at one value.

ADVERSARIAL READ of the nagini classes on THIS carrier (see the accounting block
at the foot of the file for the case-by-case disposition):
  * FRAME/PERMISSION-MUTATION — VACUOUS here. The nagini sibling carries a
    MANDATORY frame-write rival because its read-only input holds a fractional
    heap permission (``Acc(list_pred(constraints), 1/2)``) a rival could demand
    at full strength. Lean and Velvet are referentially transparent: the input
    is an immutable value, this bundle declares no ``mut`` parameter, and there
    is no heap and no aliasing — there is no read-only input to overwrite and no
    substitute probe to fabricate. Not fabricated (per the porting map).
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, exactly as the sibling
    records: ``selected``/``keep`` are concrete ``def``s in the ``pure`` region
    and the ``axioms`` region is EMPTY, so there is no answer key to echo. The
    honest grounded controls (a correct reshape + the honest cheapest impl) are
    the sibling's directive-2 substitute, carried here.
  * PARTIAL-DOMAIN / VALUE — the core attacks. Each rival is correct on part of
    the domain but diverges on a sub-domain: drop one of the two conjuncts of
    ``keep`` (count every index / require uniqueness), or an off-by-one that
    never considers the first constraint. The whole-list equality
    ``out = selected cs`` (element-wise, order included) is what rejects each
    divergence.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is a backward ``while`` loop
whose extracted program is a partial-fixpoint iteration the kernel does NOT
reduce (``decide`` gets stuck on the frozen solution's tester). This is exactly
why a bare "did not verify" attributes nothing: reshaping the loop breaks the
frozen tactic script regardless of correctness. Each reject rival is therefore a
straight-line COMPUTABLE impl (``cs.filter …``), so its extracted program
reduces under ``decide`` and the witness ``selectIndexConstraintsTester args =
false`` ELABORATES against the rival; against the frozen loop-solution the same
``decide`` stays stuck, so the witness FAILS on gold — the required
discriminator. Both halves were checked out-of-band with
``scripts/lean_verify.sh`` (rival elaborates, gold fails) for every reject case.

``Constraint`` derives only ``Inhabited`` in the frozen spec, so the tester's
``Decidable (out = selected cs)`` instance is stuck. Each witness therefore
brings ``deriving instance DecidableEq for Constraint`` into its own scope BEFORE
the tester directives; this declaration is appended to BOTH the rival and the
gold witness file (it is part of the witness snippet, not the variant), so it
exists on both sides by construction and neither half depends on a name only one
side has. It touches nothing in the frozen spec view.

AXIOM lane: EMPTY. ``meta.json`` declares no ``axiom`` and no A-reference deep
model — the selection is modeled DEEPLY as ``selected``/``keep`` (an I op, the
per-constraint filter transliterated identically), so there is no
axiom-soundness / axiom-containment obligation to probe and the gate ignores
``AXIOM_TESTS`` regardless. (The sibling records the same: axioms region empty by
design; the sibling's note that the callee is validated == the real callee is a
G-AX/G-CONF concern, dropped per the porting map.)
"""
from pathlib import Path

INSTANCE = "django__django-12708"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl body (everything strictly between the markers). Reject
# rivals replace it with a straight-line computable impl so their tester reduces.
_IMPL = (
    "    let mut result : List Constraint := []\n"
    "    let mut i := cs.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ cs.length\n"
    "      invariant result = selected (cs.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := cs[i - 1]!\n"
    "      result := (if keep c then [c] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The single per-element keep-decision inside the loop body (positive control
# keeps the loop and only reshapes this line).
_GUARD = "      result := (if keep c then [c] else []) ++ result\n"

# The first line of the impl body (anchor for the admissibility assert, inserted
# ahead of the loop while keeping the loop body verbatim).
_RESULT_DECL = "    let mut result : List Constraint := []\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = (
    "prove_correct selectIndexConstraints by\n"
    "  loom_solve\n"
    "  rw [selected_drop_step cs i (by omega) (by omega)]\n"
    "  simp_all\n"
)

# Proof for the honest-cheapest positive: `return selected cs` leaves no loop, so
# `loom_solve` closes the (now trivial) obligation with no drop-step rewrite.
_PROOF_CHEAPEST = "prove_correct selectIndexConstraints by\n  loom_solve\n"

# Proof robust to an added in-region assert VC (admissibility): discharge the
# loop step where present and close the assert by unfolding the fold.
_PROOF_RETUNED = (
    "prove_correct selectIndexConstraints by\n"
    "  loom_solve <;>\n"
    "    (try (rw [selected_drop_step cs i (by omega) (by omega)])) <;>\n"
    "    simp_all [selected, keep]\n"
)


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `selectIndexConstraintsTester cs = false` says the extracted program's
# ---- result violates `out = selected cs` at that concrete input. Checked in a
# ---- file whose `prove_correct` block is stripped, so no tactic script can mask
# ---- the verdict. The method has no `require` clause, so every input reaches
# ---- the postcondition. `deriving instance DecidableEq for Constraint` is
# ---- brought into the witness's own scope so the tester's decidability instance
# ---- reduces; it is appended to BOTH the rival and the gold build.
_TESTER = (
    "deriving instance DecidableEq for Constraint\n\n"
    "extract_program_for selectIndexConstraints\n"
    "prove_precondition_decidable_for selectIndexConstraints\n"
    "prove_postcondition_decidable_for selectIndexConstraints\n"
    "derive_tester_for selectIndexConstraints\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


def _c(name: str, idx: str, uniq: str) -> str:
    return "{ name := \"%s\", isIndex := %s, isUnique := %s }" % (name, idx, uniq)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify. If a faithful correct reshape could NOT verify the spec
    # is SPEC-TOO-STRONG. The per-element keep-decision is bound to a typed local
    # `kept` and then prepended; every loop invariant is kept verbatim, so the
    # frozen front-recursive single-unfold proof still closes (no retune needed).
    # =====================================================================
    {
        "id": "pos-hoist-keep",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _GUARD,
            "      let kept : List Constraint := if keep c then [c] else []\n"
            "      result := kept ++ result\n"),
        "rationale": "binding the per-element keep-decision "
                     "(if keep c then [c] else []) to a typed local `kept` before "
                     "prepending it leaves the prepended value identical, so "
                     "`out = selected cs` still holds; every loop invariant is "
                     "kept verbatim so the frozen single-unfold proof is "
                     "preserved (no new lemma). A faithful correct reshape that "
                     "could NOT verify would mean SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        # Honest cheapest impl: return the grounded fold directly. Because the
        # postcondition's `selected` is a function of the input (not an opaque
        # key), this DOES do the work and MUST verify — the loop is gone, so the
        # obligation collapses and `loom_solve` closes it with no drop-step
        # rewrite. Demonstrates the oracle is grounded (no wrong echo).
        "module": _swap(
            _swap(_BASE, _IMPL, "    return selected cs\n"),
            _PROOF, _PROOF_CHEAPEST),
        "rationale": "honest cheapest impl: return the grounded fold "
                     "`selected cs` directly. `selected` is a def of the input "
                     "(grounded, fully unfolded), so returning it IS doing the "
                     "work — it must verify. The loop is removed so `loom_solve` "
                     "discharges the reduced obligation directly. Demonstrates "
                     "there is no ungrounded answer-key to echo.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so no input is
    # excluded and the usual "a normal input satisfies the precondition" probe is
    # vacuous. The residual admissibility risk on a total domain is a DEGENERATE
    # / unsatisfiable post-image — a spec no impl can meet reads exactly like a
    # spec every impl meets. This case discharges an in-region assert that the
    # post-image genuinely DISTINGUISHES the two arms of `keep` at the ticket-
    # shaped point: a co-located index-backed uniqueness constraint is DROPPED
    # (selected [..true,true..] = []) while a plain index is KEPT
    # (selected [..true,false..] = [that constraint]). The two arms differ, so
    # the obligation is jointly satisfiable and non-trivial. The impl and its
    # invariants are kept verbatim so the method's own ensures still discharges;
    # the proof is retuned only to also close the added assert VC.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RESULT_DECL,
                "    assert (with_name_prefix `admiss\n"
                "      (selected [ " + _c("u", "true", "true") + " ] = ([] : List Constraint) ∧\n"
                "       selected [ " + _c("i", "true", "false") + " ] = [ " + _c("i", "true", "false") + " ]))\n"
                + _RESULT_DECL),
            _PROOF, _PROOF_RETUNED),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "ticket-shaped point: a co-located index-backed uniqueness "
                     "constraint is DROPPED (selected [{true,true}] = []) while a "
                     "plain index is KEPT (selected [{true,false}] = [that]). The "
                     "two arms of `keep` differ, so the ensures is not vacuously "
                     "met. The in-region assert must discharge (else an "
                     "unsatisfiable/degenerate obligation would read as trivially "
                     "met) and the loop body is kept verbatim so "
                     "`out = selected cs` still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # that FAILS on the frozen loop-solution, and each carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-overbroad-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The EXACT pre-patch bug: drop the `!isUnique` conjunct, keeping every
        # index whether or not it is index-backed uniqueness. isIndex=true,
        # isUnique=true (the co-located collision) is the divergence.
        "module": _impl(
            "    let out := cs.filter (fun c => c.isIndex)\n    return out\n"),
        "refinement": "dropping the `!isUnique` conjunct is the PRE-patch filter "
                      "(index-only, no uniqueness restriction). On an index-"
                      "backed uniqueness constraint co-located with the target "
                      "columns it selects BOTH the uniqueness and the index "
                      "constraint — the count-of-two collision the issue "
                      "describes, which makes the composite-index deletion abort. "
                      "It does NOT resolve the F2P.",
        "rationale": "REJECT from `out = selected cs`: `keep` requires "
                     "!isUnique, so `selected` drops an index-backed uniqueness "
                     "constraint. On cs = [{isIndex:=true, isUnique:=true}] this "
                     "rival emits that constraint but `selected` emits [], so the "
                     "whole-list equality fails. Refuted at isUnique = true, the "
                     "conjunct this rival deletes.",
        "witness": _witness(
            "selectIndexConstraintsTester [ " + _c("x", "true", "true") + " ]"),
    },
    {
        "id": "weak-pick-unique",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong bit: require isUnique instead of forbidding it (isIndex &&
        # isUnique). Selects the index-backed uniqueness constraint and drops the
        # plain index. isIndex=true, isUnique=false is the divergence.
        "module": _impl(
            "    let out := cs.filter (fun c => c.isIndex && c.isUnique)\n    return out\n"),
        "refinement": "requiring `isUnique` instead of forbidding it selects the "
                      "index-backed UNIQUENESS constraint for deletion, dropping "
                      "the user's uniqueness guarantee while leaving the plain "
                      "index. The failing test asserts the uniqueness constraint "
                      "STILL exists and the plain index is gone — the exact "
                      "opposite — so it does NOT resolve.",
        "rationale": "REJECT from `out = selected cs`: `keep` keeps a plain index "
                     "(isIndex && !isUnique) and drops uniqueness. On cs = "
                     "[{isIndex:=true, isUnique:=false}] `selected` emits that "
                     "plain index but this rival emits [], so the whole-list "
                     "equality fails. Refuted at isUnique = false with a plain "
                     "index, the element `keep` selects and this rival rejects.",
        "witness": _witness(
            "selectIndexConstraintsTester [ " + _c("i", "true", "false") + " ]"),
    },
    {
        "id": "weak-drop-index-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the `isIndex` conjunct: keep every non-uniqueness constraint,
        # including a pure non-index constraint. Moves isIndex to false — the
        # only rival whose witness exercises isIndex = false.
        "module": _impl(
            "    let out := cs.filter (fun c => !c.isUnique)\n    return out\n"),
        "refinement": "dropping the `isIndex` conjunct keeps every non-uniqueness "
                      "constraint on the target columns, including ones that "
                      "provide no index at all. It would issue index-deletion "
                      "SQL against constraints that are not indexes, mismatching "
                      "the set the deletion pipeline must target; it does NOT "
                      "resolve the F2P.",
        "rationale": "REJECT from `out = selected cs`: `keep` requires isIndex. "
                     "On cs = [{isIndex:=false, isUnique:=false}] this rival "
                     "emits that non-index constraint but `selected` emits [], so "
                     "the whole-list equality fails. Refuted at isIndex = false, "
                     "the conjunct this rival deletes — the only witness that "
                     "moves isIndex to false.",
        "witness": _witness(
            "selectIndexConstraintsTester [ " + _c("p", "false", "false") + " ]"),
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one: never considers the FIRST constraint (drop 1). Correct on
        # every input whose first element does not qualify, but drops a
        # qualifying cs[0]. Exercises list length 2 and order.
        "module": _impl(
            "    let out := (cs.drop 1).filter (fun c => keep c)\n    return out\n"),
        "refinement": "skipping the first constraint corresponds to a traversal "
                      "that enumerates the target-column constraints but drops "
                      "the first — so when the removable plain index is "
                      "enumerated first it is never selected, its index is not "
                      "deleted, and the assertion that the index is gone fails. "
                      "It does NOT resolve the F2P.",
        "rationale": "REJECT from `out = selected cs`: dropping the first element "
                     "yields `selected` over cs.drop 1, not over cs. On cs = "
                     "[{isIndex:=true, isUnique:=false}, {isIndex:=true, "
                     "isUnique:=false}] `selected` emits both but this rival "
                     "emits only the second, so the whole-list equality fails. "
                     "Refuted over a length-2 list whose leading element "
                     "qualifies, exercising list length and order.",
        "witness": _witness(
            "selectIndexConstraintsTester [ " + _c("a", "true", "false")
            + ", " + _c("b", "true", "false") + " ]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation rival, 3 partial-domain rivals)
# plus 0 AXIOM_TESTS. This bundle models the SAME single behaviour (which
# constraints on the target columns are selected for composite-index removal)
# over a narrowed carrier: the sibling counts a fold `count_selected(ToSeq(...))`
# to an int; here the operation returns the SUBLIST `selected cs` over a
# `List Constraint`, each element exposing exactly the two booleans the patch
# filters on (isIndex, isUnique). The sibling's per-code integer encoding
# (code 1 = index, code 3 = index+unique) becomes two explicit boolean fields.
#
#   sibling case                -> here                       disposition
#   ---------------------------------------------------------------------------
#   pos-control-selects         -> pos-hoist-keep             PORTED
#   pos-control-cheapest        -> pos-cheapest               PORTED
#   admiss-f2p                  -> admiss-nondegenerate       RE-AIMED
#   frame-write                 -> (none)                     VACUOUS
#   weak-overbroad-prepatch     -> weak-overbroad-prepatch    PORTED
#   weak-pick-unique            -> weak-pick-unique           PORTED
#   weak-skip-first             -> weak-skip-first            PORTED
#   (no sibling)                -> weak-drop-index-guard      ADDED
#
# 5 ported, 1 re-aimed, 1 vacuous, 1 added, 0 dropped.
#
# PORTED (pos-control-selects -> pos-hoist-keep): the sibling reshapes the branch
#   test to the @Pure helper `selects` while keeping the backward loop and every
#   invariant verbatim. Here the guard's OUTPUT (the singleton-or-empty keep-
#   list) is bound to a typed local `kept` and prepended; every invariant is kept
#   verbatim, so the frozen single-unfold proof closes unchanged. Verified.
# PORTED (pos-control-cheapest -> pos-cheapest): return the grounded fold
#   `selected cs` directly; the loop is removed and `loom_solve` closes the
#   reduced obligation with no drop-step rewrite. Same grounded-oracle
#   demonstration as the sibling. Verified.
# RE-AIMED (admiss-f2p -> admiss-nondegenerate): the sibling builds the F2P-
#   shaped input and asserts the read-only permission is establishable and the
#   result is in domain. This backend is referentially transparent (no
#   permissions) and the method has NO `require` clause, so that probe is
#   vacuous. It is re-aimed at the residual total-domain risk — a DEGENERATE /
#   unsatisfiable post-image — via an in-region assert that at the ticket point
#   the two arms of `keep` genuinely differ (index-backed uniqueness dropped,
#   plain index kept). Impl and invariants kept verbatim so the ensures still
#   discharges. Verified.
# VACUOUS (frame-write): the sibling carries this as MANDATORY because the
#   read-only input holds a fractional heap permission
#   (Acc(list_pred(constraints), 1/2)) a rival could demand at full strength.
#   Lean and Velvet are referentially transparent, have no heap/aliasing, and
#   this bundle declares no `mut` parameter — the input is an immutable value
#   with no permission footprint, so there is no read-only input to overwrite. No
#   substitute fabricated (per the porting map: this class is vacuous here).
# PORTED (the three partial-domain rivals): weak-overbroad-prepatch (drop the
#   !isUnique conjunct — the exact pre-patch bug), weak-pick-unique (require
#   isUnique — the wrong bit), and weak-skip-first (never consider the first
#   constraint) port directly. Each carries a machine-checked witness that
#   ELABORATES against its (straight-line, reducible) rival and FAILS against the
#   frozen loop-solution (two real builds per case).
# ADDED (weak-drop-index-guard): the sibling's carrier encodes "is an index" as
#   the integer predicate is_index and never tests a rival that drops it in
#   isolation (its codes always co-vary index/unique). The boolean carrier here
#   exposes isIndex as an independent field, so a rival that keeps every
#   non-uniqueness constraint regardless of isIndex is expressible and worth
#   attacking — it is the ONLY witness that moves isIndex to false, closing the
#   binder-coverage gap on the isIndex conjunct of `keep`.
# DROPPED: none. The sibling's AXIOM_TESTS list is empty (axioms region empty by
#   design); there is nothing for the axiom lane to port and the gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / DOMAIN COVERAGE of the four reject witnesses over the input carrier
#   `cs : List Constraint` and the two boolean fields `keep` reads:
#     isIndex  — true  (weak-overbroad, weak-pick-unique, weak-skip-first),
#                false (weak-drop-index-guard). BOTH values probed.
#     isUnique — true  (weak-overbroad-prepatch),
#                false (weak-pick-unique, weak-drop-index-guard, weak-skip-first).
#                BOTH values probed.
#     list length/order — length 1 (three rivals) and length 2 with an
#                order-sensitive leading qualifier (weak-skip-first).
#   CLAUSE: the single load-bearing clause `out = selected cs` is attacked by all
#     four rivals, each at a DISTINCT input point (pts=4). Both conjuncts of
#     `keep` are attacked (overbroad drops !isUnique; pick-unique inverts it;
#     drop-index-guard drops isIndex) and the traversal itself is attacked
#     (skip-first).
#
# AXIOM_TESTS: empty. This bundle declares no axiom and no A-reference deep model
# (the selection is modeled deeply as `selected`/`keep`, an I op), so there is
# nothing for the axiom lane to probe; the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
