"""Twin-artifact model for sympy__sympy-15976.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A named quantity is rendered to a small presentation-markup tree. The name may
  carry an ordered list of subscript parts and an ordered list of superscript
  parts; the renderer chooses one of four ROOT element kinds purely from whether
  those two lists are empty:

      no subscripts and no superscripts  -> an identifier element (`mi`)
      subscripts only                    -> a subscript element (`msub`)
      superscripts only                  -> a superscript element (`msup`)
      both                               -> a sub-and-superscript element (`msubsup`)

  The chosen kind is the ROOT of the produced tree. Its direct children are, in
  order: the identifier element holding the base name FIRST, then the rendered
  subscript group and/or superscript group as the kind requires (subscript group
  before superscript group for the combined kind). A group of a SINGLE part is
  rendered as a bare identifier element; a group of more than one part is
  rendered as a grouping element. The base-name identifier and the rendered
  sub/super groups are the immediate (depth-one) children of this structural
  root.

  When a bold style is requested, the bold-font marker is set on the ROOT of the
  produced tree (whichever of the four kinds it is).

  Rendering is TOTAL: every name the renderer accepts is rendered to such a tree
  in a bounded number of steps. The structural claims above are obligations on
  every invocation, not merely on those invocations that happen to produce a
  result, so a renderer that consumes a name and yields no tree — for any reason
  — has not met them.

A markup element is modelled by the only facets the rendered tree exposes to a
consumer: its element kind (`tag`, an int code), the ordered kinds of its DIRECT
children (`ctags`, a `List[int]`), and the bold-font marker (`bold`). `tag`
mirrors the DOM `nodeName` of the element. `ctags[i]` mirrors the `nodeName` of
`childNodes[i]`, refined by ROLE identity: a consumer reads each child's own
content and the slot it occupies, so two children filling different roles are
never interchangeable even when they are the same element kind. Each child
therefore carries a code naming its role together with its kind — the identifier
holding the base name; the subscript group as one part or as several; the
superscript group as one part or as several. A group's role is determined by
which of the two ordered part lists it renders, never by the element kind it
happens to take, so the subscript slot and the superscript slot of the combined
kind stay distinguishable even when both groups render to the same kind. `print_symbol` is
the verified builder.

No callee is axiomatized for the tree construction: the structural choice is pure
logic, modelled deeply. The name/sub/super decomposition of the textual name is
performed by an unchanged community helper, whose result is abstracted to the two
emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as an
A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly. Markers
(machine-parsed) delimit spec/proof/impl.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# ROOT element-kind codes (abstract DOM tag identities).
TAG_MI = 1       # identifier element
TAG_MSUB = 2     # subscript element
TAG_MSUP = 3     # superscript element
TAG_MSUBSUP = 4  # sub-and-superscript element
# Direct-CHILD codes. A child is identified by the ROLE it fills as well as by
# its element kind, so children in different roles are never interchangeable
# even when they share an element kind — see the module docstring.
TAG_MNAME = 6      # the identifier child carrying the base name
TAG_SUB_ONE = 7    # the SUBSCRIPT group, one part      -> an identifier element
TAG_SUB_ROW = 8    # the SUBSCRIPT group, several parts -> a grouping element
TAG_SUP_ONE = 9    # the SUPERSCRIPT group, one part      -> an identifier element
TAG_SUP_ROW = 10   # the SUPERSCRIPT group, several parts -> a grouping element


# axioms-start
# (No consumed axioms. The structural choice of root element kind, and the
# placement of the base-name identifier and of each script group in its own
# DIRECT-child slot of that structural root, are pure logic — modelled deeply by
# the pure functions below and the
# verified `print_symbol` builder. The only callee the real code invokes here is
# the unchanged name-decomposition helper, whose result is abstracted to the two
# emptiness flags `has_subs` / `has_supers` taken as inputs; it is validated as
# an A-reference by axiom_check.py / G-AX, not consumed as a @ContractOnly.
# G-EQ audits the refinement against the real builder.)
# axioms-end


# pure-start
class MNode:
    """One element of the produced markup tree, abstracted to the facets a
    consumer observes: its element kind `tag`, the ordered kinds of its direct
    children `ctags` (mirroring the DOM node's `childNodes[i].nodeName`), and the
    bold-font marker `bold`."""

    def __init__(self, tag: int, ctags: List[int]) -> None:
        Requires(Acc(list_pred(ctags)))
        # Making an element is likewise total: it always yields the element.
        Requires(MustTerminate(1))
        Ensures(Acc(node_pred(self)))
        Ensures(node_tag(self) == tag)
        Ensures(node_ctags(self) == Old(ToSeq(ctags)))
        Ensures(node_bold(self) == False)
        self.tag = tag
        self.ctags = ctags
        self.bold = False
        Fold(node_pred(self))


@Predicate
def node_pred(n: MNode) -> bool:
    return Acc(n.tag) and Acc(n.ctags) and Acc(list_pred(n.ctags)) and Acc(n.bold)


@Pure
def node_tag(n: MNode) -> int:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.tag)


@Pure
def node_bold(n: MNode) -> bool:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), n.bold)


@Pure
def node_ctags(n: MNode) -> PSeq[int]:
    Requires(Acc(node_pred(n), 1 / 2))
    return Unfolding(Acc(node_pred(n), 1 / 2), ToSeq(n.ctags))


@Pure
def root_tag_for(has_subs: bool, has_supers: bool) -> int:
    """The structural ROOT kind chosen purely from the two emptiness flags."""
    if not has_supers and not has_subs:
        return TAG_MI
    if not has_supers:
        return TAG_MSUB
    if not has_subs:
        return TAG_MSUP
    return TAG_MSUBSUP


@Pure
def sub_group_tag(multi: bool) -> int:
    """The code of the rendered SUBSCRIPT group: a grouping element when it holds
    more than one part, a bare identifier element for a single part. The code
    names the subscript role, so this group is never interchangeable with the
    superscript group."""
    if multi:
        return TAG_SUB_ROW
    return TAG_SUB_ONE


@Pure
def sup_group_tag(multi: bool) -> int:
    """The code of the rendered SUPERSCRIPT group: a grouping element when it
    holds more than one part, a bare identifier element for a single part. The
    code names the superscript role, so this group is never interchangeable with
    the subscript group."""
    if multi:
        return TAG_SUP_ROW
    return TAG_SUP_ONE


@Pure
def child_tags_for(has_subs: bool, has_supers: bool,
                   subs_multi: bool, supers_multi: bool) -> PSeq[int]:
    """The required direct children (role-and-kind codes, in order) of the
    structural root: the base-name identifier FIRST, then the subscript group
    and/or the superscript group as the chosen kind demands, the subscript group
    preceding the superscript group. A single-part group is an identifier; a
    multi-part group is a grouping element. Each group's code names the part
    list it renders, so the sequence pins WHICH group occupies each slot and not
    merely how many slots there are and what element kinds fill them. Empty for
    the bare identifier kind (the name text is its own text content, carrying no
    element child)."""
    if not has_supers and not has_subs:
        return PSeq(TAG_MNAME).take(0)                             # no element kids
    if not has_supers:
        return PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi))   # mname, subs
    if not has_subs:
        return PSeq(TAG_MNAME) + PSeq(sup_group_tag(supers_multi))  # mname, supers
    return (PSeq(TAG_MNAME) + PSeq(sub_group_tag(subs_multi)) +
            PSeq(sup_group_tag(supers_multi)))                     # mname, subs, sup
# pure-end


def print_symbol(name: List[int], has_subs: bool, has_supers: bool,
                 subs_multi: bool, supers_multi: bool, bold: bool) -> MNode:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    # The rendering is a TOTAL obligation: the postconditions below are claimed
    # of EVERY invocation, not merely of the ones that happen to reach a return.
    # A renderer that consumes a name and never yields a tree has not rendered
    # it. Level 2, not 1, because building the child-kind list invokes a
    # constructor that carries its own obligation and needs room strictly below
    # the renderer's level.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(node_pred(Result())))
    # The ROOT is the structural kind chosen purely from the emptiness flags.
    Ensures(node_tag(Result()) == root_tag_for(has_subs, has_supers))
    # The base-name identifier (and any sub/super groups) are the depth-one
    # direct children of the structural root, in order. Each group is an
    # identifier for a single part, a grouping element for several, and each
    # occupies the slot of the part list it renders: the subscript group's slot
    # precedes the superscript group's, and the two are not interchangeable even
    # when both render to the same element kind.
    Ensures(node_ctags(Result()) ==
            child_tags_for(has_subs, has_supers, subs_multi, supers_multi))
    # The bold-font marker lands on the produced root.
    Ensures(node_bold(Result()) == bold)
    # post-conditions-end
    # impl-start
    x = None  # type: Optional[MNode]
    sub_g = sub_group_tag(subs_multi)
    sup_g = sup_group_tag(supers_multi)
    if not has_supers:
        if not has_subs:
            # bare identifier: the name is its own text content, no element child
            kids = []  # type: List[int]
            x = MNode(TAG_MI, kids)
        else:
            kids = [TAG_MNAME, sub_g]   # mname, join(subs)
            x = MNode(TAG_MSUB, kids)
    else:
        if not has_subs:
            kids = [TAG_MNAME, sup_g]   # mname, join(supers)
            x = MNode(TAG_MSUP, kids)
        else:
            kids = [TAG_MNAME, sub_g, sup_g]  # mname, join(subs), join(supers)
            x = MNode(TAG_MSUBSUP, kids)
    # Set the bold marker on the produced root (touches only the marker; the
    # element kind and child kinds are unchanged).
    ct = node_ctags(x)
    tg = node_tag(x)
    Unfold(node_pred(x))
    x.bold = bold
    Fold(node_pred(x))
    Assert(node_ctags(x) == ct)
    Assert(node_tag(x) == tg)
    return x
    # impl-end
