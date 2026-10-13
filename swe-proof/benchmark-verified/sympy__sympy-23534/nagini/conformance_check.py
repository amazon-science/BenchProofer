#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23534 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. PSeq is realized as an
immutable tuple shim, ToSeq as a list->PSeq lift; the @Pure helpers
(DEFAULT_CLS / all_tag / all_nonneg) copy over as plain functions and are used
to sanity-check that generated inputs satisfy the Requires clauses. The proof
lemmas (all_tag_concat / nonneg_at) keep their call sites verbatim; their
bodies, with the contract calls stripped, are executable no-op recursions.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md — the
container branch of `sympy.core.symbol.symbols` (invoked by passing a tuple or
list of name entries). The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2):
  * a container of name strings  ->  List[int] of entry tokens, each token the
    entry's expansion multiplicity (the number of leaf objects that entry
    produces, a property of the entry string alone, independent of the
    requested class; realized by expanding the entry once via the real
    single-name path and counting leaves, cached per entry string);
  * the requested output class    ->  an integer class tag; the tag of the
    objects a class produces is the Python type of a directly constructed
    probe object (a metaclass like Function produces UndefinedFunction
    instances, so the probe construction is what pins the tag). The default
    class maps to tag 0 == DEFAULT_CLS();
  * the grouped result            ->  PSeq[PSeq[int]]: one group per entry, in
    order; group k holds the leaf class tags of entry k (nested per-entry
    structure flattened to leaves, per mapping.md).

Input domain: Requires demands a read-only container of non-negative
multiplicity tokens. Ordered containers (tuple/list) of well-formed name
entries — single names, ranges, and null ranges expanding to zero objects —
all satisfy it; unordered set containers fall outside the model's ordered
List[int] domain and are not generated.

>= 1e5 Requires-satisfying inputs: boundary containers + 100000 fuzz
containers. Pinned fuzz seed: 23534.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random).
"""
import json
import random
import sys

SEED = 23534
N_FUZZ = 100_000


# --- PSeq / ToSeq shims: the operations the impl+pure regions use ------------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

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

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def DEFAULT_CLS():
    return 0


def all_tag(xs, t):
    if len(xs) == 0:
        return True
    return xs[0] == t and all_tag(xs.drop(1), t)


def all_nonneg(xs):
    if len(xs) == 0:
        return True
    return xs[0] >= 0 and all_nonneg(xs.drop(1))


# --- proof lemmas, contract calls stripped (executable no-op recursions) ------

def all_tag_concat(a, b, t):
    if len(a) == 0:
        pass
    else:
        all_tag_concat(a.drop(1), b, t)


def nonneg_at(xs, i):
    if i == 0:
        pass
    else:
        nonneg_at(xs.drop(1), i - 1)


# --- impl regions of model.py, verbatim, contract calls stripped --------------

def expand_entry(cls, n):
    out = []  # type: list
    i = 0
    while i < n:
        old = ToSeq(out)
        out.append(cls)
        all_tag_concat(old, PSeq(cls), cls)
        i = i + 1
    return out


def symbols_on_sequence(names, cls):
    res = PSeq()  # type: PSeq
    i = 0
    while i < len(names):
        nonneg_at(ToSeq(names), i)
        sub = expand_entry(cls, names[i])
        grp = ToSeq(sub)  # type: PSeq
        old = res
        res = res + PSeq(grp)
        i = i + 1
    return res
    # (loop invariants / Assert proof steps stripped)


# --- bridge: real name containers / produced objects <-> the abstract types ---

def _leaves(obj):
    """Flatten a (possibly nested) tuple/list of produced objects to its leaf
    objects (a single-name entry's expansion is a scalar: one leaf)."""
    if isinstance(obj, (tuple, list)):
        out = []
        for x in obj:
            out.extend(_leaves(x))
        return out
    return [obj]


_MULT_CACHE = {}


def multiplicity_of(symbols_fn, entry):
    """The entry token of mapping.md: the number of leaf objects the entry
    expands to — a property of the entry string, computed once via the real
    single-name path (seq=True keeps zero-expansion entries observable)."""
    if entry not in _MULT_CACHE:
        _MULT_CACHE[entry] = len(_leaves(symbols_fn(entry, seq=True)))
    return _MULT_CACHE[entry]


def check_container(symbols_fn, names, cls, cls_tag, type_to_tag):
    """Run shadow and oracle on one (container, class) input; return an error
    string on disagreement, else None."""
    # bridge the input: entry string -> multiplicity token; class -> tag
    names_abs = [multiplicity_of(symbols_fn, e) for e in names]
    assert all_nonneg(ToSeq(names_abs))  # Requires holds

    shadow = symbols_on_sequence(names_abs, cls_tag)
    shadow_groups = [[shadow[k][j] for j in range(len(shadow[k]))]
                     for k in range(len(shadow))]

    real = symbols_fn(names, cls=cls)
    real_groups = []
    for k in range(len(real)):
        group = []
        for obj in _leaves(real[k]):
            group.append(type_to_tag.get(type(obj), -1))  # -1: unexpected class
        real_groups.append(group)

    if shadow_groups != real_groups:
        return ("DISAGREEMENT\n  names=%r cls=%r (tag %d)\n"
                "  abstract input names_abs=%r\n"
                "  shadow=%r\n  real(abstracted)=%r\n  real(raw)=%r"
                % (names, cls, cls_tag, names_abs, shadow_groups,
                   real_groups, real))
    return None


def main():
    # REAL patched callees, imported from the mounted repo (PYTHONPATH=/testbed)
    from sympy import symbols, Function
    from sympy.core.symbol import Symbol, Dummy, Wild

    classes = [Symbol, Function, Dummy, Wild]
    # class tag realization: the type of a probe object each class produces;
    # the default class gets tag 0 == DEFAULT_CLS()
    type_to_tag = {}
    cls_tag = {}
    for t, c in enumerate(classes):
        produced = type(c("probe"))
        cls_tag[c] = t
        type_to_tag[produced] = t
    assert cls_tag[Symbol] == DEFAULT_CLS()

    boundary_containers = [
        ("x",),
        ("x", "y"),
        ("q:2", "u:2"),
        ("a:d", "x:z"),
        ("x5:10", "y:5"),
        ["p", "q", "r"],          # list container
        ("f", "g", "h"),
        ("x:c", "y"),             # zero-expansion entry then a single name
        ("q:2", "x:0"),           # range entry then a zero-expansion entry
        ("x:0", "x1:1", "x:c"),   # all zero-expansion -> all empty groups
        ("x(:2)",),               # nested per-entry structure (flattened)
        ("x:2(1:3)", "y"),
        ("a,b", "c"),             # comma entry expanding to several leaves
    ]

    checked = 0
    for names in boundary_containers:
        for c in classes:
            err = check_container(symbols, names, c, cls_tag[c], type_to_tag)
            if err:
                print(err)
                return 1
            checked += 1

    # fuzz: random ordered containers of single names / ranges / zero-expansion
    # entries under a random requested class. Pinned seed 23534.
    rng = random.Random(SEED)
    bases = ["a", "b", "c", "x", "y", "z", "f", "g", "p", "q"]
    suffixes = ["", "", ":0", ":1", ":2", ":3", ":5", ":c", "5:10", ":z",
                "(:2)", ":2(1:3)"]
    for _ in range(N_FUZZ):
        n = rng.randint(1, 4)
        names = tuple(rng.choice(bases) + rng.choice(suffixes)
                      for _ in range(n))
        if rng.random() < 0.1:
            names = list(names)
        c = rng.choice(classes)
        err = check_container(symbols, names, c, cls_tag[c], type_to_tag)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real container-branch behaviour on %d "
          "inputs (%d boundary + %d fuzz containers, %d classes, seed %d)."
          % (checked, len(boundary_containers) * len(classes), N_FUZZ,
             len(classes), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
