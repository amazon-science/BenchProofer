"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7521 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_readCaptured`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``). The nagini bundle models the readback as
``captured_readback(written: List[int]) -> List[int]`` over a ``PSeq[int]``
carrier of code points, under a fractional-permission (``Acc(...,1/2)``)
read-only frame, and pins the postcondition ``ToSeq(Result()) == ToSeq(written)``
— the readback reproduces the written stream VERBATIM. This Lean bundle models
the SAME single purely-functional core over a ``List Char`` carrier, and the SAME
grounding: the postcondition is the IDENTITY on the input carrier
(``result = written``), with no opaque answer key to echo. Every nagini value
case carries over as an attack on that one identity clause, or as a faithful
correct positive; the nagini frame/permission-mutation class is VACUOUS here
(referential transparency — see ``assessment``), and the nagini AXIOM_TESTS are
dropped (the axiom lane is G-AX's job; this gate ignores it).

The nagini ``admiss-selfcall`` case DOES carry over, and an audit landed it: see
``admiss-reported-shapes-eval``. Nagini's version establishes a fractional
permission on a fresh argument, which has no counterpart here — but the LANE it
serves does. On a total carrier the analogue of PRECOND-TOO-STRONG is the
obligation being unsatisfiable at exactly a reported-shaped input, which a
positive that discharges the obligation at that concrete input BY EVALUATION,
before closing the frozen obligation verbatim, tests directly. Dropping the lane
would have removed one of the three directions this gate exists to test.

DEFENDED SURFACE (one modeled behavior; one top-level clause).
``problem_spec_readCaptured written result`` pins EXACTLY ``result = written``:
the text read back out of a capture buffer must reproduce, character for
character, the text that was written into it — nothing dropped, rewritten,
merged, or inserted. Every carriage return survives; none is folded to a line
feed. The BEHAVIOURAL DISCRIMINATOR (the fix) is precisely this verbatim
survival: the pre-fix readback rewrote a carriage return to a line feed AND
swallowed a line feed that immediately followed one, so the reported inputs
containing a carriage return read back changed.

THE FOUR WRONGNESS CLASSES the clause names, and which rival attacks each. The
clause's own docstring enumerates four ways a readback can betray it — a
character *rewritten*, *merged*, *dropped*, or *inserted* — and a battery that
probes only some of them attests only to those:

  * REWRITTEN — ``weak-cr-fold`` (every carriage return) and
    ``weak-trailing-cr-fold`` (only the one at the boundary). Length-preserving:
    the readback has the right shape and the wrong content.
  * MERGED — ``weak-cr-lf-merge``. Two written characters read back as one, so
    the readback is SHORTER at an interior position. This is the class an
    audit found unprobed: a per-character rewrite is only half of the pre-fix
    behavior, and the half it omits is the one that changes the length.
  * DROPPED — ``weak-drop-last``. Length-shortening at the boundary.
  * INSERTED — ``weak-append-lf``. Length-LENGTHENING; the only class whose
    readback is longer than what was written, and the only rival refuted at the
    EMPTY stream.

  Plus one class the clause implies but does not name: ORDER. ``weak-reversed``
  returns the right multiset of characters in the wrong order, so every
  length- and content-based check passes and only the positional equality of
  ``result = written`` senses it.

BINDER STRUCTURE. The spec predicate has ONE input binder, ``written`` (the
character stream written into the buffer). It is load-bearing and is varied
across the reject witnesses over SIX distinct points (``pts=6``): a carriage
return MID-sequence (``['\r','a']``), one at the TRAILING boundary
(``['a','\r']``), a carriage-return-free stream (``['x','y']``, exposing a
length/truncation defect), a carriage-return/line-feed PAIR (``['\r','\n']``,
the only point where a merge is distinguishable from a rewrite), the EMPTY
stream (``[]``, where only an insertion is observable at all), and a
carriage-return-bearing stream long enough for order to matter
(``['a','\r','b']``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival WRITES through the read-only ``Acc(...,1/2)`` reference
    to normalize the input in place. On this referentially transparent carrier
    there is no heap, no aliasing, no fractional permission, and no mutable input
    cell: ``written`` is an immutable value passed by the ``∀`` binder. The
    class has no counterpart and no substitute is fabricated (porting map:
    vacuous here). See ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED in the
    argument: ``result = written`` is the identity on the input carrier, with no
    opaque answer key an implementation could echo. Producing the output from the
    input IS doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: fold every carriage return to a line feed;
    fold only a TRAILING carriage return (the sharper sub-domain of the reported
    witnesses); merge a carriage-return/line-feed PAIR into a single line feed
    (the length-changing half of the pre-fix behavior); an off-by-one that drops
    the last read code point (correct only on the empty stream); an insertion
    that appends a line feed (wrong on EVERY input, including the empty one);
    and an order permutation that returns the right characters transposed. Each
    violates the single identity clause at a concrete input, refuted by a
    ``decide``-able witness.

DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. This bundle is
vanilla Lean 4 + Mathlib with no ``loom.semantics.termination`` setting: a total
carrier by construction, since every ``def`` must be shown terminating for the
file to elaborate at all. A diverging rival is therefore expressible only as
``partial def``, and an audit measured what that costs: with the impl replaced by
``partial def implementation_readCaptured written := implementation_readCaptured
written``, the refutation witness FAILS on the rival (exit 1) with
``Tactic `unfold` failed to unfold `implementation_readCaptured```. A ``partial
def`` is opaque to reduction, so no witness can refute it and the case could only
ever land as ``witness-unproven`` — inconclusive, never a shippable rejection.
So there is nothing to ship in this lane; the disposition is a KNOWN HOLE in what
this gate can attest, not a claim that the battery is complete.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping the impl (the frozen ``simp only [... readCaptured_forIn_eq ...]``
script is tuned to the frozen ``for``-loop form), so a bare rejection attributes
nothing to the spec. Each reject case therefore carries a ``witness``: a Lean
``example`` stating ``¬ problem_spec_readCaptured w (implementation_readCaptured
w)`` at one concrete ``w``. The carrier is fully transparent (``List Char``
literals, no opaque callee), so each witness closes by ``decide``; it elaborates
against the rival (the rival provably contradicts the identity at ``w``) and
FAILS against the frozen solution (gold satisfies the identity at ``w``), so it
is a real discriminator, not a tautology.

REGION-SURGERY: every variant is built by ``_swap`` on ``_BASE`` editing text
inside the impl region (and, for positive controls that re-prove, the proof
body). The frozen spec (post-conditions region + the ``theorem
correct_readCaptured`` statement) is never touched.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7521"

_DIR = Path(__file__).parent
_BASE = (_DIR / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_IMPL = (
    "def implementation_readCaptured (written : List Char) : List Char := Id.run do\n"
    "  let mut out : Array Char := #[]\n"
    "  for c in written do\n"
    "    out := out.push c\n"
    "  return out.toList")

_PROOF_BODY = (
    "  intro written\n"
    "  unfold problem_spec_readCaptured implementation_readCaptured\n"
    "  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]\n"
    "  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written\n"
    "  simp")

# The two reported line-ending shapes, as concrete streams: a progress-style
# stream ending in a LONE carriage return, and the same stream ending in a
# carriage-return/line-feed PAIR. Both are shapes the report exhibits.
_PT_CR = "['0','%','\\r']"
_PT_CRLF = "['0','%','\\r','\\n']"

for _a in (_IMPL, _PROOF_BODY):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS / SOUNDNESS  (expect "verify")
# ===========================================================================

# (P1) direct identity — the cheapest honest impl: hand back the written stream
# unchanged. A different SHAPE from the frozen accumulator loop, so it needs its
# own proof; the obligation `result = written` closes by `rfl` after unfolding.
# MUST verify; else the spec is over-fit to the loop FORM => SPEC-TOO-STRONG.
_POS_IDENTITY = _swap(
    _BASE, _IMPL,
    "def implementation_readCaptured (written : List Char) : List Char :=\n"
    "  written")
_POS_IDENTITY = _swap(
    _POS_IDENTITY, _PROOF_BODY,
    "  intro written\n"
    "  rfl")

# (P2) reverse-of-reverse — a genuinely different shape (a full round-trip that
# is provably the identity) that still copies verbatim. `simp` discharges
# `written.reverse.reverse = written`. MUST verify; else the spec is over-fit to
# a particular traversal => SPEC-TOO-STRONG.
_POS_REVREV = _swap(
    _BASE, _IMPL,
    "def implementation_readCaptured (written : List Char) : List Char :=\n"
    "  written.reverse.reverse")
_POS_REVREV = _swap(
    _POS_REVREV, _PROOF_BODY,
    "  intro written\n"
    "  unfold problem_spec_readCaptured implementation_readCaptured\n"
    "  simp")

# (P3) map-identity — element-wise pass applying the identity map to each code
# point, a third distinct shape. `simp` discharges `written.map id = written`.
# MUST verify; else the spec is over-fit to a copy that does not touch each
# element => SPEC-TOO-STRONG.
_POS_MAPID = _swap(
    _BASE, _IMPL,
    "def implementation_readCaptured (written : List Char) : List Char :=\n"
    "  written.map id")
_POS_MAPID = _swap(
    _POS_MAPID, _PROOF_BODY,
    "  intro written\n"
    "  unfold problem_spec_readCaptured implementation_readCaptured\n"
    "  simp")

# (P4) ADMISSIBILITY — non-vacuity of the obligation at the reported input
# shapes. The frozen obligation is an unconditional `∀ written`, so there is no
# precondition binder to attack directly; on a total carrier the analogue of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly the inputs
# the reported failures observe. This case tests that directly: it discharges
# `problem_spec_readCaptured` BY EVALUATION (`decide`, the carrier is fully
# transparent) at the two concrete reported shapes — a stream ending in a LONE
# carriage return and one ending in a carriage-return/line-feed PAIR — as two
# `have`s, and only THEN closes the frozen obligation with the frozen tactic body
# verbatim. So the identity clause is shown SATISFIABLE at the very points the
# battery's rivals are refuted at, rather than merely provable in the abstract.
# Nothing is assumed: no new declaration, no assumption token, the theorem
# STATEMENT is byte-identical, and the frozen proof body is retained unchanged as
# the closing step. Only the proof region is touched (the impl stays frozen), so
# a failure of either `have` could only mean the modeled readback is
# unsatisfiable at a reported input => PRECOND-TOO-STRONG.
_POS_ADMISS = _swap(
    _BASE, _PROOF_BODY,
    f"  have _pt_cr :\n"
    f"      problem_spec_readCaptured {_PT_CR}\n"
    f"        (implementation_readCaptured {_PT_CR}) := by\n"
    "    unfold problem_spec_readCaptured implementation_readCaptured\n"
    "    decide\n"
    f"  have _pt_crlf :\n"
    f"      problem_spec_readCaptured {_PT_CRLF}\n"
    f"        (implementation_readCaptured {_PT_CRLF}) := by\n"
    "    unfold problem_spec_readCaptured implementation_readCaptured\n"
    "    decide\n"
    + _PROOF_BODY)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes — expect "reject")
# Each keeps the frozen proof body (which no longer matches the reshaped impl),
# so verification fails; the WITNESS is what attributes the rejection to the spec.
# ===========================================================================

# (R1) PARTIAL-DOMAIN — the per-character carriage-return REWRITE. Every carriage
# return is rewritten to a line feed on readback, else copied verbatim. Correct on
# every carriage-return-free stream, wrong on every stream containing a carriage
# return (the reported sub-domain).
#
# SCOPE NOTE (audit): this is the length-PRESERVING half of the pre-fix readback,
# not the whole of it. The pre-fix behavior ALSO merges an adjacent
# carriage-return/line-feed pair into a single line feed, which R1 does not do:
# on ['\r','\n'] R1 returns ['\n','\n'] (two characters) where the pre-fix path
# returns ['\n'] (one). So R1 attacks the REWRITTEN clause only; the MERGED
# clause is a separate wrongness shape and gets its own rival (R1b) below.
_RIVAL_FOLD = _swap(
    _BASE, "    out := out.push c\n",
    "    out := out.push (if c = '\\r' then '\\n' else c)\n")

# (R1b) PARTIAL-DOMAIN — the MERGE: a carriage return followed by a line feed
# reads back as a single line feed, so two written characters become one and the
# readback is SHORTER at an interior position. Length-changing, unlike R1/R2, and
# it changes the length in the middle rather than at the boundary, unlike R3 — so
# it is the only rival that senses the identity clause's "nothing is merged".
# Correct on every stream with no adjacent carriage-return/line-feed pair.
_RIVAL_MERGE = _swap(
    _BASE, "    out := out.push c\n",
    "    if c = '\\n' && out.size > 0 && out[out.size-1]! = '\\r' then\n"
    "      out := out.set! (out.size-1) '\\n'\n"
    "    else\n"
    "      out := out.push c\n")

# (R1c) INSERTION — append a line feed to the readback. The only rival whose
# result is LONGER than what was written, and the only one wrong on EVERY input
# including the EMPTY stream (where a drop, a rewrite and a merge are all
# invisible), so it is what makes the empty stream a discriminating point at all.
_RIVAL_INSERT = _swap(
    _BASE, "  return out.toList\n",
    "  return out.toList ++ ['\\n']\n")

# (R1d) ORDER — the readback is the written stream REVERSED (prepend instead of
# append). Same length, same multiset of characters, every carriage return still
# present and unfolded: every length check and every "does a carriage return
# survive" check passes, and only the POSITIONAL equality of `result = written`
# senses it. Correct exactly on the palindromes, which the reported inputs are
# not.
_RIVAL_REVERSED = _swap(
    _BASE, "    out := out.push c\n",
    "    out := #[c] ++ out\n")

# (R2) PARTIAL-DOMAIN — trailing-carriage-return fold (the sharper sub-domain:
# the reported witnesses end in a lone carriage return). Only the LAST code point
# is folded; all other positions copy verbatim. Correct on any stream not ending
# in a carriage return (including one ending in a line feed), wrong on every
# stream ending in a lone carriage return.
_RIVAL_TAIL = _swap(
    _BASE, "  return out.toList\n",
    "  let n := out.size\n"
    "  if n > 0 then\n"
    "    if out[n-1]! = '\\r' then\n"
    "      out := out.set! (n-1) '\\n'\n"
    "  return out.toList\n")

# (R3) PARTIAL-DOMAIN — off-by-one truncation: drop the LAST read code point.
# Correct ONLY on the empty stream; for any non-empty stream the readback is one
# code point short, so the identity fails.
_RIVAL_TRUNC = _swap(
    _BASE, "  return out.toList\n",
    "  return out.toList.dropLast\n")


# ---------------------------------------------------------------------------
# witness scaffolds. Each states the spec predicate NEGATED at one concrete
# `written`, referencing only the (kept) spec + impl regions, closed by `decide`
# (the carrier is fully transparent). It elaborates against the rival and fails
# on the frozen solution.
# ---------------------------------------------------------------------------
def _witness(written):
    return (
        f"example : ¬ problem_spec_readCaptured {written}\n"
        f"    (implementation_readCaptured {written}) := by\n"
        "  unfold problem_spec_readCaptured implementation_readCaptured\n"
        "  decide\n")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-identity", "kind": "soundness", "expect": "verify",
     "module": _POS_IDENTITY,
     "rationale": "the cheapest honest impl — hand back the written stream "
                  "unchanged. A different SHAPE from the frozen accumulator loop, "
                  "re-proved with its own body (`rfl` after unfolding the identity "
                  "clause). A correct verbatim copy must verify; else the "
                  "postcondition is over-fit to one textual proof FORM => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-reverse-reverse", "kind": "soundness", "expect": "verify",
     "module": _POS_REVREV,
     "rationale": "a genuinely different shape: a full reverse-of-reverse "
                  "round-trip that is provably the identity, so it copies "
                  "verbatim. `simp` discharges `written.reverse.reverse = "
                  "written`. Must verify; else the spec is over-fit to a "
                  "particular traversal => SPEC-TOO-STRONG."},
    {"id": "pos-map-identity", "kind": "soundness", "expect": "verify",
     "module": _POS_MAPID,
     "rationale": "an element-wise pass applying the identity map to each code "
                  "point — a third distinct shape that touches every element yet "
                  "changes none. `simp` discharges `written.map id = written`. "
                  "Must verify; else the spec is over-fit to a copy that never "
                  "inspects each element => SPEC-TOO-STRONG."},

    # ---- admissibility (must VERIFY) ----
    {"id": "admiss-reported-shapes-eval", "kind": "admissibility",
     "expect": "verify", "module": _POS_ADMISS,
     "rationale": "NON-VACUITY at the reported input shapes. The frozen "
                  "obligation is an unconditional `∀ written` with no "
                  "precondition binder, so on this total carrier the analogue of "
                  "PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at "
                  "exactly a reported input. This case discharges "
                  "`problem_spec_readCaptured` BY EVALUATION (`decide`) at the "
                  "two concrete reported shapes — a stream ending in a LONE "
                  "carriage return (['0','%','\\r']) and one ending in a "
                  "carriage-return/line-feed PAIR (['0','%','\\r','\\n']) — as "
                  "two `have`s, and only then closes the frozen obligation with "
                  "the frozen tactic body verbatim. The identity clause is thus "
                  "shown SATISFIABLE at the very points the rivals are refuted "
                  "at, not merely provable in the abstract. The impl region stays "
                  "frozen and only the proof region is touched, so a failure of "
                  "either `have` could only mean the modeled readback is "
                  "unsatisfiable at a reported input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "weak-cr-fold", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FOLD,
     "refinement": "the length-PRESERVING half of the regression: rewriting every "
                   "carriage return to a line feed on readback. A faithful patch "
                   "that leaves the newline-translating read policy enabled "
                   "produces at least this rewrite and FAILS the F2P checks that "
                   "the readback ends in the carriage return that was written "
                   "(once the carriage return is folded to a line feed the tail no "
                   "longer matches) — a verify-not-resolve break. NOT the whole of "
                   "the pre-fix behavior, and the manifest does not claim it is: "
                   "the pre-fix readback additionally MERGES an adjacent "
                   "carriage-return/line-feed pair into one line feed, which this "
                   "rival does not (on ['\\r','\\n'] it returns two characters "
                   "where the pre-fix path returns one). That merge is a distinct "
                   "wrongness shape and is attacked separately by weak-cr-lf-merge.",
     "rationale": "REJECT from the identity clause `result = written`. The fold "
                  "emits a line feed where the input holds a carriage return, so "
                  "on any carriage-return-bearing input result != written. Refuted "
                  "at a stream with a carriage return MID-sequence "
                  "(['\\r','a']), where the rival returns ['\\n','a'] != "
                  "['\\r','a']. If it verified => SPEC-TOO-WEAK (the spec would "
                  "not sense carriage-return loss).",
     "witness": _witness("['\\r','a']")},
    {"id": "weak-trailing-cr-fold", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TAIL,
     "refinement": "folds only a TRAILING lone carriage return — exactly the "
                   "reported witnesses whose captured text ends in a carriage "
                   "return. A faithful patch losing only the trailing carriage "
                   "return still FAILS the F2P check that the readback ends in "
                   "that carriage return — verify-not-resolve. Sharper than "
                   "weak-cr-fold: it is correct on a stream ending in a line feed "
                   "yet still wrong on one ending in a lone carriage return.",
     "rationale": "REJECT from the identity clause `result = written`. On an input "
                  "ending in a lone carriage return the last result code point is a "
                  "line feed, not a carriage return, so result != written. Refuted "
                  "at a stream with a TRAILING carriage return (['a','\\r']), a "
                  "DIFFERENT input than weak-cr-fold on which that rival is "
                  "correct. If it verified => SPEC-TOO-WEAK (the spec would miss "
                  "carriage-return loss at the sequence boundary).",
     "witness": _witness("['a','\\r']")},
    {"id": "weak-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRUNC,
     "refinement": "off-by-one truncation: the readback drops its LAST code point, "
                   "so it is one shorter than what was written. A faithful patch "
                   "dropping the last captured code point corrupts the capture "
                   "round-trip the F2P/P2P exercise (the readback must equal what "
                   "was written), so it would NOT resolve — verify-not-resolve. "
                   "Supporting near-miss on a carriage-return-FREE input, so it "
                   "also varies the binder away from the carriage-return cases.",
     "rationale": "REJECT from the identity clause `result = written`. Dropping "
                  "the last code point leaves result one shorter than written on "
                  "every non-empty input; correct only on the empty stream. "
                  "Refuted at a carriage-return-free stream (['x','y']), where the "
                  "rival returns ['x'] != ['x','y']. If it verified => "
                  "SPEC-TOO-WEAK.",
     "witness": _witness("['x','y']")},
    {"id": "weak-cr-lf-merge", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_MERGE,
     "refinement": "the length-CHANGING half of the regression, and the half "
                   "weak-cr-fold does not model: a carriage return immediately "
                   "followed by a line feed reads back as a SINGLE line feed, so "
                   "the readback is one character short at an interior position. "
                   "This is what the newline-translating read policy does to the "
                   "pair, on top of rewriting a lone carriage return, so a faithful "
                   "patch that leaves that policy enabled exhibits BOTH — and the "
                   "reported inputs include the pair shape, whose F2P check that "
                   "the readback ends in the two characters written fails once they "
                   "are merged into one. Verify-not-resolve.",
     "rationale": "REJECT from the identity clause `result = written`, on the "
                  "\"nothing is MERGED\" reading rather than the \"nothing is "
                  "rewritten\" one: two written characters collapse to one, so "
                  "result is SHORTER than written while every carriage-return-free "
                  "and every pair-free stream still copies verbatim. Refuted at the "
                  "carriage-return/line-feed PAIR (['\\r','\\n']) — a fourth "
                  "distinct input, and the only one at which a merge is "
                  "distinguishable from weak-cr-fold's rewrite (there the rival "
                  "returns ['\\n'] where weak-cr-fold returns ['\\n','\\n']). If it "
                  "verified => SPEC-TOO-WEAK (the spec would sense a rewritten "
                  "character but not a merged pair).",
     "witness": _witness("['\\r','\\n']")},
    {"id": "weak-append-lf", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INSERT,
     "refinement": "INSERTION: the readback carries a line feed that was never "
                   "written, so it is one character LONGER than what was written. "
                   "A faithful patch whose readback appends a terminator corrupts "
                   "the capture round-trip the F2P/P2P exercise — the readback must "
                   "equal what was written, and the checks on what the captured "
                   "text ends in read the wrong final character — so it would not "
                   "resolve. Complements the other rivals, which all return a "
                   "result no longer than the input: none of them would catch a "
                   "spec that only bounded the readback's length from above.",
     "rationale": "REJECT from the identity clause `result = written`. Appending a "
                  "line feed makes result one longer than written on EVERY input, "
                  "so unlike every other rival here it has no correct sub-domain at "
                  "all. Refuted at the EMPTY stream (([] : List Char)) — a fifth "
                  "distinct input, and one on which every other rival in this "
                  "battery is CORRECT (a rewrite, a merge and a drop are all "
                  "invisible with no characters to rewrite, merge or drop), so it "
                  "is the only case that exercises the clause at the empty carrier. "
                  "If it verified => SPEC-TOO-WEAK (the spec would not sense an "
                  "inserted character).",
     "witness": _witness("([] : List Char)")},
    {"id": "weak-reversed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVERSED,
     "refinement": "ORDER: the readback holds exactly the characters that were "
                   "written, the right number of them, with every carriage return "
                   "present and unfolded — but transposed. A faithful patch that "
                   "assembles the readback in the wrong direction corrupts the "
                   "captured text the F2P/P2P compare against (the reported check "
                   "is on what the readback ENDS in, which under a reversal is the "
                   "first character written), so it would not resolve. This is the "
                   "one rival no length check and no \"does a carriage return "
                   "survive\" check can catch.",
     "rationale": "REJECT from the identity clause `result = written`, on its "
                  "POSITIONAL reading: list equality pins each character to its "
                  "index, not merely the multiset or the length, and a reversal "
                  "preserves both of those. Refuted at ['a','\\r','b'] — a sixth "
                  "distinct input, chosen long enough to be a non-palindrome (the "
                  "rival is correct on every palindrome, so a witness whose two "
                  "characters happened to be equal would not discriminate) and "
                  "still carriage-return-bearing. If it verified => SPEC-TOO-WEAK "
                  "(the spec would pin content and length but not order).",
     "witness": _witness("['a','\\r','b']")},
]
