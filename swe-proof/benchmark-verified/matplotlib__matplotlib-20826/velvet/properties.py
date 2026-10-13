"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20826 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct resetAxisTickKeywords`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE. One contracted method that re-derives a single distinguished
entry of two total settings maps while leaving every other entry of both maps
untouched:

  resetAxisTickKeywords
      (mut majorKw : String → Bool) (mut minorKw : String → Bool)
      (key : String) (majorVal : Bool) (minorVal : Bool)  return (u : Unit)
    ensures majorKw key = majorVal                               (C1)
    ensures minorKw key = minorVal                               (C2)
    ensures ∀ k, k ≠ key → majorKw k = majorKwOld k              (C3)
    ensures ∀ k, k ≠ key → minorKw k = minorKwOld k              (C4)

FOUR independent, load-bearing top-level clauses over five free INPUT BINDERS
(``majorKw``, ``minorKw``, ``key``, ``majorVal``, ``minorVal``); no ``require``,
so the admitted domain is total:
  (C1)/(C2) the RECOMPUTE — the distinguished entry ``key`` of each map is set to
       the supplied recomputed value (``majorVal`` for the major map, ``minorVal``
       for the minor map). Grounded entirely in the method's own value inputs;
       there is no opaque answer key to echo (the ``axioms`` region is empty).
  (C3)/(C4) the FRAME — every OTHER entry of each map is preserved (same value on
       every ``k ≠ key``). This is the directive-5 frame on the two mutable
       binders, and it is the reported defect itself: a reset that discards the
       other entries un-hides the per-side visibility flags that linked/shared
       axes had turned off. The recompute writes the one entry IN PLACE, so the
       rest of each map survives.

CARRIER NOTE — the settings map is modeled as a TOTAL function ``String → Bool``,
so the frame clauses C3/C4 quantify ``∀ k : String`` and are UNDECIDABLE. Two
consequences shape every witness:

  * ``derive_tester_for`` needs a decidable postcondition; with ``∀ k : String``
    frame conjuncts it cannot synthesise the ``Decidable`` instance (measured:
    ``prove_postcondition_decidable_for`` leaves ``Decidable (∀ (k : String), …)``
    unsolved). So the sibling velvet ``…Tester args = false`` route is
    UNAVAILABLE on this carrier, exactly as on the opaque-``Vertex`` carrier of
    the collect-vertices bundle.
  * Even so, the post-state of each map is a concrete function value, and the
    map APPLIED at one probe entry is a decidable ``Bool``. Each witness
    ``extract_program_for``s the rival (extraction needs no decidability — it just
    names ``resetAxisTickKeywordsExec``) and states, at ONE concrete input, that
    the rival's post-state map read at one entry differs from what C1–C4 demand:

        ((resetAxisTickKeywordsExec majorKw minorKw key majorVal minorVal).run)
            .2.1 <probe-entry> = <wrong-Bool>

    (``.2.1`` = the major map component of the returned ``Unit × (String→Bool) ×
    (String→Bool)``, ``.2.2`` = the minor map), discharged by
    ``simp [NonDetT.run, DivM.run, Function.update]``. The frozen impl writes the
    entry in place (``Function.update majorKw …``), so the SAME probe reads the
    preserved/correct value there and the witness FAILS on gold — a genuine
    discriminator, not a tautology. Every witness binds NO hypotheses (all inputs
    are concrete literals / ``fun _ => …`` maps), so the consistency probe is
    trivially satisfiable; no opaque-term conditioning is needed.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION (the nagini MANDATORY rival) — VACUOUS as a
    PERMISSION attack. The nagini sibling holds ``tick_kw`` at
    ``Acc(dict_pred(tick_kw),1/2)`` and writes the read-only input to trip
    INSUFFICIENT PERMISSION. Lean/Velvet are referentially transparent: there is
    no heap, no aliasing and no fractional permission to trip. BUT the ARGUMENT
    behind that rival — a reset must not silently discard the map's other entries
    — is NOT lost here: it is captured directly by the value-level frame clauses
    C3/C4 on the two ``mut`` binders, and is attacked by the drop-frame rivals
    below. So the permission MECHANISM is vacuous; the behaviour it guarded is
    fully expressible and exercised.
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. C1–C4 are pinned to the
    method's own value inputs (``majorVal``/``minorVal``) and the framed old
    maps; there is no axiomatized answer key to echo (the ``axioms`` region is
    empty).
  * WRONG-CONJUNCTION (nagini ``_WRONG_OR`` / ``_PARTIAL_DOMAIN``) — NOT
    expressible here, and legitimately so. On nagini the recomputed grid value is
    ``flag_enabled and selection_covers`` COMPUTED inside the modeled function, so
    a rival could pin it to ``flag_enabled`` alone or to an ``or``. On this
    backend that ``rcParams`` conjunction is transliterated OUTSIDE the model and
    supplied as the input booleans ``majorVal``/``minorVal`` (an R/I leg checked
    by G-CONF, mapping.md §2/§4), so there is no conjunction inside the spec to
    weaken. The recompute VALUE is still attacked — by writing the WRONG supplied
    value at the entry (the wrong-value rivals), which is the on-carrier analogue.
  * PRESERVATION-DROPPER / SPURIOUS-KEY / PARTIAL-DOMAIN — APPLY, and are the
    reject surface: dropping the other entries of the major or minor map (the
    literal prepatch), injecting a spurious entry, or writing the wrong recomputed
    value at the distinguished entry.

WITNESS PLACEMENT. The five reject witnesses sit at five DISTINCT input points,
varying every meaningful binder: ``key`` over {"gridOn","tick1On"}, ``majorVal``
over {true,false}, ``minorVal`` over {true,false}, and the entry maps over
{all-true, all-false}. Each of the four clauses is attacked (C3 twice — by a
drop and by an injection, the two directions of the frame). No clause is
demonstrated at a single pinned input.

AXIOM lane: EMPTY. This bundle declares no ``axiom`` and no deep-model reference
(the whole operation is a pure ``Function.update`` on the carrier, whose frame is
Mathlib library knowledge); ``meta.json`` records G-AX = skip. There is nothing
here for this gate to probe, and it ignores ``AXIOM_TESTS`` regardless.

WHY SPEC-TOO-WEAK IS UNREACHABLE HERE (audit result, machine-checked). The four
clauses do not merely constrain the post-state, they PIN it: C1/C2 fix each map at
``key`` and C3/C4 fix each map at every other point, and a total function is
determined by its values everywhere. Proven as a standalone meta-theorem (exit 0):

    theorem post_unique (mo no m n : String → Bool) (key : String) (mv nv : Bool)
        (h : Post mo no m n key mv nv) :
        m = Function.update mo key mv ∧ n = Function.update no key nv

by ``funext`` and a case split on ``k = key``. So ANY impl that verifies is
observationally equal to the frozen one on every input, and no wrong impl can
verify within the modeled boundary — the reject lane below is exhaustive by
construction rather than by sampling. Nine independent wrong impls were tried
against a deliberately much stronger proof script (``rfl``/``decide``/``simp_all
[Function.update]``/``aesop``/case-split, in addition to the frozen lemmas) and all
nine were rejected on genuine semantic goals such as
``⊢ ∀ (k : String), ¬k = key → majorKwOld k = false``; none was a tactic artifact.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20826"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (marker lines included);
# ---- lies wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    majorKw := Function.update majorKw key majorVal\n"
    "    minorKw := Function.update minorKw key minorVal\n"
    "    return\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is elided from the consumer
# ---- spec view (only the obligation statement is kept), so a positive control
# ---- may retune it without touching the spec or dropping the obligation.
# ---- Unique in the file.
_GOLD_PROOF = (
    "prove_correct resetAxisTickKeywords by\n"
    "  loom_solve <;>\n"
    "    first\n"
    "      | exact Function.update_self _ _ _\n"
    "      | (intro k hk; exact Function.update_of_ne hk _ _)"
)
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced (frozen proof
    kept — used by rivals, whose rejection is carried by the witness)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes / the
    admissibility assert)."""
    return _swap(_impl(body), _GOLD_PROOF, new_proof)


# ---- witness preamble. Reaches the rival's extracted program (extraction needs
# ---- no decidability — it just names `resetAxisTickKeywordsExec`) and states,
# ---- at one concrete input, that the rival's post-state map read at one entry
# ---- differs from what the postcondition demands. Discriminated by a decidable
# ---- `Bool` read of the returned function value; checked in a file whose
# ---- `prove_correct` block is stripped. No `axiom`/`sorry`/`native_decide`.
def _witness(claim):
    return (
        "extract_program_for resetAxisTickKeywords\n\n"
        f"example : {claim} := by\n"
        "  unfold resetAxisTickKeywordsExec resetAxisTickKeywords\n"
        "  simp [NonDetT.run, DivM.run, Function.update]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify; else the spec is SPEC-TOO-STRONG. Each keeps the
    # two in-place updates (so all four clauses still discharge) and only reshapes
    # the executable surface, so the frozen tactic script still closes.
    # =====================================================================
    {
        "id": "pos-update-order-swapped",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: write the minor map's entry BEFORE the major map's. The two
        # updates are independent (different `mut` binders), so the post-state of
        # each map — and hence all four clauses — is identical on every input.
        "module": _impl(
            "    minorKw := Function.update minorKw key minorVal\n"
            "    majorKw := Function.update majorKw key majorVal\n"
            "    return"),
        "rationale": "writing the two independent map entries in the opposite "
                     "order leaves the post-state of each map identical on every "
                     "input (they touch disjoint `mut` binders), so C1–C4 still "
                     "discharge under the frozen script. If it failed to verify "
                     "the spec would be SPEC-TOO-STRONG on statement order.",
    },
    {
        "id": "pos-local-value-binding",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind each recomputed value to a typed local before the update.
        # Same value flow; the in-place updates are unchanged, so the frozen
        # proof still closes.
        #
        # AUDIT NOTE (weak-but-honest). This reshape and `pos-update-order-swapped`
        # are both DEFINITIONALLY equal to the frozen impl: each map's post-state is
        # the same `Function.update` term, so the frozen tactic script closes them
        # unchanged (measured: `(let x : Bool := v; Function.update m key x) =
        # Function.update m key v := rfl` elaborates, exit 0). They are real
        # soundness controls but weak ones — they cannot detect a spec that is too
        # strong on the SHAPE of the written map, only on statement order and value
        # binding. `pos-lambda-if-reshape` below is the non-defeq positive that
        # carries that weight; it is kept alongside these rather than replacing
        # them so the cheap controls still guard the cheap regressions.
        "module": _impl(
            "    let mv : Bool := majorVal\n"
            "    let nv : Bool := minorVal\n"
            "    majorKw := Function.update majorKw key mv\n"
            "    minorKw := Function.update minorKw key nv\n"
            "    return"),
        "rationale": "binding each recomputed value to a typed local before the "
                     "in-place update leaves the written value and the frame "
                     "identical, so C1–C4 are unchanged; a correct reshape must "
                     "verify, else SPEC-TOO-STRONG on value binding. Weak by "
                     "construction: definitionally equal to the frozen impl "
                     "(`rfl`-provable), so it is a regression guard rather than a "
                     "shape probe — see pos-lambda-if-reshape for the latter.",
    },
    {
        "id": "pos-lambda-if-reshape",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The battery's two shipped positives are both
        # DEFINITIONALLY equal to the frozen impl, so neither exercises the spec
        # against a genuinely different map SHAPE: the frozen script closes them
        # because the post-state term is literally unchanged. This positive writes
        # each map as an explicit branching lambda instead of `Function.update`.
        # Measured NOT defeq — `(fun k => if k = key then v else m k) =
        # Function.update m key v := rfl` FAILS with a type mismatch (exit 1) — so
        # the frozen `Function.update_self` / `Function.update_of_ne` script no
        # longer applies and the clauses must be re-discharged from the branch
        # structure (`simp` for C1/C2, `simp [hk]` under the `k ≠ key` hypothesis
        # for C3/C4). It is nonetheless the SAME total function pointwise, hence a
        # faithful correct impl: if the spec rejected it, the spec would be
        # SPEC-TOO-STRONG on the representation of the settings map rather than on
        # its observable content.
        "module": _impl_reproved(
            "    majorKw := fun k => if k = key then majorVal else majorKw k\n"
            "    minorKw := fun k => if k = key then minorVal else minorKw k\n"
            "    return",
            "prove_correct resetAxisTickKeywords by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "      | simp\n"
            "      | (intro k hk; simp [hk])"),
        "rationale": "a correct impl that builds each post-state map as an explicit "
                     "branching lambda rather than via `Function.update`. Pointwise "
                     "the same total function — the distinguished entry reads the "
                     "recomputed value and every other entry reads its old value — "
                     "so C1–C4 all hold, but the term is NOT definitionally the "
                     "frozen one (`rfl` between the two shapes fails), so the "
                     "clauses are re-proven from the branch structure instead of "
                     "reusing the frozen update lemmas. Must verify, else the spec "
                     "is SPEC-TOO-STRONG on how the map is represented. This is the "
                     "battery's only positive whose shape the frozen script does "
                     "not already close.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition, so the sibling's "a
    # normal F2P-shaped input satisfies the precondition" probe is degenerate
    # (every input is in-domain). Re-aimed at the residual total-domain risk: that
    # the recompute/frame is DEGENERATE at the interesting point — i.e. that
    # C1/C2 and C3/C4 could be jointly satisfied without the two actually
    # SEPARATING (the distinguished entry moving to the recomputed value while
    # every other entry stays put).
    #
    # AUDIT REPAIR (second pass). Two earlier forms of this assert were both
    # IMPL-INDEPENDENT, and the second failure mode is the subtle one worth
    # recording, because "mentions the binders" is what it was mistaken for.
    #
    # (1) The form first shipped was stated over closed literals
    #     (`Function.update (fun _ => false) "gridOn" true "gridOn" = true ∧ …`),
    #     mentioning none of the method's binders.
    # (2) The repair for (1) restated it over the binders but still over the
    #     UPDATE TERM, in PRE-state position:
    #
    #       Function.update majorKw key majorVal key = majorVal ∧ …
    #       (∀ k, k ≠ key → Function.update majorKw key majorVal k = majorKw k)
    #
    #     which is just `Function.update_self` / `Function.update_of_ne`
    #     instantiated at the binders — a Mathlib fact about `Function.update`,
    #     true whatever the impl below it does. Measured, and this is the evidence
    #     that matters: it elaborates as a STANDALONE `example` with no method, no
    #     impl and no spec anywhere in the file (exit 0); and planted inside the
    #     `drop-major-frame-prepatch` WRONG rival under a deliberately strong
    #     script it leaves ONLY the `ensures_2` goal unsolved — every `adm_1`
    #     subgoal CLOSES (exit 1 attributable entirely to the postcondition, not
    #     to the assert). So it would have discharged against any impl whatsoever,
    #     including the pre-patch one. Naming a binder is not the same as
    #     depending on it.
    #
    # Re-aimed at the POST-STATE program variables, AFTER the two updates, so the
    # assert is a claim about what the impl actually WROTE (`majorKw key =
    # majorVal`, and the frame against the `…Old` snapshots) rather than about the
    # `Function.update` term. Now genuinely impl-dependent and live, all measured
    # under a strong script (`simp_all [Function.update]` / `decide` / `aesop` on
    # every residual goal), so each failure attributes to the CLAIM and not to
    # tactic shape:
    #   * as shipped, on the frozen impl                        -> exit 0
    #   * same assert inside the drop-major WRONG rival          -> exit 1 on
    #     `adm_1 … refine_3` (the frame conjunct itself fails; contrast form (2),
    #     which closed all `adm_1` goals there)
    #   * `k ≠ key` guard dropped from a frame conjunct          -> exit 1 on
    #     `adm_1 … refine_3`
    #   * recompute conjunct flipped to `!majorVal`              -> exit 1 on
    #     `adm_1 … refine_1`
    # The impl is kept verbatim so C1–C4 still discharge; the proof is extended to
    # close the assert VC from the same two update lemmas.
    #
    # WHY THIS IS THE ADMISSIBILITY LANE on a carrier with no `require`. The
    # analogue of PRECOND-TOO-STRONG on a total carrier is the obligation being
    # unsatisfiable at an F2P-shaped input, so this discharges C1-C4's own
    # conjunction at the reset point, in-region, as a `have`-style assert, before
    # the frozen obligation closes verbatim — if the four clauses could not be
    # jointly met by a real reset, this goal is where it would surface.
    # =====================================================================
    {
        "id": "admiss-recompute-frame-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    majorKw := Function.update majorKw key majorVal\n"
            "    minorKw := Function.update minorKw key minorVal\n"
            "    assert (with_name_prefix `adm\n"
            "      (majorKw key = majorVal ∧ minorKw key = minorVal ∧\n"
            "       (∀ k, k ≠ key → majorKw k = majorKwOld k) ∧\n"
            "       (∀ k, k ≠ key → minorKw k = minorKwOld k)))\n"
            "    return",
            _GOLD_PROOF
            + "\n      | (refine ⟨Function.update_self _ _ _, Function.update_self _ _ _, ?_, ?_⟩ <;>"
              "\n          (intro k hk; exact Function.update_of_ne hk _ _))"),
        "rationale": "the four clauses are JOINTLY SATISFIABLE by a real reset, "
                     "discharged in-region at the reset point over the POST-STATE "
                     "program variables: after the two writes the distinguished "
                     "entry of each map reads the recomputed value "
                     "(`majorKw key = majorVal`, `minorKw key = minorVal`) while "
                     "every other entry still reads its pre-state snapshot "
                     "(`∀ k, k ≠ key → majorKw k = majorKwOld k`, and the minor "
                     "dual) — the recompute-plus-frame separation a reset must make. "
                     "On a carrier with no `require` this is the admissibility "
                     "obligation: PRECOND-TOO-STRONG surfaces here as C1–C4 being "
                     "unsatisfiable at an F2P-shaped reset, and this goal is where "
                     "that would appear. Stated over the post-state rather than over "
                     "the `Function.update` TERM because the term-level form is "
                     "`Function.update_self`/`_of_ne` at the binders — a library "
                     "fact that discharges against any impl (measured: it closes "
                     "standalone with no method in the file, and closes inside the "
                     "drop-major wrong rival). Impl-dependence and liveness both "
                     "measured under a strong script: this form FAILS on `adm_1` "
                     "inside that same wrong rival, and fails if the `k ≠ key` guard "
                     "is dropped or the recomputed value is flipped.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a reshaped impl carrying a machine-checked
    # refutation witness at a DISTINCT concrete input (discriminated by a decidable
    # Bool read of the returned map) and the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "drop-major-frame-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE prepatch on the major map: blank the whole map to its default
        # (every entry `false`) then set only the distinguished entry. C1 still
        # holds (the entry is set correctly); C3's frame is violated for every
        # previously-true non-key entry.
        "module": _impl(
            "    majorKw := Function.update (fun _ => false) key majorVal\n"
            "    minorKw := Function.update minorKw key minorVal\n"
            "    return"),
        "refinement": "this IS the pre-patch behaviour: the major map is blanked "
                      "to its default before the distinguished entry is written, "
                      "so every other entry — including the per-side visibility "
                      "flags a linked/shared axis had turned off — is discarded and "
                      "reverts to shown. The failing render-equality test observes "
                      "exactly those flags reappearing, so it still fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT from C3 (`∀ k ≠ key → majorKw k = majorKwOld k`): "
                     "blanking the map drops every previously-set non-key entry. "
                     "Refuted at all-true entry maps, key=\"gridOn\", vals "
                     "true/true, where the preserved entry \"tick1On\" must stay "
                     "true but the rival returns false.",
        "witness": _witness(
            '((resetAxisTickKeywordsExec (fun _ => true) (fun _ => true) '
            '"gridOn" true true).run).2.1 "tick1On" = false'),
    },
    {
        "id": "drop-minor-frame-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The prepatch on the MINOR map (the symmetric half): blank the minor map
        # then set only the distinguished entry. Attacks C4 — the independent
        # frame clause on the OTHER mutable binder — so a battery that only dropped
        # the major map would never notice a reset that dropped the minor map.
        "module": _impl(
            "    majorKw := Function.update majorKw key majorVal\n"
            "    minorKw := Function.update (fun _ => false) key minorVal\n"
            "    return"),
        "refinement": "the pre-patch behaviour on the minor map: it is blanked "
                      "before the distinguished entry is written, so the minor "
                      "map's own previously-set entries are discarded on reset — "
                      "the same class of regression as the major-map drop, on the "
                      "independent minor settings map. The failing render-equality "
                      "test observes the dropped minor-map flags reappearing. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C4 (`∀ k ≠ key → minorKw k = minorKwOld k`): "
                     "blanking the minor map drops its previously-set non-key "
                     "entries. Refuted at a DISTINCT input (major map all-false, "
                     "minor map all-true, vals false/false), where the preserved "
                     "minor entry \"label1On\" must stay true but the rival returns "
                     "false — the independent frame binder no major-drop rival "
                     "attacks.",
        "witness": _witness(
            '((resetAxisTickKeywordsExec (fun _ => false) (fun _ => true) '
            '"gridOn" false false).run).2.2 "label1On" = false'),
    },
    {
        "id": "wrong-major-value",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on the recompute VALUE: write the MINOR recomputed value
        # into the major map's distinguished entry (a patch that used the wrong
        # side's computation for the major map). The frame C3 still holds; only C1
        # is violated, and only when the two recomputed values differ.
        "module": _impl(
            "    majorKw := Function.update majorKw key minorVal\n"
            "    minorKw := Function.update minorKw key minorVal\n"
            "    return"),
        "refinement": "a counterpart that writes the wrong side's recomputed grid "
                      "value into the major map's distinguished entry sets the "
                      "major grid state incorrectly whenever the two sides' "
                      "recomputed values differ (e.g. grid enabled for one side "
                      "only). The grid-recompute P2P tests (which enable the grid "
                      "and assert the per-side state) then diverge. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 (`majorKw key = majorVal`): the rival writes "
                     "`minorVal` at the major entry. Refuted at all-false maps, "
                     "key=\"gridOn\", majorVal=true, minorVal=false, where C1 "
                     "demands the major entry be true but the rival returns "
                     "false — a point separating majorVal from minorVal that the "
                     "frame rivals hold correct.",
        "witness": _witness(
            '((resetAxisTickKeywordsExec (fun _ => false) (fun _ => false) '
            '"gridOn" true false).run).2.1 "gridOn" = false'),
    },
    {
        "id": "wrong-minor-value",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual on C2: write the MAJOR recomputed value into the minor map's
        # distinguished entry. Also VARIES the `key` binder (uses "tick1On" as the
        # distinguished entry) so no witness pins `key` to "gridOn".
        "module": _impl(
            "    majorKw := Function.update majorKw key majorVal\n"
            "    minorKw := Function.update minorKw key majorVal\n"
            "    return"),
        "refinement": "the dual counterpart writes the wrong side's recomputed "
                      "value into the minor map's distinguished entry, setting the "
                      "minor grid state incorrectly whenever the two sides' values "
                      "differ. The grid-recompute P2P tests then diverge on the "
                      "minor side. It would NOT resolve.",
        "rationale": "REJECT from C2 (`minorKw key = minorVal`): the rival writes "
                     "`majorVal` at the minor entry. Refuted at all-false maps, "
                     "key=\"tick1On\", majorVal=true, minorVal=false — a DISTINCT "
                     "key value (varying the `key` binder) where C2 demands the "
                     "minor entry be false but the rival returns true.",
        "witness": _witness(
            '((resetAxisTickKeywordsExec (fun _ => false) (fun _ => false) '
            '"tick1On" true false).run).2.2 "tick1On" = true'),
    },
    {
        "id": "spurious-major-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # SPURIOUS-KEY (the OTHER direction of the frame on C3): set the entry
        # correctly AND preserve the rest, but ALSO flip an extra non-key entry
        # that was not set on entry. C1 holds; C3 is violated at the injected
        # entry. Where the drop rival flips a true entry to false, this flips a
        # false entry to true — the complementary frame violation.
        "module": _impl(
            "    majorKw := Function.update (Function.update majorKw key majorVal) "
            "\"tick2On\" true\n"
            "    minorKw := Function.update minorKw key minorVal\n"
            "    return"),
        "refinement": "a counterpart that injects an appearance entry the caller "
                      "never set (turning a side-visibility flag ON that was off) "
                      "un-hides a tick side that should stay hidden after reset — "
                      "the same visible regression the fix removes, in the opposite "
                      "direction to the drop. The failing render-equality test "
                      "observes the spurious tick. It would NOT resolve.",
        "rationale": "REJECT from C3 (`∀ k ≠ key → majorKw k = majorKwOld k`): the "
                     "rival flips the non-key entry \"tick2On\" from its old value. "
                     "Refuted at all-false maps, key=\"gridOn\", vals true/true, "
                     "where C3 demands \"tick2On\" stay false but the rival returns "
                     "true — the frame's injection direction the drop rivals do not "
                     "exercise.",
        "witness": _witness(
            '((resetAxisTickKeywordsExec (fun _ => false) (fun _ => false) '
            '"gridOn" true true).run).2.1 "tick2On" = true'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 4 uniqueness
# rivals) plus 2 AXIOM_TESTS. The sibling contracts TWO structurally-identical
# functions (reinit_tick_kw_major / _minor), each taking a read-only
# Dict[int,bool] at half-permission and RETURNING a fresh dict, with the grid
# value COMPUTED inside as `flag_enabled and selection_covers`. This bundle
# collapses the two functions into ONE method mutating BOTH settings maps in
# place (`mut majorKw` / `mut minorKw`), models each map as a total `String →
# Bool`, and — crucially — supplies the recomputed grid value as INPUT booleans
# `majorVal`/`minorVal` (the `rcParams` conjunction is transliterated OUTSIDE the
# model, an R/I leg checked by G-CONF), so the in-function conjunction the
# sibling's value rivals attack does not exist here. Every sibling case is
# accounted for below.
#
#   sibling case (nagini)              -> here                            disposition
#   -----------------------------------------------------------------------------
#   pos-local-binding                   -> pos-local-value-binding         PORTED
#   pos-commuted-and                    -> pos-update-order-swapped        RE-SHAPED
#   (no sibling counterpart)            -> pos-lambda-if-reshape           ADDED (audit:
#                                          the only non-defeq positive)
#   admiss-f2p-shaped-input             -> admiss-recompute-frame-...      RE-AIMED
#   frame-mutation-write-input (MAND)   -> (none as permission attack;     VACUOUS-MECH
#                                          behaviour -> drop-*-frame)
#   drop-other-keys-prepatch            -> drop-major-frame-prepatch +
#                                          drop-minor-frame-prepatch       PORTED (split)
#   partial-domain-ignore-selection     -> wrong-major-value              RE-AIMED
#   spurious-extra-key                  -> spurious-major-entry            PORTED
#   wrong-conjunction-or                -> (none)                          VACUOUS
#   (no sibling counterpart)            -> wrong-minor-value              ADDED (C2 + key binder)
#
# 5 ported/re-shaped, 1 re-aimed, 2 vacuous, 2 added (one by the audit).
#
# VACUOUS-MECH (frame-mutation-write-input, MANDATORY on nagini): the sibling's
#   rival writes the read-only input dict held at Acc(dict_pred,1/2) to trip
#   INSUFFICIENT PERMISSION before any postcondition is considered. This backend
#   is referentially transparent — no heap, no aliasing, no fractional
#   permission — so the permission MECHANISM is vacuous. But the BEHAVIOUR that
#   rival guarded (a reset must not silently discard the map's other entries) is
#   NOT lost: it is captured directly by the value-level frame clauses C3/C4 on
#   the two `mut` binders and is attacked by drop-major-frame-prepatch /
#   drop-minor-frame-prepatch (and, in the opposite direction, spurious-major-
#   entry). So the class is not fabricated and not silently dropped — its
#   mechanism is vacuous, its behaviour fully exercised.
#   AUDIT (demonstrated, not asserted). Two builds pin this down rather than
#   arguing it. (a) The only on-carrier act resembling "write the read-only
#   input" is assigning a non-`mut` binder, and that is not a rejected PROGRAM but
#   a non-program: `key := "gridOn"` fails to elaborate with "`key` cannot be
#   mutated, only variables declared using `let mut` can be mutated" — a parse/
#   scope error, so there is no impl here whose rejection could attribute to the
#   spec. (b) The distinction the nagini rival turns on — mutate in place versus
#   return a fresh copy — does not exist on this carrier: `Function.update m key v
#   = Function.update (fun k => m k) key v := rfl` elaborates (exit 0), i.e. the
#   in-place write and the copy-then-write denote the SAME value. A rival built on
#   that difference would be definitionally equal to gold and therefore vacuous by
#   attack C, not merely unlandable.
# VACUOUS (wrong-conjunction-or / the OR half of partial-domain): on nagini the
#   grid value is `flag_enabled and selection_covers` COMPUTED inside the modeled
#   function, so a rival could pin it to `or` or to one flag alone. On this
#   backend that `rcParams` conjunction is transliterated OUTSIDE the model and
#   handed in as the input booleans `majorVal`/`minorVal` (mapping.md §2/§4,
#   checked by G-CONF, NOT by this gate) — there is no in-spec conjunction to
#   weaken, so an `and`->`or` rival has no counterpart on this carrier. The
#   recompute VALUE is still attacked, by writing the WRONG supplied value at the
#   distinguished entry (wrong-major-value / wrong-minor-value), which is the
#   faithful on-carrier analogue of the partial-domain value break. Reported, not
#   fabricated.
#   AUDIT: confirmed by construction. `majorVal`/`minorVal` are opaque Bool INPUT
#   binders, so there is no `and` inside the spec for an `and`->`or` rival to
#   weaken. The nearest on-carrier reconstruction — writing `majorVal || minorVal`
#   at both entries — was built and is REJECTED on the semantic goal
#   `⊢ majorVal = true → minorVal = true` (exit 1), i.e. it is simply a third
#   wrong-value rival at the same clauses C1/C2 that wrong-major-value and
#   wrong-minor-value already attack, not a new class. Not added: it would raise
#   the case count without touching an unprobed clause or binder.
# RE-AIMED (admissibility): the sibling self-calls the function on an F2P-shaped
#   input to establish the half-permission precondition. This method has NO
#   precondition, so that probe is degenerate. Re-aimed at the residual
#   total-domain risk — that the recompute/frame is degenerate at the interesting
#   point — via an in-region assert that the in-place update sets the
#   distinguished entry to the recomputed value AND leaves every non-key entry
#   unchanged. AUDIT (two passes): the form originally shipped was stated over
#   closed literals, and its first repair restated it over the binders but still
#   over the `Function.update` TERM in pre-state position — which is just
#   `Function.update_self`/`_of_ne` instantiated, and was measured to close both
#   standalone (no method in the file) and inside the drop-major WRONG rival, so
#   neither form demonstrated anything about the impl. It is now stated over the
#   POST-STATE program variables after the writes, which is impl-dependent (it
#   FAILS on `adm_1` inside that wrong rival) and live (fails if the `k ≠ key`
#   guard is dropped or the recomputed value flipped), all under a strong script.
#   See the case.
# PORTED-SPLIT (drop-*-frame-prepatch): the sibling's single prepatch rival
#   empties the one returned dict. This bundle mutates TWO maps under two
#   independent frame clauses (C3 major, C4 minor), so the prepatch is split into
#   a major-drop (attacks C3) and a minor-drop (attacks C4) at distinct inputs —
#   without both, a reset that dropped only the un-attacked map would verify.
# ADDED (wrong-minor-value): the dual of wrong-major-value, attacking C2 and — by
#   using "tick1On" as the distinguished `key` — VARYING the `key` binder so no
#   witness pins it to "gridOn".
#
# CLAUSE / BINDER COVERAGE. All four independent top-level clauses are attacked:
#   C1 by wrong-major-value; C2 by wrong-minor-value; C3 by drop-major-frame-
#   prepatch AND spurious-major-entry (the drop and injection directions of the
#   frame); C4 by drop-minor-frame-prepatch. All four are defended by the three
#   positive controls and the admissibility case. The five reject witnesses probe
#   FIVE DISTINCT inputs (pts=5):
#     majorKw    minorKw    key       majorVal minorVal   case
#     all-true   all-true   gridOn    true     true       drop-major-frame-prepatch
#     all-false  all-true   gridOn    false    false      drop-minor-frame-prepatch
#     all-false  all-false  gridOn    true     false      wrong-major-value
#     all-false  all-false  tick1On   true     false      wrong-minor-value
#     all-false  all-false  gridOn    true     true       spurious-major-entry
#   so `key` is varied over {gridOn, tick1On}, `majorVal` over {true, false},
#   `minorVal` over {true, false}, and the entry maps over {all-true, all-false} —
#   no binder is pinned across the battery. The two drop rivals fail for the same
#   reason on DIFFERENT maps (C3 vs C4), the two wrong-value rivals on different
#   clauses (C1 vs C2), and the spurious rival attacks C3 in the opposite
#   direction to the major drop — so no rival is a near-miss of another sharing an
#   input.
#
# WITNESS FORM. The tester route is UNAVAILABLE (the `∀ k : String` frame clauses
#   are undecidable, so `derive_tester_for` cannot synthesise a decidable
#   postcondition — measured). So each witness `extract_program_for`s the rival
#   and reads the returned post-state map at ONE probe entry (a decidable `Bool`),
#   asserting it differs from what the postcondition demands. Confirmed
#   empirically with scripts/lean_verify.sh: each witness ELABORATES against its
#   rival (`simp [NonDetT.run, DivM.run, Function.update]` closes it) and FAILS
#   against the frozen solution (the in-place update reads the preserved/correct
#   value at that entry, leaving `⊢ False`) — the required discrimination; each
#   rival module does NOT verify (the frozen `Function.update_self` /
#   `Function.update_of_ne` script no longer matches the reshaped impl).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` and no deep-model reference (the whole operation is a pure
#   `Function.update` whose frame is Mathlib library knowledge; meta.json records
#   G-AX = skip), so there is nothing here to probe and the gate ignores it.
AXIOM_TESTS = []
