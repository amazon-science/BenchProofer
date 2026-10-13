#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8621 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the forward
              `kbdSplit` scan over `splitParts` / `sepLen` / `stepLen` /
              `lastFlank`) transliterated to Python over the *real* repo type
              (`str`), via the mapping.md bijection (`List Char` ↔ `str`,
              `Char.ofNat (ord ch)` ↔ ch). There are NO A-tagged callees in the
              impl region, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `KeyboardTransform.pattern.split(text)` at base_commit (the real
              correctness oracle, G-RESOLVE). The patched `pattern` is the
              segmentation the issue is about; `run()` consumes its result
              positionally, so equality of the split list is equality of the
              produced kbd segmentation.

They must agree on EVERY input: the contract is total over `List Char`, so the
generator is total too. In particular the generator DOES emit whitespace (all 29
code points of the scanner's whitespace class, including the line feed and the
non-ASCII spaces), because a whitespace RUN is one of the two separator forms and
whether a run is one separator or several — and whether a line feed can flank one
— is observable in the segmentation the renderer consumes. A generator that
declined to emit whitespace would make a zero-disagreement result vacuous over
exactly the sub-domain where the two sides are hardest to keep in step.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. Runs in-container, stdlib only. Seed pinned (mapping.md §4).
"""
import itertools
import random
import re
import sys

SEED = 8621
N_FUZZ = 100_000

_SEP = set("-+^")

# The scanner's whitespace class: the 29 code points `\s` matches for `str`.
_BLANK = frozenset(
    list(range(0x9, 0xE)) + list(range(0x1C, 0x21))
    + [0x85, 0xA0, 0x1680, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]
    + list(range(0x2000, 0x200B)))


# --- the R/I shadow: Solution.lean kbdSplit/splitParts, transliterated -------
def _is_blank(c):
    return ord(c) in _BLANK


def _is_flank(c):
    """isFlank: every character except the line feed counts as a key character
    flanking a separator."""
    return c != "\n"


def _blank_run(s):
    n = 0
    for c in s:
        if not _is_blank(c):
            break
        n += 1
    return n


def _gap_fit(rest, n):
    """gapFit: trim a candidate separator of length n to the longest prefix still
    followed by a flanking key character; 0 if none is."""
    while n > 0:
        tail = rest[n:]
        if tail and _is_flank(tail[0]):
            return n
        n -= 1
    return 0


def _sep_len(left_ok, rest):
    """sepLen: length of the separator at the front of `rest`, or 0."""
    if not rest or not left_ok:
        return 0
    c = rest[0]
    if c in _SEP:
        return _gap_fit(rest, 1)
    if _is_blank(c):
        return _gap_fit(rest, _blank_run(rest))
    return 0


def _step_len(left_ok, rest):
    s = _sep_len(left_ok, rest)
    return 1 if s == 0 else s


def _last_flank(s):
    return _is_flank(s[-1]) if s else False


def shadow_split(text):
    """splitParts false [] (text.toList), transliterated to a list of str.

    Forward cursor scan: at each step either the separator run at the front (a
    single connector, or a maximal whitespace run — recognized only with a
    flanking key character on both sides after trimming) or one key character."""
    acc = []
    cur = ""
    left_ok = False
    rest = text
    while rest:
        L = _step_len(left_ok, rest)
        piece = rest[:L]
        if _sep_len(left_ok, rest) == 0:
            cur = cur + piece
        else:
            acc.append(cur)
            acc.append(piece)
            cur = ""
        left_ok = _last_flank(piece)
        rest = rest[L:]
    acc.append(cur)
    return acc


def oracle_split(text):
    """patch.diff's behaviour: the patched KeyboardTransform.pattern.split.
    Imported from the repo at base_commit with the gold patch applied (the
    harness applies patch.diff before this runs); fall back to compiling the
    patched pattern directly if the import is unavailable."""
    try:
        from sphinx.builders.html.transforms import KeyboardTransform
        pattern = KeyboardTransform.pattern
    except Exception:
        pattern = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')
    return pattern.split(text)


def fuzz_inputs(n, rng):
    # boundary cases first (the bug, both F2P inputs, and the P2P inputs whose
    # separator is whitespace rather than a connector)
    for s in ("", "-", "+", "^", "a", "ab", "Alt+^", "Shift-+", "Control+X",
              "Control-x", "--", "a-", "-a", "a^", "^a", "a--b", "a-+b", "+++",
              "a+b+c", "space", "M-x  M-s", "a b", "a  b", "a   b", " a", "a ",
              "  ", " ", "\n", "a\n", "\na", "a\nb", "a-\n", "\n-a", "a\n-b",
              "a \n b", "a-\n-b", "\t", "a\tb", "a \t b", "a b",
              "a  b", "a　b", "a \n", "\n \na"):
        yield s
    # exhaustive over a small alphabet that includes the separator forms, the
    # line feed (the one non-flanking character), and an ordinary key character
    small = "a-+^ \n"
    for k in range(0, 5):
        for t in itertools.product(small, repeat=k):
            yield "".join(t)
    # total-domain fuzz: keystroke chars, the three connectors, and whitespace
    # drawn from the WHOLE 29-code-point class (not just the ASCII space), so the
    # non-ASCII spaces and the line feed are really exercised.
    blanks = [chr(o) for o in sorted(_BLANK)]
    alphabet = list("abAZ09xX") + list("-+^") + blanks
    heavy = list("ab-+^") + [" ", " ", "\n", "\t"]
    for i in range(n):
        # alternate the two generators so runs of whitespace occur often enough
        # to exercise maximal munch, not just isolated whitespace characters
        alpha = heavy if i % 2 else alphabet
        k = rng.randint(0, 12)
        yield "".join(rng.choice(alpha) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_split(s)
        oracle = oracle_split(s)
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
    print("G-CONF OK: R/I shadow of kbdSplit agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
