#!/usr/bin/env python3
"""G-CONF differential conformance for sphinx-doc__sphinx-7454 (plan §4.1).

Refutes the R/I refinement leg: the modeled dispatch `desiredKind` (and the
per-token reference record built by `referenceForName`) against `patch.diff`'s
behaviour, over the inputs that reach the modeled scope.

ORACLE CHOICE — drive the REAL patched code.
  The modeled function is the per-token cross-reference builder nested inside
  `sphinx.domains.python._parse_annotation`. We cannot import the nested
  `make_xref` directly, but for a single-name annotation the outer parser emits
  exactly ONE `pending_xref` node, and that node IS the builder's output. So the
  ORACLE is the real **patched** `_parse_annotation(name)` (the harness applies
  patch.diff before this runs): we parse a single name, locate the lone
  `pending_xref`, and read back its observable fields
  (`reftype`/`refdomain`/`reftarget`/shown text). The SHADOW is the modeled
  dispatch from Solution.lean (`referenceForName`/`desiredKind`), transliterated.

  Inputs are restricted to names that reach the builder as a single token and
  yield exactly one xref: the `None` singleton, ordinary type names (`int`,
  `str`, dotted names, user identifiers), plus seeded identifier fuzz. (Subscript
  forms like `List[int]` emit several xrefs and punctuation; they are unions of
  single-token cases and add no new behaviour for the modeled per-token map, so
  they are out of the modeled scope by construction.)

  They must agree on every input. Exit 0 iff zero disagreements. stdlib only
  (plus sphinx/docutils, already installed in the instance image).
"""
import random
import sys

SEED = 7454
N_FUZZ = 100_000

CLASS = "class"   # RefKind.classRef  <-> reftype 'class'
OBJ = "obj"       # RefKind.valueRef  <-> reftype 'obj'


# --- the R/I shadow: Solution.lean desiredKind / referenceForName ------------
def shadow(name):
    """The modeled per-token reference, transliterated from Solution.lean.

    referenceForName returns a record (kind, domain, target, label); desiredKind
    selects the kind. We compare the same four observable fields the F2P test
    reads off the node."""
    kind = OBJ if name == "None" else CLASS          # desiredKind
    return {
        "reftype": kind,
        "refdomain": "py",
        "reftarget": name,
        "label": name,
    }


# --- the ORACLE: patch.diff behaviour via the real patched parser ------------
def oracle(name):
    """Drive the real patched `_parse_annotation(name)` and read back the lone
    pending_xref's observable fields."""
    from sphinx.domains.python import _parse_annotation
    from sphinx.addnodes import pending_xref

    result = _parse_annotation(name)
    # collect every pending_xref produced
    xrefs = []
    for node in result:
        if isinstance(node, pending_xref):
            xrefs.append(node)
        else:
            # walk children (defensive; single names do not nest here)
            try:
                xrefs.extend(node.traverse(pending_xref))
            except Exception:
                pass
    if len(xrefs) != 1:
        return {"__shape__": "expected 1 xref, got %d" % len(xrefs)}
    node = xrefs[0]
    return {
        "reftype": node["reftype"],
        "refdomain": node["refdomain"],
        "reftarget": node["reftarget"],
        "label": node.astext(),
    }


def fuzz_names(n, rng):
    # boundary / structured cases first
    yield "None"            # the singleton — the discriminating input
    yield "int"
    yield "str"
    yield "bool"
    yield "float"
    yield "bytes"
    yield "object"
    yield "List"
    yield "Dict"
    yield "Any"
    yield "MyClass"
    yield "_private"
    yield "a.b.c"           # dotted name (Attribute) -> single xref, text 'a.b.c'
    yield "package.Module"
    yield "T"
    yield "None_"           # near-miss: NOT the singleton
    yield "NoneType"        # near-miss
    yield "none"            # near-miss (case)
    # randomized identifier fuzz
    first = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    rest = first + "0123456789"
    for _ in range(n):
        k = rng.randint(1, 12)
        name = rng.choice(first) + "".join(rng.choice(rest) for _ in range(k - 1))
        yield name


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    saw_none = False
    for name in fuzz_names(N_FUZZ, rng):
        count += 1
        if name == "None":
            saw_none = True
        s = shadow(name)
        o = oracle(name)
        if s != o:
            disagreements.append((name, s, o))
            if len(disagreements) >= 5:
                break
    if not saw_none:
        print("G-CONF FAIL: the discriminating input 'None' was never exercised")
        return 1
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, s, o in disagreements:
            print("  name=%r shadow=%r oracle=%r" % (name, s, o))
        return 1
    print("G-CONF OK: R/I shadow of referenceForName agrees with patch.diff "
          "behaviour (real _parse_annotation) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
