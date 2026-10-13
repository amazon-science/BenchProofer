"""Twin-artifact model for psf__requests-6028.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A location string is normalised by re-assembling it from its already-parsed
  components: a scheme, an optional userinfo (credentials) segment, an authority
  segment (host with an optional port), a path, an optional query and an
  optional fragment. The re-assembled location MUST preserve the userinfo: when
  credentials are present they appear, joined to the authority by a single '@',
  as the leading part of the authority segment of the result -- so a location
  that carried credentials keeps them after normalisation, rather than silently
  dropping them.

  Concretely, write the effective authority as

        authority,                      if no credentials are present
        credentials + '@' + authority,  if credentials are present

  and the normalised location is the assembly

        scheme + '://' + effective_authority + path
                 (+ '?' + query, if any)  (+ '#' + fragment, if any).

  The credentials, the authority and the rest of the components are taken
  verbatim from the parse of the input. The required behaviour is that the
  credentials survive into the effective authority whenever they are present;
  the query and fragment pass through unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The component decomposition is produced by an unchanged parsing callee; the
re-assembly is an unchanged combining callee. Both are modelled deeply (the
combining concatenation is spelled out and validated == the real callee by
axiom_check.py / G-AX). The single behavioural choice under specification -- the
'@'-join that keeps the credentials in the authority -- is modelled deeply as a
verified sequence construction.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def effective_authority(creds: PSeq[int], authority: PSeq[int],
                        has_creds: bool) -> PSeq[int]:
    """The authority segment that must flow into the assembly. With credentials
    present, they are prepended to the authority joined by a single '@' (64);
    otherwise the authority is used as-is. This is the behavioural choice under
    specification."""
    if has_creds:
        return creds + PSeq(64) + authority
    return authority


@Pure
def assembled(scheme: PSeq[int], authority: PSeq[int], path: PSeq[int],
              query: PSeq[int], frag: PSeq[int], has_query: bool,
              has_frag: bool) -> PSeq[int]:
    """The combining callee's assembly of a location from its components, for
    the regime these locations inhabit (non-empty authority, present scheme,
    empty params): scheme '://' authority path, with '?' query appended when a
    query is present and '#' fragment appended when a fragment is present.
    Spelled out and validated == the real combining callee by axiom_check.py
    (G-AX)."""
    base = scheme + PSeq(58, 47, 47) + authority + path
    if has_query:
        if has_frag:
            return base + PSeq(63) + query + PSeq(35) + frag
        return base + PSeq(63) + query
    if has_frag:
        return base + PSeq(35) + frag
    return base
# pure-end


def normalize_location(scheme: List[int], creds: List[int],
                       authority: List[int], path: List[int],
                       query: List[int], frag: List[int], has_creds: bool,
                       has_query: bool, has_frag: bool) -> List[int]:
    """Re-assemble a normalised location from its parsed components, preserving
    the credentials. All component carriers are read-only.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(scheme), 1 / 2))
    Requires(Acc(list_pred(creds), 1 / 2))
    Requires(Acc(list_pred(authority), 1 / 2))
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(Acc(list_pred(query), 1 / 2))
    Requires(Acc(list_pred(frag), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(scheme), 1 / 2))
    Ensures(Acc(list_pred(creds), 1 / 2))
    Ensures(Acc(list_pred(authority), 1 / 2))
    Ensures(Acc(list_pred(path), 1 / 2))
    Ensures(Acc(list_pred(query), 1 / 2))
    Ensures(Acc(list_pred(frag), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The normalised location is the assembly over the EFFECTIVE authority,
    # i.e. the authority that retains the credentials when they are present.
    Ensures(ToSeq(Result()) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    # When credentials are present they survive into the result: the effective
    # authority is exactly credentials '@' authority, never the bare authority.
    Ensures(Implies(has_creds,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds)
                    == ToSeq(creds) + PSeq(64) + ToSeq(authority)))
    Ensures(Implies(has_creds and len(creds) > 0,
                    effective_authority(ToSeq(creds), ToSeq(authority),
                                        has_creds) != ToSeq(authority)))
    # post-conditions-end
    # impl-start
    netloc = authority  # type: List[int]
    if has_creds:
        netloc = creds + [64] + authority
    Assert(ToSeq(netloc) == effective_authority(
        ToSeq(creds), ToSeq(authority), has_creds))
    base = scheme + [58, 47, 47] + netloc + path  # type: List[int]
    result = base  # type: List[int]
    if has_query:
        result = base + [63] + query
    if has_frag:
        result = result + [35] + frag
    Assert(ToSeq(result) == assembled(
        ToSeq(scheme),
        effective_authority(ToSeq(creds), ToSeq(authority), has_creds),
        ToSeq(path), ToSeq(query), ToSeq(frag), has_query, has_frag))
    return result
    # impl-end
