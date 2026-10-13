#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11087.

This bundle consumes NO `@ContractOnly` axiom: the two modelled decisions are
pure boolean / sequence logic over abstract observation flags and column
tokens, spelled out in full in model.py. G-AX therefore validates the
*behavioural facts the deep model rests on* against the REAL runtime semantics
the patched code uses:

  (A-reference 1) the exposure predicate `exposed_to_observers(pre, post)` ==
      `pre or post` is the real `_has_signal_listeners`:
        signals.pre_delete.has_listeners(model) or
        signals.post_delete.has_listeners(model)
      G-AX drives the REAL `django.db.models.signals.pre_delete` /
      `post_delete` Signal objects: with no receiver connected the disjunction
      is False; connecting a `pre_delete` (or `post_delete`) receiver makes it
      True; disconnecting restores False. It also confirms the NEW helper omits
      the `m2m_changed` term that the old `can_fast_delete` guard carried — a
      connected `m2m_changed` receiver does NOT make `_has_signal_listeners`
      True (only `pre_delete`/`post_delete` do).

  (A-reference 2) the column decision `select_cascade_fields`. G-AX
      reconstructs the patched `collect` data flow EXACTLY as the gold patch
      writes it
        if not (sub_objs.query.select_related or
                self._has_signal_listeners(related_model)):
            referenced_fields = set(chain.from_iterable(
                (rf.attname for rf in rel.field.foreign_related_fields)
                for rel in get_candidate_relations_to_delete(related_model._meta)))
            sub_objs = sub_objs.only(*tuple(referenced_fields))
      over a mirror of the query layer faithful to the deferred-loading
      semantics documented in §3.2 of mapping.md, and asserts the model's cell
      postconditions. It also asserts the PRE-patch skeleton violates exactly
      the model clause `model_prepatch` fails on.

      Crucially, the pending queryset the branch receives is NOT assumed
      unrestricted. `Collector.related_objects` obtains it from
      `related_model._base_manager`, so a `Meta.base_manager_name` pointing at a
      manager that already narrowed the column set — or an overridden
      `related_objects`, as `django.contrib.admin.utils.NestedObjects` does
      in-tree — hands the branch a query that already carries a restriction of
      its own. The mirror therefore models `deferred_loading` as the real
      `(field_names, defer)` pair and reproduces the real transitions.

`django.db.models.signals` needs no settings/DB connection. The column-set
mirror uses only the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from django.db.models import signals


# --- (A-reference 1) the real pre/post-delete has_listeners disjunction ------

def real_has_signal_listeners(sender):
    """Reconstruct the REAL `_has_signal_listeners` from the gold patch."""
    return (
        signals.pre_delete.has_listeners(sender) or
        signals.post_delete.has_listeners(sender)
    )


def check_signal_observable():
    # A unique sender object per check so receiver bookkeeping cannot leak.
    sender = type("Sender_%d" % random.randrange(1 << 30), (), {})

    assert real_has_signal_listeners(sender) is False, (
        "with no receiver connected the exposure predicate must be False")

    def receiver(instance=None, **kwargs):
        pass

    # pre_delete alone -> True
    signals.pre_delete.connect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is True, (
        "a connected pre_delete receiver must make the predicate True "
        "(model: Implies(pre, Result()))")
    signals.pre_delete.disconnect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is False

    # post_delete alone -> True
    signals.post_delete.connect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is True, (
        "a connected post_delete receiver must make the predicate True "
        "(model: Implies(post, Result()))")
    signals.post_delete.disconnect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is False

    # m2m_changed alone -> still False: the NEW helper dropped this term.
    signals.m2m_changed.connect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is False, (
        "a connected m2m_changed receiver must NOT make the exposure predicate "
        "True: the new _has_signal_listeners omits the m2m_changed term "
        "(model: exposed_to_observers == pre or post, no third term)")
    signals.m2m_changed.disconnect(receiver, sender=sender)
    assert real_has_signal_listeners(sender) is False


# --- (A-reference 2) the real column decision --------------------------------
# A mirror of the query layer's deferred-loading state and of the column set it
# compiles, encoding the facts the real code exhibits (each of them verified
# against the REAL emitted SQL by conformance_check.py, which CALLS the real
# function on real querysets):
#
#   * the state is the real `(field_names, defer)` pair. `defer=True` means
#     "load everything except these"; `defer=False` means "load only these",
#     and an empty `field_names` means "no restriction at all" — the compiler's
#     `deferred_to_data` returns at `if not field_names`
#     (django/db/models/sql/query.py:656);
#   * `.only(*cols)` calls `add_immediate_loading(cols)` (sql/query.py:1959),
#     which RESPECTS an existing deferral: when the pending state is a deferral
#     it stores `set(cols).difference(existing)`, so a column the pending query
#     already deferred is NOT brought back by naming it. When the pending state
#     is itself an immediate-loading set it is REPLACED outright;
#   * whatever the restriction, the compiler always retains the row-identity
#     column: `deferred_to_data` seeds `must_include` with `orig_opts.pk`
#     (sql/query.py:660), so the loaded set contains the pk even when it is not
#     one of the referenced FK targets;
#   * `.only()` with NO arguments therefore stores an EMPTY immediate-loading
#     set, which is not a narrowing but a reset: every concrete column is
#     loaded, including any the pending query had been deferring;
#   * with no `.only` call at all, the pending state stands unchanged — so what
#     the pending query already fetches is what is fetched, which need not be
#     the full column set.
#
# Two earlier revisions of this mirror were wrong and are recorded here so the
# lane cannot regress to either: the first encoded `loaded = set(fields)`
# unconditionally (dropping the always-retained row identity and turning the
# empty `.only()` reset into a fetch of nothing); the second fixed those but
# still hard-wired the pending query to the unrestricted state, so it could not
# express either the `difference(existing)` subtraction or the fact that with no
# request made the pending query's own narrower set is what is fetched.
# We model a column as an integer token and a column set as a set of tokens.

class FakeQuery:
    """The real `Query`'s deferred-loading state and compiled column set."""

    def __init__(self, all_fields, pk, deferred_loading=None,
                 select_related=False):
        self._all = set(all_fields)
        self._pk = pk
        # the real `Query.deferred_loading` pair; the real default
        self.deferred_loading = (
            (frozenset(), True) if deferred_loading is None
            else (frozenset(deferred_loading[0]), deferred_loading[1]))
        self.select_related = select_related

    # --- sql/query.py:1959, add_immediate_loading ------------------------
    def add_immediate_loading(self, field_names):
        existing, defer = self.deferred_loading
        field_names = set(field_names)
        if defer:
            # "immediate loading ... respects existing deferrals"
            self.deferred_loading = field_names.difference(existing), False
        else:
            self.deferred_loading = frozenset(field_names), False

    # --- sql/query.py:1939, add_deferred_loading -------------------------
    def add_deferred_loading(self, field_names):
        existing, defer = self.deferred_loading
        if defer:
            self.deferred_loading = existing.union(field_names), True
        else:
            self.deferred_loading = existing.difference(field_names), False

    # --- sql/query.py:645, deferred_to_data + the compiler's column list --
    def compiled_columns(self):
        field_names, defer = self.deferred_loading
        if not field_names:
            # `deferred_to_data` returns here: NO restriction is applied.
            return set(self._all)
        if defer:
            loaded = self._all - set(field_names)
            if not loaded:
                # The defer branch builds `workset` from the local fields NOT
                # deferred; if every field is deferred the model never enters
                # `workset`, and "an empty set means include all fields"
                # (sql/query.py:700-703), so deferring everything restricts
                # nothing at all.
                return set(self._all)
        else:
            loaded = set(field_names) & self._all
        # must_include = {concrete_model: {orig_opts.pk}}
        return loaded | {self._pk}


class FakeQS:
    def __init__(self, all_fields, pk, deferred_loading=None,
                 select_related=False):
        self.query = FakeQuery(all_fields, pk,
                               deferred_loading=deferred_loading,
                               select_related=select_related)

    def only(self, *fields):
        self.query.add_immediate_loading(fields)
        return self

    def defer(self, *fields):
        self.query.add_deferred_loading(fields)
        return self

    def loaded_columns(self):
        return self.query.compiled_columns()


def gold_collect_columns(all_fields, pk, pending, referenced, select_related,
                         pre, post):
    """The patched `collect` branch, transcribed over the query-layer mirror.

    `pending` is the pending query's own `deferred_loading` pair (the state the
    branch INHERITS from `related_objects`); `referenced` is the raw consulted
    set the branch itself computes and hands to `.only()` unfiltered.
    """
    qs = FakeQS(all_fields, pk, deferred_loading=pending,
                select_related=select_related)
    related_model = type("RelModel_%d" % random.randrange(1 << 30), (), {})

    def has_signal_listeners(model):
        return pre or post  # the new _has_signal_listeners (pre/post only)

    if not (qs.query.select_related or has_signal_listeners(related_model)):
        referenced_fields = set(referenced)
        qs = qs.only(*tuple(referenced_fields))
    return qs.loaded_columns()


def prepatch_collect_columns(all_fields, pk, pending, referenced,
                             select_related, pre, post):
    """The PRE-patch `collect` branch: `sub_objs` is passed on untouched, so
    whatever the pending query fetches on its own is what is fetched, and no
    narrowing is ever requested."""
    qs = FakeQS(all_fields, pk, deferred_loading=pending,
                select_related=select_related)
    return qs.loaded_columns()


def model_cells(all_fields, already_selected, referenced, pk,
                whole_row_required, pre, post):
    """The model's own cell partition, as `select_cascade_fields` states it."""
    if whole_row_required or pre or post:
        return set(already_selected)          # cell 4: the pending set stands
    if len(referenced) > 0:
        return set(referenced) | {pk}         # cells 1 & 2: narrowed + identity
    return set(all_fields)                    # cell 3: naming nothing resets


def check_column_decision(all_fields, pk, pending, referenced, select_related,
                          pre, post):
    all_set = set(all_fields)
    ref_set = set(referenced)
    assert ref_set <= all_set, "referenced columns must be a subset of all"
    assert pk in all_set, "the row-identity column must be one of the columns"

    # The model's inputs, derived from the pending query the same way the type
    # bridge derives them (mapping.md §2): `already_selected` is what the
    # pending query fetches with no further request, and `referenced` is the
    # consulted set MINUS what the pending query defers, because
    # `add_immediate_loading` subtracts exactly that.
    pending_qs = FakeQS(all_fields, pk, deferred_loading=pending,
                        select_related=select_related)
    already_selected = pending_qs.loaded_columns()
    pending_names, pending_defer = pending_qs.query.deferred_loading
    deferred = set(pending_names) if pending_defer else set()
    reachable = ref_set - deferred

    observed = gold_collect_columns(all_fields, pk, pending, referenced,
                                    select_related, pre, post)
    expected = model_cells(all_fields, already_selected, sorted(reachable), pk,
                           select_related, pre, post)
    assert observed == expected, (
        "gold collect column set wrong: all=%r pk=%r pending=%r referenced=%r "
        "select_related=%r pre=%r post=%r -> observed=%r expected=%r"
        % (all_fields, pk, pending, referenced, select_related, pre, post,
           observed, expected))

    # The pre-patch never narrows: it hands on whatever the pending query
    # fetches. It disagrees with the model in exactly the reducible case where
    # the reachable-plus-identity set is not what the pending query fetches
    # (the F2P scenario, where the pending query is unrestricted and the model
    # cell asks for strictly fewer columns).
    pre_observed = prepatch_collect_columns(all_fields, pk, pending, referenced,
                                            select_related, pre, post)
    assert pre_observed == already_selected, (
        "the pre-patch branch must leave the pending query untouched")
    reduced = (not (select_related or pre or post)) and bool(reachable)
    if reduced and (reachable | {pk}) != already_selected:
        assert pre_observed != (reachable | {pk}), (
            "pre-patch must over-fetch in the reducible case (the bug)")


def main():
    # --- (A-reference 1) signal observable ---------------------------------
    for _ in range(200):
        check_signal_observable()

    # --- (A-reference 2) the column decision -------------------------------
    # The F2P scenario: Referrer has columns {id, unique_field, large_field};
    # only {id, unique_field} are referenced by SecondReferrer's FKs, and the
    # pending query is the plain unrestricted base-manager one.
    ID, UNIQUE, LARGE = 1, 2, 3
    f2p_all = [ID, UNIQUE, LARGE]
    f2p_ref = [ID, UNIQUE]
    NONE = (frozenset(), True)                       # the real default state
    # no signals -> only referenced columns (large_field not fetched)
    check_column_decision(f2p_all, ID, NONE, f2p_ref, False, False, False)
    # pre_delete or post_delete connected -> the pending set (here: everything)
    check_column_decision(f2p_all, ID, NONE, f2p_ref, False, True, False)
    check_column_decision(f2p_all, ID, NONE, f2p_ref, False, False, True)
    check_column_decision(f2p_all, ID, NONE, f2p_ref, False, True, True)
    # select_related -> the pending set (the feature-interaction guard)
    check_column_decision(f2p_all, ID, NONE, f2p_ref, True, False, False)

    # boundary cases over the consulted set
    check_column_decision([7], 7, NONE, [7], False, False, False)
    check_column_decision([7, 8, 9], 7, NONE, [], False, False, False)
    # the row identity OUTSIDE the consulted set: it is fetched anyway (the
    # to_field-only reverse-FK shape)
    check_column_decision([7, 8, 9], 7, NONE, [8], False, False, False)
    check_column_decision([7, 8, 9], 7, NONE, [8, 9], False, False, False)

    # boundary cases over the PENDING query's own restriction
    # (a) the pending query defers a CONSULTED column: naming it does not bring
    #     it back, and when it was the only consulted column nothing consulted
    #     remains reachable, so the request degenerates to a reset.
    check_column_decision([7, 8, 9], 7, ({8}, True), [8], False, False, False)
    check_column_decision([7, 8, 9], 7, ({8}, True), [8, 9], False, False, False)
    # (b) the pending query defers a NON-consulted column: the narrowing still
    #     reaches every consulted column.
    check_column_decision([7, 8, 9], 7, ({9}, True), [8], False, False, False)
    # (c) the pending query carries an IMMEDIATE-loading set, which the request
    #     replaces outright rather than subtracting from.
    check_column_decision([7, 8, 9], 7, ({8}, False), [9], False, False, False)
    # (d) the pending query is narrowed AND no request is made: its own set is
    #     what is fetched, and it is NOT the full column set.
    check_column_decision([7, 8, 9], 7, ({9}, True), [8], False, True, False)
    check_column_decision([7, 8, 9], 7, ({8}, False), [9], False, False, True)
    check_column_decision([7, 8, 9], 7, ({9}, True), [8], True, False, False)
    # (e) the pending query defers EVERY consulted column and no request is
    #     made: the two cells that could be confused are pulled apart.
    check_column_decision([7, 8, 9], 7, ({8, 9}, True), [8, 9], False, False,
                          False)
    check_column_decision([7, 8, 9], 7, ({8, 9}, True), [8, 9], False, True,
                          False)

    # randomized fuzz over flags, column/consulted subsets AND pending states
    rng = random.Random(11087)
    for _ in range(20000):
        n = rng.randint(1, 8)
        all_fields = rng.sample(range(1, 50), n)
        pk = all_fields[rng.randrange(n)]
        k = rng.randint(0, n)
        referenced = rng.sample(all_fields, k)
        # a pending state drawn over the whole space: no restriction, a
        # deferral of a random subset, or an immediate-loading set
        r = rng.random()
        if r < 0.34:
            pending = (frozenset(), True)
        else:
            j = rng.randint(0, n)
            names = frozenset(rng.sample(all_fields, j))
            pending = (names, r < 0.67)
        select_related = rng.random() < 0.5
        pre = rng.random() < 0.5
        post = rng.random() < 0.5
        check_column_decision(all_fields, pk, pending, referenced,
                              select_related, pre, post)

    print("G-AX OK: exposure predicate == real pre/post-delete has_listeners "
          "(m2m_changed excluded) over 200 connect/disconnect cycles; "
          "column decision == the real .only-based collect branch over the real "
          "deferred-loading semantics (identity column always retained; an "
          "empty .only() resets rather than narrows; a new immediate-loading "
          "set respects an existing deferral; with no request the pending "
          "query's own set stands) over 19 boundary + 20000 fuzz "
          "configurations spanning every pending-query state.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
