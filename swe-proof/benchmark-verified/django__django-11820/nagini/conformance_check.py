#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11820 (nagini).

SHADOW: the impl region of model.py's ``check_related_path``, copied VERBATIM
below with only the contract calls (Requires / Ensures / Invariant / Assert /
MustTerminate) stripped.  The @Pure fold ``walk_err`` copies over on a small
immutable tuple-backed PSeq shim and serves as an internal cross-check of the
executable shadow (it is the ghost value the impl region computes first).  The
five @ContractOnly graph functions of the axioms region (``resolve_kind`` /
``relation_target`` / ``pk_kind`` / ``pk_target`` / ``transform_present``) are
backed by the REAL repo callees they are bound to in mapping.md section 1:
``Options.get_field`` + ``Field.is_relation``, ``Field.get_path_info()[-1]
.to_opts.model``, ``Options.pk`` (+ its relation kind/target), and
``Field.get_transform(name) is not None`` — resolved through an integer-id
bridge over concrete Django model classes built for each scenario.

ORACLE: the REAL patched repo function per mapping.md section 1 — the inner
per-name walk of ``django.db.models.base.Model._check_ordering`` over one
related ordering path.  The gate applies patch.diff to /testbed and sets
PYTHONPATH=/testbed before this script runs, so ``import django`` resolves to
the patched module.  Each probe sets ``cls._meta.ordering = (path,)`` on the
root model and calls the real classmethod; the boolean observed is whether a
``models.E015`` error carrying exactly this path's lookup message is emitted
(the outer loop and message formatting are identity over this boolean, per
mapping.md section 2).

TYPE BRIDGE (mapping.md section 2): a related ordering path str, already
split on the lookup separator into name parts, is carried as ``List[int]`` of
name identifiers with the literal alias name ``pk`` <-> the reserved id 0;
model classes <-> distinct non-negative int ids with ``None`` <-> -1.  The
bridge dictionaries below realize exactly that bijection per scenario.

DOMAIN: the modelled walk is the per-related-path inner loop, i.e. paths of
>= 2 name parts (a path with no separator never reaches this loop); roots are
concrete models.  The abstraction keys transform admission on found *field*
objects (mapping.md: the last field is a (model, name) pair), so scenario
graphs use forward fields only (reverse accessors are suppressed via
``related_name='+'`` and the name pool is disjoint from accessor names).
A ``lower`` transform is registered on CharField so the transform-rescue
branch is exercised; both sides consult the same lookup registry.

>= 1e5 Requires-satisfying inputs: curated boundary paths over six scenario
graphs (relation chains, self-relations, a relational pk via model
inheritance, an explicit one-to-one pk, transform tails, missing/empty
names, attname aliases, long paths) + 100000 fuzz paths (random scenario,
root, and 2..6 name parts from the scenario pool).  Pinned fuzz seed: 11820.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib + django (the framework under test) only.
"""
import json
import os
import random
import sys
import tempfile

SEED = 11820
N_FUZZ = 100000


# --- Django setup: a throwaway app so dynamically-defined models register ----

_appdir = tempfile.mkdtemp(prefix='confcheck_')
_pkgdir = os.path.join(_appdir, 'confcheck')
os.makedirs(_pkgdir, exist_ok=True)
with open(os.path.join(_pkgdir, '__init__.py'), 'w'):
    pass
with open(os.path.join(_pkgdir, 'models.py'), 'w'):
    pass
with open(os.path.join(_pkgdir, 'apps.py'), 'w') as _f:
    _f.write(
        "from django.apps import AppConfig\n"
        "class ConfCheckConfig(AppConfig):\n"
        "    name = 'confcheck'\n"
        "    label = 'confcheck'\n"
    )
sys.path.insert(0, _appdir)

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=['confcheck.apps.ConfCheckConfig'],
    )

import django  # noqa: E402

django.setup()

from django.db import models  # noqa: E402
from django.core.exceptions import FieldDoesNotExist  # noqa: E402
from django.db.models.constants import LOOKUP_SEP  # noqa: E402
from django.db.models.functions import Lower  # noqa: E402

# Give CharField a registered transform so the transform-rescue branch is
# reachable; importing django.db.models.functions also registers the date
# extraction transforms.  Both shadow and oracle read the same registry.
models.CharField.register_lookup(Lower)


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

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- id bridge: integer model/name identifiers <-> real classes/strings ------
# Reserved: name id 0 <-> the literal alias name 'pk'; model id -1 <-> None.

MODEL_BY_ID = {}
ID_BY_MODEL = {}
NAME_BY_ID = {0: 'pk'}
ID_BY_NAME = {'pk': 0}


def model_id(cls):
    if cls not in ID_BY_MODEL:
        mid = len(MODEL_BY_ID)
        ID_BY_MODEL[cls] = mid
        MODEL_BY_ID[mid] = cls
    return ID_BY_MODEL[cls]


def name_id(s):
    if s not in ID_BY_NAME:
        nid = len(NAME_BY_ID)
        ID_BY_NAME[s] = nid
        NAME_BY_ID[nid] = s
    return ID_BY_NAME[s]


# --- @ContractOnly graph functions, backed by the REAL repo callees ----------

def resolve_kind(model, name):
    """Real Options.get_field + Field.is_relation over the id bridge:
    0 = resolves to nothing, 1 = relation field, 2 = non-relation field."""
    cls = MODEL_BY_ID[model]
    try:
        fld = cls._meta.get_field(NAME_BY_ID[name])
    except FieldDoesNotExist:
        return 0
    return 1 if fld.is_relation else 2


def relation_target(model, name):
    """Real fld.get_path_info()[-1].to_opts.model over the id bridge."""
    cls = MODEL_BY_ID[model]
    fld = cls._meta.get_field(NAME_BY_ID[name])
    return model_id(fld.get_path_info()[-1].to_opts.model)


def pk_kind(model):
    """Real Options.pk + is_relation: 1 = relation, 2 = non-relation."""
    cls = MODEL_BY_ID[model]
    return 1 if cls._meta.pk.is_relation else 2


def pk_target(model):
    """Real _meta.pk.get_path_info()[-1].to_opts.model over the id bridge."""
    cls = MODEL_BY_ID[model]
    return model_id(cls._meta.pk.get_path_info()[-1].to_opts.model)


def transform_present(field_model, field_name, name):
    """Real Field.get_transform(name) is not None, for the field identified
    by the (model, name) pair (name id 0 = the model's primary key)."""
    cls = MODEL_BY_ID[field_model]
    if field_name == 0:
        fld = cls._meta.pk
    else:
        fld = cls._meta.get_field(NAME_BY_ID[field_name])
    return fld.get_transform(NAME_BY_ID[name]) is not None


# --- pure region of model.py, contracts stripped (internal cross-check) ------

def walk_err(path, model, fld_model, fld_name):
    if len(path) == 0:
        return False
    name = path[0]
    rest = path.drop(1)
    if model == -1:
        # Nothing to resolve the name against: in error unless the last field
        # that was found admits the name as a registered transform.
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, -1, fld_model, fld_name)
    if name == 0:
        # The ``pk`` alias resolves to the model's primary-key field directly.
        if pk_kind(model) == 1:
            return walk_err(rest, pk_target(model), model, name)
        return walk_err(rest, -1, model, name)
    k = resolve_kind(model, name)
    if k == 0:
        # Resolves to nothing: error unless rescued by a transform on the last
        # field that was found (the current name was not assigned as a field).
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, model, fld_model, fld_name)
    if k == 1:
        return walk_err(rest, relation_target(model, name), model, name)
    # k == 2: ordinary non-relation field; no model to continue from.
    return walk_err(rest, -1, model, name)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def check_related_path(path, root):
    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
    n = len(path)
    i = 0
    acc = False
    model = root
    fld_model = root
    fld_name = -1
    while i < n:
        name = path[i]
        if model == -1:
            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                acc = True
            # model stays -1; fld unchanged
        elif name == 0:
            # pk alias: the field is found on the current model.
            fld_model = model
            fld_name = name
            if pk_kind(model) == 1:
                model = pk_target(model)
            else:
                model = -1
        else:
            k = resolve_kind(model, name)
            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                fld_model = model
                fld_name = name
                model = -1
        i = i + 1
    return acc


# --- oracle: the real patched per-path walk, observed via _check_ordering ----

def real_path_err(root_cls, path_str):
    """Whether the real (patched) validator reports this related path as a
    models.E015 error.  The ordering option carries exactly this one path."""
    root_cls._meta.ordering = (path_str,)
    want = "lookup '%s'." % path_str
    for e in root_cls._check_ordering():
        if getattr(e, 'id', None) == 'models.E015' and want in e.msg:
            return True
    return False


# --- scenario graphs (concrete Django models; forward fields only) -----------

_counter = [0]


def fresh(name):
    _counter[0] += 1
    return "%s%d" % (name, _counter[0])


def mk(base_name, fields, bases=(models.Model,)):
    attrs = dict(fields)
    attrs['__module__'] = 'confcheck.models'
    attrs['Meta'] = type('Meta', (), {'app_label': 'confcheck'})
    return type(fresh(base_name), bases, attrs)


def fk(target, **kw):
    kw.setdefault('related_name', '+')
    kw.setdefault('on_delete', models.CASCADE)
    return models.ForeignKey(target, **kw)


def build_scenarios():
    """Each scenario: (list of model classes, list of candidate name parts)."""
    scenarios = []

    # S1: one relation hop, two plain fields (the classic shapes).
    P1 = mk('ConfP', {'f1': models.CharField(max_length=20),
                      'f2': models.CharField(max_length=20)})
    C1 = mk('ConfC', {'parent': fk(P1)})
    scenarios.append(([P1, C1],
                      ['parent', 'f1', 'f2', 'pk', 'nope', 'lower', '',
                       'parent_id']))

    # S2: two-hop relation chain.
    A2 = mk('ConfA', {'x': models.IntegerField()})
    B2 = mk('ConfB', {'a': fk(A2)})
    C2 = mk('ConfC', {'b': fk(B2)})
    scenarios.append(([A2, B2, C2], ['a', 'b', 'x', 'pk', 'nope']))

    # S3: self-relation (unbounded chains of the same hop).
    S3 = mk('ConfS', {'parent': fk('self', null=True),
                      'val': models.IntegerField()})
    scenarios.append(([S3], ['parent', 'val', 'pk', 'nope']))

    # S4: relational primary key via model inheritance (parent link pk).
    Base4 = mk('ConfBase', {'name': models.CharField(max_length=20)})
    Der4 = mk('ConfDer', {'d1': models.IntegerField()}, bases=(Base4,))
    ptr_name = Der4._meta.pk.name
    scenarios.append(([Base4, Der4],
                      ['name', 'd1', 'pk', ptr_name, 'nope']))

    # S5: explicit relational primary key (one-to-one as pk).
    T5 = mk('ConfT', {'t': models.CharField(max_length=20)})
    O5 = mk('ConfO', {'target': models.OneToOneField(
                          T5, models.CASCADE, primary_key=True,
                          related_name='+'),
                      'o': models.IntegerField()})
    scenarios.append(([T5, O5], ['target', 't', 'o', 'pk', 'nope']))

    # S6: registered-transform tails (lower on char, year on date; none on int).
    TF6 = mk('ConfTF', {'c': models.CharField(max_length=20),
                        'i': models.IntegerField(),
                        'd': models.DateField()})
    U6 = mk('ConfU', {'tf': fk(TF6)})
    scenarios.append(([TF6, U6],
                      ['tf', 'c', 'i', 'd', 'pk', 'lower', 'year', 'nope']))

    return scenarios


# --- differential driver ------------------------------------------------------

def check(root_cls, parts):
    """Run shadow and oracle on one (root model, name parts) input; return an
    error string on disagreement, else None."""
    path_ids = [name_id(p) for p in parts]           # bridge: names -> ids
    root = model_id(root_cls)                        # bridge: model -> id
    shadow = check_related_path(path_ids, root)
    # internal cross-check: the impl region agrees with the pure fold
    if shadow != walk_err(ToSeq(path_ids), root, root, -1):
        return ("INTERNAL: impl region and pure fold disagree on root=%s "
                "path=%r" % (root_cls.__name__, parts))
    path_str = LOOKUP_SEP.join(parts)
    real = real_path_err(root_cls, path_str)
    if shadow != real:
        return ("DISAGREEMENT on root=%s path=%r (ids root=%d path=%r):\n"
                "  shadow (impl region)            = %r\n"
                "  real (patched repo _check_ordering E015) = %r"
                % (root_cls.__name__, path_str, root, path_ids, shadow, real))
    return None


def boundary_cases(scenarios):
    (m1, _), (m2, _), (m3, _), (m4, _), (m5, _), (m6, _) = scenarios
    P1, C1 = m1
    A2, B2, C2 = m2
    (S3,) = m3
    Base4, Der4 = m4
    T5, O5 = m5
    TF6, U6 = m6
    ptr = Der4._meta.pk.name
    cases = [
        # relation hop then plain / plain-then-more (the two headline shapes)
        (C1, ['parent', 'f1']),
        (C1, ['parent', 'f1', 'f2']),
        (C1, ['parent', 'pk']),
        (C1, ['parent', 'pk', 'nope']),
        (C1, ['parent', 'nope']),
        (C1, ['parent', 'parent']),
        (C1, ['pk', 'nope']),
        (C1, ['pk', 'pk']),
        (C1, ['nope', 'nope']),
        (C1, ['nope', 'parent', 'f1']),
        (C1, ['parent', '']),
        (C1, ['', 'parent']),
        (C1, ['parent_id', 'nope']),      # attname alias of the relation
        (C1, ['parent_id', 'f1']),
        (P1, ['f1', 'f2']),
        (P1, ['f1', 'lower']),
        (P1, ['f1', 'lower', 'lower']),
        (P1, ['f1', 'lower', 'nope']),
        (P1, ['pk', 'lower']),
        (P1, ['f1', 'f1']),
        # two-hop chains
        (C2, ['b', 'a', 'x']),
        (C2, ['b', 'a', 'pk']),
        (C2, ['b', 'a', 'x', 'nope']),
        (C2, ['b', 'x']),
        (C2, ['b', 'a', 'a']),
        (B2, ['a', 'x', 'x']),
        # self-relation chains (incl. a long one)
        (S3, ['parent', 'pk']),
        (S3, ['parent', 'parent', 'parent', 'pk']),
        (S3, ['parent', 'val', 'parent']),
        (S3, ['parent'] * 12 + ['val']),
        (S3, ['parent'] * 12 + ['nope']),
        # relational pk via inheritance: pk hop keeps walking
        (Der4, ['pk', 'name']),
        (Der4, ['pk', 'pk']),
        (Der4, ['pk', 'nope']),
        (Der4, ['pk', 'name', 'lower']),
        (Der4, [ptr, 'name']),
        (Der4, [ptr, 'pk', 'nope']),
        (Base4, ['pk', 'nope']),
        # explicit relational pk (one-to-one as pk)
        (O5, ['pk', 't']),
        (O5, ['pk', 'nope']),
        (O5, ['pk', 'pk', 'nope']),
        (O5, ['target', 't']),
        (O5, ['target', 'pk']),
        (O5, ['o', 'nope']),
        # transform tails
        (U6, ['tf', 'c', 'lower']),
        (U6, ['tf', 'c', 'lower', 'nope']),
        (U6, ['tf', 'c', 'nope']),
        (U6, ['tf', 'i', 'lower']),
        (U6, ['tf', 'd', 'year']),
        (U6, ['tf', 'd', 'year', 'nope']),
        (U6, ['tf', 'd', 'nope']),
        (U6, ['tf', 'pk', 'lower']),
        (TF6, ['c', 'lower']),
        (TF6, ['d', 'year']),
        (TF6, ['i', 'nope']),
    ]
    return cases


def main():
    scenarios = build_scenarios()

    checked = 0
    boundary = boundary_cases(scenarios)
    for root_cls, parts in boundary:
        err = check(root_cls, parts)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz: random scenario, random root, 2..6 name parts drawn
    # from the scenario's pool (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        mdls, pool = scenarios[rng.randrange(len(scenarios))]
        root_cls = mdls[rng.randrange(len(mdls))]
        n = rng.randint(2, 6)
        parts = [pool[rng.randrange(len(pool))] for _ in range(n)]
        err = check(root_cls, parts)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched _check_ordering per-path "
          "E015 verdict on %d inputs (%d boundary + %d fuzz over 6 scenario "
          "graphs, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"status": "pass", "checked": checked,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
