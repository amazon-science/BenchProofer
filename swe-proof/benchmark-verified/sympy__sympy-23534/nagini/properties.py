# properties.py — PBT falsification battery for sympy__sympy-23534.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# byte-for-byte (region-surgery: only the text strictly INSIDE a # impl-start /
# # impl-end region is swapped) and is checked by Nagini verify + same_spec.
#
# ---------------------------------------------------------------------------
# Defended surface (model.py):
#
#   expand_entry(cls: int, n: int) -> List[int]
#     Requires: n >= 0
#     Ensures:  Acc(list_pred(Result()))
#               len(Result()) == n                       (E-mult: exact multiplicity)
#               all_tag(ToSeq(Result()), cls)            (E-tag: every leaf == cls)
#     -- the deep A-reference model of the single-name branch of sympy.symbols.
#        BOTH args are pass-by-value ints; NO read-only object input here.
#
#   symbols_on_sequence(names: List[int], cls: int) -> PSeq[PSeq[int]]
#     Requires: Acc(list_pred(names), 1/2)              (READ-ONLY container input)
#               all_nonneg(ToSeq(names))                (every entry multiplicity >= 0)
#     Ensures:  Acc(list_pred(names), 1/2)              (returns the half-perm: no mutation)
#               len(Result()) == len(names)             (G-group: one group per entry)
#               Forall k in [0,len(Result())):
#                   len(Result()[k]) == names[k]        (G-mult: per-entry multiplicity)
#                   and all_tag(Result()[k], cls)       (G-tag: every leaf of group k == cls)
#
#   The LOAD-BEARING postcondition is the Forall: it pins (a) the grouped shape
#   (one group per entry), (b) each group's multiplicity == the entry token, and
#   (c) every leaf of every group carries the REQUESTED class tag `cls`, never the
#   default. The whole content of the gold patch is `cls=cls`: forwarding the
#   requested class into the per-entry recursion (model: passing `cls`, not
#   DEFAULT_CLS(), into expand_entry). model_prepatch.py reverts exactly that and
#   fails the all_tag(res[k], cls) invariant.
#
# ---------------------------------------------------------------------------
# WHICH WEAKNESS CLASSES APPLY (others justified-N/A in the agent 'assessment'):
#
#  * FRAME-MUTATION: MANDATORY and present (S-frame-mut). `names` is a READ-ONLY
#    input held at Acc(list_pred(names), 1/2). A rival that WRITES to it
#    (names[i] = ...) to satisfy the postcondition must be rejected for
#    INSUFFICIENT PERMISSION (a store needs full permission). The gold invariants
#    are kept verbatim so the rejection is attributable to the write, not a proof
#    gap. This is the #1 weakness class a byte-fuzzer never finds.
#
#  * UNGROUNDED-ORACLE ECHO: N/A as a "wrong echo". The postcondition's tag clause
#    all_tag(Result()[k], cls) is GROUNDED in the `cls` ARGUMENT (fully unfolded by
#    the front-recursive all_tag fold over the produced sequence); there is no
#    opaque @Pure answer-key to echo. The only "echo" available is to forward the
#    WRONG tag (DEFAULT_CLS()) -- which is exactly the prepatch bug and CANNOT
#    verify (S-wrong-class). So the honest substitute is a cheapest-correct
#    positive control (S-pos) + an admissibility self-call (S-admiss).
#
#  * PARTIAL-DOMAIN: the strong uniqueness class here. The Forall pins EVERY group;
#    a rival correct on most entries but diverging on one sub-domain (the first
#    entry / a non-unit multiplicity) must reject. S-partial-firstentry attacks the
#    first group's multiplicity; S-flat attacks the whole non-unit-multiplicity
#    sub-domain (the documented prior verify-not-resolve break).
#
#  * VALUE-LEVEL DOUBLE-MASK / structure-flattening: S-flat -- a flat
#    one-object-per-entry impl that pins len(Result())==len(names) (group count)
#    but collapses every group to length 1, dropping the per-entry multiplicity.
#    This is the EXACT historical G-EQ break (a flat result.append(cls) whose
#    [0][0] raised TypeError); it must reject on len(res[k])==names[k].
#
#  * CONTROL-FLOW-EFFECT: N/A. symbols_on_sequence is total (no raise / no
#    return-vs-raise distinction / no observable side effect beyond the returned
#    pure PSeq). The frame condition (Acc(...,1/2) in == out) is what guards the
#    only side-effect channel (mutating `names`), and that IS exercised by the
#    frame-mutation case. There is no separate capability-token rival to build.
#
#  * POSITIVE CONTROL (soundness) + ADMISSIBILITY: included (S-pos, S-admiss).
#
# AXIOM_TESTS: one axiom-soundness probe (ax-sound-expand). meta.axioms == []
# (no @ContractOnly axiom) but expand_entry is an A-reference DEEP MODEL whose
# Ensures the proof of symbols_on_sequence consumes directly; PBT_PLAN §2.4 checks
# A-reference deep models the same way as axioms (deep model == real callee on
# every caller-reachable input). The probe re-runs the bundle's own axiom_check.py
# logic against the REAL sympy.symbols in-container (apply_gold=True) -- including
# the zero-multiplicity null-range boundary the model's len-clause must be sound on
# -- so a real-callee disagreement (AXIOM-UNSOUND) is caught here, not only by G-AX.
# ---------------------------------------------------------------------------
from pathlib import Path

INSTANCE = "sympy__sympy-23534"
FLOAT_ENCODING = None  # meta.json float_encoding == null (no floats anywhere)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The verbatim body of the symbols_on_sequence impl region (text strictly between
# its "    # impl-start\n" and "    # impl-end\n"). Every variant below is _BASE
# with THIS block (or a uniquely-anchored single line inside it) replaced -> the
# frozen axioms/pure/pre/post regions are never edited, so same_spec holds by
# construction. The expand_entry impl region is left gold-verbatim everywhere
# except where a variant explicitly says otherwise (none do; all attacks live in
# symbols_on_sequence, the changed function, or in expand_entry's caller).
_SEQ_IMPL = (
    "    res = PSeq()  # type: PSeq[PSeq[int]]\n"
    "    i = 0\n"
    "    while i < len(names):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(names), 1 / 2))\n"
    "        Invariant(all_nonneg(ToSeq(names)))\n"
    "        Invariant(0 <= i and i <= len(names))\n"
    "        Invariant(len(res) == i)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(res),\n"
    "                len(res[k]) == names[k] and all_tag(res[k], cls)),\n"
    "                [[res[k]]])))\n"
    "        # invariants-end\n"
    "        nonneg_at(ToSeq(names), i)\n"
    "        sub = expand_entry(cls, names[i])\n"
    "        grp = ToSeq(sub)  # type: PSeq[int]\n"
    "        old = res\n"
    "        res = res + PSeq(grp)\n"
    "        Assert(len(res) == i + 1)\n"
    "        Assert(res[i] == grp)\n"
    "        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i, res[k] == old[k]), [[res[k]]])))\n"
    "        i = i + 1\n"
    "    return res\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# S-frame-mut  (FRAME-MUTATION, MANDATORY) -- expect REJECT for insufficient
# permission. `names` is held at Acc(list_pred(names), 1/2) (read-only). This
# rival adds a WRITE to names[i] inside the loop. With only half permission a
# store is illegal -> Nagini rejects for INSUFFICIENT PERMISSION. Every gold
# invariant/assert is kept verbatim so the rejection is attributable solely to
# the write, never a proof gap.
# ===========================================================================
_SEQ_FRAME_MUT = _SEQ_IMPL.replace(
    "        nonneg_at(ToSeq(names), i)\n",
    "        nonneg_at(ToSeq(names), i)\n"
    "        names[i] = names[i]  # FRAME VIOLATION: write to a 1/2-perm input\n",
    1,
)

# ===========================================================================
# S-wrong-class  (UNIQUENESS / grounded-tag) -- expect REJECT. THIS IS THE
# PREPATCH BUG: forward DEFAULT_CLS() into the per-entry processing instead of
# the requested `cls` (mirrors the missing `cls=cls`). Fails the loop invariant
# all_tag(res[k], cls) whenever cls != DEFAULT_CLS().
# ===========================================================================
_SEQ_WRONG_CLASS = _SEQ_IMPL.replace(
    "        sub = expand_entry(cls, names[i])\n",
    "        sub = expand_entry(DEFAULT_CLS(), names[i])\n",
    1,
)

# ===========================================================================
# S-partial-firstentry  (PARTIAL-DOMAIN) -- expect REJECT. Forwards the correct
# class for every entry, but OVER-produces the FIRST group by one object
# (multiplicity names[0]+1). Correct on every group k>0; wrong only on k==0.
# Fails len(res[0]) == names[0]. A test that only ever reads the first group's
# class (the literal added F2P assertion reads only [0][0]) would still pass with
# the analogous real bug, but the SPEC pins every group's multiplicity, so the
# divergence is caught.
# ===========================================================================
_SEQ_PARTIAL = _SEQ_IMPL.replace(
    "        nonneg_at(ToSeq(names), i)\n"
    "        sub = expand_entry(cls, names[i])\n",
    "        nonneg_at(ToSeq(names), i)\n"
    "        m = names[i]  # type: int\n"
    "        if i == 0:\n"
    "            m = m + 1  # PARTIAL-DOMAIN: over-produce the first group by one\n"
    "        sub = expand_entry(cls, m)\n",
    1,
)

# ===========================================================================
# S-flat  (VALUE-DOUBLE-MASK / structure-flattening) -- expect REJECT. THE
# DOCUMENTED PRIOR verify-not-resolve BREAK: build one SINGLE-element group per
# entry (PSeq(cls)), so len(Result())==len(names) holds (group count is right)
# but every group has length 1, dropping the per-entry multiplicity. Fails
# len(res[k]) == names[k] for any entry whose multiplicity != 1 (e.g. the range
# entry 'q:2'). The forwarded class is correct, so all_tag holds -- it is ONLY
# the grouped-multiplicity clause that rejects it, exactly as G-EQ records.
# ===========================================================================
_SEQ_FLAT = _swap(
    _SEQ_IMPL,
    "        nonneg_at(ToSeq(names), i)\n"
    "        sub = expand_entry(cls, names[i])\n"
    "        grp = ToSeq(sub)  # type: PSeq[int]\n"
    "        old = res\n",
    "        nonneg_at(ToSeq(names), i)\n"
    "        grp = PSeq(cls)  # type: PSeq[int]\n"
    "        # FLAT: one object per entry, ignoring the entry's multiplicity.\n"
    "        old = res\n",
)

# ===========================================================================
# S-pos  (POSITIVE CONTROL / soundness) -- expect VERIFY. Structurally-different
# but behaviourally-identical: the new group is built via an intermediate typed
# local `newres` (a data-flow reshape) instead of assigning `res` directly, and
# the two INDEPENDENT post-append asserts are reordered (element pin before the
# length pin). EVERY gold proof obligation is preserved verbatim -- the Forall
# prefix-preservation framing assert, the per-element pin res[i]==grp, the length
# pin, and all four invariants -- so no induction lemma is newly required and the
# gold proof still discharges. No loop-direction flip (which would need an
# f(a+b)==f(a)+f(b) lemma). MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================
_SEQ_POS = _swap(
    _SEQ_IMPL,
    "        old = res\n"
    "        res = res + PSeq(grp)\n"
    "        Assert(len(res) == i + 1)\n"
    "        Assert(res[i] == grp)\n",
    "        old = res\n"
    "        newres = res + PSeq(grp)  # type: PSeq[PSeq[int]]\n"
    "        res = newres\n"
    "        Assert(res[i] == grp)\n"
    "        Assert(len(res) == i + 1)\n",
)

# ===========================================================================
# S-admiss  (ADMISSIBILITY) -- expect VERIFY. The whole impl body is a self-call
# to symbols_on_sequence on the IN-SCOPE input (names, cls) -- an arbitrary
# F2P/P2P-shaped in-domain container (the F2P witness ('q:2','u:2') maps to
# names=[2,2], cls=1). The call site must DISCHARGE the precondition
# Acc(list_pred(names),1/2) & all_nonneg(ToSeq(names)); both hold verbatim at
# entry, so if a legitimate input could not satisfy Requires the call would be
# rejected -> PRECOND-TOO-STRONG. The probe then asserts the returned grouped
# shape len(probe)==len(names) and returns it; the callee's Ensures is identical
# to this function's Ensures, so the postcondition discharges by construction.
#
# IMPORTANT (why the body is JUST the self-call, not a self-call followed by the
# real loop): symbols_on_sequence holds `names` at Acc(list_pred(names),1/2)
# (READ-ONLY) and its Ensures restores ONLY that half-permission -- it does NOT
# pin ToSeq(names) to its pre-call value. So after ANY self-call Nagini havocs
# the heap-dependent pure value all_nonneg(ToSeq(names)); a subsequent loop
# could no longer RE-ESTABLISH its `Invariant(all_nonneg(ToSeq(names)))` on
# entry. That is a FRAME re-establishment proof obligation -- nothing to do with
# whether the precondition is satisfiable (the precondition discharge at the
# call site already succeeds). Admissibility's sole job is to show Requires is
# dischargeable for a legitimate input; this body does exactly that at a genuine
# call site without polluting the proof with an unrelated frame obligation. (The
# soundness lane -- a correct impl satisfying Ensures -- is covered separately
# and independently by S-pos.) Self-recursion is sound under Nagini's
# contract-based verification; no termination metric is required.
# ===========================================================================
_SEQ_ADMISS = (
    "    probe = symbols_on_sequence(names, cls)  # type: PSeq[PSeq[int]]\n"
    "    Assert(len(probe) == len(names))\n"
    "    return probe\n"
)


SPEC_TESTS = [
    {
        "id": "S-pos",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_POS),
        "rationale": "Structurally-different CORRECT impl: the per-iteration group "
                     "append is reshaped through an intermediate typed local "
                     "`newres` and the two independent post-append asserts "
                     "(element pin res[i]==grp, length pin len(res)==i+1) are "
                     "reordered. All four loop invariants, the Forall "
                     "prefix-preservation framing assert, and the per-element pin "
                     "are kept verbatim, so the gold proof discharges without any "
                     "new induction lemma. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "S-admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_ADMISS),
        "rationale": "Whole-body self-call symbols_on_sequence(names, cls) on the "
                     "in-scope F2P/P2P-shaped input (the F2P witness ('q:2','u:2') "
                     "is names=[2,2], cls=1). The call forces the precondition "
                     "Acc(list_pred(names),1/2) & all_nonneg(ToSeq(names)) to be "
                     "discharged at the call site (both hold verbatim at entry); "
                     "the probe asserts the returned grouped shape "
                     "len(probe)==len(names) and returns it (callee Ensures == this "
                     "Ensures, so the postcondition discharges by construction). If "
                     "a legitimate input could not satisfy Requires, the call would "
                     "be rejected -> PRECOND-TOO-STRONG. The body is JUST the "
                     "self-call (not self-call + the real loop) because the callee "
                     "restores only the 1/2 permission and does not pin "
                     "ToSeq(names), so a subsequent loop could not re-establish its "
                     "all_nonneg invariant -- a FRAME re-establishment proof gap "
                     "unrelated to precondition satisfiability. The soundness lane "
                     "is covered independently by S-pos.",
    },
    {
        "id": "S-frame-mut",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_FRAME_MUT),
        "refinement": "Writing to names[i] has NO counterpart in the gold patch "
                      "(`result.append(symbols(name, cls=cls, **args))` never "
                      "mutates the input container `names`; it only reads each "
                      "entry and appends to a fresh `result`). A faithful real "
                      "patch that mutated the caller's container would corrupt the "
                      "very entries it must expand and would not reproduce "
                      "symbols(('q:2','u:2'), cls=Function) == ((q0,q1),(u0,u1)); "
                      "the F2P/P2P equality assertions would FAIL -> not resolved.",
        "rationale": "Rejected by the PERMISSION system: a store names[i]=... needs "
                     "full Acc(list_pred(names)) but only 1/2 is held (the "
                     "read-only frame condition Requires/Ensures Acc(...,1/2)). The "
                     "frame-mutation probe -- the #1 weakness class -- a byte "
                     "fuzzer never constructs.",
    },
    {
        "id": "S-wrong-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_WRONG_CLASS),
        "refinement": "This IS model_prepatch.py / the base_commit bug: the "
                      "per-entry processing receives DEFAULT_CLS() (the Symbol "
                      "default) instead of the requested `cls`, exactly mirroring "
                      "the missing `cls=cls` in `symbols(name, **args)`. The "
                      "faithful real patch (the unpatched branch) makes "
                      "type(symbols(('q:2','u:2'), cls=Function)[0][0]) == Symbol, "
                      "not UndefinedFunction -> the added F2P assertion FAILS -> "
                      "the instance is NOT resolved.",
        "rationale": "Violates the loop invariant / postcondition "
                     "all_tag(res[k], cls): every leaf would carry DEFAULT_CLS()==0 "
                     "while cls is the requested (non-default) tag. The spec senses "
                     "the dropped class forwarding on precisely the patched line.",
    },
    {
        "id": "S-partial-firstentry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_PARTIAL),
        "refinement": "Over-producing the FIRST group by one object has no gold "
                      "counterpart (the gold appends exactly symbols(name, ...)'s "
                      "own expansion per entry). A faithful real patch that emitted "
                      "an extra object in the first entry's group would make "
                      "symbols(('aa:d','x:z'))[0] a 5-tuple, not (aa,ab,ac,ad); the "
                      "existing P2P assertion in test_symbols "
                      "symbols(('aa:d','x:z')) == ((aa,ab,ac,ad),(x,y,z)) FAILS -> "
                      "not resolved.",
        "rationale": "Violates the Forall clause len(Result()[0]) == names[0] on "
                     "the first-entry sub-domain (group 0 has names[0]+1 leaves). "
                     "Correct on every other group, so it isolates a partial-domain "
                     "defect the all-domain attacks would not pinpoint.",
    },
    {
        "id": "S-flat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _SEQ_IMPL, _SEQ_FLAT),
        "refinement": "THE documented prior verify-not-resolve break: a flat impl "
                      "that appends ONE object per entry (here a length-1 group "
                      "PSeq(cls)), ignoring per-entry multiplicity, with the class "
                      "correctly forwarded. Its real counterpart "
                      "(result.append(cls(...)) -- a single object, not the entry's "
                      "tuple) makes symbols(('q:2','u:2'), cls=Function)[0] a single "
                      "object, so [0][0] raises TypeError ('not subscriptable'); "
                      "the F2P assertion errors -> NOT resolved. The grouped shape "
                      "the F2P test deconstructs via [0][0] is real, not abstracted.",
        "rationale": "Verifies len(Result())==len(names) (group count) and "
                     "all_tag(Result()[k], cls) (class is forwarded) but FAILS "
                     "len(Result()[k]) == names[k] for any non-unit-multiplicity "
                     "entry (the range entry 'q:2', multiplicity 2). This is the "
                     "value-level double-mask / structure-flattening attack; the "
                     "per-entry multiplicity clause is what rejects it (G-EQ).",
    },
]


# ===========================================================================
# AXIOM_TESTS: expand_entry is an A-reference DEEP MODEL (no @ContractOnly
# axiom). PBT_PLAN §2.4 validates A-reference deep models the same way as axioms:
# the deep model must equal the real callee on every caller-reachable input. We
# re-run the bundle's own axiom_check.py soundness logic against the REAL
# sympy.symbols IN-CONTAINER (apply_gold=True). The probe is SELF-CONTAINED: it
# embeds the host-side axiom_check.py source (read at manifest-load time, since
# the runner mounts ONLY the probe script at /work and model.py/axiom_check.py
# are NOT in-container) and exec's it. axiom_check.py imports only `sympy` +
# stdlib and exits 0 iff every observation (one group per entry, exact per-entry
# multiplicity incl. zero-multiplicity null ranges, every leaf == type(cls(probe))
# never the default Symbol, + the F2P witness) is consistent with the model.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# Embedded host-side axiom_check.py (the runner does NOT mount it in-container).\n"
    "# It calls the REAL sympy.symbols and asserts the A-reference deep model holds;\n"
    "# exits 0 iff sound. We exec it and propagate its exit code.\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__main__', '__file__': 'axiom_check.py'}\n"
    "try:\n"
    "    exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "    # axiom_check.py's `if __name__ == '__main__': sys.exit(main())` already\n"
    "    # exits; if it returned (it should not), treat a clean fall-through as pass.\n"
    "    sys.exit(0)\n"
    "except SystemExit as e:\n"
    "    code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)\n"
    "    if code == 0:\n"
    "        print('ax-sound-expand: A-reference deep model == real sympy.symbols')\n"
    "    else:\n"
    "        print('ax-sound-expand: AXIOM-UNSOUND (real callee disagreed), rc=%r' % (e.code,))\n"
    "    sys.exit(code)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-expand",
        "axiom": "expand_entry",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "expand_entry is the single A-reference deep model (the "
                     "single-name branch of sympy.symbols). Its Ensures "
                     "(len(Result())==n and all_tag(Result(), cls)) and the "
                     "container grouping/per-entry-multiplicity it supports are "
                     "validated against the REAL callee in-container by the "
                     "bundle's axiom_check.py: one group per entry, EXACT per-entry "
                     "multiplicity (incl. zero-multiplicity null ranges -- the "
                     "boundary the len-clause must be sound on), every leaf == "
                     "type(cls(probe)) never the default Symbol, over 10 boundary + "
                     "300 fuzz containers + the F2P witness. A real-callee "
                     "disagreement => AXIOM-UNSOUND.",
    },
]
