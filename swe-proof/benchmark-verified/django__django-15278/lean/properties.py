# properties.py — G-PBT falsification battery for django__django-15278 (lean).
# PORTED from the nagini sibling battery and re-expressed against this backend's
# carrier. NOT a Lean module — a record of adversarial cases the spec-lane gate
# executes, each editing ONLY the impl region (and, for the positives, the proof
# tactic body) of the frozen Solution.lean, so `same_spec` holds by construction
# and every rejection is attributable to the postcondition rather than to a
# tampered spec.
#
# Defended surface (read off the frozen Solution.lean):
#   implementation_requiresTableRebuild (c : ColumnProps) : Bool
#   problem_spec_requiresTableRebuild (c : ColumnProps) (result : Bool) : Prop :=
#       result = (c.isPrimaryKey || c.isUnique || !c.allowsNull
#                 || c.hasStoredDefault)
#   ONE obligation: `theorem correct_requiresTableRebuild : ∀ c, spec c (impl c)`.
#   There is NO precondition hypothesis — the obligation quantifies over the whole
#   16-point `ColumnProps` domain.
#
#   The spec is a SINGLE top-level clause: an equality pinning the returned
#   decision to a four-way disjunction over the four input binders. Because it is
#   an equality (not an implication), it pins the decision in BOTH directions:
#   `true` is forced on every column satisfying any disjunct, and `false` is
#   forced on the column satisfying none. There is no slack: a rival that decides
#   ANY of the 16 columns differently from the disjunction violates the clause.
#
#   INPUT BINDERS (all four are attacked, at both polarities, by the witnesses):
#     isPrimaryKey / isUnique / allowsNull / hasStoredDefault.
#   Note the third binder enters NEGATED (`!c.allowsNull`), so its two polarities
#   are semantically asymmetric and both are probed separately.
#
# CARRIER NARROWING vs the nagini sibling. Nagini models the same decision but
#   reports it as an int route discriminator (1 = reconstruct / 0 = plain in-place
#   add) under a permission-carrying contract with SEVEN postcondition clauses
#   (a 2-valuedness clause, the load-bearing biconditional pin, four
#   one-per-disjunct implications, and the all-constraints-absent converse). Here
#   the whole of that fortification collapses into the ONE `result = (...)`
#   equality, which is exactly as strong: the nagini biconditional was the
#   load-bearing clause and the six others were redundant reinforcement of it.
#   Consequently every nagini value-level rival ports, and each ports to a rival
#   against the same single clause — with a Bool rather than an int carrier.
#
# VACUOUS / NON-PORTED LANES (stated, never fabricated):
#   * FRAME-MUTATION — nagini's MANDATORY rival writes back into an input granted
#     at half permission, and is rejected for insufficient permission. Lean is
#     referentially transparent: there is no aliasing and no fractional
#     permission, so "write to an input" is not an expressible rival. The class is
#     genuinely VACUOUS here, not merely untested. MEASURED rather than asserted:
#     the ported rival (`let mut d := c`, overwrite all four fields of the copy,
#     then return the gold decision computed from the untouched `c`) VERIFIES —
#     exit 0 under the real verifier. There is no frame obligation for it to
#     violate, because the local rebind cannot be observed by any caller. Making
#     the decision READ the mutated copy instead does get rejected, but then it is
#     wrong by VALUE and collapses into the weak-always-rebuild class already
#     covered below, so it adds no lane. Omitted, legitimately.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling carries no such case, and
#     on this backend the class is vacuous anyway: `implementation_*` is a total
#     Lean `def`, so a diverging implementation cannot be written at all. (Unlike
#     velvet under partial termination semantics, where the same rival would be a
#     real spec hole — see the corpus-wide termination-semantics finding.)
#   * UNGROUNDED-ORACLE-ECHO — nagini reports this as N/A because its route is
#     pinned to a helper that COMPUTES from the argument. Same here, and more
#     strongly: the spec's right-hand side is a transparent boolean expression
#     over the four input fields, with NO `opaque` callee and no consumed axiom
#     anywhere in the file. There is no answer-key term an impl could echo, and
#     conversely no opaque term that could block a `decide`-able witness.
#   * AXIOM_TESTS — nagini's two probes cover its single @ContractOnly callee.
#     This bundle abstracts the stored-default observation into the `ColumnProps`
#     input instead of consuming a callee contract (mapping.md: "No consumed
#     callee axiom"; axiom_check.py is a skip stub), so there is nothing to probe.
#     The axiom lane is G-AX's job and this gate ignores it. Dropped, as directed.
#
# WITNESSES. Every reject case carries a Lean `example` asserting the spec
#   predicate is FALSE of the rival at ONE concrete column, checked in a file with
#   the proof obligation stripped so no tactic script can mask the verdict. All
#   four fields are boolean literals, so the carrier computes and `decide` closes
#   the goal outright — no hypothesis binders are needed anywhere in this battery,
#   hence no risk of a `witness-inconsistent` forgery. Each was built against the
#   rival and against the frozen solution before shipping: it elaborates on the
#   rival and FAILS on gold, so it is a real discriminator and not a tautology.
#   The first nine rivals are refuted at NINE DISTINCT columns, and each of the
#   four binders takes both values across that set, so no binder is held fixed.
#   The two audit-lane carve-out rivals reuse two of those nine columns rather
#   than adding new ones, necessarily: each carve diverges from the frozen
#   decision at exactly ONE column, so that column is the only place its witness
#   could be stated. Their contribution is not a new point but a new STRENGTH at
#   an existing one — a rival that agrees with the frozen decision at the other
#   fifteen columns, which forces the clause to be load-bearing pointwise rather
#   than only across a sub-domain.
from pathlib import Path

INSTANCE = "django__django-15278"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl-region def, verbatim (everything the impl markers enclose).
# Every variant _swap()s inside here; the spec view elides the region, so
# same_spec is guaranteed.
_IMPL = """\
def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
    return true
  return false"""

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after `:= by`). Only the positives
# touch it; the reject rivals leave the frozen script alone, since their
# rejection is attested by the witness rather than by the tactic breakage that
# reshaping an impl causes by default.
_PROOF = """\
  intro c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  simp only [Id.run, bind, pure]
  by_cases h : (c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault) = true
  · simp [h]
  · simp only [Bool.not_eq_true] at h
    simp [h]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl-region def replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Full Solution.lean with the impl def AND the proof tactic body replaced.

    The `theorem correct_requiresTableRebuild` STATEMENT stays byte-identical;
    only the tactics after `:= by` change.
    """
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _guard(guard):
    """An impl keeping the frozen control-flow shape with a different decision."""
    return (
        "def implementation_requiresTableRebuild (c : ColumnProps) : Bool := "
        "Id.run do\n"
        f"  if {guard} then\n"
        "    return true\n"
        "  return false"
    )


def _wit(pk, uq, nl, df):
    """A refutation `example`: the spec predicate is FALSE of the rival at this
    concrete column. All four components are literals, so `decide` reduces the
    instance without any opaque term; the statement is unconditional, so there
    are no binders that could be jointly unsatisfiable. Fails against the frozen
    solution, which satisfies the spec at every column."""
    b = (("true" if pk else "false"), ("true" if uq else "false"),
         ("true" if nl else "false"), ("true" if df else "false"))
    rec = "⟨%s, %s, %s, %s⟩" % b
    return (
        f"example : ¬ problem_spec_requiresTableRebuild {rec}\n"
        f"    (implementation_requiresTableRebuild {rec}) := by\n"
        "  unfold problem_spec_requiresTableRebuild "
        "implementation_requiresTableRebuild\n"
        "  decide"
    )


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY, with a proof that actually closes
# for the NEW impl shape and a byte-identical theorem STATEMENT.
# ---------------------------------------------------------------------------

# pos-direct: ports nagini's pos-call-helper. That case routed via a direct call
# to the spec's own decision helper instead of inlining the disjunction; the
# counterpart here is the impl that IS the decision expression, dropping the
# `Id.run do` / early-return scaffolding entirely so the returned value is
# produced by one pure boolean term. It is the cheapest HONEST satisfier of the
# clause (the decision is COMPUTED from the input fields, not asserted), and its
# proof closes by `rfl` because impl and spec right-hand side are now literally
# the same term. If it FAILS => SPEC-TOO-STRONG.
_POS_DIRECT = """\
def implementation_requiresTableRebuild (c : ColumnProps) : Bool :=
  c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault"""

_POS_DIRECT_PROOF = """\
  intro c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  rfl"""

# pos-reorder: ports nagini's pos-disjunct-reorder. The SAME four-way
# disjunction with the operands permuted (stored default first, then
# nullability, then uniqueness, then primary key). Boolean `||` is commutative
# and associative, so the decision is unchanged at all 16 columns; the frozen
# `by_cases`-on-the-gold-guard script no longer applies, so it is reproven by
# destructuring the column and deciding the resulting closed boolean identity
# exhaustively. If it FAILS => SPEC-TOO-STRONG.
_POS_REORDER = _guard(
    "c.hasStoredDefault || !c.allowsNull || c.isUnique || c.isPrimaryKey")

_POS_EXHAUSTIVE_PROOF = """\
  intro c
  obtain ⟨pk, uq, nl, df⟩ := c
  unfold problem_spec_requiresTableRebuild implementation_requiresTableRebuild
  revert pk uq nl df
  decide"""

# pos-plain-first: ports nagini's pos-negated-append-first. Tests the NEGATED
# (plain-column) condition FIRST and returns `false` there, else `true` — a
# mutually-exclusive control-flow reshape with identical semantics, exercising
# the `false` direction of the equality directly. De Morgan makes the two guards
# complementary at every column; reproven exhaustively. If it FAILS =>
# SPEC-TOO-STRONG.
_POS_PLAIN_FIRST = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool := "
    "Id.run do\n"
    "  if !c.isPrimaryKey && !c.isUnique && c.allowsNull "
    "&& !c.hasStoredDefault then\n"
    "    return false\n"
    "  return true"
)

# admiss-total-domain: ports nagini's admiss-reads. There the precondition was
# three half-permission reads and the control confirmed a normal column
# descriptor is in-domain. Here the obligation carries NO precondition
# hypothesis, so the analogous question is whether the obligation is discharged
# over the WHOLE domain rather than only the shapes the frozen script's
# `by_cases` split happens to reach. This case keeps the frozen impl VERBATIM and
# reproves it by destructuring the column and enumerating all 16 assignments
# exhaustively — an admissibility check that no column is excluded from the
# domain the spec must govern. If it FAILS => some column is not actually
# in-domain (PRECOND/DOMAIN-TOO-STRONG).


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each changes ONLY
# the impl region; the frozen proof body is left intact, and the attribution is
# carried by the witness.
# ---------------------------------------------------------------------------

# weak-prepatch: ports nagini's weak-prepatch. Drops BOTH the primary-key and
# uniqueness disjuncts, deciding on nullability and the stored default alone.
_WEAK_PREPATCH = _guard("!c.allowsNull || c.hasStoredDefault")

# weak-drop-unique: ports nagini's weak-drop-unique. Drops ONLY the uniqueness
# disjunct; correct at every column except the uniqueness-bearing, nullable,
# default-free one.
_WEAK_DROP_UNIQUE = _guard(
    "c.isPrimaryKey || !c.allowsNull || c.hasStoredDefault")

# weak-drop-pk: ports nagini's weak-drop-pk. Drops ONLY the primary-key
# disjunct.
_WEAK_DROP_PK = _guard("c.isUnique || !c.allowsNull || c.hasStoredDefault")

# weak-drop-nullable: no nagini counterpart as a standalone case (nagini folds
# this signal into weak-prepatch, which retains it). Added because the third
# binder enters the clause NEGATED and would otherwise be varied by no rival
# built to abuse it specifically: this rival drops ONLY the nullability
# disjunct.
_WEAK_DROP_NULLABLE = _guard(
    "c.isPrimaryKey || c.isUnique || c.hasStoredDefault")

# weak-drop-default: likewise added for binder coverage — drops ONLY the
# stored-default disjunct, the one signal the decision already consulted before
# the two leading disjuncts were introduced.
_WEAK_DROP_DEFAULT = _guard("c.isPrimaryKey || c.isUnique || !c.allowsNull")

# weak-always-rebuild: ports nagini's weak-always-rebuild. Decides
# "reconstruct" for every column, unconditionally.
_WEAK_ALWAYS_REBUILD = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool := "
    "Id.run do\n"
    "  return true"
)

# weak-always-plain: ports nagini's weak-always-append. Decides "plain in-place
# addition" for every column, unconditionally.
_WEAK_ALWAYS_PLAIN = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool := "
    "Id.run do\n"
    "  return false"
)

# weak-swap: ports nagini's weak-swap-route. Computes the CORRECT condition and
# reports the OPPOSITE decision.
_WEAK_SWAP = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool := "
    "Id.run do\n"
    "  if c.isPrimaryKey || c.isUnique || !c.allowsNull "
    "|| c.hasStoredDefault then\n"
    "    return false\n"
    "  return true"
)

# weak-conjunction: no nagini counterpart. Attacks the CONNECTIVE rather than any
# individual disjunct — it requires all four properties at once instead of any
# one of them. Included because a rival that merely drops a disjunct leaves the
# "each condition independently forces reconstruction" reading of the clause
# untested as a whole.
_WEAK_CONJUNCTION = _guard(
    "c.isPrimaryKey && c.isUnique && !c.allowsNull && c.hasStoredDefault")

# weak-carve-default-only: no nagini counterpart. Added by the AUDIT lane. Every
# rival above is wrong on a whole sub-domain described by dropping or rewiring a
# disjunct, so each is refutable at many columns and the witness merely picks
# one. This rival is instead correct on FIFTEEN of the sixteen columns and wrong
# at exactly ONE — the nullable, default-carrying column with neither the
# primary-key nor the uniqueness property — which is the tightest possible
# near-miss on the stored-default disjunct and a strictly harder test of the
# clause than weak-drop-default (that rival is wrong at the same single column
# but reaches it by deleting the disjunct outright, whereas this one keeps the
# full disjunction and carves out the single point).
_WEAK_CARVE_DEFAULT_ONLY = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool :=\n"
    "  if c.isPrimaryKey = false && c.isUnique = false && c.allowsNull = true\n"
    "       && c.hasStoredDefault = true then false\n"
    "  else (c.isPrimaryKey || c.isUnique || !c.allowsNull "
    "|| c.hasStoredDefault)"
)

# weak-carve-maximal: likewise added by the AUDIT lane, and the mirror carve at
# the opposite corner of the domain — correct at fifteen columns and wrong only
# at the maximally constrained one (primary key AND uniqueness-bearing AND
# non-nullable AND defaulted). No other rival in the battery is refutable ONLY
# there, so without it the all-four-properties corner is a point every case
# either decides correctly or reaches incidentally.
_WEAK_CARVE_MAXIMAL = (
    "def implementation_requiresTableRebuild (c : ColumnProps) : Bool :=\n"
    "  if c.isPrimaryKey && c.isUnique && !c.allowsNull && c.hasStoredDefault "
    "then false\n"
    "  else (c.isPrimaryKey || c.isUnique || !c.allowsNull "
    "|| c.hasStoredDefault)"
)


# Shared framing for the reject rationales: what the observable decision means
# and what "does not resolve" means for a faithful real patch.
_R_TAIL = (
    "A faithful real patch with this decision would hand a column that cannot "
    "be appended in place to the plain in-place addition path (or conversely), "
    "so the operation the failing test performs would not be materialized as "
    "the test asserts. It does NOT resolve."
)


SPEC_TESTS = [
    # -------------------- positives --------------------
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_DIRECT, _POS_DIRECT_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl (ports nagini's "
            "pos-call-helper): the decision is returned as one pure boolean "
            "expression over the four input fields, with the `Id.run do` / "
            "early-return scaffolding removed entirely. Every one of the 16 "
            "columns is decided identically to the frozen impl, so the single "
            "spec clause `result = (isPrimaryKey || isUnique || !allowsNull || "
            "hasStoredDefault)` holds by construction; it is the grounded "
            "satisfier of that clause (the value is COMPUTED from the binders, "
            "never asserted). Reproven honestly: the theorem STATEMENT is "
            "byte-identical and the tactic body closes by `rfl`, since impl and "
            "the clause's right-hand side are now the same term. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_REORDER, _POS_EXHAUSTIVE_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl (ports nagini's "
            "pos-disjunct-reorder): the SAME four-way disjunction with its "
            "operands permuted (stored default, nullability, uniqueness, primary "
            "key). Boolean disjunction is commutative and associative, so the "
            "decision agrees with the frozen impl at all 16 columns and the spec "
            "clause is satisfied. The frozen tactic script splits on the gold "
            "guard and no longer applies, so this is reproven by destructuring "
            "the column and deciding the resulting closed boolean identity "
            "exhaustively — the theorem STATEMENT is byte-identical and no "
            "helper lemma or assumption is introduced. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-plain-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_PLAIN_FIRST, _POS_EXHAUSTIVE_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl (ports nagini's "
            "pos-negated-append-first): it tests the NEGATED plain-column "
            "condition FIRST and returns `false` there, else `true` — a "
            "mutually-exclusive branch reshape that exercises the `false` "
            "direction of the spec equality directly. De Morgan makes the two "
            "guards complementary at every column, so the clause holds; "
            "reproven exhaustively over the 16-point domain with the theorem "
            "STATEMENT unchanged. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-total-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(_IMPL, _POS_EXHAUSTIVE_PROOF),
        "rationale": (
            "ports nagini's admiss-reads, whose job was to show a normal column "
            "descriptor is in-domain under the precondition. This obligation "
            "carries NO precondition hypothesis, so the counterpart question is "
            "whether it really is discharged over the WHOLE `ColumnProps` domain "
            "rather than only the shapes the frozen script's case split reaches. "
            "The impl is kept VERBATIM and reproven by destructuring the column "
            "and enumerating all 16 boolean assignments exhaustively, so every "
            "column — including the uniqueness-bearing nullable default-free one "
            "the failing test exercises — is confirmed in-domain and decided as "
            "the clause demands. If it FAILS => the domain the spec governs is "
            "narrower than the carrier claims."
        ),
    },

    # -------------------- rivals: one dropped disjunct each --------------------
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "witness": _wit(1, 1, 1, 0),
        "refinement": (
            "this is the PRE-PATCH behavior: the decision consults only "
            "nullability and the presence of a stored default, omitting both "
            "properties the change introduces. Its faithful real patch is the "
            "unchanged repository, which sends a nullable, default-free, "
            "uniqueness-bearing column down the plain in-place addition path "
            "that this backend cannot express for such a column — exactly the "
            "behavior the single FAIL_TO_PASS test detects. It does NOT resolve; "
            "this is the strongest available refinement (it IS the state the "
            "change moves away from — the same guard, over the same two "
            "observations, as the shipped Solution_prepatch impl region, which "
            "differs from this rival only by an explanatory comment)."
        ),
        "rationale": (
            "REJECTED by the single spec clause `result = (isPrimaryKey || "
            "isUnique || !allowsNull || hasStoredDefault)`, on both the "
            "isPrimaryKey and isUnique binders. Witness: the column "
            "⟨isPrimaryKey := true, isUnique := true, allowsNull := true, "
            "hasStoredDefault := false⟩ — the rival's guard is false so it "
            "returns `false`, while the clause's right-hand side is true. "
            "`decide` closes the negation against the rival and it fails "
            "against gold, so the refutation is attributable to the clause and "
            "not to the frozen tactic script. If it VERIFIES => SPEC-TOO-WEAK "
            "(neither new disjunct is enforced)."
        ),
    },
    {
        "id": "weak-drop-unique",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_UNIQUE),
        "witness": _wit(0, 1, 1, 0),
        "refinement": (
            "dropping ONLY the uniqueness disjunct is the near-miss a real patch "
            "that added the primary-key condition but forgot the uniqueness one "
            "would produce. It decides every column correctly EXCEPT the "
            "uniqueness-bearing but otherwise plain one — which is precisely the "
            "column the FAIL_TO_PASS test adds (nullable, default-free, not the "
            "primary key, uniqueness forced by its relation kind). On that "
            "column the plain in-place addition is attempted and this backend "
            "cannot express it, so the test still fails. It does NOT resolve — "
            "a genuine partial-domain break on the uniqueness sub-domain, and "
            "the tightest such near-miss in this battery. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause on the isUnique binder specifically. "
            "Witness: ⟨false, true, true, false⟩ — the F2P-shaped column, and a "
            "DIFFERENT input from weak-prepatch's (isPrimaryKey is false here), "
            "so this near-miss is refuted at the point where it actually "
            "diverges from gold rather than at a point weak-prepatch already "
            "covers. The rival returns `false`; the clause's right-hand side is "
            "true because of uniqueness alone. If it VERIFIES => SPEC-TOO-WEAK "
            "on the uniqueness sub-domain."
        ),
    },
    {
        "id": "weak-drop-pk",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_PK),
        "witness": _wit(1, 0, 1, 0),
        "refinement": (
            "the dual near-miss: the uniqueness condition is added but the "
            "primary-key one is forgotten. A nullable, default-free, "
            "non-uniqueness-bearing primary-key column is then sent to the plain "
            "in-place addition path, which this backend cannot express for a "
            "primary-key column, so any scenario adding such a column through "
            "this backend breaks. It does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause on the isPrimaryKey binder "
            "specifically. Witness: ⟨true, false, true, false⟩ — isUnique is "
            "false here, so this is a third distinct column, isolating the "
            "primary-key disjunct from the uniqueness one. The rival returns "
            "`false`; the right-hand side is true because of the primary-key "
            "property alone. If it VERIFIES => SPEC-TOO-WEAK on the "
            "primary-key sub-domain."
        ),
    },
    {
        "id": "weak-drop-nullable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_NULLABLE),
        "witness": _wit(0, 0, 0, 0),
        "refinement": (
            "dropping ONLY the nullability disjunct is what a real patch that "
            "introduced the two new conditions while deleting the long-standing "
            "nullability one would do. A non-nullable column with no stored "
            "default, no uniqueness requirement and no primary-key role is then "
            "appended in place, which cannot succeed for a column that forbids "
            "nulls on an existing populated table. It regresses the "
            "already-passing behavior for non-nullable columns while leaving the "
            "new sub-domains correct, so it does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause on the allowsNull binder. This binder "
            "enters the clause NEGATED, and no ported nagini rival attacks it in "
            "isolation (nagini folds it into its pre-patch case, which RETAINS "
            "it), so without this rival the binder would be varied by no witness "
            "built to abuse it. Witness: ⟨false, false, false, false⟩ — the "
            "all-properties-absent-but-non-nullable column, a fourth distinct "
            "input and the only witness in the battery at which all four fields "
            "are false. The rival returns `false`; the right-hand side is "
            "true via `!allowsNull`. If it VERIFIES => SPEC-TOO-WEAK on the "
            "nullability sub-domain."
        ),
    },
    {
        "id": "weak-drop-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_DEFAULT),
        "witness": _wit(0, 0, 1, 1),
        "refinement": (
            "dropping ONLY the stored-default disjunct is the other regression "
            "of the pre-existing behavior: a nullable column carrying a stored "
            "default value, with no uniqueness requirement and no primary-key "
            "role, is appended in place even though its default cannot be "
            "materialized and then removed by the restricted in-place statement. "
            "It breaks the already-passing stored-default column paths, so it "
            "does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause on the hasStoredDefault binder. Like "
            "the nullability rival this has no standalone nagini counterpart, "
            "and it is required so that the fourth binder is varied by a witness "
            "built against it. Witness: ⟨false, false, true, true⟩ — a fifth "
            "distinct input, and the first at which hasStoredDefault is true. "
            "The rival returns `false`; the right-hand side is true via the "
            "stored default alone. If it VERIFIES => SPEC-TOO-WEAK on the "
            "stored-default sub-domain."
        ),
    },

    # -------------------- rivals: the decision as a whole --------------------
    {
        "id": "weak-always-rebuild",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_REBUILD),
        "witness": _wit(0, 0, 1, 0),
        "refinement": (
            "ports nagini's weak-always-rebuild: hard-coding reconstruction for "
            "every column is what a real patch that deleted the decision and "
            "always took the expensive path would do. It over-reconstructs the "
            "whole table even for a plain column that the restricted in-place "
            "addition handles perfectly well — the cheap path the change "
            "deliberately preserves — changing the observable behavior of the "
            "untouched branch and breaking the already-passing plain-column "
            "paths. It does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the `false` direction of the spec equality, which the "
            "one-dropped-disjunct rivals cannot reach: they only ever "
            "under-decide. Witness: ⟨false, false, true, false⟩ — the unique "
            "plain column (nothing set, nulls permitted), a sixth distinct "
            "input. The rival returns `true` while the clause's right-hand side "
            "is false. If it VERIFIES => SPEC-TOO-WEAK (the plain-column "
            "decision is unpinned and the equality is really only an "
            "implication)."
        ),
    },
    {
        "id": "weak-always-plain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS_PLAIN),
        "witness": _wit(1, 1, 0, 1),
        "refinement": (
            "ports nagini's weak-always-append: hard-coding the plain in-place "
            "addition for every column is what a real patch that deleted the "
            "decision in the other direction would do. It attempts the "
            "restricted in-place statement for EVERY column, including the "
            "primary-key, uniqueness-bearing, non-nullable and defaulted ones it "
            "cannot express — failing the FAIL_TO_PASS test and every "
            "already-passing path that adds a constrained column. It does NOT "
            "resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the `true` direction of the spec equality. Witness: "
            "⟨true, true, false, true⟩ — a maximally constrained column, a "
            "seventh distinct input and the only one in the battery at which ALL "
            "FOUR disjuncts hold at once, so the rival is refuted where its "
            "error is most flagrant rather than at a boundary. The rival returns "
            "`false` while the right-hand side is true. If it VERIFIES => "
            "SPEC-TOO-WEAK (the reconstruction decision is unpinned)."
        ),
    },
    {
        "id": "weak-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "witness": _wit(0, 1, 0, 1),
        "refinement": (
            "ports nagini's weak-swap-route: this computes the CORRECT condition "
            "and reports the OPPOSITE decision, as a real patch that wired the "
            "two branches backwards would. Every column then takes the wrong "
            "path — plain columns get reconstructed and constrained columns get "
            "an in-place addition the backend cannot express — so it fails the "
            "FAIL_TO_PASS test and the already-passing plain-column paths alike. "
            "It does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec equality at EVERY column, since the rival's "
            "result is the negation of the required right-hand side throughout; "
            "the equality carrier makes the swap fully observable. Witness: "
            "⟨false, true, false, true⟩ — an eighth distinct input, chosen away "
            "from the other rivals' points to show the refutation does not "
            "depend on any particular binder combination. The rival returns "
            "`false` where the right-hand side is true. If it VERIFIES => "
            "SPEC-TOO-WEAK (the decision is not pinned to its polarity)."
        ),
    },
    {
        "id": "weak-conjunction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CONJUNCTION),
        "witness": _wit(1, 0, 1, 1),
        "refinement": (
            "no nagini counterpart: this attacks the CONNECTIVE rather than any "
            "one property, requiring all four at once instead of any one of "
            "them. A real patch that combined the conditions conjunctively would "
            "reconstruct the table only for a column that is simultaneously the "
            "primary key, uniqueness-bearing, non-nullable and defaulted, and "
            "would take the plain in-place path for every realistic constrained "
            "column — including the FAIL_TO_PASS column. It does NOT resolve. "
            + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause's independence reading: each property "
            "alone forces reconstruction. A rival that merely drops one disjunct "
            "leaves that reading untested as a whole, which is why this case "
            "exists. Witness: ⟨true, false, true, true⟩ — a ninth distinct "
            "input, deliberately one where TWO of the four disjuncts "
            "(isPrimaryKey and hasStoredDefault) would individually suffice yet "
            "the conjunction still fails, so the "
            "refutation cannot be read as a boundary artifact. The rival returns "
            "`false` while the right-hand side is true. If it VERIFIES => "
            "SPEC-TOO-WEAK (the disjuncts are not independently load-bearing)."
        ),
    },

    # ---------------- rivals: single-column carve-outs (audit lane) ----------
    {
        "id": "weak-carve-default-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CARVE_DEFAULT_ONLY),
        "witness": _wit(0, 0, 1, 1),
        "refinement": (
            "added by the audit lane as the TIGHTEST near-miss the battery can "
            "state: the decision keeps the full four-way disjunction and carves "
            "out a single column, the nullable default-carrying one with neither "
            "the primary-key nor the uniqueness property. It is correct at "
            "fifteen of the sixteen columns, so it is the closest a wrong "
            "decision can come to the required one while still being wrong. A "
            "real patch shaped like this appends that column in place, where the "
            "stored default cannot be materialized and then dropped by the "
            "restricted statement, so the stored-default column paths that "
            "already passed regress. It does NOT resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause on the hasStoredDefault binder at the "
            "ONE column where this rival diverges. It shares weak-drop-default's "
            "witness column ⟨false, false, true, true⟩ deliberately: that is the "
            "only point at which either rival is refutable, and the two reach it "
            "differently — weak-drop-default deletes the disjunct (wrong on the "
            "whole stored-default sub-domain as soon as the other three are "
            "absent), whereas this one retains the disjunct and excludes exactly "
            "that column, so the clause has to be load-bearing POINTWISE and not "
            "merely sub-domain-wise. If it VERIFIES => SPEC-TOO-WEAK (the clause "
            "constrains sub-domains but leaves an individual column unpinned)."
        ),
    },
    {
        "id": "weak-carve-maximal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CARVE_MAXIMAL),
        "witness": _wit(1, 1, 0, 1),
        "refinement": (
            "the mirror carve-out at the opposite corner of the domain, also "
            "added by the audit lane: correct at fifteen columns and wrong only "
            "at the maximally constrained one — primary key AND uniqueness- "
            "bearing AND non-nullable AND defaulted. A real patch shaped like "
            "this sends the single most constrained column to the plain in-place "
            "path, the one column for which that statement is least expressible, "
            "while handling every less-constrained column correctly. It does NOT "
            "resolve. " + _R_TAIL
        ),
        "rationale": (
            "REJECTED by the spec clause at the all-four-properties column. It "
            "shares weak-always-plain's witness ⟨true, true, false, true⟩ because "
            "that is this rival's only divergence, but the two are not "
            "interchangeable: weak-always-plain is wrong at fifteen columns and "
            "would be caught by almost any witness, while this rival agrees with "
            "the frozen decision everywhere EXCEPT there. Together with "
            "weak-carve-default-only it pins the two corners of the domain "
            "pointwise. If it VERIFIES => SPEC-TOO-WEAK (the maximally "
            "constrained column is not actually pinned by the equality)."
        ),
    },
]
