"""Twin-artifact model for django__django-12741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database-operations helper exposes a routine that runs a prepared batch of
  flush statements against the database. The database the batch runs against is
  the helper's OWN connection — its identity is taken from the connection the
  helper is bound to, not supplied separately by the caller. Concretely, once
  the routine returns:

    (1) the atomic block it opened was scoped to the helper's own connection:
        the database identifier the block ran under equals the connection's
        own identifier;

    (2) the block's rollback-savepoint behaviour matched the connection's
        declared capability;

    (3) every statement in the supplied batch was executed, in the order given,
        and exactly those statements (no statement dropped, reordered, or
        invented).

The connection is modelled as a minimal class carrying only the touched
facets: its own database identifier, its rollback-savepoint capability flag,
and two observation recorders standing for the effect of the unchanged
callees — the database identifier the opened atomic block ran under, the
savepoint flag it was opened with, and the ordered list of statements that were
executed. The helper is a minimal class holding only that connection.

The two unchanged callees the routine invokes — opening an atomic block scoped
to a database, and executing one statement against the database — are not
themselves changed by the behaviour under specification; their observable
effects (which database the block was scoped to, which statements ran, in what
order) are recorded so the contract can pin them. SQL statements are modelled
as integer identifiers (opaque tokens); the specification is carried by
``PSeq[int]`` via ``ToSeq``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Connection:
    def __init__(self, alias: int, supports_rollback: bool, caller_alias: int) -> None:
        Ensures(Acc(self.alias) and self.alias == alias)                       # type: ignore
        Ensures(Acc(self.supports_rollback) and self.supports_rollback == supports_rollback)  # type: ignore
        Ensures(Acc(self.caller_alias) and self.caller_alias == caller_alias)  # type: ignore
        Ensures(Acc(self.scoped_alias))                                        # type: ignore
        Ensures(Acc(self.scoped_savepoint))                                    # type: ignore
        Ensures(Acc(self.executed) and Acc(list_pred(self.executed)))          # type: ignore
        Ensures(len(self.executed) == 0)                                       # type: ignore
        self.alias = alias                       # the connection's own database identifier
        self.supports_rollback = supports_rollback # declared rollback-savepoint capability
        self.caller_alias = caller_alias         # a database identifier supplied externally (caller-threaded)
        self.scoped_alias = 0                    # recorder: database the atomic block ran under
        self.scoped_savepoint = False            # recorder: savepoint flag the block opened with
        self.executed = []  # type: List[int]    # recorder: statements executed, in order


class DatabaseOperations:
    def __init__(self, connection: Connection) -> None:
        Requires(Acc(connection.alias) and Acc(connection.supports_rollback))
        Requires(Acc(connection.caller_alias))
        Requires(Acc(connection.scoped_alias) and Acc(connection.scoped_savepoint))
        Requires(Acc(connection.executed) and Acc(list_pred(connection.executed)))
        Ensures(Acc(self.connection) and self.connection is connection)        # type: ignore
        self.connection = connection


# axioms-start
# (no @ContractOnly callee axioms are required: the unchanged callees the
# routine invokes are modelled by their observable effects on the recorders,
# validated against the real callees out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def execute_statement_batch(self: DatabaseOperations, sql_list: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(self.connection))
    Requires(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Requires(Acc(self.connection.caller_alias, 1 / 2))
    Requires(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Requires(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Requires(Acc(list_pred(sql_list), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.connection))
    # frame: the routine runs the batch against the helper's OWN connection — the
    # helper's connection identity is unchanged (it is not rebound to a different
    # object). Without this, a fake connection satisfying the recorders below
    # would vacuously discharge the contract.
    Ensures(self.connection is Old(self.connection))
    Ensures(Acc(self.connection.alias, 1 / 2) and Acc(self.connection.supports_rollback, 1 / 2))
    Ensures(Acc(self.connection.caller_alias, 1 / 2))
    Ensures(Acc(self.connection.scoped_alias) and Acc(self.connection.scoped_savepoint))
    Ensures(Acc(self.connection.executed) and Acc(list_pred(self.connection.executed)))
    Ensures(Acc(list_pred(sql_list), 1 / 2))
    # (1) the atomic block was scoped to the helper's OWN connection: the
    # database it ran under is the connection's own identifier — derived
    # internally, never supplied by the caller.
    Ensures(self.connection.scoped_alias == self.connection.alias)
    # (2) the block's savepoint behaviour matched the connection's declared
    # rollback capability.
    Ensures(self.connection.scoped_savepoint == self.connection.supports_rollback)
    # (3) exactly the supplied batch ran, in order: the recorded execution list
    # equals the input batch element-wise.
    Ensures(ToSeq(self.connection.executed) == ToSeq(sql_list))
    # post-conditions-end
    # impl-start
    # PRE-PATCH: the database the atomic block runs under is taken from a value
    # supplied separately (the caller-threaded alias) rather than derived from
    # the helper's own connection. It is not guaranteed to be the connection's
    # own identifier, so clause (1) does not hold.
    self.connection.scoped_alias = self.connection.caller_alias
    self.connection.scoped_savepoint = self.connection.supports_rollback
    executed = []  # type: List[int]
    i = 0
    while i < len(sql_list):
        # invariants-start
        Invariant(Acc(list_pred(sql_list), 1 / 2))
        Invariant(Acc(list_pred(executed)))
        Invariant(0 <= i and i <= len(sql_list))
        Invariant(ToSeq(executed) == ToSeq(sql_list).take(i))
        Invariant(MustTerminate(len(sql_list) - i + 1))
        # invariants-end
        executed.append(sql_list[i])
        i = i + 1
    self.connection.executed = executed
    # impl-end
