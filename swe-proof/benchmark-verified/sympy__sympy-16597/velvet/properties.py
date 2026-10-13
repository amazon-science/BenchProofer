"""properties.py — G-PBT falsification battery for sympy__sympy-16597 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct deduceEven`` / ``prove_correct deduceInfinite`` obligations
survive with byte-identical statements) and swaps in a candidate implementation,
checked by the real verifier. ``expect="verify"`` passes iff (in scope AND
verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: it must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (two contracted queries over the empty input domain):

  deduceEven return (out : KB)
    ensures consistentTheory out
    ensures out.even = some true
    ensures out.finite = some true
    ensures out.transcendental = some false
    ensures out.irrational = some false
    ensures out.prime = none
    ensures out.composite = none

  deduceInfinite return (out : KB)
    ensures consistentTheory out
    ensures out.infinite = some true      ensures out.real = some true
    ensures out.finite = some false        ensures out.rational = some false
    ensures out.integer = some false       ensures out.even = some false
    ensures out.odd = some false           ensures out.algebraic = some false
    ensures out.transcendental = some false
    ensures out.irrational = some false    ensures out.composite = some false
    ensures out.noninteger = some true

Each query returns a fresh ``KB`` record of trits (``Option Bool``) — the closed
fact table for one seeded numeric quantity. ``consistentTheory`` is a GROUNDED
predicate over the record's OWN fields (a spelled-out conjunction of containment
clauses and their contrapositives); there is no opaque answer-key oracle to echo
(the ``axioms`` region is empty), so the ungrounded-oracle-echo class is N/A —
here an "echo" is just a correct record. The load-bearing behaviour under
specification is the boundedness cascade: a quantity in a "small" number set is
BOUNDED (``finite``), so an even quantity is finite (the F2P
``Symbol('x', even=True).is_finite is True`` delta), and an unbounded real
resolves the whole rational/algebraic/integer/even/... cascade to false with
``noninteger`` true (the F2P ``S.Infinity`` cascade).

BINDERS. Both queries take NO input and mutate nothing (directive 5): the input
domain is the empty tuple, so there is exactly ONE input point per query and no
input binder to vary. ``pts=1`` per query is therefore STRUCTURAL, not a
coverage gap — there is no argument to move.

CLAUSE COVERAGE — MEASURED, NOT ASSERTED (2026-08-13 audit). What the battery
can cover instead of input points is the independent output-facets of the two
postconditions, and that claim has to be checked rather than stated. It was
checked by enumerating all 3^14 trit tables against a Python transcription of
``consistentTheory`` plus each query's pinned clauses, which partitions the
``ensures`` clauses into two groups:

  * clauses whose violation ALSO breaks ``consistentTheory`` — on deduceEven
    ``finite = some true``; on deduceInfinite ``finite/rational/integer/even/
    odd/algebraic/transcendental/irrational/composite = some false`` and
    ``noninteger = some true``. A rival driving one of these is refuted by the
    closure predicate, so the pinned clause is redundant defence-in-depth.
  * SOLE-DEFENCE clauses, where a single-field deviation keeps
    ``consistentTheory`` TRUE and only the pinned ``ensures`` rejects: on
    deduceEven ``even = some true``, ``transcendental = some false``,
    ``irrational = some false``, ``prime = none``, ``composite = none``; on
    deduceInfinite ``infinite = some true`` and ``real = some true``. Delete one
    of these clauses from the spec and NOTHING else catches the deviation.

The five rivals this battery was ported with all land in the FIRST group: three
are refuted by ``consistentTheory`` alone (``even → ¬odd``, ``integer →
¬noninteger``, ``real → complex``) and two by ``consistentTheory`` together with
a redundant pinned clause. Not one of them exercised a sole-defence clause, so
the pre-audit claim that "every independent top-level clause of each
postcondition is attacked by some rival" was FALSE. Five rivals
(``weak-even-prime-resolved``, ``weak-even-transcendental-unresolved``,
``weak-even-seed-unrecorded``, ``weak-infinite-seed-unrecorded``,
``weak-infinite-real-unrecorded``) were added by that audit to attack the
sole-defence clauses directly; each keeps ``consistentTheory`` satisfied so its
rejection is attributable to exactly one pinned trit.

ADMISSIBLE-RECORD COUNT (same enumeration). deduceInfinite's postcondition pins
12 of 14 fields and the closure forces the rest, so EXACTLY ONE trit table
satisfies it. deduceEven's admits exactly TWO: the frozen table, and the frozen
table with ``infinite := some false`` (the spec leaves ``infinite`` unpinned and
the theory permits either). This bounds what a positive control can be, and both
positives below are written against that bound rather than against a guess.

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's own tester machinery (``deduceEvenTester = false`` /
``deduceInfiniteTester = false`` says the extracted program's returned record
violates the method's postcondition), checked in a file whose ``prove_correct``
blocks have been stripped so no tactic script can mask the verdict. Each query
takes no argument, so its tester is a nullary ``Bool``. The impl is a single
``let``-of-literal record followed by ``return`` — loop-free — so the extracted
program reduces under ``decide`` without getting stuck. The tester was confirmed
to be a TWO-WAY oracle rather than a one-way failure: ``deduceEvenTester = true``
and ``deduceInfiniteTester = true`` both ELABORATE against the frozen solution
(exit 0) and both FAIL against a rival (exit 1), so a ``= false`` refutation that
holds of a rival and fails on gold is deciding the postcondition and not merely
getting stuck. Every gold-side witness failure in this battery is the semantic
form ``Tactic `decide` proved that the proposition <name>Tester = false is
false`` — a refutation of the concrete claim, not a missing identifier, type
error, unfolding failure or timeout. The carrier is fully transparent (every trit
is a concrete ``Option Bool`` literal; the ``axioms`` region is empty), so
witnesses use concrete records and never condition on a hypothesis; each has no
head binder, so the gate's consistency probe is vacuous by construction.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION — VACUOUS. The nagini sibling explicitly records this class as
    N/A already: the deducers take no inputs and hold no read-only fractional
    permission parameter, so there is no caller input to overwrite. This backend
    is additionally referentially transparent (no heap, no aliasing, no ``mut``
    binder, no permission system). No substitute probe is fabricated (per the
    porting map, dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A. ``consistentTheory`` is a fully unfolded ``def``
    over the record's own fields and the pinned trits are concrete literals; the
    ``axioms`` region is empty. There is no answer-key to echo — a correct record
    is the only way to satisfy the post-image, which the positive controls do
    honestly. (The nagini sibling reached the identical conclusion.)
  * SPEC-TOO-WEAK — APPLIES, and carries the reject lane: an engine-contradicting
    trit on a closure edge OR on a sole-defence pinned clause. The ten rivals
    below split five/five across those two groups.
  * SPEC-TOO-STRONG — APPLIES: a structurally-different CORRECT record must still
    verify (the two positive controls).

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. Every frozen impl region is
LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: EMPTY. No ``@ContractOnly`` axioms in the nagini sibling
(``meta.axioms == []``) and no A-consumed deep model; ``consistentTheory`` is an
A-reference validated out of band by ``conformance_check.py`` (G-CONF), which
this gate does not re-run. ``AXIOM_TESTS == []`` (the gate ignores it regardless).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16597"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each is the entire frozen record-return body of one
# ---- deducer; each lies wholly inside that method's single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap). Rivals and positive controls replace the
# ---- whole record so the extracted tester `decide`s over a loop-free program.
_EVEN_IMPL = (
    "    let k : KB :=\n"
    "      { integer := some true, rational := some true, real := some true,\n"
    "        finite := some true, even := some true, odd := some false,\n"
    "        algebraic := some true, transcendental := some false, irrational := some false,\n"
    "        infinite := none, complex := some true, noninteger := some false,\n"
    "        prime := none, composite := none }\n"
    "    return k"
)
assert _BASE.count(_EVEN_IMPL) == 1, "deduceEven impl anchor drift — re-sync _EVEN_IMPL"

_INF_IMPL = (
    "    let k : KB :=\n"
    "      { integer := some false, rational := some false, real := some true,\n"
    "        finite := some false, even := some false, odd := some false,\n"
    "        algebraic := some false, transcendental := some false,\n"
    "        irrational := some false, infinite := some true, complex := some true,\n"
    "        noninteger := some true, prime := some false, composite := some false }\n"
    "    return k"
)
assert _BASE.count(_INF_IMPL) == 1, "deduceInfinite impl anchor drift — re-sync _INF_IMPL"

# The frozen proof bodies (tactic script only; elided from the spec view). Only
# the two cases that genuinely reproof — the admissibility case (extra assert
# goal) and pos-infinite-reshape (a record the frozen script does not close) —
# retune these; every other case leaves them alone.
_EVEN_PROOF = "prove_correct deduceEven by\n  loom_solve\n  unfold consistentTheory; simp"
assert _BASE.count(_EVEN_PROOF) == 1, "deduceEven proof anchor drift"

_INF_PROOF = "prove_correct deduceInfinite by\n  loom_solve\n  unfold consistentTheory; simp"
assert _BASE.count(_INF_PROOF) == 1, "deduceInfinite proof anchor drift"


# ---- rival builders. Each rebuilds one deducer's record with a field override,
# ---- keeping the field order and every other trit at its gold value, then leaves
# ---- the frozen proof script in place (for a reject rival that proof FAILS, which
# ---- is the point: the rejection is attributed to the spec via the witness). The
# ---- record stays a single loop-free literal so its extracted tester `decide`s.
_EVEN_FIELDS = [
    ("integer", "some true"), ("rational", "some true"), ("real", "some true"),
    ("finite", "some true"), ("even", "some true"), ("odd", "some false"),
    ("algebraic", "some true"), ("transcendental", "some false"),
    ("irrational", "some false"), ("infinite", "none"), ("complex", "some true"),
    ("noninteger", "some false"), ("prime", "none"), ("composite", "none"),
]
_INF_FIELDS = [
    ("integer", "some false"), ("rational", "some false"), ("real", "some true"),
    ("finite", "some false"), ("even", "some false"), ("odd", "some false"),
    ("algebraic", "some false"), ("transcendental", "some false"),
    ("irrational", "some false"), ("infinite", "some true"), ("complex", "some true"),
    ("noninteger", "some true"), ("prime", "some false"), ("composite", "some false"),
]


def _record(fields, **over):
    fs = dict(fields)
    for k, v in over.items():
        assert k in fs, f"unknown field {k!r}"
        fs[k] = v
    body = ", ".join(f"{k} := {v}" for k, v in fs.items())
    return ("    let k : KB :=\n"
            f"      {{ {body} }}\n"
            "    return k")


def _even_rival(**over):
    return _swap(_BASE, _EVEN_IMPL, _record(_EVEN_FIELDS, **over))


def _inf_rival(**over):
    return _swap(_BASE, _INF_IMPL, _record(_INF_FIELDS, **over))


# ---- witness preambles. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `<name>Tester = false` says the extracted program's returned record
# ---- violates the method's postcondition. Each query takes no argument, so the
# ---- tester is a nullary `Bool`. Checked in a file whose `prove_correct` blocks
# ---- have been stripped, so no tactic script can mask the verdict. Neither
# ---- witness binds anything, so neither can smuggle in an unsatisfiable
# ---- hypothesis (the gate's consistency probe is `None` for both).
_EVEN_WITNESS = (
    "extract_program_for deduceEven\n"
    "prove_precondition_decidable_for deduceEven\n"
    "prove_postcondition_decidable_for deduceEven\n"
    "derive_tester_for deduceEven\n\n"
    "example : deduceEvenTester = false := by\n  decide\n"
)
_INF_WITNESS = (
    "extract_program_for deduceInfinite\n"
    "prove_precondition_decidable_for deduceInfinite\n"
    "prove_postcondition_decidable_for deduceInfinite\n"
    "derive_tester_for deduceInfinite\n\n"
    "example : deduceInfiniteTester = false := by\n  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify, else the
    # spec is SPEC-TOO-STRONG. What a positive can be here is BOUNDED by the
    # spec: exhaustive enumeration over all 3^14 trit tables shows deduceEven's
    # postcondition admits exactly TWO records and deduceInfinite's exactly ONE.
    # So the two lanes need different constructions, and each is written against
    # that bound.
    # =====================================================================
    {
        "id": "pos-even-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The OTHER admissible record: reverse containment order AND infinite
        # pinned to `some false` instead of left `none`. Not merely reshaped —
        # this returns a record that DIFFERS from the frozen one observably
        # (verified: `poseven ≠ evenTable` closes by `decide`, exit 0, and
        # `poseven = evenTable := rfl` FAILS, exit 1).
        "module": _swap(
            _BASE, _EVEN_IMPL,
            "    let k : KB :=\n"
            "      { complex := some true, algebraic := some true, finite := some true,\n"
            "        real := some true, rational := some true, integer := some true,\n"
            "        even := some true, transcendental := some false, irrational := some false,\n"
            "        infinite := some false, odd := some false, noninteger := some false,\n"
            "        prime := none, composite := none }\n"
            "    return k"),
        "rationale": (
            "a CORRECT deduceEven returning a record that is OBSERVABLY DIFFERENT "
            "from the frozen one, not a re-spelling of it: it pins infinite := "
            "some false where the frozen impl leaves it none (a fact the real "
            "engine deduces for a bounded quantity, which consistentTheory "
            "permits and the postcondition does not pin). Machine-checked to be a "
            "genuinely distinct term: `poseven ≠ evenTable` closes by `decide` "
            "(exit 0) while `poseven = evenTable := rfl` fails (exit 1). By "
            "exhaustive enumeration of all 3^14 trit tables this is the ONLY "
            "other record deduceEven's postcondition admits, so it is the "
            "strongest available soundness probe on this lane. It MUST verify; a "
            "failure would be SPEC-TOO-STRONG (over-fit to the gold field "
            "ordering or to leaving infinite indefinite)."
        ),
    },
    {
        "id": "pos-infinite-reshape",
        "kind": "soundness",
        "expect": "verify",
        # REPLACES the ported `pos-infinite-reorder`, which was VACUOUS: Lean
        # resolves anonymous-constructor fields to DECLARATION order, so that
        # case's "reverse order" record elaborated to the very same `KB.mk`
        # application as the frozen one (verified: `posinf = infiniteTable :=
        # rfl` closes, exit 0; `posinf ≠ infiniteTable := by decide` fails, exit
        # 1). It re-verified the frozen impl under a different spelling and could
        # not have failed. deduceInfinite's postcondition admits exactly ONE
        # record, so no correct rival can differ in VALUE; the available axis is
        # PROGRAM shape. This builds the record by masking two seed trits out of
        # the closed table and re-establishing them through an intermediate
        # `let`, which is real reproof work: the frozen tactic script does NOT
        # close it (exit 1), so the retuned script below is doing the work.
        "module": _swap(
            _swap(
                _BASE, _INF_IMPL,
                "    let seed : KB := { infiniteTable with infinite := none, noninteger := none }\n"
                "    let k : KB := { seed with infinite := some true, noninteger := some true }\n"
                "    return k"),
            _INF_PROOF,
            "prove_correct deduceInfinite by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | simp [consistentTheory, infiniteTable]\n"
            "    | (unfold consistentTheory; simp)"),
        "rationale": (
            "a CORRECT deduceInfinite with a different PROGRAM shape: the record "
            "is assembled by masking the two seed trits (infinite, noninteger) "
            "out of the closed table and re-establishing them through an "
            "intermediate `let`, rather than written as one literal. Exhaustive "
            "enumeration shows this postcondition pins 12 of 14 fields and the "
            "closure forces the rest, so EXACTLY ONE record satisfies it — a "
            "value-distinct correct rival is impossible on this lane, and shape "
            "is the only axis left. The reshape is load-bearing rather than "
            "cosmetic: the frozen tactic script fails on it (exit 1), so the "
            "retuned script is genuinely reproving the obligation. It MUST verify; "
            "a failure would be SPEC-TOO-STRONG (over-fit to the frozen record's "
            "syntactic form). Replaces the ported `pos-infinite-reorder`, whose "
            "field-reordered record elaborated to the SAME term as the frozen one "
            "(`= infiniteTable := rfl`, exit 0) and so tested nothing."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — neither query declares a `require` clause, so the usual "a
    # normal input satisfies the precondition" probe is vacuous (the domain is the
    # empty tuple). The residual admissibility risk on a total domain is that the
    # post-image is UNSATISFIABLE / DEGENERATE at the interesting point — a spec no
    # impl can meet reads exactly like one every impl meets.
    #
    # The ported version asserted its three facts about the frozen CONSTANT
    # `evenTable` and discharged them with `exact ⟨evenTable_consistent, rfl,
    # rfl⟩` — citing a lemma the frozen file already proves (`@[grind] lemma
    # evenTable_consistent`). That restated a frozen fact instead of claiming
    # anything about the impl under test (verified: both conjuncts close against
    # the untouched frozen file, exit 0). Repaired to assert about the impl's OWN
    # returned record `k`, plus the `prime = none` facet, so the claim is about
    # what this variant actually computes. Liveness re-measured on the repaired
    # form: the true claim verifies (exit 0) while `k.finite = some false`,
    # `k.prime = some true` and `k.even = some false` each leave an unsolved goal
    # (exit 1, 1, 1).
    # =====================================================================
    {
        "id": "admiss-even-consistent-finite",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _EVEN_IMPL,
                _EVEN_IMPL.replace(
                    "    return k",
                    "    assert (with_name_prefix `admiss\n"
                    "      (consistentTheory k ∧ k.finite = some true ∧ k.even = some true ∧ k.prime = none))\n"
                    "    return k")),
            _EVEN_PROOF,
            "prove_correct deduceEven by\n"
            "  loom_solve\n"
            "  all_goals (unfold consistentTheory; simp)"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the record the "
            "impl actually returns: the closure theory holds of `k`, the F2P delta "
            "trit finite = some true is realised (with even = some true) rather "
            "than left indefinite (none, the pre-fix value), AND the Unknown facet "
            "prime = none is realised as genuinely undetermined rather than "
            "resolved. Asserted about the impl's OWN `k`, not about the frozen "
            "constant `evenTable` — an assert about that constant would restate "
            "the frozen `evenTable_consistent` lemma and claim nothing about the "
            "variant. The assert is live: the true claim verifies while each of "
            "`k.finite = some false`, `k.prime = some true` and `k.even = some "
            "false` leaves an unsolved goal. The impl is otherwise kept verbatim "
            "so deduceEven's own `ensures` still discharge."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong records sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at the
    # single input point and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each keeps the frozen proof
    # script (which fails on the reshaped record) so the rejection is attributed
    # to the spec via the witness, not to a tactic gap.
    #
    # GROUP 1 — closure rivals. Refuted by `consistentTheory out` itself; the
    # pinned trit clauses are redundant here (defence in depth).
    # =====================================================================
    {
        "id": "weak-even-odd",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that ALSO sets odd = some true.
        "module": _even_rival(odd="some true"),
        "refinement": (
            "the real property engine carries 'even ≡ integer ∧ ¬odd', so an even "
            "quantity deduces is_odd is False; the failing test asserts "
            "Symbol('x', even=True).is_odd is False. A faithful real patch whose "
            "engine produced odd=True for an even seed would FAIL that assertion, "
            "so this rival cannot resolve — a verify here would be a genuine "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from `consistentTheory out`: the theory clause `even = some "
            "true → odd = some false` (the ¬odd direction of even ≡ integer ∧ "
            "¬odd) is contradicted by a record with even = some true AND odd = "
            "some true. Attacks the closure `even → ¬odd` clause. If it verified "
            "=> SPEC-TOO-WEAK (an engine-contradicting odd trit would pass while "
            "the vacuous-antecedent clauses still hold)."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-even-noninteger",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that sets noninteger = some true on an integer.
        "module": _even_rival(noninteger="some true"),
        "refinement": (
            "an even quantity IS an integer, and a bounded integer is not a "
            "non-integer, so the real engine gives is_noninteger is False; the "
            "engine carries integer → ¬noninteger. A real patch deducing "
            "noninteger=True for an even (integer) seed would contradict "
            "integer=True, breaking the assumptions-consistency the passing suite "
            "relies on, so it cannot resolve."
        ),
        "rationale": (
            "REJECT from `consistentTheory out`: the theory clause `integer = some "
            "true → noninteger = some false` (the reverse-direction exclusion of "
            "noninteger ≡ real ∧ ¬integer) is contradicted by a record with "
            "integer = some true AND noninteger = some true. Attacks a distinct "
            "closure clause from weak-even-odd (integer → ¬noninteger vs even → "
            "¬odd). If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-even-drop-finite",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that DROPS finite (leaves it none) — the pre-patch
        # behaviour. Violates both the pinned `finite = some true` clause and the
        # theory clauses `rational = some true → finite = some true` and
        # `algebraic = some true → finite = some true`.
        "module": _even_rival(finite="none"),
        "refinement": (
            "leaving finite indefinite (none) reproduces the PRE-PATCH behaviour "
            "(is_finite returns None for an even symbol); the failing test asserts "
            "Symbol('x', even=True).is_finite is True, which the pre-patch engine "
            "fails. This IS the defect the fix corrects, so a real patch leaving "
            "it None would NOT resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.finite = some true` AND the theory "
            "clauses `rational = some true → finite = some true` / `algebraic = "
            "some true → finite = some true` (both antecedents still hold here). "
            "Attacks the F2P delta of this instance. Enumeration confirms the "
            "closure alone already refutes this record, so the pinned clause is "
            "redundant defence-in-depth rather than the sole defence. If it "
            "verified => SPEC-TOO-WEAK (the whole point of the fix would be "
            "unpinned; prepatch parity)."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-infinite-complex",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceInfinite rival that sets complex = some false on a real quantity.
        "module": _inf_rival(complex="some false"),
        "refinement": (
            "the real engine gives S.Infinity.is_complex is True (a real quantity "
            "is complex); every real seed deduces is_complex=True. A real patch "
            "whose engine left/derived complex=False for a real quantity would "
            "contradict the engine on every real seed and break the passing suite, "
            "so it cannot resolve."
        ),
        "rationale": (
            "REJECT from `consistentTheory out`: the theory clause `real = some "
            "true → complex = some true` is contradicted by an unbounded real with "
            "complex = some false (real is still some true here). Attacks the "
            "real → complex closure clause on the deduceInfinite query — a clause "
            "and query neither even rival reaches. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _INF_WITNESS,
    },
    {
        "id": "weak-infinite-drop-noninteger",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceInfinite rival that DROPS noninteger (leaves it none).
        "module": _inf_rival(noninteger="none"),
        "refinement": (
            "the failing test asserts S.Infinity.is_noninteger is True (an "
            "unbounded real is a non-integer); a real patch leaving it None fails "
            "that assertion, so it cannot resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.noninteger = some true` AND the "
            "theory clause `real = some true ∧ integer = some false → noninteger = "
            "some true` (both antecedents still hold). Attacks the pinned "
            "noninteger trit of the deduceInfinite cascade. Enumeration confirms "
            "the closure alone already refutes it, so this is redundant "
            "defence-in-depth rather than a sole-defence probe. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _INF_WITNESS,
    },

    # =====================================================================
    # GROUP 2 — SOLE-DEFENCE rivals (added by the 2026-08-13 audit). Each keeps
    # `consistentTheory out` SATISFIED and violates exactly ONE pinned trit
    # clause, so its rejection is attributable to that clause and to nothing
    # else. These are the clauses whose deletion from the spec the ported
    # battery would not have noticed; every one is verified to reject with a
    # discriminating witness (rival elaborates, gold semantically refuted).
    # =====================================================================
    {
        "id": "weak-even-seed-unrecorded",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that leaves the SEED trit itself indefinite. Every
        # closure clause still holds (`even = none` fires no antecedent and
        # `integer = some true` is still recorded), so `ensures out.even = some
        # true` is the only thing rejecting it.
        "module": _even_rival(even="none"),
        "refinement": (
            "the failing test asserts Symbol('x', even=True).is_even is True: a "
            "quantity declared even reports its parity. A real patch whose engine "
            "left is_even None for an even-declared symbol would fail that "
            "assertion outright, so it cannot resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.even = some true` ALONE. This is a "
            "SOLE-DEFENCE probe: leaving the seed trit indefinite fires no closure "
            "antecedent, so `consistentTheory out` still HOLDS of this record "
            "(confirmed by enumeration) and the pinned clause is the only defence. "
            "Delete that clause from the spec and nothing else catches a deducer "
            "that forgets to record its own seed. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-even-prime-resolved",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that RESOLVES primality (prime := some false) on a
        # parity-only seed. `prime = some false` fires no closure antecedent
        # (only `prime = some true → integer = some true` and `integer = some
        # false → prime = some false` exist, and integer is some true here), so
        # consistentTheory still holds and `ensures out.prime = none` is the sole
        # defence.
        "module": _even_rival(prime="some false"),
        "refinement": (
            "parity does not decide primality: the reference engine this spec is "
            "validated against (G-CONF, and independently re-checked by the "
            "faithfulness panel over the witnessed deductions) leaves primality "
            "genuinely UNDETERMINED for a parity-only seed — it is not forced "
            "either way, since such a quantity could be 2 or 4. A patch whose "
            "engine resolved is_prime to False for every even quantity would "
            "assert a deduction the real engine does not make, contradicting it on "
            "the even prime, so it is not a faithful realization and cannot "
            "resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.prime = none` ALONE — a "
            "SOLE-DEFENCE probe on the UNKNOWN-preservation facet. `prime = some "
            "false` fires no closure antecedent (integer is still some true), so "
            "`consistentTheory out` HOLDS of this record (confirmed by "
            "enumeration) and no other clause objects. This is the direction the "
            "closure predicate structurally cannot police: a theory of "
            "containments constrains over-claiming memberships, never "
            "over-RESOLVING an undetermined fact. If it verified => SPEC-TOO-WEAK "
            "(a deducer could invent determinacy the engine never deduced)."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-even-transcendental-unresolved",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceEven rival that leaves transcendental indefinite. The closure
        # only constrains transcendental from ITS OWN antecedent
        # (`transcendental = some true → ...`) and from `finite = some false`,
        # neither of which fires here, so consistentTheory holds and the pinned
        # clause is the sole defence.
        "module": _even_rival(transcendental="none"),
        "refinement": (
            "an even quantity is algebraic, and being algebraic excludes being "
            "transcendental, so the real engine RESOLVES is_transcendental to "
            "False for such a seed rather than leaving it None. A patch whose "
            "engine left it indefinite would under-deduce relative to the real "
            "engine on the very small-set membership this instance's boundedness "
            "cascade turns on, so it does not faithfully realise the fixed "
            "behaviour."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.transcendental = some false` "
            "ALONE — a SOLE-DEFENCE probe. The closure constrains transcendental "
            "only from its own `some true` antecedent and from `finite = some "
            "false`, and neither fires for a bounded algebraic record, so "
            "`consistentTheory out` HOLDS here (confirmed by enumeration). "
            "Attacks the under-resolution direction on a small-set membership, "
            "which no closure clause polices. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _EVEN_WITNESS,
    },
    {
        "id": "weak-infinite-seed-unrecorded",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceInfinite rival that leaves the seed trit `infinite` indefinite
        # while keeping the whole cascade (finite = some false etc.) intact. Only
        # `infinite = some true → finite = some false` mentions infinite, and a
        # `none` antecedent does not fire, so consistentTheory still holds.
        "module": _inf_rival(infinite="none"),
        "refinement": (
            "the failing test asserts S.Infinity.is_infinite is True; an unbounded "
            "quantity reports its unboundedness. A real patch whose engine left "
            "is_infinite None for such a quantity would fail that assertion, so it "
            "cannot resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.infinite = some true` ALONE — a "
            "SOLE-DEFENCE probe on the deduceInfinite seed. The only clause "
            "mentioning infinite is `infinite = some true → finite = some false`, "
            "whose antecedent does not fire at `none`, so `consistentTheory out` "
            "HOLDS of this record (confirmed by enumeration) even though the seed "
            "the whole cascade is derived FROM has gone unrecorded. If it verified "
            "=> SPEC-TOO-WEAK."
        ),
        "witness": _INF_WITNESS,
    },
    {
        "id": "weak-infinite-real-unrecorded",
        "kind": "uniqueness",
        "expect": "reject",
        # deduceInfinite rival that leaves `real` indefinite. This also switches
        # OFF the two clauses that would otherwise object (`real → complex` and
        # `real ∧ ¬integer → noninteger`), which is exactly why the pinned clause
        # has to carry it: dropping an antecedent is how a rival buys silence
        # from a closure theory.
        "module": _inf_rival(real="none"),
        "refinement": (
            "the failing test asserts S.Infinity.is_real is True; the modeled "
            "quantity is an unbounded REAL and the engine deduces its realness. A "
            "real patch whose engine left is_real None for it would fail that "
            "assertion, so it cannot resolve."
        ),
        "rationale": (
            "REJECT from the pinned clause `out.real = some true` ALONE — a "
            "SOLE-DEFENCE probe, and the sharpest one in the battery: leaving "
            "`real` indefinite does not merely avoid contradicting the closure, it "
            "DISABLES the two clauses that would have objected (`real → complex` "
            "and `real ∧ ¬integer → noninteger`) by removing their antecedent. "
            "`consistentTheory out` therefore HOLDS (confirmed by enumeration) "
            "while the record silently drops the seed that makes the quantity a "
            "real one. Demonstrates directly why the pinned trits cannot be left "
            "to the closure predicate. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _INF_WITNESS,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals; AXIOM_TESTS empty) over the
# two no-input deducers `deduce_even` / `deduce_infinite`, each returning a KB
# record of trits closed under the containment theory `consistent_theory`. This
# bundle models the SAME two functions with the SAME grounded closure predicate
# (no axiom, no permission surface), so the battery carries across almost
# one-to-one — the only translation is nagini's mutate-a-fresh-record impl style
# to velvet's single record literal, and Viper's automatic postcondition
# discharge to velvet's tester-machinery witnesses (the genuinely new work).
#
#   nagini case                      -> here
#   -----------------------------------------------------------------------
#   pos-even-reorder                 -> pos-even-reorder               PORTED
#   pos-infinite-reorder             -> pos-infinite-reshape           PORTED (re-derived; see below)
#   admiss-even                      -> admiss-even-consistent-finite  PORTED (re-shaped assert)
#   weak-even-odd                    -> weak-even-odd                  PORTED
#   weak-even-noninteger             -> weak-even-noninteger           PORTED
#   weak-infinite-complex            -> weak-infinite-complex          PORTED
#   nm-even-drop-finite              -> weak-even-drop-finite          PORTED
#   nm-infinite-drop-noninteger      -> weak-infinite-drop-noninteger  PORTED
#   (none — new on this carrier)     -> weak-even-seed-unrecorded      ADDED
#   (none — new on this carrier)     -> weak-even-prime-resolved       ADDED
#   (none — new on this carrier)     -> weak-even-transcendental-unresolved ADDED
#   (none — new on this carrier)     -> weak-infinite-seed-unrecorded  ADDED
#   (none — new on this carrier)     -> weak-infinite-real-unrecorded  ADDED
#
# 8 of 8 ported, 5 added by audit (2 positives, 1 admissibility, 10 uniqueness).
# No frame-mutation case existed to drop (the nagini sibling records the class
# N/A — the deducers take no inputs and hold no fractional-permission
# parameter). No divergence case existed (both deducers are straight-line). No
# axiom lane (meta.axioms == []). Nothing was dropped because a proof was hard,
# and nothing is recorded as inexpressible.
#
# PORTED (positives) — RE-DERIVED 2026-08-13. The nagini positives assign the
#   record in reverse containment order. That translation is sound for
#   deduce_even, where reverse order plus the additional engine-deduced negative
#   fact yields a record that genuinely DIFFERS from the frozen one (and is, by
#   enumeration, the only other admissible one). It is NOT sound for
#   deduce_infinite: Lean resolves anonymous-constructor fields to DECLARATION
#   order, so a reordered literal is the SAME TERM, and the ported case
#   re-verified the frozen impl under a different spelling (`= infiniteTable :=
#   rfl` closes, exit 0). Replaced by `pos-infinite-reshape`, which varies
#   PROGRAM shape instead — the only axis available, since that postcondition
#   admits exactly one record — and which the frozen tactic script does not close
#   (exit 1), so its reproof is real work.
# PORTED (re-shaped assert) — REPAIRED 2026-08-13. The nagini admissibility case
#   adds `Assert(consistent_theory(k)); Assert(k.finite is True); Assert(k.even
#   is True)` inside the impl, about the record the impl BUILT. The port pointed
#   the same three facts at the frozen constant `evenTable` and discharged them
#   with `exact ⟨evenTable_consistent, rfl, rfl⟩`, citing a lemma the frozen file
#   already proves — a restatement of frozen facts rather than a claim about the
#   variant. Re-pointed at the impl's own `k` (matching the nagini original) and
#   extended with the `prime = none` Unknown facet; liveness re-measured with
#   three failing negative controls.
# PORTED (uniqueness): each nagini rival drives one KB trit to an
#   engine-contradicting value on one deducer; each carries across verbatim in
#   its attacked field, and each gains a machine-checked witness (the part with
#   no nagini counterpart — Viper discharged the postcondition itself, but a
#   tactic-proof backend needs a concrete discriminator).
# ADDED (uniqueness): the five sole-defence rivals. The nagini sibling had no
#   counterpart because Viper's automatic discharge made the closure-vs-pinned
#   distinction invisible there; on this carrier it is measurable, and measuring
#   it showed all five ported rivals landing on closure clauses. These five
#   attack the pinned clauses that nothing else defends.
#
# WITNESS EVIDENCE. All ten witnesses were rebuilt independently against the
#   rival (elaborates, exit 0) and against the frozen solution (fails, exit 1),
#   and every gold-side failure was read: each is the SEMANTIC form ``Tactic
#   `decide` proved that the proposition <name>Tester = false is false``, i.e. a
#   refutation of the concrete claim, never a missing identifier / type error /
#   stuck reduction / timeout. The tester was additionally shown to be a two-way
#   oracle: `<name>Tester = true` elaborates against gold (exit 0) and fails
#   against a rival (exit 1), so the `= false` claims are being decided rather
#   than merely failing. No witness binds a hypothesis, so none can smuggle in an
#   unsatisfiable side condition.
#
# BINDER / CLAUSE / POINT COVERAGE. Both queries take NO argument, so there is no
#   input binder to vary and each extracted tester is a nullary `Bool`. There is
#   exactly ONE input point per query; `pts=1` per query is STRUCTURAL, not a
#   coverage defect — no distinct input exists to move a witness to, so the
#   coverage tool's "move the witness to a distinguishing input" finding is N/A.
#   What the battery covers instead is the output-facets of the two
#   postconditions, split by what actually does the rejecting:
#     CLOSURE clauses (pinned trit redundant):
#       * deduceEven, `even → ¬odd`                : weak-even-odd
#       * deduceEven, `integer → ¬noninteger`      : weak-even-noninteger
#       * deduceEven, `rational/algebraic → finite`: weak-even-drop-finite (F2P delta)
#       * deduceInfinite, `real → complex`         : weak-infinite-complex
#       * deduceInfinite, `real ∧ ¬integer → noninteger`
#                                                  : weak-infinite-drop-noninteger
#     SOLE-DEFENCE pinned clauses (closure still holds; nothing else objects):
#       * deduceEven, `even = some true`           : weak-even-seed-unrecorded
#       * deduceEven, `prime = none`               : weak-even-prime-resolved
#       * deduceEven, `transcendental = some false`: weak-even-transcendental-unresolved
#       * deduceInfinite, `infinite = some true`   : weak-infinite-seed-unrecorded
#       * deduceInfinite, `real = some true`       : weak-infinite-real-unrecorded
#   The remaining sole-defence clauses on deduceEven (`irrational = some false`,
#   `composite = none`) are NOT separately attacked: each is refuted by the same
#   mechanism as its listed twin (`transcendental = some false` and `prime =
#   none` respectively — same clause shape, same closure-silence reason), so a
#   rival for each was built and confirmed to reject with a discriminating
#   witness during the audit but not shipped, to keep the battery's build cost
#   proportionate. Recorded here rather than left implicit: this is a deliberate
#   bounded omission, not a claim of full coverage.
#   Both modeled queries are attacked (deduceEven by six rivals, deduceInfinite
#   by four) and defended (each by one positive control; deduceEven additionally
#   by the admissibility assert).
#
# AXIOM_TESTS: empty. No axiomatized callee to probe — the containment theory is
#   modeled deeply as `consistentTheory` (an A-reference validated by G-CONF, not
#   an axiom); the axiom lane is G-AX's job and this gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
