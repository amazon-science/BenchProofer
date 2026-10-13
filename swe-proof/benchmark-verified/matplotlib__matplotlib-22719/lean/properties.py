"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-22719 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so ``markers.same_spec``
holds and every ``theorem correct_<name>`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with every
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

This battery is a PORT of the nagini sibling (``../nagini/properties.py``); it
carries over that battery's adversarial ARGUMENT and re-expresses it against this
backend's carrier. It is not a translation of the nagini text.

DEFENDED SURFACE (two total decision functions over list carriers)
------------------------------------------------------------------
Two independent, structurally identical decisions govern whether a side
notification fires when a sequence is handed to a categorical (string) unit
converter. Each is a boolean flag computed by scanning every element of the
incoming sequence for a per-element property:

  numericPassthrough (values : List Element) : Bool
  parsableInfo       (data   : List String)  : Bool

The load-bearing postcondition of each is the SAME shape:

  result = (!seq.isEmpty && seq.all <perElementPredicate>)

i.e. the notification fires exactly when the sequence is non-empty AND its
per-element conjunction holds. Two independent factors sit inside the single
conjunction:

  (NE)   the non-empty guard ``!seq.isEmpty``     — the bug the gold change fixes
  (ALL)  the per-element conjunction ``seq.all p`` — the pre-existing classifier

WHAT DRIVES THE REJECTS. A per-element "all" check over an EMPTY sequence is
VACUOUSLY true, so ``seq.all p`` alone is ``true`` when there is nothing to
convert; the flag then fires spuriously. The defect the gold change repairs is
exactly the omission of the ``(NE)`` factor. The F2P regression drives the
converter with an empty sequence and asserts that NO notification fires; a
decision missing ``(NE)`` fires on empty input and turns the spurious notice into
a downstream failure. Every empty-input reject here is that pre-patch shape.
``(ALL)`` is the pre-existing correctness of the classifier; a decision missing
``(ALL)`` fires on a non-empty non-classifying sequence, where the notice must
NOT fire. Attacking both factors independently is what pins the single
conjunction as a conjunction rather than either factor alone.

BINDER / CLAUSE COVERAGE. Each spec has one input binder (``values`` / ``data``).
The rejects vary it across the empty sequence AND a non-empty non-classifying
sequence, on BOTH sites, and attack each factor of the conjunction separately:

  * ``drop-ne-f1`` / ``drop-ne-f2`` — return the per-element conjunction alone
    (the exact pre-patch shape): fires on the empty sequence where the spec
    demands ``false``. Attacks ``(NE)``. This is the gold-repaired defect.
  * ``drop-all-f1`` / ``drop-all-f2`` — return the non-empty guard alone: fires
    on a non-empty non-classifying sequence where the spec demands ``false``.
    Attacks ``(ALL)``.
  * ``const-true-f1`` — ignore the input entirely: fires on the empty sequence,
    violating both factors. A supporting cheapest-wrong rival.
  * ``never-fire-f1`` / ``never-fire-f2`` — return ``false`` always: the
    POSITIVE direction, on both sites. Fails to fire on a non-empty classifying
    sequence, where the spec demands ``true``.
  * ``any-not-all-f1`` — replace the conjunction by a disjunction: fires on a
    MIXED sequence, pinning the quantifier's shape.

DIRECTIONALITY. The rejects above split into two groups, and both are needed.
The five OVER-firing rivals are refuted at points where the spec demands
``false``; the two ``never-fire-*`` rivals are refuted at points where it demands
``true``. A battery containing only the first group leaves the spec unconstrained
against a decision that simply never notifies — which passes the empty-input
regression while destroying the notification the change preserves. ``any-not-all``
covers a third axis: every 0- and 1-element witness leaves ``all``, ``any`` and
``head`` indistinguishable, so the quantifier is pinned only at a mixed sequence
of length 2.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
loop's exact elaboration — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Site 1's per-element predicate
(``isNumeric``) is fully TRANSPARENT, so its witnesses state the refutation at a
literal input and close by ``decide`` (no hypothesis, so no consistency
obligation). Site 2's predicate (``looksNumeric``) is an OPAQUE callee: the
empty-input witness is still literal (the ``all`` over ``[]`` reduces without the
callee), but the value-level witnesses must CONDITION on the carrier — each
assumes a single fact about the callee at one string (``looksNumeric "a" = false``
for the ``(ALL)`` rival, ``looksNumeric "1" = true`` for the under-firing one),
which is exactly the sub-domain where the corresponding rival is wrong. One
hypothesis about one opaque term, jointly satisfiable, so the gate's consistency
probe cannot derive ``False`` from it. Each witness was checked with two real
builds to ELABORATE against its rival and to FAIL on the frozen solution — and in
each frozen-side build the failure is a SEMANTIC refutation (``decide`` proved the
proposition false), never a stuck reduction, an unknown identifier or a timeout.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
  * nagini ``admiss-gold-baseline`` (the frozen impl verifies, so the read-only
    half-permission precondition is satisfiable) ↦ ``admiss-ground-f1`` here.
    The frozen ``correct_*`` obligation carries NO precondition hypothesis (the
    modeled behavior is total), so there is no permission precondition to admit;
    the honest analogue discharges the spec predicate at the ground F2P input
    (the empty sequence) by evaluation, inside the proof region, alongside the
    frozen obligation. If that could not be discharged the modeled behavior would
    be unsatisfiable at exactly the input the F2P exercises.
  * nagini ``pos-reorder-f1`` / ``pos-reorder-f2`` (branch-as-conjunction
    reshapes that stay correct) ↦ ``pos-commute-f1`` / ``pos-foldr-f2``:
    structurally different but correct impls that each RE-PROVE the obligation.
    Cross-site soundness controls, one per obligation. (The port originally
    mapped these to a pair of ``let``-bound-guard reshapes; an audit measured
    those to be definitionally equal to the frozen impl — a bare ``rfl`` proves
    the two bodies equal — so they could not detect an over-fit spec and were
    replaced. See the AUDIT NOTE on the positive controls.)
  * nagini ``partial-empty-f1`` / ``partial-empty-f2`` (the empty-input
    divergence, both sites) ↦ ``drop-ne-f1`` / ``drop-ne-f2``.
  * nagini ``weak-len-only-f1`` (drop the classifier conjunct) ↦ ``drop-all-f1``,
    plus ``drop-all-f2`` added for cross-site coverage of the ``(ALL)`` factor on
    the second obligation (nagini attacked it only on site 1).
  * nagini ``weak-const-true-f1`` (constant true) ↦ ``const-true-f1``.
  * ``never-fire-f1`` / ``never-fire-f2`` / ``any-not-all-f1`` have NO nagini
    counterpart: the sibling battery had no under-firing rival and no rival at a
    sequence longer than one element either, so both gaps are inherited from the
    design document rather than introduced by the port. Added here because this
    carrier expresses them directly (see DIRECTIONALITY above).
  * FRAME / PERMISSION MUTATION (nagini ``frame-mutation-f1``, MANDATORY there —
    a rival that WRITES to the read-only input to produce its answer, rejected by
    insufficient half-permission) — VACUOUS here. Lean is referentially
    transparent: the input carries no heap permission, there is no read-only
    half-permission to overwrite and no aliasing, so the write-to-input rival has
    no counterpart and no substitute is fabricated. The frame OBLIGATION that
    survives on this carrier is the emptiness factor ``(NE)``, which is attacked
    directly by the ``drop-ne`` rivals.

AXIOM lane: the nagini ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's job
and this gate ignores it. (The bundle's one ``opaque`` callee, the per-string
parsability predicate of site 2, is exercised here only as the transparent
conditioning fact inside the ``drop-all-f2`` witness, never as an answer-key
oracle: both specs are grounded in the input via ``isEmpty`` / ``all``, so there
is nothing to echo.)
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22719"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----

# The two final returns (each lies entirely inside an impl region; the accumulator
# name — `isNumlike` vs `convertible` — makes each unique in the file).
_F1_RET = "  return (!values.isEmpty && isNumlike)"
_F2_RET = "  return (!data.isEmpty && convertible)"

# The `intro` that opens each proof body (unique per obligation by its binder).
_F1_INTRO = "  intro values\n"

# The site-2 impl body in full, for the reshape that replaces the scanning loop
# outright (a `let`-bound guard is definitionally equal to the frozen body — see
# the AUDIT NOTE on the positive controls — so a positive control has to change
# the RECURSION, not the spelling of the return).
_F2_IMPL = """def implementation_parsableInfo (data : List String) : Bool := Id.run do
  let mut convertible := true
  for val in data do
    if !looksNumeric val then
      convertible := false
  return (!data.isEmpty && convertible)"""

# The two frozen proof bodies (each unique by its binder / predicate). A reshape
# that changes the impl's recursion must RE-PROVE, so it swaps these out.
_F1_PROOF = """  intro values
  unfold problem_spec_numericPassthrough implementation_numericPassthrough
  simp only [Id.run, bind]
  rw [flag_loop isNumeric values true]
  rfl"""

_F2_PROOF = """  intro data
  unfold problem_spec_parsableInfo implementation_parsableInfo
  simp only [Id.run, bind]
  rw [flag_loop looksNumeric data true]
  rfl"""


# ---- witness helpers --------------------------------------------------------
# A reject witness states the spec predicate directly at a concrete input and
# refutes it. Where the per-element predicate is transparent the input is
# literal; where it is the opaque site-2 callee, the witness conditions on one
# fact about it (see `_wit_f2_all`).

def _wit_f1_empty():
    # numericPassthrough on []: spec demands false; a rival that returns the
    # vacuously-true conjunction (or a constant true) returns true.
    return (
        "example : ¬ problem_spec_numericPassthrough []\n"
        "    (implementation_numericPassthrough []) := by\n"
        "  unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


def _wit_f1_all():
    # numericPassthrough on [categorical]: non-empty but the conjunction is
    # false, so spec demands false; a rival returning the non-empty guard alone
    # returns true. Fully transparent (isNumeric categorical = false).
    return (
        "example : ¬ problem_spec_numericPassthrough [Element.categorical]\n"
        "    (implementation_numericPassthrough [Element.categorical]) := by\n"
        "  unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


def _wit_f2_empty():
    # parsableInfo on []: same empty-input divergence, site 2. The `all` over []
    # reduces without the opaque callee, so no hypothesis is needed.
    return (
        "example : ¬ problem_spec_parsableInfo []\n"
        "    (implementation_parsableInfo []) := by\n"
        "  unfold problem_spec_parsableInfo implementation_parsableInfo\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


def _wit_f2_all():
    # parsableInfo on ["a"]: non-empty; CONDITION on the opaque callee being
    # false at "a" (the sub-domain where dropping the (ALL) factor is wrong), so
    # the spec demands false while a rival returning the non-empty guard alone
    # returns true. One hypothesis about one opaque term (jointly satisfiable).
    #
    # The scanning loop must be UNROLLED for this to discriminate. The opaque
    # callee occurs in the frozen impl only under the loop's lambda
    # (`fun val r => if !looksNumeric val ...`), where the hypothesis cannot
    # rewrite it; rewriting only the spec side then leaves an irreducible atom on
    # the impl side and `decide` gets STUCK — the same non-verdict for a true
    # claim as for a false one, which discriminates nothing. Adding the `forIn`
    # unrolling lemmas applies the loop to the literal `"a"`, so `h` fires on BOTH
    # sides and the frozen build fails by a decided `decide proved that the
    # proposition is false`. The two lemmas are reported unused against THIS rival
    # (it drops the loop) but are load-bearing for the frozen-side half, hence the
    # linter suppression.
    #
    # AUDIT NOTE, measured. The counterfactual was built to check that claim: the
    # same witness with the unrolling lemmas REMOVED (`simp only [Id.run, bind,
    # pure, h]; decide`) fails on BOTH subjects with `decide failed ... its
    # `Decidable` instance instDecidableNot did not reduce to `isTrue` or
    # `isFalse``, i.e. stuck reduction on the rival too, which the gate would
    # record as `witness-unproven` rather than as a refutation. So the unrolling
    # is genuinely load-bearing, but the port's stated reason was imprecise: the
    # stuck reduction is not specific to the frozen side (the rival's own
    # `["a"].all looksNumeric` on the SPEC side is equally irreducible). What the
    # lemmas buy is a decidable goal on both sides at once.
    return (
        "set_option linter.unusedSimpArgs false in\n"
        'example (h : looksNumeric "a" = false) : ¬ problem_spec_parsableInfo ["a"]\n'
        '    (implementation_parsableInfo ["a"]) := by\n'
        "  unfold problem_spec_parsableInfo implementation_parsableInfo\n"
        "  simp only [Id.run, bind, pure, List.forIn_cons, List.forIn_nil,\n"
        "    List.all_cons, List.all_nil, List.isEmpty_cons, h]\n"
        "  decide\n"
    )


def _wit_f1_true():
    # numericPassthrough on [numeric]: non-empty AND the conjunction holds, so
    # the spec demands TRUE. Refutes any rival that under-fires here (a constant
    # false, or a guard strengthened past `!isEmpty`). The other site-1 witnesses
    # all pin points where the spec demands FALSE, so without this one no case
    # constrains the spec's positive direction and a never-notify rival would be
    # indistinguishable from the fix. Fully transparent; closes by `decide`.
    return (
        "example : ¬ problem_spec_numericPassthrough [Element.numeric]\n"
        "    (implementation_numericPassthrough [Element.numeric]) := by\n"
        "  unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


def _wit_f1_mixed():
    # numericPassthrough on [numeric, categorical]: a MIXED sequence. The spec
    # demands false (the conjunction fails at the second element) while an
    # `any`-shaped rival returns true. Distinguishes the per-element conjunction
    # from a disjunction / first-element test — a distinction every single-element
    # and empty witness leaves free. Fully transparent; closes by `decide`.
    return (
        "example : ¬ problem_spec_numericPassthrough [Element.numeric, Element.categorical]\n"
        "    (implementation_numericPassthrough [Element.numeric, Element.categorical]) := by\n"
        "  unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
        "  simp only [Id.run, bind, pure]\n"
        "  decide\n"
    )


def _wit_f2_true():
    # parsableInfo on ["1"]: the positive direction at the OPAQUE site. Conditions
    # on the callee holding at "1" (the sub-domain where the notice must fire), so
    # the spec demands true and an under-firing rival returns false. Unrolls the
    # loop for the same reason `_wit_f2_all` does; the two lemmas are reported
    # unused against this rival but are load-bearing on the frozen side.
    return (
        "set_option linter.unusedSimpArgs false in\n"
        'example (h : looksNumeric "1" = true) : ¬ problem_spec_parsableInfo ["1"]\n'
        '    (implementation_parsableInfo ["1"]) := by\n'
        "  unfold problem_spec_parsableInfo implementation_parsableInfo\n"
        "  simp only [Id.run, bind, pure, List.forIn_cons, List.forIn_nil,\n"
        "    List.all_cons, List.all_nil, List.isEmpty_cons, h]\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at the normal
    # F2P-shaped input. The frozen theorem carries no precondition hypothesis (the
    # modeled behavior is total), so the nagini precondition-admission probe has
    # no binder to attack; the honest analogue discharges the spec predicate at
    # the ground input the F2P exercises (the empty sequence) by evaluation,
    # inside the proof region, then closes the frozen obligation verbatim. If that
    # ground instance could not be discharged, the modeled behavior would be
    # unsatisfiable at exactly the empty input the fix concerns (the analogue of
    # PRECOND-TOO-STRONG). Nothing is assumed: the theorem statement is
    # byte-identical and the ground instance is a `have` inside the tactic body.
    # =====================================================================
    {
        "id": "admiss-ground-f1",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _F1_INTRO,
            "  have _ground : problem_spec_numericPassthrough []\n"
            "      (implementation_numericPassthrough []) := by\n"
            "    unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
            "    simp only [Id.run, bind, pure]\n"
            "    decide\n"
            "  intro values\n",
        ),
        "rationale": "the decision obligation is discharged at the ground empty "
                     "input (the shape the F2P exercises) by evaluation, then the "
                     "frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior is unsatisfiable at the normal input, the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: the "
                     "theorem statement is byte-identical and the ground instance "
                     "is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify (else the spec is over-fit => SPEC-TOO-STRONG). Each keeps
    # the `theorem correct_*` statement byte-identical and introduces no axiom,
    # `sorry` or new top-level theorem; each RE-PROVES inside the proof region,
    # because each genuinely changes the impl's recursion.
    #
    # AUDIT NOTE (why these replaced the port's `pos-letbind-*` pair). Those two
    # bound the non-empty guard to a `let` and returned `(ne && flag)`, and closed
    # under the frozen tactic body UNCHANGED. That is exactly the tell: a `let` is
    # definitionally transparent, so the reshaped body is DEFEQ to the frozen one.
    # Measured, not argued — appending
    #     example (values : List Element) : (Id.run do ... return (!values.isEmpty
    #       && isNumlike)) = (Id.run do ... let ne := !values.isEmpty
    #       return (ne && isNumlike)) := rfl
    # to the frozen file elaborates (exit 0) with a BARE `rfl`. A positive control
    # that is defeq to gold cannot detect an over-fit spec: it verifies for the
    # same reason gold does, whatever the spec says. The replacements below change
    # the recursion itself (a commuted conjunction whose `rfl` no longer closes; a
    # `foldr` in place of the `for`-loop accumulator), so each is a real test that
    # the spec admits a faithful impl it was not written against.
    # =====================================================================
    {
        "id": "pos-commute-f1",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _F1_RET, "  return (isNumlike && !values.isEmpty)"),
            _F1_PROOF,
            "  intro values\n"
            "  unfold problem_spec_numericPassthrough implementation_numericPassthrough\n"
            "  simp only [Id.run, bind]\n"
            "  rw [flag_loop isNumeric values true]\n"
            "  simp only [Bool.true_and, pure]\n"
            "  exact Bool.and_comm _ _",
        ),
        "rationale": "the conjunction is COMMUTED: the per-element flag is tested "
                     "before the non-empty guard. `&&` is commutative on Bool, so "
                     "this agrees with the frozen decision on every input and must "
                     "verify (else SPEC-TOO-STRONG). Unlike a `let`-bound guard this "
                     "is NOT definitionally equal — the frozen `rfl` no longer "
                     "closes it (measured: `unsolved goals ⊢ pure (all && !isEmpty) "
                     "= (all && !isEmpty)` ... modulo orientation), so the proof is "
                     "re-closed by `Bool.and_comm`. A real soundness probe: it "
                     "verifies only because the spec is an equation on the DECISION, "
                     "not on the frozen syntactic form.",
    },
    {
        "id": "pos-foldr-f2",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _F2_IMPL,
                "def implementation_parsableInfo (data : List String) : Bool :=\n"
                "  !data.isEmpty && data.foldr (fun s acc => looksNumeric s && acc) true",
            ),
            _F2_PROOF,
            "  intro data\n"
            "  unfold problem_spec_parsableInfo implementation_parsableInfo\n"
            "  have key : ∀ l : List String,\n"
            "      List.foldr (fun s acc => looksNumeric s && acc) true l "
            "= l.all looksNumeric := by\n"
            "    intro l\n"
            "    induction l with\n"
            "    | nil => rfl\n"
            "    | cons a as ih => simp [List.all_cons, ih]\n"
            "  rw [key]",
        ),
        "rationale": "cross-site soundness control that removes the scanning LOOP "
                     "entirely: a right fold of the opaque per-element callee "
                     "replaces the mutable accumulator. Same decision on every "
                     "input (a fold of `&&` over the list is its conjunction), so it "
                     "must verify. The frozen proof's `flag_loop` rewrite no longer "
                     "applies (there is no `forIn` left), so the obligation is "
                     "re-closed by an inline induction — the `have` is local to the "
                     "tactic body, so no new top-level theorem is introduced. This "
                     "is the strongest available soundness probe on this bundle: it "
                     "shows the spec admits an impl of a wholly different recursive "
                     "shape over the OPAQUE callee.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival is a true
    # verify-does-not-imply-resolve break, and (b) a refutation witness pinning
    # the violation at one concrete input.
    # =====================================================================

    # -- (NE) factor: the empty-input divergence (the gold-repaired defect) ----
    {
        "id": "drop-ne-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F1_RET, "  return isNumlike"),
        "refinement": "this is the PRE-patch decision — the per-element "
                      "conjunction WITHOUT the non-empty guard. On the empty "
                      "sequence the conjunction is vacuously true, so the "
                      "notification fires; the F2P regression drives the converter "
                      "with empty data and asserts no notification, so this rival "
                      "FAILS it — it would NOT resolve.",
        "rationale": "REJECT from the (NE) factor of the postcondition "
                     "(result = (!isEmpty && all p)): on values==[] the rival "
                     "returns the vacuously-true conjunction (true) while the spec "
                     "demands false. If it verified => SPEC-TOO-WEAK (admits the "
                     "empty-input defect).",
        "witness": _wit_f1_empty(),
    },
    {
        "id": "drop-ne-f2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F2_RET, "  return convertible"),
        "refinement": "PRE-patch decision at the second site — the per-element "
                      "conjunction without the non-empty guard. The conjunction is "
                      "vacuously true on empty data, so the informational notice "
                      "fires on an empty sequence; this is the behavior the fix "
                      "removes. Would NOT resolve the empty-data smoke test.",
        "rationale": "REJECT from the (NE) factor on the second obligation: on "
                     "data==[] the rival returns the vacuously-true conjunction "
                     "(true) while the spec demands false. Independent empty-input "
                     "witness for the second site.",
        "witness": _wit_f2_empty(),
    },

    # -- (ALL) factor: fires on a non-empty non-classifying sequence -----------
    {
        "id": "drop-all-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F1_RET, "  return !values.isEmpty"),
        "refinement": "a decision that fires whenever the sequence is non-empty, "
                      "ignoring the per-element classifier, emits the advisory for "
                      "genuine non-numeric categories where it must not; that "
                      "changes the converter's notification behavior on the "
                      "non-numeric conversion tests — would NOT resolve.",
        "rationale": "REJECT from the (ALL) factor (result = (!isEmpty && all p)): "
                     "on a non-empty sequence with a non-classifying element the "
                     "conjunction is false so the spec demands false, but the rival "
                     "returns the non-empty guard alone (true). If it verified => "
                     "SPEC-TOO-WEAK. Pins the (ALL) factor the (NE) rivals leave "
                     "fixed at true.",
        "witness": _wit_f1_all(),
    },
    {
        "id": "drop-all-f2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F2_RET, "  return !data.isEmpty"),
        "refinement": "same (ALL)-dropping shape at the second site: firing the "
                      "informational notice whenever data is non-empty, regardless "
                      "of whether the strings are parsable, emits it for strings "
                      "that are not all parsable — the notice's stated condition. "
                      "Would NOT resolve.",
        "rationale": "REJECT from the (ALL) factor on the second obligation: on a "
                     "non-empty sequence whose per-element predicate fails at some "
                     "element the spec demands false, but the rival returns true. "
                     "Cross-site coverage of the (ALL) factor (nagini attacked it "
                     "only on the first site). Refuted by CONDITIONING on the "
                     "opaque callee at one string (a single satisfiable fact).",
        "witness": _wit_f2_all(),
    },

    # -- POSITIVE DIRECTION: rivals that UNDER-fire ----------------------------
    # AUDIT ADDITION. Every rival the port shipped is wrong by firing where the
    # spec demands FALSE (empty input, or a non-classifying element), so all five
    # witnesses pinned points whose demanded value is `false`. Nothing constrained
    # the spec's positive direction: a decision that NEVER notifies satisfies
    # every one of those witnesses' concerns, and the battery would have recorded
    # SOUND for a spec that could not tell the fix from "delete the notification".
    # These close that direction on both sites.
    {
        "id": "never-fire-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F1_RET, "  return false"),
        "refinement": "a decision that never emits the advisory does satisfy the "
                      "empty-input regression, but it also suppresses the notice for "
                      "the genuine all-numeric sequence it is meant to announce — "
                      "the pre-existing behavior the change PRESERVES, exercised by "
                      "the numeric-passthrough conversion tests. Silently dropping a "
                      "notification the surrounding tests assert is emitted would "
                      "NOT resolve.",
        "rationale": "REJECT from the POSITIVE direction of the postcondition "
                     "(result = (!isEmpty && all p)): on values==[numeric] the "
                     "sequence is non-empty and the conjunction holds, so the spec "
                     "demands TRUE while this rival returns false. If it verified => "
                     "SPEC-TOO-WEAK in the direction no other rival probes (all the "
                     "others are wrong by OVER-firing).",
        "witness": _wit_f1_true(),
    },
    {
        "id": "never-fire-f2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F2_RET, "  return false"),
        "refinement": "same never-notify shape at the second site: the "
                      "informational notice is dropped even for a sequence of "
                      "genuinely parsable strings, which is precisely when it is "
                      "supposed to appear. Would NOT resolve.",
        "rationale": "REJECT from the positive direction on the second obligation: "
                     "conditioning on the opaque callee holding at one string, the "
                     "sequence is non-empty and the conjunction holds, so the spec "
                     "demands TRUE while the rival returns false. Cross-site cover "
                     "of the positive direction; one satisfiable hypothesis about "
                     "one opaque term.",
        "witness": _wit_f2_true(),
    },

    # -- the conjunction is over ALL elements, not just one --------------------
    {
        "id": "any-not-all-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _F1_RET, "  return (!values.isEmpty && values.any isNumeric)"),
        "refinement": "testing whether SOME element is a non-string numeric value, "
                      "rather than every one, emits the advisory for a mixed "
                      "sequence that still contains real categories — the values "
                      "that must go through categorical mapping rather than the "
                      "numeric path. That changes the conversion behavior on mixed "
                      "input; would NOT resolve.",
        "rationale": "REJECT: pins the per-element conjunction as a CONJUNCTION "
                     "rather than a disjunction or a first-element test. On "
                     "values==[numeric, categorical] the spec demands false (the "
                     "`all` fails at the second element) while this rival returns "
                     "true. Every other witness in this battery states its "
                     "refutation at a 0- or 1-element sequence, where `all`, `any` "
                     "and `head` all coincide — so this is the only case that "
                     "constrains the quantifier's shape.",
        "witness": _wit_f1_mixed(),
    },

    # -- supporting: constant true (violates both factors) ---------------------
    {
        "id": "const-true-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _F1_RET, "  return true"),
        "refinement": "unconditionally emitting the notification (even on empty "
                      "input and on non-classifying sequences) fails both the "
                      "empty-data F2P test and the non-numeric conversion tests; "
                      "would NOT resolve.",
        "rationale": "REJECT: violates the postcondition on values==[] (spec "
                     "demands false via the (NE) factor) as well as on any "
                     "non-classifying non-empty input. Cheapest-wrong supporting "
                     "rival; refuted at the empty input.",
        "witness": _wit_f1_empty(),
    },
]

# AXIOM_TESTS — none. The axiom lane is G-AX's job and this gate ignores it.
AXIOM_TESTS = []
