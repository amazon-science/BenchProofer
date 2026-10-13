# properties.py — PBT falsification battery for scikit-learn__scikit-learn-13124.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of per_class_draw_states for a
# new body and leave the FROZEN spec (axioms `seed_state`/`advance`; the @Pure
# fold `state_stream`; the pre-condition; the three post-conditions; the
# signature) byte-identical. spec_view elides the WHOLE impl region (the nested
# `invariants` included), so same_spec is GUARANTEED for every case regardless of
# the proof scaffolding inside.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   per_class_draw_states(seed, n_classes) -> List[int] pins, on the verified output:
#     (P1) Acc(list_pred(Result()))                              -- result permission
#     (P2) len(Result()) == n_classes                            -- length pin
#     (P3) ToSeq(Result()) == state_stream(seed_state(seed), n_classes)
#          -- the LOAD-BEARING clause: the output is EXACTLY the advancing draw
#             stream from the seed's initial state. state_stream is the @Pure
#             front-recursive fold
#               state_stream(s,0) == empty
#               state_stream(s,n) == [s] ++ state_stream(advance(s), n-1)
#             so element k is the k-fold advance of seed_state(seed). No two
#             classes are pinned to one and the same unchanging state.
#
#   The bug the fix repairs: the pre-patch drew every class from the SAME state
#   (re-seeding a fresh source from the identical raw seed per class), i.e. the
#   constant list [start, start, ...]; the fix shares ONE advancing source so the
#   per-class draws differ. The F2P test_shuffle_stratifiedkfold asserts two seeds
#   give DIFFERENT sorted per-fold test sets -- which holds iff the per-class draws
#   genuinely advance (P3), not if they are all the same state. model_prepatch.py
#   reproduces the bug ([start]*n) and FAILS P3 (G-DIFF).
#
# GROUNDED ORACLE, NO WRONG ECHO:
#   state_stream is @Pure and TRANSPARENT in its arguments -- it is the spec's own
#   structural fold over seed_state(seed)/advance, not an opaque answer-key. An
#   impl that "echoes" it (materializes the fold) has actually done the work (it
#   built the advancing stream). There is therefore NO wrong echo to construct;
#   the ungrounded-oracle slot is filled instead by an honest cheapest-impl
#   POSITIVE CONTROL that materializes the fold (expect=verify). See 'assessment'.
#
# READ-ONLY INPUTS: NONE. Both parameters are `int` passed by value (seed,
#   n_classes); there is no Acc(x, 1/2) read-only reference and no list_pred input.
#   FRAME-MUTATION is therefore N/A for this instance (nothing the impl is given
#   can be illegally written to vacuously satisfy a postcondition). Documented in
#   'assessment'. CONTROL-FLOW-EFFECT is likewise N/A: the modeled function is a
#   pure total value function (no raise / no observable side effect / no capability
#   distinction invisible to the value abstraction). The whole discriminating
#   content lives in the value P3, which the uniqueness attacks below target.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13124"
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
# of per_class_draw_states (verified verbatim from model.py). Each variant
# re-emits `# impl-start` first and `# impl-end` last so the region boundary is
# preserved exactly -- only the body between them changes, and spec_view elides
# all of it (invariants included), guaranteeing same_spec.
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace per_class_draw_states's whole impl block with a new body.
    `body_lines` is the source BETWEEN the markers (no markers); we wrap it back
    in the exact `# impl-start` / `# impl-end` markers so the region is intact
    and same_spec holds."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The gold loop body verbatim (the forward loop with the prefix++rest==whole
# invariant and the single-unfold Assert). Reused so positive controls differ
# ONLY in the executable shape and keep every proof obligation the spec needs --
# per the pilot calibration: do NOT drop a framing invariant/assert (that fails
# the loop for a PROOF reason, not a spec reason). Indentation matches model.py.
_GOLD_BODY = """    start = seed_state(seed)
    cur = start
    result = []  # type: List[int]
    i = 0
    while i < n_classes:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n_classes)
        Invariant(len(result) == i)
        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==
                  state_stream(start, n_classes))
        # invariants-end
        Assert(state_stream(cur, n_classes - i) ==
               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))
        result = result + [cur]
        cur = advance(cur)
        i = i + 1
    return result
"""


SPEC_TESTS = [

    # ======================================================= soundness (pos ctrl)
    # POSITIVE CONTROL A (local-variable reshape -- the LOW-RISK kind per the pilot
    # caution). KEEP the gold proof structure and every gold invariant/assert
    # verbatim in meaning, but rename every local (start->s0, cur->st, result->acc,
    # i->k). This is a genuinely different source shape that keeps the gold forward
    # loop + the prefix++rest==whole invariant + the single-unfold Assert intact
    # (no new fold/append-direction lemma is introduced -- it is the SAME forward
    # append against the SAME front-recursive spec, which the gold already
    # discharges). If this cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-rename-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    s0 = seed_state(seed)\n"
            "    st = s0\n"
            "    acc = []  # type: List[int]\n"
            "    k = 0\n"
            "    while k < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(acc)))\n"
            "        Invariant(0 <= k and k <= n_classes)\n"
            "        Invariant(len(acc) == k)\n"
            "        Invariant(ToSeq(acc) + state_stream(st, n_classes - k) ==\n"
            "                  state_stream(s0, n_classes))\n"
            "        # invariants-end\n"
            "        Assert(state_stream(st, n_classes - k) ==\n"
            "               PSeq(st) + state_stream(advance(st), n_classes - k - 1))\n"
            "        acc = acc + [st]\n"
            "        st = advance(st)\n"
            "        k = k + 1\n"
            "    return acc\n"
        ),
        "rationale": "a correct impl with a renamed-local reshape (start/cur/result/i "
                     "-> s0/st/acc/k) keeps the gold forward loop, the "
                     "prefix++rest==whole invariant, and the single-unfold Assert -- "
                     "the exact proof the gold discharges -- so it MUST verify. "
                     "No new lemma is required (same forward-append against the same "
                     "front-recursive fold). Else SPEC-TOO-STRONG.",
    },

    # POSITIVE CONTROL B (different control flow: explicit n==0 early return, then
    # the gold loop). The gold runs a 0-iteration loop when n_classes==0; this
    # returns the empty list up-front (state_stream(s,0) is the empty PSeq, so P2/P3
    # hold trivially) and otherwise runs the gold loop verbatim. A structurally
    # DIFFERENT control flow that is still CORRECT, keeping every gold invariant/
    # assert in the loop branch. Stands ALSO in place of the (non-existent)
    # ungrounded-oracle echo: the cheapest correct impl materializes the spec fold,
    # which is the real work. If it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-zero-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if n_classes == 0:\n"
            "        empty = []  # type: List[int]\n"
            "        return empty\n"
            "    start = seed_state(seed)\n"
            "    cur = start\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==\n"
            "                  state_stream(start, n_classes))\n"
            "        # invariants-end\n"
            "        Assert(state_stream(cur, n_classes - i) ==\n"
            "               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))\n"
            "        result = result + [cur]\n"
            "        cur = advance(cur)\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "rationale": "a different control flow (explicit n_classes==0 early return of "
                     "an empty list -- state_stream(s,0) is the empty PSeq so P2/P3 "
                     "hold trivially -- then the gold loop verbatim) is still correct "
                     "and MUST verify; it is the honest cheapest impl that materializes "
                     "the grounded spec fold (the real work). The empty local is bound "
                     "with a typed `# type: List[int]` before return (pilot bug #1). "
                     "Else SPEC-TOO-STRONG.",
    },

    # ====================================================== admissibility (1)
    # ADMISSIBILITY: a self-call caller invokes per_class_draw_states on an
    # F2P-shaped in-domain input (n_classes==3, a normal seed) BEFORE returning,
    # establishing the precondition Requires(n_classes >= 0) for a legitimate input
    # and asserting the post facts are derivable (the result has list_pred and the
    # required length). If the Requires could not be established for a normal input
    # => PRECOND-TOO-STRONG. The caller lives strictly inside the impl region
    # (frozen spec untouched). The gold body runs first so the modeled function
    # still returns its correct result.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    start = seed_state(seed)\n"
            "    cur = start\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        Invariant(ToSeq(result) + state_stream(cur, n_classes - i) ==\n"
            "                  state_stream(start, n_classes))\n"
            "        # invariants-end\n"
            "        Assert(state_stream(cur, n_classes - i) ==\n"
            "               PSeq(cur) + state_stream(advance(cur), n_classes - i - 1))\n"
            "        result = result + [cur]\n"
            "        cur = advance(cur)\n"
            "        i = i + 1\n"
            "    # Admissibility self-call: n_classes==3 with a fixed seed is an\n"
            "    # F2P-shaped in-domain input (>=0 classes). If the precondition\n"
            "    # could not be established for it, this call site would fail =>\n"
            "    # PRECOND-TOO-STRONG.\n"
            "    probe = per_class_draw_states(7, 3)\n"
            "    Assert(Acc(list_pred(probe)))\n"
            "    Assert(len(probe) == 3)\n"
            "    return result\n"
        ),
        "rationale": "the precondition Requires(n_classes >= 0) must admit a normal "
                     "F2P-shaped input (3 classes, seed 7); the self-call establishes "
                     "it and the post facts (list_pred(probe), len==3) are derivable. "
                     "Else PRECOND-TOO-STRONG.",
    },

    # ====================================================== uniqueness (attacks)
    # ATTACK 1 (WRONG-STREAM / the prepatch bug -- the central discriminator).
    # Draw EVERY class from the SAME initial state seed_state(seed): the constant
    # list [start, start, ...]. This is exactly model_prepatch.py. It satisfies P1
    # (permission) and P2 (length n_classes) but VIOLATES P3 for n_classes >= 2:
    # state_stream(start, n) == [start, advance(start), ...] and advance(start) is
    # an ABSTRACT, unconstrained function -- there is no proof that
    # advance(start) == start, so the constant list cannot be proven equal to the
    # advancing stream. Must reject.
    {
        "id": "weak-constant-state-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    start = seed_state(seed)\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        # invariants-end\n"
            "        cur = seed_state(seed)  # fresh source from the raw seed, every class\n"
            "        result = result + [cur]\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "refinement": "this is the PRE-PATCH data-flow: rng = self.random_state (the raw "
                      "int) re-converted to a FRESH RandomState(seed) inside every "
                      "class's KFold, so every class re-seeds from the identical initial "
                      "state and draws the SAME permutation. The F2P "
                      "test_shuffle_stratifiedkfold asserts that StratifiedKFold(5, "
                      "shuffle=True, random_state=0) and random_state=1 give DIFFERENT "
                      "sorted per-fold test sets; with identical per-class draws the "
                      "assignment is the same shuffle replicated, and (validated by "
                      "axiom_check.py A-reference 2) re-seeding gives identical "
                      "per-class permutations -- so the F2P assertion test_set1 != "
                      "test_set2 still FAILS. The faithful real patch (= the pre-patch) "
                      "does NOT resolve. (= model_prepatch.py, G-DIFF.)",
        "rationale": "violates P3: ToSeq(Result()) == [start]*n_classes, but "
                     "state_stream(start, n_classes) == [start, advance(start), ...]; "
                     "advance is an abstract unconstrained function so advance(start) "
                     "cannot be proven equal to start -- the constant list != the "
                     "advancing stream for n_classes >= 2. Comes from the postcondition "
                     "P3 (the advancing-stream pin).",
    },

    # ATTACK 2 (PARTIAL-DOMAIN: correct at index 0, diverges for n>=2 -- double
    # advance). Emit start at class 0 but advance TWICE per step thereafter:
    # [start, advance(advance(start)), advance^4(start), ...]. CORRECT on n_classes
    # in {0, 1} (the empty / single-element stream), WRONG for n_classes >= 2: the
    # class-1 draw is advance^2(start) but the spec pins advance(start). Targets the
    # advance step granularity of P3. Must reject.
    {
        "id": "weak-double-advance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    start = seed_state(seed)\n"
            "    cur = start\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        # invariants-end\n"
            "        result = result + [cur]\n"
            "        cur = advance(advance(cur))  # WRONG: advances two draws per class\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "refinement": "this advances the shared source by TWO draws between classes "
                      "instead of one (e.g. an extra spurious .shuffle / .rand call per "
                      "class). The per-class permutation for class 1 is then the source "
                      "state after two draws, not one, so the real patched "
                      "StratifiedKFold's per-fold test sets differ from the gold's at "
                      "every class beyond the first. The gold patch's exact sorted "
                      "per-fold test sets (the F2P pins seed-dependence AND the precise "
                      "assignment that other P2P split tests, e.g. "
                      "test_cross_validator_with_default_params / fold-coverage checks, "
                      "depend on) would change -- the faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates P3 for n_classes >= 2: element 1 is advance(advance("
                     "start)) but state_stream pins advance(start); the abstract advance "
                     "gives no advance^2(start) == advance(start) fact. Correct only on "
                     "n_classes in {0,1}. Partial-domain over the class count.",
    },

    # ATTACK 3 (PARTIAL-DOMAIN: wrong FIRST element -- start one draw advanced).
    # Begin the stream at advance(seed_state(seed)) instead of seed_state(seed):
    # [advance(start), advance^2(start), ...]. WRONG for every n_classes >= 1 (the
    # class-0 draw is off by one advance); CORRECT only on n_classes == 0 (empty
    # stream). Targets the stream's anchor (which state class 0 draws from) in P3.
    # Must reject.
    {
        "id": "weak-start-advanced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    start = advance(seed_state(seed))  # WRONG: class 0 draws from the\n"
            "                                       # ONCE-advanced state, not the seed's\n"
            "                                       # initial state\n"
            "    cur = start\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        # invariants-end\n"
            "        result = result + [cur]\n"
            "        cur = advance(cur)\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "refinement": "this draws an extra throw-away permutation from the shared source "
                      "BEFORE the first class (the source is advanced once before class "
                      "0). Every class's permutation is then shifted by one draw vs the "
                      "gold, so the real patched StratifiedKFold produces a different "
                      "(though still seed-dependent) per-fold assignment than the gold "
                      "patch on the F2P input. The gold's exact sorted test sets (and "
                      "the deterministic fold layout the P2P coverage/index tests "
                      "assume) change -- the faithful real patch does NOT resolve.",
        "rationale": "violates P3 for n_classes >= 1: element 0 is advance(seed_state("
                     "seed)) but state_stream pins seed_state(seed) at index 0; advance "
                     "is abstract so advance(start)==start is unprovable. Correct only "
                     "on n_classes == 0. Partial-domain (the input that fails first).",
    },

    # ATTACK 4 (WRONG LENGTH -- off-by-one, drop the last class). Build the correct
    # advancing stream but stop one class early (loop to n_classes - 1). CORRECT on
    # the value of every emitted element AND on n_classes == 0; WRONG on the LENGTH
    # for every n_classes >= 1 (len == n_classes - 1) and hence on P3 (a shorter
    # prefix of the stream). Targets P2 (and P3's length) specifically. Must reject.
    {
        "id": "weak-drop-last-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    start = seed_state(seed)\n"
            "    cur = start\n"
            "    result = []  # type: List[int]\n"
            "    i = 0\n"
            "    while i < n_classes - 1:  # WRONG: stops one class short\n"
            "        # invariants-start\n"
            "        Invariant(Acc(list_pred(result)))\n"
            "        Invariant(0 <= i and i <= n_classes)\n"
            "        Invariant(len(result) == i)\n"
            "        # invariants-end\n"
            "        result = result + [cur]\n"
            "        cur = advance(cur)\n"
            "        i = i + 1\n"
            "    return result\n"
        ),
        "refinement": "this processes one fewer class than there are classes (e.g. an "
                      "off-by-one in the per-class loop bound), so the last class never "
                      "gets a draw and is dropped from the stratified split. The real "
                      "StratifiedKFold would then fail to assign one class's samples to "
                      "folds -- the fold-coverage / shape P2P tests "
                      "(check_cv_coverage, test_cross_validator_with_default_params) "
                      "and the F2P would diverge from the gold. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "violates P2 (len(Result()) == n_classes - 1 != n_classes for "
                     "n_classes >= 1) and hence P3 (the result is a strict prefix of "
                     "state_stream, missing the last element). Comes from the length "
                     "postcondition. Correct only on n_classes == 0.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE.
#
# meta.axioms == [] (no @ContractOnly axiom claims an Ensures the proof consumes;
# the axioms region declares seed_state/advance as ABSTRACT pure symbols with NO
# claimed contract -- refinement.md §B). The only callee-level obligation is the
# A-REFERENCE deep model: the abstract trio seed_state / advance / state_stream
# must correspond to the REAL pseudo-random source the gold patch shares across
# the per-class loop, AND the one discriminating fact the spec relies on --
# that `advance` is a genuine state MOVE (per-class draws are NOT all identical) --
# must hold for the real callee. That is precisely what the bundle's
# axiom_check.py (G-AX) validates by RUNNING the real numpy RandomState and the
# real patched sklearn StratifiedKFold (not by scraping source):
#   (A-reference 1) one shared RandomState drawn once per class ADVANCES (per-class
#                   draws differ) over 25 seeds -> `advance` is a real move;
#   (A-reference 2) re-seeding a fresh RandomState from the same int per class is
#                   CONSTANT (identical draws) over 25 seeds -> the pre-patch the
#                   model forbids (grounds the weak-constant-state reject above);
#   (end-to-end)    the real patched StratifiedKFold yields seed-dependent sorted
#                   per-fold test sets (the exact F2P observation).
#
# We re-run that host-validated oracle IN-CONTAINER as the axiom-soundness probe,
# so the A-reference is grounded in the REAL numpy/sklearn callees (not a regex
# over source -- pilot bug #4). axiom_check.py imports only numpy + the repo's own
# sklearn, reads NO files (no utf-8 codec concern -- pilot bug #5), and CALLS the
# real routines; the runner mounts only this probe script, so axiom_check.py's
# source is embedded VERBATIM from the HOST at load time (pilot bug #6).
# apply_gold=True: A-reference 1 / end-to-end describe the POST-gold patched
# StratifiedKFold (the shared advancing source).
#
# CONTAINMENT: there is no @ContractOnly axiom with a Requires domain, so there is
# no caller-reachable input outside an axiom domain (no axiom domain exists). The
# A-reference is checked for SOUNDNESS only (covering MORE real inputs than the
# caller reaches would be sound, not a defect). Documented in 'assessment'.
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-advancing-source",
        "axiom": "seed_state/advance/state_stream (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness: the abstract trio (seed_state/advance and "
                     "the state_stream fold) must correspond to the REAL shared "
                     "pseudo-random source, and the discriminating fact the spec relies "
                     "on -- that `advance` genuinely MOVES the state so per-class draws "
                     "differ -- must hold for the real callee. This re-runs the bundle's "
                     "G-AX oracle in-container (real numpy RandomState + real patched "
                     "StratifiedKFold): A-reference 1 (shared source advances over 25 "
                     "seeds), A-reference 2 (re-seed is constant -- grounds the "
                     "weak-constant-state reject), and the end-to-end seed-dependent "
                     "sorted test sets (the F2P observation). Exit 0 iff every "
                     "obligation holds; any mismatch => the A-reference is unsound. "
                     "No @ContractOnly axiom and no caller-reachable input outside any "
                     "axiom domain exist (no axiom domain to under-cover).",
    },
]
