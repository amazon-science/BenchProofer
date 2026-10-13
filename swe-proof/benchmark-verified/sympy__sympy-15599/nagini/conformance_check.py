#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15599 (nagini).

SHADOW: the impl region of model.py (`reduce_coefficients`), copied VERBATIM
below with the contract statement lines (Requires/Ensures/Invariant/Assert)
stripped — the model IS Python, no transliteration. The @Pure helper
`reduced_factor` copies over as a plain function. The single @ContractOnly
callee `residue` (the unchanged numeric remainder primitive, mapping.md
section 3.2) calls the REAL repo function: sympy `Integer.__mod__` via
`Integer(value) % Integer(m)`. No PSeq values cross the impl region (the
carrier is plain List[int]), so no sequence shim is needed.

ORACLE: the REAL patched repo code the model models per mapping.md section 1
— the per-factor integer-coefficient reduction of a product's non-modular
factor list inside the modulo evaluator's product branch
(sympy/core/mod.py, `Mod.eval`). The gate applies patch.diff to /testbed
before this script runs (this script does NOT apply it); PYTHONPATH=/testbed
makes the patched module importable. Because the modeled behaviour is an
inline block of a larger classmethod rather than a standalone function, the
oracle is obtained by locating that exact statement in the patched module's
AST (the unique conditional inside `Mod.eval` whose test consults the
divisor's integer-ness and whose body loops over the factor list) and
executing the REAL statement object — the repo's own code, byte for byte,
not a transliteration — over controlled bindings of the names it reads
(the factor list, the divisor, and the singleton registry).

An end-to-end grounding leg additionally drives the public `Mod(p, q)`
entry point on products of an integer coefficient and an opaque integer
symbol, asserting the coefficient-shrinking observable the tests read
(a product coefficient congruent to a smaller one modulo m yields the same
Mod object; a coefficient that is a multiple of m yields zero).

TYPE BRIDGE (mapping.md section 2): factor k <-> (is_int[k], value[k]);
  is_int[k] == 1  <-> a concrete Integer factor with int(factor) == value[k]
  is_int[k] == 0  <-> an opaque (non-Integer) factor: a symbol, a symbolic
                      product/power, or a non-integer number — its carried
                      value[k] is an irrelevant placeholder, and the bridge
                      obligation is that the real factor object is left
                      identically unchanged while the shadow echoes value[k]
  m               <-> the divisor as an Integer, with int(divisor) == m
The rewritten list compares positionally: at integer positions the real
output factor must be an Integer whose int() equals the shadow's value; at
opaque positions the real output must be the very same object that went in
and the shadow must echo the placeholder.

INPUT DOMAIN: the Requires are len(is_int) == len(value) and m >= 2; the
carrier's meaningful tag alphabet is {0, 1} (mapping.md section 2 — the tag
is the factor's integer-ness, so only 0/1 have a repo preimage under the
bridge). Generation covers: the empty factor list, single-factor lists over
a dense value grid straddling the residue boundaries (negatives, zero,
in-range values, exact multiples of m, values just above/below multiples),
opaque-only lists, mixed lists, long lists, small and large moduli, and
huge coefficient magnitudes.

>= 1e5 Requires-satisfying inputs: boundary catalogue + 100000 fuzz lists.
Pinned fuzz seed: 15599.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import ast
import inspect
import json
import random
import sys

SEED = 15599
N_FUZZ = 100_000


# --- real-callee bridge for the @ContractOnly symbol --------------------------
# `residue` models the unchanged numeric remainder primitive; per the G-CONF
# contract a @ContractOnly callee calls the REAL repo function.

_Integer = None  # bound in main() after the repo import


def residue(value, m):
    return int(_Integer(value) % _Integer(m))


# --- pure region of model.py, copied as a plain function ----------------------

def reduced_factor(is_int, value, m):
    if is_int == 1 and residue(value, m) != 0:
        return residue(value, m)
    return value


# --- impl region of model.py, VERBATIM, contract calls stripped ---------------

def reduce_coefficients(is_int, value, m):
    n = len(value)
    result = []  # type: list
    k = 0
    while k < n:
        if is_int[k] == 1 and residue(value[k], m) != 0:
            v = residue(value[k], m)
        else:
            v = value[k]
        old_result = result  # noqa: F841  (kept: verbatim impl line)
        result = result + [v]
        k = k + 1
    return result


# --- oracle: locate and compile the real rewrite block from the patched repo --

def load_rewrite_block(mod_module):
    """Find, inside the patched module's `Mod.eval`, the unique conditional
    whose test consults the divisor's integer-ness and whose body loops over
    the factor list, and compile that REAL statement for execution."""
    src = inspect.getsource(mod_module)
    tree = ast.parse(src)
    eval_fn = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Mod":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "eval":
                    eval_fn = item
    if eval_fn is None:
        raise RuntimeError("could not locate Mod.eval in the patched module")
    hits = [n for n in ast.walk(eval_fn)
            if isinstance(n, ast.If)
            and "is_Integer" in ast.dump(n.test)
            and any(isinstance(b, ast.For) for b in n.body)]
    if len(hits) != 1:
        raise RuntimeError("expected exactly one factor-rewrite conditional "
                           "in Mod.eval, found %d" % len(hits))
    module = ast.parse("")  # empty module shell (portable across versions)
    module.body = [hits[0]]
    ast.fix_missing_locations(module)
    return compile(module, "<real-rewrite-block>", "exec")


def real_rewrite(code, S, factors, q):
    """Execute the real rewrite block over a fresh binding of the names it
    reads; return the rewritten factor list."""
    ns = {"non_mod_l": list(factors), "q": q, "S": S}
    exec(code, ns)
    return ns["non_mod_l"]


# --- differential check on one carrier input -----------------------------------

def check_one(env, is_int, value, m):
    """Run shadow and real block on one (is_int, value, m) input; return an
    error string on disagreement, else None."""
    factors = []
    for k in range(len(is_int)):
        if is_int[k] == 1:
            factors.append(env["Integer"](value[k]))
        else:
            factors.append(env["opaque_pool"][env["rng"].randrange(
                len(env["opaque_pool"]))])
    real = real_rewrite(env["code"], env["S"], factors, env["Integer"](m))
    shadow = reduce_coefficients(list(is_int), list(value), m)
    inp = "is_int=%r value=%r m=%r factors=%r" % (is_int, value, m, factors)
    if len(real) != len(shadow) or len(shadow) != len(value):
        return ("DISAGREEMENT (length)\n  input: %s\n  shadow=%r\n  real=%r"
                % (inp, shadow, real))
    for k in range(len(value)):
        if is_int[k] == 1:
            if not real[k].is_Integer or int(real[k]) != shadow[k]:
                return ("DISAGREEMENT (integer factor %d)\n  input: %s\n"
                        "  shadow=%r\n  real=%r" % (k, inp, shadow, real))
        else:
            # opaque factor: real output must be the identical object,
            # shadow output must echo the carried placeholder
            if real[k] is not factors[k] or shadow[k] != value[k]:
                return ("DISAGREEMENT (opaque factor %d)\n  input: %s\n"
                        "  shadow=%r\n  real=%r" % (k, inp, shadow, real))
    return None


# --- input generation ------------------------------------------------------------

def boundary_inputs():
    cases = []
    # the empty factor list, at several moduli
    for m in (2, 3, 4, 7, 100):
        cases.append(([], [], m))
    # single integer factor: dense value grid straddling residue boundaries
    for m in (2, 3, 4, 5, 8, 12):
        for v in (-2 * m, -m - 1, -m, -m + 1, -1, 0, 1, m - 1, m, m + 1,
                  2 * m, 2 * m + 1, 3, 8, 10 ** 9, -(10 ** 9), 10 ** 18):
            cases.append(([1], [v], m))
    # single opaque factor (placeholder values incl. extremes)
    for m in (2, 4, 10):
        for v in (0, 1, -7, 10 ** 12):
            cases.append(([0], [v], m))
    # mixed lists: every tag pattern of length 3 over a residue-boundary grid
    for m in (2, 4):
        for pat in range(8):
            tags = [(pat >> b) & 1 for b in range(3)]
            cases.append((tags, [3, 2 * m, m - 1], m))
            cases.append((tags, [-1, 0, m], m))
    # long lists
    cases.append(([1] * 12, list(range(-6, 6)), 4))
    cases.append(([0, 1] * 6, [5] * 12, 3))
    return cases


def fuzz_input(rng):
    n = rng.randint(0, 8)
    is_int = [rng.randint(0, 1) for _ in range(n)]
    value = []
    for _ in range(n):
        r = rng.random()
        if r < 0.70:
            value.append(rng.randint(-100, 100))
        elif r < 0.90:
            value.append(rng.randint(-10 ** 6, 10 ** 6))
        else:
            value.append(rng.randint(-10 ** 18, 10 ** 18))
    r = rng.random()
    if r < 0.70:
        m = rng.randint(2, 12)
    elif r < 0.95:
        m = rng.randint(2, 10 ** 4)
    else:
        m = rng.randint(2, 10 ** 9)
    return is_int, value, m


# --- end-to-end grounding through the public entry point --------------------------

def grounding_leg(env):
    """Drive the full public Mod on products coefficient * opaque-integer
    symbol; the coefficient-shrinking observable must hold."""
    Mod, Integer, Symbol = env["Mod"], env["Integer"], env["Symbol"]
    i = Symbol("i", integer=True)
    for m in (2, 3, 4, 5, 7):
        for c in range(-3 * m, 3 * m + 1):
            got = Mod(c * i, m)
            want = Mod((c % m) * i, m)
            if got != want:
                return ("DISAGREEMENT (end-to-end)\n  input: coeff=%d m=%d\n"
                        "  full evaluation gave %r, expected %r"
                        % (c, m, got, want))
            if c % m == 0 and got != 0:
                return ("DISAGREEMENT (end-to-end zero)\n  input: coeff=%d "
                        "m=%d\n  full evaluation gave %r, expected 0"
                        % (c, m, got))
    return None


def main():
    global _Integer
    import importlib
    mod_module = importlib.import_module("sympy.core.mod")
    from sympy import Integer, S, Symbol, Rational, Float, Mod, sqrt
    _Integer = Integer

    x = Symbol("x")
    y = Symbol("y")
    i = Symbol("i", integer=True, positive=True)
    opaque_pool = [x, y, i, x * y, i * x, x ** 2, Rational(1, 3),
                   Rational(7, 2), Float("2.5"), sqrt(2)]

    env = {
        "code": load_rewrite_block(mod_module),
        "Integer": Integer,
        "S": S,
        "Mod": Mod,
        "Symbol": Symbol,
        "opaque_pool": opaque_pool,
        "rng": random.Random(SEED + 1),  # opaque-object picker (bridge-only)
    }

    err = grounding_leg(env)
    if err:
        print(err)
        return 1

    checked = 0
    n_boundary = 0
    for is_int, value, m in boundary_inputs():
        err = check_one(env, is_int, value, m)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    n_fuzz = 0
    while n_fuzz < N_FUZZ:
        is_int, value, m = fuzz_input(rng)
        # Requires mirror: equal lengths (by construction) and m >= 2
        if len(is_int) != len(value) or m < 2:
            continue
        err = check_one(env, is_int, value, m)
        if err:
            print(err)
            return 1
        checked += 1
        n_fuzz += 1

    print("G-CONF OK: shadow impl == real factor-rewrite block on %d inputs "
          "(%d boundary + %d fuzz, seed %d); end-to-end grounding leg passed."
          % (checked, n_boundary, n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
