# properties.py — PBT falsification battery for sphinx-doc__sphinx-8595.
#
# NOT a Nagini module: a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT onto.
#
# Modeled function (model.py):
#   select_module_members(member_names: List[int], excluded: List[bool],
#                         all_present: bool, all_names: List[int]) -> bool
#
# Defended surface (the four load-bearing postcondition clauses):
#   (P1) Implies(not all_present, Result() == True)
#   (P2) Implies(not all_present, Forall k: excluded[k] == False)
#   (P3) Implies(all_present, Result() == False)
#   (P4) Implies(all_present,
#                ToSeq(excluded) == exclusion_flags(ToSeq(member_names),
#                                                   ToSeq(all_names)))
#   plus the frame: Ensures Acc(all_names,1/2), Acc(member_names,1/2),
#   Acc(excluded) and len(excluded)==len(member_names).
#
# Read-only inputs (Acc(...,1/2)):  all_names AND member_names  -> frame-mutation
# is MANDATORY.  excluded is the only full-permission (writable) carrier.
#
# The oracle exclusion_flags is a @Pure function FULLY GROUNDED in the inputs
# (member_names, all_names) — there is no opaque answer-key to echo, so the
# ungrounded-oracle-echo class is N/A (see assessment); P4 pins the output to a
# computed-from-inputs value, which the rivals below must actually reproduce.
#
# Region surgery: every spec variant is built by _swap on _BASE, editing ONLY
# text physically inside the `# impl-start` / `# impl-end` region. The frozen
# spec (axioms/pure/pre/post-conditions/signatures) is never touched, which
# GUARANTEES markers.same_spec(_BASE, variant) == True.

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8595"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found in base")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ----------------------------------------------------------------------------
# Anchors inside the impl region (all unique substrings of the impl body).
# ----------------------------------------------------------------------------

# The implicit-membership branch (absent export list).
_IMPLICIT_BRANCH = """    if not all_present:
        # for implicit module members, every discovered member is a candidate:
        # none is excluded (the flags are already clear), and implicit
        # membership is signalled.
        return True"""

# The per-member exclusion assignment (the substance of clause P4).
_SET_EXCLUDED = """            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False"""

# The top of the else-branch, right before the backward loop.
_ELSE_TOP = """    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:"""

# The terminal return of the present branch.
_PRESENT_RETURN = """            i = i - 1
        return False"""


# ===========================================================================
# SPEC LANE
# ===========================================================================

SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness) ---------------------------------------
    # Structurally DIFFERENT but CORRECT: the two branches of the per-member
    # assignment are reordered (test `contains` directly instead of its
    # negation) and the written value is produced via a single local boolean
    # `excl`. The backward loop, the front-recursion-friendly drop(i)
    # invariant, and all gold framing asserts are kept verbatim, so the gold
    # proof still discharges (no induction lemma is needed — this is a local
    # branch/value reshape, NOT a loop-direction flip; cf. directive 3).
    # MUST verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _SET_EXCLUDED,
            """            excl = contains(seq, c)
            if excl:
                excluded[i - 1] = False
            else:
                excluded[i - 1] = True""",
        ),
        "rationale": "a correct impl that only reshapes the per-member "
                     "assignment (reordered branches + local bool, same "
                     "value `not contains(seq,c)`, same backward loop and "
                     "framing asserts) must verify; else SPEC-TOO-STRONG.",
    },

    # -- ADMISSIBILITY ------------------------------------------------------
    # In-region witness that the precondition admits a normal F2P-shaped
    # input: at the top of the impl assert the cleared-flags Forall from the
    # Requires is actually derivable (every entry False on entry). This is the
    # precondition the F2P input (members foo/bar/baz, all flags default
    # False) satisfies. If this assert cannot be established the precondition
    # is internally unusable -> PRECOND-TOO-STRONG. The rest of the gold impl
    # is untouched so the postcondition still discharges.
    {
        "id": "admiss-cleared-flags",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _IMPLICIT_BRANCH,
            """    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                          ToSeq(excluded)[k] == False),
                                  [[ToSeq(excluded)[k]]])))
    if not all_present:
        # for implicit module members, every discovered member is a candidate:
        # none is excluded (the flags are already clear), and implicit
        # membership is signalled.
        return True""",
        ),
        "rationale": "the precondition must admit a freshly-discovered member "
                     "set (all exclusion flags clear) — the exact F2P shape; "
                     "if the cleared-flags Forall is not derivable at entry "
                     "the precondition is unusable -> PRECOND-TOO-STRONG.",
    },

    # -- FRAME-MUTATION (MANDATORY: member_names is Acc(...,1/2) read-only) --
    # The rival OVERWRITES the read-only `member_names` input. It keeps the
    # gold exclusion logic verbatim (so the rejection is attributable to the
    # write, not to a value error). With only Acc(member_names,1/2) the write
    # `member_names[i-1] = 0` MUST be rejected for INSUFFICIENT PERMISSION.
    # If it verified, the half-permission frame would be a lie and a real
    # patch could clobber the discovered member names.
    {
        "id": "frame-mutation-member-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SET_EXCLUDED,
            """            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False
            member_names[i - 1] = 0""",
        ),
        "refinement": "the faithful real patch (writing to the discovered "
                      "member-name carrier `member.__name__`) would corrupt "
                      "ObjectMember identities and the documented member set, "
                      "so list(actual) in test_empty_all would NOT match -> "
                      "does NOT resolve the F2P.",
        "rationale": "member_names is Acc(list_pred(member_names), 1/2) "
                     "(read-only); the in-place write demands full permission "
                     "the caller never granted -> rejected for insufficient "
                     "permission by the permission system.",
    },

    # -- FRAME-MUTATION (also exercise the second read-only input all_names) -
    # Same attack on the OTHER half-permission input. Gold logic kept verbatim;
    # the write `all_names[0] = 0` must be rejected for insufficient permission.
    # Guarded behind len>0 so it is a genuine write attempt, not dead code.
    {
        "id": "frame-mutation-all-names",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ELSE_TOP,
            """    else:
        seq = ToSeq(all_names)
        if len(all_names) > 0:
            all_names[0] = 0
        i = len(excluded)
        while i > 0:""",
        ),
        "refinement": "the faithful real patch would mutate self.__all__ "
                      "(the module export list), changing which members are "
                      "documented on later use and breaking the read-only "
                      "contract on __all__ -> does NOT resolve the F2P.",
        "rationale": "all_names is Acc(list_pred(all_names), 1/2) "
                     "(read-only); any in-place write needs full permission "
                     "-> rejected for insufficient permission.",
    },

    # -- UNIQUENESS: value-level inversion (double-mask of clause P4) -------
    # The rival INVERTS the exclusion test: it excludes members that ARE
    # exported and keeps members that are NOT. ToSeq(excluded) then equals the
    # complement of exclusion_flags(...), violating clause P4. Must reject.
    {
        "id": "weak-invert-exclusion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _SET_EXCLUDED,
            """            if not contains(seq, c):
                excluded[i - 1] = False
            else:
                excluded[i - 1] = True""",
        ),
        "refinement": "the faithful real patch (`if member.__name__ IN "
                      "self.__all__: member.skipped = True`) would skip "
                      "exactly the exported members and document the "
                      "non-exported ones — the inverse of the issue's "
                      "requirement; for empty __all__ it documents every "
                      "member, so test_empty_all still shows foo/bar/baz "
                      "-> does NOT resolve.",
        "rationale": "violates P4: ToSeq(excluded) == exclusion_flags(...) "
                     "requires excluded[k] == (name_k not in all_names); the "
                     "inverted write makes it the negation.",
    },

    # -- PARTIAL-DOMAIN: correct on most inputs, wrong on the empty-all_names
    # sub-domain (the EXACT F2P discriminator). The rival short-circuits the
    # present branch when all_names is empty and returns True with nothing
    # excluded — i.e. it reproduces the original bug for present-but-empty
    # __all__ while remaining gold-correct for every non-empty present list
    # and every absent list. Must reject (P3 demands Result()==False, P4
    # demands all-excluded, whenever all_present).
    {
        "id": "partial-domain-empty-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _ELSE_TOP,
            """    elif len(all_names) == 0:
        # WRONG on the present-but-empty sub-domain: treat it like absent.
        return True
    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:""",
        ),
        "refinement": "this is the pre-patch behaviour (`if not self.__all__`) "
                      "restricted to the empty-list case: an empty __all__ "
                      "documents every member, so test_empty_all sees "
                      "foo/bar/baz instead of nothing -> does NOT resolve the "
                      "F2P (the very bug the issue reports).",
        "rationale": "violates P3 (Result()==False required when all_present) "
                     "and P2-style nothing-excluded clashes with P4 (which "
                     "for empty all_names requires every entry True) on the "
                     "present-but-empty sub-domain.",
    },

    # -- PARTIAL-DOMAIN: off-by-one, leaves the LAST-processed (first) member
    # unmasked. The rival skips writing index 0 (stops the loop one early),
    # so for member 0 the exclusion flag keeps its cleared (False) entry value
    # even when member 0 is not exported. Correct for every member except the
    # first -> violates P4 whenever member_names[0] not in all_names.
    {
        "id": "partial-domain-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PRESENT_RETURN,
            """            i = i - 1
            if i == 1:
                break
        return False""",
        ),
        "refinement": "the faithful real patch would never mark the first "
                      "discovered member as skipped, so a non-exported first "
                      "member stays documented; with empty __all__ the first "
                      "of foo/bar/baz would still appear in test_empty_all "
                      "-> does NOT resolve the F2P.",
        "rationale": "violates P4: leaving excluded[0] at its cleared False "
                     "while exclusion_flags requires True (member 0 not in "
                     "all_names) breaks ToSeq(excluded)==exclusion_flags(...).",
    },

    # -- CONTROL-FLOW-EFFECT: wrong Result() boolean on the present branch.
    # The value carrier `excluded` is computed correctly (gold logic kept),
    # but the present branch RETURNS True instead of False — the implicit-vs-
    # explicit membership flag (the first tuple element of the real return) is
    # inverted. This is a return/flag difference; P3 (Implies(all_present,
    # Result()==False)) catches it. Must reject.
    {
        "id": "control-flow-wrong-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PRESENT_RETURN,
            """            i = i - 1
        return True""",
        ),
        "refinement": "the real return value (`return True, ...` vs "
                      "`return False, ...`) is the implicit-membership flag; "
                      "returning True for a present __all__ tells autodoc to "
                      "fall back to __module__-based implicit membership, "
                      "documenting imported objects the explicit list "
                      "intends to govern -> wrong behaviour, does NOT resolve.",
        "rationale": "violates P3: Implies(all_present, Result()==False); the "
                     "present branch must return False.",
    },

    # -- UNIQUENESS (supporting near-miss): drop P2's nothing-excluded in the
    # absent branch by writing an exclusion into the read-only-default flags.
    # Returns the right Result() (True) but sets excluded[0]=True on the absent
    # path. expect reject — but the write is on `excluded` (full permission) so
    # the rejection is a VALUE defect (P2: absent => all flags False), not a
    # permission defect. This is a cheap supporting case, not a reasoned
    # frame attack.
    {
        "id": "weak-absent-excludes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _IMPLICIT_BRANCH,
            """    if not all_present:
        # WRONG: an absent export list must leave every member documented.
        if len(excluded) > 0:
            excluded[0] = True
        return True""",
        ),
        "refinement": "marking a member skipped when __all__ is absent "
                      "(implicit membership) would hide a legitimately "
                      "discovered member; the gold absent branch documents "
                      "all of them -> behaviour diverges, does NOT resolve.",
        "rationale": "violates P2: Implies(not all_present, Forall k: "
                     "excluded[k]==False); the absent branch must leave the "
                     "flags clear.",
    },
]


# ===========================================================================
# AXIOM LANE
# ===========================================================================
# meta.axioms == []  (no consumed @ContractOnly axioms). The two deep models
# `contains` and `exclusion_flags` are A-reference and already validated by
# axiom_check.py / G-AX (contains == Python `in`; exclusion_flags == a faithful
# transcription of the repo else-loop; is-None-vs-truthiness on None/[]). Per
# PBT_PLAN §2.4 the axiom lane is for @ContractOnly axioms / A-reference deep
# models; there is no consumed axiom whose Ensures a real callee could violate,
# and the A-reference soundness obligation is already discharged by G-AX. We
# therefore leave AXIOM_TESTS empty (the deep-model soundness is not re-litigated
# here; see assessment).
AXIOM_TESTS = []
