# properties.py — PBT falsification battery for sympy__sympy-20801.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only the text strictly INSIDE the single
# # impl-start / # impl-end region is swapped) and is checked by Nagini verify +
# markers.same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (model.py `float_equals`):
#   float_equals(self_is_zero: bool, kind: int, other_truthy: bool,
#                numeric_eq: bool) -> bool
#   Requires: 0 <= kind <= 6
#   Requires: MustTerminate(1)   # total correctness: the bounded, loop-free
#            dispatch must terminate; forbids diverging rivals that satisfy the
#            value postconditions vacuously
#   Ensures:
#     (E1) Implies(is_truth_value(kind),       Result() == False)        # kind 0
#     (E2) Implies(is_irrational_const(kind),  Result() == False)        # kind 1
#     (E3) Implies(is_numeric_kind(kind),      Result() == numeric_eq)   # kinds 2..5
#     (E4) Implies(is_other_kind(kind) and self_is_zero,
#                                              Result() == (not other_truthy))  # kind 6, zero
#     (E5) Implies(is_other_kind(kind) and not self_is_zero,
#                                              Result() == False)        # kind 6, nonzero
#   where is_truth_value/is_irrational_const/is_numeric_kind/is_other_kind are
#   @Pure predicates fully UNFOLDED over `kind` (kind==0 / ==1 / in 2..5 / ==6).
#
# The fix (gold patch) relocates `if not self: return not other` from the FRONT
# of the dispatch to AFTER all the boolean/number branches. The whole content of
# the change lives in the ORDER of the kind-0 (truth-value) branch vs the
# self_is_zero short circuit: post-patch kind 0 yields False BEFORE the zero
# short circuit fires, so a zero float is never equal to a symbolic boolean. The
# load-bearing clause is (E1): it must hold even when self_is_zero is True and
# other_truthy is False (the issue's S(0.0) == S.false witness). model_prepatch.py
# violates exactly (E1) by placing the zero short circuit first.
#
# ---------------------------------------------------------------------------
# WHICH WEAKNESS CLASSES APPLY (the rest are justified-N/A in 'assessment'):
#
#  * FRAME-MUTATION: N/A. EVERY input is a pass-by-value primitive
#    (bool/int/bool/bool); there is NO object / list / dict and NO Acc(x,1/2)
#    read-only input to overwrite. There is nothing to mutate to satisfy a
#    postcondition vacuously, so the frame-mutation probe is not constructible
#    here (has_readonly_input == False).
#
#  * UNGROUNDED-ORACLE ECHO: N/A. The postcondition is GROUNDED in the args. The
#    is_* predicates are fully-unfolded comparisons on `kind` (no opaque @Pure
#    answer-key), and `numeric_eq` is itself a caller-supplied input, not an
#    answer-key the impl could "echo without doing the work" — for the numeric
#    kinds the verdict IS numeric_eq by definition (it is the unchanged numeric
#    sub-decision the model carries opaquely; A-reference, validated by
#    axiom_check.py). There is no wrong echo. Instead we ship an honest positive
#    control (structurally-different correct impl) and an admissibility self-call.
#
#  * PARTIAL-DOMAIN: the STRONG class here and the bulk of the battery. The spec
#    pins SEVEN disjoint kind sub-domains (with a self_is_zero split on kind 6).
#    Each reject rival is correct on most of the domain but diverges on exactly
#    one sub-domain (incl. the F2P-discriminating kind-0/zero domain = the
#    prepatch bug). A test that never instantiates a given kind would miss it.
#
#  * CONTROL-FLOW-EFFECT: N/A. float_equals is a total pure boolean function (no
#    raise, no return-vs-raise distinction, no side effect, no read-only input to
#    leave un-mutated); the value abstraction (a bool) captures every observable.
#    There is no capability-token rival to build.
#
#  * DIVERGENCE (non-termination): MANDATORY here. Nagini verifies PARTIAL
#    correctness by default, so before the spec carried Requires(MustTerminate(1))
#    a diverging impl (`while True: pass`) satisfied every value postcondition
#    VACUOUSLY yet its faithful real patch — a Float.__eq__ that never returns —
#    hangs every equality comparison (the F2P/P2P test run times out) and does
#    NOT resolve: the exact verify-but-wrong impl a G-EQ/G-PANEL audit exhibited
#    (atk_7). The termination obligation closes the class: any loop now needs a
#    decreasing MustTerminate measure, so a bare infinite loop is rejected. The
#    gold dispatch is straight-line and discharges MustTerminate(1) trivially,
#    so the obligation is faithful (the real method terminates on every input),
#    not spec-too-strong. Exercised by uniq-diverge-loop below.
#
#  * POSITIVE CONTROL (soundness) + ADMISSIBILITY: included (see below). NOTE:
#    the admissibility probe asserts the precondition's admissibility INLINE
#    (the Requires clauses hold for the F2P-shaped facet tuples) rather than by
#    a recursive self-call — under MustTerminate(1) a self-call at equal
#    measure (1 < 1) is correctly rejected by the obligation checker, so the
#    old self-call probe shape is no longer expressible; the result values the
#    old probe asserted are already pinned directly by E1/E4 on those inputs.
#
# AXIOM_TESTS: EMPTY. meta.axioms == [] (axioms region empty); the proof consumes
# NO @ContractOnly Ensures. The dispatch is an A-reference deep model validated
# == the real Float.__eq__ by axiom_check.py / G-AX (161 operand pairs covering
# kinds {0..6}, run apply_gold=True). That is the existing G-AX obligation, not a
# new per-input axiom obligation a Docker probe could falsify, so there is no
# axiom-soundness / axiom-containment case to add.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-20801"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim text strictly BETWEEN "    # impl-start\n" and "    # impl-end\n"
# in model.py. Every variant is _BASE with this block replaced by an alternative
# body that touches ONLY the impl region -> markers.same_spec == True by
# construction (the frozen axioms/pure/pre/post regions are never edited).
_IMPL = (
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    return False\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _variant(new_impl):
    """Return full model source with the impl region body replaced by new_impl
    (the text strictly between the # impl-start / # impl-end markers, so
    same_spec is preserved by construction)."""
    return _swap(_BASE, _IMPL, new_impl)


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — structurally-DIFFERENT but CORRECT impl.
# The dispatch is rewritten with a DIFFERENT control shape that still satisfies
# every Ensures clause: the four numeric kinds (2..5) are collapsed into one
# inclusive-range test (kind >= 2 and kind <= 5) instead of four separate ifs;
# kinds 0 and 1 are collapsed into a single `kind <= 1 -> False`; and the kind-6
# fall-through is written with an explicit `not self_is_zero -> False` arm so the
# self_is_zero split is reordered. No loops / no fold -> no induction lemma; every
# branch returns a value the postcondition pins, so the gold proof obligations are
# discharged exactly as before. MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================
_POS = (
    "    # Collapsed, reordered dispatch -- same verdict on every kind.\n"
    "    if kind <= 1:\n"
    "        # kind 0 (truth value) and kind 1 (irrational const) are both False.\n"
    "        return False\n"
    "    if kind >= 2 and kind <= 5:\n"
    "        # the four numeric kinds all defer to the numeric-equality decision.\n"
    "        return numeric_eq\n"
    "    # kind == 6 (otherwise-uncategorised): matches only a zero float.\n"
    "    if not self_is_zero:\n"
    "        return False\n"
    "    return not other_truthy\n"
)

# ===========================================================================
# 6. ADMISSIBILITY — the precondition must admit the discriminating F2P-shaped
# input. The issue's witness S(0.0) == S.false maps to (self_is_zero=True,
# kind=0, other_truthy=False, numeric_eq=anything). The probe asserts INLINE
# that the Requires clauses hold on that literal tuple (0 <= 0 <= 6 — kind 0 is
# in domain) and on the kind-6/zero shape (0 <= 6 <= 6), and that the pure kind
# predicates classify them onto the load-bearing E1/E4 clauses (is_truth_value(0),
# is_other_kind(6)), whose pinned verdicts (False / not other_truthy) are the
# issue's desired behaviour. A recursive self-call is NOT used: under the
# termination obligation MustTerminate(1) a self-call at a non-decreasing
# measure is correctly rejected, and the values the old self-call asserted are
# exactly what E1/E4 already pin on these inputs. If the precondition rejected
# this normal input shape, PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = (
    "    # Admissibility: the discriminating F2P-shaped input S(0.0) == S.false\n"
    "    # -> (self_is_zero=True, kind=0, other_truthy=False) satisfies the\n"
    "    # Requires (0 <= kind <= 6): kind 0 is in domain, else PRECOND-TOO-\n"
    "    # STRONG. Its kind falls on the E1 clause, which pins the verdict False\n"
    "    # (the fix).\n"
    "    Assert(0 <= 0 and 0 <= 6)          # kind=0 (S.false) is in domain\n"
    "    Assert(is_truth_value(0))          # ... and E1 governs it -> False\n"
    "    # Also admit the kind-6 zero arm (self_is_zero, other falsy -> True).\n"
    "    Assert(0 <= 6 and 6 <= 6)          # kind=6 is in domain\n"
    "    Assert(is_other_kind(6))           # ... and E4 governs it -> not other\n"
    "    # Real logic (unchanged behaviour).\n"
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    return False\n"
)

# ===========================================================================
# 3a. PARTIAL-DOMAIN — THE PREPATCH BUG / F2P discriminator. The self_is_zero
# short circuit is moved to the FRONT, before the kind-0 (truth-value) branch
# (= model_prepatch.py = the pre-patch dispatch order). For kind 0 with
# self_is_zero=True and other_truthy=False it returns `not False == True` instead
# of False. Correct on every other input. MUST reject (violates E1).
# ===========================================================================
_REJ_PREPATCH = (
    "    # PRE-PATCH ORDER: zero short circuit BEFORE the truth-value case.\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    return False\n"
)

# ===========================================================================
# 3b. PARTIAL-DOMAIN — truth-value kind echoes the numeric decision. For kind 0
# it returns numeric_eq instead of the constant False. Wrong whenever numeric_eq
# is True (e.g. a zero float vs S.false, where the real numeric sub-decision a
# careless impl might compute is truthy). Correct on every other kind and even on
# kind 0 when numeric_eq happens to be False. MUST reject (violates E1).
# ===========================================================================
_REJ_TRUTH_NUMERIC = (
    "    if kind == 0:\n"
    "        # WRONG: a symbolic boolean must be False unconditionally; this leaks\n"
    "        # the numeric-equality decision into the truth-value verdict.\n"
    "        return numeric_eq\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    return False\n"
)

# ===========================================================================
# 3c. PARTIAL-DOMAIN — irrational-constant kind echoes the numeric decision. For
# kind 1 it returns numeric_eq instead of False. Wrong whenever numeric_eq is
# True. Correct on every other kind. MUST reject (violates E2).
# ===========================================================================
_REJ_IRRATIONAL_NUMERIC = (
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        # WRONG: an irrational named constant (pi, E, GoldenRatio) is never\n"
    "        # equal to a float; this defers to the numeric decision instead.\n"
    "        return numeric_eq\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    return False\n"
)

# ===========================================================================
# 3d. PARTIAL-DOMAIN — ONE numeric sub-kind negated. For kind 3 (another floating
# value -> exact mpf compare) it returns `not numeric_eq`; kinds 2/4/5 stay
# correct. A test that only ever compares against integers/rationals/named
# constants (never another Float operand) would NOT instantiate kind 3 and so
# would not catch this. MUST reject (violates E3 on the kind==3 sub-domain).
# ===========================================================================
_REJ_FLOAT_KIND_NEGATED = (
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        # WRONG: negate the exact mpf compare on the Float-vs-Float kind only.\n"
    "        return not numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        return not other_truthy\n"
    "    return False\n"
)

# ===========================================================================
# 3e. PARTIAL-DOMAIN — kind-6 NON-ZERO arm returns the zero-arm verdict. For
# kind 6 with self_is_zero=False it returns `not other_truthy` instead of the
# constant False. Wrong whenever other_truthy is False (a non-zero float vs a
# falsy non-number operand -> returns True). The kind-6 ZERO arm is left correct,
# so a test that only ever uses a zero float as `self` against a kind-6 operand
# would miss it. MUST reject (violates E5).
# ===========================================================================
_REJ_OTHER_NONZERO = (
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    # WRONG: a NON-zero float against an uncategorised operand must be False;\n"
    "    # this drops the self_is_zero guard and always negates other_truthy.\n"
    "    return not other_truthy\n"
)

# ===========================================================================
# 3f. PARTIAL-DOMAIN — kind-6 ZERO arm drops the negation. For kind 6 with
# self_is_zero=True it returns other_truthy instead of `not other_truthy`. Wrong
# on the whole kind-6/zero domain (e.g. a zero float vs a falsy non-number: gold
# True, rival False; vs a truthy non-number: gold False, rival True). The
# non-zero arm is left correct. MUST reject (violates E4).
# ===========================================================================
_REJ_OTHER_ZERO_NONEG = (
    "    if kind == 0:\n"
    "        return False\n"
    "    if kind == 1:\n"
    "        return False\n"
    "    if kind == 2:\n"
    "        return numeric_eq\n"
    "    if kind == 3:\n"
    "        return numeric_eq\n"
    "    if kind == 4:\n"
    "        return numeric_eq\n"
    "    if kind == 5:\n"
    "        return numeric_eq\n"
    "    if self_is_zero:\n"
    "        # WRONG: drop the negation -- the zero-float-vs-uncategorised verdict\n"
    "        # is `not bool(other)`, not bool(other).\n"
    "        return other_truthy\n"
    "    return False\n"
)

# ===========================================================================
# 3h. DIVERGENCE — the non-termination rival (= the audit's atk_7). The whole
# dispatch is replaced by an infinite `while True: pass`. Under partial
# correctness this VERIFIES (every value postcondition E1..E5 holds vacuously
# on the unreachable exit); its faithful real patch replaces the body of
# Float.__eq__ with a bare infinite loop, so ANY Float equality comparison
# hangs — the F2P/P2P test run times out and the instance is NOT resolved.
# The spec's Requires(MustTerminate(1)) forces the verifier to demand a
# termination measure the bare loop cannot supply, so the rival MUST reject.
# ===========================================================================
_REJ_DIVERGE_LOOP = (
    "    # Divergence: never return; every value postcondition holds vacuously.\n"
    "    while True:\n"
    "        pass\n"
)

# ===========================================================================
# 3g. SUPPORTING near-miss (cheap, but carries a real refinement): always return
# False. Correct on kinds 0/1 and on the kind-6/non-zero arm, but WRONG on every
# numeric kind whose sub-decision is True, and on the kind-6/zero arm against a
# falsy operand. Kept as a cheap supporting case, not a substitute for the
# reasoned sub-domain rivals above. MUST reject (violates E3 / E4).
# ===========================================================================
_REJ_ALWAYS_FALSE = (
    "    # Cheap near-miss: every comparison is unequal.\n"
    "    return False\n"
)


SPEC_TESTS = [
    {
        "id": "pos-control-collapsed-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS),
        "rationale": "A structurally-different but behaviourally-identical impl: "
                     "kinds 0/1 collapsed into `kind <= 1 -> False`, kinds 2..5 "
                     "into one inclusive-range test, and the kind-6 self_is_zero "
                     "split reordered (non-zero arm first). No loops/folds, so no "
                     "induction lemma; every branch returns the postcondition-pinned "
                     "value, so the gold proof obligations (E1..E5) all discharge. "
                     "MUST verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS),
        "rationale": "Inline admissibility probe for the discriminating F2P-shaped "
                     "input (self_is_zero=True, kind=0, other_truthy=False) "
                     "(= S(0.0) == S.false): asserts Requires(0 <= kind <= 6) holds "
                     "on kind=0 and that is_truth_value(0) routes it onto E1 (whose "
                     "pinned verdict False IS the fix), plus the same for the "
                     "kind-6/zero arm (is_other_kind(6) -> E4). A recursive "
                     "self-call is not used: under Requires(MustTerminate(1)) a "
                     "self-call at a non-decreasing measure is correctly rejected "
                     "by the obligation checker; the values the old self-call "
                     "asserted are exactly what E1/E4 pin on these inputs. If the "
                     "precondition rejected this normal input, PRECOND-TOO-STRONG.",
    },
    {
        "id": "uniq-prepatch-zero-short-circuit-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_PREPATCH),
        "refinement": "This IS model_prepatch.py / the pre-patch dispatch order: "
                      "`if not self: return not other` placed at the FRONT of "
                      "Float.__eq__, before the isinstance(other, Boolean) test. "
                      "The faithful real patch (this order) makes S(0.0) == S.false "
                      "return `not S.false == True` -- exactly the reported bug -- "
                      "so the F2P test_zero_not_false assertion "
                      "`(S(0.0) == S.false) is False` FAILS and the instance is NOT "
                      "resolved.",
        "rationale": "Violates Ensures (E1) Implies(is_truth_value(kind), Result() "
                     "== False) on the sub-domain kind==0 & self_is_zero=True & "
                     "other_truthy=False (returns True). The rejection is the spec "
                     "sensing the relocation -- the whole content of the fix.",
    },
    {
        "id": "uniq-truthvalue-echoes-numeric",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_TRUTH_NUMERIC),
        "refinement": "For a symbolic Boolean operand the gold returns the constant "
                      "False (`if isinstance(other, Boolean): return False`). This "
                      "rival instead defers to the numeric-equality decision, which "
                      "for S.false against a zero float is truthy -> returns True. "
                      "The faithful real patch (delete the Boolean branch and fall "
                      "into the numeric path) reproduces S(0.0) == S.false == True, "
                      "so the F2P test_zero_not_false FAILS -> not resolved.",
        "rationale": "Violates Ensures (E1) on kind==0 whenever numeric_eq is True. "
                     "Distinct from the prepatch rival: here the Boolean branch is "
                     "present but returns the wrong value rather than being skipped.",
    },
    {
        "id": "uniq-irrational-echoes-numeric",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_IRRATIONAL_NUMERIC),
        "refinement": "For an irrational named constant (pi, E, GoldenRatio: "
                      "is_NumberSymbol and is_irrational True) the gold returns the "
                      "constant False (`if other.is_irrational: return False`). This "
                      "rival defers to the numeric decision instead. The faithful "
                      "real patch (drop the is_irrational early-False) would let an "
                      "irrational constant compare numerically to a float, changing "
                      "Float == pi from False to a numeric verdict -> the "
                      "NumberSymbol comparison tests (test_NumberSymbol_comparison, "
                      "test_int_NumberSymbols) would diverge from the gold result.",
        "rationale": "Violates Ensures (E2) Implies(is_irrational_const(kind), "
                     "Result() == False) on kind==1 whenever numeric_eq is True. A "
                     "disjoint sub-domain from the truth-value attacks.",
    },
    {
        "id": "uniq-float-kind-negated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_FLOAT_KIND_NEGATED),
        "refinement": "For another floating value (other.is_Float) the gold returns "
                      "the exact mpf compare `self._mpf_ == other._mpf_`. This rival "
                      "negates ONLY the Float-vs-Float kind (kind 3), leaving "
                      "integers/rationals/named-constants correct. The faithful real "
                      "patch (negate the mpf compare) inverts every Float == Float "
                      "verdict -> test_Float, test_Float_eq, test_float_mpf "
                      "(P2P, all Float-vs-Float equality) FAIL -> not resolved. A "
                      "test that never compares two Floats would miss this.",
        "rationale": "Violates Ensures (E3) Implies(is_numeric_kind(kind), Result() "
                     "== numeric_eq) on the kind==3 sub-domain only (Result() == not "
                     "numeric_eq). Targets a single numeric facet the other clauses "
                     "do not constrain.",
    },
    {
        "id": "uniq-other-nonzero-drops-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_OTHER_NONZERO),
        "refinement": "For an uncategorised operand against a NON-zero float the "
                      "gold falls through to `return False` (the zero short circuit "
                      "does not fire). This rival drops the self_is_zero guard and "
                      "returns `not other_truthy`, so a non-zero Float == Symbol('x') "
                      "(other_truthy True) stays False but a non-zero Float against a "
                      "falsy non-number returns True. The faithful real patch (remove "
                      "the `if not self` guard so `return not other` runs "
                      "unconditionally) makes a non-zero float spuriously equal to a "
                      "falsy non-number -> the general Float-vs-Expr equality tests "
                      "(test_relational, test_comparisons_with_unknown_type) diverge.",
        "rationale": "Violates Ensures (E5) Implies(is_other_kind(kind) and not "
                     "self_is_zero, Result() == False) when other_truthy is False "
                     "(returns True). The non-zero half of the kind-6 split.",
    },
    {
        "id": "uniq-other-zero-drops-negation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_OTHER_ZERO_NONEG),
        "refinement": "For an uncategorised operand against a ZERO float the gold "
                      "returns `not other` (a zero float equals only a falsy "
                      "non-number). This rival returns `other` instead, inverting the "
                      "whole kind-6/zero verdict. The faithful real patch (`return "
                      "other` rather than `return not other` in the relocated block) "
                      "makes S(0.0) equal to a TRUTHY non-number and unequal to a "
                      "falsy one -> the zero-comparison behaviour the issue is about "
                      "is broken in the opposite direction -> F2P/P2P FAIL.",
        "rationale": "Violates Ensures (E4) Implies(is_other_kind(kind) and "
                     "self_is_zero, Result() == (not other_truthy)) on the whole "
                     "kind==6 & self_is_zero domain. The zero half of the kind-6 "
                     "split (disjoint from 3e).",
    },
    {
        "id": "uniq-diverge-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_DIVERGE_LOOP),
        "refinement": "The faithful real patch replaces the body of Float.__eq__ "
                      "(after the sympify preamble) with a bare infinite loop "
                      "(`while True: pass`): every Float equality comparison then "
                      "hangs, the F2P/P2P test run (test_zero_not_false et al.) "
                      "times out, and the instance is NOT resolved. This is the "
                      "exact verify-but-wrong rival the G-EQ/G-PANEL audit "
                      "exhibited (atk_7): under partial correctness all of E1..E5 "
                      "hold vacuously on the unreachable exit.",
        "rationale": "REJECTED by the TERMINATION OBLIGATION: the precondition "
                     "carries Requires(MustTerminate(1)), so the verifier demands "
                     "a decreasing termination measure the bare `while True` loop "
                     "cannot supply. The gold dispatch is straight-line and "
                     "discharges MustTerminate(1) trivially, so the obligation is "
                     "faithful, not spec-too-strong (see the positive control).",
    },
    {
        "id": "uniq-always-false-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_REJ_ALWAYS_FALSE),
        "refinement": "Cheap supporting near-miss: every comparison is unequal "
                      "(return False). The faithful real patch (make Float.__eq__ "
                      "always return False) breaks every TRUE equality: Float(2) == "
                      "Float(2), Float == Rational, the idempotence/eval tests -> "
                      "test_Float, test_Float_eq, test_Float_idempotence (P2P) FAIL, "
                      "and S(0.0) equals nothing at all -> not resolved.",
        "rationale": "Violates Ensures (E3) on every numeric kind whose numeric_eq "
                     "is True, and (E4) on the kind-6/zero falsy-operand arm. Kept "
                     "as a cheap supporting case, NOT a substitute for the reasoned "
                     "sub-domain rivals above.",
    },
]

# No @ContractOnly axioms in this bundle (meta.axioms == []; axioms region empty).
# The dispatch is an A-reference deep model validated == the real Float.__eq__ by
# axiom_check.py / G-AX (in-container, apply_gold=True, 161 operand pairs over
# kinds {0..6}), not a consumed obligation the proof relies on. There is no
# per-input axiom-soundness / axiom-containment obligation a Docker probe could
# falsify here, so AXIOM_TESTS is empty.
AXIOM_TESTS = []
