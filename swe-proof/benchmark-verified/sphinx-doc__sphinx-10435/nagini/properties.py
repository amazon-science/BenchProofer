# properties.py — PBT manifest for sphinx-doc__sphinx-10435.
#
# NOT a Nagini module. A record of adversarially-reasoned falsification cases the
# runner (swebench_nagini.pbt) executes against the FROZEN spec in model.py.
# Every spec case is a full model.py whose ONLY edit is inside the
# # impl-start .. # impl-end region (spec_view elides it), so same_spec holds
# byte-for-byte against the frozen spec; the surgery is performed by _swap on
# anchors that live exclusively inside that region.
#
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py):
#   assemble_inline_code(content: List[int]) -> List[int]
#
#   Requires(Acc(list_pred(content), 1/2))            # content is READ-ONLY
#   Requires(len(content) > 0)
#   Requires(content[len(content)-1] != cp_break())   # tail is not a line-break
#   Ensures(Acc(list_pred(content), 1/2))             # frame: caller keeps half
#   Ensures(Acc(list_pred(Result())))
#   Ensures(ToSeq(Result()) ==                        # << LOAD-BEARING master pin
#       open_wrap() + PSeq(cp_suppress()) + PSeq(cp_break()) + ToSeq(content)
#       + PSeq(cp_suppress()) + PSeq(cp_break()) + close_wrap())
#   Ensures(Result()[len(open_wrap())]     == cp_suppress())   # opening '%'
#   Ensures(Result()[len(open_wrap())+1]   == cp_break())      # opening '\n'
#   Ensures(Result()[len(Result())-len(close_wrap())-2] == cp_suppress()) # close '%'
#   Ensures(Result()[len(Result())-len(close_wrap())-1] == cp_break())    # close '\n'
#
# READ-ONLY INPUT: `content` is held at Acc(...,1/2) on both Requires and Ensures.
# => the FRAME-MUTATION attack is MANDATORY (frame-mut-write below): an impl that
# WRITES to `content` must be rejected for INSUFFICIENT PERMISSION.
#
# UNGROUNDED-ORACLE: the postcondition oracle is open_wrap()/close_wrap()/
# cp_suppress()/cp_break() — all @Pure TOTAL constants fully unfolded, plus
# ToSeq(content) which is the literal input. The master clause is a GROUNDED
# function of the args + fixed literals; there is no opaque answer-key to echo
# without doing the work (materialising the concatenation literally IS the work).
# So there is no WRONG-echo attack. We instead supply an honest cheapest-impl
# positive control (pos-control-split) and document this in 'assessment'.
#
# CONTROL-FLOW-EFFECT: the modeled function is a pure value producer (returns a
# List[int]; no raise/side-effect distinguishes correct outputs that the value
# abstraction misses). The real writer raises nodes.SkipNode unconditionally on
# this path regardless of the assembled string, so there is no value-invisible
# control-flow effect to discriminate. Class N/A (see 'assessment').
#
# AXIOMS: meta.json axioms == []; the changed string surgery is an A-reference
# deep model (validated by axiom_check.py / G-AX), NOT a consumed @ContractOnly
# axiom, and there is no caller-reachable callee outside an axiom domain. So
# AXIOM_TESTS == [].

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10435"
FLOAT_ENCODING = None  # meta.json float_encoding is null (pure sequence surgery)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors that live EXCLUSIVELY inside the # impl-start .. # impl-end region.
# Each is unique in _BASE (asserted below), so _swap edits only the impl.
_A_COPY = "result = result + [content[k]]"           # the content copy-loop body
_A_SUFFIX = "result = result + [pct, br, 125, 125]"  # append '%','\n','}}'
_A_RETURN = "    return result"
_A_LOOPHEAD = "while k < len(content):"
_A_PRECOPY = "    # copy the content"                # 4-space indent, before k=0

for _a in (_A_COPY, _A_SUFFIX, _A_RETURN, _A_LOOPHEAD, _A_PRECOPY):
    assert _BASE.count(_a) == 1, f"impl anchor drifted: {_a!r}"


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY — content is Acc(...,1/2) read-only). expect=reject
# ---------------------------------------------------------------------------
# A rival that WRITES to the read-only input `content` (here: overwrite its first
# code point with the suppressor before the copy loop). With only HALF permission
# this is illegal — Nagini rejects the assignment for INSUFFICIENT PERMISSION,
# never reaching the postcondition. The gold invariants/asserts are kept verbatim
# so the rejection is attributable to the write, not a broken proof.
#
# refinement: the writer's `content` is the upstream-highlighted code body; the
# real surgery only READS it (substitutes the wrapper, strips the trailer). A
# faithful patch that mutated the highlighted body would corrupt `common_content`,
# and the F2P test (test_latex_code_role) matches `common_content` VERBATIM as a
# substring of python.tex — so a mutating patch would NOT resolve. A rival that
# verified here despite writing to content would be a true verify⇏resolve break.
# Inserted BEFORE the copy loop (4-space indent, where a normal statement lives).
_FRAME_MUT = """    content[0] = pct  # ILLEGAL write to a 1/2-permission input
""" + _A_PRECOPY
SPEC_FRAME_MUT = _swap(_BASE, _A_PRECOPY, _FRAME_MUT)


# ===========================================================================
# 2. PARTIAL-DOMAIN — drop the TRAILING suppressor only. expect=reject
# ---------------------------------------------------------------------------
# Emits the opening '%' correctly but appends [br, 125, 125] (a bare line-break
# then '}}') with NO trailing '%'. This is exactly the pre-patch bug on the
# CLOSING side. Rejected by the master equality (which pins '%' before the
# closing break) and by the offset clause
#   Ensures(Result()[len(Result())-len(close_wrap())-2] == cp_suppress()).
#
# refinement: this is model_prepatch's closing-side defect; the rendered output is
# `...content\n}}` instead of `...content%\n}}`, so the closing line-break renders
# as a spurious trailing space. F2P expects `common_content + '%\\n}}'`; a patch
# producing `common_content + '\\n}}'` fails the substring assertion → not resolve.
_TRAIL_DROP = "result = result + [br, 125, 125]"
SPEC_TRAIL_DROP = _swap(_BASE, _A_SUFFIX, _TRAIL_DROP)


# ===========================================================================
# 3. PARTIAL-DOMAIN — drop the OPENING suppressor only (the full pre-patch). reject
# ---------------------------------------------------------------------------
# Builds the prefix WITHOUT the opening '%' (open_wrap ++ break only) and the
# suffix without the trailing '%' — i.e. the literal pre-patch behaviour
# (model_prepatch.py). Rejected by both offset pins (opening '%' absent) and the
# master equality. The whole prefix literal must be rebuilt without `pct`, so we
# swap the suffix AND the asserted prefix line is replaced by a no-suppressor
# prefix. We edit only inside impl by swapping the prefix-construction block.
_GOLD_PREFIX = """    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, pct, br]  # type: List[int]
    Assert(ToSeq(result) == open_wrap() + PSeq(pct) + PSeq(br))"""
assert _BASE.count(_GOLD_PREFIX) == 1, "gold prefix block drifted"
# pre-patch prefix: open_wrap ++ break, NO suppressor; invariant must match so we
# also drop pct from the loop invariant... but the loop invariant lives in impl
# (between impl-start/impl-end) so editing it is still same_spec. We rebuild the
# whole loop region to the no-opening-suppressor shape.
_PREPATCH_IMPL_PREFIX = """    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, br]  # type: List[int]
    Assert(ToSeq(result) == open_wrap() + PSeq(br))"""
_PREPATCH_INV = """        Invariant(ToSeq(result) ==
                  open_wrap() + PSeq(pct) + PSeq(br) + ToSeq(content).take(k))"""
assert _BASE.count(_PREPATCH_INV) == 1, "gold loop invariant drifted"
_PREPATCH_INV_NEW = """        Invariant(ToSeq(result) ==
                  open_wrap() + PSeq(br) + ToSeq(content).take(k))"""
_PREPATCH_SUFFIX = "result = result + [br, 125, 125]"
# build the full pre-patch rival by three impl-region swaps
_tmp = _swap(_BASE, _GOLD_PREFIX, _PREPATCH_IMPL_PREFIX)
_tmp = _swap(_tmp, _PREPATCH_INV, _PREPATCH_INV_NEW)
SPEC_PREPATCH = _swap(_tmp, _A_SUFFIX, _PREPATCH_SUFFIX)


# ===========================================================================
# 4. PARTIAL-DOMAIN — off-by-one on the content copy (drop the LAST code point). reject
# ---------------------------------------------------------------------------
# Copies content[0 .. len-2] instead of content[0 .. len-1] by stopping the loop
# one short. Correct for every content prefix but diverges on the FINAL code
# point. Rejected by the master equality (ToSeq(Result()) pins the FULL
# ToSeq(content)). The loop invariant/final assert are adjusted only inside impl.
#
# refinement: the rendered inline code would drop the last char of the highlighted
# body (e.g. `\\PYG{k}{pass}` -> `\\PYG{k}{pass`), so `common_content` no longer
# matches as a substring → F2P fails → would NOT resolve.
_OFFBYONE_LOOPHEAD = "while k < len(content) - 1:"
_GOLD_FINAL_ASSERT = "Assert(ToSeq(content).take(len(content)) == ToSeq(content))"
assert _BASE.count(_GOLD_FINAL_ASSERT) == 1, "gold final assert drifted"
# stopping one short leaves ToSeq(result) == prefix ++ take(len-1); the master
# equality demands the full content, so the postcondition fails. We change the
# loop bound; the existing invariant (prefix ++ take(k)) still holds at exit with
# k == len-1, and the final assert (take(len)==content) becomes irrelevant but
# harmless. expect=reject from the postcondition equality, not a proof gap.
SPEC_OFFBYONE = _swap(_BASE, _A_LOOPHEAD, _OFFBYONE_LOOPHEAD)


# ===========================================================================
# 5. POSITIVE CONTROL (soundness) — structurally different but CORRECT. expect=verify
# ---------------------------------------------------------------------------
# Splits the single suffix append into TWO appends (first [pct, br], then the two
# close-wrap code points). Keeps the gold loop, its invariants, and the closing
# `Assert(PSeq(125,125)==close_wrap())` so the framing the proof needs is intact
# (avoid-bug #2). No loop-direction flip / no @Pure fold reshape (avoid-bug #3).
# A faithful correct impl with a different append shape MUST verify; if not =>
# SPEC-TOO-STRONG.
_POS_SUFFIX = """result = result + [pct, br]
    result = result + [125, 125]"""
SPEC_POS = _swap(_BASE, _A_SUFFIX, _POS_SUFFIX)


# ===========================================================================
# 6. ADMISSIBILITY — an F2P-shaped in-domain input. expect=verify
# ---------------------------------------------------------------------------
# Inside the impl, a concrete in-domain content (the single code point 'x' ==
# [120]: non-empty, tail != '\n') is built and EVERY Requires conjunct of
# assemble_inline_code is asserted for it. The Asserts keep the spec untouched.
# If a conjunct cannot be established for this normal input =>
# PRECOND-TOO-STRONG. The probe builds its own list so it consumes no permission
# the gold body still needs.
#
# Assert-style rather than the self-call this case used before:
# assemble_inline_code now carries Requires(MustTerminate(2)) (total
# correctness), and Nagini demands a callee's obligation level be STRICTLY below
# its caller's, so an equal-level self-call is rejected by the obligation system
# ("Callee assemble_inline_code might not take all unsatisfied obligations from
# the caller") — an artifact of the termination spec, unrelated to the value
# preconditions this case probes.
_ADMISS = """    witness_in = [120]  # type: List[int]
    # every Requires conjunct of assemble_inline_code, for that input
    Assert(Acc(list_pred(witness_in), 1 / 2))
    Assert(len(witness_in) > 0)
    Assert(witness_in[len(witness_in) - 1] != cp_break())
""" + _A_PRECOPY
SPEC_ADMISS = _swap(_BASE, _A_PRECOPY, _ADMISS)


SPEC_TESTS = [
    {
        "id": "frame-mut-write-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_FRAME_MUT,
        "refinement": (
            "content is the upstream-highlighted code body; the real surgery only "
            "READS it. A faithful patch that wrote into the highlighted body would "
            "corrupt common_content, which the F2P test matches VERBATIM as a "
            "substring of python.tex — so a mutating patch would NOT resolve."),
        "rationale": (
            "content is held at Acc(list_pred(content),1/2) (read-only) on both "
            "Requires and Ensures; `content[0] = pct` requires FULL permission, so "
            "Nagini rejects for INSUFFICIENT PERMISSION before the postcondition. "
            "If it verified, the spec would admit a frame-mutating impl => "
            "SPEC-TOO-WEAK. (#1 weakness class; a byte-fuzzer never tries this.)"),
    },
    {
        "id": "partial-drop-trailing-suppressor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_TRAIL_DROP,
        "refinement": (
            "this is the pre-patch CLOSING-side bug: output is `...content\\n}}` "
            "not `...content%\\n}}`, so the closing line-break renders as a spurious "
            "trailing space. F2P expects common_content + '%\\n}}'; producing "
            "common_content + '\\n}}' fails the substring assert => NOT resolve."),
        "rationale": (
            "rejected by the master equality (pins cp_suppress before the closing "
            "break) and by Ensures(Result()[len-len(close_wrap())-2]==cp_suppress())."),
    },
    {
        "id": "prepatch-no-suppressors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_PREPATCH,
        "refinement": (
            "literal pre-patch behaviour (model_prepatch.py): open_wrap++break++"
            "content++break++}} with NEITHER '%'. Both adjacent breaks render as "
            "spurious spaces. F2P expects `\\sphinxcode{\\sphinxupquote{%\\n` and "
            "`%\\n}}`; the pre-patch produces `{\\n` and `\\n}}` => fails => NOT "
            "resolve (this is exactly the bug the gold patch fixes)."),
        "rationale": (
            "rejected by BOTH offset pins (opening '%' absent at len(open_wrap), "
            "closing '%' absent) and the master equality. The loop invariant is "
            "edited inside impl to the no-opening-suppressor shape so the rejection "
            "is the POSTCONDITION failing, not a proof gap."),
    },
    {
        "id": "partial-offbyone-drop-last-codepoint",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SPEC_OFFBYONE,
        "refinement": (
            "copies content[0..len-2], dropping the LAST highlighted code point "
            "(e.g. `\\PYG{k}{pass}` -> `\\PYG{k}{pass`). common_content no longer "
            "matches as a substring of python.tex => F2P fails => NOT resolve."),
        "rationale": (
            "rejected by the master equality which pins the FULL ToSeq(content); "
            "stopping the loop one short leaves ToSeq(content).take(len-1) so the "
            "concatenation is shorter than required. Correct on every prefix, wrong "
            "on the final element => partial-domain."),
    },
    {
        "id": "pos-control-split-suffix",
        "kind": "soundness",
        "expect": "verify",
        "module": SPEC_POS,
        "rationale": (
            "structurally-different but CORRECT: the single suffix append is split "
            "into two appends ([pct,br] then [125,125]); the gold loop, invariants "
            "and the close_wrap framing assert are kept verbatim. A faithful correct "
            "impl of a different append shape MUST verify, else SPEC-TOO-STRONG."),
    },
    {
        "id": "admissibility-selfcall-fshaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": SPEC_ADMISS,
        "rationale": (
            "the F2P-shaped content [120] ('x': len>0, tail!='\\n') is built and "
            "EVERY Requires conjunct of assemble_inline_code is asserted for it "
            "(Acc(list_pred(content),1/2), len>0, tail!=cp_break()). The probe "
            "builds its own list so it consumes no permission the gold body still "
            "needs. If a conjunct could not be established for this normal input => "
            "PRECOND-TOO-STRONG. Assert-style rather than a self-call: under "
            "Requires(MustTerminate(2)) an equal-level recursive self-call is "
            "rejected by the obligation system, an artifact unrelated to the value "
            "preconditions."),
    },
]

AXIOM_TESTS = []  # meta.json axioms == []; the string surgery is an A-reference
# deep model (G-AX / axiom_check.py), not a consumed @ContractOnly axiom, and no
# caller-reachable callee lies outside an axiom domain — nothing to probe here.
