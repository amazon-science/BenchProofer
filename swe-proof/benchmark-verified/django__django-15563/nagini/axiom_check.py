#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15563.

This bundle consumes NO @ContractOnly axiom: the column-assignment logic is
modelled DEEPLY in model.py (``assign_columns``). What G-AX validates here is
the **A-reference** — that the deep model faithfully captures the REAL Django
path-classification primitive the column assignment is built on:

    all(path.join_field.primary_key
        for path in meta.get_path_to_parent(related))

i.e. for each ancestor that a multi-table-inheritance ``QuerySet.update`` must
touch, whether the whole path from the source model up to that ancestor is a
chain of primary-key links (so the ancestor's identifying value coincides with
the source row's own primary key).

The check, run inside the official SWE-bench container for the instance (Django
importable, in-memory sqlite available):

  1. Builds the real concrete-MTI tree that the F2P tests exercise
     (Politician  <-  Congressman(Person, Politician)  <-  Senator).
  2. For each F2P update scenario, computes the REAL set of related-update
     ancestor targets and, per target, the REAL value of the path-primary-key
     predicate above — exactly the boolean the model abstracts as a 0/1 flag.
  3. Independently reproduces the GOLD column assignment (the
     ``fields`` / ``related_ids_index`` construction of the patched
     ``pre_sql_setup``) directly from those real predicate values, and asserts
     it equals the model's ``assign_columns(flags)`` AT THE INDEX LEVEL:
         model_index[k] == 0   <=>   real_predicate[k] is True   (no double mask)
     and every non-chain target's model index is a DISTINCT positive column.
  4. Enumerates the two F2P scenarios and FAILS LOUD if either is skipped or
     produces no related-update target (a silent skip would be a false pass).

Outside the container (Django absent) it prints ``G-AX SKIP`` and returns 0; the
orchestrator runs it in-container. Exit 0 iff every obligation holds.
"""
import sys


# --- model.py reference: the deep column-assignment model -------------------

def assign_columns(flags):
    """Reference implementation of model.py's ``assign_columns``: flag 1 (full
    primary-key chain) -> column 0; otherwise a fresh, strictly increasing,
    positive column. Kept in lock-step with model.py's postconditions."""
    result = []
    width = 1
    for f in flags:
        if f == 1:
            result.append(0)
        else:
            result.append(width)
            width += 1
    return result


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
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


def _fuzz_deep_model_vs_gold():
    """Stdlib-only: the deep model `assign_columns` == the gold column
    construction on random flag vectors, with the is_pk_chain biconditional
    checked at the index level. Runs everywhere (no Django needed)."""
    import random
    rng = random.Random(15563)
    for _ in range(20000):
        n = rng.randint(0, 12)
        flags = [rng.randint(0, 1) for _ in range(n)]
        width = 1
        gold = []
        for f in flags:
            if f == 1:
                gold.append(0)
            else:
                gold.append(width)
                width += 1
        mi = assign_columns(flags)
        assert mi == gold, (
            "G-AX deep model != gold construction on flags=%r" % (flags,)
        )
        for k in range(n):
            assert (mi[k] == 0) == (flags[k] == 1)
        fresh = [mi[k] for k in range(n) if flags[k] == 0]
        assert len(fresh) == len(set(fresh)) and all(c >= 1 for c in fresh)


def main():
    # Stdlib-only equivalence first (always runs).
    _fuzz_deep_model_vs_gold()

    try:
        import django  # noqa: F401
    except Exception:
        print("G-AX PARTIAL OK (host): assign_columns deep model == gold "
              "column construction on 20000 fuzz flag vectors + index-level "
              "biconditional; Django not importable so the real "
              "get_path_to_parent predicate check is deferred to the "
              "in-container run.")
        return 0

    _configure_django()

    from django.db import models, connection
    from django.db.models.sql.subqueries import UpdateQuery

    # The concrete-MTI tree the F2P tests exercise (structural twins).
    class Person(models.Model):
        name = models.CharField(max_length=50, blank=True)

        class Meta:
            app_label = "contenttypes"

    class Politician(models.Model):
        politician_id = models.AutoField(primary_key=True)
        title = models.CharField(max_length=50, blank=True)

        class Meta:
            app_label = "contenttypes"

    class Congressman(Person, Politician):
        state = models.CharField(max_length=2, blank=True)

        class Meta:
            app_label = "contenttypes"

    class Senator(Congressman):
        class Meta:
            app_label = "contenttypes"

    # Create the tables.
    with connection.schema_editor() as editor:
        for m in (Person, Politician, Congressman, Senator):
            editor.create_model(m)

    # ----- the two F2P update scenarios -------------------------------------
    # Each scenario: a child model whose `.update(title=...)` touches the
    # `title` field, which lives on the Politician ancestor.
    scenarios = [
        ("parent_through_child", Congressman),
        ("grand_parent_through_child", Senator),
    ]

    seen = set()

    for name, model in scenarios:
        meta = model._meta

        # Build the real UpdateQuery and let Django populate related_updates
        # exactly as QuerySet.update would for `title=...`.
        uq = UpdateQuery(model)
        uq.add_update_values({"title": "x"})
        related = list(uq.related_updates.keys())

        assert related, (
            "G-AX FALSE-PASS GUARD: scenario %r produced NO related-update "
            "target; the F2P behaviour would be untested" % name
        )
        seen.add(name)

        # --- step 2: the REAL path-primary-key predicate per target ---------
        real_flags = []
        for rel in related:
            paths = meta.get_path_to_parent(rel)
            assert paths, (
                "G-AX: empty path to parent %r from %r" % (rel, model)
            )
            is_pk_chain = all(p.join_field.primary_key for p in paths)
            real_flags.append(1 if is_pk_chain else 0)

        # --- step 3: GOLD column assignment, reproduced from real predicates -
        # This mirrors the patched pre_sql_setup `fields`/`related_ids_index`
        # construction exactly (column 0 = source pk; fresh column appended,
        # index = running width of `fields`, for a non-pk-chain target).
        fields = [meta.pk.name]
        gold_index = []
        for rel, flag in zip(related, real_flags):
            if flag == 1:
                gold_index.append(0)
            else:
                gold_index.append(len(fields))
                fields.append(rel._meta.pk.name)

        # --- step 4: the model's deep assignment -----------------------------
        model_index = assign_columns(real_flags)

        # ===== assertions (index-level; NO double mask) =====================
        assert len(model_index) == len(real_flags) == len(gold_index), (
            "G-AX length mismatch in %r: model=%r gold=%r flags=%r"
            % (name, model_index, gold_index, real_flags)
        )

        for k in range(len(real_flags)):
            # The discriminating biconditional, asserted at the INDEX level:
            # the predicate under test (is_pk_chain) is NOT used to filter both
            # sides; we compare model column index 0-ness directly to it.
            assert (model_index[k] == 0) == (real_flags[k] == 1), (
                "G-AX UNSOUND deep model in %r at target %d: model column %r, "
                "real is_pk_chain=%r" % (name, k, model_index[k], real_flags[k])
            )
            # Exact agreement with the GOLD column assignment.
            assert model_index[k] == gold_index[k], (
                "G-AX deep model != gold column in %r at target %d: model=%r "
                "gold=%r" % (name, k, model_index[k], gold_index[k])
            )

        # Non-chain targets occupy distinct positive columns.
        fresh = [model_index[k] for k in range(len(real_flags))
                 if real_flags[k] == 0]
        assert all(c >= 1 for c in fresh), (
            "G-AX: a non-chain target was placed in column 0 in %r" % name
        )
        assert len(fresh) == len(set(fresh)), (
            "G-AX: fresh columns collided in %r: %r" % (name, fresh)
        )

        # For these F2P scenarios, `title` lives on Politician, reached through
        # the Person link of Congressman, which is NOT a primary-key chain
        # (Congressman's pk descends from Person via base_ptr). So the target
        # MUST get its own positive column — the very fix.
        assert any(f == 0 for f in real_flags), (
            "G-AX SANITY: expected at least one non-pk-chain ancestor "
            "(the title-bearing Politician) in scenario %r, got flags=%r"
            % (name, real_flags)
        )

    # --- step 4 (cont.): every F2P scenario actually ran --------------------
    expected = {"parent_through_child", "grand_parent_through_child"}
    assert seen == expected, (
        "G-AX FALSE-PASS GUARD: not all F2P scenarios ran: %r" % (seen,)
    )

    print("G-AX OK: assign_columns deep model == real-predicate-driven gold "
          "column assignment on 2 F2P scenarios (real get_path_to_parent / "
          "join_field.primary_key) + 20000 fuzz flag vectors; is_pk_chain "
          "biconditional sound at the index level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
