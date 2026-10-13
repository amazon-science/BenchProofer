#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of
`implementation_consistency_pairs` against the patch.diff behaviour (the
post-patch `(app_label, model_name)` enumeration in makemigrations' consistency
check).

The impl region has R/I content (the nested accumulator `for` loops + ordered
pair construction), so this runs a real fuzz. Both legs operate over the modeled
carrier: a project = a list of applications, each carrying its label and the
names of the models it OWNS (the Lean ↔ Python bijection in mapping.md). This is
the abstraction shared by the Lean impl and the post-patch Python generator.

* shadow  — reproduces `implementation_consistency_pairs` op-for-op: empty
  accumulator; outer loop over applications; inner loop over the application's
  OWN models; append `(label, model)`; return the accumulation.
* patched — an independent reconstruction of the POST-patch generator semantics:
      for app_label in <apps in order>
          for model in get_app_config(app_label).get_models()   # the app's OWN models
              yield (app_label, model_name)
  i.e. each application paired only with the models it owns.

We assert zero disagreements over >=10^5 fuzzed projects.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 7530          # pinned in mapping.md
N = 120000           # >= 10^5

LABELS = ["migrations", "migrations2", "auth", "contenttypes", "sites",
          "admin", "sessions", "app_a", "app_b", "shard1", "shard2"]
MODELS = ["UnicodeModel", "Migrations2Model", "User", "Group", "Permission",
          "ContentType", "Site", "Book", "Author", "Tribble", "OtherModel"]


def shadow(apps):
    """R/I shadow of implementation_consistency_pairs:
        acc = []                          -- let mut acc := []
        for a in apps:                    -- for a in apps do
            for m in a['models']:         -- for m in a.models do  (the app's OWN models)
                acc.append((a['label'], m))   -- acc := acc ++ [(a.label, m)]
        return acc                        -- return acc
    """
    acc = []
    for a in apps:
        for m in a["models"]:
            acc.append((a["label"], m))
    return acc


def patched(apps):
    """Independent reconstruction of the POST-patch generator:
    for app_label in consistency_check_labels:
        for model in apps.get_app_config(app_label).get_models():  # app's own models
            -> (app_label, model_name)
    `get_app_config(label).get_models()` attributes each model only to the app
    that owns it, so the pairs are exactly each app's label with each of its
    own models, in order."""
    pairs = []
    for a in apps:                       # iterate applications in order
        own_models = a["models"]         # get_app_config(label).get_models(): OWN models
        for m in own_models:
            pairs.append((a["label"], m))
    return pairs


def rand_project(rng):
    n_apps = rng.randint(0, 5)
    apps = []
    for _ in range(n_apps):
        label = rng.choice(LABELS)
        k = rng.randint(0, 4)
        models = [rng.choice(MODELS) for _ in range(k)]
        apps.append({"label": label, "models": models})
    return apps


def main() -> int:
    rng = random.Random(SEED)

    # Deterministic boundary cases first (incl. the F2P-shaped discriminator:
    # two apps owning distinct models — the bug would cross-pair them).
    fixed = [
        [],
        [{"label": "migrations", "models": []}],
        [{"label": "migrations", "models": ["UnicodeModel"]}],
        [{"label": "migrations", "models": ["UnicodeModel"]},
         {"label": "migrations2", "models": ["Migrations2Model"]}],
        [{"label": "auth", "models": ["User", "Group", "Permission"]},
         {"label": "contenttypes", "models": ["ContentType"]}],
        [{"label": "a", "models": ["X", "Y"]},
         {"label": "b", "models": []},
         {"label": "c", "models": ["Z"]}],
    ]
    cases = fixed + [rand_project(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for apps in cases:
        got = shadow(apps)
        want = patched(apps)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((apps, got, want))

    if disagreements:
        print("G-CONF FAIL: {0} disagreements".format(disagreements))
        for a, g, w in examples:
            print("  in={0!r} shadow={1!r} patched={2!r}".format(a, g, w))
        return 1

    print("G-CONF OK: {0} inputs, 0 disagreements (seed={1})".format(len(cases), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
