"""Twin-artifact model for django__django-16560.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A declarative integrity rule carries, alongside its human-readable violation
  message, an optional machine-readable violation classifier (a short code).
  The classifier is supplied when the rule is configured and threads through the
  rule's whole observable surface:

    (1) Configuration. The rule accepts an optional classifier. When a
        classifier is supplied it is retained verbatim; when it is absent the
        rule carries the neutral "no classifier" marker.

    (2) Reporting a violation. When the rule's underlying check reports that the
        data violates the rule, the rule signals a validation failure and the
        classifier carried on that surfaced failure is EXACTLY the rule's own
        classifier (the same marker it was configured with), never the neutral
        marker substituted in regardless. When the check reports no violation,
        the rule signals nothing.

    (3) Identity. Two rules are considered equal only when they agree on every
        configured facet, the classifier included: two rules that differ only in
        their classifier are NOT equal, and two rules that agree on the
        classifier (and everything else) ARE equal.

    (4) Reconstruction keywords. The keyword bundle that reconstructs an
        equivalent rule names the classifier exactly when a classifier is
        present (a non-neutral marker), and omits it when the rule carries the
        neutral marker.

The classifier is modelled as ``Optional[int]`` — a token domain where the null
token is the neutral "no classifier" marker and each distinct non-null token is
a distinct classifier (Nagini bans ``str`` indexing and the discriminating
observable is purely the token identity, not its characters). The rule's
remaining configured payload is one opaque ``int`` (``key``) standing for every
other identity facet. The underlying violation check is an unchanged callee; it
is abstracted by a boolean reporting whether the data violates the rule. The
validation failure is a user-defined exception class (a builtin exception in an
``Exsures`` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class ValidationFailure(Exception):
    """The validation failure a rule signals when its underlying check reports a
    violation. User-defined stand-in for the framework's validation error (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2). The classifier the surfaced failure carries is pinned
    functionally by ``surfaced_violation_code`` (the discriminating value)."""


# axioms-start
# (no @ContractOnly axioms: the unchanged violation check is abstracted as a
# boolean verdict input — see `validate_rule` — and every other touched
# operation is modelled directly, so the proof consumes no axiom.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for these behaviours.)
# pure-end


def configured_code(code: Optional[int]) -> Optional[int]:
    # pre-conditions-start
    # `code` is a plain token input (no heap permission needed):
    #   code is None  -> the neutral "no classifier" marker;
    #   code not None -> the supplied classifier, to be retained verbatim.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) Configuration: the supplied classifier is retained verbatim; an absent
    # classifier (None) is carried as the neutral marker (None).
    Ensures(Result() is code)
    # post-conditions-end
    # impl-start
    return code
    # impl-end


def surfaced_violation_code(rule_code: Optional[int], violated: bool) -> Optional[int]:
    # pre-conditions-start
    # `rule_code` is the rule's configured classifier; `violated` is the
    # unchanged underlying check's verdict (True iff the data violates the rule).
    # Only meaningful when a violation is reported.
    Requires(violated)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # (2) The classifier carried on the surfaced failure is EXACTLY the rule's
    # own classifier — never the neutral marker substituted in regardless.
    Ensures(Result() is rule_code)
    # post-conditions-end
    # impl-start
    # PRE-PATCH: the surfaced failure carries no classifier — the neutral marker
    # is substituted in regardless of the rule's configured classifier.
    return None
    # impl-end


def validate_rule(rule_code: Optional[int], violated: bool) -> None:
    # pre-conditions-start
    # `rule_code` and `violated` are plain inputs (no heap permission needed).
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # (2) No violation reported -> the rule signals nothing (normal return is
    # reachable on EXACTLY the no-violation verdict). A reported violation must
    # raise the validation failure; the classifier that failure carries is the
    # rule's own, pinned by `surfaced_violation_code`'s contract.
    Ensures(not violated)
    Exsures(ValidationFailure, violated)
    # post-conditions-end
    # impl-start
    if violated:
        raise ValidationFailure()
    return
    # impl-end


def constraints_equal(a_key: int, a_code: Optional[int], b_key: int, b_code: Optional[int]) -> bool:
    # pre-conditions-start
    # All four are plain token inputs (no heap permission needed): the rule's
    # opaque identity payload (`*_key`) and its classifier (`*_code`).
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    # (3) Identity: equal iff every configured facet agrees, the classifier
    # included. Two rules differing only in classifier are NOT equal.
    Ensures(Result() == (a_key == b_key and a_code is b_code))
    # post-conditions-end
    # impl-start
    return a_key == b_key and a_code is b_code
    # impl-end


def keyword_bundle_names_code(rule_code: Optional[int]) -> bool:
    # pre-conditions-start
    # `rule_code` is a plain token input (no heap permission needed).
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    # (4) Reconstruction keywords name the classifier EXACTLY when one is
    # present (a non-neutral marker), and omit it for the neutral marker.
    Ensures(Result() == (rule_code is not None))
    # post-conditions-end
    # impl-start
    return rule_code is not None
    # impl-end
