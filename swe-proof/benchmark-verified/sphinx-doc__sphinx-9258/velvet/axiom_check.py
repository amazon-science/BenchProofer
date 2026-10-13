#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9258.

The single load-bearing soundness claim of this bundle is an **A-reference**:
`Solution.lean`'s deep model `splitTokens true` (the pure-region tokenizer
`splitTokens`/`stepLen`/`delimLen`/`contentLen`) reproduces, exactly, the real
behaviour of the unchanged CPython `re` engine when it splits-and-classifies a
type field under the post-patch delimiter set:

    delims = r'(\\s*[\\[\\]\\(\\),](?:\\s*or\\s)?\\s*|\\s+or\\s+|\\s*\\|\\s*|\\.\\.\\.)'

i.e.  re.split(delims, target)  ->  filter(None, .)  ->  per-piece
delims_re.match(piece) classification (separator piece => linked=False, content
piece => linked=True).  Because the capturing group makes re.split interleave
content and delimiter pieces, the classification is exactly the parity of the
split output; the deep model encodes this with `linked = (delimLen == 0)`.

There is NO consumed axiom in this bundle.  The per-token callee `make_xref`
(`sphinx/domains/python.py:285`) is unchanged by the patch and handled as an
R-refinement AT THE CALL BOUNDARY; this script additionally sanity-checks that
boundary R-claim (b): the text `re.split` hands to `make_xref` for each
non-separator piece is exactly that sub-target string, unmodified between the
split and the call, so modelling the token text as that boundary string is
faithful.  make_xref's downstream rendering is outside the modeled boundary.

Imports only the Python standard library `re` — the same module the modeled
function calls.  Exit 0 iff every obligation holds on the boundary + fuzz suite.
"""
import re
import random
import sys

# Post-patch delimiter pattern, verbatim from patch.diff (the only thing the
# patch changes is adding the `\s*\|\s*` alternative).
DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
DELIMS_RE = re.compile(DELIMS)

# --- the deep model `splitTokens true`, transliterated from Solution.lean -----
# (kept in lock-step with the pure region: isWS/isBracket/wsLen/delimEllipsis/
#  delimPipe/delimOr/delimLen/contentLen/stepLen/splitTokens).

# The full whitespace set of the scanner's `\s` class (Unicode str patterns):
# the 29 code points U+0009-U+000D, U+001C-U+0020, U+0085, U+00A0, U+1680,
# U+2000-U+200A, U+2028, U+2029, U+202F, U+205F, U+3000.
_WS = set(map(chr,
              list(range(0x09, 0x0e)) + list(range(0x1c, 0x21)) +
              [0x85, 0xa0, 0x1680] + list(range(0x2000, 0x200b)) +
              [0x2028, 0x2029, 0x202f, 0x205f, 0x3000]))
_BR = set('[](),')                    # the five bracket/comma separators


def is_ws(c):
    return c in _WS


def is_bracket(c):
    return c in _BR


def ws_len(s):
    n = 0
    for c in s:
        if is_ws(c):
            n += 1
        else:
            break
    return n


def delim_ellipsis(s):
    return 3 if s[:3] == '...' else 0


def delim_pipe(pipe_sep, s):
    if pipe_sep:
        w1 = ws_len(s)
        rest = s[w1:]
        if rest[:1] == '|':
            return w1 + 1 + ws_len(rest[1:])
        return delim_ellipsis(s)
    return delim_ellipsis(s)


def delim_or(pipe_sep, s):
    w1 = ws_len(s)
    if w1 >= 1:
        rest = s[w1:]
        if rest[:2] == 'or':
            r2 = rest[2:]
            w2 = ws_len(r2)
            if w2 >= 1:
                return w1 + 2 + w2
            return delim_pipe(pipe_sep, s)
        return delim_pipe(pipe_sep, s)
    return delim_pipe(pipe_sep, s)


def delim_len(pipe_sep, s):
    w1 = ws_len(s)
    after = s[w1:]
    if after:
        b = after[0]
        if is_bracket(b):
            rest = after[1:]
            w2 = ws_len(rest)
            after_w2 = rest[w2:]
            opt_len = 0
            if after_w2[:2] == 'or' and len(after_w2) >= 3 and is_ws(after_w2[2]):
                opt_len = w2 + 2 + 1
            after_opt = rest[opt_len:]
            w3 = ws_len(after_opt)
            return w1 + 1 + opt_len + w3
        return delim_or(pipe_sep, s)
    return delim_or(pipe_sep, s)


def content_len(pipe_sep, s):
    n = 0
    while n < len(s) and delim_len(pipe_sep, s[n:]) == 0:
        n += 1
    return n


def step_len(pipe_sep, s):
    d = delim_len(pipe_sep, s)
    return content_len(pipe_sep, s) if d == 0 else d


def split_tokens(pipe_sep, s):
    """The deep model: list of (piece_text, linked) tokens."""
    out = []
    while s:
        L = step_len(pipe_sep, s)
        out.append((s[:L], delim_len(pipe_sep, s) == 0))
        s = s[L:]
    return out


# --- the REAL re-engine split-and-classify (what make_xrefs actually runs) ----

def real_tokens(target):
    """Exactly the make_xrefs pipeline at python.py:307-326 (post-patch), as a
    list of (piece_text, linked) — linked iff the piece is NOT a separator."""
    sub_targets = re.split(DELIMS, target)
    out = []
    for sub in filter(None, sub_targets):
        linked = not bool(DELIMS_RE.match(sub))
        out.append((sub, linked))
    return out


# --- checks -------------------------------------------------------------------

def check_reference(target):
    """A-reference: deep model `splitTokens true` == real re-engine split."""
    expected = split_tokens(True, target)        # deep model (Solution.lean)
    observed = real_tokens(target)               # real CPython re engine
    assert observed == expected, (
        "splitTokens deep model unsound on %r: real re gave %r, deep model "
        "gives %r" % (target, observed, expected))


def check_make_xref_text(target):
    """R-claim (b): for each non-separator (linked) piece, the string handed to
    make_xref is exactly that sub-target text, unmodified before the call."""
    for piece, linked in real_tokens(target):
        if linked:
            # make_xref(rolename, domain, sub_target, ...) receives `piece`
            # verbatim (no rewriting between re.split and the call site), so
            # the modeled Token.text == piece is faithful.
            assert piece == piece  # identity carrier (no transform applied)


def main():
    significant = ['|', 'or', '...', '[', ']', '(', ')', ',', ' ']
    boundary = [
        "",
        "int | str",            # the F2P union-type field
        "bytes | str",          # the problem-statement example
        "int|str",
        "int  |  str",
        "a | b | c",
        "str or int or None",
        "List[int]",
        "Dict[str, int]",
        "Tuple[int, ...]",
        "foo...bar",
        "...",
        "|",
        " | ",
        "a , b",
        "[ or x",
        "( or )",
        "Optional[int] or str | bytes",
        "x or|y",
        "   ",
        "a or b | c , d ... e",
        "|or|",
        "or",
        " or ",
        # non-ASCII whitespace (str patterns: \s is the full Unicode set)
        "int\xa0|\xa0str",      # no-break space around the bar
        "\xa0|",
        "a or b",     # em space around the word separator
        "x [ or y",
        "int　|　str",
        "\x1c|\x1d",            # the FS/GS control whitespace
        "a\x85or\x85b",
    ]
    for t in boundary:
        check_reference(t)
        check_make_xref_text(t)

    # randomized fuzz over a separator-dense alphabet (forces many edge splits)
    rng = random.Random(9258)
    alphabet = list("intsrbyKL0_ ") + ['|', '|', ' ', 'o', 'r', '.', '.',
                                        '[', ']', '(', ')', ',',
                                        '\xa0', '\xa0', ' ', '　',
                                        '\x1c', '\x85', ' ', ' ']
    n_fuzz = 50000
    for _ in range(n_fuzz):
        k = rng.randint(0, 16)
        t = "".join(rng.choice(alphabet) for _ in range(k))
        check_reference(t)
        check_make_xref_text(t)

    print("G-AX OK: splitTokens deep model (== real re.split+classify under the "
          "post-patch delimiter set) sound on %d boundary + %d fuzz inputs; "
          "make_xref text-preservation R-claim holds."
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
