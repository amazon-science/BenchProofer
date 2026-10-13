#!/usr/bin/env python3
"""G-AX — A-reference soundness check for sympy__sympy-21930.

The bundle consumes NO `axiom <callee>_prop`. One sub-operation is modeled
DEEPLY as an A-reference (SPEC_GUIDE §3) and must be validated == the real
callee:

  `joinNames names` (front-recursive empty-string concatenation)
     ==  `"".join([i.name for i in self.args[k]])`

i.e. the in-order empty-string join of the index names that the indexed-symbol
renderer performs over its upper / lower index blocks. We validate it against the
REAL objects' `args[1]`/`args[2]` name lists.

Runs INSIDE the instance image (PYTHONPATH=/testbed). stdlib + the in-repo
`sympy` package only; no network. exit 0 iff sound.
"""
import sys

SEED = 21930
N = 60_000


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def shadow_join(names):
    # Lean: joinNames []=="" ; (x::xs)==x ++ joinNames xs
    out = ""
    for n in names:
        out = out + n
    return out


def main() -> int:
    try:
        from sympy import Symbol
        from sympy.physics.secondquant import AntiSymmetricTensor
    except Exception as e:  # pragma: no cover
        print(f"status=fail could not import real callees: {e!r}")
        return 1

    name_alpha = list("abcdefghijkABXY0123456789") + ["α", "β", "ψ"]
    checked = 0
    mismatches = 0

    def check(sym, up, lo):
        nonlocal checked, mismatches
        obj = AntiSymmetricTensor(Symbol(sym),
                                  tuple(Symbol(n) for n in up),
                                  tuple(Symbol(n) for n in lo))
        if getattr(obj, "func", None) is None or obj.func.__name__ != "AntiSymmetricTensor":
            return  # canonicalisation collapsed it; skip
        for k in (1, 2):
            real_join = "".join([i.name for i in obj.args[k]])
            model_join = shadow_join([i.name for i in obj.args[k]])
            if real_join != model_join:
                print(f"MISMATCH join args[{k}] sym={sym!r} up={up} lo={lo}: "
                      f"real={real_join!r} model={model_join!r}")
                mismatches += 1
        checked += 1

    # boundary / hand-picked
    for sym in ["t", "v", "f", "A"]:
        for up in [[], ["a"], ["a", "b"], ["a", "b", "c"]]:
            for lo in [[], ["i"], ["i", "j"]]:
                check(sym, up, lo)

    # fuzz
    rnd = _lcg(SEED)

    def rand_name():
        length = (next(rnd) % 4) + 1
        return "".join(name_alpha[next(rnd) % len(name_alpha)] for _ in range(length))

    for _ in range(N):
        sym = rand_name()
        nu = next(rnd) % 5
        nl = next(rnd) % 5
        up = [rand_name() for _ in range(nu)]
        lo = [rand_name() for _ in range(nl)]
        check(sym, up, lo)
        if mismatches:
            break

    if mismatches:
        print(f"checked={checked} mismatches={mismatches}")
        print("status=fail")
        return 1
    print(f"checked={checked} mismatches=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
