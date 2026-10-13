#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-15976.

The bundle models ONE routine: the presentation MathML printer's symbol-markup
assembly (`MathMLPresentationPrinter._print_Symbol`, mapping.md). Its observable
output is a markup tree (a minidom node). We capture a node as a canonical tuple:
  ('text', value)                          for a text leaf
  ('elem', tag, [(k,v),...], [child,...])  for an element

The modeled boundary is the markup assembly that runs AFTER the (unchanged)
`split_super_sub` + unicode `translate` steps: it consumes the base `name`, the
list of superscript strings `supers`, the list of subscript strings `subs`, and
the rendering `style`. So we fuzz those four directly.

ORACLE: an op-for-op replica of the POST-PATCH assembly, built with the real
stdlib `xml.dom.minidom` (the exact DOM API the gold code uses:
`createElement` / `appendChild` / `createTextNode` / `setAttribute`), then
canonicalised. This is maximally faithful to the gold edit.

SHADOW: an op-for-op transliteration of `implementation_symbolMarkup`
(Solution.lean impl region), per refinement.md.

This tests the soundness-critical clause: a scripted symbol must be rendered as
the bare `msub`/`msup`/`msubsup` element at top level (NOT wrapped in an extra
`mi`), an unscripted symbol as a single `mi`, multi-piece scripts laid out as an
`mrow` with `mo` space separators, and the `mathvariant="bold"` attribute set on
the resulting top element exactly under the bold style — matching the F2P
expectations in test_presentation_symbol / test_print_matrix_symbol.

stdlib-only. Pinned seed: 15976 (also in mapping.md / meta.json).
"""
import random
import string
import sys
from xml.dom import minidom


SEED = 15976
N = 120_000


# --- ORACLE: faithful replica of the POST-PATCH assembly via real minidom -----
_DOM = minidom.Document()


def _canon(node):
    if node.nodeType == node.TEXT_NODE:
        return ("text", node.nodeValue)
    attrs = []
    if node.attributes is not None:
        # preserve insertion order (setAttribute order); minidom keeps it
        for i in range(node.attributes.length):
            a = node.attributes.item(i)
            attrs.append((a.name, a.value))
    children = [_canon(c) for c in node.childNodes]
    return ("elem", node.nodeName, attrs, children)


def oracle(name, supers, subs, style):
    def join(items):
        if len(items) > 1:
            mrow = _DOM.createElement('mrow')
            for i, item in enumerate(items):
                if i > 0:
                    mo = _DOM.createElement('mo')
                    mo.appendChild(_DOM.createTextNode(" "))
                    mrow.appendChild(mo)
                mi = _DOM.createElement('mi')
                mi.appendChild(_DOM.createTextNode(item))
                mrow.appendChild(mi)
            return mrow
        else:
            mi = _DOM.createElement('mi')
            mi.appendChild(_DOM.createTextNode(items[0]))
            return mi

    mname = _DOM.createElement('mi')
    mname.appendChild(_DOM.createTextNode(name))
    if len(supers) == 0:
        if len(subs) == 0:
            x = mname
        else:
            x = _DOM.createElement('msub')
            x.appendChild(mname)
            x.appendChild(join(subs))
    else:
        if len(subs) == 0:
            x = _DOM.createElement('msup')
            x.appendChild(mname)
            x.appendChild(join(supers))
        else:
            x = _DOM.createElement('msubsup')
            x.appendChild(mname)
            x.appendChild(join(subs))
            x.appendChild(join(supers))
    if style == 'bold':
        x.setAttribute('mathvariant', 'bold')
    return _canon(x)


# --- SHADOW of implementation_symbolMarkup (the R/I legs) ---------------------
# Mirrors Solution.lean impl region exactly.
def join_sep(items):
    if not items:
        return []
    if len(items) == 1:
        return [("elem", "mi", [], [("text", items[0])])]
    x, *rest = items
    return ([("elem", "mi", [], [("text", x)]),
             ("elem", "mo", [], [("text", " ")])] + join_sep(rest))


def join_pieces(items):
    if len(items) > 1:
        return ("elem", "mrow", [], join_sep(items))
    else:
        head = items[0] if items else ""
        return ("elem", "mi", [], [("text", head)])


def set_attr(node, k, v):
    if node[0] == "elem":
        _, tag, attrs, children = node
        return ("elem", tag, attrs + [(k, v)], children)
    return node


def shadow(name, supers, subs, style):
    mname = ("elem", "mi", [], [("text", name)])
    if len(supers) == 0:
        if len(subs) == 0:
            x = mname
        else:
            x = ("elem", "msub", [], [mname, join_pieces(subs)])
    else:
        if len(subs) == 0:
            x = ("elem", "msup", [], [mname, join_pieces(supers)])
        else:
            x = ("elem", "msubsup", [], [mname, join_pieces(subs), join_pieces(supers)])
    if style == "bold":
        x = set_attr(x, "mathvariant", "bold")
    return x


def disagree(name, supers, subs, style):
    got = oracle(name, supers, subs, style)
    want = shadow(name, supers, subs, style)
    if got != want:
        return ((name, supers, subs, style), got, want)
    return None


def _edge_cases():
    return [
        # F2P x^2 -> msup
        ("x", ["2"], [], "plain"),
        # F2P x_2 -> msub
        ("x", [], ["2"], "plain"),
        # F2P x^3_2 -> msubsup (subs then supers)
        ("x", ["3"], ["2"], "plain"),
        # F2P x_2_a -> msub with mrow of two subs separated by space
        ("x", [], ["2", "a"], "plain"),
        # F2P x^2^a -> msup with mrow of two supers
        ("x", ["2", "a"], [], "plain"),
        # unscripted -> bare mi
        ("y", [], [], "plain"),
        # bold matrix symbol A -> mi mathvariant bold
        ("A", [], [], "bold"),
        # bold + scripted -> attribute on the script element
        ("A", ["1"], ["0"], "bold"),
        # three subs
        ("z", [], ["1", "2", "3"], "plain"),
        # both with multi pieces
        ("w", ["a", "b"], ["c", "d"], "bold"),
    ]


def _names(rng):
    return "".join(rng.choice(string.ascii_letters) for _ in range(rng.randint(1, 3)))


def _piece_list(rng):
    n = rng.randint(0, 4)
    pool = ["1", "2", "3", "a", "b", "x", "10", "i"]
    return [rng.choice(pool) for _ in range(n)]


def main() -> int:
    checked = 0
    for nm, sup, sub, st in _edge_cases():
        d = disagree(nm, sup, sub, st)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        nm = _names(rng)
        sup = _piece_list(rng)
        sub = _piece_list(rng)
        st = "bold" if rng.random() < 0.3 else "plain"
        d = disagree(nm, sup, sub, st)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
