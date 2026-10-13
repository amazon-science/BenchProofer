# properties.py — PBT falsification battery for matplotlib__matplotlib-23412.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region — which spec_view elides,
# INCLUDING the nested invariants region — so same_spec holds by construction)
# and are checked by Nagini verify; axiom cases are real-callee probes in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   render_dash_pattern(phase: int, onoff: List[int]) -> List[int]
#     Requires Acc(list_pred(onoff), 1/2)                  <-- READ-ONLY input (half perm)
#     Ensures  Acc(list_pred(onoff), 1/2)                  <-- frame: caller keeps its half
#     Ensures  ToSeq(onoff) == Old(ToSeq(onoff))           <-- onoff unmutated
#     Ensures  Acc(list_pred(Result()))                    <-- result freshly owned
#     Ensures  len(Result()) == len(onoff) + 1             <-- exact length
#     Ensures  len(Result()) >= 1
#     Ensures  ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))   <-- LOAD-BEARING
#     Ensures  Result()[0] == phase                        <-- THE discriminator
#
#   The bug (issue, Patch.draw): the pre-patch installed dash pattern was
#   (0, self._dash_pattern[1]) — the offset FORCED TO ZERO — so a nonzero stored
#   offset had no rendering effect. The fix installs self._dash_pattern, carrying
#   the offset through. The discriminator is Result()[0] == phase (head = the
#   stored offset, NOT the literal 0). model_prepatch.py reproduces result=[0]
#   and FAILS exactly that clause whenever phase != 0. The F2P test exercises
#   phase = 6 (a (6,[6,6]) patch must render like a (0,[0,6,6,0]) patch).
#
#   GROUNDED ORACLE, not an answer-key: the load-bearing postcondition pins
#   Result() to PSeq(phase) + Old(ToSeq(onoff)) — a value built ENTIRELY from the
#   two args, fully unfolded; there is NO opaque @Pure marker to echo. So the
#   "ungrounded-oracle echo" class is N/A here (see 'assessment'); the cheapest
#   honest impl IS the gold [phase] + onoff concatenation, so its positive control
#   is a local-variable reshape, not an echo.
#
#   No @ContractOnly axioms and no A-reference deep models (meta.axioms == [],
#   deep_model_references == []): the change is pure tuple construction from
#   values already held on the object — no library callee to axiomatize. Hence
#   AXIOM_TESTS = []. See 'assessment'.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23412"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchor INSIDE the single impl region (between # impl-start / # impl-end).
# Editing only this body keeps spec_view (hence same_spec) byte-identical: the
# whole impl body — including the nested invariants region — is elided by
# spec_view, so loop shape / invariants / asserts are all impl-region surgery.
# The gold impl body is the unique anchor.
# ===========================================================================
_IMPL_GOLD = """    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: render_dash_pattern body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Local-variable reshape: bind the phase into a named local `head` first and seed
# the result from it (result = [head], head == phase) — a genuinely different impl
# shape from gold's result = [phase]. Keep the forward append direction so NO fold
# lemma is introduced (directive 3). Every still-needed gold proof obligation is
# kept verbatim (the per-element take Assert, the sequence/length invariants, the
# exit take==full Assert). NOTE: the two Acc(...) permission invariants are kept
# FIRST, ahead of any len(result)/ToSeq(result)/take(i) use — in Nagini's
# separation-logic loop invariants the permission grant must textually precede the
# expressions that consume it (invariant order is NOT immaterial for permission-
# bearing conjuncts; an out-of-order len(result) raises "precondition of len might
# not hold / insufficient permission"). Same observable value as gold. Must verify,
# else SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    head = phase  # type: int
    result = [head]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result"""

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the half-permission `onoff` is
# usable (read its length / its elements via ToSeq, append each element) and
# reach a NORMAL non-raising return — exactly an F2P-shaped run (phase != 0,
# nonempty onoff). If the Requires Acc(list_pred(onoff),1/2) were vacuous or
# over-strong, the impl could not both consume the half-permission AND return =>
# PRECOND-TOO-STRONG. (Adds only readable Asserts in-region; the build is gold.)
# ===========================================================================
_IMPL_ADMISS = """    result = [phase]  # type: List[int]
    # admissibility: the half-permission onoff input is usable (length + ToSeq
    # readable) and a normal (non-raising) return is reachable for a typical
    # F2P-shaped run.
    Assert(len(onoff) >= 0)
    Assert(ToSeq(onoff) == Old(ToSeq(onoff)))
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    Assert(len(result) == len(onoff) + 1)
    return result"""

# ===========================================================================
# (3) FRAME-MUTATION — write to the read-only input `onoff` (reject). MANDATORY.
# render_dash_pattern holds only Acc(list_pred(onoff), 1/2). Inside the loop the
# index onoff[i] is known in-bounds (0 <= i < len(onoff)), so a value-NEUTRAL
# write onoff[i] = onoff[i] is well-typed — yet a list-element write needs FULL
# permission. With only the half-permission the Requires grants, Nagini rejects
# for INSUFFICIENT PERMISSION. The gold invariants/asserts are kept VERBATIM so
# the rejection is attributable to the write, not to a spec change. A byte-fuzzer
# never thinks to mutate the read-only input — this is the #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        # FRAME MUTATION: write back into the read-only half-permission input.
        onoff[i] = onoff[i]
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result"""

# ===========================================================================
# (4) HEAD-ZERO / pre-patch bug — partial-domain on phase (reject). THIS IS THE
# pre-patch behaviour (model_prepatch.py): seed the head with the literal 0
# instead of the stored phase — exactly the old (0, self._dash_pattern[1])
# install. It agrees with the fix when phase == 0, but DROPS the offset on the
# phase != 0 sub-domain. The load-bearing Result()[0] == phase (and the head of
# ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))) therefore fails. The
# invariant is restated truthfully for the [0]-seeded build (head 0, tail onoff),
# so the loop verifies and the POSTCONDITION is what rejects — a spec reason.
# ===========================================================================
_IMPL_HEADZERO = """    result = [0]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(0) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result"""

# ===========================================================================
# (5) DROP-LAST on/off element — partial-domain on the tail (reject). Loop bound
# `while i < len(onoff) - 1` renders the phase plus all but the LAST on/off
# element. On an EMPTY onoff (len-1 == -1) the loop never runs and the result is
# correct — so it is correct on the empty/solid sub-domain but DROPS the last
# ink-length on every nonempty run. At exit i == len(onoff) - 1 (nonempty), so
# len(result) == len(onoff), violating len(Result()) == len(onoff) + 1 (and the
# tail of the load-bearing sequence equality). The invariant is restated
# truthfully for the shorter build, so the loop verifies and the POSTCONDITION
# rejects — a spec reason.
# ===========================================================================
_IMPL_DROPLAST = """    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff) - 1:
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        Invariant(MustTerminate(len(onoff) - i + 1))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    return result"""

# ===========================================================================
# (6) TAIL-CONSTANT (append the phase value instead of the on/off element) —
# value-double-mask on the on/off passthrough (reject). Head correct (phase) and
# length correct (len(onoff)+1), so the Result()[0] == phase, len, and >=1
# clauses ALL hold — only the load-bearing ToSeq(Result()) == PSeq(phase) +
# Old(ToSeq(onoff)) catches it, because the tail is PSeq(phase) repeated rather
# than the stored on/off sequence. We keep only the length/permission invariants
# (true for this build) and drop the gold sequence invariant (it is false for the
# corrupted build); the impl genuinely produces a wrong value, so no invariant
# could rescue it — the verifier cannot establish the sequence postcondition and
# rejects. On the F2P input (phase 6, onoff [6,6]) the corrupted tail [6,6]
# happens to coincide (6 == the element value), so the F2P alone is BLIND to this
# corruption — only the spec's verbatim onoff-passthrough clause catches it,
# which is exactly the value the uniqueness lane adds over the test.
# ===========================================================================
_IMPL_TAILCONST = """    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(len(result) >= 1 and result[0] == phase)
        # invariants-end
        result.append(phase)
        i = i + 1
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the phase is bound into a "
                     "named local `head` and the result is seeded from it "
                     "(result = [head], head == phase) — a different impl shape from "
                     "gold's result = [phase]. The forward append direction is kept "
                     "(NO fold lemma introduced, directive 3), and every still-needed "
                     "gold proof obligation is kept verbatim (the per-element take "
                     "Assert, the sequence + length invariants, the exit take==full "
                     "Assert). The two Acc(...) permission invariants are kept first, "
                     "ahead of the len/ToSeq uses, because Nagini's separation-logic "
                     "loop invariants require the permission grant to textually precede "
                     "expressions consuming it (order is NOT immaterial for permission-"
                     "bearing conjuncts). Same observable value as gold. Must verify, "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-onoff",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that the half-permission onoff input is "
                     "usable (its length and ToSeq are readable, each element is "
                     "appended) and reaches a normal non-raising return for an "
                     "F2P-shaped run (phase != 0, nonempty onoff). If the Requires "
                     "Acc(list_pred(onoff),1/2) were vacuous or over-strong the impl "
                     "could not both consume the half-permission and return => "
                     "PRECOND-TOO-STRONG. Source: the Acc(list_pred(onoff),1/2) "
                     "Requires.",
    },
    {
        "id": "frame-mutation-write-onoff",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which Patch.draw built the installed "
                      "_dash_pattern by writing back into self._dash_pattern[1] (the "
                      "stored on/off sequence) — e.g. mutating the list in place to "
                      "stage the render value — would corrupt the patch's own stored "
                      "dash pattern for the rest of its lifetime (cbook._setattr_cm is "
                      "supposed to RESTORE the original after draw). Subsequent draws "
                      "and the get_linestyle() assertions in the F2P "
                      "(rect_test.get_linestyle() == (0, [6, 6])) would see the "
                      "mutated sequence, so the faithful patch would NOT resolve "
                      "test_dash_offset_patch_draw — the stored on/off sequence must "
                      "be read-only.",
        "rationale": "render_dash_pattern holds only Acc(list_pred(onoff), 1/2). The "
                     "value-neutral element write onoff[i] = onoff[i] (in-bounds via "
                     "the loop bound) needs FULL list permission => Nagini rejects for "
                     "INSUFFICIENT PERMISSION. Gold invariants/asserts kept verbatim so "
                     "the rejection is attributable to the write. Source: the "
                     "permission system + the Acc(list_pred(onoff),1/2) Requires.",
    },
    {
        "id": "head-zero-prepatch-offset-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_HEADZERO),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): seed the "
                      "render-time head with the literal 0, exactly the old "
                      "_dash_pattern=(0, self._dash_pattern[1]) install. For the F2P "
                      "scenario a (6, [6, 6]) patch would render with offset 0, i.e. "
                      "identically to a (0, [6, 6]) patch — NOT like the offset-shifted "
                      "(0, [0, 6, 6, 0]) reference. check_figures_equal would see "
                      "different images, so test_dash_offset_patch_draw FAILS — the "
                      "faithful (pre-patch) code does not resolve.",
        "rationale": "result is seeded [0], so Result()[0] == 0 != phase whenever "
                     "phase != 0, and the head of ToSeq(Result()) == PSeq(phase) + "
                     "Old(ToSeq(onoff)) is 0 not phase. Both load-bearing clauses fail "
                     "on the phase != 0 sub-domain (the F2P uses phase 6). The "
                     "invariant is restated truthfully for the [0]-seed so the loop "
                     "verifies; the POSTCONDITION rejects. Source: Result()[0] == phase "
                     "and the head of the sequence postcondition.",
    },
    {
        "id": "drop-last-onoff-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DROPLAST),
        "refinement": "A faithful real patch that installed (offset, onoffseq[:-1]) — "
                      "dropping the last ink-length — would hand the renderer a "
                      "different dash pattern (one ink segment short) for every "
                      "nonempty on/off sequence. A (6, [6, 6]) patch would render with "
                      "on/off [6] instead of [6, 6], producing a visibly different "
                      "dashing from the (0, [0, 6, 6, 0]) reference, so "
                      "check_figures_equal FAILS and the patch does not resolve. (It "
                      "agrees on the empty/solid case, so it is a true partial-domain "
                      "miss on the nonempty sub-domain.)",
        "rationale": "Loop bound `while i < len(onoff) - 1` ends with i == len(onoff)-1 "
                     "on a nonempty onoff, so len(result) == len(onoff), violating "
                     "len(Result()) == len(onoff) + 1 (and the tail of the sequence "
                     "equality). The invariant is restated truthfully for the shorter "
                     "build so the loop verifies; the POSTCONDITION rejects. Source: "
                     "len(Result()) == len(onoff) + 1 and the sequence postcondition.",
    },
    {
        "id": "tail-constant-onoff-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_TAILCONST),
        "refinement": "A faithful real patch that built the render-time on/off "
                      "sequence from the offset value (filling every ink length with "
                      "the offset rather than copying self._dash_pattern[1]) would hand "
                      "the renderer a corrupted dash pattern on any patch whose on/off "
                      "sequence differs from a constant-offset run. For the workaround "
                      "reference (0, [0, 6, 6, 0]) the equivalence the F2P asserts "
                      "would break, so the patch does not resolve. NOTE: on the exact "
                      "F2P input (phase 6, onoff [6, 6]) the corrupted tail [6, 6] "
                      "coincides with the real one (6 == element value), so the F2P "
                      "test alone is BLIND to this corruption — only the spec's "
                      "verbatim onoff-passthrough clause catches it.",
        "rationale": "result appends the phase value, not onoff[i], so the tail is "
                     "PSeq(phase) repeated rather than the stored on/off sequence. Head "
                     "(phase), length (len(onoff)+1) and >=1 ALL still hold (kept as "
                     "true invariants), so only the load-bearing ToSeq(Result()) == "
                     "PSeq(phase) + Old(ToSeq(onoff)) catches it; the gold sequence "
                     "invariant (false for this build) is dropped, and no invariant "
                     "could establish a wrong value, so the verifier cannot discharge "
                     "the sequence postcondition and rejects. Source: the on/off "
                     "passthrough clause of the sequence postcondition.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] and deep_model_references == [] — the
# change is pure tuple construction from values already held on the patch
# (self._dash_pattern[0], self._dash_pattern[1]); it calls no library/utility
# routine, so there is no @ContractOnly axiom and no A-reference deep model to
# validate against a real callee (G-AX is vacuous; there is no axiom_check.py).
# Hence nothing for the axiom lane to run. See 'assessment' in the structured
# return.
AXIOM_TESTS = []
