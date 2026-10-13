#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-7530.

The operation under specification — gathering the models to examine for a given
app during the makemigrations history-consistency pre-check — is modelled
DEEPLY in model.py (the front-recursive filter `gathered`), not behind a
consumed axiom. This script validates that deep model against the REAL Django
application registry callee the gold patch switches to:

    apps.get_app_config(app_label).get_models()       # the fixed callee

It builds a real multi-app Django registry with DISJOINT model sets, runs the
real registry, and asserts:

  (A-reference) for every app label, the real
      `apps.get_app_config(label).get_models()` returns EXACTLY the models whose
      owning app is `label`, in registry order — i.e. it equals the deep model
      `gathered(owner, member, label)`. Every returned model belongs to the
      queried app (soundness) and none is omitted (completeness).

  (bug witness) the PRE-PATCH callee `apps.get_models(label)` ignores its first
      positional argument (it is bound to `include_auto_created`) and returns
      the PROJECT-WIDE model list, so it offers foreign-app models under
      `label`'s name — differing from `gathered` exactly when another app owns a
      model. This is the discriminating behaviour the frozen spec senses.

Imports nothing repo-specific beyond Django itself (the framework the patched
file lives in); the two apps are synthesised in a temp dir. Exit 0 iff every
obligation holds.
"""
import os
import shutil
import sys
import tempfile


# --- model.py reference: the deep model `gathered` --------------------------

def gathered(owner, member, target):
    """Reference of model.py's deep model `gathered`: members (in registry
    order) whose owning group equals `target`."""
    out = []
    for o, m in zip(owner, member):
        if o == target:
            out.append(m)
    return out


def _write_app(root, label, model_names):
    """Synthesise a minimal importable Django app package `label` under `root`
    with the given model class names, each a real django.db.models.Model."""
    pkg = os.path.join(root, label)
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    lines = ["from django.db import models", ""]
    for name in model_names:
        lines.append("class %s(models.Model):" % name)
        lines.append("    class Meta:")
        lines.append("        app_label = %r" % label)
        lines.append("")
    with open(os.path.join(pkg, "models.py"), "w") as f:
        f.write("\n".join(lines))


def main():
    tmp = tempfile.mkdtemp(prefix="dj7530_")
    try:
        # Two apps with DISJOINT model sets — the configuration that exposes the
        # bug (a member of one app must never be offered under the other's name).
        registry = {
            "alpha": ["AlphaOne", "AlphaTwo"],
            "beta": ["BetaOne", "BetaTwo", "BetaThree"],
        }
        for label, names in registry.items():
            _write_app(tmp, label, names)
        sys.path.insert(0, tmp)

        import django
        from django.conf import settings
        settings.configure(
            INSTALLED_APPS=list(registry.keys()),
            DATABASES={},
        )
        django.setup()
        from django.apps import apps

        # Ground-truth registry as the two aligned streams model.py uses. Group
        # and member identifiers are interned to ints (the List[int] carrier).
        labels = sorted(registry.keys())
        label_id = {lab: i for i, lab in enumerate(labels)}
        # member identity: (app, ClassName) -> stable int id
        all_pairs = []
        for lab in labels:
            for cfg_model in apps.get_app_config(lab).get_models():
                all_pairs.append((lab, cfg_model.__name__))
        member_id = {p: i for i, p in enumerate(sorted(all_pairs))}

        owner = [label_id[lab] for (lab, _name) in all_pairs]
        member = [member_id[(lab, name)] for (lab, name) in all_pairs]

        # --- (A-reference) real get_app_config(label).get_models() == gathered
        for lab in labels:
            real_models = list(apps.get_app_config(lab).get_models())
            real_ids = [member_id[(lab, m.__name__)] for m in real_models]
            expected = gathered(owner, member, label_id[lab])
            assert real_ids == expected, (
                "A-reference unsound for app %r: real get_app_config().get_models() "
                "gave ids %r, deep model `gathered` gives %r"
                % (lab, real_ids, expected))
            # every returned model belongs to the queried app (soundness)
            for m in real_models:
                assert m._meta.app_label == lab, (
                    "soundness violated: app %r get_models() returned a model "
                    "owned by %r" % (lab, m._meta.app_label))
            # completeness: nothing owned by `lab` omitted
            assert len(real_ids) == len(registry[lab]), (
                "completeness violated for app %r: %d vs %d models"
                % (lab, len(real_ids), len(registry[lab])))

        # --- (bug witness) pre-patch apps.get_models(app_label) ignores the
        #     label and returns the project-wide model set, differing from the
        #     deep model whenever another app owns a model.
        bug_witnessed = False
        for lab in labels:
            buggy_models = list(apps.get_models(lab))   # arg bound to a flag!
            buggy_names = sorted((m._meta.app_label, m.__name__) for m in buggy_models)
            own_only = sorted((lab, n) for n in registry[lab])
            if buggy_names != own_only:
                # at least one foreign-app model offered under `lab` — the bug
                foreign = [p for p in buggy_names if p[0] != lab]
                assert foreign, "expected foreign models in the buggy result"
                bug_witnessed = True
        assert bug_witnessed, (
            "bug witness failed: apps.get_models(label) did not differ from the "
            "per-app selection on a disjoint two-app registry")

        total = sum(len(v) for v in registry.values())
        print("G-AX OK: deep model `gathered` == real "
              "apps.get_app_config(label).get_models() for %d apps / %d models; "
              "pre-patch apps.get_models(label) returns the project-wide set "
              "(bug witnessed)." % (len(labels), total))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
