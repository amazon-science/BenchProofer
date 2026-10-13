#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7166 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`eligible`/`finalDoc`/`resolvedDocs`) transliterated to Python,
              over the real member observations bridged via mapping.md §2
              (`inspect.isfunction` -> isCallable, `inspect.isdatadescriptor` ->
              isProperty, `is_public_member` -> isPublic, `val.__doc__` ->
              ownDoc, the MRO doc walk -> inheritedDoc). There are no A-tagged
              callees consumed in the impl, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `InheritDocstrings`
              metaclass (astropy.utils.misc) applied at base_commit. We build a
              real subclass through the metaclass and read each member's
              resulting `__doc__` from the class dict (the correctness oracle,
              G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import inspect
import random
import sys

SEED = 7166
N_FUZZ = 100_000


# --- the unchanged nested predicate (mapping.md §1: is_public_member) ---------
def is_public_member(key):
    return (
        (key.startswith('__') and key.endswith('__') and len(key) > 4) or
        not key.startswith('_'))


# --- the R/I shadow: eligible / finalDoc / resolvedDocs, transliterated -------
def shadow_eligible(is_callable, is_property, is_public, own_doc_is_none):
    return (is_callable or is_property) and is_public and own_doc_is_none


def shadow_final_doc(is_callable, is_property, is_public, own_doc, inherited_doc):
    if shadow_eligible(is_callable, is_property, is_public, own_doc is None):
        return inherited_doc
    return own_doc


def shadow_resolved_docs(observations):
    """resolvedDocs members: the per-member finalDoc list, in member order."""
    return [shadow_final_doc(*o) for o in observations]


# --- member factories: the member kinds appearing in a class body ------------
def make_function(doc):
    def f(self):
        pass
    f.__doc__ = doc
    return f


def make_property(doc):
    def g(self):
        return 0
    return property(g, doc=doc)


def make_other_descriptor(doc):
    class Desc:
        __doc__ = doc

        def __get__(self, obj, objtype=None):
            return 0

        def __set__(self, obj, value):
            pass
    return Desc()


def make_non_descriptor(doc):
    class Val:
        __doc__ = doc
    return Val()


KINDS = {
    "function": make_function,
    "property": make_property,
    "other_descriptor": make_other_descriptor,
    "non_descriptor": make_non_descriptor,
}
KIND_NAMES = list(KINDS)

KEY_POOL = ["wiggle", "bar", "baz", "__call__", "__len__", "__x__", "_private",
            "__weird", "PublicAttr", "value", "_", "x", "__contains__", "Z9"]
DOC_POOL = [None, "BASE DOC", "FOO", "BAR", "", "multi\nline"]


def load_metaclass():
    """The patched InheritDocstrings (harness applies patch.diff before this)."""
    from astropy.utils.misc import InheritDocstrings
    return InheritDocstrings


def gen_class_body(rng):
    """A random subclass body + matching base members. Returns
    (base_attrs, sub_specs) where sub_specs is a list of (key, kind, own_doc)
    and base_attrs maps key -> a base member object (or absent)."""
    n = rng.randint(1, 6)
    keys = rng.sample(KEY_POOL, k=min(n, len(KEY_POOL)))
    sub_specs = []
    base_attrs = {}
    for key in keys:
        kind = rng.choice(KIND_NAMES)
        own_doc = rng.choice(DOC_POOL)
        sub_specs.append((key, kind, own_doc))
        if rng.random() < 0.75:
            base_kind = rng.choice(KIND_NAMES)
            base_doc = rng.choice(DOC_POOL)
            base_attrs[key] = KINDS[base_kind](base_doc)
    return base_attrs, sub_specs


def run_case(InheritDocstrings, base_attrs, sub_specs):
    """Build Base (plain) + Subclass (through the metaclass), return per-member
    (shadow_doc, oracle_doc) pairs in member order."""
    Base = type("Base", (object,), dict(base_attrs))

    # subclass member objects; capture own_doc BEFORE the metaclass mutates them
    sub_dict = {}
    observations = []
    for key, kind, own_doc in sub_specs:
        val = KINDS[kind](own_doc)
        sub_dict[key] = val
        is_callable = inspect.isfunction(val)
        is_property = inspect.isdatadescriptor(val)
        is_public = bool(is_public_member(key))
        captured_own = val.__doc__
        # inheritedDoc: the unchanged MRO doc walk, mirroring the real loop
        inherited = None
        for base in Base.__mro__:  # == cls.__mro__[1:] for the subclass
            super_method = getattr(base, key, None)
            if super_method is not None:
                inherited = super_method.__doc__
                break
        observations.append(
            (is_callable, is_property, is_public, captured_own, inherited))

    shadow = shadow_resolved_docs(observations)

    # ORACLE: create the subclass through the REAL patched metaclass, which
    # mutates the member objects' __doc__ in place; read from the class dict.
    Subclass = InheritDocstrings("Subclass", (Base,), dict(sub_dict))
    oracle = [Subclass.__dict__[key].__doc__ for key, _, _ in sub_specs]
    return list(zip(shadow, oracle, (s[0] for s in sub_specs)))


def fixed_f2p_case(InheritDocstrings):
    """The exact FAIL_TO_PASS scenario (test_misc.py::test_inherit_docstrings):
    a property `bar` with docstring "BAR" in the base, redefined without a
    docstring in the subclass, must inherit "BAR"; plus a __call__ method."""
    base_attrs = {
        "__call__": make_function("FOO"),
        "bar": make_property("BAR"),
    }
    sub_specs = [("__call__", "function", None), ("bar", "property", None)]
    return run_case(InheritDocstrings, base_attrs, sub_specs)


def main():
    try:
        InheritDocstrings = load_metaclass()
    except Exception as e:  # pragma: no cover
        print("G-CONF ERROR: cannot import patched InheritDocstrings: %r" % e)
        return 2

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # boundary: the F2P scenario first
    for shadow_doc, oracle_doc, key in fixed_f2p_case(InheritDocstrings):
        count += 1
        if shadow_doc != oracle_doc:
            disagreements.append(("F2P:" + key, shadow_doc, oracle_doc))

    while count < N_FUZZ:
        base_attrs, sub_specs = gen_class_body(rng)
        try:
            pairs = run_case(InheritDocstrings, base_attrs, sub_specs)
        except Exception as e:
            disagreements.append((repr(sub_specs), "EXC", repr(e)))
            break
        for shadow_doc, oracle_doc, key in pairs:
            count += 1
            if shadow_doc != oracle_doc:
                disagreements.append((key, shadow_doc, oracle_doc))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d member observations:"
              % (len(disagreements), count))
        for key, sh, orc in disagreements[:5]:
            print("  member=%r shadow=%r oracle=%r" % (key, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of resolveMemberDocstrings (eligible/finalDoc) "
          "agrees with the patched InheritDocstrings metaclass on %d member "
          "observations (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
