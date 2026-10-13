"""Twin-artifact model for sphinx-doc__sphinx-9591.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a documented object carries a declared type annotation, the rendered
  annotation group placed after the object name is built so that a type name it
  mentions becomes a CROSS-REFERENCE node (a node that links to the documented
  type) rather than inert literal text. Concretely, the annotation group is the
  literal separator text ": " emitted as its own plain-text node, followed by
  the nodes produced by parsing the annotation string with the shared annotation
  parser. A declared type that is a simple type name parses to exactly one node,
  and that node is a cross-reference carrying the name, so such an annotation
  renders as the separator followed by a single cross-reference. An object that
  declares no type annotation contributes no annotation group at all.

  What KIND of node each child of the group is, is part of the rendered result
  and not merely which characters it carries. Three kinds of child occur: a BARE
  TEXT node, which is nothing but the characters it renders and carries no inline
  markup role of its own; a CROSS-REFERENCE; and any other marked-up inline node,
  rendered punctuation among them. The separator child is a BARE TEXT node.
  Rendered punctuation carrying those same two characters is a DIFFERENT child —
  it is equally not a cross-reference, yet a consumer that reads the group's
  children apart by kind, as consumers of a rendered signature do, sees a bare
  text child and a marked-up one as two different renderings — so emitting it in
  the separator's place does not satisfy the requirement above. The children
  after the separator are exactly the parser's own nodes, each at the kind the
  parser gave it: the operation splices them and re-kinds none of them, and
  passes each through unaltered — it does not rebuild one, re-wrap one, or edit
  what any of them holds inside.

  A marked-up child is not only a kind, it also has an INSIDE: the run or runs of
  inline content it holds and draws its rendered text from. That too is part of
  the rendered result. A cross-reference whose whole label is one bare text run
  is a different rendering from one whose label is itself further marked up or
  split across several runs, even when the two spell the same characters, because
  a consumer reading the label apart from the node that carries it finds one run
  in the first and not in the second. A simple type name's cross-reference holds
  exactly one bare text run, the name; the separator child holds no inner node at
  all, being itself the run it renders.

  The group is furthermore an ANNOTATION node — the node kind a rendered
  signature uses to hold a declared annotation — and exactly one such node is
  contributed when an annotation is declared. Which node holds the children is
  the emitting operation's own choice, not the parser's, so it is pinned here:
  putting the same children inside some other inline wrapper contributes a
  different thing to the signature and does not satisfy the requirement above.

  The shared annotation parser is PARTIAL: it ACCEPTS most annotation strings
  and REJECTS some, and on a rejected string it yields no node list at all.
  Delegating to it therefore means inheriting that: when the declared annotation
  is one the parser rejects, no annotation group is rendered and the rejection
  propagates to the caller rather than being absorbed into some substitute
  rendering. A simple type name is always accepted, so the cross-referencing
  guarantee above is unconditional on that class.

The annotation string is modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing). The rendered annotation group is modelled as the four
parallel sequences the group's children induce plus one flag on the group node
itself: `is_xref[k]` is True iff child `k` is a cross-reference, `is_bare_text[k]`
is True iff child `k` is a bare text node, `holds_one_bare_text[k]` is True iff
child `k` holds exactly one inner node and that node is a bare text node,
`text[k]` is child `k`'s rendered text as `PSeq[int]`, and `is_annotation_node`
says the children are held in an annotation node. The kind flags are independent
observations of one child — a marked-up inline node that is not a cross-reference
reads False in both, and a bare text child holds no inner node so it reads False
in the third — so the sequences together distinguish kinds and insides that the
texts alone do not. The shared annotation parser is an unchanged callee: the
strings it accepts are axiomatized as `accepted`, its rendered output as the four
sequences `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts`, and its value level as
`rendered_nodes`; all are properties of the real parser's node list validated
out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AnnotationRejected(Exception):
    """The shared annotation parser REJECTS the declared annotation string: it
    yields no rendered node list for it, so no annotation group exists to
    produce. Modelled as a user-defined exception because a builtin one in an
    `Exsures` crashes the Nagini translator (mapping.md §2)."""


class AnnotationGroup:
    """The rendered annotation group: the sequences its children induce, and the
    kind of the node holding them.

    `is_xref[k]` is True iff child `k` is a cross-reference (a link to a
    documented object) and False for any other inline node (a bare text run,
    rendered punctuation). `is_bare_text[k]` is True iff child `k` is a BARE TEXT
    node — a child that is nothing but the characters it renders, carrying no
    inline markup role of its own — and False for every marked-up inline node,
    cross-references and rendered punctuation alike. `holds_one_bare_text[k]` is
    True iff child `k` holds exactly ONE inner node and that node is a bare text
    node: its whole rendered text comes from a single plain run held inside it.
    It is False for a bare text child (which holds no inner node, being itself
    the run it renders) and False for a marked-up child whose label is split
    across several runs or is itself further marked up. Reading the flags
    together therefore says which kind child `k` is and what it holds, and a
    child's text says nothing about either: a bare text run and a
    rendered-punctuation node may carry exactly the same characters and are still
    different children, as are two cross-references spelling the same name with
    different insides. `text[k]` is child `k`'s rendered text as a sequence of
    Unicode code points. The four sequences have equal length: one entry per
    child, in rendered order. `is_annotation_node` is True iff the children are
    held in an annotation node — the node kind a rendered signature uses for a
    declared annotation — and False when no such node is contributed at all.
    """

    def __init__(self, is_xref: PSeq[bool], text: PSeq[PSeq[int]],
                 is_bare_text: PSeq[bool], holds_one_bare_text: PSeq[bool],
                 is_annotation_node: bool) -> None:
        Requires(MustTerminate(1))
        self.is_xref = is_xref  # type: PSeq[bool]
        self.text = text  # type: PSeq[PSeq[int]]
        self.is_bare_text = is_bare_text  # type: PSeq[bool]
        self.holds_one_bare_text = holds_one_bare_text  # type: PSeq[bool]
        self.is_annotation_node = is_annotation_node  # type: bool
        Ensures(Acc(self.is_xref) and Acc(self.text) and Acc(self.is_bare_text)
                and Acc(self.holds_one_bare_text)
                and Acc(self.is_annotation_node))
        Ensures(self.is_xref == is_xref and self.text == text
                and self.is_bare_text == is_bare_text
                and self.holds_one_bare_text == holds_one_bare_text
                and self.is_annotation_node == is_annotation_node)


# pure-start
@Pure
def sep_text() -> PSeq[int]:
    # ": "  (the U+003A U+0020 separator emitted before a type annotation)
    return PSeq(58, 32)


@Pure
def no_kinds() -> PSeq[bool]:
    """The empty sequence of cross-reference flags: no children at all."""
    return PSeq(False).drop(1)


@Pure
def no_texts() -> PSeq[PSeq[int]]:
    """The empty sequence of child texts: no children at all."""
    return PSeq(sep_text()).drop(1)


@Pure
def is_name_start(c: int) -> bool:
    # A-Z, a-z, _ : the code points a simple type name may begin with.
    return (65 <= c and c <= 90) or (97 <= c and c <= 122) or c == 95


@Pure
def is_name_char(c: int) -> bool:
    # a name-start code point or a digit 0-9.
    return is_name_start(c) or (48 <= c and c <= 57)


@Pure
def is_simple_name(s: PSeq[int]) -> bool:
    """A simple type name: a non-empty run of name characters that does not
    begin with a digit (e.g. the documented class a property's type names)."""
    return len(s) > 0 and is_name_start(s[0]) and Forall(int, lambda k: (
        Implies(0 <= k and k < len(s), is_name_char(s[k])), [[s[k]]]))
# pure-end


# axioms-start
@Pure
@ContractOnly
def accepted(s: PSeq[int]) -> bool:
    """The shared annotation parser's DOMAIN: True iff it accepts `s` and so
    yields a rendered node list for it. The parser is PARTIAL — some strings it
    rejects outright, yielding no node list — so `annotation_kinds` /
    `annotation_texts` are defined only where this holds. Relied-on fact: a
    SIMPLE type name is always accepted. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Ensures(Implies(is_simple_name(s), Result()))


@Pure
@ContractOnly
def annotation_kinds(s: PSeq[int]) -> PSeq[bool]:
    """The shared annotation parser's rendered output on an ACCEPTED string,
    cross-reference flags: entry `k` is True iff the parser's `k`-th node is a
    cross-reference. An accepted string with no content yields no nodes.
    Relied-on fact: a SIMPLE type name renders to exactly one node and that node
    IS a cross-reference. Unchanged callee the rendering delegates to;
    provenance + executable soundness in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))


@Pure
@ContractOnly
def annotation_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output's other kind flags: entry `k` is True iff the
    parser's `k`-th node is a BARE TEXT node rather than a marked-up inline one.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node is NOT a bare text node — it is the
    cross-reference `annotation_kinds` reports, and a cross-reference carries an
    inline markup role, so it reads False here. That is the same single
    measurement `annotation_kinds`' simple-name fact rests on, read on the other
    flag, so this axiom asserts nothing about the parser beyond what
    axiom_check.py already observes of it: one node, and that node a
    cross-reference. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(False)))


@Pure
@ContractOnly
def annotation_holds_one_bare_text(s: PSeq[int]) -> PSeq[bool]:
    """The same parser output read one level in: entry `k` is True iff the
    parser's `k`-th node holds exactly ONE inner node and that node is a bare
    text node — its whole rendered text comes from a single plain run inside it.
    One entry per node, so its length agrees with `annotation_kinds`. Relied-on
    fact: a SIMPLE type name's single node holds exactly one bare text run,
    namely the name itself, so it reads True here. That is the same node
    `annotation_kinds` / `annotation_texts` report on, read on what it holds
    rather than on its kind or its characters, and it is what makes a
    cross-reference whose label is one plain run distinguishable from one
    spelling the same name with a different inside. Unchanged callee; provenance
    in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(True)))


@Pure
@ContractOnly
def annotation_texts(s: PSeq[int]) -> PSeq[PSeq[int]]:
    """The same parser output's rendered texts: entry `k` is the `k`-th node's
    text. One entry per node, so its length agrees with `annotation_kinds`.
    Relied-on fact: a SIMPLE type name's single node carries that name as its
    text. Unchanged callee; provenance in mapping.md / axiom_check.py.
    """
    Requires(accepted(s))
    Ensures(len(Result()) == len(annotation_kinds(s)))
    Ensures(Implies(is_simple_name(s), Result() == PSeq(s)))


@ContractOnly
def rendered_nodes(typ: List[int]) -> AnnotationGroup:
    """Runtime form of the shared annotation parser, at the value level: handed
    an ACCEPTED string it yields that string's rendered node list (the value of
    `annotation_kinds` / `annotation_bare_text` /
    `annotation_holds_one_bare_text` / `annotation_texts`); handed one
    it REJECTS it yields no
    node list and signals `AnnotationRejected` instead. Which strings it accepts
    is not something the caller decides — returning normally is itself the
    witness that the argument was accepted. The nodes it yields come out at the
    kinds it gave them and with the insides it gave them: those flags are read
    off that very node list, so a caller that splices them can pass them along
    unaltered but has no node of its own at those positions to substitute. Its
    result carries no `is_annotation_node` claim: a bare node list is not held in
    anything, and which node holds the spliced children is the CALLER's choice,
    which is why the operation below must pin it. Unchanged callee; provenance +
    executable soundness in mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    Ensures(accepted(ToSeq(typ)))
    Ensures(Result().is_xref == annotation_kinds(ToSeq(typ)))
    Ensures(Result().text == annotation_texts(ToSeq(typ)))
    Ensures(Result().is_bare_text == annotation_bare_text(ToSeq(typ)))
    Ensures(Result().holds_one_bare_text
            == annotation_holds_one_bare_text(ToSeq(typ)))
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2) and not accepted(ToSeq(typ)))
# axioms-end


def handle_property_annotation(present: bool, typ: List[int]) -> AnnotationGroup:
    # `present` is True iff a non-empty type annotation was declared (the
    # operation's guard); `typ` carries that annotation's code points.
    # pre-conditions-start
    Requires(Acc(list_pred(typ), 1 / 2))
    Requires(Implies(present, len(typ) > 0))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(typ), 1 / 2))
    Ensures(Acc(Result().is_xref) and Acc(Result().text)
            and Acc(Result().is_bare_text)
            and Acc(Result().holds_one_bare_text)
            and Acc(Result().is_annotation_node))
    # One entry per rendered child.
    Ensures(len(Result().is_xref) == len(Result().text))
    Ensures(len(Result().is_bare_text) == len(Result().is_xref))
    Ensures(len(Result().holds_one_bare_text) == len(Result().is_xref))
    # No declared annotation -> no annotation group is produced.
    Ensures(Implies(not present, len(Result().is_xref) == 0))
    # A declared annotation contributes exactly one ANNOTATION node holding the
    # children below, and a declared-nothing contributes no such node. WHICH node
    # holds them is this operation's own choice, never the parser's, so putting
    # the same children inside any other inline wrapper is a different
    # contribution to the rendered signature and does not discharge this.
    Ensures(Result().is_annotation_node == present)
    # RETURNING A GROUP AT ALL means the annotation was one the shared parser
    # ACCEPTS: the rendering is delegated to that parser, so its domain is the
    # domain on which a group exists. (This clause also makes the ones below
    # well-defined, since `annotation_kinds` / `annotation_bare_text` /
    # `annotation_holds_one_bare_text` / `annotation_texts` are only defined on
    # an accepted string; it must therefore precede them.)
    Ensures(Implies(present, accepted(ToSeq(typ))))
    # A declared annotation produces, in order: the literal ": " separator as a
    # plain-text node, then the nodes the annotation parser renders.
    Ensures(Implies(present,
                    Result().is_xref == PSeq(False) + annotation_kinds(ToSeq(typ))))
    Ensures(Implies(present,
                    Result().text == PSeq(sep_text()) + annotation_texts(ToSeq(typ))))
    # The KIND of each of those children, not just its text: the separator is a
    # BARE TEXT child — carrying the separator's characters as rendered
    # punctuation, or as any other marked-up inline node, is a different child and
    # does not discharge this — and each child after it keeps the kind the
    # annotation parser gave it, the splice re-kinding none of them.
    Ensures(Implies(present,
                    Result().is_bare_text
                    == PSeq(True) + annotation_bare_text(ToSeq(typ))))
    # And what each child HOLDS, one level in: the separator holds no inner node,
    # being itself the run it renders, while every child after it keeps the inside
    # the annotation parser gave it — so rebuilding one of the parser's nodes with
    # the same kind and the same characters but a different inside (its label
    # split across several runs, or wrapped in further markup) is a different
    # child and does not discharge this either.
    Ensures(Implies(present,
                    Result().holds_one_bare_text
                    == PSeq(False) + annotation_holds_one_bare_text(ToSeq(typ))))
    # A declared SIMPLE type name is therefore rendered through a CROSS-REFERENCE
    # node, never as a single inert text run: the group is the separator, a bare
    # text child holding no inner node, followed by exactly one cross-reference
    # carrying the type name as one bare text run inside it.
    Ensures(Implies(present and is_simple_name(ToSeq(typ)),
                    Result().is_xref == PSeq(False, True)
                    and Result().text == PSeq(sep_text(), ToSeq(typ))
                    and Result().is_bare_text == PSeq(True, False)
                    and Result().holds_one_bare_text == PSeq(False, True)))
    # An annotation the shared parser REJECTS yields no annotation group: the
    # rejection propagates, unabsorbed, and the declared annotation is left
    # untouched. Together with the clause above this is exhaustive: on a declared
    # annotation the operation returns the delegated group where the parser
    # accepts and signals where it rejects, and nothing else on either side.
    Exsures(AnnotationRejected,
            Acc(list_pred(typ), 1 / 2)
            and present and not accepted(ToSeq(typ)))
    # post-conditions-end
    # impl-start
    if present:
        one_kind = PSeq(False)  # type: PSeq[bool]
        one_text = PSeq(sep_text() + ToSeq(typ))  # type: PSeq[PSeq[int]]
        one_bare = PSeq(True)  # type: PSeq[bool]
        one_holds = PSeq(False)  # type: PSeq[bool]
        return AnnotationGroup(one_kind, one_text, one_bare, one_holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
    # impl-end
