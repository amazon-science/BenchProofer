# properties.py — PBT falsification battery for matplotlib__matplotlib-22719.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE THE FROZEN SPEC (same_spec) and differ ONLY
# inside the `# impl-start`/`# impl-end` regions; each is checked by Nagini
# verify. There are NO @ContractOnly axioms in this bundle (meta.axioms == []),
# so AXIOM_TESTS is empty; the deep-model A-reference (all_classify) is grounded
# inside the postcondition itself (front-recursive @Pure fold over the input),
# so there is no opaque oracle to echo (see assessment / case `pos-reorder`).
#
# Defended surface (model.py):
#   Two near-identical decision functions, each with
#     Requires(Acc(list_pred(flags), 1/2))            # READ-ONLY half-permission
#     Ensures (Acc(list_pred(flags), 1/2))            # returns the half-perm
#     Ensures (Result() == (len(flags) > 0 and all_classify(ToSeq(flags))))  # LOAD-BEARING
#     Ensures (Implies(len(flags) == 0, not Result()))                       # empty guard
#   The bug fix is the `len(flags) > 0` conjunct (= numpy `values.size`/`data.size`);
#   the discriminating sub-domain is the EMPTY input (the F2P test
#   test_no_deprecation_on_empty_data plots ax.plot([], [])).

from pathlib import Path

INSTANCE = "matplotlib__matplotlib-22719"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Gold impl text fragments (each occurs once per function -> unique by the
# distinct accumulator variable name `every` vs `classify`).
# ---------------------------------------------------------------------------

# function 1: should_warn_numeric_passthrough — gold return
_F1_RETURN = "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    return len(flags) > 0 and every"
# function 1: gold branch (the `if c == 0: every = False`)
_F1_BRANCH = "        if c == 0:\n            every = False\n        i = i - 1"

# function 2: should_log_numeric_strings — gold return
_F2_RETURN = "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    return len(flags) > 0 and classify"
# function 2: gold branch
_F2_BRANCH = "        if c == 0:\n            classify = False\n        i = i - 1"


# ===========================================================================
# SPEC_TESTS
# ===========================================================================

SPEC_TESTS = [

    # -- ADMISSIBILITY (expect verify) --------------------------------------
    # The frozen gold impl, untouched. Verifies => the precondition
    # Acc(list_pred(flags),1/2) is satisfiable for the normal F2P-shaped input
    # (a flag list, incl. the empty list that the F2P test exercises) and the
    # spec is self-consistent. If THIS could not verify => PRECOND-TOO-STRONG.
    {
        "id": "admiss-gold-baseline",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,
        "rationale": "frozen gold impl; the precondition admits a normal flag "
                     "sequence (including the empty list of the F2P scenario) "
                     "and the loop body discharges under the 1/2 permission. "
                     "If it cannot verify, PRECOND-TOO-STRONG.",
    },

    # -- POSITIVE CONTROL #1 (expect verify): branch reorder ----------------
    # Structurally-different but CORRECT: replace `if c == 0: every = False`
    # with the algebraic `every = every and (c != 0)`. Same backward loop,
    # same framing asserts, same invariant (every == all_classify(drop(i))),
    # same grounded return. A correct impl MUST verify (else SPEC-TOO-STRONG).
    {
        "id": "pos-reorder-f1",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _F1_BRANCH,
            "        every = every and (c != 0)\n        i = i - 1",
        ),
        "rationale": "branch-as-conjunction reshape of fn1; keeps the backward "
                     "loop, the framing asserts and the invariant, and the "
                     "grounded `len>0 and every` return. Correct => must verify. "
                     "The load-bearing Ensures is grounded in the input "
                     "(len + the unfolded @Pure all_classify), so there is no "
                     "opaque oracle to echo — this honest variant is the "
                     "soundness positive control in its place.",
    },

    # -- POSITIVE CONTROL #2 (expect verify): the OTHER site, reshaped ------
    # Same reshape on should_log_numeric_strings (cross-site coverage): the
    # second decision function is independently a correct, structurally-
    # different impl and must verify.
    {
        "id": "pos-reorder-f2",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE,
            _F2_BRANCH,
            "        classify = classify and (c != 0)\n        i = i - 1",
        ),
        "rationale": "same branch-as-conjunction reshape on fn2; independently "
                     "correct, must verify (cross-site soundness control).",
    },

    # -- FRAME-MUTATION (expect reject): MANDATORY (read-only input) --------
    # flags is read-only (Acc(list_pred(flags),1/2)). A rival that WRITES to
    # flags to "produce" its answer must fail for INSUFFICIENT PERMISSION.
    # We keep the entire gold proof verbatim and only insert a write
    # `flags[0] = 0` guarded by len>0 (so the rejection is attributable to the
    # write, not an index-out-of-bounds). Under 1/2 permission an assignment to
    # flags[0] is not allowed -> reject.
    {
        "id": "frame-mutation-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _F1_RETURN,
            "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n"
            "    if len(flags) > 0:\n"
            "        flags[0] = 0\n"
            "    return len(flags) > 0 and every",
        ),
        "refinement": "Its faithful real patch would MUTATE the incoming "
                      "numpy value array (e.g. overwrite values[0]) inside "
                      "convert(); the real convert() must not corrupt the "
                      "caller's data, so such a patch breaks the convert/"
                      "round-trip P2P tests (TestStrCategoryConverter::"
                      "test_convert*) — it would NOT resolve.",
        "rationale": "rejection comes from the permission system: writing "
                     "flags[0] needs full permission but only Acc(...,1/2) is "
                     "held; insufficient-permission verification failure. A "
                     "byte-fuzzer never thinks to mutate the read-only input.",
    },

    # -- PARTIAL-DOMAIN #1 (expect reject): the EMPTY-input divergence ------
    # The exact prepatch defect (model_prepatch.py). Drop the `len(flags) > 0`
    # conjunct from fn1's return -> on the empty sequence `every ==
    # all_classify([]) == True`, but the postcondition requires
    # Result() == (len>0 and ...) == False, and Implies(len==0, not Result()).
    {
        "id": "partial-empty-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _F1_RETURN,
            "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    return every",
        ),
        "refinement": "This is the PRE-patch convert() behaviour `if "
                      "is_numlike:` without the `values.size` conjunct. The "
                      "F2P test test_no_deprecation_on_empty_data (ax.plot([], "
                      "[]) after categorical update) asserts NO deprecation is "
                      "emitted on empty data; the prepatch behaviour emits it "
                      "(all([]) is True) and FAILS the F2P — would NOT resolve.",
        "rationale": "rejection comes from the load-bearing postcondition "
                     "Result() == (len(flags)>0 and all_classify(...)) and the "
                     "empty-guard Implies(len==0, not Result()): on flags==[] "
                     "the rival returns True but the spec demands False.",
    },

    # -- PARTIAL-DOMAIN #2 (expect reject): empty-input divergence, site B --
    # Same drop on fn2 (model_prepatch_2.py): independent witness for the
    # update() site.
    {
        "id": "partial-empty-f2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _F2_RETURN,
            "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    return classify",
        ),
        "refinement": "PRE-patch update() behaviour `if convertible:` without "
                      "the `data.size` conjunct; the info advisory would log on "
                      "empty data (unentered loop leaves convertible True), "
                      "the behaviour the issue #22640 fix removes. Faithful "
                      "patch would not resolve the empty-data smoke test.",
        "rationale": "same postcondition clause on fn2: on flags==[] the rival "
                     "returns classify==True but spec demands False.",
    },

    # -- UNIQUENESS #3 (expect reject): drop the classifier, keep only len --
    # Return `len(flags) > 0` alone (drop the all_classify conjunct). Correct on
    # the empty input, but on any NON-empty sequence with a non-classifying
    # element it returns True where the spec requires
    # (len>0 and all_classify) == False. Diverges on the non-empty
    # not-all-classify sub-domain.
    {
        "id": "weak-len-only-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _F1_RETURN,
            "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    return len(flags) > 0",
        ),
        "refinement": "Equivalent to convert() firing the deprecation whenever "
                      "values.size, ignoring is_numlike. That emits the numeric "
                      "pass-through advisory for genuine string categories "
                      "(e.g. TestStrCategoryConverter::test_convert[unicode], "
                      "test_convert_fail) where is_numlike is False — changing "
                      "convert()'s return path and warning behaviour; would NOT "
                      "resolve the P2P convert tests.",
        "rationale": "load-bearing postcondition: on a non-empty flags with a "
                     "zero element, all_classify is False so spec demands "
                     "False, but the rival returns True.",
    },

    # -- UNIQUENESS #4 (expect reject): constant True ------------------------
    # Cheapest wrong impl: ignore the input entirely, always emit. Diverges on
    # BOTH the empty input and any non-classifying sequence. Supporting case.
    {
        "id": "weak-const-true-f1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE,
            _F1_RETURN,
            "    Assert(ToSeq(flags).drop(i) == ToSeq(flags))\n    empty_is_irrelevant = True\n    return empty_is_irrelevant",
        ),
        "refinement": "convert() unconditionally emitting the deprecation "
                      "warning (even on empty input and on string categories) "
                      "fails both the F2P empty-data test and the non-numeric "
                      "P2P convert tests; would NOT resolve.",
        "rationale": "violates both Ensures clauses: on flags==[] requires "
                     "False (Implies(len==0, not Result())), and on any "
                     "non-classifying non-empty input all_classify is False.",
    },
]


# ===========================================================================
# AXIOM_TESTS — none.
# meta.axioms == []; there is no @ContractOnly axiom. The single A-reference
# deep model (all_classify) is GROUNDED in the postcondition itself (a
# front-recursive @Pure fold over the input, fully unfolded by the loop), not a
# consumed axiom, so there is no real-callee soundness obligation to probe here
# in the Nagini lane. The behavioural equivalence of all_classify to the real
# all(...)/convertible verdict (incl. the vacuous-truth fact on empty input) is
# already validated by axiom_check.py / G-AX (numpy array layer, 9 boundary +
# 20000 fuzz cases). Re-encoding that here would duplicate G-AX, not add an
# independent obligation, so AXIOM_TESTS stays empty per PLAN §3.
# ===========================================================================

AXIOM_TESTS = []
