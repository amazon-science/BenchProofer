#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14608 (nagini).

SHADOW: the impl region of `finish_group_clean` from model.py, copied VERBATIM
below with the contract calls stripped (the impl region contains only
`Invariant(...)` calls inside the copy loop — those lines are removed; every
other statement is byte-identical). The @Pure helpers (`generic_class`,
`nonform_tag`, `class_attr`) copy over as plain functions with `PSeq` shimmed
to a plain tuple. `MessageCollection` becomes a plain two-field class. There
are no @ContractOnly callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo step the model models per mapping.md section 1 —
`django.forms.formsets.BaseFormSet.full_clean`, specifically the post-state of
the group-wide message collection `self._non_form_errors` (its rendered class
attribute `.error_class` and its held messages) after the whole-clean step.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable. Each input drives one
fresh bound formset through `full_clean` (via `non_form_errors()`, which
triggers it) and reads the collection's two observed fields.

Control-flag bridge (mapping.md sections 1-2):
  - `rejected` <-> whether the cross-form-validation try block raised; driven
    here by a `clean()` override that raises with a chosen message list (the
    same handler the built-in max/min checks reach — a few boundary witnesses
    drive it through `validate_max`/`validate_min` too).
  - `rejection_messages: List[int]` <-> the raised exception's message list,
    element-for-element; the bijection carries each abstract int id `k` as the
    concrete message string "m<k>" (order- and multiplicity-preserving), so
    shadow items and real held messages compare positionally through it.
  - `group_flagged` <-> whether the management form failed validation (driven
    by handing it a non-numeric count field), causing the unchanged append of
    exactly one group-wide message before the try block.
  - `group_message` (int) <-> that single appended message, carried
    structurally (count/identity, not text — mapping.md section 1): on that
    path the shadow must hold exactly `[group_message]` and the real
    collection exactly one message.
  - `collection.css_class: List[int]` of code points <-> the real
    collection's `.error_class` str: `''.join(chr(c) ...) == error_class`.

Input domain: the model's Requires place no constraint beyond types —
any bools, any int `group_message`, any `List[int]` of message ids is
Requires-satisfying. Boundary cases enumerate every flag combination with
message lists of assorted shapes (empty, singleton, duplicates, long,
negative/large ids); fuzz draws flags uniformly and 0..8 ids of mixed
magnitude.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz values.
Pinned fuzz seed: 14608.

Exit 0 iff zero disagreements; on disagreement prints the input and both
post-states and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14608
N_FUZZ = 100_000


# --- PSeq shim + pure helpers from model.py (decorators stripped) --------------

def PSeq(*args):
    return tuple(args)


def generic_class():
    # 'errorlist' — the generic list class every such collection carries.
    return PSeq(101, 114, 114, 111, 114, 108, 105, 115, 116)


def nonform_tag():
    # 'nonform' — the marker tag distinguishing group-wide messages.
    return PSeq(110, 111, 110, 102, 111, 114, 109)


def class_attr(tag):
    """The rendered class attribute the collection constructor produces from an
    optional marker tag: an empty tag yields just the generic class; a non-empty
    tag `t` yields the generic class, a single space (U+0020), then `t`."""
    if len(tag) == 0:
        return generic_class()
    return generic_class() + PSeq(32) + tag


# --- MessageCollection shim (contracts stripped) --------------------------------

class MessageCollection:
    def __init__(self, css_class, items):
        self.css_class = css_class
        self.items = items


# --- the impl region of model.py, verbatim (Invariant lines stripped) ----------

def finish_group_clean(collection, group_flagged, group_message,
                       rejected, rejection_messages):
    # init site: rebuild the collection empty, with the marker tag.
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        # a single group-wide message is appended to the collection before the
        # rejection check (the collection is NOT rebuilt here, so the marker
        # class set at the init site is preserved).
        collection.items = collection.items + [group_message]
    if rejected:
        # rejection site: rebuild the collection from the rejection messages,
        # again with the marker tag (this replaces any earlier group-wide
        # message held in the collection).
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end (shadow)


# --- oracle drivers --------------------------------------------------------------

def _msg(mid):
    """The id <-> message-string bijection carrying an abstract int message id
    as concrete message content (order/multiplicity preserving)."""
    return "m%d" % (mid,)


def real_post_state(forms_mod, ValidationError, group_flagged, rejected,
                    rejection_ids):
    """Drive one fresh bound formset through the real whole-clean step and
    return (error_class_str, held_message_strings)."""
    class OneForm(forms_mod.Form):
        name = forms_mod.CharField(required=False)

    Base = forms_mod.formset_factory(OneForm)
    msgs = [_msg(k) for k in rejection_ids]

    class FS(Base):
        def clean(self):
            if rejected:
                raise ValidationError([ValidationError(m) for m in msgs])

    data = {
        'form-TOTAL_FORMS': '1',
        # a non-numeric count makes the management form fail validation,
        # driving the unchanged single group-wide-message append.
        'form-INITIAL_FORMS': 'x' if group_flagged else '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-name': 'a',
    }
    fs = FS(data)
    el = fs.non_form_errors()   # triggers the whole-clean step
    return el.error_class, [str(m) for m in el]


def check_case(forms_mod, ValidationError, group_flagged, group_message,
               rejected, rejection_ids):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    coll = MessageCollection([], [])
    finish_group_clean(coll, group_flagged, group_message, rejected,
                       list(rejection_ids))
    shadow_class = ''.join(chr(c) for c in coll.css_class)
    real_class, real_items = real_post_state(
        forms_mod, ValidationError, group_flagged, rejected, rejection_ids)

    ok = shadow_class == real_class
    if ok:
        if rejected:
            # element-for-element through the id<->string bijection.
            ok = [_msg(k) for k in coll.items] == real_items
        elif group_flagged:
            # structural carry: exactly one group-wide message on both sides,
            # the shadow holding exactly its abstract id.
            ok = coll.items == [group_message] and len(real_items) == 1
        else:
            ok = coll.items == [] and real_items == []
    if not ok:
        return ("DISAGREEMENT\n"
                "  input: group_flagged=%r group_message=%r rejected=%r "
                "rejection_ids=%r\n"
                "  shadow: css_class=%r items=%r\n"
                "  real:   error_class=%r items=%r"
                % (group_flagged, group_message, rejected, rejection_ids,
                   shadow_class, coll.items, real_class, real_items))
    return None


def check_builtin_raise_case(forms_mod, kind):
    """Extra witnesses: drive the SAME exception assignment site through the
    repo's own count checks (instead of a clean() override). The raised
    message text is repo-produced, so the items bridge here is structural
    (one message); the class attribute compares exactly."""
    class OneForm(forms_mod.Form):
        name = forms_mod.CharField(required=False)

    if kind == "max":
        FS = forms_mod.formset_factory(OneForm, max_num=1, validate_max=True)
        total = 2
    else:
        FS = forms_mod.formset_factory(OneForm, min_num=2, validate_min=True)
        total = 1
    data = {
        'form-TOTAL_FORMS': str(total),
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
    }
    for i in range(total):
        data['form-%d-name' % i] = 'a'
    fs = FS(data)
    el = fs.non_form_errors()
    real_items = [str(m) for m in el]

    coll = MessageCollection([], [])
    finish_group_clean(coll, False, 0, True, [7])   # one rejection message
    shadow_class = ''.join(chr(c) for c in coll.css_class)
    if shadow_class != el.error_class or len(coll.items) != len(real_items):
        return ("DISAGREEMENT (builtin %s-count raise)\n"
                "  shadow: css_class=%r items=%r\n"
                "  real:   error_class=%r items=%r"
                % (kind, shadow_class, coll.items, el.error_class, real_items))
    return None


# --- input generation -------------------------------------------------------------

def boundary_cases():
    id_lists = [
        [], [0], [1], [-1], [7, 7], [1, 2, 3],
        [2 ** 31 - 1, -2 ** 31], [0] * 8, list(range(50)),
        [-10 ** 12, 10 ** 12, 0, 5],
    ]
    cases = []
    for gf in (False, True):
        for gm in (0, 1, -7, 2 ** 40):
            for rej in (False, True):
                for ids in id_lists:
                    cases.append((gf, gm, rej, ids))
    return cases


def rand_case(rng):
    gf = rng.random() < 0.5
    gm = rng.randint(-2 ** 31, 2 ** 31)
    rej = rng.random() < 0.5
    n = rng.randint(0, 8)
    ids = []
    for _ in range(n):
        if rng.random() < 0.7:
            ids.append(rng.randint(-100, 100))
        else:
            ids.append(rng.randint(-2 ** 40, 2 ** 40))
    return gf, gm, rej, ids


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, USE_L10N=False, USE_TZ=False)
    django.setup()
    from django import forms as forms_mod
    from django.core.exceptions import ValidationError

    checked = 0
    for gf, gm, rej, ids in boundary_cases():
        err = check_case(forms_mod, ValidationError, gf, gm, rej, ids)
        if err:
            print(err)
            return 1
        checked += 1

    for kind in ("max", "min"):
        err = check_builtin_raise_case(forms_mod, kind)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        gf, gm, rej, ids = rand_case(rng)
        err = check_case(forms_mod, ValidationError, gf, gm, rej, ids)
        if err:
            print(err)
            return 1
        checked += 1

    n_boundary = len(boundary_cases()) + 2
    print("G-CONF OK: shadow impl == real whole-clean post-state "
          "(rendered class attribute + held messages) on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
