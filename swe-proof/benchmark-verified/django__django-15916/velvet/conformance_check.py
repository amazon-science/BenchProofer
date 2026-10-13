#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15916 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region
              (`selectFieldCallback`) transliterated to Python over the real
              repo configuration, via the mapping.md §2 bijection:
                  configCallback    <-> the callback the form's OWN Meta resolves
                                         to (its Meta.formfield_callback, taken
                                         directly when present on its Meta, else
                                         inherited through the Meta MRO)
                  declaredCallback  <-> attrs.get("formfield_callback") together
                                         with whether that key is present in the
                                         class body (`Option (Option Nat)`)
                  inheritedCallback <-> the first base form's
                                         Meta.formfield_callback (the base-scan)
              The modeled selection is simply `out = configCallback`. Callbacks
              are identified by an integer tag (`some n`) / absence (`none`);
              `none` is "no callback". There are NO A-tagged callees in the impl
              region (no axioms), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.forms.models.ModelFormMetaclass.__new__` applied at
              base_commit (the harness applies the gold patch before this runs).
              For each configuration we build a genuine `ModelForm` subclass and
              observe which callback actually built its fields — read off the
              produced widget class on `Form.base_fields[name].widget`, exactly
              what the F2P tests (`test_custom_callback_in_meta`,
              `test_custom_callback_from_base_form_meta`) assert.

They must agree on the selected callback for every configuration. Exit 0 iff
zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), Django
+ stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )
    django.setup()

from django import forms
from django.db import models

SEED = 15916
N_FUZZ = 100_000

# ---------------------------------------------------------------------------
# A model with a single, simple, editable field. The default ModelForm gives it
# a TextInput widget; any of our callbacks overrides the widget to a tagged
# class, so the widget class read off base_fields identifies which callback ran.
# ---------------------------------------------------------------------------


class _Person(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "contenttypes"   # borrow an installed app's registry


# A family of distinguishable callbacks. Tag n -> a callback that produces a
# CharField whose widget is _Widget[n]; tag is recoverable from the widget class.
_WIDGETS = [
    type("CB0Widget", (forms.Textarea,), {}),
    type("CB1Widget", (forms.Textarea,), {}),
    type("CB2Widget", (forms.Textarea,), {}),
]


def _make_callback(tag):
    w = _WIDGETS[tag]

    def callback(db_field, **kwargs):
        return forms.CharField(widget=w)

    return callback


_CALLBACKS = [_make_callback(0), _make_callback(1), _make_callback(2)]
# default widget (no callback) -> the model field's own formfield widget
_DEFAULT_WIDGET_CLASS = forms.CharField().widget.__class__  # TextInput


def _tag_of_widget_class(wc):
    """Recover the callback tag (or None) that produced a widget of class wc."""
    for i, w in enumerate(_WIDGETS):
        if issubclass(wc, w):
            return i
    return None


# ---------------------------------------------------------------------------
# SHADOW: Solution.lean selectFieldCallback transliterated.
#   out = configCallback   (the form's own Meta-resolved callback)
# ---------------------------------------------------------------------------


def shadow_select(config_callback, declared_callback, inherited_callback):
    """`selectFieldCallback` transliterated: the result is exactly the form's
    own configuration callback, ignoring class-body and parent offerings."""
    return config_callback


# ---------------------------------------------------------------------------
# ORACLE: build a real ModelForm subclass for a configuration and observe which
# callback built `name`'s field.
# ---------------------------------------------------------------------------


def _build_form(meta_cb_tag, declared_present, declared_tag, base_meta_cb_tag):
    """Construct a genuine ModelForm subclass through the real (patched)
    metaclass for one configuration, and return the callback tag that actually
    built the `name` field (None == no callback ran / default widget).

    * meta_cb_tag       : tag set on THIS form's own Meta.formfield_callback,
                          or None to leave it unset on this Meta.
    * declared_present  : whether the class body names `formfield_callback`.
    * declared_tag      : the value named there (a tag, or None == an explicit
                          "no callback") -- only meaningful if declared_present.
    * base_meta_cb_tag  : tag on a parent ModelForm's Meta.formfield_callback,
                          or None for no such parent contribution.
    """
    # Build form classes through the REAL metaclass of ModelForm (exactly as
    # modelform_factory does: `type(form)(name, bases, attrs)`), so the patched
    # ModelFormMetaclass.__new__ runs.
    meta_cls = type(forms.ModelForm)

    # Optional base form carrying a Meta.formfield_callback (the base-scan
    # source / the Meta-MRO inheritance source).
    if base_meta_cb_tag is not None:
        base_meta_attrs = {
            "model": _Person,
            "fields": "__all__",
            "formfield_callback": staticmethod(_CALLBACKS[base_meta_cb_tag]),
        }
        BaseMeta = type("Meta", (), base_meta_attrs)
        BaseForm = meta_cls("BaseForm", (forms.ModelForm,), {"Meta": BaseMeta})
        bases = (BaseForm,)
    else:
        bases = (forms.ModelForm,)

    # This form's own Meta. It inherits from the base form's Meta (mirroring how
    # a subclass's inner Meta inherits) so that, when this Meta omits the
    # callback, it resolves through the Meta MRO to the parent's.
    meta_parent = (bases[0].Meta,) if hasattr(bases[0], "Meta") else ()
    meta_attrs = {"model": _Person, "fields": "__all__"}
    if meta_cb_tag is not None:
        meta_attrs["formfield_callback"] = staticmethod(_CALLBACKS[meta_cb_tag])
    Meta = type("Meta", meta_parent, meta_attrs)

    attrs = {"Meta": Meta}
    if declared_present:
        if declared_tag is None:
            attrs["formfield_callback"] = None
        else:
            attrs["formfield_callback"] = staticmethod(_CALLBACKS[declared_tag])

    Form = meta_cls("NewForm", bases, attrs)
    widget_class = Form.base_fields["name"].widget.__class__
    return _tag_of_widget_class(widget_class)


def _config_callback_tag(meta_cb_tag, base_meta_cb_tag):
    """mapping.md §2: configCallback = the form's OWN Meta-resolved callback.
    When this form's Meta sets the callback, that wins; otherwise it inherits
    through the Meta MRO from the base form's Meta."""
    if meta_cb_tag is not None:
        return meta_cb_tag
    return base_meta_cb_tag   # inherited through the Meta MRO (or None)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(meta_cb_tag, declared_present, declared_tag, base_meta_cb_tag):
        nonlocal count
        count += 1
        config = _config_callback_tag(meta_cb_tag, base_meta_cb_tag)
        shadow = shadow_select(
            config,
            (declared_tag if declared_present else "ABSENT"),
            base_meta_cb_tag,
        )
        try:
            oracle = _build_form(meta_cb_tag, declared_present, declared_tag,
                                 base_meta_cb_tag)
        except Exception as e:  # pragma: no cover
            oracle = "ORACLE-EXC:%r" % e
        if shadow != oracle:
            disagreements.append(
                (meta_cb_tag, declared_present, declared_tag, base_meta_cb_tag,
                 shadow, oracle))

    tags = [None, 0, 1, 2]
    # --- boundary cases: the F2P scenarios + the full combination matrix -----
    # test_custom_callback_in_meta: own Meta callback, nothing else.
    check(0, False, None, None)
    # test_custom_callback_from_base_form_meta: base Meta callback, factory sets
    # class-body formfield_callback=None explicitly; own Meta inherits via MRO.
    check(None, True, None, 1)
    # full matrix over the four sources
    for meta_cb in tags:
        for base_cb in tags:
            for decl_present in (False, True):
                if decl_present:
                    for decl_tag in tags:
                        check(meta_cb, True, decl_tag, base_cb)
                else:
                    check(meta_cb, False, None, base_cb)

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        meta_cb = rng.choice(tags)
        base_cb = rng.choice(tags)
        decl_present = rng.random() < 0.5
        decl_tag = rng.choice(tags) if decl_present else None
        check(meta_cb, decl_present, decl_tag, base_cb)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for mc, dp, dt, bc, sh, orc in disagreements:
            print("  meta_cb=%r declared_present=%r declared_tag=%r "
                  "base_meta_cb=%r shadow=%r oracle=%r"
                  % (mc, dp, dt, bc, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectFieldCallback agrees with the real "
          "patched ModelFormMetaclass on %d configurations (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
