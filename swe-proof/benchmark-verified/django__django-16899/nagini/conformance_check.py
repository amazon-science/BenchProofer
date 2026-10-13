#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16899 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Acc) stripped. The impl is plain Python over
List[int]; the @Pure helpers (seg_* / diagnostic_message) are spec-side
PSeq constructs the impl does not call, so no PSeq shim is needed. There are
no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.contrib.admin.checks.BaseModelAdminChecks._check_readonly_fields_item`
called on a ModelAdmin instance. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable.

Type bridge (mapping.md section 2):
  * each string carrier (label, value, cls, model_label) is a List[int] of
    Unicode code points; real strings map via ord/chr.
  * the five constant prose markers [1..5] in the shadow output expand to the
    five literal fixed-prose pieces of the message template (the mapping.md
    marker<->literal bijection); all content code points are > 5 (the input
    alphabet is printable text, as in the real domain), so the expansion is
    unambiguous.
  * `resolves` is, per mapping.md, the disjunction of the four UNCHANGED
    resolution lookups (callable / attribute of the admin object / attribute
    of the model / declared model field). The bridge computes it by
    performing exactly those lookups on the real objects.
  * cls / model_label are the admin class name and the model's meta label;
    they are realized by a pool of dynamically created (ModelAdmin, Model)
    pairs with distinct names (real class names are Python identifiers, so
    the fuzz domain for these two carriers is identifier-shaped).
  * empty result <-> no diagnostic; one-element result <-> one diagnostic
    whose content is the message string (the wrapper's other fields are
    unchanged and out of scope).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz calls.
Pinned fuzz seed: 16899.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 16899
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def check_reference(label, value, cls, model_label, resolves):
    if resolves:
        ok = []  # type: list
        return ok
    result = []  # type: list
    result = result + [1]          # first fixed prose piece
    result = result + label        # label
    result = result + [2]          # second fixed prose piece
    result = result + value        # value
    result = result + [3]          # third fixed prose piece
    result = result + cls          # class name
    result = result + [4]          # fourth fixed prose piece
    result = result + model_label  # model label
    result = result + [5]          # fifth fixed prose piece
    return result


# --- bridge: marker <-> literal prose (mapping.md section 2 bijection) --------

MARKER_PROSE = {
    1: "The value of '",
    2: "' refers to '",
    3: "', which is not a callable, an attribute of '",
    4: "', or an attribute of '",
    5: "'.",
}


def to_codes(s):
    codes = [ord(ch) for ch in s]
    for c in codes:
        # content must not collide with the marker tokens; the real domain
        # (labels, attribute names, class names) is printable text
        assert c > 5, "input alphabet must avoid marker code points"
    return codes


def render(codes):
    """Expand a shadow output code-point list to the real message string."""
    return "".join(MARKER_PROSE[c] if c in MARKER_PROSE else chr(c)
                   for c in codes)


def real_resolves(admin_obj, field_name, field_does_not_exist):
    """The bridge for the boolean guard: the four UNCHANGED resolution
    lookups, exactly as mapping.md defines them."""
    if callable(field_name):
        return True
    if hasattr(admin_obj, field_name):
        return True
    if hasattr(admin_obj.model, field_name):
        return True
    try:
        admin_obj.model._meta.get_field(field_name)
        return True
    except field_does_not_exist:
        return False


def check_case(checker, admin_obj, field_does_not_exist, label, field_name):
    """Run shadow and oracle on one (admin object, field_name, label) input;
    return an error string on disagreement, else None."""
    resolves = real_resolves(admin_obj, field_name, field_does_not_exist)

    cls_s = admin_obj.__class__.__name__
    ml_s = admin_obj.model._meta.label
    # a callable reference has no string carrier; it only exercises the
    # resolving (empty-output) path, where the value content is immaterial
    value_s = field_name if isinstance(field_name, str) else ""

    shadow_out = check_reference(to_codes(label), to_codes(value_s),
                                 to_codes(cls_s), to_codes(ml_s), resolves)
    real_out = checker._check_readonly_fields_item(admin_obj, field_name,
                                                   label)

    ok_empty = (len(shadow_out) == 0) == (len(real_out) == 0)
    if not ok_empty or len(real_out) > 1:
        return ("DISAGREEMENT (emptiness/arity)\n"
                "  label=%r field_name=%r cls=%r model_label=%r resolves=%r\n"
                "  shadow=%r\n  real=%r"
                % (label, field_name, cls_s, ml_s, resolves,
                   render(shadow_out), real_out))
    if real_out:
        shadow_msg = render(shadow_out)
        real_msg = real_out[0].msg
        if shadow_msg != real_msg:
            return ("DISAGREEMENT (message)\n"
                    "  label=%r field_name=%r cls=%r model_label=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (label, field_name, cls_s, ml_s, shadow_msg, real_msg))
    return None


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.admin.apps.SimpleAdminConfig",
                "django.contrib.auth",
                "django.contrib.contenttypes",
            ],
            DATABASES={},
        )
        django.setup()
    from django.contrib import admin
    from django.contrib.admin.checks import BaseModelAdminChecks  # REAL
    from django.core.exceptions import FieldDoesNotExist
    from django.db import models

    checker = BaseModelAdminChecks()

    def make_admin(app_label, model_name, admin_name):
        model = type(model_name, (models.Model,), {
            "__module__": "conf_shadow_models",
            "title": models.CharField(max_length=100),
            "Meta": type("Meta", (), {"app_label": app_label}),
        })
        admin_cls = type(admin_name, (admin.ModelAdmin,), {})
        return admin_cls(model, admin.site)

    # pool of (ModelAdmin, Model) pairs -> varies the cls / model_label
    # carriers over identifier-shaped values, including the shapes the test
    # suite uses and short/long edges
    pool = [
        make_admin("admin_checks", "Song", "SongAdmin"),
        make_admin("admin_checks", "City", "CityInline"),
        make_admin("a", "M", "A"),
        make_admin("some_long_app_label", "AVeryLongModelName",
                   "AVeryLongModelNameAdmin"),
        make_admin("app1", "Thing", "ThingAdmin"),
        make_admin("app2", "Widget", "WidgetOptions"),
        make_admin("app_3", "Item_X", "Item_XAdmin"),
        make_admin("uni", "Modelo", "AdminC"),
    ]

    # names that resolve through each of the unchanged lookup routes
    resolving_names = [
        "title",          # declared model field
        "id",             # auto pk field
        "pk",             # model attribute
        "model",          # admin-object attribute
        "opts",           # admin-object attribute
        "get_queryset",   # admin-object attribute (method)
    ]

    boundary = [
        # (label, field_name) -- the shapes the test suite exercises + edges
        ("readonly_fields[1]", "nonexistent"),
        ("readonly_fields[0]", "i_dont_exist"),
        ("readonly_fields[0]", ""),                    # empty reference
        ("", "missing"),                               # empty label
        ("", ""),
        ("L", "V"),
        ("readonly_fields[10]", "field_with_underscores"),
        ("l'abel", "va'lue"),                          # apostrophes
        ("a%sb", "c%sd"),                              # percent in data
        ("é", "•"),                                    # non-ascii
        ("readonly_fields[2]", "café"),
        ("readonly_fields[0]", "no such attr"),        # space in name
    ] + [("readonly_fields[0]", n) for n in resolving_names]

    checked = 0
    for admin_obj in pool:
        for (lab, fn) in boundary:
            err = check_case(checker, admin_obj, FieldDoesNotExist, lab, fn)
            if err:
                print(err)
                return 1
            checked += 1
        # a callable reference resolves via the first lookup
        err = check_case(checker, admin_obj, FieldDoesNotExist,
                         "readonly_fields[0]", len)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    alphabet = list("abcdefghij ABC_.[]0123456789'%é•\"<>")

    def tok():
        n = rng.randint(0, 16)
        return "".join(rng.choice(alphabet) for _ in range(n))

    n_boundary = checked
    for _ in range(N_FUZZ):
        admin_obj = rng.choice(pool)
        lab = tok()
        # mostly free strings; sometimes a name known to resolve, so both
        # branches of the guard stay exercised
        fn = rng.choice(resolving_names) if rng.random() < 0.1 else tok()
        err = check_case(checker, admin_obj, FieldDoesNotExist, lab, fn)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real per-reference validator on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
