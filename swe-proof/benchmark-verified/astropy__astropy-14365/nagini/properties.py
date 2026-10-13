# properties.py — PBT falsification battery for astropy__astropy-14365.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py source whose SPEC (axioms/pure/pre/post-
# conditions/invariants/signatures) is byte-identical to the frozen model.py —
# only text INSIDE an `# impl-start`/`# impl-end` region is changed — checked by
# markers.same_spec. Spec cases are checked by Nagini verify on the host.
#
# Defended surface (read from model.py + refinement.md + meta.json):
#   Three leaf deciders, each with READ-ONLY (Acc(...,1/2)) input(s):
#     masked_field(field)            : Ensures Result() == is_masked_field(ToSeq(field))
#     reserved_data_token(field)     : Ensures Result() == is_reserved_data_token(ToSeq(field))
#     command_line(tok0,tok1,ncols)  : Ensures Result() == is_command_tokens(ToSeq(tok0),ToSeq(tok1),ncols)
#   The load-bearing postcondition clause in every case is the `Result() == is_X(...)`
#   equality to a @Pure predicate that is FULLY GROUNDED in the args (an unfold of
#   `upseq`/`up` over the input code points). There is NO opaque answer-key oracle:
#   `is_masked_field`/`is_reserved_data_token`/`is_command_tokens` compute the
#   verdict from the args themselves, so a "echo the oracle" impl is simply the
#   CORRECT impl, not a wrong one (see UNGROUNDED-ORACLE note in assessment / the
#   ECHO positive control below). The witness Ensures (`no`/`NO`, `read serr`,
#   `READ SERR`) pin the case-insensitive behaviour the F2P/P2P exercises.
#
# Attacks (each reject case carries the refinement argument that its faithful real
# patch would NOT resolve the F2P/P2P, so a verifying rival is a real verify⇏resolve
# break, not an artifact):
#   - FRAME-MUTATION (MANDATORY, read-only inputs): a rival that WRITES the
#     half-permission input to satisfy the postcondition vacuously must be rejected
#     for INSUFFICIENT PERMISSION (the spec only grants Acc(...,1/2)).
#   - PARTIAL-DOMAIN: rivals correct on the witness sub-domain but diverging on a
#     case variant / sign / keyword the F2P relies on (these reproduce the three
#     prepatch behaviours: case-sensitive raw comparison).
#   - POSITIVE CONTROL (soundness): structurally-different-but-correct impls
#     (branch-reorder; honest grounded "echo" of the @Pure predicate) MUST verify.
#   - ADMISSIBILITY: the gold impl verifies on the normal F2P-shaped input, so the
#     precondition admits it.
from pathlib import Path

INSTANCE = "astropy__astropy-14365"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# --- region-surgery helpers --------------------------------------------------
# Each modeled function has exactly one `# impl-start` ... `# impl-end` region.
# We replace the WHOLE body between those markers, so the edit is GUARANTEED to
# stay inside the impl region (same_spec preserved).

_START = "    # impl-start\n"
_END = "    # impl-end"


def _region_body(src, occ):
    """Return the text strictly between the `occ`-th impl-start marker and the
    following impl-end marker (markers excluded). occ is 1-based."""
    idx = -1
    for _ in range(occ):
        idx = src.index(_START, idx + 1)
    s = idx + len(_START)
    e = src.index(_END, s)
    return src[s:e]


# 1 = masked_field, 2 = reserved_data_token, 3 = command_line (source order).
_BODY_MASKED = _region_body(_BASE, 1)
_BODY_RESERVED = _region_body(_BASE, 2)
_BODY_COMMAND = _region_body(_BASE, 3)
for _b in (_BODY_MASKED, _BODY_RESERVED, _BODY_COMMAND):
    assert _BASE.count(_b) == 1, "region body not unique; cannot do region surgery"


def _replace_body(old_body, new_body):
    """Return _BASE with `old_body` (a full impl-region body) swapped for
    `new_body`. Raises if the body drifted or is non-unique."""
    if old_body not in _BASE:
        raise AssertionError("drift: impl-region body not found")
    if _BASE.count(old_body) != 1:
        raise AssertionError("not unique: impl-region body")
    return _BASE.replace(old_body, new_body, 1)


# =============================================================================
# POSITIVE CONTROLS (soundness) — structurally different CORRECT impls; verify.
# =============================================================================

# masked_field: branch-REORDER positive control. Same backward front-recursive
# fold (so the gold loop invariant `ToSeq(folded) == upseq(ToSeq(field).drop(i))`
# and every witness lemma are unchanged), but the branch order is changed to
# test the long-s code point first. This keeps EVERY gold proof obligation
# (directives 2 & 3: no loop-direction flip, no dropped framing assert).
_POS_MASKED = """    folded = []  # type: List[int]
    i = len(field)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field), 1 / 2))
        Invariant(Acc(list_pred(folded)))
        Invariant(0 <= i and i <= len(field))
        Invariant(ToSeq(folded) == upseq(ToSeq(field).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = field[i - 1]
        Assert(ToSeq(field).drop(i - 1)[0] == c)
        Assert(ToSeq(field).drop(i - 1).drop(1) == ToSeq(field).drop(i))
        if c == 383:
            folded = [83] + folded
        elif 97 <= c and c <= 122:
            folded = [c - 32] + folded
        else:
            folded = [c] + folded
        i = i - 1
    Assert(ToSeq(field).drop(0) == ToSeq(field))
    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())
    Assert(upseq(PSeq(110, 111)) == kw_NO())
    return ToSeq(folded) == kw_NO()
"""

# masked_field: honest GROUNDED-ECHO positive control. Because the postcondition
# oracle `is_masked_field` is fully grounded in the arg (a @Pure unfold of upseq
# over the input), the cheapest CORRECT impl is to simply return the predicate
# applied to ToSeq(field). This is the "echo" an ungrounded-oracle attack would
# exploit — but here it is CORRECT (not a wrong echo), so it MUST verify. Its
# verifying is the proof that there is no wrong echo to build (see assessment).
# We KEEP the gold WITNESS-LEMMA asserts (the upseq-unfold of the two concrete
# spellings) so the two witness Ensures discharge without a proof gap (directive
# 2: keep the lemmas a positive control still needs); only the executable
# fold-loop + comparison is replaced by the direct grounded predicate call.
_ECHO_MASKED = """    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())
    Assert(upseq(PSeq(110, 111)) == kw_NO())
    return is_masked_field(ToSeq(field))
"""

# command_line: branch-reorder positive control on BOTH fold loops (the long-s
# test moves first); keeps the two loop invariants and the full witness-lemma
# block.
_OLD_F0 = ("        if 97 <= c and c <= 122:\n            f0 = [c - 32] + f0\n"
           "        elif c == 383:\n            f0 = [83] + f0\n"
           "        else:\n            f0 = [c] + f0\n")
_NEW_F0 = ("        if c == 383:\n            f0 = [83] + f0\n"
           "        elif 97 <= c and c <= 122:\n            f0 = [c - 32] + f0\n"
           "        else:\n            f0 = [c] + f0\n")
_OLD_F1 = ("        if 97 <= d and d <= 122:\n            f1 = [d - 32] + f1\n"
           "        elif d == 383:\n            f1 = [83] + f1\n"
           "        else:\n            f1 = [d] + f1\n")
_NEW_F1 = ("        if d == 383:\n            f1 = [83] + f1\n"
           "        elif 97 <= d and d <= 122:\n            f1 = [d - 32] + f1\n"
           "        else:\n            f1 = [d] + f1\n")
assert _OLD_F0 in _BODY_COMMAND and _OLD_F1 in _BODY_COMMAND, \
    "drift: command fold-loop bodies not found for branch-reorder control"
_POS_COMMAND = _BODY_COMMAND.replace(_OLD_F0, _NEW_F0).replace(_OLD_F1, _NEW_F1)

# reserved_data_token: honest GROUNDED-ECHO positive control (cheapest correct).
# Keeps the gold witness-lemma asserts (no/NO unfold) so the two witness Ensures
# discharge; only the fold loop + final verdict is replaced by the predicate call.
_ECHO_RESERVED = """    Assert(up(78) == 78 and up(79) == 79 and up(110) == 78 and up(111) == 79)
    Assert(PSeq(78, 79).drop(1) == PSeq(79) and PSeq(79).drop(1) == PSeq(0).take(0))
    Assert(PSeq(110, 111).drop(1) == PSeq(111) and PSeq(111).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(79)) == PSeq(79) and upseq(PSeq(111)) == PSeq(79))
    Assert(upseq(PSeq(78, 79)) == kw_NO())
    Assert(upseq(PSeq(110, 111)) == kw_NO())
    return is_reserved_data_token(ToSeq(field))
"""

# command_line: honest GROUNDED-ECHO positive control (cheapest correct). Keeps
# the gold witness-lemma asserts (read/serr + READ/SERR unfold) so the two witness
# Ensures discharge; only the fold loops + final verdict become the predicate call.
_ECHO_COMMAND = """    Assert(up(114) == 82 and up(101) == 69 and up(97) == 65 and up(100) == 68)
    Assert(up(115) == 83 and up(82) == 82 and up(69) == 69 and up(65) == 65)
    Assert(up(68) == 68 and up(83) == 83)
    Assert(PSeq(114, 101, 97, 100).drop(1) == PSeq(101, 97, 100))
    Assert(PSeq(101, 97, 100).drop(1) == PSeq(97, 100))
    Assert(PSeq(97, 100).drop(1) == PSeq(100))
    Assert(PSeq(100).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(0).take(0)) == PSeq(0).take(0))
    Assert(upseq(PSeq(100)) == PSeq(68))
    Assert(upseq(PSeq(97, 100)) == PSeq(65, 68))
    Assert(upseq(PSeq(101, 97, 100)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(114, 101, 97, 100)) == kw_READ())
    Assert(PSeq(115, 101, 114, 114).drop(1) == PSeq(101, 114, 114))
    Assert(PSeq(101, 114, 114).drop(1) == PSeq(114, 114))
    Assert(PSeq(114, 114).drop(1) == PSeq(114))
    Assert(PSeq(114).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(114)) == PSeq(82))
    Assert(upseq(PSeq(114, 114)) == PSeq(82, 82))
    Assert(upseq(PSeq(101, 114, 114)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(115, 101, 114, 114)) == kw_SERR())
    Assert(PSeq(82, 69, 65, 68).drop(1) == PSeq(69, 65, 68))
    Assert(PSeq(69, 65, 68).drop(1) == PSeq(65, 68))
    Assert(PSeq(65, 68).drop(1) == PSeq(68))
    Assert(PSeq(68).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(68)) == PSeq(68))
    Assert(upseq(PSeq(65, 68)) == PSeq(65, 68))
    Assert(upseq(PSeq(69, 65, 68)) == PSeq(69, 65, 68))
    Assert(upseq(PSeq(82, 69, 65, 68)) == kw_READ())
    Assert(PSeq(83, 69, 82, 82).drop(1) == PSeq(69, 82, 82))
    Assert(PSeq(69, 82, 82).drop(1) == PSeq(82, 82))
    Assert(PSeq(82, 82).drop(1) == PSeq(82) and PSeq(82).drop(1) == PSeq(0).take(0))
    Assert(upseq(PSeq(82)) == PSeq(82))
    Assert(upseq(PSeq(82, 82)) == PSeq(82, 82))
    Assert(upseq(PSeq(69, 82, 82)) == PSeq(69, 82, 82))
    Assert(upseq(PSeq(83, 69, 82, 82)) == kw_SERR())
    return is_command_tokens(ToSeq(tok0), ToSeq(tok1), ncols)
"""


# =============================================================================
# FRAME-MUTATION (uniqueness / permission) — MANDATORY: read-only inputs.
# A rival that WRITES the Acc(...,1/2) input must be REJECTED for insufficient
# permission. We keep the gold verdict body verbatim and ONLY prepend a write to
# the read-only input, so the rejection is attributable to the write alone.
# =============================================================================

# masked_field: write field[0] before the gold work. field is Acc(list_pred,1/2)
# (read-only) -> assigning field[0] needs full permission -> insufficient perm.
_FRAME_MASKED = """    if len(field) > 0:
        field[0] = 78  # WRITE to read-only Acc(list_pred(field),1/2) input
""" + _BODY_MASKED

# command_line: write tok0[0] before the gold work. tok0 is Acc(...,1/2).
_FRAME_COMMAND = """    if len(tok0) > 0:
        tok0[0] = 82  # WRITE to read-only Acc(list_pred(tok0),1/2) input
""" + _BODY_COMMAND

# reserved_data_token: write field[0] before the gold work.
_FRAME_RESERVED = """    if len(field) > 0:
        field[0] = 78  # WRITE to read-only Acc(list_pred(field),1/2) input
""" + _BODY_RESERVED


# =============================================================================
# PARTIAL-DOMAIN (uniqueness) — rivals correct on the witness sub-domain but
# wrong on a case/sign variant the F2P depends on. Each must be REJECTED by the
# `Result() == is_X(...)` postcondition. These reproduce the three prepatch
# behaviours (case-sensitive raw comparison), so a faithful real patch built
# this way would CRASH the F2P (refinement below).
# =============================================================================

# masked_field, case-SENSITIVE raw comparison (prepatch behaviour, hunk 2 reverted):
# masks only the exact upper-case "NO" (PSeq(78,79)), not "no"/"No"/"nO".
# Correct on the "NO" witness but WRONG on the "no" witness -> rejects.
_PARTIAL_MASKED = """    return ToSeq(field) == PSeq(78, 79)
"""

# masked_field, near-miss: masks NO and no (both witnesses) but NOT No/nO. Passes
# both Ensures witnesses yet still violates Result()==is_masked_field on "No".
_PARTIAL_MASKED_2 = """    return ToSeq(field) == PSeq(78, 79) or ToSeq(field) == PSeq(110, 111)
"""

# command_line, case-SENSITIVE raw comparison (prepatch_2 behaviour, hunk 1
# reverted): recognise only the all-upper-case "READ" + "SERR"/"TERR". Correct on
# the upper-case witness but WRONG on the lower-case "read serr" witness.
_PARTIAL_COMMAND = """    return ((ToSeq(tok0) == kw_READ())
            and (ToSeq(tok1) == kw_SERR() or ToSeq(tok1) == kw_TERR())
            and ncols >= 1)
"""

# reserved_data_token, case-SENSITIVE exact-spelling comparison (prepatch_3
# behaviour, hunk 1 reverted on data/new): recognise NO upper-case and nan
# lower-case-only (optionally signed). Correct on the "NO" witness but WRONG on
# the lower-case "no" witness -> rejects.
_PARTIAL_RESERVED = """    no_upper = PSeq(78, 79)
    nan_lower = PSeq(110, 97, 110)
    nan_plus = PSeq(43, 110, 97, 110)
    nan_minus = PSeq(45, 110, 97, 110)
    return (ToSeq(field) == no_upper
            or ToSeq(field) == nan_lower
            or ToSeq(field) == nan_plus
            or ToSeq(field) == nan_minus)
"""

# reserved_data_token, subtle: drop the SIGNED-NAN alternative (recognise NO/NAN
# case-insensitively but reject "+nan"/"-nan"). Passes both witnesses (no/NO) yet
# violates Result()==is_reserved_data_token on "+nan" -> rejects. A faithful patch
# built this way classifies a signed-NAN data field as unrecognised => ValueError.
_PARTIAL_RESERVED_2 = """    is_no = is_masked_field(ToSeq(field))
    is_nan = upseq(ToSeq(field)) == kw_NAN()
    return is_no or is_nan
"""


SPEC_TESTS = [
    # ---- POSITIVE CONTROLS (soundness) -----------------------------------
    {
        "id": "pos-masked-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_body(_BODY_MASKED, _POS_MASKED),
        "rationale": "structurally-different correct masked_field (if/else reordered, "
                     "same backward front-recursive fold + all gold witness lemmas "
                     "kept). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-command-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_body(_BODY_COMMAND, _POS_COMMAND),
        "rationale": "structurally-different correct command_line (both fold loops' "
                     "if/else reordered; loop invariants + witness lemmas kept). Must "
                     "verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-masked-grounded-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_body(_BODY_MASKED, _ECHO_MASKED),
        "rationale": "the postcondition oracle is_masked_field is fully GROUNDED in "
                     "the arg, so `return is_masked_field(ToSeq(field))` is the cheapest "
                     "CORRECT impl and must verify. Demonstrates there is no WRONG echo "
                     "(no ungrounded answer-key to exploit).",
    },
    {
        "id": "pos-reserved-grounded-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_body(_BODY_RESERVED, _ECHO_RESERVED),
        "rationale": "grounded-echo of is_reserved_data_token is the cheapest correct "
                     "impl; must verify (no ungrounded oracle to exploit).",
    },
    {
        "id": "pos-command-grounded-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_body(_BODY_COMMAND, _ECHO_COMMAND),
        "rationale": "grounded-echo of is_command_tokens is the cheapest correct impl; "
                     "must verify (no ungrounded oracle to exploit).",
    },
    # ---- ADMISSIBILITY ---------------------------------------------------
    {
        "id": "admiss-reserved-gold",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # gold impl verbatim
        "rationale": "the frozen gold model.py verifies, so the preconditions "
                     "(Acc(list_pred,1/2) read-only; ncols>=0) admit the normal "
                     "F2P-shaped inputs (a length-2 'no'/'NO' field; a 'read serr 1' "
                     "command). Else PRECOND-TOO-STRONG.",
    },
    # ---- FRAME-MUTATION (MANDATORY: read-only inputs) --------------------
    {
        "id": "frame-mutation-masked",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_MASKED, _FRAME_MASKED),
        "refinement": "writing field[0] then running the gold verdict is NOT a faithful "
                      "patch of qdp.py:309 (the real code never mutates the split field "
                      "`v`); a real patch that overwrote the field would corrupt the "
                      "round-tripped table and FAIL test_roundtrip[True]. The only reason "
                      "to write here is to vacuously satisfy a postcondition, which the "
                      "spec must forbid.",
        "rationale": "field is Acc(list_pred(field),1/2) (read-only). Assigning field[0] "
                      "needs full permission -> Nagini rejects for INSUFFICIENT PERMISSION "
                      "(the permission system), not the value postcondition. If it "
                      "verified, the read-only frame condition would be vacuous.",
    },
    {
        "id": "frame-mutation-command",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_COMMAND, _FRAME_COMMAND),
        "refinement": "writing tok0[0] is not a faithful patch of _line_type (which "
                      "matches a read-only line via regex and never mutates its words); a "
                      "real patch mutating the parsed words would corrupt classification "
                      "of subsequent lines and FAIL the F2P. The write only serves to "
                      "vacuously satisfy the postcondition.",
        "rationale": "tok0 is Acc(list_pred(tok0),1/2) (read-only). Assigning tok0[0] "
                      "needs full permission -> rejected for INSUFFICIENT PERMISSION.",
    },
    {
        "id": "frame-mutation-reserved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_RESERVED, _FRAME_RESERVED),
        "refinement": "writing field[0] is not a faithful patch of the data/new branch "
                      "token recognition (the real regex reads the field, never rewrites "
                      "it); a real mutation would corrupt the data row and FAIL the F2P. "
                      "The write only serves to vacuously satisfy the postcondition.",
        "rationale": "field is Acc(list_pred(field),1/2) (read-only). Assigning field[0] "
                      "needs full permission -> rejected for INSUFFICIENT PERMISSION.",
    },
    # ---- PARTIAL-DOMAIN --------------------------------------------------
    {
        "id": "partial-masked-uppercase-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_MASKED, _PARTIAL_MASKED),
        "refinement": "this is exactly the PRE-patch case-sensitive `v == \"NO\"` test "
                      "(prepatch hunk 2). A faithful patch keeping it does NOT mask the "
                      "lower-case `no` fields in the lower-cased F2P data row, so "
                      "test_roundtrip[True] reads them as numbers / errors and FAILS "
                      "(does not resolve).",
        "rationale": "violates Ensures(Result()==is_masked_field(ToSeq(field))) and the "
                      "witness Ensures(ToSeq(field)==PSeq(110,111) -> Result()) on the "
                      "lower-case `no` input. Rejection from the postcondition equality.",
    },
    {
        "id": "partial-masked-no-and-NO-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_MASKED, _PARTIAL_MASKED_2),
        "refinement": "masks only the two literal spellings `NO` and `no` (the exact "
                      "witnesses) but not `No`/`nO`. A faithful patch built this way "
                      "(special-casing two spellings instead of a real case fold) would "
                      "mis-handle mixed-case `No` fields a QDP file may contain, diverging "
                      "from the gold v.upper()=='NO'. It passes BOTH witness Ensures yet "
                      "still violates the general Result()==is_masked_field clause.",
        "rationale": "the two witness Ensures are satisfied, so rejection comes from the "
                      "LOAD-BEARING general clause Result()==is_masked_field(ToSeq(field)) "
                      "on a mixed-case input (e.g. `No`=PSeq(78,111)). Confirms the spec "
                      "is not merely the witnesses.",
    },
    {
        "id": "partial-command-uppercase-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_COMMAND, _PARTIAL_COMMAND),
        "refinement": "this is the PRE-patch case-sensitive command match (prepatch_2, "
                      "hunk 1 reverted). A faithful patch keeping it raises ValueError on "
                      "the lower-case `read serr 1 2` line of the lower-cased F2P file, so "
                      "test_roundtrip[True] FAILS at line classification (does not resolve).",
        "rationale": "violates Ensures(Result()==is_command_tokens(...)) and the witness "
                      "Ensures(ToSeq(tok0)==`read` and ToSeq(tok1)==`serr` and ncols>=1 -> "
                      "Result()) on lower-case input. Rejection from the postcondition.",
    },
    {
        "id": "partial-reserved-exact-spelling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_RESERVED, _PARTIAL_RESERVED),
        "refinement": "this is the PRE-patch exact-source-spelling recognition (prepatch_3, "
                      "hunk 1 reverted on data/new). A faithful patch keeping it does NOT "
                      "recognise the lower-case `no` data field, so the whole data row in "
                      "the lower-cased F2P file is classified None -> ValueError at "
                      "line-classification, BEFORE the masking loop. test_roundtrip[True] "
                      "FAILS (this is the G-EQ adversarial counterexample).",
        "rationale": "violates Ensures(Result()==is_reserved_data_token(ToSeq(field))) and "
                      "the witness Ensures(ToSeq(field)==PSeq(110,111) -> Result()) on the "
                      "lower-case `no` input. Rejection from the postcondition equality.",
    },
    {
        "id": "partial-reserved-drop-signed-nan",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_body(_BODY_RESERVED, _PARTIAL_RESERVED_2),
        "refinement": "recognises NO/NAN case-insensitively but DROPS the signed-NAN "
                      "alternative (`+nan`/`-nan`). A faithful patch built this way leaves "
                      "the data-grammar's `[-+]?nan` alternative incomplete, so a signed-NAN "
                      "data field is classified None -> ValueError on any QDP file using it "
                      "(the gold regex `(NO|[-+]?nan)` accepts it). It passes BOTH witness "
                      "Ensures (no/NO) yet still violates the general clause.",
        "rationale": "the two witness Ensures hold, so rejection comes from the general "
                      "Result()==is_reserved_data_token(ToSeq(field)) clause on a signed-NAN "
                      "input (e.g. `+nan`=PSeq(43,110,97,110)). Confirms the signed-NAN sub-"
                      "domain is genuinely pinned, not just the witnesses.",
    },
]


# =============================================================================
# AXIOM_TESTS — the bundle has NO consumed @ContractOnly axioms (meta.axioms == []
# and the model.py axioms region is empty). The changed operation is the ASCII
# case fold, modelled DEEPLY (up/upseq) and validated against the real callee
# (str.upper / the patched _line_type) by axiom_check.py / G-AX. Those deep models
# (A-references) are already exercised by the heavy G-AX check; there is nothing to
# re-probe in the axiom lane here. (Per PLAN §2.4 / §3, the axiom lane is for
# @ContractOnly axioms / A-reference deep models; this instance's A-references are
# verdict-level decision-equivalence checks already owned by G-AX, not consumed
# obligations the spec lane can falsify.)
# =============================================================================
AXIOM_TESTS = []
