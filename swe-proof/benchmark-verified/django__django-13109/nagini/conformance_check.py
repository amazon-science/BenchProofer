#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13109 (nagini).

SHADOW: the impl region of model.py's ``validate_reference``, copied verbatim
below with the contract calls (Requires/Ensures/Exsures/Invariant/Assert and
the MustTerminate obligation) stripped. The model IS Python: the carriers are
plain ``List[int]`` and the loop runs directly. The one @Pure @ContractOnly
callee, ``choice_permitted`` (the A-consumed axiom, mapping.md section 3.1),
delegates to the REAL repo callee: whether the single row carrying the key
survives ``QuerySet.complex_filter(field.get_limit_choices_to())`` — memoized
per database state, since the axiom pins a deterministic per-key predicate.

ORACLE: the REAL patched repo function the model models per mapping.md —
``django.db.models.fields.related.ForeignObject.validate`` driven through a
concrete ``ForeignKey``. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable.

TYPE BRIDGE (mapping.md section 2):

  * a row collection <-> the ``List[int]`` of its rows' referenced-field keys:
      ``complete_rows`` = keys from the target model's unfiltered manager
      (every stored row); ``curated_rows`` = keys from its default manager,
      which here applies a standing ``archived=False`` filter and so exposes
      a subset (asserted per snapshot);
  * ``value: int`` <-> the candidate reference value (the referenced field is
      the integer pk, so the carrier is exact);
  * ``choice_permitted(key)`` <-> the per-field choice restriction: the row
      carrying ``key`` survives ``complex_filter(get_limit_choices_to())``
      (vacuously permitted when no row carries the key — the membership
      conjunct is then already false, so the conjunction is unaffected);
  * ``ReferenceInvalid`` <-> ``ValidationError``: only the raise/no-raise
      outcome is the pinned observable, not the message payload.

FIXTURES: a target model whose default manager hides ``archived=True`` rows
while the unfiltered manager returns everything, referenced by TWO foreign
keys — one with no choice restriction (empty restriction admits every key)
and one restricted to ``flag=True`` rows — so both arms of the
``choice_permitted`` conjunct are exercised against the real callee. The
upstream guards the model discloses as out-of-scope (``value is None``,
``parent_link``) are outside the int input domain / fixture by construction.

INPUT DOMAIN: the shadow's Requires demands only read access to the two int
lists; every (value, snapshot) pair drawn below satisfies it. The database
population is mutated across 10 phases (empty table; live rows; hidden rows;
restriction-failing rows; deletions creating key gaps; random churn), and per
phase every input is checked against BOTH foreign keys. Boundary values per
phase: every stored key (each hidden/visible x restricted/unrestricted cell),
every deleted key, 0, -1, and keys just past both ends of the stored range.
Fuzz: uniform ints straddling the stored key range. Pinned seed: 13109.

>= 1e5 Requires-satisfying inputs total (counted checks, asserted at the
end). Exit 0 iff zero disagreements; on disagreement prints the input and
both outcomes and exits 1. stdlib + Django (the framework under test,
present in the image) only.
"""
import json
import random
import sys

SEED = 13109
MIN_CHECKS = 100_000
PHASES = 10
FUZZ_PER_PHASE_PER_FIELD = 5_200


# --- the impl region of model.py, verbatim, contract calls stripped ----------

class ReferenceInvalid(Exception):
    pass


def validate_reference(value, complete_rows, curated_rows):
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `present` (one unfold per step).
    found = False  # type: bool
    i = len(complete_rows)
    while i > 0:
        if complete_rows[i - 1] == value:
            found = True
        i = i - 1
    if not (found and choice_permitted(value)):
        raise ReferenceInvalid()
    return


# `choice_permitted` is the model's @Pure @ContractOnly axiom (A-consumed):
# a deterministic per-key predicate. Here it calls the REAL repo callee via
# the bridge installed per (field, database-state) below.
_REAL_CHOICE_PERMITTED = None


def choice_permitted(key):
    return _REAL_CHOICE_PERMITTED(key)


def shadow_rejects(value, complete_rows, curated_rows):
    try:
        validate_reference(value, complete_rows, curated_rows)
        return False
    except ReferenceInvalid:
        return True


# --- the differential check ---------------------------------------------------

def main():
    global _REAL_CHOICE_PERMITTED

    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.core.exceptions import ValidationError
    from django.db import connection, models

    # Target model: default manager applies a standing filter (hides
    # archived rows); the unfiltered manager returns every stored row.
    class VisibleManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(archived=False)

    class Target(models.Model):
        archived = models.BooleanField(default=False)
        flag = models.BooleanField(default=True)
        objects = VisibleManager()

        class Meta:
            app_label = "confcheck"

    class Referrer(models.Model):
        # one reference with no choice restriction, one restricted to
        # flag=True rows: both arms of the choice conjunct get exercised.
        plain = models.ForeignKey(Target, on_delete=models.CASCADE,
                                  related_name="+")
        choosy = models.ForeignKey(Target, on_delete=models.CASCADE,
                                   related_name="+",
                                   limit_choices_to={"flag": True})

        class Meta:
            app_label = "confcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Target)
        editor.create_model(Referrer)

    fields = [Referrer._meta.get_field("plain"),
              Referrer._meta.get_field("choosy")]
    instance = Referrer()

    def make_real_choice_permitted(fk):
        """Bridge for the axiom: the REAL restriction callee. A key is
        permitted iff the row carrying it survives
        complex_filter(get_limit_choices_to()); a key carried by no row is
        vacuously permitted (the membership conjunct is already false).
        Memoized: the axiom pins a deterministic per-key predicate for a
        fixed database state."""
        target = fk.remote_field.model
        field_name = fk.remote_field.field_name
        restriction = fk.get_limit_choices_to()
        memo = {}

        def permitted(key):
            if key not in memo:
                qs = target._base_manager.filter(**{field_name: key})
                memo[key] = ((not qs.exists())
                             or qs.complex_filter(restriction).exists())
            return memo[key]

        return permitted

    def real_rejects(fk, value):
        try:
            fk.validate(value, instance)
            return False
        except ValidationError:
            return True

    def snapshot(fk):
        target = fk.remote_field.model
        complete = list(target._base_manager.values_list("pk", flat=True))
        curated = list(target._default_manager.values_list("pk", flat=True))
        # bridge sanity: the curated collection is a subset of the complete one
        assert set(curated) <= set(complete), (
            "default-manager keys must be a subset of the unfiltered keys")
        return complete, curated

    def describe_rows():
        return [
            {"pk": r.pk, "archived": r.archived, "flag": r.flag}
            for r in Target._base_manager.order_by("pk")
        ]

    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    n_fuzz = 0
    deleted_keys = set()

    def check_one(fk, value, complete, curated, kind):
        nonlocal checked
        real = real_rejects(fk, value)
        shad = shadow_rejects(value, complete, curated)
        if real != shad:
            print("DISAGREEMENT (%s)\n  field=%s value=%r"
                  "\n  complete_rows=%r\n  curated_rows=%r\n  rows=%s"
                  "\n  real validate rejects=%s\n  shadow rejects=%s"
                  % (kind, fk.name, value, sorted(complete), sorted(curated),
                     json.dumps(describe_rows()), real, shad))
            return False
        checked += 1
        return True

    def mutate_population(phase):
        """Evolve the stored rows so the snapshots cover empty, all-visible,
        hidden-witness, restriction-failing, gappy, and churned states."""
        if phase == 0:
            return  # empty table
        if phase == 1:
            for _ in range(4):
                Target._base_manager.create(archived=False, flag=True)
        elif phase == 2:
            # hidden rows: stored but absent from the curated collection
            for _ in range(4):
                Target._base_manager.create(archived=True, flag=True)
        elif phase == 3:
            # rows failing the per-field choice restriction
            Target._base_manager.create(archived=False, flag=False)
            Target._base_manager.create(archived=True, flag=False)
        elif phase == 4:
            # key gaps: delete a visible and a hidden row
            pks = list(Target._base_manager.order_by("pk")
                       .values_list("pk", flat=True))
            for pk in (pks[0], pks[-1]):
                deleted_keys.add(pk)
                Target._base_manager.filter(pk=pk).delete()
        else:
            # random churn: create / delete / toggle
            for _ in range(rng.randint(1, 4)):
                Target._base_manager.create(
                    archived=rng.random() < 0.5, flag=rng.random() < 0.5)
            pks = list(Target._base_manager.values_list("pk", flat=True))
            if pks and rng.random() < 0.7:
                victim = rng.choice(pks)
                deleted_keys.add(victim)
                Target._base_manager.filter(pk=victim).delete()
            pks = list(Target._base_manager.values_list("pk", flat=True))
            if pks:
                flipped = rng.choice(pks)
                row = Target._base_manager.get(pk=flipped)
                Target._base_manager.filter(pk=flipped).update(
                    archived=not row.archived if rng.random() < 0.5
                    else row.archived,
                    flag=not row.flag if rng.random() < 0.5 else row.flag)

    for phase in range(PHASES):
        mutate_population(phase)
        stored = list(Target._base_manager.values_list("pk", flat=True))
        lo = min(stored) if stored else 1
        hi = max(stored) if stored else 1

        for fk in fields:
            complete, curated = snapshot(fk)
            _REAL_CHOICE_PERMITTED = make_real_choice_permitted(fk)

            # boundary values: every stored key, every deleted key, and the
            # edges just outside the stored range
            boundary = sorted(set(stored) | deleted_keys
                              | {0, -1, lo - 1, hi + 1, hi + 1000})
            for value in boundary:
                if not check_one(fk, value, complete, curated, "boundary"):
                    return 1
                n_boundary += 1

            for _ in range(FUZZ_PER_PHASE_PER_FIELD):
                value = rng.randint(lo - 5, hi + 10)
                if not check_one(fk, value, complete, curated, "fuzz"):
                    return 1
                n_fuzz += 1

    assert checked >= MIN_CHECKS, (
        "input budget not met: %d < %d" % (checked, MIN_CHECKS))
    print("G-CONF OK: shadow impl == real patched validate on %d inputs "
          "(%d boundary + %d fuzz, %d population phases x 2 reference "
          "fields, seed %d)."
          % (checked, n_boundary, n_fuzz, PHASES, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "choice_permitted axiom -> real "
                                "complex_filter(get_limit_choices_to()))"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
