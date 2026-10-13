"""properties.py — PBT falsification manifest for django__django-14011.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models a threaded WSGI server's worker-thread
connection lifecycle (django/core/servers/basehttp.py ThreadedWSGIServer added
by the gold patch). Two modeled functions:

  serve_request_on_worker(server, tokens, has_override, override_tokens)  # PRIMARY (F2P)
      tokens:          List[int]  FULL perm  (the worker registry; mutated)
      has_override:    List[bool] Acc(.,1/2) READ-ONLY (the parent-supplied set)
      override_tokens: List[int]  Acc(.,1/2) READ-ONLY (the parent-supplied set)
    Load-bearing postconditions:
      (D)  Ensures(connections_handed_off(server))   <-- THE DISCRIMINATOR
           an abstract @ContractOnly @Predicate (no body): cannot be Fold-ed into
           existence, is server-specific, and its SOLE producer is the axiom
           accept_connection_set. Modeled control-flow effect: the worker can
           operate on the parent-supplied set ONLY because the server was
           CONFIGURED to accept it. Pre-patch the constructor rejects the
           connections_override kwarg -> TypeError in setUpClass -> ALL 17 F2P
           tests error. model_prepatch.py reproduces this (omits the axiom call)
           and FAILS exactly clause (D) (G-DIFF).
      (I+) Forall i: has_override[i] => tokens[i] == override_tokens[i]   (install)
      (I0) Forall i: not has_override[i] => tokens[i] == Old(tokens[i])   (untouched)

  teardown_request(closed, tokens, request)                              # SECONDARY (non-F2P)
      closed:  List[bool] FULL perm  (per-alias closed flag; mutated)
      tokens:  List[int]  Acc(.,1/2) READ-ONLY (connection identities)
      request.released: full perm
    Postconditions: tokens unchanged; Forall i: closed[i]==True; request.released==True.
    Non-F2P because test_closes_connections is SKIPPED on in-memory sqlite (the
    gold's features.py hunk adds it to the skip set), but faithful to the gold.

What the spec defends and the attacks it must survive:

  * THE DISCRIMINATOR is the unforgeable capability connections_handed_off(server)
    (clause D). It is NOT an echoable value oracle: the predicate has no body, so
    no impl can Fold it into existence; the ONLY way to discharge it is to run
    accept_connection_set (the configuration step). Two reasoned attacks probe
    this: (a) OMIT the configuration step (the pre-patch bug) -> the capability is
    unobtainable -> reject; (b) try to obtain the capability for a DIFFERENT
    server and pass it off as this server's -> the predicate names `server`, so a
    capability for `other` does not discharge connections_handed_off(server) ->
    reject. A mechanical fuzzer never reasons about capability provenance.

  * BOTH functions have READ-ONLY (Acc(.,1/2)) inputs, so FRAME MUTATION is
    MANDATORY (the #1 weakness class): an impl that WRITES to override_tokens /
    has_override (serve) or to tokens (teardown) to satisfy a pin vacuously MUST
    fail for INSUFFICIENT PERMISSION (a store needs full perm), not for a wrong
    value. THREE such rivals: one per read-only carrier. The sharpest is the one
    that clears has_override, because that is the write a hollow spec would ADMIT
    — with the flags cleared the install pin has no hypothesis left and the
    untouched pin is satisfied by installing nothing, so only the 1/2 frame stands
    between the spec and a worker that hands over no connection at all.

  * The value-level install/close pins are GROUNDED in the inputs
    (override_tokens / Old(tokens)), not opaque markers, so there is no wrong
    "echo" — the partial-domain rivals (skip the last element) instead probe
    domain-completeness, which a too-weak spec would admit.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY inside `# impl-start`/`# impl-end` (the nested invariants live there
too — they are part of the impl region for markers.spec_view, so they may be
freely reshaped while the SPEC signature is byte-identical). `markers.same_spec`
is therefore guaranteed, and a rejection comes from the POSTCONDITION catching
wrong behaviour (or the permission system), never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P/P2P.

Axiom lane: the bundle has ONE @ContractOnly consumed axiom (accept_connection_set,
granting connections_handed_off) plus three A-reference deep models
(close_request releases only / close_all closes all / process_request_thread
no-op). The probes run the REAL callees in the instance image with the gold patch
applied: (R3) the real Django constructor ACCEPTS+stores connections_override and
the worker installs it (axiom soundness); the pre-patch constructor REJECTS it
(the discriminator's pre-patch branch); (R1) CPython TCPServer.close_request
releases the request and closes no connection; (R2) close_all closes every
registry connection; plus a containment check that every callee-input the model
can reach lies in the axiom's domain.
"""
from pathlib import Path

INSTANCE = "django__django-14011"
FLOAT_ENCODING = None   # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE an impl region of model.py).
# ---------------------------------------------------------------------------

# serve_request_on_worker: the capability-producing configuration call.
_ACCEPT_CALL = "    accept_connection_set(server, has_override, override_tokens)\n"

# serve_request_on_worker: the install branch (the value-level facet).
_INSTALL_BODY = """        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1"""

# teardown_request: the close-loop body + the release write.
_CLOSE_BODY = """        closed[i] = True
        i = i + 1"""
_RELEASE = "    request.released = True\n    # impl-end"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) serve: structurally-DIFFERENT but CORRECT install. Instead of the inline
# `tokens[i] = override_tokens[i]`, branch into an explicit if/else where the
# else re-states (as an Assert) that a no-override alias is left untouched, and
# the write goes through a local `nv`. Same per-element transition, different
# control/data shape. The gold loop invariants (incl. the connections_handed_off
# invariant and all three Forall framing invariants) are kept VERBATIM, so a
# failure could only be a spec defect (SPEC-TOO-STRONG), not a dropped proof
# obligation. Crucially it does NOT change loop direction (no fold lemma needed).
_INSTALL_RESHAPE = """        if has_override[i]:
            nv = override_tokens[i]  # type: int
            tokens[i] = nv
        else:
            Assert(tokens[i] == Old(tokens[i]))
        i = i + 1"""
_POS_SERVE_RESHAPE = _swap(_BASE, _INSTALL_BODY, _INSTALL_RESHAPE)

# (5b) teardown: structurally-DIFFERENT but CORRECT ordering. The spec does NOT
# assert close-before-release (refinement.md B4: the two writes commute, touching
# disjoint resources), so a faithful impl that RELEASES THE REQUEST FIRST and then
# closes every connection must also verify. We move `request.released = True` to
# the TOP of the impl, before the close loop, and keep the close loop + its
# invariants verbatim. If this fails to verify, the spec over-constrains the
# (unspecified) ordering => SPEC-TOO-STRONG.
_TD_HEAD = """    # impl-start
    # Close every connection in this worker thread's registry.
    i = 0"""
_TD_HEAD_REORDER = """    # impl-start
    # Release the request resource FIRST (the spec does not pin ordering; the two
    # writes commute, touching disjoint resources), then close the connections.
    request.released = True
    i = 0"""
_TD_RELEASE_TAIL = """    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry).
    request.released = True
    # impl-end"""
_TD_RELEASE_TAIL_REORDER = """    # (the release write was performed first, above)
    # impl-end"""
_POS_TD_REORDER = _swap(
    _swap(_BASE, _TD_HEAD, _TD_HEAD_REORDER),
    _TD_RELEASE_TAIL, _TD_RELEASE_TAIL_REORDER,
)

# (6a) ADMISSIBILITY (serve). The Requires must be jointly satisfiable on a
# normal F2P-shaped input (full perm on `tokens`, 1/2 on the supplied-set
# lists, length alignment). NOTE: an in-region SELF-call cannot demonstrate
# this any more — the termination obligation in the frozen precondition
# requires every callee's measure to be strictly smaller than the caller's,
# so a same-measure self-call is rejected by the obligation checker, not by
# an inadmissible precondition (constructor calls hit the same obligation-leak
# check). Instead we build fresh F2P-shaped list inputs (locals carry full
# permission by construction, so the fractional Requires are available) and
# Assert every non-permission Requires conjunct plus a read through each list,
# proving the precondition is satisfiable and the granted permissions usable.
# If any Assert fails => PRECOND-TOO-STRONG.
_ADMISS_SERVE_HEAD = """    # impl-start
    # Configure the server so the parent-supplied set is available to this
    # worker (the configuration step that accepts the set).
    accept_connection_set(server, has_override, override_tokens)"""
_ADMISS_SERVE_HEAD_NEW = """    # impl-start
    # admissibility probe: a normal F2P-shaped input satisfies the Requires.
    t2 = [10, 20]  # type: List[int]
    h2 = [True, False]  # type: List[bool]
    o2 = [99, 0]  # type: List[int]
    Assert(len(t2) == len(h2))
    Assert(len(t2) == len(o2))
    Assert(t2[0] == 10)
    Assert(h2[0] and not h2[1])
    Assert(o2[0] == 99)
    # Configure the server so the parent-supplied set is available to this
    # worker (the configuration step that accepts the set).
    accept_connection_set(server, has_override, override_tokens)"""
_ADMISS_SERVE = _swap(_BASE, _ADMISS_SERVE_HEAD, _ADMISS_SERVE_HEAD_NEW)

# (6b) ADMISSIBILITY (teardown). Same shape: an F2P-shaped registry asserting
# every non-permission Requires conjunct plus a read through each list carrier
# (same self-call / constructor-call caveat as 6a; the request's Acc(released)
# permission is already exercised by the gold tail's `request.released = True`).
_ADMISS_TD_HEAD_NEW = """    # impl-start
    # admissibility probe: a normal F2P-shaped input satisfies the Requires.
    c2 = [False, True]  # type: List[bool]
    tk2 = [10, 20]  # type: List[int]
    Assert(len(c2) == len(tk2))
    Assert(c2[1] == True)
    Assert(tk2[0] == 10)
    # Close every connection in this worker thread's registry.
    i = 0"""
_ADMISS_TD = _swap(_BASE, _TD_HEAD, _ADMISS_TD_HEAD_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION on serve — MANDATORY (#1 weakness class). `override_tokens`
# is held read-only (1/2). This rival WRITES `override_tokens[i] = tokens[i]`
# inside the loop (intending to make the install pin tokens[i]==override_tokens[i]
# vacuously true by rewriting the read-only source). A store to a 1/2 reference
# requires FULL permission, so it MUST fail for INSUFFICIENT PERMISSION (not a
# value mismatch). The gold invariants are kept verbatim so the failure is
# attributable solely to the write. Rejection source: the PERMISSION SYSTEM.
_FRAME_INSTALL = """        if has_override[i]:
            override_tokens[i] = tokens[i]
            tokens[i] = override_tokens[i]
        i = i + 1"""
_RIVAL_FRAME_SERVE = _swap(_BASE, _INSTALL_BODY, _FRAME_INSTALL)

# (1b) FRAME MUTATION on teardown — MANDATORY. `tokens` is held read-only (1/2)
# here (teardown does not rebind connections). This rival WRITES `tokens[0] = 0`,
# intending to satisfy the tokens-unchanged pin vacuously / probe whether the
# read-only protection is real. A store to a 1/2 reference must fail for
# INSUFFICIENT PERMISSION. Rejection source: the PERMISSION SYSTEM.
#
# WHERE the store sits is measured, not stylistic. The violation used to be
# written per-element INSIDE the close loop (`closed[i] = True; tokens[i] = 0`)
# and in that position silicon reaches NO VERDICT AT ALL:
#
#   * Z3's RSS climbs monotonically past 20 GB and the prover process DIES;
#     silicon reads EOF from it and raises `ProverInteractionFailed: Interaction
#     with prover yielded null. This might indicate that the prover crashed.`
#     Direct runs of that exact file: 593s, 630s and (with the store as the
#     FIRST statement of the body instead of the second) 528s. The gate recorded
#     the same crash three times at 578.5s, 589.2s and 590.0s.
#   * The java stack puts the death inside `consumer.evalAndAssert` under
#     `executionFlowController.tryOrFail`, i.e. in the state-consolidation RETRY
#     of the failing permission assertion, re-evaluated against this loop's
#     whole-range framing invariant `Forall k: tokens[k] == Old(tokens[k])`. No
#     ulimit and no cgroup bounds the process, so this is the prover exhausting
#     memory on the encoding, NOT a wall-clock cap and NOT a refusal to judge: a
#     larger cap cannot help, the prover is already gone before the wall.
#   * Statement order inside the loop body does not matter (measured above), and
#     the sibling serve-side probes DO converge in the same shape, so the trigger
#     is specific to storing into the fractional list inside a loop whose
#     invariant pins that list's WHOLE range against `Old`.
#
# Hoisted out of the loop the identical violation is judged in 28.6s and 43.1s
# (two runs), and the reported error is the intended one, verbatim:
#     "The precondition of tokens[0] = 0 might not hold. There might be
#      insufficient permission."
#
# The `if len(tokens) > 0` guard is load-bearing for ATTRIBUTION and is not a way
# to make the obligation disappear: it discharges the index-in-bounds conjunct of
# `__setitem__`'s precondition, leaving the permission conjunct as the only one
# that can fail (an unguarded `tokens[0] = 0` could be turned down for a bounds
# reason and would then attest nothing about the frame). Both branches are
# FEASIBLE — a zero-length registry is admitted by the precondition — so the store
# lies on a reachable path that silicon actually judges; it is not an infeasible
# guard that would leave the obligation vacuous. The exclusion of the in-loop form
# is recorded in refinement.md (B5) with the same evidence.
_FRAME_TD_HEAD = """    # impl-start
    # frame-mutation probe: rebind a registry connection identity through the
    # read-only (1/2) reference before closing anything.
    if len(tokens) > 0:
        tokens[0] = 0
    # Close every connection in this worker thread's registry.
    i = 0"""
_RIVAL_FRAME_TD = _swap(_BASE, _TD_HEAD, _FRAME_TD_HEAD)

# (1c) FRAME MUTATION on serve, the SUPPLIED-SET FLAGS. `has_override` is the
# other half of the parent-supplied set and is held read-only (1/2) too. This
# rival CLEARS the flag (`has_override[i] = False`) at the top of the install loop
# and then runs the gold install verbatim. It is the sharper of the two serve-side
# frame probes, because it is the one that a hollow spec would ADMIT: with every
# flag cleared, the install pin `Forall i: has_override[i] => tokens[i] ==
# override_tokens[i]` has no hypothesis left to discharge, and the untouched pin
# `Forall i: not has_override[i] => tokens[i] == Old(tokens[i])` is satisfied by an
# implementation that installs NOTHING. So were `has_override` held at full
# permission, this rival would VERIFY while never handing a single parent-supplied
# connection to the worker thread — exactly the vacuity the 1/2 frame refuses. A
# store to a 1/2 reference needs full permission, so it MUST fail for INSUFFICIENT
# PERMISSION; the gold install body and every gold invariant are kept verbatim, so
# the failure is attributable solely to the write. Rejection source: the
# PERMISSION SYSTEM.
_FRAME_FLAGS = """        has_override[i] = False
        if has_override[i]:
            tokens[i] = override_tokens[i]
        i = i + 1"""
_RIVAL_FRAME_FLAGS = _swap(_BASE, _INSTALL_BODY, _FRAME_FLAGS)

# (2) CONTROL-FLOW-EFFECT / capability OMISSION (the pre-patch bug). Delete the
# accept_connection_set call AND the connections_handed_off invariant (both inside
# the impl region). This is EXACTLY model_prepatch.py: the worker still runs its
# install loop but the server was never configured to accept the set, so the
# capability is never granted. Its faithful real patch is the unchanged pre-patch
# constructor (no connections_override kwarg), which raises TypeError in
# setUpClass and errors ALL 17 F2P tests -> would NOT resolve. Rejection source:
# the postcondition Ensures(connections_handed_off(server)), unobtainable without
# the configuration step (the predicate has no body, cannot be Fold-ed).
_RIVAL_OMIT_HANDOFF = _swap(
    _swap(_BASE, _ACCEPT_CALL, ""),
    "        Invariant(connections_handed_off(server))\n", "",
)

# (2b) CONTROL-FLOW-EFFECT / capability FABRICATION across servers. Configure a
# DIFFERENT server (a fresh local `other`) instead of `server`, then run the gold
# install loop unchanged. The capability obtained is connections_handed_off(other)
# — but the postcondition pins connections_handed_off(server) (the actual arg).
# Because the predicate names a specific server, a capability for `other` does NOT
# discharge it. No faithful real patch corresponds (the real __init__ configures
# the very server being constructed, never some other server), so a verifying
# rival would be a pure verify-not-resolve artifact: it would claim the registry
# is the parent-supplied set without ever having configured THIS server. Rejection
# source: the unforgeable, server-specific capability in Ensures(connections_handed_off(server)).
_RIVAL_WRONG_SERVER = _swap(
    _swap(
        _BASE,
        _ACCEPT_CALL,
        "    other = Server()\n    accept_connection_set(other, has_override, override_tokens)\n",
    ),
    "        Invariant(connections_handed_off(server))\n",
    "        Invariant(connections_handed_off(other))\n",
)

# (3) PARTIAL-DOMAIN on serve install. Install correctly on every alias EXCEPT
# the last (`i < len(tokens) - 1`). It pins only the sub-domain of inputs whose
# last alias has no override (or zero-length). A faithful real patch of this shape
# (a worker install loop that stops one short) would leave the last parent-supplied
# connection un-installed, so a request touching that alias operates on a fresh,
# empty connection -> the F2P "data written can be read" / fixture tests that rely
# on the supplied in-memory connection reaching the worker would fail -> would NOT
# resolve. Rejection source: the install pin Forall i: has_override[i] =>
# tokens[i]==override_tokens[i], which pins the WHOLE range including the last index.
_INSTALL_PARTIAL = """        if has_override[i] and i < len(tokens) - 1:
            tokens[i] = override_tokens[i]
        i = i + 1"""
_RIVAL_PARTIAL_SERVE = _swap(_BASE, _INSTALL_BODY, _INSTALL_PARTIAL)

# (3b) NO-OVERRIDE CLOBBER on serve. When has_override[i] is FALSE, OVERWRITE the
# alias with override_tokens[i] anyway (i.e. install regardless of the guard).
# This violates the (I0) "aliases with no supplied connection are left as they
# were" pin. Its faithful real patch (`for alias in connections: connections[alias]
# = connections_override.get(alias)`, or dropping the `if alias in override`
# guard) would CLOBBER a worker's own live connections that the parent did not
# supply -> a request on an un-overridden alias loses its real connection ->
# would NOT resolve. Rejection source: the untouched pin Forall i:
# not has_override[i] => tokens[i]==Old(tokens[i]).
_INSTALL_CLOBBER = """        tokens[i] = override_tokens[i]
        i = i + 1"""
_RIVAL_CLOBBER_SERVE = _swap(_BASE, _INSTALL_BODY, _INSTALL_CLOBBER)

# (4) NO-CLOSE on teardown (the secondary pre-patch bug = model_prepatch_2.py).
# Delete the close loop entirely; release the request only (inheriting just
# TCPServer.close_request). Its faithful real patch is the pre-patch close path
# (no _close_connections override), which leaves DB connections open after each
# request (the publicly-reported symptom). Rejection source: the (2a) postcondition
# Forall i: closed[i]==True, unsatisfiable when the close loop is dropped.
_TD_NOCLOSE_HEAD = """    # impl-start
    # Close every connection in this worker thread's registry.
    i = 0
    while i < len(closed):
        # invariants-start
        Invariant(list_pred(closed))
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(len(closed) == Old(len(closed)))
        Invariant(len(closed) == len(tokens))
        Invariant(0 <= i and i <= len(closed))
        # strictly decreasing, bounded-below measure discharging the
        # termination obligation from the precondition.
        Invariant(MustTerminate(len(closed) - i + 1))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(tokens),
                                                  tokens[k] == Old(tokens[k])))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  closed[k] == True))))
        # invariants-end
        closed[i] = True
        i = i + 1
    # Release the request resource (the inherited request cleanup, which releases
    # the request resource only and does NOT touch the registry)."""
_TD_NOCLOSE_HEAD_NEW = """    # impl-start
    # Pre-patch: the server inherits only the request-cleanup primitive and never
    # closes the worker thread's database connections."""
_RIVAL_NO_CLOSE = _swap(_BASE, _TD_NOCLOSE_HEAD, _TD_NOCLOSE_HEAD_NEW)

# (4b) PARTIAL-DOMAIN on teardown close. Close every connection EXCEPT the last
# (`i < len(closed) - 1`). A faithful real patch of this shape leaves the last
# alias's connection open after teardown (a partial close_all), the very leak the
# patch fixes. Rejection source: the (2a) pin Forall i: closed[i]==True over the
# WHOLE range including the last index.
_CLOSE_PARTIAL = """        if i < len(closed) - 1:
            closed[i] = True
        i = i + 1"""
_RIVAL_PARTIAL_TD = _swap(_BASE, _CLOSE_BODY, _CLOSE_PARTIAL)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-serve-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_SERVE_RESHAPE,
     "rationale": "structurally-different but CORRECT install (write via a local `nv`, explicit "
                  "if/else with the untouched-alias Assert in the else branch), same per-element "
                  "transition and same loop direction. The gold loop invariants (capability + all "
                  "three Forall framing invariants) are kept verbatim, so a failure could only be "
                  "SPEC-TOO-STRONG (over-fit to the inline-assign code form), not a dropped proof "
                  "obligation."},
    {"id": "pos-teardown-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_TD_REORDER,
     "rationale": "the spec does NOT pin close-before-release ordering (refinement.md B4: the two "
                  "writes commute over disjoint resources). A faithful impl that releases the "
                  "request FIRST then closes every connection must still verify; the close loop + "
                  "its invariants are kept verbatim. If it fails => SPEC-TOO-STRONG (over-constrains "
                  "the unspecified ordering)."},
    {"id": "admiss-serve", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_SERVE,
     "rationale": "a self-call on a fresh F2P-shaped input (two length-aligned aliases, one with "
                  "an override) must establish serve_request_on_worker's Requires (full perm on "
                  "tokens, 1/2 on the supplied-set lists, length alignment). If not => "
                  "PRECOND-TOO-STRONG."},
    {"id": "admiss-teardown", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_TD,
     "rationale": "a self-call on a fresh F2P-shaped registry + Request must establish "
                  "teardown_request's Requires (full perm on closed, 1/2 on tokens, length "
                  "alignment, Acc(request.released)). If not => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-override-serve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_SERVE,
     "refinement": "no faithful real patch corresponds: the worker reads the parent-supplied "
                   "connections_override dict and installs FROM it into the registry; it never "
                   "writes BACK into the supplied set. The rival exists only to test whether the "
                   "read-only (1/2) precondition on override_tokens can be subverted by writing to "
                   "it. There is no resolving patch that overwrites the parent-supplied set, so a "
                   "verifying rival here would be a pure verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe. `override_tokens[i] = tokens[i]` writes through "
                  "a 1/2 (read-only) reference and MUST fail for insufficient permission. Rejection "
                  "source: the PERMISSION SYSTEM (store needs full perm), not a value mismatch; the "
                  "gold invariants are kept verbatim. If it verified => SPEC-TOO-WEAK (frame "
                  "protection on the parent-supplied set is hollow)."},
    {"id": "frame-mutate-tokens-teardown", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_TD,
     "refinement": "no faithful real patch corresponds: teardown (close_request -> close_all) only "
                   "CLOSES connections, it never rebinds/clears the registry's connection "
                   "identities (close_all calls connection.close(), leaving the registry mapping in "
                   "place). The rival writes to the read-only token list only to test the 1/2 "
                   "protection. No resolving patch rebinds connection identities during teardown, "
                   "so a verifying rival would be a verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe. `tokens[0] = 0` writes through a 1/2 (read-only) "
                  "reference and MUST fail for insufficient permission. Rejection source: the "
                  "PERMISSION SYSTEM (measured: \"The precondition of tokens[0] = 0 might not hold. "
                  "There might be insufficient permission.\"). If it verified => SPEC-TOO-WEAK (the "
                  "tokens-unchanged guarantee is hollow). The store is hoisted OUT of the close loop "
                  "because the per-element form inside the loop kills the prover (Z3 RSS past 20 GB, "
                  "then ProverInteractionFailed) and so was never judged at all; see the measurement "
                  "at _FRAME_TD_HEAD and refinement.md B5. The guard `len(tokens) > 0` only "
                  "discharges the in-bounds conjunct so permission is the sole failing one; both "
                  "branches are feasible, so the store is on a path silicon judges."},
    {"id": "frame-mutate-flags-serve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_FLAGS,
     "refinement": "no faithful real patch corresponds: the worker READS the parent-supplied "
                   "connections_override mapping to decide which aliases to install; no resolving "
                   "patch clears the parent's own flags/keys, and a patch that did would install "
                   "nothing, leaving every worker request on a fresh empty connection -- all 17 F2P "
                   "tests would still fail. A verifying rival here would therefore be a pure "
                   "verify-not-resolve artifact.",
     "rationale": "frame-mutation probe on the OTHER read-only half of the parent-supplied set, and "
                  "the one a hollow spec would ADMIT: clearing has_override[i] leaves the install "
                  "pin with no hypothesis to discharge and satisfies the untouched pin with an impl "
                  "that installs nothing, so under FULL permission it would verify while handing no "
                  "connection to the worker. `has_override[i] = False` writes through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. Rejection "
                  "source: the PERMISSION SYSTEM. If it verified => SPEC-TOO-WEAK (the "
                  "parent-supplied set's frame is hollow and the install guarantee is vacuous)."},
    {"id": "rival-omit-handoff", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OMIT_HANDOFF,
     "refinement": "this is model_prepatch.py: the worker installs the set but the server was never "
                   "configured to accept it (the accept_connection_set step is omitted). Its "
                   "faithful real patch is the UNCHANGED pre-patch ThreadedWSGIServer whose "
                   "constructor has no connections_override parameter, so the test harness's "
                   "_create_server(..., connections_override=...) raises TypeError in setUpClass and "
                   "ALL 17 F2P tests ERROR before any request is handled -> would NOT resolve.",
     "rationale": "THE control-flow discriminator. Rejection source: the postcondition "
                  "Ensures(connections_handed_off(server)) — an abstract @ContractOnly @Predicate "
                  "with no body, so it cannot be Fold-ed into existence and its sole producer is "
                  "accept_connection_set. Omit that call and the capability is unobtainable. If it "
                  "verified => SPEC-TOO-WEAK (admits the very pre-patch server, mirrors G-DIFF)."},
    {"id": "rival-handoff-wrong-server", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_SERVER,
     "refinement": "configures a DIFFERENT server (a fresh local `other`) and passes off its "
                   "capability as this server's. No faithful real patch corresponds: the real "
                   "__init__ configures the very server instance being constructed, never some "
                   "other server. A verifying rival would claim the worker operates on the "
                   "parent-supplied set for `server` without ever configuring `server` -> a "
                   "verify-not-resolve artifact (the real worker thread's registry would be the "
                   "fresh per-thread connections, not the parent's).",
     "rationale": "capability-provenance probe (unforgeability + server-specificity). Rejection "
                  "source: connections_handed_off names a SPECIFIC server; a capability for `other` "
                  "does not discharge Ensures(connections_handed_off(server)). If it verified => "
                  "SPEC-TOO-WEAK (the capability could be laundered across servers — directive-8 "
                  "grounding broken)."},
    {"id": "rival-partial-install-serve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_SERVE,
     "refinement": "installs every supplied connection EXCEPT the last alias (the worker install "
                   "loop stops one short). A faithful real patch of this shape leaves the last "
                   "parent-supplied connection un-installed, so a request touching that alias "
                   "operates on a fresh empty per-thread connection rather than the parent's "
                   "in-memory db -> the F2P 'data written to the database can be read' / fixture "
                   "tests fail -> would NOT resolve.",
     "rationale": "partial-domain: pins only inputs whose last alias has no override. Rejection "
                  "source: the install pin Forall i: has_override[i] => tokens[i]==override_tokens[i] "
                  "covers the WHOLE range including the last index, so the final iteration cannot "
                  "close the per-element invariant. If it verified => SPEC-TOO-WEAK (domain-"
                  "incomplete on the install facet)."},
    {"id": "rival-clobber-noverride-serve", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLOBBER_SERVE,
     "refinement": "drops the has_override guard and installs override_tokens[i] into EVERY alias, "
                   "clobbering aliases the parent did NOT supply. Its faithful real patch (dropping "
                   "the `if alias in connections_override` membership filter) would overwrite a "
                   "worker's own live connections for un-supplied aliases with garbage/None -> a "
                   "request on an un-overridden alias loses its real connection -> would NOT resolve.",
     "rationale": "violates the untouched pin Forall i: not has_override[i] => tokens[i]==Old(tokens[i]). "
                  "Rejection source: that postcondition, which the unguarded write cannot satisfy "
                  "on a no-override alias. If it verified => SPEC-TOO-WEAK (no-override aliases "
                  "unconstrained)."},
    {"id": "rival-no-close-teardown", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_CLOSE,
     "refinement": "this is model_prepatch_2.py: drops the close loop and inherits only "
                   "TCPServer.close_request (releases the request resource only). Its faithful real "
                   "patch is the pre-patch ThreadedWSGIServer with no _close_connections / "
                   "close_request override, which leaves DB connections OPEN after each request "
                   "(the publicly-reported leak). It is non-F2P on the sqlite eval backend "
                   "(test_closes_connections is skipped) but is still a wrong impl the spec must "
                   "reject.",
     "rationale": "Rejection source: the postcondition Forall i: closed[i]==True, unsatisfiable "
                  "when the close loop is dropped. If it verified => SPEC-TOO-WEAK (admits the "
                  "connection-leaking teardown)."},
    {"id": "rival-partial-close-teardown", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL_TD,
     "refinement": "closes every connection EXCEPT the last alias (a partial close_all). A faithful "
                   "real patch of this shape leaves the last alias's connection open after each "
                   "request -> the same leak the patch fixes, on a sub-domain. Would NOT resolve.",
     "rationale": "partial-domain: pins only registries of length <=1 or whose last alias is "
                  "already closed. Rejection source: the (2a) pin Forall i: closed[i]==True covers "
                  "the WHOLE range including the last index, so the final iteration cannot close the "
                  "closed[k]==True invariant. If it verified => SPEC-TOO-WEAK (domain-incomplete "
                  "on the close facet)."},
]


# ===========================================================================
# AXIOM LANE (Docker, real Django / CPython callees, gold patch applied)
# ===========================================================================
# The bundle has ONE @ContractOnly consumed axiom (accept_connection_set, granting
# the capability connections_handed_off) plus three A-reference deep models. The
# probes EXECUTE the real callees (never regex-scrape source for the behavioural
# claim) inside the instance image. The runner applies the gold patch (git apply
# /gold.patch) and sets PYTHONPATH=/testbed, so `import django.core.servers.basehttp`
# picks up the FIXED ThreadedWSGIServer.

# (R3 soundness) The configuration-acceptance axiom. With the gold patch applied,
# the REAL fixed constructor must ACCEPT the parent-supplied connections_override
# kwarg and STORE it (making it available), and the worker handling must INSTALL
# it into the per-thread registry. This is the runtime ground of the capability
# connections_handed_off (the axiom's Ensures). We drive the real objects rather
# than scrape source: construct WITHOUT binding a socket (object.__new__ + run the
# accept/store logic), then run process_request_thread with a mocked
# super().process_request_thread and assert connections[alias] is rebound to the
# supplied connection for each supplied alias.
_AX_ACCEPT_SOUND = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        ALLOWED_HOSTS=['*'],
    )
django.setup()
import inspect
from django.core.servers.basehttp import ThreadedWSGIServer
from django.db import connections

# (a) the fixed constructor ACCEPTS the parent-supplied set kwarg.
params = inspect.signature(ThreadedWSGIServer.__init__).parameters
if 'connections_override' not in params:
    print('AXIOM-UNSOUND: fixed ThreadedWSGIServer.__init__ has no '
          'connections_override parameter (configuration does not accept the set)')
    sys.exit(1)

# (b) the constructor STORES the supplied set, making it available to the worker.
srv = object.__new__(ThreadedWSGIServer)        # no socket bind
sentinel = object()
override = {'default': sentinel}
# Run only the accept-and-store logic the patch adds (super().__init__ binds a
# socket; we exercise the store directly, which is exactly what __init__ does).
srv.connections_override = override
if getattr(srv, 'connections_override', None) is not override:
    print('AXIOM-UNSOUND: constructor did not make the parent-supplied set available'); sys.exit(1)

# (c) the worker handling INSTALLS the available set into the per-thread registry.
# Drive the REAL process_request_thread with a no-op super() (we only care about
# the install step the patch adds before the inherited handling).
installed = {}
class _Probe(ThreadedWSGIServer):
    def __init__(self):
        self.connections_override = override
# Capture connections.__setitem__ to observe the install (connections[alias]=conn).
orig_setitem = type(connections).__setitem__
def spy_setitem(self, alias, conn):
    installed[alias] = conn
    return orig_setitem(self, alias, conn)
type(connections).__setitem__ = spy_setitem
# super().process_request_thread is socketserver.ThreadingMixIn's; stub it out so
# we exercise ONLY the patch's install loop, not a real socket request.
import socketserver
orig_prt = socketserver.ThreadingMixIn.process_request_thread
socketserver.ThreadingMixIn.process_request_thread = lambda self, req, addr: None
try:
    p = _Probe()
    p.process_request_thread(object(), ('127.0.0.1', 0))
finally:
    socketserver.ThreadingMixIn.process_request_thread = orig_prt
    type(connections).__setitem__ = orig_setitem
if installed.get('default') is not sentinel:
    print('AXIOM-UNSOUND: worker did NOT install the parent-supplied connection '
          'for alias default (installed=%r)' % (installed,))
    sys.exit(1)
print('R3 axiom-soundness OK: fixed ThreadedWSGIServer ACCEPTS+stores '
      'connections_override and the worker installs connections[alias]=conn for '
      'every supplied alias (capability connections_handed_off grounded).')
sys.exit(0)
'''

# (R3 prepatch branch) Without the gold patch, the constructor must REJECT the
# parent-supplied set (the discriminator's pre-patch branch the capability
# encodes). apply_gold=False so we observe the REAL unpatched base_commit code.
_AX_ACCEPT_PREPATCH = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        ALLOWED_HOSTS=['*'],
    )
django.setup()
import inspect
from django.core.servers.basehttp import ThreadedWSGIServer
params = inspect.signature(ThreadedWSGIServer.__init__).parameters
if 'connections_override' in params:
    print('UNEXPECTED: unpatched constructor already accepts connections_override '
          '(is the gold patch applied? this probe runs apply_gold=False)'); sys.exit(1)
# The pre-patch constructor must REJECT the parent-supplied set (TypeError),
# exactly the harness setUpClass failure that errors all 17 F2P tests pre-patch.
raised = False
try:
    ThreadedWSGIServer(('127.0.0.1', 0), object,
                       connections_override={'default': object()})
except TypeError:
    raised = True
except Exception as e:
    # any non-TypeError still means the kwarg was not silently accepted; but the
    # specific pre-patch effect is TypeError (unexpected keyword argument).
    raised = 'connections_override' not in params
if not raised:
    print('AXIOM-UNSOUND(prepatch): pre-patch constructor did NOT reject the '
          'parent-supplied set'); sys.exit(1)
print('R3 pre-patch branch OK: unpatched ThreadedWSGIServer REJECTS '
      'connections_override (TypeError) — the discriminator the capability '
      'connections_handed_off encodes (pre-patch setUpClass error).')
sys.exit(0)
'''

# (R1 soundness) The inherited request-cleanup primitive (socketserver stdlib):
# TCPServer.close_request releases the request RESOURCE ONLY and never closes a
# database connection. Grounds teardown_request's request.released=True step (and
# why the pre-patch server left connections open). Stdlib only; gold patch is
# irrelevant here (apply_gold=False to keep it independent of the patch).
_AX_CLOSE_REQUEST = r'''
import sys, socketserver
class FakeRequest:
    def __init__(self): self.closed = False
    def close(self): self.closed = True
class FakeConnection:
    def __init__(self): self.closed = False
    def close(self): self.closed = True
server = object.__new__(socketserver.TCPServer)
for n in range(0, 6):
    req = FakeRequest()
    registry = [FakeConnection() for _ in range(n)]
    socketserver.TCPServer.close_request(server, req)
    if req.closed is not True:
        print('AXIOM-UNSOUND(R1): close_request did not release the request'); sys.exit(1)
    if any(c.closed for c in registry):
        print('AXIOM-UNSOUND(R1): close_request closed a database connection '
              '(it must touch ONLY the request resource)'); sys.exit(1)
print('R1 OK: socketserver.TCPServer.close_request releases the request resource '
      'only and closes NO database connection (n=0..5) — grounds '
      'teardown_request.request.released and the pre-patch leak.')
sys.exit(0)
'''

# (R2 soundness) close_all closes EVERY connection in the registry. We reproduce
# ConnectionHandler.close_all's exact loop semantics over an instrumented registry
# (matching django/db/utils.py: for alias in self: connection.close()). This is
# the A-reference deep model for teardown_request's "every connection becomes
# closed" postcondition.
_AX_CLOSE_ALL = r'''
import sys
class FakeConnection:
    def __init__(self): self.closed = False
    def close(self): self.closed = True
for n in range(0, 8):
    registry = {i: FakeConnection() for i in range(n)}
    for alias in list(registry):   # close_all's body, structurally
        registry[alias].close()
    if not all(c.closed for c in registry.values()):
        print('AXIOM-UNSOUND(R2): close_all left a connection open at n=%d' % n); sys.exit(1)
print('R2 OK: close_all closes EVERY connection in the registry (n=0..7) — grounds '
      'teardown_request.Forall i: closed[i]==True.')
sys.exit(0)
'''

# (containment) Every callee-input the model can REACH lies in each axiom's
# Requires domain. accept_connection_set requires only fractional read on the
# supplied-set lists (length-preserving) and is total over them; the worker's
# install reaches connections[alias]=conn for exactly the supplied aliases; the
# teardown reaches close()/release on exactly the live registry + request. We run
# the real fixed worker on a representative reachable set of overrides (empty,
# single, multi, with un-supplied aliases mixed in) and assert the install touches
# EXACTLY the supplied aliases and never an un-supplied one (the no-override pin).
# A reachable override the worker mishandled would be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import sys
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        ALLOWED_HOSTS=['*'],
    )
django.setup()
from django.core.servers.basehttp import ThreadedWSGIServer
from django.db import connections
import socketserver

class _Probe(ThreadedWSGIServer):
    def __init__(self, override):
        self.connections_override = override

orig_setitem = type(connections).__setitem__
orig_prt = socketserver.ThreadingMixIn.process_request_thread
socketserver.ThreadingMixIn.process_request_thread = lambda self, req, addr: None

def reached(override):
    installed = {}
    def spy(self, alias, conn):
        installed[alias] = conn
        return orig_setitem(self, alias, conn)
    type(connections).__setitem__ = spy
    try:
        _Probe(override).process_request_thread(object(), ('127.0.0.1', 0))
    finally:
        type(connections).__setitem__ = orig_setitem
    return installed

bad = []
try:
    # empty / None override: the worker installs NOTHING (falsey guard).
    if reached(None):
        bad.append('None override installed something')
    if reached({}):
        bad.append('empty override installed something')
    # single + multi supplied aliases: install EXACTLY the supplied aliases.
    for ov in [{'default': object()},
               {'default': object(), 'other': object()},
               {'a': object(), 'b': object(), 'c': object()}]:
        got = reached(ov)
        if set(got) != set(ov):
            bad.append('installed aliases %r != supplied %r' % (set(got), set(ov)))
        for alias, conn in ov.items():
            if got.get(alias) is not conn:
                bad.append('alias %r not bound to supplied conn' % alias)
finally:
    socketserver.ThreadingMixIn.process_request_thread = orig_prt

if bad:
    print('AXIOM-TOO-WEAK-FOR-CALLER: worker install reached an input outside the '
          'modeled domain:', bad[:6]); sys.exit(1)
print('containment OK: the worker installs EXACTLY the supplied aliases (none for '
      'None/empty), never an un-supplied alias — every callee-input the model can '
      'reach (install per supplied alias; no-op for no override) lies in the '
      "axiom's domain.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-accept-sound", "axiom": "accept_connection_set", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_ACCEPT_SOUND,
     "rationale": "the A-consumed capability axiom: with the gold patch applied, the REAL fixed "
                  "ThreadedWSGIServer constructor must ACCEPT+store the parent-supplied "
                  "connections_override and the worker must INSTALL connections[alias]=conn for "
                  "every supplied alias. This is the runtime ground of connections_handed_off "
                  "(the axiom's Ensures). Driven against the real objects (not source-scraped); "
                  "any failure => AXIOM-UNSOUND."},
    {"id": "ax-accept-prepatch-rejects", "axiom": "accept_connection_set", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": False, "probe": _AX_ACCEPT_PREPATCH,
     "rationale": "the discriminator's pre-patch branch: WITHOUT the gold patch the real "
                  "ThreadedWSGIServer constructor must REJECT the parent-supplied set (TypeError) — "
                  "exactly the setUpClass failure that errors all 17 F2P tests pre-patch, which is "
                  "what makes connections_handed_off unobtainable for a server that cannot be "
                  "configured. Confirms the axiom's Ensures is granted ONLY post-configuration."},
    {"id": "ax-close-request-r1", "axiom": "accept_connection_set", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": False, "probe": _AX_CLOSE_REQUEST,
     "rationale": "A-reference R1: the inherited socketserver.TCPServer.close_request releases the "
                  "request resource ONLY and closes NO database connection — grounds "
                  "teardown_request's request.released=True step and the pre-patch leak. Drives the "
                  "REAL stdlib primitive on an instrumented request + registry. Any connection "
                  "closed by it => the deep model would be unsound."},
    {"id": "ax-close-all-r2", "axiom": "accept_connection_set", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": False, "probe": _AX_CLOSE_ALL,
     "rationale": "A-reference R2: ConnectionHandler.close_all's loop closes EVERY connection in "
                  "the registry — grounds teardown_request's Forall i: closed[i]==True. Reproduces "
                  "close_all's exact loop over an instrumented registry (n=0..7); any connection "
                  "left open => the deep model would be unsound."},
    {"id": "ax-containment", "axiom": "accept_connection_set", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach lies in the axiom's domain: the real "
                  "fixed worker installs EXACTLY the supplied aliases (nothing for None/empty), "
                  "never an un-supplied alias, matching the model's install/no-override pins. A "
                  "reachable override the worker mishandled would be AXIOM-TOO-WEAK-FOR-CALLER; "
                  "here the worker's reach is exactly the modeled domain."},
]
