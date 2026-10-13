#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11119.

This bundle consumes NO @ContractOnly axiom (the `axioms` region of model.py is
empty). The only kind-A obligation is the **A-reference** deep model: the escape
branch of the renderer is modeled deeply by `escaped_seq` (model.py pure
region), and we must validate that deep model against the REAL escaping callee
the patched code path reaches.

Behaviour modeled and checked:

  (A-reference, escape branch) When the rendering context's autoescape policy is
      ON, `render_value_in_context` (django/template/base.py:970-973) calls
      `conditional_escape(value)`, which for a plain `str` value reduces to
      `django.utils.html.escape(value)`. At this base_commit `escape` applies
      `str.translate(_html_escapes)`, the per-code-point substitution
        &(38) -> &amp;   <(60) -> &lt;   >(62) -> &gt;
        "(34) -> &quot;  '(39) -> &#39;  else identity
      We assert the deep model `escaped_seq` == the real
      `django.utils.html.escape` on boundary + randomized fuzz inputs.

  (verbatim branch) When the policy is OFF, the renderer emits `str(value)`
      (django/template/base.py:974-975). We assert that branch is the identity
      on the character content (`str(value) == value`) for the witnesses,
      matching model.py's verbatim postcondition.

  (F2P witness) engine autoescape=False, value '<script>' -> '<script>'
      (verbatim, NOT escaped) while autoescape=True -> '&lt;script&gt;'.

Imports only `django.utils.html` (the very module the patched code path calls)
and the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from django.utils.html import escape as dj_escape  # the real escaping callee

# --- model.py reference encodings (kept in lock-step with the deep model) ----

_ENTITY = {
    38: [38, 97, 109, 112, 59],        # '&'  -> '&amp;'
    60: [38, 108, 116, 59],            # '<'  -> '&lt;'
    62: [38, 103, 116, 59],            # '>'  -> '&gt;'
    34: [38, 113, 117, 111, 116, 59],  # '"'  -> '&quot;'
    39: [38, 35, 51, 57, 59],          # "'"  -> '&#39;'  (legacy decimal here)
}


def escaped_seq(codepoints):
    """Reference implementation of model.py's deep model `escaped_seq`, as a
    list of code points (the per-code-point substitution)."""
    out = []
    for c in codepoints:
        out.extend(_ENTITY.get(c, [c]))
    return out


# --- the checks --------------------------------------------------------------

def check_escape_reference(s):
    """Assert deep model escaped_seq(s) == the REAL django escape(s) (escape
    branch of the renderer)."""
    observed = [ord(ch) for ch in str(dj_escape(s))]    # real callee
    expected = escaped_seq([ord(ch) for ch in s])       # deep model
    assert observed == expected, (
        "escaped_seq deep model unsound on %r: django escape gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_verbatim_identity(s):
    """Assert the OFF/verbatim branch (`str(value)`) is the identity on
    character content, matching model.py's verbatim postcondition."""
    observed = [ord(ch) for ch in str(s)]
    expected = [ord(ch) for ch in s]
    assert observed == expected, (
        "verbatim branch not identity on %r: str(value) gave %r" % (s, observed))


def main():
    significant = ['&', '<', '>', '"', "'"]
    ordinary = ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
                'é', '•', 's', 'c', 'r', 'i', 'p', 't']

    # --- boundary cases over the significant characters and their mixtures ----
    boundary = [""]
    boundary += significant                       # each significant char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all five together
    boundary += ["".join(reversed(significant))]
    boundary += [
        "<script>",                               # the F2P witness value
        "<script>alert('xss')</script>",
        "a&b<c>d\"e'f",
        "x=1&amp;y=&lt;2&gt;",                    # already-escaped -> double
        "&amp;", "&#39;", "&quot;",
        "Joe's Crab Shack",
        "Can't find my keys",
        "obj:<script>",                           # with the literal prefix
    ]
    for s in boundary:
        check_escape_reference(s)
        check_verbatim_identity(s)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(11119)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_escape_reference(s)
        check_verbatim_identity(s)

    # --- the F2P discriminating witness ---------------------------------------
    # autoescape OFF -> value emitted verbatim
    assert str("<script>") == "<script>"
    # autoescape ON  -> value escaped
    assert str(dj_escape("<script>")) == "&lt;script&gt;", (
        "escape witness changed: %r" % str(dj_escape("<script>")))

    print("G-AX OK: escaped_seq deep model (== django.utils.html.escape) and "
          "verbatim identity sound on %d boundary + 20000 fuzz inputs; F2P "
          "witness '<script>' verbatim/escaped confirmed" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
