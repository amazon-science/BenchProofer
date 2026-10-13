"""properties.py — G-PBT falsification battery for django__django-16950 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant sharing the FROZEN spec
byte-for-byte (region surgery: only text inside ``-- impl-start``/``-- impl-end``
and, where a case legitimately re-proves, ``-- proof-start``/``-- proof-end``,
so ``markers.same_spec`` holds and the single ``theorem
correct_clearParentKeyDefault`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the decision as a PROCEDURE mutating a heap field: a ``ParentObject``
whose ``key : Optional[int]`` is held at full permission, with the post-state
pinned by three clauses — a framing clause ``Acc(instance.key)``, a CLEAR clause,
and a PRESERVE clause — plus a termination obligation in the precondition. This
Lean bundle models the SAME decision on a referentially-transparent carrier: one
total function of the four boolean observables plus the attribute's current
value, returning the attribute's resulting value as ``Option V``. The heap
mutation becomes a returned value, so nagini's three post-state clauses collapse
into ONE equational clause over a two-branch conditional, and the CLEAR/PRESERVE
split survives as the two branches of that conditional. Each nagini rival's
ARGUMENT ports directly (it attacks a conjunct of the decision, or the
retained-value half); only its mechanics are rewritten. The per-case mapping,
and every nagini case principledly omitted, is in ``assessment`` at the bottom.

DEFENDED SURFACE (one modeled behavior, one obligation). The single obligation
pins ``result`` equal to a grounded two-branch computation over the inputs:
``none`` exactly when the decision predicate holds, and ``some current`` — the
existing value carried through UNCHANGED — otherwise. The decision predicate is
itself grounded (fully unfolded over the four boolean observables, no opaque
callee anywhere in the spec), so the independent top-level structure the
postcondition pins is:

  * the CLEAR branch — the attribute is absent exactly when the parent is being
    added AND the key field carries a default AND (the key field is the parent's
    primary key OR the form carries no submitted data). Four conjunct/disjunct
    positions, each of which a rival can drop, weaken, or invert;
  * the RETAIN branch — when the decision does not hold, the result is ``some
    current``: the FRAME half. The retained value is pinned to the INPUT value,
    so an implementation may neither clear it nor substitute a different one;
  * the two branches are mutually exclusive and exhaustive over all 16 boolean
    combinations, so a rival that shifts the boundary in EITHER direction (clears
    where the spec retains, or retains where the spec clears) contradicts the
    equation.

BEHAVIOURAL DISCRIMINATOR (the fix). An alternate (non-primary) key carrying a
default is left UNTOUCHED whenever the form carries submitted data — the
sub-domain ``adding ∧ hasDefault ∧ ¬isParentPk ∧ hasFormData``, where the
decision is false and the value must survive. The ``reject-prepatch`` rival below
IS the pre-fix behaviour (its guard drops the second factor entirely) and its
witness is exactly that sub-domain's input.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS AS A PERMISSION CLASS, LIVE AS A VALUE
    CLASS. Lean is referentially transparent: the inputs carry no heap
    permission, there is no fractional half-permission to overwrite and no
    aliasing to exploit, so the permission-system flavour of the nagini rival has
    no expressible instance and no substitute is fabricated. But note that the
    nagini case it came from was ALREADY not a permission attack — the nagini
    docstring records that the attribute is held at FULL permission precisely
    because the clear path genuinely mutates it, so that rival was caught by the
    PRESERVE clause, not by insufficient permission. That argument ports exactly:
    it becomes an attack on the RETAIN branch, and it is carried below
    (``reject-clear-everything``, plus every rival whose witness sits in the
    retain sub-domain).

    One HALF of that nagini rival is genuinely inexpressible here, and this was
    measured rather than argued. nagini's ``frame-preserve-write`` writes a
    *specific different* value (``instance.key = 999``) on the preserve path. On
    this carrier the retained value has type ``V``, an arbitrary ``Type`` with no
    instance available, so there is no second inhabitant to name: the closest
    shape, ``keyAttr := some default``, fails to elaborate with ``failed to
    synthesize Inhabited V`` (two occurrences, at the retain branch and the
    not-adding branch). The type variable is what makes it unwritable — and it is
    also what makes the frame claim STRONGER than nagini's, since parametricity
    means an impl cannot invent any ``V`` at all. What remains expressible is
    substituting the OTHER inhabitant of ``Option V`` — ``none`` — on a retained
    path, and that is exactly ``reject-clear-everything``. So the value-class heir
    is shipped and the specific-wrong-value flavour is inexpressible for a
    demonstrated reason, not a difficulty.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE (not a vacuous class).
    CORRECTED BY AUDIT. An earlier revision of this docstring recorded the class
    as "genuinely vacuous — a diverging implementation cannot be WRITTEN against
    this obligation at all", resting on the claim that escaping to ``partial def``
    "demands an ``Inhabited V`` instance the byte-identical theorem statement
    cannot supply (failed to synthesize Inhabited V)". That claim is FALSE and was
    measured false: a ``partial def`` whose body is a self-call at an unchanged
    measure elaborates with NO ``Inhabited`` error whatsoever. ``partial def``
    needs ``Inhabited`` only for the *return* type, and the return type here is
    ``Option V``, which is ``Inhabited`` for every ``V`` via ``none`` — so no
    instance on ``V`` is ever required. (The ``Inhabited V`` error is real but
    belongs to a DIFFERENT rival: writing a *different* value on the retain path
    needs ``some default``, and THAT is what fails to synthesize. The prior text
    attached the right error to the wrong case.)

    What is actually true, measured on both shapes:
      - a NON-partial self-call is rejected at DEFINITION time by the termination
        checker ("no parameters suitable for structural recursion … does not take
        any (non-fixed) arguments"), so that shape is genuinely unwritable;
      - a ``partial def`` self-call IS writable, is in ``variant_scope`` (no new
        declaration, no banned token, statement byte-identical), and DOES fail to
        verify — but it fails with ``Tactic `unfold` failed to unfold
        implementation_clearParentKeyDefault``, i.e. because a ``partial def`` is
        irreducible and the frozen script cannot unfold it. That is a TACTIC gap,
        not an attribution to the spec, which is exactly the failure mode the
        witness requirement exists to expose.

    So the rival exists; what does not exist is a witness that discriminates it.
    A closed witness cannot be stated (the impl is irreducible, so ``decide``
    decides nothing about it). Both hypothesis-conditioned shapes were built:
    ``(h : impl … = none)`` and ``(h : impl … ≠ some 7)``. Each elaborates against
    the partial rival AND against the frozen solution (both exit 0), because the
    hypothesis is false of any correct impl and therefore proves the refutation
    outright — the gate reads that as ``witness-vacuous``, correctly. A
    ``witness_reference`` cannot help either, for the same reason: the hypothesis
    contradicts EVERY verifying impl of this spec, so it would hold of the
    reference too. No reject case is therefore shipped, and the honest
    disposition is a KNOWN HOLE in the spec — this obligation does not constrain
    a non-terminating implementation, and this battery does not detect one — NOT
    a vacuous class, which would assert the battery is complete here.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is grounded in the
    inputs; there is no opaque answer key an implementation could echo instead of
    doing the work, because echoing the grounded computation IS the work. In its
    place the battery carries honest cheapest-implementation positive controls
    (``pos-decision-branch`` is exactly the echo shape, and it is CORRECT).

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery: rivals
    correct on most of the domain but diverging where one factor of the decision
    bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script closes by exhaustive
``cases … <;> rfl`` tuned to the frozen branch form — so a rejection alone
attributes nothing to the spec. Every ``expect="reject"`` case therefore carries
a Lean snippet stating the spec predicate directly at ONE concrete input and
refuting it. The carrier is FULLY TRANSPARENT (four ``Bool`` literals plus a
concrete value for ``V``), so no conditioning on an opaque term is needed and no
witness binds any hypothesis — every witness is closed, so there are no
assumptions that could be jointly unsatisfiable. Each was built BOTH ways before
shipping: it elaborates against its rival, and ``decide`` reports the proposition
false against the frozen solution.

FORGERY-CHECKED (audit). All seven gold-side failures are PLAIN EVALUATIONS —
``Tactic `decide` proved that the proposition ¬(…) is false``, with the fully
reduced conditional and the concrete value printed in the error. That is the
kernel having computed the claim and found the negation false, not a stuck
reduction, a missing identifier, a type error, or a timeout. It was nonetheless
confirmed to carry information about the CLAIM rather than about the file: for
each of the seven, a second file differing ONLY in what it asserts (the ``¬``
dropped, so it claims the frozen impl SATISFIES the spec at that same point) was
built against the frozen solution, and all seven elaborate CLEANLY (exit 0, empty
output) where the witness itself exits 1. The exit code therefore tracks the
claim in both directions at every one of the seven points, so no case is hollow.

BINDER / POINT SPREAD. The obligation binds five inputs — ``adding``,
``hasDefault``, ``isParentPk``, ``hasFormData`` (all ``Bool``) and ``current :
V`` — plus the result. The seven reject witnesses probe SEVEN DISTINCT points and
move every binder:

    case                        adding hasDefault isParentPk hasFormData current
    reject-prepatch               T        T          F           T        7
    reject-drop-pk-arm            T        T          T           T        0
    reject-drop-hasdefault        T        F          T           F        3
    reject-ignore-adding          F        T          T           F        42
    reject-and-for-or             T        T          F           F        "s"
    reject-never-clear            T        T          T           F        5
    reject-clear-everything       F        F          F           F        9

Each of the four booleans takes BOTH polarities across the witnesses, so no
rival mishandling a single observable could slip through on a binder every
witness pinned at one value. ``current`` takes SEVEN distinct values (six
``Nat`` — 7, 0, 3, 42, 5, 9 — and one ``String``), and the type variable ``V`` is
instantiated at TWO different types (``Nat`` and ``String``) — the retained value
is genuinely opaque to the decision, so a rival inspecting or substituting it is
refuted at either instantiation. Three witnesses sit in the CLEAR sub-domain and
four in the RETAIN sub-domain, so both branches of the postcondition's
conditional are attacked.

AUDIT RECORD — the seven witnesses sit at seven distinct points, which leaves 9
of the 16 boolean combinations carrying no shipped witness. An audit pass built a
single-point-wrong rival for EACH of those 9 residual points (a rival agreeing
with the frozen decision everywhere except that one combination, in whichever
direction the frozen decision does not go there) and confirmed all of them are
REJECTED, each with a closed witness that elaborates at exactly that point. So
the uncovered points are uncovered by CHOICE OF ECONOMY, not by weakness: the
obligation is a single equation over a total function on a finite 16-point
domain, so a rival differing from the frozen decision at ANY point is refutable
by ``decide`` at that point, and no residual sub-domain is admitted. Four NEW
correct reshapes were also probed for SPEC-TOO-STRONG — a De Morgan/negation-
normal retain-first form, a 4-way ``match`` with no ``Id.run`` mutable local, an
``Option.filter`` form, and a ``bif`` chain — and all four VERIFY, so the spec
admits faithful correct impls well away from the frozen syntactic shape.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the axioms region is a comment explaining why none is needed: the
decision is a pure boolean function of the four observables and the attribute's
value is carried as a type variable). nagini's ``AXIOM_TESTS`` was likewise
empty; dropped — the axiom lane is G-AX's job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "django__django-16950"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it edits and is unique in
# the frozen file (asserted by _swap at import, so the manifest breaks loudly if
# the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# The nested guard inside the impl region: the decision, in the frozen branch
# shape. Rivals that corrupt ONE factor of the decision edit only this.
_IMPL_GUARD = """  if adding then
    if hasDefault && (isParentPk || !hasFormData) then
      keyAttr := none"""

# The whole impl BODY (mutable local, guard, return) — for rivals and positives
# that replace the shape wholesale rather than editing a factor.
_IMPL_BODY = """  let mut keyAttr : Option V := some current
  if adding then
    if hasDefault && (isParentPk || !hasFormData) then
      keyAttr := none
  return keyAttr"""

# The frozen proof body (tactic script only; the theorem STATEMENT above it is
# never touched by any case). Used by the admissibility positive, which PREPENDS
# a ground instance and then closes the frozen obligation verbatim.
_PROOF_BODY = """  intro adding hasDefault isParentPk hasFormData current
  unfold problem_spec_clearParentKeyDefault implementation_clearParentKeyDefault
    shouldReset
  cases adding <;> cases hasDefault <;> cases isParentPk <;> cases hasFormData <;> rfl"""


# ---------------------------------------------------------------------------
# SOUNDNESS POSITIVES — structurally different but CORRECT implementations that
# MUST verify. If a faithful correct implementation cannot satisfy the frozen
# obligation, the spec is SPEC-TOO-STRONG. Each keeps the theorem statement
# byte-identical and introduces no new declaration / axiom / assumption token.
#
# All three were built and close under the FROZEN tactic script unchanged: the
# script finishes with an exhaustive case split over the four booleans followed
# by `rfl`, which is robust to a reshaped branch structure as long as the
# decision is the same. So none of these needs the proof region touched at all —
# the cheapest possible positive, and the one least able to hide a weakened
# obligation.
# ---------------------------------------------------------------------------

# S1: flatten the nested guard into ONE conjunction, single conditional store.
_POS_FLAT = _swap(
    _BASE, _IMPL_GUARD,
    """  if adding && hasDefault && (isParentPk || !hasFormData) then
    keyAttr := none""")

# S2: branch REORDER — hoist the (primary-key OR no-form-data) disjunct to the
# OUTER test, with the adding + has-default conjuncts inner. Same truth value on
# all 16 combinations, De Morgan-free.
_POS_REORDER = _swap(
    _BASE, _IMPL_GUARD,
    """  if isParentPk || !hasFormData then
    if adding && hasDefault then
      keyAttr := none""")

# S3: drop the imperative mutable-local shape entirely for a functional
# two-branch return that names the grounded decision predicate directly. This is
# the "echo the grounded computation" shape — and it is CORRECT, which is exactly
# why the ungrounded-oracle class is vacuous here.
_POS_DECISION_BRANCH = _swap(
    _BASE, _IMPL_BODY,
    """  if shouldReset adding hasDefault isParentPk hasFormData then
    return none
  else
    return some current""")


# ---------------------------------------------------------------------------
# ADMISSIBILITY POSITIVE — the obligation is SATISFIABLE at the discriminating
# input, not merely in the abstract. The frozen theorem carries NO precondition
# hypothesis (the modeled behavior is total, so the `∀` is unguarded), so
# nagini's precondition-admission probe has no binder to attack here; the honest
# analogue is to discharge the spec predicate by EVALUATION at the ground
# discriminating input and then close the frozen obligation verbatim. The ground
# instance is a `have` inside the existing tactic body: no new declaration, the
# theorem statement byte-identical, nothing assumed.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE, _PROOF_BODY,
    """  have _ground : problem_spec_clearParentKeyDefault true true false true (7 : Nat)
      (implementation_clearParentKeyDefault true true false true (7 : Nat)) := by
    unfold problem_spec_clearParentKeyDefault implementation_clearParentKeyDefault
      shouldReset
    decide
""" + _PROOF_BODY)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — wrong implementations sharing the frozen spec that MUST be
# rejected. Each carries (a) the refinement argument that its faithful real patch
# would not resolve the F2P or would regress the P2P set, so a VERIFYING rival
# would be a true verify-does-not-imply-resolve break rather than an artifact,
# and (b) a refutation witness pinning the violation at one concrete input,
# checked to hold of the rival and to FAIL on the frozen solution.
# ---------------------------------------------------------------------------

# R1: drop the entire second factor — clear whenever the parent is being added
# and the key field has a default. This is the PRE-FIX decision.
_REJECT_PREPATCH = _swap(
    _BASE, _IMPL_GUARD,
    """  if adding then
    if hasDefault then
      keyAttr := none""")

# R2: drop the primary-key disjunct — clear only when the form carries no data.
_REJECT_DROP_PK_ARM = _swap(
    _BASE, _IMPL_GUARD,
    """  if adding then
    if hasDefault && !hasFormData then
      keyAttr := none""")

# R3: drop the has-a-default conjunct — clear a key field that carries no
# default at all.
_REJECT_DROP_HASDEFAULT = _swap(
    _BASE, _IMPL_GUARD,
    """  if adding then
    if isParentPk || !hasFormData then
      keyAttr := none""")

# R4: drop the being-added conjunct — clear an already-established parent's key.
_REJECT_IGNORE_ADDING = _swap(
    _BASE, _IMPL_GUARD,
    """  if hasDefault && (isParentPk || !hasFormData) then
    keyAttr := none""")

# R5: replace the disjunction with a CONJUNCTION — require both that the key
# field is the primary key and that the form carries no data.
_REJECT_AND_FOR_OR = _swap(
    _BASE, _IMPL_GUARD,
    """  if adding then
    if hasDefault && (isParentPk && !hasFormData) then
      keyAttr := none""")

# R6: never clear — always retain the current value.
_REJECT_NEVER_CLEAR = _swap(
    _BASE, _IMPL_BODY,
    """  let keyAttr : Option V := some current
  return keyAttr""")

# R7: always clear — never retain. Attacks the RETAIN branch unconditionally;
# this is the value-level heir of nagini's frame-flavoured rival (see the
# module docstring on why that nagini case was never a permission attack).
_REJECT_CLEAR_EVERYTHING = _swap(
    _BASE, _IMPL_BODY,
    """  let keyAttr : Option V := none
  return keyAttr""")


# Every witness states the frozen spec predicate at one concrete input and
# refutes it. All are CLOSED (no binders, hence no satisfiability question), and
# the carrier is fully transparent, so `decide` closes after unfolding.
def _witness(comment, adding, has_default, is_pk, has_data, current):
    args = f"{adding} {has_default} {is_pk} {has_data} {current}"
    return (
        f"{comment}\n"
        f"example : ¬ problem_spec_clearParentKeyDefault {args}\n"
        f"    (implementation_clearParentKeyDefault {args}) := by\n"
        f"  unfold problem_spec_clearParentKeyDefault implementation_clearParentKeyDefault\n"
        f"    shouldReset\n"
        f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness). Ports nagini `pos-flat` and `pos-reorder`
    # one-for-one (the nagini positives were exactly a guard flatten and a
    # branch reorder); S3 additionally covers the shape nagini's echo-class
    # discussion points at.
    # =====================================================================
    {
        "id": "pos-flat-single-conjunction",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLAT,
        "rationale": (
            "structurally-different CORRECT impl: the nested guard is flattened "
            "into a single conjunction with one conditional store, instead of "
            "two nested tests. Same decision on all 16 boolean combinations, so "
            "the obligation `result = if decision then none else some current` "
            "still closes under the frozen exhaustive case split. Theorem "
            "statement byte-identical; proof region untouched; no new "
            "declaration / axiom / assumption token. If this cannot verify => "
            "SPEC-TOO-STRONG. Ports nagini `pos-flat`."
        ),
    },
    {
        "id": "pos-reorder-outer-disjunct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "a second structurally-different CORRECT impl: the "
            "(is-primary-key OR no-form-data) disjunct is hoisted to the OUTER "
            "branch and the being-added + has-default conjuncts moved inner. "
            "De Morgan-free, same truth value everywhere, so the retained/"
            "cleared partition is unchanged and the obligation closes under the "
            "frozen script. Distinct in shape from both the frozen impl and S1. "
            "Ports nagini `pos-reorder`."
        ),
    },
    {
        "id": "pos-decision-branch-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DECISION_BRANCH,
        "rationale": (
            "a third CORRECT impl that abandons the imperative mutable-local "
            "shape for a functional two-branch return naming the grounded "
            "decision predicate directly — the cheapest correct implementation, "
            "and the closest thing to an 'echo' this carrier admits. It "
            "verifies, which is the point: the postcondition is GROUNDED in the "
            "inputs, so echoing the computation IS doing the work and there is "
            "no ungrounded answer key to cheat with. Documents nagini's "
            "echo-class discussion as vacuous rather than fabricating a rival "
            "for it."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. Ports nagini `admiss-f2p`.
    # =====================================================================
    {
        "id": "admiss-discriminating-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "the obligation is discharged at the DISCRIMINATING ground input "
            "(parent being added, key field carries a default, key field is NOT "
            "the parent's primary key, form carries submitted data, current "
            "value 7) by `decide`, and then the frozen obligation is closed "
            "verbatim. Verifies, else the modeled behavior is unsatisfiable at "
            "exactly the input the discriminating test exercises — the analogue "
            "of nagini's PRECOND-TOO-STRONG outcome. The frozen theorem carries "
            "no precondition hypothesis (the behavior is total, the `∀` "
            "unguarded), so there is no precondition binder to attack; the "
            "honest analogue is this ground evaluation. Nothing is assumed: no "
            "new declaration, theorem statement byte-identical, the ground "
            "instance is a `have` inside the existing tactic body. Ports nagini "
            "`admiss-f2p`. AUDIT: the ground `have` was confirmed LOAD-BEARING "
            "rather than decoration — replacing its claimed result with the "
            "wrong one (`none`, i.e. asserting the attribute is cleared at this "
            "input) makes the case FAIL to elaborate, with `decide` reporting "
            "`none = if (true && true && (false || !true)) = true then none else "
            "some 7` is false. So the `have` genuinely pins the retained value "
            "at the discriminating input and cannot be satisfied by an "
            "arbitrary result."
        ),
    },

    # =====================================================================
    # UNIQUENESS RIVALS.
    # =====================================================================
    {
        "id": "reject-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_PREPATCH,
        "refinement": (
            "this rival IS the pre-fix behaviour: it clears the parent's key "
            "attribute whenever the parent is being added and the key field "
            "carries a default, dropping the second factor entirely. On the "
            "reported scenario — a child linked to a parent by an ALTERNATE "
            "(non-primary) key that carries a default, with submitted form data "
            "present — it clears a value that must survive. The failing test "
            "asserts that the parent's generated alternate key is populated and "
            "that the child's stored link equals that same value; this rival "
            "leaves the attribute absent, so both assertions fail. Its faithful "
            "real patch is the pre-fix code, which is the defect being fixed, so "
            "it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the RETAIN branch: at (adding, has-default, NOT "
            "primary-key, form-data-present) the decision predicate is FALSE, so "
            "the spec pins `result = some current`, while the rival returns "
            "`none`. PRIMARY partial-domain rival — it agrees with the spec on "
            "every other combination and diverges exactly on the discriminating "
            "sub-domain. Binder spread: the only witness at isParentPk=false "
            "WITH hasFormData=true. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness(
            "-- The discriminating sub-domain: alternate (non-primary) key with a\n"
            "-- default, form data present. The spec RETAINS the value; the rival\n"
            "-- clears it. Fully concrete carrier, closes by `decide`.",
            "true", "true", "false", "true", "(7 : Nat)"),
    },
    {
        "id": "reject-drop-pk-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_DROP_PK_ARM,
        "refinement": (
            "a faithful real patch keeping only the no-form-data half of the "
            "second factor (dropping the is-the-parent's-primary-key disjunct) "
            "would fail to clear a parent's auto-generated PRIMARY key when form "
            "data is submitted, leaving a stale generated value in place instead "
            "of letting it be regenerated on save. The regression suite pins "
            "exactly that case — a parent being added must have its "
            "auto-generated primary key ignored — so this rival regresses it and "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the CLEAR branch: at (adding, has-default, "
            "primary-key, form-data-present) the decision predicate is TRUE via "
            "the primary-key disjunct, so the spec pins `result = none`, while "
            "the rival's conjunction fails on the form-data test and returns "
            "`some current`. partial-domain: correct on every alternate-key "
            "combination, diverging on the primary-key-with-data sub-domain. A "
            "NEAR-MISS of `reject-and-for-or` in outcome but not in domain — it "
            "is refuted with isParentPk=TRUE, where that rival is refuted with "
            "isParentPk=false, so the two do not share a witness. Ports nagini "
            "`drop-pk-arm`."
        ),
        "witness": _witness(
            "-- Primary key with a default, form data present: the spec CLEARS via\n"
            "-- the primary-key disjunct; the rival's conjunction retains.",
            "true", "true", "true", "true", "(0 : Nat)"),
    },
    {
        "id": "reject-drop-hasdefault",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_DROP_HASDEFAULT,
        "refinement": (
            "a faithful real patch dropping the carries-a-default conjunct would "
            "clear a linked key that has NO default — there is nothing to "
            "regenerate on save, so a value the user actually supplied would be "
            "destroyed. The regression suite pins the clearing behaviour to the "
            "has-a-default case specifically; nulling a non-default key changes "
            "observable behaviour for every ordinary inline relation and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the RETAIN branch: at (adding, NO default, primary-key, "
            "no form data) the decision predicate is FALSE because the "
            "has-default conjunct fails, so the spec pins `result = some "
            "current`, while the rival clears. partial-domain (the no-default "
            "sub-domain). Binder spread: the ONLY witness holding hasDefault at "
            "false together with adding=true — so it is the only rival that "
            "could expose a mishandling of that conjunct while the parent is "
            "being added. Ports nagini `drop-hasdefault`."
        ),
        "witness": _witness(
            "-- No default on the key field: nothing to regenerate, so the spec\n"
            "-- RETAINS regardless of the other observables; the rival clears.",
            "true", "false", "true", "false", "(3 : Nat)"),
    },
    {
        "id": "reject-ignore-adding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_IGNORE_ADDING,
        "refinement": (
            "a faithful real patch dropping the outer being-newly-added guard "
            "would reset the linked key of an ALREADY-ESTABLISHED parent every "
            "time an inline child form is prepared, destroying a persisted "
            "parent's key and breaking every edit of an existing record. The "
            "clearing behaviour exists only for a parent in the process of being "
            "added; the regression suite covers editing established records, so "
            "this rival regresses them and does NOT resolve."
        ),
        "rationale": (
            "REJECT from the RETAIN branch: at (NOT adding, has-default, "
            "primary-key, no form data) the decision predicate is FALSE because "
            "the being-added conjunct fails, so the spec pins `result = some "
            "current`, while the rival clears. partial-domain (the "
            "not-being-added sub-domain). Binder spread: one of only two "
            "witnesses at adding=false, and the only one that holds every OTHER "
            "observable at a value where the decision WOULD fire — so it isolates "
            "the being-added conjunct exactly. Ports nagini `ignore-adding`."
        ),
        "witness": _witness(
            "-- An already-established parent (not being added): the spec RETAINS\n"
            "-- even though every other observable would license clearing.",
            "false", "true", "true", "false", "(42 : Nat)"),
    },
    {
        "id": "reject-and-for-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_AND_FOR_OR,
        "refinement": (
            "a faithful real patch writing a CONJUNCTION where the second factor "
            "is a disjunction — requiring both that the key field is the "
            "parent's primary key AND that no form data was submitted — clears "
            "strictly less often than intended. It leaves an alternate key with "
            "a default populated when no form data is submitted, the case the "
            "regression suite covers as a variant of the auto-generated-key "
            "behaviour, and it also leaves a primary key populated when data is "
            "submitted. Both are regressions, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the CLEAR branch: at (adding, has-default, NOT "
            "primary-key, NO form data) the decision predicate is TRUE via the "
            "no-form-data disjunct, so the spec pins `result = none`, while the "
            "rival's conjunction fails on the primary-key test and retains. This "
            "rival is refuted in a DIFFERENT sub-domain from "
            "`reject-drop-pk-arm` (isParentPk false with no data, versus true "
            "with data), so it gets its own witness rather than sharing one. "
            "Binder spread: this witness also instantiates the type variable `V` "
            "at `String` rather than `Nat`, confirming the retained value is "
            "genuinely opaque to the decision. Ports nagini `and-disjunct`."
        ),
        "witness": _witness(
            "-- Alternate key with a default and NO form data: the spec CLEARS via\n"
            "-- the no-form-data disjunct; the rival's conjunction retains. Also\n"
            "-- instantiates the value type at `String`.",
            "true", "true", "false", "false", '"s"'),
    },
    {
        "id": "reject-never-clear",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_NEVER_CLEAR,
        "refinement": (
            "this is the remove-the-clearing-behaviour-entirely patch: the "
            "linked key is always retained. Every case the regression suite pins "
            "as requiring the auto-generated key to be ignored — a parent being "
            "added whose key field has a default, whether the primary key or an "
            "alternate key with no submitted data — would keep a stale generated "
            "value, reintroducing the original validation failure. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the CLEAR branch: at (adding, has-default, primary-key, "
            "no form data) the decision predicate is TRUE, so the spec pins "
            "`result = none`, while the rival returns `some current` on every "
            "input. The mirror of `reject-prepatch` (never clears, versus clears "
            "too eagerly), and it establishes that the CLEAR branch is "
            "load-bearing rather than satisfiable by blanket retention. Ports "
            "nagini `noop-never-clear`."
        ),
        "witness": _witness(
            "-- A genuine clear case: the spec pins the attribute ABSENT, the rival\n"
            "-- retains it.",
            "true", "true", "true", "false", "(5 : Nat)"),
    },
    {
        "id": "reject-clear-everything",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJECT_CLEAR_EVERYTHING,
        "refinement": (
            "a faithful real patch that unconditionally cleared the linked key "
            "would destroy it on every inline form preparation — for established "
            "parents, for key fields with no default, and for alternate keys "
            "with submitted data alike. It is a strict superset of the pre-fix "
            "defect: it fails the discriminating test (which asserts the "
            "alternate key survives) AND regresses the ordinary-relation cases "
            "the suite already covered, so it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the RETAIN branch, attacked UNCONDITIONALLY: at (NOT "
            "adding, NO default, NOT primary-key, no form data) — every "
            "observable at the value that forbids clearing — the spec pins "
            "`result = some current` and the rival returns `none`. This is the "
            "value-level heir of nagini's frame-flavoured rival: it 'touches' the "
            "attribute on a path the spec pins unchanged. On this carrier the "
            "rejection comes from the RETAIN clause, exactly as it did on nagini "
            "(where the attribute was held at FULL permission precisely because "
            "the clear path mutates it, so no permission violation was ever "
            "involved). Binder spread: the ONLY witness with all four booleans "
            "false — the corner of the domain furthest from the decision firing, "
            "which no other rival probes. Ports nagini "
            "`frame-preserve-write`."
        ),
        "witness": _witness(
            "-- Every observable forbids clearing: the spec RETAINS the value, the\n"
            "-- rival clears it anyway.",
            "false", "false", "false", "false", "(9 : Nat)"),
    },
]


# The axiom lane is empty on this bundle: no `opaque` callee is declared and no
# `axiom` is consumed (the axioms region records why none is needed — the
# decision is a pure boolean function of four observables and the attribute's
# value is carried through as a type variable). nagini's AXIOM_TESTS was empty
# for the same reason. The axiom lane belongs to G-AX; this gate ignores it.
AXIOM_TESTS = []
