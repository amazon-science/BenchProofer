#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13786 (nagini).

SHADOW: the impl region of model.py `reduced_create_options`, copied verbatim
below with the contract calls (Requires/Ensures) stripped. The @Pure helpers
(key_managed_a/key_managed_b/key_other/is_managed_option) copy over as plain
functions. The two @ContractOnly callees are unchanged language primitives, so
per the contract they call the REAL constructs they model: `merge_options`
executes the real dict-display merge `{**a, **b}` and `without_key` executes
the real one-key-removal residue (`dict.pop(k, None)` on a fresh copy) --
exactly as axiom_check.py validates them.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.db.migrations.operations.models.CreateModel.reduce`, driven with a
following options-alteration step on the same model name; the observation is
the `options` mapping of the single collapsed model-creation step it returns.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.

Type bridge (mapping.md section 2): model option-name int token <-> repo str
option name. The managed family in the model is exactly
{key_managed_a()=0, key_managed_b()=1}; these bridge to two distinct members
of the repo's managed-option name family (taken from the live class attribute,
not hard-coded). Every other int token bridges to a synthetic non-managed name
`custom_opt_<token>` (checked to be outside the managed family), preserving
key distinctness and membership. Option-value int tokens carry over as-is
(dict values compare by ==, which int preserves). The oracle's resulting
str-keyed mapping is pulled back through the inverse name map and compared
for dict equality against the shadow's int-keyed result.

Input domain: the model's Requires demand dict access plus that every key is
a genuine int (not bool). Generation therefore draws int-keyed, int-valued
pairs: exhaustive boundary coverage over the representative tokens
{0 (managed-a), 1 (managed-b), 2 (other), 3, -1, 10**6} -- each token absent
or present with distinct value tokens in each of the two inputs -- plus
randomized fuzz pairs. Pinned fuzz seed: 13786.

>= 1e5 Requires-satisfying inputs: 65536 exhaustive boundary pairs over
{0,1,2,3} + curated edge pairs + 100000 fuzz pairs.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13786
N_FUZZ = 100_000


# --- @ContractOnly callees: the REAL language primitives they model ----------

def merge_options(a, b):
    # the real mapping merge (later mapping wins), returning a fresh dict
    return {**a, **b}


def without_key(d, k):
    # the real residue of removing one name (no-op if absent), fresh dict
    r = dict(d)
    r.pop(k, None)
    return r


# --- pure helpers from model.py, contracts stripped ---------------------------

def key_managed_a():
    # A representative MANAGED option name (one the options step may set/clear).
    return 0


def key_managed_b():
    # A second, distinct representative MANAGED option name.
    return 1


def key_other():
    # A representative option name OUTSIDE the managed family (the options step
    # neither compares nor clears it).
    return 2


def is_managed_option(k):
    return k == key_managed_a() or k == key_managed_b()


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def reduced_create_options(self_options, operation_options):
    # Step 1: merge -- the options step's values win over the creation step's.
    options = merge_options(self_options, operation_options)
    # Step 2 (the new logic): clear every managed name the options step does not
    # provide, so the options step's mapping is the complete set of managed
    # options on the collapsed creation step.
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options


# --- oracle plumbing: drive the REAL patched CreateModel.reduce ---------------

def make_oracle():
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
    import django
    if hasattr(django, "setup"):
        try:
            django.setup()
        except Exception:
            pass
    from django.db.migrations.operations.models import (
        AlterModelOptions, CreateModel)

    # Two distinct members of the repo's managed-option family, read from the
    # live class attribute so the bridge tracks the real family.
    managed_keys = list(AlterModelOptions.ALTER_OPTION_KEYS)
    assert len(managed_keys) >= 2, managed_keys
    name_managed_a = managed_keys[-2]
    name_managed_b = managed_keys[-1]
    managed_set = set(managed_keys)

    def token_to_name(k):
        """Bridge an int option-name token to a repo str option name.

        Token 0/1 (the model's managed family) map to two distinct real
        managed names; every other token maps to a synthetic non-managed
        name. Injective by construction."""
        if k == 0:
            return name_managed_a
        if k == 1:
            return name_managed_b
        nm = "custom_opt_%d" % k if k >= 0 else "custom_opt_neg_%d" % (-k)
        assert nm not in managed_set, nm
        return nm

    def bridge(d):
        out = {}
        for k, v in d.items():
            out[token_to_name(k)] = v
        assert len(out) == len(d), (d, out)  # injectivity sanity
        return out

    def oracle(self_tokens, op_tokens, name_map_back):
        create = CreateModel("ProbeModel", fields=[],
                             options=bridge(self_tokens))
        alter = AlterModelOptions("ProbeModel", options=bridge(op_tokens))
        reduced = create.reduce(alter, "probe_app")
        assert isinstance(reduced, list) and len(reduced) == 1, reduced
        real_opts = reduced[0].options
        # pull the str-keyed result back to int tokens
        back = {}
        for nm, v in real_opts.items():
            assert nm in name_map_back, (nm, real_opts)
            back[name_map_back[nm]] = v
        return back

    return oracle, token_to_name


# --- differential driver -------------------------------------------------------

def check_pair(oracle, token_to_name, self_tokens, op_tokens):
    """Run shadow and oracle on one input pair; return an error string on
    disagreement, else None."""
    shadow = reduced_create_options(dict(self_tokens), dict(op_tokens))
    name_map_back = {token_to_name(k): k
                     for k in set(self_tokens) | set(op_tokens)}
    real = oracle(self_tokens, op_tokens, name_map_back)
    if shadow != real:
        return ("DISAGREEMENT\n  self_options=%r\n  operation_options=%r\n"
                "  shadow=%r\n  real=%r"
                % (self_tokens, op_tokens, shadow, real))
    return None


def boundary_pairs():
    """Exhaustive coverage over the representative tokens {0,1,2,3}: each
    token independently absent or present with one of three value tokens in
    each of the two inputs -> 4**4 * 4**4 = 65536 pairs, covering every
    pointwise behaviour combination of the managed/other partition (absent /
    present-agreeing / present-differing on each side). Plus curated edge
    pairs with negative and large tokens."""
    tokens = [0, 1, 2, 3]
    pairs = []
    # per token: 0 = absent, 1..3 = present with one of three value tokens
    # (values chosen so overlapping keys can agree or differ across inputs)
    choices = [None, 10, 20, 30]
    import itertools
    for combo_a in itertools.product(range(4), repeat=4):
        for combo_b in itertools.product(range(4), repeat=4):
            a = {t: choices[c] for t, c in zip(tokens, combo_a) if c}
            b = {t: choices[c] for t, c in zip(tokens, combo_b) if c}
            pairs.append((a, b))
    # curated edges: empty maps, negative / large tokens, equal values
    pairs += [
        ({}, {}),
        ({0: 7}, {}),
        ({0: 7}, {0: 7}),
        ({0: 7}, {0: 9}),
        ({1: 5}, {}),
        ({2: 5}, {}),
        ({-1: 4, 0: 1, 1: 2, 2: 3}, {-1: 8}),
        ({10**6: 1}, {0: 2, 1: 3}),
        ({0: 1, 1: 2, 2: 3, 3: 4, -5: 6}, {}),
        ({}, {0: 1, 1: 2, 2: 3, 3: 4, -5: 6}),
        ({-2: 0, -3: 0}, {-2: 0, 4: 0}),
    ]
    return pairs


def main():
    oracle, token_to_name = make_oracle()

    checked = 0
    boundary = boundary_pairs()
    for a, b in boundary:
        err = check_pair(oracle, token_to_name, a, b)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    token_pool = [0, 1, 2, 3, 4, 5, -1, -7, 100, 10**6]
    for _ in range(N_FUZZ):
        na = rng.randint(0, 6)
        nb = rng.randint(0, 6)
        a = {rng.choice(token_pool): rng.randint(-3, 9) for _ in range(na)}
        b = {rng.choice(token_pool): rng.randint(-3, 9) for _ in range(nb)}
        err = check_pair(oracle, token_to_name, a, b)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched reduce-options on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
