# properties.py — PBT manifest for sympy__sympy-21612. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json):
#   * bracket_flags(factors: List[Factor]) -> List[bool]
#       READ-ONLY inputs (Acc(...,1/2)):
#         - the list spine:  Acc(list_pred(factors), 1/2)
#         - every element:   Acc(factors[k].parts,1/2) and Acc(factors[k].form,1/2)
#       LOAD-BEARING post (pinned pointwise, in factor order):
#         len(Result()) == len(factors)  AND
#         Forall k in [0,len): Result()[k] == needs_brackets(parts_k, form_k)
#       where needs_brackets(parts, form) := parts != 1 and (form==1 or form==2).
#
#   * needs_brackets / is_composite_form are @Pure helpers, but they are a
#     GROUNDED oracle: they fully unfold to int/bool arithmetic over the ACTUAL
#     element fields (parts_k, form_k) the caller passes -- not an opaque
#     answer-key. So `return needs_brackets(parts,form)` IS the correct value;
#     there is no WRONG echo to build (see assessment). The honest analogue is a
#     cheapest-impl positive control that echoes the Pure helper directly
#     (kept here as the structurally-different positive control).
#
#   * No @ContractOnly axioms (axioms region empty). There IS one A-reference
#     deep model: needs_brackets/is_composite_form vs the real post-patch guard
#     `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))`
#     (form tag 1==Mul, 2==Pow, 0==other; the disjunction form in {1,2} ==
#     isinstance(_, (Mul,Pow))). The axiom lane validates that bijection against
#     the REAL sympy structure in-container (mirrors axiom_check.py), and checks
#     caller-domain containment (the model only ever reaches form in {0,1,2}).
#
# Region-surgery (_swap on _BASE) edits ONLY inside the # impl-start/# impl-end
# region, so every spec case is same_spec by construction (the frozen
# axioms/pure/pre/post-conditions and the loop invariants are never touched).
from pathlib import Path

INSTANCE = "sympy__sympy-21612"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor: the per-iteration decision block. Strictly inside the impl region
# (after `# invariants-end`, before `return result`). Editing only this block
# keeps the frozen spec AND the loop invariants verbatim, so same_spec holds and
# any rejection is attributable to the impl change, not a touched invariant.
# ---------------------------------------------------------------------------
_DECISION = (
    "        f = factors[i]\n"
    "        flag = f.parts != 1 and (f.form == 1 or f.form == 2)\n"
    "        result.append(flag)\n"
    "        i = i + 1\n"
)


# ===========================================================================
# (1) FRAME-MUTATION (a) — MANDATORY: factors[k] fields are read-only
# (Acc(factors[k].parts,1/2) / Acc(factors[k].form,1/2)). A rival that WRITES a
# field of the input element (here factors[i].parts = factors[i].parts, a VALUE
# no-op) while still computing the correct flag must be REJECTED for INSUFFICIENT
# PERMISSION -- the loop holds only 1/2 of factors[i].parts, enough to read but
# not to assign. Gold decision/append kept verbatim so the rejection is
# attributable solely to the write.
# ===========================================================================
_frame_mut_field = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        flag = f.parts != 1 and (f.form == 1 or f.form == 2)\n"
    "        factors[i].parts = f.parts  # WRITE to read-only field -> insufficient permission\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)

# ===========================================================================
# (1) FRAME-MUTATION (b) — write to the list SPINE (Acc(list_pred(factors),1/2)).
# Reassigning factors[i] = f needs full list_pred permission; the caller grants
# only 1/2. VALUE no-op (writes back the same handle), so a real patch mutating
# the denominator list in place would still compute the same flags -- the value
# abstraction cannot see it. Must be rejected for INSUFFICIENT PERMISSION.
# ===========================================================================
_frame_mut_spine = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        flag = f.parts != 1 and (f.form == 1 or f.form == 2)\n"
    "        factors[i] = f  # WRITE to read-only list spine -> insufficient permission\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)


# ===========================================================================
# (2) PARTIAL-DOMAIN / pre-patch defect — drop the power (form==2) disjunct, so
# the guard tests only the PRODUCT form. This is exactly model_prepatch.py and
# the literal pre-patch repo guard isinstance(item.base, Mul). Correct on every
# product-form and atomic factor, WRONG only on a power-form reciprocal with
# parts != 1 (the issue's 1/(1/y) factor, form==2). The postcondition pins
# Result()[k] == needs_brackets(...) which is True there, so the loop invariant
# fails on the first such factor.
# ===========================================================================
_partial_product_only = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        flag = f.parts != 1 and (f.form == 1)  # pre-patch: only product form is composite\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)

# ===========================================================================
# (2b) PARTIAL-DOMAIN / over-wide form test — treat ANY non-atomic form
# (form != 0) as composite, i.e. form in {1,2,3,...}. Correct on every factor
# whose form tag is 0/1/2 (the only tags the F2P witnesses produce), but the
# postcondition predicate is form in {1,2}; for any factor with form >= 3 and
# parts != 1 it returns True while needs_brackets returns False. The Factor
# precondition only requires form >= 0, so form == 3 is an admissible input the
# postcondition decides the other way -> loop invariant fails.
# Refinement: the faithful real patch widening this would be
#   isinstance(item.base, (Mul, Pow, Add))  (or any extra class)
# which brackets an Add-based denominator the gold guard leaves bare; sympy's
# test_Mul/test_Add string assertions for additive denominators (e.g. terms
# rendered without that extra bracketing) would then mismatch, so it does NOT
# resolve.
# ===========================================================================
_partial_overwide = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        flag = f.parts != 1 and (f.form != 0)  # over-wide: brackets any non-atomic form, incl. form>=3\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)

# ===========================================================================
# (3) PART-COUNT DOUBLE-MASK — replace the `parts != 1` test with `parts != 0`.
# Equivalent on most fuzz inputs (most reciprocated quantities have >= 2 parts),
# but it FLIPS exactly on a one-part composite reciprocal (parts == 1, form in
# {1,2}): gold returns False (a single-part product/power is left bare) while
# this returns True. parts == 1 with form == 1/2 is an admissible input
# (Requires only parts >= 0, form >= 0).
# Refinement: the faithful real-patch correspondent drops the `len(...) != 1`
# guard, so a single-argument Mul/Pow base would be bracketed when the gold
# guard leaves it bare; the #14160-style invariants in test_Mul (which keep
# certain single-part bases un-bracketed) would mismatch -> does NOT resolve.
# ===========================================================================
_partcount_mask = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        flag = f.parts != 0 and (f.form == 1 or f.form == 2)  # wrong: != 0 not != 1\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)

# ===========================================================================
# (4) CONSTANT-FALSE cheapest-wrong — never bracket anything. Trivially correct
# on factors that genuinely don't need brackets; WRONG on the issue's power-form
# reciprocal (and every composite factor). len(Result())==len(factors) still
# holds, so only the per-factor pin catches it.
# Refinement: corresponds to deleting the pow_paren collection entirely (never
# append to pow_paren); every denominator factor renders bare -> the exact
# reported bug `x/1/y` and also breaks `-2*x/(y*y)`. Does NOT resolve.
# ===========================================================================
_const_false = _swap(
    _BASE,
    _DECISION,
    "        flag = False  # never brackets: ignores parts/form entirely\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)


# ===========================================================================
# (5) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT. The
# decision is recomputed by (a) reading the two fields into named locals, (b)
# expressing the part-count test as `not (p == 1)` instead of `p != 1`, and (c)
# computing the form test via the @Pure helper `is_composite_form(g)` rather than
# the inline disjunction. All three are provably equal to the gold flag, so the
# loop invariant `result[k] == needs_brackets(parts_k, form_k)` still discharges.
# This is a local-variable / equivalent-expression reshape (pilot-safe: no loop
# direction flip, no dropped framing assert, no forward-append-vs-fold mismatch).
# If a faithful correct impl of this shape cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        p = f.parts\n"
    "        g = f.form\n"
    "        flag = (not (p == 1)) and is_composite_form(g)\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)


# ===========================================================================
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input. The
# loop already reads factors[i].parts / .form under the 1/2 permissions; we add
# an Assert (inside the impl) that the read-only halves are present and the
# per-element decision matches the Pure oracle on a representative factor, then
# proceed with the gold decision unchanged. If the Requires could not be
# established for a legitimate factor list this Assert would not verify =>
# PRECOND-TOO-STRONG. Uses only permissions the gold proof already holds.
# ===========================================================================
_admiss = _swap(
    _BASE,
    _DECISION,
    "        f = factors[i]\n"
    "        Assert(Acc(factors[i].parts, 1 / 2) and Acc(factors[i].form, 1 / 2))\n"
    "        flag = f.parts != 1 and (f.form == 1 or f.form == 2)\n"
    "        Assert(flag == needs_brackets(f.parts, f.form))\n"
    "        result.append(flag)\n"
    "        i = i + 1\n",
)


SPEC_TESTS = [
    {
        "id": "frame-mut-field",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_field,
        "refinement": (
            "factors[i].parts = f.parts writes back the SAME value, a no-op on the "
            "flag value, so a 'faithful' real patch that mutated a denominator "
            "factor's facet in place would still compute the same bracketing flags "
            "and could look correct on test_Mul -- the value abstraction is blind "
            "to the write. The gold patch never mutates the denominator item "
            "(_print_Mul only READS item.args[0].args and item.base to decide "
            "pow_paren membership); a mutating patch would corrupt a shared/cached "
            "sympy expression and is unfaithful. The spec must reject it on "
            "PERMISSION grounds."
        ),
        "rationale": (
            "Rejection comes from the permission system: factors[i].parts = ... "
            "needs full write permission to factors[i].parts, but the "
            "precondition/invariant grant only Acc(factors[i].parts, 1/2). "
            "INSUFFICIENT PERMISSION, not a postcondition failure."
        ),
    },
    {
        "id": "frame-mut-spine",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_spine,
        "refinement": (
            "factors[i] = f reassigns the same handle (value no-op), so a real "
            "patch mutating the denominator list in place would still produce the "
            "same flag list and pass the F2P value checks. The gold guard only "
            "iterates and reads the denominator items; it never rebinds the list, "
            "so a mutating patch is unfaithful."
        ),
        "rationale": (
            "Rejection from the permission system: assigning factors[i] needs full "
            "list_pred(factors) permission; the caller holds only Acc(list_pred("
            "factors), 1/2). INSUFFICIENT PERMISSION."
        ),
    },
    {
        "id": "partial-product-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_product_only,
        "refinement": (
            "Dropping the form==2 (power) disjunct is exactly the PRE-PATCH repo "
            "guard isinstance(item.base, Mul) (model_prepatch.py). It is correct on "
            "every product-form / atomic denominator factor but leaves a power-form "
            "reciprocal with parts != 1 un-bracketed -- precisely the issue's "
            "1/(1/y) factor (form==2, parts==2). The faithful real patch is the "
            "literal pre-patch code, which renders the issue expression as the "
            "buggy 'x/1/y' instead of 'x/(1/y)', so F2P test_Mul's issue-21537 "
            "assertion fails: it does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()[k] == needs_brackets("
            "parts_k, form_k): on a factor with form==2 and parts!=1, "
            "needs_brackets is True but this impl produces False, so the loop "
            "invariant / postcondition equality fails."
        ),
    },
    {
        "id": "partial-overwide-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_overwide,
        "refinement": (
            "form != 0 brackets ANY non-atomic form, including form >= 3 which the "
            "gold predicate (form in {1,2}) leaves bare. The Factor precondition "
            "admits form==3, so this is a reachable input decided the other way. "
            "The faithful real-patch widening would be isinstance(item.base, (Mul, "
            "Pow, <extra class>)) -- bracketing a denominator base class the gold "
            "guard leaves bare; sympy's existing test_Mul/test_Add string "
            "assertions for those denominators would mismatch, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejection from the postcondition: needs_brackets uses "
            "is_composite_form(form) == (form==1 or form==2); for form==3, parts!=1 "
            "the spec value is False but this impl yields True, breaking the "
            "per-factor equality."
        ),
    },
    {
        "id": "partcount-double-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partcount_mask,
        "refinement": (
            "Replacing parts != 1 with parts != 0 agrees on every reciprocated "
            "quantity with >= 2 parts (the common case) but FLIPS on a single-part "
            "composite (parts == 1, form in {1,2}): gold leaves it bare, this "
            "brackets it. The faithful real correspondent drops the len(...) != 1 "
            "guard, so a single-argument Mul/Pow base would be bracketed; the "
            "#14160-style single-part invariants the test_Mul suite pins (a "
            "single-part base left un-bracketed) would mismatch, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejection from the postcondition: needs_brackets requires parts != 1; "
            "for parts==1, form in {1,2} the spec value is False but this impl "
            "yields True, breaking the per-factor equality. parts==1 is an "
            "admissible input (Requires only parts >= 0)."
        ),
    },
    {
        "id": "const-false-cheapest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _const_false,
        "refinement": (
            "Returning all-False never brackets any factor -- it corresponds to "
            "deleting the pow_paren collection entirely, so every denominator "
            "renders bare: the issue's 'x/1/y' bug AND a regression on "
            "'-2*x/(y*y)'. test_Mul asserts both bracketed forms, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejection from the postcondition: on any factor with parts != 1 and "
            "form in {1,2}, needs_brackets is True but this impl yields False, "
            "breaking the per-factor equality (len(Result())==len(factors) alone "
            "is not enough)."
        ),
    },
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl,
        "rationale": (
            "A structurally-different but CORRECT impl: fields hoisted to named "
            "locals, the part-count test written as `not (p == 1)` (== p != 1), and "
            "the form test computed via the @Pure helper is_composite_form(g) "
            "instead of the inline disjunction -- all provably equal to the gold "
            "flag, so the loop invariant result[k]==needs_brackets(...) still "
            "discharges. It MUST verify; if it cannot, the postcondition is "
            "SPEC-TOO-STRONG. Local-variable / equivalent-expression reshape only "
            "(pilot-safe: no loop-direction flip, no dropped framing assert)."
        ),
    },
    {
        "id": "admiss-selfread",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The precondition Acc(list_pred(factors),1/2) + per-element 1/2 facet "
            "permissions must admit a normal F2P-shaped factor list: the Assert "
            "confirms both read-only halves are present at the loop body and that "
            "the per-factor decision equals the Pure oracle on a representative "
            "factor, then the gold decision proceeds unchanged. If the Requires "
            "could not be established for a legitimate input this would not verify "
            "=> PRECOND-TOO-STRONG. Uses only permissions the gold proof holds."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — no @ContractOnly axioms, but ONE A-reference deep model:
# needs_brackets / is_composite_form must equal the REAL post-patch guard
# `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` on every
# caller-reachable denominator factor (form tag 1==Mul, 2==Pow, 0==other). The
# probe mirrors axiom_check.py: build the issue (21537) and #14160 real
# unevaluated expressions in-container, extract each denominator item's real
# (len(item.args[0].args), form-of(item.base)) facets, and assert the model
# predicate equals the real post-patch guard, differs from the pre-patch guard
# EXACTLY on the issue's power-form reciprocal, and confirm the rendered strings.
# It also performs the CONTAINMENT check: every form tag the model can reach is
# in {0,1,2} and parts >= 0, so the bijection covers the caller's whole reach.
#
# axiom_check.py is read on the HOST at load time and its main() logic is
# embedded into the self-contained probe (the runner mounts ONLY the probe at
# /work; model.py / axiom_check.py are NOT in-container). The probe imports only
# stdlib + sympy (the repo under test), prints a diagnostic, sys.exit(0) iff the
# A-reference obligation holds.
# ===========================================================================
_AXREF_PROBE = r'''
import sys

# --- model.py reference predicate (kept in lock-step with the frozen spec) ---
def is_composite_form(form):
    return form == 1 or form == 2

def needs_brackets(parts, form):
    return parts != 1 and is_composite_form(form)

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

from sympy import symbols, Mul, Pow, S

x, y = symbols('x y')

def form_tag(base):
    # model's structural-form tag (mapping.md s2): 1 product, 2 power, 0 other.
    # Order matters: a Pow is not a Mul; check Mul first then Pow.
    if isinstance(base, Mul):
        return 1
    if isinstance(base, Pow):
        return 2
    return 0

def real_guard_post(item):
    return (len(item.args[0].args) != 1 and
            isinstance(item.base, (Mul, Pow)))

def real_guard_pre(item):
    return (len(item.args[0].args) != 1 and
            isinstance(item.base, Mul))

# Witnesses: the issue (21537) and the #14160 case the test_Mul guard pins.
issue = Mul(x, Pow(1 / y, -1, evaluate=False), evaluate=False)
case14160 = Mul(-2, x,
                Pow(Mul(y, y, evaluate=False), -1, evaluate=False),
                evaluate=False)

def denom_items(expr):
    # the denominator items the gather loop sees: commutative Pow factors with
    # exp == -1 (mapping.md s1).
    out = []
    for item in expr.args:
        if (getattr(item, 'is_commutative', False) and
                isinstance(item, Pow) and
                item.exp is S.NegativeOne):
            out.append(item)
    return out

checked = 0
pre_post_disagreements = []

for name, expr in (('issue21537', issue), ('issue14160', case14160)):
    for item in denom_items(expr):
        parts = len(item.args[0].args)
        form = form_tag(item.base)

        # CONTAINMENT: every facet the model reaches must be in the abstraction's
        # domain (form tag in {0,1,2}, parts >= 0). A facet outside this would be
        # AXIOM-TOO-WEAK-FOR-CALLER.
        if form not in (0, 1, 2):
            fail("form tag %r out of model domain {0,1,2} on %s factor %r"
                 % (form, name, item))
        if parts < 0:
            fail("parts %r < 0 out of model domain on %s factor %r"
                 % (parts, name, item))

        model = needs_brackets(parts, form)
        post = real_guard_post(item)
        pre = real_guard_pre(item)

        # SOUNDNESS: deep model == real POST-patch guard on every reachable factor.
        if model != post:
            fail("deep model unsound on %s factor %r: needs_brackets(%r,%r)=%r "
                 "but real post-patch guard=%r"
                 % (name, item, parts, form, model, post))
        checked += 1

        if pre != post:
            pre_post_disagreements.append((name, item, parts, form))

# The change is observable: exactly the issue's 1/y factor flips, nothing in
# #14160 flips.
if len(pre_post_disagreements) != 1:
    fail("expected exactly one pre/post guard disagreement (the bug); got %r"
         % (pre_post_disagreements,))
else:
    name, item, parts, form = pre_post_disagreements[0]
    if not (name == 'issue21537' and form == 2 and parts != 1):
        fail("discriminating factor must be the issue's power-form reciprocal "
             "(form=2, parts!=1); got %r" % ((name, parts, form),))

# Rendered strings: with the gold patch applied in-container the issue renders
# bracketed and #14160 is preserved.
s_issue = str(issue)
s_14160 = str(case14160)
if s_14160 != '-2*x/(y*y)':
    fail("#14160 rendering drifted: %r" % (s_14160,))
if s_issue != 'x/(1/y)':
    fail("issue rendering not the post-patch bracketed form: %r" % (s_issue,))

if FAIL:
    print("A-REF FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("A-REF OK: deep model needs_brackets == real post-patch guard on %d "
      "denominator factors; exactly 1 pre/post disagreement (the issue's "
      "power-form reciprocal 1/y); #14160 unchanged; issue str=%r; every reached "
      "form tag in {0,1,2}." % (checked, s_issue))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-formguard-ref",
        "axiom": "needs_brackets / is_composite_form (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXREF_PROBE,
        "rationale": (
            "A-reference: the deep model needs_brackets/is_composite_form must "
            "equal the real post-patch guard `len(item.args[0].args) != 1 and "
            "isinstance(item.base, (Mul, Pow))` on every caller-reachable "
            "denominator factor. The probe builds the issue (21537) and #14160 "
            "real unevaluated expressions, extracts each denominator item's real "
            "(len(item.args[0].args), form-of(item.base)) facets, and asserts the "
            "model predicate equals the real post-patch guard and differs from the "
            "pre-patch guard EXACTLY on the issue's power-form reciprocal -- plus a "
            "containment check that every reached form tag is in {0,1,2}. "
            "Divergence is an A-reference unsoundness (verify would not imply "
            "resolve); a facet outside {0,1,2} would be AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
