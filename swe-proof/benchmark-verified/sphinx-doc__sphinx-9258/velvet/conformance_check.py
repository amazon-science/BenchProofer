#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9258 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` <-> `str`, `Char.ofNat (ord ch)` <-> ch).
              The impl computes the token stream `out : List Token` by the
              `while` fold over `stepLen true`/`delimLen true`; this is the
              transliteration of the deep model `splitTokens true`
              (the A-reference, modeled as R/I content here, exactly as the
              django exemplar transliterates `escapedSeq`).  Each Token is
              (piece_text, linked).

  * ORACLE  — `patch.diff`'s behaviour: the patched `make_xrefs`
              (`sphinx/domains/python.py:304`) applied at base_commit.  Its
              observable result is the list of result nodes; per node we read
              (astext, is-it-a-link).  make_xrefs is `re.split(delims, target)`
              -> `filter(None, .)` -> per-piece classification by
              `delims_re.match`; a matched piece becomes a verbatim separator
              node (linked=False), an unmatched piece is handed to the callee
              `make_xref` (linked=True).  The modeled observable is taken at
              that call boundary: (the raw piece string handed on, linked) —
              the boundary R-claim validated by G-AX §3.2; make_xref's own
              downstream rendering is outside the boundary.  The unchanged
              `re` engine is the real repo callee, not the deep model; that
              is what isolates the R/I leg.

They must agree on every input.  Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only.  The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.

Coverage note (plan §4.1 honesty): inputs are bounded to length <= 18 over a
separator-dense alphabet (the type-field domain the issue/F2P exercise),
including non-ASCII whitespace code points (NBSP U+00A0, em space U+2003,
ideographic space U+3000, U+001C, U+0085, U+2028, U+202F) so the full-Unicode
whitespace class of the real engine is exercised.  Unbounded tails are not fuzzed;
recorded here so under-coverage is not read as "R/I proven".
"""
import random
import re
import sys

SEED = 9258
N_FUZZ = 100_000

# Post-patch delimiter pattern, verbatim from patch.diff.  Used by the ORACLE
# only (the real unchanged `re` engine), NOT by the shadow.
DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
DELIMS_RE = re.compile(DELIMS)


# --- the R/I shadow: Solution.lean splitTokens/stepLen/delimLen, transliterated
# (kept in lock-step with the pure region of Solution.lean).

# The full whitespace set of the scanner's `\s` class (Unicode str patterns):
# the 29 code points U+0009-U+000D, U+001C-U+0020, U+0085, U+00A0, U+1680,
# U+2000-U+200A, U+2028, U+2029, U+202F, U+205F, U+3000.
_WS = set(map(chr,
              list(range(0x09, 0x0e)) + list(range(0x1c, 0x21)) +
              [0x85, 0xa0, 0x1680] + list(range(0x2000, 0x200b)) +
              [0x2028, 0x2029, 0x202f, 0x205f, 0x3000]))
_BR = set('[](),')


def _ws_len(s):
    n = 0
    for c in s:
        if c in _WS:
            n += 1
        else:
            break
    return n


def _delim_ellipsis(s):
    return 3 if s[:3] == '...' else 0


def _delim_pipe(s):
    # pipeSep = true (the post-patch separator set)
    w1 = _ws_len(s)
    rest = s[w1:]
    if rest[:1] == '|':
        return w1 + 1 + _ws_len(rest[1:])
    return _delim_ellipsis(s)


def _delim_or(s):
    w1 = _ws_len(s)
    if w1 >= 1:
        rest = s[w1:]
        if rest[:2] == 'or':
            r2 = rest[2:]
            w2 = _ws_len(r2)
            if w2 >= 1:
                return w1 + 2 + w2
            return _delim_pipe(s)
        return _delim_pipe(s)
    return _delim_pipe(s)


def _delim_len(s):
    w1 = _ws_len(s)
    after = s[w1:]
    if after:
        b = after[0]
        if b in _BR:
            rest = after[1:]
            w2 = _ws_len(rest)
            after_w2 = rest[w2:]
            opt_len = 0
            if after_w2[:2] == 'or' and len(after_w2) >= 3 and after_w2[2] in _WS:
                opt_len = w2 + 2 + 1
            after_opt = rest[opt_len:]
            w3 = _ws_len(after_opt)
            return w1 + 1 + opt_len + w3
        return _delim_or(s)
    return _delim_or(s)


def _content_len(s):
    n = 0
    while n < len(s) and _delim_len(s[n:]) == 0:
        n += 1
    return n


def _step_len(s):
    d = _delim_len(s)
    return _content_len(s) if d == 0 else d


def shadow_tokens(target):
    """The `while` fold of splitUnionTypeField, transliterated: list of
    (piece_text, linked) Tokens, linked = (delimLen true rest == 0)."""
    out = []
    s = target
    while s:
        L = _step_len(s)
        out.append((s[:L], _delim_len(s) == 0))
        s = s[L:]
    return out


# --- the ORACLE: patch.diff's make_xrefs observable behaviour ----------------

def oracle_tokens(target):
    """patch.diff behaviour of make_xrefs, observed at the split+classify
    boundary as (raw piece string, linked): re.split(delims) -> filter(None)
    -> per-piece classify by delims_re.match.  A matched piece -> verbatim
    separator node (innernode text == piece, linked=False).  An unmatched
    piece -> handed to make_xref(...) as-is (linked=True; the boundary
    R-claim of G-AX §3.2 — downstream rendering is outside the boundary).
    The `re` engine here is the real unchanged repo callee (stdlib `re`),
    not the deep model."""
    sub_targets = re.split(DELIMS, target)
    out = []
    for sub in filter(None, sub_targets):
        linked = not bool(DELIMS_RE.match(sub))
        out.append((sub, linked))
    return out


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the F2P + problem-statement fields
    yield ""
    yield "int | str"
    yield "bytes | str"
    yield "int|str"
    yield "int  |  str"
    yield "a | b | c"
    yield "str or int or None"
    yield "List[int]"
    yield "Dict[str, int]"
    yield "Tuple[int, ...]"
    yield "Optional[int] or str | bytes"
    yield "foo...bar"
    yield "..."
    yield "|"
    yield " | "
    yield "a , b"
    yield "[ or x"
    yield "x or|y"
    yield "|or|"
    yield "a or b | c , d ... e"
    # non-ASCII whitespace (str patterns: \s is the full Unicode set)
    yield "int\xa0|\xa0str"
    yield "\xa0|"
    yield "a or b"
    yield "x [ or y"
    yield "int　|　str"
    yield "\x1c|\x1d"
    yield "a\x85or\x85b"
    alphabet = list("intsrbyKL0_ ") + ['|', '|', ' ', 'o', 'r', '.', '.',
                                       '[', ']', '(', ')', ',',
                                       '\xa0', '\xa0', ' ', '　',
                                       '\x1c', '\x85', ' ', ' ']
    for _ in range(n):
        k = rng.randint(0, 18)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_tokens(s)
        oracle = oracle_tokens(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of splitUnionTypeField agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
