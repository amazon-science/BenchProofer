"""Twin-artifact model for django__django-14376.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a client invocation is assembled for a MySQL-style command line, the
  database name to pass is selected from a connection-options mapping with a
  THREE-LEVEL precedence:

    (1) the value under the non-deprecated database-name option, when that
        option is present in the mapping;
    (2) otherwise the value under the deprecated, legacy database-name option,
        when present;
    (3) otherwise the database name configured in the top-level settings.

  The non-deprecated option therefore takes precedence over the legacy option,
  which in turn takes precedence over the settings-level name. The selected
  name is then appended to the command-line argument list as a trailing
  positional argument, but only when it is non-empty; an empty selected name
  contributes no trailing argument.

Modelling choices (Nagini fragment):
  * Database-name strings are modelled as ``List[int]`` of Unicode code points
    (Nagini bans ``str`` indexing); the specification is carried by
    ``PSeq[int]`` via ``ToSeq``. Only equality of the carried character content
    is observed.
  * "Option present in the connection-options mapping" is modelled by an
    ``Optional[List[int]]``: ``None`` means the key is absent (so the lookup
    falls through to the next precedence level); a present value is the value
    stored under that key. This mirrors ``mapping.get(key, fallback)``
    (mapping.md §2).
  * "Non-empty selected name" is the truthiness test on the selected string,
    modelled as a non-empty code-point sequence; ``appended`` reports whether
    the selected name became a trailing positional argument.

The connection-options values and the settings-level name are read-only inputs
(the operation selects among them); they are held at fractional permission. The
selection and the append decision are modelled deeply (spelled out in the impl
region); there is no axiomatised callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the precedence selection and the trailing-argument decision are the
# behaviour under specification and are spelled out deeply in the impl region.
# There is no unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def select_name(opt_primary: Optional[List[int]],
                opt_legacy: Optional[List[int]],
                settings_name: PSeq[int]) -> PSeq[int]:
    """The selected database name as a pure sequence, under the three-level
    precedence: the non-deprecated option's value when present, otherwise the
    legacy option's value when present, otherwise the settings-level name.

    A present option contributes its value regardless of whether that value is
    empty (mirrors ``mapping.get(key, fallback)``: a present key short-circuits
    the fallback even when its stored value is the empty string)."""
    Requires(Implies(opt_primary is not None, Acc(list_pred(opt_primary), 1 / 8)))
    Requires(Implies(opt_legacy is not None, Acc(list_pred(opt_legacy), 1 / 8)))
    if opt_primary is not None:
        return ToSeq(opt_primary)
    if opt_legacy is not None:
        return ToSeq(opt_legacy)
    return settings_name
# pure-end


def resolve_db_arg(opt_database: Optional[List[int]],
                   opt_db: Optional[List[int]],
                   settings_name: List[int]) -> Tuple[bool, List[int]]:
    # pre-conditions-start
    # The candidate database names are read-only inputs (selected among, never
    # mutated): fractional permission, required AND ensured.
    Requires(Implies(opt_database is not None, Acc(list_pred(opt_database), 1 / 2)))
    Requires(Implies(opt_db is not None, Acc(list_pred(opt_db), 1 / 2)))
    Requires(Acc(list_pred(settings_name), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(opt_database is not None, Acc(list_pred(opt_database), 1 / 2)))
    Ensures(Implies(opt_db is not None, Acc(list_pred(opt_db), 1 / 2)))
    Ensures(Acc(list_pred(settings_name), 1 / 2))
    Ensures(Acc(list_pred(Result()[1])))
    # The selected name (the returned sequence) follows the three-level
    # precedence: non-deprecated option > legacy option > settings-level name.
    Ensures(ToSeq(Result()[1]) == select_name(opt_database, opt_db, ToSeq(settings_name)))
    # It becomes a trailing positional argument exactly when it is non-empty.
    Ensures(Result()[0] == (len(select_name(opt_database, opt_db, ToSeq(settings_name))) > 0))
    Ensures(Result()[0] == (len(Result()[1]) > 0))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the legacy option is consulted first and the
    # non-deprecated option is never examined, so a present non-deprecated
    # option does NOT take precedence.
    if opt_db is not None:
        chosen = opt_db  # type: List[int]
    else:
        chosen = settings_name
    # Materialise the selected name as a freshly-owned argument value (the
    # trailing positional argument carries the selected name's content).
    database = []  # type: List[int]
    i = 0
    while i < len(chosen):
        # invariants-start
        Invariant(Implies(opt_database is not None, Acc(list_pred(opt_database), 1 / 2)))
        Invariant(Implies(opt_db is not None, Acc(list_pred(opt_db), 1 / 2)))
        Invariant(Acc(list_pred(settings_name), 1 / 2))
        Invariant(chosen is opt_database or chosen is opt_db or chosen is settings_name)
        Invariant(Implies(opt_database is not None, chosen is not opt_database or
                          ToSeq(chosen) == ToSeq(opt_database)))
        Invariant(Acc(list_pred(database)))
        Invariant(0 <= i and i <= len(chosen))
        Invariant(ToSeq(database) == ToSeq(chosen).take(i))
        Invariant(MustTerminate(len(chosen) - i + 1))
        # invariants-end
        database.append(chosen[i])
        i = i + 1
    Assert(ToSeq(chosen).take(len(chosen)) == ToSeq(chosen))
    appended = len(database) > 0
    return appended, database
    # impl-end
