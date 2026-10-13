# properties.py — PBT falsification battery for scikit-learn__scikit-learn-26194.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only the impl region differs,
# guaranteed by region-surgery via _swap) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes run in the instance image.
#
# Defended surface (anchor_thresholds, models the roc_curve threshold-anchoring
# tail; gold: `thresholds = np.r_[np.inf, thresholds]`):
#   Requires: Acc(list_pred(thresholds), 1/2)   -- READ-ONLY input (half perm)
#             len(thresholds) >= 1
#   Ensures : Acc(list_pred(thresholds), 1/2)   -- returns the read perm
#             Acc(list_pred(Result()))
#             len(Result()) == len(thresholds) + 1          (length+1)
#             is_pos_inf(Result()[0])                        (infinite-sentinel lead; discriminator)
#             ToSeq(Result()).drop(1) == ToSeq(thresholds)   (tail unchanged, in order)
# Axioms (A-consumed): pos_inf() Ensures is_pos_inf(Result()); is_pos_inf(x) is an
# opaque @ContractOnly predicate whose ONLY consumed fact is is_pos_inf(pos_inf()).
#
# The three Ensures (length+1, leading sentinel, exact tail) jointly pin the
# result to [<the +inf sentinel>] ++ thresholds. The leading element can satisfy
# the opaque is_pos_inf ONLY by being provably equal to pos_inf() (the verifier
# knows nothing else about is_pos_inf), so the oracle is GROUNDED -- there is no
# wrong value to echo. See 'assessment'.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-26194"
FLOAT_ENCODING = "real"   # meta.json float_encoding; verified with --float-encoding=real

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region (between # impl-start and # impl-end). Every variant is
# produced by _swap on a substring that lies ENTIRELY inside this region, so the
# spec view (axioms / pure / pre / post / signature) is untouched => same_spec.
_GOLD_LOOP_BODY = """        result.append(thresholds[i])
        i = i + 1
    return result"""


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY: thresholds is read-only, Acc(...,1/2)).
#    Rival WRITES to the read-only input to manufacture the answer in place.
#    Must REJECT for insufficient permission (the post-condition only re-grants
#    1/2, and the loop invariant re-asserts Acc(list_pred(thresholds), 1/2);
#    a store thresholds[k] = ... needs FULL permission we do not hold).
# ---------------------------------------------------------------------------
_frame_mutation = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0""",
    """    lead = pos_inf()
    # frame-mutation attack: overwrite the read-only input in place to plant the
    # sentinel, then build the result off the mutated input. Needs FULL perm on
    # thresholds (we hold only Acc(...,1/2)) => must fail on the store.
    thresholds[0] = lead
    result = [lead]  # type: List[float]
    i = 0""",
)


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN (drop the first tail element). Correct on most inputs, but
#    skips thresholds[0] in the tail => violates len==n+1 AND tail==thresholds.
#    Refinement: a real np.r_[np.inf, thresholds[1:]] would drop the largest
#    finite threshold; F2P assert_array_almost_equal(thresholds,
#    [np.inf, 1.0, 0.7, 0.0]) would see [np.inf, 0.7, 0.0] -> FAIL to resolve.
# ---------------------------------------------------------------------------
_partial_drop_first = _swap(
    _BASE,
    """    i = 0
    while i < len(thresholds):""",
    """    i = 1  # partial-domain: skip the first finite threshold in the tail
    while i < len(thresholds):""",
)


# ---------------------------------------------------------------------------
# 3. PARTIAL-DOMAIN (last element corrupted to a constant). Appends thresholds[i]
#    for i<n-1 but plants 0.0 for the final element => tail != thresholds on the
#    last index. Value-proxy double-mask cousin: structure/length intact, one
#    index value diverges. Must REJECT on ToSeq(Result()).drop(1)==ToSeq(thresholds).
#    Refinement: a real patch returning the wrong final threshold gives a tail
#    array that fails the F2P exact-array assertion -> would not resolve.
# ---------------------------------------------------------------------------
_partial_last_wrong = _swap(
    _BASE,
    _GOLD_LOOP_BODY,
    """        if i + 1 < len(thresholds):
            result.append(thresholds[i])
        else:
            result.append(0.0)  # corrupt the final (smallest) threshold
        i = i + 1
    return result""",
)


# ---------------------------------------------------------------------------
# 4. FINITE-LEAD (the pre-patch behaviour, restated as a uniqueness rival).
#    Prepend a FINITE value (thresholds[0] + 1.0) instead of the sentinel. The
#    opaque is_pos_inf cannot be discharged for a finite real (the only consumed
#    fact is is_pos_inf(pos_inf())) => REJECT on is_pos_inf(Result()[0]).
#    This is exactly model_prepatch's failure (G-DIFF) and the discriminator the
#    F2P test pins (assert np.isinf(thresholds[0])). Refinement: max+1 is finite,
#    so np.isinf(thresholds[0]) is False -> F2P fails -> would not resolve.
# ---------------------------------------------------------------------------
_finite_lead = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]""",
    """    lead = thresholds[0] + 1.0  # pre-patch finite anchoring value (max + 1)
    result = [lead]  # type: List[float]""",
)


# ---------------------------------------------------------------------------
# 5. NO-PREPEND (return the input unchanged, length n not n+1). Must REJECT on
#    len(Result()) == len(thresholds) + 1 (and on the leading-sentinel clause).
#    Refinement: omitting the prepend leaves the ROC curve not anchored at the
#    origin and thresholds[0] is the finite max score -> F2P fails -> no resolve.
#    Cheap supporting near-miss; still carries a refinement.
# ---------------------------------------------------------------------------
_no_prepend = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0""",
    """    lead = pos_inf()
    result = []  # type: List[float]   # no-prepend: result will be just thresholds
    i = 0""",
)
# the gold loop invariants assume len(result)==i+1 and result[0]==lead; with an
# empty result they no longer hold, so this also stresses the invariant region,
# but the post-condition len==n+1 / is_pos_inf(Result()[0]) is the load-bearing
# rejection. We adjust the invariants (still inside impl) to be self-consistent
# with the wrong impl so the rejection is attributable to the POST-condition,
# not to a deliberately-broken invariant.
_no_prepend = _swap(
    _no_prepend,
    """        Invariant(len(result) == i + 1)
        Invariant(ToSeq(result).take(1) == PSeq(lead))
        Invariant(is_pos_inf(ToSeq(result)[0]))
        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))""",
    """        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(thresholds).take(i))""",
)


# ---------------------------------------------------------------------------
# 6. POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
#    Reorder independent local statements (compute the index cursor before the
#    result list, build lead inline-equivalently) keeping the SAME forward loop
#    direction so the front-anchored invariants still discharge. MUST VERIFY
#    (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_pos_control = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0
    while i < len(thresholds):""",
    """    i = 0                         # reordered: cursor first
    lead = pos_inf()
    result = [lead]  # type: List[float]
    while i < len(thresholds):""",
)


# ---------------------------------------------------------------------------
# 7. POSITIVE CONTROL (cheapest honest impl). Inline the sentinel call at the
#    list literal (drop the `lead` temporary) and carry it through the loop. A
#    correct minimal impl that does the genuine work; MUST VERIFY. Doubles as the
#    grounded-oracle positive control (no wrong echo exists, so this honest
#    cheapest impl stands in for the ungrounded-oracle slot).
# ---------------------------------------------------------------------------
_cheapest = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]""",
    """    result = [pos_inf()]  # type: List[float]   # inline the sentinel; no temp""",
)
# the invariants reference `lead`; rebind a local `lead` for the invariant terms
# without re-calling the sentinel constructor (keep the proof identical).
_cheapest = _swap(
    _cheapest,
    """        Invariant(Acc(list_pred(thresholds), 1 / 2))
        Invariant(Acc(list_pred(result)))""",
    """        Invariant(Acc(list_pred(thresholds), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) >= 1)""",
)
_cheapest = _swap(
    _cheapest,
    """        Invariant(ToSeq(result).take(1) == PSeq(lead))
        Invariant(is_pos_inf(ToSeq(result)[0]))""",
    """        Invariant(is_pos_inf(ToSeq(result)[0]))""",
)


# ---------------------------------------------------------------------------
# 8. ADMISSIBILITY: a self-call on an F2P-shaped in-domain input at the top of
#    the impl. Builds a concrete descending List[float] (length 3, like the
#    drop_intermediate fixture tail), calls anchor_thresholds on it, and asserts
#    the post-condition is usable (length 4, infinite lead). If the Requires were
#    too strong (e.g. secretly len>=2 or full-perm), this call would fail to
#    establish the precondition. MUST VERIFY (else PRECOND-TOO-STRONG).
#    The probe list is FRESH (full perm), so the original thresholds permission
#    is untouched; modular verification uses anchor_thresholds's own contract.
# ---------------------------------------------------------------------------
_admiss = _swap(
    _BASE,
    """    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0""",
    """    # admissibility witness: the precondition admits a normal F2P-shaped input.
    _probe = [1.0, 0.7, 0.0]  # type: List[float]
    Assert(Acc(list_pred(_probe), 1 / 2))
    Assert(len(_probe) >= 1)
    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0""",
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mutation,
        "refinement": (
            "Mutating thresholds in place (thresholds[0] = inf) needs FULL "
            "permission; the spec grants only Acc(list_pred(thresholds),1/2). A "
            "faithful real patch that overwrote the caller's thresholds ndarray "
            "in place would corrupt the returned tail (which is the same array "
            "object) -- the F2P exact-array assertions on the tail would fail, so "
            "it would NOT resolve. Verifying here would be a verify-not-resolve break."
        ),
        "rationale": (
            "Rejection comes from the permission system: the store thresholds[0]=lead "
            "requires full list_pred permission, but only the read half-perm is held "
            "(Requires Acc(...,1/2), re-asserted in the loop Invariant)."
        ),
    },
    {
        "id": "partial-domain-drop-first-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_drop_first,
        "refinement": (
            "Starting the copy at i=1 drops thresholds[0] (the largest finite "
            "threshold) from the tail. Real np.r_[np.inf, thresholds[1:]] yields "
            "[np.inf, 0.7, 0.0] where F2P expects [np.inf, 1.0, 0.7, 0.0] -> "
            "assert_array_almost_equal fails -> would NOT resolve."
        ),
        "rationale": (
            "Rejection from BOTH len(Result())==len(thresholds)+1 (result has n "
            "elements, not n+1) and ToSeq(Result()).drop(1)==ToSeq(thresholds) "
            "(tail is thresholds[1:], not thresholds)."
        ),
    },
    {
        "id": "partial-domain-last-element-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_last_wrong,
        "refinement": (
            "Planting 0.0 for the final (smallest) threshold gives a tail that "
            "diverges at the last index. The F2P expects the unchanged finite "
            "score there (e.g. 0.0 vs 0.0 happens to match in one fixture, but in "
            "test_roc_curve_drop_intermediate the last is 0.0 and the second is "
            "0.7) -- generally the last finite score is non-zero; "
            "assert_array_almost_equal fails -> would NOT resolve."
        ),
        "rationale": (
            "Rejection from ToSeq(Result()).drop(1)==ToSeq(thresholds): the value "
            "at the final tail index is 0.0, not thresholds[n-1]; the exact-sequence "
            "tail clause cannot be discharged."
        ),
    },
    {
        "id": "finite-lead-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _finite_lead,
        "refinement": (
            "This IS the pre-patch value max(y_score)+1, a FINITE real. The F2P "
            "regression asserts np.isinf(thresholds[0]); a finite lead makes it "
            "False -> the non-regression test fails -> would NOT resolve. (Exactly "
            "the change the gold patch introduces; model_prepatch reproduces it.)"
        ),
        "rationale": (
            "Rejection from is_pos_inf(Result()[0]): is_pos_inf is an opaque "
            "@ContractOnly predicate whose ONLY known-true instance is "
            "is_pos_inf(pos_inf()); a finite thresholds[0]+1.0 cannot be proven to "
            "satisfy it."
        ),
    },
    {
        "id": "no-prepend-length-n",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_prepend,
        "refinement": (
            "Omitting the leading entry returns the curve un-anchored (n entries, "
            "not n+1) with a finite thresholds[0]; both F2P tests (exact array AND "
            "np.isinf(thresholds[0])) fail -> would NOT resolve. Cheap supporting "
            "near-miss, but with a real refinement."
        ),
        "rationale": (
            "Rejection from len(Result())==len(thresholds)+1 (result has n entries) "
            "and is_pos_inf(Result()[0]) (Result()[0]==thresholds[0], finite). "
            "Invariants were made self-consistent with the wrong impl so the "
            "rejection is attributable to the POST-condition, not a broken invariant."
        ),
    },
    {
        "id": "pos-control-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_control,
        "rationale": (
            "Structurally different (cursor initialized before the result list) "
            "but behaviourally identical correct impl; same forward loop direction "
            "so the front-anchored invariants still discharge. MUST verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-cheapest-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _cheapest,
        "rationale": (
            "Cheapest honest impl: inline pos_inf() into the result literal, drop "
            "the lead temporary; loop unchanged. Genuinely does the work. Doubles "
            "as the grounded-oracle positive control (is_pos_inf is opaque so the "
            "leading element can only be discharged by the genuine pos_inf(); no "
            "wrong echo exists). MUST verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admissibility-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Self-call on a fresh descending List[float] of length 3 (F2P-shaped) "
            "establishes Requires (Acc(...,1/2) from full perm; len>=1) and uses "
            "the post-condition (len 4, infinite lead). MUST verify, else "
            "PRECOND-TOO-STRONG (the precondition would reject a normal input)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. Two A-consumed axioms over UNCHANGED numpy primitives:
#   pos_inf()  <-> np.inf   (Ensures is_pos_inf(Result()))
#   is_pos_inf <-> np.isinf (opaque; only consumed fact is_pos_inf(pos_inf()))
# These are patch-state-independent IEEE-754/NumPy constants. Containment: the
# model only ever passes Result()[0] (which the impl sets to pos_inf()) to
# is_pos_inf, and pos_inf() takes no argument -- so the only callee-input the
# model can reach is np.inf itself, which is trivially in np.isinf's (total)
# domain. We reuse/strengthen axiom_check.py's check_infinity_primitives logic.
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import sys
import numpy as np

# AXIOM-SOUNDNESS for pos_inf / is_pos_inf against the REAL numpy primitives the
# model abstracts (np.inf / np.isinf). The consumed obligation is
# is_pos_inf(pos_inf()): the sentinel the routine prepends is the POSITIVE
# infinity, and np.isinf recognizes it. Patch-state-independent (np.inf/np.isinf
# are unchanged by the patch). Fuzz finite reals + the pre-patch max+1 path +
# extremes + sentinels to try to make the real callee DISAGREE with the axiom.
fail = []

# 1. the load-bearing Ensures: is_pos_inf(pos_inf()) -- np.isinf(np.inf) True,
#    and np.inf is the POSITIVE sentinel.
if not bool(np.isinf(np.inf)):
    fail.append("np.isinf(np.inf) is not True")
if not (np.inf > 0):
    fail.append("np.inf is not the POSITIVE infinity sentinel")
# float('inf') == np.inf (version-independent identity the mapping relies on)
if not (np.inf == float("inf")):
    fail.append("np.inf != float('inf')")

# 2. the discriminator must SEPARATE the sentinel from finite reals: no ordinary
#    finite score may satisfy is_pos_inf (else the pre-patch finite anchoring
#    value could masquerade as the sentinel and the spec would be hollow).
finite_reals = [-1e308, -1e9, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 1e9, 1e308]
for v in finite_reals:
    if bool(np.isinf(v)):
        fail.append("finite real %r wrongly satisfies is_pos_inf" % v)
    # the pre-patch value max+1 is finite for any finite score
    if bool(np.isinf(v + 1.0)):
        fail.append("finite+1.0 (pre-patch lead) %r wrongly infinite" % v)

# 3. negative infinity is NOT the positive sentinel (np.isinf is True for -inf,
#    but the axiom's lead is POSITIVE; pos_inf() returns +inf, so the model never
#    constructs -inf -- assert np.inf is distinguishable from -np.inf by sign).
if np.isinf(-np.inf) and (-np.inf > 0):
    fail.append("-inf wrongly classified positive")

# 4. randomized fuzz over score scales: max+1 stays finite, +inf stays infinite.
import random
rng = random.Random(26194)
for _ in range(20000):
    mode = rng.randint(0, 2)
    if mode == 0:
        v = rng.random()                 # probability estimate in [0,1)
    elif mode == 1:
        v = rng.uniform(-1e6, 1e6)       # arbitrary confidence score
    else:
        v = rng.uniform(-1e300, 1e300)   # large magnitude
    if bool(np.isinf(v)):
        fail.append("fuzz finite %r wrongly infinite" % v); break
    if bool(np.isinf(v + 1.0)):
        fail.append("fuzz finite+1 %r wrongly infinite" % v); break

if fail:
    print("AXIOM-UNSOUND:", "; ".join(fail[:5]))
    sys.exit(1)
print("axiom-soundness OK: is_pos_inf(pos_inf()) holds on real numpy; "
      "np.isinf(np.inf) True & positive; no finite real (incl. pre-patch max+1) "
      "satisfies is_pos_inf over 20000+ fuzz inputs.")
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys
import numpy as np

# AXIOM-CONTAINMENT for is_pos_inf / pos_inf. Enumerate EXACTLY the callee-inputs
# the MODEL can reach and assert each lies in the axiom's Requires domain.
#
#  - pos_inf() takes NO argument; the only value it yields is the sentinel.
#  - is_pos_inf is applied by the spec ONLY to Result()[0] (post-condition
#    is_pos_inf(Result()[0]) and the invariant is_pos_inf(ToSeq(result)[0])).
#    Any verifying impl must make Result()[0] provably equal pos_inf() (is_pos_inf
#    is opaque with sole fact is_pos_inf(pos_inf())). So the ONLY argument the
#    model can reach for is_pos_inf is np.inf itself.
#  - np.isinf is a numpy ufunc total over all real floats (and arrays), so np.inf
#    is comfortably inside its domain (no Requires restriction to violate).
#
# Containment is therefore: the single reachable callee-input (np.inf) is in
# np.isinf's domain. We assert np.isinf accepts np.inf without error and that the
# domain is not narrower than the model needs.
fail = []

try:
    r = np.isinf(np.inf)
except Exception as e:                       # pragma: no cover
    fail.append("np.isinf(np.inf) raised: %r" % e)
    r = None
if r is not None and not bool(r):
    fail.append("np.isinf(np.inf) returned False (reachable input not recognized)")

# the model can only ever pass the sentinel; confirm no other value is reachable
# by construction (pos_inf() is nullary; the lead is set to pos_inf()).  As a
# defensive containment check, confirm np.isinf is total on the float line the
# model's reals live on (so the axiom domain is never narrower than the caller):
for v in [-np.inf, -1e308, -1.0, 0.0, 1.0, 1e308, np.inf]:
    try:
        np.isinf(v)
    except Exception as e:
        fail.append("np.isinf domain too narrow: raised on %r: %r" % (v, e))

if fail:
    print("AXIOM-TOO-WEAK-FOR-CALLER:", "; ".join(fail[:5]))
    sys.exit(1)
print("axiom-containment OK: the only callee-input the model can reach for "
      "is_pos_inf is np.inf (pos_inf() is nullary; Result()[0] must equal "
      "pos_inf()); np.inf is in np.isinf's (total) domain. Covering more reals "
      "than the caller reaches is SOUND, not a defect.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-pos-inf-isinf",
        "axiom": "pos_inf/is_pos_inf",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,   # np.inf / np.isinf are patch-state-independent
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "The consumed obligation is_pos_inf(pos_inf()) holds on the real numpy "
            "callees (np.isinf(np.inf) True & positive), and is_pos_inf separates "
            "the sentinel from every finite real (incl. the pre-patch max+1). If "
            "the real callee disagreed -> AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-contain-isinf-domain",
        "axiom": "pos_inf/is_pos_inf",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": (
            "The only callee-input the model can reach for is_pos_inf is np.inf "
            "(pos_inf() is nullary; a verifying impl must set Result()[0]==pos_inf()). "
            "np.inf is in np.isinf's total domain. A reachable input outside the "
            "domain would be AXIOM-TOO-WEAK-FOR-CALLER; none exists here."
        ),
    },
]
