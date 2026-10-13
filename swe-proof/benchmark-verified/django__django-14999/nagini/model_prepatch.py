"""Twin-artifact model for django__django-14999.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Applying a model-rename to the database is driven entirely by whether the
  stored table name actually changes. The operation is handed the stored table
  identifier the model used before the rename and the one it uses after, plus
  the dependents that have to be carried along with the renamed table. The
  dependents arrive in TWO collections, because the two kinds of dependent need
  different amounts of schema work:

    * a COLUMN RELATION is a column in some OTHER table that reaches the
      renamed model (a foreign key pointing at it). Carrying it along takes ONE
      request: rewrite that column.
    * a LINK RELATION is an auto-created link table standing behind one of the
      renamed model's many-to-many relations. The link table's OWN name is
      derived from the renamed model's name, so carrying it along takes TWO
      requests: MOVE that link table, and rewrite the column INSIDE it that
      reaches the renamed model.

  SCOPE. What follows describes a rename that the storage layer actually
  carries out and whose dependents are all reachable. Two things are assumed of
  the configuration, and both are assumptions about the INPUT rather than
  properties of the schedule:

    * the operation is permitted to act on the renamed model's storage at all.
      An operation that is not permitted to act on it asks for nothing whatever
      the two identifiers say, so there is no schedule of dependent work to
      describe.
    * every link relation really does CARRY the column that reaches the renamed
      model, addressable inside its link table under the renamed model's name
      BOTH before and after the rename. A link relation whose inside column
      cannot be addressed under one of those two names has no such column to
      rewrite, so no schedule covering it exists either -- and, because the
      schedule is issued as it is computed, such a link relation also cuts short
      whatever dependent work would otherwise have followed it.

  Neither assumption is about the table identifiers, so both branches below are
  described in full within this scope.

  The observable is the SCHEDULE of schema operations the rename REQUESTS of
  the schema layer, IN THE ORDER it requests them. Each entry says WHAT the
  request operates on: the move of the renamed model's OWN table, the rewrite
  of ONE PARTICULAR column relation, or ONE of the TWO requests belonging to
  ONE PARTICULAR link relation. A link relation's two requests are two SEPARATE
  entries, not one: they operate on different things -- a table, and a column
  inside that same table -- so the schedule that carries them also carries the
  order between them. (Whether a requested operation then turns into a
  statement the database executes is the schema layer's own affair and is
  deliberately not part of this observable.)

    (1) When the before- and after- table identifiers are the SAME, the whole
        operation is observationally inert: it requests NO schema work at all —
        not the move of its own table, and crucially none of the requests
        belonging to the dependent column relations and link relations. The
        schedule is empty.

    (2) When the two table identifiers DIFFER the operation proceeds, and the
        schedule is then precisely a relocation of that one table together with
        its dependents:
          (a) the move of the renamed model's own table comes FIRST, ahead of
              every dependent request. That order is load-bearing rather than
              cosmetic: a dependent request is addressed to the renamed model's
              table under its NEW identifier, so a request scheduled ahead of
              the move addresses a table that is not there yet, and the move
              that follows then arrives at an identifier something else already
              occupies.
          (b) after the move, EVERY dependent request is issued EXACTLY ONCE
              and the schedule holds nothing else: one request for each column
              relation, and BOTH requests for each link relation. Both halves
              matter: a dependent whose request is missing keeps naming a table
              that has moved, and a request issued twice is applied a second
              time to a table the first one already moved.
          (c) WITHIN one link relation, the MOVE of the link table comes before
              the rewrite of the column inside that link table. This is the
              same already-moved discipline one level down: the column rewrite
              is addressed to the link table under the link table's NEW
              identifier, so asking for it first addresses a table that is not
              there yet, and the move that follows then relocates a table whose
              column still names the identifier the renamed model no longer
              uses. WHICH link relation is served first is free; the order of
              the two requests INSIDE one of them is not.

The discriminating behaviour is this: request nothing at all exactly when the
table identifier is unchanged, and otherwise request the move of the model's own
table first and then, once each, every request the dependents need — with each
link relation's move preceding its own column rewrite. Neither non-emptiness nor
the total number of requests is the property: a schedule can be non-empty, or
even have exactly the right length, while omitting the move of the model's own
table, while deferring that move behind the dependent requests, while serving
one dependent twice and another not at all, or while asking to rewrite the
column inside a link table before that link table has been moved — and none of
those is a rename. What is deliberately NOT pinned is the order the dependents
are taken in among THEMSELVES: any order of the column relations, any order of
the link relations, and any interleaving of the two will do, because each
dependent request is addressed to the renamed model's table after that table has
already moved.

The two table identifiers are modelled as ``int`` (only their equality is
observable to the schema layer). The dependents are modelled as the POSITIONS of
two ``List[int]``s, ``column_relations`` and ``link_relations``: the identity of
a dependent is irrelevant, but WHICH of them a request operates on is not, so a
request names a position. The schedule is a ``List[int]``, with ``nc`` written
for ``len(column_relations)``:

  * ``OP_MAIN_MOVE``   — move the renamed model's own table;
  * ``i``              — rewrite the column relation at position ``i``
                         (``0 <= i < nc``);
  * ``nc + 2 * j``     — move the link table of the link relation at position
                         ``j``;
  * ``nc + 2 * j + 1`` — rewrite the column inside THAT SAME link table.

So the two requests of one link relation are two CONSECUTIVE codes: the one
whose offset from ``nc`` is EVEN moves the link table, and its successor
rewrites the column inside it. Positions and offsets are never negative, so no
dependent request can pass for the move of the model's own table and no move can
pass for a dependent request.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged callee needs axiomatizing: the relevant behaviour — which schema
# operations the rename requests, and in which order — is decided entirely by
# the table-identity comparison and the two dependent collections, all modelled
# deeply below. There is no axiomatized callee whose contract the proof
# consumes.)
# axioms-end


# pure-start
OP_MAIN_MOVE = -1  # the request to move the renamed model's OWN table
# Every other schedule entry is a request belonging to ONE dependent, named by
# the code scheme in the module docstring: a position of ``column_relations``,
# or one of the two consecutive codes of a position of ``link_relations`` (the
# even offset from len(column_relations) being the move of the link table, its
# successor the rewrite of the column inside that link table). Codes are never
# negative, so no dependent request can pass for the move of the model's own
# table and no move can pass for a dependent request.
# pure-end


def rename_schema_schedule(before_table: int, after_table: int,
                           column_relations: List[int],
                           link_relations: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(column_relations), 1 / 2))
    Requires(Acc(list_pred(link_relations), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(column_relations), 1 / 2))
    Ensures(Acc(list_pred(link_relations), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) Same table identifier => inert: the schedule is empty, so neither the
    # move of the model's own table nor any dependent request is issued.
    Ensures(Implies(before_table == after_table, len(Result()) == 0))
    # (2) Proceeding => the move of the renamed model's OWN table is the FIRST
    # request. A rename relocates that table before anything is addressed to its
    # new identifier, so a schedule that never asks for the move, or that asks
    # for it only after some dependent request, is not a rename of it.
    Ensures(Implies(before_table != after_table,
                    len(Result()) > 0 and Result()[0] == OP_MAIN_MOVE))
    # (3) Every request after that first one is a dependent request — a position
    # of ``column_relations``, or one of the two codes of a position of
    # ``link_relations``. So the schedule carries no second move of the model's
    # own table and no entry that names no schema work at all.
    Ensures(Forall(int, lambda i: Implies(1 <= i and i < len(Result()),
                   0 <= Result()[i]
                   and Result()[i] < len(column_relations)
                   + 2 * len(link_relations))))
    # (4) No request is issued twice: two entries never carry the same code,
    # because the second would be applied to a table the first one already
    # moved. In particular a link relation's move is not issued twice and
    # neither is the rewrite of the column inside it.
    Ensures(Forall(int, lambda i: Forall(int, lambda j: Implies(
        1 <= i and i < j and j < len(Result()),
        Result()[i] != Result()[j]))))
    # (5) Proceeding => the schedule is that one move plus one request per
    # column relation plus BOTH requests per link relation, and nothing besides.
    # Together with (3) and (4) this also leaves no dependent request
    # unrequested: 1 + nc + 2*nl entries, each carrying a code of the scheme and
    # no two of them carrying the same code, carry EVERY code — so every column
    # relation is rewritten exactly once, every link table is moved exactly
    # once, the column inside every link table is rewritten exactly once, and no
    # filler entry can stand in for a request that is missing.
    Ensures(Implies(before_table != after_table,
                    len(Result()) == 1 + len(column_relations)
                    + 2 * len(link_relations)))
    # (6) WITHIN one link relation the move of the link table precedes the
    # rewrite of the column inside that link table. The two codes of one link
    # relation are consecutive, the move sitting at the EVEN offset from
    # len(column_relations); so this says: wherever the schedule carries a link
    # table's move, the entry carrying that link table's own column rewrite
    # (code + 1) comes strictly later. Nothing here constrains two requests
    # belonging to DIFFERENT dependents — the guard's parity is exactly what
    # keeps clause (6) silent about a link relation's column rewrite and the
    # NEXT link relation's move, whose codes are also consecutive.
    Ensures(Forall(int, lambda p: Forall(int, lambda q: Implies(
        1 <= p and p < len(Result()) and 1 <= q and q < len(Result())
        and Result()[p] >= len(column_relations)
        and (Result()[p] - len(column_relations)) % 2 == 0
        and Result()[q] == Result()[p] + 1,
        p < q))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    nc = len(column_relations)
    nl = len(link_relations)
    # The move of the model's own table is asked for only when the identifier
    # actually changes (the schema layer's own equality guard covers that one
    # request on its own). Every dependent request is then issued
    # UNCONDITIONALLY: one rewrite per column relation, then, per link relation,
    # the move of its link table and the rewrite of the column inside it. The
    # inert-case behaviour this skeleton reproduces is exactly that -- the
    # dependent requests are still issued when the stored table identifier is
    # unchanged.
    #
    # The two branches issue the SAME dependent requests in the SAME order and
    # differ only in whether the move of the model's own table sits in front, so
    # writing the loops out twice is a proof-tractability device rather than
    # behaviour: it lets every loop invariant carry a CONCRETE offset (1 above,
    # 0 below) instead of the symbolic one the two paths would share, and each
    # branch then closes with the facts its own loops established. Measured: the
    # refutation of clause (1) arrives in 35s this way; no verdict came back at
    # 3600s while one shared pair of loops carried the symbolic offset.
    if before_table != after_table:
        result = [OP_MAIN_MOVE]
        i = 0
        while i < nc:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= i and i <= nc)
            Invariant(len(result) == 1 + i)
            Invariant(result[0] == OP_MAIN_MOVE)
            Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                      result[t] == t - 1)))
            Invariant(MustTerminate(nc - i + 1))
            # invariants-end
            result.append(i)
            i = i + 1
        m = 0
        while m < 2 * nl:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= m and m <= 2 * nl)
            Invariant(len(result) == 1 + nc + m)
            Invariant(result[0] == OP_MAIN_MOVE)
            Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                      result[t] == t - 1)))
            Invariant(MustTerminate(2 * nl - m + 1))
            # invariants-end
            result.append(nc + m)
            m = m + 1
        Assert(len(result) == 1 + nc + 2 * nl)
        Assert(result[0] == OP_MAIN_MOVE)
        Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
               result[t] == t - 1)))
    else:
        i = 0
        while i < nc:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= i and i <= nc)
            Invariant(len(result) == i)
            Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                      result[t] == t)))
            Invariant(MustTerminate(nc - i + 1))
            # invariants-end
            result.append(i)
            i = i + 1
        m = 0
        while m < 2 * nl:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= m and m <= 2 * nl)
            Invariant(len(result) == nc + m)
            Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                      result[t] == t)))
            Invariant(MustTerminate(2 * nl - m + 1))
            # invariants-end
            result.append(nc + m)
            m = m + 1
        Assert(len(result) == nc + 2 * nl)
        Assert(Forall(int, lambda t: Implies(0 <= t and t < len(result),
               result[t] == t)))
    return result
    # impl-end
