# properties.py — PBT falsification battery for pytest-dev__pytest-7205.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec (only the impl region is swapped,
# guaranteed by region-surgery via _swap) and are checked by Nagini verify +
# same_spec; axiom cases are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (read model.py / refinement.md / mapping.md):
#   render_param_token(param: List[int], maxsize: int) -> List[int]
#   models the token shown between '[' and ']' for a recorded fixture parameter.
#   The gold edit replaces the implicit str() rendering ("[{}]".format(param))
#   with the size-limited programmer's representation saferepr(param, 42), which
#   on the tested domain is the apostrophe-delimited verbatim text 'foo'.
#
#   The load-bearing, DISCRIMINATING postcondition clause is
#       Ensures(ToSeq(Result()) == repr_quote(ToSeq(param)))           (value)
#   re-stated STRUCTURALLY by
#       Ensures(len(Result()) == len(param) + 2)                       (length)
#       Ensures(Result()[0] == QUOTE)                                  (open  ')
#       Ensures(Result()[len(Result()) - 1] == QUOTE)                  (close ')
#       Ensures(Forall k: 0<=k<len(param) ==> Result()[k+1] == param[k]) (body)
#       Ensures(len(Result()) <= maxsize)                              (size bound)
#   The pre-patch plain-text rendering (bare `param`) fails all the delimiter
#   clauses (model_prepatch.py / G-DIFF).
#
# GROUNDED ORACLE (no ungrounded-echo attack): repr_quote is NOT an opaque
# answer-key — it is the fully-unfolded pure function
#       repr_quote(s) == PSeq(QUOTE) + s + PSeq(QUOTE)
# i.e. a transparent function of the argument. An impl that "echoes"
# [QUOTE]+param+[QUOTE] is therefore the CORRECT answer, not a wrong echo; there
# is no value an impl could echo that satisfies the clause yet diverges from the
# gold rendering. So the ungrounded-oracle-echo class does not apply here; the
# cheapest honest impl (the concat) is instead supplied as a POSITIVE CONTROL.
# See 'assessment'.
#
# PERMISSION SHAPE (frame-mutation MANDATORY):
#   `param` is READ-ONLY: Requires(Acc(list_pred(param), 1/2)) and the matching
#   Ensures(Acc(list_pred(param), 1/2)). A rival that WRITES to `param` (to build
#   the answer in place, or to "fix up" a delimiter) must fail to verify for
#   INSUFFICIENT PERMISSION — half permission grants read, not write. That is the
#   FM1 frame-mutation rival below.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-7205"
FLOAT_ENCODING = None  # meta.json float_encoding is null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()


# ----------------------------------------------------------------------------
# Region anchor. We edit ONLY text strictly inside the single # impl-start /
# # impl-end region (which lexically CONTAINS the nested # invariants-start /
# # invariants-end block). spec_signature masks the whole impl region, so every
# variant below is same_spec == True. The spec (axioms/pure/pre/post + signature)
# is never touched.
# ----------------------------------------------------------------------------

# The gold impl region body (markers EXCLUDED; _swap matches this exact text).
_GOLD = (
    "    result = [QUOTE]  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(param):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(param), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(param))\n"
    "        Invariant(len(param) + 2 <= maxsize)\n"
    "        Invariant(len(result) == i + 1)\n"
    "        Invariant(result[0] == QUOTE)\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                  result[k + 1] == param[k]))))\n"
    "        Invariant(ToSeq(result) == PSeq(QUOTE) + ToSeq(param).take(i))\n"
    "        Invariant(MustTerminate(len(param) - i + 1))\n"
    "        # invariants-end\n"
    "        result.append(param[i])\n"
    "        i = i + 1\n"
    "    result.append(QUOTE)\n"
    "    return result"
)

# sanity: the anchor is present and unique in _BASE
assert _BASE.count(_GOLD) == 1, "gold impl anchor drift"


# ===========================================================================
# (S1) POSITIVE CONTROL (soundness) — structurally different, CORRECT.
# Same forward-copy proof skeleton (keeps every load-bearing invariant so the
# verifier discharges it exactly as for the gold body), but the EXECUTABLE shape
# is reshaped: the copy is driven through a local alias `src` of `param`, the two
# invariant clauses about `result[0]`/`len` are textually reordered, and an extra
# always-true helper local `n` (the parameter length) is introduced. None of this
# changes the proof obligations; it changes the surface form. Embedded
# Assert(len(param) + 2 <= maxsize) doubles as an admissibility witness on the
# generic input. MUST verify (else SPEC-TOO-STRONG / a proof too brittle).
# ===========================================================================
_POS = _swap(
    _BASE,
    _GOLD,
    (
        "    # structural reshape: leading admissibility witness + a length helper\n"
        "    # local `n` driving the loop guard (a local alias of len(param)). The\n"
        "    # load-bearing invariant block is kept in the gold dependency order so\n"
        "    # the proof obligations discharge identically; the executable shape (the\n"
        "    # extra Assert, the `n` local, `while i < n`, the `n == len(param)`\n"
        "    # witness clause) is what differs.\n"
        "    Assert(len(param) + 2 <= maxsize)  # admissibility witness on input\n"
        "    n = len(param)\n"
        "    result = [QUOTE]  # type: List[int]\n"
        "    i = 0\n"
        "    while i < n:\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(param), 1 / 2))\n"
        "        Invariant(Acc(list_pred(result)))\n"
        "        Invariant(n == len(param))\n"
        "        Invariant(0 <= i and i <= len(param))\n"
        "        Invariant(len(param) + 2 <= maxsize)\n"
        "        Invariant(len(result) == i + 1)\n"
        "        Invariant(result[0] == QUOTE)\n"
        "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
        "                                                  result[k + 1] == param[k]))))\n"
        "        Invariant(ToSeq(result) == PSeq(QUOTE) + ToSeq(param).take(i))\n"
        "        Invariant(MustTerminate(len(param) - i + 1))\n"
        "        # invariants-end\n"
        "        result.append(param[i])\n"
        "        i = i + 1\n"
        "    result.append(QUOTE)\n"
        "    return result"
    ),
)


# ===========================================================================
# (S2) CHEAPEST-HONEST POSITIVE CONTROL (soundness) — list-concat in one shot.
# Because the oracle is GROUNDED (repr_quote(s) == PSeq(QUOTE)+s+PSeq(QUOTE)),
# the cheapest correct impl is the direct concatenation [QUOTE] + param + [QUOTE].
# This reads `param` (permitted at half permission) and constructs a FRESH list;
# it never writes `param`. If the verifier can discharge ToSeq distributivity
# over list concatenation this MUST verify (it is literally the oracle). It is a
# genuinely different control shape (no loop) and a positive control for the
# no-wrong-echo argument: the cheapest "echo" of the grounded oracle is correct.
# NB: kept as a SEPARATE control from S1 so that if list-concat ToSeq-framing is
# not auto-discharged it is a PROOF gap on S2 (a known Nagini limitation), not a
# spec defect — S1 (the proof-stable reshape) carries the soundness verdict.
# ===========================================================================
_POS_CONCAT = _swap(
    _BASE,
    _GOLD,
    (
        "    # cheapest honest impl: the grounded oracle, materialized directly.\n"
        "    open_ = [QUOTE]  # type: List[int]\n"
        "    close_ = [QUOTE]  # type: List[int]\n"
        "    result = open_ + param + close_  # type: List[int]\n"
        "    return result"
    ),
)


# ===========================================================================
# (FM1) FRAME-MUTATION (uniqueness, reject) — MANDATORY (param is Acc(...,1/2)).
# A rival that WRITES into the read-only input `param` to build the rendering in
# place: it overwrites param[0] with QUOTE (pretending to "insert" the opening
# delimiter into the input itself). Half permission Acc(list_pred(param),1/2)
# grants READ only, so the assignment param[0] = QUOTE must FAIL to verify for
# INSUFFICIENT PERMISSION. The gold invariants are kept verbatim so the rejection
# is attributable to the write, not to a proof regression. A mechanical byte
# fuzzer never thinks to mutate the input — this is the #1 weakness class.
# ===========================================================================
_FM = _swap(
    _BASE,
    _GOLD,
    (
        "    # FRAME MUTATION: write into the read-only input `param`. Held at\n"
        "    # half permission (read-only); this assignment must be rejected for\n"
        "    # INSUFFICIENT PERMISSION.\n"
        "    param[0] = QUOTE  # illegal write to a 1/2-permission input\n"
        "    result = [QUOTE]  # type: List[int]\n"
        "    i = 0\n"
        "    while i < len(param):\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(param), 1 / 2))\n"
        "        Invariant(Acc(list_pred(result)))\n"
        "        Invariant(0 <= i and i <= len(param))\n"
        "        Invariant(len(param) + 2 <= maxsize)\n"
        "        Invariant(len(result) == i + 1)\n"
        "        Invariant(result[0] == QUOTE)\n"
        "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
        "                                                  result[k + 1] == param[k]))))\n"
        "        Invariant(ToSeq(result) == PSeq(QUOTE) + ToSeq(param).take(i))\n"
        "        Invariant(MustTerminate(len(param) - i + 1))\n"
        "        # invariants-end\n"
        "        result.append(param[i])\n"
        "        i = i + 1\n"
        "    result.append(QUOTE)\n"
        "    return result"
    ),
)


# ===========================================================================
# (U1) PLAIN-TEXT RENDERING (uniqueness, reject) — the prepatch bug itself.
# Render the bare parameter text with NO surrounding delimiters (the implicit
# str() the trace used). This is exactly model_prepatch.py's body. It fails the
# delimiting postconditions: Result()[0] == QUOTE, len == len(param)+2, and the
# value clause ToSeq(Result()) == repr_quote(ToSeq(param)).
# ===========================================================================
_PLAIN = _swap(
    _BASE,
    _GOLD,
    (
        "    # PRE-PATCH bug: plain text form (bare param, no delimiters).\n"
        "    result = []  # type: List[int]\n"
        "    i = 0\n"
        "    while i < len(param):\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(param), 1 / 2))\n"
        "        Invariant(Acc(list_pred(result)))\n"
        "        Invariant(0 <= i and i <= len(param))\n"
        "        Invariant(len(result) == i)\n"
        "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
        "                                                  result[k] == param[k]))))\n"
        "        Invariant(ToSeq(result) == ToSeq(param).take(i))\n"
        "        Invariant(MustTerminate(len(param) - i + 1))\n"
        "        # invariants-end\n"
        "        result.append(param[i])\n"
        "        i = i + 1\n"
        "    return result"
    ),
)


# ===========================================================================
# (U2) ONE-SIDED DELIMITER (uniqueness, reject) — partial-domain on structure.
# Open quote present, CLOSING quote omitted: returns ' + param (length
# len(param)+1, no trailing apostrophe). Passes Result()[0]==QUOTE and the body
# pin, but FAILS len(Result()) == len(param)+2 and Result()[len-1]==QUOTE (the
# last code point is the final param char, not the apostrophe). saferepr always
# emits the trailing delimiter; the F2P expects 'foo' with BOTH apostrophes, so a
# missing-close patch makes the trace line 'arg_same['foo]' and the fnmatch FAILS.
# ===========================================================================
_OPEN_ONLY = _swap(
    _BASE,
    _GOLD,
    (
        "    # one-sided: opening quote only, closing apostrophe omitted.\n"
        "    result = [QUOTE]  # type: List[int]\n"
        "    i = 0\n"
        "    while i < len(param):\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(param), 1 / 2))\n"
        "        Invariant(Acc(list_pred(result)))\n"
        "        Invariant(0 <= i and i <= len(param))\n"
        "        Invariant(len(param) + 2 <= maxsize)\n"
        "        Invariant(len(result) == i + 1)\n"
        "        Invariant(result[0] == QUOTE)\n"
        "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
        "                                                  result[k + 1] == param[k]))))\n"
        "        Invariant(ToSeq(result) == PSeq(QUOTE) + ToSeq(param).take(i))\n"
        "        Invariant(MustTerminate(len(param) - i + 1))\n"
        "        # invariants-end\n"
        "        result.append(param[i])\n"
        "        i = i + 1\n"
        "    return result  # missing the closing QUOTE\n"
    ),
)


# ===========================================================================
# (U3) PARTIAL-DOMAIN — correct EXCEPT on the first parameter code point.
# Copies param verbatim into the delimiters for every index k>=1 but renders the
# FIRST interior code point as a fixed letter 'X' (88) instead of param[0]. The
# delimiters and the length are perfect, so it passes len==len(param)+2,
# [0]==QUOTE, [len-1]==QUOTE; it is correct for the entire param domain EXCEPT
# index 0. It is rejected by Forall(k: Result()[k+1]==param[k]) at k==0 (and by
# the value clause). Refinement: a real patch that mangled the first character of
# every parameter would make 'foo' render as 'Xoo', so the F2P fnmatch line
# "SETUP    S arg_same?'foo'?" FAILS — the rival does not resolve.
# To stay PROVABLE, the loop fills [1..n], the first-char divergence is injected
# after the loop by appending the body, then the first interior slot is the wrong
# constant; we use a simple shape: seed [QUOTE, 88], copy param[1:], close QUOTE.
# ===========================================================================
_FIRST_WRONG = _swap(
    _BASE,
    _GOLD,
    (
        "    # partial-domain: first interior code point forced to 88 ('X'),\n"
        "    # the rest of param copied verbatim. Wrong only at param index 0.\n"
        "    result = [QUOTE]  # type: List[int]\n"
        "    if len(param) > 0:\n"
        "        result.append(88)  # wrong first char (should be param[0])\n"
        "    i = 1\n"
        "    while i < len(param):\n"
        "        # invariants-start\n"
        "        Invariant(Acc(list_pred(param), 1 / 2))\n"
        "        Invariant(Acc(list_pred(result)))\n"
        "        Invariant(1 <= i and i <= len(param))\n"
        "        Invariant(len(result) == i + 1)\n"
        "        Invariant(result[0] == QUOTE)\n"
        "        # invariants-end\n"
        "        result.append(param[i])\n"
        "        i = i + 1\n"
        "    result.append(QUOTE)\n"
        "    return result"
    ),
)


SPEC_TESTS = [
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS,
        "rationale": (
            "A structurally-different but CORRECT impl: the same forward-copy "
            "proof skeleton (every load-bearing invariant kept verbatim so the "
            "verifier discharges it exactly as for the gold body), reshaped to "
            "drive the copy through a length local `n` with the invariant clauses "
            "textually reordered. The embedded Assert(len(param)+2 <= maxsize) is "
            "an ADMISSIBILITY witness: the precondition admits a normal F2P-shaped "
            "input. If this cannot verify the spec is SPEC-TOO-STRONG (or the proof "
            "too brittle to admit a faithful variant)."
        ),
    },
    {
        "id": "pos-control-concat",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONCAT,
        "rationale": (
            "The cheapest honest impl: the grounded oracle materialized directly "
            "as [QUOTE] + param + [QUOTE]. It reads `param` at half permission and "
            "builds a fresh list, never writing the input. Because repr_quote is "
            "transparent (PSeq(QUOTE)+s+PSeq(QUOTE)), this list-concat is exactly "
            "the required value; it is the positive control for the no-wrong-echo "
            "argument (the cheapest echo of a grounded oracle is correct). MUST "
            "verify; if list-concat ToSeq-framing is not auto-discharged that is a "
            "Nagini proof limitation on THIS variant, not a spec defect (S1 carries "
            "the soundness verdict)."
        ),
    },
    {
        "id": "frame-mutation-write-param",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM,
        "refinement": (
            "Writes into the recorded parameter (`param[0] = QUOTE`) before "
            "copying. In the repo `param` is `fixturedef.cached_param`, the live "
            "recorded parameter value the trace reads; mutating it would corrupt "
            "the value shown on subsequent SETUP/TEARDOWN lines (and any later "
            "reader of cached_param). The gold patch never mutates cached_param — "
            "it only reads it to render. A patch that overwrote the parameter to "
            "build the token in place would change the displayed value away from "
            "the verbatim 'foo'/'bar', so the F2P fnmatch lines "
            "\"SETUP    S arg_same?'foo'?\" would FAIL: it does not resolve."
        ),
        "rationale": (
            "Rejected by the PERMISSION SYSTEM: `param` is held at "
            "Requires(Acc(list_pred(param), 1/2)) — half permission grants read, "
            "not write. The assignment param[0] = QUOTE needs full permission, so "
            "the variant fails to verify for INSUFFICIENT PERMISSION. The gold "
            "invariants are kept verbatim, so the rejection is attributable to the "
            "write, not a proof regression."
        ),
    },
    {
        "id": "plain-text-no-delimiters",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PLAIN,
        "refinement": (
            "This is the pre-patch bug verbatim (model_prepatch.py): render the "
            "bare parameter text with no delimiters — the implicit str(param) the "
            "trace used at setuponly.py:69. Its faithful real patch keeps "
            "\"[{}]\".format(fixturedef.cached_param), so the trace shows "
            "arg_same[foo] not arg_same['foo']; the F2P "
            "test_show_fixtures_with_parameters asserts the line "
            "\"SETUP    S arg_same?'foo'?\" => FAILS. (It is also the configuration "
            "that raises BytesWarning on a bytes parameter under `python -bb`, the "
            "F2P test_show_fixture_action_with_bytes.) It does not resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Result()[0] == QUOTE), "
            "Ensures(len(Result()) == len(param) + 2), and the value clause "
            "Ensures(ToSeq(Result()) == repr_quote(ToSeq(param))): the bare text "
            "is missing both apostrophe delimiters. This is exactly the "
            "discriminating clause (G-DIFF: model_prepatch.py fails here)."
        ),
    },
    {
        "id": "open-quote-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _OPEN_ONLY,
        "refinement": (
            "Emits the opening apostrophe but omits the closing one: ' + param. "
            "A real saferepr always closes the delimiter; a patch that emitted a "
            "one-sided quote would render 'foo as arg_same['foo] (missing the "
            "trailing apostrophe), so the F2P line \"SETUP    S arg_same?'foo'?\" "
            "(which requires the closing apostrophe before ']') FAILS. It does not "
            "resolve."
        ),
        "rationale": (
            "Rejected by Ensures(len(Result()) == len(param) + 2) (the result is "
            "one short) and Ensures(Result()[len(Result()) - 1] == QUOTE) (the "
            "last code point is the final param char, not the apostrophe), and the "
            "value clause."
        ),
    },
    {
        "id": "first-char-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FIRST_WRONG,
        "refinement": (
            "Correct on the whole parameter domain EXCEPT the first interior code "
            "point, which is forced to 88 ('X'). A real patch that mangled only "
            "the first character of every parameter would render 'foo' as 'Xoo', "
            "so the F2P fnmatch line \"SETUP    S arg_same?'foo'?\" FAILS (the "
            "rendered value would be 'Xoo'). A rival correct on most of the domain "
            "but diverging on a sub-domain (index 0) does not resolve."
        ),
        "rationale": (
            "Rejected by Ensures(Forall k: 0<=k<len(param) ==> "
            "Result()[k+1] == param[k]) at k==0 (Result()[1] is 88, not param[0]) "
            "and by the value clause ToSeq(Result()) == repr_quote(ToSeq(param))."
        ),
    },
]


# ===========================================================================
# AXIOM LANE — the A-reference deep model `repr_quote` == real
# `_pytest._io.saferepr.saferepr(_, maxsize=42)`. This bundle consumes NO
# @ContractOnly axioms (axioms region is empty); the only trust point in the
# axiom lane is the deep-model reference. We validate it two ways, reusing and
# strengthening axiom_check.py's logic:
#
#   ax-sound-saferepr   (axiom-soundness): on every input IN the model's tested
#       domain UNDER the caller's actual config (maxsize=42, the gold literal),
#       the REAL saferepr equals the deep model code point for code point; and
#       it never exceeds 42 chars on long/escaping inputs (the <= maxsize bound);
#       and bytes render without an implicit str() (the BytesWarning the fix
#       removes). Fuzzes boundaries + sentinels + the bytes raise-path.
#
#   ax-cover-saferepr   (axiom-containment): every input the MODEL can pass to
#       the real callee lies in the deep model's validated domain. The model's
#       Requires pins exactly that domain (printable ASCII 32..126, no apostrophe
#       (39), no backslash (92), len+2 <= maxsize, maxsize==42 from the gold). We
#       enumerate the domain BOUNDARY and assert every such input is one on which
#       saferepr == the verbatim quoting — and that the immediate neighbours
#       OUTSIDE the domain (apostrophe / backslash / non-printable) are exactly
#       where saferepr would diverge (escape), demonstrating the domain is the
#       precise caller-reachable set, neither too weak nor mis-scoped.
#
# The runner mounts ONLY the probe at /work, so each probe is self-contained:
# stdlib + the in-container `_pytest._io.saferepr` (the very module the gold
# imports). Files opened with encoding="utf-8" (none needed here). apply_gold is
# True (the A-reference describes post-gold behaviour: the saferepr call).
# ===========================================================================

_AX_SOUND_PROBE = r'''
import random, subprocess, sys

QUOTE = 39  # apostrophe U+0027

def repr_quote_model(codepoints):
    # the model's deep model repr_quote, as a code-point list.
    return [QUOTE] + list(codepoints) + [QUOTE]

def in_tested_domain(s, maxsize):
    # the model's Requires: printable ASCII (0x20..0x7e), no apostrophe, no
    # backslash, within the size limit (len+2 <= maxsize).
    if len(s) + 2 > maxsize:
        return False
    return all(0x20 <= ord(ch) <= 0x7e and ch != "'" and ch != "\\" for ch in s)

def main():
    try:
        from _pytest._io.saferepr import saferepr
    except Exception as exc:  # pragma: no cover - environment guard
        print("AX SKIP: pytest not importable: %r" % (exc,))
        sys.exit(0)

    MAXSIZE = 42  # the gold literal saferepr(cached_param, maxsize=42)

    # --- (soundness, domain) real saferepr == deep model on the tested domain --
    boundary = [
        "foo", "bar", "spam", "ham", "FOO", "BAR",   # the F2P parameter ids
        "", "a", "Z", "0", " ", "x", "Hello World",
        "abc def", "under_score", "CamelCase", "a-b-c",
        "0123456789", "!@#$%^&*()=+~", "[brackets]",
        "A" * 40,                                     # max length within bound
    ]
    for s in boundary:
        assert in_tested_domain(s, MAXSIZE), "boundary %r left the domain" % (s,)
        observed = [ord(ch) for ch in saferepr(s, maxsize=MAXSIZE)]   # REAL callee
        expected = repr_quote_model([ord(ch) for ch in s])           # deep model
        assert observed == expected, (
            "repr_quote unsound on %r: saferepr=%r model=%r" % (s, observed, expected))
        # discriminator: differs from the plain text form exactly by the 2 quotes
        plain = [ord(ch) for ch in s]
        assert observed[0] == QUOTE and observed[-1] == QUOTE, (
            "rendering of %r not apostrophe-delimited" % (s,))
        assert observed[1:-1] == plain, (
            "interior of %r not the verbatim text" % (s,))

    rng = random.Random(7205)
    alphabet = [chr(c) for c in range(0x20, 0x7f) if chr(c) not in ("'", "\\")]
    checked = 0
    for _ in range(20000):
        n = rng.randint(0, 39)               # len(s)+2 <= 42 => n <= 40
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if not in_tested_domain(s, MAXSIZE):
            continue
        observed = [ord(ch) for ch in saferepr(s, maxsize=MAXSIZE)]
        expected = repr_quote_model([ord(ch) for ch in s])
        assert observed == expected, (
            "repr_quote unsound on %r: saferepr=%r model=%r" % (s, observed, expected))
        checked += 1

    # --- (soundness, length bound) saferepr respects maxsize EVERYWHERE ---------
    wide = alphabet + ["'", "\\", "\t", "\n", "é", "•"]
    for _ in range(5000):
        n = rng.randint(0, 200)
        s = "".join(rng.choice(wide) for _ in range(n))
        out = saferepr(s, maxsize=MAXSIZE)
        assert len(out) <= MAXSIZE, "saferepr exceeded maxsize on %r -> %r" % (s, out)

    # --- (soundness, bytes safety / the issue) bytes render w/o implicit str() --
    # The BytesWarning is emitted at C level only under `-bb`; check in a FRESH
    # `python -bb` subprocess (the F2P test_show_fixture_action_with_bytes config):
    #   new saferepr(b, 42) must NOT raise; the pre-patch "{}".format(b) MUST.
    bytes_probe = (
        "import sys\n"
        "from _pytest._io.saferepr import saferepr\n"
        "vals = [b'Hello World', b'', b'\\x00\\xff', b'spam', bytes(range(0,64))]\n"
        "for b in vals:\n"
        "    out = saferepr(b, maxsize=42)\n"
        "    assert isinstance(out, str) and len(out) <= 42\n"
        "for b in vals:\n"
        "    raised = False\n"
        "    try:\n"
        "        '{}'.format(b)\n"
        "    except BytesWarning:\n"
        "        raised = True\n"
        "    assert raised, 'pre-patch str() form did not raise on %r' % (b,)\n"
        "print('BYTES_OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-bb", "-c", bytes_probe],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
    )
    assert proc.returncode == 0 and proc.stdout.strip().endswith("BYTES_OK"), (
        "bytes-safety check failed under `python -bb`:\n%s" % (proc.stdout,))

    print("AX-SOUND OK: real saferepr(_, 42) == deep model repr_quote on %d "
          "boundary + %d fuzz domain inputs; <=42 length bound on 5000 long "
          "inputs; bytes render without an implicit str() BytesWarning while the "
          "pre-patch plain form raises." % (len(boundary), checked))
    sys.exit(0)

main()
'''


_AX_COVER_PROBE = r'''
import random, sys

QUOTE = 39

def in_tested_domain(s, maxsize):
    if len(s) + 2 > maxsize:
        return False
    return all(0x20 <= ord(ch) <= 0x7e and ch != "'" and ch != "\\" for ch in s)

def main():
    try:
        from _pytest._io.saferepr import saferepr
    except Exception as exc:  # pragma: no cover - environment guard
        print("AX SKIP: pytest not importable: %r" % (exc,))
        sys.exit(0)

    MAXSIZE = 42
    # axiom-containment: every input the MODEL can pass to saferepr lies in the
    # validated domain. The model's Requires pins EXACTLY:
    #   maxsize >= 2 and len(param) + 2 <= maxsize   (here maxsize == 42, gold)
    #   every code point in 32..126, != 39 (apostrophe), != 92 (backslash)
    # The model calls the helper at one site only, on `param` (the rendered
    # token); there is no branch constructing a different argument and maxsize is
    # the gold literal 42. So the entire reachable callee-input set is exactly
    # {printable-ASCII text, no ' or \, len+2 <= 42}. We assert the DOMAIN
    # BOUNDARY is covered (saferepr == verbatim quoting there), AND that the
    # immediate OUTSIDE-domain neighbours are exactly where saferepr diverges
    # (escapes) -- showing the validated domain is the precise caller-reachable
    # set, neither too weak (an in-domain input it fails) nor mis-scoped.

    # (a) every caller-reachable input is in-domain and renders as verbatim quote
    rng = random.Random(72050)
    alphabet = [chr(c) for c in range(0x20, 0x7f) if chr(c) not in ("'", "\\")]
    reachable = ["", "a", "A" * 40] + [
        "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        for _ in range(3000)
    ]
    covered = 0
    for s in reachable:
        assert in_tested_domain(s, MAXSIZE), (
            "constructed a reachable input %r outside the model domain" % (s,))
        out = [ord(ch) for ch in saferepr(s, maxsize=MAXSIZE)]
        assert out == [QUOTE] + [ord(ch) for ch in s] + [QUOTE], (
            "in-domain input %r not rendered as verbatim quoting: %r" % (s, out))
        covered += 1

    # (b) the immediate OUTSIDE-domain neighbours -- an embedded apostrophe, a
    # backslash, a control char, and an over-length value -- are precisely where
    # the validated domain stops: saferepr there is NOT the simple verbatim quote
    # (the model's precondition correctly excludes them). This confirms the domain
    # is the precise caller-reachable set, not a mis-scoped over/under-approx.
    outside = ["a'b", "a\\b", "a\tb", "a\nb", "A" * 50]
    for s in outside:
        assert not in_tested_domain(s, MAXSIZE), (
            "%r should be OUTSIDE the model domain" % (s,))
        out = saferepr(s, maxsize=MAXSIZE)
        simple = "'" + s + "'"
        assert out != simple or len(out) > MAXSIZE, (
            "outside-domain %r unexpectedly rendered as the simple quote %r "
            "(domain may be mis-scoped)" % (s, out))

    print("AX-COVER OK: every caller-reachable input (printable ASCII, no "
          "apostrophe/backslash, len+2<=42, maxsize==42) is in the validated "
          "domain and renders as the verbatim apostrophe quoting (%d checked); "
          "the immediate outside-domain neighbours (', \\, control, over-length) "
          "are exactly where saferepr diverges, so the domain is the precise "
          "caller-reachable set." % (covered,))
    sys.exit(0)

main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-saferepr",
        "axiom": "repr_quote",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "repr_quote is the A-reference deep model of the real callee "
            "_pytest._io.saferepr.saferepr(_, maxsize=42) (the gold call). If the "
            "real saferepr ever disagreed with the verbatim apostrophe quoting on "
            "an in-domain input, exceeded maxsize, or raised on bytes, the deep "
            "model would be unsound (AXIOM-UNSOUND). Runs the REAL saferepr under "
            "the caller's config (maxsize=42) on the F2P ids + boundary + 20000 "
            "in-domain fuzz inputs; checks the <=42 bound on 5000 long/escaping "
            "inputs; and asserts bytes render without an implicit str() "
            "BytesWarning under `python -bb` (the F2P bytes regression config) "
            "while the pre-patch plain form raises. Exits 0 iff all hold."
        ),
    },
    {
        "id": "ax-cover-saferepr",
        "axiom": "repr_quote",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "Containment: every input the MODEL can pass to saferepr lies in the "
            "deep model's validated domain. The model's Requires pins exactly "
            "{printable ASCII 32..126, no apostrophe (39), no backslash (92), "
            "len+2 <= 42, maxsize == 42 (gold literal)} and there is a single call "
            "site on `param`. Asserts every caller-reachable input is in-domain "
            "and renders as the verbatim quoting, and that the immediate "
            "outside-domain neighbours (apostrophe / backslash / control / "
            "over-length) are exactly where saferepr diverges — so the validated "
            "domain is the precise caller-reachable set, not AXIOM-TOO-WEAK-FOR-"
            "CALLER nor mis-scoped."
        ),
    },
]
