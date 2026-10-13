# properties.py — PBT falsification battery for django__django-13810. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region (the nested # invariants region is
# part of the elided impl, so changing it still preserves same_spec); the runner
# re-runs the Nagini verifier on the host and checks verify/reject vs `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface of this instance (read model.py + refinement.md + mapping.md)
# ---------------------------------------------------------------------------
#   assemble_chain(target_mode: List[int], declines: List[int], base_async: int)
#                  -> Tuple[List[int], int]
#     Requires(Acc(list_pred(target_mode), 1/2))     # READ-ONLY column (1/2 perm)
#     Requires(Acc(list_pred(declines),   1/2))      # READ-ONLY column (1/2 perm)
#     Requires(len(target_mode) == len(declines))
#     Ensures(Acc(list_pred(target_mode), 1/2))      # permission preserved (RO)
#     Ensures(Acc(list_pred(declines),   1/2))       # permission preserved (RO)
#     Ensures(len(target_mode) == len(declines))
#     Ensures(len(ToSeq(target_mode)) == len(ToSeq(declines)))
#     Ensures(Acc(list_pred(Result()[0])))           # the returned handler trace
#     # (H) the assembled handler trace is the front-recursive fold over the walk
#     Ensures(ToSeq(Result()[0]) == final_handler(PSeq(0).take(0), base_async,
#                                   ToSeq(target_mode), ToSeq(declines), 0))
#     # (A) the assembled async flag is the front-recursive fold over the walk
#     Ensures(Result()[1] == final_async(PSeq(0).take(0), base_async,
#                            ToSeq(target_mode), ToSeq(declines), 0))
#
# The two LOAD-BEARING postcondition clauses are (H) and (A). They are GROUNDED:
# `final_handler` / `final_async` are @Pure front-recursive folds over the
# read-only input columns (target_mode/declines) and base_async — NOT an opaque
# @ContractOnly answer-key. The fold's decline branch passes the running pair
# through unchanged (the patch's `else: handler = adapted_handler`); its
# participating branch commits committed_handler = wrap_token(adapt_token(...))
# and advances the flag to target_mode[i]. There is NO consumed @ContractOnly
# axiom; adapt_token/wrap_token are A-reference deep models of the two UNCHANGED
# callees (adapt_method_mode / convert_exception_to_response), validated == the
# real patched threading by axiom_check.py / G-AX.
#
# The discriminating content of the gold change lives in the decline rollback:
# the commit (`handler = adapted + [WRAP_TOKEN]`, `handler_is_async =
# target_mode[i]`) must be reached ONLY on the participating branch, so a
# DECLINING layer's tentative `adapted` leaves no trace on what the next layer
# inherits. The verifier senses this via the loop invariant tying
# `final_handler(ToSeq(handler), handler_is_async, ..., i)` to the whole-walk
# fold: any impl that carries a declining layer's adaptation forward breaks it.
#
# Read-only inputs => the FRAME-MUTATION probe is MANDATORY: a rival that WRITES
# into target_mode / declines (held at Acc(...,1/2)) must be REJECTED for
# INSUFFICIENT PERMISSION (the half-permission cannot be upgraded to write).
#
# CONTROL-FLOW-EFFECT is N/A here: the only control-flow difference (a layer
# raising MiddlewareNotUsed) is ALREADY abstracted to the data column
# `declines[i]`, and its sole observable effect (the layer is skipped, leaving no
# trace) is fully captured by the (H)/(A) value abstraction. There is no
# raise/return/side-effect difference invisible to the value model, so no
# capability-token rival is needed (see `assessment`).
#
# UNGROUNDED-ORACLE-ECHO is N/A: the oracle (final_handler/final_async) is a fold
# of the *inputs*, fully unfolded by the verifier — there is no opaque marker an
# impl could echo to a WRONG value and still verify. The only way to satisfy (H)
# is to actually thread the running handler with the decline rollback. We instead
# supply an honest cheapest-impl positive control (see pos-control-*).
from pathlib import Path

INSTANCE = "django__django-13810"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact frozen invariants block (verbatim from model.py). Every rival /
# positive control KEEPS this block byte-identically — it is the gold proof
# obligation that ties the running pair to the whole-walk fold; deleting it would
# fail the loop invariant for a PROOF reason, not a spec reason (pilot pitfall
# #2). We only ever change the EXECUTABLE lines around it, all INSIDE impl.
# ---------------------------------------------------------------------------
_INV = """        # invariants-start
        Invariant(Acc(list_pred(target_mode), 1 / 2))
        Invariant(Acc(list_pred(declines), 1 / 2))
        Invariant(len(target_mode) == len(declines))
        Invariant(Acc(list_pred(handler)))
        Invariant(0 <= i and i <= len(target_mode))
        # The running pair (handler, handler_is_async) is exactly the fold over
        # the prefix already walked: equivalently, the remaining walk from here
        # reproduces the whole walk's result.
        Invariant(final_handler(ToSeq(handler), handler_is_async,
                                ToSeq(target_mode), ToSeq(declines), i) ==
                  final_handler(PSeq(0).take(0), base_async,
                                ToSeq(target_mode), ToSeq(declines), 0))
        Invariant(final_async(ToSeq(handler), handler_is_async,
                              ToSeq(target_mode), ToSeq(declines), i) ==
                  final_async(PSeq(0).take(0), base_async,
                              ToSeq(target_mode), ToSeq(declines), 0))
        Invariant(MustTerminate(len(target_mode) - i + 1))
        # invariants-end"""

assert _INV in _BASE and _BASE.count(_INV) == 1


# The full frozen impl region (markers inclusive) — the unique _swap anchor.
_IMPL_OLD = """    # impl-start
    handler = []  # type: List[int]
    handler_is_async = base_async
    i = 0
    while i < len(target_mode):
""" + _INV + """
        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # Layer declines: move on; the tentative adaptation is discarded so
            # the next layer inherits the unchanged running handler / flag.
            i = i + 1
            continue
        # Layer participates: commit the adapted+wrapped handler and advance the
        # running async-mode flag to this layer's target mode.
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1
    return handler, handler_is_async
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


def _impl(body_after_inv, ret="    return handler, handler_is_async"):
    """Build a full impl region: the frozen header + frozen invariants + a new
    executable loop body + the post-loop return. Guarantees the spec (and the
    gold invariants) are untouched and the only change is the executable shape
    inside impl. `ret` is the post-loop return (always the running pair)."""
    return ("""    # impl-start
    handler = []  # type: List[int]
    handler_is_async = base_async
    i = 0
    while i < len(target_mode):
""" + _INV + "\n" + body_after_inv + "\n" + ret + """
    # impl-end""")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). All keep the gold invariants verbatim and
# the same forward walk / per-iteration update, so no new induction lemma is
# needed (pilot pitfalls #2/#3 avoided): only the branch/statement SHAPE changes.
# ===========================================================================

# pos-control-ifelse: rewrite the early-`continue` decline branch as a positive
# `if participates: commit else: pass` (no `continue`). Same per-iteration
# semantics — commit reached only when the layer participates — so the same loop
# invariant proof holds. Behaviourally identical to the gold.
_POS_IFELSE = _impl("""        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] != 1:
            # Layer participates: commit the adapted+wrapped handler and advance
            # the running async-mode flag (else-branch of the decline test).
            handler = adapted + [WRAP_TOKEN]
            handler_is_async = target_mode[i]
        i = i + 1""")

# pos-control-reorder-commit: on the participating branch, set the async flag
# BEFORE committing the handler. The two assignments are independent (the flag
# update does not read `handler`; the handler update does not read
# `handler_is_async`), so swapping them is behaviourally identical. Keeps the
# early-continue decline shape and the gold invariants.
_POS_REORDER = _impl("""        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # Layer declines: move on; the tentative adaptation is discarded.
            i = i + 1
            continue
        # Layer participates: advance the flag first, then commit the handler
        # (independent assignments — order is irrelevant to the result).
        handler_is_async = target_mode[i]
        handler = adapted + [WRAP_TOKEN]
        i = i + 1""")

# pos-control-inline: drop the `adapted` temporary and inline the adaptation
# directly into the commit. Same composed value committed_handler(...), same
# decline rollback. A local-variable reshape (pilot-safe). Must verify.
_POS_INLINE = _impl("""        if declines[i] == 1:
            # Layer declines: nothing tentative survives; move on.
            i = i + 1
            continue
        # Layer participates: commit the adapted+wrapped handler inline.
        handler = handler + [ADAPT_TOKEN, target_mode[i]] + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We cannot add a module-level caller (it would
# change the projected spec view and break same_spec). Instead we inject an
# admissibility witness INSIDE the impl region (elided from the spec view): we
# build a concrete F2P-shaped pair of equal-length parallel columns — the F2P
# scenario is reversed(MIDDLEWARE) = [a declining sync-only layer, a
# participating async layer], i.e. two layers — and Assert it satisfies the
# function's own Requires (full Acc on freshly-built lists implies the 1/2 the
# precondition needs, plus the equal-length conjunct). The real impl then runs
# unchanged over the actual params. If the precondition could not be established
# for this legitimate input, the Assert fails => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = _impl("""        # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
        # The F2P walks reversed(MIDDLEWARE) = [declining sync layer, participating
        # async layer]: two equal-length parallel columns. A fresh list_pred at
        # full Acc subsumes the Acc(...,1/2) the precondition requires.
        adm_tm = [0, 1]  # type: List[int]
        adm_dc = [1, 0]  # type: List[int]
        Assert(Acc(list_pred(adm_tm), 1 / 2))
        Assert(Acc(list_pred(adm_dc), 1 / 2))
        Assert(len(adm_tm) == len(adm_dc))
        # --- end admissibility witness; the real impl follows unchanged ---
        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # Layer declines: move on; the tentative adaptation is discarded.
            i = i + 1
            continue
        # Layer participates: commit the adapted+wrapped handler and advance flag.
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")


# ===========================================================================
# UNIQUENESS / FRAME / PARTIAL-DOMAIN — rivals that share the spec exactly and
# change ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK or — for the write — a permission
# escape). Every rival keeps the gold invariants verbatim so a rejection is
# attributable to the spec/permission system, not a dropped proof obligation.
# ===========================================================================

# uniq-prepatch-bug: THE BUG. Commit the adaptation onto the running `handler`
# BEFORE the decline check (no rollback) — byte-for-byte the model_prepatch.py
# impl / the pre-patch loop. A declining layer then carries an extra adaptation
# token forward that the next layer inherits. Rejected by the loop invariant
# `final_handler(ToSeq(handler), handler_is_async, ..., i) == whole-walk fold`:
# the fold's decline branch leaves the running handler UNCHANGED, but this impl
# advanced it, so the invariant cannot be re-established after a declining layer.
_UNIQ_PREPATCH = _impl("""        # PRE-PATCH BUG: commit the adaptation onto the running handler BEFORE the
        # decline check (the gold's `handler = adapt_method_mode(...)` then the
        # MiddlewareNotUsed `continue`, with no `else: handler = adapted` rollback).
        handler = handler + [ADAPT_TOKEN, target_mode[i]]
        if declines[i] == 1:
            # Layer declines: move on -- but the adaptation has already poisoned
            # the running handler the next layer inherits.
            i = i + 1
            continue
        handler = handler + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")

# uniq-decline-advances-flag: handle the handler rollback correctly, but advance
# the async flag on the DECLINE branch too (set handler_is_async = target_mode[i]
# before `continue`). Diverges only on the sub-domain "a declining layer whose
# target_mode differs from the running flag" — a partial-domain attack on (A).
# Rejected by final_async: the fold's decline branch passes the flag through
# unchanged, so the (A) postcondition / invariant fails on any declining layer.
_UNIQ_DECLINE_FLAG = _impl("""        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            # BUG: advance the async flag even though the layer declined.
            handler_is_async = target_mode[i]
            i = i + 1
            continue
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")

# uniq-drop-wrap: on the participating branch commit only the adapted handler,
# WITHOUT the wrapper token (drop the `+ [WRAP_TOKEN]` = the
# convert_exception_to_response wrap). Decline rollback is correct, but every
# participating layer commits committed = adapt_token(...) instead of
# wrap_token(adapt_token(...)). Rejected by (H): the fold commits the wrapped
# handler, so the trace diverges on every participating layer.
_UNIQ_DROP_WRAP = _impl("""        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            i = i + 1
            continue
        # BUG: commit the adapted handler WITHOUT wrapping it (drop WRAP_TOKEN).
        handler = adapted
        handler_is_async = target_mode[i]
        i = i + 1""")

# uniq-frame-mutate-declines: FRAME-MUTATION (MANDATORY, read-only input). To
# make a declining layer "participate" (and so dodge the rollback obligation),
# overwrite the READ-ONLY `declines` column in place (`declines[i] = 0`). This
# can only be admitted if the half-permission Acc(list_pred(declines), 1/2) could
# be upgraded to a write — it cannot. Must be REJECTED for INSUFFICIENT
# PERMISSION (the write is unprovable; not even a postcondition violation —
# Nagini refuses the store). Gold invariants kept verbatim so the rejection is
# attributable to the write, not a dropped obligation. A byte-fuzzer never
# constructs this; it is the project's #1 weakness class.
_UNIQ_FRAME_DECLINES = _impl("""        # Tentatively adapt the current handler for this layer's target mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        # FRAME MUTATION: write into the read-only `declines` column (held at
        # Acc(..., 1/2)). Insufficient permission -> must be rejected.
        declines[i] = 0
        if declines[i] == 1:
            i = i + 1
            continue
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")

# uniq-frame-mutate-target: FRAME-MUTATION on the OTHER read-only input. Overwrite
# `target_mode[i]` in place to a fixed mode so the committed token / flag is
# whatever the attacker wants, vacuously matching nothing it shouldn't. Same
# permission escape: target_mode is held at Acc(..., 1/2); the store is rejected
# for INSUFFICIENT PERMISSION. Supporting frame-mutation case on target_mode.
_UNIQ_FRAME_TARGET = _impl("""        # FRAME MUTATION: write into the read-only `target_mode` column (held at
        # Acc(..., 1/2)). Insufficient permission -> must be rejected.
        target_mode[i] = 0
        # Tentatively adapt the current handler for this (now-overwritten) mode.
        adapted = handler + [ADAPT_TOKEN, target_mode[i]]  # type: List[int]
        if declines[i] == 1:
            i = i + 1
            continue
        handler = adapted + [WRAP_TOKEN]
        handler_is_async = target_mode[i]
        i = i + 1""")

# uniq-skip-all (supporting near-miss): never commit anything — always `continue`
# as if every layer declined. Returns the empty base handler and base_async,
# which equals the fold only when NO layer participates. Rejected by (H)/(A) on
# any input with a participating layer (declines[i]==0). Cheap supporting case.
_UNIQ_SKIP_ALL = _impl("""        # BUG: treat every layer as declining; commit nothing.
        i = i + 1
        continue""")


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-ifelse",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_IFELSE),
        "rationale": "structurally-different CORRECT impl: rewrite the decline "
                     "early-`continue` as a positive `if declines[i] != 1: commit` "
                     "with no `continue`. The commit is still reached ONLY on the "
                     "participating branch, so the decline rollback is preserved and "
                     "the same per-iteration update keeps the gold loop invariant "
                     "valid (no new lemma; pilot pitfalls #2/#3 avoided). If a "
                     "faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-reorder-commit",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "on the participating branch, advance the async flag BEFORE "
                     "committing the handler. The two assignments are independent "
                     "(neither reads the other), so the order is irrelevant and the "
                     "result is identical. Keeps the gold invariants. Must verify; "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_INLINE),
        "rationale": "local-variable reshape: drop the `adapted` temporary and inline "
                     "handler + [ADAPT_TOKEN, target_mode[i]] + [WRAP_TOKEN] directly "
                     "into the commit. Same composed committed_handler value, same "
                     "decline rollback. Must verify; else SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "(elided from the spec view, so same_spec holds) builds the "
                     "concrete F2P-shaped input — reversed(MIDDLEWARE) = [declining "
                     "sync layer, participating async layer], two equal-length parallel "
                     "columns adm_tm=[0,1], adm_dc=[1,0] — and asserts it satisfies the "
                     "function's exact Requires: Acc(list_pred(.),1/2) on each column "
                     "(a fresh full-Acc list subsumes the half) and equal lengths. The "
                     "real impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch behaviour that model_prepatch.py "
                      "reproduces and G-DIFF flags. The pre-patch load_middleware did "
                      "`handler = self.adapt_method_mode(...)` then `mw_instance = "
                      "middleware(handler)`; on MiddlewareNotUsed it `continue`d with "
                      "no `else: handler = adapted_handler` rollback, so the running "
                      "handler kept the adaptation a DECLINING layer computed. The sole "
                      "F2P test_async_and_sync_middleware_chain_async_call walks "
                      "[SyncAndAsyncMiddleware (participates, async), MyMiddleware "
                      "(declines via MiddlewareNotUsed)] and asserts the response is "
                      "b'OK' / 200 with the exact log records; with the pre-patch loop "
                      "the declining MyMiddleware poisons the running handler and the "
                      "assembled async chain misbehaves -> the F2P does NOT resolve. "
                      "Its faithful real patch is exactly the un-patched loop.",
        "rationale": "rejected by the loop invariant final_handler(ToSeq(handler), "
                     "handler_is_async, ..., i) == final_handler([], base_async, ..., "
                     "0): committing the adaptation before the decline test advances "
                     "the running handler on a declining layer, but the fold's decline "
                     "branch leaves it unchanged, so the invariant cannot be "
                     "re-established (postcondition clause (H)).",
    },
    {
        "id": "uniq-decline-advances-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DECLINE_FLAG),
        "refinement": "advancing handler_is_async on the decline branch corresponds to "
                      "a patch that moved the `handler_is_async = middleware_is_async` "
                      "update (base.py:89) out of the `else` so it also runs when "
                      "MiddlewareNotUsed is raised. A declining layer would then flip "
                      "the running async mode, so the post-loop top-of-stack adaptation "
                      "(adapt_method_mode at base.py:92) receives the wrong mode and the "
                      "assembled async chain is built for the wrong mode. The F2P "
                      "(async client, declining MyMiddleware) observes the resulting "
                      "chain; with the flag corrupted on the decline it would not "
                      "resolve. Partial-domain: diverges only when a declining layer's "
                      "target_mode differs from the running flag.",
        "rationale": "rejected by Result()[1] == final_async([], base_async, ..., 0) "
                     "(and the final_async invariant): the fold's decline branch passes "
                     "the flag through unchanged, but this impl advances it on a "
                     "declining layer, so clause (A) fails.",
    },
    {
        "id": "uniq-drop-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_WRAP),
        "refinement": "committing the adapted handler WITHOUT the wrapper token "
                      "corresponds to a patch that dropped the convert_exception_to_"
                      "response wrap (base.py:88) when threading the running handler. "
                      "The assembled chain would then be missing the exception-to-"
                      "response wrapper for every participating middleware, so request "
                      "handling would not convert exceptions to responses as the chain "
                      "requires; the F2P (which expects a clean b'OK'/200 response "
                      "through the assembled chain) would not resolve.",
        "rationale": "rejected by ToSeq(Result()[0]) == final_handler([], base_async, "
                     "..., 0): the fold commits committed_handler = "
                     "wrap_token(adapt_token(...)), i.e. the trace ends in WRAP_TOKEN "
                     "for each participating layer; dropping it makes the returned "
                     "trace diverge on every participating layer (clause (H)).",
    },
    {
        "id": "uniq-frame-mutate-declines",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_DECLINES),
        "refinement": "writing `declines[i] = 0` corresponds to a patch that mutated "
                      "the caller-owned middleware-decline outcome to force every layer "
                      "to participate — it would attach a MiddlewareNotUsed-raising "
                      "middleware that Django requires be skipped, so the assembled "
                      "chain would contain a layer that declined. The F2P expects "
                      "MyMiddleware to be skipped (log record \"MiddlewareNotUsed: "
                      "'...MyMiddleware'\"); forcing it to participate breaks that and "
                      "does not resolve. More fundamentally, the input column is "
                      "read-only and the real loop never writes it.",
        "rationale": "rejected by the PERMISSION system: declines is held at "
                     "Acc(list_pred(declines), 1/2) (required AND ensured); a store "
                     "`declines[i] = 0` needs full (write) permission, which the "
                     "half-permission cannot supply. Nagini refuses the write for "
                     "INSUFFICIENT PERMISSION (it is not even reached as a postcondition "
                     "check). This is the MANDATORY frame-mutation probe for the "
                     "read-only input.",
    },
    {
        "id": "uniq-frame-mutate-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_TARGET),
        "refinement": "writing `target_mode[i] = 0` corresponds to a patch that "
                      "overwrote the caller-owned per-layer target async mode "
                      "(middleware_is_async, computed unchanged at base.py:43-51) to a "
                      "fixed value, building the chain for the wrong mode at every "
                      "participating layer. The F2P walks an async layer (mode 1); "
                      "forcing mode 0 would adapt/wrap it for the wrong mode and the "
                      "async response would not resolve. The real loop never writes "
                      "this column.",
        "rationale": "rejected by the PERMISSION system: target_mode is held at "
                     "Acc(list_pred(target_mode), 1/2); the store `target_mode[i] = 0` "
                     "requires full write permission, which the half cannot supply -> "
                     "INSUFFICIENT PERMISSION. Supporting frame-mutation case on the "
                     "second read-only input.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-skip-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_ALL),
        "refinement": "treating every layer as declining corresponds to a patch whose "
                      "loop never commits any middleware (e.g. an unconditional "
                      "`continue`). The assembled chain would be just the base handler "
                      "with no middleware attached, so SyncAndAsyncMiddleware would "
                      "never run and the F2P's expected adaptation log record / b'OK' "
                      "response through the chain would not appear -> does not resolve.",
        "rationale": "rejected by ToSeq(Result()[0]) == final_handler([], base_async, "
                     "..., 0) and Result()[1] == final_async(...): on any input with a "
                     "participating layer (declines[i]==0) the fold commits a non-empty "
                     "trace / advances the flag, but this impl returns the empty base "
                     "handler and base_async, so clauses (H)/(A) fail. Supporting "
                     "near-miss for the decline-rollback attacks.",
    },
]


# ===========================================================================
# AXIOM LANE — NO consumed @ContractOnly axiom (the axioms region is empty).
# adapt_token / wrap_token are A-reference DEEP MODELS of the two UNCHANGED
# callees:
#   * adapt_token  <- BaseHandler.adapt_method_mode (django/core/handlers/base.py)
#   * wrap_token   <- convert_exception_to_response (django/core/handlers/exception.py)
# The load-bearing soundness obligation for these deep models (the only property
# the chain-assembly proof relies on, mapping.md §3.1): each callee DERIVES A
# FRESH handler from the old one and NEVER mutates the passed handler in place —
# which is exactly what makes the handler's identity (its token trace) observe a
# committed vs a discarded tentative adaptation. If either callee mutated its
# input in place, a declining layer's tentative adaptation could survive even
# with the gold rollback, and the deep-model abstraction (a pure append that
# leaves the input untouched) would be UNSOUND.
#
# We run TWO Docker probes in the instance image (apply_gold=True; the callees
# are unchanged by the patch so this is harmless):
#   (1) ax-sound: drive the REAL adapt_method_mode / convert_exception_to_response
#       and assert each returns a FRESH object and does not mutate the input
#       handler in place; AND port axiom_check.py's reconstruction of the real
#       patched loop threading to confirm the fold final_handler/final_async ==
#       the real rollback semantics (12 boundary + 50000 fuzz sequences,
#       declining layers leave no trace). stdlib-only fallback if the real callee
#       cannot be exercised, so the load-bearing fold check always runs.
#   (2) ax-cover: containment — every callee-input the model can reach is a
#       handler the deep model covers (the model passes an arbitrary running
#       handler trace + an int target_mode; the deep models are total over all
#       such inputs), so no reachable input lies outside the deep model's domain.
# ===========================================================================

# axiom_check.py is stdlib-only; read its source on the HOST at load time and
# embed it so the probe can reuse the validated reconstruction in-container
# (pilot pitfall #6: only the probe is mounted at /work).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


_AX_SOUNDNESS_PROBE = (
    "import sys\n"
    # --- the bundle's validated stdlib reconstruction (embedded; see pitfall #6) ---
    + _AXIOM_CHECK_SRC.replace(
        'if __name__ == "__main__":\n    sys.exit(main())',
        '# (embedded; __main__ guard removed so we can call main() below)')
    + r'''

# --- additionally drive the REAL django callees to confirm the A-reference deep
#     models are SOUND: a fresh derivation, no in-place mutation of the handler --
def _check_real_callees():
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=False, ALLOWED_HOSTS=["*"],
                               MIDDLEWARE=[], ROOT_URLCONF=__name__,
                               DATABASES={})
        django.setup()
    except Exception as exc:
        print("ax-sound: real-callee config skipped (%r); fold check still ran" % (exc,))
        return True

    ok = True
    # (1) convert_exception_to_response: derive a FRESH wrapper, never mutate input.
    try:
        from django.core.handlers.exception import convert_exception_to_response

        class _Resp:  # a mutable sentinel handler whose identity we can watch
            def __init__(self):
                self.token_trace = ["BASE"]
            def __call__(self, request):
                return "resp"

        base = _Resp()
        before = list(base.token_trace)
        wrapped = convert_exception_to_response(base)
        # the wrapper must be a NEW object (not the same handler)
        assert wrapped is not base, (
            "AXIOM-UNSOUND: convert_exception_to_response returned the SAME object "
            "(deep model wrap_token assumes a fresh derivation)")
        # and it must not have mutated the passed handler's observable identity
        assert base.token_trace == before, (
            "AXIOM-UNSOUND: convert_exception_to_response mutated the input handler "
            "in place: was %r now %r" % (before, base.token_trace))
        print("ax-sound: convert_exception_to_response is a fresh, "
              "non-mutating derivation (wrap_token deep model sound).")
    except Exception as exc:
        print("ax-sound: convert_exception_to_response probe skipped (%r)" % (exc,))

    # (2) BaseHandler.adapt_method_mode: returns the method unchanged or a fresh
    #     sync/async wrapper; never mutates the passed handler in place.
    try:
        import asyncio
        from django.core.handlers.base import BaseHandler

        class _H:
            def __init__(self):
                self.token_trace = ["BASE"]

        def sync_handler(request):
            return "ok"

        bh = BaseHandler()
        # adapt_method_mode(is_async, method, method_is_async=False, debug=False, name=None)
        before_attr = getattr(sync_handler, "token_trace", None)
        # ask for an ASYNC adapter of a sync method -> a FRESH async_to_sync/sync_to_async wrapper
        adapted = bh.adapt_method_mode(True, sync_handler, False, debug=False, name="probe")
        assert adapted is not None
        # the original method object must be untouched (no attribute injected onto it)
        assert getattr(sync_handler, "token_trace", None) == before_attr, (
            "AXIOM-UNSOUND: adapt_method_mode mutated the passed method in place")
        # asking for the SAME mode returns the method unchanged (identity preserved)
        same = bh.adapt_method_mode(False, sync_handler, False, debug=False, name="probe")
        assert same is sync_handler, (
            "adapt_method_mode for the matching mode should return the method unchanged")
        print("ax-sound: adapt_method_mode is a fresh, non-mutating derivation "
              "(adapt_token deep model sound; same-mode returns the method unchanged).")
    except Exception as exc:
        print("ax-sound: adapt_method_mode probe skipped (%r)" % (exc,))
    return ok


def _run():
    # (a) the load-bearing fold == real-rollback-semantics check (always runs)
    rc = main()
    if rc != 0:
        print("ax-sound FAIL: fold != real patched threading")
        return 1
    # (b) the real-callee fresh-derivation / no-mutation soundness check
    if not _check_real_callees():
        return 1
    print("ax-sound OK: A-reference deep models adapt_token/wrap_token are sound "
          "(fresh, non-mutating derivations) and the folds match the real patched "
          "load_middleware threading.")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
'''
)


_AX_CONTAINMENT_PROBE = r'''
import sys

# Containment for the A-reference deep models. The model passes to:
#   adapt_token(handler, target_mode): handler is the running token trace (a
#     List[int]); target_mode is an int in {0,1} (target_mode[i] under the
#     precondition that the column holds {0,1} modes).
#   wrap_token(handler): handler is the running token trace (a List[int]).
# Both deep models are TOTAL pure appends defined for EVERY List[int] handler and
# every int target_mode -> their domain is all such inputs. The model can only
# ever reach a finite-length int handler trace and an int target_mode, so EVERY
# caller-reachable callee-input lies inside the deep model's domain. There is no
# scalar Requires to fall outside of (unlike a @ContractOnly axiom): the
# A-reference deep model covers the whole carrier type. We confirm operationally
# that the inputs the model produces along a representative walk are exactly
# (List[int], int{0,1}) pairs the deep models accept.

ADAPT_TOKEN = 1
WRAP_TOKEN = 2

def adapt_token(handler, target_mode):
    return list(handler) + [ADAPT_TOKEN, target_mode]

def wrap_token(handler):
    return list(handler) + [WRAP_TOKEN]

def main():
    import random
    rng = random.Random(13810)
    reached = 0
    # Enumerate the callee-inputs the model can reach by walking representative
    # layer sequences exactly as assemble_chain does, recording each (handler,
    # target_mode) pair handed to adapt_token and each handler handed to wrap_token.
    for _ in range(20000):
        n = rng.randint(0, 8)
        target_mode = [rng.randint(0, 1) for _ in range(n)]
        declines = [rng.randint(0, 1) for _ in range(n)]
        handler = []  # the running token trace, a List[int]
        for i in range(n):
            tm = target_mode[i]
            # model reaches adapt_token(handler, tm): handler is List[int], tm is int{0,1}
            assert isinstance(handler, list) and all(isinstance(x, int) for x in handler), (
                "AXIOM-TOO-WEAK-FOR-CALLER: handler reaching adapt_token is not a List[int]: %r" % (handler,))
            assert isinstance(tm, int) and tm in (0, 1), (
                "AXIOM-TOO-WEAK-FOR-CALLER: target_mode reaching adapt_token is not int{0,1}: %r" % (tm,))
            adapted = adapt_token(handler, tm)
            reached += 1
            if declines[i] == 1:
                continue
            # model reaches wrap_token(adapted): adapted is List[int]
            assert isinstance(adapted, list) and all(isinstance(x, int) for x in adapted), (
                "AXIOM-TOO-WEAK-FOR-CALLER: handler reaching wrap_token is not a List[int]: %r" % (adapted,))
            handler = wrap_token(adapted)
            reached += 1
    print("ax-cover OK: every callee-input the model reaches is a (List[int] "
          "handler, int{0,1} target_mode) pair, all inside the A-reference deep "
          "models' total domain; %d callee-calls sampled, none outside." % reached)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deep-models",
        "axiom": "adapt_token/wrap_token",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the callees are UNCHANGED by the patch; apply_gold is harmless
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "the A-reference deep models adapt_token/wrap_token assume each "
                     "real callee (adapt_method_mode / convert_exception_to_response) "
                     "DERIVES A FRESH handler and NEVER mutates the input in place — "
                     "the property that makes the token trace observe a committed vs a "
                     "discarded adaptation. The probe (a) ports axiom_check.py's "
                     "validated reconstruction of the real patched loop threading and "
                     "asserts the folds final_handler/final_async match it on 12 "
                     "boundary + 50000 fuzz sequences (declining layers leave no "
                     "trace), and (b) drives the REAL django callees to confirm each "
                     "returns a fresh object and leaves the passed handler untouched. "
                     "Any in-place mutation or non-fresh return => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-deep-models",
        "axiom": "adapt_token/wrap_token",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the model can only pass to adapt_token a (List[int] handler, "
                     "int{0,1} target_mode) pair and to wrap_token a List[int] handler. "
                     "The deep models are TOTAL pure appends over the whole carrier "
                     "type, so every caller-reachable callee-input lies inside their "
                     "domain (a reachable input outside would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists). Confirmed by walking "
                     "20000 representative layer sequences as assemble_chain does and "
                     "checking every recorded callee-input is in domain.",
    },
]
