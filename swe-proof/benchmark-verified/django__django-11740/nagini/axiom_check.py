#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11740.

Executes the REAL unchanged callee
``MigrationAutodetector._get_dependencies_for_foreign_key`` (the helper the
gold patch invokes to compute the ordering dependencies of a relational field)
on a range of relational field definitions and asserts the property the
`fk_dependencies` axiom (model.py axioms region) encodes:

    for every relational field definition `field`,
        len(_get_dependencies_for_foreign_key(field)) > 0

i.e. computing the dependencies of a referencing field always yields at least
one dependency (the dependency on the referenced model itself is emitted
unconditionally). This is the only obligation the proof consumes from the
axiom (A-consumed): the altered-field operation, when its new definition is
relational, carries a NON-EMPTY dependency list.

Boundary + fuzz over the shapes a relational field can take that reach this
helper:
  - a plain ForeignKey to a concrete model in another app,
  - a ForeignKey to a model in the same app,
  - a OneToOneField,
  - a ManyToManyField (auto-created through table) and a ManyToManyField with
    an explicit (non-auto-created) through model,
  - a ForeignKey to a swappable model (the swappable_setting branch).

Imports only Django (the framework under test, configured here exactly as the
autodetector test module configures it) and the standard library. Exit 0 iff
every observation satisfies the axiom Ensures.
"""
import sys


def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            AUTH_USER_MODEL="auth.User",
        )
    django.setup()


def build_fields():
    """Return a list of resolved relational field instances reaching the
    helper, each paired with a human label."""
    from django.db import models

    class TargetB(models.Model):
        class Meta:
            app_label = "axiomapp_b"

    class ThroughExplicit(models.Model):
        src = models.ForeignKey("axiomapp_a.SourceA", on_delete=models.CASCADE)
        dst = models.ForeignKey(TargetB, on_delete=models.CASCADE)

        class Meta:
            app_label = "axiomapp_a"

    class SourceA(models.Model):
        # FK to a model in another app
        fk_other_app = models.ForeignKey(
            TargetB, null=True, on_delete=models.SET_NULL, related_name="+",
        )
        # FK to a model in the same app
        fk_same_app = models.ForeignKey(
            "axiomapp_a.SourceA", null=True, on_delete=models.SET_NULL,
            related_name="+",
        )
        # one-to-one
        o2o = models.OneToOneField(
            TargetB, null=True, on_delete=models.SET_NULL, related_name="+",
        )
        # m2m with auto-created through
        m2m_auto = models.ManyToManyField(TargetB, related_name="+")
        # m2m with an explicit (non-auto-created) through model
        m2m_through = models.ManyToManyField(
            TargetB, through=ThroughExplicit, related_name="+",
        )
        # FK to the swappable user model (exercises the swappable_setting branch)
        fk_swappable = models.ForeignKey(
            "auth.User", null=True, on_delete=models.SET_NULL, related_name="+",
        )

        class Meta:
            app_label = "axiomapp_a"

    meta = SourceA._meta
    labelled = []
    for name in ["fk_other_app", "fk_same_app", "o2o", "m2m_auto",
                 "m2m_through", "fk_swappable"]:
        labelled.append((name, meta.get_field(name)))
    return labelled


def main():
    configure_django()
    import inspect
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ProjectState

    project_state = ProjectState()
    autodetector = MigrationAutodetector(project_state, project_state)

    # The helper's signature is stable in meaning but its arity has varied
    # across Django versions: at this instance's base_commit (3.0) it is
    # `_get_dependencies_for_foreign_key(self, field)`; later versions added
    # `(app_label, model_name, field, project_state)`. Bind by parameter name
    # so the soundness property is checked against whichever real callee is
    # present (the in-container G-AX run uses the 3.0 single-argument form).
    sig = inspect.signature(MigrationAutodetector._get_dependencies_for_foreign_key)
    extra_names = [p for p in sig.parameters if p not in ("self", "field")]
    extras = {}
    for name in extra_names:
        if name == "app_label":
            extras[name] = "axiomapp_a"
        elif name == "model_name":
            extras[name] = "sourcea"
        elif name == "project_state":
            extras[name] = project_state
        else:
            extras[name] = None

    checked = 0
    for label, field in build_fields():
        # Only relational field definitions reach this helper in the patch
        # (guarded by `new_field.remote_field.model`).
        assert getattr(field, "is_relation", False), (
            "%s is unexpectedly non-relational" % label)
        deps = autodetector._get_dependencies_for_foreign_key(field=field, **extras)
        assert isinstance(deps, list), (
            "axiom unsound: %s -> dependencies is not a list: %r" % (label, deps))
        assert len(deps) > 0, (
            "axiom unsound on %s: _get_dependencies_for_foreign_key returned an "
            "EMPTY list, but the fk_dependencies axiom requires len(Result()) > 0"
            % label)
        checked += 1

    print("G-AX OK: _get_dependencies_for_foreign_key returned a non-empty "
          "dependency list for all %d relational field shapes "
          "(fk_dependencies axiom: len(Result()) > 0)." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
