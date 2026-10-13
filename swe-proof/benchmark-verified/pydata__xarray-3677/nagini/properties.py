# properties.py — PBT falsification battery for pydata__xarray-3677. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside a # impl-start/# impl-end region; the runner re-runs the Nagini verifier
# on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   merge_method(receiver: Operand, other: Operand) -> List[Operand]
#     Requires(Acc(receiver.*, 1/2))                                 # READ-ONLY (4 fields)
#     Requires(Acc(other.*, 1/2))                                    # READ-ONLY (4 fields)
#     Requires(receiver.is_mapping)                                  # receiver already mapping-shaped
#     Requires(Implies(is_array_shaped(other), other.name >= 0))     # named single value
#     # NO distinctness Requires: supplying the SAME mapping-shaped operand as
#     # both operands is a real call shape, so it is INSIDE the specified domain
#     # (admiss-same-object-input witnesses that, and the reject cases below pin
#     # what must happen on it).
#     # postconditions (the load-bearing clauses):
#     Ensures(len(Result()) == 2)                                    # (P1) exactly two operands
#     Ensures(Result()[0] is receiver)                               # (P2) receiver passes through (same obj)
#     Ensures(Acc(Result()[0].is_mapping,1/4) and Result()[0].is_mapping)  # (P3a) op0 mapping-shaped
#     Ensures(Acc(Result()[1].is_mapping,1/4) and Result()[1].is_mapping)  # (P3b) op1 mapping-shaped
#     Ensures(Result()[1].name == other.name and Result()[1].value == other.value)  # (P4) name/value preserved
#     Ensures(other.is_mapping == Old(other.is_mapping))                            # (P4b) NEITHER operand is
#     Ensures(other.name == Old(other.name) and other.value == Old(other.value))    #       altered: each still
#     Ensures(other.name_is_own_label == Old(other.name_is_own_label))              #       carries its own entry
#     Ensures(Implies(not Old(is_array_shaped(other)), Result()[1] is other))        # (P5) identity on no-op branch
#     Ensures(Implies(is_array_shaped(other), not other.name_is_own_label))          # (P6) returns only where defined
#     Exsures(NormalisationUndefined, ... not other.is_mapping and other.name_is_own_label
#             and <all 4 fields of other> == Old(...))               # (P7) signalled exactly
#                                                                    #      there, operands
#                                                                    #      equally untouched
#
#   as_mapping(o) is a DEEP MODEL (A-reference, NOT a consumed @ContractOnly
#   axiom) of the unchanged conversion callee DataArray.to_dataset(); it is an
#   ordinary verified function that either returns a fresh mapping-shaped Operand
#   with the same name/value, or signals NormalisationUndefined on exactly the
#   array-shaped operands whose entry name is also the name of one of their own
#   label entries (o.name_is_own_label) -- for which no one-entry mapping-shaped
#   form exists. It takes and returns only Acc(o.*, 1/4), so a caller holding a
#   1/2 share still retains 1/4 across the call and can frame the operand's
#   fields over it (which is what lets (P4b) be discharged on the array branch).
#   is_array_shaped(o) == not o.is_mapping is a @Pure helper.
#
# Read-only inputs: BOTH receiver and other are held at Acc(...,1/2) (and only
# 1/4 is returned). So FRAME-MUTATION is MANDATORY (directive 5): an impl that
# WRITES any field of receiver/other must reject for INSUFFICIENT PERMISSION.
# With ONE call shape excepted, and it is the one the domain now admits: when the
# SAME operand is supplied as both operands, the two 1/2 shares SUM to a whole,
# so permission alone no longer forbids a write there. (P4b) is what forbids it.
# The aliased frame attacks (alias-frame-write-value / alias-frame-write-flag)
# below target exactly that shape; a verify there would mean the operands are not
# pinned to the entries they arrived with.
#
# Ungrounded-oracle (directive 2): the postcondition is GROUNDED in the inputs —
# it pins object identity (P2, P5), the mapping-shaped flag (P3), and name/value
# equality to other's own fields (P4). There is NO opaque @Pure answer-key to
# echo: as_mapping is a deep model (an ordinary fn whose Ensures are themselves
# input-grounded: Result().name == o.name etc.), not an answer key. So there is
# no "wrong echo that still verifies"; the honest substitute is the cheapest
# correct positive control (pos-control-ifelse) — see `assessment`.
#
# Control-flow-effect (directive 4): PRESENT and defended. The normalisation of
# an array-shaped operand is a PARTIAL operation: it is undefined when the
# operand's single entry name is also the name of one of its own label entries
# (o.name_is_own_label), and on that class the whole combination produces NO
# operand sequence and signals NormalisationUndefined instead. So the function
# has TWO outcomes in-domain, and the return channel alone does not pin the
# behaviour. Both directions are attacked below: cfe-swallow-undefined /
# cfe-launder-collision (return where the real operation is undefined) and
# cfe-raise-always / cfe-raise-on-array (signal where it is defined). The
# admiss-collision-input case pins that the collision class is IN-domain.
# alias-raise-on-name-clash attacks the same channel on the aliased call shape:
# refusing to produce a sequence for an operand pair that shares an entry name is
# an outcome the specified behaviour does not have (whether the core can go on to
# combine what it is handed is downstream of this operation).
from pathlib import Path

INSTANCE = "pydata__xarray-3677"
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
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec. Two of them: the
# combination itself (_IMPL_OLD) and the partial normalisation (_IMPL_AS_MAPPING),
# whose two outcomes the control-flow-effect lane attacks.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1

_IMPL_AS_MAPPING = """    # impl-start
    if o.name_is_own_label:
        raise NormalisationUndefined()
    res = Operand(True, o.name, o.value, False)
    return res
    # impl-end"""

assert _IMPL_AS_MAPPING in _BASE and _BASE.count(_IMPL_AS_MAPPING) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). All keep the exact gold dataflow that the
# proof needs: the second operand is either `other` itself (no-op branch, so P5
# identity holds) or `as_mapping(other)` (array branch, so P3b/P4 hold).
# ===========================================================================

# pos-control-ifelse: replace the `second = other; if ...: second = ...` mutate
# pattern with a single if/else that binds `second` exactly once per path. The
# array-shaped path binds as_mapping(other); the else path binds `other` itself
# (the SAME object — so P5 still holds). Behaviourally identical; no loop/fold,
# no new lemma (pilot pitfalls #2/#3 avoided). The cheapest honest correct impl.
_POS_IFELSE = """    # impl-start
    if is_array_shaped(other):
        second = as_mapping(other)  # type: Operand
    else:
        second = other
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# pos-control-listfirst: build the list with the receiver first, then assign the
# second element in place (different local/data shape: construct a one-element
# list then append). Keeps the same `second` selection. A list-append reshape
# that does not need any fold lemma (the postcondition reasons about Result()[0]
# / Result()[1] positionally, which `[receiver]` + append still establishes).
_POS_LISTFIRST = """    # impl-start
    second = other  # type: Operand
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver]  # type: List[Operand]
    result.append(second)
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We CANNOT add a module-level caller (it would
# change the spec view and break same_spec). Instead we inject the admissibility
# witness INSIDE the impl region (elided from the spec view): construct the exact
# F2P shapes — a mapping-shaped receiver (Dataset {"a":0}) and an array-shaped
# named second operand (DataArray name="b", data=1) — and Assert the function's
# Requires holds for them (read-perms from the constructor Ensures; receiver
# mapping-shaped; the named-array implication). The real impl then runs unchanged
# over the actual params. If a legitimate input could not establish the Requires
# the Assert fails => PRECOND-TOO-STRONG. Three witnesses: the F2P shape, the
# undefined-normalisation class, and the SAME-OBJECT pair (a P2P call shape).
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for the F2P input (elided from spec view) ---
    # receiver: a mapping-shaped operand (the F2P Dataset {"a": 0})
    adm_recv = Operand(True, 0, 0, False)
    # other: an array-shaped NAMED operand (the F2P DataArray name="b", data=1)
    adm_other = Operand(False, 1, 1, False)
    # the function's Requires is establishable for these concrete F2P operands:
    Assert(Acc(adm_recv.is_mapping, 1 / 2) and Acc(adm_recv.name, 1 / 2) and Acc(adm_recv.value, 1 / 2) and Acc(adm_recv.name_is_own_label, 1 / 2))
    Assert(Acc(adm_other.is_mapping, 1 / 2) and Acc(adm_other.name, 1 / 2) and Acc(adm_other.value, 1 / 2) and Acc(adm_other.name_is_own_label, 1 / 2))
    Assert(adm_recv.is_mapping)
    Assert(Implies(is_array_shaped(adm_other), adm_other.name >= 0))
    # --- end admissibility witness; the real impl follows unchanged ---
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# admiss-collision-input: the SECOND admissibility witness, for the operand class
# on which the normalisation is UNDEFINED — an array-shaped NAMED operand whose
# entry name is also one of its own axis-label names (name_is_own_label). This
# class is IN the precondition's domain (it satisfies every Requires, including
# the named-single-value clause), so the spec must have something to say about it
# rather than exclude it. Asserting the Requires holds for it pins that the
# domain was NOT narrowed to dodge the partial-normalisation case.
_ADMISS_COLLISION = """    # impl-start
    # --- admissibility witness: the undefined-normalisation class is IN domain ---
    adm_recv = Operand(True, 0, 0, False)
    # an array-shaped NAMED operand whose name is ALSO one of its own axis labels
    adm_other = Operand(False, 1, 1, True)
    Assert(Acc(adm_recv.is_mapping, 1 / 2) and Acc(adm_recv.name, 1 / 2) and Acc(adm_recv.value, 1 / 2) and Acc(adm_recv.name_is_own_label, 1 / 2))
    Assert(Acc(adm_other.is_mapping, 1 / 2) and Acc(adm_other.name, 1 / 2) and Acc(adm_other.value, 1 / 2) and Acc(adm_other.name_is_own_label, 1 / 2))
    Assert(adm_recv.is_mapping)
    Assert(Implies(is_array_shaped(adm_other), adm_other.name >= 0))
    # it really is the undefined-normalisation class, and it really is admissible
    Assert(is_array_shaped(adm_other) and adm_other.name_is_own_label)
    # --- end admissibility witness; the real impl follows unchanged ---
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# admiss-same-object-input: the THIRD admissibility witness, for the SAME-OBJECT
# call shape — ONE mapping-shaped operand supplied as BOTH the receiver and the
# second operand (combining a collection with itself). This is a real call shape
# the graded behaviour includes, so the specification must SAY what happens on it
# rather than exclude it: excluding it would let any behaviour whatsoever verify
# there. The witness constructs one operand and asserts the function's Requires is
# establishable for the pair (operand, operand): the aliased call needs TWO 1/2
# read shares of each field, which together are exactly the whole permission the
# constructor hands back, plus receiver.is_mapping and the named-array implication
# (trivial for a mapping-shaped operand). If this Assert failed, the domain had
# been narrowed to dodge the aliased case => PRECOND-TOO-STRONG.
_ADMISS_ALIASED = """    # impl-start
    # --- admissibility witness: the SAME-OBJECT pair is IN domain ---
    adm_both = Operand(True, 0, 0, False)
    # the aliased call passes 1/2 of each field TWICE; the two shares sum to the
    # whole permission the constructor returned, so the Requires is establishable
    Assert(Acc(adm_both.is_mapping, 1 / 2) and Acc(adm_both.is_mapping, 1 / 2))
    Assert(Acc(adm_both.name, 1 / 2) and Acc(adm_both.name, 1 / 2))
    Assert(Acc(adm_both.value, 1 / 2) and Acc(adm_both.value, 1 / 2))
    Assert(Acc(adm_both.name_is_own_label, 1 / 2) and Acc(adm_both.name_is_own_label, 1 / 2))
    # ... and the value part of the Requires holds of that same single operand in
    # BOTH argument positions
    Assert(adm_both.is_mapping)
    Assert(Implies(is_array_shaped(adm_both), adm_both.name >= 0))
    # --- end admissibility witness; the real impl follows unchanged ---
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""


# ===========================================================================
# UNIQUENESS / partial-domain / frame-mutation — rivals that share the spec
# exactly and change ONLY the impl. Each MUST be rejected; a verifying rival is a
# real verify-but-not-resolve break (SPEC-TOO-WEAK or, for frame-mutation, the
# permission system failing). Each carries the refinement argument that its
# faithful real patch would NOT resolve the F2P/P2P.
# ===========================================================================

# uniq-drop-conversion: THE BUG. Never convert — pass the array-shaped second
# operand straight through (`second = other` always). This is exactly the
# pre-patch behaviour model_prepatch.py reproduces and G-DIFF flags. On an
# array-shaped `other` the second result operand is NOT mapping-shaped, so the
# core would hit `obj.items()` on a DataArray. Rejected by P3b
# (Result()[1].is_mapping).
_UNIQ_DROP_CONVERSION = """    # impl-start
    second = other  # type: Operand
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-rebuild-noop: the LOSSY-REBUILD cheat (the G-MUT mutant the refinement
# added P5 to kill). Always rebuild a FRESH single-entry mapping-shaped operand
# from other's name/value, on BOTH branches. P3b and P4 (name/value) hold, but on
# the already-mapping-shaped branch Result()[1] is a NEW object, not `other`, so
# P5 (Result()[1] is other) fails. Under the bijection (one carrier abstracts a
# multi-variable Dataset) this drops every variable of a multi-variable Dataset
# beyond the first. Rejected by P5.
_UNIQ_REBUILD_NOOP = """    # impl-start
    second = Operand(True, other.name, other.value, other.name_is_own_label)  # type: Operand
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""


# ===========================================================================
# CONTROL-FLOW-EFFECT (directive 4) — the normalisation is PARTIAL, so the spec
# pins BOTH outcomes: it returns a sequence exactly on the operands whose
# normalisation is defined (P6) and signals NormalisationUndefined exactly on the
# ones where it is not (P7). Both directions of getting that wrong are attacked.
# The first two edit as_mapping's impl region, the last two merge_method's.
# ===========================================================================

# cfe-swallow-undefined: DROP the undefinedness — always return a one-entry
# mapping-shaped operand, even for an operand whose entry name is also one of its
# own axis-label names. This is the over-claimed no-raise implementation: it
# invents a one-entry form where none exists. Its faithful real patch would have
# to make the conversion return a Dataset holding two different things under one
# name; the real conversion instead reports the conflict, and a wrapper that
# swallowed it would hand the core a silently-wrong operand.
_CFE_SWALLOW = """    # impl-start
    res = Operand(True, o.name, o.value, False)
    return res
    # impl-end"""

# cfe-launder-collision: return an operand but COPY the collision flag onto the
# product, pretending a one-entry form exists while marking it as still colliding.
# A near-miss of cfe-swallow-undefined that also violates the product's own
# non-collision guarantee. Its faithful patch produces an operand the core would
# then iterate as if well-formed.
_CFE_LAUNDER = """    # impl-start
    res = Operand(True, o.name, o.value, o.name_is_own_label)
    return res
    # impl-end"""

# cfe-raise-always: signal undefinedness UNCONDITIONALLY — never produce an
# operand at all. The mirror-image over-claim: it refuses the whole class,
# including the F2P input (a named array with NO axis-label collision), which the
# real conversion converts happily. Its faithful patch would make ds.merge(da)
# fail for every DataArray, so test_merge_dataarray would not resolve.
_CFE_RAISE_ALWAYS = """    # impl-start
    raise NormalisationUndefined()
    # impl-end"""

# cfe-raise-on-array: signal undefinedness for EVERY array-shaped second operand
# (rather than only the collision class) and pass a mapping-shaped one straight
# through. Refuses exactly the inputs the fix exists to support: the F2P's named
# array-shaped operand raises instead of being combined. Does NOT resolve.
_CFE_RAISE_ON_ARRAY = """    # impl-start
    if is_array_shaped(other):
        raise NormalisationUndefined()
    result = [receiver, other]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-swap-order: put the normalized second operand FIRST and the receiver
# second. P1 (len 2), P3 (both mapping-shaped on the array branch), P4 fail/shift,
# but most directly P2 (Result()[0] is receiver) is violated. A faithful patch
# that built objs = [other, dataset] would merge in the wrong precedence order
# (the receiver's variables would be overwritten by other on conflict, reversing
# the documented merge semantics) and fail test_merge_dataarray / test_merge.
# Rejected by P2.
_UNIQ_SWAP_ORDER = """    # impl-start
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [second, receiver]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-frame-mutation (MANDATORY — read-only inputs at Acc(...,1/2)): instead of
# converting, OVERWRITE the read-only input `other.is_mapping = True` so the
# pass-through trivially looks mapping-shaped, then return [receiver, other].
# This is the canonical frame attack: satisfy P3b by mutating the input rather
# than producing a converted operand. merge_method holds only Acc(other.is_mapping,
# 1/2); a WRITE needs FULL permission, so this MUST reject for INSUFFICIENT
# PERMISSION. Gold invariants are kept verbatim so the rejection is attributable
# to the write. Its faithful real patch would mutate the caller's DataArray in
# place (set an attribute on the user's object) — a destructive side effect the
# real Dataset.merge must never do; assert_identical(ds.merge(da), xr.merge([ds,
# da])) and the surrounding P2P tests reuse `da` afterward, so a mutated input
# fails the F2P/P2P. (verify here would mean the permission frame is broken.)
_UNIQ_FRAME_MUTATION = """    # impl-start
    other.is_mapping = True
    second = other  # type: Operand
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-frame-mutation-recv: a second frame attack on the OTHER read-only input.
# Overwrite receiver.value (held at Acc(receiver.value, 1/2)) before returning.
# The value abstraction would be unaffected by the postcondition (P2 pins only
# identity, not receiver.value), so ONLY the permission system can reject this.
# A write needs full permission; only 1/2 is held => INSUFFICIENT PERMISSION.
# Its faithful patch would clobber a field of the receiver Dataset in place,
# corrupting `self` for any later use — failing the round-trip P2P tests.
_UNIQ_FRAME_MUTATION_RECV = """    # impl-start
    receiver.value = 0
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# alias-frame-write-value: the frame attack the PERMISSION SYSTEM CANNOT CATCH.
# Write other.value, but ONLY on the same-object call shape. There the two 1/2
# read shares of the aliased operand sum to a whole, so the write is
# permission-legal; and the clobbered value is invisible to (P4) (which relates
# Result()[1].value to other.value -- both are the clobbered field) and to
# (P2)/(P5) (identity only). So ONLY (P4b), pinning each operand to the entry it
# arrived with, rejects this. Everything else is gold, verbatim.
_ALIAS_WRITE_VALUE = """    # impl-start
    if receiver is other:
        other.value = 0
    second = other  # type: Operand
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# alias-frame-write-flag: the same aliased frame attack on the OTHER unpinned
# field -- overwrite other.name_is_own_label. On the same-object shape the operand
# is mapping-shaped (the receiver is), so the normalisation is never invoked and
# the flag is read by nothing: (P6) is vacuous on this branch and (P7) is not
# taken. Permission-legal for the same aliasing reason. Only (P4b) rejects it.
_ALIAS_WRITE_FLAG = """    # impl-start
    if receiver is other:
        other.name_is_own_label = False
    second = other  # type: Operand
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# alias-flip-then-raise: edit an operand INTO the shape that makes the signal look
# justified, then signal. On the same-object shape the write is permission-legal
# (the two 1/2 shares sum to a whole) and the post-state satisfies the signalling
# condition (not other.is_mapping and other.name_is_own_label) because the impl
# just established it. Only the Old(...) conjuncts of (P7) -- the preservation on
# the EXCEPTIONAL outcome -- reject it. Measured: with (P7) pinning name/value
# alone this impl VERIFIED, which is why the exceptional path pins all four fields.
_ALIAS_FLIP_THEN_RAISE = """    # impl-start
    if receiver is other and other.name_is_own_label:
        other.is_mapping = False
        raise NormalisationUndefined()
    second = other  # type: Operand
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# alias-raise-on-name-clash: refuse to produce a sequence when the two operands
# carry the same entry name -- which is always true of the same-object pair. The
# control-flow-effect attack on the newly-admitted call shape: the right value on
# most inputs, a wholly absent value on that one, and a signal the specified
# behaviour does not have there.
_ALIAS_RAISE_NAME_CLASH = """    # impl-start
    if receiver.name == other.name:
        raise NormalisationUndefined()
    second = other  # type: Operand
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-drop-second (partial-domain / list-shape): return ONLY the receiver (a
# one-element list). P2/P3a hold but P1 (len == 2) fails. A faithful patch that
# handed the core a single-operand list would never merge in `other` at all —
# test_merge_dataarray asserts the merged Dataset contains BOTH a and b; with
# `other` dropped it would be missing b and not resolve. Rejected by P1.
_UNIQ_DROP_SECOND = """    # impl-start
    result = [receiver]  # type: List[Operand]
    return result
    # impl-end"""

# uniq-pad-list (partial-domain / list-shape, supporting): return a three-element
# list [receiver, second, second]. P1 (len == 2) fails. Cheap supporting near-miss
# for the list-length pin; a faithful patch passing a padded operand list would
# merge `other` twice (a duplicate-operand conflict) and not resolve. Rejected by P1.
_UNIQ_PAD_LIST = """    # impl-start
    second = other
    if is_array_shaped(other):
        second = as_mapping(other)
    result = [receiver, second, second]  # type: List[Operand]
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-ifelse",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_IFELSE),
        "rationale": "structurally-different CORRECT impl: a single if/else binds "
                     "`second` exactly once per path (as_mapping(other) on the array "
                     "branch, `other` itself on the no-op branch) instead of the gold "
                     "mutate-then-maybe-reassign. Behaviourally identical: on the "
                     "no-op branch Result()[1] is still `other` (P5 holds), on the "
                     "array branch as_mapping gives a mapping-shaped operand with the "
                     "same name/value (P3b/P4). No loop/fold so no new lemma needed. "
                     "If a faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-listfirst",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_LISTFIRST),
        "rationale": "local-variable/data-shape reshape: build [receiver] then append "
                     "the selected second operand, instead of a 2-element literal. The "
                     "postcondition reasons positionally about Result()[0]/Result()[1], "
                     "which [receiver] + append establishes without any fold lemma. "
                     "Same `second` selection, so P3b/P4/P5 hold. If it cannot verify "
                     "=> SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) constructs the exact F2P "
                     "shapes — a mapping-shaped receiver Operand(True,0,0) (Dataset "
                     "{'a':0}) and an array-shaped named second operand "
                     "Operand(False,1,1) (DataArray name='b', data=1) — and asserts "
                     "the function's full Requires holds for them: the 1/2-read perms "
                     "(from the constructor Ensures), receiver.is_mapping, and the "
                     "named-array implication. The real impl "
                     "then runs unchanged. If the precondition could not be established "
                     "for this legitimate F2P input the Assert fails => PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-collision-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS_COLLISION),
        "rationale": "the SECOND admissibility witness, for the class on which the "
                     "normalisation is UNDEFINED: an array-shaped NAMED operand whose "
                     "entry name is also one of its own axis-label names "
                     "(Operand(False,1,1,True) — e.g. a named array carrying an "
                     "axis-label of the same name). It satisfies every Requires, "
                     "including the named-single-value clause, so it is IN the "
                     "specified domain and the spec must SAY what happens on it (it "
                     "signals NormalisationUndefined, P7) rather than exclude it. If "
                     "this Assert failed, the domain had been narrowed to dodge the "
                     "partial-normalisation case => PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-same-object-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS_ALIASED),
        "rationale": "the THIRD admissibility witness, for the SAME-OBJECT call shape: "
                     "ONE mapping-shaped operand supplied as BOTH the receiver and the "
                     "second operand (combining a collection with itself, "
                     "xarray/tests/test_merge.py:148 `data.merge(data)`, which is in the "
                     "graded P2P set). The witness constructs a single Operand and "
                     "asserts the whole Requires is establishable for the pair "
                     "(operand, operand): the aliased call needs 1/2 of each field "
                     "TWICE, and the additive conjunction Acc(f,1/2) and Acc(f,1/2) "
                     "asserts exactly that the whole permission is available, plus "
                     "receiver.is_mapping and the named-array implication. If this "
                     "Assert failed, the aliased shape would be OUT of domain and any "
                     "behaviour at all would verify there (vacuously) => "
                     "PRECOND-TOO-STRONG. This is the pin that keeps the three "
                     "alias-* reject cases below non-vacuous.",
    },

    # ---- uniqueness (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-drop-conversion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_CONVERSION),
        "refinement": "this IS the pre-patch behaviour model_prepatch.py reproduces "
                      "and G-DIFF flags: `other` is passed to dataset_merge_method "
                      "unconverted. The sole F2P test_merge_dataarray does "
                      "ds.merge(da) with da a DataArray; with the to_dataset() "
                      "conversion absent, merge_core hits `for k,v in obj.items()` on a "
                      "DataArray and raises AttributeError: 'DataArray' object has no "
                      "attribute 'items' — exactly the gold traceback. Its faithful "
                      "real patch (the un-patched merge) is precisely what does NOT "
                      "resolve.",
        "rationale": "rejected by P3b Ensures(Acc(Result()[1].is_mapping,1/4) and "
                     "Result()[1].is_mapping): on an array-shaped `other` "
                     "(is_array_shaped true) the second result operand is `other` "
                     "itself with is_mapping == False, so the verifier cannot discharge "
                     "Result()[1].is_mapping.",
    },
    {
        "id": "uniq-rebuild-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_REBUILD_NOOP),
        "refinement": "the lossy-rebuild cheat the refinement added P5 to kill: always "
                      "rebuild a FRESH one-entry mapping-shaped operand from other's "
                      "(name,value). Under the bijection (one Operand carrier abstracts "
                      "an N-variable Dataset to its first (name,value) pair) the "
                      "faithful patch — `other = Dataset({other.name: other.value})` on "
                      "the already-Dataset branch — drops every variable of a multi-"
                      "variable Dataset beyond the first. The P2P tests test_merge / "
                      "test_merge_compat merge a multi-variable create_test_data "
                      "Dataset; the rebuild keeps only its first variable and they fail "
                      "assert_identical. Does NOT resolve.",
        "rationale": "rejected by P5 Ensures(Implies(not Old(is_array_shaped(other)), "
                     "Result()[1] is other)): on the already-mapping-shaped branch the "
                     "result operand is a freshly-constructed Operand, NOT the same "
                     "object as `other`; object identity is unforgeable so the verifier "
                     "cannot discharge Result()[1] is other.",
    },
    {
        "id": "uniq-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SWAP_ORDER),
        "refinement": "building [second, receiver] instead of [receiver, second] "
                      "corresponds to objs = [other, dataset] handed to the core merge. "
                      "merge precedence is order-dependent: the FIRST operand's "
                      "variables win on conflict. Reversing the order makes `other` "
                      "override the receiver's variables, reversing the documented "
                      "ds.merge(da) semantics; test_merge_dataarray's assert_identical "
                      "against xr.merge([ds, da]) (receiver-first) would fail. Does NOT "
                      "resolve.",
        "rationale": "rejected by P2 Ensures(Result()[0] is receiver): with the "
                     "operands swapped, Result()[0] is `second` (the normalized other), "
                     "not the receiver object; the verifier cannot discharge "
                     "Result()[0] is receiver.",
    },
    {
        "id": "uniq-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_MUTATION),
        "refinement": "FRAME-MUTATION (mandatory; `other` is read-only at Acc(other.*, "
                      "1/2)): rather than convert, overwrite other.is_mapping = True so "
                      "the unconverted pass-through trivially looks mapping-shaped. The "
                      "faithful real patch would mutate the caller's DataArray in place "
                      "(monkey-patching an attribute onto the user's object) — a "
                      "destructive side effect Dataset.merge must never have. "
                      "test_merge_dataarray reuses `da` in xr.merge([ds, da]) on the "
                      "same line, and the P2P suite reuses its operands; an in-place "
                      "mutation of the input would corrupt those and not resolve. A "
                      "verify here would mean the permission frame is broken.",
        "rationale": "rejected by the PERMISSION SYSTEM: merge_method holds only "
                     "Acc(other.is_mapping, 1/2); the assignment other.is_mapping = "
                     "True requires FULL (write) permission, so the verifier reports "
                     "INSUFFICIENT PERMISSION at the write. Gold invariants are kept "
                     "verbatim so the rejection is attributable to the write, not a "
                     "postcondition.",
    },
    {
        "id": "uniq-frame-mutation-recv",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FRAME_MUTATION_RECV),
        "refinement": "second FRAME attack on the other read-only input: overwrite "
                      "receiver.value (held at Acc(receiver.value, 1/2)) before "
                      "returning the otherwise-gold result. The value abstraction is "
                      "invisible to P2 (which pins only receiver identity), so ONLY the "
                      "permission system can catch it. A faithful patch clobbering a "
                      "field of `self` (the receiver Dataset) in place would corrupt the "
                      "receiver for later use; the round-trip P2P tests that reuse the "
                      "receiver Dataset would fail. Does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(receiver.value, 1/2) "
                     "is held; the write receiver.value = 0 needs FULL permission, so "
                     "the verifier reports INSUFFICIENT PERMISSION at the assignment.",
    },
    {
        "id": "alias-frame-write-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _ALIAS_WRITE_VALUE),
        "refinement": "the frame attack the PERMISSION SYSTEM CANNOT CATCH, and the "
                      "reason (P4b) has to exist. It clobbers other.value ONLY on the "
                      "same-object call shape, where the two 1/2 read shares of the one "
                      "aliased operand SUM to a whole -- so the write is "
                      "permission-legal, unlike uniq-frame-mutation. Its faithful real "
                      "patch alters the caller's own collection in place while combining "
                      "it with itself. The real behaviour alters neither operand: the "
                      "normalisation builds a FRESH product from copied entries "
                      "(xarray/core/dataarray.py:479-487) and the core routine only "
                      "READS the pair it is handed (xarray/core/merge.py:818), which is "
                      "why the method has no in-place form at all (the removed one is "
                      "still refused at xarray/core/dataset.py:3606). Whether one of the "
                      "21 graded P2P assertions happens to observe a particular "
                      "clobbered field is not the point of the case: the point is that "
                      "on this newly-admitted shape NOTHING but (P4b) stands between the "
                      "spec and an operand-mutating implementation.",
        "rationale": "rejected by (P4b) Ensures(other.value == Old(other.value)): the "
                      "clobbered field is invisible to (P4) (which relates "
                      "Result()[1].value to other.value -- after the write both are the "
                      "clobbered field) and to (P2)/(P5) (identity only), and the "
                      "permission system cannot reject the write because the aliased "
                      "shares sum to 1. Only the Old(...) preservation clause rejects it.",
    },
    {
        "id": "alias-frame-write-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _ALIAS_WRITE_FLAG),
        "refinement": "the same aliased frame attack on the other unpinned field: "
                      "overwrite other.name_is_own_label. On the same-object shape the "
                      "operand is mapping-shaped (the receiver is, by precondition), so "
                      "the normalisation is never invoked and the flag is read by "
                      "nothing on that path -- (P6) is vacuous there and (P7) is not "
                      "taken. Its faithful patch reaches into the caller's collection "
                      "and rewrites the label bookkeeping the conversion later consults; "
                      "the real behaviour rewrites nothing on either operand. Permission "
                      "cannot reject it (aliased shares sum to 1), so a verify would "
                      "mean the spec admits an implementation that edits its inputs.",
        "rationale": "rejected by (P4b) Ensures(other.name_is_own_label == "
                      "Old(other.name_is_own_label)): no other clause observes the flag "
                      "on the mapping-shaped branch, and the write is permission-legal "
                      "under aliasing, so the preservation clause is the only rejector.",
    },
    {
        "id": "alias-flip-then-raise",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _ALIAS_FLIP_THEN_RAISE),
        "refinement": "the self-justifying signal: edit an operand INTO the shape on "
                      "which no sequence exists, then report that no sequence exists. On "
                      "the same-object shape the write is permission-legal (the two 1/2 "
                      "shares sum to a whole) and the signalling condition holds in the "
                      "POST-state because the impl just established it. Its faithful "
                      "patch would rewrite the caller's own collection and then refuse "
                      "the combination -- both halves wrong: the real behaviour edits "
                      "neither operand (a fresh product is built from copied entries, "
                      "xarray/core/dataarray.py:479-487, and the core only reads the "
                      "pair, xarray/core/merge.py:818) and reports nothing on a "
                      "mapping-shaped operand. Combining a collection with itself must "
                      "return a collection identical to it (xarray/tests/test_merge.py:"
                      "148-149, graded P2P), so a refusal there does NOT resolve.",
        "rationale": "rejected by the Old(...) conjuncts of (P7) -- specifically "
                      "Exsures(..., other.is_mapping == Old(other.is_mapping)): the "
                      "signalling condition itself (not other.is_mapping and "
                      "other.name_is_own_label) is satisfied by the post-state this impl "
                      "manufactures, and permission cannot reject the write under "
                      "aliasing, so preservation on the EXCEPTIONAL outcome is the only "
                      "rejector. Measured during this cell's repair: with (P7) pinning "
                      "name/value alone, this impl VERIFIED.",
    },
    {
        "id": "alias-raise-on-name-clash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _ALIAS_RAISE_NAME_CLASH),
        "refinement": "the control-flow-effect attack on the newly-admitted shape: "
                      "produce NO sequence when the two operands carry the same entry "
                      "name, which is always so for the same-object pair. Its faithful "
                      "patch raises for `data.merge(data)` (xarray/tests/test_merge.py:"
                      "148-149, in the graded P2P set), where the required behaviour is "
                      "to return a collection identical to `data`; the assertion at 149 "
                      "would never run. It also refuses every legitimate merge of two "
                      "collections that happen to share a variable name with equal "
                      "values, which the core combines happily. Does NOT resolve -- this "
                      "is the family the earlier audit's counterexample came from, and "
                      "it verified only because the aliased shape was excluded from the "
                      "domain.",
        "rationale": "rejected by merge_method's Exsures(NormalisationUndefined, ... and "
                      "not other.is_mapping and other.name_is_own_label): signalling is "
                      "permitted ONLY where the normalisation of an array-shaped operand "
                      "is genuinely undefined. A name clash between the two operands is "
                      "not that case (and on the aliased shape the operand is "
                      "mapping-shaped), so neither conjunct can be discharged on the "
                      "raise path.",
    },
    {
        "id": "uniq-drop-second",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_SECOND),
        "refinement": "returning a one-element list [receiver] corresponds to handing "
                      "the core a single-operand list objs = [dataset] — `other` is "
                      "never merged in at all. test_merge_dataarray asserts the merged "
                      "Dataset is identical to xr.merge([ds, da]) (which contains BOTH "
                      "variables a and b); with `other` dropped the result is missing b "
                      "and assert_identical fails. Does NOT resolve.",
        "rationale": "rejected by P1 Ensures(len(Result()) == 2): the result list has "
                     "length 1, so the verifier cannot discharge len(Result()) == 2 "
                     "(and the P3b/P4 clauses about Result()[1] would also be out of "
                     "bounds).",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-pad-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PAD_LIST),
        "refinement": "a three-element list [receiver, second, second] corresponds to "
                      "passing `other` to the core merge twice. dataset_merge_method "
                      "would attempt to merge the same operand a second time — at best a "
                      "redundant no-op, at worst a self-conflict — and never matches "
                      "xr.merge([ds, da]) (a two-operand merge). Supporting near-miss "
                      "for the list-length pin; does NOT resolve.",
        "rationale": "rejected by P1 Ensures(len(Result()) == 2): the result list has "
                     "length 3, so len(Result()) == 2 cannot be discharged.",
    },

    # ---- control-flow-effect (directive 4; must reject). Reject-lane cases:
    # a verifying one would be SPEC-TOO-WEAK, so they carry kind "uniqueness". ----
    {
        "id": "cfe-swallow-undefined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_AS_MAPPING, _CFE_SWALLOW),
        "refinement": "the OVER-CLAIMED no-raise implementation: always return a "
                      "one-entry mapping-shaped operand, including for an array-shaped "
                      "operand whose entry name is also one of its own axis-label names "
                      "— for which no one-entry form exists (it would have to hold two "
                      "different things under one name). The real conversion reports "
                      "that collision instead of inventing a product; a wrapper that "
                      "swallowed it would hand the core a silently-wrong operand and "
                      "the reported conflict would vanish. Does NOT match the real "
                      "conversion on that class.",
        "rationale": "rejected by as_mapping's Ensures(not o.name_is_own_label): the "
                      "returning path claims the operand's name is NOT one of its own "
                      "axis-label names, which this impl returns without establishing "
                      "(it returns on the collision case too), so the verifier cannot "
                      "discharge it.",
    },
    {
        "id": "cfe-launder-collision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_AS_MAPPING, _CFE_LAUNDER),
        "refinement": "near-miss of cfe-swallow-undefined: still returns on the "
                      "undefined class, but copies the collision flag onto the product "
                      "— pretending a one-entry form exists while marking it as still "
                      "colliding. Its faithful patch produces an operand the core would "
                      "iterate as if well-formed. Does NOT resolve.",
        "rationale": "rejected by as_mapping's Ensures(not o.name_is_own_label) (and "
                      "additionally its Ensures(not Result().name_is_own_label)): the "
                      "impl returns on the collision case, which neither clause admits.",
    },
    {
        "id": "cfe-raise-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_AS_MAPPING, _CFE_RAISE_ALWAYS),
        "refinement": "the MIRROR-IMAGE over-claim: signal undefinedness "
                      "unconditionally, never producing an operand. This refuses the "
                      "F2P input itself (a named array-shaped operand with NO "
                      "axis-label collision), which the real conversion converts "
                      "happily. Its faithful patch would make ds.merge(da) fail for "
                      "every DataArray, so test_merge_dataarray would not resolve.",
        "rationale": "rejected by as_mapping's Exsures(NormalisationUndefined, ... and "
                      "o.name_is_own_label): the signalling path may be taken ONLY on "
                      "the collision class, and this impl takes it always, so "
                      "o.name_is_own_label cannot be discharged on the raise path.",
    },
    {
        "id": "cfe-raise-on-array",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _CFE_RAISE_ON_ARRAY),
        "refinement": "signal undefinedness for EVERY array-shaped second operand "
                      "instead of only the collision class, passing a mapping-shaped "
                      "one straight through. It refuses exactly the inputs the desired "
                      "behaviour exists to support: the F2P's named array-shaped "
                      "operand would raise rather than be combined, so "
                      "test_merge_dataarray does NOT resolve. This is the attack that "
                      "an over-broad raise path would let through.",
        "rationale": "rejected by merge_method's Exsures(NormalisationUndefined, ... "
                      "and other.name_is_own_label): signalling is permitted only where "
                      "the normalisation is genuinely undefined, and this impl signals "
                      "for every array-shaped operand, so other.name_is_own_label "
                      "cannot be discharged on the raise path.",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO consumed @ContractOnly axiom in this bundle (the
# axioms region is empty). The single kind-A obligation is an A-REFERENCE deep
# model: as_mapping (model.py) must equal the REAL unchanged conversion callee
# the fix invokes, xarray.DataArray.to_dataset(). We reuse the bundle's own
# axiom_check.py soundness logic (read on the HOST at load time and embedded into
# the probe — the runner mounts ONLY the probe at /work, so axiom_check.py is NOT
# in-container; but its imports, numpy + xarray, ARE present in the instance
# image). Two probes: SOUNDNESS (deep model == real callee, fuzzed) and
# CONTAINMENT (every callee-input the model can reach lies in the callee's domain).
# apply_gold is harmless here: the conversion callee is UNCHANGED by the patch.
# ===========================================================================

# Read the bundle's audited G-AX oracle on the HOST and embed its source so the
# in-container probe runs the SAME check (open with encoding="utf-8" — eval
# images use an ASCII locale; pilot pitfall #5). Strip axiom_check.py's own
# `if __name__ == "__main__": sys.exit(main())` guard so it does NOT exit before
# our unified guard runs both main() and the extra-boundary block below.
_AX_CHECK_SRC_RAW = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")
_GUARD = 'if __name__ == "__main__":\n    sys.exit(main())'
if _GUARD not in _AX_CHECK_SRC_RAW:
    raise AssertionError("axiom_check.py guard drifted; cannot strip it safely")
_AX_CHECK_SRC = _AX_CHECK_SRC_RAW.replace(_GUARD, "")

# axiom-soundness: run the real DataArray.to_dataset() (via the embedded
# axiom_check.check_to_dataset_reference) on the bundle's 10 boundary + 2000 fuzz
# named arrays AND extra adversarial boundaries (empty-string name, the F2P
# (name='b', data=1) exactly, a 0-D vs 1-D value), asserting the product is a
# mapping-shaped Dataset carrying the same single {name: value} variable. This is
# as_mapping's relied-on Ensures (Result().is_mapping, name/value preserved). Any
# disagreement => AXIOM-UNSOUND (the deep model would not equal the real callee).
_AX_SOUNDNESS_PROBE = (
    _AX_CHECK_SRC
    + r'''

# ---- PBT extension: run the bundle's own G-AX oracle, then extra boundaries ----
def _pbt_extra():
    import numpy as _np
    import xarray as _xr
    # the F2P input exactly: named array 'b' carrying scalar 1
    check_to_dataset_reference("b", 1)
    # the F2P receiver's lone variable shape
    check_to_dataset_reference("a", 0)
    # boundary names/values that stress the conversion's name/value preservation
    for nm, val in [("b", 0), ("z", -(2 ** 31)), ("q", 3.14159),
                    ("single", [7]), ("col", [[1], [2]])]:
        check_to_dataset_reference(nm, val)
    # sanity: an UNNAMED array is OUTSIDE as_mapping's domain (o.name >= 0); the
    # model never reaches it (merge_method requires Implies(is_array_shaped(other),
    # other.name >= 0)). Confirm the real callee RAISES there, matching the
    # precondition exclusion (it is not a soundness violation — it is excluded).
    raised = False
    try:
        _xr.DataArray(data=1).to_dataset()  # name is None -> ValueError
    except Exception:
        raised = True
    assert raised, ("to_dataset() on an UNNAMED array did NOT raise; the model "
                    "excludes this via o.name >= 0, so the real callee's raise is "
                    "the expected behaviour at the domain boundary")
    print("PBT-EXTRA OK: to_dataset() sound on F2P + boundary named arrays; "
          "unnamed array raises (excluded by the model precondition)")

if __name__ == "__main__":
    # main() runs the bundle's full boundary+2000-fuzz soundness battery (exit 0
    # iff every obligation holds); then our extra adversarial boundaries.
    import sys as _sys
    rc = main()
    if rc != 0:
        _sys.exit(rc)
    try:
        _pbt_extra()
    except AssertionError as _e:
        print("AXIOM-UNSOUND: %s" % (_e,))
        _sys.exit(1)
    _sys.exit(0)
'''
)

# axiom-containment: enumerate EXACTLY the callee-inputs the MODEL can reach and
# assert each lies in the conversion callee's well-defined domain. The model
# calls as_mapping(other) ONLY when is_array_shaped(other) (other.is_mapping ==
# False) AND, by merge_method's precondition, other.name >= 0 — i.e. a NAMED
# array-shaped operand. So the only callee-inputs the model reaches are NAMED
# DataArrays. The real callee DataArray.to_dataset() is well-defined for exactly
# named arrays and raises ValueError on an UNNAMED one (dataarray.py:467-471). We
# confirm (a) every model-reachable input (a named array) is accepted and yields
# the mapping-shaped product, and (b) the one input OUTSIDE the callee's domain
# (unnamed) is exactly the one the model's precondition excludes. A model-
# reachable input the callee rejected would be AXIOM-TOO-WEAK-FOR-CALLER; none is.
_AX_CONTAINMENT_PROBE = r'''
import sys

def main():
    try:
        import numpy as np
        import xarray as xr
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: xarray not importable: %r" % (exc,))
        return 1

    # Model-reachable callee-inputs: NAMED array-shaped operands only
    # (is_array_shaped(other) and other.name >= 0). Enumerate representative
    # named arrays the model can pass to as_mapping == to_dataset(); each must be
    # accepted (in the callee's domain) and produce the mapping-shaped product.
    reached = 0
    boundary_names = ["b", "a", "x", "0", "longname", "_", "Z9", "v"]
    boundary_vals = [1, 0, -1, 2.0, 42, [1, 2, 3], [[1, 2], [3, 4]], 2 ** 31]
    for name in boundary_names:
        for val in boundary_vals:
            da = xr.DataArray(data=val, name=name)   # a NAMED array (name >= 0)
            assert da.name not in da.coords, "probe built the undefined class"
            ds = da.to_dataset()                     # must NOT raise (in domain)
            assert isinstance(ds, xr.Dataset), (
                "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable named array (name=%r) "
                "did not convert to a Dataset: %r" % (name, type(ds)))
            items = list(ds.items())
            assert len(items) == 1, (
                "model-reachable named array produced %d variables" % len(items))
            (k, v), = items
            assert k == name and np.array_equal(
                np.asarray(v.values), np.asarray(val)), (
                "conversion did not preserve the single (name,value) the model "
                "relies on: name=%r value=%r" % (name, val))
            reached += 1

    # A model-reachable input on which the callee reports NO one-entry form: a
    # named array whose name is one of its OWN coordinate names. The model DOES
    # reach this class (it satisfies name >= 0), and it does not claim a product
    # there — it claims the conversion is undefined (as_mapping's Exsures). So
    # containment means the model's SIGNALLING outcome matches the callee's, not
    # that the callee accepts every reachable input.
    undefined_reached = 0
    for name in boundary_names:
        for val in [1, 0, -1, 2.0]:
            da = xr.DataArray(data=val, name=name, coords={name: val})  # 0-D coord
            raised = False
            try:
                da.to_dataset()
            except ValueError:
                raised = True
            assert raised, (
                "AXIOM-TOO-WEAK-FOR-CALLER: the model claims no one-entry form "
                "exists for a name-is-own-coordinate array (name=%r), but the "
                "callee produced one" % (name,))
            undefined_reached += 1

    # The ONLY input outside the callee's domain is an UNNAMED array — which the
    # model's precondition (other.name >= 0 / Implies(is_array_shaped, name>=0))
    # forbids, so the model NEVER reaches it. Confirm the callee raises there:
    # this is the float-vs-int rule (the callee's domain is named arrays; the
    # caller reaches a subset of it, never the excluded unnamed input).
    excluded_raises = False
    try:
        xr.DataArray(data=1).to_dataset()            # unnamed -> ValueError
    except Exception:
        excluded_raises = True
    assert excluded_raises, (
        "the UNNAMED array (outside as_mapping's o.name >= 0 domain) did NOT "
        "raise; if the callee accepted it the model's precondition would be "
        "over-restrictive, but the model never reaches it regardless")

    print("AXIOM-CONTAINMENT OK: all %d model-reachable callee-inputs whose "
          "normalisation the model claims is DEFINED convert to the "
          "mapping-shaped product, and all %d whose normalisation it claims is "
          "UNDEFINED (name is one of the array's own coordinate names) are "
          "reported undefined by the callee too; the one excluded input "
          "(unnamed) is exactly the one the model precondition forbids."
          % (reached, undefined_reached))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-as_mapping",
        "axiom": "as_mapping",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the conversion callee is UNCHANGED by the patch
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "the A-reference deep model as_mapping must equal the real "
                     "unchanged callee DataArray.to_dataset(): for a named array-shaped "
                     "operand the product is a mapping-shaped Dataset (.items()) "
                     "carrying the same single {name: value} variable (as_mapping's "
                     "Ensures: Result().is_mapping, Result().name==o.name, "
                     "Result().value==o.value). Runs the bundle's audited axiom_check.py "
                     "battery (10 boundary + 2000 fuzz) plus the F2P input and extra "
                     "boundaries, and the Exsures side on the class whose name is one "
                     "of its own coordinate names (no one-entry form exists); an "
                     "unnamed array (outside the domain) is confirmed to raise. Any "
                     "disagreement on a named array => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-as_mapping",
        "axiom": "as_mapping",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "the model calls as_mapping(other) ONLY when is_array_shaped(other) "
                     "and (by precondition) other.name >= 0 — i.e. a NAMED array-shaped "
                     "operand. For each, the model's claimed OUTCOME must match the "
                     "real DataArray.to_dataset(): the ones it claims convert do "
                     "convert to the mapping-shaped Dataset, and the ones it claims "
                     "have no one-entry form (name is also one of the array's own "
                     "coordinate names) are reported undefined by the callee too. The "
                     "one input outside the domain (an unnamed array) is exactly the "
                     "one the model precondition excludes. A reachable input whose "
                     "outcome the model got wrong would be AXIOM-TOO-WEAK-FOR-CALLER; "
                     "none exists.",
    },
]
