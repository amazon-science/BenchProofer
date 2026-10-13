#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11276.

Executes the REAL stdlib callees (`html.escape`, `html.unescape`) on inputs
(boundary cases over the five significant characters and their mixtures, plus
randomized fuzzing) and asserts that every observation matches the model, as
encoded in model.py.

The two kind-A checks:

  (A-reference) the deep model `escaped_seq` (model.py pure region) == the real
      `html.escape`. The escaper's changed string operation is modeled DEEPLY,
      not behind a consumed axiom; G-AX validates that deep model against the
      real callee:
        &(38) -> &amp;      <(60) -> &lt;     >(62) -> &gt;
        "(34) -> &quot;     '(39) -> &#x27;   else identity
      (ampersand first, so emitted '&' are not re-escaped).

  (A-consumed) the `entity_decode` axiom (model.py axioms region) inverts the
      five emitted entities (and the legacy decimal apostrophe '&#39;'):
        &amp;  -> &(38)   &lt;  -> <(60)   &gt;   -> >(62)
        &quot; -> "(34)   &#x27;-> '(39)   &#39;  -> '(39)

Imports nothing repo-specific: `html` is the Python standard library — the same
module the gold patch calls. Exit 0 iff every obligation holds.
"""
import html
import random
import sys

# --- model.py reference encodings (kept in lock-step with the axioms) --------

_ENTITY = {
    38: [38, 97, 109, 112, 59],      # '&'  -> '&amp;'
    60: [38, 108, 116, 59],          # '<'  -> '&lt;'
    62: [38, 103, 116, 59],          # '>'  -> '&gt;'
    34: [38, 113, 117, 111, 116, 59],  # '"'  -> '&quot;'
    39: [38, 35, 120, 50, 55, 59],   # "'"  -> '&#x27;'
}

# entity_decode: the six entity tokens -> single decoded code point
_DECODE = {
    "&amp;": 38,
    "&lt;": 60,
    "&gt;": 62,
    "&quot;": 34,
    "&#x27;": 39,   # the apostrophe entity emitted by the new escaper
    "&#39;": 39,    # legacy decimal apostrophe entity
}


def escaped_seq(codepoints):
    """Reference implementation of model.py's deep model `escaped_seq`, as a
    list of code points (the per-code-point substitution, ampersand-first)."""
    out = []
    for c in codepoints:
        out.extend(_ENTITY.get(c, [c]))
    return out


# --- the checks --------------------------------------------------------------

def check_escape_reference(s):
    """Assert the deep model escaped_seq(s) == the REAL html.escape(s)."""
    observed = [ord(ch) for ch in html.escape(s)]            # real callee
    expected = escaped_seq([ord(ch) for ch in s])            # deep model
    assert observed == expected, (
        "escaped_seq deep model unsound on %r: html.escape gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_decode_axiom(token, expected_codepoint):
    """Assert entity_decode(token) == [expected] on the REAL html.unescape."""
    observed = [ord(ch) for ch in html.unescape(token)]      # real callee
    expected = [expected_codepoint]                          # axiom Ensures
    assert observed == expected, (
        "entity_decode axiom unsound on %r: html.unescape gave %r, "
        "axiom requires %r" % (token, observed, expected))


def main():
    significant = ['&', '<', '>', '"', "'"]
    ordinary = ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
                'é', '•', 'q', 'u', 'o', 't', 'l', 'g', 'm', 'p']

    # --- escaped_seq deep model (A-reference): boundary cases --------------
    boundary = [""]
    boundary += significant                       # each significant char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all five together
    boundary += ["".join(reversed(significant))]
    # mixtures with ordinary text and with already-escaped sequences
    boundary += [
        "a&b<c>d\"e'f",
        "x=1&amp;y=&lt;2&gt;",      # already-escaped input must double-escape
        "&amp;", "&#39;", "&#x27;", "&quot;",
        "Joe's Crab Shack",
        "<script>alert('xss')</script>",
        "Can't find my keys",
        "!$&'()*+,;=~:@,",
    ]
    for s in boundary:
        check_escape_reference(s)

    # --- escaped_seq deep model (A-reference): randomized fuzz -------------
    rng = random.Random(11276)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_escape_reference(s)

    # --- entity_decode (A-consumed): every token in the axiom's Ensures ----
    for token, cp in _DECODE.items():
        check_decode_axiom(token, cp)

    # round-trip witness: escaping then decoding each significant char is id
    for ch in significant:
        esc = html.escape(ch)                     # e.g. "'" -> "&#x27;"
        assert html.unescape(esc) == ch, (
            "round trip broken for %r: escape=%r unescape=%r"
            % (ch, esc, html.unescape(esc)))

    print("G-AX OK: escaped_seq deep model (== html.escape) + entity_decode "
          "axiom sound on %d boundary + 20000 fuzz escape inputs and %d "
          "decode tokens" % (len(boundary), len(_DECODE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
