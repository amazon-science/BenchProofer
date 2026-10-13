#!/usr/bin/env python3
"""G-CONF for django__django-11163.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_modelToDict` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `model_to_dict`
(django/forms/models.py) over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): walk the field records in order; keep a field iff it is
editable AND (fields is None OR f.name in fields) AND NOT (exclude has it). The
empty inclusion list keeps nothing; the empty exclusion list bars nothing.

  * Oracle  = the REAL patched `model_to_dict(instance, fields, exclude)`, driven
              with a duck-typed instance whose `_meta` exposes the field walk and
              whose fields implement `.name`, `.editable`, `.value_from_object`.
              Compared as the ordered list of `(name, value)` pairs
              (`list(d.items())`).
  * Shadow  = the op-for-op transliteration of implementation_modelToDict.

Type bijection (mapping.md): fs:List (FieldRec a) <-> the field walk
chain(concrete_fields, private_fields, many_to_many); FieldRec.name/.editable/.val
<-> f.name / getattr(f,'editable',False) / f.value_from_object(instance);
fields/exclude : Option (List String) <-> Optional[list[str]] (None<->none);
result : List (String x a) <-> list(model_to_dict(...).items()).
stdlib-only; no hypothesis required.
"""
import os
import random
import sys
from itertools import chain

# --- configure Django settings before importing the forms machinery ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, DATABASES={},
        INSTALLED_APPS=[], USE_I18N=False,
    )
    django.setup()

from django.forms.models import model_to_dict


# --- duck-typed model machinery -----------------------------------------------
class FakeField:
    """A model field exposing exactly what model_to_dict reads."""
    def __init__(self, name, editable, value):
        self.name = name
        self.editable = editable
        self._value = value

    def value_from_object(self, instance):
        return self._value


class FakeMeta:
    def __init__(self, concrete, private, m2m):
        self.concrete_fields = concrete
        self.private_fields = private
        self.many_to_many = m2m


class FakeInstance:
    def __init__(self, meta):
        self._meta = meta


def oracle(meta_fields_split, fields, exclude):
    concrete, private, m2m = meta_fields_split
    inst = FakeInstance(FakeMeta(concrete, private, m2m))
    d = model_to_dict(inst, fields=fields, exclude=exclude)
    return list(d.items())


def shadow(all_fields, fields, exclude):
    """R/I transliteration of implementation_modelToDict (Lean).

    Op 2: skip non-editable. Op 3 (the fix): a present `fields` (even []) must
    name the field. Op 4: a present `exclude` bars a named field. Op 5: append.
    """
    data = []
    for f in all_fields:
        if not getattr(f, "editable", False):
            continue
        if fields is not None:
            if f.name not in fields:
                continue
        if exclude is not None:
            if f.name in exclude:
                continue
        data.append((f.name, f.value_from_object(None)))
    return data


_NAMES = ["id", "name", "score", "writer_ptr", "title", "x", "y", "z", "a_b",
          "dup", "Name", "ID", ""]


def rand_fields(rng):
    """Build a field walk: random concrete/private/m2m splits with unique names
    (model field names are unique within a model)."""
    n = rng.randint(0, 8)
    names = rng.sample(_NAMES, min(n, len(_NAMES)))
    objs = [FakeField(nm, rng.random() < 0.8, rng.randint(0, 1000)) for nm in names]
    # split into the three iterables the chain() walks
    i = rng.randint(0, len(objs))
    j = rng.randint(i, len(objs))
    return objs, (objs[:i], objs[i:j], objs[j:])


def rand_opt_list(rng, present_names):
    """Draw fields/exclude from {None, [], subset of present, names absent}."""
    r = rng.random()
    if r < 0.30:
        return None
    if r < 0.55:
        return []                      # the discriminating empty-list case
    if r < 0.80 and present_names:
        k = rng.randint(1, len(present_names))
        return rng.sample(present_names, k)
    # names mostly/partly absent from the walk
    pool = _NAMES + ["ghost1", "ghost2", "missing"]
    k = rng.randint(1, 4)
    return [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(11163)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        all_fields, split = rand_fields(rng)
        present = [f.name for f in all_fields]
        fields = rand_opt_list(rng, present)
        exclude = rand_opt_list(rng, present)
        o = oracle(split, fields, exclude)
        s = shadow(all_fields, fields, exclude)
        if o != s:
            disagreements += 1
            if first is None:
                first = (present, fields, exclude, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
