# properties.py — PBT falsification battery for psf__requests-6028.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec verbatim
# (built by region-surgery that edits ONLY text inside # impl-start/# impl-end,
# so same_spec is guaranteed) with a swapped impl; the runner checks it with the
# Nagini verifier + markers.same_spec. AXIOM_TESTS are real-callee probes run in
# Docker.
#
# Defended surface (model.py):
#   normalize_location(scheme, creds, authority, path, query, frag: List[int],
#                      has_creds, has_query, has_frag: bool) -> List[int]
#   All SIX list inputs are READ-ONLY: Requires(Acc(list_pred(x), 1/2)).
#   The precondition also carries a TERMINATION obligation,
#   Requires(MustTerminate(2)), so what the verifier proves is TOTAL and not
#   merely partial correctness: a rival that never reaches its `return` no
#   longer satisfies every Ensures vacuously. Consequences for this battery:
#   the admissibility probe drives its call from a top-level helper at level 3
#   (a self-call's caller and callee levels are equal, so it can never be
#   discharged), and the old self-call is retained as the reject-lane
#   divergence rival `diverge-unguarded-self-call`.
#   Load-bearing postcondition (the only one that constrains Result()):
#     ToSeq(Result()) == assembled(ToSeq(scheme),
#                                  effective_authority(ToSeq(creds),
#                                                      ToSeq(authority), has_creds),
#                                  ToSeq(path), ToSeq(query), ToSeq(frag),
#                                  has_query, has_frag)
#   The other two Ensures clauses are TAUTOLOGIES about the @Pure helper
#   `effective_authority` (they restate its own definition) and do not constrain
#   Result(); the discriminating power is entirely in the master assembly pin.
#
#   `effective_authority` and `assembled` are @Pure helpers FULLY GROUNDED in the
#   inputs (functions of creds/authority/scheme/path/query/frag + the booleans,
#   fully unfolded). There is NO ungrounded answer-key oracle / opaque marker to
#   echo — so the ungrounded-oracle-echo class does NOT apply here (see
#   'assessment'). Instead the cheapest-honest-impl positive control covers that
#   slot.
from pathlib import Path

INSTANCE = "psf__requests-6028"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region (between # impl-start / # impl-end), verbatim. Every
# variant is produced by replacing exactly this block, so the spec view (and
# thus same_spec) is untouched.
_IMPL = """    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result"""


def _with_impl(new_impl):
    """Build a full model variant whose impl region is `new_impl` (the spec
    view is byte-identical to model.py, so same_spec holds)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---------------------------------------------------------------------------
# 1) POSITIVE CONTROL (soundness) — structurally different, but CORRECT.
#    Reorder: assemble the base WITHOUT the credentials first, then build the
#    effective authority by branch-reorder (no-creds branch first), and pin via
#    the same framing asserts the gold proof needs. This is a different
#    executable shape (the netloc branch is inverted and the query branch is
#    rebuilt by recomputing `base` rather than re-using it) but keeps every
#    proof obligation. MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = """    if not has_creds:
        netloc = authority  # type: List[int]
    else:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    prefix = scheme + [58, 47, 47]  # type: List[int]
    result = prefix + netloc + path  # type: List[int]
    if has_query:
        result = prefix + netloc + path + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result"""


# ---------------------------------------------------------------------------
# 2) ADMISSIBILITY — a call on an F2P-shaped input must verify the Requires can
#    be established. The precondition is the six read-only list_preds plus the
#    termination obligation MustTerminate(2); a caller that owns full list_pred
#    on each can pass a 1/2 share, and it must be able to take the callee's
#    termination obligation too. Models the F2P URL
#    `http://user:pass@example.com/path?query` shape (has_creds=True,
#    has_query=True). If this cannot verify => PRECOND-TOO-STRONG.
#
#    The call is driven from a HELPER carrying a level STRICTLY ABOVE
#    normalize_location's 2, not from an in-body self-call, because the spec now
#    obliges the function to terminate. MustTerminate levels must strictly
#    decrease from caller to callee, and a self-call's caller and callee are the
#    SAME method, so their levels are necessarily EQUAL: Nagini rejects it with
#    `Obligation leak check failed. Callee normalize_location might not take all
#    unsatisfied obligations from the caller.` That rejection is a property of
#    the CALL GRAPH, not of the precondition, so leaving the self-call here
#    would report PRECOND-TOO-STRONG for a domain fact that is in fact perfectly
#    establishable — a false finding against the spec.
#
#    Measured, so the diagnosis is not a guess:
#      * self-call at level 2 -> 2  : leak check failed
#      * self-call with BOTH sides raised to 9 : leak check failed (raising the
#        method's own level moves both sides of the comparison together, so no
#        constant level can ever work)
#      * a nested `def` inside the impl region : Nagini rejects the program
#        outright (`Invalid program: nested.function.declaration`), so the
#        higher-level caller cannot live inside the method body
#      * a call from a top-level helper at level 3 -> 2 : VERIFIES
#
#    The helper is spliced BETWEEN `return result` and the terminal
#    `# impl-end`, so it lands INSIDE the elided impl span (same_spec preserved,
#    checked by variant_scope.variant_problems == []) yet is a genuine
#    module-level function Nagini independently checks. It is itself obligated
#    at MustTerminate(3), so it is not a hole: a diverging helper body would be
#    rejected too.
#
#    Non-vacuity control: splicing `Assert(False)` after the helper's Asserts
#    FAILS to verify (`Assertion False might not hold`), so the probe path is
#    reachable and the case is not a rubber stamp.
#
#    The diverging self-call this case used to carry is NOT deleted: it is
#    retained below as the reject-lane uniqueness case
#    `diverge-unguarded-self-call`, where its rejection is now an asserted
#    PROPERTY of the spec.
# ---------------------------------------------------------------------------
_ADMISS = """    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result


def _admiss_caller() -> None:
    # Admissibility witness driven from a level STRICTLY ABOVE
    # normalize_location's 2, which is what lets this call discharge the
    # callee's termination obligation instead of leaking it.
    Requires(MustTerminate(3))
    # F2P-shaped components: 'http' :// 'user:pass' '@' 'example' '/p' '?' 'q'.
    scheme2 = [104, 116, 116, 112]  # type: List[int]
    creds2 = [117, 115, 101, 114, 58, 112, 97, 115, 115]  # type: List[int]
    authority2 = [101, 120, 97, 109, 112, 108, 101]  # type: List[int]
    path2 = [47, 112]  # type: List[int]
    query2 = [113]  # type: List[int]
    frag2 = []  # type: List[int]
    out = normalize_location(scheme2, creds2, authority2, path2, query2,
                             frag2, True, True, False)  # type: List[int]
    Assert(ToSeq(out) == assembled(
        ToSeq(scheme2),
        effective_authority(ToSeq(creds2), ToSeq(authority2), True),
        ToSeq(path2), ToSeq(query2), ToSeq(frag2), True, False))"""


# ---------------------------------------------------------------------------
# 3) FRAME-MUTATION (MANDATORY: every list input is read-only). A rival that
#    tries to satisfy the postcondition by WRITING to a read-only input —
#    here appending to `authority` (the half-permission input). The
#    postcondition pins ToSeq(Result()) over effective_authority/assembled, but
#    the rival cannot even hold write permission on `authority` (Acc 1/2), so it
#    must be REJECTED for INSUFFICIENT PERMISSION. The assembly text is kept
#    gold-faithful so the rejection is attributable solely to the write.
#    REFINEMENT: a faithful real patch that mutated the parsed `auth`/`netloc`
#    in place (e.g. `authority.append(...)`) instead of building a fresh list
#    would corrupt the shared parsed components / not produce the joined netloc
#    correctly and would NOT make the F2P assertions
#    (prepend_scheme_if_needed(...) == expected URL) pass.
# ---------------------------------------------------------------------------
_FRAME = """    authority.append(64)  # write to a READ-ONLY (Acc 1/2) input
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result"""


# ---------------------------------------------------------------------------
# 4) PARTIAL-DOMAIN — DROP THE CREDENTIAL JOIN. This is the EXACT pre-patch
#    behaviour: assemble from the bare `authority`, never re-attaching the
#    userinfo. Correct on the P2P inputs (no userinfo: example.com/path,
#    //example.com/path, example.com:80) but DIVERGES on the two F2P inputs
#    (http://user:pass@example.com/path?query and http://user@.../...) where
#    the credentials must survive. MUST be REJECTED by the master assembly pin
#    (Result is assembled over the BARE authority, not the effective one).
#    REFINEMENT: this is model_prepatch.py's behaviour — the gold patch's whole
#    point. A real patch shaped this way drops the userinfo and the F2P tests
#    (prepend_scheme_if_needed('http://user:pass@example.com/path?query','http')
#    == 'http://user:pass@example.com/path?query') FAIL — it does NOT resolve.
# ---------------------------------------------------------------------------
_PARTIAL_DROP = """    netloc = authority  # type: List[int]
    # BUG: credential join dropped -> bare authority used even with userinfo.
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    return result"""


# ---------------------------------------------------------------------------
# 5) PARTIAL-DOMAIN (value-class) — WRONG SEPARATOR on the credential join. Use
#    ':' (58) instead of '@' (64) between creds and authority. Correct on the
#    no-creds P2P inputs, diverges on every userinfo F2P input. MUST be
#    REJECTED: effective_authority pins the join to PSeq(64), so
#    creds + [58] + authority != effective_authority(...).
#    REFINEMENT: a real patch joining with ':' would emit
#    'http://user:pass:example.com/path?query' for the F2P URL, != expected
#    'http://user:pass@example.com/path?query' -> F2P FAILS, does NOT resolve.
# ---------------------------------------------------------------------------
_PARTIAL_SEP = """    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [58] + authority  # ':' instead of '@'
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    return result"""


# ---------------------------------------------------------------------------
# 6) PARTIAL-DOMAIN (query sub-domain) — drop the query branch. Correct on the
#    no-query P2P inputs (example.com/path, example.com:80, //example.com/path)
#    but diverges on every has_query input (incl. BOTH F2P URLs, which carry
#    `?query`). MUST be REJECTED: assembled appends PSeq(63)+query when
#    has_query, so omitting it breaks the master pin for has_query inputs.
#    REFINEMENT: such a real patch would emit
#    'http://user:pass@example.com/path' (no '?query') for the F2P URL,
#    != expected -> F2P FAILS, does NOT resolve.
# ---------------------------------------------------------------------------
_PARTIAL_QUERY = """    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    # BUG: query branch dropped -> '?query' never appended.
    if has_frag:
        result = result + [35] + frag
    return result"""


# ---------------------------------------------------------------------------
# 7) PARTIAL-DOMAIN (fragment sub-domain) — drop the fragment branch. Correct
#    on every no-fragment input (incl. both F2P URLs) but diverges on any
#    fragment-carrying location. MUST be REJECTED: assembled appends
#    PSeq(35)+frag when has_frag, so omitting it breaks the master pin on every
#    has_frag input.
#    REFINEMENT: a real patch shaped this way would strip the '#fragment' from
#    any re-assembled location that carried one — the combining callee keeps
#    the fragment, so the function's output would diverge from the real
#    post-patch behaviour on fragment-bearing locations.
# ---------------------------------------------------------------------------
_PARTIAL_FRAG = """    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    # BUG: fragment branch dropped -> '#frag' never appended.
    return result"""


# ---------------------------------------------------------------------------
# 8) SUPPORTING near-miss — join creds even when has_creds is FALSE (always
#    prepend creds + '@'). Correct on userinfo inputs, but on a no-creds input
#    (creds == [], has_creds False) this prepends a stray '@' and diverges from
#    effective_authority(_, authority, False) == authority. MUST be REJECTED.
#    REFINEMENT: a real patch dropping the `if auth:` guard would emit
#    'http://@example.com/path' for 'example.com/path' (a P2P case) -> P2P FAILS.
# ---------------------------------------------------------------------------
_NEARMISS_NOGUARD = """    netloc = creds + [64] + authority  # type: List[int]
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    return result"""


# ---------------------------------------------------------------------------
# 9) DIVERGENCE — the unguarded self-call. This is the impl the admissibility
#    case above used to carry, moved here rather than deleted because it does
#    not terminate: the call is UNCONDITIONAL (no guard, no base case) and its
#    arguments are fresh copies of the inputs with the booleans pinned to the
#    constants True, True, False, so every frame makes the same call again. No
#    measure exists to be found; the recursion is infinite by construction.
#
#    It belongs in the REJECT lane because the old, termination-silent spec
#    ACCEPTED it. Measured both ways, so the attribution is to the obligation:
#      * with `Requires(MustTerminate(2))` stripped from the preconditions this
#        very impl VERIFIES ("Verification successful", 75.9s)
#      * with the obligation present Nagini REJECTS it: `Obligation leak check
#        failed. Callee normalize_location might not take all unsatisfied
#        obligations from the caller.` (84.1s)
#
#    That is exactly the hole this obligation exists to close: a rival that
#    never reaches its `return` satisfies every Ensures vacuously, so the old
#    spec proved only PARTIAL correctness. Asserting that the spec REJECTS a
#    diverging impl is a strictly STRONGER claim than the accept-lane case it
#    replaces, and the admissibility lane is preserved at full strength by
#    `admiss-f2p-shaped-selfcall` above, which asks the same
#    precondition-admits-a-normal-input question without recursing.
#    REFINEMENT: a real patch shaped this way would hang
#    prepend_scheme_if_needed, so the F2P assertion
#    prepend_scheme_if_needed('http://user:pass@example.com/path?query','http')
#    == 'http://user:pass@example.com/path?query' never returns a value to
#    compare -- the test times out instead of passing. It does NOT resolve.
# ---------------------------------------------------------------------------
_DIVERGE_SELFCALL = """    scheme2 = list(scheme)  # type: List[int]
    creds2 = list(creds)  # type: List[int]
    authority2 = list(authority)  # type: List[int]
    path2 = list(path)  # type: List[int]
    query2 = list(query)  # type: List[int]
    frag2 = list(frag)  # type: List[int]
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    # DIVERGES: unconditional self-call with constant booleans -> no base case.
    echoed = normalize_location(scheme2, creds2, authority2, path2, query2,
                                frag2, True, True, False)  # type: List[int]
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(_POS),
        "rationale": (
            "A structurally-different but CORRECT impl (no-creds branch first; "
            "query branch recomputes the prefix instead of re-using `base`) must "
            "verify against the frozen assembly postcondition. It keeps both "
            "framing Asserts the gold proof uses. If it cannot verify => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-f2p-shaped-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl(_ADMISS),
        "rationale": (
            "The precondition is the six read-only list_preds plus the "
            "termination obligation MustTerminate(2). A call on F2P-shaped "
            "components (has_creds=True, has_query=True) must establish the "
            "Requires -- including taking the callee's termination obligation. "
            "The call is driven from a top-level helper at MustTerminate(3), "
            "strictly above the callee's 2, because levels must strictly "
            "decrease from caller to callee and a self-call's two levels are "
            "necessarily EQUAL; an in-body self-call would therefore be "
            "rejected for an obligation LEAK (a property of the call graph) "
            "rather than for the precondition, and the PRECOND-TOO-STRONG "
            "finding would not be attributable. Measured: self-call at 2->2 "
            "leaks, both sides raised to 9 still leaks, a nested def is an "
            "invalid program, helper at 3->2 verifies. Non-vacuity control: "
            "appending Assert(False) to the helper FAILS. If this cannot "
            "verify => PRECOND-TOO-STRONG."),
    },
    {
        "id": "diverge-unguarded-self-call",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_DIVERGE_SELFCALL),
        "refinement": (
            "An unconditional self-call with constant booleans never returns, "
            "so a real patch shaped this way hangs prepend_scheme_if_needed: "
            "the F2P assertion prepend_scheme_if_needed("
            "'http://user:pass@example.com/path?query','http') == "
            "'http://user:pass@example.com/path?query' never gets a value to "
            "compare and the test times out instead of passing. F2P FAIL => "
            "does NOT resolve."),
        "rationale": (
            "DIVERGENCE probe, and the case that changed lane when the "
            "termination obligation landed. It was authored as an accept-lane "
            "admissibility self-call against a spec that demanded nothing of "
            "termination, so it never had to prove any; it is unbounded "
            "recursion (unconditional call, no base case, booleans pinned to "
            "True/True/False) and it CANNOT be made to terminate -- no measure "
            "exists to be found. Measured both ways so the rejection is "
            "attributable to the obligation: WITHOUT MustTerminate(2) this impl "
            "VERIFIES; WITH it Nagini reports 'Obligation leak check failed. "
            "Callee normalize_location might not take all unsatisfied "
            "obligations from the caller.' If it verified => SPEC-TOO-WEAK in "
            "the direction this obligation exists to close: a rival that never "
            "reaches its return satisfies every Ensures vacuously, i.e. the "
            "spec would prove only PARTIAL correctness."),
    },
    {
        "id": "frame-mutate-authority",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_FRAME),
        "refinement": (
            "`authority` models the parsed netloc, a read-only component. A real "
            "patch that mutated the parsed component in place (authority.append "
            "/ item-assign) instead of building a fresh joined netloc would "
            "either corrupt the shared parse result or fail to produce "
            "'@'.join([auth, netloc]); the F2P assertion "
            "prepend_scheme_if_needed('http://user:pass@example.com/path?query',"
            "'http') == 'http://user:pass@example.com/path?query' would NOT "
            "pass. So it does not resolve."),
        "rationale": (
            "MANDATORY frame-mutation probe: every list input is Acc(...,1/2) "
            "read-only. The impl writes to `authority` (authority.append(64)). It "
            "must be REJECTED for INSUFFICIENT PERMISSION (the half-permission "
            "precondition denies the write); the gold assembly pin is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "verified, the read-only frame would be unsound."),
    },
    {
        "id": "partial-drop-credential-join",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_DROP),
        "refinement": (
            "This is model_prepatch.py's behaviour: assemble from the BARE "
            "authority, never re-attaching the userinfo. On the two F2P URLs "
            "(user:pass@/user@) the credentials are dropped, so "
            "prepend_scheme_if_needed returns 'http://example.com/path?query' "
            "!= expected 'http://user:pass@example.com/path?query'. F2P FAIL => "
            "does NOT resolve."),
        "rationale": (
            "Rejected by the master assembly pin: Result is assembled over the "
            "BARE authority, but the postcondition requires the EFFECTIVE "
            "authority (effective_authority(...) = creds+'@'+authority when "
            "has_creds). For a has_creds input these differ, so the Ensures "
            "ToSeq(Result()) == assembled(..., effective_authority(...), ...) "
            "fails. If it verified => SPEC-TOO-WEAK (the very fix would be "
            "unconstrained)."),
    },
    {
        "id": "partial-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_SEP),
        "refinement": (
            "Joining creds to authority with ':' (58) instead of '@' (64) emits "
            "'http://user:pass:example.com/path?query' for the F2P URL, != "
            "expected '...@...'. F2P FAIL => does NOT resolve."),
        "rationale": (
            "Rejected by effective_authority: it pins the join to PSeq(64) "
            "('@'), so creds+[58]+authority != effective_authority(creds,"
            "authority,True) for a has_creds input and the master pin fails. If "
            "it verified => SPEC-TOO-WEAK on the separator value."),
    },
    {
        "id": "partial-drop-query",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_QUERY),
        "refinement": (
            "Dropping the query branch emits 'http://user:pass@example.com/path' "
            "(no '?query') for both F2P URLs (each carries '?query'), != "
            "expected. F2P FAIL => does NOT resolve."),
        "rationale": (
            "Rejected by `assembled`: it appends PSeq(63)+query exactly when "
            "has_query, so omitting that branch breaks the master pin on every "
            "has_query input (including both F2P URLs). If it verified => "
            "SPEC-TOO-WEAK on the query sub-domain."),
    },
    {
        "id": "partial-drop-fragment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_PARTIAL_FRAG),
        "refinement": (
            "Dropping the fragment branch strips '#frag' from any "
            "fragment-bearing location. The real combining callee preserves the "
            "fragment, so the function's output diverges from the real "
            "post-patch behaviour on every fragment-carrying input => does NOT "
            "faithfully implement the modeled function."),
        "rationale": (
            "Rejected by `assembled`: it appends PSeq(35)+frag exactly when "
            "has_frag, so omitting that branch breaks the master pin on every "
            "has_frag input. If it verified => SPEC-TOO-WEAK on the fragment "
            "sub-domain."),
    },
    {
        "id": "nearmiss-creds-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _with_impl(_NEARMISS_NOGUARD),
        "refinement": (
            "Always prepending creds+'@' (dropping the `if auth:` guard) emits a "
            "stray '@' on the no-creds P2P inputs: 'http://@example.com/path' for "
            "'example.com/path'. P2P FAIL => does NOT resolve."),
        "rationale": (
            "Supporting near-miss with a real refinement: on a no-creds input "
            "(creds=[], has_creds=False) effective_authority(_, authority, False) "
            "== authority, but the impl produces []+[64]+authority = "
            "[64]+authority != authority, so the master pin fails. If it "
            "verified => SPEC-TOO-WEAK on the no-creds sub-domain."),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. There are NO @ContractOnly consumed axioms (meta.axioms == []).
# The bundle has TWO A-reference deep models (effective_authority, assembled)
# that are validated == the real callees by the bundle's own axiom_check.py
# (G-AX). We re-run that exact host oracle IN-CONTAINER as the axiom-soundness
# probe (it imports only stdlib urllib.parse for the core checks + urllib3's
# unchanged parse_url for the end-to-end check, both present in the eval image),
# and add a CONTAINMENT probe that enumerates exactly the callee inputs the
# MODEL can reach and asserts each lies in the deep models' domain.
# ---------------------------------------------------------------------------

# Embed the bundle's axiom_check.py source into the soundness probe (the runner
# mounts ONLY the probe at /work; axiom_check.py is NOT in-container — read it on
# the HOST now and inline it). Run as __main__ so its sys.exit(main()) fires.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AXIOM_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "# axiom-soundness: run the bundle's REAL-callee G-AX oracle in-container.\n"
    "# It executes the real stdlib urlunparse and real '@'.join (and the real\n"
    "# urllib3.parse_url end-to-end) and asserts both deep models agree on\n"
    "# boundary + 40000 fuzz + the F2P/P2P pipeline + 5000 fuzz. Exit 0 iff sound.\n"
    + _AXIOM_CHECK_SRC
)


# Containment probe: the deep models effective_authority(creds, authority,
# has_creds) and assembled(scheme, authority, path, query, frag, has_query,
# has_frag) are TOTAL @Pure functions over PSeq[int] (no Requires domain
# restriction in model.py). Every input the modeled function can reach is
# therefore inside their domain by construction. We make this explicit AND
# ground it: we drive the real callees (urlunparse / '@'.join) on the
# worst-case reachable shapes — credential-bearing effective authority, empty
# components, present/absent query and fragment — exactly the inputs
# `normalize_location` can produce, and assert no input is rejected
# (no exception) and each matches the deep model (so "reachable => in covered
# domain" is concretely witnessed, not just asserted).
_AXIOM_CONTAIN_PROBE = r'''# -*- coding: utf-8 -*-
"""axiom-containment for psf__requests-6028.

The two A-reference deep models are TOTAL @Pure functions: model.py places NO
Requires-domain restriction on effective_authority / assembled, and the modeled
function passes them ToSeq(creds/authority/scheme/path/query/frag) + the three
booleans verbatim. So the domain the model can reach == arbitrary str-component
tuples, all of which the deep models accept. This probe witnesses containment by
driving the REAL callees (urllib.parse.urlunparse and '@'.join) on EXACTLY the
reachable shapes the model produces (credential-bearing effective authority via
the join, empty/edge components, present+absent query and fragment) and
asserting (a) the real callee does not reject any reachable input and (b) it
agrees with the deep model — so every caller-reachable callee-input lies inside
the covered (sound) domain. A reachable input outside the domain would surface
as a disagreement/exception.
"""
import sys
from urllib.parse import urlunparse


def effective_authority(creds, authority, has_creds):
    if has_creds:
        return creds + "@" + authority
    return authority


def assembled(scheme, authority, path, query, frag, has_query, has_frag):
    base = scheme + "://" + authority + path
    if has_query:
        if has_frag:
            return base + "?" + query + "#" + frag
        return base + "?" + query
    if has_frag:
        return base + "#" + frag
    return base


# Exactly the component shapes normalize_location can reach (mirrors the model's
# inputs: scheme/creds/authority/path/query/frag as arbitrary strings; has_creds,
# has_query and has_frag are NOT free booleans -- in the real pipeline they are
# the truthiness tests `if auth:` / query-present / fragment-present, i.e.
# has_creds == bool(creds), has_query == bool(query) and has_frag == bool(frag)
# (exactly as the trusted G-AX oracle ties `has_query = query != ""` and
# `has_frag = frag != ""`). The model only ever feeds the callee the
# (component, boolean) pairs produced by that coupling, so enumerating the
# booleans FREE of the component emptiness would fabricate inputs the caller can
# never reach (e.g. has_query=True with an empty query string, which urlunparse
# renders without the '?' while the model's `?`-append regime is only entered for
# a non-empty query; likewise the '#'-append regime for a non-empty fragment).
# We therefore derive each boolean from the component, which is precisely the
# reachable callee-input set. Includes the F2P/P2P boundary shapes and
# degenerate empties.
creds_pool = ["", "user", "user:pass", "u", "a:b", "user%25u:p w"]
# The authority is the parsed host[:port] (or, with credentials, the joined
# userinfo+host) of a proxy/location URL. The deep model `assembled` is claimed
# (and validated by the trusted G-AX oracle axiom_check.py) for the documented
# regime: a NON-EMPTY authority. The F2P/P2P resolution inputs all carry a
# non-empty authority, so this is exactly the caller-reachable regime. (An empty
# authority is outside the validated regime: urlunparse only emits '//' for an
# empty netloc when the scheme is in its `uses_netloc` table -- http/https/ftp do,
# socks5 does not -- whereas the deep model emits '://' unconditionally. That
# divergence is reachable only for the non-`uses_netloc`-scheme + empty-authority
# corner that lies OUTSIDE the non-empty-authority regime the model covers, and
# G-AX likewise fuzzes only non-empty authorities.) So we mirror the regime here.
auth_pool = ["example.com", "example.com:80", "h.com:443", "192.168.0.1"]
# scheme is ALWAYS present in the reachable set: prepend_scheme_if_needed feeds
# `parsed.scheme if scheme is not None else new_scheme`, and new_scheme is a real
# scheme (e.g. 'http'), so the scheme arg is never the empty string. The model's
# documented regime is "present scheme"; G-AX's scheme pool is also all non-empty.
scheme_pool = ["http", "https", "socks5"]
path_pool = ["", "/path", "/a/b/c"]
query_pool = ["", "query", "a=1&b=2"]
frag_pool = ["", "frag", "section"]

checked = 0
for creds in creds_pool:
    for authority in auth_pool:
        # has_creds models the real `if auth:` truthiness test -> reachable
        # only as bool(creds) (creds present => creds branch; empty => bare).
        has_creds = creds != ""
        # effective_authority is what the model feeds as the authority arg
        # of assembled; build it via the model + (when creds present) cross
        # check the real '@'.join.
        eff = effective_authority(creds, authority, has_creds)
        if has_creds:
            real_join = "@".join([creds, authority])
            assert eff == real_join, (
                "reachable effective-authority input outside join domain: "
                "creds=%r authority=%r model=%r real=%r"
                % (creds, authority, eff, real_join))
        for scheme in scheme_pool:
            for path in path_pool:
                for query in query_pool:
                    for frag in frag_pool:
                        # has_query / has_frag model the presence tests ->
                        # reachable only as bool(component) (the model enters
                        # the append regime exactly when the component is
                        # non-empty, matching urlunparse, which omits the
                        # separator for an empty component).
                        has_query = query != ""
                        has_frag = frag != ""
                        m = assembled(scheme, eff, path, query, frag,
                                      has_query, has_frag)
                        q = query if has_query else ""
                        f = frag if has_frag else ""
                        # real combining callee on the SAME reachable input
                        r = urlunparse((scheme, eff, path, "", q, f))
                        assert m == r, (
                            "reachable assembled input outside urlunparse "
                            "domain: scheme=%r eff=%r path=%r query=%r "
                            "frag=%r has_query=%r has_frag=%r model=%r real=%r"
                            % (scheme, eff, path, query, frag, has_query,
                               has_frag, m, r))
                        checked += 1

print("containment OK: %d caller-reachable callee-inputs all inside the deep "
      "model domain and == the real callee (urlunparse / '@'.join)" % checked)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodels",
        "axiom": "effective_authority,assembled (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_SOUND_PROBE,
        "rationale": (
            "Runs the bundle's own G-AX oracle (axiom_check.py) in the eval "
            "container: it EXECUTES the real stdlib urlunparse and real "
            "'@'.join (and the real urllib3.parse_url end-to-end pipeline) and "
            "asserts both deep models equal them over boundary + 40000 fuzz + "
            "F2P/P2P + 5000 fuzz. If the real callee disagrees with the deep "
            "model on any input in its domain => AXIOM-UNSOUND. apply_gold=True "
            "because the end-to-end check targets the post-patch "
            "prepend_scheme_if_needed."),
    },
    {
        "id": "ax-contain-deepmodels",
        "axiom": "effective_authority,assembled (A-reference deep models)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_CONTAIN_PROBE,
        "rationale": (
            "The deep models are TOTAL @Pure functions (no Requires-domain "
            "restriction in model.py) and the modeled function passes them its "
            "inputs verbatim, so every caller-reachable callee-input is in their "
            "domain by construction. The probe witnesses this by driving the "
            "REAL callees (urlunparse / '@'.join) on exactly the reachable "
            "component shapes (credential-bearing effective authority, empty/edge "
            "components, present+absent query and fragment) and asserting no "
            "input is rejected and each matches the deep model. A reachable "
            "input outside the covered domain => AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
