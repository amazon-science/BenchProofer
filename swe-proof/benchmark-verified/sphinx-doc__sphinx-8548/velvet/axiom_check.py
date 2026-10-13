#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8548.

This bundle has NO consumed axiom and NO deep-model reference: the collection
under specification is modeled DIRECTLY in Solution.lean by
`levelCandidates`/`candidates`/`collectStep`/`collected` (refinement.md §C).
G-AX therefore validates the *structural-abstraction facts the direct model
depends on* by executing the REAL Sphinx callees in-container at the BASE commit
(no patch applied). It deliberately does NOT restate the changed collection loop:
a restatement can only reproduce its author's reading of it, and the changed loop
is checked against the REAL patched function by G-CONF. Every obligation below is
either (a) a real callee compared against ground truth known from the generated
source, or (b) the model compared against the REAL pre-image function.

  (1) MRO SHAPE. `getmro(subject)` leads with the subject (most-derived-first),
      its entries are pairwise distinct, and mapping.md §2's class identity
      ('<module>.<qualname>') is injective on it — so `hierarchy`'s k-th
      `ClassLevel` denotes exactly one class and `Member.owner` denotes exactly
      one `ClassLevel`.

  (2) `annots` ABSTRACTION. For each MRO class, `ClassLevel.annots` is
      `[unmangle(cls, n) or "" for n in getannotations(cls)]` read from the REAL
      helpers. Asserted against ground truth: every non-private identifier
      annotated in that class's own body is present under its own name; a private
      identifier annotated by a DIFFERENT class of the MRO is present as the
      empty string (the real `unmangle` returns None there), which is what
      Solution.lean's `annots.filter (· ≠ "")` models; and the empty-string slot
      is really exercised (a non-zero count is asserted, so the clause cannot
      pass vacuously).

  (3) `attrs` ABSTRACTION. For each MRO class, `ClassLevel.attrs` is the entries
      of THAT class's own module's `ModuleAnalyzer.attr_docs` whose namespace key
      equals that class's `__qualname__`, in analyzer order. Asserted against
      ground truth: it equals the documented instance attributes written in that
      class's body, in source order — including for a base class living in a
      DIFFERENT module from the subject, which is only reachable because the
      analyzer is looked up per class.

  (4) `existing` ABSTRACTION. The member names already present before the
      collection are read from the REAL base `get_class_members(subject, objpath,
      attrgetter)` (analyzer omitted, so its attr-doc phase is inert): the names
      whose value is not INSTANCEATTR. Asserted equal to mapping.md §3.2's
      transliteration of the unchanged prefix, on every input.

  (5) DISCRIMINATION. `collected existing (candidates hierarchy)` is compared to
      the REAL pre-image `get_class_members(subject, objpath, attrgetter,
      analyzer)` at the base commit — the actual function, not a restatement. On
      the F2P `Bar(Foo)` fixture the pre-image omits the inherited `attr1`
      entirely, and the model's `owner` for `attr1` is the class whose body
      declares it (ground truth), not the subject. Also asserted: model != base
      pre-image, i.e. the modeled collection is a change and not a no-op.

Imports only `sphinx` (the package under change) + the standard library. Builds
real module source files (so the REAL `ModuleAnalyzer` parses real `#:` attribute
docstrings and the REAL `__annotations__` are populated) over boundary
hierarchies + randomized fuzz. Exit 0 iff every obligation holds.
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

_TMPDIR = tempfile.mkdtemp(prefix="gax_8548_")
sys.path.insert(0, _TMPDIR)
_MODCOUNT = [0]
_EMPTY_ANNOT_SLOTS = [0]


# --- input generation: real modules with real classes ------------------------

def emit_class(cname, bases, annots, classattrs, slots, attrs):
    lines = ["class %s(%s):" % (cname, ", ".join(bases)) if bases
             else "class %s:" % cname]
    body = []
    if slots:
        body.append("__slots__ = (%s)" % "".join("%r, " % s for s in slots))
    for a in annots:
        body.append("%s: int" % a)
    for a in classattrs:
        body.append("%s = 1" % a)
    if attrs:
        body.append("def __init__(self):")
        for attr, doc in attrs:
            body.append("    self.%s = None  #: %s" % (attr, doc))
    for b in (body or ["pass"]):
        lines.append("    " + b)
    lines.append("")
    return lines


def build_modules(specs, split):
    """specs: list of (class_name, [base], annots, classattrs, slots, [(attr,doc)]),
    base-first. The first `split` classes go into a SECOND real module that the
    first imports, so the per-class analyzer lookup is exercised."""
    _MODCOUNT[0] += 1
    n = _MODCOUNT[0]
    base_mod, main_mod = "gax_base_%d" % n, "gax_main_%d" % n
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
    mods = {False: None, True: None}
    if src_base:
        mods[True] = importlib.import_module(base_mod)
    mods[False] = importlib.import_module(main_mod)
    return {sp[0]: getattr(mods[i < split], sp[0]) for i, sp in enumerate(specs)}


# --- the abstraction functions (mapping.md §2/§3), on the REAL callees --------

def owner_key(cls):
    if cls is None:
        return "<none>"
    return "%s.%s" % (safe_getattr(cls, '__module__', '?'),
                      safe_getattr(cls, '__qualname__', '?'))


def real_hierarchy(subject):
    """mapping.md §2 `hierarchy : List ClassLevel` from the REAL callees."""
    hierarchy = []
    for cls in getmro(subject):
        annots = []
        try:
            for name in getannotations(cls):
                u = unmangle(cls, name)
                if not u:
                    _EMPTY_ANNOT_SLOTS[0] += 1
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
    """mapping.md §3.2 `existing`: transliteration of the UNCHANGED prefix of
    get_class_members (the enum / __slots__ / dir() phases)."""
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


# --- Solution.lean's pure region, transliterated -----------------------------

def level_candidates(level):
    owner, annots, attrs = level
    return ([(n, owner, None) for n in annots if n != ""]
            + [(name, owner, doc) for name, doc in attrs])


def model_collect(hierarchy, existing):
    """`collected existing (candidates hierarchy)` as name -> (owner, doc)."""
    out, seen = {}, set(existing)
    for level in hierarchy:
        for name, owner, doc in level_candidates(level):
            if name in seen:
                continue
            seen.add(name)
            out[name] = (owner, doc)
    return out


# --- the REAL base-commit function, in both of its two call shapes -----------

def base_without_analyzer(subject, objpath):
    """The base get_class_members with the analyzer omitted: its attr-doc phase
    is inert, so the non-INSTANCEATTR names it reports are exactly the member
    names present before the collection (`existing`)."""
    return get_class_members(subject, objpath, _attrgetter)


def base_pre_image(subject, objpath, analyzer):
    """The REAL pre-image collection: the base get_class_members driven with the
    subject module's analyzer, restricted to the INSTANCEATTR entries and
    observed as name -> (class_ identity, docstring)."""
    members = get_class_members(subject, objpath, _attrgetter, analyzer)
    return {n: (owner_key(a.class_), a.docstring)
            for n, a in members.items() if a.value is INSTANCEATTR}


def check_subject(subject, specs, split, classes):
    qn = subject.__qualname__
    objpath = [qn]

    # (1) MRO shape
    mro = getmro(subject)
    assert mro and mro[0] is subject, "%s: getmro does not lead with the subject" % qn
    assert len(set(mro)) == len(mro), "%s: getmro repeats a class: %r" % (qn, mro)
    keys = [owner_key(c) for c in mro]
    assert len(set(keys)) == len(keys), (
        "%s: class identity not injective on the MRO: %r" % (qn, keys))

    hierarchy = real_hierarchy(subject)
    assert len(hierarchy) == len(mro), "%s: hierarchy/MRO length mismatch" % qn

    by_name = {sp[0]: sp for sp in specs}
    for cls, (owner, annots, attrs) in zip(mro, hierarchy):
        assert owner == owner_key(cls)
        sp = by_name.get(cls.__name__)
        if sp is None or classes.get(cls.__name__) is not cls:
            continue                      # `object`: nothing declared, nothing to check
        _, _, decl_annots, _, _, decl_attrs = sp

        # (2) annots abstraction vs ground truth
        for a in decl_annots:
            if a.startswith("__") and not a.endswith("__"):
                mangled = "_%s__%s" % (cls.__name__, a.lstrip("_"))
                assert unmangle(cls, mangled) == a, (
                    "%s: unmangle(%s, %r) != %r" % (qn, cls.__name__, mangled, a))
                assert a in annots, (
                    "%s.%s: own private annotation %r missing from annots %r"
                    % (qn, cls.__name__, a, annots))
            else:
                assert a in annots, (
                    "%s.%s: own annotation %r missing from annots %r"
                    % (qn, cls.__name__, a, annots))
        for other in mro:
            if other is cls:
                continue
            for a in (by_name.get(other.__name__, (None, None, []))[2] or []):
                if a.startswith("__") and not a.endswith("__"):
                    foreign = "_%s__%s" % (other.__name__, a.lstrip("_"))
                    if foreign in getannotations(cls):
                        assert unmangle(cls, foreign) is None, (
                            "%s: unmangle(%s, %r) should be None" % (qn, cls.__name__, foreign))
                        assert "" in annots, (
                            "%s.%s: foreign private annotation %r not represented as ''"
                            % (qn, cls.__name__, foreign))

        # (3) attrs abstraction vs ground truth (source order preserved)
        assert [n for n, _ in attrs] == [n for n, _ in decl_attrs], (
            "%s.%s: attrs %r != declared %r"
            % (qn, cls.__name__, attrs, decl_attrs))
        for (n, doc), (dn, ddoc) in zip(attrs, decl_attrs):
            assert doc.rstrip("\n") == ddoc, (
                "%s.%s: attr %r docstring %r != declared %r"
                % (qn, cls.__name__, n, doc, ddoc))

    # (4) existing abstraction vs the REAL base callee
    real_pre = base_without_analyzer(subject, objpath)
    real_existing = {n for n, a in real_pre.items() if a.value is not INSTANCEATTR}
    modeled_existing = prefix_member_names(subject)
    assert real_existing == modeled_existing, (
        "%s: existing mismatch, symmetric difference %r"
        % (qn, sorted(real_existing ^ modeled_existing)))

    return hierarchy, model_collect(hierarchy, modeled_existing)


def main():
    rng = random.Random(SEED)

    # --- boundary: the F2P fixture (target/instance_variable.py verbatim) ----
    f2p = [("Foo", [], [], [], None,
            [("attr1", "docstring foo"), ("attr2", "docstring foo")]),
           ("Bar", ["Foo"], [], [], None,
            [("attr2", "docstring bar"), ("attr3", "docstring bar")])]
    classes = build_modules(f2p, 0)
    Bar, Foo = classes["Bar"], classes["Foo"]
    hierarchy, model = check_subject(Bar, f2p, 0, classes)
    assert set(model) == {"attr1", "attr2", "attr3"}, (
        "F2P: unexpected member set %r" % sorted(model))
    # The analyzer stores a one-line `#:` docstring as ['docstring foo', ''], so
    # '\n'.join(...) carries a trailing newline; the docstring bijection
    # (mapping.md §2) is compared up to that trailing blank in these literal
    # assertions (both sides of every model/oracle comparison join identically,
    # so it cancels there).
    def norm(v):
        o, d = v
        return (o, d.rstrip("\n") if isinstance(d, str) else d)
    assert norm(model["attr1"]) == (owner_key(Foo), "docstring foo"), (
        "F2P: attr1 not surfaced from its declaring class: %r" % (model["attr1"],))
    assert norm(model["attr2"]) == (owner_key(Bar), "docstring bar"), (
        "F2P: attr2 not resolved most-derived-first: %r" % (model["attr2"],))
    assert norm(model["attr3"]) == (owner_key(Bar), "docstring bar")

    # (5) discrimination against the REAL base-commit pre-image
    analyzer = ModuleAnalyzer.for_module(Bar.__module__)
    analyzer.analyze()
    pre = base_pre_image(Bar, [Bar.__qualname__], analyzer)
    assert "attr1" not in pre, (
        "the base pre-image already surfaces the inherited attr1: %r" % pre)
    assert set(pre) == {"attr2", "attr3"}, "unexpected base pre-image %r" % pre
    assert pre != model, "base pre-image == model (the collection is a no-op!)"

    # a subject with no inheritance: model and pre-image agree there
    h_foo, m_foo = check_subject(Foo, f2p, 0, classes)
    assert set(m_foo) == {"attr1", "attr2"}, "unexpected Foo model %r" % sorted(m_foo)

    # --- boundary: cross-module base, annotations, __slots__, mangled names --
    boundaries = [
        ([("Base", [], ["m"], [], None, [("n", "dn base")]),
          ("Sub", ["Base"], [], [], None, [("m", "dm sub"), ("o", "do sub")])], "Sub", 1),
        ([("A", [], ["__p", "q"], [], None, []),
          ("B", ["A"], [], [], None, [("q", "dq"), ("__p", "dp")])], "B", 0),
        ([("A", [], [], [], ("s1",), [("s1", "ds"), ("t", "dt")])], "A", 0),
        ([("A", [], ["a"], ["c"], None, [("a", "da"), ("c", "dc")])], "A", 0),
        ([("L", [], [], [], None, [("l", "dl")]),
          ("R", [], ["l"], [], None, [("r", "dr")]),
          ("D", ["L", "R"], [], [], None, [("d", "dd")])], "D", 2),
    ]
    for specs, subj, split in boundaries:
        cs = build_modules(specs, split)
        check_subject(cs[subj], specs, split, cs)
    # the cross-module base really does contribute (only possible if the analyzer
    # is looked up per class, not once for the subject's module)
    specs, subj, split = boundaries[0]
    cs = build_modules(specs, split)
    _, m = check_subject(cs[subj], specs, split, cs)
    assert cs["Base"].__module__ != cs["Sub"].__module__, "base/sub share a module"
    assert m["n"][0] == owner_key(cs["Base"]), (
        "cross-module base attribute not attributed to it: %r" % (m["n"],))

    # --- randomized fuzz -----------------------------------------------------
    pool = ["a", "b", "c", "d", "x", "y", "z", "attr1", "attr2", "attr3"]
    built = 0
    for _ in range(600):
        depth = rng.randint(1, 4)
        specs, prev = [], []
        for d in range(depth):
            cname = "C%d" % d
            annots = rng.sample(pool, rng.randint(0, 3))
            if rng.random() < 0.25:
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
        split = rng.randint(0, len(specs)) if rng.random() < 0.3 else 0
        try:
            cs = build_modules(specs, split)
        except Exception:            # a draw Python itself rejects
            continue
        built += 1
        check_subject(cs[specs[-1][0]], specs, split, cs)

    assert _EMPTY_ANNOT_SLOTS[0] > 0, (
        "no annotation ever unmangled to None: the empty-string slot of "
        "ClassLevel.annots was never exercised, so obligation (2) is vacuous")

    print("G-AX OK: MRO shape (distinct, most-derived-first, injective class "
          "identity) + annots/attrs/existing abstractions checked against the "
          "REAL callees and the generated ground truth on the F2P Bar(Foo) "
          "fixture, %d boundary hierarchies (cross-module base, __slots__, class "
          "attributes, mangled annotations, diamond MRO) and %d fuzzed "
          "hierarchies; %d annotation slot(s) unmangled to None; the REAL base "
          "pre-image omits the inherited attr1 while the model surfaces it "
          "attributed to its declaring class (the discriminating change)."
          % (len(boundaries), built, _EMPTY_ANNOT_SLOTS[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
