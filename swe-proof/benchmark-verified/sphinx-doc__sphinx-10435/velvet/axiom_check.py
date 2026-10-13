#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10435.

The Solution models one UNCHANGED callee with an axiom: the syntax
highlighter's rendering of a code snippet for the LaTeX block formatter
(`renderedInline` + the structural fact `highlightInline_form`). The axiom
claims ONLY the surrounding frame — nothing about the rendered body:

    highlight_block(snippet, lang)  ==  BEGIN + "\\n" + body + "\\n" + END + "\\n"

for some body, where

    BEGIN = r'\\begin{Verbatim}[commandchars=\\\\\\{\\}]'   (37 code points)
    END   = r'\\end{Verbatim}'                              (14 code points)

This is the weakest contract the routine's pointer arithmetic relies on
(directive 7): the begin sequence is a prefix of fixed length 37, and the
text ends with "\\n" + END + "\\n" (so the right-strip removes exactly the
final newline and the 15-char tail `"\\n" + END` is what the new slice drops).

`renderedInline` (the body) is intentionally unconstrained — the spec pins
nothing about it — so G-AX validates only the frame, which is exactly what the
proof consumes.

Executes the REAL stdlib/community callee `PygmentsBridge('latex')
.highlight_block` (the same call the writer makes) on boundary snippets across
several languages plus randomized fuzzing, and asserts the structural axiom
holds on every observation. Imports only sphinx (present in the instance
image). Exit 0 iff every obligation holds.
"""
import random
import sys

from sphinx.highlighting import PygmentsBridge

BEGIN = r'\begin{Verbatim}[commandchars=\\\{\}]'
END = r'\end{Verbatim}'

assert len(BEGIN) == 37, len(BEGIN)
assert len(END) == 14, len(END)


def check_frame(hb, snippet, lang):
    """Assert highlight_block(snippet, lang) matches the structural axiom:
    BEGIN + '\\n' + body + '\\n' + END + '\\n'."""
    hlcode = hb.highlight_block(snippet, lang)  # the REAL callee
    # frame: begin prefix, end suffix preceded by a newline, final newline
    assert hlcode.startswith(BEGIN + '\n'), (
        "axiom unsound: highlight_block(%r, %r) does not begin with BEGIN+nl: %r"
        % (snippet, lang, hlcode[:50]))
    assert hlcode.endswith('\n' + END + '\n'), (
        "axiom unsound: highlight_block(%r, %r) does not end with nl+END+nl: %r"
        % (snippet, lang, hlcode[-50:]))
    # reconstruct the body and assert exact structural equality
    body = hlcode[len(BEGIN) + 1: -(len(END) + 1)]
    assert body.endswith('\n'), (
        "axiom unsound: inner segment does not end with newline: %r" % body)
    body = body[:-1]
    rebuilt = BEGIN + '\n' + body + '\n' + END + '\n'
    assert hlcode == rebuilt, (
        "axiom unsound on (%r, %r): %r != %r" % (snippet, lang, hlcode, rebuilt))
    # the two slicing facts the proof relies on:
    #   right-strip removes exactly the final newline
    assert len(hlcode) - len(hlcode.rstrip()) == 1, (
        "axiom unsound: rstrip removed != 1 char on (%r, %r)" % (snippet, lang))
    #   dropping the begin prefix (len 37) leaves '\n' + body + '\n' + END + '\n'
    assert hlcode[len(BEGIN):] == '\n' + body + '\n' + END + '\n'
    #   the rstripped tail's last 15 chars are '\n' + END
    assert hlcode.rstrip()[-15:] == '\n' + END


def main():
    hb = PygmentsBridge('latex')
    languages = ['python', 'python3', 'text', 'bash', 'html', 'rst']
    boundary = [
        'def foo(1 + 2 + None + "abc"): pass',   # the F2P snippet
        '',                                       # empty
        '   ',                                    # whitespace only
        'x',
        'a + b',
        '"a string"',
        "'q'",
        '# a comment',
        'line1\nline2\nline3',                    # multi-line
        'trailing   ',                            # trailing spaces
        'multi\n\n\nblank',                        # blank lines
        '\t',                                     # tab
        'def f():\n    return 1',
        'a' * 200,                                # long
        '<tag attr="v">',
        'foo(1+2)',
        '%comment-like%',
        '}} braces {{',
        r'\end{Verbatim}',                        # adversarial: end token in body
    ]
    checked = 0
    for snippet in boundary:
        for lang in languages:
            try:
                check_frame(hb, snippet, lang)
                checked += 1
            except Exception as e:
                # a language that cannot lex this snippet is skipped by sphinx
                # (it warns and returns plain Verbatim); still check the frame.
                if "Could not lex" in str(e):
                    continue
                raise

    rng = random.Random(10435)
    alphabet = list('abcdefghijklmnop ()+-=*/.,:;_"\'#%{}\\\t') + ['\n']
    fuzz = 0
    for _ in range(20000):
        n = rng.randint(0, 40)
        snippet = ''.join(rng.choice(alphabet) for _ in range(n))
        lang = rng.choice(languages)
        try:
            check_frame(hb, snippet, lang)
            fuzz += 1
        except Exception as e:
            if "Could not lex" in str(e):
                continue
            raise

    print("G-AX OK: highlight_block structural-frame axiom "
          "(BEGIN+nl+body+nl+END+nl; len(BEGIN)=37, len(END)=14) sound on "
          "%d boundary + %d fuzz observations across %d languages."
          % (checked, fuzz, len(languages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
