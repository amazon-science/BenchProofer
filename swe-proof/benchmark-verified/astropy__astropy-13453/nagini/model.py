"""Twin-artifact model for astropy__astropy-13453.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular writer prepares a list of output columns for rendering. The caller
  may supply a per-name formatting mapping: a dictionary from a column's name to
  the format specification that column should be rendered with. The preparation
  step resolves, for every output column, the format specification that will
  govern how that column's values are turned into text:

    * if the column's name appears as a key in the supplied mapping, the
      resolved format for that column is the value the mapping records for that
      name;
    * otherwise the column keeps the format specification it already carried.

  The consequence that matters: when a column's name is present in the supplied
  mapping, the rendered values of that column must honour the supplied
  specification rather than the column's pre-existing one. A column whose name
  is absent from the mapping is left untouched.

Modelling choices (Nagini fragment):
  * Column names are `int` keys (opaque identity tokens); format
    specifications are `int` tokens (opaque identity of a format spec). The
    tested behaviour only observes WHICH spec each column ends up bound to, so
    integer identity is the faithful carrier (mapping.md §2).
  * The set of output columns is two parallel `List[int]`: `names[i]` and the
    pre-existing `prior_formats[i]` of column `i`.
  * The supplied mapping is a `Dict[int, int]` from name to format token.
  * The result is a `List[int]`: the resolved format token of each column,
    index-aligned with the inputs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Dict
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The format-resolution logic is the behaviour under
# specification and is modelled deeply (resolved_format / the loop). The
# per-name dictionary membership/lookup it composes is ordinary mapping
# semantics, validated against real Python semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def resolved_format(name: int, prior: int, formats: Dict[int, int]) -> int:
    """The format token column `name` ends up bound to.

    `prior` is the format specification the column already carried. If the
    supplied mapping records the column's name, the recorded value is used;
    otherwise the prior specification is kept.
    """
    Requires(Acc(dict_pred(formats), 1 / 4))
    if name in formats:
        return formats[name]
    return prior
# pure-end


def resolve_column_formats(names: List[int], prior_formats: List[int],
                           formats: Dict[int, int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(prior_formats), 1 / 2))
    Requires(Acc(dict_pred(formats), 1 / 2))
    # The two parallel column arrays are index-aligned.
    Requires(len(names) == len(prior_formats))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(prior_formats), 1 / 2))
    Ensures(Acc(dict_pred(formats), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is one resolved format token per column, in order.
    Ensures(len(Result()) == len(names))
    # Element i is the resolved format of column i: the supplied mapping's
    # value when the column's name is present, the prior format otherwise.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats),
        Result()[i] == resolved_format(names[i], prior_formats[i], formats)))))
    # The discriminating behaviour: a column whose name is in the mapping is
    # bound to exactly the supplied specification ...
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and (names[i] in formats),
        Result()[i] == formats[names[i]]))))
    # ... and a column whose name is absent keeps its prior specification.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names)
        and i < len(prior_formats) and not (names[i] in formats),
        Result()[i] == prior_formats[i]))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(prior_formats), 1 / 2))
        Invariant(Acc(dict_pred(formats), 1 / 2))
        Invariant(len(names) == len(prior_formats))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(names))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i
            and k < len(prior_formats),
            result[k] == resolved_format(names[k], prior_formats[k], formats)))))
        # invariants-end
        name = names[i]
        if name in formats:
            result.append(formats[name])
        else:
            result.append(prior_formats[i])
        i = i + 1
    return result
    # impl-end
