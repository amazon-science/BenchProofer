#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7889.

Executes the REAL repo callee `_make_subclass`
(`sphinx/ext/autodoc/mock.py`, UNCHANGED by the patch) on inputs (boundary
cases plus randomized fuzzing) and asserts that every observation matches the
deep model `buildSubclass` (Solution.lean pure region).

The one kind-A check:

  (A-reference) the deep model `build_subclass` (== Solution.lean's
      `buildSubclass`) equals the real `_make_subclass`:
        * textual name  -> succeeds; result.__display_name__ == module + '.' + name
        * non-textual name -> raises TypeError (the bug the patch fixes:
              `module + '.' + name` cannot concat str+non-str, and `type(name,...)`
              requires a str name)

It also confirms `str()` of each fuzzed non-textual object yields exactly the
textual form `textForm` (Solution.lean) assumes — i.e. the modeled coercion is
faithful to the builtin the patch introduces.

Imports the repo module (the same `_make_subclass` the gold patch leaves
untouched) plus stdlib only. Exit 0 iff every obligation holds.
"""
import random
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _make_subclass   # real, UNCHANGED callee


# --- Solution.lean deep model `buildSubclass`, transliterated ----------------
# buildSubclass (module) (name : Key) : Except MockErr String
#   .str s -> if nameRejected s then Except.error .valueError
#             else Except.ok (module ++ "." ++ s)
#   .obj _ -> Except.error .typeError
# nameRejected s = s.contains (Char.ofNat 0)  -- a NUL char cannot name a class
# A Key is `("str", s)` (already textual) or `("obj", s)` (non-textual, rendering s).
def name_rejected(s):
    """Solution.lean `nameRejected`: a textual name carrying a NUL char is
    refused by the class machinery (cannot name a class)."""
    return "\x00" in s


def build_subclass(module, key):
    kind, _s = key
    if kind == "str":
        if name_rejected(_s):
            return ("err", "valueError")
        return ("ok", module + "." + _s)
    return ("err", "typeError")


def textform(key):
    """Solution.lean `textForm`: textual form of a key is always textual."""
    kind, s = key
    return ("str", s)        # str of a string is itself; str of an object is its rendering


def real_observe(module, name_value):
    """Run the REAL _make_subclass and reduce to the model's observation domain:
    ('ok', display_name) on success, ('err','typeError') on TypeError (a
    non-textual name), ('err','valueError') on ValueError (a textual name the
    class machinery refuses, e.g. one containing a NUL byte)."""
    try:
        cls = _make_subclass(name_value, module)
        return ("ok", cls.__display_name__)
    except ValueError:
        return ("err", "valueError")
    except TypeError:
        return ("err", "typeError")


def check_textual(module, s):
    """A-reference, textual-name leg: the model agrees with the real callee. On an
    admissible name the callee succeeds with display == module.name; on a refused
    name (NUL byte) it raises ValueError and the model returns valueError."""
    observed = real_observe(module, s)
    expected = build_subclass(module, ("str", s))
    assert observed == expected, (
        "buildSubclass deep model unsound on textual name %r (module %r): real "
        "_make_subclass gave %r, model gives %r" % (s, module, observed, expected))
    if name_rejected(s):
        assert observed == ("err", "valueError"), (
            "refused-name law broken on %r/%r: %r" % (module, s, observed))
    else:
        assert observed == ("ok", module + "." + s), (
            "display-name law broken on %r/%r: %r" % (module, s, observed))


def check_nontextual(module, obj):
    """A-reference, non-textual-name leg: real callee raises TypeError, and the
    model agrees; and str(obj) is the textual form textForm assumes."""
    observed = real_observe(module, obj)
    key = ("obj", str(obj))
    expected = build_subclass(module, key)              # model on the raw obj key
    assert observed == ("err", "typeError"), (
        "expected real _make_subclass to raise TypeError on non-textual name %r "
        "(module %r), got %r" % (obj, module, observed))
    assert observed == expected, (
        "buildSubclass deep model unsound on non-textual name %r: real gave %r, "
        "model gives %r" % (obj, observed, expected))
    # textForm faithfulness: the model's coerced key constructs successfully and
    # the real callee, given str(obj), produces module + '.' + str(obj).
    coerced = textform(key)                             # ("str", str(obj))
    observed_coerced = real_observe(module, str(obj))
    expected_coerced = build_subclass(module, coerced)
    assert observed_coerced == expected_coerced, (
        "textForm coercion unsound on %r: real _make_subclass(str(obj)) gave %r, "
        "model gives %r" % (obj, observed_coerced, expected_coerced))
    if name_rejected(str(obj)):
        assert observed_coerced == ("err", "valueError"), (
            "coerced refused-name law broken on %r: %r" % (obj, observed_coerced))
    else:
        assert observed_coerced == ("ok", module + "." + str(obj)), (
            "coerced display-name law broken on %r: %r" % (obj, observed_coerced))


def main():
    modules = ["", "_MockObject", "a.b.c", "pkg", "sphinx.ext.autodoc.mock"]

    # --- textual names: boundary cases (incl. NUL / control-byte names) ---
    textual_boundary = ["", "x", "T", "SomeClass", "a.b", "name with spaces",
                        "0", "__init__", "café", "•", "_MockObject",
                        "\x00", "\x00null", "pre\x00post", "a\x00",
                        "\t", "\n", "\x01", "\x1f", "\x7f"]
    for module in modules:
        for s in textual_boundary:
            check_textual(module, s)

    # --- textual names: randomized fuzz (alphabet includes NUL + controls) -
    rng = random.Random(7889)
    alphabet = list("abcDEF0123_.- TZ") + ["é", "•", "\x00", "\x01", "\x1f"]
    for _ in range(20000):
        n = rng.randint(0, 18)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        module = rng.choice(modules)
        check_textual(module, s)

    # --- non-textual names: the bug class (boundary) ----------------------
    T = TypeVar("T")
    U = TypeVar("U", covariant=True)

    class NulStr:
        """A non-textual object whose str() rendering carries a NUL byte: its
        textual form is `type()`-illegal, exercising the valueError leg through
        the coercion."""
        def __str__(self):
            return "bad\x00name"

    nontextual_boundary = [T, U, int, str, object, list, 0, 1, -5, 3.14,
                           None, True, ["a"], ("a",), {"k": "v"}, type,
                           TypeVar("Name"), NulStr()]
    for module in modules:
        for obj in nontextual_boundary:
            check_nontextual(module, obj)

    # --- non-textual names: randomized fuzz over TypeVars + ints ----------
    for _ in range(2000):
        choice = rng.randint(0, 2)
        if choice == 0:
            obj = TypeVar("V%d" % rng.randint(0, 9999))
        elif choice == 1:
            obj = rng.randint(-10000, 10000)
        else:
            obj = rng.random()
        module = rng.choice(modules)
        check_nontextual(module, obj)

    print("G-AX OK: buildSubclass deep model (== _make_subclass) sound on "
          "%d textual boundary + 20000 textual fuzz names and "
          "%d non-textual boundary + 2000 non-textual fuzz names; textForm "
          "coercion faithful to str()."
          % (len(modules) * len(textual_boundary),
             len(modules) * len(nontextual_boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
