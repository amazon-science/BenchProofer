#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15380 (nagini).

SHADOW: the impl region of model.py, copied verbatim below (no contract calls
live inside the impl region, so nothing to strip) plus the @Pure helper
`prior_name` copied over as a plain function. There are no @ContractOnly
callees and no PSeq usage in this bundle; the carriers are plain dicts and
ints, so no sequence shim is needed.

ORACLE: the REAL patched repo routine the model models per mapping.md --
`django.db.migrations.autodetector.MigrationAutodetector
.generate_renamed_fields` -- whose per-field loop body selects the model's
prior-state and later-state descriptors from the two state registries. The
gate applies patch.diff to /testbed before this script runs; PYTHONPATH=
/testbed makes the patched code importable. The two project states are
bridged as duck-typed objects whose `.models` mappings are recording dicts:
every subscription the real loop performs is captured (key and fetched
value), so the pair of descriptors the real code selects for each enumerated
field is observed directly at the two selection sites. The per-field keys the
loop enumerates are preset (`new_field_keys`), the rename-correspondence map
(`renamed_models`) is preset from the bridged correspondence, and
`old_field_keys` is left empty so the not-modeled remainder of the loop body
(candidate-rename scanning; mapping.md tags it outside the modeled
selection) stays inert while both modeled registry subscriptions still
execute unconditionally. The field read off the selected later descriptor
(also not modeled -- the descriptor token stands for the object it is read
from) is served by the duck-typed descriptor's `get_field`, which hands back
an opaque object.

Type bridge (mapping.md section 2): one app label is fixed ("app"); an int
model-name token n maps to the model name string "m%d" and the registry key
("app", "m%d"); an int descriptor token maps to a duck-typed model-state
object carrying that token (tokens are globally unique across both
registries, so descriptor equality pins both the registry and the key that
was used). The correspondence map bridges to `renamed_models`
{("app", later_str): prior_str}. Real iteration order is the loop's sorted
key order, recomputed here to align each observed lookup pair with its
later-name token.

Input domain: the model's preconditions require the later name to be a key
of the later-state registry and the prior name (correspondence with
fallback) to be a key of the prior-state registry. The generator (mirroring
axiom_check.py's) enforces both for every enumerated model: the later
registry is built over the sampled later names, the correspondence maps a
random subset to fresh distinct prior names, and the prior registry holds
every model under its prior name. Boundary cases mirror axiom_check.py's
four configurations; fuzz draws 1-6 models per state with roughly half
renamed, batching all models of a configuration through one real call to
exercise the actual loop.

>= 1e5 Requires-satisfying inputs: boundary cases + fuzz configurations
until 100000 enumerated (configuration, later-name) queries are checked.
Pinned fuzz seed: 15380.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15380
N_TARGET = 100_000

APP = "app"


# --- pure helper from model.py, decorator stripped ------------------------------

def prior_name(correspondence, later):
    """The model's name in the prior state: the correspondence map applied to
    the later-state name `later`, falling back to `later` when the model kept
    its name (i.e. `later` is not recorded in the map)."""
    if later in correspondence:
        return correspondence[later]
    return later


# --- the impl region of model.py, verbatim ---------------------------------------

def resolve_field_states(prior_registry, later_registry, correspondence, later):
    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[later]  # type: int
    return (old_descriptor, new_descriptor)


# --- type bridge: int tokens <-> registry keys / duck-typed descriptors ----------

def name_str(token):
    return "m%d" % token


def key_for(token):
    return (APP, name_str(token))


def token_of_name(name):
    assert name.startswith("m"), "unexpected model name %r" % (name,)
    return int(name[1:])


class _Descriptor(object):
    """Duck-typed model-state descriptor: carries its unique token; serves the
    (not-modeled) field read with an opaque object."""
    def __init__(self, token):
        self.token = token

    def get_field(self, field_name):
        return object()


class _RecordingDict(dict):
    """A registry that records every subscription (key, fetched value)."""
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.log = []

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        self.log.append((key, value))
        return value


class _State(object):
    """Duck-typed project state: only the `.models` registry is consumed."""
    def __init__(self, models):
        self.models = models


# --- differential -----------------------------------------------------------------

def check_config(make_detector, from_tokens, to_tokens, corr_tokens):
    """One configuration: prior registry {name_tok: desc_tok}, later registry
    {name_tok: desc_tok}, correspondence {later_tok: prior_tok}. Runs ONE real
    call enumerating every later-state model and compares, per model, the
    pair of descriptors the real loop fetched against the shadow's pair.
    Returns (n_checked, error_string_or_None)."""
    from_reg = _RecordingDict(
        {key_for(n): _Descriptor(t) for n, t in from_tokens.items()})
    to_reg = _RecordingDict(
        {key_for(n): _Descriptor(t) for n, t in to_tokens.items()})
    renamed = {key_for(l): name_str(p) for l, p in corr_tokens.items()}

    new_field_keys = {(APP, name_str(n), "f") for n in to_tokens}

    detector = make_detector(_State(from_reg), _State(to_reg))
    detector.renamed_models = renamed
    detector.renamed_models_rel = {}
    detector.new_field_keys = set(new_field_keys)
    detector.old_field_keys = set()

    detector.generate_renamed_fields()

    order = sorted(new_field_keys)
    if len(from_reg.log) != len(order) or len(to_reg.log) != len(order):
        return 0, ("HARNESS MISMATCH: expected one lookup per registry per "
                   "enumerated field; from=%d to=%d fields=%d"
                   % (len(from_reg.log), len(to_reg.log), len(order)))

    for i, (_app, model_str, _f) in enumerate(order):
        later_tok = token_of_name(model_str)
        real_out = (from_reg.log[i][1].token, to_reg.log[i][1].token)
        shadow_out = resolve_field_states(
            dict(from_tokens), dict(to_tokens), dict(corr_tokens), later_tok)
        if shadow_out != real_out:
            return i, ("DISAGREEMENT\n  prior_registry=%r\n  later_registry=%r\n"
                       "  correspondence=%r\n  later=%r\n  shadow=%r\n  real=%r"
                       % (from_tokens, to_tokens, corr_tokens, later_tok,
                          shadow_out, real_out))
    return len(order), None


def boundary_configs():
    # Mirrors axiom_check.py's boundary configurations (from, to, corr).
    return [
        ({1: 100}, {2: 200}, {2: 1}),
        ({5: 500}, {5: 555}, {}),
        ({1: 100, 3: 300, 7: 700}, {2: 200, 3: 301, 7: 701}, {2: 1}),
        ({1: 100, 3: 300}, {2: 200, 3: 301}, {2: 1}),
    ]


def rand_config(rng, uniq):
    """Random Requires-satisfying configuration; descriptor tokens drawn from
    `uniq` (a counter list) so they are globally unique across registries."""
    def fresh_desc():
        uniq[0] += 1
        return uniq[0]

    n_later = rng.randint(1, 6)
    later_names = rng.sample(range(0, 40), n_later)
    to_tokens = {nm: fresh_desc() for nm in later_names}

    corr = {}
    used_prior = set(later_names)
    for nm in later_names:
        if rng.random() < 0.5:
            candidates = [c for c in range(40, 90) if c not in used_prior]
            pn = rng.choice(candidates)
            used_prior.add(pn)
            corr[nm] = pn

    from_tokens = {prior_name(corr, nm): fresh_desc() for nm in later_names}
    return from_tokens, to_tokens, corr


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched callee: the autodetector method whose per-field loop body
    # the model contracts (mapping.md section 1).
    from django.db.migrations.autodetector import MigrationAutodetector

    def make_detector(from_state, to_state):
        return MigrationAutodetector(from_state, to_state)

    checked = 0

    for from_tokens, to_tokens, corr in boundary_configs():
        n, err = check_config(make_detector, from_tokens, to_tokens, corr)
        if err:
            print(err)
            return 1
        checked += n
    n_boundary = checked

    rng = random.Random(SEED)
    uniq = [1000]
    n_configs = 0
    while checked < N_TARGET:
        from_tokens, to_tokens, corr = rand_config(rng, uniq)
        n, err = check_config(make_detector, from_tokens, to_tokens, corr)
        if err:
            print(err)
            return 1
        checked += n
        n_configs += 1

    print("G-CONF OK: shadow impl == real per-field descriptor selection on "
          "%d inputs (%d boundary + %d fuzz over %d configurations, seed %d)."
          % (checked, n_boundary, checked - n_boundary, n_configs, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
