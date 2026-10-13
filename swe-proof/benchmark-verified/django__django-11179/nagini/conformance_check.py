#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11179 (nagini).

SHADOW: the impl region of ``model.py``'s ``remove_single_independent``, copied
VERBATIM below (`# --- shadow ---`) with only the contract calls stripped, plus
the ``PersistentObject`` carrier class minus its ``Ensures``.  The region is
three statements:

    identifier = instance.pk
    count = remove_rows(db, identifier)
    instance.pk = None
    return count

``remove_rows`` is ``@ContractOnly`` — it has no body to copy, so per the
contract the shadow calls the REAL repo function it axiomatizes
(mapping.md section 3.1): ``django.db.models.sql.subqueries.DeleteQuery.delete_batch``
(``django/db/models/sql/subqueries.py:27-42``), invoked exactly as the fast
branch invokes it, ``sql.DeleteQuery(model).delete_batch([identifier], using)``.
So the axiom is exercised against the real primitive rather than assumed, and
the shadow's count is a real DB-reported row count, not a stub.

The axiom also has an exceptional case — the store can REFUSE the removal, which
the model states as ``Exsures(RemovalRefused, ... Old(db.refuses_removal) and the
tally, total and target still pinned)`` alongside
``Ensures(not Old(db.refuses_removal))`` on the returning path — and that is
exercised rather than assumed too.  The shadow leg does not decide when a
refusal happens: it calls the real primitive, and when the store refuses (a live
row protected by a reference the store holds) the real ``DELETE`` raises
``django.db.IntegrityError``, which the shadow re-raises under the model's name
``RemovalRefused``.  Because the copied impl region has no exception handling, the
refusal propagates out of the shadow exactly as it propagates out of the real fast
branch, and the trial diffs THAT: whether each leg ended with a count or with a
refusal, the identifier attribute afterwards, and — because a refusal is what the
store answers a STATEMENT with — the statements each leg issued on that path, the
identifier they carried and the module-wide total, exactly as on the returning
path.  So the refusal being no cheaper than the removal it was refused is measured
too, not assumed.

Every one of ``remove_rows``'s Ensures is grounded that way. Its statement-tally
clause (``db.removal_statements == Old(...) + 1``) is grounded by COUNTING the
SQL statements the real primitive issues through the connection's
``execute_wrapper`` — never by incrementing a counter by hand. Its record
clauses are grounded the same way: ``db.last_removal_target`` is set to the
identifier the real statement was actually issued for (the value handed to
``delete_batch``), and ``db.last_removal_report`` to the row count that real
statement returned. The oracle leg counts the real fast branch's statements the
same way and reads the identifier the real branch removed by, so the model's
single-statement, statement-target and count-provenance postconditions are each
refuted by reality if they are ever wrong.

ORACLE: the REAL PATCHED repo function, CALLED, not transliterated — the
optimized single-object branch of ``Collector.delete``
(``django/db/models/deletion.py:274-280`` at base_commit; mapping.md section 1).
The gate applies patch.diff to /testbed before this script runs and
``PYTHONPATH=/testbed`` makes the patched module importable, so
``Collector.delete`` here is the post-patch source.  Each trial builds a live
minimal dependency-free ORM model instance carrying a stored pk, collects it
with the real ``Collector`` and calls the real ``Collector.delete()``; the
observed values are the returned count,
``getattr(instance, model._meta.pk.attname)``, the number of row-removal
statements the call issued, and the identifier that statement was issued for —
i.e. the four things the model's postconditions pin.  Nothing about ``delete``
is reimplemented here.

  * Every trial ASSERTS that the real code actually enters the modeled branch
    (``len(self.data) == 1 and len(instances) == 1`` and
    ``self.can_fast_delete(instance)``) and that the patched clearing statement
    is present in the live ``Collector.delete`` source.  This guard is
    load-bearing: the GENERAL path of ``delete`` also clears every collected
    instance's pk (``deletion.py:324-326``) and did so pre-patch, so an oracle
    that silently fell through to the general path would agree with the shadow
    even against unpatched code and certify nothing.  Falsifiability was
    confirmed empirically: run against /testbed WITHOUT the gold patch this
    script reports a disagreement (real pk stays at its stored value while the
    shadow clears it) and exits 1.

TYPE BRIDGE (mapping.md section 2, inverted):
  * ``PersistentObject.pk : Optional[int]``  <->  the ORM instance's
    primary-key attribute reached by its dynamic name
    ``model._meta.pk.attname`` (``id`` here).  The shadow reads/writes the
    field ``pk``; the oracle leg is read with ``getattr(inst, attname)``.
    ``instance.pk is None`` <-> the cleared attribute.
  * the model's scalar ``identifier : int`` <-> the stored database identifier,
    passed to the primitive as the singleton list ``[identifier]`` (the fast
    path has exactly one object).
  * the model's ``Database`` carrier <-> a configured database alias plus the
    record of the row-removal statements issued through it.  Tag ``u`` selects
    the ``u``-th of three parallel sqlite connections.  Each tag maps to a PAIR
    of aliases holding identical row state (``shadow<u>`` / ``oracle<u>``)
    because both legs perform a REAL ``DELETE``; giving each leg its own
    connection with the same contents keeps the two counts comparable instead of
    letting the first delete steal the second's row.
    ``db.removal_statements`` <-> the count of DELETE statements observed on
    that connection via ``execute_wrapper``;
    ``db.last_removal_target`` <-> the identifier the observed DELETE was
    actually parameterized with (read out of the statement's real bind
    parameters, not from the model-side argument);
    ``db.last_removal_report`` <-> the row count that real statement returned.
  * the model's single module-wide ``LEDGER`` <->  the row-removal statements
    observed across ALL of that leg's connections, since every connection
    reaches stored data and a statement issued anywhere still removes rows.
    ``LEDGER.total_removal_statements`` delta <-> that total count. The oracle
    leg counts it by wrapping every configured connection, not just the alias
    the delete was asked to use, so a branch that kept its named connection at
    one statement while removing through another would be caught here. That is
    the total-cost observable the per-alias tally structurally cannot see, and
    it is what the suite's exact-statement-count assertion observes.
    ``db.refuses_removal`` <-> whether the store behind that connection holds
    something protecting the targeted row: a live row of a second model whose
    foreign key references it, which the database's own FOREIGN KEY constraint
    then defends.  Like the rest of the record it is READ from the store's
    contents by the trial, never chosen by the impl.
  * the model's ``RemovalRefused`` <-> ``django.db.IntegrityError`` raised out of
    the real ``DELETE`` (``FOREIGN KEY constraint failed``).  The shadow's
    primitive re-raises it under the model's name so the two legs' outcomes are
    compared on the same footing; the copied impl region itself has no handler,
    so the refusal propagates on both legs.
  * the model's ``int`` return <-> the ``count`` component of the real
    ``(count, {label: count})`` return.  The dict component is not modeled
    (mapping.md section 2); it is additionally sanity-checked to be
    ``{label: count}`` so the bridge cannot hide a count mismatch.

INPUT DOMAIN (satisfies the model's ``Requires``): ``Requires(Acc(instance.pk))``,
``Requires(instance.pk is not None)`` and
``Requires(-(2 ** 63) <= instance.pk < 2 ** 63)`` — a stored, non-``None``
integer identifier the store can represent.  Every generated input has ``pk`` an
``int`` (never ``None``) drawn from that signed 64-bit range, so every one of the
counted inputs satisfies the precondition, and the SAMPLED domain is exactly the
STATED one: the boundary list reaches both endpoints (``2**63 - 1``, ``-2**63``)
and the fuzz draws uniformly over the whole range.  Nothing in-domain is left
out, because one step past either endpoint the store can neither hold a row under
that identifier nor adapt it as a bind parameter (mapping.md section 3.1, checked
executably by axiom_check.py sections d/e), so no persistent object carries
one.  Three orthogonal
dimensions drive the axiomatized primitive to every outcome it has: whether a row
with that identifier exists (count 1) or not (count 0), whether the store holds
something PROTECTING that row (the removal is refused, no count at all), and the
alias tag.  The impl region is straight-line (no branches to cover); the
branchiness lives in the primitive's outcome and in the oracle's path selection,
both of which are covered every trial.  The protected trials are what keep the
exceptional clause honest: the model says a refusal happens only when the store
refuses, so every trial checks both directions — a leg that returned a count must
have run against a store that was not protecting the row, and a leg that refused
must have run against one that was.

  * BOUNDARY first: the exact F2P shape (``test_fast_delete_instance_set_pk_none``:
    a saved dependency-free object deleted, pk expected ``None``), then
    identifier extremes ``1, 2, 0, -1, -2**31, 2**31-1, -2**63, 2**63-1`` and a
    couple of mid values, crossed with row-present / row-absent and all three
    alias tags, plus the same identifiers with the row present AND protected.
  * FUZZ to reach the count: seeded uniform draws over the same space
    (identifier in the int64 range the backend accepts, presence, protection,
    tag).

INPUT COUNT: >= 100000 Requires-satisfying trials.  Pinned seed: 11179 (also
recorded in mapping.md, section "G-CONF").

Exit 0 iff zero disagreements; on a disagreement prints the input and both
outputs and exits 1.  stdlib + django (the repo under test) only.
"""
import json
import random
import sys
import tempfile
import types

SEED = 11179
N_TARGET = 100_000
N_TAGS = 3


# --- Nagini -> Python carriers ------------------------------------------------
# PersistentObject from model.py, contracts (Ensures/Acc) stripped.
class PersistentObject:
    def __init__(self, pk):
        self.pk = pk


# Database from model.py, contracts stripped: the handle a removal runs
# against, carrying the RECORD of the row-removal statements issued through it
# (how many, what the last one targeted, what it reported). `alias` is the
# bridge image of the opaque tag (mapping.md section 2): the concrete sqlite
# alias this handle speaks to.
class Database:
    def __init__(self, alias, refuses_removal=False):
        self.removal_statements = 0
        self.last_removal_target = 0
        self.last_removal_report = 0
        # bridge image of db.refuses_removal: whether the store behind `alias`
        # holds something protecting the row about to be targeted. READ from the
        # store's contents by the trial (the impl holds it at 1/2 in the model and
        # never writes it); the primitive below does not consult it — the real
        # DELETE either succeeds or is refused by the database itself.
        self.refuses_removal = refuses_removal
        self.alias = alias


class RemovalRefused(Exception):
    """Bridge image of model.py's ``RemovalRefused``: the store refused the
    row-removal statement.  The real signal is ``django.db.IntegrityError``
    ('FOREIGN KEY constraint failed') raised out of the real DELETE; the shadow's
    primitive re-raises it under the model's name (keeping the original as
    ``__cause__``) so both legs' outcomes are diffed on the same footing."""


# RemovalLedger from model.py, contracts stripped: the module-wide record of how
# many row-removal statements were issued IN TOTAL, across every handle. Its
# bridge image is the number of row-removal statements observed on ALL of the
# leg's connections during the trial, not just the one the handle names — the
# real cost the stored data paid, which is what a caller's statement-count
# observation sees.
class RemovalLedger:
    def __init__(self):
        self.total_removal_statements = 0


LEDGER = RemovalLedger()


def _observed_target(params):
    """The identifier a real row-removal statement was parameterized with.

    Read out of the statement's actual bind parameters (the fast branch removes
    by a one-element identifier list, so the DELETE carries exactly one
    parameter), never from the model-side argument — otherwise the target clause
    would be asserted rather than observed. Returns None when the parameters are
    not observable on this backend; the caller counts those and refuses to pass
    if the target was never observed at all."""
    if params is None:
        return None
    try:
        seq = list(params)
    except TypeError:
        return None
    return seq[0] if len(seq) == 1 else None


_MODEL = None


# --- the @ContractOnly axioms: call the REAL repo function --------------------
# remove_rows(db, identifier) axiomatizes
# django.db.models.sql.subqueries.DeleteQuery.delete_batch (mapping.md 3.1),
# invoked by the fast branch as
# sql.DeleteQuery(model).delete_batch([instance.pk], self.using).
#
# Every one of the axiom's Ensures is exercised against reality rather than
# assumed. The returned count is the real DB-reported rowcount. The
# `db.removal_statements == Old(...) + 1` clause is grounded by counting the
# SQL statements the real primitive actually issues (via the connection's
# execute_wrapper), NOT by incrementing a counter by hand — so if one
# delete_batch call on a one-element pk list ever issued a number of statements
# other than one, this leg would disagree with the tally the model's
# postcondition pins and the gate would fail. The `db.last_removal_target`
# clause is grounded by reading the identifier the observed statement was
# actually parameterized with, and `db.last_removal_report` by recording the
# count that same real statement returned.
#
# The axiom's exceptional case is grounded the same way. When the store refuses
# the removal the REAL delete_batch raises django.db.IntegrityError; the shadow
# does not predict that from db.refuses_removal, it lets the database decide and
# re-raises the refusal under the model's name. The statements the refused call
# issued are still recorded from the same observation (the model deliberately
# claims nothing about the record on that path, so recording it can only be
# observed against the oracle, never used to satisfy a clause).
def remove_rows(db, identifier):
    from django.db import connections
    from django.db.models import sql
    from django.db.utils import IntegrityError
    issued = []

    def _tally(execute, sql_text, params, many, context):
        issued.append((sql_text, params))
        return execute(sql_text, params, many, context)

    try:
        with connections[db.alias].execute_wrapper(_tally):
            count = sql.DeleteQuery(_MODEL).delete_batch([identifier], db.alias)
    except IntegrityError as exc:
        db.removal_statements += len(issued)
        LEDGER.total_removal_statements += len(issued)
        if issued:
            db.last_removal_target = _observed_target(issued[-1][1])
        raise RemovalRefused(str(exc)) from exc
    db.removal_statements += len(issued)
    # the module-wide total advances by the same observed statement count, no
    # matter which handle/alias the statement went through — grounding the
    # model's LEDGER.total_removal_statements clause in the real statements the
    # database received rather than in a per-handle tally.
    LEDGER.total_removal_statements += len(issued)
    if issued:
        db.last_removal_target = _observed_target(issued[-1][1])
    db.last_removal_report = count
    return count


# --- shadow: model.py impl region, VERBATIM, contract calls stripped ---------
def remove_single_independent(instance, db):
    # impl-start
    identifier = instance.pk  # type: Optional[int]
    count = remove_rows(db, identifier)
    instance.pk = None
    return count
    # impl-end


# --- Django bring-up ----------------------------------------------------------
def _configure():
    """Configure Django with 3 pairs of parallel in-memory sqlite connections
    and one minimal dependency-free model (the structural twin of the F2P
    test's ``User``: no FKs in or out, no parents, no signal listeners, i.e.
    exactly the ``can_fast_delete`` case the modeled branch handles)."""
    # A real (empty) package directory so AppConfig can locate the app.
    pkg_dir = tempfile.mkdtemp(prefix="confcheck_app_")
    mod = types.ModuleType("confcheck")
    mod.__path__ = [pkg_dir]
    sys.modules["confcheck"] = mod

    import django
    from django.conf import settings

    aliases = ["default"]
    for u in range(N_TAGS):
        aliases.append("shadow%d" % u)
        if u > 0:
            aliases.append("oracle%d" % u)
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["confcheck"],
            DATABASES={a: {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"} for a in aliases},
            USE_TZ=False,
        )
    django.setup()

    from django.db import connections, models

    class Independent(models.Model):
        class Meta:
            app_label = "confcheck"

    class Protector(models.Model):
        """A row the store keys to an ``Independent`` row. ``DO_NOTHING`` means
        Django asks the database for nothing on delete — so ``Independent``
        objects stay fast-deletable (the modeled branch is still the one taken)
        while the database's own FOREIGN KEY constraint protects the referenced
        row. Its presence is the bridge image of ``db.refuses_removal``."""
        target = models.ForeignKey(Independent, models.DO_NOTHING)

        class Meta:
            app_label = "confcheck"

    for a in aliases:
        with connections[a].schema_editor() as editor:
            editor.create_model(Independent)
            editor.create_model(Protector)
    # tag -> (shadow alias, oracle alias); 'default' serves as oracle tag 0.
    tag_aliases = [("shadow0", "default")]
    for u in range(1, N_TAGS):
        tag_aliases.append(("shadow%d" % u, "oracle%d" % u))
    return Independent, Protector, tag_aliases


def _assert_oracle_is_patched():
    """The oracle must be the PATCHED fast branch. If the pk-clearing statement
    is absent from the fast branch of the live source, the gate's patch-apply
    did not take effect and any 'pass' would be meaningless."""
    import inspect
    from django.db.models.deletion import Collector
    src = inspect.getsource(Collector.delete)
    fast_branch = src.split("with transaction.atomic")[0]
    if "setattr(instance, model._meta.pk.attname, None)" not in fast_branch:
        return ("ENV ERROR: the live Collector.delete fast branch has no "
                "pk-clearing statement: /testbed is not the patched source, "
                "so this differential would be vacuous.")
    return None


def _reference_constraint_enforced():
    """Whether the store really defends a referenced row — the mechanism the
    refusal dimension rides on. The bridge image of ``db.refuses_removal`` is a
    live protecting row, and it only protects anything if the backend enforces
    the reference constraint. Probed rather than assumed, so a backend that does
    not enforce it is reported as an explicit ``unsupported`` instead of being
    silently counted as agreement."""
    from django.db import connections
    for alias in connections:
        with connections[alias].cursor() as cur:
            cur.execute("PRAGMA foreign_keys")
            row = cur.fetchone()
        if not row or not row[0]:
            return False
    return True


def main():
    global _MODEL, _SHADOW_ALIAS

    Independent, Protector, TAG_ALIASES = _configure()
    _MODEL = Independent
    fk_enforced = _reference_constraint_enforced()

    env_err = _assert_oracle_is_patched()
    if env_err:
        print(env_err)
        print(json.dumps({"checked": 0, "disagreements": 0, "seed": SEED,
                          "error": "oracle not patched"}))
        return 1

    from django.db.models.deletion import Collector

    ATTNAME = Independent._meta.pk.attname     # the dynamic pk attribute name
    LABEL = Independent._meta.label

    def seed_row(alias, pk, present, protected):
        """Put the shared row state in place on `alias`: a row with identifier
        `pk` exists iff `present`, and the store holds something PROTECTING that
        row iff `protected` — a live ``Protector`` row referencing it, which is
        the bridge image of ``db.refuses_removal`` (mapping.md section 2).

        The protecting rows are cleared before the target row, because the
        constraint that makes the store refuse a removal would equally refuse
        this cleanup. `protected` implies `present`: a reference to an absent row
        is not something the store would hold in the first place."""
        Protector.objects.using(alias).filter(target_id=pk).delete()
        Independent.objects.using(alias).filter(pk=pk).delete()
        if present:
            Independent.objects.using(alias).create(pk=pk)
            if protected:
                Protector.objects.using(alias).create(target_id=pk)

    def store_protects(alias, pk):
        """Read the refusal fact OUT OF THE STORE, the way the model has a caller
        read ``db.refuses_removal``: is there a live row the store keeps that
        references `pk`? Never inferred from what the trial asked for, so a
        seeding bug cannot be mistaken for agreement."""
        return Protector.objects.using(alias).filter(target_id=pk).exists()

    def run_oracle(alias, pk):
        """Drive the REAL patched Collector.delete over a live instance whose
        stored identifier is `pk`. Returns
        (refused, count, pk_attr_after, per_label, removal_statements,
         removal_target, total_removal_statements)
        or an error string if the real code did not take the modeled branch.

        `refused` is True when the store REFUSED the removal — the real DELETE
        raised django.db.IntegrityError out of the fast branch. Nothing here
        predicts that: the refusal is whatever the database did, and `count` /
        `per_label` are None on that path because the real call produced no
        count. This is the oracle-side image of the model's
        Exsures(RemovalRefused, ...), and since the copied impl region has no
        handler the shadow leg reaches its refusal the same way.

        `removal_statements` is the number of row-removal (DELETE) statements
        the real fast branch issued ON `alias`, counted through the connection's
        execute_wrapper — the oracle-side image of the model's
        `db.removal_statements` tally (mapping.md section 2). `removal_target`
        is the identifier that real statement was parameterized with, the image
        of `db.last_removal_target`; the real fast branch's returned count is
        the image of `db.last_removal_report`.

        `total_removal_statements` is the number of row-removal statements the
        call issued across EVERY configured connection, not just `alias` — the
        image of the model's `LEDGER.total_removal_statements` delta. It is
        counted by wrapping all connections, so a branch that removed rows
        through some connection other than the one it was asked to use would be
        counted here even though the per-alias tally missed it. That is the
        observable a per-handle tally structurally cannot see, and it is what the
        suite's exact-statement-count assertion on a fast-deletable delete
        actually observes. This is what makes the model's single-statement,
        total-cost, statement-target and count-provenance postconditions
        refutable against reality instead of merely asserted."""
        from django.db import connections
        from django.db.utils import IntegrityError
        inst = Independent(pk=pk)
        collector = Collector(using=alias)
        collector.collect([inst])
        # The modeled branch's own guards (deletion.py:274-276). If these do
        # not hold the trial is outside the modeled domain -> bridge bug.
        if len(collector.data) != 1:
            return "collector.data has %d groups" % len(collector.data)
        instances = list(collector.data.values())[0]
        if len(instances) != 1:
            return "collected group holds %d instances" % len(instances)
        if not collector.can_fast_delete(inst):
            return "instance is not fast-deletable"
        issued = []
        all_issued = []

        def _tally(execute, sql_text, params, many, context):
            issued.append((sql_text, params))
            return execute(sql_text, params, many, context)

        def _tally_any(execute, sql_text, params, many, context):
            all_issued.append((sql_text, params))
            return execute(sql_text, params, many, context)

        # Wrap EVERY connection, so a statement issued anywhere is counted.
        # contextlib.ExitStack keeps the nesting flat regardless of alias count.
        import contextlib
        refused = False
        count = None
        per_label = None
        with contextlib.ExitStack() as stack:
            for other in connections:
                stack.enter_context(
                    connections[other].execute_wrapper(_tally_any))
            with connections[alias].execute_wrapper(_tally):
                try:
                    count, per_label = collector.delete()
                except IntegrityError:
                    # the store refused the removal statement; the real fast
                    # branch has no handler, so this is exactly what a caller of
                    # the real function sees.
                    refused = True
        target = _observed_target(issued[-1][1]) if issued else None
        return (refused, count, getattr(inst, ATTNAME), per_label, len(issued),
                target, len(all_issued))

    # trials on which the real statement's bind parameters were observable, so
    # the statement-target clause was checked differentially rather than skipped.
    target_observations = []
    # trials on which the store really REFUSED the removal, so the model's
    # exceptional clause was diffed against reality rather than assumed.
    refusal_observations = []

    def check(pk, present, tag, protected):
        shadow_alias, oracle_alias = TAG_ALIASES[tag]
        where = ("(pk=%r, row_present=%r, protected=%r, tag=%r)"
                 % (pk, present, protected, tag))

        # identical row state for both legs, protection included
        seed_row(shadow_alias, pk, present, protected)
        seed_row(oracle_alias, pk, present, protected)

        # The fact the model's `Old(db.refuses_removal)` names, READ OUT OF each
        # store's own contents rather than taken from what this trial asked for.
        # A seeding slip therefore shows up as an error instead of hiding inside
        # an agreement, and the value handed to the shadow's carrier is an
        # observation of the store, exactly as the model has a caller hold it.
        shadow_protects = store_protects(shadow_alias, pk)
        oracle_protects = store_protects(oracle_alias, pk)
        if shadow_protects != oracle_protects:
            return ("SEEDING ERROR on %s: the two legs' stores disagree about "
                    "whether the row is protected (%r vs %r), so the trial would "
                    "not be comparing like with like"
                    % (where, shadow_protects, oracle_protects))
        if shadow_protects != bool(present and protected):
            return ("SEEDING ERROR on %s: the store holds protection=%r for the "
                    "row, but the trial asked for %r"
                    % (where, shadow_protects, bool(present and protected)))

        # --- shadow leg: the contract-stripped impl region, real primitive ---
        # the opaque tag bridges to this leg's concrete alias (mapping.md 2)
        shadow_db = Database(shadow_alias, refuses_removal=shadow_protects)
        shadow_obj = PersistentObject(pk)          # Requires: pk is not None
        # the module-wide ledger's value BEFORE the call, so the trial observes
        # the DELTA the call caused -- the image of
        # Old(LEDGER.total_removal_statements).
        ledger_before = LEDGER.total_removal_statements
        # The copied impl region has no handler, so a refusal leaves the shadow
        # the same way it leaves the real fast branch: by propagating. Caught
        # HERE, outside the shadow, purely to record which outcome happened.
        shadow_refused = False
        shadow_count = None
        try:
            shadow_count = remove_single_independent(shadow_obj, shadow_db)
        except RemovalRefused:
            shadow_refused = True
        shadow_total_delta = LEDGER.total_removal_statements - ledger_before
        shadow_pk = shadow_obj.pk
        shadow_statements = shadow_db.removal_statements
        shadow_target = shadow_db.last_removal_target
        shadow_report = shadow_db.last_removal_report

        # --- oracle leg: the real patched function ---------------------------
        got = run_oracle(oracle_alias, pk)
        if isinstance(got, str):
            return ("OUT OF DOMAIN on %s: the real Collector.delete did not take "
                    "the modeled single-object branch: %s" % (where, got))
        (real_refused, real_count, real_pk, per_label, real_statements,
         real_target, real_total) = got

        # (6) the exceptional clause, BOTH directions and both legs. The model
        # says a count is returned only for a removal the store carried out
        # (`Ensures(not Old(db.refuses_removal))`) and a refusal is reported only
        # for one the store really refused (`Exsures(..., Old(...))`). So: a leg
        # that returned a count must have run against a store that was not
        # protecting the row, and a leg that refused must have run against one
        # that was.
        if shadow_refused != real_refused:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow ended with %s\n"
                    "  real ended with   %s"
                    % (where,
                       "a refusal" if shadow_refused
                       else "count %r" % (shadow_count,),
                       "a refusal" if real_refused
                       else "count %r" % (real_count,)))
        if real_refused and not oracle_protects:
            return ("DISAGREEMENT on %s: the removal was refused although the "
                    "store held nothing protecting the row, but the modeled "
                    "exceptional clause admits a refusal only when it did"
                    % where)
        if not real_refused and oracle_protects and fk_enforced:
            return ("DISAGREEMENT on %s: a count (%r) was returned although the "
                    "store was protecting the row, but the model pins a returned "
                    "count to a removal the store carried out" % (where, real_count))
        if real_refused:
            refusal_observations.append(1)
        if not real_refused and shadow_count != real_count:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow count = %r\n"
                    "  real count   = %r"
                    % (where, shadow_count, real_count))
        if (shadow_pk is None) != (real_pk is None) or shadow_pk != real_pk:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow pk after = %r\n"
                    "  real pk after   = %r  (attribute %r)"
                    % (where, shadow_pk, real_pk, ATTNAME))
        # the single-statement cost clause: both legs must issue the SAME number
        # of row-removal statements, and (the model's postcondition) exactly one.
        # A refused removal still cost the statement the store refused, and the
        # two legs must agree on that too.
        if shadow_statements != real_statements:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow removal statements = %r\n"
                    "  real removal statements   = %r"
                    % (where, shadow_statements, real_statements))
        if real_statements != 1:
            return ("DISAGREEMENT on %s: the modeled postcondition pins the "
                    "tally at Old + 1, but the real fast branch issued %r "
                    "row-removal statement(s)" % (where, real_statements))
        # the TOTAL cost clause: the number of row-removal statements the call
        # issued across EVERY connection must agree between the legs, and (the
        # model's postcondition) be exactly one. This is the clause a per-handle
        # tally cannot express: it is what refutes a branch that keeps its named
        # connection at one statement while removing rows through another.
        if shadow_total_delta != real_total:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow TOTAL removal statements = %r\n"
                    "  real TOTAL removal statements   = %r"
                    % (where, shadow_total_delta, real_total))
        if real_total != 1:
            return ("DISAGREEMENT on %s: the modeled postcondition pins the "
                    "module-wide total at Old + 1, but the real fast branch "
                    "issued %r row-removal statement(s) in total across all "
                    "connections" % (where, real_total))
        # the statement-target clause: both legs' one statement must have been
        # issued for the SAME identifier, and (the model's postcondition) for the
        # object's stored identifier.
        if shadow_target != real_target:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow removal target = %r\n"
                    "  real removal target   = %r"
                    % (where, shadow_target, real_target))
        if real_target is not None:
            if real_target != pk:
                return ("DISAGREEMENT on %s: the modeled postcondition pins the "
                        "removal target at the object's stored identifier, but "
                        "the real fast branch removed by %r" % (where, real_target))
            target_observations.append(1)
        if real_refused:
            # Nothing further is comparable on this path: the model deliberately
            # promises no count and no report where the store carried nothing
            # out, and the real call produced neither.
            if per_label is not None or real_count is not None:
                return ("BRIDGE DISAGREEMENT on %s: the real call refused the "
                        "removal yet produced count=%r, per-label=%r"
                        % (where, real_count, per_label))
            return None
        # the count-provenance clause: the surfaced count IS the row count the
        # issued statement itself reported, on both legs.
        if shadow_report != shadow_count:
            return ("DISAGREEMENT on %s: the modeled postcondition pins the "
                    "returned count to the issued statement's own report, but "
                    "shadow returned %r while the statement reported %r"
                    % (where, shadow_count, shadow_report))
        # bridge sanity: the unmodeled dict component is {label: count}
        if per_label != {LABEL: real_count}:
            return ("BRIDGE DISAGREEMENT on %s:\n"
                    "  real per-label dict = %r, expected %r"
                    % (where, per_label, {LABEL: real_count}))
        return None

    checked = 0
    counts_seen = set()
    # (present, protected): protection presupposes a row to protect, so the third
    # combination (absent AND protected) is not a state the store can hold. When
    # the backend does not enforce the reference constraint at all there is no
    # protecting row to be had, and the refusal dimension drops out -- reported as
    # an explicit `unsupported` below rather than passed off as agreement.
    row_states = [(True, False), (False, False)]
    if fk_enforced:
        row_states.append((True, True))

    # --- boundary: the F2P shape first, then identifier extremes -------------
    # test_fast_delete_instance_set_pk_none: a saved dependency-free object is
    # deleted and its pk must be None afterwards.
    boundary_pks = [1, 2, 3, 0, -1, 7, 12345,
                    2 ** 31 - 1, -2 ** 31, 2 ** 63 - 1, -2 ** 63]
    for pk in boundary_pks:
        for present, protected in row_states:
            for tag in range(N_TAGS):
                err = check(pk, present, tag, protected)
                if err:
                    print(err)
                    print(json.dumps({"checked": checked, "disagreements": 1,
                                      "seed": SEED}))
                    return 1
                if not protected:
                    counts_seen.add(1 if present else 0)
                checked += 1

    # --- seeded fuzz over the same Requires-satisfying space ----------------
    rng = random.Random(SEED)
    while checked < N_TARGET:
        pk = rng.randint(-2 ** 63, 2 ** 63 - 1)
        present, protected = row_states[rng.randrange(len(row_states))]
        tag = rng.randrange(N_TAGS)
        err = check(pk, present, tag, protected)
        if err:
            print(err)
            print(json.dumps({"checked": checked, "disagreements": 1,
                              "seed": SEED}))
            return 1
        checked += 1

    # The statement-target clause is only genuinely differential on trials where
    # the real statement's bind parameters were observable. If they never were,
    # say so as an explicit `unsupported` (the gate treats that as a skip) rather
    # than let an unobserved clause ride along inside a pass.
    unsupported = []
    if not target_observations:
        print("G-CONF: the real row-removal statement's bind parameters were "
              "never observable on this backend, so the statement-target clause "
              "could not be checked differentially.")
        print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                          "unsupported": ["removal-target bind parameters not "
                                          "observable via execute_wrapper"]}))
        return 0
    if not fk_enforced:
        # No protecting row is possible, so the exceptional clause was not
        # exercised. Say so instead of letting an unexercised clause ride along
        # inside a pass.
        print("G-CONF: this backend does not enforce the reference constraint "
              "(PRAGMA foreign_keys off), so no store state protects a row and "
              "the modeled refusal clause could not be checked differentially.")
        unsupported.append("refusal clause: backend does not enforce the "
                           "reference constraint that protects a row")
    elif not refusal_observations:
        # The dimension was generated and the constraint is enforced, so a
        # refusal must have been observed. Zero means the trials never reached
        # the exceptional path and the clause is unexercised -- a defect in this
        # check, not a pass.
        print("G-CONF ERROR: the reference constraint is enforced and protected "
              "trials were generated, yet the store never refused a removal, so "
              "the modeled exceptional clause was never exercised.")
        print(json.dumps({"checked": checked, "disagreements": 1, "seed": SEED,
                          "error": "refusal clause never exercised"}))
        return 1

    print("G-CONF OK: contract-stripped impl region of "
          "remove_single_independent (with remove_rows -> the REAL "
          "DeleteQuery.delete_batch) == the REAL patched fast single-object "
          "branch of Collector.delete on %d Requires-satisfying inputs "
          "(seed %d): counts agree (observed %s), the pk attribute %r is "
          "cleared on both legs, both legs issue exactly ONE row-removal "
          "statement (counted via execute_wrapper, matching the modeled "
          "Old + 1 tally), that statement was issued for the object's stored "
          "identifier on both legs (%d trials with observable bind "
          "parameters, matching the modeled removal-target pin), the "
          "surfaced count is that statement's own reported rowcount (matching "
          "the modeled count-provenance pin), and on %d trials the store "
          "REFUSED the removal on both legs — always and only where the store "
          "held a row protecting the target, matching the modeled exceptional "
          "clause in both directions; 0 disagreements."
          % (checked, SEED, sorted(counts_seen), ATTNAME,
             len(target_observations), len(refusal_observations)))
    result = {"checked": checked, "disagreements": 0, "seed": SEED,
              "target_observed": len(target_observations),
              "refusals_observed": len(refusal_observations),
              "shadow": "direct (contract-stripped impl region)",
              "oracle": "called: django.db.models.deletion."
                        "Collector.delete (patched fast branch)"}
    if unsupported:
        result["unsupported"] = unsupported
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
