"""properties.py — PBT falsification manifest for scikit-learn__scikit-learn-13496.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. Three functions are under spec:

    refit_to_size(existing: List[int], target_count: int,
                  requested_reuse: bool) -> List[int]      # the changed dispatch
    reuse_and_extend(existing: List[int], target_count: int) -> List[int]
    rebuild_all(target_count: int) -> List[int]

modeling `IsolationForest.__init__`'s newly-forwarded `warm_start` option (the
gold patch) driving the UNCHANGED `BaseBagging._fit` rebuild-or-extend decision.
The carrier: `self.estimators_` (a list of fitted sub-estimator objects) ->
`List[int]` of `id()` identities; a freshly-built member is the sentinel
`FRESH_MEMBER() == -1`, an already-present member is non-negative (precondition),
so a preserved member is structurally distinguishable from a fresh one.

LOAD-BEARING contract (refit_to_size):

    Requires(Acc(list_pred(existing), 1/2))                    # READ-ONLY existing
    Requires(len(existing) <= target_count)
    Requires(Forall k: 0<=k<len(existing) -> existing[k] >= 0) # non-neg identities
    Ensures (Acc(list_pred(existing), 1/2))                    # returned read-only
    Ensures (len(Result()) == target_count)                    # SIZE pin
    Ensures (Implies(effective_reuse(requested_reuse, len(existing)>0),
                     ToSeq(Result()) == ToSeq(existing)
                                      + fresh_run(target_count-len(existing))))
                                                               # REUSE: prefix-preserve
    Ensures (Implies(not effective_reuse(requested_reuse, len(existing)>0),
                     ToSeq(Result()) == fresh_run(target_count)))   # REBUILD: all fresh

What this spec defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the REUSE-case postcondition
    `ToSeq(Result()) == ToSeq(existing) + fresh_run(target_count-len(existing))`.
    The `ToSeq(existing)` prefix forces `Result()[0] == existing[0]` (a
    non-negative identity), which DIFFERS from a rebuilt roster (all
    `FRESH_MEMBER() == -1`). The F2P test `test_iforest_warm_start` fits 10
    trees with `warm_start=True`, remembers `tree_1 = clf.estimators_[0]`,
    enlarges to 20, fits again, and asserts `len == 20` AND
    `clf.estimators_[0] is tree_1`. Both facts are pinned here: the prefix pins
    `estimators_[0] is tree_1`, the SIZE pin pins `== 20`. `model_prepatch.py`
    (refit_to_size ALWAYS rebuilds, ignoring requested_reuse) reproduces the
    pre-patch behaviour (warm_start dropped at construction -> self.warm_start
    stays False -> every fit rebuilds) and FAILS exactly this prefix conjunct
    (G-DIFF): a rebuilt roster's first element is -1 != existing[0] >= 0.

  * `existing` is held at HALF permission `Acc(list_pred(existing), 1/2)`: it is
    a READ-ONLY input (the roster is read, never mutated, by the keep-prefix
    path). So a frame-mutation / insufficient-permission attack DOES apply and is
    MANDATORY: a rival that WRITES to `existing` to satisfy a postcondition
    vacuously must be rejected for INSUFFICIENT PERMISSION (you need full perm to
    write). This is the project's #1 weakness class and a byte-fuzzer never finds
    it. Both `reuse_and_extend` and `refit_to_size` take `existing` read-only;
    frame-mutation rivals are built against both.

  * The oracle (`fresh_run`, `effective_reuse`, the `ToSeq(existing)` prefix) is
    GROUNDED in the inputs — `fresh_run(n)` is a fully-unfolded function of
    `target_count`/`len(existing)`, `effective_reuse` is a function of the two
    flags, and the preserved prefix is literally `ToSeq(existing)`. There is no
    opaque @Pure answer-key a wrong impl could ECHO without doing the work: to
    satisfy the reuse postcondition you must actually copy the existing prefix
    and append the right number of fresh sentinels. So there is no ungrounded-echo
    rival; the cheapest honest impl (the positive control) still has to build the
    prefix-then-fresh-tail roster. (See `assessment`.)

  * There is no raise / return / side-effect difference invisible to the value
    abstraction: the entire observable behaviour is the returned roster
    `List[int]`, fully captured by ToSeq(Result()) + len(Result()). So the
    control-flow-effect class is N/A here (no capability-token rival needed);
    every behavioural difference shows up in the returned-list value. (See
    `assessment`.)

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside ONE `# impl-start`/`# impl-end` region (this
model has THREE — one per function); the frozen spec (axioms/pure/pre/post) is
NEVER touched, so `markers.same_spec` is guaranteed and a rejection comes from
the POSTCONDITION / the permission system, never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P. This bundle has NO @ContractOnly axiom (the
reuse decision + roster update are modeled DEEPLY: effective_reuse /
reuse_and_extend / rebuild_all / fresh_run), so AXIOM_TESTS is empty; the deep
model is validated == the real IsolationForest by axiom_check.py (G-AX,
A-reference), out of the PBT lane's scope.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13496"
FLOAT_ENCODING = None  # meta.json float_encoding is null (no floats; List[int])

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace the UNIQUE occurrence of an impl-region substring. Assert it is
    found and unique so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(
            f"properties.py: substring not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — each is the WHOLE impl body of one function, strictly
# between that function's # impl-start and # impl-end. Each occurs exactly once.
# ---------------------------------------------------------------------------

# refit_to_size dispatch (lines 200-205 of model.py)
_DISPATCH = """    if requested_reuse and len(existing) > 0:
        return reuse_and_extend(existing, target_count)
    else:
        return rebuild_all(target_count)"""

# reuse_and_extend body (lines 112-139): copy prefix, then append fresh tail.
_REUSE_BODY = """    result = []  # type: List[int]
    j = 0
    while j < len(existing):
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(existing))
        Invariant(len(existing) <= target_count)
        Invariant(len(result) == j)
        Invariant(ToSeq(result) == ToSeq(existing).take(j))
        Invariant(MustTerminate(len(existing) - j + 1))
        # invariants-end
        result.append(existing[j])
        j = j + 1
    Assert(ToSeq(existing).take(len(existing)) == ToSeq(existing))
    Assert(ToSeq(result) == ToSeq(existing))
    while len(result) < target_count:
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(existing) <= len(result) and
                  len(result) <= target_count)
        Invariant(ToSeq(result) ==
                  ToSeq(existing) + fresh_run(len(result) - len(existing)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result) - len(existing)))
        result.append(FRESH_MEMBER())
    return result"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-different but CORRECT refit dispatch: invert the guard and
# swap the branch bodies. `if not (requested_reuse and len(existing) > 0):
# rebuild else reuse`. Identical semantics (De Morgan-equivalent guard, branches
# swapped), a different control-flow source. effective_reuse(requested_reuse,
# len(existing)>0) == requested_reuse and len(existing)>0, so the reuse branch is
# taken on EXACTLY the same inputs. If this fails to verify the postcondition is
# over-fit to one guard polarity => SPEC-TOO-STRONG. Also the cheapest honest
# dispatch (still calls a real roster builder per case; no echoable oracle).
_DISPATCH_INVERTED = """    if not (requested_reuse and len(existing) > 0):
        return rebuild_all(target_count)
    else:
        return reuse_and_extend(existing, target_count)"""
_POS_DISPATCH_INVERTED = _swap(_BASE, _DISPATCH, _DISPATCH_INVERTED)

# (5b) Structurally-different but CORRECT reuse_and_extend: hoist the prefix copy
# into a single-test while loop driven by `len(result) < len(existing)` instead
# of an explicit `j` counter. Same observable roster; the per-element framing
# asserts and the lemma_fresh_snoc bridge (needed by the front-recursive fold)
# are KEPT verbatim, only the loop SHAPE of the prefix copy changes (j-counter ->
# len(result) test). If it fails to verify the spec is over-fit to the j-counter
# loop shape => SPEC-TOO-STRONG. (Does NOT flip loop direction or drop a lemma —
# pilot trap #2/#3 avoided: the back-append fold still has its snoc bridge.)
_REUSE_LENTEST = """    result = []  # type: List[int]
    while len(result) < len(existing):
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= len(result) and len(result) <= len(existing))
        Invariant(len(existing) <= target_count)
        Invariant(ToSeq(result) == ToSeq(existing).take(len(result)))
        Invariant(MustTerminate(len(existing) - len(result) + 1))
        # invariants-end
        result.append(existing[len(result)])
    Assert(ToSeq(existing).take(len(existing)) == ToSeq(existing))
    Assert(ToSeq(result) == ToSeq(existing))
    while len(result) < target_count:
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(existing) <= len(result) and
                  len(result) <= target_count)
        Invariant(ToSeq(result) ==
                  ToSeq(existing) + fresh_run(len(result) - len(existing)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result) - len(existing)))
        result.append(FRESH_MEMBER())
    return result"""
_POS_REUSE_LENTEST = _swap(_BASE, _REUSE_BODY, _REUSE_LENTEST)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped, in-domain input establishes
# the precondition for a normal input. We build an F2P-shaped roster — one
# already-present member with a non-negative identity (estimators_[0]) — and call
# refit_to_size(probe, 2, True) (reuse, enlarge by one), establishing
# Acc(list_pred(probe),1/2), len(probe) <= target_count, and the non-negative
# identity precondition; the half-permission RESULT lets the call return cleanly.
# Then the gold dispatch runs unchanged. If the self-call cannot establish the
# precondition for a normal warm-start input => PRECOND-TOO-STRONG.
_DISPATCH_ADMISS = """    probe = [0]  # type: List[int]
    Assert(probe[0] >= 0)
    Assert(Acc(list_pred(probe), 1 / 2))
    Assert(len(probe) <= 2)
    Assert(Forall(int, lambda k:
                  (Implies(0 <= k and k < len(probe), probe[k] >= 0),
                   [[probe[k]]])))
    if requested_reuse and len(existing) > 0:
        return reuse_and_extend(existing, target_count)
    else:
        return rebuild_all(target_count)"""
_POS_ADMISS = _swap(_BASE, _DISPATCH, _DISPATCH_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) THE BUG ITSELF — always rebuild, ignore requested_reuse (exactly
# model_prepatch.py). In the reuse case (requested_reuse and len(existing)>0) the
# result is fresh_run(target_count) whose first element is FRESH_MEMBER() == -1,
# NOT the preserved existing[0] >= 0 — violating the REUSE-case prefix postcond.
_DISPATCH_ALWAYS_REBUILD = """    return rebuild_all(target_count)"""
_RIVAL_ALWAYS_REBUILD = _swap(_BASE, _DISPATCH, _DISPATCH_ALWAYS_REBUILD)

# (1b) Dual bug — always REUSE-and-extend, ignore requested_reuse. (Guarded so it
# still type-checks: reuse_and_extend's precondition needs len(existing) <=
# target_count, which refit_to_size already requires.) In the REBUILD case
# (requested_reuse False, or no members) it preserves the existing prefix instead
# of rebuilding all fresh — violating the REBUILD-case postcond
# ToSeq(Result()) == fresh_run(target_count) whenever existing is non-empty (its
# first element would be existing[0] >= 0, not -1).
_DISPATCH_ALWAYS_REUSE = """    return reuse_and_extend(existing, target_count)"""
_RIVAL_ALWAYS_REUSE = _swap(_BASE, _DISPATCH, _DISPATCH_ALWAYS_REUSE)

# (2) FRAME-MUTATION on refit_to_size's read-only `existing` (MANDATORY). Before
# dispatching, overwrite the first already-present identity in place
# (existing[0] = FRESH_MEMBER()). `existing` is Acc(list_pred(existing),1/2):
# WRITING needs FULL permission, which the caller does not hold — the assignment
# fails to verify for INSUFFICIENT PERMISSION. The gold dispatch is kept verbatim
# after the write, so the rejection is attributable solely to the frame write.
_DISPATCH_FRAME_WRITE = """    existing[0] = FRESH_MEMBER()
    if requested_reuse and len(existing) > 0:
        return reuse_and_extend(existing, target_count)
    else:
        return rebuild_all(target_count)"""
_RIVAL_FRAME_WRITE = _swap(_BASE, _DISPATCH, _DISPATCH_FRAME_WRITE)

# (2b) FRAME-MUTATION inside reuse_and_extend's read-only `existing`. The keep-
# prefix loop is reshaped to MUTATE the source roster in place (existing[j] =
# existing[j]) before reading it — a no-op value-wise, but it WRITES through a
# half-permission reference, so it fails for INSUFFICIENT PERMISSION. All gold
# invariants/asserts/lemmas are kept verbatim so the rejection is attributable to
# the write, not to a dropped proof obligation.
_REUSE_FRAME_WRITE = """    result = []  # type: List[int]
    j = 0
    while j < len(existing):
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(existing))
        Invariant(len(existing) <= target_count)
        Invariant(len(result) == j)
        Invariant(ToSeq(result) == ToSeq(existing).take(j))
        Invariant(MustTerminate(len(existing) - j + 1))
        # invariants-end
        existing[j] = existing[j]
        result.append(existing[j])
        j = j + 1
    Assert(ToSeq(existing).take(len(existing)) == ToSeq(existing))
    Assert(ToSeq(result) == ToSeq(existing))
    while len(result) < target_count:
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(existing) <= len(result) and
                  len(result) <= target_count)
        Invariant(ToSeq(result) ==
                  ToSeq(existing) + fresh_run(len(result) - len(existing)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result) - len(existing)))
        result.append(FRESH_MEMBER())
    return result"""
_RIVAL_REUSE_FRAME_WRITE = _swap(_BASE, _REUSE_BODY, _REUSE_FRAME_WRITE)

# (3) PARTIAL-DOMAIN — reuse_and_extend stops the fresh tail ONE member short:
# `while len(result) < target_count - 1`. Correct on the prefix and on most of
# the count, but the final roster has target_count - 1 members (when target_count
# > len(existing)), violating the SIZE pin len(Result()) == target_count. (When
# target_count == len(existing) the loop never runs and it is accidentally
# correct — so it diverges only on the enlarge sub-domain, the exact F2P case
# 10 -> 20.) The prefix-copy loop and the fresh-tail invariant/lemma are kept;
# only the tail loop BOUND is corrupted.
_REUSE_SHORT_TAIL = """    result = []  # type: List[int]
    j = 0
    while j < len(existing):
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(existing))
        Invariant(len(existing) <= target_count)
        Invariant(len(result) == j)
        Invariant(ToSeq(result) == ToSeq(existing).take(j))
        Invariant(MustTerminate(len(existing) - j + 1))
        # invariants-end
        result.append(existing[j])
        j = j + 1
    Assert(ToSeq(existing).take(len(existing)) == ToSeq(existing))
    Assert(ToSeq(result) == ToSeq(existing))
    while len(result) < target_count - 1:
        # invariants-start
        Invariant(Acc(list_pred(existing), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(existing) <= len(result) and
                  len(result) <= target_count)
        Invariant(ToSeq(result) ==
                  ToSeq(existing) + fresh_run(len(result) - len(existing)))
        Invariant(MustTerminate(target_count - len(result) + 1))
        # invariants-end
        Assert(lemma_fresh_snoc(len(result) - len(existing)))
        result.append(FRESH_MEMBER())
    return result"""
_RIVAL_SHORT_TAIL = _swap(_BASE, _REUSE_BODY, _REUSE_SHORT_TAIL)

# (4) PARTIAL-DOMAIN on the dispatch guard — require BOTH members present AND a
# stronger threshold: `if requested_reuse and len(existing) > 1:`. Reuse is taken
# only when MORE THAN ONE member is present, so on the (requested_reuse=True,
# len(existing)==1) sub-domain it falls into rebuild_all and produces an all-fresh
# roster — violating the REUSE-case prefix postcond (effective_reuse is True
# there, since len(existing)>0, yet the result is fresh_run, not the preserved
# prefix). Correct on every other input; wrong on the single-member reuse case.
_DISPATCH_GT1 = """    if requested_reuse and len(existing) > 1:
        return reuse_and_extend(existing, target_count)
    else:
        return rebuild_all(target_count)"""
_RIVAL_GT1 = _swap(_BASE, _DISPATCH, _DISPATCH_GT1)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-dispatch-inverted-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_DISPATCH_INVERTED,
     "rationale": "structurally-different but semantically identical refit dispatch: the guard is "
                  "inverted (De Morgan) and the two branches swapped, so the reuse builder is "
                  "called on EXACTLY the same inputs (requested_reuse and len(existing)>0) and the "
                  "rebuild builder otherwise. effective_reuse is unchanged. If it fails to verify, "
                  "the postcondition is over-fit to one guard polarity => SPEC-TOO-STRONG. Also the "
                  "cheapest honest dispatch — there is no echoable oracle, it must call a real "
                  "roster builder per case."},
    {"id": "pos-reuse-lentest-loop", "kind": "soundness", "expect": "verify",
     "module": _POS_REUSE_LENTEST,
     "rationale": "a correct reuse_and_extend with a DIFFERENT prefix-copy loop shape "
                  "(driven by `len(result) < len(existing)` instead of an explicit j counter); "
                  "same observable roster. ALL framing asserts and the lemma_fresh_snoc bridge are "
                  "kept verbatim (pilot trap #2/#3 avoided: the back-append fold still has its snoc "
                  "lemma), only the loop SHAPE changes. If it fails to verify the spec is over-fit "
                  "to the j-counter loop shape => SPEC-TOO-STRONG."},
    {"id": "admiss-self-call-warmstart", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on an F2P-shaped in-domain input (a one-member roster [0] with a "
                  "non-negative identity, enlarged to 2 under reuse) must establish the precondition "
                  "Acc(list_pred(existing),1/2) + len(existing)<=target_count + non-negative "
                  "identities. If the self-call cannot establish the precondition for a normal "
                  "warm-start input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-always-rebuild", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_REBUILD,
     "refinement": "this is model_prepatch.py verbatim: refit_to_size ALWAYS rebuilds, ignoring "
                   "requested_reuse. Its faithful real patch is the UNCHANGED pre-patch "
                   "IsolationForest.__init__, which never forwards warm_start, so self.warm_start "
                   "keeps its inherited default False and BaseBagging._fit rebuilds the whole forest "
                   "on every fit. That is exactly the bug the F2P test asserts against: it fits 10 "
                   "trees with warm_start=True, remembers tree_1, enlarges to 20, fits again, and "
                   "requires len(estimators_)==20 AND estimators_[0] is tree_1. A rebuild gives 20 "
                   "BRAND-NEW trees, so estimators_[0] is NOT tree_1 — it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / model_prepatch.py). "
                  "Rejection source: the REUSE-case postcondition "
                  "ToSeq(Result()) == ToSeq(existing) + fresh_run(target_count-len(existing)) — when "
                  "effective_reuse holds, an all-fresh roster's first element is FRESH_MEMBER() == "
                  "-1, unequal to existing[0] >= 0, so the prefix conjunct fails. If it verified => "
                  "SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "rival-always-reuse", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYS_REUSE,
     "refinement": "always keeps the existing prefix and extends, ignoring requested_reuse. Its "
                   "faithful real patch would FORCE warm-start on every fit (never reset "
                   "estimators_), so a cold caller (warm_start=False) that re-fits would silently "
                   "keep stale trees instead of rebuilding a whole new forest. The P2P suite "
                   "(test_iforest etc., all warm_start=False) re-fits and expects a freshly built "
                   "forest each time; keeping the old roster prefix would change the fitted model "
                   "and the predictions — it would NOT resolve.",
     "rationale": "dual of the bug: forces reuse on the rebuild domain. Rejection source: the "
                  "REBUILD-case postcondition Implies(not effective_reuse(...), ToSeq(Result()) == "
                  "fresh_run(target_count)) — when requested_reuse is False (or no members) but "
                  "existing is non-empty, keeping the prefix makes Result()[0] == existing[0] >= 0, "
                  "unequal to fresh_run's -1. If it verified => SPEC-TOO-WEAK (rebuild case "
                  "unconstrained)."},
    {"id": "rival-frame-mutate-existing-dispatch", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_WRITE,
     "refinement": "overwrites the first already-present identity in place (existing[0] = "
                   "FRESH_MEMBER()) before dispatching. Its faithful real patch would MUTATE "
                   "clf.estimators_[0] in place during a refit — corrupting the preserved roster so "
                   "that estimators_[0] is NO LONGER tree_1. The F2P test asserts estimators_[0] is "
                   "tree_1, so any patch that rewrites the first member in place would NOT resolve. "
                   "(Here it must be rejected for INSUFFICIENT PERMISSION, not value: existing is "
                   "read-only.)",
     "rationale": "FRAME-MUTATION (MANDATORY, the #1 weakness class). `existing` is held at "
                  "Acc(list_pred(existing),1/2) (read-only); the assignment existing[0]=... needs "
                  "FULL write permission, which the caller does not hold. Rejection source: the "
                  "PERMISSION SYSTEM (insufficient permission to write a half-permission predicate), "
                  "not the postcondition. The gold dispatch is kept verbatim after the write, so the "
                  "rejection is attributable solely to the frame write. If it verified => the "
                  "read-only contract is unsound."},
    {"id": "rival-frame-mutate-existing-reuse", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REUSE_FRAME_WRITE,
     "refinement": "inside reuse_and_extend, writes through the half-permission `existing` "
                   "(existing[j] = existing[j], value-wise a no-op) while copying the prefix. A "
                   "faithful real patch that wrote back into clf.estimators_ during the keep-prefix "
                   "copy would still corrupt object identity (a re-assigned slot is no longer the "
                   "same tree object), failing estimators_[0] is tree_1 — would NOT resolve. The "
                   "value being identical is irrelevant: the write itself is illegal.",
     "rationale": "FRAME-MUTATION (second read-only surface). `existing` in reuse_and_extend is "
                  "Acc(list_pred(existing),1/2); the in-place write existing[j]=... requires full "
                  "permission. Rejection source: the PERMISSION SYSTEM. All gold invariants/asserts/"
                  "lemmas are kept verbatim, so the rejection is attributable solely to the write, "
                  "not a dropped proof obligation. If it verified => the read-only contract is "
                  "unsound."},
    {"id": "rival-partial-short-tail", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SHORT_TAIL,
     "refinement": "reuse_and_extend stops the fresh-member tail ONE short (loop bound "
                   "target_count - 1), so a warm-start enlarge to n_total yields n_total-1 trees. A "
                   "faithful real patch that appended one too few estimators would make "
                   "len(clf.estimators_) == 19, not 20, after the F2P enlarge-to-20 — failing the "
                   "assert len(clf.estimators_) == 20. It would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN: correct on the prefix and accidentally correct when target_count "
                  "== len(existing) (loop never runs), but wrong on the enlarge sub-domain (the "
                  "exact F2P 10->20). Rejection source: the SIZE pin len(Result()) == target_count — "
                  "with the tail one short, len(Result()) == target_count - 1. If it verified => "
                  "SPEC-TOO-WEAK (count not pinned on the enlarge domain)."},
    {"id": "rival-partial-gt1-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_GT1,
     "refinement": "the dispatch reuses only when MORE THAN ONE member is present "
                   "(len(existing) > 1), falling into rebuild on the single-member reuse case. A "
                   "faithful real patch that re-enabled warm-start only above one existing tree would "
                   "rebuild a forest whenever exactly one tree was present — the F2P-shaped warm "
                   "refit starting from a one-tree roster would lose estimators_[0] (rebuilt, not "
                   "preserved). It would NOT resolve on that sub-domain.",
     "rationale": "PARTIAL-DOMAIN on the dispatch threshold. Rejection source: the REUSE-case "
                  "postcondition — for (requested_reuse=True, len(existing)==1) effective_reuse is "
                  "True (len(existing)>0), so the contract demands the preserved prefix, but the "
                  "impl rebuilds all-fresh (Result()[0] == -1 != existing[0] >= 0). If it verified "
                  "=> SPEC-TOO-WEAK (reuse domain incomplete at the boundary len(existing)==1)."},
]

# ===========================================================================
# AXIOM LANE — empty. This bundle consumes NO @ContractOnly axiom: the reuse
# decision and the roster update are modeled DEEPLY (effective_reuse /
# reuse_and_extend / rebuild_all / fresh_run). The deep model is validated ==
# the real sklearn.ensemble.IsolationForest incremental behaviour out-of-band by
# axiom_check.py (G-AX, A-reference: 70 scenarios, reuse + rebuild, object
# identity via `is`), which is NOT in the PBT lane's scope. meta.json axioms is
# [] and deep_model_references are A-reference, so there is no in-domain @Pure
# axiom soundness/containment obligation for PBT to check here.
# ===========================================================================
AXIOM_TESTS = []
