#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11133.

The bundle has NO consumed axioms. Its single non-trivial semantic claim is an
A-reference (mapping.md §3.1, refinement.md A2/A3):

  (A-reference) materialising a byte-buffer view yields its underlying bytes —
      `bytes(memoryview(x)) == x` byte-for-byte — IDENTICAL to materialising a
      plain byte string (`bytes(b) == b`). This is the deep content of the binary
      branch the patch widens (`isinstance(value, (bytes, memoryview))` ->
      `return bytes(value)`), modeled in Solution.lean as the `.buffer b => b`
      and `.bytes b => b` arms of `bodyBytes`.

We execute the REAL builtins (`bytes`, `memoryview`, `bytearray`) on boundary
byte regions plus randomized fuzzing and assert:

  1. `list(bytes(memoryview(x))) == list(x)`            (the buffer arm sound)
  2. `list(bytes(x)) == list(x)`                        (the bytes arm sound)
  3. for NON-EMPTY x: `bytes(memoryview(x)) != str(memoryview(x)).encode(cs)`
     (the contrast the bug turns on: the pre-patch fallback `str(value).encode`
     produced the memoryview's repr `b'<memory at 0x...>'`, NOT its content)

Imports nothing repo-specific: `bytes`/`memoryview`/`bytearray` are builtins —
the same the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys


def check_buffer_reference(x):
    """A-reference arm `.buffer b => b`: bytes(memoryview(x)) == x."""
    mv = memoryview(x)
    observed = list(bytes(mv))            # real builtin: materialise the view
    expected = list(x)                    # underlying bytes (the model's `b`)
    assert observed == expected, (
        "buffer A-reference unsound on %r: bytes(memoryview(.)) gave %r, "
        "model `.buffer b => b` requires %r" % (bytes(x), observed, expected))


def check_bytes_reference(x):
    """A-reference arm `.bytes b => b`: bytes(x) == x for a plain bytes."""
    observed = list(bytes(x))
    expected = list(x)
    assert observed == expected, (
        "bytes A-reference unsound on %r: bytes(.) gave %r, model requires %r"
        % (bytes(x), observed, expected))


def check_bug_contrast(x):
    """The discriminator: for a NON-EMPTY buffer the patched binary branch
    (bytes(value)) differs from the pre-patch fallback (str(value).encode()).
    Confirms the modeled behaviour is the one that fixes the bug, not the repr."""
    if not x:
        return
    mv = memoryview(x)
    content = bytes(mv)                          # post-patch: the content
    fallback = str(mv).encode("utf-8")           # pre-patch: encoded repr
    assert content != fallback, (
        "bug-contrast vacuous on %r: bytes(memoryview)==str(memoryview).encode "
        "(%r) — the pre/post-patch branches do not differ here" % (bytes(x), content))
    # And the fallback is indeed the repr-shaped junk the issue reports.
    assert str(mv).startswith("<memory at "), (
        "unexpected str(memoryview) form: %r" % (str(mv),))


def main():
    # --- boundary byte regions -------------------------------------------
    boundary = [
        b"",                                 # empty buffer
        b"\x00",                             # single NUL
        b"\xff",                             # single high byte
        bytes(range(256)),                   # every byte value 0..255
        b"My Content",                       # the issue's example
        b"memoryview",                       # the F2P test's payload
        b"\x00\x01\x02\x03 binary \xfe\xff",
        b"a" * 4096,                         # large
    ]
    for x in boundary:
        check_buffer_reference(x)
        check_bytes_reference(x)
        check_bug_contrast(x)

    # subviews / slices of a memoryview must also materialise to their bytes
    base = bytes(range(256))
    mv = memoryview(base)
    for lo, hi in [(0, 0), (0, 1), (10, 20), (255, 256), (0, 256), (128, 200)]:
        sub = bytes(mv[lo:hi])
        assert list(sub) == list(base[lo:hi]), (
            "subview unsound [%d:%d]: %r vs %r" % (lo, hi, sub, base[lo:hi]))

    # non-`bytes` backings: bytearray also exposes the buffer protocol
    for x in [bytearray(b""), bytearray(b"abc"), bytearray(range(64))]:
        observed = list(bytes(memoryview(x)))
        assert observed == list(x), (
            "bytearray-backed buffer unsound on %r: %r" % (bytes(x), observed))

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(11133)
    for _ in range(20000):
        n = rng.randint(0, 64)
        x = bytes(rng.randint(0, 255) for _ in range(n))
        check_buffer_reference(x)
        check_bytes_reference(x)
        check_bug_contrast(x)

    print("G-AX OK: bytes(memoryview(x))==x and bytes(x)==x sound on %d boundary "
          "+ 20000 fuzz byte regions (+ subviews, bytearray backings); "
          "bug-contrast (content != repr.encode) holds on every non-empty buffer."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
