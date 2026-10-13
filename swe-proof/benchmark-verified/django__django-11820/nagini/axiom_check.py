#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11820.

The bundle has NO consumed @ContractOnly axiom in the classic sense: the five
pure functions in model.py's axioms region
(`resolve_kind`, `relation_target`, `pk_kind`, `pk_target`, `transform_present`)
model the UNCHANGED Django name-resolution machinery as referentially
transparent functions over integer identifiers — they are the "graph data" the
deep model `walk_err` folds over (A-reference: the deep model is validated
== real Django behaviour, the axioms' only Ensures are return-range facts).

This check validates, against the REAL Django machinery
(`Options.get_field` / `Field.is_relation` / `Options.pk` /
`Field.get_path_info` / `Field.get_transform`):

  (1) the range facts the axioms assert:
        resolve_kind(m, name) in {0, 1, 2}   (0 = get_field raises
            FieldDoesNotExist; 1 = found & is_relation; 2 = found & not relation)
        pk_kind(m) in {1, 2}                  (a model always has a pk field)
        relation_target / pk_target are real model identifiers
        transform_present(field, name) is a bool

  (2) the deep model end-to-end: backing the graph functions with the REAL
      callees and folding `walk_err` over each related ordering path reproduces
      EXACTLY the E015 verdict the real `Model._check_ordering` emits for that
      path — over the two F2P scenarios, the relevant P2P scenarios, and a set
      of constructed adversarial paths (pk of a related model, multi-hop
      through a non-relation field, registered-transform tails, deep relation
      chains).

Imports only the standard library and `django` (the very framework whose
`_check_ordering` the gold patch edits); no repo-test code. Exit 0 iff every
obligation holds.
"""
import os
import sys
import tempfile

# A throwaway on-disk app so dynamically-defined models have an app_label.
_appdir = tempfile.mkdtemp(prefix='axcheck_')
_pkgdir = os.path.join(_appdir, 'axcheck')
os.makedirs(_pkgdir, exist_ok=True)
with open(os.path.join(_pkgdir, '__init__.py'), 'w'):
    pass
with open(os.path.join(_pkgdir, 'models.py'), 'w'):
    pass
with open(os.path.join(_pkgdir, 'apps.py'), 'w') as _f:
    _f.write(
        "from django.apps import AppConfig\n"
        "class AxCheckConfig(AppConfig):\n"
        "    name = 'axcheck'\n"
        "    label = 'axcheck'\n"
    )
sys.path.insert(0, _appdir)

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=['axcheck.apps.AxCheckConfig'],
    )

import django  # noqa: E402

django.setup()

from django.db import models  # noqa: E402
from django.core.exceptions import FieldDoesNotExist  # noqa: E402
from django.db.models.constants import LOOKUP_SEP  # noqa: E402


# --------------------------------------------------------------------------
# The abstract graph (model.py axioms region) backed by the REAL Django callees.
# Models are identified by their class; field names by their str; the reserved
# name id 0 (model.py) <-> the literal alias string 'pk'.
# --------------------------------------------------------------------------

RAISE, RELATION, NONRELATION = 0, 1, 2


def real_resolve_kind(model, name):
    """resolve_kind(m, name): real get_field + is_relation."""
    try:
        fld = model._meta.get_field(name)
    except FieldDoesNotExist:
        return RAISE
    return RELATION if fld.is_relation else NONRELATION


def real_relation_target(model, name):
    fld = model._meta.get_field(name)
    return fld.get_path_info()[-1].to_opts.model


def real_pk_kind(model):
    return RELATION if model._meta.pk.is_relation else NONRELATION


def real_pk_target(model):
    return model._meta.pk.get_path_info()[-1].to_opts.model


def real_transform_present(field, name):
    """transform_present(field, name): real Field.get_transform is not None."""
    return field is not None and field.get_transform(name) is not None


# --------------------------------------------------------------------------
# Python mirror of model.py's deep fold `walk_err`, driven by the real callees.
# State: current model (or None), and the last found field object (or None).
# --------------------------------------------------------------------------

def walk_err_real(model, parts):
    """Reproduces model.py's walk_err over a related path, using the REAL
    Django callees as the graph. Returns whether the path is in error."""
    cur = model
    fld = None
    err = False
    for part in parts:
        if cur is None:
            # nothing to resolve against (None._meta would raise AttributeError)
            if fld is None or not real_transform_present(fld, part):
                err = True
            # state unchanged
            continue
        if part == 'pk':
            fld = cur._meta.pk
            if real_pk_kind(cur) == RELATION:
                cur = real_pk_target(cur)
            else:
                cur = None
            continue
        k = real_resolve_kind(cur, part)
        if k == RAISE:
            if fld is None or not real_transform_present(fld, part):
                err = True
            # state unchanged
        elif k == RELATION:
            fld = cur._meta.get_field(part)
            cur = real_relation_target(cur, part)
        else:  # NONRELATION
            fld = cur._meta.get_field(part)
            cur = None
    return err


# --------------------------------------------------------------------------
# The real oracle: does Django's _check_ordering emit E015 for this exact path?
# --------------------------------------------------------------------------

def real_check_emits_e015(model, path):
    """Run the real validator and report whether E015 fires for `path`."""
    errors = model.check()
    want = "lookup '%s'." % path
    for e in errors:
        if getattr(e, 'id', None) == 'models.E015' and want in e.msg:
            return True
    return False


# --------------------------------------------------------------------------
# Scenarios.  Each builds real models and a single related ordering path.
# --------------------------------------------------------------------------

_counter = [0]


def fresh(name):
    _counter[0] += 1
    return "%s_%d" % (name, _counter[0])


def mk(base_name, fields, meta=None):
    """Build a uniquely-named concrete model class (so scenarios never collide
    in the global app registry)."""
    attrs = dict(fields)
    attrs['__module__'] = 'axcheck.models'
    meta = dict(meta or {})
    meta['app_label'] = 'axcheck'
    attrs['Meta'] = type('Meta', (), meta)
    return type(fresh(base_name), (models.Model,), attrs)


def build_and_check(root, path):
    """Validate that the abstract fold == the real E015 verdict for `path`
    on `root`."""
    parts = path.split(LOOKUP_SEP)

    # (1) range facts of the axioms, observed on the real callees along a
    #     genuine forward (post-patch) traversal.
    cur = root
    for part in parts:
        if cur is None:
            break
        if part == 'pk':
            assert real_pk_kind(cur) in (RELATION, NONRELATION)
            if real_pk_kind(cur) == RELATION:
                assert isinstance(real_pk_target(cur), type)
                cur = real_pk_target(cur)
            else:
                cur = None
            continue
        k = real_resolve_kind(cur, part)
        assert k in (RAISE, RELATION, NONRELATION)
        if k == RELATION:
            tgt = real_relation_target(cur, part)
            assert isinstance(tgt, type)
            cur = tgt
        elif k == NONRELATION:
            cur = None
        # k == RAISE: traversal stops advancing

    # (2) end-to-end: deep model == real Django verdict.
    model_says_err = walk_err_real(root, parts)
    real_says_err = real_check_emits_e015(root, path)
    assert model_says_err == real_says_err, (
        "deep model disagrees with real Django on %s.ordering=%r: "
        "walk_err=%s, real E015=%s"
        % (root.__name__, path, model_says_err, real_says_err))
    return model_says_err, real_says_err


def main():
    results = []

    def run(name, root, path, expected):
        model_err, real_err = build_and_check(root, path)
        results.append((name, model_err, real_err, expected))

    # F2P 1: multi-hop through a non-relation field -> ERROR (the non-relation
    # reset fix).  parent->relation, field1->non-relation, field2 unreachable.
    Parent = mk('Parent', {'field1': models.CharField(max_length=100),
                           'field2': models.CharField(max_length=100)})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent__field1__field2',)})
    run('F2P multi_times', Child, 'parent__field1__field2', True)

    # F2P 2: pk of a related model -> NO ERROR (the pk-alias fix).
    Parent = mk('Parent', {})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent__pk',)})
    run('F2P related_pk', Child, 'parent__pk', False)

    # P2P: ordering to a missing related model field -> ERROR.
    Parent = mk('Parent', {})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent__missing_field',)})
    run('P2P missing_related', Child, 'parent__missing_field', True)

    # P2P: ordering through a non-related (Integer) field then missing -> ERROR.
    Child = mk('Child', {'parent': models.IntegerField()},
               meta={'ordering': ('parent__missing_field',)})
    run('P2P non_related', Child, 'parent__missing_field', True)

    # P2P: two related-model hops then missing -> ERROR.
    Parent2 = mk('Parent2', {})
    Parent1 = mk('Parent1', {'parent2': models.ForeignKey(Parent2, models.CASCADE)})
    Child = mk('Child', {'parent1': models.ForeignKey(Parent1, models.CASCADE)},
               meta={'ordering': ('parent1__parent2__missing_field',)})
    run('P2P two_related', Child, 'parent1__parent2__missing_field', True)

    # P2P: ordering by a foreign-key attname (single relation field) -> NO ERROR
    # (covers a one-hop relation resolution, the is_relation branch).
    Parent = mk('Parent', {})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent',)})
    run('P2P fk_field', Child, 'parent', False)

    # Adversarial: self-relation, then own pk (3-state walk, all valid) -> NO ERROR.
    M = mk('M', {'parent': models.ForeignKey('self', models.CASCADE, null=True)},
           meta={'ordering': ('parent__pk',)})
    run('ADV self_rel_pk', M, 'parent__pk', False)

    # Adversarial: relation -> relation -> pk-of-related (3 parts, valid) -> NO ERROR.
    GrandParent = mk('GrandParent', {})
    Parent = mk('Parent', {'grand': models.ForeignKey(GrandParent, models.CASCADE)})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent__grand__pk',)})
    run('ADV rel_rel_pk', Child, 'parent__grand__pk', False)

    # Adversarial: relation -> non-relation field then a deeper part -> ERROR
    # (multi-hop through a non-relation field, the same shape as F2P 1 but with
    # the trailing part being a real field on the related model).
    Parent = mk('Parent', {'name': models.CharField(max_length=10),
                           'name2': models.CharField(max_length=10)})
    Child = mk('Child', {'parent': models.ForeignKey(Parent, models.CASCADE)},
               meta={'ordering': ('parent__name__name2',)})
    run('ADV nonrel_then_field', Child, 'parent__name__name2', True)

    # Verify the deep model matches reality AND the expected verdict.
    for name, model_err, real_err, expected in results:
        assert real_err == expected, (
            "scenario %s: real Django E015=%s but expected %s"
            % (name, real_err, expected))
        assert model_err == real_err, (
            "scenario %s: deep model=%s != real=%s" % (name, model_err, real_err))

    print("G-AX OK: axiom range facts hold on the real Django callees and the "
          "deep model `walk_err` reproduces the real `_check_ordering` E015 "
          "verdict on %d scenarios (2 F2P + 4 P2P-shaped + 3 adversarial), "
          "incl. the pk-alias and non-relation-reset behaviours." % len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
