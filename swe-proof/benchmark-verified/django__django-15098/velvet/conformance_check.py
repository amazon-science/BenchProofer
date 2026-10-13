#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15098 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region transliterated to
              Python: the `leadingLocaleTag 2` scan (the `lstep`/`ldecode` fold)
              over the URL path, via the mapping.md bijection (`List Char` ↔
              `str`, `Char` ↔ Python char). This is the leading locale tag the
              path carries, the value the changed operation extracts.
  * ORACLE  — `patch.diff`'s behaviour: the *patched* prefix matcher
              `language_code_prefix_re` from the repo at base_commit (the real
              correctness oracle, G-RESOLVE), read straight out of
              `django.utils.translation.trans_real`; the extracted tag is
              `match.group(1)` (or None when the path does not match).

The A-tagged downstream callee (`listedLanguage` ↔ `get_supported_language_variant`)
is NOT in scope here — G-CONF isolates the R/I leg (the regex/prefix change);
the A leg stays with G-AX. So the shadow is pure R/I and the oracle is exactly
the operation patch.diff edits.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

SEED = 15098
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean leadingLocaleTag 2, transliterated ---------
# isWordChar (c) := c.isAlphanum || c == '_'   (ASCII \w domain; see mapping.md)
_WORD = set(string.ascii_letters + string.digits + "_")


def _is_word(c):
    return c in _WORD


def _is_sep(c):
    return c == "-" or c == "@"


def shadow_leading_tag(path, max_segs=2):
    """leadingLocaleTag max_segs (Solution.lean), transliterated to str.

    Direct port of `lstep`/`ldecode` folded over the characters: a left-to-right
    automaton recognising the leading locale tag a path carries, admitting the
    primary subtag plus up to `max_segs` further '-'/'@'-separated subtags."""
    # status: 0 scanning, 1 locked by '/', 2 rejected, 3 tentative-accept by a
    # trailing line-terminator (stands only if it was the path's last char).
    status, phase, acc, segs = 0, 0, [], 0
    for c in path:
        if status == 1 or status == 2:
            break
        if status == 3:
            # a '\n' tentatively closed the tag, but a further char follows it,
            # so it was not the path's last char -> reject.
            status = 2
            break
        if phase == 0:
            if c == "/":
                phase = 1
            else:
                status = 2
        elif phase == 1:
            if _is_word(c):
                phase = 2
                acc.append(c)
            else:
                status = 2
        elif phase == 2:
            if _is_word(c):
                acc.append(c)
            elif _is_sep(c):
                if segs < max_segs:
                    phase = 3
                    acc.append(c)
                else:
                    status = 2
            elif c == "/":
                status = 1
            elif c == "\n":
                status = 3
            else:
                status = 2
        else:  # phase == 3
            if _is_word(c):
                phase = 2
                acc.append(c)
                segs += 1
            else:
                status = 2
    # ldecode
    if status == 1:
        return "".join(acc)
    if status == 2:
        return None
    if status == 3:
        return "".join(acc)
    if phase == 2:
        return "".join(acc)
    return None


def oracle_leading_tag(path):
    """patch.diff's behaviour: the patched language_code_prefix_re group(1)."""
    from django.utils.translation.trans_real import language_code_prefix_re
    mo = language_code_prefix_re.match(path)
    if not mo:
        return None
    return mo[1]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the F2P + issue paths.
    boundary = [
        "/pl/", "/pl", "/xyz/", "/en/", "/en-gb/",
        "/en-latn-us/", "/en-Latn-US/", "/de/", "/de-1996/", "/de-at/",
        "/de-ch/", "/de-ch-1901/", "/de-simple-page-test/", "/de-simple-page/",
        "/i-mingo/", "/kl-tunumiit/", "/nan-hani-tw/",
        "", "/", "//", "/a", "/a-", "/-a", "/a@b@c/", "/a-b-c-d/",
        "/en_US/", "/x.y/", "/a b/", "/UPPER-CASE-TAG/",
        # trailing line-terminator boundary: Python `$` matches before a single
        # final '\n', so an otherwise-valid tag immediately followed by exactly
        # one trailing '\n' (and nothing after) is accepted; any further char,
        # or a second '\n', rejects.
        "/en\n", "/en\n/", "/en\n\n", "/en\nx", "/de-ch-1901\n", "/a-b\n",
        "/en-latn-us\n", "/en-latn-us-x\n", "/\n", "/en-\n", "/en/\n",
    ]
    for s in boundary:
        yield s
    # Randomized fuzz over the ASCII langtag domain (mapping.md §2: the carrier
    # is ASCII `List Char` — RFC 5646 langtags, the F2P inputs, and every
    # configured LANGUAGES code are ASCII; Lean `Char.isAlphanum` is ASCII-only,
    # matching the modeled word class on this domain). Alphabet = ASCII word
    # chars + the two subtag separators + path separator + a few non-word ASCII
    # delimiters (so rejection paths are exercised).
    alphabet = list("abZ_09-@/. =x\n")
    for _ in range(n):
        k = rng.randint(0, 14)
        if rng.random() < 0.85:
            s = "/" + "".join(rng.choice(alphabet) for _ in range(k))
        else:
            s = "".join(rng.choice(alphabet) for _ in range(k))
        yield s


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_leading_tag(s, 2)
        oracle = oracle_leading_tag(s)
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
    print("G-CONF OK: R/I shadow of leadingLocaleTag agrees with patch.diff "
          "language_code_prefix_re group(1) on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
