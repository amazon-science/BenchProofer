#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7521.

Constructs the REAL text stream exactly as the gold patch configures it — an
`io.TextIOWrapper` over a byte buffer with `encoding="utf-8"`, `errors="replace"`,
`newline=""`, `write_through=True` (the post-patch `FDCaptureBinary.__init__`
configuration in src/_pytest/capture.py) — writes each test input, reads it back
(the `FDCapture.snap` `tmpfile.read()` round-trip), and asserts the observation
matches the model encoded in Solution.lean.

The kind-A check:

  (A-reference) the deep model `readback` (Solution.lean pure region, proven ==
      identity by `readback_id`) == the real `newline=""` stream read-back. The
      changed newline-handling operation is modeled DEEPLY, not behind a
      consumed axiom; G-AX validates that deep model against the real callee:
        read-back is VERBATIM — every code point (incl. U+000D '\\r' and
        U+000A '\\n') is recovered unchanged, no \\r->\\n or \\r\\n->\\n.

  (negative control) the PRE-patch configuration (no `newline` argument =>
      platform default universal-newline mode) DOES rewrite '\\r' and '\\r\\n'
      to '\\n' on read. This proves the modeled distinction is real and the fix
      is necessary (it is what the F2P tests observe).

Imports nothing repo-specific: `io` is the Python standard library — the same
module the gold patch's `TextIOWrapper` lives in. Exit 0 iff every obligation
holds.
"""
import io
import random
import sys


def real_readback(s, newline):
    """Write `s` into a UTF-8 byte buffer through a TextIOWrapper configured as
    the patch configures it, then read it back — the snap() round-trip.

    `newline=""` is the post-patch config; `newline=None` is the pre-patch
    default (universal-newline mode)."""
    buf = io.BytesIO()
    w = io.TextIOWrapper(
        buf,
        encoding="utf-8",
        errors="replace",
        newline=newline,
        write_through=True,
    )
    w.write(s)
    w.flush()
    w.seek(0)
    return w.read()


def model_readback(s):
    """Reference implementation of Solution.lean's deep model `readback`
    (== identity by readback_id): the verbatim per-code-point copy."""
    return "".join(ch for ch in s)


def check_reference(s):
    """A-reference: the deep model readback(s) == the REAL newline="" read-back."""
    observed = real_readback(s, newline="")     # real patched stream
    expected = model_readback(s)                # deep model (== identity)
    assert observed == expected, (
        "readback deep model unsound on %r: real newline=\"\" stream gave %r, "
        "deep model gives %r" % (s, observed, expected))


def check_negative(s):
    """Negative control: the PRE-patch default-newline stream translates CR.
    Only assert divergence for inputs that actually contain a carriage return;
    for CR-free inputs both configs agree (and that is fine)."""
    pre = real_readback(s, newline=None)        # pre-patch (buggy) stream
    if "\r" in s:
        assert pre != s or "\r" not in pre, (
            "negative control failed: pre-patch stream unexpectedly preserved "
            "carriage returns verbatim on %r -> %r" % (s, pre))


def main():
    newlines = ["\n", "\r", "\r\n", "\n\r"]
    # --- boundary cases: every newline form, alone / doubled / mixed / with text
    boundary = [""]
    boundary += newlines
    boundary += [nl + nl for nl in newlines]
    boundary += ["test" + nl for nl in newlines]          # the F2P shape
    boundary += [nl + "test" for nl in newlines]
    boundary += [
        "Greetings from DOS\r",                            # the issue reproducer
        "  0%\r",                                          # the borgbackup case
        "a\rb\r\nc\nd",
        "\r\r\r", "\n\n\n", "\r\n\r\n",
        "line1\nline2\r\nline3\rline4",
        "no newlines here",
        "tab\tand spaces  ",
        "unicode é • ☃ end\r",
    ]
    for s in boundary:
        check_reference(s)
        check_negative(s)

    # --- randomized fuzz over an alphabet rich in newline/CR code points -------
    rng = random.Random(7521)
    alphabet = list("\r\n\r\n abABzZ09.!-") + ["é", "•", "\t", "\r", "\n"]
    for _ in range(20000):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        check_reference(s)
        check_negative(s)

    print("G-AX OK: readback deep model (== real newline=\"\" TextIOWrapper "
          "read-back) verbatim on %d boundary + 20000 fuzz inputs; negative "
          "control confirms pre-patch default-newline stream translates CR."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
