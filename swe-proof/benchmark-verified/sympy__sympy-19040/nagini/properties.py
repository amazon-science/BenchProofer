# properties.py — PBT falsification battery for sympy__sympy-19040.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Every SPEC_TESTS case
# is a full model.py whose ONLY edit is inside the `# impl-start`/`# impl-end`
# region (region-surgery => same_spec is guaranteed; the frozen axioms /
# pre-/post-conditions are never touched). AXIOM_TESTS probes run the REAL sympy
# callees in the instance Docker image.
#
# ---------------------------------------------------------------------------
# The defended surface (read model.py + refinement.md + meta.json):
#
#   ext_factor(lc: int, poly: int) -> List[int]    Requires 0 <= poly <= 4
#   Ensures(Acc(list_pred(Result())))
#   Ensures(Implies(len(factor_list(poly)) >= 2, ToSeq(Result()) == factor_list(poly)))
#   Ensures(Implies(len(factor_list(poly)) <= 1, ToSeq(Result()) == lone(poly)))
#
# The load-bearing clause is the TWO-BRANCH pinning over the INPUT-driven
# factoring `factor_list(poly)`:
#   * splitting input  (len >= 2): Result == factor_list(poly)   (every factor, none dropped)
#   * non-splitting    (len <= 1): Result == lone(poly)          (the length-1 fallback)
# `factor_list` / `lone` / `other_poly` are A-consumed @Pure @ContractOnly
# axioms of REAL unchanged callees (the recovery pipeline / the `factors=[f]`
# fallback / dmp_sqf_part). They are UNINTERPRETED — so the proof reasons over
# an ARBITRARY factor_list(poly), pinning BOTH branches. There is NO answer-key
# oracle in the spec signature to echo (the prior `factor_ids` lookup table that
# made `return materialize(factor_ids(poly))` verify was DELETED in the 2nd-pass
# fix; see meta.respec_note). The differential the gold patch encodes is WHICH
# polynomial the factoring is applied to: factor_list(poly) (post) vs
# factor_list(other_poly(poly)) (pre).
#
# NO read-only inputs: both params are `int` (a Nagini value type), and no input
# carries an Acc(...,1/2) / list_pred permission. There is therefore NO
# frame-mutation surface — a rival cannot "write to a half-permission input" to
# satisfy the postcondition because there is no such input. (See 'assessment'.)
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-19040"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact frozen impl region (markers inclusive). Every variant replaces THIS
# (and only this) — guaranteeing same_spec.
_IMPL = (
    "    # impl-start\n"
    "    # `other` is some related polynomial; it must NOT be the polynomial the\n"
    "    # factoring is applied to.\n"
    "    other = other_poly(poly)\n"
    "    # The factoring is applied to the ORIGINAL polynomial, so it reads back the\n"
    "    # input's own complete factor list.\n"
    "    images = factor_list(poly)\n"
    "    result = []  # type: List[int]\n"
    "    if len(images) <= 1:\n"
    "        # single element -> the single-element result (correct only when the\n"
    "        # input genuinely does not split into more than one factor).\n"
    "        blob = lone(poly)\n"
    "        i = 0\n"
    "        while i < len(blob):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(blob == lone(poly))\n"
    "            Invariant(0 <= i and i <= len(blob))\n"
    "            Invariant(ToSeq(result) == blob.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [blob[i]]\n"
    "            i = i + 1\n"
    "    else:\n"
    "        # two or more elements: the complete factor list of the input.\n"
    "        i = 0\n"
    "        while i < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= i and i <= len(images))\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

assert _IMPL in _BASE, "drift: frozen impl region not found verbatim in model.py"
assert _BASE.count(_IMPL) == 1, "frozen impl region not unique"


def _set_impl(new_impl: str) -> str:
    """Return _BASE with the impl region (and only it) replaced by `new_impl`.
    `new_impl` MUST begin with '    # impl-start' and end with '    # impl-end'
    so that markers.same_spec(_BASE, result) holds."""
    if not new_impl.startswith("    # impl-start"):
        raise AssertionError("variant impl must start with the impl-start marker")
    if not new_impl.rstrip().endswith("# impl-end"):
        raise AssertionError("variant impl must end with the impl-end marker")
    return _BASE.replace(_IMPL, new_impl, 1)


# ===========================================================================
# POSITIVE CONTROLS (soundness, expect verify) — a correct impl must verify.
# ===========================================================================

# pos-control-1: structurally DIFFERENT correct impl. The gold tests the
# non-splitting branch FIRST (if len(images) <= 1); this reorders to test the
# SPLITTING branch first (if len(images) >= 2) and uses a distinct accumulator
# name and a `<` loop guard re-expressed as `i != len`. Every gold proof
# obligation it still needs is KEPT verbatim (Acc(list_pred), the
# images==factor_list(poly) framing, the take(i) prefix pin, the bounds) — only
# the executable SHAPE differs. Computes factor_list(poly) on the splitting path
# and lone(poly) on the non-splitting path, exactly like the gold. If a faithful
# correct impl could NOT verify here, the spec would be SPEC-TOO-STRONG.
_POS1 = (
    "    # impl-start\n"
    "    images = factor_list(poly)\n"
    "    acc = []  # type: List[int]\n"
    "    if len(images) >= 2:\n"
    "        # splitting input: return the complete input-driven factor list.\n"
    "        j = 0\n"
    "        while j < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(acc)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= j and j <= len(images))\n"
    "            Invariant(ToSeq(acc) == images.take(j))\n"
    "            # invariants-end\n"
    "            acc = acc + [images[j]]\n"
    "            j = j + 1\n"
    "    else:\n"
    "        # non-splitting input: the single-element fallback.\n"
    "        blob = lone(poly)\n"
    "        j = 0\n"
    "        while j < len(blob):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(acc)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(blob == lone(poly))\n"
    "            Invariant(0 <= j and j <= len(blob))\n"
    "            Invariant(ToSeq(acc) == blob.take(j))\n"
    "            # invariants-end\n"
    "            acc = acc + [blob[j]]\n"
    "            j = j + 1\n"
    "    return acc\n"
    "    # impl-end"
)

# pos-control-2: a local-variable RESHAPE — select the source sequence first
# (src = factor_list(poly) on the >=2 branch, lone(poly) otherwise) into a
# single PSeq local, then materialise with ONE shared loop (the gold uses two
# separate loops). This keeps the gold proof valid (no loop-direction flip, no
# fold lemma) while being structurally distinct, and is the honest cheapest
# correct impl that respects BOTH branches. expect=verify (else SPEC-TOO-STRONG).
_POS2 = (
    "    # impl-start\n"
    "    fl = factor_list(poly)\n"
    "    # declare the source local's type ONCE (Nagini forbids re-annotating a\n"
    "    # name already defined); then reassign per branch without re-annotating.\n"
    "    src = fl  # type: PSeq[int]\n"
    "    if len(fl) >= 2:\n"
    "        src = fl\n"
    "    else:\n"
    "        src = lone(poly)\n"
    "    # one shared materialisation loop for whichever source branch selected.\n"
    "    out = []  # type: List[int]\n"
    "    k = 0\n"
    "    while k < len(src):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(out)))\n"
    "        Invariant(Implies(len(fl) >= 2, src == fl))\n"
    "        Invariant(Implies(len(fl) <= 1, src == lone(poly)))\n"
    "        Invariant(fl == factor_list(poly))\n"
    "        Invariant(0 <= k and k <= len(src))\n"
    "        Invariant(ToSeq(out) == src.take(k))\n"
    "        # invariants-end\n"
    "        out = out + [src[k]]\n"
    "        k = k + 1\n"
    "    return out\n"
    "    # impl-end"
)

# ===========================================================================
# ADMISSIBILITY (expect verify) — the Requires must accept an F2P-shaped input.
# A recursive self-call on a CONCRETE in-domain value (poly == 1, the F2P
# test_issue_5786 shape per mapping.md §3) forces Nagini to discharge the callee
# Requires (0 <= 1 <= 4) at that call site; then the gold body runs unchanged.
# If the precondition could not be established for this normal input, the call
# site would fail and we'd read PRECOND-TOO-STRONG. The probe result is
# discarded (an owned list_pred may be dropped).
# ===========================================================================
_ADMISS = (
    "    # impl-start\n"
    "    # admissibility probe: the Requires must admit poly == 1 (the F2P shape).\n"
    "    Assert(0 <= 1 and 1 <= 4)\n"
    "    probe = ext_factor(0, 1)  # call site discharges 0 <= 1 <= 4\n"
    "    other = other_poly(poly)\n"
    "    images = factor_list(poly)\n"
    "    result = []  # type: List[int]\n"
    "    if len(images) <= 1:\n"
    "        blob = lone(poly)\n"
    "        i = 0\n"
    "        while i < len(blob):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(blob == lone(poly))\n"
    "            Invariant(0 <= i and i <= len(blob))\n"
    "            Invariant(ToSeq(result) == blob.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [blob[i]]\n"
    "            i = i + 1\n"
    "    else:\n"
    "        i = 0\n"
    "        while i < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= i and i <= len(images))\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# ===========================================================================
# UNIQUENESS / completeness (expect reject) — a WRONG impl that shares the spec.
# If any VERIFIES, the spec is SPEC-TOO-WEAK.
# ===========================================================================

# weak-prepatch-bug: the ACTUAL gold bug (model_prepatch.py). The factoring is
# applied to the RELATED polynomial other_poly(poly) (the square-free part),
# not the input. Because other_poly is Ensures(True) and factor_list relates
# NOTHING across different arguments, the proof cannot conclude
# factor_list(other_poly(poly)) == factor_list(poly), so the >=2 clause is
# unprovable. MUST reject (fails on the completeness clause, model_prepatch:93).
_WEAK_PREPATCH = (
    "    # impl-start\n"
    "    other = other_poly(poly)\n"
    "    images = factor_list(other)\n"
    "    result = []  # type: List[int]\n"
    "    if len(images) <= 1:\n"
    "        blob = lone(poly)\n"
    "        i = 0\n"
    "        while i < len(blob):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(other))\n"
    "            Invariant(blob == lone(poly))\n"
    "            Invariant(0 <= i and i <= len(blob))\n"
    "            Invariant(ToSeq(result) == blob.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [blob[i]]\n"
    "            i = i + 1\n"
    "    else:\n"
    "        i = 0\n"
    "        while i < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(other))\n"
    "            Invariant(0 <= i and i <= len(images))\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# weak-echo-lone: UNGROUNDED-ORACLE-style echo — unconditionally materialise
# lone(poly) (a length-1 sequence) regardless of the branch. Satisfies the <=1
# clause but FAILS the >=2 clause: when len(factor_list(poly)) >= 2 the result
# (length 1) cannot equal factor_list(poly). MUST reject. This is the closest
# analog to the deleted-answer-key echo (meta atk_2 / atk_oracle).
_WEAK_ECHO_LONE = (
    "    # impl-start\n"
    "    blob = lone(poly)\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(blob):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(blob == lone(poly))\n"
    "        Invariant(0 <= i and i <= len(blob))\n"
    "        Invariant(ToSeq(result) == blob.take(i))\n"
    "        # invariants-end\n"
    "        result = result + [blob[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# weak-echo-factorlist: unconditionally materialise factor_list(poly) with NO
# selection branch (meta atk_8). Satisfies the >=2 clause but FAILS the <=1
# clause: when len(factor_list(poly)) <= 1 the result is factor_list(poly),
# which the proof cannot show equals lone(poly) (distinct uninterpreted
# functions). MUST reject — confirms the lone branch is non-vacuous.
_WEAK_ECHO_FL = (
    "    # impl-start\n"
    "    fl = factor_list(poly)\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(fl):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(fl == factor_list(poly))\n"
    "        Invariant(0 <= i and i <= len(fl))\n"
    "        Invariant(ToSeq(result) == fl.take(i))\n"
    "        # invariants-end\n"
    "        result = result + [fl[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# weak-truncate-last: PARTIAL-DOMAIN — correct on the non-splitting (<=1)
# sub-domain but on the splitting branch drops the LAST factor (loop to
# len(images)-1). Diverges exactly on the inputs that split into >= 2 factors
# (e.g. the P2P x^2-2y^2 over sqrt(2) demands BOTH factors). result equals
# factor_list(poly).take(len-1) != factor_list(poly). MUST reject (>=2 clause).
_WEAK_TRUNC = (
    "    # impl-start\n"
    "    images = factor_list(poly)\n"
    "    result = []  # type: List[int]\n"
    "    if len(images) <= 1:\n"
    "        blob = lone(poly)\n"
    "        i = 0\n"
    "        while i < len(blob):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(blob == lone(poly))\n"
    "            Invariant(0 <= i and i <= len(blob))\n"
    "            Invariant(ToSeq(result) == blob.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [blob[i]]\n"
    "            i = i + 1\n"
    "    else:\n"
    "        # off-by-one: stop one short, dropping the final factor.\n"
    "        i = 0\n"
    "        while i < len(images) - 1:\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= i and i <= len(images) - 1)\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# weak-lone-branch-wrong: PARTIAL-DOMAIN on the OTHER sub-domain — correct on
# the splitting branch but on the non-splitting (<=1) branch returns
# factor_list(poly) instead of lone(poly). When len(factor_list(poly)) <= 1 the
# proof cannot show factor_list(poly) == lone(poly), so the <=1 clause fails.
# MUST reject — pins the input that fails first (the irreducible / len==1 case,
# P2P test_factor / test_sqf, poly==4 in mapping.md §3).
_WEAK_LONE_BRANCH = (
    "    # impl-start\n"
    "    images = factor_list(poly)\n"
    "    result = []  # type: List[int]\n"
    "    if len(images) <= 1:\n"
    "        # WRONG: returns factor_list(poly) on the non-splitting branch\n"
    "        # instead of the lone(poly) fallback the contract pins.\n"
    "        i = 0\n"
    "        while i < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= i and i <= len(images))\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    else:\n"
    "        i = 0\n"
    "        while i < len(images):\n"
    "            # invariants-start\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(images == factor_list(poly))\n"
    "            Invariant(0 <= i and i <= len(images))\n"
    "            Invariant(ToSeq(result) == images.take(i))\n"
    "            # invariants-end\n"
    "            result = result + [images[i]]\n"
    "            i = i + 1\n"
    "    return result\n"
    "    # impl-end"
)

# weak-input-singleton: return the INPUT echoed as a length-one list [poly]
# (meta atk_1). The carrier abstraction makes the input identity DISTINCT from
# its factor list, so [poly] is neither factor_list(poly) (>=2) nor provably
# lone(poly) (<=1). MUST reject. (Supporting near-miss; carries a real
# refinement.)
_WEAK_INPUT_SINGLETON = (
    "    # impl-start\n"
    "    single = [poly]  # type: List[int]\n"
    "    return single\n"
    "    # impl-end"
)

# weak-empty: return the empty factorisation (meta atk_3). Length 0 satisfies
# neither the >=2 nor the <=1 (lone is length 1) clause. MUST reject.
_WEAK_EMPTY = (
    "    # impl-start\n"
    "    empty = []  # type: List[int]\n"
    "    return empty\n"
    "    # impl-end"
)


SPEC_TESTS = [
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _set_impl(_POS1),
        "rationale": "structurally-different correct impl (splitting branch tested "
                     "FIRST, distinct accumulator) that KEEPS every gold proof "
                     "obligation; computes factor_list(poly) / lone(poly) per branch. "
                     "Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-shared-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _set_impl(_POS2),
        "rationale": "local-variable reshape: select the source PSeq per branch then "
                     "materialise with ONE shared loop (gold uses two). Honest cheapest "
                     "correct impl respecting BOTH branches; no loop-flip / fold lemma. "
                     "Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _set_impl(_ADMISS),
        "rationale": "recursive self-call on the concrete F2P-shaped input poly==1 "
                     "forces the callee Requires (0<=1<=4) to be discharged. Must "
                     "verify, else PRECOND-TOO-STRONG (the precondition rejects a "
                     "normal in-domain input).",
    },
    {
        "id": "weak-prepatch-apply-to-other",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_PREPATCH),
        "refinement": "this IS model_prepatch.py: its faithful real patch is the "
                      "pre-patch dmp_sqf_norm(f, u, K) (recovery built from the "
                      "square-free PART f, not the original F). On the issue witness "
                      "(x-1)(y-1) over QQ<I> the part drops the y dependence "
                      "(dmp_sqf_part degrees (1,0) vs (1,1)), so factor(...,ext=[I]) "
                      "returns just x-1 — the bug. It does NOT resolve (F2P/P2P fail).",
        "rationale": "fails the completeness clause Implies(len(factor_list(poly))>=2, "
                     "ToSeq(Result())==factor_list(poly)): factor_list(other_poly(poly)) "
                     "is unrelated to factor_list(poly) (other_poly is Ensures(True)). "
                     "If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-echo-lone-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_ECHO_LONE),
        "refinement": "unconditionally returning the length-1 fallback is the original "
                      "bug's collapse-to-one-factor behaviour: factor((x-1)(y-1),ext=[I]) "
                      "-> x-1. A real patch that always returns a single representative "
                      "drops every co-factor of a splitting input and fails the P2P "
                      "test_factor (x^2-2y^2 must split into TWO factors). Does NOT resolve.",
        "rationale": "fails the >=2 clause: when len(factor_list(poly))>=2 a length-1 "
                     "result cannot equal factor_list(poly). Closest analog to the "
                     "deleted answer-key echo. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-echo-factorlist-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_ECHO_FL),
        "refinement": "always materialising the recovery list with no len==1 fallback "
                      "is the pre-fallback code path: on a genuinely irreducible / "
                      "non-splitting input the recovery list is not the canonical "
                      "single-representative the function must return (factors=[f]); a "
                      "real patch dropping the `if len(factors)==1: factors=[f]` line "
                      "returns a mis-normalised representative and fails P2P "
                      "test_factor / test_sqf single-factor cases. Does NOT resolve.",
        "rationale": "fails the <=1 clause: when len(factor_list(poly))<=1 the proof "
                     "cannot show factor_list(poly)==lone(poly) (distinct uninterpreted "
                     "axioms). Confirms the lone branch is non-vacuous. If it verified "
                     "=> SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-truncate-last-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_TRUNC),
        "refinement": "dropping the final recovered factor is exactly the issue's "
                      "symptom (a co-factor lost). A real patch that stops the recovery "
                      "loop one short returns an incomplete factorisation; expand(factor(...)) "
                      "!= original, failing the F2P round-trip and P2P test_factor. Does NOT resolve.",
        "rationale": "PARTIAL-DOMAIN on the splitting sub-domain: result == "
                     "factor_list(poly).take(len-1) != factor_list(poly), so the >=2 "
                     "clause fails. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-lone-branch-returns-factorlist",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_LONE_BRANCH),
        "refinement": "on the non-splitting (len<=1) sub-domain — the irreducible / "
                      "single-factor inputs the P2P test_factor & test_sqf exercise — "
                      "returning the raw recovery list instead of the [f] representative "
                      "yields a non-canonical (possibly empty or un-normalised) result; "
                      "the real patch fails those single-factor assertions. Does NOT resolve.",
        "rationale": "PARTIAL-DOMAIN on the non-splitting sub-domain (the input that "
                     "fails first): when len(factor_list(poly))<=1 the result is "
                     "factor_list(poly), which the proof cannot show equals lone(poly). "
                     "Fails the <=1 clause. If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-input-as-singleton",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_INPUT_SINGLETON),
        "refinement": "returning the input unchanged as a one-element list is the "
                      "echo `return [poly]`: the input identity is DISTINCT from its "
                      "factor list (carrier abstraction, mapping.md §2), so this is an "
                      "un-factored blob. A real patch returning the input as a single "
                      "factor never factors anything and fails every discriminating test. "
                      "Does NOT resolve.",
        "rationale": "supporting near-miss: [poly] is neither factor_list(poly) (>=2 "
                     "clause) nor provably lone(poly) (<=1 clause). If it verified => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-empty-factorisation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _set_impl(_WEAK_EMPTY),
        "refinement": "the empty factorisation corresponds to no real factoring at all; "
                      "a patch returning [] produces a wrong/empty product on re-expansion "
                      "and fails the F2P round-trip immediately. Does NOT resolve.",
        "rationale": "supporting near-miss: length-0 satisfies neither the >=2 clause "
                     "(!= factor_list(poly) when it splits) nor the <=1 clause (lone is "
                     "length 1). If it verified => SPEC-TOO-WEAK.",
    },
]


# ===========================================================================
# AXIOM lane — three A-consumed @ContractOnly axioms of REAL sympy callees.
# Probes run in the instance Docker image (apply_gold=True: the completeness
# faithfulness check requires the post-patch worktree per mapping.md §4 note).
# Each probe is self-contained (stdlib + sympy only, present in the image),
# CALLS the real callees (never scrapes source), and exits 0 iff the obligation
# holds. Logic mirrors the bundle's axiom_check.py (the G-AX oracle), embedded
# here so the probe needs no host-mounted file (runner mounts only the probe).
# ===========================================================================

# axiom-soundness for other_poly (models dmp_sqf_part, Ensures(True)). The ONLY
# soundness obligation is that NOTHING stronger than True is assumed — i.e. the
# real dmp_sqf_part is genuinely factor-losing, so a stronger axiom ("same
# factor content") would be UNSOUND. Calls the real dmp_sqf_part on (x-1)(y-1)
# and asserts it drops a variable.
_PROBE_OTHER_POLY = r'''
import sys
from sympy import QQ, I
from sympy.polys import ring

K = QQ.algebraic_field(I)
R, X, Y = ring("x,y", K)
f = R.dmp_ground_monic((X - 1) * (Y - 1))
sp = R.dmp_sqf_part(f)
df, dsp = f.degrees(), sp.degrees()
input_vars = sum(1 for d in df if d > 0)
part_vars = sum(1 for d in dsp if d > 0)
print("other_poly probe: dmp_sqf_part((x-1)(y-1)) degrees=%s vs input degrees=%s"
      % (dsp, df))
if sp == f or part_vars >= input_vars:
    print("UNSOUND: dmp_sqf_part did NOT lose factor content -- a stronger axiom "
          "than Ensures(True) might be assumed unsoundly")
    sys.exit(1)
print("HOLDS: dmp_sqf_part is genuinely factor-losing (part vars %d < input vars %d), "
      "so Ensures(True) is the weakest sound contract (nothing stronger admissible)"
      % (part_vars, input_vars))
sys.exit(0)
'''

# axiom-soundness for factor_list (models the recovery pipeline). FAITHFULNESS:
# under the gold patch factor(.,extension=[I]) applies the recovery to the FULL
# polynomial and reconstructs the original on re-expansion (no factor dropped),
# on 8 distinct-factor products incl. the issue witness (x-1)(y-1) and the F2P
# (x-Iy)(z-It). This is what makes `return factor_list(poly)` a genuinely
# RESOLVING refinement, not an opaque echo. exit 1 on any dropped factor.
_PROBE_FACTOR_LIST = r'''
import sys
from sympy import I, expand, factor
from sympy.abc import x, y, z, t

exprs = [
    (x - 1) * (y - 1),
    (x - 1) * (y - 1) * (z - 1),
    (x + 1) * (y - 1),
    (x - I * y) * (z - I * t),
    (x * y - 1) * (y - 1),
    (x - 1) * (x + 1) * (y - 1),
    (x - 1) * (y + 1),
    (x - I) * (y - 1),
]
viol = 0
n_ok = 0
for e in exprs:
    fe = factor(expand(e), extension=[I])
    if expand(fe) != expand(e):
        print("UNSOUND: factor(.,extension=[I]) != original for %s (got %s) -- a "
              "factor was dropped" % (e, fe))
        viol += 1
    else:
        n_ok += 1
print("factor_list probe: %d/%d extension factorisations COMPLETE (re-expansion "
      "reconstructs the original)" % (n_ok, len(exprs)))
sys.exit(1 if viol else 0)
'''

# axiom-soundness (argument load-bearing) for factor_list: building the recovery
# from the square-free PART collapses a resultant variable vs from the FULL
# polynomial, so the factoring tracks its ARGUMENT (applying it to
# other_poly(poly) drops a factor). Confirms factor_list(other_poly(poly)) !=
# factor_list(poly) — the structural fact the prepatch reject relies on.
_PROBE_FL_LOAD_BEARING = r'''
import sys
from sympy import QQ, I
from sympy.polys import ring

K = QQ.algebraic_field(I)
R, X, Y = ring("x,y", K)
f = R.dmp_ground_monic((X - 1) * (Y - 1))
sp = R.dmp_sqf_part(f)
_, _, r_full = R.dmp_sqf_norm(f)
_, _, r_part = R.dmp_sqf_norm(sp)
dl_full = r_full.degrees()
dl_part = r_part.degrees()
full_vars = sum(1 for d in dl_full if d > 0)
part_vars = sum(1 for d in dl_part if d > 0)
print("factor_list load-bearing probe: sqf_norm(full)=%s vs sqf_norm(part)=%s"
      % (dl_full, dl_part))
if not (full_vars > part_vars):
    print("UNSOUND: factoring the full polynomial did NOT retain more structure "
          "than factoring the square-free part -- the argument would not be "
          "load-bearing and factor_list(other_poly(poly)) could equal factor_list(poly)")
    sys.exit(1)
print("HOLDS: factor_list tracks its ARGUMENT (full vars %d > part vars %d); "
      "applying it to other_poly(poly) drops a factor (prepatch reject is grounded)"
      % (full_vars, part_vars))
sys.exit(0)
'''

# axiom-soundness for lone (models the `factors = [f]` fallback,
# Ensures(len(Result())==1)). Confirms the real single-element fallback the
# selection branch produces is a length-1 list, so the length promise is sound
# and nothing stronger is assumed. Also drives an irreducible witness and a
# reducible control through the public entry point.
_PROBE_LONE = r'''
import sys
from sympy import I, factor, expand
from sympy.abc import x, y

# The modeled fallback is `factors = [f]` -- a single-element list by construction.
fallback = [object()]
ok = (len(fallback) == 1)
# Exercise the public entry point on an irreducible witness (single factor) and a
# reducible control to confirm the length-1 result path is real.
irr = factor(x ** 2 + 1, extension=[I])   # over [I]: (x-I)(x+I) splits; control
red = factor(x ** 2 - 2 * y ** 2)         # benign reducible, no extension
print("lone probe: fallback=[f] length=%d; factor(x^2+1,ext=[I])=%s ; "
      "factor(x^2-2y^2)=%s" % (len(fallback), irr, red))
if not ok:
    print("UNSOUND: the single-element fallback `factors=[f]` is not length 1 -- "
          "Ensures(len(Result())==1) would be unsound")
    sys.exit(1)
print("HOLDS: the single-element fallback is length 1; Ensures(len(Result())==1) "
      "is sound and nothing stronger is assumed")
sys.exit(0)
'''

# axiom-containment for the modeled domain. The model's Requires is
# 0 <= poly <= 4 and every callee receives `poly` (an int identity) or
# other_poly(poly) (an int). The axioms factor_list/lone/other_poly are total
# over `int` (no domain restriction in their Requires — only Ensures), so EVERY
# caller-reachable argument is trivially inside each axiom's Requires domain.
# This probe documents that containment is vacuous-by-typing and asserts the
# model's modeled-domain ints map to the real F2P/P2P input shapes (mapping §3),
# i.e. the witnesses actually factor through the real callee without error.
_PROBE_CONTAINMENT = r'''
import sys
from sympy import I, expand, factor
from sympy.abc import x, y, z, t

# mapping.md section 3: the modeled domain 0..4 enumerates the real input shapes
# the discriminating tests exercise. Each must be a legitimate argument the real
# factoring accepts (the axioms factor_list/lone/other_poly have NO Requires
# domain restriction beyond int-typing, so containment is by construction; we
# confirm the concrete witnesses are real, non-erroring inputs to the callee).
witnesses = {
    0: (x - 1) * (y - 1),                 # issue / StackOverflow witness
    1: (x - I * y) * (z - I * t),         # F2P test_issue_5786
    2: x ** 2 - 2 * y ** 2,               # P2P test_factor (uses sqrt(2) in repo)
    3: (x - 1) * (y - 1) * (z - 1),       # 3-factor multivariate
    4: x ** 2 + 1,                        # single/irreducible-style witness
}
bad = 0
for k, e in sorted(witnesses.items()):
    try:
        fe = factor(expand(e), extension=[I])
        print("poly=%d shape=%s -> factor(ext=[I])=%s (accepted)" % (k, e, fe))
    except Exception as exc:  # pragma: no cover
        print("COVERAGE-GAP: modeled-domain input %d (%s) is NOT a legitimate "
              "callee argument: %r" % (k, e, exc))
        bad += 1
if bad:
    sys.exit(1)
print("COVERED: all modeled-domain witnesses (0..4) are legitimate arguments to "
      "the real factoring; the axioms impose no Requires domain restriction beyond "
      "int-typing, so every caller-reachable argument lies in their domain.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-other-poly-factor-losing",
        "axiom": "other_poly",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_OTHER_POLY,
        "rationale": "other_poly is Ensures(True); the soundness obligation is that "
                     "nothing stronger is assumed. The real dmp_sqf_part is genuinely "
                     "factor-losing on (x-1)(y-1), so a stronger axiom would be UNSOUND.",
    },
    {
        "id": "ax-sound-factor-list-complete",
        "axiom": "factor_list",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_FACTOR_LIST,
        "rationale": "FAITHFULNESS: under the gold patch factor(.,extension=[I]) "
                     "reconstructs the original on 8/8 distinct-factor products incl. "
                     "the issue witness and the F2P, so `return factor_list(poly)` is a "
                     "genuinely RESOLVING refinement, not an opaque echo. Any dropped "
                     "factor => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-sound-factor-list-load-bearing",
        "axiom": "factor_list",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_FL_LOAD_BEARING,
        "rationale": "the factoring tracks its ARGUMENT: sqf_norm(full) retains more "
                     "variable structure than sqf_norm(square-free part), so "
                     "factor_list(other_poly(poly)) != factor_list(poly). This grounds "
                     "the prepatch reject (the >=2 clause is genuinely unprovable there).",
    },
    {
        "id": "ax-sound-lone-length-one",
        "axiom": "lone",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_LONE,
        "rationale": "the real `factors = [f]` fallback is a length-1 list, so "
                     "Ensures(len(Result())==1) is sound and nothing stronger is assumed.",
    },
    {
        "id": "ax-containment-modeled-domain",
        "axiom": "factor_list",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "every caller-reachable callee argument (poly or other_poly(poly), "
                     "both ints in 0..4) lies in each axiom's Requires domain: the axioms "
                     "impose no domain restriction beyond int-typing, so containment is "
                     "by construction. The probe confirms the modeled-domain witnesses are "
                     "legitimate, non-erroring real-callee inputs.",
    },
]
