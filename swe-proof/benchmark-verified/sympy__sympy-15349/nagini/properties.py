# properties.py — PBT falsification battery for sympy__sympy-15349.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-for-byte (only the two `# impl-start/# impl-end`
# regions are edited, guaranteed by region-surgery via _swap) and are checked by
# Nagini verify + markers.same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (what THIS spec actually pins):
#
#   rotation_matrix(a,b,c,d,s) -> List[Scalar] (len 9, row-major 3x3) and
#   rotation_matrix_affine(a,b,c,d,s,x,y,z) -> List[Scalar] (len 16, row-major
#   4x4) model Quaternion.to_rotation_matrix. The CARRIER is the EXPRESSIONS of
#   the computation: `Scalar` is opaque and its only inhabitants are built by the
#   seven constructors zero/one/two/add/sub/mul/sq, which assert NOTHING -- no
#   postcondition, no algebraic law, no ordering, no numeric content. `Scalar` is
#   also the ONLY sort this behaviour computes with: the three constants are
#   nullary and the other four take scalars and return a scalar, so no number is
#   an argument, an operand or a result anywhere in the model. Three consequences
#   are what the battery leans on:
#     * sameness on this carrier is CONGRUENCE and nothing else, so a claim
#       "entry k is the term T" is a claim about how the entry is BUILT. Naming
#       subterms, sharing them, calling the @Pure helpers or delegating to the
#       3x3 method all preserve the term and still verify (the four soundness
#       cases); rebuilding it differently does not.
#     * an equation between differently-built terms is UNDECIDED here, exactly as
#       it is undecided for the repository's expressions (two expressions that
#       agree at every number are still distinct expressions). So a realisation
#       that decides an entry on such an equation must satisfy the clauses on
#       BOTH sides of it, and cannot hide a divergent branch behind a condition
#       that a numeric reading would settle (see rej-identity-guard-3x3).
#     * there is no second, numeric sort for an arithmetic guard to live in. A
#       realisation that computes with numbers is computing in a sort this
#       behaviour does not have, and what it computes there has no counterpart
#       under the map; mapping.md R-1sort records what follows for its
#       translation. The battery does not carry a reject case of that kind, and
#       deliberately so -- the note above rej-identity-guard-3x3 says why.
#   Every entry is pinned EXACTLY to a @Pure helper that is FULLY GROUNDED in
#   the args (e.g. off_cd_minus(a,b,c,d,s) unfolds to mul(two_s(s),
#   sub(mul(c,d), mul(b,a)))); the helpers unfold all the way down to
#   constructor applications, so there is no opaque answer-key to echo.
#
#   The LOAD-BEARING clause (the one edited entry) is the SIGN of the b*a term in
#   the third-column second-row entry:
#       3x3   : Ensures(Result()[5] is off_cd_minus(a,b,c,d,s))   # = 2s(cd - ba)
#       4x4   : Ensures(Result()[6] is off_cd_minus(a,b,c,d,s))   # same block entry
#       4x4   : Ensures(Result()[7] is translation(y, ..., off_cd_minus(...)))
#   The pre-change source computed 2s(cd + ba) (= off_cd_plus).
#   model_prepatch.py FAILS exactly these clauses (G-DIFF). So every rival below
#   that keeps the frozen spec but reintroduces the +b*a sign must be REJECTED by
#   the verifier; if any verifies, the spec is SPEC-TOO-WEAK (it would admit an
#   implementation that does NOT resolve the F2P test test_quaternion_conversions
#   / test_quaternion_rotation_iss1593).
#
#   There are NO read-only (Acc(x,1/2)) inputs — `Scalar` has no field, so an
#   argument carries no permission to over-write and the only mutable object
#   (Result()) is freshly constructed. Hence FRAME-MUTATION is N/A. Besides the
#   method-level MustTerminate obligation there is NO precondition at all: every
#   argument ranges over every scalar, so PRECOND-TOO-STRONG is covered by the
#   soundness cases verifying over the whole domain.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-15349"

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Unique multi-line anchors. The m12 line is identical in BOTH impl regions, so
# each anchor carries enough surrounding (function-distinctive) context to be
# unique. The 3x3 impl's block is followed by the 9-element list; the affine
# impl's by m03/m13/m23 and the 16-element list. Every edit is strictly INSIDE a
# `# impl-start/-end` region, so spec_signature (impl elided) is preserved ->
# same_spec == True.
# ---------------------------------------------------------------------------

_BLOCK = """    m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))
    m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))
    m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))

    m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))
    m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))
    m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))

    m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))
    m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))
    m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))
"""

_M12_GOLD = "m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))"
_M12_PLUS = "m12 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))"

# --- 3x3 impl region anchor (whole block, uniquely ends with the 9-elt list) ---
_IMPL3_GOLD = _BLOCK + """
    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
    return result"""

# --- affine impl region anchor (uniquely contains m03/m13/m23 + 16-elt list) ---
_IMPL4_GOLD = _BLOCK + """
    m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))
    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
    m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))
    m30 = zero()
    m31 = zero()
    m32 = zero()
    m33 = one()

    result = [m00, m01, m02, m03,
              m10, m11, m12, m13,
              m20, m21, m22, m23,
              m30, m31, m32, m33]  # type: List[Scalar]
    return result"""


def _build(impl3=None, impl4=None):
    """Return a full model.py source with the 3x3 and/or affine impl region
    replaced. Each replacement is contained within that function's impl markers."""
    src = _BASE
    if impl3 is not None:
        src = _swap(src, _IMPL3_GOLD, impl3)
    if impl4 is not None:
        src = _swap(src, _IMPL4_GOLD, impl4)
    return src


# ===========================================================================
# POSITIVE CONTROLS (expect="verify") — a faithful, structurally-DIFFERENT
# correct impl MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================

# POS-1: cheapest honest impl — build each entry by CALLING the @Pure helpers
# (the grounded oracle) rather than re-spelling the constructor applications.
# This is a different executable shape that is provably correct because each
# helper unfolds to exactly the pinned term. It is also the honest
# "cheapest-impl positive control" replacing the ungrounded-oracle echo (there is
# no WRONG echo: the oracle is grounded).
_POS1_IMPL3 = """    m00 = diag0(b, c, d, s)
    m01 = off_bc_minus(a, b, c, d, s)
    m02 = off_bd_plus(a, b, c, d, s)
    m10 = off_bc_plus(a, b, c, d, s)
    m11 = diag1(b, c, d, s)
    m12 = off_cd_minus(a, b, c, d, s)
    m20 = off_bd_minus(a, b, c, d, s)
    m21 = off_cd_plus(a, b, c, d, s)
    m22 = diag2(b, c, d, s)

    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
    return result"""

# POS-2: the reshaping a real implementation would actually make — compute the
# shared factor 2s ONCE and each repeated product ONCE, then assemble the nine
# entries from the named subterms. Congruence is exactly what makes this
# admissible, and it is the case that shows the spec pins the term rather than
# the spelling: the text is quite different, the terms are the same.
_POS2_IMPL3 = """    t = mul(two(), s)
    unit = one()
    bc = mul(b, c)
    bd = mul(b, d)
    cd = mul(c, d)
    da = mul(d, a)
    ca = mul(c, a)
    ba = mul(b, a)

    m00 = sub(unit, mul(t, add(sq(c), sq(d))))
    m01 = mul(t, sub(bc, da))
    m02 = mul(t, add(bd, ca))
    m10 = mul(t, add(bc, da))
    m11 = sub(unit, mul(t, add(sq(b), sq(d))))
    m12 = mul(t, sub(cd, ba))
    m20 = mul(t, sub(bd, ca))
    m21 = mul(t, add(cd, ba))
    m22 = sub(unit, mul(t, add(sq(b), sq(c))))

    result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]  # type: List[Scalar]
    return result"""

# POS-3: structurally-different correct impl for the affine branch — build the
# rows in REVERSED declaration order (last row first) via the same helpers; the
# final list is constructed in the identical row-major order, so every Ensures
# still holds. Different control flow / ordering, same terms.
_POS3_IMPL4 = """    m22 = diag2(b, c, d, s)
    m21 = off_cd_plus(a, b, c, d, s)
    m20 = off_bd_minus(a, b, c, d, s)

    m12 = off_cd_minus(a, b, c, d, s)
    m11 = diag1(b, c, d, s)
    m10 = off_bc_plus(a, b, c, d, s)

    m02 = off_bd_plus(a, b, c, d, s)
    m01 = off_bc_minus(a, b, c, d, s)
    m00 = diag0(b, c, d, s)

    m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))
    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
    m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))

    result = [m00, m01, m02, m03,
              m10, m11, m12, m13,
              m20, m21, m22, m23,
              zero(), zero(), zero(), one()]  # type: List[Scalar]
    return result"""

# POS-4: the affine branch DELEGATES to the 3x3 method for the shared block and
# embeds the nine returned entries — which is what the source itself does when it
# computes the block once and reuses it in both return branches. This is the case
# that tests the claim made by the two MustTerminate levels (6 above 2): a
# realisation factoring the shared block out must stay admissible.
_POS4_IMPL4 = """    block = rotation_matrix(a, b, c, d, s)
    m00 = block[0]
    m01 = block[1]
    m02 = block[2]
    m10 = block[3]
    m11 = block[4]
    m12 = block[5]
    m20 = block[6]
    m21 = block[7]
    m22 = block[8]

    m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))
    m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))
    m23 = sub(sub(sub(z, mul(x, m20)), mul(y, m21)), mul(z, m22))

    result = [m00, m01, m02, m03,
              m10, m11, m12, m13,
              m20, m21, m22, m23,
              zero(), zero(), zero(), one()]  # type: List[Scalar]
    return result"""


# ===========================================================================
# UNIQUENESS / REJECT rivals (expect="reject") — same spec, WRONG impl. Each
# MUST fail to verify; a verifying rival is SPEC-TOO-WEAK. Each carries the
# refinement argument that its faithful real patch would NOT resolve the F2P.
# ===========================================================================

# REJ-1: the EXACT pre-change bug in the 3x3 branch — 2s(cd + ba) (= off_cd_plus).
# This is verbatim model_prepatch.py's discriminating impl.
_REJ1_IMPL3 = _IMPL3_GOLD.replace(_M12_GOLD, _M12_PLUS)

# REJ-2: the same bug carried into the affine branch.
_REJ2_IMPL4 = _IMPL4_GOLD.replace(_M12_GOLD, _M12_PLUS)

# REJ-3: SWAP the two (cd)-off-diagonals — put off_cd_plus at index 5 (m12) and
# off_cd_minus at index 7 (m21). This is the natural "which one is negative?"
# transcription error. Violates BOTH Result()[5] is off_cd_minus and
# Result()[7] is off_cd_plus.
_REJ3_IMPL3 = _IMPL3_GOLD.replace(
    _M12_GOLD, _M12_PLUS).replace(
    "m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))",
    "m21 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))")

# REJ-4: PARTIAL-DOMAIN — the corrected sign only when the first component is the
# scalar 0, the +b*a sign otherwise. On the X-rotation witness
# Quaternion(cos(x/2),sin(x/2),0,0) that component is cos(x/2), which is not the
# scalar 0, so this rival carries the pre-change entry on the issue witness.
_REJ4_IMPL3 = _IMPL3_GOLD.replace(
    "    " + _M12_GOLD,
    """    if a is zero():
        %s
    else:
        %s""" % (_M12_GOLD, _M12_PLUS))

# REJ-5: PARTIAL-DOMAIN ON AN ALGEBRAIC IDENTITY. The rival decides the entry on
# the condition (a+d)*(a+d) != a**2 + 2*a*d + d**2 -- two expressions that agree
# at every number and are DISTINCT expressions. This is the case the carrier
# exists for; see the rationale below.
_REJ5_IMPL3 = _IMPL3_GOLD.replace(
    "    " + _M12_GOLD,
    """    if mul(add(a, d), add(a, d)) != add(add(sq(a), mul(two(), mul(a, d))), sq(d)):
        %s
    else:
        %s""" % (_M12_PLUS, _M12_GOLD))

# The condition the three cases below decide on. Its two sides agree at every
# number and are DISTINCT expressions, so the repository leaves it standing while
# a carrier of numbers settles it. Kept as one name so the three cases are known
# to be probing the same condition at three different entries.
_GUARD_SQ = ("mul(add(a, d), add(a, d)) != "
             "add(add(sq(a), mul(two(), mul(a, d))), sq(d))")

_M01_GOLD = "m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))"
_M01_PLUS = "m01 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))"
_M00_GOLD = "m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))"
_M00_SWAP = "m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(b))))"
_M03_GOLD = "m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m02))"
_M03_BAD = "m03 = sub(sub(sub(x, mul(x, m00)), mul(y, m01)), mul(z, m22))"


def _guarded(impl, gold, alt, cond):
    """Insert `if cond: <alt>` immediately after the gold assignment, so the
    gold value is what the rival computes when the condition does not hold."""
    old = "    " + gold
    if impl.count(old) != 1:
        raise AssertionError("not unique: %r" % gold)
    return impl.replace(old, "    %s\n    if %s:\n        %s" % (gold, cond, alt), 1)


# REJ-9: the identity guard at a DIFFERENT entry (m01), in BOTH branches. Same
# condition as REJ-5, different entry and both methods -- so the reject lane does
# not rest on one entry happening to be the pinned one.
_REJ9_IMPL3 = _guarded(_IMPL3_GOLD, _M01_GOLD, _M01_PLUS, _GUARD_SQ)
_REJ9_IMPL4 = _guarded(_IMPL4_GOLD, _M01_GOLD, _M01_PLUS, _GUARD_SQ)

# REJ-10 (WITHDRAWN FROM THE EXECUTED LANE -- the verifier refuses to judge it).
# The RELATIONAL family: a rival deciding the diagonal entry on an ORDER
# comparison between two expressions,
#     if mul(sub(a, d), add(a, d)) < sub(sq(a), sq(d)):
#         m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(b))))
# is not merely refutable on this carrier, it is INEXPRESSIBLE: `Scalar` has no
# order, so the file does not reach the verifier at all. Measured, verbatim:
#     Translation failed
#     Type error: Unsupported left operand type for < ("Scalar")
#   -> nagini exit 1 after 12.7s, no Viper verdict.
# A front-end refusal is NOT a verification rejection, and the runner is right to
# file it as NO-VERDICT rather than as a kill: an expect="reject" case that never
# reached the verifier certifies nothing about the spec, and counting it would be
# the same soundness hole as counting a timeout. So the case is stated here as
# prose and is NOT in SPEC_TESTS. What closes the family is the carrier itself --
# there is no order on `Scalar` for a rival to branch on, and mapping.md R-vocab
# enumerates what is left (`==`, `!=`, `is`, `is not`, and truthiness), every one
# of which is undecided between differently-built terms, so both sides of any
# guard a rival can actually write carry the entry obligations. The judged
# evidence for that is rej-identity-guard-3x3/-m01 (equational) and the three
# rej-truthiness-guard cases (truth value).

# REJ-11: the identity guard on the AFFINE TRANSLATION COLUMN only -- the whole
# 3x3 block is gold, so every block clause holds and only the m03 entry diverges.
_REJ11_IMPL4 = _guarded(_IMPL4_GOLD, _M03_GOLD, _M03_BAD, _GUARD_SQ)


# REJ-6: PARTIAL-DOMAIN ON THE AFFINE TRANSLATION COLUMN — the upper-left 3x3
# block is correct (so Result()[6] is off_cd_minus holds), but m13 is built from a
# differently-signed local re-derivation of m12, breaking only Result()[7] (the
# inherited translation entry). This targets the SECOND load-bearing clause,
# which the block-only attacks miss.
_REJ6_IMPL4 = _IMPL4_GOLD.replace(
    "    m03 = sub(",
    "    m12b = %s\n    m03 = sub(" % _M12_PLUS).replace(
    "m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))",
    "m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12b))")

# REJ-7: TRANSPOSE the rotation block (3x3). A transposed proper-rotation matrix
# is its inverse (the rotation by the negated angle); transposition swaps every
# off-diagonal pair, in particular index 5 <-> index 7 (off_cd_minus <->
# off_cd_plus) and 1<->3, 2<->6.
_REJ7_IMPL3 = _IMPL3_GOLD.replace(
    "result = [m00, m01, m02, m10, m11, m12, m20, m21, m22]",
    "result = [m00, m10, m20, m01, m11, m21, m02, m12, m22]")

# REJ-8 (WITHDRAWN FROM THE EXECUTED LANE -- the verifier refuses to judge it),
# same disposition and same reason as REJ-10 above. The TRUNCATION family: the
# multiply-floor-divide idiom on the load-bearing entry,
#     m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a))) // one()
# which is the identity on integers and a rounding step on anything else. There
# is no division and no rounding on `Scalar`, so the rival does not translate.
# Measured, verbatim:
#     Translation failed
#     Type error: Unsupported left operand type for // ("Scalar")
#   -> nagini exit 1 after 13.3s, no Viper verdict.
# Not in SPEC_TESTS for the same reason: nothing was judged, so nothing is
# certified. The family is closed by the carrier having ONE sort and no division
# on it (model.py CARRIER; mapping.md R-1sort), which is a property of the spec
# view and is checked there rather than by a rival the front end throws out.


# REJ-12/13/14: CONSTANT CONFUSION -- the wrong nullary constant at a load-bearing
# position. These are the direct authored counterpart of what the mutation gate
# used to generate here, and the reason they are authored: when the three
# constants were a single constructor taking a whole-number index, the index was
# an integer LITERAL in the impl region and a token-level mutation of it (0->1,
# 1->2, 2->3) was a behavioural mutant. Three nullary constants leave no integer
# token in the impl region at all -- which is the point of them, the modelled
# behaviour having only one sort of computed value -- so that surface is empty and
# G-MUT reports the empty surface rather than an inflated kill rate. The evidence
# belongs in this lane instead, where it is stated as a rival rather than derived
# from a token, and where the verifier decides it under the same oracle as every
# other case here.
_REJ12_IMPL3 = _IMPL3_GOLD.replace(
    _M00_GOLD, "m00 = sub(two(), mul(mul(two(), s), add(sq(c), sq(d))))")

_REJ13_IMPL3 = _IMPL3_GOLD.replace(
    _M12_GOLD, "m12 = mul(mul(one(), s), sub(mul(c, d), mul(b, a)))")

_REJ14_IMPL4 = _IMPL4_GOLD.replace("    m33 = one()", "    m33 = zero()")

# REJ-15/16: TRUTHINESS OF A CARRIER TERM. The rival decides the load-bearing
# entry on the TRUTH VALUE of a scalar rather than on a relation between two of
# them: it computes the corrected entry and then overwrites it with the
# pre-change one behind `if not zero():`. A reader who supposes the nought
# scalar counts as false reads the guarded branch as the one always taken; a
# reader who supposes every scalar counts as true reads it as dead. The carrier
# settles neither, which is the point of these cases: `Scalar.__bool__` is
# declared and asserts NOTHING, so the truth value of a scalar is undecided
# exactly as an equation between differently-built scalars is, and BOTH sides of
# such a guard carry the entry obligations.
_REJ15_IMPL3 = _guarded(_IMPL3_GOLD, _M12_GOLD, _M12_PLUS, "not zero()")
_REJ15_IMPL4 = _guarded(_IMPL4_GOLD, _M12_GOLD, _M12_PLUS, "not zero()")

# REJ-16: the same lever on an argument rather than a constant, and inverted so
# the CORRECTED entry sits on the guarded side. Fires where the third component
# counts as false, which is where the issue's own rotation witness lives.
_REJ16_IMPL3 = _guarded(_IMPL3_GOLD, _M12_GOLD, _M12_PLUS, "not c")

# REJ-17: truthiness reached through a term BUILT FROM THE ARGUMENTS, so the
# guard is not a constant fold: a scalar minus itself. Nothing on this carrier
# identifies that term with nought and nothing decides its truth value either.
_REJ17_IMPL3 = _guarded(_IMPL3_GOLD, _M12_GOLD, _M12_PLUS,
                        "not sub(mul(c, d), mul(c, d))")

# POS-5: the OVER-CONSTRAINT control for the undecided truth value. Making
# truthiness undecided is a constraint on rivals, so it has to be shown not to be
# a constraint on faithful realisations: this one branches on the truth value of a
# scalar exactly as REJ-15 does and computes the PINNED term on both sides. The
# obligation is discharged on each branch separately, so it must verify -- if it
# does not, the truth-value clause has over-constrained the spec and forbids a
# realisation that merely spells the entry twice.
_POS5_IMPL3 = _guarded(_IMPL3_GOLD, _M12_GOLD, _M12_GOLD, "not zero()")


SPEC_TESTS = [
    # ---------------- positive controls (soundness) ----------------
    {
        "id": "pos-helpers-3x3",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(impl3=_POS1_IMPL3),
        "rationale": "A faithful, structurally-different 3x3 impl that constructs "
                     "each entry by CALLING the grounded @Pure helpers (off_cd_minus "
                     "etc.) instead of re-spelling the constructor applications. Each "
                     "helper unfolds to exactly the pinned term, so every Ensures holds. "
                     "Must verify, else the postcondition is SPEC-TOO-STRONG (it would "
                     "reject the obvious correct construction). Also the honest "
                     "cheapest-impl positive control standing in for the "
                     "ungrounded-oracle case (the oracle here is grounded -> no wrong echo). "
                     "Because it verifies over the WHOLE argument domain -- there is no "
                     "precondition on any argument -- it is at the same time the "
                     "admissibility control for the preconditions.",
    },
    {
        "id": "pos-shared-subterms-3x3",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(impl3=_POS2_IMPL3),
        "rationale": "The reshaping a real implementation would actually make: the "
                     "shared factor 2s and each repeated product are computed ONCE and "
                     "the nine entries assembled from the named subterms. The impl text "
                     "differs substantially from the pinned spelling while the TERMS are "
                     "the same, and congruence is exactly what lets the verifier see "
                     "that. Must verify, else the spec is SPEC-TOO-STRONG in the way "
                     "this carrier would be most likely to be -- pinning a spelling "
                     "rather than a term. This is the control that says the opaque "
                     "carrier does not force a realisation to copy the reference text.",
    },
    {
        "id": "pos-reversed-affine",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(impl4=_POS3_IMPL4),
        "rationale": "A correct affine impl that computes the rows in REVERSED "
                     "declaration order (m22..m00) and the translation entries "
                     "m23,m13,m03 in reversed order, then assembles the SAME row-major "
                     "16-list (with the zero(),zero(),zero(),one() trailer). Different "
                     "control flow, identical terms; all 16 Ensures hold. Must verify "
                     "(else SPEC-TOO-STRONG). No front-recursive fold / forward-append "
                     "lemma is involved (straight-line construction), so this is a safe "
                     "structural positive control.",
    },
    {
        "id": "pos-delegate-affine",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(impl4=_POS4_IMPL4),
        "rationale": "The affine branch DELEGATES to rotation_matrix for the shared "
                     "upper-left block and embeds the nine returned entries -- which is "
                     "what the source itself does, computing the block once and reusing "
                     "it in both return branches. This case exists to TEST the claim the "
                     "two MustTerminate levels make (6 above 2, rather than both 2): "
                     "that a realisation factoring the shared block out stays "
                     "admissible. If it fails to verify the levels are SPEC-TOO-STRONG "
                     "and reject the source's own factoring; it must verify.",
    },
    # ---------------- uniqueness / reject rivals ----------------
    {
        "id": "pos-truthiness-branch-both-sides-3x3",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(impl3=_POS5_IMPL3),
        "rationale": "The admissibility control for the carrier's UNDECIDED truth "
                     "value. `Scalar.__bool__` is declared with no postcondition, so a "
                     "guard on a scalar's truth value is live on both sides and each "
                     "side carries the entry obligations. That is what rejects the "
                     "rej-truthiness-guard rivals; this case is the other half of the "
                     "measurement, and it is the shape a real implementation would have "
                     "if it spelled the entry inside a branch it happens to take: the "
                     "SAME pinned term on both sides of `if not zero():`. Measured: "
                     "`Verification successful`, Viper 22.8s. Must verify, else the "
                     "truth-value clause is SPEC-TOO-STRONG -- it would be rejecting an "
                     "implementation that "
                     "computes exactly the pinned entry, and the strengthening that "
                     "closed the truthiness family would have cost admissibility rather "
                     "than bought soundness.",
    },
    {
        "id": "rej-prepatch-sign-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ1_IMPL3),
        "refinement": "This is model_prepatch.py's discriminating impl verbatim: "
                      "2*s*(c*d + b*a). It is the pre-change source line the diff "
                      "edits (quaternion.py:532, the only changed line). A real patch "
                      "keeping that line is the unchanged method, which fails "
                      "test_quaternion_conversions and test_quaternion_rotation_iss1593 "
                      "(the X-rotation gets +sin where -sin is required) -> does NOT resolve.",
        "rationale": "Must be rejected by Ensures(Result()[5] is off_cd_minus(a,b,c,d,s)) "
                     "in rotation_matrix: off_cd_plus is a different term, and no equation "
                     "between the two is available on this carrier. If it verifies, "
                     "SPEC-TOO-WEAK (it would admit an implementation that does not resolve).",
    },
    {
        "id": "rej-prepatch-sign-affine",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl4=_REJ2_IMPL4),
        "refinement": "Same bug in the affine (4x4) branch: 2*s*(c*d + b*a). Since the "
                      "edit is a SINGLE source line consumed by BOTH return branches, the "
                      "faithful real patch missing it is unchanged in both, so "
                      "q1.to_rotation_matrix((1,1,1)) in test_quaternion_conversions "
                      "yields the pre-change block (and m13) -> does NOT resolve.",
        "rationale": "Rejected by Ensures(Result()[6] is off_cd_minus(...)) (the upper-left "
                     "block entry) AND Ensures(Result()[7] is translation(y, ..., "
                     "off_cd_minus(...))) (the inherited translation entry) in "
                     "rotation_matrix_affine. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-swap-cd-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ3_IMPL3),
        "refinement": "Swaps which (cd)-off-diagonal carries the minus sign: m12 gets "
                      "+b*a and m21 gets -b*a (the two are interchanged). A real patch with "
                      "this transcription puts the negative sign in the LOWER off-diagonal "
                      "instead of the upper one, producing the transpose-like matrix that "
                      "fails the exact Matrix equality in test_quaternion_conversions -> does "
                      "NOT resolve.",
        "rationale": "Rejected by BOTH Ensures(Result()[5] is off_cd_minus) (now off_cd_plus) "
                     "and Ensures(Result()[7] is off_cd_plus) (now off_cd_minus). If it verifies, "
                     "SPEC-TOO-WEAK (the spec failed to pin WHICH off-diagonal is negative).",
    },
    {
        "id": "rej-partial-domain-a0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ4_IMPL3),
        "refinement": "The corrected sign only when the first component is the scalar 0, "
                      "the +b*a sign otherwise. The issue witness "
                      "Quaternion(cos(x/2), sin(x/2), 0, 0) has a = cos(x/2), which is not "
                      "the scalar 0, so this rival carries the pre-change entry on the very "
                      "input test_quaternion_rotation_iss1593 checks -> does NOT resolve. "
                      "(Even a rival that happened to be correct on every literal F2P input "
                      "would be a verify-without-resolve break, since the change must be "
                      "correct for all quaternions.)",
        "rationale": "Rejected by Ensures(Result()[5] is off_cd_minus(a,b,c,d,s)), which the "
                     "verifier must establish for EVERY a; on this carrier a is zero() is "
                     "undecided, so BOTH branches are reachable and the else-branch is "
                     "refuted. Demonstrates the postcondition pins the entire domain, not a "
                     "sampled subset (partial-domain class). If it verifies, SPEC-TOO-WEAK.",
    },
    # -----------------------------------------------------------------------
    # Why there is no reject case guarding on a CLOSED NUMERIC expression.
    #
    # A rival can write, inside its impl region, a guard on an expression built
    # entirely from whole-number literals -- one whose value the verifier and the
    # repository's language disagree about, integer division being the readiest
    # source (this language floors, the verifier divides toward zero, so the two
    # differ at every negative divisor). Neither direction of that construction
    # belongs in this lane, and saying which is worth doing here rather than
    # leaving the absence to look like an oversight.
    #
    #   * A guard the verifier decides FALSE, and this language TRUE, VERIFIES:
    #     the branch behind it is unreachable in the proof, so no clause is
    #     evaluated on it. Listing it as expect="reject" would fail this lane and
    #     would be wrong to list, because no strengthening of the model closes it
    #     -- the guard is a closed expression, so the rival's impl and the gold
    #     impl are the SAME computation under the verifier's semantics, and any
    #     model the one satisfies the other satisfies. The construction is
    #     available against every specification of every behaviour, which is
    #     precisely why it is not a fact about THIS one. What answers it is the
    #     MAP: mapping.md R-1sort, refinement.md A0-note.
    #   * A guard the other way round -- decided TRUE by the verifier, FALSE by
    #     this language -- is refuted here (measured: the verifier proves
    #     7 // -2 is -3, so a guard reading it as -4 is dead and one reading it
    #     as -3 is live and carries the clause into the divergent branch). But
    #     that rival's realisation RESOLVES: this language reads the same guard
    #     as false and takes the correct branch. Its rejection is the model being
    #     stricter than correctness, not a hole being closed, and recording it as
    #     a reject-lane win would credit this spec with strength it does not
    #     have. The honest place for it is a measurement, so it is one:
    #     conformance_check.py check_no_number_sort records both languages'
    #     readings and confirms that neither impl region depends on either.
    # -----------------------------------------------------------------------
    {
        "id": "rej-identity-guard-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ5_IMPL3),
        "refinement": "The rival decides the load-bearing entry on the condition "
                      "(a+d)*(a+d) != a**2 + 2*a*d + d**2, taking the +b*a sign when it "
                      "holds. The two sides agree at every number, so a reader who thinks "
                      "of the scalars as numbers reads the branch as dead -- but the "
                      "repository's scalars are EXPRESSIONS and its equality is an equality "
                      "of expressions, under which those two are distinct. A real patch "
                      "guarded this way therefore takes the guarded branch on the F2P "
                      "witnesses and returns the pre-change entry -> does NOT resolve.",
        "rationale": "This case exists for the CARRIER, not the entry, and it is the one "
                     "that rules a carrier of numbers out. Over any field (or ring) of "
                     "scalars the guard is unsatisfiable, the branch behind it is "
                     "unreachable, and the rival VERIFIES while carrying a divergent entry "
                     "at every argument the behaviour is realised at -- a "
                     "verify-without-resolve hole that no strengthening of the entry "
                     "equations can close, because the rival violates none of them. It is "
                     "not an artificial condition either: any polynomial identity does the "
                     "same, and the repository leaves all of them standing. On the "
                     "expression carrier the two sides are distinct terms, no equation "
                     "between them is provable in either direction, both branches are "
                     "reachable, and Ensures(Result()[5] is off_cd_minus(a,b,c,d,s)) is "
                     "refuted on the guarded one. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-identity-guard-m01",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ9_IMPL3, impl4=_REJ9_IMPL4),
        "refinement": "The same condition as rej-identity-guard-3x3 at a DIFFERENT "
                      "entry and in BOTH branches: m01 takes the +d*a sign when "
                      "(a+d)*(a+d) != a**2 + 2*a*d + d**2 holds. In the repository that "
                      "condition holds of expressions, so a real patch guarded this way "
                      "returns the divergent m01 on every input, including the F2P "
                      "witnesses: the X-rotation matrix comes back with +sin where -sin "
                      "is required, which is the issue's own symptom relocated to another "
                      "entry -> does NOT resolve. Both branches are edited, so the "
                      "3x3 and the 4x4 return path are both affected.",
        "rationale": "Present so the reject lane does not rest on the load-bearing entry "
                     "happening to be the one a rival picks. Rejected by "
                     "Ensures(Result()[1] is off_bc_minus(a,b,c,d,s)) in rotation_matrix "
                     "and Ensures(Result()[1] is off_bc_minus(...)) in "
                     "rotation_matrix_affine, plus the translation clause at index 3 "
                     "which is built from m01. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-identity-guard-affine-m03",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl4=_REJ11_IMPL4),
        "refinement": "PARTIAL DOMAIN, narrowest form: the entire 3x3 block is gold, so "
                      "every block clause holds, and only the first translation entry m03 "
                      "diverges -- it is built from m22 in place of m02 behind the same "
                      "condition. A real patch shaped this way returns a correct rotation "
                      "block and a divergent affine 4x4, and test_quaternion_conversions "
                      "checks q1.to_rotation_matrix((1,1,1)) for exact Matrix equality "
                      "-> does NOT resolve.",
        "rationale": "The case that asks whether the 4x4 clauses are load-bearing on "
                     "their own. A rival corrupting only the translation column satisfies "
                     "all nine block clauses, so if the translation clauses were absent "
                     "or weaker it would verify. Rejected by "
                     "Ensures(Result()[3] is translation(x, x, y, z, diag0(...), "
                     "off_bc_minus(...), off_bd_plus(...))): the rival's m03 is built "
                     "from diag2 in the third slot, a different term. If it verifies, "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-partial-domain-translation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl4=_REJ6_IMPL4),
        "refinement": "The 3x3 block is correct (Result()[6] is off_cd_minus holds), but m13 "
                      "is built from a differently-signed local re-derivation of m12 (+b*a). "
                      "A real patch that corrected the matrix entry but reused a stale +b*a "
                      "expression when forming the translation column produces a divergent "
                      "affine 4x4: q1.to_rotation_matrix((1,1,1)) in "
                      "test_quaternion_conversions yields the divergent row-2 translation "
                      "entry -> does NOT resolve.",
        "rationale": "Rejected by Ensures(Result()[7] is translation(y, x, y, z, "
                     "off_bc_plus(...), diag1(...), off_cd_minus(...))): m13 here is built "
                     "from off_cd_plus, a different term. Targets the SECOND load-bearing "
                     "clause that block-only rivals never touch. If it verifies, "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-constant-diag-unity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ12_IMPL3),
        "refinement": "The leading term of the first diagonal entry is the scalar "
                      "denoted by twice unity where the entry is 1 - 2s(c^2+d^2), so the "
                      "realised source line reads 2 - 2*s*(q.c**2 + q.d**2). The F2P "
                      "witness compares the whole matrix for exact equality, so the "
                      "diagonal is wrong at every quaternion -> does NOT resolve.",
        "rationale": "Rejected by Ensures(Result()[0] is diag0(b, c, d, s)), whose "
                     "leading subterm is one() and not two(); the two are distinct "
                     "scalars on this carrier and no equation relates them. Replaces the "
                     "literal-index mutant the mutation surface no longer carries: it "
                     "asks whether the spec pins WHICH constant a position holds, which "
                     "is the one thing a nullary constant could get wrong. If it "
                     "verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-constant-factor-unity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ13_IMPL3),
        "refinement": "The shared off-diagonal factor is unity rather than twice unity "
                      "at the load-bearing entry, so the realised source line reads "
                      "1*s*(q.c*q.d - q.b*q.a) -- half the correct entry at every "
                      "quaternion, and the entry the issue witness turns on -> does NOT "
                      "resolve.",
        "rationale": "Rejected by Ensures(Result()[5] is off_cd_minus(a, b, c, d, s)), "
                     "which unfolds through two_s to mul(two(), s); mul(one(), s) is a "
                     "different scalar and nothing identifies them (there is no unit law "
                     "on this carrier -- the constructors assert nothing). The companion "
                     "of the case above at the entry the change is about. If it verifies, "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-constant-affine-corner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl4=_REJ14_IMPL4),
        "refinement": "The affine corner is nought instead of unity, so the realised "
                      "trailing row is (0, 0, 0, 0) and the 4x4 result is not an affine "
                      "embedding at all. P2P covers the affine branch, so this is wrong "
                      "on every translation point -> does NOT resolve.",
        "rationale": "Rejected by Ensures(Result()[15] is one()). Covers the third "
                     "constant and the second modelled function, so the constant-"
                     "confusion evidence is not concentrated in one method or one "
                     "constant. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-truthiness-guard-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ15_IMPL3, impl4=_REJ15_IMPL4),
        "refinement": "The rival computes the corrected entry and then overwrites it "
                      "with the pre-change +b*a sign inside `if not zero():`, in BOTH "
                      "methods. The repository's scalars are expressions, and the "
                      "expression this behaviour's nought scalar names is one the "
                      "surrounding library treats as false -- so a real patch guarded "
                      "this way takes the guarded branch on every input, including both "
                      "F2P witnesses, and returns the pre-change entry -> does NOT "
                      "resolve.",
        "rationale": "This case exists for the TRUTH VALUE of the carrier, the way "
                     "rej-identity-guard-3x3 exists for equations on it. A carrier whose "
                     "scalars are ordinary references has their truth value DECIDED (a "
                     "non-null reference counts as true), so the guarded branch is dead "
                     "in the proof and a rival hiding the pre-change entry behind it "
                     "verifies while computing that entry at every argument the "
                     "behaviour is realised at -- and no strengthening of the entry "
                     "equations reaches it, since it violates none of them on the live "
                     "branch. Here `Scalar.__bool__` is declared with no postcondition, "
                     "so no scalar is known to count as true and none is known to count "
                     "as false: both sides of the guard are reachable and "
                     "Ensures(Result()[5] is off_cd_minus(a,b,c,d,s)) (resp. [6]) is "
                     "refuted on the guarded one. Measured on this spec, verbatim: "
                     "`Verification failed` / `error: Postcondition of rotation_matrix "
                     "might not hold. Assertion (Result()[5] is off_cd_minus(a, b, c, "
                     "d, s)) might not hold.` and `error: Postcondition of "
                     "rotation_matrix_affine might not hold. Assertion (Result()[6] is "
                     "off_cd_minus(a, b, c, d, s)) might not hold.` -- a real Viper "
                     "verdict in 26.9s, not a front-end refusal (a `Translation failed` "
                     "comes back in ~13s and judges nothing; see REJ-8/REJ-10). The "
                     "guarded branch is REACHABLE and not vacuously discharged: the same "
                     "rival with `Assert(False)` as the first statement inside the guard "
                     "is REFUTED (`error: Assert might fail. Assertion False might not "
                     "hold.`, 23.2s), and so is the complementary guard `if zero(): "
                     "Assert(False)` (25.6s), so the verifier decides the truth value of "
                     "a scalar NEITHER way. If this case verifies, SPEC-TOO-WEAK: the "
                     "spec would again admit a rival whose faithful patch reintroduces "
                     "the pre-change +b*a entry on every input -- measured, that patch "
                     "fails F2P test_quaternion_conversions (1 failed, 3 P2P passed) "
                     "while the gold patch passes 4/4.",
    },
    {
        "id": "rej-truthiness-guard-argument",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ16_IMPL3),
        "refinement": "The same lever on an ARGUMENT rather than a constant: the "
                      "pre-change sign is taken where the third component counts as "
                      "false. The issue's own witness has that component nought, so the "
                      "realised patch carries the pre-change entry on exactly the "
                      "rotation the report is about -> does NOT resolve.",
        "rationale": "Guards the case that the undecidedness is a property of the "
                     "carrier and not of the three constants: an argument ranges over "
                     "every scalar, and nothing decides whether a given one counts as "
                     "true. Refuted at Result()[5]. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-truthiness-guard-built-term",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ17_IMPL3),
        "refinement": "The guard is the truth value of a term BUILT FROM THE ARGUMENTS "
                      "-- a product minus itself -- so it is not a constant a reader can "
                      "fold away. The repository evaluates that difference to the "
                      "expression its library treats as false, so the realised patch "
                      "takes the guarded branch on every input -> does NOT resolve.",
        "rationale": "Closes the path of writing the same lever without naming a "
                     "constant. Sameness on this carrier is congruence, so nothing "
                     "identifies sub(mul(c,d), mul(c,d)) with nought, and __bool__ "
                     "asserting nothing means nothing decides its truth value either; "
                     "both branches carry the obligation and the guarded one refutes "
                     "Result()[5]. If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-transpose-3x3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(impl3=_REJ7_IMPL3),
        "refinement": "Returns the TRANSPOSE of the rotation block (row-major of M.T). For a "
                      "proper rotation M.T == M^-1 (rotation by the negated angle), so a real "
                      "patch returning the transposed Matrix gives a different rotation and "
                      "fails the exact Matrix equality in test_quaternion_conversions on q1 "
                      "(all components nonzero) -> does NOT resolve. Coincides with the "
                      "required matrix only on symmetric ones.",
        "rationale": "Rejected by Ensures(Result()[5] is off_cd_minus) (which now holds "
                     "off_cd_plus, the transposed entry) plus the Result()[1]/[2]/[3]/[6]/[7] "
                     "pins. A structural attack (off-diagonal permutation) invisible to any "
                     "abstraction that only checks the diagonal or a value multiset. If it "
                     "verifies, SPEC-TOO-WEAK.",
    },
]


# ===========================================================================
# AXIOM LANE — empty.
#
# The seven @ContractOnly functions listed in meta.axioms are the CONSTRUCTORS of
# the carrier and they assert nothing: no postcondition, no algebraic law, no
# ordering, no numeric content. There is consequently no axiom obligation for
# this lane to probe -- an axiom with no content cannot be exploited, and there
# is no `Ensures` a rival could satisfy vacuously or lean on. What the refinement
# does rely on are R-references (each constructor names one repository operation;
# the Matrix constructor is row-major and value-preserving; congruence holds of
# the repository's expressions), and those are validated against the REAL callee
# by axiom_check.py / tasks/sympy__sympy-15349/axiom_check.py (G-AX: boundary +
# fuzz quaternions over both shapes, fully symbolic quaternions compared as
# expression TREES, and the exhibition of differently-built expressions that
# agree at every number while being distinct there). AXIOM_TESTS is therefore
# empty by design.
# ===========================================================================
AXIOM_TESTS = []
