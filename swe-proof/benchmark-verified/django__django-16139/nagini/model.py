"""Twin-artifact model for django__django-16139.

Behaviour under specification (stated as desired behaviour):

  When an editable object is reachable through more than one identifier, a
  read-only field offers a relative hyperlink to a SECONDARY action page for
  that same object. The action page is addressed by the object's CANONICAL
  identifier (its primary key), NOT by whatever identifier happened to be used
  to reach the current page. So the relative reference, once resolved against
  the current page's location, must land on the action page keyed by the
  canonical identifier, regardless of which identifier addressed the current
  page.

  Concretely: the current page lives at a location whose path is

      [.. shared prefix ..] / <access-token> / <current-action>         (a "directory" URL, trailing slash)

  and the desired target is

      [.. shared prefix ..] / <primary-key> / <secondary-action>

  The function builds a RELATIVE reference `rel` (a list of path steps, each
  either an ordinary segment or the up-one-level step "..") to embed in the
  page. Correctness means: resolving `rel` against the current location yields
  exactly the target above, for EVERY access-token value — in particular when
  the access-token differs from the primary key.

Relative-reference resolution is the standard hierarchical-URL rule (pop one
segment per ".."; otherwise append). It is modelled DEEPLY here as a verified
segment fold (`resolve`), validated equal to the real resolver out of band by
axiom_check.py (G-AX), NOT consumed as an axiom.

URLs are modelled as `List[int]` / `PSeq[int]` of opaque path-segment ids; the
sentinel `DOTDOT == -1` denotes the up-one-level step. Distinct ids model
distinct path segments (so an access-token id and a primary-key id are
independent), which is exactly what lets the spec require the resolved target
to be keyed by the primary key for every access-token value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms. The one unchanged callee whose semantics
#  the proof relies on — hierarchical relative-reference resolution — is
#  modelled DEEPLY as the verified pure fold `resolve` below, and validated
#  equal to the real resolver by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def DOTDOT() -> int:
    """Sentinel path step meaning 'up one level' (the ".." segment)."""
    return -1


@Pure
def resolve(base_dir: PSeq[int], rel: PSeq[int]) -> PSeq[int]:
    """Resolve a relative reference `rel` against the directory-segment list
    `base_dir` of the current (trailing-slash) location, per the standard
    hierarchical rule: a ".." step (DOTDOT) drops the last accumulated segment;
    any other step is appended. Front-recursive over `rel` so a single unfold
    is available per loop step."""
    if len(rel) == 0:
        return base_dir
    if rel[0] == DOTDOT():
        if len(base_dir) == 0:
            return resolve(base_dir, rel.drop(1))
        return resolve(base_dir.take(len(base_dir) - 1), rel.drop(1))
    return resolve(base_dir + PSeq(rel[0]), rel.drop(1))
# pure-end


def build_action_reference(prefix: List[int], token: int, current_action: int,
                           pk: int, secondary_action: int) -> List[int]:
    # pre-conditions-start
    # `prefix` is the constant, shared leading path of both URLs (e.g. the
    # collection path up to but excluding the per-object identifier). It is
    # read, never mutated -> fractional permission, required AND ensured.
    Requires(Acc(list_pred(prefix), 1 / 2))
    # The up-one-level sentinel must not collide with any real segment id used
    # in the location: ordinary segments (prefix entries, token, action codes,
    # pk) are non-negative; DOTDOT is the only negative step.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(prefix),
                                            prefix[k] >= 0), [[prefix[k]]])))
    Requires(token >= 0 and current_action >= 0 and pk >= 0
             and secondary_action >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Resolving the produced relative reference against the current location
    # lands EXACTLY on the secondary-action page keyed by the PRIMARY KEY,
    # for every access token (the token is popped away, the pk is supplied).
    Ensures(
        resolve(ToSeq(prefix) + PSeq(token) + PSeq(current_action),
                ToSeq(Result()))
        == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
    )
    # post-conditions-end
    # impl-start
    # rel = ['..', '..', <pk>, <secondary_action>]
    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
    # --- proof that resolving rel against the current location yields the
    #     pk-keyed target (one unfold of `resolve` per step). ---
    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
    rel = ToSeq(result)
    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
    Assert(len(rel) == 4)
    Assert(rel[0] == DOTDOT())
    Assert(rel.drop(1)[0] == DOTDOT())
    Assert(rel.drop(1).drop(1)[0] == pk)
    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
    # base sequences after each pop / push, with the take/drop algebra facts.
    base1 = ToSeq(prefix) + PSeq(token)
    Assert(base0.take(len(base0) - 1) == base1)
    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
    Assert(pk != DOTDOT())
    Assert(secondary_action != DOTDOT())
    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
    # tail backwards, so each equality is a single definitional unfold.
    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
                   rel.drop(1).drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base1, rel.drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base0, rel)
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    return result
    # impl-end
