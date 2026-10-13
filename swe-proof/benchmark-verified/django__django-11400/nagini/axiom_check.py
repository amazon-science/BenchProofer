#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11400.

The bundle's single consumed callee is the unchanged queryset reorder operation
`QuerySet.order_by(*ordering)` applied to a related model's base manager
queryset. It is captured by the `reordered` (`@Pure`) / `apply_order_by`
(effecting) axioms in model.py. This check executes the REAL callee --
`Model._default_manager.all().order_by(*ordering)` over an in-memory SQLite
database -- and asserts that every observation satisfies what those axioms
promise, and that the axioms promise nothing the callee lacks:

  (1) `reordered` IS UNINTERPRETED, and it must be. The axiom states NO
      property of the reorder operation's value. That is not laziness: this
      check exhibits the real callee BREAKING each of the tempting positive
      clauses, so an axiom asserting any of them would be UNSOUND.

      (1a) LENGTH IS NOT PRESERVED, upward. An ordering specification names
           traversal paths. When a path crosses a to-many association the
           operation repeats a base entry once per associated element, so the
           result can be LONGER than the base collection. An axiom promising
           `len(reordered(base, ordering)) == len(base)` would be false here.

      (1b) LENGTH IS NOT PRESERVED, downward, and MEMBERSHIP is not either.
           When a path crosses a MANDATORY single-valued association, an entry
           whose associate is missing drops out of the result entirely, so the
           result can be SHORTER than the base collection and can omit one of
           its entries. So no count, set or multiset relation to `base` holds.

  (2) NON-EMPTY ORDERING is honoured: for a specification naming a plain local
      field, `order_by(*ordering)` yields the entries in exactly that order.
      (The axiom ties `reordered(base, ordering)` to whatever the operation
      returns; this confirms the operation is the real sort it is taken to be,
      so pinning the result to it is meaningful rather than degenerate.)

  (3) THE SOUNDNESS OF THE SILENCE ON THE EMPTY CASE. The axiom does not
      promise `reordered(base, []) == base`: an empty ordering specification
      CLEARS any pre-existing order. This check exhibits a base manager whose
      default order comes from `Meta.ordering` and shows that `order_by()`
      (empty) produces a DIFFERENT arrangement than the base manager's own
      order -- so an implementation that routed the empty case through
      `order_by()` would NOT preserve the base order. This is why the axiom
      must stay silent on the empty case, and why the specified behaviour skips
      the reorder when the specification is empty. (The F2P tests set
      `Meta.ordering` and read the resulting order back.)

  (4) CONTAINMENT: every callee-input the model can reach -- an empty and a
      non-empty specification, over a populated and an empty base -- is
      accepted by the real callee without error.

Imports only Django (the framework whose ORM IS the real callee) and the
standard library; no repo test fixtures, no network, in-memory SQLite. Exit 0
iff every obligation holds.
"""
import sys


def _configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


def main():
    _configure()
    from django.db import models, connection

    # A model with NO default ordering, a sortable local field `a`, and a
    # TO-MANY association (`tags`) so that an ordering path can fan entries out.
    class Tag(models.Model):
        label = models.CharField(max_length=10)

        class Meta:
            app_label = "axcheck"
            ordering = ()

    class Thing(models.Model):
        a = models.CharField(max_length=10)
        tags = models.ManyToManyField(Tag, related_name="things")

        class Meta:
            app_label = "axcheck"
            ordering = ()  # base order is insertion/pk order

    # A second pair for the DROP direction: `room` is MANDATORY, so ordering
    # across it is an inner join and an entry with a missing associate vanishes.
    class Room(models.Model):
        code = models.CharField(max_length=10)

        class Meta:
            app_label = "axcheck"
            ordering = ()

    class Desk(models.Model):
        label = models.CharField(max_length=10)
        room = models.ForeignKey(Room, models.CASCADE, related_name="desks")

        class Meta:
            app_label = "axcheck"
            ordering = ()

    with connection.schema_editor() as se:
        for m in (Tag, Thing, Room, Desk):
            se.create_model(m)

    # Insert rows whose alphabetical order on `a` is the REVERSE of pk order, so
    # an applied ascending ordering visibly differs from the base order.
    rows = [
        Thing.objects.create(a="d"),
        Thing.objects.create(a="c"),
        Thing.objects.create(a="b"),
        Thing.objects.create(a="a"),
    ]
    base_pks = [t.pk for t in Thing.objects.all()]          # base manager order
    assert base_pks == [r.pk for r in rows], base_pks       # insertion/pk order

    def reordered(ordering):
        # The REAL callee: order_by(*ordering) on the base manager queryset.
        return [t.pk for t in Thing.objects.all().order_by(*ordering)]

    # ---- (1a) the real callee GROWS the collection on a to-many path --------
    t1, t2 = Tag.objects.create(label="x"), Tag.objects.create(label="y")
    rows[0].tags.add(t1, t2)          # one entry gains two associated elements
    rows[1].tags.add(t1)
    fanned = reordered(("tags__label",))
    assert len(fanned) > len(base_pks), (
        "expected a to-many ordering path to repeat base entries, but got "
        "len %d vs base len %d (%r) -- if the callee really did preserve "
        "length here, the axiom could soundly say so"
        % (len(fanned), len(base_pks), fanned))

    # ---- (1b) the real callee SHRINKS it on a mandatory single-valued path --
    room = Room.objects.create(code="r1")
    d1 = Desk.objects.create(label="d1", room=room)
    d2 = Desk.objects.create(label="d2", room=room)
    desk_base = [d.pk for d in Desk.objects.all()]
    # Orphan d2's MANDATORY associate with referential enforcement off, so the
    # inner join the ordering path emits has nothing to match it against.
    with connection.cursor() as c:
        c.execute("PRAGMA foreign_keys=OFF")
        c.execute("UPDATE axcheck_desk SET room_id=%s WHERE id=%s",
                  [max(desk_base) + 9999, d2.pk])
    dropped = [d.pk for d in Desk.objects.all().order_by("room__code")]
    # Restore the associate immediately: the connection's teardown runs a
    # referential-integrity check that a lingering orphan would trip.
    with connection.cursor() as c:
        c.execute("UPDATE axcheck_desk SET room_id=%s WHERE id=%s",
                  [room.pk, d2.pk])
        c.execute("PRAGMA foreign_keys=ON")
    assert len(dropped) < len(desk_base), (
        "expected a mandatory single-valued ordering path to drop an entry "
        "with a missing associate, got len %d vs base len %d (%r)"
        % (len(dropped), len(desk_base), dropped))
    assert set(dropped) != set(desk_base), (
        "expected the dropped entry to leave the result set, got %r vs %r"
        % (dropped, desk_base))

    # ---- (2) a plain local-field ordering IS honoured (asc and desc) --------
    asc = reordered(("a",))
    assert asc == [rows[3].pk, rows[2].pk, rows[1].pk, rows[0].pk], asc
    desc = reordered(("-a",))
    assert desc == [rows[0].pk, rows[1].pk, rows[2].pk, rows[3].pk], desc

    # ---- (3) the silence on the EMPTY case is sound -------------------------
    # Give the base manager a NON-trivial default order via Meta.ordering, then
    # show that order_by() (empty) does NOT reproduce it. This mirrors the F2P
    # scenario (the tests set Foo/Bar/Employee/Book._meta.ordering then read
    # get_choices back).
    Thing._meta.ordering = ("a",)
    base_ordered_pks = [t.pk for t in Thing.objects.all()]   # NOW = ascending a
    assert base_ordered_pks == [rows[3].pk, rows[2].pk, rows[1].pk, rows[0].pk], \
        base_ordered_pks

    empty_applied = reordered(())   # order_by() clears ordering
    # The empty-ordering reorder must NOT be assumed equal to the base order:
    # here it diverges (SQLite returns rowid/pk order, not the Meta order).
    assert empty_applied != base_ordered_pks, (
        "order_by() unexpectedly reproduced the base Meta.ordering; the axiom's "
        "silence on the empty case would then be over-weak, but the skip on the "
        "empty branch is what makes the base order observable -- got %r"
        % (empty_applied,))

    Thing._meta.ordering = ()

    # ---- (4) containment over every model-reachable regime ------------------
    class EmptyThing(models.Model):
        a = models.CharField(max_length=10)

        class Meta:
            app_label = "axcheck"
            ordering = ()

    with connection.schema_editor() as se:
        se.create_model(EmptyThing)
    for ordering in [(), ("a",), ("-a",), ("a", "id"), ("tags__label",)]:
        reordered(ordering)                                  # populated base
    assert [t.pk for t in EmptyThing.objects.all().order_by()] == []
    assert [t.pk for t in EmptyThing.objects.all().order_by("a")] == []

    print(
        "G-AX OK: QuerySet.order_by axioms sound -- `reordered` is "
        "UNINTERPRETED and must be: the real callee GROWS the collection on a "
        "to-many ordering path (len %d > base %d) and SHRINKS it on a mandatory "
        "single-valued one (len %d < base %d, row set changed), so no length, "
        "set or multiset clause would be sound. A local-field ordering is "
        "honoured (asc/desc); empty order_by() clears the base Meta.ordering "
        "(%r != %r), confirming the axiom must not promise reordered(b, [])==b "
        "and the skip on the empty branch is required; every model-reachable "
        "input is accepted."
        % (len(fanned), len(base_pks), len(dropped), len(desk_base),
           empty_applied, base_ordered_pks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
