#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-7889.

The bundle models ONE fragment: `_MockObject.__getitem__`. Its Lean
implementation (`implementation_mockSubscript`) decides, for a parent display
name and a subscript key:

    name   = str(key)                         # the CHANGED op (render to text)  [R/I]
    result = module + '.' + name              # display-name join (A-reference)
                                              #   -> ok(result), never error post-fix

This script transliterates that render-and-join leg into Python
(`shadow_subscript`) and differential-tests it against the ORACLE: a faithful
in-process replica of the POST-PATCH `__getitem__` outcome
(`sphinx/ext/autodoc/mock.py:55-56` post-patch + the unchanged display-name
construction at mock.py:73):

    def __getitem__(self, key):                       # post-patch
        return _make_subclass(str(key), self.__display_name__, ...)()
    # _make_subclass display name = module + '.' + name

Outcomes are encoded as ("ok", display_name) (subclass constructed) or "error"
(TypeError raised), matching the Lean `Except Unit (List Char)`. Post-patch the
result is ALWAYS ("ok", ...) — the fix guarantees subscripting never raises —
so the differential also witnesses the absence of the error leg.

A key is modeled as either a real `str` (the `PyKey.str` case) or a non-`str`
object whose `str()` rendering is what the join consumes (the `PyKey.other`
case); the corpus includes a `TypeVar` (the issue's trigger).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 7889 (also in mapping.md).
"""
import sys

SEED = 7889
N = 120_000


# --- ORACLE: the post-patch __getitem__ outcome -----------------------------
# Faithful replica of mock.py:55-56 post-patch + the display-name construction.
def oracle_subscript(module: str, key):
    try:
        name = str(key)                       # post-patch: str(key)
        display = module + '.' + name         # _make_subclass display-name join
        return ("ok", display)
    except TypeError:
        return "error"


# --- shadow of implementation_mockSubscript (render-then-join) ---------------
# Mirrors Solution.lean: name = PyKey.str (strChars key); concatName.
# A key is given as ("str", s) or ("other", r); strChars returns the payload,
# wrapped as a textual component, so the join never hits the error leg.
def shadow_subscript(module: str, key):
    kind, payload = key
    name = payload                            # strChars: str s -> s ; other r -> r
    # concatName module (PyKey.str name) = ok(module ++ '.' :: name)
    return ("ok", module + '.' + name)


def _key_payload(key):
    # The textual rendering the model carries for a key (str or non-str).
    return str(key)


def disagree(module: str, real_key, model_key):
    got = oracle_subscript(module, real_key)
    want = shadow_subscript(module, model_key)
    if got != want:
        return (module, real_key, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


_ALPHABET = ['*', '.', '-', '_', '@', '/', ' ', ':', '0', '9',
             'a', 'b', 'z', 'A', 'Z', 'x', '~', '%', '+', '☃', 'ジ', 'ß']


def _edge_cases():
    from typing import TypeVar
    T = TypeVar('T')
    out = []
    # text keys (PyKey.str): real str s, model ("str", s)
    for module in ["", "mod", "pkg.mod", "☃"]:
        for s in ["", "T", "int", "List", "~T", "a.b", "  ", "*", "ジ"]:
            out.append((module, s, ("str", s)))
    # non-text keys (PyKey.other): real object, model ("other", str(obj))
    for module in ["mod", "pkg.mod", ""]:
        for k in [T, 5, 3.5, (1, 2), None, True]:
            out.append((module, k, ("other", str(k))))
    return out


def main() -> int:
    checked = 0

    for module, real_key, model_key in _edge_cases():
        d = disagree(module, real_key, model_key)
        if d:
            print(f"DISAGREE edge module={d[0]!r} key={d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        ml = next(rnd) % 9
        module = "".join(_ALPHABET[next(rnd) % len(_ALPHABET)] for _ in range(ml))
        # half the time a str key, half the time a non-str key
        if next(rnd) % 2 == 0:
            sl = next(rnd) % 11
            s = "".join(_ALPHABET[next(rnd) % len(_ALPHABET)] for _ in range(sl))
            real_key, model_key = s, ("str", s)
        else:
            choice = next(rnd) % 5
            obj = [123, 4.5, (1, 2), None, True][choice]
            real_key, model_key = obj, ("other", _key_payload(obj))
        d = disagree(module, real_key, model_key)
        if d:
            print(f"DISAGREE fuzz module={d[0]!r} key={d[1]!r}: oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
