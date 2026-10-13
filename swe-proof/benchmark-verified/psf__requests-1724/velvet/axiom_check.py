#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-1724.

Executes the REAL callees the construction site relies on and asserts that every
observation matches Solution.lean, on boundary cases over the HTTP-method
alphabet plus randomized fuzzing.

The two kind-A checks:

  (A-consumed) the native-flavour stub (`flavour :| flavour = true` in the impl
      region) stands for the unchanged native-text-flavour constructor that the
      construction site applies to the supplied method. Its only consumed
      obligation is that the produced value IS of the native text flavour,
      independent of the argument flavour. The real callee is
      `requests.compat.builtin_str` (the native `str` constructor on every
      supported interpreter; on the Python-2 runtime the issue reports, it is the
      byte-`str` constructor, NOT the module-level `unicode` alias). G-AX asserts
      that applying it to either a native or a non-native argument always yields a
      native value.

  (A-reference) the deep model `upperSeq` / `upperCp` (Solution.lean pure region)
      == the real case-normalisation `str.upper` on the ASCII domain the method
      names inhabit:
        'a'..'z' (97..122) -> 'A'..'Z' (65..90),  every other code point id.
      The deep model is validated == the real callee out-of-band here (it is NOT
      a consumed axiom).

Imports nothing repo-specific beyond `requests.compat.builtin_str` (the very
symbol the gold patch imports and calls); falls back to the stdlib native `str`
constructor if requests is not importable. Exit 0 iff every obligation holds.
"""
import random
import sys

# The real native-flavour constructor the patch calls. On Python 3 this is the
# builtin `str`; on Python 2 it is the byte-`str` constructor (requests.compat
# binds `builtin_str = str` BEFORE rebinding the module-level `str = unicode`).
try:
    from requests.compat import builtin_str as REAL_BUILTIN_STR
except Exception:  # pragma: no cover - requests always present in-container
    REAL_BUILTIN_STR = str


def upper_cp(c):
    """Reference of Solution.lean's deep model `upperCp` (one code point)."""
    if 97 <= c <= 122:        # 'a'..'z' -> 'A'..'Z'
        return c - 32
    return c


def upper_seq(codepoints):
    """Reference of Solution.lean's deep model `upperSeq` (per-code-point map)."""
    return [upper_cp(c) for c in codepoints]


def check_upper_reference(s):
    """Assert the deep model upperSeq(s) == the REAL str.upper(s) (ASCII)."""
    observed = [ord(ch) for ch in s.upper()]          # real callee
    expected = upper_seq([ord(ch) for ch in s])       # deep model
    assert observed == expected, (
        "upperSeq deep model unsound on %r: str.upper gave %r, "
        "deep model gives %r" % (s, observed, expected))


def is_native(value):
    """The native text flavour == the builtin `str` type on the running
    interpreter (`str` on py3; the byte-`str` on py2)."""
    return type(value) is str


def check_native_stub(value):
    """Assert the REAL builtin_str(value) is of the native text flavour,
    regardless of the flavour of `value` (the `flavour = true` stub contract)."""
    produced = REAL_BUILTIN_STR(value)
    assert is_native(produced), (
        "native-flavour stub unsound on %r (%s): builtin_str produced %r (%s), "
        "which is not the native flavour"
        % (value, type(value).__name__, produced, type(produced).__name__))


def main():
    # --- upperSeq deep model (A-reference): boundary cases -----------------
    boundary = [
        "", "get", "post", "put", "delete", "head", "options", "patch",
        "trace", "connect",
        "GET", "POST", "Get", "pOsT",
        "a", "z", "A", "Z", "0", "9", "-", "_", " ", "abcXYZ123",
        "".join(chr(c) for c in range(0, 128)),   # every ASCII code point
    ]
    for s in boundary:
        check_upper_reference(s)

    # --- upperSeq deep model (A-reference): randomized ASCII fuzz ----------
    rng = random.Random(1724)
    for _ in range(20000):
        n = rng.randint(0, 16)
        s = "".join(chr(rng.randint(0, 127)) for _ in range(n))
        check_upper_reference(s)

    # exhaustive single-code-point sweep over the full ASCII range
    for c in range(0, 128):
        check_upper_reference(chr(c))

    # --- native-flavour stub (A-consumed): native and non-native arguments --
    native_args = ["POST", "get", "", "DELETE", "x"]
    # non-native arguments: on py3 there is no separate unicode type, so we
    # exercise the spectrum builtin_str must coerce -- text already-native plus
    # bytes (the other text flavour) -- and assert the product is native.
    other_flavour = [b"POST", b"get", b"", u"POST", u"get"]
    for v in native_args + other_flavour:
        check_native_stub(v)

    print("G-AX OK: upperSeq deep model (== str.upper) sound on %d boundary "
          "+ 20000 fuzz + 128 sweep inputs; native-flavour stub (builtin_str -> "
          "native flavour) sound on %d arguments"
          % (len(boundary), len(native_args) + len(other_flavour)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
