#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14559 (nagini).

SHADOW: the impl region of model.py's `bulk_apply_count`, copied verbatim
below with the contract calls (Invariant/Assert) stripped. `ToSeq` / PSeq
become a plain tuple shim with `take`/`drop`. The single @ContractOnly callee,
`matched_rows`, calls the REAL repo primitive it models per mapping.md §3.1 —
the per-group filtered update `QuerySet.filter(pk__in=group_keys).update(...)`
— so the shadow exercises the genuine per-group report, not a re-model of it.

ORACLE: the REAL repo function the model models per mapping.md §1 —
`django.db.models.query.QuerySet.bulk_update(objs, fields, batch_size=None)`.
The gate applies the diff to /testbed before this script runs and sets
PYTHONPATH=/testbed; this script never applies any diff itself.

Type bridge (mapping.md §2):
  objs (model instances)            -> keys: List[int] of primary-key values,
                                       order and multiplicity preserved
  effective batch size              -> group_size: int >= 1; computed with the
                                       real backend primitive
                                       ops.bulk_batch_size(['pk','pk']+fields,
                                       objs) exactly as the operation does
                                       (user value capped by the backend
                                       maximum; backend maximum when the user
                                       passes none)
  the callable's return value       -> Optional[int]: None <-> the absent
                                       value, an int <-> the produced count
The Requires (group_size >= 1) holds by construction: the backend maximum is a
positive int and generated user batch sizes are None or >= 1.

Both sides run against the same in-memory sqlite database. The per-group
report depends only on which primary keys currently have a stored row (never
on prior field values), so interleaving the oracle's and the shadow's update
calls cannot perturb either side's counts; row existence is held fixed during
checking (live rows are created up front, "ghost" keys are rows deleted via a
queryset delete so the in-memory instances keep their pk values).

>= 1e5 Requires-satisfying inputs: structured boundary cases (empty
collection, single key, duplicates within one group vs. split across groups,
absent keys, group size 1 / equal to / larger than the collection, a
collection larger than the backend maximum group size) plus 100000 fuzz
configurations. Pinned fuzz seed: 145590.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 145590
N_FUZZ = 100_000


# --- PSeq shim: plain-tuple sequence with take/drop -------------------------

class Seq:
    __slots__ = ("items",)

    def __init__(self, items):
        self.items = tuple(items)

    def take(self, n):
        return Seq(self.items[:max(n, 0)])

    def drop(self, n):
        return Seq(self.items[max(n, 0):])

    def __len__(self):
        return len(self.items)


def ToSeq(keys):
    return Seq(keys)


# --- @ContractOnly callee: the REAL repo primitive --------------------------
# matched_rows(group_keys) is axiomatized in model.py; here it invokes the
# real per-group filtered update and returns the DB-reported matched-row
# count. Row and a fresh value counter are installed by main().

_ROW = None
_STAMP = [0]


def matched_rows(group_keys):
    _STAMP[0] += 1
    return _ROW.objects.filter(pk__in=list(group_keys.items)).update(
        note="s%d" % (_STAMP[0] % 97,))


# --- the impl region of model.py, verbatim, contract calls stripped ---------

def bulk_apply_count(keys, group_size):
    total = 0
    if len(keys) == 0:
        return 0
    off = 0
    while off < len(keys):
        rem = ToSeq(keys).drop(off)
        step = group_size
        if step > len(keys) - off:
            step = len(keys) - off
        total = total + matched_rows(rem.take(group_size))
        off = off + step
    return total


# --- environment ------------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    global _ROW
    _configure_django()
    from django.db import connection, connections, models

    # A minimal, dependency-free model with one updatable concrete field.
    # An already-installed app_label so setup succeeds without a stub app.
    class Row(models.Model):
        note = models.CharField(max_length=32, default="")

        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(Row)
    _ROW = Row

    field_objs = [Row._meta.get_field("note")]

    def effective_group_size(user_bs, objs):
        """The effective group size the real operation splits `objs` into,
        computed with the same real backend primitive: the user value capped
        by the backend maximum, or the backend maximum when absent."""
        max_bs = connections["default"].ops.bulk_batch_size(
            ["pk", "pk"] + field_objs, objs)
        eff = min(user_bs, max_bs) if user_bs else max_bs
        assert eff >= 1  # the model's Requires holds by construction
        return eff

    def check_one(objs, user_bs, label):
        """Run the REAL patched operation and the shadow on the bridged input;
        return an error string on disagreement."""
        _STAMP[0] += 1
        real = Row.objects.bulk_update(objs, ["note"],
                                       batch_size=user_bs)
        keys = [o.pk for o in objs]
        eff = effective_group_size(user_bs, objs)
        shadow = bulk_apply_count(keys, eff)
        # bridge the return value: the absent value never equals a count
        if real is None or real != shadow:
            return ("DISAGREEMENT (%s)\n  keys=%r user_batch_size=%r "
                    "effective_group_size=%r\n  shadow=%r  real=%r"
                    % (label, keys, user_bs, eff, shadow, real))
        return None

    # ---- fixed population: live rows first, then ghosts (rows deleted via a
    # queryset delete so the instances keep their pk attribute) --------------
    live = [Row.objects.create(note="x") for _ in range(60)]
    ghosts = [Row.objects.create(note="g") for _ in range(12)]
    Row.objects.filter(pk__in=[g.pk for g in ghosts]).delete()

    checked = 0

    def run_case(objs, user_bs, label):
        nonlocal checked
        # touch the value each object carries so the operation always has a
        # concrete field value to write
        for o in objs:
            o.note = "v%d" % (checked % 89,)
        err = check_one(list(objs), user_bs, label)
        checked += 1
        return err

    # ---- boundary cases -----------------------------------------------------
    a, b, c = live[0], live[1], live[2]
    g0, g1 = ghosts[0], ghosts[1]
    boundary = [
        # empty collection, with and without an explicit group size
        ([], None), ([], 1), ([], 5),
        # single present key
        ([a], None), ([a], 1), ([a], 7),
        # single absent key
        ([g0], None), ([g0], 1),
        # duplicates within ONE group (collapsed to a single-group report)
        ([a, a], None), ([a, a], 2), ([a, a], 5),
        # the same duplicate split across SEPARATE groups (summed per group)
        ([a, a], 1),
        ([a, b, a], 1), ([a, b, a], 2), ([a, b, a], 3),
        # triples of one key across group sizes
        ([a, a, a], 1), ([a, a, a], 2), ([a, a, a], 3), ([a, a, a], None),
        # mixed present/absent, various group sizes
        ([a, g0], 1), ([a, g0], 2), ([g0, g1], None), ([g0, g0], 1),
        ([a, g0, b, g1, c], 1), ([a, g0, b, g1, c], 2),
        ([a, g0, b, g1, c], 4), ([a, g0, b, g1, c], 5),
        ([a, g0, b, g1, c], 100), ([a, g0, b, g1, c], None),
        # group size equal to / one off / far beyond the collection length
        (live[:8], 8), (live[:8], 7), (live[:8], 9), (live[:8], 10 ** 6),
        # every key present, group size 1 (maximal splitting)
        (live[:10], 1),
        # duplicates saturating several groups
        ([a] * 9 + [b] * 3, 4), ([a, b] * 6, 3), ([a, b] * 6, 2),
    ]
    for objs, user_bs in boundary:
        err = run_case(objs, user_bs, "boundary")
        if err:
            print(err)
            return 1

    # a collection larger than the backend maximum group size, no explicit
    # group size: exercises the cap and multiple full groups
    big = [live[i % len(live)] for i in range(400)]
    err = run_case(big, None, "boundary-large")
    if err:
        print(err)
        return 1
    n_boundary = checked

    # ---- fuzz ---------------------------------------------------------------
    rng = random.Random(SEED)
    pool = live + ghosts
    for _ in range(N_FUZZ):
        r = rng.random()
        if r < 0.15:
            n = 0
        elif r < 0.90:
            n = rng.randint(1, 8)
        else:
            n = rng.randint(9, 30)
        objs = [rng.choice(pool) for _ in range(n)]
        # bias toward duplicate-heavy collections now and then
        if n >= 2 and rng.random() < 0.25:
            objs = [rng.choice(objs) for _ in range(n)]
        if rng.random() < 0.30:
            user_bs = None
        else:
            user_bs = rng.randint(1, n + 3)
        err = run_case(objs, user_bs, "fuzz")
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real patched batched-update return on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
