#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7454 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. PSeq is realized as an
immutable tuple shim (constructor, take, equality — the only operations the
impl and pure helpers use); ToSeq lifts a plain list into the shim. The @Pure
helpers (name_value / tag_value / tag_type / kind_for) copy over as plain
functions. There are no @ContractOnly callees in this bundle (meta.json
axioms = []), so no real-repo callee is substituted inside the shadow.

ORACLE: the REAL patched repo function the model models per mapping.md —
the nested helper `make_xref` inside `_parse_annotation` in
sphinx/domains/python.py. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. Because
the helper is nested, its code object is extracted from the enclosing
function's constants and materialized against the module globals (it closes
over nothing — verified via co_freevars — so this is the function itself,
not a re-implementation). The resulting docutils node's two modeled fields
are read back: 'reftype' (model: kind) and 'reftarget' (model: target).

Type bridge (mapping.md section 2): str <-> List[int] of Unicode code points,
s <-> [ord(ch) for ch in s]; the bridge is a bijection on valid code points,
so fuzzing is over str values directly and shadow outputs are decoded back to
str for the comparison.

Input domain: Requires demands only read access to the input list, i.e. any
code-point sequence; under the str refinement that is any str. Boundary cases
cover the discriminating name, near-miss spellings, common annotation names,
the empty string, and non-ASCII text; fuzz draws random-length strings over an
identifier-ish alphabet plus occasional arbitrary Unicode code points.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz strings.
Pinned fuzz seed: 745400.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
import types

SEED = 745400
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence with the operations the model uses ---------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ----------------------------

def name_value():
    # the singleton value name, as Unicode code points
    return PSeq(78, 111, 110, 101)


def tag_value():
    # the constant kind tag for a value reference, as Unicode code points
    return PSeq(111, 98, 106)


def tag_type():
    # the constant kind tag for an ordinary type reference, as code points
    return PSeq(99, 108, 97, 115, 115)


def kind_for(text):
    if text == name_value():
        return tag_value()
    return tag_type()


# --- CrossReference carrier, contract calls stripped ----------------------------

class CrossReference:
    def __init__(self):
        self.kind = []
        self.target = []


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def make_cross_reference(text):
    ref = CrossReference()
    target = []
    i = 0
    while i < len(text):
        target = target + [text[i]]
        i = i + 1
    ref.target = target
    if ToSeq(text) == name_value():
        ref.kind = [111, 98, 106]
    else:
        ref.kind = [99, 108, 97, 115, 115]
    return ref


# --- oracle: the real nested repo helper ---------------------------------------

def load_real_helper():
    """Materialize the nested helper from the patched module: pull its code
    object out of the enclosing function's constants and bind it to the module
    globals (it has no free variables, so this IS the repo function)."""
    import sphinx.domains.python as pymod
    outer = pymod._parse_annotation
    codes = [c for c in outer.__code__.co_consts
             if isinstance(c, types.CodeType) and c.co_name == "make_xref"]
    assert len(codes) == 1, "expected exactly one nested make_xref code object"
    code = codes[0]
    assert code.co_freevars == (), (
        "nested helper unexpectedly closes over enclosing state: %r"
        % (code.co_freevars,))
    return types.FunctionType(code, pymod.__dict__)


# --- bridge + comparison --------------------------------------------------------

def check_text(real_fn, text):
    """Run shadow and oracle on one input string; return an error string on
    disagreement, else None."""
    codepoints = [ord(ch) for ch in text]
    shadow = make_cross_reference(codepoints)
    shadow_kind = "".join(chr(c) for c in shadow.kind)
    shadow_target = "".join(chr(c) for c in shadow.target)

    node = real_fn(text)
    real_kind = node.get("reftype")
    real_target = node.get("reftarget")

    if shadow_kind != real_kind or shadow_target != real_target:
        return ("DISAGREEMENT\n  input=%r\n  shadow: kind=%r target=%r\n"
                "  real:   kind=%r target=%r"
                % (text, shadow_kind, shadow_target, real_kind, real_target))
    return None


def boundary_texts():
    return [
        "None",                    # the discriminating name itself
        "none", "NONE", "nONE", "None ", " None", "Nonee", "Non", "N",
        "NoneType",                # near-miss spellings
        "",                        # empty string
        "int", "str", "float", "bool", "bytes", "object", "type",
        "List", "Dict", "Tuple", "Optional", "Any", "Callable",
        "obj", "class",            # the tag spellings as ordinary names
        "typing.Optional", "x.y.z", "List[int]",
        "Néné", "Ｎｏｎｅ", " ", "a\tb", "None\n", "\x00",  # non-ASCII / control
    ]


def rand_text(rng, alphabet):
    n = rng.randint(0, 12)
    if rng.random() < 0.05:
        # occasional arbitrary Unicode code points (excluding surrogates)
        out = []
        for _ in range(n):
            cp = rng.randint(0, 0x10FFFF)
            while 0xD800 <= cp <= 0xDFFF:
                cp = rng.randint(0, 0x10FFFF)
            out.append(chr(cp))
        return "".join(out)
    if rng.random() < 0.10:
        # mutations in the neighbourhood of the discriminating name
        base = list("None")
        k = rng.randrange(4)
        op = rng.random()
        if op < 0.34:
            base[k] = rng.choice(alphabet)
        elif op < 0.67:
            base.insert(k, rng.choice(alphabet))
        else:
            del base[k]
        return "".join(base)
    return "".join(rng.choice(alphabet) for _ in range(n))


def main():
    real_fn = load_real_helper()

    checked = 0
    for text in boundary_texts():
        err = check_text(real_fn, text)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    alphabet = list("abcdefghijklmnopqrstuvwxyz"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.[], ")
    for _ in range(N_FUZZ):
        err = check_text(real_fn, rand_text(rng, alphabet))
        if err:
            print(err)
            return 1
        checked += 1

    # force the exact discriminating spelling through the fuzz path too
    err = check_text(real_fn, "None")
    if err:
        print(err)
        return 1
    checked += 1

    print("G-CONF OK: shadow impl == real repo helper on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_texts()), N_FUZZ + 1, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
