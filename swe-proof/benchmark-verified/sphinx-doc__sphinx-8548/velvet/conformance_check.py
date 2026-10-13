#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8548 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the FULL observable output:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`collectStep`/`collected` over `candidates hierarchy`)
              transliterated to Python over the *real* repo types, via the
              mapping.md §2 bijection: each MRO class becomes a `ClassLevel`
              {owner, annots, attrs} read from the REAL unchanged callees
              (`getmro`, `getannotations`+`unmangle`, per-class
              `ModuleAnalyzer.attr_docs` selected by `ns == cls.__qualname__`),
              and `existing` is the member-name set the unchanged prefix of
              `get_class_members` has already filled.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `get_class_members`
              applied at base_commit (the harness applies the gold patch before
              this runs), restricted to the entries the rewritten MRO loop
              creates (`value is INSTANCEATTR`) and observed as the caller
              observes them: name -> (`class_` identity, `docstring`).
              `ClassDocumenter.get_object_members` filters the members-only
              listing on `m.class_ == self.object`
              (sphinx/ext/autodoc/__init__.py:1606) and renders `m.docstring`,
              so BOTH components are user-visible; comparing only the name set
              or only name->docstring would miss a patch that surfaces the right
              identifiers attributed to the wrong class.

The `hierarchy` fed to the shadow is itself read from the REAL unchanged callees,
so this isolates the R/I fold leg: shadow and oracle must agree as a
`name -> (owner, docstring)` map (autodoc renders members sorted, so order is
not observable). `existing` is derived from the oracle's own output (the
complement of the INSTANCEATTR entries) AND independently by transliterating the
unchanged prefix `importer.py:259-298`; the two are asserted equal on every
input, so the bridge cannot be tuned per case.

The generator deliberately exercises the constructs the collection interleaves:
class-level annotations (`x: int`, including private/mangled ones and the
`__annotations__`-inherited-by-getattr quirk), real class attributes and
`__slots__` (which populate `existing`), documented instance attributes
(`self.x = None  #: doc`), names shared between an annotation on one class and
an attr-doc on another (the case that decides whether a docstring survives),
single/multiple inheritance, and hierarchies split across two modules (so the
per-class `ModuleAnalyzer.for_module(cls.__module__)` lookup is live).

Runs in-container (the prebuilt SWE-Bench instance image, gold patch applied),
`sphinx` + stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import importlib
import os
import random
import sys
import tempfile

from sphinx.ext.autodoc import INSTANCEATTR
from sphinx.ext.autodoc.importer import get_class_members, unmangle
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.util.inspect import (getannotations, getmro, getslots, isenumclass,
                                 safe_getattr)

_attrgetter = safe_getattr

SEED = 8548
# Each input is a *real* class hierarchy that must be source-generated, imported
# and parsed by the real ModuleAnalyzer (the oracle needs live class objects for
# getmro/__dict__/__annotations__). That is far heavier than scalar fuzzing, so
# the input volume is a few thousand distinct real hierarchies rather than 10^5
# scalar draws; the honest count is logged (plan §4 "no silent caps"). Every draw
# is a distinct hierarchy exercising the per-class annotation/attr-doc
# interleaving and the first-wins attribution the spec pins.
N_HIERARCHIES = 20000

_TMPDIR = tempfile.mkdtemp(prefix="gconf_8548_")
sys.path.insert(0, _TMPDIR)
_MODCOUNT = [0]


# --- input generation: real modules with real classes ------------------------

def emit_class(cname, bases, annots, classattrs, slots, attrs):
    lines = []
    lines.append("class %s(%s):" % (cname, ", ".join(bases)) if bases
                 else "class %s:" % cname)
    body = []
    if slots is not None:
        body.append("__slots__ = (%s)" % "".join("%r, " % s for s in slots))
    for a in annots:
        body.append("%s: int" % a)
    for a in classattrs:
        body.append("%s = 1" % a)
    if attrs:
        body.append("def __init__(self):")
        for attr, doc in attrs:
            body.append("    self.%s = None  #: %s" % (attr, doc))
    if not body:
        body.append("pass")
    for b in body:
        lines.append("    " + b)
    lines.append("")
    return lines


def build_modules(specs, split):
    """specs: list of (class_name, [base_ref], annots, classattrs, slots_or_None,
    [(attr, doc)]), ordered so a base precedes its subclasses.  The first
    `split` classes are written into a SECOND real module that the first imports,
    so `ModuleAnalyzer.for_module(cls.__module__)` is exercised per class (the
    patched loop rebuilds the analyzer for each MRO class's own module, which is
    the only way a base class in another module can contribute at all).
    Returns {class_name: class object}."""
    _MODCOUNT[0] += 1
    n = _MODCOUNT[0]
    base_mod, main_mod = "gconf_base_%d" % n, "gconf_main_%d" % n
    src_base, src_main = [], []
    for idx, (cname, bases, annots, classattrs, slots, attrs) in enumerate(specs):
        in_base = idx < split
        refs = []
        for b in bases:
            b_idx = [i for i, sp in enumerate(specs) if sp[0] == b][0]
            refs.append(b if (b_idx < split) == in_base else "%s.%s" % (base_mod, b))
        (src_base if in_base else src_main).extend(
            emit_class(cname, refs, annots, classattrs, slots, attrs))
    if src_base:
        with open(os.path.join(_TMPDIR, base_mod + ".py"), "w") as fh:
            fh.write("\n".join(src_base) + "\n")
    head = ["import %s" % base_mod, ""] if src_base else []
    with open(os.path.join(_TMPDIR, main_mod + ".py"), "w") as fh:
        fh.write("\n".join(head + src_main) + "\n")
    importlib.invalidate_caches()
    mods = {}
    if src_base:
        mods[True] = importlib.import_module(base_mod)
    mods[False] = importlib.import_module(main_mod)
    return {sp[0]: getattr(mods[i < split], sp[0])
            for i, sp in enumerate(specs)}


# --- the abstraction functions (mapping.md §2/§3), on the REAL callees --------

def owner_key(cls):
    """mapping.md §2: the identity of a class as `ClassLevel.owner` /
    `Member.owner` — '<module>.<qualname>', injective on an MRO (the MRO has no
    repeats, asserted below)."""
    if cls is None:
        return "<none>"
    return "%s.%s" % (safe_getattr(cls, '__module__', '?'),
                      safe_getattr(cls, '__qualname__', '?'))


def real_hierarchy(subject):
    """mapping.md §2 `hierarchy : List ClassLevel`, read from the REAL unchanged
    callees: for each class of getmro(subject) (most-derived-first) its owner
    identity, its annotation names after `unmangle` (a None unmangle — a private
    name owned by another class — becomes '' so the Lean `annots.filter (≠ "")`
    models the `if name` guard at importer.py:306), and its own-namespace
    documented instance attributes (`ns == cls.__qualname__`) in analyzer order."""
    hierarchy = []
    for cls in getmro(subject):
        annots = []
        try:
            for name in getannotations(cls):
                u = unmangle(cls, name)
                annots.append(u if u else "")
        except AttributeError:
            annots = []
        attrs = []
        try:
            modname = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')
            analyzer = ModuleAnalyzer.for_module(modname)
            analyzer.analyze()
            for (ns, name), docstring in analyzer.attr_docs.items():
                if ns == qualname:
                    attrs.append((name, '\n'.join(docstring)))
        except (AttributeError, PycodeError):
            attrs = []
        hierarchy.append((owner_key(cls), annots, attrs))
    return hierarchy


def prefix_member_names(subject):
    """`existing : List String` computed INDEPENDENTLY of the oracle output, by
    transliterating the UNCHANGED prefix of get_class_members
    (importer.py:259-298 — byte-identical pre- and post-patch): the enum,
    __slots__ and dir() phases that fill `members` before the MRO loop the
    patch rewrote. Cross-checked against the oracle-derived set on every input."""
    obj_dict = _attrgetter(subject, '__dict__', {})
    members = set()
    if isenumclass(subject):
        for name in subject.__members__:
            members.add(name)
        superclass = subject.__mro__[1]
        for name in obj_dict:
            if name not in superclass.__dict__:
                try:
                    safe_getattr(subject, name)
                except AttributeError:
                    continue
                members.add(name)
    try:
        slots = getslots(subject)
        if slots:
            for name in slots:
                members.add(name)
    except (AttributeError, TypeError, ValueError):
        pass
    for name in dir(subject):
        try:
            _attrgetter(subject, name)
            unmangled = unmangle(subject, name)
            if unmangled and unmangled not in members:
                members.add(unmangled)
        except AttributeError:
            continue
    return members


# --- the R/I shadow: Solution.lean candidates/collected, transliterated ------

def level_candidates(level):
    """Solution.lean `levelCandidates`: this class's annotation-only names
    (no docstring) first, then its documented instance attributes, both
    attributed to this class."""
    owner, annots, attrs = level
    out = [(n, owner, None) for n in annots if n != ""]
    out += [(name, owner, doc) for name, doc in attrs]
    return out


def shadow_collect(hierarchy, existing):
    """Solution.lean `collected existing (candidates hierarchy)`: first-occurrence
    admission over the per-class candidate stream. Returned as the observable
    map name -> (owner, docstring)."""
    cands = []
    for level in hierarchy:
        cands.extend(level_candidates(level))
    out = {}
    seen = set(existing)
    for name, owner, doc in cands:
        if name in seen:
            continue
        seen.add(name)
        out[name] = (owner, doc)
    return out


# --- the oracle: patch.diff's behaviour (real patched get_class_members) ------

def oracle_collect(subject, objpath):
    """The patched get_class_members restricted to the entries its rewritten MRO
    loop creates (`value is INSTANCEATTR`), observed as the caller observes them:
    name -> (class_ identity, docstring)."""
    members = get_class_members(subject, objpath, _attrgetter)
    out = {}
    rest = set()
    for name, attr in members.items():
        if attr.value is INSTANCEATTR:
            out[name] = (owner_key(attr.class_), attr.docstring)
        else:
            rest.add(name)
    return out, rest


def fuzz_cases(n, rng):
    """Yields (specs, subject_name, split)."""
    pool = ["a", "b", "c", "d", "x", "y", "z", "attr1", "attr2", "attr3"]

    def case(specs, subject, split=0):
        return (specs, subject, split)

    # --- boundary: the F2P fixture (target/instance_variable.py verbatim) ----
    yield case([("Foo", [], [], [], None,
                 [("attr1", "docstring foo"), ("attr2", "docstring foo")]),
                ("Bar", ["Foo"], [], [], None,
                 [("attr2", "docstring bar"), ("attr3", "docstring bar")])], "Bar")
    # annotation on the BASE, attr-doc on the SUBJECT for the same name and
    # vice versa: the pair that decides whether a docstring survives, and the
    # exact pair a flat pre-fixed annotation set cannot distinguish.
    yield case([("Foo", [], ["x"], [], None, [("y", "doc foo y")]),
                ("Bar", ["Foo"], ["y"], [], None, [("x", "doc bar x")])], "Bar")
    yield case([("Foo", [], [], [], None, [("x", "doc foo x")]),
                ("Bar", ["Foo"], ["x"], [], None, [("x", "doc bar x")])], "Bar")
    yield case([("A", [], [], [], None, [])], "A")               # nothing at all
    yield case([("A", [], ["a"], [], None, [("a", "da")])], "A")  # one class, both phases
    yield case([("A", [], [], ["a"], None, [("a", "da")])], "A")  # class attr shadows
    yield case([("A", [], [], [], ("s1",), [("s1", "ds")])], "A")  # __slots__ shadows
    yield case([("A", [], ["__p"], [], None, [("__p", "dp")])], "A")  # mangled annotation
    yield case([("A", [], ["__p", "q"], [], None, []),           # mangled + inherited
                ("B", ["A"], [], [], None, [("q", "dq"), ("__p", "dp")])], "B")
    # cross-module base: Base lives in the OTHER module
    yield case([("Base", [], ["m"], [], None, [("n", "dn base")]),
                ("Sub", ["Base"], [], [], None,
                 [("m", "dm sub"), ("o", "do sub")])], "Sub", split=1)
    # multiple inheritance (C3 order decides which class owns the shared name)
    yield case([("L", [], [], [], None, [("l", "dl")]),
                ("R", [], ["l"], [], None, [("r", "dr")]),
                ("D", ["L", "R"], [], [], None, [("d", "dd")])], "D")
    yield case([("L", [], [], [], None, [("l", "dl")]),
                ("R", [], ["l"], [], None, [("r", "dr")]),
                ("D", ["L", "R"], [], [], None, [("d", "dd")])], "D", split=2)

    for _ in range(n):
        depth = rng.randint(1, 4)
        specs = []
        prev = []
        for d in range(depth):
            cname = "C%d" % d
            annots = rng.sample(pool, rng.randint(0, 3))
            if rng.random() < 0.15:
                annots = annots + ["__p"]
            classattrs = [nm for nm in rng.sample(pool, rng.randint(0, 2))
                          if nm not in annots]
            slots = None
            if rng.random() < 0.12:
                slots = tuple(nm for nm in rng.sample(pool, rng.randint(1, 2))
                              if nm not in classattrs) or None
            attrs = [(nm, "doc_%s_%d" % (nm, d))
                     for nm in rng.sample(pool, rng.randint(0, 4))]
            specs.append((cname, list(prev), annots, classattrs, slots, attrs))
            prev = [cname]
            if d + 1 < depth and rng.random() < 0.25:
                # a sibling base, so the next class inherits from two parents
                extra = "X%d" % d
                specs.append((extra, [], rng.sample(pool, rng.randint(0, 2)), [],
                              None, [(nm, "doc_%s_x%d" % (nm, d))
                                     for nm in rng.sample(pool, rng.randint(0, 2))]))
                prev = [cname, extra]
        yield (specs, specs[-1][0] if specs[-1][0].startswith("C") else prev[0],
               rng.randint(0, len(specs)) if rng.random() < 0.3 else 0)


def main():
    rng = random.Random(SEED)
    disagreements = []
    bridge_fails = []
    count = 0
    unbuildable = 0
    for specs, subject_name, split in fuzz_cases(N_HIERARCHIES, rng):
        try:
            classes = build_modules(specs, split)
        except Exception:  # a draw Python itself rejects (MRO/slots conflict)
            unbuildable += 1
            continue
        count += 1
        subject = classes[subject_name]
        objpath = [subject.__module__, subject.__qualname__]
        mro = getmro(subject)
        if len(set(mro)) != len(mro):
            bridge_fails.append(("mro-not-distinct", subject.__qualname__))
            continue
        if len({owner_key(c) for c in mro}) != len(mro):
            bridge_fails.append(("owner-key-not-injective", subject.__qualname__))
            continue
        hierarchy = real_hierarchy(subject)
        oracle, rest = oracle_collect(subject, objpath)
        existing = prefix_member_names(subject)
        if existing != rest:
            bridge_fails.append(("existing-mismatch", subject.__qualname__,
                                 sorted(existing ^ rest)))
            continue
        shadow = shadow_collect(hierarchy, existing)
        if shadow != oracle:
            disagreements.append((subject.__qualname__, shadow, oracle))
        if len(disagreements) + len(bridge_fails) >= 5:
            break
    if bridge_fails:
        print("G-CONF FAIL: %d abstraction-bridge violation(s) over %d inputs:"
              % (len(bridge_fails), count))
        for b in bridge_fails:
            print("  %r" % (b,))
        return 1
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nm, sh, orc in disagreements:
            only_sh = {k: v for k, v in sh.items() if orc.get(k) != v}
            only_or = {k: v for k, v in orc.items() if sh.get(k) != v}
            print("  subject=%s shadow-only=%r oracle-only=%r" % (nm, only_sh, only_or))
        return 1
    print("G-CONF OK: R/I shadow of collectInstanceAttrDocs (collected existing "
          "(candidates hierarchy)) agrees with patch.diff behaviour (real patched "
          "get_class_members, observed as name -> (class_ identity, docstring)) on "
          "%d real class hierarchies (seed=%d), 0 disagreements; `existing` "
          "cross-checked against the unchanged prefix on every input."
          % (count, SEED))
    print("(%d generated draws were rejected by Python itself -- MRO or "
          "__slots__/class-variable conflicts -- and never reached the "
          "comparison.)" % unbuildable)
    return 0


if __name__ == "__main__":
    sys.exit(main())
