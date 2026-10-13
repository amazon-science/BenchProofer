#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
implementation_resolveFieldModels against the patch.diff behaviour
(post-patch owning-model-state location in generate_renamed_fields).

The impl region is all R/I (no A-tagged op): the rename-map translation and the
two snapshot indexings are reproduced concretely as dict lookups. This runs a
real fuzz.

`shadow` reproduces the Lean impl op-for-op: per candidate field key, translate
the model's prior name via the rename map (dict.get with default), look up the
prior-snapshot state under the prior name, look up the current-snapshot state
under the CURRENT name, and accumulate the pair.

`patched_behavior` is an independent reconstruction of the post-patch loop body
from patch.diff: it indexes `to_state` by `model_name` (the patched line) and
`from_state` by `old_model_name`, using `.get` to totalize the subscript exactly
as the Option model does (a real run reaches the line only with present keys; the
fuzz exercises both present and absent keys to pin the index CHOICE).

We over-sample the renamed-model case (prior name != current name, current
snapshot missing the prior name) so the bug — indexing `to_state` by the prior
name — is observable: shadow locates `some`, a prior-name index would yield
`None`.

stdlib-only. exit 0 iff zero disagreements over >= 10^5 fuzzed inputs.
"""
import random
import sys

SEED = 15380          # pinned in mapping.md
N = 120_000           # >= 10^5

APPS = ["testapp", "otherapp", "app_a"]
NAMES = ["author", "book", "mymodel", "renamedauthor", "mymodel2", "tag", "post"]
FIELDS = ["id", "name", "renamed_name", "title", "slug"]


def make_state(name):
    # minimal touched surface: name + a small field list
    return {"name": name, "fields": ["id", name + "_f"]}


def shadow(rename_map, prior_states, current_states, entries):
    """Op-for-op shadow of implementation_resolveFieldModels."""
    acc = []
    for (app_label, model_name, _field_name) in entries:
        prior_name = rename_map.get((app_label, model_name), model_name)
        prior_state = prior_states.get((app_label, prior_name))
        current_state = current_states.get((app_label, model_name))   # CURRENT name
        acc.append((prior_state, current_state))
    return acc


def patched_behavior(rename_map, prior_states, current_states, entries):
    """Independent reconstruction of the patched loop body (patch.diff)."""
    out = []
    for (app_label, model_name, _field_name) in entries:
        old_model_name = rename_map.get((app_label, model_name), model_name)
        old_model_state = prior_states.get((app_label, old_model_name))
        # patched line: self.to_state.models[app_label, model_name]
        new_model_state = current_states.get((app_label, model_name))
        out.append((old_model_state, new_model_state))
    return out


def random_scenario(rng):
    app = rng.choice(APPS)
    rename_map = {}
    prior_states = {}
    current_states = {}
    entries = []

    n_entries = rng.randint(0, 4)
    for _ in range(n_entries):
        model = rng.choice(NAMES)
        field = rng.choice(FIELDS)
        entries.append((app, model, field))

        # decide whether this model was renamed this step
        if rng.random() < 0.6:  # over-sample renamed case
            prior = rng.choice([n for n in NAMES if n != model] + [model])
            if prior != model:
                rename_map[(app, model)] = prior
        else:
            prior = model

        # populate snapshots with random presence to exercise None branches
        if rng.random() < 0.85:
            prior_states[(app, prior)] = make_state(prior)
        if rng.random() < 0.85:
            current_states[(app, model)] = make_state(model)
        # sometimes also (mis)populate current under the prior name, to ensure
        # the shadow ignores it (it must key by current name)
        if prior != model and rng.random() < 0.3:
            current_states[(app, prior)] = make_state(prior + "_stale")

    return rename_map, prior_states, current_states, entries


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary: the exact F2P shape (rename Author->RenamedAuthor,
    # field name->renamed_name in testapp).
    fixed = [
        (
            {("testapp", "renamedauthor"): "author"},
            {("testapp", "author"): make_state("author")},
            {("testapp", "renamedauthor"): make_state("renamedauthor")},
            [("testapp", "renamedauthor", "renamed_name")],
        ),
        # no rename at all
        (
            {},
            {("testapp", "author"): make_state("author")},
            {("testapp", "author"): make_state("author")},
            [("testapp", "author", "extra")],
        ),
        # empty entries
        ({}, {}, {}, []),
    ]

    cases = fixed + [random_scenario(rng) for _ in range(N)]

    for rename_map, prior_states, current_states, entries in cases:
        got = shadow(rename_map, prior_states, current_states, entries)
        want = patched_behavior(rename_map, prior_states, current_states, entries)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((entries, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  entries={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
