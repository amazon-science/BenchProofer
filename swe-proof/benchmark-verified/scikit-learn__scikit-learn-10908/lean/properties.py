"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10908 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_getFeatureNames``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total behavior over a small state carrier):

  getFeatureNames (st : VecState) : Except VErr (List String)

The ordered feature names are produced whenever a vocabulary is available, and
exactly the documented error is reported otherwise. ``VecState`` carries two
independent optional fields — an already-available (data-derived) vocabulary and
a construction-supplied ordered term list — and the postcondition is a nested
case analysis with these top-level clauses, all pinned by the single obligation:

  * AVAILABLE-VOCABULARY leg — if an available vocabulary is present, an empty
    one reports the empty-vocabulary error, a non-empty one yields its
    index-ordered feature names.
  * SUPPLIED-LIST leg — else, if a construction list was supplied, that list is
    validated; on a validation error THAT error is reported; on success the
    (non-empty) validated vocabulary yields its index-ordered feature names.
  * NO-VOCABULARY leg — else the not-fitted error is reported.

The pre-existing behavior only ever consulted the available-vocabulary field and
reported the not-fitted error whenever it was absent; the corrected behavior adds
the on-demand establishment of the construction-supplied list before the
availability check. The load-bearing discriminants are therefore (a) that a
supplied list is CONSULTED at all when no available vocabulary exists (the
supplied-list leg is not collapsed into the not-fitted error), and (b) that its
validation outcome — success, empty, or duplicate — is faithfully mapped.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: no
    input carries a heap permission, there is no read-only half-permission over
    the supplied list to overwrite and no aliasing to exploit. The nagini
    frame-mutation rival (write into the half-permission constructor list) has no
    expressible instance here and no substitute is fabricated for it.

  * RAISE-PATH SIDE-EFFECT / recorded-flag rivals — VACUOUS. Those nagini rivals
    attack an imperative side effect (a boolean recorded on the object before the
    error surfaces) that the Lean model does not carry: the model is a pure
    input→output relation returning an ``Except``, with no separate observable
    flag. The recorded-flag distinction collapses on this carrier, so those
    rivals have no counterpart and none is invented. What IS modeled — the
    outcome on each state shape — is attacked below.

  * WRONG-MATERIALISATION / SPEC-TOO-WEAK — APPLIES. The nagini wrong-names and
    no-raise rivals port to rivals that misroute one leg of the case analysis
    (ignore the supplied list, swallow the no-vocabulary error, or mis-map the
    validation outcome); each verifies only where its leg happens to agree with
    the spec and is refuted on its own leg. The nagini wrong-names rival ALSO has
    a direct counterpart that misrouting alone does not cover — accept the
    supplied list as valid and then build no names — carried here as
    ``weak-supplied-list-no-materialisation``.

  * DIVERGENCE — APPLIES, and is carried. This bundle sets no
    ``loom.semantics.termination`` option: it is a plain Mathlib carrier where
    every ``def`` must show termination, so a diverging rival is expressible only
    as a ``partial def`` (measured: the same recursion without ``partial`` is
    refused outright with ``fail to show termination``). A ``partial def`` body is
    OPAQUE, which is exactly the condition under which a witness must state its
    refutation by structure rather than by evaluation — and that is landable here:
    a non-terminating implementation ignores its input, so it returns ONE value at
    every state, while the spec forces two DIFFERENT values at two states. Carried
    below as ``diverge-input-independent-nontermination``.

  * SOUNDNESS + ADMISSIBILITY positives — APPLY. A structurally different but
    correct implementation must verify (else SPEC-TOO-STRONG), and the modeled
    behavior must be satisfiable at the F2P-shaped custom-vocabulary input. The
    soundness positive must additionally be a reshape that is NOT DEFINITIONALLY
    EQUAL to the frozen impl: on this carrier ``Id.run``/``let mut`` is pure sugar
    that unfolds to the nested ``match``, so a continuation-style reshape is defeq
    to gold, is closed by the frozen script verbatim, and re-proves nothing while
    passing honestly. The positive below is measured non-defeq (``rfl`` fails).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet proving the rival CONTRADICTS the spec at one
concrete input, stated directly against the spec predicate at literal inputs. Each
was checked to hold of its rival and to FAIL on the frozen solution (so it
discriminates rather than asserting a tautology); ``native_decide`` is banned and
not used.

THE ONE TACTIC FACT EVERY WITNESS HERE DEPENDS ON. The frozen implementation is
written in ``Id.run do`` with a ``let mut`` accumulator, so the result it returns
is wrapped: the spec's equation appears to ``simp`` as ``pure (Except.ok ...) =
Except.ok ...``. ``simp`` will NOT strip that wrapper on its own, and neither
``Id.run``, ``Id.pure_eq``, nor ``Id.run_pure`` in the simp set is enough — the
goal halts as ``¬pure (Except.ok ["a"]) = Except.ok ["a"]``. A witness left in
that state is HOLLOW rather than merely weak, and it is hollow in a way both
builds still look right: the rival build happens to elaborate, the gold build
fails, so the gate records a refutation — but the gold-side failure is a stuck
reduction and NOT a statement about the claim. Measured directly: with the
wrapper unstripped, a FORGERY that drops the ``¬`` (i.e. asserts the frozen
solution is CORRECT at that input, the opposite of a refutation) fails on gold
with the byte-identical error, differing only in the printed ``¬``. Adding
``pure, Id.instMonad`` to the simp set is what makes the goal reduce to ``False``
on gold, and the same forgery then ELABORATES on gold (exit 0) — so the exit code
tracks what is claimed. Every witness below therefore carries ``pure,
Id.instMonad``, and this is a load-bearing requirement of the carrier, not
tidiness.

A corollary, recorded because an earlier revision of this file asserted the
opposite and the assertion foreclosed real rivals: it is NOT true that a witness
here must be a CONSTRUCTOR CLASH (an error tag vs a different tag, or an error vs
an ``ok``). The ordering helper (``mergeSort``) and the validator's ``dedup`` DO
reduce on small literals, so a rival that returns an ``ok`` on exactly the states
the spec does is still refutable on the list VALUE inside it — which is the only
way to reach the ordering and materialisation clauses at all. Two cases below do
exactly that. The tag clash was never the mechanism doing the work; stripping the
``Id`` wrapper was.

Witness inputs are spread across the modeled state carrier rather than fixed at
one point: the reject witnesses move BOTH fields of ``st`` — the supplied-list
rival at (no available vocabulary, a supplied singleton), the swallow rival at
(no available vocabulary, no list), the fitted-misdetect rival at (an available
singleton, no list), the validation-mismap rival at (no available vocabulary, an
empty supplied list), the precedence rival at (an available EMPTY vocabulary, a
supplied singleton — the only point where both fields are populated), the
ordering rival at an available vocabulary stored OUT of index order, the
error-tag-swap rival at (no available vocabulary, a supplied DUPLICATE list),
and the no-materialisation rival at the supplied-list SUCCESS arm. All three
legs of the case analysis are attacked, and so is each leg's internal structure:
which leg wins when both apply, which of the two validation failures is
reported, whether the names are built at all, and whether they are index-ORDERED.

Two of the rivals (the ordering rival and the no-materialisation rival) return an
``ok`` on exactly the states the spec does and are therefore refutable ONLY on
the list VALUE inside it — the clause a tag clash structurally cannot reach.
Those are stated at small literals where the ordering helper and ``dedup`` do
reduce. ``native_decide`` is banned and not used.

GOLD-SIDE EVIDENCE, per case, re-measured with the wrapper stripped: all eight
reject witnesses now fail on the frozen solution with the goal ``False`` — from
two unequal literal lists for the value-level pair, and from a reduced
constructor/tag disagreement for the other six. For each, the FORGERY that flips
the claim (drops the ``¬``) ELABORATES against the frozen solution (exit 0),
which is what certifies that gold's exit code is a statement about the claim
rather than a stuck reduction.

AXIOM lane: DROPPED. The nagini AXIOM_TESTS (soundness + containment of the
validation A-reference) belong to G-AX, not to this gate; they are omitted here
by design.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10908"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL body of the single impl region, and the FULL tactic body of the single
# proof region, so every replacement lands entirely inside the region it edits.
_I_IMPL = (
    "def implementation_getFeatureNames\n"
    "    (st : VecState) : Except VErr (List String) := Id.run do\n"
    "  let mut voc : List (String × Nat) := []\n"
    "  match st.learned with\n"
    "  | some v => voc := v\n"
    "  | none =>\n"
    "    match st.param with\n"
    "    | none => return Except.error VErr.notFitted\n"
    "    | some p =>\n"
    "      match validateList p with\n"
    "      | Except.error e => return Except.error e\n"
    "      | Except.ok v => voc := v\n"
    "  if voc.isEmpty then return Except.error VErr.empty\n"
    "  return Except.ok (featureNames voc)"
)
_P_PROOF = (
    "  intro st\n"
    "  unfold problem_spec_getFeatureNames implementation_getFeatureNames\n"
    "  simp only [Id.run, bind, pure]\n"
    "  rcases st with ⟨learned, param⟩\n"
    "  cases learned with\n"
    "  | some v =>\n"
    "    simp only\n"
    "    constructor\n"
    "    · intro h; simp [h]\n"
    "    · intro h; simp [h]\n"
    "  | none =>\n"
    "    cases param with\n"
    "    | none => simp\n"
    "    | some p =>\n"
    "      cases hv : validateList p with\n"
    "      | error e => simp [hv]\n"
    "      | ok v =>\n"
    "        simp only [hv]\n"
    "        constructor\n"
    "        · intro h; simp [h]\n"
    "        · intro h; simp [h]"
)

# sanity: both anchors present exactly once in the frozen solution.
assert _BASE.count(_I_IMPL) == 1, "impl anchor drifted from Solution.lean"
assert _BASE.count(_P_PROOF) == 1, "proof anchor drifted from Solution.lean"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # implementation that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Keeps
    # the `theorem correct_getFeatureNames` STATEMENT byte-identical and
    # re-proves it for the new shape; introduces no helper lemma, axiom, or
    # assumption token.
    #
    # AUDIT NOTE (why this case is shaped the way it is). An earlier version of
    # this positive reshaped the `Id.run do` / `let mut` accumulator into a
    # `match` cascade with a shared `finish` continuation. That reshape was
    # measured to be DEFINITIONALLY EQUAL to the frozen impl — `example :
    # implFrozen = implReshaped := rfl` elaborates (exit 0) — and the frozen
    # proof script closed it VERBATIM, without the `simp only [Id.run, bind,
    # pure]` line the case claimed it had to drop (impl swapped, proof left
    # frozen: exit 0). A positive that is defeq to gold exercises no new proof
    # obligation, so it cannot detect SPEC-TOO-STRONG: `Id.run`/`let mut` on
    # `Id` is pure sugar that unfolds to exactly the nested `match`. Replaced
    # with a reshape that is NOT defeq (`rfl` fails with a genuine type
    # mismatch, exit 1): the two Option fields are scrutinised in ONE
    # simultaneous `match`, and the empty-check + ordering tail is DUPLICATED
    # into each producing branch instead of being shared, so the term tree
    # differs structurally and the obligation is genuinely re-proved.
    # =====================================================================
    {
        "id": "pos-control-simultaneous-match-duplicated-tail",
        "kind": "soundness",
        "expect": "verify",
        # Scrutinise BOTH state fields in a single simultaneous `match` and
        # duplicate the empty-check/ordering tail into each producing branch
        # (rather than routing every branch through one shared continuation).
        # Same value on every state; NOT definitionally equal to the frozen
        # accumulator shape, so the obligation is genuinely re-discharged.
        "module": _swap(
            _swap(
                _BASE, _I_IMPL,
                "def implementation_getFeatureNames\n"
                "    (st : VecState) : Except VErr (List String) :=\n"
                "  match st.learned, st.param with\n"
                "  | some v, _ =>\n"
                "    if v.isEmpty then Except.error VErr.empty else Except.ok (featureNames v)\n"
                "  | none, none => Except.error VErr.notFitted\n"
                "  | none, some p =>\n"
                "    match validateList p with\n"
                "    | Except.error e => Except.error e\n"
                "    | Except.ok v =>\n"
                "      if v.isEmpty then Except.error VErr.empty else Except.ok (featureNames v)",
            ),
            _P_PROOF,
            "  intro st\n"
            "  unfold problem_spec_getFeatureNames implementation_getFeatureNames\n"
            "  rcases st with ⟨learned, param⟩\n"
            "  cases learned with\n"
            "  | some v =>\n"
            "    cases param <;> simp only <;>\n"
            "      exact ⟨fun h => by simp [h], fun h => by simp [h]⟩\n"
            "  | none =>\n"
            "    cases param with\n"
            "    | none => simp\n"
            "    | some p =>\n"
            "      cases hv : validateList p with\n"
            "      | error e => simp [hv]\n"
            "      | ok v =>\n"
            "        simp only [hv]\n"
            "        exact ⟨fun h => by simp [h], fun h => by simp [h]⟩",
        ),
        "rationale": (
            "Scrutinising both optional state fields in ONE simultaneous match, "
            "and duplicating the empty-check + index-ordering tail into each "
            "producing branch instead of sharing one continuation, preserves the "
            "exact result on every state, so all three legs of the postcondition "
            "still hold; a correct reshape must verify (else SPEC-TOO-STRONG). "
            "Unlike a `let`-bound-continuation reshape — which is definitionally "
            "equal to the frozen accumulator (`rfl` closes it) and is therefore "
            "closed by the frozen script verbatim, testing nothing — this term "
            "tree is NOT defeq to the frozen one (`rfl` fails with a type "
            "mismatch), so the obligation is genuinely re-discharged: the "
            "available leg is now split across two `param` shapes and the "
            "empty/non-empty split is proved twice over independent branches. No "
            "new declaration, axiom, or assumption token."),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the exact F2P-shaped custom-vocabulary input:
    # no available vocabulary, but a construction-supplied list. The frozen
    # theorem is universally quantified; the honest analogue of the nagini
    # precondition-admission probe is to discharge the spec predicate at this
    # concrete input by evaluation, inside the proof region ALONGSIDE the frozen
    # obligation (which is closed verbatim after). If that ground instance could
    # not be discharged, the newly-modeled behavior would be unsatisfiable at
    # exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-f2p-custom-vocabulary",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_PROOF,
            "  have _ground : problem_spec_getFeatureNames\n"
            "      { learned := none, param := some [\"a\"] }\n"
            "      (implementation_getFeatureNames { learned := none, param := some [\"a\"] }) := by\n"
            "    have hv : validateList [\"a\"] = Except.ok [(\"a\", 0)] := rfl\n"
            "    simp only [problem_spec_getFeatureNames, implementation_getFeatureNames, hv, Id.run]\n"
            "    refine ⟨by simp, fun _ => rfl⟩\n"
            + _P_PROOF,
        ),
        "rationale": (
            "The obligation is discharged at the concrete F2P custom-vocabulary "
            "input (no available vocabulary; a supplied singleton list) by "
            "evaluation, then the frozen obligation is closed verbatim. Verifies "
            "(else the newly-modeled supplied-list behavior is unsatisfiable at "
            "the normal input — the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: no new declaration, the theorem statement is byte-identical, "
            "and the ground instance is a `have` inside the existing tactic body "
            "whose only fact is `validateList [\"a\"] = ok [(\"a\", 0)]`, closed by "
            "`rfl`."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the graded suite,
    # so a verifying rival is a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input by a constructor clash.
    # =====================================================================
    {
        "id": "weak-ignore-supplied-list",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-existing behavior: when no available vocabulary exists, report
        # the not-fitted error unconditionally, never consulting the supplied
        # construction list. Verifies only where no list was supplied; refuted
        # wherever a list was supplied (the SUPPLIED-LIST leg).
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none => return Except.error VErr.notFitted\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This is exactly the pre-existing behavior: the availability check "
            "fires whenever no data-derived vocabulary is present, without first "
            "establishing the construction-supplied list. In the F2P a "
            "custom-vocabulary object (a supplied 9-term list, never fitted from "
            "data) is queried for its feature names; the faithful real analogue "
            "reports the not-fitted error instead of the list, so the "
            "custom-vocabulary assertion FAILS and it does NOT resolve."),
        "rationale": (
            "REJECT from the SUPPLIED-LIST leg: on a state with no available "
            "vocabulary but a supplied list, the spec requires the validated "
            "list's outcome while the rival returns the not-fitted error. Attacks "
            "the leg the fix adds; if it verified the spec would be SPEC-TOO-WEAK "
            "(admits the pre-existing behavior). Refuted at (no available "
            "vocabulary, supplied singleton) — the F2P-shaped divergence — by the "
            "error-vs-ok constructor clash."),
        "witness": (
            "-- With no available vocabulary but a supplied singleton list the spec\n"
            "-- requires the ok index-ordered names; the pre-existing behavior\n"
            "-- returns the not-fitted error. `pure`/`Id.instMonad` are REQUIRED:\n"
            "-- without them `simp` halts at `¬pure (ok [\"a\"]) = ok [\"a\"]` on BOTH\n"
            "-- subjects, i.e. stuck on the `Id` wrapper rather than refuting, and\n"
            "-- the gold-side exit code would carry no information about the claim.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := none, param := some [\"a\"] }\n"
            "    (implementation_getFeatureNames { learned := none, param := some [\"a\"] }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, featureNames, Id.run, pure, Id.instMonad]\n"
        ),
    },
    {
        "id": "weak-swallow-no-vocabulary-error",
        "kind": "uniqueness",
        "expect": "reject",
        # On the genuinely-no-vocabulary state (no available vocabulary AND no
        # supplied list) the rival does NOT report the not-fitted error; it
        # returns an ok empty list. Verifies on every other state; refuted on the
        # NO-VOCABULARY leg.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.ok []\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error e => return Except.error e\n"
            "      | Except.ok v => voc := v\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This swallows the failure on an object that has neither a data-fitted "
            "vocabulary nor a construction list, returning an empty name list "
            "instead of raising. The F2P asserts that querying feature names on "
            "exactly such an unfitted object RAISES; the faithful real analogue "
            "returns silently, so that assertion FAILS and it does NOT resolve."),
        "rationale": (
            "REJECT from the NO-VOCABULARY leg (`result = Except.error "
            "VErr.notFitted`): on the no-available/no-list state the spec requires "
            "the not-fitted error while the rival returns `ok []`. Attacks the "
            "not-fitted leg specifically; if it verified the spec would be "
            "SPEC-TOO-WEAK on that sub-domain. Refuted at (no available "
            "vocabulary, no list) by the ok-vs-error constructor clash — a "
            "distinct input point from the supplied-list rival."),
        "witness": (
            "-- On a state with no available vocabulary and no supplied list the\n"
            "-- spec requires the not-fitted error; the rival returns ok []. The\n"
            "-- tag clash alone does NOT close it: `pure`/`Id.instMonad` are needed\n"
            "-- to strip the `Id` wrapper, else `simp` halts at\n"
            "-- `¬pure (error notFitted) = error notFitted` on BOTH subjects and\n"
            "-- gold's failure would be a stuck reduction, not a refutation.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := none, param := none }\n"
            "    (implementation_getFeatureNames { learned := none, param := none }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    Id.run, pure, Id.instMonad]\n"
        ),
    },
    {
        "id": "weak-fitted-misdetect",
        "kind": "uniqueness",
        "expect": "reject",
        # When an available (data-derived) vocabulary IS present, the rival still
        # reports the not-fitted error rather than its feature names. Verifies on
        # states with no available vocabulary; refuted on the AVAILABLE-VOCABULARY
        # leg.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some _ => return Except.error VErr.notFitted\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.error VErr.notFitted\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error e => return Except.error e\n"
            "      | Except.ok v => voc := v\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This misdetects availability: even an object with a materialised "
            "data-derived vocabulary is reported as not fitted. The F2P also "
            "queries feature names on a fit-from-data object and asserts they "
            "equal the learned vocabulary; the faithful real analogue raises "
            "instead, so that assertion FAILS and it does NOT resolve — the fix "
            "must not regress the availability path it builds on."),
        "rationale": (
            "REJECT from the AVAILABLE-VOCABULARY leg (`¬ v.isEmpty → result = "
            "Except.ok (featureNames v)`): on a state with a non-empty available "
            "vocabulary the spec requires the ok index-ordered names while the "
            "rival returns the not-fitted error. Attacks the availability leg; "
            "refuted at (an available singleton, no list) by the error-vs-ok "
            "constructor clash — a third distinct input point that moves the "
            "available-vocabulary field the other rivals hold at `none`."),
        "witness": (
            "-- With a non-empty available vocabulary the spec requires the ok\n"
            "-- index-ordered names; the rival returns the not-fitted error.\n"
            "-- `pure`/`Id.instMonad` are required to strip the `Id` wrapper: without\n"
            "-- them `simp` halts at `¬pure (ok [\"a\"]) = ok [\"a\"]` on BOTH subjects,\n"
            "-- so gold's exit code would not track what the witness claims.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := some [(\"a\", 0)], param := none }\n"
            "    (implementation_getFeatureNames { learned := some [(\"a\", 0)], param := none }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    featureNames, Id.run, pure, Id.instMonad]\n"
        ),
    },
    {
        "id": "weak-validation-outcome-mismap",
        "kind": "uniqueness",
        "expect": "reject",
        # The supplied list IS consulted, but a validation ERROR is mis-mapped to
        # the not-fitted error instead of being propagated faithfully. Correct on
        # the validation-success sub-domain; refuted wherever validation fails
        # (the error-propagation arm of the SUPPLIED-LIST leg).
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.error VErr.notFitted\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error _ => return Except.error VErr.notFitted\n"
            "      | Except.ok v => voc := v\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This consults the supplied list but reports the wrong error shape on "
            "an invalid list: an empty or duplicate-term construction list is "
            "surfaced as the not-fitted error rather than the specific "
            "empty/duplicate error the validation raises. The graded suite pins "
            "the concrete error a bad construction vocabulary yields (the "
            "duplicate-index and empty-vocabulary regression tests), which this "
            "mis-maps, so it is not a faithful fix and does NOT leave the suite "
            "resolved."),
        "rationale": (
            "REJECT from the error-propagation arm of the SUPPLIED-LIST leg "
            "(`Except.error e => result = Except.error e`): on a supplied list "
            "that fails validation the spec requires THAT validation error while "
            "the rival collapses it to the not-fitted error. Attacks the "
            "error-faithfulness of the supplied-list leg; refuted at (no available "
            "vocabulary, an empty supplied list) — where validation yields the "
            "empty error — by the notFitted-vs-empty tag clash, a fourth distinct "
            "input point."),
        "witness": (
            "-- An empty supplied list validates to the empty error, which the spec\n"
            "-- must propagate; the rival returns the not-fitted error instead.\n"
            "-- notFitted-vs-empty is a constructor(tag) clash; `validateList []`\n"
            "-- reduces because the empty branch is taken before any dedup fold.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := none, param := some [] }\n"
            "    (implementation_getFeatureNames { learned := none, param := some [] }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, Id.run, Id.pure_eq]\n"
        ),
    },

    # =====================================================================
    # AUDIT ADDITIONS. The four rivals above move the state carrier across all
    # three top-level legs, but each attacks WHICH leg is taken. Four clauses of
    # the postcondition were left entirely unprobed, and a rival is the only
    # thing that can attest to them:
    #   (1) the PRECEDENCE of the two legs when BOTH fields are populated (the
    #       available vocabulary must win over the supplied list);
    #   (2) the CONTENT of the index-ordering (not merely that an `ok` is
    #       returned) — no existing rival returns a wrongly-ordered list;
    #   (3) WHICH validation error is reported (`dup` vs `empty`) — the mismap
    #       rival above collapses both to notFitted, so a rival that swaps the
    #       two error tags against each other is unattacked;
    #   (4) the supplied-list SUCCESS path building the names AT ALL (the
    #       nagini wrong-materialisation rival's real counterpart: validate the
    #       list, then return no names).
    # Each was built and measured: rival module rejected, witness holds of the
    # rival, witness FAILS on the frozen solution by a SEMANTIC goal.
    # =====================================================================
    {
        "id": "weak-supplied-list-takes-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        # Consults the construction-supplied list FIRST and only falls back to
        # the already-available vocabulary when no list was supplied. Agrees with
        # the spec whenever at most one field is populated; refuted where BOTH
        # are, because the spec's outer `match` fixes the available vocabulary as
        # the one that wins.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.param with\n"
            "  | some p =>\n"
            "    match validateList p with\n"
            "    | Except.error e => return Except.error e\n"
            "    | Except.ok v => voc := v\n"
            "  | none =>\n"
            "    match st.learned with\n"
            "    | some v => voc := v\n"
            "    | none => return Except.error VErr.notFitted\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This inverts the priority of the two vocabulary sources: a "
            "construction-supplied list would override an already-materialised "
            "data-derived vocabulary. The faithful real analogue re-derives the "
            "vocabulary from the constructor argument even on an object that has "
            "already been fitted from data, so a fit-then-query object reports "
            "the constructor list rather than what it learned; the graded suite "
            "queries feature names on objects that carry both a supplied list and "
            "a fitted vocabulary and expects the fitted one, so it does NOT "
            "resolve."),
        "rationale": (
            "REJECT from the PRECEDENCE of the two legs, which no other rival "
            "attacks: the spec's outer `match st.learned` fixes the "
            "available-vocabulary leg as the one taken whenever `learned` is "
            "`some`, REGARDLESS of `param`. Refuted at (an available EMPTY "
            "vocabulary, a supplied singleton) — a fifth distinct input point and "
            "the only one where both fields are populated at once — where the spec "
            "demands the empty error from the available leg while the rival "
            "reports the supplied list's `ok`. Measured: rival module exit 1, "
            "witness exit 0 on the rival, exit 1 on the frozen solution with the "
            "goal `False`. The gold-side goal is `False` only because the witness "
            "carries `pure, Id.instMonad`; an earlier revision omitted them and "
            "stalled at `¬pure (Except.error VErr.empty) = Except.error VErr.empty` "
            "— a stuck `Id` wrapper that is NOT evidence, since the flipped claim "
            "failed there identically. Re-measured after adding them: the flipped "
            "claim elaborates on gold (exit 0), so the exit code tracks the claim."),
        "witness": (
            "-- With an available-but-EMPTY vocabulary the spec takes the\n"
            "-- available leg and demands the empty error; this rival prefers the\n"
            "-- supplied singleton and returns its ok names. `pure`/`Id.instMonad`\n"
            "-- are required to strip the `Id` wrapper: without them `simp` halts at\n"
            "-- `¬pure (error empty) = error empty` on BOTH subjects, so gold's\n"
            "-- failure would be a stuck reduction rather than a refutation.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := some [], param := some [\"b\"] }\n"
            "    (implementation_getFeatureNames { learned := some [], param := some [\"b\"] }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, featureNames, Id.run, pure, Id.instMonad]\n"
        ),
    },
    {
        "id": "weak-unordered-feature-names",
        "kind": "uniqueness",
        "expect": "reject",
        # Routes every leg correctly and returns an `ok` exactly where the spec
        # does, but takes the terms in STORED order rather than in increasing
        # index order. Every constructor-tag clash the other rivals rely on is
        # absent: this one can only be caught on the ORDERING content.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.error VErr.notFitted\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error e => return Except.error e\n"
            "      | Except.ok v => voc := v\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (voc.map (·.1))",
        ),
        "refinement": (
            "This returns the vocabulary's terms in whatever order the mapping "
            "happens to store them instead of in increasing index order. The "
            "faithful real analogue drops the index-ordered extraction and emits "
            "the terms in iteration order, so the returned names no longer line "
            "up with the column indices; the graded suite checks, for every "
            "returned name, that its position equals the index the vocabulary "
            "assigns it, and that check FAILS on any vocabulary whose storage "
            "order differs from its index order. It does NOT resolve."),
        "rationale": (
            "REJECT from the ORDERING CONTENT of both producing legs (`result = "
            "Except.ok (featureNames v)`) — the one clause a constructor-tag "
            "clash cannot reach, and the reason this rival is worth carrying: it "
            "returns an `ok` on exactly the states the spec does, so it is caught "
            "only by the VALUE inside the `ok`. Refuted at an available "
            "vocabulary stored out of index order — `[(\"b\", 1), (\"a\", 0)]`, a "
            "sixth distinct input point — where the spec demands `[\"a\", \"b\"]` "
            "and the rival yields `[\"b\", \"a\"]`. Measured: rival module exit 1, "
            "witness exit 0 on the rival, exit 1 on the frozen solution with the "
            "semantic goal `False` (the two literal lists are unequal). The "
            "ordering helper DOES reduce on this two-element literal, so the "
            "witness needs no clash: unfolding `Id`'s `pure` is what closes it."),
        "witness": (
            "-- The available vocabulary is stored out of index order, so the spec's\n"
            "-- index-ordered names are [\"a\", \"b\"] while the rival returns the\n"
            "-- stored order [\"b\", \"a\"]. `mergeSort` reduces on a two-element\n"
            "-- literal, so this is a genuine list-value disagreement rather than a\n"
            "-- constructor clash; `pure`/`Id.instMonad` strip the `Id` wrapper.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := some [(\"b\", 1), (\"a\", 0)], param := none }\n"
            "    (implementation_getFeatureNames { learned := some [(\"b\", 1), (\"a\", 0)], param := none }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    featureNames, List.mergeSort, Id.run, pure, Id.instMonad]\n"
        ),
    },
    {
        "id": "weak-swap-validation-error-tags",
        "kind": "uniqueness",
        "expect": "reject",
        # The supplied list IS consulted and a validation failure IS reported as
        # a validation failure — but the two error shapes are swapped for one
        # another. Strictly finer than the notFitted mismap above, which cannot
        # distinguish the empty error from the duplicate error at all.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.error VErr.notFitted\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error _ => return Except.error VErr.empty\n"
            "      | Except.ok v => voc := v\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This reports every invalid construction list as the "
            "empty-vocabulary failure, including one whose defect is a REPEATED "
            "term. The faithful real analogue surfaces the empty-vocabulary "
            "complaint for a list that names the same term twice, so the graded "
            "regression test that pins the duplicate-term failure for a "
            "repeated-term construction vocabulary sees the wrong failure and "
            "FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from the error-propagation arm of the SUPPLIED-LIST leg, at a "
            "strictly finer grain than the notFitted mismap: that rival collapses "
            "BOTH validation failures to one foreign tag, so it never tests that "
            "the two validation failures are told apart FROM EACH OTHER. This one "
            "propagates a validation error as a validation error and still "
            "mis-identifies which. Refuted at (no available vocabulary, a "
            "supplied duplicate list `[\"a\", \"a\"]`) — a seventh distinct input "
            "point, and the only one that exercises the duplicate branch of the "
            "validator, which no other case reaches. Measured: rival module exit "
            "1, witness exit 0 on the rival, exit 1 on the frozen solution with "
            "the semantic goal `False`."),
        "witness": (
            "-- A supplied list naming the same term twice validates to the\n"
            "-- duplicate error, which the spec must propagate; the rival reports\n"
            "-- the empty error. empty-vs-dup is a tag clash; `List.dedup` reduces\n"
            "-- on this two-element literal so the duplicate branch is reached.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := none, param := some [\"a\", \"a\"] }\n"
            "    (implementation_getFeatureNames { learned := none, param := some [\"a\", \"a\"] }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, List.dedup, Id.run, pure]\n"
        ),
    },
    {
        "id": "weak-supplied-list-no-materialisation",
        "kind": "uniqueness",
        "expect": "reject",
        # The direct counterpart of the nagini wrong-materialisation rival
        # (fake the fit, build no names): accept the supplied list as VALID —
        # so the validation outcome is routed correctly — and then return an
        # empty name list instead of the validated vocabulary's names.
        "module": _swap(
            _BASE, _I_IMPL,
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := Id.run do\n"
            "  let mut voc : List (String × Nat) := []\n"
            "  match st.learned with\n"
            "  | some v => voc := v\n"
            "  | none =>\n"
            "    match st.param with\n"
            "    | none => return Except.error VErr.notFitted\n"
            "    | some p =>\n"
            "      match validateList p with\n"
            "      | Except.error e => return Except.error e\n"
            "      | Except.ok _ => return Except.ok []\n"
            "  if voc.isEmpty then return Except.error VErr.empty\n"
            "  return Except.ok (featureNames voc)",
        ),
        "refinement": (
            "This is the wrong-materialisation defect: the supplied list is "
            "accepted as valid, and the object is reported as usable, but the "
            "vocabulary is never actually built from it — the query returns no "
            "names. The faithful real analogue marks a custom-vocabulary object "
            "usable while leaving its mapping empty, so the graded assertion that "
            "a custom-vocabulary object's feature names equal the supplied terms "
            "in order sees an empty list and FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from the SUCCESS arm of the SUPPLIED-LIST leg (`¬ v.isEmpty → "
            "result = Except.ok (featureNames v)`) — the arm the fix exists to "
            "add, and which the other supplied-list rivals only reach through "
            "their error arms or by skipping the leg wholesale. This rival routes "
            "the whole case analysis correctly and fails only in what it BUILDS, "
            "which is the nagini wrong-materialisation class the port dropped as "
            "\"covered\": no other case here returns an `ok` of the wrong length "
            "on this arm. Refuted at (no available vocabulary, supplied "
            "singleton) where the spec demands the ok names and the rival yields "
            "`ok []`. Measured: rival module exit 1, witness exit 0 on the rival, "
            "exit 1 on the frozen solution with the semantic goal `False`."),
        "witness": (
            "-- The supplied singleton validates, so the spec demands its ok\n"
            "-- index-ordered names; the rival accepts the list and returns ok [].\n"
            "-- Both sides are `ok`, so this is a list-value disagreement, not a\n"
            "-- tag clash: `pure`/`Id.instMonad` strip the `Id` wrapper.\n"
            "example : ¬ problem_spec_getFeatureNames\n"
            "    { learned := none, param := some [\"a\"] }\n"
            "    (implementation_getFeatureNames { learned := none, param := some [\"a\"] }) := by\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, featureNames, Id.run, pure, Id.instMonad]\n"
        ),
    },

    # =====================================================================
    # DIVERGENCE lane. This bundle sets no `loom.semantics.termination`: it is a
    # plain Mathlib carrier, so every `def` must show termination and the ONLY
    # way to write a non-terminating rival is `partial def`. Measured: the same
    # recursion WITHOUT `partial` is refused outright (`fail to show termination
    # for spin`), so the carrier does discharge a termination obligation and a
    # diverging rival is genuinely rejected rather than vacuously admitted.
    #
    # The witness cannot evaluate a `partial def` — its body is opaque, and no
    # tactic reduces `spin 0`. It does not need to. A non-terminating impl takes
    # no information from its input, so it returns ONE value at EVERY state,
    # while the spec forces two DIFFERENT values at two states. The refutation is
    # therefore stated over the CONJUNCTION of the obligation at two inputs and
    # closed by transitivity, with the diverging term never unfolded.
    #
    # Measured on both subjects, including the type-revealing probe that
    # distinguishes a real refutation from a stuck reduction (`exact (h1 : Nat)`
    # in place of the final step): against the RIVAL, `h1` has type
    # `spin 0 = Except.error VErr.notFitted` — simp could NOT prove the equation,
    # so the two states really do force one term to equal two things; against the
    # FROZEN solution, the same `h1` has type `True` — simp PROVED the equation,
    # so no contradiction is available and the witness correctly fails. Rival
    # exit 0, gold exit 1.
    # =====================================================================
    {
        "id": "diverge-input-independent-nontermination",
        "kind": "uniqueness",
        "expect": "reject",
        # A `partial def` that recurses forever, returning nothing for any state.
        # `partial` is what makes it elaborate at all; the value it "returns" is
        # opaque, and crucially it is the SAME opaque value for every input.
        "module": _swap(
            _BASE, _I_IMPL,
            "partial def spin (n : Nat) : Except VErr (List String) := spin (n + 1)\n"
            "\n"
            "def implementation_getFeatureNames\n"
            "    (st : VecState) : Except VErr (List String) := spin 0",
        ),
        "refinement": (
            "The faithful real analogue never returns from the query at all — the "
            "vocabulary-establishment step recurses without making progress, so "
            "every call hangs. The graded suite calls the query on several objects "
            "and asserts concrete results (the custom-vocabulary list, the "
            "learned names, the documented failures); a call that never returns "
            "produces none of them, so it does NOT resolve."),
        "rationale": (
            "REJECT from the whole postcondition at once, on the one property no "
            "value-level rival can express: INPUT DEPENDENCE. A non-terminating "
            "implementation returns the same opaque term for every state, while "
            "the spec demands the not-fitted error at (no available vocabulary, no "
            "list) and the ok index-ordered names at (no available vocabulary, "
            "supplied singleton). Those cannot both hold of one term, so the "
            "conjunction of the obligation at those two inputs is refutable "
            "WITHOUT evaluating the diverging body — which is what makes an opaque "
            "carrier attackable. This also confirms the carrier discharges a "
            "termination obligation: the same recursion without `partial` is "
            "refused with `fail to show termination`, so divergence is a real "
            "reject lane here and not a vacuous class. Measured: rival module exit "
            "1, witness exit 0 on the rival, exit 1 on the frozen solution; the "
            "type-revealing probe prints `h1 : spin 0 = Except.error "
            "VErr.notFitted` against the rival versus `h1 : True` against gold, "
            "i.e. simp proved the equation for gold and could not for the rival."),
        "witness": (
            "-- A NON-TERMINATING impl ignores its input, so it returns ONE value at\n"
            "-- every state. The spec forces two DIFFERENT values at two states (the\n"
            "-- not-fitted error when nothing is available, the ok names when a list\n"
            "-- is supplied), so one term would have to equal both. Refuted by\n"
            "-- transitivity; the diverging term `spin 0` is never unfolded, which is\n"
            "-- why an opaque body is still attackable.\n"
            "example : ¬ (problem_spec_getFeatureNames\n"
            "      { learned := none, param := none }\n"
            "      (implementation_getFeatureNames { learned := none, param := none })\n"
            "    ∧ problem_spec_getFeatureNames\n"
            "      { learned := none, param := some [\"a\"] }\n"
            "      (implementation_getFeatureNames { learned := none, param := some [\"a\"] })) := by\n"
            "  rintro ⟨h1, h2⟩\n"
            "  simp [problem_spec_getFeatureNames, implementation_getFeatureNames,\n"
            "    validateList, featureNames] at h1 h2\n"
            "  rw [h1] at h2\n"
            "  simp at h2\n"
        ),
    },
]
