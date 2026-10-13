"""Twin-artifact model for sphinx-doc__sphinx-7910.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A documentation-tooling hook decides, for a documented special/init/private
  member of a class, whether that member should be INCLUDED in the generated
  documentation. The decision depends on whether the member's owning class can
  be recovered as the genuine owner of the member: the hook resolves the class
  by name through the member object's surrounding global namespace, then
  confirms the member is actually defined on that class.

  The member object handed to the hook may be a callable that has been WRAPPED
  by a decorator (the wrapper carries the original member's documentation and
  qualified name, but its surrounding global namespace is the decorator's, not
  the one in which the owning class is defined). The owning class must therefore
  be resolved through the ORIGINAL (unwrapped) member object's global namespace
  -- the namespace in which the member, and hence its class, is genuinely
  defined -- never through the wrapper's. Concretely:

    * the owning class is looked up by its name token in the global namespace of
      the canonical (unwrapped) member object, and the member is the class's own
      member iff that lookup both resolves the class AND records the member name
      among the class's own members;
    * a documented special/init/private member that IS its class's own member,
      and whose corresponding inclusion setting is enabled, is INCLUDED
      (Result() is False -- "do not skip"); otherwise the hook abstains
      (Result() is None) and leaves the default decision untouched.

  The behavioural consequence that matters: wrapping a member with a
  documentation-preserving decorator does not hide it from the docs, because the
  ownership lookup follows the unwrapped object's namespace, which still knows
  the class.

Modelling choices (Nagini fragment):
  * The member name and the owning class-name token are opaque ``int``
    identities; the tested behaviour only observes whether the ownership lookup
    succeeds, so integer identity is the faithful carrier (mapping.md s2).
  * The member object is a minimal class exposing only the touched fields: the
    ``has_doc`` flag, the ground-truth ``is_class_member`` flag, the owning
    class-name token ``cls_name`` (from the qualified name) and the surrounding
    global namespace ``ns`` (``Dict[int, bool]`` keyed by a class-name token; a
    present key records, for the class resolved at that name, whether the member
    is among the class's OWN members -- the repository's
    ``cls_path in globals and name in cls.__dict__`` collapsed into the single
    ``cls_is_owner`` outcome). For a decorated object this ``ns`` is the
    wrapper's and need not contain ``cls_name`` at all.
  * ``canonical`` is the unchanged library primitive that recovers the original
    member object from a wrapper (the identity on an un-wrapped object). It is
    axiomatized (A-consumed) and checked against the real callee out-of-band by
    axiom_check.py (G-AX). It is the WEAKEST contract the proof needs.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional, Dict
from nagini_contracts.contracts import *


class MemberObj:
    """Minimal view of the member object handed to the hook. ``ns`` maps a
    class-name token to whether the class resolved there owns this member."""

    def __init__(self, has_doc: bool, is_class_member: bool, cls_name: int,
                 ns: Dict[int, bool]) -> None:
        Requires(Acc(dict_pred(ns), 1 / 2))
        Ensures(Acc(self.has_doc) and self.has_doc == has_doc)        # type: ignore
        Ensures(Acc(self.is_class_member) and self.is_class_member == is_class_member)  # type: ignore
        Ensures(Acc(self.cls_name) and self.cls_name == cls_name)     # type: ignore
        Ensures(Acc(self.ns) and self.ns is ns)                       # type: ignore
        Ensures(Acc(dict_pred(ns), 1 / 2))
        self.has_doc = has_doc
        self.is_class_member = is_class_member
        self.cls_name = cls_name
        self.ns = ns


# axioms-start
@ContractOnly
def canonical(obj: MemberObj) -> MemberObj:
    """The unchanged library primitive that recovers the ORIGINAL member object
    from a (possibly decorator-wrapped) one, following the documentation-
    preserving wrapper chain to its end; the identity on an object that is not
    wrapped. The recovered object carries the SAME inclusion-relevant identity
    (has_doc / membership / class name) and exposes the global namespace in
    which the member -- and therefore its owning class -- is genuinely defined,
    so that resolving the class there agrees with the ground-truth membership.
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    WEAKEST contract the proof needs.
    """
    Requires(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Requires(Acc(obj.cls_name, 1 / 4))
    Ensures(Acc(obj.has_doc, 1 / 4) and Acc(obj.is_class_member, 1 / 4))
    Ensures(Acc(obj.cls_name, 1 / 4))
    Ensures(Result() is not None)
    Ensures(Acc(Result().has_doc, 1 / 2) and Acc(Result().is_class_member, 1 / 2))
    Ensures(Acc(Result().cls_name, 1 / 2))
    Ensures(Acc(Result().ns) and Acc(dict_pred(Result().ns)))
    Ensures(Result().has_doc == obj.has_doc)
    Ensures(Result().cls_name == obj.cls_name)
    Ensures(Result().is_class_member == obj.is_class_member)
    # The recovered object's namespace genuinely records ownership: the owning
    # class is resolvable there and owns the member EXACTLY when the member is a
    # genuine class member. (The wrapper's namespace need not -- that is the
    # whole point of recovering the original.)
    Ensures(obj.is_class_member ==
            (obj.cls_name in Result().ns and Result().ns[obj.cls_name]))
# axioms-end


# pure-start
# No pure helpers required.
# pure-end


def skip_decision(obj: MemberObj, is_special: bool, is_init: bool,
                  is_private: bool, inc_special: bool, inc_init: bool,
                  inc_private: bool) -> Optional[bool]:
    # pre-conditions-start
    # `obj` is read-only -- fractional permission on every touched field and on
    # its namespace (directive 5).
    Requires(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Requires(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Requires(Acc(dict_pred(obj.ns), 1 / 4))
    # Exactly one inclusion category applies to a member (init / special /
    # private are mutually exclusive in the repository's classification).
    Requires(Implies(is_init, not is_special and not is_private))
    Requires(Implies(is_special, not is_init and not is_private))
    Requires(Implies(is_private, not is_init and not is_special))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(obj.has_doc, 1 / 2) and Acc(obj.is_class_member, 1 / 2))
    Ensures(Acc(obj.cls_name, 1 / 2) and Acc(obj.ns, 1 / 2))
    Ensures(Acc(dict_pred(obj.ns), 1 / 4))
    # The result is grounded in the TRUE ownership (recovered through the
    # unwrapped namespace), never in whether the wrapper's namespace happens to
    # contain the class:
    #   * a documented, genuinely-owned member whose category is enabled is
    #     INCLUDED -- Result() is False (do not skip);
    #   * any other case abstains -- Result() is None.
    Ensures(Result() is False or Result() is None)
    Ensures((Result() is False) ==
            (obj.has_doc and obj.is_class_member and
             ((is_special and inc_special) or
              (is_init and inc_init) or
              (is_private and inc_private))))
    # post-conditions-end
    # impl-start
    doc = obj.has_doc
    member = obj.is_class_member
    if not doc:
        return None
    # PRE-PATCH (buggy): resolve the owning class through the member object's
    # OWN namespace -- which, for a decorator-wrapped object, is the wrapper's
    # and need not contain the class, so the ground-truth ownership is lost.
    cls_is_owner = False
    if obj.cls_name in obj.ns:
        cls_is_owner = obj.ns[obj.cls_name]
    if cls_is_owner:
        if ((is_special and inc_special) or
                (is_init and inc_init) or
                (is_private and inc_private)):
            return False
    return None
    # impl-end
