"""Twin-artifact model for sphinx-doc__sphinx-8120.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A message catalog is assembled from an ORDERED list of catalog sources. Each
  source may or may not provide a translation for a given message, and when it
  does it provides a specific replacement text. The assembled catalog resolves
  a message by the conventional first-wins precedence: the translation is taken
  from the FIRST source, in order, that provides one for that message; if no
  source provides one, the message itself is returned untranslated. A later
  source only fills a gap no earlier source covered.

  There are three kinds of source, in a definite precedence order from most to
  least authoritative:

      (1) the environment's default source (placed first only as a conventional
          probe; for the catalogs in question it provides nothing);
      (2) the project-supplied sources, in their given order -- the
          translations a project author intends to apply;
      (3) the bundled fallback source shipped with the tool.

  The decisive desired behaviour: when a project-supplied source and the
  bundled fallback source BOTH provide a translation for the same message, the
  resolved translation is the PROJECT-supplied one. A project author's
  intentional override of a message wins over the value bundled with the tool;
  the bundled value is used only for messages no project source covers.

Translations are modelled abstractly as small `int` codes (each distinct text
is a distinct code); the spec is about WHICH source's text is selected, not
about the characters of any text, so the carrier is opaque identity. The
resolution precedence is modelled DEEPLY as a front-recursive fold over the
ordered source list; no library callee is consumed as an axiom (the first-wins
precedence of the merged catalog is spelled out and verified). A per-source
pair of parallel lists -- whether the source provides a translation for the
message, and which text it provides -- is plain input data, not an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The merged-catalog first-wins precedence used by the
#  resolution is modelled DEEPLY below (`resolved`, a front-recursive fold over
#  the ordered source list) and validated == the real merged-catalog lookup
#  out-of-band by axiom_check.py / G-AX, never consumed. The per-source catalog
#  facts -- whether a source provides a translation for the message and which
#  text it provides -- are plain input data, not axioms.)
# axioms-end


# pure-start
@Pure
def NO_TEXT() -> int:
    """The sentinel meaning "no translation" (the untranslated message stands
    in for itself). Distinct from every real translation code, which are >= 1.
    """
    return 0


@Pure
def seq_defines(system_defines: bool, ud: PSeq[bool], builtin_defines: bool) -> PSeq[bool]:
    """The assembled ordered "provides?" sequence: default, then project
    sources, then bundled fallback."""
    Ensures(len(Result()) == len(ud) + 2)
    return (PSeq(system_defines) + ud) + PSeq(builtin_defines)


@Pure
def seq_tr(system_tr: int, ut: PSeq[int], builtin_tr: int) -> PSeq[int]:
    """The assembled ordered "text" sequence, aligned with seq_defines."""
    Ensures(len(Result()) == len(ut) + 2)
    return (PSeq(system_tr) + ut) + PSeq(builtin_tr)


@Pure
def resolved(defines: PSeq[bool], tr: PSeq[int]) -> int:
    """First-wins resolution: the translation text of the FIRST source (in
    order) that provides one for the message, or NO_TEXT() if none does.
    Front-recursive so a single unfold is available per loop step. The two
    parallel sequences are aligned: `tr[i]` is the text source `i` provides,
    meaningful only where `defines[i]` holds."""
    Requires(len(defines) == len(tr))
    if len(defines) == 0:
        return NO_TEXT()
    if defines[0]:
        return tr[0]
    return resolved(defines.drop(1), tr.drop(1))


@Pure
def resolved_assembled(system_defines: bool, system_tr: int,
                       ud: PSeq[bool], ut: PSeq[int],
                       builtin_defines: bool, builtin_tr: int) -> int:
    """First-wins resolution over the fully assembled order (default ++ project
    ++ bundled). Wrapper so callers need only the project-list length equality;
    the assembled-length equality is discharged here."""
    Requires(len(ud) == len(ut))
    return resolved(seq_defines(system_defines, ud, builtin_defines),
                    seq_tr(system_tr, ut, builtin_tr))


@Pure
def some_provides(defines: PSeq[bool]) -> bool:
    """Whether ANY source in the order provides a translation for the message.
    Front-recursive so a single unfold is available per loop step."""
    if len(defines) == 0:
        return False
    if defines[0]:
        return True
    return some_provides(defines.drop(1))


@Pure
def first_provider(defines: PSeq[bool]) -> int:
    """Index of the FIRST source (in order) that provides a translation, given
    that some source does. Front-recursive."""
    Requires(some_provides(defines))
    if defines[0]:
        return 0
    return 1 + first_provider(defines.drop(1))


@Pure
def lemma_first_provider_bound(defines: PSeq[bool]) -> bool:
    """The first provider's index is in range and that source provides.
    Proven by front-recursion."""
    Requires(some_provides(defines))
    Ensures(Result())
    Ensures(0 <= first_provider(defines) and first_provider(defines) < len(defines))
    Ensures(defines[first_provider(defines)])
    if defines[0]:
        return True
    return lemma_first_provider_bound(defines.drop(1))


@Pure
def lemma_seq_len(system_defines: bool, ud: PSeq[bool], builtin_defines: bool,
                  system_tr: int, ut: PSeq[int], builtin_tr: int) -> bool:
    """The two assembled sequences have equal length when the project lists do
    (each adds the same two endpoints)."""
    Requires(len(ud) == len(ut))
    Ensures(Result())
    Ensures(len(seq_defines(system_defines, ud, builtin_defines))
            == len(seq_tr(system_tr, ut, builtin_tr)))
    return True
# pure-end


def select_translation(system_defines: bool, system_tr: int,
                     user_defines: List[bool], user_tr: List[int],
                     builtin_defines: bool, builtin_tr: int,
                     message: int) -> int:
    # pre-conditions-start
    # The project-supplied source facts are read only; fractional permission.
    Requires(Acc(list_pred(user_defines), 1 / 2))
    Requires(Acc(list_pred(user_tr), 1 / 2))
    Requires(len(user_defines) == len(user_tr))
    Requires(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # `message` is the (code for the) untranslated message. Real translations
    # are coded >= 1; NO_TEXT() (0) is reserved for "untranslated". A source
    # that PROVIDES a translation supplies a real (>= 1) text.
    Requires(message >= 1)
    Requires(Implies(system_defines, system_tr >= 1))
    Requires(Implies(builtin_defines, builtin_tr >= 1))
    Requires(Forall(int, lambda i: (
        Implies(0 <= i and i < len(user_defines) and user_defines[i], user_tr[i] >= 1),
        [[user_defines[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(user_defines), 1 / 2))
    Ensures(Acc(list_pred(user_tr), 1 / 2))
    Ensures(len(user_defines) == len(user_tr))
    Ensures(len(ToSeq(user_defines)) == len(ToSeq(user_tr)))
    # The result is the first-wins resolution over the assembled order, with the
    # untranslated message standing in when no source provides a translation.
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) == NO_TEXT(),
        Result() == message))
    Ensures(Implies(
        resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                           ToSeq(user_tr), builtin_defines, builtin_tr) != NO_TEXT(),
        Result() == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                       ToSeq(user_tr), builtin_defines, builtin_tr)))
    # Decisive precedence: when the environment default provides nothing but a
    # project-supplied source provides a translation, the result is the FIRST
    # such project source's text -- NOT the bundled fallback's, even if the
    # bundled source also provides one. (`first_provider` over the project
    # sources is the least index that provides; the result is its text.)
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        0 <= first_provider(ToSeq(user_defines))
        and first_provider(ToSeq(user_defines)) < len(user_defines)))
    Ensures(Implies(
        not system_defines and some_provides(ToSeq(user_defines)),
        Result() == ToSeq(user_tr)[first_provider(ToSeq(user_defines))]))
    # post-conditions-end
    # impl-start
    # Assemble the ordered source list:  default, then project sources, then
    # the bundled fallback (project sources ahead of the bundled fallback).
    defines = [system_defines]  # type: List[bool]
    defines = defines + user_defines
    defines = defines + [builtin_defines]
    tr = [system_tr]  # type: List[int]
    tr = tr + user_tr
    tr = tr + [builtin_tr]

    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(len(defines) == len(tr))

    n = len(defines)
    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
    res = NO_TEXT()
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(defines)))
        Invariant(Acc(list_pred(tr)))
        Invariant(Acc(list_pred(user_defines), 1 / 2))
        Invariant(Acc(list_pred(user_tr), 1 / 2))
        Invariant(len(user_defines) == len(user_tr))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < len(user_defines) and user_defines[k], user_tr[k] >= 1),
            [[user_defines[k]]])))
        Invariant(len(defines) == n and len(tr) == n)
        Invariant(0 <= i and i <= n)
        Invariant(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
        Invariant(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
        # invariants-end
        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
        if defines[i - 1]:
            res = tr[i - 1]
        i = i - 1

    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
    # res now equals first-wins resolution over the whole assembled list.
    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
    Assert(ToSeq(defines) == seq_defines(system_defines, ToSeq(user_defines), builtin_defines))
    Assert(ToSeq(tr) == seq_tr(system_tr, ToSeq(user_tr), builtin_tr))
    Assert(res == resolved(seq_defines(system_defines, ToSeq(user_defines), builtin_defines),
                           seq_tr(system_tr, ToSeq(user_tr), builtin_tr)))
    Assert(res == resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                                     ToSeq(user_tr), builtin_defines, builtin_tr))
    out = res
    if res == NO_TEXT():
        out = message

    # Relate the whole-list resolution to the project-prefix first provider
    # (the decisive precedence clause). When some project source provides, the
    # first provider's text is real (>= 1), so it is not the NO_TEXT sentinel
    # and `out` keeps it.
    if not system_defines and some_provides(ToSeq(user_defines)):
        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
                                      ToSeq(user_tr), builtin_defines, builtin_tr))
        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
        fp = first_provider(ToSeq(user_defines))
        Assert(ToSeq(user_defines)[fp])
        Assert(0 <= fp and fp < len(user_defines))
        Assert(user_defines[fp])
        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
        Assert(user_tr[fp] >= 1)
        Assert(res == ToSeq(user_tr)[fp])
        Assert(res >= 1)
        Assert(out == res)
    return out
    # impl-end


# Helper @Pure lemmas for the postcondition proof (out of the spec regions;
# pure proof glue, no behavioural content).
@Pure
def _resolution_picks_user(system_defines: bool, system_tr: int,
                           ud: PSeq[bool], ut: PSeq[int],
                           builtin_defines: bool, builtin_tr: int) -> bool:
    """The whole-list first-wins resolution, when the default provides nothing
    and some project source provides, equals the first project source's text.
    The assembled list is [default] ++ project ++ [bundled]; with the default
    not providing, resolution descends into the project prefix, whose first
    provider wins (it precedes the bundled fallback)."""
    Requires(len(ud) == len(ut))
    Requires(not system_defines)
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(seq_defines(system_defines, ud, builtin_defines),
                     seq_tr(system_tr, ut, builtin_tr)) == ut[first_provider(ud)])
    # Peel the (non-providing) default head: seq_defines == [sys] ++ (ud++[builtin]).
    da = seq_defines(system_defines, ud, builtin_defines)  # type: PSeq[bool]
    ta = seq_tr(system_tr, ut, builtin_tr)  # type: PSeq[int]
    tail_d = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    tail_t = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(da == PSeq(system_defines) + tail_d)
    Assert(ta == PSeq(system_tr) + tail_t)
    Assert(da[0] == system_defines)
    Assert(da.drop(1) == tail_d)
    Assert(ta.drop(1) == tail_t)
    # resolved(da, ta): da[0] is False, so it equals resolved(tail_d, tail_t).
    Assert(resolved(da, ta) == resolved(tail_d, tail_t))
    return _resolution_over_prefix(ud, ut, builtin_defines, builtin_tr)


@Pure
def _resolution_over_prefix(ud: PSeq[bool], ut: PSeq[int],
                            builtin_defines: bool, builtin_tr: int) -> bool:
    """If some source in `ud` provides, resolution over `ud ++ [bundled]`
    equals `ud`'s first provider's text (the bundled tail is never reached).
    Front-recursive on `ud`."""
    Requires(len(ud) == len(ut))
    Requires(some_provides(ud))
    Ensures(Result())
    Ensures(0 <= first_provider(ud) and first_provider(ud) < len(ud))
    Ensures(resolved(ud + PSeq(builtin_defines), ut + PSeq(builtin_tr))
            == ut[first_provider(ud)])
    cd = ud + PSeq(builtin_defines)  # type: PSeq[bool]
    ct = ut + PSeq(builtin_tr)  # type: PSeq[int]
    Assert(cd[0] == ud[0])
    Assert(ct[0] == ut[0])
    if ud[0]:
        return True
    Assert(cd.drop(1) == ud.drop(1) + PSeq(builtin_defines))
    Assert(ct.drop(1) == ut.drop(1) + PSeq(builtin_tr))
    Assert(some_provides(ud.drop(1)))
    Assert(lemma_first_provider_bound(ud.drop(1)))
    Assert(first_provider(ud) == 1 + first_provider(ud.drop(1)))
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[1 + first_provider(ud.drop(1))])
    Assert(ut.drop(1)[first_provider(ud.drop(1))] == ut[first_provider(ud)])
    return _resolution_over_prefix(ud.drop(1), ut.drop(1), builtin_defines, builtin_tr)
