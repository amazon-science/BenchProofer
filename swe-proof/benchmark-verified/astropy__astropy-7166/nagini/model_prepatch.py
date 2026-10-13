"""Twin-artifact model for astropy__astropy-7166.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-construction helper fills in a missing docstring on a member of a
  newly-built class from the corresponding member resolved along the base
  classes. For one such member, the docstring is filled in EXACTLY when all
  three conditions hold:

    (1) the member is a kind whose docstring participates in this inheritance:
        either an ordinary callable member, OR a computed-attribute member
        (one exposed through the descriptor protocol, such as a managed
        attribute whose access runs code). BOTH kinds participate; the second
        is the behaviour pinned here.
    (2) the member is a public member of the class, and
    (3) the member does not already carry its own docstring.

  When all three hold the member's docstring becomes the docstring resolved
  from the base classes (the inherited docstring). When any one fails the
  member's docstring is left exactly as it was.

A member is modelled as a minimal object carrying the two kind predicates that
the standard introspection callees report for it (`is_callable_member`,
`is_computed_attribute`), whether it is public (`is_public`), whether it
already has its own docstring (`has_own_doc`), the docstring resolved from the
base classes (`inherited_doc`), and its current docstring (`doc`). A docstring
is modelled as an `int` identity (0 denotes "no docstring"); the discriminating
observable is *whether and to what* the docstring is assigned, not its
characters (Nagini bans `str` indexing).

The two kind predicates are the results of unchanged standard introspection
callees; their classification of the two member kinds (a computed-attribute
member is NOT reported callable but IS reported as a descriptor) is validated
against the real callees out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms are consumed: the introspection-callee results and
# the base-class docstring resolution are carried on the member as already-
# computed fields — type refinements of unchanged callees, validated against
# the real callees by axiom_check.py / G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def fills_docstring(is_callable_member: bool, is_computed_attribute: bool,
                    is_public: bool, has_own_doc: bool) -> bool:
    """The member participates in docstring inheritance and is eligible to be
    filled: it is a callable member OR a computed-attribute member, it is
    public, and it has no docstring of its own."""
    return ((is_callable_member or is_computed_attribute)
            and is_public and not has_own_doc)
# pure-end


class Member:
    """A member of a newly-built class: the two introspection predicates that
    classify its kind, whether it is public, whether it already has a docstring,
    the docstring resolved from the base classes, and its current docstring
    (`doc`; 0 denotes no docstring)."""

    def __init__(self, is_callable_member: bool, is_computed_attribute: bool,
                 is_public: bool, has_own_doc: bool, inherited_doc: int,
                 doc: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_callable_member) and Acc(self.is_computed_attribute)
                and Acc(self.is_public) and Acc(self.has_own_doc)
                and Acc(self.inherited_doc) and Acc(self.doc))
        Ensures(self.is_callable_member == is_callable_member)
        Ensures(self.is_computed_attribute == is_computed_attribute)
        Ensures(self.is_public == is_public)
        Ensures(self.has_own_doc == has_own_doc)
        Ensures(self.inherited_doc == inherited_doc)
        Ensures(self.doc == doc)
        # post-conditions-end
        # impl-start
        self.is_callable_member = is_callable_member      # type: bool
        self.is_computed_attribute = is_computed_attribute  # type: bool
        self.is_public = is_public                        # type: bool
        self.has_own_doc = has_own_doc                    # type: bool
        self.inherited_doc = inherited_doc                # type: int
        self.doc = doc                                    # type: int
        # impl-end


def apply_inheritance(m: Member) -> None:
    # pre-conditions-start
    Requires(Acc(m.is_callable_member, 1 / 2)
             and Acc(m.is_computed_attribute, 1 / 2)
             and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
             and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # Termination obligation. This method owns no loop, so the level only has to
    # leave room beneath the caller for the obligated callees it may reach:
    # Member.__init__ (level 2). The level is heap-dependent rather than a bare
    # constant because a self-call needs the caller's level to be STRICTLY
    # greater than the callee's, which no constant can satisfy against itself.
    # A member already reported as a computed attribute sits at 3; any other
    # member sits at 4, so a call whose argument is a computed-attribute member
    # (as the F2P discriminator is) strictly decreases 4 -> 3 and terminates.
    Requires(MustTerminate(3 if m.is_computed_attribute else 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(m.is_callable_member, 1 / 2)
            and Acc(m.is_computed_attribute, 1 / 2)
            and Acc(m.is_public, 1 / 2) and Acc(m.has_own_doc, 1 / 2)
            and Acc(m.inherited_doc, 1 / 2) and Acc(m.doc))
    # The kind predicates, public flag, own-doc flag and resolved inherited
    # docstring are read-only: unchanged across the call.
    Ensures(m.is_callable_member == Old(m.is_callable_member))
    Ensures(m.is_computed_attribute == Old(m.is_computed_attribute))
    Ensures(m.is_public == Old(m.is_public))
    Ensures(m.has_own_doc == Old(m.has_own_doc))
    Ensures(m.inherited_doc == Old(m.inherited_doc))
    # When the member is eligible (callable OR computed-attribute, public, no
    # own docstring) its docstring becomes the one resolved from the bases.
    Ensures(Implies(fills_docstring(Old(m.is_callable_member),
                                    Old(m.is_computed_attribute),
                                    Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.inherited_doc)))
    # Otherwise the docstring is left exactly as it was.
    Ensures(Implies(not fills_docstring(Old(m.is_callable_member),
                                        Old(m.is_computed_attribute),
                                        Old(m.is_public), Old(m.has_own_doc)),
                    m.doc == Old(m.doc)))
    # post-conditions-end
    # impl-start
    # Pre-patch: only an ordinary callable member is considered eligible; a
    # computed-attribute member is overlooked, so its missing docstring is
    # never filled from the bases.
    if m.is_callable_member and m.is_public and not m.has_own_doc:
        m.doc = m.inherited_doc
    # impl-end
