# properties.py — PBT manifest for sympy__sympy-17139. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Each SPEC_TESTS["module"] is a FULL model.py built by region-surgery: we read
# the frozen model.py and _swap text ONLY inside the # impl-start / # impl-end
# region, so the spec (axioms / pure / pre / post) is provably untouched
# (markers.same_spec stays True). AXIOM_TESTS probes execute the REAL sympy
# callees in the instance Docker image (apply_gold=True).
#
# Defended surface (read model.py + refinement.md + mapping.md + instance.json):
#   transform_power(is_target, exp, max, pow) -> int (branch tag 0/1/2).
#   - exp: Expon is a READ-ONLY input — Requires/Ensures Acc(exp.real,1/2) and
#     Acc(exp.value,1/2). Half permission => a rival that WRITES exp cannot get
#     the full permission it needs and is rejected for INSUFFICIENT PERMISSION.
#   - The discriminating fix is the `if not exp.real: return 0` guard that
#     PRECEDES order_lt_zero/order_gt_max, whose Requires(e.real) the proof
#     CONSUMES. Drop the guard => the ordering call's precondition cannot be
#     established (mirrors the real TypeError on sin(x)**I).
#   - is_perfect_power is @Pure @ContractOnly with NO value Ensures (only
#     determinism). The postcondition that branches on it (pow-true arm) is
#     GROUNDED in exp.value, not an opaque answer-key oracle: there is no wrong
#     echo to build. (See 'assessment'.) The two ordering axioms have grounded
#     Ensures(Result()==(e.value<0)/(e.value>m)).
#   - The post-guard dispatch pins every magnitude sub-case (==1,==2,==4, parity
#     under !pow, perfect-power under pow). Partial-domain rivals that flip a
#     single sub-case are the residual SPEC-TOO-WEAK risk; each is targeted.

from pathlib import Path

INSTANCE = "sympy__sympy-17139"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region (verbatim from model.py, between the markers).
_GOLD_IMPL = """    if not is_target:
        return 0
    if not exp.real:
        return 0
    if order_lt_zero(exp) == True:
        return 0
    if order_gt_max(exp, max) == True:
        return 0
    if exp.value == 1:
        return 0
    if exp.value == 2:
        return 1
    else:
        if exp.value == 4:
            return 2
        elif not pow:
            if exp.value % 2 == 1:
                return 0
            return 2
        else:
            if not is_perfect_power(exp.value):
                return 0
            return 2"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Return a full model.py source with the impl region body replaced.
    Only text strictly between the impl markers changes => same_spec holds."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

SPEC_TESTS = [

    # === 6. ADMISSIBILITY ===================================================
    # The precondition must admit a normal F2P-shaped input. We assert it by
    # having the impl reach (and discharge) every postcondition branch on a
    # representative carrier exactly as gold does — if the Requires were too
    # strong, the gold impl itself would not verify. As an explicit
    # admissibility witness we additionally build an F2P-shaped Expon (real,
    # value 6) inside the impl and call transform_power's guards on it via a
    # local helper-free path: the gold body already exercises is_target=True,
    # real exponent, in-range value, both pow arms. A pure positive
    # restatement (same control flow) is the cleanest admissibility proof.
    {
        "id": "admiss-gold",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_GOLD_IMPL),  # identity: the frozen gold impl
        "rationale": "the frozen gold impl must verify against its own frozen "
                     "spec; if it did not the precondition (Acc 1/2 on exp, "
                     "max>=4) would be PRECOND-TOO-STRONG. Identity positive "
                     "control / admissibility witness.",
    },

    # === 5. POSITIVE CONTROL (soundness) ====================================
    # A structurally-DIFFERENT but behaviourally CORRECT impl. The gold body is
    # a cascade of `if ... return`; this variant reshapes it: it first computes
    # the not-eligible / non-real / out-of-range short-circuits, then handles
    # the in-range magnitudes with a SINGLE nested dispatch whose branch ORDER
    # is reversed (perfect-power/pow arm tested via an explicit boolean local,
    # value==4 checked last inside the rewrite group). No induction lemma is
    # needed (straight-line branch logic over a scalar carrier), so the gold
    # proof stays valid. MUST verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # short-circuits first (different grouping, same outcomes)\n"
            "    if not is_target or not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True or order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    # in-range real magnitude dispatch, branches reordered\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    if exp.value == 4:\n"
            "        return 2\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if pow:\n"
            "        if is_perfect_power(exp.value):\n"
            "            return 2\n"
            "        return 0\n"
            "    if exp.value % 2 == 0:\n"
            "        return 2\n"
            "    return 0"
        ),
        "rationale": "a correct impl with reordered branches (==2/==4/==1 then "
                     "the pow fork, even-test phrased as %2==0 instead of !=1) "
                     "is behaviourally identical to gold on every in-domain "
                     "input and keeps the gold proof valid (straight-line scalar "
                     "dispatch, no induction). Must verify; else SPEC-TOO-STRONG.",
    },

    # === 1. FRAME-MUTATION (MANDATORY: exp is read-only at Acc(...,1/2)) =====
    # A rival that WRITES the read-only input exp to satisfy a postcondition
    # vacuously. exp is held at half permission (Acc 1/2) by both Requires and
    # Ensures; writing exp.value needs FULL permission, which the caller does
    # not grant. Must be rejected for INSUFFICIENT PERMISSION. The body is
    # otherwise the gold dispatch, so the rejection is attributable to the
    # write, not to a value error.
    {
        "id": "frame-write-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    # ATTACK: overwrite the read-only exponent magnitude (only 1/2\n"
            "    # permission held -> insufficient to assign). Folds the input to\n"
            "    # value 2 so the squared-rewrite postcondition becomes trivial.\n"
            "    exp.value = 2\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "the real _f never assigns to rv.exp; mutating the node's "
                      "exponent in place would corrupt the bottom_up traversal "
                      "and the rewrite of every sibling node, so the faithful "
                      "real patch is a no-write guard insertion and a mutating "
                      "patch would NOT resolve test__TR56 / test_issue_17137.",
        "rationale": "rejected by the PERMISSION SYSTEM: writing exp.value "
                     "requires Acc(exp.value, 1) but the precondition grants "
                     "only Acc(exp.value, 1/2); also the Ensures(Acc(exp.value, "
                     "1/2)) frame cannot be re-established after a full write. "
                     "A byte-fuzzer never constructs this — directive 5.",
    },

    # === 1b. FRAME-MUTATION on the other read-only field (supporting) =======
    {
        "id": "frame-write-real",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    # ATTACK: flip the read-only realness flag to force the\n"
            "    # not-real short-circuit on EVERY node. Needs full permission\n"
            "    # on exp.real (only 1/2 held).\n"
            "    exp.real = False\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "writing rv.exp.is_real is not even an operation the real "
                      "patch performs (is_real is a derived SymPy assumption, "
                      "not assignable); a patch that forced every node unchanged "
                      "would fail the rewrite F2P assertions (sin(x)**6 must be "
                      "rewritten), so it would NOT resolve test__TR56.",
        "rationale": "rejected by the PERMISSION SYSTEM: exp.real held at "
                     "Acc(...,1/2), assignment needs full permission and breaks "
                     "the Ensures frame. Supporting frame-mutation case.",
    },

    # === 3. PARTIAL-DOMAIN: the historical D1 defect (odd => rewrite) =======
    # A rival correct on most of the domain but flipping the odd-magnitude,
    # not-pow sub-case from UNCHANGED (0) to REWRITTEN (2). This is exactly the
    # D1 defect the 2nd-pass fix repaired; the spec's clause
    #   Implies(... !=1 !=2 !=4 and not pow and value%2==1, Result()==0)
    # must reject it. Must be rejected; else SPEC-TOO-WEAK on the F2P input
    # T(sin(x)**3, ..., 4, False) == sin(x)**3.
    {
        "id": "partial-odd-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            # ATTACK: rewrite ALL in-range magnitudes (drop the odd\n"
            "            # short-circuit). Diverges from gold on every odd>4 mag.\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "gold _f returns odd magnitudes UNCHANGED under pow=False "
                      "(`if rv.exp % 2: return rv`, fu.py:516); the F2P test "
                      "asserts T(sin(x)**3, sin, cos, h, 4, False) == sin(x)**3 "
                      "(unchanged). A patch that rewrote odd magnitudes would "
                      "produce (1-cos**2)**1 and FAIL that assertion, not "
                      "resolving test__TR56.",
        "rationale": "rejected by the postcondition clause Implies(is_target and "
                     "exp.real and 0<=value<=max and value!=1,2,4 and not pow "
                     "and value%2==1, Result()==0) (model.py:148-151): the rival "
                     "returns 2 where the spec mandates 0 for an odd magnitude.",
    },

    # === 3b. PARTIAL-DOMAIN: even => unchanged (parity inverted) ============
    # Mirror of D1: rewrite ODD, leave EVEN unchanged under not-pow. Wrong on
    # the F2P sin(x)**6/pow=False (must be rewritten, code 2). The even-arm
    # clause Implies(... not pow and value%2==0, Result()==2) rejects it.
    {
        "id": "partial-even-unchanged",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            # ATTACK: parity inverted -- even unchanged, odd rewrite\n"
            "            if exp.value % 2 == 0:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "gold rewrites EVEN magnitudes under pow=False (e = "
                      "rv.exp//2; fu.py:517); F2P asserts T(sin(x)**6, sin, cos, "
                      "h, 6, False) == (1-cos**2)**3 (rewritten). A patch that "
                      "left even magnitudes unchanged would FAIL that assertion, "
                      "not resolving test__TR56.",
        "rationale": "rejected by Implies(... not pow and value%2==0, "
                     "Result()==2) (model.py:152-155): the rival returns 0 where "
                     "the spec mandates 2 for an even in-range magnitude (e.g. 6).",
    },

    # === 3c. PARTIAL-DOMAIN: ignore pow, always use the parity arm ==========
    # A rival that ignores the `pow` flag and applies the not-pow (parity) rule
    # to BOTH arms. Diverges under pow=True: e.g. value 6 (even, NOT a perfect
    # power) -> gold returns 0 (perfect_power(6) falsy) but this returns 2; and
    # value 9 (odd, perfect power) -> gold returns 2 but this returns 0. The
    # perfect-power clauses pin both, so it must be rejected.
    {
        "id": "partial-ignore-pow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        else:\n"
            "            # ATTACK: ignore pow; always use the parity rule.\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "the gold pow=True arm gates on perfect_power, NOT parity; "
                      "F2P asserts T(sin(x)**6, sin, cos, h, 6, True) == sin(x)**6 "
                      "(unchanged: 6 is even but not a perfect power) and "
                      "T(sin(x)**8, sin, cos, h, 10, True) == (1-cos**2)**4 "
                      "(rewritten: 8 is a perfect power). A parity-only patch "
                      "would rewrite 6 and so FAIL the sin(x)**6/True assertion, "
                      "not resolving test__TR56.",
        "rationale": "rejected by the pow-true clauses Implies(... pow and "
                     "is_perfect_power(value), Result()==2) and Implies(... pow "
                     "and not is_perfect_power(value), Result()==0) (model.py:"
                     "159-166): for value=6, pow=True the spec mandates 0 (6 is "
                     "not a perfect power) but the rival returns 2.",
    },

    # === 3d. PARTIAL-DOMAIN: squared case mislabeled (boundary value 2) =====
    # The value==2 case is special (its own result code 1, the squared-form
    # rewrite). A rival that returns the GENERAL code 2 for value==2 diverges
    # only on that single magnitude. The dedicated clause Implies(... value==2,
    # Result()==1) rejects it.
    {
        "id": "partial-squared-as-general",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    # ATTACK: collapse the squared-base special case into the\n"
            "    # general rewrite (code 2 instead of code 1).\n"
            "    if exp.value == 2:\n"
            "        return 2\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "gold's value==2 branch is the squared-base rewrite "
                      "`return h(g(rv.base.args[0])**2)` (fu.py:508-509), a "
                      "DIFFERENT expression shape from the general "
                      "`h(g(...)**2)**e`; the P2P TR5/TR6/TR56 trig-rewrite "
                      "tests pin the squared form, so a patch emitting the "
                      "general shape for the square would produce the wrong "
                      "expression and not resolve the rewrite tests.",
        "rationale": "rejected by the dedicated clause Implies(is_target and "
                     "exp.real and 0<=value<=max and value==2, Result()==1) "
                     "(model.py:138-140): the rival returns 2 where the spec "
                     "mandates the squared code 1.",
    },

    # === 2 / CONTROL-FLOW: drop the non-real guard (the prepatch DEFECT) ====
    # The discriminating fix is `if not exp.real: return 0` PRECEDING the
    # ordering. Dropping it calls order_lt_zero(exp) with exp.real possibly
    # false, violating its Requires(e.real). Must be rejected for an
    # UNSATISFIED PRECONDITION of the axiom — the spec sensing the bug exactly
    # as model_prepatch.py does. This is the canonical verify=>resolve guard:
    # a verifying rival here would be the prepatch crashing on sin(x)**I.
    {
        "id": "drop-nonreal-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    # ATTACK: omit `if not exp.real: return 0` -- the prepatch bug.\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "this IS the prepatch (`_f` without the added "
                      "`if not rv.exp.is_real: return rv`); on sin(x)**I the "
                      "real `(rv.exp < 0)` raises TypeError('Invalid comparison "
                      "of complex I') (expr.py:406). The F2P test_issue_17137 "
                      "and the sin(x)**I/sin(x)**(2*I+1) assertions in "
                      "test__TR56 crash, so it does NOT resolve.",
        "rationale": "rejected by the PRECONDITION of order_lt_zero "
                     "(Requires(e.real)): without the non-real short-circuit the "
                     "call site cannot establish exp.real (it may be False), and "
                     "the postcondition Implies(is_target and not exp.real, "
                     "Result()==0) also cannot be met since the unchanged path "
                     "is skipped. Same failure as model_prepatch.py:173.",
    },

    # === 2b / CONTROL-FLOW: guard placed AFTER ordering (too late) ==========
    # A subtler variant: keep the non-real return-0 but place it AFTER the
    # ordering calls. The ordering precondition Requires(e.real) is still
    # unmet at the first call, so it must be rejected — proving the spec pins
    # the GUARD ORDER (the actual content of the gold change), not merely the
    # presence of a non-real branch somewhere.
    {
        "id": "guard-after-ordering",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    if order_gt_max(exp, max) == True:\n"
            "        return 0\n"
            "    # ATTACK: non-real guard present but AFTER the ordering (the\n"
            "    # gold change is specifically the guard PLACEMENT before it).\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "placing the guard after the ordering still evaluates "
                      "`rv.exp < 0` on a non-real exponent first => the same "
                      "TypeError crash on sin(x)**I as the prepatch. The gold "
                      "fix is precisely the guard placed BEFORE the ordering "
                      "(fu.py:+503 before :504), so a late-guard patch would "
                      "NOT resolve test_issue_17137.",
        "rationale": "rejected by the PRECONDITION of order_lt_zero "
                     "(Requires(e.real)) at the first ordering call: exp.real is "
                     "not yet established there. The spec pins guard ORDER, not "
                     "mere presence.",
    },

    # === SUPPORTING near-miss: out-of-range over-max mislabeled =============
    # value > max must be UNCHANGED (code 0). A rival that rewrites it (code 2)
    # diverges on the F2P T(sin(x)**10, ..., 4, False) == sin(x)**10. Cheap
    # supporting partial-domain case (carries a real refinement).
    {
        "id": "over-max-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not is_target:\n"
            "        return 0\n"
            "    if not exp.real:\n"
            "        return 0\n"
            "    if order_lt_zero(exp) == True:\n"
            "        return 0\n"
            "    # ATTACK: drop the >max short-circuit; rewrite over-max mags.\n"
            "    if exp.value == 1:\n"
            "        return 0\n"
            "    if exp.value == 2:\n"
            "        return 1\n"
            "    else:\n"
            "        if exp.value == 4:\n"
            "            return 2\n"
            "        elif not pow:\n"
            "            if exp.value % 2 == 1:\n"
            "                return 0\n"
            "            return 2\n"
            "        else:\n"
            "            if not is_perfect_power(exp.value):\n"
            "                return 0\n"
            "            return 2"
        ),
        "refinement": "gold returns over-max magnitudes unchanged "
                      "(`if (rv.exp > max) == True: return rv`, fu.py:506); F2P "
                      "asserts T(sin(x)**10, sin, cos, h, 4, False) == sin(x)**10 "
                      "(unchanged, 10 > max 4). A patch that rewrote over-max "
                      "magnitudes would FAIL that assertion, not resolving "
                      "test__TR56.",
        "rationale": "rejected by Implies(is_target and exp.real and "
                     "exp.value > max, Result()==0) (model.py:132): the rival "
                     "drops the >max short-circuit and returns 2 for value 10, "
                     "max 4, where the spec mandates 0. Supporting case.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# Three axiomatized callees: order_lt_zero / order_gt_max (A-consumed,
# Expr.__lt__ / __gt__) and is_perfect_power (A-reference, bool(perfect_power)).
# Soundness + caller-domain containment probes execute the REAL sympy callees
# (apply_gold=True; sympy 1.5 in the instance image). Imports only sympy +
# stdlib. Each prints a diagnostic and sys.exit(0) iff the obligation holds.

AXIOM_TESTS = [

    # --- order_lt_zero / order_gt_max : AXIOM-SOUNDNESS ----------------------
    # On the axioms' VALUE domain (real integer exponent) the real ordering
    # `(exp < 0) == True` / `(exp > m) == True` must agree with the encoded
    # Ensures (value<0 / value>m). Fuzz boundaries + sentinels.
    {
        "id": "ax-sound-ordering-value",
        "axiom": "order_lt_zero,order_gt_max",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "from sympy import Integer\n"
            "rng = random.Random(17139)\n"
            "boundary = [-100, -5, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10, 20, 100]\n"
            "maxes = [4, 6, 10, 30]\n"
            "checked = 0\n"
            "def lt0(e):\n"
            "    return (e < 0) == True\n"
            "def gtm(e, m):\n"
            "    return (e > m) == True\n"
            "for v in boundary:\n"
            "    e = Integer(v)\n"
            "    for m in maxes:\n"
            "        assert lt0(e) == (v < 0), 'order_lt_zero unsound at v=%d' % v\n"
            "        assert gtm(e, m) == (v > m), 'order_gt_max unsound v=%d m=%d' % (v, m)\n"
            "        checked += 1\n"
            "for _ in range(20000):\n"
            "    v = rng.randint(-60, 60); m = rng.randint(4, 40)\n"
            "    e = Integer(v)\n"
            "    assert lt0(e) == (v < 0), 'order_lt_zero unsound at v=%d' % v\n"
            "    assert gtm(e, m) == (v > m), 'order_gt_max unsound v=%d m=%d' % (v, m)\n"
            "    checked += 1\n"
            "print('AX-SOUND ordering VALUE ok: %d checks, real ordering == "
            "integer comparison on all real integer exponents' % checked)\n"
            "sys.exit(0)\n"
        ),
        "rationale": "if the real Expr.__lt__/__gt__ disagreed with value<0 / "
                     "value>m on any real integer exponent the axioms' Ensures "
                     "would be AXIOM-UNSOUND. The proof consumes these values to "
                     "discharge the unchanged-branch postconditions.",
    },

    # --- order_lt_zero / order_gt_max : DOMAIN soundness + necessity --------
    # On a NON-real exponent (outside the axioms' Requires(e.real) domain) the
    # real ordering must RAISE TypeError. This proves the precondition is both
    # sound (the model never claims a value there) and NECESSARY (the operation
    # is genuinely undefined). Mirrors the real crash on sin(x)**I.
    {
        "id": "ax-domain-raises-nonreal",
        "axiom": "order_lt_zero,order_gt_max",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "from sympy import I, Integer\n"
            "nonreal = [I, 2*I + 1, 3*I, Integer(2) + 3*I, 1 - I, -I, I/2, 5*I - 7]\n"
            "for e in nonreal:\n"
            "    assert e.is_real is not True, 'setup: %r should be non-real' % e\n"
            "    for op, nm in ((lambda: (e < 0) == True, 'exp<0'),\n"
            "                   (lambda: (e > 4) == True, 'exp>max')):\n"
            "        raised = False\n"
            "        try:\n"
            "            op()\n"
            "        except TypeError:\n"
            "            raised = True\n"
            "        assert raised, ('axiom DOMAIN unsound: %s did NOT raise on "
            "non-real %r; Requires(e.real) must exclude it' % (nm, e))\n"
            "print('AX-DOMAIN ok: real ordering RAISES TypeError on %d non-real "
            "exponents -> Requires(e.real) sound AND necessary' % len(nonreal))\n"
            "sys.exit(0)\n"
        ),
        "rationale": "the axioms' Requires(e.real) is the SAFE non-raising "
                     "domain. If the real ordering did NOT raise on a non-real "
                     "exponent the precondition would be unnecessary; if it "
                     "raised on a real one the proof would be unsound. This "
                     "pins the exact crash the gold fix avoids (sin(x)**I).",
    },

    # --- is_perfect_power : A-REFERENCE soundness ---------------------------
    # is_perfect_power(n) (the boolean the pow-true arm branches on) must equal
    # bool(perfect_power(n)) on every magnitude the dispatch can consult. Fuzz
    # boundaries + the F2P-relevant 6,8 + perfect/non-perfect powers.
    {
        "id": "ax-ref-perfect-power",
        "axiom": "is_perfect_power",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": (
            "import sys, random\n"
            "from sympy import perfect_power\n"
            "def ref(n):\n"
            "    return bool(perfect_power(n))\n"
            "rng = random.Random(17139)\n"
            "boundary = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 18, 20, 25, 27,\n"
            "            32, 36, 49, 50, 64, 100, 128]\n"
            "# documented perfect / non-perfect classifications (the dispatch\n"
            "# branches on exactly this boolean under pow=True):\n"
            "known = {6: False, 8: True, 9: True, 10: False, 16: True, 25: True,\n"
            "         27: True, 32: True, 36: True, 49: True, 64: True, 3: False,\n"
            "         5: False, 7: False, 12: False, 50: False}\n"
            "for n, exp in known.items():\n"
            "    assert ref(n) == exp, 'perfect_power classification wrong n=%d' % n\n"
            "checked = 0\n"
            "for n in boundary:\n"
            "    ref(n); checked += 1\n"
            "for _ in range(20000):\n"
            "    n = rng.randint(1, 200); ref(n); checked += 1\n"
            "print('AX-REF perfect_power ok: bool(perfect_power) deterministic "
            "and matches documented classifications on %d magnitudes (6=False, "
            "8=True ... the F2P-pinned values)' % checked)\n"
            "sys.exit(0)\n"
        ),
        "rationale": "the A-reference deep dispatch is validated == "
                     "bool(perfect_power); a disagreement would be AXIOM-UNSOUND "
                     "(the model would branch on the wrong boolean for the "
                     "pow-true arm, mis-deciding the F2P sin(x)**6/True and "
                     "sin(x)**8/True outcomes).",
    },

    # --- is_perfect_power : caller-domain CONTAINMENT -----------------------
    # The model can reach is_perfect_power(exp.value) only when (control flow):
    # is_target, exp.real, value>=0 (order_lt_zero false), value<=max
    # (order_gt_max false), value!=1, value!=2, value!=4, and pow=True. So the
    # reachable magnitudes are {0,3,5,6,...,max} minus {1,2,4}. Every such n
    # must lie in is_perfect_power's Requires(n>=0) domain. CAUTION: in sympy
    # 1.5 perfect_power raises ValueError on 0; the dispatch never reaches it
    # with 0 (x**0 is not a Pow; smallest reachable magnitude is 3). We assert
    # both: containment in the axiom Requires (n>=0) AND that the REAL callee
    # does not raise on any ACTUALLY-reachable magnitude (n>=3).
    {
        "id": "ax-contain-perfect-power",
        "axiom": "is_perfect_power",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "from sympy import perfect_power\n"
            "# Enumerate EXACTLY the magnitudes the model can pass to\n"
            "# is_perfect_power, derived from the impl control flow:\n"
            "#   is_target & exp.real & not(value<0) & not(value>max) &\n"
            "#   value!=1 & value!=2 & value!=4 & pow  ==> value in [0,max]\\{1,2,4}\n"
            "# value 0 is unreachable in practice (x**0 is not a Pow), and the\n"
            "# smallest magnitude the dispatch consults is 3.\n"
            "violations = []\n"
            "raised = []\n"
            "for m in (4, 6, 10, 20, 30, 100):\n"
            "    reachable = [v for v in range(0, m + 1)\n"
            "                 if v not in (1, 2, 4)]\n"
            "    for v in reachable:\n"
            "        # (a) containment in the axiom Requires domain n>=0\n"
            "        if not (v >= 0):\n"
            "            violations.append((m, v))\n"
            "        # (b) the REAL callee must not raise on a value the dispatch\n"
            "        #     actually consults (v>=3); v==0 is not consulted.\n"
            "        if v >= 3:\n"
            "            try:\n"
            "                perfect_power(v)\n"
            "            except Exception as ex:\n"
            "                raised.append((v, type(ex).__name__))\n"
            "assert not violations, ('caller-reachable magnitude OUTSIDE axiom "
            "Requires(n>=0): %r => AXIOM-TOO-WEAK-FOR-CALLER' % violations[:5])\n"
            "assert not raised, ('real perfect_power RAISES on a reachable "
            "magnitude (v>=3): %r => domain misscoped' % raised[:5])\n"
            "print('AX-CONTAIN ok: every caller-reachable magnitude (value in "
            "[0,max] minus {1,2,4}, pow=True) lies in Requires(n>=0); real "
            "perfect_power does not raise on any consulted magnitude (v>=3). "
            "v==0 is in-domain but never reached (x**0 is not a Pow).')\n"
            "sys.exit(0)\n"
        ),
        "rationale": "containment, not whole-domain coverage: every magnitude "
                     "the dispatch can actually pass to is_perfect_power lies in "
                     "Requires(n>=0). The version-sensitive ValueError-on-0 of "
                     "sympy-1.5 is not a defect because 0 is never reached (x**0 "
                     "is not a Pow; smallest consulted magnitude is 3). A "
                     "reachable n outside the domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
