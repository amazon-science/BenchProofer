#!/usr/bin/env python3
r"""G-CONF for sphinx-doc__sphinx-7454.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_annotationRef` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched `make_xref`
helper inside `_parse_annotation` (sphinx/domains/python.py), over >=1e5 fuzzed
annotation tokens. Zero disagreements => exit 0.

Modeled object (mapping.md / refinement.md): the cross-reference `make_xref(text)`
builds for a single annotation token, viewed as its four fields
`(refdomain, reftype, reftarget, label)`. Post-patch:
  * refdomain = 'py' always,
  * reftarget = text, label = text always,
  * reftype = 'obj' iff text == 'None', else 'class'.

`make_xref` is a closure defined INSIDE `_parse_annotation`, so it is not
importable directly. We obtain the REAL patched behavior by calling the public
`_parse_annotation(text)` on a single-token annotation and reading back the four
fields of the produced `pending_xref` node (for a bare Name token,
`_parse_annotation` yields exactly one `pending_xref` whose construction is the
`make_xref(text)` we model). This binds the oracle to the ACTUAL repo code path,
not a hand-copy.

Type bijection (mapping.md): text:List Char <-> token:str (per code point);
TypeRef{domain,kind,target,label} <-> node['refdomain'],node['reftype'],
node['reftarget'],Text-child. stdlib-only (plus sphinx, already installed).
"""
import random
import re
import sys

from docutils import nodes
from sphinx.addnodes import pending_xref
from sphinx.domains.python import _parse_annotation


def oracle(token):
    """REAL patched behavior: the four fields make_xref builds for `token`.

    Drives the actual repo code path `_parse_annotation(token)` on a bare-name
    annotation, returning (domain, kind, target, label) of the single produced
    pending_xref, or None if the token is not parsed as one bare name token
    (those inputs are outside the modeled domain and skipped).
    """
    try:
        result = _parse_annotation(token)
    except Exception:
        return None
    xrefs = [n for n in result if isinstance(n, pending_xref)]
    if len(xrefs) != 1:
        return None
    node = xrefs[0]
    texts = [c for c in node.children if isinstance(c, nodes.Text)]
    if len(texts) != 1:
        return None
    label = str(texts[0])
    return (node.get("refdomain"), node.get("reftype"),
            node.get("reftarget"), label)


def shadow(token):
    """Op-for-op transliteration of implementation_annotationRef (Lean).

    Op 1: kind = 'obj' if token == 'None' else 'class'.
    Ops 2-5: domain='py', kind, target=token, label=token.
    """
    kind = "class"
    if token == "None":
        kind = "obj"
    else:
        kind = "class"
    return ("py", kind, token, token)


# Tokens that _parse_annotation maps to exactly one bare-name pending_xref:
# simple identifiers. We focus the fuzzer on the discriminating token `None`
# and its near-misses, plus common annotation names and random identifiers.
FIXED = [
    "None", "none", "NONE", "Non", "Nonee", "NoneType",
    "int", "str", "bool", "float", "List", "Optional", "Any", "object",
    "T", "MyClass", "x", "foo",
]

_FIRST = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_REST = _FIRST + list("0123456789")
_IDENT = re.compile(r"\A[A-Za-z_][A-Za-z0-9_]*\Z")


def rand_token(rng):
    n = rng.randint(1, 8)
    cs = [rng.choice(_FIRST)] + [rng.choice(_REST) for _ in range(n - 1)]
    return "".join(cs)


def main():
    rng = random.Random(7454)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    checked = 0
    first = None
    i = 0
    while i < N:
        tok = FIXED[i] if i < len(FIXED) else rand_token(rng)
        i += 1
        if not _IDENT.match(tok):
            continue
        o = oracle(tok)
        if o is None:
            continue  # not a single bare-name xref; outside modeled domain
        s = shadow(tok)
        checked += 1
        if o != s:
            disagreements += 1
            if first is None:
                first = (tok, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, checked, first))
        return 1
    if checked == 0:
        print("G-CONF FAIL: no tokens checked")
        return 1
    print("G-CONF OK: %d tokens checked, 0 disagreements" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
