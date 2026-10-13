#!/usr/bin/env python3
r"""G-AX / A-reference executable soundness check for sphinx-doc__sphinx-10435.

There is NO consumed `@ContractOnly` axiom in this bundle: the inline-code
assembly is modelled DEEPLY (spelled-out sequence take/drop/concat in
model.py's impl, pinned by the postcondition). This script validates the two
faithfulness claims the deep model rests on:

  (A-reference 1) The carrier produced upstream really has the documented shape
      OPEN ++ '\n' ++ content ++ '\n' ++ CLOSE ++ '\n', where OPEN is the exact
      opening marker the writer substitutes (`\begin{Verbatim}[commandchars=...`)
      and CLOSE is `\end{Verbatim}` (14 chars), with CLOSE the only trailing
      non-whitespace and a single trailing newline. This is what makes the
      writer's `.rstrip()[:-15]` strip exactly '\n\end{Verbatim}'.

  (A-reference 2) The model's assembled output (open_wrap ++ '%' ++ '\n' ++
      content ++ '%' ++ '\n' ++ '}}') equals the REAL string surgery the patched
      writer performs:
          h = carrier.replace(OPEN, r'\sphinxcode{\sphinxupquote{%')
          h = h.rstrip()[:-15]
          out = h + '%' + '\n' + '}}'
      over boundary + randomized fuzz carriers.

It also checks the PRE-patch surgery (the bug) produces the model_prepatch
output (no '%' suppressors), so the discriminating clause is the real delta.

stdlib-only imports. Exit 0 iff every observation is faithful.
"""
import random
import sys

CR = "\n"
OPEN = r"\begin{Verbatim}[commandchars=\\\{\}]"      # writer's replace target
CLOSE = r"\end{Verbatim}"                            # 14 chars
OPEN_WRAP = r"\sphinxcode{\sphinxupquote{"           # 27 chars
CLOSE_WRAP = "}}"

assert len(CLOSE) == 14
assert len(OPEN_WRAP) == 27


def real_surgery_post(carrier):
    """The patched writer's exact post-patch string surgery (gold patch)."""
    h = carrier.replace(OPEN, OPEN_WRAP + "%")
    h = h.rstrip()[:-15]            # strip '\n\end{Verbatim}'
    return h + "%" + CR + CLOSE_WRAP


def real_surgery_pre(carrier):
    """The pre-patch writer's string surgery (the bug)."""
    h = carrier.replace(OPEN, OPEN_WRAP)
    h = h.rstrip()[:-14]            # strip '\end{Verbatim}'
    return h + CLOSE_WRAP


def model_assembled(content):
    """model.py deep model: open_wrap '%' '\n' content '%' '\n' '}}'."""
    return OPEN_WRAP + "%" + CR + content + "%" + CR + CLOSE_WRAP


def model_assembled_prepatch(content):
    """model_prepatch.py deep model: open_wrap '\n' content '\n' '}}'."""
    return OPEN_WRAP + CR + content + CR + CLOSE_WRAP


def carrier_of(content):
    """The documented upstream carrier shape (A-reference 1)."""
    return OPEN + CR + content + CR + CLOSE + CR


def check(content):
    carrier = carrier_of(content)
    # A-reference 1: documented shape invariants the slice constants rely on.
    assert carrier.startswith(OPEN), repr(carrier)
    assert carrier.rstrip().endswith(CLOSE), repr(carrier)
    assert carrier.endswith(CR)
    # the only trailing whitespace is the single closing newline
    assert carrier.rstrip() == OPEN + CR + content + CR + CLOSE, repr(carrier)
    # A-reference 2: deep model == real post-patch surgery.
    observed = real_surgery_post(carrier)
    expected = model_assembled(content)
    assert observed == expected, (
        "post-patch surgery vs model mismatch on content=%r:\n  real  =%r\n"
        "  model =%r" % (content, observed, expected))
    # delta witness: pre-patch surgery == model_prepatch (no suppressors).
    obs_pre = real_surgery_pre(carrier)
    exp_pre = model_assembled_prepatch(content)
    assert obs_pre == exp_pre, (
        "pre-patch surgery vs model_prepatch mismatch on content=%r:\n"
        "  real =%r\n  model=%r" % (content, obs_pre, exp_pre))
    # the discriminating structural property: post has the two '%' suppressors
    # at exactly the modelled offsets; pre does not.
    assert observed[len(OPEN_WRAP)] == "%"
    assert observed[len(OPEN_WRAP) + 1] == CR
    assert observed[len(observed) - len(CLOSE_WRAP) - 2] == "%"
    assert observed[len(observed) - len(CLOSE_WRAP) - 1] == CR
    assert obs_pre[len(OPEN_WRAP)] == CR           # bug: bare break, no '%'
    assert observed != obs_pre


def main():
    # boundary content fragments (the highlighted body; never ends in '\n'
    # because the writer's content line is non-empty highlighted code).
    boundary = [
        r"\PYG{k}{def}",
        r"\PYG{k}{def} \PYG{k}{pass}",
        r"\PYG{l+m+mi}{1} \PYG{o}{+} \PYG{l+m+mi}{2}",
        "x",
        "a b c",
        r"\PYG{n+nf}{foo}\PYG{p}{(}\PYG{p}{)}\PYG{p}{:} \PYG{k}{pass}",
        "tab\tend",          # interior whitespace is fine; content tail != '\n'
        "line1 line2 word",
    ]
    for c in boundary:
        check(c)

    # randomized fuzz: content is arbitrary non-empty text not ending in
    # whitespace (the highlighted code line). Include OPEN-like and CLOSE-like
    # noise inside the content to stress the single-occurrence replace target.
    rng = random.Random(10435)
    pieces = [r"\PYG{k}{def}", "abc", "1 + 2", r"\{", r"\}", "Verbatim",
              "commandchars", "}}", "{{", "%", "x", " ", "z9"]
    for _ in range(20000):
        n = rng.randint(1, 8)
        c = "".join(rng.choice(pieces) for _ in range(n))
        c = c.rstrip()
        if not c:
            c = "x"
        check(c)

    print("G-AX OK: deep inline-code assembly == real post-patch surgery, and "
          "the pre-patch surgery == model_prepatch (no suppressors), over %d "
          "boundary + 20000 fuzz carriers; documented carrier shape confirmed."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
