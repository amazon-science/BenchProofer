#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10323 (nagini).

SHADOW: the `# impl-start` / `# impl-end` region of model.py, copied VERBATIM
below with only the contract calls removed (`Requires`, `Ensures`, `Invariant`,
`Assert`, `MustTerminate`) together with the `# invariants-start`/`-end`
markers.  Nothing is restructured, renamed or simplified: the two `while` loops,
the backward fold that builds `trimmed`, the `(emit(lead) + trimmed) +
emit(trail)` concatenation and the second (purely proof-carrying) loop over `j`
all appear here exactly as in the model, in the same order.  The `@Pure` helpers
`trim_block` and `emit` from the model's `# pure-start`/`# pure-end` region are
copied over as plain functions (contracts stripped); `trim_block` is also used as
an auxiliary cross-check on the fold's result, and `emit` is the author-line
PRESENCE rule the shadow executes for real (an empty author line contributes no
line), so this check senses it rather than assuming it.  `trim_block_at` is a
proof lemma whose body is `True`/a recursive call with no computation, so it
carries no observable behaviour.  `PSeq` is realized as an immutable tuple shim
exposing exactly the operations the region uses (`take`, `drop`, `+`, `len`,
`[]`, `==`).

There are NO `@ContractOnly` axioms in this bundle (model.py's axioms region is
empty by construction): the per-line left-margin trim is modelled DEEPLY as
`trim_block`, so every operation the shadow performs is real computation the
model itself performs.  Consequently nothing here is assumed — the pure region
and the impl region are both executed.

ORACLE: the REAL patched repo function named in mapping.md §1 —
`sphinx.directives.code.LiteralIncludeReader.read` (`sphinx/directives/code.py:219`,
the filter pipeline at lines 223-232 whose ordering the gold patch changes).
It is CALLED, not transliterated: the gate applies patch.diff to /testbed before
this script runs and PYTHONPATH=/testbed makes the patched module importable, so
`read()` runs with the fixed filter order (dedent_filter before prepend_filter /
append_filter).  Driving it needs only an include file and an options dict, both
of which we can build in-container, so there is no reason to reimplement it.
Its unchanged sub-callees (`read_file`, `dedent_filter` -> `dedent_lines`,
`prepend_filter`, `append_filter` — mapping.md §1 / §3) therefore also run for
real; the deep model `trim_block` is checked against them here as well as by
G-AX.  Because the oracle is the whole `read()`, this check senses the gold
reordering directly: run against the PRE-patch pipeline it fails on the F2P
boundary case (the oracle then reports the trimmed `ass Foo:` / `comment`).

TYPE BRIDGE (mapping.md §2, inverted).  A model line is its CONTENT as a
`PSeq[int]` of Unicode code points with the trailing newline factored out as an
implicit separator; a repo line is `content + '\n'` (a `str`).  So:

    to_line(s)   : str            -> PSeq[int]        PSeq(*map(ord, s))
    from_line(p) : PSeq[int]      -> str              ''.join(map(chr, p))
    render(b)    : PSeq[PSeq[int]]-> str              ''.join(from_line(c) + '\n'
                                                              for c in b)

Inputs are generated on the CONCRETE side (str content lines, str lead/trail,
int n) and lifted into the carrier for the shadow, which keeps every generated
input inside the model's `Requires` by construction.  The included block is
written to an include file as `''.join(content + '\n')`; `read_file` recovers it
line-for-line via `splitlines(True)` (no `tab-width` option is set), so the
generator's alphabet excludes every character `str.splitlines` treats as a line
boundary ('\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', ' ',
' ') — with any of those the *file* would no longer denote the generated
block and the harness, not the model, would be at fault.  The shadow's rendered
block is compared to the oracle's returned content string exactly.

INPUT DOMAIN.  Exactly model.py's `Requires`: `n >= 0`.  NOTHING is required of
the author lines, so the domain includes every combination of author-line
presence and absence and the zero-width trim, and the generators below cover all
four presence combinations plus `n == 0`.  The bridge to the real function is the
option dict: an ABSENT author line is the empty string, which is exactly what
makes `read()`'s guarded author filters (`if prepend:` / `if append:`) contribute
no line, so the model's presence rule (`emit`) is checked against the real
filters rather than assumed.  The regime where both author lines are present and
the trim width is positive is the one the gold reordering fixes (the F2P shape);
the regimes where an author line is ABSENT are the ones the repo's own
dedent-only tests exercise, and they are in-domain here for the same reason they
are in-domain in the model — the trim reaches the included text either way.  The
space is INFINITE (arbitrary content lines), so: boundary cases first — the exact
F2P shape (`lines 9-11` of the fixture, `dedent: 2`, `prepend: 'class Foo:'`,
`append: '# comment'`), the original bug report's XML snippet with a
pre-indented opening tag, the dedent-only shapes with NEITHER author line and
with only one of the two, `n == 0` with and without author lines, an empty
included block and a singleton block (the two sides of the `while i > 0` /
`while j < len(included)` branch), a lead/trail that is pure indentation,
over-long trim widths, exact-width trims and the empty-line/newline special case
— then seeded fuzz to fill the count.

>= 1e5 Requires-satisfying inputs: 39 boundary + 100000 fuzz = 100039.
Pinned fuzz seed: 10323 (recorded in mapping.md under `## G-CONF`).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1.  stdlib + the repo's own sphinx only.
"""
import json
import logging
import os
import random
import sys
import tempfile

# `dedent_lines` logs "non-whitespace stripped by dedent" when the trim eats
# non-blank text. It is a pure side effect that does not alter the returned
# lines (mapping.md §3.1), and it is in-domain here, so silence it to keep the
# verdict line the last stdout line.
logging.disable(logging.CRITICAL)

from sphinx.directives.code import LiteralIncludeReader   # noqa: E402  ORACLE

SEED = 10323
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- @Pure helper from model.py's pure region, contracts stripped ------------

def trim_block(lines, n):
    """model.py `trim_block`, verbatim minus Requires/Ensures."""
    if len(lines) == 0:
        return PSeq(PSeq(0).take(0)).take(0)
    return PSeq(lines[0].drop(n)) + trim_block(lines.drop(1), n)


def emit(line):
    """model.py `emit`, verbatim minus Ensures: the contribution of ONE author
    line — the single-line block holding it verbatim when it has content, and NO
    line at all when it is empty."""
    if len(line) == 0:
        return PSeq(line).take(0)
    return PSeq(line)


# --- SHADOW: the impl region of model.py, verbatim, contracts stripped -------

def assemble(included, lead, trail, n):
    # impl-start
    # Margin trim first — over the included text only, and unconditionally.
    # Build the trimmed block by a backward fold matching `trim_block`.
    trimmed = PSeq()  # type: PSeq[PSeq[int]]
    i = len(included)
    while i > 0:
        trimmed = PSeq(included[i - 1].drop(n)) + trimmed
        i = i - 1
    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)
    # and only when it has content.
    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]
    # Discharge the per-included-line characterization of the trim via the
    # lemma, index by index, in both author-line regimes.
    j = 0
    while j < len(included):
        j = j + 1
    return result
    # impl-end


# --- type bridge (mapping.md §2, inverted) ----------------------------------

def to_line(s):
    """Concrete repo line content (str) -> model carrier (PSeq[int])."""
    return PSeq(*[ord(c) for c in s])


def to_block(contents):
    """List[str] of line contents -> PSeq[PSeq[int]]."""
    return PSeq(*[to_line(c) for c in contents])


def from_line(p):
    """Model carrier (PSeq[int]) -> repo line content (str)."""
    return "".join(chr(p[k]) for k in range(len(p)))


def render(block):
    """PSeq[PSeq[int]] -> the repo text: each line's content plus the implicit
    '\\n' separator, i.e. what `''.join(lines)` returns."""
    return "".join(from_line(block[k]) + "\n" for k in range(len(block)))


# --- ORACLE: the real patched LiteralIncludeReader.read() -------------------

class _Config:
    source_encoding = "utf-8"


_ORACLE_FD, _ORACLE_PATH = tempfile.mkstemp(suffix=".inc")
os.close(_ORACLE_FD)


def oracle(included, lead, trail, n):
    """Call the REAL patched `LiteralIncludeReader.read` (mapping.md §1) with the
    included block on disk and dedent/prepend/append set to n/lead/trail."""
    with open(_ORACLE_PATH, "w", encoding="utf-8", newline="") as f:
        f.write("".join(c + "\n" for c in included))
    reader = LiteralIncludeReader(
        _ORACLE_PATH, {"dedent": n, "prepend": lead, "append": trail},
        _Config())
    content, _nlines = reader.read()
    return content


# --- the differential check -------------------------------------------------

_BAD = set("\n\r\v\f\x1c\x1d\x1e\x85  ")


def in_requires(included, lead, trail, n):
    """model.py's Requires: n >= 0 (nothing is required of the author lines, so
    either or both may be absent == the empty string). Also rejects any character
    that would make the include FILE stop denoting the generated block (a harness
    precondition, not a model one)."""
    if not n >= 0:
        return False
    for s in list(included) + [lead, trail]:
        if any(ch in _BAD for ch in s):
            return False
    return True


def check(included, lead, trail, n, counters):
    assert in_requires(included, lead, trail, n), \
        "generated input outside Requires: %r %r %r %r" % (included, lead, trail, n)
    block = to_block(included)
    shadow_block = assemble(block, to_line(lead), to_line(trail), n)
    # Auxiliary: the fold really did compute the pure region's `trim_block`, and
    # the author lines entered through the pure presence rule `emit`.
    if shadow_block != (emit(to_line(lead)) + trim_block(block, n)) + emit(to_line(trail)):
        print("DISAGREE (shadow fold != pure trim_block): included=%r lead=%r "
              "trail=%r n=%r" % (included, lead, trail, n))
        return False
    got_shadow = render(shadow_block)
    got_oracle = oracle(included, lead, trail, n)
    counters["checked"] += 1
    if got_shadow != got_oracle:
        print("DISAGREE: included=%r lead=%r trail=%r n=%r" % (included, lead, trail, n))
        print("  shadow=%r" % (got_shadow,))
        print("  oracle=%r" % (got_oracle,))
        return False
    return True


BOUNDARY = [
    # The exact F2P shape: fixture literal.inc lines 9-11, dedent 2, a class
    # header prepended and a comment appended. Both author lines begin with
    # content the trim WOULD alter only if it reached them.
    (["    def baz():", "        pass", ""], "class Foo:", "# comment", 2),
    # The original bug report: an XML snippet whose prepended opening tag is
    # already indented and must survive verbatim.
    (["        <groupId>x</groupId>", "      </plugin>"], "      <plugin>", "# end", 1),
    # `while i > 0` NOT taken / `while j < len(included)` NOT taken: empty block.
    ([], "L", "T", 1),
    ([], "  indented lead", "  indented trail", 4),
    # Both loops taken exactly once: singleton block.
    (["only"], "L", "T", 1),
    (["  x"], "lead", "trail", 5),          # over-long trim (line shorter than n)
    ([""], "p", "a", 1),                    # single EMPTY line (newline special case)
    (["  "], "p", "a", 4),                  # whitespace-only line, over-trimmed
    (["  "], "p", "a", 2),                  # whitespace-only line, exact trim
    # Multi-line blocks.
    (["    a", "    b"], "L", "T", 4),      # exact-width trim
    (["    a", "      b", ""], "HEAD", "TAIL", 2),
    (["        deep", "    less"], "lead", "trail", 8),
    (["a", "b", "c", "d", "e", "f", "g", "h"], "L", "T", 1),   # long block
    # Author lines that are pure indentation (trim would empty them).
    ([" a"], " ", " ", 1),
    (["  a"], "   ", "    ", 3),
    # n at the low boundary and well past every line length.
    (["x"], "y", "z", 1),
    (["x"], "y", "z", 100),
    (["", "", ""], "L", "T", 1),            # all-empty lines
    (["\ta", "\t\tb"], "\tlead", "\ttrail", 1),   # tabs (no tab-width option)
    (["# comment after Bar class definition"], "class Bar:", "def bar(): pass", 2),
    (["  def baz():", "      pass", ""], "class Foo:", "# comment", 2),  # already-trimmed
    (["non-whitespace"], "L", "T", 4),      # triggers the dedent warning path
    (["a b c", " d e f "], "  keep me", "  keep me too", 2),
    (["üöä", "  中文"], "élead", "étrail", 2),  # non-ASCII
    # --- author line ABSENT (the empty string == the option not supplied). This
    # is the regime the repo's dedent-only tests exercise and the regime in which
    # the trim's unconditional presence is observable: the assembled block must be
    # exactly the trimmed included text and must NOT gain a blank line where the
    # missing author line would have gone.
    (["    def baz():", "        pass", ""], "", "", 2),   # dedent-only, F2P block
    (["    def baz():", "        pass", ""], "", "", 4),
    (["    def baz():", "        pass", ""], "", "", 6),
    (["    def quux(self):", "        pass"], "", "", 4),  # tabwidth-dedent shape
    (["    a", "      b"], "L", "", 2),                    # lead only
    (["    a", "      b"], "", "T", 2),                    # trail only
    ([], "", "", 3),                                       # empty block, no author line
    ([], "L", "", 1),
    ([], "", "T", 1),
    ([""], "", "", 1),                                     # single empty line, no author line
    (["  "], "", "", 4),
    # --- zero-width trim (identity), with and without author lines.
    (["    a", "      b"], "L", "T", 0),
    (["    a", "      b"], "", "", 0),
    ([], "", "", 0),
    ([""], "L", "T", 0),
]

_ALPHABET = list(" \tabxyzXY{}<>:#/_.()ü中")


def _rand_case(rng):
    ni = rng.randint(0, 6)
    included = []
    for _ in range(ni):
        L = rng.randint(0, 10)
        included.append("".join(rng.choice(_ALPHABET) for _ in range(L)))
    # in-domain: n >= 0, and NOTHING required of the author lines — so each of
    # them is absent (the empty string) a quarter of the time, giving all four
    # presence combinations, and n == 0 is drawn too.
    if rng.randint(0, 3) == 0:
        lead = ""
    else:
        lead = "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(1, 8)))
    if rng.randint(0, 3) == 0:
        trail = ""
    else:
        trail = "".join(rng.choice(_ALPHABET) for _ in range(rng.randint(1, 8)))
    n = rng.randint(0, 12)
    return included, lead, trail, n


def main():
    counters = {"checked": 0}

    for included, lead, trail, n in BOUNDARY:
        if not check(included, lead, trail, n, counters):
            print(json.dumps({"checked": counters["checked"], "disagreements": 1,
                              "seed": SEED, "phase": "boundary",
                              "status": "fail"}))
            return 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        included, lead, trail, n = _rand_case(rng)
        if not check(included, lead, trail, n, counters):
            print(json.dumps({"checked": counters["checked"], "disagreements": 1,
                              "seed": SEED, "phase": "fuzz", "status": "fail"}))
            return 1

    checked = counters["checked"]
    print("G-CONF OK: contract-stripped impl region of model.py `assemble` == "
          "real patched LiteralIncludeReader.read() on %d inputs "
          "(%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, len(BOUNDARY), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "oracle": "sphinx.directives.code.LiteralIncludeReader.read (called)",
                      "shadow": "direct (contract-stripped impl region)",
                      "status": "pass"}))
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    finally:
        try:
            os.unlink(_ORACLE_PATH)
        except OSError:
            pass
    sys.exit(rc)
