"""Twin-artifact model for django__django-15851.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive database-shell invocation is assembled as an ordered argument
  vector for the client program. The vector is built in three ordered segments:

    (1) a leading segment of connection flags (program name plus any
        user / host / port options), assembled first;
    (2) the caller-supplied extra arguments, passed through verbatim and in
        order;
    (3) the target database name, when one is in effect, as a single trailing
        token.

  The required ordering is segment (1), then (2), then (3): every caller-supplied
  extra argument precedes the database-name token, because the client program
  treats only the arguments that come before the database name as options and
  silently ignores anything that follows it. When no database name is in effect,
  the vector is just segment (1) followed by segment (2).

Argument tokens are modelled as `List[int]` of opaque token identities (Nagini
bans `str` indexing); the specification is carried by `PSeq[int]` via `ToSeq`.
The leading flag segment and the extra arguments are read-only inputs; the
result vector is freshly constructed. There are no axiomatized callees: the
operation is pure list construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled behaviour is pure list construction; no library callee
# is invoked by the changed operation.)
# axioms-end


# pure-start
# (no pure specification helpers needed; ordering is expressed directly with
# PSeq concatenation in the postconditions.)
# pure-end


def build_argv(prefix: List[int], parameters: List[int],
               has_dbname: bool, dbname: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(prefix), 1 / 2))
    Requires(Acc(list_pred(parameters), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(parameters), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the flag segment, then the extra arguments, then the
    # database-name token when one is in effect. Every extra argument precedes
    # the database-name token.
    Ensures(Implies(has_dbname,
                    ToSeq(Result())
                    == ToSeq(prefix) + ToSeq(parameters) + PSeq(dbname)))
    Ensures(Implies(not has_dbname,
                    ToSeq(Result()) == ToSeq(prefix) + ToSeq(parameters)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(prefix):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(prefix))
        Invariant(ToSeq(result) == ToSeq(prefix).take(i))
        Invariant(MustTerminate(len(prefix) - i + 1))
        # invariants-end
        result.append(prefix[i])
        Assert(ToSeq(prefix).take(i) + PSeq(prefix[i]) == ToSeq(prefix).take(i + 1))
        i = i + 1
    Assert(ToSeq(prefix).take(len(prefix)) == ToSeq(prefix))
    # PRE-PATCH BUG: the database-name token is appended BEFORE the extra
    # arguments, so the extras follow the database name and are ignored.
    if has_dbname:
        result.append(dbname)
    j = 0
    while j < len(parameters):
        # invariants-start
        Invariant(Acc(list_pred(prefix), 1 / 2))
        Invariant(Acc(list_pred(parameters), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(parameters))
        Invariant(ToSeq(result)
                  == ToSeq(prefix)
                  + (PSeq(dbname) if has_dbname else PSeq(dbname).take(0))
                  + ToSeq(parameters).take(j))
        Invariant(MustTerminate(len(parameters) - j + 1))
        # invariants-end
        result.append(parameters[j])
        Assert(ToSeq(parameters).take(j) + PSeq(parameters[j])
               == ToSeq(parameters).take(j + 1))
        j = j + 1
    Assert(ToSeq(parameters).take(len(parameters)) == ToSeq(parameters))
    return result
    # impl-end
