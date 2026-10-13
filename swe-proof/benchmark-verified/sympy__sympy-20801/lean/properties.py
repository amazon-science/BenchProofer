# properties.py — PBT falsification battery for sympy__sympy-20801 (lean).
#
# NOT a Lean module: a manifest of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Every case is a full
# Solution.lean built by region surgery — it edits ONLY the impl region (and,
# for the reshaped soundness positive, the proof body), so the frozen spec
# (axioms / pure / post-conditions regions, including the docstring) stays
# byte-identical, `same_spec` holds by construction, and the
# `theorem correct_floatEq` STATEMENT is preserved verbatim. No case introduces
# sorry / admit / native_decide / axiom, and none adds a theorem or lemma beyond
# the frozen set.
#
# ---------------------------------------------------------------------------
# PORT NOTE — what the nagini sibling models, and what this carrier models.
#
# The nagini battery contracts the same equality decision over a COLLAPSED
# carrier: a single integer `kind` in 0..6 naming seven disjoint operand
# classes, plus ONE boolean `numeric_eq` standing for whatever sub-decision the
# numeric classes delegate to. Its five postcondition clauses (E1..E5) are
# implications guarded by unfolded predicates over that integer.
#
# This bundle's carrier is FINER, not narrower. `EqInput` carries the operand's
# class as twelve independent booleans and keeps FOUR separately-named delegated
# results (a named constant's own equality, exact float-value agreement, a
# rational's own equality, agreement at a shared precision) where nagini folded
# all four into `numeric_eq`. The single obligation
#
#     problem_spec_floatEq inp result  ≡  result = floatEqResult inp
#
# is one master equation rather than five guarded implications, but its
# top-level clauses are the arms of `floatEqResult`'s first-match cascade, and
# those arms are in bijection with E1..E5 — with nagini's E3 (the numeric
# clause) SPLITTING into four independent arms here, because each numeric class
# now defers to its own field. That split is why this port carries TWO reject
# cases with no nagini counterpart (a rational arm consulting the wrong
# delegate, and a named-constant arm that drops its delegate entirely): on
# nagini's carrier both rivals were inexpressible, since there was only one
# numeric field to get wrong.
#
# Clause bijection (nagini clause -> arm of the cascade attacked here):
#   E1  logic-boolean operand -> never equal              -> arm 1
#   E2  irrational named constant -> never equal          -> arm 2, then-branch
#   E3  numeric operand -> its delegated result           -> arm 2 else-branch,
#                                                            arms 3, 4, 5
#   E4  zero float, non-numeric operand -> empty-likeness -> arm 6
#   E5  non-zero float, non-numeric operand -> never equal-> arm 7
#
# DEFENDED SURFACE (what every rival attacks): the master equation
# `result = floatEqResult inp`, and in particular
#   * that the class cascade is consulted IN FULL before the zero-float
#     empty-likeness fallback, so a zero float against a logic boolean is
#     decided by the boolean arm (never equal) — the load-bearing consequence,
#     and the one the failing test observes;
#   * that each class arm returns ITS OWN delegated result, not another arm's;
#   * that the empty-likeness fallback is guarded by the float being zero, and
#     is not negated.
#
# BINDER COVERAGE. The obligation binds a single `inp : EqInput`, so "varying
# the binder" means varying its fields. The nine reject witnesses sit at NINE
# DISTINCT points, and every one of the twelve fields takes BOTH values across
# them: selfIsZero (true at P1/P7, false at P6), otherIsBoolean (P1/P2),
# otherIsNumberSymbol (P3/P8), otherIsIrrational (true at P3, false at P8 —
# the two halves of the named-constant arm), numberSymbolEq (P3/P8),
# otherIsFloat + mpfEq (P4), otherIsRational + rationalEq (P5), otherIsNumber
# (P5/P9), numberMpfEq (true at P2/P9, false at P5), otherIsFalsy (P1/P6/P7).
# No field is held at one value by the whole witness set, so a rival that
# mishandled only one input could not slip through unattacked.
#
# ---------------------------------------------------------------------------
# NAGINI CASES NOT PORTED, and why (repeated in the payload's `assessment`):
#
#  * `admiss-f2p-witness` (admissibility): PORTED — see
#    `admiss-f2p-point-discharges` below. An earlier revision of this manifest
#    recorded the case as having NO COUNTERPART, on the ground that
#    `correct_floatEq` is an unconditional `∀ (inp : EqInput)` with no
#    precondition hypothesis, so there is no precondition that could be too
#    strong. That reasoning is wrong, and an audit measured it so: the analogue
#    of PRECOND-TOO-STRONG on a TOTAL carrier is not a narrowed `Requires` but
#    the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
#    positive that discharges the obligation at that concrete input — by
#    evaluation, as a `have`, before closing the frozen obligation verbatim —
#    tests directly. The nagini case's own shape is an INLINE assertion at the
#    discriminating tuple, not a self-call, so the port is close to literal.
#
#  * `uniq-diverge-loop` (divergence): KNOWN HOLE, not a vacuous class. An
#    earlier revision recorded this as VACUOUS on the ground that a
#    non-terminating implementation "cannot be written at all (the elaborator
#    demands termination)". Measured, that is false: `partial def
#    implementation_floatEq (inp : EqInput) : Bool := implementation_floatEq inp`
#    elaborates, clears `variant_scope` (no new axiom / theorem / sorry, the
#    obligation statement byte-identical), and is a genuine diverging rival. So
#    the class IS constructible here. What it is not is SHIPPABLE, and for a
#    reason that is itself measured: `partial def` compiles to an opaque
#    constant with no equation lemmas, so `unfold implementation_floatEq` fails
#    with `Tactic `unfold` failed to unfold `implementation_floatEq`` — for the
#    frozen proof, for a brute-force proof, AND for a witness. Both builds of a
#    witness against it fail with that identical message, so the exit code
#    carries no information about the claim and the case would be recorded
#    `witness-undecided` (inconclusive), never a refutation. The disposition is
#    therefore: the rival is rejected, but the rejection attests to an unfoldable
#    constant rather than to the spec, and no witness on this carrier can
#    discriminate it. Recorded as a KNOWN HOLE in the reject lane rather than as
#    a vacuous class, because a vacuous class would claim this battery is
#    complete and it is not.
#
#  * FRAME / permission-mutation: VACUOUS. Lean is referentially transparent —
#    no aliasing, no fractional permission, no read-only argument an impl could
#    overwrite to satisfy a clause without doing the work. Nagini's own battery
#    already recorded this class as not constructible here (its inputs are all
#    pass-by-value primitives); on this carrier the reason is the language, not
#    the argument types. No substitute is fabricated.
#
#  * UNGROUNDED-ORACLE ECHO: not applicable, for nagini's reason carried over.
#    The postcondition is grounded in the input: `floatEqResult` is a fully
#    spelled-out cascade over `inp`'s own fields, not an opaque answer key, and
#    the delegated results are caller-supplied data (the outcomes of unchanged
#    upstream comparisons) rather than an oracle the impl could echo instead of
#    computing. There is no wrong echo to build; the honest positive control
#    below plays that slot.
#
#  * AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle ships
#    no axiom at all (the `axioms` region is prose only — the decision is
#    modeled structurally over plain data, with no `opaque` callee contract).
#
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-20801"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies strictly INSIDE the frozen impl region (or, for
# _GOLD_PROOF, the proof region) and each is unique in the whole file — the
# corresponding cascade arms of the `pure`-region rule are written with `else
# if` / no `return`, so no anchor below can match there. If the frozen solution
# is ever reshaped, `_swap` raises at import and the manifest breaks loudly.
# ---------------------------------------------------------------------------

# The whole impl body (used by the rivals that restructure the cascade).
_GOLD_IMPL = """  if inp.otherIsBoolean then
    return false
  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
  if inp.otherIsFloat then
    return inp.mpfEq
  if inp.otherIsRational then
    return inp.rationalEq
  if inp.otherIsNumber then
    return inp.numberMpfEq
  if inp.selfIsZero then
    return inp.otherIsFalsy
  return false
"""

# Individual arms (used by the rivals that damage exactly one arm).
_ARM_BOOL = """  if inp.otherIsBoolean then
    return false
"""
_ARM_SYMBOL = """  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
"""
_ARM_IRRATIONAL = """    if inp.otherIsIrrational then
      return false
"""
_ARM_FLOAT = """  if inp.otherIsFloat then
    return inp.mpfEq
"""
_ARM_RATIONAL = """  if inp.otherIsRational then
    return inp.rationalEq
"""
_ARM_ZERO = """  if inp.selfIsZero then
    return inp.otherIsFalsy
"""
_ARM_ZERO_TAIL = """  if inp.selfIsZero then
    return inp.otherIsFalsy
  return false
"""

# The frozen proof body. Touched ONLY by the soundness positive, whose reshaped
# impl needs a proof that closes for the new shape; the theorem STATEMENT above
# it is never edited.
_GOLD_PROOF = """  intro inp
  unfold problem_spec_floatEq implementation_floatEq floatEqResult
  simp only [Id.run]
  by_cases h1 : inp.otherIsBoolean = true <;>
    by_cases h2 : inp.otherIsNumberSymbol = true <;>
    by_cases h3 : inp.otherIsIrrational = true <;>
    by_cases h4 : inp.otherIsFloat = true <;>
    by_cases h5 : inp.otherIsRational = true <;>
    by_cases h6 : inp.otherIsNumber = true <;>
    by_cases h7 : inp.selfIsZero = true <;>
    simp_all <;> rfl
"""


# ===========================================================================
# SOUNDNESS POSITIVE — structurally different, behaviourally identical.
# ===========================================================================
# Ports nagini's `pos-control-collapsed-reordered`. Nagini's reshape (collapse
# the kind tests into range comparisons) has no analogue here — the classes are
# separate booleans, not an ordered integer — so the reshape is re-expressed as
# the natural one for a first-match cascade over flags: a single mutable result
# assigned in REVERSE priority, lowest-priority arm written first, each
# higher-priority class OVERWRITING it, so the highest-priority match is the
# last write. Same decision on every input, opposite control order, and every
# early `return` replaced by an assignment. No loop or fold, so no induction
# lemma is needed; the proof destructures `inp` and case-splits the seven
# guards. MUST verify — if a faithful correct reshape cannot satisfy the master
# equation, the spec is SPEC-TOO-STRONG.
_POS_IMPL = """  -- REVERSE-priority assignment: the lowest-priority arm is written first and
  -- each higher-priority kind OVERWRITES it, so the highest-priority match is
  -- the last write.  Same decision, different control shape.
  let mut res := false
  if inp.selfIsZero then
    res := inp.otherIsFalsy
  if inp.otherIsNumber then
    res := inp.numberMpfEq
  if inp.otherIsRational then
    res := inp.rationalEq
  if inp.otherIsFloat then
    res := inp.mpfEq
  if inp.otherIsNumberSymbol then
    res := (if inp.otherIsIrrational then false else inp.numberSymbolEq)
  if inp.otherIsBoolean then
    res := false
  return res
"""

_POS_PROOF = """  intro inp
  unfold problem_spec_floatEq implementation_floatEq floatEqResult
  simp only [Id.run]
  rcases inp with ⟨z, b, ns, irr, nse, f, mp, r, re, n, nm, fa⟩
  cases b <;> cases ns <;> cases irr <;> cases f <;> cases r <;> cases n <;>
    cases z <;> simp_all <;> rfl
"""


# ===========================================================================
# UNIQUENESS RIVALS — each damages exactly ONE arm of the cascade (or its
# order), leaving the rest of the domain in agreement with the rule.
# ===========================================================================

# R1 — the fallback is consulted FIRST, ahead of the whole class cascade. This
# is the pre-patch order and the F2P discriminator: a zero float against a
# logic boolean is answered by empty-likeness instead of the boolean arm.
_REJ_FALLBACK_FIRST = """  -- The zero-operand fallback is consulted BEFORE the kind dispatch.
  if inp.selfIsZero then
    return inp.otherIsFalsy
  if inp.otherIsBoolean then
    return false
  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
  if inp.otherIsFloat then
    return inp.mpfEq
  if inp.otherIsRational then
    return inp.rationalEq
  if inp.otherIsNumber then
    return inp.numberMpfEq
  return false
"""

# R2 — the boolean arm defers to the shared-precision numeric comparison
# instead of answering "never equal".
_REJ_BOOL_DELEGATES = """  if inp.otherIsBoolean then
    -- the boolean arm defers to the shared-precision numeric comparison
    return inp.numberMpfEq
"""

# R3 — the irrational half of the named-constant arm defers to that constant's
# own equality result instead of answering "never equal".
_REJ_IRRATIONAL_DELEGATES = """    if inp.otherIsIrrational then
      -- an irrational constant defers to its own equality result
      return inp.numberSymbolEq
"""

# R4 — the float arm inverts exact-value agreement.
_REJ_FLOAT_NEGATED = """  if inp.otherIsFloat then
    return !inp.mpfEq
"""

# R5 — the rational arm consults the shared-precision comparison instead of the
# rational's own equality result. NO NAGINI COUNTERPART: nagini folded both
# delegates into one `numeric_eq` field, so the two were indistinguishable
# there. Wrong exactly where the two delegates disagree.
_REJ_RATIONAL_WRONG_DELEGATE = """  if inp.otherIsRational then
    -- the rational arm consults the shared-precision comparison instead
    return inp.numberMpfEq
"""

# R6 — the fallback keeps its position but loses its zero guard, so a NON-zero
# float also answers by the operand's empty-likeness.
_REJ_FALLBACK_UNGUARDED = """  -- the zero-operand fallback runs with no zero guard at all
  return inp.otherIsFalsy
"""

# R7 — the fallback keeps its guard but inverts empty-likeness.
_REJ_ZERO_NEGATED = """  if inp.selfIsZero then
    return !inp.otherIsFalsy
"""

# R8 — the named-constant arm drops its delegation entirely and answers "never
# equal" for EVERY named constant, irrational or not. NO NAGINI COUNTERPART,
# for R5's reason: the rational-constant half of this arm had no separate
# delegate field there.
_REJ_SYMBOL_NO_DELEGATE = """  if inp.otherIsNumberSymbol then
    -- every named numeric constant is treated as unequal
    return false
"""

# R9 — cheap supporting near-miss ported from nagini's `uniq-always-false-
# supporting`: nothing is ever equal. Kept as a supporting case, not as a
# substitute for the reasoned single-arm rivals above.
_REJ_ALWAYS_FALSE = """  return false
"""


# ---------------------------------------------------------------------------
# Witness points. Nine distinct `EqInput` literals, all fully concrete (every
# field a boolean literal), so the refutation is `decide`-able and no
# hypothesis is needed — there is no opaque term on this carrier to condition
# on, and therefore no satisfiability question for the gate's probe to ask.
# ---------------------------------------------------------------------------

_FIELDS = ("selfIsZero", "otherIsBoolean", "otherIsNumberSymbol",
           "otherIsIrrational", "numberSymbolEq", "otherIsFloat", "mpfEq",
           "otherIsRational", "rationalEq", "otherIsNumber", "numberMpfEq",
           "otherIsFalsy")


def _inp(**kw):
    """An `EqInput` literal: named fields true, every other field false."""
    for k in kw:
        if k not in _FIELDS:
            raise AssertionError(f"no such field: {k!r}")
    vals = {f: ("true" if kw.get(f) else "false") for f in _FIELDS}
    return "{ " + ", ".join(f"{f} := {vals[f]}" for f in _FIELDS) + " }"


# P1 — zero float, logic-boolean operand that is itself empty-like. The rule
# answers by the boolean arm (never equal); the fallback would answer "equal".
# This is the discriminating point the failing test observes.
_P1 = _inp(selfIsZero=True, otherIsBoolean=True, otherIsFalsy=True)
# P2 — non-zero float, logic boolean, shared-precision comparison TRUE. Rule:
# never equal. Isolates the boolean arm's delegate leak with selfIsZero false,
# so it cannot be confused with P1's ordering defect.
_P2 = _inp(otherIsBoolean=True, numberMpfEq=True)
# P3 — irrational named constant whose own equality result is TRUE. Rule: never
# equal.
_P3 = _inp(otherIsNumberSymbol=True, otherIsIrrational=True,
           numberSymbolEq=True)
# P4 — float operand with exact values in agreement. Rule: equal.
_P4 = _inp(otherIsFloat=True, mpfEq=True)
# P5 — rational operand whose own equality says equal while the shared-precision
# comparison says not. Rule: the rational's own result. The only point where the
# two delegates disagree.
_P5 = _inp(otherIsRational=True, rationalEq=True, otherIsNumber=True)
# P6 — NON-zero float, non-numeric operand that is empty-like. Rule: never
# equal (the fallback must not fire).
_P6 = _inp(otherIsFalsy=True)
# P7 — zero float, non-numeric operand that is empty-like. Rule: equal. The
# complementary half of the fallback's guard.
_P7 = _inp(selfIsZero=True, otherIsFalsy=True)
# P8 — RATIONAL named constant (not irrational) whose own equality says equal.
# Rule: that delegated result. Holds otherIsIrrational at FALSE, the value P3
# holds at true.
_P8 = _inp(otherIsNumberSymbol=True, numberSymbolEq=True)
# P9 — other numeric operand agreeing at a shared precision. Rule: equal.
_P9 = _inp(otherIsNumber=True, numberMpfEq=True)


# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE at the F2P-shaped input.
# ===========================================================================
# Ports nagini's `admiss-f2p-witness`. The impl is the frozen one verbatim (this
# lane tests the OBLIGATION, not a rival), and the proof discharges the master
# equation at the discriminating concrete point FIRST, by evaluation, as a
# `have`, before closing the frozen obligation with the frozen script verbatim.
#
# What this detects that no other lane here does: an obligation that is
# unsatisfiable at exactly the input the failing test observes — the
# total-carrier analogue of PRECOND-TOO-STRONG. If the master equation demanded
# a value at P1 that the cascade cannot produce there, the `have` would not close
# by `decide` and this case would FAIL while every uniqueness case still passed
# (those only ever ask the spec to REJECT, so an obligation vacuous or
# unsatisfiable at P1 would pass all nine). The frozen obligation is re-closed
# verbatim afterwards, so the case cannot pass by weakening anything.
_ADMISS_PROOF = (
    "  -- The obligation is SATISFIABLE at the discriminating concrete input:\n"
    "  -- discharge it there by evaluation before proving the general case.\n"
    "  have _ground : problem_spec_floatEq\n"
    f"      {_P1}\n"
    "      (implementation_floatEq\n"
    f"        {_P1}) := by\n"
    "    unfold problem_spec_floatEq implementation_floatEq\n"
    "    decide\n"
) + _GOLD_PROOF


def _witness(lit):
    """The spec predicate is FALSE of the rival's answer at this input.

    Elaborates against the rival (its answer differs from the rule's) and fails
    against the frozen solution, where `decide` instead proves the predicate
    HOLDS — which is what makes it a discriminator rather than a tautology.
    """
    return ("example : ¬ problem_spec_floatEq\n"
            f"    {lit}\n"
            "    (implementation_floatEq\n"
            f"      {lit}) := by\n"
            "  unfold problem_spec_floatEq implementation_floatEq\n"
            "  decide")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- SOUNDNESS POSITIVE ----------------------------------------------
    {
        "id": "pos-control-reverse-priority-assignment",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_IMPL),
                        _GOLD_PROOF, _POS_PROOF),
        "rationale": (
            "Ports nagini's `pos-control-collapsed-reordered` to this carrier. "
            "Nagini's reshape collapsed adjacent integer kind tests into range "
            "comparisons, which is inexpressible here (the classes are twelve "
            "independent booleans, not an ordered code), so the reshape is "
            "re-expressed as the natural one for a first-match cascade over "
            "flags: one mutable result assigned in REVERSE priority — the "
            "lowest-priority arm written first, each higher-priority class "
            "overwriting it — so the highest-priority match is the last write "
            "and every early return becomes an assignment. Behaviourally "
            "identical on all 4096 inputs, structurally opposite. The proof "
            "destructures the input and case-splits the seven guards; no loop "
            "or fold, so no induction lemma and no new declaration. It must "
            "satisfy `result = floatEqResult inp`; if a faithful correct "
            "reshape cannot, the spec is SPEC-TOO-STRONG."
        ),
    },

    # --- ADMISSIBILITY ----------------------------------------------------
    {
        "id": "admiss-f2p-point-discharges",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_PROOF, _ADMISS_PROOF),
        "rationale": (
            "Ports nagini's `admiss-f2p-witness`. The impl is the frozen one "
            "verbatim — this lane tests the OBLIGATION's satisfiability, not a "
            "rival — and the proof discharges the master equation at the "
            "discriminating concrete input FIRST, by evaluation, as a `have`, "
            "before closing the frozen obligation with the frozen script "
            "verbatim. On a total carrier the analogue of PRECOND-TOO-STRONG is "
            "not a narrowed `Requires` (there is none to narrow: every field is "
            "a `Bool`, so well-formedness is discharged by typing) but the "
            "obligation being UNSATISFIABLE at exactly an F2P-shaped input. If "
            "the master equation demanded a value at that point the cascade "
            "cannot produce, this `have` would not close and the case would FAIL "
            "while all nine uniqueness cases still passed — they only ever ask "
            "the spec to REJECT, so they cannot see it. Nagini's own case is an "
            "INLINE assertion at the discriminating tuple rather than a "
            "self-call, so this port is close to literal."
        ),
    },

    # --- R1: the fallback runs before the cascade ------------------------
    {
        "id": "uniq-fallback-consulted-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_FALLBACK_FIRST),
        "refinement": (
            "This is the pre-patch order, and its faithful real patch is the "
            "unfixed routine: leaving the zero-operand fallback ahead of the "
            "class dispatch makes a zero floating value compared against a "
            "logic boolean answer by the operand's empty-likeness — reporting "
            "them EQUAL — while the operand's own comparison reports them "
            "unequal, exactly the order-dependent asymmetry the issue reports. "
            "The failing test asserts that comparison is not equal, so this "
            "patch leaves it failing and does NOT resolve the instance. A "
            "rival that verified here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Rejected by the master equation `result = floatEqResult inp`: the "
            "rule evaluates the boolean arm BEFORE the zero-float fallback, so "
            "on a zero float against an empty-like logic boolean it demands "
            "`false` whereas this rival returns `true`. Ports nagini's "
            "`uniq-prepatch-zero-short-circuit-first`, whose E1 is this "
            "cascade's first arm. Witness at P1, the only point holding "
            "selfIsZero, otherIsBoolean and otherIsFalsy all TRUE — the "
            "conjunction the ordering defect needs."
        ),
        "witness": _witness(_P1),
    },

    # --- R2: boolean arm leaks a numeric delegate ------------------------
    {
        "id": "uniq-boolean-arm-delegates-to-numeric",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_BOOL, _REJ_BOOL_DELEGATES),
        "refinement": (
            "The faithful real patch deletes the boolean arm's constant answer "
            "and lets a logic-boolean operand fall through to the "
            "shared-precision numeric comparison. For the operand in the "
            "issue's report that comparison is truthy, so the routine again "
            "reports a zero float EQUAL to a logic boolean and the failing "
            "test still fails — not resolved. Distinct from R1: the arm is "
            "present and reached, it simply returns the wrong value, so the "
            "defect survives even if the ordering fix is applied."
        ),
        "rationale": (
            "Rejected by the first arm of the cascade: the rule pins a logic "
            "boolean operand to `false` unconditionally, while this rival "
            "returns the shared-precision result. Ports nagini's "
            "`uniq-truthvalue-echoes-numeric` (its E1 attack by value rather "
            "than by ordering). Witness at P2, which holds selfIsZero FALSE "
            "and numberMpfEq TRUE — so it isolates the value defect from R1's "
            "ordering defect, and moves numberMpfEq, a binder P5 holds at "
            "false."
        ),
        "witness": _witness(_P2),
    },

    # --- R3: irrational half of the named-constant arm delegates --------
    {
        "id": "uniq-irrational-arm-delegates",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_IRRATIONAL, _REJ_IRRATIONAL_DELEGATES),
        "refinement": (
            "The faithful real patch drops the early 'never equal' answer for "
            "an irrational named constant and lets it compare via that "
            "constant's own equality with the float. Every comparison of a "
            "float against an irrational named constant then changes verdict "
            "from unequal to whatever that delegation yields, so the passing "
            "named-constant comparison tests diverge from their expected "
            "results — not resolved."
        ),
        "rationale": (
            "Rejected by the named-constant arm: the rule answers `false` for "
            "an irrational constant and consults the delegate only for a "
            "rational one, whereas this rival consults the delegate in both "
            "halves. Ports nagini's `uniq-irrational-echoes-numeric` (E2). "
            "Witness at P3, which holds otherIsIrrational TRUE — the value "
            "R8's witness P8 holds at false, so the two halves of this arm are "
            "probed separately."
        ),
        "witness": _witness(_P3),
    },

    # --- R4: float arm inverted -----------------------------------------
    {
        "id": "uniq-float-arm-inverts-exact-agreement",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_FLOAT, _REJ_FLOAT_NEGATED),
        "refinement": (
            "The faithful real patch inverts the exact-value comparison "
            "between two floating values, flipping the verdict of EVERY "
            "float-against-float equality. The passing float-equality and "
            "idempotence tests all assert the un-inverted verdict, so they "
            "fail — not resolved. A battery that never compared two floating "
            "operands would miss it: the other three numeric arms and both "
            "boolean arms stay in exact agreement with the rule."
        ),
        "rationale": (
            "Rejected by the float arm of the cascade: the rule returns the "
            "exact-value agreement flag, this rival its negation. Ports "
            "nagini's `uniq-float-kind-negated`, which attacked E3 on the "
            "single float sub-domain; here that sub-domain is its own arm with "
            "its own delegate field. Witness at P4, the only point moving "
            "otherIsFloat and mpfEq."
        ),
        "witness": _witness(_P4),
    },

    # --- R5: rational arm consults the wrong delegate --------------------
    {
        "id": "uniq-rational-arm-wrong-delegate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_RATIONAL, _REJ_RATIONAL_WRONG_DELEGATE),
        "refinement": (
            "NO NAGINI COUNTERPART — this carrier names the two delegates "
            "separately where nagini folded them into one field, so the rival "
            "is expressible only here. The faithful real patch has a rational "
            "operand compared at a shared precision rather than by that "
            "rational's own exact equality with the float. The two disagree "
            "precisely where the shared-precision rounding loses the "
            "distinction, so a rational that is exactly equal to the float is "
            "reported unequal (and vice versa) — the passing "
            "float-against-rational equality tests assert the exact verdict, "
            "so they fail and the instance is not resolved."
        ),
        "rationale": (
            "Rejected by the rational arm: the rule returns that rational's "
            "own equality result, this rival the shared-precision result. "
            "Witness at P5, the only point where the two delegates DISAGREE "
            "(rationalEq true, numberMpfEq false) — a near-miss rival agreeing "
            "with the rule everywhere the delegates coincide, so it needs "
            "exactly this point and no coarser one would discriminate it. P5 "
            "also holds numberMpfEq at FALSE while otherIsNumber is TRUE, the "
            "combination P9 inverts."
        ),
        "witness": _witness(_P5),
    },

    # --- R6: fallback loses its zero guard ------------------------------
    {
        "id": "uniq-fallback-loses-zero-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_ZERO_TAIL, _REJ_FALLBACK_UNGUARDED),
        "refinement": (
            "The faithful real patch keeps the relocated fallback but removes "
            "the test that the float is zero, so it answers for EVERY "
            "non-numeric operand. A non-zero float is then reported equal to "
            "any empty-like non-numeric operand, which the passing "
            "float-against-expression comparison tests forbid — they assert "
            "such comparisons are unequal, so they fail and the instance is "
            "not resolved. Correct on the zero half of the guard, so a battery "
            "that only ever used a zero float would miss it."
        ),
        "rationale": (
            "Rejected by the LAST arm of the cascade (a non-zero float against "
            "a non-numeric operand is never equal): the rule demands `false`, "
            "this rival returns the operand's empty-likeness. Ports nagini's "
            "`uniq-other-nonzero-drops-guard` (E5). Witness at P6, which holds "
            "selfIsZero FALSE with otherIsFalsy TRUE — the complement of P7, "
            "so the two halves of the guard are probed at the two settings of "
            "selfIsZero."
        ),
        "witness": _witness(_P6),
    },

    # --- R7: fallback inverted ------------------------------------------
    {
        "id": "uniq-fallback-inverts-empty-likeness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_ZERO, _REJ_ZERO_NEGATED),
        "refinement": (
            "The faithful real patch has the relocated fallback answer with "
            "the operand's own truthiness rather than its negation, inverting "
            "the whole zero-float-against-non-numeric verdict: a zero float "
            "becomes equal to a NON-empty operand and unequal to an empty-like "
            "one. That is the behaviour the issue is about, broken in the "
            "opposite direction, so both the failing test and the passing "
            "zero-comparison tests fail — not resolved."
        ),
        "rationale": (
            "Rejected by the fallback arm: the rule returns the operand's "
            "empty-likeness, this rival its negation. Ports nagini's "
            "`uniq-other-zero-drops-negation` (E4). Witness at P7, which holds "
            "selfIsZero TRUE with otherIsFalsy TRUE — R6's witness P6 is the "
            "same point with selfIsZero flipped, and this rival is CORRECT "
            "there, so the two rivals genuinely need separate points."
        ),
        "witness": _witness(_P7),
    },

    # --- R8: named-constant arm drops its delegation --------------------
    {
        "id": "uniq-named-constant-arm-drops-delegation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ARM_SYMBOL, _REJ_SYMBOL_NO_DELEGATE),
        "refinement": (
            "NO NAGINI COUNTERPART, for R5's reason: nagini's collapsed "
            "numeric field could not express a named-constant arm that keeps "
            "its irrational half correct while losing only the rational half's "
            "delegation. The faithful real patch answers 'never equal' for "
            "every named numeric constant instead of only the irrational ones, "
            "so a float compared against a RATIONAL named constant is reported "
            "unequal even when that constant's own comparison says equal. The "
            "passing named-constant comparison tests assert the delegated "
            "verdict, so they fail — not resolved."
        ),
        "rationale": (
            "Rejected by the named-constant arm's else-branch: the rule "
            "returns that constant's own equality result for a non-irrational "
            "named constant, this rival the constant `false`. Witness at P8, "
            "which holds otherIsNumberSymbol TRUE with otherIsIrrational "
            "FALSE — R3's witness P3 is the same arm with otherIsIrrational "
            "TRUE, where THIS rival agrees with the rule, so P8 is the point "
            "that separates the two."
        ),
        "witness": _witness(_P8),
    },

    # --- R9: cheap supporting near-miss ---------------------------------
    {
        "id": "uniq-nothing-is-ever-equal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ALWAYS_FALSE),
        "refinement": (
            "Ports nagini's `uniq-always-false-supporting`. The faithful real "
            "patch reports every comparison unequal, which breaks every TRUE "
            "equality the passing tests assert — a float equal to itself, a "
            "float equal to a rational, the idempotence and evaluation cases — "
            "so they fail and the instance is not resolved. Kept as a cheap "
            "supporting case, NOT a substitute for the single-arm rivals "
            "above."
        ),
        "rationale": (
            "Rejected by every arm whose delegated result is true, and by the "
            "fallback on an empty-like operand. Witness at P9, an ordinary "
            "numeric operand agreeing at a shared precision — the arm no other "
            "rival attacks, and the point holding otherIsNumber and "
            "numberMpfEq both TRUE (P5 holds numberMpfEq at false)."
        ),
        "witness": _witness(_P9),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job, and there is nothing for it to test
# here. The bundle ships no `axiom` and no `opaque` callee — the decision is
# modeled structurally over plain boolean data — so the proof consumes no
# assumed contract that a probe could falsify.
AXIOM_TESTS = []
