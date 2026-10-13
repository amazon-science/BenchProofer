#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-11445 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type, via the mapping.md bijection
              (`List (List Char)` ↔ list of source lines, char ↔ `ord ch`). The
              per-line classifier `isMetadataLine` (an A-reference deep model)
              and the counting `while` loop are transliterated; the count is
              `countLeadingMetadataLines`.
  * ORACLE  — `patch.diff`'s behaviour: the patched `sphinx.util.rst`'s
              `prepend_prolog` applied at base_commit (the real correctness
              oracle, G-RESOLVE). We run it on a `StringList`, then recover the
              leading count `pos` it used (the number of original lines kept
              ahead of the inserted prolog block).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + docutils +
sphinx only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from docutils.statemachine import StringList

SEED = 11445
N_FUZZ = 100_000
PROLOG = "this is rst_prolog\nhello reST!"   # a 2-line prolog, like the F2P tests


# --- the R/I shadow: Solution.lean isMetadataLine/metaScan + counting loop ---
def _meta_scan(cs, prev):
    while True:
        if not cs:
            return False
        c, rest = cs[0], cs[1:]
        if c == ':':
            if not rest:
                return prev != ' '
            d = rest[0]
            if d == ' ':
                return prev != ' '
            elif d == '`':
                return False
            else:
                cs, prev = rest, c
                continue
        elif c == '\\':
            if not rest:
                return False
            prev = rest[0] if rest else ' '
            cs = rest[1:]
            continue
        else:
            cs, prev = rest, c
            continue


def _is_metadata_line(line):
    cs = list(line)
    if len(cs) < 2:
        return False
    a, b = cs[0], cs[1]
    if a == ':' and b != ':' and b != ' ':
        return _meta_scan(cs[1:], ':')
    return False


def shadow_count(lines):
    """countLeadingMetadataLines (lines.toList) transliterated: the bounded
    forward scan that stops at the first non-metadata line."""
    i = 0
    while i < len(lines) and _is_metadata_line(lines[i]):
        i += 1
    return i


# --- the oracle: the real patched prepend_prolog -----------------------------
def oracle_count(lines):
    """patch.diff's behaviour. Run the real patched prepend_prolog on a copy of
    `lines` and recover the leading count it used: the number of original
    source lines kept ahead of the inserted <rst_prolog> block."""
    from sphinx.util.rst import prepend_prolog  # patched: FIELD_NAME_RE classifier
    sl = StringList(list(lines), 'dummy.rst')
    prepend_prolog(sl, PROLOG)
    items = list(sl.xitems())
    try:
        idx = next(i for i, (src, ln, txt) in enumerate(items)
                   if src == '<rst_prolog>')
    except StopIteration:
        # prolog non-empty ⇒ always inserted; this should not happen.
        return -1
    # original lines preserved before the insertion block (the <generated>
    # blank inserted when pos>0 is sourced '<generated>', so it is excluded).
    return sum(1 for (src, ln, txt) in items[:idx] if src == 'dummy.rst')


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) — incl. the exact F2P-test bodies
    yield [':title: test of SphinxFileInput', ':author: Sphinx team', '',
           ':mod:`foo`', '----------', '', 'hello']
    yield [':mod:`foo`', '-' * 10, '', 'hello']
    yield [':a: b', ':c: d', 'rest']
    yield ['plain', 'more']
    yield [':a:`x`', 'next']
    yield []
    yield ['']
    yield [':title: x']
    yield [':mod:`foo`']
    yield [':a: 1', ':b: 2', ':c: 3']

    line_alphabet = list(":\\` abcXYZ._0123") + ["é"]
    for _ in range(n):
        nlines = rng.randint(0, 6)
        lines = []
        for _ in range(nlines):
            k = rng.randint(0, 14)
            lines.append("".join(rng.choice(line_alphabet) for _ in range(k)))
        yield lines


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for lines in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_count(lines)
        oracle = oracle_count(lines)
        if shadow != oracle:
            disagreements.append((lines, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lines, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (lines, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of countLeadingMetadataLines agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
