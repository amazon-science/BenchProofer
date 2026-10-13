#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10449 (nagini).

SHADOW: the impl regions of model.py (`suppress_for_kind`,
`has_return_field_in`, `append_return_type`), copied verbatim below with the
contract calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized
as an immutable tuple shim. The @Pure helpers copy over as plain functions.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo functions the model models per mapping.md —
`sphinx.ext.autodoc.typehints.modify_field_list` (its trailing return-type
emit block) and `sphinx.ext.autodoc.typehints.merge_typehints` (the kind
dispatch on the "all" rendering target). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable.

Type bridge (mapping.md section 2):
  * object-kind / return-annotation strings <-> List[int] of Unicode code
    points (chr/ord on each side);
  * the existing docutils field list <-> List[int] of per-field kind codes:
    code 1 = a field whose name's first token is `rtype` (it already declares
    a return type), code 0 = any other field (realized as a rotating pool of
    non-return-typed field names);
  * the appended field <-> Optional[List[int]]: None = no return-type field
    appended, a list = the appended field's rendered body text as code
    points. On the oracle side the observable is extracted by diffing the
    field list's children before/after the call and reading the body text of
    any newly appended `rtype`-named field.

Two differential tiers:
  A. flag-level: shadow `append_return_type(fields, has_return, ann, flag)`
     vs real `modify_field_list(node, annotations, suppress_rtype=flag)`
     called directly, over both flag values;
  B. kind-level (end to end): shadow composition
     `append_return_type(..., suppress_for_kind(kind))` vs real
     `merge_typehints` driven with a minimal app/config/env stand-in and a
     real desc/desc_signature/desc_content node tree, so the real kind
     dispatch selects the flag itself.

Input domain: the model's Requires only demand list permissions, so any
code-point/kind-code lists qualify; generation sticks to the refinement's
carrier domain (kind codes in {0,1}, annotation/kind strings over a printable
alphabet, with the distinguished literal values mixed in heavily). The
`annotations` dict may also carry extra non-return keys: the model abstracts
the dict to (has_return, return text) and the extra keys must not perturb
the modeled observable.

>= 1e5 Requires-satisfying inputs: boundary grids + fuzz.
Pinned fuzz seed: 10449.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from types import SimpleNamespace

SEED = 10449
N_FUZZ_A = 70_000
N_FUZZ_B = 30_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure helpers from model.py, contracts stripped ---------------------------

def seq_class():
    # 'class' as Unicode code points
    return PSeq(99, 108, 97, 115, 115)


def seq_none():
    # 'None' as Unicode code points
    return PSeq(78, 111, 110, 101)


def is_return_field(code):
    return code == 1


def opt_seq(x):
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


def has_return_field(fields):
    if len(fields) == 0:
        return False
    return is_return_field(fields[0]) or has_return_field(fields.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def suppress_for_kind(object_kind):
    return ToSeq(object_kind) == seq_class()


def has_return_field_in(fields):
    found = False
    i = len(fields)
    while i > 0:
        if is_return_field(fields[i - 1]):
            found = True
        i = i - 1
    return found


def append_return_type(fields, has_return, return_annotation,
                       suppress_void_return):
    no_return_field = not has_return_field_in(fields)
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []
        j = 0
        while j < len(return_annotation):
            field.append(return_annotation[j])
            j = j + 1
        return field
    return None


# --- bridge: strings / docutils nodes <-> model carriers -----------------------

def str_to_codes(s):
    return [ord(c) for c in s]

def codes_to_str(codes):
    return "".join(chr(c) for c in codes)


# Kind-code 0 fields: any field that does not declare a return type. Rotate
# through several realizations so the bridge does not depend on one shape.
OTHER_FIELD_NAMES = ["param alpha", "type beta", "returns", "raises",
                     "param gamma delta"]


def build_field_list(nodes_mod, field_codes):
    fl = nodes_mod.field_list()
    for k, code in enumerate(field_codes):
        f = nodes_mod.field()
        if code == 1:
            name = "rtype"
        else:
            name = OTHER_FIELD_NAMES[k % len(OTHER_FIELD_NAMES)]
        f += nodes_mod.field_name("", name)
        f += nodes_mod.field_body("", nodes_mod.paragraph("", "existing"))
        fl += f
    return fl


def extract_new_rtype(fl, n_original):
    """The observable: among fields appended past the original ones, the body
    text of a newly added return-type field (None if none was added). Also
    reports how many were added (must be 0 or 1)."""
    added = []
    for f in fl.children[n_original:]:
        if f[0].astext() == "rtype":
            added.append(f[1].astext())
    if not added:
        return None, 0
    return added[0], len(added)


def make_annotations(has_return, ann_str, extra):
    annotations = {}
    for k, v in extra:
        annotations[k] = v
    if has_return:
        annotations["return"] = ann_str
    return annotations


# --- tier A: flag-level, real modify_field_list --------------------------------

def check_flag_level(nodes_mod, modify_field_list, field_codes, has_return,
                     ann_str, flag, extra):
    shadow = append_return_type(list(field_codes), has_return,
                                str_to_codes(ann_str), flag)
    shadow_content = None if shadow is None else codes_to_str(shadow)

    fl = build_field_list(nodes_mod, field_codes)
    annotations = make_annotations(has_return, ann_str, extra)
    modify_field_list(fl, annotations, suppress_rtype=flag)
    real_content, n_added = extract_new_rtype(fl, len(field_codes))

    if n_added > 1 or real_content != shadow_content:
        return ("DISAGREEMENT (flag-level)\n"
                "  fields=%r has_return=%r ann=%r flag=%r extra=%r\n"
                "  shadow=%r\n  real=%r (n_added=%d)"
                % (field_codes, has_return, ann_str, flag, extra,
                   shadow_content, real_content, n_added))
    return None


# --- tier B: kind-level, real merge_typehints end to end ------------------------

def check_kind_level(nodes_mod, addnodes_mod, merge_typehints, field_codes,
                     has_return, ann_str, kind_str, extra):
    flag = suppress_for_kind(str_to_codes(kind_str))
    shadow = append_return_type(list(field_codes), has_return,
                                str_to_codes(ann_str), flag)
    shadow_content = None if shadow is None else codes_to_str(shadow)

    desc = addnodes_mod.desc()
    sig = addnodes_mod.desc_signature("", "")
    sig["module"] = ""
    sig["fullname"] = "Thing"
    content = addnodes_mod.desc_content()
    desc += sig
    desc += content
    fl = build_field_list(nodes_mod, field_codes)
    content += fl
    annotations = make_annotations(has_return, ann_str, extra)
    app = SimpleNamespace(
        config=SimpleNamespace(autodoc_typehints="description",
                               autodoc_typehints_description_target="all"),
        env=SimpleNamespace(temp_data={"annotations": {"Thing": annotations}}))
    merge_typehints(app, "py", kind_str, content)
    real_content, n_added = extract_new_rtype(fl, len(field_codes))

    if n_added > 1 or real_content != shadow_content:
        return ("DISAGREEMENT (kind-level)\n"
                "  fields=%r has_return=%r ann=%r kind=%r extra=%r\n"
                "  shadow=%r\n  real=%r (n_added=%d)"
                % (field_codes, has_return, ann_str, kind_str, extra,
                   shadow_content, real_content, n_added))
    return None


# --- input generation -----------------------------------------------------------

BOUNDARY_FIELDS = [[], [0], [1], [0, 0], [1, 0], [0, 1], [1, 1]]
BOUNDARY_ANNS = ["None", "int", "", "None ", "none", "Optional[int]",
                 "NoneType"]
BOUNDARY_KINDS = ["class", "function", "method", "exception", "Class",
                  "class ", ""]
ANN_POOL = ["None", "int", "str", "", "Optional[int]", "none", "NONE",
            "None ", " None", "NoneType", "Dict[str, int]", "Any",
            "MyClass", "type"]
KIND_POOL = ["class", "function", "method", "exception", "attribute",
             "property", "data", "Class", "class ", "clas", "classs", ""]
ALPHABET = ("abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789[]., _")


def rand_str(rng, nmax=12):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, nmax)))


def rand_ann(rng):
    r = rng.random()
    if r < 0.30:
        return "None"
    if r < 0.65:
        return rng.choice(ANN_POOL)
    return rand_str(rng)


def rand_kind(rng):
    r = rng.random()
    if r < 0.30:
        return "class"
    if r < 0.65:
        return rng.choice(KIND_POOL)
    return rand_str(rng, 8)


def rand_fields(rng):
    n = rng.randint(0, 6)
    return [1 if rng.random() < 0.25 else 0 for _ in range(n)]


def rand_extra(rng):
    # Extra non-return annotation keys: the model abstracts the annotation
    # mapping to (presence, text) of the return entry only, so these must not
    # change the modeled observable.
    if rng.random() < 0.3:
        return [("zz%d" % k, rng.choice(ANN_POOL))
                for k in range(rng.randint(1, 2))]
    return []


def main():
    from docutils import nodes as nodes_mod
    from sphinx import addnodes as addnodes_mod
    # REAL patched callees:
    from sphinx.ext.autodoc.typehints import merge_typehints, modify_field_list

    checked = 0

    # -- tier A boundary grid
    for fields in BOUNDARY_FIELDS:
        for has_return in (True, False):
            for ann in BOUNDARY_ANNS:
                for flag in (True, False):
                    err = check_flag_level(nodes_mod, modify_field_list,
                                           fields, has_return, ann, flag, [])
                    if err:
                        print(err)
                        return 1
                    checked += 1

    # -- tier B boundary grid
    for fields in BOUNDARY_FIELDS:
        for has_return in (True, False):
            for ann in BOUNDARY_ANNS:
                for kind in BOUNDARY_KINDS:
                    err = check_kind_level(nodes_mod, addnodes_mod,
                                           merge_typehints, fields,
                                           has_return, ann, kind, [])
                    if err:
                        print(err)
                        return 1
                    checked += 1

    rng = random.Random(SEED)

    # -- tier A fuzz
    for _ in range(N_FUZZ_A):
        err = check_flag_level(nodes_mod, modify_field_list,
                               rand_fields(rng), rng.random() < 0.7,
                               rand_ann(rng), rng.random() < 0.5,
                               rand_extra(rng))
        if err:
            print(err)
            return 1
        checked += 1

    # -- tier B fuzz
    for _ in range(N_FUZZ_B):
        err = check_kind_level(nodes_mod, addnodes_mod, merge_typehints,
                               rand_fields(rng), rng.random() < 0.7,
                               rand_ann(rng), rand_kind(rng),
                               rand_extra(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched functions on %d inputs "
          "(boundary grids + %d flag-level fuzz + %d kind-level fuzz, seed %d)."
          % (checked, N_FUZZ_A, N_FUZZ_B, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
