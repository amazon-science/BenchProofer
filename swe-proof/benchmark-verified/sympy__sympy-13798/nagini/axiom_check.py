#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13798.

The bundle has exactly one @ContractOnly axiom, `trimmed` (an A-reference: it
models the unchanged stdlib whitespace-trim callee `str.strip()` and is
validated == the real callee by this check — the proof does NOT consume its
Ensures, the numeric postcondition discharges by functional congruence). Its
Ensures is:

    no_outer_blank(s)  =>  trimmed(s) == s

where `no_outer_blank(s)` (model.py pure region) holds iff `s` is empty OR both
its first and last code points are printable non-space ASCII (33..126), via
`is_visible_ascii`.

This script executes the REAL `str.strip()` and asserts the axiom never
over-claims: for every input whose model predicate `no_outer_blank` is True,
`s.strip() == s` actually holds in CPython. It deliberately fuzzes the
whitespace-stripping behaviour — leading/trailing ASCII and Unicode whitespace,
all-whitespace tokens, and the in-domain spacing tokens the numeric branch keys
on — exactly the boundaries an adversarial G-AX would probe.

It also pins the two F2P-relevant facts the proof relies on:
  * trimmed('\\,') == '\\,'        (the thin-space selector is unchanged by the
                                    trim, so it is recognised as spacing-only)
  * the seven spacing-only tokens are each their own strip-fixpoint.

Imports nothing repo-specific (`str.strip` is a builtin). Exit 0 iff sound.
"""
import random
import sys


# --- model.py reference predicates (kept in lock-step with model.py) ---------

def is_visible_ascii(c):
    return 33 <= c <= 126


def no_outer_blank(codepoints):
    if len(codepoints) == 0:
        return True
    return is_visible_ascii(codepoints[0]) and is_visible_ascii(codepoints[-1])


# The seven "spacing only" tokens the numeric branch keys on (model.py
# is_spacing_only), as Python strings.
SPACING_ONLY = ["", " ", "\\", "\\,", "\\:", "\\;", "\\quad"]


# --- the axiom soundness check -----------------------------------------------

def check_trim_axiom(s):
    """If the model predicate no_outer_blank holds for s, the REAL str.strip()
    must be the identity on s (the axiom's only Ensures)."""
    cps = [ord(ch) for ch in s]
    if no_outer_blank(cps):
        assert s.strip() == s, (
            "trimmed axiom UNSOUND on %r: no_outer_blank is True but "
            "str.strip() = %r != input" % (s, s.strip()))


def main():
    # Code points str.strip() removes from the ends (the whitespace class) up to
    # a generous bound — used to build adversarial padded inputs.
    ws_chars = [chr(c) for c in range(0x3001) if chr(c).strip() == ""]
    assert " " in ws_chars and "\t" in ws_chars and "\xa0" in ws_chars

    # --- boundary inputs ------------------------------------------------------
    boundary = []
    boundary += SPACING_ONLY                      # the in-domain spacing tokens
    boundary += ["\\,", "dot", "times", "ldot", "*", "x", "ab", "a b",
                 "\\cdot", "\\times", "a\\,b"]
    # whitespace-padded variants (no_outer_blank False -> axiom claims nothing,
    # but str.strip will differ; this guards against an accidental over-claim)
    for core in ["\\,", "x", "ab", "dot"]:
        for w in ws_chars[:12]:
            boundary.append(w + core)
            boundary.append(core + w)
            boundary.append(w + core + w)
    boundary += ws_chars                          # all-whitespace single chars
    boundary += ["".join(ws_chars[:5])]           # all-whitespace multi
    for s in boundary:
        check_trim_axiom(s)

    # --- the discriminating F2P fact -----------------------------------------
    # The thin-space selector is unchanged by the trim, hence spacing-only.
    assert "\\,".strip() == "\\,", "\\, must be a strip-fixpoint"
    assert no_outer_blank([ord(c) for c in "\\,"]), \
        "model: \\, must satisfy no_outer_blank"

    # Each spacing-only token is its own strip-fixpoint except those with outer
    # whitespace; the numeric branch compares the TRIMMED token, so verify the
    # trimmed form is what is_spacing_only recognises.
    for tok in SPACING_ONLY:
        assert tok.strip() == tok or tok.strip() in SPACING_ONLY, (
            "spacing token %r trims to %r, not in the recognised set"
            % (tok, tok.strip()))

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13798)
    alphabet = (["\\", ",", ":", ";", "d", "o", "t", "x", "a", "q", "u",
                 "*", "+", "=", "(", ")", " "] + ws_chars[:8]
                + [chr(c) for c in range(33, 127)])
    fuzz = 0
    for _ in range(60000):
        n = rng.randint(0, 10)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_trim_axiom(s)
        fuzz += 1
    # high code points and astral plane (none are visible-ASCII, so the model
    # predicate is False for them at the ends, but the interior may be anything)
    for _ in range(20000):
        n = rng.randint(0, 6)
        s = "".join(chr(rng.randint(0, 0x2FFFF)) for _ in range(n))
        check_trim_axiom(s)
        fuzz += 1

    print("G-AX OK: trimmed axiom (no_outer_blank(s) => str.strip(s)==s) sound "
          "on %d boundary + %d fuzz inputs; thin-space selector \\, confirmed "
          "spacing-only" % (len(boundary), fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
