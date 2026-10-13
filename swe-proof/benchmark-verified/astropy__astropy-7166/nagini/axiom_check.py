#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7166.

The model carries, on each member, the boolean RESULTS of two unchanged
standard-introspection callees:

    is_callable_member   <-  inspect.isfunction(val)
    is_computed_attribute <- inspect.isdatadescriptor(val)

These are type refinements of the real callees (refinement.md tags R /
A-reference). This script validates that the model's abstraction is FAITHFUL to
the real `inspect` predicates: it executes the REAL `inspect.isfunction` and
`inspect.isdatadescriptor` on representative member objects and asserts the
classification the model relies on, in particular the discriminating fact:

    a computed-attribute member (a `property`, the descriptor-protocol member
    pinned by the F2P test) is NOT reported as a function but IS reported as a
    data descriptor  ->  is_callable_member == False, is_computed_attribute == True

while an ordinary callable member is reported as a function:

    is_callable_member == True

It then independently re-derives the WHOLE pinned behaviour by running the real
docstring-inheritance decision (the patched loop body) against the real
introspection callees, for both member kinds, and asserts it matches the model's
`fills_docstring` eligibility + assignment semantics.

Imports nothing repo-specific: `inspect` is the Python standard library — the
same module the gold patch calls. Exit 0 iff every obligation holds.
"""
import inspect
import sys


# --- model.py reference: the eligibility predicate (kept in lock-step) -------

def fills_docstring(is_callable_member, is_computed_attribute,
                    is_public, has_own_doc):
    return ((is_callable_member or is_computed_attribute)
            and is_public and not has_own_doc)


# --- representative members, exactly as they appear in a class __dict__ ------

def sample_members():
    """Return (label, member_object, expected_is_function,
    expected_is_datadescriptor) for the member kinds the behaviour ranges
    over. The class-dict value is what `InheritDocstrings.__init__` inspects."""
    class C:
        def meth(self):
            "M"
            pass

        def __call__(self, *a):
            "CALL"
            pass

        @property
        def prop(self):
            "P"
            return 1

        attr = 5  # an ordinary data attribute (not a descriptor)

    d = C.__dict__
    return [
        # an ordinary callable member -> a function, not a data descriptor
        ("function meth", d["meth"], True, False),
        ("dunder-call meth", d["__call__"], True, False),
        # the computed-attribute member (property) -> a data descriptor, NOT
        # a function. This is the discriminating case the F2P test exercises.
        ("property prop", d["prop"], False, True),
        # a plain data attribute participates in neither predicate
        ("plain attr", d["attr"], False, False),
    ]


def check_introspection_classification():
    """Assert the real inspect predicates classify each member kind as the
    model's boolean fields assume."""
    for label, obj, exp_fn, exp_dd in sample_members():
        got_fn = inspect.isfunction(obj)
        got_dd = inspect.isdatadescriptor(obj)
        assert got_fn == exp_fn, (
            "is_callable_member abstraction unsound for %s: "
            "inspect.isfunction gave %r, model assumes %r"
            % (label, got_fn, exp_fn))
        assert got_dd == exp_dd, (
            "is_computed_attribute abstraction unsound for %s: "
            "inspect.isdatadescriptor gave %r, model assumes %r"
            % (label, got_dd, exp_dd))


# --- the real patched decision (loop body) against the real callees ----------

def real_should_fill(val, is_public, has_own_doc):
    """The patched eligibility guard, computed with the REAL introspection
    callees on the real member object. Mirrors
    `(inspect.isfunction(val) or inspect.isdatadescriptor(val))
       and is_public_member(key) and val.__doc__ is None`."""
    return ((inspect.isfunction(val) or inspect.isdatadescriptor(val))
            and is_public and has_own_doc is False)


def is_public_member(key):
    """is_public_member from astropy/utils/misc.py (unchanged by the patch)."""
    return ((key.startswith('__') and key.endswith('__') and len(key) > 4)
            or not key.startswith('_'))


def check_behaviour_equivalence():
    """Re-derive the whole pinned behaviour with the real callees and assert it
    equals the model's fills_docstring eligibility, over the cross product of
    member kind x public x has-own-doc."""
    for label, obj, exp_fn, exp_dd in sample_members():
        for is_public in (True, False):
            for has_own_doc in (True, False):
                model = fills_docstring(exp_fn, exp_dd, is_public, has_own_doc)
                real = real_should_fill(obj, is_public, has_own_doc)
                assert model == real, (
                    "behaviour mismatch for %s (public=%r own_doc=%r): "
                    "model fills=%r, real fills=%r"
                    % (label, is_public, has_own_doc, model, real))

    # The discriminating witness, spelled out: a public, undocumented property
    # IS filled under the patched guard but a plain function is the only thing
    # filled under the pre-patch (isfunction-only) guard.
    _, prop_obj, _, _ = sample_members()[2]
    assert inspect.isfunction(prop_obj) is False, "property must not be a function"
    assert inspect.isdatadescriptor(prop_obj) is True, "property must be a descriptor"
    # patched guard fills the property; isfunction-only guard would not.
    assert real_should_fill(prop_obj, True, False) is True, (
        "patched guard must fill a public undocumented property")
    assert (inspect.isfunction(prop_obj) and True and True) is False, (
        "pre-patch isfunction-only guard would NOT fill a property")


def check_public_member_predicate():
    """Sanity-check is_public_member matches the model's is_public flag intent
    for representative keys (dunder, public, private)."""
    cases = {
        "__call__": True,    # dunder of length > 4 -> public
        "bar": True,         # ordinary public name
        "meth": True,
        "_hidden": False,    # leading underscore -> not public
        "__x": False,        # length-4 dunder boundary -> not public ('__x' not endswith __)
    }
    for key, exp in cases.items():
        got = is_public_member(key)
        assert got == exp, (
            "is_public_member(%r) gave %r, expected %r" % (key, got, exp))


def main():
    check_introspection_classification()
    check_public_member_predicate()
    check_behaviour_equivalence()
    print("G-AX OK: inspect.isfunction / inspect.isdatadescriptor classify "
          "the modeled member kinds as the spec assumes (property: not a "
          "function, is a data descriptor); the real patched decision matches "
          "fills_docstring over all member-kind x public x own-doc cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
