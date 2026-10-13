"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9673 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct augmentTypeFields`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec — here a named ``witness_reference``
rather than the frozen solution, which cannot decide anything; see WITNESS
MECHANICS).

DEFENDED SURFACE (one contracted method):

  augmentTypeFields (fields : List (List Tok)) (annotations : List (Tok × Tok))
      return (out : List Field)
    ensures out = buildFields fields annotations                          -- C1

The method augments a documented entity's info-field list with the type fields
implied by its recorded annotations. First every existing field is classified by
the leading token of its name into two membership sets (which keys carry a
description, which carry a declared type); a result-description field is
recognized under EITHER accepted spelling. Then, for each annotation in order, a
parameter that has a description but no declared type gains a type field;
finally, if the result is annotated, described, and untyped, a trailing
result-type field is appended. The whole appended sequence is the pure
``def buildFields`` (built from ``classifyField`` / ``emitStep`` / ``rtypeField``
/ ``classifyFields``), all TRANSPARENT ``def``s over the method's own two inputs
— there is NO opaque answer-key oracle in the load-bearing clause, so pinning
``out = buildFields fields annotations`` is grounded, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``out = buildFields fields annotations``)
is the sole and total pin: it is a function of BOTH input binders and fixes the
appended-field sequence at every point of both — which field kinds record a
description vs a declared type, whether both accepted result-description
spellings count, which annotations warrant a fresh type field, and whether the
trailing result-type field is emitted. Every uniqueness rival therefore targets
C1, each at a different sub-domain of the two binders.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-kinds`` rival writes through a read-only (``Acc(.,1/2)``)
    reference to the input to steer the decision on a self-mutated value, and is
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: both inputs are immutable values, this bundle declares no
    ``mut`` parameter, and there is no heap, aliasing, or permission system to
    subvert. There is no read-only input to overwrite, so the class is vacuous.
    No substitute probe is fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image is
    ``buildFields fields annotations``, transparent ``def``s over the method's
    own arguments; there is no answer key to echo. The honest cheapest CORRECT
    impl (``return buildFields fields annotations``) is carried as a POSITIVE
    control instead — it doubles as proof the spec is not echo-vulnerable, since
    any WRONG classification/emission fails ``out = buildFields fields
    annotations``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. A rival
    can recognize only the SHORT result-description spelling (the pre-gold bug),
    recognize the plural spelling everywhere except at the leading field, treat a
    result-TYPE field as a description, inject a type field for an annotated key
    that has no description (the ``no_undoc`` invariant), or drop the result-key
    skip in the back-fill loop.
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
    loop in the impl (2 loops here, measures ``fields.length - i``,
    ``annotations.length - j``). A rival that loops without a measure is
    refused outright (``Decreasing annotations are required in total
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

WITNESS MECHANICS ON THIS BUNDLE. C1's carrier ``buildFields`` is a TRANSPARENT
chain of ``def``s that ``decide`` reduces fully at a concrete input. Each rival is
written LOOP-FREE (``List.foldl`` / a ``match`` on the field list with an inline
buggy local classifier or emitter), so its extracted program
``augmentTypeFieldsExec`` — the ``NonDetT``-run of the ``do`` body — REDUCES under
``decide`` at a concrete input. Each witness states, at one concrete input,

    (match augmentTypeFieldsExec <fields> <annotations> with
        | DivM.res r => r | _ => [])
        ≠ buildFields <fields> <annotations>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator can see by computation.

THE FROZEN IMPL CANNOT BE THE SECOND SUBJECT, so every reject case names an
explicit ``witness_reference``. Gold's body is the two backward ``while`` loops,
whose ``…Exec`` elaborates through well-founded recursion the kernel does NOT
unfold, so a ``decide`` against gold is STUCK for every claim regardless of its
truth: the build fails with ``did not reduce to `isTrue` or `isFalse` `` at
``.hasDecEq``, an error that carries NO information about whether the claim
holds. Measured, not assumed: a FORGERY asserting the exact OPPOSITE of a
refutation — that the rival AGREES with the post-image at an agreement point
(``fields = []``, ``annotations = []``) — elaborates against the rival (exit 0)
and fails against gold (exit 1) with that same stuck-reduction error, clearing
both halves of a naive two-build check while attesting to nothing. So gold's
exit 1 must not be read as "gold satisfies the spec here"; this is exactly the
``witness-undecided`` class the gate screens for, and a battery may not describe
it as its discrimination.

The repair the gate provides is ``witness_reference``: a DIFFERENT impl of the
same frozen spec that the gate independently checks (a) shares the frozen spec
and (b) VERIFIES, and which the witness is refuted against instead. An impl the
verifier accepts cannot violate its own spec, so a genuine refutation must still
fail there — and because the reference is loop-free, the failure is a real
verdict rather than a stall. Every reject case here names ``_REFERENCE`` (below):
a loop-free impl that COMPOSES the frozen pure helpers over both binders.
Measured with ``scripts/lean_verify.sh``: each of the seven witnesses elaborates
against its rival (exit 0) and fails against ``_REFERENCE`` (exit 1) with
``Tactic `decide` proved that the proposition … is false`` — a SEMANTIC
refutation of the concrete claim, at the reduced value, not a stall, not an
unknown identifier, not a timeout. The same forgery above, refuted against
``_REFERENCE``, ELABORATES (exit 0) and is therefore caught as
``witness-vacuous`` — which is the check the frozen impl could not perform.

No witness here binds any hypothesis (every input is a concrete literal that
decides C1), so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries none either
(``meta.axioms == []``, ``deep_model_references == []``); the whole changed
behaviour is pure structural classification modeled deeply, no consumed axiom or
deep-model reference, and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9673"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the two backward `while`
# ---- folds), everything strictly BETWEEN the method's `-- impl-start` /
# ---- `-- impl-end`. Every variant replaces exactly this text, so each edit lies
# ---- wholly inside the one impl region and same_spec holds by construction
# ---- (both facts asserted at load by _swap).
_IMPL = (
    "    let mut s : Sets := emptySets\n"
    "    let mut i := 0\n"
    "    while i < fields.length\n"
    "      invariant i ≤ fields.length\n"
    "      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets\n"
    "      done_with i = fields.length\n"
    "      decreasing fields.length - i\n"
    "    do\n"
    "      s := classifyField fields[i]! s\n"
    "      i := i + 1\n"
    "    let mut result : List Field := []\n"
    "    let mut j := 0\n"
    "    while j < annotations.length\n"
    "      invariant j ≤ annotations.length\n"
    "      invariant result = (annotations.take j).foldl (emitStep s) []\n"
    "      done_with j = annotations.length\n"
    "      decreasing annotations.length - j\n"
    "    do\n"
    "      result := emitStep s result annotations[j]!\n"
    "      j := j + 1\n"
    "    return result ++ rtypeField s annotations"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct augmentTypeFields by\n"
    "  loom_solve\n"
    "  case _ =>\n"
    "    have hi : i < fields.length := by omega\n"
    "    rw [foldlTakeStep (fun acc f => classifyField f acc) emptySets fields i hi,\n"
    "        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]\n"
    "    simp_all\n"
    "  case _ =>\n"
    "    have hj : j < annotations.length := by omega\n"
    "    rw [foldlTakeStep (emitStep _) [] annotations j hj]\n"
    "    simp_all\n"
    "  all_goals simp_all [buildFields, classifyFields]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a loop-free correct reshape
    whose residual goal no longer needs the backward-fold step lemmas)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble + builder. C1's carrier `buildFields` is transparent and
# ---- each rival is loop-free, so the extracted program `augmentTypeFieldsExec`
# ---- reduces under `decide`; the witness refutes C1 directly against the
# ---- transparent `buildFields`. Checked in a file whose `prove_correct` block
# ---- is stripped, so no tactic script can mask the verdict.
_EXTRACT = "extract_program_for augmentTypeFields\n\n"


def _witness(fields, annotations):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match augmentTypeFieldsExec ({fields}) ({annotations}) with"
        " | DivM.res r => r | _ => [])\n"
        f"        ≠ buildFields ({fields}) ({annotations}) := by\n"
        "  decide\n"
    )


# ---- THE DISCRIMINATION REFERENCE (`witness_reference` on every reject case).
# ---- The frozen impl cannot serve as the witness's second subject: its two
# ---- backward `while` loops make `augmentTypeFieldsExec` irreducible in the
# ---- kernel, so `decide` STALLS against gold for every claim, true or false
# ---- (`did not reduce to isTrue or isFalse` at `.hasDecEq`). A forgery
# ---- asserting the OPPOSITE of a refutation clears a gold-only two-build check
# ---- for that reason alone; see the module docstring.
# ----
# ---- `_REFERENCE` is a loop-free impl of the SAME frozen spec that DOES reduce.
# ---- It is not the post-image term itself: it COMPOSES the frozen pure helpers
# ---- (`classifyField` folded over `fields`, `emitStep` folded over
# ---- `annotations`, then `rtypeField`), so refuting a witness against it is a
# ---- statement about a genuinely computed field sequence. The gate checks it
# ---- shares the frozen spec AND verifies before using it, so nothing is trusted
# ---- here on the manifest's word.
_REFERENCE = _impl_reproved(
    "    let s := fields.foldl (fun acc f => classifyField f acc) emptySets\n"
    "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations",
    "prove_correct augmentTypeFields by\n"
    "  loom_solve\n"
    "  all_goals simp_all [buildFields, classifyFields]")


# ---- Loop-free correct/buggy body builders. Each collapses the two backward
# ---- `while` folds into `List.foldl` (a straight-line body), so the extracted
# ---- program reduces under `decide`. The frozen `classifyField`/`emitStep`/
# ---- `rtypeField`/`buildFields` are NOT touched (they live in the frozen pure
# ---- region); a rival supplies its OWN buggy inline classifier/emitter local.


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
        # Reshape: report the whole appended-field sequence DIRECTLY via the
        # transparent `def`, no per-field/per-annotation loop. C1 is literally
        # `out = buildFields fields annotations`, so this is the cheapest HONEST
        # correct impl — and, since `buildFields …` is GROUNDED in the inputs
        # (not an opaque answer key), it doubles as proof the spec is not
        # echo-vulnerable (any WRONG classification/emission fails C1). The loops
        # are gone, so the frozen proof's two backward-fold steps are unneeded and
        # the residual goal closes under `loom_solve` alone.
        "module": _impl_reproved(
            "    return buildFields fields annotations",
            "prove_correct augmentTypeFields by\n  loom_solve"),
        "rationale": (
            "the post-image `buildFields fields annotations` is GROUNDED in the "
            "inputs (transparent `def`s over both binders, no opaque answer key), "
            "so `return buildFields fields annotations` is the honest cheapest "
            "CORRECT impl; C1 is literally that equation, so it MUST verify, else "
            "C1 is SPEC-TOO-STRONG. Ports the nagini echo-attempt-honest control: "
            "the cheapest impl satisfying the grounded pin, showing the spec is "
            "not echo-vulnerable (any wrong classification/emission fails C1)."
        ),
    },
    {
        "id": "pos-control-staged-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep both backward `while` folds but stage each per-step
        # update into a typed local (`s'`, `r'`) before assigning it. Same value
        # flow (`s' = classifyField fields[i]! s`, `r' = emitStep s result
        # annotations[j]!`), different control shape; the frozen proof still
        # closes unchanged (the loop invariants and step lemmas are untouched).
        "module": _impl(
            "    let mut s : Sets := emptySets\n"
            "    let mut i := 0\n"
            "    while i < fields.length\n"
            "      invariant i ≤ fields.length\n"
            "      invariant s = (fields.take i).foldl (fun acc f => classifyField f acc) emptySets\n"
            "      done_with i = fields.length\n"
            "      decreasing fields.length - i\n"
            "    do\n"
            "      let s' := classifyField fields[i]! s\n"
            "      s := s'\n"
            "      i := i + 1\n"
            "    let mut result : List Field := []\n"
            "    let mut j := 0\n"
            "    while j < annotations.length\n"
            "      invariant j ≤ annotations.length\n"
            "      invariant result = (annotations.take j).foldl (emitStep s) []\n"
            "      done_with j = annotations.length\n"
            "      decreasing annotations.length - j\n"
            "    do\n"
            "      let r' := emitStep s result annotations[j]!\n"
            "      result := r'\n"
            "      j := j + 1\n"
            "    return result ++ rtypeField s annotations"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (stage each per-step "
            "classifier/emitter update into a typed local before assigning it) "
            "must verify; the value flow is unchanged (`s' = classifyField …`, "
            "`r' = emitStep …`) so C1 still discharges and the frozen loop proof "
            "closes as-is. Ports the nagini pos-control local-variable reshape. "
            "If it fails => SPEC-TOO-STRONG (over-fit to the inline-assignment "
            "code form)."
        ),
    },
    # ---- ADDED BY AUDIT. Recovers the nagini branch-reorder positives
    # ---- (pos-control-rtype-first / pos-control-disj-swapped), which the port
    # ---- recorded as having "no impl-region counterpart" on the grounds that
    # ---- branch order lives in the frozen pure `def classifyField`. That is a
    # ---- statement about editing the frozen `def`, not about expressibility: a
    # ---- variant may declare its OWN local classifier in the impl region with
    # ---- the branches in a different order and prove it extensionally equal to
    # ---- the frozen one. Measured: exit 0. So the omission was a proof-effort
    # ---- gap, not a carrier limit, and it is the sharper positive of the two —
    # ---- it re-derives the classification obligation for a new impl shape
    # ---- instead of restating it.
    {
        "id": "pos-control-rtype-first-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: an impl-region local classifier that tests the result-TYPE
        # branch FIRST and the result-DESCRIPTION branch second, with `param`
        # last — the reverse of the frozen `def`'s order. The five leading
        # tokens are pairwise distinct, so the branches are disjoint and the
        # classification is identical; the equality is DISCHARGED in the proof
        # region by case analysis on the leading token, not assumed.
        "module": _impl_reproved(
            "    let cfRtypeFirst : List Tok → Sets → Sets := fun parts st =>\n"
            "      match parts with\n"
            "      | [] => st\n"
            "      | p0 :: rest =>\n"
            "        if p0 == rtypeTok then addType st returnKey\n"
            "        else if p0 == returnTok || p0 == returnsTok then addDesc st returnKey\n"
            "        else if p0 == typeTok then addType st (joinSp rest)\n"
            "        else if p0 == paramTok then\n"
            "          match rest with\n"
            "          | []           => st\n"
            "          | [x]          => addDesc st x\n"
            "          | _ :: c :: cs => let nm := joinSp (c :: cs); addType (addDesc st nm) nm\n"
            "        else st\n"
            "    let s := fields.foldl (fun acc f => cfRtypeFirst f acc) emptySets\n"
            "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations",
            "prove_correct augmentTypeFields by\n"
            "  have hcf : ∀ (parts : List Tok) (st : Sets),\n"
            "      (match parts with\n"
            "       | [] => st\n"
            "       | p0 :: rest =>\n"
            "         if p0 == rtypeTok then addType st returnKey\n"
            "         else if p0 == returnTok || p0 == returnsTok then addDesc st returnKey\n"
            "         else if p0 == typeTok then addType st (joinSp rest)\n"
            "         else if p0 == paramTok then\n"
            "           match rest with\n"
            "           | []           => st\n"
            "           | [x]          => addDesc st x\n"
            "           | _ :: c :: cs => let nm := joinSp (c :: cs); addType (addDesc st nm) nm\n"
            "         else st) = classifyField parts st := by\n"
            "    intro parts st\n"
            "    match parts with\n"
            "    | [] => rfl\n"
            "    | p0 :: rest =>\n"
            "      simp only [classifyField]\n"
            "      by_cases h1 : p0 = paramTok\n"
            "      · subst h1; simp [paramTok, typeTok, returnTok, returnsTok, rtypeTok]\n"
            "      · by_cases h2 : p0 = typeTok\n"
            "        · subst h2; simp [paramTok, typeTok, returnTok, returnsTok, rtypeTok]\n"
            "        · by_cases h3 : p0 = returnTok\n"
            "          · subst h3; simp [paramTok, typeTok, returnTok, returnsTok, rtypeTok]\n"
            "          · by_cases h4 : p0 = returnsTok\n"
            "            · subst h4; simp [paramTok, typeTok, returnTok, returnsTok, rtypeTok]\n"
            "            · by_cases h5 : p0 = rtypeTok\n"
            "              · subst h5; simp [paramTok, typeTok, returnTok, returnsTok, rtypeTok]\n"
            "              · simp_all [beq_iff_eq]\n"
            "  loom_solve\n"
            "  all_goals simp_all [buildFields, classifyFields, hcf]"),
        "rationale": (
            "a correct impl whose classification BRANCH ORDER is reversed "
            "(result-type tested first, `param` last) must verify: the five "
            "leading tokens are pairwise distinct so the branches are disjoint "
            "and the classification is identical. Recovers the nagini "
            "pos-control-rtype-first / pos-control-disj-swapped reshapes, which "
            "this port had recorded as having no impl-region counterpart — they "
            "do, via a local classifier proven extensionally equal to the frozen "
            "`def`. Stronger than the staged-local positive because the "
            "equality is RE-PROVEN by case analysis on the leading token rather "
            "than holding by definitional unfolding. If it fails => "
            "SPEC-TOO-STRONG (C1 over-fit to one branch order)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-f2p-shaped. That case
    # established the read-only precondition `Acc(list_pred(.),1/2)` on an
    # F2P-shaped field-list and derived an F2P-shaped fact from it. This method
    # carries NO `require` clause (the pre-conditions region is empty), so nothing
    # could exclude a normal input and the classic "a normal input is admitted"
    # probe is vacuous. Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is SATISFIABLE by a gold-shaped computation. The
    # frozen impl discharging C1 IS that witness. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the augmenter is total over every "
            "field-list and annotation table; the gold impl discharging C1 is the "
            "admissibility witness that the post-image `out = buildFields fields "
            "annotations` is satisfiable by a gold-shaped computation. Near-trivial "
            "precisely because the precondition is empty. Re-aimed from the nagini "
            "admiss-f2p-shaped, whose read-only fractional-permission half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = buildFields
    # fields annotations`); between them they vary BOTH input binders (`fields`
    # and `annotations`) across five distinct input points.
    # =====================================================================
    {
        "id": "rival-short-spelling-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating bug. The classifier recognizes only the SHORT
        # result-description spelling and drops the plural synonym — exactly the
        # pre-gold behaviour. On any field-list with no plural result-description
        # field it agrees with gold; it diverges precisely on the plural-spelling
        # input the F2P feeds.
        "module": _impl(
            "    let classifyShort : List Tok → Sets → Sets := fun parts st =>\n"
            "      match parts with\n"
            "      | [] => st\n"
            "      | p0 :: rest =>\n"
            "        if p0 == paramTok then\n"
            "          match rest with\n"
            "          | []           => st\n"
            "          | [x]          => addDesc st x\n"
            "          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm\n"
            "        else if p0 == typeTok then\n"
            "          addType st (joinSp rest)\n"
            "        else if p0 == returnTok then\n"
            "          addDesc st returnKey\n"
            "        else if p0 == rtypeTok then\n"
            "          addType st returnKey\n"
            "        else st\n"
            "    let s := fields.foldl (fun acc f => classifyShort f acc) emptySets\n"
            "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations"),
        "refinement": (
            "recognizes only the SHORT result-description spelling and ignores the "
            "plural synonym — exactly the pre-gold behaviour of the changed "
            "function (a single-spelling leading-token test). Its faithful real "
            "patch is the pre-patch classification loop, which FAILS the F2P "
            "(a result documented under the plural spelling must still be counted "
            "as described so a trailing result-type field is appended) — it would "
            "NOT resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): `buildFields` "
            "records a result description under EITHER spelling, so on a plural "
            "result-description field the short-only rival records no description, "
            "emits no trailing result-type field, and diverges from the post-image. "
            "Refuted at input `fields = [[param a], [returns]]`, `annotations = "
            "[(return, int)]` — a plural result-description field alongside a "
            "described param, where gold appends the result-type field and the "
            "rival does not. If it verified => SPEC-TOO-WEAK (admits the synonym "
            "bug)."
        ),
        "witness": _witness(
            '[["param".toList, "a".toList], ["returns".toList]]',
            '[("return".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-drop-first-plural",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: recognize the plural result-description spelling
        # EVERYWHERE except when it sits at the FIRST field of the list, where it
        # is ignored. Every field-list whose leading field is not a plural
        # result-description is handled exactly like gold.
        "module": _impl(
            "    let s := match fields with\n"
            "      | []      => emptySets\n"
            "      | f0 :: rest =>\n"
            "        let classifyNoLeadPlural : List Tok → Sets → Sets := fun parts st =>\n"
            "          match parts with\n"
            "          | [] => st\n"
            "          | p0 :: pr =>\n"
            "            if p0 == paramTok then\n"
            "              match pr with\n"
            "              | []           => st\n"
            "              | [x]          => addDesc st x\n"
            "              | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm\n"
            "            else if p0 == typeTok then addType st (joinSp pr)\n"
            "            else if p0 == returnTok then addDesc st returnKey\n"
            "            else if p0 == rtypeTok then addType st returnKey\n"
            "            else st\n"
            "        rest.foldl (fun acc f => classifyField f acc) (classifyNoLeadPlural f0 emptySets)\n"
            "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations"),
        "refinement": (
            "recognizes the plural result-description spelling EVERYWHERE except "
            "at the first field of the list, which it ignores. A faithful real "
            "patch special-casing the leading field would still miss a LEADING "
            "plural result-description field, and the F2P pins the synonym "
            "regardless of field position, so it would NOT resolve. A genuine "
            "partial-domain break — correct on every non-leading plural field."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): C1 pins the "
            "WHOLE field-list including index 0, so a rival that mishandles only "
            "the leading plural result-description field still diverges from "
            "`buildFields`. Refuted at input `fields = [[returns]]`, `annotations "
            "= [(return, int)]` — a DISTINCT point from rival-short-spelling-only "
            "(a plural field at position 0 with no preceding param), varying the "
            "`fields` binder. If it verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness(
            '[["returns".toList]]',
            '[("return".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-rtype-as-description",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: classify a result-TYPE field as a result-DESCRIPTION instead
        # of a declared type. The result key then looks described-but-untyped, so
        # a spurious trailing result-type field is emitted even though the result
        # already has a declared type.
        "module": _impl(
            "    let classifyRtypeAsDesc : List Tok → Sets → Sets := fun parts st =>\n"
            "      match parts with\n"
            "      | [] => st\n"
            "      | p0 :: rest =>\n"
            "        if p0 == paramTok then\n"
            "          match rest with\n"
            "          | []           => st\n"
            "          | [x]          => addDesc st x\n"
            "          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm\n"
            "        else if p0 == typeTok then addType st (joinSp rest)\n"
            "        else if p0 == returnTok || p0 == returnsTok then addDesc st returnKey\n"
            "        else if p0 == rtypeTok then addDesc st returnKey\n"
            "        else st\n"
            "    let s := fields.foldl (fun acc f => classifyRtypeAsDesc f acc) emptySets\n"
            "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations"),
        "refinement": (
            "treats a declared result-type field as a result-description and never "
            "records the result as typed. A faithful real patch doing this would "
            "append a spurious trailing result-type field even when the result "
            "already carries a declared type — duplicating the type section — "
            "failing the autodoc assertions that pin the result-type-emission "
            "decision, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): `classifyField` "
            "records a declared result-type field into `hasType` (not `hasDesc`), "
            "so `rtypeField` emits nothing when the result is already typed. The "
            "rival records it as a description, so on a result-type field plus a "
            "result annotation it appends a trailing result-type field the "
            "post-image does not. Refuted at input `fields = [[rtype]]`, "
            "`annotations = [(return, int)]` — a distinct field-kind point. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[["rtype".toList]]',
            '[("return".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-emit-no-desc-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The `no_undoc` invariant. The back-fill emitter drops the "already has a
        # description" guard, so it injects a type field for an annotated key that
        # was never documented. Attacks the emission arm of C1.
        "module": _impl(
            "    let s := fields.foldl (fun acc f => classifyField f acc) emptySets\n"
            "    let emitNoDescGuard : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>\n"
            "      let name := na.1\n"
            "      if name == returnTok || name == returnsTok then acc\n"
            "      else if !(st.hasType.contains name) then\n"
            "        acc ++ [Field.typeOf name na.2]\n"
            "      else acc\n"
            "    return (annotations.foldl (emitNoDescGuard s) []) ++ rtypeField s annotations"),
        "refinement": (
            "drops the requirement that a parameter already carry a description "
            "before its declared type is back-filled, so it injects a type field "
            "for an UNDOCUMENTED annotated key. The F2P is precisely the "
            "no-undocumented-injection case (an undescribed parameter/result must "
            "NOT gain a type section), so a real patch emitting a type field for "
            "an undocumented name would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): `emitStep` "
            "emits a parameter-type field only for an annotated name that ALREADY "
            "carries a description; the rival drops that guard and emits for any "
            "untyped annotated name. Refuted at input `fields = []`, `annotations "
            "= [(a, int)]` — an annotated key with NO recorded description, where "
            "gold emits nothing and the rival emits a type field. This is the only "
            "witness that moves the `annotations` binder off `[(return, int)]` and "
            "holds `fields` empty, so the battery discriminates both binders. If "
            "it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[]',
            '[("a".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-emit-no-return-skip",
        "kind": "uniqueness",
        "expect": "reject",
        # The back-fill loop's result-key skip is dropped, so a documented +
        # annotated result gains a spurious parameter-type field (`type return`)
        # in addition to its trailing result-type field. Ports the nagini hunk-2
        # surface (the second gold hunk skips the result key in the back-fill
        # loop), re-aimed at the behaviour the modeled carrier can observe.
        "module": _impl(
            "    let s := fields.foldl (fun acc f => classifyField f acc) emptySets\n"
            "    let emitNoReturnSkip : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>\n"
            "      let name := na.1\n"
            "      if st.hasDesc.contains name && !(st.hasType.contains name) then\n"
            "        acc ++ [Field.typeOf name na.2]\n"
            "      else acc\n"
            "    return (annotations.foldl (emitNoReturnSkip s) []) ++ rtypeField s annotations"),
        "refinement": (
            "drops the skip of the result key in the parameter-type back-fill "
            "loop, so a documented + annotated result gains a spurious "
            "parameter-type field in addition to its trailing result-type field. "
            "This is exactly the second gold hunk (skip the result key under "
            "either spelling in the back-fill loop); reverting it emits a "
            "duplicated/misplaced type field for the result, so a faithful real "
            "patch would NOT resolve. It ports the nagini hunk-2 surface "
            "(name_is_return_key), re-aimed: the modeled carrier observes the skip "
            "via the emitted field sequence rather than a scalar boolean."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): `emitStep` "
            "skips the result key so the result's type is handled solely by the "
            "trailing `rtypeField`; the rival's emitter drops that skip and "
            "appends a parameter-type field for the result too. Refuted at input "
            "`fields = [[return]]`, `annotations = [(return, int)]` — a documented "
            "result with a result annotation, where gold appends only the trailing "
            "result-type field and the rival appends an extra `type return` field. "
            "A distinct field-content point. If it verified => SPEC-TOO-WEAK "
            "(admits the hunk-2 bug)."
        ),
        "witness": _witness(
            '[["return".toList]]',
            '[("return".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    # ---- ADDED BY AUDIT. The five ported rivals all attack the
    # ---- result-description / result-key arms of C1 and leave two of its
    # ---- decision points unprobed: the "no declared type yet" half of the
    # ---- back-fill guard, and the multi-token name join. A rival on either arm
    # ---- that VERIFIED would be a spec hole, so the battery has to try them.
    {
        "id": "rival-emit-no-type-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # The back-fill emitter keeps the "already described" half of its guard
        # but drops the "not already typed" half, so a parameter that ALREADY
        # carries a declared type gets a second, duplicate type field. The
        # complement of rival-emit-no-desc-guard: same emission arm, other
        # conjunct. Agrees with gold on every input where no annotated name is
        # already typed, which is why it is a genuine partial-domain break.
        "module": _impl(
            "    let s := fields.foldl (fun acc f => classifyField f acc) emptySets\n"
            "    let emitNoTypeGuard : Sets → List Field → (Tok × Tok) → List Field := fun st acc na =>\n"
            "      let name := na.1\n"
            "      if name == returnTok || name == returnsTok then acc\n"
            "      else if st.hasDesc.contains name then\n"
            "        acc ++ [Field.typeOf name na.2]\n"
            "      else acc\n"
            "    return (annotations.foldl (emitNoTypeGuard s) []) ++ rtypeField s annotations"),
        "refinement": (
            "drops the requirement that a parameter have NO declared type yet "
            "before one is back-filled, so a parameter that already documents "
            "its type gains a duplicate type section. A faithful real patch "
            "doing this would emit two type entries for one already-typed "
            "parameter, which the autodoc assertions pinning the emitted field "
            "sequence reject, so it would NOT resolve. Distinct from "
            "rival-emit-no-desc-guard: that one injects for an UNDOCUMENTED "
            "name, this one duplicates for an ALREADY-TYPED one."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): `emitStep` "
            "emits only when the annotated name is described AND not already "
            "typed; the rival drops the second conjunct. Refuted at input "
            "`fields = [[param a], [type a]]`, `annotations = [(a, int)]` — a "
            "parameter carrying BOTH a description and a declared type, where "
            "gold emits nothing and the rival emits a duplicate `type a`. A "
            "sixth distinct `fields` point, and the first that exercises a "
            "`type` field. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[["param".toList, "a".toList], ["type".toList, "a".toList]]',
            '[("a".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-type-first-token-only",
        "kind": "uniqueness",
        "expect": "reject",
        # A `type` field whose name spans several tokens is keyed on the FIRST
        # trailing token instead of the space-joined remainder, so a multi-word
        # parameter name is recorded under the wrong key and looks untyped.
        # Identical to gold on every single-token name — the whole rest of the
        # domain.
        "module": _impl(
            "    let classifyFirstTok : List Tok → Sets → Sets := fun parts st =>\n"
            "      match parts with\n"
            "      | [] => st\n"
            "      | p0 :: rest =>\n"
            "        if p0 == paramTok then\n"
            "          match rest with\n"
            "          | []           => st\n"
            "          | [x]          => addDesc st x\n"
            "          | _ :: b :: cs => let nm := joinSp (b :: cs); addType (addDesc st nm) nm\n"
            "        else if p0 == typeTok then\n"
            "          addType st (match rest with | [] => [] | x :: _ => x)\n"
            "        else if p0 == returnTok || p0 == returnsTok then addDesc st returnKey\n"
            "        else if p0 == rtypeTok then addType st returnKey\n"
            "        else st\n"
            "    let s := fields.foldl (fun acc f => classifyFirstTok f acc) emptySets\n"
            "    return (annotations.foldl (emitStep s) []) ++ rtypeField s annotations"),
        "refinement": (
            "keys a declared-type field on the first trailing name token rather "
            "than on the whole space-joined remainder, so a multi-word "
            "parameter name is recorded under a truncated key. A faithful real "
            "patch doing this would treat an already-typed multi-word parameter "
            "as untyped and back-fill a duplicate type section for it, failing "
            "the autodoc assertions on the emitted sequence — it would NOT "
            "resolve. Probes the name-join arm no other rival touches."
        ),
        "rationale": (
            "REJECT from C1 (`out = buildFields fields annotations`): "
            "`classifyField` records a `type` field under `joinSp rest`, the "
            "full space-joined remainder; the rival records only the first "
            "token. Refuted at input `fields = [[param b], [type b c]]`, "
            "`annotations = [(b, int)]` — where gold records the declared type "
            "under `b c`, leaving `b` described-and-untyped so a `type b` field "
            "is emitted, and the rival records it under `b`, suppressing that "
            "emission. Note the naive point `[[param a b], [type a b]]` is NOT "
            "usable: there the `param` clause already types `a b` under both "
            "impls, so they agree and the witness would be vacuous — measured, "
            "then re-aimed. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            '[["param".toList, "b".toList], ["type".toList, "b".toList, "c".toList]]',
            '[("b".toList, "int".toList)]'),
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                   -> here
#   -----------------------------------------------------------------------
#   pos-control-rtype-first       -> pos-control-rtype-first-local  PORTED (audit)
#   pos-control-disj-swapped      -> pos-control-rtype-first-local  (merged)
#   echo-attempt-honest           -> pos-control-direct         RE-EXPRESSED
#   admiss-f2p-shaped             -> admiss-gold-total          RE-AIMED
#   frame-mutate-kinds            -> (none)                     VACUOUS
#   rival-short-spelling-only     -> rival-short-spelling-only  PORTED
#   rival-drop-first-plural       -> rival-drop-first-plural    PORTED
#   rival-rtype-as-description    -> rival-rtype-as-description  PORTED
#   rival-name-short-only         -> rival-emit-no-return-skip  RE-AIMED (hunk 2)
#   (no direct sibling)           -> rival-emit-no-desc-guard   ADDED (no_undoc)
#   (no direct sibling)           -> rival-emit-no-type-guard   ADDED (audit)
#   (no direct sibling)           -> rival-type-first-token-only ADDED (audit)
#   (nagini pos-control-staged)   -> pos-control-staged-local   PORTED
#   AXIOM_TESTS ([])              -> (none)                     DROPPED (empty)
#
# 11 velvet SPEC cases: 3 soundness, 1 admissibility, 7 uniqueness.
#
# AUDIT REPAIRS (this file was audited after its first SOUND was recorded; the
#   three defects found are recorded here rather than quietly fixed):
#   (1) WITNESS DISCRIMINATION WAS NOT WHAT THE FILE CLAIMED. The original
#       docstring described the gold-side witness build failing because gold's
#       `while` loops leave `…Exec` irreducible under `decide`, and presented
#       that as "exactly the discrimination the gate requires". It is the
#       opposite: a stuck reduction is a build failure the kernel never
#       evaluated, so its exit code carries no information. Re-derived with real
#       builds — all five gold-side builds failed with `did not reduce to
#       isTrue or isFalse` at `.hasDecEq`, and a FORGERY asserting the exact
#       opposite of a refutation (that the rival AGREES with the post-image at
#       `fields = []`, `annotations = []`) also got rival exit 0 / gold exit 1.
#       Repair: every reject case now names an explicit `witness_reference`
#       (`_REFERENCE`, loop-free, composes the frozen pure helpers, gate-checked
#       to share the spec and verify). All witnesses now fail against it with
#       `decide proved that the proposition … is false` — a semantic refutation
#       at the reduced value — and the forgery ELABORATES there, so it is caught
#       as `witness-vacuous`. NOTE: the recorded SOUND was not in fact hollow,
#       because the gate's own stuck-reduction screen had already detected this
#       and silently fallen back to a battery positive (meta.json recorded
#       `witness_subject: "a verifying positive from this battery (gold cannot
#       decide)"` on all five). The defect was the FILE'S PROSE claiming a
#       mechanism that does not hold; naming the reference explicitly makes the
#       artifact say what was actually measured instead of relying on a fallback.
#   (2) A DROPPED POSITIVE WAS EXPRESSIBLE. The nagini branch-reorder positives
#       were recorded as having no impl-region counterpart because branch order
#       lives in the frozen pure `def classifyField`. But a variant may declare
#       its OWN local classifier in the impl region and prove it extensionally
#       equal to the frozen one; measured, exit 0. Restored as
#       pos-control-rtype-first-local. The original reason was a proof-effort
#       gap described as a carrier limit.
#   (3) TWO ARMS OF C1 WERE UNPROBED. The five ported rivals all attack the
#       result-description / result-key arms. Added rival-emit-no-type-guard
#       (the "not already typed" conjunct of the back-fill guard, the complement
#       of rival-emit-no-desc-guard) and rival-type-first-token-only (the
#       multi-token name join). Both are rejected and both witnesses
#       discriminate against `_REFERENCE`.
#   SPEC PROBES THAT FOUND NOTHING (recorded so the coverage claim is checkable):
#       five further wrong impls were written and all five were rejected — the
#       two now shipped, plus dropping `rtypeField`'s "is the result annotated"
#       guard, emitting the trailing result-type field FIRST rather than last,
#       and skipping only the short spelling in the back-fill loop. Two correct
#       reshapes beyond the shipped positives were written and both verified
#       (a loop-free composition, and a `foldr`-over-`reverse` classification
#       scan). No spec hole in either direction was found.
#
# WHY THE SHAPE CHANGES (carrier narrowing, not omission). The nagini bundle
#   models TWO scalar functions — `augment_return_typefield` (a bool over a
#   `List[int]` of field-codes) and `name_is_return_key` (a bool over three
#   scalar names). This velvet bundle models ONE method returning the WHOLE
#   appended-field sequence over the two structural inputs (`fields`,
#   `annotations`), pinned by the single grounded clause C1. So the two nagini
#   functions collapse into one method, and every nagini rival becomes a rival
#   over the combined field-sequence result.
# PORTED, MERGED (pos-control-rtype-first + pos-control-disj-swapped ->
#   pos-control-rtype-first-local): the nagini positives reorder the if/elif
#   classification branches (rtype-first) and the return-description disjunction
#   (3-or-2). Branch order does live in the FROZEN pure `def classifyField`, which
#   a variant may NOT edit — but that only rules out editing it in place. The
#   impl region may declare its OWN classifier with the branches reordered and
#   prove it extensionally equal to the frozen `def` by case analysis on the
#   leading token, which is what pos-control-rtype-first-local does (measured:
#   verifies). Both nagini reshapes collapse onto it, since the five leading
#   tokens are pairwise distinct and so BOTH the branch order and the
#   disjunction order are immaterial for the same reason. This supersedes an
#   earlier reading of this file, which recorded the reshapes as having no
#   impl-region counterpart at all. pos-control-staged-local (staging each
#   per-step update into a typed local) is retained as the weaker, control-shape
#   reshape that keeps both loops.
# RE-EXPRESSED (echo-attempt-honest -> pos-control-direct): the nagini honest-echo
#   control asserts, in-region, that the built flags equal the @Pure folds. Here
#   the oracle IS the transparent `buildFields` and C1 already IS `out =
#   buildFields fields annotations`, so the honest cheapest impl is `return
#   buildFields fields annotations` — the same grounded-pin argument (no wrong
#   echo verifies) as a loop-free correct impl (proof retuned since the loops are
#   gone).
# RE-AIMED (admiss-f2p-shaped -> admiss-gold-total): the nagini case established
#   the read-only fractional-permission precondition on an F2P-shaped input. This
#   method has no `require` and no heap permission, so that probe is vacuous;
#   re-aimed at the residual total-domain risk (post-image satisfiability),
#   witnessed by the frozen impl discharging C1.
# PORTED (3): rival-short-spelling-only (THE discriminating bug — short-only
#   result-description recognition), rival-drop-first-plural (the leading-field
#   partial domain), and rival-rtype-as-description (misclassify a result-type
#   field) carry across intact; only the carrier changes from a nagini `List[int]`
#   code-classification to a Velvet field-token classification, and each now
#   carries a machine-checked witness at a distinct input.
# RE-AIMED (rival-name-short-only -> rival-emit-no-return-skip): the nagini hunk-2
#   rival attacks `name_is_return_key` recognizing only the short return spelling.
#   This bundle does not model that scalar predicate; the modeled counterpart is
#   the back-fill loop's result-key SKIP (the second gold hunk). Note the plural
#   half of that skip is unobservable on the F2P carrier (Python records the
#   result annotation under the key 'return', never 'returns'), so a literal
#   plural-only revert would still resolve — that case is NOT ported. Instead the
#   rival drops the result-key skip outright, emitting a spurious `type return`
#   field, which its faithful patch (reverting the skip) would fail the F2P for.
# ADDED (rival-emit-no-desc-guard): no direct nagini sibling. The F2P is literally
#   the "no_undoc" case — an undocumented annotated key must NOT gain a type field
#   — which the emission guard (`name ∈ hasDesc`) enforces. A rival dropping that
#   guard is a real SPEC-TOO-WEAK risk on C1's emission arm and the only witness
#   that moves the `annotations` binder off `[(return, int)]`. Real divergence
#   with a machine-checked witness.
# FRAME-MUTATION (frame-mutate-kinds): VACUOUS. The nagini rival writes through a
#   read-only (1/2) reference to the field-code list and is rejected for
#   insufficient permission. Velvet is referentially transparent, both inputs are
#   immutable values, no `mut` binder, no heap, no aliasing, no permission system.
#   There is no read-only input to overwrite. No substitute fabricated.
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
#   loop in the impl (2 loops here, measures ``fields.length - i``,
#   ``annotations.length - j``). A rival that loops without a measure is
#   refused outright (``Decreasing annotations are required in total
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
# DROPPED (AXIOM_TESTS): the nagini file's AXIOM_TESTS is already empty
#   (meta.axioms == [], deep_model_references == []); the whole changed behaviour
#   is pure structural classification modeled deeply, no consumed axiom or
#   deep-model reference. The G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause is C1
#   (`out = buildFields fields annotations`), attacked by all SEVEN uniqueness
#   rivals across its distinct arms: result-description recognition
#   (rival-short-spelling-only, rival-drop-first-plural), result-type
#   classification (rival-rtype-as-description), the annotation back-fill
#   emission on BOTH its conjuncts (rival-emit-no-desc-guard for "is described",
#   rival-emit-no-type-guard for "is not already typed"), the back-fill result-key
#   skip (rival-emit-no-return-skip), and the multi-token name join
#   (rival-type-first-token-only). Both input binders are varied: `annotations` is
#   moved off `[(return, int)]` to `[(a, int)]` and `[(b, int)]`; `fields` ranges
#   over SEVEN distinct points — `[[param a],[returns]]`, `[[returns]]`,
#   `[[rtype]]`, `[]`, `[[return]]`, `[[param a],[type a]]`,
#   `[[param b],[type b c]]` — so no binder is held fixed by every witness, and
#   the last two are the first to put a `type` field in the list at all. The
#   variation is MEANINGFUL rather than two spellings of one point: at each of
#   the seven, gold and the rival at that case produce different field
#   sequences, which is what the witness decides. All three positives and the
#   admissibility case defend C1.
#
# WITNESS MECHANICS: C1's carrier `buildFields` is a transparent chain of `def`s
#   and each rival is loop-free (`List.foldl` / a `match`), so each rival's
#   extracted program `augmentTypeFieldsExec` reduces fully under `decide`; each
#   witness refutes C1 directly against the transparent `buildFields` at a
#   concrete input. The FROZEN impl cannot be the second subject — its two
#   `while` loops leave `…Exec` irreducible, so `decide` stalls there for every
#   claim regardless of truth, which discriminates nothing — so every reject case
#   names `_REFERENCE` as its `witness_reference`. All seven checked with
#   scripts/lean_verify.sh: rival exit 0, `_REFERENCE` exit 1 with `decide proved
#   that the proposition … is false`. No witness binds a hypothesis (every input
#   is a concrete literal), so no consistency probe is needed.
AXIOM_TESTS = []
