# properties.py — PBT falsification battery for django__django-16661.
#
# NOT a Nagini module; a manifest the runner swebench_nagini.pbt parses. Every
# SPEC_TESTS module is the frozen model.py with edits made ONLY inside the
# # impl-start / # impl-end region (region surgery => same_spec is guaranteed).
#
# Defended surface of this instance:
#   retained_segments(prev_is_relation, field_is_parent_link, field_is_auto_identity,
#                     model_has_auto_identity, segment_targets_prior_hop,
#                     field_is_prior_hop_target) -> List[int]
#   takes SIX read-only List[bool] fact vectors (all Acc(list_pred(.), 1/2)) and
#   returns a 0/1 retention mask. The load-bearing postcondition clause is
#     ToSeq(Result()) == retained_mask(ToSeq(prev_is_relation), ...,
#                                       ToSeq(segment_targets_prior_hop), True)
#   which pins the WHOLE mask to the pure front-recursive fold `retained_mask`
#   over the per-segment predicate `keep_at`. The gold patch swaps the coarse
#   pre-patch test `field in prev_field.path_infos[-1].target_fields`
#   (modelled by the 6th vector field_is_prior_hop_target, which the post-patch
#   impl must NOT consult) for the three precise conjuncts of keep_at.
#
# Notes on the two falsification classes that need explicit justification:
#  * UNGROUNDED-ORACLE ECHO: the oracle `retained_mask` is GROUNDED — it is a
#    pure fold fully unfolded from the input vectors (no opaque answer-key, no
#    @ContractOnly), so `result = materialize(retained_mask(...))` would be the
#    CORRECT work, not a wrong echo. There is therefore no wrong-echo break;
#    instead pos-control / cheapest-honest-impl is the relevant positive control.
#  * FRAME-MUTATION: MANDATORY here — all six inputs are read-only at 1/2
#    permission. A rival that writes to one to satisfy the postcondition must be
#    rejected for insufficient permission (it cannot prove the write).
from pathlib import Path

INSTANCE = "django__django-16661"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The exact gold keep-decision + result-build block (inside the impl region).
# Every rival edits only a sub-slice of this block (or inserts ahead of it),
# so the frozen spec view is never touched.
# ---------------------------------------------------------------------------
_GOLD_RESULTBUILD = """        if keep:
            result = [1] + result
        else:
            result = [0] + result
        i = i - 1"""

_GOLD_KEEP = """        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = keep_at(pr, field_is_parent_link[i - 1],
                           field_is_auto_identity[i - 1],
                           model_has_auto_identity[i - 1],
                           segment_targets_prior_hop[i - 1])"""


# === 1. POSITIVE CONTROL (soundness) =======================================
# Structurally different but CORRECT: the result-build branches are swapped
# (guard negated, branch bodies exchanged). Logically identical to gold; every
# proof obligation (the loop invariant tying ToSeq(result) to the front-
# recursive fold, the per-element pins) is discharged exactly as in gold. Must
# verify; if it cannot, SPEC-TOO-STRONG.
_POS = _swap(_BASE, _GOLD_RESULTBUILD,
             """        if not keep:
            result = [0] + result
        else:
            result = [1] + result
        i = i - 1""")


# === 2. FRAME-MUTATION (uniqueness; MANDATORY) =============================
# Rival writes to a read-only input (field_is_parent_link, held at 1/2 perm)
# before computing keep. The gold invariants are kept VERBATIM, so the only
# new obligation is the write itself — which needs full (write) permission the
# Requires never grants. Must be REJECTED for insufficient permission.
# refinement: a faithful real patch that MUTATES the resolved field-metadata
# fact vectors (e.g. overwriting prev_field.path_infos / _meta.parents state)
# would corrupt the metadata other segments and other lookup_allowed calls read,
# and is NOT what the gold does (gold only READS field/_meta). Such an impl
# would not faithfully implement the retention condition and would not resolve
# test_lookup_allowed_foreign_primary, which exercises a fresh model graph.
_FRAME_MUT = _swap(_BASE, _GOLD_KEEP,
                   """        field_is_parent_link[i - 1] = False
        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = keep_at(pr, field_is_parent_link[i - 1],
                           field_is_auto_identity[i - 1],
                           model_has_auto_identity[i - 1],
                           segment_targets_prior_hop[i - 1])""")


# === 3. PRE-PATCH RIVAL (uniqueness; partial-domain) =======================
# The literal pre-patch retention test (model_prepatch.py): a non-first
# relational segment is retained iff its field is NOT the prior hop's target.
# Correct on most paths but WRONG on the foreign-key-as-primary-key family,
# where field_is_prior_hop_target is True yet the segment must be retained.
# refinement: this IS model_prepatch.py's impl; it produces the bug mask
# [1,0,1] on the F2P scenario (drops the `place` pk segment), so the gold F2P
# test test_lookup_allowed_foreign_primary FAILS (lookup wrongly disallowed).
# Must be REJECTED by the retained_mask postcondition.
_PREPATCH = _swap(_BASE, _GOLD_KEEP,
                  """        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = pr and not field_is_prior_hop_target[i - 1]""")


# === 4. ALWAYS-RETAIN (uniqueness; partial-domain) =========================
# keep is unconditionally True. Correct only on paths where every non-first
# segment is genuinely a new hop; wrong wherever keep_at would drop a segment
# (parent link / auto-identity / locally-reachable). Mask becomes all-ones.
# refinement: retaining a concrete-inheritance parent-link or auto-id segment
# the gold drops makes relation_parts longer than gold's; the unchanged
# membership test (len(relation_parts) <= 1 / isdisjoint(valid_lookups)) then
# diverges, so a lookup the gold ALLOWS (because the redundant segment was
# dropped) is wrongly disallowed — failing the existing P2P lookup_allowed
# tests. Must be REJECTED.
_ALWAYS = _swap(_BASE, _GOLD_KEEP,
                """        keep = True  # type: bool""")


# === 5. DROP-A-CONJUNCT (uniqueness; partial-domain) =======================
# keep_at with the `not field_is_auto_identity` conjunct removed. Agrees with
# gold except exactly when a segment IS the reached model's synthesised auto
# identity field (field_is_auto_identity=True) while the other guards would
# retain it: gold drops it, this rival keeps it.
# refinement: dropping `field is not model._meta.auto_field` from the real
# condition re-introduces retention of the auto-identity segment the gold
# explicitly excludes (the `employee__department__id` style locally-reachable
# id), lengthening relation_parts and flipping the membership verdict on the
# P2P lookups that rely on that exclusion. Must be REJECTED.
_DROP_CONJ = _swap(_BASE, _GOLD_KEEP,
                   """        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = (pr
                    and not field_is_parent_link[i - 1]
                    and ((not model_has_auto_identity[i - 1])
                         or (not segment_targets_prior_hop[i - 1])))""")


# === 6. NEVER-RETAIN-NONFIRST (uniqueness; partial-domain) =================
# Retains only the first segment; every non-first segment is dropped. Correct
# only on length-1 paths or paths where no later segment is a new hop.
# refinement: drops genuinely-new relational hops (incl. the F2P `place` and
# `country` segments), shortening relation_parts so the join no longer matches
# list_filter — the F2P and other multi-hop P2P lookups become wrongly
# disallowed. Must be REJECTED.
_NEVER = _swap(_BASE, _GOLD_KEEP,
               """        keep = (i - 1 == 0)  # type: bool""")


# === 7. ADMISSIBILITY (verify) =============================================
# Confirms the precondition admits a normal F2P-shaped input by asserting,
# from the (frozen) Requires/invariants, the equal-length facts an in-domain
# input satisfies — discharged purely from the contract, not added as new
# constraint. The impl is otherwise gold. If this cannot verify, the precond
# is unsatisfiable for legitimate inputs => PRECOND-TOO-STRONG.
_ADMISS = _swap(_BASE,
                """        result = [1] + result
        else:
            result = [0] + result
        i = i - 1""",
                """        result = [1] + result
        else:
            result = [0] + result
        # admissibility: the equal-length precondition facts hold for any
        # in-domain input (derivable from Requires/Invariant), so a normal
        # F2P-shaped path is accepted by the contract.
        Assert(len(field_is_parent_link) == len(prev_is_relation))
        Assert(len(segment_targets_prior_hop) == len(prev_is_relation))
        i = i - 1""")


SPEC_TESTS = [
    {"id": "pos-control-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS,
     "rationale": "structurally-different but logically identical correct impl "
                  "(result-build branches swapped, guard negated); every gold "
                  "proof obligation is discharged unchanged. Must verify, else "
                  "SPEC-TOO-STRONG."},

    {"id": "frame-mut-write-input", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_MUT,
     "refinement": "a faithful real patch that mutates the resolved field-fact "
                   "vectors (e.g. clears _meta.parents / path_infos state) "
                   "corrupts metadata other segments and other lookup_allowed "
                   "calls read; the gold only READS field/_meta, so such an "
                   "impl is not faithful and would not resolve "
                   "test_lookup_allowed_foreign_primary on a fresh model graph.",
     "rationale": "field_is_parent_link is read-only (Acc(...,1/2)); the write "
                  "needs full permission the Requires never grants. Rejection "
                  "comes from the permission system, not the postcondition. "
                  "A byte-fuzzer never constructs this."},

    {"id": "prepatch-target-fields", "kind": "uniqueness", "expect": "reject",
     "module": _PREPATCH,
     "refinement": "this is model_prepatch.py's retention test verbatim "
                   "(`pr and not field_is_prior_hop_target`); on the F2P "
                   "scenario it yields mask [1,0,1] (drops the `place` pk "
                   "segment), so lookup_allowed('restaurant__place__country') "
                   "returns False and test_lookup_allowed_foreign_primary FAILS "
                   "— the very bug the gold fixes. Does NOT resolve.",
     "rationale": "violates the load-bearing postcondition ToSeq(Result()) == "
                  "retained_mask(...,True): on the FK-as-PK family keep_at "
                  "retains (1) where the pre-patch test drops (0). G-DIFF "
                  "confirms this exact rival fails verification."},

    {"id": "always-retain", "kind": "uniqueness", "expect": "reject",
     "module": _ALWAYS,
     "refinement": "keep=True retains parent-link / auto-identity / locally-"
                   "reachable segments the gold drops, lengthening "
                   "relation_parts; the unchanged membership test then wrongly "
                   "disallows lookups the gold allows (the existing P2P "
                   "lookup_allowed tests that depend on those segments being "
                   "dropped). Does NOT resolve.",
     "rationale": "postcondition mismatch: retained_mask emits 0 wherever "
                  "keep_at is False, so an all-ones mask cannot equal the fold "
                  "on any path with a dropped segment."},

    {"id": "drop-auto-identity-conjunct", "kind": "uniqueness", "expect": "reject",
     "module": _DROP_CONJ,
     "refinement": "removing `field is not model._meta.auto_field` re-admits "
                   "retention of the synthesised auto-identity segment the gold "
                   "excludes (the employee__department__id locally-reachable "
                   "case), lengthening relation_parts and flipping the "
                   "membership verdict on the P2P lookups that rely on that "
                   "exclusion. Does NOT resolve.",
     "rationale": "the fold uses the full keep_at conjunction; dropping the "
                  "field_is_auto_identity term flips the mask exactly on the "
                  "auto-identity sub-domain, violating the postcondition."},

    {"id": "never-retain-nonfirst", "kind": "uniqueness", "expect": "reject",
     "module": _NEVER,
     "refinement": "retaining only segment 0 drops genuine new hops (incl. the "
                   "F2P `place`/`country`), shortening relation_parts so the "
                   "join no longer matches list_filter; F2P and multi-hop P2P "
                   "lookups become wrongly disallowed. Does NOT resolve.",
     "rationale": "postcondition mismatch: retained_mask emits 1 for every "
                  "segment keep_at retains; a first-only mask disagrees on any "
                  "retained non-first segment."},

    {"id": "admissibility-f2p-shape", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the equal-length precondition facts are derivable from the "
                  "frozen Requires/Invariant, so a normal F2P-shaped input is "
                  "admitted (the asserts discharge). If it cannot verify, "
                  "PRECOND-TOO-STRONG."},
]

# No @ContractOnly axioms and no consumed A-reference deep models in this
# bundle (meta.axioms == []; the retention rule is modelled deeply via keep_at /
# retained_mask, validated by the stdlib-only axiom_check.py, NOT consumed).
# There is therefore no real callee to execute against an axiom Ensures and no
# caller-domain containment obligation. Axiom lane is vacuous.
AXIOM_TESTS = []
