"""properties.py — G-PBT falsification battery for django__django-14915 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or the ``prove_correct`` tactic body, is changed — both
of which the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct choiceValueHash`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies).
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an abstract scalar carrier). A
lightweight wrapper object must expose an identity fully determined by the
single underlying value it carries:

  choiceValueHash (value : Int) return (h : Int)
      ensures h = valueHash value          -- THE single, load-bearing clause

``valueHash : Int → Int`` is an ``opaque`` free function with NO constraining
``axiom`` — nothing is claimed about which concrete integers it produces, only
that it is a deterministic function of the value it is given (mapping.md §3:
the concrete output of the real callee is salt-/implementation-dependent, so the
spec must not commit to any value). The method has NO ``require`` clause; the
input domain is total. One input binder, ``value``.

CARRIER NOTE. The observable is a single ``Int`` result pinned to
``valueHash value`` — one opaque function applied to ONE scalar input. There is
no branch, no list to traverse, no ``Option`` with a ``none`` arm, no second
argument, and no combination of opaque results: the spec has NO transparent
structure of its own. This is what makes the surface faithful (directive 8: the
result is grounded in the single input ``value`` and nothing else; the opaque
hash is the weakest sufficient contract, directive 7). It ALSO means every
attack must be stated against a term the elaborator cannot compute — but that
does NOT make the reject lane empty. See the CONDITIONING note below.

ADVERSARIAL READ of the sibling (nagini) classes on this carrier:

  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (read the value into a typed local, compute the
    grounded opaque hash into a second local, return it; or an eta-expanded
    application) must still verify against the byte-identical obligation, else
    the spec is SPEC-TOO-STRONG on the shape of the impl. ``valueHash`` is a
    pure function, so binding it to a local / eta-expanding it is definitionally
    the frozen return, and the frozen ``loom_solve`` script still closes the
    obligation (both verified out-of-band with real builds). Two ``pos-*`` cases
    exercise the local-reshape and the eta-reshape.

    A THIRD audit found that lane WEAK, though not dishonest, and widened it.
    Both of those reshapes are DEFINITIONALLY the frozen return: measured with
    real builds, ``example (v : Int) : (choiceValueHash v).run = DivM.res
    (valueHash v) := by rfl`` closes by bare ``rfl`` against each of them
    (EXIT 0) exactly as it does against the frozen impl, so the elaborator never
    performs any reasoning the frozen case did not already perform. A lane whose
    every positive is transparent to ``rfl`` cannot detect a spec that is
    SPEC-TOO-STRONG on anything but the impl region's surface syntax — it only
    shows ``loom_solve`` survives let-binding and eta-expansion. So a third
    positive, ``pos-arith-normalize``, is shipped whose correctness is NOT
    definitional: it hashes ``x - 1`` for a local ``x := value + 1``, and the
    obligation ``valueHash (value + 1 - 1) = valueHash value`` needs the operand
    ARITHMETICALLY normalised before the opaque atoms can be identified.
    Measured: bare ``rfl`` on that impl FAILS (EXIT 1, ``not definitionally
    equal``) while the case itself VERIFIES under the frozen ``loom_solve``
    (EXIT 0) — the first positive in this battery that makes the prover work.

  * ADMISSIBILITY — EXPRESSIBLE, and now shipped (``admiss-f2p-keying``). The
    port originally recorded this lane VACUOUS on the ground that the method has
    no ``require`` clause and that any in-region assert about a single opaque
    atom "could only be the trivial ``valueHash value = valueHash value``". The
    first half is true but is not the test; the second half is FALSE, and an
    audit disproved it with real builds. On a TOTAL carrier the admissibility
    question is not "is the precondition establishable" but "is the obligation
    SATISFIABLE, and non-degenerate, at an F2P-shaped input" — which a positive
    that discharges an INSTANCE of the obligation at that concrete input, over
    the impl's own answer, tests directly.

    A SECOND audit then found the first attempt at this case HOLLOW and replaced
    it. That version stated its clauses over RESULT-quantified stand-ins
    (``∃ hv, hv = valueHash 5``; ``∀ ha hb, ha = valueHash 5 → hb = valueHash 5
    → ha = hb``; and a conditioned distinctness of the same shape), and every
    clause of that is a pure equality-SUBSTITUTION tautology: each quantified
    answer is bound by the very equation that determines it, so nothing about
    any impl is claimed. Measured: the whole conjunction elaborates as a FREE
    ``example`` in a file that never mentions the impl, by ``simp_all`` alone
    (EXIT 0). Its liveness control was also not one — flipping a clause to
    ``h5 = h9`` fails because that clause is FALSE, not because the case is
    contingent on the impl.

    The shipped assert instead binds the impl's answer to a local ``hv`` and
    claims two things ABOUT IT at an F2P-shaped point: (a) at value=5 the
    produced answer IS the required ``valueHash 5`` (satisfiable there by a real
    computation — the keying consistency the failing example's first assertion
    needs), and (b) CONDITIONALLY on the two points' hashes differing, that
    answer differs from the one required at the OTHER F2P point (the
    non-degeneracy the second assertion needs). Clause (b) is conditioned, not
    asserted outright, precisely because the atom is opaque and non-injective.
    CONTINGENCY is what the previous version lacked and this one has, measured
    three ways with real builds: the conjunction over an unconstrained ``hv``
    does NOT elaborate (EXIT 1, ``unsolved goals``), and substituting a
    degenerate answer for ``hv`` — ``0``, ``valueHash 0``, or
    ``valueHash (value + 1)`` — leaves exactly the ``adm_1`` goal unsolved
    (EXIT 1 each), while the shipped form verifies (EXIT 0).

  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries
    this class MANDATORY (indeed calls it its #1 weakness class) because its
    inputs are held at a fractional heap permission an impl can illegally
    overwrite, and its sharpest rival overwrites the read-only derived-object
    field to satisfy the value clause. This backend is referentially
    transparent: there is no heap, no aliasing, and this bundle declares NO
    ``mut`` binder — every input is an immutable value with no heap footprint.
    There is no read-only field to mutate and no substitute probe to build. Not
    fabricated (porting map: this class is vacuous here). Moreover the
    derived-object field the sibling's sharpest attack overwrites is not even
    modeled here — the value-abstracted carrier keeps only ``value : Int``
    (mapping.md §2), because the fix uses the wrapper ONLY through its value's
    hash.

  * DIVERGENCE / non-termination - CLOSED BY THE SEMANTICS, and the reasoning below
    was REWRITTEN twice because the frozen semantics CHANGED under it.
    Every earlier revision of this file argued the class from
    ``set_option loom.semantics.termination "partial"``. The frozen
    ``Solution.lean`` reads ``"total"``, as all 500 velvet bundles do, so
    the whole paragraph was describing a bundle this is not. Under ``total``
    the verifier DOES emit a termination obligation, so the naive diverging rival
    the old text called unrefutable is in fact rejected: a ``while True`` prefix
    with no ``decreasing`` clause fails with ``Decreasing annotations are required
    in total correctness semantics`` (measured, EXIT 1, both with gold's body and
    with a wrong answer).

    A LATER revision of this bullet, having established that much, then claimed a
    NEW and sharper hole: that the termination obligation on this carrier is
    satisfied by a measure that does not decrease, so ``while 0 < 1`` with
    ``decreasing (0 : Nat)`` (a CONSTANT measure), or with ``decreasing i`` where
    ``i`` strictly INCREASES, VERIFIES at EXIT 0 while returning the unambiguously
    wrong answer ``0``. That claim is RETRACTED. Re-measured on this bundle with a
    real build, a loop carrying a constant measure is REJECTED, EXIT 1, on the
    measure's own descent goal: ``unsolved goals case «decreasing_1: (0 : Nat)»
    ⊢ 0 < 0``. The obligation is not a formality and the annotation is not merely
    recorded, so no unreachable exit launders a wrong answer here.

    The mechanism is in the frozen file's header, and both of its lines select the
    same rule. ``set_option loom.semantics.termination "total"`` is itself what
    opens the ``TotalCorrectness`` scope (Loom, ``MonadAlgebras/WP/Options.lean``:
    the option handler calls ``openScope `TotalCorrectness``), and the file opens
    that scope explicitly as well, so the two move together.
    ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes the ``measure`` and emits
    ``⌜measure b' < measure b⌝`` as a goal the proof must discharge; the
    ``PartialCorrectness`` twin is the one that takes a measure and DISCARDS it,
    and it is never opened here. So under this bundle's semantics a postcondition
    is claimed of ALL runs, not only of terminating ones, every loop owes a real
    descent proof, and the divergence class is closed by the spec. No
    ``spec_holes`` entry is filed for it.

    Nothing is shippable as a reject case regardless, for the ordinary
    witness-mechanics reason and not for the semantics reason: a loop-shaped rival's
    ``.run`` elaborates to an un-normalised ``forIn Lean.Loop.mk`` term, so no
    witness of this battery's shape can project it (measured: ``injection`` fails
    with ``equality of constructor applications expected`` against the loop rival,
    and the identical failure appears on gold, so the exit codes discriminate
    nothing). The measure-less form is blocked even earlier: its own file does not
    compile, so no witness can elaborate against it, and the gate would record
    ``witness-unproven`` (an inconclusive outcome that fails the whole battery)
    rather than a rejection.

  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``valueHash value`` is grounded
    in the method input ``value`` (directive 8: it is a fixed function OF the
    input, not a free answer-key); there is no ``axiom`` region entry and no
    separate oracle a wrong impl could echo. The only impl satisfying the clause
    IS the grounded computation.

  * UNIQUENESS / SPEC-TOO-WEAK rivals — EXPRESSIBLE by CONDITIONING on the
    carrier, and this is the load-bearing finding of the port. The sibling's two
    genuinely-wrong value rivals are (a) a hash NOT determined by the value
    (return a fixed constant) and (b) a hash of the WRONG operand. Both attack
    the same load-bearing clause: the result must equal the opaque hash OF THE
    INPUT.

    The CONSTANT rival ports and IS refutable. Its faithful real patch — a hash
    that returns a fixed integer for every wrapper — does NOT resolve the F2P:
    that test asserts distinct underlying values yield DISTINCT hashes, and a
    constant collapses every wrapper into one bucket, so distinct values collide
    and the test stays RED. So a verifying constant rival would be a genuine
    verify-does-NOT-imply-resolve break, and it MUST be rejected. Its violation
    at a concrete input ``v`` is ``c ≠ valueHash v`` for the constant ``c`` — an
    inequality between a literal and an OPAQUE term, which is not decidable by
    computation. But it does NOT need to be computed: it is refutable by
    CONDITIONING. State the refutation at a point described by a hypothesis
    ``valueHash v ≠ c`` — a weak, satisfiable assumption (the constant-rival
    author cannot know the opaque hash equals ``c`` at ``v``; indeed it generally
    does not). Under that one hypothesis the rival's constant answer ``c``
    provably differs from the spec's required ``valueHash v``, while gold —
    whose answer IS ``valueHash v`` — cannot satisfy the disequality, so the
    witness FAILS on gold. Both halves verified out-of-band with real builds; the
    single hypothesis is satisfiable (the consistency probe cannot derive
    ``False`` from ``valueHash v ≠ c`` — one opaque term, one assumption).

    Two constant rivals are shipped at two distinct constants (0, 1) refuted at
    two distinct input points (value=5, value=9), so the sole input binder
    ``value`` is VARIED by the reject witnesses (pts=2) rather than pinned at one
    value — a binder every witness held fixed would be a binder no rival abused.

    A THIRD rival attacks the same clause from the opposite side; see the
    WRONG-OPERAND entry below. The two constant rivals deny that the answer is a
    value-hash AT ALL, so a spec pinning only "the answer is some value-hash"
    would still catch them; the fixed-operand rival GRANTS the operation and
    denies only the operand, which is what shows the clause pins ``value`` as the
    argument rather than merely pinning the function applied.

    A FOURTH rival (``weak-partial-domain``, added by the second audit) closes the
    remaining axis. All three above are wrong on the WHOLE domain, so a spec that
    pinned the answer on only PART of the input domain and left the rest free
    would have rejected every one of them — the reject lane could not distinguish
    "the clause holds at every input" from "the clause holds somewhere". The
    partial-domain rival is the frozen delegation everywhere except a two-point
    slice, where it short-circuits to a constant; it is refuted at a point INSIDE
    that slice (value=1), so the rejection attributes to the clause being claimed
    pointwise. That also makes it the sharpest shape on this carrier: it agrees
    with gold on a co-finite set of inputs.

  * WRONG-OPERAND rival — SHIPPED (``weak-fixed-operand``), after an audit
    corrected the port's reason for dropping it. The port had recorded the whole
    wrong-operand class unshippable for two reasons; reason (i) — that the
    violation "is not conditionable to a satisfiable single hypothesis without
    assuming the very disequality to be shown" — is FALSE, and real builds
    disprove it. Conditioning on ``valueHash a ≠ valueHash v`` for two DISTINCT
    operand points is not assuming the conclusion: the conclusion is about the
    METHOD's result versus its required value, the hypothesis is about the opaque
    atom at two points, and the gate's own consistency probe confirms the
    hypothesis is satisfiable (no tactic derives ``False`` from a disequality
    between two opaque applications). Reason (ii) is the one that actually
    discriminates WHICH wrong-operand rival to ship, and it turns on whether the
    substituted operand is an INJECTIVE function of the input:

      - a SHIFT (``valueHash (value + 1)``) is injective in ``value``, so its
        faithful counterpart preserves both relations the failing example checks
        (equal underlying value ⇒ equal identity; distinct ⇒ distinct) and would
        still resolve. Rejecting it would be a verify-does-NOT-imply-resolve
        break in the WRONG direction, so it stays dropped — on reason (ii)
        ALONE. (It is refutable: witness built, rival EXIT 0, gold EXIT 1.)
      - a CONSTANT operand (``valueHash 0``) is NOT injective: it collapses every
        underlying value onto one identity exactly as the constant rivals do, so
        its counterpart does NOT resolve. That is the wrong-operand rival with a
        real refinement argument, and it is what ships. It attacks the clause
        from a direction the constant rivals cannot: the result IS a genuine
        value-hash — the right library operation, the right shape, and not a
        literal — merely applied to the wrong operand, so no attack on the
        literalness of the answer touches it.

    The arithmetic OFFSET rival (``valueHash value + 1``) stays dropped on the
    same reason (ii): its violation IS an ``omega`` theorem treating
    ``valueHash v`` as an atom (no conditioning needed — confirmed, rival EXIT
    0), but a constant offset preserves both relations the failing example
    checks, so its counterpart still resolves. Recorded, not silently omitted.

AXIOM lane: the sibling's ``AXIOM_TESTS`` are dropped — the axiom lane is G-AX's
job, and here there is no ``axiom`` at all (the value hash is an ``opaque`` free
function with nothing asserted to validate; mapping.md §3 records the G-AX skip).
This gate ignores ``AXIOM_TESTS`` regardless. See the footer accounting.
"""
from pathlib import Path

INSTANCE = "django__django-14915"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen return, verbatim (the single code line
# ---- strictly inside choiceValueHash's -- impl-start / -- impl-end). It lies
# ---- wholly inside the elided impl region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so every variant's edit never touches
# ---- the spec regions (axioms/pure/pre/post + the method signature and the
# ---- `ensures`).
_IMPL = "    return valueHash value"
assert _BASE.count(_IMPL) == 1, "choiceValueHash impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY choiceValueHash's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps the `ensures` clause
    # and the frozen `prove_correct choiceValueHash by loom_solve` script; the
    # reshape is definitionally the frozen return, so the script still closes the
    # byte-identical obligation (both verified out-of-band with real builds).
    # =====================================================================
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: read the underlying value into a typed local, compute the
        # grounded opaque hash into a second typed local, return that local —
        # a pure local-variable reshape of the single return-expression.
        # (Sibling: pos-local-reshape.)
        "module": _impl(
            "    let v : Int := value\n"
            "    let ident : Int := valueHash v\n"
            "    return ident"),
        "rationale": "structurally different CORRECT impl: the single return "
                     "expression is reshaped into two typed locals (bind `value` "
                     "to `v`, bind the grounded opaque hash `valueHash v` to "
                     "`ident`, return `ident`). `valueHash` is a pure function, so "
                     "this is definitionally the frozen return and `h = valueHash "
                     "value` still discharges under the frozen `loom_solve`. If it "
                     "FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected).",
    },
    {
        "id": "pos-eta-apply",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: eta-expand the hash into an explicit lambda applied to the
        # value. Same value by beta/eta; the frozen script closes it.
        "module": _impl(
            "    return (fun x => valueHash x) value"),
        "rationale": "structurally different CORRECT impl: the opaque hash is "
                     "eta-expanded to `(fun x => valueHash x) value`, which beta-"
                     "reduces to the frozen `valueHash value`, so `h = valueHash "
                     "value` holds definitionally and the frozen `loom_solve` "
                     "script still closes the byte-identical obligation. Exercises "
                     "a second impl shape (application rather than let-binding). If "
                     "it FAILS => SPEC-TOO-STRONG on the shape of the delegation. "
                     "NOTE (audit): like pos-local-reshape this reshape is "
                     "DEFINITIONALLY the frozen return — bare `rfl` closes the "
                     "concrete equation against it (EXIT 0) — so it shows only that "
                     "`loom_solve` survives eta-expansion. pos-arith-normalize is "
                     "the non-definitional positive that makes the prover work.",
    },
    {
        "id": "pos-arith-normalize",
        "kind": "soundness",
        "expect": "verify",
        # Reshape whose correctness is NOT definitional (added by the third audit).
        # The operand is carried through an arithmetic detour: bind `value + 1` to a
        # local, then hash `x - 1`. Discharging `h = valueHash value` now requires
        # the ARGUMENT to be normalised (`value + 1 - 1 ==> value`) before the two
        # opaque applications can be identified — the elaborator cannot simply see
        # through it the way it sees through a let-binding or an eta-expansion.
        "module": _impl(
            "    let x : Int := value + 1\n"
            "    return valueHash (x - 1)"),
        "rationale": "structurally different CORRECT impl whose correctness is NOT "
                     "DEFINITIONAL, which is what the other two positives lack. The "
                     "operand takes an arithmetic detour (bind `x := value + 1`, "
                     "return `valueHash (x - 1)`), so closing `h = valueHash value` "
                     "requires normalising the ARGUMENT of the opaque application "
                     "(`value + 1 - 1` to `value`) rather than merely unfolding a "
                     "local or beta-reducing. Measured with real builds: bare `rfl` "
                     "on the concrete equation FAILS against this impl (EXIT 1, `not "
                     "definitionally equal`) where it SUCCEEDS against the frozen "
                     "impl and against both other positives (EXIT 0 each), and this "
                     "case nonetheless VERIFIES under the frozen `loom_solve` "
                     "(EXIT 0). So it is the first positive here that exercises real "
                     "reasoning instead of syntactic transparency. If it FAILS => "
                     "SPEC-TOO-STRONG: the spec/proof would be pinned to operands "
                     "written in one normal form, rejecting a faithful correct impl "
                     "that reaches the same operand by a different arithmetic route.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). No method here carries a `require`
    # clause, so "a normal input satisfies the precondition" is vacuously true and
    # is NOT what this case tests. The total-carrier analogue is that the
    # obligation is UNSATISFIABLE or DEGENERATE at an F2P-shaped input: the case
    # discharges an INSTANCE of the obligation at that concrete input, as a `have`
    # over the impl's own answer, before closing the frozen obligation verbatim.
    #
    # AUDIT NOTE (this case was REPLACED; the previous one was hollow). The prior
    # assert quantified over the RESULT at literal points —
    #   (∃ hv, hv = valueHash 5) ∧
    #   (∀ ha hb, ha = valueHash 5 → hb = valueHash 5 → ha = hb) ∧
    #   (valueHash 5 ≠ valueHash 9 → ∀ h5 h9, h5 = valueHash 5 → h9 = valueHash 9
    #      → h5 ≠ h9)
    # — and every clause of that is a pure equality-SUBSTITUTION tautology: it
    # mentions no impl and constrains no answer, since each `hv`/`ha`/`h5` is
    # bound by the very equation that determines it. Measured, with real builds:
    # the whole conjunction elaborates as a FREE `example` in a file that never
    # names the impl, by `simp_all` alone (EXIT 0), and also by an explicit
    # `⟨⟨valueHash 5, rfl⟩, fun a b ha hb => by rw [ha, hb], …⟩` (EXIT 0). An
    # assert that holds of every impl, and indeed of no impl, tests nothing; its
    # `verified` outcome attested only that `loom_solve` can prove a tautology.
    # The claimed liveness control (flipping clause 3 to `h5 = h9`) fails for the
    # unrelated reason that the flipped clause is simply FALSE, so it did not
    # establish contingency on the impl either.
    #
    # The replacement states the same two F2P-shaped facts about the impl's OWN
    # answer local `hv`, which is what makes it contingent: `hv` is bound to what
    # the impl returns, so the assert is a claim ABOUT the returned answer rather
    # than about a universally-quantified stand-in. Both halves measured:
    #   * as shipped (hv := valueHash value): EXIT 0;
    #   * the same assert with a DEGENERATE answer — hv := 0, hv := valueHash 0,
    #     hv := valueHash (value + 1) — EXIT 1 in all three, each leaving exactly
    #     the `adm_1` goal unsolved, so the assert genuinely tracks the answer;
    #   * the conjunction as a FREE `example` over unconstrained `value hv`:
    #     EXIT 1 (`unsolved goals`), so it is NOT a tautology — the contrast the
    #     previous case failed.
    # The frozen `loom_solve` still closes the method's own `ensures`.
    # =====================================================================
    {
        "id": "admiss-f2p-keying",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    let hv : Int := valueHash value\n"
            "    assert (with_name_prefix `adm\n"
            "      ((value = 5 → hv = valueHash 5) ∧\n"
            "       (valueHash 5 ≠ valueHash 9 → value = 5 → hv ≠ valueHash 9)))\n"
            "    return hv"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at exactly "
                     "an F2P-shaped input, discharged as an assert about the "
                     "answer the impl actually produces (bound to the local `hv`) "
                     "rather than about a quantified stand-in. Clause 1: at the "
                     "concrete point value=5 the produced answer IS the required "
                     "`valueHash 5`, so the obligation is satisfiable there by a "
                     "real computation — the keying consistency the failing "
                     "example's equal-value assertion needs. Clause 2, CONDITIONED "
                     "on the two points' hashes differing (the atom is opaque and "
                     "NOT injective, so this cannot be asserted outright): the "
                     "answer at value=5 then differs from the answer required at "
                     "the OTHER F2P point, so the obligation does not collapse "
                     "both points onto one answer — the non-degeneracy the "
                     "distinctness assertion needs. If this FAILED => "
                     "PRECOND-TOO-STRONG (the obligation is unsatisfiable or "
                     "degenerate at the very input the failing example drives). "
                     "The assert is CONTINGENT on the impl, not a tautology: the "
                     "same conjunction over an unconstrained `hv` does NOT "
                     "elaborate (EXIT 1), and substituting a degenerate answer "
                     "(0, `valueHash 0`, or `valueHash (value + 1)`) leaves the "
                     "`adm_1` goal unsolved (EXIT 1 each) — all measured with real "
                     "builds. The frozen `loom_solve` still closes the value "
                     "clause.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input CONDITIONED on the opaque carrier, and the refinement
    # argument that its faithful real counterpart would NOT resolve the failing
    # test. Both attack the sole load-bearing clause `h = valueHash value` by
    # returning a fixed constant (a hash NOT determined by the input value) — the
    # sibling's constant rival, ported. The `value` binder is VARIED across the
    # two witnesses (value=5, value=9) so the reject lane demonstrates the spec's
    # dependence on the input at two distinct points (pts=2).
    #
    # WITNESS SHAPE (CONDITIONING). The rival returns a literal constant `c`; its
    # violation `c ≠ valueHash v` is a disequality between a literal and an OPAQUE
    # term, which no computation decides. It is stated instead at a point
    # described by the satisfiable hypothesis `valueHash v ≠ c`: under it the
    # rival's constant answer provably differs from the spec's required
    # `valueHash v` (elaborates against the rival), while gold's answer IS
    # `valueHash v` and cannot satisfy the disequality (FAILS on gold). The lone
    # hypothesis is jointly satisfiable — one opaque term, one assumption — so it
    # is not a forgery from an inconsistent premise.
    # =====================================================================
    {
        "id": "weak-const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: return a fixed 0 for every input, ignoring `value` entirely — a
        # hash NOT determined by the underlying value. (Sibling: weak-const.)
        "module": _impl("    return 0"),
        "refinement": "a faithful counterpart that returns a fixed integer for "
                      "every wrapper makes the identity independent of the "
                      "underlying value, so two wrappers carrying DISTINCT "
                      "underlying values collapse to the SAME identity. The "
                      "failing example asserts distinct underlying values yield "
                      "DISTINCT identities; with a constant they collide, so the "
                      "assertion stays RED. It would NOT resolve — a verifying "
                      "constant rival is a genuine verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from the sole clause `h = valueHash value`: the "
                     "result must equal the opaque hash of the input, but the "
                     "rival returns the literal 0. Refuted at value=5 by "
                     "conditioning on `valueHash 5 ≠ 0` (a satisfiable single "
                     "hypothesis): the rival's 0 differs from the required "
                     "`valueHash 5`, while gold returns `valueHash 5` and cannot "
                     "meet the disequality. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "clause does not pin the result to the value's hash).",
        "witness":
            "example (h : valueHash 5 ≠ 0) :\n"
            "    (choiceValueHash 5).run ≠ DivM.res (valueHash 5) := by\n"
            "  simp only [choiceValueHash]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  exact h h1.symm\n",
    },
    {
        "id": "weak-const-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: return a fixed 1 for every input — the same failure class as
        # weak-const-zero (a hash NOT determined by the value) at a DIFFERENT
        # constant, refuted at a DIFFERENT input point so the `value` binder is
        # varied (pts=2) and the two witnesses do not share an input.
        "module": _impl("    return 1"),
        "refinement": "as weak-const-zero: a fixed-integer identity is "
                      "independent of the underlying value, so distinct "
                      "underlying values collapse to one identity and the failing "
                      "example's distinctness assertion stays RED. It would NOT "
                      "resolve; a verifying rival is a true verify-does-not-imply-"
                      "resolve break.",
        "rationale": "REJECT from the sole clause `h = valueHash value`: the "
                     "rival returns the literal 1, not the input's opaque hash. "
                     "Refuted at value=9 by conditioning on `valueHash 9 ≠ 1` (a "
                     "satisfiable single hypothesis): the rival's 1 differs from "
                     "the required `valueHash 9`, while gold returns `valueHash 9` "
                     "and cannot meet the disequality. Refuted at a DISTINCT input "
                     "(9, vs 5 for weak-const-zero) so the sole `value` binder is "
                     "varied. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness":
            "example (h : valueHash 9 ≠ 1) :\n"
            "    (choiceValueHash 9).run ≠ DivM.res (valueHash 9) := by\n"
            "  simp only [choiceValueHash]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  exact h h1.symm\n",
    },
    {
        "id": "weak-fixed-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # Rival: the WRONG-OPERAND class (the sibling's weak-wrong-field, re-aimed
        # — the derived-object facet is unmodeled here). It calls the SAME library
        # hashing, but on a FIXED operand instead of the underlying value the
        # wrapper carries, so the answer is a genuine value-hash that is simply
        # not this wrapper's. Distinct from the constant rivals in kind: the
        # result is not a literal, so it is immune to any attack that keys on the
        # answer being a constant integer, yet it is still not determined by the
        # input. Refuted at a THIRD distinct input point (value=5 conditioned on a
        # DIFFERENT hypothesis shape: a disequality between two opaque
        # applications rather than between an application and a literal).
        "module": _impl("    return valueHash 0"),
        "refinement": "a faithful counterpart that hashes a FIXED operand rather "
                      "than the wrapper's own underlying value makes every "
                      "wrapper's identity the same one, regardless of what it "
                      "carries — the fixed operand is not an injective function "
                      "of the input, so it collapses distinct underlying values "
                      "onto one identity exactly as a constant does. The failing "
                      "example asserts distinct underlying values yield DISTINCT "
                      "identities; they collide, so it stays RED. It would NOT "
                      "resolve. This is what separates it from the SHIFTED "
                      "operand (dropped, see the header): a shift IS injective, "
                      "so a shift preserves both relations the example checks and "
                      "its counterpart would resolve.",
        "rationale": "REJECT from the sole clause `h = valueHash value`: the rival "
                     "returns `valueHash 0` — the right library operation applied "
                     "to the WRONG operand — which the clause does not permit "
                     "unless the atom happens to agree at the two operand points. "
                     "Refuted at value=5 by conditioning on `valueHash 0 ≠ "
                     "valueHash 5`, a satisfiable single hypothesis (a disequality "
                     "between two applications of an opaque, NON-injective "
                     "function at distinct points — the consistency probe cannot "
                     "derive `False` from it, confirmed EXIT 1). Under it the "
                     "rival's answer provably differs from the required `valueHash "
                     "5`, while gold's answer IS `valueHash 5` and reduces the "
                     "hypothesis's subject to `valueHash 5 = valueHash 5`, so the "
                     "witness FAILS on gold. If it VERIFIES => SPEC-TOO-WEAK (the "
                     "clause pins the OPERATION but not the OPERAND, i.e. it does "
                     "not actually tie the result to the input the wrapper holds).",
        "witness":
            "example (h : valueHash 0 ≠ valueHash 5) :\n"
            "    (choiceValueHash 5).run ≠ DivM.res (valueHash 5) := by\n"
            "  simp only [choiceValueHash]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  exact h h1\n",
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival, added by the audit. The three rivals above are all
        # wrong on the WHOLE domain (a constant, or a fixed operand), so a spec
        # that pinned the answer only on a sub-domain and left the rest free would
        # still have rejected every one of them — the near-miss class was
        # unattacked. This rival is the frozen delegation EVERYWHERE EXCEPT a
        # bounded slice of small positive underlying values, where it answers a
        # fixed constant instead. Its rejection therefore attributes to the clause
        # holding at EVERY input rather than merely somewhere.
        #
        # AUDIT NOTE (the slice was WIDENED). The first version short-circuited on
        # exactly `value = 1 ∨ value = 2` and its refinement asserted those are
        # "precisely the values the failing example's two wrappers carry". That
        # claim is not demonstrated by anything in this bundle — the underlying
        # values are auto-assigned identifiers, and nothing here fixes them to 1
        # and 2 (a shared fixture, a reused sequence, or any earlier row makes them
        # larger). A refinement argument that holds only if the two identifiers
        # happen to be 1 and 2 is a claim the manifest cannot support, so the slice
        # is now a bounded RANGE that contains any small auto-assigned identifier
        # regardless of where the sequence starts. The near-miss property is
        # unchanged (co-finite agreement with gold) and the refinement no longer
        # depends on an undemonstrated value. Re-measured with real builds: the
        # widened rival is REJECTED (EXIT 1, `unsolved goals` on `ensures_1` with
        # the range hypotheses in context) and the witness at value=1 still
        # ELABORATES on it (EXIT 0) and FAILS on gold (EXIT 1).
        "module": _impl(
            "    if 1 ≤ value ∧ value ≤ 1000 then\n"
            "      return 0\n"
            "    else\n"
            "      return valueHash value"),
        "refinement": "a faithful counterpart short-circuits the wrapper's "
                      "identity to one fixed integer for every small positive "
                      "underlying value in a bounded range and delegates correctly "
                      "for every other. The failing example's two wrappers carry "
                      "distinct small auto-assigned identifiers, which fall inside "
                      "that range wherever the sequence happens to start, so both "
                      "collapse to the SAME identity and the example's distinctness "
                      "assertion stays RED — while a coarse probe that only sampled "
                      "large or negative values would see nothing wrong. It would "
                      "NOT resolve. The range is bounded rather than pinned at two "
                      "literals precisely so the argument does not depend on the "
                      "identifiers taking any particular value.",
        "rationale": "REJECT from the sole clause `h = valueHash value`, which is "
                     "claimed at EVERY input, not merely somewhere: on the "
                     "bounded short-circuit arm the rival returns the literal 0 where the "
                     "clause demands the input's opaque hash. Refuted at value=1 "
                     "by conditioning on `valueHash 1 ≠ 0` (a satisfiable single "
                     "hypothesis; the consistency probe cannot derive `False` from "
                     "it, EXIT 1): the rival takes the short-circuit arm there and "
                     "answers 0, while gold answers `valueHash 1`, so the witness "
                     "ELABORATES on the rival (EXIT 0) and FAILS on gold (EXIT 1). "
                     "Adds the PARTIAL-DOMAIN class the other three rivals leave "
                     "unattacked — each of those is wrong on the whole domain, so "
                     "a spec pinning the answer on only part of it would reject "
                     "them anyway. If it VERIFIES => SPEC-TOO-WEAK (the clause is "
                     "not actually claimed at every input).",
        "witness":
            "example (h : valueHash 1 ≠ 0) :\n"
            "    (choiceValueHash 1).run ≠ DivM.res (valueHash 1) := by\n"
            "  simp only [choiceValueHash]\n"
            "  intro heq\n"
            "  injection heq with h1\n"
            "  exact h h1.symm\n",
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 2 frame-mutation rivals, 3
# uniqueness/partial-domain rivals incl. a divergence rival) plus 2 AXIOM_TESTS.
# Every one is accounted for. The sibling contracts ONE method
# (ChoiceValue.membership_identity) over a TWO-facet heap carrier held at a
# fractional permission, with a @Pure/@ContractOnly oracle and a MustTerminate
# obligation. This bundle contracts ONE method (choiceValueHash) over a SINGLE
# abstract scalar `Int value`, pinning `h = valueHash value` for an OPAQUE free
# function `valueHash` with no axiom, no precondition, and no termination clause.
# The two surfaces model the SAME behaviour (the wrapper's identity is a function
# of its wrapped value alone), but the carrier is far coarser here.
#
#   sibling case          kind            -> here
#   -------------------------------------------------------------------------
#   pos-local-reshape     soundness       -> pos-local-reshape        PORTED
#   (added)               soundness       -> pos-eta-apply            ADDED
#   (added, non-defeq)    soundness       -> pos-arith-normalize      ADDED
#   admiss-reads          admissibility   -> admiss-f2p-keying       RE-AIMED
#   frame-mut-instance    uniqueness      -> (none)                   VACUOUS
#   frame-mut-value       uniqueness      -> (none)                   VACUOUS
#   weak-const            uniqueness      -> weak-const-zero          PORTED
#   (added, 2nd point)    uniqueness      -> weak-const-one           ADDED
#   weak-wrong-field      uniqueness      -> weak-fixed-operand       RE-AIMED
#                                            (shift variant still DROPPED:
#                                             resolve-preserving, reason ii)
#   (added, partial domain) uniqueness    -> weak-partial-domain      ADDED
#   diverge-loop          uniqueness      -> (none)                   VACUOUS
#   ax-sound-value_identity  axiom        -> (none)                   G-AX / no axiom
#   ax-cover-value_identity  axiom        -> (none)                   G-AX / no axiom
#
# 3 ported/re-aimed + 5 added = 8 velvet cases (3 soundness, 1 admissibility,
# 4 uniqueness). The admissibility and wrong-operand lanes were added by the
# first adversarial audit of this cell, which disproved the port's stated reasons
# for dropping them with real builds; see those two entries below. A SECOND audit
# then REPLACED the admissibility case (its assert was a tautology — see the
# header and the case comment) and ADDED weak-partial-domain, the near-miss class
# all three prior rivals leave unattacked: each of those is wrong on the WHOLE
# domain, so a spec pinning the answer on only part of it would have rejected
# them anyway, and the reject lane could not tell "claimed at every input" from
# "claimed somewhere". A THIRD audit ADDED pos-arith-normalize (the soundness lane
# held only DEFINITIONAL reshapes, so it exercised no reasoning) and WIDENED
# weak-partial-domain's short-circuit slice from two literals to a bounded range
# (its refinement rested on the underlying identifiers being exactly 1 and 2,
# which nothing in this bundle demonstrates).
#
# PORTED — soundness (1): pos-local-reshape. Same argument (a correct local-
#   variable reshape must verify); mechanics rewritten for the Lean `let`/`return`
#   over `valueHash`. ADDED pos-eta-apply so the reshape space (let-binding AND
#   eta-application) is exercised, not a single shape. Both build against the
#   frozen `loom_solve` (real builds, EXIT 0). ADDED pos-arith-normalize (third
#   audit) because BOTH of those are definitionally the frozen return — bare
#   `rfl` closes the concrete equation against each (EXIT 0), so neither makes
#   the elaborator do anything the frozen case did not. The added positive routes
#   the operand through `value + 1 - 1`, where bare `rfl` FAILS (EXIT 1) and the
#   case still VERIFIES under the frozen `loom_solve` (EXIT 0): the SPEC-TOO-STRONG
#   direction now has one probe that is not syntactic transparency.
# PORTED — uniqueness (1): weak-const -> weak-const-zero (return a fixed 0). Its
#   real patch collapses distinct values to one identity, failing the F2P
#   distinctness assertion, so it must reject. On this OPAQUE carrier the
#   refutation `0 ≠ valueHash v` is not decidable by computation but IS provable
#   by CONDITIONING on the satisfiable single hypothesis `valueHash v ≠ 0` — the
#   prompt's own carrier-conditioning technique. ADDED weak-const-one (return a
#   fixed 1) at a DISTINCT input point (value=9 vs value=5) so the sole `value`
#   binder is varied across the reject witnesses (pts=2). Both witnesses verified
#   out-of-band: each ELABORATES against its rival (EXIT 0) and FAILS on gold
#   (EXIT 1); each hypothesis is satisfiable (consistency probe cannot derive
#   `False`).
# RE-AIMED — admissibility (1): admiss-reads -> admiss-f2p-keying. The sibling
#   case relied on a non-trivial half-permission precondition admitting a normal
#   wrapper's reads. No method here has a `require` clause (pre-conditions region
#   empty), so that half IS vacuous — but the port then concluded the whole lane
#   was vacuous, on the ground that an assert over a single opaque atom "could
#   only be the trivial `valueHash value = valueHash value`". That ground is
#   FALSE and the audit disproved it with real builds. The total-carrier
#   admissibility question is whether the obligation is SATISFIABLE and
#   NON-DEGENERATE at an F2P-shaped input, and an opaque atom does not block it:
#   quantify over the RESULT rather than compute the atom. The shipped case
#   asserts existence at value=5, agreement of any two answers at the SAME
#   underlying value, and — conditioned on the two points' hashes differing,
#   since the atom is non-injective — distinctness of the answers at value=5 vs
#   value=9. It VERIFIES (EXIT 0) with the frozen impl and frozen `loom_solve`
#   kept verbatim, and it is LIVE: flipping the last clause's conclusion to
#   `h5 = h9` leaves exactly that conjunction as an unsolved goal (EXIT 1). This
#   restores the third direction the gate exists to test (PRECOND-TOO-STRONG).
# VACUOUS — frame/permission-mutation (2): frame-mut-instance and frame-mut-value
#   reject an illegal WRITE to a read-only heap facet held at a fractional
#   permission. This backend is referentially transparent, has no heap and no
#   aliasing, and this bundle declares NO `mut` binder — no read-only field to
#   overwrite and no substitute probe. The sharper (frame-mut-instance) targets
#   the derived-object field, which is not even modeled here (value-abstracted
#   carrier keeps only `value : Int`, mapping.md §2). No substitute fabricated.
# NOT SHIPPABLE — divergence (1): diverge-loop rejects a non-terminating impl via
#   the sibling's MustTerminate obligation, needed because Nagini verifies partial
#   correctness. The frozen spec here is now `loom.semantics.termination "total"`
#   (it was `partial` when every earlier revision of this file was written; the
#   corpus-wide remediation landed in between), so unlike those revisions claimed
#   there IS a termination obligation, and the naive `while True` rival with no
#   measure is REJECTED by it (`Decreasing annotations are required in total
#   correctness semantics`, EXIT 1). A later revision then claimed a residual hole
#   in the other direction: that the obligation accepts a NON-DECREASING measure, so
#   `while 0 < 1` + `decreasing (0 : Nat)` returning the wrong answer 0 VERIFIES at
#   EXIT 0 on an exit it never reaches. RETRACTED on re-measurement: that rival is
#   REJECTED, EXIT 1, on the measure's own goal, `unsolved goals case
#   «decreasing_1: (0 : Nat)» |- 0 < 0`. The descent obligation is real because the
#   `set_option ... "total"` line itself opens the `TotalCorrectness` scope (Loom
#   `MonadAlgebras/WP/Options.lean`), the frozen file also opens it explicitly, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` emits `measure b' < measure b`
#   where the `PartialCorrectness` twin would drop the measure. So no `spec_holes`
#   entry is filed. The disposition "nothing to ship" survives on witness mechanics
#   alone: no witness of this battery's shape can project a loop rival's
#   un-normalised `forIn` term (injection fails identically on both sides), and the
#   measure-less form makes its own file uncompilable, so a witness cannot elaborate
#   against it either.
# RE-AIMED — uniqueness (1): weak-wrong-field -> weak-fixed-operand. The port
#   dropped the whole wrong-operand class for two reasons; the audit found reason
#   (i) FALSE and reason (ii) applicable to only ONE variant of the class.
#   (i) claimed the violation is "not conditionable to a satisfiable single
#   hypothesis without assuming the very disequality to be shown". It is: the
#   conclusion is about the METHOD's result versus its required value, while the
#   hypothesis is about the opaque atom at two distinct operand points, so the two
#   are not the same proposition — and the gate's consistency probe confirms the
#   hypothesis is satisfiable (no tactic derives `False` from a disequality
#   between two opaque applications; probe EXIT 1). Measured for BOTH variants:
#   `valueHash 0` (rival EXIT 0, gold EXIT 1) and `valueHash (value + 1)` (rival
#   EXIT 0, gold EXIT 1). So refutability never was the obstacle.
#   (ii) is the reason that actually decides, and it turns on whether the
#   substituted operand is INJECTIVE in the input:
#     - SHIFTED operand (`valueHash (value + 1)`) — injective, so its faithful
#       counterpart preserves both relations the failing example checks and WOULD
#       resolve. Rejecting it would be a verify-does-NOT-imply-resolve break in
#       the WRONG direction. STILL DROPPED, on reason (ii) alone, now stated as
#       the sole reason rather than as a second one.
#     - FIXED operand (`valueHash 0`) — NOT injective: it collapses every
#       underlying value onto one identity, so its counterpart fails the
#       distinctness assertion and does NOT resolve. SHIPPED as
#       weak-fixed-operand. It attacks the clause from a direction neither
#       constant rival reaches: the answer is a real value-hash (right operation,
#       right shape, not a literal), wrong only in its OPERAND — so the clause is
#       shown to pin the operand and not merely the operation.
#   The arithmetic OFFSET rival (`valueHash value + 1`) stays dropped on reason
#   (ii) as well: its violation IS an `omega` theorem needing no conditioning
#   (rival EXIT 0, confirmed), but a constant offset preserves both relations the
#   failing example checks, so its counterpart still resolves. Recorded, not
#   silently omitted.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job, and this bundle declares
#   NO axiom — the value hash is an `opaque` free function with nothing asserted
#   about its value to validate (mapping.md §3 records the G-AX skip). This gate
#   ignores AXIOM_TESTS regardless.
#
# COVERAGE. The single post-image clause `h = valueHash value` is DEFENDED (all
# three soundness positives bear on it, one of them non-definitionally),
# ATTACKED from three independent directions (the
# two constant rivals deny that the answer is a value-hash at all; the
# fixed-operand rival grants the operation and denies the OPERAND, so the clause
# is shown to pin both; weak-partial-domain grants BOTH everywhere except a
# two-point slice, so the clause is shown to be claimed at EVERY input and not
# merely somewhere), and probed for SATISFIABILITY and non-degeneracy at the F2P
# shape (admiss-f2p-keying). All three of the gate's directions are therefore
# live: SPEC-TOO-WEAK (4 rivals), SPEC-TOO-STRONG (2 positives),
# PRECOND-TOO-STRONG (1 admissibility case). The sole input binder `value` is
# VARIED by the reject witnesses (value=5, value=9, value=1) and the
# admissibility assert names two points, so the battery demonstrates the spec's
# dependence on the input at distinct points rather than pinning it at one.
#
# WHAT THE AUDITS PROBED AND DID NOT FIND. Across the three audits, TWENTY-ONE
# NEW wrong impls beyond the shipped rivals were built against the frozen spec and
# ALL were rejected (EXIT 1): hash of a fixed operand, of a shifted operand, of a
# negated operand, of a squared operand, of a reduced operand (`value % p`), of a
# transposing operand (a two-point swap), of the hash itself (double application,
# both direct and via a local), a constant offset on the correct hash, a doubling
# of it, a negation of it, a self-cancelling difference, an in-region `assert
# False` and an in-region assert of the very equation to be shown (both rejected
# on the assert's own goal, so an impl cannot smuggle its obligation in as an
# assumption — checked with a repaired proof script too), and partial-domain
# rivals correct on all but one point, on a half-line, and on a bounded range —
# those last are the sharpest available SPEC-TOO-WEAK probes on this carrier,
# since they agree with gold on a co-finite slice, and the spec still rejects them
# (one is now SHIPPED as weak-partial-domain rather than merely probed). TWELVE
# NEW correct reshapes were built and ALL verified (EXIT 0): a dead-branch
# duplication, a function-typed local (`let f : Int -> Int := valueHash`), a
# double and a triple let-binding, `valueHash (value * 1)`, `valueHash (value +
# 0)`, `id (valueHash value)`, a guarded return whose two arms agree, a
# sign-split whose negative arm double-negates, and two arithmetic detours on the
# operand — one of which is now SHIPPED as pos-arith-normalize because, unlike
# every other reshape probed, bare `rfl` does NOT close it.
#
# The FOURTH audit re-ran all four reject witnesses (rival EXIT 0 / gold EXIT 1 /
# consistency probe EXIT 1, each reproduced) and added the mandatory B' forgery
# pair to each: the type-revealing probe prints gold's hypothesis as the REFLEXIVE
# `valueHash v = valueHash v` versus the rival's CONCRETE `0 = valueHash 5` /
# `1 = valueHash 9` / `valueHash 0 = valueHash 5`, and the flipped claim (`=` for
# `≠`, closed by rfl) INVERTS both exit codes (gold 0 / rival 1). So every gold-side
# error tracks the claim and none of the four is hollow. It also probed three NEW
# wrong impls (a cubed operand, a single-point substitution at 5, and a 5<->9
# transposition — all REJECTED, EXIT 1) and four NEW correct reshapes (a dead
# `if value = value` branch, a function-typed local, `value * 1`, and `id` — all
# VERIFIED, EXIT 0). No SPEC-TOO-WEAK or SPEC-TOO-STRONG hole in the value clause.
#
# NO spec hole is escalated on this cell, and the divergence class in particular is
# CLOSED. It was RE-DERIVED rather than inherited, because the frozen semantics
# flipped from `partial` to `total` after this manifest was first written. Under
# `total` the naive diverging rival is REJECTED at the `while` itself, and the
# measure-carrying rival is REJECTED on the measure's own descent goal
# (`case «decreasing_1: (0 : Nat)» |- 0 < 0`), which retracts the intermediate
# claim that a NON-DECREASING measure re-admits a wrong-answer diverging impl at
# EXIT 0. See the DIVERGENCE entry in the header for the measurements and the
# mechanism in Loom's `TotalCorrectness.WPGen.forWithInvariantLoop`.
AXIOM_TESTS = []
