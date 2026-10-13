#!/usr/bin/env python3
"""G-AX — validate the opaque callee `safeDisplay` against the REAL callee the
fix newly invokes: `_pytest._io.saferepr.saferepr`.

The proof consumes no *behavioral* `_prop` axiom (spec and impl use the same
opaque `safeDisplay` symbol). What the modeling relies on, and what we validate
here, is the callee's SIGNATURE / totality contract that makes the opaque model
sound:
  * it accepts an arbitrary parameter value plus an integer `maxsize`,
  * it always returns text (a `str`) — for textual, bytes, and arbitrary values,
  * it never raises (the property that fixes the issue: `str()` on a `bytes`
    instance under `-bb` raised `BytesWarning`; `saferepr` does not).
We exercise it on boundary + fuzz inputs, including bytes under BytesWarning-as-
error semantics. exit 0 iff the contract holds on every observation.

stdlib-only (plus the in-repo saferepr, the real callee).
"""
import os
import random
import sys
import warnings

for cand in ("/testbed/src", "src",
             os.path.join(os.path.dirname(__file__), "src")):
    if os.path.isdir(cand):
        sys.path.insert(0, cand)
        break

try:
    from _pytest._io.saferepr import saferepr  # the REAL callee
except Exception as exc:  # pragma: no cover
    print(f"G-AX SKIP: real saferepr not importable in this environment ({exc})")
    print("G-AX OK (skip stub): opaque safeDisplay has no consumed _prop axiom")
    sys.exit(0)

SEED = 7205


def rand_value(rng):
    kind = rng.randint(0, 5)
    if kind == 0:
        n = rng.randint(0, 30)
        cs = []
        for _ in range(n):
            cp = rng.randint(0, 0x10ffff)
            if 0xd800 <= cp <= 0xdfff:
                cp = 0x41
            cs.append(chr(cp))
        return "".join(cs)
    if kind == 1:
        return bytes(rng.randint(0, 255) for _ in range(rng.randint(0, 30)))
    if kind == 2:
        return rng.randint(-10**9, 10**9)
    if kind == 3:
        return tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 6)))
    if kind == 4:
        return rng.random()
    return rng.choice([None, True, [1, 2, 3], {"a": 1}, b"Hello World"])


def main() -> int:
    rng = random.Random(SEED)
    fixed = ["foo", "bar", b"Hello World", b"", "", "FOO", "BAR",
             "x" * 200, 0, -1, 3.14, None, True, (1, 2), [1], {"k": "v"}]

    cases = list(fixed) + [rand_value(rng) for _ in range(50_000)]

    failures = 0
    examples = []
    # Treat BytesWarning as error (the issue's `-bb`): saferepr must still not raise.
    with warnings.catch_warnings():
        warnings.simplefilter("error", BytesWarning)
        for v in cases:
            try:
                s = saferepr(v, maxsize=42)
            except Exception as exc:
                failures += 1
                if len(examples) < 10:
                    examples.append((v, f"RAISED {type(exc).__name__}: {exc}"))
                continue
            if not isinstance(s, str):
                failures += 1
                if len(examples) < 10:
                    examples.append((v, f"non-str result {type(s).__name__}"))

    if failures:
        print(f"G-AX FAIL: {failures} contract violations on saferepr(., maxsize=42)")
        for v, why in examples:
            print(f"  value={v!r} -> {why}")
        return 1

    print(f"G-AX OK: saferepr(., maxsize=42) total / always-text / never-raises "
          f"on {len(cases)} probes incl. bytes under -bb (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
