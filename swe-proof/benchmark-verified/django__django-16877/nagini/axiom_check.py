#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16877.

The model has NO consumed @ContractOnly axiom. The one kind-A obligation is an
A-reference: the deep model `escaped_seq` (model.py pure region) is the escape
applied per element when an item is NOT already marked safe, and it must equal
the REAL escaper the gold patch invokes through `conditional_escape`.

The gold filter is `[conditional_escape(obj) for obj in value]`. For each item:

  (A-reference, unsafe branch) an item that is NOT a safe string is escaped by
      `conditional_escape(obj) == escape(obj) == SafeString(html.escape(str(obj)))`.
      The deep model `escaped_seq` must equal `html.escape` (quote=True, the
      CPython default that Django relies on) on the item's code points:
        &(38) -> &amp;      <(60) -> &lt;     >(62) -> &gt;
        "(34) -> &quot;     '(39) -> &#x27;   else identity
      (ampersand first, so emitted '&' are not re-escaped).

  (passthrough, safe branch) an item that IS a safe string (exposes the
      `__html__` convention, like Django's SafeString / markupsafe) is returned
      UNCHANGED by `conditional_escape` -- never re-escaped. We model this with a
      minimal `__html__`-bearing object and assert `conditional_escape` is the
      identity on its content.

This check imports the Python standard library `html` (the very module the gold
patch's escape path calls) and re-implements `conditional_escape`'s observable
contract via the public `__html__` convention; it imports nothing repo-specific
so it runs even outside the Django source tree. When run in the SWE-bench
container the real `django.utils.html.conditional_escape` is additionally
exercised if importable. Exit 0 iff every obligation holds.
"""
import html
import random
import sys

# --- model.py reference encodings (kept in lock-step with the deep model) -----

_ENTITY = {
    38: [38, 97, 109, 112, 59],        # '&'  -> '&amp;'
    60: [38, 108, 116, 59],            # '<'  -> '&lt;'
    62: [38, 103, 116, 59],            # '>'  -> '&gt;'
    34: [38, 113, 117, 111, 116, 59],  # '"'  -> '&quot;'
    39: [38, 35, 120, 50, 55, 59],     # "'"  -> '&#x27;'
}


def escaped_seq(codepoints):
    """Reference implementation of model.py's deep model `escaped_seq`, as a
    list of code points (the per-code-point substitution, ampersand-first)."""
    out = []
    for c in codepoints:
        out.extend(_ENTITY.get(c, [c]))
    return out


class _SafeLike(str):
    """A minimal already-safe string mirroring Django's SafeString / the
    `__html__` convention `conditional_escape` keys on."""
    def __html__(self):
        return self


def _conditional_escape_contract(obj):
    """The observable contract of `conditional_escape`: pass through anything
    exposing `__html__` unchanged; otherwise escape via the stdlib escaper."""
    if hasattr(obj, "__html__"):
        return obj.__html__()
    return html.escape(str(obj))


# --- the checks ---------------------------------------------------------------

def check_escape_reference(s):
    """Assert the deep model escaped_seq(s) == the REAL html.escape(s) (the
    unsafe-item escape branch of conditional_escape)."""
    observed = [ord(ch) for ch in html.escape(s)]            # real callee
    expected = escaped_seq([ord(ch) for ch in s])            # deep model
    assert observed == expected, (
        "escaped_seq deep model unsound on %r: html.escape gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_conditional_escape(s):
    """Cross-check against conditional_escape's contract on BOTH branches:
    a plain str is escaped (== deep model); a safe string passes through."""
    # unsafe item: escaped, and equal to the deep model
    ce_plain = _conditional_escape_contract(s)
    assert [ord(c) for c in ce_plain] == escaped_seq([ord(c) for c in s]), (
        "conditional_escape unsafe branch != deep model on %r" % (s,))
    # safe item: returned byte-for-byte unchanged (no re-escaping)
    safe = _SafeLike(s)
    ce_safe = _conditional_escape_contract(safe)
    assert str(ce_safe) == s, (
        "conditional_escape re-escaped an already-safe item %r -> %r"
        % (s, str(ce_safe)))


def check_real_django():
    """If the real Django callee is importable (in-container), exercise it too."""
    try:
        from django.utils.html import conditional_escape
        from django.utils.safestring import mark_safe
    except Exception:
        return False
    samples = ["x&y", "<p>", "Joe's \"crab\" shack", "a&b<c>d\"e'f", "plain"]
    for s in samples:
        # unsafe: escaped == deep model
        got = str(conditional_escape(s))
        assert [ord(c) for c in got] == escaped_seq([ord(c) for c in s]), (
            "real conditional_escape unsafe branch != deep model on %r" % (s,))
        # safe: unchanged
        got_safe = str(conditional_escape(mark_safe(s)))
        assert got_safe == s, (
            "real conditional_escape re-escaped a safe item %r -> %r"
            % (s, got_safe))
    return True


def main():
    significant = ['&', '<', '>', '"', "'"]
    ordinary = ['a', 'Z', '0', ' ', ';', '#', 'x', '3', '9', '2', '7',
                'é', '•', 'q', 'u', 'o', 't', 'l', 'g', 'm', 'p']

    boundary = [""]
    boundary += significant                       # each significant char alone
    boundary += [c + c for c in significant]      # doubled
    boundary += ["".join(significant)]            # all five together
    boundary += ["".join(reversed(significant))]
    boundary += [
        "a&b<c>d\"e'f",
        "x=1&amp;y=&lt;2&gt;",      # already-escaped text must double-escape
        "&amp;", "&#39;", "&#x27;", "&quot;",
        "Joe's Crab Shack",
        "<script>alert('xss')</script>",
        "Can't find my keys",
        "!$&'()*+,;=~:@,",
    ]
    for s in boundary:
        check_escape_reference(s)
        check_conditional_escape(s)

    rng = random.Random(16877)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_escape_reference(s)
        check_conditional_escape(s)

    used_real = check_real_django()

    print("G-AX OK: escaped_seq deep model == real html.escape and matches "
          "conditional_escape on both branches (safe passthrough + unsafe "
          "escape) over %d boundary + 20000 fuzz inputs%s"
          % (len(boundary), " (incl. real django.utils.html)" if used_real else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
