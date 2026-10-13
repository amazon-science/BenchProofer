"""Twin-artifact model for sphinx-doc__sphinx-8551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An implicit type cross-reference produced by an info field (the inline type
  specifier of a parameter/return annotation) must be resolved relative to the
  namespace in which it appears.  The reference node therefore has to record the
  surrounding namespace context — the enclosing module and the enclosing class
  — in addition to the (unqualified) target name and the "prefer-specific"
  search flag.

  Resolution in prefer-specific mode tries the contextual prefixes in priority
  order:

      module + class + name      (the most specific candidate)
      module + name
      name                       (the bare, top-level candidate)

  and only if NONE of those fully-qualified candidates is a registered object
  does it fall back to a suffix ("fuzzy") match, which may match several
  registered names.  Consequently, when the surrounding context is recorded on
  the node and a contextual object exists, an unqualified target resolves to
  exactly that one object; when the context is dropped (left empty), resolution
  skips straight to the suffix fallback and an unqualified target that occurs in
  several sub-namespaces resolves ambiguously (more than one candidate).

Qualified names are modelled as `PSeq[int]` of segment tokens (a dotted name is
the concatenation of its segment sequences); Nagini bans `str` indexing.  The
namespace context is `Optional[PSeq[int]]` — `None` denotes "no surrounding
module/class".  The registry of known objects is a `PSeq[PSeq[int]]`.

The prefer-specific resolver is modelled DEEPLY as the pure functions
`resolve_count` / `resolve_name` (the suffix/membership cascade); its equality
to the real resolver is checked out-of-band by axiom_check.py (G-AX), NOT
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# axioms-start
# (no consumed @ContractOnly axiom: the resolver is modelled deeply below and
#  validated == the real resolver out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def suffix_eq(obj: PSeq[int], name: PSeq[int]) -> bool:
    """True iff the qualified name `obj` ends with the segment sequence `name`
    (the suffix test used by the fallback match: an object `a.b.A` ends with the
    target `A`)."""
    if len(name) > len(obj):
        return False
    return obj.drop(len(obj) - len(name)) == name


@Pure
def member(objs: PSeq[PSeq[int]], q: PSeq[int]) -> bool:
    """True iff the exact qualified name `q` is a registered object.
    Front-recursive so a single unfold is available per scan step."""
    if len(objs) == 0:
        return False
    if objs[0] == q:
        return True
    return member(objs.drop(1), q)


@Pure
def count_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> int:
    """Number of registered objects whose qualified name ends with `name` — the
    size of the fallback (suffix) candidate set.  Front-recursive."""
    Ensures(Result() >= 0)
    if len(objs) == 0:
        return 0
    rest = count_suffix(objs.drop(1), name)
    if suffix_eq(objs[0], name):
        return 1 + rest
    return rest


@Pure
def has_ctx_candidate(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                      name: PSeq[int], objs: PSeq[PSeq[int]]) -> bool:
    """True iff some contextual prefix candidate (module.class.name, module.name
    or the bare name) is a registered object.  Empty context (`None`) supplies
    no qualified candidate, so only the bare name can match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return True
    if mod is not None and member(objs, mod + name):
        return True
    return member(objs, name)


@Pure
def resolve_count(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                  name: PSeq[int], objs: PSeq[PSeq[int]]) -> int:
    """Number of candidates prefer-specific resolution returns: exactly one when
    a contextual prefix candidate is a registered object, otherwise the size of
    the suffix-fallback set."""
    Ensures(Result() >= 0)
    if has_ctx_candidate(mod, cls, name, objs):
        return 1
    return count_suffix(objs, name)


@Pure
def first_suffix(objs: PSeq[PSeq[int]], name: PSeq[int]) -> PSeq[int]:
    """The first registered object whose qualified name ends with `name` — the
    single candidate the suffix fallback selects when exactly one matches.
    Front-recursive; defined (returns `name`) only when no object matches."""
    if len(objs) == 0:
        return name
    if suffix_eq(objs[0], name):
        return objs[0]
    return first_suffix(objs.drop(1), name)


@Pure
def resolve_name(mod: Optional[PSeq[int]], cls: Optional[PSeq[int]],
                 name: PSeq[int], objs: PSeq[PSeq[int]]) -> PSeq[int]:
    """The single qualified name prefer-specific resolution selects, following
    the priority order module.class.name > module.name > name; when no
    contextual prefix candidate exists it is the unique suffix-fallback match."""
    if mod is not None and cls is not None and member(objs, mod + cls + name):
        return mod + cls + name
    if mod is not None and member(objs, mod + name):
        return mod + name
    if member(objs, name):
        return name
    return first_suffix(objs, name)
# pure-end


class RefNode:
    """The reference node a field xref builds: its target name, the prefer-
    specific flag, and the recorded surrounding namespace context."""

    def __init__(self, target: PSeq[int], specific: bool,
                 ctx_mod: Optional[PSeq[int]], ctx_cls: Optional[PSeq[int]]) -> None:
        self.target = target          # type: PSeq[int]
        self.specific = specific      # type: bool
        self.ctx_mod = ctx_mod        # type: Optional[PSeq[int]]
        self.ctx_cls = ctx_cls        # type: Optional[PSeq[int]]
        Ensures(Acc(self.target) and self.target is target)
        Ensures(Acc(self.specific) and self.specific == specific)
        Ensures(Acc(self.ctx_mod) and self.ctx_mod is ctx_mod)
        Ensures(Acc(self.ctx_cls) and self.ctx_cls is ctx_cls)


def make_field_ref(target: PSeq[int], cur_module: Optional[PSeq[int]],
                   cur_class: Optional[PSeq[int]], objs: PSeq[PSeq[int]]) -> RefNode:
    # pre-conditions-start
    Requires(cur_module is not None)
    # the contextual object module.target exists, while the bare target does not
    # and the same simple name also occurs in a deeper sub-namespace (so the
    # suffix fallback alone is ambiguous): the situation in which the surrounding
    # context is what makes resolution unique.  The module-qualified candidate is
    # the most specific one that is registered (no class-nested object of the
    # same simple name).
    Requires(member(objs, cur_module + target))
    Requires(Implies(cur_class is not None,
                     not member(objs, cur_module + cur_class + target)))
    Requires(not member(objs, target))
    Requires(count_suffix(objs, target) >= 2)
    # pre-conditions-end
    # post-conditions-start
    # The node records the surrounding namespace context and is prefer-specific.
    Ensures(Acc(Result().target) and Acc(Result().specific) and
            Acc(Result().ctx_mod) and Acc(Result().ctx_cls))
    Ensures(Result().target is target)
    Ensures(Result().specific)
    Ensures(Result().ctx_mod is cur_module)
    Ensures(Result().ctx_cls is cur_class)
    # End-to-end: resolving the produced node against the registry yields exactly
    # the one contextual object, not the ambiguous suffix-fallback set.
    Ensures(resolve_count(Result().ctx_mod, Result().ctx_cls,
                          Result().target, objs) == 1)
    Ensures(resolve_name(Result().ctx_mod, Result().ctx_cls,
                         Result().target, objs) == cur_module + target)
    # post-conditions-end
    # impl-start
    node = RefNode(target, True, None, None)
    return node
    # impl-end
