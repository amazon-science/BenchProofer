#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-7530 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable output: the
collection of (application label, model) pairs the registry consistency scan
enumerates (the pairs handed to ``router.allow_migrate``).

  * SHADOW  — the R/I-tagged ops of Solution.lean's ``appModelPairs`` impl region
              transliterated to Python over the *real* repo carrier, via the
              mapping.md bijection: an ``AppEntry`` is an application label paired
              with the list of models that application owns
              (``apps.get_app_config(label).get_models()``); ``appPairs`` maps the
              label over those owned models; ``allPairs`` concatenates, in registry
              order, every application's own pairs.  No A-tagged callee is consumed
              (the proof consumes no axiom); the impl region is pure R/I.
  * ORACLE  — ``patch.diff``'s behaviour: the patched generator expression
              (``django/core/management/commands/makemigrations.py`` line 105-108)
                  (app_label, model)
                  for app_label in consistency_check_labels
                  for model in apps.get_app_config(app_label).get_models()
              i.e. each application label paired with *that application's own*
              models — the real correctness oracle (G-RESOLVE).

Both registry methods are reproduced *faithfully from the real Django source* at
base_commit (``django/apps/registry.py`` ``Apps.get_models`` and
``django/apps/config.py`` ``AppConfig.get_models``); when a live, configured
Django ``apps`` registry is importable we additionally cross-check the real
methods (the live oracle).  The comparison is order-insensitive on the label
dimension because ``consistency_check_labels`` is a Python ``set`` — pairs are
compared as multisets.

To give the check teeth (it must distinguish the fix from the *bug*) every fuzz
case also computes the BUGGY expansion — the pre-patch
``apps.get_models(app_label)`` which, because ``app_label`` binds to the
``include_auto_created`` positional flag, returns the WHOLE-registry model union
for every label — and asserts SHADOW disagrees with the bug exactly when the
registry is non-degenerate (more than one distinct owned-model set).  A shadow
that matched the bug would be a spec that fails the F2P test.

Exit 0 iff (a) zero SHADOW-vs-patched disagreements and (b) the modeled
behaviour is the fix, not the bug, on every discriminating registry.  Runs
in-container (stdlib only); the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
from collections import Counter

SEED = 7530
N_FUZZ = 100000


# --- faithful transliteration of the real Django registry source ------------
# django/apps/config.py  AppConfig.get_models(include_auto_created=False,
#                                              include_swapped=False):
#     yields each of *this* application's own models, skipping auto-created /
#     swapped unless the corresponding flag is set.
# django/apps/registry.py  Apps.get_models(include_auto_created=False,
#                                           include_swapped=False):
#     iterates over *every* app_config and extends the result with each
#     app_config.get_models(...) -> the flat union across the whole project.
#
# We model a registry as an ordered list of (label, owned_models), where each
# owned model is a (name, auto_created, swapped) triple.

def appconfig_get_models(owned, include_auto_created=False, include_swapped=False):
    out = []
    for (name, auto_created, swapped) in owned:
        if auto_created and not include_auto_created:
            continue
        if swapped and not include_swapped:
            continue
        out.append(name)
    return out


def apps_get_models(registry, include_auto_created=False, include_swapped=False):
    """Apps.get_models: union over ALL app_configs (django/apps/registry.py)."""
    result = []
    for (_label, owned) in registry:
        result.extend(appconfig_get_models(owned, include_auto_created, include_swapped))
    return result


def get_app_config(registry, label):
    for (lbl, owned) in registry:
        if lbl == label:
            return owned
    raise LookupError(label)


# --- ORACLE: patch.diff's patched generator expression ----------------------
def oracle_pairs(registry, labels):
    """Patched: each label paired with that app's OWN models."""
    pairs = []
    for label in labels:
        for model in appconfig_get_models(get_app_config(registry, label)):
            pairs.append((label, model))
    return pairs


# --- BUGGY: pre-patch generator expression (apps.get_models(app_label)) ------
def buggy_pairs(registry, labels):
    """Pre-patch: ``apps.get_models(app_label)`` — app_label binds to the
    include_auto_created flag, so every label is paired with the WHOLE-registry
    model union (auto-created models included when the label is truthy)."""
    pairs = []
    for label in labels:
        for model in apps_get_models(registry, include_auto_created=bool(label)):
            pairs.append((label, model))
    return pairs


# --- SHADOW: Solution.lean appModelPairs / allPairs, transliterated ----------
def shadow_pairs(registry, labels):
    """allPairs over the carrier built per the mapping.md bijection: AppEntry
    for label L = (L, that app's own models = appconfig_get_models). appPairs
    maps L over those models; allPairs concatenates in registry order."""
    # carrier: only the apps whose labels are scanned, in registry order
    carrier = [(lbl, appconfig_get_models(owned))
               for (lbl, owned) in registry if lbl in labels]
    out = []
    for (lbl, models) in carrier:        # allPairs: front-recursive concat
        for m in models:                 # appPairs: map label over own models
            out.append((lbl, m))
    return out


# --- fuzzing -----------------------------------------------------------------
def random_registry(rng):
    n_apps = rng.randint(0, 6)
    registry = []
    used_labels = set()
    for _ in range(n_apps):
        # labels are small positive ints (truthy) or, rarely, 0 to exercise the
        # bug's include_auto_created=bool(label) edge.
        lbl = rng.choice([0] + list(range(1, 12)))
        while lbl in used_labels:
            lbl = rng.randint(1, 40)
        used_labels.add(lbl)
        n_models = rng.randint(0, 5)
        owned = []
        for _ in range(n_models):
            name = rng.randint(0, 30)
            auto = rng.random() < 0.15
            swapped = rng.random() < 0.08
            owned.append((name, auto, swapped))
        registry.append((lbl, owned))
    return registry


def boundary_registries():
    # empty project
    yield []
    # single app, no models
    yield [(1, [])]
    # single app, one model
    yield [(1, [(10, False, False)])]
    # two apps with DISJOINT models (the discriminating shape)
    yield [(1, [(10, False, False)]), (2, [(20, False, False)])]
    # three shards with different model sets (the issue's scenario)
    yield [(1, [(10, False, False), (11, False, False)]),
           (2, [(20, False, False)]),
           (3, [])]
    # app whose only models are auto-created / swapped (filtered out)
    yield [(1, [(10, True, False), (11, False, True)]), (2, [(20, False, False)])]
    # label 0 (falsy) to exercise include_auto_created=bool(label) in the bug
    yield [(0, [(10, True, False)]), (1, [(20, False, False)])]


def main():
    rng = random.Random(SEED)
    disagreements = []      # shadow != patched  (R/I infidelity)
    spec_too_weak = []      # shadow == bug on a discriminating registry
    count = 0

    def check(registry):
        nonlocal count
        count += 1
        # consistency_check_labels is a SET over the registry's labels; emulate
        # the unordered iteration by shuffling a copy.
        labels = [lbl for (lbl, _o) in registry]
        shuffled = labels[:]
        rng.shuffle(shuffled)
        labelset = set(shuffled)

        shadow = Counter(shadow_pairs(registry, labelset))
        patched = Counter(oracle_pairs(registry, shuffled))
        if shadow != patched:
            disagreements.append((registry, shadow, patched))

        # teeth: where the fix and the bug differ, the model must follow the fix
        bug = Counter(buggy_pairs(registry, shuffled))
        if bug != patched and shadow == bug:
            spec_too_weak.append((registry, shadow, bug))

    for reg in boundary_registries():
        check(reg)
    for _ in range(N_FUZZ):
        check(random_registry(rng))
        if len(disagreements) >= 5 or len(spec_too_weak) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d registries:"
              % (len(disagreements), count))
        for reg, sh, orc in disagreements[:5]:
            print("  registry=%r shadow=%r patched=%r" % (reg, dict(sh), dict(orc)))
        return 1
    if spec_too_weak:
        print("G-CONF FAIL: modeled behaviour matched the BUG (not the fix) on "
              "%d discriminating registries:" % len(spec_too_weak))
        for reg, sh, bug in spec_too_weak[:5]:
            print("  registry=%r shadow=%r bug=%r" % (reg, dict(sh), dict(bug)))
        return 1

    # optional live cross-check against the real Django registry methods
    live = _live_crosscheck()
    print("G-CONF OK: R/I shadow of appModelPairs agrees with patch.diff "
          "(per-app own-models enumeration) on %d registries (seed=%d), 0 "
          "disagreements; modeled behaviour tracks the fix not the bug.%s"
          % (count, SEED, live))
    return 0


def _live_crosscheck():
    """If a configured Django is importable, confirm on the real registry that
    get_app_config(L).get_models() (patched) differs from get_models(L) (buggy)
    — i.e. the divergence the model captures is the real one. Best-effort; never
    fails the gate (the faithful-source oracle above is authoritative)."""
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
                DATABASES={}, USE_TZ=False)
        django.setup()
        from django.apps import apps
        labels = [c.label for c in apps.get_app_configs()]
        all_models = set(apps.get_models())
        diverged = False
        for L in labels:
            own = set(apps.get_app_config(L).get_models())
            if own != all_models and len(all_models) > len(own):
                diverged = True
                break
        return (" Live Django cross-check: per-app own-models are a strict "
                "subset of the whole-project model union (the bug's divergence "
                "confirmed).") if diverged else \
               " Live Django importable; registry too small to diverge."
    except Exception as e:        # noqa: BLE001 — best-effort only
        return " (live cross-check skipped: %s)" % type(e).__name__


if __name__ == "__main__":
    sys.exit(main())
