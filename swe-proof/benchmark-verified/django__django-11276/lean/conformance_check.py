#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11276.

The bundle models ONE thing: `escape(text)` in `django/utils/html.py`, which the
gold patch rewrites from `str(text).translate(_html_escapes)` to
`html.escape(str(text))` (mapping.md). `mark_safe` and `str(text)` are
character-preserving identities outside the modeled boundary.

* ORACLE — the POST-PATCH behaviour: the real Python stdlib `html.escape(s)`
  (default `quote=True`), which is exactly what the patched body calls. Driven
  directly — no re-implementation.
* SHADOW — the op-for-op transliteration of `implementation_escape`
  (Solution.lean impl region), per refinement.md (rows 1-5): accumulate, for
  each code point, its per-character HTML encoding `escapeChar`.

We diff SHADOW vs ORACLE over an edge set (incl. the F2P apostrophe strings)
plus >=10^5 fuzzed inputs over an alphabet stressing the five HTML-significant
characters and ordinary text. Exit 0 iff zero disagreements.

stdlib-only. Pinned seed: 11276 (also in mapping.md).
"""
import html
import random
import sys

SEED = 11276
N = 150_000


def oracle(s: str) -> str:
    """Post-patch semantics: the real stdlib escaper with its default quote=True."""
    return html.escape(s)


# --- SHADOW of implementation_escape (the R/I + A-reference legs) -------------
def escape_char(c: str) -> str:
    # escapeChar: the five HTML-significant code points -> entity, else identity.
    if c == '&':
        return '&amp;'
    if c == '<':
        return '&lt;'
    if c == '>':
        return '&gt;'
    if c == '"':
        return '&quot;'
    if c == "'":
        return '&#x27;'
    return c


def shadow(s: str) -> str:
    acc = ''
    for c in s:                 # for c in s do
        acc = acc + escape_char(c)   # acc := acc ++ escapeChar c
    return acc


def disagree(s):
    got, want = oracle(s), shadow(s)
    if got != want:
        return (s, got, want)
    return None


def _edge_cases():
    return [
        "",                        # empty -> empty
        "'",                       # apostrophe -> &#x27;  (the F2P change)
        "Joe's",                   # -> Joe&#x27;s          (test_title1)
        "<a>'",                    # -> &lt;a&gt;&#x27;     (test_addslashes02)
        "&",                       # -> &amp;              (test_make_list02)
        "\"",                      # -> &quot;
        "<",                       # -> &lt;
        ">",                       # -> &gt;
        "&<>\"'",                  # all five, in order
        "<script>alert('foo')</script>",  # test_urlize06
        "Can't find my keys",      # test_message_only
        "a&amp;b",                 # already-escaped -> re-escaped
        "no special chars here",   # identity
        "''''",                    # repeated apostrophes
        "&&&",                     # repeated ampersands
        "é•",            # non-ASCII passthrough (é, bullet)
    ]


def main() -> int:
    checked = 0
    for s in _edge_cases():
        d = disagree(s)
        if d:
            print(f"DISAGREE edge: in={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    # Alphabet stressing the five HTML-significant characters plus ordinary text,
    # whitespace, and some non-ASCII code points (which must pass through).
    alphabet = list("&<>\"'") + list("abcXYZ019 \t\n") + ["é", "•", "\U0001F600"]
    for _ in range(N):
        n = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        d = disagree(s)
        if d:
            print(f"DISAGREE fuzz: in={d[0]!r} oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"status=pass checked={checked}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
