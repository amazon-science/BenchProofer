#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14539.

The model `trim_trailing_punct(middle, trail, decoded_len, kept_len)` models the
trailing-punctuation trim deeply over `List[int]` code points. The two unchanged
callees that produce the two integer parameters are:

    decoded_len = len(html.unescape(middle))                       # the decoder
    kept_len    = len(html.unescape(middle).rstrip(PUNCT))         # + rstrip

This script executes those REAL callees (the stdlib `html.unescape` + `str`
methods — exactly what the patched code calls) on boundary + randomized fuzz
inputs and checks two things:

  (A-reference, precondition facts)  the relationship the model's `Requires`
      assumes between `decoded_len`, `kept_len`, and `len(middle)` actually holds
      for the real callees:
        0 <= decoded_len <= len(middle)      (decoding never lengthens)
        0 <= kept_len   <= decoded_len       (rstrip never lengthens)

  (A-reference, end-to-end)  feeding the REAL callee outputs into the model's
      slicing reproduces the GOLD patched code's (middle, trail) result exactly,
      AND — on inputs where the encoded form is longer than the decoded form
      (markup entities present and trimmed) — differs from the PRE-FIX code,
      i.e. the spec genuinely discriminates the bug.

Imports only the standard library (`html`), the very module the patch calls.
Exit 0 iff every obligation holds.
"""
import html
import random
import sys

TRAILING_PUNCTUATION_CHARS = '.,:;!'


# --- reference implementation of model.py's deep slicing (over code points) ---

def model_trim(middle, trail, decoded_len, kept_len):
    """model.py `trim_trailing_punct` as code-point lists. Precondition: this is
    only called when kept_len < decoded_len (some trailing punctuation found)."""
    punctuation_count = decoded_len - kept_len
    split = len(middle) - punctuation_count
    moved = middle[split:]
    new_trail = moved + trail
    new_middle = middle[:split]
    return new_middle, new_trail


# --- the GOLD patched code (django/utils/html.py, post-patch) -----------------

def gold_trim(middle, trail):
    """Exact transcription of the post-fix trailing-trim block (on str)."""
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    if middle_unescaped != stripped:
        punctuation_count = len(middle_unescaped) - len(stripped)
        trail = middle[-punctuation_count:] + trail
        middle = middle[:-punctuation_count]
    return middle, trail


# --- the PRE-FIX code (the bug) -----------------------------------------------

def prefix_trim(middle, trail):
    """Exact transcription of the pre-fix trailing-trim block (on str)."""
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    if middle_unescaped != stripped:
        trail = middle[len(stripped):] + trail
        middle = middle[:len(stripped) - len(middle_unescaped)]
    return middle, trail


def to_cp(s):
    return [ord(ch) for ch in s]


def check_one(middle, trail):
    """Run all obligations on one (middle, trail) str pair."""
    middle_unescaped = html.unescape(middle)
    stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)
    decoded_len = len(middle_unescaped)
    kept_len = len(stripped)

    # (A-reference precondition facts) the bounds the model's Requires assume.
    assert 0 <= decoded_len <= len(middle), (
        "decode lengthened %r: len(unescape)=%d > len(middle)=%d"
        % (middle, decoded_len, len(middle)))
    assert 0 <= kept_len <= decoded_len, (
        "rstrip lengthened %r: kept=%d > decoded=%d"
        % (middle, kept_len, decoded_len))

    if not (kept_len < decoded_len):
        # No trailing punctuation: the patched block is skipped; the model's
        # Requires(kept_len < decoded_len) is not entered. Nothing to compare.
        return False

    # (A-reference end-to-end) model output == gold patched code output.
    m_mid, m_trail = model_trim(to_cp(middle), to_cp(trail), decoded_len, kept_len)
    g_mid, g_trail = gold_trim(middle, trail)
    assert m_mid == to_cp(g_mid), (
        "model new_middle != gold on middle=%r trail=%r: %r vs %r"
        % (middle, trail, m_mid, to_cp(g_mid)))
    assert m_trail == to_cp(g_trail), (
        "model new_trail != gold on middle=%r trail=%r: %r vs %r"
        % (middle, trail, m_trail, to_cp(g_trail)))
    return True


def main():
    rng = random.Random(14539)

    # --- boundary cases -------------------------------------------------------
    # The issue example + entity-bearing middles where encoded length exceeds
    # decoded length (these are exactly the inputs the bug mishandles), plus
    # plain trailing-punctuation cases with no entities.
    boundary = [
        ("google.com/?q=1&lt!", ""),
        ("example.com.", ""),
        ("example.com&gt;;", ""),
        ("foo.com!!!", ")"),
        ("a.com&amp;.", "abc"),
        ("&lt;&gt;!!", "X"),
        ("&amp;&amp;&amp;;", ""),
        ("x&lt;y&gt;z.,:;!", "tail"),
        ("plain.text;", ""),
        ("&#x27;quote'.", ""),
        ("no_punct_here", ""),       # kept_len == decoded_len: block skipped
        ("", ""),                    # empty: block skipped
        ("....", ""),                # all punctuation
        ("&amp;.", "&gt;"),
    ]
    discriminated = 0
    compared = 0
    for middle, trail in boundary:
        if check_one(middle, trail):
            compared += 1
            # Confirm the spec genuinely discriminates the bug where entities
            # make the encoded form longer than the decoded form.
            if html.unescape(middle) != middle:
                if prefix_trim(middle, trail) != gold_trim(middle, trail):
                    discriminated += 1
    assert discriminated >= 1, (
        "no boundary input discriminated the bug (gold == prefix everywhere)")

    # --- randomized fuzz ------------------------------------------------------
    entities = ["&lt;", "&gt;", "&amp;", "&quot;", "&#x27;", "&#39;"]
    fillers = list("abcdefghijklmnopqrstuvwxyz.@:/?=0123456789") + \
        list(TRAILING_PUNCTUATION_CHARS) + entities
    fuzz_discriminated = 0
    for _ in range(50000):
        n = rng.randint(0, 12)
        middle = "".join(rng.choice(fillers) for _ in range(n))
        m = rng.randint(0, 4)
        trail = "".join(rng.choice(fillers) for _ in range(m))
        did = check_one(middle, trail)
        if did and html.unescape(middle) != middle:
            if prefix_trim(middle, trail) != gold_trim(middle, trail):
                fuzz_discriminated += 1

    print("G-AX OK: trim_trailing_punct deep model == gold patched code over "
          "%d boundary (%d entered the trim branch) + 50000 fuzz inputs; "
          "callee bounds (0<=decoded<=len(middle), 0<=kept<=decoded) hold on "
          "the real html.unescape+rstrip; bug discriminated on %d boundary + "
          "%d fuzz entity-bearing inputs."
          % (len(boundary), compared, discriminated, fuzz_discriminated))
    return 0


if __name__ == "__main__":
    sys.exit(main())
