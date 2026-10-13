# properties.py — PBT falsification battery for psf__requests-1921.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec
# byte-identically (region-surgery edits ONLY inside the # impl-start/# impl-end
# region; the nested invariants region lives inside impl and is therefore part
# of the elided impl view, so it too may be reshaped without touching the spec)
# and is checked by Nagini verify + markers.same_spec. AXIOM_TESTS is empty:
# the bundle has NO @ContractOnly axioms / consumed axioms (the merge-and-drop
# is modelled DEEPLY via the @Pure effective/combined; the single A-reference is
# already validated by axiom_check.py/G-AX in Docker, out of PBT's spec lane).
#
# Defended surface (model.py):
#   effective_collection(session, request, n) -> List[int]
#     READ-ONLY inputs: session, request held at Acc(list_pred(.), 1/2)
#       (Requires AND Ensures) => frame-mutation attack is MANDATORY.
#     Output: freshly built, fully owned (Acc(list_pred(Result()))).
#     Postcondition load-bearing clauses:
#       (len)  len(Result()) == n
#       (1)    Forall k in [0,n): Result()[k] == combined(session[k], request[k])
#              -- pins every position to the GROUNDED deep model `combined`
#              (a @Pure function of the args, fully unfolded). No opaque oracle:
#              there is no "wrong echo" to build (see assessment); the cheapest
#              honest impl IS the gold loop, so the oracle lane is a positive
#              control, not an echo-reject.
#       (2)    Forall k in [0,n): Result()[k] != none_val()
#              -- the headline guarantee a one-sided (per-request-only) drop
#              violates on a session-only None.
#     Delivery obligation: Requires(MustTerminate(2)) => the clauses above are
#       owed about a collection that is actually handed back, so a rival that
#       never delivers one does NOT satisfy them => a divergence rival is
#       MANDATORY (see case 7) and every variant's loop must carry its own
#       decreasing measure (the gold's Invariant(MustTerminate(n - i + 1)) lives
#       inside the elided impl region and rides along with _BASE).

from pathlib import Path

INSTANCE = "psf__requests-1921"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors (ALL strictly inside the # impl-start / # impl-end region).
# ---------------------------------------------------------------------------

# The precedence branch + its framing assert (impl region, the request-wins step).
_PRECEDENCE = """        if rv != absent():
            ev = rv
        else:
            ev = sv
        Assert(ev == effective(sv, rv))"""

# The unset-drop branch + its framing assert (impl region, keyed off the
# EFFECTIVE value ev -- the discriminating content of the gold change).
_DROP = """        if ev == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))"""

# The comment line that sits between the precedence branch and the drop branch
# in model.py (verbatim), so a full-body reshape can span both as one unit.
_DROP_COMMENT = """        # Drop the key (absent) when its effective value is the unset value,
        # regardless of which side contributed it; otherwise carry it through."""

# The whole per-key body between the invariant block and the append, so a
# positive control can reshape it as one unit while keeping every gold
# proof-obligation assert verbatim.
_BODY = _PRECEDENCE + "\n" + _DROP_COMMENT + "\n" + _DROP


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY: session & request are read-only Acc(.,1/2)).
#    A rival that WRITES the read-only `session` input. It changes nothing the
#    value abstraction observes (it overwrites session[i] AFTER reading sv), so
#    the postcondition obligations are untouched; the ONLY reason it cannot
#    verify is INSUFFICIENT PERMISSION -- the impl holds Acc(list_pred(session),
#    1/2) and a store needs full permission. expect=reject, attributable to the
#    write. Refinement: a faithful real merge_setting MUST NOT mutate its
#    `session_setting` argument (it is the persistent Session.headers shared
#    across every request); a patch that did would corrupt subsequent requests
#    and break PASS_TO_PASS (test_cookie_persists_via_api, the repeated-request
#    suite), so it would NOT resolve.
_FRAME_MUT = _swap(
    _BASE, _DROP,
    _DROP + "\n        session[i] = absent()  # ILLEGAL write to read-only input")


# ===========================================================================
# 2. UNGROUNDED-ORACLE — N/A as an echo attack. `combined` is GROUNDED (a @Pure
#    function of session[k]/request[k], fully unfolded), so there is no opaque
#    answer-key to echo wrongly. The honest cheapest impl that satisfies clause
#    (1) IS to compute combined(session[i], request[i]) directly. That is a
#    POSITIVE control (expect=verify): a correct impl that calls the oracle
#    helpers directly instead of recomputing the branches inline must verify
#    (else the spec would reject its own grounded oracle == SPEC-TOO-STRONG).
#    Keeps all gold framing asserts verbatim.
_ORACLE_POS = _swap(
    _BASE, _BODY,
    """        ev = effective(sv, rv)
        val = combined(sv, rv)""")


# ===========================================================================
# 3a. PARTIAL-DOMAIN (the base_commit / model_prepatch bug). Keys the drop off
#     the PER-REQUEST value rv instead of the EFFECTIVE value ev. Correct on
#     every key EXCEPT a session-only None (rv == absent(), sv == none_val()):
#     there it leaves none_val() in place instead of dropping to absent().
#     Violates clause (1) (result[k] != combined) AND clause (2)
#     (Result()[k] == none_val()). expect=reject.
#     Refinement: this IS the base_commit behaviour (per-request-only del). Its
#     faithful real patch is the UNPATCHED merge_setting, which sends a
#     session-set None Accept-Encoding header -> F2P
#     test_headers_on_session_with_None_are_not_sent asserts
#     'Accept-Encoding' not in prep.headers and FAILS. So it would NOT resolve.
_PARTIAL_PREPATCH = _swap(
    _BASE, _DROP,
    """        if rv == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))""")


# ===========================================================================
# 3b. PARTIAL-DOMAIN (first-element carve-out). Correct on every position k > 0
#     but at k == 0 it carries the effective value through with NO unset-drop.
#     A fuzzer that pins "most positions" would miss this; the universal
#     Forall over [0,n) catches it. On an input whose key 0 has effective value
#     none_val() the result holds none_val() at position 0 -> violates clause
#     (1) and clause (2). expect=reject.
#     Refinement: a real patch that skipped the None-drop for the first header
#     key would still send a None-valued first header -> the F2P observable
#     ('Accept-Encoding' not in prep.headers) can fall on that key and FAIL, so
#     it would NOT resolve.
_PARTIAL_FIRST = _swap(
    _BASE, _DROP,
    """        if ev == none_val() and i > 0:
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))""")


# ===========================================================================
# 4. VALUE-LEVEL OVER-DROP (drops MORE than the spec: a too-aggressive drop that
#     also removes a real per-request override). At a key where the request
#     supplies a real value (rv >= 1) it should be carried; this rival instead
#     drops it whenever the per-session value was the unset value (sv ==
#     none_val()), even though the request override makes the effective value
#     real. Violates clause (1) (result[k] == absent() != combined == rv).
#     expect=reject.
#     Refinement: a real patch that dropped a header whenever the SESSION value
#     was None -- even when the request explicitly overrides it with a real
#     value -- would strip a legitimately-set per-request header. The
#     PASS_TO_PASS request-construction suite (e.g. header/auth merges in
#     test_POSTBIN_GET_POST_FILES / the params+headers tests) would lose a
#     header it must send, so it would NOT resolve.
_OVERDROP = _swap(
    _BASE, _DROP,
    """        if ev == none_val() or sv == none_val():
            val = absent()
        else:
            val = ev
        Assert(val == combined(sv, rv))""")


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
#    Reorders BOTH branches (tests the negative condition first) and fuses the
#    precedence + drop into a single computation, keeping every gold framing
#    assert verbatim. No loop-direction flip, no dropped invariant: the gold
#    prefix-preservation Forall, the per-element pin, and the length assert all
#    remain, so the loop invariant still discharges. Must verify (else
#    SPEC-TOO-STRONG: the spec would reject a faithful reordered correct impl).
_POS_CONTROL = _swap(
    _BASE, _BODY,
    """        if rv == absent():
            ev = sv
        else:
            ev = rv
        Assert(ev == effective(sv, rv))
        if ev != none_val():
            val = ev
        else:
            val = absent()
        Assert(val == combined(sv, rv))""")


# ===========================================================================
# 6. ADMISSIBILITY — a positive-control witness that builds an F2P-shaped input
#    (the issue's exact scenario: a session-only None at key 0, a real value at
#    key 1, n == 2) and asserts, AT that witness, every frozen precondition
#    clause of effective_collection plus the per-key answer the spec's own
#    grounded oracle owes on that shape. Must verify (else PRECOND-TOO-STRONG:
#    the precondition would reject a normal merge input). The witness is appended
#    INSIDE the impl region (before `return result`) so the frozen spec view is
#    untouched.
#
#    The precondition clauses are transcribed from model.py's pre-conditions
#    region, MINUS the MustTerminate obligation: that clause is the CALLER's
#    remaining obligation level, not a fact about the input's admissibility, and
#    it is not re-established at a witness. Correspondingly the witness does not
#    CALL effective_collection: a self-call passing a fresh, non-shrinking
#    argument triple never delivers a value, so under the frozen delivery
#    obligation Nagini rejects it ("Obligation leak check failed. Callee
#    effective_collection might not take all unsatisfied obligations from the
#    caller") -- and it would be rejected for the divergence, not for anything
#    about the precondition this case exists to probe. Asserting the clauses
#    themselves probes the precondition directly, and it still has teeth: a
#    witness outside the frozen domain (e.g. n == 3 against two 2-element
#    collections) fails the third Assert.
#
#    NOTE: a freshly constructed list already holds full Acc(list_pred(.)) in
#    Nagini, so no Fold is needed (Fold(list_pred(.)) on a literal is malformed:
#    list_pred is a built-in predicate auto-established at construction, and
#    folding it crashes the translator); a 1/2 share is lendable from it.
_ADMISS_CALLER = '''
    # admissibility positive-control witness (impl-region only; spec untouched)
    s = [none_val(), 5]  # type: List[int]
    r = [absent(), absent()]  # type: List[int]
    # every frozen precondition clause, at this witness (MustTerminate excluded:
    # it is the caller's obligation level, not an admissibility fact)
    Assert(Acc(list_pred(s), 1 / 2))
    Assert(Acc(list_pred(r), 1 / 2))
    Assert(0 <= 2 and 2 <= len(s) and 2 <= len(r))
    # and the per-key answer the spec owes on this shape: key 0 (carried only by
    # the session collection, holding the unset value) is dropped to absent();
    # key 1 keeps its real value.
    Assert(combined(none_val(), absent()) == absent())
    Assert(combined(none_val(), absent()) != none_val())
    Assert(combined(5, absent()) == 5)'''

# Inject the caller body just before `return result` so it lives entirely inside
# the impl region (the post-conditions/invariants/spec are not touched). The
# callee call needs the precondition to be establishable for an F2P-shaped
# input; if it cannot be, that is PRECOND-TOO-STRONG.
_ADMISS = _swap(_BASE, "        i = i + 1\n    return result",
                "        i = i + 1" + _ADMISS_CALLER + "\n    return result")


# ===========================================================================
# 7. DIVERGENCE (MANDATORY once the contract obliges delivery). A rival that is
#    gold-shaped on every key whose effective value is real -- same precedence
#    merge, same per-key reads, every loop invariant maintained -- but on exactly
#    the key whose EFFECTIVE value is the unset value (rv == absent(),
#    sv == none_val(): the F2P shape) restarts the whole combination on the same
#    arguments instead of dropping the key. Nagini ASSUMES a callee's Ensures at
#    the call site, so the postconditions (1) and (2) are discharged there and no
#    per-key value obligation is ever violated; nothing but the delivery
#    obligation stands between this rival and a verdict of "verifies". The guard
#    is genuinely reachable (an Assert(False) in its place does NOT verify), so
#    this is a live path, not an infeasible one. expect=reject.
#    Refinement: its faithful patch restarts merge_setting on the same two
#    mappings whenever a merged value is the unset value, so a session-set None
#    header makes the call never return -- measured: F2P
#    test_headers_on_session_with_None_are_not_sent FAILS (5/6 F2P) plus P2P
#    test_header_remove_is_case_insensitive. So it would NOT resolve.
_DIVERGE_F2P = _swap(
    _BASE, _DROP,
    """        if ev == none_val():
            # restart the whole combination on the same arguments instead of
            # settling this key: the callee's Ensures are assumed here, so every
            # per-key obligation is discharged while no value is ever delivered
            return effective_collection(session, request, n)
        val = ev
        Assert(val == combined(sv, rv))""")


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-session",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FRAME_MUT,
        "refinement": (
            "A faithful merge_setting must not mutate session_setting -- it is "
            "the persistent Session.headers shared across requests. A patch that "
            "wrote it back would corrupt later requests and break PASS_TO_PASS "
            "(test_cookie_persists_via_api / repeated-request suite); it would "
            "NOT resolve."),
        "rationale": (
            "Rejection from the PERMISSION SYSTEM: the impl holds only "
            "Acc(list_pred(session), 1/2); a store session[i] = ... needs full "
            "permission, so it cannot verify. Every gold postcondition obligation "
            "is otherwise unchanged, so the failure is attributable to the write."),
    },
    {
        "id": "oracle-direct-positive",
        "kind": "soundness",
        "expect": "verify",
        "module": _ORACLE_POS,
        "rationale": (
            "`combined` is a GROUNDED @Pure oracle (a function of the args, not an "
            "opaque answer key), so there is no wrong echo to build. The honest "
            "cheapest impl computes combined(sv, rv) directly; it MUST verify, "
            "else the spec would reject its own grounded oracle (SPEC-TOO-STRONG)."),
    },
    {
        "id": "partial-domain-prepatch-rv-keyed-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_PREPATCH,
        "refinement": (
            "This is the base_commit behaviour: the drop keys off the per-request "
            "value rv (the unpatched per-request-only del) instead of the "
            "effective value ev. Its faithful real patch is the UNPATCHED "
            "merge_setting, which leaves a session-set None Accept-Encoding in "
            "place and sends it -> F2P test_headers_on_session_with_None_are_not_"
            "sent asserts 'Accept-Encoding' not in prep.headers and FAILS. NOT "
            "resolve."),
        "rationale": (
            "Rejection from postcondition (1) (loop invariant result[k] == "
            "combined(session[k], request[k])) and (2) (Result()[k] != none_val()): "
            "on a session-only None (rv == absent(), sv == none_val()) the rival "
            "yields none_val() but combined requires absent()."),
    },
    {
        "id": "partial-domain-first-element-no-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PARTIAL_FIRST,
        "refinement": (
            "A real patch that skipped the None-drop for the first header key "
            "would still send a None-valued first header; the F2P observable "
            "('Accept-Encoding' not in prep.headers) can land on that key, so the "
            "test FAILS -> NOT resolve."),
        "rationale": (
            "Rejection from postcondition (1)/(2): at i == 0 the rival carries the "
            "effective value through with no unset-drop, so on an input whose key 0 "
            "has effective value none_val() result[0] == none_val() != combined == "
            "absent(). The universal Forall over [0,n) catches the carve-out a "
            "'most positions' fuzzer would miss."),
    },
    {
        "id": "over-drop-real-request-override",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OVERDROP,
        "refinement": (
            "A real patch that dropped a header whenever the SESSION value was None "
            "-- even when the request explicitly overrides it with a real value -- "
            "would strip a legitimately-set per-request header. The PASS_TO_PASS "
            "request-construction suite would lose a header it must send -> NOT "
            "resolve."),
        "rationale": (
            "Rejection from postcondition (1): at a key with sv == none_val() and a "
            "real rv >= 1 the effective value is the real rv (request wins) so "
            "combined == rv, but the rival drops it to absent(). result[k] == "
            "absent() != combined."),
    },
    {
        "id": "pos-control-branch-reorder-fused",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": (
            "A structurally-different CORRECT impl: both branches reordered (negative "
            "condition first) and precedence+drop fused, keeping every gold framing "
            "assert (ev == effective, val == combined, the prefix-preservation Forall, "
            "the per-element pin, the length assert) verbatim. Must verify; else the "
            "spec rejects a faithful reordering (SPEC-TOO-STRONG)."),
    },
    {
        "id": "admissibility-f2p-shaped-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "A positive-control witness builds the issue's exact F2P shape (session-"
            "only None at key 0, real value at key 1, n == 2) and asserts EVERY "
            "frozen precondition clause at it -- the two Acc(.,1/2) shares (lendable "
            "from a freshly built list) and 0 <= 2 <= len(s), 2 <= len(r) -- plus the "
            "per-key answer the grounded oracle owes there (key 0 dropped to "
            "absent(), key 1 carried). Must verify; else the precondition rejects a "
            "normal merge input (PRECOND-TOO-STRONG). It still has teeth: a witness "
            "outside the frozen domain (n == 3 over two 2-element collections) fails "
            "the third Assert. The MustTerminate clause is excluded -- it is the "
            "caller's obligation level, not an admissibility fact -- and the case "
            "asserts the clauses instead of self-calling, because a self-call on a "
            "non-shrinking argument triple never delivers and would be rejected for "
            "THAT (the divergence case below owns that probe)."),
    },
    {
        "id": "diverge-restart-on-f2p-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _DIVERGE_F2P,
        "refinement": (
            "A faithful patch restarts merge_setting on the same two mappings "
            "whenever a merged value is the unset value, so a session-set None "
            "header makes the call never return. Measured: F2P "
            "test_headers_on_session_with_None_are_not_sent FAILS (5/6 F2P) and P2P "
            "test_header_remove_is_case_insensitive FAILS -> NOT resolve."),
        "rationale": (
            "Rejection from the DELIVERY obligation Requires(MustTerminate(2)): the "
            "self-call passes session/request/n straight through, so it cannot be "
            "discharged at a strictly lower level and Nagini reports 'Obligation "
            "leak check failed. Callee effective_collection might not take all "
            "unsatisfied obligations from the caller.' Every per-key value "
            "obligation is otherwise DISCHARGED -- Nagini assumes the callee's "
            "Ensures at the call site -- so the rejection is attributable solely to "
            "the non-delivery. Without that obligation this rival verifies while its "
            "patch hangs the very test the change is about, which is the "
            "verify-does-not-resolve shape this lane exists to catch. The guarded "
            "path is live, not vacuous: an Assert(False) in its place does not "
            "verify."),
    },
]

# No @ContractOnly axioms / consumed axioms in this bundle (meta.axioms == []).
# The single deep-model A-reference (combined == real merge_setting machinery)
# is validated by axiom_check.py / G-AX in Docker, outside PBT's spec lane.
AXIOM_TESTS = []
