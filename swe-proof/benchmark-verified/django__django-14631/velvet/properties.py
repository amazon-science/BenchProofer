"""properties.py — G-PBT falsification battery for django__django-14631 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct cleanFields`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the witness SUBJECT. On this bundle the subject is NOT gold — gold's
``while``-loop extraction is irreducible under ``decide`` — but an explicitly
named, independently-verified ``witness_reference``; see WITNESS MECHANICS.

DEFENDED SURFACE (one contracted method):

  cleanFields (fields : List FieldSlot) return (out : List Stamp)
    ensures out = cleanedSeq fields                       -- the WHOLE pin (C1)

The method walks a list of field slots and reports, per slot, the value it
resolves for cleaning. A read-only slot resolves its exposed stored value
(``slotValue f = initialFor f``), where a coarse slot drops the finer sub-count
to 0 and any other stored value passes through; a non-read-only slot resolves
the value supplied through ordinary data (``f.given``). The whole-list result is
the pure front-recursive fold ``cleanedSeq`` (``cleanedSeq (f :: fs) =
slotValue f :: cleanedSeq fs``). ``cleanedSeq``, ``slotValue`` and ``initialFor``
are all TRANSPARENT ``def``s over the method's own input — there is NO opaque
answer-key oracle in the load-bearing clause, so pinning ``out = cleanedSeq
fields`` is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. There is exactly one ``ensures`` clause, C1
(``out = cleanedSeq fields``), and it is the only impl-constraining clause: it
is a function of ``fields`` and pins, at every list position, which value each
slot resolves — the read-only vs data branch, the coarse sub-count drop on the
exposed stored value, and the traversal order/length. Every uniqueness rival
therefore targets C1, each at a DIFFERENT input binder of the per-slot predicate
(``readOnly``, ``coarse``, ``stored`` vs ``given``) or the list structure.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts a SINGLE-field ``clean_bound_initial_field(fs) -> int`` over a
``FieldState`` carrying TWO distinct source evaluations — a cached first
evaluation ``fs.first_eval`` and an independent fresh re-evaluation
``fs.fresh_eval`` of a STATEFUL callable source. This velvet bundle models the
WHOLE per-field loop over a ``List FieldSlot`` and, crucially, narrows the
carrier: a slot has ONE resolved stored value ``f.stored`` (evaluated once),
there is no second re-evaluation to model. Several nagini rivals attack that
second-evaluation axis and have NO counterpart here — see the accounting footer.

  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-first-eval`` rival writes through a read-only
    (``Acc(fs.first_eval, 1/2)``) reference and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: ``fields`` is an
    immutable value, this bundle declares no ``mut`` parameter, and there is no
    heap, aliasing, or permission system to subvert. There is no read-only input
    to overwrite, so the class is vacuous. No substitute probe is fabricated.
  * DIVERGENCE: REJECTED BY THE SPEC, but NOT SHIPPABLE as a reject case here.
    The nagini sibling carries one ``weak-diverge-reject`` case, rejected by
    ``Requires(MustTerminate(2))``. This bundle runs under
    ``set_option loom.semantics.termination "total"`` (NOT ``partial``, which no
    velvet bundle sets), so the
    verifier does discharge a termination obligation and a diverging rival is
    genuinely REJECTED. Vacuous satisfaction is the ``partial`` disposition and
    does not arise here.

    A previous revision of this file called the class VACUOUS on the ground that
    a diverging impl is "unwritable" against the frozen ``while``. The second
    audit measured that and it is FALSE: a diverging impl is perfectly writable
    (append a second ``while spin > 0`` whose body holds the measure constant,
    or increments it, after the correct value is computed) and it is rejected
    with the TERMINATION obligation as the residual goal —
    ``case «decreasing_1: spin» … ⊢ 1 < spin`` — not with a parse or scope
    error. So the class is real and spec-attributable, and the earlier
    "unwritable" claim is withdrawn.

    It is nevertheless NOT shipped as an ``expect="reject"`` case, for a
    WITNESS-side reason that was measured rather than assumed. This backend
    requires a refutation witness that ELABORATES against the rival, and a
    diverging rival cannot supply one: its extracted ``cleanFieldsExec`` has no
    ``DivM.res`` normal form to reduce to, so ``decide`` against the rival is
    STUCK ("its ``Decidable`` instance … did not reduce") exactly as it is
    against gold's ``while``. Built both halves: witness-vs-rival exit 1 by
    stuck reduction (the half that must SUCCEED), witness-vs-reference exit 1.
    A case whose witness cannot hold of its own rival records
    ``witness-unproven`` — an inconclusive outcome, not a pass — so landing it
    would FAIL this gate rather than strengthen it. Recorded here as a KNOWN
    WITNESS-SIDE LIMITATION of the divergence lane on this carrier (the spec
    itself rejects the rival), not as a vacuous class and not as a spec hole.
  * SECOND-EVALUATION axis (``fs.fresh_eval``: the pre-patch fresh re-eval, the
    dead-then-correct re-eval, the max-mix of fresh vs first) — NO COUNTERPART.
    These three nagini rivals all abuse a SECOND, independent evaluation of a
    stateful source, whose whole point is that it disagrees with the cached first
    evaluation. This carrier collapses to a single resolved ``f.stored`` per slot
    (mapping.md §1: "evaluated once and cached on the BoundField"); there is no
    second evaluation term to feed a rival, so no impl over this carrier can
    express "clean the fresh re-evaluation". They are dropped as carrier
    narrowing (footer), NOT as omissions of difficulty.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. The one
    nagini value rival with a faithful counterpart here is
    ``partial-domain-unnormalised-first`` (use the raw stored value without the
    coarse sub-count drop — the exact pre-patch defect); it is ported as
    ``rival-raw-stored``. Four further rivals attack the other C1 binders (the
    ``readOnly`` branch selector both ways, the list length, and the traversal
    ORDER), each a genuine verify-does-not-resolve break with a machine-checked
    witness.

WITNESS MECHANICS ON THIS BUNDLE. Unlike the django-11276 sibling (whose
round-trip clauses mention an opaque ``entityDecode`` axiom and kill the
``derive_tester_for`` + ``decide`` path), C1's post-image ``cleanedSeq`` here is
FULLY TRANSPARENT over the input. Each rival is written LOOP-FREE (a
``fields.map``, or a ``match`` on the head), so its extracted program
``cleanFieldsExec`` — the ``NonDetT``-run of the impl — REDUCES fully under
``decide`` at a concrete input. Each witness states, at one concrete input,

    (match cleanFieldsExec <input> with | DivM.res r => r | _ => [])
        ≠ cleanedSeq <input>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator sees.

THE SECOND HALF CANNOT BE GOLD ON THIS BUNDLE, and every reject case therefore
names an explicit ``witness_reference``. The frozen impl is the ``while`` loop;
under ``loom.semantics.choice "demonic"`` its extracted ``cleanFieldsExec``
elaborates through ``Classical.choice``, which the kernel cannot unfold. So
``decide`` against gold does not REFUTE the witness — it gets STUCK, reporting

    its `Decidable` instance instDecidableNot did not reduce to `isTrue` or
    `isFalse` … reduction got stuck at … .hasDecEq

for EVERY claim about gold regardless of truth (measured directly: ``decide
+kernel`` is stuck identically, and ``#reduce`` exhibits the residual
``Classical.choice`` term). An exit code produced that way attests to a
refutation the kernel never performed, which is the ``witness-undecided``
defect class ``gates/pbt.py`` screens for — so "the witness fails on gold" is
NOT the discrimination this bundle can rely on, and it is not claimed here.

Instead each reject case carries ``witness_reference``: a loop-free
``fields.map slotValue`` impl of the SAME frozen spec, which the gate
independently checks shares the spec view and VERIFIES before using it as the
subject. An impl the verifier accepts cannot violate its own spec, so a genuine
"C1 is violated at this input" statement must fail there — and against this
reference the failure is a real SEMANTIC refutation, ``decide`` reporting

    Tactic `decide` proved that the proposition … is false

which is the substance the attestation needs. Naming the reference explicitly
also removes the case's dependence on the gate's internal stuck-reduction
FALLBACK (which would otherwise silently pick a battery positive), so what the
rejection is attributable to is recorded in the artifact rather than inferred.

No witness binds a hypothesis (every input is a concrete ``FieldSlot`` literal
with small ``Int`` components that decide C1), so no consistency probe is needed,
and no witness can be inconsistent. No banned token
(sorry/admit/native_decide/axiom/opaque). Every witness was checked out-of-band
with ``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0) and
FAILS with a semantic ``decide``-proved-false error against the reference impl
(exit 1).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries none either
(``meta.axioms == []``); the ``initialFor == BoundField.initial`` deep model is
an A-reference validated by G-AX / axiom_check.py, not a consumed axiom, and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14631"
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
    "    let mut result : List Stamp := []\n"
    "    let mut i := fields.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
    "      invariant result = cleanedSeq (fields.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let f := fields[i - 1]!\n"
    "      result := slotValue f :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct cleanFields by\n"
    "  loom_solve\n"
    "  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes whose residual
    goal no longer matches the frozen backward-fold tactic script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- A loop-free rival: resolve each slot with a custom per-slot map. Being
# ---- loop-free (`fields.map`), its extracted `…Exec` reduces under `decide` so
# ---- its witness discriminates; gold's `while`-loop `…Exec` stays stuck.
def _map(mapexpr):
    return _impl(f"    return (fields.map (fun f => {mapexpr}))")


# ---- witness preamble + builder. C1's post-image `cleanedSeq` is TRANSPARENT
# ---- (no opaque axiom in the clause), so the executable program is extracted
# ---- and C1 refuted directly at a concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT = "extract_program_for cleanFields\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match cleanFieldsExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ cleanedSeq ({inp}) := by\n"
        "  decide\n"
    )


# ---- THE WITNESS SUBJECT for every reject case. Gold cannot serve as one here:
# ---- the frozen impl is the `while` loop, whose extracted `cleanFieldsExec`
# ---- elaborates through `Classical.choice` under
# ---- `loom.semantics.choice "demonic"`, so `decide` against gold is STUCK for
# ---- every claim ("did not reduce to `isTrue` or `isFalse` … stuck at
# ---- `.hasDecEq`") rather than refuting anything. This reference is a LOOP-FREE
# ---- `fields.map slotValue` impl of the same frozen spec — it reduces, and the
# ---- gate checks it shares the spec view AND verifies before refuting any
# ---- witness against it, so "the witness fails here" is a real semantic
# ---- refutation ("`decide` proved that the proposition … is false"). An impl
# ---- the verifier accepts cannot violate its own spec, so this is sound as a
# ---- discriminator for exactly the reason gold would have been.
_REFERENCE = _impl_reproved(
    "    return (fields.map slotValue)",
    "prove_correct cleanFields by\n"
    "  loom_solve\n"
    "  induction fields with\n"
    "  | nil => rfl\n"
    "  | cons f fs ih => simp_all [cleanedSeq_cons]")


# ---- FieldSlot / Stamp literal helpers (keep witnesses readable). Small `Int`
# ---- components so `decide` reduces C1 without arithmetic stalls.
def _S(sec, sub):
    return f"{{ sec := {sec}, sub := {sub} }}"


def _F(ro, co, st, gi):
    return (f"{{ readOnly := {ro}, coarse := {co}, "
            f"stored := {st}, given := {gi} }}")


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
        # Reshape: report the whole-list result DIRECTLY via the transparent
        # fold, no per-slot loop. C1 is literally `out = cleanedSeq fields`, so
        # this is the cheapest HONEST correct impl — and, since `cleanedSeq
        # fields` is GROUNDED in the argument (not an opaque answer key), it
        # doubles as proof the spec is not echo-vulnerable (any WRONG per-slot
        # resolution fails `out = cleanedSeq fields`). The loop is gone, so the
        # frozen proof's backward-fold step is unneeded and the residual goal
        # closes under `loom_solve` alone.
        "module": _impl_reproved(
            "    return (cleanedSeq fields)",
            "prove_correct cleanFields by\n  loom_solve"),
        "rationale": (
            "the post-image `cleanedSeq fields` is GROUNDED in the input (a total "
            "front-recursive fold, no opaque answer key), so `return cleanedSeq "
            "fields` is the honest cheapest CORRECT impl; C1 is literally `out = "
            "cleanedSeq fields`, so it MUST verify, else C1 is SPEC-TOO-STRONG. "
            "Re-expresses the nagini pos-control-direct (return normalise of the "
            "resolved value) on the whole-list carrier: the cheapest impl "
            "satisfying the grounded pin, showing the spec is not echo-vulnerable."
        ),
    },
    {
        "id": "pos-control-inline-normalise",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold, but INLINE the per-slot
        # resolution arithmetic (the unfolded body of slotValue/initialFor: the
        # readOnly branch, and inside it the coarse sub-count drop) instead of
        # calling `slotValue`. Same value flow, different syntactic form; the
        # frozen proof is retuned by handing `slotValue`/`initialFor` to the
        # closing `simp_all` (the loop invariant and step lemma are unchanged).
        "module": _impl_reproved(
            "    let mut result : List Stamp := []\n"
            "    let mut i := fields.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ fields.length\n"
            "      invariant result = cleanedSeq (fields.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let f := fields[i - 1]!\n"
            "      let v : Stamp := if f.readOnly then "
            "(if f.coarse then { f.stored with sub := 0 } else f.stored) "
            "else f.given\n"
            "      result := v :: result\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct cleanFields by\n"
            "  loom_solve\n"
            "  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]\n"
            "  simp_all [slotValue, initialFor]"),
        "rationale": (
            "a correct impl with a DIFFERENT syntactic shape (inline the "
            "slotValue/initialFor resolution — the readOnly branch and the coarse "
            "sub-count drop — instead of calling `slotValue`) must verify; the "
            "value flow is unchanged so C1 still discharges once the closing step "
            "unfolds `slotValue`/`initialFor`. Ports the nagini "
            "pos-control-inline-normalise (unfolded normalisation arithmetic). If "
            "it fails => SPEC-TOO-STRONG (over-fit to the `slotValue`-call form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p-shaped-input, then
    # STRENGTHENED by the second audit. That nagini case established the
    # read-only fractional-permission precondition on an F2P-shaped FieldState.
    # This method carries NO `require` clause (the pre-conditions region is
    # empty), so nothing could exclude a normal input and the classic "a normal
    # input is admitted" probe has no precondition to probe.
    #
    # SECOND-AUDIT REPAIR. The previous shape was `module = _BASE` — the frozen
    # file verbatim. That passes honestly but attests to nothing this bundle does
    # not already record under G-VERIFY / G-GOLD: it re-runs the frozen build. It
    # is a HOLLOW positive, and the analogue of admissibility on a TOTAL carrier
    # is available here — the obligation being satisfiable at exactly an
    # F2P-shaped input, discharged BY EVALUATION as a `have` before the frozen
    # obligation closes verbatim. The `have`s below do that at the F2P shape (a
    # read-only + coarse slot whose stored sub-count is non-zero, alongside an
    # enabled slot), and they also show the post-image is NON-DEGENERATE: the
    # sub-count drop is a real restriction (initialFor moves the value) and the
    # enabled branch really reads `given`, so the clause is not satisfied by an
    # identity or a constant. Each edit lies wholly inside the elided
    # `prove_correct` tactic body, so same_spec still holds by construction and
    # the frozen statement is untouched.
    #
    # MEASURED LOAD-BEARING (not decoration). Three negative controls, each
    # corrupting exactly one `have` and leaving everything else alone, ALL fail
    # to build (exit 1, `decide` proving the corrupted equation false):
    #   * claim the sub-count SURVIVES at the F2P point   -> exit 1
    #   * flip the "is a real restriction" ≠ into =        -> exit 1
    #   * claim the enabled slot resolves `stored`         -> exit 1
    # So a degenerate, collapsed, or mis-branched post-image cannot satisfy them.
    # MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct cleanFields by\n"
            "  have satisfiableAtF2PShape :\n"
            "      cleanedSeq [{ readOnly := true, coarse := true,"
            " stored := { sec := 46, sub := 123456 },"
            " given := { sec := 0, sub := 0 } },\n"
            "         { readOnly := false, coarse := false,"
            " stored := { sec := 46, sub := 0 },"
            " given := { sec := 46, sub := 0 } }]\n"
            "        = [{ sec := 46, sub := 0 }, { sec := 46, sub := 0 }]"
            " := by decide\n"
            "  have subCountDropIsARealRestriction :\n"
            "      initialFor { readOnly := true, coarse := true,"
            " stored := { sec := 46, sub := 123456 },"
            " given := { sec := 0, sub := 0 } }\n"
            "        ≠ ({ sec := 46, sub := 123456 } : Stamp) := by decide\n"
            "  have enabledSlotTakesGiven :\n"
            "      slotValue { readOnly := false, coarse := false,"
            " stored := { sec := 1, sub := 0 },"
            " given := { sec := 2, sub := 0 } }\n"
            "        = ({ sec := 2, sub := 0 } : Stamp) := by decide\n"
            "  loom_solve\n"
            "  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]\n"
            "  simp_all"),
        "rationale": (
            "the input carries no `require`, so the cleaner is total over every "
            "field-slot list and there is no precondition to be TOO STRONG. The "
            "total-carrier analogue is what this case tests instead: that the "
            "obligation `out = cleanedSeq fields` is SATISFIABLE at exactly an "
            "F2P-shaped input, discharged by evaluation (`decide`) as a `have` "
            "before the frozen obligation closes verbatim — a read-only+coarse "
            "slot whose stored sub-count is non-zero, next to an enabled slot. "
            "Two further `have`s pin that the post-image is NON-DEGENERATE at "
            "that shape: the sub-count drop genuinely MOVES the value (initialFor "
            "≠ the raw stored value), and the enabled branch genuinely reads "
            "`given`, so the clause cannot be satisfied by an identity or a "
            "constant. Replaces a previous `module = _BASE` shape, which merely "
            "re-ran the frozen build and attested to nothing beyond G-VERIFY. "
            "Re-aimed from the nagini admiss-f2p-shaped-input, whose "
            "read-only-permission half (Acc 1/2 on first_eval) has no counterpart "
            "on this referentially-transparent, unconditioned carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = cleanedSeq
    # fields`); the per-slot binders (readOnly, coarse, stored vs given) and the
    # list structure are varied across the four witnesses.
    # =====================================================================
    {
        "id": "rival-raw-stored",
        "kind": "uniqueness",
        "expect": "reject",
        # The exact pre-change behaviour (Solution_prepatch.lean, refinement.md
        # §A): a read-only slot uses its RAW stored value directly, WITHOUT the
        # coarse-exposure sub-count drop that `initialFor` performs. Correct on
        # any slot that is not (read-only AND coarse), or whose stored sub-count
        # is already 0; wrong exactly on a read-only + coarse slot carrying a
        # non-zero sub-count — precisely the F2P input.
        "module": _map(
            "if f.readOnly then f.stored else f.given"),
        "refinement": (
            "this is the pre-patch code itself: for a disabled (read-only) field "
            "it uses the raw resolved stored value directly, skipping the "
            "bound-field exposure that drops the finer sub-count on a coarse "
            "widget. On the F2P input the disabled field's stored value carries a "
            "non-zero sub-count (the microsecond-bearing datetime) and its widget "
            "is coarse, so the cleaned value keeps the sub-count while the "
            "post-image drops it; the F2P assertion (the cleaned value matches the "
            "bound field's cached, normalized initial) FAILS -> does not resolve. "
            "This is exactly the defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (`out = cleanedSeq fields`): `cleanedSeq` routes a "
            "read-only slot through `initialFor`, which for a coarse slot zeroes "
            "the sub-count, so a rival returning the raw stored value diverges "
            "from the post-image on any read-only+coarse slot with a non-zero "
            "sub-count. Refuted at a single read-only+coarse slot whose stored "
            "sub-count is 1. Ports nagini partial-domain-unnormalised-first. If it "
            "verified => SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness(f"[{_F('true', 'true', _S(45, 1), _S(0, 0))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-ignore-readonly-given",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the readOnly branch SELECTOR: always resolve the data-supplied
        # value `f.given`, ignoring that a read-only slot must use its exposed
        # stored value. Correct on any non-read-only slot, and on a read-only
        # slot only when given happens to equal initialFor; wrong on a read-only
        # slot whose supplied value differs from its exposed stored value.
        "module": _map("f.given"),
        "refinement": (
            "resolves every slot from the data-supplied value, dropping the "
            "distinction that a disabled field takes its value from its own "
            "resolved initial rather than from submitted data. A faithful real "
            "patch of this shape would clean a disabled field from (absent) form "
            "data instead of its bound initial; the F2P submits an empty data "
            "dict for a disabled field, so the cleaned value would be the empty "
            "data value, not the datetime initial -> the F2P equality assertion "
            "FAILS, does not resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = cleanedSeq fields`): `cleanedSeq` selects "
            "`initialFor f` on a read-only slot, so a rival always returning "
            "`f.given` diverges whenever a read-only slot's given value differs "
            "from its exposed stored value. Refuted at a read-only (non-coarse) "
            "slot with stored != given — a distinct binder (the readOnly branch "
            "selector) and a distinct input point from rival-raw-stored, so the "
            "battery varies the readOnly/stored/given binders. If it verified => "
            "SPEC-TOO-WEAK (the read-only selector is unpinned)."
        ),
        "witness": _witness(f"[{_F('true', 'false', _S(45, 0), _S(7, 7))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-ignore-readonly-initial",
        "kind": "uniqueness",
        "expect": "reject",
        # The MIRROR of the previous rival on the same selector binder: always
        # resolve the exposed stored value (initialFor), ignoring that a
        # non-read-only slot must use the data-supplied value. Correct on any
        # read-only slot; wrong on a non-read-only slot whose given value differs
        # from its exposed stored value. Refuted at a NON-read-only slot, the
        # opposite side of the readOnly split from the previous rival.
        "module": _map(
            "if f.coarse then { f.stored with sub := 0 } else f.stored"),
        "refinement": (
            "resolves every slot from its exposed stored value, dropping the "
            "distinction that an ENABLED field takes its value from submitted "
            "data. A faithful real patch of this shape would clean an enabled "
            "field from its initial instead of the submitted data; any form whose "
            "enabled field's submitted value differs from its initial would then "
            "clean to the wrong value, so the enabled-field PASS_TO_PASS suites "
            "(e.g. changed-data and disabled-fields tests) would FAIL -> does not "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = cleanedSeq fields`): `cleanedSeq` selects "
            "`f.given` on a NON-read-only slot, so a rival always returning "
            "`initialFor f` diverges whenever a non-read-only slot's given value "
            "differs from its exposed stored value. Refuted at a non-read-only "
            "slot with stored != given — the opposite side of the readOnly split "
            "from rival-ignore-readonly-given, exercising readOnly=false. If it "
            "verified => SPEC-TOO-WEAK (the enabled selector is unpinned)."
        ),
        "witness": _witness(f"[{_F('false', 'false', _S(45, 0), _S(7, 7))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the LIST TRAVERSAL: resolve only the FIRST slot, dropping the
        # rest of the list. Correct on any input of length <= 1 (and on the empty
        # list); wrong on any list of length >= 2. Varies the list-length binder,
        # which every other witness holds at length 1.
        "module": _impl(
            "    match fields with\n"
            "    | [] => return []\n"
            "    | f :: _ => return [slotValue f]"),
        "refinement": (
            "resolves only the first field of the form and discards every "
            "subsequent field. A faithful real patch that cleaned only the first "
            "field would leave the remaining fields absent from the cleaned data; "
            "essentially every multi-field form test (the bulk of the "
            "PASS_TO_PASS suite) would then FAIL -> does not resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = cleanedSeq fields`): `cleanedSeq` maps EVERY "
            "slot, so `out` must have the input's length; a rival returning a "
            "one-element list diverges on any input of length >= 2. Refuted at a "
            "TWO-slot list — the only witness that varies the list-length binder "
            "(every other witness is length 1), so the traversal is defended, not "
            "just the per-slot resolution. If it verified => SPEC-TOO-WEAK (the "
            "traversal/length is unpinned)."
        ),
        "witness": _witness(
            f"[{_F('false', 'false', _S(1, 0), _S(1, 0))}, "
            f"{_F('false', 'false', _S(2, 0), _S(2, 0))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the traversal ORDER, the one C1 binder the four rivals above
        # leave unattacked. Every per-slot value is resolved CORRECTLY and the
        # output has the right LENGTH and the right multiset of values — only the
        # position-to-slot correspondence is inverted. rival-head-only varies the
        # length but not the order (its output is a prefix, in order), so an impl
        # that is right per-slot and right in length while wrong in ORDER is a
        # distinct wrong shape: it is the one this battery could otherwise admit.
        # Correct on inputs of length <= 1 and on any palindromic value sequence;
        # wrong on the first list whose resolved values are not symmetric.
        "module": _impl(
            "    return ((fields.map (fun f => slotValue f)).reverse)"),
        "refinement": (
            "resolves each field's value correctly but writes the cleaned values "
            "back against the form's field order. A faithful real patch of this "
            "shape would associate each cleaned value with the WRONG field name, "
            "so every multi-field form would validate one field's submitted value "
            "against another field's slot; the multi-field PASS_TO_PASS suites "
            "would FAIL -> does not resolve. Distinct from the head-only rival: "
            "nothing is dropped and no value is mis-resolved, so length- and "
            "value-level checks alone would not catch it."
        ),
        "rationale": (
            "REJECT from C1 (`out = cleanedSeq fields`): `cleanedSeq` is defined "
            "front-recursively (`cleanedSeq (f :: fs) = slotValue f :: cleanedSeq "
            "fs`), so C1 pins the value at each POSITION, not merely the length or "
            "the collection of values. A rival returning the reversed list agrees "
            "with C1 on length and on the multiset of resolved values and still "
            "diverges at every non-symmetric input. Refuted at a two-slot list "
            "whose two resolved values differ — the ORDER binder, which no other "
            "rival varies (head-only truncates but preserves order). If it "
            "verified => SPEC-TOO-WEAK (position/order unpinned: C1 would be only "
            "a multiset pin)."
        ),
        "witness": _witness(
            f"[{_F('false', 'false', _S(1, 0), _S(1, 0))}, "
            f"{_F('false', 'false', _S(2, 0), _S(2, 0))}]"),
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                        -> here
#   -----------------------------------------------------------------------
#   pos-control-inline-normalise       -> pos-control-inline-normalise  PORTED
#   pos-control-direct                 -> pos-control-direct            PORTED
#   admiss-f2p-shaped-input            -> admiss-gold-total             RE-AIMED+STRENGTHENED
#   partial-domain-unnormalised-first  -> rival-raw-stored              PORTED
#   (no direct sibling)                -> rival-ignore-readonly-given   ADDED
#   (no direct sibling)                -> rival-ignore-readonly-initial ADDED
#   (no direct sibling)                -> rival-head-only               ADDED
#   (no direct sibling)                -> rival-reversed-order          ADDED (audit)
#   frame-mutate-first-eval            -> (none)                        VACUOUS
#   weak-diverge-reject                -> (none)                        WITNESS-LIMITED
#   pre-patch-fresh-reeval             -> (none)                        NO CARRIER
#   dead-fresh-reeval-then-correct     -> (none)                        NO CARRIER
#   partial-domain-max-mix             -> (none)                        NO CARRIER
#   AXIOM_TESTS ([])                   -> (none)                        N/A
#
# 8 velvet SPEC cases: 2 soundness + 1 admissibility + 5 uniqueness. The nagini
# file has 9 cases; the difference is carrier narrowing (the fresh_eval axis),
# NOT omitted difficulty — see NO CARRIER below.
#
# PORTED (pos-control-inline-normalise, pos-control-direct,
#   partial-domain-unnormalised-first): these carry across with only a carrier
#   change (nagini single-int fs -> velvet List FieldSlot / Stamp). The inline
#   positive unfolds the resolution arithmetic in the loop; the direct positive
#   returns the grounded fold; rival-raw-stored is the pre-patch bug (skip the
#   coarse sub-count drop), now backed by a machine-checked witness at a
#   read-only+coarse slot.
# RE-AIMED + STRENGTHENED (admiss-f2p-shaped-input -> admiss-gold-total): the
#   nagini case established the read-only fractional-permission precondition on an
#   F2P-shaped input. This method has no `require` and no heap permission, so that
#   half has no counterpart; re-aimed at the total-carrier analogue — the
#   obligation being SATISFIABLE at exactly an F2P-shaped input. The second audit
#   found the case was carrying `module = _BASE`, the frozen file verbatim, which
#   only re-runs the frozen build (G-VERIFY/G-GOLD already record that) and is a
#   hollow positive. Repaired: the case now discharges the post-image AT the F2P
#   shape by evaluation (`decide`) as a `have`, plus two non-degeneracy `have`s
#   (the sub-count drop MOVES the value; the enabled branch really reads `given`),
#   before closing the frozen obligation verbatim. Measured load-bearing by three
#   negative controls, each corrupting one `have` and each failing to build.
# ADDED (4): rival-ignore-readonly-given and rival-ignore-readonly-initial attack
#   the readOnly branch SELECTOR from both sides (always-given vs always-initial),
#   each refuted at the side of the readOnly split it gets wrong; rival-head-only
#   attacks the list TRAVERSAL, refuted at a length-2 list. The nagini single-
#   field model has no list to traverse and pins its single value by two
#   equivalent oracle clauses, so these C1 binders (the branch selector on both
#   sides, the traversal) have no nagini rival; here each is a concrete
#   witnessable C1 divergence at a distinct input. Real divergences with checked
#   witnesses, not fabricated wrongness.
# VACUOUS — frame-mutate-first-eval: Velvet is referentially transparent, `fields`
#   is immutable, no `mut` binder, no heap/aliasing/permission system. No
#   read-only input to overwrite. No substitute fabricated.
# WITNESS-LIMITED (weak-diverge-reject): this bundle runs under `total` semantics
#   (not `partial`, which no velvet bundle sets), so the verifier DOES discharge a
#   termination obligation and a diverging rival is genuinely rejected by the
#   spec. Vacuous satisfaction is the `partial` disposition and does not arise
#   here. The second audit
#   WITHDREW this entry's earlier "VACUOUS / unwritable" claim: a diverging impl
#   IS writable (a second `while spin > 0` holding the measure constant after the
#   correct value is computed) and rejects with the termination obligation as the
#   residual goal (`case «decreasing_1: spin» … ⊢ 1 < spin`). It is still not
#   SHIPPED, on measured witness-side grounds: a diverging rival's extracted
#   `cleanFieldsExec` has no `DivM.res` normal form, so `decide` is STUCK against
#   the RIVAL too (witness-vs-rival exit 1 by stuck reduction — the half that must
#   succeed), which the gate records as `witness-unproven`, an inconclusive
#   outcome. Landing it would fail the gate, not strengthen it. Recorded as a
#   known witness-side limitation of the divergence lane on this carrier.
# NO CARRIER (pre-patch-fresh-reeval, dead-fresh-reeval-then-correct,
#   partial-domain-max-mix): all three nagini rivals abuse a SECOND, independent
#   evaluation of a stateful source (`fs.fresh_eval`), whose defining property is
#   that it disagrees with the cached first evaluation. This velvet carrier models
#   a single resolved stored value per slot (`f.stored`, "evaluated once and
#   cached", mapping.md §1); there is no second-evaluation term any impl over this
#   carrier could read or return. So there is no wrong impl to write for this axis
#   and no discriminating witness to author — the distinction the nagini rivals
#   exploit is COLLAPSED by the abstraction, not omitted. This is legitimate
#   carrier narrowing (the Lean-family bundles model only the purely functional
#   core; the stateful re-evaluation behaviour is unmodeled here), stated
#   explicitly rather than papered over with a fabricated substitute.
# AXIOM_TESTS: the nagini file ships none (meta.axioms == []); the
#   initialFor==BoundField.initial deep model is an A-reference (G-AX /
#   axiom_check.py), not a consumed axiom, and G-PBT ignores AXIOM_TESTS anyway.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause C1
#   (`out = cleanedSeq fields`) is DEFENDED by both positives and the
#   admissibility case (all discharge on gold) and ATTACKED by four rivals across
#   its input binders:
#     * `coarse` (the sub-count drop on the exposed stored value) — rival-raw-stored;
#     * `readOnly` branch selector, BOTH sides — rival-ignore-readonly-given
#       (readOnly=true side) and rival-ignore-readonly-initial (readOnly=false side);
#     * `stored` vs `given` — both selector rivals refute at inputs where stored != given;
#     * list length / traversal — rival-head-only, the only length-2 witness.
#     * traversal ORDER — rival-reversed-order (added by the audit): correct
#       per-slot values, correct length, correct multiset, inverted positions.
#       Without it C1's position-level content was attested only indirectly, since
#       head-only truncates in order and every other rival is length-1 (where
#       order is trivial); an impl right per-slot and right in length but wrong in
#       order was the one wrong shape the battery did not attack.
#   The five reject witnesses probe FOUR distinct input points: a read-only+coarse
#   length-1 slot, a read-only non-coarse length-1 slot, a non-read-only length-1
#   slot, and a non-read-only length-2 list (shared by head-only and
#   reversed-order, which are refuted by DIFFERENT divergences at it: a missing
#   tail vs a transposition) — so readOnly takes both values, coarse takes both
#   values, stored/given differ on two points, and list length takes 1 and 2. No
#   binder is held fixed by every witness.
#
# WITNESS MECHANICS (corrected by the audit): C1's post-image `cleanedSeq` is
#   TRANSPARENT (no opaque axiom in the clause), so — unlike the django-11276
#   sibling where the tester+`decide` path is dead — `decide` reduces a LOOP-FREE
#   impl's extracted program directly. Every rival is loop-free, so its `…Exec`
#   reduces and the witness ELABORATES against it. But gold is NOT usable as the
#   second subject: the frozen impl is the `while` loop, whose `…Exec` elaborates
#   through `Classical.choice` under `demonic` choice, so `decide` against gold is
#   STUCK ("instDecidableNot did not reduce to `isTrue` or `isFalse` … stuck at
#   `.hasDecEq`") for EVERY claim about gold, true or false. Confirmed three ways:
#   `decide`, `decide +kernel`, and `#reduce` (which exhibits the residual
#   `Classical.choice` term). A gold exit code obtained that way attests to a
#   refutation the kernel never performed — the `witness-undecided` class in
#   gates/pbt.py — so every reject case names an explicit `witness_reference`
#   (`_REFERENCE`: a loop-free `fields.map slotValue` impl of the same frozen
#   spec, checked by the gate to share the spec view and to VERIFY). Against it
#   each witness fails SEMANTICALLY ("`decide` proved that the proposition … is
#   false"), which is the discrimination the record now claims. No witness binds a
#   hypothesis, so none can be inconsistent and no consistency probe is needed.
#   Measured with scripts/lean_verify.sh: each rival module exit 1 (rejects),
#   witness-vs-rival exit 0 (elaborates), witness-vs-reference exit 1 by semantic
#   refutation; `_REFERENCE` itself exit 0 (verifies).
AXIOM_TESTS = []
