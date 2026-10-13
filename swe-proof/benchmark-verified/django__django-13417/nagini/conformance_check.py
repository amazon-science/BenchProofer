#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13417 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none in the impl region itself; the pre/post
condition calls live outside it). The model IS Python: the impl is a pure
boolean decision over five bool parameters, so it runs directly. The @Pure
helper `is_ordered` copies over as a plain function and is cross-checked
against the impl on every input. No PSeq shim is needed (no sequence types)
and there are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
the `django.db.models.query.QuerySet.ordered` property — evaluated on real
QuerySet objects. The gate applies patch.diff to /testbed before this script
runs; the container works from /testbed so the patched package imports
directly.

Type bridge (mapping.md section 2): each of the five bool parameters is the
truth value of an attribute expression the real property reads, each consumed
exclusively as a condition operand. Every generated input is realized with
CONCRETE repo-shaped values so the truthy-to-bool refinement is exercised on
real value shapes, not just on Python bools:

  * is_empty        <-> the result-set-is-empty introspection; realized via
                        the real `.none()` path (so the real class-level
                        instance check runs), False via a fresh queryset;
  * has_raw_order   <-> `query.extra_order_by or query.order_by`; realized as
                        two independent tuples (empty / non-empty), the bool
                        is the disjunction of their truth values;
  * default_on      <-> `query.default_ordering` (a plain bool attribute);
  * model_has_order <-> `query.get_meta().ordering`; realized as an empty or
                        non-empty list on the model's options object;
  * is_grouped      <-> `query.group_by`; realized over all its real value
                        shapes: None / empty tuple (falsy), True / non-empty
                        tuple (truthy).

Input domain: the modeled function has no Requires (all 2**5 bool inputs are
admissible), so every generated input is Requires-satisfying by construction.

>= 1e5 inputs: 128 exhaustive boundary combinations (all 2**5 truth-value
combinations expanded over the multiple concrete shapes per signal) plus
100000 fuzz inputs with randomized concrete shapes. Pinned fuzz seed: 13417.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random fuzzing; hypothesis not
needed).
"""
import itertools
import json
import random
import string
import sys

SEED = 13417
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped ----------------------------

def is_ordered(is_empty, has_raw_order, default_on, model_has_order,
               is_grouped):
    return (
        is_empty
        or has_raw_order
        or (default_on and model_has_order and not is_grouped)
    )


# --- the impl region of model.py, verbatim ------------------------------------

def ordered(is_empty, has_raw_order, default_on, model_has_order, is_grouped):
    if is_empty:
        return True
    if has_raw_order:
        return True
    elif default_on and model_has_order and not is_grouped:
        return True
    else:
        return False
    # impl-end (verbatim copy ends here)


# --- oracle plumbing: real QuerySets on a real model ---------------------------

def check_one(Model, empty_flag, extra_val, order_val, default_val,
              meta_ordering_val, group_val):
    """Build a real queryset carrying the given concrete signal values, read
    the real property, and compare with the shadow. Returns an error string on
    disagreement, else None."""
    # Real emptiness path: .none() so the property's class-level emptiness
    # check observes a genuinely empty result set.
    qs = Model.objects.none() if empty_flag else Model.objects.all()
    qs.query.extra_order_by = extra_val
    qs.query.order_by = order_val
    qs.query.default_ordering = default_val
    qs.query.group_by = group_val
    Model._meta.ordering = meta_ordering_val

    real = qs.ordered  # REAL patched property

    # bridge: truth values of the concrete signals (mapping.md section 2)
    b_empty = bool(empty_flag)
    b_raw = bool(extra_val) or bool(order_val)
    b_default = bool(default_val)
    b_meta = bool(meta_ordering_val)
    b_grouped = bool(group_val)

    shadow = ordered(b_empty, b_raw, b_default, b_meta, b_grouped)
    spec = is_ordered(b_empty, b_raw, b_default, b_meta, b_grouped)
    if shadow != spec:
        return ("IMPL/PURE MISMATCH (internal): inputs (%r,%r,%r,%r,%r) "
                "-> impl=%r, pure=%r"
                % (b_empty, b_raw, b_default, b_meta, b_grouped, shadow, spec))

    if bool(real) != shadow:
        return ("DISAGREEMENT\n"
                "  empty=%r extra_order_by=%r order_by=%r default_ordering=%r"
                " meta_ordering=%r group_by=%r\n"
                "  bridged bools: is_empty=%r has_raw_order=%r default_on=%r"
                " model_has_order=%r is_grouped=%r\n"
                "  shadow=%r\n  real=%r"
                % (empty_flag, extra_val, order_val, default_val,
                   meta_ordering_val, group_val,
                   b_empty, b_raw, b_default, b_meta, b_grouped,
                   shadow, real))
    return None


# Concrete shapes per signal (the real value kinds each attribute takes).
EXTRA_SHAPES = {False: [()], True: [("col1 DESC",)]}
ORDER_SHAPES = {False: [()], True: [("name",)]}
DEFAULT_SHAPES = {False: [False], True: [True]}
META_SHAPES = {False: [[]], True: [["name"]]}
GROUP_SHAPES = {False: [None, ()], True: [True, ("col1",)]}


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()
    from django.db import models

    class ConfModel(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "conf_shadow"

    checked = 0
    n_boundary = 0

    # Exhaustive boundary: all 2**5 truth-value combinations, expanded over
    # every listed concrete shape for each signal (128 concrete cases).
    for be, br_e, br_o, bd, bm, bg in itertools.product([False, True],
                                                        repeat=6):
        for extra_val in EXTRA_SHAPES[br_e]:
            for order_val in ORDER_SHAPES[br_o]:
                for default_val in DEFAULT_SHAPES[bd]:
                    for meta_val in META_SHAPES[bm]:
                        for group_val in GROUP_SHAPES[bg]:
                            err = check_one(ConfModel, be, extra_val,
                                            order_val, default_val,
                                            meta_val, group_val)
                            if err:
                                print(err)
                                return 1
                            checked += 1
                            n_boundary += 1

    # Fuzz: randomized concrete shapes, pinned seed.
    rng = random.Random(SEED)
    idents = ["name", "id", "created", "rank", "col1", "col2", "x"]

    def rand_tuple(maxlen):
        n = rng.randint(0, maxlen)
        return tuple(rng.choice(idents) for _ in range(n))

    def rand_ordering():
        n = rng.randint(0, 3)
        out = []
        for _ in range(n):
            f = rng.choice(idents)
            if rng.random() < 0.4:
                f = "-" + f
            out.append(f)
        return out

    def rand_group():
        roll = rng.random()
        if roll < 0.25:
            return None
        if roll < 0.40:
            return ()
        if roll < 0.60:
            return True
        return tuple(rng.choice(idents) for _ in range(rng.randint(1, 3)))

    def rand_raw_suffix():
        # occasional exotic-but-real string content in the raw-order tuples
        s = "".join(rng.choice(string.ascii_lowercase) for _ in range(3))
        return (s + " DESC",)

    for _ in range(N_FUZZ):
        empty_flag = rng.random() < 0.15
        extra_val = rand_raw_suffix() if rng.random() < 0.10 \
            else rand_tuple(2)
        order_val = rand_tuple(2)
        default_val = rng.random() < 0.5
        meta_val = rand_ordering()
        group_val = rand_group()
        err = check_one(ConfModel, empty_flag, extra_val, order_val,
                        default_val, meta_val, group_val)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched property on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
