"""properties.py — G-PBT falsification battery for django__django-11999 (lean).

NOT a Lean file: a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a complete ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start`` /
``-- impl-end`` — and, for the one positive that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds by construction and the ``theorem correct_registerDisplay`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

This battery is a PORT of the nagini sibling's adversarial reasoning
(``../nagini/properties.py``), re-expressed against this backend's carrier. The
argument of each sibling case is carried over; none of its mechanics are, because
the two carriers differ (see the accounting block at the bottom of this file).

DEFENDED SURFACE (one modeled behavior, one obligation). A class' attribute
namespace is presented with a field name, a flag saying whether the field carries
an enumerated choice set, and the value of the generated display accessor. The
single spec predicate pins the WHOLE resulting namespace:

  problem_spec_registerDisplay
      (attrs : Attrs) (name : String) (hasChoices : Bool) (display : Int)
      (result : Attrs) : Prop
    let key := displayKey name
    result = (if hasChoices && !hasKey attrs key
              then attrs ++ [(key, display)] else attrs)

``Attrs = List (String × Int)``; ``displayKey``, ``hasKey`` and ``setKey`` are
TRANSPARENT pure helpers in the frozen spec view (no opaque callee anywhere in
this bundle), so every clause is ground and ``decide``-able at a literal input —
no witness here needs to condition on the carrier.

BINDER STRUCTURE (read this before judging binder / clause coverage). Four input
binders — ``attrs``, ``name``, ``hasChoices``, ``display`` — and the
postcondition decomposes into independent components that a rival can attack one
at a time:

  * GUARD conjunct A — ``hasChoices``: the accessor is registered ONLY when the
    field carries a choice set. Attacked by ``weak-flag-inverted``.
  * GUARD conjunct B — ``!hasKey attrs key``: the accessor is registered ONLY
    when the namespace does not already bind that name. THE discriminating
    clause of this instance (a namespace that already provides its own accessor
    must come back unchanged). Attacked by ``weak-overwrite-existing`` (ignores
    the conjunct outright) and by ``weak-guard-on-field-name`` (evaluates the
    presence test at the wrong name — a near-miss that agrees with the frozen
    behavior on every namespace where the two names' presence coincides, so it
    carries its own distinguishing input).
  * THEN-branch, the registered NAME ``key = displayKey name``. Attacked by
    ``weak-wrong-key``.
  * THEN-branch, the registered VALUE ``display``. Attacked by
    ``weak-wrong-value`` (binds a constant instead) and by
    ``weak-skip-zero-value`` (a near-miss that reads the ``display`` binder as
    part of the GUARD, skipping the registration when the supplied accessor
    value happens to be the carrier's zero — the one value the rest of the
    battery never supplies).
  * THEN-branch, the PRESERVED PREFIX ``attrs ++ …``: everything already in the
    namespace survives the registration, in place. Attacked by
    ``weak-discard-namespace`` (keeps only the new binding) and by
    ``weak-clobber-on-install`` (registers correctly but corrupts the other
    bindings' values while doing it).
  * THE REGISTRATION ITSELF (the then-branch fires at all). Attacked by
    ``weak-never-install``.
  * ELSE-branch, ``result = attrs`` — the no-write case is exactly unchanged.
    Attacked by ``weak-clobber-other``, which does the correct nothing to the
    accessor name and corrupts an unrelated binding instead; this isolates the
    else-branch (the guard components still hold of it).

Every one of the four binders is VARIED across the reject witnesses: ``attrs``
takes seven distinct literals covering six qualitative shapes (empty; one
unrelated binding; two unrelated bindings; the accessor name already bound; the
accessor name already bound alongside an unrelated one; the FIELD name bound but
not the accessor name), ``name`` takes FOUR values (``x``, ``f``, ``z``, ``w``),
``hasChoices`` takes BOTH values, and ``display`` takes SEVEN distinct values
(``0``, ``2``, ``3``, ``4``, ``5``, ``6``, ``9``) INCLUDING ``0`` (the carrier's
zero, which ``weak-skip-zero-value`` shows is not a value the guard may
special-case). No binder is held fixed across the battery, so a rival that
mishandled only one of them could not hide.

Counts here are re-derived from the witness texts, not asserted, and they have
been wrong before in BOTH directions — which is why they are recounted rather
than carried forward. One revision claimed ``name`` took FOUR values when the
witnesses used three; a later revision then claimed FIVE while the enumeration
beside it listed four, and the closing accounting block simultaneously said
``attrs`` in six and ``display`` in six. The figures above are the ones the ten
witness texts actually contain.

ADVERSARIAL READ of the sibling's remaining weakness classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The sibling holds its namespace at a
    full write permission and its frame rivals subvert a heap footprint. Lean is
    referentially transparent: ``attrs`` is an immutable value, there is no
    aliasing and no read-only input to write through. The class's REACHABLE
    analogue — value-level corruption of a binding the operation was not asked to
    touch — is not vacuous and IS ported, as ``weak-clobber-other`` (else-branch)
    and ``weak-clobber-on-install`` (then-branch); both are refuted by the
    whole-namespace pin rather than by any permission system.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend. The sibling carries
    no such case, and none could be written here: ``implementation_registerDisplay``
    is a total Lean ``def``, so a diverging implementation is not expressible at
    all. (This is the lean disposition specifically; on velvet under partial
    termination semantics the same class would be a KNOWN SPEC HOLE, see
    ``the corpus-wide termination-semantics finding``.)

  * UNGROUNDED-ORACLE ECHO — N/A. Nothing in the spec is an opaque answer key:
    the registered value is an INPUT (``display``) and the registered name is
    computed from an input by a transparent helper. There is no oracle to echo;
    the cheapest honest implementation is shipped as a positive control.

  * CONTROL-FLOW EFFECT — N/A. The modeled behavior is a pure namespace-to-
    namespace function with no failure path, so there is no effect the value
    abstraction cannot see.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is tuned to the frozen impl's
form), so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked by hand with two
real ``lake env lean`` builds: it ELABORATES against its rival and FAILS against
the frozen solution (gold's failure text is ``decide`` proving the NEGATION of
the witness's claim — i.e. the frozen behavior satisfies the spec there), so each
is a real discriminator and not a tautology. All witnesses are literal-input and
bind nothing, so none can be inconsistent.

LANES. All three directions this gate exists to test are populated: SOUNDNESS
(4 correct reshapes that must verify => SPEC-TOO-STRONG if not), UNIQUENESS
(10 wrong rivals that must be rejected => SPEC-TOO-WEAK if any verifies), and
ADMISSIBILITY (2 positives discharging the obligation by evaluation at an
F2P-shaped input, one per branch => the total-carrier analogue of
PRECOND-TOO-STRONG if either could not be discharged).

AXIOM lane: EMPTY. ``meta.json`` records no axioms; the namespace primitives are
modeled deeply in the frozen pure region, so there is no assumed callee contract
for this gate to falsify (the axiom lane belongs to G-AX regardless).
"""
from pathlib import Path

INSTANCE = "django__django-11999"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors -------------------------------------------------------
# `_IMPL` is the whole mutable body of `implementation_registerDisplay`; it lies
# ENTIRELY inside `-- impl-start` / `-- impl-end` and is unique in the file
# (asserted by `_swap` at import, so any drift in Solution.lean breaks loudly).
_IMPL = (
    "  let mut result := attrs\n"
    "  if hasChoices then\n"
    "    let key := displayKey name\n"
    "    if !hasKey result key then\n"
    "      result := setKey result key display\n"
    "  return result"
)

# The frozen tactic body, wholly inside `-- proof-start` / `-- proof-end`. Only
# the one positive that legitimately re-proves touches it; every reject case
# leaves it frozen (a rival is judged by its witness, never by whether this
# script happens to break).
_PROOF = (
    "  intro attrs name hasChoices display\n"
    "  unfold problem_spec_registerDisplay implementation_registerDisplay hasKey setKey\n"
    "  simp only [Id.run]\n"
    "  by_cases hc : hasChoices = true <;>\n"
    "    by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>\n"
    "    simp only [hc, hk, Bool.not_true, Bool.not_false,\n"
    "      Bool.and_true, Bool.and_false, if_true] <;>\n"
    "    rfl"
)


def _impl(new_body: str, new_proof: str | None = None) -> str:
    """Solution.lean with ONLY the impl body (and optionally the tactic body)
    replaced. The spec view and the theorem STATEMENT are untouched."""
    src = _swap(_BASE, _IMPL, new_body)
    if new_proof is not None:
        src = _swap(src, _PROOF, new_proof)
    return src


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each was
    # confirmed to elaborate with the obligation closed by a real build.
    # =====================================================================
    {
        "id": "pos-merged-guard",
        "kind": "soundness",
        "expect": "verify",
        # The two nested tests collapsed into one conjunctive test, which is the
        # spec's own guard spelling. Same decision on every input, so the
        # whole-namespace pin holds; the frozen tactic body still closes it.
        "module": _impl(
            "  let mut result := attrs\n"
            "  let key := displayKey name\n"
            "  if hasChoices && !hasKey result key then\n"
            "    result := setKey result key display\n"
            "  return result"),
        "rationale": "structurally different CORRECT reshape: the two nested "
                     "conditions merged into a single conjunctive test, with the "
                     "accessor name computed unconditionally instead of inside the "
                     "branch. The registration fires on exactly the same inputs and "
                     "writes exactly the same binding, so `result = (if hasChoices && "
                     "!hasKey attrs key then attrs ++ [(key, display)] else attrs)` "
                     "holds on all four binders. A faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG (over-fit to the nested spelling). Proof body "
                     "byte-identical (the decision is definitionally the same); no new "
                     "axiom/lemma, no assumption token.",
    },
    {
        "id": "pos-swapped-nesting",
        "kind": "soundness",
        "expect": "verify",
        # The two guard conjuncts tested in the OPPOSITE nesting order. `&&` is
        # commutative on the decision, so the same inputs register.
        "module": _impl(
            "  let mut result := attrs\n"
            "  let key := displayKey name\n"
            "  if !hasKey result key then\n"
            "    if hasChoices then\n"
            "      result := setKey result key display\n"
            "  return result"),
        "rationale": "structurally different CORRECT reshape: the guard's two "
                     "conjuncts are tested in the opposite nesting order (presence "
                     "first, choice-set flag second). The set of inputs on which the "
                     "registration fires is unchanged, so the postcondition holds "
                     "identically; if this fails to verify the spec is over-fit to the "
                     "order in which the conditions are written => SPEC-TOO-STRONG. "
                     "Proof body byte-identical; no new axiom/lemma.",
    },
    {
        "id": "pos-direct-append",
        "kind": "soundness",
        "expect": "verify",
        # Different DATA-flow shape: on the branch where the name is provably not
        # yet bound, the general replace-or-append assignment is specialized to a
        # direct append. The proof drops exactly one name from the `unfold` list
        # (the assignment helper is no longer used); the STATEMENT is unchanged
        # and nothing is assumed.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := result ++ [(key, display)]\n"
            "  return result",
            "  intro attrs name hasChoices display\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay hasKey\n"
            "  simp only [Id.run]\n"
            "  by_cases hc : hasChoices = true <;>\n"
            "    by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>\n"
            "    simp only [hc, hk, Bool.not_true, Bool.not_false,\n"
            "      Bool.and_true, Bool.and_false, if_true] <;>\n"
            "    rfl"),
        "rationale": "CORRECT reshape of the DATA flow, not just the control flow: on "
                     "the branch the guard selects, the name is provably not yet bound, "
                     "so the general replace-or-append assignment is equivalent to a "
                     "direct append — which is literally the shape the postcondition "
                     "states. It must verify, else SPEC-TOO-STRONG (over-fit to the "
                     "general assignment helper). Proof retuned ONLY by removing the "
                     "now-unused helper from the `unfold` list; theorem statement "
                     "byte-identical, no new axiom/lemma/assumption token.",
    },

    {
        "id": "pos-find-presence-test",
        "kind": "soundness",
        "expect": "verify",
        # The presence test itself reshaped: a DIFFERENT decision procedure
        # (`find?`/`isNone`) in place of the spec's `List.any`, so the guard is no
        # longer definitionally the spec's guard — it has to be PROVEN equal to
        # it. The three other positives all keep a guard that reduces to the
        # frozen one by `rfl`; this is the first one whose proof needs a real
        # induction, which is what makes it a sharper over-strength probe.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if (result.find? (fun p => p.1 == key)).isNone then\n"
            "      result := result ++ [(key, display)]\n"
            "  return result",
            "  intro attrs name hasChoices display\n"
            "  have hfa : (attrs.find? (fun p => p.1 == displayKey name)).isNone\n"
            "      = !(attrs.any (fun p => p.1 == displayKey name)) := by\n"
            "    induction attrs with\n"
            "    | nil => rfl\n"
            "    | cons a t ih =>\n"
            "      by_cases h : (a.1 == displayKey name) = true <;>\n"
            "        simp [List.find?, List.any, h, ih]\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay hasKey\n"
            "  simp only [Id.run, hfa]\n"
            "  by_cases hc : hasChoices = true <;>\n"
            "    by_cases hk : (List.any attrs fun p => p.1 == displayKey name) = true <;>\n"
            "    simp only [hc, hk, Bool.not_true, Bool.not_false,\n"
            "      Bool.and_true, Bool.and_false, if_true, if_false] <;>\n"
            "    rfl"),
        "rationale": "CORRECT reshape of the DECISION PROCEDURE, not just the control or "
                     "data flow: the namespace is searched with `find?`/`isNone` instead "
                     "of the spec's `List.any`, and the two are proven equal by "
                     "induction on the namespace rather than by reduction. This is the "
                     "sharpest over-strength probe in the battery — the other positives "
                     "all keep a guard that is definitionally the frozen one, so a spec "
                     "over-fit to `List.any` specifically would pass all three and fail "
                     "only here. It must verify, else SPEC-TOO-STRONG. Statement "
                     "byte-identical; the proof adds a local `have` (no new top-level "
                     "axiom/lemma, no assumption token).",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE (non-vacuous) at a normal,
    # F2P-shaped input. The frozen obligation carries NO precondition, so the
    # sibling's precondition-admission self-call re-expresses on this total
    # carrier as: discharge the spec predicate BY EVALUATION at a concrete
    # F2P-shaped input as a `have`, then close the frozen obligation verbatim.
    # This is what detects the analogue of PRECOND-TOO-STRONG here — an
    # obligation that is unsatisfiable at exactly the input the instance is
    # about. One case per BRANCH, since the two branches are what the sibling
    # split into two preconditioned functions.
    #
    # Each was confirmed non-vacuous by a real build PAIR: the case verifies
    # (exit 0) and the same `have` with the claim NEGATED fails (exit 1,
    # "`decide` proved that the proposition ... is false"), so the `have` really
    # evaluates the predicate rather than being closed by something that would
    # close anything.
    # =====================================================================
    {
        "id": "admiss-preserve-existing-accessor",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-SHAPED point: the namespace already binds the accessor name
        # (the class declares its own) AND carries the field's own attribute.
        # The obligation must be satisfiable HERE, i.e. the spec's else-branch
        # (`result = attrs`) must be dischargeable at a real input.
        "module": _impl(
            _IMPL,
            "  intro attrs name hasChoices display\n"
            "  have _ground : problem_spec_registerDisplay\n"
            "      [(\"get_status_display\", (1 : Int)), (\"status\", (2 : Int))] \"status\" true 3\n"
            "      (implementation_registerDisplay\n"
            "        [(\"get_status_display\", (1 : Int)), (\"status\", (2 : Int))] \"status\" true 3) := by\n"
            "    unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "    simp only [Id.run]\n"
            "    decide\n" + _PROOF.split("\n", 1)[1]),
        "rationale": "ADMISSIBILITY on the branch the failing scenario is about: the "
                     "obligation is discharged BY EVALUATION at a concrete F2P-shaped "
                     "input — a namespace that already binds the generated accessor "
                     "name alongside the field's own attribute, with the choice-set flag "
                     "set — prepended as a `have`, before the frozen obligation is "
                     "closed verbatim. If the spec predicate were unsatisfiable at "
                     "exactly this normal input the `have` could not be discharged, "
                     "which is this total carrier's analogue of PRECOND-TOO-STRONG (the "
                     "frozen obligation has no precondition to admit, so the reachable "
                     "form of that finding is an obligation vacuous at an F2P-shaped "
                     "point). Ports nagini's admiss-preserve-override-present. Nothing "
                     "is assumed: statement byte-identical, no new declaration, the "
                     "ground instance is a `have` inside the existing tactic body. "
                     "Non-vacuity machine-checked: the same `have` with the claim "
                     "NEGATED fails to build.",
    },
    {
        "id": "admiss-install-missing-accessor",
        "kind": "admissibility",
        "expect": "verify",
        # The other branch: an ordinary choice-carrying field whose class does
        # NOT already bind the accessor name, so the registration must fire.
        # This is the shape the choice-and-display P2P tests exercise.
        "module": _impl(
            _IMPL,
            "  intro attrs name hasChoices display\n"
            "  have _ground : problem_spec_registerDisplay\n"
            "      [(\"status\", (2 : Int))] \"status\" true 3\n"
            "      (implementation_registerDisplay\n"
            "        [(\"status\", (2 : Int))] \"status\" true 3) := by\n"
            "    unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "    simp only [Id.run]\n"
            "    decide\n" + _PROOF.split("\n", 1)[1]),
        "rationale": "ADMISSIBILITY on the OTHER branch, so neither branch of the one "
                     "obligation is left unshown satisfiable: an ordinary "
                     "choice-carrying field whose class does not already bind the "
                     "generated accessor name, which is the shape the choice-and-display "
                     "P2P tests exercise. The spec's then-branch (`attrs ++ [(key, "
                     "display)]`) is discharged by evaluation as a `have`, then the "
                     "frozen obligation is closed verbatim. Ports nagini's "
                     "admiss-install-fresh. Statement byte-identical, no new "
                     "declaration. Non-vacuity machine-checked the same way: the "
                     "negated `have` fails to build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries a machine-checked
    # refutation witness at a concrete input (seen to elaborate against the
    # rival and to FAIL on the frozen solution) plus the refinement argument
    # for why its faithful real counterpart would NOT resolve.
    # =====================================================================
    {
        "id": "weak-overwrite-existing",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks GUARD conjunct B: registers the generated accessor whenever the
        # field carries a choice set, without first asking whether the namespace
        # already binds that name.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    result := setKey result key display\n"
            "  return result"),
        "refinement": "a faithful real counterpart registers the generated display "
                      "accessor onto every choice-carrying field's class without "
                      "consulting what the class already provides, so a class that "
                      "declares its OWN accessor for that field has it replaced by the "
                      "generated one. That is exactly the behavior the failing test "
                      "pins: it declares its own accessor and asserts the declared one "
                      "answers. The rival answers with the generated label instead, so "
                      "the F2P assertion fails and it would NOT resolve.",
        "rationale": "REJECT from GUARD conjunct B (`!hasKey attrs key`): with the "
                     "conjunct dropped the rival's result is `setKey attrs key display` "
                     "even when `hasKey attrs key`, while the spec's else-branch pins "
                     "`result = attrs`. Refuted at a namespace that ALREADY binds the "
                     "accessor name to a different value — the discriminating clause of "
                     "this instance. Binders: `attrs` at the accessor-already-bound "
                     "point, `name = \"x\"`, `hasChoices = true`, `display = 2`. If it "
                     "verified => SPEC-TOO-WEAK (the preservation guarantee is hollow).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"get_x_display\", (1 : Int))] \"x\" true 2\n"
            "    (implementation_registerDisplay [(\"get_x_display\", (1 : Int))] \"x\" true 2) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-guard-on-field-name",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on GUARD conjunct B: the presence test is evaluated at the
        # FIELD name instead of at the accessor name. Agrees with the frozen
        # behavior on every namespace where the two names' presence coincides, so
        # it needs its own distinguishing input (a namespace binding the field
        # name but NOT the accessor name).
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result name then\n"
            "      result := setKey result key display\n"
            "  return result"),
        "refinement": "a faithful real counterpart decides whether to register by "
                      "asking whether the class provides the FIELD's own attribute "
                      "rather than the accessor name. On an ordinary choice-carrying "
                      "field the class does provide that attribute, so the registration "
                      "is skipped and no display accessor exists to call — the "
                      "choice-and-display P2P tests (GetFieldDisplayTests: "
                      "test_choices_and_field_display, test_iterator_choices, "
                      "test_empty_iterator_choices) would break for lack of the "
                      "accessor. It would NOT resolve.",
        "rationale": "REJECT from GUARD conjunct B, at the sub-domain the outright "
                     "conjunct-drop does not reach: the rival's presence test is taken "
                     "at the wrong name, so on a namespace binding the FIELD name but "
                     "not the accessor name it skips a registration the spec requires "
                     "(`hasChoices && !hasKey attrs key` is TRUE there, so the spec "
                     "pins `attrs ++ [(key, display)]` while the rival returns `attrs`). "
                     "Its own distinguishing input, since it agrees with the frozen "
                     "behavior wherever the two names' presence coincides. Binders: "
                     "`attrs = [(\"x\", 7)]`, `name = \"x\"`, `hasChoices = true`, "
                     "`display = 5`. If it verified => SPEC-TOO-WEAK (the guard's "
                     "subject is unpinned).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"x\", (7 : Int))] \"x\" true 5\n"
            "    (implementation_registerDisplay [(\"x\", (7 : Int))] \"x\" true 5) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
        },
    {
        "id": "weak-never-install",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the REGISTRATION itself: the namespace is returned untouched on
        # every input, so the then-branch never fires (partial-domain: correct
        # only where the spec's guard is false).
        "module": _impl(
            "  let result := attrs\n"
            "  return result"),
        "refinement": "a faithful real counterpart never registers the generated "
                      "display accessor at all, so an ordinary choice-carrying field "
                      "has no display accessor on its class. The choice-and-display "
                      "P2P tests (GetFieldDisplayTests) call that accessor and would "
                      "raise for its absence, and the failing test — which asserts a "
                      "value FROM such an accessor — would not be reached either. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the then-branch existing at all: the spec pins "
                     "`result = attrs ++ [(key, display)]` whenever `hasChoices && "
                     "!hasKey attrs key`, and the rival returns `attrs` on every input "
                     "— provably wrong on the whole guard-true sub-domain. Refuted at a "
                     "namespace holding one unrelated binding and no accessor binding. "
                     "Binders: `attrs = [(\"other\", 7)]`, `name = \"x\"`, `hasChoices "
                     "= true`, `display = 5`. If it verified => SPEC-TOO-WEAK "
                     "(partial-domain: the registration obligation is hollow).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"other\", (7 : Int))] \"x\" true 5\n"
            "    (implementation_registerDisplay [(\"other\", (7 : Int))] \"x\" true 5) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the THEN-branch VALUE: registers under the right name but binds
        # a fixed value instead of the one supplied.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result key 0\n"
            "  return result"),
        "refinement": "a faithful real counterpart binds the display accessor name to "
                      "something other than the accessor built for this field, so "
                      "calling it does not return that field's choice label. The "
                      "choice-and-display P2P tests assert the label a given field "
                      "value maps to, and would read the wrong thing. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the then-branch VALUE pin (`… ++ [(key, display)]`): "
                     "the rival binds a constant instead of `display`, so the `display` "
                     "binder is ignored entirely. Refuted at an empty namespace, where "
                     "branch selection and registered name are both correct and ONLY "
                     "the value differs — isolating the value pin. Binders: `attrs = "
                     "[]`, `name = \"x\"`, `hasChoices = true`, `display = 5`. If it "
                     "verified => SPEC-TOO-WEAK (the registered value is unpinned, and "
                     "no rival would be caught for mishandling the `display` binder).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    ([] : List (String × Int)) \"x\" true 5\n"
            "    (implementation_registerDisplay ([] : List (String × Int)) \"x\" true 5) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-skip-zero-value",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS that folds the `display` binder into the GUARD: correct on
        # every input the rest of the battery probes, and wrong only when the
        # supplied accessor value is the carrier's zero. weak-wrong-value pins
        # WHICH value is written but never that the registration must happen
        # REGARDLESS of that value, so this reaches a sub-domain no other rival
        # touches.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices && display != 0 then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result key display\n"
            "  return result"),
        "refinement": "a faithful real counterpart decides whether to register by "
                      "inspecting the accessor object it was handed and skipping the "
                      "registration for some distinguished value of it (a falsy or "
                      "sentinel accessor). A choice-carrying field whose generated "
                      "accessor hits that case then has no display accessor on its "
                      "class, so the choice-and-display P2P tests "
                      "(GetFieldDisplayTests) raise for its absence. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the GUARD's SUBJECT: the spec's guard is `hasChoices "
                     "&& !hasKey attrs key` and mentions `display` nowhere, so whether "
                     "the registration fires may not depend on the value being "
                     "registered. The rival adds `display != 0` to the guard, so at "
                     "`display = 0` the spec pins `attrs ++ [(key, 0)]` while the rival "
                     "returns `attrs`. Refuted at the one `display` value the rest of "
                     "the battery never supplies. Binders: `attrs = []`, `name = \"w\"`, "
                     "`hasChoices = true`, `display = 0`. If it verified => "
                     "SPEC-TOO-WEAK (the registration could be made conditional on the "
                     "registered value, and every other witness would still pass).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    ([] : List (String × Int)) \"w\" true 0\n"
            "    (implementation_registerDisplay ([] : List (String × Int)) \"w\" true 0) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the THEN-branch NAME: the right value is registered under the
        # field's own name rather than the derived accessor name.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result name display\n"
            "  return result"),
        "refinement": "a faithful real counterpart registers the accessor under the "
                      "field's own attribute name instead of the derived display "
                      "accessor name, which both leaves no display accessor to call "
                      "(breaking the choice-and-display P2P tests) and overwrites the "
                      "field's own attribute. It would NOT resolve.",
        "rationale": "REJECT from the then-branch NAME pin (`key = displayKey name`): "
                     "the rival writes at `name`, so the spec's `attrs ++ [(displayKey "
                     "name, display)]` does not hold. Refuted at an empty namespace "
                     "with a DIFFERENT field name from the value-pin rival's, so the "
                     "`name` binder is genuinely varied across the battery. Binders: "
                     "`attrs = []`, `name = \"f\"`, `hasChoices = true`, `display = 3`. "
                     "If it verified => SPEC-TOO-WEAK (the registered name is "
                     "unpinned, so the `name` binder would be unprobed).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    ([] : List (String × Int)) \"f\" true 3\n"
            "    (implementation_registerDisplay ([] : List (String × Int)) \"f\" true 3) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-discard-namespace",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the THEN-branch PRESERVED PREFIX: registers correctly but drops
        # everything the namespace already held.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := [(key, display)]\n"
            "  return result"),
        "refinement": "a faithful real counterpart replaces the class' whole attribute "
                      "namespace with just the newly registered accessor, discarding "
                      "every other attribute the class carries. Essentially every P2P "
                      "test touching such a class would break (its fields and methods "
                      "would be gone). It would NOT resolve.",
        "rationale": "REJECT from the then-branch PREFIX (`attrs ++ …`, i.e. the "
                     "pre-existing bindings survive): the rival returns only the new "
                     "binding. Refuted at a namespace with TWO unrelated bindings, "
                     "where the registered name and value are both correct and only the "
                     "prefix is lost — isolating that component. Binders: `attrs = "
                     "[(\"other\", 7), (\"k\", 9)]`, `name = \"x\"`, `hasChoices = "
                     "true`, `display = 4`. If it verified => SPEC-TOO-WEAK (the "
                     "namespace-preservation part of the pin is hollow).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"other\", (7 : Int)), (\"k\", (9 : Int))] \"x\" true 4\n"
            "    (implementation_registerDisplay\n"
            "      [(\"other\", (7 : Int)), (\"k\", (9 : Int))] \"x\" true 4) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-clobber-on-install",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level frame attack on the THEN-branch (the reachable analogue of
        # the sibling's frame-mutation rival): registers exactly the right
        # binding, then zeroes every OTHER binding's value. Distinct from
        # weak-clobber-other, which corrupts on the no-write branch instead.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result key display\n"
            "      result := result.map (fun p => if p.1 == key then p else (p.1, 0))\n"
            "  return result"),
        "refinement": "a faithful real counterpart registers the display accessor "
                      "correctly but, in the same step, silently rebinds every other "
                      "attribute the class already carries. The P2P tests that depend "
                      "on those attributes (the choice-set tests read the field's own "
                      "descriptors) break, so it would NOT resolve — even though the "
                      "display accessor it installs is the right one.",
        "rationale": "REJECT from the then-branch PREFIX pin read as a FRAME clause: "
                     "the bindings carried over must be carried over UNCHANGED, and the "
                     "rival rewrites their values. Refuted on the registering branch at "
                     "a namespace with two unrelated bindings and a third field name, "
                     "so the point is distinct from the else-branch clobber rival's. "
                     "Binders: `attrs = [(\"a\", 3), (\"b\", 4)]`, `name = \"z\"`, "
                     "`hasChoices = true`, `display = 6`. If it verified => "
                     "SPEC-TOO-WEAK (the frame guarantee on the registering branch is "
                     "hollow, and a rival could corrupt unrelated state freely).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"a\", (3 : Int)), (\"b\", (4 : Int))] \"z\" true 6\n"
            "    (implementation_registerDisplay\n"
            "      [(\"a\", (3 : Int)), (\"b\", (4 : Int))] \"z\" true 6) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-clobber-other",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-level frame attack reaching the ELSE-branch: it does the correct
        # nothing to the accessor name when that name is already bound, but still
        # rewrites the other bindings — so the "namespace unchanged" case is the
        # clause that catches it. Not subsumed by weak-clobber-on-install, whose
        # corruption fires only when a registration happens.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result key display\n"
            "    result := result.map (fun p => if p.1 == key then p else (p.1, 0))\n"
            "  return result"),
        "refinement": "a faithful real counterpart correctly leaves a class' own "
                      "declared accessor alone, but corrupts the class' OTHER "
                      "attributes while processing a choice-carrying field. The failing "
                      "test's own class declares an accessor AND a field, so the field "
                      "binding it needs would be rewritten; the choice-set P2P tests "
                      "break for the same reason. It would NOT resolve.",
        "rationale": "REJECT from the ELSE-branch (`result = attrs` — no write at all "
                     "when the accessor name is already bound): the rival still "
                     "rewrites the unrelated bindings there. Refuted at a namespace "
                     "that already binds the accessor name AND holds an unrelated "
                     "binding, so the guard components hold of the rival and ONLY the "
                     "else-branch is violated — attributing the rejection to that one "
                     "clause. Binders: `attrs = [(\"get_f_display\", 1), (\"other\", "
                     "7)]`, `name = \"f\"`, `hasChoices = true`, `display = 9`. If it "
                     "verified => SPEC-TOO-WEAK (the no-write case is not actually "
                     "pinned to be a no-write).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    [(\"get_f_display\", (1 : Int)), (\"other\", (7 : Int))] \"f\" true 9\n"
            "    (implementation_registerDisplay\n"
            "      [(\"get_f_display\", (1 : Int)), (\"other\", (7 : Int))] \"f\" true 9) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
    {
        "id": "weak-flag-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks GUARD conjunct A: registers exactly when it should not, on the
        # inverted flag. This is the only rival that moves the `hasChoices`
        # binder off `true`, which is what keeps that binder from being one every
        # witness holds fixed.
        "module": _impl(
            "  let mut result := attrs\n"
            "  if !hasChoices then\n"
            "    let key := displayKey name\n"
            "    if !hasKey result key then\n"
            "      result := setKey result key display\n"
            "  return result"),
        "refinement": "a faithful real counterpart registers the generated display "
                      "accessor exactly on the fields that carry NO enumerated choice "
                      "set, and on none of the fields that do. Every choice-carrying "
                      "field then lacks its accessor (the choice-and-display P2P tests "
                      "break) while plain fields gain a spurious one. It would NOT "
                      "resolve.",
        "rationale": "REJECT from GUARD conjunct A (`hasChoices`): the rival registers "
                     "when the flag is FALSE, where the spec pins `result = attrs`. "
                     "Refuted at `hasChoices = false` — the only witness in the battery "
                     "at that value, so this is what discriminates the `hasChoices` "
                     "binder rather than holding it fixed at `true`. Binders: `attrs = "
                     "[]`, `name = \"x\"`, `hasChoices = false`, `display = 5`. If it "
                     "verified => SPEC-TOO-WEAK (the flag dependence is unpinned and a "
                     "rival ignoring the flag would go unnoticed).",
        "witness": (
            "example : ¬ problem_spec_registerDisplay\n"
            "    ([] : List (String × Int)) \"x\" false 5\n"
            "    (implementation_registerDisplay ([] : List (String × Int)) \"x\" false 5) := by\n"
            "  unfold problem_spec_registerDisplay implementation_registerDisplay\n"
            "  simp only [Id.run]\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling ships 9 SPEC cases (2 soundness, 2
# admissibility, 5 uniqueness) over TWO contracted functions plus an empty AXIOM
# lane. It splits the behavior by CASE — `preserve_existing_accessor` (precondition:
# the accessor name is already bound) and `install_missing_accessor` (precondition:
# it is not) — each with a precondition and a per-key plus quantified frame. This
# bundle models the SAME behavior as ONE total function with NO precondition, whose
# postcondition pins the entire resulting namespace in a single equation, so the
# sibling's two functions are the two BRANCHES of one obligation here.
#
#   sibling case                     -> here
#   ---------------------------------------------------------------------------
#   pos-preserve-reorder             -> pos-swapped-nesting          RE-EXPRESSED
#   pos-install-unconditional        -> pos-merged-guard             RE-EXPRESSED
#                                       + pos-direct-append          RE-EXPRESSED
#   admiss-install-fresh             -> admiss-install-missing-accessor    PORTED
#   admiss-preserve-override-present -> admiss-preserve-existing-accessor   PORTED
#   rival-preserve-overwrite         -> weak-overwrite-existing       PORTED
#   rival-install-noop               -> weak-never-install            PORTED
#   rival-install-wrong-identity     -> weak-wrong-value              PORTED
#   rival-clobber-other-install      -> weak-clobber-on-install       PORTED
#   rival-clobber-other-preserve     -> weak-clobber-other            PORTED
#   AXIOM_TESTS (0)                  -> (none)                        N/A (G-AX)
#   (added, no sibling counterpart: weak-guard-on-field-name,
#    weak-wrong-key, weak-discard-namespace, weak-flag-inverted;
#    added by the independent audit: weak-skip-zero-value,
#    pos-find-presence-test)
#
# RE-EXPRESSED (positives): the sibling's branch-reorder argument becomes
#   pos-swapped-nesting (the guard's two conjuncts nested in the opposite order),
#   and its "cheapest honest impl with the here-redundant guard removed" argument
#   becomes pos-merged-guard (the two nested tests merged into the spec's own
#   conjunctive spelling). The sibling could drop the guard outright because its
#   PRECONDITION made it redundant; this obligation has no precondition, so the
#   guard cannot be dropped — dropping it is exactly weak-overwrite-existing, a
#   rival. pos-direct-append carries the same "faithful reshape must verify"
#   argument one level deeper, on the DATA flow (the general replace-or-append
#   assignment specialized to the append the spec states); it is the only case
#   that re-proves, and it does so by deleting one now-unused name from the
#   `unfold` list, with the theorem statement byte-identical.
#
# PORTED (both admissibility cases) — CORRECTED BY THE SECOND AUDIT. An earlier
#   revision recorded this lane as VACUOUS, reasoning that
#   `correct_registerDisplay` binds `∀ attrs name hasChoices display` with no
#   precondition hypothesis, so there is no `Requires` to admit. The premise is
#   true and the CONCLUSION does not follow: "the frozen obligation has no
#   precondition" is exactly the reason that is not sufficient here. On a total
#   carrier the reachable analogue of PRECOND-TOO-STRONG is the obligation being
#   UNSATISFIABLE at an F2P-shaped input, and a positive that discharges the spec
#   predicate at that concrete input by evaluation — as a `have`, before closing
#   the frozen obligation verbatim — tests it directly. Both are now shipped, one
#   per BRANCH (the sibling's two preconditioned functions are this obligation's
#   two branches), so neither branch is left unshown satisfiable:
#   admiss-preserve-existing-accessor (accessor name already bound, the
#   F2P-shaped point) and admiss-install-missing-accessor (accessor name absent,
#   the point the choice-and-display P2P tests exercise). Both verify, and both
#   were checked NON-VACUOUS by building the same `have` with its claim negated:
#   that build fails with "`decide` proved that the proposition ... is false", so
#   the `have` genuinely evaluates the predicate.
#
#   Dropping this lane silently is a measured systematic gap in the corpus (494 of
#   500 nagini batteries carry an admissibility positive; far fewer ports do), and
#   it removes one of the three directions this gate exists to test — so it is
#   recorded here as a CORRECTION rather than quietly filled in.
#
# FRAME-MUTATION: the sibling's mandatory frame class is only PARTLY vacuous here.
#   Its permission-level half is vacuous (Lean is referentially transparent: the
#   namespace is an immutable value, no aliasing, no read-only input to write
#   through), but the value-level half the sibling itself relies on — corrupting a
#   binding the operation was not asked to touch — is fully expressible and is
#   ported as BOTH clobber rivals, one per branch. Not fabricated, and not written
#   off.
#
# DIVERGENCE: no sibling case, and none is expressible here —
#   `implementation_registerDisplay` is a total Lean `def`, so a non-terminating
#   implementation cannot be written at all. Genuinely vacuous on this backend
#   (contrast velvet under partial termination semantics, where the same class is a
#   KNOWN SPEC HOLE rather than vacuous; the corpus-wide termination-semantics finding).
#
# ADDED (no sibling counterpart, required by this carrier's binder structure):
#   * weak-flag-inverted — the sibling passes its choice-set condition as a
#     PRECONDITION split across two functions, so it has no rival that moves that
#     condition. Here `hasChoices` is an INPUT BINDER of the one obligation, and
#     without this rival every witness would hold it at `true` — a rival that
#     ignored the flag would verify and the battery would never notice.
#   * weak-wrong-key — the sibling's accessor name is an opaque token supplied to
#     the function, so mis-deriving it is not expressible there. Here the name is
#     DERIVED from the `name` binder inside the modeled behavior, which makes the
#     derivation an attackable clause and the `name` binder worth varying.
#   * weak-discard-namespace — the sibling's quantified whole-namespace frame
#     exists precisely to catch this shape (its G-EQ audit found the per-key frame
#     admitted an extra write). Here the postcondition is a single equation on the
#     whole namespace, so the shape is a rival rather than a spec amendment.
#   * weak-guard-on-field-name — a NEAR-MISS on the discriminating clause,
#     refuted at the one input shape that separates it from the outright
#     conjunct-drop, so its rationale's sub-domain claim is demonstrated rather
#     than asserted.
#
# INDEPENDENT AUDIT (adversarial re-derivation of this port, all builds re-run).
#   Statement integrity: every case's `theorem correct_registerDisplay` statement
#   was extracted and compared byte-for-byte against the frozen file — all
#   identical, and only the `impl` region differs (plus `proof` for the two
#   positives that legitimately re-prove). Each of the reject witnesses was
#   rebuilt twice by hand: all ELABORATE against their rival (exit 0) and all FAIL
#   against the frozen solution (exit 1), and every gold-side failure is the
#   SEMANTIC form — `decide` proving the negation of the witness's claim is false,
#   i.e. gold satisfies the spec at that very input. No stuck reduction, no
#   unknown identifier, no timeout, so each failure is a refutation and not a
#   syntactic accident. No witness binds anything, so no consistency probe is
#   owed.
#
#   Two amendments came out of that audit, both recorded above:
#     * weak-skip-zero-value (ADDED) — the battery pinned WHICH value gets
#       registered but never that the registration must fire REGARDLESS of that
#       value, so a rival folding `display` into the guard verified against every
#       existing witness. Found by writing it; it is refuted at `display = 0`.
#     * pos-find-presence-test (ADDED) — the three original positives all keep a
#       guard definitionally equal to the frozen one, so none of them would catch
#       a spec over-fit to `List.any` as the presence test. This one has to prove
#       the two decision procedures equal by induction.
#   A false coverage claim was also corrected: the docstring asserted `name` took
#   four values across the witnesses when the texts only used three.
#
# SECOND INDEPENDENT AUDIT (a different auditor, every build re-run from scratch;
#   54 + 20 real `lake env lean` builds). Confirmed independently:
#     * Statement integrity (attack A) — re-extracted all 14 (now 16) statements
#       both whitespace-normalized AND raw-byte, plus a line-level diff of every
#       variant against the frozen file: all statements byte-identical, and the
#       only hunks are in `impl` (plus `proof` for the positives that re-prove and
#       the two new admissibility cases). variant_problems clean on all.
#     * Witness discrimination (attack B) — all 10 rebuilt on BOTH sides: rival
#       exit 0, gold exit 1 for every one, with gold's error the SEMANTIC form
#       (`decide` proving the negation is false, printing the fully evaluated
#       namespaces). Scanned all 20 gold-side logs for every known hollow shape
#       (stuck reduction, `Dependent elimination failed`, missing `Decidable`,
#       `Application type mismatch`, unknown identifier/constant): zero hits.
#     * FORGERY test (attack B′) — for all 10, the claim was FLIPPED (the `¬`
#       dropped, i.e. asserting the spec HOLDS at that input) and built on both
#       sides. Every flipped claim VERIFIES on gold (exit 0, empty log) and FAILS
#       on its rival (exit 1). Combined with the witness pair that is a complete
#       2x2: gold's exit code tracks the claim in both directions, so it carries
#       real information about the claim and none of these cases is hollow.
#     * Rival non-vacuity (attack C) — the carrier semantics were re-implemented
#       independently and all 10 rivals differ from the spec on a large sub-domain
#       (69 to 2394 of 3591 sampled inputs), all 4 positives agree with the spec
#       everywhere sampled, and each witness input was checked to differ from gold
#       at the INDUCED-MAPPING level too, not merely as a list — so no case rests
#       on the list encoding that DUPLICATE-APPEND and PREPEND were dropped for.
#
#   Two defects were found and FIXED (both above):
#     * the ADMISSIBILITY lane was recorded VACUOUS on a reason that does not
#       follow ("the frozen obligation has no precondition"). Two cases now ship.
#     * the coverage counts were false again, in both directions: the docstring
#       claimed `name` took FIVE values while its own parenthetical listed four,
#       and the closing block said `attrs` in six / `display` in six where the
#       witnesses carry seven attrs literals (six shapes) and seven display
#       values. Recounted from the texts and corrected.
#
#   Further probes by this audit, all machine-checked, none of which found a hole:
#     * attack D, SEVEN new wrong impls beyond the shipped ten, aimed at what the
#       battery left unattacked — a guard on the field name's LENGTH (every
#       shipped witness uses a 1-character name, so none of them reaches it);
#       register only into an empty namespace; register only into a NON-empty one;
#       derive the accessor name without its trailing part; take the presence test
#       on the stored VALUE rather than the key; plus prepend and duplicate-append.
#       All SEVEN were rejected by the frozen spec, and a witness was built for
#       each against its rival (exit 0) confirming the rejection is the spec's.
#     * attack E, FOUR new correct reshapes: early-return control flow instead of
#       the mutable accumulator; `match` on the two guard conditions; the whole
#       decision hoisted into a `let`-bound Bool; and a THIRD decision procedure
#       (`(map Prod.fst).contains`, proven equal to the spec's `List.any` by
#       induction). All FOUR verify, so the spec is not over-fit. Worth recording
#       honestly: the `contains` reshape took six proof attempts, and every failure
#       was in MY helper lemma (a looping `List.elem` simp set, then `==` argument
#       order) rather than a spec rejection — a reshape one cannot immediately
#       prove is not evidence of a hole, and was not reported as one.
#     * the `refinement` prose was checked against instance.json rather than read:
#       every test named — test_overriding_FIELD_display as the F2P, and
#       test_choices_and_field_display / test_iterator_choices /
#       test_empty_iterator_choices as P2P in GetFieldDisplayTests — exists and is
#       in the lane the prose puts it in.
#
#   Rivals CONSIDERED AND REJECTED as vacuous on this carrier (recorded so they
#   are not re-proposed):
#     * DUPLICATE-APPEND (`result ++ [(key, display), (key, display)]`) — the
#       frozen spec does reject it and a witness for it builds, but under this
#       bundle's own observability rule (mapping.md: "attribute lookup is by-key,
#       so order is not observable"; G-CONF compares the INDUCED MAPPING) a
#       namespace with the accessor bound twice to the same value induces exactly
#       the mapping gold induces. It is therefore distinguishable only at carrier
#       granularity, not as modeled behavior, so shipping it would attest to the
#       list encoding rather than to the spec. Dropped deliberately.
#     * PREPEND (`(key, display) :: result`) — same reason, and worth stating
#       explicitly because the spec REJECTS it (witness built, exit 0) while the
#       modeled behavior arguably does not care: the real assignment primitive is
#       append-ordered and lookup is by key, so order is unobservable per
#       mapping.md. This is a place where the frozen spec is STRICTER than the
#       modeled surface (it pins list order), but it is stricter in the direction
#       that only ever rejects extra impls, and the real op is append-ordered
#       anyway, so no faithful counterpart of the patched behavior is excluded.
#       Noted as a modeling observation, NOT filed as a soundness hole.
#
#   SPEC-TOO-WEAK probe (attack D): five further wrong impls were written and all
#   were REJECTED — skip-registration for one hard-coded field name; register only
#   into an empty namespace; take the presence test on the stored VALUE rather
#   than the key; the duplicate above; and the zero-value near-miss now shipped.
#   SPEC-TOO-STRONG probe (attack E): five further CORRECT reshapes were written
#   and all VERIFY — early-return control flow instead of the mutable
#   accumulator; the `find?` presence test now shipped as a positive; the whole
#   decision hoisted into a `let`-bound Bool; `match` on the guard instead of
#   nested `if`; and filter-then-append (the stale binding removed before the
#   append, a no-op under the guard, proved by induction). No spec hole in either
#   direction.
#
# The ten reject witnesses probe TEN DISTINCT input points (all ten 4-tuples are
# pairwise distinct) and vary all four binders (`attrs` in seven distinct
# literals over six qualitative shapes; `name` in four; `hasChoices` in both;
# `display` in seven). Every independent component of the postcondition — both guard
# conjuncts, the registered name, the registered value, the preserved prefix, the
# existence of the registration, and the else-branch no-write — is attacked by
# some rival, and the single obligation is both defended (three verifying
# positives) and attacked.
#
# AXIOM_TESTS: empty, matching the sibling. `meta.json` records no axioms — the
# namespace primitives are modeled deeply in the frozen pure region, so there is
# no assumed callee contract to falsify, and the axiom lane belongs to G-AX in any
# case.
AXIOM_TESTS = []
