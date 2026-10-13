#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7205.

Executes the REAL repo callee `_pytest._io.saferepr.saferepr` on inputs
(boundary cases over the printable-ASCII range and the F2P literals, plus
randomized fuzzing) and asserts that every observation matches the deep model
`quotedRepr` (Solution.lean pure region), as encoded below.

The one kind-A check:

  (A-reference) the deep model `quoted_repr` (Solution.lean `quotedRepr`) ==
      the real `saferepr(v, maxsize=42)` over the whole `simpleParam` domain.
      The display's changed rendering operation is modeled DEEPLY on BOTH
      payload shapes the modeled domain distinguishes, not behind a consumed
      axiom; G-AX validates that deep model against the real callee:
        * textVal s  (len<=40, printable ASCII 32..126, no "'" no "\\"):
              saferepr(s, maxsize=42) == "'" + s + "'"
        * bytesVal s (len<=39, same character domain, ASCII-encoded bytes):
              saferepr(s.encode('ascii'), maxsize=42) == "b'" + s + "'"
      (apostrophe-wrapped, byte-string prefix on the bytes shape, no
      truncation marker on either shape).
      It additionally witnesses that the maxsize=42 bound is load-bearing on
      BOTH shapes: a length-41 text value and a length-40 byte-string DO get
      ellipsized by the real callee.

Imports the repo callee from `_pytest._io.saferepr` (the same module the gold
patch imports). Stdlib otherwise. Exit 0 iff every obligation holds.
"""
import random
import string
import sys

from _pytest._io.saferepr import saferepr  # the REAL repo callee


# --- simpleParam domain (mapping.md §3.1) -------------------------------------
# printable ASCII 32..126, excluding the apostrophe (0x27) and backslash (0x5c)
SIMPLE_ALPHABET = [
    chr(c) for c in range(32, 127) if chr(c) not in ("'", "\\")
]
MAXSIZE = 42
MAXLEN_TEXT = 40   # maxsize - 2 (the two apostrophes), so repr never exceeds maxsize
MAXLEN_BYTES = 39  # maxsize - 3 (the b prefix + two apostrophes)


def quoted_repr_text(s):
    """Reference impl of Solution.lean's `quotedRepr (.textVal s)`."""
    return "'" + s + "'"


def quoted_repr_bytes(s):
    """Reference impl of Solution.lean's `quotedRepr (.bytesVal s)`."""
    return "b'" + s + "'"


def check_text(s):
    """Assert the deep model on a text payload == the REAL saferepr(s, 42)."""
    observed = saferepr(s, maxsize=MAXSIZE)         # real callee
    expected = quoted_repr_text(s)                  # deep model
    assert observed == expected, (
        "quotedRepr deep model unsound on textVal %r: saferepr(.,42) gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_bytes(s):
    """Assert the deep model on a byte-string payload == the REAL callee."""
    b = s.encode("ascii")
    observed = saferepr(b, maxsize=MAXSIZE)         # real callee
    expected = quoted_repr_bytes(s)                 # deep model
    assert observed == expected, (
        "quotedRepr deep model unsound on bytesVal %r: saferepr(.,42) gave %r, "
        "deep model gives %r" % (b, observed, expected))


def main():
    # --- boundary cases -------------------------------------------------------
    boundary = [""]
    boundary += [c for c in SIMPLE_ALPHABET]            # each printable char alone
    boundary += [c + c for c in SIMPLE_ALPHABET]        # doubled
    boundary += ["a" * MAXLEN_TEXT]                     # the length-40 edge (no ellipsis)
    boundary += ["a" * n for n in range(0, MAXLEN_TEXT + 1)]  # every length up to the edge
    # the exact F2P parameter / id literals
    boundary += ["foo", "bar", "spam", "ham", "FOO", "BAR"]
    boundary += ["arg_same", "foobar"]
    boundary += ["Hello World"]                         # the F2P bytes literal's content
    boundary += [
        "".join(SIMPLE_ALPHABET),                        # too long -> must be excluded
    ]
    n_text = n_bytes = 0
    for s in boundary:
        if len(s) <= MAXLEN_TEXT:
            check_text(s)
            n_text += 1
        if len(s) <= MAXLEN_BYTES:
            check_bytes(s)
            n_bytes += 1

    # --- randomized fuzz over the simpleParam domain ---------------------------
    rng = random.Random(7205)
    for _ in range(200000):
        n = rng.randint(0, MAXLEN_TEXT)
        s = "".join(rng.choice(SIMPLE_ALPHABET) for _ in range(n))
        check_text(s)
        if n <= MAXLEN_BYTES:
            check_bytes(s)

    # --- witness that the maxsize=42 bound is load-bearing --------------------
    # A length-41 simple text has repr length 43 > 42, so the real callee MUST
    # ellipsize (introduce "..."), confirming the <=40 text domain bound.
    over = "a" * 41
    obs_over = saferepr(over, maxsize=MAXSIZE)
    assert "..." in obs_over and obs_over != quoted_repr_text(over), (
        "expected saferepr to ellipsize a length-41 string under maxsize=42, "
        "got %r" % (obs_over,))
    # A length-40 simple byte-string has repr length 43 > 42 (the extra `b`
    # prefix), so it too MUST ellipsize, confirming the <=39 bytes domain bound.
    over_b = b"a" * 40
    obs_over_b = saferepr(over_b, maxsize=MAXSIZE)
    assert "..." in obs_over_b and obs_over_b != quoted_repr_bytes("a" * 40), (
        "expected saferepr to ellipsize a length-40 bytes under maxsize=42, "
        "got %r" % (obs_over_b,))

    # --- witness the pre-patch divergence (plain str() vs saferepr) -----------
    # On a text value the bare str() form has NO apostrophes; saferepr does.
    for s in ["foo", "bar", "spam"]:
        assert str(s) != saferepr(s, maxsize=MAXSIZE), (
            "expected saferepr to differ from plain str() on %r" % (s,))
    # On a byte-string the pre-patch's implicit str() is an ERROR under strict
    # byte/text separation (-bb, the exact F2P flag); saferepr goes through
    # repr and raises no BytesWarning. The interpreter emits BytesWarning only
    # when started with -b/-bb, so witness in a -bb subprocess.
    import subprocess
    r_safe = subprocess.run(
        [sys.executable, "-bb", "-c",
         "from _pytest._io.saferepr import saferepr; "
         "saferepr(b'Hello World', maxsize=%d)" % MAXSIZE],
        stderr=subprocess.DEVNULL)
    assert r_safe.returncode == 0, (
        "expected saferepr of a bytes value to raise no BytesWarning under "
        "-bb, got exit %d" % r_safe.returncode)
    r_str = subprocess.run(
        [sys.executable, "-bb", "-c", "'{}'.format(b'Hello World')"],
        stderr=subprocess.DEVNULL)
    assert r_str.returncode != 0, (
        "expected the pre-patch implicit str() of a bytes value to fail "
        "under -bb (BytesWarning-as-error), got exit 0")

    print("G-AX OK: quotedRepr deep model (== saferepr(.,maxsize=42)) sound on "
          "%d text + %d bytes boundary + 200000-round fuzz simpleParam inputs; "
          "maxsize=42 bound witnessed load-bearing on both shapes; saferepr "
          "raises no BytesWarning where the pre-patch str() does."
          % (n_text, n_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
