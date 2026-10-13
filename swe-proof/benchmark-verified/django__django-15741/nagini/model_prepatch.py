"""Twin-artifact model for django__django-15741.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A localisation lookup is requested by a *name*. That name is supplied as a
  string-valued argument, which may arrive in either of two equivalent forms:

    * already-resolved — the name is directly available as a sequence of
      characters; or
    * deferred — the name is wrapped in a placeholder that only yields its
      character sequence once it is resolved (the same character sequence the
      resolved form carries).

  The looked-up value must depend ONLY on the resolved character sequence of
  the requested name. Two requests whose names resolve to the same character
  sequence MUST return the same value, regardless of whether either name
  arrived already-resolved or deferred. In particular, requesting a name in its
  deferred form returns exactly what requesting the same name in its
  already-resolved form returns.

  A request must also leave the looked-up values as it found them. The value a
  requester is handed for a name is the one the downstream lookup itself keeps
  and hands out again to every later request for that name -- it does not become
  the requester's own object to modify, and where the lookup holds no separate
  value for a name it may hand back the name object itself. So a request obtains
  read access to that value and passes it on, and the value associated with a
  name is the same after a request as it was before it: a later request for the
  same name still yields the same value.

  Nothing changes hands in the other direction either. Asking with a name does
  not modify it, but it does not leave the requester in sole possession of it:
  the downstream lookup keys itself on the resolved name and keeps hold of what
  it was keyed with. So read access is all a request needs of a name and all it
  gives back -- and since neither the name nor the value is anyone's exclusive
  property across a request, the value served for a name may be that very name.

The name is modelled as a minimal object carrying a ``deferred`` flag and its
underlying character sequence as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing). ``resolve`` is the deep model of the placeholder-to-text
coercion: it yields the underlying character sequence in both forms and is
validated == the real coercion by axiom_check.py (G-AX), NOT consumed as an
axiom. The unchanged downstream lookup keyed on a resolved name is modelled by
the pure ``format_value`` (a deterministic function of the resolved character
sequence) and its list-producing companion ``do_lookup``; their soundness —
that the real lookup is determined by the resolved name only — is checked by
G-AX.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FormatType:
    def __init__(self, deferred: bool, content: List[int]) -> None:
        Requires(Acc(list_pred(content), 1 / 2))
        # Two field stores, loop-free: the constructor always terminates. Level 1
        # so a level-2 body (lookup_format, and the admissibility witness that
        # builds a concrete FormatType) can call it without leaking its own
        # obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.deferred) and self.deferred == deferred)  # type: ignore
        Ensures(Acc(self.content) and self.content is content)  # type: ignore
        Ensures(Acc(list_pred(content), 1 / 2))
        self.deferred = deferred
        self.content = content


# axioms-start
@Pure
@ContractOnly
def format_value(name: PSeq[int]) -> PSeq[int]:
    """The value of the unchanged downstream localisation lookup, keyed on the
    *resolved* character sequence of the requested name. It is a deterministic
    function of that sequence alone (same resolved name -> same value). The
    proof consumes only this functional determinism. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """


@ContractOnly
def do_lookup(name: List[int]) -> List[int]:
    """The unchanged downstream lookup as a list-producing operation: given a
    fully-resolved name it returns the value for that name. Its character
    content is exactly ``format_value`` of the resolved name (so the value
    depends only on the resolved characters). Read-only in the name.

    The value handed back stays the lookup's own: the very same object is handed
    out again to every later request for that name, and for a name the lookup
    holds no separate value for it is the name object itself. A caller therefore
    obtains read access to that value and never the exclusive access that
    modifying it would take; nothing here asserts that the value is an object
    distinct from the name, or one the caller may keep for itself."""
    # It only READS the name it is given: read access is all it needs and all it
    # gives back, and it never takes ownership of the name.
    Requires(Wildcard(list_pred(name)))
    # A keyed dictionary lookup over the resolved name: bounded, loop-free work,
    # so it always terminates. Level 1, strictly below the level-2 caller.
    Requires(MustTerminate(1))
    Ensures(Wildcard(list_pred(name)))
    # Read access to the value the lookup serves for this name, never ownership
    # of it: a caller may read what the name is associated with, and may not
    # modify it. Because neither the name nor the value is owned across this
    # call, the value being the name object itself stays POSSIBLE here -- a
    # requester may not conclude the two are distinct objects.
    Ensures(Wildcard(list_pred(Result())))
    Ensures(ToSeq(Result()) == format_value(ToSeq(name)))
# axioms-end


# pure-start
@Pure
def resolve(ft: FormatType) -> PSeq[int]:
    """The resolved character sequence of a requested name. A deferred name and
    an already-resolved name yield the SAME underlying character sequence: the
    resolution does not depend on the ``deferred`` flag. Deep model of the
    placeholder-to-text coercion, validated == the real coercion by G-AX."""
    Requires(Acc(ft.content) and Acc(list_pred(ft.content), 1 / 4))
    return ToSeq(ft.content)
# pure-end


def lookup_format(requested_name: FormatType) -> List[int]:
    # pre-conditions-start
    # The requested name is read-only (directive 5): nothing about it is
    # mutated by the lookup.
    Requires(Acc(requested_name.deferred, 1 / 2))
    Requires(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
    # The lookup terminates. Level 2: strictly above do_lookup / FormatType.
    # __init__ (level 1), and high enough that list.__init__ (building `name`)
    # has room below the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(requested_name.deferred, 1 / 2))
    Ensures(Acc(requested_name.content, 1 / 2))
    # NOTHING IS OWNED ACROSS A REQUEST. The requester keeps read access to the
    # name it asked with -- the request does not modify that name -- but not
    # exclusive ownership of it: the downstream lookup keys itself on the resolved
    # name and holds on to what it was keyed with, so a requester cannot take the
    # name back for its own exclusive use once it has asked with it.
    Ensures(Wildcard(list_pred(requested_name.content)))
    # And the requester obtains READ access to the value the name is associated
    # with, never ownership of it. So the request leaves that association as it
    # found it -- the same name requested afterwards still yields the same value
    # -- and read access is all there is to hand over anyway, since the value
    # served may be the object the downstream lookup keeps, or the name itself.
    # Read access on both sides is also what keeps those two POSSIBLY THE SAME
    # object: nothing here lets a requester conclude that the value it was handed
    # is an object distinct from the name it asked with.
    Ensures(Wildcard(list_pred(Result())))
    # The value depends only on the RESOLVED character sequence of the name.
    # Because ``resolve`` ignores the deferred flag, a deferred name and an
    # already-resolved name with the same characters return the same value.
    Ensures(ToSeq(Result()) == format_value(resolve(requested_name)))
    # post-conditions-end
    # impl-start
    # Pre-patch: a deferred name is fed to the downstream lookup without first
    # being resolved to its character sequence; only an already-resolved name
    # can be used as a real lookup key, so the deferred form yields a value not
    # keyed on the resolved characters.
    name = []  # type: List[int]
    if not requested_name.deferred:
        i = 0
        while i < len(requested_name.content):
            # invariants-start
            Invariant(Acc(requested_name.content, 1 / 2) and Acc(list_pred(requested_name.content), 1 / 2))
            Invariant(Acc(list_pred(name)))
            Invariant(0 <= i and i <= len(requested_name.content))
            Invariant(ToSeq(name) == ToSeq(requested_name.content).take(i))
            # `i` rises by one per pass and the bound len(content) is fixed (content
            # is read-only at 1/2), so len(content) - i + 1 strictly decreases and
            # stays >= 1 while i < len(content).
            Invariant(MustTerminate(len(requested_name.content) - i + 1))
            # invariants-end
            name.append(requested_name.content[i])
            i = i + 1
        Assert(ToSeq(requested_name.content).take(len(requested_name.content)) == ToSeq(requested_name.content))
    result = do_lookup(name)
    return result
    # impl-end
