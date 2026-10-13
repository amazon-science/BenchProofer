"""Twin-artifact model for sphinx-doc__sphinx-9320.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an interactive project initializer discovers that the chosen root
  directory already holds a project configuration file, it re-prompts the
  operator for a fresh root directory and tells them that pressing Enter (an
  EMPTY response) will abandon the operation. For that abort affordance to
  work, the validator attached to the re-prompt must treat an EMPTY response
  as acceptable and hand it straight back: an empty response validates to the
  empty string WITHOUT signalling a validation error. A NON-EMPTY response is
  still held to the ordinary requirement that it name an existing directory
  (an absent directory is rejected with a validation error).

  Both validators resolve an accepted response before handing it on: the value
  they return is the response with its home prefix expanded, which is what the
  directory test is applied to. Expanding an empty response leaves it empty, so
  the abort affordance is unaffected by that resolution.

  The consuming loop then aborts the operation exactly when the validated
  response is empty: an empty validated response terminates the program, a
  non-empty one (a real existing directory) is accepted and the loop carries
  on. So pressing Enter at the re-prompt abandons the operation.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
directory-existence test and home-prefix expansion are unchanged filesystem
callees, axiomatized at their weakest relied-on behaviour: the empty path is
never an existing directory, and expanding the home prefix leaves the empty
path empty. Expansion is axiomatized twice over the same callee — once as a
pure sequence function for the specification, once as a value-producing face an
implementation can hold (a `PSeq` cannot be materialized as a `List`) — with the
second tied to the first. A validation rejection is modelled as a user-defined
exception via `Exsures` (builtin-exception `Exsures` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ValidationRejected(Exception):
    """A response was rejected by a prompt validator (the operator must retry).
    Models the initializer's own validation-error signal."""


# axioms-start
@Pure
@ContractOnly
def expand_home(x: PSeq[int]) -> PSeq[int]:
    """Home-prefix expansion of a path (unchanged filesystem callee). Weakest
    relied-on fact: expanding the EMPTY path yields the empty path (there is no
    home prefix to expand). Provenance + executable check: mapping.md /
    axiom_check.py."""
    Requires(True)
    Ensures(Implies(len(x) == 0, len(Result()) == 0))


@ContractOnly
def expand_home_value(x: List[int]) -> List[int]:
    """Home-prefix expansion applied to a response, yielding a value the caller
    can hold. Same unchanged filesystem callee as `expand_home`, whose result it
    is tied to; this face exists because a `PSeq` cannot be materialized as a
    `List` inside an implementation. Provenance: mapping.md / axiom_check.py."""
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(x) == Old(ToSeq(x)))
    Ensures(ToSeq(Result()) == expand_home(ToSeq(x)))


@Pure
@ContractOnly
def path_is_dir(x: PSeq[int]) -> bool:
    """Directory-existence test (unchanged filesystem callee). Weakest
    relied-on fact: the EMPTY path is never an existing directory. Provenance
    + executable check: mapping.md / axiom_check.py."""
    Requires(True)
    Ensures(Implies(len(x) == 0, Result() == False))
# axioms-end


# pure-start
@Pure
def is_empty(x: PSeq[int]) -> bool:
    """An empty (just-Enter) response carries no code points."""
    return len(x) == 0
# pure-end


def validate_strict(x: List[int]) -> List[int]:
    # The ordinary path validator: a response must name an existing directory
    # (after home-prefix expansion) or it is rejected. (The UNCHANGED validator
    # the re-prompt validator delegates to for non-empty responses.)
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A response that does not name an existing directory is rejected.
    Ensures(path_is_dir(expand_home(ToSeq(x))))
    # An accepted response validates to its home-prefix-expanded form.
    Ensures(ToSeq(Result()) == expand_home(ToSeq(x)))
    # An empty response is never accepted here (it is not an existing dir).
    # A rejection is permitted ONLY when the (expanded) response is NOT an
    # existing directory: a response naming an existing directory MUST be
    # accepted (returned), never rejected. The rejected response is unchanged.
    Exsures(ValidationRejected, Acc(list_pred(x), 1 / 2) and ToSeq(x) == Old(ToSeq(x)) and
            not path_is_dir(expand_home(ToSeq(x))))
    # post-conditions-end
    # impl-start
    expanded = expand_home_value(x)
    if not path_is_dir(ToSeq(expanded)):
        raise ValidationRejected()
    return expanded
    # impl-end


def validate_path_allowing_empty(x: List[int]) -> List[int]:
    # The re-prompt validator: an EMPTY response is accepted as-is (so pressing
    # Enter abandons the operation); any other response is held to the ordinary
    # existing-directory requirement.
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # An empty response validates to the empty string WITHOUT raising: this is
    # the abort affordance the issue demands.
    Ensures(is_empty(ToSeq(x)) == (len(Result()) == 0))
    # The validated value is the response's home-prefix-expanded form (for an
    # empty response that expansion is the empty response itself).
    Ensures(ToSeq(Result()) == expand_home(ToSeq(x)))
    # A rejection is possible only for a NON-EMPTY response.
    Exsures(ValidationRejected, Acc(list_pred(x), 1 / 2) and len(x) > 0)
    # post-conditions-end
    # impl-start
    if len(x) == 0:
        result = list(x)  # type: List[int]
        return result
    return validate_strict(x)
    # impl-end


def abort_on_empty_reprompt(x: List[int]) -> bool:
    # The consuming loop body's decision: after the re-prompt validator returns
    # a value, the operation is abandoned exactly when that value is empty.
    # Returns True iff the operation aborts on this response.
    # pre-conditions-start
    Requires(Acc(list_pred(x), 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x), 1 / 2))
    # The operation aborts exactly when the (empty) response was accepted: the
    # validator hands an empty value back and the loop exits. A non-empty,
    # existing-directory response is accepted and the loop continues.
    Ensures(Result() == is_empty(ToSeq(x)))
    Exsures(ValidationRejected, Acc(list_pred(x), 1 / 2) and len(x) > 0)
    # post-conditions-end
    # impl-start
    validated = validate_path_allowing_empty(x)
    aborts = len(validated) == 0
    return aborts
    # impl-end
