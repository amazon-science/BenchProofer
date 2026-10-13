# properties.py — PBT falsification battery for django__django-13821. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec. Axiom cases probe the A-reference deep model `lt_lex` against
# the REAL Python tuple `<` (see AXIOM_TESTS at the bottom).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   check_supported_version(version: List[int]) -> None
#   Models the gold start-up SQLite version guard check_sqlite_version(): reject
#   (raise) iff the runtime version is STRICTLY BELOW the minimum 3.9.0; accept
#   (normal return) iff at or above it. The minimum is min_version()==PSeq(3,9,0);
#   the ordering is the deep front-recursive fold lt_lex (== Python tuple `<`).
#   The gold change bumped the threshold from (3,8,3) to (3,9,0); the F2P mocks
#   sqlite_version_info=(3,8,11,1) and asserts ImproperlyConfigured IS raised.
#
#   PRECONDITION:
#     (P1) Requires(Acc(list_pred(version), 1/2))   # HALF permission => READ-ONLY
#     (P2) Requires(MustTerminate(2))               # TOTAL correctness: the guard
#            MUST terminate (return or raise). Closes the partial-correctness gap:
#            an impl that diverges (e.g. hangs instead of raising on an
#            unsupported runtime) satisfies the value postconditions only
#            vacuously and would hang start-up (and the F2P test) forever.
#   POSTCONDITION (three clauses; one framing/permission + two LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(version), 1/2))     # returns the read permission
#     (Q2) Ensures(not lt_lex(ToSeq(version), min_version()))
#            -- NORMAL RETURN reachable ONLY when version is NOT strictly below 3.9.0
#     (Q3) Exsures(UnsupportedConfiguration,
#                  Acc(list_pred(version),1/2) and lt_lex(ToSeq(version), min_version()))
#            -- the configuration error is raised on EXACTLY the strictly-below case
#   Q2 and Q3 together PIN the decision in BOTH directions: every below-threshold
#   runtime MUST raise, every at-or-above runtime MUST return normally. There is no
#   slack — a rival that misclassifies ANY input on EITHER side fails Q2 or Q3.
#
# FRAME-MUTATION lane is MANDATORY: `version` is Acc(list_pred(version),1/2)
#   (read-only). A rival that WRITES it must be REJECTED for INSUFFICIENT PERMISSION.
#   Byte-fuzzers never think to mutate the input; this is the #1 weakness class. The
#   real guard only READS Database.sqlite_version_info (a shared module attribute);
#   any write would corrupt the process-global SQLite version tuple.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q2/Q3 are pinned to
#   `lt_lex(ToSeq(version), min_version())` — GROUNDED entirely in the argument
#   `version` and the @Pure constant min_version()==PSeq(3,9,0). lt_lex is a @Pure
#   front-recursive fold fully unfolded over the sequence (no @ContractOnly axiom, no
#   opaque answer-key, no exact marker the impl could echo): the pure region COMPUTES
#   the ordering from the input, it does not assert an answer. There is therefore no
#   value an echo could carry that satisfies Q2/Q3 yet is wrong — the unique
#   satisfier IS the grounded decision. So the honest control is the cheapest faithful
#   impl that computes that decision (the positive control below), not a wrong echo.
#   See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: APPLIES and is directly exercised. The single behavioural
#   effect of this function is exactly a control-flow fork: raise vs normal return.
#   The value abstraction does NOT drop it — Q2 governs the normal-return path and Q3
#   governs the raise path, so a raise/return swap is observable to the spec. The
#   weak-always-accept (never raises) and weak-always-reject (always raises) rivals
#   are the capability-token-free discriminators for this fork (the exception class
#   IS the capability token here; both directions are pinned), so no separate token
#   plumbing is needed.
#
# PARTIAL-DOMAIN lane: heavily exercised. A rival can be correct on most of the
#   version domain yet diverge on the discriminating sub-domain:
#     - weak-major-only  : compares only the MAJOR component to 3 => correct on
#                          (2,*) reject / (4,*) accept but WRONG on the 3.8-vs-3.9
#                          minor boundary, which is EXACTLY the F2P (3,8,11,1).
#     - weak-prepatch    : the pre-patch threshold (3,8,3) => accepts (3,8,11,1)
#                          (the bug the gold fixes).
#
# AXIOM lane: meta.axioms == [] (no consumed @ContractOnly axiom) but
#   deep_model_references has ONE A-reference: lt_lex models Python's tuple `<`. Per
#   PBT_PLAN §2.4 / §4a an A-reference deep model is validated == the real callee on
#   every caller-reachable input. The real callee is a Python LANGUAGE operation
#   (tuple `<`), available with no repo import, so the probes run anywhere (Docker or
#   host). axiom-soundness fuzzes lt_lex == (tuple(a) < tuple(b)); axiom-containment
#   confirms every callee-input the model reaches (ToSeq(version) and
#   min_version()==(3,9,0), both finite int sequences) lies in tuple `<`'s domain.
from pathlib import Path

INSTANCE = "django__django-13821"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + the function signature). same_spec is
# computed over the spec_view, which elides every impl region (and nested
# invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    mn = [3, 9, 0]  # type: List[int]
    below = False
    i = 0
    n = len(version)
    m = len(mn)
    while i < n and i < m:
        # invariants-start
        Invariant(Acc(list_pred(version), 1 / 2))
        Invariant(Acc(list_pred(mn)))
        Invariant(0 <= i and i <= n and i <= m)
        Invariant(n == len(version) and m == len(mn))
        Invariant(ToSeq(mn) == min_version())
        Invariant(not below)
        # The undecided prefix has been consumed equal so far: the ordering of
        # the full sequences equals the ordering of their i-suffixes.
        Invariant(lt_lex(ToSeq(version), min_version())
                  == lt_lex(ToSeq(version).drop(i), min_version().drop(i)))
        # The comparison loop consumes the caller's termination obligation
        # with a strictly decreasing measure (m - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(m - i + 1))
        # invariants-end
        a = version[i]
        b = mn[i]
        Assert(ToSeq(version).drop(i)[0] == a)
        Assert(min_version().drop(i)[0] == b)
        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
        Assert(min_version().drop(i).drop(1) == min_version().drop(i + 1))
        if a < b:
            below = True
            break
        if a > b:
            below = False
            break
        i = i + 1
    else:
        # The loop ran to exhaustion (no break): one sequence ran out. The
        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
        # out of components first.
        Assert(i == n or i == m)
        if i < n:
            # minimum exhausted first => runtime is longer => not below.
            Assert(len(min_version().drop(i)) == 0)
            below = False
        elif i < m:
            # runtime exhausted first => runtime is a strict prefix => below.
            Assert(len(ToSeq(version).drop(i)) == 0)
            below = True
        else:
            # both exhausted simultaneously => equal => not below.
            Assert(len(ToSeq(version).drop(i)) == 0)
            Assert(len(min_version().drop(i)) == 0)
            below = False
    if below:
        raise UnsupportedConfiguration()
    return"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-branch-reorder: structurally DIFFERENT but behaviourally identical. The two
# early-exit branches of the loop body — `if a < b: below=True; break` and
# `if a > b: below=False; break` — are MUTUALLY EXCLUSIVE (a<b and a>b cannot both
# hold), so swapping their order is a pure source reshape with identical semantics.
# It keeps EVERY gold proof obligation verbatim: the same loop bound, the same six
# invariants (incl. the load-bearing lt_lex(full)==lt_lex(suffix.drop(i)) one), the
# same four per-step drop framing asserts, the same exhaustion `else` reasoning, and
# the same `if below: raise` tail (directive 2/3: no dropped lemma, no loop-direction
# flip, no forward-append against the front-recursive fold). Only the textual order
# of two independent guarded breaks changes. If it FAILS => SPEC-TOO-STRONG (a
# faithful, structurally-different correct impl is rejected).
_POS_REORDER = _IMPL.replace(
    "        if a < b:\n"
    "            below = True\n"
    "            break\n"
    "        if a > b:\n"
    "            below = False\n"
    "            break\n",
    "        if a > b:\n"
    "            below = False\n"
    "            break\n"
    "        if a < b:\n"
    "            below = True\n"
    "            break\n",
)
assert _POS_REORDER != _IMPL, "pos-branch-reorder did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is the single
# half-permission Acc(list_pred(version),1/2). This control keeps the gold impl
# VERBATIM but FIRST asserts, under that half-permission, that the reads a normal
# F2P-shaped runtime tuple needs are admitted — the length is readable and (when the
# version is non-empty, e.g. the F2P (3,8,11,1)) the first component is readable. No
# write, so no extra permission demand. If the precondition could not admit a
# legitimate runtime-version list, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) runtime version list is\n"
    "    # in-domain; the half-permission admits reading the length and elements.\n"
    "    Assert(len(version) >= 0)\n"
    "    if len(version) > 0:\n"
    "        Assert(version[0] == version[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `version` is Acc(list_pred(version),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: version[0] = version[0]. A no-op store, but a STORE — it demands
# FULL write permission on `version`, which the caller granted only at 1/2. The
# verifier must reject for insufficient permission. The store is placed FIRST, guarded
# by len>0 so it is reachable on the F2P input (3,8,11,1). (A real impl that mutated
# Database.sqlite_version_info would corrupt the process-global SQLite version for
# every subsequent backend operation; the spec must forbid ANY write.)
_FRAME_MUT = (
    "    if len(version) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        version[0] = version[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW RIVALS — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-always-accept: never raises — always takes the normal-return path
# (CONTROL-FLOW-EFFECT: the raise fork is removed). Then Q2
# (Ensures(not lt_lex(ToSeq(version), min_version()))) must hold for EVERY input, but
# on any strictly-below runtime (e.g. the F2P (3,8,11,1)) lt_lex is True => Q2 false.
# Bound to a bare `return None` (no `# type:` pitfall: None is the declared return).
_WEAK_ACCEPT = """\
    return"""

# weak-always-reject: always raises — every input takes the exceptional path
# (CONTROL-FLOW-EFFECT, the dual). Then Q3's condition
# `lt_lex(ToSeq(version), min_version())` must hold whenever it raises, but on an
# at-or-above runtime (e.g. the boundary (3,9,0), or (3,11,0)) lt_lex is False => the
# Exsures condition is violated.
_WEAK_REJECT = """\
    raise UnsupportedConfiguration()"""

# weak-major-only: PARTIAL-DOMAIN. Decides `below` from the MAJOR component alone
# (below iff empty, or version[0] < 3). Correct on the major-version sub-domain —
# (2,*) rejected, (4,*) accepted — but on the 3.x family it ALWAYS accepts, so it is
# WRONG on the 3.8-vs-3.9 minor boundary the gold change introduces: for the F2P
# (3,8,11,1) it returns normally while Q2 demands `not lt_lex((3,8,11,1),(3,9,0))`,
# which is false (3,8,11,1 IS below 3.9.0). Rejected by Q2.
_WEAK_MAJOR = """\
    below = False
    if len(version) == 0:
        below = True
    else:
        if version[0] < 3:
            below = True
    if below:
        raise UnsupportedConfiguration()
    return"""

# weak-prepatch: the EXACT pre-patch threshold (model_prepatch.py) — compares the
# runtime against the OLD minimum (3,8,3) instead of (3,9,0), spelled out with the
# same loop shape but mn=[3,8,3] and the mn invariant retargeted to PSeq(3,8,3). The
# post-loop `below` then reflects "version < 3.8.3", which is NOT connected to the
# frozen invariant about lt_lex(...,min_version()=3.9.0); on the F2P (3,8,11,1) the
# rival returns normally (3,8,11,1 >= 3,8,3) while Q2 demands the raise. Rejected
# (the spec senses the threshold bump — this is precisely G-DIFF).
_WEAK_PREPATCH = """\
    mn = [3, 8, 3]  # type: List[int]
    below = False
    i = 0
    n = len(version)
    m = len(mn)
    while i < n and i < m:
        # invariants-start
        Invariant(Acc(list_pred(version), 1 / 2))
        Invariant(Acc(list_pred(mn)))
        Invariant(0 <= i and i <= n and i <= m)
        Invariant(n == len(version) and m == len(mn))
        Invariant(ToSeq(mn) == PSeq(3, 8, 3))
        Invariant(MustTerminate(m - i + 1))
        # invariants-end
        a = version[i]
        b = mn[i]
        if a < b:
            below = True
            break
        if a > b:
            below = False
            break
        i = i + 1
    else:
        if i < n:
            below = False
        elif i < m:
            below = True
        else:
            below = False
    if below:
        raise UnsupportedConfiguration()
    return"""


# weak-diverge-reject: NON-TERMINATION (the exact break the G-EQ audit found while
# the spec was partial-correctness only). Keeps the gold comparison loop VERBATIM
# (so `below` is the correct decision) but on the reject path replaces the raise
# with an infinite `while True` loop. Under partial correctness this VERIFIED:
# the below-3.9.0 path never exits, so Q2 and Q3 held vacuously — and its faithful
# real patch (`if version_info < (3,9,0): while True: pass`) hung the F2P test
# (600s harness timeout, NOT resolved). With (P2) Requires(MustTerminate(2)) the
# diverging loop cannot discharge the caller's termination obligation (no
# decreasing MustTerminate measure exists for `while True`), so it is REJECTED.
_WEAK_DIVERGE = _IMPL.replace(
    "    if below:\n"
    "        raise UnsupportedConfiguration()\n"
    "    return",
    "    if below:\n"
    "        while True:\n"
    "            Invariant(Acc(list_pred(version), 1 / 2))\n"
    "    return",
)
assert _WEAK_DIVERGE != _IMPL, "weak-diverge-reject did not rewrite"


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT impl: the two MUTUALLY-EXCLUSIVE "
            "early-exit branches of the loop body (`if a < b: below=True; break` and "
            "`if a > b: below=False; break`) are swapped in source order. Semantics "
            "are identical (a<b and a>b cannot both hold) and EVERY gold proof "
            "obligation is kept verbatim — same loop bound, same six invariants "
            "(incl. lt_lex(full)==lt_lex(suffix.drop(i))), same per-step drop framing "
            "asserts, same exhaustion `else`, same `if below: raise` tail. If it FAILS "
            "=> SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (single Acc(list_pred(version),1/2) half-permission) "
            "must admit a normal F2P-shaped runtime version list: the length is "
            "readable and, when non-empty (the F2P (3,8,11,1)), the first component is "
            "readable under the half-permission. The gold impl is otherwise verbatim "
            "(only reads/asserts added inside the impl region, no write). If it FAILS "
            "=> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch only READS Database.sqlite_version_info (a process-global "
            "module attribute of sqlite3.dbapi2); it NEVER mutates it. A faithful real "
            "patch that wrote back into the version tuple (it is a tuple, so even "
            "in-place mutation of a list carrier would not faithfully model it, and "
            "any such normalisation would corrupt the global SQLite version for every "
            "subsequent backend check) would diverge from the gold's read-only guard "
            "— it would not be the gold patch and would not faithfully resolve. The "
            "store here is a no-op only by coincidence; the point is the spec must "
            "forbid ANY write to the input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `version` is granted at "
            "Acc(list_pred(version),1/2) (P1); the store version[0]=version[0] demands "
            "FULL write permission, which is not available, so the verifier rejects "
            "for INSUFFICIENT PERMISSION. The gold decision/return body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame is hollow (frame-mutation, the #1 "
            "weakness class; a byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-always-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ACCEPT),
        "refinement": (
            "always returning normally is what a real patch that DELETED the guard "
            "(or its raise) would do — it never rejects any runtime, so an embedded "
            "SQLite older than 3.9.0 passes start-up. It fails the F2P "
            "test_check_sqlite_version, which mocks sqlite_version_info=(3,8,11,1) and "
            "asserts ImproperlyConfigured IS raised. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(not lt_lex(ToSeq(version), min_version()))): on "
            "the normal-return path Q2 must hold for EVERY input, but for a "
            "strictly-below runtime (e.g. (3,8,11,1)) lt_lex(ToSeq(version), "
            "min_version()) is True, so `not lt_lex(...)` is False. CONTROL-FLOW: the "
            "raise fork is removed; the value abstraction senses it via Q2. If it "
            "VERIFIES => SPEC-TOO-WEAK (the reject condition is unpinned)."
        ),
    },
    {
        "id": "weak-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REJECT),
        "refinement": (
            "always raising is what a real patch that hard-coded the guard True (or "
            "compared against an impossibly-high minimum) would do — it rejects EVERY "
            "runtime, including the modern SQLite the project supports. It fails every "
            "P2P/start-up path that requires check_sqlite_version() to return normally "
            "on an in-spec runtime (e.g. (3,9,0) or newer). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (Exsures(UnsupportedConfiguration, ... and "
            "lt_lex(ToSeq(version), min_version()))): whenever it raises, Q3's "
            "condition lt_lex(ToSeq(version), min_version()) must hold, but on an "
            "at-or-above runtime (the boundary (3,9,0), or (3,11,0)) lt_lex is False, "
            "so the Exsures condition is violated. CONTROL-FLOW (dual): the "
            "normal-return fork is removed. If it VERIFIES => SPEC-TOO-WEAK (the "
            "accept condition is unpinned)."
        ),
    },
    {
        "id": "weak-major-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MAJOR),
        "refinement": (
            "comparing only the MAJOR component to 3 is what a real patch that wrote "
            "`if Database.sqlite_version_info[0] < 3:` would do. It is correct on the "
            "major-version sub-domain (a 2.x runtime rejected, a 4.x accepted) but "
            "ALWAYS accepts any 3.x runtime, so it does NOT reject (3,8,11,1) — the "
            "exact F2P discriminator. It fails test_check_sqlite_version (expects the "
            "raise on (3,8,11,1)). A genuine PARTIAL-DOMAIN break on the minor-version "
            "boundary; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(not lt_lex(ToSeq(version), min_version()))): for "
            "(3,8,11,1) the rival sets below=False (major==3, not <3) and returns "
            "normally, but lt_lex((3,8,11,1),(3,9,0)) is True so `not lt_lex(...)` is "
            "False. PARTIAL-DOMAIN: the rival pins only the major-component sub-domain, "
            "dropping the minor/patch ordering the spec requires. If it VERIFIES => "
            "SPEC-TOO-WEAK on the minor-version sub-domain."
        ),
    },
    {
        "id": "weak-diverge-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DIVERGE),
        "refinement": (
            "the faithful real patch is `if Database.sqlite_version_info < (3,9,0): "
            "while True: pass` — instead of raising ImproperlyConfigured on an "
            "unsupported runtime, start-up hangs forever. Empirically confirmed by "
            "the G-EQ audit: the patch applies cleanly, the F2P "
            "test_check_sqlite_version (mocks (3,8,11,1), expects the raise) times "
            "out after 600s (error=1, no tests pass) — does NOT resolve."
        ),
        "rationale": (
            "REJECTED by (P2) Requires(MustTerminate(2)): the `while True` loop on "
            "the reject path has no decreasing MustTerminate measure, so the caller's "
            "termination obligation cannot be discharged and verification fails. "
            "Under the previous partial-correctness spec this VERIFIED (Q2/Q3 held "
            "vacuously on the never-exiting path) — the exact spec-too-weak break "
            "(atk_7) the G-EQ audit demonstrated. If it VERIFIES => SPEC-TOO-WEAK "
            "(the termination obligation is unpinned)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the original guard "
            "compares against the OLD minimum (3,8,3) instead of (3,9,0). Its faithful "
            "real patch is the UNCHANGED repo (`if Database.sqlite_version_info < "
            "(3,8,3):`), which ACCEPTS (3,8,11,1) (it is >= 3.8.3 — exactly the bug the "
            "gold fixes) and so does NOT raise. It fails the F2P "
            "test_check_sqlite_version (now asserts the raise on (3,8,11,1)). Does NOT "
            "resolve — the precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(not lt_lex(ToSeq(version), min_version()))): the "
            "rival's `below` reflects 'version < (3,8,3)', not 'version < "
            "min_version()=(3,9,0)'. For (3,8,11,1) the loop finds 11>3 at the patch "
            "component and sets below=False, returning normally, but Q2 demands "
            "`not lt_lex((3,8,11,1),(3,9,0))`, which is False. (The retargeted mn "
            "invariant PSeq(3,8,3) is satisfiable but disconnected from the frozen "
            "min_version()=(3,9,0) the postcondition pins, so the proof of Q2 fails.) "
            "If it VERIFIES => SPEC-TOO-WEAK (the threshold bump is not enforced). "
            "Supporting near-miss carrying the strongest refinement (it is the literal "
            "pre-patch)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-reference deep model `lt_lex` vs the REAL Python tuple `<`.
# meta.axioms == [] (no consumed @ContractOnly axiom); deep_model_references has ONE
# A-reference (lt_lex models Python tuple comparison `<`). The real callee is a Python
# LANGUAGE operation, so the probes need NO repo import and run anywhere. The probes
# embed a faithful reimplementation of model.py's front-recursive lt_lex fold and
# compare it against the live `tuple(a) < tuple(b)`. (This mirrors axiom_check.py /
# G-AX, which already passes on the host; here it is re-run as the persisted PBT
# axiom lane: soundness == the deep model matches the real callee, containment ==
# every caller-reachable callee-input is in the callee's domain.)
# ---------------------------------------------------------------------------

# The model's front-recursive lt_lex fold, transcribed as plain Python (drop(1) is
# the tail). Shared text embedded into both probes.
_LT_LEX_SRC = '''
def lt_lex(a, b):
    """Faithful transcription of model.py's @Pure front-recursive lt_lex fold:
       len(a)==0 and len(b)==0 -> False; len(a)==0 -> True; len(b)==0 -> False;
       a[0]<b[0] -> True; a[0]>b[0] -> False; else recurse on the tails."""
    a = list(a)
    b = list(b)
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return True
    if len(b) == 0:
        return False
    if a[0] < b[0]:
        return True
    if a[0] > b[0]:
        return False
    return lt_lex(a[1:], b[1:])
'''

_AX_SOUND_PROBE = _LT_LEX_SRC + '''
import random
import sys

MIN_VERSION = (3, 9, 0)   # model.py min_version()

# Boundary version tuples the contract pins (incl. the F2P discriminators and the
# prefix/empty edge cases the front-recursive fold must get right).
boundary = [
    (),
    (3,), (3, 8), (3, 9), (3, 10),
    (3, 8, 2), (3, 8, 3), (3, 8, 11), (3, 8, 11, 1), (3, 8, 99), (3, 8, 3, 0),
    (3, 9, 0), (3, 9, 0, 0), (3, 9, 1), (3, 10, 0), (3, 11, 0),
    (2, 9, 9), (4, 0, 0), (3, 8, 3, 9, 9, 9),
]

fails = 0
# (axiom-soundness) the deep model lt_lex == the REAL Python tuple `<` on every
# boundary pair (BOTH directions, and against the minimum both ways).
for a in boundary:
    for b in boundary:
        model = lt_lex(a, b)
        real = (tuple(a) < tuple(b))
        if model != real:
            fails += 1
            print("UNSOUND lt_lex(%r,%r): model=%r real=%r" % (a, b, model, real))
for v in boundary:
    for pair in ((v, MIN_VERSION), (MIN_VERSION, v)):
        a, b = pair
        if lt_lex(a, b) != (tuple(a) < tuple(b)):
            fails += 1
            print("UNSOUND vs MIN lt_lex(%r,%r)" % (a, b))

# randomized fuzz over component sequences (lengths 0..5, components 0..12).
rng = random.Random(13821)
for _ in range(50000):
    a = [rng.randint(0, 12) for _ in range(rng.randint(0, 5))]
    b = [rng.randint(0, 12) for _ in range(rng.randint(0, 5))]
    if lt_lex(a, b) != (tuple(a) < tuple(b)):
        fails += 1
        print("UNSOUND fuzz lt_lex(%r,%r)" % (a, b))

# the discriminating F2P facts, explicitly.
checks = [
    (lt_lex((3, 8, 11, 1), MIN_VERSION) is True, "3.8.11.1 must be below 3.9.0 (rejected)"),
    ((3, 8, 11, 1) < MIN_VERSION, "real: 3.8.11.1 < 3.9.0"),
    (lt_lex((3, 9, 0), MIN_VERSION) is False, "3.9.0 must NOT be below itself (accepted)"),
    (not ((3, 9, 0) < MIN_VERSION), "real: 3.9.0 not < 3.9.0"),
    (not ((3, 8, 11, 1) < (3, 8, 3)), "pre-patch threshold 3.8.3 would accept 3.8.11.1 (the bug)"),
]
for ok, desc in checks:
    if not ok:
        fails += 1
        print("FACT FAIL:", desc)

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between deep lt_lex and real tuple `<`" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: deep lt_lex == real Python tuple `<` on %d boundary pairs + 50000 fuzz; "
      "reject decision == (version < (3,9,0)); F2P 3.8.11.1 rejected, 3.9.0 accepted." % (len(boundary) ** 2))
sys.exit(0)
'''

_AX_COVER_PROBE = _LT_LEX_SRC + '''
import random
import sys

MIN_VERSION = (3, 9, 0)   # model.py min_version() == PSeq(3,9,0)

# (axiom-containment) Which callee-inputs can the MODEL actually reach? The deep
# model lt_lex is applied by check_supported_version to EXACTLY two operands:
#   * left  = ToSeq(version), where `version: List[int]` (Requires only
#             Acc(list_pred(version),1/2) — any finite list of release-component
#             ints, including the empty list);
#   * right = min_version() == PSeq(3,9,0) — a fixed finite int sequence.
# The real callee is Python tuple comparison `<`, whose domain is any pair of tuples
# of mutually-orderable elements. Every reachable operand is a FINITE sequence of
# ints, and ints are totally ordered, so every caller-reachable callee-input lies in
# tuple `<`'s domain (no TypeError, total order, lexicographic). Covering MORE (e.g.
# mixed-type tuples) than the caller reaches would be sound, not a defect — we only
# need containment. We CONFIRM containment by executing tuple `<` on a heavy sample
# of the reachable operand space and asserting it raises nothing and the model agrees.
fails = 0
rng = random.Random(2024)

def reachable_versions():
    # representative reachable `version` lists: empty, length 1..6, ints incl. 0 and
    # large finer-level components (the spec explicitly pins "finer levels whose
    # numeric value is large", e.g. (3,8,11,1)); plus the boundary tuples.
    yield []
    for L in range(1, 7):
        for _ in range(3000):
            yield [rng.randint(0, 1000) for _ in range(L)]
    for t in [(3,), (3, 8), (3, 9), (3, 8, 11, 1), (3, 9, 0), (3, 11, 0),
              (2, 9, 9), (4, 0, 0), (3, 8, 3, 9, 9, 9)]:
        yield list(t)

for version in reachable_versions():
    left = tuple(version)          # ToSeq(version) operand
    right = MIN_VERSION            # min_version() operand
    try:
        real = (left < right)      # the real callee on a reachable input pair
    except TypeError as e:
        fails += 1
        print("CONTAINMENT FAIL: tuple `<` raised on reachable input %r < %r: %s"
              % (left, right, e))
        continue
    # the deep model must agree on every reachable input (containment + soundness on
    # the reachable slice).
    if lt_lex(version, MIN_VERSION) != real:
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL on reachable %r: model=%r real=%r"
              % (left, lt_lex(version, MIN_VERSION), real))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside tuple `<` domain "
          "or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input the model can reach (ToSeq(version) for a "
      "finite int list `version`, against min_version()==(3,9,0)) lies in Python tuple `<`'s "
      "domain (total order on ints, no TypeError) and the deep model agrees.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-lt_lex",
        "axiom": "lt_lex",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "lt_lex is an A-reference deep model of Python tuple comparison `<` (no "
            "consumed @ContractOnly axiom in this bundle). AXIOM-SOUNDNESS: the deep "
            "fold must equal the REAL callee `tuple(a) < tuple(b)` on every operand "
            "pair. The probe runs the live tuple `<` on 19^2 boundary pairs (incl. the "
            "F2P (3,8,11,1) and the (3,9,0) boundary and prefix/empty edges) + 50000 "
            "fuzz pairs and asserts agreement; mirrors axiom_check.py / G-AX. If the "
            "real callee disagrees anywhere => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-lt_lex",
        "axiom": "lt_lex",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: check_supported_version applies lt_lex to exactly "
            "(ToSeq(version), min_version()==(3,9,0)). `version` is any finite list of "
            "release-component ints (Requires grants only Acc(...,1/2); no length or "
            "value bound), so every reachable callee operand is a finite int sequence "
            "— totally ordered and lexicographically comparable, i.e. INSIDE Python "
            "tuple `<`'s domain. The probe samples the reachable operand space heavily "
            "(empty + lengths 1..6 with large finer-level components + the boundary "
            "tuples) and asserts tuple `<` raises nothing and the model agrees. A "
            "reachable input outside the domain => AXIOM-TOO-WEAK-FOR-CALLER (none "
            "expected: covering more than the caller reaches is sound, not a defect)."
        ),
    },
]
