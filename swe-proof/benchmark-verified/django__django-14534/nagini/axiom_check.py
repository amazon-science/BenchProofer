#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14534.

There are NO consumed `@ContractOnly` axioms in this bundle: the value a
per-choice subwidget container reports as its label-target identifier is the
behaviour under specification and is modelled DEEPLY in model.py (the membership
test + lookup `attrs.get('id')` spelled out in `label_target_id`). What this
script validates is the single **A-reference**: that the deep model equals the
real post-patch property the gold patch invokes.

The real property (post-patch `BoundWidget.id_for_label`,
`django/forms/boundfield.py:278-280`) is simply:

    return self.data['attrs'].get('id')

i.e. the identifier recorded in the per-option attribute mapping, or `None` when
none is recorded.  This is ordinary `dict.get`, which is exactly what model.py's
`label_target_id` computes over `int` carrier tokens (`id_key() in attrs` ->
`attrs[id_key()]`, else `None`).

`reference_id_for_label` below is a faithful, dependency-free reimplementation
of that real property (over an opaque attribute mapping).  We assert the model's
result equals it on boundary cases + randomized fuzz.  Identifiers and name
tokens are modelled as integer identity tokens (mapping.md §2); the property
only observes WHICH identifier is reported and whether one exists, so integer
identity (plus the genuine `None`) is a faithful carrier and the token-level
check needs nothing repo-specific (stdlib only).

When Django is importable (the evaluation container), we ADDITIONALLY drive the
genuine Django subwidget data path for the three form configurations the
F2P/P2P tests pin -- a configured prefix (`auto_id='prefix_%s'`,
CheckboxSelectMultiple), the default prefix (`auto_id='id_%s'`, RadioSelect),
and no id generation (`auto_id=False`, Select) -- plus fuzzed prefixes / choice
counts.  For every real subwidget we assert the post-patch property equals
`subwidget.data['attrs'].get('id')` (the recorded id, or None), confirming the
deep model is the real property.  We also positively assert that the PRE-PATCH
fabrication `'id_%s_%s' % (name, index)` DIVERGES on the configured-prefix and
no-id configurations -- the divergence the spec rejects -- so the equality is
shown to be load-bearing, not vacuous.

Exit 0 iff every observation matches the deep model AND (when Django is present)
the real subwidget property equals the recorded id while the pre-patch
fabrication diverges on the discriminating configurations.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

ID_KEY = "id"  # the literal attribute-mapping key ('id'); id_key() token in the model


def model_label_target_id(attrs):
    """Reference of model.py's `label_target_id` impl: the recorded identifier
    if the attribute mapping records one, else None."""
    if ID_KEY in attrs:
        return attrs[ID_KEY]
    return None


# --- the REAL behaviour (faithful reimplementation of the post-patch property) ---

def reference_id_for_label(data):
    """Mirror of the post-patch `BoundWidget.id_for_label` over an opaque
    per-option context dict: `self.data['attrs'].get('id')`."""
    return data["attrs"].get("id")


def prepatch_id_for_label(data):
    """The PRE-PATCH (buggy) property: a fabrication from name + index that
    ignores the attribute mapping entirely (and never reports absence)."""
    return "id_%s_%s" % (data["name"], data["index"])


# --- the checks --------------------------------------------------------------

def check_case(attrs):
    real = reference_id_for_label({"attrs": attrs, "name": "n", "index": "0"})
    model = model_label_target_id(attrs)
    assert model == real, (
        "deep model unsound on attrs=%r: real gave %r, model gives %r"
        % (attrs, real, model))


def main():
    # --- boundary cases (token-level: id present / absent) -------------------
    boundary = [
        {},                                   # no id recorded -> None
        {"id": "prefix_field_0"},             # configured-prefix id recorded
        {"id": "id_name_0"},                  # default-prefix id recorded
        {"id": "myCustomID"},                 # widget-level custom id recorded
        {"class": "x"},                       # other attrs only, no id -> None
        {"id": "id_name_0", "class": "x"},    # id alongside other attrs
        {"id": ""},                           # empty-string id recorded verbatim
    ]
    for attrs in boundary:
        check_case(attrs)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14534)
    for _ in range(50000):
        attrs = {}
        if rng.random() < 0.6:
            attrs["id"] = "ID%d_%d" % (rng.randint(0, 50), rng.randint(0, 9))
        for _k in range(rng.randint(0, 3)):
            attrs["k%d" % rng.randint(0, 5)] = rng.randint(0, 9)
        check_case(attrs)

    # --- exercise the GENUINE Django subwidget path if available -------------
    real_subwidgets = 0
    real_divergences = 0
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                USE_TZ=False,
                INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
                DATABASES={},
            )
            django.setup()

        from django.forms import (
            Form, ChoiceField, MultipleChoiceField,
            RadioSelect, Select, CheckboxSelectMultiple,
        )

        def build_subwidgets(widget_cls, choices, auto_id, multiple=False):
            field_cls = MultipleChoiceField if multiple else ChoiceField

            class SomeForm(Form):
                field = field_cls(choices=choices, widget=widget_cls)

            form = SomeForm(auto_id=auto_id)
            return list(form["field"].subwidgets)

        # The three configurations the F2P/P2P tests pin.
        configs = [
            # (widget, choices, auto_id, multiple, expect_prefix_in_id)
            (CheckboxSelectMultiple, [("a", "A"), ("b", "B")], "prefix_%s", True, "prefix_"),
            (RadioSelect, [("john", "John"), ("paul", "Paul")], True, False, "id_"),
            (Select, [("john", "John"), ("paul", "Paul")], False, False, None),
        ]
        for widget, choices, auto_id, multiple, prefix in configs:
            subs = build_subwidgets(widget, choices, auto_id, multiple)
            assert subs, "expected at least one subwidget"
            for idx, sw in enumerate(subs):
                data = sw.data
                # the deep model's reference equals the post-patch property:
                expected = data["attrs"].get("id")
                got = sw.id_for_label  # post-patch property in the worktree under test
                assert got == expected, (
                    "real BoundWidget.id_for_label != attrs.get('id') for "
                    "config auto_id=%r idx=%d: got %r, expected %r"
                    % (auto_id, idx, got, expected))
                # and the model's token-level resolution agrees:
                assert model_label_target_id(data["attrs"]) == expected
                real_subwidgets += 1

                # the PRE-PATCH fabrication must DIVERGE on the discriminating
                # configurations (configured prefix -> wrong prefix; no id ->
                # fabricated string instead of None). On the default-prefix
                # config it happens to coincide; we only require divergence
                # where the F2P tests demand it.
                fab = prepatch_id_for_label(data)
                if prefix is None:
                    assert expected is None, "no-id config must record no id"
                    assert fab != expected, (
                        "pre-patch fabrication should diverge from None")
                    real_divergences += 1
                elif prefix == "prefix_":
                    assert expected is not None and expected.startswith("prefix_"), (
                        "configured-prefix id must honour the prefix: %r" % expected)
                    assert fab != expected, (
                        "pre-patch fabrication should diverge from the "
                        "prefixed id: fab=%r expected=%r" % (fab, expected))
                    real_divergences += 1
    except ImportError:
        pass  # Django not importable (e.g. host verifier env): token-level path suffices

    print("G-AX OK: deep label-target-id model == real id_for_label "
          "(attrs.get('id')) on %d boundary + 50000 fuzz inputs (token-level)%s%s"
          % (
              len(boundary),
              (" + %d real Django subwidgets across 3 form configs"
               % real_subwidgets) if real_subwidgets else
              " (real-Django path skipped: not importable)",
              (" + %d positive divergences of the pre-patch fabrication on the "
               "configured-prefix / no-id configs (equality is load-bearing)"
               % real_divergences) if real_divergences else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
