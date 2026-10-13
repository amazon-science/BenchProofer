"""properties.py — G-PBT falsification battery for pallets__flask-5014 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct validateBlueprintName`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the witness SUBJECT. On this bundle that subject is a named
``witness_reference``, not the frozen solution, because the frozen impl cannot
DECIDE anything — see the CARRIER NOTE at ``_WITNESS_REF``.

DEFENDED SURFACE (one contracted method deciding acceptance of a candidate
construction name over its Unicode code-point sequence, ``List Char``):

  validateBlueprintName (s : List Char) return (out : Bool)
    ensures out = validName s                                    -- the only clause

where ``validName s = !s.isEmpty && !containsDot s`` and ``containsDot`` is a
TRANSPARENT front-recursive ``def`` (``containsDot (c :: cs) = (c == '.' ||
containsDot cs)``, ``containsDot [] = false``) spelled out over the input
(directive 8), NOT an opaque answer-key. The whole clause reduces to a
computation on the input's code points, so a rival cannot "echo an oracle" — the
only way to satisfy it is to compute the same accept/reject decision. There is
no consumed axiom (the ``axioms`` region is empty).

WHAT THE SPEC DEFENDS. Acceptance is the conjunction of TWO independent
sub-decisions on the name, both pinned by the single whole-value equality:

  * NON-EMPTINESS (``!s.isEmpty``) — the DISCRIMINATING behaviour of the fix: an
    empty name must be REJECTED (``out = false``). This is what the sole F2P
    demands (an empty construction name must be refused rather than accepted).
    ``reject-drop-empty-guard`` reproduces the pre-fix acceptance of the empty
    name.
  * DOT-FREENESS (``!containsDot s``) — the pre-existing guard the fix leaves in
    place: a name carrying the dot code point must be rejected. A P2P relies on
    it. ``reject-drop-dot-guard`` and ``reject-partial-leading-dot`` attack it,
    the latter on the interior-dot sub-domain.

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on the SINGLE input ``s``. The five reject witnesses vary ``s`` across
five DISTINCT points that separate the two sub-decisions and pin the emptiness
boundary from BOTH sides:

  * ``[]`` (empty, dot-free) — separates the emptiness sub-decision from below.
    gold rejects (``false``); a rival that dropped the emptiness check accepts.
  * ``"."`` (a leading dot) — separates the dot sub-decision at the front.
  * ``"a.b"`` (an interior dot, non-empty) — separates the dot sub-decision on the
    interior sub-domain a leading-dot-only check would miss.
  * ``"ok"`` (non-empty, dot-free = ACCEPTED) — the accept point; gold accepts
    (``true``), so a rival that over-rejects is caught here.
  * ``"a"`` (ACCEPTED at length one) — separates the emptiness sub-decision from
    ABOVE: gold accepts, and a rival reading "non-empty" as "at least two code
    points" is wrong ONLY here. Added under audit; ``reject-off-by-one-length``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this
    MANDATORY (``frame-mutate-name`` / ``frame-mutate-import-name``) because its
    ``name`` / ``import_name`` list inputs are held at a fractional heap
    permission (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: ``s`` is an immutable value, there is no ``mut``
    binder, no heap and no aliasing — there is no read-only input to overwrite
    and no substitute probe to build. Not fabricated (porting map: vacuous here).
  * CONTROL-FLOW-EFFECT / WRONG-EXCEPTION-CHANNEL — VACUOUS. The nagini
    ``rival-wrong-exc-on-reject`` turns on the two DISJOINT exception channels
    (``NameValidationError`` vs ``BaseInitError``) pinned by the ``init_base``
    axiom over ``import_name``. This velvet bundle abstracts the base initialiser
    away entirely (mapping.md §2–§3: it never inspects ``name`` and observes no
    state this Bool decision measures, so it is NOT modeled and NOT axiomatized).
    The carrier collapses accept/reject to a single ``Bool`` (``out = true`` vs
    ``out = false``) with no ``import_name`` binder and no exception-channel
    distinction, so there is no second channel for a rival to mis-route through
    and no witness could discriminate one. Legitimately omitted (carrier
    narrowing), not fabricated.
  * ADMISSIBILITY (nagini's F2P-shaped self-call proving the precondition
    ``Acc(list_pred(.),1/2)``) — RE-AIMED. This bundle declares NO ``require``
    clause (the pre-conditions region is empty), so nothing can exclude any input
    and the classic "the precondition admits the F2P input" probe is vacuous.
    Re-aimed at the residual total-domain risk: that the post-image is jointly
    satisfiable by a gold-shaped computation — witnessed by the frozen impl
    satisfiable at exactly the F2P-shaped inputs, discharged by EVALUATION at
    ``[]`` / ``"ok"`` / ``"a.b"`` before the frozen obligation is closed
    verbatim (see ``admiss-f2p-points``).
  * UNGROUNDED-ORACLE ECHO — N/A: the post-image ``validName`` is a transparent
    ``def`` over ``s`` (its dot test is the grounded front-recursive fold
    ``containsDot``), not an axiomatized oracle; there is no answer-key to echo.
    The cheapest honest correct impl (``return validName s``) is carried as a
    POSITIVE control (``pos-control-direct``).
  * DIVERGENCE: nothing to port, and closed BY THE VERIFIER rather than vacuous.
    The nagini sibling carries NO ``diverge-*`` / ``nonterm-*`` / ``weak-diverge``
    case, so there is no divergence rival to carry over. "Genuinely vacuous" is
    withdrawn: the frozen impl IS loop-based, and a rival owns the whole impl
    region, so a diverging rival is perfectly writable. It is REJECTED when it is
    written. This bundle sets ``loom.semantics.termination "total"``, under which a
    postcondition is claimed of ALL runs, not only terminating ones, so the
    verifier demands a decreasing measure on every loop AND discharges its descent.
    The setting cannot drift from the file's ``open TotalCorrectness DemonicChoice``,
    because the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced loop with NO measure is refused at
    the ``method`` declaration
    (``Decreasing annotations are required in total correctness semantics``), and
    the sharper shape that CARRIES a measure which does not decrease
    (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
    ``z := z + 1``) is refused on the measure's own goal:
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. (No KNOWN-HOLE
    disposition is claimed, and none applies: no velvet bundle sets ``partial``.)
  * AXIOM lane (nagini's 3 ``init_base`` soundness/containment probes over the
    real flask base initialiser) — DROPPED. The axiom lane is G-AX's job; this
    gate ignores ``AXIOM_TESTS`` regardless, and this bundle declares no consumed
    axiom (mapping.md §3).

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``validateBlueprintNameTester s = false`` says the extracted program's result
violates the postcondition ``out = validName s`` at that concrete input. It is
checked in a file whose ``prove_correct`` block has been stripped (so no tactic
script can mask the verdict) and there are no ``require`` clauses, so every input
reaches the postcondition. ``List Char`` literals via ``"…".toList`` (and the
empty ``[]``) are fully concrete, so ``decide`` settles the equality — no opaque
term, no conditioning, no head binders (hence no consistency obligation).

THE WITNESS SUBJECT IS NOT THE FROZEN SOLUTION. An earlier revision of this file
claimed each witness "FAILS against the frozen solution (a ``decide`` error)" and
read that exit code as a refutation. Re-measured under audit with real builds,
that reading was WRONG: the frozen impl's ``while`` loop under
``loom.semantics.choice "demonic"`` elaborates through ``Classical.choice``, so
``decide`` on the frozen tester is STUCK ("did not reduce to ``isTrue`` or
``isFalse`` … reduction got stuck at the ``Decidable`` instance") for EVERY claim
— the witness's own and its exact opposite alike, byte-identical but for the
echoed claim text. Gold's exit code therefore carried no information, and a forged
witness asserting the frozen impl is CORRECT at that input would have been
recorded as a refutation just as readily.

So every reject case now names an explicit ``witness_reference`` (``_WITNESS_REF``
— the ``pos-control-direct`` source, loop-free and kernel-reducible, which the
gate independently checks shares the frozen spec AND verifies). Against that
subject the exit code TRACKS the claim: the witness's claim is REFUTED BY
EVALUATION ("Tactic ``decide`` PROVED that the proposition … is false", exit 1)
while the forged opposite goes GREEN (exit 0). Every half of every case was re-run
with ``scripts/lean_verify.sh``; the full per-case exit matrix is at
``_WITNESS_REF``. Discrimination is by VALUE at a concrete input: ``List Char``
literals via ``"…".toList`` (and the empty ``[]``) are fully concrete, no
hypothesis is bound, so there is no consistency obligation.
"""
from pathlib import Path

INSTANCE = "pallets__flask-5014"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The COMPLETE frozen impl body (the backward per-code-
# ---- point loop plus the accept expression); lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). Anchoring on the whole body keeps every
# ---- surgery inside the elided region — the frozen spec (the `method` header,
# ---- `ensures out = validName s`, and the `pure` region defining `containsDot`
# ---- / `validName`) is never touched. ----
_IMPL = (
    "    let mut hasDot : Bool := false\n"
    "    let mut i := s.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ s.length\n"
    "      invariant hasDot = containsDot (s.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := s[i - 1]!\n"
    "      hasDot := c == '.' || hasDot\n"
    "      i := i - 1\n"
    "    return !s.isEmpty && !hasDot"
)
assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- reshape that removes the `while` loop retunes THIS block, so each positive
# ---- carries its own closing script; every reject rival makes the impl
# ---- loop-free but LEAVES this frozen proof in place (Rule 2 keeps the
# ---- obligation header), so the loop-tuned script no longer closes and the
# ---- variant does NOT verify — the rejection is then attested by the
# ---- machine-checked witness, not inferred from the tactic breakage. ----
_PROOF = (
    "prove_correct validateBlueprintName by\n"
    "  loom_solve\n"
    "  · rw [containsDot_drop_step s i (by omega) (by omega)]\n"
    "    simp_all [Bool.or_comm]\n"
    "  · simp_all [validName, List.drop_zero]"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _reproved(new_impl, new_proof):
    """Full Solution.lean variant: impl body replaced AND the proof retuned for
    the new (loop-free) impl shape."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _rival(new_impl):
    """A reject rival: replace ONLY the impl with a loop-free (so `…Exec`-
    reducible) wrong body, leaving the frozen `prove_correct` obligation in place
    (Rule 2: the obligation header must survive with a byte-identical statement).
    The frozen loop-based proof does not close for the reshaped impl, so the
    variant does NOT verify — the reject outcome — and its refutation is carried
    by the machine-checked witness."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- witness preamble: reach the contract through Velvet's tester machinery,
# ---- in a file whose `prove_correct` block has been stripped. ----
_TESTER = (
    "\nextract_program_for validateBlueprintName\n"
    "prove_precondition_decidable_for validateBlueprintName\n"
    "prove_postcondition_decidable_for validateBlueprintName\n"
    "derive_tester_for validateBlueprintName\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


# ---- THE WITNESS SUBJECT, and why it is NOT the frozen solution. ----
#
# The frozen impl is a backward `while` loop under `loom.semantics.choice
# "demonic"`, so the extracted `validateBlueprintNameExec` elaborates through
# `Classical.choice`, which the kernel cannot unfold. A witness stated against
# the FROZEN impl is therefore STUCK rather than refuted. Re-measured under audit
# with real builds, per reject case, against the frozen solution:
#
#   the witness's own claim   (`…Tester x = false`) -> exit 1
#     "Tactic `decide` failed for proposition …
#      because its `Decidable` instance … did not reduce to `isTrue` or `isFalse`.
#      … reduction got stuck at the `Decidable` instance"
#   the FORGED opposite claim (`…Tester x = true`)  -> exit 1, the SAME error,
#     differing only in the claim text it echoes back
#
# So gold's exit code carries NO information about the claim: a forged witness
# asserting the frozen impl is CORRECT at that input — the opposite of a
# refutation — fails exactly as loudly. Loop-freeness of the RIVAL is not the
# property the two-build check needs; KERNEL-REDUCIBILITY OF THE SUBJECT is.
#
# So every reject case names `_WITNESS_REF` explicitly: the `pos-control-direct`
# source, a loop-free impl of this same byte-identical spec that the gate
# independently checks (a) shares the frozen spec and (b) VERIFIES, before
# refuting the witness against it. An impl the verifier accepts cannot violate
# its own spec, so a genuine "the spec is violated here" claim must still fail
# there. Against THAT subject the exit code TRACKS the claim (re-measured, per
# case, with real builds):
#
#   the witness's claim   (`…Tester x = false`) -> exit 1,
#     "Tactic `decide` PROVED that the proposition … is false" — a semantic
#     refutation by evaluation, the claim decided rather than stuck
#   the FORGED opposite   (`…Tester x = true`)  -> exit 0, green
#
# That pair is the discrimination. It is named rather than left to the gate's
# stuck-reduction fallback so the artifact itself records which impl each
# refutation was checked against.
_WITNESS_REF = _reproved("    return validName s",
                         "prove_correct validateBlueprintName by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each was verified out-of-band with
    # a real build (its retuned `prove_correct` closes for the new impl shape).
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no loop. `out` IS `validName s`, so the clause holds definitionally and
        # `loom_solve` closes it outright. Because `validName` is GROUNDED in `s`
        # (its dot test is the transparent front-recursive fold, not an opaque
        # answer key), this doubles as proof the spec is not echo-vulnerable: any
        # WRONG accept/reject decision fails `out = validName s`.
        "module": _reproved(
            "    return validName s",
            "prove_correct validateBlueprintName by\n  loom_solve"),
        "rationale": "the post-image `validName s` is GROUNDED in the input (a "
                     "transparent total `def` whose dot test is the front-recursive "
                     "fold `containsDot`, no opaque answer key), so `return validName "
                     "s` is the honest cheapest CORRECT impl; the clause is literally "
                     "`out = validName s`, so it MUST verify, else SPEC-TOO-STRONG. "
                     "Re-expresses the nagini pos-control-merged-guard intent (the "
                     "cheapest honest impl over the grounded decision) and shows the "
                     "spec is not echo-vulnerable (any wrong decision fails the "
                     "clause).",
    },
    {
        "id": "pos-control-commuted-conj",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a loop-free impl that COMMUTES the two sub-decisions of the
        # conjunction (dot-freeness first, then non-emptiness). Both conjuncts are
        # independent booleans, so the order is immaterial to the value; the proof
        # closes under `simp [validName, Bool.and_comm]`.
        "module": _reproved(
            "    return !containsDot s && !s.isEmpty",
            "prove_correct validateBlueprintName by\n"
            "  loom_solve\n"
            "  simp [validName, Bool.and_comm]"),
        "rationale": "a correct impl with the two sub-decisions of the acceptance "
                     "conjunction COMMUTED (dot-freeness before non-emptiness) must "
                     "verify; the two conjuncts are independent booleans so the order "
                     "is immaterial to `out = validName s`. Ports the nagini "
                     "pos-control-reorder-guard (which reorders the two reject guards): "
                     "the accept set is unchanged. If it fails => SPEC-TOO-STRONG "
                     "(over-fit to the frozen conjunct order).",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-self-call, and AIMED AT
    # CONCRETE INPUTS. The nagini case self-calls to establish that the
    # precondition `Acc(list_pred(.),1/2)` admits an F2P/P2P-shaped accepted name.
    # This method carries NO `require` clause (the pre-conditions region is empty),
    # so nothing can exclude any input and that literal probe has no counterpart.
    #
    # An earlier revision took that as licence to ship the FROZEN FILE unchanged as
    # the admissibility case. Under audit that is a case that tests nothing: it is
    # byte-identical to the artifact G-VERIFY already builds, so it re-runs an
    # existing gate rather than asking a new question, and it would pass no matter
    # how unsatisfiable the post-image were at the inputs that matter.
    #
    # The analogue on a require-free total carrier is the obligation being
    # UNSATISFIABLE AT EXACTLY AN F2P-SHAPED INPUT, which this case now probes
    # directly: BEFORE closing the frozen obligation verbatim, it discharges the
    # post-image BY EVALUATION at the three concrete points the F2P and P2Ps pin —
    # the empty name `[]` (validName = false: the rejection the F2P demands), an
    # accepted name `"ok"` (validName = true: what every constructing P2P needs),
    # and a dotted name `"a.b"` (validName = false: the P2P dot refusal). Each is a
    # `have … := by decide`, so a point at which the post-image could not be
    # satisfied would fail the build HERE, before the frozen script runs. The
    # `have`s are then `clear`ed so the frozen proof closes from an unchanged
    # context — the obligation is reproven verbatim, not weakened, and the tactic
    # body is elided from the spec view so same_spec and the obligation header are
    # untouched (asserted by `_swap`). Built out-of-band: exit 0.
    # =====================================================================
    {
        "id": "admiss-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct validateBlueprintName by\n"
            "  have hEmpty : validName ([] : List Char) = false := by decide\n"
            "  have hAccept : validName \"ok\".toList = true := by decide\n"
            "  have hDot : validName \"a.b\".toList = false := by decide\n"
            "  clear hEmpty hAccept hDot\n"
            "  loom_solve\n"
            "  · rw [containsDot_drop_step s i (by omega) (by omega)]\n"
            "    simp_all [Bool.or_comm]\n"
            "  · simp_all [validName, List.drop_zero]"),
        "rationale": "the method declares no `require`, so the decision is total and "
                     "nothing can exclude an input; the PRECOND-TOO-STRONG analogue "
                     "here is the post-image being unsatisfiable at an F2P-shaped "
                     "input. This case discharges `validName s` BY EVALUATION at the "
                     "three points the tests pin — `[]` (= false, the empty-name "
                     "rejection the sole F2P demands), `\"ok\"` (= true, what every "
                     "constructing P2P needs), `\"a.b\"` (= false, the P2P dot "
                     "refusal) — as `have`s that must build BEFORE the frozen "
                     "obligation is closed verbatim. A point where the post-image "
                     "admitted no value would fail those `decide`s. Re-aimed from the "
                     "nagini admiss-self-call, whose precondition-admits-F2P half has "
                     "no counterpart on a require-free carrier; unlike the frozen file "
                     "this asks a question G-VERIFY does not already answer. Else "
                     "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a DISTINCT
    # concrete input (ELABORATES against the rival, FAILS against gold — both halves
    # confirmed out-of-band with real builds) and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test. Each rival
    # is LOOP-FREE so its extracted `…Exec` reduces and the tester `decide`s; the
    # frozen spec is untouched. The single binder `s` is varied across four points
    # that separate the two sub-decisions.
    # =====================================================================
    {
        "id": "reject-drop-empty-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled bug (the pre-fix behaviour): drop the non-emptiness
        # sub-decision, so an empty, dot-free name is ACCEPTED (`out = true`)
        # instead of rejected. Correct on every non-empty input, wrong on `[]`.
        "module": _rival("    return !containsDot s"),
        "refinement": "drops the non-emptiness check — exactly the pre-fix behaviour "
                      "(the constructor accepted an empty name). Its faithful real "
                      "counterpart is the unpatched constructor, which is precisely "
                      "what FAILS the sole F2P (an empty construction name must be "
                      "refused with a ValueError but the pre-fix code constructs it) — "
                      "it would NOT resolve. This is the bug the fix removes.",
        "rationale": "REJECT from `out = validName s` on its non-emptiness conjunct "
                     "(`!s.isEmpty`): at `s = []` gold rejects (validName [] = false) "
                     "but the rival accepts (!containsDot [] = true), so the decisions "
                     "differ. The DISCRIMINATING clause the fix defends. Correct on "
                     "every non-empty input, wrong on the empty name (partial-domain). "
                     "Refuted at `[]`. If it verified => SPEC-TOO-WEAK (admits the very "
                     "bug).",
        "witness": _witness("validateBlueprintNameTester ([] : List Char)"),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "reject-drop-dot-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the dot sub-decision, so a dotted name is ACCEPTED instead of
        # rejected. Correct on every dot-free input, wrong on any name carrying a
        # dot.
        "module": _rival("    return !s.isEmpty"),
        "refinement": "drops the dot check the fix leaves in place. Its faithful real "
                      "counterpart removes the guard that refuses a dotted construction "
                      "name, which FAILS the P2P asserting a dotted name is refused "
                      "with a ValueError — it would NOT resolve.",
        "rationale": "REJECT from `out = validName s` on its dot-freeness conjunct "
                     "(`!containsDot s`): at `s = \".\"` gold rejects (containsDot "
                     "\".\" = true so validName = false) but the rival accepts "
                     "(!isEmpty = true), so the decisions differ. Attacks the OTHER "
                     "sub-decision — a distinct conjunct of the clause. Refuted at "
                     "`\".\"`. If it verified => SPEC-TOO-WEAK (the dot guarantee is "
                     "hollow).",
        "witness": _witness('validateBlueprintNameTester ".".toList'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "reject-partial-leading-dot",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the dot sub-decision: reject the empty name and a name
        # whose FIRST code point is the dot, but miss dots elsewhere. Correct on
        # empty and leading-dot names; diverges on any interior-dot name.
        "module": _rival("    return !s.isEmpty && s.head? != some '.'"),
        "refinement": "weakens the dot check to only the FIRST code point (a leading "
                      "dot), so a name whose dot is interior (e.g. \"a.b\") is "
                      "accepted. Its faithful real counterpart checks only a leading "
                      "dot, so it accepts a dotted name like \"app.ui\", FAILING the "
                      "P2P that asserts such a name is refused — it would NOT resolve.",
        "rationale": "REJECT from `out = validName s` on the interior-dot sub-domain: "
                     "at `s = \"a.b\"` gold rejects (containsDot = true) but the rival "
                     "accepts (non-empty, first code point not a dot), so the decisions "
                     "differ. A genuine partial-domain break — correct on empty and on "
                     "leading-dot names, wrong on the interior-dot sub-domain — that "
                     "proves the dot decision must span the WHOLE sequence, not just "
                     "the head. Ports the nagini rival-partial-domain-leading-dot. "
                     "Refuted at `\"a.b\"` (a distinct point from the leading-dot "
                     "`\".\"`). If it verified => SPEC-TOO-WEAK (domain-incomplete dot "
                     "check).",
        "witness": _witness('validateBlueprintNameTester "a.b".toList'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "reject-over-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-rejection near-miss: reject EVERY name (return the constant false),
        # so an accepted (non-empty, dot-free) name is refused. Correct on every
        # rejected name, wrong on every accepted one.
        "module": _rival("    return false"),
        "refinement": "unconditionally rejects every name. Its faithful real "
                      "counterpart refuses a valid construction name too, which FAILS "
                      "every P2P that constructs a blueprint with an ordinary name "
                      "(used throughout the suite) — it would NOT resolve.",
        "rationale": "REJECT from `out = validName s`: at the accepted name `s = "
                     "\"ok\"` (non-empty, dot-free) gold accepts (validName = true) but "
                     "the rival returns the constant false, so the decisions differ. "
                     "The near-miss that varies the binder to the ACCEPT sub-domain "
                     "(the only witness at an accepted input), demonstrating the clause "
                     "pins acceptance and not merely rejection. Ports the nagini "
                     "rival-over-reject. Refuted at `\"ok\"`. If it verified => "
                     "SPEC-TOO-WEAK (admits rejecting valid names).",
        "witness": _witness('validateBlueprintNameTester "ok".toList'),
        "witness_reference": _WITNESS_REF,
    },
    {
        "id": "reject-off-by-one-length",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED UNDER AUDIT. The four ported rivals leave the emptiness
        # sub-decision attacked in ONE direction only: every rival that gets the
        # boundary wrong gets it wrong by ACCEPTING too much at length 0
        # (reject-drop-empty-guard) or by rejecting EVERYTHING
        # (reject-over-reject, refuted at the 2-code-point name "ok"). Nothing
        # probed the boundary from the other side — a decision that reads
        # "non-empty" as "more than one code point", which is correct at length 0
        # AND on every name of length >= 2, and wrong only on the SINGLETON
        # accepted name. That is the tightest near-miss the emptiness conjunct
        # admits, and `pts` counted four inputs none of which was a 1-code-point
        # accepted name, so the shipped set could not separate `!s.isEmpty` from
        # `s.length > 1`. Refuted at `"a"`; built out-of-band (rival 0, reference
        # 1 refuted-by-evaluation, forged opposite 0).
        "module": _rival("    return !containsDot s && decide (s.length > 1)"),
        "refinement": "reads the non-emptiness requirement as a MINIMUM LENGTH OF TWO, "
                      "so a one-code-point name is refused. Its faithful real "
                      "counterpart refuses a single-character construction name, which "
                      "FAILS the P2Ps that construct blueprints with short ordinary "
                      "names and register them — it would NOT resolve, while still "
                      "refusing the empty name the F2P is about.",
        "rationale": "REJECT from `out = validName s` on the emptiness conjunct at its "
                     "OTHER boundary: at `s = \"a\"` gold accepts (non-empty, dot-free "
                     "=> validName = true) but the rival rejects (length is not > 1), "
                     "so the decisions differ. The tightest near-miss in the battery — "
                     "it agrees with the spec on the empty name, on every dotted name, "
                     "and on every accepted name of two or more code points, differing "
                     "ONLY at the singleton. This pins that the clause requires at "
                     "least ONE code point and not at least two, a distinction no "
                     "shipped rival could separate. Refuted at `\"a\"` (a fifth "
                     "distinct point). If it verified => SPEC-TOO-WEAK (the emptiness "
                     "boundary would be off by one).",
        "witness": _witness('validateBlueprintNameTester "a".toList'),
        "witness_reference": _WITNESS_REF,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts `validate_name(name, import_name)` — the empty
# guard AND the dot guard AND the base-init exception channel over `import_name`,
# with both list inputs held read-only at `Acc(.,1/2)`. This velvet bundle models
# ONLY the pure accept/reject DECISION on the name's code points
# (`validateBlueprintName (s : List Char) → Bool`, mapping.md §1): the base
# initialiser is abstracted away (it never inspects `name` and observes no state
# this Bool decision measures — mapping.md §2–§3). That is carrier narrowing.
#
#   nagini case                       -> here                          disposition
#   ---------------------------------------------------------------------------------
#   pos-control-merged-guard          -> pos-control-direct            RE-EXPRESSED
#   pos-control-reorder-guard         -> pos-control-commuted-conj     PORTED
#   admiss-self-call                  -> admiss-f2p-points             RE-AIMED
#   rival-drop-empty-guard            -> reject-drop-empty-guard       PORTED
#   rival-drop-dot-guard              -> reject-drop-dot-guard         PORTED
#   rival-partial-domain-leading-dot  -> reject-partial-leading-dot    PORTED
#   rival-over-reject                 -> reject-over-reject            PORTED
#   (none — added under audit)        -> reject-off-by-one-length      NEW (gap)
#   frame-mutate-name                 -> (none)                        VACUOUS (no heap)
#   frame-mutate-import-name          -> (none)                        VACUOUS (no heap)
#   rival-wrong-exc-on-reject         -> (none)                        VACUOUS (no channel)
#   AXIOM_TESTS (3, init_base)        -> (none)                        DROPPED (G-AX lane)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness.
#
# RE-EXPRESSED (pos-control-merged-guard -> pos-control-direct): the nagini
#   merged-guard positive is the cheapest HONEST impl over the grounded dot fold.
#   Here the grounded decision is `validName s` itself, so the cheapest honest
#   correct impl is `return validName s` — it verifies, and because `validName`
#   reduces to a computation on `s` (not an opaque oracle) there is no wrong echo
#   that could verify. Same argument, expressed for this carrier.
# PORTED (pos-control-reorder-guard -> pos-control-commuted-conj): the nagini
#   positive reorders the two reject guards; the accept set is unchanged. Here the
#   two guards are the two conjuncts of `validName`, so the analogue commutes the
#   conjunction — order-immaterial, verifies.
# RE-AIMED (admiss-self-call -> admiss-f2p-points): the nagini case self-calls to
#   show the precondition `Acc(list_pred(.),1/2)` admits an accepted name. This
#   method has NO `require`, so nothing can exclude any input and that literal
#   probe has no counterpart. The analogue on a total require-free carrier is the
#   obligation being unsatisfiable AT AN F2P-SHAPED INPUT, so the case discharges
#   the post-image by EVALUATION at `[]`, `"ok"` and `"a.b"` as `have`s that must
#   build before the frozen obligation is closed verbatim. An earlier revision
#   shipped the frozen file unchanged here; that re-ran G-VERIFY instead of asking
#   an admissibility question, and was replaced under audit.
# NEW (reject-off-by-one-length): added under audit, no nagini counterpart. The
#   ported rivals attack the emptiness conjunct only from the accept-too-much side;
#   nothing separated `!s.isEmpty` from `s.length > 1`. This rival is correct at
#   length 0, on every dotted name, and on every accepted name of length >= 2,
#   differing from the spec ONLY at the singleton accepted name — refuted at `"a"`,
#   a fifth distinct point.
# PORTED (the four reject rivals): drop-empty-guard (the G-DIFF bug), drop-dot-
#   guard, partial-domain-leading-dot, over-reject carry across directly — only
#   the carrier changes from a nagini `List[int]` of code points to a Velvet
#   `List Char`, and the reject is now carried by a machine-checked tester witness
#   (nagini relied on Viper discharging the postcondition; a tactic-proof backend
#   needs the explicit discriminator, per the porting rules).
#
# VACUOUS (frame-mutate-name, frame-mutate-import-name): this backend is
#   referentially transparent, declares no `mut` binder, and has no heap — there
#   is no read-only input to overwrite and no substitute probe. Not fabricated
#   (porting map: this class is vacuous on Lean/Velvet).
# VACUOUS (rival-wrong-exc-on-reject): the nagini case turns on the two DISJOINT
#   exception channels pinned by the `init_base` axiom over `import_name`. This
#   bundle abstracts the base initialiser away entirely (mapping.md §2–§3) and
#   collapses accept/reject to a single `Bool` with no `import_name` binder and no
#   exception-channel distinction. There is no second channel for a rival to
#   mis-route through and no witness could discriminate one, so there is no rival
#   to write — legitimately omitted (carrier narrowing), not dropped for
#   difficulty.
#
# DROPPED (AXIOM_TESTS): the nagini file's three init_base soundness/containment
#   probes over the real flask base initialiser are G-AX's job (axiom_check.py /
#   mapping.md); the G-PBT gate ignores AXIOM_TESTS regardless. This bundle also
#   declares no consumed axiom (ConstructOutcome analogue absent; mapping.md §3).
#
# CLAUSE / BINDER / POINT COVERAGE. The single clause `out = validName s` is
#   attacked on BOTH of its independent sub-decisions: non-emptiness
#   (reject-drop-empty-guard) and dot-freeness (reject-drop-dot-guard,
#   reject-partial-leading-dot), plus the accept sub-domain (reject-over-reject).
#   The emptiness conjunct is attacked from BOTH sides of its boundary:
#   accept-too-much at length 0 (reject-drop-empty-guard) and reject-too-much at
#   length 1 (reject-off-by-one-length, added under audit). Both positives and the
#   admissibility case defend the clause. The single binder `s` is varied across
#   FIVE distinct input points (pts=5): `[]` (empty), `"."` (leading dot), `"a.b"`
#   (interior dot), `"ok"` (accepted, 2 code points), `"a"` (accepted, 1 code
#   point — the emptiness boundary from above). No binder is held at a single
#   value across the reject set, and the accept/reject decision is exercised on
#   both outcomes.
#
# WITNESS MECHANICS: the spec is a `method` contract, reached through the tester
#   machinery (`validateBlueprintNameTester s = false`). Each rival is written
#   LOOP-FREE so its `…Exec` reduces and the tester `decide`s. The SUBJECT the
#   witness is refuted against is `_WITNESS_REF`, NOT the frozen solution: gold's
#   `while` loop under demonic choice elaborates through `Classical.choice`, so
#   `decide` on the frozen tester is STUCK for every claim and its exit code
#   carries no information (re-measured under audit — the witness and its exact
#   opposite produce the byte-identical stuck-reduction error). See the CARRIER
#   NOTE at `_WITNESS_REF` for the full exit matrix. Against the loop-free
#   verifying reference the exit code TRACKS the claim: witness -> exit 1 "`decide`
#   PROVED that the proposition … is false" (refuted by evaluation), forged
#   opposite -> exit 0. No witness binds a hypothesis (every input is a concrete
#   literal), so no consistency probe is needed and no banned token
#   (sorry/admit/native_decide/axiom/opaque) appears.
AXIOM_TESTS = []
