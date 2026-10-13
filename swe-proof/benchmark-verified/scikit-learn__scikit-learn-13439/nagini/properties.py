# properties.py — PBT falsification battery for scikit-learn__scikit-learn-13439.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   composite_size(steps: List[int]) -> int      [the size query the patch adds]
#     Requires Acc(list_pred(steps), 1/2)         <-- READ-ONLY input (half perm)
#     Ensures  Acc(list_pred(steps), 1/2)         <-- frame: caller keeps its half
#     Ensures  Result() == len(steps)             <-- LOAD-BEARING value clause
#     impl:    return len(steps)
#
#   Repo binding: composite_size <-> Pipeline.__len__(self); steps <-> self.steps
#   (the ordered list of (name, estimator) stages, abstracted to List[int], one
#   opaque element per stage). The gold hunk is `def __len__(self): return
#   len(self.steps)`. At base_commit the method is ABSENT, so `len(pipe)` raises
#   TypeError; the F2P test `test_make_pipeline_memory` adds
#   `assert len(pipeline) == 2` for a 2-step pipeline, i.e. it demands exactly
#   len(self.steps). The P2P indexing tests (test_pipeline_slice / index) rely on
#   `pipe[:len(pipe)]` spanning the whole collection.
#
#   GROUNDED ORACLE, no echo class. The load-bearing postcondition is pinned to
#   `len(steps)` — the Nagini builtin length of the actual input, fully unfolded,
#   a pure function of the argument. There is NO opaque @Pure answer-key / exact
#   marker an impl could echo without doing the work; the cheapest honest impl IS
#   the gold `return len(steps)`. So the ungrounded-oracle-echo class is N/A here
#   (see 'assessment'); the soundness lane is covered by the honest
#   local-variable-reshape positive control below.
#
#   No raise / return-variant / side-effect: composite_size is a total query that
#   always returns; the value abstraction (an int == len(steps)) captures it
#   completely, so the control-flow-effect class is N/A (see 'assessment').
#
#   No @ContractOnly axioms (meta.axioms == []), no A-reference deep model: `len`
#   is the Python builtin modelled DEEPLY as Nagini's len over the List[int]
#   carrier; the proof consumes no callee contract. axiom_check.py exercises the
#   single trivial refinement fact (real len(self.steps) == constructed stage
#   count) for completeness; there is no real callee to validate. Hence
#   AXIOM_TESTS = []. See 'assessment'.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13439"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchor INSIDE the impl region (between # impl-start / # impl-end). The whole
# impl body is the single statement `return len(steps)` — it is unique in the
# module (the postcondition uses `Result() == len(steps)`, which does NOT
# contain `return`). Editing only this keeps spec_view (hence same_spec)
# byte-identical.
# ===========================================================================
_IMPL_GOLD = "return len(steps)"

assert _IMPL_GOLD in _BASE, "impl anchor drift: composite_size body not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally-different but CORRECT impl (verify).
# Local-variable reshape: bind the cardinality to a named int local, then return
# it. Same observable value (len(steps)); no loop / fold lemma / branch is
# introduced, so the gold proof stays trivially valid. If this faithful correct
# impl could NOT verify => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """n = len(steps)
    return n"""


# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# A top-level caller would leave the impl region and break same_spec, so this is
# done IN-REGION: read the half-permission input (Assert its length is well
# defined, i.e. the Acc(list_pred(steps),1/2) is usable) and reach a normal,
# non-raising return. If the Requires were vacuous / over-strong the impl could
# not both consume the half-permission read and return the correct value
# => PRECOND-TOO-STRONG. Source: the Acc(list_pred(steps),1/2) Requires.
# ===========================================================================
_IMPL_ADMISS = """Assert(len(steps) >= 0)   # half-permission input is readable
    return len(steps)"""


# ===========================================================================
# (3) FRAME-MUTATION — write to the read-only input `steps` (reject). MANDATORY:
# the input is read-only. composite_size holds only Acc(list_pred(steps), 1/2).
# A value-NEUTRAL indexed write steps[0] = 0 (guarded in-bounds) needs FULL
# permission, so Nagini rejects for INSUFFICIENT PERMISSION before any value
# reasoning. The gold value computation `return len(steps)` is kept verbatim so
# the rejection is attributable to the write alone, not to a spec change. A
# byte-fuzzer never thinks to mutate the input — this is the #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """if len(steps) > 0:
        steps[0] = 0   # WRITE to read-only Acc(list_pred(steps),1/2) input
    return len(steps)"""


# ===========================================================================
# (4) PARTIAL-DOMAIN / prepatch under-count (reject). THIS IS THE PREPATCH
# CANDIDATE (model_prepatch.py): the only stage-traversal in the surrounding
# code, `_iter(with_final=False)`, does `stop -= 1`, walking one fewer than
# len(self.steps); reusing that truncated count as the reported size under-counts
# by one. Violates the load-bearing Result() == len(steps) on EVERY input.
# ===========================================================================
_IMPL_OFFBYONE = "return len(steps) - 1"


# ===========================================================================
# (5) PARTIAL-DOMAIN / constant at the F2P size (reject). Return the constant 2:
# correct ONLY for the 2-step F2P pipeline, wrong for every other cardinality.
# Violates Result() == len(steps) on every input whose length != 2.
# ===========================================================================
_IMPL_CONST2 = "return 2"


# ===========================================================================
# (6) PARTIAL-DOMAIN / wrong only on the empty collection (reject). Correct for
# every NON-empty collection (the common F2P/P2P sizes) but reports 1 for the
# empty pipeline. Isolates the empty / first-element sub-domain: the
# load-bearing Result() == len(steps) fails exactly when len(steps) == 0.
# ===========================================================================
_IMPL_EMPTY_OFF = """if len(steps) == 0:
        return 1
    return len(steps)"""


SPEC_TESTS = [
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: bind the cardinality to "
                     "a named int local `n = len(steps)` and return it. Same "
                     "observable value; no loop / fold lemma / branch introduced, "
                     "so the gold proof stays trivially valid. Must verify, else "
                     "SPEC-TOO-STRONG. Source: the soundness of the "
                     "Result() == len(steps) postcondition under a value-equivalent "
                     "reshape.",
    },
    {
        "id": "admissibility-readonly-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives IN-REGION that the half-permission input is usable "
                     "(Assert(len(steps) >= 0) reads under Acc(list_pred(steps),1/2)) "
                     "and reaches a normal non-raising return of the correct value "
                     "for an in-domain (F2P-shaped) input. If the Requires were "
                     "vacuous or over-strong the impl could not both consume the "
                     "half-permission read and return => PRECOND-TOO-STRONG. "
                     "Source: the Acc(list_pred(steps),1/2) Requires.",
    },
    {
        "id": "frame-mutation-write-steps",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which Pipeline.__len__ wrote back "
                      "into self.steps (e.g. self.steps[0] = self.steps[0], or "
                      "any in-place mutation) is not the gold hunk (`return "
                      "len(self.steps)` never mutates). self.steps is the "
                      "pipeline's ordered stage list that _iter, __getitem__, fit, "
                      "predict and the slicing API all read; a __len__ that mutated "
                      "it would corrupt every downstream pipeline operation and "
                      "break the many P2P pipeline tests (test_pipeline_slice / "
                      "index / fit), so the faithful mutating patch would NOT "
                      "resolve. (A size query must be side-effect free.)",
        "rationale": "composite_size holds only Acc(list_pred(steps), 1/2). The "
                     "value-neutral indexed write steps[0] = 0 (guarded in-bounds) "
                     "needs FULL permission => Nagini rejects for INSUFFICIENT "
                     "PERMISSION before any value reasoning. The gold "
                     "`return len(steps)` is kept verbatim so the rejection is "
                     "attributable to the write, not a spec change. Source: the "
                     "permission system + the Acc(list_pred(steps),1/2) Requires "
                     "AND Ensures (read-only frame, directive 5).",
    },
    {
        "id": "partial-domain-prepatch-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OFFBYONE),
        "refinement": "This IS the prepatch candidate (model_prepatch.py): the only "
                      "stage-traversal present in the surrounding code, "
                      "_iter(with_final=False), does `stop -= 1` — walking one fewer "
                      "than len(self.steps). A real __len__ reusing that truncated "
                      "count returns len(self.steps) - 1, so for the F2P 2-step "
                      "pipeline it reports 1, and the F2P assertion "
                      "`assert len(pipeline) == 2` FAILS — the faithful patch does "
                      "NOT resolve. It also breaks `pipe[:len(pipe)]` (drops the "
                      "terminal stage from the span).",
        "rationale": "Returns len(steps) - 1, violating the load-bearing "
                     "Result() == len(steps) on EVERY input. Source: the "
                     "Result() == len(steps) postcondition clause — exactly the "
                     "clause G-DIFF reports the prepatch model failing on.",
    },
    {
        "id": "partial-domain-constant-f2p-size",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_CONST2),
        "refinement": "A faithful real patch `def __len__(self): return 2` passes "
                      "the F2P assertion `len(pipeline) == 2` (the 2-step pipeline) "
                      "but is correct ONLY at cardinality 2: it breaks the P2P "
                      "indexing/slice tests (test_pipeline_slice / test_pipeline_index "
                      "build pipelines of other sizes and rely on `pipe[:len(pipe)]` "
                      "spanning the whole collection), so it does NOT resolve. A "
                      "constant size is the canonical pins-only-part-of-the-domain "
                      "rival.",
        "rationale": "Returns the constant 2, violating Result() == len(steps) on "
                     "every input whose length != 2. Source: the "
                     "Result() == len(steps) postcondition clause (it pins ALL "
                     "cardinalities, not just the F2P witness).",
    },
    {
        "id": "partial-domain-empty-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_EMPTY_OFF),
        "refinement": "A faithful real patch that special-cased the empty pipeline "
                      "to report size 1 (e.g. `return len(self.steps) or 1`) is "
                      "correct for every NON-empty pipeline but mis-reports the "
                      "empty composite (`make_pipeline()` / `Pipeline([])` would "
                      "claim one stage), so `pipe[:len(pipe)]` would over-span and "
                      "index a non-existent stage. It diverges from the gold "
                      "`len(self.steps)` exactly on the empty sub-domain, so the "
                      "faithful patch does NOT resolve on that domain.",
        "rationale": "Returns 1 when len(steps) == 0 (correct otherwise), violating "
                     "Result() == len(steps) exactly on the empty / first-element "
                     "sub-domain. Source: the Result() == len(steps) postcondition "
                     "clause, which pins the count on the empty input too.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom) and there is
# no A-reference deep model. `len` is the Python builtin modelled DEEPLY as
# Nagini's len over the List[int] carrier — there is no real callee whose
# Ensures must be validated. axiom_check.py records, for completeness, the single
# trivial refinement fact (real len(self.steps) equals the constructed stage
# count, across single/multi/placeholder collections and the F2P 2-step case),
# stdlib-only, exit 0; G-AX is vacuous. Re-encoding that as a Docker probe would
# add nothing. See 'assessment' in the structured return.
AXIOM_TESTS = []
