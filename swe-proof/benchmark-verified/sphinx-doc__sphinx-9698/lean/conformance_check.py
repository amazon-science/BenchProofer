#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-9698.

The bundle models ONE function: `PyMethod.get_index_text`
(`sphinx/domains/python.py`), which builds the text of the index entry for a
documented class member. The modeled value is a PURE function of six observables
(mapping.md):

    name            : str    (dotted member name, e.g. "Class.meth5")
    modname         : str    (enclosing module name, possibly "")
    isClassmethod   : bool    ('classmethod' in self.options)
    isProperty      : bool    ('property'    in self.options)
    isStaticmethod  : bool    ('staticmethod' in self.options)
    addModuleNames  : bool    (self.env.config.add_module_names)

Standing up a full Sphinx application/environment just to drive the real
`get_index_text` through a `PyMethod` instance is heavy and unnecessary: the
modeled value is this pure string assembly over observables. So the ORACLE below
is a faithful in-process replica that uses the EXACT patched format strings
(post-patch: the `property` arm has NO `()` after the member name), and the
SHADOW is the op-for-op transliteration of `implementation_getIndexText`
(`rsplitLastDot` then per-kind concatenation, per refinement.md).

`_(...)` (gettext) is the identity on the format string under the default/test
locale, and `% (a, b)` performs the two `%s` substitutions left-to-right; both
sides model it as concatenation. The split mirrors `name.rsplit('.', 1)`: no dot
=> the `except ValueError` fallback arm.

stdlib-only. Pinned seed: 9698 (also in mapping.md).
"""
import random
import sys

SEED = 9698
N = 120_000


# --- ORACLE: faithful in-process replica of the PATCHED get_index_text -------
def oracle_label(name, modname, is_classmethod, is_property, is_staticmethod,
                 add_module_names):
    options = set()
    if is_classmethod:
        options.add('classmethod')
    if is_property:
        options.add('property')
    if is_staticmethod:
        options.add('staticmethod')

    try:
        clsname, methname = name.rsplit('.', 1)
        if modname and add_module_names:
            clsname = '.'.join([modname, clsname])
    except ValueError:
        if modname:
            return '%s() (in module %s)' % (name, modname)
        else:
            return '%s()' % name

    if 'classmethod' in options:
        return '%s() (%s class method)' % (methname, clsname)
    elif 'property' in options:
        return '%s (%s property)' % (methname, clsname)         # post-patch: no ()
    elif 'staticmethod' in options:
        return '%s() (%s static method)' % (methname, clsname)
    else:
        return '%s() (%s method)' % (methname, clsname)


# --- SHADOW of implementation_getIndexText (the R/I leg) ---------------------
def _rsplit_last_dot(s):
    parts = s.split('.')
    if len(parts) <= 1:
        return None
    last = parts[-1]
    before = '.'.join(parts[:-1])
    return (before, last)


def shadow_label(name, modname, is_classmethod, is_property, is_staticmethod,
                 add_module_names):
    sp = _rsplit_last_dot(name)
    if sp is None:
        if modname != "":
            return name + "() (in module " + modname + ")"
        else:
            return name + "()"
    clsname0, methname = sp
    clsname = clsname0
    if add_module_names and modname != "":
        clsname = modname + "." + clsname0
    if is_classmethod:
        return methname + "() (" + clsname + " class method)"
    elif is_property:
        return methname + " (" + clsname + " property)"
    elif is_staticmethod:
        return methname + "() (" + clsname + " static method)"
    else:
        return methname + "() (" + clsname + " method)"


def disagree(args):
    got = oracle_label(*args)
    want = shadow_label(*args)
    if got != want:
        return (args, got, want)
    return None


NAME_POOL = [
    "Class.meth5", "Foo.bar", "a.b.c", "x.y", "lonely", "", ".", "a.",
    ".b", "A.B.C.d", "pkg.mod.Class.member", "Cls.__init__",
]
MOD_POOL = ["", "mod", "pkg.sub", "a.b.c"]


def _enumerate_edge():
    cases = []
    flags = [(c, p, s)
             for c in (True, False) for p in (True, False) for s in (True, False)]
    for name in NAME_POOL:
        for modname in MOD_POOL:
            for (c, p, s) in flags:
                for amn in (True, False):
                    cases.append((name, modname, c, p, s, amn))
    return cases


def main() -> int:
    checked = 0
    for args in _enumerate_edge():
        d = disagree(args)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    seg_pool = ["Class", "Foo", "meth5", "bar", "baz", "x", "y", "z",
                "member", "", "A", "B"]
    for _ in range(N):
        nseg = rng.randint(0, 4)
        name = ".".join(rng.choice(seg_pool) for _ in range(nseg))
        modname = rng.choice(MOD_POOL)
        c = rng.choice([True, False])
        p = rng.choice([True, False])
        s = rng.choice([True, False])
        amn = rng.choice([True, False])
        d = disagree((name, modname, c, p, s, amn))
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]!r} shadow={d[2]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
