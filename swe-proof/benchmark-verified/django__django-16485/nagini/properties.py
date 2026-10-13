# properties.py — PBT falsification battery for django__django-16485. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
# AXIOM_TESTS probe the A-reference deep model against the REAL Django filter in
# the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + meta.json + refinement.md + mapping.md +
# instance.json + axiom_check.py + the real test_floatformat.py):
#
#   format_value(int_value: int, frac_zero: bool, p: int) -> List[int]
#     Requires(True)                                   # no input constraint
#     Ensures(Acc(list_pred(Result())))                # owns the returned list
#     Ensures(ToSeq(Result()) == rendered(int_value, frac_zero, p))   # LOAD-BEARING
#
#   rendered(int_value, frac_zero, p)  is the @Pure GROUNDED oracle (a total
#   function of the three args, fully unfolded over the @Pure digit folds
#   int_render / digits_acc / zeros_seq — NO opaque @ContractOnly answer-key):
#     * bare-integer regime  (frac_zero and p <= 0):  int_render(int_value)
#         = digits of |int_value|, leading 45 ('-') if negative, NO 46 ('.').
#     * separator-bearing regime (otherwise): int_render(int_value)
#         + PSeq(46) + zeros_seq(mag(p))  — digits, a '.' (46), then |p| zeros.
#
# The gold patch is a one-token change: the early-return guard
#   `if not m and p < 0:`  ->  `if not m and p <= 0:`
# (`m = int(d) - d`, so `not m` ↔ frac_zero; `p = int(arg)`). It moves the
# boundary case {frac_zero == True ∧ p == 0} from the separator-bearing branch
# into the bare-integer branch. model_prepatch.py (the `p < 0` pre-image) routes
# {integral ∧ p==0} into the else branch and FAILS the postcondition; in the
# real filter that misroute raises `ValueError: valid range for prec is
# [1, MAX_PREC]` on "0.00" — the F2P crash.
#
# Where the rejections come from:
#   * The postcondition pins the ENTIRE output sequence ToSeq(Result()) to the
#     grounded oracle `rendered`. There is no value-proxy / double-mask: every
#     element (sign, each digit, the separator, every fractional zero) is pinned,
#     so a divergence on ANY index is caught. The branch boundary `p <= 0` vs
#     `p < 0` and the `frac_zero` conjunct are both load-bearing through the
#     oracle's branch selector.
#   * GROUNDED-ORACLE (directive 2): `rendered` is a function of the args, fully
#     unfolded — there is no opaque answer-key to ECHO. The only way to "echo"
#     rendered(int_value,frac_zero,p) is to MATERIALIZE the correct sequence,
#     which IS the honest answer; there is no WRONG echo that verifies. So in
#     place of an ungrounded-oracle attack we give an honest cheapest-impl
#     positive control (`pos-bare-local`) — see `assessment`.
#   * FRAME-MUTATION (directive 1, the #1 class): N/A here. All three inputs are
#     pass-by-value primitives (int / bool / int); there is NO read-only
#     Acc(x, 1/2) reference parameter to overwrite. The only Acc(...) in the
#     contract is Acc(list_pred(Result())) on the freshly-built OUTPUT (full
#     ownership the impl must establish) plus the loop-local list_pred(digits) /
#     list_pred(frac). There is nothing to frame-mutate — see has_readonly_input
#     = False / `assessment`.
#   * CONTROL-FLOW-EFFECT (directive 4): N/A. format_value is a pure total
#     value-builder — no raise, no side-effect, no capability token to
#     discriminate. The crash the issue reports lives in the REAL filter's
#     decimal path and is invisible to the value abstraction; it is exercised in
#     the axiom lane (the pre-patch core construction raising on "0.00").
#
# The genuine attacks (partial-domain on the patch-changed class + on adjacent
# subdomains, separator presence, digit content) are below, each with the
# refinement that its faithful real patch would NOT resolve the F2P/P2P.
from pathlib import Path

INSTANCE = "django__django-16485"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        # invariants-start
        Invariant(Acc(list_pred(digits)))
        Invariant(k >= 0)
        Invariant(digits_acc(mag(int_value), empty_seq()) == digits_acc(k, ToSeq(digits)))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    Assert(ToSeq(digits) == digits_acc(mag(int_value), empty_seq()))
    if int_value < 0:
        digits = [45] + digits
    Assert(ToSeq(digits) == int_render(int_value))

    if frac_zero and p <= 0:
        # Bare-integer regime: no decimal separator.
        return digits
    else:
        # Separator-bearing regime: append the separator and the |p|-wide
        # fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(frac)))
            Invariant(0 <= i and i <= mag(p))
            Invariant(ToSeq(frac) == zeros_seq(mag(p) - i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))
        return out
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls
# MUST verify (else SPEC-TOO-STRONG). Both keep the digit loop + its invariants
# and the frac loop + its invariants and ALL gold framing Asserts verbatim
# (pilot pitfall #2), and neither flips the digit-loop direction against the
# front-recursive digits_acc fold (pilot pitfall #3) — only the branch SHAPE /
# a local variable changes.
# ===========================================================================

# pos-branch-reorder: invert the guard so the SEPARATOR-bearing case is the
# `if` and the bare-integer case is the `else`. Behaviourally identical (the
# two regimes are mutually exclusive and exhaustive); the guarded predicate is
# the De-Morgan complement `not (frac_zero and p <= 0)`. Same returned values,
# same Asserts. A correct reordering must verify (else SPEC-TOO-STRONG).
_POS_REORDER = """    # impl-start
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        # invariants-start
        Invariant(Acc(list_pred(digits)))
        Invariant(k >= 0)
        Invariant(digits_acc(mag(int_value), empty_seq()) == digits_acc(k, ToSeq(digits)))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    Assert(ToSeq(digits) == digits_acc(mag(int_value), empty_seq()))
    if int_value < 0:
        digits = [45] + digits
    Assert(ToSeq(digits) == int_render(int_value))

    if not (frac_zero and p <= 0):
        # Separator-bearing regime (branch reordered): append the separator and
        # the |p|-wide fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(frac)))
            Invariant(0 <= i and i <= mag(p))
            Invariant(ToSeq(frac) == zeros_seq(mag(p) - i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))
        return out
    else:
        # Bare-integer regime: no decimal separator.
        return digits
    # impl-end"""

# pos-bare-local: local-variable reshape — hoist the regime predicate into a
# typed boolean local `bare` and branch on it. Identical control flow and
# values; the honest cheapest impl that does the work (no echo possible against
# the grounded oracle). Must verify (else SPEC-TOO-STRONG).
_POS_BARE_LOCAL = """    # impl-start
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        # invariants-start
        Invariant(Acc(list_pred(digits)))
        Invariant(k >= 0)
        Invariant(digits_acc(mag(int_value), empty_seq()) == digits_acc(k, ToSeq(digits)))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    Assert(ToSeq(digits) == digits_acc(mag(int_value), empty_seq()))
    if int_value < 0:
        digits = [45] + digits
    Assert(ToSeq(digits) == int_render(int_value))

    bare = frac_zero and p <= 0  # type: bool
    if bare:
        # Bare-integer regime: no decimal separator.
        return digits
    else:
        # Separator-bearing regime: append the separator and the |p|-wide
        # fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(frac)))
            Invariant(0 <= i and i <= mag(p))
            Invariant(ToSeq(frac) == zeros_seq(mag(p) - i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))
        return out
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input, AND that the grounded oracle resolves that input to the bare-integer
# rendering the F2P observes (else PRECOND-TOO-STRONG). We CANNOT add a separate
# caller def (a new module-level def changes the projected spec view and breaks
# same_spec). Instead we inject the witness INSIDE the impl region (elided from
# the spec view): a leading block that (a) asserts the precondition holds for the
# concrete F2P-shaped input {int_value==0, frac_zero==True, p==0} (the exact
# floatformat("0.00", 0) instance) — Requires(True) is trivially establishable —
# and (b) asserts the grounded oracle resolves that input to the bare integer
# `rendered(0, True, 0) == int_render(0)` (== PSeq(48), the digit '0'), i.e. the
# postcondition is satisfiable for the F2P input. The real impl then runs
# unchanged over the actual params. If the precondition / oracle could not be
# established for this legitimate input the Asserts fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for the F2P-shaped input (elided from spec view) ---
    # floatformat("0.00", 0): int_value == 0, frac_zero == True, p == 0.
    Assert(True)  # the precondition Requires(True) holds for this input
    # the grounded oracle routes the F2P input into the bare-integer regime:
    Assert(rendered(0, True, 0) == int_render(0))
    # --- end admissibility witness; the real impl follows unchanged ---
    # Render the magnitude digits of int_value (shared by both regimes).
    digits = []  # type: List[int]
    k = mag(int_value)
    while k >= 10:
        # invariants-start
        Invariant(Acc(list_pred(digits)))
        Invariant(k >= 0)
        Invariant(digits_acc(mag(int_value), empty_seq()) == digits_acc(k, ToSeq(digits)))
        Invariant(MustTerminate(k + 1))
        # invariants-end
        digits = [48 + (k % 10)] + digits
        k = k // 10
    digits = [48 + k] + digits
    Assert(ToSeq(digits) == digits_acc(mag(int_value), empty_seq()))
    if int_value < 0:
        digits = [45] + digits
    Assert(ToSeq(digits) == int_render(int_value))

    if frac_zero and p <= 0:
        # Bare-integer regime: no decimal separator.
        return digits
    else:
        # Separator-bearing regime: append the separator and the |p|-wide
        # fractional digit field.
        frac = []  # type: List[int]
        i = mag(p)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(frac)))
            Invariant(0 <= i and i <= mag(p))
            Invariant(ToSeq(frac) == zeros_seq(mag(p) - i))
            Invariant(MustTerminate(i + 1))
            # invariants-end
            frac = [48] + frac
            i = i - 1
        out = digits + [46] + frac  # type: List[int]
        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))
        return out
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-prepatch-guard: THE BUG (== model_prepatch.py). Revert the impl branch
# guard to the pre-patch `p < 0`. On the boundary class {frac_zero==True ∧ p==0}
# this takes the else branch and returns int_render + PSeq(46) + zeros_seq(0)
# == int_render + PSeq(46), but the oracle rendered(int_value, True, 0)
# == int_render(int_value). The else-branch Assert still holds (out IS that
# value), but the POSTcondition ToSeq(Result()) == rendered(...) FAILS exactly
# on the patch-changed class. Partial-domain attack on the single class the fix
# targets.
_UNIQ_PREPATCH = _IMPL_OLD.replace(
    "    if frac_zero and p <= 0:\n        # Bare-integer regime: no decimal separator.",
    "    if frac_zero and p < 0:\n        # Bare-integer regime: no decimal separator.",
    1,
)

# uniq-drop-fraczero: drop the `frac_zero` conjunct from the impl guard
# (`if p <= 0:`). Now a NON-integral value at p <= 0 (frac_zero==False, p<=0)
# takes the bare-integer branch and returns `digits` (== int_render), but the
# oracle rendered(int_value, False, p<=0) is separator-bearing. Postcondition
# fails on the {frac_zero==False ∧ p<=0} subdomain. (On {frac_zero==True} the
# two guards agree, so this only diverges off-integral.)
_UNIQ_DROP_FRACZERO = _IMPL_OLD.replace(
    "    if frac_zero and p <= 0:\n        # Bare-integer regime: no decimal separator.",
    "    if p <= 0:\n        # Bare-integer regime: no decimal separator.",
    1,
)

# uniq-drop-separator: in the separator-bearing branch, return the bare `digits`
# (omit the '.' separator and the fractional field). The oracle requires
# int_render + PSeq(46) + zeros_seq(mag(p)); returning int_render alone drops
# the separator (46) and the field. Rejected by the postcondition on the WHOLE
# separator-bearing regime. (We keep the frac loop + its Asserts intact so the
# only change is the returned value, attributing the rejection to the missing
# separator, not to a proof gap.)
_UNIQ_DROP_SEPARATOR = _IMPL_OLD.replace(
    "        out = digits + [46] + frac  # type: List[int]\n"
    "        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))\n"
    "        return out",
    "        out = digits + [46] + frac  # type: List[int]\n"
    "        Assert(ToSeq(out) == int_render(int_value) + PSeq(46) + zeros_seq(mag(p)))\n"
    "        return digits",
    1,
)

# uniq-const-zero-bare: in the bare-integer branch, return the constant single
# digit [48] ('0') instead of the computed `digits`. For int_value != 0 the
# oracle int_render(int_value) != PSeq(48), so the postcondition is violated.
# Attacks whether the bare integer is actually the DIGITS of int_value (not a
# constant). The digit loop + its Assert stay intact; only the returned value
# changes, so the rejection is attributable to the wrong content.
_UNIQ_CONST_ZERO_BARE = _IMPL_OLD.replace(
    "    if frac_zero and p <= 0:\n"
    "        # Bare-integer regime: no decimal separator.\n"
    "        return digits",
    "    if frac_zero and p <= 0:\n"
    "        # Bare-integer regime: no decimal separator.\n"
    "        bad = [48]  # type: List[int]\n"
    "        return bad",
    1,
)

# uniq-strict-lt-only-p (supporting near-miss): use the impl guard
# `if frac_zero and p < 1:`. This is value-equivalent to `p <= 0` over integer p
# (p < 1  ⟺  p <= 0), so it is actually CORRECT and would VERIFY — we therefore
# DO NOT include it; recorded here only to document that the boundary token is
# the load-bearing one and an off-by-one in the OTHER direction (>= vs >) is the
# attack we use (uniq-prepatch-guard) rather than an equivalent rewrite.

# uniq-wrong-frac-fill (SUPPORTING near-miss): fill the fractional field with
# '1' (49) instead of '0' (48). The oracle pins zeros_seq(mag(p)) (all 48s), so
# this is rejected. NOTE (honest framing): the all-zeros fractional field is an
# A-reference SKELETON (refinement.md §3.2 / mapping.md §3.2) — its only
# load-bearing role is core-layer separator PRESENCE, and the gold patch itself
# does NOT emit all-zeros end-to-end in this (patch-unchanged) regime. So this
# rival's rejection is attributable to the skeleton's over-pin of the fill, not
# to a primary verify⇏resolve break; it is a cheap SUPPORTING case only. Its
# refinement is correspondingly weak (a real patch emitting '1's in the
# fractional field would mispredict every separator-bearing P2P), but the
# regime is patch-unchanged, so the strong attacks are the partial-domain /
# separator-presence ones above.
_UNIQ_WRONG_FRAC_FILL = _IMPL_OLD.replace(
    "            frac = [48] + frac\n            i = i - 1",
    "            frac = [49] + frac\n            i = i - 1",
    1,
)


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different CORRECT impl: invert the regime guard "
                     "so the separator-bearing case is the `if` (predicate "
                     "`not (frac_zero and p <= 0)`) and the bare-integer case is the "
                     "`else`. The two regimes are mutually exclusive + exhaustive, so "
                     "this returns identical values; all gold invariants and framing "
                     "Asserts are kept verbatim and the digit-loop direction is "
                     "unchanged (pilot pitfalls #2/#3 avoided). If a faithful correct "
                     "reordering cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-bare-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_BARE_LOCAL),
        "rationale": "local-variable reshape: hoist the regime predicate into a typed "
                     "boolean local `bare = frac_zero and p <= 0` and branch on it. "
                     "Identical control flow + values; the honest cheapest impl that "
                     "does the work (the grounded oracle `rendered` admits no wrong "
                     "echo, so this doubles as the directive-2 positive control). If it "
                     "cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-zero",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) takes the F2P-shaped "
                     "input {int_value==0, frac_zero==True, p==0} (the exact "
                     "floatformat(\"0.00\", 0) instance) and asserts (a) the "
                     "precondition Requires(True) holds and (b) the grounded oracle "
                     "routes it to the bare integer: rendered(0, True, 0) == "
                     "int_render(0) (== PSeq(48), the digit '0'). The real impl then "
                     "runs unchanged. If the precondition/oracle could not be "
                     "established for this legitimate input the Asserts fail => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-prepatch-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces "
                      "and G-DIFF flags: the real guard `if not m and p < 0:` routes "
                      "the boundary case {integral value ∧ p == 0} into the "
                      "precision-computing decimal branch. For floatformat(\"0.00\", 0) "
                      "that path computes prec = abs(0) + units + 1 = 0 and calls "
                      "Context(prec=0), raising `ValueError: valid range for prec is "
                      "[1, MAX_PREC]` — the exact crash the issue reports and the sole "
                      "F2P test_zero_values asserts is fixed (floatformat(\"0.00\", 0) "
                      "== \"0\", floatformat(Decimal(\"0.00\"), 0) == \"0\"). The "
                      "faithful real patch (the un-changed `p < 0` guard) does NOT "
                      "resolve the F2P.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == rendered(int_value, "
                     "frac_zero, p)): on {frac_zero==True ∧ p==0} the impl else branch "
                     "yields int_render + PSeq(46) + zeros_seq(0) == int_render + "
                     "PSeq(46), but the oracle rendered(_, True, 0) == int_render(_) "
                     "(bare-integer regime, no separator). The single changed boundary "
                     "token `<` vs `<=` is exactly what the postcondition senses.",
    },
    {
        "id": "uniq-drop-fraczero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_FRACZERO),
        "refinement": "dropping the `not m` (frac_zero) conjunct — guard `if p <= 0:` "
                      "— routes a NON-integral value at p <= 0 into the bare-integer "
                      "early return `\"%d\" % int(d)`. The real P2P test_inputs asserts "
                      "floatformat(6.200000, -3) == \"6.200\", floatformat(13.1031, -3) "
                      "== \"13.103\", floatformat(11.1197, -2) == \"11.12\" — all "
                      "non-integral values at p < 0 that MUST keep their fractional "
                      "digits. A faithful patch with `if p <= 0:` would render them as "
                      "the bare integers \"6\", \"13\", \"11\", failing those P2P "
                      "assertions; it does NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == rendered(...)): on "
                     "{frac_zero==False ∧ p<=0} the impl returns `digits` (== "
                     "int_render), but the oracle rendered(_, False, p<=0) is the "
                     "separator-bearing int_render + PSeq(46) + zeros_seq(mag(p)). The "
                     "`frac_zero` conjunct in the oracle's branch selector is "
                     "load-bearing.",
    },
    {
        "id": "uniq-drop-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_SEPARATOR),
        "refinement": "returning the bare `digits` in the separator-bearing branch "
                      "drops the decimal separator and the fractional field — i.e. a "
                      "patch that never emitted the '.' for non-integral values or "
                      "p > 0. The P2P test_inputs asserts floatformat(7.7, 3) == "
                      "\"7.700\", floatformat(5555.555, 2) == \"5555.56\", "
                      "floatformat(0.7) == \"0.7\"; the F2P/P2P test_zero_values "
                      "asserts floatformat(0, 6) == \"0.000000\". Stripping the "
                      "separator yields \"7700\"/\"555556\"/\"07\"/\"0000000\", failing "
                      "those assertions; it does NOT resolve. (Core-layer separator "
                      "PRESENCE is the property that distinguishes the two regimes and "
                      "is exactly what makes model_prepatch fail — refinement.md §B.)",
        "rationale": "rejected by Ensures(ToSeq(Result()) == rendered(...)): in the "
                     "separator-bearing regime the oracle is int_render + PSeq(46) + "
                     "zeros_seq(mag(p)); returning int_render alone omits PSeq(46) and "
                     "the field, so the sequences differ at the separator index. The "
                     "frac loop + its Assert are kept intact, so the rejection is "
                     "attributable to the dropped separator, not a proof gap.",
    },
    {
        "id": "uniq-const-zero-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CONST_ZERO_BARE),
        "refinement": "returning the constant single digit [48] ('0') in the "
                      "bare-integer branch corresponds to a patch whose early return "
                      "emitted a fixed \"0\" regardless of the value. The P2P "
                      "test_inputs asserts floatformat(11.0000, -2) == \"11\", "
                      "floatformat(Decimal(\"09.000\")) == \"9\", and "
                      "floatformat(-1.323297138040798e35, -2) == "
                      "\"-132329713804079800000000000000000000\"; a constant \"0\" "
                      "fails every non-zero integral case, so it does NOT resolve.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == rendered(...)): for "
                     "int_value != 0 the oracle int_render(int_value) != PSeq(48), so "
                     "the bare-integer output is pinned to the actual digits of "
                     "int_value (with sign), not a constant. The digit loop + its "
                     "Assert are kept intact; only the returned value changes.",
    },

    # ---- supporting mechanical near-miss (cheap; honest weak refinement) ----
    {
        "id": "uniq-wrong-frac-fill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRONG_FRAC_FILL),
        "refinement": "filling the fractional field with '1' (49) instead of '0' (48). "
                      "HONEST framing: the all-zeros fractional field is an A-reference "
                      "SKELETON (refinement.md/mapping.md §3.2) whose sole load-bearing "
                      "role is core-layer separator PRESENCE; the gold patch does not "
                      "emit all-zeros end-to-end in this patch-UNCHANGED regime, so the "
                      "rejection is attributable to the skeleton's over-pin of the "
                      "fill, NOT to a primary verify⇏resolve break. As a weak "
                      "refinement, a real patch emitting '1's in the fractional field "
                      "would mispredict separator-bearing P2P (e.g. floatformat(0, 6) "
                      "== \"0.000000\" not \"0.111111\"); but the strong attacks are "
                      "the partial-domain / separator-presence ones above. Supporting "
                      "case only.",
        "rationale": "rejected by Ensures(ToSeq(Result()) == rendered(...)): the oracle "
                     "pins the fractional field to zeros_seq(mag(p)) (all code point "
                     "48); filling with 49 makes ToSeq(out) differ at every fractional "
                     "index. The frac loop invariant ToSeq(frac) == zeros_seq(mag(p)-i) "
                     "no longer holds, reinforcing the rejection.",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO consumed @ContractOnly axiom (meta.axioms == []).
# The bundle has A-REFERENCE deep models (rendered / int_render / digits_acc /
# zeros_seq vs the real floatformat core, and the unchanged localisation callee
# formats.number_format). PLAN §2.4 / §4 check A-references the SAME way as
# axioms: the deep model must equal the real callee on every caller-reachable
# input. These probes run in the instance Docker image (the real Django lives
# there). The runner mounts ONLY the probe at /work, so we CANNOT import the
# bundle's axiom_check.py in-container — its logic imports only Django (present),
# so we embed that logic directly in the probe strings (pilot pitfall #6). All
# file reads (none needed here) would use encoding="utf-8" (pitfall #5); probes
# CALL the real floatformat, never scrape source (pitfall #4).
#
# apply_gold=True: the A-reference is the POST-PATCH behaviour (e.g.
# floatformat("0.00", 0) == "0"); on the bare base image it raises, so the
# soundness probe asserts the fixed facts under the gold patch (axiom_check.py
# header).
# ===========================================================================

# ax-sound-rendered: soundness of the A-reference deep model `rendered` against
# the REAL post-patch floatformat. Embeds the bundle's axiom_check.py logic:
#   (1) BARE-INTEGER end-to-end: for integral values at p <= 0 the REAL filter
#       returns exactly int_render(int_value) with NO separator (the F2P
#       observable; the localisation callee preserves the integer digit string).
#   (2) SEPARATOR-BEARING core: for non-integral values or p > 0 the faithful
#       CORE replica (the deterministic decimal-stdlib construction the patch
#       leaves unchanged) contains a separator '.' — the discriminator the model
#       encodes.
#   (3) FIX LOCALISED: in the separator-bearing regime the REAL post-patch filter
#       agrees with the pre-patch filter (the fix changes nothing outside the
#       bare-integer regime).
#   (4) number_format A-reference: digit-content preserving on the bare integer
#       string (decimal_pos=0, no grouping).
#   (5) specific F2P/P2P observables + the pre-patch discriminator (core crashes
#       on "0.00", diverges on "5.0").
# Any disagreement => the A-reference (hence the model's pure region) is unsound.
_AX_SOUNDNESS_PROBE = r'''
import sys
from decimal import Decimal, ROUND_HALF_UP, Context

import django
from django.conf import settings

if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.template.defaultfilters import floatformat
from django.utils import formats


def int_render(int_value):
    """model.py int_render: bare integer string, '-' for negatives, no '.'."""
    return str(int(int_value))


def is_integral(value):
    d = Decimal(str(value))
    return (int(d) - d) == 0


def floatformat_core(value, p, guard_le):
    """Faithful replica of the floatformat CORE digit string (value handed to the
    localisation callee). guard_le=True is the post-patch guard p <= 0; False is
    the pre-patch p < 0. Mirrors model.py `rendered` at the core layer."""
    d = Decimal(str(value))
    m = int(d) - d
    if not m and (p <= 0 if guard_le else p < 0):
        return "%d" % int(d)
    exp = Decimal(1).scaleb(-abs(p))
    tupl = d.as_tuple()
    units = len(tupl[1])
    units += -tupl[2] if m else tupl[2]
    prec = abs(p) + units + 1
    rounded_d = d.quantize(exp, ROUND_HALF_UP, Context(prec=prec))
    sign, digits, exponent = rounded_d.as_tuple()
    digits = [str(digit) for digit in reversed(digits)]
    while len(digits) <= abs(exponent):
        digits.append("0")
    digits.insert(-exponent, ".")
    if sign and rounded_d:
        digits.append("-")
    return "".join(reversed(digits))


def main():
    integral_values = [
        "0.00", "0.0", "0", "1.00", "5.0", "-0.00", "-3.00", "10.00",
        "100", "-100.000", "42", "-42", "999.0", "1000000.00",
        Decimal("0.00"), Decimal("1.00"), Decimal("-7.0"), Decimal("0"),
        0, 1, -1, 7, -7, 123, -123,
    ]
    for v in integral_values:
        assert is_integral(v), "test setup: %r should be integral" % (v,)

    # (1) bare-integer regime end-to-end (real callee) == int_render, no '.'
    bare = 0
    for v in integral_values:
        for p in [0, -1, -2, -5]:
            observed = floatformat(v, p)
            expected = int_render(Decimal(str(v)))
            assert observed == expected, (
                "AXIOM-UNSOUND (bare-integer) floatformat(%r,%r): real %r vs "
                "int_render %r" % (v, p, observed, expected))
            assert "." not in observed, (
                "AXIOM-UNSOUND: bare-integer output has a separator: %r" % observed)
            bare += 1

    # (2)+(3) separator-bearing core has '.'; fix localised (post == pre).
    sep = 0
    def _check_sep_and_localised(v, p):
        core = floatformat_core(v, p, guard_le=True)
        assert "." in core, (
            "AXIOM-UNSOUND: separator-bearing core lacks '.' for (%r,%r): %r"
            % (v, p, core))
        post = floatformat(v, p)
        if post in ("inf", "-inf", "nan"):
            return
        pre = formats.number_format(
            floatformat_core(v, p, guard_le=False), abs(p),
            use_l10n=False, force_grouping=False)
        assert post == pre, (
            "AXIOM-UNSOUND: fix not localised: post %r != pre %r for (%r,%r)"
            % (post, pre, v, p))
    for v in integral_values:
        for p in [1, 2, 6]:              # integral but p > 0
            _check_sep_and_localised(v, p); sep += 1
    for v in ["0.5", "1.25", "-0.499", "3.14159", "0.001", "-2.5",
              Decimal("0.5"), Decimal("-1.5"), "0.000000000000000000015"]:
        for p in [0, -1, 1, 2, 20]:      # non-integral (any p)
            _check_sep_and_localised(v, p); sep += 1

    # (4) number_format A-reference: digit-content preserving on integer strings.
    for n in [0, 1, 5, 10, 100, -3, -10, 12345, -98765, 2 ** 40]:
        s = "%d" % n
        out = formats.number_format(s, 0, use_l10n=False, force_grouping=False)
        assert out == s, "AXIOM-UNSOUND: number_format altered %r -> %r" % (s, out)
        assert "." not in out, "AXIOM-UNSOUND: number_format added '.': %r" % out

    # (5) specific F2P/P2P observables (post-patch facts).
    assert floatformat("0.00", 0) == "0", floatformat("0.00", 0)
    assert floatformat(Decimal("0.00"), 0) == "0", floatformat(Decimal("0.00"), 0)
    assert floatformat(0, 6) == "0.000000", floatformat(0, 6)
    assert floatformat(-0.499, 0) == "0", floatformat(-0.499, 0)
    assert floatformat("5.0", 0) == "5", floatformat("5.0", 0)
    assert floatformat(7.7, 3) == "7.700", floatformat(7.7, 3)
    assert floatformat(6.200000, -3) == "6.200", floatformat(6.200000, -3)
    assert floatformat(11.0000, -2) == "11", floatformat(11.0000, -2)

    # pre-patch discriminator: the p<0 core crashes on "0.00" / diverges on "5.0".
    crashed = False
    try:
        floatformat_core("0.00", 0, guard_le=False)
    except Exception as e:
        crashed = True
        assert "prec" in str(e), "unexpected pre-patch error: %r" % (e,)
    assert crashed, "discriminator: pre-patch core should crash on '0.00'"
    pre5 = floatformat_core("5.0", 0, guard_le=False)
    assert pre5 != "5" and "." in pre5, (
        "discriminator: pre-patch core for 5.0 should be separator-bearing, got %r"
        % pre5)
    assert floatformat_core("5.0", 0, guard_le=True) == "5"

    print("AXIOM-SOUNDNESS OK: A-reference `rendered` validated vs real "
          "floatformat: %d bare-integer end-to-end (== int_render, no '.') + %d "
          "separator-bearing core observations (each '.'-bearing, fix localised); "
          "number_format digit-content preserving; F2P/P2P observables match; "
          "pre-patch (p<0) crashes on '0.00' and diverges on '5.0' (both "
          "forbidden by the frozen postcondition)." % (bare, sep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# ax-cover-rendered: containment — every callee-input the MODEL can reach lies
# inside the A-reference's domain. The model's format_value has Requires(True)
# over (int_value: int, frac_zero: bool, p: int); the only callee it references
# end-to-end is the real floatformat. We enumerate the model-reachable inputs
# (the F2P/P2P-shaped integral and non-integral values across the boundary
# p ∈ {negative, 0, positive}) and confirm the REAL floatformat ACCEPTS each
# (does not raise) under the post-patch guard — i.e. the model never reaches an
# input on which the A-reference is undefined/divergent. The KEY containment fact
# (refinement.md §B): the patch-changed class {integral ∧ p==0} that the
# pre-patch filter RAISES on is now accepted; the model reaches exactly the
# inputs the post-patch callee is defined on. Covering more (any value/p) would
# be sound; a reachable input the post-patch callee rejects/diverges on would be
# AXIOM-TOO-WEAK-FOR-CALLER. Note floatformat tolerates more than the model
# abstracts (it also handles non-numeric / inf / nan via earlier guards outside
# the modelled branch), which is SOUND over-coverage, not a defect.
_AX_CONTAINMENT_PROBE = r'''
import sys
from decimal import Decimal

import django
from django.conf import settings

if not settings.configured:
    settings.configure(USE_I18N=False, USE_TZ=False, INSTALLED_APPS=[], DATABASES={})
django.setup()

from django.template.defaultfilters import floatformat


def is_integral(value):
    d = Decimal(str(value))
    return (int(d) - d) == 0


def main():
    # Model-reachable inputs: the modelled branch covers (int_value, frac_zero, p)
    # with Requires(True). The caller (real floatformat) maps these to numeric
    # text values across the boundary. Enumerate F2P/P2P-shaped values spanning
    # both regimes and the boundary p in {negative, 0, positive}.
    integral = ["0.00", "0.0", "0", "1.00", "5.0", "-3.00", "100", "-100.000",
                "42", "-42", "999.0", Decimal("0.00"), Decimal("-7.0"), 0, 7, -7]
    nonintegral = ["0.5", "1.25", "-0.499", "3.14159", "6.200000", "13.1031",
                   "5555.555", Decimal("555.555"), "0.000000000000000000015"]
    ps = [0, -1, -2, -5, -20, 1, 2, 6, 20]

    reached = 0
    # bare-integer regime reachable inputs: integral ∧ p <= 0 — the post-patch
    # callee MUST accept these (the pre-patch filter RAISED on {integral ∧ p==0};
    # the gold patch makes them in-domain). This is the load-bearing containment.
    for v in integral:
        for p in ps:
            out = floatformat(v, p)   # must not raise
            assert isinstance(out, str), "floatformat(%r,%r) -> %r" % (v, p, out)
            if is_integral(v) and p <= 0:
                assert out == str(int(Decimal(str(v)))) and "." not in out, (
                    "AXIOM-TOO-WEAK-FOR-CALLER: reachable bare-integer input "
                    "(%r,%r) gave %r, not the bare integer" % (v, p, out))
            reached += 1
    # separator-bearing regime reachable inputs: non-integral (any p) — accepted.
    for v in nonintegral:
        for p in ps:
            out = floatformat(v, p)   # must not raise
            assert isinstance(out, str), "floatformat(%r,%r) -> %r" % (v, p, out)
            reached += 1

    # The single class the pre-patch callee was UNDEFINED on is now in-domain:
    assert floatformat("0.00", 0) == "0", floatformat("0.00", 0)
    assert floatformat(Decimal("0.00"), 0) == "0", floatformat(Decimal("0.00"), 0)

    print("AXIOM-CONTAINMENT OK: every model-reachable input (%d sampled across "
          "both regimes and the boundary p in {neg,0,pos}) lies inside the "
          "post-patch floatformat's domain (no raise); the patch-changed class "
          "{integral ∧ p==0} the pre-patch callee raised on is now in-domain. The "
          "caller reaches a subset of the callee's domain; no reachable input is "
          "outside it." % reached)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-rendered",
        "axiom": "rendered",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # A-reference == POST-PATCH floatformat (header note)
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "the A-reference deep model `rendered` (int_render / zeros_seq) "
                     "must equal the REAL floatformat on every caller-reachable input: "
                     "bare-integer regime end-to-end == int_render (no '.'); "
                     "separator-bearing core '.'-bearing; the fix localised (post == "
                     "pre outside the bare-integer regime); number_format digit-content "
                     "preserving; the pre-patch (p<0) core crashes on '0.00' and "
                     "diverges on '5.0'. Any disagreement => the A-reference (hence the "
                     "model's pure region) is unsound (AXIOM-UNSOUND). Embeds the "
                     "bundle's axiom_check.py logic (Django-only imports; no source "
                     "scraping — calls the real callee).",
    },
    {
        "id": "ax-cover-rendered",
        "axiom": "rendered",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every input the model can reach (integral ∧ p<=0 -> bare-integer; "
                     "non-integral / p>0 -> separator-bearing; the boundary p in "
                     "{neg,0,pos}) lies inside the post-patch floatformat's domain (no "
                     "raise). The load-bearing containment: the patch-changed class "
                     "{integral ∧ p==0}, on which the PRE-patch callee RAISED, is now "
                     "in-domain — so the caller reaches exactly the inputs the "
                     "post-patch A-reference is defined on. A reachable input the "
                     "callee rejected/diverged on would be AXIOM-TOO-WEAK-FOR-CALLER; "
                     "none exists (floatformat tolerating MORE — inf/nan/non-numeric "
                     "via earlier guards — is sound over-coverage).",
    },
]
