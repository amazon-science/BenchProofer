"""Twin-artifact model for sphinx-doc__sphinx-8593.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documenter collects the members of a target module, each member's
  effective documentation is the inline attribute documentation recorded for
  that name in the module source (when such documentation exists), falling back
  to the value's own intrinsic documentation only when no attribute
  documentation is present. The visibility classification of a member is then
  derived from THAT effective documentation: a member is treated as public when
  its documentation carries the explicit "public" visibility marker, private
  when it carries the explicit "private" marker, and otherwise according to the
  leading-underscore naming convention. A member whose effective documentation
  marks it public is therefore retained even when its name begins with an
  underscore.

This bundle models two cooperating behaviours:

  (1) the effective documentation chosen for a module member (the attribute
      documentation takes precedence over the value's intrinsic documentation),
      and

  (2) the retention decision for a documented module member under the
      "all members" mode, given the visibility classification derived from (1)
      and the private-members selection mode.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); specifications are carried by `PSeq[int]` via `ToSeq`. The
visibility classifier of a documentation block (the unchanged community
metadata extractor) is axiomatized as `meta_class`; provenance and an
executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# Visibility classification of a documentation block (a community metadata
# extractor reads its explicit visibility marker):
#   0 = no explicit visibility marker
#   1 = explicit "public"  marker present
#   2 = explicit "private" marker present
# A pure total function of the documentation text. G-AX checks it against the
# real extractor.
NONE = 0  # type: int
PUBLIC = 1  # type: int
PRIVATE = 2  # type: int


@Pure
@ContractOnly
def meta_class(doc: PSeq[int]) -> int:
    Requires(True)
    Ensures(Result() == NONE or Result() == PUBLIC or Result() == PRIVATE)
    # The empty documentation block carries no marker.
    Ensures(Implies(len(doc) == 0, Result() == NONE))
# axioms-end


# pure-start
@Pure
def effective_doc(attr_doc: PSeq[int], value_doc: PSeq[int]) -> PSeq[int]:
    """The documentation that drives the visibility classification of a module
    member: the inline attribute documentation when it is non-empty, otherwise
    the value's own intrinsic documentation."""
    if len(attr_doc) > 0:
        return attr_doc
    return value_doc


@Pure
def is_private(name_underscored: bool, doc: PSeq[int]) -> bool:
    """Visibility classification of a member: an explicit public marker forces
    it public, an explicit private marker forces it private, otherwise the
    leading-underscore naming convention decides."""
    mc = meta_class(doc)
    if mc == PUBLIC:
        return False
    if mc == PRIVATE:
        return True
    return name_underscored


@Pure
def in_private_selection(mode: int, selected: bool) -> bool:
    """Whether a private member is selected for retention.
       mode 0: private-members not requested  -> never selected
       mode 1: all private members requested  -> always selected
       mode 2: an explicit list was given      -> selected iff listed."""
    Requires(mode == 0 or mode == 1 or mode == 2)
    if mode == 0:
        return False
    if mode == 1:
        return True
    return selected
# pure-end


def member_effective_doc(attr_doc: List[int], value_doc: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The attribute documentation takes precedence when present; only when it is
    # absent does the value's intrinsic documentation apply.
    Ensures(ToSeq(Result()) == effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: module members are collected without their inline
    # attribute documentation, so the effective documentation is always the
    # value's intrinsic documentation, ignoring any attribute documentation.
    result = list(value_doc)  # type: List[int]
    return result
    # impl-end


def keep_module_member(name_underscored: bool, name_special: bool,
                       attr_doc: List[int], value_doc: List[int],
                       want_all: bool, private_mode: int,
                       name_selected: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(attr_doc), 1 / 2))
    Requires(Acc(list_pred(value_doc), 1 / 2))
    Requires(private_mode == 0 or private_mode == 1 or private_mode == 2)
    # Modeled slice: a DOCUMENTED module member, i.e. one that carries some
    # documentation (inline attribute documentation or the value's own
    # documentation). A member with no documentation at all is decided by a
    # different, unmodeled retention branch and lies outside this boundary.
    Requires(len(attr_doc) > 0 or len(value_doc) > 0)
    # Modeled slice: an ORDINARILY NAMED member. A member whose name has the
    # reserved form (leading and trailing double underscore) is decided by a
    # separate, unmodeled retention branch that runs before the modeled one,
    # and lies outside this boundary.
    Requires(not name_special)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attr_doc), 1 / 2))
    Ensures(Acc(list_pred(value_doc), 1 / 2))
    # A documented module member is retained exactly per its visibility, which
    # is derived from its EFFECTIVE documentation (attribute documentation
    # preferred over intrinsic documentation).  A non-private member is always
    # retained; a private one only when the private-members selection picks it.
    Ensures(Result() == (
        (not want_all) or
        (not is_private(name_underscored,
                        effective_doc(ToSeq(attr_doc), ToSeq(value_doc)))) or
        in_private_selection(private_mode, name_selected)))
    # Discriminating consequence: a member carrying the explicit public marker
    # in its attribute documentation is retained regardless of an underscore
    # name and regardless of the private-members selection.
    Ensures(Implies(
        meta_class(effective_doc(ToSeq(attr_doc), ToSeq(value_doc))) == PUBLIC,
        Result()))
    # post-conditions-end
    # impl-start
    doc = member_effective_doc(attr_doc, value_doc)
    private = is_private(name_underscored, ToSeq(doc))
    if not want_all:
        keep = True
    elif not private:
        keep = True
    else:
        keep = in_private_selection(private_mode, name_selected)
    return keep
    # impl-end
