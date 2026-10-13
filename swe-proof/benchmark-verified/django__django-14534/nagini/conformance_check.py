#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14534 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The @Pure helper `id_key` copies over as a plain function,
and `ChoiceContext` becomes a plain attribute carrier (its __init__ body is
the same three assignments with the Requires/Ensures removed). There are no
@ContractOnly callees and no PSeq usage in this bundle; the attribute mapping
is a plain dict, so no sequence shim is needed.

ORACLE: the REAL patched repo property the model models per mapping.md —
`django.forms.boundfield.BoundWidget.id_for_label`, the label-target
identifier a per-choice subwidget container reports. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched code importable. Each input constructs a genuine `BoundWidget` around
a per-option context dict (the object the property reads) and reads the
property; additionally the full genuine subwidget data path
(`form[field].subwidgets` across the three form configurations the tests pin,
plus fuzzed prefixes / choice counts) is driven so the structured production
of the context dict is covered too.

TYPE BRIDGE (mapping.md section 2): the model carries identifiers and
attribute keys as opaque int identity tokens and the absence of an identifier
as None. Per case, the real attribute mapping (string keys, string id value)
is bijected into the model carrier: the identifier-recording key maps to the
`id_key()` token, every other key to a fresh distinct token, and each value
to a fresh distinct value token (per-case registry). The shadow's Optional
token result maps back through the inverse registry and is compared `==`
against the real property's Optional[str] result, with an explicit
None/not-None kind check. The modeled domain records an identifier by key
PRESENCE with a real (non-None) value — mapping.md documents that bijection —
so inputs where the key is present but explicitly maps to None are outside
the Requires-satisfying domain and are not generated (and are skipped if the
genuine subwidget path were ever to produce one).

Input domain: the model's preconditions only require the carrier shape
(an attribute mapping plus name/index fields), so every context whose
attribute mapping either omits the identifier key or records a non-None
identifier is Requires-satisfying. Boundary cases cover: no attributes at
all, an identifier alone, an identifier among other attributes, the
empty-string identifier, identifiers resembling each generation scheme, and
attribute maps with only non-identifier keys.

>= 1e5 Requires-satisfying inputs: 8 boundary + 100000 direct fuzz contexts
+ the genuine subwidget-path cases. Pinned fuzz seed: 14534.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import string
import sys

SEED = 14534
N_FUZZ = 100_000


# --- pure helper from model.py, decorator stripped ----------------------------

def id_key():
    """The opaque attribute-mapping key under which a resolved identifier is
    recorded (the literal string key 'id' in the repository; an int token
    here)."""
    return 1


# --- carrier class from model.py, contracts stripped ---------------------------

class ChoiceContext:
    def __init__(self, attrs, name, index):
        self.attrs = attrs
        self.name = name
        self.index = index


# --- the impl region of model.py, verbatim -------------------------------------

def label_target_id(ctx):
    if id_key() in ctx.attrs:
        return ctx.attrs[id_key()]
    return None


# --- type bridge (mapping.md section 2) -----------------------------------------

REAL_ID_KEY = "id"  # the repo-side attribute-mapping key the id_key() token models


def bridge_attrs(real_attrs):
    """Biject a real attribute mapping into the model carrier.

    Returns (model_attrs, inverse) where model_attrs is the Dict[int, int]
    the shadow consumes and inverse maps value tokens back to the real
    values. Distinct real values get distinct tokens; the identifier key gets
    the id_key() token, other keys fresh distinct key tokens (never 1).
    """
    model_attrs = {}
    inverse = {}
    next_val_tok = 100
    next_key_tok = 2
    for k in sorted(real_attrs, key=repr):
        v = real_attrs[k]
        vtok = None
        for t, seen in inverse.items():
            if seen == v:
                vtok = t
                break
        if vtok is None:
            vtok = next_val_tok
            next_val_tok += 1
            inverse[vtok] = v
        if k == REAL_ID_KEY:
            model_attrs[id_key()] = vtok
        else:
            model_attrs[next_key_tok] = vtok
            next_key_tok += 1
    return model_attrs, inverse


def check_case(make_real, real_attrs, name, index, label):
    """Run the shadow (through the bridge) and the real property on one
    per-option context; return an error string on disagreement, else None."""
    if REAL_ID_KEY in real_attrs and real_attrs[REAL_ID_KEY] is None:
        # outside the modeled domain: an identifier is recorded by key
        # presence with a real value (mapping.md section 2 bijection)
        return None
    model_attrs, inverse = bridge_attrs(real_attrs)
    tok = label_target_id(ChoiceContext(model_attrs, 0, index))
    shadow_out = None if tok is None else inverse[tok]
    real_out = make_real(real_attrs, name, index)
    same_kind = (shadow_out is None) == (real_out is None)
    if not same_kind or shadow_out != real_out:
        return ("DISAGREEMENT [%s]\n  attrs=%r name=%r index=%r\n"
                "  shadow=%r\n  real=%r"
                % (label, real_attrs, name, index, shadow_out, real_out))
    return None


def boundary_attrs():
    return [
        {},                                   # nothing recorded
        {"id": "prefix_field_0"},             # custom-prefix style identifier
        {"id": "id_name_0"},                  # default-prefix style identifier
        {"id": "myCustomID"},                 # widget-level custom identifier
        {"class": "x"},                       # other attributes only
        {"id": "id_name_0", "class": "x"},    # identifier among other attrs
        {"id": ""},                           # empty-string identifier
        {"id": "0", "checked": True, "class": "c1 c2", "data-x": "y"},
    ]


def rand_attrs(rng):
    attrs = {}
    if rng.random() < 0.65:
        kind = rng.random()
        if kind < 0.4:
            attrs["id"] = "id_%s_%d" % (
                "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 8))),
                rng.randint(0, 30))
        elif kind < 0.7:
            attrs["id"] = "%s_%s_%d" % (
                "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 6))),
                "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 6))),
                rng.randint(0, 30))
        elif kind < 0.9:
            attrs["id"] = "".join(
                rng.choices(string.ascii_letters + string.digits + "_-.:",
                            k=rng.randint(0, 20)))
        else:
            attrs["id"] = str(rng.randint(0, 10 ** 6))
    for _ in range(rng.randint(0, 3)):
        k = rng.choice(["class", "checked", "required", "disabled",
                        "data-k%d" % rng.randint(0, 4)])
        attrs[k] = rng.choice(["x", "", True, "a b", str(rng.randint(0, 99))])
    return attrs


def main():
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

    # REAL patched callee: the per-choice subwidget container whose property
    # reports the label-target identifier.
    from django.forms.boundfield import BoundWidget
    from django.forms import (
        Form, ChoiceField, MultipleChoiceField,
        RadioSelect, Select, CheckboxSelectMultiple,
    )
    from django.forms.widgets import Select as SelectWidget

    parent = SelectWidget()

    def make_real(attrs, name, index):
        # A genuine BoundWidget around the per-option context dict, mirroring
        # the container built at BoundField.subwidgets time; the property only
        # reads the context, so the renderer is inert here.
        data = {
            "attrs": attrs,
            "name": name,
            "index": index,
            "value": "v",
            "label": "L",
            "selected": False,
            "type": parent.input_type if hasattr(parent, "input_type") else "select",
            "template_name": "django/forms/widgets/select_option.html",
            "wrap_label": True,
        }
        return BoundWidget(parent, data, None).id_for_label

    checked = 0
    for i, attrs in enumerate(boundary_attrs()):
        err = check_case(make_real, attrs, "field", i % 3, "boundary")
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        attrs = rand_attrs(rng)
        name = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(1, 8)))
        err = check_case(make_real, attrs, name, rng.randint(0, 50), "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    # --- the genuine subwidget data path (structured production of the
    # --- per-option context), across the three pinned form configurations
    # --- plus fuzzed prefixes / choice counts -----------------------------
    def build_subwidgets(widget_cls, choices, auto_id, multiple):
        field_cls = MultipleChoiceField if multiple else ChoiceField

        class SomeForm(Form):
            field = field_cls(choices=choices, widget=widget_cls)

        form = SomeForm(auto_id=auto_id)
        return list(form["field"].subwidgets)

    real_path = 0
    configs = [
        (CheckboxSelectMultiple, [("a", "A"), ("b", "B")], "prefix_%s", True),
        (RadioSelect, [("john", "John"), ("paul", "Paul")], True, False),
        (Select, [("john", "John"), ("paul", "Paul")], False, False),
    ]
    for _ in range(40):
        n = rng.randint(1, 6)
        choices = [("c%d" % i, "C%d" % i) for i in range(n)]
        auto_id = rng.choice([True, False, "p%d_%s" % (rng.randint(0, 9), "%s")])
        widget = rng.choice([RadioSelect, CheckboxSelectMultiple, Select])
        configs.append((widget, choices, auto_id,
                        widget is CheckboxSelectMultiple))
    for widget, choices, auto_id, multiple in configs:
        for sw in build_subwidgets(widget, choices, auto_id, multiple):
            data = sw.data
            err = check_case(lambda a, nm, ix, _sw=sw: _sw.id_for_label,
                             data["attrs"], data["name"], data["index"],
                             "subwidget-path auto_id=%r" % (auto_id,))
            if err:
                print(err)
                return 1
            checked += 1
            real_path += 1

    print("G-CONF OK: shadow impl == real reported label-target identifier "
          "on %d inputs (%d boundary + %d fuzz + %d genuine subwidget-path, "
          "seed %d)." % (checked, len(boundary_attrs()), N_FUZZ, real_path,
                         SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
