#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""G-AX executable soundness check for psf__requests-1724.

Executes the REAL callees the construction site relies on and asserts that
every observation matches the model (model.py), on boundary cases over the
HTTP-method alphabet plus randomized fuzzing.

The two kind-A checks:

  (A-consumed) the `to_native` axiom (model.py axioms region) stands for the
      unchanged native-text-flavour constructor that the construction site now
      applies to the supplied method. Its only consumed obligation is
      `Ensures(native_form(Result()))`: the flavour it yields IS the native text
      flavour, independent of the argument flavour (which flavour value that is
      stays uninterpreted, so the model cannot name it without calling the
      constructor -- mapping.md 3.1). The real callee is `requests.compat.builtin_str` (which is the
      native `str` constructor on every supported interpreter; on the Python-2
      runtime that the issue reports, it is the byte-`str` constructor, NOT the
      module-level `unicode` alias). G-AX asserts that applying it to either a
      native or a non-native argument always yields a native value.

  (A-reference) the deep model `upper_seq` / `upper_cp` (model.py pure region)
      == the real case-normalisation `str.upper` on the ASCII domain the method
      names inhabit:
        'a'..'z' (97..122) -> 'A'..'Z' (65..90),  every other code point id.
      The deep model is validated == the real callee out-of-band here (it is
      NOT a consumed axiom).

Imports nothing repo-specific beyond `requests.compat.builtin_str` (the very
symbol the gold patch imports and calls); falls back to the stdlib native
`str` constructor if requests is not importable. Exit 0 iff every obligation
holds.

RUNTIME: the instance image for this bundle runs Python 2.7.18, which is the
interpreter the reported failure is about and the only one on which the
native/non-native text split this file checks (`str` vs `unicode`) exists at
all. This file is therefore written to the Python-2 language so that the
assertions actually execute on the interpreter hosting the real callees.
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
    """Reference of model.py's deep model `upper_cp` (one code point)."""
    if 97 <= c <= 122:        # 'a'..'z' -> 'A'..'Z'
        return c - 32
    return c


def upper_seq(codepoints):
    """Reference of model.py's deep model `upper_seq` (per-code-point fold)."""
    return [upper_cp(c) for c in codepoints]


def check_upper_reference(s):
    """Assert the deep model upper_seq(s) == the REAL str.upper(s) (ASCII)."""
    observed = [ord(ch) for ch in s.upper()]          # real callee
    expected = upper_seq([ord(ch) for ch in s])       # deep model
    assert observed == expected, (
        "upper_seq deep model unsound on %r: str.upper gave %r, "
        "deep model gives %r" % (s, observed, expected))


def is_native(value):
    """The native text flavour == the builtin `str` type on the running
    interpreter (`str` on py3; the byte-`str` on py2)."""
    return type(value) is str


def check_to_native_axiom(value):
    """Assert the REAL builtin_str(value) is of the native text flavour,
    regardless of the flavour of `value` -- the to_native axiom's Ensures,
    native_form(Result()), read on the real callee."""
    produced = REAL_BUILTIN_STR(value)
    assert is_native(produced), (
        "to_native axiom unsound on %r (%s): builtin_str produced %r (%s), "
        "which is not the native flavour"
        % (value, type(value).__name__, produced, type(produced).__name__))


def main():
    # --- upper_seq deep model (A-reference): boundary cases ----------------
    boundary = [
        "", "get", "post", "put", "delete", "head", "options", "patch",
        "trace", "connect",
        "GET", "POST", "Get", "pOsT",
        "a", "z", "A", "Z", "0", "9", "-", "_", " ", "abcXYZ123",
        "".join(chr(c) for c in range(0, 128)),   # every ASCII code point
    ]
    for s in boundary:
        check_upper_reference(s)

    # --- upper_seq deep model (A-reference): randomized ASCII fuzz ----------
    rng = random.Random(1724)
    for _ in range(20000):
        n = rng.randint(0, 16)
        s = "".join(chr(rng.randint(0, 127)) for _ in range(n))
        check_upper_reference(s)

    # exhaustive single-code-point sweep over the full ASCII range
    for c in range(0, 128):
        check_upper_reference(chr(c))

    # --- to_native axiom (A-consumed): native and non-native arguments -----
    # native arguments (already the native flavour)
    native_args = ["POST", "get", "", "DELETE", "x"]
    # non-native arguments. On Python 2 (this image's runtime) the non-native
    # text flavour is a real builtin, `unicode`, and it is exactly the flavour
    # the reported failure supplies -- so it is exercised directly, alongside
    # the byte-flavour arguments builtin_str must also coerce. On Python 3
    # there is no separate unicode type, so the same list degenerates to
    # already-native text plus bytes; the asserted obligation is identical.
    other_flavour = [b"POST", b"get", b"", u"POST", u"get", u"", u"PoSt-_.9"]
    for v in native_args + other_flavour:
        check_to_native_axiom(v)

    print("G-AX OK: upper_seq deep model (== str.upper) sound on %d boundary "
          "+ 20000 fuzz + 128 sweep inputs; to_native axiom (builtin_str -> "
          "native flavour) sound on %d arguments"
          % (len(boundary), len(native_args) + len(other_flavour)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
