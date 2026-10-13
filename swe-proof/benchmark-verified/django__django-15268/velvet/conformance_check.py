#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15268.

Refutes the R/I refinement leg of the optimization-eligibility decision modeled
in Solution.lean (`reorderableBase`, `reorderableTogether`, `optimizeAgainst`,
and the pure helpers `affectsModel` / `isTogetherOp` / `sameKind` / `mergeable`).
There are NO axioms in this bundle: every op is pure boolean/enum logic over the
features the decision observes, so the whole impl region is R/I-tagged
(conf_skip=false).

ORACLE — the REAL patched operation classes.
  Unlike the admin/inline bundles, the migration `Operation` classes instantiate
  WITHOUT a database, app registry, or request: `AlterUniqueTogether(name, set())`,
  `AlterIndexTogether(name, set())`, `DeleteModel(name)`, `AlterModelTable(name,
  table)` are plain Python objects, and `op.reduce(other, app_label)` /
  `op.can_reduce_through(other, app_label)` / `other.references_model(name,
  app_label)` are pure attribute/identity logic. So the ORACLE is the REAL
  patched `django/db/migrations/operations/models.py` (patch.diff applied at
  base_commit): we instantiate the actual classes and call the actual
  `op.reduce(...)`, mapping its result to the three-valued OptimizeOutcome:

      list  -> merge        (optimizer replaces the pair with one op)
      True  -> reorderable  (optimizer may advance `op` across `other`)
      False -> blocked      (optimizer stops scanning)

  `reduce`'s value is exactly what `MigrationOptimizer.optimize_inner`
  (django/db/migrations/optimizer.py) branches on, so this is the observable the
  fix changes.

TYPE BRIDGE (mapping.md §2):
  selfKind  unique/index  <-> AlterUniqueTogether / AlterIndexTogether
  selfName  Nat           <-> model name "m{n}" (only equality observed)
  OtherOp.together n k     <-> Alter{Unique,Index}Together("m{n}", set())
  OtherOp.deleteModel n    <-> DeleteModel("m{n}")
  OtherOp.generic refsSelf elidable
                           <-> a real NON-together, NON-delete operation whose
                               (unchanged) `references_model("m{self}")` realizes
                               the free `refsSelf` bit and whose (unchanged)
                               `elidable` attribute realizes the free `elidable`
                               bit. Realizations:
                                 (refsSelf, elidable=False): AlterModelTable —
                                   references_model is name identity (refsSelf
                                   <-> same model name), elidable is the class
                                   default False.
                                 (refsSelf=True, elidable=True): RunSQL(...,
                                   elidable=True) — base Operation.
                                   references_model returns True.
                                 (refsSelf=False, elidable=True): a minimal
                                   RunSQL subclass overriding references_model
                                   to False (Django's documented extension
                                   points: `elidable` and `references_model`
                                   are public Operation API any user operation
                                   may set/override; the reduce machinery under
                                   test is entirely Django's).
                               Operation.reduce's `elif operation.elidable:
                               return [self]` branch (base.py) makes an elidable
                               neighbour MERGE regardless of references_model —
                               the case the model's `mergeable` now carries.

The SHADOW is the model from Solution.lean transliterated verbatim. We
differential-test SHADOW vs ORACLE over fuzzed (selfName, selfKind, other)
triples, with boundary cases first. Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 15268
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------
# OtherOp encodings (kind: 'unique'|'index'):
#   ('together', name, kind) | ('delete', name)
#   | ('generic', refsSelf:bool, elidable:bool)

def affects_model(self_name, other):
    tag = other[0]
    if tag == 'together':
        return other[1] == self_name
    if tag == 'delete':
        return True                # DeleteModel.references_model is always True
    return bool(other[1])          # generic: refsSelf


def is_together_op(other):
    return other[0] == 'together'


def same_kind(self_kind, other):
    return other[0] == 'together' and other[2] == self_kind


def mergeable(self_name, self_kind, other):
    tag = other[0]
    if tag == 'together':
        return other[2] == self_kind and other[1] == self_name
    if tag == 'delete':
        return other[1] == self_name
    return bool(other[2])          # generic: elidable neighbour merges


def shadow_reorderable_base(self_name, other):
    return (not affects_model(self_name, other))


def shadow_reorderable_together(self_name, self_kind, other):
    return shadow_reorderable_base(self_name, other) or (
        is_together_op(other) and not same_kind(self_kind, other))


def shadow_optimize_against(self_name, self_kind, other):
    if mergeable(self_name, self_kind, other):
        return 'merge'
    if shadow_reorderable_together(self_name, self_kind, other):
        return 'reorderable'
    return 'blocked'


# ---- ORACLE: real patched django operation classes ------------------------

def _load_real_classes():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
        django.setup()
    from django.db.migrations.operations.models import (
        AlterUniqueTogether, AlterIndexTogether, DeleteModel, AlterModelTable,
    )
    from django.db.migrations.operations.special import RunSQL
    return (AlterUniqueTogether, AlterIndexTogether, DeleteModel,
            AlterModelTable, RunSQL)


def main():
    try:
        AUT, AIT, DM, AMT, RunSQL = _load_real_classes()
    except Exception as e:  # pragma: no cover
        print("G-CONF ERROR: could not load real django operation classes: %r" % e)
        return 2

    APP = "myapp"

    # (refsSelf=False, elidable=True): a real elidable operation whose
    # (unchanged, overridable-by-design) references_model answers False.
    class NoRefRunSQL(RunSQL):
        def references_model(self, name, app_label):
            return False

    def name_of(n):
        return "m%d" % n

    def make_self(self_name, self_kind):
        cls = AUT if self_kind == 'unique' else AIT
        return cls(name_of(self_name), set())

    def make_other(self_name, other):
        tag = other[0]
        if tag == 'together':
            cls = AUT if other[2] == 'unique' else AIT
            return cls(name_of(other[1]), set())
        if tag == 'delete':
            return DM(name_of(other[1]))
        # generic (refsSelf, elidable): realized by real non-together /
        # non-delete operations.
        refs_self, elidable = bool(other[1]), bool(other[2])
        if elidable:
            # RunSQL's references_model is the base Operation's (always True);
            # for refsSelf=False use the subclass overriding it to False.
            return (RunSQL("SELECT 1", elidable=True) if refs_self
                    else NoRefRunSQL("SELECT 1", elidable=True))
        # non-elidable: AlterModelTable, whose (unchanged) references_model
        # realizes refsSelf via name identity. refsSelf True -> same model
        # name as self; False -> a distinct model name.
        gen_name = self_name if refs_self else self_name + 1000
        return AMT(name_of(gen_name), "tbl")

    def oracle_outcome(self_name, self_kind, other):
        s = make_self(self_name, self_kind)
        o = make_other(self_name, other)
        res = s.reduce(o, APP)
        if isinstance(res, list):
            return 'merge'
        if res is True:
            return 'reorderable'
        if res is False:
            return 'blocked'
        raise AssertionError("unexpected reduce result: %r" % (res,))

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def cases():
        kinds = ['unique', 'index']
        # Boundary / F2P-shaped cases first.
        # different-flavour, same model -> the fix's discriminator (reorderable)
        yield (0, 'unique', ('together', 0, 'index'))
        yield (0, 'index', ('together', 0, 'unique'))
        # same-flavour, same model -> merge
        yield (0, 'unique', ('together', 0, 'unique'))
        yield (0, 'index', ('together', 0, 'index'))
        # different-flavour, DIFFERENT model -> reorderable (base already true)
        yield (0, 'unique', ('together', 1, 'index'))
        # same-flavour, different model -> reorderable (base true)
        yield (0, 'unique', ('together', 1, 'unique'))
        # delete of my model -> merge ; delete of other model -> reorderable
        yield (0, 'unique', ('delete', 0))
        yield (0, 'unique', ('delete', 1))
        # generic (non-elidable) touching my model -> blocked ;
        # not touching -> reorderable
        yield (0, 'unique', ('generic', True, False))
        yield (0, 'index', ('generic', False, False))
        # generic ELIDABLE -> merge regardless of references_model
        # (Operation.reduce's `elif operation.elidable: return [self]` branch)
        yield (0, 'unique', ('generic', True, True))
        yield (0, 'unique', ('generic', False, True))
        yield (0, 'index', ('generic', True, True))
        yield (0, 'index', ('generic', False, True))
        # Fuzz.
        for _ in range(N_FUZZ):
            sk = rng.choice(kinds)
            sn = rng.randint(0, 3)
            t = rng.randint(0, 2)
            if t == 0:
                other = ('together', rng.randint(0, 3), rng.choice(kinds))
            elif t == 1:
                other = ('delete', rng.randint(0, 3))
            else:
                other = ('generic', rng.random() < 0.5, rng.random() < 0.5)
            yield (sn, sk, other)

    for sn, sk, other in cases():
        count += 1
        shadow = shadow_optimize_against(sn, sk, other)
        oracle = oracle_outcome(sn, sk, other)
        if shadow != oracle:
            disagreements.append((sn, sk, other, shadow, oracle))
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of optimizeAgainst (reorderableBase / "
          "reorderableTogether / mergeable) agrees with the real patched "
          "AlterFooTogether.reduce on %d checks "
          "(boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
