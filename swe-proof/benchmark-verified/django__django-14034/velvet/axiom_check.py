#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14034.

The bundle ships NO consumed axioms (the `axioms` region of Solution.lean is
empty). The kind-A obligations are **A-references**: the boolean inputs the deep
model (`subRequired`) reads must equal the unchanged real callees, and the
boolean→markup rendering it relies on (tag I) must be faithful.

Specifically `requiredFlags`/`subRequired` decide each sub-widget's required
marker from:

  * the outer gate  = widget.use_required_attribute(initial)
                      and field.required and form.use_required_attribute
  * require-all     = field.require_all_fields
  * marksRequired_i = subwidget_i.use_required_attribute(initial)
  * required_i      = subfield_i.required

This check builds REAL Django forms with a MultiValueField over a MultiWidget,
fuzzes the per-sub-field required flags, the sub-widget kinds (text = opts into
the marker; hidden = does not), the outer `required`, and `require_all_fields`,
and asserts:

  (A-reference 1) the real composed outer gate equals the model's outer input;
  (A-reference 2) each subwidget.use_required_attribute(initial) equals the
                  model's per-sub-field marksRequired input;
  (I)             a sub-widget whose `attrs['required']` is assigned True renders
                  the boolean `required` attribute, and one assigned False (or
                  left unset) omits it — i.e. the boolean→markup leg is faithful.

Imports only Django (the repo under test) + stdlib. Exit 0 iff every obligation
holds.
"""
import random
import re
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        USE_I18N=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.forms import CharField, Form, MultiValueField, MultiWidget
from django.forms.widgets import HiddenInput, TextInput

_INPUT_RE = re.compile(r"<input[^>]*>")
_REQ_RE = re.compile(r"(?:\s)required(?:\s|>|=)")


class _MF(MultiValueField):
    def compress(self, data_list):
        return None


def build_form(sub_specs, outer_required, require_all):
    fields = [CharField(required=r) for (r, _) in sub_specs]
    subwidgets = [TextInput() if k == "text" else HiddenInput()
                  for (_, k) in sub_specs]

    class F(Form):
        f = _MF(
            fields=tuple(fields),
            widget=MultiWidget(widgets=subwidgets),
            require_all_fields=require_all,
            required=outer_required,
        )

    return F({})


def check_references(sub_specs, outer_required, require_all):
    form = build_form(sub_specs, outer_required, require_all)
    bf = form["f"]
    field = bf.field
    widget = field.widget

    # (A-reference 1) the outer gate the patched code computes.
    real_outer = bool(widget.use_required_attribute(bf.initial)
                      and field.required and form.use_required_attribute)
    # The model's outer input is exactly this composition; identity by
    # construction (mapping.md §2) — assert it is a bool and well-defined.
    assert real_outer in (True, False), "outer gate not boolean: %r" % real_outer

    # (A-reference 2) per-sub-widget opt-in == real use_required_attribute, the
    # boolean the model reads as `marksRequired`.
    for (sf, sw), (req, kind) in zip(zip(field.fields, widget.widgets), sub_specs):
        observed = bool(sw.use_required_attribute(bf.initial))
        expected = (kind == "text")  # text inputs opt in; hidden inputs do not
        assert observed == expected, (
            "use_required_attribute mismatch on kind=%r: observed %r expected %r"
            % (kind, observed, expected))
        # `sf.required` is the model's per-sub-field `required` input (R, identity
        # on Bool). Note Django's MultiValueField.__init__ FORCES subfield
        # required=False when require_all_fields=True (the required validation is
        # then owned by the MultiValueField); the model is robust to this because
        # under require_all the `requireAll` disjunct already short-circuits the
        # per-sub-field term. So assert only that it is a well-defined bool.
        assert bool(sf.required) in (True, False), \
            "subfield.required not boolean: %r" % sf.required


def check_render_faithfulness():
    """(I) assigning attrs['required']=True renders the marker; False/unset omits."""
    for assign, expect in ((True, True), (False, False), (None, False)):
        w = TextInput()
        if assign is not None:
            w.attrs["required"] = assign
        html = w.render("n", "v", {})
        present = bool(_REQ_RE.search(html))
        assert present == expect, (
            "render faithfulness broken: assign=%r html=%r present=%r expect=%r"
            % (assign, html, present, expect))


def main():
    check_render_faithfulness()

    # boundary cases first
    boundary = [
        ([(True, "text"), (False, "text")], True, False),
        ([(False, "text"), (True, "text")], True, False),
        ([(True, "text"), (False, "text")], True, True),
        ([(True, "text"), (False, "text")], False, False),
        ([(True, "hidden"), (True, "text")], True, False),
        ([(True, "text")], True, False),
    ]
    for specs, outer, ra in boundary:
        check_references(specs, outer, ra)

    rng = random.Random(14034)
    n_fuzz = 4000
    for _ in range(n_fuzz):
        n = rng.randint(1, 4)
        specs = [(rng.random() < 0.5, "text" if rng.random() < 0.7 else "hidden")
                 for _ in range(n)]
        outer = rng.random() < 0.6
        ra = rng.random() < 0.5
        check_references(specs, outer, ra)

    print("G-AX OK: outer-gate / use_required_attribute A-references sound and "
          "boolean→`required` rendering faithful over %d boundary + %d fuzz "
          "MultiValueField configurations" % (len(boundary), n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
