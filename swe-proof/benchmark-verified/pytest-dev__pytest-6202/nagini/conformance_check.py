#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-6202 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires / Ensures / Invariant / Assert / MustTerminate) stripped.
PSeq is shimmed as a plain tuple (PSeq(46) -> (46,); PSeq + PSeq -> tuple
concatenation), so the backward fold runs unchanged. There is no
@ContractOnly callee in this bundle (mapping.md section 3: no consumed axiom).

ORACLE: the REAL repo method the model models per mapping.md --
`PyobjMixin.getmodpath` in `_pytest.python` (the dotted path of a collected
node relative to its containing module). The gate applies the gold diff to
/testbed before this script runs and sets PYTHONPATH; this script never
applies any diff itself.

Bridge (mapping.md section 2): the modeled function takes the already
accumulated list of name parts as its input -- the earlier portion of
getmodpath (the listchain walk that builds that list) is upstream of the
modeled boundary and unchanged. To drive the real method on an arbitrary
part list, we hand it a synthetic node chain whose listchain() walk yields
exactly those parts: a module sentinel (an uninitialised Module instance so
the isinstance stop-condition fires) followed by one plain named node per
part, and call getmodpath with its default arguments. Types bridge as
  name part (str)      <-> tuple of Unicode code points (ord per char)
  list of parts        <-> tuple of such tuples
  returned path (str)  <-> tuple of code points of the result
The model's Requires (len(parts) >= 1) is honoured by generating only
non-empty part lists (the real walk always appends the node's own name, so
this matches the reachable domain).

>= 1e5 Requires-satisfying inputs: structured boundary part lists (single
parts, parts containing '.', '[', '.[', the F2P collection shape, empty-string
parts, deep nesting, non-ASCII names) plus 100000 fuzz rounds over a
'.['-rich alphabet with occasional arbitrary Unicode code points.
Pinned fuzz seed: 620202.

Exit 0 iff zero disagreements; on disagreement prints the input part list and
both outputs, then exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 620202
N_FUZZ = 100_000


# --- PSeq shim: a PSeq of ints is a plain tuple of ints -----------------------

def PSeq(*elems):
    return tuple(elems)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def modpath_of(parts):
    result = parts[len(parts) - 1]
    i = len(parts) - 1
    while i > 0:
        result = (parts[i - 1] + PSeq(46)) + result
        i = i - 1
    return result


# --- bridge: str name parts <-> code-point tuples ------------------------------

def cps(s):
    return tuple(ord(ch) for ch in s)


def to_str(codepoints):
    return "".join(chr(c) for c in codepoints)


def make_driver_class(PyobjMixin):
    """A minimal stand-in node exposing exactly what the real method reads:
    a listchain() whose walk yields the given part names."""
    class Driver:
        getmodpath = PyobjMixin.getmodpath

        def __init__(self, chain):
            self._chain = chain

        def listchain(self):
            return list(self._chain)

    return Driver


class _NamedNode:
    """A plain chain node (not a Module, not an Instance): contributes its
    name to the accumulated part list."""

    def __init__(self, name):
        self.name = name


def make_module_sentinel(Module):
    """An uninitialised Module instance: the walk's stop condition is an
    isinstance check, so only the type identity and a .name matter here."""
    mod = Module.__new__(Module)
    mod.name = "mod.py"
    return mod


def real_modpath(Driver, module_sentinel, names):
    """Run the REAL patched method on a synthetic chain built so that the
    upstream (unchanged) walk accumulates exactly `names`."""
    chain = [module_sentinel] + [_NamedNode(n) for n in names]
    return Driver(chain).getmodpath()


def check_one(Driver, module_sentinel, names):
    shadow = modpath_of(tuple(cps(n) for n in names))
    real = real_modpath(Driver, module_sentinel, names)
    if to_str(shadow) != real:
        return ("DISAGREEMENT\n  parts=%r\n  shadow=%r\n  real=%r"
                % (list(names), to_str(shadow), real))
    return None


def boundary_cases():
    """Part lists covering the single-part base case, separator-rich parts,
    the F2P collection shape, empty-string parts, and non-ASCII names."""
    return [
        ["testone"],
        [""],
        ["."], ["["], [".["], ["..["], [".[.["],
        ["test_boo[..[]"],
        ["TestX", "testmethod_one"],
        ["TestY", "testmethod_one"],
        ["TestY", "testmethod_two[.[]"],
        ["", ""],
        ["a.b", "c"],
        ["x", "["], ["x", ".["],
        [".[", ".["],
        ["Outer", "Inner", "test[.[x]"],
        ["A", "B", "C", "D", "E"],
        ["", ".[", ""],
        ["test[param.[0]"],
        ["Testé", "méthode[.[]"],
        ["\U0001f600", "t[.[\U0001f600]"],
        ["ends.", ".starts"],
        ["[.[]", "[.[]", "[.[]"],
    ]


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    from _pytest.python import Module, PyobjMixin

    Driver = make_driver_class(PyobjMixin)
    module_sentinel = make_module_sentinel(Module)

    checked = 0
    n_boundary = 0
    for names in boundary_cases():
        err = check_one(Driver, module_sentinel, names)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    alphabet = list(".[]abT0_")

    def rand_name():
        m = rng.randint(0, 12)
        out = []
        for _ in range(m):
            if rng.random() < 0.05:
                # arbitrary Unicode code point (surrogates excluded)
                c = rng.randint(1, 0x10FFFF)
                while 0xD800 <= c <= 0xDFFF:
                    c = rng.randint(1, 0x10FFFF)
                out.append(chr(c))
            else:
                out.append(rng.choice(alphabet))
        return "".join(out)

    for _ in range(N_FUZZ):
        nparts = rng.randint(1, 5)  # Requires: at least one part
        names = [rand_name() for _ in range(nparts)]
        err = check_one(Driver, module_sentinel, names)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real dotted-path method on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
