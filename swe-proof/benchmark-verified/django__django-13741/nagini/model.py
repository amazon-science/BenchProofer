"""Twin-artifact model for django__django-13741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A specialised form field that merely DISPLAYS a stored value (it renders
      no editable control) must, when constructed without the caller naming the
      two presentation flags, come into existence already marked as
      non-editable: such a field is optional (not required) AND is flagged as
      not user-editable by default. A caller that explicitly names either flag
      keeps the value it chose; only an unset flag falls back to the default.

  (2) The generic "did the submitted value differ from the stored value?"
      decision a field reports is short-circuited for a field flagged
      non-editable: such a field NEVER reports a change, because its submitted
      value is always ignored in favour of the stored value. For an editable
      field the decision is the ordinary inequality of the stored and submitted
      values, where an absent value (None) is indistinguishable from the empty
      value.

The field is modelled as a minimal class carrying only the two touched flags
(`required`, `disabled`). Caller-supplied keyword values are modelled as
`Optional[bool]` where `None` means "the caller did not name this flag" (so the
default applies). Text values are modelled as `Optional[List[int]]` of Unicode
code points (None = absent), since Nagini bans `str` indexing.

The generic field constructor's flag storage and the generic change decision's
non-editable short-circuit are unchanged base behaviours, modelled deeply (the
flags are stored verbatim; the short-circuit is spelled out) and validated
== the real base field by axiom_check.py (G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Field:
    def __init__(self, required: bool, disabled: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.required) and self.required == required)    # type: ignore
        Ensures(Acc(self.disabled) and self.disabled == disabled)    # type: ignore
        self.required = required
        self.disabled = disabled


# axioms-start
# (No @ContractOnly axioms are consumed: the base field's flag storage and the
#  base change-decision short-circuit are modelled deeply below and validated
#  against the real base field out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def norm_seq(v: Optional[List[int]]) -> PSeq[int]:
    """Normalised value content: an absent value (None) is indistinguishable
    from the empty value, so both map to the empty sequence; otherwise the
    value's own code-point sequence."""
    Requires(Implies(v is not None, Acc(list_pred(v), 1 / 4)))
    if v is None:
        return PSeq(0).take(0)
    return ToSeq(v)
# pure-end


def make_field(required_kw: Optional[bool], disabled_kw: Optional[bool]) -> Field:
    # pre-conditions-start
    # No permission obligations on the Optional[bool] keyword carriers.
    # The constructed field must actually be delivered: this termination
    # obligation forbids implementations that satisfy the flag postconditions
    # only vacuously by never returning (flag selection is bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().required) and Acc(Result().disabled))
    # An unnamed flag falls back to the field's own default; a named flag keeps
    # the caller's value. Defaults: not-required, and not-editable.
    Ensures(Implies(required_kw is None, Result().required == False))
    Ensures(Implies(required_kw is not None, Result().required == required_kw))
    Ensures(Implies(disabled_kw is None, Result().disabled == True))
    Ensures(Implies(disabled_kw is not None, Result().disabled == disabled_kw))
    # post-conditions-end
    # impl-start
    if required_kw is None:
        required = False
    else:
        required = required_kw
    if disabled_kw is None:
        disabled = True
    else:
        disabled = disabled_kw
    return Field(required, disabled)
    # impl-end


def differs(self: Field, initial: Optional[List[int]], data: Optional[List[int]]) -> bool:
    # pre-conditions-start
    Requires(Acc(self.disabled, 1 / 2))
    Requires(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Requires(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # The change decision must actually be delivered: this termination
    # obligation forbids implementations that satisfy either branch's value
    # postcondition only vacuously by never returning (both the short-circuit
    # and the normalised comparison are bounded work).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.disabled, 1 / 2))
    Ensures(Implies(initial is not None, Acc(list_pred(initial), 1 / 2)))
    Ensures(Implies(data is not None, Acc(list_pred(data), 1 / 2)))
    # A non-editable field NEVER reports a change (its submitted value is
    # ignored in favour of the stored value).
    Ensures(Implies(self.disabled, Result() == False))
    # An editable field reports a change exactly when the stored and submitted
    # values differ, treating an absent value (None) as the empty value.
    Ensures(Implies(not self.disabled, Result() == (norm_seq(initial) != norm_seq(data))))
    # post-conditions-end
    # impl-start
    if self.disabled:
        return False
    return norm_seq(initial) != norm_seq(data)
    # impl-end
