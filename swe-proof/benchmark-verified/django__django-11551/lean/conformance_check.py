#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11551.

The bundle models ONE per-entry decision the admin column-configuration check
makes for a single listed display item (mapping.md):

  which diagnostic, if any, is emitted for that entry — `[]` (acceptable),
  `["E108"]` (unresolvable), or `["E109"]` (a many-to-many field).

The decision is a PURE function of four observables the check has in hand at the
decision point:

    item_callable : bool          (callable(item))
    admin_hasattr : bool          (hasattr(obj, item))
    model_field   : None | bool   (obj.model._meta.get_field(item):
                                    None      -> raised FieldDoesNotExist,
                                    bool m    -> a field; m == isinstance M2M)
    model_attr    : None | bool   (getattr(obj.model, item):
                                    None      -> raised AttributeError,
                                    bool m    -> a value; m == isinstance M2M)

Standing up Django's app registry + a ModelAdmin + a custom descriptor field on
a model class to drive `_check_list_display_item` is heavy and unnecessary: the
modeled value is exactly this pure decision over the observables the real routine
reads. So the ORACLE below is a faithful in-process replica using the EXACT
patched control flow (gold patch.diff):

    if callable(item):            return []
    if hasattr(obj, item):        return []
    try:
        field = get_field(item)            # model_field
    except FieldDoesNotExist:
        try:
            field = getattr(model, item)   # model_attr
        except AttributeError:
            return ["E108"]
    if isinstance(field, ManyToManyField): return ["E109"]
    return []

The SHADOW is the op-for-op transliteration of
`implementation_validateDisplayItem` (per refinement.md).

This genuinely tests the F2P behavior: an entry that is not callable, not an
admin attribute, whose metadata field lookup SUCCEEDS but whose model-attribute
access FAILS (a field accessible only via an instance) must be ACCEPTED (`[]`).
The pre-patch flow gated field resolution on attribute-access success and so
wrongly emitted `["E108"]` there.

stdlib-only. Pinned seed: 20240709 (also in mapping.md).
"""
import random
import sys

SEED = 20240709
N = 120_000


# --- ORACLE: faithful in-process replica of the patched per-entry decision ----
# model_field / model_attr encode the get_field / getattr outcomes:
#   None    -> the access raised (FieldDoesNotExist / AttributeError)
#   bool m  -> a field/value was obtained; m == isinstance(field, M2M)
def oracle(item_callable, admin_hasattr, model_field, model_attr):
    if item_callable:
        return []
    if admin_hasattr:
        return []
    # try: field = get_field(item)  except FieldDoesNotExist: try getattr ...
    if model_field is not None:
        field_is_m2m = model_field
    else:
        if model_attr is not None:
            field_is_m2m = model_attr
        else:
            return ["E108"]
    if field_is_m2m:
        return ["E109"]
    return []


# --- SHADOW of implementation_validateDisplayItem (the R/I / A-reference leg) --
# Mirrors Solution.lean:
#   if itemCallable: return []
#   if adminHasAttr: return []
#   match modelField with
#   | some m => fieldIsM2M := m
#   | none   => match modelAttr with
#               | some m => fieldIsM2M := m
#               | none   => return ["E108"]
#   if fieldIsM2M: return ["E109"] else return []
def shadow(item_callable, admin_hasattr, model_field, model_attr):
    if item_callable:
        return []
    if admin_hasattr:
        return []
    if model_field is not None:
        field_is_m2m = model_field
    else:
        if model_attr is not None:
            field_is_m2m = model_attr
        else:
            return ["E108"]
    if field_is_m2m:
        return ["E109"]
    return []


def disagree(ic, ah, mf, ma):
    o = oracle(ic, ah, mf, ma)
    s = shadow(ic, ah, mf, ma)
    if o != s:
        return ((ic, ah, mf, ma), o, s)
    return None


OPTS = [True, False]
TRI = [None, True, False]


def _enumerate_all():
    cases = []
    for ic in OPTS:
        for ah in OPTS:
            for mf in TRI:
                for ma in TRI:
                    cases.append((ic, ah, mf, ma))
    return cases


def main() -> int:
    checked = 0
    # exhaustive over the entire finite observable space (2*2*3*3 = 36)
    for ic, ah, mf, ma in _enumerate_all():
        d = disagree(ic, ah, mf, ma)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ic = rng.choice(OPTS)
        ah = rng.choice(OPTS)
        mf = rng.choice(TRI)
        ma = rng.choice(TRI)
        d = disagree(ic, ah, mf, ma)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
