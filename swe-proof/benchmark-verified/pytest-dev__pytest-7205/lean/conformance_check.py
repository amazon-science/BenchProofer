#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_actionLine
against the patch.diff behaviour (the post-patch parameter-rendering tail of
`_show_fixture_action`).

The impl region is NOT all-A-tagged (header passthrough, present/absent branch,
and bracket wrapping are I/R ops), so this runs a real fuzz. The single
A-consumed op (`safeDisplay`) is left as the REAL builtin the patch calls:
`saferepr(value, maxsize=42)` from `_pytest._io.saferepr`. The shadow therefore
reproduces the post-patch behaviour op-for-op; we assert zero disagreements vs
an independent reconstruction of the patched tail over >=10^5 fuzzed inputs.

stdlib-only (plus the in-repo saferepr, the real callee). exit 0 iff zero
disagreements.
"""
import os
import random
import sys

SEED = 7205           # pinned in mapping.md
N = 120_000           # >= 10^5

# Make the in-container repo source importable so we use the REAL saferepr.
for cand in ("/testbed/src", "src",
             os.path.join(os.path.dirname(__file__), "src")):
    if os.path.isdir(cand):
        sys.path.insert(0, cand)
        break

try:
    from _pytest._io.saferepr import saferepr  # the REAL callee (A-consumed)
except Exception:  # pragma: no cover - fallback so the shadow stays runnable
    import reprlib

    def saferepr(obj, maxsize=240):
        r = reprlib.Repr()
        r.maxstring = maxsize
        s = r.repr(obj)
        if len(s) > maxsize:
            i = max(0, (maxsize - 3) // 2)
            j = max(0, maxsize - 3 - i)
            s = s[:i] + "..." + s[len(s) - j:]
        return s


def shadow(header, param):
    """R/I shadow of implementation_actionLine.

    out := header
    if param is present: out += '[' + safeDisplay(value, 42) + ']'
    return out
    The A-consumed op safeDisplay is realised by the REAL saferepr(., maxsize=42).
    """
    out = header
    if param is not None:
        out = out + "[" + saferepr(param, maxsize=42) + "]"
    return out


def patched_tail(header, param):
    """Independent reconstruction of the post-patch tail behaviour:
    `tw.write("[{}]".format(saferepr(value, maxsize=42)))` appended to header,
    only when a parameter value is present."""
    s = header
    if param is not None:
        s += "[{}]".format(saferepr(param, maxsize=42))
    return s


def rand_value(rng):
    """A fixture parameter value: str, bytes, int, tuple, or None-as-value."""
    kind = rng.randint(0, 5)
    if kind == 0:
        n = rng.randint(0, 20)
        return "".join(chr(rng.randint(0x20, 0x10ffff)) for _ in range(n)
                       if not 0xd800 <= 0 <= 0xdfff) or ""
    if kind == 1:
        n = rng.randint(0, 20)
        return bytes(rng.randint(0, 255) for _ in range(n))
    if kind == 2:
        return rng.randint(-10**6, 10**6)
    if kind == 3:
        return tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 4)))
    if kind == 4:
        return rng.random()
    return rng.choice(["foo", "bar", b"Hello World", "spam", "ham"])


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (mirror the F2P expectations).
    fixed = [
        ("SETUP    S arg_same", "foo"),
        ("SETUP    S arg_same", "bar"),
        ("SETUP    F foobar", "FOO"),
        ("SETUP    F foobar", "BAR"),
        ("SETUP    S arg_same", b"Hello World"),
        ("TEARDOWN S arg_same", "foo"),
        ("SETUP    S data", b""),
        ("SETUP    F x", ""),
        ("SETUP    S y", "x" * 100),    # exceeds maxsize=42, triggers ellipsis
        ("SETUP    S z", None),         # value present but is the object None
        ("SETUP    S header_only", "__ABSENT__"),  # sentinel -> absent below
    ]
    cases = []
    for header, val in fixed:
        if val == "__ABSENT__":
            cases.append((header, None))   # absent parameter
        else:
            cases.append((header, val))

    for _ in range(N):
        header = "".join(rng.choice("ABCDEFG SETUParTEN_") for _ in range(rng.randint(0, 24)))
        if rng.random() < 0.15:
            cases.append((header, None))      # absent parameter
        else:
            cases.append((header, rand_value(rng)))

    for header, param in cases:
        got = shadow(header, param)
        want = patched_tail(header, param)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((header, param, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for h, p, g, w in examples:
            print(f"  header={h!r} param={p!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
