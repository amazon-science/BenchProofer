# properties.py — PBT falsification battery for astropy__astropy-14309.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# # impl-start / # impl-end region) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes checked in Docker.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   is_recognised_input(stream_present, sig_matches, path_present,
#                       path_recognised, n_trailing, first_trailing_accepted)
#   is a first-match priority cascade over READ-ONLY value inputs (4 bools, an
#   int >= 0, a bool). It returns an int code R_TRUE(1)/R_FALSE(0)/R_FAULT(-1),
#   where R_FAULT models the IndexError that indexing an absent trailing
#   argument would raise.
#
#   The postcondition pins FOUR clauses:
#     (C1) Result() == decided(...)                              [total]
#     (C2) not stream & path & recognised      -> Result()==R_TRUE
#     (C3) not stream & path & not recognised  -> Result()==R_FALSE
#     (C4) not stream & path                   -> Result()!=R_FAULT
#   and the precondition carries a TOTAL-CORRECTNESS obligation:
#     (P3) Requires(MustTerminate(2))   # the predicate must ANSWER: a diverging
#          body (unbounded self-recursion / infinite loop) satisfies C1-C4 only
#          vacuously and is rejected by the termination obligation.
#   The load-bearing delta of the gold patch (one-armed `if ...: return True`
#   with NO else  ->  `return ...endswith(...)`) is sensed by C1/C3/C4: a
#   present-but-unrecognised path with NO trailing argument must return FALSE,
#   not fall through and FAULT (IndexError). The F2P test is exactly that:
#   is_fits("", "foo.bar", None) must return False, not raise IndexError.
#
# NOTE on frame-mutation (project directive 5): there is NO read-only HEAP
# input here. Every parameter is a Nagini value type (bool / int) passed by
# value — there is no Acc(x, 1/2) permission to overwrite, so the frame-mutation
# probe is VACUOUS for this instance (see 'assessment'). The FAULT sentinel is a
# returned VALUE, not a raise/side-effect, so it is fully captured by the value
# abstraction and discriminated by C4 — no capability-token is required either.
#
# NOTE on ungrounded-oracle echo (directive 2): `decided` is a @Pure function
# fully UNFOLDED over the input facts (model.py pure region) — it is not an
# opaque answer-key. An impl that "echoes" decided IS the gold behaviour, not a
# wrong echo, so there is no SPEC-TOO-WEAK echo cheat. We therefore include an
# honest cheapest-impl positive control (return decided(...)) as a control,
# expect="verify".

from pathlib import Path

INSTANCE = "astropy__astropy-14309"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of model.py (everything between the markers, exclusive).
# Every rival rewrites ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
    # index the trailing-argument tuple.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    # Only reached when neither a stream nor a path name is present: the first
    # trailing argument decides; indexing it when there is none is the fault.
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError("not unique: old block")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full model.py source whose impl region is `new_body` (the gold
    spec/pure/pre/post regions untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

# (A) PARTIAL-DOMAIN — the pre-patch one-armed fall-through. The path branch
# returns only in the recognised case (no else), so a present-but-unrecognised
# path falls through to the trailing-argument cascade and yields R_FAULT when
# n_trailing == 0. This is the EXACT pre-patch behaviour (model_prepatch.py).
# Diverges from `decided` only on the present-unrecognised-path sub-domain
# (C1 + C3 + C4). MUST be rejected.
_IMPL_PREPATCH_FALLTHROUGH = """    # PARTIAL-DOMAIN rival: pre-patch one-armed present-path branch (NO else).
    # Correct everywhere EXCEPT a present-but-unrecognised path, where it falls
    # through to the trailing-argument access and faults when n_trailing == 0.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        # (no else: fall through to the trailing-argument access below)
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""

# (B) VALUE-SWAP on the discriminating branch — the present-unrecognised-path
# case returns R_TRUE instead of R_FALSE. Total boolean (never faults, so it
# passes C4) but WRONG verdict on the unrecognised-path sub-domain (C1 + C3).
# MUST be rejected.
_IMPL_UNRECOGNISED_TRUE = """    # VALUE-SWAP rival: present unrecognised path returns TRUE (wrong verdict).
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_TRUE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""

# (C) NARROW FAULT-LEAK — diverge ONLY on the single F2P sub-domain: a present
# unrecognised path with NO trailing argument returns R_FAULT (mimicking the
# IndexError), but returns the correct R_FALSE for an unrecognised path WITH a
# trailing argument. A surgically-minimal rival that is correct on the whole
# domain except the exact failing F2P input. Fails C4 (and C1/C3) on that point.
# MUST be rejected.
_IMPL_NARROW_FAULT = """    # NARROW FAULT-LEAK rival: faults only on the exact F2P input (present
    # unrecognised path, no trailing argument); correct everywhere else.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        if n_trailing == 0:
            return R_FAULT()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""

# (D) UNCHANGED-BRANCH PARTIAL-DOMAIN — swap the stream-signature verdict
# (return R_FALSE on a matching signature). This branch is unchanged by the
# patch but is part of the same frozen spec; a rival must still honour it.
# Fails C1 on the present-stream sub-domain. MUST be rejected.
_IMPL_STREAM_SWAP = """    # UNCHANGED-BRANCH rival: stream branch returns the WRONG signature verdict.
    if stream_present:
        if sig_matches:
            return R_FALSE()
        return R_TRUE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""

# (E) POSITIVE CONTROL — structurally DIFFERENT but CORRECT. Keeps the exact
# first-match cascade ORDER, but reshapes the path branch into a single
# local-variable return (verdict assigned once, returned once) instead of two
# returns. No loops, no induction lemma; the same first-match semantics, so it
# MUST verify (else SPEC-TOO-STRONG).
_IMPL_POS_LOCALVAR = """    # POSITIVE CONTROL: same first-match cascade, path branch reshaped to a
    # single-return on a local (assign-once / return-once); semantically equal
    # to the gold cascade.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        path_verdict = R_FALSE()
        if path_recognised:
            path_verdict = R_TRUE()
        return path_verdict
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""

# (F) POSITIVE CONTROL — honest cheapest impl: return the grounded oracle
# directly. Because `decided` is fully unfolded over the inputs (not an opaque
# answer key), `return decided(...)` IS the gold behaviour and MUST verify.
# This is the directive-2 "grounded oracle => no wrong echo" positive control.
_IMPL_POS_DELEGATE = """    # POSITIVE CONTROL (grounded oracle): delegate to the pure cascade directly.
    # `decided` is fully unfolded over the inputs, so this is the gold behaviour
    # (not a wrong echo); it must verify.
    return decided(stream_present, sig_matches, path_present, path_recognised,
                   n_trailing, first_trailing_accepted)"""

# (G) ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped
# input (no stream, present unrecognised path, no trailing argument — the
# gh-14305 input). We edit ONLY the impl region (so same_spec holds): the body
# FIRST asserts, on concrete F2P-shaped facts, that every Requires clause is
# establishable (n_trailing>=0; first_trailing_accepted -> n_trailing>=1) and
# that the grounded pure oracle yields the desired R_FALSE verdict for those
# facts. (A recursive self-call is no longer usable as the witness: the
# MustTerminate obligation correctly forbids a self-call at the same measure.)
# If the precondition could not be established for this legitimate input the
# asserts would fail to verify => PRECOND-TOO-STRONG. The original gold cascade
# follows verbatim, so the postcondition obligation is unchanged.
_IMPL_ADMISS = """    # ADMISSIBILITY: assert the F2P-shaped input facts (no stream, present
    # unrecognised path, n_trailing==0, no trailing accept) satisfy every
    # Requires clause, and that the grounded oracle decides the desired
    # R_FALSE for them (else PRECOND-TOO-STRONG).
    f2p_n = 0
    f2p_accepted = False
    Assert(f2p_n >= 0)
    Assert(Implies(f2p_accepted, f2p_n >= 1))
    Assert(decided(False, False, True, False, f2p_n, f2p_accepted)
           == R_FALSE())
    # --- gold cascade verbatim below ---
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()"""


# (H) DIVERGENCE — a body that never answers. Delegates to itself with the
# same arguments; every value postcondition holds vacuously (the call's own
# contract supplies them), so ONLY the MustTerminate obligation can reject it.
# MUST be rejected (this is the total-correctness clause the spec pins).
_IMPL_DIVERGE_RECUR = """    # DIVERGENCE rival: unbounded self-recursion (never answers). Meets every
    # value postcondition vacuously; only the termination obligation rejects it.
    return is_recognised_input(stream_present, sig_matches, path_present,
                               path_recognised, n_trailing,
                               first_trailing_accepted)"""


SPEC_TESTS = [
    {
        "id": "partial-domain-prepatch-fallthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PREPATCH_FALLTHROUGH),
        "refinement": (
            "This is the pre-patch one-armed branch verbatim (model_prepatch.py): "
            "`if path_recognised: return True` with NO else. Its faithful real "
            "patch is the UNPATCHED is_fits, which on the F2P input "
            "is_fits('', 'foo.bar', None) falls through to "
            "isinstance(args[0], ...) with args==() and raises IndexError instead "
            "of returning False — so test_is_fits_gh_14305 FAILS. It does not "
            "resolve."),
        "rationale": (
            "Rejected by C1 (Result()==decided): on a present unrecognised path "
            "with n_trailing==0 it returns R_FAULT where decided requires "
            "R_FALSE; also violates C3 and C4. This is exactly what G-DIFF "
            "senses against model_prepatch.py."),
    },
    {
        "id": "value-swap-unrecognised-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_UNRECOGNISED_TRUE),
        "refinement": (
            "Faithful real patch: `return filepath.lower().endswith(...) or True` "
            "/ `return True` in the present-path branch — i.e. a present path is "
            "always recognised. On the F2P input is_fits('', 'foo.bar', None) it "
            "returns True, but the test asserts False, so test_is_fits_gh_14305 "
            "FAILS. It also misclassifies every non-FITS path as FITS (P2P "
            "read-dispatch regressions). It does not resolve."),
        "rationale": (
            "Rejected by C3 (not stream & path & not recognised -> Result()==R_FALSE) "
            "and C1: returns R_TRUE on a present unrecognised path. It passes C4 "
            "(never faults) yet is still rejected on the verdict value."),
    },
    {
        "id": "narrow-fault-leak-f2p-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_NARROW_FAULT),
        "refinement": (
            "Surgically-minimal rival that diverges ONLY on the exact F2P input: "
            "a present unrecognised path with no trailing argument yields the "
            "IndexError-fault (R_FAULT), but returns the correct False when a "
            "trailing argument is present. Its faithful real patch keeps the "
            "fall-through guarded to `len(args)==0`, so is_fits('', 'foo.bar', "
            "None) still raises IndexError and test_is_fits_gh_14305 FAILS. "
            "It does not resolve. This is the partial-domain attack pinned to the "
            "single input that fails first."),
        "rationale": (
            "Rejected by C4 (not stream & path -> Result()!=R_FAULT) and C1/C3 on "
            "the n_trailing==0 sub-domain. Demonstrates the spec is tight even on a "
            "one-point divergence — the FAULT sentinel is a returned value caught "
            "by the value abstraction, so no capability-token is needed."),
    },
    {
        "id": "unchanged-branch-stream-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_STREAM_SWAP),
        "refinement": (
            "Faithful real patch: the stream branch returns `sig != FITS_SIGNATURE` "
            "(inverted). The patch does not touch this branch, but a rival that "
            "shares the frozen spec must still honour it. On a real FITS stream "
            "(matching signature) is_fits returns False instead of True, breaking "
            "the FITS read/identify dispatch — the P2P TestSingleTable.* round-trip "
            "tests (which open real .fits streams) FAIL. It does not resolve."),
        "rationale": (
            "Rejected by C1 (Result()==decided): on a present stream with a "
            "matching signature decided requires R_TRUE but the rival returns "
            "R_FALSE. Confirms the spec pins the whole cascade, not just the "
            "patched branch."),
    },
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_LOCALVAR),
        "rationale": (
            "Structurally different but correct: same first-match cascade order, "
            "but the path branch is reshaped to assign a verdict to a local and "
            "return it once (instead of two returns). No loop / no induction "
            "lemma needed; semantically equal to the gold cascade, so it MUST "
            "verify (else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-control-grounded-oracle-delegate",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_DELEGATE),
        "rationale": (
            "Directive-2 grounded-oracle positive control: `decided` is fully "
            "unfolded over the inputs (not an opaque answer key), so delegating to "
            "it directly IS the gold behaviour and MUST verify. There is no wrong "
            "echo to exploit, so this is a positive control, not a weakness."),
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_ADMISS),
        "rationale": (
            "Asserts inside the impl region that the F2P-shaped facts (no "
            "stream, present unrecognised path, n_trailing==0, no trailing "
            "accept) establish every Requires clause (n_trailing>=0; "
            "first_trailing_accepted implies n_trailing>=1) and that the "
            "grounded pure oracle decides R_FALSE for them. If the "
            "precondition rejected this legitimate input the asserts would "
            "not verify (PRECOND-TOO-STRONG). Confirms the precondition "
            "admits the gh-14305 input; editing only the impl region keeps "
            "same_spec true."),
    },
    {
        "id": "divergence-self-recursion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_DIVERGE_RECUR),
        "refinement": (
            "A body that never answers: it delegates to itself forever. Its "
            "faithful real patch replaces the predicate's body with an "
            "unconditional self-call, so every invocation recurses until the "
            "interpreter's recursion limit — the F2P test errors instead of "
            "returning False. It does not resolve."),
        "rationale": (
            "Rejected by the MustTerminate(2) termination obligation (P3): a "
            "self-call at the same measure cannot discharge the caller's "
            "obligation, so the diverging body fails to verify even though it "
            "meets C1-C4 vacuously. This is the total-correctness clause the "
            "unified gate demands."),
    },
]

# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# The axioms region of model.py is EMPTY: no @ContractOnly axiom is consumed and
# no A-reference stdlib deep-model is referenced (meta.json axioms=[],
# deep_model_references=[]). The modeled delta is a pure control-flow decision
# over R-refined boolean / int inputs; no opaque callee appears inside any
# Ensures. There is therefore no axiom-soundness or axiom-containment obligation.
AXIOM_TESTS = []
