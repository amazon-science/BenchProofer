"""properties.py — PBT falsification manifest for sympy__sympy-16886.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical"). The battery is
reasoned from THIS spec's defended surface, not stamped out by a corruption
template.

The functions under spec
------------------------
    encode_morse(msg: List[int], sep: int) -> List[int]
    morse_list(c: int) -> List[int]

`encode_morse` renders ONE plaintext word -- a possibly-empty sequence of code
points that the Morse representation table represents -- into International
Morse Code: each symbol's standard representation, joined by a single separator
signal. `morse_list` is the per-symbol table lookup (modeled as an executable
List[int] builder) and is pinned on EVERY code point: the 52 represented ones to
their standard code, and every other one to no signals at all.

Read-only input (frame-mutation MANDATORY)
-------------------------------------------
`encode_morse`'s `msg` is READ-ONLY: Requires(Acc(list_pred(msg), 1/2)) and the
postcondition GIVES IT BACK (Ensures(Acc(list_pred(msg), 1/2))). So the
frame-mutation attack (directive 5) APPLIES and is MANDATORY: an impl that WRITES
to `msg` to satisfy the postcondition vacuously must be REJECTED for insufficient
permission. A byte-fuzzer never thinks to mutate the input — this is the project's
#1 weakness class. `morse_list`'s only input is a scalar `c: int` (no read-only
container), so the frame attack does not apply to it.

The load-bearing postcondition clauses
---------------------------------------
  encode_morse:
    (E1) Acc(list_pred(msg), 1/2)                 — read-only frame given back
    (E2) Acc(list_pred(Result()))                 — fresh result fully owned
    (E3) ToSeq(Result()) == encoded_seq(ToSeq(msg), sep)   — THE encoding pin
  morse_list:
    (M1) Acc(list_pred(Result()))
    (M2) ToSeq(Result()) == morse_of(c)           — THE per-symbol table pin,
         with NO Requires on c, so it binds on every code point

The DISCRIMINATING content of the gold patch lives in morse_of(49) == PSeq(dot,
dash, dash, dash, dash) = '.----' (the gold table) vs the pre-patch '----' (four
dashes). Any morse_list impl that returns four dashes for c==49 violates (M2);
any encode_morse that drops/mis-joins symbols violates (E3).

Why the battery covers letters, punctuation, unrepresented code points and the
empty word as well as digits
----------------------------------------------------------------------------
The correctness oracle is the whole F2P test function, and that function asserts
on letters ('ABC', 'SMS'), on punctuation ('!@#$%^&*()_+'), on the empty message
and on messages whose unrepresented characters must be DROPPED — not only on the
two digit strings the gold patch flips. A spec that pinned the digit branches
alone would leave the rest of the table free, and an impl free on a branch is an
impl that can carry a table corruption the oracle observes. `morse_of` is
therefore TOTAL on `int` and the battery attacks one branch of each class:
letter (c==65), digit (c==49, c==48), punctuation (c==33), unrepresented
(c==35), plus the empty word.

The @Pure oracles `morse_of` / `encoded_seq` are GROUNDED, not an answer-key
---------------------------------------------------------------------------
`morse_of(c)` is a TOTAL function of the arg, fully unfolded in the contract (an
ordered chain of literal PSeq returns per code point, and `no_signals()`
otherwise). `encoded_seq(s, sep)` is a TOTAL front-recursion over the input
sequence (morse_of(s[0]) joined by PSeq(sep) with encoded_seq(s.drop(1), sep),
and no signals for the empty word). The postconditions pin Result() to these.
There is therefore NO opaque oracle an impl could echo WITHOUT doing the work —
echoing `morse_of(c)` / `encoded_seq(ToSeq(msg), sep)` IS computing the answer
(and Nagini cannot materialise a PSeq into a List for free; the impl must
actually build the correct List[int]). Hence ungrounded-oracle ECHO (directive 2)
does NOT apply; instead we supply honest cheapest-correct positive controls that
MUST verify. Stated in the StructuredOutput assessment.

No control-flow / raise / side-effect difference is observable
--------------------------------------------------------------
Both functions are TOTAL over their precondition domains (a word of represented
symbols, of any length including zero; any code point at all for `morse_list`).
Neither raises nor has any side effect other than building a fresh result list;
the value abstraction `ToSeq(Result())` captures the entire observable
behaviour, and the read-only `msg` frame (E1) is already defended by the
frame-mutation rival. So there is no raise/effect channel invisible to the value
abstraction and CONTROL-FLOW-EFFECT (directive 4) is N/A; no capability-token
rival is needed. Stated in the assessment.

No @ContractOnly axioms / A-consumed callees
---------------------------------------------
This bundle consumes NO axiom (meta.axioms == []). The only deep model is the
A-reference `morse_of` (the whole representation table), validated == the real
`char_morse` by axiom_check.py / G-AX out-of-band. The proof never depends on an
axiom Ensures. Hence AXIOM_TESTS = [] (there is no @ContractOnly Requires-domain
to fuzz and no caller-reachable callee input to contain). The deep-model
soundness already lives in axiom_check.py (G-AX), which this PBT layer does not
duplicate.

Region surgery
--------------
Every variant is built by `_swap` on _BASE, editing ONLY text strictly inside an
`# impl-start`/`# impl-end` region (the invariants of encode_morse live INSIDE
its impl region and are part of the elided block). The frozen spec
(axioms/pure/pre/post-conditions + signatures) is never touched, so `same_spec`
holds for every spec case.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16886"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors: the exact gold impl text (verbatim from model.py impl regions).
# ---------------------------------------------------------------------------

# encode_morse impl body (empty-word guard + backward fold matching the
# front-recursive encoded_seq).
_GOLD_ENCODE = """    n = len(msg)
    if n == 0:
        empty = []  # type: List[int]
        return empty
    result = morse_list(msg[n - 1])  # type: List[int]
    Assert(ToSeq(msg).drop(n - 1) == PSeq(msg[n - 1]))
    i = n - 1
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(msg), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(n == len(msg))
        Invariant(0 <= i and i <= n - 1)
        Invariant(sep != dot() and sep != dash())
        Invariant(len(ToSeq(msg).drop(i)) == n - i)
        Invariant(ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 2 (headroom for the
        # morse_list call and the list constructions in the body), discharging
        # MustTerminate(3) from the precondition.
        Invariant(MustTerminate(i + 2))
        # invariants-end
        c = msg[i - 1]
        Assert(ToSeq(msg).drop(i - 1)[0] == c)
        Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))
        Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)
        result = morse_list(c) + [sep] + result
        i = i - 1
    Assert(ToSeq(msg).drop(0) == ToSeq(msg))
    return result"""

# The empty-word guard alone (first three statements of the body).
_GOLD_EMPTY_GUARD = """    n = len(msg)
    if n == 0:
        empty = []  # type: List[int]
        return empty"""

# The DIGIT block of morse_list's table (ten ordered conditionals), in ascending
# code-point order as the gold impl writes them.
_GOLD_DIGITS = """    if c == 48:
        return [dash(), dash(), dash(), dash(), dash()]
    if c == 49:
        return [dot(), dash(), dash(), dash(), dash()]
    if c == 50:
        return [dot(), dot(), dash(), dash(), dash()]
    if c == 51:
        return [dot(), dot(), dot(), dash(), dash()]
    if c == 52:
        return [dot(), dot(), dot(), dot(), dash()]
    if c == 53:
        return [dot(), dot(), dot(), dot(), dot()]
    if c == 54:
        return [dash(), dot(), dot(), dot(), dot()]
    if c == 55:
        return [dash(), dash(), dot(), dot(), dot()]
    if c == 56:
        return [dash(), dash(), dash(), dot(), dot()]
    if c == 57:
        return [dash(), dash(), dash(), dash(), dot()]"""

# The first branch of morse_list's table: the letter 'A' (65) -> '.-'.
_GOLD_LETTER_A = """    if c == 65:
        return [dot(), dash()]"""

# The punctuation branch for '!' (33) -> '-.-.--'.
_GOLD_BANG = """    if c == 33:
        return [dash(), dot(), dash(), dot(), dash(), dash()]"""

# The table's fall-through: an unrepresented code point contributes no signals.
_GOLD_TAIL = """    unrepresented = []  # type: List[int]
    return unrepresented"""

# The one statement that reads the plaintext before the fold — reused by the
# frame-mutation rival to inject a write into `msg` at a point where the
# in-bounds facts are already known, so the rejection is attributable to the
# permission system alone.
_ENCODE_READ = "    result = morse_list(msg[n - 1])  # type: List[int]\n"


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) morse_list DIGIT-BLOCK REORDER positive control. Test the ten digit
# branches in DESCENDING order (c==57 first, c==48 last) in the middle of an
# otherwise untouched 52-branch table. Each branch still returns the SAME
# correct code, so (M2) ToSeq(Result()) == morse_of(c) is discharged exactly as
# before — only the executable branch ORDER changes. No fold lemma is involved
# (morse_list has no loop). If this CORRECT impl fails to verify, the
# postcondition is over-fit to the gold ascending branch order =>
# SPEC-TOO-STRONG.
_POS_MLIST_REORDER = """    if c == 57:
        return [dash(), dash(), dash(), dash(), dot()]
    if c == 56:
        return [dash(), dash(), dash(), dot(), dot()]
    if c == 55:
        return [dash(), dash(), dot(), dot(), dot()]
    if c == 54:
        return [dash(), dot(), dot(), dot(), dot()]
    if c == 53:
        return [dot(), dot(), dot(), dot(), dot()]
    if c == 52:
        return [dot(), dot(), dot(), dot(), dash()]
    if c == 51:
        return [dot(), dot(), dot(), dash(), dash()]
    if c == 50:
        return [dot(), dot(), dash(), dash(), dash()]
    if c == 49:
        return [dot(), dash(), dash(), dash(), dash()]
    if c == 48:
        return [dash(), dash(), dash(), dash(), dash()]"""
_POS_REORDER = _swap(_BASE, _GOLD_DIGITS, _POS_MLIST_REORDER)

# (5b) encode_morse LOCAL-RESHAPE positive control. Compute the per-symbol code
# into a typed local `code` first, then prepend it once, instead of inlining the
# call into the `+` expression. SAME backward fold direction (matching the
# front-recursive encoded_seq — directive avoids forward-append against a
# front-recursive fold), SAME control flow, ALL gold invariants and framing asserts
# kept VERBATIM (so the loop-invariant proof obligation
# ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep) is discharged exactly as
# before). Only the data shape of one statement changes. If it fails => the spec is
# over-fit to the inlined-call code form => SPEC-TOO-STRONG.
_POS_ENCODE_RESHAPE = _GOLD_ENCODE.replace(
    "        result = morse_list(c) + [sep] + result",
    "        code = morse_list(c)  # type: List[int]\n"
    "        result = code + [sep] + result")
assert _POS_ENCODE_RESHAPE != _GOLD_ENCODE
_POS_RESHAPE = _swap(_BASE, _GOLD_ENCODE, _POS_ENCODE_RESHAPE)

# (5c) EMPTY-WORD GUARD RESHAPE positive control. The empty word is IN the
# modelled domain and its encoding is pinned to no signals at all. This control
# writes the same guard a different way — `len(msg) < 1` instead of the
# precomputed `n == 0`, and a differently-named local — so it is behaviourally
# identical. If it fails to verify, the empty-word clause of (E3) is over-fit to
# the gold statement form => SPEC-TOO-STRONG.
_POS_EMPTY_RESHAPE = """    n = len(msg)
    if len(msg) < 1:
        nothing = []  # type: List[int]
        return nothing"""
_POS_EMPTY = _swap(_BASE, _GOLD_EMPTY_GUARD, _POS_EMPTY_RESHAPE)

# (6) ADMISSIBILITY. The precondition must admit a normal F2P-shaped call: a
# word with the default separator '|' (code point 124). The witness re-derives
# the separator-side precondition facts for that concrete in-domain separator by
# leading Asserts — sep_accepted(124) holds (124 is none of the represented code
# points) and 124 differs from both signal code points — and confirms that a
# digit, a letter and a punctuation mark are all represented, i.e. all three
# symbol classes the F2P test uses are inside the domain. The gold body then
# follows UNCHANGED. (A self-call witness is not usable here: the caller's own
# MustTerminate(3) obligation cannot be handed to a callee demanding the same
# measure — the obligation system requires a strictly smaller callee measure —
# and that rejection would be about obligations, not admissibility.) If a normal
# in-domain input could not establish these facts, this would fail =>
# PRECOND-TOO-STRONG.
_ADMISS_BODY = (
    "    # Admissibility: the default separator '|' (124) is accepted and is\n"
    "    # neither signal; digits, letters and punctuation are all in-domain\n"
    "    # symbols, and the word may have any length.\n"
    "    Assert(sep_accepted(124))\n"
    "    Assert(124 != dot() and 124 != dash())\n"
    "    Assert(represented(49) and represented(65) and represented(33))\n"
    "    Assert(len(msg) >= 0)\n"
    "    # Real logic (unchanged behaviour).\n" + _GOLD_ENCODE
)
_ADMISS = _swap(_BASE, _GOLD_ENCODE, _ADMISS_BODY)


# ===========================================================================
# UNIQUENESS / FRAME-MUTATION RIVALS (must be REJECTED)
# ===========================================================================

# (FRAME-MUTATION — MANDATORY, directive 5) Before the fold, the rival WRITES to the
# read-only input `msg[0] = dash()` (clobbering the caller's first plaintext symbol
# in place). To assign `msg[0] = ...` Nagini needs FULL permission on `msg`, but the
# precondition grants only Acc(list_pred(msg), 1/2). The write is REJECTED for
# INSUFFICIENT PERMISSION — before any postcondition is even considered. The write is
# injected AFTER the empty-word guard, where `len(msg) >= 1` is already known, so
# nothing about bounds can be confused with the permission failure; the gold body
# (invariants, framing asserts, fold) is kept VERBATIM around it.
#
# Refinement (why its faithful real patch would NOT resolve): the half-permission
# abstracts the gold encoder's contract that it READS the plaintext word and the
# table and builds the codes in a FRESH carrier, leaving the input untouched
# (Python strings are immutable; the real per-word step only appends to a fresh
# `morseword` — crypto.py:1575-1580). A real "patch" that overwrote the input
# plaintext to encode (e.g. clobbered msg[0]) would corrupt the very symbol it must
# encode and any caller alias — under it `encode_morse('12345')` would no longer
# emit '.----|..---|...' for the original first symbol, so the F2P
# `test_encode_morse` exact-string assertion FAILS. It would NOT resolve. The
# half-permission is exactly the spec defending that read-only contract.
_RIVAL_FRAME = _swap(
    _BASE, _ENCODE_READ,
    "    msg[0] = dash()\n" + _ENCODE_READ,
)

# (uniqueness — PRE-PATCH bug / PARTIAL-DOMAIN on digit '1') The rival returns the
# four-dash code '----' for c==49 (the pre-patch table entry) and is CORRECT on
# every other symbol. It satisfies (M1) but VIOLATES (M2) ToSeq(Result()) ==
# morse_of(c) for c==49, where the frozen morse_of(49) is the five-signal '.----'.
# This is the EXACT discriminator the patch fixes (G-DIFF / model_prepatch.py).
#
# Refinement: its faithful real patch is the unmodified table `char_morse['1'] ==
# '----'`. Under it `encode_morse('12345')` renders '----|..---|...--|...'
# instead of '.----|...', so the F2P assertion
# `encode_morse('12345') == '.----|..---|...--|....-|.....'` FAILS. It would NOT
# resolve (this is precisely the bug the patch fixes). Rejection source: (M2) at
# c==49 (length 4 != 5 and value '----' != '.----').
_RIVAL_PREPATCH1 = _swap(
    _BASE,
    "    if c == 49:\n        return [dot(), dash(), dash(), dash(), dash()]",
    "    if c == 49:\n        return [dash(), dash(), dash(), dash()]",
)

# (uniqueness — PARTIAL-DOMAIN on digit '0') The rival returns a WRONG (but still
# five-signal) code for c==48: '....-' (dot,dot,dot,dot,dash = morse_of('4')) rather
# than the all-dash '-----'. Correct on every other symbol. It satisfies (M1) and is
# the right LENGTH (so a length-only check would pass), but VIOLATES (M2)
# ToSeq(Result()) == morse_of(48). This targets the value clause specifically, on a
# digit ('0') the F2P witness '67890' exercises as its LAST symbol.
#
# Refinement: its faithful real patch is a table whose '0' entry is wrong; under it
# `encode_morse('67890')` ends in '....-' instead of '-----', so the F2P assertion
# `encode_morse('67890') == '-....|--...|---..|----.|-----'` FAILS. It would NOT
# resolve. Rejection source: (M2) at c==48.
_RIVAL_WRONG0 = _swap(
    _BASE,
    "    if c == 48:\n        return [dash(), dash(), dash(), dash(), dash()]",
    "    if c == 48:\n        return [dot(), dot(), dot(), dot(), dash()]",
)

# (uniqueness — the LETTER branch of the table) The rival returns '--' for c==65
# instead of the letter 'A''s standard '.-'. Every other branch is correct, and no
# digit is touched at all: this is the rival class a digits-only domain could not
# see, because c==65 would then sit outside morse_list's precondition and (M2)
# would say nothing about it. With morse_of TOTAL on `int` the branch is pinned.
#
# Refinement: its faithful real patch is a table whose 'A' entry is '--'
# (`char_morse['A'] = '--'`) alongside the gold digit fix. Under it
# `encode_morse('ABC')` renders '--|-...|-.-.' instead of '.-|-...|-.-.', so the
# FIRST assertion of the F2P `test_encode_morse` FAILS even though every digit
# assertion passes and all 42 PASS_TO_PASS tests still pass. It would NOT resolve.
# Rejection source: (M2) at c==65 — morse_of(65) is PSeq(dot(), dash()).
_RIVAL_LETTER_A = _swap(
    _BASE, _GOLD_LETTER_A,
    "    if c == 65:\n        return [dash(), dash()]",
)

# (uniqueness — the PUNCTUATION branch of the table) The rival drops the final
# dash from '!' (c==33), returning the five-signal '-.-.-' instead of the
# six-signal '-.-.--'. Same class of hole as the letter rival, in the third
# symbol class of the table's key set.
#
# Refinement: its faithful real patch is a table whose '!' entry is '-.-.-'.
# Under it `encode_morse('!@#$%^&*()_+')` begins '-.-.-|...' instead of
# '-.-.--|...', so the F2P assertion
# `encode_morse('!@#$%^&*()_+') == '-.-.--|.--.-.|...-..-|-.--.|-.--.-|..--.-|.-.-.'`
# FAILS. It would NOT resolve. Rejection source: (M2) at c==33.
_RIVAL_BANG = _swap(
    _BASE, _GOLD_BANG,
    "    if c == 33:\n        return [dash(), dot(), dash(), dot(), dash()]",
)

# (uniqueness — an UNREPRESENTED code point) The rival gives '#' (c==35) a
# representation of one dot. 35 is not a key of the table, and the spec pins
# exactly that: morse_of(35) == no_signals(), so the lookup must contribute
# NOTHING. The rival therefore violates (M2) on a code point that a
# key-set-restricted precondition would have left free.
#
# Refinement: its faithful real patch ADDS a key, `char_morse['#'] = '.'`. That
# also enlarges `ok = set(mapping.keys())` (crypto.py:1569), so '#' is no longer
# deleted by `translate(msg, None, ''.join(chars - ok))` (crypto.py:1570) and it
# acquires its own separator-delimited field in the output. Under it
# `encode_morse('!@#$%^&*()_+')` renders '-.-.--|.--.-.|.|...-..-|...' — an extra
# '|.'  field — so the F2P assertion FAILS. It would NOT resolve. Rejection
# source: (M2) at c==35, where morse_of(35) is the empty signal sequence.
_RIVAL_UNREPRESENTED = _swap(
    _BASE, _GOLD_LETTER_A,
    "    if c == 35:\n        return [dot()]\n" + _GOLD_LETTER_A,
)

# (uniqueness — the EMPTY WORD) The rival returns three dots for the empty word
# and is correct on every non-empty word. The empty word is IN the domain and
# (E3) pins its encoding to no signals, so the rival is refuted; under a
# `Requires(len(msg) >= 1)` domain this branch would have been free.
#
# Refinement: the empty word is a WIDENING of the per-word step's real input set
# (mapping.md §2: `msg.split()` never yields an empty piece), so this rival's
# faithful patch -- a guard at the top of the per-word body, `if not word:
# morseword = ['...']` -- cannot fire, and the case is a PINNING check rather
# than a resolution-breaking rival: it shows the empty-word clause of (E3) is not
# vacuous. Under the coarser reading that binds the model to the whole encoder
# the same branch becomes `if not msg: return '...'`, and then
# `encode_morse('')` returns '...' instead of '', failing the F2P assertion
# `encode_morse('') == ''`. Rejecting it is right under both readings, and
# keeping the empty word IN the domain is what removes the
# `Requires(len(msg) >= 1)` dead branch that the coarser reading could exploit.
_RIVAL_EMPTY_WORD = _swap(
    _BASE, _GOLD_EMPTY_GUARD,
    "    if len(msg) == 0:\n        return [dot(), dot(), dot()]\n"
    + _GOLD_EMPTY_GUARD,
)

# (uniqueness — PARTIAL-DOMAIN on the FIRST symbol of the message) The rival builds
# the fold correctly for symbols 1..n-1 but SKIPS the first symbol: the loop runs
# `while i > 1` instead of `while i > 0`, so msg[0]'s code is never prepended. On a
# single-symbol message (n==1) it is correct (loop body never runs); it diverges
# only when len(msg) >= 2. All invariants/asserts are kept verbatim; only the loop
# guard changes.
#
# Refinement: its faithful real patch is a per-word step that skips the word's
# first symbol (e.g. `for letter in word[1:]`). Under it `encode_morse('12345')`
# emits '..---|...--|....-|.....' (missing the leading '.----|'), so the F2P
# assertion FAILS. It would NOT resolve. Rejection source: (E3)
# ToSeq(Result()) == encoded_seq(ToSeq(msg), sep) — on exit the result equals
# encoded_seq of ToSeq(msg).drop(1), not ToSeq(msg), so the loop-exit value at
# i==1 cannot satisfy the final postcondition for n>=2.
_RIVAL_SKIP_FIRST = _swap(_BASE, "    while i > 0:", "    while i > 1:")

# (uniqueness — PARTIAL-DOMAIN: WRONG separator on a sub-domain) The rival uses the
# correct separator between every adjacent pair EXCEPT it prepends `dot()` (a Morse
# signal) instead of `sep` on the very first fold step (i == n-1). Because the
# precondition guarantees sep != dot(), this is a genuine divergence whenever
# n >= 2: the join between the first two symbols uses the wrong signal. Correct on a
# single-symbol message. Invariants/asserts kept verbatim; only the joined separator
# of one step changes.
#
# Refinement: its faithful real patch is a per-word step that uses the wrong join
# token at one position (e.g. a stray hardcoded separator). Under it
# `encode_morse('12345')` emits '.----...---|...' (a '.' instead of '|' between the
# 1st and 2nd symbols), so the F2P exact-string assertion FAILS. It would NOT
# resolve. Rejection source: (E3) — encoded_seq joins with PSeq(sep) at every step,
# so substituting dot() at any step makes ToSeq(result) != encoded_seq(...) and the
# fold invariant ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep) cannot be
# re-established after the step that used dot().
_RIVAL_WRONG_SEP = _swap(
    _BASE,
    "        c = msg[i - 1]\n"
    "        Assert(ToSeq(msg).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))\n"
    "        Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)\n"
    "        result = morse_list(c) + [sep] + result\n"
    "        i = i - 1",
    "        c = msg[i - 1]\n"
    "        Assert(ToSeq(msg).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(msg).drop(i - 1).drop(1) == ToSeq(msg).drop(i))\n"
    "        Assert(len(ToSeq(msg).drop(i - 1)) == n - i + 1)\n"
    "        if i == n - 1:\n"
    "            result = morse_list(c) + [dot()] + result\n"
    "        else:\n"
    "            result = morse_list(c) + [sep] + result\n"
    "        i = i - 1",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-mlist-digit-block-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT impl: morse_list tests the "
                  "ten digit branches in DESCENDING order inside an otherwise "
                  "untouched 52-branch table, each returning the same correct "
                  "code. (M2) ToSeq(Result()) == morse_of(c) is discharged exactly "
                  "as for gold (no loop / no fold lemma involved). If it fails to "
                  "verify, the postcondition is over-fit to the gold ascending "
                  "branch order => SPEC-TOO-STRONG."},
    {"id": "pos-encode-local-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_RESHAPE,
     "rationale": "structurally-different but CORRECT impl: encode_morse computes the "
                  "per-symbol code into a typed local `code` then prepends it once, "
                  "instead of inlining morse_list(c) into the `+` expression. SAME "
                  "backward fold direction (no forward-append against the "
                  "front-recursive encoded_seq), ALL gold invariants/framing asserts "
                  "kept VERBATIM so the fold invariant is discharged as before. If it "
                  "fails => the spec is over-fit to the inlined-call form => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-empty-word-guard-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_EMPTY,
     "rationale": "the empty word is IN the modelled domain and (E3) pins its "
                  "encoding to no signals. This CORRECT impl writes the same guard "
                  "a different way (`len(msg) < 1` instead of the precomputed "
                  "`n == 0`, differently-named local). If it fails to verify, the "
                  "empty-word clause is over-fit to the gold statement form => "
                  "SPEC-TOO-STRONG."},
    {"id": "admiss-default-sep", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the precondition must admit a normal F2P-shaped call: a word with "
                  "the default separator '|' (code point 124). Leading Asserts "
                  "re-derive the separator-side facts for that concrete in-domain "
                  "value — sep_accepted(124) holds and 124 differs from both signal "
                  "code points — and confirm that a digit (49), a letter (65) and a "
                  "punctuation mark (33) are all represented, i.e. all three symbol "
                  "classes the F2P test uses are in-domain, with no length lower "
                  "bound assumed. The gold body follows unchanged. (A self-call "
                  "witness is unusable under the termination obligation: the caller's "
                  "MustTerminate(3) cannot be handed to a callee demanding the same "
                  "measure, and that rejection would be about obligations, not "
                  "admissibility.) If these facts could not be established for a "
                  "legitimate input => PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY) + uniqueness rivals (must be REJECTED) ----
    {"id": "rival-frame-mutate-msg", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "WRITES to the read-only input `msg[0] = dash()` before the fold, "
                   "clobbering the caller's first plaintext symbol in place. The "
                   "half-permission Acc(list_pred(msg), 1/2) abstracts the gold "
                   "encoder's contract that it READS the immutable plaintext and the "
                   "table and builds the codes in a FRESH carrier without mutating the "
                   "input (crypto.py:1575-1580; Python strings are immutable). A real "
                   "patch that overwrote the input plaintext would corrupt the very "
                   "symbol it must encode (and any caller alias), so `encode_morse('12345')` "
                   "would no longer emit '.----|...' for the original first symbol and "
                   "the F2P test_encode_morse exact-string assertion would FAIL — it "
                   "would NOT resolve.",
     "rationale": "FRAME-MUTATION (directive 5). Rejection source: the PERMISSION SYSTEM "
                  "— assigning msg[0] needs full Acc(list_pred(msg)) but the "
                  "precondition grants only 1/2, so the write fails for INSUFFICIENT "
                  "PERMISSION before any postcondition is considered (the write sits "
                  "after the empty-word guard, so `len(msg) >= 1` is already known and "
                  "no bounds obligation is involved). If it verified, a mutating impl "
                  "could satisfy (E3) vacuously => SPEC-TOO-WEAK."},
    {"id": "rival-prepatch-digit1-four-dash", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH1,
     "refinement": "morse_list returns the four-dash '----' for c==49 — exactly the "
                   "pre-patch table entry char_morse['1'] == '----' (model_prepatch.py, "
                   "the bug this instance fixes). Under that table "
                   "`encode_morse('12345')` renders '----|..---|...--|....-|.....' "
                   "instead of '.----|...', so the F2P assertion "
                   "`encode_morse('12345') == '.----|..---|...--|....-|.....'` FAILS. It "
                   "would NOT resolve (G-DIFF: model_prepatch.py fails this exact "
                   "postcondition).",
     "rationale": "Rejection source: the DISCRIMINATING clause (M2) ToSeq(Result()) == "
                  "morse_of(c) at c==49 — frozen morse_of(49) is the five-signal "
                  "'.----', so a four-dash result is both the wrong length (4 != 5) "
                  "and the wrong value. If it verified => SPEC-TOO-WEAK (admits the "
                  "pre-patch bug)."},
    {"id": "rival-wrong-digit0", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG0,
     "refinement": "morse_list returns a wrong but five-signal code '....-' (morse_of of "
                   "'4') for c==48 instead of the all-dash '-----'; correct on every "
                   "other symbol. Its faithful real patch is a table whose '0' entry is "
                   "wrong; under it `encode_morse('67890')` ends in '....-' instead of "
                   "'-----', so the F2P assertion "
                   "`encode_morse('67890') == '-....|--...|---..|----.|-----'` FAILS. It "
                   "would NOT resolve.",
     "rationale": "PARTIAL-DOMAIN on digit '0' (the LENGTH is right, so a length-only "
                  "check would not catch it). Rejection source: (M2) at c==48 — the "
                  "value '....-' != morse_of(48) == '-----'. If it verified => "
                  "SPEC-TOO-WEAK (a wrong same-length digit code slips through)."},
    {"id": "rival-dead-branch-letter-A", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LETTER_A,
     "refinement": "morse_list returns '--' for the letter 'A' (c==65) instead of the "
                   "standard '.-'; every digit branch is untouched. Its faithful real "
                   "patch sets `char_morse['A'] = '--'` alongside the gold digit fix. "
                   "Under it `encode_morse('ABC')` renders '--|-...|-.-.' instead of "
                   "'.-|-...|-.-.', so the FIRST assertion of the F2P "
                   "`test_encode_morse` FAILS while both digit assertions pass and all "
                   "42 PASS_TO_PASS tests still pass. It would NOT resolve.",
     "rationale": "This is the hole a digits-only modelled domain leaves open: with "
                  "`Requires(48 <= c and c <= 57)` on morse_list, c==65 is outside the "
                  "precondition and (M2) constrains nothing there, so the corruption "
                  "verifies. morse_of is TOTAL on int and morse_list carries no "
                  "Requires on c, so the branch is pinned. Rejection source: (M2) at "
                  "c==65 — morse_of(65) == PSeq(dot(), dash()). If it verified => "
                  "SPEC-TOO-WEAK (a table entry the F2P oracle reads is unpinned)."},
    {"id": "rival-wrong-punctuation-bang", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BANG,
     "refinement": "morse_list drops the final dash from '!' (c==33), returning the "
                   "five-signal '-.-.-' instead of the six-signal '-.-.--'. Its "
                   "faithful real patch is a table whose '!' entry is '-.-.-'; under it "
                   "`encode_morse('!@#$%^&*()_+')` begins '-.-.-|...' so the F2P "
                   "assertion "
                   "`encode_morse('!@#$%^&*()_+') == '-.-.--|.--.-.|...-..-|-.--.|-.--.-|..--.-|.-.-.'` "
                   "FAILS. It would NOT resolve.",
     "rationale": "the third symbol class of the table's key set (punctuation), same "
                  "hole shape as the letter rival. Rejection source: (M2) at c==33 — "
                  "morse_of(33) is six signals. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-unrepresented-emits-signals", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNREPRESENTED,
     "refinement": "morse_list gives '#' (c==35) a one-dot representation. 35 is not a "
                   "key of the table, and the faithful real patch ADDS one: "
                   "`char_morse['#'] = '.'`. That also enlarges "
                   "`ok = set(mapping.keys())` (crypto.py:1569), so '#' is no longer "
                   "deleted by `translate(msg, None, ''.join(chars - ok))` "
                   "(crypto.py:1570) and gains its own separator-delimited field. "
                   "Under it `encode_morse('!@#$%^&*()_+')` renders "
                   "'-.-.--|.--.-.|.|...-..-|...' — one extra field — so the F2P "
                   "assertion FAILS. It would NOT resolve.",
     "rationale": "an unrepresented code point must contribute NO signals, which is "
                  "what the deletion step guarantees; morse_of pins exactly that "
                  "(morse_of(35) == no_signals()). Rejection source: (M2) at c==35. If "
                  "it verified => SPEC-TOO-WEAK (the table's key set itself would be "
                  "unpinned, so an impl could enlarge it)."},
    {"id": "rival-empty-word-emits-signals", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY_WORD,
     "refinement": "returns three dots for the empty word, correct on every non-empty "
                   "word. The empty word is a WIDENING of the per-word step's real "
                   "input set (`msg.split()` never yields an empty piece, "
                   "crypto.py:1573), so the faithful per-word patch `if not word: "
                   "morseword = ['...']` cannot fire and this case is a PINNING check "
                   "-- it shows the empty-word clause of (E3) is not vacuous. Under "
                   "the coarser reading that binds the model to the whole encoder the "
                   "same branch is `if not msg: return '...'`, and then "
                   "`encode_morse('')` returns '...' instead of '', so the F2P "
                   "assertion `encode_morse('') == ''` FAILS and it would NOT resolve. "
                   "Rejecting it is right under both readings, and admitting the empty "
                   "word is what removes the `Requires(len(msg) >= 1)` dead branch the "
                   "coarser reading could exploit.",
     "rationale": "the empty word is INSIDE the domain (no `Requires(len(msg) >= 1)`), "
                  "so (E3) pins it: encoded_seq of the empty sequence is "
                  "no_signals(). Rejection source: (E3) at len(msg) == 0. If it "
                  "verified => SPEC-TOO-WEAK (a length the F2P oracle asserts on "
                  "would be unpinned)."},
    {"id": "rival-skip-first-symbol", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SKIP_FIRST,
     "refinement": "PARTIAL-DOMAIN on the first symbol: the fold loop runs `while i > 1` "
                   "instead of `while i > 0`, so msg[0]'s code is never prepended "
                   "(correct on a single-symbol word, diverges for len >= 2). Its "
                   "faithful real patch is a per-word step that skips the word's first "
                   "symbol (`for letter in word[1:]`); under it `encode_morse('12345')` "
                   "emits '..---|...--|....-|.....' (missing the leading '.----|'), so "
                   "the F2P assertion FAILS. It would NOT resolve.",
     "rationale": "Rejection source: (E3) ToSeq(Result()) == encoded_seq(ToSeq(msg), sep). "
                  "On exit the result equals encoded_seq of ToSeq(msg).drop(1), not "
                  "ToSeq(msg); the final Assert `ToSeq(msg).drop(0) == ToSeq(msg)` "
                  "cannot bridge the missing first symbol for n >= 2, so the "
                  "postcondition fails. If it verified => SPEC-TOO-WEAK (drops the "
                  "first symbol)."},
    {"id": "rival-wrong-separator-first-step", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_SEP,
     "refinement": "PARTIAL-DOMAIN on the join: prepends `dot()` (a Morse signal) instead "
                   "of `sep` on the first fold step (i == n-1), so the join between the "
                   "first two symbols uses the wrong token whenever n >= 2 (correct on a "
                   "single symbol; the precondition guarantees sep != dot(), so this is a "
                   "genuine divergence). Its faithful real patch is a per-word step that "
                   "hardcodes/garbles the join token at one position; under it "
                   "`encode_morse('12345')` emits '.----...---|...' (a '.' instead of '|' "
                   "between the 1st and 2nd symbols), so the F2P exact-string assertion "
                   "FAILS. It would NOT resolve.",
     "rationale": "Rejection source: (E3) — encoded_seq interleaves PSeq(sep) at EVERY "
                  "adjacent pair, so substituting dot() at one step makes "
                  "ToSeq(result) != encoded_seq(...) and the fold invariant "
                  "ToSeq(result) == encoded_seq(ToSeq(msg).drop(i), sep) cannot be "
                  "re-established after that step. If it verified => SPEC-TOO-WEAK (the "
                  "separator is unpinned on a sub-domain)."},
]

# No @ContractOnly axioms / A-consumed callees in this bundle (meta.axioms == []).
# The sole deep model `morse_of` (A-reference) is validated == the real char_morse
# table by axiom_check.py / G-AX out-of-band; there is no Requires-domain to fuzz
# and no caller-reachable callee input to contain. See module docstring.
AXIOM_TESTS = []
