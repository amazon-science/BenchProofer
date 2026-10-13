"""properties.py — PBT falsification battery for django__django-16136.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap) and are checked by Nagini
verify + markers.same_spec. There are NO @ContractOnly axioms in this bundle
(meta.axioms == []); the conditional delivery is modelled DEEPLY and validated
against the real async-def-wrap mechanism by axiom_check.py (G-AX). That
A-reference is a model-fidelity check, not an over-approximation of a library
callee whose Requires-domain we could leave un-contained, so AXIOM_TESTS is a
single soundness probe that re-runs the real coroutine-wrap mechanism (mirroring
axiom_check.py) to keep the deep-model claim under continuous falsification.

DEFENDED SURFACE (why these cases and not byte-fuzz):
  method_not_allowed(async_mode: bool, allowed_methods: List[int]) -> Delivered
  builds the not-allowed reply (a Reply carrying the permitted-method list) and
  delivers it in the convention the view's execution mode requires. Three
  load-bearing postcondition clauses:
    (P1) Result().is_awaitable == async_mode  -- the returned object is an
         awaitable placeholder EXACTLY when the view is async. This is the
         discriminating bug-fix clause (pre-patch always returned the bare
         response; model_prepatch.py = Delivered(False,...) unconditionally and
         FAILS this clause on the async case, G-DIFF).
    (P2) Result().reply.methods is allowed_methods  -- reply-preservation:
         the delivered reply carries the SAME method-list object in BOTH modes
         (deciding the delivery convention must not change which reply is
         delivered). This is an IDENTITY pin (`is`), not a value/contents pin.
    (P3) the permission accounting -- allowed_methods enters and leaves at
         Acc(list_pred(allowed_methods), 1/2) (Required + Ensured): it is a
         READ-ONLY input. has_readonly_input = True.

  GROUNDED ORACLE, no echo (directive 2): P1 pins is_awaitable to the input
  async_mode DIRECTLY (a bool == bool, fully unfolded -- no @Pure answer-key, no
  opaque marker). There is therefore no "wrong echo that nonetheless verifies":
  any impl that satisfies `is_awaitable == async_mode` has already computed the
  correct value, because async_mode is the ground truth. So instead of an
  ungrounded-oracle-echo rival we carry an honest cheapest-correct positive
  control (pos-direct-bool). The genuine uniqueness attacks below all target the
  TWO ways an impl can be wrong while keeping the right SHAPE: get the
  async->awaitable mapping wrong on a sub-domain (P1), or deliver a reply that
  is not the given method list (P2).

  FRAME-MUTATION (directive 5, MANDATORY -- allowed_methods is read-only at
  Acc(...,1/2)): a rival that WRITES to allowed_methods (allowed_methods.append)
  must be REJECTED for INSUFFICIENT PERMISSION (.append needs full
  Acc(list_pred(allowed_methods)); only 1/2 is held). The gold postcondition is
  kept verbatim so the rejection is attributable to the write, not to a value
  divergence. A byte-fuzzer never thinks to mutate the input -- this is the
  project's #1 weakness class.
"""
from pathlib import Path

INSTANCE = "django__django-16136"
FLOAT_ENCODING = None  # meta.float_encoding is null; bool + List[int] carrier, no --float-encoding


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region, anchored on a unique substring so every variant edits
# ONLY inside # impl-start .. # impl-end (guarantees same_spec). The gold body:
#
#     response = Reply(allowed_methods)
#     if async_mode:
#         result = Delivered(True, response)
#     else:
#         result = Delivered(False, response)
#     return result
#
# We surgically replace the if/else delivery block (the discriminating content).
# ---------------------------------------------------------------------------

_GOLD_BLOCK = """    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result"""


def _variant(block):
    return _swap(_BASE, _GOLD_BLOCK, block)


# === POSITIVE CONTROL 1 (soundness) ========================================
# Branch-REORDER: test the SYNC case (not async_mode) first, async in the else.
# Identical values, mirrored control flow. No loop, no fold lemma involved
# (directive 3 N/A here -- the function is loop-free), so this is a pure
# control-flow reshape that keeps every gold proof obligation. Must verify; else
# SPEC-TOO-STRONG.
_POS1_BLOCK = """    response = Reply(allowed_methods)
    if not async_mode:
        result = Delivered(False, response)
    else:
        result = Delivered(True, response)
    return result"""


# === POSITIVE CONTROL 2 (soundness) ========================================
# Local-variable reshape: compute the awaitable flag once into a local (it is
# exactly async_mode) and build the Delivered once, dropping the branch entirely.
# This is the cheapest-correct impl AND the honest grounded-oracle control
# (directive 2): is_awaitable is pinned to the input async_mode, so building it
# straight from async_mode is correct by construction. Must verify.
_POS2_BLOCK = """    response = Reply(allowed_methods)
    flag = async_mode  # type: bool
    result = Delivered(flag, response)
    return result"""


# === POSITIVE CONTROL 3 (soundness) ========================================
# Direct construction with no intermediate local at all: Delivered(async_mode,
# Reply(allowed_methods)). Structurally collapsed (no `result` temp, no `flag`,
# no branch) yet behaviourally identical. Must verify.
_POS3_BLOCK = """    return Delivered(async_mode, Reply(allowed_methods))"""


# === ADMISSIBILITY (precondition not too strong) ===========================
# Inject, at the top of the impl, a concrete F2P-shaped witness: a fresh
# 3-element method-token list (a freshly bound local carries full
# Acc(list_pred(adm))), run it through the whole construction chain
# Reply -> Delivered and Assert the two observable facts. This proves the
# precondition Acc(list_pred(...),1/2) and the Reply/Delivered construction
# admit a normal input (else PRECOND-TOO-STRONG -- e.g. an unsatisfiable
# Requires would make the whole spec vacuous). The real impl then runs unchanged
# over the actual params. (The witness uses a FRESH list, so it never touches
# the read-only allowed_methods permission.)
_ADMISS_BLOCK = """    # admissibility witness (elided from spec view): a concrete F2P-shaped
    # method-token list flows through the real construction chain.
    adm = [200, 201, 202]  # type: List[int]
    adm_reply = Reply(adm)
    adm_del_async = Delivered(True, adm_reply)
    Assert(adm_del_async.is_awaitable == True)
    Assert(adm_del_async.reply.methods is adm)
    adm_del_sync = Delivered(False, adm_reply)
    Assert(adm_del_sync.is_awaitable == False)
    Assert(adm_del_sync.reply.methods is adm)
    # --- end admissibility witness; the real impl follows unchanged ---
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result"""


# === UNIQUENESS / PARTIAL-DOMAIN + FRAME + CONTROL-FLOW rivals (REJECT) =====

# --- weak-always-sync: the PRE-PATCH bug. Always returns the bare response
# (is_awaitable = False) regardless of async_mode. Correct on the sync sub-domain
# (async_mode == False), diverges on the async sub-domain. This is exactly
# model_prepatch.py's behaviour.
_ALWAYS_SYNC_BLOCK = """    response = Reply(allowed_methods)
    result = Delivered(False, response)
    return result"""

# --- weak-always-async: the dual. Always returns an awaitable placeholder
# (is_awaitable = True) regardless of async_mode. Correct on the async sub-domain,
# diverges on the SYNC sub-domain (the common case).
_ALWAYS_ASYNC_BLOCK = """    response = Reply(allowed_methods)
    result = Delivered(True, response)
    return result"""

# --- weak-inverted: flips the mapping (awaitable iff SYNC). Correct on neither
# normal sub-domain; a sign-flip partial-domain rival that still produces a
# well-shaped Delivered.
_INVERTED_BLOCK = """    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(False, response)
    else:
        result = Delivered(True, response)
    return result"""

# --- weak-fresh-reply: keeps the async->awaitable mapping CORRECT (P1 holds) but
# delivers a FRESH reply built from a brand-new empty list instead of the given
# allowed_methods. Defeats any value-only abstraction; rejected only by the
# identity pin P2 (Result().reply.methods is allowed_methods).
_FRESH_REPLY_BLOCK = """    empty = []  # type: List[int]
    bogus = Reply(empty)
    if async_mode:
        result = Delivered(True, bogus)
    else:
        result = Delivered(False, bogus)
    return result"""

# --- frame-mutation: WRITES to the read-only allowed_methods (appends a token)
# before delivering the correct reply. .append needs full Acc(list_pred(
# allowed_methods)); only Acc(...,1/2) is held => MUST reject for INSUFFICIENT
# PERMISSION. The gold delivery (P1/P2) is kept verbatim so the rejection is
# attributable purely to the write, not to a value divergence.
_FRAME_MUT_BLOCK = """    allowed_methods.append(999)
    response = Reply(allowed_methods)
    if async_mode:
        result = Delivered(True, response)
    else:
        result = Delivered(False, response)
    return result"""


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS1_BLOCK),
        "rationale": (
            "branch-REORDER positive control: the SYNC case (not async_mode) is "
            "tested first, the ASYNC case in the else. Identical values, mirrored "
            "control flow; the function is loop-free so no fold/induction lemma is "
            "involved (directive 3 N/A). Keeps both gold postcondition obligations "
            "(P1 is_awaitable==async_mode, P2 reply.methods is allowed_methods). "
            "Must verify; else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-direct-bool",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS2_BLOCK),
        "rationale": (
            "local-variable reshape AND the honest grounded-oracle control "
            "(directive 2): is_awaitable is pinned by P1 to the input async_mode, "
            "so binding flag = async_mode and building Delivered(flag, response) "
            "once -- dropping the branch -- is correct by construction. The "
            "cheapest correct impl; must verify."
        ),
    },
    {
        "id": "pos-collapsed-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS3_BLOCK),
        "rationale": (
            "fully collapsed positive control: return Delivered(async_mode, "
            "Reply(allowed_methods)) with no intermediate `result`/`flag` local "
            "and no branch. Behaviourally identical to gold; a different "
            "executable shape that must still satisfy P1+P2. Must verify; else "
            "SPEC-TOO-STRONG (the spec would be over-constraining the impl shape "
            "rather than the observable behaviour)."
        ),
    },
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS_BLOCK),
        "rationale": (
            "admissibility: a concrete F2P-shaped 3-token method list flows "
            "through the real Reply->Delivered construction chain in both modes "
            "and the two observable facts (is_awaitable, reply.methods identity) "
            "are Asserted. This proves the precondition Acc(list_pred(...),1/2) "
            "and the Reply/Delivered Requires admit a normal input (else "
            "PRECOND-TOO-STRONG / a vacuous Requires). The witness uses a FRESH "
            "list so it never disturbs the read-only allowed_methods permission; "
            "the gold impl follows unchanged. Must verify."
        ),
    },
    # ----- uniqueness / partial-domain rivals (must be rejected) ----------
    {
        "id": "weak-always-sync-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ALWAYS_SYNC_BLOCK),
        "refinement": (
            "this IS the pre-patch behaviour: always return the bare response "
            "(never an awaitable). Its faithful real patch is the PRE-patch code "
            "`return HttpResponseNotAllowed(self._allowed_methods())`, which for "
            "an async view returns a bare HttpResponseNotAllowed that the ASGI "
            "handler then tries to `await`, raising "
            "'object HttpResponseNotAllowed can't be used in await expression' -- "
            "the exact reported bug. test_http_method_not_allowed_responds_"
            "correctly asserts asyncio.iscoroutine(response) is True for AsyncView "
            "and would FAIL. So a verifying rival here is a true verify-but-not-"
            "resolve break."
        ),
        "rationale": (
            "rejected by postcondition P1: Result().is_awaitable == async_mode, "
            "but this rival pins is_awaitable to False unconditionally; on the "
            "async sub-domain (async_mode == True) False != True, so the clause "
            "fails. Rejection comes from the discriminating bug-fix clause P1, not "
            "from shape (a well-formed Delivered is still produced)."
        ),
    },
    {
        "id": "weak-always-async",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_ALWAYS_ASYNC_BLOCK),
        "refinement": (
            "the dual partial-domain rival: always wrap in an awaitable, even for "
            "a SYNC view. Its faithful real patch would `return func()` (a "
            "coroutine) unconditionally; for a SyncView, test_http_method_not_"
            "allowed_responds_correctly asserts asyncio.iscoroutine(response) is "
            "False and would FAIL (the sync handler now hands back an un-awaited "
            "coroutine, which WSGI never resolves -- a regression on the common "
            "sync path). verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by P1: is_awaitable is pinned to True unconditionally; on "
            "the sync sub-domain (async_mode == False) True != False, so "
            "Result().is_awaitable == async_mode fails. The shape (P2) is "
            "untouched -- the rejection is squarely the P1 mapping."
        ),
    },
    {
        "id": "weak-inverted-mapping",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_INVERTED_BLOCK),
        "refinement": (
            "inverts the entire mapping: awaitable iff SYNC. A faithful real patch "
            "with the `if self.view_is_async` guard negated would deliver a "
            "coroutine for sync views and a bare response for async views -- "
            "wrong on BOTH F2P rows (SyncView expects iscoroutine False, AsyncView "
            "expects True), so both subTests of test_http_method_not_allowed_"
            "responds_correctly FAIL. verify-but-not-resolve."
        ),
        "rationale": (
            "rejected by P1 on the entire domain: is_awaitable == (not async_mode) "
            "contradicts Result().is_awaitable == async_mode for every value of "
            "async_mode (True!=False and False!=True). The strongest P1 violation."
        ),
    },
    {
        "id": "weak-fresh-reply-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRESH_REPLY_BLOCK),
        "refinement": (
            "keeps the async->awaitable mapping CORRECT (P1 holds) but delivers a "
            "reply built from a brand-new EMPTY method list rather than the given "
            "allowed_methods. Its faithful real patch would build "
            "HttpResponseNotAllowed([]) (or any list other than "
            "self._allowed_methods()) -- after asyncio.run the F2P test asserts "
            "isinstance(response, HttpResponseNotAllowed) but the delivered Allow "
            "header would be wrong/empty; more sharply, the modeled reply is no "
            "longer the not-allowed response carrying the view's permitted "
            "methods, so the 405 response is malformed. The contents differ AND "
            "the object identity differs from self._allowed_methods(). verify-but-"
            "not-resolve (a value-only abstraction would miss this; the identity "
            "pin catches it)."
        ),
        "rationale": (
            "rejected by postcondition P2: Result().reply.methods is "
            "allowed_methods (object IDENTITY). The rival's reply.methods is the "
            "fresh `empty` list, never `allowed_methods`, so `is` is False and the "
            "clause fails. Rejection comes from the reply-preservation IDENTITY "
            "clause, not from P1 (which this rival deliberately satisfies)."
        ),
    },
    # ----- frame-mutation (read-only input) -- MANDATORY ------------------
    {
        "id": "frame-mutate-allowed-methods",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUT_BLOCK),
        "refinement": (
            "WRITES to the read-only allowed_methods (appends a bogus token) "
            "before delivering an otherwise-correct reply. A faithful real patch "
            "that mutated the list returned by self._allowed_methods() would "
            "corrupt the Allow header of the 405 response (an extra/garbage "
            "method) and, because _allowed_methods builds a fresh sorted list per "
            "call, would at best be a pointless side-effect and at worst leak a "
            "wrong method set into the response the F2P test inspects. The patch "
            "never mutates that list -- it only reads it -- so this rival is "
            "behaviourally divergent and would not faithfully resolve."
        ),
        "rationale": (
            "rejected by the PERMISSION SYSTEM, not a value clause: allowed_"
            "methods is held at Acc(list_pred(allowed_methods), 1/2) (Required + "
            "Ensured -- read-only). `allowed_methods.append(999)` requires full "
            "Acc(list_pred(allowed_methods)); with only 1/2 the call fails for "
            "INSUFFICIENT PERMISSION. The gold delivery (P1+P2) is kept verbatim, "
            "so the rejection is attributable solely to the write. This is the "
            "frame-mutation guard (directive 5) and a byte-fuzzer never finds it."
        ),
    },
]


# ===========================================================================
# AXIOM lane. There are NO @ContractOnly axioms (meta.axioms == []); the only
# deep-model reference is the A-reference conditional delivery, validated by
# axiom_check.py (G-AX) against the REAL async-def-wrap mechanism. There is no
# library callee whose Requires-domain could be left un-contained (the construct
# is pure Python `async def` + asyncio.iscoroutine/run, no flag dependency -- see
# mapping.md S3.1). So there is no axiom-containment obligation here. We DO carry
# one axiom-soundness probe that re-runs the real coroutine-wrap mechanism
# (mirroring axiom_check.py) so the deep-model claim stays under continuous
# falsification: it asserts iscoroutine(returned) == view_is_async and that the
# asyncio.run-resolved reply is the SAME object carrying the given methods, over
# boundary + fuzz inputs -- exactly as the F2P test observes. The probe is
# self-contained stdlib (asyncio + random); it CALLS the real construct (never
# scrapes source) and opens no files (no codec/mount concerns).
# ===========================================================================

_AXIOM_DELIVERY_PROBE = r'''
import asyncio
import random
import sys


class _Reply:
    """Stand-in for HttpResponseNotAllowed: the gold patch does not change the
    response class, only how it is delivered, so a minimal object carrying the
    permitted-method list is faithful."""

    def __init__(self, methods):
        self.methods = methods


def real_method_not_allowed(view_is_async, allowed_methods):
    """Faithful stdlib-only reproduction of the gold patch's delivery logic
    (identical in shape to View.options): build the reply, then deliver it as a
    coroutine iff the view is async, else directly."""
    response = _Reply(allowed_methods)
    if view_is_async:

        async def func():
            return response

        return func()
    else:
        return response


def check_reference(view_is_async, allowed_methods):
    returned = real_method_not_allowed(view_is_async, allowed_methods)

    # fact (i): the returned object is a coroutine (awaitable placeholder) iff
    # the view is async -- exactly what Delivered.is_awaitable == async_mode (P1)
    # encodes and what the F2P test asserts via asyncio.iscoroutine.
    is_coroutine = asyncio.iscoroutine(returned)
    assert is_coroutine == view_is_async, (
        "P1 VIOLATION view_is_async=%r: iscoroutine=%r" % (view_is_async, is_coroutine))

    # resolve the placeholder in the async mode, exactly as the F2P test does.
    if is_coroutine:
        reply = asyncio.run(returned)
    else:
        reply = returned

    # fact (ii)+(iii): the delivered reply is the SAME not-allowed reply carrying
    # the given permitted methods -- Delivered.reply.methods is allowed_methods
    # (P2, an IDENTITY pin). Identity must survive the await.
    assert isinstance(reply, _Reply), (
        "delivered value is not the reply object for view_is_async=%r: %r" % (view_is_async, reply))
    assert reply.methods is allowed_methods, (
        "P2 VIOLATION view_is_async=%r: delivered reply lost its method-list identity" % (view_is_async,))


def main():
    # boundary: both execution modes, with representative method lists (incl.
    # the empty list and a maximal verb set -- the F2P/admissibility shapes).
    boundary_methods = [
        [],
        ["GET"],
        ["GET", "HEAD", "OPTIONS"],
        ["POST"],
        ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    ]
    checked = 0
    for methods in boundary_methods:
        for view_is_async in (False, True):
            check_reference(view_is_async, methods)
            checked += 1

    # randomized fuzz: random async-mode flags and random method lists, trying
    # to make the real mechanism DISAGREE with P1/P2 (it cannot -- coroutine-ness
    # follows from `async def` regardless of payload, and the captured response
    # identity survives asyncio.run).
    rng = random.Random(16136)
    vocab = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"]
    for _ in range(4000):
        view_is_async = bool(rng.getrandbits(1))
        n = rng.randint(0, len(vocab))
        methods = rng.sample(vocab, n)
        check_reference(view_is_async, methods)
        checked += 1

    print("AXIOM OK: A-reference conditional-delivery deep model == the real "
          "async-def-wrap-iff-async mechanism (identical to View.options); "
          "iscoroutine==view_is_async (P1) and resolved-reply identity (P2) hold "
          "on %d boundary+fuzz inputs" % checked)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("AXIOM VIOLATION:", e)
        sys.exit(1)
'''


AXIOM_TESTS = [
    {
        "id": "ax-delivery-coroutine-iff-async",
        "axiom": "method_not_allowed/Delivered (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_DELIVERY_PROBE,
        "rationale": (
            "the bundle has no @ContractOnly axiom; the conditional delivery is "
            "an A-reference deep model. This probe re-runs the REAL async-def-wrap "
            "construct the gold patch uses (mirroring axiom_check.py / G-AX) and "
            "asserts the two facts the deep model encodes -- asyncio.iscoroutine("
            "returned) == view_is_async (P1) and the asyncio.run-resolved reply is "
            "the SAME object carrying the given methods (P2) -- on 10 boundary + "
            "4000 fuzz inputs, observed exactly as the F2P test observes them. If "
            "the real mechanism ever disagreed, the deep model would be unsound. "
            "It CALLS the construct (never scrapes source) and opens no files."
        ),
    },
]
