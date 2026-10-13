#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7166 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM below with the
          contract calls (Requires/Ensures/Acc) stripped; the @Pure helper
          `fills_docstring` copies over as a plain function. The model IS
          Python: `Member` is a plain record and `apply_inheritance` runs
          unchanged. No PSeq usage, no @ContractOnly callees.

BRIDGE  — mapping.md section 2: a docstring is carried as an int identity
          (0 denotes "no docstring"); each distinct string observed in a
          case gets a distinct nonzero id via a per-case table. The two kind
          predicates and the public flag are the REAL callee results
          (inspect.isfunction / inspect.isdatadescriptor and the unchanged
          public-name rule), computed on the actual member object/key.
          `inherited_doc` is the result of the unchanged MRO resolution
          replayed on the real class (first base along the MRO that has the
          member -> its docstring); when no base has the member the walk
          resolves nothing and the member keeps its current docstring, so
          the bridge feeds the current docstring's identity (assignment is
          then the identity, matching the real no-op).

ORACLE  — the REAL patched class-construction helper (PYTHONPATH=/testbed,
          gold patch applied by the gate before this script runs):
          astropy.utils.misc.InheritDocstrings, invoked as a metaclass on a
          freshly-built class dict over a freshly-built base chain; the
          observable is the member's resulting __doc__.

Input domain: the modeled preconditions are trivially satisfiable (any
member record). Cases range over member kind (plain function, lambda,
property with/without docstring, staticmethod, plain data attribute),
key visibility (public / _private / dunder / short-dunder boundary),
own-docstring presence, and base-chain shape (no base member / direct base /
grandparent only / base member with no docstring).

>= 1e5 Requires-satisfying inputs: all boundary combinations plus 100000
fuzzed cases. Pinned seed: 7166.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo package only.
"""
import inspect
import itertools
import random
import sys

SEED = 7166
N_FUZZ = 100_000

# ---------------------------------------------------------------------------
# model.py pure region + impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Acc) stripped.
# ---------------------------------------------------------------------------


def fills_docstring(is_callable_member, is_computed_attribute,
                    is_public, has_own_doc):
    return ((is_callable_member or is_computed_attribute)
            and is_public and not has_own_doc)


class Member:
    def __init__(self, is_callable_member, is_computed_attribute,
                 is_public, has_own_doc, inherited_doc, doc):
        self.is_callable_member = is_callable_member
        self.is_computed_attribute = is_computed_attribute
        self.is_public = is_public
        self.has_own_doc = has_own_doc
        self.inherited_doc = inherited_doc
        self.doc = doc


def apply_inheritance(m):
    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc


# ---------------------------------------------------------------------------
# Case construction: fresh member objects and base chains per case.
# ---------------------------------------------------------------------------

KEYS = [
    "value", "compute", "bar",          # public
    "_hidden", "_x",                    # private
    "__norm__", "__thing__", "__ab__",  # dunder (public per the rule)
    "____",                             # len-4 dunder boundary (private)
    "_",                                # single underscore (private)
]

OWN_DOC = "OWN DOC TEXT"
BASE_DOC = "BASE DOC TEXT"
GRAND_DOC = "GRANDPARENT DOC TEXT"

KINDS = ["function", "function_doc", "lambda", "property", "property_doc",
         "staticmethod", "data"]
BASES = ["none", "base_doc", "base_nodoc", "grand_doc"]


def make_member(kind):
    """A fresh member object of the requested kind (fresh per case: the real
    helper mutates the member's __doc__ in place)."""
    if kind == "function":
        def f(self):
            pass
        return f
    if kind == "function_doc":
        def f(self):
            """OWN DOC TEXT"""
        return f
    if kind == "lambda":
        return lambda self: 42
    if kind == "property":
        return property(lambda self: 42)
    if kind == "property_doc":
        return property(lambda self: 42, doc=OWN_DOC)
    if kind == "staticmethod":
        def f():
            pass
        return staticmethod(f)
    # plain data attribute
    return 5


def make_base_member(doc):
    """The base-class counterpart: a property carrying the given docstring
    (any attribute kind works for the unchanged getattr resolution; a
    property keeps its docstring intact on class-level access)."""
    return property(lambda self: 0, doc=doc)


def make_bases(base_shape, key):
    if base_shape == "none":
        return (object,)
    if base_shape == "base_doc":
        Base = type("Base", (object,), {key: make_base_member(BASE_DOC)})
        return (Base,)
    if base_shape == "base_nodoc":
        Base = type("Base", (object,), {key: make_base_member(None)})
        return (Base,)
    # grand_doc: only the grandparent has the member
    Grand = type("Grand", (object,), {key: make_base_member(GRAND_DOC)})
    Mid = type("Mid", (Grand,), {})
    return (Mid,)


def is_public_name(key):
    # the unchanged public-name rule the helper applies to each key
    return ((key.startswith("__") and key.endswith("__") and len(key) > 4)
            or not key.startswith("_"))


def run_case(InheritDocstrings, kind, key, base_shape):
    """Build the case, run the real patched helper and the shadow, and
    return an error string on disagreement, else None."""
    val = make_member(kind)
    bases = make_bases(base_shape, key)

    # real predicate results + current docstring, observed BEFORE construction
    is_callable_member = inspect.isfunction(val)
    is_computed_attribute = inspect.isdatadescriptor(val)
    is_public = is_public_name(key)
    own_doc_before = getattr(val, "__doc__", None)
    has_own_doc = own_doc_before is not None

    # ORACLE: the real patched metaclass builds the class
    cls = InheritDocstrings("Case", bases, {key: val})
    real_doc = getattr(cls.__dict__[key], "__doc__", None)

    # BRIDGE: replay the unchanged MRO resolution for inherited_doc
    inherited = None
    resolved = False
    for base in cls.__mro__[1:]:
        super_member = getattr(base, key, None)
        if super_member is not None:
            inherited = super_member.__doc__
            resolved = True
            break
    if not resolved:
        inherited = own_doc_before  # nothing to resolve: assignment is a no-op

    # per-case docstring identity table (0 = no docstring)
    table = {}

    def ident(s):
        if s is None:
            return 0
        return table.setdefault(s, len(table) + 1)

    doc_before_id = ident(own_doc_before)
    inherited_id = ident(inherited)

    # SHADOW
    m = Member(is_callable_member, is_computed_attribute, is_public,
               has_own_doc, inherited_id, doc_before_id)
    apply_inheritance(m)

    if real_doc is None:
        real_id = 0
    elif real_doc in table:
        real_id = table[real_doc]
    else:
        real_id = -1  # a docstring the shadow could not have produced

    if m.doc != real_id:
        return ("DISAGREEMENT\n"
                "  kind=%r key=%r base=%r\n"
                "  predicates: callable=%r computed=%r public=%r own_doc=%r\n"
                "  inherited=%r\n"
                "  shadow doc id=%r  real doc=%r (id=%r)"
                % (kind, key, base_shape, is_callable_member,
                   is_computed_attribute, is_public, has_own_doc,
                   inherited, m.doc, real_doc, real_id))
    return None


def main():
    from astropy.utils.misc import InheritDocstrings

    boundary = list(itertools.product(KINDS, KEYS, BASES))

    rng = random.Random(SEED)
    fuzz = [(rng.choice(KINDS), rng.choice(KEYS), rng.choice(BASES))
            for _ in range(N_FUZZ)]

    checked = 0
    for kind, key, base_shape in itertools.chain(boundary, fuzz):
        err = run_case(InheritDocstrings, kind, key, base_shape)
        if err:
            print("G-CONF FAIL (seed=%d):" % SEED)
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "class-construction docstring helper on %d cases (%d boundary + "
          "%d fuzz, seed=%d), 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
