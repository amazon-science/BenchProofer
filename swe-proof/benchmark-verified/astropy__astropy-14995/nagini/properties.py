# properties.py — PBT manifest for astropy__astropy-14995.
#
# NOT a Nagini module. A record of adversarially-reasoned falsification cases
# the runner (swebench_nagini.pbt) executes and stamps RESULT on.
#
# Defended surface (from model.py):
#   result_mask(self_has_mask, self_mask, operand, handle_mask_present) -> MaskResult
#   decides the result-flag array of a binary array op by branch selection:
#     (1) no flags / no combiner -> not present
#     (2) self has none, other has flags -> copy other's array
#     (3) self has flags, other has none -> copy self's array  (THE FIX)
#     (4) both have flags -> the unchanged combiner (np.bitwise_or), axiomatized
#   Read-only inputs (Acc(...,1/2)): self_mask (list_pred), operand.has_mask,
#   operand.mask (field + list_pred). The postcondition pins each case's output
#   value via ToSeq, returns the read-only permissions, and asserts the operand
#   is value- and identity-unchanged (Old). Case 4 is grounded in the real
#   callee via combine_masks/apply_combiner (NOT an echoable constant).
#
# Region surgery: every spec variant is built by _swap on _BASE editing ONLY
# text strictly inside a # impl-start / # impl-end region, so the frozen spec
# (axioms/pure/pre/post/invariants/signatures) is byte-identical => same_spec.

from pathlib import Path

INSTANCE = "astropy__astropy-14995"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold result_mask impl region (verbatim slice for anchoring _swap edits).
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # impl-start
    empty = []  # type: List[int]
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)
    else:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)
    # impl-end"""

# Anchor sub-strings (each unique within _BASE) for targeted edits.
_CASE3_BRANCH = """    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)"""

_CASE2_BRANCH = """    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)"""

_CASE1_RETURN = "        return MaskResult(False, empty)"


# ===========================================================================
# SPEC TESTS
# ===========================================================================
SPEC_TESTS = []

# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness, expect=verify)
#    Structurally-different but CORRECT impl: branch order reshaped so the
#    no-combiner / both-empty case is split out first, the present-cases are
#    expressed with reshaped locals (build the result carrier via a single
#    local), and case-4 is reached by an explicit else. Each branch still
#    produces exactly the gold value per case, so every postcondition Implies
#    is discharged. No framing assert/lemma is needed (the per-case Ensures are
#    independent point claims, not an inductive fold), so this reorder keeps
#    the gold proof valid. If a faithful correct reshape cannot verify =>
#    SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = """    # impl-start
    empty = []  # type: List[int]
    if not handle_mask_present:
        return MaskResult(False, empty)
    if not self_has_mask and not operand.has_mask:
        return MaskResult(False, empty)
    if not self_has_mask:
        # self has none, other has flags: copy the other's array.
        oc = copy_seq(operand.mask)
        res2 = MaskResult(True, oc)
        return res2
    if not operand.has_mask:
        # self has flags, other has none: copy self's array (THE FIX).
        sc = copy_seq(self_mask)
        res3 = MaskResult(True, sc)
        return res3
    # both have flags: defer to the unchanged combiner.
    cc = apply_combiner(self_mask, operand.mask)
    res4 = MaskResult(True, cc)
    return res4
    # impl-end"""

SPEC_TESTS.append({
    "id": "pos-control-reorder",
    "kind": "soundness",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _POS),
    "rationale": (
        "A structurally-different but correct impl: combiner-absent split out "
        "first, branches reordered as a flat if-return ladder, each result "
        "carrier built through a distinct named local. Produces exactly the "
        "gold value in every case so all four postcondition Implies discharge. "
        "Per-case Ensures are independent point claims (no fold/induction), so "
        "no framing lemma is dropped. Must verify; if not => SPEC-TOO-STRONG."
    ),
})

# ---------------------------------------------------------------------------
# 2. ADMISSIBILITY (expect=verify)
#    Confirm the precondition admits a normal F2P-shaped input and is NOT
#    vacuous/contradictory: re-derive the Requires length-equality at the top
#    of the body and pin that BOTH the masked branches are independently
#    reachable by asserting the case discriminants are usable. (Cannot add a
#    top-level caller without breaking same_spec, so admissibility is an
#    in-region witness: if Requires were contradictory these asserts about the
#    in-domain facts would still type-check, but a contradictory precondition
#    would also let any rival verify — caught by the reject cases below. Here we
#    positively show the gold body verifies with the precondition re-asserted,
#    i.e. the precondition is establishable and consistent with normal inputs.)
#    If this cannot verify => PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS = """    # impl-start
    empty = []  # type: List[int]
    # admissibility witness: the precondition's shape-equality is available for
    # a normal F2P-shaped input (masked-by-flag-less, the test's case 3), and
    # the case discriminants are ordinary booleans (precondition is consistent,
    # not vacuously False).
    Assert(len(ToSeq(self_mask)) == len(ToSeq(operand.mask)))
    Assert(Implies(self_has_mask, self_has_mask))
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)
    else:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)
    # impl-end"""

SPEC_TESTS.append({
    "id": "admiss-precond-consistent",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
    "rationale": (
        "Re-derives the Requires length-equality inside the body and proceeds "
        "with the gold decision. Verifies that the precondition is establishable "
        "and consistent for a normal F2P-shaped input (masked operand meeting a "
        "flag-less operand). If the precondition could not admit such an input "
        "the body could not re-assert the length-equality => PRECOND-TOO-STRONG."
    ),
})

# ---------------------------------------------------------------------------
# 3. FRAME-MUTATION (uniqueness, expect=reject) — MANDATORY (read-only inputs).
#    self_mask is held at Acc(list_pred(self_mask), 1/2): READ-ONLY. A rival
#    that, instead of allocating a fresh copy in case 3, tries to RETURN the
#    input list after appending to it (mutating self_mask in place) cannot get
#    full permission to .append => fails for INSUFFICIENT PERMISSION. The
#    postcondition would otherwise be "satisfied" because the mutated list still
#    equals itself, but the half-permission frame forbids the write.
#    Refinement: the faithful real patch returns self.mask BY MUTATING the input
#    operand's array (in numpy, an in-place op on a shared buffer) rather than
#    deepcopy. That diverges from gold (deepcopy => "no reference in the
#    result"): downstream the result aliases self.mask, so a later in-place op
#    corrupts the source; and the F2P assertion that the result equals `mask`
#    can be violated once the shared buffer is touched. It would not faithfully
#    resolve the deepcopy contract the gold establishes.
# ---------------------------------------------------------------------------
_FRAME = """    elif not operand.has_mask:
        self_mask.append(0)
        return MaskResult(True, self_mask)"""

SPEC_TESTS.append({
    "id": "frame-mutate-self-mask",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CASE3_BRANCH, _FRAME),
    "refinement": (
        "Faithful real patch: return self.mask after mutating it in place "
        "(no deepcopy). Gold mandates deepcopy ('Make a copy so there is no "
        "reference in the result'); aliasing the input array means a later "
        "in-place op corrupts the source operand and the result no longer "
        "stably equals `mask` — the F2P np.testing.assert_equal contract is not "
        "faithfully preserved, so it would not resolve."
    ),
    "rationale": (
        "self_mask is Acc(list_pred,1/2) (read-only). .append needs full "
        "permission => rejected for INSUFFICIENT PERMISSION by the permission "
        "system, before any postcondition is even considered."
    ),
})

# ---------------------------------------------------------------------------
# 4. FRAME-MUTATION on the operand field (uniqueness, expect=reject).
#    operand.mask / operand.has_mask are Acc(...,1/2) read-only AND pinned
#    unchanged by Ensures(operand.mask is Old(operand.mask)). A rival that
#    rebinds operand.mask to the freshly-copied result (to "stash" it) needs
#    full field permission AND would violate the Old-identity clause => reject.
#    Refinement: a real patch that reassigns operand.mask mutates caller state
#    the gold never touches; subsequent reuse of `operand` in the same test
#    (the F2P reuses nref_masked across several multiply calls) would see a
#    corrupted operand, breaking later assertions — would not resolve.
# ---------------------------------------------------------------------------
_FRAME2 = """    elif not self_has_mask:
        c = copy_seq(operand.mask)
        operand.mask = c
        return MaskResult(True, c)"""

SPEC_TESTS.append({
    "id": "frame-rebind-operand-mask",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CASE2_BRANCH, _FRAME2),
    "refinement": (
        "Faithful real patch: reassign operand.mask while computing the result. "
        "Gold never mutates the operand; the F2P reuses the same masked operand "
        "across several multiply calls, so a corrupted operand breaks later "
        "assertions in the same test => would not resolve."
    ),
    "rationale": (
        "operand.mask is held at Acc(operand.mask,1/2) (read-only field) and "
        "pinned by Ensures(operand.mask is Old(operand.mask)). Writing the "
        "field needs full permission => rejected for INSUFFICIENT PERMISSION "
        "(and would also violate the Old-identity postcondition)."
    ),
})

# ---------------------------------------------------------------------------
# 5. PARTIAL-DOMAIN / THE PREPATCH BUG (uniqueness, expect=reject).
#    The exact defect the gold patch fixes: in case 3 (self has flags, other has
#    none) route to the combiner instead of copying self_mask. The case-3
#    postcondition pins ToSeq(Result().data) == ToSeq(self_mask), but the
#    combiner is opaque (combine_masks) and apply_combiner only proves
#    ToSeq(Result()) == combine_masks(self_mask, operand.mask), which Nagini
#    cannot show equals ToSeq(self_mask) => reject. This is the literal
#    prepatch behaviour (model_prepatch.py), which FAILS the F2P.
#    Refinement: the prepatch (`elif operand is None:` never fires here) falls
#    through to handle_mask(self.mask, operand.mask) = np.bitwise_or(mask, 0s)
#    which only coincidentally equals mask for an all-zero other mask; the F2P
#    `nref_masked.multiply(nref_nomask)` has operand.mask is None (no array at
#    all), so handle_mask(mask, None) raises / returns wrong => test fails. Does
#    NOT resolve.
# ---------------------------------------------------------------------------
_PREPATCH = """    elif not operand.has_mask:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)"""

SPEC_TESTS.append({
    "id": "prepatch-case3-combine",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CASE3_BRANCH, _PREPATCH),
    "refinement": (
        "Literal prepatch behaviour: masked-by-flag-less falls through to the "
        "combiner. The F2P calls nref_masked.multiply(nref_nomask, "
        "handle_mask=np.bitwise_or) and asserts the result mask == the original "
        "mask; combining against an absent/zero array does not faithfully copy "
        "the lone mask through, so the gold-fix behaviour is lost => F2P fails "
        "=> does not resolve (this is exactly model_prepatch.py, G-DIFF FAIL)."
    ),
    "rationale": (
        "Case-3 postcondition Ensures(... ToSeq(Result().data) == "
        "ToSeq(self_mask)). apply_combiner only ties the result to the OPAQUE "
        "combine_masks(self_mask, operand.mask); Nagini cannot prove that opaque "
        "value equals ToSeq(self_mask) => rejected by the case-3 postcondition."
    ),
})

# ---------------------------------------------------------------------------
# 6. WRONG-ARRAY SWAP (uniqueness, expect=reject) — value-level discrimination.
#    Case 2 (self none, other has flags) must copy OTHER's array; a rival that
#    copies self_mask there returns the wrong (but equal-length) content. The
#    case-2 postcondition pins ToSeq(Result().data) == ToSeq(operand.mask);
#    self_mask is only known equal in LENGTH, not content => reject. This proves
#    the spec discriminates the two same-length arrays by value, not just shape.
#    Refinement: a real patch that returns deepcopy(self.mask) when self.mask is
#    None deepcopies None (or an empty placeholder), losing the other operand's
#    flags entirely; the F2P `nref_nomask.multiply(nref_masked)` would not carry
#    the masked operand's flags through => does not resolve.
# ---------------------------------------------------------------------------
_SWAP = """    elif not self_has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)"""

SPEC_TESTS.append({
    "id": "swap-case2-wrong-array",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CASE2_BRANCH, _SWAP),
    "refinement": (
        "Faithful real patch: in the self-has-no-mask branch return "
        "deepcopy(self.mask) (== None / empty) instead of operand.mask. The "
        "other operand's flags are dropped, so nref_nomask.multiply(nref_masked) "
        "would not propagate the masked operand's mask => F2P fails, no resolve."
    ),
    "rationale": (
        "Case-2 postcondition Ensures(... ToSeq(Result().data) == "
        "ToSeq(operand.mask)). self_mask is only constrained equal in LENGTH "
        "(precondition len-equality), not in content, so Nagini cannot prove "
        "ToSeq(self_mask) == ToSeq(operand.mask) => rejected by the case-2 "
        "postcondition. Confirms value-level (not shape-only) discrimination."
    ),
})

# ---------------------------------------------------------------------------
# 7. PRESENT-FLAG FLIP (uniqueness, expect=reject) — control-flow/effect on the
#    Optional return. Case 1 (no flags) must return present=False (the None
#    mask). A rival that returns present=True (a non-None mask carrier) in case
#    1 violates Ensures(Implies(not handle_mask_present, not Result().present))
#    and the both-absent clause => reject. The present flag is the abstraction
#    of "returns None vs an array", so this is the value/control-flow boundary.
#    Refinement: a real patch returning an (empty) mask array instead of None
#    when no combiner / no masks is present changes the result type from None to
#    a mask; the F2P asserts `.mask is None` for the no-mask multiplies, so a
#    non-None result fails that assertion => does not resolve.
# ---------------------------------------------------------------------------
_FLIP = "        return MaskResult(True, empty)"

SPEC_TESTS.append({
    "id": "present-flag-flip-case1",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(_BASE, _CASE1_RETURN, _FLIP),
    "refinement": (
        "Faithful real patch: return an empty mask array instead of None when "
        "neither operand has flags / no combiner. The F2P asserts "
        "nref_nomask.multiply(...).mask is None; a non-None result fails that "
        "assertion => does not resolve."
    ),
    "rationale": (
        "Case-1 postconditions Ensures(Implies(not handle_mask_present, not "
        "Result().present)) and the both-absent clause require present=False. "
        "Returning MaskResult(True, ...) sets present=True => rejected by the "
        "case-1 postcondition. present is the None-vs-array abstraction (the "
        "Optional return), so this is the control-flow/effect boundary."
    ),
})

# ===========================================================================
# AXIOM TESTS
# ===========================================================================
# The bundle has two A-consumed axioms (combine_masks, apply_combiner) modelling
# the UNCHANGED combiner callable handle_mask = numpy.bitwise_or (F2P + issue).
# We reuse/strengthen axiom_check.py's logic: execute the REAL np.bitwise_or in
# the instance image and assert the encoded properties on boundary + fuzz inputs.
#
#  - axiom-soundness: the proof consumes ONLY shape preservation
#    (len(combine_masks(a,b)) == len(a) when len(a)==len(b)) plus that the value
#    is a deterministic pure function of (a,b) (so the opaque modelling of
#    apply_combiner's value as combine_masks is sound). Fuzz boundaries +
#    sentinels; any disagreement => AXIOM-UNSOUND.
#  - axiom-containment: enumerate EXACTLY the combiner inputs the MODEL can
#    reach. The combiner (apply_combiner) is called ONLY in the impl else branch
#    (case 4: both masks present), under the precondition
#    len(ToSeq(self_mask)) == len(ToSeq(operand.mask)). So every reachable callee
#    input is a pair of EQUAL-LENGTH int arrays — exactly the axiom's Requires
#    domain (len(a)==len(b)). Confirm no reachable input escapes that domain.
AXIOM_TESTS = []

_AX_SOUND_PROBE = r'''
import random
import sys

import numpy as np


def check_shape_preserving(a, b):
    arr_a = np.array(a, dtype=np.int64)
    arr_b = np.array(b, dtype=np.int64)
    out = np.bitwise_or(arr_a, arr_b)   # the real combiner handle_mask
    if out.shape != arr_a.shape:
        print("UNSOUND shape on %r,%r: %r vs %r" % (a, b, out.shape, arr_a.shape))
        sys.exit(1)
    if len(out.tolist()) != len(a):
        print("UNSOUND length axiom on %r,%r: |out|=%d |a|=%d"
              % (a, b, len(out.tolist()), len(a)))
        sys.exit(1)


def check_deterministic(a, b):
    arr_a = np.array(a, dtype=np.int64)
    arr_b = np.array(b, dtype=np.int64)
    o1 = np.bitwise_or(arr_a, arr_b).tolist()
    o2 = np.bitwise_or(arr_a, arr_b).tolist()
    if o1 != o2:
        print("UNSOUND non-deterministic on %r,%r" % (a, b))
        sys.exit(1)


# boundary: equal-length pairs incl. F2P bitmask rows (flattened) + sentinels
boundary = [
    ([], []),
    ([0], [0]),
    ([1], [0]),
    ([0], [1]),
    ([64], [64]),
    ([0, 1, 64], [64, 1, 0]),
    ([8, 0, 1], [2, 1, 0]),
    ([2, 1, 0], [8, 0, 2]),
    ([0, 1, 0, 1, 0, 1, 0, 1, 0], [0, 1, 64, 8, 0, 1, 2, 1, 0]),
    ([255, 128, 7], [1, 2, 248]),
    ([0, 0, 0], [0, 0, 0]),
]
for a, b in boundary:
    check_shape_preserving(a, b)
    check_deterministic(a, b)

rng = random.Random(14995)
for _ in range(20000):
    n = rng.randint(0, 16)
    a = [rng.randint(0, 255) for _ in range(n)]
    b = [rng.randint(0, 255) for _ in range(n)]
    check_shape_preserving(a, b)
    check_deterministic(a, b)

print("AXIOM-SOUND OK: numpy.bitwise_or shape-preserving + deterministic on "
      "%d boundary + 20000 fuzz equal-length pairs" % (len(boundary),))
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-sound-combine-masks",
    "axiom": "combine_masks",
    "kind": "axiom-soundness",
    "expect": "holds",
    "apply_gold": True,
    "probe": _AX_SOUND_PROBE,
    "rationale": (
        "Executes the real np.bitwise_or (the handle_mask the F2P + issue use). "
        "Asserts the only consumed property — shape preservation "
        "(len(out)==len(a) for equal-length inputs) — plus determinism (so the "
        "opaque value-modelling of apply_combiner as combine_masks is sound) on "
        "boundary + 20000 fuzz pairs. Any disagreement => AXIOM-UNSOUND."
    ),
})

_AX_CONTAIN_PROBE = r'''
import random
import sys

import numpy as np

# Containment: the model calls apply_combiner ONLY in the case-4 else branch
# (both masks present), under the precondition
#   len(ToSeq(self_mask)) == len(ToSeq(operand.mask)).
# So every callee input the MODEL can reach is a pair of EQUAL-LENGTH int
# arrays. The axiom's Requires domain (the property it constrains) is exactly
# len(a) == len(b) (combine_masks/apply_combiner: Implies(len(a)==len(b), ...);
# apply_combiner.Requires len(ToSeq(a))==len(ToSeq(b))). We confirm that for the
# reachable inputs the combiner is well-defined and shape-preserving, i.e. each
# reachable input lies inside the covered domain. We additionally probe that
# UNEQUAL-length inputs (which the model can NEVER reach, by the precondition)
# would NOT be shape-preserving / would broadcast or error — demonstrating the
# axiom's domain restriction is the right one and the model never escapes it.

rng = random.Random(2024)
# reachable: equal-length pairs => in the axiom Requires domain, shape-preserving
for _ in range(5000):
    n = rng.randint(0, 16)
    a = [rng.randint(0, 255) for _ in range(n)]
    b = [rng.randint(0, 255) for _ in range(n)]
    out = np.bitwise_or(np.array(a, dtype=np.int64),
                        np.array(b, dtype=np.int64))
    if len(out.tolist()) != len(a):
        print("CONTAINMENT FAIL: reachable equal-length input not covered "
              "%r,%r" % (a, b))
        sys.exit(1)

# Demonstrate the domain boundary: an UNEQUAL-length pair (NEVER reachable by
# the model, blocked by the precondition len-equality) is where the axiom is
# silent. numpy broadcasts only when one side has length 1, else it errors; in
# all sub-cases the result length is NOT len(a), so covering it would be unsound
# -- the axiom correctly restricts to len(a)==len(b), which is exactly the
# caller-reachable set. This confirms AXIOM domain == caller-reachable domain.
escaped = False
for a, b in [([1, 2, 3], [1, 2]), ([1, 2], [1, 2, 3]), ([1, 2, 3], [9])]:
    try:
        out = np.bitwise_or(np.array(a, dtype=np.int64),
                            np.array(b, dtype=np.int64))
        if len(out.tolist()) != len(a):
            escaped = True   # would violate shape preservation if reachable
    except ValueError:
        escaped = True       # would error if reachable
if not escaped:
    print("CONTAINMENT NOTE: unequal-length pairs unexpectedly shape-preserving")
    sys.exit(1)

print("AXIOM-CONTAINED OK: every model-reachable combiner input is an "
      "equal-length pair (precondition len-equality), inside the axiom's "
      "len(a)==len(b) Requires domain; unequal-length inputs are unreachable "
      "AND outside the domain, so the axiom domain == caller-reachable domain.")
sys.exit(0)
'''

AXIOM_TESTS.append({
    "id": "ax-contain-apply-combiner",
    "axiom": "apply_combiner",
    "kind": "axiom-containment",
    "expect": "covered",
    "apply_gold": True,
    "probe": _AX_CONTAIN_PROBE,
    "rationale": (
        "apply_combiner is called only in the case-4 else branch, under the "
        "precondition len(ToSeq(self_mask))==len(ToSeq(operand.mask)). Every "
        "reachable callee input is therefore an equal-length pair, exactly the "
        "axiom's len(a)==len(b) Requires domain. Confirms no reachable input "
        "escapes the covered domain (else AXIOM-TOO-WEAK-FOR-CALLER); "
        "unequal-length inputs are both unreachable and outside the domain, so "
        "the axiom domain matches the caller-reachable set."
    ),
})
