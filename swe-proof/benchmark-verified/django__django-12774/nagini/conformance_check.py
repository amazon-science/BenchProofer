#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12774 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Invariant) stripped, plus the @Pure helpers ``permits_alone``
and ``any_permits`` copied over as plain functions. PSeq becomes a plain
tuple (only ``len`` and indexing are used), List stays a Python list. There
are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo decision the model models per mapping.md — the
field-name acceptability guard of ``QuerySet.in_bulk`` in
``django/db/models/query.py``. The gate applies patch.diff to /testbed before
this script runs and sets PYTHONPATH=/testbed, so the patched code is what we
import. Calling ``qs.in_bulk(id_list=[], field_name=fn)`` evaluates the guard
and, when the field is accepted, returns an empty dict BEFORE any database
query (the empty-id_list early return), so no tables are needed; a raised
ValueError from the guard means "rejected". The guard reads the REAL
unchanged callees (``opts.total_unique_constraints``,
``opts.get_field(fn).unique``) off real model classes we construct.

Type bridge (mapping.md section 2):
  * field-name str -> int identity: per constructed class, its non-pk fields
    f1..fk map injectively to ids 1..k; the 'pk' alias AND the class's actual
    primary-key field name both map to the distinguished identity PK == 0
    (only name equality participates in the decision, so any injective
    encoding is faithful).
  * UniqueConstraint -> (condition is None, tuple of field ids). We encode
    EVERY declared constraint, conditional ones included, with the flag
    False when a condition is present; the shadow's per-guarantee predicate
    never lets a conditional or multi-field entry permit a field, which is
    exactly the real guard's behaviour (its derivation only ever consults the
    unconditional ones), so the encodings agree while the conditional branch
    of the shadow is genuinely exercised.
  * the field's individual-unique flag -> the REAL opts.get_field(fn).unique
    read per observation (for a pk lookup the real guard short-circuits
    before reading it, mirrored by the shadow's PK early return; the flag
    value is then irrelevant and passed as False).
  * ValueError raised <-> shadow returns True (rejection).

Input domain: the shadow's precondition only demands read access to the
guarantees list, so every (int, bool, list-of-(bool, int-tuple)) triple is
Requires-satisfying; we draw the triples from REAL constructed Django model
classes so each shadow input is bridged 1:1 to a real guard invocation.
Boundary cases pin the discriminating layouts (single-field unconditional,
conditional/partial, multi-field, duplicated single-field, unique=True field,
no constraints at all, a constraint over an already-unique field); fuzz
constructs randomized classes (2..6 fields, random unique flags, 0..4
constraints of random arity/conditionality/order) and checks every field of
each plus the 'pk' alias and the actual primary-key name.

>= 1e5 Requires-satisfying inputs (one per (class, field-name) observation).
Pinned fuzz seed: 12774.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12774
TARGET = 100_000

PK = 0  # the distinguished primary-key field identity


# --- pure helpers from model.py, decorators/contracts stripped ----------------

def permits_alone(g, field_name):
    return g[0] and len(g[1]) == 1 and g[1][0] == field_name


def any_permits(guarantees, idx, field_name):
    if idx == len(guarantees):
        return False
    return permits_alone(guarantees[idx], field_name) or \
        any_permits(guarantees, idx + 1, field_name)


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def should_reject(field_name, field_unique, guarantees):
    if field_name == PK:
        return False
    if field_unique:
        return False
    # Scan the declared guarantees for one that makes this field acceptable on
    # its own (unconditional and ranging over this single field).
    i = 0
    found = False
    while i < len(guarantees):
        if permits_alone(guarantees[i], field_name):
            found = True
        i = i + 1
    return not found


# --- oracle plumbing -----------------------------------------------------------

def _configure_django():
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


def real_reject(klass, field_name):
    """Whether the REAL patched guard rejects field_name for klass: call
    in_bulk with an empty id list (returns {} before any DB access when the
    field is accepted) and observe the ValueError."""
    try:
        klass._default_manager.all().in_bulk(id_list=[], field_name=field_name)
    except ValueError:
        return True
    return False


def encode_guarantees(klass, name_to_id):
    """Bridge every declared UniqueConstraint of klass to the model carrier
    (condition-is-absent flag, tuple of field ids)."""
    out = []
    for c in klass._meta.constraints:
        out.append((c.condition is None,
                    tuple(name_to_id[n] for n in c.fields)))
    return out


def check_class(klass, field_names, name_to_id, tag):
    """Compare shadow vs real guard on each candidate field name; return the
    number of observations, or raise SystemExit(1) printing the disagreement."""
    opts = klass._meta
    guarantees = encode_guarantees(klass, name_to_id)
    n = 0
    for fn in field_names:
        is_pk = (fn == 'pk' or fn == opts.pk.name)
        if is_pk:
            fn_id, field_unique = PK, False  # shadow short-circuits on PK
        else:
            fn_id = name_to_id[fn]
            field_unique = opts.get_field(fn).unique  # REAL unchanged callee
        r_shadow = should_reject(fn_id, field_unique, guarantees)
        r_real = real_reject(klass, fn)
        if r_shadow != r_real:
            print("DISAGREEMENT [%s]\n  field_name=%r (id=%r)\n"
                  "  field_unique=%r\n  guarantees=%r\n"
                  "  shadow=%r\n  real=%r"
                  % (tag, fn, fn_id, field_unique, guarantees,
                     r_shadow, r_real))
            sys.exit(1)
        n += 1
    return n


_class_counter = [0]


def make_class(models, field_specs, constraint_specs):
    """Construct a real concrete model class.

    field_specs: list of (name, unique_flag). constraint_specs: list of
    (field_name_list, conditional_field_or_None)."""
    _class_counter[0] += 1
    idx = _class_counter[0]
    attrs = {"__module__": "django.contrib.auth.models"}
    for name, uniq in field_specs:
        attrs[name] = models.IntegerField(unique=uniq, null=True)
    constraints = []
    for j, (cfields, cond_field) in enumerate(constraint_specs):
        kwargs = {"fields": list(cfields), "name": "cc_%d_%d" % (idx, j)}
        if cond_field is not None:
            kwargs["condition"] = models.Q(**{cond_field: 1})
        constraints.append(models.UniqueConstraint(**kwargs))
    meta = type("Meta", (), {"app_label": "auth",
                             "constraints": constraints})
    attrs["Meta"] = meta
    return type("ConfCase%d" % idx, (models.Model,), attrs)


def boundary_observations(models):
    """The discriminating layouts, checked field-by-field."""
    total = 0
    cases = [
        # single-field unconditional guarantee over a non-unique field
        ([("f1", False), ("f2", False)], [(["f1"], None)]),
        # conditional (partial) single-field + multi-field composite
        ([("f1", False), ("f2", False), ("f3", False)],
         [(["f1"], "f3"), (["f2", "f3"], None)]),
        # individually unique field, no constraints
        ([("f1", True), ("f2", False)], []),
        # mix: single unconditional + composite + conditional over same field
        ([("f1", False), ("f2", False), ("f3", False), ("f4", False)],
         [(["f1"], None), (["f2", "f3"], None), (["f3"], "f4")]),
        # duplicated single-field unconditional guarantees
        ([("f1", False)], [(["f1"], None), (["f1"], None)]),
        # unconditional guarantee over an already-unique field
        ([("f1", True), ("f2", False)], [(["f1"], None)]),
        # no fields beyond pk, no constraints
        ([], []),
        # conditional guarantee only (never permits)
        ([("f1", False)], [(["f1"], "f1")]),
        # wide composite touching every field
        ([("f1", False), ("f2", False), ("f3", False)],
         [(["f1", "f2", "f3"], None)]),
    ]
    for fs, cs in cases:
        klass = make_class(models, fs, cs)
        name_to_id = {name: i + 1 for i, (name, _) in enumerate(fs)}
        fnames = ['pk', klass._meta.pk.name] + [name for name, _ in fs]
        total += check_class(klass, fnames, name_to_id, "boundary")
    return total


def fuzz_class_specs(rng):
    nf = rng.randint(2, 6)
    field_specs = [("f%d" % (i + 1), rng.random() < 0.15)
                   for i in range(nf)]
    names = [n for n, _ in field_specs]
    constraint_specs = []
    for _ in range(rng.randint(0, 4)):
        arity = min(nf, 1 + (0 if rng.random() < 0.6 else rng.randint(1, 2)))
        cfields = rng.sample(names, arity)
        cond = rng.choice(names) if rng.random() < 0.3 else None
        constraint_specs.append((tuple(cfields), cond))
    return field_specs, constraint_specs


def main():
    try:
        _configure_django()
    except Exception as exc:
        print("G-CONF ERROR: Django not configurable: %r" % (exc,))
        return 1
    from django.db import models

    checked = boundary_observations(models)
    n_boundary = checked

    from django.apps import apps
    rng = random.Random(SEED)
    while checked < TARGET:
        fs, cs = fuzz_class_specs(rng)
        klass = make_class(models, fs, cs)
        name_to_id = {name: i + 1 for i, (name, _) in enumerate(fs)}
        fnames = ['pk', klass._meta.pk.name] + [name for name, _ in fs]
        checked += check_class(klass, fnames, name_to_id, "fuzz")
        # Keep the app registry bounded: registering each throwaway class
        # invalidates caches across ALL registered models, which turns the
        # fuzz loop quadratic if classes accumulate. The classes have no
        # relations, so dropping them after use is safe.
        apps.all_models["auth"].pop(klass.__name__.lower(), None)

    print("G-CONF OK: shadow impl == real bulk-lookup field-name guard on "
          "%d observations (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
