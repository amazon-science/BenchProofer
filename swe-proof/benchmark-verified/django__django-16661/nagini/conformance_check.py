#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16661 (nagini).

SHADOW: the impl region of model.py (`retained_segments`), copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helper `keep_at` copies over as a plain function. The impl region
uses no PSeq (sequences appear only inside the stripped proof annotations),
so no sequence shim is needed. There are no @ContractOnly callees.

ORACLE: the REAL patched repo method the model models per mapping.md --
`django.contrib.admin.options.ModelAdmin.lookup_allowed` -- specifically its
per-segment retention loop. The gate applies patch.diff to /testbed before
this script runs and PYTHONPATH includes /testbed, so the patched code is
imported directly. Each trial builds a duck-typed chain of model/field
objects realizing one per-segment structural-fact assignment (mapping.md
section 2), calls the real method, and captures the retained-segment list
(the loop's accumulated local) via sys.settrace at frame return. The mask
compared against the shadow is the characteristic vector of that list over
the segment positions -- exactly the modelled observable (mapping.md
section 1).

Type bridge (mapping.md section 2, one duck attribute per fact):
  - segment k's name is the unique token "s<k>" (no separator substring),
    so membership in the retained list decodes the mask exactly;
  - prev_is_relation[k]      <-> field_{k-1}.is_relation (unused at k=0 by
    both shadow and oracle: the first segment is retained unconditionally);
  - field_is_parent_link[k]  <-> field_k in model_k._meta.parents.values();
  - field_is_auto_identity[k]<-> field_k is model_k._meta.auto_field;
  - model_has_auto_identity[k] <-> model_k._meta.auto_field is not None;
  - segment_targets_prior_hop[k] <-> "s<k>" in field_{k-1}.to_fields;
  - field_is_prior_hop_target[k] <-> field_k in
    field_{k-1}.path_infos[-1].target_fields (realized for fidelity; the
    patched method does not consult it, and the shadow ignores it).
Every field carries a non-empty path_infos to the next model so the real
loop walks all n segments (the model's carrier is a fully-resolved path;
shorter walks correspond to shorter fact vectors).

Bridged input domain (the image of the abstraction, within the Requires):
  - n >= 1 (a lookup path always has at least one segment);
  - field_is_auto_identity[k] implies model_has_auto_identity[k]: identity
    with an attribute that is None is not satisfiable by any object, so
    fact assignments violating the implication denote no concrete state
    and are outside the bridge. All other combinations are realized.

Inputs: exhaustive boundary enumeration (n=1 both fact settings; n=2 all
valid per-segment fact combos x irrelevant-coordinate settings; n=3 all
valid combo pairs) plus 100000 fuzz paths of length 1..8 -- >= 1e5
Requires-satisfying inputs total. Pinned fuzz seed: 16661.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random).
"""
import itertools
import random
import sys

SEED = 16661
N_FUZZ = 100_000


# --- pure helper from model.py, decorator stripped ---------------------------

def keep_at(prev_is_relation,
            field_is_parent_link,
            field_is_auto_identity,
            model_has_auto_identity,
            segment_targets_prior_hop):
    return (prev_is_relation
            and not field_is_parent_link
            and not field_is_auto_identity
            and ((not model_has_auto_identity)
                 or (not segment_targets_prior_hop)))


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def retained_segments(prev_is_relation,
                      field_is_parent_link,
                      field_is_auto_identity,
                      model_has_auto_identity,
                      segment_targets_prior_hop,
                      field_is_prior_hop_target):
    result = []  # type: list
    n = len(prev_is_relation)
    i = n
    while i > 0:
        # The facts of segment i-1 (the new head); list index ties to PSeq index.
        pr = prev_is_relation[i - 1]
        if i - 1 == 0:
            keep = True  # type: bool
        else:
            keep = keep_at(pr, field_is_parent_link[i - 1],
                           field_is_auto_identity[i - 1],
                           model_has_auto_identity[i - 1],
                           segment_targets_prior_hop[i - 1])
        if keep:
            result = [1] + result
        else:
            result = [0] + result
        i = i - 1
    return result


# --- oracle setup: import the real patched method ----------------------------

sys.path.insert(0, "/testbed")
import django  # noqa: E402
from django.conf import settings  # noqa: E402

settings.configure()
django.setup()

from django.contrib.admin.options import ModelAdmin  # noqa: E402
from django.core.exceptions import FieldDoesNotExist  # noqa: E402

_LOOKUP_ALLOWED_CODE = ModelAdmin.lookup_allowed.__code__


# --- duck-typed realization of one fact assignment ---------------------------

class _Meta(object):
    def __init__(self):
        self.related_fkey_lookups = []
        self.parents = {}
        self.auto_field = None
        self._fields = {}

    def get_field(self, name):
        try:
            return self._fields[name]
        except KeyError:
            raise FieldDoesNotExist(name)


class _Model(object):
    def __init__(self):
        self._meta = _Meta()


class _PathInfo(object):
    def __init__(self, to_model, target_fields):
        self.to_opts = to_model._meta
        self.to_opts.model = to_model
        self.target_fields = tuple(target_fields)


class _Field(object):
    def __init__(self):
        self.is_relation = False
        self.to_fields = []
        self.path_infos = None


class _Admin(object):
    def __init__(self, model):
        self.model = model
        self.list_filter = ()
        self.date_hierarchy = None


def build_chain(facts):
    """models[0..n], fields[0..n-1], parts[0..n-1] realizing the fact vectors."""
    n = len(facts["prev_is_relation"])
    parts = ["s%d" % k for k in range(n)]
    models = [_Model() for _ in range(n + 1)]
    fields = [_Field() for _ in range(n)]
    for k in range(n):
        models[k]._meta._fields[parts[k]] = fields[k]
        if facts["field_is_parent_link"][k]:
            models[k]._meta.parents = {object(): fields[k]}
        if facts["field_is_auto_identity"][k]:
            # bridged domain guarantees model_has_auto_identity[k]
            models[k]._meta.auto_field = fields[k]
        elif facts["model_has_auto_identity"][k]:
            models[k]._meta.auto_field = _Field()
        if k + 1 < n:
            fields[k].is_relation = facts["prev_is_relation"][k + 1]
            if facts["segment_targets_prior_hop"][k + 1]:
                fields[k].to_fields = [parts[k + 1]]
            tgt = (fields[k + 1],) if facts["field_is_prior_hop_target"][k + 1] else ()
            fields[k].path_infos = [_PathInfo(models[k + 1], tgt)]
        else:
            fields[k].path_infos = [_PathInfo(models[k + 1], ())]
    return models[0], parts


def oracle_mask(facts):
    """Run the real patched method; decode the retained-segment mask."""
    root, parts = build_chain(facts)
    lookup = "__".join(parts)
    captured = {}

    def local_trace(frame, event, arg):
        if event == "return":
            captured["rp"] = list(frame.f_locals["relation_parts"])
        return local_trace

    def global_trace(frame, event, arg):
        if frame.f_code is _LOOKUP_ALLOWED_CODE:
            return local_trace
        return None

    sys.settrace(global_trace)
    try:
        ModelAdmin.lookup_allowed(_Admin(root), lookup, "v")
    finally:
        sys.settrace(None)
    rp = set(captured["rp"])
    return [1 if p in rp else 0 for p in parts]


# --- input generation ---------------------------------------------------------

FACT_KEYS = ("prev_is_relation", "field_is_parent_link", "field_is_auto_identity",
             "model_has_auto_identity", "segment_targets_prior_hop",
             "field_is_prior_hop_target")


def valid_combos():
    """All per-segment fact 6-tuples inside the bridged domain."""
    out = []
    for c in itertools.product((False, True), repeat=6):
        (pr, pl, ai, ha, st, pt) = c
        if ai and not ha:
            continue
        out.append(c)
    return out


def facts_from_columns(cols):
    """cols: list of per-segment 6-tuples (ordered as FACT_KEYS)."""
    return {key: [c[j] for c in cols] for j, key in enumerate(FACT_KEYS)}


def boundary_inputs():
    combos = valid_combos()
    cases = []
    # n = 1: the single segment's facts are all irrelevant (always retained).
    for c in combos:
        cases.append(facts_from_columns([c]))
    # n = 2: exhaust segment 1's facts x a spread of segment-0 settings.
    seg0 = [(False,) * 6, (True, True, True, True, True, True),
            (True, False, True, True, False, True)]
    for c0 in seg0:
        for c1 in combos:
            cases.append(facts_from_columns([c0, c1]))
    # n = 3: exhaust (segment 1, segment 2) fact pairs.
    c0 = (False,) * 6
    for c1 in combos:
        for c2 in combos:
            cases.append(facts_from_columns([c0, c1, c2]))
    # The concrete three-segment scenario from mapping.md section 2.
    cases.append({
        "prev_is_relation": [False, True, True],
        "field_is_parent_link": [False, False, False],
        "field_is_auto_identity": [False, False, False],
        "model_has_auto_identity": [False, False, True],
        "segment_targets_prior_hop": [False, True, False],
        "field_is_prior_hop_target": [False, True, False],
    })
    return cases


def fuzz_input(rng):
    n = rng.randint(1, 8)
    cols = []
    for _ in range(n):
        pr = rng.random() < 0.5
        pl = rng.random() < 0.5
        ha = rng.random() < 0.5
        ai = ha and (rng.random() < 0.5)
        st = rng.random() < 0.5
        pt = rng.random() < 0.5
        cols.append((pr, pl, ai, ha, st, pt))
    return facts_from_columns(cols)


# --- driver -------------------------------------------------------------------

def check_one(facts):
    shadow = retained_segments(facts["prev_is_relation"],
                               facts["field_is_parent_link"],
                               facts["field_is_auto_identity"],
                               facts["model_has_auto_identity"],
                               facts["segment_targets_prior_hop"],
                               facts["field_is_prior_hop_target"])
    real = oracle_mask(facts)
    if shadow != real:
        print("DISAGREEMENT")
        print("input facts:", facts)
        print("shadow mask:", shadow)
        print("oracle mask:", real)
        return False
    return True


def main():
    rng = random.Random(SEED)
    checked = 0
    for facts in boundary_inputs():
        if not check_one(facts):
            return 1
        checked += 1
    for _ in range(N_FUZZ):
        if not check_one(fuzz_input(rng)):
            return 1
        checked += 1
    print("OK: %d inputs, zero disagreements" % checked)
    print('{"checked": %d, "disagreements": 0, "seed": %d}' % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
