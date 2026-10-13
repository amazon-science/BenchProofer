#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8548.

This bundle has NO consumed @ContractOnly axiom. The operation that changed --
the rule that resolves a documented data attribute against the class's whole
method-resolution order (MRO) rather than against the class's own namespace
only, with earliest-MRO-class precedence -- is modelled DEEPLY in model.py
(the pure `resolve_from` / `resolved_doc` and the verified nested loop). This
script validates that deep model (an A-reference) against the REAL behaviour it
abstracts.

Two checks:

  (1) Always-runnable, standard-library only. A faithful transcription of the
      real (patched) collection loop -- the nested scan
        for cls in MRO:                      # earliest MRO class wins
            for (ns, name), doc in records:  # first matching record wins
                if ns == cls and name not in members:
                    members[name] = doc
      operating on the SAME abstract record table the model consumes (records
      keyed by (owner, name) -> doc, with `owner` standing for a class's
      qualified name and the MRO a list of those qualnames). The model's
      `resolve_from` rule is asserted to agree with this reference, per queried
      name, on boundary cases and randomized fuzz. The comparison is at the
      resolution level (which record wins for each name) -- NOT masked by any
      value/membership proxy.

  (2) End-to-end, only when the real Sphinx package is importable in the
      evaluation container. Synthesises real classes with comment-documented
      instance attributes (incl. base-only and overridden attributes), runs the
      REAL `sphinx.ext.autodoc.importer.get_class_members`, and asserts that the
      attribute -> documentation map it returns is exactly the model's
      resolution over the same hierarchy.

Exit 0 iff every observation matches the model.
"""
import random
import sys

ABSENT = -1


# --- model.py reference encodings (kept in lock-step with the pure spec) ------

def model_resolve(nm, mro, ens, enm, edoc):
    """Reference implementation of model.py's `resolved_doc` / `resolve_from`:
    earliest-MRO-owner, first-record resolution of attribute name `nm`."""
    for owner in mro:                       # earliest MRO class wins
        for j in range(len(ens)):           # first matching record wins
            if ens[j] == owner and enm[j] == nm:
                return edoc[j]
    return ABSENT


# --- (1) faithful transcription of the patched collection loop ---------------

def real_loop_collect(mro, records):
    """Transcription of the patched `get_class_members` instance-attribute loop.
    `records` is an ordered list of ((owner, name), doc). Returns the resolved
    name -> doc map."""
    members = {}
    for cls in mro:                         # for cls in getmro(subject)
        for (ns, name), doc in records:     # for (ns, name), doc in attr_docs
            if ns == cls and name not in members:
                members[name] = doc
    return members


def check_against_loop(mro, records):
    """Assert the model resolution agrees with the real loop for EVERY name that
    appears in any record (so an over-keep/under-keep cannot hide)."""
    ens = [ns for (ns, _name), _doc in records]
    enm = [name for (_ns, name), _doc in records]
    edoc = [doc for (_k, doc) in records]
    expected = real_loop_collect(mro, records)
    all_names = set(enm)
    for nm in all_names:
        got = model_resolve(nm, mro, ens, enm, edoc)
        exp = expected.get(nm, ABSENT)
        assert got == exp, (
            "resolve_from deep model unsound: name=%r mro=%r records=%r -> "
            "model gave %r, real loop gives %r" % (nm, mro, records, got, exp))
    # also a name on NO record must be ABSENT on both sides
    absent_name = max(all_names, default=0) + 1
    assert model_resolve(absent_name, mro, ens, enm, edoc) == ABSENT
    assert expected.get(absent_name, ABSENT) == ABSENT


def fuzz_loop_equivalence():
    rng = random.Random(8548)
    # boundary hierarchies
    boundary = [
        # the F2P scenario: Bar(Foo); attr1 base-only, attr2 overridden, attr3 own
        ([1, 0, 9], [(0, 1, 100), (0, 2, 100), (1, 2, 200), (1, 3, 200)]),
        # subject(=1) first then base(=0); attr2 documented on both
        ([1, 0], [(0, 2, 50), (1, 2, 60)]),
        # empty record table
        ([1, 0], []),
        # empty MRO
        ([], [(0, 1, 7)]),
        # base-only single attribute
        ([1, 0], [(0, 5, 500)]),
        # an unrelated owner (not on the MRO) must never resolve
        ([1, 0], [(7, 4, 400)]),
        # multiple records same owner+name: first one wins
        ([1], [(1, 3, 10), (1, 3, 20)]),
        # deeper MRO, attribute on the third class only
        ([3, 2, 1, 0], [(1, 8, 80)]),
    ]
    for mro, records in boundary:
        # records are (owner, name, doc) triples -> normalise to ((owner,name),doc)
        recs = [((o, n), d) for (o, n, d) in records]
        check_against_loop(mro, recs)

    # randomized fuzz
    for _ in range(20000):
        depth = rng.randint(0, 5)
        # distinct owner codes for the MRO classes
        owners_pool = rng.sample(range(0, 12), depth) if depth else []
        mro = owners_pool
        nrec = rng.randint(0, 8)
        recs = []
        for _ in range(nrec):
            # owner may or may not be on the MRO; name from a small alphabet so
            # collisions (overrides) and absences both occur
            owner = rng.randint(0, 13)
            name = rng.randint(0, 6)
            doc = rng.randint(0, 999)
            recs.append(((owner, name), doc))
        check_against_loop(mro, recs)


# --- (2) end-to-end against the real get_class_members -----------------------

def check_real_sphinx():
    """Run the REAL patched get_class_members on synthesised classes and assert
    its (attribute -> documentation) map equals the model's resolution. Skipped
    (returns None) when Sphinx is not importable; the Docker G-AX runs it."""
    try:
        from sphinx.ext.autodoc.importer import get_class_members
        from sphinx.util.inspect import safe_getattr, getmro
    except Exception:
        return None  # not in a Sphinx environment; the container G-AX covers it

    import textwrap
    import types

    # Build a real module with documented instance attributes, base + derived.
    src = textwrap.dedent('''
        class Foo:
            def __init__(self):
                self.attr1 = None  #: docstring foo
                self.attr2 = None  #: docstring foo


        class Bar(Foo):
            def __init__(self):
                self.attr2 = None  #: docstring bar
                self.attr3 = None  #: docstring bar
    ''')
    # Write to a real importable module file so ModuleAnalyzer.for_module works.
    import os
    import tempfile
    import importlib
    tmpdir = tempfile.mkdtemp()
    modname = "_gax_instance_variable_8548"
    path = os.path.join(tmpdir, modname + ".py")
    with open(path, "w") as f:
        f.write(src)
    sys.path.insert(0, tmpdir)
    try:
        mod = importlib.import_module(modname)
        Bar = mod.Bar

        members = get_class_members(Bar, ["Bar"], safe_getattr)

        # Collect the documentation strings the real function assigns, for the
        # instance attributes attr1/attr2/attr3.
        def doc_of(name):
            ca = members.get(name)
            if ca is None:
                return None
            # The model abstracts a documentation body to a single code; the
            # real `get_class_members` stores `'\n'.join(comment.splitlines() +
            # [''])` (a representational trailing-newline artifact of the
            # StringList join). Compare at the modeled resolution level -- WHICH
            # body wins for each name -- not raw bytes: normalize the trailing
            # newline(s) the join introduces.
            doc = ca.docstring
            return doc.rstrip("\n") if doc is not None else None

        observed = {n: doc_of(n) for n in ("attr1", "attr2", "attr3")}

        # Expected per the model: with the full MRO [Bar, Foo, object] and the
        # records (Foo,attr1)->foo, (Foo,attr2)->foo, (Bar,attr2)->bar,
        # (Bar,attr3)->bar, earliest-MRO-owner + first-record wins.
        # attr1: base-only -> foo ; attr2: overridden -> bar ; attr3: own -> bar
        expected = {
            "attr1": "docstring foo",
            "attr2": "docstring bar",
            "attr3": "docstring bar",
        }
        assert observed == expected, (
            "real get_class_members disagrees with model: observed=%r "
            "expected=%r" % (observed, expected))
        return True
    finally:
        sys.path.remove(tmpdir)


def check_real_parser():
    """Validate the record-table ABSTRACTION against the real Sphinx source
    parser: the comment-documentation keys it produces are exactly
    (owner-qualname, attribute-name) -> documentation, which is what the model's
    (ens, enm, edoc) table encodes. Then run the model's resolution over the
    real keys + the real MRO and assert the F2P/P2P attribute documentation.
    Uses only `sphinx.pycode.parser` (no docutils), so it runs on the host too;
    returns None if Sphinx is not importable at all."""
    try:
        from sphinx.pycode.parser import Parser
    except Exception:
        return None

    import textwrap
    src = textwrap.dedent('''
        class Foo:
            def __init__(self):
                self.attr1 = None  #: docstring foo
                self.attr2 = None  #: docstring foo


        class Bar(Foo):
            def __init__(self):
                self.attr2 = None  #: docstring bar
                self.attr3 = None  #: docstring bar
    ''')
    p = Parser(src)
    p.parse()
    # Real keys: (owner-qualname, attr-name) -> documentation comment.
    comments = dict(p.comments)
    assert set(comments.keys()) == {
        ("Foo", "attr1"), ("Foo", "attr2"),
        ("Bar", "attr2"), ("Bar", "attr3"),
    }, "record-table abstraction drift: real parser keys=%r" % (
        list(comments.keys()),)

    # Encode owners as integer codes and run the model resolution over the REAL
    # record table with Bar's MRO [Bar, Foo, object].
    code = {"Bar": 0, "Foo": 1, "object": 2}
    name_code = {"attr1": 10, "attr2": 11, "attr3": 12}
    doc_code = {}
    ens, enm, edoc = [], [], []
    for (owner, name), doc in comments.items():
        ens.append(code[owner])
        enm.append(name_code[name])
        d = doc_code.setdefault(doc, len(doc_code) + 100)
        edoc.append(d)
    inv_doc = {v: k for k, v in doc_code.items()}
    mro = [code["Bar"], code["Foo"], code["object"]]

    def model_doc(name):
        r = model_resolve(name_code[name], mro, ens, enm, edoc)
        if r == ABSENT:
            return None
        doc = inv_doc.get(r)
        # Compare at the modeled resolution level (which body wins), normalizing
        # any trailing-newline representational artifact -- the parser's raw
        # `comments` value is newline-free here, but keep this in lock-step with
        # check_real_sphinx so neither side is sensitive to the StringList join.
        return doc.rstrip("\n") if doc is not None else None

    observed = {n: model_doc(n) for n in ("attr1", "attr2", "attr3")}
    expected = {
        "attr1": "docstring foo",   # base-only -> resolves under fix
        "attr2": "docstring bar",   # overridden -> subject wins
        "attr3": "docstring bar",   # own
    }
    assert observed == expected, (
        "model resolution over REAL parser keys disagrees: observed=%r "
        "expected=%r" % (observed, expected))
    return True


def main():
    fuzz_loop_equivalence()
    parser_ok = check_real_parser()
    real = check_real_sphinx()
    tail = ""
    if parser_ok is True:
        tail += (" + record-table abstraction validated against the real "
                 "sphinx.pycode parser (F2P Bar(Foo): attr1/attr2/attr3)")
    if real is True:
        tail += (" + real get_class_members end-to-end "
                 "(Bar(Foo): attr1/attr2/attr3)")
    elif real is None:
        tail += " (real get_class_members end-to-end skipped: not importable here)"
    print("G-AX OK: resolve_from deep model == patched collection loop on 8 "
          "boundary + 20000 fuzz hierarchies" + tail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
