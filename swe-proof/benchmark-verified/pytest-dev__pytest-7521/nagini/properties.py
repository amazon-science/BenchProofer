"""PBT manifest for pytest-dev__pytest-7521 (NOT a Nagini module; a record of
adversarial cases the runner swebench_nagini.pbt executes + stamps RESULT).

Defended surface (frozen spec in model.py; see refinement.md / mapping.md):

  captured_readback(written: List[int]) -> List[int]
    Requires: Acc(list_pred(written), 1/2)         -- written is READ-ONLY (1/2)
    Ensures (frame): Acc(list_pred(written), 1/2)  -- the 1/2 perm is returned
    Ensures: Acc(list_pred(Result()))
    Ensures (LOAD-BEARING): ToSeq(Result()) == ToSeq(written)
        the captured read-back reproduces the written code points VERBATIM --
        every carriage return (U+000D, 13) is preserved, NOT folded to a line
        feed (U+000A, 10).

  cr_folded(s)  (pure region, A-reference deep model -- NOT consumed in the
    proof, NOT referenced by the postcondition): a front-recursive fold that
    rewrites every carriage return (13) -> line feed (10), else identity. It is
    the carriage-return-losing read translation the REGRESSION exhibits (the
    default `io.TextIOWrapper` reader). The gold patch adds `newline=""` so the
    reader returns line endings untranslated (verbatim). cr_folded is validated
    == the real reader out-of-band by axiom_check.py (G-AX); the model proves
    only the identity.

This models the one-line gold hunk in FDCaptureBinary.__init__
(src/_pytest/capture.py:388):
  +                newline="",
which switches the EncodedFile (an io.TextIOWrapper subclass) from the default
universal-newline read policy (every '\\r','\\r\\n','\\n' -> '\\n', losing the
carriage return) to no translation (line endings returned verbatim). The F2P
witnesses are `"test\\r\\n"` and `"test\\r"`; both must read back ending in the
written newline.

GROUNDED-ORACLE NOTE: the postcondition `ToSeq(Result()) == ToSeq(written)` is
GROUNDED in the argument -- it is the IDENTITY on the input carrier, with no
opaque answer-key. There is therefore NO *wrong* echo a rival can return: the
cheapest honest impl is "copy `written`", which is exactly the gold (included
below as a positive control). The pure helper `cr_folded` is NOT referenced by
the postcondition, so echoing it does NOT satisfy the postcondition -- echoing
it is instead the canonical partial-domain attack (it equals `written` on
CR-free inputs but diverges on every '\\r'-bearing input, the F2P sub-domain).
The uniqueness lane is therefore: (a) can a rival subvert the read-only (1/2)
precondition by overwriting `written`? and (b) can a rival satisfy the identity
on the CR-free majority while losing carriage returns on the discriminating
sub-domain (the exact regression)?

CONTROL-FLOW-EFFECT: N/A. captured_readback is a pure value transform
(List[int] -> List[int]); there is no raise / return-code / side-effect channel
invisible to the ToSeq value abstraction, so a capability-token rival adds
nothing. (Stated in assessment.)

AXIOM LANE: there is NO @ContractOnly axiom in this bundle (axioms region
empty). The changed read-back is modelled DEEPLY (pure region) and validated ==
the real callee (io.TextIOWrapper, the stdlib class EncodedFile subclasses)
out-of-band by axiom_check.py (G-AX). PBT re-runs that real-callee equivalence
as an axiom-soundness probe: (1) the real `newline=""` read-back reproduces the
written text VERBATIM [the FIX = model.py's postcondition]; (2a) the real
default reader's output never contains a carriage return [the regression] and
(2b) equals cr_folded on lone-CR inputs. axiom_check.py's logic (stdlib io /
tempfile / random only, no file opens, no repo import) is read on the HOST at
load time and embedded into the probe string (the runner mounts only the probe
at /work). A containment probe is N/A: there is no axiom Requires domain for a
caller-reachable input to fall outside (no consumed axiom).

REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY text
inside # impl-start/# impl-end (the invariants are nested inside that region, so
editing them is still inside impl and preserves same_spec). The frozen spec
(axioms / pure / pre-conditions / post-conditions / signatures) is never touched.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7521"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_INIT = "    result = []  # type: List[int]\n    i = len(written)\n"
_INV_TOSEQ = "        Invariant(ToSeq(result) == ToSeq(written).drop(i))\n"
_READ_C = "        c = written[i - 1]\n"
_ASSERT_1 = "        Assert(ToSeq(written).drop(i - 1)[0] == c)\n"
_ASSERT_2 = ("        Assert(ToSeq(written).drop(i - 1).drop(1) == "
             "ToSeq(written).drop(i))\n")
_PREPEND = "        result = [c] + result\n"
_DEC = "        i = i - 1\n"
_RETURN = "    return result\n"
# the full executable body (everything from `result = []` through `return result`)
_BODY = _BASE[_BASE.index(_INIT):_BASE.index("    # impl-end")]

for _a in (_INIT, _INV_TOSEQ, _READ_C, _ASSERT_1, _ASSERT_2, _PREPEND, _DEC,
           _RETURN):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"
assert _BASE.count(_BODY) == 1


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL -- local-variable reshape of the gold backward loop.
# Bind `j = i - 1` and read through it; reorder the two INDEPENDENT framing
# asserts. Semantically identical, every invariant kept verbatim, the gold proof
# obligations preserved (the second assert no longer depends on the first, so the
# order is immaterial). MUST verify; else the postcondition is over-fit to one
# textual FORM of the proof => SPEC-TOO-STRONG.
_POS_RESHAPE = _swap(
    _BASE,
    _READ_C + _ASSERT_1 + _ASSERT_2,
    "        j = i - 1\n"
    "        c = written[j]\n"
    "        Assert(ToSeq(written).drop(j).drop(1) == ToSeq(written).drop(i))\n"
    "        Assert(ToSeq(written).drop(j)[0] == c)\n",
)
# update the prepend/dec to use the reshape's locals consistently (still a copy)
# (prepend/dec are unchanged: result=[c]+result, i=i-1 -- they reference c,i only)

# (5b) POSITIVE CONTROL -- forward APPEND loop (a genuinely different shape: the
# gold walks backward and front-prepends; this walks forward and appends). The
# loop invariant is the dual `ToSeq(result) == ToSeq(written).take(i)`, and the
# framing assert pins take(i+1) == take(i) + the element just read -- both are
# built-in PSeq theory facts about take (NOT a front-recursive @Pure fold, so no
# f(a+b)==f(a)+f(b) lemma is needed; cf. pilot failure-mode #3). MUST verify;
# else the spec is over-fit to the backward loop direction => SPEC-TOO-STRONG.
_POS_FORWARD = _swap(
    _BASE, _BODY,
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(written):\n"
    "        Invariant(Acc(list_pred(written), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(written))\n"
    "        Invariant(ToSeq(result) == ToSeq(written).take(i))\n"
    "        c = written[i]\n"
    "        Assert(ToSeq(written).take(i + 1) == "
    "ToSeq(written).take(i) + ToSeq(written).take(i + 1).drop(i))\n"
    "        Assert(ToSeq(written).take(i + 1).drop(i) == PSeq(c))\n"
    "        result = result + [c]\n"
    "        i = i + 1\n"
    "    return result\n",
)

# (6) ADMISSIBILITY -- a self-call on a fresh, F2P-shaped CR-bearing input
# "test\r" ([116,101,115,116,13]) establishes Acc(list_pred(.),1/2) (a freshly
# constructed list carries full permission) and asserts the result-property
# (ToSeq(_r) == ToSeq(probe)); then the gold body runs on the actual `written`.
# MUST verify; else the precondition rejects a normal F2P input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _INIT,
    "    probe = [116, 101, 115, 116, 13]  # type: List[int]\n"
    "    _r = captured_readback(probe)\n"
    "    Assert(ToSeq(_r) == ToSeq(probe))\n"
    "    result = []  # type: List[int]\n    i = len(written)\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (1) FRAME MUTATION -- MANDATORY (#1 weakness class). `written` is read-only at
# 1/2. This rival WRITES `written[i - 1] = 10` ('\n') before reading it,
# attempting to normalize the input in place so that a CR was never present and
# the identity is vacuously satisfiable. Under Acc(list_pred(written),1/2) a
# store needs FULL permission, so it MUST be rejected for INSUFFICIENT PERMISSION
# (not a value mismatch). All gold invariants/asserts are kept verbatim, so the
# rejection is attributable solely to the write.
_RIVAL_FRAME = _swap(
    _BASE, _READ_C,
    "        written[i - 1] = 10\n        c = written[i - 1]\n",
)

# (3a) PARTIAL-DOMAIN -- the carriage-return fold (== model_prepatch.py / the
# regression / cr_folded). The body pushes 10 ('\n') wherever the written code
# point is 13 ('\r'), else copies verbatim. The ToSeq invariant is weakened to
# Invariant(True) and the two framing asserts are dropped (they would be FALSE
# under the fold), so the loop itself is internally consistent and verifies; the
# ONLY remaining obligation is the postcondition ToSeq(Result()) == ToSeq(written),
# which is FALSE on any input containing a carriage return (result has 10 where
# written has 13). Correct on every CR-free input, wrong on every '\r'-bearing
# input (the F2P sub-domain). The invariants markers are kept intact (only the
# ToSeq line's text changes, inside the impl region) so same_spec holds.
_RIVAL_FOLD = _swap(_BASE, _INV_TOSEQ, "        Invariant(True)\n")
_RIVAL_FOLD = _swap(
    _RIVAL_FOLD,
    _READ_C + _ASSERT_1 + _ASSERT_2 + _PREPEND,
    "        c = written[i - 1]\n"
    "        d = c\n"
    "        if c == 13:\n"
    "            d = 10\n"
    "        result = [d] + result\n",
)

# (3b) PARTIAL-DOMAIN -- trailing-CR-only fold (the sharper sub-domain: the
# borgbackup witness '  0%\r' and the F2P `"test\r"` end in a lone CR). Only the
# LAST code point is folded 13 -> 10 (i == len on the first iteration); all other
# positions copy verbatim. Correct on every input not ending in '\r' (including
# "test\r\n", whose last char is '\n'), wrong on every input ending in a lone
# '\r'. Demonstrates the postcondition senses CR loss at the boundary too, not
# just mid-sequence. The ToSeq invariant is weakened to Invariant(True) and the
# framing asserts dropped (false under the conditional fold).
_RIVAL_TAIL = _swap(_BASE, _INV_TOSEQ, "        Invariant(True)\n")
_RIVAL_TAIL = _swap(
    _RIVAL_TAIL,
    _READ_C + _ASSERT_1 + _ASSERT_2 + _PREPEND,
    "        c = written[i - 1]\n"
    "        d = c\n"
    "        if c == 13 and i == len(written):\n"
    "            d = 10\n"
    "        result = [d] + result\n",
)

# (3c) PARTIAL-DOMAIN -- drop the LAST written code point (off-by-one truncation:
# stop the backward copy at i == 1 instead of i == 0, never copying written[0]).
# Correct ONLY on the empty input; for the F2P inputs the leading 't' is dropped
# and length differs by one, so ToSeq(Result()) != ToSeq(written). The ToSeq
# invariant is retained but re-pinned to drop(i) which still holds for i>=1; the
# loop guard `i > 1` and the postcondition are the discriminator. (Supporting
# near-miss; carries a real refinement below.)
_RIVAL_TRUNC = _swap(_BASE, "    while i > 0:\n", "    while i > 1:\n")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "local-variable reshape of the gold backward loop (bind j=i-1, "
                  "read through it, reorder the two independent framing asserts). "
                  "Semantically identical, every invariant kept verbatim, all gold "
                  "proof obligations preserved. Must verify; else the postcondition "
                  "is over-fit to one textual proof FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-forward-append", "kind": "soundness", "expect": "verify",
     "module": _POS_FORWARD,
     "rationale": "a genuinely different shape: forward walk + append (gold walks "
                  "backward + front-prepends), with the dual invariant "
                  "ToSeq(result)==ToSeq(written).take(i) and a take-based framing "
                  "assert. take is built-in PSeq theory (NOT a front-recursive @Pure "
                  "fold), so no f(a+b)==f(a)+f(b) lemma is needed (pilot failure-mode "
                  "#3 avoided). A correct verbatim copy must verify; else the spec is "
                  "over-fit to loop DIRECTION => SPEC-TOO-STRONG."},
    {"id": "admiss-selfcall", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on a fresh F2P-shaped CR-bearing input \"test\\r\" "
                  "([116,101,115,116,13]) must establish the precondition "
                  "Acc(list_pred(.),1/2) (a fresh list carries full perm) and the "
                  "result-property Assert(ToSeq(_r)==ToSeq(probe)). If the precondition "
                  "rejects this normal F2P input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-written", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: FDCapture.snap() reads "
                   "back the captured text (self.tmpfile.read()) -- it never mutates the "
                   "bytes/text it captured, and the written str is immutable. The rival "
                   "exists solely to test whether the read-only (1/2) precondition can be "
                   "subverted by overwriting `written` in place (rewriting CRs away so the "
                   "identity holds vacuously). There is no resolving patch that rewrites "
                   "its captured input, so a verifying rival would be a pure "
                   "verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe. `written[i-1] = 10` writes through a "
                  "1/2 (read-only) reference and MUST fail for INSUFFICIENT PERMISSION (a "
                  "store needs full Acc(list_pred(written))), NOT a value mismatch; the "
                  "gold invariants/asserts are kept verbatim so the rejection is "
                  "attributable solely to the write. Rejection source: the PERMISSION "
                  "SYSTEM. If it verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "weak-cr-fold", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FOLD,
     "refinement": "this is EXACTLY the regression (== model_prepatch.py == cr_folded): "
                   "folding every '\\r' -> '\\n' on read-back is the default "
                   "io.TextIOWrapper newline policy the gold patch fixes by adding "
                   "newline=\"\". A faithful patch that omits newline=\"\" (or otherwise "
                   "leaves the default reader) produces this fold and FAILS the F2P "
                   "test_cafd_preserves_newlines[\\r] and [\\r\\n] (out.endswith('\\r') / "
                   "endswith('\\r\\n') are false once the CR is folded to '\\n') -- "
                   "verify-not-resolve.",
     "rationale": "rejection source: the postcondition ToSeq(Result())==ToSeq(written). "
                  "The fold writes 10 where written holds 13, so on any '\\r'-bearing "
                  "input ToSeq(Result()) != ToSeq(written); the retained weaker index "
                  "invariant keeps the loop internally consistent so the ONLY unmet "
                  "obligation is the identity postcondition. If it verified => "
                  "SPEC-TOO-WEAK (the spec would not sense carriage-return loss)."},
    {"id": "weak-trailing-cr-fold", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TAIL,
     "refinement": "folds only a TRAILING lone carriage return ('\\r' as the last code "
                   "point) -> '\\n' -- exactly the borgbackup witness '  0%\\r' and the "
                   "F2P `print(\"test\", end=\"\\r\")` => out == 'test\\r'. A faithful "
                   "patch losing only the trailing CR still FAILS the F2P "
                   "test_cafd_preserves_newlines[\\r] (out.endswith('\\r') is false) -- "
                   "verify-not-resolve. Sharper than weak-cr-fold: it is correct on "
                   "\"test\\r\\n\" (last char '\\n') yet still wrong on \"test\\r\".",
     "rationale": "rejection source: the postcondition ToSeq(Result())==ToSeq(written). "
                  "On an input ending in a lone '\\r' the last result code point is 10, "
                  "not 13, so the identity fails; the loop stays internally consistent "
                  "under the retained index invariant. If it verified => SPEC-TOO-WEAK "
                  "(the spec would miss carriage-return loss at the sequence boundary)."},
    {"id": "weak-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRUNC,
     "refinement": "off-by-one truncation: the backward copy stops at i==1, never copying "
                   "written[0], so the read-back is missing its FIRST code point and is one "
                   "shorter. For the F2P inputs (\"test\\r\", \"test\\r\\n\") the leading "
                   "'t' is dropped, so out != the written text and out.endswith(nl) may "
                   "even pass by accident yet the captured text is corrupted -- a faithful "
                   "patch dropping the first captured code point fails the broader capture "
                   "round-trip the F2P/P2P exercise (the read-back must equal what was "
                   "written). Supporting near-miss with a real refinement.",
     "rationale": "rejection source: the postcondition ToSeq(Result())==ToSeq(written). "
                  "Stopping at i>1 leaves result == written.drop(1) (length one short), so "
                  "ToSeq(Result()) != ToSeq(written) on every non-empty input. Correct only "
                  "on []. If it verified => SPEC-TOO-WEAK."},
]


# ===========================================================================
# AXIOM LANE -- no @ContractOnly axiom is consumed; the changed read-back is an
# A-reference deep model validated == the real callee (io.TextIOWrapper, the
# stdlib class EncodedFile subclasses). We re-run that real-callee equivalence
# (axiom_check.py's logic, read on the HOST and embedded into a self-contained
# probe) as an axiom-soundness check: (1) the real `newline=""` read-back is
# verbatim [the FIX = model.py's postcondition]; (2a) the real default reader
# loses every carriage return [the regression] and (2b) equals cr_folded on
# lone-CR inputs. If any observation disagrees, the A-reference is unsound. A
# containment probe is N/A (no axiom Requires domain for a caller-reachable input
# to fall outside). axiom_check.py uses only stdlib io/tempfile/random, opens no
# files, and imports nothing repo-specific, so it runs unchanged in-container.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-readback-equals-real-reader",
        "axiom": "cr_folded",  # the A-reference deep model (not a consumed axiom)
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep model (the verbatim read-back model.py proves, and the "
                     "contrasting cr_folded fold) is an A-reference: it must equal the "
                     "REAL callee io.TextIOWrapper. This probe (axiom_check.py verbatim, "
                     "stdlib io/tempfile/random only) executes the real reader on the F2P "
                     "shape + boundary witnesses (\"test\\r\", \"test\\r\\n\", '  0%\\r', "
                     "'Greetings from DOS\\r', \\r-runs, mixed) + 20000 fuzz inputs and "
                     "asserts: (1) newline=\"\" read-back == written VERBATIM [the FIX = "
                     "model.py's postcondition ToSeq(Result())==ToSeq(written)]; (2a) the "
                     "default reader's output never contains a carriage return [the "
                     "regression]; (2b) on lone-CR (LF-free) inputs the default reader == "
                     "cr_folded code-point for code-point. Exit 0 iff every observation "
                     "agrees; any disagreement => the A-reference is UNSOUND.",
    },
]
