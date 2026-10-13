#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7166.

Validates the ONE kind-A claim of this bundle — the A-reference that the deep
model `eligible`/`finalDoc` (Solution.lean `pure` region) equals the post-patch
membership guard of `InheritDocstrings.__init__` over REAL member objects.

The post-patch guard is, verbatim:

    ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and
            is_public_member(key) and
            val.__doc__ is None)

i.e. `(isCallable or isProperty) and isPublic and ownDoc is None` = `eligible`.
The single behavioral change is the `or inspect.isdatadescriptor(val)` disjunct:
a property (a data descriptor) now qualifies.

This check runs the REAL callees:
  * `inspect.isfunction`        -> Member.isCallable
  * `inspect.isdatadescriptor`  -> Member.isProperty   (the A-reference)
  * `is_public_member`          -> Member.isPublic     (verbatim, unchanged)
  * `val.__doc__ is None`       -> Member.ownDoc.isNone
and the REAL metaclass-style MRO documentation walk -> Member.inheritedDoc,
over a matrix of member kinds, visibilities, and own-doc states plus randomized
fuzzing, asserting the deep model reproduces the guard's outcome AND the
member's resulting `__doc__` in every case.

There is no consumed axiom in this bundle; only the A-reference is checked.
Imports only the Python standard library (`inspect`, `random`). Exit 0 iff sound.
"""
import inspect
import random
import sys


# --- the unchanged nested predicate, lifted verbatim from the metaclass ------
# (InheritDocstrings.__init__.is_public_member, astropy/utils/misc.py:524-528;
#  unchanged by the patch, so it is part of the trusted boundary G-AX runs.)
def is_public_member(key):
    return (
        (key.startswith('__') and key.endswith('__') and len(key) > 4) or
        not key.startswith('_'))


# --- the deep model, transliterated from Solution.lean (kept in lock-step) ---
def model_eligible(is_callable, is_property, is_public, own_doc_is_none):
    """eligible (m : Member) = (isCallable || isProperty) && isPublic && ownDoc.isNone"""
    return (is_callable or is_property) and is_public and own_doc_is_none


def model_final_doc(is_callable, is_property, is_public, own_doc, inherited_doc):
    """finalDoc m = if eligible m then m.inheritedDoc else m.ownDoc"""
    if model_eligible(is_callable, is_property, is_public, own_doc is None):
        return inherited_doc
    return own_doc


# --- the REAL post-patch guard outcome, computed from real objects -----------
def real_guard_outcome(key, val, mro_after_self):
    """Replicate the post-patch InheritDocstrings.__init__ body for one member.

    Returns (qualified, resulting_doc): `qualified` is the real value of the
    post-patch `if` guard; `resulting_doc` is the member's `__doc__` after the
    loop body runs (the inherited doc if qualified, else its own)."""
    qualified = (
        (inspect.isfunction(val) or inspect.isdatadescriptor(val)) and
        is_public_member(key) and
        val.__doc__ is None)
    if qualified:
        for base in mro_after_self:
            super_method = getattr(base, key, None)
            if super_method is not None:
                return True, super_method.__doc__
        # guard held but no base supplied the member: __doc__ stays None
        return True, val.__doc__
    return False, val.__doc__


# --- value carriers (mapping.md §2) for the model side -----------------------
def observe(key, val, mro_after_self):
    """Bridge a real (key, val) member to the Member fields the model reads."""
    is_callable = inspect.isfunction(val)
    is_property = inspect.isdatadescriptor(val)
    is_public = bool(is_public_member(key))
    own_doc = val.__doc__
    inherited_doc = None
    for base in mro_after_self:
        super_method = getattr(base, key, None)
        if super_method is not None:
            inherited_doc = super_method.__doc__
            break
    return is_callable, is_property, is_public, own_doc, inherited_doc


# --- member factories: the kinds of objects appearing in a class dict --------
def make_plain_function(doc):
    def f(self):
        pass
    f.__doc__ = doc
    return f


def make_property(doc):
    def g(self):
        return 0
    return property(g, doc=doc)


def make_other_descriptor(doc):
    # a non-property data descriptor (defines __get__ and __set__)
    class Desc:
        __doc__ = doc

        def __get__(self, obj, objtype=None):
            return 0

        def __set__(self, obj, value):
            pass
    return Desc()


def make_non_descriptor(doc):
    # a plain value: not a function, not a data descriptor
    class Val:
        __doc__ = doc
    return Val()


KINDS = {
    "function": make_plain_function,
    "property": make_property,
    "other_descriptor": make_other_descriptor,
    "non_descriptor": make_non_descriptor,
}

KEYS = ["wiggle", "bar", "__call__", "__len__", "_private", "__weird",
        "PublicAttr", "x", "_", "__x__"]

DOCS = [None, "BASE DOC", "", "multi\nline\ndoc"]


def build_base_with(key, kind_name, base_doc):
    """A base class exposing `key` with the given kind and docstring, so the MRO
    walk has something to resolve to (or not, when base_doc-bearing member is
    absent)."""
    member = KINDS[kind_name](base_doc)
    return type("Base", (object,), {key: member})


def check_case(key, kind_name, own_doc, base_present, base_kind, base_doc):
    """One member-shaped case: build the member + (optionally) a base, observe
    it, and assert the model reproduces the real guard outcome and resulting
    doc."""
    val = KINDS[kind_name](own_doc)
    if base_present:
        base = build_base_with(key, base_kind, base_doc)
        mro_after_self = base.__mro__  # bases of a subclass, in MRO order
    else:
        mro_after_self = (object,)

    obs = observe(key, val, mro_after_self)
    is_callable, is_property, is_public, obs_own_doc, inherited_doc = obs

    model_doc = model_final_doc(is_callable, is_property, is_public,
                                obs_own_doc, inherited_doc)
    real_qualified, real_doc = real_guard_outcome(key, val, mro_after_self)

    model_qualified = model_eligible(is_callable, is_property, is_public,
                                     obs_own_doc is None)

    assert model_qualified == real_qualified, (
        "eligible deep model unsound: key=%r kind=%r own_doc=%r -> model "
        "qualified=%r but real guard=%r" %
        (key, kind_name, own_doc, model_qualified, real_qualified))
    assert model_doc == real_doc, (
        "finalDoc deep model unsound: key=%r kind=%r own_doc=%r base=(%r,%r,%r) "
        "-> model doc=%r but real doc=%r" %
        (key, kind_name, own_doc, base_present, base_kind, base_doc,
         model_doc, real_doc))


def main():
    # --- direct A-reference invariants: the property/datadescriptor facts ----
    assert inspect.isdatadescriptor(make_property("d")) is True, \
        "a property must be a data descriptor"
    assert inspect.isfunction(make_property("d")) is False, \
        "a property must not be an inspect.isfunction"
    assert inspect.isfunction(make_plain_function("d")) is True
    assert inspect.isdatadescriptor(make_plain_function("d")) is False, \
        "a plain function is not a data descriptor"
    assert inspect.isdatadescriptor(make_other_descriptor("d")) is True
    assert inspect.isfunction(make_other_descriptor("d")) is False
    assert inspect.isdatadescriptor(make_non_descriptor("d")) is False
    assert inspect.isfunction(make_non_descriptor("d")) is False

    # --- full boundary matrix ------------------------------------------------
    count = 0
    for key in KEYS:
        for kind in KINDS:
            for own_doc in DOCS:
                for base_present in (False, True):
                    for base_kind in KINDS:
                        for base_doc in DOCS:
                            check_case(key, kind, own_doc, base_present,
                                       base_kind, base_doc)
                            count += 1

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(7166)
    fuzz_keys = KEYS + ["a", "_a", "__a", "a__", "__init__", "value_x",
                        "__contains__", "Z9", "_x_y_", "____"]
    for _ in range(20000):
        key = rng.choice(fuzz_keys)
        kind = rng.choice(list(KINDS))
        own_doc = rng.choice(DOCS + ["fuzz-%d" % rng.randint(0, 9)])
        base_present = rng.random() < 0.7
        base_kind = rng.choice(list(KINDS))
        base_doc = rng.choice(DOCS + ["fuzz-base-%d" % rng.randint(0, 9)])
        check_case(key, kind, own_doc, base_present, base_kind, base_doc)
        count += 1

    print("G-AX OK: eligible/finalDoc deep model (== post-patch "
          "InheritDocstrings guard) sound on %d member cases "
          "(boundary matrix + 20000 fuzz); property is a data descriptor and "
          "not a function, confirmed on real objects." % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
