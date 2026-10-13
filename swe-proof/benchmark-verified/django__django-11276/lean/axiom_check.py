#!/usr/bin/env python3
"""G-AX — django__django-11276.

The bundle consumes NO callee axiom (`meta.json axioms = []`). It declares ONE
A-reference: `escapeChar`/`escapeSeq` deeply models the stdlib escaper
`html.escape(·, quote=True)` — the operation the patch introduces (refinement.md
row 4). §0.7 forbids axiomatizing the changed op, so it is modeled deeply and
validated == the real callee here (rather than assumed via an axiom).

This check drives the REAL `html.escape` and asserts:
  (a) per-code-point: for every code point c, html.escape(c) == escapeChar(c)
      (the deep model is faithful character-by-character); and
  (b) whole-string: html.escape(s) equals the in-order concatenation of
      escapeChar over s's code points (escapeSeq), over boundary + fuzz inputs —
      i.e. html.escape is observationally a per-code-point map, justifying the
      `for`-loop skeleton.

stdlib-only; exit 0 iff every observation meets the A-reference property.
"""
import html
import json
import random
import sys

SEED = 11276


def escape_char(c: str) -> str:
    """escapeChar (Solution.lean pure region), transliterated."""
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


def escape_seq(s: str) -> str:
    """escapeSeq: in-order concatenation of escapeChar over the code points."""
    return "".join(escape_char(c) for c in s)


def main() -> int:
    failures = []

    # (a) per-code-point faithfulness. The five HTML-significant chars + a broad
    # sweep of other code points (ASCII, latin-1, a few astral), each of which
    # must pass through html.escape unchanged and equal escapeChar.
    codepoints = [chr(i) for i in range(0, 0x250)]           # C0/C1 + latin ext
    codepoints += ['&', '<', '>', '"', "'"]                  # the significant 5
    codepoints += ['•', 'é', ' ', '\U0001F600', '\U0001F4A9']
    for c in codepoints:
        got = html.escape(c)          # real callee, default quote=True
        want = escape_char(c)
        if got != want:
            failures.append({"kind": "per-char", "cp": ord(c),
                             "html_escape": got, "escapeChar": want})
            if len(failures) > 20:
                break

    # (b) whole-string == escapeSeq over boundary + fuzz inputs.
    edges = ["", "'", "Joe's", "<a>'", "&", '"', "&<>\"'",
             "<script>alert('foo')</script>", "a&amp;b", "''''", "&&&",
             "Can't find my keys", "é•\U0001F600"]
    for s in edges:
        if html.escape(s) != escape_seq(s):
            failures.append({"kind": "whole-edge", "in": s,
                             "html_escape": html.escape(s),
                             "escapeSeq": escape_seq(s)})

    rng = random.Random(SEED)
    alphabet = list("&<>\"'") + list("abc019 \t\n") + ["é", "•", "\U0001F600"]
    for _ in range(100_000):
        n = rng.randint(0, 12)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if html.escape(s) != escape_seq(s):
            failures.append({"kind": "whole-fuzz", "in": s})
            break

    if failures:
        print(json.dumps({"status": "fail", "instance": "django__django-11276",
                          "failures": failures[:20]}))
        return 1
    print(json.dumps({
        "status": "pass",
        "instance": "django__django-11276",
        "reference": "html.escape (default quote=True)",
        "reason": "escapeChar is faithful to html.escape per code point, and "
                  "html.escape is observationally the in-order per-code-point "
                  "concatenation (escapeSeq) — the A-reference deep model holds.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
