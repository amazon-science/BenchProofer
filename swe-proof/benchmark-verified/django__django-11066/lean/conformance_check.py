#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11066.

The bundle models ONE function: `RenameContentType._rename`
(`django/contrib/contenttypes/management/__init__.py`). Its Lean
implementation (`implementation_renameContentType`) renames one content-type
row, located on the database the migration runs against (`db`), and persists
the change to that SAME database:

    if not has_key(world[db], app_label, old_model):
        return world                       # DoesNotExist -> nothing changes
    target = db                            # save(using=db): explicit destination
    if rename_conflicts(world[target], app_label, old_model, new_model):
        return world                       # IntegrityError -> rollback, no change
    world[target] = rename_in_store(world[target], app_label, old_model, new_model)
    return world

This script transliterates that R/I impl into Python (`shadow_rename`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `_rename`:

    db = schema_editor.connection.alias
    try:
        ct = world[db].get_by_natural_key(app_label, old_model)
    except DoesNotExist:
        pass                               # nothing changes
    else:
        ct.model = new_model
        try:
            with transaction.atomic(using=db):
                ct.save(using=db, update_fields={'model'})   # <-- the fix: write lands on db
        except IntegrityError:             # unique (app_label, model) collision
            ct.model = old_model           # atomic() rolled the write back: no change

We do NOT stand up Django/ORM (heavy, and the modeled value is a pure decision
over which database the write is directed to). Instead we reproduce the patched
routing with light stand-in stores: a multi-database `world` mapping each alias
to its list of `(app_label, model)` rows (mapping.md). The read uses
`db_manager(db)` (explicitly `db`); the post-patch save uses `using=db`, so the
write lands on `db` regardless of the router's free `db_for_write` choice.

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`saveTarget routerChoice (some db) = db` (an explicit destination overrides the
router), whereas the oracle reproduces the patched `save(using=db)` routing. The
free `routerChoice` is fed to BOTH legs and must be IRRELEVANT to the outcome —
in particular when `routerChoice != db` with the row present on `db`, the case
the patch fixes (pre-fix the write would have leaked to `routerChoice`).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11066 (also recorded in
mapping.md).
"""
import sys

SEED = 11066
N = 120_000


# --- helpers shared by both legs ---------------------------------------------
def matches_key(row, app_label, old_model):
    # row is a (app_label, model) tuple
    return row[0] == app_label and row[1] == old_model


def has_key(store, app_label, old_model):
    return any(matches_key(r, app_label, old_model) for r in store)


def rename_in_store(store, app_label, old_model, new_model):
    out = []
    for r in store:
        if matches_key(r, app_label, old_model):
            out.append((r[0], new_model))
        else:
            out.append(r)
    return out


def rename_conflicts(store, app_label, old_model, new_model):
    # Persisting the rename violates the unique (app_label, model) constraint
    # iff it targets a genuinely different model name and the destination key
    # already exists in the store receiving the write.
    return new_model != old_model and has_key(store, app_label, new_model)


# --- ORACLE: the post-patch _rename, faithful in-process replica -------------
# `world` is a dict alias -> list of (app_label, model) rows. The read is on
# `db` (db_manager(db).get_by_natural_key); the save uses using=db, so the write
# lands on `db`. `router_choice` is what the router's db_for_write WOULD pick;
# the post-patch save passes using=db and therefore ignores it.
def oracle_rename(world, db, router_choice, app_label, old_model, new_model):
    result = {a: list(rows) for a, rows in world.items()}
    # read the row from db; DoesNotExist -> nothing changes
    if not has_key(world.get(db, []), app_label, old_model):
        return result
    # ct.model = new_model; ct.save(using=db) -> write directed to db.
    # The write is wrapped in transaction.atomic(using=db): if it collides with
    # the unique (app_label, model) constraint on db, IntegrityError is raised,
    # the atomic block rolls the write back, and the except branch restores
    # ct.model = old_model -> nothing is persisted anywhere.
    if rename_conflicts(world.get(db, []), app_label, old_model, new_model):
        return result
    result[db] = rename_in_store(world.get(db, []), app_label, old_model, new_model)
    return result


# --- shadow of implementation_renameContentType (the R/I leg) ----------------
# Mirrors Solution.lean: locate on db; if absent return world; else
# target = saveTarget router_choice (some db) = db; apply renameInStore there.
def save_target(router_choice, using):
    return using if using is not None else router_choice


def shadow_rename(world, db, router_choice, app_label, old_model, new_model):
    result = {a: list(rows) for a, rows in world.items()}
    if not has_key(world.get(db, []), app_label, old_model):
        return result
    target = save_target(router_choice, db)   # some db -> db
    # renameConflicts (world target): the receiving database's unique
    # natural-key constraint rejects a colliding rename -> rollback, no change.
    if rename_conflicts(world.get(target, []), app_label, old_model, new_model):
        return result
    result[target] = rename_in_store(world.get(target, []), app_label, old_model, new_model)
    return result


def disagree(world, db, router_choice, app_label, old_model, new_model):
    got = oracle_rename(world, db, router_choice, app_label, old_model, new_model)
    want = shadow_rename(world, db, router_choice, app_label, old_model, new_model)
    if got != want:
        return ((world, db, router_choice, app_label, old_model, new_model), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the discriminating routing clause."""
    # Two databases; 'other'==0 holds the row, 'default'==1 is the router target.
    cases = [
        # THE fix: row present on db=0, router would route to 1 (router_choice != db)
        ({0: [(7, 100)], 1: []}, 0, 1, 7, 100, 200),
        # router coincides with db -> unchanged behaviour either way
        ({0: [(7, 100)], 1: []}, 0, 0, 7, 100, 200),
        # row absent on db -> DoesNotExist -> nothing changes anywhere
        ({0: [], 1: [(7, 100)]}, 0, 1, 7, 100, 200),
        # row present on a non-db database only; db has no such row -> no change
        ({0: [(7, 100)], 1: [(7, 100)]}, 1, 0, 7, 100, 200),
        # row present on db, router_choice points at a third database
        ({0: [(7, 100)], 1: [], 2: []}, 0, 2, 7, 100, 200),
        # multiple rows, only the matching natural key renamed
        ({0: [(7, 100), (7, 101), (8, 100)], 1: []}, 0, 1, 7, 100, 200),
        # empty world entirely
        ({0: [], 1: []}, 0, 1, 7, 100, 200),
        # new_model == old_model (no observable change but routing still on db)
        ({0: [(7, 100)], 1: []}, 0, 1, 7, 100, 100),
        # unique-key collision on db: (7,200) already exists -> IntegrityError,
        # rollback, nothing persisted anywhere (the G-PANEL-2 counterexample)
        ({0: [(7, 100), (7, 200)], 1: []}, 0, 1, 7, 100, 200),
        # collision row lives only on a NON-db database -> no conflict on db,
        # rename proceeds on db
        ({0: [(7, 100)], 1: [(7, 200)]}, 0, 1, 7, 100, 200),
        # new_model == old_model with the key present: not a conflict (the row
        # being renamed IS the destination key), write proceeds (a no-op)
        ({0: [(7, 100), (8, 100)], 1: []}, 0, 1, 7, 100, 100),
    ]
    return cases


def _rand_store(rnd):
    length = next(rnd) % 7            # 0..6 rows
    rows = []
    for _ in range(length):
        app = next(rnd) % 4          # app_label 0..3
        model = next(rnd) % 5        # model 0..4 (repeats so keys collide)
        rows.append((app, model))
    return rows


def _rand_world(rnd, aliases):
    return {a: _rand_store(rnd) for a in aliases}


def main() -> int:
    checked = 0

    for world, db, rc, app, old, new in _enumerate_edge():
        d = disagree(world, db, rc, app, old, new)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        n_alias = 2 + (next(rnd) % 3)        # 2..4 aliases
        aliases = list(range(n_alias))
        world = _rand_world(rnd, aliases)
        db = next(rnd) % n_alias
        router_choice = next(rnd) % n_alias  # may or may not equal db
        app = next(rnd) % 4
        old = next(rnd) % 5
        new = next(rnd) % 5
        d = disagree(world, db, router_choice, app, old, new)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
