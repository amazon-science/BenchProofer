#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8551.

The prefer-specific name resolver is modelled DEEPLY in model.py (the pure
functions `resolve_count` / `resolve_name` / `has_ctx_candidate`, the
suffix/membership cascade), NOT behind a consumed @ContractOnly axiom.  G-AX
therefore validates that deep model against the REAL resolver:

    sphinx.domains.python.PythonDomain.find_obj(env, modname, classname, name,
                                                type, searchmode=1)

`find_obj` in prefer-specific mode (searchmode == 1) is exactly the cascade

    modname.classname.name  >  modname.name  >  name  >  suffix-fallback

modelled by `resolve_*`.  This script constructs a REAL `PythonDomain`
(populating only the attributes `find_obj` reads — `objects`, `object_types`,
`objtypes_for_role`), runs the unmodified `find_obj`, and asserts that for every
input:

  * the NUMBER of matches equals model.py's `resolve_count`, and
  * whenever the model resolves to a single contextual object, the real
    resolver returns exactly that one qualified name (`resolve_name`).

Boundary cases mirror the issue scenario (the same simple class name registered
under several sub-modules, looked up with/without module and class context),
plus randomized fuzzing over multi-segment namespaces.

Imports the REAL sphinx under test (the module the gold patch's resolution path
runs through); nothing is stubbed except the env handle `find_obj` ignores in
searchmode 1.  Exit 0 iff every observation matches the deep model.
"""
import itertools
import random
import sys

from sphinx.domains.python import PythonDomain, ObjectEntry


# --- model.py deep-model reference (kept in lock-step with the pure region) --
# Names are tuples of segment tokens (model.py: PSeq[int]); a dotted name is the
# concatenation of its segments.  Context is a tuple or None (model.py:
# Optional[PSeq[int]]).

def _suffix_eq(obj, name):
    return len(name) <= len(obj) and obj[len(obj) - len(name):] == name


def _member(objs, q):
    return any(o == q for o in objs)


def _count_suffix(objs, name):
    return sum(1 for o in objs if _suffix_eq(o, name))


def _has_ctx_candidate(mod, cls, name, objs):
    if mod is not None and cls is not None and _member(objs, mod + cls + name):
        return True
    if mod is not None and _member(objs, mod + name):
        return True
    return _member(objs, name)


def resolve_count(mod, cls, name, objs):
    if _has_ctx_candidate(mod, cls, name, objs):
        return 1
    return _count_suffix(objs, name)


def _first_suffix(objs, name):
    for o in objs:
        if _suffix_eq(o, name):
            return o
    return name


def resolve_name(mod, cls, name, objs):
    if mod is not None and cls is not None and _member(objs, mod + cls + name):
        return mod + cls + name
    if mod is not None and _member(objs, mod + name):
        return mod + name
    if _member(objs, name):
        return name
    return _first_suffix(objs, name)


# --- real-callee harness ------------------------------------------------------

def _dotted(segs):
    return ".".join(segs)


def make_domain(object_fullnames):
    """A REAL PythonDomain populated with just what find_obj reads."""
    dom = object.__new__(PythonDomain)
    dom.data = {"objects": {fn: ObjectEntry("index", fn, "class")
                            for fn in object_fullnames}}
    role2type = {}
    for name, ot in PythonDomain.object_types.items():
        for role in ot.roles:
            role2type.setdefault(role, []).append(name)
    dom._role2type = role2type
    dom.objtypes_for_role = role2type.get
    return dom


def check_case(dom, objs_tuples, mod, cls, name):
    """Assert real find_obj(searchmode=1) agrees with the deep model."""
    modname = _dotted(mod) if mod is not None else None
    clsname = _dotted(cls) if cls is not None else None
    target = _dotted(name)

    matches = dom.find_obj(None, modname, clsname, target, "class", 1)
    observed_names = sorted(n for n, _ in matches)

    exp_count = resolve_count(mod, cls, name, objs_tuples)
    assert len(observed_names) == exp_count, (
        "resolve_count unsound: mod=%r cls=%r name=%r objs=%r -> real %d (%r), "
        "model %d" % (modname, clsname, target,
                      [_dotted(o) for o in objs_tuples],
                      len(observed_names), observed_names, exp_count))

    if exp_count == 1:
        exp_name = _dotted(resolve_name(mod, cls, name, objs_tuples))
        assert observed_names == [exp_name], (
            "resolve_name unsound: mod=%r cls=%r name=%r objs=%r -> real %r, "
            "model %r" % (modname, clsname, target,
                          [_dotted(o) for o in objs_tuples],
                          observed_names, exp_name))


def main():
    # --- boundary cases: the issue scenario ----------------------------------
    issue_objs = [("mod", "A"), ("mod", "submod", "A")]
    dom = make_domain([_dotted(o) for o in issue_objs])
    boundary = [
        (("mod", "submod"), None, ("A",)),   # fix: -> mod.submod.A (unique)
        (("mod",), None, ("A",)),            # -> mod.A (unique)
        (None, None, ("A",)),                # bug: -> {mod.A, mod.submod.A}
        (("mod", "submod"), None, ("mod", "A")),       # qualified target
        (("mod", "submod"), None, ("mod", "submod", "A")),
        (("mod", "submod"), ("C",), ("A",)), # class ctx, no C.A obj
        (("other",), None, ("A",)),          # unknown module ctx -> fuzzy
        (None, None, ("B",)),                # absent name -> 0 matches
        (("mod",), None, ("B",)),
    ]
    for mod, cls, name in boundary:
        check_case(dom, issue_objs, mod, cls, name)

    # --- randomized fuzz over multi-segment namespaces -----------------------
    rng = random.Random(8551)
    segs = ["mod", "submod", "pkg", "sub", "A", "B", "C", "x", "y"]
    for _ in range(20000):
        n_objs = rng.randint(1, 5)
        objs_tuples = []
        for _ in range(n_objs):
            depth = rng.randint(1, 4)
            objs_tuples.append(tuple(rng.choice(segs) for _ in range(depth)))
        # dedupe while preserving content
        objs_tuples = list(dict.fromkeys(objs_tuples))
        dom = make_domain([_dotted(o) for o in objs_tuples])

        mod = None if rng.random() < 0.3 else tuple(
            rng.choice(segs) for _ in range(rng.randint(1, 2)))
        cls = None if rng.random() < 0.6 else (rng.choice(segs),)
        name = tuple(rng.choice(segs) for _ in range(rng.randint(1, 3)))
        check_case(dom, objs_tuples, mod, cls, name)

    # --- small exhaustive sweep ----------------------------------------------
    universe = [("mod", "A"), ("mod", "submod", "A"), ("mod", "B"),
                ("pkg", "A"), ("A",)]
    for k in range(1, 4):
        for combo in itertools.combinations(universe, k):
            dom = make_domain([_dotted(o) for o in combo])
            ctxs = [None, ("mod",), ("mod", "submod"), ("pkg",)]
            clss = [None, ("A",), ("B",)]
            names = [("A",), ("B",), ("mod", "A")]
            for mod in ctxs:
                for cls in clss:
                    for name in names:
                        check_case(dom, list(combo), mod, cls, name)

    print("G-AX OK: deep model resolve_count/resolve_name == real "
          "PythonDomain.find_obj(searchmode=1) on %d boundary + 20000 fuzz + "
          "exhaustive-subset cases" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
