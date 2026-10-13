#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15467 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (the key token and the
two distinguished label codes) copy over as plain functions. There are no
@ContractOnly callees in this bundle (mapping.md section 3).

ORACLE: the REAL patched repo path the model models per mapping.md — the
branch of ``django.contrib.admin.options.ModelAdmin.formfield_for_foreignkey``
taken when the relation is configured for radio rendering, which decides the
empty-choice entry of the accumulated keyword mapping. The gate applies the
patch to /testbed before this script runs; the script only imports and drives
the patched code. The observable is the keyword mapping as forwarded to the
field-construction call (mapping.md section 2, last row): the forwarding
callee on the field object is replaced per call by a capturing shim so the
mapping's post-state is read off exactly at the forwarding boundary.

Type bridge (mapping.md section 2):
  * ``permits_empty`` <-> the relation's permits-empty boolean. Realised by
    two real relation fields on one host model, one declared permitting the
    empty selection and one not; the flag picks which field is driven.
  * the mapping ``Dict[int, int]``: key 1 <-> the empty-choice key string;
    any other key code k <-> an inert extra keyword name ("x<k>") that the
    driven branch neither reads nor writes. Value codes: 0 <-> None (the
    absent sentinel), 2 <-> the built-in default empty-choice label (compared
    via its text), 3 <-> "" (a falsy caller label), 4 <-> the integer 0 (a
    falsy non-string caller label), any other code c <-> a unique marker
    object carrying c (an arbitrary caller label, read back verbatim —
    lowered by identity of the marker, so "kept verbatim" is checked as
    object identity, not mere equality).
  * the widget entry the enclosing branch also assigns is selection context
    (mapping.md section 1), not part of the modeled assignment; it is dropped
    when lowering the captured mapping.

Input domain: the precondition demands only a writable mapping; every
generated (permits_empty, kwargs) pair satisfies it. Generation stresses the
discriminating boundary: the empty-choice key present with falsy values
("" / 0 / None-as-deliberate-choice) and with the value equal to the built-in
default, key absent, both flag polarities, plus inert extra keys to show the
update is key-local.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 154670.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 154670
N_FUZZ = 100000


# --- pure helpers from model.py, contracts stripped ---------------------------

def empty_label_key():
    # The distinguished mapping key holding the empty-choice label.
    return 1


def absent_label():
    # The sentinel stored when no empty choice is offered (the relation does
    # not permit the empty selection). Distinct from every real label.
    return 0


def default_label():
    # The built-in default empty-choice label, used only when the relation
    # permits the empty selection and the caller supplied no label. Distinct
    # from the absent sentinel.
    return 2


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def set_radio_empty_label(permits_empty, kwargs):
    if permits_empty:
        if empty_label_key() in kwargs:
            value = kwargs[empty_label_key()]
        else:
            value = default_label()
    else:
        value = absent_label()
    kwargs[empty_label_key()] = value
    return value


# --- value bridge --------------------------------------------------------------

class Label(object):
    """Unique caller-label marker carrying its int code; lowered by identity."""
    __slots__ = ("code",)

    def __init__(self, code):
        self.code = code

    def __repr__(self):
        return "Label(%d)" % self.code


EMPTY_KEY_NAME = "empty_label"
DEFAULT_TEXT = "None"  # text of the built-in default empty-choice label


def lift_value(code, markers):
    """int value code -> real label value (mapping.md section 2)."""
    if code == 0:
        return None
    if code == 2:
        return DEFAULT_TEXT          # caller supplies exactly the default text
    if code == 3:
        return ""                    # falsy string label
    if code == 4:
        return 0                     # falsy non-string label
    m = Label(code)
    markers.append(m)
    return m


def lower_value(value, markers):
    """real label value -> int value code; None on an unbridgeable value."""
    if value is None:
        return 0
    if isinstance(value, Label):
        # verbatim retention must be the very object the caller supplied
        if not any(value is m for m in markers):
            return None
        return value.code
    if isinstance(value, int) and not isinstance(value, bool):
        return 4 if value == 0 else None
    text = str(value)                # tolerant of lazy-translation proxies
    if text == DEFAULT_TEXT:
        return 2
    if text == "":
        return 3
    return None


def lift_kwargs(model_kwargs, markers):
    real = {}
    for k, v in model_kwargs.items():
        name = EMPTY_KEY_NAME if k == empty_label_key() else ("x%d" % k)
        real[name] = lift_value(v, markers)
    return real


def lower_kwargs(real_kwargs, markers):
    """Captured mapping -> model carrier; the widget entry the enclosing
    branch assigns is selection context and is dropped. Returns (dict, err)."""
    model = {}
    for name, v in real_kwargs.items():
        if name == "widget":
            continue
        if name == EMPTY_KEY_NAME:
            k = empty_label_key()
        elif name.startswith("x"):
            k = int(name[1:])
        else:
            return None, "unexpected key %r in captured mapping" % name
        code = lower_value(v, markers)
        if code is None:
            return None, "unbridgeable value %r at key %r" % (v, name)
        model[k] = code
    return model, None


# --- oracle plumbing -----------------------------------------------------------

def build_oracle():
    """Configure Django minimally, declare a host model with two relation
    fields (one permitting the empty selection, one not), both configured for
    radio rendering on the admin object. Returns (admin_obj, field_by_flag)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.contrib import admin
    from django.contrib.admin.sites import AdminSite
    from django.db import models

    class ConfTarget(models.Model):
        class Meta:
            app_label = "contenttypes"

    class ConfHost(models.Model):
        rel_optional = models.ForeignKey(
            ConfTarget, models.CASCADE, blank=True, null=True,
            related_name="conf_opt")
        rel_mandatory = models.ForeignKey(
            ConfTarget, models.CASCADE, blank=False,
            related_name="conf_req")

        class Meta:
            app_label = "contenttypes"

    class ConfAdmin(admin.ModelAdmin):
        radio_fields = {
            "rel_optional": admin.VERTICAL,
            "rel_mandatory": admin.VERTICAL,
        }

    admin_obj = ConfAdmin(ConfHost, AdminSite())
    field_by_flag = {
        True: ConfHost._meta.get_field("rel_optional"),
        False: ConfHost._meta.get_field("rel_mandatory"),
    }
    return admin_obj, field_by_flag


_CAPTURE_SENTINEL = object()


def call_real(admin_obj, db_field, real_kwargs):
    """Drive the real patched branch; capture the keyword mapping at the
    field-construction forwarding boundary (the observable per mapping.md)."""
    captured = {}

    def capture(**kw):
        captured.update(kw)
        return _CAPTURE_SENTINEL

    db_field.formfield = capture     # instance attribute shadows the method
    try:
        rv = admin_obj.formfield_for_foreignkey(db_field, None, **real_kwargs)
    finally:
        del db_field.formfield
    if rv is not _CAPTURE_SENTINEL:
        raise RuntimeError("capture shim was not the forwarding callee")
    return captured


# --- differential driver ---------------------------------------------------------

def check_one(admin_obj, field_by_flag, permits_empty, model_kwargs):
    """One input pair; returns an error string on disagreement, else None."""
    markers = []
    real_kwargs = lift_kwargs(model_kwargs, markers)

    shadow_kwargs = dict(model_kwargs)
    shadow_result = set_radio_empty_label(permits_empty, shadow_kwargs)

    captured = call_real(admin_obj, field_by_flag[permits_empty], real_kwargs)
    real_lowered, err = lower_kwargs(captured, markers)
    if err:
        return ("BRIDGE ERROR on permits_empty=%r kwargs=%r: %s\n"
                "  captured mapping = %r"
                % (permits_empty, model_kwargs, err, captured))

    if real_lowered != shadow_kwargs:
        return ("DISAGREEMENT (mapping post-state) on permits_empty=%r "
                "kwargs=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (patched repo, lowered) = %r  [captured %r]"
                % (permits_empty, model_kwargs, shadow_kwargs,
                   real_lowered, captured))
    if real_lowered.get(empty_label_key()) != shadow_result:
        return ("DISAGREEMENT (returned entry) on permits_empty=%r "
                "kwargs=%r:\n"
                "  shadow result = %r\n"
                "  real entry (lowered) = %r"
                % (permits_empty, model_kwargs, shadow_result,
                   real_lowered.get(empty_label_key())))
    return None


def boundary_cases():
    """(permits_empty, model_kwargs) pairs on the discriminating boundary."""
    cases = []
    K = empty_label_key()
    for pe in (True, False):
        cases.append((pe, {}))                       # key absent, no extras
        cases.append((pe, {K: 7}))                   # caller label present
        cases.append((pe, {K: 0}))                   # caller stores the absent code
        cases.append((pe, {K: 2}))                   # caller stores the default text
        cases.append((pe, {K: 3}))                   # falsy string label kept?
        cases.append((pe, {K: 4}))                   # falsy non-string label kept?
        cases.append((pe, {K: 1}))                   # value colliding with key token
        cases.append((pe, {K: -6}))                  # negative caller code
        cases.append((pe, {5: 9}))                   # extra key only, target absent
        cases.append((pe, {K: 7, 5: 9, 6: 0}))       # target + inert extras
        cases.append((pe, {5: 3, 6: 4, 7: 2}))       # falsy-ish extras, target absent
    return cases


def main():
    try:
        admin_obj, field_by_flag = build_oracle()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: oracle setup failed: %r" % (exc,))
        return 1

    checked = 0
    boundary = boundary_cases()
    for permits_empty, model_kwargs in boundary:
        err = check_one(admin_obj, field_by_flag, permits_empty, model_kwargs)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        permits_empty = rng.random() < 0.5
        model_kwargs = {}
        if rng.random() < 0.6:                       # key present ~60%
            model_kwargs[empty_label_key()] = rng.choice(
                [0, 2, 3, 4, rng.randint(-8, 40), rng.randint(41, 10 ** 6)])
        for _extra in range(rng.randint(0, 3)):      # inert extra entries
            model_kwargs[rng.randint(5, 20)] = rng.choice(
                [0, 2, 3, 4, rng.randint(-8, 10 ** 6)])
        err = check_one(admin_obj, field_by_flag, permits_empty, model_kwargs)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched empty-choice decision on "
          "%d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
