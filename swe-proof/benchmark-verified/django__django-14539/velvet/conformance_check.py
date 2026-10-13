#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14539 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`peelTrailingPunctuation`) transliterated to Python over the real
              repo type (`str`), via the mapping.md bijection
              (`List Char` ↔ `str`).  The single A-tagged callee `entityDecode`
              is LEFT AS THE REAL REPO CALLEE `html.unescape` (worker rule:
              A-tagged callees run the real callee in G-CONF, not an axiom
              model).  Note `stripTrailingPunct` is transliterated faithfully to
              the Lean model (reverse / drop-while / reverse), NOT as `.rstrip`,
              so the differential genuinely exercises the model.

  * ORACLE  — `patch.diff`'s behaviour: the trailing-punctuation trimming block
              of the gold-patched `trim_punctuation` (django/utils/html.py,
              lines 283-288 post-patch) executed verbatim.  `trim_punctuation`
              is a closure nested inside `urlize`, so it cannot be imported; the
              oracle replicates the gold-patched lines verbatim (the same lines
              the harness applies, and that G-RESOLVE confirms `resolved`).  An
              end-to-end anchor against the real patched `urlize` is run first
              on the issue's own example for independent confidence.

They must agree on every input (this single-step peel has no precondition).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib only.  The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import html
import random
import sys

SEED = 14539
N_FUZZ = 100_000

TRAILING_PUNCTUATION_CHARS = '.,:;!'   # django.utils.html module constant


# --- the R/I shadow: Solution.lean peelTrailingPunctuation, transliterated ---
def _is_trailing_punct(ch):
    # isTrailingPunct (c : Char)
    return ch in TRAILING_PUNCTUATION_CHARS


def _strip_trailing_punct(s):
    # stripTrailingPunct : (s.reverse.dropWhile isTrailingPunct).reverse
    rev = list(reversed(s))
    i = 0
    while i < len(rev) and _is_trailing_punct(rev[i]):
        i += 1
    return "".join(reversed(rev[i:]))


def shadow_peel(token, tail):
    """peelTrailingPunctuation (token, tail) transliterated to str.
    entityDecode is the REAL callee html.unescape (A-tagged -> real)."""
    decoded = html.unescape(token)                 # A: real repo callee
    stripped = _strip_trailing_punct(decoded)
    punctuation_count = len(decoded) - len(stripped)
    core = token
    new_tail = tail
    if decoded != stripped:
        # token.take (len - pc) ; token.drop (len - pc) ++ tail
        cut = len(token) - punctuation_count
        core = token[:cut]
        new_tail = token[cut:] + tail
    return core, new_tail


# --- the oracle: patch.diff's gold-patched trailing-punct block --------------
def oracle_peel(middle, trail):
    """The gold-patched trailing-punctuation trimming block of
    trim_punctuation (django/utils/html.py:283-288 post-patch), verbatim."""
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    if middle_unescaped != stripped:
        punctuation_count = len(middle_unescaped) - len(stripped)
        trail = middle[-punctuation_count:] + trail
        middle = middle[:-punctuation_count]
    return middle, trail


def _anchor():
    """Independent end-to-end anchor: the real patched urlize on the issue's
    own example must produce the expected output (G-RESOLVE territory)."""
    try:
        from django.utils.html import urlize
    except Exception as e:                       # pragma: no cover
        print("G-CONF note: could not import urlize for anchor (%r); "
              "continuing with block-level oracle." % (e,))
        return True
    got = urlize('Search for google.com/?q=1&lt! and see.')
    want = ('Search for <a href="http://google.com/?q=1%3C">'
            'google.com/?q=1&lt</a>! and see.')
    if got != want:
        print("G-CONF FAIL (anchor): urlize gave %r, expected %r" % (got, want))
        return False
    return True


def fuzz_inputs(n, rng):
    # tokens crafted to exercise entity / trailing-punct interaction
    entities = ['&lt;', '&gt;', '&amp;', '&quot;', '&#x27;', '&period;',
                '&excl;', '&comma;', '&semi;', '&#33;']
    puncts = list(TRAILING_PUNCTUATION_CHARS)
    ordinary = list('abcXYZ09/=?_&;#') + ['é']
    alphabet = ordinary + puncts + entities

    # boundary cases first
    yield from [
        ('', ''),
        ('google.com/?q=1&lt!', ''),
        ('google.com/?q=!', ''),
        ('plain.', 'TRAIL'),
        ('a&lt;b!!', ''),
        ('&lt;&lt;!', ''),
        ('foo&semi;', ''),
        ('a&gt;.', ''),
        ('foo&period;', ''),
        ('&amp;.', ''),
        (';;;', ''),
        ('no_punct_here', ''),
        ('&lt;', '!'),
        ('!!!', 'X'),
        ('&lt;;', ''),
    ]
    for _ in range(n):
        k = rng.randint(0, 8)
        parts = [rng.choice(alphabet) for _ in range(k)]
        token = "".join(parts)
        tail = rng.choice(['', 'X', '!Y', '</a>'])
        yield (token, tail)


def main():
    if not _anchor():
        return 1
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for token, tail in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow_peel(token, tail)
        orc = oracle_peel(token, tail)
        if sh != orc:
            disagreements.append((token, tail, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for token, tail, sh, orc in disagreements:
            print("  token=%r tail=%r shadow=%r oracle=%r"
                  % (token, tail, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of peelTrailingPunctuation agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
