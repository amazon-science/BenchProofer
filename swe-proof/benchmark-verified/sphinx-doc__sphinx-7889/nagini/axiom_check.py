#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7889.

The one consumed axiom in model.py is `display_name` -- the abstraction of the
UNCHANGED placeholder-subclass fabricator

    sphinx.ext.autodoc.mock._make_subclass(name, module, superclass) -> type

restricted to the two properties the proof relies on:

  (Ensures) for a TEXTUAL name argument, the fabricated subclass's display name
      is exactly   module + '.' + name
      (model.py: display_name(True, name, module) == module ++ PSeq(46) ++ name,
       46 == ord('.')).

  (Requires) the fabricator is DEFINED ONLY for a textual name argument whose
      code points are all honest scalar values: no interior NUL code point and
      no surrogate code point (model.py: Requires(name_is_text and not (0 in
      name)) plus the Forall excluding 55296..57343).  This precondition must
      not over-claim, and it has THREE halves the real callee enforces:
        * a NON-textual name fails, since the body performs `module + '.' + name`
          (string concatenation) and `type(name, ...)` (which requires a str
          name) -- a TypeError;
        * a textual name that CONTAINS A NUL also fails, since `type(name, ...)`
          rejects it with `ValueError: type name must not contain null
          characters`.  (Being a str is NOT sufficient.)
        * a textual name that CONTAINS A SURROGATE code point (U+D800..U+DFFF)
          also fails, since `type(name, ...)` must encode the class name and a
          lone surrogate has no encoded form -- a UnicodeEncodeError.
      G-AX confirms the real callee raises in ALL THREE cases -- so the axiom
      promises nothing the real callee cannot deliver, and the pre-patch's
      modelled failure on a non-textual index is a real TypeError.

It also confirms the end-to-end behaviour the fix targets: handing the index on
UNCHANGED (pre-patch) raises for a non-textual index, whereas reducing it to its
textual rendering first (post-patch, `str(key)`) succeeds and names the result
after that rendering -- for textual AND non-textual indices alike.

Imports the REAL sphinx under test (the very module the gold patch edits);
nothing is stubbed.  Exit 0 iff every observation matches the axiom.
"""
import random
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _make_subclass, _MockObject


# --- (Ensures) display name == module + '.' + name, for textual names --------

def check_display_name(name, module):
    """Assert the real _make_subclass assigns display name module + '.' + name
    for a textual `name` -- the axiom's Ensures."""
    cls = _make_subclass(name, module)
    observed = cls.__display_name__
    expected = module + "." + name
    assert observed == expected, (
        "display_name axiom unsound on name=%r module=%r: real "
        "_make_subclass gave __display_name__=%r, axiom requires %r"
        % (name, module, observed, expected))
    # the fabricated object is a placeholder subclass (a _MockObject subclass)
    assert issubclass(cls, _MockObject), (
        "fabricated class is not a _MockObject subclass: %r" % (cls,))


# --- (Requires) the fabricator is defined only for a textual name ------------

def check_requires_textual(nontext_name, module):
    """Assert the real _make_subclass RAISES for a non-textual name -- so the
    axiom's Requires(name_is_text) does not over-claim."""
    try:
        cls = _make_subclass(nontext_name, module)
    except TypeError:
        return  # expected: precondition genuinely required
    # Some objects (e.g. ints) might survive type() but then the display-name
    # concatenation must still be a str op; if it produced a class at all the
    # axiom would be over-claiming for a non-text name, so flag it.
    raise AssertionError(
        "Requires(name_is_text) over-claims: real _make_subclass accepted "
        "non-textual name %r (-> %r) without raising" % (nontext_name, cls))


# --- (Requires) a textual name with an interior NUL is also rejected ---------

def check_requires_no_nul(nul_name, module):
    """Assert the real _make_subclass RAISES for a textual name that contains a
    NUL (code point 0) -- so the axiom's `not (0 in name)` half of the
    precondition does not over-claim.  `type(name, ...)` rejects a NUL in the
    name with `ValueError: type name must not contain null characters`, so the
    real fabricator cannot deliver the Ensures on such a name; the precondition
    must exclude it (it is NOT enough to be merely textual)."""
    assert isinstance(nul_name, str) and "\x00" in nul_name, (
        "test bug: %r is not a NUL-containing str" % (nul_name,))
    try:
        cls = _make_subclass(nul_name, module)
    except (ValueError, TypeError):
        return  # expected: NUL name genuinely rejected by type()
    raise AssertionError(
        "Requires(not (0 in name)) over-claims: real _make_subclass accepted "
        "NUL-containing name %r (-> %r) without raising" % (nul_name, cls))


# --- (Requires) a textual name with a surrogate code point is also rejected --

def check_requires_no_surrogate(surr_name, module):
    """Assert the real _make_subclass RAISES for a textual name that contains a
    surrogate code point (U+D800..U+DFFF) -- so the axiom's surrogate-excluding
    half of the precondition does not over-claim.  `type(name, ...)` must
    encode the class name, and a lone surrogate has no encoded form, so the
    real fabricator raises UnicodeEncodeError; the precondition must exclude
    such names (being a NUL-free str is NOT sufficient)."""
    assert isinstance(surr_name, str) and any(
        0xD800 <= ord(c) <= 0xDFFF for c in surr_name), (
        "test bug: %r carries no surrogate code point" % (surr_name,))
    try:
        cls = _make_subclass(surr_name, module)
    except (UnicodeEncodeError, ValueError, TypeError):
        return  # expected: surrogate-bearing name genuinely rejected
    raise AssertionError(
        "surrogate-excluding Requires over-claims: real _make_subclass "
        "accepted surrogate-bearing name %r (-> %r) without raising"
        % (surr_name, cls))


# --- end-to-end: the subscript behaviour the fix targets ---------------------

def check_subscript_endtoend(key, module):
    """Pre-patch hands `key` on unchanged; post-patch hands `str(key)`.

    Confirm: post-patch succeeds for any key and names the result after
    str(key); pre-patch raises exactly when key is non-textual."""
    # post-patch: str(key) coercion -- always succeeds, display = module.str(key)
    cls_post = _make_subclass(str(key), module)
    assert cls_post.__display_name__ == module + "." + str(key)

    # pre-patch: raw key -- succeeds iff key already textual
    if isinstance(key, str):
        cls_pre = _make_subclass(key, module)
        assert cls_pre.__display_name__ == module + "." + key
    else:
        try:
            _make_subclass(key, module)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "pre-patch unexpectedly succeeded on non-textual key %r" % (key,))


def main():
    # --- (Ensures) textual names: boundary + fuzz ----------------------------
    modules = ["", "a", "mod", "pkg.sub", "a.b.c", "MyModule", "x9"]
    text_names = ["", "A", "name", "SomeClass", "T", "x", "Foo.Bar",
                  "a_b", "9", "~T", "list", "Dict", "已", "café"]
    for module in modules:
        for name in text_names:
            check_display_name(name, module)

    rng = random.Random(7889)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_.0123"
                    "456789~ é•")
    for _ in range(20000):
        n = rng.randint(0, 16)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        m = rng.randint(0, 12)
        module = "".join(rng.choice(alphabet) for _ in range(m))
        check_display_name(name, module)

    # --- (Requires) non-textual names raise ----------------------------------
    T = TypeVar("T")
    S = TypeVar("S", covariant=True)
    nontextual = [T, S, TypeVar("U"), object(), [1, 2], {"k": 1}, (1, 2)]
    for module in modules:
        for nm in nontextual:
            check_requires_textual(nm, module)

    # --- (Requires) textual names with an interior NUL also raise -------------
    # The precondition is `name_is_text and not (0 in name)`: a name may be a
    # str and STILL be rejected if it carries a NUL code point, because
    # `type(name, ...)` raises `ValueError: type name must not contain null
    # characters`.  Sweep NUL in leading / interior / trailing / sole positions
    # so the axiom_check exercises the directive-7 control-character boundary
    # that a happy-path-only alphabet would miss.
    nul_names = ["\x00", "T\x00", "\x00T", "a\x00b", "name\x00", "\x00\x00",
                 "Foo\x00Bar", "café\x00", "已\x00"]
    for module in modules:
        for nn in nul_names:
            check_requires_no_nul(nn, module)

    # --- (Requires) textual names with a surrogate code point also raise ------
    # The precondition additionally excludes surrogate code points
    # (55296..57343): a str may carry a lone surrogate (e.g. from
    # surrogateescape decoding), and `type(name, ...)` rejects it with
    # UnicodeEncodeError because the class name cannot be encoded.  Sweep the
    # range boundaries (D800, DBFF, DC00, DFFF) in leading / interior /
    # trailing / sole positions so the boundary is genuinely exercised.
    surrogate_names = ["\ud800", "\udfff", "T\ud800", "\udc00T", "a\udbffb",
                       "name\udfff", "\ud834X", "Foo\ud800Bar"]
    for module in modules:
        for sn in surrogate_names:
            check_requires_no_surrogate(sn, module)

    # --- end-to-end subscript: the issue scenario ----------------------------
    # mock.SomeClass[T] (T a TypeVar) is the exact failing case in the report.
    e2e_keys = ["A", "name", "T", T, S, TypeVar("V"), 0, 3, object()]
    for module in ["mod", "pkg.sub", "_MockObject"]:
        for key in e2e_keys:
            check_subscript_endtoend(key, module)

    print("G-AX OK: display_name axiom sound -- Ensures (module + '.' + name) "
          "holds on %d boundary + 20000 fuzz textual names (all scalar-only); "
          "Requires (textual, NUL-free, surrogate-free) genuinely required: "
          "real _make_subclass raises on TypeVar/object/list/dict/tuple names, "
          "on NUL-containing textual names (type() rejects a NUL with "
          "ValueError) AND on surrogate-bearing textual names (type() rejects "
          "a lone surrogate with UnicodeEncodeError); end-to-end subscript "
          "matches (str(key) coercion succeeds for TypeVar indices, raw key "
          "raises)."
          % (len(modules) * len(text_names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
