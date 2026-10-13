#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-8548.

The bundle models ONE fragment: the `for cls in getmro(subject)` member-collection
loop at the tail of `get_class_members` (`sphinx/ext/autodoc/importer.py:300-327`
post-patch). Its Lean implementation (`implementation_gatherMemberDocs`) walks the
inheritance chain once and folds, per class, that class's TWO sources into a member
table — the names it declares by annotation alone, then the attributes recorded
under its own namespace — recording for each entry the class that supplied it:

    members = initial
    for cls in mro:                            # the loop the passes were MOVED INSIDE of
        for name in cls.annNames:              # annotation only member (ex. attr: int)
            if name not in members:
                members.append((name, None, cls))     # a name, NO documentation, owner cls
        for (ns, name, doc) in cls.attrDocs:
            if ns == cls.nsKey and name not in members:   # the CHANGED predicate
                members.append((name, doc, cls))          # the CHANGED owner
    return members

This script transliterates that R/I leg into Python (`shadow_gather`) and
differential-tests it against the ORACLE — and, unlike an earlier revision, the
oracle is not a hand-written replica of the loop but the REAL post-patch
`get_class_members` itself, driven over generated class hierarchies inside the
patched container (`real_oracle`). That is the point: a replica oracle can only
ever confirm the model's own assumptions, and it did — an earlier model applied the
annotation pass to the WHOLE chain up-front and only then walked the chain for
documented attributes, and the replica shared that flattening, so both agreed while
the real callee did something else. Concretely, when a base class DECLARES a name
that a more-derived class DOCUMENTS, the real nested loop reaches the derived class
first and records its docstring, whereas the flattened version let the base's bare
declaration land first and pre-empt it. Driving the real function is what makes this
gate able to refute that class of drift.

The member table is encoded as an ordered list of `(name, docstring, owner)`
triples, matching the Lean assoc-list model: `None` docstring for an
annotation-declared member, the joined docstring for a documented one, and `owner`
the IDENTITY of the class recorded in the entry (`ClassAttribute.class_`), bridged
to the Lean `classKey` by an injective per-class-object token — `None` where the
entry records no class, which the pre-loop `dir(subject)` pass really does produce
(`ClassAttribute(None, unmangled, value)`), so the `none` owner is a reachable
value of the carrier and not a modelling artifact. The owner is checked on BOTH
lanes: it is the component whose absence from an earlier revision of this carrier
let a rival that credits every collected attribute to the target class verify
against the spec. The `ClassAttribute.value` slot (INSTANCEATTR / SLOTSATTR) is the
one field still omitted, and it is omitted as a genuine frame: inside the modeled
fragment BOTH writes pass the same constant, so the fragment never chooses it — see
mapping.md for the measurement backing that.

`initial` is not fuzzed as an opaque list: it is COMPUTED by replaying the
patch-unchanged passes that run BEFORE the MRO loop (enum members, `__slots__`,
`dir(subject)`), so the seed the shadow receives is the seed the real function
actually built — owners included. Pinned seed: 8548 (also in mapping.md). exit 0
iff zero disagreements.
"""
import random
import sys
import traceback

SEED = 8548
N_REAL = 600          # generated hierarchies driven through the REAL callee
N_FUZZ = 120_000      # pure-carrier fuzz against the replica loop

GEN_DIR = "/tmp/sbu_conf_8548_gen"


# ===========================================================================
# LANE 1 — the REAL post-patch callee as oracle, over generated hierarchies.
# ===========================================================================

def _lane_real():
    """Drive the REAL patched `get_class_members` and compare to the shadow.

    Returns (checked, disagreements, note). If Sphinx cannot be imported (the
    script is being run outside the instance container) this lane reports
    unavailable and lane 2 still runs.
    """
    try:
        import os
        os.makedirs(GEN_DIR, exist_ok=True)
        if GEN_DIR not in sys.path:
            sys.path.insert(0, GEN_DIR)
        import importlib
        from sphinx.ext.autodoc.importer import get_class_members, unmangle
        from sphinx.util.inspect import (getannotations, getmro, getslots,
                                         isenumclass, safe_getattr)
        from sphinx.pycode import ModuleAnalyzer
    except Exception as exc:                                   # pragma: no cover
        return 0, 0, f"unavailable ({type(exc).__name__}: {exc})"

    # ---- the bijection for the OWNER component. The real entries record a class
    # ---- OBJECT (or None), and the consumer tests it by identity
    # ---- (`sphinx/ext/autodoc/__init__.py:1606`, `m.class_ == self.object`), so the
    # ---- token must be injective on object identity — NOT on the qualified name,
    # ---- which two classes on one chain can share. The class is kept alive in the
    # ---- table so an id() is never recycled under us.
    tokens = {}

    def token(cls):
        if cls is None:
            return None
        k = id(cls)
        if k not in tokens:
            tokens[k] = (f"c{len(tokens)}:{getattr(cls, '__qualname__', '?')}", cls)
        return tokens[k][0]

    # ---- the passes BEFORE the MRO loop, unchanged by the patch: they build the
    # ---- `initial` table the modeled fragment starts from. Their owners are part of
    # ---- that seed: the enum, __slots__ and own-__dict__ entries record the subject
    # ---- itself, and an inherited name reached through dir() records NO class.
    def initial_table(subject):
        obj_dict = safe_getattr(subject, '__dict__', {})
        members = {}
        if isenumclass(subject):
            for name in subject.__members__:
                if name not in members:
                    members[name] = (name, None, token(subject))
            superclass = subject.__mro__[1]
            for name in obj_dict:
                if name not in superclass.__dict__:
                    members[name] = (name, None, token(subject))
        try:
            __slots__ = getslots(subject)
            if __slots__:
                for name, docstring in __slots__.items():
                    members[name] = (name, docstring, token(subject))
        except (AttributeError, TypeError, ValueError):
            pass
        for name in dir(subject):
            try:
                safe_getattr(subject, name)
                unmangled = unmangle(subject, name)
                if unmangled and unmangled not in members:
                    owner = token(subject) if name in obj_dict else None
                    members[unmangled] = (unmangled, None, owner)
            except AttributeError:
                continue
        return [members[k] for k in members]

    # ---- the bijection: a real subject -> the Lean `mro : List ClassInfo`.
    def bridge(subject):
        mro = []
        for cls in getmro(subject):
            try:
                annNames = [n for n in (unmangle(cls, n) for n in getannotations(cls)) if n]
            except AttributeError:
                annNames = []
            attrDocs = []
            try:
                modname = safe_getattr(cls, '__module__')
                analyzer = ModuleAnalyzer.for_module(modname)
                analyzer.analyze()
                for (ns, name), doc in analyzer.attr_docs.items():
                    attrDocs.append((ns, name, '\n'.join(doc)))
            except Exception:
                attrDocs = []
            mro.append({"classKey": token(cls),
                        "nsKey": safe_getattr(cls, '__qualname__', ''),
                        "annNames": annNames, "attrDocs": attrDocs})
        return mro

    def real_oracle(subject, objpath):
        members = get_class_members(subject, objpath, safe_getattr)
        return [(n, ca.docstring, token(ca.class_)) for n, ca in members.items()]

    NAMES = ["a", "b", "c", "_D__m", "__x"]

    def gen(rnd, i):
        """A random hierarchy. Shapes deliberately include the interleaving case
        (a base DECLARES what a derived class DOCUMENTS), diamonds, slots, enums,
        nested qualnames, empty `#:` docstrings, and two classes on ONE chain that
        SHARE a qualified name (the shape that separates the recorded class's
        identity from its namespace key)."""
        lines = []
        shape = rnd.choice(["interleave", "linear", "diamond", "slots", "enum",
                            "nested", "samequalname"])
        if shape == "enum":
            lines.append("import enum")
        if shape == "interleave":
            # the exact class the faithfulness review's witness belongs to
            lines += ["class Base:", "    x: int", "    z: int", "",
                      "class C0(Base):", "    y: int", "    def __init__(self):",
                      "        self.x = 1  #: derived x doc",
                      "        self.w = 2  #: derived w doc", ""]
            target = "C0"
        elif shape == "diamond":
            lines += ["class A:", "    a: int",
                      "    def __init__(self):", "        self.b = 1  #: A b doc", "",
                      "class L(A):", "    def __init__(self):",
                      "        self.a = 1  #: L a doc", "",
                      "class R(A):", "    c: int",
                      "    def __init__(self):", "        self.c = 1  #: R c doc", "",
                      "class C0(L, R):", "    pass", ""]
            target = "C0"
        elif shape == "slots":
            lines += ["class A:", "    __slots__ = {'a': 'slot a doc', 'b': None}", "",
                      "class C0(A):", "    a: int", "    def __init__(self):",
                      "        self.a = 1  #: C0 a doc", "        self.b = 2  #:",
                      "        self.c = 3  #: C0 c doc", ""]
            target = "C0"
        elif shape == "enum":
            lines += ["class C0(enum.Enum):", "    a = 1", "    b = 2",
                      "    def __init__(self, *args):",
                      "        self.c = 1  #: C0 c doc", ""]
            target = "C0"
        elif shape == "nested":
            lines += ["class Outer:", "    class C0:", "        a: int",
                      "        def __init__(self):",
                      "            self.b = 1  #: inner b doc", ""]
            target = "Outer.C0"
        elif shape == "samequalname":
            # TWO distinct classes on one chain with the SAME __qualname__: the base
            # is built and then shadowed by a second definition of the same name, so
            # `nsKey` no longer identifies the chain member. The recorded owner must
            # still be the class that supplied the member.
            lines += ["class Shadow:", "    a: int",
                      "    def __init__(self):", "        self.a = 1  #: first a doc",
                      "        self.b = 2  #: first b doc", "",
                      "_first = Shadow", "",
                      "class Shadow(_first):", "    c: int",
                      "    def __init__(self):", "        self.c = 3  #: second c doc", "",
                      "C0 = Shadow", ""]
            target = "C0"
        else:
            n = rnd.randint(1, 3)
            names = [f"K{k}" for k in range(n)]
            for k, cn in enumerate(names):
                base = f"({names[k - 1]})" if k > 0 else ""
                lines.append(f"class {cn}{base}:")
                body = []
                for nm in NAMES:
                    if rnd.random() < 0.3:
                        body.append(f"    {nm}: int")
                inits = [nm for nm in NAMES if rnd.random() < 0.3]
                if inits:
                    body.append("    def __init__(self):")
                    for nm in inits:
                        doc = "" if rnd.random() < 0.2 else f" {cn} {nm} doc"
                        body.append(f"        self.{nm} = 1  #:{doc}")
                if not body:
                    body.append("    pass")
                lines += body + [""]
            target = names[-1]
        mod = f"sbu_conf_{i}"
        with open(f"{GEN_DIR}/{mod}.py", "w") as fh:
            fh.write("\n".join(lines))
        return mod, target

    rnd = random.Random(SEED)
    checked = 0
    bad = 0
    interleave_seen = 0
    owner_seen = 0
    for i in range(N_REAL):
        mod, target = gen(rnd, i)
        try:
            m = importlib.import_module(mod)
            subject = m
            for part in target.split('.'):
                subject = getattr(subject, part)
            got = real_oracle(subject, target.split('.'))
            want = shadow_gather(bridge(subject), initial_table(subject))
        except Exception:
            print(f"ERROR driving {mod}:")
            traceback.print_exc()
            bad += 1
            continue
        checked += 1
        # does this case exercise the interleaving clause at all?
        names_with_doc = {n for n, d, _ in got if d}
        if names_with_doc:
            interleave_seen += 1
        # does it exercise the OWNER clause — i.e. is any member credited to a class
        # OTHER than the subject (an inherited one), which is what a rival crediting
        # everything to the target class would get wrong?
        subj_token = token(subject)
        if any(o is not None and o != subj_token for _, _, o in got):
            owner_seen += 1
        if got != want:
            bad += 1
            if bad <= 5:
                print(f"DISAGREE {mod} (target {target})")
                print(f"  real  ={got}")
                print(f"  shadow={want}")
    if owner_seen == 0:
        print("ERROR: no generated hierarchy credits a member to a class other than "
              "the target, so the owner clause is untested on this lane")
        bad += 1
    return checked, bad, (f"interleaving-exercising cases={interleave_seen} "
                          f"owner-exercising cases={owner_seen}")


# ===========================================================================
# LANE 2 — pure-carrier fuzz against a replica of the post-patch nested loop.
# Kept as a cheap high-volume lane over the bijected carrier directly (it can
# reach namespace/name/identity combinations the generated-source lane cannot
# express — notably two chain classes sharing a qualified name), but it is
# explicitly NOT the primary oracle: lane 1 is.
# ===========================================================================

NAMES = ["a", "b", "c", "d"]
NSKEYS = ["Bar", "Foo", "Base", "Mix"]
DOCS = ["d0", "d1", "d2"]


def replica_gather(mro, initial):
    """The POST-PATCH nested loop, replicated over the bijected carrier."""
    members = list(initial)
    seen = {n for (n, _, _) in members}
    for cls in mro:                                    # for cls in getmro(subject)
        for name in cls["annNames"]:                   # annotation only member
            if name not in seen:
                # ClassAttribute(cls, name, INSTANCEATTR)
                members.append((name, None, cls["classKey"]))
                seen.add(name)
        qualname = cls["nsKey"]
        for (ns, name, doc) in cls["attrDocs"]:        # analyzer.attr_docs.items()
            if ns == qualname and name not in seen:    # post-patch: ns == qualname
                # ClassAttribute(cls, name, INSTANCEATTR, '\n'.join(docstring))
                members.append((name, doc, cls["classKey"]))
                seen.add(name)
    return members


def shadow_gather(mro, initial):
    """Shadow of `implementation_gatherMemberDocs` (the R/I leg), transliterated."""
    members = list(initial)
    for cls in mro:
        for name in cls["annNames"]:
            if name not in [m[0] for m in members]:
                members = members + [(name, None, cls["classKey"])]
        for (ns, name, doc) in cls["attrDocs"]:
            if ns == cls["nsKey"] and name not in [m[0] for m in members]:
                members = members + [(name, doc, cls["classKey"])]
    return members


def prepatch_gather(mro, initial):
    """base_commit: the annotation pass runs over the WHOLE chain first, then the
    attribute-docstring pass runs ONCE, for the TARGET (head) class only — and
    credits what it collects to that TARGET class (`ClassAttribute(subject, ...)`)."""
    members = list(initial)
    for cls in mro:
        for name in cls["annNames"]:
            if name not in [m[0] for m in members]:
                members = members + [(name, None, cls["classKey"])]
    if mro:
        target = mro[0]
        for (ns, name, doc) in target["attrDocs"]:
            if ns == target["nsKey"] and name not in [m[0] for m in members]:
                members = members + [(name, doc, target["classKey"])]
    return members


def target_owner_gather(mro, initial):
    """The recorded verify-does-not-imply-resolve rival, on the bijected carrier:
    the post-patch walk exactly, except that every collected documented attribute is
    credited to the HEAD of the chain instead of the class whose own namespace it
    matched (`ClassAttribute(subject, ...)` where the patch writes `cls`). Kept here
    so this gate, and not only the falsification battery, records that the modeled
    carrier can SEE that divergence."""
    members = list(initial)
    head = mro[0]["classKey"] if mro else None
    for cls in mro:
        for name in cls["annNames"]:
            if name not in [m[0] for m in members]:
                members = members + [(name, None, cls["classKey"])]
        for (ns, name, doc) in cls["attrDocs"]:
            if ns == cls["nsKey"] and name not in [m[0] for m in members]:
                members = members + [(name, doc, head)]
    return members


def _lcg(seed):
    # Yield the HIGH bits of the LCG state: an LCG's low-order bits have very
    # short periods, so `next(rnd) % k` on the raw state is badly correlated.
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield (x >> 16) & 0x7FFF


def _gen_case(rnd):
    nclasses = next(rnd) % 5 + 1                   # 1..5 classes in the chain
    mro = []
    for k in range(nclasses):
        nsKey = NSKEYS[next(rnd) % len(NSKEYS)]
        # The identity is INDEPENDENT of the namespace key: distinct per chain
        # position, so two classes CAN share a key (a shape the source-generating
        # lane can only reach through name shadowing).
        classKey = f"c{k}"
        nann = next(rnd) % 3                       # 0..2 annotation-declared names
        annNames = [NAMES[next(rnd) % len(NAMES)] for _ in range(nann)]
        nentries = next(rnd) % 4                   # 0..3 recorded attr docs
        attrDocs = []
        for _ in range(nentries):
            ns = NSKEYS[next(rnd) % len(NSKEYS)]   # may or may NOT equal nsKey
            name = NAMES[next(rnd) % len(NAMES)]
            doc = DOCS[next(rnd) % len(DOCS)]
            attrDocs.append((ns, name, doc))
        mro.append({"classKey": classKey, "nsKey": nsKey,
                    "annNames": annNames, "attrDocs": attrDocs})
    ninit = next(rnd) % 3                          # 0..2 pre-existing members
    initial = []
    for _ in range(ninit):
        # the pre-loop passes record the subject, or NO class at all (the dir() pass)
        owner = None if next(rnd) % 3 == 0 else "c0"
        initial.append((NAMES[next(rnd) % len(NAMES)],
                        DOCS[next(rnd) % len(DOCS)], owner))
    return mro, initial


def _lane_fuzz():
    rnd = _lcg(SEED)
    checked = 0
    discriminated = 0
    owner_discriminated = 0
    for _ in range(N_FUZZ):
        mro, initial = _gen_case(rnd)
        got = replica_gather(mro, initial)
        want = shadow_gather(mro, initial)
        if got != want:
            print(f"DISAGREE mro={mro} initial={initial}: replica={got} shadow={want}")
            return checked, 1, 0, 0
        if prepatch_gather(mro, initial) != got:
            discriminated += 1
        if target_owner_gather(mro, initial) != got:
            owner_discriminated += 1
        checked += 1
    return checked, 0, discriminated, owner_discriminated


def main() -> int:
    fails = 0

    # ---- lane 1: the real callee ----
    r_checked, r_bad, r_note = _lane_real()
    print(f"lane=real checked={r_checked} disagreements={r_bad} {r_note}")
    if r_bad:
        fails += 1
    if r_checked == 0:
        # The real-callee lane is the load-bearing one; if it could not run we
        # must not report a pass on the replica lane alone.
        print("status=fail reason=real-callee lane unavailable "
              "(must run inside the patched instance container)")
        return 1

    # ---- lane 2: pure-carrier fuzz ----
    f_checked, f_bad, f_disc, f_owner = _lane_fuzz()
    print(f"lane=fuzz checked={f_checked} disagreements={f_bad} "
          f"discriminating_cases={f_disc} owner_discriminating_cases={f_owner}")
    if f_bad:
        fails += 1
    if f_disc == 0:
        print("status=fail reason=corpus does not discriminate prepatch from spec")
        return 1
    if f_owner == 0:
        print("status=fail reason=corpus does not discriminate the "
              "target-credited-owner rival from spec")
        return 1

    # ---- pinned FAIL_TO_PASS-shaped case, on the bijected carrier ----
    # Foo and Bar live in ONE module, so each MRO class re-analyzes that module and
    # sees the WHOLE module's table: entries for BOTH ("Bar", attrN) and
    # ("Foo", attrN). The discriminator the patch changed is the NAMESPACE FILTER:
    # base-commit keys the single pass on the target namespace ("Bar"), so the
    # ("Foo", attr1) entry already visible in the table is FILTERED OUT; post-patch
    # the pass runs per MRO class keyed on that class's own qualname, so when
    # cls == Foo the filter ns == "Foo" admits attr1 — and credits it to Foo, which
    # is what the consumer's own-members test then reads.
    MODULE_TABLE = [
        ("Bar", "attr2", "bar"), ("Bar", "attr3", "bar"),
        ("Foo", "attr1", "foo"), ("Foo", "attr2", "foo"),
    ]
    f2p = [
        {"classKey": "cBar", "nsKey": "Bar", "annNames": [],
         "attrDocs": list(MODULE_TABLE)},
        {"classKey": "cFoo", "nsKey": "Foo", "annNames": [],
         "attrDocs": list(MODULE_TABLE)},
    ]
    got = replica_gather(f2p, [])
    want = shadow_gather(f2p, [])
    if got != want:
        print(f"DISAGREE f2p: replica={got} shadow={want}")
        print("status=fail")
        return 1
    assert got == [("attr2", "bar", "cBar"), ("attr3", "bar", "cBar"),
                   ("attr1", "foo", "cFoo")], got
    assert ("attr1", "foo", "cFoo") in got, "post-patch must collect inherited attr1"
    pre = prepatch_gather(f2p, [])
    assert not [t for t in pre if t[0] == "attr1"], \
        "prepatch namespace filter must drop attr1"
    # the recorded rival agrees on names and docstrings here and differs ONLY in the
    # class credited with the inherited attribute — the whole reason that field is
    # modeled.
    tgt = target_owner_gather(f2p, [])
    assert [(n, d) for n, d, _ in tgt] == [(n, d) for n, d, _ in got], tgt
    assert tgt != got and ("attr1", "foo", "cBar") in tgt, tgt

    # ---- pinned INTERLEAVING case: the faithfulness review's witness, on the
    # ---- bijected carrier. A base class DECLARES `x`; a more-derived class
    # ---- DOCUMENTS `x`. The documentation must win.
    wit = [
        {"classKey": "cDerived", "nsKey": "Derived", "annNames": ["y"],
         "attrDocs": [("Derived", "x", "derived x doc\n")]},
        {"classKey": "cBase", "nsKey": "Base", "annNames": ["x"],
         "attrDocs": [("Derived", "x", "derived x doc\n")]},
        {"classKey": "cobject", "nsKey": "object", "annNames": [], "attrDocs": []},
    ]
    got = replica_gather(wit, [])
    want = shadow_gather(wit, [])
    if got != want:
        print(f"DISAGREE interleave: replica={got} shadow={want}")
        print("status=fail")
        return 1
    assert got == [("y", None, "cDerived"), ("x", "derived x doc\n", "cDerived")], got
    # and the FLATTENED model the review refuted must differ here
    flat = [(n, wit[0]["classKey"]) for n in wit[0]["annNames"]]
    flat += [(n, wit[1]["classKey"]) for n in wit[1]["annNames"]]
    flattened, seen = [], set()
    for n, own in flat:
        if n not in seen:
            flattened.append((n, None, own))
            seen.add(n)
    for cls in wit:
        for (ns, name, doc) in cls["attrDocs"]:
            if ns == cls["nsKey"] and name not in seen:
                flattened.append((name, doc, cls["classKey"]))
                seen.add(name)
    assert {n: d for n, d, _ in flattened}.get("x") is None, flattened
    assert {n: d for n, d, _ in got}.get("x") == "derived x doc\n", got

    # ---- pinned SHARED-QUALNAME case: two DISTINCT classes on one chain carrying
    # ---- the same namespace key. The entry must be credited to the class being
    # ---- visited, which a lookup keyed on the namespace gets wrong — so the
    # ---- carrier must keep the identity and the key as separate data.
    shared = [
        {"classKey": "cSecond", "nsKey": "Q", "annNames": [], "attrDocs": []},
        {"classKey": "cFirst", "nsKey": "Q", "annNames": [],
         "attrDocs": [("Q", "x", "first x doc")]},
    ]
    got = replica_gather(shared, [])
    want = shadow_gather(shared, [])
    if got != want:
        print(f"DISAGREE shared-qualname: replica={got} shadow={want}")
        print("status=fail")
        return 1
    assert got == [("x", "first x doc", "cFirst")], got
    by_key = [(n, d, next(c["classKey"] for c in shared if c["nsKey"] == ns))
              for c0 in shared for (ns, n, d) in c0["attrDocs"] if ns == c0["nsKey"]]
    assert by_key == [("x", "first x doc", "cSecond")] and by_key != got, by_key

    if fails:
        print("status=fail")
        return 1
    print(f"checked={r_checked + f_checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
