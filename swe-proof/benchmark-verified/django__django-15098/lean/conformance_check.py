#!/usr/bin/env python3
"""G-CONF — mechanical cross-language differential test for django__django-15098.

The single changed op in `implementation_langCodeFromPath` is the URL-path
language-prefix matcher (Solution.lean's `langPrefix` = `langPrefixN 2`), which
deep-models group 1 of the post-patch regex

    language_code_prefix_re = ^/(\\w+([@-]\\w+){0,2})(/|$)

The downstream callee `resolveVariant` (= `get_supported_language_variant`) is
UNCHANGED and is invoked identically on both sides of the spec; it is an A-tagged
reference, so the R/I behavior under test is the candidate-extraction (group 1).

This script rebuilds the R/I shadow of the impl in Python — `langPrefixN(n, path)`
mirroring Solution.lean's `langPrefixN`/`grabSubtags`/`isWord`/`isSep` — and
diffs it against the REAL `re` engine for BOTH the post-patch matcher (n=2) and
the pre-patch matcher (n=1), over >=10^5 fuzzed paths. Exit 0 iff zero
disagreements. stdlib-only.
"""
import re
import random
import string
import sys

POST_RE = re.compile(r'^/(\w+([@-]\w+){0,2})(/|$)')
PRE_RE = re.compile(r'^/(\w+([@-]\w+)?)(/|$)')
CONF_SEED = 15098
N_FUZZ = 200_000


# ---- R/I shadow of Solution.lean (langPrefixN / grabSubtags / isWord / isSep) ----
def is_word(c: str) -> bool:
    # ASCII \w: letter, digit, or underscore (mapping.md flag dep)
    return c.isascii() and (c.isalpha() or c.isdigit() or c == '_')


def is_sep(c: str) -> bool:
    return c == '-' or c == '@'


def grab_subtags(n: int, s: str):
    """Greedily consume up to n trailing subtags (sep + non-empty word run)."""
    consumed = []
    i = 0
    while n > 0 and i < len(s):
        if not is_sep(s[i]):
            break
        j = i + 1
        w = []
        while j < len(s) and is_word(s[j]):
            w.append(s[j])
            j += 1
        if not w:
            break
        consumed.append(s[i])
        consumed.extend(w)
        i = j
        n -= 1
    return ''.join(consumed), s[i:]


def lang_prefix_n(n: int, path: str):
    if not path or path[0] != '/':
        return None
    rest = path[1:]
    k = 0
    while k < len(rest) and is_word(rest[k]):
        k += 1
    seg0 = rest[:k]
    r0 = rest[k:]
    if seg0 == '':
        return None
    subs, rrest = grab_subtags(n, r0)
    # terminator: '/' , end of path, or a single trailing line-terminator
    # (the end-of-input anchor convention of the host pattern language)
    if rrest == '' or rrest[0] == '/' or rrest == '\n':
        return seg0 + subs
    return None


# ---- the real re engine: group 1 (or None) ----
def real_group1(rx, path):
    m = rx.match(path)
    return m[1] if m else None


def main() -> int:
    rng = random.Random(CONF_SEED)
    # the modeled domain is the ASCII plane; fuzz over a langtag-shaped
    # alphabet (dense hits) AND over full ASCII (code points 0-127)
    alphabet = string.ascii_letters + string.digits + '_-@/'
    full_ascii = ''.join(chr(i) for i in range(128))
    mismatches = 0
    examples = []
    # boundary corpus
    corpus = [
        '', '/', '//', '/pl/', '/pl', '/xyz/', '/en/', '/en-gb/',
        '/en-latn-us/', '/en-Latn-US/', '/de/', '/de-1996/', '/de-at/',
        '/de-ch/', '/de-ch-1901/', '/de-simple-page-test/', '/de-simple-page/',
        '/i-mingo/', '/kl-tunumiit/', '/nan-hani-tw/', '/de-/', '/de-ch-',
        '/a-b-c-d/', '/_x/', '/a@b/', '/a@b@c/', '/a@b-c/', 'no-slash', '/a//',
        # end-of-input anchor boundaries: a single trailing line-terminator is
        # admitted; anything after it (or a second one) is not
        '/en\n', '/en\nx', '/en\n\n', '/en-gb\n', '/en-latn-us\n', '/en-\n',
        '/en@\n', '/en\r', '/en\r\n', '/\n', '/en/\n', '/en.\n', '/en \n',
    ]
    for path in corpus:
        for n, rx in ((2, POST_RE), (1, PRE_RE)):
            got = lang_prefix_n(n, path)
            exp = real_group1(rx, path)
            if got != exp:
                mismatches += 1
                if len(examples) < 12:
                    examples.append((n, path, got, exp))
    for i in range(N_FUZZ):
        L = rng.randint(0, 14)
        src = alphabet if i % 2 == 0 else full_ascii
        path = ''.join(rng.choice(src) for _ in range(L))
        for n, rx in ((2, POST_RE), (1, PRE_RE)):
            got = lang_prefix_n(n, path)
            exp = real_group1(rx, path)
            if got != exp:
                mismatches += 1
                if len(examples) < 12:
                    examples.append((n, path, got, exp))

    if mismatches:
        print(f"G-CONF FAIL: {mismatches} disagreement(s)")
        for n, p, g, e in examples:
            print(f"  n={n} path={p!r} shadow={g!r} real={e!r}")
        return 1
    print(f"G-CONF pass: 0 disagreements over {N_FUZZ} fuzzed + "
          f"{len(corpus)} boundary paths x {{pre,post}} matchers")
    return 0


if __name__ == '__main__':
    sys.exit(main())
