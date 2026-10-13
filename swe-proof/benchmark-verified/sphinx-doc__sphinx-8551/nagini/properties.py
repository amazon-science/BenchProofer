"""properties.py — PBT falsification battery for sphinx-doc__sphinx-8551.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap) and are checked by Nagini
verify + markers.same_spec. There are NO @ContractOnly axioms consumed in this
bundle (meta.axioms == []; the resolver is modelled DEEPLY in the pure region as
resolve_count/resolve_name and validated == the real find_obj out-of-band by
axiom_check.py / G-AX), so AXIOM_TESTS = [].

=========================================================================
DEFENDED SURFACE  (why these cases, not byte-fuzz)
=========================================================================
Modeled function:

    make_field_ref(target, cur_module, cur_class, objs) -> RefNode

building the implicit info-field type xref node that must carry the surrounding
(module, class) namespace context.  The impl region is two lines:

    node = RefNode(target, True, cur_module, cur_class)
    return node

PRECONDITION (the F2P "ambiguous unqualified name" scenario):
    - cur_module is not None
    - member(objs, cur_module + target)                  # module-qualified obj exists
    - Implies(cur_class is not None,
              not member(objs, cur_module + cur_class + target))   # no class-nested obj
    - not member(objs, target)                           # bare target NOT registered
    - count_suffix(objs, target) >= 2                    # suffix fallback is AMBIGUOUS

POSTCONDITION — the load-bearing clauses:
    (P1) Result().target is target          # identity
    (P2) Result().specific                  # prefer-specific flag True
    (P3) Result().ctx_mod is cur_module     # LOAD-BEARING: module context recorded (identity)
    (P4) Result().ctx_cls is cur_class      # LOAD-BEARING: class context recorded (identity)
    (P5) resolve_count(ctx_mod, ctx_cls, target, objs) == 1
    (P6) resolve_name (ctx_mod, ctx_cls, target, objs) == cur_module + target

NO READ-ONLY HEAP INPUT (has_readonly_input = False).  target/cur_module/
cur_class are PSeq[int] / Optional[PSeq[int]] and objs is PSeq[PSeq[int]] — pure,
immutable Nagini value carriers that hold NO Acc(...) heap permission at all (the
function's Requires has no Acc clause on any input).  The only heap object is the
*freshly allocated* RefNode the impl creates and writes (full permission, by
construction).  There is therefore no half-permission input cell to overwrite:
the FRAME-MUTATION class is vacuous here — a mutating rival cannot even be
written, because there is no input field to write to.  This is the deliberate
effect of the PSeq carrier (mapping.md S2), so directive 5 is satisfied by
construction rather than by a contract.  frame_mutation N/A; justified in the
returned assessment.

UNGROUNDED-ORACLE ECHO is also vacuous.  resolve_count/resolve_name are @Pure but
they are GROUNDED: total functions of (ctx_mod, ctx_cls, target, objs), fully
unfolded over member/count_suffix/first_suffix, with NO opaque answer-key the
impl could echo.  The impl does not even return their value — it returns a
RefNode whose fields P5/P6 then constrain.  Moreover P5/P6 are ENTAILED by the
field-identity clauses P3/P4/P1 plus the precondition (resolve_* are functions of
exactly those fields and objs), so once the node records the true context the
resolution facts follow.  Equivalently: the only way to satisfy P5/P6 while the
impl can only set the node's fields is to set ctx_mod/ctx_cls to the genuine
context — there is no wrong echo.  Per directive 2 we therefore carry an honest
cheapest-correct positive control instead.

THE GENUINE ATTACKS (uniqueness / partial-domain): rivals that drop or replace a
piece of context, satisfying SOME postcondition clauses but failing the
load-bearing identity/resolution clause — exactly the prepatch defect family
(node built without the (module, class) context, resolution falls to the
ambiguous suffix fallback -> "more than one target found" WARNING).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8551"
FLOAT_ENCODING = None  # meta.float_encoding is null; PSeq[int] token carrier, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The entire gold impl region, anchored on a unique substring, so every variant
# edits ONLY inside # impl-start .. # impl-end (guarantees same_spec). We anchor
# on the two-line body (not the markers) so insert-before-construction variants
# remain inside the region.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    node = RefNode(target, True, cur_module, cur_class)
    return node"""


# === POSITIVE CONTROL 1 (soundness, expect=verify) =========================
# Structurally-different CORRECT impl: bind the prefer-specific flag and the two
# context arguments to local variables first, then construct.  Assignment
# preserves object identity (m is cur_module, c is cur_class), so P3/P4 still
# hold; flag == True so P2 holds; target passed through so P1 holds; P5/P6 follow
# as before.  A pure local-variable reshape that keeps every gold proof
# obligation valid (no fold lemma, no loop, no dropped framing assert -> directives
# 2 & 3 respected).  If a faithful correct impl could not verify => SPEC-TOO-STRONG.
_POS1 = """    flag = True  # type: bool
    m = cur_module  # type: Optional[PSeq[int]]
    c = cur_class  # type: Optional[PSeq[int]]
    node = RefNode(target, flag, m, c)
    return node"""

# === POSITIVE CONTROL 2 (soundness, expect=verify) =========================
# Construct the gold node, then add harmless redundant Assert()s of the
# resolution facts the postcondition already pins (P5/P6).  These are entailed by
# the node fields + precondition, so they verify; the executable shape differs
# (extra proof-only statements) while the returned value is byte-identical to
# gold.  Confirms the spec admits a correct impl that makes the resolution
# reasoning explicit (else SPEC-TOO-STRONG).
_POS2 = """    node = RefNode(target, True, cur_module, cur_class)
    Assert(node.ctx_mod is cur_module and node.ctx_cls is cur_class)
    Assert(resolve_count(node.ctx_mod, node.ctx_cls, node.target, objs) == 1)
    Assert(resolve_name(node.ctx_mod, node.ctx_cls, node.target, objs)
           == cur_module + target)
    return node"""


# === ADMISSIBILITY (precondition not too strong, expect=verify) ============
# Build a CONCRETE F2P-shaped input (the issue scenario: simple name "A" (=3)
# registered under both "mod" (=1) and "mod.submod" (=1,2); current module "mod",
# no class) and self-CALL make_field_ref on it.  The self-call's precondition
# must be discharged for the concrete witness -> that IS the admissibility
# obligation:
#   member(objs, mod+target)        : objs[0] == PSeq(1,3)            -> True
#   not member(objs, target)        : neither obj == PSeq(3)          -> True
#   count_suffix(objs, target) >= 2 : both end with PSeq(3)           -> 2
# We unfold member/count_suffix with explicit Asserts (front-recursive: one
# .drop(1) unfold per element) so the verifier discharges the predicate on the
# 2-element registry without a search.  cur_class = None makes the class-context
# precondition vacuous.  If this could not verify => PRECOND-TOO-STRONG (the
# Requires would be unsatisfiable / contradictory for a normal info-field input).
_ADMISS = """    # admissibility witness (issue scenario): mod=1, submod=2, A=3
    w_target = PSeq(3)  # type: PSeq[int]
    w_mod = PSeq(1)  # type: PSeq[int]
    o0 = PSeq(1, 3)  # type: PSeq[int]
    o1 = PSeq(1, 2, 3)  # type: PSeq[int]
    w_objs = PSeq(o0, o1)  # type: PSeq[PSeq[int]]
    w_cls = None  # type: Optional[PSeq[int]]
    # the module-qualified object exists, the bare target does not
    Assert(w_mod + w_target == o0)
    Assert(w_objs[0] == o0 and w_objs[1] == o1)
    Assert(member(w_objs, w_mod + w_target))
    # unfold member front-recursion over the 2-element registry: neither
    # registered object equals the bare target, so the bare name is not a member
    Assert(o0 != w_target and o1 != w_target)
    Assert(w_objs.drop(1) == PSeq(o1))
    Assert(not member(w_objs.drop(1).drop(1), w_target))
    Assert(not member(w_objs.drop(1), w_target))
    Assert(not member(w_objs, w_target))
    # both registered objects end with the simple name -> suffix fallback >= 2
    Assert(suffix_eq(o0, w_target))
    Assert(suffix_eq(o1, w_target))
    # unfold count_suffix front-recursion: both registered objects' suffix
    # matches the bare name, so the fallback set has >= 2 members
    Assert(count_suffix(w_objs.drop(1).drop(1), w_target) == 0)
    Assert(count_suffix(w_objs.drop(1), w_target) == 1)
    Assert(count_suffix(w_objs, w_target) == 2)
    Assert(count_suffix(w_objs, w_target) >= 2)
    witness = make_field_ref(w_target, w_mod, w_cls, w_objs)
    node = RefNode(target, True, cur_module, cur_class)
    return node"""


# === UNIQUENESS rivals (must be REJECTED) ==================================

# --- weak-prepatch-module: THE gold bug (joint hunk A+B, module half).  Drop the
# module context: build the node with ctx_mod = None.  This is exactly the
# prepatch state (make_xref omits result['py:module'] / transform omits env=).
# FAILS P3 (None is not cur_module, and cur_module is not None) AND P5/P6 (with
# ctx_mod None the resolve cascade skips every qualified branch and falls to the
# suffix fallback, count_suffix(objs,target) >= 2 != 1).  expect=reject.
_REJ_DROP_MOD = """    node = RefNode(target, True, None, cur_class)
    return node"""

# --- weak-prepatch-class: drop the class context (ctx_cls = None).  Mirrors the
# patch omitting result['py:class'].  FAILS P4 whenever cur_class is not None
# (None is not cur_class).  This is a PARTIAL-DOMAIN rival: it is *correct on the
# sub-domain cur_class is None* (None is None) but wrong on the
# cur_class-is-present sub-domain the F2P exercises (the issue registers a class
# context "Class").  expect=reject.
_REJ_DROP_CLS = """    node = RefNode(target, True, cur_module, None)
    return node"""

# --- weak-flag: drop the prefer-specific flag (specific = False).  Mirrors NOT
# setting result['refspecific'] = True.  FAILS P2 (Result().specific).  Without
# refspecific the real resolve_xref runs find_obj in searchmode 0 (the
# non-prefer-specific path), a different resolution entirely.  expect=reject.
_REJ_FLAG = """    node = RefNode(target, False, cur_module, cur_class)
    return node"""

# --- weak-target-qualify: "resolve-by-rewriting-the-target".  Instead of
# recording the context and leaving the unqualified target, pre-qualify the
# target to cur_module + target and drop the context (ctx_mod=None,
# ctx_cls=None).  A real patch could rewrite reftarget to the fully-qualified
# name rather than attaching py:module/py:class.  This satisfies the RESOLUTION
# intent in spirit but FAILS P1 (Result().target is cur_module+target, not the
# original target) AND P3 (ctx_mod None is not cur_module).  Refinement below
# explains why the faithful patch would NOT resolve the F2P.  expect=reject.
_REJ_QUALIFY = """    node = RefNode(cur_module + target, True, None, None)
    return node"""


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS1),
        "rationale": "structurally-different but correct: bind flag/context to "
                     "locals (identity preserved) then construct. P1-P6 still "
                     "hold. If it cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-explicit-resolve-asserts",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS2),
        "rationale": "gold node + redundant Asserts of the resolution facts P5/P6 "
                     "(entailed by the field-identity clauses + precondition); "
                     "returned value byte-identical to gold. Must verify else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-issue-scenario",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "self-call make_field_ref on a concrete F2P-shaped witness "
                     "(mod.A + mod.submod.A, target A, module mod, no class); the "
                     "self-call's precondition (member / not-member / "
                     "count_suffix>=2) is discharged via explicit fold-unfold "
                     "Asserts. If unsatisfiable => PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-drop-module",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_DROP_MOD),
        "refinement": "The faithful real patch is make_xref WITHOUT "
                      "result['py:module'] = env.ref_context.get('py:module') "
                      "(the prepatch state). find_obj then receives modname=None, "
                      "skips the module.name branch, and falls to the suffix "
                      "('fuzzy') fallback, which returns >=2 matches "
                      "(mod.A AND mod.submod.A) -> the 'more than one target found "
                      "for cross-reference A' WARNING. F2P test_info_field_list "
                      "asserts the pending_xref resolves to the single contextual "
                      "object and carries py:module='example'; it FAILS. So a "
                      "verifying drop-module rival would be a true verify-not-resolve break.",
        "rationale": "rejection from P3 (Result().ctx_mod is cur_module; None is "
                     "not the non-None cur_module) and P5/P6 (ctx_mod None -> "
                     "suffix fallback, resolve_count == count_suffix(objs,target) "
                     ">= 2 != 1). If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-drop-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_DROP_CLS),
        "refinement": "The faithful real patch omits "
                      "result['py:class'] = env.ref_context.get('py:class'); the "
                      "node then carries no class context. The F2P scenario "
                      "registers a current class (py:class) and asserts the "
                      "produced pending_xref carries py:class='Class'; with the "
                      "class context dropped that attribute is None and the "
                      "assertion FAILS. (Correct only on the cur_class-is-None "
                      "sub-domain; the F2P exercises a present class.) "
                      "A verifying drop-class rival would be verify-not-resolve.",
        "rationale": "PARTIAL-DOMAIN: rejection from P4 (Result().ctx_cls is "
                     "cur_class; None is not cur_class when cur_class present). "
                     "If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-drop-specific-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_FLAG),
        "refinement": "A patch that does not set result['refspecific'] = True "
                      "leaves the node WITHOUT the refspecific marker, so "
                      "resolve_xref computes searchmode = 0 (find_obj line 1297) "
                      "and the prefer-specific module/class cascade never runs at "
                      "all; the unqualified name resolves by the non-specific "
                      "path, not to the contextual object. The F2P's expected "
                      "single contextual resolution does not occur -> test FAILS. "
                      "A verifying flag-dropped rival would be verify-not-resolve.",
        "rationale": "rejection from P2 (Result().specific). If it verifies => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-pre-qualify-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_QUALIFY),
        "refinement": "An alternative 'fix' that rewrites the reftarget to the "
                      "fully-qualified cur_module + target (instead of attaching "
                      "py:module/py:class context) changes the observable node: "
                      "the F2P asserts the pending_xref keeps the ORIGINAL "
                      "unqualified reftarget AND carries py:module/py:class; a "
                      "rewritten reftarget with no context fails those assertions "
                      "and also breaks every other unqualified xref that legitimately "
                      "should fuzzy-match. So the faithful patch would NOT resolve "
                      "the F2P.",
        "rationale": "rejection from P1 (Result().target is target; "
                     "cur_module + target is a fresh sequence, not the input "
                     "target) and P3 (ctx_mod None is not cur_module). If it "
                     "verifies => SPEC-TOO-WEAK.",
    },
]

# No @ContractOnly axioms are consumed (meta.axioms == []); the resolver is an
# A-reference deep model (resolve_count/resolve_name) validated == the real
# PythonDomain.find_obj(searchmode=1) out-of-band by axiom_check.py / G-AX
# (issue scenario + 20000 fuzz + exhaustive subset, 0 mismatches). The spec view
# consumes the deep model's @Pure definitions directly (fully unfolded, not via an
# Ensures), so there is no axiom obligation to probe in this lane.
AXIOM_TESTS = []
