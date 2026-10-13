"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9320 (lean).

NOT a Lean file; a record of adversarially-reasoned cases the G-PBT gate
executes. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte — region surgery touches only text inside the
``-- impl-start`` / ``-- impl-end`` region and, for a case that legitimately
re-proves, inside ``-- proof-start`` / ``-- proof-end`` — so
``markers.same_spec`` holds by construction and every ``theorem correct_*``
STATEMENT stays byte-identical. ``expect:"verify"`` passes iff the variant is in
scope AND the file elaborates with the obligation genuinely closed (no ``sorry``
/ ``admit`` / ``native_decide`` / new ``axiom`` / new lemma);
``expect:"reject"`` passes iff the variant is in scope AND it does NOT verify
AND the case's refutation ``witness`` holds of the rival while FAILING on the
frozen solution.

This battery is a PORT of the nagini sibling's spec lane, re-expressed against
this backend's carrier. The nagini bundle contracts THREE functions over a
``List[int]`` code-point carrier with fractional read permissions; this bundle
models only the purely functional core — one entry validator over Lean
``String`` returning ``Except String String`` — so the case count is smaller by
carrier narrowing, not by omission of work. See PORTED / DROPPED below.

=========================================================================
DEFENDED SURFACE
=========================================================================

One modeled behavior, one obligation (``correct_validateRootEntry``):

    problem_spec_validateRootEntry (x : String)
        (result : Except String String) : Prop :=
      (x = "" → result = Except.ok x) ∧
      (x ≠ "" → result = checkExistingDir x)

ONE input binder, ``x`` — the candidate entry — and NO precondition hypothesis:
the ``∀`` in ``correct_validateRootEntry`` is unguarded, so the behavior is
total and every entry is in domain.

The postcondition has TWO independent top-level clauses, and the battery attacks
both:

  (C1) the EMPTY-ENTRY clause. An empty entry is accepted, and accepted
       VERBATIM: the result is ``.ok x`` (i.e. ``.ok ""``) — not an error, and
       not some other accepted value. Two degrees of freedom a wrong
       implementation can abuse here: the ok-vs-error disposition, and WHICH
       value is handed back.
  (C2) the NON-EMPTY-ENTRY clause. A non-empty entry yields exactly the
       existing-directory check's result FOR THAT ENTRY. Two degrees of freedom:
       WHICH entries are routed to the check (the empty/non-empty split must
       land the right way round, and must key on emptiness rather than on some
       other property of the entry), and WHICH ARGUMENT the check is applied to
       (the entry as given, not an adjusted form of it).

C1 is the load-bearing clause for the FAIL_TO_PASS observation: the single F2P
test supplies an empty entry at the re-prompt and requires the surrounding flow
to stop. That can only happen if the empty entry flows back to the caller as an
accepted empty value instead of being reported as a validation error. C2 is the
preservation half — the existing-directory requirement that the PASS_TO_PASS
flows depend on must survive unchanged for every non-empty entry.

=========================================================================
ADVERSARIAL READ OF EACH CLASS ON THIS CARRIER
=========================================================================

* FRAME / PERMISSION MUTATION — **VACUOUS**. Lean is referentially transparent:
  ``x`` is an immutable ``String`` value, there is no heap permission to hold at
  a fraction, no aliasing, and no way to write through an input reference. The
  nagini sibling's two frame-mutation rivals (each writing to an input the
  contract grants only read access to) have no expressible instance here. No
  substitute is fabricated for them.

* DIVERGENCE / NON-TERMINATION — **KNOWN HOLE, not vacuous**, and measured
  rather than argued. This bundle sets no ``loom.semantics.termination`` option
  at all: it is a vanilla Lean bundle, so there is no termination obligation for
  a rival to fail. The earlier claim that "``partial`` is rejected outright by
  the scope check" is FALSE and was checked: ``variant_problems`` returns ``[]``
  for a ``partial def implementation_validateRootEntry x := implementation_
  validateRootEntry x`` variant — the scope check bans no such thing — and the
  variant is admissible. It is REJECTED by the verifier, but for the wrong
  reason: the build fails at ``Tactic `unfold` failed to unfold
  `implementation_validateRootEntry``` (a ``partial def`` is irreducible and gets
  no equation lemmas), which is a TOOLING failure, not a refutation. And no
  witness can close the gap: the strongest statable refutation
  (``example (h : implementation_validateRootEntry "" ≠ Except.ok "") : ¬ …``)
  ELABORATES AGAINST THE FROZEN SOLUTION TOO (both builds exit 0), so it is
  vacuous by the gate's own definition — an opaque, irreducible impl symbol
  cannot be discriminated from gold's. There is therefore nothing shippable in
  this class, but the disposition is recorded as a HOLE (the spec does not
  constrain termination) rather than as a vacuous class (which would claim the
  battery is complete). The nagini sibling carries no divergence case either.

* PRECONDITION ADMISSIBILITY — **PORTED, contrary to the port's first reading.**
  It is true that the obligation's ``∀ (x : String)`` carries no hypothesis, so
  there is no guard that could be too strong. But that is not the whole of the
  lane on a TOTAL carrier: the analogue is the obligation being jointly
  UNSATISFIABLE at a concrete input — two clauses demanding incompatible results
  for the same entry — in which case ``correct_*`` is unprovable there for EVERY
  impl including gold, and the spec defends nothing at exactly the point the
  observation is made. That is expressible and is now tested by
  ``admiss-empty-entry-satisfiable``, which exhibits a concrete satisfying
  ``result`` at the F2P-shaped input BY EVALUATION, and at a non-empty entry, as
  ``have``s discharged before the frozen obligation is closed verbatim. It is not
  "a positive that merely mentions extra ground instances": each ``have`` is a
  proof obligation that fails if the corresponding sub-domain is empty.

* UNGROUNDED-ORACLE ECHO — **VACUOUS**, for the same reason the nagini sibling
  gives: both clauses are functions OF the binder (``x`` itself, and the check
  applied to the actual ``x``), never an opaque answer-key the implementation
  could echo to a wrong value. Returning the specified expression IS the
  specified behavior, which is why the reshaped-but-correct variants appear
  below as honest POSITIVE controls rather than as rivals.

* PARTIAL-DOMAIN / VALUE / ROUTING — **the whole battery**. Every ported nagini
  rival lands here, re-expressed against clauses C1 and C2.

A note on the OPAQUE carrier. ``checkExistingDir`` is ``opaque``, so for a
non-empty entry no literal input computes a result and ``decide`` is useless on
it. Four of the seven witnesses therefore CONDITION on the carrier rather than
computing it: each assumes, at one concrete entry, only that the check
distinguishes the two values the rival and the spec respectively name. That
hypothesis is exactly the sub-domain where the rival is wrong; it is a SINGLE
assumption about a single application pair, so it is jointly satisfiable (the
gate's consistency probe cannot derive ``False`` from it — checked by hand
first, and it cannot, since ``checkExistingDir`` is constrained by no axiom
whatsoever); and it makes a strictly stronger claim than any one literal could.
What stays FULLY transparent, and is what the other three witnesses exploit
directly, is clause C1: the empty entry's result is pinned to a literal
``Except.ok ""``, so a rival that reports an error there, or hands back a
different accepted value, is refuted with no assumption about the carrier at
all.

=========================================================================
BINDER + CLAUSE COVERAGE
=========================================================================

The single input binder ``x`` is VARIED across the seven reject witnesses, which
probe FIVE distinct input points spanning both halves of the spec's own case
split (and the admissibility positive adds ``""`` and ``"docs"`` as satisfiable
points, discharged by evaluation rather than by refutation):

  * ``x = ""`` — the empty entry, at ``weak-route-every-entry``,
    ``weak-reject-empty-entry`` and ``weak-empty-substitutes-value``. This is
    the point clause C1 lives at, and the one the F2P observation turns on.
  * ``x = "no/such/dir"`` — a multi-segment non-empty entry, at
    ``weak-routing-inverted``. Refuting the inverted routing REQUIRES a
    non-empty point: at ``x = ""`` the inverted rival happens to agree with the
    spec on nothing (it routes the empty entry to the check) but it is the
    NON-EMPTY clause it strands, so a battery whose every witness sat at ``""``
    would leave C2's routing direction untested.
  * ``x = "a"`` — a SINGLE-CHARACTER non-empty entry, at
    ``weak-wrong-emptiness-test``. That is the point where "keys on emptiness"
    becomes separable from "keys on some other size property": a rival whose
    short-circuit fires on length one instead of length zero agrees with the
    spec at ``""`` (both accept it verbatim) and at every entry of length two or
    more (both delegate), so holding this binder away from length one would let
    that whole degree of freedom go unprobed.
  * ``x = " "`` — a non-empty ALL-WHITESPACE entry, at
    ``weak-whitespace-emptiness-test``. The separating point for widening the
    short-circuit by CONTENT rather than by length: that rival is correct at
    ``""``, at ``"a"`` and at ``"docs"``, so no other probe point in this battery
    refutes it, and unlike the length-one near-miss it leaves clause C1 entirely
    intact — it is a C2-only failure.
  * ``x = "docs"`` — a plain non-empty entry, at
    ``weak-adjusts-delegated-entry``. Used to attack the ARGUMENT rather than
    the routing: the rival delegates the right entries but not the right value.

Both independent top-level clauses are attacked: C1 by three rivals (covering
both of its degrees of freedom — ok-vs-error, and which value), C2 by four
(covering both of ITS degrees of freedom — which entries are routed, widened
both by length and by content, and which argument is passed). No clause is
defended only by positives, and no binder is held at one value by every rival.
All three kind lanes are populated, so PRECOND-TOO-STRONG is tested and not
merely argued away.

=========================================================================
PORTED FROM NAGINI — and what was DROPPED, with reasons
=========================================================================

PORTED (nagini id -> this battery):
  pos-vae-reorder        -> ``pos-guard-inverted`` (same argument: the validator
                            written with the branches reordered, non-empty
                            guarded first and the empty case as fall-through,
                            is behaviorally identical and must verify).
  pos-abort-inline       -> ``pos-branchless-total-if`` (the nagini case inlines
                            an intermediate local; here the same "structurally
                            different, behaviorally identical" argument is made
                            by dropping the imperative ``do`` block for a single
                            branchless functional expression over a decidable
                            propositional test).
  pos-strict-reorder     -> ``pos-named-emptiness-flag`` (the nagini case
                            reshapes the second modeled function, which this
                            bundle does not model; its ARGUMENT — a reshaped
                            control-flow spelling of the same decision must
                            verify — is carried over as the surviving third
                            shape, naming the emptiness test as a local and
                            branching on it with an explicit ``else``, over the
                            carrier's ``String.isEmpty`` so the shape is not
                            definitionally equal to the frozen impl).
  admiss-empty-and-nonempty -> ``admiss-empty-entry-satisfiable``. The nagini
                            case shows its read-permission precondition accepts a
                            freshly built empty input. There is no precondition
                            here, so the total-carrier analogue is ported instead:
                            the obligation is SATISFIABLE at the F2P-shaped input
                            (and at a non-empty one), discharged by evaluation
                            before the frozen obligation is closed verbatim.
  weak-vae-prepatch-delegate-all -> ``weak-route-every-entry``. The documented
                            pre-patch program: every entry, empty included, is
                            routed to the existing-directory check.
  weak-vae-raise-on-empty        -> ``weak-reject-empty-entry``. The same
                            defect spelled explicitly as an error for the empty
                            entry.
  partial-vae-empty-returns-nonempty -> ``weak-empty-substitutes-value``.
                            Accepts the empty entry but hands back a different
                            value for it.
  weak-abort-inverted            -> ``weak-routing-inverted``. The nagini case
                            inverts the CONSUMING abort decision, a function
                            this bundle does not model; the inversion is
                            re-expressed at the surface that IS modeled — the
                            empty/non-empty routing itself is swapped, so the
                            empty entry is checked and the non-empty entry
                            waved through.
  weak-strict-accept-all         -> ``weak-adjusts-delegated-entry``. The
                            nagini case drops the existing-directory guard in
                            the second modeled function; here the same "the
                            existing-directory requirement is no longer applied
                            as written" attack is expressed on the surface this
                            bundle models — the check is still called, but on an
                            adjusted entry rather than the entry as given.

NEW (no nagini counterpart; added for binder coverage on this carrier):
  ``weak-wrong-emptiness-test`` — keys the short-circuit on the wrong size
  property of the entry. Nagini's carrier makes this the same edit as the
  prepatch rival; here it is a separable near-miss, and it is the only rival
  that probes a length-one entry.
  ``weak-whitespace-emptiness-test`` — widens the short-circuit by CONTENT
  instead of by length: correct at ``""``, at ``"a"`` and at ``"docs"``, wrong
  only on a non-empty all-whitespace entry. The only rival that leaves clause C1
  fully satisfied while breaking C2, and the only one whose witness has to route
  around a kernel-irreducible term (``" ".trim``) to reach the rival's branch.

DROPPED, with reasons (repeated in the submitted ``assessment``):
  frame-mut-vae-append, frame-mut-abort-append — VACUOUS on this carrier
  (referential transparency; no permission system to subvert). No substitute
  fabricated.
  weak-abort-const-false — DROPPED as a REJECT case because it has no
  counterpart on the modeled surface, not because it was hard to refute. It
  pins the CONSUMING decision (the caller's stop-or-continue choice) to a
  constant; that decision is outside this bundle's model, and the nearest
  in-model rewrite — pinning the validator's own result to a constant — is
  already covered, at the same input, by ``weak-reject-empty-entry`` and
  ``weak-empty-substitutes-value``. Shipping it too would be two rivals sharing
  one witness without a distinct sub-domain to claim, which the manifest
  contract forbids.
  AXIOM_TESTS (both soundness probes + the containment probe) — out of scope
  for this gate; the axiom lane is G-AX's job, and this bundle's G-AX is in any
  case a skip stub (the existing-directory check is an A-reference identical in
  spec and impl, so no property of it is consumed).

Every ``expect="verify"`` case below was built with ``scripts/lean_verify.sh``
and exits 0 with the frozen obligation STATEMENT byte-identical and its proof
genuinely re-closed for the new implementation shape — no case weakens the
obligation, adds a helper lemma, or reaches for an assumption. Every
``expect="reject"`` case's ``witness`` was built BOTH ways by hand: it
elaborates against the rival (exit 0) and FAILS against the frozen solution
(exit 1), and where the witness binds a hypothesis, the gate's consistency
probe was run and could NOT derive ``False`` from it.

=========================================================================
FORGERY CONTROL — why each gold-side exit code carries information
=========================================================================

"The witness fails on gold" is admissible evidence only if gold's exit code
TRACKS THE CLAIM. Every reject case here was additionally rebuilt with the
claim FLIPPED (the leading ``¬`` dropped, refutation step removed) and with the
post-``simp`` goal REVEALED (final step replaced by a deliberate type error) on
both sides. For six of the seven the revealed goals differ between gold and
rival, which is the whole point. The seventh is recorded first, because its
first witness FAILED that control and was re-authored for it:

  * ``weak-reject-empty-entry``: RE-AUTHORED after the control was measured
    rather than read. As first shipped the witness closed with ``simp [Id.run]``
    and gold's failure was ``unsolved goals ⊢ ¬pure (Except.ok "") = Except.ok
    ""``. That exit code carried NO information. The OPPOSITE claim — the same
    script with the leading ``¬`` dropped, i.e. the assertion that gold DOES
    satisfy the clause at ``""``, which is exactly what gold's own
    ``correct_validateRootEntry`` proves — fails on gold IDENTICALLY, ``unsolved
    goals ⊢ pure (Except.ok "") = Except.ok ""`` at exit 1, because ``simp
    [Id.run]`` never unwraps the ``Id``-monad ``pure`` that the impl's ``return``
    introduces and so decided the clause for gold in NEITHER direction. (Against
    the rival the same flipped claim does decide: ``unsolved goals ⊢ False``. The
    hollow half was gold's, which is the half the evidence rests on.) The
    re-authored witness applies C1 to a concrete result (``hspec.1 rfl``) and
    puts ``Pure.pure`` in the simp set. Re-measured, all four builds: witness vs
    rival exit 0 with no diagnostic at all; witness vs gold exit 1 at ``unsolved
    goals hspec : problem_spec_validateRootEntry "" (implementation_
    validateRootEntry "") ⊢ ¬True`` — that ``¬True`` IS the reduct of C1's own
    equation for gold, i.e. gold satisfies the clause the witness says it
    violates; and the OPPOSITE claim under the identical ``simp only`` set now
    VERIFIES against gold (``implementation_validateRootEntry "" = Except.ok ""``,
    exit 0, and likewise for the whole-spec form ``problem_spec_
    validateRootEntry "" (implementation_validateRootEntry "")``) while FAILING
    against the rival (``unsolved goals ⊢ False``). Gold's exit code is therefore
    a function of what is claimed, which is the property the first witness
    lacked.
  * ``weak-empty-substitutes-value``: the flipped claim ELABORATES against gold
    (exit 0) while the witness fails — the sharpest possible demonstration that
    gold's exit code is about the claim and nothing else.
  * the four conditioned witnesses: the revealed goal names the RIVAL's own
    result term against the rival (``¬pure (Except.ok "no/such/dir") =
    checkExistingDir "no/such/dir"``) and gold's against gold (``¬pure
    (checkExistingDir "no/such/dir") = checkExistingDir "no/such/dir"`` — a
    reflexive equation, i.e. gold SATISFIES the clause the rival strands). The
    ``Application type mismatch`` in those signatures is therefore a semantic
    refutation and not a tactic gap: the mismatch is precisely between what the
    hypothesis says and what gold's result reduces to.

None of the gold-side failures matches a stuck-reduction screen: no
``did not reduce to isTrue or isFalse``, no missing ``Decidable`` instance, no
``forIn Lean.Loop.mk`` unification. Every ``simp`` here ran to completion on
both sides.
"""

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9320"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body and the frozen proof body, verbatim. Every anchor below
# lies ENTIRELY inside the region it names and is unique in the file, so the
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

_IMPL = """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir x"""

_PROOF = """  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  · have hne : (x == "") = false := by
      simp [beq_eq_false_iff_ne, h]
    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, hne]
    rfl"""


def _impl(new_impl, new_proof=None):
    """A full Solution.lean with the impl region replaced (and, for a case that
    legitimately re-proves, the proof BODY replaced -- never its statement)."""
    src = _swap(_BASE, _IMPL, new_impl)
    if new_proof is not None:
        src = _swap(src, _PROOF, new_proof)
    return src


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROLS (soundness): structurally different, still CORRECT --
    # Each reproves the frozen obligation for its own shape. If any of these
    # cannot verify, the postcondition is too strong (SPEC-TOO-STRONG).
    {
        "id": "pos-guard-inverted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x ≠ "" then
      return checkExistingDir x
    return Except.ok x""",
            """  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => ?_, fun hx => absurd rfl hx⟩
    simp only [Id.run, ne_eq, not_true_eq_false, if_false]
    rfl
  · refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, ne_eq, h, not_false_eq_true, if_true]
    rfl""",
        ),
        "rationale": "the same decision written with the branches REORDERED: the "
        "non-empty case is guarded first (on the negated propositional test) and "
        "the empty case becomes the fall-through. Behaviorally identical, so both "
        "clauses C1 and C2 must still be dischargeable; the proof is re-closed "
        "for the new shape with the obligation statement byte-identical. If this "
        "cannot verify, the postcondition over-constrains the SPELLING of the "
        "split rather than its behavior => SPEC-TOO-STRONG.",
    },

    {
        "id": "pos-branchless-total-if",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  if x = "" then Except.ok x else checkExistingDir x""",
            """  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · simp [h]
  · simp [h]""",
        ),
        "rationale": "the imperative block collapsed to ONE branchless functional "
        "expression over the decidable propositional emptiness test -- no `Id.run`, "
        "no early `return`, no monadic `pure` wrapping the result. This is the "
        "cheapest correct implementation of the spec, and the shape furthest from "
        "the frozen one that is still behaviorally identical. Must verify; if not, "
        "the postcondition is pinned to the frozen impl's monadic form rather than "
        "to its input->output relation => SPEC-TOO-STRONG.",
    },

    {
        "id": "pos-named-emptiness-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    let entryIsEmpty : Bool := x.isEmpty
    if entryIsEmpty then
      return Except.ok x
    else
      return checkExistingDir x""",
            """  intro x
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  by_cases h : x = ""
  · subst h
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  · have hne : x.isEmpty = false := by
      rw [Bool.eq_false_iff]
      intro hi
      exact h ((String.isEmpty_iff x).mp hi)
    refine ⟨fun hx => absurd hx h, fun _ => ?_⟩
    simp only [Id.run, hne]
    rfl""",
        ),
        "rationale": "the emptiness test bound to a NAMED intermediate flag, "
        "branched on with an explicit `else`, AND expressed through a DIFFERENT "
        "emptiness predicate than the frozen impl's `== \"\"` -- the carrier's own "
        "`String.isEmpty`. The last part is what makes this positive load-bearing "
        "rather than decorative: a named flag over the SAME `x == \"\"` test is "
        "DEFINITIONALLY EQUAL to the frozen impl (the `let` zeta-reduces and the "
        "explicit `else` desugars to the same term -- machine-checked: `example "
        "(x : String) : namedFlagImpl x = frozenImpl x := rfl` elaborates), so the "
        "frozen proof script closes it BYTE-IDENTICALLY and it would probe nothing "
        "while passing honestly. Over `x.isEmpty` the two impls are NOT defeq: the "
        "frozen script's final `rfl` fails (`if x.isEmpty = true then pure "
        "(Except.ok x) else pure (checkExistingDir x)` is not definitionally equal "
        "to `checkExistingDir x`), so the non-empty branch must be RE-DERIVED -- "
        "here by carrying `x ≠ \"\"` through `String.isEmpty_iff` instead of "
        "through `beq_eq_false_iff_ne`. Must verify; if not, the postcondition "
        "constrains WHICH decidable emptiness predicate the split is spelled with "
        "rather than the input->output relation => SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY: the obligation is SATISFIABLE at the F2P-shaped input --
    # On a total carrier PRECOND-TOO-STRONG arrives not as a rejected guard but
    # as an obligation that is UNSATISFIABLE at a concrete input: no `result`
    # whatsoever makes both clauses hold there, so `correct_*` is vacuously
    # unprovable at that point and every impl is "wrong" there. This case
    # discharges the postcondition AT the F2P-shaped entry, by evaluation,
    # against a concrete result, BEFORE closing the frozen obligation verbatim.
    {
        "id": "admiss-empty-entry-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            _IMPL,
            """  -- ADMISSIBILITY, discharged before the frozen obligation is touched.
  -- (1) At the EMPTY entry -- the entry the F2P observation supplies -- the
  -- postcondition is satisfiable: `Except.ok ""` makes both clauses hold. The
  -- empty branch is evaluated here, not assumed: `rfl` closes `Except.ok "" =
  -- Except.ok ""` and the second clause is discharged from `"" ≠ ""` being
  -- absurd. If the two clauses jointly admitted NO result at this entry, this
  -- `have` could not be closed for any witness and the whole obligation would be
  -- vacuous exactly where the modeled behavior is observed.
  have adm_empty : problem_spec_validateRootEntry "" (Except.ok "") := by
    refine ⟨fun _ => rfl, fun hx => absurd rfl hx⟩
  -- (2) And at a NON-EMPTY entry, so neither half of the spec's own case split
  -- is empty in domain: the check's own result for that entry satisfies it.
  have adm_nonempty :
      problem_spec_validateRootEntry "docs" (checkExistingDir "docs") := by
    refine ⟨fun hx => absurd hx (by decide), fun _ => rfl⟩
  -- The frozen obligation, closed verbatim for the frozen impl.
""" + _PROOF,
        ),
        "rationale": "PRECOND-TOO-STRONG on this carrier. The obligation's "
        "`∀ (x : String)` carries no hypothesis, so there is no guard to be too "
        "strong -- but the total-carrier ANALOGUE is live and is what this case "
        "tests: a postcondition can be jointly UNSATISFIABLE at a concrete input "
        "(two clauses demanding incompatible results for the same entry), and "
        "then `correct_*` is unprovable there for EVERY impl, gold included, so "
        "the spec would defend nothing at exactly the point the observation is "
        "made. The two `have`s exhibit a concrete satisfying `result` at both "
        "halves of the spec's own case split -- `Except.ok \"\"` for the empty "
        "entry (the F2P-shaped input, discharged BY EVALUATION: `rfl` on the "
        "literal, and the non-empty clause from `\"\" ≠ \"\"` being absurd), and "
        "the check's own result for a non-empty entry -- and only then close the "
        "frozen obligation verbatim. If either `have` could not be closed, the "
        "domain would be empty where it matters and this case would fail while "
        "every uniqueness case still passed, which is why the lane is not "
        "redundant with them.",
    },

    # -- UNIQUENESS on clause C1: the empty entry ------------------------------
    # The pre-patch program: EVERY entry is routed to the existing-directory
    # check, so the empty entry is never accepted verbatim.
    {
        "id": "weak-route-every-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    return checkExistingDir x"""
        ),
        "refinement": "this is the PRE-PATCH program. An empty entry is handed to "
        "the existing-directory check, which does not accept it, so the entry is "
        "reported as a validation error and the prompt is re-issued rather than "
        "returning to the caller. The caller therefore never gets the chance to "
        "act on an empty entry, and the F2P test -- which supplies an empty entry "
        "and requires the flow to stop -- does NOT resolve. This is the observed "
        "bug itself, so a faithful patch shaped this way resolves nothing.",
        "rationale": "rejection comes from clause C1 (`x = \"\" → result = "
        "Except.ok x`): the spec pins the empty entry's result to the literal "
        "`Except.ok \"\"`, and this rival yields the existing-directory check's "
        "result for the empty entry instead. Since that check is opaque, the "
        "witness CONDITIONS on the carrier at `x = \"\"`, assuming only that the "
        "check does not itself accept the empty entry verbatim -- which is exactly "
        "the sub-domain where routing the empty entry is wrong.",
        "witness": """-- Refutation of `weak-route-every-entry` at x = "".
-- The rival routes the EMPTY entry to the existing-directory check. Stated by
-- conditioning on the carrier (the check is opaque, so no literal computes it):
-- whenever that check does not itself accept the empty entry verbatim, the
-- rival contradicts clause C1. ONE hypothesis about ONE application, and the
-- callee is constrained by no axiom, so it is satisfiable.
example (h : checkExistingDir "" ≠ Except.ok "") :
    ¬ problem_spec_validateRootEntry "" (implementation_validateRootEntry "") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run]
  exact h
""",
    },

    # Same defect spelled explicitly: the empty entry is reported as an error.
    {
        "id": "weak-reject-empty-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.error "entry rejected"
    return checkExistingDir x"""
        ),
        "refinement": "a faithful patch that explicitly reported a validation "
        "error for the empty entry reproduces the pre-patch observable exactly: "
        "the empty entry is rejected, the prompt is re-issued, and the caller is "
        "never handed an empty value to act on. The F2P test's required stop never "
        "happens, so it does NOT resolve.",
        "rationale": "rejection comes from clause C1, on its ok-vs-error degree of "
        "freedom: the spec requires `Except.ok \"\"` for the empty entry and this "
        "rival produces an `Except.error`. Fully TRANSPARENT -- the witness needs "
        "no assumption about the opaque check at all, because C1's right-hand side "
        "is a literal. Distinct from `weak-route-every-entry`, whose refutation "
        "holds only on the sub-domain where the check rejects the empty entry; "
        "this one is wrong unconditionally.",
        "witness": """-- Refutation of `weak-reject-empty-entry` at x = "".
-- Fully transparent: clause C1 pins the empty entry's result to the literal
-- `Except.ok ""`, and an `Except.error` is not it. No hypothesis, hence nothing
-- that could be inconsistent.
--
-- C1 is APPLIED to a concrete result here rather than left standing under the
-- monadic carrier: `hspec.1 rfl` instantiates the clause at the empty entry, and
-- `Pure.pure` is the step that unwraps the `Id`-monad `pure` the impl's `return`
-- introduces. That step is load-bearing for the EVIDENCE, not just for the
-- tactic: without it `simp` stalls on `pure (Except.ok "") = Except.ok ""` and
-- decides nothing on either side, so gold's exit code would not depend on what
-- is claimed. With it the claim is decided on both sides -- for the rival
-- `Except.error "entry rejected"` collapses against `Except.ok ""` and the goal
-- closes, while for gold the same script reduces C1's own equation to `True` and
-- the residual goal is `¬True`, i.e. gold SATISFIES exactly the clause this
-- witness claims is violated. Confirmed claim-dependent by the opposite claim
-- under the identical `simp only` set, which VERIFIES against gold (exit 0) and
-- fails against the rival.
example : ¬ problem_spec_validateRootEntry "" (implementation_validateRootEntry "") := by
  intro hspec
  refine absurd (hspec.1 rfl) ?_
  simp only [implementation_validateRootEntry, Id.run, Pure.pure, beq_self_eq_true,
             if_true, reduceCtorEq, not_false_eq_true]
""",
    },

    # Accepts the empty entry but substitutes a DIFFERENT accepted value.
    {
        "id": "weak-empty-substitutes-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok "."
    return checkExistingDir x"""
        ),
        "refinement": "a faithful patch that accepted the empty entry but "
        "substituted some other value for it hands the caller a NON-empty value. "
        "The caller's stop-or-continue decision keys on the returned value being "
        "empty, so it would continue with a substituted entry instead of stopping. "
        "The F2P test requires the flow to stop, so it does NOT resolve -- and "
        "this rival is strictly worse than the bug, since it also silently "
        "redirects the operation to an entry the operator never supplied.",
        "rationale": "rejection comes from clause C1, on its WHICH-VALUE degree of "
        "freedom: the spec accepts the empty entry VERBATIM (`result = Except.ok "
        "x`, i.e. `.ok \"\"`), not merely with SOME accepted value. This is the "
        "clause that would be missing if the spec had said only `∃ s, result = "
        ".ok s` for the empty entry. Fully TRANSPARENT; no carrier assumption. "
        "It gets its own witness rather than sharing `weak-reject-empty-entry`'s "
        "because it fails for a DIFFERENT reason at that input -- it satisfies the "
        "ok-vs-error half and violates only the value half.",
        "witness": """-- Refutation of `weak-empty-substitutes-value` at x = "".
-- Fully transparent: the rival ACCEPTS the empty entry (so it satisfies C1's
-- ok-vs-error half) but returns a value other than the entry itself, which
-- C1's `result = Except.ok x` forbids. No hypothesis.
example : ¬ problem_spec_validateRootEntry "" (implementation_validateRootEntry "") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run, pure, Except.ok.injEq]
""",
    },

    # -- UNIQUENESS on clause C2: the non-empty entry --------------------------
    # The routing is swapped: the empty entry is checked, non-empty entries are
    # waved through unvalidated.
    {
        "id": "weak-routing-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return checkExistingDir x
    return Except.ok x"""
        ),
        "refinement": "a faithful patch with the routing swapped waves EVERY "
        "non-empty entry through without applying the existing-directory "
        "requirement, while still rejecting the empty entry. It fails on both "
        "sides: the empty entry is still not accepted, so the F2P test's required "
        "stop still never happens and it does NOT resolve; and the "
        "existing-directory requirement the surrounding flows depend on is "
        "dropped, so a non-existent entry would be accepted and the flow would "
        "proceed into it -- breaking the PASS_TO_PASS flows that supply a real "
        "entry and expect it to be validated.",
        "rationale": "rejection comes from clause C2 (`x ≠ \"\" → result = "
        "checkExistingDir x`): a non-empty entry must yield the check's result for "
        "that entry, and this rival returns the entry itself accepted instead. The "
        "witness must sit at a NON-EMPTY input -- that is the clause the inversion "
        "strands -- so it probes a multi-segment entry and conditions on the "
        "carrier, assuming only that the check does not accept that entry "
        "verbatim.",
        "witness": """-- Refutation of `weak-routing-inverted` at x = "no/such/dir".
-- The rival waves non-empty entries through. Refuted on clause C2, which
-- REQUIRES a non-empty probe point. Conditioned on the carrier: whenever the
-- existing-directory check does not itself accept this entry verbatim, the
-- rival's accepted-as-given result differs from the check's. ONE hypothesis
-- about ONE application, and no axiom constrains the callee, so it holds of
-- some interpretation.
example (h : checkExistingDir "no/such/dir" ≠ Except.ok "no/such/dir") :
    ¬ problem_spec_validateRootEntry "no/such/dir"
        (implementation_validateRootEntry "no/such/dir") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run]
  exact fun hcontra => h hcontra.symm
""",
    },

    # NEAR-MISS: keys the short-circuit on the wrong size property.
    {
        "id": "weak-wrong-emptiness-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x.length == 1 then
      return Except.ok x
    return checkExistingDir x"""
        ),
        "refinement": "a faithful patch that short-circuited on the wrong size "
        "property of the entry does NOT resolve the F2P: the empty entry no longer "
        "matches the short-circuit, so it is handed to the existing-directory "
        "check, rejected, and the prompt re-issued exactly as before the fix -- "
        "the caller is still never given an empty value to act on. It "
        "additionally waves single-character entries through unvalidated, so it "
        "also weakens the existing-directory requirement the surrounding flows "
        "rely on.",
        "rationale": "rejection comes from clause C2, on its WHICH-ENTRIES-ARE-"
        "ROUTED degree of freedom: the split must key on the entry being EMPTY, "
        "not on some other size property. This is a genuine NEAR-MISS -- it agrees "
        "with the spec at every entry of length zero (both accept it verbatim, so "
        "clause C1 is satisfied!) and at every entry of length two or more (both "
        "delegate). It is wrong ONLY at length one, so it gets its own witness at "
        "that input; refuting it anywhere else is impossible, which is precisely "
        "why the battery needs a length-one probe point.",
        "witness": """-- Refutation of `weak-wrong-emptiness-test` at x = "a".
-- This rival's ONLY wrong sub-domain is entries of length one, so the witness
-- must sit there: at "" and at any longer entry it agrees with the spec.
-- Conditioned on the carrier -- whenever the existing-directory check does not
-- accept this single-character entry verbatim, the rival's short-circuit
-- contradicts clause C2. ONE hypothesis, ONE application.
example (h : checkExistingDir "a" ≠ Except.ok "a") :
    ¬ problem_spec_validateRootEntry "a" (implementation_validateRootEntry "a") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run]
  exact fun hcontra => h hcontra.symm
""",
    },

    # NEAR-MISS: keys the short-circuit on WHITESPACE-emptiness rather than on
    # emptiness. Agrees with the spec at `""` and at every entry with a
    # non-space character; wrong exactly on the all-whitespace entries.
    {
        "id": "weak-whitespace-emptiness-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x.trim == "" then
      return Except.ok x
    return checkExistingDir x"""
        ),
        "refinement": "a faithful patch that treated a whitespace-only entry as "
        "if the operator had declined DOES resolve the F2P (the truly empty entry "
        "still short-circuits and flows back accepted), which is what makes it a "
        "near-miss rather than a re-statement of the bug -- and it is still wrong: "
        "a whitespace-only entry is waved through without the existing-directory "
        "requirement, and the caller's stop-or-continue decision keys on the "
        "returned value being EMPTY, so a whitespace entry is handed back as a "
        "non-empty accepted value and the flow proceeds into an entry that names "
        "no directory. The PASS_TO_PASS flows that depend on every non-empty entry "
        "being validated therefore break.",
        "rationale": "rejection comes from clause C2, on its WHICH-ENTRIES-ARE-"
        "ROUTED degree of freedom, at a point NO other rival reaches. "
        "`weak-wrong-emptiness-test` widens the short-circuit by LENGTH (wrong at "
        "length one, and it also breaks C1's own input); this one widens it by "
        "CONTENT while leaving C1 fully satisfied -- it is correct at `\"\"`, "
        "correct at `\"a\"`, correct at `\"docs\"`, and wrong only where the entry "
        "is non-empty but all-whitespace. That is a distinct sub-domain and a "
        "fifth probe point for the single binder. The witness conditions on the "
        "carrier at `\" \"` and ALSO takes `\" \".trim = \"\"` as a hypothesis: "
        "that equation is TRUE but is not kernel-reducible in this Mathlib "
        "(`decide`, `decide +kernel`, `rfl`, and `simp [String.trim]` all fail on "
        "it -- `simp` leaves `\" \".toSubstring.trim.toString = \"\"`), so stating "
        "it as a hypothesis is what lets the refutation reach the rival's branch "
        "at all rather than stalling on an irreducible term. Both hypotheses are "
        "jointly satisfiable and the consistency probe confirms it.",
        "witness": """-- Refutation of `weak-whitespace-emptiness-test` at x = " ".
-- The rival short-circuits on WHITESPACE-emptiness, so a non-empty
-- all-whitespace entry is accepted verbatim instead of being routed to the
-- existing-directory check. Two hypotheses, both about single applications:
--   * `ht` supplies the trim fact. It is TRUE, but `" ".trim` is not
--     kernel-reducible here (`decide`/`decide +kernel`/`rfl` all get stuck on
--     the `instDecidableEqString` instance, and `simp [String.trim]` reduces
--     only to `" ".toSubstring.trim.toString = ""`), so without it the witness
--     cannot get past the rival's guard.
--   * `h` conditions on the opaque carrier, as the other non-empty witnesses do.
-- Neither constrains the other, so they hold jointly.
example (ht : " ".trim = "") (h : checkExistingDir " " ≠ Except.ok " ") :
    ¬ problem_spec_validateRootEntry " " (implementation_validateRootEntry " ") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run, ht]
  exact fun hcontra => h hcontra.symm
""",
    },

    # Attacks the ARGUMENT rather than the routing.
    {
        "id": "weak-adjusts-delegated-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            """def implementation_validateRootEntry (x : String) : Except String String :=
  Id.run do
    if x == "" then
      return Except.ok x
    return checkExistingDir (x ++ "/")"""
        ),
        "refinement": "a faithful patch that routed the right entries but adjusted "
        "each one before applying the existing-directory requirement changes the "
        "unchanged validator's contract: the requirement is no longer evaluated "
        "for the entry the operator supplied, and the value handed back to the "
        "caller is the adjusted one. The surrounding flows then build against an "
        "entry that differs from the one they were given, so the PASS_TO_PASS "
        "flows that supply a real entry and assert on the artifacts produced under "
        "it break. It also does not help the F2P observation, which turns entirely "
        "on the empty entry and never reaches this branch -- so it is pure "
        "collateral damage, resolving nothing.",
        "rationale": "rejection comes from clause C2, on its WHICH-ARGUMENT degree "
        "of freedom: the spec says the result equals the check applied to `x` "
        "ITSELF, not to some function of `x`. This is the clause that would be "
        "missing if the spec had merely said the result is `.ok`-or-`.error` "
        "according to the check on SOME entry. Refuting it does not require "
        "knowing what the check computes -- only that it distinguishes the "
        "adjusted entry from the entry as given, which is a single assumption "
        "about a single application pair.",
        "witness": """-- Refutation of `weak-adjusts-delegated-entry` at x = "docs".
-- Attacks the ARGUMENT, not the result: the rival delegates the right entries
-- but not the right value. Conditioned on the carrier -- whenever the
-- existing-directory check distinguishes the adjusted entry from the entry as
-- given, clause C2 is contradicted. ONE hypothesis, about ONE pair of
-- applications of an unconstrained callee, so it is satisfiable (nothing forces
-- the check to agree on the two).
example (h : checkExistingDir "docs/" ≠ checkExistingDir "docs") :
    ¬ problem_spec_validateRootEntry "docs"
        (implementation_validateRootEntry "docs") := by
  unfold problem_spec_validateRootEntry implementation_validateRootEntry
  simp [Id.run]
  exact h
""",
    },
]
