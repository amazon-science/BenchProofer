#!/usr/bin/env python3
"""G-CONF for django__django-15695.

The gold patch is already applied to /testbed when this runs, so the REAL
`RenameIndex.database_forwards` carries the added guard. We compare the R/I
Python shadow of `implementation_applyIndexRenameForward` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`database_forwards`, driven over lightweight recording fakes for the state and
schema-editor objects, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

What the modeled decision reads (mapping.md):
  canMigrate : Bool         <-> self.allow_migrate_model(alias, model) result
  oldIndex   : Index{name}  <-> old_index (resolved by get_index_by_name)
  newIndex   : Index{name}  <-> new_index (resolved by get_index_by_name)
  newName    : String       <-> self.new_name
  result : Option (Index x Index)
                            <-> the at-most-one schema_editor.rename_index call:
                                none  -> no rename_index call emitted
                                some (oldIndex,newIndex) -> rename_index(old,new)

We bypass the upstream old_fields-vs-old_name split (both branches converge to a
single old_index; mapping.md) by exercising the named branch and feeding the
resolved old_index.name directly via the fakes. The post-decision call
`rename_index(model, old_index, new_index)` is captured by a recording fake; its
(old.name, new.name) is the observable we diff.

stdlib-only; no hypothesis required.
"""
import random
import sys
import types

import django
from django.conf import settings

if not settings.configured:
    settings.configure(DEBUG=False, DATABASES={}, INSTALLED_APPS=[])
    django.setup()

from django.db.migrations.operations.models import RenameIndex


class FakeIndex:
    def __init__(self, name):
        self.name = name


class FakeModelState:
    """Stands in for a ModelState; get_index_by_name returns the index we pinned."""
    def __init__(self, index):
        self._index = index

    def get_index_by_name(self, name):
        return self._index


class FakeStateModels(dict):
    pass


class FakeApps:
    def get_model(self, app_label, model_name):
        return object()  # the `model` arg is only forwarded to rename_index


class FakeState:
    def __init__(self, models_map, apps=None):
        self.models = models_map
        self.apps = apps or FakeApps()


class FakeConnection:
    alias = "default"


class RecordingSchemaEditor:
    def __init__(self):
        self.connection = FakeConnection()
        self.calls = []

    def rename_index(self, model, old_index, new_index):
        self.calls.append((old_index.name, new_index.name))


APP_LABEL = "app"
MODEL_NAME = "Pony"


def oracle(can_migrate, old_name, new_name, new_index_name):
    """Real patched RenameIndex.database_forwards behavior.

    Returns: None if no rename_index emitted, else (old_index.name, new_index.name).
    """
    op = RenameIndex(model_name=MODEL_NAME, new_name=new_name, old_name=old_name)
    # Force the allow_migrate_model decision (canMigrate).
    op.allow_migrate_model = types.MethodType(
        lambda self, alias, model: can_migrate, op
    )
    old_index = FakeIndex(old_name)
    new_index = FakeIndex(new_index_name)
    key = (APP_LABEL, MODEL_NAME.lower())
    from_state = FakeState(FakeStateModels({key: FakeModelState(old_index)}))
    to_state = FakeState(FakeStateModels({key: FakeModelState(new_index)}))
    editor = RecordingSchemaEditor()
    op.database_forwards(APP_LABEL, editor, from_state, to_state)
    if not editor.calls:
        return None
    assert len(editor.calls) == 1
    return editor.calls[0]


def shadow(can_migrate, old_name, new_name, new_index_name):
    """R/I transliteration of implementation_applyIndexRenameForward (Lean).

    canMigrate -> can_migrate ; oldIndex.name -> old_name ; newName -> new_name ;
    newIndex.name -> new_index_name. Result mirrored as the (old,new) name pair or
    None.
    """
    if can_migrate is False:                 # `if canMigrate = false then return none`
        return None
    if old_name == new_name:                 # `if oldIndex.name = newName then return none`
        return None
    return (old_name, new_index_name)        # `return some (oldIndex, newIndex)`


NAME_POOL = [
    "idx_a", "idx_b", "new_pony_test_idx", "pony_pink_weight_idx",
    "old_idx", "auto_generated_8a1b", "x", "z2",
]


def rand_name(rng):
    return rng.choice(NAME_POOL)


def main():
    rng = random.Random(15695)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    saw_equal = 0
    saw_emit = 0
    for _ in range(N):
        can_migrate = rng.random() < 0.8       # mostly permitted, some blocked
        old_name = rand_name(rng)
        new_name = rand_name(rng)              # small pool => frequent collisions
        new_index_name = rand_name(rng)
        if can_migrate and old_name == new_name:
            saw_equal += 1
        o = oracle(can_migrate, old_name, new_name, new_index_name)
        s = shadow(can_migrate, old_name, new_name, new_index_name)
        if s is not None:
            saw_emit += 1
        if o != s:
            disagreements += 1
            if first is None:
                first = (can_migrate, old_name, new_name, new_index_name, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements "
          "(equal-name noops exercised=%d, emits=%d)" % (N, saw_equal, saw_emit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
