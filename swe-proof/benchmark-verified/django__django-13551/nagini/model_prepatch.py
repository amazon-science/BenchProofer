"""Twin-artifact model for django__django-13551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The single-use credential-reset token for an account is derived from a
  fingerprint of the account state that must change whenever the account is
  altered in a way that should retire any outstanding token. The fingerprint
  is the concatenation, in a set order, of:

    1. the account's primary key,
    2. the stored password verifier,
    3. the truncated last-sign-in instant,
    4. the issuing timestamp, and
    5. the account's contact-address value.

  The contact-address value participates in the fingerprint exactly like the
  other components: two accounts that agree on the first four components but
  differ in their contact address MUST produce different fingerprints, so a
  token minted before a contact-address change no longer matches the
  fingerprint computed afterwards. An account need not have a contact address;
  when the address is absent or empty it contributes the empty sequence (and an
  account with no address therefore fingerprints exactly as the historical
  four-component concatenation did).

The components are modelled as `List[int]` sequences of Unicode code points
(Nagini bans `str` indexing); the account is a minimal object exposing only the
five touched components, the contact address being an `Optional[List[int]]`
(absent ~ `None`). The pure sequence theory `PSeq[int]` carries the spec, the
fingerprint being the front-to-back concatenation of the five component
sequences.

No callee is axiomatized: the change is pure concatenation/structure logic over
the account's own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_address(addr: Optional[List[int]]) -> PSeq[int]:
    """The contact-address contribution to the fingerprint: the address itself
    when present and non-empty, otherwise the empty sequence (an absent or
    empty address contributes nothing)."""
    Requires(Implies(addr is not None, Acc(list_pred(addr), 1 / 4)))
    if addr is None:
        return PSeq(0).take(0)
    if len(addr) == 0:
        return PSeq(0).take(0)
    return ToSeq(addr)
# pure-end


class Account:
    def __init__(self) -> None:
        # Terminates: field initialisation is straight-line work, but the four
        # empty containers it builds each carry their own obligation, so this
        # sits at the leaf level above them rather than at 1.
        Requires(MustTerminate(2))
        Ensures(Acc(self.pk) and Acc(list_pred(self.pk)) and len(self.pk) == 0)
        Ensures(Acc(self.password) and Acc(list_pred(self.password)) and len(self.password) == 0)
        Ensures(Acc(self.login_repr) and Acc(list_pred(self.login_repr)) and len(self.login_repr) == 0)
        Ensures(Acc(self.address) and self.address is None)
        self.pk = []  # type: List[int]
        self.password = []  # type: List[int]
        self.login_repr = []  # type: List[int]
        self.address = None  # type: Optional[List[int]]


def make_hash_value(user: Account, timestamp: List[int]) -> List[int]:
    # pre-conditions-start
    # All read-only inputs at fractional permission (directive 5): the
    # fingerprint computation mutates nothing it is given.
    Requires(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Requires(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Requires(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Requires(Acc(user.address, 1 / 2))
    Requires(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Requires(Acc(list_pred(timestamp), 1 / 2))
    # Strictly above the account constructor's own level (2), so a caller may
    # build an account value before invoking this.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
    Ensures(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
    Ensures(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
    Ensures(Acc(user.address, 1 / 2))
    Ensures(Implies(user.address is not None, Acc(list_pred(user.address), 1 / 2)))
    Ensures(Acc(list_pred(timestamp), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The fingerprint is the set-order concatenation of the five components,
    # the contact address last. Because the address contributes its own
    # sequence, two accounts agreeing on the first four components but differing
    # in contact address produce different fingerprints.
    Ensures(ToSeq(Result()) ==
            ToSeq(user.pk) + ToSeq(user.password) + ToSeq(user.login_repr) +
            ToSeq(timestamp) + effective_address(user.address))
    # The contact address contributes faithfully as the trailing segment: what
    # follows the four leading components is exactly the resolved contact address.
    Ensures(ToSeq(Result()).drop(
        len(user.pk) + len(user.password) + len(user.login_repr) + len(timestamp))
        == effective_address(user.address))
    # post-conditions-end
    # impl-start
    # Ghost snapshots of the component sequences, so the loop invariants read
    # only locals (each field's fractional permission is held by the frame).
    pk_s = ToSeq(user.pk)
    pw_s = ToSeq(user.password)
    lr_s = ToSeq(user.login_repr)
    ts_s = ToSeq(timestamp)

    result = []  # type: List[int]
    i = 0
    while i < len(user.pk):
        # invariants-start
        Invariant(Acc(user.pk, 1 / 2) and Acc(list_pred(user.pk), 1 / 2))
        Invariant(pk_s == ToSeq(user.pk))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.pk))
        Invariant(ToSeq(result) == pk_s.take(i))
        Invariant(MustTerminate(len(user.pk) - i + 1))
        # invariants-end
        result.append(user.pk[i])
        i = i + 1
    Assert(pk_s.take(len(user.pk)) == pk_s)

    i = 0
    while i < len(user.password):
        # invariants-start
        Invariant(Acc(user.password, 1 / 2) and Acc(list_pred(user.password), 1 / 2))
        Invariant(pw_s == ToSeq(user.password))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.password))
        Invariant(ToSeq(result) == pk_s + pw_s.take(i))
        Invariant(MustTerminate(len(user.password) - i + 1))
        # invariants-end
        result.append(user.password[i])
        i = i + 1
    Assert(pw_s.take(len(user.password)) == pw_s)

    i = 0
    while i < len(user.login_repr):
        # invariants-start
        Invariant(Acc(user.login_repr, 1 / 2) and Acc(list_pred(user.login_repr), 1 / 2))
        Invariant(lr_s == ToSeq(user.login_repr))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(user.login_repr))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s.take(i))
        Invariant(MustTerminate(len(user.login_repr) - i + 1))
        # invariants-end
        result.append(user.login_repr[i])
        i = i + 1
    Assert(lr_s.take(len(user.login_repr)) == lr_s)

    i = 0
    while i < len(timestamp):
        # invariants-start
        Invariant(Acc(list_pred(timestamp), 1 / 2))
        Invariant(ts_s == ToSeq(timestamp))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(timestamp))
        Invariant(ToSeq(result) == pk_s + pw_s + lr_s + ts_s.take(i))
        Invariant(MustTerminate(len(timestamp) - i + 1))
        # invariants-end
        result.append(timestamp[i])
        i = i + 1
    Assert(ts_s.take(len(timestamp)) == ts_s)

    # Pre-patch (buggy) skeleton: the fingerprint stops after the issuing
    # timestamp and never folds in the contact address, so changing the
    # contact address leaves the fingerprint unchanged.
    return result
    # impl-end
