#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8638.

Validates the ONE deep-model reference of the bundle (no consumed axioms):

  (A-reference) the deep model `crossRefOrText` (Solution.lean pure region) ==
      the real UNCHANGED helper `sphinx.util.docfields.Field.make_xref`. The
      rendering rule the patch toggles is *which role is passed* for the
      variable-field NAME; `make_xref` itself is unchanged. The model claims:
        - a falsy/empty role  -> a plain inline text node (no pending_xref);
        - a truthy role `r`   -> a `pending_xref` of reftype=r, reftarget=target.
      G-AX drives the REAL `Field.make_xref` over boundary roles
      (None, '', 'obj', 'class', 'data', 'func', …) and fuzzed role/target
      strings and asserts the node shape matches `crossRefOrText`.

It also asserts the structural invariants the refinement relies on at
base_commit (G-AX runs WITHOUT the gold patch applied):
  - the 'variable' doc field is a PyTypedField whose `typerolename == 'class'`
    (UNCHANGED by the patch — the TYPE stays a class cross-reference);
  - the patch's effect is localized to the NAME role: the only thing the gold
    hunk changes is `rolename`, which `make_xref` consumes via `if not rolename`.
  (We deliberately do NOT assert the NAME `rolename` value here: at base_commit
  it is still the pre-patch 'obj'; the post-patch None is checked by G-CONF,
  which runs with the gold patch applied.)

Imports docutils + sphinx (the repo under test) only. Exit 0 iff sound.
"""
import random
import string
import sys

from sphinx.util.docfields import Field, TypedField
from sphinx.domains.python import PyObject
from sphinx import addnodes


# --- the deep model crossRefOrText (kept in lock-step with Solution.lean) -----
def cross_ref_or_text(refrole, target):
    """Returns ('text', target) or ('xref', refrole, target)."""
    if refrole is None or refrole == "":
        return ("text", target)
    return ("xref", refrole, target)


def _describe(node):
    """Map a real make_xref node to the mapping.md §2 observable."""
    if isinstance(node, addnodes.pending_xref):
        return ("xref", node.get("reftype"), node.get("reftarget"))
    return ("text", node.astext())


def check_make_xref_reference(role, target):
    """Assert crossRefOrText(role, target) == shape of the REAL Field.make_xref."""
    f = Field("dummy")
    # env=None is the path TypedField uses when no env is threaded; make_xref
    # only consults env for the truthy-role branch's process_field_xref, which
    # we bypass by passing env=None (the node is still constructed).
    node = f.make_xref(role, "py", target, env=None)
    observed = _describe(node)
    expected = cross_ref_or_text(role, target)
    assert observed == expected, (
        "crossRefOrText deep model unsound on role=%r target=%r: "
        "real make_xref gave %r, deep model gives %r"
        % (role, target, observed, expected))


def main():
    # --- structural invariant: the unchanged TYPE role -----------------------
    vf = None
    for fld in PyObject.doc_field_types:
        if getattr(fld, "name", None) == "variable":
            vf = fld
            break
    assert vf is not None, "no 'variable' doc field on PyObject"
    assert isinstance(vf, TypedField), \
        "'variable' field is not a (Py)TypedField: %r" % type(vf)
    assert vf.typerolename == "class", (
        "'variable' field typerolename changed from 'class' to %r — the TYPE "
        "cross-reference must be preserved by the patch" % vf.typerolename)

    # --- A-reference: crossRefOrText == real Field.make_xref node shape -------
    boundary_roles = [None, "", "obj", "class", "data", "func", "meth", "attr"]
    boundary_targets = ["attr", "int", "Foo", "x", "a.b.C", "limit", "value"]
    for role in boundary_roles:
        for target in boundary_targets:
            check_make_xref_reference(role, target)

    # randomized fuzz over role/target strings
    rng = random.Random(8638)
    role_alphabet = string.ascii_lowercase
    target_alphabet = string.ascii_letters + string.digits + "._"
    n_checks = 0
    for _ in range(20000):
        # mix in the empty/None role frequently to exercise the text branch
        choice = rng.randint(0, 3)
        if choice == 0:
            role = None
        elif choice == 1:
            role = ""
        else:
            role = "".join(rng.choice(role_alphabet)
                           for _ in range(rng.randint(1, 8)))
        target = "".join(rng.choice(target_alphabet)
                         for _ in range(rng.randint(1, 16)))
        check_make_xref_reference(role, target)
        n_checks += 1

    print("G-AX OK: crossRefOrText deep model (== Field.make_xref) sound on "
          "%d boundary + %d fuzz (role,target) pairs; 'variable' field "
          "typerolename=='class' preserved."
          % (len(boundary_roles) * len(boundary_targets), n_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
