#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7521 (nagini).

SHADOW: the impl region of model.py's `captured_readback`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The impl region uses only plain List[int] operations, so no PSeq value flows
through the shadow path; the @Pure helper `cr_folded` from the pure region
(which model.py references only inside specifications) copies over as a plain
function on a minimal immutable-sequence shim. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
the captured-text read-back of an fd capture: `_pytest.capture.FDCapture`,
whose constructor builds the text wrapper over the capture buffer
(src/_pytest/capture.py, the changed construction site) and whose `snap()`
reads the captured text back. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable.
The oracle round trip mirrors real usage exactly: construct a capture on a
scratch file descriptor, start() it, write the encoded text to the captured
fd at the OS level, then snap() the text back (snap truncates, so one capture
object serves many inputs, exactly as repeated readouterr() calls do).

Type bridge (mapping.md section 2): the written text `str` maps to List[int]
of Unicode code points via ord/chr; the utf-8 encode-on-write / decode-on-read
byte round trip is the identity on every encodable code point. Following the
declared refinement domain, generated inputs use only encodable, non-surrogate
code points (the replacement-character path never triggers), spanning the
newline forms, ASCII, control characters, accented and astral characters.

Requires demands only read access to the written list, so every generated
input is Requires-satisfying.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz strings.
Pinned fuzz seed: 75210.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys

SEED = 75210
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure region of model.py, contracts stripped ------------------------------
# (model.py references cr_folded only inside specifications, as the contrasting
#  line-ending normalization; it is not called on the shadow path below.)

def cr_folded(s):
    if len(s) == 0:
        return PSeq(10).take(0)
    if s[0] == 13:
        return PSeq(10) + cr_folded(s.drop(1))
    return PSeq(s[0]) + cr_folded(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def captured_readback(written):
    result = []  # type: list
    i = len(written)
    while i > 0:
        c = written[i - 1]
        result = [c] + result
        i = i - 1
    return result


# --- oracle: the real fd-capture read-back ------------------------------------

class RealCapture:
    """Drives the REAL `_pytest.capture.FDCapture` on a scratch fd: writes go
    to the captured fd at the OS level (as the captured program's output
    does); snap() returns the captured text and resets the buffer."""

    def __init__(self, fdcapture_cls):
        # A scratch descriptor to capture; not 0/1/2, so this script's own
        # stdio is untouched and the capture uses the fd (not sys) path.
        self._targetfd = os.open(os.devnull, os.O_WRONLY)
        self._cap = fdcapture_cls(self._targetfd)
        self._cap.start()

    def readback(self, text):
        data = text.encode("utf-8")
        off = 0
        while off < len(data):
            off += os.write(self._targetfd, data[off:])
        return self._cap.snap()

    def close(self):
        self._cap.done()
        os.close(self._targetfd)


def check_one(real, text):
    """Run shadow and oracle on one written text; return an error string on
    disagreement, else None."""
    written = [ord(ch) for ch in text]          # str -> List[int] bridge
    shadow = captured_readback(written)
    shadow_text = "".join(chr(c) for c in shadow)
    observed = real.readback(text)
    if shadow_text != observed:
        return ("DISAGREEMENT\n  written=%r\n  shadow=%r\n  real=%r"
                % (text, shadow_text, observed))
    return None


def boundary_texts():
    newlines = ["\n", "\r\n", "\r"]
    cases = [""]
    cases += newlines
    cases += ["test" + nl for nl in newlines]
    cases += [nl + "x" for nl in newlines]
    cases += [nl * 3 for nl in newlines]
    cases += [
        "a\rb\nc\r\nd",
        "  0%\r",
        "Greetings from DOS\r",
        "line1\r\nline2\r\n",
        "\r\r\r",
        "mix\r\n\r\n\rdone",
        "no newlines here",
        "unicode é • \r ok",
        "astral \U0001f600\r\n end",
        "\x00\x0b\x0c\x85  ",     # other control/separator chars
    ]
    return cases


def main():
    from _pytest.capture import FDCapture    # REAL patched repo class

    real = RealCapture(FDCapture)
    checked = 0
    boundary = boundary_texts()
    try:
        for text in boundary:
            err = check_one(real, text)
            if err:
                print(err)
                return 1
            checked += 1

        # Fresh-capture belt: each boundary case once more against a freshly
        # constructed capture object (constructor exercised per input).
        for text in boundary:
            fresh = RealCapture(FDCapture)
            try:
                err = check_one(fresh, text)
            finally:
                fresh.close()
            if err:
                print(err)
                return 1
            checked += 1

        rng = random.Random(SEED)
        # Alphabet weighted toward the newline forms; all code points are
        # utf-8-encodable non-surrogates per the declared refinement domain.
        alphabet = (["\r", "\n", "\r\n"] * 4
                    + list("test abcXYZ;%#\t01")
                    + ["\x00", "\x0b", "\x0c", "\x85", " ", " ",
                       "é", "θ", "中", "\U0001f600"])
        for _ in range(N_FUZZ):
            n = rng.randint(0, 32)
            text = "".join(rng.choice(alphabet) for _ in range(n))
            err = check_one(real, text)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        real.close()

    print("G-CONF OK: shadow impl == real captured-text read-back on %d "
          "inputs (%d boundary [x2] + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
