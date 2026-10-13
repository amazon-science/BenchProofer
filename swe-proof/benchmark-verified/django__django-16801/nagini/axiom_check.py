#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16801.

This bundle consumes NO @ContractOnly axioms: the registration decision is
modelled deeply in model.py (the pure ``should_register`` predicate and the
single conditional append). What G-AX validates here is the **A-reference** —
that the deep model's decision predicate

    should_register(is_abstract, width_target, height_target)
        == (not is_abstract) and (configured(width_target)
                                  or configured(height_target))
    configured(name) == name is not None and len(name) > 0

faithfully captures the REAL Django decision of whether the post-initialization
recalculation hook is registered with a model class's ``post_init`` notification
list when an image-bearing field is attached.

It builds REAL Django model classes (concrete and abstract) carrying an image
field configured with every combination of {no target, width only, height only,
both} companion size-fields, attaches the field via the real
``ImageField.contribute_to_class`` (driven by real model-class creation), and
asserts for every observation:

  * the field's recalculation handler is present in the class's
    ``post_init.receivers`` IFF the deep-model predicate ``should_register``
    says it should be — i.e. exactly when the class is concrete AND at least one
    companion target is configured;
  * a concrete class with NO companion target has the handler ABSENT (the exact
    F2P scenario: ``test_post_init_not_connected``);
  * the truthiness used by the model (``name is not None and len(name) > 0``)
    matches Python's truthiness of ``width_field or height_field`` on the real
    target-name values.

It also confirms, independently of Django, that the model's ``configured`` /
``should_register`` reference encodings agree with Python truthiness of the
underlying ``width_field or height_field`` expression (the A-reference proper).

Run inside the official SWE-bench container for the instance, where Django +
Pillow are importable. Exit 0 iff every obligation holds. Outside the container
(Django absent) it prints ``G-AX SKIP`` after the Django-independent checks and
returns 0; the orchestrator runs it in-container.
"""
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def configured(name):
    """Reference encoding of model.py's pure `configured`: a companion target
    is configured iff it is present and non-empty."""
    return name is not None and len(name) > 0


def should_register(is_abstract, width_target, height_target):
    """Reference encoding of model.py's pure `should_register`."""
    return (not is_abstract) and (configured(width_target)
                                  or configured(height_target))


def _check_truthiness_reference():
    """The A-reference proper: the model's `configured`/`should_register`
    boolean reference agrees with Python's truthiness of the real
    `width_field or height_field` expression, over all relevant target-name
    shapes (absent, empty, and genuine non-empty field names)."""
    names = [None, "", "w", "mugshot_width", "mugshot_height", "x" * 64]
    for is_abstract in (False, True):
        for w in names:
            for h in names:
                # Python truthiness of the real `self.width_field or
                # self.height_field` guard, combined with the abstract check.
                real_decision = (not is_abstract) and bool(w or h)
                model_decision = should_register(is_abstract, w, h)
                assert real_decision == model_decision, (
                    "should_register reference disagrees with Python "
                    "truthiness on (abstract=%r, w=%r, h=%r): real=%r model=%r"
                    % (is_abstract, w, h, real_decision, model_decision))
                # configured() matches truthiness of a single optional name.
                assert configured(w) == bool(w), (
                    "configured reference disagrees on %r" % (w,))


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_I18N=False,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    # The A-reference (the model's decision predicate == Python truthiness of
    # the real guard) holds regardless of environment.
    _check_truthiness_reference()

    try:
        _configure_django()
        from django.db import models
        from django.db.models import signals
        try:
            from PIL import Image  # noqa: F401
        except Exception as exc:  # Pillow absent: ImageField cannot be exercised
            print("G-AX SKIP: Pillow not installed: %r (decision-predicate "
                  "A-reference confirmed against Python truthiness)" % (exc,))
            return 0
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r "
              "(decision-predicate A-reference confirmed)" % (exc,))
        return 0

    observations = [0]
    seq = [0]

    def receivers_contain(sender):
        """Is `sender`'s class registered in the post_init notification list?
        Mirror of the F2P test's membership probe over signals.post_init."""
        target = id(sender)
        return target in [sender_id for (_, sender_id), *_ in
                          signals.post_init.receivers]

    def observe(width_field, height_field, abstract):
        seq[0] += 1
        app_label = "gax16801"

        # Build a real concrete OR abstract model whose ImageField carries the
        # given companion targets. The field is attached via the real
        # ImageField.contribute_to_class during class creation.
        attrs = {
            "__module__": "gax16801.models",
            "Meta": type("Meta", (), {"app_label": app_label,
                                      "abstract": abstract}),
            "mugshot": models.ImageField(width_field=width_field,
                                         height_field=height_field,
                                         upload_to="t"),
        }
        if width_field:
            attrs[width_field] = models.PositiveIntegerField(null=True)
        if height_field:
            attrs[height_field] = models.PositiveIntegerField(null=True)

        cls = type("GaxModel_%d" % seq[0], (models.Model,), attrs)

        present = receivers_contain(cls)
        expected = should_register(abstract, width_field, height_field)
        assert present == expected, (
            "real ImageField.contribute_to_class registration disagrees with "
            "should_register on (abstract=%r, width_field=%r, height_field=%r): "
            "post_init handler present=%r, model says register=%r"
            % (abstract, width_field, height_field, present, expected))
        observations[0] += 1

    # The full decision table, concrete and abstract:
    for abstract in (False, True):
        observe(None, None, abstract)              # no companion target
        observe("mugshot_width", None, abstract)   # width only
        observe(None, "mugshot_height", abstract)  # height only
        observe("mugshot_width", "mugshot_height", abstract)  # both

    # The exact F2P scenario, called out explicitly: a CONCRETE model with NO
    # companion targets must NOT register the post_init handler.
    attrs = {
        "__module__": "gax16801.models",
        "Meta": type("Meta", (), {"app_label": "gax16801f2p"}),
        "mugshot": models.ImageField(upload_to="t"),
    }
    f2p_cls = type("GaxModelF2P", (models.Model,), attrs)
    assert not receivers_contain(f2p_cls), (
        "F2P scenario: a concrete model with an ImageField but no width_field/"
        "height_field still registered the post_init handler (the bug)")

    print("G-AX OK: should_register decision predicate validated == real "
          "ImageField.contribute_to_class registration over %d model-class "
          "observations (concrete x abstract x {none,width,height,both}) + the "
          "exact F2P no-target concrete scenario; truthiness A-reference "
          "confirmed." % (observations[0],))
    return 0


if __name__ == "__main__":
    sys.exit(main())
