#!/usr/bin/env python3
"""G-CONF for django__django-11820.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_lookupPathValid` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`Model._check_ordering` decision (does a given `Meta.ordering` lookup path
trigger `models.E015`?), over >=1e5 fuzzed (start-model, lookup-path) inputs on a
fixed but rich real model graph. Zero disagreements => exit 0.

Modeled unit (mapping.md / refinement.md): the traversal of ONE related-field
lookup path (`field.split(LOOKUP_SEP)`, i.e. a path containing `__`). For each
path we read the REAL graph data from the models' `_meta` (A-reference: by-name
field resolution `opts.get_field`, primary-key field `opts.pk`, relation target
`field.get_path_info()[-1].to_opts.model`, transform admissibility
`field.get_transform`) into plain `FieldInfo`/`ModelInfo` data, then run the
pure shadow walk — the SHADOW's control flow is what is under test.

Type bijection (mapping.md):
  model class (_meta)         <-> Nat index into the graph
  _cls (current model / None) <-> Option Nat   (none = walk ended)
  fld (last resolved / None)  <-> Option FieldInfo
  field.split(LOOKUP_SEP)     <-> parts : List String
  opts.get_field(part)/raises <-> getField part : Option FieldInfo  (none = FieldDoesNotExist)
  opts.pk                     <-> primaryKey : FieldInfo
  fld.is_relation             <-> FieldInfo.isRelation
  fld.get_path_info()[-1].to_opts.model <-> FieldInfo.target : Nat
  fld.get_transform(part) is not None   <-> FieldInfo.acceptsTransform part
  no-E015-for-this-path / E015 appended <-> result : Bool (true = valid)

stdlib-only (no hypothesis).
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, DATABASES={}, TEMPLATES=[], USE_I18N=False,
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.db import models
from django.db.models.functions import Lower
from django.db.models.lookups import Transform
from django.test.utils import register_lookup

SEED = 11820
N = 120_000
LOOKUP_SEP = "__"

APP = "confapp"


# --- a fixed, rich real model graph -------------------------------------------
class Author(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = APP


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, models.CASCADE)

    class Meta:
        app_label = APP


class Child(models.Model):
    book = models.ForeignKey(Book, models.CASCADE)
    parent = models.ForeignKey("self", models.CASCADE, null=True)

    class Meta:
        app_label = APP


MODELS = [Author, Book, Child]
INDEX = {id(m): i for i, m in enumerate(MODELS)}

# Segment vocabulary: relation fields, value fields, the pk alias, a registered
# transform name, and bogus names — covers every branch of the walk.
VOCAB = ["name", "title", "author", "book", "parent", "pk", "lower", "nope", "id"]


# --- A-reference data read from the REAL _meta --------------------------------
class FieldInfo:
    __slots__ = ("isRelation", "target", "_transforms")

    def __init__(self, isRelation, target, transforms):
        self.isRelation = isRelation
        self.target = target
        self._transforms = transforms  # dict name -> bool

    def acceptsTransform(self, name):
        return self._transforms.get(name, False)


def build_field_info(fld):
    """Read the real field's relation/target/transform data into FieldInfo."""
    isRel = bool(fld.is_relation)
    target = -1
    if isRel:
        try:
            target = INDEX[id(fld.get_path_info()[-1].to_opts.model)]
        except Exception:
            target = -2  # relation leaves the modeled graph
    # transform admissibility for every vocabulary name (real get_transform)
    transforms = {}
    for nm in VOCAB:
        try:
            transforms[nm] = fld.get_transform(nm) is not None
        except Exception:
            transforms[nm] = False
    return FieldInfo(isRel, target, transforms)


def get_field(model, name):
    """opts.get_field(name) -> FieldInfo, or None on FieldDoesNotExist.
    The 'pk' alias is NOT a real field, so get_field('pk') raises -> None."""
    try:
        fld = model._meta.get_field(name)
    except Exception:
        return None
    return build_field_info(fld)


def primary_key(model):
    return build_field_info(model._meta.pk)


# --- shadow: transliteration of implementation_lookupPathValid ----------------
def shadow(start_idx, parts):
    cur = start_idx               # Option Nat (None = walk ended)
    fld = None                    # Option FieldInfo
    invalid = False
    for part in parts:
        if cur is not None:
            model = MODELS[cur]
            resolved = primary_key(model) if part == "pk" else get_field(model, part)
            if resolved is not None:
                fld = resolved
                if fld.isRelation:
                    cur = fld.target if fld.target >= 0 else None
                else:
                    cur = None
            else:
                if fld is not None:
                    if not fld.acceptsTransform(part):
                        invalid = True
                else:
                    invalid = True
        else:
            if fld is not None:
                if not fld.acceptsTransform(part):
                    invalid = True
            else:
                invalid = True
    return not invalid


# --- oracle: the REAL patched _check_ordering verdict for a path --------------
def oracle(model, path_str):
    """True iff setting Meta.ordering=(path_str,) yields NO models.E015 for it."""
    model._meta.ordering = (path_str,)
    errors = model._check_ordering()
    for e in errors:
        if getattr(e, "id", None) == "models.E015" and ("'%s'" % path_str) in str(e.msg):
            return False
    return True


def rand_path(rng):
    k = rng.randint(2, 4)  # multi-segment => a related-field path (contains __)
    return [rng.choice(VOCAB) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    fails = 0
    # `lower` must be a registered transform on CharField for the transform
    # branch to be exercised exactly as the F2P registered-lookup test does.
    with register_lookup(models.CharField, Lower):
        for i in range(N):
            start = rng.randrange(len(MODELS))
            model = MODELS[start]
            parts = rand_path(rng)
            path_str = LOOKUP_SEP.join(parts)
            o = oracle(model, path_str)
            s = shadow(start, parts)
            if o != s:
                fails += 1
                if fails <= 20:
                    print(f"DISAGREE i={i} start={model.__name__} path={path_str!r} "
                          f"oracle={o} shadow={s}")
    if fails:
        print(f"FAIL: {fails}/{N} disagreements")
        return 1
    print(f"OK: {N} inputs, 0 disagreements (status=pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
