"""Twin-artifact model for django__django-13406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lazy result set carries a *row producer* that decides what shape each
  fetched row takes: either a full model instance, or a plain value mapping
  (one entry per selected value-field). A separately-built lookup description
  may be attached to a freshly-created result set. When such a lookup
  description is attached, the result set's row producer must agree with the
  KIND of lookup the description encodes:

    * if the description selects an explicit set of value-fields (it carries a
      non-empty value-field selection), the result set must produce value
      mappings — NOT model instances — once the description is attached;

    * if the description selects no value-fields, the result set keeps whatever
      row producer it already had.

  Attaching the description also stores it as the result set's active lookup
  description. The pinned observable: a freshly-created result set, which by
  default would produce model instances, must switch to producing value
  mappings exactly when the attached description carries a value-field
  selection — otherwise the fetched value rows are wrongly wrapped as model
  instances.

The lookup description is modelled as a minimal class carrying only the one
touched, read-only field: the count of selected value-fields (an ``int`` >= 0;
a non-empty selection <-> count > 0). The result set is modelled as a minimal
class carrying the two touched fields: an integer *row-producer tag*
(0 = produces model instances, 1 = produces value mappings) and the attached
lookup description (an ``Optional[LookupDescription]`` reference). No callee is
axiomatized: the attachment is a conditional attribute update over those tags.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# row-producer tags
PRODUCES_MODEL_INSTANCES = 0   # default producer (full model instances)
PRODUCES_VALUE_MAPPINGS = 1    # producer that yields one value mapping per row


class LookupDescription:
    def __init__(self, values_field_count: int) -> None:
        Requires(values_field_count >= 0)
        # level 2 < attach_description's 6: leaves room beneath the caller, so a
        # caller holding an obligation can construct a description.
        Requires(MustTerminate(2))
        Ensures(Acc(self.value_field_count) and self.value_field_count == values_field_count)  # type: ignore
        self.value_field_count = values_field_count


class ResultSet:
    def __init__(self, producer_tag: int) -> None:
        # level 2 < attach_description's 6 (see LookupDescription.__init__).
        Requires(MustTerminate(2))
        Ensures(Acc(self.producer_tag) and self.producer_tag == producer_tag)  # type: ignore
        Ensures(Acc(self.description) and self.description is None)  # type: ignore
        self.producer_tag = producer_tag
        self.description = None  # type: Optional[LookupDescription]


# axioms-start
# (no callee is axiomatized: the attachment is a conditional attribute update
# over integer producer tags and the description's value-field count.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def attach_description(rs: ResultSet, value: LookupDescription) -> None:
    # pre-conditions-start
    Requires(Acc(rs.producer_tag))
    Requires(Acc(rs.description))
    # the attached description is read, never mutated -> fractional permission.
    Requires(Acc(value.value_field_count, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rs.producer_tag))
    Ensures(Acc(rs.description))
    Ensures(Acc(value.value_field_count, 1 / 2))
    # the description is now the result set's active lookup description.
    Ensures(rs.description is value)
    # the description carrying a value-field selection forces the value-mapping
    # producer; the count is read-only across the call.
    Ensures(value.value_field_count == Old(value.value_field_count))
    Ensures(Implies(value.value_field_count > 0,
                    rs.producer_tag == PRODUCES_VALUE_MAPPINGS))
    # no value-field selection -> the existing row producer is preserved.
    Ensures(Implies(value.value_field_count == 0,
                    rs.producer_tag == Old(rs.producer_tag)))
    # post-conditions-end
    # impl-start
    if value.value_field_count > 0:
        rs.producer_tag = PRODUCES_VALUE_MAPPINGS
    rs.description = value
    # impl-end
