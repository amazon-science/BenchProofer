#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7521.

Executes the REAL text reader (`io.TextIOWrapper`, the standard-library class
that `EncodedFile` subclasses) on captured-text round trips and asserts that
every observation matches model.py.

The round trip mirrors fd-capture exactly: text is written to a temporary byte
buffer through a text wrapper, then read back through a text wrapper. The only
difference between the corrected and the regressed reader is whether newline
preservation is requested (`newline=""` vs the wrapper's default).

Two checks:

  (1) FIX soundness -- the VERIFIED behaviour of model.py.
      Reading the captured bytes back through a newline-preserving text reader
      (`newline=""`) reproduces the written code points VERBATIM (identity):
        '\\n' -> '\\n'   '\\r\\n' -> '\\r\\n'   '\\r' -> '\\r'   else identity
      This is exactly model.py's postcondition
      `ToSeq(Result()) == ToSeq(written)` and what the gold patch achieves.

  (2) A-reference -- the deep model `cr_folded` (model.py pure region) faithfully
      captures the read-side carriage-return LOSS of the default (regressed)
      reader:
        * the default reader's output NEVER contains a carriage return (13):
          every captured '\\r' goes missing -- this is the regression -- and
          `cr_folded` encodes that loss (every 13 -> 10);
        * on inputs whose only newline characters are STANDALONE carriage
          returns, the default reader equals `cr_folded` exactly (13 -> 10).

Imports nothing repo-specific: `io` / `tempfile` are the Python standard
library (`io.TextIOWrapper` is the class the patched line constructs). Exit 0
iff every obligation holds.
"""
import io
import os
import random
import sys
import tempfile


# --- model.py reference encoding (kept in lock-step with the pure region) ----

def cr_folded(codepoints):
    """Reference of model.py's deep model `cr_folded` as a list of code points:
    every carriage return (13) becomes a line feed (10); all else identity."""
    return [10 if c == 13 else c for c in codepoints]


# --- real round trip through the standard-library text reader ----------------

def _write_capture_bytes(text):
    """Write `text` the way fd-capture does (through a newline-preserving text
    wrapper over a byte buffer) and return the raw captured bytes on 'disk'."""
    buf = io.BytesIO()
    w = io.TextIOWrapper(buf, encoding="utf-8", errors="replace",
                         newline="", write_through=True)
    w.write(text)
    w.flush()
    data = buf.getvalue()
    w.detach()
    return data


def _read_back(data, newline):
    """Read captured bytes back through a text reader with the given newline
    policy (the patched line passes newline=''; the regression used default)."""
    r = io.TextIOWrapper(io.BytesIO(data), encoding="utf-8", errors="replace",
                         newline=newline)
    return r.read()


def check_fix_identity(text):
    """(1) newline-preserving read-back reproduces the written text verbatim."""
    data = _write_capture_bytes(text)
    observed = _read_back(data, newline="")           # the gold patch's reader
    assert observed == text, (
        "FIX unsound on %r: newline='' read-back gave %r, expected verbatim %r"
        % (text, observed, text))


def check_default_loses_cr(text):
    """(2a) the default (regressed) reader's output never contains a carriage
    return -- the captured '\\r' is lost, which is what `cr_folded` models."""
    data = _write_capture_bytes(text)
    observed = _read_back(data, newline=None)          # the regressed reader
    assert "\r" not in observed, (
        "A-reference unsound: default reader preserved a carriage return on "
        "%r -> %r (cr_folded models it as lost)" % (text, observed))


def check_default_equals_cr_folded_on_lone_cr(text):
    """(2b) on inputs whose newline chars are only STANDALONE carriage returns,
    the default reader equals the deep model `cr_folded` exactly."""
    assert "\n" not in text, "guard: caller must pass LF-free text"
    data = _write_capture_bytes(text)
    observed = [ord(ch) for ch in _read_back(data, newline=None)]
    expected = cr_folded([ord(ch) for ch in text])
    assert observed == expected, (
        "A-reference unsound on lone-CR input %r: default reader gave %r, "
        "cr_folded gives %r" % (text, observed, expected))


def main():
    newlines = ["\n", "\r\n", "\r"]
    ordinary = list("test")

    # --- boundary cases -------------------------------------------------------
    boundary = [""]
    boundary += newlines
    boundary += ["test" + nl for nl in newlines]          # the F2P shape
    boundary += [nl + "x" for nl in newlines]
    boundary += [nl * 3 for nl in newlines]
    boundary += [
        "a\rb\nc\r\nd",
        "  0%\r",                  # the borgbackup progress-bar witness
        "Greetings from DOS\r",    # the issue's reproducer
        "line1\r\nline2\r\n",
        "\r\r\r",
        "mix\r\n\r\n\rdone",
        "no newlines here",
        "unicode é • \r ok",
    ]

    # (1) FIX: verbatim read-back on every boundary case
    for s in boundary:
        check_fix_identity(s)
    # (2a) default reader loses every carriage return on every boundary case
    for s in boundary:
        check_default_loses_cr(s)
    # (2b) lone-CR (LF-free) boundary cases: default reader == cr_folded
    for s in boundary:
        if "\n" not in s:
            check_default_equals_cr_folded_on_lone_cr(s)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(7521)
    alphabet = newlines + ordinary + list("abc \tXYZ;%#")
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_fix_identity(s)            # the verified behaviour holds always
        check_default_loses_cr(s)        # the regression loses every CR

    # lone-CR fuzz (LF-free): exercise the exact cr_folded == default equality
    cr_alphabet = ["\r"] + ordinary + list("abc XYZ;%#")
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(cr_alphabet) for _ in range(n))
        assert "\n" not in s
        check_default_equals_cr_folded_on_lone_cr(s)

    print("G-AX OK: newline-preserving read-back is verbatim (FIX) on %d "
          "boundary + 20000 fuzz inputs; default reader loses every carriage "
          "return and equals the cr_folded deep model on lone-CR inputs over "
          "%d boundary + 20000 fuzz inputs" % (len(boundary), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
