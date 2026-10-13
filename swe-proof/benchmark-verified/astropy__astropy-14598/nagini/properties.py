"""properties.py — PBT manifest for astropy__astropy-14598. NOT a Nagini module;
a record of adversarial cases. The runner (swebench_nagini.pbt) executes each and
stamps RESULT. Spec cases are full model.py variants (same frozen spec, swapped
impl) checked by Nagini verify + markers.same_spec; axiom cases are real-callee
probes in Docker.

Defended surface (read from model.py + refinement.md + gold patch):

  Two contracted functions, both over List[int] code points, BOTH with read-only
  half-permission inputs:

  * recover_payload(segment)  — Acc(segment, 1/2) read-only; Requires no '/'(47)
    in segment.  Load-bearing post: ToSeq(Result()) == ToSeq(segment)  (FULL
    payload recovery — the regex `$`-anchor fix, gold hunk 1).  GROUNDED: the
    output is pinned to the input itself, no opaque oracle.

  * unescape_value(captured, witness) — Acc(captured,1/2) AND Acc(witness,1/2),
    both read-only.  Load-bearing posts:
      (B1) ToSeq(Result()) == unescape_quotes(ToSeq(captured))  — exactly ONE
           `''`->`'` collapse (the removed `.replace("''","'")`, gold hunk 2);
      (B2) Implies(captured == escape_quotes(witness), Result == witness) — the
           round-trip witness clause (the FAIL_TO_PASS identity), discharged via
           rt_lemma.  GROUNDED in `captured` (a @Pure fold of the actual arg,
           fully unfolded), so there is no wrong oracle to echo.

The F2P test (test_long_string_value_with_quotes) asserts fromstring(str(card))
round-trips a value ending in / containing `''` with and without trailing text
and an interior space — exactly what hunk 1 (full capture) + hunk 2 (single
un-escape) restore.  Each reject rival carries the refinement argument that its
faithful real patch would NOT resolve that F2P.

NO @ContractOnly axioms (axioms region empty); the three deep models
(escape_quotes / unescape_quotes / full recover_payload) are A-references checked
by axiom_check.py (G-AX), not consumed axioms.  Per PBT_PLAN §2.4 the axiom lane
covers only consumed/@ContractOnly axioms, so AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14598"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused; pure-int spec)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors: every edit below lives strictly INSIDE an # impl-start / # impl-end
# region (or its nested # invariants), so markers.same_spec is preserved (the
# spec view elides impl).  The two impl bodies are byte-identical to model.py.
# ---------------------------------------------------------------------------

# --- recover_payload impl body (forward full copy) ---
_RP_IMPL = """    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result"""

# --- unescape_value impl body (single un-escape pass) ---
_UV_IMPL = """    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
    rt_lemma(ToSeq(witness))
    return result"""

# sanity: the anchors are present + unique in the frozen model
assert _BASE.count(_RP_IMPL) == 1, "recover_payload impl anchor drift"
assert _BASE.count(_UV_IMPL) == 1, "unescape_value impl anchor drift"


# ===========================================================================
# POSITIVE CONTROL 1 (soundness) — recover_payload, structurally different but
# correct.  Reorder/local-reshape only: capture segment[j] into a typed local
# `c` and append [c] instead of [segment[j]], and split the framing Assert into
# the equivalent take-step using `c`.  KEEPS the gold take-invariant + the final
# take(n)==full Assert (PBT §5a-2: don't drop framing).  Still forward-append
# against the take()-based invariant (NOT a front-recursive fold), so no
# auto-undischargeable lemma (PBT §5a-3).  MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_RP = _swap(_BASE, _RP_IMPL, """    result = []  # type: List[int]
    n = len(segment)
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        c = segment[j]
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(c))
        result = result + [c]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result""")


# ===========================================================================
# POSITIVE CONTROL 2 (soundness) — unescape_value, structurally different but
# correct.  Reshape the else-branch: bind c via an extra local and negate the
# pair test into an explicit `not (...)` guard reorder; keep BOTH gold branches'
# framing Asserts and rt_lemma exactly (PBT §5a-2).  Forward against the
# front-recursive unescape_quotes invariant is the GOLD shape, so the proof
# stays valid (we do NOT flip loop direction — PBT §5a-3).  MUST verify.
# ===========================================================================
_POS_UV = _swap(_BASE, _UV_IMPL, """    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        is_pair = j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39
        if not is_pair:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
        else:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
    rt_lemma(ToSeq(witness))
    return result""")


# ===========================================================================
# ADMISSIBILITY — a self-call caller proving the Requires admits an F2P-shaped
# input.  We add the caller INSIDE recover_payload's impl (so same_spec holds):
# before doing the real work, construct an F2P-shaped segment (the escaped form
# of "xxx''xxx" carried by a continuation segment — code points, no '/'(47)),
# Assert the no-'/' precondition holds for it, and call recover_payload on it.
# If the Requires cannot be established for this legitimate input the call site
# fails => PRECOND-TOO-STRONG.  Then run the unchanged real body.  MUST verify.
# ===========================================================================
_ADM = _swap(_BASE, _RP_IMPL, """    # admissibility self-call: an F2P-shaped escaped continuation payload,
    # "xxx''xxx" -> code points (x=120, '=39), contains no '/' (47).
    probe = [120, 120, 120, 39, 39, 120, 120, 120]  # type: List[int]
    Assert(Forall(int, lambda k:
        (Implies(0 <= k and k < len(probe), probe[k] != 47))))
    if len(probe) < len(segment):   # keeps the callee's obligation level below ours
        _echoed = recover_payload(probe)
        Assert(ToSeq(_echoed) == ToSeq(probe))
    # ... then the unchanged real body on the actual argument ...
    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result""")


# ===========================================================================
# FRAME-MUTATION 1 (uniqueness, MANDATORY) — recover_payload WRITES to the
# read-only Acc(segment,1/2) input.  The cheapest way to "satisfy"
# ToSeq(Result())==ToSeq(segment) AND re-Ensure Acc(segment,1/2) is to copy
# segment then return it; instead this rival mutates segment in place
# (segment[0] = segment[0]) and returns it.  With only 1/2 permission to
# segment a write is ILLEGAL => must be REJECTED for insufficient permission.
# refinement: a real patch that wrote back into the parsed source segment would
# corrupt the shared card-image buffer (the segment is a slice of the card
# string the caller still reads); it would not be the gold one-line regex/replace
# fix and would not resolve test_long_string_value_with_quotes.
# rationale: rejection comes from the permission system (Acc(segment,1/2) cannot
# be written), NOT from the value postcondition.
# ===========================================================================
_FRAME_RP = _swap(_BASE, _RP_IMPL, """    n = len(segment)
    if n > 0:
        segment[0] = segment[0]   # ILLEGAL write to a 1/2-permission input
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result""")


# ===========================================================================
# FRAME-MUTATION 2 (uniqueness, MANDATORY) — unescape_value WRITES to the
# read-only Acc(witness,1/2) ghost original.  The round-trip clause B2 says
# `captured == escape_quotes(witness) ==> Result == witness`; a rival that
# OVERWRITES witness to make the antecedent / consequent trivially align is a
# vacuous satisfaction.  With only 1/2 permission to witness the write is
# ILLEGAL => REJECTED for insufficient permission.
# refinement: witness models the original value the caller still holds and
# compares against (card1.value == card2.value in the F2P); a real patch that
# mutated the user's original value object is nonsensical and not the gold
# one-line fix — it would not resolve the F2P.
# rationale: rejection comes from the permission system on witness, not from
# either value postcondition.
# ===========================================================================
_FRAME_UV = _swap(_BASE, _UV_IMPL, """    if len(witness) > 0:
        witness[0] = witness[0]   # ILLEGAL write to a 1/2-permission input
    result = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            result = result + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            result = result + [c]
            j = j + 1
    rt_lemma(ToSeq(witness))
    return result""")


# ===========================================================================
# PARTIAL-DOMAIN 1 (uniqueness) — recover_payload that recovers all but the
# LAST code point (loop `j < n - 1`).  Correct on the empty segment and agrees
# with the full recovery on the prefix, but drops the final char — exactly the
# truncation class the regex `$`-fix removes.  Diverges precisely on the F2P
# input "x"*100 + "''": the final escaped quote would be lost.  expect reject.
# refinement: its faithful real patch is the UNFIXED (or partially-fixed) regex
# that still truncates the tail; the issue report shows that drops the trailing
# `'`, so card1.value != card2.value and the F2P FAILS.
# rationale: rejection comes from Ensures ToSeq(Result())==ToSeq(segment) (the
# loop cannot re-establish take(n)==full when it stops at n-1).
# ===========================================================================
_PARTIAL_RP = _swap(_BASE, _RP_IMPL, """    result = []  # type: List[int]
    j = 0
    n = len(segment)
    while j < n - 1:           # PARTIAL: drops the last code point
        # invariants-start
        Invariant(Acc(list_pred(segment), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(segment))
        Invariant(ToSeq(result) == ToSeq(segment).take(j))
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(segment).take(j + 1) == ToSeq(segment).take(j) + PSeq(segment[j]))
        result = result + [segment[j]]
        j = j + 1
    Assert(ToSeq(segment).take(n) == ToSeq(segment))
    return result""")


# ===========================================================================
# PARTIAL-DOMAIN 2 (uniqueness) — unescape_value that un-escapes TWICE (the
# pre-patch double-collapse, model_prepatch.py's bug, recast minimally).  This
# rival is correct on every captured payload WITHOUT a surviving `''` pair after
# the first pass, but on a genuine embedded quote pair `''''` -> first pass ->
# `''` -> second pass -> `'`, wrongly collapsing it.  It diverges exactly on the
# F2P value ending/containing `''`.  expect reject.
# refinement: the faithful real patch is to KEEP `value.rstrip().replace("''","'")`
# in _split AND the _parse_value re.sub — the double un-escape the issue reports
# (the `''`->`'` bug).  It does NOT resolve test_long_string_value_with_quotes.
# rationale: rejection comes from Ensures ToSeq(Result())==unescape_quotes(...)
# (one collapse) — a second pass breaks it whenever a pair survives.
# ===========================================================================
_PARTIAL_UV = _swap(_BASE, _UV_IMPL, """    # first un-escape pass
    interm = []  # type: List[int]
    j = 0
    n = len(captured)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(captured), 1 / 2))
        Invariant(Acc(list_pred(interm)))
        Invariant(0 <= j and j <= n and n == len(captured))
        Invariant(ToSeq(interm) + unescape_quotes(ToSeq(captured).drop(j))
                  == unescape_quotes(ToSeq(captured)))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        if j + 2 <= n and captured[j] == 39 and captured[j + 1] == 39:
            Assert(ToSeq(captured).drop(j)[0] == 39)
            Assert(ToSeq(captured).drop(j)[1] == 39)
            Assert(len(ToSeq(captured).drop(j)) >= 2)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(39) + unescape_quotes(ToSeq(captured).drop(j).drop(2)))
            Assert(ToSeq(captured).drop(j).drop(2) == ToSeq(captured).drop(j + 2))
            interm = interm + [39]
            j = j + 2
        else:
            c = captured[j]
            Assert(ToSeq(captured).drop(j)[0] == c)
            Assert(unescape_quotes(ToSeq(captured).drop(j))
                   == PSeq(c) + unescape_quotes(ToSeq(captured).drop(j).drop(1)))
            Assert(ToSeq(captured).drop(j).drop(1) == ToSeq(captured).drop(j + 1))
            interm = interm + [c]
            j = j + 1
    # second (wrongful) un-escape pass on the intermediate result
    result = []  # type: List[int]
    k = 0
    mlen = len(interm)
    while k < mlen:
        # invariants-start
        Invariant(Acc(list_pred(interm)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= mlen and mlen == len(interm))
        Invariant(ToSeq(result) + unescape_quotes(ToSeq(interm).drop(k))
                  == unescape_quotes(ToSeq(interm)))
        Invariant(MustTerminate(mlen - k + 1))
        # invariants-end
        if k + 2 <= mlen and interm[k] == 39 and interm[k + 1] == 39:
            Assert(ToSeq(interm).drop(k)[0] == 39)
            Assert(ToSeq(interm).drop(k)[1] == 39)
            Assert(len(ToSeq(interm).drop(k)) >= 2)
            Assert(unescape_quotes(ToSeq(interm).drop(k))
                   == PSeq(39) + unescape_quotes(ToSeq(interm).drop(k).drop(2)))
            Assert(ToSeq(interm).drop(k).drop(2) == ToSeq(interm).drop(k + 2))
            result = result + [39]
            k = k + 2
        else:
            c2 = interm[k]
            Assert(ToSeq(interm).drop(k)[0] == c2)
            Assert(unescape_quotes(ToSeq(interm).drop(k))
                   == PSeq(c2) + unescape_quotes(ToSeq(interm).drop(k).drop(1)))
            Assert(ToSeq(interm).drop(k).drop(1) == ToSeq(interm).drop(k + 1))
            result = result + [c2]
            k = k + 1
    rt_lemma(ToSeq(witness))
    return result""")


# ===========================================================================
# SUPPORTING near-miss (uniqueness) — recover_payload that returns the EMPTY
# list.  Cheapest impl ignoring the input; trivially wrong (Result != segment
# for any non-empty segment).  Carries a real refinement and exercises the
# load-bearing full-recovery clause.  expect reject.
# refinement: returning the empty payload is not any faithful patch of the
# regex capture; every non-trivial F2P value would be lost -> F2P FAILS.
# rationale: Ensures ToSeq(Result())==ToSeq(segment) forces a non-empty result
# for a non-empty segment.
# ===========================================================================
_EMPTY_RP = _swap(_BASE, _RP_IMPL, """    empty = []  # type: List[int]
    return empty""")


SPEC_TESTS = [
    {"id": "pos-recover-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RP,
     "rationale": "structurally-different but correct full-copy (local var + "
                  "split take-step Assert, gold take-invariant kept). A faithful "
                  "correct impl MUST verify, else SPEC-TOO-STRONG."},

    {"id": "pos-unescape-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_UV,
     "rationale": "structurally-different but correct single un-escape "
                  "(branch-reorder via `not is_pair`, both branches' framing "
                  "Asserts + rt_lemma kept). MUST verify, else SPEC-TOO-STRONG."},

    {"id": "admiss-recover-fshape", "kind": "admissibility", "expect": "verify",
     "module": _ADM,
     "rationale": "a self-call on an F2P-shaped escaped payload (no '/') proves "
                  "the no-47 Requires admits a legitimate input; if it cannot be "
                  "established the call fails => PRECOND-TOO-STRONG."},

    {"id": "frame-mutate-segment", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_RP,
     "refinement": "writing back into the parsed source segment (a slice of the "
                   "card-image buffer the caller still reads) is not the gold "
                   "one-line regex/replace fix and would corrupt shared state; it "
                   "does not resolve test_long_string_value_with_quotes.",
     "rationale": "rejection from the PERMISSION system: Acc(segment,1/2) cannot "
                  "be written. If it VERIFIED the spec would let an impl mutate a "
                  "read-only input — the #1 weakness class."},

    {"id": "frame-mutate-witness", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_UV,
     "refinement": "witness is the original value the caller still holds and "
                   "compares (card1.value == card2.value); a patch that mutated "
                   "the user's original value object is nonsensical, not the gold "
                   "fix, and would not resolve the F2P.",
     "rationale": "rejection from the PERMISSION system on Acc(witness,1/2); the "
                  "round-trip clause must not be satisfiable by overwriting the "
                  "read-only ghost original."},

    {"id": "partial-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _PARTIAL_RP,
     "refinement": "the faithful real patch is the unfixed/partial regex that "
                   "still truncates the tail; the issue shows that drops the "
                   "trailing quote so card1.value != card2.value — F2P FAILS.",
     "rationale": "rejection from Ensures ToSeq(Result())==ToSeq(segment): a loop "
                  "stopping at n-1 cannot re-establish take(n)==full."},

    {"id": "partial-double-unescape", "kind": "uniqueness", "expect": "reject",
     "module": _PARTIAL_UV,
     "refinement": "the faithful real patch keeps BOTH `.replace(\"''\",\"'\")` "
                   "in _split and the _parse_value re.sub — the double un-escape "
                   "the bug report describes; a surviving `''` is wrongly "
                   "collapsed, so the F2P (value ending in `''`) FAILS.",
     "rationale": "rejection from Ensures ToSeq(Result())==unescape_quotes("
                  "ToSeq(captured)) (exactly one collapse); a second pass breaks "
                  "it whenever a quote pair survives the first."},

    {"id": "empty-recover", "kind": "uniqueness", "expect": "reject",
     "module": _EMPTY_RP,
     "refinement": "returning the empty payload is no faithful patch of the regex "
                   "capture; every non-trivial F2P value is lost — F2P FAILS. "
                   "(supporting near-miss; still carries a real refinement.)",
     "rationale": "rejection from Ensures ToSeq(Result())==ToSeq(segment), which "
                  "forces a non-empty result for a non-empty segment."},
]

# No @ContractOnly / consumed axioms (axioms region empty). The three deep models
# (escape_quotes / unescape_quotes / full recover_payload) are A-references whose
# soundness vs. the real card.py regex/re.sub/str.replace is checked by
# axiom_check.py (G-AX), not by a consumed-axiom obligation, so the axiom lane is
# vacuous here.
AXIOM_TESTS = []  # type: list
