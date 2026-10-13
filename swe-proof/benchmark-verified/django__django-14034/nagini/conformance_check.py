#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14034 (nagini).

SHADOW: the impl region of model.py's `build_required_attrs`, copied VERBATIM
below with the contract calls (Requires/Ensures/Invariant) stripped, plus the
@Pure helper `constituent_marker` copied over as a plain function and the two
carrier classes (`Constituent`, `Result2`) with their contract lines removed.
No @ContractOnly callees exist in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.forms.boundfield.BoundField.build_widget_attrs` at /testbed with the
gate having applied patch.diff. Real forms/fields/widgets are built so that
every abstract input of the model is realized:

  * `widget_mark` / per-constituent widget marks: widget subclasses whose
    `use_required_attribute` returns a chosen bool (the model consumes only
    the truth value of that report — mapping.md §2).
  * `field_required`, `form_marks`, `field_disabled`: the field's `required`
    / `disabled` flags and the form-level `use_required_attribute` switch.
  * `is_partial_multi`: realized structurally by the field kind —
      - 'plain'        : an ordinary CharField (no per-constituent policy
                         attribute at all)            -> False
      - 'mvf_all'      : a MultiValueField whose per-constituent policy is
                         switched ON (all constituents mandatory together),
                         composite widget              -> False
      - 'mvf_partial'  : a MultiValueField whose per-constituent policy is
                         switched OFF, composite widget -> True
  * `subs`: the (subfield, subwidget) pairs of the composite field. The
    shadow's Constituent inputs are read back FROM the constructed real
    objects (subwidget's report, subfield's `required` flag) so the bridge
    is exact even where the field constructor normalizes subfield flags.

Output bridges (mapping.md §2):
  * aggregate slots: `attrs['required'] is True` <-> required_attr == 1,
    key absent <-> -1 (the method only ever assigns True at the aggregate
    level, so 0 never arises there); `attrs['disabled']` likewise.
  * per-constituent marker: subwidget.attrs['required'] True <-> 1,
    False <-> 0, key absent <-> -1.

Input domain (the model's Requires): fresh output slots (we pass a fresh
attrs dict and fresh widgets, so every marker starts unset), all five bools
free, any list of constituent (widget-mark, required) pairs. Boundary set:
the full 2^4 flag product for each field kind crossed with every constituent
configuration of length <= 2 (16 + 2*16*21 = 688 trials); fuzz draws flags
with a bias toward the guard-true region and 0..4 constituents. Total
100688 >= 1e5 Requires-satisfying inputs. Pinned fuzz seed: 14034.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import random
import sys

SEED = 14034
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            DATABASES={},
            INSTALLED_APPS=[],
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {},
            }],
        )
    django.setup()


# --- model.py carrier classes, contract lines stripped -------------------------

class Constituent:
    def __init__(self, widget_mark, field_required):
        self.widget_mark = widget_mark
        self.field_required = field_required
        self.marker = -1


class Result2:
    def __init__(self):
        self.required_attr = -1
        self.disabled_attr = -1


# --- @Pure helper from model.py, decorator + docstring kept, no contracts ------

def constituent_marker(widget_mark, field_required):
    if widget_mark and field_required:
        return 1
    return 0


# --- the impl region of model.py, verbatim (Invariant calls stripped) ----------

def build_required_attrs(out, widget_mark, field_required, form_marks,
                         is_partial_multi, field_disabled, subs):
    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1


# --- bridge: build the real repo objects for one abstract trial ----------------

def _widget_classes():
    """Widget subclasses whose mandatory report is a chosen constant, so each
    abstract bool input maps onto a real widget object."""
    from django.forms.widgets import MultiWidget, TextInput

    class MarkedTextInput(TextInput):
        def __init__(self, mark, attrs=None):
            super().__init__(attrs)
            self._mark = mark

        def use_required_attribute(self, initial):
            return self._mark

    class MarkedMultiWidget(MultiWidget):
        def __init__(self, mark, widgets, attrs=None):
            super().__init__(widgets, attrs)
            self._mark = mark

        def use_required_attribute(self, initial):
            return self._mark

    return MarkedTextInput, MarkedMultiWidget


def make_bound_field(spec, ctx):
    """spec = (widget_mark, field_required, form_marks, field_kind,
    field_disabled, sub_specs); sub_specs = tuple of (widget_mark,
    field_required) bool pairs (must be () for 'plain'). Returns the real
    BoundField, freshly constructed (all marker slots start unset)."""
    from django import forms
    wm, fr, fm, kind, dis, sub_specs = spec
    MarkedTextInput, MarkedMultiWidget = ctx

    if kind == 'plain':
        field = forms.CharField(required=fr, disabled=dis,
                                widget=MarkedTextInput(wm))
    else:
        subfields = tuple(forms.CharField(required=sfr) for _, sfr in sub_specs)
        subwidgets = [MarkedTextInput(swm) for swm, _ in sub_specs]
        field = forms.MultiValueField(
            fields=subfields,
            required=fr,
            disabled=dis,
            require_all_fields=(kind == 'mvf_all'),
            widget=MarkedMultiWidget(wm, subwidgets),
        )

    form = forms.Form()
    form.use_required_attribute = fm
    form.fields['f'] = field
    return form['f']


def tri_of_attrs(attrs, key):
    """Map a real attribute-dict slot onto the model's tri-state carrier."""
    if key not in attrs:
        return -1
    v = attrs[key]
    if v is True:
        return 1
    if v is False:
        return 0
    return ('non-bool', v)


# --- the differential check ----------------------------------------------------

def check_trial(spec, ctx):
    wm, fr, fm, kind, dis, sub_specs = spec

    # Real side: fresh objects, one call to the patched method.
    bf = make_bound_field(spec, ctx)
    field = bf.field
    real_attrs = bf.build_widget_attrs({})

    # Shadow side: abstract inputs read back FROM the constructed reality so
    # the bridge is exact (the composite field's constructor may normalize
    # its constituents' flags).
    is_partial_multi = (kind == 'mvf_partial')
    if kind == 'plain':
        subs = []
        real_pairs = []
    else:
        real_pairs = list(zip(field.fields, field.widget.widgets))
        subs = [Constituent(bool(sw.use_required_attribute(bf.initial)),
                            bool(sf.required))
                for sf, sw in real_pairs]
    out = Result2()
    build_required_attrs(out, bool(wm), bool(field.required), bool(fm),
                         is_partial_multi, bool(field.disabled), subs)

    want_req = tri_of_attrs(real_attrs, 'required')
    want_dis = tri_of_attrs(real_attrs, 'disabled')
    if out.required_attr != want_req or out.disabled_attr != want_dis:
        return ("DISAGREEMENT (aggregate slots)\n  input=%r\n"
                "  shadow=(required_attr=%r, disabled_attr=%r)\n"
                "  real  =(required=%r, disabled=%r) attrs=%r"
                % (spec, out.required_attr, out.disabled_attr,
                   want_req, want_dis, real_attrs))

    for k, (sf, sw) in enumerate(real_pairs):
        want_marker = tri_of_attrs(sw.attrs, 'required')
        if subs[k].marker != want_marker:
            return ("DISAGREEMENT (constituent %d marker)\n  input=%r\n"
                    "  shadow marker=%r\n  real subwidget attrs=%r -> %r"
                    % (k, spec, subs[k].marker, sw.attrs, want_marker))
    return None


def boundary_specs():
    bools = (False, True)
    specs = []
    # plain fields: full flag product, no constituents.
    for wm in bools:
        for fr in bools:
            for fm in bools:
                for dis in bools:
                    specs.append((wm, fr, fm, 'plain', dis, ()))
    # composite fields: both per-constituent policies x full flag product x
    # every constituent configuration of length <= 2.
    sub_cfgs = [()]
    sub_cfgs += [((a, b),) for a in bools for b in bools]
    sub_cfgs += [((a, b), (c, d)) for a in bools for b in bools
                 for c in bools for d in bools]
    for kind in ('mvf_partial', 'mvf_all'):
        for wm in bools:
            for fr in bools:
                for fm in bools:
                    for dis in bools:
                        for cfg in sub_cfgs:
                            specs.append((wm, fr, fm, kind, dis, cfg))
    return specs


def rand_spec(rng):
    # bias the guard bools toward True so both regimes are hit often
    # (uniform draws would leave the guard true only 1/8 of the time).
    wm = rng.random() < 0.65
    fr = rng.random() < 0.65
    fm = rng.random() < 0.65
    dis = rng.random() < 0.5
    kind = rng.choice(('plain', 'mvf_partial', 'mvf_partial', 'mvf_all'))
    if kind == 'plain':
        cfg = ()
    else:
        n = rng.randint(0, 4)
        cfg = tuple((rng.random() < 0.5, rng.random() < 0.5)
                    for _ in range(n))
    return (wm, fr, fm, kind, dis, cfg)


def main():
    _setup_django()
    ctx = _widget_classes()

    checked = 0
    boundary = boundary_specs()
    for spec in boundary:
        err = check_trial(spec, ctx)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        spec = rand_spec(rng)
        err = check_trial(spec, ctx)
        if err:
            print(err)
            return 1
        checked += 1

    import json
    print("G-CONF OK: shadow impl (build_required_attrs) == real patched "
          "attribute assembly on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
