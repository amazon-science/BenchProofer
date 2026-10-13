#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9591.

Executes the REAL unchanged callee `sphinx.domains.python._parse_annotation` on
inputs (boundary type names + randomized identifier fuzz, plus a structural
spot-check on compound annotations) and asserts every observation matches the
model in Solution.lean, as restated in model form below.

The one kind-A check:

  (A-reference) the deep model `annotationNodes` (Solution.lean `pure` region)
      == the real `_parse_annotation`, on the spec domain `isBareName`
      (a single, possibly dotted, type name). The model says such a name renders
      to exactly ONE cross-reference node targeting that name:

          annotationNodes(name) == [xref(name)]

      i.e. real `_parse_annotation(name, env)` returns a single node that is a
      `pending_xref` whose reference target == name. This is the discriminator
      the fix turns on: pre-patch the property branch emitted inert text, not a
      cross-reference.

  (carrier faithfulness) on compound annotations (out of the spec domain, but
      checked to confirm the `DocNode` carrier — text / xref / punct — is
      faithful) every emitted node is one of nodes.Text / pending_xref /
      desc_sig_punctuation, and every bare type name becomes a pending_xref.

Imports only the repo module under change plus docutils/sphinx.addnodes (the
same machinery the gold patch's `_parse_annotation` call uses). A minimal `env`
stub supplies the two attributes `type_to_xref` reads
(`config.python_use_unqualified_type_names`, `ref_context`). Exit 0 iff every
obligation holds. Runs in-container (the prebuilt SWE-Bench instance image).
"""
import random
import string
import sys

from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import _parse_annotation


class _Config:
    # The property/attribute path uses the default configuration; with
    # unqualified type names OFF, type_to_xref emits a single nodes.Text child
    # inside the pending_xref (the xref node itself is what we observe).
    python_use_unqualified_type_names = False


class _Env:
    def __init__(self):
        self.config = _Config()
        self.ref_context = {}


def is_bare_name(s):
    """Mirror of Solution.lean `isBareName`: nonempty, starts with letter/'_',
    all chars are identifier chars or '.'."""
    if not s:
        return False
    if not (s[0].isalpha() or s[0] == '_'):
        return False
    return all(c.isalnum() or c == '_' or c == '.' for c in s)


def xref_target(node):
    """The reference target a pending_xref renders/links to. astext() yields the
    visible text, which for these single-name xrefs equals the type name; the
    'reftarget' attribute is the link target. Both equal the name."""
    return node.astext(), node.get('reftarget')


def check_bare_name_reference(name, env):
    """A-reference: real _parse_annotation(name) == annotationNodes model
    == [xref(name)]."""
    result = _parse_annotation(name, env)
    assert len(result) == 1, (
        "annotationNodes deep model unsound on %r: expected 1 node, "
        "_parse_annotation gave %d (%r)" % (name, len(result), result))
    node = result[0]
    assert isinstance(node, addnodes.pending_xref), (
        "annotationNodes deep model unsound on %r: expected a cross-reference "
        "(pending_xref), got %s (%r)" % (name, type(node).__name__, node))
    text, target = xref_target(node)
    assert text == name and target == name, (
        "annotationNodes deep model unsound on %r: xref text=%r target=%r, "
        "expected both == %r" % (name, text, target, name))


def check_compound_carrier(annotation, env):
    """Carrier faithfulness: every node is text / pending_xref /
    desc_sig_punctuation, and at least one bare name became a pending_xref."""
    result = _parse_annotation(annotation, env)
    allowed = (nodes.Text, addnodes.pending_xref, addnodes.desc_sig_punctuation)
    for node in result:
        assert isinstance(node, allowed), (
            "DocNode carrier unfaithful on %r: emitted %s (%r) which is not "
            "text/xref/punct" % (annotation, type(node).__name__, node))
    assert any(isinstance(n, addnodes.pending_xref) for n in result), (
        "DocNode carrier unfaithful on %r: no cross-reference emitted for a "
        "compound annotation containing type names" % (annotation,))


def main():
    env = _Env()

    # --- A-reference: boundary single type names --------------------------
    boundary = [
        "int", "str", "bool", "bytes", "float", "object", "None",
        "Point", "Square", "Rectangle",            # from the issue reproducer
        "Optional", "List", "Dict", "T", "_T", "x",
        "datetime", "pathlib.Path", "a.b.C",       # dotted names
        "MyVeryLongCamelCaseTypeName",
    ]
    for name in boundary:
        assert is_bare_name(name), "test bug: %r is not a bare name" % (name,)
        check_bare_name_reference(name, env)

    # --- A-reference: randomized identifier fuzz --------------------------
    rng = random.Random(9591)
    first = string.ascii_letters + "_"
    rest = string.ascii_letters + string.digits + "_"
    n_fuzz = 20000
    for _ in range(n_fuzz):
        k = rng.randint(0, 18)
        name = rng.choice(first) + "".join(rng.choice(rest) for _ in range(k))
        # optionally make it dotted
        if rng.random() < 0.25:
            k2 = rng.randint(1, 10)
            name = name + "." + rng.choice(first) + "".join(
                rng.choice(rest) for _ in range(k2))
        assert is_bare_name(name), "test bug: %r is not a bare name" % (name,)
        check_bare_name_reference(name, env)

    # --- carrier faithfulness: compound annotations (out of spec domain) --
    for annotation in [
        "Optional[str]", "List[int]", "Dict[str, int]",
        "Tuple[int, str]", "int | None", "Callable[[int], str]",
    ]:
        check_compound_carrier(annotation, env)

    print("G-AX OK: annotationNodes deep model (== _parse_annotation, single "
          "xref per bare name) sound on %d boundary + %d fuzz names; DocNode "
          "carrier faithful on 6 compound annotations"
          % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
