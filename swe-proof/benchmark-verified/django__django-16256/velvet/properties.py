"""properties.py — G-PBT falsification battery for django__django-16256 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives with a byte-identical header) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: it must ELABORATE against the rival and FAIL against the frozen
solution).

DEFENDED SURFACE (three contracted methods over one carrier):

  A parent owns a collection of related object identities, modeled as the
  ``mut`` carrier ``related : List Nat``; an object's identity is a ``Nat`` and
  "``o`` is owned by the parent" is ``o ∈ related``; settling a fresh object is
  ``related := related ++ [o]``. Each method is an async coroutine that awaits
  the relation-managing step and yields its result, so the observable content is
  exactly that synchronous effect.

  aCreate (mut related) (newObj) return (out : Nat)
    require newObj ∉ related
    ensures out = newObj                             (A1)
    ensures related = relatedOld ++ [newObj]         (A2)

  aGetOrCreate / aUpdateOrCreate (mut related) (preexists) (existingObj) (newObj)
      return (out : Nat × Bool)
    require preexists → existingObj ∈ related
    require ¬ preexists → newObj ∉ related
    ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)   (G1)
    ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj]) (G2)

  A1 pins the reported identity to the settled object; A2 pins the settle EFFECT
  (an exact append, so the multiplicity is fixed — a single new membership row,
  not a superset predicate). G1 is the LOCATE arm: when a matching object is
  already owned, its identity is reported with the not-produced flag and the
  collection is left EXACTLY as it was (no spurious membership change). G2 is the
  PRODUCE arm: when no matching object exists, a fresh one is settled and
  reported with the produced flag. aGetOrCreate and aUpdateOrCreate carry the
  same clause shape over the same carrier; both are attacked and defended
  independently.

  The carrier is FULLY TRANSPARENT (``List Nat`` with ``++``, ``∈``, tuple and
  ``Bool`` equality); the ``axioms`` and ``pure`` regions are empty — there is no
  opaque callee and no answer key to echo. So the whole reject lane is
  expressible by ``decide`` at concrete inputs.

CARRIER — witness form. The spec is a ``method`` CONTRACT, not a bare predicate,
so each witness reaches the post-image through Velvet's own tester machinery:
``extract_program_for`` → ``<name>Exec``, then ``prove_precondition_decidable_for``
/ ``prove_postcondition_decidable_for`` / ``derive_tester_for`` synthesize the
``Decidable`` instances and the boolean tester. ``<name>Tester args = false``
says the extracted program's (out, related) violates the method's postcondition
at that concrete input; the postcondition here equates ``Nat`` / ``List Nat`` /
``Nat × Bool`` values, all with decidable equality, so no assumption
(axiom/sorry/native_decide) is needed. Each witness is checked in a file whose
``prove_correct`` blocks have been stripped, so no tactic script can interfere,
and binds nothing at its ``example`` head (concrete literal inputs), so the
consistency probe is trivially satisfied.

ADVERSARIAL READ of the nagini classes:

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The class exists on
    nagini because a read-only input held at a fractional heap permission carries
    a permission an impl can overwrite. Velvet is referentially transparent:
    there is no heap, no aliasing, and no fractional-permission system to trip.
    ``related`` IS mutated (it is the settle carrier), so it is a full ``mut``
    parameter and no read-only-input rival exists. The soundness of the effect is
    instead pinned by the exact-append clauses A2/G2 and the unchanged-collection
    clause G1, which the uniqueness rivals attack directly. No substitute is
    fabricated (per the porting map, this class is legitimately dropped).

  * DIVERGENCE / NON-TERMINATION - CLOSED BY THE SEMANTICS in both its shapes, on
    a carrier setting that MOVED during this bundle's life. An earlier revision of
    this docstring recorded the whole class as a spec hole because the bundle set
    ``termination "partial"``, under which a diverging impl satisfies every
    ``ensures`` vacuously; that was accurate for the bytes it was written
    against. Solution.lean line 4 now reads
    ``set_option loom.semantics.termination "total"``, and the file opens
    ``TotalCorrectness``, which INVERTS the disposition for the whole class: a
    postcondition is now claimed of ALL runs, not only of terminating ones, and
    every loop owes a strict-decrease proof. Both shapes were re-measured with real
    builds against the current bytes, and both are REJECTED:

    (a) MEASURE-FREE divergence is REJECTED by the frozen spec, so it is not a
        hole. A ``while true do pure ()`` prefix spliced ahead of aCreate's
        frozen body fails with ``error: Decreasing annotations are required in
        total correctness semantics`` (exit 1); same for a variant that also
        returns a wrong identity, and for the ``let mut b := true; while b``
        spelling. It is nonetheless NOT SHIPPABLE as a reject case, for a
        structural reason rather than a proof difficulty: the termination error
        fires while elaborating the ``method`` body, UPSTREAM of anything
        appended, so the rival-side half of the witness contract (the witness
        must ELABORATE against the rival) is unreachable for EVERY claim.
        Measured on this bundle — against the diverging rival the tester witness,
        a bare ``example : 1 + 1 = 2 := by decide``, and a derive-only witness
        claiming ``True`` ALL exit 1 on the decreasing-annotation error, while
        the latter two exit 0 against the frozen solution. A ``witness_reference``
        cannot help: it substitutes the GOLD-side subject, never the rival-side
        one. So the gate could only ever record ``witness-unproven``
        (inconclusive, which fails the whole battery). Disposition:
        REJECTED-BY-SPEC, NOT-EXPRESSIBLE-AS-A-WITNESSED-CASE — neither a spec
        hole nor a battery gap.

    (b) Divergence CARRYING a measure is REJECTED TOO, on the measure's own
        descent goal, and this retracts a claim an earlier revision of this
        docstring escalated as a spec hole. That revision held the termination
        obligation to be discharged by the mere PRESENCE of a ``decreasing``
        annotation, so that an impl whose loop cannot exit verifies while
        returning a wrong answer. Re-measured on this bundle: an aCreate whose
        body is ``let mut i := 0; while 0 < 1 decreasing i do i := i + 1`` and
        then ``return newObj + 1`` is REJECTED, exit 1, with
        ``unsolved goals case «decreasing_1: i» ... ⊢ i + 1 < i``. The strict
        decrease is demanded and is unprovable for an increasing counter. The
        same holds with the fuller clause block (``invariant``/``done_with``
        present) and with a CONSTANT measure, which leaves ``⊢ 0 < 0``. So the
        value clause is never reached, let alone satisfied on an unreachable
        exit, and there is no hole to escalate.

        The mechanism is Loom's, and it is worth stating because the earlier
        claim came from reading only the ``set_option``: that option handler
        ITSELF opens the ``TotalCorrectness`` scope
        (``Loom/MonadAlgebras/WP/Options.lean``), the frozen file opens the same
        scope explicitly, and
        ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and
        emits ``⌜measure b' < measure b⌝``. Only the ``PartialCorrectness`` twin
        takes a measure and discards it. No ``spec_holes`` entry is filed for
        this class, and nothing ships for it: shape (a) cannot carry a witness,
        and shape (b) is an ordinary spec rejection whose attribution is the
        termination obligation rather than any postcondition at a point.

  * UNGROUNDED-ORACLE ECHO — N/A. Every clause is a total relation of the input
    binders (``related`` / ``newObj`` / ``preexists`` / ``existingObj`` via
    ``++`` / ``∈`` / tuple equality); there is no opaque answer key a wrong impl
    could echo.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject surface: the
    pre-patch no-settle shape (delivers the object but never links it), the
    over-settle shape (links it more than once), the locate-branch spurious
    settle (links an already-owned object), the flipped produced/located flag,
    and a wrong reported identity.

WITNESS PLACEMENT / BINDER COVERAGE. The three obligations are each DEFENDED (a
structurally-different correct reshape verifies) and ATTACKED (>=1 reject). The
reject witnesses move every INPUT binder:
  * aCreate: ``related`` ∈ {[], [3]}, ``newObj`` ∈ {5, 7}; A1 attacked by the
    wrong-identity rival, A2 by the no-settle and double-settle rivals.
  * aGetOrCreate: ``preexists`` ∈ {false, true} (both branches), ``existingObj``
    ∈ {0, 7}, ``newObj`` ∈ {5, 3}, ``related`` ∈ {[], [7]}; G2 attacked by the
    no-settle rival, G1 by the locate-branch settle rival, and both flag halves
    by the flipped-flag rival.
  * aUpdateOrCreate: ``preexists`` ∈ {false, true} (both branches),
    ``existingObj`` ∈ {0, 9, 2}, ``newObj`` ∈ {5, 4, 7, 8}, ``related`` ∈ {[],
    [9], [2]}; G2 by the no-settle rival, G1's MEMBERSHIP half by the
    locate-branch settle rival, G1's IDENTITY half by the locate-wrong-identity
    rival, and both flag halves by the flipped-flag rival.
Every clause of every obligation therefore carries at least one rival, and each
of the two flag halves and each of G1's two halves (identity, membership) is
attacked separately rather than folded into one rival.
Confirmed empirically with scripts/lean_verify.sh across all 14 SPEC cases: every
positive verifies, and every reject witness elaborates against its rival and
FAILS against the frozen solution (the required discrimination), with the failure
being a `decide`-level refutation of the claim rather than a missing identifier
or an unfolding failure.
"""
from pathlib import Path

INSTANCE = "django__django-16256"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each lies ENTIRELY inside one method's
# `-- impl-start`/`-- impl-end` block (so a _swap touches only that impl and
# `same_spec` holds). The two locate-or-produce methods have BYTE-IDENTICAL
# bodies, so the bare body is NOT unique; each is anchored together with the
# unique text that FOLLOWS its `-- impl-end` (the next method's docstring, or the
# `prove_correct` block) so the anchor occurs exactly once (asserted by _swap).
# ---------------------------------------------------------------------------

_ACREATE = (
    "    -- impl-start\n"
    "    related := related ++ [newObj]\n"
    "    return newObj\n"
    "    -- impl-end")

_AGETORCREATE = (
    "    -- impl-start\n"
    "    if preexists then\n"
    "      return (existingObj, false)\n"
    "    else\n"
    "      related := related ++ [newObj]\n"
    "      return (newObj, true)\n"
    "    -- impl-end\n"
    "\n"
    "/- Return an object owned by the parent — refreshing")

_AUPDATEORCREATE = (
    "    -- impl-start\n"
    "    if preexists then\n"
    "      return (existingObj, false)\n"
    "    else\n"
    "      related := related ++ [newObj]\n"
    "      return (newObj, true)\n"
    "    -- impl-end\n"
    "\n"
    "prove_correct aCreate by")

# aCreate proof block (unique: the sibling proofs name aGetOrCreate /
# aUpdateOrCreate). Used only by the admissibility case, whose in-region assert
# adds a decidable goal the frozen `loom_solve` does not discharge alone.
_ACREATE_PROOF = "prove_correct aCreate by\n  loom_solve"

assert _BASE.count(_ACREATE) == 1, "aCreate impl region drifted"
assert _BASE.count(_AGETORCREATE) == 1, "aGetOrCreate impl region drifted"
assert _BASE.count(_AUPDATEORCREATE) == 1, "aUpdateOrCreate impl region drifted"
assert _BASE.count(_ACREATE_PROOF) == 1, "aCreate proof region drifted"


def _witness(name, args):
    """A tester witness: extract the program, synthesize the decidability
    instances and boolean tester for `name`, then assert its post-image is
    violated at the concrete `args` (`<name>Tester args = false`). Checked in a
    file whose `prove_correct` blocks are stripped; binds nothing at its head."""
    return (
        f"extract_program_for {name}\n"
        f"prove_precondition_decidable_for {name}\n"
        f"prove_postcondition_decidable_for {name}\n"
        f"derive_tester_for {name}\n\n"
        f"example : {name}Tester {args} = false := by decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — one structurally-different but CORRECT
    # reshape per obligation. Each keeps the method's `ensures` and the frozen
    # `prove_correct <name> by loom_solve` obligation verbatim; only the impl
    # region changes. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on that method's SHAPE.
    # =====================================================================
    {
        "id": "pos-acreate-let-bind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the reported identity to a local, settle it, return it.
        # Observationally the frozen settle-then-report; a distinct executable
        # surface that still discharges A1/A2 under `loom_solve`.
        "module": _swap(
            _BASE, _ACREATE,
            "    -- impl-start\n"
            "    let r := newObj\n"
            "    related := related ++ [r]\n"
            "    return r\n"
            "    -- impl-end"),
        "rationale": (
            "binding the reported identity to a local and settling it computes "
            "the identical (out, related) as the frozen impl, so A1 (out=newObj) "
            "and A2 (related=relatedOld++[newObj]) still discharge under the "
            "frozen `loom_solve`; a correct reshape must verify, else "
            "SPEC-TOO-STRONG on aCreate's shape."),
    },
    {
        "id": "pos-agetorcreate-negate-swap",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: negate the branch condition and swap the arms — produce on
        # `¬ preexists`, locate otherwise. The identical decision on both arms.
        "module": _swap(
            _BASE, _AGETORCREATE,
            "    -- impl-start\n"
            "    if ¬ preexists then\n"
            "      related := related ++ [newObj]\n"
            "      return (newObj, true)\n"
            "    else\n"
            "      return (existingObj, false)\n"
            "    -- impl-end\n"
            "\n"
            "/- Return an object owned by the parent — refreshing"),
        "rationale": (
            "negating the branch condition and swapping the arms settles-and-"
            "reports on the produce arm and leaves the collection on the locate "
            "arm — the identical transition on both — so G1 and G2 still "
            "discharge under the frozen `loom_solve`; a correct reshape must "
            "verify, else SPEC-TOO-STRONG on aGetOrCreate's arm order."),
    },
    {
        "id": "pos-aupdateorcreate-negate-swap",
        "kind": "soundness",
        "expect": "verify",
        # Same reshape for the third obligation, so it too is defended by a
        # structurally-different correct impl rather than only attacked.
        "module": _swap(
            _BASE, _AUPDATEORCREATE,
            "    -- impl-start\n"
            "    if ¬ preexists then\n"
            "      related := related ++ [newObj]\n"
            "      return (newObj, true)\n"
            "    else\n"
            "      return (existingObj, false)\n"
            "    -- impl-end\n"
            "\n"
            "prove_correct aCreate by"),
        "rationale": (
            "the negate-and-swap reshape settles-and-reports on the produce arm "
            "and leaves the collection on the locate arm — the identical "
            "transition — so G1 and G2 still discharge for aUpdateOrCreate under "
            "the frozen `loom_solve`; a correct reshape must verify, else "
            "SPEC-TOO-STRONG on aUpdateOrCreate's arm order."),
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition (`newObj ∉ related`) is met by every
    # F2P-shaped input (a freshly-produced identity is not yet owned), so the
    # usual "a normal input satisfies the precondition" probe is trivial.
    # Re-aimed at the residual total-domain risk: that the post-image is
    # UNSATISFIABLE / degenerate at the F2P corner. The in-region assert pins the
    # modeled settle effect, the freshness precondition, and the OBSERVABILITY of
    # the settle at the F2P-shaped starting shape (an EMPTY collection, which is
    # exactly setUp's initial state) AND at a nonempty one; the surrounding impl
    # is kept verbatim so A1/A2 still discharge.
    #
    # The assert is LIVE, and this audit measured HOW live rather than asserting
    # it. Each conjunct was falsified in turn and the build FAILED each time
    # (exit 1, ``Tactic `decide` proved that the proposition ... is false``):
    # a wrong append RHS, a wrong element order at the nonempty point, and a
    # false freshness claim. What the previous revision's assert did NOT
    # establish is the ``≠`` conjunct's job: a bare tautology (``(5 : Nat) = 5``)
    # in its place ALSO verifies (measured, exit 0), so "the assert discharges"
    # on its own only witnesses that `loom_solve <;> decide` closes a true
    # decidable literal goal. The ``++ [5] ≠ []`` conjuncts are what make the
    # claim about the CARRIER — they say the modeled settle actually CHANGES the
    # collection, i.e. the settle effect is observable and the post-image is
    # non-degenerate, which a tautology cannot say.
    # =====================================================================
    {
        "id": "admiss-acreate-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _ACREATE,
                "    -- impl-start\n"
                "    assert (with_name_prefix `assert\n"
                "      ((([] : List Nat) ++ [5] = [5] ∧ (5 : Nat) ∉ ([] : List Nat)\n"
                "         ∧ ([] : List Nat) ++ [5] ≠ ([] : List Nat))\n"
                "       ∧ ([3] ++ [5] = [3, 5] ∧ (5 : Nat) ∉ [3]\n"
                "         ∧ ([3] : List Nat) ++ [5] ≠ ([3] : List Nat))))\n"
                "    related := related ++ [newObj]\n"
                "    return newObj\n"
                "    -- impl-end"),
            _ACREATE_PROOF,
            "prove_correct aCreate by\n  loom_solve <;> decide"),
        "rationale": (
            "the post-image is satisfiable, OBSERVABLE and non-degenerate at the "
            "F2P-shaped corner AND at a nonempty collection: settling a fresh "
            "identity into an EMPTY collection extends it to exactly that "
            "one-element collection (A2), the freshness precondition holds there "
            "(5 ∉ []), and the settle genuinely CHANGES the collection "
            "([] ++ [5] ≠ []) — so the modeled effect is not a no-op on a carrier "
            "that collapses it. The same three claims are pinned at `related = "
            "[3]`, where the exact-append also fixes the ORDER ([3,5], not "
            "[5,3]). The in-region assert must discharge (else the modeled settle "
            "is degenerate / PRECOND-TOO-STRONG at a normal input); the impl and "
            "obligation are verbatim so A1/A2 still discharge too. Every conjunct "
            "is load-bearing: falsifying any one of them fails the build."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-acreate-no-settle",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch defect: deliver the produced object but never settle it
        # into THIS parent's collection.
        "module": _swap(
            _BASE, _ACREATE,
            "    -- impl-start\n"
            "    return newObj\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-patch shape: the async creator delivers the produced "
            "object but delegates to a step that does NOT link it into the "
            "owning parent's collection, so a newly-produced object is not owned "
            "by the parent. Its faithful real counterpart is the bug the change "
            "fixes: the F2P tests create an object through the parent and then "
            "assert it is reachable via the parent (the collection count grows to "
            "one / the object is fetchable), which stays RED when nothing was "
            "linked. It would NOT resolve."),
        "rationale": (
            "REJECT from A2 (related = relatedOld ++ [newObj]): returning the "
            "identity without appending leaves `related` = relatedOld, so the "
            "post-image demands one more member than the impl produces. Refuted "
            "at `related = [], newObj = 5`, where the frozen post demands `[5]` "
            "but the impl leaves `[]`."),
        "witness": _witness("aCreate", "[] 5"),
    },
    {
        "id": "weak-acreate-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Value rival: settle correctly but report a different identity than the
        # one produced. Attacks A1 while A2 still holds.
        "module": _swap(
            _BASE, _ACREATE,
            "    -- impl-start\n"
            "    related := related ++ [newObj]\n"
            "    return newObj + 1\n"
            "    -- impl-end"),
        "refinement": (
            "a counterpart that links the object but reports a DIFFERENT identity "
            "than the one produced hands the caller a handle that does not match "
            "the settled object. The F2P tests bind the returned object and then "
            "assert on it (its field / that it equals the parent-linked one), so "
            "a mismatched identity stays RED. It would NOT resolve."),
        "rationale": (
            "REJECT from A1 (out = newObj): the impl reports `newObj + 1` where "
            "the post-image demands `newObj`, on every input. A2 still holds (the "
            "correct object was settled), so the rejection is attributable solely "
            "to the reported-identity clause. Refuted at `related = [3], "
            "newObj = 7`, where the impl reports `8` but the post demands `7` "
            "(and varies `related`/`newObj` off the no-settle witness's point)."),
        "witness": _witness("aCreate", "[3] 7"),
    },
    {
        "id": "weak-acreate-double-settle",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-settle: link the produced object TWICE, so it appears twice in the
        # parent's collection. Attacks the exact-append multiplicity of A2.
        "module": _swap(
            _BASE, _ACREATE,
            "    -- impl-start\n"
            "    related := related ++ [newObj]\n"
            "    related := related ++ [newObj]\n"
            "    return newObj\n"
            "    -- impl-end"),
        "refinement": (
            "a counterpart that links the produced object twice (a duplicate "
            "membership row) makes it appear twice in the parent's collection. "
            "The F2P tests assert exactly one member after one create (the count "
            "is one / a unique fetch succeeds), which fails when the object was "
            "double-linked (count two / an ambiguous fetch). It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from A2 as an EXACT equality (related = relatedOld ++ "
            "[newObj], not a `newObj ∈ related` superset predicate): a second "
            "append yields relatedOld ++ [newObj, newObj], which is not "
            "relatedOld ++ [newObj]. This is why the clause pins the multiplicity. "
            "Refuted at `related = [3], newObj = 5`, where the post demands `[3, "
            "5]` but the impl produces `[3, 5, 5]`."),
        "witness": _witness("aCreate", "[3] 5"),
    },
    {
        "id": "weak-agetorcreate-no-settle",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch defect for the locate-or-produce family: deliver the correct
        # (identity, produced-flag) but never link a NEWLY-produced object.
        "module": _swap(
            _BASE, _AGETORCREATE,
            "    -- impl-start\n"
            "    if preexists then\n"
            "      return (existingObj, false)\n"
            "    else\n"
            "      return (newObj, true)\n"
            "    -- impl-end\n"
            "\n"
            "/- Return an object owned by the parent — refreshing"),
        "refinement": (
            "the pre-patch shape for locate-or-produce: on the produce branch it "
            "reports the correct (identity, produced) tuple but never links the "
            "new object to the parent. The F2P tests create-or-get a new object "
            "and then assert the parent's collection count is one, which holds "
            "only if the parent's own linking step ran. It would NOT resolve."),
        "rationale": (
            "REJECT from G2 (¬ preexists → related = relatedOld ++ [newObj]): on "
            "the produce branch no append occurs, so `related` stays relatedOld "
            "where the post demands one more member. The value halves (identity, "
            "flag) still hold, so the rejection is attributable solely to the "
            "missing link. Refuted at `related = [], preexists = false, "
            "existingObj = 0, newObj = 5`."),
        "witness": _witness("aGetOrCreate", "[] false 0 5"),
    },
    {
        "id": "weak-agetorcreate-settle-on-locate",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: link unconditionally, so it also links on the LOCATE
        # branch where the object is already owned. Correct on produce; wrong on
        # locate (the collection must be left unchanged).
        "module": _swap(
            _BASE, _AGETORCREATE,
            "    -- impl-start\n"
            "    related := related ++ [newObj]\n"
            "    if preexists then\n"
            "      return (existingObj, false)\n"
            "    else\n"
            "      return (newObj, true)\n"
            "    -- impl-end\n"
            "\n"
            "/- Return an object owned by the parent — refreshing"),
        "refinement": (
            "a counterpart that links unconditionally settles even when a "
            "matching object was already owned (the located branch), "
            "double-counting it. The F2P tests get-or-create an EXISTING object "
            "and assert the count does NOT grow, which fails when a located "
            "object is spuriously linked. It would NOT resolve."),
        "rationale": (
            "REJECT from G1 (preexists → related = relatedOld): when preexists is "
            "true the unconditional append makes `related` = relatedOld ++ "
            "[newObj] ≠ relatedOld, violating the unchanged-collection clause. "
            "Refuted at `related = [7], preexists = true, existingObj = 7, "
            "newObj = 5` (the LOCATE sub-domain, the branch the no-settle rival "
            "leaves untouched)."),
        "witness": _witness("aGetOrCreate", "[7] true 7 5"),
    },
    {
        "id": "weak-agetorcreate-flip-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Value rival: the link effect is correct but the produced/located flag
        # is INVERTED on both branches.
        "module": _swap(
            _BASE, _AGETORCREATE,
            "    -- impl-start\n"
            "    if preexists then\n"
            "      return (existingObj, true)\n"
            "    else\n"
            "      related := related ++ [newObj]\n"
            "      return (newObj, false)\n"
            "    -- impl-end\n"
            "\n"
            "/- Return an object owned by the parent — refreshing"),
        "refinement": (
            "a counterpart with the link effect correct but the produced/located "
            "flag inverted reports produced on a located object and vice-versa. "
            "The F2P tests assert the exact flag (produced on the first call, "
            "located on the repeat call), so an inverted flag stays RED. It would "
            "NOT resolve."),
        "rationale": (
            "REJECT from the flag half of G1/G2: on the produce branch the impl "
            "reports the located flag where G2 demands produced (and dually on "
            "locate), on every input. The membership halves still hold, isolating "
            "the flag clause. Refuted at `related = [], preexists = false, "
            "existingObj = 0, newObj = 3` (a produce point off the other "
            "witnesses' points), where the impl reports the located flag but the "
            "post demands produced."),
        "witness": _witness("aGetOrCreate", "[] false 0 3"),
    },
    {
        "id": "weak-aupdateorcreate-no-settle",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch defect on the THIRD obligation: report the correct tuple but
        # never link a newly-produced object.
        "module": _swap(
            _BASE, _AUPDATEORCREATE,
            "    -- impl-start\n"
            "    if preexists then\n"
            "      return (existingObj, false)\n"
            "    else\n"
            "      return (newObj, true)\n"
            "    -- impl-end\n"
            "\n"
            "prove_correct aCreate by"),
        "refinement": (
            "the pre-patch shape for the update-or-produce family: on the produce "
            "branch it reports the correct tuple but never links the new object. "
            "The F2P tests update-or-create a new object and assert the parent's "
            "collection count is one, which holds only if the parent's own "
            "linking step ran. It would NOT resolve."),
        "rationale": (
            "REJECT from G2 for aUpdateOrCreate (¬ preexists → related = "
            "relatedOld ++ [newObj]): the produce branch omits the append, so "
            "`related` stays relatedOld where the post demands one more member. "
            "Refuted at `related = [], preexists = false, existingObj = 0, "
            "newObj = 5`."),
        "witness": _witness("aUpdateOrCreate", "[] false 0 5"),
    },
    {
        "id": "weak-aupdateorcreate-settle-on-locate",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on the third obligation: link unconditionally, so it
        # also links on the locate branch where the object is already owned.
        "module": _swap(
            _BASE, _AUPDATEORCREATE,
            "    -- impl-start\n"
            "    related := related ++ [newObj]\n"
            "    if preexists then\n"
            "      return (existingObj, false)\n"
            "    else\n"
            "      return (newObj, true)\n"
            "    -- impl-end\n"
            "\n"
            "prove_correct aCreate by"),
        "refinement": (
            "a counterpart that links unconditionally settles even when a "
            "matching object was already owned (the refreshed branch), "
            "double-counting it. The F2P tests update-or-create an EXISTING "
            "object and assert the count does NOT grow, which fails when a "
            "refreshed object is spuriously linked. It would NOT resolve."),
        "rationale": (
            "REJECT from G1 for aUpdateOrCreate (preexists → related = "
            "relatedOld): when preexists is true the unconditional append makes "
            "`related` ≠ relatedOld. Refuted at `related = [9], preexists = true, "
            "existingObj = 9, newObj = 4` (the LOCATE sub-domain, at a distinct "
            "input point from the no-settle witness)."),
        "witness": _witness("aUpdateOrCreate", "[9] true 9 4"),
    },
    {
        "id": "weak-aupdateorcreate-flip-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Value rival on the THIRD obligation. Added by the audit: the flag half
        # of G1/G2 was attacked only on aGetOrCreate, so aUpdateOrCreate's flag
        # clause was defended by no rival at all even though it is a separate
        # `prove_correct` obligation.
        "module": _swap(
            _BASE, _AUPDATEORCREATE,
            "    -- impl-start\n"
            "    if preexists then\n"
            "      return (existingObj, true)\n"
            "    else\n"
            "      related := related ++ [newObj]\n"
            "      return (newObj, false)\n"
            "    -- impl-end\n"
            "\n"
            "prove_correct aCreate by"),
        "refinement": (
            "a counterpart with the link effect correct but the produced/located "
            "flag inverted reports produced on a refreshed object and vice-versa. "
            "The F2P tests assert the exact flag (produced on the first call, "
            "located on the repeat call that refreshes), so an inverted flag stays "
            "RED. It would NOT resolve."),
        "rationale": (
            "REJECT from the flag half of G1/G2 for aUpdateOrCreate: on the "
            "produce branch the impl reports the located flag where G2 demands "
            "produced (and dually on refresh), on every input. The membership "
            "halves still hold, isolating the flag clause. Refuted at `related = "
            "[], preexists = false, existingObj = 0, newObj = 7` (a produce point "
            "distinct from every other witness's point)."),
        "witness": _witness("aUpdateOrCreate", "[] false 0 7"),
    },
    {
        "id": "weak-aupdateorcreate-locate-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Value rival: on the LOCATE/refresh arm report the freshly-produced
        # identity instead of the already-owned one. Added by the audit: the
        # identity half of G1 (as opposed to its membership half) was previously
        # attacked on neither locate-or-produce obligation.
        "module": _swap(
            _BASE, _AUPDATEORCREATE,
            "    -- impl-start\n"
            "    if preexists then\n"
            "      return (newObj, false)\n"
            "    else\n"
            "      related := related ++ [newObj]\n"
            "      return (newObj, true)\n"
            "    -- impl-end\n"
            "\n"
            "prove_correct aCreate by"),
        "refinement": (
            "a counterpart that, on the branch where a matching object is already "
            "owned, hands back the identity it would have produced instead of the "
            "one it actually found. The collection is left correctly unchanged, so "
            "a count assertion still passes, but the caller receives a handle to "
            "an object the parent does not own. The F2P tests bind the returned "
            "object and assert on it (that it equals the parent-linked one), so a "
            "mismatched identity on the refresh arm stays RED. It would NOT "
            "resolve."),
        "rationale": (
            "REJECT from the IDENTITY half of G1 (preexists → out = (existingObj, "
            "false)): the impl reports `newObj` where the post demands "
            "`existingObj`. The membership half of G1 (related = relatedOld) still "
            "holds — no append occurs on that arm — so the rejection is "
            "attributable solely to the reported identity, a clause the "
            "settle-on-locate rival (which attacks G1's membership half) leaves "
            "untested. Refuted at `related = [2], preexists = true, existingObj = "
            "2, newObj = 8`, where the impl reports `8` but the post demands `2`."),
        "witness": _witness("aUpdateOrCreate", "[2] true 2 8"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness rivals including 1 divergence rival)
# plus 0 AXIOM_TESTS. The sibling contracts SIX functions (three "immediate"
# forms and three "deferred" delegators); this bundle narrows to the purely
# functional core — the three distinct operation SHAPES — modeling each as one
# `method` over the carrier `related : List Nat`. The deferred/immediate
# distinction collapses (the async bridge is observationally the sync effect,
# mapping.md §2/§3), so the sibling's deferred-vs-immediate split becomes one
# method per shape; the membership/flag/value surface carries across intact.
#
#   sibling case (nagini)              -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder-goc            -> pos-agetorcreate-negate-swap   RE-SHAPED
#                                         (+ pos-acreate-let-bind,
#                                            pos-aupdateorcreate-negate-swap ADDED)
#   admiss-acreate-fresh-accessor      -> admiss-acreate-grounded        RE-AIMED
#   weak-acreate-no-attach             -> weak-acreate-no-settle         PORTED
#   weak-aget-or-create-no-attach      -> weak-agetorcreate-no-settle    PORTED
#   weak-goc-always-attach-located     -> weak-agetorcreate-settle-on-locate PORTED
#   weak-goc-flip-created-flag         -> weak-agetorcreate-flip-flag    PORTED
#   weak-acreate-double-attach         -> weak-acreate-double-settle     PORTED
#   weak-acreate-diverge               -> (none)                         NOT EXPRESSIBLE
#                                         (rejected by the spec, but no witness
#                                          shape is reachable — see below)
#   (no sibling counterpart)           -> weak-acreate-wrong-identity    ADDED
#   (no sibling counterpart)           -> weak-aupdateorcreate-no-settle ADDED
#   (no sibling counterpart)           -> weak-aupdateorcreate-settle-on-locate ADDED
#   (no sibling counterpart)           -> weak-aupdateorcreate-flip-flag ADDED
#   (no sibling counterpart)           -> weak-aupdateorcreate-locate-wrong-identity ADDED
#
# 14 SPEC cases: 5 ported, 1 re-shaped, 1 re-aimed, 1 not-expressible (divergence);
# 2 positives + 5 uniqueness rivals ADDED.
#
# RE-SHAPED (pos-control-reorder-goc -> pos-agetorcreate-negate-swap): the
#   sibling reorders get_or_create so the produce branch is taken first. The
#   equivalent structural reshape here is the negate-and-swap on the branch
#   condition. ADDED pos-acreate-let-bind and pos-aupdateorcreate-negate-swap so
#   ALL THREE obligations are defended by a structurally-different correct impl
#   (the sibling defends only one of its six functions with a positive; the
#   coverage invariant here is per-obligation).
# RE-AIMED (admiss-acreate-fresh-accessor -> admiss-acreate-grounded): the
#   sibling builds a fresh F2P-shaped accessor and asserts create's Requires
#   (list_pred) holds — a permission-precondition probe. This method's
#   precondition (`newObj ∉ related`) is met by every F2P-shaped input, so the
#   "admits a normal input" reading is trivial. The case is re-aimed at proving
#   the post-image is satisfiable and NON-degenerate at the F2P corner (settling
#   a fresh identity into an empty collection), via a live in-region assert; the
#   impl and obligation are kept verbatim.
# NOT EXPRESSIBLE (weak-acreate-diverge): the sibling's divergence rival is
#   rejected by Nagini's MustTerminate obligation. This bundle NOW sets
#   `loom.semantics.termination "total"` (it previously set "partial", under which
#   this class WAS a live hole — see the DIVERGENCE bullet in the module docstring
#   for the measurements under the current setting), so a measure-free diverging impl is
#   likewise REJECTED here (measured: three diverging shapes all fail with
#   "Decreasing annotations are required in total correctness semantics"). So the
#   class is NOT a hole at the measure-free shape. It is nonetheless not
#   shippable as a reject case: the termination error fires while elaborating the
#   `method` body, UPSTREAM of anything the harness appends, so the rival-side
#   half of the witness contract is unreachable for EVERY claim (measured: the
#   real tester witness, a bare `example : 1 + 1 = 2 := by decide`, and a
#   derive-only `example : True := trivial` ALL exit 1 against the diverging
#   rival, while the latter two exit 0 against the frozen impl). The gate could
#   only ever record `witness-unproven`. Disposition: REJECTED-BY-SPEC,
#   NOT-EXPRESSIBLE-AS-A-WITNESSED-CASE — not a silent gap and not a hole.
#
#   The OTHER shape in this class is rejected too, which RETRACTS an escalation
#   this entry used to carry: divergence that CARRIES a measure. The entry held
#   that under "total" the termination obligation is discharged by the mere
#   PRESENCE of a `decreasing` annotation, so that `let mut i : Nat := 0;
#   while 0 < 1 decreasing i do i := i + 1` followed by `return newObj + 1`
#   VERIFIES against the frozen aCreate obligation. Re-measured with a real build:
#   that rival is REJECTED, exit 1, on `unsolved goals case «decreasing_1: i» ...
#   |- i + 1 < i`, and a constant measure leaves `|- 0 < 0`. Strict decrease IS
#   demanded here, so nothing reaches A1/A2 or G1/G2 to be laundered, and the
#   verify-does-not-imply-resolve break this entry reported does not exist on this
#   cell. Mechanism: the `set_option ... "total"` line itself opens the
#   `TotalCorrectness` scope (Loom `MonadAlgebras/WP/Options.lean`), the frozen
#   file opens it explicitly as well, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` emits `measure b' < measure b`
#   where the `PartialCorrectness` twin would record the annotation and drop it.
#   No `spec_holes` entry is filed for this class.
# VACUOUS (frame/permission-mutation): not present as a distinct sibling case
#   here (the sibling documents it as N/A because `mgr.members` is held at full
#   permission — it is mutated). On velvet it is likewise vacuous: `related` is a
#   full `mut` carrier, and Velvet has no heap / aliasing / fractional-permission
#   system. The effect's soundness is pinned by the exact-append A2/G2 and the
#   unchanged-collection G1, attacked by the settle rivals above. No substitute
#   fabricated.
# ADDED beyond the sibling: weak-acreate-wrong-identity (attacks A1, the reported-
#   identity clause the sibling's create positive covers only implicitly);
#   weak-aupdateorcreate-no-settle, weak-aupdateorcreate-settle-on-locate,
#   weak-aupdateorcreate-flip-flag and weak-aupdateorcreate-locate-wrong-identity
#   (the third modeled obligation — aUpdateOrCreate — is a distinct `prove_correct`
#   here, so it must be independently attacked; the sibling folds it into the
#   deferred family). The last two close per-clause gaps: the flag half of G1/G2
#   was attacked only on aGetOrCreate, and the IDENTITY half of G1 was attacked on
#   no obligation at all (the settle-on-locate rivals attack G1's membership half,
#   leaving `out = (existingObj, false)` undefended).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. The
#   async bridge is an A-reference validated == the real callee by axiom_check.py,
#   and the `axioms`/`pure` regions are empty.
AXIOM_TESTS = []
