#!/usr/bin/env python
"""G-CONF: differential conformance for sphinx-doc__sphinx-10435.

Modeled function: the highlighted-`code`-role tail of
`LaTeXTranslator.visit_literal` (`sphinx/writers/latex.py`), i.e. the
post-processing applied to the syntax-highlighter output `hlcode` before it is
appended to `self.body`. The gold patch rewrites three lines so the framing
newlines of the Verbatim environment are comment-suppressed (no spurious
leading/trailing space in the rendered PDF).

This post-processing is pure string manipulation (`str.replace`, `str.rstrip`,
fixed slice, concatenation). The REAL patch behaviour leg below is the gold
patch's lines executed verbatim (CR = '\\n', the module constant). It is diffed
against the Python shadow of the Lean `implementation_visit_literal` skeleton
over a discrete catalogue plus >= 1e5 fuzzed Pygments-`LatexFormatter`-shaped
`hlcode` strings.

Bridge (mapping.md): Python `str` <-> Lean `List Char`; the concatenation of the
two `self.body.append(...)` strings <-> the Lean `result`. Exit 0 iff zero
disagreements. stdlib only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 150_000  # >= 1e5

CR = '\n'

BEGIN = r'\begin{Verbatim}[commandchars=\\\{\}]'
# The fixed replacement target, POST-patch (note trailing '%').
UPQUOTE = r'\sphinxcode{\sphinxupquote{%'
END = r'\end{Verbatim}'
assert len(END) == 14


# ---- REAL patch behaviour (gold patch.diff lines, executed verbatim) --------

def patch_behaviour(hlcode):
    """The gold-patched post-processing of `visit_literal`. Returns the string
    contributed to `self.body` (concatenation of the two appends)."""
    hlcode = hlcode.replace(r'\begin{Verbatim}[commandchars=\\\{\}]',
                            r'\sphinxcode{\sphinxupquote{%')
    # get consistent trailer
    hlcode = hlcode.rstrip()[:-15]  # strip \n\end{Verbatim}
    body = []
    body.append(hlcode)
    body.append('%' + CR + '}}')
    return ''.join(body)


# ---- Python shadow of implementation_visit_literal (R/I leg) ----------------

def _rstrip_ws(s):
    # rstripWs: default Python whitespace set (matches str.rstrip()).
    return s.rstrip(' \t\n\r\x0b\x0c')


def _drop_last_n(n, s):
    # dropLastN n s == s[:max(0,len-n)]
    return s[:max(0, len(s) - n)]


def _replace_all(pat, rep, s):
    # replaceAll: all non-overlapping, left-to-right (== str.replace).
    out = []
    i = 0
    L = len(pat)
    while i < len(s):
        if L > 0 and s.startswith(pat, i):
            out.append(rep)
            i += L
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def lean_shadow(hlcode):
    hl = hlcode
    hl = _replace_all(BEGIN, UPQUOTE, hl)
    hl = _drop_last_n(15, _rstrip_ws(hl))
    body = []
    body.append(hl)
    body.append('%' + CR + '}}')
    return ''.join(body)


# ---- fuzzed Pygments-LatexFormatter-shaped hlcode ---------------------------

PYG_TOKENS = [
    r'\PYG{k}{def}', r'\PYG{n+nf}{foo}', r'\PYG{p}{(}', r'\PYG{l+m+mi}{1}',
    r'\PYG{o}{+}', r'\PYG{k+kc}{None}', r'\PYG{l+s+s2}{\PYGZdq{}}',
    r'\PYG{p}{)}', r'\PYG{p}{:}', r'\PYG{k}{pass}', 'abc', 'x_y',
    r'\PYGZsh{}', ' ', '\t',
]


def make_hlcode(rng):
    """Build a string shaped like Pygments LatexFormatter output: a Verbatim
    environment with a newline after the opening and (usually) before the
    closing, plus possible extra trailing whitespace that rstrip removes."""
    n = rng.randint(0, 8)
    inner_lines = []
    for _ in range(rng.randint(1, 3)):
        line = ''.join(rng.choice(PYG_TOKENS) for _ in range(n))
        inner_lines.append(line)
    inner = '\n'.join(inner_lines)
    # Canonical highlighter shape: BEGIN \n <code> \n END, then maybe trailing ws.
    s = BEGIN + '\n' + inner + '\n' + END
    # Pygments sometimes emits trailing whitespace/newlines that rstrip handles.
    s += rng.choice(['', '\n', '\n\n', ' \n', '\t', '  ', '\x0c'])
    return s


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # discrete catalogue including the exact F2P example fragment.
    f2p_inner = (r'\PYG{k}{def} \PYG{n+nf}{foo}\PYG{p}{(}\PYG{l+m+mi}{1} '
                 r'\PYG{o}{+} \PYG{l+m+mi}{2}\PYG{p}{)}\PYG{p}{:} \PYG{k}{pass}')
    catalogue = [
        BEGIN + '\n' + f2p_inner + '\n' + END + '\n',
        BEGIN + '\n' + 'x' + '\n' + END,
        BEGIN + '\n' + '\n' + END + '\n\n',
        BEGIN + '\n' + 'a\nb\nc' + '\n' + END + '   \n',
    ]
    for hlcode in catalogue:
        checked += 1
        if patch_behaviour(hlcode) != lean_shadow(hlcode):
            disagreements += 1
            print(f"DISAGREE (catalogue): {hlcode!r}")
            print(f"  patch={patch_behaviour(hlcode)!r}")
            print(f"  lean ={lean_shadow(hlcode)!r}")

    for _ in range(N_RANDOM):
        hlcode = make_hlcode(rng)
        checked += 1
        a = patch_behaviour(hlcode)
        b = lean_shadow(hlcode)
        if a != b:
            disagreements += 1
            if disagreements <= 10:
                print(f"DISAGREE: {hlcode!r}\n  patch={a!r}\n  lean ={b!r}")

    print(f"checked={checked} disagreements={disagreements} seed={SEED}")
    if disagreements == 0:
        print("status=pass G-CONF: lean shadow == gold patch behaviour")
        sys.exit(0)
    print("status=fail")
    sys.exit(1)


if __name__ == "__main__":
    main()
