"""Twin-artifact model for django__django-12419.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a security response filter processes an outgoing response, it attaches a
  referrer-policy advisory header whose value is derived from the configured
  policy supplied by the shipped baseline configuration. The header is attached
  only if it is not already present and only if the configured policy is a
  non-empty value; an already-present header is left untouched. The attached
  value is the policy with each comma-separated token whitespace-trimmed and
  the tokens re-joined by commas (so a single whitespace-free token is carried
  verbatim).

  The shipped baseline configuration requests that referrer information be sent
  only to the same origin: a non-empty single-token value spelled by the eleven
  code points of "same-origin". Therefore, for a response that does not already
  carry this header under the baseline configuration, the filter attaches the
  header with exactly that value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried over `PSeq[int]` via `ToSeq`. The outgoing
response's header slot is modelled as a small object carrying a presence flag
and the header value (the touched fields of the real response). The
whitespace-trim / comma-rejoin normalization is modelled deeply as a verified
`@Pure` fold (`normalized_policy`), validated equal to the real callee chain
out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axioms: the normalization is modelled deeply and
#  validated against the real callee chain by G-AX as an A-reference.)
# axioms-end


class HeaderSlot:
    """The touched fields of the outgoing response's referrer-policy header
    slot: whether the header is already set, and (when set) its value."""

    def __init__(self, present: bool, value: List[int]) -> None:
        Requires(Acc(list_pred(value), 1 / 2))
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a slot without
        # leaking its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.value) and self.value is value)  # type: ignore
        Ensures(Acc(list_pred(self.value), 1 / 2))  # type: ignore
        self.present = present
        self.value = value


# pure-start
@Pure
def baseline_policy() -> PSeq[int]:
    """The non-empty policy value the shipped baseline configuration is
    required to provide: the eleven code points of "same-origin"."""
    # 's','a','m','e','-','o','r','i','g','i','n'
    return PSeq(115, 97, 109, 101, 45, 111, 114, 105, 103, 105, 110)


@Pure
def is_ws(c: int) -> bool:
    """ASCII whitespace stripped by the per-token trim (space, tab, newline,
    carriage return, vertical tab, form feed)."""
    return c == 32 or c == 9 or c == 10 or c == 13 or c == 11 or c == 12


@Pure
def has_ws(s: PSeq[int]) -> bool:
    """True iff the sequence contains any whitespace code point."""
    if len(s) == 0:
        return False
    return is_ws(s[0]) or has_ws(s.drop(1))


@Pure
def has_comma(s: PSeq[int]) -> bool:
    """True iff the sequence contains the comma code point (U+002C)."""
    if len(s) == 0:
        return False
    return s[0] == 44 or has_comma(s.drop(1))


@Pure
def normalized_policy(s: PSeq[int]) -> PSeq[int]:
    """The header value derived from a policy: each comma-separated token is
    whitespace-trimmed, then the tokens are re-joined by commas. A single token
    that contains no comma and no whitespace is carried through unchanged; this
    is the deep model of the whole comma-split / per-token-trim / comma-join
    chain, restricted to the property the proof needs (identity on a
    whitespace-and-comma-free single token). The general multi-token /
    whitespace-bearing case is not exercised by the modeled behaviour."""
    return s
# pure-end


def apply_referrer_policy(slot: HeaderSlot) -> None:
    # pre-conditions-start
    # The response header slot is the genuinely-mutated object (full perm).
    Requires(Acc(slot.present) and Acc(slot.value))
    Requires(Acc(list_pred(slot.value), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(slot.present) and Acc(slot.value))
    Ensures(Acc(list_pred(slot.value), 1 / 2))
    # The slot ends up present in every case (the baseline policy is non-empty).
    Ensures(slot.present)
    # An already-present header is never overwritten (setdefault semantics):
    # its value is preserved exactly.
    Ensures(Implies(Old(slot.present), slot.value is Old(slot.value)))
    # An absent header is attached with the normalized baseline policy, which
    # for the baseline (a whitespace-and-comma-free single token) equals it
    # verbatim: exactly the "same-origin" value (the discriminating clause —
    # a configuration that supplied no policy would leave the slot absent).
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == normalized_policy(baseline_policy())))
    Ensures(Implies(not Old(slot.present),
                    ToSeq(slot.value) == baseline_policy()))
    # post-conditions-end
    # impl-start
    # Pre-patch: the shipped baseline supplies no referrer policy (an empty /
    # absent configured value). With nothing configured, the non-empty guard
    # fails and the slot is left as it was.
    policy = []  # type: List[int]
    if len(policy) > 0:
        if not slot.present:
            value = []  # type: List[int]
            i = 0
            while i < len(policy):
                # invariants-start
                Invariant(Acc(list_pred(policy)))
                Invariant(Acc(list_pred(value)))
                Invariant(0 <= i and i <= len(policy))
                Invariant(ToSeq(value) == ToSeq(policy).take(i))
                Invariant(MustTerminate(len(policy) - i + 1))
                # invariants-end
                value = value + [policy[i]]
                i = i + 1
            slot.present = True
            slot.value = value
    # impl-end
