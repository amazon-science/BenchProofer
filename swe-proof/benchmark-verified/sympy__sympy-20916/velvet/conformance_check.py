#!/usr/bin/env python3
r"""G-CONF differential conformance check for sympy__sympy-20916 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`peelDigits`
              via `letterPrefix`/`afterLetters`) transliterated to Python over
              the real repo type (`str`), via the mapping.md bijection
              (`List Char` ↔ `str` over code points). The A-reference
              recognizers `isLetterU`/`isDigitU` are NOT replaced by axiom stubs
              here — G-CONF isolates the R/I legs by running the *same real*
              character classes the oracle uses (`re.match(r'[^\W\d_]', …, re.U)`
              / `re.match(r'\d', …, re.U)`); their soundness is G-AX's job.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sympy.printing.conventions.split_super_sub` applied at base_commit
              (the real correctness oracle, G-RESOLVE). We feed separator-free
              symbol names so the unchanged parsing loop is the identity
              (`name = text`, `supers = []`), and the only observable is the
              trailing-digit decomposition this bundle models: the oracle triple
              `(name', [], subs)` maps to `(name', some subs[0])` on a split and
              `(text, none)` otherwise.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
stdlib + repo only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import re
import sys

SEED = 20916
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean peelDigits, transliterated ----------------
# isLetterU / isDigitU : the two real character classes (A-reference recognizers
# run live, per mapping.md §4 — not substituted by their axiom stubs).
_LETTER = re.compile(r'[^\W\d_]', re.U)
_DIGIT = re.compile(r'\d', re.U)


def _is_letter(c):
    return bool(_LETTER.match(c))


def _is_digit(c):
    return bool(_DIGIT.match(c))


def shadow_peel(name):
    """peelDigits (Solution.lean), transliterated to a (name', subs) pair that
    matches the oracle's observable for a separator-free name:
      match  -> (letters, [digits])
      else   -> (name,    [])
    `letterPrefix`=takeWhile isLetterU, `afterLetters`=dropWhile isLetterU,
    `stripFinalNewline`: at most one final '\n' is set aside before the
    all-digits test and omitted from the digit block — mirroring Python's `$`
    anchor, which matches at end-of-string OR before ONE final newline."""
    i = 0
    while i < len(name) and _is_letter(name[i]):
        i += 1
    letters, rest = name[:i], name[i:]
    digits = rest[:-1] if rest.endswith("\n") else rest   # stripFinalNewline
    if letters != "" and digits != "" and all(_is_digit(c) for c in digits):
        return (letters, [digits])
    return (name, [])


def oracle_split(text):
    """patch.diff's behaviour: the patched split_super_sub. The harness applies
    patch.diff before this runs, so we import the real (post-patch) callee.
    For a separator-free name, supers == [] and the result reduces to
    (name', subs)."""
    from sympy.printing.conventions import split_super_sub
    name, supers, subs = split_super_sub(text)
    return (name, supers, subs)


def fuzz_inputs(n, rng):
    # Separator-free names: letters (Latin/Greek/Cyrillic) + digits (ASCII +
    # non-BMP / Arabic / fullwidth) + a few word-but-not-\d code points (Roman
    # numerals, superscripts) that the letter class accepts.
    letters = ['w', 'a', 'Z', 'ω', 'α', 'а']        # w a Z ω α а
    digits = ['0', '1', '9', '\U0001D7D9', '١', '１']     # 0 1 9 𝟙 ١ １
    trickies = ['Ⅰ', '²', '①', '\n', '\r']           # Ⅰ ² ① + `$`-anchor probes
    alphabet = letters + digits + trickies
    # boundary cases first (plan §4.1 step 4) — the FAIL_TO_PASS matrix bases.
    yield ""
    for s in ["w1", "w\U0001D7D9", "w11", "w\U0001D7D9\U0001D7D9",
              "w\U0001D7D92\U0001D7D9", "ω1", "ω11", "ω\U0001D7D9",
              "ω\U0001D7D92", "w", "ω", "a", "alpha", "alpha11",
              # Python `$` matches before ONE final newline: these split …
              "w1\n", "ω1\n", "abc123\n", "w\U0001D7D9\n",
              # … and these do not.
              "w1\n\n", "w1\r", "w1\r\n", "w\n1", "w\n", "1\n", "\n"]:
        yield s
    for _ in range(n):
        k = rng.randint(0, 6)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    try:
        oracle_split("w1")  # import / smoke
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched repo callee: %r" % e)
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for text in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s_name, s_subs = shadow_peel(text)
        o_name, o_supers, o_subs = oracle_split(text)
        # separator-free name => the loop yields no superscripts; assert that
        # invariant (a scoping check), then compare the trailing-digit split.
        if o_supers != [] or (s_name, s_subs) != (o_name, o_subs):
            disagreements.append((text, (s_name, s_subs), (o_name, o_supers, o_subs)))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for t, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (t, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of splitTrailingDigits agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
