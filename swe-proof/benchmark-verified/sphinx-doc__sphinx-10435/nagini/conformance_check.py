#!/usr/bin/env python3
r"""G-CONF differential conformance check for sphinx-doc__sphinx-10435 (nagini).

SHADOW: the impl region of model.py's `assemble_inline_code`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers (`cp_break`, `cp_suppress`, `open_wrap`, `close_wrap`) copy
over as plain functions with PSeq realized as an immutable tuple shim (the
impl itself only touches `cp_break`/`cp_suppress`; the sequence-valued helpers
appear in contracts only). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`sphinx.writers.latex.LaTeXTranslator.visit_literal`, its highlighted
inline-code branch. The gate applies patch.diff to /testbed before this script
runs; PYTHONPATH=/testbed makes the patched module importable. The branch is
driven directly on a translator instance whose upstream highlighter is stubbed
to deliver a carrier of the documented shape (the model's precondition
boundary: the producer is unchanged and outside the modeled behavior); the
oracle output is the concatenation of the fragments the real method appends to
`self.body` (mapping.md section 2 maps the two appends to one concatenation).
A separate tier additionally runs the REAL producer (PygmentsBridge) end to
end on generated source snippets, confirming its carriers have the documented
shape and that shadow == real on those fully-reachable inputs too.

Type bridge (mapping.md section 2): str <-> List[int] of code points
(`ord`/`chr` per position); the shadow's returned List[int] is decoded back to
str and compared byte-for-byte against the oracle's appended text.

Input domain (the Requires): content is a non-empty code-point list whose
final code point is not the line-break. Generation additionally stays inside
the unchanged producer's reachable alphabet — in particular the content never
embeds the raw opening-marker literal, which the producer's escaping cannot
emit (the substitution target must occur exactly once, at the carrier head;
this is the documented carrier shape the precondition states).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz contents +
a real-producer tier. Pinned fuzz seed: 10435.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib-only imports (plus the repo under test).
"""
import json
import random
import sys

SEED = 10435
N_FUZZ = 100_000
N_REAL_PRODUCER = 300


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

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


# --- pure helpers from model.py, contracts stripped ---------------------------

def cp_break():
    # the line-break code point ('\n')
    return 10


def cp_suppress():
    # the renderer's end-of-line line-suppression / comment marker ('%')
    return 37


def open_wrap():
    # the opening inline-code wrapper after substitution
    return PSeq(92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
                92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
                116, 101, 123)


def close_wrap():
    # the closing inline-code wrapper appended last
    return PSeq(125, 125)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def assemble_inline_code(content):
    br = cp_break()
    pct = cp_suppress()

    # prefix = open_wrap ++ [SUPPRESS] ++ [BREAK]  (literal opening wrapper)
    result = [92, 115, 112, 104, 105, 110, 120, 99, 111, 100, 101, 123,
              92, 115, 112, 104, 105, 110, 120, 117, 112, 113, 117, 111,
              116, 101, 123, pct, br]
    # copy the content
    k = 0
    while k < len(content):
        result = result + [content[k]]
        k = k + 1
    # suffix = [SUPPRESS] ++ [BREAK] ++ close_wrap
    result = result + [pct, br, 125, 125]
    return result


# --- oracle plumbing -----------------------------------------------------------

# the carrier markers of the documented upstream shape (mapping.md section 3.1)
OPEN_MARKER = "\\begin{Verbatim}[commandchars=\\\\\\{\\}]"
CLOSE_MARKER = "\\end{Verbatim}"
BREAK = "\n"


class _FakeNode:
    """Minimal element that routes visit_literal into its highlighted
    inline-code branch (a 'code' class plus a language)."""

    def __init__(self, text):
        self._text = text

    def __getitem__(self, key):
        if key == "classes":
            return ["code"]
        raise KeyError(key)

    def get(self, key, default=None):
        if key == "language":
            return "python"
        return default

    def astext(self):
        return self._text


class _FakeHighlighter:
    """Delivers a fixed carrier — the precondition boundary: the unchanged
    upstream producer's documented output shape."""

    def __init__(self, carrier):
        self._carrier = carrier

    def highlight_block(self, *args, **kwargs):
        return self._carrier


class _FakeConfig:
    highlight_options = {}


def real_branch_output(LaTeXTranslator, SkipNode, carrier):
    """Drive the REAL patched visit_literal on a translator whose highlighter
    returns `carrier`; return the concatenation of the appended fragments."""
    t = object.__new__(LaTeXTranslator)
    t.in_title = False
    t.config = _FakeConfig()
    t.highlighter = _FakeHighlighter(carrier)
    t.body = []
    try:
        LaTeXTranslator.visit_literal(t, _FakeNode("src"))
    except SkipNode:
        pass
    else:
        return None  # branch not taken: reported as a disagreement upstream
    return "".join(t.body)


def carrier_of(content):
    """The documented upstream carrier shape (the model's precondition)."""
    return OPEN_MARKER + BREAK + content + BREAK + CLOSE_MARKER + BREAK


def check_content(LaTeXTranslator, SkipNode, content, tier):
    """Run shadow and oracle on one content fragment; return an error string
    on disagreement, else None."""
    # Requires: non-empty, final code point is not the line-break
    cps = [ord(ch) for ch in content]
    assert len(cps) > 0 and cps[-1] != cp_break()

    shadow = "".join(chr(c) for c in assemble_inline_code(cps))
    real = real_branch_output(LaTeXTranslator, SkipNode, carrier_of(content))
    if real is None:
        return ("DISAGREEMENT (%s): highlighted branch not taken\n"
                "  content=%r" % (tier, content))
    if shadow != real:
        return ("DISAGREEMENT (%s)\n  content=%r\n  shadow=%r\n  real  =%r"
                % (tier, content, shadow, real))
    return None


def boundary_contents():
    return [
        "x",
        "%",
        "}",
        "{",
        "}}",
        " leading and trailing space ",
        "ends in tab\t",
        "a b c",
        "\\PYG{k}{pass}",
        "\\PYG{k}{def} \\PYG{n+nf}{f}\\PYG{p}{(}\\PYG{p}{)}\\PYG{p}{:}",
        "\\PYG{l+m+mi}{1} \\PYG{o}{+} \\PYG{l+m+mi}{2}",
        "line one\nline two",              # interior break is allowed
        "Verbatim",                        # marker-word noise inside content
        "commandchars=\\\\",
        "\\end{Verbatim} inside",          # closing-marker text interior
        "unicode \u00e9\u2192\u4e2d",
        "%\n%",
    ]


_PIECES = ["\\PYG{k}{def}", "abc", "1 + 2", "\\{", "\\}", "Verbatim",
           "commandchars", "}}", "{{", "%", "x", " ", "z9", "\t",
           "\\PYGZbs{}", "\\PYGZob{}", "\\PYGZcb{}", "\u00e9", "\n"]


def rand_content(rng):
    n = rng.randint(1, 8)
    c = "".join(rng.choice(_PIECES) for _ in range(n))
    # Requires: non-empty and not break-terminated. The piece alphabet cannot
    # assemble the raw opening-marker literal (producer-reachable contents
    # never contain it), so the substitution target stays unique.
    while c.endswith("\n"):
        c = c[:-1]
    if not c:
        c = "x"
    return c


def real_producer_tier(LaTeXTranslator, SkipNode, rng):
    """Run the REAL upstream producer end to end: confirm its carriers have
    the documented shape, then diff shadow vs real on the extracted content."""
    from sphinx.highlighting import PygmentsBridge
    bridge = PygmentsBridge("latex")
    snippets = ["pass", "def f():\n    pass", "x = 1 + 2", "print('hi')",
                "class A:\n    y = {1: 'a'}", "import os", "a = '%'",
                "s = 'Verbatim'", "b = \"\\\\\"", "lambda z: z * 2"]
    checked = 0
    for _ in range(N_REAL_PRODUCER):
        src = rng.choice(snippets)
        carrier = bridge.highlight_block(src, "python", opts={}, location=None)
        head = OPEN_MARKER + BREAK
        tail = BREAK + CLOSE_MARKER + BREAK
        if not (carrier.startswith(head) and carrier.endswith(tail)):
            return None, ("real producer carrier off documented shape:\n"
                          "  src=%r\n  carrier=%r" % (src, carrier)), checked
        content = carrier[len(head):-len(tail)]
        if not content or content.endswith(BREAK):
            # outside the Requires domain; the producer never emits this for
            # a non-empty highlighted body, so treat it as a shape violation
            return None, ("real producer content off precondition:\n"
                          "  src=%r\n  content=%r" % (src, content)), checked
        err = check_content(LaTeXTranslator, SkipNode, content,
                            "real-producer")
        if err:
            return None, err, checked
        checked += 1
    return checked, None, checked


def main():
    sys.setrecursionlimit(10000)
    from sphinx.writers.latex import LaTeXTranslator  # REAL patched module
    from docutils.nodes import SkipNode

    checked = 0
    for content in boundary_contents():
        err = check_content(LaTeXTranslator, SkipNode, content, "boundary")
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_content(LaTeXTranslator, SkipNode, rand_content(rng),
                            "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    n_real, err, part = real_producer_tier(LaTeXTranslator, SkipNode, rng)
    if err:
        print(err)
        return 1
    checked += n_real

    print("G-CONF OK: shadow impl == real highlighted inline-code branch on "
          "%d inputs (%d boundary + %d fuzz + %d real-producer, seed %d)."
          % (checked, len(boundary_contents()), N_FUZZ, n_real, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
