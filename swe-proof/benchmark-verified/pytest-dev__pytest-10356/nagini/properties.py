# properties.py — PBT falsification battery for pytest-dev__pytest-10356. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# the text BETWEEN # impl-start / # impl-end (the nested invariants region is
# inside impl, so it too is editable without touching the spec view). The runner
# re-runs the Nagini verifier on the host and checks the verify/reject outcome
# against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   unpacked_tokens(chain: PSeq[PSeq[int]], consider_chain: bool) -> PSeq[int]
#     Requires(len(chain) >= 1)                                     # pre
#     Ensures(Implies(consider_chain, Result() == concat_chain(chain)))   # (1)
#     Ensures(Implies(not consider_chain, Result() == chain[0]))          # (2)
#   @Pure concat_chain(chain) = chain[0] + concat_chain(chain.drop(1)) ;
#                               len 0 -> empty.  A front-recursive fold:
#     the FULL MRO-ordered concatenation of every member's own token list.
#
# What the spec defends (the load-bearing facts):
#   * (1) consider_chain=True branch: Result() == concat_chain(chain) — the
#     EXACT, ordered, full-chain concatenation. This is the discriminating
#     content of the gold change: a class with two independently-decorated
#     ancestors must keep BOTH ancestors' tokens (["c","a","b"]), not just one.
#     The pre-patch read a single MRO-resolved attribute and lost the others;
#     model_prepatch.py reproduces that (return chain[0]) and FAILS clause (1)
#     (G-DIFF). Because concat_chain is GROUNDED (a @Pure fold of the input
#     chain, fully unfoldable by the verifier), no fabricated/echoed wrong value
#     can satisfy this clause — the verifier proves Result() == concat_chain(
#     chain) only when the returned sequence provably IS that fold.
#   * (2) consider_chain=False branch: Result() == chain[0] — exactly the
#     class's own directly-attached tokens.
#
# Permission / frame-mutation: BOTH inputs are pure mathematical VALUE types —
# `chain: PSeq[PSeq[int]]` is an immutable Viper Seq passed by value and
# `consider_chain: bool` is a scalar. There is NO heap reference and NO
# Acc(...) permission anywhere in this bundle (verified: model.py has zero
# Acc/Rd/Fold/Predicate). So there is NO read-only Acc(x,1/2) input, and the
# canonical frame-mutation probe (write a half-permission input to satisfy the
# postcondition vacuously, expect insufficient-permission) does NOT apply and
# cannot even be expressed here — there is nothing on the heap to overwrite.
# See `assessment`.
#
# Ungrounded-oracle echo: concat_chain is NOT an opaque @ContractOnly answer-key;
# it is a fully-spelled-out @Pure fold of the input `chain`. Echoing it
# (return concat_chain(chain)) is the HONEST cheapest correct impl, not a cheat —
# so it is the positive control (pos-control-direct), not a weak-echo reject.
# There is no WRONG value an impl can echo that the verifier would accept,
# because the only oracle is a function of the args. (Directive 2 honest path.)
#
# Axioms: AXIOM_TESTS = [] — there is NO consumed @ContractOnly axiom (axioms
# region is empty). The changed collection is modelled DEEPLY as concat_chain
# (an A-reference), validated == the real get_unpacked_marks out-of-band by
# axiom_check.py / G-AX (F2P shape + 6 boundary shapes + ~4000 fuzz hierarchies).
# That A-reference soundness is a Docker-callee check already owned by G-AX; the
# PBT axiom lane adds nothing here, so it is intentionally empty.
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10356"
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
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec. The nested
# invariants region is INSIDE impl, so it is elided from the spec view too.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    if not consider_chain:
        return chain[0]
    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
    # is empty, and concat_chain of the empty chain is the empty sequence).
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        # `result` is the concatenation of the suffix chain[i:].
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-direct: the cheapest honest impl. concat_chain is grounded (a
# @Pure fold of the input), so returning it directly in the true branch is
# behaviourally exactly the gold result. No loop, no invariant, no asserts —
# a structurally different shape that the postcondition (Result() ==
# concat_chain(chain)) accepts trivially. The false branch is unchanged. This is
# also the directive-2 honest oracle positive control (the oracle is grounded,
# so echoing it is correct). If this cannot verify => SPEC-TOO-STRONG.
_POS_DIRECT = """    # impl-start
    if not consider_chain:
        return chain[0]
    return concat_chain(chain)
    # impl-end"""

# pos-control-reshape: keep the gold BACKWARD loop (front-recursive concat_chain
# discharges with a single unfold per member, so the gold proof is valid — we do
# NOT flip to a forward append, which would need an f(a+b)==f(a)+f(b) lemma the
# verifier cannot auto-discharge; pilot pitfall #3 avoided), but reshape the
# accumulator seed and the loop variable. Seed the empty accumulator from
# chain[0].take(0) instead of chain[len-1].take(0) (both are the empty PSeq for
# any in-bounds index — exactly the G-MUT survivor's equivalence), and reorder
# the two framing Asserts. The gold invariants and per-step framing Asserts are
# KEPT verbatim (pilot pitfall #2 avoided), so the loop invariant still proves.
# Must verify (else SPEC-TOO-STRONG).
_POS_RESHAPE = """    # impl-start
    if not consider_chain:
        return chain[0]
    result = chain[0].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a separate caller function: a
# new module-level def changes the projected spec view and breaks same_spec.
# Instead we inject the admissibility witness INSIDE the impl region (elided from
# the spec view) as a leading block that constructs a concrete F2P-shaped chain
# (the F2P shape C(A,B) -> __mro__ = [C, A, B, object], own tokens
# [["c"],["a"],["b"],[]] -> a length-4 chain of PSeq[int]) and asserts the
# function's exact Requires (len(chain) >= 1) holds for it. The real impl then
# runs unchanged over the actual params. If the precondition could not be
# established for this legitimate input the Assert fails => PRECOND-TOO-STRONG.
# (PSeq(...) literals + .take(0) build value sequences with no permission.)
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for the F2P-shaped input (elided from spec view) ---
    # C(A,B) decorated ["c"]/["a"]/["b"]: MRO own-token lists C,A,B,object.
    c_own = PSeq(101)            # type: PSeq[int]
    a_own = PSeq(102)            # type: PSeq[int]
    b_own = PSeq(103)            # type: PSeq[int]
    obj_own = PSeq(101).take(0)  # type: PSeq[int]
    adm = PSeq(c_own, a_own, b_own, obj_own)  # type: PSeq[PSeq[int]]
    # the function's Requires is establishable for this concrete F2P-shaped chain:
    Assert(len(adm) >= 1)
    # --- end admissibility witness; the real impl follows unchanged ---
    if not consider_chain:
        return chain[0]
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain / control-flow — rivals that share the spec
# exactly and change ONLY the impl. Each MUST be rejected; a verifying rival is
# a real verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-class-only-prepatch: THE BUG. Return chain[0] in BOTH branches — i.e. only
# the class's own tokens even when the full chain is considered. This is exactly
# model_prepatch.py and the pre-patch single-MRO-resolved-attribute read.
# Rejected by clause (1): on the F2P shape Result() would be ["c"] but
# concat_chain(chain) == ["c","a","b"].
_UNIQ_CLASS_ONLY = """    # impl-start
    return chain[0]
    # impl-end"""

# uniq-drop-first (partial-domain): concatenate only the ANCESTORS, dropping the
# class's own tokens (loop down to i > 1, leaving chain[0] out; the accumulator
# ends as concat_chain(chain.drop(1))). Correct on the SUFFIX of the domain
# (ancestor tokens, in order) but diverges on chain[0]. Rejected by clause (1):
# Result() == concat_chain(chain.drop(1)) != concat_chain(chain) whenever
# chain[0] is non-empty (the F2P shape: ["a","b"] vs ["c","a","b"]).
_UNIQ_DROP_FIRST = """    # impl-start
    if not consider_chain:
        return chain[0]
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 1:
        # invariants-start
        Invariant(1 <= i and i <= len(chain))
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-drop-last (partial-domain): concatenate every member EXCEPT the last
# (stop the loop one member early: while i > 1 prepending down to chain[1], then
# never prepend chain[0]... no — here we drop the deepest member). We seed from
# the full chain but start the loop at len-1 so chain[len-1] (the deepest MRO
# member, e.g. `object`'s slot / the last decorated ancestor) is never folded in.
# Correct on the PREFIX of the domain but diverges on the last element. Rejected
# by clause (1) whenever the last member's tokens are non-empty.
_UNIQ_DROP_LAST = """    # impl-start
    if not consider_chain:
        return chain[0]
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-swap-branches (control-flow-effect): swap the two branch outputs — return
# the full concatenation when the chain is NOT considered, and only chain[0]
# when it IS. The value abstraction sees a flag-routing difference invisible
# unless both Ensures clauses pin their respective branch. Rejected: on
# consider_chain=True it returns chain[0] (violates clause (1)); on
# consider_chain=False it returns concat_chain(chain) (violates clause (2)).
_UNIQ_SWAP = """    # impl-start
    if consider_chain:
        return chain[0]
    return concat_chain(chain)
    # impl-end"""

# uniq-self-only-when-chain (supporting near-miss / partial-domain on the empty-
# ancestor sub-domain): return concat_chain(chain) only when len(chain) > 1,
# else (a single-member chain) return the empty sequence. Correct on
# multi-member chains but wrong on the length-1 sub-domain (a class with no
# decorated ancestors). Rejected by clause (1): for len(chain)==1,
# concat_chain(chain) == chain[0] which may be non-empty, but this returns empty.
_UNIQ_LEN1_EMPTY = """    # impl-start
    if not consider_chain:
        return chain[0]
    if len(chain) > 1:
        return concat_chain(chain)
    empty = chain[0].take(0)  # type: PSeq[int]
    return empty
    # impl-end"""

# uniq-reverse-order (value-level ordering attack): build the concatenation in
# the WRONG order — fold the chain front-to-back appending (so deepest ancestor
# ends up first / order reversed relative to MRO). Concretely, return
# concat_chain of the reversed chain is not expressible cheaply; instead drop the
# first member's contribution to the FRONT and append it at the END, i.e. return
# concat_chain(chain.drop(1)) + chain[0]. This contains the same multiset of
# tokens but in the wrong order (ancestors first, class last: ["a","b","c"]
# instead of ["c","a","b"]). Rejected by clause (1): ordered equality fails even
# though every token is present — defeats any membership/multiset value proxy.
_UNIQ_REORDER = """    # impl-start
    if not consider_chain:
        return chain[0]
    return concat_chain(chain.drop(1)) + chain[0]
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_DIRECT),
        "rationale": "the cheapest honest impl: return concat_chain(chain) directly "
                     "in the consider_chain=True branch (no loop, no invariant). "
                     "concat_chain is a GROUNDED @Pure fold of the input, so this is "
                     "behaviourally the gold result and satisfies clause (1) "
                     "trivially; the false branch is unchanged. Also the directive-2 "
                     "honest grounded-oracle positive control. If a faithful correct "
                     "impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_RESHAPE),
        "rationale": "structural reshape of the gold backward loop: seed the empty "
                     "accumulator from chain[0].take(0) instead of "
                     "chain[len-1].take(0) (both are the empty PSeq for any in-bounds "
                     "index — the G-MUT-survivor equivalence) and reorder the two "
                     "framing Asserts. The gold backward direction and the gold "
                     "invariants/Asserts are KEPT (no forward-append lemma needed; "
                     "pilot pitfalls #2/#3 avoided), so the loop invariant still "
                     "proves. If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds the F2P "
                     "shape C(A,B) as a concrete length-4 chain of PSeq[int] "
                     "([[c],[a],[b],[]] for MRO C,A,B,object) and asserts the "
                     "function's exact Requires (len(chain) >= 1) holds for it. The "
                     "real impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness / partial-domain / control-flow (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-class-only-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_CLASS_ONLY),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags: get_unpacked_marks read a single "
                      "MRO-resolved attribute (getattr(obj,'pytestmark',[])) and "
                      "returned only ONE source's marks. The sole F2P test "
                      "test_mark_mro builds C(A,B) with @xfail('c')/@xfail('a')/"
                      "@xfail('b') and asserts get_unpacked_marks(C) == "
                      "[xfail('c').mark, xfail('a').mark, xfail('b').mark]; returning "
                      "only the class's own marks gives [xfail('c').mark] and the F2P "
                      "assertion fails. Its faithful real patch (the un-patched "
                      "single-attribute read) is exactly what does NOT resolve.",
        "rationale": "rejected by clause (1) Ensures(Implies(consider_chain, "
                     "Result() == concat_chain(chain))): returning chain[0] gives the "
                     "class's own tokens only, but concat_chain(chain) is the full "
                     "MRO concatenation (F2P: [c] != [c,a,b]).",
    },
    {
        "id": "uniq-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_FIRST),
        "refinement": "drops the class's OWN tokens, returning only the ancestors' "
                      "concatenation (the loop stops at i>1, never folding chain[0]). "
                      "The faithful real patch — collecting [x.__dict__.get("
                      "'pytestmark',[]) for x in obj.__mro__[1:]] (skipping obj "
                      "itself) — loses the directly-applied marks; on the F2P shape "
                      "get_unpacked_marks(C) would be [xfail('a').mark, "
                      "xfail('b').mark], dropping xfail('c').mark, so the F2P "
                      "assertion fails. Does NOT resolve.",
        "rationale": "rejected by clause (1): Result() == concat_chain(chain.drop(1)) "
                     "!= concat_chain(chain) whenever chain[0] is non-empty (F2P: "
                     "[a,b] != [c,a,b]). Partial-domain: correct on the ancestor "
                     "suffix, wrong on the first member.",
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_LAST),
        "refinement": "drops the DEEPEST MRO member's tokens (the loop starts at "
                      "i=len-1, so chain[len-1] is never folded in). The faithful "
                      "real patch — iterating obj.__mro__[:-1] (skipping the last "
                      "base) — loses the last ancestor's marks; on a chain whose last "
                      "member carries tokens (e.g. the F2P deepest decorated "
                      "ancestor) the resulting list is missing that ancestor's marks "
                      "and the F2P ordered-equality assertion fails. Does NOT resolve.",
        "rationale": "rejected by clause (1): Result() omits the last member's "
                     "tokens, so Result() != concat_chain(chain) whenever the last "
                     "member is non-empty. Partial-domain: correct on the prefix, "
                     "wrong on the final element.",
    },
    {
        "id": "uniq-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWAP),
        "refinement": "swaps the two flag branches — returns the full MRO "
                      "concatenation when consider_mro is FALSE and only the class's "
                      "own marks when it is TRUE. The faithful real patch would route "
                      "the consider_mro flag backwards: get_unpacked_marks(C) (default "
                      "consider_mro=True) would return only [xfail('c').mark] (F2P "
                      "first assertion fails), and get_unpacked_marks(C, "
                      "consider_mro=False) would return [c,a,b] (F2P second assertion "
                      "fails). Additionally store_mark calls with consider_mro=False "
                      "expecting only own marks; this rival would make it collect the "
                      "whole MRO and double-count. Does NOT resolve.",
        "rationale": "control-flow-effect: rejected by BOTH clauses. On "
                     "consider_chain=True it returns chain[0] (violates clause (1) "
                     "Result()==concat_chain(chain)); on consider_chain=False it "
                     "returns concat_chain(chain) (violates clause (2) "
                     "Result()==chain[0]). The flag-routing difference is caught only "
                     "because each branch is pinned by its own Ensures.",
    },
    {
        "id": "uniq-reorder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REORDER),
        "refinement": "produces the same multiset of tokens in the WRONG order — "
                      "ancestors first, the class's own tokens appended last "
                      "(concat_chain(chain.drop(1)) + chain[0]). The faithful real "
                      "patch — building mark_list by extending the ancestor lists "
                      "first and the class's own list last — yields [xfail('a').mark, "
                      "xfail('b').mark, xfail('c').mark] for the F2P shape, but the "
                      "F2P asserts == [xfail('c').mark, xfail('a').mark, "
                      "xfail('b').mark]; ordered list equality fails. Does NOT resolve.",
        "rationale": "value-level ordering attack: rejected by clause (1) because "
                     "Result() == concat_chain(chain.drop(1)) + chain[0] is the same "
                     "tokens in reversed-group order, != concat_chain(chain) "
                     "(class-first). Ordered PSeq equality defeats any "
                     "membership/multiset value proxy ([a,b,c] != [c,a,b]).",
    },
    {
        "id": "uniq-len1-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_LEN1_EMPTY),
        "refinement": "supporting partial-domain near-miss: correct for chains with "
                      ">1 member, but returns the empty sequence for a single-member "
                      "chain (a class with NO decorated ancestors, just its own "
                      "marks). The faithful real patch — short-circuiting "
                      "len(obj.__mro__)==1 to [] — would make get_unpacked_marks of a "
                      "lone decorated class return [] instead of its own marks, "
                      "breaking store_mark accumulation and the P2P mark-collection "
                      "tests (e.g. a standalone @pytest.mark class loses its mark). "
                      "Does NOT resolve.",
        "rationale": "rejected by clause (1) on the length-1 sub-domain: for "
                     "len(chain)==1, concat_chain(chain) == chain[0] (which is "
                     "non-empty when the class carries its own tokens), but this "
                     "returns the empty PSeq. Partial-domain: the failing input is "
                     "the smallest legitimate one (len(chain)==1, allowed by "
                     "Requires).",
    },
]

# No consumed @ContractOnly axiom and no A-reference deep model needs a Docker
# real-callee probe here at the PBT layer: concat_chain's soundness against the
# real get_unpacked_marks is owned by axiom_check.py / G-AX (already pass). See
# the header note. Hence the axiom lane is intentionally empty.
AXIOM_TESTS = []
