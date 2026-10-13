"""PBT falsification battery for scikit-learn__scikit-learn-25232.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants (frozen spec, swapped impl region) checked by Nagini verify +
markers.same_spec; the axiom lane runs the REAL scikit-learn callee in Docker.

Defended surface  (initial_constant_fill : (Optional[int], int) -> List[int])
-----------------------------------------------------------------------------
Models IterativeImputer's first-round constant initialization: it must install,
for every feature, the user-requested replacement value `fill_value` (carried
through to the inner single-pass SimpleImputer), default-resolved to the neutral
numeric 0 when None. The FAIL_TO_PASS observes exactly this:
  IterativeImputer(initial_strategy="constant", fill_value=100, max_iter=0)
  ...; assert_array_equal(imputer.initial_imputer_.statistics_, 100)

Preconditions:
  * Requires(n_features >= 0)
  -> Both formal parameters are SCALARS PASSED BY VALUE: `requested: Optional[int]`
     and `n_features: int`. There is NO list/object input, hence NO read-only
     Acc(.,1/2) INPUT parameter anywhere in the Requires. The frame-mutation
     weakness class (overwrite a half-permission read-only input to satisfy a
     postcondition vacuously) therefore DOES NOT APPLY to this spec — there is no
     aliased input the impl could write back through to cheat. has_readonly_input
     == False; frame_mutation_included == False (documented in 'assessment').
     The only Acc() in the spec is `Acc(list_pred(Result()))` — a permission on
     the FRESH output list the function produces, not on any input.

Postconditions (load-bearing clauses), all over the fresh Result():
  (1) Acc(list_pred(Result()))                                  -- owns the list
  (2) len(Result()) == n_features                               -- one per feature
  (3) Forall j in [0,n_features): Result()[j] == resolved_value(requested)
      -- THE discriminating clause: every installed per-feature constant equals
         the (default-resolved) requested value. This is what the F2P observes
         (statistics_ == 100 for fill_value=100) and exactly what the pre-patch
         omission violated (it dropped `requested`, so every entry was 0).
         resolved_value(None) == 0 ; resolved_value(v) == v.

Oracle grounding: `resolved_value` is @Pure and FULLY GROUNDED in the input
argument (`requested`) — it is `0 if requested is None else requested`, an
unfoldable function of the arg, NOT an opaque answer-key the impl could echo
without doing the work. So there is no "wrong echo" rival (a UNGROUNDED-ORACLE
break is impossible here). UNGROUNDED-ORACLE is instead covered by an honest
cheapest-/structurally-different-correct positive control (must verify). See
'assessment'.

Axiom: `constant_statistics` is the @ContractOnly A-consumed axiom for the
UNCHANGED single-pass SimpleImputer(strategy="constant"); its Ensures equals the
postcondition. The impl satisfies (1)-(3) by calling it with `requested` (gold);
the pre-patch dropped it to `None`. The axiom lane checks (a) the real callee is
sound on every input in the axiom Requires domain under the caller's config, and
(b) every callee-input the model can reach lies in the axiom Requires domain.

Construction: every spec variant is built by _swap on _BASE, editing ONLY the
text inside # impl-start / # impl-end. The frozen spec (axioms/pure/pre/
post-conditions) is never touched, which mechanically GUARANTEES same_spec.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25232"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl block, verbatim from model.py (everything strictly inside the
# # impl-start / # impl-end markers). Swapping this whole block edits ONLY the
# free region.
_GOLD = '''    # The user's requested replacement value is carried through to the
    # underlying single-pass imputer.
    statistics = constant_statistics(requested, n_features)
    return statistics'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): build the per-feature constant array with an
# explicit FORWARD-APPEND loop, appending resolved_value(requested) n_features
# times, instead of the single axiom call. Structurally very different from the
# gold (no call to constant_statistics at all). resolved_value(requested) is a
# loop-INVARIANT constant (not a fold over the index), so forward-append needs
# NO f(a+b)==f(a)+f(b) lemma — the standard len(result)==i + per-prefix pin
# invariants discharge the postcondition. Keeps every obligation it needs. MUST
# verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_LOOP = '''    result = []  # type: List[int]
    i = 0
    while i < n_features:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_features)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == resolved_value(requested)))))
        Invariant(MustTerminate(n_features - i + 1))
        # invariants-end
        result.append(resolved_value(requested))
        i = i + 1
    return result'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): a local-variable reshape — bind the requested
# value through an intermediate local (carrying it unchanged) before the axiom
# call, and return through a second local. Same computation, different shape.
# MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_RESHAPE = '''    carried = requested
    filled = constant_statistics(carried, n_features)
    out = filled
    return out'''


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold impl, but assert at entry that the precondition is
# establishable / non-vacuous for a normal F2P-shaped input (the F2P fits a
# 4-feature array, so n_features >= 0 holds, and the requested value is readable).
# If a legitimate input could not establish the Requires this would fail =>
# PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS = '''    Assert(n_features >= 0)
    Assert(resolved_value(requested) == resolved_value(requested))
''' + _GOLD


# ---------------------------------------------------------------------------
# UNIQUENESS / partial-domain rivals (each MUST be rejected by a postcondition).
# ---------------------------------------------------------------------------

# (a) DEFAULT-ZERO twin: drop `requested` and pass None to the unchanged callee,
#     so every feature gets the neutral default 0 (this is model_prepatch.py /
#     the pre-patch omission verbatim). Verifies internally (the axiom holds for
#     None), but fails postcondition (3) whenever requested != None.
_W_DEFAULT_ZERO = '''    # Pre-patch omission: the requested value is NOT carried through; the inner
    # single-pass imputer sees no value and falls back to the neutral default 0.
    statistics = constant_statistics(None, n_features)
    return statistics'''

# (b) PARTIAL-FIRST: honestly fill via the axiom, then corrupt feature 0 to a
#     fixed wrong constant (0). For requested != 0 (e.g. 100) the first entry is
#     wrong. Fails postcondition (3) at j=0.
_W_PARTIAL_FIRST = '''    statistics = constant_statistics(requested, n_features)
    if n_features > 0:
        statistics[0] = 0
    return statistics'''

# (c) PARTIAL-LAST: same, but corrupt the LAST feature. Fails (3) at j=n-1.
_W_PARTIAL_LAST = '''    statistics = constant_statistics(requested, n_features)
    if n_features > 0:
        statistics[n_features - 1] = 0
    return statistics'''

# (d) WRONG-LENGTH-LONG: fill the right value but ONE TOO MANY features
#     (n_features + 1). Every value is resolved_value(requested) so clause (3)
#     holds, but clause (2) len == n_features fails.
_W_LEN_LONG = '''    statistics = constant_statistics(requested, n_features + 1)
    return statistics'''

# (e) WRONG-LENGTH-EMPTY: return the empty list. Clause (3)'s Forall is vacuous,
#     but clause (2) len == n_features fails for n_features > 0. Isolates the
#     length clause from the value clause. (Typed local, NOT a bare `return []`.)
_W_EMPTY = '''    empty = []  # type: List[int]
    return empty'''


SPEC_TESTS = [
    {
        "id": "pos-explicit-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_LOOP),
        "rationale": "structurally-different CORRECT impl: build the per-feature "
        "constant array with an explicit forward-append loop appending "
        "resolved_value(requested) n_features times, with NO call to the axiom. "
        "resolved_value(requested) is a loop-invariant constant (not an "
        "index-fold), so forward-append needs no f(a+b) lemma; the len(result)==i "
        "and per-prefix-pin invariants discharge clauses (1)-(3). Must verify; "
        "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_RESHAPE),
        "rationale": "correct local-variable reshape: carry `requested` through an "
        "intermediate local unchanged, call the axiom, return through a second "
        "local. Same computation, different shape; keeps the gold proof valid. "
        "Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-nonvacuous",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "the precondition is establishable for a normal F2P-shaped "
        "input: at entry n_features >= 0 holds and resolved_value(requested) is "
        "readable (the requested value is in-domain). Must verify; else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-default-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_DEFAULT_ZERO),
        "refinement": "this is the PRE-PATCH bug verbatim (model_prepatch.py): the "
        "first-round initializer constructs SimpleImputer(strategy='constant') "
        "WITHOUT forwarding fill_value, so the inner imputer defaults to 0 for "
        "numerical data. With the F2P's fill_value=100 the real statistics_ would "
        "be [0,0,0,0], but the test asserts assert_array_equal(statistics_, 100) "
        "-> the F2P FAILS. A verifying rival here would be a true verify-not-"
        "resolve break.",
        "rationale": "rejected by postcondition (3): for requested != None (e.g. "
        "100) Result()[j] == resolved_value(requested) == 100 is violated "
        "(every entry is 0). The verifier must prove (3) for ALL requested, so "
        "passing None fails.",
    },
    {
        "id": "weak-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_PARTIAL_FIRST),
        "refinement": "partial-domain: a faithful patch that special-cases the "
        "first feature (e.g. forces statistics_[0]=0 / skips index 0 when "
        "propagating) leaves statistics_[0]=0 != 100. assert_array_equal compares "
        "EVERY entry, so the F2P FAILS on the first feature. A verify-not-resolve "
        "break.",
        "rationale": "rejected by postcondition (3) at j=0: after the corrupting "
        "write statistics[0]==0, but the spec requires Result()[0]==resolved_value"
        "(requested), which fails when resolved_value(requested) != 0 (e.g. 100).",
    },
    {
        "id": "weak-partial-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_PARTIAL_LAST),
        "refinement": "partial-domain: a faithful patch that drops the LAST "
        "feature (e.g. an off-by-one that stops one column short, leaving the "
        "final statistics_ entry at the default 0) yields statistics_[n-1]=0 != "
        "100. The F2P's array has 4 features and assert_array_equal checks all of "
        "them, so it FAILS on the last. A verify-not-resolve break.",
        "rationale": "rejected by postcondition (3) at j=n_features-1: the "
        "corrupting write sets the last entry to 0, but the spec requires it to "
        "equal resolved_value(requested) (e.g. 100).",
    },
    {
        "id": "weak-len-long",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_LEN_LONG),
        "refinement": "a faithful patch that installs one constant TOO MANY (an "
        "off-by-one over-allocation of the per-feature array) yields statistics_ "
        "of shape (n+1,) while X has n features. The F2P's "
        "assert_array_equal(statistics_, fill_value) and downstream fit_transform "
        "require shape (n_features,); a length-(n+1) array mismatches the data and "
        "FAILS. A verify-not-resolve break against the length clause.",
        "rationale": "rejected by postcondition (2): len(Result()) == n_features "
        "is violated (the array has n_features + 1 entries). Clause (3) holds (all "
        "entries are resolved_value(requested)), isolating the length clause.",
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_EMPTY),
        "refinement": "a faithful patch that returns an empty / unpopulated "
        "statistics_ (shape (0,)) installs no per-feature constant at all; the F2P "
        "reads imputer.initial_imputer_.statistics_ and assert_array_equal against "
        "fill_value=100 FAILS on the empty array (and fit_transform breaks). A "
        "verify-not-resolve break isolating the length clause from the value "
        "clause.",
        "rationale": "rejected by postcondition (2): len(Result()) == n_features "
        "is violated for n_features > 0 (the list is empty). Clause (3)'s Forall "
        "is vacuously true over an empty list, so ONLY clause (2) fails.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — constant_statistics is the @ContractOnly A-consumed axiom for the
# UNCHANGED single-pass SimpleImputer(strategy="constant"). Two obligations:
#   * axiom-soundness: the REAL callee, on every input in the axiom Requires
#     domain (n_features >= 0) under the caller's config, installs per-feature
#     resolved_value(requested) and has length n_features. Fuzz requested values
#     + feature counts + the end-to-end IterativeImputer propagation (the F2P).
#   * axiom-containment: every callee-input the MODEL can reach lies in the axiom
#     Requires domain. The caller's own Requires is n_features >= 0 and `requested`
#     is an unconstrained Optional[int]; the axiom Requires is ALSO n_features >= 0
#     with `requested` unconstrained. Identical domain => containment holds; no
#     caller-reachable input lies outside the axiom domain.
# Both probes import only the public scikit-learn API + numpy (the package under
# test), open nothing, exit 0 iff the obligation holds. apply_gold=True so the
# end-to-end IterativeImputer propagation reflects the patched data flow (the
# unchanged SimpleImputer callee is gold-invariant, so its soundness is unaffected
# either way).
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
import sys

import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer


def resolved_value(requested):
    """model.py resolved_value: supplied value, else neutral default 0."""
    return 0 if requested is None else requested


def check_simpleimputer_constant(requested, n_features):
    """The REAL SimpleImputer(strategy='constant') is the unchanged callee the
    axiom abstracts: assert len(statistics_) == n_features and every entry ==
    resolved_value(requested) — the axiom Ensures, on numerical data."""
    rng = np.random.RandomState(25232)
    X = rng.randint(-5, 5, size=(6, n_features)).astype(float)
    X[0, :] = -1  # sentinel missing so there is something to fill
    kwargs = {"missing_values": -1, "strategy": "constant"}
    if requested is not None:
        kwargs["fill_value"] = requested
    imp = SimpleImputer(**kwargs)
    imp.fit(X)
    stats = imp.statistics_
    expected = resolved_value(requested)
    assert stats.shape[0] == n_features, (
        "AXIOM-UNSOUND len: statistics_ has %d entries, n_features=%d"
        % (stats.shape[0], n_features))
    for j in range(n_features):
        assert stats[j] == expected, (
            "AXIOM-UNSOUND value on requested=%r feature %d: statistics_[j]=%r, "
            "axiom requires %r" % (requested, j, stats[j], expected))


def check_iterative_propagation(requested):
    """End-to-end: IterativeImputer's first-round constant initializer must
    carry the requested value through to the inner callee (the discriminating
    F2P observation: fill_value=100 -> statistics_ == 100, not 0)."""
    X = np.array(
        [[-1, 2, 3, -1], [4, -1, 5, -1], [6, 7, -1, -1], [8, 9, 0, -1]],
        dtype=float,
    )
    kwargs = {"missing_values": -1, "initial_strategy": "constant", "max_iter": 0}
    if requested is not None:
        kwargs["fill_value"] = requested
    imp = IterativeImputer(**kwargs)
    imp.fit_transform(X)
    stats = imp.initial_imputer_.statistics_
    expected = resolved_value(requested)
    for j in range(stats.shape[0]):
        assert stats[j] == expected, (
            "PROPAGATION-UNSOUND on fill_value=%r feature %d: statistics_[j]=%r, "
            "expected %r" % (requested, j, stats[j], expected))


def main():
    # axiom Requires domain: n_features >= 1 here (we run the real callee; the
    # n_features == 0 boundary is exercised by the containment probe, which only
    # asserts domain-membership, since a 0-column array is not a meaningful fit).
    requested_values = [None, 0, 1, -1, 100, -100, 7, 42, 999, -3]
    feature_counts = [1, 2, 3, 4, 8, 16]
    for req in requested_values:
        for n in feature_counts:
            check_simpleimputer_constant(req, n)
    # end-to-end propagation incl. the F2P fill_value=100 case
    for req in [None, 0, 1, 100, -1, 50]:
        check_iterative_propagation(req)
    print("AXIOM-SOUND OK: constant_statistics sound on %d (requested x n) obs; "
          "propagation incl. fill_value=100 sound"
          % (len(requested_values) * len(feature_counts)))
    sys.exit(0)


if __name__ == "__main__":
    main()
'''


_AX_CONTAIN_PROBE = r'''
import sys

import numpy as np
from sklearn.impute import SimpleImputer

# The model's impl calls constant_statistics(requested, n_features) where the
# caller's own Requires is `n_features >= 0` and `requested` is an unconstrained
# Optional[int]. The axiom's Requires is ALSO `n_features >= 0` with `requested`
# unconstrained. Containment: every callee-input the MODEL can reach must lie in
# the axiom Requires domain. Since the two domains are IDENTICAL, containment is
# total — there is no caller-reachable input outside the axiom domain.
#
# We demonstrate this concretely: enumerate representative model-reachable
# inputs (requested across None/0/+-/large; n_features across the >= 0 domain
# incl. the 0 boundary) and assert each satisfies the axiom Requires
# (n_features >= 0). For the non-degenerate ones we additionally RUN the real
# callee to confirm an in-domain input is genuinely accepted and yields a
# length-n_features result (grounding "in domain"). n_features == 0 is asserted
# in-domain by the predicate only (a 0-column fit is degenerate for the real
# callee, but it is still inside the axiom Requires domain, so no caller-reachable
# input escapes coverage).

def resolved_value(requested):
    return 0 if requested is None else requested


def axiom_requires(requested, n_features):
    """The axiom's Requires predicate: n_features >= 0 (requested unconstrained)."""
    return n_features >= 0


def main():
    requested_domain = [None, 0, 1, -1, 100, -100, 7, 42, 999, -3]
    nfeatures_domain = [0, 1, 2, 3, 4, 8, 16]
    for requested in requested_domain:
        for n in nfeatures_domain:
            # every caller-reachable (requested, n_features) is in the axiom domain
            assert axiom_requires(requested, n), (
                "AXIOM-TOO-WEAK-FOR-CALLER: caller-reachable n_features=%d is "
                "OUTSIDE the axiom Requires domain (n_features >= 0)" % n)
            if n >= 1:
                # ground it: the real callee accepts this in-domain input and
                # returns a length-n result.
                rng = np.random.RandomState(25232)
                X = rng.randint(-5, 5, size=(6, n)).astype(float)
                X[0, :] = -1
                kwargs = {"missing_values": -1, "strategy": "constant"}
                if requested is not None:
                    kwargs["fill_value"] = requested
                imp = SimpleImputer(**kwargs)
                imp.fit(X)
                assert imp.statistics_.shape[0] == n, (
                    "in-domain input (requested=%r, n=%d) did not yield a "
                    "length-n result" % (requested, n))
    print("AXIOM-CONTAINED OK: every caller-reachable (requested in %d vals, "
          "n_features in %r) is inside the axiom Requires domain (n_features>=0); "
          "domains are identical." % (len(requested_domain), nfeatures_domain))
    sys.exit(0)


if __name__ == "__main__":
    main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-constant-statistics",
        "axiom": "constant_statistics",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the real SimpleImputer(strategy='constant') installs, for "
        "every feature, resolved_value(requested) with length n_features (axiom "
        "Ensures) across fuzzed requested values x feature counts; and the gold "
        "IterativeImputer carries fill_value through end-to-end (F2P). If the real "
        "callee disagreed => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-constant-statistics",
        "axiom": "constant_statistics",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "the caller's Requires (n_features >= 0, requested any "
        "Optional[int]) equals the axiom Requires (n_features >= 0, requested "
        "unconstrained); every caller-reachable callee-input lies in the axiom "
        "domain. A reachable input outside it => AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
