#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16315 (nagini).

SHADOW: the impl regions of model.py (`conflict_columns` and its runtime
callee `lookup`), copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
`name_present` / `column_for` copy over as plain functions on top of a small
immutable-tuple PSeq shim; they serve here to enforce the Requires domain and
as an internal cross-check of the shadow. There are no @ContractOnly callees
in this bundle (see mapping.md section 4).

ORACLE: the REAL patched repo behaviour the model models per mapping.md
section 1 -- per requested field name, the storage identifier handed to the
backend's conflict-resolution hook. Two oracle layers, both over the patched
/testbed (the gate applies patch.diff before this script runs):

  (a) the resolution pipeline `Model._meta.get_field(name).column`, i.e. the
      name->field lookup composed with the storage-identifier projection,
      evaluated on real dynamically-declared models; and
  (b) END-TO-END: real `QuerySet.bulk_create(..., update_conflicts=True,
      update_fields=..., unique_fields=...)` calls against sqlite tables,
      with the backend's conflict-suffix hook intercepted at the
      compiler/backend boundary so the two identifier lists the patched code
      actually passes down are captured verbatim and compared to the shadow.

Type bridge (mapping.md section 2): field-name and storage-identifier strings
are interned into int identifiers via one injective map per registry (equal
strings <-> equal ints across both the name and the column lists, so
column == name exactly when no storage-column override is configured). The
registry itself is the model's concrete fields as parallel name/column lists.

Input domain (the Requires): len(field_columns) == len(field_names) holds by
registry construction, and every requested name is registered
(`name_present`); requested lists may be empty and may repeat names.

>= 1e5 Requires-satisfying inputs: exhaustive requested-permutation boundary
cases over two fixed models (one with case-only storage-column overrides, one
without) + 100000 fuzz draws over a pool of 200 random models (random
override patterns, including overrides colliding with sibling field names)
+ 500 end-to-end bulk_create interceptions. Pinned seed: 163150.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. Imports: stdlib + Django itself (the framework under
test, importable in the container at /testbed).
"""
import random
import string
import sys

SEED = 163150
N_FUZZ = 100000
N_END_TO_END = 500


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def name_present(name, names):
    if len(names) == 0:
        return False
    if names[0] == name:
        return True
    return name_present(name, names.drop(1))


def column_for(name, names, columns):
    if len(names) == 0 or len(columns) == 0:
        return 0
    if names[0] == name:
        return columns[0]
    return column_for(name, names.drop(1), columns.drop(1))


# --- impl regions of model.py, contracts stripped (verbatim) ------------------

def conflict_columns(requested, field_names, field_columns):
    result = []  # type: list
    i = 0
    while i < len(requested):
        # resolve the requested name to a declared field, then take its column.
        col = lookup(requested[i], field_names, field_columns)
        result = result + [col]
        i = i + 1
    return result


def lookup(name, field_names, field_columns):
    j = 0
    while j < len(field_names):
        if field_names[j] == name:
            return field_columns[j]
        j = j + 1
    # unreachable: name_present guarantees a match before j == len
    return 0


# --- Django configuration ------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=False,
        )
    django.setup()


def _registry(model):
    """The parallel (names, columns) registry from a real model's concrete
    fields, using the REAL storage-identifier attribute."""
    names, columns = [], []
    for f in model._meta.concrete_fields:
        names.append(f.name)
        columns.append(f.column)
    return names, columns


def _intern(names, columns, requested):
    """The mapping.md section 2 bridge: one injective str->int map over the
    union of the registry strings, applied to names, columns and requests
    alike (so equal strings map to equal ints and vice versa). Returns the
    int-domain triple plus the decoder."""
    table = {}
    for s in list(names) + list(columns):
        if s not in table:
            table[s] = len(table) + 1
    inv = {}
    for s, k in table.items():
        inv[k] = s
    names_i = [table[s] for s in names]
    columns_i = [table[s] for s in columns]
    requested_i = [table[s] for s in requested]
    return names_i, columns_i, requested_i, inv


def _shadow_columns(requested, names, columns):
    """Run the shadow over the int domain and decode back to strings.
    Enforces (and asserts) the Requires before calling."""
    names_i, columns_i, requested_i, inv = _intern(names, columns, requested)
    assert len(columns_i) == len(names_i)
    for r in requested_i:
        assert name_present(r, ToSeq(names_i)), \
            "input generator bug: requested name not registered"
    out = conflict_columns(requested_i, names_i, columns_i)
    # internal cross-check against the pure deep model (spec side):
    for k in range(len(requested_i)):
        assert out[k] == column_for(requested_i[k], ToSeq(names_i),
                                    ToSeq(columns_i)), \
            "shadow impl / pure deep model divergence (shadow bug)"
    return [inv[v] for v in out]


def _disagree(tag, model_name, requested, names, columns, got, real):
    print("DISAGREEMENT [%s] model=%s" % (tag, model_name))
    print("  registry names   = %r" % (names,))
    print("  registry columns = %r" % (columns,))
    print("  requested        = %r" % (requested,))
    print("  shadow  -> %r" % (got,))
    print("  real    -> %r" % (real,))
    sys.exit(1)


# --- oracle (a): the resolution pipeline over real models ----------------------

def _pipeline(model, requested):
    return [model._meta.get_field(n).column for n in requested]


def _make_model(class_name, spec):
    """Declare a real Django model from spec = [(field_name, db_column|None)].
    IntegerFields throughout (the identifier selection under test is
    field-type-agnostic)."""
    from django.db import models
    attrs = {"__module__": __name__, "Meta": type("Meta", (), {
        "app_label": "confcheck"})}
    for fname, dbcol in spec:
        attrs[fname] = models.IntegerField(null=True, db_column=dbcol)
    return type(class_name, (models.Model,), attrs)


def _rand_name(rng, taken):
    while True:
        n = rng.randint(1, 8)
        s = "".join(rng.choice(string.ascii_lowercase) for _ in range(n))
        if s not in taken and s not in ("id", "pk"):
            return s


def _rand_spec(rng):
    """Random field spec: 1..6 fields, each with no override, a case-flipped
    override, a fresh random override, or an override colliding with a sibling
    field's name (the discrimination stress case)."""
    k = rng.randint(1, 6)
    taken = set()
    fnames = []
    for _ in range(k):
        s = _rand_name(rng, taken)
        taken.add(s)
        fnames.append(s)
    spec = []
    for fname in fnames:
        mode = rng.randint(0, 3)
        if mode == 0:
            dbcol = None
        elif mode == 1:
            flipped = fname.upper() if fname != fname.upper() else fname + "X"
            dbcol = flipped
        elif mode == 2:
            dbcol = _rand_name(rng, taken)
        else:
            other = rng.choice(fnames)
            dbcol = other if other != fname else None
        spec.append((fname, dbcol))
    return spec


# --- oracle (b): end-to-end interception of the patched code path --------------

class _Capture(object):
    def __init__(self):
        self.update_cols = None
        self.unique_cols = None


def _intercept_ops(connection, capture):
    """Replace the backend's conflict-suffix hook on this connection's ops
    instance so the two identifier iterables the patched compiler passes down
    are materialised and recorded; returns the original for restoration."""
    original = connection.ops.on_conflict_suffix_sql

    def hook(fields, on_conflict, update_fields, unique_fields):
        capture.update_cols = list(update_fields)
        capture.unique_cols = list(unique_fields)
        return ""

    connection.ops.on_conflict_suffix_sql = hook
    return original


def _end_to_end(rng, models_with_tables):
    from django.db import connection
    checked = 0
    for _ in range(N_END_TO_END):
        model = rng.choice(models_with_tables)
        names, columns = _registry(model)
        pk_name = model._meta.pk.name
        non_pk = [n for n in names if n != pk_name]
        if not non_pk:
            continue
        # update_fields: non-empty, no pk (a documented caller obligation);
        # unique_fields: non-empty, may use the "pk" alias.
        upd = [rng.choice(non_pk) for _ in range(rng.randint(1, len(non_pk)))]
        uniq_raw = [rng.choice(names + ["pk"])
                    for _ in range(rng.randint(1, len(names)))]
        # the alias substitution happens before the modeled transform; the
        # model's requested list is the post-substitution name list.
        uniq = [pk_name if n == "pk" else n for n in uniq_raw]

        objs = [model(**{n: rng.randint(0, 99) for n in non_pk})
                for _ in range(rng.randint(1, 3))]
        cap = _Capture()
        original = _intercept_ops(connection, cap)
        try:
            model.objects.bulk_create(
                objs, update_conflicts=True,
                update_fields=list(upd), unique_fields=list(uniq_raw))
        finally:
            connection.ops.on_conflict_suffix_sql = original
        assert cap.update_cols is not None and cap.unique_cols is not None, \
            "end-to-end capture did not fire (bulk_create took another path)"

        got_upd = _shadow_columns(upd, names, columns)
        got_uniq = _shadow_columns(uniq, names, columns)
        if got_upd != cap.update_cols:
            _disagree("end-to-end/update", model.__name__, upd, names,
                      columns, got_upd, cap.update_cols)
        if got_uniq != cap.unique_cols:
            _disagree("end-to-end/unique", model.__name__, uniq_raw, names,
                      columns, got_uniq, cap.unique_cols)
        checked += 2
    return checked


# --- main ----------------------------------------------------------------------

def main():
    _configure_django()
    from django.db import connection, models
    from itertools import permutations

    rng = random.Random(SEED)
    total = 0
    saw_override_disagreement_case = False

    # fixed boundary models: one with case-only storage-column overrides
    # (columns differ from names), one plain (columns equal names).
    class OverriddenFields(models.Model):
        rank = models.IntegerField(null=True, db_column="rAnK")
        name = models.IntegerField(null=True, db_column="oTheRNaMe")

        class Meta:
            app_label = "confcheck"

    class PlainFields(models.Model):
        alpha = models.IntegerField(null=True)
        beta = models.IntegerField(null=True)

        class Meta:
            app_label = "confcheck"

    # (1) boundary: every requested-permutation (incl. empty) of each fixed
    # model's registry names, plus repeated-name requests.
    for model in (OverriddenFields, PlainFields):
        names, columns = _registry(model)
        cases = []
        for r in range(0, len(names) + 1):
            cases.extend(list(p) for p in permutations(names, r))
        for n in names:
            cases.append([n, n])
            cases.append([n] * 3)
        for requested in cases:
            got = _shadow_columns(requested, names, columns)
            real = _pipeline(model, requested)
            if got != real:
                _disagree("boundary", model.__name__, requested, names,
                          columns, got, real)
            total += 1
            for g, n in zip(got, requested):
                if g != n:
                    saw_override_disagreement_case = True

    # (2) fuzz: 100000 requested-list draws over a pool of 200 random models.
    pool = []
    for idx in range(200):
        spec = _rand_spec(rng)
        pool.append(_make_model("ConfFuzz%d" % idx, spec))
    for _ in range(N_FUZZ):
        model = rng.choice(pool)
        names, columns = _registry(model)
        requested = [rng.choice(names) for _ in range(rng.randint(0, 6))]
        got = _shadow_columns(requested, names, columns)
        real = _pipeline(model, requested)
        if got != real:
            _disagree("fuzz", model.__name__, requested, names, columns,
                      got, real)
        total += 1
        for g, n in zip(got, requested):
            if g != n:
                saw_override_disagreement_case = True

    # (3) end-to-end: intercept the identifier lists the patched code actually
    # hands the backend during real bulk_create upsert calls.
    if not connection.features.supports_update_conflicts:
        print("G-CONF ERROR: this backend cannot exercise the end-to-end "
              "upsert path (supports_update_conflicts is False)")
        return 1
    tabled = [OverriddenFields, PlainFields,
              _make_model("ConfE2EMixed", [
                  ("first", "FiRsT"), ("second", None),
                  ("third", "elsewhere")])]
    with connection.schema_editor() as editor:
        for model in tabled:
            editor.create_model(model)
    total += _end_to_end(rng, tabled)

    # guard against a vacuous run: the name-vs-column discriminator (an
    # override in play, so the produced identifier differs from the requested
    # name) must have been exercised.
    assert saw_override_disagreement_case, \
        "no storage-column-override case exercised; generator bug"

    print("G-CONF OK: shadow == real patched pipeline on %d "
          "Requires-satisfying inputs (boundary permutations + %d fuzz over "
          "200 random registries + %d end-to-end intercepted bulk_create "
          "upserts); seed=%d" % (total, N_FUZZ, N_END_TO_END * 2, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
