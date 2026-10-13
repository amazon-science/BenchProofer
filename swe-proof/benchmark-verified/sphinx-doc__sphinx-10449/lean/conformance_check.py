#!/usr/bin/env python3
"""G-CONF for sphinx-doc__sphinx-10449.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_render_typehint_fields` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`sphinx.ext.autodoc.typehints.modify_field_list` over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

`modify_field_list(node, annotations, suppress_rtype=False)` scans the existing
docutils fields of `node`, then APPENDS `type`/`param` fields for each annotation
and a final `rtype` field for the return annotation — unless `suppress_rtype` is
set and the return annotation is 'None'.

We observe a docutils `nodes.field` only through its field-name text
(`field[0].astext()`) and its body paragraph text. We build a real
`nodes.field_list` from a fuzzed list of (name, body) pairs, run the REAL
`modify_field_list` on it, and read the resulting field list back out as
(name, body) records. The shadow computes the same record list directly.

Type bijection (mapping.md):
  existing : List DocField        <-> fields present in `node` before the call,
                                       each (field[0].astext(), field[1].astext())
  annotations : List(name, ann)   <-> the annotations OrderedDict items, in order
  suppressTrivialReturn : Bool    <-> the suppress_rtype parameter
  result : List DocField          <-> fields in `node` after the call, in order

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + sphinx/docutils.
"""
import json
import random
import re
import sys

from docutils import nodes

from sphinx.ext.autodoc.typehints import modify_field_list


# --- shadow: R/I transliteration of implementation_render_typehint_fields -----
def tokenize(s):
    return [t for t in re.split(' +', s) if t != '']


def declares_type_field(name, nm):
    parts = tokenize(name)
    if parts[:1] == ['type']:
        rest = parts[1:]
        return rest != [] and ' '.join(rest) == nm
    if parts[:1] == ['param'] and len(parts) >= 3:
        return ' '.join(parts[2:]) == nm
    return False


def declares_param_field(name, nm):
    parts = tokenize(name)
    if parts[:1] == ['param']:
        if len(parts) == 2:
            return parts[1] == nm
        if len(parts) >= 3:
            return ' '.join(parts[2:]) == nm
    return False


def is_return_field(name):
    parts = tokenize(name)
    if parts[:1] == ['rtype']:
        return True
    # A field that declares a type for, or the parameter named, the return
    # position also records the return name in the scan's arguments dict.
    return declares_type_field(name, 'return') or declares_param_field(name, 'return')


def shadow(existing, annotations, suppress):
    """existing: list[(name,body)], annotations: list[(name,ann)] (unique keys)."""
    declares_type = lambda nm: any(declares_type_field(n, nm) for n, _ in existing)
    declares_param = lambda nm: any(declares_param_field(n, nm) for n, _ in existing)
    has_return = any(is_return_field(n) for n, _ in existing)

    fields = list(existing)
    for name, ann in annotations:
        if name == 'return':
            continue
        if not declares_type(name):
            fields.append(('type ' + name, ann))
        if not declares_param(name):
            fields.append(('param ' + name, ''))

    ret = None
    for name, ann in annotations:
        if name == 'return':
            ret = ann
            break
    if ret is not None:
        if not has_return:
            if ret == 'None' and suppress:
                return fields
            fields.append(('rtype', ret))
    return fields


# --- real: drive modify_field_list on a built field_list ----------------------
def build_field_list(existing):
    fl = nodes.field_list()
    for name, body in existing:
        field = nodes.field()
        field += nodes.field_name('', name)
        field += nodes.field_body('', nodes.paragraph('', body))
        fl += field
    return fl


def read_field_list(fl):
    out = []
    for field in fl:
        name = field[0].astext()
        body = field[1].astext() if len(field) > 1 else ''
        out.append((name, body))
    return out


def real(existing, annotations, suppress):
    fl = build_field_list(existing)
    od = {}
    for name, ann in annotations:
        od[name] = ann
    modify_field_list(fl, od, suppress_rtype=suppress)
    return read_field_list(fl)


# --- fuzz ---------------------------------------------------------------------
NAMES = ['x', 'y', 'value', 'foo', 'bar', 'self']
TYPES = ['int', 'str', 'None', 'bool', 'float', 'List[int]']


def rand_existing(rng):
    out = []
    k = rng.randint(0, 4)
    for _ in range(k):
        kind = rng.choice(['param', 'type', 'param2', 'rtype', 'other'])
        # 'return' as the declared name exercises the scan's recording of the
        # return position via type/param fields (arguments['return']).
        nm = rng.choice(NAMES + ['return'])
        if kind == 'param':
            out.append(('param ' + nm, ''))
        elif kind == 'type':
            out.append(('type ' + nm, rng.choice(TYPES)))
        elif kind == 'param2':
            out.append(('param ' + rng.choice(NAMES) + ' ' + nm, ''))
        elif kind == 'rtype':
            out.append(('rtype', rng.choice(TYPES)))
        else:
            out.append((rng.choice(['returns', 'raises ' + nm]), ''))
    return out


def rand_annotations(rng):
    items = []
    used = set()
    k = rng.randint(0, 4)
    for _ in range(k):
        nm = rng.choice(NAMES)
        if nm in used:
            continue
        used.add(nm)
        items.append((nm, rng.choice(TYPES)))
    if rng.random() < 0.7:
        items.append(('return', rng.choice(TYPES)))
    return items


def main():
    rng = random.Random(10449)
    N = 100000
    for i in range(N):
        existing = rand_existing(rng)
        annotations = rand_annotations(rng)
        suppress = rng.random() < 0.5
        try:
            r_real = real([(n, b) for n, b in existing], annotations, suppress)
        except Exception as e:  # noqa
            print(json.dumps({"status": "error", "i": i, "exc": repr(e),
                              "existing": existing, "annotations": annotations,
                              "suppress": suppress}))
            sys.exit(1)
        r_shadow = shadow(existing, annotations, suppress)
        if r_real != r_shadow:
            print(json.dumps({"status": "disagree", "i": i,
                              "existing": existing, "annotations": annotations,
                              "suppress": suppress,
                              "real": r_real, "shadow": r_shadow}))
            sys.exit(1)
    print(json.dumps({"status": "ok", "n": N, "seed": 10449}))
    sys.exit(0)


if __name__ == '__main__':
    main()
