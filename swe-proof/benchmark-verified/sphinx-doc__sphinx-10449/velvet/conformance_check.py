#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10449 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions transliterated
              to Python: `returnTypeEntry` / `returnTypeEntryForKind` over the
              four observations the decision reads — whether the object has a
              return annotation (`'return' in annotations`), whether the
              description already declares a return type (`'return' in
              arguments`), the rendered annotation text (`annotations['return']`)
              and (for the dispatcher) the object kind (`objtype`). The bundle
              has NO axioms (mapping.md §3), so the whole shadow is in scope.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `sphinx.ext.autodoc.typehints.modify_field_list`, driven on a
              synthetic docutils `field_list`. We observe the trailing
              return-type entry: whether an `rtype` field is appended, and the
              text it carries. The patched `merge_typehints` "all" arm is exactly
              `modify_field_list(fl, ann, suppress_rtype=(objtype == 'class'))`,
              so the dispatcher (site B) is exercised by calling the real
              `modify_field_list` with that flag.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the prebuilt
SWE-Bench instance image, patch applied), stdlib + the in-image docutils/Sphinx
only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 10449
N_FUZZ = 100_000


# --- ORACLE setup: the REAL gold-patched modify_field_list -------------------

def _load_real():
    """Import the gold-patched modify_field_list + docutils nodes. The harness
    applies patch.diff before this runs."""
    from sphinx.ext.autodoc.typehints import modify_field_list
    from docutils import nodes
    return modify_field_list, nodes


def _make_field(nodes, name_text, body_text):
    field = nodes.field()
    field += nodes.field_name('', name_text)
    field += nodes.field_body('', nodes.paragraph('', body_text))
    return field


def oracle_entry(modify_field_list, nodes, kind, has_return_anno,
                 return_in_args, return_annotation):
    """Run the REAL patched modify_field_list with suppress_rtype selected by the
    kind (exactly the patched merge_typehints "all" arm), on a synthetic
    field_list, and read back the appended return-type entry.

    Returns the carried rtype text (str) if an entry was appended, else None."""
    node = nodes.field_list()
    # `arguments['return']` becomes set iff an rtype field is already present, so
    # to model `return_in_args` we seed the node with a pre-existing rtype field.
    if return_in_args:
        node += _make_field(nodes, 'rtype', 'preexisting')

    # annotations carries 'return' iff the object has a return annotation. We use
    # ONLY the 'return' key so the unchanged per-parameter loop appends nothing.
    annotations = {}
    if has_return_anno:
        annotations['return'] = return_annotation

    initial = list(node.children)
    suppress_rtype = (kind == 'class')
    modify_field_list(node, annotations, suppress_rtype=suppress_rtype)

    # the appended entry (if any) is a field beyond the initial children whose
    # field_name is 'rtype'.
    for child in node.children[len(initial):]:
        if child[0].astext() == 'rtype':
            return child[1].astext()
    return None


# --- SHADOW: Solution.lean returnTypeEntry / returnTypeEntryForKind -----------

def shadow_entry(kind, has_return_anno, return_in_args, return_annotation):
    """returnTypeEntryForKind transliterated: a class kind suppresses a `None`
    return type; the entry is otherwise the annotation text, appended only when
    the object has a return annotation not already declared. Returns the carried
    text (str) or None (no entry)."""
    omit_none = (kind == 'class')
    if has_return_anno and not return_in_args:
        if return_annotation == 'None' and omit_none:
            return None
        return return_annotation
    return None


def main():
    rng = random.Random(SEED)
    try:
        modify_field_list, nodes = _load_real()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched modify_field_list: %r" % e)
        return 2

    kinds = ['class', 'function', 'method', 'data', 'attribute', 'exception']
    annos = ['None', 'int', 'str', 'float', 'bool', 'MyClass',
             'Optional[int]', 'None ', 'none', 'NoneType', '']

    disagreements = []
    count = 0

    def run(kind, hra, ria, ann):
        nonlocal count
        count += 1
        shadow = shadow_entry(kind, hra, ria, ann)
        oracle = oracle_entry(modify_field_list, nodes, kind, hra, ria, ann)
        if shadow != oracle:
            disagreements.append((kind, hra, ria, ann, shadow, oracle))

    # --- boundary cases: the full decision matrix (the F2P case + neighbours) -
    # F2P: class object, return annotation 'None', not already declared -> omit.
    for kind in kinds:
        for hra in (True, False):
            for ria in (True, False):
                for ann in ('None', 'int', ''):
                    run(kind, hra, ria, ann)

    # --- randomized fuzz ------------------------------------------------------
    for _ in range(N_FUZZ):
        kind = rng.choice(kinds)
        hra = rng.random() < 0.7
        ria = rng.random() < 0.4
        ann = rng.choice(annos)
        run(kind, hra, ria, ann)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for kind, hra, ria, ann, sh, orc in disagreements:
            print("  kind=%r has_return_anno=%r return_in_args=%r annotation=%r "
                  "shadow=%r oracle=%r" % (kind, hra, ria, ann, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of emitReturnTypeEntry/emitReturnTypeForKind "
          "agrees with the real gold-patched modify_field_list (suppress_rtype "
          "selected per objtype, the patched merge_typehints 'all' arm) on %d "
          "inputs (boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
