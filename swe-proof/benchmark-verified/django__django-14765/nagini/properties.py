"""PBT manifest for django__django-14765.

NOT a Nagini module: an adversarial falsification battery for the frozen spec of
`build_state`. The runner (`swebench_nagini.pbt`) parses SPEC_TESTS (full
model.py variants — same frozen spec, impl region swapped — checked by Nagini
verify + same_spec) and AXIOM_TESTS (real-callee probes in Docker). Every
variant is built by `_swap` editing ONLY text strictly between `# impl-start`
and `# impl-end`, so the frozen spec (axioms/pure/pre/post/Exsures) is never
touched and same_spec is guaranteed.

Defended surface (read from model.py + refinement.md + mapping.md + meta.json):
  * `build_state(real_apps: List[int], present: bool, is_expected_kind: bool)
    -> List[int]` models `ProjectState.__init__`'s real_apps processing:
    `present` == `real_apps is not None`; `is_expected_kind` == `isinstance(
    real_apps, set)`; the returned List[int] membership == the stored
    self.real_apps membership; OffKindCollection == the AssertionError raised by
    `assert isinstance(real_apps, set)`.
  * INPUT IS READ-ONLY: `Requires(Acc(list_pred(real_apps), 1/2))` and
    `Ensures(Acc(list_pred(real_apps), 1/2))` — half permission only, returned
    unchanged. Any WRITE to real_apps (append/pop/index-store) needs full
    permission and rejects for INSUFFICIENT PERMISSION. (frame-mutation lane:
    MANDATORY here.)
  * LOAD-BEARING postcondition clauses:
      (P-disc)  Ensures((not present) or is_expected_kind)
                — normal return is reachable ONLY for an absent OR
                  expected-kind collection. THE discriminating clause: the
                  pre-patch coerced a present off-kind collection and returned
                  normally; this clause forbids that. (== F2P:
                  ProjectState(real_apps=['contenttypes']) must raise.)
      (P-absent) Ensures(Implies(not present, len(Result()) == 0))
      (P-mem)    Ensures(Implies(present and is_expected_kind,
                                 ToSeq(Result()) == ToSeq(real_apps)))
      (P-raise)  Exsures(OffKindCollection, present and not is_expected_kind)
                — a present off-kind collection raises, for EVERY such
                  collection (empty OR non-empty), never a coerced result.
  * The oracle is GROUNDED in the inputs (functions of present /
    is_expected_kind / ToSeq(real_apps)); there is no @Pure answer-key to echo,
    so the ungrounded-oracle-echo lane is N/A (see 'assessment') and we instead
    supply honest positive controls.
  * meta.json axioms == [] and deep_model_references == []: the changed
    operation is pure control flow + a runtime kind test + an assert, modeled
    directly. AXIOM_TESTS is therefore []. (G-AX is vacuous for this bundle.)
"""
from pathlib import Path

INSTANCE = "django__django-14765"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (everything strictly between the markers).
# Every variant replaces THIS block — and only this block — so the swap edits
# nothing outside `# impl-start`/`# impl-end`; same_spec is preserved.
_GOLD_IMPL = """    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present-and-expected: the stored collection preserves the supplied
    # membership unchanged. Materialised here as a same-membership sequence so
    # the result carries full permission while the input stays read-only
    # (refinement.md: the real store is by reference, contents preserved — an
    # R-refinement of object identity to membership equality).
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


# --------------------------------------------------------------------------- #
# 1. FRAME-MUTATION (read-only input) — MANDATORY.                            #
#    real_apps is held at Acc(list_pred(real_apps), 1/2): half permission, so #
#    the function may READ but never WRITE it. This rival, on the             #
#    present-and-expected path, MUTATES the input (real_apps.append) before   #
#    materialising the result. It keeps the whole correct gold skeleton so    #
#    the rejection is attributable ONLY to the write, which requires full     #
#    permission the caller never granted -> INSUFFICIENT PERMISSION (not a    #
#    value mismatch). A pure byte-fuzzer never thinks to mutate the input.    #
# --------------------------------------------------------------------------- #
_FRAME_MUTATE = """    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # ATTACK (frame-mutation): write to the read-only input real_apps. The
    # contract grants only Acc(list_pred(real_apps), 1/2) (read-only), so this
    # append lacks the permission to mutate -> must reject for insufficient
    # permission. Everything else below is the correct gold skeleton, so the
    # rejection is attributable ONLY to the write.
    real_apps.append(0)
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 2. PARTIAL-DOMAIN / pre-patch bug — coerce a present non-empty off-kind.     #
#    This IS the pre-patch skeleton (model_prepatch.py): a present, NON-EMPTY  #
#    collection of ANY kind is accepted and copied (coerced) rather than       #
#    failing; only absent/empty yields empty. For a present off-kind non-empty #
#    collection it returns NORMALLY (a coerced membership) instead of raising  #
#    -> violates (P-disc) (not present) or is_expected_kind. This is exactly   #
#    the F2P: ProjectState(real_apps=['contenttypes']) must raise.             #
# --------------------------------------------------------------------------- #
_COERCE_NONEMPTY = """    # ATTACK (pre-patch bug): accept a present NON-EMPTY collection of any kind
    # and copy it (silent coercion) instead of failing on an off-kind one; only
    # absent/empty yields empty. Returns normally for a present off-kind
    # non-empty collection -> violates the discriminating normal-return clause.
    if present and len(real_apps) > 0:
        result = []  # type: List[int]
        i = 0
        while i < len(real_apps):
            # invariants-start
            Invariant(Acc(list_pred(real_apps), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(real_apps))
            Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
            Invariant(MustTerminate(len(real_apps) - i + 1))
            # invariants-end
            Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
            result.append(real_apps[i])
            i = i + 1
        return result
    empty = []  # type: List[int]
    return empty
"""


# --------------------------------------------------------------------------- #
# 3. PARTIAL-DOMAIN — only raise on a NON-EMPTY off-kind collection.           #
#    Correct on the whole domain EXCEPT a present off-kind EMPTY collection,   #
#    for which it returns the empty list instead of raising. The spec pins the #
#    raise for EVERY present off-kind collection (P-raise + P-disc), empty or  #
#    not. So returning normally on the empty off-kind sub-domain violates      #
#    (P-disc) (not present) or is_expected_kind. A subtle truthiness bug a     #
#    fuzzer never targets (it mirrors the real `if real_apps:` truthiness      #
#    blind spot — an empty non-set is falsy and slips through).                #
# --------------------------------------------------------------------------- #
_RAISE_NONEMPTY_ONLY = """    if not present:
        empty = []  # type: List[int]
        return empty
    # ATTACK (partial-domain): raise ONLY for a present off-kind collection that
    # is also NON-EMPTY; a present off-kind EMPTY collection slips through and
    # returns normally (the empty list) instead of raising. The spec pins the
    # raise for EVERY present off-kind collection, so this returns normally on a
    # sub-domain the discriminating clause forbids.
    if (not is_expected_kind) and len(real_apps) > 0:
        raise OffKindCollection()
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 4. PARTIAL-DOMAIN — drop the last element of a present-expected collection.  #
#    Copies all but the final element. Agrees with the spec only on the        #
#    empty/singleton-into-empty sub-domain; for any present-expected           #
#    collection with >= 1 element it stores a STRICT prefix, so                #
#    ToSeq(Result()) != ToSeq(real_apps) -> violates (P-mem). A genuine        #
#    off-by-one membership corruption (the real patch must store the WHOLE     #
#    set; dropping one app label would make StateApps miss a registered app).  #
# --------------------------------------------------------------------------- #
_DROP_LAST = """    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # ATTACK (partial-domain): copy all elements EXCEPT the last one. Agrees on
    # the empty input but stores a strict prefix for any non-empty present
    # collection -> the stored membership != the supplied membership.
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps) - 1:
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 4b. DIVERGENCE (non-termination) — evade the outcome instead of producing it. #
#     On the present off-kind path, where the spec demands the internal-        #
#     contract violation, this rival instead descends into itself without       #
#     bound: each call re-enters on a fresh collection with the same present /  #
#     off-kind flags, so no call ever reaches the raise. It NEVER returns and   #
#     NEVER raises. Because every Ensures/Exsures speaks about an outcome,      #
#     an impl that reaches no outcome would discharge all of them VACUOUSLY:    #
#     partial correctness alone cannot see this rival. It is caught only by     #
#     the termination clause (the construction must complete within a budget    #
#     bounded by the supplied collection's size). This case is what makes that  #
#     clause load-bearing rather than decorative.                               #
#                                                                              #
#     NOTE the discrimination is on DIVERGENCE, not on self-reference: a rival  #
#     whose recursion is bounded (guarded so it bottoms out) still terminates,  #
#     still raises, and MUST keep verifying — see the measure chosen in         #
#     model.py, which admits any descent that decreases the input.              #
# --------------------------------------------------------------------------- #
_DIVERGE_OFFKIND = """    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        # ATTACK (divergence): instead of reporting the internal-contract
        # violation, re-enter unboundedly with the same present/off-kind flags.
        # No call in the chain ever reaches the raise below, so construction
        # produces NEITHER outcome and every Ensures/Exsures would hold
        # vacuously. Only the termination obligation rejects this.
        spare = []  # type: List[int]
        again = build_state(spare, present, is_expected_kind)
        raise OffKindCollection()
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 5b. POSITIVE CONTROL (soundness) — BOUNDED self-reference, still CORRECT.    #
#     Guards the same self-descent so it bottoms out immediately: the inner    #
#     call receives an empty collection, whose own guard is false, so the      #
#     chain has depth 1 and the internal-contract violation still propagates   #
#     to the caller. Behaviourally identical to gold on every branch (its      #
#     faithful real patch RESOLVES the instance). It MUST verify: the spec is  #
#     entitled to forbid DIVERGENCE, but not to forbid a terminating           #
#     implementation merely for being structured recursively. This is the      #
#     over-fit guard on the termination clause — if a measure rejects this,    #
#     the measure pins an incidental detail of the gold shape.                 #
# --------------------------------------------------------------------------- #
_POS_BOUNDED_RECURSION = """    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        # POSITIVE CONTROL: self-descent that provably bottoms out (the inner
        # call gets an empty collection, so its own guard is false). Depth 1;
        # the internal-contract violation below still reaches the caller.
        if len(real_apps) > 0:
            spare = []  # type: List[int]
            again = build_state(spare, present, is_expected_kind)
        raise OffKindCollection()
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 5. POSITIVE CONTROL (soundness) — structurally different, still CORRECT.     #
#    Reorders the decision: handle the off-kind RAISE first (a present non-set #
#    must fail), THEN the absent case, THEN copy the present-expected          #
#    membership. The copy loop keeps EVERY gold invariant + the per-element    #
#    framing Assert verbatim (so no proof obligation is dropped — pilot bug 2).#
#    Pure branch-reorder + a forward index copy against a take()-prefix        #
#    invariant the gold proof already uses; no induction/fold lemma is         #
#    introduced (pilot bug 3). It MUST verify (else SPEC-TOO-STRONG).          #
# --------------------------------------------------------------------------- #
_POS_REORDER = """    # POSITIVE CONTROL: same behaviour, reordered decision. Raise on a present
    # off-kind collection first, then handle the absent case, then copy the
    # present-expected membership with the gold invariants/Assert kept verbatim.
    if present and not is_expected_kind:
        raise OffKindCollection()
    if not present:
        empty = []  # type: List[int]
        return empty
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
"""


# --------------------------------------------------------------------------- #
# 6. ADMISSIBILITY — the precondition admits a normal F2P/P2P-shaped input.    #
#    A correct impl that ALSO Asserts, on its own in-domain inputs, the facts  #
#    the Requires/control-flow guarantee on each reachable branch:             #
#      - absent (P2P ProjectState()): result is empty;                        #
#      - present & expected (P2P ProjectState(real_apps=set)): the copy keeps  #
#        the supplied membership;                                             #
#    plus a read of len(real_apps) >= 0 to show the half-permission read of    #
#    the input is admitted. If the precondition were too strong these          #
#    reads/asserts would fail; it must verify (else PRECOND-TOO-STRONG). We    #
#    assert on the function's own parameters (no fresh constructor) to avoid a #
#    permission obligation unrelated to the precondition under test.           #
# --------------------------------------------------------------------------- #
_ADMISS = """    # ADMISSIBILITY: the precondition must accept a normal F2P/P2P-shaped input.
    # The half-permission read of the input is in-domain (len is non-negative).
    Assert(len(real_apps) >= 0)
    if not present:
        # Absent (P2P ProjectState()): the stored membership is empty.
        empty = []  # type: List[int]
        Assert(len(empty) == 0)
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present & expected (P2P ProjectState(real_apps=set)): copy the membership.
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    Assert(ToSeq(result) == ToSeq(real_apps))
    return result
"""


SPEC_TESTS = [
    {
        "id": "frame-mutate-real-apps",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUTATE),
        "refinement": (
            "The faithful real patch of this rival WRITES to the supplied "
            "real_apps argument inside ProjectState.__init__ (e.g. "
            "real_apps.add(...) / real_apps.clear()) before/while storing it. "
            "The gold edit only READS real_apps (asserts it is a set, then stores "
            "the same object by reference); PR #14760 made every caller pass its "
            "own set, and those callers reuse that set afterwards. Mutating the "
            "caller's set would corrupt that shared state and break the P2P tests "
            "that build a ProjectState from an Apps' real_apps set and then "
            "compare/iterate it (e.g. the StateApps / set-of-real-apps P2P cases) "
            "-> would NOT resolve. In the model real_apps is Acc(...,1/2): the "
            "write has no permission and must reject."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION SYSTEM, not a value mismatch: "
            "real_apps is held at Acc(list_pred(real_apps), 1/2) (read-only) by "
            "the precondition and re-promised at 1/2 by the postcondition; "
            "real_apps.append(...) requires full permission the caller never "
            "granted -> INSUFFICIENT PERMISSION."
        ),
    },
    {
        "id": "prepatch-coerce-nonempty-offkind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _COERCE_NONEMPTY),
        "refinement": (
            "This is the pre-patch code itself (model_prepatch.py / the gold "
            "diff's '-' lines): `if real_apps: self.real_apps = real_apps if "
            "isinstance(real_apps, set) else set(real_apps)`. A present non-empty "
            "off-kind collection is SILENTLY COERCED to a set and stored, "
            "returning normally. The F2P test ProjectState(real_apps="
            "['contenttypes']) expects assertRaises(AssertionError); the pre-patch "
            "returns normally -> the F2P FAILS, does not resolve (this is exactly "
            "the bug the ticket fixes; mirrors G-DIFF / model_prepatch.py)."
        ),
        "rationale": (
            "Fails the discriminating postcondition (P-disc) Ensures((not present) "
            "or is_expected_kind): on a present off-kind (is_expected_kind=False) "
            "non-empty collection it returns NORMALLY, but the spec demands a "
            "raise (the verifier cannot prove the normal-return clause)."
        ),
    },
    {
        "id": "partial-domain-raise-nonempty-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RAISE_NONEMPTY_ONLY),
        "refinement": (
            "Its faithful real patch guards the assert on truthiness rather than "
            "is-None, e.g. keeping `if real_apps: assert isinstance(real_apps, "
            "set)` — so a present but EMPTY off-kind collection (an empty list, "
            "which is falsy) slips past and is stored as the empty set, returning "
            "normally instead of raising. The fix's intent (and the gold "
            "`else: assert isinstance(real_apps, set)`, reached for ANY non-None "
            "real_apps) is that a present non-set ALWAYS fails; an empty-list "
            "real_apps must still raise AssertionError. A patch that only raises "
            "for non-empty off-kind collections silently accepts the off-kind "
            "empty case -> diverges from the gold contract on that sub-domain and "
            "would not be the faithful fix."
        ),
        "rationale": (
            "Fails (P-disc) Ensures((not present) or is_expected_kind) on the "
            "sub-domain present=True, is_expected_kind=False, len(real_apps)==0: "
            "it returns NORMALLY there, but the spec demands a raise for EVERY "
            "present off-kind collection (Exsures P-raise + P-disc). The empty "
            "off-kind case is exactly where the truthiness guard differs from the "
            "is-None guard."
        ),
    },
    {
        "id": "partial-domain-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DROP_LAST),
        "refinement": (
            "Its faithful real patch stores a STRICT SUBSET of the supplied set "
            "(drops one app label), e.g. self.real_apps = "
            "set(list(real_apps)[:-1]). The stored real_apps is consumed by "
            "StateApps (which loads exactly the apps in self.real_apps) and by "
            "ProjectState.__eq__ (self.real_apps == other.real_apps); dropping a "
            "label means a registered unmigrated app is missing, so the P2P cases "
            "that construct a ProjectState from a non-trivial real_apps set and "
            "then rely on its full membership (StateApps rendering / equality) "
            "FAIL -> would not resolve."
        ),
        "rationale": (
            "Fails (P-mem) Ensures(Implies(present and is_expected_kind, "
            "ToSeq(Result()) == ToSeq(real_apps))): for any present-expected "
            "collection with >= 1 element the loop stores ToSeq(real_apps).take("
            "len-1), a strict prefix != ToSeq(real_apps)."
        ),
    },
    {
        "id": "diverge-offkind-never-completes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DIVERGE_OFFKIND),
        "refinement": (
            "Its faithful real patch replaces the assert's failure path in "
            "ProjectState.__init__ with an unbounded self-construction — e.g. on "
            "a non-None non-set real_apps it does ProjectState(real_apps=set()) "
            "-style re-entry (per mapping.md §1, build_state <-> "
            "ProjectState.__init__, so a self-recursive model call refines to "
            "constructing another ProjectState) instead of letting `assert "
            "isinstance(real_apps, set)` fire. Construction then never completes: "
            "CPython unwinds with RecursionError rather than the AssertionError "
            "the fix specifies. The F2P test test_real_apps_non_set does "
            "assertRaises(AssertionError) on ProjectState(real_apps="
            "['contenttypes']); RecursionError is not an AssertionError, so the "
            "exact discriminating test of the change FAILS -> does NOT resolve. "
            "(This is the counterexample class a prior audit confirmed against "
            "the official harness: applied cleanly, completed, resolved=false.)"
        ),
        "rationale": (
            "Caught ONLY by the termination obligation, and this is why that "
            "obligation must exist. The impl reaches neither outcome, so every "
            "Ensures (P-disc/P-absent/P-mem) and the Exsures (P-raise) hold "
            "VACUOUSLY — control never arrives at a return or a raise, and the "
            "value clauses have nothing to constrain. The precondition's "
            "MustTerminate budget is bounded by len(real_apps), while the "
            "self-descent re-enters with the same present/off-kind flags and no "
            "decrease, so the callee cannot take on the caller's unsatisfied "
            "obligation -> rejected. Without the termination clause this rival "
            "VERIFIES while being wrong, which is precisely verify =/=> correct."
        ),
    },
    {
        "id": "pos-control-bounded-self-reference",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_BOUNDED_RECURSION),
        "rationale": (
            "OVER-FIT GUARD for the termination clause. Behaviourally identical "
            "to gold: the self-descent is guarded so it bottoms out at depth 1 "
            "(the inner call receives an empty collection, whose guard is false), "
            "the internal-contract violation still propagates for every present "
            "off-kind collection (P-raise/P-disc), the absent case returns empty "
            "(P-absent) and the present-expected case copies the membership "
            "(P-mem). Its faithful real patch RESOLVES the instance. The spec "
            "must forbid DIVERGENCE without forbidding a terminating recursive "
            "structure, so a termination measure that rejects this one is pinning "
            "an incidental detail of the gold implementation's shape rather than "
            "the behaviour (must verify, else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-control-reorder-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": (
            "Structurally different (the off-kind RAISE is decided first, then "
            "the absent case, then the present-expected copy) but behaviourally "
            "identical to the gold impl on every branch: present off-kind raises "
            "(P-raise), absent returns empty (P-absent), present-expected copies "
            "the membership (P-mem) and returns normally only when (not present) "
            "or is_expected_kind (P-disc). The copy loop keeps every gold "
            "invariant and the per-element framing Assert verbatim (no dropped "
            "proof obligation), and uses the same forward take()-prefix invariant "
            "the gold proof uses (no induction/fold lemma). Must verify (else "
            "SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-f2p-p2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": (
            "The precondition (Acc(list_pred(real_apps), 1/2), read-only) must "
            "admit the normal F2P/P2P-shaped inputs: absent (ProjectState() -> "
            "empty), present-and-expected (ProjectState(real_apps=set) -> "
            "membership copied), and present off-kind (raise). A correct impl that "
            "additionally Asserts the in-domain facts each branch guarantees "
            "(len(real_apps) >= 0 read of the half-permission input; empty result "
            "when absent; ToSeq(result) == ToSeq(real_apps) when present-expected) "
            "must verify; if the precondition were too strong these reads/asserts "
            "would fail -> PRECOND-TOO-STRONG."
        ),
    },
]


# No @ContractOnly axioms (meta.json axioms == []) and no deep-model references
# (deep_model_references == []). The changed operation is pure Python control
# flow + a runtime kind test (isinstance, modeled directly as the
# is_expected_kind boolean — axiomatizing it would model the thing under change)
# + an assert (the Exsures raise). There is no consumed axiom or A-reference for
# the PBT axiom lane to re-discharge, so AXIOM_TESTS is empty (G-AX is vacuous
# for this bundle; mapping.md §3, refinement.md §B).
AXIOM_TESTS = []
