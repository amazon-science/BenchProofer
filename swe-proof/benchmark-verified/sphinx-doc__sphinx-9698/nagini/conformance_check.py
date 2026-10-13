#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9698 (nagini).

SHADOW: the impl region of model.py `get_member_index_text`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The impl region operates on plain Python lists of code points, so no PSeq shim
is needed at runtime; the single @Pure helper the impl calls
(`is_callable_role`) copies over as a plain function. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`sphinx.domains.python.PyMethod.get_index_text`, driven directly on a
minimally-constructed PyMethod (same technique as axiom_check.py). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable.

Type bridge (mapping.md section 2):
  * str <-> List[int] of Unicode code points: text[k] == ord(s[k]).
  * the integer role selector <-> `self.options` membership:
    0 -> {}, 1 -> {'classmethod'}, 2 -> {'property'}, 3 -> {'staticmethod'}.
  * the model takes the already-split member/class names; the real callee
    takes the dotted `name_cls` pair and re-derives the split at the LAST
    dot. The bridge passes ('<clsname>.<methname>', clsname) with an empty
    module name (so no module-prefix rewriting occurs). For the split to
    round-trip, fuzzed member names contain no '.' (class names may -- the
    split is at the last dot); this is a bridge restriction, not a Requires
    restriction, and matches the callee's operating domain (member names are
    identifiers, never dotted).

Input domain: Requires demands read access to both code-point lists and
0 <= option <= 3. Code points are drawn from an identifier-flavoured alphabet
plus punctuation/space/non-ASCII; empty names are included as boundaries.

>= 1e5 Requires-satisfying inputs: 1600 boundary (20 member x 20 class x 4
roles) + 100000 fuzz triples. Pinned fuzz seed: 96982.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import random
import sys

SEED = 96982
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped ----------------------------

def is_callable_role(option):
    return option != 2


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def get_member_index_text(methname, clsname, option):
    result = []  # type: list
    j = 0
    while j < len(methname):
        result.append(methname[j])
        j = j + 1
    if is_callable_role(option):
        result.append(40)
        result.append(41)
    result.append(32)
    result.append(40)
    k = 0
    while k < len(clsname):
        result.append(clsname[k])
        k = k + 1
    if option == 1:
        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
    elif option == 2:
        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
    elif option == 3:
        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
    else:
        result = result + [32, 109, 101, 116, 104, 111, 100, 41]
    return result


# --- oracle: the real patched repo function -----------------------------------

_OPT_KW = {0: None, 1: 'classmethod', 2: 'property', 3: 'staticmethod'}


def make_oracles(PyMethod):
    """One minimally-constructed PyMethod per role selector; calling its
    get_index_text with an empty module name exercises exactly the member-role
    branch under specification (no module-prefix rewriting, no env access)."""
    oracles = {}
    for option, kw in _OPT_KW.items():
        pm = PyMethod.__new__(PyMethod)
        pm.options = {} if kw is None else {kw: True}
        oracles[option] = pm
    return oracles


def check_triple(oracles, methname, clsname, option):
    """Run shadow and oracle on one (methname, clsname, option) triple;
    return an error string on disagreement, else None."""
    shadow = get_member_index_text([ord(c) for c in methname],
                                   [ord(c) for c in clsname], option)
    real = oracles[option].get_index_text('', (clsname + '.' + methname, clsname))
    real_cp = [ord(ch) for ch in real]
    if shadow != real_cp:
        return ("DISAGREEMENT\n  methname=%r clsname=%r option=%d\n"
                "  shadow=%r (%r)\n  real  =%r (%r)"
                % (methname, clsname, option,
                   shadow, ''.join(chr(c) for c in shadow), real_cp, real))
    return None


def main():
    # Importing the domain module first trips a circular import inside this
    # checkout (addnodes <-> util); loading the top-level application module
    # first settles the package, then the domain import is clean.
    import sphinx.application  # noqa: F401
    from sphinx.domains.python import PyMethod  # REAL patched repo class

    oracles = make_oracles(PyMethod)

    # Boundary: cartesian names x names x all four roles. Member names carry
    # no '.' (bridge round-trip); class names include dotted forms.
    methnames = ['meth5', 'bar', 'baz', 'do_thing', 'value', 'a', '', 'X',
                 'data_set', 'name_with_underscores', 'CamelCase', 'mixedCase',
                 'with space', "o'brien", 'unicode_é', '__init__',
                 '_private', 'p123', '%s', '()']
    clsnames = ['Class', 'Foo', 'a', '', 'X', 'pkg.Class', 'a.b.C',
                'CamelCase', 'with space', "o'brien", 'unicode_é',
                '_Private', 'C123', '%s', '()', 'trailing.', '.leading',
                'Class_', 'x', 'Zz']
    checked = 0
    for m in methnames:
        for c in clsnames:
            for option in (0, 1, 2, 3):
                err = check_triple(oracles, m, c, option)
                if err:
                    print(err)
                    return 1
                checked += 1

    # Fuzz: pinned seed. Member-name alphabet excludes '.'; class-name
    # alphabet includes it.
    rng = random.Random(SEED)
    meth_alpha = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      "0123456789_ '()%é")
    cls_alpha = meth_alpha + ['.']
    for _ in range(N_FUZZ):
        m = ''.join(rng.choice(meth_alpha) for _ in range(rng.randint(0, 16)))
        c = ''.join(rng.choice(cls_alpha) for _ in range(rng.randint(0, 16)))
        option = rng.randint(0, 3)
        err = check_triple(oracles, m, c, option)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real get_index_text on %d inputs "
          "(%d boundary + %d fuzz, seed %d), zero disagreements."
          % (checked, len(methnames) * len(clsnames) * 4, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
