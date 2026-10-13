# properties.py — PBT falsification battery for sympy__sympy-13615.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of complement_finite for a new
# body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the ENTIRE impl region — markers
# inclusive, the nested `invariants` block included (markers.spec_view) — so
# same_spec is GUARANTEED for every case regardless of the impl/invariant shape.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json)
# ---------------------------------------------------------------------------
# complement_finite(other: List[int]) -> Tuple[List[int], List[int]] models the
# FiniteSet branch of the gold Set._complement patch: a three-way partition of a
# finite collection by a three-valued membership verdict
#     verdict(el) in {DEFINITELY_OUT=0, DEFINITELY_IN=1, UNDECIDED=2}
# (the unchanged self.contains collapsed by the patch's ternary_sift). It returns
# (survivors, pending):
#   * survivors  = Result()[0] = the DEFINITELY-OUT elements, in input order
#   * pending    = Result()[1] = the UNDECIDED elements, in input order
#   * DEFINITELY-IN elements appear in NEITHER list.
#
# LOAD-BEARING postcondition clauses (the things an impl must satisfy):
#   (P0a) Acc(list_pred(other), 1/2)            — `other` is READ-ONLY (half perm,
#                                                  Required AND Ensured)
#   (P0b) Acc(list_pred(Result()[0]))           — survivors fully owned
#   (P0c) Acc(list_pred(Result()[1]))           — pending fully owned
#   (P1)  ToSeq(Result()[0]) == keep_out(ToSeq(other))        [survivors pin]
#   (P2)  ToSeq(Result()[1]) == keep_undecided(ToSeq(other))  [pending pin — THE FIX]
# keep_out / keep_undecided are @Pure front-recursive folds that select EXACTLY
# the verdict-0 (resp. verdict-2) elements of ToSeq(other), in order. They are
# FULLY GROUNDED in the input handles (the only opaque ingredient is `verdict`,
# whose ONLY contract is the range {0,1,2}); they are NOT an opaque answer-key
# equated to Result(). So there is NO "wrong ungrounded-oracle echo" to build:
# `return ... ` cannot echo a constant — the result must be PRODUCED by selecting
# the input elements whose verdict is 0 (resp. 2). We say so in 'assessment' and
# stand structurally-different + honest-cheapest positive controls in its place
# (PBT_PLAN §2.2, directive 2).
#
# The discriminating F2P behaviour (test_Complement, issue 12712):
#     Complement(FiniteSet(x, y, 2), Interval(-10, 10)) ==
#         Complement(FiniteSet(x, y), Interval(-10, 10))
# Here x, y are UNDECIDED (symbol membership in an interval is unevaluated) and 2
# is DEFINITELY-OUT (2 not in [-10,10] is False... actually 2 IS in [-10,10] so 2
# is DEFINITELY-IN — dropped). x, y must be carried in the SEPARATE pending
# collection (the symbolic Complement), never folded into the bare survivors
# FiniteSet. The pre-patch single comprehension
#     FiniteSet(*[el for el in other if self.contains(el) != True])
# placed BOTH the DEFINITELY-OUT and the UNDECIDED elements in ONE concrete
# FiniteSet and produced no pending collection — silently asserting that the
# UNDECIDED x, y are NOT members. model_prepatch.py reproduces that (if v !=
# DEFINITELY_IN: out=[e]+out; undecided left empty) and FAILS P1 (survivors then
# contain the verdict-2 elements keep_out excludes) — exactly the spec sensing the
# change (G-DIFF). Any rival that folds an UNDECIDED element into survivors, or
# drops it from pending, reproduces this exact bug and would NOT resolve the F2P.
#
# READ-ONLY INPUT (Acc(list_pred(other),1/2)) -> FRAME-MUTATION IS MANDATORY:
#   `other: List[int]` is held at HALF permission in BOTH Requires and Ensures.
#   complement_finite only READS other (indexing other[i-1]); it returns the
#   half-permission unchanged. An impl that WRITES other (append / index-assign /
#   del) holds only Acc(list_pred(other),1/2) and MUST be rejected for
#   INSUFFICIENT PERMISSION, not a value mismatch. A byte-fuzzer never thinks to
#   mutate the input; this is the project's #1 weakness class (frame-mutation
#   cases below).
from pathlib import Path

INSTANCE = "sympy__sympy-13615"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of complement_finite (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly — only the body (and its nested invariants) between them changes, and
# spec_view elides ALL of it (same_spec guaranteed).
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace complement_finite's whole impl block with a new body.
    `body_lines` is the source BETWEEN the markers (no markers); we wrap it back
    in the exact `# impl-start` / `# impl-end` markers so the region is intact.
    Indentation is 4 spaces (function body level)."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The gold impl body, verbatim (between the markers), reused as the baseline
# shape for the frame-mutation rivals (so a rejection is attributable SOLELY to
# the illegal write, not a value mismatch) and the admissibility probe.
_GOLD_BODY = (
    "    out = []  # type: List[int]\n"
    "    undecided = []  # type: List[int]\n"
    "    i = len(other)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other), 1 / 2))\n"
    "        Invariant(Acc(list_pred(out)))\n"
    "        Invariant(Acc(list_pred(undecided)))\n"
    "        Invariant(0 <= i and i <= len(other))\n"
    "        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))\n"
    "        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))\n"
    "        # invariants-end\n"
    "        e = other[i - 1]\n"
    "        Assert(ToSeq(other).drop(i - 1)[0] == e)\n"
    "        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))\n"
    "        v = verdict(e)\n"
    "        if v == DEFINITELY_OUT:\n"
    "            out = [e] + out\n"
    "        elif v == UNDECIDED:\n"
    "            undecided = [e] + undecided\n"
    "        i = i - 1\n"
    "    Assert(ToSeq(other).drop(0) == ToSeq(other))\n"
    "    return out, undecided\n"
)


SPEC_TESTS = [

    # ===================================================================
    # SOUNDNESS — positive controls (must VERIFY; else SPEC-TOO-STRONG)
    # ===================================================================

    # POS-CONTROL 1 (branch-reorder reshape). A structurally-DIFFERENT but
    # CORRECT impl: the two membership branches are written in the OPPOSITE order
    # (UNDECIDED tested first, then DEFINITELY_OUT) and as two independent `if`s
    # rather than one if/elif. Same backward walk + front-prepend (so the
    # front-recursive keep_out / keep_undecided unfold by one step per iteration,
    # matching the spec folds — no f(a+b)=f(a)+f(b) lemma needed, directive 3).
    # Every gold framing assert + per-step invariant is KEPT verbatim (directive
    # 2). If a faithful correct impl with reordered branches cannot verify =>
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))\n"
            "        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        Assert(ToSeq(other).drop(i - 1)[0] == e)\n"
            "        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))\n"
            "        v = verdict(e)\n"
            "        # Branches reordered (UNDECIDED first) and split into two ifs:\n"
            "        if v == UNDECIDED:\n"
            "            undecided = [e] + undecided\n"
            "        if v == DEFINITELY_OUT:\n"
            "            out = [e] + out\n"
            "        i = i - 1\n"
            "    Assert(ToSeq(other).drop(0) == ToSeq(other))\n"
            "    return out, undecided\n"
        ),
        "rationale": "a correct impl with the two membership branches REORDERED "
                     "(UNDECIDED tested first) and split into two independent ifs "
                     "must verify; it produces the same survivors/pending on every "
                     "input (the verdicts are disjoint, so order of the two ifs is "
                     "irrelevant). Same backward-walk + front-prepend as gold, so "
                     "the front-recursive folds unfold by one step per iteration; "
                     "every gold framing assert + invariant kept. Else "
                     "SPEC-TOO-STRONG.",
    },

    # POS-CONTROL 2 (local-variable reshape — single accumulator via a tuple-free
    # restructure). A correct impl that computes the verdict ONCE into a local and
    # dispatches with an explicit equality ladder, keeping the same prepend
    # direction and the same invariants/asserts. Confirms the spec is not pinned
    # to the gold's exact if/elif token shape. Must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-equality-ladder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))\n"
            "        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        Assert(ToSeq(other).drop(i - 1)[0] == e)\n"
            "        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))\n"
            "        v = verdict(e)\n"
            "        # Equality ladder: explicit DEFINITELY_IN no-op middle rung\n"
            "        # (DEFINITELY_IN elements go to NEITHER list).\n"
            "        if v == DEFINITELY_OUT:\n"
            "            out = [e] + out\n"
            "        elif v == DEFINITELY_IN:\n"
            "            i = i - 1\n"
            "            continue\n"
            "        else:\n"
            "            undecided = [e] + undecided\n"
            "        i = i - 1\n"
            "    Assert(ToSeq(other).drop(0) == ToSeq(other))\n"
            "    return out, undecided\n"
        ),
        "rationale": "a correct impl with an explicit three-rung equality ladder "
                     "(the DEFINITELY_IN rung an explicit no-op `continue`, vs "
                     "gold's implicit fall-through) must verify: verdict's range "
                     "is {0,1,2}, so the `else` rung is exactly UNDECIDED and the "
                     "partition is identical. Same prepend direction + invariants "
                     "+ asserts. Else SPEC-TOO-STRONG.",
    },

    # ===================================================================
    # ADMISSIBILITY — the precondition admits a normal input (must VERIFY;
    # else PRECOND-TOO-STRONG)
    # ===================================================================

    # ADMISS: a self-call caller builds an F2P-shaped in-domain input — a fresh
    # list literal `[7]` carries FULL Acc(list_pred), so passing half is
    # admissible — then invokes complement_finite on it. This is exactly the
    # FiniteSet branch being called on a one-element collection. If the Requires
    # (Acc(list_pred(other),1/2)) could not be established for this normal input
    # => PRECOND-TOO-STRONG. The self-call sits BEFORE the gold body's return, so
    # it is verified; the modeled body then returns normally. We also Assert that
    # ToSeq of both outputs equals the spec folds on the probe input (the
    # precondition admits AND the postcondition is establishable).
    {
        "id": "admiss-self-call-singleton",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # Admissibility self-call: a fresh one-element list is an\n"
            "    # F2P-shaped in-domain input (full Acc from the list literal, so\n"
            "    # half is trivially establishable). If the precondition could not\n"
            "    # be established for it, this call site fails => PRECOND-TOO-STRONG.\n"
            "    probe = [7]  # type: List[int]\n"
            "    p_out, p_und = complement_finite(probe)\n"
            "    Assert(ToSeq(p_out) == keep_out(ToSeq(probe)))\n"
            "    Assert(ToSeq(p_und) == keep_undecided(ToSeq(probe)))\n"
            + _GOLD_BODY
        ),
        "rationale": "the precondition (Acc(list_pred(other),1/2)) must admit a "
                     "normal F2P-shaped input: a fresh one-element list literal "
                     "(full Acc, so half is establishable). The self-call "
                     "establishes the Requires and the two Asserts confirm the "
                     "postcondition is establishable for it; else "
                     "PRECOND-TOO-STRONG.",
    },

    # ===================================================================
    # UNIQUENESS — frame mutation (MANDATORY: other is Acc 1/2 read-only)
    # ===================================================================

    # ATTACK 1 (FRAME-MUTATION, MANDATORY — the #1 weakness class). The impl
    # WRITES the read-only input: it appends to `other` before doing the gold
    # partition work. Only Acc(list_pred(other),1/2) is held; a list append needs
    # FULL permission, so the verifier MUST reject this for INSUFFICIENT
    # PERMISSION — not for a value mismatch. The gold body is kept verbatim AFTER
    # the write so the rejection is attributable SOLELY to the illegal append.
    {
        "id": "frame-mutate-other-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) list input.\n"
            "    other.append(0)\n"
            + _GOLD_BODY
        ),
        "refinement": "in the real Set._complement the read-only input is `other` "
                      "(the FiniteSet being removed-from, iterated element by "
                      "element). The gold code only READS it (the `for el in "
                      "other` inside sift, and the per-element self.contains "
                      "queries). A patch that APPENDS to `other` during the "
                      "partition mutates the caller's FiniteSet argument as a side "
                      "effect of computing a complement — FiniteSet is an "
                      "immutable Basic, and even the iteration order other "
                      "PASS_TO_PASS set operations rely on would be corrupted. The "
                      "faithful real patch does NOT resolve (it would also fail "
                      "the many P2P set-algebra tests that re-use the same "
                      "operands).",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants "
                     "only Acc(list_pred(other),1/2); a list append needs full "
                     "permission. Insufficient permission, NOT a value mismatch. "
                     "Mandatory frame-mutation probe #1.",
    },

    # ATTACK 2 (FRAME-MUTATION, second probe — index-assignment style). The impl
    # overwrites an element of the read-only input (other[0] = ...) to steer a
    # verdict before partitioning. Same class: only Acc(...,1/2) is held, an
    # index-assignment is a mutation needing full permission => rejected for
    # insufficient permission. Guarded by `len(other) > 0` so the write is
    # reachable (and the rejection is the permission, not an index error).
    {
        "id": "frame-mutate-other-index-assign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: index-assign into a read-only (Acc 1/2) list input.\n"
            "    if len(other) > 0:\n"
            "        other[0] = 0\n"
            + _GOLD_BODY
        ),
        "refinement": "this overwrites the first element of the caller's "
                      "FiniteSet operand as a side effect of complementing it. The "
                      "real partition never writes its operand; rewriting an "
                      "element would silently change which set is being removed "
                      "from, corrupting every downstream set operation that shares "
                      "the operand (the P2P union/intersection/difference tests "
                      "re-use the same FiniteSets). The faithful real patch does "
                      "NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: index-assignment is a "
                     "list mutation needing full permission; only "
                     "Acc(list_pred(other),1/2) is held. Insufficient permission. "
                     "Second mandatory frame-mutation probe.",
    },

    # ===================================================================
    # UNIQUENESS — partial-domain / value-divergence wrong impls
    # (must REJECT; else SPEC-TOO-WEAK)
    # ===================================================================

    # ATTACK 3 (THE BUG — prepatch / G-DIFF). Fold every non-IN element into the
    # ONE survivors bucket and leave pending empty — the pre-patch single
    # comprehension `[el for el in other if self.contains(el) != True]`. CORRECT
    # on every input with NO UNDECIDED elements; WRONG the moment an UNDECIDED
    # element appears (it lands in survivors, and pending is empty). Violates P1
    # (survivors then include the verdict-2 elements keep_out excludes) AND P2
    # (pending should hold them). Must reject.
    {
        "id": "weak-prepatch-fold-undecided-into-survivors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        v = verdict(e)\n"
            "        # PRE-PATCH BUG: everything that is not DEFINITELY_IN is\n"
            "        # folded into the ONE survivors bucket; pending left empty.\n"
            "        if v != DEFINITELY_IN:\n"
            "            out = [e] + out\n"
            "        i = i - 1\n"
            "    return out, undecided\n"
        ),
        "refinement": "this is the EXACT pre-patch FiniteSet branch "
                      "(FiniteSet(*[el for el in other if self.contains(el) != "
                      "True])) — the bug the issue reports. It conflates "
                      "DEFINITELY-OUT and UNDECIDED into one concrete FiniteSet "
                      "and produces no symbolic pending Complement, silently "
                      "asserting the UNDECIDED x, y are non-members. On the F2P "
                      "witness Complement(FiniteSet(x, y, 2), Interval(-10, 10)) "
                      "it returns FiniteSet(x, y) instead of "
                      "Complement(FiniteSet(x, y), Interval(-10, 10)), so the F2P "
                      "equality fails. This is model_prepatch.py / G-DIFF — the "
                      "faithful real patch (= prepatch) does NOT resolve.",
        "rationale": "violates P1 (ToSeq(Result()[0]) != keep_out(...) the moment "
                     "an UNDECIDED element appears — keep_out excludes verdict-2) "
                     "AND P2 (ToSeq(Result()[1]) is empty but keep_undecided is "
                     "not). The discriminating UNDECIDED-element case the F2P "
                     "exercises.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN — pending always empty, survivors correct). Handle
    # the DEFINITELY-OUT bucket exactly as gold, but NEVER populate pending (drop
    # the UNDECIDED branch). CORRECT on every input with NO UNDECIDED elements;
    # WRONG (pending empty) whenever an UNDECIDED element exists. Targets P2
    # precisely; P1 still holds. Must reject.
    {
        "id": "weak-pending-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        Invariant(ToSeq(out) == keep_out(ToSeq(other).drop(i)))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        Assert(ToSeq(other).drop(i - 1)[0] == e)\n"
            "        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))\n"
            "        v = verdict(e)\n"
            "        # WRONG: never carry the UNDECIDED elements in pending.\n"
            "        if v == DEFINITELY_OUT:\n"
            "            out = [e] + out\n"
            "        i = i - 1\n"
            "    return out, undecided\n"
        ),
        "refinement": "this gets the survivors bucket right but produces an EMPTY "
                      "pending collection — equivalent to dropping the UNDECIDED "
                      "elements entirely (sifted[None] never read, no symbolic "
                      "Complement emitted). On the F2P witness it returns "
                      "FiniteSet() (or just the DEFINITELY-OUT part) instead of "
                      "Complement(FiniteSet(x, y), Interval(-10, 10)): the "
                      "UNDECIDED x, y vanish from the result, so the F2P equality "
                      "fails. The faithful real patch does NOT resolve.",
        "rationale": "violates P2 (ToSeq(Result()[1]) == keep_undecided(...)) "
                     "whenever an UNDECIDED element exists: pending is empty but "
                     "keep_undecided is not. P1 still holds, so the rejection is "
                     "attributable solely to the missing pending elements.",
    },

    # ATTACK 5 (VALUE-DOUBLE-COUNT — UNDECIDED leaks into survivors AND pending).
    # Populate pending correctly, but ALSO add the UNDECIDED element to survivors
    # (a double-count that a length-only or membership-only proxy would miss).
    # CORRECT on inputs with no UNDECIDED elements; WRONG (survivors over-full)
    # otherwise. Targets P1. Must reject.
    {
        "id": "weak-undecided-leaks-into-survivors",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        Invariant(ToSeq(undecided) == keep_undecided(ToSeq(other).drop(i)))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        Assert(ToSeq(other).drop(i - 1)[0] == e)\n"
            "        Assert(ToSeq(other).drop(i - 1).drop(1) == ToSeq(other).drop(i))\n"
            "        v = verdict(e)\n"
            "        if v == DEFINITELY_OUT:\n"
            "            out = [e] + out\n"
            "        elif v == UNDECIDED:\n"
            "            undecided = [e] + undecided\n"
            "            # WRONG: also leak the UNDECIDED element into survivors.\n"
            "            out = [e] + out\n"
            "        i = i - 1\n"
            "    return out, undecided\n"
        ),
        "refinement": "this carries the UNDECIDED elements in pending (correct) "
                      "but ALSO puts them in the concrete survivors FiniteSet — "
                      "i.e. sifted[None] is fed to BOTH FiniteSet(*sifted[False]) "
                      "and the symbolic Complement. The survivors bucket then "
                      "asserts the UNDECIDED x, y ARE known non-members while the "
                      "pending Complement says their membership is unresolved — a "
                      "contradiction the gold result never produces. On the F2P "
                      "witness it returns Union(FiniteSet(x,y), Complement(...)) != "
                      "Complement(FiniteSet(x,y), Interval(-10,10)). The faithful "
                      "real patch does NOT resolve.",
        "rationale": "violates P1 (ToSeq(Result()[0]) == keep_out(...)) whenever "
                     "an UNDECIDED element exists: survivors over-count by the "
                     "verdict-2 elements keep_out excludes. P2 holds, so the "
                     "rejection is attributable solely to the survivors over-count "
                     "(a double-count an order-/length-only proxy would miss).",
    },

    # ATTACK 6 (PARTIAL-DOMAIN — buckets SWAPPED). Route DEFINITELY-OUT into
    # pending and UNDECIDED into survivors. CORRECT on inputs with NO verdict-0
    # and NO verdict-2 elements (e.g. all DEFINITELY-IN, or empty); WRONG the
    # moment either appears. Violates BOTH P1 and P2. Must reject.
    {
        "id": "weak-buckets-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    while i > 0:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(0 <= i and i <= len(other))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        v = verdict(e)\n"
            "        # WRONG: swap the two buckets.\n"
            "        if v == DEFINITELY_OUT:\n"
            "            undecided = [e] + undecided\n"
            "        elif v == UNDECIDED:\n"
            "            out = [e] + out\n"
            "        i = i - 1\n"
            "    return out, undecided\n"
        ),
        "refinement": "this swaps the destinations: DEFINITELY-OUT survivors land "
                      "in the symbolic pending Complement and the UNDECIDED "
                      "elements in the concrete survivors FiniteSet — i.e. "
                      "sifted[False] fed to the Complement and sifted[None] fed to "
                      "the bare FiniteSet. It asserts the UNDECIDED x, y are known "
                      "non-members and leaves the known-out elements pending. On "
                      "the F2P witness the result is structurally wrong (the bare "
                      "FiniteSet contains x, y), so the equality fails. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates P1 (survivors get the verdict-2 elements, not the "
                     "verdict-0) AND P2 (pending gets the verdict-0 elements, not "
                     "the verdict-2) whenever any verdict-0 or verdict-2 element "
                     "exists.",
    },

    # ATTACK 7 (PARTIAL-DOMAIN — off-by-one, first input element skipped). A
    # backward loop that stops at `i > 1` instead of `i > 0`, so the element at
    # index 0 (the FIRST input element, processed LAST in the backward walk) is
    # never classified. CORRECT on every input whose first element is
    # DEFINITELY-IN (it would be dropped anyway); WRONG whenever the first element
    # is DEFINITELY-OUT (missing from survivors) or UNDECIDED (missing from
    # pending). Targets the off-by-one boundary a value-proxy that ignores the
    # first element would miss. Must reject.
    {
        "id": "weak-skip-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    out = []  # type: List[int]\n"
            "    undecided = []  # type: List[int]\n"
            "    i = len(other)\n"
            "    # WRONG: stop at i > 1, never classifying index 0 (the first\n"
            "    # input element, processed last in the backward walk).\n"
            "    while i > 1:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(other), 1 / 2))\n"
            "        Invariant(Acc(list_pred(out)))\n"
            "        Invariant(Acc(list_pred(undecided)))\n"
            "        Invariant(1 <= i and i <= len(other))\n"
            "        # invariants-end\n"
            "        e = other[i - 1]\n"
            "        v = verdict(e)\n"
            "        if v == DEFINITELY_OUT:\n"
            "            out = [e] + out\n"
            "        elif v == UNDECIDED:\n"
            "            undecided = [e] + undecided\n"
            "        i = i - 1\n"
            "    return out, undecided\n"
        ),
        "refinement": "this never classifies the first element of the collection. "
                      "In the real partition that means the first FiniteSet "
                      "element is dropped from BOTH buckets regardless of its "
                      "verdict — a DEFINITELY-OUT first element vanishes from "
                      "survivors, an UNDECIDED first element vanishes from "
                      "pending. On any removal where the first element survives or "
                      "is undecided (e.g. the issue's own collection ordered with "
                      "x first), the gold result drops an element it must keep, so "
                      "the F2P / P2P Complement equalities fail. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates P1/P2 on the first input element whenever it is "
                     "DEFINITELY-OUT (missing from keep_out's survivors) or "
                     "UNDECIDED (missing from keep_undecided's pending) — an "
                     "off-by-one a value proxy that ignores index 0 would miss.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# This bundle has ONE @ContractOnly axiom — `verdict` (A-consumed) — and TWO
# A-reference deep models — keep_out / keep_undecided. We re-run the
# HOST-validated G-AX oracle (axiom_check.py) IN-CONTAINER, against the REAL
# sympy callee, as the axiom-lane probe. It covers BOTH obligations:
#
#  (1) axiom-soundness of `verdict` (A-consumed). verdict's ONLY contract is the
#      range Ensures(0 <= Result() <= 2). The probe collapses the REAL
#      Set.contains exactly as the gold ternary_sift does (contains if contains
#      in [True, False] else None) over a broad grid of removal sets (intervals,
#      finite sets, S.Naturals/Integers/Reals) x a mixed element pool + 400 fuzz,
#      asserting every collapsed verdict in {0,1,2}. flag_dependency: NONE
#      (meta + mapping.md §3.1 — contains takes no kwargs here), so no caller
#      runtime-config branch to set. It CALLS the real Set.contains (avoids pilot
#      bug 4: no source scraping).
#
#  (2) axiom-soundness + containment of keep_out / keep_undecided (A-reference).
#      The probe runs the REAL gold-patched Set._complement end-to-end on
#      FiniteSet removals and asserts it equals Union(FiniteSet(out),
#      Complement(FiniteSet(undecided), self, evaluate=False) if undecided else
#      S.EmptySet) where (out, undecided) is the verdict-driven partition — i.e.
#      survivors == keep_out and pending == keep_undecided on every reachable
#      input (54 boundary + 400 fuzz). The F2P witness is asserted directly and
#      the pre-patch single-bucket behaviour confirmed detectably wrong.
#
# CONTAINMENT note: the model's verdict consumes ONLY the range {0,1,2}; every
# real collapsed Set.contains lands in exactly that set by construction of
# ternary_sift (True->1, False->0, everything-else->2 is total and three-valued),
# so there is NO caller-reachable input outside the axiom's Requires domain — the
# axiom is sound AND fully covers the caller (no AXIOM-TOO-WEAK-FOR-CALLER).
# FiniteSet-vs-FiniteSet removal is range-checked but excluded from the structural
# end-to-end comparison because it additionally triggers the UNCHANGED downstream
# Complement(FiniteSet, FiniteSet) reduction (orthogonal to the modeled
# partition) — covering MORE than the partition reaches is sound, not a defect.
#
# The probe runs apply_gold=True (the end-to-end check needs the gold-patched
# _complement). It imports ONLY sympy + stdlib, opens no files (no utf-8 codec
# concern, pilot bug 5), and reads no bundle files in-container (pilot bug 6):
# axiom_check.py is read on the HOST at load time and embedded verbatim.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-verdict-range-and-partition-fidelity",
        "axiom": "verdict (A-consumed range {0,1,2}); keep_out / keep_undecided "
                 "(A-reference deep models of the sifted[False] / sifted[None] "
                 "buckets)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "axiom-soundness + containment in one in-container probe "
                     "against the REAL sympy callee. (1) verdict A-consumed: the "
                     "ternary collapse of the real Set.contains (the gold "
                     "ternary_sift) is in {0,1,2} on every (set, element) pair — "
                     "112 grid + 400 fuzz; no flag dependency (contains takes no "
                     "kwargs). Every reachable verdict is in {0,1,2} by "
                     "construction, so the range axiom is sound AND covers the "
                     "caller (no AXIOM-TOO-WEAK-FOR-CALLER). (2) keep_out / "
                     "keep_undecided A-reference: the real gold-patched "
                     "Set._complement == Union(FiniteSet(survivors), "
                     "Complement(FiniteSet(pending), self)) where survivors == "
                     "keep_out and pending == keep_undecided over 54 boundary + "
                     "400 fuzz cases; the F2P witness holds and the pre-patch "
                     "single-bucket behaviour is detectably wrong. CALLS the real "
                     "callee (no source scraping). Any mismatch => AXIOM-UNSOUND.",
    },
]
