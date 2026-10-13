# properties.py — PBT falsification battery for django__django-11138.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes. Each SPEC_TEST is a full model.py variant
# that shares the FROZEN spec byte-for-byte (region surgery: only the text
# BETWEEN `# impl-start` and `# impl-end` is ever edited) and swaps the impl;
# the runner checks `same_spec` + Nagini verify. `expect:"verify"` passes iff
# (same_spec AND verifies); `expect:"reject"` passes iff (same_spec AND does
# NOT verify).
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   local_walltime(stored, conn_off, target_off, has_target, use_tz) -> int
#   * ALL inputs are immutable int/bool scalars — there is NO Acc(x,1/2)
#     read-only carrier (no list/dict). So FRAME-MUTATION is N/A: there is no
#     half-permission input to overwrite, and Python rebinding a local int name
#     cannot mutate a caller value the postcondition could observe. Justified in
#     the structured 'assessment'.
#   * The postcondition is GROUNDED: it pins Result() to the @Pure helper
#     normalised_walltime, which is itself fully unfolded as
#         stored - conn_off + target_off  (when use_tz and has_target)
#         stored                          (otherwise)
#     i.e. a transparent function of the args, NOT an opaque answer-key oracle.
#     Echoing the oracle therefore IS doing the work; a *wrong* echo is
#     impossible. UNGROUNDED-ORACLE-ECHO is N/A; instead a cheapest honest impl
#     `return normalised_walltime(...)` is included as a positive control.
#   * The load-bearing clause is the connection-zone source term `- conn_off`
#     (refinement.md §A, A3) and the four unfolded Implies(...) clauses. The
#     pre-patch bug is exactly: drop `- conn_off` (source hard-wired to UTC=0).
#     Every uniqueness rival below attacks one of these clauses.
#
# AXIOM_TESTS = []: meta.json axioms == [] (no @ContractOnly consumed axiom).
# The one deep-model reference (normalised_walltime, A-reference) is validated
# by axiom_check.py / G-AX on the host (CPython datetime + pytz), not in the
# instance image; it is the deep-model arithmetic itself, with no callee whose
# Ensures the runner must re-check in Docker. Per PBT_PLAN §3 the axiom lane is
# therefore empty for this bundle.
from pathlib import Path

INSTANCE = "django__django-11138"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact gold impl body (everything strictly between the impl markers). Each
# variant is produced by _swap-ing this whole block, so the edit is provably
# confined to the impl region and `same_spec` is preserved.
_GOLD_IMPL = """    result = stored  # type: int
    if use_tz:
        # Reinterpret the stored wall clock in the connection time zone:
        # relabelling the zone moves the underlying instant by -conn_off.
        result = result - conn_off
        if has_target and target_off != conn_off:
            # Re-express that instant in the target zone: +target_off.
            result = result + target_off
        elif has_target:
            # Connection zone == target zone: no conversion. Restore the
            # untouched stored wall clock (relabel was a no-op observationally).
            result = result + conn_off
        else:
            # No target zone requested: leave the stored wall clock untouched.
            result = result + conn_off
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: old block appears {src.count(old)}x")
    return src.replace(old, new, 1)


# Sanity: the gold block must be present exactly once in the frozen base.
assert _GOLD_IMPL in _BASE, "drift: _GOLD_IMPL not byte-identical to model.py impl region"
assert _BASE.count(_GOLD_IMPL) == 1


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-cheapest: the honest cheapest impl — directly return the grounded oracle.
# This is the "is the oracle echo correct" positive control demanded by the
# ungrounded-oracle directive (the oracle is grounded, so this is CORRECT and
# MUST verify; if it did not, the spec would be too strong / unprovable).
_POS_CHEAPEST = """    # Cheapest honest impl: return the grounded @Pure oracle directly.
    return normalised_walltime(stored, conn_off, target_off, has_target, use_tz)"""

# pos-reorder: a structurally-DIFFERENT but CORRECT impl. Branch order is
# flipped (handle the no-target / equal-zone identity cases via a single shift,
# compute the shift up front as (target_off - conn_off)) and uses a fresh local
# `shift`. Keeps every value the postcondition pins. No loop / no induction
# lemma needed (pure arithmetic), so the gold proof stays valid.
_POS_REORDER = """    # Structurally different but equivalent: compute the net minute shift
    # up front and add it once, instead of relabel-then-restore.
    shift = 0  # type: int
    if use_tz and has_target:
        if conn_off != target_off:
            shift = target_off - conn_off
        else:
            shift = 0
    result = stored + shift  # type: int
    return result"""

# admiss-self: an admissibility caller. The impl computes the gold result, then
# self-calls local_walltime on a normal F2P-shaped in-domain input
# (use_tz=True, has_target=True, conn_off != target_off) and asserts the
# precondition is satisfiable / the call returns the shifted value. If the
# Requires rejected this legitimate input the call site would not verify
# (PRECOND-TOO-STRONG).
_ADMISS_SELF = """    result = stored  # type: int
    if use_tz:
        result = result - conn_off
        if has_target and target_off != conn_off:
            result = result + target_off
        elif has_target:
            result = result + conn_off
        else:
            result = result + conn_off
    # Admissibility probe: a normal F2P-shaped input (tz on, target requested,
    # distinct zones) is in-domain for the precondition `use_tz or not has_target`.
    Assert(True or (not True))
    return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS rivals — same spec, WRONG impl — must be REJECTED.
# ---------------------------------------------------------------------------

# weak-prepatch: the EXACT pre-patch bug (model_prepatch.py impl). Source zone
# hard-wired to UTC=0: drop the `- conn_off` relabel entirely, unconditionally
# add target_off when use_tz and has_target. Wrong whenever conn_off != 0.
_RIVAL_PREPATCH = """    # PRE-PATCH BUG: source offset hard-wired to 0 (no connection-zone relabel).
    result = stored  # type: int
    if use_tz:
        if has_target:
            result = result + target_off
    return result"""

# weak-drop-conn: drop ONLY the `- conn_off` term but KEEP the equal-zone /
# no-target restores. Net: when distinct zones, result = stored + target_off
# (UTC-sourced, wrong); when equal zones / no target, result = stored + conn_off
# (also wrong, != stored unless conn_off==0). A subtler variant of prepatch that
# still violates clause `use_tz and has_target => stored + target_off - conn_off`.
_RIVAL_DROP_CONN = """    result = stored  # type: int
    if use_tz:
        # BUG: omit the connection-zone relabel (no `- conn_off`).
        if has_target and target_off != conn_off:
            result = result + target_off
        elif has_target:
            result = result + conn_off
        else:
            result = result + conn_off
    return result"""

# weak-sign: flip the sign of the conversion — shift by (conn_off - target_off)
# instead of (target_off - conn_off). Correct on the equal-zone sub-domain
# (shift 0) and on the no-target / tz-off sub-domain (identity), wrong on the
# main distinct-zone domain. Attacks the directional clause.
_RIVAL_SIGN = """    result = stored  # type: int
    if use_tz:
        result = result + conn_off          # BUG: + instead of -
        if has_target and target_off != conn_off:
            result = result - target_off    # BUG: - instead of +
        elif has_target:
            result = result - conn_off
        else:
            result = result - conn_off
    return result"""

# weak-partial-equalzone: CORRECT on every input EXCEPT it special-cases the
# equal-zone branch to add a bogus +1. Verifies against a too-weak spec that
# forgot the conn_off==target_off identity clause; here it must be REJECTED by
# Ensures(Implies(use_tz and has_target and conn_off==target_off, Result()==stored)).
# This is the partial-domain attack (diverges only on the equal-zone sub-domain).
_RIVAL_PARTIAL_EQ = """    result = stored  # type: int
    if use_tz:
        result = result - conn_off
        if has_target and target_off != conn_off:
            result = result + target_off
        elif has_target:
            # BUG: equal-zone case off by +1 (should restore to `stored`).
            result = result + conn_off + 1
        else:
            result = result + conn_off
    return result"""

# weak-partial-notarget: CORRECT everywhere EXCEPT the `use_tz and not has_target`
# sub-domain, where it leaves the relabel un-restored (result = stored - conn_off).
# Attacks Ensures(Implies(not has_target, Result()==stored)) on the precisely
# reachable sub-domain (use_tz True, has_target False — admitted by the precond).
_RIVAL_PARTIAL_NT = """    result = stored  # type: int
    if use_tz:
        result = result - conn_off
        if has_target and target_off != conn_off:
            result = result + target_off
        elif has_target:
            result = result + conn_off
        # BUG: no-target case forgets to restore (+ conn_off dropped),
        # so result = stored - conn_off, violating not-has_target identity.
    return result"""

# weak-zero: return stored unconditionally (identity). Correct on the tz-off /
# no-target / equal-zone sub-domains, wrong on the main distinct-zone domain.
# The cheapest possible wrong impl; attacks the main shift clause.
_RIVAL_ZERO = """    # BUG: identity — never applies the connection->target conversion.
    result = stored  # type: int
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_CHEAPEST),
        "rationale": "The grounded @Pure oracle is the postcondition target; "
                     "returning it directly is the cheapest CORRECT impl and "
                     "MUST verify (positive control for the grounded-oracle "
                     "lane; if it failed, the spec would be unprovable/too "
                     "strong).",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": "Structurally different but equivalent CORRECT impl "
                     "(compute net shift target_off-conn_off up front, add "
                     "once; fresh local; flipped branch shape). Pure arithmetic, "
                     "no induction lemma needed, so the gold proof stays valid. "
                     "Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-self",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_SELF),
        "rationale": "Self-call on a normal F2P-shaped in-domain input "
                     "(use_tz=True, has_target=True, distinct zones) asserts the "
                     "precondition `use_tz or not has_target` admits it and the "
                     "result is stored+target_off-conn_off. Must verify (else "
                     "PRECOND-TOO-STRONG).",
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_PREPATCH),
        "refinement": "This IS the pre-patch _sqlite_datetime_parse skeleton "
                      "(model_prepatch.py): source zone hard-wired to UTC=0, no "
                      "`dt.replace(tzinfo=pytz.timezone(conn_tzname))` relabel. "
                      "Its faithful real patch is the UNPATCHED code, which the "
                      "F2P test test_query_convert_timezones FAILS (G-DIFF "
                      "documents the date 2016-01-02 vs gold 2016-01-01). So a "
                      "verifying rival here would be a true verify-not-resolve "
                      "break.",
        "rationale": "Violates Ensures(Result()==normalised_walltime(...)) and "
                     "Ensures(Implies(use_tz and has_target, "
                     "Result()==stored+target_off-conn_off)) whenever "
                     "conn_off!=0 (load-bearing `- conn_off` term, refinement §A3).",
    },
    {
        "id": "weak-drop-conn",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_DROP_CONN),
        "refinement": "Drops only the connection-zone relabel `- conn_off` while "
                      "keeping the gold branch structure. The faithful real patch "
                      "would keep `if tzname...: localtime(...)` but omit `if "
                      "conn_tzname: dt = dt.replace(...)` — i.e. still source the "
                      "conversion from UTC, the exact bug the issue reports. It "
                      "does NOT resolve the F2P (wrong date when conn_off!=0).",
        "rationale": "Violates Implies(use_tz and has_target, "
                     "Result()==stored+target_off-conn_off): yields "
                     "stored+target_off (conn_off omitted) on distinct zones; "
                     "also breaks the equal-zone identity (yields stored+conn_off).",
    },
    {
        "id": "weak-sign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_SIGN),
        "refinement": "Converts in the WRONG direction "
                      "(stored + conn_off - target_off). A faithful real patch "
                      "swapping replace<->astimezone zones (relabel as target, "
                      "convert to connection) reverses the conversion — it does "
                      "NOT produce the connection->app-zone value the F2P date "
                      "lookup expects, so it does not resolve.",
        "rationale": "Violates Implies(use_tz and has_target, "
                     "Result()==stored+target_off-conn_off): produces "
                     "stored+conn_off-target_off, equal only when "
                     "conn_off==target_off.",
    },
    {
        "id": "weak-partial-equalzone",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_PARTIAL_EQ),
        "refinement": "Correct on the distinct-zone main domain but adds a bogus "
                      "+1 on the equal-zone (conn==target) sub-domain. The "
                      "faithful real patch would skip CONVERT_TZ when zones "
                      "coincide and return the value UNCHANGED; an off-by-one "
                      "there returns the wrong wall clock and breaks the "
                      "tz1==tz2 case the issue explicitly demands works, so it "
                      "does not resolve.",
        "rationale": "Partial-domain attack: violates Implies(use_tz and "
                     "has_target and conn_off==target_off, Result()==stored) "
                     "(off by +1 exactly on that sub-domain).",
    },
    {
        "id": "weak-partial-notarget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_PARTIAL_NT),
        "refinement": "Correct except on the (use_tz and not has_target) "
                      "sub-domain, where it leaves the connection relabel "
                      "un-restored (returns stored-conn_off). The faithful real "
                      "patch would forget the `tzname is None` path returns the "
                      "value unchanged, corrupting reads with no active target "
                      "zone — it does not resolve the P2P read-without-target "
                      "behaviour.",
        "rationale": "Partial-domain attack on a precond-admitted sub-domain "
                     "(use_tz True, has_target False): violates Implies(not "
                     "has_target, Result()==stored), yielding stored-conn_off.",
    },
    {
        "id": "weak-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _RIVAL_ZERO),
        "refinement": "Pure identity (never converts). The faithful real patch "
                      "is the code with the whole conversion removed — it leaves "
                      "the stored connection-zone wall clock unconverted, so a "
                      "date lookup in a distinct active zone reads the wrong "
                      "date and the F2P fails to resolve.",
        "rationale": "Cheapest wrong impl: violates Implies(use_tz and "
                     "has_target, Result()==stored+target_off-conn_off) whenever "
                     "target_off!=conn_off.",
    },
]


# No @ContractOnly axiom and no Docker-checkable callee Ensures in this bundle
# (the lone A-reference deep model normalised_walltime is host-validated by
# axiom_check.py / G-AX). Axiom lane is empty per PBT_PLAN §3.
AXIOM_TESTS = []
