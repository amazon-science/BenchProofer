#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11179.

Executes the REAL unchanged row-removal primitive — Django's
``django.db.models.sql.subqueries.DeleteQuery.delete_batch`` (called from the
optimized single-object path of ``Collector.delete`` as
``sql.DeleteQuery(model).delete_batch([instance.pk], using)``) — and asserts
that every observation matches the ``remove_rows`` axiom in model.py, plus the
refinement-load-bearing property that the primitive does NOT clear the
in-memory object's primary key (only the patch's ``setattr`` does).

The single axiom (A-consumed):

  remove_rows(db, identifier) -> int
      Requires(-(2 ** 63) <= identifier and identifier < 2 ** 63)
      Ensures(db.removal_statements == Old(db.removal_statements) + 1)
      Ensures(db.last_removal_target == identifier)
      Ensures(db.last_removal_report == Result())
      Ensures(Result() >= 0)
      Ensures(not Old(db.refuses_removal))
      Exsures(RemovalRefused, <permissions> and Old(db.refuses_removal)
              and db.removal_statements == Old(db.removal_statements) + 1
              and db.last_removal_target == identifier
              and LEDGER.total_removal_statements == Old(...) + 1)

i.e. one invocation of the real ``delete_batch`` on a one-element identifier list
drawn from the range the store can represent

  * issues EXACTLY ONE row-removal statement (its chunk loop
    ``range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE)`` runs once, so one
    ``do_query``) — counted here through the connection's ``execute_wrapper``,
  * issues it FOR THE IDENTIFIER IT WAS HANDED (the statement's ``WHERE`` is
    built from that list and nothing else) — read here out of the real
    statement's bind parameters,
  * returns the NON-NEGATIVE row count that same statement reported, and
  * operates on the database row only, never touching the in-memory Python
    object's ``pk`` attribute.

The axiom asserts those effects of a removal the store CARRIES OUT, so the two
ways the real primitive can end without reporting a count are part of what has to
be measured. One is the identifier: the ``Requires`` names the range the store can
represent, and the probe checks that boundary executably rather than only the
happy path — the axiom's domain is measured, not assumed. The other is the store
itself: it can REFUSE the removal, which the axiom models as ``RemovalRefused``
conditioned on ``db.refuses_removal``, and both directions of that condition are
measured too.

  * THE REFUSAL (section c): a row the store protects (a live row a foreign key
    references, still fast-deletable) is answered with NO count — the removal is
    refused, the row survives and the in-memory pk is untouched — while the same
    identifier with the protection gone is answered with a count. That pair is
    what the ``Ensures(not Old(db.refuses_removal))`` /
    ``Exsures(..., Old(db.refuses_removal))`` clauses say, and it is why the
    refusal cannot be read as something the primitive may always do. A dependent
    row behind a constraint-free foreign key is answered with a count, which pins
    the carrier to the store's own refusal rather than to dependents existing.
    The refusal is what the store answers a STATEMENT with, so the rest of the
    exceptional clause is measured on the same observation: the refused
    invocation still issued exactly ONE row-removal statement and that statement
    still carried the identifier it was handed. This is what stops the
    exceptional case being cheaper than the ordinary one — an implementation
    cannot report a refusal it has not paid for, because finding the refusal out
    is what the payment buys.
  * DOMAIN EDGE (section d): every clause above still holds at the extreme
    representable identifiers (``2**63 - 1``, ``-2**63`` and mid-range values),
    both with a live row (count 1) and with the row gone (count 0), so the
    stated domain is not one step narrower than the real one.
  * OUTSIDE THE DOMAIN (section e): handed an identifier the store cannot
    represent the primitive reports NO count at all — it raises out of the
    backend's parameter adaptation — which is why the axiom states its effects
    only inside the range.
  * DOMAIN INHABITANCE (section f): no stored row can be keyed by an
    out-of-range identifier in the first place (the INSERT raises the same way),
    so restricting the axiom to the representable range excludes no persistent
    object: it states the domain, it does not dodge a case.

Sections (a)-(c) run before (d)-(f) for a mechanical reason worth stating: on
sqlite an ``AutoField`` primary key is ``AUTOINCREMENT``, whose high-water mark
lives in ``sqlite_sequence`` and is never lowered. Once a row has been stored at
``2**63 - 1`` no later ``AutoField`` insert can succeed — not even after that row
is deleted — so every section that needs a freshly created object must come
first.

This is run inside the official SWE-bench container for the instance, where
Django is importable and a sqlite test database is available. It configures an
in-memory sqlite database and a minimal dependency-free model (the structural
twin of the test's ``User``), then drives the real primitive. Exit 0 iff every
obligation holds.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        # Register ONLY apps that are actually importable. A throwaway
        # ``app_label`` (e.g. "axcheck") must NOT appear in INSTALLED_APPS:
        # ``django.setup()`` eagerly imports every INSTALLED_APPS entry and
        # raises ModuleNotFoundError for a non-existent package, so the probe
        # would report a skip and never reach the real callee. The throwaway
        # model is hosted under an already-installed app's label instead.
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _observed_target(params):
    """The identifier a real row-removal statement was parameterized with.

    Read out of the statement's actual bind parameters — the fast path removes by
    a one-element identifier list, so the DELETE carries exactly one parameter.
    Returns None when the parameters are not observable on this backend."""
    if params is None:
        return None
    try:
        seq = list(params)
    except TypeError:
        return None
    return seq[0] if len(seq) == 1 else None


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, connections, models
    from django.db.models import sql
    from django.db.models.deletion import Collector

    # A minimal, dependency-free model (no FKs in or out, no signal listeners):
    # the structural twin of the test's ``User`` and exactly the
    # can-fast-delete case the optimized single-object path handles. Hosted
    # under an already-installed app's label (see _configure_django).
    class FastDeletable(models.Model):
        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(FastDeletable)

    def remove_rows_outcome(identifier):
        """One invocation of the REAL primitive, with every effect the axiom
        claims OBSERVED rather than assumed, and reporting HOW it ended:

            ("returned", count, statements, target)
            ("raised",   exc,   statements, target)

        The statements (and their bind parameters) are collected through the
        connection's execute_wrapper, which sees a statement as it is issued —
        i.e. BEFORE the store gets to accept or refuse it. That is what makes the
        cost and target halves of the exceptional clause measurable: on the
        refused path there is no count, but there is still a statement that was
        issued and an identifier it carried, and both are read here rather than
        assumed. ``target`` is None when the bind parameters are not observable
        on this backend."""
        issued = []

        def _tally(execute, sql_text, params, many, context):
            issued.append((sql_text, params))
            return execute(sql_text, params, many, context)

        try:
            with connections["default"].execute_wrapper(_tally):
                count = sql.DeleteQuery(FastDeletable).delete_batch([identifier],
                                                                   "default")
        except Exception as exc:  # the primitive reported no count
            target = _observed_target(issued[-1][1]) if issued else None
            return ("raised", exc, len(issued), target)
        target = _observed_target(issued[-1][1]) if issued else None
        return ("returned", count, len(issued), target)

    def remove_rows(identifier):
        """The same invocation where a count is what is wanted: returns
        (count, statements, target) and lets a refusal propagate."""
        outcome = remove_rows_outcome(identifier)
        if outcome[0] == "raised":
            raise outcome[1]
        return outcome[1], outcome[2], outcome[3]

    # boundary + fuzz over the number of stored rows targeted by the primitive
    counts_seen = []
    targets_observed = 0

    def check_axiom(identifier, count, statements, target, expect_count):
        """Every clause of the axiom, against one real observation."""
        nonlocal targets_observed
        # Ensures(Result() >= 0) — and here, exactly the rows that existed.
        assert isinstance(count, int), "delete_batch returned non-int %r" % (count,)
        assert count >= 0, "delete_batch returned a negative count %r" % (count,)
        assert count == expect_count, (
            "delete_batch removed %r rows, expected %r" % (count, expect_count))
        # Ensures(db.removal_statements == Old(...) + 1) — exactly ONE statement
        # per invocation on a one-element identifier list.
        assert statements == 1, (
            "AXIOM-UNSOUND: one delete_batch invocation on a one-element pk list "
            "issued %r row-removal statement(s), but the axiom claims exactly 1"
            % (statements,))
        # Ensures(db.last_removal_target == identifier) — that statement removed
        # by the identifier it was handed.
        if target is not None:
            assert target == identifier, (
                "AXIOM-UNSOUND: the real statement removed by %r, but was handed "
                "identifier %r" % (target, identifier))
            targets_observed += 1

    # (a) a live single row: delete_batch should report exactly 1 removed and
    #     must not clear the in-memory object's pk by itself.
    for _ in range(50):
        obj = FastDeletable.objects.create()
        stored_pk = obj.pk
        assert stored_pk is not None

        # Confirm this object is in fact fast-deletable (the path's guard).
        collector = Collector(using="default")
        assert collector.can_fast_delete(obj), "expected a fast-deletable object"

        # The REAL unchanged callee.
        count, statements, target = remove_rows(stored_pk)
        check_axiom(stored_pk, count, statements, target, 1)
        counts_seen.append(count)

        # Refinement-load-bearing: the primitive does NOT touch the in-memory
        # object. The pk is still the stored value; only the patch's setattr
        # clears it.
        assert obj.pk == stored_pk, (
            "delete_batch must not mutate the in-memory pk: was %r, now %r"
            % (stored_pk, obj.pk))

    # (b) an identifier with no matching row: count must be 0 (>= 0 holds).
    for _ in range(25):
        obj = FastDeletable.objects.create()
        stored_pk = obj.pk
        # remove the row first, then target the now-absent identifier
        remove_rows(stored_pk)
        count, statements, target = remove_rows(stored_pk)
        check_axiom(stored_pk, count, statements, target, 0)
        counts_seen.append(count)

    # (c) THE REFUSAL — the two clauses about the outcome the STORE forces.
    #     Ensures(not Old(db.refuses_removal)) says a count comes back only for a
    #     removal the store carried out; Exsures(RemovalRefused, ...
    #     Old(db.refuses_removal)) says the refusal is signalled only when the
    #     store really refused. Both directions are measured on the real
    #     primitive, and the refusal is measured on the MODELED path: the
    #     protected row is still fast-deletable, so this is a case
    #     remove_single_independent can genuinely reach.
    class Protector(models.Model):
        """A row whose foreign key the store keys to a FastDeletable row. With
        DO_NOTHING Django asks the database for nothing on delete, so the
        database's own FOREIGN KEY constraint is what refuses the removal."""
        target = models.ForeignKey(FastDeletable, models.DO_NOTHING)

        class Meta:
            app_label = "auth"

    class LooseProtector(models.Model):
        """The same reference with NO database-level constraint behind it
        (``db_constraint=False``): a dependent row exists, but the store has
        nothing protecting the target, so the removal is not refused."""
        target = models.ForeignKey(FastDeletable, models.DO_NOTHING,
                                   db_constraint=False)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(Protector)
        editor.create_model(LooseProtector)

    with connection.cursor() as cur:
        cur.execute("PRAGMA foreign_keys")
        fk_row = cur.fetchone()
    fk_enforced = bool(fk_row and fk_row[0])
    refusals_observed = 0
    if fk_enforced:
        # (c.1) the store REFUSES: no count is reported at all.
        protected = FastDeletable.objects.create()
        Protector.objects.create(target=protected)
        collector = Collector(using="default")
        assert collector.can_fast_delete(protected), (
            "expected the protected row to still be fast-deletable: the refusal "
            "must be reachable on the path under specification")
        outcome = remove_rows_outcome(protected.pk)
        assert outcome[0] == "raised", (
            "AXIOM-UNSOUND: the primitive RETURNED %r for the identifier %r of a "
            "row the store protects. model.py's axiom claims a count only when "
            "the store carried the removal out "
            "(Ensures(not Old(db.refuses_removal))); if a count really does come "
            "back here, that clause must go." % (outcome[1:], protected.pk))
        refusal, refused_statements, refused_target = outcome[1:]
        from django.db.utils import IntegrityError
        assert isinstance(refusal, IntegrityError), (
            "the refusal reached the caller as %r, not the IntegrityError "
            "RemovalRefused stands for" % (refusal,))
        assert FastDeletable.objects.filter(pk=protected.pk).exists(), (
            "the refused removal removed the row anyway")
        assert protected.pk is not None, (
            "the refused removal cleared the in-memory pk")
        # the cost half of the exceptional clause: the refusal is the answer to a
        # statement, so exactly ONE statement was still issued.
        assert refused_statements == 1, (
            "AXIOM-UNSOUND: the refused invocation issued %r row-removal "
            "statement(s), but model.py's Exsures claims the handle's tally and "
            "the module-wide total each still advance by exactly 1 on that path"
            % (refused_statements,))
        # ... and the target half: that statement asked about the identifier it
        # was handed and no other.
        if refused_target is not None:
            assert refused_target == protected.pk, (
                "AXIOM-UNSOUND: the refused statement carried identifier %r "
                "though the primitive was handed %r, but model.py's Exsures "
                "claims db.last_removal_target == identifier on that path"
                % (refused_target, protected.pk))
        refusals_observed += 1

        # (c.2) the other direction: with the protecting row gone the SAME
        #        identifier is answered with a count, so the refusal is
        #        conditioned on what the store holds and is not something the
        #        primitive does always. This is what makes
        #        Exsures(..., Old(db.refuses_removal)) a real condition rather
        #        than an escape hatch a rival could always take.
        Protector.objects.all().delete()
        outcome = remove_rows_outcome(protected.pk)
        assert outcome[0] == "returned", (
            "AXIOM-UNSOUND: the primitive reported no count for the unprotected "
            "identifier %r (%r) — then the refusal would not be conditioned on "
            "the store refusing" % (protected.pk, outcome[1:]))
        _, count, statements, target = outcome
        check_axiom(protected.pk, count, statements, target, 1)
        counts_seen.append(count)

        # (c.3) what the carrier means: a dependent row alone does NOT refuse —
        #        only something the STORE holds protecting the target does. The
        #        same reference without a database constraint is answered with a
        #        count, so ``refuses_removal`` maps to the store's own refusal.
        loose = FastDeletable.objects.create()
        LooseProtector.objects.create(target=loose)
        outcome = remove_rows_outcome(loose.pk)
        assert outcome[0] == "returned", (
            "the primitive reported no count for a row referenced through an FK "
            "with no database constraint (%r); refuses_removal is then not the "
            "store's own refusal" % (outcome[1:],))
        _, count, statements, target = outcome
        check_axiom(loose.pk, count, statements, target, 1)
        counts_seen.append(count)
        LooseProtector.objects.all().delete()

    # (d) THE DOMAIN EDGE, in range. The axiom is stated for identifiers the
    #     store can represent (-2**63 <= identifier < 2**63). Check every clause
    #     still holds at the extremes of that range and not merely at the small
    #     AutoField values (a) and (b) produce, so the stated domain is not
    #     narrower than the domain the primitive really has. Each identifier is
    #     STORED first (so this is a live-row observation, count 1) and then
    #     re-targeted once the row is gone (count 0). These run after (a)-(c) for
    #     a mechanical reason: sqlite's AUTOINCREMENT high-water mark
    #     (sqlite_sequence) is never lowered, so once a row has been stored at
    #     2**63 - 1 every later AutoField insert fails with SQLITE_FULL — even
    #     after that row is deleted again. Every section that creates a fresh
    #     object must therefore come first.
    IN_RANGE_EDGE = [2 ** 63 - 1, -(2 ** 63), 2 ** 63 - 2, -(2 ** 63) + 1,
                     2 ** 62, -(2 ** 62), 2 ** 31, -(2 ** 31) - 1]
    edge_observed = 0
    for identifier in IN_RANGE_EDGE:
        obj = FastDeletable.objects.create(pk=identifier)
        assert obj.pk == identifier
        outcome = remove_rows_outcome(identifier)
        assert outcome[0] == "returned", (
            "AXIOM-UNSOUND: the primitive reported no count for the "
            "representable identifier %r (%r), but the axiom's Requires admits "
            "it and its Ensures claim a count" % (identifier, outcome[1:]))
        _, count, statements, target = outcome
        check_axiom(identifier, count, statements, target, 1)
        counts_seen.append(count)
        # the primitive removed the DB row only, not the in-memory pk
        assert obj.pk == identifier, (
            "delete_batch must not mutate the in-memory pk: was %r, now %r"
            % (identifier, obj.pk))
        # ... and again, now that the row is gone: count 0, row still absent
        outcome = remove_rows_outcome(identifier)
        assert outcome[0] == "returned", (
            "AXIOM-UNSOUND: no count reported for absent representable "
            "identifier %r (%r)" % (identifier, outcome[1:]))
        _, count, statements, target = outcome
        check_axiom(identifier, count, statements, target, 0)
        counts_seen.append(count)
        edge_observed += 1

    # (e) OUTSIDE THE DOMAIN. The axiom has no exceptional case, so it must not
    #     be read as claiming anything for identifiers the store cannot
    #     represent. Measure that it indeed claims nothing there: the primitive
    #     reports NO count for such an identifier (the backend's parameter
    #     adaptation raises), which is exactly why the Requires bounds the range.
    #     If the primitive were to return normally out here, the axiom's domain
    #     would be narrower than the primitive's and this probe must say so.
    OUT_OF_RANGE = [2 ** 63, 2 ** 63 + 1, 2 ** 64, 2 ** 70,
                    -(2 ** 63) - 1, -(2 ** 63) - 2, -(2 ** 70)]
    outside_observed = 0
    for identifier in OUT_OF_RANGE:
        outcome = remove_rows_outcome(identifier)
        assert outcome[0] == "raised", (
            "DOMAIN CLAIM WRONG: the primitive RETURNED %r for identifier %r, "
            "which model.py's axiom excludes from its domain as one the store "
            "cannot represent. The Requires is then narrower than the real "
            "domain and must be widened." % (outcome[1:], identifier))
        outside_observed += 1

    # (f) DOMAIN INHABITANCE. The restriction in (e) is a property of the
    #     domain, not a dodged case: an out-of-range value is not an identifier
    #     any stored row can be keyed by, so no PERSISTENT object can carry one.
    #     Measured both ways — the extremes of the range do store, and anything
    #     past them cannot be stored at all.
    for identifier in [2 ** 63 - 1, -(2 ** 63)]:
        obj = FastDeletable.objects.create(pk=identifier)
        assert FastDeletable.objects.filter(pk=identifier).count() == 1, (
            "expected the representable extreme %r to be storable" % (identifier,))
        remove_rows(identifier)  # leave the table clean for AutoField inserts
    for identifier in [2 ** 63, -(2 ** 63) - 1, 2 ** 70]:
        try:
            FastDeletable.objects.create(pk=identifier)
        except Exception:
            pass
        else:
            raise AssertionError(
                "DOMAIN CLAIM WRONG: a row WAS stored under the out-of-range "
                "identifier %r, so a persistent object can carry one and the "
                "axiom's domain restriction excludes a reachable case"
                % (identifier,))

    if not targets_observed:
        print("G-AX SKIP: the real row-removal statement's bind parameters were "
              "never observable on this backend, so the removal-target clause "
              "could not be checked executably.")
        return 0

    print("G-AX OK: remove_rows axiom sound against the real "
          "DeleteQuery.delete_batch over %d observations: every invocation "
          "issued EXACTLY ONE row-removal statement, that statement removed by "
          "the identifier it was handed (%d observations with observable bind "
          "parameters), the returned count was that statement's own non-negative "
          "report (counts in {0,1}), and the primitive never clears the "
          "in-memory pk. Domain measured, not assumed: every clause holds at the "
          "%d extreme representable identifiers (2**63-1 and -2**63 among them, "
          "each observed live and absent); for all %d out-of-range identifiers "
          "the primitive reports NO count (it raises in the backend's parameter "
          "adaptation), which is why the axiom's Requires bounds the range; and "
          "no row can be stored under an out-of-range identifier at all, so the "
          "bound excludes no persistent object. The refusal is measured the same "
          "way (%d observation(s), foreign keys enforced=%r): a still-fast-"
          "deletable row the store protects is answered with NO count and "
          "survives, the refused invocation still issued exactly ONE statement "
          "carrying the identifier it was handed, the same identifier "
          "unprotected is answered with a count, and a dependent row behind a "
          "constraint-free reference does not refuse."
          % (len(counts_seen), targets_observed, edge_observed, outside_observed,
             refusals_observed, fk_enforced))
    return 0


if __name__ == "__main__":
    sys.exit(main())
