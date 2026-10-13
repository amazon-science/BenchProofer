# properties.py — G-PBT falsification battery for django__django-13128 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival and
# FAILS on the frozen solution, so the rejection is attributable to the spec and not
# to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   resolveKind : ExprKind → Connector → Option FieldType → Option FieldType → ExprKind
#   Resolving an arithmetic combination of two operands sorts it into one of three
#   KINDS purely from the combination's current kind, the operator, and the two
#   operands' value-types. The single postcondition `problem_spec_resolveKind` pins
#   the result to the total decision function `classifyKind`, whose independent
#   dispatch clauses are:
#     (D-guard) an ALREADY-specialized combination (`selfKind ≠ combined`) keeps its
#               own kind — the reclassification guard; the operand types/operator are
#               not consulted.
#     (D-dur)   an ordinary combination becomes `duration` exactly when one operand
#               (and NOT the other) has the duration value-type — the disjunction
#               `lhsType = some duration ∨ rhsType = some duration` AND the inequality
#               `lhsType ≠ rhsType` both hold.
#     (D-tmp)   an ordinary combination becomes `temporal` exactly when the operator
#               is subtraction AND both operands share one date/datetime/time type
#               (`connector = sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType`).
#     (D-fall)  otherwise it stays `combined`.
#   classifyKind and isDateTimeField are total, transparent functions over the finite
#   inductive carriers (no opaque callee, no answer-key), so witnesses need no
#   conditioning on the carrier — `decide` reduces them at any concrete input.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled the same decision as
# an integer kind code (K_PLAIN/K_DURATION/K_TEMPORAL) computed from four scalar args
# (two bool, two int type codes in 0..5). This backend models it directly over three
# finite inductives — ExprKind, Connector, Option FieldType — a faithful bijection
# (see mapping.md). The four nagini uniqueness rivals port one-for-one onto the four
# dispatch clauses:
#   * nagini `weak-drop-duration-neq-guard`  -> weak-drop-neq  (attacks D-dur's `≠`).
#   * nagini `weak-drop-already-temporal-guard` -> weak-drop-guard (attacks D-guard).
#   * nagini `weak-drop-sub-requirement`     -> weak-drop-sub  (attacks D-tmp's `sub`).
#   * nagini `weak-const-plain-prepatch`     -> weak-const-combined (attacks D-dur/D-tmp
#       together; this is the literal pre-patch behaviour).
# Those four leave D-tmp's THIRD conjunct — the date/datetime/time family test — unpinned,
# so weak-drop-family is added here (no nagini ancestor; found by auditing which conjunct
# no rival varies). The three nagini positive controls (branch reorder / direct helper /
# local-predicate reshape) port as below, and the RESULT half of the nagini admissibility
# case ports as admiss-f2p-temporal-nondegenerate.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (the nagini docstring's #1 weakness class, explicitly declared
#     structurally inapplicable there too: every parameter is an immutable scalar with
#     no Acc(x,1/2) heap reference). Lean is referentially transparent — there is no
#     aliasing and no fractional permission to overwrite — so a "store into a read-only
#     input" rival is not expressible and the lane is VACUOUS here. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. The nagini sibling carries NO diverge-*/nonterm-*
#     case (its impl body is straight-line, no MustTerminate probe). On lean
#     `implementation_resolveKind` is a total Lean `def` anyway; a non-terminating
#     implementation cannot be written at all, so the class is genuinely VACUOUS (NOT
#     the velvet-partial known-spec-hole disposition). See 'assessment'.
#   * PRECONDITION ADMISSIBILITY (the DOMAIN half of nagini's `admiss-f2p-datetime-sub`,
#     which established T_UNKNOWN <= t <= T_OTHER on the F2P-shaped input). This half
#     does not port: `Option FieldType` is exactly the 0..5 enumeration nagini's Requires
#     admits (five constructors + none), so every input is in-domain by construction and
#     the lean obligation carries NO precondition hypothesis. There is nothing that could
#     be PRECOND-TOO-STRONG. The RESULT half of that case (its `Assert` that the
#     F2P-shaped input classifies as the temporal-subtraction kind) DOES port and is
#     carried as `admiss-f2p-temporal-nondegenerate` below. See 'assessment'.
#   * AXIOM_TESTS (nagini's `ax-ref-resolved-kind-equals-real-dispatch`). The axiom lane
#     is G-AX's job; this gate ignores it. The dispatch is modeled DEEPLY (classifyKind)
#     over transparent carriers, so there is no consumed axiom here anyway.
from pathlib import Path

INSTANCE = "django__django-13128"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# Each of these lies ENTIRELY inside impl-start/impl-end and is unique in _BASE. The
# whole impl body is a straight-line early-return cascade; these are the exact gold
# lines. The fall-through `return ExprKind.combined` is NOT unique on its own (it also
# ends classifyKind in the pure region), so it is only ever swapped as part of the
# unique whole-body block _IMPL_BODY.
_GUARD = (
    "  if selfKind ≠ ExprKind.combined then\n"
    "    return selfKind\n"
)
_DUR = (
    "  if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)\n"
    "        ∧ lhsType ≠ rhsType then\n"
    "    return ExprKind.duration\n"
)
_TMP = (
    "  if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then\n"
    "    return ExprKind.temporal\n"
)
_FALL = "  return ExprKind.combined\n"
_IMPL_BODY = _GUARD + _DUR + _TMP + _FALL

for _a in (_GUARD, _DUR, _TMP, _IMPL_BODY):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the positives whose reshaped impl the frozen `simp only [Id.run, bind, pure]` no
# longer closes; each reproof keeps the theorem STATEMENT byte-identical and introduces
# no new axiom/lemma/sorry.
_PROOF = (
    "  intro selfKind connector lhsType rhsType\n"
    "  unfold problem_spec_resolveKind implementation_resolveKind classifyKind\n"
    "  simp only [Id.run, bind, pure]\n"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"

# The reproof used by the reorder / local positives: after unfolding, split the finite
# inductive inputs and discharge each of the 3*2*6*6 leaves by `decide`. Honest, cheap,
# no new lemma.
_REPROOF = (
    "  intro selfKind connector lhsType rhsType\n"
    "  unfold problem_spec_resolveKind implementation_resolveKind classifyKind\n"
    "  simp only [Id.run, bind, pure]\n"
    "  cases selfKind <;> cases connector <;> rcases lhsType with _ | lt <;>\n"
    "    rcases rhsType with _ | rt <;> (try cases lt) <;> (try cases rt) <;> decide\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-reorder: structurally-different but CORRECT impl — the two dispatch
# branches are swapped (the temporal-subtraction branch tested BEFORE the duration
# branch). The two branch guards are MUTUALLY EXCLUSIVE (D-tmp needs lhsType = rhsType,
# D-dur needs lhsType ≠ rhsType), so the reorder is semantically identical on every
# input. The reshaped early-return order means the frozen `simp only` no longer closes,
# so the byte-identical theorem statement is reproven with a per-leaf `decide`. If it
# FAILS => the postcondition is over-fit to the gold branch ORDER => SPEC-TOO-STRONG.
_POS_REORDER = _swap(_swap(_BASE, _DUR + _TMP, _TMP + _DUR), _PROOF, _REPROOF)

# pos-control-direct: the cheapest HONEST impl — directly return the total decision
# function `classifyKind`. The postcondition IS `result = classifyKind …`, and
# classifyKind is GROUNDED in the inputs (a transparent dispatch over finite inductives,
# no opaque answer-key), so this is a correct fully-grounded implementation, not an
# ungrounded-oracle echo. Proof reduces the trivial `Id.run`/`pure`. If it FAILS =>
# SPEC-TOO-STRONG. It also demonstrates the spec is not echo-vulnerable: any WRONG
# constant/reshape fails the equality (the rivals below).
_POS_DIRECT = _swap(
    _swap(_BASE, _IMPL_BODY, "  return classifyKind selfKind connector lhsType rhsType\n"),
    _PROOF,
    "  intro selfKind connector lhsType rhsType\n"
    "  unfold problem_spec_resolveKind implementation_resolveKind\n"
    "  simp only [Id.run, pure]\n",
)

# pos-control-local-accumulator: a data-flow reshape — accumulate the kind into a single
# mutable local via a chained if/else-if and one `return`, instead of the early-return
# cascade. Same logical dispatch (the else-if chain preserves the gold precedence).
# The frozen proof body still closes (the accumulator collapses under
# `simp only [Id.run, bind, pure]`). If it FAILS => SPEC-TOO-STRONG (over-fit to the
# early-return SHAPE).
_POS_LOCAL = _swap(
    _BASE, _IMPL_BODY,
    "  let mut k := ExprKind.combined\n"
    "  if selfKind ≠ ExprKind.combined then\n"
    "    k := selfKind\n"
    "  else if (lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration)\n"
    "        ∧ lhsType ≠ rhsType then\n"
    "    k := ExprKind.duration\n"
    "  else if connector = Connector.sub ∧ isDateTimeField lhsType ∧ lhsType = rhsType then\n"
    "    k := ExprKind.temporal\n"
    "  return k\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits only the impl region; the frozen proof body is left in place
# (it will not close for the reshaped impl, but the gate reads the witness — checked in
# a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-drop-neq: PARTIAL-DOMAIN. Drop the `lhsType ≠ rhsType` conjunct on the duration
# branch. Now ANY operand of duration type dispatches to `duration`, including two
# EQUAL duration operands (duration − duration). Correct on every differing-type input;
# WRONG on the equal-duration sub-domain (D-dur), which gold leaves `combined`.
_RIV_NEQ = _swap(
    _BASE, _DUR,
    "  if lhsType = some FieldType.duration ∨ rhsType = some FieldType.duration then\n"
    "    return ExprKind.duration\n",
)

# weak-drop-guard: PARTIAL-DOMAIN. Drop the already-classified guard (D-guard). An
# expression already sorted into a specialized kind is now RE-classified by the operand
# types/operator — e.g. an already-duration self that is a subtraction of two equal
# date/datetime/time operands becomes `temporal` again. Correct on every ordinary self;
# WRONG on the already-specialized sub-domain, which gold keeps at its own kind.
_RIV_GUARD = _swap(_BASE, _IMPL_BODY, _DUR + _TMP + _FALL)

# weak-drop-sub: PARTIAL-DOMAIN. Drop the `connector = sub` requirement on the temporal
# branch (D-tmp). Now a NON-subtraction combination of two equal date/datetime/time
# operands also dispatches to `temporal`. Correct on every subtraction input; WRONG on
# the non-sub equal-date/time sub-domain, which gold leaves `combined`.
_RIV_SUB = _swap(
    _BASE, _TMP,
    "  if isDateTimeField lhsType ∧ lhsType = rhsType then\n"
    "    return ExprKind.temporal\n",
)

# weak-const-combined: the pre-patch behaviour — always `combined`, performing no
# resolve-time classification at all. Fails D-dur and D-tmp on every input those clauses
# specialize. Cheap supporting baseline carrying the strongest refinement (it IS the
# literal pre-patch code).
_RIV_CONST = _swap(_BASE, _IMPL_BODY, "  return ExprKind.combined\n")

# weak-drop-family: PARTIAL-DOMAIN. Drop the FAMILY-MEMBERSHIP conjunct
# (`isDateTimeField lhsType`) on the temporal branch, keeping both the `sub` operator and
# the two-types-agree requirements. Now ANY subtraction of two operands that share one
# value-type dispatches to `temporal` — including two operands of a non-temporal type, and
# two operands whose value-type cannot be determined. Correct on every input where the
# shared type IS in the date/datetime/time family; WRONG on the equal-non-temporal
# sub-domain (3 of the 216 carrier points), which gold leaves `combined`. This is the third
# conjunct of D-tmp: the other two are attacked by weak-drop-sub (the operator) and, from
# the other side, by weak-drop-neq (the D-dur inequality), leaving the family test as the
# one D-tmp conjunct no other rival unpins.
_RIV_FAMILY = _swap(
    _BASE, _TMP,
    "  if connector = Connector.sub ∧ lhsType = rhsType then\n"
    "    return ExprKind.temporal\n",
)

# admiss-f2p-temporal-nondegenerate: the RESULT half of nagini's `admiss-f2p-datetime-sub`.
# Insert a `have` that discharges the postcondition AT the F2P-shaped input with the
# temporal-subtraction kind SUPPLIED as the result, then close the frozen obligation
# verbatim. The frozen theorem statement is untouched, no new declaration/axiom/sorry is
# introduced, and nothing is assumed — the `have` is proven by reducing the transparent
# decision function. It pins the spec's POSITIVE direction: `problem_spec` is satisfiable
# at the F2P input by the temporal kind, so the D-tmp clause really does demand that kind
# there rather than being satisfiable only vacuously.
_POS_ADMISS = _swap(
    _BASE, _PROOF,
    "  have _ground : problem_spec_resolveKind ExprKind.combined Connector.sub\n"
    "      (some FieldType.datetime) (some FieldType.datetime) ExprKind.temporal := by\n"
    "    unfold problem_spec_resolveKind classifyKind\n"
    "    decide\n"
    + _PROOF,
)


def _wit(sk, co, lt, rt, note):
    """A refutation witness: `¬ problem_spec_resolveKind … (implementation_… …)` at a
    concrete literal input. classifyKind / isDateTimeField are total transparent
    functions over finite inductives, so `decide` reduces both sides. Elaborates
    against a rival that diverges from the spec at this input, and FAILS on gold (which
    satisfies the spec at every input) — SEEN to discriminate both ways."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_resolveKind {sk} {co} {lt} {rt}\n"
        f"    (implementation_resolveKind {sk} {co} {lt} {rt}) := by\n"
        f"  unfold problem_spec_resolveKind implementation_resolveKind classifyKind\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "structurally-different but CORRECT impl: the duration and temporal-"
            "subtraction branches are swapped. Their guards are mutually exclusive "
            "(the temporal branch needs lhsType = rhsType, the duration branch needs "
            "lhsType ≠ rhsType), so the reorder is semantically identical on every "
            "input. The reshaped early-return order breaks the frozen `simp only`, so "
            "the byte-identical theorem statement is reproven with a per-leaf `decide` "
            "over the finite inductive inputs — no new axiom/lemma/sorry. If it FAILS "
            "=> the postcondition is over-fit to the gold branch ORDER => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIRECT,
        "rationale": (
            "the cheapest HONEST impl: directly return the total decision function the "
            "postcondition pins. That function is GROUNDED in the inputs (a transparent "
            "dispatch over finite inductives, no opaque answer-key), so this is a "
            "correct fully-grounded implementation, not an ungrounded-oracle echo. "
            "Proof reduces the trivial monadic wrapper. If it FAILS => SPEC-TOO-STRONG. "
            "Also shows the spec is not echo-vulnerable: any WRONG constant/reshape "
            "fails the equality (see the rivals)."
        ),
    },
    {
        "id": "pos-control-local-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": (
            "data-flow reshape: accumulate the kind into a single mutable local via a "
            "chained if/else-if and one return, instead of the early-return cascade. "
            "The else-if chain preserves the gold precedence, so the dispatch is "
            "identical on every input; the frozen proof body still closes (the "
            "accumulator collapses under `simp only [Id.run, bind, pure]`). If it FAILS "
            "=> SPEC-TOO-STRONG (over-fit to the early-return SHAPE)."
        ),
    },
    {
        "id": "admiss-f2p-temporal-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "ports the RESULT half of the nagini sibling's admissibility case. The frozen "
            "impl and the frozen proof argument, with a `have` inserted that discharges "
            "the postcondition at the F2P-shaped input (an ordinary combination, "
            "subtraction, two operands sharing the datetime value-type) with the "
            "temporal-subtraction kind SUPPLIED as the result. It pins the POSITIVE "
            "direction of clause D-tmp: the spec is satisfiable at that input by exactly "
            "that kind, so the clause demands the specialized kind there rather than being "
            "dischargeable only by the fall-through. Were the D-tmp clause unsatisfiable "
            "at the very input the F2P behavior turns on, the obligation would be "
            "vacuously true there — the analogue of PRECOND-TOO-STRONG. Nothing is "
            "assumed: the theorem statement is byte-identical, no new "
            "declaration/axiom/sorry, and the ground instance is proven by reducing the "
            "transparent decision function. The DOMAIN half of the nagini case does not "
            "port (every input is in-domain by construction on this carrier, so the lean "
            "obligation carries no precondition hypothesis to be too strong)."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-drop-neq",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEQ,
        "refinement": (
            "dropping the operand-types-DIFFER conjunct makes the real patch wrap a "
            "subtraction of two EQUAL duration operands in the duration-arithmetic form "
            "instead of leaving it an ordinary combination. The gold dispatch produces "
            "the duration form only when exactly one operand is a duration and the two "
            "types differ; two equal duration operands are an ordinary duration result. "
            "A faithful patch of this shape changes the SQL emitted for duration−"
            "duration arithmetic and diverges from the post-patch dispatch the F2P "
            "tests observe, so it does NOT resolve — a verifying rival is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause D-dur (the `lhsType ≠ rhsType` conjunct). On two EQUAL "
            "duration operands the spec's decision is `combined`, but the rival returns "
            "`duration`. Witness probes the equal-duration sub-domain the dropped "
            "conjunct exposes. If it VERIFIES => SPEC-TOO-WEAK (the inequality is "
            "unpinned)."
        ),
        # selfKind=combined, non-sub, both operands duration (equal): gold -> combined,
        # rival -> duration.
        "witness": _wit(
            "ExprKind.combined", "Connector.other",
            "(some FieldType.duration)", "(some FieldType.duration)",
            "equal duration operands: gold stays combined, drop-neq rival returns duration",
        ),
    },
    {
        "id": "weak-drop-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_GUARD,
        "refinement": (
            "dropping the already-classified guard makes the real patch RE-classify an "
            "expression that was already sorted into a specialized kind: on the "
            "recursive resolve of a freshly-built specialized wrapper the dispatch would "
            "re-enter and wrap again, defeating the guard whose whole purpose is to stop "
            "that re-entry. A faithful patch without the guard recurses/re-wraps and "
            "does not match the post-patch dispatch — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause D-guard. On an already-specialized combination "
            "(selfKind ≠ combined) the spec's decision is that same kind, but the rival "
            "re-runs the operand-type dispatch and can return a DIFFERENT kind. Witness "
            "varies the selfKind BINDER to an already-duration self that is a subtraction "
            "of two equal datetime operands: gold keeps `duration`, the rival returns "
            "`temporal`. If it VERIFIES => SPEC-TOO-WEAK (the guard is unpinned)."
        ),
        # selfKind=duration (already specialized), sub, datetime==datetime: gold ->
        # duration (keeps its kind), rival -> temporal (re-classifies).
        "witness": _wit(
            "ExprKind.duration", "Connector.sub",
            "(some FieldType.datetime)", "(some FieldType.datetime)",
            "already-specialized self: gold keeps duration, drop-guard rival re-classifies to temporal",
        ),
    },
    {
        "id": "weak-drop-sub",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SUB,
        "refinement": (
            "dropping the subtraction requirement makes the real patch wrap a NON-"
            "subtraction combination of two equal date/datetime/time operands in the "
            "temporal-subtraction form. The gold dispatch produces that form only for "
            "the subtraction operator; a non-subtraction combination of two dates is not "
            "a temporal subtraction and must stay ordinary. A faithful patch would emit "
            "subtraction SQL for a non-subtraction operator and diverge from gold — "
            "verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause D-tmp (the `connector = sub` conjunct). On a NON-"
            "subtraction combination of two equal datetime operands the spec's decision "
            "is `combined`, but the rival returns `temporal`. Witness varies the "
            "connector BINDER to non-sub. If it VERIFIES => SPEC-TOO-WEAK (the operator "
            "requirement is unpinned)."
        ),
        # selfKind=combined, NON-sub, datetime==datetime: gold -> combined, rival ->
        # temporal.
        "witness": _wit(
            "ExprKind.combined", "Connector.other",
            "(some FieldType.datetime)", "(some FieldType.datetime)",
            "non-subtraction of equal datetime operands: gold stays combined, drop-sub rival returns temporal",
        ),
    },
    {
        "id": "weak-const-combined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_CONST,
        "refinement": (
            "always returning the ordinary kind is EXACTLY the pre-patch behaviour: "
            "resolution performed no resolve-time classification, so a subtraction of "
            "two temporal operands never acquired a determinate value-type and the "
            "annotation raised the mixed-types error unless wrapped explicitly. A "
            "faithful patch doing this is the UNCHANGED repo — it fails every F2P test "
            "(the bare temporal subtraction is never specialized). "
            "verify-does-not-imply-resolve; the same failure G-DIFF records for the "
            "prepatch. Cheap supporting baseline carrying the strongest refinement."
        ),
        "rationale": (
            "REJECTED by clauses D-dur and D-tmp. On any combination those clauses "
            "specialize the spec's decision is `duration`/`temporal`, but the rival "
            "always returns `combined`. Witness probes the F2P-shaped temporal-"
            "subtraction sub-domain (subtraction of two equal datetime operands): gold "
            "-> temporal, rival -> combined. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # selfKind=combined, sub, datetime==datetime (the F2P bare datetime subtraction):
        # gold -> temporal, rival -> combined.
        "witness": _wit(
            "ExprKind.combined", "Connector.sub",
            "(some FieldType.datetime)", "(some FieldType.datetime)",
            "F2P datetime subtraction: gold classifies temporal, const rival stays combined",
        ),
    },
    {
        "id": "weak-drop-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FAMILY,
        "refinement": (
            "dropping the family-membership test makes the real patch wrap a subtraction of "
            "two operands of the SAME NON-temporal value-type in the temporal-subtraction "
            "form, which declares a duration value-type. Subtracting two operands of an "
            "ordinary type is an ordinary combination of that type, not a temporal "
            "subtraction: a faithful patch of this shape would give such a combination a "
            "duration value-type and emit temporal-subtraction SQL for it, changing results "
            "for ordinary same-type arithmetic that the passing tests already observe. It "
            "therefore does not resolve — verify-does-not-imply-resolve."
        ),
        "rationale": (
            "REJECTED by clause D-tmp's family conjunct (`isDateTimeField lhsType`). On a "
            "subtraction of two operands sharing a NON-temporal value-type the spec's "
            "decision is `combined`, but the rival returns `temporal`. This is the one D-tmp "
            "conjunct the other rivals leave unpinned: weak-drop-sub attacks the operator "
            "conjunct and weak-drop-neq the D-dur inequality, so without this case a spec "
            "that omitted the family test would pass the whole battery. The witness varies "
            "the value-type BINDERS to a non-temporal type, an input no other case reaches. "
            "If it VERIFIES => SPEC-TOO-WEAK (the family membership is unpinned)."
        ),
        # selfKind=combined, sub, other==other (equal NON-temporal operands): gold ->
        # combined, rival -> temporal.
        "witness": _wit(
            "ExprKind.combined", "Connector.sub",
            "(some FieldType.other)", "(some FieldType.other)",
            "subtraction of two equal non-temporal operands: gold stays combined, "
            "drop-family rival returns temporal",
        ),
    },
]


# No @ContractOnly axioms and no opaque callees: the resolve-time classification
# (classifyKind) and the datetime-family membership test (isDateTimeField) are modeled
# DEEPLY over transparent finite inductives, so the axiom lane is vacuous here and
# belongs to G-AX regardless.
AXIOM_TESTS = []
