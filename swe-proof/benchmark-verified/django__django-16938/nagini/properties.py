# properties.py — PBT falsification battery for django__django-16938. NOT a
# Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant that shares the FROZEN spec exactly
# (markers.same_spec) and edits ONLY inside an # impl-start/# impl-end region;
# the runner re-runs the Nagini verifier on the host and checks the
# verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + meta.json):
#
#   class Fetch(restricted: bool, requested: PSet[int], members: PSet[int],
#               listed: PSet[int], excluding: bool)
#     carries only the touched query facets. The projection is carried the way
#     the query state itself carries it: an explicitly LISTED set of field codes
#     plus a flag saying whether that list is the codes to leave OUT
#     (`excluding`) rather than the codes to keep; an EMPTY list imposes no
#     restriction (every code loads). Its fields are MUTABLE heap locations
#     (Acc(self.*)) — unlike a PSet value, `q.restricted = ...` is a genuine,
#     expressible write, so the frame-mutation attack here is a real in-place
#     field write (NOT a 1/2->1 permission bump).
#
#   @Pure dropped(listed, excluding, pk, f) -> bool
#     == f != pk and len(listed) > 0 and (f in listed if excluding
#                                         else not (f in listed))
#   @Pure ill_formed(restricted, requested, listed, excluding, pk) -> bool
#     == restricted and len(listed) > 0 and Exists(int, lambda f:
#          f in requested and dropped(listed, excluding, pk, f))
#     The deep model (A-reference) of the descend check's raise branch, including
#     its restriction-non-empty conjunct. Both are FULLY GROUNDED in their
#     arguments (unfolded predicates, not an opaque answer-key / marker), so
#     there is NO "wrong echo" to build: echoing ill_formed(args) yields the
#     genuinely-correct value. => the ungrounded-oracle-echo class does NOT apply
#     (see `assessment`); we attack the value/well-formedness pins and supply
#     honest positive controls.
#
#   THREE modeled functions, ALL with a READ-ONLY input held at Acc(.,1/2)
#   over all five facets:
#     clear_specific_request(q)  Ensures Result().restricted == False,
#                                len(Result().requested) == 0,
#                                Result().members is q.members,
#                                Result().listed is q.listed,
#                                Result().excluding == q.excluding.
#     only_pk(q, pk)             Ensures Result().restricted == q.restricted,
#                                Result().requested is q.requested,
#                                Result().members is q.members,
#                                Result().excluding == False, and the
#                                CASE-SPLIT projection: len(Result().listed)==0
#                                when q.excluding and pk in q.listed, else
#                                Result().listed == PSet(pk).
#     build_pk_iterator(base,pk) THE modeled changed function. Read-only
#                                Acc(base.*,1/2).  LOAD-BEARING postconditions:
#                                  (W) not ill_formed(Result().restricted,
#                                        Result().requested, Result().listed,
#                                        Result().excluding, pk)
#                                  (U) Result().restricted == False
#                                  (D) len(Result().requested) == 0 — the reset
#                                      is WHOLESALE: the built fetch names no
#                                      adjacent-record code at all, so the codes
#                                      the accessor baked in are DISCARDED, not
#                                      carried / narrowed / reshuffled.
#                                  (P) Result().excluding == False, plus the
#                                      case-split pin on Result().listed
#                                      (empty when the accessor's own leave-out
#                                      list already carried pk, else PSet(pk))
#                                  (G) Result().members == base.members
#                                (W)+(U)+(D)+(P)+(G) pin ALL FIVE facets of
#                                Result, so its value is fully determined for
#                                EVERY base — the state the real chain builds.
#
#   WHY (D) IS LOAD-BEARING (it closes a free-facet hole). Before (D) was added,
#   `Result().requested` was the ONE facet no clause constrained: it appears only
#   as an argument position inside (W)'s `not ill_formed(...)`, and `ill_formed`
#   opens with `restricted and ...`, so (U)'s `Result().restricted == False`
#   short-circuits (W) to False REGARDLESS of `requested`. The single clause
#   mentioning the facet was therefore vacuous in it, leaving a rival free to
#   fabricate any named-request set (see `free-facet-fabricate-requested` below).
#   (D) is TRUE of the real operation because resetting to the unrestricted
#   default REPLACES the named-request mapping wholesale with a scalar, so the
#   named codes are destroyed rather than retained — the built fetch names no
#   adjacent-record code for any accessor default.
#
#   All three modeled functions additionally carry a TERMINATION obligation
#   (Requires(MustTerminate(...)), the constructor at a strictly lower level than
#   every method that builds a Fetch), so the spec states TOTAL — not partial —
#   correctness: an impl that never returns does not satisfy it. That obligation
#   is a defended clause like any value clause, and the `diverging-self-call`
#   reject case below is what pins it.
#
# The frame-mutation attack (MANDATORY: base/q are read-only Acc(.,1/2)) is a
# real in-place write to a half-owned field; it must be REJECTED for
# INSUFFICIENT PERMISSION. Partial-domain rivals split exactly along (W) (a
# restriction-preserving impl that omits the clearing step = the pre-patch bug,
# model_prepatch), (G) (a base-discarding impl = the documented atk_drop_base
# that G-EQ had to close), and (P) (an impl that pins the projection to PSet(pk)
# unconditionally, missing the leave-out-list case the real narrowing has).
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "django__django-16938"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl regions (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, so the spec view (and same_spec) is never
# touched. Each block's inner line makes the # impl-start/# impl-end pair unique.
# ---------------------------------------------------------------------------

_CLEAR_IMPL = """    # impl-start
    return Fetch(False, q.requested - q.requested, q.members, q.listed,
                 q.excluding)
    # impl-end"""

_ONLYPK_IMPL = """    # impl-start
    if q.excluding and pk in q.listed:
        return Fetch(q.restricted, q.requested, q.members,
                     PSet(pk) - PSet(pk), False)
    return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
    # impl-end"""

_BUILD_IMPL = """    # impl-start
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end"""

assert _BASE.count(_CLEAR_IMPL) == 1
assert _BASE.count(_ONLYPK_IMPL) == 1
assert _BASE.count(_BUILD_IMPL) == 1


SPEC_TESTS = []

# ===========================================================================
# 1. POSITIVE CONTROLS (soundness) — a structurally-DIFFERENT but CORRECT impl
#    MUST verify (else SPEC-TOO-STRONG). No loop / no @Pure fold here, so no
#    induction lemma is at risk (pilot pitfalls #2/#3 are N/A); we only reshape
#    the executable form while keeping the gold output value.
# ===========================================================================

# 1a. build_pk_iterator: construct the chain's output DIRECTLY in fresh Fetches,
#     bypassing the two helper calls. The case split is the same one only_pk
#     performs, so the value is identical; restricted==False makes ill_formed
#     vacuously False (short-circuit), so (W) holds with no quantifier
#     reasoning; (U), (P) and (G) are immediate. Must verify.
_BUILD_DIRECT = """    # impl-start
    if base.excluding and pk in base.listed:
        return Fetch(False, base.requested - base.requested, base.members,
                     PSet(pk) - PSet(pk), False)
    built = Fetch(False, base.requested - base.requested, base.members,
                  PSet(pk), False)  # type: Fetch
    return built
    # impl-end"""
SPEC_TESTS.append({
    "id": "pos-build-direct-construct",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_DIRECT),
    "rationale": "structurally-different CORRECT impl: instead of chaining the "
                 "two helper transitions, construct the chain's output value "
                 "directly, performing the same projection case split inline. "
                 "restricted==False discharges (W) not ill_formed(...) by "
                 "short-circuit (no quantifier/induction reasoning), (U), (P) "
                 "and (G) are immediate. If this faithful correct impl cannot "
                 "verify => SPEC-TOO-STRONG.",
})

# 1b. build_pk_iterator: REORDER the two transitions — narrow the projection
#     FIRST (only_pk), then clear the request (clear_specific_request). Both
#     orders yield the same state: only_pk preserves restricted/requested/members
#     and sets the projection (case-split) with excluding False, then
#     clear_specific_request sets restricted False, empties requested and threads
#     the projection through unchanged. A genuine structural reorder that keeps
#     the chain's output. Must verify.
_BUILD_REORDER = """    # impl-start
    narrowed = only_pk(base, pk)                # type: Fetch
    cleared = clear_specific_request(narrowed)  # type: Fetch
    return cleared
    # impl-end"""
SPEC_TESTS.append({
    "id": "pos-build-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_REORDER),
    "rationale": "structurally-different CORRECT impl: the two state transitions "
                 "are applied in the opposite order (only_pk then "
                 "clear_specific_request). only_pk(base) sets the projection and "
                 "keeps restricted/requested/members; clearing it then empties "
                 "the request and threads the projection through — the same "
                 "output state, since clearing does not touch the projection and "
                 "narrowing does not consult the request. No loop / no @Pure "
                 "fold, so no induction lemma is needed (pilot pitfalls #2/#3 "
                 "N/A). If it cannot verify => SPEC-TOO-STRONG.",
})

# 1c. only_pk: hoist the case-split guard into a local boolean and bind the
#     result Fetch before returning it (a local-variable reshape; identical
#     value in both branches). Must verify.
_ONLYPK_RESHAPE = """    # impl-start
    cancels = q.excluding and pk in q.listed  # type: bool
    if cancels:
        out = Fetch(q.restricted, q.requested, q.members,
                    PSet(pk) - PSet(pk), False)  # type: Fetch
        return out
    kept = Fetch(q.restricted, q.requested, q.members, PSet(pk),
                 False)  # type: Fetch
    return kept
    # impl-end"""
SPEC_TESTS.append({
    "id": "pos-onlypk-local-reshape",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _ONLYPK_IMPL, _ONLYPK_RESHAPE),
    "rationale": "local-variable reshape of only_pk: hoist the case-split guard "
                 "into a typed local and bind each branch's result Fetch before "
                 "returning it (the same pattern the model uses for its own "
                 "locals), identical value in both branches. A correct reshape "
                 "must verify (else SPEC-TOO-STRONG).",
})


# ===========================================================================
# 2. ADMISSIBILITY — confirm the precondition admits an F2P/reproducer-shaped
#    input (else PRECOND-TOO-STRONG). A new module-level caller would change the
#    spec view and break same_spec, so the witness is injected INSIDE the
#    build_pk_iterator impl region (elided from the spec view): build the issue's
#    worst-case base (restricted, requesting an adjacent code 7 that the
#    by-reference projection drops — exactly the reproducer shape), feed it
#    through the chain, and Assert the precondition is establishable AND the
#    built result is well-formed. A fresh Fetch grants full permission, of which
#    Acc(.,1/2) is freely given; the real impl then runs unchanged on the actual
#    params. If the Requires could not be met for this legitimate input the
#    helper call sites or the Assert would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_BUILD_ADMISS = """    # impl-start
    # --- admissibility witness for the reproducer-shaped input (elided from spec view) ---
    # Build the issue's worst-case base: restricted, requesting an adjacent code
    # 7, with NO projection restriction of its own (an empty list) -- exactly the
    # reproducer shape, where narrowing to the pk is what drops code 7.
    wit = Fetch(True, PSet(7), PSet(11), PSet(5) - PSet(5), True)   # type: Fetch
    # The precondition Acc(wit.*,1/2) is establishable (a fresh Fetch grants full
    # permission, of which 1/2 is freely given), so the chain ACCEPTS this
    # legitimate worst-case input and yields a WELL-FORMED, grounded fetch whose
    # projection is the by-reference one.
    w_cleared = clear_specific_request(wit)  # type: Fetch
    w_built = only_pk(w_cleared, 3)          # type: Fetch
    Assert(w_built.restricted == False)
    Assert(not ill_formed(w_built.restricted, w_built.requested, w_built.listed,
                          w_built.excluding, 3))
    Assert(w_built.members is wit.members)
    Assert(w_built.excluding == False)
    Assert(w_built.listed == PSet(3))
    # A second witness: the accessor's own projection is a leave-out list that
    # already carries the code the build narrows to, so narrowing cancels the
    # restriction outright and the projection then imposes no limit.
    wit2 = Fetch(True, PSet(7), PSet(11), PSet(3), True)   # type: Fetch
    w2 = only_pk(clear_specific_request(wit2), 3)          # type: Fetch
    Assert(len(w2.listed) == 0)
    Assert(not ill_formed(w2.restricted, w2.requested, w2.listed,
                          w2.excluding, 3))
    # --- end admissibility witness; the real impl follows unchanged ---
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end"""
SPEC_TESTS.append({
    "id": "admiss-reproducer-shaped-input",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_ADMISS),
    "rationale": "an admissibility witness injected INSIDE the impl region (so "
                 "same_spec holds) builds the issue's worst-case base "
                 "(restricted, requesting an adjacent code 7, no projection "
                 "restriction of its own — the reproducer shape), then feeds it "
                 "through the chain and Asserts the built result is well-formed, "
                 "by-reference and grounded; a SECOND witness exercises the other "
                 "branch, where the accessor's leave-out list already carried the "
                 "narrowed-to code so the restriction is cancelled. Both follow "
                 "from restricted==False by short-circuit, so no existential "
                 "witness is needed (pilot pitfalls avoided). A fresh Fetch grants "
                 "the Acc(.,1/2) the precondition needs, so the chain ACCEPTS "
                 "these legitimate inputs; the real impl then runs unchanged. If "
                 "the precondition could not be established for them the "
                 "calls/Asserts fail => PRECOND-TOO-STRONG.",
})


# ===========================================================================
# 3. FRAME-MUTATION (MANDATORY — base/q are read-only Acc(.,1/2)). A rival that
#    WRITES the half-owned input field to satisfy the postcondition vacuously
#    must be REJECTED for INSUFFICIENT PERMISSION. Fetch fields are mutable heap
#    locations, so this is a genuine in-place write (not a permission bump). The
#    postconditions are kept verbatim so the rejection is attributable solely to
#    the write. A byte-fuzzer never thinks to mutate the input — #1 weakness.
# ===========================================================================

# 3a. build_pk_iterator: instead of building a fresh Fetch via the helpers,
#     MUTATE the read-only base in place (base.restricted = False) and then
#     construct the result FROM base's now-cleared fields. The resulting VALUE
#     would satisfy (W)+(U)+(P)+(G); the only reason it fails is the write
#     `base.restricted = False`, which needs full permission on base.restricted
#     while the precondition grants only 1/2.
_BUILD_FRAME_MUT = """    # impl-start
    base.restricted = False
    if base.excluding and pk in base.listed:
        return Fetch(base.restricted, base.requested - base.requested,
                     base.members, PSet(pk) - PSet(pk), False)
    built = Fetch(base.restricted, base.requested - base.requested,
                  base.members, PSet(pk), False)  # type: Fetch
    return built
    # impl-end"""
SPEC_TESTS.append({
    "id": "frame-mut-base-restricted-write",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_FRAME_MUT),
    "refinement": "a faithful real patch that mutates the related-collection "
                  "queryset's eager-co-selection request in place (rather than "
                  "chaining a fresh clone) has no resolving analogue: the base "
                  "queryset is obtained from the custom accessor's default and is "
                  "SHARED state — the real query operations always clone "
                  "precisely so the accessor's baked default is not corrupted. "
                  "Mutating it would clobber that default for every subsequent "
                  "access (other collection fields, other objects in the "
                  "serialize loop), regressing the P2P serialization tests rather "
                  "than resolving them. It only 'works' here by vacuously "
                  "satisfying the postcondition through an illegal write to a "
                  "read-only input.",
    "rationale": "REJECT comes from the PERMISSION system: `base.restricted = "
                 "False` requires full Acc(base.restricted) but the precondition "
                 "grants only Acc(base.restricted, 1/2), so Nagini reports "
                 "'Insufficient permission to access base.restricted'. The "
                 "postconditions are verbatim; the rejection is attributable to "
                 "the write to the half-owned input, not a wrong value.",
})

# 3b. clear_specific_request: the same illegal-write attack on the smaller
#     helper — set q.restricted = False in place, then return a Fetch built from
#     q's fields. The value matches the Ensures; the write q.restricted=False
#     needs full permission, only 1/2 held.
_CLEAR_FRAME_MUT = """    # impl-start
    q.restricted = False
    out = Fetch(q.restricted, q.requested - q.requested, q.members, q.listed,
                q.excluding)  # type: Fetch
    return out
    # impl-end"""
SPEC_TESTS.append({
    "id": "frame-mut-clear-q-restricted-write",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CLEAR_IMPL, _CLEAR_FRAME_MUT),
    "refinement": "modeling the request-clearing operation as an IN-PLACE write "
                  "to the input query (q.restricted=False) rather than producing "
                  "a new clone has no resolving real analogue: the real operation "
                  "returns a clone and never mutates the receiver; a patch that "
                  "mutated the accessor's shared queryset in place would corrupt "
                  "its baked default for all later uses and fail the P2P "
                  "serialization tests.",
    "rationale": "REJECT from the PERMISSION system: q.restricted = False needs "
                 "full Acc(q.restricted) but only Acc(q.restricted, 1/2) is "
                 "granted by the precondition => 'Insufficient permission'. "
                 "Ensures kept verbatim; rejection attributable to the write.",
})


# ===========================================================================
# 4. PARTIAL-DOMAIN — a rival correct on most of the F2P/P2P input domain but
#    diverging on a sub-domain. expect="reject". The build's input domain (the
#    arbitrary baked-in request and projection `base` carries) splits exactly
#    along the discriminating clauses (W), (G) and (P).
# ===========================================================================

# 4a. THE PRE-PATCH BUG (model_prepatch): omit the clearing step — preserve the
#     baked-in restriction and only narrow the projection. Correct on every base
#     whose accessor baked in NO specific request (restricted==False: ill_formed
#     vacuously False), but WRONG on the reproducer sub-domain (restricted and a
#     requested code the by-reference projection drops): ill_formed is True.
#     Rejected by (W) (and by (U)).
_BUILD_PREPATCH = """    # impl-start
    narrowed = only_pk(base, pk)            # type: Fetch
    return narrowed
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-prepatch-keep-restriction",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_PREPATCH),
    "refinement": "this IS the pre-patch behaviour (model_prepatch.py): the chain "
                  "narrows the projection but never clears the baked-in "
                  "eager-co-selection request. For a related collection whose "
                  "custom accessor bakes in a request naming an adjacent record "
                  "that the by-reference projection drops, evaluating the fetch "
                  "raises the error the issue reports. The F2P "
                  "test_serialize_prefetch_related_m2m / test_serialize_only_pk "
                  "(a collection whose accessor bakes in such a request) fail. "
                  "Does NOT resolve — it is literally the reported behaviour the "
                  "gold changes.",
    "rationale": "REJECT from the load-bearing well-formedness clause (W) "
                 "Ensures(not ill_formed(Result().restricted, Result().requested, "
                 "Result().listed, Result().excluding, pk)): on a base with "
                 "restricted==True and a requested code the narrowed projection "
                 "drops, the result keeps restricted and that dropped code, so "
                 "ill_formed(...) is True and (W) fails (clause (U) "
                 "Result().restricted == False fails too).",
})

# 4b. THE BASE-DISCARDING IMPL (the documented atk_drop_base G-EQ had to close):
#     return a well-formed by-reference fetch that fabricates the addressed
#     member set instead of threading base.members. Well-formed (restricted
#     False) and by-reference, so (W)+(U)+(P) hold; correct only when
#     base.members happens to equal the fabricated set. Rejected by (G).
_BUILD_DROP_BASE = """    # impl-start
    if base.excluding and pk in base.listed:
        return Fetch(False, base.requested - base.requested, PSet(pk),
                     PSet(pk) - PSet(pk), False)
    built = Fetch(False, base.requested - base.requested, PSet(pk), PSet(pk),
                  False)  # type: Fetch
    return built
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-drop-base-fabricate-members",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_DROP_BASE),
    "refinement": "this discards the base collection and fabricates the addressed "
                  "member set. The refined real patch would build the reference "
                  "iterator from a DIFFERENT/empty related queryset (not the "
                  "owning record's accessor), so the serialized related row list "
                  "would not be the object's actual members. The behavioural F2P "
                  "(test_serialize_prefetch_related_m2m asserts the exact related "
                  "pk row list, and the basic serialization tests assert the "
                  "collection contents) would fail. Does NOT resolve. This is the "
                  "verified-but-unresolved witness G-EQ closed by adding the "
                  "grounding clause (G).",
    "rationale": "REJECT from the grounding clause (G) "
                 "Ensures(Result().members == base.members): the rival returns "
                 "members=={pk}, which differs from base.members whenever the "
                 "accessor yielded any other member set (including the empty "
                 "one), violating (G). (W), (U) and (P) alone would admit it — "
                 "(G) is what rejects it.",
})

# 4c. SUPPORTING near-miss: clear the request but DROP the projection narrowing
#     (carry base's own projection through instead of narrowing to the pk).
#     Well-formed (restricted False) and grounded (members preserved), so
#     (W)+(U)+(G) hold; correct only when base's projection happened to be
#     exactly the by-reference one. Rejected by the projection clause (P).
_BUILD_NO_NARROW = """    # impl-start
    built = Fetch(False, base.requested - base.requested, base.members,
                  base.listed, base.excluding)  # type: Fetch
    return built
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-no-projection-narrow",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_NO_NARROW),
    "refinement": "this clears the eager-co-selection request but omits the "
                  "narrowing to the primary key (carries the accessor's own "
                  "projection through). The serialized reference would then load "
                  "every column of each related row instead of just the key — the "
                  "by-reference / no-superfluous-columns guarantee is lost. "
                  "test_serialize_only_pk / test_serialize_no_only_pk_with_"
                  "natural_keys assert the cascade SELECT carries ONLY the key "
                  "(e.g. no extra column on the related query); over-loading "
                  "columns fails those assertNotIn checks. Does NOT resolve.",
    "rationale": "REJECT from the projection clause (P): carrying base.listed / "
                 "base.excluding through means the result's projection is the "
                 "accessor's, which differs from the pinned by-reference one "
                 "(Result().excluding == False plus the case-split pin on "
                 "Result().listed) whenever the accessor's projection was not "
                 "already exactly that.",
})

# 4d. THE UNCONDITIONAL-PIN near-miss (the case the repaired projection clause
#     splits on): narrow to PSet(pk) ALWAYS, ignoring that a narrowing whose
#     target the accessor's own leave-out list already carried cancels the
#     restriction instead of imposing it. Correct on every base whose projection
#     is a keep list or whose leave-out list omits pk — the overwhelming majority
#     — and WRONG exactly on the leave-out-list-carrying-pk sub-domain, where the
#     real narrowing leaves NO restriction at all. Rejected by (P)'s first case.
_BUILD_UNCOND_PIN = """    # impl-start
    built = Fetch(False, base.requested - base.requested, base.members,
                  PSet(pk), False)  # type: Fetch
    return built
    # impl-end"""
SPEC_TESTS.append({
    "id": "partial-unconditional-projection-pin",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_UNCOND_PIN),
    "refinement": "this asserts the built projection is ALWAYS the single-key "
                  "keep list. The real narrowing keeps the named code minus what "
                  "the incoming leave-out list already excluded, so when the "
                  "accessor's own projection is a leave-out list that carries the "
                  "key itself, the narrowing yields an EMPTY list — which imposes "
                  "no restriction, i.e. every column loads. A patch refined from "
                  "this rival would be predicting a single-column reference fetch "
                  "where the real one selects the whole row, so its "
                  "no-superfluous-columns reasoning is wrong on exactly that "
                  "family of accessors. Does NOT resolve.",
    "rationale": "REJECT from the projection clause (P)'s first case "
                 "Ensures(Implies(base.excluding and pk in base.listed, "
                 "len(Result().listed) == 0)): the rival returns listed==PSet(pk) "
                 "there, whose length is 1, violating that Implies. Its second "
                 "case, (W), (U) and (G) all still hold — the case split is what "
                 "rejects it.",
})

# 4e. THE FREE-FACET FABRICATION (what clause (D) closes). Everything (W), (U),
#     (P) and (G) ask for is delivered exactly, and the ONLY deviation is the
#     named-request facet: instead of the accessor's baked-in codes being
#     DISCARDED, a code is invented for the built fetch. Before (D) this VERIFIED
#     — (W) short-circuits on restricted==False and so says nothing about the
#     facet, and no other clause mentioned it. It is the ungrounded-oracle-echo
#     shape at the state level: the right answer on every observed facet, an
#     arbitrary answer on the unobserved one.
_BUILD_FABRICATE_REQ = """    # impl-start
    if base.excluding and pk in base.listed:
        return Fetch(False, PSet(pk), base.members, PSet(pk) - PSet(pk), False)
    return Fetch(False, PSet(pk), base.members, PSet(pk), False)
    # impl-end"""
SPEC_TESTS.append({
    "id": "free-facet-fabricate-requested",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_FABRICATE_REQ),
    "refinement": "this leaves the built fetch carrying a *specific* named "
                  "eager-co-selection request while claiming the unrestricted "
                  "default. A patch refined from it would reset the request only "
                  "half-way — dropping the restricted flag but leaving named "
                  "adjacent-record codes standing — a state the real operation "
                  "cannot produce, because falling back on the unrestricted "
                  "default replaces the whole named-request mapping with a scalar "
                  "and so destroys the names. Any real chain that did keep a name "
                  "standing would put that name back in conflict with the "
                  "key-only projection, i.e. re-raise the very error the reported "
                  "issue is about on the reproducer accessor. Does NOT resolve.",
    "rationale": "REJECT from the new clause (D) Ensures(len(Result().requested) "
                 "== 0): the rival returns requested==PSet(pk), whose length is 1. "
                 "(W), (U), (P) and (G) ALL still hold of it — (W) vacuously, "
                 "since restricted==False short-circuits ill_formed — so (D) is "
                 "the only clause that rejects it, which is precisely why it is "
                 "needed. This is the counterexample family the free `requested` "
                 "facet admitted.",
})

# 4f. THE HALF-DOMAIN FABRICATION: the same free-facet deviation, but confined to
#     the leave-out-list branch, so it is correct on the overwhelming majority of
#     accessors and wrong only where the accessor's own projection is a leave-out
#     list carrying the key. A rival that survives 4e by narrowing its footprint
#     must still be rejected, else (D) would only be pinning one path.
_BUILD_FABRICATE_REQ_BRANCH = """    # impl-start
    if base.excluding and pk in base.listed:
        return Fetch(False, PSet(pk), base.members, PSet(pk) - PSet(pk), False)
    return Fetch(False, base.requested - base.requested, base.members,
                 PSet(pk), False)
    # impl-end"""
SPEC_TESTS.append({
    "id": "free-facet-fabricate-requested-one-branch",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_FABRICATE_REQ_BRANCH),
    "refinement": "the partial-domain version of 4e: the built fetch keeps a "
                  "named adjacent-record request ONLY when the accessor's own "
                  "projection is a leave-out list already carrying the key. That "
                  "sub-domain is exactly the family where the narrowing cancels "
                  "the projection restriction outright, so a patch refined from "
                  "this rival is wrong precisely where the interaction between the "
                  "accessor's projection and the key-only narrowing is subtlest, "
                  "while looking right everywhere else. Does NOT resolve.",
    "rationale": "REJECT from (D) again, on the branch it deviates in: "
                 "requested==PSet(pk) there has length 1, so "
                 "len(Result().requested) == 0 fails. Every other clause holds in "
                 "both branches. Included so (D) is shown to pin the facet across "
                 "the whole domain, not just the unconditional shape of 4e.",
})


# ===========================================================================
# 5. TERMINATION — the spec's obligation (Requires(MustTerminate(...))) makes it
#    a TOTAL-correctness statement, so an impl that never returns must be
#    REJECTED even though every value clause would hold of whatever it did
#    return. This case pins that obligation as a defended clause.
# ===========================================================================

# 5a. DIVERGENCE: build the reference fetch by returning the result of an
#     unconditional SELF-call. Every value clause — (W), (U), (P), (G) — would
#     follow from build_pk_iterator's own postcondition applied to the very same
#     (base, pk), and the permission accounting balances (the callee hands
#     Acc(base.*,1/2) back), so under PARTIAL correctness this rival would verify
#     while looping forever. It must be rejected, and for the termination reason
#     alone.
#
#     NOTE on the shape. A method's obligation level is a per-method CONSTANT and
#     a call must sit at a level strictly BELOW its caller's, so a self-call can
#     never discharge it — which is exactly the statement "this recursion has no
#     decreasing measure". That is also why the admissibility case above builds
#     its witness and asserts the precondition conjuncts on it DIRECTLY instead
#     of handing the witness to the method under specification: admissibility
#     must test that a caller can ESTABLISH the precondition for a normal input,
#     not the separate — and false — claim that the method may call itself
#     unboundedly. Verified non-vacuous: splicing `Assert(False)` after that
#     case's Asserts FAILS, so its probe path is reachable.
_BUILD_DIVERGE = """    # impl-start
    return build_pk_iterator(base, pk)
    # impl-end"""
SPEC_TESTS.append({
    "id": "diverging-self-call",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _BUILD_IMPL, _BUILD_DIVERGE),
    "refinement": "a serializer that builds the reference fetch by asking itself "
                  "to build the very same fetch never reaches the query at all: "
                  "there is no smaller sub-problem to descend to, so serializing "
                  "any object with a related collection recurses until the "
                  "interpreter's recursion limit instead of emitting the related "
                  "keys. Every serialization test errors out. Does NOT resolve — "
                  "there is no resolving real analogue of divergence.",
    "rationale": "REJECT from the TERMINATION obligation: the level in the "
                 "precondition's MustTerminate is a per-method constant, so a "
                 "self-call cannot sit strictly below its caller and Nagini "
                 "reports 'Obligation leak check failed. Callee "
                 "build_pk_iterator might not take all unsatisfied obligations "
                 "from the caller.' No value clause is reported: (W)/(U)/(P)/(G) "
                 "all follow from the callee's own postcondition, so the "
                 "rejection is attributable solely to divergence. This is the "
                 "case that pins TOTAL correctness.",
})


# ===========================================================================
# 6. CONTROL-FLOW-EFFECT — N/A. All three modeled functions are pure value
#    transitions over the touched facets: each returns a freshly-built Fetch and
#    has no raise / no observable side-effect on a shared object that the value
#    abstraction would miss (the error the issue concerns is modeled DEEPLY as
#    the value predicate ill_formed, which (W) already pins, not as a runtime
#    raise). The only observable is the returned Fetch, fully pinned by
#    (W)+(U)+(P)+(G). So no capability-token rival is needed. (See assessment.)
# ===========================================================================


# ===========================================================================
# AXIOMS — none. meta.json "axioms": [] and the axioms region is an empty
# comment: the bundle consumes NO @ContractOnly axiom (the proof depends on no
# opaque contract). The three deep models (clear_specific_request, only_pk,
# ill_formed/dropped) are A-reference: each is validated == its real unchanged
# callee by the existing tasks/django__django-16938/axiom_check.py (G-AX), which
# runs the REAL ORM in the pinned eval container and confirms the pre-patch chain
# errors (ill_formed True) while the post-patch chain is well-formed, that the
# reset leaves no specific request standing, and that the narrowing's two cases
# (the by-reference keep list, and the cancellation when the accessor's leave-out
# list already carried the key) are the real ones. That is the correct lane for
# A-references and it already passes; there is no @ContractOnly axiom-soundness /
# axiom-containment obligation for the PBT axiom lane to re-probe. So:
# ===========================================================================
AXIOM_TESTS = []
