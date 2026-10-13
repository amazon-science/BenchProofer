#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11119.

Executes the REAL escaping callee that `Engine.render_to_string`'s rendering
path delegates to and asserts the deep model `escaped_seq` matches it.

The rendering path is: a context value is displayed by
`django.template.base.render_value_in_context`, whose escaping branch
(`if context.autoescape:`) calls `conditional_escape(str(value))`. For a plain
`str` value (the F2P input domain — not a `Promise`, not `SafeData`/`__html__`)
`conditional_escape` reduces to `django.utils.html.escape`, which at this
base_commit is `str(text).translate(_html_escapes)` with

    & -> &amp;   < -> &lt;   > -> &gt;   " -> &quot;   ' -> &#39;

every other code point passing through. `str.translate` is a single-pass,
per-code-point substitution, so it equals the model `escaped_seq`/`entity`.

  (A-reference) the deep model `escaped_seq` (Solution.lean pure region) ==
      the real `django.utils.html.escape` (and the real `conditional_escape`)
      on plain `str` values.

NB: at THIS commit the apostrophe maps to the LEGACY decimal reference '&#39;'
(the switch to '&#x27;' is a later Django change — instance 11276 — and must
NOT be assumed here). G-AX pins '&#39;' and would fail if the model used
'&#x27;'.

Imports only `django.utils.html` (the repo's own escaping module, in-container).
Exit 0 iff every obligation holds.
"""
import random
import sys

# --- Solution.lean reference encodings (kept in lock-step with `entity`) -----
# entity (c : Char) : List Char  -- per-code-point substitution, legacy '&#39;'.
_ENTITY = {
    38: [38, 97, 109, 112, 59],          # '&'  -> '&amp;'
    60: [38, 108, 116, 59],              # '<'  -> '&lt;'
    62: [38, 103, 116, 59],              # '>'  -> '&gt;'
    34: [38, 113, 117, 111, 116, 59],    # '"'  -> '&quot;'
    39: [38, 35, 51, 57, 59],            # "'"  -> '&#39;'  (legacy decimal)
}


def escaped_seq(codepoints):
    """Reference implementation of Solution.lean's deep model `escapedSeq`, as a
    list of code points (the per-code-point substitution)."""
    out = []
    for c in codepoints:
        out.extend(_ENTITY.get(c, [c]))
    return out


def check_escape_reference(s):
    """Assert escaped_seq(s) == the REAL escape(s) AND conditional_escape(s)."""
    from django.utils.html import escape, conditional_escape
    observed_escape = [ord(ch) for ch in escape(s)]              # real callee
    observed_cond = [ord(ch) for ch in conditional_escape(s)]    # rendering path
    expected = escaped_seq([ord(ch) for ch in s])                # deep model
    assert observed_escape == expected, (
        "escaped_seq deep model unsound on %r: html.escape gave %r, "
        "deep model gives %r" % (s, observed_escape, expected))
    assert observed_cond == expected, (
        "escaped_seq deep model unsound on %r: conditional_escape gave %r, "
        "deep model gives %r" % (s, observed_cond, expected))


def main():
    significant = ['&', '<', '>', '"', "'"]
    ordinary = ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
                'é', '•', 'q', 'u', 'o', 't', 'l', 'g', 'm', 'p', 's',
                'c', 'r', 'i', 'p']

    # --- boundary cases ---------------------------------------------------
    boundary = [""]
    boundary += significant                       # each significant char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all five together
    boundary += ["".join(reversed(significant))]
    boundary += [
        "a&b<c>d\"e'f",
        "<script>alert('xss')</script>",          # the F2P-shaped markup
        "<script>",                               # exact F2P value
        "x=1&amp;y=&lt;2&gt;",                    # already-escaped input doubles
        "&amp;", "&#39;", "&quot;",
        "Joe's Crab Shack",
        "Can't find my keys",
        "!$&'()*+,;=~:@,",
    ]
    for s in boundary:
        check_escape_reference(s)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(11119)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_escape_reference(s)

    print("G-AX OK: escaped_seq deep model (== django.utils.html.escape and "
          "conditional_escape, legacy '&#39;') sound on %d boundary + 20000 "
          "fuzz inputs" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
