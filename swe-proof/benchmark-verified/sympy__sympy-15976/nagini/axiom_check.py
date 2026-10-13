#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-15976.

The structural choice in model.py is modelled DEEPLY (the pure `root_tag_for` /
`child_tags_for` and the verified `print_symbol` builder); there is no consumed
@ContractOnly axiom. Two things are validated here against the REAL code:

  (A-reference 1) the unchanged name-decomposition helper `split_super_sub`
      (sympy.printing.conventions) — the only callee `_print_Symbol` invokes —
      maps each textual symbol name to (name, supers, subs) whose EMPTINESS is
      exactly the two flags the model reads. We run the real helper and derive
      `has_subs = len(subs) > 0`, `has_supers = len(supers) > 0`.

  (A-reference 2) the FIXED `_print_Symbol` builder == the model's deep
      structural mapping. We construct the post-fix presentation printer (by
      installing the gold builder onto the real printer class) and assert, for a
      battery of symbol names (every FAIL_TO_PASS case + fuzz), that the produced
      DOM element's `nodeName` equals the model's `root_tag_for(...)` and its
      `childNodes[i].nodeName` sequence equals the model's `child_tags_for(...)`,
      under the tag<->nodeName mapping below. Bold styling is checked to land on
      the produced root.

Imports only sympy (the repo under test) and the stdlib. Exit 0 iff every
observation matches the model.
"""
import random
import sys

# ---- model.py reference encodings (kept in lock-step with model.py) ---------
# Child codes are refined by ROLE IDENTITY: each direct child carries a code
# naming the role it fills as well as its element kind, so children in different
# roles are never interchangeable even when they share a DOM nodeName. The
# base-name identifier (TAG_MNAME), a one-part subscript group (TAG_SUB_ONE) and
# a one-part superscript group (TAG_SUP_ONE) all map to nodeName 'mi'; the
# several-part groups (TAG_SUB_ROW / TAG_SUP_ROW) map to 'mrow'. The role each
# code names is checked POSITIONALLY against the real child's content below.
TAG_MI, TAG_MSUB, TAG_MSUP, TAG_MSUBSUP = 1, 2, 3, 4
TAG_MNAME = 6
TAG_SUB_ONE, TAG_SUB_ROW, TAG_SUP_ONE, TAG_SUP_ROW = 7, 8, 9, 10
_TAG_NAME = {TAG_MI: 'mi', TAG_MSUB: 'msub', TAG_MSUP: 'msup',
             TAG_MSUBSUP: 'msubsup', TAG_MNAME: 'mi',
             TAG_SUB_ONE: 'mi', TAG_SUB_ROW: 'mrow',
             TAG_SUP_ONE: 'mi', TAG_SUP_ROW: 'mrow'}
# Which part list a group code renders — the ROLE the model claims for that
# slot. Used to check the real child's content at that position.
_ROLE_OF = {TAG_SUB_ONE: 'subs', TAG_SUB_ROW: 'subs',
            TAG_SUP_ONE: 'supers', TAG_SUP_ROW: 'supers'}


def root_tag_for(has_subs, has_supers):
    if not has_supers and not has_subs:
        return TAG_MI
    if not has_supers:
        return TAG_MSUB
    if not has_subs:
        return TAG_MSUP
    return TAG_MSUBSUP


def sub_group_tag(multi):
    return TAG_SUB_ROW if multi else TAG_SUB_ONE


def sup_group_tag(multi):
    return TAG_SUP_ROW if multi else TAG_SUP_ONE


def child_tags_for(has_subs, has_supers, subs_multi, supers_multi):
    if not has_supers and not has_subs:
        return []
    if not has_supers:
        return [TAG_MNAME, sub_group_tag(subs_multi)]
    if not has_subs:
        return [TAG_MNAME, sup_group_tag(supers_multi)]
    return [TAG_MNAME, sub_group_tag(subs_multi), sup_group_tag(supers_multi)]


def model_root_nodename(has_subs, has_supers):
    return _TAG_NAME[root_tag_for(has_subs, has_supers)]


def model_child_nodenames(has_subs, has_supers, subs_multi, supers_multi):
    return [_TAG_NAME[t]
            for t in child_tags_for(has_subs, has_supers, subs_multi,
                                    supers_multi)]


# ---- the post-fix _print_Symbol builder (the gold patch behaviour) ----------
# This is the gold-patch body of MathMLPresentationPrinter._print_Symbol: the
# structural element is the root `x`, the bold marker is set on it at the end.
def fixed_print_Symbol(self, sym, style='plain'):
    from sympy.printing.conventions import split_super_sub
    from sympy.printing.pretty.pretty_symbology import greek_unicode

    def join(items):
        if len(items) > 1:
            mrow = self.dom.createElement('mrow')
            for i, item in enumerate(items):
                if i > 0:
                    mo = self.dom.createElement('mo')
                    mo.appendChild(self.dom.createTextNode(" "))
                    mrow.appendChild(mo)
                mi = self.dom.createElement('mi')
                mi.appendChild(self.dom.createTextNode(item))
                mrow.appendChild(mi)
            return mrow
        else:
            mi = self.dom.createElement('mi')
            mi.appendChild(self.dom.createTextNode(items[0]))
            return mi

    def translate(s):
        if s in greek_unicode:
            return greek_unicode.get(s)
        else:
            return s

    name, supers, subs = split_super_sub(sym.name)
    name = translate(name)
    supers = [translate(sup) for sup in supers]
    subs = [translate(sub) for sub in subs]

    mname = self.dom.createElement('mi')
    mname.appendChild(self.dom.createTextNode(name))
    if len(supers) == 0:
        if len(subs) == 0:
            x = mname
        else:
            x = self.dom.createElement('msub')
            x.appendChild(mname)
            x.appendChild(join(subs))
    else:
        if len(subs) == 0:
            x = self.dom.createElement('msup')
            x.appendChild(mname)
            x.appendChild(join(supers))
        else:
            x = self.dom.createElement('msubsup')
            x.appendChild(mname)
            x.appendChild(join(subs))
            x.appendChild(join(supers))
    if style == 'bold':
        x.setAttribute('mathvariant', 'bold')
    return x


def make_printer():
    from sympy.printing.mathml import MathMLPresentationPrinter
    p = MathMLPresentationPrinter()
    return p


def decomposition_flags(symname):
    """Run the REAL unchanged helper to derive the four flags the model reads:
    whether each of the subscript / superscript lists is non-empty (drives the
    root kind) and whether each holds more than one part (drives the group kind
    via `join`)."""
    from sympy.printing.conventions import split_super_sub
    name, supers, subs = split_super_sub(symname)
    return (len(subs) > 0, len(supers) > 0, len(subs) > 1, len(supers) > 1)


def check_name(symname, bold=False):
    from sympy import Symbol
    has_subs, has_supers, subs_multi, supers_multi = decomposition_flags(symname)
    printer = make_printer()
    style = 'bold' if bold else 'plain'
    node = fixed_print_Symbol(printer, Symbol(symname), style=style)

    exp_root = model_root_nodename(has_subs, has_supers)
    assert node.nodeName == exp_root, (
        "root nodeName mismatch for %r: real fixed printer gave %r, model "
        "expects %r (has_subs=%s has_supers=%s)"
        % (symname, node.nodeName, exp_root, has_subs, has_supers))

    exp_kids = model_child_nodenames(has_subs, has_supers, subs_multi,
                                     supers_multi)
    # The model abstracts `ctags` as the kinds of ELEMENT children; a bare
    # identifier's text content is a '#text' node (the node's text, not an
    # element child) and is not part of that abstraction.
    elem_kids = [c for c in node.childNodes if c.nodeName != '#text']
    obs_kids = [c.nodeName for c in elem_kids]
    assert obs_kids == exp_kids, (
        "child nodeName sequence mismatch for %r: real fixed printer gave %r, "
        "model expects %r" % (symname, obs_kids, exp_kids))

    # ROLE-identity refinement: wherever the model places a role-bearing code
    # the real child at that POSITION must render exactly that role's content.
    # For TAG_MNAME that is the (translated) base name; for a group code it is
    # the part list (subs or supers) the code names. Checking the group slots by
    # content is what makes the subscript slot and the superscript slot
    # non-interchangeable even when both take the same element kind.
    from sympy.printing.conventions import split_super_sub
    from sympy.printing.pretty.pretty_symbology import greek_unicode
    base, supers, subs = split_super_sub(symname)
    base = greek_unicode.get(base, base)
    parts = {'subs': [greek_unicode.get(s, s) for s in subs],
             'supers': [greek_unicode.get(s, s) for s in supers]}
    exp_tags = child_tags_for(has_subs, has_supers, subs_multi, supers_multi)
    for i, t in enumerate(exp_tags):
        child = elem_kids[i]
        if t == TAG_MNAME:
            assert child.nodeName == 'mi', (
                "base-name child for %r is %r, expected an identifier"
                % (symname, child.nodeName))
            txt = "".join(c.nodeValue for c in child.childNodes
                          if c.nodeName == '#text')
            assert txt == base, (
                "base-name child position mismatch for %r: child %d carries "
                "text %r, model expects the base name %r"
                % (symname, i, txt, base))
        elif t in _ROLE_OF:
            role = _ROLE_OF[t]
            expect = parts[role]
            # `join` renders one part as a bare identifier holding that part's
            # text, and several parts as a grouping element whose identifier
            # children hold the parts in order (separated by 'mo' spacers).
            if len(expect) > 1:
                got = ["".join(g.nodeValue for g in mi.childNodes
                               if g.nodeName == '#text')
                       for mi in child.childNodes if mi.nodeName == 'mi']
            else:
                got = ["".join(g.nodeValue for g in child.childNodes
                               if g.nodeName == '#text')]
            assert got == expect, (
                "role/slot mismatch for %r: child %d is the %s slot per the "
                "model, but the real child renders %r where the %s parts are "
                "%r (the other list is %r) — the two script slots are not "
                "interchangeable"
                % (symname, i, role, got, role, expect,
                   parts['supers' if role == 'subs' else 'subs']))

    # The structural root must never be wrapped in an extra <mi> (the bug):
    # when there are sub/superscripts the root is NOT an identifier element.
    if has_subs or has_supers:
        assert node.nodeName != 'mi', (
            "extra-mi-wrapper regression for %r: root is an <mi> again" % symname)

    if bold:
        assert node.getAttribute('mathvariant') == 'bold', (
            "bold marker not on produced root for %r" % symname)


def main():
    # Every FAIL_TO_PASS symbol name in test_presentation_symbol, plus the
    # plain/sub/super/combined and trailing-digit cases the issue is about.
    f2p_names = [
        "x",          # bare identifier
        "x^2",        # super only
        "x__2",       # super only (alt notation)
        "x_2",        # sub only
        "x^3_2",      # both
        "x__3_2",     # both
        "x_2_a",      # sub only, multi-part subscript
        "x^2^a",      # super only, multi-part superscript
        "x__2__a",    # super only, multi-part superscript
        "x1",         # trailing-digit -> treated as subscript (the issue)
        "x2",         # the reported symbol
        "alpha",      # plain greek
        "alpha_1",    # greek with subscript
    ]
    for nm in f2p_names:
        check_name(nm, bold=False)
        check_name(nm, bold=True)

    # Fuzz: random names over a small alphabet with sub/sup/digit decorations.
    base = list("abcxyzXYZ")
    decos = ["", "_1", "^2", "_a^b", "__c", "1", "23", "_1_2", "^1^2",
             "_i^j", "_alpha", "^beta"]
    rng = random.Random(15976)
    for _ in range(4000):
        nm = rng.choice(base) + rng.choice(decos)
        # split_super_sub requires a non-empty name; guard trivially.
        if not nm:
            continue
        check_name(nm, bold=rng.random() < 0.5)

    print("G-AX OK: real split_super_sub + fixed _print_Symbol match the model "
          "deep structure on %d named + 4000 fuzz cases (root nodeName + child "
          "nodeName sequence + no-extra-mi + bold marker placement)"
          % len(f2p_names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
