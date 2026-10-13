# properties.py — PBT falsification battery for pytest-dev__pytest-5631.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region (the nested # invariants region lives inside
# impl, so editing it still keeps same_spec — spec_view elides the whole impl
# span); the runner checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance.json):
#   count_mock_patch_args(kinds: List[int]) -> int
#   counts how many replacement directives stand in for a runner-supplied arg.
#   `kinds` is a List[int] of per-directive kind tags in {0,1,2,3}:
#     0 binds an attribute name (never counts); 1 binds none + value IS a
#     placeholder singleton by IDENTITY (counts); 2 binds none + comparable
#     non-placeholder (excluded); 3 binds none + NON-truth-evaluable equality
#     (excluded by identity; the pre-patch value-equality membership RAISES here).
#
#   `kinds` is READ-ONLY: Requires/Ensures/Invariant all carry Acc(list_pred(kinds),
#   1/2). The helper must not mutate it. => FRAME-MUTATION case is MANDATORY.
#
#   Load-bearing postcondition clauses:
#     (P1) Acc(list_pred(kinds), 1/2)                      [frame: return the half-perm]
#     (P2) Result() == count_sentinel_directives(ToSeq(kinds))   [the EXACT count]
#     (P3) 0 <= Result() and Result() <= len(kinds)        [soundness bound]
#     (P4) implicit TOTALITY: there is NO Exsures on the contract, so the helper
#          may NEVER raise on any admissible input — including a kind-3 directive.
#          This is the discriminator vs the pre-patch value-equality membership.
#
#   count_sentinel_directives is a @Pure FRONT-RECURSIVE fold over ToSeq(kinds)
#   with counts_as_mock(k) == (k == 1). It is GROUNDED in the input (fully
#   unfoldable element-by-element), NOT an opaque answer-key oracle — so there is
#   no "wrong echo" that verifies (see 'assessment'); P2 echoes are honest
#   positive controls, not weak-spec breaks.
#
# F2P: TestMockDecoration::test_mock_sentinel_check_against_numpy_like — collects
#      a @patch(new=NumpyLike(...)) decoration whose .new has a raising __eq__;
#      the pre-patch `p.new in sentinels` raised ValueError at COLLECTION, the
#      post-patch identity decision does not. (the kind-3 totality break.)
# P2P: TestMockDecoration::test_getfuncargnames_patching et al. — keep counting
#      the same mock arguments (the kind-1 count must stay exact).

from pathlib import Path

INSTANCE = "pytest-dev__pytest-5631"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body (model.py lines 124-145). Every rival edits ONLY inside
# the # impl-start/# impl-end span (which contains the nested # invariants
# region). The block below is the verbatim region between the markers, used as
# the unique anchor for region surgery.
# ---------------------------------------------------------------------------
_IMPL = """    count = 0
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
                                                 0 <= kinds[k] and kinds[k] <= 3),
                                          [[kinds[k]]])))
        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
        Invariant(0 <= count and count <= len(kinds) - i)
        # invariants-end
        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        # Total identity decision: kind 1 (identity match, no attribute name)
        # counts; every other kind — including kind 3 (non-truth-evaluable
        # equality) — does not, and is handled without failure.
        if counts_as_mock(c):
            count = count + 1
        i = i - 1
    return count"""


# === POSITIVE CONTROL (soundness) =========================================
# Structurally-different but CORRECT: keep the backward loop (a forward loop
# against the FRONT-recursive count_sentinel_directives fold would need an
# f(a+b)==f(a)+f(b) lemma the verifier can't auto-discharge — directive 3), and
# instead reshape the accumulation: replace the `if`-increment with an
# arithmetic accumulate `count = count + (1 if counts_as_mock(c) else 0)`.
# Same executable meaning, every gold Invariant/Assert kept VERBATIM, so the
# loop invariant `count == count_sentinel_directives(ToSeq(kinds).drop(i))` (which
# unfolds to exactly `(1 if counts_as_mock(c) else 0) + ...`) still discharges.
# If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
_POS_IMPL = _IMPL.replace(
    """        if counts_as_mock(c):
            count = count + 1
        i = i - 1""",
    """        count = count + (1 if counts_as_mock(c) else 0)
        i = i - 1""",
)
POS_ARITH = _swap(_BASE, _IMPL, _POS_IMPL)


# === POSITIVE CONTROL 2 (cheapest grounded oracle) ========================
# The postcondition pins Result() to a GROUNDED @Pure fold, so the honest
# cheapest impl returns that fold directly (P2). This is NOT an ungrounded-oracle
# echo (the fold is fully unfolded over the input, not an opaque marker) — it is
# the faithful one-liner that MUST verify. The RETURN VALUE is the bare grounded
# fold `count_sentinel_directives(ToSeq(kinds))`; the spec accepts that output
# directly (P2 holds trivially).
#
# The only obstacle is P3 (`0 <= Result() and Result() <= len(kinds)`): proving
# the front-recursive @Pure fold is bounded requires INDUCTION over its
# recursion, which Nagini cannot auto-discharge from the @Pure definition alone
# (P3 fails with "Assertion (0 <= Result()) might not hold" on the bare
# one-liner). A module-level inductive lemma is NOT permissible here — it would
# add a top-level symbol and break same_spec. So the inductive bound is
# discharged INSIDE the impl region by a ghost proof loop that walks the suffixes
# of ToSeq(kinds), establishing `0 <= count_sentinel_directives(ToSeq(kinds)) <=
# len(kinds)` step-by-step (the standard in-region induction for a recursive
# @Pure). The proof loop accumulates a GHOST counter only; the returned value is
# still the bare grounded fold. This is a PROOF-ENGINEERING discharge of P3, not
# a spec change — same_spec is preserved (edits live entirely inside the impl
# span). Without it the case is a positive-control proof gap (a test artifact),
# NOT SPEC-TOO-STRONG: the spec admits the cheap fold output, it just needs the
# fold's intrinsic bound proven.
_CHEAP_IMPL = """    # Cheapest grounded oracle: return the @Pure fold directly (P2). The ghost
    # proof loop below discharges P3 (0 <= fold <= len) — the inductive
    # non-negativity / upper bound of the front-recursive fold, which Nagini
    # cannot auto-derive (and a module-level lemma would break same_spec).
    g = 0
    i = len(kinds)
    while i > 0:
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
                                                 0 <= kinds[k] and kinds[k] <= 3),
                                          [[kinds[k]]])))
        Invariant(g == count_sentinel_directives(ToSeq(kinds).drop(i)))
        Invariant(0 <= g and g <= len(kinds) - i)
        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        if counts_as_mock(c):
            g = g + 1
        i = i - 1
    n = count_sentinel_directives(ToSeq(kinds))  # type: int
    return n"""
POS_CHEAP = _swap(_BASE, _IMPL, _CHEAP_IMPL)


# === ADMISSIBILITY ========================================================
# A top-level caller addition would break same_spec (spec_view elides only the
# impl region; any new module-level symbol enters the spec signature). So the
# admissibility probe lives INSIDE the impl region, at the very top, before any
# gold obligation: construct a concrete F2P-shaped kind list ([0,1,2,3] — one of
# every directive kind, the exact shape the F2P/P2P populations build) and assert
# the Requires predicate (list_pred + the {0..3} range) is establishable on it.
# A self-recursive call would need a Decreases the spec doesn't carry (proof gap,
# not a spec defect), so we exercise the Requires-predicate directly. If this
# block cannot verify, the precondition is unsatisfiable for a normal input =>
# PRECOND-TOO-STRONG. Inserted right after `# impl-start`; every following gold
# obligation is preserved verbatim.
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P/P2P-shaped directive-kind list
    # (one of every kind tag {0,1,2,3}) establishes the Requires predicate.
    probe = [0, 1, 2, 3]  # type: List[int]
    Assert(list_pred(probe))
    Assert(len(probe) == 4)
    Assert(Forall(int, lambda j: (Implies(0 <= j and j < len(probe),
                                          0 <= probe[j] and probe[j] <= 3),
                                   [[probe[j]]])))"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- FRAME-MUTATION (MANDATORY: kinds is Acc(list_pred(kinds), 1/2) read-only).
# Rival that WRITES to the read-only input on the way to producing the count:
# it overwrites each visited element to 0 ("normalize away" non-mock kinds)
# before deciding. `kinds` is held at only 1/2 permission throughout (Requires,
# Invariant, Ensures), so a store `kinds[i-1] = 0` is NOT permitted — the rival
# must fail to verify for INSUFFICIENT PERMISSION, before any postcondition is
# even reached. Gold invariants/asserts kept verbatim so the rejection is
# attributable solely to the write.
# refinement: a faithful real patch that MUTATED `function.patchings` (e.g.
# del'd / rewrote directive entries while counting) would corrupt the live
# _patch list pytest later consults to actually apply the patches — every
# mock-decorated test (the P2P TestMockDecoration suite, e.g.
# test_getfuncargnames_patching) would then mis-apply or drop a patch and FAIL;
# it would NOT resolve.
# rejection source: the PERMISSION SYSTEM — only Acc(list_pred(kinds), 1/2) is
# held, so a store to kinds[...] is rejected for insufficient permission.
_FRAME_IMPL = _IMPL.replace(
    """        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)""",
    """        c = kinds[i - 1]
        # FRAME-MUTATION RIVAL: write to the READ-ONLY input. Only 1/2 permission
        # is held, so this store must be rejected for insufficient permission.
        kinds[i - 1] = 0
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)""",
)
FRAME_WRITE = _swap(_BASE, _IMPL, _FRAME_IMPL)


# --- CONTROL-FLOW-EFFECT / totality (THE discriminator — the actual bug).
# Rival reproducing the PRE-PATCH value-equality membership: on a kind-3
# directive (the array-like replacement value whose equality is non-truth-
# evaluable), it RAISES instead of returning a count. The contract carries NO
# Exsures, so any reachable raise on an admissible input (kind 3 is admissible —
# Requires allows kinds[i] in {0,1,2,3}) violates the totality obligation
# ("method raises no exceptions might not hold"). This is exactly what
# model_prepatch.py does and how G-DIFF senses the change.
# refinement: this IS the pre-patch behaviour (`p.new in sentinels` truth-tests
# `p.new == sentinel`, which raises ValueError on a NumPy-like p.new). The F2P
# test_mock_sentinel_check_against_numpy_like collects a @patch(new=NumpyLike)
# decoration; the raise happens at COLLECTION, so the test errors instead of
# passing — it does NOT resolve (it is the very bug the patch fixes).
# rejection source: the TOTALITY clause (absence of any Exsures, P4); a reachable
# raise on a kind-3 input is an inadmissible exceptional post-state.
_RAISE_IMPL = _IMPL.replace(
    """        if counts_as_mock(c):
            count = count + 1
        i = i - 1""",
    """        if c == 3:
            # PRE-PATCH VALUE-EQUALITY RIVAL: the non-truth-evaluable equality
            # surfaces as a raise. The contract has no Exsures => must be rejected.
            raise NonTruthEvaluableEquality()
        if counts_as_mock(c):
            count = count + 1
        i = i - 1""",
)
RAISE_ON_KIND3 = _swap(_BASE, _IMPL, _RAISE_IMPL)


# --- PARTIAL-DOMAIN: over-count by treating kind 3 as a mock too.
# Correct on every population WITHOUT a kind-3 directive (so it matches gold on
# the kind-{0,1,2} sub-domain that most P2P tests build), but DIVERGES on any
# population containing a kind-3 directive: it counts that array-like value as a
# placeholder. Identity (counts_as_mock) says kind 3 does NOT count, so this
# over-counts => violates P2 (Result() == count_sentinel_directives(...)).
# refinement: a faithful patch deciding membership by VALUE-EQUALITY-with-a-guard
# (e.g. `try: p.new in sentinels except: True`) would treat any uncomparable
# replacement value as a sentinel and COUNT it as a mock argument — the
# fixture-injection machinery would then expect pytest to supply that argument,
# breaking the F2P decoration (NumpyLike is NOT a mock sentinel and must NOT be
# counted); it would NOT resolve.
# rejection source: P2 — count_sentinel_directives counts kind 1 only, so an
# impl that increments on kind 3 produces a result != the pinned fold.
_PARTIAL_IMPL = _IMPL.replace(
    """        if counts_as_mock(c):
            count = count + 1
        i = i - 1""",
    """        if counts_as_mock(c) or c == 3:
            # PARTIAL-DOMAIN RIVAL: also counts kind 3 (the array-like value).
            count = count + 1
        i = i - 1""",
)
PARTIAL_KIND3_COUNTS = _swap(_BASE, _IMPL, _PARTIAL_IMPL)


# --- COUNT-EVERYTHING: the pre-patch `return len(patchings)` fallback (the path
# taken when no mock module is loaded). Returns len(kinds) regardless of kind.
# Correct ONLY on the all-kind-1 sub-domain; diverges on every directive of kind
# 0/2/3. Violates P2 (and P3's upper bound is not enough to save it — len(kinds)
# can exceed the true count). The whole loop is replaced by `return len(kinds)`.
# refinement: this is the pre-patch `return len(patchings)` branch; it counts
# attribute-bound and non-placeholder directives as mock arguments, so pytest's
# fixture machinery would expect to supply arguments it must not — the P2P
# TestMockDecoration tests (which assert specific funcarg counts, e.g.
# test_getfuncargnames_patching) would get the wrong count and FAIL; it would NOT
# resolve.
# rejection source: P2 — len(kinds) != count_sentinel_directives(ToSeq(kinds))
# whenever any directive is not kind 1.
_ALL_IMPL = """    total = len(kinds)  # type: int
    return total"""
COUNT_ALL = _swap(_BASE, _IMPL, _ALL_IMPL)


# --- VALUE-PROXY / OFF-BY-ONE on the first directive: count correctly but skip
# the FIRST directive (index 0 — the last loop iteration in the backward loop).
# Correct on every population whose first directive is NOT kind 1; diverges when
# the first directive IS a mock sentinel (it undercounts by 1). This pins the
# partial-domain hole "the input that fails first / a boundary element".
# refinement: a faithful patch with an off-by-one slice (`patchings[1:]`) would
# drop the first @patch directive from the count; a single-mock-arg decorated
# test (the common case) would then report 0 mock args, so pytest would try to
# supply the mocked argument as a fixture and the test would ERROR — it would NOT
# resolve.
# rejection source: P2 — stopping the loop at i==1 (skipping index 0) yields
# count_sentinel_directives(ToSeq(kinds).drop(1)) != the full fold whenever
# kinds[0] is kind 1.
_SKIPFIRST_IMPL = _IMPL.replace(
    """    count = 0
    i = len(kinds)
    while i > 0:""",
    """    count = 0
    i = len(kinds)
    # OFF-BY-ONE RIVAL: stop at i==1, skipping the first directive (index 0).
    while i > 1:""",
)
SKIP_FIRST = _swap(_BASE, _IMPL, _SKIPFIRST_IMPL)


SPEC_TESTS = [
    {
        "id": "pos-arith-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_ARITH,
        "rationale": "structurally-different CORRECT impl: keep the backward loop "
        "(a forward loop against the front-recursive fold would need an "
        "f(a+b) lemma — directive 3) and replace the if-increment with an "
        "arithmetic accumulate `count + (1 if counts_as_mock(c) else 0)`. Every "
        "gold Invariant/Assert kept verbatim, so the fold invariant still "
        "discharges. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-cheap-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CHEAP,
        "rationale": "honest cheapest impl: return the GROUNDED @Pure fold "
        "count_sentinel_directives(ToSeq(kinds)) directly (P2). The fold is fully "
        "unfolded over the input — not an opaque answer-key — so this is a faithful "
        "one-liner that MUST verify, not an ungrounded-oracle echo. Positive control "
        "for the grounded-oracle class (see 'assessment').",
    },
    {
        "id": "admiss-allkinds",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control probe builds an F2P/P2P-shaped directive-kind "
        "list [0,1,2,3] (one of every kind) and asserts the Requires predicate "
        "(list_pred + the {0..3} range invariant) is establishable — the "
        "precondition must admit a normal input, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write-readonly-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE,
        "refinement": "a faithful patch that MUTATED function.patchings while counting "
        "(rewrote/deleted directive entries) would corrupt the live _patch list "
        "pytest later applies; every mock-decorated test (P2P TestMockDecoration, "
        "e.g. test_getfuncargnames_patching) would mis-apply or drop a patch and FAIL "
        "— it would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(list_pred(kinds), 1/2) "
        "is held (Requires/Invariant/Ensures), so the store kinds[i-1]=0 fails for "
        "INSUFFICIENT PERMISSION before any postcondition is reached. MANDATORY "
        "frame-mutation probe (the read-only input is half-permission).",
    },
    {
        "id": "raise-on-kind3-totality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": RAISE_ON_KIND3,
        "refinement": "this IS the pre-patch behaviour: `p.new in sentinels` truth-tests "
        "`p.new == sentinel`, which raises ValueError on a NumPy-like p.new. The F2P "
        "test_mock_sentinel_check_against_numpy_like collects a @patch(new=NumpyLike) "
        "decoration; the raise fires at COLLECTION so the test ERRORS instead of "
        "passing — it does NOT resolve (it is the very bug the patch fixes).",
        "rationale": "rejected by the TOTALITY clause (P4: no Exsures on the contract): "
        "kind 3 is admissible (Requires allows {0,1,2,3}), so a reachable raise on it "
        "is an inadmissible exceptional post-state — the verifier reports 'method "
        "raises no exceptions might not hold'. control-flow-effect: a raise invisible "
        "to the value count, caught by the absence of an exceptional postcondition.",
    },
    {
        "id": "partial-kind3-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_KIND3_COUNTS,
        "refinement": "a faithful patch deciding membership by guarded value-equality "
        "(`try: p.new in sentinels except: True`) would treat any uncomparable "
        "replacement value as a sentinel and COUNT it as a mock argument; the F2P "
        "NumpyLike directive (not a sentinel) would be mis-counted, so pytest's "
        "fixture machinery would expect to supply it as an argument and the F2P test "
        "would FAIL — it would NOT resolve.",
        "rationale": "rejected by P2 (Result() == count_sentinel_directives(ToSeq(kinds))): "
        "the fold counts kind 1 ONLY, so incrementing on kind 3 over-counts on any "
        "kind-3 population. partial-domain: correct on the {0,1,2} sub-domain, diverges "
        "on any directive of kind 3.",
    },
    {
        "id": "count-everything-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": COUNT_ALL,
        "refinement": "this is the pre-patch `return len(patchings)` fallback (no-mock-"
        "module path): it counts attribute-bound and non-placeholder directives as mock "
        "arguments. The P2P TestMockDecoration tests assert specific funcarg counts "
        "(e.g. test_getfuncargnames_patching), which would be wrong; it would NOT resolve.",
        "rationale": "rejected by P2: len(kinds) != count_sentinel_directives(ToSeq(kinds)) "
        "whenever any directive is not kind 1 (P3's upper bound Result()<=len(kinds) "
        "alone does not pin the value). partial-domain: correct only on the all-kind-1 "
        "sub-domain.",
    },
    {
        "id": "skip-first-directive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SKIP_FIRST,
        "refinement": "a faithful patch with an off-by-one slice (`patchings[1:]`) would "
        "drop the first @patch directive from the count; a single-mock-arg decorated "
        "test would then report 0 mock args, so pytest would try to inject the mocked "
        "argument as a fixture and the test would ERROR — it would NOT resolve.",
        "rationale": "rejected by P2: stopping the loop at i==1 (skipping index 0) "
        "computes count_sentinel_directives(ToSeq(kinds).drop(1)) != the full fold "
        "whenever kinds[0] is kind 1. partial-domain: the boundary (first) element.",
    },
]


# === AXIOM LANE ===========================================================
# meta.json axioms == []: there is NO consumed @ContractOnly axiom (the membership
# decision is the CHANGED op, modelled DEEPLY — directive 7 / SPEC_GUIDE §3). But
# there IS an A-reference deep model (counts_as_mock / count_sentinel_directives),
# which the plan (§4 "A-reference deep models are checked the same way") and G-AX
# require to equal the real runtime identity semantics. The probe below reuses the
# bundle's axiom_check.py logic (self-contained; imports ONLY unittest.mock +
# random from the stdlib — unittest.mock IS the module the patched code consults
# for its placeholder singleton DEFAULT) so it runs in the instance image:
#   axiom-soundness: assert the IDENTITY decision (kind tag) is TOTAL + exact on
#     the real unittest.mock.DEFAULT (never raises, even on a NumPy-like value),
#     that the PRE-PATCH value-equality membership RAISES on the kind-3 value, and
#     that count_sentinel_directives over the kind tags == the real identity count
#     over 7 boundary + 20000 fuzz directive populations, with 0<=count<=len.
# A violation on any caller-reachable directive population would be AXIOM-UNSOUND
# (the deep model would not equal the real identity semantics it abstracts).
_AXIOM_SOUNDNESS_PROBE = r'''
import random, sys
import unittest.mock as um


class Directive:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


class NumpyLike:
    """equality is NON-truth-evaluable (kind 3) — the #5606 reproducer."""
    def __init__(self, value):
        self.value = value
    def __eq__(self, other):
        raise ValueError("like numpy, cannot compare against others for truth")
    __hash__ = None


SENTINELS = [um.DEFAULT]   # the real placeholder singletons the helper consults


# --- model.py deep-model reference encodings (kept in lock-step) -------------
def counts_as_mock(kind):
    return kind == 1


def count_sentinel_directives(kinds):
    return sum(1 for k in kinds if counts_as_mock(k))


# --- the real-semantics classification --------------------------------------
def real_kind(d):
    if d.attribute_name:
        return 0
    is_sentinel = any(d.new is s for s in SENTINELS)   # IDENTITY: total
    if is_sentinel:
        return 1
    try:
        _ = bool(d.new == um.DEFAULT)
        return 2
    except Exception:
        return 3


def real_count_identity(directives):
    n = 0
    for d in directives:
        if not d.attribute_name and any(d.new is s for s in SENTINELS):
            n += 1
    return n


def real_count_equality(directives):
    try:
        n = 0
        for d in directives:
            if not d.attribute_name and (d.new in SENTINELS):
                n += 1
        return n
    except ValueError:
        return "RAISED"


def check_facts():
    # (1) identity is total + exact on the placeholder singleton, never raises
    assert (um.DEFAULT is um.DEFAULT) is True
    assert (NumpyLike(1) is um.DEFAULT) is False
    assert (object() is um.DEFAULT) is False
    nl = NumpyLike(50)
    assert (nl is um.DEFAULT) is False        # must NOT raise (identity is total)
    # (2) value-equality membership RAISES on the kind-3 value (the pre-patch op)
    raised = False
    try:
        _ = nl in SENTINELS
    except ValueError:
        raised = True
    assert raised, "expected value-equality membership to raise on NumpyLike"


def check_population(directives):
    kinds = [real_kind(d) for d in directives]
    model_n = count_sentinel_directives(kinds)
    real_n = real_count_identity(directives)
    assert model_n == real_n, (
        "deep model count %d != real identity count %d on %r"
        % (model_n, real_n, kinds))
    assert 0 <= model_n <= len(directives)
    if any(k == 3 for k in kinds):
        assert real_count_equality(directives) == "RAISED", (
            "expected pre-patch equality count to RAISE on a kind-3 population")
    else:
        assert real_count_equality(directives) == real_n


def sample_value(rng):
    r = rng.random()
    if r < 0.30:
        return um.DEFAULT
    if r < 0.60:
        return NumpyLike(rng.randint(0, 100))
    if r < 0.80:
        return object()
    return rng.choice([0, 1, "x", (1, 2), None, 3.5])


def main():
    check_facts()
    boundary = [
        [],
        [Directive(None, um.DEFAULT)],
        [Directive("name", um.DEFAULT)],
        [Directive(None, NumpyLike(50))],
        [Directive(None, object())],
        [Directive(None, um.DEFAULT), Directive(None, NumpyLike(1))],
        [Directive("a", um.DEFAULT), Directive(None, um.DEFAULT),
         Directive(None, NumpyLike(2)), Directive(None, 5)],
    ]
    for pop in boundary:
        check_population(pop)
    rng = random.Random(5631)
    for _ in range(20000):
        n = rng.randint(0, 8)
        pop = []
        for _ in range(n):
            attr = None if rng.random() < 0.7 else "attr%d" % rng.randint(0, 3)
            pop.append(Directive(attr, sample_value(rng)))
        check_population(pop)
    print("AXIOM-SOUND OK: identity decision total + exact on the real "
          "unittest.mock.DEFAULT; value-equality membership raises on the "
          "NumPy-like value; deep-model count == real identity count over "
          "%d boundary + 20000 fuzz populations." % len(boundary))
    sys.exit(0)


try:
    main()
except AssertionError as e:
    print("AXIOM-UNSOUND:", e)
    sys.exit(1)
'''


AXIOM_TESTS = [
    {
        "id": "ax-deepmodel-identity-soundness",
        "axiom": "counts_as_mock / count_sentinel_directives (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_SOUNDNESS_PROBE,
        "rationale": "A-reference deep model: the identity classifier counts_as_mock "
        "(kind==1) and its fold must equal the REAL runtime identity decision "
        "`p.new is <unittest.mock.DEFAULT>`. The probe runs the real callee semantics "
        "in-container — asserts identity is TOTAL+exact (never raises, even on the "
        "NumpyLike #5606 value), the PRE-PATCH value-equality membership RAISES on the "
        "kind-3 value, and the deep-model count == the real identity count over 7 "
        "boundary + 20000 fuzz directive populations. A disagreement => AXIOM-UNSOUND. "
        "No containment case: the kind domain {0,1,2,3} is exactly the set the model "
        "reaches (Requires) and the real_kind classifier covers all four, so every "
        "caller-reachable directive lies in the deep model's domain (see 'assessment').",
    },
]
