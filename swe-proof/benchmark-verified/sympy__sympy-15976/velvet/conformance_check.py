#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-15976 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md: the modeled
node-assembly `buildSymbol` (which node represents a printed variable, and where
the bold attribute lands) against the behaviour of the patched real printer.

ORACLE CHOICE — why we drive the real `_print_Symbol` end-to-end rather than
re-deriving the node from a transliterated table:
  The node assembly is produced inside `MathMLPresentationPrinter._print_Symbol`
  (a minidom node result), so the real correctness oracle is the patched printer
  itself. We build a `Symbol` for each modeled script combination, render it with
  the patched printer, and recover the OBSERVABLE the model pins:
      (top node tag, top node bold?, tuple of child tags).
  The SHADOW is the modeled `buildSymbol` from Solution.lean's `buildSymbolNode`
  post-image, fed the SAME base name and the SAME presence/absence of each script
  node recovered from the real render. The script nodes' own internal structure
  (how `join` lays out a multi-piece subscript) is UNCHANGED by the patch and is
  treated as an input on both sides; G-CONF isolates the R/I top-node-shape leg —
  the behaviour the patch changes.

  Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image with the gold patch
applied), sympy + stdlib only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 15976
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean `buildSymbol`, transliterated -------------
# Carrier: a node is (tag, bold, (child tags...)).  `subs`/`sups` are the
# presence flags (None or a stand-in tag string for the rendered script node).
def shadow_build(name_present, sub_tag, sup_tag, bold):
    """buildSymbol transliterated from Solution.lean (pure region).

    Returns the observable triple (top_tag, top_bold, child_tags).
    `sub_tag`/`sup_tag` are None when absent, else the tag of the already-rendered
    script node (an input — its shape is not under test)."""
    mname_tag = "mi"
    if sup_tag is None and sub_tag is None:
        top_tag, children = "mi", ("#text",)          # bare base-name <mi>(name)
    elif sup_tag is None and sub_tag is not None:
        top_tag, children = "msub", (mname_tag, sub_tag)
    elif sup_tag is not None and sub_tag is None:
        top_tag, children = "msup", (mname_tag, sup_tag)
    else:
        top_tag, children = "msubsup", (mname_tag, sub_tag, sup_tag)
    return (top_tag, bool(bold), children)


# --- the oracle: the patched real printer -----------------------------------
def observe(node):
    """Recover (top_tag, top_bold, child_tags) from a rendered minidom node."""
    bold = bool(node.attributes and node.hasAttribute("mathvariant")
                and node.getAttribute("mathvariant") == "bold")
    child_tags = tuple(
        ("#text" if c.nodeType == c.TEXT_NODE else c.nodeName)
        for c in node.childNodes
    )
    return (node.nodeName, bold, child_tags)


# Name fragments that exercise the four script combinations.  split_super_sub
# reads `^`/`__` as superscripts and `_` as subscripts.
def make_name(rng, kind):
    base = rng.choice(["x", "y", "z", "a", "b", "alpha", "beta", "Q", "w"])
    # script pieces (1 or 2) drawn from a small alphabet
    def pieces():
        n = rng.randint(1, 2)
        return [rng.choice(["1", "2", "3", "a", "b", "i", "n"]) for _ in range(n)]
    if kind == "none":
        return base, (False, False)
    if kind == "sub":
        return base + "_" + "_".join(pieces()), (True, False)
    if kind == "sup":
        return base + "^" + "^".join(pieces()), (False, True)
    # both
    sups = pieces()
    subs = pieces()
    return base + "^" + "^".join(sups) + "_" + "_".join(subs), (True, True)


def main():
    try:
        from sympy import Symbol
        from sympy.printing.mathml import MathMLPresentationPrinter
    except Exception as e:  # pragma: no cover - import guard
        print("G-CONF ERROR: cannot import sympy: %r" % (e,))
        return 2

    mpp = MathMLPresentationPrinter()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # canonical boundary cases first (plain + bold across every combination)
    canonical = [
        ("x", "none"), ("x2", "sub"), ("x^2", "sup"), ("x^3_2", "both"),
        ("x_2_a", "sub"), ("x^2^a", "sup"), ("x__3_2", "both"),
    ]
    cases = [(nm, kind, False) for nm, kind in canonical]
    cases += [(nm, kind, True) for nm, kind in canonical]

    # fuzz
    for _ in range(N_FUZZ):
        kind = rng.choice(["none", "sub", "sup", "both"])
        name, _flags = make_name(rng, kind)
        bold = rng.random() < 0.5
        cases.append((name, kind, bold))

    for name, kind, bold in cases:
        style = "bold" if bold else "plain"
        node = mpp._print_Symbol(Symbol(name), style=style)
        top_tag, top_bold, child_tags = observe(node)
        count += 1

        # Recover the script-node presence + the actual child tags from the real
        # render to feed the shadow (they are inputs, not under test).  For a
        # scripted top node the children are (mname=mi, [sub], [sup]) in
        # post-image order; for the bare case it is the name text.
        if top_tag == "mi" and child_tags == ("#text",):
            sub_tag = sup_tag = None
        elif top_tag == "msub":
            sub_tag, sup_tag = child_tags[1], None
        elif top_tag == "msup":
            sub_tag, sup_tag = None, child_tags[1]
        elif top_tag == "msubsup":
            sub_tag, sup_tag = child_tags[1], child_tags[2]
        else:
            # an <mi> wrapping a container (the pre-patch shape) or anything
            # unexpected: recover presence from the wrapped child so the shadow
            # is fed honest inputs; the top-tag comparison will then expose the
            # disagreement (which is the point).
            inner = child_tags[0] if child_tags else None
            if inner == "msub":
                sub_tag, sup_tag = "mi", None
            elif inner == "msup":
                sub_tag, sup_tag = None, "mi"
            elif inner == "msubsup":
                sub_tag, sup_tag = "mi", "mi"
            else:
                sub_tag = sup_tag = None

        shadow = shadow_build(True, sub_tag, sup_tag, bold)
        oracle = (top_tag, top_bold, child_tags)
        if shadow != oracle:
            disagreements.append((name, style, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nm, st, sh, orc in disagreements:
            print("  name=%r style=%s shadow=%r oracle=%r" % (nm, st, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildSymbolNode agrees with the patched "
          "printer's node assembly on %d symbol renders (14 canonical + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
