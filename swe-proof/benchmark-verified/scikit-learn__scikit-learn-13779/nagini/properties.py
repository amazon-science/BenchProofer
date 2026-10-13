"""PBT falsification battery for scikit-learn__scikit-learn-13779.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap on the whole gold block,
which mechanically GUARANTEES same_spec) and are checked by Nagini verify. The
axiom lane probes the single A-consumed @ContractOnly axiom `accepts_weighting`
(modelling the real `sklearn.utils.validation.has_fit_parameter`) in the
instance Docker image.

Defended surface (check_weighting_support(roster: List[int]) -> None)
---------------------------------------------------------------------
Models the gold one-hunk fix to `_BaseVoting.fit`'s weighted-fit pre-check
(sklearn/ensemble/voting.py:79-83): insert `if step is None: continue` BEFORE the
`has_fit_parameter` probe, so an absent (None) sub-estimator is SKIPPED and never
passed to the probe (which would raise `AttributeError: 'NoneType' object has no
attribute 'fit'` -- the bug).

Carrier: roster: List[int] of per-entry status tags -- 0 = ABSENT (step is None),
1 = PRESENT-and-accepts-weighting, 2 = PRESENT-and-rejects-weighting.

Preconditions (frozen):
  (R1) Acc(list_pred(roster), 1/2)  -- READ-ONLY input: only HALF permission, so
       a rival cannot WRITE the roster to satisfy a postcondition vacuously.
  (R2) Forall k in [0,len): 0 <= roster[k] <= 2  -- every entry is a valid tag.

Postconditions (frozen, load-bearing clauses):
  (P1) Ensures(Acc(list_pred(roster), 1/2))  -- the half-permission is RETURNED
       (read-only framing on the normal path).
  (P2) Ensures(config_supports(ToSeq(roster)))  -- returns NORMALLY exactly when
       every PRESENT entry accepts weighting. config_supports is a @Pure
       front-recursive fold `roster[0] != 2 and config_supports(roster.drop(1))`
       -- fully GROUNDED in the input roster (a total function of roster), NOT an
       opaque answer-key; there is no "wrong echo" to exploit (see assessment).
  (P3) Exsures(WeightingUnsupported, Acc(list_pred(roster),1/2)
                                     and not config_supports(ToSeq(roster)))
       -- REJECTS (raises) exactly when some PRESENT entry rejects weighting, and
       the half-permission is returned on the exceptional path too.

The single A-consumed axiom (frozen):
  accepts_weighting(status): Requires(status==1 or status==2);
                             Ensures(Result() == (status==1)).
  The load-bearing precondition `status in {1,2}` -- the probe is meaningful ONLY
  for a PRESENT entry; consulting it on a status-0 (absent) entry is OUT OF
  CONTRACT (the real has_fit_parameter dereferences None.fit and RAISES). This is
  the exact formal face of the bug; the pre-patch impl violates it.

Weakness-class coverage for THIS instance
------------------------------------------
* FRAME-MUTATION (MANDATORY -- has_readonly_input == True): roster is a heap list
  held at HALF permission (Acc(list_pred(roster),1/2)) in R1/P1/P3. The rival
  `weak-frame-mutation` WRITES roster[i-1] = 1 to clear every present-rejecting
  entry, making config_supports(ToSeq(roster)) trivially true on the mutated
  list. It MUST be rejected for INSUFFICIENT PERMISSION (a write needs full
  list_pred(roster), the caller only granted 1/2). The gold invariants/asserts
  are kept verbatim so the rejection is attributable to the write alone.
* UNGROUNDED-ORACLE ECHO: NO wrong echo exists. P2/P3 ground the outcome in the
  @Pure fold config_supports(ToSeq(roster)), which fully unfolds to a function of
  roster -- it is not an opaque oracle the impl could echo without doing the
  work. Covered instead by the honest cheapest-/structural-variant positive
  controls (pos-nest-branch, pos-explicit-status) -- see assessment.
* PARTIAL-DOMAIN: weak-skip-first (scan stops one short, wrong iff roster[0]==2)
  and weak-treat2-as-accept (correct unless a present-rejecting entry exists).
* CONTROL-FLOW-EFFECT: the sole observable beyond the value abstraction is
  return-normally vs raise-WeightingUnsupported. weak-never-raise (always returns
  normally) and weak-always-raise (always raises) attack exactly that axis.
* PROBE-ON-ABSENT (the prepatch bug / out-of-contract callee): weak-prepatch
  consults accepts_weighting on EVERY entry incl. status 0, violating the axiom
  precondition -- the discriminating change.
* POSITIVE CONTROL + ADMISSIBILITY: present below. Positive controls KEEP the
  back-to-front scan and ALL gold invariants/framing-asserts (pitfall #2/#3): a
  forward-append against the front-recursive config_supports would need an
  f(a+b) lemma the verifier won't auto-discharge, so only the branch shape is
  reshaped, never the loop direction.

Every variant is built by _swap on _BASE, editing ONLY inside
# impl-start / # impl-end -- the frozen spec (axioms/pure/pre/post-conditions) is
never touched, so same_spec holds by construction.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13779"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl body, VERBATIM from model.py, strictly between (and including)
# the marker lines. Swapping this whole block edits ONLY the free region, so the
# frozen spec (and same_spec) is guaranteed untouched.
_GOLD = '''    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `config_supports` (one unfold per
    # step). An absent entry (0) is skipped — the probe is never consulted on it,
    # honouring its precondition. A present entry (1 or 2) is consulted via the
    # probe; `supported` folds whether every present entry seen so far accepts.
    # The single rejection is raised once, at the end, when `supported` is false
    # (observationally identical to raising on the first present-rejecting entry;
    # refinement.md justifies the short-circuit equivalence).
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        # `supported` tracks support over the suffix already scanned.
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            # absent entry: skip, never consult the probe on it
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''

assert _GOLD in _BASE and _BASE.count(_GOLD) == 1, "gold impl block drift"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): NEST the absent-guard instead of using elif.
# `if status == 0: skip ... elif not accepts_weighting(status): ...` becomes
# `if status != 0: (if not accepts_weighting(status): supported = False)`.
# Logically identical: the probe is consulted exactly for present entries
# (status != 0, and by R2 that means status in {1,2}, establishing the axiom
# precondition). Back-to-front scan, ALL invariants and BOTH framing asserts kept
# verbatim. Still CONSUMES the accepts_weighting axiom. MUST verify; else
# SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_NEST = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status != 0:
            # present entry: consult the probe (status in {1,2} by R2)
            if not accepts_weighting(status):
                supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): decide support by the STATUS TAG directly --
# `elif status == 2: supported = False`. Since the axiom gives
# accepts_weighting(status) == (status == 1), for a present entry
# `not accepts_weighting(status)` is exactly `status == 2`, which is also the
# `roster[0] != 2` condition config_supports folds over -- so the loop invariant
# `supported == config_supports(...)` is preserved. A structurally-different
# CORRECT impl that does NOT call the probe (the value abstraction does not
# REQUIRE the axiom to be consumed -- config_supports is the ground truth). Back-
# to-front scan + all invariants/asserts kept. MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_EXPLICIT = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 2:
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold loop, but FIRST assert (at impl entry) that the
# precondition is establishable for a normal F2P-shaped input -- the roster is a
# valid tag list (R2) -- and that config_supports is well-defined on the empty
# suffix (the loop's base case). If a legitimate input could not establish the
# Requires this would fail => PRECOND-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS = '''    # impl-start
    # The precondition admits a normal roster: every entry is a valid status tag.
    Assert(Forall(int, lambda k:
                  (Implies(0 <= k and k < len(roster),
                           0 <= roster[k] and roster[k] <= 2),
                   [[roster[k]]])))
    # The empty-suffix base case of the fold is True (vacuously supported).
    Assert(config_supports(ToSeq(roster).drop(len(roster))))
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


# ---------------------------------------------------------------------------
# UNIQUENESS / reject rivals (each MUST be rejected by a contract clause).
# ---------------------------------------------------------------------------

# (FRAME-MUTATION) Overwrite the read-only roster: clear every present-rejecting
# entry to 1 (present-accepts) BEFORE folding, so config_supports(ToSeq(roster))
# becomes trivially true and the impl returns normally. It only holds
# Acc(list_pred(roster),1/2), so the WRITE `roster[i-1] = 1` is rejected for
# INSUFFICIENT PERMISSION. Gold invariants/asserts kept verbatim so the rejection
# is attributable to the write.
_W_FRAME = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 2:
            roster[i - 1] = 1
        i = i - 1
    return
    # impl-end'''


# (PROBE-ON-ABSENT / prepatch bug) Drop the absent-entry skip: consult
# accepts_weighting(status) on EVERY entry, including status 0. This is exactly
# model_prepatch.py. It is rejected because the axiom precondition status in {1,2}
# is unprovable at a status-0 entry -- the formal face of the AttributeError.
_W_PREPATCH = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


# (CONTROL-FLOW-EFFECT) NEVER raise: drop the rejection entirely, always return
# normally. On a roster with a present-rejecting (status 2) entry,
# config_supports(ToSeq(roster)) is false, but the impl returns normally claiming
# support -- rejected by the normal-path postcondition P2.
_W_NEVER_RAISE = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    return
    # impl-end'''


# (CONTROL-FLOW-EFFECT) ALWAYS raise: raise WeightingUnsupported unconditionally.
# On an all-supported roster (every entry 0 or 1), config_supports is true, so
# the Exsures requirement `not config_supports(ToSeq(roster))` cannot hold --
# rejected by the exceptional-path postcondition P3.
_W_ALWAYS_RAISE = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    raise WeightingUnsupported()
    # impl-end'''


# (PARTIAL-DOMAIN) SKIP-FIRST: stop the scan one short (`while i > 1`), so the
# leading entry roster[0] is never inspected. Correct on every roster whose first
# entry is not present-rejecting, but WRONG when roster[0] == 2 (returns normally
# though config_supports(ToSeq(roster)) is false). The final invariant
# `supported == config_supports(ToSeq(roster).drop(i))` cannot be established at
# loop exit (i == 1, not 0), so P2 fails. Rejected.
_W_SKIP_FIRST = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(1 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            supported = supported
        elif not accepts_weighting(status):
            supported = False
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


# (PARTIAL-DOMAIN / value-mask) TREAT-2-AS-ACCEPT: never mark a present-rejecting
# entry as unsupported (treat status 2 like status 1). Correct on every roster
# with no present-rejecting entry, but WRONG when a status-2 entry exists
# (returns normally though config_supports is false). The invariant
# `supported == config_supports(ToSeq(roster).drop(i))` breaks at the first
# status-2 step, so P2 fails. Rejected.
_W_TREAT2 = '''    # impl-start
    supported = True  # type: bool
    i = len(roster)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(roster), 1 / 2))
        Invariant(0 <= i and i <= len(roster))
        Invariant(Forall(int, lambda k:
                        (Implies(0 <= k and k < len(roster),
                                 0 <= roster[k] and roster[k] <= 2),
                         [[roster[k]]])))
        Invariant(supported == config_supports(ToSeq(roster).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(roster).drop(i - 1)[0] == roster[i - 1])
        Assert(ToSeq(roster).drop(i - 1).drop(1) == ToSeq(roster).drop(i))
        status = roster[i - 1]
        if status == 0:
            supported = supported
        elif accepts_weighting(status):
            supported = supported
        i = i - 1
    if not supported:
        raise WeightingUnsupported()
    return
    # impl-end'''


SPEC_TESTS = [
    {
        "id": "pos-nest-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_NEST),
        "rationale": "structurally-different CORRECT impl: nest the absent-guard "
        "(`if status != 0: if not accepts_weighting(status): supported=False`) "
        "instead of the gold `if status==0 ... elif ...`. Logically identical -- "
        "the probe is consulted exactly for present entries (status != 0, which by "
        "R2 means status in {1,2}, establishing the axiom precondition), and the "
        "loop invariant supported == config_supports(ToSeq(roster).drop(i)) is "
        "preserved. Back-to-front scan + all invariants/framing-asserts kept "
        "verbatim (pitfall #2/#3). Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-explicit-status",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_EXPLICIT),
        "rationale": "structurally-different CORRECT impl deciding support by the "
        "status tag directly (`elif status == 2: supported=False`), NOT via the "
        "probe. Since the axiom gives accepts_weighting(status)==(status==1), for a "
        "present entry `not accepts_weighting(status)` IS `status==2`, which is the "
        "same `roster[0] != 2` config_supports folds over, so the invariant holds. "
        "Demonstrates the value abstraction does not REQUIRE consuming the axiom -- "
        "config_supports is the ground truth. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-precond-nonvacuous",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "the precondition is non-vacuous for a normal F2P-shaped "
        "roster: every entry is a valid status tag (R2) and the empty-suffix base "
        "case of config_supports is true. The F2P test_none_estimator_with_weights "
        "fits a 2-estimator voter with one set to None (one status-0 entry, one "
        "status-1) and sample_weight set -- a roster like [0,1] is admitted. Must "
        "verify; else PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_FRAME),
        "refinement": "its faithful real patch would MUTATE self.estimators in "
        "place during the pre-check -- e.g. rewrite each weight-rejecting "
        "sub-estimator into a weight-accepting clone so the configuration appears "
        "to support weights. That silently corrupts the user's ensemble (the "
        "subsequent parallel clone/fit would train the wrong estimators), so the "
        "P2P tests that assert the configured estimators are fit unchanged "
        "(test_estimator_init, test_set_estimator_none, the predict/transform "
        "tests) FAIL. A verifying rival would be a true verify-not-resolve break.",
        "rationale": "rejected by the PERMISSION SYSTEM: roster is held at "
        "Acc(list_pred(roster),1/2) (R1) only, so the write `roster[i-1] = 1` "
        "requires full permission the impl does not have -- INSUFFICIENT "
        "PERMISSION. Not a value-postcondition failure; the read-only frame "
        "condition is what forbids satisfying P2 by overwriting the input.",
    },
    {
        "id": "weak-prepatch-probe-on-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_PREPATCH),
        "refinement": "this IS the pre-patch bug (model_prepatch.py, G-DIFF): drop "
        "the `if step is None: continue` guard and call has_fit_parameter(step, "
        "'sample_weight') on EVERY entry, including a None (absent) one. The real "
        "has_fit_parameter dereferences None.fit and raises `AttributeError: "
        "'NoneType' object has no attribute 'fit'` -- exactly the crash in the "
        "issue. The F2P test_none_estimator_with_weights (fit a voter after "
        "set_params(lr=None) with sample_weight) FAILS. A verifying rival would be "
        "a true verify-not-resolve break.",
        "rationale": "rejected by the AXIOM PRECONDITION of accepts_weighting "
        "(status == 1 or status == 2): consulting it on a status-0 entry is "
        "unprovable (the call site cannot establish status in {1,2} for an absent "
        "entry). This is the formal face of the AttributeError; the absent-entry "
        "skip in the gold impl is what discharges it.",
    },
    {
        "id": "weak-never-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_NEVER_RAISE),
        "refinement": "its faithful real patch deletes the `raise ValueError(...)` "
        "so the pre-check never rejects an unsupported configuration -- a "
        "weight-rejecting present estimator (e.g. KNeighborsClassifier) is silently "
        "accepted and then crashes (or silently ignores the weights) deep in the "
        "parallel fit. The P2P tests asserting the pre-check raises on a "
        "non-supporting estimator (the sample-weight-support guard tests) FAIL. A "
        "verify-not-resolve break.",
        "rationale": "rejected by the normal-path postcondition P2 "
        "Ensures(config_supports(ToSeq(roster))): on a roster with a status-2 entry "
        "config_supports is false, but this impl returns normally, so "
        "config_supports(ToSeq(roster)) cannot be proven at the return.",
    },
    {
        "id": "weak-always-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_ALWAYS_RAISE),
        "refinement": "its faithful real patch raises ValueError unconditionally in "
        "the pre-check, rejecting EVERY weighted fit even when every present "
        "estimator accepts weights. The F2P test_none_estimator_with_weights (which "
        "fits successfully after skipping the None entry) and the normal weighted "
        "voting P2P tests FAIL. A verify-not-resolve break.",
        "rationale": "rejected by the exceptional-path postcondition P3 "
        "Exsures(WeightingUnsupported, ... and not config_supports(ToSeq(roster))): "
        "on an all-supported roster (entries in {0,1}) config_supports is true, so "
        "the required `not config_supports(ToSeq(roster))` cannot hold when raising.",
    },
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_SKIP_FIRST),
        "refinement": "partial-domain / off-by-one: its faithful real patch stops "
        "the loop one estimator short (never checks the FIRST estimator in "
        "self.estimators). It is correct unless the first estimator is a present "
        "weight-rejecting one, in which case the unsupported configuration is "
        "accepted and the fit later crashes. The P2P sample-weight-support guard "
        "test with a weight-rejecting first estimator FAILS. A verify-not-resolve "
        "break on the first-element sub-domain.",
        "rationale": "rejected by the normal-path postcondition P2: at loop exit "
        "i == 1 (not 0), so supported tracks config_supports(ToSeq(roster).drop(1)) "
        "-- the leading entry roster[0] is unaccounted for, and "
        "config_supports(ToSeq(roster)) cannot be established (it differs from the "
        "drop(1) fold exactly when roster[0] == 2).",
    },
    {
        "id": "weak-treat2-as-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_TREAT2),
        "refinement": "partial-domain: its faithful real patch inverts the probe "
        "test (only marks unsupported when has_fit_parameter is TRUE), so a "
        "weight-rejecting present estimator is treated as supported. The "
        "configuration is accepted though it cannot honour the weights; the P2P "
        "guard tests for a weight-rejecting estimator FAIL. A verify-not-resolve "
        "break on the present-rejecting sub-domain.",
        "rationale": "rejected by the normal-path postcondition P2: never setting "
        "supported = False on a status-2 entry breaks the invariant "
        "supported == config_supports(ToSeq(roster).drop(i)) at the first "
        "status-2 step, so config_supports(ToSeq(roster)) cannot be proven at the "
        "return.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: ONE A-consumed @ContractOnly axiom, accepts_weighting, modelling the
# real sklearn.utils.validation.has_fit_parameter(estimator, 'sample_weight') --
# the UNCHANGED callee the gold patch's surrounding code invokes
# (sklearn/ensemble/voting.py:81). No deep-model (A-reference) references. We
# re-derive axiom_check.py's validation as in-Docker probes against the real
# callee + real sklearn estimators (present in the instance image).
#
# axiom-soundness (accepts_weighting): the real has_fit_parameter must agree with
#   Ensures(Result() == (status == 1)) on every PRESENT estimator -- True (status
#   1) for an estimator whose fit declares sample_weight, False (status 2) for one
#   that does not -- AND must RAISE on an absent entry (None), which is what makes
#   the precondition status in {1,2} a FAITHFUL restriction (the bug the fix
#   avoids), not an over-restriction. has_fit_parameter has NO flag/config
#   dependency (it inspects the fit signature alone -- meta.json provenance).
#
# axiom-containment: the caller (check_weighting_support / the real pre-check)
#   reaches the probe ONLY on PRESENT entries -- the status-0 skip / `if step is
#   None: continue` guard means accepts_weighting is invoked exactly when status
#   in {1,2}, i.e. exactly the axiom's Requires domain. We assert that every
#   estimator the caller can reach the probe with is a real, present (non-None)
#   estimator on which has_fit_parameter is well-defined (returns a bool, does not
#   raise), and that the ONLY input the model can produce OUTSIDE {1,2} (status 0)
#   is precisely the one the guard removes before the call -- so no
#   caller-reachable probe input lies outside the axiom domain (not
#   AXIOM-TOO-WEAK-FOR-CALLER).
# ---------------------------------------------------------------------------

_PROBE_SOUNDNESS = r'''
import random
import sys

from sklearn.utils.validation import has_fit_parameter   # the REAL probe

# status-1 estimators: real sklearn estimators whose fit DECLARES sample_weight.
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
# status-2 estimator: real sklearn estimator whose fit does NOT declare it.
from sklearn.neighbors import KNeighborsClassifier


class _NoWeight(object):
    def fit(self, X, y):
        return self


class _Weight(object):
    def fit(self, X, y, sample_weight=None):
        return self


def assert_bool_eq(est, expected):
    observed = has_fit_parameter(est, 'sample_weight')   # REAL probe
    if not isinstance(observed, bool):
        print("FAIL: real has_fit_parameter returned non-bool %r on %s"
              % (observed, type(est).__name__))
        sys.exit(1)
    if observed != expected:
        print("FAIL: accepts_weighting UNSOUND on %s: real probe gave %r, "
              "axiom Ensures requires %r (status %d)"
              % (type(est).__name__, observed, expected, 1 if expected else 2))
        sys.exit(1)


# status 1 (present-accepts): probe must return True == (status == 1).
accepts = [
    LogisticRegression(), LinearRegression(),
    RandomForestClassifier(n_estimators=2), RandomForestRegressor(n_estimators=2),
    DecisionTreeClassifier(), DecisionTreeRegressor(),
    SVC(), GaussianNB(), _Weight(),
]
for est in accepts:
    assert_bool_eq(est, True)

# status 2 (present-rejects): probe must return False == (status == 1 is False).
rejects = [KNeighborsClassifier(), _NoWeight()]
for est in rejects:
    assert_bool_eq(est, False)

# status 0 (absent): OUTSIDE the precondition. Soundness of the exclusion: the
# REAL probe RAISES on None (None.fit -> AttributeError). If it did NOT raise,
# status 0 would be admissible and the precondition status in {1,2} would be an
# over-restriction. Confirm it raises.
raised = False
try:
    has_fit_parameter(None, 'sample_weight')   # REAL probe on an absent entry
except Exception:
    raised = True
if not raised:
    print("FAIL: real has_fit_parameter(None, 'sample_weight') did NOT raise; "
          "status 0 would be admissible and the precondition over-restrictive")
    sys.exit(1)

# fuzz: synthesized present estimators with / without a sample_weight kwarg.
rng = random.Random(13779)
for _ in range(2000):
    if rng.random() < 0.5:
        assert_bool_eq(_Weight(), True)
    else:
        assert_bool_eq(_NoWeight(), False)

print("AX-SOUND OK: real has_fit_parameter == (status==1) on %d present-accepts "
      "+ %d present-rejects estimators + 2000 fuzz, and RAISES on an absent entry "
      "(None) -- the precondition status in {1,2} is a faithful restriction."
      % (len(accepts), len(rejects)))
sys.exit(0)
'''


_PROBE_CONTAINMENT = r'''
import sys

from sklearn.utils.validation import has_fit_parameter   # the REAL probe
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


class _NoWeight(object):
    def fit(self, X, y):
        return self


# Containment: in the real pre-check the probe is reached ONLY for a PRESENT
# estimator -- the `if step is None: continue` guard (model status-0 skip) removes
# the only out-of-domain input (status 0, an absent/None entry) BEFORE the call.
# So the caller-reachable probe inputs are exactly present estimators, i.e. exactly
# the axiom's Requires domain status in {1,2}. Verify both halves:
#  (a) every present estimator the caller can pass is a well-defined probe input
#      (returns a bool, does not raise) -- it lies INSIDE the axiom domain;
#  (b) the ONLY input the model could otherwise produce outside {1,2} is status 0
#      (None), which the guard removes -- and that input is precisely the one the
#      real probe cannot handle (it raises). There is no OTHER reachable input
#      outside {1,2} (the roster tags are constrained to {0,1,2} by R2, and 0 is
#      guarded), so the axiom is not AXIOM-TOO-WEAK-FOR-CALLER.
present = [
    LogisticRegression(), LinearRegression(),
    RandomForestClassifier(n_estimators=2), RandomForestRegressor(n_estimators=2),
    _NoWeight(),
]
for est in present:
    try:
        observed = has_fit_parameter(est, 'sample_weight')
    except Exception as exc:
        print("FAIL: a caller-reachable PRESENT estimator %s is outside the probe "
              "domain (raised %r) -- AXIOM-TOO-WEAK-FOR-CALLER"
              % (type(est).__name__, exc))
        sys.exit(1)
    if not isinstance(observed, bool):
        print("FAIL: probe non-bool on present estimator %s" % type(est).__name__)
        sys.exit(1)

# The single out-of-domain input the model could form is status 0 (None). Confirm
# it is exactly what the guard removes (the probe genuinely cannot handle it), so
# excluding it from the axiom domain is the correct containment, not a gap.
removed_input_unhandlable = False
try:
    has_fit_parameter(None, 'sample_weight')
except Exception:
    removed_input_unhandlable = True
if not removed_input_unhandlable:
    print("FAIL: the guarded status-0 input (None) IS handlable by the probe, so "
          "the absent-entry skip would be removing an in-domain input")
    sys.exit(1)

print("AX-CONTAIN OK: every caller-reachable probe input is a PRESENT estimator "
      "(status in {1,2}, in the axiom domain, probe well-defined); the only "
      "out-of-domain input the model could form (status 0 / None) is exactly the "
      "one the absent-entry guard removes and the real probe cannot handle. No "
      "caller-reachable input lies outside the axiom domain.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-accepts-weighting",
        "axiom": "accepts_weighting",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "the A-consumed accepts_weighting axiom must agree with the "
        "REAL has_fit_parameter: Ensures(Result()==(status==1)) holds -- True for "
        "every present estimator whose fit declares sample_weight (status 1), False "
        "for one that does not (status 2) -- on real sklearn estimators + 2000 "
        "fuzz; and the real probe RAISES on an absent entry (None), so the "
        "precondition status in {1,2} is a faithful restriction (the exact bug the "
        "fix avoids), not an over-restriction. If the real probe disagreed or did "
        "not raise on None, the axiom would be AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-present-only",
        "axiom": "accepts_weighting",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "containment: the caller reaches the probe ONLY for present "
        "entries -- the absent-entry skip (`if step is None: continue` / the model "
        "status-0 branch) removes the only input outside the axiom domain (status 0 "
        "/ None) BEFORE the call. Every caller-reachable probe input is a present "
        "estimator (status in {1,2}, in the axiom's Requires domain, probe "
        "well-defined), and the single removed input is exactly the one the real "
        "probe cannot handle. No caller-reachable input lies outside the axiom "
        "domain, so it is not AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
