#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15976 (nagini).

SHADOW: the `# impl-start` / `# impl-end` region of model.py, copied VERBATIM
below with only the contract calls stripped (`Requires`/`Ensures`/`Assert`/
`Fold`/`Unfold` and the `# type:` comments kept as written). Its dependencies
come over the same way: the `MNode` carrier (constructor body only, its
`Requires`/`Ensures`/`Fold` removed), the `@Pure` accessors `node_tag` /
`node_ctags` / `node_bold` (bodies with `Unfolding(...)` reduced to the field
read it denotes), and the `@Pure` helper `group_tag`. `PSeq`/`ToSeq` are
realized by the immutable-tuple shim below (the Nagini carrier's `take`/`+`/
`len`/`[]`/`==`). `root_tag_for` and `child_tags_for` are NOT part of the
shadow: they occur only inside `Ensures`, so they are contract text, not impl.
There are no `@ContractOnly` callees in this bundle (model.py's `axioms` region
is empty: the structural choice is modelled deeply).

ORACLE: the REAL patched repo function named by mapping.md §1 —
`MathMLPresentationPrinter._print_Symbol(self, sym, style='plain')`
(`sympy/printing/mathml.py:745` @ base_commit). It is CALLED, not
transliterated: the gate git-applies patch.diff to /testbed before this script
runs and sets PYTHONPATH, so `from sympy.printing.mathml import
MathMLPresentationPrinter` imports the patched module and the printer is
constructible in-container with no extra context (it only needs its own
`xml.dom.minidom.Document`). The observable the model pins is read straight off
the returned minidom element, so nothing about the patched builder is re-derived
here. The four decomposition flags the model takes as inputs are likewise
derived by CALLING the real unchanged `sympy.printing.conventions.
split_super_sub` (mapping.md §3.1), not by re-implementing its `_` / `^` / `__`
/ trailing-digit rules.

TYPE BRIDGE (mapping.md §2, inverted). Model side -> repo side: a symbol name
carried as `List[int]` code points becomes the `str` passed to `Symbol(...)`;
`bold` becomes `style='bold'` vs `'plain'`; `has_subs`/`has_supers`/
`subs_multi`/`supers_multi` are derived from the REAL `split_super_sub(name)`
lists as `len(subs)>0`, `len(supers)>0`, `len(subs)>1`, `len(supers)>1`. Repo
side -> model side: the returned element becomes an `MNode`-shaped observation
via `element.nodeName == _TAG_NAME[tag]`; `ctags[i]` against the nodeName of the
i-th direct ELEMENT child (a bare identifier's base name is a `#text` node, not
an element child, so the bare-identifier kind observes an empty child list);
`element.getAttribute('mathvariant') == 'bold'` against `bold`. §2's
ROLE-identity refinement is checked POSITIONALLY at every index: where the
shadow's `ctags` says `TAG_MNAME` the real child must be an `mi` whose text is
the translated base name; where it says a script-group code
(`TAG_SUB_ONE`/`TAG_SUB_ROW`/`TAG_SUP_ONE`/`TAG_SUP_ROW`) the real child at that
position must render exactly the part list that code names — the subscripts for a
`SUB` code, the superscripts for a `SUP` code. That content check is what makes
the two script slots non-interchangeable: they share an element kind whenever the
two lists have the same multiplicity, so a kind-only comparison could not tell a
subscript slot from a superscript one. Checking positionally rather than by
mapping text->kind is deliberate: a name like `x_x` has a subscript identifier
whose text also equals the base name, and a text->kind map would invent a
disagreement there.

INPUT DOMAIN. `print_symbol`'s only `Requires` is `Acc(list_pred(name), 1/2)`,
i.e. any name whatsoever; every generated input satisfies it. The abstract input
space the OBSERVABLE depends on is FINITE: `(has_subs, subs_multi)` and
`(has_supers, supers_multi)` are each one of three reachable states
(absent / single part / several parts) and `bold` is one of two, so 3*3*2 = 18
classes, and all 18 are enumerated exhaustively with witness names (both styles)
before any fuzzing — every branch of the impl region, both `group_tag` results,
and both bold outcomes are taken. The remaining model input, the name's code
points, is unbounded, so the fuzz phase varies it (bases, greek names,
trailing-digit names, `_`/`^`/`__` decorations, empty/degenerate script parts)
while re-covering the same 18 classes, up to >= 1e5 total checks. Includes the
F2P shapes from `test_presentation_symbol` (`x`, `x^2`, `x__2`, `x_2`, `x^3_2`,
`x__3_2`, `x_2_a`, `x^2^a`, `x2`) and the P2P bold matrix-symbol shape.

Pinned fuzz seed: 15976 (recorded in mapping.md under `## G-CONF`).

Exit 0 iff zero disagreements; on a disagreement the input and both sides are
printed and the exit status is 1. stdlib + sympy (the repo under test) only.
"""
import json
import random
import sys

SEED = 15976
N_FUZZ = 100_000


# --- PSeq / ToSeq shim: the Nagini immutable-sequence carrier ----------------

class PSeq:
    """Immutable sequence carrier (`take`/`drop`/`+`/`len`/`[]`/`==`)."""
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- element-kind codes, from model.py verbatim ------------------------------

TAG_MI = 1       # identifier element
TAG_MSUB = 2     # subscript element
TAG_MSUP = 3     # superscript element
TAG_MSUBSUP = 4  # sub-and-superscript element
TAG_MNAME = 6      # the identifier CHILD carrying the base name
TAG_SUB_ONE = 7    # the SUBSCRIPT group, one part      -> an identifier element
TAG_SUB_ROW = 8    # the SUBSCRIPT group, several parts -> a grouping element
TAG_SUP_ONE = 9    # the SUPERSCRIPT group, one part      -> an identifier element
TAG_SUP_ROW = 10   # the SUPERSCRIPT group, several parts -> a grouping element

# mapping.md §2: child code <-> DOM nodeName. TAG_MNAME, TAG_SUB_ONE and
# TAG_SUP_ONE all share the nodeName 'mi', and TAG_SUB_ROW/TAG_SUP_ROW share
# 'mrow'; they are separated by ROLE identity, checked positionally against the
# real child's rendered content (see the docstring).
_TAG_NAME = {TAG_MI: 'mi', TAG_MSUB: 'msub', TAG_MSUP: 'msup',
             TAG_MSUBSUP: 'msubsup', TAG_MNAME: 'mi',
             TAG_SUB_ONE: 'mi', TAG_SUB_ROW: 'mrow',
             TAG_SUP_ONE: 'mi', TAG_SUP_ROW: 'mrow'}
# Which part list each group code claims for its slot.
_ROLE_OF = {TAG_SUB_ONE: 'subs', TAG_SUB_ROW: 'subs',
            TAG_SUP_ONE: 'supers', TAG_SUP_ROW: 'supers'}


# --- model.py carrier + @Pure helpers, contracts stripped --------------------

class MNode:
    def __init__(self, tag, ctags):
        self.tag = tag
        self.ctags = ctags
        self.bold = False


def node_tag(n):
    return n.tag


def node_bold(n):
    return n.bold


def node_ctags(n):
    return ToSeq(n.ctags)


def sub_group_tag(multi):
    if multi:
        return TAG_SUB_ROW
    return TAG_SUB_ONE


def sup_group_tag(multi):
    if multi:
        return TAG_SUP_ROW
    return TAG_SUP_ONE


# --- SHADOW: the impl region of model.py, verbatim, contract calls stripped --

def print_symbol(name, has_subs, has_supers, subs_multi, supers_multi, bold):
    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            # bare identifier: the name is its own text content, no element child
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
            x = MNode(TAG_MSUBSUP, kids)
    # Set the bold marker on the produced root (touches only the marker; the
    # element kind and child kinds are unchanged).
    ct = node_ctags(x)
    tg = node_tag(x)
    x.bold = bold
    return x


# --- bridge: model carrier <-> repo values ----------------------------------

def name_to_codepoints(s):
    """Model carrier for `sym.name` (mapping.md §2): a `List[int]`."""
    return [ord(ch) for ch in s]


def codepoints_to_name(cps):
    """Inverse of the above: the `str` the real printer wants."""
    return "".join(chr(c) for c in cps)


def decomposition_flags(split_super_sub, symname):
    """The four flags model.py takes as inputs, from the REAL unchanged helper
    (mapping.md §3.1) — emptiness and multiplicity of its two lists."""
    base, supers, subs = split_super_sub(symname)
    return base, supers, subs, (len(subs) > 0, len(supers) > 0,
                                len(subs) > 1, len(supers) > 1)


def observe_real(node):
    """Bring the real minidom element into the model's observation carrier:
    (nodeName, direct ELEMENT children as (nodeName, text, part_texts), bold
    marker). `part_texts` is the ordered text of the child's own identifier
    children — what a grouping element renders when it joins several parts. It
    is what makes a script slot's ROLE observable (mapping.md §2): two children
    of the same element kind still differ if they render different part lists."""
    kids = []
    for c in node.childNodes:
        if c.nodeName == '#text':
            continue  # text content is not an element child (mapping.md §2)
        text = "".join(t.nodeValue for t in c.childNodes
                       if t.nodeName == '#text' and t.nodeValue is not None)
        parts = ["".join(g.nodeValue for g in mi.childNodes
                         if g.nodeName == '#text' and g.nodeValue is not None)
                 for mi in c.childNodes if mi.nodeName == 'mi']
        kids.append((c.nodeName, text, parts))
    bold = (node.getAttribute('mathvariant') == 'bold')
    return node.nodeName, kids, bold


def check_one(printer, Symbol, split_super_sub, translate, symname, bold):
    """Run shadow and oracle on one (name, style); return an error string on
    disagreement, else None."""
    base, supers, subs, flags = decomposition_flags(split_super_sub, symname)
    has_subs, has_supers, subs_multi, supers_multi = flags

    # --- shadow, over the model's carrier (name as List[int] code points) ---
    cps = name_to_codepoints(symname)
    shadow = print_symbol(cps, has_subs, has_supers,
                          subs_multi, supers_multi, bold)
    s_tag = node_tag(shadow)
    s_ctags = node_ctags(shadow)
    s_bold = node_bold(shadow)

    # --- oracle: the real patched _print_Symbol ---
    style = 'bold' if bold else 'plain'
    # the bridge back to the concrete value the real function wants
    node = printer._print_Symbol(Symbol(codepoints_to_name(cps)), style=style)
    r_tag, r_kids, r_bold = observe_real(node)

    def fail(what):
        return ("G-CONF FAIL (%s)\n  input: name=%r style=%s "
                "(flags has_subs=%s has_supers=%s subs_multi=%s "
                "supers_multi=%s from real split_super_sub -> "
                "base=%r supers=%r subs=%r)\n"
                "  shadow: tag=%s(%r) ctags=%r bold=%r\n"
                "  oracle: nodeName=%r element_children=%r bold=%r"
                % (what, symname, style, has_subs, has_supers, subs_multi,
                   supers_multi, base, supers, subs,
                   s_tag, _TAG_NAME[s_tag], [t for t in s_ctags._t], s_bold,
                   r_tag, r_kids, r_bold))

    # root element kind
    if _TAG_NAME[s_tag] != r_tag:
        return fail("root element kind")
    # direct element children, in order
    if len(s_ctags) != len(r_kids):
        return fail("number of direct element children")
    expected_base = translate(base)
    expected_parts = {'subs': [translate(s) for s in subs],
                      'supers': [translate(s) for s in supers]}
    for i in range(len(s_ctags)):
        t = s_ctags[i]
        cname, ctext, cparts = r_kids[i]
        if _TAG_NAME[t] != cname:
            return fail("kind of direct element child %d" % i)
        if t == TAG_MNAME and not (cname == 'mi' and ctext == expected_base):
            # §2 role identity: this position must be the identifier carrying
            # the base-name text.
            return fail("child %d is not the base-name identifier "
                        "(text=%r, expected %r)" % (i, ctext, expected_base))
        if t in _ROLE_OF:
            # §2 role identity for the script slots: this position must render
            # the part list its code names. Checked by CONTENT, so the subscript
            # slot and the superscript slot stay distinguishable even when both
            # groups take the same element kind.
            role = _ROLE_OF[t]
            want = expected_parts[role]
            got = cparts if len(want) > 1 else [ctext]
            if got != want:
                other = 'supers' if role == 'subs' else 'subs'
                return fail("child %d is the %s slot per the model but renders "
                            "%r; the %s parts are %r and the %s parts are %r "
                            "(script slots are not interchangeable)"
                            % (i, role, got, role, want, other,
                               expected_parts[other]))
    # bold marker placement (on the produced root)
    if s_bold != r_bold:
        return fail("bold marker on the root")
    return None


# --- input generation -------------------------------------------------------

# One witness name per reachable (subs state, supers state) class. States:
#   0 = absent, 1 = exactly one part, 2 = more than one part.
# 3 x 3 classes, each crossed with both styles below = the 18-class exhaustive
# enumeration of the observable's finite abstract domain.
_CLASS_WITNESS = {
    (0, 0): "x",            # bare identifier
    (1, 0): "x_2",          # sub only, single part          -> msub / mi
    (2, 0): "x_2_a",        # sub only, several parts        -> msub / mrow
    (0, 1): "x^2",          # super only, single part        -> msup / mi
    (0, 2): "x^2^a",        # super only, several parts      -> msup / mrow
    (1, 1): "x^3_2",        # both, single each              -> msubsup / mi mi
    (2, 1): "x^3_2_a",      # both, several subs             -> msubsup mrow mi
    (1, 2): "x^3^b_2",      # both, several supers           -> msubsup mi mrow
    (2, 2): "x^3^b_2_a",    # both, several of each          -> msubsup mrow mrow
}

# F2P shapes from test_presentation_symbol + the trailing-digit case from the
# issue + the P2P bold matrix-symbol shape + degenerate/boundary names.
_BOUNDARY_NAMES = sorted(set(list(_CLASS_WITNESS.values()) + [
    "x", "x^2", "x__2", "x_2", "x^3_2", "x__3_2", "x_2_a", "x^2^a", "x__2__a",
    "x1", "x2", "x23",                 # trailing digits -> subscript (the bug)
    "A",                                # bold matrix symbol (P2P)
    "alpha", "alpha_1", "beta^2",       # greek: translate() rewrites the base
    "",                                 # empty name
    "y", "Q_i^j", "w_a_b^c^d",
    "x_", "x__", "x^",                  # empty script parts
    "_x", "^x", "_", "^",               # degenerate leading markers
]))

_BASES = ["x", "y", "z", "a", "b", "c", "Q", "X", "Y", "alpha", "beta",
          "gamma", "Lambda", "phi", "ab", "xyz"]
_PARTS = ["1", "2", "3", "10", "a", "b", "i", "j", "n", "alpha", ""]


def _fuzz_name(rng):
    """A Requires-satisfying name; every draw stays inside the real printer's
    operating domain (the model's Requires admits any name)."""
    nm = rng.choice(_BASES)
    if rng.random() < 0.12:
        nm += str(rng.randint(0, 99))          # trailing-digit subscript path
    n_sub = rng.choice([0, 0, 1, 1, 2, 3])
    n_sup = rng.choice([0, 0, 1, 1, 2, 3])
    for _ in range(n_sup):
        nm += ("__" if rng.random() < 0.3 else "^") + rng.choice(_PARTS)
    for _ in range(n_sub):
        nm += "_" + rng.choice(_PARTS)
    return nm


def _class_of(split_super_sub, symname):
    _b, supers, subs = split_super_sub(symname)
    st = 0 if len(subs) == 0 else (1 if len(subs) == 1 else 2)
    sp = 0 if len(supers) == 0 else (1 if len(supers) == 1 else 2)
    return (st, sp)


def main():
    try:
        from sympy import Symbol
        from sympy.printing.mathml import MathMLPresentationPrinter
        from sympy.printing.conventions import split_super_sub
        from sympy.printing.pretty.pretty_symbology import greek_unicode
    except Exception as exc:                              # pragma: no cover
        print("G-CONF ERROR: cannot import the patched repo module: %r" % (exc,))
        return 2

    def translate(s):
        # the printer's own unicode step (mathml.py, unchanged by the patch)
        if s in greek_unicode:
            return greek_unicode.get(s)
        return s

    printer = MathMLPresentationPrinter()
    checked = 0
    seen_classes = set()

    # Phase 1: exhaustive over the finite abstract domain (9 script classes x
    # both styles = 18), then the F2P / degenerate boundary names.
    for cls, nm in sorted(_CLASS_WITNESS.items()):
        got = _class_of(split_super_sub, nm)
        if got != cls:
            print("G-CONF ERROR: witness %r for class %r lands in class %r "
                  "(real split_super_sub) — enumeration would be incomplete"
                  % (nm, cls, got))
            return 2
    for nm in _BOUNDARY_NAMES:
        for bold in (False, True):
            err = check_one(printer, Symbol, split_super_sub, translate, nm,
                            bold)
            if err:
                print(err)
                print(json.dumps({"checked": checked, "disagreements": 1,
                                  "seed": SEED, "status": "fail"}))
                return 1
            checked += 1
        seen_classes.add(_class_of(split_super_sub, nm))
    n_boundary = checked

    if len(seen_classes) != 9:
        print("G-CONF ERROR: boundary phase covered %d/9 script classes (%r)"
              % (len(seen_classes), sorted(seen_classes)))
        return 2

    # Phase 2: seeded fuzz over the same domain, varying the name's code points.
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        nm = _fuzz_name(rng)
        bold = rng.random() < 0.5
        err = check_one(printer, Symbol, split_super_sub, translate, nm, bold)
        if err:
            print(err)
            print(json.dumps({"checked": checked, "disagreements": 1,
                              "seed": SEED, "status": "fail"}))
            return 1
        checked += 1
        seen_classes.add(_class_of(split_super_sub, nm))

    print("G-CONF OK: contract-stripped impl region of model.py == real patched "
          "MathMLPresentationPrinter._print_Symbol on %d inputs (%d boundary: "
          "9/9 script classes x both styles + F2P/degenerate names, %d fuzz, "
          "seed %d); root element kind, direct element-child kinds with the "
          "base-name identifier pinned by content, and bold-marker placement "
          "all agree; 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "boundary": n_boundary,
                      "fuzz": N_FUZZ, "script_classes": len(seen_classes),
                      "disagreements": 0, "seed": SEED,
                      "oracle": "sympy.printing.mathml."
                                "MathMLPresentationPrinter._print_Symbol "
                                "(called, patched)",
                      "shadow": "direct (contract-stripped impl region)",
                      "status": "pass"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
