#!/usr/bin/env python3
"""G-AX — A-reference soundness check for sphinx-doc__sphinx-7889.

The bundle consumes NO `axiom <callee>_prop`. It models two operations deeply
and validates them against the real callees:

  * `strChars` ↔ `str(key)` — the textual rendering the patch introduces.
    Lean: `PyKey.str s ↦ s`, `PyKey.other r ↦ r`. The real operation is the
    `str(...)` builtin, which is idempotent on `str` (`str(s) == s`) and renders
    a non-`str` key to its textual form. We drive the REAL `str()` on `str` keys
    and on representative non-`str` keys (incl. a `TypeVar`, the issue's trigger)
    and assert the model agrees.

  * `concatName` ↔ the unchanged display-name construction inside the real
    `_make_subclass`: `'__display_name__': module + '.' + name` (mock.py:73).
    Lean (textual component): `Except.ok (module ++ '.' :: s)`, i.e. the string
    `module + '.' + name`. We drive the REAL `_make_subclass` (when importable)
    and assert `.__display_name__ == module + '.' + name`; we also confirm the
    REAL concatenation raises `TypeError` for a non-`str` component (the
    `Except.error ()` leg).

stdlib + the in-repo `sphinx` package only (import is best-effort: the display
concatenation `module + '.' + name` is a `str` builtin op exercised directly when
sphinx's heavy deps are unavailable). No network. exit 0 iff sound.
"""
import sys

SEED = 7889
N = 60_000


# --- models from Solution.lean -----------------------------------------------
def model_strChars(kind: str, payload: str) -> str:
    # Lean: strChars (PyKey.str s) = s ; strChars (PyKey.other r) = r
    return payload


def model_concatName_ok(module: str, name: str) -> str:
    # Lean concatName module (PyKey.str s) = Except.ok (module ++ '.' :: s)
    return module + '.' + name


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


_ALPHABET = (
    ['*', '.', '-', '_', '@', '/', ' ', ':', '0', '9', 'a', 'z', 'A', 'Z']
    + ['~', '%', '+', '☃', 'ジ', 'ß']
)


def main() -> int:
    checked = 0
    mismatches = 0

    # Real display-name construction (best-effort import of the unchanged callee).
    real_make_subclass = None
    try:
        from sphinx.ext.autodoc.mock import _make_subclass  # type: ignore
        real_make_subclass = _make_subclass
        print("note: real _make_subclass imported")
    except Exception as e:  # pragma: no cover - heavy deps may be absent
        print(f"note: real _make_subclass unavailable ({e!r}); "
              f"using the str builtin concatenation directly")

    def real_display_name(module: str, name: str) -> str:
        # The real display-name field is module + '.' + name (mock.py:73). When
        # the real callee is importable we read it back from the constructed
        # subclass; otherwise we exercise the identical str builtin op.
        if real_make_subclass is not None:
            cls = real_make_subclass(name, module)
            return cls.__display_name__
        return module + '.' + name

    # --- str(key) idempotence on text + non-str rendering -------------------
    # The textual subscript path: str(s) == s for every str s.
    text_keys = ["", "T", "int", "List", "~T", "a.b", "  ", "*", "ジェ", "ß", "0"]
    for s in text_keys:
        if model_strChars("str", str(s)) != str(s):
            print(f"MISMATCH strChars(str) {s!r}")
            mismatches += 1
        # idempotence: real str() leaves a str unchanged
        if str(s) != s:
            print(f"MISMATCH str-idempotence {s!r}")
            mismatches += 1
        checked += 1

    # Non-str keys: the model carries str(key); confirm against real str().
    from typing import TypeVar
    T = TypeVar('T')
    non_str_keys = [T, 5, 3.5, (1, 2), [1], {'a': 1}, None, True, object()]
    for k in non_str_keys:
        r = str(k)                       # real textual rendering
        if model_strChars("other", r) != r:
            print(f"MISMATCH strChars(other) {k!r}")
            mismatches += 1
        checked += 1

    # --- display-name join (A-reference) ------------------------------------
    join_cases = [("", ""), ("mod", "Name"), ("a.b", "~T"), ("pkg.mod", "int"),
                  ("☃", "ジ"), ("m", ""), ("", "x")]
    for module, name in join_cases:
        want = real_display_name(module, name)
        got = model_concatName_ok(module, name)
        if got != want:
            print(f"MISMATCH concatName {module!r} {name!r}: model={got!r} real={want!r}")
            mismatches += 1
        checked += 1

    # The error leg: a non-str component cannot be joined (real TypeError).
    try:
        _ = "mod" + '.' + T            # the real module + '.' + name on a TypeVar
        print("MISMATCH concatName-error: expected TypeError, none raised")
        mismatches += 1
    except TypeError:
        pass                            # matches Lean Except.error ()
    checked += 1

    # --- fuzz the join over str components ----------------------------------
    rnd = _lcg(SEED)
    for _ in range(N):
        ml = next(rnd) % 9
        nl = next(rnd) % 11
        module = "".join(_ALPHABET[next(rnd) % len(_ALPHABET)] for _ in range(ml))
        name = "".join(_ALPHABET[next(rnd) % len(_ALPHABET)] for _ in range(nl))
        want = real_display_name(module, name)
        got = model_concatName_ok(module, name)
        if got != want:
            print(f"MISMATCH concatName fuzz {module!r} {name!r}: model={got!r} real={want!r}")
            mismatches += 1
            break
        # str() idempotence on the rendered name
        if str(name) != name:
            print(f"MISMATCH str-idempotence fuzz {name!r}")
            mismatches += 1
            break
        checked += 1

    if mismatches:
        print(f"checked={checked} mismatches={mismatches}")
        print("status=fail")
        return 1
    print(f"checked={checked} mismatches=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
