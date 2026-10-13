#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14539.

`Solution.lean` models the HTML entity decoder as the OPAQUE callee
`entityDecode` (no value-level axioms about it) and models the changed slicing
operation DEEPLY (`stripTrailingPunct` / `trailingPunctCount` and the
`take`/`drop` peel).  This file executes the REAL stdlib callee `html.unescape`
(the function the gold patch's `html.unescape(middle)` invokes) and the real
`str.rstrip(TRAILING_PUNCTUATION_CHARS)`, and asserts the soundness obligations
the refinement relies on:

  (A-reference 1) `entityDecode` ≡ `html.unescape`.  The decoder NEVER LENGTHENS
      its input: ``len(html.unescape(s)) <= len(s)`` for every s.  This is the
      property that makes the Lean spec's truncated Nat subtraction
      ``token.length - trailingPunctCount token`` EXACT rather than spuriously
      clamped — i.e. the peeled punctuation count never exceeds the encoded
      token length.  If this failed, `token.drop (len - count)` could drop the
      wrong amount and the deep model would be unsound.

  (A-reference 2) the deep model `stripTrailingPunct` ≡ Python
      ``str.rstrip(TRAILING_PUNCTUATION_CHARS)`` on the decoded string, and the
      derived `trailingPunctCount` ≡ ``len(decoded) - len(decoded.rstrip(...))``
      — the count the gold patch computes (`punctuation_count`).

  (A-reference 3) end-to-end: the deep-model peel
      ``token[:len-count], token[len-count:]`` reproduces the gold-patched
      trailing-punctuation block's ``middle, trail`` on every observation.

Imports only the Python standard library `html` — the same module the gold
patch calls.  Exit 0 iff every obligation holds.
"""
import html
import random
import sys

TRAILING_PUNCTUATION_CHARS = '.,:;!'


# --- deep-model reference encodings (lock-step with Solution.lean) -----------
def strip_trailing_punct(s):
    """stripTrailingPunct: (s.reverse.dropWhile isTrailingPunct).reverse."""
    rev = list(reversed(s))
    i = 0
    while i < len(rev) and rev[i] in TRAILING_PUNCTUATION_CHARS:
        i += 1
    return "".join(reversed(rev[i:]))


def trailing_punct_count(token):
    """trailingPunctCount: len(decode) - len(strip(decode))."""
    decoded = html.unescape(token)
    return len(decoded) - len(strip_trailing_punct(decoded))


# --- the checks --------------------------------------------------------------
def check_decoder_non_lengthening(s):
    """A-reference 1: html.unescape never lengthens; count <= len(token)."""
    decoded = html.unescape(s)
    assert len(decoded) <= len(s), (
        "html.unescape LENGTHENED %r -> %r (len %d > %d): truncated Nat "
        "subtraction in the spec would be unsound"
        % (s, decoded, len(decoded), len(s)))
    assert trailing_punct_count(s) <= len(s), (
        "trailing_punct_count(%r)=%d exceeds token length %d"
        % (s, trailing_punct_count(s), len(s)))


def check_strip_model(s):
    """A-reference 2: stripTrailingPunct model == real str.rstrip."""
    model = strip_trailing_punct(s)
    real = s.rstrip(TRAILING_PUNCTUATION_CHARS)
    assert model == real, (
        "stripTrailingPunct model unsound on %r: model=%r rstrip=%r"
        % (s, model, real))


def deep_peel(token, tail):
    """The deep-model peel of Solution.lean."""
    count = trailing_punct_count(token)
    decoded = html.unescape(token)
    if decoded != strip_trailing_punct(decoded):
        cut = len(token) - count
        return token[:cut], token[cut:] + tail
    return token, tail


def gold_peel(middle, trail):
    """The gold-patched trailing-punct block (html.py:283-288 post-patch)."""
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    if middle_unescaped != stripped:
        punctuation_count = len(middle_unescaped) - len(stripped)
        trail = middle[-punctuation_count:] + trail
        middle = middle[:-punctuation_count]
    return middle, trail


def check_peel_reference(token, tail):
    """A-reference 3: deep-model peel == gold-patched block."""
    model = deep_peel(token, tail)
    gold = gold_peel(token, tail)
    assert model == gold, (
        "deep-model peel unsound on token=%r tail=%r: model=%r gold=%r"
        % (token, tail, model, gold))


def main():
    entities = ['&lt;', '&gt;', '&amp;', '&quot;', '&#x27;', '&#39;',
                '&period;', '&excl;', '&comma;', '&semi;', '&colon;', '&#33;',
                '&nbsp;', '&copy;']
    puncts = list(TRAILING_PUNCTUATION_CHARS)
    ordinary = list('abcXYZ09/=?_&;#') + ['é', '•']

    boundary = [
        '', 'google.com/?q=1&lt!', 'google.com/?q=!', 'plain.', 'a&lt;b!!',
        '&lt;&lt;!', 'foo&semi;', 'a&gt;.', 'foo&period;', '&amp;.', ';;;',
        'no_punct_here', '&lt;', '!!!', '&lt;;', 'x&comma;y', '&#x27;!',
        '&amp;&amp;.', 'a;b;c', '<&>', 'café!', '&copy;.',
    ]
    for s in boundary:
        check_decoder_non_lengthening(s)
        check_strip_model(s)
    for s in boundary:
        for tail in ['', 'X', '</a>']:
            check_peel_reference(s, tail)

    rng = random.Random(14539)
    alphabet = ordinary + puncts + entities
    N = 20000
    for _ in range(N):
        k = rng.randint(0, 8)
        token = "".join(rng.choice(alphabet) for _ in range(k))
        check_decoder_non_lengthening(token)
        check_strip_model(token)
        tail = rng.choice(['', 'Y', '!Z'])
        check_peel_reference(token, tail)

    print("G-AX OK: html.unescape non-lengthening + stripTrailingPunct model "
          "== str.rstrip + deep-model peel == gold block, sound on %d boundary "
          "+ %d fuzz inputs." % (len(boundary), N))
    return 0


if __name__ == "__main__":
    sys.exit(main())
