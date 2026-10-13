#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-22914 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with no contract
calls to strip (the impl region contains none). The @Pure helpers
(`is_supported`, `target_name`, `call_render`, the name-code constants) copy
over as plain functions on a PSeq realized as an immutable tuple shim; they
are used for a shadow-vs-pure self-consistency cross-check. There are no
@ContractOnly callees (the axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md — the
function-application rendering of the code printer (`PythonCodePrinter`,
whose dispatch consults the printer's supported-function table). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable. No table monkey-patching happens here:
if the patch were not applied, the supported-selection cases below would
disagree and the check would fail — that is the point of the diff.

Type bridge (mapping.md section 2):
  * repo `str` renderings <-> List[int] of Unicode code points
    (`s[k]` <-> `ord(s[k])`, concatenation <-> list `+`);
  * the function identity <-> integer name_code: 0 = the absolute-value
    function, 1 = the smaller-of selection, 2 = the larger-of selection,
    3 = any identity outside the supported table;
  * `joined_args` <-> the already-rendered argument text, comma-and-space
    joined, computed from the SAME real printer (`prntr._print(a)` per arg in
    the canonicalised application-argument order) — the unchanged
    sub-computation the model carries pre-rendered;
  * `fallback` <-> the unchanged non-call machinery's output for an
    unsupported identity, carried opaquely. For name_code 3 the real
    machinery's own rendering IS that input, so the oracle observation and
    the modeled input coincide by construction of the modeling boundary; the
    diff still exercises the shadow's unsupported branch (exact, unaltered
    pass-through) against it. For supported codes the fallback input is
    fuzz garbage the real rendering must not (and does not) depend on.

Input domain: Requires demand 0 <= name_code <= 3 and read access to the two
code-point lists. Supported-code inputs are realized through real
applications (the selection functions n-ary over >=2 distinct arguments so
the application does not collapse by a lattice identity; absolute value
unary, including compound arguments so the joined text carries spaces and
operators); unsupported-code inputs through undefined functions of 1-3
arguments. All generated inputs satisfy the Requires.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases, every
one diffed against a real printer rendering. Pinned fuzz seed: 22914.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repository under test only.
"""
import json
import random
import sys

SEED = 22914
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, copied over as plain functions --------------

def name_min():
    return 1


def name_max():
    return 2


def name_abs():
    return 0


def name_unknown():
    return 3


def is_supported(name_code):
    return name_code == 0 or name_code == 1 or name_code == 2


def target_name(name_code):
    if name_code == 0:
        return PSeq(97, 98, 115)        # 'abs'
    if name_code == 1:
        return PSeq(109, 105, 110)      # 'min'
    return PSeq(109, 97, 120)           # 'max'


def call_render(name_code, joined_args):
    return target_name(name_code) + PSeq(40) + joined_args + PSeq(41)


# --- the impl region of model.py, verbatim (it contains no contract calls) ---

def print_function_call(name_code, joined_args, fallback):
    if name_code == 0 or name_code == 1 or name_code == 2:
        nm = []  # type: list
        if name_code == 0:
            nm = [97, 98, 115]
        elif name_code == 1:
            nm = [109, 105, 110]
        else:
            nm = [109, 97, 120]
        result = nm + [40] + joined_args + [41]  # type: list
        return result
    empty = []  # type: list
    out = empty + fallback  # type: list
    return out


# --- bridge: str <-> List[int] of code points ---------------------------------

def to_codes(s):
    return [ord(c) for c in s]


def to_str(codes):
    return "".join(chr(c) for c in codes)


def check_supported(PythonCodePrinter, name_code, expr, garbage_fallback):
    """One supported-identity case: real rendering vs shadow. Returns an
    error string on disagreement, else None."""
    prntr = PythonCodePrinter()
    joined = ", ".join(prntr._print(a) for a in expr.args)
    observed = prntr.doprint(expr)                       # REAL printer
    shadow = print_function_call(name_code, to_codes(joined),
                                 list(garbage_fallback))
    if shadow != to_codes(observed):
        return ("DISAGREEMENT (supported rendering)\n"
                "  name_code=%d expr=%r joined=%r fallback(codes)=%r\n"
                "  shadow=%r\n  real=%r"
                % (name_code, str(expr), joined, garbage_fallback,
                   to_str(shadow), observed))
    # pure-helper self-consistency: the spec's call_render agrees with the
    # shadow impl on the same input.
    pure = call_render(name_code, PSeq(*to_codes(joined)))
    if list(pure._t) != shadow:
        return ("DISAGREEMENT (pure helper vs shadow impl)\n"
                "  name_code=%d joined=%r" % (name_code, joined))
    return None


def check_unsupported(PythonCodePrinter, expr):
    """One unsupported-identity case: the real machinery's output is the
    modeled fallback input; the shadow must return it exactly, unaltered."""
    prntr = PythonCodePrinter()
    observed = prntr.doprint(expr)                       # REAL printer
    fallback = to_codes(observed)
    shadow = print_function_call(3, to_codes(
        ", ".join(PythonCodePrinter()._print(a) for a in expr.args)),
        fallback)
    if shadow != fallback:
        return ("DISAGREEMENT (unsupported pass-through)\n"
                "  expr=%r\n  shadow=%r\n  real=%r"
                % (str(expr), to_str(shadow), observed))
    return None


def main():
    # REAL patched callees (PYTHONPATH=/testbed; the gate applied the patch).
    from sympy import Min, Max, Abs, Symbol, Function, Integer, Rational

    import importlib
    # NOTE: `import sympy.printing.pycode as pc` binds the exported `pycode`
    # FUNCTION (which shadows the submodule in the package namespace), so
    # load the real module object explicitly.
    pc = importlib.import_module("sympy.printing.pycode")
    PythonCodePrinter = pc.PythonCodePrinter

    rng = random.Random(SEED)

    # Symbol pool: plain identifiers plus a few printable oddities the
    # printer renders by name.
    names = (["x", "y", "z", "a", "b", "c", "t", "u", "p", "q",
              "alpha", "beta", "n1", "n2", "_under", "CamelCase"]
             + ["s%d" % i for i in range(40)])
    syms = [Symbol(n) for n in names]

    # Undefined-function pool for the unsupported identity (created once:
    # each construction mints a class).
    ufuncs = [Function("h_unmodeled_%d" % i) for i in range(30)]

    checked = 0
    disagreements = 0

    def fail(err):
        print(err)
        return 1

    def rand_garbage(maxlen=10):
        return [rng.randint(1, 0x10FFFF) for _ in range(rng.randint(0, maxlen))
                ] or []

    # ---- boundary cases ------------------------------------------------
    x, y, z, a = syms[0], syms[1], syms[2], syms[3]
    boundary = [
        (1, Min(x, y)),
        (2, Max(x, y)),
        (1, Min(x, y, z)),
        (2, Max(x, y, z, a)),
        (1, Min(*syms[:6])),
        (2, Max(*syms[:6])),
        (0, Abs(x)),
        (0, Abs(x - y)),              # joined text with spaces/operators
        (0, Abs(x * y + z)),
        (1, Min(x + 1, y)),           # mixed compound arguments
        (2, Max(x, Integer(7))),      # numeric argument
        (1, Min(x, Rational(1, 3))),
        (3, ufuncs[0](x)),
        (3, ufuncs[1](x, y)),
        (3, ufuncs[2](x, y, z)),
    ]
    for name_code, expr in boundary:
        if name_code == 3:
            err = check_unsupported(PythonCodePrinter, expr)
        else:
            fn = {0: Abs, 1: Min, 2: Max}[name_code]
            if expr.func is not fn:
                continue   # collapsed by evaluation; not this identity
            err = check_supported(PythonCodePrinter, name_code, expr,
                                  rand_garbage())
        if err:
            return fail(err)
        checked += 1

    # ---- fuzz ------------------------------------------------------------
    compounds = [x + y, x - y, x * y, x + 1, 2 * x, x - z + a]
    while checked < N_FUZZ + len(boundary):
        name_code = rng.randint(0, 3)
        if name_code == 3:
            f = rng.choice(ufuncs)
            args = rng.sample(syms, rng.randint(1, 3))
            err = check_unsupported(PythonCodePrinter, f(*args))
        elif name_code == 0:
            arg = (rng.choice(syms) if rng.random() < 0.7
                   else rng.choice(compounds))
            expr = Abs(arg)
            if expr.func is not Abs:
                continue   # simplified away (e.g. a constant factor pulled out)
            err = check_supported(PythonCodePrinter, 0, expr,
                                  rand_garbage())
        else:
            fn = Min if name_code == 1 else Max
            arity = rng.randint(2, 5)
            args = rng.sample(syms, arity)
            if rng.random() < 0.15:
                args[rng.randrange(arity)] = rng.choice(compounds)
            expr = fn(*args)
            if expr.func is not fn:
                continue   # collapsed by evaluation; resample
            err = check_supported(PythonCodePrinter, name_code, expr,
                                  rand_garbage())
        if err:
            return fail(err)
        checked += 1

    print("G-CONF OK: shadow impl == real code-printer rendering on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), checked - len(boundary), SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-free impl region, verbatim)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
