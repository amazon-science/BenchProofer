#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8621.

The bundle models ONE behavior: the token list produced by the post-patch
`KeyboardTransform.pattern.split(text)` in `sphinx/builders/html/transforms.py`,
where the gold patch changes the pattern to

    re.compile(r'(?<=.)(-|\\+|\\^|\\s+)(?=.)')

i.e. a separator (`-`, `+`, `^`, or a `\\s+` run) separates only when it has a
character on BOTH sides. The modeled value is the pure return value of
`pattern.split(text)` (mapping.md); the unchanged node-rebuilding loop in
`KeyboardTransform.run` is a deterministic function of that list and is not
modeled.

ORACLE  = the REAL changed callee: `re.split` driven by the EXACT post-patch
          regex. This is the genuine operation the patch installs, so the oracle
          is the real library splitter (not a hand replica).
SHADOW  = an op-for-op transliteration of `implementation_tokenizeKeystrokes`
          (Solution.lean) = the `step`/`finalize` deferred-fold tokenizer
          (refinement.md). All ops are R-tagged (conf_skip=false).

Bridge (mapping.md): `text : str` ↔ `List Char` via `list(text)`; the result
`list[str]` ↔ `List (List Char)` element-wise via `''.join`. So the comparison is
`re.split(POST, text) == [''.join(t) for t in shadow(list(text))]`, i.e. directly
on the Python-side `list[str]`.

Modeled domain (mapping.md "newline note"): a `:kbd:` keystroke spec is a single
inline text line and never contains `'\\n'`. Python `\\s` matches `'\\n'` but the
post-patch lookaround `.` does not, so the regex's newline behavior is outside the
modeled domain. The fuzzer therefore draws ONLY newline-free inputs (whitespace
alphabet = `\\s` minus `\\n`). This is a documented domain restriction, logged
below — not a silent cap.

stdlib-only. Pinned seed: 8621 (also in mapping.md).
"""
import itertools
import random
import re
import sys

SEED = 8621
N = 200_000

# The REAL post-patch callee — the genuine changed operation.
POST = re.compile(r'(?<=.)(-|\+|\^|\s+)(?=.)')

SEP1 = set('-+^')
# `\s` minus `\n` (the modeled newline-free domain).
WS = set(' \t\r\f\x0b')


def _isws(c):
    return c in WS


# --- SHADOW of implementation_tokenizeKeystrokes (op-for-op, refinement.md) ----
# Pending candidate: None | ('s', ch) | ('w', [chars]).
def shadow(text):
    out = []          # st.out : list of committed tokens (each a list of chars)
    cur = []          # st.cur
    pend = None       # st.pend
    started = False   # st.started

    def step_no_pend(c):
        nonlocal cur, pend, started
        if not started:                       # op 3: lookbehind — first char is text
            cur = cur + [c]
            started = True
        elif c in SEP1:                        # op 6: single separator candidate
            pend = ('s', c)
        elif _isws(c):                         # op 5/6: whitespace run candidate
            pend = ('w', [c])
        else:
            cur = cur + [c]

    for c in text:
        if pend is not None:
            if pend[0] == 'w' and _isws(c):    # op 5: greedy \s+ munch
                pend = ('w', pend[1] + [c])
                continue
            else:                              # op 4: lookahead satisfied -> commit
                out.append(cur)
                out.append(list(pend[1]) if pend[0] == 'w' else [pend[1]])
                cur = []
                pend = None
        step_no_pend(c)

    # finalize (ops 7/8): a candidate with no following char is at EOS.
    if pend is not None:
        if pend[0] == 'w':
            run = pend[1]
            if len(run) >= 2:                  # op 8: shave last char for lookahead
                out.append(cur)
                out.append(run[:-1])
                cur = [run[-1]]
            else:                              # op 7: single trailing ws -> text
                cur = cur + run
        else:                                  # op 7: trailing/standalone sep -> text
            cur = cur + [pend[1]]
    out.append(cur)
    return out


def shadow_str(text):
    """Bridge to the Python `list[str]` shape (mapping.md)."""
    return [''.join(tok) for tok in shadow(list(text))]


def disagree(text):
    o = POST.split(text)
    s = shadow_str(text)
    if o != s:
        return (text, o, s)
    return None


def _edge_cases():
    # FAIL_TO_PASS shapes + PASS_TO_PASS kbd shapes + boundary cases.
    return [
        'Alt+^',          # F2P: ['Alt','+','^']
        '-',              # F2P: ['-']
        '+',              # standalone +
        '^',              # standalone ^
        'Shift-+',        # ['Shift','-','+']
        'Control+X',      # P2P: ['Control','+','X']
        'M-x M-s',        # P2P
        'space',          # P2P single token
        '',               # empty
        'a', 'ab',
        'a-', '-a', 'a-b',
        'a ', ' a', 'a  ', '  a', 'a  b', 'a   b', 'a b',
        'a -', '- b', 'a - b', 'a -- b', 'a  -  b',
        '   ', '  ', 'a\t\tb', '\ta', 'a\t',
        'a^b^c', 'a---b', 'Shift-+x',
        '+ +', '^ ^', '- -',
    ]


def main() -> int:
    checked = 0

    for s in _edge_cases():
        d = disagree(s)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle(re.split)={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # Exhaustive over a small newline-free alphabet (lengths 0..6).
    alpha = ['a', 'b', '-', '+', '^', ' ', '\t']
    for L in range(0, 7):
        for tup in itertools.product(alpha, repeat=L):
            s = ''.join(tup)
            d = disagree(s)
            if d:
                print(f"DISAGREE exhaustive {d[0]!r}: oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
            checked += 1

    # Random newline-free fuzz, biased to separators/whitespace.
    rng = random.Random(SEED)
    big = ['a', 'b', 'c', 'X', '-', '+', '^', ' ', ' ', '\t', '\r', '\f', '\x0b']
    for _ in range(N):
        s = ''.join(rng.choice(big) for _ in range(rng.randint(0, 18)))
        d = disagree(s)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print("oracle=real re.split(post-patch pattern); domain=newline-free (mapping.md)")
    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
