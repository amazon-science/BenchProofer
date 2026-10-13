"""Twin-artifact model for pytest-dev__pytest-5840.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A loaded configuration helper file is cached against a deduplication key
  derived from its canonical filesystem location, so that a second request for
  the SAME physical file reuses the cached entry instead of loading it again.
  The cached entry is later used to import the file as a dotted module, and
  that import succeeds only when the cache lookup for the file actually FINDS
  the entry stored by the earlier request.

  A canonical location string alone is not enough to make the lookup succeed:
  the deduplication key is produced by a key constructor, and two keys with
  the SAME canonical location string need not be recognised as the same key by
  the cache's membership test. There are two constructor conventions:

    * a convention whose keys are recognised by the cache's membership test as
      equal to an independently-recomputed key for the same canonical location
      (so storing under such a key and later looking the file up by recomputing
      its key FINDS the entry); and
    * a convention whose keys carry the same canonical location string but are
      NOT recognised by that membership test as equal to an independently
      recomputed key (so a later lookup that recomputes the key MISSES the
      entry, even though the location strings are identical).

  The required behaviour is that the deduplication key be produced under the
  recognised convention, so that an independently-recomputed key for the same
  location finds the stored entry. Producing a key with the correct canonical
  location string is necessary but NOT sufficient: a key that merely carries the
  right string yet is built under the unrecognised convention does not make the
  lookup succeed. The result is therefore required to be a key the recognised
  construction actually produced — not merely one whose location string equals
  the canonical one.

Filesystem location strings are modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); the specification is carried over `PSeq[int]`.
The unchanged value-level canonicalisation of a location (the structural
resolution both conventions share) is modelled as a deterministic pure callee
`canonical`. The key constructor is an UNCHANGED callee too; its contract
captures the EFFECT that distinguishes the two conventions — only the recognised
convention grants an unforgeable `lookup_recognised` token on its output, the
unrecognised convention yields the same location string but no token. The
result's postcondition REQUIRES that token, so a verifying construction must
route its result through the recognised convention; it cannot return a key the
recognised construction never produced. The constructor contract is validated
against the real cache-membership semantics out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def canonical(loc: PSeq[int]) -> PSeq[int]:
    """The unchanged value-level canonicalisation of a location string: its
    structural resolution (the part both key-construction conventions share and
    that neither convention under change alters). Deterministic — the canonical
    location depends only on the location string. Never the operation under
    change; provenance + executable soundness check: mapping.md / axiom_check.py.
    """


# Abstract token marking a key that the cache's membership test RECOGNISES as
# equal to an independently-recomputed key for the same canonical location: a
# capability the recognised construction grants on its output and that nothing
# else can fabricate. Its argument records the canonical location the key
# carries. The result of the whole operation must hold this token, so the
# result can only be a key the recognised construction actually produced — a key
# built under the convention that is not recognised by the membership test never
# grants it, even though its location string is identical. Provenance +
# executable soundness check: mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def lookup_recognised(canon: PSeq[int]) -> bool:
    pass


@ContractOnly
def make_key(loc: List[int], recognised_convention: bool) -> List[int]:
    """The deduplication-key constructor (the UNCHANGED callee that builds the
    cache key from a location). It is invoked under one of two conventions:

      * `recognised_convention == True`: it builds a key the cache's membership
        test recognises as equal to an independently-recomputed key for the
        same canonical location; and
      * `recognised_convention == False`: it builds a key carrying the same
        canonical location string, but one the membership test does NOT
        recognise as equal to an independently-recomputed key.

    EITHER convention returns a key whose carried location string is the
    canonical location of the input (the location strings are identical across
    conventions). The distinguishing EFFECT is recognition: only the recognised
    convention grants the `lookup_recognised` token on its output. A key built
    under the unrecognised convention carries the same location string but is
    never granted the token — so a later lookup that recomputes the key would
    miss it. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(loc), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(loc), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Both conventions carry the canonical location string of the input.
    Ensures(ToSeq(Result()) == canonical(Old(ToSeq(loc))))
    # Only the recognised convention grants the recognition token on its output.
    Ensures(Implies(recognised_convention, lookup_recognised(ToSeq(Result()))))
# axioms-end


# pure-start
# (No deep value fold needed: the value-level canonicalisation both conventions
#  share is the unchanged callee `canonical`; the load-bearing change is the
#  key-construction convention, modelled by the `make_key` effect above.)
# pure-end


def conftest_dedup_key(loc: List[int]) -> List[int]:
    # pre-conditions-start
    # The location is read-only; only fractional permission is needed and
    # returned (the spec may not be satisfied by overwriting the input).
    Requires(Acc(list_pred(loc), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(loc), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The key carries the canonical location string of the input (necessary, but
    # not sufficient — both conventions satisfy this).
    Ensures(ToSeq(Result()) == canonical(Old(ToSeq(loc))))
    # The load-bearing clause: the key must be one the RECOGNISED construction
    # actually produced — it holds the token the membership test grants only on
    # a key it recognises as equal to an independently-recomputed key for the
    # same location. It CANNOT be discharged by location-string equality alone,
    # because a key built under the unrecognised convention carries the identical
    # location string yet is never granted the token; the discriminator is the
    # recognition effect, not the string value.
    Ensures(lookup_recognised(ToSeq(Result())))
    # post-conditions-end
    # impl-start
    # Build the deduplication key under the recognised convention, so an
    # independently-recomputed key for the same location finds the stored entry.
    result = make_key(loc, True)
    return result
    # impl-end
