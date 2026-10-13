#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15104 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with no contract
calls to strip (the impl region contains none). The @Pure helper ``TO`` is
copied over as a plain function. The single @ContractOnly callee the impl
uses, ``pop_default``, calls the REAL language primitive it deep-models per
mapping.md section 3.1 -- ``dict.pop(key, None)`` -- applied to a copy,
because the model is functional (it relates a fresh result mapping to a
read-only input). No PSeq usage in this bundle, so no sequence shim.

ORACLE: the REAL patched repo method the model models per mapping.md --
``django.db.migrations.autodetector.MigrationAutodetector
.only_relation_agnostic_fields`` -- whose per-field body reduces a field's
deconstructed keyword mapping to the relation-agnostic form. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable. Each generated field is a duck-typed object whose
``deconstruct()`` returns a controllable (path, args, kwargs) triple --
exactly what ``deep_deconstruct`` consumes for a non-Field deconstructible --
and whose ``remote_field`` attribute realizes the relation guard the model's
``is_relation`` parameter abstracts (mapping.md section 2).

Type bridge (mapping.md section 2): the model carrier Dict[int, int] maps a
keyword-name token to an opaque value token; only key membership and per-key
value identity are observed. Token 0 (``TO()``) <-> the related-target
keyword name 'to'; any non-zero token j <-> the distinct keyword name
'k%d' % j (injective, never the target keyword); value tokens carry over as
the int values themselves (opaque under equality). The oracle's resulting
kwargs dict is mapped back to tokens and compared to the shadow's result
dict with ==. The relation flag bridges to the guard's truth value: the
generated field's relation attribute is one of several shapes (absent
target, target-carrying, falsy inner attribute) whose guard truth equals
the shadow's ``is_relation`` argument.

Input domain: the model's precondition places no constraint on the mapping
beyond its Dict[int, int] type (plus read-only permission, which the shadow
respects by construction), and ``is_relation`` ranges over bool. Boundary
cases mirror axiom_check.py's boundary mappings crossed with both flag
values and all guard shapes; fuzz draws mappings of 0-8 entries with keys
straddling token 0, forcing both the target-present and target-absent arms
heavily, batching 1-4 fields per oracle call to exercise the real per-field
loop as well.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz fields.
Pinned fuzz seed: 15104.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15104
N_FUZZ = 100_000


# --- pure helper from model.py, decorator stripped ------------------------------

def TO():
    # The token for the related-target keyword (the one dropped from the
    # relation-agnostic form). A distinguished keyword-name token.
    return 0


# --- @ContractOnly callee shim: the REAL primitive it deep-models ----------------

def pop_default(d, k):
    # The real broadly-applicable removal primitive (mapping.md section 3.1),
    # run on a copy because the model relates a FRESH result mapping to the
    # read-only input.
    result = dict(d)
    result.pop(k, None)
    return result


# --- the impl region of model.py, verbatim ---------------------------------------

def reduce_to_relation_agnostic(kwargs, is_relation):
    if is_relation:
        return pop_default(kwargs, TO())
    return kwargs


# --- type bridge: token mapping <-> string-keyed kwargs dict ---------------------

def token_key_to_name(j):
    return "to" if j == TO() else "k%d" % j


def name_to_token_key(name):
    if name == "to":
        return TO()
    assert name.startswith("k"), "unexpected keyword name %r" % (name,)
    return int(name[1:])


def tokens_to_kwargs(d):
    return {token_key_to_name(j): v for j, v in d.items()}


def kwargs_to_tokens(kw):
    return {name_to_token_key(name): v for name, v in kw.items()}


class _Remote(object):
    """The relation attribute shape the guard inspects."""
    def __init__(self, model):
        self.model = model


class _FakeField(object):
    """Duck-typed deconstructible: deep_deconstruct sees the deconstruct()
    triple; the guard sees remote_field."""
    def __init__(self, kwargs_names, remote_field):
        self._kwargs = kwargs_names
        self.remote_field = remote_field

    def deconstruct(self):
        # (path, args, kwargs) -- a non-Field deconstructible's triple.
        return ("conf.bridge.FakeField", [], dict(self._kwargs))


def remote_shapes_for(is_relation, rng):
    """A relation attribute whose guard truth value equals is_relation."""
    if is_relation:
        return _Remote(model=object())
    # guard-false shapes: no relation attribute at all, or one whose inner
    # attribute is falsy.
    return None if rng.random() < 0.5 else _Remote(model=None)


# --- differential ----------------------------------------------------------------

def check_batch(autodetector_call, cases):
    """cases: list of (token_dict, is_relation, remote_field). Runs one real
    oracle call over the whole batch (exercising the per-field loop) and the
    shadow per field; returns an error string on any disagreement."""
    fields = {}
    for i, (tok, _is_rel, remote) in enumerate(cases):
        fields["f%02d" % i] = _FakeField(tokens_to_kwargs(tok), remote)
    fields_def = autodetector_call(fields)
    # sorted(fields.items()) iterates names f00, f01, ... in order.
    for i, (tok, is_rel, _remote) in enumerate(cases):
        real_kwargs = fields_def[i][2]
        real_out = kwargs_to_tokens(real_kwargs)
        shadow_out = reduce_to_relation_agnostic(dict(tok), is_rel)
        if shadow_out != real_out:
            return ("DISAGREEMENT\n  kwargs(tokens)=%r  is_relation=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (tok, is_rel, shadow_out, real_out))
    return None


def boundary_token_dicts():
    # Mirrors axiom_check.py's boundary mappings.
    T = TO()
    return [
        {},                                    # empty mapping
        {T: 99},                               # only the target keyword
        {1: 10},                               # one non-target keyword, no target
        {1: 10, 2: 20},                        # several non-target, no target
        {T: 99, 1: 10, 2: 20},                 # target + others
        {T: 0},                                # target with falsy value
        {0: 0, 1: 0, 2: 0, 3: 0},              # target + others, repeated value
        {5: 5},                                # disjoint single key
        {T: 7, 5: 5, 9: 9, 13: 13},            # target + scattered others
    ]


def rand_token_dict(rng):
    d = {}
    n = rng.randint(0, 8)
    for _ in range(n):
        key = rng.randint(-3, 6)               # key space straddles TO()==0
        d[key] = rng.randint(-3, 50)
    # force both arms hard: target present / target absent
    coin = rng.random()
    if coin < 0.4:
        d[TO()] = rng.randint(-3, 50)
    elif coin < 0.8:
        d.pop(TO(), None)
    return d


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched callee: the detector method whose per-field body the
    # model contracts (mapping.md section 1).
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ProjectState

    detector = MigrationAutodetector(ProjectState(), ProjectState())

    def autodetector_call(fields):
        return detector.only_relation_agnostic_fields(fields)

    rng = random.Random(SEED)
    checked = 0

    # boundary: every boundary mapping x both flag values x each guard shape
    boundary = boundary_token_dicts()
    for tok in boundary:
        for is_rel in (True, False):
            for remote in ((_Remote(model=object()),) if is_rel
                           else (None, _Remote(model=None))):
                err = check_batch(autodetector_call, [(tok, is_rel, remote)])
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # fuzz: batches of 1-4 fields per oracle call
    while checked - n_boundary < N_FUZZ:
        batch = []
        for _ in range(rng.randint(1, 4)):
            tok = rand_token_dict(rng)
            is_rel = rng.random() < 0.5
            batch.append((tok, is_rel, remote_shapes_for(is_rel, rng)))
        err = check_batch(autodetector_call, batch)
        if err:
            print(err)
            return 1
        checked += len(batch)

    print("G-CONF OK: shadow impl == real relation-agnostic reduction on %d "
          "field inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee shimmed to the real "
                                "dict removal primitive)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
