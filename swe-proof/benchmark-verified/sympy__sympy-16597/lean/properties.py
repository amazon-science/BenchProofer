"""properties.py — G-PBT falsification battery for sympy__sympy-16597 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and each ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect="verify"`` passes iff (in scope AND
the file elaborates with the obligation closed); ``expect="reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

DEFENDED SURFACE (two no-input closed fact tables):

  deduceEven   : KB      — the closed fact table for a quantity seeded `even`.
  deduceInfinite : KB    — the closed fact table for an unbounded real quantity.

  A ``KB`` is a record of three-valued facts (each ``Option Bool``:
  ``some true`` / ``some false`` / ``none``). Both functions take NO input, so
  the only binder of each spec predicate is the output record ``out : KB``; a
  rival varies that record. The load-bearing postconditions are:

    * deduceEven   : ``consistentTheory out`` AND ``even = some true`` AND — the
      instance's central delta — ``finite = some true``, plus
      ``transcendental``/``irrational`` resolved false and ``prime``/``composite``
      left ``none`` (parity does not decide primality).
    * deduceInfinite : ``consistentTheory out`` AND the whole unbounded-real
      cascade: ``infinite``/``real`` true, ``finite`` false, and every set
      membership (``rational``/``integer``/``even``/``odd``/``algebraic``/
      ``transcendental``/``irrational``/``composite``) false, with
      ``noninteger = some true``.

  ``consistentTheory`` is a GROUNDED predicate over the record's OWN fields (a
  spelled-out conjunction of containment implications), not an opaque answer-key
  oracle, so an "echo" here is just a correct record — the ungrounded-oracle
  class is N/A. The functions take no input and hold no read-only alias, so the
  frame/permission class is also N/A. The live surface is SPEC-TOO-WEAK (an
  unpinned or engine-contradicting trit that the theory's containment clauses
  still admit) and SPEC-TOO-STRONG (a structurally-different correct record must
  still verify).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-overwrite attack meaningful only because its inputs are held at
    fractional (read-only) permission. Lean is referentially transparent and
    both functions take no input at all, so there is no permission to violate
    and no aliasing to exploit. No substitute is fabricated.

  * DIVERGENCE / NON-TERMINATION — EXPRESSIBLE but NOT SHIPPABLE (a known
    limitation of the witness rule on this carrier, not a vacuous class).
    Corrected 2026-08-13: this entry previously claimed a diverging impl "cannot
    be written; the class has no expressible instance". That is FALSE and was
    measured false. A rival whose boundedness fact is produced by a
    non-terminating search,

        partial def spinFinite : Nat → Option Bool
          | n => spinFinite (n + 1)
        def implementation_deduceEven : KB := { ..., finite := spinFinite 0, ... }

    passes ``variant_problems`` (no new theorem/axiom/``sorry``; the
    ``correct_deduceEven`` STATEMENT is byte-identical) and IS rejected by the
    verifier — exit 1, with the honest semantic goal ``⊢ spinFinite 0 = some
    true`` left open, i.e. the postcondition's pinned boundedness clause is
    exactly what cannot be discharged. Lean's termination checker also rejects
    the cruder shapes (a self-referential ``def``, and a ``def`` whose recursion
    counts upward: ``fail to show termination for``), so the class has expressible
    instances by several routes.

    What blocks SHIPPING one is the witness rule, and it blocks in both
    directions — measured, four builds:

      - the battery's own unconditional witness shape leaves
        ``⊢ spinFinite 0 = some true → ¬spinFinite 0 = some false →
        ¬spinFinite 0 = some true`` and FAILS against the rival (exit 1 =
        ``witness-unproven``). Correctly so: ``partial def`` yields an OPAQUE
        term, so the rival's ``finite`` is unknown rather than wrong, and a rival
        that is not provably wrong has no refutation to state.
      - conditioning instead on ``implementation_deduceEven.finite ≠ some true``
        (the only shared-vocabulary phrasing — naming ``spinFinite`` is barred by
        ``witness_scope_problems``, since gold's failure would then be an unknown
        name) ELABORATES against the rival AND against the frozen solution
        (exit 0 / exit 0 = ``witness-vacuous``): on gold that hypothesis is
        contradictory, so it proves anything.

    So the rejection here is real but UNATTRIBUTABLE, and shipping the case would
    record a rejection the gate cannot tie to the spec. The disposition is
    therefore "known hole in the witness rule for opaque-valued rivals", NOT
    "vacuous class" — a vacuous class would claim this battery is complete, and
    on this axis it is not. No ``set_option loom.semantics.termination`` appears
    in the frozen file (this is the plain lean carrier, total by construction),
    so there is no termination obligation for a rival to evade either.

  * UNGROUNDED-ORACLE ECHO — N/A. ``consistentTheory`` is spelled out over the
    record's own fields; there is no opaque callee whose value a rival could
    echo without doing the deduction.

  * UNIQUENESS / SPEC-TOO-WEAK — APPLIES; the load-bearing surface. Eight rivals
    set an engine-contradicting or unpinned trit and are refuted at the record
    they return.

  * SOUNDNESS / SPEC-TOO-STRONG — APPLIES. Two structurally-different but
    correct records (one more-complete `deduceEven`, one `deduceInfinite`
    assembled by structure update from an auxiliary table) must still verify
    against the frozen obligation.

CARRIER NOTE — what does NOT count as a reshape here. `KB` is a plain structure
and Lean normalises NAMED-FIELD order at elaboration, so writing the same
fourteen fields in a permuted order produces the BYTE-IDENTICAL elaborated term
(`#print` under `pp.explicit` shows the two bodies equal; `rfl` closes their
equation). A "field reorder" variant is therefore the frozen impl under a
different source spelling and tests nothing. A record built by structure UPDATE
does differ: it elaborates to `have __src := aux; { f := __src.f, ... }`, so the
untouched fields arrive as PROJECTIONS and the obligation must be discharged
through that indirection — measured, the frozen tactic body does not close it
without also unfolding the auxiliary constant. That is the shape the soundness
positive uses.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``refine ⟨?_, ?_⟩ <;> simp`` is tuned
to the frozen record — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet stating
``¬ problem_spec_<name> implementation_<name>`` and closing it after unfolding
the spec + record + theory. Because the two records (rival vs frozen) are
distinct constants, ``implementation_<name>`` denotes a DIFFERENT value on each
side, so the same witness text HOLDS of the rival and FAILS on gold. Each was
built against the rival (must succeed) and against the frozen solution (must
fail) to confirm it discriminates. The goal is a decidable clash of
``Option Bool`` literals inside ``consistentTheory``; ``decide`` cannot synthesize
a ``Decidable`` instance for the implication-laden theory, so each witness closes
with ``simp`` (which reduces the record projections and the false implication).

BINDER / CLAUSE COVERAGE. The single binder of each predicate is the output
record; the reject witnesses hold it at NINE distinct constants (``pts`` = 9).
The spec's solution set is nearly a singleton — an exhaustive enumeration of all
3^14 fact tables finds exactly TWO records satisfying ``problem_spec_deduceEven``
(they differ only in ``infinite``, which the postcondition does not pin) and
exactly ONE satisfying ``problem_spec_deduceInfinite`` — so the rivals are chosen
to separate WHICH part of the spec does the rejecting, not merely to be wrong:

  * deduceEven — theory edges: ``even → ¬odd`` (weak-even-odd),
    ``integer → ¬noninteger`` (weak-even-noninteger),
    ``rational → algebraic`` (weak-even-algebraic). Pinned clauses:
    ``finite = some true`` (nm-even-drop-finite, which also breaks
    ``rational → finite``) and BOTH ``none`` pins — ``prime = none``
    (weak-even-prime) and ``composite = none`` (weak-even-composite). Those two
    are the only rivals the THEORY admits, so in each the pin alone refutes.
  * deduceInfinite — theory edges: ``real → complex``
    (weak-infinite-complex) and the contrapositive ``¬integer → ¬prime``
    (nm-infinite-drop-prime — the only field here the postcondition does NOT pin,
    so the theory alone refutes it). Pinned clause: ``noninteger = some true``
    (nm-infinite-drop-noninteger).

The two ``prime`` rivals are deliberately mirrored: on ``deduceEven`` the theory
is silent and the pin carries the rejection; on ``deduceInfinite`` there is no
pin and the theory carries it. That pair is what distinguishes the spec's two
independent rejection sources instead of conflating them.

PORTED / OMITTED (see assessment): all five nagini uniqueness rivals and both
soundness positives port 1:1 (this lean bundle models BOTH deducers, so parity
is achievable rather than narrowed), and three further rivals plus a second
admissibility positive are added here beyond nagini parity. The nagini
admissibility case ports as a proof-region ground ``have`` (there is no
precondition binder — the deducers are unguarded — so the analogue is
discharging the spec predicate at the realised record, by kernel EVALUATION,
before the frozen obligation) and is carried for BOTH obligations.
Frame/permission-mutation is VACUOUS here (referential transparency + the
functions take no input at all). The divergence lane is NOT shippable, but not
for the reason first recorded: a diverging rival IS expressible and IS rejected
(see the DIVERGENCE entry above for the four builds), and what blocks it is that
no witness both holds of it and fails on gold — the unconditional shape is
``witness-unproven``, the conditioned shape is ``witness-vacuous``. That is a
known hole in the witness rule for rivals whose wrong field is an OPAQUE term,
adjacent to the ``partial`` findings recorded in
``the corpus-wide termination-semantics finding``. The
AXIOM_TESTS lane is dropped (this bundle declares no ``axiom``/opaque callee —
``consistentTheory`` is a deep-model reference validated out of band by G-CONF,
not this gate's job).

AXIOM lane: EMPTY. No consumed axioms and no opaque callee; the containment
theory is modeled directly over the record's fields, so there is no in-model
axiom obligation for the PBT axiom lane to re-discharge. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16597"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region record literals, and the frozen deduceEven proof body, so
# every replacement lands entirely inside the region it means to edit.
_EVEN_GOLD = (
    "def implementation_deduceEven : KB :=\n"
    "  { integer := some true, rational := some true, real := some true,\n"
    "    finite := some true, even := some true, odd := some false,\n"
    "    algebraic := some true, transcendental := some false, irrational := some false,\n"
    "    infinite := none, complex := some true, noninteger := some false,\n"
    "    prime := none, composite := none }"
)

_INF_GOLD = (
    "def implementation_deduceInfinite : KB :=\n"
    "  { integer := some false, rational := some false, real := some true,\n"
    "    finite := some false, even := some false, odd := some false,\n"
    "    algebraic := some false, transcendental := some false,\n"
    "    irrational := some false, infinite := some true, complex := some true,\n"
    "    noninteger := some true, prime := some false, composite := some false }"
)

_EVEN_PROOF = (
    "  unfold problem_spec_deduceEven implementation_deduceEven consistentTheory\n"
    "  refine ⟨?_, ?_⟩ <;> simp"
)

# The frozen `deduceInfinite` proof body, so a positive whose record is assembled
# INDIRECTLY can add its auxiliary constant to the `unfold` list. A variant may
# legitimately reprove; the theorem STATEMENT stays byte-identical either way.
_INF_PROOF = (
    "  unfold problem_spec_deduceInfinite implementation_deduceInfinite "
    "consistentTheory\n"
    "  refine ⟨?_, ?_⟩ <;> simp"
)
_INF_PROOF_UPD = (
    "  unfold problem_spec_deduceInfinite implementation_deduceInfinite "
    "kbAllFalse consistentTheory\n"
    "  refine ⟨?_, ?_⟩ <;> simp"
)

assert _BASE.count(_EVEN_GOLD) == 1, "deduceEven impl region drifted"
assert _BASE.count(_INF_GOLD) == 1, "deduceInfinite impl region drifted"
assert _BASE.count(_EVEN_PROOF) == 1, "deduceEven proof region drifted"
assert _BASE.count(_INF_PROOF) == 1, "deduceInfinite proof region drifted"


# ---------------------------------------------------------------------------
# Rival / positive record literals (each a full impl region; only the impl
# changes, so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# UNIQUENESS — deduceEven with odd = some true. The theory carries
# `even = some true → odd = some false` (the ¬odd direction of even ≡ integer ∧
# ¬odd), so even ∧ odd is inconsistent and consistentTheory REJECTS it.
_EVEN_ODD = _EVEN_GOLD.replace("odd := some false", "odd := some true")

# UNIQUENESS — deduceEven with noninteger = some true. The theory carries
# `integer = some true → noninteger = some false`, so integer ∧ noninteger is
# inconsistent and is REJECTED.
_EVEN_NONINT = _EVEN_GOLD.replace(
    "noninteger := some false", "noninteger := some true")

# NEAR-MISS — deduceEven that leaves finite = none (the pre-patch behaviour).
# The postcondition pins finite = some true AND the theory needs
# `rational = some true → finite = some true`, so this MUST be rejected.
_EVEN_DROP_FIN = _EVEN_GOLD.replace("finite := some true", "finite := none")

# UNIQUENESS — deduceInfinite with complex = some false on a real quantity. The
# theory carries `real = some true → complex = some true`, so a real quantity
# with complex = some false is inconsistent and is REJECTED.
_INF_COMPLEX = _INF_GOLD.replace("complex := some true", "complex := some false")

# NEAR-MISS — deduceInfinite that leaves noninteger = none. The postcondition
# pins noninteger = some true, so this MUST be rejected.
_INF_DROP_NONINT = _INF_GOLD.replace(
    "noninteger := some true", "noninteger := none")

# UNIQUENESS — deduceEven that resolves prime = some true. The postcondition pins
# `prime = none`: parity does not decide primality, and the theory alone would
# ADMIT prime = some true (an even quantity IS an integer, so the containment
# `prime → integer` is satisfied). So this rival is refuted only by the pinned
# `prime = none` clause, which no other case attacks — it is the one direction
# where the theory is silent and the postcondition is doing all the work.
_EVEN_PRIME = _EVEN_GOLD.replace("prime := none", "prime := some true")

# UNIQUENESS — deduceEven with algebraic = some false. A rational quantity IS
# algebraic, so the theory's `rational → algebraic` containment refutes it. The
# `algebraic` field is otherwise untouched by any rival, and it is one of the four
# memberships whose boundedness consequent is the instance's behavioural delta.
_EVEN_ALGEBRAIC = _EVEN_GOLD.replace(
    "algebraic := some true", "algebraic := some false")

# UNIQUENESS — deduceEven that resolves composite = some true. The postcondition
# pins `composite = none`. Like _EVEN_PRIME the closure theory ADMITS this record
# (an even quantity is an integer, so the `composite → integer` containment is
# satisfied), so the pinned clause alone carries the rejection. Added by audit
# 2026-08-13: `composite` was the one field of either record that NO rival
# touched, and it is the second of the two trits `problem_spec_deduceEven` pins
# to `none` — so without it that pin was never exercised, while its twin
# (`prime = none`) was.
_EVEN_COMPOSITE = _EVEN_GOLD.replace(
    "composite := none", "composite := some true")

# UNIQUENESS — deduceInfinite that leaves prime = none. `prime` is the one field
# of this record the postcondition does NOT pin, so the refutation must come from
# the theory: `integer = some false → prime = some false`. This is the exact
# mirror of _EVEN_PRIME (there the pin carries it and the theory is silent; here
# the theory carries it and there is no pin), so the pair separates the two
# independent sources of rejection instead of conflating them.
_INF_DROP_PRIME = _INF_GOLD.replace("prime := some false", "prime := none")

# POSITIVE (soundness) — deduceEven that additionally records infinite = some
# false (the record leaves infinite = none). A finite quantity is not infinite;
# the real engine deduces is_infinite = False for an even seed. This is a
# structurally-different, MORE-complete but CORRECT record; the theory admits it
# and every pinned clause still holds, so the frozen proof closes unchanged.
_POS_EVEN = _EVEN_GOLD.replace("infinite := none", "infinite := some false")

# POSITIVE (soundness) — deduceInfinite DERIVED by structure update from an
# auxiliary all-negative fact table (every fact known not to hold), overriding
# only the four facts an unbounded real quantity resolves positively. This is a
# genuinely different CONSTRUCTION, not a re-spelling: the elaborated term is
# `have __src := kbAllFalse; { integer := __src.integer, ... }`, so ten of the
# fourteen fields reach the obligation as PROJECTIONS of another constant rather
# than as literals, and `consistentTheory` must be discharged through that
# indirection. Measured: the frozen proof body does NOT close it (the goal is
# left as un-reduced `kbAllFalse.<field>` projections), so the case additionally
# needs `kbAllFalse` in the `unfold` list — which is exactly why it is a real
# SPEC-TOO-STRONG probe: a faithful correct impl whose record is assembled
# indirectly must still be provable against the frozen obligation.
#
# NOTE (audit 2026-08-13): this replaces a previous "field reorder" positive
# whose record was written with the same fourteen named fields in a permuted
# order. Lean normalises named-field order at elaboration, so that variant's
# `implementation_deduceInfinite` was the BYTE-IDENTICAL elaborated term as the
# frozen one (verified with `#print` under `pp.explicit`: the two bodies are
# equal, and `example : reorderedInf = implementation_deduceInfinite := rfl`
# closes). It therefore re-verified the frozen impl under a different source
# spelling and probed nothing. The claim it made ("confirms the obligation does
# not depend on field order") was true but unfalsifiable on this carrier.
_POS_INF = (
    "def kbAllFalse : KB :=\n"
    "  { integer := some false, rational := some false, real := some false,\n"
    "    finite := some false, even := some false, odd := some false,\n"
    "    algebraic := some false, transcendental := some false,\n"
    "    irrational := some false, infinite := some false, complex := some false,\n"
    "    noninteger := some false, prime := some false, composite := some false }\n"
    "\n"
    "def implementation_deduceInfinite : KB :=\n"
    "  { kbAllFalse with\n"
    "    real := some true, infinite := some true,\n"
    "    complex := some true, noninteger := some true }"
)

# ADMISSIBILITY — the frozen deduceEven impl+statement, with a ground instance
# discharged BEFORE the frozen obligation, proving the realised record satisfies
# the closure theory and the witnessed F2P trit. The deducers carry no
# precondition binder (they are unguarded totals), so nagini's precondition-
# admission probe has no hypothesis to attack; the honest analogue is to
# discharge the spec content at the realised record inside the proof region.
#
# The F2P-shaped facts are discharged by KERNEL EVALUATION (`decide`), NOT by the
# frozen obligation's own `simp`. That distinction is the whole point: `simp` can
# close a goal by rewriting it away, so a `have` closed by the same tactic as the
# obligation adds no independent evidence. `decide` reduces the concrete
# `Option Bool` projections in the kernel and returns `isTrue`, so its success is
# a positive statement that the realised record CARRIES those trit values — the
# analogue, on a total carrier, of showing the obligation is satisfiable at an
# F2P-shaped input rather than vacuously true.
_ADMISS_EVEN_PROOF = (
    "  have _f2p : implementation_deduceEven.finite = some true\n"
    "      ∧ implementation_deduceEven.even = some true\n"
    "      ∧ implementation_deduceEven.odd = some false\n"
    "      ∧ implementation_deduceEven.integer = some true\n"
    "      ∧ implementation_deduceEven.prime = none\n"
    "      ∧ implementation_deduceEven.composite = none := by decide\n"
    "  have _closed : consistentTheory implementation_deduceEven := by\n"
    "    unfold consistentTheory implementation_deduceEven\n"
    "    refine ⟨?_, ?_⟩ <;> simp\n"
    "  have _adm : problem_spec_deduceEven implementation_deduceEven :=\n"
    "    ⟨_closed, _f2p.2.1, _f2p.1, by decide, by decide, _f2p.2.2.2.2.1,\n"
    "      _f2p.2.2.2.2.2⟩\n"
    "  unfold problem_spec_deduceEven implementation_deduceEven consistentTheory\n"
    "  refine ⟨?_, ?_⟩ <;> simp"
)

# ADMISSIBILITY (second obligation) — the same shape on `deduceInfinite`: the
# whole unbounded-real cascade the F2P tests observe for `oo` / `-oo` discharged
# at the realised record by kernel evaluation, before the frozen obligation is
# closed verbatim. Covers the second obligation, which the ported battery left
# without an admissibility positive.
_ADMISS_INF_PROOF = (
    "  have _f2p : implementation_deduceInfinite.finite = some false\n"
    "      ∧ implementation_deduceInfinite.infinite = some true\n"
    "      ∧ implementation_deduceInfinite.noninteger = some true\n"
    "      ∧ implementation_deduceInfinite.integer = some false\n"
    "      ∧ implementation_deduceInfinite.rational = some false\n"
    "      ∧ implementation_deduceInfinite.even = some false\n"
    "      ∧ implementation_deduceInfinite.odd = some false\n"
    "      ∧ implementation_deduceInfinite.algebraic = some false\n"
    "      ∧ implementation_deduceInfinite.transcendental = some false\n"
    "      ∧ implementation_deduceInfinite.irrational = some false\n"
    "      ∧ implementation_deduceInfinite.composite = some false := by decide\n"
    "  unfold problem_spec_deduceInfinite implementation_deduceInfinite "
    "consistentTheory\n"
    "  refine ⟨?_, ?_⟩ <;> simp"
)


def _even(body):
    return _swap(_BASE, _EVEN_GOLD, body)


def _inf(body):
    return _swap(_BASE, _INF_GOLD, body)


def _inf_upd(body):
    """`deduceInfinite` impl swap PLUS the auxiliary constant in the `unfold`.

    A record assembled by structure update reaches the obligation as projections
    of another constant, so the proof body must unfold that constant too. Only
    the tactic body changes; the `theorem correct_deduceInfinite` STATEMENT stays
    byte-identical, which is what `variant_scope` requires.
    """
    return _swap(_swap(_BASE, _INF_GOLD, body), _INF_PROOF, _INF_PROOF_UPD)


def _witness(fn):
    """`¬ problem_spec_fn implementation_fn`, closed after unfolding.

    Because the rival and the frozen solution define `implementation_fn` as
    DIFFERENT record constants, this same text holds of the rival (the spec is
    violated at its record) and fails on gold (gold's record satisfies the
    spec). `decide` cannot build a `Decidable` for the implication-laden
    `consistentTheory`, so `simp` reduces the projections and the false clause.
    """
    return (
        f"example : ¬ problem_spec_{fn} implementation_{fn} := by\n"
        f"  unfold problem_spec_{fn} implementation_{fn} consistentTheory\n"
        f"  simp"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally-different but CORRECT
    # records that MUST verify. If a faithful correct impl cannot satisfy the
    # frozen obligation the spec is SPEC-TOO-STRONG. The `correct_<name>`
    # STATEMENT is byte-identical and the frozen proof body is unchanged (both
    # records satisfy the same closed predicate); no helper lemma, axiom, or
    # assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-even-more-complete",
        "kind": "soundness",
        "expect": "verify",
        "module": _even(_POS_EVEN),
        "rationale": (
            "a correct, MORE-complete deduceEven that additionally records "
            "`infinite = some false` (the frozen record leaves it `none`) — a "
            "finite quantity is not infinite, exactly what the real engine "
            "deduces for an even seed. The closure theory admits it and every "
            "pinned clause (`even`/`finite`/`transcendental`/`irrational` and "
            "`prime`/`composite = none`) still holds, so the frozen proof closes "
            "unchanged. Must verify else SPEC-TOO-STRONG. No new "
            "declaration/axiom/assumption token."
        ),
    },
    {
        "id": "pos-infinite-structure-update",
        "kind": "soundness",
        "expect": "verify",
        "module": _inf_upd(_POS_INF),
        "rationale": (
            "deduceInfinite DERIVED by structure update from an auxiliary "
            "all-negative fact table, overriding only the four facts an "
            "unbounded real quantity resolves positively (`real`, `infinite`, "
            "`complex`, `noninteger`). Same VALUE as the frozen record, "
            "genuinely different CONSTRUCTION: the elaborated term is "
            "`have __src := kbAllFalse; { integer := __src.integer, ... }`, so "
            "ten of the fourteen fields arrive at the obligation as projections "
            "of another constant instead of as literals, and `consistentTheory` "
            "must be discharged through that indirection (the tactic body adds "
            "`kbAllFalse` to the `unfold` list; the theorem STATEMENT is "
            "byte-identical and no new declaration/axiom/assumption token "
            "appears). Must verify else SPEC-TOO-STRONG — a faithful correct "
            "impl that assembles its table indirectly rather than as one literal "
            "must still satisfy the frozen obligation. Replaces a prior "
            "field-reorder variant that Lean elaborated to the byte-identical "
            "frozen term and so probed nothing."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the realised record. The frozen theorem
    # carries no precondition hypothesis (the deducers are unguarded totals), so
    # nagini's precondition-admission probe has no binder to attack; the honest
    # analogue discharges the closure theory and the witnessed F2P trit at the
    # realised record inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-even",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _EVEN_PROOF, _ADMISS_EVEN_PROOF),
        "rationale": (
            "before the frozen obligation, the F2P-observed trits of the realised "
            "record (`finite = some true` — the instance's central delta — plus "
            "`even`/`odd`/`integer` and `prime`/`composite = none`) are discharged "
            "by KERNEL EVALUATION (`decide`), and the whole spec predicate is then "
            "assembled as a `have` from those evaluated facts plus the closure "
            "proof, before the frozen obligation is closed verbatim. `decide` "
            "rather than the obligation's own `simp` on purpose: `simp` can close "
            "a goal by rewriting it away, so a ground instance closed by the same "
            "tactic as the obligation adds no independent evidence, whereas "
            "`decide` reducing to `isTrue` positively states the record CARRIES "
            "those trit values. On a total carrier with no precondition binder "
            "this is the analogue of PRECOND-TOO-STRONG: the obligation being "
            "SATISFIABLE at an F2P-shaped input rather than vacuously true. "
            "Nothing is assumed: the STATEMENT is byte-identical, the ground "
            "instance is a `have` inside the existing tactic body, no new "
            "declaration/axiom/`sorry`."
        ),
    },
    {
        "id": "admiss-infinite",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INF_PROOF, _ADMISS_INF_PROOF),
        "rationale": (
            "the same admissibility probe on the SECOND obligation, which the "
            "ported battery left uncovered. The entire unbounded-real cascade the "
            "F2P tests observe (`finite = some false`, `infinite`/`noninteger` "
            "true, and the `integer`/`rational`/`even`/`odd`/`algebraic`/"
            "`transcendental`/`irrational`/`composite` memberships false) is "
            "discharged at the realised record by kernel evaluation, then the "
            "frozen obligation is closed verbatim. Verifies, else "
            "`problem_spec_deduceInfinite` is unsatisfiable at the record it is "
            "supposed to describe. STATEMENT byte-identical; no new declaration, "
            "axiom, or assumption token."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong records sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, so a verifying rival would
    # be a true verify-does-not-imply-resolve break rather than an artifact, and
    # (b) a refutation witness pinning the violation at the record it returns.
    # =====================================================================
    {
        "id": "weak-even-odd",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_ODD),
        "refinement": (
            "the real `_assume_rules` has `even ≡ integer & !odd`, so an even "
            "quantity deduces is_odd = False; the F2P `test_other_symbol` asserts "
            "`Symbol('x', even=True).is_odd is False`. A faithful patch whose "
            "engine derived odd = True for an even seed would FAIL that F2P "
            "assertion, so this rival cannot resolve."
        ),
        "rationale": (
            "REJECT from the consistentTheory clause "
            "`even = some true → odd = some false` (the ¬odd direction of "
            "even ≡ integer ∧ ¬odd): a record with even = some true AND "
            "odd = some true is inconsistent with the theory, so "
            "`consistentTheory out` fails and the postcondition rejects it. If it "
            "verifies, the spec does not force ¬odd on an even quantity "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "weak-even-noninteger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_NONINT),
        "refinement": (
            "an even quantity IS an integer, so the real engine gives "
            "is_noninteger = False (a finite integer is not a non-integer). An "
            "engine deducing noninteger = True for an integer contradicts the "
            "assumptions consistency the F2P suite relies on, so such a patch "
            "cannot resolve."
        ),
        "rationale": (
            "REJECT from the consistentTheory clause "
            "`integer = some true → noninteger = some false` (the reverse-"
            "direction exclusion of noninteger ≡ real ∧ ¬integer): integer = "
            "some true with noninteger = some true is inconsistent, so "
            "`consistentTheory out` fails. Distinct from weak-even-odd (a "
            "different theory edge, a different field of the record). If it "
            "verifies, the spec leaves the integer/noninteger exclusion unpinned "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "weak-infinite-complex",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _inf(_INF_COMPLEX),
        "refinement": (
            "the real engine gives S.Infinity.is_complex is True (real → "
            "complex); every real seed deduces is_complex = True. A patch whose "
            "engine left/derived complex = False for a real quantity would "
            "contradict the real engine on every real seed, so it cannot resolve."
        ),
        "rationale": (
            "REJECT from the consistentTheory clause "
            "`real = some true → complex = some true`: an unbounded real with "
            "complex = some false is inconsistent with the theory, so "
            "`consistentTheory out` fails. Attacks the deduceInfinite obligation "
            "(a distinct predicate and record from the deduceEven rivals). If it "
            "verifies, the spec does not force complex on a real quantity "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceInfinite"),
    },

    # ---- supporting near-miss rejects (a pinned clause is load-bearing) ----
    {
        "id": "nm-even-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_DROP_FIN),
        "refinement": (
            "leaving finite = none reproduces the PRE-PATCH behaviour; the F2P "
            "`test_other_symbol` asserts `Symbol('x', even=True).is_finite is "
            "True`, which the pre-patch engine (returning None) fails. This is "
            "exactly the bug the instance fixes."
        ),
        "rationale": (
            "REJECT from the pinned clause `finite = some true` AND the "
            "consistentTheory clause `rational = some true → finite = some true`: "
            "a record leaving finite = none violates both. Confirms the central "
            "`finite` clause is load-bearing (prepatch parity). If it verifies, "
            "the spec does not pin the boundedness fact (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "weak-even-prime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_PRIME),
        "refinement": (
            "parity does not decide primality: the real engine leaves is_prime "
            "undetermined for a bare `even` seed (2 is prime, 4 is not, and both "
            "are even), so a patch whose engine resolved is_prime = True from "
            "parity alone would contradict it on every even non-prime and could "
            "not resolve the suite."
        ),
        "rationale": (
            "REJECT from the PINNED clause `prime = none` alone. This is the one "
            "rival the closure theory does NOT refute: an even quantity is an "
            "integer, so `prime = some true` satisfies the `prime → integer` "
            "containment and `consistentTheory` ADMITS this record (machine-"
            "checked: an exhaustive enumeration of all 3^14 fact tables shows the "
            "theory alone leaves `prime` free here, and only the postcondition's "
            "`prime = none` excludes it). It therefore probes a clause no other "
            "case reaches, and separates 'the theory rejects it' from 'the "
            "postcondition pins it'. If it verifies, the spec lets a deducer "
            "invent a primality fact parity cannot support (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "weak-even-algebraic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_ALGEBRAIC),
        "refinement": (
            "a rational quantity is algebraic (it is a root of a degree-one "
            "polynomial over the integers); the real engine deduces is_algebraic "
            "= True for every rational seed, so an engine resolving it False for "
            "an even quantity contradicts the engine on every rational seed."
        ),
        "rationale": (
            "REJECT from the consistentTheory clause "
            "`rational = some true → algebraic = some true`. Attacks the "
            "`algebraic` field, which no other rival touches and which is one of "
            "the four memberships whose boundedness consequent is this instance's "
            "behavioural delta — so it also exercises the `algebraic → finite` "
            "edge's antecedent. If it verifies, the spec does not force "
            "algebraicity on a rational quantity (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "weak-even-composite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _even(_EVEN_COMPOSITE),
        "refinement": (
            "parity does not decide compositeness either: 2 is even and NOT "
            "composite while 4 is even and composite, so the real engine leaves "
            "is_composite undetermined for a bare `even` seed. A patch whose "
            "engine resolved is_composite = True from parity alone would "
            "contradict it at every even prime, so it cannot resolve the suite."
        ),
        "rationale": (
            "REJECT from the PINNED clause `composite = none` alone. Like "
            "weak-even-prime the closure theory ADMITS this record — an even "
            "quantity IS an integer, so the `composite → integer` containment is "
            "satisfied and `consistentTheory` cannot refute it (machine-checked "
            "by the same exhaustive 3^14 enumeration: with `composite` freed the "
            "theory has a model, and only the postcondition excludes it). Added "
            "because `composite` was the one field of either record that no rival "
            "varied, leaving the SECOND of the two `none` pins in "
            "`problem_spec_deduceEven` unexercised while its twin `prime = none` "
            "was attacked twice. If it verifies, the spec lets a deducer invent a "
            "compositeness fact parity cannot support (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceEven"),
    },
    {
        "id": "nm-infinite-drop-prime",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _inf(_INF_DROP_PRIME),
        "refinement": (
            "the F2P `test_infinity` asserts `oo.is_prime is False` (it is one of "
            "the assertions the suite already carried before this change); a "
            "patch leaving it None fails that assertion."
        ),
        "rationale": (
            "REJECT from the consistentTheory clause "
            "`integer = some false → prime = some false`. The exact MIRROR of "
            "weak-even-prime: `prime` is the one field of this record the "
            "postcondition does not pin, so here the theory alone must carry the "
            "refutation, where in weak-even-prime the pin alone must. The pair "
            "separates the spec's two independent rejection sources on the same "
            "field. If it verifies, the theory's `¬integer → ¬prime` "
            "contrapositive is not load-bearing (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceInfinite"),
    },
    {
        "id": "nm-infinite-drop-noninteger",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _inf(_INF_DROP_NONINT),
        "refinement": (
            "leaving noninteger = none fails the F2P `test_infinity` "
            "(oo.is_noninteger is True) and `test_neg_infinity`; a patch leaving "
            "it None cannot resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `noninteger = some true`: a record "
            "leaving noninteger = none violates it. Confirms the cascade's "
            "noninteger clause is load-bearing. If it verifies, the spec leaves "
            "the noninteger fact unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("deduceInfinite"),
    },
]


# No consumed axioms and no opaque callee: the containment theory is modeled
# directly over the record's fields (a deep-model reference validated == the
# real engine by G-CONF out of band), so there is no in-model axiom obligation
# for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
