"""properties.py — PBT falsification manifest for django__django-16502.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. TWO functions are under spec (a genuine two-site change —
the gold patch edits `cleanup_headers` and adds `finish_response`):

    prepare_response_headers(resp: Resp, head: bool, keepalive: bool) -> None
    emit_response_body(result: List[int], head: bool) -> List[int]

------------------------------------------------------------------------------
Site A — prepare_response_headers (models cleanup_headers). `resp` is held at
FULL permission (genuinely mutated in place), so there is NO read-only input on
this site; the relevant attacks are value-level postcondition violations. The
load-bearing contract:

    Requires(Acc(resp.has_size) and Acc(resp.conn_terminate) and Acc(resp.terminate_flag))
    Requires(resp.conn_terminate == False)            # base step set no terminate
    Requires(resp.terminate_flag == False)
    Ensures (Implies(head, resp.has_size == False))            # (a) HEAD drops size
    Ensures (Implies(not head, resp.has_size == Old(resp.has_size)))  # body-bearing untouched
    Ensures (resp.conn_terminate == want_terminate(head, resp.has_size, keepalive))  # (b)
    Ensures (Implies(head and keepalive, resp.conn_terminate == False))  # the DISCRIMINATOR
    Ensures (resp.terminate_flag == resp.conn_terminate)       # (c) flag mirrors

  The DISCRIMINATING clause this patch fixes is `Implies(head and keepalive,
  conn_terminate == False)` together with `conn_terminate == want_terminate(...)`:
  a HEAD request that keeps alive is NEVER terminated merely for lacking a
  payload-size header. The pre-patch `cleanup_headers` set `Connection: close`
  whenever `Content-Length not in headers`, regardless of method, so it closed a
  HEAD-without-size; `model_prepatch.py` reproduces that (`if not has_size:
  conn_terminate = True`) and FAILS this clause (G-DIFF). It ALSO fails
  `Implies(head, has_size == False)` (no method-sensitive size drop). The F2P
  test observes both: the HEAD response carries no `Content-Length:` line and no
  `Connection: close`.

  Is `want_terminate` an echoable ungrounded oracle?  NO. `want_terminate` is a
  @Pure helper GROUNDED entirely in the arguments — `((not head) and (not
  has_size_after)) or (not keepalive)` — fully unfolded by the verifier from the
  inputs (head/has_size/keepalive). There is no opaque answer-key a wrong impl
  could echo to satisfy `conn_terminate == want_terminate(...)` without computing
  the right value: writing `conn_terminate = want_terminate(head, resp.has_size,
  keepalive)` IS the correct computation. So there is no "wrong echo" rival to
  build; instead the positive controls below are the cheapest honest impls and
  the partial-domain rivals attack the genuine value computation. (See
  `assessment`.)

------------------------------------------------------------------------------
Site B — emit_response_body (models finish_response). `result` (the application
body iterable) is held at FRACTIONAL permission `Acc(list_pred(result), 1/2)` —
READ-ONLY. The contract:

    Requires(Acc(list_pred(result), 1 / 2))                    # read-only input
    Ensures (Acc(list_pred(result), 1 / 2))
    Ensures (Acc(list_pred(Result())))
    Ensures (Implies(head, ToSeq(Result()) == PSeq(0).take(0)))  # HEAD: empty
    Ensures (Implies(head, len(Result()) == 0))
    Ensures (Implies(not head, ToSeq(Result()) == ToSeq(result)))  # GET: identity
    Ensures (Implies(not head, len(Result()) == len(result)))

  Because `result` is read-only at 1/2 permission, the MANDATORY frame-mutation
  probe applies on this site: a rival whose impl WRITES to `result` (append /
  index-assign) to "satisfy" a postcondition must be REJECTED for INSUFFICIENT
  PERMISSION — not for a value mismatch. A byte-fuzzer never thinks to mutate the
  read-only input; this is the project's #1 weakness class.

------------------------------------------------------------------------------
Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside an `# impl-start`/`# impl-end` region (the
nested `invariants` region of site B lives inside its impl span and is elided
by `spec_view`, so reshaping the loop/invariants keeps `markers.same_spec`).
The frozen spec (axioms/pure/pre/post-conditions + signatures) is never touched,
so a rejection is always attributable to the impl, never a tampered contract.
Each `expect:"reject"` rival carries the refinement argument that its faithful
real patch would NOT resolve the F2P. There are NO @ContractOnly axioms and NO
A-reference deep model of a changed callee in this bundle (every changed decision
is modeled deeply); the only callees are the UNCHANGED wsgiref base methods,
validated against the real stdlib by axiom_check.py — so the axiom lane is
vacuous here and AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "django__django-16502"
FLOAT_ENCODING = None

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


# ===========================================================================
# Region landmarks — the WHOLE impl body of each function, strictly between its
# # impl-start and # impl-end. Each occurs exactly once in model.py.
# ===========================================================================

# Site A: prepare_response_headers impl body.
_IMPL_HEADERS = """    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    # Ask to terminate only for a body-bearing method of unknown length,
    # otherwise only when the environment cannot keep connections alive.
    if (not head) and (not resp.has_size):
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    # Mirror the terminate decision onto the handler flag.
    if resp.conn_terminate:
        resp.terminate_flag = True"""

# Site B: emit_response_body impl body (includes the nested invariants region,
# which spec_view elides along with the rest of the impl span).
_IMPL_BODY = """    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    j = 0
    while j < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Site A, structurally-different but CORRECT. Compute the terminate decision
# into an explicit local boolean first (a different control-flow source than the
# in-place if/elif), then assign all three fields from it. The size-drop is moved
# AFTER the terminate computation is staged but the value used for the terminate
# is the post-drop size, so the local is computed only after the drop — preserving
# the gold ordering semantics. Semantically identical; if it fails to verify the
# postcondition is over-fit to the gold's exact statement shape => SPEC-TOO-STRONG.
_HEADERS_LOCAL = """    # Drop the payload-size header for a body-less method, then decide terminate
    # from the post-drop state via an explicit local (different control shape).
    if head and resp.has_size:
        resp.has_size = False
    terminate = ((not head) and (not resp.has_size)) or (not keepalive)  # type: bool
    resp.conn_terminate = terminate
    resp.terminate_flag = terminate"""
_POS_HEADERS_LOCAL = _swap(_BASE, _IMPL_HEADERS, _HEADERS_LOCAL)

# (5b) Site A, branch-reorder positive control. Test the keep-alive guard FIRST,
# then the body-bearing-unknown-length guard, joined by `or`-equivalent nested
# ifs — opposite evaluation order to the gold if/elif, same result set. Keep the
# flag mirror as in gold. If this fails to verify the spec is over-fit to the
# gold guard order => SPEC-TOO-STRONG.
_HEADERS_REORDER = """    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    # Reordered guards: keep-alive guard first, then the body-bearing-unknown
    # guard. Same terminate result set as the gold if/elif.
    if not keepalive:
        resp.conn_terminate = True
    elif (not head) and (not resp.has_size):
        resp.conn_terminate = True
    if resp.conn_terminate:
        resp.terminate_flag = True"""
_POS_HEADERS_REORDER = _swap(_BASE, _IMPL_HEADERS, _HEADERS_REORDER)

# (5c) Site B, structurally-different but CORRECT. Local-variable reshape: hoist
# len(result) into a typed local `n` and loop `j < n`; keep every gold invariant
# verbatim (forward append against the forward-prefix `ToSeq(out) ==
# ToSeq(result).take(j)` — NO induction lemma needed). If it fails to verify the
# body spec is over-fit to the literal `len(result)`-in-guard shape =>
# SPEC-TOO-STRONG. (We do NOT flip loop direction: a back-to-front fill would
# need an f(a+b)==f(a)+f(b) lemma the verifier won't auto-discharge — pilot bug 3.)
_BODY_HOIST = """    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    n = len(result)  # type: int
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(n == len(result))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out"""
_POS_BODY_HOIST = _swap(_BASE, _IMPL_BODY, _BODY_HOIST)

# (6) ADMISSIBILITY — the frozen gold module verbatim. Verifying the unmodified
# model proves the precondition is SATISFIABLE for an F2P-shaped input (the proof
# establishes Requires at entry of both sites on the representative HEAD/GET x
# size x keepalive cube the F2P exercises) and the postconditions are jointly
# satisfiable. If the gold model itself cannot verify the precondition for a
# normal input => PRECOND-TOO-STRONG. (Cheapest honest positive control; same
# spec trivially since impl is unchanged.)
_POS_ADMISS = _BASE


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (A-bug) THE DISCRIMINATING BUG ITSELF (site A) — pre-patch terminate rule.
# Terminate whenever the payload-size header is absent, REGARDLESS of method
# (and never drop the size header for HEAD). This is model_prepatch.py verbatim.
# For (head=True, has_size=True/False, keepalive=True): a HEAD keeping alive that
# lacks a size header is wrongly terminated, AND the size header is never dropped.
_HEADERS_PREPATCH = """    # Pre-patch: never drop the size header; terminate whenever it is absent,
    # regardless of method.
    if not resp.has_size:
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    if resp.conn_terminate:
        resp.terminate_flag = True"""
_RIVAL_HEADERS_PREPATCH = _swap(_BASE, _IMPL_HEADERS, _HEADERS_PREPATCH)

# (A-nodrop) PARTIAL-DOMAIN (site A) — keep the correct terminate decision but
# DROP the HEAD size-removal. Correct on the terminate clause and on every
# body-bearing input, but for (head=True, has_size=True) the size header survives.
# Note: with size still present, `want_terminate(True, True, keepalive)` differs
# from the gold's `want_terminate(True, False, keepalive)` only when keepalive is
# True (both give False) — so the terminate clause may still hold; the defect is
# isolated to the size-drop clause `Implies(head, has_size == False)`.
_HEADERS_NODROP = """    # Defect: omit the body-less size-header drop entirely.
    if (not head) and (not resp.has_size):
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    if resp.conn_terminate:
        resp.terminate_flag = True"""
_RIVAL_HEADERS_NODROP = _swap(_BASE, _IMPL_HEADERS, _HEADERS_NODROP)

# (A-flag) CONTROL-FLOW/STATE-MIRROR rival (site A) — compute the size + terminate
# correctly, but NEVER set the handler terminate_flag (leave it at its entry
# False). For any terminating input (e.g. a body-bearing no-size request, or any
# request that cannot keep alive) conn_terminate becomes True while terminate_flag
# stays False, violating the mirror.
_HEADERS_NOFLAG = """    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    if (not head) and (not resp.has_size):
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    # Defect: never mirror the terminate decision onto the handler flag."""
_RIVAL_HEADERS_NOFLAG = _swap(_BASE, _IMPL_HEADERS, _HEADERS_NOFLAG)

# (A-overterminate) PARTIAL-DOMAIN (site A) — terminate a HEAD-without-size even
# while keeping alive (drop the `not head` guard on the unknown-length branch).
# Correct everywhere EXCEPT the discriminating (head=True, has_size=False,
# keepalive=True) sub-domain, where it sets conn_terminate=True. This is the
# narrowest form of the pre-patch bug, isolated to the F2P-relevant cell.
_HEADERS_OVERTERM = """    # Drop the payload-size header for a body-less method.
    if head and resp.has_size:
        resp.has_size = False
    # Defect: terminate on a missing size header even for a body-less method.
    if not resp.has_size:
        resp.conn_terminate = True
    elif not keepalive:
        resp.conn_terminate = True
    if resp.conn_terminate:
        resp.terminate_flag = True"""
_RIVAL_HEADERS_OVERTERM = _swap(_BASE, _IMPL_HEADERS, _HEADERS_OVERTERM)

# (B-frame) ** FRAME-MUTATION ** (site B, MANDATORY) — `result` is read-only at
# Acc(list_pred(result), 1/2). This rival WRITES to it: in the body-bearing
# branch it mutates `result` in place (overwriting the first byte) instead of
# only reading. Even though the emitted `out` would still equal the (now-mutated)
# input, the write requires FULL permission on list_pred(result); the impl holds
# only 1/2, so it MUST be rejected for INSUFFICIENT PERMISSION — not a value
# mismatch. Keeps the gold invariants verbatim so the rejection is attributable
# to the write alone.
_BODY_FRAME = """    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    if len(result) > 0:
        # FRAME VIOLATION: writing to a read-only (1/2-permission) input.
        result[0] = 0
    j = 0
    while j < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out"""
_RIVAL_BODY_FRAME = _swap(_BASE, _IMPL_BODY, _BODY_FRAME)

# (B-nonempty) THE OTHER DISCRIMINATING BUG (site B) — pre-patch body emission:
# ALWAYS copy the application data, even for HEAD (no finish_response override).
# This is model_prepatch_2.py verbatim. For head=True the emitted body equals the
# (non-empty) input, violating Implies(head, len(Result()) == 0).
_BODY_NONEMPTY = """    out = []  # type: List[int]
    j = 0
    while j < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out"""
_RIVAL_BODY_NONEMPTY = _swap(_BASE, _IMPL_BODY, _BODY_NONEMPTY)

# (B-truncate) PARTIAL-DOMAIN (site B) — body-bearing branch emits all but the
# LAST byte (loop to len-1). Correct for HEAD (empty) and for length-0/length-1
# edge inputs only by accident, but for any body of length >= 1 it drops the final
# element, violating ToSeq(Result()) == ToSeq(result) (and len equality). Targets
# the last-element sub-domain a value proxy would miss.
_BODY_TRUNCATE = """    out = []  # type: List[int]
    if head:
        # The body-less branch contributes nothing to the output.
        return out
    j = 0
    while j + 1 < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    return out"""
_RIVAL_BODY_TRUNCATE = _swap(_BASE, _IMPL_BODY, _BODY_TRUNCATE)

# (B-headleak) PARTIAL-DOMAIN (site B) — emit the body for HEAD when the body is
# non-empty (drop the early HEAD return; gate the empty result on the loop only).
# i.e. unconditionally copy. Distinct in intent from B-nonempty: it models a patch
# that "consumes but accidentally re-writes" the iterator for HEAD. For head=True
# with a non-empty body, the output is non-empty, violating len(Result()) == 0.
_BODY_HEADLEAK = """    out = []  # type: List[int]
    j = 0
    while j < len(result):
        # invariants-start
        Invariant(Acc(list_pred(result), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(result))
        Invariant(ToSeq(out) == ToSeq(result).take(j))
        Invariant(len(out) == j)
        Invariant(MustTerminate(len(result) - j + 1))
        # invariants-end
        out.append(result[j])
        j = j + 1
    if head:
        # Defect: clear nothing — HEAD still emits whatever was copied.
        return out
    return out"""
_RIVAL_BODY_HEADLEAK = _swap(_BASE, _IMPL_BODY, _BODY_HEADLEAK)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-headers-local-bool", "kind": "soundness", "expect": "verify",
     "module": _POS_HEADERS_LOCAL,
     "rationale": "site A, structurally-different but semantically identical: the terminate "
                  "decision is staged into an explicit local boolean computed from the post-drop "
                  "state (`((not head) and (not has_size)) or (not keepalive)`) and assigned to "
                  "both conn_terminate and terminate_flag, instead of the gold's in-place "
                  "if/elif + flag-mirror. Same result on the whole HEAD/GET x size x keepalive "
                  "cube. If it fails to verify the postcondition is over-fit to the gold "
                  "statement shape => SPEC-TOO-STRONG. Also the cheapest honest impl (the "
                  "terminate value is grounded, not echoed)."},
    {"id": "pos-headers-reorder-guards", "kind": "soundness", "expect": "verify",
     "module": _POS_HEADERS_REORDER,
     "rationale": "site A, branch-reorder: evaluate the keep-alive guard FIRST then the "
                  "body-bearing-unknown-length guard (opposite order to the gold if/elif), keep "
                  "the gold flag mirror. Same terminate result set. If it fails to verify the "
                  "spec is over-fit to the gold guard order => SPEC-TOO-STRONG."},
    {"id": "pos-body-hoist-len", "kind": "soundness", "expect": "verify",
     "module": _POS_BODY_HOIST,
     "rationale": "site B, local-variable reshape: hoist len(result) into a typed local `n`, loop "
                  "`j < n`, add the framing invariant `n == len(result)`, keep every gold "
                  "invariant verbatim (forward append against the forward-prefix take-invariant — "
                  "no induction lemma needed). If it fails to verify the body spec is over-fit to "
                  "the literal-len-in-guard shape => SPEC-TOO-STRONG."},
    {"id": "admiss-gold-verbatim", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "the frozen gold module unchanged: verifying it proves both sites' Requires are "
                  "SATISFIABLE for an F2P-shaped input (the proof establishes the entry "
                  "preconditions on the representative HEAD/GET x size x keepalive cube the F2P "
                  "exercises) and the postconditions are jointly satisfiable. If the gold model "
                  "itself cannot verify the precondition for a normal input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-headers-prepatch-terminate", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HEADERS_PREPATCH,
     "refinement": "this is the PRE-PATCH cleanup_headers verbatim (model_prepatch.py): no "
                   "method-sensitive Content-Length removal, and `Connection: close` set whenever "
                   "`Content-Length not in self.headers` regardless of REQUEST_METHOD. Its "
                   "faithful real patch is the UNCHANGED pre-#16502 code, which on a HEAD request "
                   "(whose Content-Length the base step did not set) sets `Connection: close` and "
                   "leaves no size header dropped — failing the F2P assertions that a HEAD "
                   "response carries NO `Connection: close` line (and the GET/HEAD size handling). "
                   "So it would NOT resolve.",
     "rationale": "the discriminating bug this patch fixes (mirrors G-DIFF / model_prepatch.py). "
                  "Rejection source: `conn_terminate == want_terminate(head, has_size, keepalive)` "
                  "and `Implies(head and keepalive, conn_terminate == False)` — for "
                  "(head=True, has_size=False, keepalive=True) the rival sets conn_terminate=True "
                  "but want_terminate is False; AND `Implies(head, has_size == False)` is violated "
                  "(no drop). If it verified => SPEC-TOO-WEAK (admits the very bug)."},
    {"id": "rival-headers-no-size-drop", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HEADERS_NODROP,
     "refinement": "keeps the correct terminate decision but omits the body-less size-header "
                   "drop. Faithful real patch = cleanup_headers with the `if REQUEST_METHOD == "
                   "'HEAD' and 'Content-Length' in headers: del headers['Content-Length']` hunk "
                   "removed: a HEAD response would still carry the base-injected `Content-Length` "
                   "header, failing the F2P assertion that NO `Content-Length:` line appears for "
                   "HEAD. So it would NOT resolve.",
     "rationale": "partial-domain rival isolated to the size-drop clause. Rejection source: "
                  "`Implies(head, resp.has_size == False)` — for (head=True, has_size=True) the "
                  "header survives, so has_size != False. If it verified => SPEC-TOO-WEAK (the "
                  "HEAD size omission unenforced)."},
    {"id": "rival-headers-flag-not-mirrored", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HEADERS_NOFLAG,
     "refinement": "computes size + terminate correctly but never sets the handler "
                   "close_connection flag. Faithful real patch = cleanup_headers with the final "
                   "`if self.headers.get('Connection') == 'close': self.request_handler."
                   "close_connection = True` mirror deleted: the connection would NOT actually be "
                   "closed when `Connection: close` was emitted (e.g. a body-bearing no-size "
                   "request, or a non-threading server), leaving the persistent-connection "
                   "behaviour broken — the P2P persistent-connection / close semantics the patch "
                   "preserves would regress. So it would NOT resolve.",
     "rationale": "state-mirror (control-flow-effect) rival. Rejection source: "
                  "`resp.terminate_flag == resp.conn_terminate` — for any terminating input the "
                  "flag stays False while conn_terminate is True. If it verified => SPEC-TOO-WEAK "
                  "(the handler-flag mirror unconstrained)."},
    {"id": "rival-headers-overterminate-head", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HEADERS_OVERTERM,
     "refinement": "drops the `not head` guard on the unknown-length terminate branch: terminates "
                   "a HEAD-without-size request even while keeping alive. Faithful real patch = "
                   "cleanup_headers whose persistent-connection guard is still `if "
                   "'Content-Length' not in self.headers` (the pre-patch guard) rather than the "
                   "method-gated `if REQUEST_METHOD != 'HEAD' and ...` — so a HEAD response gets "
                   "`Connection: close`, failing the F2P assertion that the HEAD response carries "
                   "no `Connection: close` line. So it would NOT resolve.",
     "rationale": "narrowest partial-domain form of the pre-patch bug, isolated to the "
                  "discriminating (head=True, has_size=False, keepalive=True) cell. Rejection "
                  "source: `Implies(head and keepalive, resp.conn_terminate == False)` and "
                  "`conn_terminate == want_terminate(...)` — for that cell want_terminate is False "
                  "but the rival sets conn_terminate=True. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-body-frame-mutation", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BODY_FRAME,
     "refinement": "writes to the read-only application iterable (`result[0] = 0`) before copying "
                   "it. Faithful real patch = a finish_response that MUTATES self.result (the "
                   "application's returned body) in place — corrupting the bytes the WSGI app "
                   "produced; the GET response body would no longer equal the application's data, "
                   "failing the F2P assertion `self.assertEqual(body, hello_world_body)`. So it "
                   "would NOT resolve. (This is the MANDATORY frame-mutation probe: the input is "
                   "read-only at Acc(list_pred(result), 1/2).)",
     "rationale": "FRAME-MUTATION rival on the read-only 1/2-permission input. Rejection source: "
                  "the PERMISSION SYSTEM — writing `result[0] = 0` requires FULL permission on "
                  "list_pred(result) but the impl holds only 1/2, so the assignment is rejected "
                  "for INSUFFICIENT PERMISSION (not a value mismatch). The gold invariants are "
                  "kept verbatim so the rejection is attributable to the write alone. If it "
                  "verified => the read-only frame was not actually enforced (SPEC-TOO-WEAK / "
                  "permission hole)."},
    {"id": "rival-body-nonempty-head", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BODY_NONEMPTY,
     "refinement": "this is the PRE-PATCH body emission verbatim (model_prepatch_2.py): no "
                   "finish_response override, so the base path always writes the full application "
                   "body — for HEAD too. Faithful real patch = the unchanged pre-#16502 code "
                   "(no HEAD bypass), which emits the body for a HEAD request, failing the F2P "
                   "assertion that a HEAD response has an empty body (`self.assertEqual(body, "
                   "b'\\r\\n')`). So it would NOT resolve.",
     "rationale": "the other discriminating bug this patch fixes (G-DIFF / model_prepatch_2.py). "
                  "Rejection source: `Implies(head, len(Result()) == 0)` and `Implies(head, "
                  "ToSeq(Result()) == empty)` — for head=True with a non-empty body the output is "
                  "non-empty. If it verified => SPEC-TOO-WEAK (admits the HEAD-body bug)."},
    {"id": "rival-body-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BODY_TRUNCATE,
     "refinement": "body-bearing branch emits all but the LAST byte (loops while `j + 1 < "
                   "len(result)`). Faithful real patch = a finish_response that writes all but the "
                   "final chunk of the application body — a GET response body truncated by its "
                   "last byte, failing the F2P assertion `self.assertEqual(body, "
                   "hello_world_body)` (the body must equal the full application data). So it "
                   "would NOT resolve.",
     "rationale": "partial-domain rival targeting the last-element sub-domain. Rejection source: "
                  "`Implies(not head, ToSeq(Result()) == ToSeq(result))` and `len(Result()) == "
                  "len(result)` — for any body of length >= 1 the output is one element short. "
                  "If it verified => SPEC-TOO-WEAK (a value proxy that drops the final index)."},
    {"id": "rival-body-head-emits-body", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BODY_HEADLEAK,
     "refinement": "drops the early HEAD return and unconditionally copies the body, so HEAD also "
                   "emits the data (it consumes but then re-emits). Faithful real patch = a "
                   "finish_response whose HEAD branch consumes the iterator but still calls the "
                   "base write path (or otherwise writes the consumed bytes) — emitting the body "
                   "for a HEAD request, failing the F2P empty-HEAD-body assertion. So it would NOT "
                   "resolve.",
     "rationale": "partial-domain rival on the HEAD sub-domain (distinct shape from "
                  "rival-body-nonempty-head: explicit-but-ineffective HEAD branch). Rejection "
                  "source: `Implies(head, len(Result()) == 0)` — for head=True with a non-empty "
                  "body the output is non-empty. If it verified => SPEC-TOO-WEAK."},
]

# ===========================================================================
# AXIOM LANE — VACUOUS for this bundle.
# ===========================================================================
# There are NO @ContractOnly axioms and NO A-reference deep model standing in for
# a *changed* opaque callee (meta.json: axioms == [], deep_model_references ==
# []; G-AX == "vacuous"). Every changed decision (the HEAD size-header drop, the
# terminate-only-for-body-bearing-unknown-length rule, the empty HEAD body) is
# modeled DEEPLY in the impl regions, so there is no contract-about-a-changed-
# callee to falsify. The only callees are the UNCHANGED wsgiref base-handler
# methods (super().cleanup_headers/finish_response, the base finish_content/
# write); their modeling assumptions are validated against the REAL stdlib by
# axiom_check.py (RC=0). Nothing for the axiom lane to probe here.
AXIOM_TESTS = []
