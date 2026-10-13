"""properties.py — PBT falsification manifest for astropy__astropy-14182.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models the two independently-observable changes
of the gold patch (rst.py: WRITE framing index + READ data-start offset) as two
contracted functions over `List[int]` row tags, plus three @Pure helpers. There
are NO @ContractOnly axioms (meta.axioms == []), so AXIOM_TESTS == []. The two
A-reference deep models (`frame_index`, `data_start_index`) are validated == the
real astropy reader/writer by axiom_check.py (G-AX), out-of-band of this PBT.

THE DEFENDED SURFACE
--------------------
(1) `rst_frame_block(block: List[int], n: int, rule: int) -> List[int]`
    Frames the fixed-width block by repeating its closing rule line (at offset
    `n`) above and below. Read-only input `block` at `Acc(list_pred(block),1/2)`.
    The LOAD-BEARING postcondition pins the whole sequence:

        Ensures(ToSeq(Result()) == PSeq(rule_at(ToSeq(block),n))
                + ToSeq(block) + PSeq(rule_at(ToSeq(block),n)))
        Ensures(ToSeq(Result())[0]  == rule)
        Ensures(ToSeq(Result())[-1] == rule)

    `rule_at(rows,n)` is a @Pure accessor returning `rows[n]` — GROUNDED in the
    input, fully unfolded by Viper. `rule` is an OPAQUE per-block parameter, not
    a synthesisable constant (this is the post-G-EQ fix: a previous revision
    pinned the framing line to the fixed sentinel -1, letting `sep = -1` echo it
    without reading the input — the directive-8 hole. Now the framing value can
    be discharged ONLY by copying the actual input line `block[n]`).

(2) `data_row_offset(header_rows: List[int]) -> int`
    Returns the first-data-row offset `n + 2`. Read-only input `header_rows` at
    `Acc(list_pred(header_rows),1/2)`. LOAD-BEARING postcondition:

        Ensures(Result() == data_start_index(len(header_rows)))   # == n + 2
        Ensures(Result() == len(header_rows) + 2)

    The offset is a CONSTANT affine function of the header-row count; the
    pre-patch bug returns the constant 3 (correct only for n == 1).

ATTACKS THIS SPEC MUST SURVIVE
------------------------------
  * FRAME-MUTATION (MANDATORY, both functions have a 1/2 read-only input):
    `frame-mutate-block` writes through `block` before reading it;
    `frame-mutate-headers` writes through `header_rows`. Both must fail for
    INSUFFICIENT PERMISSION (the gold invariants kept verbatim so the rejection
    is attributable to the write).
  * UNGROUNDED-ORACLE ECHO is the historical hole: `wrong-const-echo` builds
    `sep = -1` (the old echoed sentinel). With `rule` opaque it cannot prove
    `-1 == rule`, so it must reject — re-confirming the G-EQ fix holds.
    `honest-cheapest` is the grounded positive control (the oracle IS a function
    of the arg `block[n]`, so the cheapest faithful impl still reads the input).
  * PARTIAL-DOMAIN: `frame-const-1` (the pre-patch `idx = 1`, correct only n==1)
    and `offset-const-3` (the pre-patch `return 3`, correct only n==1) pin only
    the single-header-row sub-domain. Both must reject for n != 1.
  * POSITIVE CONTROL (soundness): a structurally-different but correct impl of
    each function (a different but provably-equal index expression / a reshaped
    list build) MUST verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY: a self-call confirming the precondition admits an F2P-shaped
    input (n >= 1, block long enough, block[n]==rule, headers != rule).

  CONTROL-FLOW-EFFECT is N/A: both modeled functions are pure value/index
  computations with no raise/return/side-effect difference invisible to the
  value abstraction (no exception paths in either spec; the only effect is the
  returned sequence/int, fully pinned). VALUE-DOUBLE-MASK is N/A: the WRITE
  postcondition pins the ENTIRE sequence (not an index-via-value proxy that
  could drop disagreeing indices), and the READ postcondition pins a scalar.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION (or the permission
system), never from a tampered spec. Each `expect:"reject"` rival carries the
refinement argument that its faithful real patch would NOT resolve the F2P
(`test_rst_with_header_rows`, which exercises n == 3 header rows).
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14182"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError("drift: %r not in model.py" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r (%d)" % (old, src.count(old)))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two gold impl regions, verbatim, used as the surgery anchors.
# ---------------------------------------------------------------------------
_GOLD_FRAME = (
    "    idx = frame_index(n)\n"
    "    sep = block[idx]\n"
    "    result = [sep] + block + [sep]  # type: List[int]\n"
    "    return result\n"
)
_GOLD_OFFSET = (
    "    n = len(header_rows)\n"
    "    return 2 + n\n"
)


def _frame(new_body: str) -> str:
    return _swap(_BASE, _GOLD_FRAME, new_body)


def _offset(new_body: str) -> str:
    return _swap(_BASE, _GOLD_OFFSET, new_body)


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # -- POSITIVE CONTROLS (soundness): structurally-different CORRECT impls ---

    # rst_frame_block: index the block directly with `n` (instead of via the
    # @Pure `frame_index(n)`), and build the framed list as
    # block[n:n+1] is NOT available in Nagini; use the same selected element but
    # via a plain `n` local + a reshaped construction that prepends/appends a
    # one-element list literal. frame_index(n)==n is in the postcondition so the
    # verifier still proves the framing equality from `sep == block[n]`.
    {"id": "pos-frame-direct-n", "kind": "soundness", "expect": "verify",
     "module": _frame(
         "    sep = block[n]\n"
         "    front = [sep]  # type: List[int]\n"
         "    result = front + block + [sep]  # type: List[int]\n"
         "    return result\n"),
     "rationale": "structurally-different but CORRECT: indexes block with the "
                  "raw `n` (not via frame_index) and builds the list with a "
                  "pre-bound front local. frame_index(n)==n is an Ensures of the "
                  "@Pure helper, so the framing-equality postcondition still "
                  "discharges from sep==block[n]. Must verify (else SPEC-TOO-"
                  "STRONG)."},

    # data_row_offset: compute n+2 via a different-but-equal expression and a
    # reshaped local sequence (n + 1 + 1) — same value, different shape.
    {"id": "pos-offset-reassoc", "kind": "soundness", "expect": "verify",
     "module": _offset(
         "    n = len(header_rows)\n"
         "    return n + 1 + 1\n"),
     "rationale": "structurally-different but CORRECT: `n + 1 + 1` is the same "
                  "integer as `2 + n` and `data_start_index(n)==n+2`. Must "
                  "verify (else SPEC-TOO-STRONG)."},

    # -- ADMISSIBILITY: precondition admits an F2P-shaped input ----------------

    # The F2P (test_rst_with_header_rows) renders n == 3 header rows; the inner
    # block is [h0,h1,h2,rule,data...]. Encode an n==3 block as row tags with the
    # closing rule carrying an opaque value and the headers carrying others, then
    # self-call rst_frame_block and assert the precondition is establishable.
    {"id": "admiss-frame-n3", "kind": "admissibility", "expect": "verify",
     "module": _frame(_GOLD_FRAME +  # keep gold body, append an in-region caller
                      "\n"
                      "\n"
                      "def _admiss_frame_caller() -> None:\n"
                      "    # F2P shape: n=3 header rows, block long enough, the\n"
                      "    # closing rule at offset 3 carries an opaque value 7,\n"
                      "    # the 3 header rows carry values != 7. A normal input\n"
                      "    # must establish Requires (else PRECOND-TOO-STRONG).\n"
                      "    blk = [1, 2, 3, 7, 9, 9]  # type: List[int]\n"
                      "    out = rst_frame_block(blk, 3, 7)\n"
                      "    Assert(len(out) == 8)\n"),
     "rationale": "the precondition (n>=1, len(block)>n, block[n]==rule, headers"
                  " != rule) must accept the F2P-shaped n==3 block. If the self-"
                  "call cannot establish Requires => PRECOND-TOO-STRONG."},

    {"id": "admiss-offset-n3", "kind": "admissibility", "expect": "verify",
     "module": _offset(_GOLD_OFFSET +
                       "\n"
                       "\n"
                       "def _admiss_offset_caller() -> None:\n"
                       "    # F2P shape: 3 header rows -> data start offset 5.\n"
                       "    hdr = [1, 2, 3]  # type: List[int]\n"
                       "    ds = data_row_offset(hdr)\n"
                       "    Assert(ds == 5)\n"),
     "rationale": "the precondition (len(header_rows)>=1) must accept the F2P "
                  "n==3 header list; result must be 5 (else PRECOND-TOO-STRONG)."},

    # -- FRAME-MUTATION (MANDATORY: both inputs are Acc(...,1/2) read-only) -----

    # rst_frame_block: WRITE through `block` (held at 1/2) before reading it.
    # Storing `block[idx] = rule` overwrites the closing rule line so the gold
    # postcondition would be trivially satisfiable IF the write were permitted —
    # but a store through a 1/2 list_pred is INSUFFICIENT PERMISSION, so it must
    # reject. Gold invariants kept verbatim so the rejection is attributable to
    # the write, not to a weakened spec.
    {"id": "frame-mutate-block", "kind": "uniqueness", "expect": "reject",
     "module": _frame(
         "    idx = frame_index(n)\n"
         "    block[idx] = rule\n"          # <-- write through 1/2 permission
         "    sep = block[idx]\n"
         "    result = [sep] + block + [sep]  # type: List[int]\n"
         "    return result\n"),
     "refinement": "the real RST.write receives `lines` from super().write and "
                   "must NOT overwrite the rendered block — overwriting "
                   "lines[idx] would corrupt the table content and the F2P "
                   "round-trip (test_rst_with_header_rows asserts "
                   "out.getvalue().splitlines() == the exact 8 input lines). A "
                   "patch that mutates its input does not produce the gold "
                   "output, so it would NOT resolve.",
     "rationale": "MANDATORY frame-mutation probe. `block[idx] = rule` writes "
                  "through Acc(list_pred(block),1/2). Nagini requires FULL "
                  "permission for a store; with only 1/2 the assignment fails "
                  "for INSUFFICIENT PERMISSION. Rejection comes from the "
                  "permission system, not the postcondition."},

    # data_row_offset: WRITE through `header_rows` (held at 1/2). len>=1 so
    # index 0 is in bounds; the store needs full permission and must reject.
    {"id": "frame-mutate-headers", "kind": "uniqueness", "expect": "reject",
     "module": _offset(
         "    header_rows[0] = 0\n"          # <-- write through 1/2 permission
         "    n = len(header_rows)\n"
         "    return 2 + n\n"),
     "refinement": "the real RST.read only reads len(self.header.header_rows) "
                   "to compute start_line; it never writes into the header list. "
                   "A patch that mutates header_rows would corrupt the header "
                   "metadata and not match gold READ behaviour, so it would NOT "
                   "resolve.",
     "rationale": "MANDATORY frame-mutation probe on the second read-only input. "
                  "`header_rows[0] = 0` writes through Acc(list_pred(header_rows)"
                  ",1/2); a store needs full permission. Rejects for INSUFFICIENT "
                  "PERMISSION, not the postcondition."},

    # -- UNGROUNDED-ORACLE ECHO (historical directive-8 hole) ------------------

    # The previous revision pinned the framing line to the fixed sentinel -1
    # (RULE()==-1); `sep = -1` echoed it without reading the input. With `rule`
    # now OPAQUE, the impl cannot prove -1 == rule, so the framing-equality
    # postcondition (Result()[0] == rule) must reject. This re-confirms the fix.
    {"id": "wrong-const-echo", "kind": "uniqueness", "expect": "reject",
     "module": _frame(
         "    sep = -1\n"
         "    result = [sep] + block + [sep]  # type: List[int]\n"
         "    return result\n"),
     "refinement": "echoing a synthesised constant -1 ignores the actual "
                   "rendered rule line. The real RST.write must emit the actual "
                   "rule string (e.g. '======= ======== ===='); a patch that "
                   "wrote a literal sentinel instead of lines[idx] produces "
                   "garbage frame lines and fails the F2P round-trip equality, "
                   "so it would NOT resolve.",
     "rationale": "UNGROUNDED-ORACLE ECHO. The framing value `rule` is an opaque "
                  "per-block parameter (not a constant), so the verifier cannot "
                  "prove -1 == rule; the Ensures(Result()[0]==rule) clause "
                  "rejects. This is the directive-8 marker-echo cheat the G-EQ "
                  "panel closed by grounding the rule line in the input carrier."},

    # honest cheapest positive control for the grounded oracle: the cheapest
    # impl that satisfies the framing pin still has to READ block[n] (the oracle
    # is a function of the arg, so there is no shortcut). Verifies.
    {"id": "honest-cheapest", "kind": "soundness", "expect": "verify",
     "module": _frame(
         "    sep = block[frame_index(n)]\n"
         "    result = [sep] + block + [sep]  # type: List[int]\n"
         "    return result\n"),
     "rationale": "the grounded-oracle positive control: because `rule` is "
                  "block[n] (a function of the arg, fully unfolded), the cheapest "
                  "faithful impl still reads block[frame_index(n)]. It must "
                  "verify, proving the spec is satisfiable by honest work (no "
                  "echo shortcut exists for a grounded oracle)."},

    # -- PARTIAL-DOMAIN: pin only the single-header-row sub-domain -------------

    # The pre-patch WRITE bug: idx = 1 (correct only when n == 1). For n != 1
    # block[1] is a header row (value != rule), so block[1] != rule and the
    # framing-equality postcondition fails. This is the exact model_prepatch.py.
    {"id": "frame-const-1", "kind": "uniqueness", "expect": "reject",
     "module": _frame(
         "    sep = block[1]\n"
         "    result = [sep] + block + [sep]  # type: List[int]\n"
         "    return result\n"),
     "refinement": "this IS the pre-patch code (`lines = [lines[1]] + lines + "
                   "[lines[1]]`). For n != 1 (the F2P uses n == 3) lines[1] is a "
                   "header text row, not the closing rule, so the framed output "
                   "differs from gold and the F2P round-trip "
                   "(test_rst_with_header_rows, header_rows of length 3) fails. "
                   "It would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN: pins only n==1. For n>=2, block[1] is a "
                  "header row whose value != rule (Requires: headers != rule), "
                  "so Result()[0]==block[1]!=rule violates Ensures(Result()[0]"
                  "==rule) and the full-sequence equality. Rejection from the "
                  "framing postcondition (model_prepatch.py)."},

    # The pre-patch READ bug: return the constant 3 (correct only when n == 1).
    # data_start_index(n) == n + 2; for n != 1, 3 != n + 2. model_prepatch_2.py.
    {"id": "offset-const-3", "kind": "uniqueness", "expect": "reject",
     "module": _offset(
         "    return 3\n"),
     "refinement": "this IS the pre-patch code (`start_line = 3`). For n != 1 "
                   "(the F2P uses n == 3, expecting data start 5) the data slice "
                   "begins at the wrong processed line, so reading "
                   "test_rst_with_header_rows recovers the wrong rows / units / "
                   "dtypes and the F2P assertions fail. It would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN: pins only n==1. data_start_index(n)==n+2, so "
                  "for n>=2 the constant 3 != n+2 violates Ensures(Result()=="
                  "data_start_index(len(header_rows))) and Result()==len+2. "
                  "Rejection from the offset postcondition (model_prepatch_2.py)."},

    # supporting near-miss: off-by-one on the READ offset (n+1 instead of n+2)
    # — wrong for EVERY n, a cheap mutant that the constant-pin must reject.
    {"id": "offset-off-by-one", "kind": "uniqueness", "expect": "reject",
     "module": _offset(
         "    n = len(header_rows)\n"
         "    return 1 + n\n"),
     "refinement": "n+1 lands on the closing header rule line, not the first "
                   "data row; the base reader would slice from the rule and the "
                   "F2P round-trip mis-parses the data, so it would NOT resolve.",
     "rationale": "supporting near-miss: 1+n != n+2 for all n, violating "
                  "Result()==len(header_rows)+2 and data_start_index(n). Cheap "
                  "mutant; the constant-affine pin rejects it (offset postcond)."},
]

# ===========================================================================
# AXIOM CASES — none.
# ===========================================================================
# meta.axioms == [] (no @ContractOnly axioms). The two A-reference deep models
# (frame_index, data_start_index) are validated == the real astropy RST
# reader/writer by axiom_check.py (G-AX, in-container, header-row counts 1..3 +
# 400 fuzz shapes + a full QTable.read round-trip). PBT's axiom lane only covers
# @ContractOnly axioms / A-reference deep-model containment that is NOT already
# discharged by G-AX; here G-AX already executes the real callee and asserts the
# two formulas, so there is no additional axiom obligation for this lane.
AXIOM_TESTS = []
