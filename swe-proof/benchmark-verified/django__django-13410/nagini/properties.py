# properties.py — PBT falsification battery for django__django-13410.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside a # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec actually protects — see model.py /
# refinement.md / mapping.md). Two modeled functions, two impl regions, two
# A-consumed axioms over the unchanged callee fcntl.flock:
#
#   acquire(available: bool) -> bool                     (lock-acquisition helper)
#     Requires lock_state()                              <-- FRAMING resource only;
#                                                            constrains NO input, so
#                                                            both bool values admissible
#     Requires answerable_acquisition()                  <-- SCOPE, as ONE EXPENDABLE
#                                                            CAPABILITY: an acquisition
#                                                            is the operation another
#                                                            holder CAN leave pending,
#                                                            so this helper's promise
#                                                            to answer is scoped to
#                                                            answered requests. Pure
#                                                            contract-only fact:
#                                                            constrains no value, both
#                                                            bools and both paths stay
#                                                            live (see the
#                                                            admissibility case)
#     Ensures  lock_state()                              <-- world handed back
#     Ensures  Result() == available                     <-- LOAD-BEARING: report
#                                                            the outcome faithfully
#     Ensures  Implies(Result() is True, holds_lock())   <-- LOAD-BEARING (EXIT
#                                                            STATE): when the helper
#                                                            reports success the lock
#                                                            must be IN FORCE at the
#                                                            return point
#     Ensures  Implies(Result() is False,                <-- LOAD-BEARING (EXIT
#                holds_lock() == Old(holds_lock()))           STATE, failure half): a
#                                                            reported failure must
#                                                            leave the lock state
#                                                            exactly as it was found
#     impl: try: primitive_lock(available); return True
#           except LockUnavailable: return False
#
#   release() -> bool                                    (lock-release helper)
#     Requires lock_state()                              <-- FRAMING resource only
#     (NO answerability condition)                       <-- LOAD-BEARING BY ABSENCE:
#                                                            a release of a held lock
#                                                            is always answered, so
#                                                            this helper's promise to
#                                                            report back is
#                                                            UNCONDITIONAL -- and a
#                                                            release body therefore has
#                                                            no answerability fact to
#                                                            hand to an acquisition
#                                                            step, which is what
#                                                            rejects "release by
#                                                            acquiring first" (case 12)
#     Ensures  lock_state()
#     Ensures  Result() is True                          <-- LOAD-BEARING: a held
#                                                            release reports True
#     Ensures  holds_lock() is False                     <-- LOAD-BEARING (EXIT
#                                                            STATE): THIS CALLER must
#                                                            NOT hold the lock at the
#                                                            return point (another
#                                                            party's compatible claim
#                                                            is untouched, not denied)
#     impl: primitive_release(); return True
#
#   lock_state() @ContractOnly @Predicate  (abstract, NO body) -- the abstract lock
#               WORLD, threaded unchanged through every operation; framing only
#   holds_lock() @Pure @ContractOnly       -- the SINGLE-VALUED state observation
#               "does THIS CALLER hold the lock IT REQUESTED, RIGHT NOW", readable
#               only inside contracts (no implementation can compute or echo it).
#               Indexed to the CALLER (a compatible claim another party holds on the
#               same lock is not reported) and to the lock THIS REQUEST NAMED
#
#   answerable_acquisition() @ContractOnly @Predicate (abstract, NO body) -- the
#               EXPENDABLE CAPABILITY to make ONE acquisition request the world will
#               answer (grant or refuse) rather than leave PENDING, and will settle
#               outright. A RESOURCE, not a proposition: it can only be received and
#               SPENT -- nothing creates it, nothing duplicates it, and there is no
#               fact for a body to interrogate or branch on. primitive_lock CONSUMES
#               it and does not return it, so one authorisation buys exactly ONE
#               answered acquisition. acquire is handed one; release is handed none
#
#   primitive_lock(available) -> int   @ContractOnly  (A-consumed; fcntl.flock)
#     Requires lock_state();  Ensures lock_state()
#     Requires answerable_acquisition()     (CONSUMED here, not re-established: the
#                                            two-answer contract below describes
#                                            exactly the answered, outright-settled
#                                            requests, and one capability authorises
#                                            exactly one such request)
#     Ensures  available is True            (normal completion reachable only when
#                                            the lock WAS available)
#     Ensures  Result() is None             (THE VALUE IS EMPTY -- the granted
#                                            request reports NOTHING by value. No
#                                            numeric fact is claimed, not even
#                                            "differs from zero": an empty value
#                                            cannot be ordered, cannot enter
#                                            arithmetic and does not answer whether
#                                            it is "set", so the reported boolean is
#                                            NOT derivable from it by any route and
#                                            must come from the control flow)
#     Ensures  holds_lock()                 (a granted acquisition leaves the lock
#                                            IN FORCE -- direction 1 of the state)
#     Exsures  LockUnavailable, lock_state() and available is False
#              and holds_lock() == Old(holds_lock())
#                                           (refusal raises, exactly on the
#                                            unavailable case, and a refused
#                                            request moved nothing)
#
#   primitive_release() -> int         @ContractOnly  (A-consumed; fcntl.flock UN)
#     Requires lock_state();  Ensures lock_state()
#     (NO answerability condition -- a release of a held lock always completes)
#     Ensures  Result() is None                                   (no Exsures)
#                                           (THE VALUE IS EMPTY here too, and
#                                            independently: a completed release
#                                            reports nothing by value either)
#     Ensures  holds_lock() is False        (a release leaves THIS CALLER no longer
#                                            holding the lock -- direction 2; this is
#                                            what makes the observation REVERSIBLE,
#                                            hence a claim about the state at a
#                                            program point rather than about history.
#                                            It does not assert the lock is unclaimed
#                                            by every party)
#
# KEY ARCHITECTURE OF THE SPEC (why the attacks land where they do):
#   * The postconditions are GROUNDED in the input/literal: acquire pins
#     Result()==available (a function OF THE ARGUMENT) and release pins
#     Result() is True (a literal). There is NO opaque @Pure answer-key oracle a
#     wrong impl could echo — so the ungrounded-oracle-echo class is N/A. (See
#     'assessment'.)
#   * The DISCRIMINATING content of the gold change is "translate the primitive's
#     CONTROL-FLOW signal (normal completion vs. raise) into the boolean", NOT
#     "read the discarded return value". The pre-patch read ret == 0 off the
#     return value, which on a granted request is THE EMPTY VALUE and therefore
#     says nothing about the outcome — so the pre-patch reported failure even on a
#     successful acquire, the headline bug. The axioms encode the value as EMPTY
#     (Result() is None) precisely so the spec senses that bug and so that NO
#     numeric interrogation of the value is available to any body: a comparison
#     against zero is not a question the empty value answers at all, so the
#     pre-patch bodies are rejected AT THE COMPARISON rather than only at the
#     reported boolean (model_prepatch.py / model_prepatch_2.py — G-DIFF).
#   * WHY NOT A NUMERIC SENTINEL (this is the load-bearing modelling choice). If
#     the axioms handed back a definite number that merely "differs from zero",
#     the value would answer questions the real empty value refuses, and it would
#     answer them however that particular number happens to fall: it would count
#     as "set" or not, it would order against zero one way or the other, and it
#     would combine arithmetically. A body could then decide the outcome it
#     reports by asking the value one of those questions -- and every such body is
#     wrong, because the real granted request answers none of them and a caller
#     that interrogates the empty value learns nothing about whether it got the
#     lock. Those bodies are exercised as reject cases below (value-truthiness,
#     value-ordering, and vacuous-value-interrogation).
#   * The single subtle proof fact is primitive_lock's Ensures(available is True):
#     on the try-normal-path the verifier learns available is True (so return
#     True gives Result()==available); on the except path the Exsures gives
#     available is False (so return False gives Result()==available).
#   * EXIT-STATE GROUNDING (the closed flank). The value postconditions alone
#     cannot see the world behind the boolean — a helper that just returns
#     `available` (or the literal True) echoes the same boolean without ever
#     invoking fcntl.flock, and a helper that invokes it and then performs the
#     INVERSE operation before returning also echoes the same boolean while
#     handing its caller the opposite world. Both are closed by pinning the
#     single-valued state observation holds_lock() AT THE HELPER'S RETURN POINT:
#     acquire must leave the lock IN FORCE whenever it reports True, release must
#     leave it NOT in force. holds_lock() is @Pure @ContractOnly (no impl can
#     compute or echo it) and is driven in BOTH directions by the two primitives,
#     so it is a claim about the state at a program point rather than an
#     accumulating record of operations that once ran. That is what makes the
#     obligation sensitive to WHICH state-moving operation a body performed LAST:
#         - never invoke the primitive        -> cannot ESTABLISH the state (the
#                                                bypass / no-op class below)
#         - invoke it and then reverse it     -> actively FALSIFIES the state (the
#                                                inverse-effect class below)
#     Both classes are exercised below as reject cases, each carrying the
#     refinement that the corresponding real helper hands its caller a lock it
#     does not hold (or keeps one it promised to drop) and so does NOT resolve the
#     F2P. (Directive-8 / control-flow grounding, made STATE-BASED rather than
#     history-based: a monotone "the primitive was invoked at some point" fact is
#     satisfiable by a body that invokes the primitive and then undoes it, which
#     is exactly the hole a reversible observation closes.)
#   * ANSWERABILITY ASYMMETRY (the second closed flank). An exit-state clause pins
#     WHERE the world ends up, but not the ROUTE taken to get there — and one wrong
#     route is observably wrong: a release helper that first ACQUIRES and only then
#     releases ends in exactly gold's state with exactly gold's boolean, yet a
#     blocking acquisition can be left PENDING forever by another holder, so
#     unlock() may never return where gold always does (measured: the F2P's
#     unlock(f1), called while f1 holds LOCK_EX with f2 open, hangs; non-blocking, it
#     raises out of unlock). The two operations differ in the real primitive: an
#     acquisition can be left pending, a release of a held lock cannot. The spec
#     records that by making the acquisition primitive CONSUME the expendable
#     answerable_acquisition() capability while the release helper is handed none.
#     Because the capability is a RESOURCE rather than a proposition, a release body
#     has nothing with which to pay for an acquisition step and cannot obtain the
#     standing by testing for it -- there is no fact to test -- so the pending-step
#     class is rejected; the acquisition helper, whose own report is scoped the same
#     way, spends its one capability on the single acquisition it performs. The same
#     expendability rejects a body that issues REPEATED acquisition requests: the
#     standing for the first is spent on the first. Note the
#     direction of strength: this makes the RELEASE helper's promise UNCONDITIONAL
#     (strictly stronger than before), and it constrains no input value -- both
#     booleans and both control-flow paths of acquire remain live, as the
#     admissibility case demonstrates.
#   * The FAILURE path is an obligation too. acquire's second exit-state clause
#     Implies(Result() is False, holds_lock() == Old(holds_lock())) says a
#     reported failure left the lock state exactly as it was found — the caller
#     told FALSE learns only that it did not get this lock, not that anything it
#     already held was given up. Without it the FALSE branch is unconstrained in
#     the state dimension and a body can pay for its FALSE report by moving the
#     world; the frame-preservation reject case below exercises that path.
#
# NO read-only heap inputs: acquire takes a plain `bool` and release takes NO
# parameters; the only Requires is the abstract lock_state() framing resource,
# which carries NO value information and is threaded unchanged (there is no
# Acc(...,1/2) half-permission input to over-write for an insufficient-permission
# rejection). So the FRAME-MUTATION class is N/A. lock_state() also does not
# narrow the input domain: both boolean inputs to acquire remain admissible (the
# admissibility case below establishes both control-flow paths). Justified in
# 'assessment'. has_readonly_input = False.
from pathlib import Path

INSTANCE = "django__django-13410"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Verbatim gold impl bodies (text between a # impl-start / # impl-end pair in
# model.py). Editing only inside one of these keeps spec_view — hence same_spec
# — byte-identical. Each block is UNIQUE in _BASE so _swap targets it
# unambiguously.
# ---------------------------------------------------------------------------

# --- acquire gold impl (translate control-flow signal to bool) ---
_ACQ_GOLD = """    # impl-start
    try:
        primitive_lock(available)
        return True
    except LockUnavailable:
        return False
    # impl-end"""

# --- release gold impl (held release reports True) ---
_REL_GOLD = """    # impl-start
    primitive_release()
    return True
    # impl-end"""

assert _ACQ_GOLD in _BASE, "anchor drift: acquire gold impl not found verbatim"
assert _REL_GOLD in _BASE, "anchor drift: release gold impl not found verbatim"


# === (1) POSITIVE CONTROL — acquire, structurally different but CORRECT ========
# Local-variable reshape: bind the outcome to a typed local on each control-flow
# path, then return it once at the end (instead of two in-branch returns). The
# verifier still learns `available is True` on the try-normal-path (primitive_lock
# Ensures) and `available is False` on the except-path (Exsures), so result ==
# available on both — Result()==available holds. Same observable behaviour; only
# the executable shape (single exit, local binding) differs. No loops, no fold,
# no induction lemma needed. If a faithful correct impl could NOT verify =>
# SPEC-TOO-STRONG.
_ACQ_POS = """    # impl-start
    # single-exit local-variable reshape (still routes through the primitive's
    # control-flow signal; the success/contention facts are unchanged).
    result = False  # type: bool
    try:
        primitive_lock(available)
        result = True
    except LockUnavailable:
        result = False
    return result
    # impl-end"""

# === (2) POSITIVE CONTROL — release, structurally different but CORRECT ========
# Local-variable reshape of release: call the primitive, bind True to a typed
# local, return the local. Same behaviour; the release postcondition Result() is
# True is satisfied via the local. Must verify, else SPEC-TOO-STRONG on release.
_REL_POS = """    # impl-start
    primitive_release()
    ok = True  # type: bool
    return ok
    # impl-end"""

# === (3) ADMISSIBILITY — the (empty) precondition admits a normal input ========
# acquire has NO Requires (a plain bool is unconditionally admissible) so a
# PRECOND-TOO-STRONG cannot occur; we cannot add a top-level caller (that would
# leave the impl region and break same_spec). Instead, in-region in acquire,
# confirm the call site is admissible: primitive_lock(available) is callable for
# an arbitrary bool input, the try-normal-path is reachable, and on it the
# verifier can DISCHARGE the axiom's Ensures (available is True) — i.e. the
# F2P-shaped reasoning is admitted. If the call site or that fact were
# inadmissible for a normal input this would not verify.
_ACQ_ADMISS = """    # impl-start
    # admissibility: the call site accepts a normal bool input and the
    # success-path fact (available is True) is establishable.
    try:
        primitive_lock(available)
        Assert(available is True)   # from primitive_lock's Ensures on normal path
        return True
    except LockUnavailable:
        Assert(available is False)  # from the Exsures on the contention path
        return False
    # impl-end"""

# === (4) CONTROL-FLOW-EFFECT — acquire bypasses the primitive (reject) =========
# THE primary uniqueness attack on this spec's exposed flank. The helper returns
# the argument WITHOUT ever invoking primitive_lock — a no-op that never takes a
# real lock. The value postcondition Result()==available is trivially satisfied
# by `return available`, so the abstraction alone cannot see the missing
# side-effect. If this VERIFIES it is a true verify-not-resolve break:
# SPEC-TOO-WEAK (control-flow-effect class — the side-effect of actually calling
# fcntl.flock is invisible to the boolean value abstraction).
_ACQ_NOOP = """    # impl-start
    # NO-OP: returns the abstract availability without ever invoking the
    # primitive — never actually acquires (or attempts) the lock.
    return available
    # impl-end"""

# === (5) CONTROL-FLOW-EFFECT — release bypasses the primitive (reject) =========
# release returns True WITHOUT calling primitive_release — never releases the
# real lock. Result() is True is trivially satisfied. If this VERIFIES, the spec
# cannot distinguish a real release from a no-op => SPEC-TOO-WEAK
# (control-flow-effect).
_REL_NOOP = """    # impl-start
    # NO-OP: reports success without ever releasing the held lock.
    return True
    # impl-end"""

# === (6) INVERTED VALUE — acquire reports the opposite outcome (reject) ========
# Swap the two control-flow paths: report a normal completion (lock acquired) as
# False and a contention (lock NOT acquired) as True. On the try-normal-path the
# verifier knows available is True but returns False; Result()==available fails.
# This is the inverse of the faithful translation.
_ACQ_INVERT = """    # impl-start
    try:
        primitive_lock(available)
        return False
    except LockUnavailable:
        return True
    # impl-end"""

# === (7) ALWAYS-FALSE — the literal pre-patch acquire bug (reject) =============
# This is the headline bug: the pre-patch read `ret == 0` off the discarded
# return value, and since a granted request yields the EMPTY VALUE this ALWAYS
# evaluated False — a successful acquisition reported as failure.
# Modelled here as the constant False after invoking the primitive. On the
# normal path available is True but the result is False; Result()==available
# fails. Confirms the spec senses the primary "always returns False" defect.
_ACQ_ALWAYS_FALSE = """    # impl-start
    # the pre-patch bug: `ret == 0` is always False because the success value
    # is the EMPTY VALUE, which answers no such comparison. Modelled here as the
    # constant False, which is what that comparison degenerated to in practice.
    try:
        primitive_lock(available)
        return False
    except LockUnavailable:
        return False
    # impl-end"""

# === (8) ALWAYS-FALSE — the literal pre-patch release bug (reject) =============
# The release sibling of the same bug: `ret == 0` (False -- the value is empty)
# reported as the return. release's postcondition is Result() is True, which the
# constant False cannot satisfy. Confirms the spec senses the release bug
# (model_prepatch_2.py).
_REL_ALWAYS_FALSE = """    # impl-start
    primitive_release()
    # the pre-patch bug: `ret == 0` is always False (the success value is empty).
    return False
    # impl-end"""

# === (9) INVERSE-EFFECT — acquire drops the lock before reporting TRUE (reject) =
# The helper DOES perform the acquisition, then performs the INVERSE operation,
# then reports TRUE. Every value clause is untouched (Result() == available still
# holds) and the acquisition genuinely happened, so any history-flavoured "the
# primitive was invoked" fact is satisfied — this is the case a monotone
# capability token cannot see. It is caught only because the state observation is
# SINGLE-VALUED and REVERSIBLE: the release drives holds_lock() back to False, so
# at the return point Implies(Result() is True, holds_lock()) is FALSIFIED (not
# merely unprovable). If this VERIFIES => SPEC-TOO-WEAK (inverse-effect /
# control-flow-effect: the state the caller is handed is unpinned).
_ACQ_DROPS = """    # impl-start
    # INVERSE EFFECT: takes the lock, then gives it up again, then reports the
    # acquisition as successful — the caller is told it holds a lock it does not.
    try:
        primitive_lock(available)
        primitive_release()
        return True
    except LockUnavailable:
        return False
    # impl-end"""

# === (10) INVERSE-EFFECT — release re-takes the lock before reporting (reject) ==
# The release sibling: perform the release, then re-perform the acquisition, then
# report TRUE. Result() is True is untouched and the release genuinely happened,
# so again a history fact is satisfied; the exit-state clause holds_lock() is
# False is FALSIFIED because the re-acquisition drives the observation back to
# True. If this VERIFIES => SPEC-TOO-WEAK on the release site.
_REL_RETAKES = """    # impl-start
    # INVERSE EFFECT: releases the lock, then takes it again, then reports the
    # release as successful — the caller is told a lock was dropped that is held.
    primitive_release()
    try:
        primitive_lock(True)
    except LockUnavailable:
        pass
    return True
    # impl-end"""

# === (11) FRAME-PRESERVATION — acquire moves the state on its FAILURE path ======
# PARTIAL-DOMAIN shape: on the inputs where the request is granted this body is
# byte-for-byte the gold translation and every clause holds; it differs ONLY
# elsewhere in the precondition's domain — it gives the lock up on the way to
# reporting FALSE. The value clause Result() == available is satisfied on BOTH
# branches, and the success-path exit-state clause is untouched, so only the
# FAILURE-half exit-state clause can see it. If this VERIFIES => SPEC-TOO-WEAK
# (the FALSE branch is unconstrained in the state dimension).
_ACQ_DROPS_ON_FAIL = """    # impl-start
    # FRAME BREAK on the failure path: gives the lock up first, then reports the
    # outcome — a caller told FALSE also silently loses protection it had.
    primitive_release()
    try:
        primitive_lock(available)
        return True
    except LockUnavailable:
        return False
    # impl-end"""

# === (12) PENDING-STEP — release implemented BY ACQUIRING (reject) ==============
# The release helper performs an acquisition first (asserting it is granted) and
# only then releases, reporting TRUE. Every clause of the previous generation of
# this spec holds: the value clause Result() is True is a literal, the release
# genuinely happens LAST so the exit-state clause holds_lock() is False is
# satisfied outright, and the net effect on the lock state is identical to gold.
# What is NOT identical is the PROMISE TO ANSWER. Releasing a lock the caller
# holds is answered unconditionally, but an acquisition is the one operation
# another holder can leave PENDING indefinitely, so this body converts a
# guaranteed answer into a possible indefinite wait. Its faithful refinements
# bear that out: realized as a blocking exclusive request, the F2P's
# `unlock(f1)` (called while f1's own exclusive lock is held and f2 exists)
# HANGS FOREVER; realized non-blocking, the acquisition raises out of the helper
# and `unlock(f1)` propagates the error instead of returning True. Both fail
# test_exclusive_lock, so if this VERIFIES it is a true verify-not-resolve break
# => SPEC-TOO-WEAK (the release helper's unconditional answerability is unpinned;
# the scope obligation the acquisition primitive carries, and which a release
# body has nothing to discharge, is what rejects it).
_REL_ACQUIRES_FIRST = """    # impl-start
    # PENDING STEP: reaches the correct final state, but gets there via an
    # operation another holder can leave pending — so a caller asking to drop a
    # lock it holds can be made to wait for a lock instead.
    primitive_lock(True)
    primitive_release()
    return True
    # impl-end"""

# === (13) VALUE-TRUTHINESS — acquire decides the outcome by TESTING the value ===
# The body performs the real acquisition and then reports the outcome by asking
# whether the value the primitive handed back counts as "set". That is not a
# question the empty value answers, so this body reads an outcome out of
# something that carries none. Under a numeric sentinel this VERIFIES (the number
# either counts as set or does not, and whichever way it falls the body can be
# written to match), which is exactly why no numeric fact is claimed: the axiom
# states only that the value is EMPTY, so the test is not available and the
# reported boolean cannot be derived from the value at all.
_ACQ_VALUE_TRUTHY = """    # impl-start
    # decides the reported outcome by INTERROGATING the returned value instead of
    # observing the control flow.
    try:
        ret = primitive_lock(available)
        if ret:
            return True
        return False
    except LockUnavailable:
        return False
    # impl-end"""

# === (14) VALUE-TRUTHINESS — the release sibling (reject) =======================
# The same defect at the independent release site: report the release by testing
# the value it handed back rather than by the fact that it completed.
_REL_VALUE_TRUTHY = """    # impl-start
    ret = primitive_release()
    if ret:
        return True
    return False
    # impl-end"""

# === (15) VALUE-ORDERING — acquire orders the value against a number (reject) ===
# A different interrogation of the same non-answer: order the returned value
# against zero. The empty value is not ordered against numbers at all, so a real
# helper written this way does not return a wrong boolean — it fails outright
# where the gold helper returns one.
_ACQ_VALUE_ORDER = """    # impl-start
    try:
        ret = primitive_lock(available)
        return ret < 0
    except LockUnavailable:
        return False
    # impl-end"""

# === (16) VACUOUS VALUE INTERROGATION — a tautology on the value (reject) =======
# UNGROUNDED-ORACLE ECHO, and the case that shows why "differs from zero" is not
# enough. This body reports TRUE on the normal path without consulting the
# control flow's meaning at all: it asks the value a question every NUMBER
# answers affirmatively (is it equal to itself / at least itself), so under any
# numeric sentinel it is provable and VERIFIES while doing none of the work. The
# empty value answers no such question, so the body has nothing to stand on.
_ACQ_VALUE_TAUTOLOGY = """    # impl-start
    try:
        ret = primitive_lock(available)
        return ret >= ret
    except LockUnavailable:
        return False
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-control-acquire-single-exit",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_POS),
        "rationale": "Structurally different but correct: acquire reshaped to a "
                     "single exit with a typed local `result` bound on each "
                     "control-flow path (instead of two in-branch returns). The "
                     "verifier still gets `available is True` on the try-normal-path "
                     "(primitive_lock Ensures) and `available is False` on the "
                     "except-path (Exsures), so result == available on both and "
                     "Result()==available holds. Same behaviour, no loop/fold/"
                     "induction. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-release-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _REL_GOLD, _REL_POS),
        "rationale": "release reshaped: call the primitive, bind True to a typed "
                     "local `ok`, return the local. Same observable behaviour; the "
                     "postcondition Result() is True is satisfied via the local. A "
                     "correct re-shaping must verify, else SPEC-TOO-STRONG on "
                     "release.",
    },
    {
        "id": "admissibility-acquire-indomain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_ADMISS),
        "rationale": "In-region in acquire: the call site primitive_lock(available) "
                     "is admissible for a normal bool input and the success-path "
                     "fact (available is True, from the axiom's Ensures) and "
                     "contention-path fact (available is False, from the Exsures) "
                     "are both establishable via Assert. acquire has NO Requires, so "
                     "a plain bool is unconditionally admissible; if the call site "
                     "or those facts were inadmissible for an F2P-shaped input this "
                     "could not verify => PRECOND-TOO-STRONG.",
    },
    {
        "id": "control-flow-effect-acquire-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_NOOP),
        "refinement": "A faithful real patch `def lock(f, flags): return <truthy>` "
                      "that returns without ever calling fcntl.flock NEVER ACQUIRES "
                      "THE LOCK. The F2P tests (test_exclusive_lock, "
                      "test_shared_lock) rely on the lock actually being held: f1 "
                      "takes LOCK_EX, then f2's non-blocking LOCK_EX|LOCK_NB / "
                      "LOCK_SH|LOCK_NB must observe CONTENTION and the helper must "
                      "report False (assertIs(..., False)). A no-op helper that "
                      "returns a constant/echo never makes f1 hold a real lock, so "
                      "f2 would NOT see contention and the assertIs(..., False) "
                      "assertions FAIL — the refined patch does NOT resolve.",
        "rationale": "acquire's value postcondition Result()==available is grounded "
                     "in the argument and is trivially satisfied by `return "
                     "available`; the value clause alone does NOT force the "
                     "primitive to be called. The EFFECT clause "
                     "Implies(Result() is True, lock_held()) closes that flank: on "
                     "the available case the no-op returns True and must therefore "
                     "present lock_held(), but it never called primitive_lock (the "
                     "sole producer) and the token is a body-less predicate that "
                     "cannot be Fold-ed into existence — so this is REJECTED for the "
                     "missing token. If it instead verified => SPEC-TOO-WEAK "
                     "(control-flow-effect). Source: the capability-token EFFECT "
                     "clause grounding the lock-acquisition side-effect.",
    },
    {
        "id": "control-flow-effect-release-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_NOOP),
        "refinement": "A faithful real patch `def unlock(f): return True` that "
                      "never calls fcntl.flock(_fd(f), LOCK_UN) NEVER RELEASES THE "
                      "LOCK. In test_shared_lock the sequence unlock(f1) then "
                      "unlock(f2) — and in real usage a later acquisition — depends "
                      "on the lock actually being dropped; a no-op release leaves "
                      "the kernel lock held, so subsequent lock semantics (and any "
                      "test that re-locks or checks release) break. The helper that "
                      "merely returns True without releasing does NOT resolve the "
                      "intended behaviour.",
        "rationale": "release's value postcondition Result() is True is satisfied by "
                     "the constant `return True`; the value clause alone does NOT "
                     "force primitive_release to be called. The EFFECT clause "
                     "lock_freed() closes that flank: the no-op must present "
                     "lock_freed(), but it never called primitive_release (the sole "
                     "producer) and the token is a body-less predicate that cannot "
                     "be Fold-ed into existence — so this is REJECTED for the missing "
                     "token. If it instead verified => SPEC-TOO-WEAK "
                     "(control-flow-effect). Source: the capability-token EFFECT "
                     "clause grounding the lock-release side-effect.",
    },
    {
        "id": "inverted-value-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_INVERT),
        "refinement": "A faithful real patch that reports a successful acquisition "
                      "as False and a contention as True inverts the contract the "
                      "issue demands: 'a normal completion must never be reported "
                      "as failure'. test_exclusive_lock asserts assertIs(lock(f1, "
                      "LOCK_EX), True) (success) and assertIs(lock(f2, "
                      "LOCK_EX|LOCK_NB), False) (contention); an inverted helper "
                      "returns False for the success and True for the contention, "
                      "FAILING both assertions — the refined patch does NOT resolve.",
        "rationale": "On the try-normal-path the verifier learns available is True "
                     "(primitive_lock Ensures) but the impl returns False, so "
                     "Result()==available fails (True != False). Source: acquire's "
                     "faithful-translation postcondition Result()==available.",
    },
    {
        "id": "always-false-acquire-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_ALWAYS_FALSE),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): "
                      "`ret = fcntl.flock(...); return ret == 0` always returned "
                      "False because fcntl.flock returns None on success and "
                      "the empty value. A helper that always reports False reports every "
                      "successful acquisition as a failure — the headline bug the "
                      "issue files. test_exclusive_lock's assertIs(lock(f1, "
                      "LOCK_EX), True) FAILS, so the refined patch does NOT resolve.",
        "rationale": "On the try-normal-path available is True but the impl returns "
                     "the constant False, so Result()==available fails. This is the "
                     "exact clause model_prepatch.py fails (G-DIFF). Source: "
                     "acquire's Result()==available postcondition; the axiom's "
                     "EMPTY-VALUE clause (Result() is None) makes the spec sense the "
                     "always-False bug.",
    },
    {
        "id": "always-false-release-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_ALWAYS_FALSE),
        "refinement": "This IS the pre-patch release behaviour (model_prepatch_2.py):"
                      " `ret = fcntl.flock(..., LOCK_UN); return ret == 0` always "
                      "returned False (the value is empty), so a successful release was "
                      "reported as failure. test_exclusive_lock / test_shared_lock "
                      "assert assertIs(unlock(f1), True); an always-False release "
                      "FAILS that assertion — the refined patch does NOT resolve.",
        "rationale": "release's postcondition Result() is True cannot be satisfied "
                     "by the constant False (False is True is False). This is the "
                     "clause model_prepatch_2.py fails (G-DIFF). Source: release's "
                     "Result() is True postcondition; the axiom's EMPTY-VALUE clause "
                     "(Result() is None) makes the spec sense the always-False "
                     "release bug.",
    },
    {
        "id": "inverse-effect-acquire-drops-lock",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_DROPS),
        "refinement": "A faithful real patch `def lock(f, flags): try: "
                      "fcntl.flock(_fd(f), flags); fcntl.flock(_fd(f), "
                      "fcntl.LOCK_UN); return True except BlockingIOError: return "
                      "False` DOES perform the real acquisition, and returns "
                      "exactly the boolean the gold helper returns on every "
                      "input — but it drops the lock again on the way out, so its "
                      "caller is handed a lock it does not hold. "
                      "test_exclusive_lock takes f1's LOCK_EX (reported True) and "
                      "then asserts assertIs(lock(f2, LOCK_EX|LOCK_NB), False) and "
                      "assertIs(lock(f2, LOCK_SH|LOCK_NB), False): with f1's lock "
                      "already dropped, f2's non-blocking requests are GRANTED and "
                      "the helper returns True, FAILING both assertions — the "
                      "refined patch does NOT resolve (F2P test_exclusive_lock).",
        "rationale": "This is the case a value clause plus a monotone 'the "
                     "primitive was invoked' fact cannot see: Result() == "
                     "available is untouched and primitive_lock genuinely ran, so "
                     "an accumulating history fact remains derivable after the "
                     "inverse operation. The exit-state clause "
                     "Implies(Result() is True, holds_lock()) is what rejects it: "
                     "holds_lock() is SINGLE-VALUED and primitive_release's "
                     "Ensures(holds_lock() is False) drives it back to False, so at "
                     "the return point the postcondition is FALSIFIED, not merely "
                     "unproven. If it instead verified => SPEC-TOO-WEAK "
                     "(inverse-effect). Source: acquire's exit-state postcondition "
                     "together with the second (release) direction of the state "
                     "observation in the axioms region.",
    },
    {
        "id": "inverse-effect-release-retakes-lock",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_RETAKES),
        "refinement": "A faithful real patch `def unlock(f): fcntl.flock(_fd(f), "
                      "fcntl.LOCK_UN); fcntl.flock(_fd(f), fcntl.LOCK_EX); return "
                      "True` DOES perform the real release and returns the gold "
                      "boolean, but leaves the lock held again on exit, so the "
                      "caller told the lock was dropped still holds it. Any "
                      "subsequent acquisition by another party that must be granted "
                      "after a release is instead refused (and a caller relying on "
                      "unlock to end the critical section keeps the kernel lock "
                      "indefinitely), so the intended release behaviour is not "
                      "achieved.",
        "rationale": "The release sibling of the same hole: Result() is True is "
                     "untouched and primitive_release genuinely ran, so a monotone "
                     "history fact survives. The exit-state clause holds_lock() is "
                     "False rejects it, because the re-acquisition's "
                     "Ensures(holds_lock()) drives the single-valued observation "
                     "back to True at the return point. If it instead verified => "
                     "SPEC-TOO-WEAK (inverse-effect) on the release site. Source: "
                     "release's exit-state postcondition together with the first "
                     "(acquisition) direction of the state observation.",
    },
    {
        "id": "frame-preservation-acquire-drops-on-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_DROPS_ON_FAIL),
        "refinement": "A faithful real patch `def lock(f, flags): "
                      "fcntl.flock(_fd(f), fcntl.LOCK_UN); try: "
                      "fcntl.flock(_fd(f), flags); return True except "
                      "BlockingIOError: return False` returns the gold boolean on "
                      "every input, but it unlocks the descriptor before every "
                      "attempt. In test_exclusive_lock f1 takes LOCK_EX (True), "
                      "then lock(f2, LOCK_EX|LOCK_NB) must be False: the leading "
                      "LOCK_UN is applied to f2 (not f1) so that assertion "
                      "survives — but a caller that re-requests a lock it already "
                      "holds, and any caller whose descriptor is protecting a "
                      "critical section, silently loses that lock on a failed "
                      "attempt. The helper reports 'you did not get the lock' while "
                      "having taken away the one the caller had, which is not the "
                      "behaviour the issue asks for and not what the gold helper "
                      "does (it touches nothing on the failure path).",
        "rationale": "PARTIAL-DOMAIN: identical to gold wherever the request is "
                     "granted, so Result() == available and the success-path "
                     "exit-state clause both hold and neither can see the defect. "
                     "It is rejected by the FAILURE-half exit-state clause "
                     "Implies(Result() is False, holds_lock() == Old(holds_lock())):"
                     " primitive_release's Ensures(holds_lock() is False) moves the "
                     "observation before the attempt, so on an input where the "
                     "caller held the lock the post-state differs from Old(...) "
                     "while the helper returns False. If it instead verified => "
                     "SPEC-TOO-WEAK (the failure path would be free in the state "
                     "dimension). Source: acquire's failure-half exit-state "
                     "postcondition plus the refusal case's own preservation "
                     "clause in the primitive's Exsures.",
    },
    {
        "id": "pending-step-release-acquires-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_ACQUIRES_FIRST),
        "refinement": "A faithful real patch `def unlock(f): fcntl.flock(_fd(f), "
                      "fcntl.LOCK_EX); fcntl.flock(_fd(f), fcntl.LOCK_UN); return "
                      "True` ends in exactly the gold final state (the lock is "
                      "released) and returns the gold boolean, so it is "
                      "indistinguishable from gold in both the value and the "
                      "exit-state dimension. It still does NOT resolve: in "
                      "test_exclusive_lock, unlock(f1) is called while f1 holds "
                      "LOCK_EX and f2 exists on the same file, and the leading "
                      "blocking LOCK_EX request BLOCKS FOREVER -- the test hangs "
                      "instead of asserting True. Realized non-blocking "
                      "(LOCK_EX|LOCK_NB) it raises BlockingIOError out of unlock, so "
                      "assertIs(locks.unlock(f1), True) errors. Measured on the real "
                      "fcntl on real fds: blocking => hang, non-blocking => "
                      "BlockingIOError; both fail test_exclusive_lock while gold "
                      "passes.",
        "rationale": "The flank a pure exit-STATE clause still leaves open: this body "
                     "reaches the right state by the wrong route, so both the value "
                     "clause (a literal True) and the exit-state clause "
                     "(holds_lock() is False, established by the release performed "
                     "LAST) are satisfied, and the net state change equals gold's. "
                     "What differs is the STRENGTH OF THE PROMISE TO ANSWER: a "
                     "release of a held lock is answered unconditionally, whereas an "
                     "acquisition can be left pending indefinitely by another holder. "
                     "The spec makes that asymmetry observable by conditioning the "
                     "acquisition primitive on answerability while the release helper "
                     "carries no such condition -- so a release body has no "
                     "answerability fact to hand to an acquisition step and cannot "
                     "discharge its obligation. If it instead verified => "
                     "SPEC-TOO-WEAK (a release could be implemented by way of a step "
                     "that may never return, which is the hang above). Source: the "
                     "acquisition primitive's answerability precondition together "
                     "with the release helper's deliberately unconditional contract.",
    },
    {
        "id": "value-truthiness-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_VALUE_TRUTHY),
        "refinement": "A faithful real patch `def lock(f, flags): try: ret = "
                      "fcntl.flock(_fd(f), flags); return True if ret else False "
                      "except BlockingIOError: return False` performs the real "
                      "acquisition and leaves the lock in force, so every state "
                      "obligation is met -- but it decides the boolean by testing a "
                      "value that carries no outcome. The real granted request hands "
                      "back the EMPTY value, which does not count as 'set', so the "
                      "helper returns False on a GRANTED acquisition. That is exactly "
                      "the reported defect: test_exclusive_lock's assertIs(lock(f1, "
                      "LOCK_EX), True) FAILS, and test_shared_lock's granted requests "
                      "fail with it -- the refined patch does NOT resolve.",
        "rationale": "THE VALUE-INTERROGATION CLASS, and the reason the axiom claims "
                     "emptiness rather than a number. Every state clause and the "
                     "control-flow structure are gold's; the body differs only in "
                     "deriving the reported boolean FROM THE RETURNED VALUE. Under a "
                     "numeric sentinel this VERIFIES -- the number either counts as "
                     "set or it does not, and the body can be written whichever way "
                     "it falls -- while its refinement reports a granted acquisition "
                     "as failure. It is rejected because the axiom's only value "
                     "obligation is Result() is None: an empty value does not answer "
                     "whether it is 'set', so `if ret` is not a test this body may "
                     "perform and the boolean cannot be derived from the value at "
                     "all. If it verified => SPEC-TOO-WEAK (the outcome would be "
                     "readable off a value that carries none). Source: the "
                     "empty-value clause on the acquisition primitive.",
    },
    {
        "id": "value-truthiness-release",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REL_GOLD, _REL_VALUE_TRUTHY),
        "refinement": "The same defect at the INDEPENDENT release site: `def "
                      "unlock(f): ret = fcntl.flock(_fd(f), fcntl.LOCK_UN); return "
                      "True if ret else False` really does release the lock, but the "
                      "empty value it hands back does not count as 'set', so unlock "
                      "reports False on a SUCCESSFUL release. Both F2P tests assert "
                      "assertIs(locks.unlock(f1), True), so the refined patch does "
                      "NOT resolve.",
        "rationale": "The release sibling, exercised separately because it is a "
                     "separate obligation on a separate operation: release's exit "
                     "state and its unconditional answer are both satisfied, and only "
                     "the value clause can see the defect. Rejected because "
                     "primitive_release's value obligation is Result() is None, so "
                     "the value supports no such test. Source: the empty-value clause "
                     "on the release primitive.",
    },
    {
        "id": "value-ordering-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_VALUE_ORDER),
        "refinement": "A faithful real patch `def lock(f, flags): try: ret = "
                      "fcntl.flock(_fd(f), flags); return ret < 0 except "
                      "BlockingIOError: return False` interrogates the returned value "
                      "by ORDERING it against a number. The real granted request "
                      "hands back the empty value, which is not ordered against "
                      "numbers at all, so the comparison FAILS OUTRIGHT and lock() "
                      "raises where the gold helper returns a boolean -- "
                      "test_exclusive_lock and test_shared_lock both error out. The "
                      "refined patch does NOT resolve.",
        "rationale": "A second, independent interrogation of the same non-answer, "
                     "included because a spec that pinned only 'the value differs "
                     "from zero' would still admit it (ordering is derivable from any "
                     "definite number) while its refinement does not merely return "
                     "the wrong boolean -- it fails to return one. Rejected because "
                     "the axiom claims only emptiness, so the value is not orderable "
                     "and the comparison is unavailable. Source: the empty-value "
                     "clause on the acquisition primitive.",
    },
    {
        "id": "vacuous-value-interrogation-acquire",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ACQ_GOLD, _ACQ_VALUE_TAUTOLOGY),
        "refinement": "A faithful real patch `def lock(f, flags): try: ret = "
                      "fcntl.flock(_fd(f), flags); return ret >= ret except "
                      "BlockingIOError: return False` asks the returned value a "
                      "question every number answers affirmatively. The real empty "
                      "value answers it not at all: the comparison fails outright, so "
                      "lock() raises where the gold helper returns a boolean and both "
                      "F2P tests error out. The refined patch does NOT resolve.",
        "rationale": "UNGROUNDED-ORACLE ECHO on the value axis, and the sharpest "
                     "argument for claiming emptiness rather than any numeric fact: "
                     "this body satisfies the reported-outcome clause on the normal "
                     "path WITHOUT consulting the outcome, because the question it "
                     "asks is one that any definite number answers 'yes' to. So it "
                     "verifies under an exact-value sentinel AND under the weaker "
                     "'differs from zero', and it would keep verifying under any "
                     "numeric model, while its refinement does not return a boolean "
                     "at all. Only an EMPTY value withdraws the question. Rejected "
                     "because Result() is None leaves nothing to interrogate. If it "
                     "verified => SPEC-TOO-WEAK (a tautology on the modelled value "
                     "would stand in for the work). Source: the empty-value clause on "
                     "the acquisition primitive.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the two A-consumed axioms primitive_lock / primitive_release over
# the UNCHANGED callee fcntl.flock.
#
# The bundle carries axiom_check.py (the G-AX real-callee check). To make this
# battery's axiom lane self-standing, the probe below re-derives the SAME
# soundness obligations in-container by EXECUTING the real fcntl.flock (never
# scraping source) on real file descriptors of a temp file, over a fuzz grid of
# acquisition flags + the contention path + the release path. It imports only
# stdlib (fcntl/os/tempfile), opens files for raw fds (no text decode), and
# exits 0 iff every observation matches the axioms.
#
# CONTAINMENT note: primitive_lock / primitive_release have EMPTY Requires (no
# precondition domain restriction), and the model only ever calls
# primitive_lock(available) / primitive_release() — there is no callee-input the
# model can produce that lies outside the axiom domain. So containment is trivial
# and folded into the soundness sweep; the only real axiom obligation is
# soundness (the real callee must satisfy the Ensures/Exsures). On a non-POSIX
# image (no fcntl) the modelled posix branch does not exist => vacuously sound.
# ---------------------------------------------------------------------------

_FLOCK_PROBE = r'''
import os
import sys
import tempfile

# The model claims the primitives' normal-completion value is THE EMPTY VALUE
# (Ensures(Result() is None)). That is what this probe checks on the real callee.


def main():
    try:
        import fcntl
    except ImportError:
        # Non-POSIX: the modelled posix lock branch is not compiled => vacuous.
        print("AX OK (vacuous): fcntl unavailable, posix lock branch absent")
        return 0


    fd_path = None
    try:
        tf = tempfile.NamedTemporaryFile(prefix="dj13410_pbt_", delete=False)
        fd_path = tf.name
        tf.close()

        # === primitive_lock NORMAL completion (lock WAS available) ===========
        # Ensures(Result() is None): the real fcntl.flock returns the EMPTY value
        # on a granted acquisition — so the model's empty-value clause is sound,
        # and (checked below) that value supports no numeric interrogation, which
        # is what the clause is for. Ensures(
        # available is True): a normal completion is reachable here precisely
        # because the lock WAS available (no other holder). Swept across the
        # acquisition flags the F2P tests use, blocking and non-blocking.
        normal_seen = 0
        for flags in (fcntl.LOCK_EX, fcntl.LOCK_EX | fcntl.LOCK_NB,
                      fcntl.LOCK_SH, fcntl.LOCK_SH | fcntl.LOCK_NB):
            with open(fd_path) as f1:
                ret = fcntl.flock(f1.fileno(), flags)
                assert ret is None, (
                    "primitive_lock UNSOUND: real fcntl.flock(%r) returned %r, "
                    "expected the empty value None" % (flags, ret))
                assert ret is None, (
                    "primitive_lock UNSOUND: success value %r is not the empty "
                    "value; the empty-value clause would be unsound" % (ret,))
                # The empty value answers NO numeric interrogation. This is the
                # fact the axiom's emptiness clause exists to preserve: a body
                # cannot read the outcome off this value, because asking it a
                # numeric question is an error rather than an answer.
                for probe in ("order", "arith"):
                    try:
                        if probe == "order":
                            ret < 0
                        else:
                            ret - ret
                    except TypeError:
                        continue
                    raise AssertionError(
                        "primitive_lock UNSOUND: the real success value %r "
                        "answered a numeric interrogation (%s); a numeric "
                        "sentinel would license deciding the reported outcome "
                        "from the value" % (ret, probe))
                assert not ret, (
                    "primitive_lock UNSOUND: the real success value %r counts as "
                    "'set'; a body could then report the outcome by testing it"
                    % (ret,))
                normal_seen += 1
                rel = fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
                assert rel is None and rel != 0
        assert normal_seen == 4

        # === primitive_lock CONTENTION (lock NOT available) ==================
        # Exsures(LockUnavailable, available is False): when the lock is NOT
        # available (another holder owns an incompatible lock), a NON-BLOCKING
        # request does NOT complete normally — it raises OSError (BlockingIOError,
        # EAGAIN/EWOULDBLOCK). The model abstracts that raise as LockUnavailable.
        # This is the bit that makes the contention path of the F2P tests assert
        # assertIs(..., False).
        contention_seen = 0
        for second_flags in (fcntl.LOCK_EX | fcntl.LOCK_NB,
                              fcntl.LOCK_SH | fcntl.LOCK_NB):
            with open(fd_path) as f1, open(fd_path) as f2:
                got = fcntl.flock(f1.fileno(), fcntl.LOCK_EX)
                assert got is None and got != 0, (
                    "setup UNSOUND: first holder's LOCK_EX did not complete "
                    "normally (got %r)" % (got,))
                raised = False
                try:
                    fcntl.flock(f2.fileno(), second_flags)
                except OSError:
                    # BlockingIOError <: OSError; gold catches BlockingIOError,
                    # the issue's patch catches OSError. Both absorb this.
                    raised = True
                assert raised, (
                    "primitive_lock UNSOUND: a non-blocking request (flags=%r) "
                    "for an exclusively-held lock did NOT raise; the contention "
                    "signal Exsures(LockUnavailable) relies on is absent"
                    % (second_flags,))
                contention_seen += 1
                fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
        assert contention_seen == 2

        # === primitive_release NORMAL completion =============================
        # Ensures(Result() is None), NO Exsures: releasing a held lock returns the
        # EMPTY value and does NOT raise.
        with open(fd_path) as f1:
            acq = fcntl.flock(f1.fileno(), fcntl.LOCK_EX)
            assert acq is None and acq != 0
            rel = fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
            assert rel is None, (
                "primitive_release UNSOUND: real fcntl.flock(LOCK_UN) returned "
                "%r, expected None" % (rel,))
            assert not rel, (
                "primitive_release UNSOUND: release value %r counts as 'set'; a "
                "body could then report the outcome by testing it" % (rel,))
            # A second LOCK_UN (idempotent release) also completes normally and
            # does not raise — confirming the no-Exsures clause.
            rel2 = fcntl.flock(f1.fileno(), fcntl.LOCK_UN)
            assert rel2 is None and rel2 != 0

        # === the STATE observation, BOTH directions ===========================
        # Ensures(holds_lock()) on a granted acquisition, the Exsures
        # preservation conjunct holds_lock() == Old(holds_lock()) on a refused
        # one, and Ensures(holds_lock() is False) after a release. Observed the
        # way a third party observes them: a probe descriptor's non-blocking
        # exclusive request is REFUSED while the lock is in force and GRANTED
        # once it has been released. The SECOND direction is what makes the
        # observation reversible rather than monotone, which is what lets the
        # helpers' postconditions speak about the state at the RETURN POINT (a
        # monotone token would need only the first direction and could not tell
        # "acquired" from "acquired then released").
        def probe_in_force(probe):
            try:
                fcntl.flock(probe.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return True
            fcntl.flock(probe.fileno(), fcntl.LOCK_UN)
            return False

        with open(fd_path) as sub, open(fd_path) as other, open(fd_path) as prb:
            assert not probe_in_force(prb), "setup: lock already in force"
            assert fcntl.flock(sub.fileno(), fcntl.LOCK_EX) is None
            assert probe_in_force(prb), (
                "primitive_lock UNSOUND: a granted acquisition did NOT put the "
                "lock in force; Ensures(holds_lock()) fails")
            refused = False
            try:
                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                refused = True
            assert refused, "setup: contended request was granted"
            assert probe_in_force(prb), (
                "primitive_lock UNSOUND: a REFUSED request moved the lock "
                "state; the Exsures preservation conjunct fails")
            assert fcntl.flock(sub.fileno(), fcntl.LOCK_UN) is None
            assert not probe_in_force(prb), (
                "primitive_release UNSOUND: after the release the lock is still "
                "in force; Ensures(holds_lock() is False) fails")

    finally:
        if fd_path is not None and os.path.exists(fd_path):
            os.unlink(fd_path)

    print("AX OK: real fcntl.flock returns THE EMPTY VALUE (which answers no "
          "numeric interrogation and does not count as set) on normal completion for "
          "acquire and release, raises OSError on non-blocking contention, and "
          "moves the lock state in BOTH directions (in force on a granted "
          "acquisition, untouched on a refused one, out of force on release); "
          "primitive_lock / primitive_release axioms sound")
    return 0


sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-primitive-lock-soundness",
        "axiom": "primitive_lock",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _FLOCK_PROBE,
        "rationale": "primitive_lock encodes three obligations on the unchanged "
                     "fcntl.flock the acquisition helper relies on: a NORMAL "
                     "completion yields THE EMPTY VALUE (Ensures Result() is None, "
                     "modelling the real callee's empty return) and is reachable only when "
                     "the lock WAS available (Ensures available is True), and a "
                     "CONTENTION case signals out of band (Exsures LockUnavailable, "
                     "available is False). This probe EXECUTES the real fcntl.flock "
                     "on real fds across the F2P acquisition flags (LOCK_EX/LOCK_SH "
                     "± LOCK_NB), asserts None (!= 0) on a granted acquisition, and "
                     "asserts that a non-blocking request for an exclusively-held "
                     "lock raises OSError. It also probes the STATE clause with a "
                     "third descriptor: the lock is IN FORCE after a granted "
                     "acquisition (Ensures holds_lock()) and UNCHANGED after a "
                     "refused one (the Exsures preservation conjunct "
                     "holds_lock() == Old(holds_lock())). If the real callee "
                     "violated any clause, "
                     "AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX, executed "
                     "self-contained (CALLS the callee, no source scraping).",
    },
    {
        "id": "ax-primitive-release-soundness",
        "axiom": "primitive_release",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _FLOCK_PROBE,
        "rationale": "primitive_release encodes Ensures(Result() is None) "
                     "with NO Exsures: releasing a held lock "
                     "completes normally, yields None (!= 0), and never signals "
                     "contention. The same probe EXECUTES fcntl.flock(fd, LOCK_UN) "
                     "on a real held lock and asserts it returns None (!= 0) without "
                     "raising (including an idempotent second LOCK_UN), and that it "
                     "takes the lock OUT of force (a third descriptor's non-blocking "
                     "exclusive request, refused while the lock was held, is granted "
                     "after the release) -- the second direction that makes the state "
                     "observation REVERSIBLE rather than monotone, hence a claim about "
                     "the state AT a program point. If the real "
                     "release raised, returned 0, or left the lock in force, "
                     "AXIOM-UNSOUND. CONTAINMENT is "
                     "trivial (empty Requires; the model passes no out-of-domain "
                     "input). Mirrors axiom_check.py / G-AX.",
    },
]
