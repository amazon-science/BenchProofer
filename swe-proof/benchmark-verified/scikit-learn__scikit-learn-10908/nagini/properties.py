# properties.py — PBT falsification battery for scikit-learn__scikit-learn-10908.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# get_feature_names # impl-start / # impl-end region) and are checked by Nagini
# verify + markers.same_spec. Axiom cases are real-callee probes run in Docker.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + the gold
# patch + the F2P test):
#
#   get_feature_names(self: Vectoriser) -> List[int]
#     models CountVectorizer.get_feature_names after the gold one-liner
#       if not hasattr(self,'vocabulary_'): self._validate_vocabulary()
#     Fields:  fitted   <- hasattr(self,'vocabulary_')   (materialised mapping?)
#              has_param<- self.vocabulary is not None    (ctor list supplied?)
#              param    <- the ctor vocabulary list       (READ-ONLY input)
#              supplied <- self.fixed_vocabulary_          (records ctor-supplied)
#              names    <- vocabulary_ in index order      (the returned names)
#
#   READ-ONLY INPUT (project directive 5): inside get_feature_names the supplied
#   list `self.param` is held at HALF permission
#       Requires(Acc(list_pred(self.param), 1 / 2))
#   so the *contents* of self.param may be read but NOT mutated. (The `param`
#   FIELD reference is at full Acc, but the list it points at is at 1/2 — only
#   __init__ ever owns full list_pred on it.) This is the frame-mutation surface.
#
#   UNCONSTRAINED INPUT: `param` carries NO precondition. The ctor vocabulary is
#   an arbitrary caller-supplied list, so an empty one and one repeating a term are
#   admissible, and the spec gives each a modelled outcome. The @Pure predicate
#     usable_terms(xs) == len(xs) > 0 and no term listed twice
#   is what a list must satisfy to serve as a name-to-index mapping; the only
#   precondition using it is Implies(self.fitted, usable_terms(self.names)), the
#   representation invariant of an already-materialised mapping.
#
#   NOR is `names` tied to `param` on an already-fitted object. A fitted object
#   whose ctor list no longer matches its materialised mapping is reachable
#   (set_params rebinds the ctor list without touching the mapping or the
#   supplied-at-construction flag), so those states are IN the domain and the
#   clauses below have to hold there too. That is what forbids an impl from
#   reporting the ctor list where the real query reports the mapping.
#
#   The postcondition's LOAD-BEARING clauses:
#     (E1) self.fitted                                   [object ends usable]
#     (E2) ToSeq(Result()) == ToSeq(self.names)          [returns the mapping]
#     (E3) Implies(not Old(self.fitted),
#                  Old(self.has_param) and Old(usable_terms(self.param))
#                  and self.supplied
#                  and ToSeq(Result()) == ToSeq(self.param))
#          [an unfitted object only became usable BECAUSE a USABLE ctor list was
#           supplied; it is now recorded supplied-at-construction and the names
#           equal that list in order. Reads Old(...): pre-state of the read-only
#           inputs, so an impl cannot satisfy it by overwriting them. The
#           Old(usable_terms(self.param)) conjunct is what forbids returning a list
#           that cannot become a mapping instead of rejecting it.]
#     (X)  Exsures(NotFittedError, ... not Old(self.fitted) and
#                  not Old(self.has_param) and not self.supplied)
#          [the failure surfaces ONLY on a genuinely-unusable object (no mapping
#           AND no ctor list) AND ONLY after recording not self.supplied — the
#           gold's unconditional _validate_vocabulary sets fixed_vocabulary_=False
#           on the vocabulary-None object before _check_vocabulary raises; the
#           F2P asserts that side effect FIRST (assert_false(cv.fixed_vocabulary_),
#           test_text.py:546).]
#     (Y)  Exsures(UnusableTermsError, ... not Old(self.fitted) and
#                  Old(self.has_param) and not Old(usable_terms(self.param))
#                  and not self.fitted and self.supplied == Old(self.supplied)
#                  and names/has_param/param at their entry values)
#          [the materialise step's OWN rejection surfaces exactly when there was a
#           mapping to build and it could not be built, and the object is left
#           untouched: the step validates before its first write, so no mapping
#           appears and the supplied flag keeps its entry value.]
#     (E4) Ensures(self.has_param == Old(self.has_param)) and
#          Ensures(ToSeq(self.param) == Old(ToSeq(self.param))), restated inside
#          (X) and (Y)
#          [the query REPORTS names; it does not reconfigure the object. Whether a
#           list was supplied at construction, and that list itself, are read-only
#           to it on every exit. TRUE of the real query: it reads the ctor list
#           (through the materialise step, which copies it into a local) and never
#           assigns it.]
#     (E5) Ensures(Implies(Old(self.fitted),
#                  ToSeq(self.names) == Old(ToSeq(self.names))
#                  and self.supplied == Old(self.supplied)
#                  and ToSeq(Result()) == Old(ToSeq(self.names))))
#          [PRESERVATION on the already-materialised object: the query only reads
#           an existing mapping. It does not rebuild it, permute it, drop names
#           from it, replace it with the ctor list, or touch the supplied flag; the
#           names it reports are that mapping as it stood on entry. TRUE of the
#           real query: the on-demand materialise step runs ONLY when the mapping
#           is absent, and the remaining work reads the mapping and returns a
#           freshly built list. Without (E5) every observable on this path is free
#           except Result()==names, which an impl satisfies by overwriting names —
#           the tautology (X)/(Y)/(E3) cannot see because they are all guarded by
#           not Old(self.fitted).]
#
#   (X) and (Y) partition the failure surface on read-only pre-state, and together
#   with (E3) they cover every not-already-fitted object: the three exits are
#   mutually exclusive and exhaustive, so no admissible input is left unspecified.
#   (E5) covers the remaining case (already fitted, which must return normally
#   since both Exsures require not Old(self.fitted)) and (E4) covers all three, so
#   every field's exit value is a function of the entry state on every path.
#   The uniqueness rivals below attack each discriminant of each clause, plus the
#   mandatory frame-mutation probe on the half-permission read-only list.
#
# F2P: sklearn/feature_extraction/tests/test_text.py::test_feature_names asserts
#   (a) assert_raises(ValueError, cv.get_feature_names) on an UNFITTED vocab=None
#       object, THEN assert_false(cv.fixed_vocabulary_);
#   (b) on CountVectorizer(vocabulary=<9 distinct food terms>), get_feature_names()
#       == that list in order AND assert_true(cv.fixed_vocabulary_).
#
# AXIOM LANE: there is NO consumed @ContractOnly axiom (meta.axioms == []). The
# single deep-model A-reference is the helper materialise_from_param ==
# _validate_vocabulary (list branch), validated by axiom_check.py / G-AX. The
# axiom probe below re-runs the REAL _validate_vocabulary in the instance image
# and asserts the helper's three Ensures + caller-domain containment + the
# raise-path side effect the Exsures pins (fixed_vocabulary_==False on vocab=None).

from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10908"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The EXACT get_feature_names impl region (between # impl-start / # impl-end,
# exclusive). Every rival rewrites ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # A supplied list that cannot become a mapping: the materialise
                # step reports its rejection and writes nothing at all.
                raise UnusableTermsError()
        else:
            # The on-demand materialise step runs on the unfitted object; with
            # no construction-supplied list it builds nothing but records that
            # the vocabulary was not supplied at construction, and the failure
            # then surfaces.
            self.supplied = False
            raise NotFittedError()
    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        # invariants-start
        Invariant(Acc(self.names) and Acc(list_pred(self.names)))
        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
        Invariant(Acc(self.fitted) and self.fitted)
        Invariant(Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # The construction inputs are only read, so they still hold their entry
        # values on every pass.
        Invariant(self.has_param == Old(self.has_param))
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # The mapping being reported is numbered by place throughout: the copy
        # below reads it, it does not re-index it.
        Invariant(numbered_by_place(self.idx, self.names))
        # Whenever the object was not already fitted, a usable construction-
        # supplied list is what materialised it: the object records a supplied-
        # at-construction vocabulary, and the materialised names equal that list.
        # These facts are stable across the loop below.
        Invariant(Implies(not Old(self.fitted),
                          Old(self.has_param) and Old(usable_terms(self.param))
                          and self.supplied
                          and ToSeq(self.names) == ToSeq(self.param)))
        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
        # re-indexed the mapping, so both of its halves and the supplied-at-
        # construction record are still the ones the object came in with.
        Invariant(Implies(Old(self.fitted),
                          ToSeq(self.names) == Old(ToSeq(self.names))
                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
                          and self.supplied == Old(self.supplied)))
        Invariant(0 <= j and j <= len(self.names))
        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
        # At most len(self.names) - j + 1 passes remain: the materialised mapping
        # is held by the invariant above so its length cannot change, and j rises
        # by exactly one per pass, so the bound strictly decreases; the loop guard
        # j < len(self.names) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.names) - j + 1))
        # invariants-end
        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
        result.append(self.names[j])
        j = j + 1
    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
    return result"""

# The shared, gold copy-loop tail (loop + asserts + return) — reused verbatim by
# every reject rival so the rejection is attributable to ONLY the head change,
# never to a deleted loop invariant / framing assert (pilot bug class 2).
_LOOP_TAIL = """    result = []  # type: List[int]
    j = 0
    while j < len(self.names):
        # invariants-start
        Invariant(Acc(self.names) and Acc(list_pred(self.names)))
        Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
        Invariant(Acc(self.param) and Acc(self.has_param) and Acc(self.supplied))
        Invariant(Acc(self.fitted) and self.fitted)
        Invariant(Acc(list_pred(self.param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # The construction inputs are only read, so they still hold their entry
        # values on every pass.
        Invariant(self.has_param == Old(self.has_param))
        Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
        # The mapping being reported is numbered by place throughout: the copy
        # below reads it, it does not re-index it.
        Invariant(numbered_by_place(self.idx, self.names))
        # Whenever the object was not already fitted, a usable construction-
        # supplied list is what materialised it: the object records a supplied-
        # at-construction vocabulary, and the materialised names equal that list.
        # These facts are stable across the loop below.
        Invariant(Implies(not Old(self.fitted),
                          Old(self.has_param) and Old(usable_terms(self.param))
                          and self.supplied
                          and ToSeq(self.names) == ToSeq(self.param)))
        # Whenever it WAS already fitted, nothing above rebuilt, replaced or
        # re-indexed the mapping, so both of its halves and the supplied-at-
        # construction record are still the ones the object came in with.
        Invariant(Implies(Old(self.fitted),
                          ToSeq(self.names) == Old(ToSeq(self.names))
                          and ToSeq(self.idx) == Old(ToSeq(self.idx))
                          and self.supplied == Old(self.supplied)))
        Invariant(0 <= j and j <= len(self.names))
        Invariant(ToSeq(result) == ToSeq(self.names).take(j))
        # At most len(self.names) - j + 1 passes remain: the materialised mapping
        # is held by the invariant above so its length cannot change, and j rises
        # by exactly one per pass, so the bound strictly decreases; the loop guard
        # j < len(self.names) keeps it >= 2 on entry to a pass.
        Invariant(MustTerminate(len(self.names) - j + 1))
        # invariants-end
        Assert(ToSeq(self.names).take(j + 1).drop(j)[0] == self.names[j])
        result.append(self.names[j])
        j = j + 1
    Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
    return result"""


def _impl(new_head):
    """Build a full model.py whose get_feature_names impl region is new_head
    followed by the verbatim gold copy-loop tail (spec/pure/pre/post and the
    materialise_from_param impl all untouched => same_spec)."""
    return _swap(_BASE, _GOLD_IMPL, new_head + "\n" + _LOOP_TAIL)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

# (R1) FRAME-MUTATION (MANDATORY, directive 5). The supplied list self.param is a
# READ-ONLY input held at Acc(list_pred(self.param), 1 / 2) inside this query. A
# rival that materialises faithfully but then "canonicalises the supplied buffer
# in place" by mutating self.param's CONTENTS (self.param.append(...)) requires
# FULL list_pred permission it does not hold. Nagini must reject it for
# INSUFFICIENT PERMISSION. The gold materialise + loop tail are kept verbatim so
# the rejection is attributable solely to the write. A byte-fuzzer never thinks
# to mutate the input — this is the project's #1 weakness class.
_HEAD_FRAME_MUT = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
                # FRAME-MUTATION ATTACK: write to the half-permission read-only
                # list.
                self.param.append(self.param[0])
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R2) RAISE-PATH SIDE-EFFECT OMISSION (the batch-05 RE-AUDIT defect, re-attacked).
# On the genuinely-unfitted (no ctor list) path, raise NotFittedError WITHOUT
# recording self.supplied = False. This is the pre-patch _check_vocabulary-only
# behaviour: it leaves fixed_vocabulary_ unset, so the F2P's FIRST post-raise
# assertion assert_false(cv.fixed_vocabulary_) gets AttributeError and FAILS.
# Must be rejected by the Exsures clause "... and not self.supplied".
_HEAD_RAISE_NO_SUPPLIED = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            # ATTACK: raise WITHOUT recording not-supplied (pre-patch path).
            raise NotFittedError()"""

# (R3) WRONG MATERIALISATION on the has_param success path (Old(has_param)/E3
# attack). Instead of calling the audited materialise helper, the rival fakes a
# fit: marks fitted+supplied but leaves self.names EMPTY (does not build the
# mapping from the supplied list). E1 (self.fitted) and E2 (Result()==names) are
# trivially met, but E3's "ToSeq(Result()) == ToSeq(self.param)" FAILS whenever
# self.param is non-empty (the F2P 9-term list). Must be rejected by E3.
_HEAD_WRONG_NAMES = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                # ATTACK: fake a fit without building the mapping from the list.
                # (Both halves of the mapping view are written, so the rival's
                # state IS numbered by place — an empty mapping vacuously is —
                # and the rejection is attributable to the reported names, not
                # to an inconsistent representation.)
                empty = []  # type: List[int]
                empty_idx = []  # type: List[int]
                self.names = empty
                self.idx = empty_idx
                self.fitted = True
                self.supplied = True
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R4) NO-RAISE-ON-UNFITTED (partial-domain, the pre-patch bug's mirror image).
# On the genuinely-unfitted path the rival does NOT raise; it fakes a fit (empty
# names) and falls through to return []. This is a "swallow the error" wrong
# patch. It violates E3: not Old(self.fitted) holds but Old(self.has_param) is
# False, so the consequent Old(self.has_param) is unprovable. Must be rejected.
# (Its faithful real patch returns [] instead of raising NotFittedError on the
# vocab=None object => F2P assert_raises(ValueError, cv.get_feature_names) FAILS.)
_HEAD_NO_RAISE = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            # ATTACK: swallow the failure — fake a fit and return [].
            # (Both halves written, so the faked mapping is numbered by place.)
            empty = []  # type: List[int]
            empty_idx = []  # type: List[int]
            self.names = empty
            self.idx = empty_idx
            self.fitted = True
            self.supplied = False"""

# (R7) UNUSABLE-LIST SWALLOWED as a successful return. On an unfitted object whose
# construction-supplied list cannot become a mapping (empty, or a name listed
# twice), the rival does NOT report the materialise step's rejection: it copies the
# list through as if it were a mapping and returns it. Must be rejected by the
# not-already-fitted success consequent, whose Old(usable_terms(self.param)) conjunct
# is FALSE on exactly these inputs, so a normal return cannot be justified.
_HEAD_UNUSABLE_RETURNED = """    if not self.fitted:
        if self.has_param:
            # ATTACK: treat ANY supplied list as a mapping, usable or not.
            # The copy loop carries the construction-input preservation
            # invariant and builds BOTH halves of the mapping view (numbered by
            # place, exactly as the real materialise step numbers one), so the
            # rejection is attributable to the rival's screen — it accepts a
            # list that cannot become a mapping — and not to lost framing or an
            # inconsistent representation.
            materialise_any = []  # type: List[int]
            any_idx = []  # type: List[int]
            m = 0
            while m < len(self.param):
                # invariants-start
                Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
                Invariant(Acc(list_pred(materialise_any)) and Acc(list_pred(any_idx)))
                Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
                Invariant(0 <= m and m <= len(self.param) and not isinstance(m, bool))
                Invariant(ToSeq(materialise_any) == ToSeq(self.param).take(m))
                Invariant(len(any_idx) == m and ToSeq(any_idx) == places(m))
                Invariant(MustTerminate(len(self.param) - m + 1))
                # invariants-end
                Assert(ToSeq(self.param).take(m + 1).drop(m)[0] == self.param[m])
                materialise_any.append(self.param[m])
                any_idx.append(m)
                m = m + 1
            Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
            Assert(len(materialise_any) == m and len(any_idx) == m)
            Assert(places(len(materialise_any)) == places(m))
            self.names = materialise_any
            self.idx = any_idx
            self.fitted = True
            self.supplied = True
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R8) UNUSABLE-LIST REPORTED AS THE WRONG FAILURE. The rival screens the supplied
# list correctly but, when it is not usable, reports the unfitted-object failure
# instead of the materialise step's own rejection (and records not-supplied on the
# way out). Must be rejected by the unfitted-object failure's own guard, whose
# not Old(self.has_param) conjunct is FALSE here — a list WAS supplied.
_HEAD_WRONG_FAILURE = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # ATTACK: report the unfitted-object failure for a list that was
                # supplied but could not become a mapping.
                self.supplied = False
                raise NotFittedError()
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R9) UNUSABLE-LIST PATH WRITES THE FLAG. The rival reports the right rejection but
# also records not-supplied-at-construction on the way out. The materialise step
# rejects such a list BEFORE it records anything, so the flag must keep its entry
# value. Must be rejected by that Exsures' self.supplied == Old(self.supplied).
_HEAD_REJECT_WRITES_FLAG = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                # ATTACK: record a flag the rejecting step never writes.
                self.supplied = False
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R10) ALREADY-FITTED MAPPING DISCARDED (the E5 attack; the shape the P2 audit
# found VERIFYING against the pre-repair spec). The not-yet-fitted paths are the
# gold ones, so every clause guarded by not Old(self.fitted) is satisfied; on the
# ALREADY-fitted object the rival throws the mapping away and reports no names.
# Under the pre-repair spec this verified: E1 (self.fitted) still held, and E2
# (ToSeq(Result()) == ToSeq(self.names)) was satisfied by writing self.names, so
# nothing observed the already-present mapping. Must be rejected by (E5).
_HEAD_FITTED_DISCARD = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: throw away the mapping the object already had. (Both halves
        # are cleared together, so the resulting state is still numbered by
        # place — vacuously — and the rejection is attributable to the lost
        # names, not to a half-updated representation.)
        cleared = []  # type: List[int]
        cleared_idx = []  # type: List[int]
        self.names = cleared
        self.idx = cleared_idx"""

# (R11) ALREADY-FITTED MAPPING PERMUTED. Same guarded prologue; on the already-
# fitted object the rival reports the mapping in the reverse of its index order
# (and stores it that way, so E2 still holds). The inner loop carries the
# preservation invariant so the rejection is attributable to the single write
# self.names = rev, not to lost framing. Must be rejected by (E5).
_HEAD_FITTED_REORDER = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: report the mapping in the reverse of its index order.
        rev = []  # type: List[int]
        k = len(self.names)
        while k > 0:
            # invariants-start
            Invariant(Acc(self.names) and Acc(list_pred(self.names)))
            Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
            Invariant(Acc(list_pred(rev)))
            Invariant(ToSeq(self.names) == Old(ToSeq(self.names)))
            # The numbering half is left exactly as it was, and the reversed
            # list has the same LENGTH, so the rival's end state is still
            # numbered by place: it re-orders the reported names without
            # touching which index each place carries. The rejection is
            # therefore attributable to the single write self.names = rev.
            Invariant(numbered_by_place(self.idx, self.names))
            Invariant(0 <= k and k <= len(self.names))
            Invariant(len(rev) == len(self.names) - k)
            Invariant(MustTerminate(k + 1))
            # invariants-end
            rev.append(self.names[k - 1])
            k = k - 1
        Assert(len(rev) == len(self.names) and len(self.idx) == len(rev))
        Assert(places(len(rev)) == places(len(self.names)))
        self.names = rev"""

# (R12) ALREADY-FITTED OBJECT REPORTS THE CONSTRUCTION LIST INSTEAD OF ITS
# MAPPING. This is the rival the G-PANEL-2 faithfulness role found: it is correct
# on every state where the materialised mapping and the ctor list agree, and wrong
# exactly on the states a fitted object reaches after its ctor list is rebound.
# Those states are IN the domain (no precondition ties names to param), so the
# rival must be rejected — by (E5), whose ToSeq(self.names) == Old(ToSeq(self.names))
# it cannot establish after overwriting the mapping with the supplied list.
_HEAD_FITTED_RETURN_PARAM = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        if self.supplied and usable_terms(self.param):
            # ATTACK: report the construction-supplied list, not the mapping.
            # The loop carries the construction-input preservation invariant and
            # builds a consistent numbering for the echoed list, so the rival's
            # end state is a well-formed mapping numbered by place and the
            # rejection is attributable to WHICH names it reports.
            echo = []  # type: List[int]
            echo_idx = []  # type: List[int]
            m = 0
            while m < len(self.param):
                # invariants-start
                Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
                Invariant(Acc(list_pred(echo)) and Acc(list_pred(echo_idx)))
                Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
                Invariant(0 <= m and m <= len(self.param) and not isinstance(m, bool))
                Invariant(ToSeq(echo) == ToSeq(self.param).take(m))
                Invariant(len(echo_idx) == m and ToSeq(echo_idx) == places(m))
                Invariant(MustTerminate(len(self.param) - m + 1))
                # invariants-end
                Assert(ToSeq(self.param).take(m + 1).drop(m)[0] == self.param[m])
                echo.append(self.param[m])
                echo_idx.append(m)
                m = m + 1
            Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
            Assert(len(echo) == m and len(echo_idx) == m)
            Assert(places(len(echo)) == places(m))
            self.names = echo
            self.idx = echo_idx"""

# (R13) THE QUERY RECONFIGURES ITS OBJECT (the E4 attack). Values are all
# CORRECT — the right names are reported on every path — but on the way out of a
# successful call the rival also drops the construction-supplied list and the
# record that one was supplied, "releasing" an input it no longer needs. Right
# value, wrong effect. Must be rejected by (E4).
_HEAD_RECONFIGURES = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    # ATTACK: right names, but the construction inputs are cleared on the way out.
    dropped = []  # type: List[int]
    self.param = dropped
    self.has_param = False"""

# (R14) THE UNFITTED-OBJECT FAILURE PLANTS A MAPPING VIEW. The rival records the
# not-supplied side effect the failure exit demands (so clause X's original
# conjuncts hold) but also rewrites the mapping view on the way out. The failure
# exit's own step builds nothing, so the mapping view must keep its entry value.
# Must be rejected by the strengthened NotFittedError exit.
_HEAD_RAISE_PLANTS_NAMES = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            # ATTACK: rewrite the mapping view on the failure exit.
            planted = [0]  # type: List[int]
            self.names = planted
            self.supplied = False
            raise NotFittedError()"""

# (R15) POSITIVE CONTROL (soundness) for (E5): the preservation clause is about
# VALUES, not object identity. This rival is CORRECT — on the already-fitted path
# it replaces the mapping view with a freshly built list of the SAME names in the
# SAME order (the real query likewise re-derives its answer from the mapping on
# every call) and reports those names. It MUST verify; if it could not, (E5) would
# be pinning an incidental representation detail rather than behaviour.
_HEAD_FITTED_REBUILD_EQUAL = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        same = []  # type: List[int]
        p = 0
        while p < len(self.names):
            # invariants-start
            Invariant(Acc(self.names) and Acc(list_pred(self.names)))
            Invariant(Acc(list_pred(same)))
            Invariant(ToSeq(self.names) == Old(ToSeq(self.names)))
            Invariant(0 <= p and p <= len(self.names))
            Invariant(ToSeq(same) == ToSeq(self.names).take(p))
            Invariant(MustTerminate(len(self.names) - p + 1))
            # invariants-end
            Assert(ToSeq(self.names).take(p + 1).drop(p)[0] == self.names[p])
            same.append(self.names[p])
            p = p + 1
        Assert(ToSeq(self.names).take(len(self.names)) == ToSeq(self.names))
        self.names = same"""

# (R17) ALREADY-FITTED MAPPING RENUMBERED (the shape the G-PANEL-1 role found
# verifying against the pre-`idx` spec, restated against the carrier that can now
# see it). The reported names are EXACTLY the ones the object came in with, in
# exactly their order — so every clause about the name sequence, including (E5)'s
# ToSeq(self.names) == Old(ToSeq(self.names)) and (E2), is satisfied — but the
# mapping those names belong to is re-indexed: the name at place k is sent to 2k.
# Must be rejected by Ensures(numbered_by_place(self.idx, self.names)) and by
# (E5)'s ToSeq(self.idx) == Old(ToSeq(self.idx)).
_HEAD_FITTED_RENUMBER = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: report the very same names in the very same order, but send the
        # name at place k to index 2k instead of k.
        renum = []  # type: List[int]
        q = 0
        while q < len(self.idx):
            # invariants-start
            Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
            Invariant(Acc(list_pred(renum)))
            Invariant(ToSeq(self.idx) == Old(ToSeq(self.idx)))
            Invariant(0 <= q and q <= len(self.idx))
            Invariant(len(renum) == q)
            Invariant(MustTerminate(len(self.idx) - q + 1))
            # invariants-end
            renum.append(2 * q)
            q = q + 1
        Assert(len(renum) == len(self.idx))
        self.idx = renum"""

# (R18) ALREADY-FITTED MAPPING RENUMBERED FROM ONE (boundary token swap). Same
# shape as R17 but the numbering is shifted by exactly one — the name at place k
# is sent to k + 1, so the mapping is 1-based instead of 0-based. Every name is
# reported at its original place; only the base of the numbering moves. It is the
# smallest possible renumbering, and it must still be rejected: places are indices
# 0 .. n-1, not 1 .. n.
_HEAD_FITTED_ONE_BASED = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: number the mapping from one instead of from zero.
        shifted = []  # type: List[int]
        q = 0
        while q < len(self.idx):
            # invariants-start
            Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
            Invariant(Acc(list_pred(shifted)))
            Invariant(ToSeq(self.idx) == Old(ToSeq(self.idx)))
            Invariant(0 <= q and q <= len(self.idx))
            Invariant(len(shifted) == q)
            Invariant(MustTerminate(len(self.idx) - q + 1))
            # invariants-end
            shifted.append(q + 1)
            q = q + 1
        Assert(len(shifted) == len(self.idx))
        self.idx = shifted"""

# (R19) THE MATERIALISED MAPPING IS NUMBERED FROM ONE (the F2P custom-vocabulary
# path). This rival does NOT touch an already-fitted object; it attacks the path
# the gold patch adds. On an unfitted object with a usable construction-supplied
# list it materialises the RIGHT names in the RIGHT order — so (E3)'s
# ToSeq(Result()) == ToSeq(self.param), self.fitted and self.supplied all hold,
# and the returned list is indistinguishable from the gold's — but it numbers
# those names 1 .. n instead of 0 .. n-1. Must be rejected by
# Ensures(numbered_by_place(self.idx, self.names)); no other clause sees it.
_HEAD_SUPPLIED_RENUMBER = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                # ATTACK: materialise the right names from the supplied list, but
                # give term i of that list index i + 1.
                shift_names = []  # type: List[int]
                shift_idx = []  # type: List[int]
                q = 0
                while q < len(self.param):
                    # invariants-start
                    Invariant(Acc(self.param) and Acc(list_pred(self.param), 1 / 2))
                    Invariant(Acc(list_pred(shift_names)) and Acc(list_pred(shift_idx)))
                    Invariant(ToSeq(self.param) == Old(ToSeq(self.param)))
                    Invariant(0 <= q and q <= len(self.param))
                    Invariant(ToSeq(shift_names) == ToSeq(self.param).take(q))
                    Invariant(len(shift_idx) == q)
                    Invariant(MustTerminate(len(self.param) - q + 1))
                    # invariants-end
                    Assert(ToSeq(self.param).take(q + 1).drop(q)[0] == self.param[q])
                    shift_names.append(self.param[q])
                    shift_idx.append(q + 1)
                    q = q + 1
                Assert(ToSeq(self.param).take(len(self.param)) == ToSeq(self.param))
                Assert(len(shift_names) == len(shift_idx))
                self.names = shift_names
                self.idx = shift_idx
                self.fitted = True
                self.supplied = True
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()"""

# (R20) RENUMBERS ONLY THE MAPPINGS IT CANNOT BE CAUGHT ON (partial-domain guard).
# The rival is the gold everywhere except on an already-fitted mapping holding
# MORE than two names, where it doubles every index. A domain-restricted rival
# like this is the classic way a weak spec is exploited: it is correct on the
# small states a reader checks by hand and wrong on the rest. Every state it is
# wrong on is admissible (nothing bounds the size of a materialised mapping), so
# it must be rejected exactly as R17 is.
_HEAD_RENUMBER_BIG_ONLY = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        if len(self.idx) > 2:
            # ATTACK: renumber, but only where a small hand-checked example
            # cannot see it.
            renum_big = []  # type: List[int]
            q = 0
            while q < len(self.idx):
                # invariants-start
                Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
                Invariant(Acc(list_pred(renum_big)))
                Invariant(ToSeq(self.idx) == Old(ToSeq(self.idx)))
                Invariant(0 <= q and q <= len(self.idx))
                Invariant(len(renum_big) == q)
                Invariant(MustTerminate(len(self.idx) - q + 1))
                # invariants-end
                renum_big.append(2 * q)
                q = q + 1
            Assert(len(renum_big) == len(self.idx))
            self.idx = renum_big"""

# (R21) THE INDEX OF A NAME IS THE NAME (oracle echo). Instead of reporting which
# index each name carries, the rival echoes the names themselves back as their own
# indices. This is the echo family: it is right exactly on the states where the
# answer happens to coincide with the input (a mapping whose term ids are already
# 0, 1, 2, … in order — including the F2P-shaped states built from term ids 0..8),
# and wrong on every other, so a battery that only ever exercises canonical term
# ids would not see it. Lengths still match, so only the place-numbering clause
# can reject it.
_HEAD_IDX_ECHO_NAMES = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: echo each name as its own index.
        echo_idx = []  # type: List[int]
        q = 0
        while q < len(self.names):
            # invariants-start
            Invariant(Acc(self.names) and Acc(list_pred(self.names)))
            Invariant(Acc(list_pred(echo_idx)))
            Invariant(ToSeq(self.names) == Old(ToSeq(self.names)))
            Invariant(0 <= q and q <= len(self.names))
            Invariant(len(echo_idx) == q)
            Invariant(MustTerminate(len(self.names) - q + 1))
            # invariants-end
            echo_idx.append(self.names[q])
            q = q + 1
        Assert(len(echo_idx) == len(self.names))
        self.idx = echo_idx"""

# (R22) EVERY NAME ADDRESSES COLUMN ZERO (over-approximation). The rival keeps a
# mapping of the right SIZE holding the right names in the right order, but throws
# the numbering away: every name is sent to index 0. This is what "the mapping has
# an index for each name" degrades to when the index VALUES are not pinned — the
# weakest possible witness that still has one index per name. Must be rejected.
_HEAD_IDX_ALL_ZERO = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        # ATTACK: send every name to column 0.
        flat_idx = []  # type: List[int]
        q = 0
        while q < len(self.idx):
            # invariants-start
            Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
            Invariant(Acc(list_pred(flat_idx)))
            Invariant(ToSeq(self.idx) == Old(ToSeq(self.idx)))
            Invariant(0 <= q and q <= len(self.idx))
            Invariant(len(flat_idx) == q)
            Invariant(MustTerminate(len(self.idx) - q + 1))
            # invariants-end
            flat_idx.append(0)
            q = q + 1
        Assert(len(flat_idx) == len(self.idx))
        self.idx = flat_idx"""

# (R23) POSITIVE CONTROL (soundness) for the place-numbering clause: like R15 for
# the names half, it must be about VALUES, not object identity. On the already-
# fitted path this rival rebuilds the index half as a freshly allocated list
# carrying the SAME numbering (place q ↦ q) and reports the same names. The real
# query likewise re-derives its answer from the mapping on every call. It MUST
# verify; if it could not, numbered_by_place / the idx frame would be pinning
# which list object holds the numbering rather than what the numbering IS.
_HEAD_FITTED_REBUILD_IDX_EQUAL = """    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()
    else:
        fresh_idx = []  # type: List[int]
        q = 0
        while q < len(self.idx):
            # invariants-start
            Invariant(Acc(self.idx) and Acc(list_pred(self.idx)))
            Invariant(Acc(list_pred(fresh_idx)))
            Invariant(ToSeq(self.idx) == Old(ToSeq(self.idx)))
            Invariant(0 <= q and q <= len(self.idx) and not isinstance(q, bool))
            Invariant(len(fresh_idx) == q)
            Invariant(ToSeq(fresh_idx) == places(q))
            Invariant(MustTerminate(len(self.idx) - q + 1))
            # invariants-end
            fresh_idx.append(q)
            q = q + 1
        Assert(len(fresh_idx) == len(self.idx))
        Assert(places(len(fresh_idx)) == places(q))
        self.idx = fresh_idx"""


# (R5) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT. The
# guard is FLATTENED from a nested if/else into two sequential guards:
#   materialise iff (not fitted and has_param); then raise iff still not fitted.
# Semantically identical first-match cascade (after materialise, fitted is True,
# so the raise guard is skipped). The verbatim gold copy-loop tail keeps every
# framing assert / invariant, so it MUST verify (else SPEC-TOO-STRONG). No loop
# reversal / induction lemma is introduced (pilot bug classes 2 & 3 avoided).
_HEAD_POS_FLAT = """    if not self.fitted and self.has_param and not usable_terms(self.param):
        raise UnusableTermsError()
    if not self.fitted and self.has_param:
        materialise_from_param(self)
    if not self.fitted:
        self.supplied = False
        raise NotFittedError()"""

# (R6) ADMISSIBILITY (precondition admits an F2P-shaped input). The probe builds
# a fresh F2P-shaped Vectoriser (UNFITTED, has_param, supplied=False, a non-empty
# supplied list, empty names) — exactly the gold custom-vocabulary case — and
# ASSERTS every Requires conjunct of get_feature_names for it, including the
# representation invariant Implies(fitted, usable_terms(names)) (vacuously true
# for an unfitted object) and the half permission on the read-only supplied
# list. If any conjunct could not be established for this legitimate input =>
# PRECOND-TOO-STRONG. The gold head + loop tail follow verbatim, so the function's
# own postcondition obligation is unchanged. Editing ONLY the impl region keeps
# same_spec true.
#
# Assert-style rather than a recursive self-call: get_feature_names now carries
# Requires(MustTerminate(3)) (total correctness), and Nagini requires a callee's
# obligation level to be STRICTLY below the caller's, so an equal-level self-call
# is rejected by the obligation system ("Callee get_feature_names might not take
# all unsatisfied obligations from the caller") — an artifact of the termination
# spec, unrelated to the value preconditions this case is about. The constructor
# call is still a REAL call site (level 1 < 3), so __init__'s own Requires are
# discharged for these arguments, and every value conjunct is then asserted
# directly. The sibling MustTerminate bundles use this same shape.
_HEAD_ADMISS = """    supplied_list = [7, 8, 9]  # type: List[int]
    empty_names = []  # type: List[int]
    empty_idx = []  # type: List[int]
    # the input really is the discriminating F2P shape: a NON-EMPTY supplied list
    # and an empty (not yet materialised) mapping.
    Assert(len(supplied_list) == 3)
    Assert(len(empty_names) == 0)
    probe = Vectoriser(False, True, False, supplied_list, empty_names, empty_idx)
    # every Requires conjunct of get_feature_names, for that input
    Assert(Acc(probe.fitted) and Acc(probe.has_param) and Acc(probe.supplied))
    Assert(Acc(probe.param) and Acc(probe.names) and Acc(probe.idx))
    Assert(Acc(list_pred(probe.param), 1 / 2))
    Assert(Acc(list_pred(probe.names)))
    Assert(Acc(list_pred(probe.idx)))
    Assert(Implies(probe.fitted, usable_terms(probe.names)))
    Assert(Implies(probe.fitted, numbered_by_place(probe.idx, probe.names)))
    # unfitted, a construction-supplied list present, not yet recorded as
    # supplied-at-construction — exactly the case the failure must NOT fire on.
    Assert(not probe.fitted and probe.has_param and not probe.supplied)
    Assert(probe.param is supplied_list and probe.names is empty_names)
    Assert(probe.idx is empty_idx)
    # --- gold head verbatim below ---
    if not self.fitted:
        if self.has_param:
            if usable_terms(self.param):
                materialise_from_param(self)
            else:
                raise UnusableTermsError()
        else:
            self.supplied = False
            raise NotFittedError()"""


# For R5 / R6 the gold loop tail must follow; R6 already includes the gold head,
# so it uses _impl too (head = the probe + gold head).
SPEC_TESTS = [
    {
        "id": "frame-mutation-write-readonly-param",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FRAME_MUT),
        "refinement": (
            "Its faithful real patch would mutate the user-supplied constructor "
            "vocabulary list in place inside get_feature_names "
            "(self.vocabulary.append(...)). The gold patch NEVER writes to the "
            "constructor list — get_feature_names only reads it via "
            "_validate_vocabulary. A real patch that appended to self.vocabulary "
            "would corrupt the object's vocabulary on every call and on the F2P "
            "9-term list would return 10 names, so "
            "assert_array_equal(['beer',...], feature_names) FAILS. It does not "
            "resolve."),
        "rationale": (
            "Rejected by the PERMISSION SYSTEM, not a value clause: self.param's "
            "list contents are held at Acc(list_pred(self.param), 1 / 2) "
            "(directive-5 read-only input), so self.param.append(...) needs full "
            "list_pred permission the query does not have — Nagini reports "
            "insufficient permission. The gold materialise + loop tail are kept "
            "verbatim, so the failure is attributable solely to the write."),
    },
    {
        "id": "raise-without-recording-not-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_RAISE_NO_SUPPLIED),
        "refinement": (
            "This is the pre-patch _check_vocabulary-only refinement the batch-05 "
            "re-audit found: 'if not hasattr(self,\"vocabulary_\") and "
            "self.vocabulary is not None: self._validate_vocabulary()' — which "
            "SKIPS _validate_vocabulary on the vocab=None object and goes straight "
            "to the raise. fixed_vocabulary_ is therefore never set, so the F2P's "
            "first post-raise assertion assert_false(cv.fixed_vocabulary_) "
            "(test_text.py:546) hits AttributeError and FAILS. It does not "
            "resolve."),
        "rationale": (
            "Rejected by the Exsures discriminant '... and not self.supplied': the "
            "raise path leaves self.supplied at its (true/unknown) entry value "
            "rather than writing False, so Nagini reports 'Postcondition ... "
            "Assertion (not self.supplied) might not hold'. This is exactly the "
            "raise-path side effect (fixed_vocabulary_=False) the gold's "
            "unconditional _validate_vocabulary records before _check_vocabulary "
            "raises."),
    },
    {
        "id": "fake-fit-empty-names-has-param",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_WRONG_NAMES),
        "refinement": (
            "Faithful real patch: the inserted guard sets vocabulary_ = {} and "
            "fixed_vocabulary_=True WITHOUT iterating the supplied list (a broken "
            "materialisation). get_feature_names then returns [] for the F2P "
            "9-term custom vocabulary, so assert_array_equal(['beer',...], "
            "feature_names) FAILS. It does not resolve."),
        "rationale": (
            "Rejected by E3 (Implies(not Old(self.fitted), ... ToSeq(Result()) == "
            "ToSeq(self.param))): the object was not already fitted, so the "
            "returned names must equal the supplied list in order; an empty names "
            "list violates this whenever self.param is non-empty (the F2P case). "
            "E1/E2 alone are too weak to catch it — E3's tie to ToSeq(self.param) "
            "is what rejects it."),
    },
    {
        "id": "swallow-failure-no-raise-on-unfitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_NO_RAISE),
        "refinement": (
            "Faithful real patch: the genuinely-unfitted (vocabulary is None) "
            "object is given vocabulary_={} and returns [] instead of raising "
            "NotFittedError. The F2P test asserts assert_raises(ValueError, "
            "cv.get_feature_names) on exactly that object, so the patch FAILS that "
            "assertion (no exception is raised). It does not resolve."),
        "rationale": (
            "Rejected by E3: not Old(self.fitted) holds on this path but "
            "Old(self.has_param) is False, so the consequent Old(self.has_param) "
            "is unprovable on the normal (non-exceptional) return. The success "
            "consequent forbids returning normally from a genuinely-unfitted "
            "object that had no ctor list — it must raise instead."),
    },
    {
        "id": "unusable-supplied-list-returned-not-rejected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_UNUSABLE_RETURNED),
        "refinement": (
            "Faithful real patch: the inserted on-demand materialisation builds "
            "vocabulary_ from the constructor list WITHOUT the validation the real "
            "routine performs, so CountVectorizer(vocabulary=['x','x']) "
            ".get_feature_names() returns ['x','x'] and "
            "CountVectorizer(vocabulary=[]).get_feature_names() returns [], where "
            "the real routine raises ValueError('Duplicate term in vocabulary')/"
            "ValueError('empty vocabulary passed to fit'). It does not resolve: it "
            "silently accepts vocabularies every other entry point on the object "
            "rejects, so a repeated term would collapse two features onto one "
            "index."),
        "rationale": (
            "Rejected by the not-already-fitted success consequent: its "
            "Old(usable_terms(self.param)) conjunct is FALSE for an empty or "
            "repeating supplied list, so a normal return cannot be justified on "
            "those inputs — the query has to exit through the materialise step's "
            "rejection instead. The screen + gold loop tail are otherwise kept, so "
            "the failure is attributable solely to the missing screen."),
    },
    {
        "id": "unusable-supplied-list-reported-as-unfitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_WRONG_FAILURE),
        "refinement": (
            "Faithful real patch: get_feature_names screens the constructor list "
            "itself and calls _check_vocabulary (raising NotFittedError) for a list "
            "it will not materialise, instead of letting _validate_vocabulary's own "
            "ValueError surface. It does not resolve: "
            "CountVectorizer(vocabulary=['x','x']).get_feature_names() would report "
            "\"Vocabulary wasn't fitted\" for an object that HAS a vocabulary, "
            "hiding the duplicate the real routine names, and would set "
            "fixed_vocabulary_=False on an object constructed WITH a vocabulary."),
        "rationale": (
            "Rejected by the unfitted-object failure's own guard: that Exsures "
            "requires not Old(self.has_param), and a list WAS supplied here, so "
            "Nagini reports the (not Old(self.has_param)) assertion might not "
            "hold. The two failures are not interchangeable — each is pinned to "
            "the state that produces it."),
    },
    {
        "id": "rejecting-step-writes-supplied-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_REJECT_WRITES_FLAG),
        "refinement": (
            "Faithful real patch: the guard sets fixed_vocabulary_ = False before "
            "letting the constructor list's validation error propagate. It does not "
            "resolve as a faithful model of the callee: the real routine validates "
            "the list BEFORE its fixed_vocabulary_ = True write and before its "
            "vocabulary is None else-branch, so a rejected list leaves the flag "
            "exactly as it was — absent on a fresh object, unchanged on one that "
            "already carried it (confirmed by running the real "
            "get_feature_names on CountVectorizer(vocabulary=['x','x']) with and "
            "without fixed_vocabulary_ preset)."),
        "rationale": (
            "Rejected by the rejection Exsures' self.supplied == Old(self.supplied): "
            "the rival overwrites the flag on a path where the modelled step writes "
            "nothing. This pins the no-side-effect half of the rejection, the mirror "
            "of the not-self.supplied side effect the unfitted-object failure pins."),
    },
    {
        "id": "already-fitted-mapping-discarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FITTED_DISCARD),
        "refinement": (
            "Faithful real patch: the inserted guard is gold, but on an object "
            "that ALREADY has vocabulary_ the query sets vocabulary_ = {} and "
            "returns []. It does not resolve — F2P test_feature_names calls "
            "get_feature_names on the object it has just fit_transform'ed and "
            "asserts assert_equal(len(feature_names), n_features) then "
            "assert_array_equal(['beer',...,'water'], feature_names) "
            "(test_text.py:555-558 with the test patch applied); [] fails both. "
            "It also breaks every downstream P2P user of the fitted path "
            "(test_count_vectorizer_max_features, test_count_binary_occurrences)."),
        "rationale": (
            "Rejected by (E5): with Old(self.fitted) true the query must leave the "
            "mapping at its entry value, so ToSeq(self.names) == "
            "Old(ToSeq(self.names)) fails after the write. Note (E1) and (E2) do "
            "NOT catch this — the rival keeps self.fitted true and satisfies "
            "ToSeq(Result()) == ToSeq(self.names) by rewriting names, which is why "
            "an already-fitted preservation clause is needed rather than a "
            "stronger version of the not-already-fitted one. The rival clears "
            "BOTH halves of the mapping view together, so its end state is a "
            "well-formed (vacuously numbered-by-place) mapping and the rejection "
            "cannot be dismissed as a half-updated representation."),
    },
    {
        "id": "already-fitted-mapping-permuted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FITTED_REORDER),
        "refinement": (
            "Faithful real patch: on an already-fitted object the query re-sorts "
            "the mapping by DESCENDING index (key=itemgetter(1), reverse=True) and "
            "stores the reversed correspondence back. It does not resolve: F2P's "
            "already-fitted block asserts assert_array_equal(['beer',...,'water'], "
            "feature_names) in ASCENDING index order, and the following loop "
            "assert_equal(idx, cv.vocabulary_.get(name)) checks the returned order "
            "against the mapping's own indices."),
        "rationale": (
            "Rejected by (E5): the mapping the object carries out is the reverse "
            "of the one it came in with, so ToSeq(self.names) == "
            "Old(ToSeq(self.names)) fails. The reversing loop carries that same "
            "preservation invariant, so the rejection is attributable to the single "
            "write self.names = rev and not to lost framing. It also leaves the "
            "numbering half untouched at the same length, so the rival's end state "
            "is still numbered by place: it is rejected for re-ordering the names "
            "it reports, not for an inconsistent representation."),
    },
    {
        "id": "already-fitted-reports-ctor-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FITTED_RETURN_PARAM),
        "refinement": (
            "Faithful real patch: on an object that reports a construction-supplied "
            "vocabulary the query answers from self.vocabulary (the ctor list) "
            "rather than from self.vocabulary_ (the materialised mapping). It "
            "agrees with the gold on every object whose two still match, and "
            "diverges as soon as they do not — e.g. after set_params(vocabulary=...) "
            "on a fitted object, where the real query keeps reporting the "
            "materialised mapping. It does not resolve as a faithful model: it "
            "reads a mutable constructor parameter where the real query reads the "
            "learned attribute, so the names it reports need not be the ones the "
            "object's own vocabulary_ indices name (the F2P loop "
            "assert_equal(idx, cv.vocabulary_.get(name)) is exactly that check)."),
        "rationale": (
            "Rejected by (E5). This is the rival the faithfulness role exhibited "
            "against the pre-repair spec, which admitted it only because a "
            "precondition ASSUMED ToSeq(self.names) == ToSeq(self.param) on every "
            "fitted-and-supplied object — an assumption the real object does not "
            "maintain. With that assumption gone the states where the two differ "
            "are in the domain, and (E5) forbids answering from the ctor list "
            "there. Diagnostic value: if this case ever verifies again, a "
            "names-to-param tie has crept back into the precondition."),
    },
    {
        "id": "query-reconfigures-construction-inputs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_RECONFIGURES),
        "refinement": (
            "Faithful real patch: get_feature_names returns exactly the gold names "
            "but signs off with self.vocabulary = []; that is, it clears the "
            "constructor parameter once the mapping is materialised. Right value, "
            "wrong effect. It does not resolve: the constructor parameter is part "
            "of the estimator's get_params contract, so P2P "
            "test_vectorizer_vocab_clone (clone(vec) rebuilds from get_params and "
            "compares) and test_countvectorizer_vocab_sets_when_pickling / "
            "..._dicts_when_pickling (which round-trip the object and re-check its "
            "vocabulary) all break after a single get_feature_names call."),
        "rationale": (
            "Rejected by (E4): the query may report the construction inputs' "
            "consequences but not overwrite them, so self.has_param == "
            "Old(self.has_param) and ToSeq(self.param) == Old(ToSeq(self.param)) "
            "fail. This is the value-clause counterpart of the frame-mutation case "
            "above: that one writes THROUGH the read-only list (caught by the "
            "permission system), this one REBINDS the field to a different list "
            "(permissions allow it, so a value clause must forbid it)."),
    },
    {
        "id": "unfitted-failure-plants-mapping",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_RAISE_PLANTS_NAMES),
        "refinement": (
            "Faithful real patch: on the genuinely-unfitted object the query "
            "records fixed_vocabulary_ = False (so the F2P's first post-raise "
            "assertion passes) but also assigns a bogus vocabulary_ before letting "
            "NotFittedError propagate. It does not resolve: the object is left "
            "carrying a fabricated one-term vocabulary_, so hasattr(cv, "
            "'vocabulary_') is now True and the NEXT call returns that fabrication "
            "instead of raising — and cv.fit_transform's own bookkeeping is "
            "observed against a vocabulary_ the object never learned."),
        "rationale": (
            "Rejected by the strengthened NotFittedError exit: that path's only "
            "write is the not-supplied record, so ToSeq(self.names) == "
            "Old(ToSeq(self.names)) fails. Pinning the whole exit state (rather "
            "than only the not-supplied conjunct) is what stops an impl from paying "
            "the required side effect and then adding others."),
    },
    {
        "id": "already-fitted-mapping-renumbered",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FITTED_RENUMBER),
        "refinement": (
            "Faithful real patch: on an object that already HAS vocabulary_, "
            "rebuild it with the same terms in the same ascending order but at "
            "doubled indices — "
            "'self.vocabulary_ = dict((t, 2 * k) for k, t in "
            "enumerate(self.get_feature_names_unsorted()))' before the return. "
            "get_feature_names still returns the identical list (index ORDER is "
            "unchanged), so the F2P's assert_array_equal passes — and the test's "
            "second loop, 'for idx, name in enumerate(feature_names): "
            "assert_equal(idx, cv.vocabulary_.get(name))' (test_text.py:571), "
            "FAILS with '1 != 2'. It does not resolve. This was measured in the "
            "instance image: the patch fails FAIL_TO_PASS 1/1 while the gold hunk "
            "passes on the same container."),
        "rationale": (
            "Rejected by the place-numbering half of the mapping: the returned "
            "names are untouched, so nothing about the name sequence can see this "
            "rival, and it is exactly the state the carrier could not express "
            "before `idx` was added. Now Ensures(numbered_by_place(self.idx, "
            "self.names)) fails (the indices are 0,2,4,… not 0,1,2,…) and so does "
            "(E5)'s ToSeq(self.idx) == Old(ToSeq(self.idx)). The head keeps a "
            "fully framed loop and asserts len(renum) == len(self.idx), so the "
            "length conjunct of numbered_by_place holds and the rejection is "
            "attributable to the NUMBERING alone."),
    },
    {
        "id": "already-fitted-mapping-numbered-from-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_FITTED_ONE_BASED),
        "refinement": (
            "Faithful real patch: the same rebuild as above but with 'k + 1' — a "
            "1-based vocabulary_. The reported names are byte-identical to the "
            "gold's; the F2P's index loop fails at its first iteration "
            "(assert_equal(0, cv.vocabulary_.get('beer')) sees 1). It does not "
            "resolve."),
        "rationale": (
            "Boundary token swap on the numbering base: the smallest renumbering "
            "there is, and the one an off-by-one in _sort_features / "
            "_limit_features would produce (text.py:749-751, 783-789 renumber to "
            "0..n-1 precisely). Rejected by the same clause as R17; kept as its "
            "own case because a spec could pin the SET of indices, or their "
            "spacing, while still admitting a shifted base."),
    },
    {
        "id": "materialised-mapping-numbered-from-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_SUPPLIED_RENUMBER),
        "refinement": (
            "Faithful real patch: the gold guard is inserted, but instead of "
            "delegating to _validate_vocabulary the query builds vocabulary_ "
            "itself as '{t: i + 1 for i, t in enumerate(self.vocabulary)}' (and "
            "sets fixed_vocabulary_ = True). This is the F2P custom-vocabulary "
            "path: get_feature_names returns exactly ['beer', ...] in the supplied "
            "order and assert_true(cv.fixed_vocabulary_) passes, but "
            "'assert_equal(idx, cv.vocabulary_.get(name))' FAILS. It does not "
            "resolve."),
        "rationale": (
            "The attack on the very path the gold patch adds, and the one no other "
            "clause can see: (E3) is fully satisfied (the object is fitted, "
            "recorded supplied-at-construction, and the returned names equal the "
            "supplied list in order), (E2) holds, both Exsures are untouched. Only "
            "Ensures(numbered_by_place(self.idx, self.names)) rejects it. This is "
            "the clause's load-bearing case: it is the state the F2P test's second "
            "assertion loop actually observes."),
    },
    {
        "id": "renumbers-only-large-mappings",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_RENUMBER_BIG_ONLY),
        "refinement": (
            "Faithful real patch: the doubling rebuild above, guarded by "
            "'if len(self.vocabulary_) > 2:'. On the F2P's nine-term vocabulary "
            "the guard fires and the index loop FAILS; on a one- or two-term "
            "example it does not. It does not resolve."),
        "rationale": (
            "Partial-domain guard: correct on exactly the small states a reader "
            "checks by hand, wrong on the rest. Nothing in the precondition bounds "
            "the size of a materialised mapping, so those states are IN the domain "
            "and the same place-numbering clause must reject it. Included because "
            "a spec repaired by narrowing a precondition (e.g. only claiming the "
            "numbering for short mappings) would admit this rival while still "
            "passing R17."),
    },
    {
        "id": "index-of-a-name-is-the-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_IDX_ECHO_NAMES),
        "refinement": (
            "Faithful real patch: rebuild vocabulary_ as '{t: hash-free term "
            "identity}' — concretely, on the already-fitted path, "
            "'self.vocabulary_ = {t: _TERM_ID[t] for t in names}', i.e. each term "
            "keeps the column it had in some OTHER vectoriser's vocabulary rather "
            "than its place in this one. For a fitted object whose mapping is a "
            "sub-range or a permutation of the term pool the F2P-style index loop "
            "FAILS. It does not resolve."),
        "rationale": (
            "Oracle echo: the answer is copied from the input (the names) instead "
            "of being the mapping's own numbering, so the rival is right exactly "
            "on the states where the two coincide — a mapping whose term ids are "
            "already 0,1,2,… in order, which includes the canonical F2P-shaped "
            "states built from ids 0..8. A battery that only ever exercised "
            "canonical term ids would not see it. Rejected because "
            "numbered_by_place pins the index at each place to that PLACE, not to "
            "the name sitting there."),
    },
    {
        "id": "every-name-addresses-column-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_HEAD_IDX_ALL_ZERO),
        "refinement": (
            "Faithful real patch: 'self.vocabulary_ = dict.fromkeys(names, 0)'. "
            "get_feature_names' own sort is stable, so the reported name list is "
            "unchanged and assert_array_equal still passes, while every "
            "cv.vocabulary_.get(name) is 0 — the F2P index loop FAILS at its "
            "second name. Downstream, every document term would be counted into "
            "column 0. It does not resolve."),
        "rationale": (
            "Over-approximation: the degenerate witness of 'the mapping has an "
            "index for each name' — one index per name, of the right length, with "
            "the values thrown away. It is what the spec would admit if the "
            "numbering half were stated as a shape (len(idx) == len(names)) "
            "instead of a value (ToSeq(idx) == places(len(names))). Rejected by "
            "the value form."),
    },
    {
        "id": "pos-control-numbering-rebuilt-equal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_HEAD_FITTED_REBUILD_IDX_EQUAL),
        "rationale": (
            "CORRECT but structurally different on the already-fitted path: the "
            "index half of the mapping is replaced by a freshly built list "
            "carrying the SAME numbering (place q ↦ q). numbered_by_place and the "
            "idx frame are stated on ToSeq values, not on object identity, so this "
            "MUST verify — the real query is free to rebuild the dict it reports "
            "from as long as the numbering it leaves behind is the same one. If "
            "this case could not verify, the repair would be pinning which list "
            "object holds the numbering (over-fitting) and the six reject cases "
            "above would be passing for the wrong reason."),
    },
    {
        "id": "pos-control-mapping-rebuilt-equal",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_HEAD_FITTED_REBUILD_EQUAL),
        "rationale": (
            "CORRECT but structurally different on the already-fitted path: the "
            "mapping view is replaced by a freshly built list carrying the SAME "
            "names in the SAME order, then reported. (E5) is stated on ToSeq "
            "values, not on object identity, so this MUST verify — the real query "
            "likewise re-derives its answer from the mapping on every call and is "
            "free to hand back a new list each time. If this case could not verify, "
            "(E5) would be pinning a representation detail the real function does "
            "not guarantee (over-fitting), and the sibling reject cases above would "
            "be passing for the wrong reason."),
    },
    {
        "id": "pos-control-flattened-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_HEAD_POS_FLAT),
        "rationale": (
            "Structurally different but CORRECT: the nested if/else guard is "
            "flattened into two sequential guards (materialise iff not-fitted & "
            "has_param; raise iff still not-fitted). After materialise, fitted is "
            "True so the raise guard is skipped — semantically the identical "
            "first-match cascade. The verbatim gold copy-loop tail keeps every "
            "framing assert / loop invariant (no loop reversal, no induction "
            "lemma), so it MUST verify. If it could not => SPEC-TOO-STRONG."),
    },
    {
        "id": "admissibility-f2p-custom-vocab",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_HEAD_ADMISS),
        "rationale": (
            "Builds a freshly-constructed F2P-shaped Vectoriser (UNFITTED, "
            "has_param=True, supplied=False, a non-empty supplied list, empty "
            "names) — the gold custom-vocabulary input — and asserts every Requires "
            "conjunct of get_feature_names for it, incl. the representation "
            "invariant Implies(fitted, usable_terms(names)) (vacuously true for "
            "an unfitted object). Note what is NOT asserted, because it is not "
            "required: nothing about the shape of the supplied list, and nothing "
            "relating the materialised mapping to the ctor list. If the precondition "
            "could not be established for this legitimate input => "
            "PRECOND-TOO-STRONG. Assert-style rather than a recursive self-call "
            "because get_feature_names carries MustTerminate(3) and Nagini demands "
            "a callee's level be strictly below the caller's; the constructor call "
            "is still a real call site, so __init__'s Requires are discharged for "
            "these arguments. The gold head + loop tail follow verbatim so the "
            "function's own postcondition is unchanged; editing only the impl "
            "region keeps same_spec true."),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# meta.axioms == [] — NO consumed @ContractOnly axiom. The single deep-model
# A-reference is materialise_from_param == VectorizerMixin._validate_vocabulary
# (list-vocabulary branch). It is validated == the real callee by axiom_check.py
# (G-AX). We re-run the REAL _validate_vocabulary in the instance image and assert:
#   (1) AXIOM-SOUNDNESS of the helper's three Ensures (self.fitted, self.supplied,
#       ToSeq(names)==ToSeq(param)) on the helper's whole domain — a USABLE list
#       vocabulary, non-empty with no term listed twice, incl. the exact F2P 9-term
#       list + order-sensitivity;
#   (2) CALLER-DOMAIN CONTAINMENT: the helper is invoked ONLY under self.has_param
#       AND usable_terms(self.param), so every callee-input the model can reach lies
#       inside _validate_vocabulary's accepted set. The probe shows the real routine
#       REJECTS everything outside it (a repeated term, or an empty list) and
#       rejects WITHOUT WRITING — so the caller's own UnusableTermsError exit, which
#       is where those inputs go, claims the right state. Note the caller does NOT
#       exclude them: an arbitrary ctor list is admissible and every list has a
#       modelled outcome;
#   (3) the RAISE-PATH side effect the Exsures pins: on a vocabulary-None object,
#       the real _validate_vocabulary records fixed_vocabulary_ == False (the
#       'not self.supplied' the spec requires) — confirming clause X is grounded
#       in real behaviour, not invented.
# The probe imports ONLY sklearn (the package under test), runs at base_commit,
# opens nothing on disk, and exits 0 iff every obligation holds.

_AX_PROBE = r'''
import sys

try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.exceptions import NotFittedError
except Exception as e:  # pragma: no cover
    print("IMPORT-FAIL:", repr(e))
    sys.exit(1)

from operator import itemgetter


def index_ordered_names(cv):
    """The (unchanged) get_feature_names body after the fitted check: the
    vocabulary_ terms in ascending index order."""
    return [t for t, i in sorted(cv.vocabulary_.items(), key=itemgetter(1))]


def check_helper_ensures(vocab):
    """A-reference / AXIOM-SOUNDNESS: the REAL _validate_vocabulary establishes
    the deep helper's three Ensures on a caller-reachable distinct-term list."""
    cv = CountVectorizer(vocabulary=list(vocab))
    # before: no materialised mapping (model: not self.fitted)
    if hasattr(cv, "vocabulary_"):
        print("FAIL: fresh vectoriser already has vocabulary_ for", vocab)
        sys.exit(1)
    # run the UNCHANGED materialise-from-supplied-list routine
    cv._validate_vocabulary()
    # Ensures self.fitted
    if not hasattr(cv, "vocabulary_"):
        print("FAIL: _validate_vocabulary did not materialise vocabulary_ for", vocab)
        sys.exit(1)
    # Ensures self.supplied
    if cv.fixed_vocabulary_ is not True:
        print("FAIL: fixed_vocabulary_ not True after materialise for", vocab)
        sys.exit(1)
    # Ensures ToSeq(self.names) == ToSeq(self.param)
    names = index_ordered_names(cv)
    if names != list(vocab):
        print("FAIL: index-ordered names", names, "!= supplied list", list(vocab))
        sys.exit(1)


def check_domain_rejected(vocab, label):
    """CONTAINMENT / domain honesty: a list OUTSIDE the helper's accepted domain
    (a term listed twice, or empty) is REJECTED by the real routine with
    ValueError, so the helper never claims to materialise it. The caller does not
    exclude such a list — it screens for it with usable_terms and models this very
    rejection as its own UnusableTermsError exit — so the rejection STATE is
    checked too: the routine raises before either of its assignments, leaving
    vocabulary_ absent and fixed_vocabulary_ at its entry value, which is exactly
    what that Exsures claims (not self.fitted, supplied unchanged)."""
    cv = CountVectorizer(vocabulary=vocab)
    sentinel = "<entry value>"
    cv.fixed_vocabulary_ = sentinel
    try:
        cv._validate_vocabulary()
    except ValueError:
        if hasattr(cv, "vocabulary_"):
            print("FAIL:", label, "rejected but vocabulary_ was materialised:", vocab)
            sys.exit(1)
        if cv.fixed_vocabulary_ is not sentinel:
            print("FAIL:", label, "rejected but fixed_vocabulary_ was overwritten:",
                  vocab, "->", cv.fixed_vocabulary_)
            sys.exit(1)
        return
    print("FAIL:", label, "vocabulary was NOT rejected:", vocab)
    sys.exit(1)


def check_raise_path_side_effect():
    """The Exsures pin 'not self.supplied': on a genuinely-unfitted object
    (vocabulary is None) the REAL _validate_vocabulary records
    fixed_vocabulary_ == False and sets NO vocabulary_, so the subsequent
    unusable check still raises. This grounds clause X in real behaviour."""
    cv = CountVectorizer()  # vocabulary is None
    if hasattr(cv, "vocabulary_"):
        print("FAIL: vocab=None object unexpectedly has vocabulary_")
        sys.exit(1)
    cv._validate_vocabulary()  # no-op materialisation
    if getattr(cv, "fixed_vocabulary_", None) is not False:
        print("FAIL: vocab=None object did not record fixed_vocabulary_ == False;",
              "got", getattr(cv, "fixed_vocabulary_", "<unset>"))
        sys.exit(1)
    if hasattr(cv, "vocabulary_"):
        print("FAIL: vocab=None object built a vocabulary_ (should stay unfitted)")
        sys.exit(1)
    # the unusable check still raises on this object
    raised = False
    try:
        cv._check_vocabulary()
    except NotFittedError:
        raised = True
    if not raised:
        print("FAIL: genuinely-unfitted object did not raise after _validate_vocabulary")
        sys.exit(1)


def check_differential_witness(vocab):
    """The change is observable: a supplied-list object raises on the PRE-PATCH
    path (straight to _check_vocabulary) and succeeds on the POST-PATCH path."""
    cv = CountVectorizer(vocabulary=list(vocab))
    raised = False
    try:
        cv._check_vocabulary()  # pre-patch: no on-demand materialise
    except NotFittedError:
        raised = True
    if not raised:
        print("FAIL: pre-patch path did NOT raise on a supplied-vocabulary object")
        sys.exit(1)
    cv2 = CountVectorizer(vocabulary=list(vocab))
    if not hasattr(cv2, "vocabulary_"):
        cv2._validate_vocabulary()  # post-patch: materialise on demand
    cv2._check_vocabulary()
    if index_ordered_names(cv2) != list(vocab):
        print("FAIL: post-patch path did not return the supplied list in order")
        sys.exit(1)
    if cv2.fixed_vocabulary_ is not True:
        print("FAIL: post-patch path did not set fixed_vocabulary_ True")
        sys.exit(1)


def main():
    # caller-reachable distinct-term list vocabularies (the F2P 9-term list +
    # order-sensitivity + size variety)
    vocabs = [
        ["beer", "burger", "celeri", "coke", "pizza",
         "salad", "sparkling", "tomato", "water"],   # the exact F2P list
        ["a"],
        ["z", "y", "x", "w"],                          # reverse order
        ["and", "document", "first", "is", "one",
         "second", "the", "third", "this"],
        [str(i) for i in range(50)],                   # larger
    ]
    for vocab in vocabs:
        check_helper_ensures(vocab)
        check_differential_witness(vocab)

    # domain honesty / containment: out-of-domain lists are rejected, not claimed,
    # and the rejection writes nothing (the caller's rejection-exit state)
    check_domain_rejected(["pizza", "beer", "pizza"], "duplicate-term")
    check_domain_rejected(["x", "x"], "duplicate-term")
    check_domain_rejected(["a", "b", "c", "b"], "duplicate-term")
    check_domain_rejected([], "empty")

    # the raise-path side effect the Exsures pins
    check_raise_path_side_effect()

    print("AX OK: deep helper materialise_from_param == real _validate_vocabulary "
          "on its whole domain -- every usable supplied list (non-empty, no term "
          "listed twice) yields fitted, supplied, index-ordered names == the "
          "supplied list; every unusable one is rejected AND leaves the object "
          "untouched (containment, and the caller's rejection-exit state); "
          "vocab=None records fixed_vocabulary_==False before the raise (the "
          "Exsures 'not self.supplied' pin); differential witness confirmed.")
    sys.exit(0)


main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-validate-vocabulary",
        "axiom": "materialise_from_param",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "Runs the REAL VectorizerMixin._validate_vocabulary (the UNCHANGED "
            "callee the gold patch newly invokes) on real CountVectorizer objects "
            "and asserts the deep helper's three Ensures (self.fitted, "
            "self.supplied, ToSeq(names)==ToSeq(param)) on the helper's whole "
            "domain — every usable list vocabulary, non-empty with no term listed "
            "twice, incl. the exact F2P 9-term list. If the "
            "real callee disagreed => AXIOM-UNSOUND. It also confirms the "
            "raise-path side effect the Exsures pins (vocab=None records "
            "fixed_vocabulary_==False) and the differential witness."),
    },
    {
        "id": "ax-contain-validate-vocabulary-domain",
        "axiom": "materialise_from_param",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": (
            "CALLER-DOMAIN CONTAINMENT: the helper is invoked ONLY under "
            "self.has_param AND usable_terms(self.param) — the caller screens the "
            "ctor list before invoking the step — so every callee-input the model "
            "can reach lies inside _validate_vocabulary's accepted domain. The "
            "probe shows the real routine REJECTS everything outside it (a repeated "
            "term, or an empty list) with ValueError and rejects WITHOUT WRITING, "
            "which is precisely the state the caller's own UnusableTermsError exit "
            "claims for those inputs — they are admissible at the top level and "
            "routed there, not excluded. A reachable input outside the domain would "
            "be AXIOM-TOO-WEAK-FOR-CALLER; the screen makes sure none exists."),
    },
]
