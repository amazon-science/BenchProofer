# properties.py — PBT falsification battery for django__django-14007.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap a
# whole `# impl-start` .. `# impl-end` body for ONE of the two modeled functions
# (apply_row / execute_returning) and leave the frozen spec (axioms / pure /
# pre / post-conditions / signatures) byte-identical. same_spec is therefore
# guaranteed for every case. (The `invariants` region is nested INSIDE impl and
# is elided from the spec view too, so reshaping the proof never breaks
# same_spec — but a positive control must KEEP the loop invariants + framing
# asserts it still needs, or it fails for a PROOF reason, not a spec reason.)
#
# Defended surface (read from model.py / refinement.md / instance.json):
#   apply_row(row, chains, ncols) pins, per column p < ncols:
#     (W) len(Result()) == ncols                                   -- width kept
#     (F) Result()[p] == fold_chain(chains[p], row[p])             -- the fold
#   execute_returning(rows, chains, ncols) pins:
#     (N) len(Result()) == len(rows)                               -- row count
#     (Wj) len(Result()[j]) == ncols  for every row j              -- width kept
#     (Fjp) Result()[j][p] == fold_chain(chains[p], rows[j][p])    -- THE delta
#   (Fjp)/(F) is the discriminating fix: the returned insert rows are run
#   through the per-column converter pipeline (left-fold of the chain over the
#   raw value), identity where a column's chain is empty. The F2P
#   test_auto_field_subclass_create asserts the created object's id is a
#   MyWrapper -- i.e. from_db_value (one non-empty chain) WAS applied, the
#   converted-vs-raw distinction. The pre-patch returned the raw rows and FAILS
#   (Fjp) on any non-empty chain because `step` is OPAQUE (Ensures(True)), so a
#   raw value is not provably equal to fold_chain over a non-empty chain.
#
# Read-only inputs: NONE in the Acc(...,1/2) sense. `rows`, `chains` and the
# Result() are PURE sequences (PSeq[...]), which carry NO heap permission at
# all -- the spec quantifies over them directly. ncols is an immutable int.
# There is therefore no half-permission heap parameter an impl could overwrite,
# so the frame-mutation weakness class does NOT apply to this bundle (a PSeq is
# immutable: `out = out + PSeq(nv)` rebinds a local, it does not mutate `rows`).
# See 'assessment' in the structured return for the full justification and what
# stands in for it (the raw-passthrough uniqueness attacks below).
#
# Oracle grounding: fold_chain is @Pure but GROUNDED -- it is fully unfolded
# (front-recursive over `chain`) as a deterministic function of (chains[p],
# row[p]), which are actual arguments; `step` is @Pure @ContractOnly with the
# weakest contract Ensures(True). There is no ungrounded answer-key to echo: the
# only "echo" of the raw value (return rows unchanged) is exactly the pre-patch,
# and it CORRECTLY fails (Fjp) on a non-empty chain. So instead of an
# ungrounded-oracle-echo case, the honest stand-in is (a) the cheapest-correct
# positive control that computes the grounded fold directly, and (b) the
# raw-passthrough uniqueness attacks that the grounded oracle rightly rejects.
from pathlib import Path

INSTANCE = "django__django-14007"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two whole-impl anchors. Each is the EXACT body between `# impl-start` and
# `# impl-end` for one function (verbatim from model.py). We replace the body
# and re-emit the `# impl-end` marker so the region boundary stays put and the
# swap is strictly inside one function's impl region.
# ---------------------------------------------------------------------------

_AR_IMPL = """    out = PSeq(0).take(0)  # type: PSeq[int]
    p = 0
    while p < ncols:
        # invariants-start
        Invariant(0 <= p and p <= ncols)
        Invariant(len(row) == ncols)
        Invariant(len(chains) == ncols)
        Invariant(len(out) == p)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[int]
        nv = fold_chain(chains[p], row[p])
        out = out + PSeq(nv)
        Assert(out[p] == nv)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,
            out[k] == old[k]), [[out[k]]])))
        p = p + 1
    return out
    # impl-end"""

_ER_IMPL = """    out = rows.take(0)  # type: PSeq[PSeq[int]]
    j = 0
    while j < len(rows):
        # invariants-start
        Invariant(0 <= j and j <= len(rows))
        Invariant(len(chains) == ncols)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),
            len(rows[k]) == ncols), [[rows[k]]])))
        Invariant(len(out) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            len(out[k]) == ncols), [[out[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
            Forall(int, lambda p: (Implies(0 <= p and p < ncols,
                out[k][p] == fold_chain(chains[p], rows[k][p])),
                [[out[k][p]]]))), [[out[k]]])))
        # invariants-end
        old = out  # type: PSeq[PSeq[int]]
        cr = apply_row(rows[j], chains, ncols)
        out = out + PSeq(cr)
        Assert(out[j] is cr)
        Assert(len(out[j]) == ncols)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
            out[k] is old[k]), [[out[k]]])))
        j = j + 1
    return out
    # impl-end"""


def _ar(new_body: str) -> str:
    """Replace ONLY apply_row's impl body (keep the trailing `# impl-end`)."""
    return _swap(_BASE, _AR_IMPL, new_body + "\n    # impl-end")


def _er(new_body: str) -> str:
    """Replace ONLY execute_returning's impl body."""
    return _swap(_BASE, _ER_IMPL, new_body + "\n    # impl-end")


SPEC_TESTS = [

    # ----------------------------------------------------------------- soundness
    # POSITIVE CONTROL #1 (apply_row, structural reshape). The loop is kept
    # forward (front-recursive fold_chain => forward-append is the gold-proof
    # shape; a backward loop would need an f(a+b) split lemma the verifier will
    # NOT auto-discharge -- AVOID per directive 3). We reshape locally: bind the
    # fold to `conv` first, append, and KEEP both framing asserts (the per-prefix
    # preservation and the new-element pin) plus every loop invariant verbatim,
    # so the gold proof obligations are all still discharged. If this cannot
    # verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-apply-row-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _ar(
            "    empty = PSeq(0).take(0)  # type: PSeq[int]\n"
            "    out = empty\n"
            "    p = 0\n"
            "    while p < ncols:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= p and p <= ncols)\n"
            "        Invariant(len(row) == ncols)\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(len(out) == p)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,\n"
            "            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))\n"
            "        # invariants-end\n"
            "        prev = out  # type: PSeq[int]\n"
            "        conv = fold_chain(chains[p], row[p])\n"
            "        tail = PSeq(conv)  # type: PSeq[int]\n"
            "        out = prev + tail\n"
            "        Assert(out[p] == conv)\n"
            "        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,\n"
            "            out[k] == prev[k]), [[out[k]]])))\n"
            "        p = p + 1\n"
            "    return out"
        ),
        "rationale": "a correct, locally-reshaped (extra typed locals, same "
                     "forward-append shape) impl that keeps every loop invariant "
                     "and both framing asserts must verify; else SPEC-TOO-STRONG. "
                     "Forward-append is the gold-proof shape for the "
                     "front-recursive fold_chain (a reverse loop would need a "
                     "fold-split lemma -- avoided).",
    },

    # POSITIVE CONTROL #2 (execute_returning, structural reshape). Same forward
    # loop, but the per-row converted result is bound through an extra typed
    # local and the singleton sequence built separately. KEEP all three loop
    # invariants and all three framing asserts (the `is cr` identity, the width,
    # and the per-prefix `is old[k]` preservation). Must verify; else
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-exec-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _er(
            "    base = rows.take(0)  # type: PSeq[PSeq[int]]\n"
            "    out = base\n"
            "    j = 0\n"
            "    while j < len(rows):\n"
            "        # invariants-start\n"
            "        Invariant(0 <= j and j <= len(rows))\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),\n"
            "            len(rows[k]) == ncols), [[rows[k]]])))\n"
            "        Invariant(len(out) == j)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            len(out[k]) == ncols), [[out[k]]])))\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            Forall(int, lambda p: (Implies(0 <= p and p < ncols,\n"
            "                out[k][p] == fold_chain(chains[p], rows[k][p])),\n"
            "                [[out[k][p]]]))), [[out[k]]])))\n"
            "        # invariants-end\n"
            "        prev = out  # type: PSeq[PSeq[int]]\n"
            "        cr = apply_row(rows[j], chains, ncols)\n"
            "        rowseq = PSeq(cr)  # type: PSeq[PSeq[int]]\n"
            "        out = prev + rowseq\n"
            "        Assert(out[j] is cr)\n"
            "        Assert(len(out[j]) == ncols)\n"
            "        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            out[k] is prev[k]), [[out[k]]])))\n"
            "        j = j + 1\n"
            "    return out"
        ),
        "rationale": "a correct, locally-reshaped execute_returning that keeps "
                     "all loop invariants and the three framing asserts must "
                     "verify; else SPEC-TOO-STRONG.",
    },

    # ----------------------------------------------------------------- admissibility
    # A self-call caller in apply_row's impl region constructs an F2P-shaped
    # input (the issue's single-returning-column create case: ncols == 1, a
    # one-element row and a one-element chains seq) and invokes apply_row on it,
    # then asserts a postcondition consequence. If the Requires (ncols>=0,
    # len(row)==ncols, len(chains)==ncols) cannot be established for a normal
    # input => PRECOND-TOO-STRONG. We keep the original loop verbatim so the
    # function still satisfies its own postcondition, then add the probe.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ar(
            "    out = PSeq(0).take(0)  # type: PSeq[int]\n"
            "    p = 0\n"
            "    while p < ncols:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= p and p <= ncols)\n"
            "        Invariant(len(row) == ncols)\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(len(out) == p)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < p,\n"
            "            out[k] == fold_chain(chains[k], row[k])), [[out[k]]])))\n"
            "        # invariants-end\n"
            "        old = out  # type: PSeq[int]\n"
            "        nv = fold_chain(chains[p], row[p])\n"
            "        out = out + PSeq(nv)\n"
            "        Assert(out[p] == nv)\n"
            "        Assert(Forall(int, lambda k: (Implies(0 <= k and k < p,\n"
            "            out[k] == old[k]), [[out[k]]])))\n"
            "        p = p + 1\n"
            "    # admissibility probe: the issue's create case is one returning\n"
            "    # column whose chain is the single from_db_value converter. A\n"
            "    # one-element row + one-element chains seq + ncols==1 satisfies\n"
            "    # Requires; the call site verifies and the post fact is derivable.\n"
            "    prow = PSeq(2)  # type: PSeq[int]\n"
            "    pchain = PSeq(9)  # type: PSeq[int]\n"
            "    pchains = PSeq(pchain)  # type: PSeq[PSeq[int]]\n"
            "    res = apply_row(prow, pchains, 1)\n"
            "    Assert(len(res) == 1)\n"
            "    Assert(res[0] == fold_chain(pchains[0], prow[0]))\n"
            "    return out"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input (one "
                     "returning column with a single converter); the self-call "
                     "verifies and the post fact is derivable, else "
                     "PRECOND-TOO-STRONG.",
    },

    # ----------------------------------------------------------------- uniqueness
    # ATTACK 1 (THE bug-delta: raw passthrough in execute_returning). Re-emit
    # each raw row unchanged -- exactly model_prepatch.py / the pre-patch
    # `return rows`. This must FAIL (Fjp) on any non-empty chain: fold_chain over
    # a non-empty chain invokes the OPAQUE step (Ensures(True)), so the raw value
    # is not provably equal to it. The clearest converted-vs-raw discriminator.
    {
        "id": "weak-exec-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _er(
            "    out = rows.take(0)  # type: PSeq[PSeq[int]]\n"
            "    j = 0\n"
            "    while j < len(rows):\n"
            "        # invariants-start\n"
            "        Invariant(0 <= j and j <= len(rows))\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),\n"
            "            len(rows[k]) == ncols), [[rows[k]]])))\n"
            "        Invariant(len(out) == j)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            len(out[k]) == ncols), [[out[k]]])))\n"
            "        # invariants-end\n"
            "        out = out + PSeq(rows[j])\n"
            "        j = j + 1\n"
            "    return out"
        ),
        "refinement": "this is the pre-patch `return rows` (the three branches "
                      "returned the raw fetched rows, never running them through "
                      "self.apply_converters). The F2P test_auto_field_subclass_"
                      "create asserts the created id is a MyWrapper, i.e. "
                      "from_db_value was applied; raw passthrough leaves a plain "
                      "int => the faithful real patch (no apply_converters call) "
                      "FAILS the F2P and does NOT resolve.",
        "rationale": "violates postcondition (Fjp) Result()[j][p] == "
                     "fold_chain(chains[p], rows[j][p]) on any non-empty chain, "
                     "because step is opaque (Ensures(True)) so the raw value is "
                     "not provably the fold.",
    },

    # ATTACK 2 (raw passthrough at the row level, apply_row). Re-emit the raw
    # column value instead of the fold. Same defect at the inner function: a raw
    # column is not provably the fold over a non-empty chain. Pins (F).
    {
        "id": "weak-row-raw-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ar(
            "    out = PSeq(0).take(0)  # type: PSeq[int]\n"
            "    p = 0\n"
            "    while p < ncols:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= p and p <= ncols)\n"
            "        Invariant(len(row) == ncols)\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(len(out) == p)\n"
            "        # invariants-end\n"
            "        out = out + PSeq(row[p])\n"
            "        p = p + 1\n"
            "    return out"
        ),
        "refinement": "this returns the raw column values (the per-row body never "
                      "runs the converter fold). In the real apply_converters the "
                      "from_db_value column would stay a plain int, so the created "
                      "id is not a MyWrapper => the F2P fails; the faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates postcondition (F) Result()[p] == "
                     "fold_chain(chains[p], row[p]) on any non-empty chain (raw "
                     "value vs the opaque-step fold).",
    },

    # ATTACK 3 (partial-domain: only the FIRST column is converted). Fold column
    # 0 correctly, but re-emit the raw value for every column p >= 1. CORRECT for
    # ncols <= 1 (the issue's single-PK-column create case!) but WRONG for any
    # multi-column returning set whose column p>=1 has a non-empty chain. A
    # value-proxy that only inspected column 0 would miss it; (F) pins EVERY
    # column, so it must reject.
    {
        "id": "weak-row-first-col-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ar(
            "    out = PSeq(0).take(0)  # type: PSeq[int]\n"
            "    p = 0\n"
            "    while p < ncols:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= p and p <= ncols)\n"
            "        Invariant(len(row) == ncols)\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(len(out) == p)\n"
            "        # invariants-end\n"
            "        if p == 0:\n"
            "            nv = fold_chain(chains[p], row[p])  # type: int\n"
            "        else:\n"
            "            nv = row[p]\n"
            "        out = out + PSeq(nv)\n"
            "        p = p + 1\n"
            "    return out"
        ),
        "refinement": "this converts only the first returning column and leaves "
                      "the rest raw. bulk_create / multi-field returning sets "
                      "(e.g. a from_db_value on a non-first returning field) would "
                      "keep that column a plain int instead of the wrapper => the "
                      "converted-vs-raw assertion fails on that column; the "
                      "faithful real patch (apply_converters only on col 0) does "
                      "NOT resolve such a case. apply_converters folds EVERY "
                      "converter-bearing column.",
        "rationale": "violates postcondition (F) for any column p>=1 with a "
                     "non-empty chain (raw value vs the fold there).",
    },

    # ATTACK 4 (off-by-one in the fold: drop the FIRST converter of each chain).
    # Apply fold_chain(chains[p].drop(1), row[p]) -- i.e. skip the head
    # converter. CORRECT only when every chain has length <= 1 (drop(1) of a
    # 1-elt chain is empty => identity == the single step? NO: drop(1) of a
    # 1-chain is empty => returns raw, which is WRONG for a 1-chain too). So this
    # is wrong on EVERY non-empty chain (it under-applies). A double-mask attack:
    # the structure (a fold over a chain) is present, but the wrong slice.
    {
        "id": "weak-row-drop-head-converter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ar(
            "    out = PSeq(0).take(0)  # type: PSeq[int]\n"
            "    p = 0\n"
            "    while p < ncols:\n"
            "        # invariants-start\n"
            "        Invariant(0 <= p and p <= ncols)\n"
            "        Invariant(len(row) == ncols)\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(len(out) == p)\n"
            "        # invariants-end\n"
            "        nv = fold_chain(chains[p].drop(1), row[p])  # type: int\n"
            "        out = out + PSeq(nv)\n"
            "        p = p + 1\n"
            "    return out"
        ),
        "refinement": "this skips the first converter of each column's chain. For "
                      "the F2P field the chain is exactly [from_db_value]; dropping "
                      "it leaves the raw int (never wrapped) => the created id is "
                      "not a MyWrapper and the F2P fails. For longer chains it "
                      "applies the wrong (truncated) conversion; the faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates postcondition (F): fold over chains[p].drop(1) "
                     "differs from fold over chains[p] whenever chains[p] is "
                     "non-empty (the dropped head step is opaque, not identity).",
    },

    # ATTACK 5 (supporting near-miss: drop the LAST row in execute_returning).
    # Convert every row correctly but emit one fewer row (skip the final row).
    # Correct on the per-element fold for the rows it does emit, but violates the
    # row-count clause (N) len(Result()) == len(rows). Cheap supporting case,
    # still carries a real refinement (bulk_create returns one object per input).
    {
        "id": "weak-exec-drop-last-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _er(
            "    out = rows.take(0)  # type: PSeq[PSeq[int]]\n"
            "    j = 0\n"
            "    while j + 1 < len(rows):\n"
            "        # invariants-start\n"
            "        Invariant(0 <= j and j <= len(rows))\n"
            "        Invariant(len(chains) == ncols)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(rows),\n"
            "            len(rows[k]) == ncols), [[rows[k]]])))\n"
            "        Invariant(len(out) == j)\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            len(out[k]) == ncols), [[out[k]]])))\n"
            "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            Forall(int, lambda p: (Implies(0 <= p and p < ncols,\n"
            "                out[k][p] == fold_chain(chains[p], rows[k][p])),\n"
            "                [[out[k][p]]]))), [[out[k]]])))\n"
            "        # invariants-end\n"
            "        old = out  # type: PSeq[PSeq[int]]\n"
            "        cr = apply_row(rows[j], chains, ncols)\n"
            "        out = out + PSeq(cr)\n"
            "        Assert(out[j] is cr)\n"
            "        Assert(len(out[j]) == ncols)\n"
            "        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,\n"
            "            out[k] is old[k]), [[out[k]]])))\n"
            "        j = j + 1\n"
            "    return out"
        ),
        "refinement": "this returns one fewer converted row than it received "
                      "(skips the last). bulk_create on a backend that returns "
                      "rows assigns one pk per input object; dropping the last row "
                      "loses an object's converted id => the faithful real patch "
                      "does NOT resolve (a bulk_create P2P/F2P would see a missing "
                      "row).",
        "rationale": "violates postcondition (N) len(Result()) == len(rows) "
                     "whenever len(rows) >= 1 (emits len(rows)-1 rows).",
    },
]


# ---------------------------------------------------------------------------
# Axiom lane. This bundle has ONE @ContractOnly axiom (`step`, A-consumed,
# Ensures(True)) and ONE A-reference deep model (fold_chain / apply_row /
# execute_returning == the real SQLCompiler.apply_converters). The existing
# host-validated G-AX oracle (axiom_check.py) CALLS the real apply_converters
# (imported from Django in-container; verbatim stdlib transcription as a robust
# fallback) and asserts the deep model equals it on 9 boundary + 20000 fuzz
# (rows x cols x per-column chain) cases, AND that representative real converters
# (incl. a from_db_value wrapper) return a value (meet step's Ensures(True)). We
# re-run that exact oracle in-container so the axiom lane is grounded in the REAL
# callee (never a regex over source). The runner mounts ONLY this probe script at
# /work, so axiom_check.py is read on the HOST at load time and embedded verbatim.
#
# Soundness: step's Ensures(True) cannot over-claim (it asserts nothing), so it
# is trivially sound for any total converter; the only failure mode is a converter
# that does not return -- the probe exercises real converter behaviour. The
# A-reference deep model must equal the real apply_converters on every
# caller-reachable input; the probe fuzzes that equality.
#
# Containment: the model passes `step` arbitrary int converter ids and int values
# (chains[p][i] and the running fold value), and `step`/`apply_converters` have NO
# Requires domain restriction (Ensures(True); apply_converters accepts any
# rows/converters dict). Every caller-reachable input is therefore inside the
# axiom domain -- there is no input the model can produce that lies outside it, so
# AXIOM-TOO-WEAK-FOR-CALLER cannot arise. The fuzz already spans 0..4 rows/cols and
# 0..3-length chains, i.e. the model's reachable shapes. No flag dependency (the
# fold is connection/expression-agnostic for the modeled converters).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-apply-converters-equals-deep-model-and-step-sound",
        "axiom": "step,apply_converters(A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        # The probe is the bundle's host-validated G-AX oracle, embedded verbatim
        # (the runner mounts only this script; axiom_check.py is NOT in-container).
        # It CALLS the real SQLCompiler.apply_converters (or the verbatim
        # transcription) on boundary + 20000 fuzz cases and asserts the deep model
        # equals it, and that representative real converters return a value (meet
        # step's Ensures(True)). It never scrapes source. No file is opened, so no
        # utf-8 codec concern. Exits 0 iff sound.
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "axiom-soundness + containment: step's Ensures(True) is "
                     "trivially met by any total converter (the probe runs real "
                     "from_db_value-style converters); the A-reference deep model "
                     "must equal the REAL apply_converters on every "
                     "caller-reachable (rows x cols x chain) shape -- a "
                     "disagreement => AXIOM-UNSOUND. Containment is trivial: "
                     "neither step nor apply_converters restricts its domain, so "
                     "every int id / int value / row-grid the model can reach is "
                     "in-domain (no AXIOM-TOO-WEAK-FOR-CALLER).",
    },
]
