#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9258.

This bundle consumes NO `@ContractOnly` axiom: the behaviour the change
introduces — a bar-separated type specification is tokenised into one
cross-reference per named type, interleaved with literal separators — is
modelled DEEPLY by the pure `rendered` fold in model.py (and by its kind
projection `marks`, which is what `split_render` is obliged to return). G-AX
validates those deep models (the A-reference) against the REAL tokeniser the
patched code uses:

    delims = r'(\\s*[\\[\\]\\(\\),](?:\\s*or\\s)?\\s*|\\s+or\\s+|\\s*\\|\\s*|\\.\\.\\.)'
    delims_re = re.compile(delims)
    sub_targets = re.split(delims, target)
    for sub_target in filter(None, sub_targets):
        if delims_re.match(sub_target): -> literal separator node   (is_xref False)
        else:                           -> cross-reference node      (is_xref True)

i.e. each non-empty split piece becomes ONE rendered node, whose kind is
`not delims_re.match(piece)` (True = cross-reference) and whose carried text is
the piece VERBATIM.

TWO deep models are validated against that, at two strengths.

(1) `rendered(s, 0)` -- the whole node stream, over the WHOLE input domain, with
    NO restriction: node count, per-node kind AND per-node exact text, encoded as
    `<carried code points> <kind marker>` per node (-1 cross-reference, -2
    literal separator) closed by -3. This is the A-reference for
    `render_nodes`'s postcondition AND, through its kind projection `marks`, for
    `split_render`'s. It is checked here against the real tokenisation of every
    generated input, well-formed or not, so no input class is left unvalidated. Its separator vocabulary is `sep_end`: the padded bar, the
    bracket/comma group with its optional `or`, the whitespace-bounded `or` and
    the three-dot run, tried in that order -- the same order the alternation is
    written in, which is what fixes each token's extent.

(2) `kinds(s, 0)` -- the bar-only kind reading, on the EXACTNESS REGION marked by
    `well_formed` in model.py, which has TWO clauses —
(a) every bar-separated segment names a non-empty type, AND (b) the spec uses
the vertical bar as its ONLY separator (no `[ ] ( ) , ...` and no
whitespace-bounded `or`). On that region the raw-bar split with strict
alternation equals the real regex tokenisation; off it, it does not. `well_formed`
is NOT a precondition of anything: `split_render`'s postcondition is the total
`marks` fold (the kind projection of `rendered`, so it is covered at full strength
by (1) here and measured directly against the called function by G-CONF). `kinds`
is retained as this validated bar-structure reading, which is why the region it is
exact on is still measured here.

CRITICAL (the prior version of this check was unsound — it masked a real defect
by drawing fuzz inputs from a strict subset of the region, an alphabet
that excluded exactly the other delimiters): the fuzzer below draws from the
FULL delimiter alphabet `{ type-name chars, space, | , [ ] ( ) , . o r }`, so it
actually exercises the `well_formed` boundary. Inputs that hit any other
delimiter are correctly rejected by `well_formed` (clause b) and skipped for the
bar-only comparison while still being checked against (1); the remaining
well-formed inputs are checked against both. Exit 0 iff every observation
matches the deep model.

The check imports only the standard-library `re` module and reproduces the
patched regex verbatim (the very pattern the gold patch installs).
"""
import random
import re
import sys

# The delimiter regex EXACTLY as installed by the gold patch (sphinx/domains/
# python.py, make_xrefs). The change adds the `\s*\|\s*` alternative.
DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
DELIMS_RE = re.compile(DELIMS)

BAR = ord('|')
SPACE = ord(' ')
DOT = ord('.')
O = ord('o')
R = ord('r')
BRACKETS = {ord('['), ord(']'), ord('('), ord(')'), ord(',')}


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def is_space(c):
    """model.py `is_space`: a whitespace code point. The FULL whitespace set the
    delimiter pattern's `\s` matches, NOT merely the ASCII space 32 — the guard
    below pins this transcription to the regex engine's own class."""
    return ((9 <= c <= 13) or (28 <= c <= 32) or c == 133 or c == 160 or
            c == 5760 or (8192 <= c <= 8202) or c == 8232 or c == 8233 or
            c == 8239 or c == 8287 or c == 12288)


_WS_BAD = [c for c in range(0x110000)
           if bool(re.match(r'\s', chr(c))) != is_space(c)]
assert not _WS_BAD, (
    "is_space transcription != the regex \\s class at %r; this check would "
    "validate a different model than model.py's" % (_WS_BAD[:8],))


def first_bar(s, i):
    """model.py `first_bar`: index of the first '|' at/after i, clamped."""
    while i < len(s) and s[i] != BAR:
        i += 1
    return i


def model_kinds(codepoints, i=0):
    """Reference of model.py's deep model `kinds(s, i)`: the strictly-
    alternating kind sequence (True = cross-reference, False = literal
    separator) for the raw-bar split of s[i:]."""
    out = []
    while True:
        p = first_bar(codepoints, i)
        out.append(True)            # cross-reference for the current segment
        if p >= len(codepoints):
            break
        out.append(False)           # literal separator for the bar
        i = p + 1
    return out


def seg_text_nonempty(codepoints, i, j):
    """True iff the trimmed segment codepoints[i:j] is non-empty (has a non-
    whitespace code point) — mirrors model.py `len(seg_text(...)) > 0`, whose
    strip_left/strip_right trim ANY whitespace, not only the ASCII space."""
    a, b = i, j
    while a < b and is_space(codepoints[a]):
        a += 1
    while b > a and is_space(codepoints[b - 1]):
        b -= 1
    return b > a


def no_other_sep(codepoints, i=0):
    """model.py `no_other_sep(s, i)`: the suffix s[i:] contains none of the
    non-bar separator triggers — no `[ ] ( ) ,`, no `...` run, no whitespace-
    bounded `or` (bounded by ANY whitespace, per model.py's `is_space` guard) —
    so the vertical bar is the only delimiter. Byte-for-byte the
    same position-wise scan as the Nagini `@Pure` `no_other_sep`."""
    n = len(codepoints)
    x = i
    while x < n:
        c = codepoints[x]
        if c in BRACKETS:
            return False
        if (c == DOT and x + 2 < n and codepoints[x + 1] == DOT and
                codepoints[x + 2] == DOT):
            return False
        if (is_space(c) and x + 3 < n and codepoints[x + 1] == O and
                codepoints[x + 2] == R and is_space(codepoints[x + 3])):
            return False
        x += 1
    return True


def well_formed(codepoints, i=0):
    """model.py `well_formed(s, i)`: (a) every bar-separated segment of s[i:]
    names a non-empty type (some non-whitespace character), AND (b)
    `no_other_sep` (the bar is the only separator). The region on which the
    bar-only `kinds` reading is EXACT -- a precondition of nothing."""
    if not no_other_sep(codepoints, i):
        return False
    while True:
        p = first_bar(codepoints, i)
        if not seg_text_nonempty(codepoints, i, p):
            return False
        if p >= len(codepoints):
            return True
        i = p + 1


# --- the real tokeniser (the patched make_xrefs splitting/classification) -----

def real_kinds(target):
    """The REAL rendered-node kind sequence the patched make_xrefs produces:
    split on the delimiter regex, drop empty pieces, each remaining piece is a
    literal separator iff it matches the delimiter regex, else a cross-ref."""
    pieces = [p for p in re.split(DELIMS, target) if p]
    return [not bool(DELIMS_RE.match(p)) for p in pieces]


def strip_left_cps(s, i, j):
    """model.py `strip_left`: first index in [i, j) whose code point is not
    whitespace, or j if they all are."""
    while i < j and i < len(s) and is_space(s[i]):
        i += 1
    return i


def sep_end_cps(s, i):
    """model.py `sep_end`: one past the end of the separator token that starts at
    `i`, or -1 if none does. The four alternatives are tried in the SAME order
    the delimiter pattern writes them, since the first one that applies fixes the
    token's extent."""
    n = len(s)
    a = strip_left_cps(s, i, n)
    if a < n and s[a] in BRACKETS:
        c = strip_left_cps(s, a + 1, n)
        if (c + 2 < n and s[c] == O and s[c + 1] == R and
                is_space(s[c + 2])):
            return strip_left_cps(s, c + 3, n)
        return strip_left_cps(s, a + 1, n)
    if (i < n and is_space(s[i]) and a + 2 < n and s[a] == O and
            s[a + 1] == R and is_space(s[a + 2])):
        return strip_left_cps(s, a + 2, n)
    if a < n and s[a] == BAR:
        return strip_left_cps(s, a + 1, n)
    if i + 2 < n and s[i] == DOT and s[i + 1] == DOT and s[i + 2] == DOT:
        return i + 3
    return -1


def next_sep_cps(s, i):
    """model.py `next_sep`: the leftmost separator position at or after `i`,
    clamped to len(s)."""
    n = len(s)
    while i < n and sep_end_cps(s, i) < 0:
        i += 1
    return i


def model_rendered(s, i=0):
    """Reference of model.py's deep model `rendered(s, i)`: the whole node
    stream, `<carried code points> <kind marker>` per node (-1 cross-reference,
    -2 literal separator), closed by -3."""
    out = []
    n = len(s)
    while True:
        j = next_sep_cps(s, i)
        if j >= n:
            if i < n:
                out.extend(s[i:n])
                out.append(-1)
            out.append(-3)
            return out
        e = sep_end_cps(s, j)
        if j > i:
            out.extend(s[i:j])
            out.append(-1)
        out.extend(s[j:e])
        out.append(-2)
        i = e


def real_stream(target):
    """The REAL node stream the patched tokenisation produces, in the deep
    model's encoding: split on the delimiter regex, drop empty pieces, and emit
    each remaining piece's code points VERBATIM followed by -2 when the piece
    matches the delimiter regex (a literal separator node) or -1 when it does not
    (a cross-reference node); close with -3."""
    out = []
    for piece in re.split(DELIMS, target):
        if not piece:
            continue
        out.extend(ord(ch) for ch in piece)
        out.append(-2 if DELIMS_RE.match(piece) else -1)
    out.append(-3)
    return out


# --- the check ----------------------------------------------------------------

_STREAM_CHECKED = [0]


def check_stream(target):
    """UNRESTRICTED: assert the `rendered` deep model == the real tokenisation on
    `target`, whatever shape it has. No domain filter, so a shape that mixes the
    bar with a bracket, comma, `or` or ellipsis is validated too rather than
    skipped."""
    cps = [ord(ch) for ch in target]
    observed = real_stream(target)
    expected = model_rendered(cps)
    assert observed == expected, (
        "rendered deep model unsound on %r: real tokenisation gives the node "
        "stream %r, deep model gives %r" % (target, observed, expected))
    _STREAM_CHECKED[0] += 1


def check(target):
    """Validate BOTH deep models: the node stream unconditionally (this is the
    model `split_render`'s postcondition is stated over, so EVERY input is
    checked at full strength), and the bar-only `kinds` reading on its exactness
    region. Returns True if the `kinds` reading was also checked (well-formed),
    False if only the stream was."""
    check_stream(target)
    cps = [ord(ch) for ch in target]
    if not well_formed(cps):
        return False                     # outside `kinds`' exactness region; skip
                                         # (the stream model above still carried it)
    observed = real_kinds(target)        # real re.split / re.match
    expected = model_kinds(cps)          # deep model `kinds`
    assert observed == expected, (
        "kinds deep model unsound on %r: real tokeniser gave %r, deep model "
        "gives %r" % (target, observed, expected))
    return True


def main():
    # --- boundary cases INSIDE the region (bar-only well-formed specs) -------
    boundary_in = [
        "int | str",                     # the F2P case
        "int|str",
        "bytes | str | None",
        "a | b | c | d",
        "int",                           # single type, no bar
        "SomeClass",
        "a|b",
        "x | y",
        "foo |bar",                      # asymmetric spacing around the bar
        "x| y",
        "List | Dict | Tuple | Set",     # bare names (no brackets) + bars
        "int   |   str",                 # wide spacing
        "mod.Class | other.Class",       # single dots inside dotted names are OK
        "colored | factor",             # embedded 'or' substrings are OK (not ws-bounded)
        "a or",                          # trailing 'or' with no following space: OK
        # Non-ASCII whitespace PADDING a bar is in-domain: the pattern consumes it
        # into the separator exactly as it does an ASCII space, and each segment
        # still names a type.
        "int\t|\tstr",                   # TAB-padded bar
        "a\n|\nb",                       # newline-padded bar
        "x\xa0|\xa0y",                   # NBSP-padded bar
        "int\u3000|\u3000str",           # IDEOGRAPHIC SPACE-padded bar
        "a \t| \tb",                     # mixed-whitespace padding
        "aorb | c",                      # 'or' not whitespace-bounded: not a separator
        "ore\t| int",
    ]
    checked = 0
    for t in boundary_in:
        assert check(t), "well-formed boundary case wrongly rejected: %r" % (t,)
        checked += 1

    # --- boundary cases that MUST fall OUTSIDE the exactness region ----------
    # (these are precisely the inputs the prior, too-broad `well_formed` wrongly
    #  admitted while the bar-only reading disagreed with the real tokeniser.
    #  They are STILL checked at full strength by (1) above -- the node-stream
    #  model, which is what `split_render` is actually obliged to compute.)
    boundary_out = [
        "Tuple[str, ...]",               # brackets, comma, ellipsis
        "Dict[str, str]",                # brackets, comma
        "List[int]",                     # brackets
        "str or int",                    # whitespace-bounded 'or'
        "word or other",
        ",",                             # bare comma
        "...",                           # bare ellipsis
        "a, b",                          # comma separator
        "Optional[int] | str",           # mixes a bracket with a bar
        "abc...def",                     # internal ellipsis
        # An `or` bounded by ANY whitespace is a separator, not part of a name —
        # so these are OUTSIDE the region exactly as space-padded "str or int" is.
        "a\tor\tb",                      # TAB-bounded 'or'
        "int\tor\tstr",
        "a\nor\nb",                      # newline-bounded 'or'
        "x\xa0or\xa0y",                  # NBSP-bounded 'or'
        "a\u3000or\u3000b",              # IDEOGRAPHIC SPACE-bounded 'or'
        "a\x0bor\ror b",
        "a\tor\tb\t|\tc",                # a ws-bounded 'or' alongside a bar
        # A segment of nothing but whitespace names no type: the padding belongs to
        # the separator, so these are OUTSIDE the region as "int|" / " | " are.
        "a|\t", "\t|a", "a|\t|b", "a|\xa0", "\xa0|a", "\x0b|ce\r",
        "\u3000|a", "int\t|\t", "\n|\n",
        # shapes on which the bar-only `kinds` reading is not exact, and which
        # the node-stream model above therefore carries alone:
        "|", " | ", "|int", "int|", "a||b", "", "int | str | ",
        "List[int] | str", "Tuple[int, str] | None", "int or str | bytes",
        "a...b | c", "Dict[str, List[int]]", "( )", ",,,", " or ", "...|...",
    ]
    rejected = 0
    for t in boundary_out:
        assert not check(t), (
            "case outside the exactness region wrongly admitted (the bar-only "
            "reading would be unsound there): %r" % (t,))
        rejected += 1

    # --- randomized fuzz over the FULL DELIMITER ALPHABET --------------------
    # The alphabet now includes every delimiter character ([ ] ( ) , . o r) plus
    # the bar and spaces, so the fuzz actually probes the well_formed boundary
    # (clause b). EVERY draw is checked against the node-stream model; the draws
    # inside the exactness region are checked against the bar-only reading too.
    rng = random.Random(9258)
    # The alphabet includes every delimiter character AND the non-ASCII whitespace
    # the pattern's `\s` matches. Those code points are precisely where a
    # space-only whitespace notion would part company with the real pattern (a
    # TAB-padded `or` still separates; a segment of pure NBSP names no type), so
    # omitting them would make this check unable to fail — it would draw only from
    # the subset on which any such model agrees. (The prior version of this check
    # did exactly that and masked a real defect one layer down.)
    unicode_ws = ["\t", "\n", "\x0b", "\x0c", "\r", "\x1c", "\x1d", "\x1e",
                  "\x1f", "\x85", "\xa0", "\u1680", "\u2000", "\u2001",
                  "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007",
                  "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f",
                  "\u205f", "\u3000"]
    alphabet = list("abcdeFGHIJ_0129") + [
        " ", " ", "|", "[", "]", "(", ")", ",", ".", "o", "r"] + unicode_ws
    fuzzed = 0
    skipped = 0
    attempts = 0
    while fuzzed < 60000 and attempts < 4000000:
        attempts += 1
        n = rng.randint(0, 22)
        t = "".join(rng.choice(alphabet) for _ in range(n))
        if check(t):
            fuzzed += 1
        else:
            skipped += 1

    # --- structured fuzz over the full delimiter alphabet --------------------
    # Join 1..5 random names (some containing brackets/commas/dots/`or` so the
    # generator straddles the region boundary) with bar separators; the stream
    # model is checked on all of them, the bar-only reading on the well-formed
    # ones.
    names = ["int", "str", "bytes", "None", "List", "Dict", "X", "Foo_1", "T2",
             "List[int]", "Dict[str, str]", "Tuple[str, ...]", "a or b",
             "mod.Class", "Optional[int]",
             "a\tor\tb", "x\xa0or\xa0y", "a\u3000or\u3000b", "aorb"]
    # pads straddle the region boundary: "" plus whitespace of several kinds, so
    # some draws pad a bar (well-formed) and others make a segment pure whitespace.
    pads = ["", " ", "  ", "\t", "\n", "\xa0", "\u3000", " \t", "\u2003"]
    structured = 0
    structured_skipped = 0
    for _ in range(60000):
        k = rng.randint(1, 5)
        parts = [rng.choice(names) for _ in range(k)]
        seps = [rng.choice(pads) + "|" + rng.choice(pads) for _ in range(k - 1)]
        t = parts[0]
        for idx in range(k - 1):
            t += seps[idx] + parts[idx + 1]
        if check(t):
            structured += 1
        else:
            structured_skipped += 1

    print("G-AX OK: (1) `rendered` deep model -- the WHOLE node stream, node "
          "count + per-node kind + per-node exact text, and hence the `marks` "
          "kind projection `split_render` is obliged to return -- == the real "
          "re.split/re.match tokenisation on ALL %d generated inputs with NO "
          "domain restriction; (2) the retained bar-only `kinds` reading is "
          "exact on its `well_formed` region and NOT beyond it: %d well-formed "
          "boundary + %d boundary cases outside the region (correctly excluded "
          "by `well_formed`, still carried by (1)) + %d fuzz (%d outside the "
          "region) + %d structured (%d outside it) inputs over the FULL "
          "delimiter alphabet"
          % (_STREAM_CHECKED[0], checked, rejected, fuzzed, skipped,
             structured, structured_skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
