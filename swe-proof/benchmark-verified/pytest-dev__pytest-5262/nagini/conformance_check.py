#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5262 (nagini).

SHADOW: the impl region of model.py `reported_mode`, copied verbatim below with
the contract calls (Requires/Ensures/Invariant/Assert) stripped. The impl uses
only plain lists and ints, so no PSeq shim is needed at runtime (ToSeq/PSeq
appear exclusively inside the stripped contract clauses). `BINARY_MARKER` comes
over from the pure region as a plain constant. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo attribute the model models per mapping.md — the
`mode` reported by `_pytest.capture.EncodedFile`. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. The wrapper's only input for this attribute is the
underlying buffer's mode string, so the oracle wraps a minimal buffer stub
carrying an arbitrary `mode` (plus, as extra grounding, real binary file
objects opened in every binary mode CPython accepts) and reads the wrapper's
advertised mode.

Type bridge (mapping.md section 2): the mode is a `str` in the repo and a
`List[int]` of Unicode code points in the model; the bijection is
`buffer_mode[k] == ord(s[k])`. The shadow's output list is joined back to a
`str` via `chr` and compared to the oracle's value for exact equality.

Input domain: the precondition admits any code-point list (read-only), i.e.
any `str` on the repo side. Generation covers boundary mode strings (every
file-mode CPython produces, repeated/adjacent/leading/trailing markers,
uppercase, ordinary words, empty), real opened-file modes, and randomized
fuzz over mode-letter alphabets plus full-Unicode draws (ASCII, Latin-1,
BMP, astral, control, combining code points).

>= 1e5 Requires-satisfying inputs: boundary cases + >=110000 fuzz strings.
Pinned fuzz seed: 52620.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
import tempfile

SEED = 52620
N_FUZZ_MODEISH = 60_000
N_FUZZ_UNICODE = 50_000


# --- pure region constant (model.py) ------------------------------------------

BINARY_MARKER = 98  # the code point 'b'


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reported_mode(buffer_mode):
    result = []  # type: list
    i = len(buffer_mode)
    while i > 0:
        c = buffer_mode[i - 1]
        if c != BINARY_MARKER:
            result = [c] + result
        i = i - 1
    return result
    # (impl region ends)


# --- differential driver -------------------------------------------------------

class _BufferStub(object):
    """Minimal underlying-buffer stand-in: the wrapper reads only `.mode`."""

    def __init__(self, mode):
        self.mode = mode


def real_reported_mode(EncodedFile, mode_str):
    """The oracle: the mode the patched text wrapper advertises for an
    underlying buffer whose mode is `mode_str`."""
    return EncodedFile(_BufferStub(mode_str), "utf-8").mode


def check_mode(EncodedFile, mode_str):
    """Run shadow and oracle on one mode string; return an error string on
    disagreement, else None."""
    shadow = reported_mode([ord(ch) for ch in mode_str])
    shadow_str = "".join(chr(c) for c in shadow)
    real_str = real_reported_mode(EncodedFile, mode_str)
    if shadow_str != real_str:
        return ("DISAGREEMENT\n  buffer mode=%r\n  shadow=%r\n  real=%r"
                % (mode_str, shadow_str, real_str))
    return None


def boundary_modes():
    return [
        "", "r", "w", "a", "x", "+", "t", "b",
        "rb", "wb", "ab", "xb", "rt", "wt",
        "rb+", "wb+", "ab+", "xb+", "r+b", "w+b", "a+b", "x+b",
        "r+", "w+", "a+", "x+",
        "bb", "bbb", "brb", "rbb", "bbr", "b+b",       # repeated / adjacent markers
        "rb+t", "abc", "subprocess", "verbatim",       # marker inside ordinary text
        "no markers here", "BBB", "B", "Rb", "bR",     # uppercase B must be KEPT
        "ébé", "b☃b", "\U0001F600b",    # non-ASCII neighbours
        " b ", "\tb\n", "b" * 50,
    ]


def real_file_modes():
    """Modes as reported by actual binary file objects (extra grounding: the
    repo wraps real dup'd binary streams)."""
    modes = []
    for open_mode in ("wb", "wb+", "ab", "ab+", "rb", "rb+", "xb", "xb+"):
        try:
            if open_mode.startswith(("r", "x")):
                tmp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
                path = tmp.name
                tmp.close()
                if open_mode.startswith("x"):
                    import os
                    os.unlink(path)
                f = open(path, open_mode)
            else:
                f = tempfile.NamedTemporaryFile(mode=open_mode)
        except (OSError, ValueError):
            continue
        modes.append(f.mode)
        f.close()
    return modes


def main():
    from _pytest.capture import EncodedFile  # REAL patched repo class

    checked = 0
    for s in boundary_modes() + real_file_modes():
        err = check_mode(EncodedFile, s)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)

    # mode-letter-shaped fuzz (dense on the strings the domain actually sees)
    alphabet = list("rwaxbB+tU") + list("bcdefg 0123456789")
    for _ in range(N_FUZZ_MODEISH):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        err = check_mode(EncodedFile, s)
        if err:
            print(err)
            return 1
        checked += 1

    # full-Unicode fuzz: arbitrary code points (skipping surrogates), with the
    # marker code point salted in so deletions happen at random positions
    for _ in range(N_FUZZ_UNICODE):
        n = rng.randint(0, 16)
        chars = []
        for _ in range(n):
            if rng.random() < 0.3:
                chars.append("b")
                continue
            cp = rng.randint(0, 0x10FFFF)
            if 0xD800 <= cp <= 0xDFFF:
                cp = cp - 0xD800  # remap surrogates into valid range
            chars.append(chr(cp))
        s = "".join(chars)
        err = check_mode(EncodedFile, s)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real advertised mode on %d inputs "
          "(%d boundary + real-file modes + fuzz, seed %d)."
          % (checked, len(boundary_modes()), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
