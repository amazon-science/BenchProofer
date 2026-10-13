#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8638 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`renderFieldEntry`
              routed through the deep model `crossRefOrText`) transliterated to
              Python over the real repo types. There are NO A-tagged callees in
              the impl region (no axioms), so the shadow is pure R/I. The impl
              hardcodes the post-patch role for the variable NAME (`none`) and the
              unchanged role for the TYPE (`'class'`).
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched Sphinx renders the one
              entry of the `'variable'` info field by calling the actual
              `PyTypedField('variable', …)`'s `make_xrefs` with its (now patched)
              `rolename` for the NAME and its `typerolename` for the TYPE — i.e.
              exactly the `sphinx/util/docfields.py` `handle_item` path. The
              field config is read live from the repo, so after patch.diff is
              applied the NAME role is `None`.

Observable of one rendered entry, per the mapping.md §2 bijection:
  - the NAME node: ('xref', reftype, reftarget) if it is a pending_xref, else
    ('text', text)  ↔  RefNode.xref / RefNode.text;
  - the TYPE node: likewise.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch.diff applied),
stdlib + docutils + sphinx (the repo under test) only. The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import string
import sys

SEED = 8638
N_FUZZ = 100_000

from sphinx.domains.python import PyObject
from sphinx import addnodes


class _FakeDomain:
    def process_field_xref(self, refnode):  # no-op: we only inspect node shape
        pass


class _FakeEnv:
    def __init__(self):
        self.ref_context = {}

    def get_domain(self, domain):
        return _FakeDomain()


def _variable_field():
    for f in PyObject.doc_field_types:
        if getattr(f, "name", None) == "variable":
            return f
    raise RuntimeError("no 'variable' doc field on PyObject")


def _describe(node):
    """Map a rendered inline node to the mapping.md §2 observable."""
    if isinstance(node, addnodes.pending_xref):
        return ("xref", node.get("reftype"), node.get("reftarget"))
    return ("text", node.astext())


# --- the R/I shadow: Solution.lean crossRefOrText / renderFieldEntry ----------
def shadow_crossref_or_text(refrole, target):
    """crossRefOrText (pure region) transliterated. refrole is None or a str
    (an empty str counts as no role, per Field.make_xref's `if not rolename`)."""
    if refrole is None or refrole == "":
        return ("text", target)
    return ("xref", refrole, target)


def shadow_entry(name, typ):
    """renderFieldEntry's impl: NAME role is None (post-patch), TYPE role is the
    unchanged 'class'."""
    return (shadow_crossref_or_text(None, name),
            shadow_crossref_or_text("class", typ))


# --- the oracle: patch.diff's real rendering ----------------------------------
def oracle_entry(vf, env, name, typ):
    """Render the one entry of the real 'variable' field exactly as
    TypedField.make_field's handle_item does: NAME via make_xrefs(self.rolename),
    TYPE via make_xrefs(self.typerolename). Read the live (patched) config."""
    name_nodes = vf.make_xrefs(vf.rolename, "py", name,
                               addnodes.literal_strong, env=env)
    type_nodes = vf.make_xrefs(vf.typerolename, "py", typ,
                               addnodes.literal_emphasis, env=env)
    return (_describe(name_nodes[0]), _describe(type_nodes[0]))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary_names = ["attr", "x", "limit", "somename", "value", "a"]
    boundary_types = ["int", "str", "Foo", "bool", "MyClass", "float"]
    for nm in boundary_names:
        for ty in boundary_types:
            yield (nm, ty)
    # Identifier-ish strings so make_xrefs yields a single node (matching the
    # single-node spec model). This is the spec's EXPLICIT modeled domain
    # (Solution.lean `require` clauses: nonempty, isIdentChar-only, typ /=
    # "None"). Excludes the make_xrefs delimiters [](),/or, the leading-'.'/'~'
    # prefixes that PyXrefMixin.make_xref strips, and the literal type "None"
    # that PyTypedField.make_xref rewrites to the 'obj' role (all unchanged
    # behaviour orthogonal to the patched NAME role); '_' is safe.
    alphabet = string.ascii_letters + string.digits + "_"
    for _ in range(n):
        kn = rng.randint(1, 16)
        kt = rng.randint(1, 16)
        nm = "".join(rng.choice(alphabet) for _ in range(kn))
        ty = "".join(rng.choice(alphabet) for _ in range(kt))
        if ty == "None":  # outside the spec domain (`require typ != "None"`)
            ty = "None_"
        yield (nm, ty)


def main():
    rng = random.Random(SEED)
    vf = _variable_field()
    env = _FakeEnv()
    disagreements = []
    count = 0
    for name, typ in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_entry(name, typ)
        oracle = oracle_entry(vf, env, name, typ)
        if shadow != oracle:
            disagreements.append((name, typ, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for nm, ty, sh, orc in disagreements:
            print("  name=%r type=%r shadow=%r oracle=%r" % (nm, ty, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderFieldEntry agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
