#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16877.

This bundle has NO consumed axioms. Its single callee, `conditional_escape`
(UNCHANGED by the patch), is modeled DEEPLY in Solution.lean's `pure` region
(`condEscape`, with `escapedSeq`/`entity`) — an A-reference. G-AX validates that
deep model against the REAL callee:

  (A-reference) the deep model `cond_escape` (mirror of Solution.lean's
      `condEscape`) == the real `django.utils.html.conditional_escape`:
        - an element already marked safe (has `__html__`, i.e. SafeData /
          mark_safe) passes through UNCHANGED;
        - any other element is HTML-escaped per code point by `html.escape`:
            &(38) -> &amp;   <(60) -> &lt;   >(62) -> &gt;
            "(34) -> &quot;  '(39) -> &#x27;   else identity
          (ampersand first, so emitted '&' are not re-escaped).

  (sub-reference) beneath it, `escaped_seq` == the real `html.escape(str(s))`.

Runs in-container (the prebuilt SWE-Bench instance image): imports the REAL
`django.utils.html.conditional_escape` and `django.utils.safestring.mark_safe`,
plus stdlib `html`. Exercises both safe and non-safe elements over boundary cases
and 20 000 randomized fuzz strings. Exit 0 iff every observation matches the model.
"""
import html
import random
import sys

from django.utils.html import conditional_escape   # the REAL unchanged callee
from django.utils.safestring import mark_safe

# --- Solution.lean reference encodings (kept in lock-step with the pure region) --

_ENTITY = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def escaped_seq(s):
    """Mirror of Solution.lean `escapedSeq`/`entity`: per-code-point HTML escape
    of a non-safe element (ampersand-first, so emitted '&' is not re-escaped)."""
    return "".join(_ENTITY.get(ch, ch) for ch in s)


def cond_escape(text, safe):
    """Mirror of Solution.lean `condEscape`: a safe element passes through
    unchanged; any other element is escaped per code point."""
    if safe:
        return text
    return escaped_seq(text)


# --- the checks --------------------------------------------------------------

def check_escaped_seq_reference(s):
    """Assert the sub-model escaped_seq(s) == the REAL html.escape(s)."""
    observed = html.escape(s)                 # real stdlib callee, quote=True
    expected = escaped_seq(s)                  # deep sub-model
    assert observed == expected, (
        "escaped_seq sub-model unsound on %r: html.escape gave %r, model %r"
        % (s, observed, expected))


def check_cond_escape_reference(s):
    """Assert cond_escape == the REAL conditional_escape, for both the non-safe
    element `s` and the already-safe element `mark_safe(s)`."""
    # non-safe element: conditional_escape applies escape()
    observed_plain = str(conditional_escape(s))
    expected_plain = cond_escape(s, safe=False)
    assert observed_plain == expected_plain, (
        "condEscape (non-safe) unsound on %r: conditional_escape gave %r, "
        "model %r" % (s, observed_plain, expected_plain))
    # already-safe element: conditional_escape returns __html__() unchanged
    safe_s = mark_safe(s)
    observed_safe = str(conditional_escape(safe_s))
    expected_safe = cond_escape(s, safe=True)
    assert observed_safe == expected_safe, (
        "condEscape (safe) unsound on %r: conditional_escape(mark_safe) gave "
        "%r, model %r" % (s, observed_safe, expected_safe))


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
        "x=1&amp;y=&lt;2&gt;",      # already-escaped input must double-escape
        "&amp;", "&#39;", "&#x27;", "&quot;",
        "Joe's Crab Shack",
        "<script>alert('xss')</script>",
        "Can't find my keys",
        "!$&'()*+,;=~:@,",
        "x&y", "<p>",               # the exact F2P element payloads
    ]
    for s in boundary:
        check_escaped_seq_reference(s)
        check_cond_escape_reference(s)

    # --- randomized fuzz: both safe and non-safe element flavours ----------
    rng = random.Random(16877)
    alphabet = significant + ordinary
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_escaped_seq_reference(s)
        check_cond_escape_reference(s)

    print("G-AX OK: condEscape deep model (== conditional_escape, safe and "
          "non-safe) + escaped_seq (== html.escape) sound on %d boundary + "
          "20000 fuzz elements" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
