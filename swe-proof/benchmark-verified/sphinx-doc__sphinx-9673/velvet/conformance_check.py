#!/usr/bin/env python3
r"""G-CONF differential conformance check for sphinx-doc__sphinx-9673 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. The whole
impl region is pure R/I (no A-tagged callee — mapping.md §3), so conf_skip=false.

The modeled observable is the SEQUENCE OF FIELDS APPENDED to an info-field list
by `augment_descriptions_with_types`, as a function of (a) the leading-token
classification of the existing field names and (b) the recorded annotation table
(mapping.md §2):

  * SHADOW — `buildFields` / `augmentTypeFields` transliterated to Python over
             the real repo types:
               existing field names ↔ `fields : List (List Tok)`  (each name
                   split on runs of spaces, each token a `List Char`)
               annotation table     ↔ `annotations : List (Tok × Tok)`
             It classifies every field by its leading token (a result-description
             field recognized under EITHER 'return' OR 'returns'), then emits the
             parameter `type` fields and the optional trailing `rtype` field.
  * ORACLE — `patch.diff`'s behaviour: the REAL patched
             `sphinx.ext.autodoc.typehints.augment_descriptions_with_types`,
             observed through the fields it APPENDS to a freshly-built docutils
             `field_list` node (everything beyond the pre-existing children).

For each fuzzed (field-name list, annotation table):

      shadow_emit(field_names, annotations)  ==  oracle_emit(field_names, annotations)

where each emitted field is normalized to its rendered ('name', 'body') pair.
This isolates exactly the classification + back-fill logic the patch changed: the
discriminating case is a result documented under the plural 'returns' spelling,
where the pre-patch code emitted no rtype field and the gold now does. Exit 0 iff
zero disagreements. stdlib + docutils + sphinx only. Seed pinned (mapping.md §4).
"""
import random
import re
import sys

SEED = 9673
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# Bijection-domain canonicalization (mapping.md §2).
# ---------------------------------------------------------------------------
def canon_annotations(annotations):
    """Project a fuzzed (key, type-string) pair-list onto the bijection domain.

    mapping.md §2 declares `annotations : List (Tok × Tok)` to correspond to a
    Python `Dict[str, str]` (insertion-ordered, UNIQUE keys). A pair-list with a
    repeated key is NOT in the image of that dict↔assoc-list bijection — no real
    `dict` ever serializes to it (the oracle's `ann = {}` build collapses repeats
    to one key with the last value). We therefore canonicalize every fuzzed table
    to its dict form (first-occurrence key order, last value) before feeding BOTH
    legs, so the differential test stays inside the refinement's declared domain.
    On unique-key tables (the only ones the bijection claims) this is the identity.
    """
    d = {}
    for (k, v) in annotations:
        d[k] = v
    return list(d.items())


# ---------------------------------------------------------------------------
# SHADOW — Python transliteration of buildFields (R/I legs of refinement.md).
# ---------------------------------------------------------------------------
def shadow_emit(field_names, annotations):
    """Return the list of ('name','body') fields buildFields appends.

    field_names : list[str]            (existing info-field names)
    annotations : list[tuple[str,str]] (ordered (key, type-string) table)
    """
    has_desc = []   # list, membership-only (Sets.hasDesc)
    has_type = []   # list, membership-only (Sets.hasType)

    def add_desc(t):
        has_desc.append(t)

    def add_type(t):
        has_type.append(t)

    # classifyFields: classify every existing field by its name's leading token.
    for fname in field_names:
        parts = re.split(' +', fname)
        p0 = parts[0]
        rest = parts[1:]
        if p0 == 'param':
            if len(rest) == 0:
                pass
            elif len(rest) == 1:
                add_desc(rest[0])
            else:
                nm = ' '.join(rest[1:])
                add_desc(nm)
                add_type(nm)
        elif p0 == 'type':
            add_type(' '.join(rest))
        elif p0 == 'return' or p0 == 'returns':       # the two-spelling synonym
            add_desc('return')
        elif p0 == 'rtype':
            add_type('return')
        # else: ignored

    out = []
    # emitStep fold: parameter type fields, in annotation order.
    for (name, body) in annotations:
        if name == 'return' or name == 'returns':
            continue
        if name in has_desc and name not in has_type:
            out.append(('type ' + name, body))
    # rtypeField: trailing result-type field.
    if any(k == 'return' for (k, _) in annotations) \
            and ('return' in has_desc) and ('return' not in has_type):
        ret_body = next(v for (k, v) in annotations if k == 'return')
        out.append(('rtype', ret_body))
    return out


# ---------------------------------------------------------------------------
# ORACLE — real patched augment_descriptions_with_types via a docutils node.
# ---------------------------------------------------------------------------
def oracle_emit(field_names, annotations):
    from docutils import nodes
    from sphinx.ext.autodoc.typehints import augment_descriptions_with_types

    node = nodes.field_list()
    for fname in field_names:
        f = nodes.field()
        f += nodes.field_name('', fname)
        f += nodes.field_body('', nodes.paragraph('', 'desc'))
        node += f
    n_before = len(node)

    ann = {}            # dict preserves insertion order (3.7+)
    for (k, v) in annotations:
        ann[k] = v

    augment_descriptions_with_types(node, ann)

    out = []
    for f in list(node)[n_before:]:
        name = f[0].astext()
        body = f[1].astext()
        out.append((name, body))
    return out


# ---------------------------------------------------------------------------
# Fuzzers.
# ---------------------------------------------------------------------------
NAMES = ['x', 'y', 'arg', 'value', 'a', 'b', 'foo_bar', 'n']
TYPES = ['int', 'str', 'float', 'bool', 'Tuple[int, int]', 'List[str]', 'None']


def fuzz_field_names(rng):
    """A small list of existing info-field names of varied shapes."""
    k = rng.randint(0, 5)
    out = []
    for _ in range(k):
        kind = rng.random()
        if kind < 0.25:
            nm = rng.choice(NAMES)
            out.append('param ' + nm if rng.random() < 0.7 else 'param')
        elif kind < 0.40:
            nm = rng.choice(NAMES)
            ty = rng.choice(NAMES)
            out.append('param %s %s' % (nm, ty))   # inline-typed param
        elif kind < 0.55:
            out.append('type ' + rng.choice(NAMES))
        elif kind < 0.75:
            # the discriminating axis: short vs plural return-description field
            out.append('returns' if rng.random() < 0.5 else 'return')
        elif kind < 0.88:
            out.append('rtype')
        else:
            out.append(rng.choice(['arg ' + rng.choice(NAMES), 'kwarg', 'raises ValueError', '']))
    return out


def fuzz_annotations(rng):
    """An ordered (key, type-string) annotation table."""
    k = rng.randint(0, 4)
    out = []
    for _ in range(k):
        if rng.random() < 0.3:
            out.append(('return', rng.choice(TYPES)))
        else:
            out.append((rng.choice(NAMES), rng.choice(TYPES)))
    return out


# Boundary / F2P-shaped cases (plan §4.1 step 4): the documented-return matrix.
BOUNDARY = [
    # (field_names, annotations)
    ([], []),
    (['return'], [('return', 'int')]),                       # short, documented
    (['returns'], [('return', 'int')]),                      # PLURAL, documented (F2P)
    (['returns'], []),                                        # plural, no annotation
    (['return', 'rtype'], [('return', 'int')]),              # already typed -> no rtype
    (['returns', 'rtype'], [('return', 'int')]),             # plural + typed
    (['param x'], [('x', 'int')]),                            # param backfill
    (['param x', 'returns'], [('x', 'int'), ('return', 'str')]),
    (['param x y'], [('x y', 'int')]),                        # inline-typed param -> no backfill
    (['type x', 'param x'], [('x', 'int')]),                  # described+typed -> no backfill
    (['returns'], [('returns', 'int')]),                      # annotation key never 'returns' in repo, but symmetry
    (['return', 'returns'], [('return', 'int')]),            # both spellings present
]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(BOUNDARY)
    for _ in range(N_FUZZ):
        cases.append((fuzz_field_names(rng), fuzz_annotations(rng)))

    for field_names, annotations in cases:
        count += 1
        # Stay inside the dict↔assoc-list bijection domain (mapping.md §2):
        # collapse any repeated annotation key exactly as a real Python dict would.
        annotations = canon_annotations(annotations)
        try:
            shadow = shadow_emit(field_names, annotations)
            oracle = oracle_emit(field_names, annotations)
        except Exception as e:                                # noqa: BLE001
            disagreements.append((field_names, annotations, 'EXC:%r' % e, None))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((field_names, annotations, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d cases:" % (len(disagreements), count))
        for fn, an, sh, orc in disagreements:
            print("  fields=%r ann=%r shadow=%r oracle=%r" % (fn, an, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of augmentTypeFields agrees with patch.diff "
          "behaviour (real augment_descriptions_with_types) on %d cases "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
