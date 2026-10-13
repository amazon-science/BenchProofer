"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25775 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and every ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with every obligation closed); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a boolean carrier)
------------------------------------------------------------
A single modeled function resolves an effective boolean preference from three
sources, in increasing priority:

  resolve (rcDefault : Bool) (ctorArg laterSet : Option Bool) : Bool
    result = laterSet.getD (ctorArg.getD rcDefault)

  * ``rcDefault`` — a global default boolean (the configured fallback);
  * ``ctorArg`` — an optional value chosen at creation (``none`` = omitted, so
    the global default stands);
  * ``laterSet`` — an optional value chosen by a later explicit assignment
    (``none`` = never assigned, so the previously-resolved value stands).

The load-bearing clauses of ``result = laterSet.getD (ctorArg.getD rcDefault)``:
  (D1) laterSet = none, ctorArg = none  =>  result = rcDefault    (fallback)
  (D2) ctorArg = some v (laterSet = none) =>  result = v          (creation wins)
  (D3) laterSet = some v                =>  result = v            (later wins)
These are exactly what the F2P tests observe: a value chosen at creation is read
back verbatim (D2 / test_get_antialiased txt2,txt3), a value chosen by a later
assignment is read back verbatim (D3 / test_set_antialiased), and with no
per-object choice the global default stands (D1 / test_get_antialiased txt4).

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models FOUR heap procedures (build/set/get/copy) over a
mutable object carrying two fields — a boolean preference AND a redraw flag —
under fractional permissions. This lean carrier is referentially transparent and
abstracts the whole thing to ONE pure resolution over ``(rcDefault, ctorArg,
laterSet)``. Three of the nagini classes therefore have NO expressible instance
here and are omitted deliberately (see the ``assessment`` in the port report):

  * FRAME / PERMISSION MUTATION — VACUOUS. No input carries a heap permission;
    there is no read-only half-permission to overwrite and no aliasing. The two
    mandatory nagini frame rivals (get-pref forced write, copy-state src write)
    have no counterpart and no substitute is fabricated.
  * REDRAW-FLAG (``dirty``/``stale``) rivals — VACUOUS. The lean model carries no
    redraw flag; the resolution is a pure value. The nagini rivals that DROP the
    stale flag (set-no-dirty, copy-no-dirty) attack a component this carrier does
    not model, so they cannot be re-expressed.
  * COPY-STATE (``update_from``) rivals — VACUOUS. Object-to-object propagation is
    not part of the modeled resolution kernel; the copy rivals (copy-no-pref) map
    onto no clause of ``result = laterSet.getD (ctorArg.getD rcDefault)``.
  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the inputs
    (an equality against a term built only from ``rcDefault``/``ctorArg``/
    ``laterSet``, fully unfolded); the bundle declares no ``opaque``/``axiom``, so
    there is no answer key to echo. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS (``pos-*``) that must verify.

BINDER COVERAGE. The three input binders are each load-bearing for some rival,
and — importantly — the reject witnesses VARY each of them rather than probing a
single input point:

  * ``ctorArg`` — ``weak-ignore-ctor`` (dropped at ``some true``).
  * ``laterSet`` — ``weak-ignore-later`` / ``weak-negate-later`` (at ``some true``).
  * ``rcDefault`` — attacked at BOTH polarities, which matters because the
    fallback is the one input a rival can hard-code invisibly: ``weak-default-true``
    seeds the fallback ``true`` (refuted at ``rcDefault = false``),
    ``weak-default-false`` seeds it ``false`` (refuted at ``rcDefault = true``), and
    ``weak-default-leaks-through`` lets the global default survive a per-object
    choice instead of being superseded — refutable ONLY at ``rcDefault = true``,
    since at ``rcDefault = false`` the leak is unobservable. Without that last
    rival every witness would sit at ``rcDefault = false`` and a rival that
    mishandled the fallback path alone could not be distinguished.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases … <;> rfl`` is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each is stated directly against the
spec predicate at ``decide``-able boolean literals, and each was checked to hold
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology).

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the inputs, so there is no
axiom-soundness / axiom-containment obligation to probe here (that lane belongs
to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25775"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the single impl region, and the FULL tactic body of the
# single proof region, so every replacement lands entirely inside the region it
# means to edit.
_I_GOLD = (
    "  Id.run do\n"
    "    let mut acc := rcDefault\n"
    "    if let some b := ctorArg then\n"
    "      acc := b\n"
    "    if let some b := laterSet then\n"
    "      acc := b\n"
    "    return acc\n"
)
_P_GOLD = (
    "  intro rcDefault ctorArg laterSet\n"
    "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
    "  cases ctorArg <;> cases laterSet <;> rfl\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_textAntialiased` statement byte-identical; where
    # the frozen `cases … <;> rfl` still closes the new shape it is retained,
    # else the obligation is re-proved with core lemmas only — no helper lemma,
    # no axiom, no assumption token.
    # =====================================================================
    {
        "id": "pos-resolve-match",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: spell the priority order as an explicit nested
        # pattern match (later value if present, else creation value if present,
        # else the global default) instead of the accumulator loop. Same value on
        # every input, so the frozen `cases … <;> rfl` still closes each leg.
        "module": _swap(
            _BASE, _I_GOLD,
            "  match laterSet with\n"
            "  | some b => b\n"
            "  | none =>\n"
            "    match ctorArg with\n"
            "    | some b => b\n"
            "    | none => rcDefault\n",
        ),
        "rationale": "a correct reshape of the resolution (the priority order "
                     "written as a nested match on the later value then the "
                     "creation value, falling through to the default) must "
                     "satisfy `result = laterSet.getD (ctorArg.getD rcDefault)`; "
                     "if it cannot, the resolution postcondition is "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
                     "(`cases ctorArg <;> cases laterSet <;> rfl` closes each arm "
                     "definitionally).",
    },
    {
        "id": "pos-resolve-init-collapse",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the creation-time override into the initial value: seed the
        # accumulator with the creation-resolved value, then apply only the later
        # assignment. Same accumulator flow, same result on every input.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := ctorArg.getD rcDefault\n"
            "    if let some b := laterSet then\n"
            "      acc := b\n"
            "    return acc\n",
        ),
        "rationale": "seeding the accumulator with the creation-resolved value "
                     "(`ctorArg.getD rcDefault`) and then applying only the later "
                     "assignment preserves `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG). Proof: frozen tactic body retained "
                     "(`cases ctorArg <;> cases laterSet <;> rfl`).",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack here;
    # the honest analogue is to discharge the spec predicate at a ground
    # creation-choice input (a value chosen at creation, no later assignment) by
    # evaluation, inside the proof region, alongside the frozen obligation. If
    # that ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-resolve-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_GOLD,
            "  have _ground : problem_spec_textAntialiased false (some true) none\n"
            "      (implementation_textAntialiased false (some true) none) := by\n"
            "    unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "    decide\n"
            + _P_GOLD,
        ),
        "rationale": "the resolution obligation is discharged at a ground "
                     "creation-choice input (a value chosen at creation with no "
                     "later assignment, and a contrary global default) by "
                     "`decide`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal "
                     "input, the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-ignore-ctor",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the creation-time choice entirely: the fallback stands even when
        # a value was chosen at creation. This is the pre-existing behavior of the
        # leg (the creation choice never overrides the global default).
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := rcDefault\n"
            "    if let some b := laterSet then\n"
            "      acc := b\n"
            "    return acc\n",
        ),
        "refinement": "a resolution that ignores the creation-time choice reads "
                      "back the global default for an object created with an "
                      "explicit choice; the F2P tests assert an object created "
                      "with an explicit True/False reads back exactly that value, "
                      "which FAILS when the creation choice is dropped. It would "
                      "NOT resolve — this is the leg's prepatch.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: at laterSet = none with ctorArg = some v the "
                     "spec requires v and the rival returns rcDefault.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased false (some true) none\n"
            "    (implementation_textAntialiased false (some true) none) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-default-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Honours both choices but hard-codes the fallback to True instead of the
        # global default: wrong on the no-choice sub-domain when the default is
        # False.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := true\n"
            "    if let some b := ctorArg then\n"
            "      acc := b\n"
            "    if let some b := laterSet then\n"
            "      acc := b\n"
            "    return acc\n",
        ),
        "refinement": "seeding the fallback to a constant True (rather than the "
                      "global default) makes an object with no per-object choice "
                      "read back True even when the configured default is False; "
                      "the F2P tests assert the no-choice object reads back the "
                      "global default, which FAILS whenever that default is "
                      "False. Verify-not-resolve break on the fallback "
                      "sub-domain.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: at ctorArg = none and laterSet = none with "
                     "rcDefault = false the spec requires false and the rival "
                     "returns true.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased false none none\n"
            "    (implementation_textAntialiased false none none) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-later",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the later assignment: a later explicit choice never takes effect,
        # so the previously-resolved value stands. This is the no-op-setter
        # prepatch of the leg.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := rcDefault\n"
            "    if let some b := ctorArg then\n"
            "      acc := b\n"
            "    return acc\n",
        ),
        "refinement": "a resolution that ignores the later explicit assignment "
                      "leaves the previously-resolved value in effect after an "
                      "explicit assignment; the F2P test that assigns a value and "
                      "reads it back asserts the assigned value is returned, which "
                      "FAILS for a no-op assignment. It would NOT resolve — this "
                      "is the leg's prepatch.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: at laterSet = some v the spec requires v and "
                     "the rival returns ctorArg.getD rcDefault (here rcDefault).",
        "witness": (
            "example : ¬ problem_spec_textAntialiased false none (some true)\n"
            "    (implementation_textAntialiased false none (some true)) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-negate-later",
        "kind": "uniqueness",
        "expect": "reject",
        # Applies the later assignment but stores its NEGATION: wrong for both a
        # True and a False later choice.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := rcDefault\n"
            "    if let some b := ctorArg then\n"
            "      acc := b\n"
            "    if let some b := laterSet then\n"
            "      acc := !b\n"
            "    return acc\n",
        ),
        "refinement": "a resolution that inverts the later explicit assignment "
                      "reads back the opposite of the assigned value; the F2P "
                      "test that assigns True and asserts the value read back is "
                      "True FAILS (it reads False). Wrong for both True and False "
                      "assignments — a verify-not-resolve break.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: at laterSet = some v the spec requires v and "
                     "the rival returns !v.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased false none (some true)\n"
            "    (implementation_textAntialiased false none (some true)) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-default-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of `weak-default-true`: honours both per-object choices but
        # hard-codes the fallback to False instead of the global default. Wrong on
        # the no-choice sub-domain when the global default is TRUE — the opposite
        # polarity of the fallback, which no other rival here probes.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := false\n"
            "    if let some b := ctorArg then\n"
            "      acc := b\n"
            "    if let some b := laterSet then\n"
            "      acc := b\n"
            "    return acc\n",
        ),
        "refinement": "seeding the fallback to a constant False (rather than "
                      "consulting the global default) makes an object with no "
                      "per-object choice read back False even when the configured "
                      "default is True; the F2P tests assert the no-choice object "
                      "reads back the global default, and the configured default "
                      "they run under is True, so this FAILS. Verify-not-resolve "
                      "break on the fallback sub-domain at the polarity the "
                      "constant-True seed cannot expose.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: at ctorArg = none and laterSet = none with "
                     "rcDefault = true the spec requires true and the rival "
                     "returns false. Together with `weak-default-true` this pins "
                     "the fallback at BOTH values of the rcDefault binder, so no "
                     "rival can hard-code a fallback constant and survive.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased true none none\n"
            "    (implementation_textAntialiased true none none) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-default-leaks-through",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the INDEPENDENCE half of the rule: a per-object choice is
        # combined with the global default instead of overriding it, so the
        # default still leaks into the resolved value after a per-object choice
        # was made. Wrong exactly when the global default is TRUE and the
        # per-object choice is FALSE — a sub-domain (rcDefault = true, a `some
        # false` choice) no other rival reaches.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    let mut acc := rcDefault\n"
            "    if let some b := ctorArg then\n"
            "      acc := b || rcDefault\n"
            "    if let some b := laterSet then\n"
            "      acc := b || rcDefault\n"
            "    return acc\n",
        ),
        "refinement": "combining a per-object choice with the global default "
                      "(instead of letting the choice override it) makes an "
                      "object created with — or later assigned — an explicit "
                      "False read back True whenever the configured default is "
                      "True; the F2P tests assert an object given an explicit "
                      "False reads back False, and the configured default they "
                      "run under is True, so this FAILS. A faithful patch that "
                      "merged the per-object flag with the global one rather than "
                      "superseding it would NOT resolve.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`, whose right-hand side does NOT mention "
                     "rcDefault once a per-object value is present: at rcDefault "
                     "= true with ctorArg = some false and laterSet = none the "
                     "spec requires false and the rival returns true. This is the "
                     "only rival whose defect is invisible at rcDefault = false, "
                     "so it is what makes the rcDefault binder load-bearing.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased true (some false) none\n"
            "    (implementation_textAntialiased true (some false) none) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns a constant True regardless of every input: correct only when the
        # resolved value happens to be True. A read-only body (no branching on the
        # inputs at all), isolating the pure value defect.
        "module": _swap(
            _BASE, _I_GOLD,
            "  Id.run do\n"
            "    return true\n",
        ),
        "refinement": "a resolution that always reports True regardless of the "
                      "inputs reads back True for an object whose resolved "
                      "preference is False; the F2P test that creates an object "
                      "with an explicit False (or reads a False global default) "
                      "asserts the value read back is False, which FAILS. It would "
                      "NOT resolve.",
        "rationale": "REJECT from `result = laterSet.getD (ctorArg.getD "
                     "rcDefault)`: whenever the resolved value is false (e.g. all "
                     "sources false/absent with rcDefault = false) the spec "
                     "requires false and the rival returns true.",
        "witness": (
            "example : ¬ problem_spec_textAntialiased false none none\n"
            "    (implementation_textAntialiased false none none) := by\n"
            "  unfold problem_spec_textAntialiased implementation_textAntialiased resolveAntialiased\n"
            "  decide\n"
        ),
    },
]
