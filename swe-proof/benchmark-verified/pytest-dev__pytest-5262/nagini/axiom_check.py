#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5262.

Executes the REAL changed string operation (`str.replace("b", "")`) on inputs
(boundary file-mode strings CPython actually produces, plus randomized fuzzing)
and asserts that every observation matches the model, as encoded in model.py.

The single kind-A item is an A-reference (NOT a consumed axiom):

  (A-reference) the deep model `without_marker` (model.py pure region) == the
      real `str.replace("b", "")` on the buffer's mode. The changed string
      operation is modeled DEEPLY, not behind a consumed axiom; G-AX validates
      that deep model against the real callee:
        kept(c)         = ""      if c == 'b' (U+0062, 98)
                        = chr(c)  otherwise
        without_marker  = concatenation of kept over the input code points
      and asserts the real result is `marker_free` (contains no 'b').

There are no @ContractOnly axioms to check: the modeled function reads only its
input mode string and deletes a character. Imports nothing repo-specific
(`str.replace` is a built-in — the same operation the gold patch calls). Exit 0
iff every obligation holds.
"""
import random
import sys

BINARY_MARKER = ord("b")  # 98


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def kept(c):
    """Reference for model.py `kept`: a single code point's contribution."""
    if c == BINARY_MARKER:
        return []
    return [c]


def without_marker(codepoints):
    """Reference implementation of model.py's deep model `without_marker`, as a
    list of code points (the per-code-point deletion of the binary marker)."""
    out = []
    for c in codepoints:
        out.extend(kept(c))
    return out


def marker_free(codepoints):
    """Reference for model.py `marker_free`."""
    return all(c != BINARY_MARKER for c in codepoints)


# --- the checks --------------------------------------------------------------

def check_reference(s):
    """Assert the deep model without_marker(s) == the REAL str.replace('b','')
    and that the real result is marker_free."""
    observed = [ord(ch) for ch in s.replace("b", "")]        # real callee
    expected = without_marker([ord(ch) for ch in s])         # deep model
    assert observed == expected, (
        "without_marker deep model unsound on %r: str.replace gave %r, "
        "deep model gives %r" % (s, observed, expected))
    assert marker_free(observed), (
        "marker_free violated on %r: result %r still contains the binary marker"
        % (s, observed))


def main():
    # --- boundary cases: every file-mode string CPython produces ----------
    # (and the duplication modes _pytest.capture uses: safe_text_dupfile adds
    #  a trailing 'b' to give wb+ -> the underlying buffer reports rb+/wb+).
    boundary = [
        "", "r", "w", "a", "x", "+", "t", "b",
        "rb", "wb", "ab", "xb", "rt", "wt",
        "rb+", "wb+", "ab+", "xb+", "r+b", "w+b",
        "rb+", "r+", "w+", "a+",
        "bb", "bbb", "brb", "rbb", "bbr",          # repeated / adjacent markers
        "rb+t", "abc", "subprocess", "verbatim",   # 'b' inside ordinary text
        "no markers here", "BBB",                  # uppercase B must be KEPT
    ]
    for s in boundary:
        check_reference(s)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(5262)
    alphabet = list("rwax+tbB") + list("abcdefgABCDEF0123456789 ")
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_reference(s)

    print("G-AX OK: without_marker deep model (== str.replace('b','')) sound "
          "and marker-free on %d boundary + 20000 fuzz inputs" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
