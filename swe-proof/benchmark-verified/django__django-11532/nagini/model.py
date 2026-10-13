"""Twin-artifact model for django__django-11532.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A reusable transform takes a domain label and returns its ASCII-Compatible
      Encoding (ACE): the standard internationalised-domain ToASCII form. Its
      defining observable property is that, whenever it answers a label with a
      value, that value consists ENTIRELY of ASCII code points (every code point
      is strictly below 128) — even when the input label contains non-ASCII code
      points. A purely-ASCII label is returned in ASCII form unchanged in
      content. The concrete content is the standard ACE of the label (e.g. a
      label of the two code points U+6F22 U+5B57 yields the eleven ASCII code
      points spelling ``xn--p8s937b``).

      Not every label has an ACE: the standard form constrains the shape of a
      label. The transform accepts such a label as input all the same, and the
      specified behaviour on it is that it yields NO value — it signals that
      condition to its caller out of band, leaving the label as it found it, so
      the caller can observe the condition and decide what to do. Equivalently,
      the two outcomes are complementary and neither is at the transform's
      discretion: a value comes back exactly for the labels that have an ACE, and
      a label that has none is never answered with a substitute value of the
      transform's own choosing.

  (2) The cached host name used to stamp outgoing messages is the ACE of the
      host name reported by the platform. Because that platform-reported name
      may contain non-ASCII code points, the cached value is obtained by passing
      it through the ACE transform of (1). The defining observable property is
      therefore that the cached host name is ALWAYS an all-ASCII sequence,
      regardless of whether the platform's name was ASCII — so it can be placed
      verbatim into a header that is later serialised under a single-byte
      (non-Unicode) charset without provoking an encoding failure.

      The platform-reported name is handed to the transform exactly as reported,
      so the transform's out-of-band condition reaches the caller of the cached
      host name unaltered: a platform name that has no ACE yields no cached
      value, rather than some stand-in name being cached in its place.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by ``PSeq[int]`` via ``ToSeq``.
The ACE transform itself is a standard library callee the new code CALLS but
does not change; it is axiomatized (its all-ASCII guarantee, a concrete witness,
and the out-of-band condition that is the exact complement of its value-yielding
domain), with its soundness checked out-of-band by axiom_check.py (G-AX). The
all-ASCII predicate is modelled deeply (a front-recursive fold) and the cached
host name is the verified composition of the platform name with that transform.
The out-of-band condition is carried by a user-defined exception, because a
builtin exception in an ``Exsures`` crashes the Nagini translator.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class LabelNotEncodable(Exception):
    """The out-of-band condition of the ACE transform: the label handed to it
    has no ASCII-Compatible Encoding, so the transform has no value to answer
    with and reports the condition to its caller instead. A user-defined
    exception because a builtin exception in an ``Exsures`` crashes the Nagini
    translator."""


# axioms-start
@Pure
@ContractOnly
def valid_label(domain: PSeq[int]) -> bool:
    """Whether a domain label HAS an ASCII-Compatible Encoding under the standard
    ToASCII operation's label-shape rules. This is the
    CHARACTERISTIC predicate of the transform's value-yielding domain: the
    transform answers with a value on exactly these labels and signals its
    out-of-band condition on exactly the others, so the two outcomes are
    complementary by construction rather than by choice. Unchanged callee;
    provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(Implies(domain == seq_host_witness(), Result()))


@Pure
@ContractOnly
def ace_seq(domain: PSeq[int]) -> PSeq[int]:
    """The ASCII-Compatible-Encoding (ToASCII) value of a domain label that has
    one, as a pure sequence of code points. Its defining property is that the
    result is ENTIRELY ASCII (every code point < 128). A concrete witness pins
    the standard ACE of one non-ASCII label. Unchanged standard internationalised
    -domain ToASCII codec; provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Requires(valid_label(domain))
    # The ACE of a label that has one is all-ASCII (a label that is not fully
    # ASCII-representable has no ACE at all) — the property the proof consumes.
    Ensures(all_ascii(Result()))
    # Concrete witness: the standard ACE of the non-ASCII label U+6F22 U+5B57.
    Ensures(Implies(domain == seq_host_witness(), Result() == seq_ace_witness()))


@ContractOnly
def ace_encode(domain: List[int]) -> List[int]:
    """The impl-callable face of the ACE transform, defined on EVERY label: on a
    label that has an ACE it answers with a freshly-built ASCII code-point list
    equal to ``ace_seq`` of the input; on a label that has none it answers with
    no value at all and signals the out-of-band condition instead, leaving the
    label as it found it. Unchanged standard internationalised-domain ToASCII
    codec."""
    Requires(Acc(list_pred(domain), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(domain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value comes back ONLY for a label that has an ACE ...
    Ensures(valid_label(ToSeq(domain)))
    Ensures(ToSeq(Result()) == ace_seq(ToSeq(domain)))
    # ... and a label that has none is reported out of band instead, never
    # answered with a substitute value, with the label left as it was.
    Exsures(LabelNotEncodable,
            Acc(list_pred(domain), 1 / 2)
            and ToSeq(domain) == Old(ToSeq(domain))
            and not valid_label(ToSeq(domain)))
# axioms-end


# pure-start
@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is an ASCII code point (< 128).
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return s[0] < 128 and all_ascii(s.drop(1))


@Pure
def seq_host_witness() -> PSeq[int]:
    """The non-ASCII domain label of the worked witness (code points
    U+6F22 U+5B57)."""
    return PSeq(28450, 23383)


@Pure
def seq_ace_witness() -> PSeq[int]:
    """The standard ACE of seq_host_witness(): the eleven ASCII code points
    spelling ``xn--p8s937b``."""
    return PSeq(120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98)
# pure-end


def ascii_compatible_domain(domain: List[int]) -> List[int]:
    # pre-conditions-start
    # ``domain`` is read-only (fractional permission, directive 5). ANY label is
    # admissible input, including one that has no ACE: reporting that condition
    # out of band is part of the specified behaviour, not an excluded case.
    Requires(Acc(list_pred(domain), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(domain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value is returned ONLY for a label that HAS an ACE: a label that has none
    # is never answered with a substitute value of the transform's own choosing.
    Ensures(valid_label(ToSeq(domain)))
    # The result is the ACE of the input label ...
    Ensures(ToSeq(Result()) == ace_seq(ToSeq(domain)))
    # ... and is therefore an all-ASCII sequence (the defining property).
    Ensures(all_ascii(ToSeq(Result())))
    # A label with no ACE reaches the caller as the out-of-band condition, with
    # the label left as it was, so the caller can observe and handle it.
    Exsures(LabelNotEncodable,
            Acc(list_pred(domain), 1 / 2)
            and ToSeq(domain) == Old(ToSeq(domain))
            and not valid_label(ToSeq(domain)))
    # post-conditions-end
    # impl-start
    return ace_encode(domain)
    # impl-end


def cached_host_name(platform_name: List[int]) -> List[int]:
    # pre-conditions-start
    # ``platform_name`` is the host name reported by the platform: read-only, and
    # unrestricted — it may be non-ASCII, and it may be a label that has no ACE.
    Requires(Acc(list_pred(platform_name), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(platform_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A cached value exists ONLY for a platform name that HAS an ACE: no stand-in
    # host name is ever cached in place of one that has none.
    Ensures(valid_label(ToSeq(platform_name)))
    # The cached host name is the ACE of the platform name ...
    Ensures(ToSeq(Result()) == ace_seq(ToSeq(platform_name)))
    # ... and is ALWAYS all-ASCII even when the platform name was not (the
    # property an outgoing single-byte-charset header depends on).
    Ensures(all_ascii(ToSeq(Result())))
    # A platform name with no ACE yields no cached value: the transform's
    # out-of-band condition reaches this function's caller unaltered, with the
    # reported name left as it was.
    Exsures(LabelNotEncodable,
            Acc(list_pred(platform_name), 1 / 2)
            and ToSeq(platform_name) == Old(ToSeq(platform_name))
            and not valid_label(ToSeq(platform_name)))
    # post-conditions-end
    # impl-start
    return ascii_compatible_domain(platform_name)
    # impl-end
