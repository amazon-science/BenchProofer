#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_renderArg
against the patched `_recursive_to_string` behaviour.

The impl region is all I/R (no A-tagged op), so this runs a real fuzz. The
shadow reproduces the Lean impl op-for-op: a leaf renders to its own string; a
list node renders its elements ', '-joined inside "[" .. "]"; a tuple node
renders its elements ', '-joined inside "(" .. ",)" (the trailing comma is the
fix). The unchanged leaf-printing callee `doprint` is realised as the identity
on string leaves (the real function's `isinstance(arg,str): return arg` branch),
which is exactly what the Arg.leaf refinement models.

We import the REAL patched `_recursive_to_string` from the installed sympy
(the gold patch is applied in-container) and assert zero disagreements over
>=10^5 fuzzed nested structures of python list/tuple/str leaves.

stdlib-only (plus the repo under test). exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 23262          # pinned in mapping.md
N = 120_000           # >= 10^5

# ASCII-ish leaf alphabet incl. the empty string (boundary).
def rand_leaf(rng):
    n = rng.randint(0, 4)
    return "".join(chr(rng.randint(0x61, 0x7a)) for _ in range(n))


def rand_struct(rng, depth):
    """Random nested structure of python list/tuple/str leaves."""
    if depth <= 0 or rng.random() < 0.45:
        return rand_leaf(rng)
    k = rng.randint(0, 4)          # node arity (0 exercises empty list/tuple)
    children = [rand_struct(rng, depth - 1) for _ in range(k)]
    return tuple(children) if rng.random() < 0.5 else list(children)


def shadow(arg):
    """R/I shadow of implementation_renderArg (the Lean impl, op-for-op)."""
    if isinstance(arg, str):
        return arg                                  # Arg.leaf s => s
    if isinstance(arg, list):
        parts = [shadow(e) for e in arg]
        return "[" + ", ".join(parts) + "]"
    if isinstance(arg, tuple):
        parts = [shadow(e) for e in arg]
        return "(" + ", ".join(parts) + ",)"        # THE FIX: trailing comma
    raise TypeError(f"unexpected leaf kind: {type(arg)}")


def main() -> int:
    try:
        from sympy.utilities.lambdify import _recursive_to_string
    except Exception as e:  # pragma: no cover
        print(f"G-CONF ERROR: cannot import _recursive_to_string: {e}")
        return 2

    # doprint stand-in: leaves are strings hitting `isinstance(arg,str): return
    # arg` inside the real function, so this is only used defensively.
    doprint = lambda x: str(x)

    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. the exact F2P input (1,)).
    fixed = [
        ("1",),                       # gh-23224: lambdify([], (1,)) -> "(1,)"
        ("1", "2"),                   # two-element tuple
        tuple(),                      # empty tuple
        ["a"],                        # one-element list (unchanged branch)
        [],                           # empty list
        ["a", ("b",)],                # list containing a singleton tuple
        (("x",),),                    # nested singleton tuples
        ("a", ("b", "c")),            # tuple containing a tuple
        "leaf",                       # bare leaf
    ]
    cases = fixed + [rand_struct(rng, 5) for _ in range(N)]

    for arg in cases:
        got = shadow(arg)
        want = _recursive_to_string(doprint, arg)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((arg, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, g, w in examples:
            print(f"  in={a!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
