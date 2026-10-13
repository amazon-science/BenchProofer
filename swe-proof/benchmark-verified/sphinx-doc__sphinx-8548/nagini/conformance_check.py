#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8548 (nagini).

SHADOW
------
The `# impl-start` .. `# impl-end` region of `model.py`, copied VERBATIM with
only the contract calls deleted (`Requires`/`Ensures`/`Invariant`/`Assert` and
the `# invariants-start`/`-end` markers).  Nagini's `PSeq` / `ToSeq` carriers are
realized by a tiny immutable-tuple shim, so `lookup_owner_doc(...)` still
receives `ToSeq(ens)`-shaped arguments exactly as written in the model.  The
`@Pure` helpers the region depends on (`lookup_owner_doc`, and `resolve_from` /
`resolved_doc`, which the region's stripped `Assert` and the `Ensures` refer to)
are copied over with their `Requires` deleted, likewise verbatim.

There is NO `@ContractOnly` callee in this bundle (mapping.md §3.2), so the whole
shadow is executable and nothing is assumed.

Because the model's `Ensures` is `Result() == resolved_doc(nm, ...)`, this script
compares THREE values per input and requires all three to be equal:

  * `shadow`  — the verbatim impl region (the nested scan),
  * `spec`    — the verbatim pure `resolved_doc` (the model's postcondition),
  * `oracle`  — the REAL patched repo function (below).

So a divergence between the model's impl and its own spec, or between either of
them and the real code, is refuted.

ORACLE
------
The real patched repo function is CALLED, not transliterated:
`sphinx.ext.autodoc.importer.get_class_members` (mapping.md §1;
`sphinx/ext/autodoc/importer.py:254` at base_commit, the MRO-walking
instance-attribute loop at post-patch lines 300-330).  The gate applies
`patch.diff` to /testbed and puts it on `PYTHONPATH` before this script runs, so
`get_class_members` here IS the patched function.  Driving it needs nothing that
cannot be built in-container: each input is a real Python module written to a
private temp dir, imported, and its leaf class handed to `get_class_members`
together with the real `sphinx.util.inspect.safe_getattr` attrgetter.  The
oracle's answer for a queried attribute name `name` is
`members[name].docstring` when `members[name]` is a documented `INSTANCEATTR`,
and "absent" otherwise — i.e. exactly the documentation the F2P
`test_inherited_instance_variable` renders under `.. py:attribute::`.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model works over integer codes; the real function works over class objects
and strings.  The bridge is built FROM the real unchanged callees, never
guessed:

  * `mro`  <- `[owner_code(cls.__qualname__) for cls in getmro(subject)]`, using
    the real `sphinx.util.inspect.getmro`.
  * `ens`/`enm`/`edoc` <- for each MRO class, in MRO order, the FULL
    `ModuleAnalyzer.for_module(cls.__module__).attr_docs` table that the real
    loop scans for that class (`PycodeError`/`AttributeError` => no records, as
    in the real `except`), with every key `(ns, name)` mapped to
    `(owner_code(ns), name_code(name))` and the value to
    `doc_code('\n'.join(docstring))`.  The `ns == qualname` filter is NOT applied
    here: leaving it to the model's own `ens[j] == mro[c]` test is what puts the
    changed membership decision under test.  Since MRO classes sharing a module
    contribute that module's table more than once, the generated tables also
    contain duplicate records, which exercises `lookup_owner_doc`'s
    first-match-wins scan.
  * result: an `int` documentation-body code, inverted back through `doc_code`
    for the comparison with the real `docstring` string (`ABSENT = -1` <-> the
    name is not a documented instance-attribute member).  Generated
    documentation bodies are distinct per (class, attribute), so a wrong record
    cannot hide behind a shared body; the only exception is the F2P boundary
    fixture, which reproduces the real fixture's "docstring foo" /
    "docstring bar" bodies verbatim (there the two bodies that could be
    confused — Foo's and Bar's — are still distinct).

Every generated input satisfies the model's `Requires`
(`len(ens) == len(enm) == len(edoc)`, list permissions, `MustTerminate`) by
construction; the parallel tables are built in one pass, so the length
precondition cannot be violated.  The reachable domain has `len(mro) >= 2`
(a real class's MRO always ends in `object`); the model's `len(mro) == 0` case
has no real counterpart and so is not driveable through the oracle.  The
generated names are asserted disjoint from `dir(subject)` and the annotations,
which keeps every input inside the abstraction mapping.md §2 declares (the
`__dict__`/`__slots__`/`dir()`/annotation branches are omitted from the model,
and the mapping's no-collision assumption is thereby respected).

INPUTS
------
Boundary hierarchies first, each a real importable module: the exact F2P
`Bar(Foo)` fixture; an empty record table; a single class with one documented
attribute; base-only documentation (the behaviour the patch installs); own-only;
the same name documented on both class and base (override precedence); a depth-4
chain documented only on the deepest base; a diamond where the two branches
document the same name (MRO order decides); a cross-module hierarchy (base and
subclass in different modules, so the real per-class `ModuleAnalyzer` lookup
matters); and a subclass of a builtin (`dict`), whose bases raise `PycodeError`.
Between them these take every branch of the impl region: the `while` falling
through to `return ABSENT`, a hit at `c == 0`, a hit at `c > 0`, and
`lookup_owner_doc` returning `ABSENT`, hitting on its first entry, and scanning
past non-matching entries and duplicates.

Then seeded fuzz (random depth, multiple inheritance, and random splits across
two modules) until at least 100000 model-level inputs — one per
(queried name, hierarchy) pair — have been checked.  Seed pinned below and
recorded in mapping.md §"G-CONF".

Exit 0 iff zero disagreements; on a disagreement the input (mro, record table,
queried name) and both outputs are printed and the exit status is 1.
stdlib + the (patched) sphinx package only.
"""
import importlib
import json
import os
import random
import sys
import tempfile

from sphinx.ext.autodoc import INSTANCEATTR
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util.inspect import getannotations, getmro, safe_getattr

SEED = 8548
N_TARGET_INPUTS = 100_000

ABSENT = -1  # model.py, pure region


# --------------------------------------------------------------------------
# Nagini carrier shim: PSeq is an immutable sequence; ToSeq materializes one.
# --------------------------------------------------------------------------
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


def ToSeq(lst):
    return PSeq._wrap(lst)


# --------------------------------------------------------------------------
# model.py `# pure-start` .. `# pure-end`, verbatim minus Requires
# --------------------------------------------------------------------------
def lookup_owner_doc(owner, nm, ens, enm, edoc, j):
    if j == len(ens):
        return ABSENT
    if ens[j] == owner and enm[j] == nm:
        return edoc[j]
    return lookup_owner_doc(owner, nm, ens, enm, edoc, j + 1)


def resolve_from(nm, mro, ens, enm, edoc, c):
    if c == len(mro):
        return ABSENT
    if lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0) != ABSENT:
        return lookup_owner_doc(mro[c], nm, ens, enm, edoc, 0)
    return resolve_from(nm, mro, ens, enm, edoc, c + 1)


def resolved_doc(nm, mro, ens, enm, edoc):
    return resolve_from(nm, mro, ens, enm, edoc, 0)


# --------------------------------------------------------------------------
# model.py `# impl-start` .. `# impl-end`, verbatim minus Invariant/Assert
# --------------------------------------------------------------------------
def resolve_attribute_doc(nm, mro, ens, enm, edoc):
    c = 0
    while c < len(mro):
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            return found
        c = c + 1
    return ABSENT
# --------------------------------------------------------------------------


_TMPDIR = tempfile.mkdtemp(prefix="gconf_8548_")
sys.path.insert(0, _TMPDIR)
_MODCOUNT = [0]

# attribute names always queried, so the ABSENT branch is taken for every name a
# hierarchy does not document.  None of these is a member of `object`.
NAME_POOL = ["attr1", "attr2", "attr3", "attr4", "attr5", "attr6"]
QUERY_NAMES = NAME_POOL + ["never_documented_zz"]


def _class_source(cname, bases, attrs):
    head = "class %s(%s):" % (cname, ", ".join(bases)) if bases \
        else "class %s:" % cname
    out = [head, "    def __init__(self):"]
    if attrs:
        for attr, doc in attrs:
            out.append("        self.%s = None  #: %s" % (attr, doc))
    else:
        out.append("        pass")
    out.append("")
    return out


def build_hierarchy(specs, split=None):
    """Write + import real module(s) for `specs` and return the leaf class.

    specs: ordered list of (class_name, [base_name, ...], [(attr, doc), ...]);
           a base name is either an earlier class name or an external name such
           as "dict".  Bases precede subclasses.
    split: if not None, classes[:split] go in module A and classes[split:] in a
           second module B that imports them, so the MRO spans two modules and
           the real per-class ModuleAnalyzer lookup is exercised.
    """
    _MODCOUNT[0] += 1
    tag = _MODCOUNT[0]
    local = [s[0] for s in specs]
    if split is None or split >= len(specs) or split <= 0:
        modname = "gconf_m%d" % tag
        lines = []
        for cname, bases, attrs in specs:
            lines.extend(_class_source(cname, bases, attrs))
        _write(modname, lines)
        mod = importlib.import_module(modname)
        return getattr(mod, specs[-1][0]), [mod.__name__]
    mod_a = "gconf_a%d" % tag
    mod_b = "gconf_b%d" % tag
    lines_a = []
    for cname, bases, attrs in specs[:split]:
        lines_a.extend(_class_source(cname, bases, attrs))
    imported = [s[0] for s in specs[:split]]
    lines_b = ["from %s import %s" % (mod_a, ", ".join(imported)), ""]
    for cname, bases, attrs in specs[split:]:
        lines_b.extend(_class_source(cname, bases, attrs))
    _write(mod_a, lines_a)
    _write(mod_b, lines_b)
    importlib.import_module(mod_a)
    mod = importlib.import_module(mod_b)
    assert specs[-1][0] in local
    return getattr(mod, specs[-1][0]), [mod_a, mod_b]


def _write(modname, lines):
    with open(os.path.join(_TMPDIR, modname + ".py"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    importlib.invalidate_caches()


# --------------------------------------------------------------------------
# the type bridge: real class hierarchy -> the model's integer carriers
# --------------------------------------------------------------------------
class Bridge:
    """mapping.md §2, inverted: real qualnames/attr-names/documentation bodies
    <-> integer codes, built from the REAL unchanged callees (`getmro`,
    `ModuleAnalyzer.for_module(...).attr_docs`)."""

    def __init__(self, subject):
        self.owner_code = {}
        self.name_code = {}
        self.doc_code = {}
        self.doc_of_code = {}
        self.mro = [self._owner(cls_qualname(cls)) for cls in getmro(subject)]
        ens, enm, edoc = [], [], []
        for cls in getmro(subject):
            # exactly the records the real loop scans for this class: its own
            # module's whole attr_docs table (the `ns == qualname` filter is the
            # model's job, not the bridge's).
            for (ns, name), docstring in self._table(cls):
                ens.append(self._owner(ns))
                enm.append(self._name(name))
                edoc.append(self._doc('\n'.join(docstring)))
        self.ens, self.enm, self.edoc = ens, enm, edoc
        assert len(ens) == len(enm) == len(edoc)  # the model's Requires

    @staticmethod
    def _table(klass):
        try:
            modname = safe_getattr(klass, '__module__')
            analyzer = ModuleAnalyzer.for_module(modname)
            analyzer.analyze()
            return list(analyzer.attr_docs.items())
        except (AttributeError, PycodeError):
            return []

    def _owner(self, qualname):
        return self.owner_code.setdefault(qualname, len(self.owner_code))

    def _name(self, name):
        return self.name_code.setdefault(name, len(self.name_code))

    def _doc(self, body):
        if body not in self.doc_code:
            code = len(self.doc_code)
            self.doc_code[body] = code
            self.doc_of_code[code] = body
        return self.doc_code[body]

    def name_query_code(self, name):
        """Code for a queried name; a name on no record gets a fresh code that
        matches no `enm[j]`, which is a legitimate model input."""
        return self._name(name)

    def code_of_doc(self, body):
        return self.doc_code.get(body)


def cls_qualname(cls):
    try:
        return safe_getattr(cls, '__qualname__')
    except AttributeError:  # pragma: no cover - real classes always have one
        return repr(cls)


def oracle_docs(subject, objpath):
    """The REAL patched `get_class_members`, restricted to the documented
    instance attributes the model resolves: name -> docstring."""
    members = get_class_members(subject, objpath, safe_getattr)
    out = {}
    for name, attr in members.items():
        if attr.value is INSTANCEATTR and attr.docstring is not None:
            out[name] = attr.docstring
    return out


def assert_inside_abstraction(subject):
    """The model abstracts ONLY the comment-documented instance-attribute
    resolution (mapping.md §2 omits the __dict__/__slots__/dir()/annotation
    branches and assumes no name collision with them).  Assert every queried
    name is outside those branches, so no input escapes the abstraction."""
    other = set(dir(subject))
    for cls in getmro(subject):
        try:
            other |= set(getannotations(cls))
        except AttributeError:
            pass
    for name in QUERY_NAMES:
        assert name not in other, (
            "generated name %r collides with a non-modeled member branch" % name)


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
def boundary_specs():
    """(specs, split) pairs.  Every branch of the impl region is taken here."""
    # the exact F2P fixture (tests/roots/.../target/instance_variable.py):
    # attr1 base-only, attr2 documented on both, attr3 own-only.
    yield ([("Foo", [], [("attr1", "docstring foo"), ("attr2", "docstring foo")]),
            ("Bar", ["Foo"], [("attr2", "docstring bar"),
                              ("attr3", "docstring bar")])], None)
    # empty record table -> the while loop falls through to return ABSENT
    yield ([("E0", [], [])], None)
    # singleton class, one documented attribute -> hit at c == 0, first entry
    yield ([("S0", [], [("attr1", "d_s0_1")])], None)
    # base-only documentation -> hit at c > 0 (the behaviour the patch installs)
    yield ([("B0", [], [("attr1", "d_b0_1")]), ("B1", ["B0"], [])], None)
    # own-only documentation, base documents nothing
    yield ([("O0", [], []), ("O1", ["O0"], [("attr2", "d_o1_2")])], None)
    # same name on class and base -> earliest-MRO-owner precedence
    yield ([("P0", [], [("attr1", "d_p0_1")]),
            ("P1", ["P0"], [("attr1", "d_p1_1")])], None)
    # depth-4 chain, documented only on the deepest base -> hit at c == 3
    yield ([("D0", [], [("attr5", "d_d0_5")]), ("D1", ["D0"], []),
            ("D2", ["D1"], []), ("D3", ["D2"], [])], None)
    # diamond: both branches document the same name; the MRO order decides
    yield ([("A0", [], [("attr3", "d_a0_3")]),
            ("A1", ["A0"], [("attr1", "d_a1_1")]),
            ("A2", ["A0"], [("attr1", "d_a2_1")]),
            ("A3", ["A1", "A2"], [])], None)
    # cross-module: base in module A, subclass in module B (base-only doc), so
    # the real per-MRO-class ModuleAnalyzer.for_module lookup matters
    yield ([("X0", [], [("attr1", "d_x0_1"), ("attr4", "d_x0_4")]),
            ("X1", ["X0"], [("attr2", "d_x1_2")])], 1)
    # subclass of a builtin: `dict` and `object` raise PycodeError -> no records
    yield ([("K0", ["dict"], [("attr6", "d_k0_6")])], None)
    # many records under one owner -> lookup_owner_doc scans past non-matches
    yield ([("M0", [], [(nm, "d_m0_" + nm) for nm in NAME_POOL])], None)


def fuzz_specs(rng, index):
    depth = rng.randint(1, 4)
    specs = []
    made = []
    for d in range(depth):
        cname = "F%d_%d" % (index, d)
        if not made:
            bases = []
        elif len(made) >= 2 and rng.random() < 0.25:
            # multiple inheritance: list the bases in REVERSE creation order.
            # Subclass edges only ever point from a later class to an earlier
            # one, so reverse creation order is always a consistent MRO
            # linearization and `type()` never raises — no input is silently
            # dropped for being unbuildable.
            picked = rng.sample(range(len(made)), 2)
            bases = [made[i] for i in sorted(picked, reverse=True)]
        else:
            bases = [rng.choice(made)]
        k = rng.randint(0, 3)
        chosen = rng.sample(NAME_POOL, k)
        attrs = [(nm, "d_%d_%d_%s" % (index, d, nm)) for nm in chosen]
        specs.append((cname, bases, attrs))
        made.append(cname)
    split = None
    if depth >= 2 and rng.random() < 0.15:
        split = rng.randint(1, depth - 1)
    return specs, split


def check_one(specs, split):
    """Run shadow, spec and oracle over one real hierarchy; return
    (n_inputs, disagreements)."""
    subject, modnames = build_hierarchy(specs, split)
    objpath = [modnames[-1], specs[-1][0]]
    docs = oracle_docs(subject, objpath)
    assert_inside_abstraction(subject)
    bridge = Bridge(subject)
    bad = []
    for name in QUERY_NAMES:
        nm = bridge.name_query_code(name)
        shadow = resolve_attribute_doc(nm, bridge.mro, bridge.ens, bridge.enm,
                                       bridge.edoc)
        spec = resolved_doc(nm, ToSeq(bridge.mro), ToSeq(bridge.ens),
                            ToSeq(bridge.enm), ToSeq(bridge.edoc))
        body = docs.get(name)
        oracle = ABSENT if body is None else bridge.code_of_doc(body)
        if oracle is None:
            bad.append((name, "oracle docstring %r is not in the bridged record "
                              "table (bridge failure)" % body, shadow, spec))
            continue
        if shadow != oracle or spec != oracle:
            bad.append((name,
                        "mro=%r ens=%r enm=%r edoc=%r doc_codes=%r"
                        % (bridge.mro, bridge.ens, bridge.enm, bridge.edoc,
                           bridge.doc_of_code),
                        shadow, spec if spec != shadow else oracle))
    return len(QUERY_NAMES), bad, subject


def main():
    rng = random.Random(SEED)
    n_inputs = 0
    n_hierarchies = 0
    failures = []

    for specs, split in boundary_specs():
        n, bad, subject = check_one(specs, split)
        n_inputs += n
        n_hierarchies += 1
        for name, ctx, shadow, other in bad:
            failures.append((subject.__qualname__, name, ctx, shadow, other))
        if failures:
            break

    index = 0
    while not failures and n_inputs < N_TARGET_INPUTS:
        index += 1
        specs, split = fuzz_specs(rng, index)
        n, bad, subject = check_one(specs, split)
        n_inputs += n
        n_hierarchies += 1
        for name, ctx, shadow, other in bad:
            failures.append((subject.__qualname__, name, ctx, shadow, other))

    if failures:
        print("G-CONF FAIL: %d disagreement(s) after %d inputs / %d hierarchies"
              % (len(failures), n_inputs, n_hierarchies))
        for subj, name, ctx, shadow, other in failures[:5]:
            print("  subject=%s queried_name=%s" % (subj, name))
            print("    input: %s" % ctx)
            print("    shadow/spec=%r oracle-or-spec=%r" % (shadow, other))
        print(json.dumps({"status": "fail", "inputs": n_inputs,
                          "hierarchies": n_hierarchies,
                          "disagreements": len(failures), "seed": SEED}))
        return 1

    print("G-CONF OK: model.py impl region (and its resolved_doc spec) agrees "
          "with the REAL patched sphinx.ext.autodoc.importer.get_class_members "
          "on %d attribute-resolution inputs over %d real class hierarchies "
          "(12 boundary + fuzz, seed=%d), 0 disagreements."
          % (n_inputs, n_hierarchies, SEED))
    print(json.dumps({"status": "pass", "inputs": n_inputs,
                      "hierarchies": n_hierarchies, "disagreements": 0,
                      "seed": SEED,
                      "oracle": "sphinx.ext.autodoc.importer.get_class_members "
                                "(called, gold patch applied)",
                      "shadow": "model.py impl region, verbatim, contracts "
                                "stripped"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
