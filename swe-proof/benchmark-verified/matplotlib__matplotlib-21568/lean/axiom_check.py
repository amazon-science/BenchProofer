#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-21568 — A-reference validation.

The bundle CONSUMES no unchanged-callee axiom. It does, however, deep-model ONE
unchanged library callee: the regular-expression substitution that lifts maximal
ASCII-letter runs out of the math group,

    re.sub(r'([a-zA-Z]+)', r'}$\\1$\\mathdefault{', text)

modeled in Solution.lean as `bracketLetterRuns` (an A-reference, refinement.md).
This check validates that the deep model reproduces the REAL callee exactly on
boundary + fuzz inputs: for every test string, the character list produced by
`bracketLetterRuns` (transliterated below) must equal the real `re.sub` output.

If they ever disagree the deep model is unsound (G-AX fail). stdlib-only; the
real callee is `re.sub` from the standard library, used verbatim.
"""
import json
import random
import re
import sys

SEED = 21568
N = 200_000


# --- REAL callee: the exact regex substitution the patch leaves unchanged ----
def real_re_sub(text):
    return re.sub(r'([a-zA-Z]+)', r'}$\1$\\mathdefault{', text)


# --- DEEP MODEL: transliteration of `bracketLetterRuns` (Solution.lean) ------
def model_bracket_letter_runs(text):
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isascii() and c.isalpha():          # Char.isAlpha == ASCII [a-zA-Z]
            j = i
            while j < n and text[j].isascii() and text[j].isalpha():
                j += 1
            out.extend(list("}$"))
            out.extend(list(text[i:j]))
            out.extend(list("$\\mathdefault{"))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


EDGE = [
    "", "Jan", "Jan 1990-01-01 00:00", "1990-01-01", "01-01 00", "01 00:00",
    "Jan 01", "00:00:00", "59.5", "Feb", "Jan-01", "-", ":", " ", "::--  ",
    "abc", "a b c", "1996-Jan-01", "20:00", "AB12CD", "aA1bB2",
    "JanFebMar", "x", "Z9",
]
POOL = list("abcXYZ0123456789-: .,/JanFeb")


def main() -> int:
    checked = 0
    bad = None
    for t in EDGE:
        if real_re_sub(t) != model_bracket_letter_runs(t):
            bad = (t, real_re_sub(t), model_bracket_letter_runs(t))
            break
        checked += 1
    if bad is None:
        rng = random.Random(SEED)
        for _ in range(N):
            k = rng.randint(0, 24)
            t = "".join(rng.choice(POOL) for _ in range(k))
            if real_re_sub(t) != model_bracket_letter_runs(t):
                bad = (t, real_re_sub(t), model_bracket_letter_runs(t))
                break
            checked += 1

    if bad is not None:
        print(json.dumps({
            "status": "fail",
            "instance": "matplotlib__matplotlib-21568",
            "input": bad[0], "real": bad[1], "model": bad[2],
        }))
        return 1

    print(json.dumps({
        "status": "pass",
        "instance": "matplotlib__matplotlib-21568",
        "checked": checked,
        "reference": "re.sub(r'([a-zA-Z]+)', r'}$\\\\1$\\\\mathdefault{', text) "
                     "== bracketLetterRuns (A-reference)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
