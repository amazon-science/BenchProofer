# properties.py — PBT falsification battery for scikit-learn__scikit-learn-14053.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py variant that shares the frozen spec
# (markers.same_spec) and differs ONLY inside the # impl-start/# impl-end region
# (loop body + loop invariants). The runner re-runs the Nagini verifier on each.
#
# Defended surface of resolve_node_names(names: List[int], feat: List[int]):
#   - BOTH inputs are READ-ONLY: Acc(list_pred(names), 1/2) and
#     Acc(list_pred(feat), 1/2) in Requires AND Ensures => frame-mutation is the
#     #1 attack and is MANDATORY.
#   - Precondition: in_domain(ToSeq(names), ToSeq(feat)) — every selector is the
#     reserved out-of-band value -2 or a valid position in the name table.
#   - LOAD-BEARING postcondition: ToSeq(Result()) == built_seq(ToSeq(names),
#     ToSeq(feat)), plus len(Result()) == len(feat) and Acc(list_pred(Result())).
#   - built_seq is a fully-unfolded @Pure DEEP MODEL of the patched comprehension
#     [feature_names[i] if i != _tree.TREE_UNDEFINED else None for i in
#      tree_.feature]; it is GROUNDED in the args (not an opaque answer key), so
#     there is no "wrong echo that still verifies" — echoing built_seq IS doing
#     the work. See 'assessment' / the ungrounded-oracle note below.
#   - No @ContractOnly callee, axioms == [] => AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14053"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (everything from `result = []` to `return
# result`, including the loop invariants). Editing only these keeps same_spec.
# ---------------------------------------------------------------------------

# The whole gold loop body that selects each node's resolved entry.
_GOLD_BODY = """        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1"""

# The two framing asserts the loop invariant needs (front-recursive unfold).
_GOLD_FRAMING = """        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))"""


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — a structurally-DIFFERENT but CORRECT impl
#    must verify. Reshape: hoist the per-node resolved entry into a single
#    local `elem` and prepend ONCE, instead of two `[x] + result` branches.
#    Keeps the backward loop direction (front-recursive built_seq stays valid)
#    and keeps BOTH gold framing asserts (directive: don't drop the lemma).
#    If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS_BODY = """        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        elem = None  # type: Optional[int]
        if fi != -2:
            elem = names[fi]
        result = [elem] + result
        i = i - 1"""
_pos = _swap(_BASE, _GOLD_BODY, _POS_BODY)


# ===========================================================================
# 2. ADMISSIBILITY — the precondition admits a normal, F2P-shaped input. We
#    invoke resolve_node_names on the in-scope (already in-domain) params via a
#    self-call (it requires/returns Acc(...,1/2), so permission round-trips),
#    and RETURN the probe's result so the contract is consumable end-to-end (the
#    self-call's postcondition re-establishes our own). If the Requires were
#    contradictory/too strong this self-call could not be established
#    => PRECOND-TOO-STRONG.
#
#    NOTE: the probe must PRODUCE the result, not precede the gold loop. The
#    Ensures returns Acc(list_pred(names/feat), 1/2) but does NOT pin
#    ToSeq(names)/ToSeq(feat) to their pre-call values (faithful: the spec is
#    about the RESULT, not echoing immutable inputs). So a self-call placed
#    before the loop drops the value-framing of the inputs across the call,
#    after which the loop invariant in_domain(ToSeq(names), ToSeq(feat)) cannot
#    be re-derived on entry — a probe-construction artifact, NOT a too-strong
#    precondition (asserting in_domain on the in-scope params alone verifies).
#    Returning the probe avoids any downstream framing: our postcondition
#    (len/ToSeq(Result())==built_seq/Acc) follows directly from the probe's.
# ===========================================================================
_ADMISS_BODY = """    result = []  # type: List[Optional[int]]
    i = len(feat)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(feat), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(feat))
        Invariant(in_domain(ToSeq(names), ToSeq(feat)))
        Invariant(len(result) == len(feat) - i)
        Invariant(ToSeq(result) == built_seq(ToSeq(names), ToSeq(feat).drop(i)))
        # invariants-end
        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1
    return result"""
_ADMISS_NEW = """    probe = resolve_node_names(names, feat)  # type: List[Optional[int]]
    Assert(len(probe) == len(feat))
    return probe"""
_admiss = _swap(_BASE, _ADMISS_BODY, _ADMISS_NEW)


# ===========================================================================
# 3. FRAME-MUTATION (uniqueness, reject) — MANDATORY: `feat` is read-only
#    (Acc(list_pred(feat), 1/2)). A rival that WRITES the input to cheat the
#    fold must fail for INSUFFICIENT PERMISSION, not for value mismatch. We keep
#    the exact gold value flow and gold framing asserts so the rejection is
#    attributable solely to the write `feat[i - 1] = fi`.
# ===========================================================================
_FRAME_BODY = """        fi = feat[i - 1]
        feat[i - 1] = fi
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1"""
_frame = _swap(_BASE, _GOLD_BODY, _FRAME_BODY)


# ===========================================================================
# 3b. FRAME-MUTATION on `names` (uniqueness, reject) — the OTHER read-only input.
#     A rival that appends to / overwrites `names` (e.g. to "pad" the table so a
#     leaf marker becomes in range) must fail for insufficient permission.
# ===========================================================================
_FRAME2_BODY = """        fi = feat[i - 1]
        names[0] = fi
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1"""
_frame2 = _swap(_BASE, _GOLD_BODY, _FRAME2_BODY)


# ===========================================================================
# 4. PARTIAL-DOMAIN (uniqueness, reject) — correct on MOST nodes but diverges
#    on the FIRST node (the last backward iteration, i == 1): emit the leaf
#    placeholder None even for an internal-node selector. On the F2P input the
#    root is an INTERNAL node (the single feature 'first'), so this drops the
#    root's resolved name. The postcondition ToSeq(Result()) == built_seq(...)
#    pins names[fi] at every internal node, so this MUST be rejected.
#    Refinement: a faithful patch that returns None at the root would print the
#    root split without its feature name (the comparison line `|--- first <= 0`)
#    => export_text output != the expected report => test_export_text FAILS.
# ===========================================================================
_PARTIAL_BODY = """        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2 and i > 1:
            nm = names[fi]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1"""
_partial = _swap(_BASE, _GOLD_BODY, _PARTIAL_BODY)


# ===========================================================================
# 5. VALUE / WRONG-ENTRY (uniqueness, reject) — every internal node resolves to
#    names[0] (the first table entry) instead of names[fi]. This is ACCIDENTALLY
#    correct on the F2P single-feature tree (every internal node selects feature
#    0, so names[fi] == names[0]) but wrong as soon as the table has >= 2
#    features. The postcondition pins names[fi] exactly, so it MUST be rejected.
#    Refinement: a faithful patch substituting feature_names[0] for every node
#    mislabels every split on feature index != 0 (e.g. a 2-feature tree's
#    feature_1 nodes print 'first' instead of the real name) => for any
#    multi-feature export_text the printed report is wrong. (It happens to pass
#    the single-feature F2P, which is exactly why pinning the exact entry — not
#    just "some name" — is load-bearing.)
# ===========================================================================
_WRONG_BODY = """        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if fi != -2:
            nm = names[0]  # type: Optional[int]
            result = [nm] + result
        else:
            none_val = None  # type: Optional[int]
            result = [none_val] + result
        i = i - 1"""
_wrong = _swap(_BASE, _GOLD_BODY, _WRONG_BODY)


# ===========================================================================
# 6. LENGTH / DROP-NODE (uniqueness, reject) — supporting case. Skip prepending
#    the very first node entirely (i == 1): result is one element short. The
#    postcondition len(Result()) == len(feat) MUST reject this.
#    Refinement: a patch that drops a node's entry yields a feature_names_ list
#    shorter than tree_.feature; export_text indexes feature_names_ by node id,
#    so the misalignment crashes / prints the wrong names => F2P fails.
# ===========================================================================
_DROP_BODY = """        fi = feat[i - 1]
        Assert(ToSeq(feat).drop(i - 1)[0] == fi)
        Assert(ToSeq(feat).drop(i - 1).drop(1) == ToSeq(feat).drop(i))
        if i > 1:
            if fi != -2:
                nm = names[fi]  # type: Optional[int]
                result = [nm] + result
            else:
                none_val = None  # type: Optional[int]
                result = [none_val] + result
        i = i - 1"""
_drop = _swap(_BASE, _GOLD_BODY, _DROP_BODY)


SPEC_TESTS = [
    {
        "id": "pos-control-single-prepend",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos,
        "rationale": "structurally-different but CORRECT impl (hoist the resolved "
                     "entry into one local `elem`, prepend once, instead of two "
                     "[x]+result branches); keeps the backward loop and BOTH gold "
                     "framing asserts so the front-recursive built_seq proof stays "
                     "valid. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": "self-call on the in-domain params (Acc(...,1/2) round-trips) "
                     "that PRODUCES the returned result; asserts the contract is "
                     "consumable (len(probe)==len(feat)) and re-establishes our own "
                     "postcondition from the probe's. If Requires were contradictory/"
                     "too strong this call could not be established => PRECOND-TOO-"
                     "STRONG.",
    },
    {
        "id": "frame-mutation-feat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame,
        "refinement": "writing feat[i-1] mutates tree_.feature, the fitted tree's "
                      "internal split-feature array shared across export_text; a "
                      "faithful patch that overwrites it corrupts the tree object "
                      "(subsequent print_tree_recurse reads tree_.feature) and "
                      "would not produce the expected report — F2P fails.",
        "rationale": "feat is read-only (Acc(list_pred(feat),1/2)); the write "
                     "demands full permission the caller never grants. Rejection "
                     "is from the PERMISSION SYSTEM, not a value mismatch (gold "
                     "value flow + framing asserts are kept verbatim).",
    },
    {
        "id": "frame-mutation-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame2,
        "refinement": "writing names[0] mutates the caller's feature_names list "
                      "in place; a faithful patch that overwrites the name table "
                      "corrupts the names other nodes resolve to, so the printed "
                      "report is wrong — F2P fails.",
        "rationale": "names is read-only (Acc(list_pred(names),1/2)); the store "
                     "needs full permission. Rejection is from the PERMISSION "
                     "SYSTEM (gold value flow + framing asserts kept verbatim).",
    },
    {
        "id": "partial-domain-root-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial,
        "refinement": "emits None at the first node (the tree root) even though it "
                      "is an internal split node; a faithful patch doing this drops "
                      "the root split's feature name, so export_text prints the root "
                      "comparison without 'first' (`|--- <= 0.0` instead of "
                      "`|--- first <= 0.0`) => output != expected_report => "
                      "test_export_text FAILS.",
        "rationale": "postcondition ToSeq(Result())==built_seq(...) pins names[fi] "
                     "at every internal node, including node 0; emitting None there "
                     "violates that clause.",
    },
    {
        "id": "wrong-entry-names0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong,
        "refinement": "resolves every internal node to names[0] instead of "
                      "names[fi]. Accidentally CORRECT on the single-feature F2P "
                      "tree (all internal nodes select feature 0). A faithful patch "
                      "substituting feature_names[0] for every node mislabels any "
                      "split on a feature index != 0, so every multi-feature "
                      "export_text report is wrong — this is exactly why the spec "
                      "must pin the EXACT entry, not merely 'some name'.",
        "rationale": "postcondition pins names[fi] (via built_seq); names[0] != "
                     "names[fi] in general, so the fold-equality clause rejects it.",
    },
    {
        "id": "drop-first-node-length",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop,
        "refinement": "skips prepending the first node, so feature_names_ is one "
                      "shorter than tree_.feature; export_text indexes "
                      "feature_names_ by node id, so the off-by-one misaligns/"
                      "crashes the printed names — F2P fails. (Supporting case: a "
                      "node-count drop the length clause must reject.)",
        "rationale": "postcondition len(Result())==len(feat) is violated (result "
                     "is len(feat)-1).",
    },
]


# No @ContractOnly axioms and no A-reference deep callees (axioms == [], the
# changed operation is the deep model built_seq, fully verified in-module). The
# axiom lane is vacuous for this instance.
AXIOM_TESTS = []
