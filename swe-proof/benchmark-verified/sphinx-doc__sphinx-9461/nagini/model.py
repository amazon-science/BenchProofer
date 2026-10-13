"""Twin-artifact model for sphinx-doc__sphinx-9461.

Two desired behaviours are specified (stated as desired behaviour, not as an
edit). Both concern how a property whose binding is at the class level is
rendered.

== Behaviour 1: the qualifier prefix ==

  A property description carries a textual qualifier prefix assembled from a
  predetermined ordered vocabulary of role words, each word emitted in canonical
  order and followed by a single separating space (so the whole prefix ends with
  a trailing space). The word `property` is ALWAYS present and is the LAST word.
  Two optional qualifiers may precede it, in this canonical order:

    1. the abstractness qualifier `abstract`, present iff the description is
       marked abstract;
    2. the class-level qualifier `class`, present iff the description is marked
       as bound at the class level.

  Thus the prefix for an ordinary property is `property `; an abstract
  property is `abstract property `; a class-level property is `class property `;
  a property that is both is `abstract class property `. The class-level
  qualifier must contribute its own word even when the abstractness qualifier
  is absent.

== Behaviour 2: discovery and option-line emission ==

  When a member of a class is examined for automatic documentation, a member
  qualifies for documentation as a property when it is a property, AND ALSO when
  it is a class-level property (a property whose access is bound at the class
  level). A member that is neither does not qualify. Only a member that
  qualifies has documentation emitted for it at all.

  For a member that qualifies, an ordered block of option lines is emitted. The
  abstractness option line is emitted iff the member is marked abstract; the
  class-level option line is emitted iff the member is a class-level property.
  The class-level option line must therefore appear for a class-level property
  and must be absent for an ordinary property.

  Emission is gated on qualification: the option block for a member is produced
  only after that member has been established as documentable (capability
  `documented_as_property` below). A member that is not established as
  documentable has no option block.

== Behaviour 3: retention in the enclosing-class member walk ==

  When the members of an enclosing class are walked to decide which to document,
  a member is retained for documentation iff its own descriptive text can be
  resolved (an undocumented member is dropped). For a class-level property the
  descriptive text IS resolvable -- it is the text carried by the underlying
  property -- so a class-level property that has descriptive text is retained,
  exactly like an ordinary property; it is NOT dropped on the grounds that its
  class-level binding hides the text.

  Retention is the gate for the enclosing-class walk's emission: the option
  block is produced for a walked member only after that member has been retained
  (capability `retained_in_class_walk` below). A member that is not retained has
  no option block in the walk.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`. Both the prefix and the
emitted option block are modelled deeply as front-recursive concatenations of
the present words/lines.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees. Behaviour 1's assembled prefix and behaviour 2's
# emitted option block are both per-element concatenations, modelled deeply in
# the pure region; the string-join behaviour the real code relies on is
# validated == the real callee by axiom_check.py / G-AX.)
#
# `documented_as_property` is an abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# ESTABLISHED as documentable-as-a-property. An implementation cannot `Fold` it
# into existence (no body), and it names the specific member identifier, so a
# capability obtained for a different member does not discharge it. Its SOLE
# producer is `establish_documented` below -- the abstract "register this member
# as documentable" step the discovery decision performs on its qualifying
# branch. The option-block emission REQUIRES it, so an option block can be
# produced only for a member the discovery step actually established as
# documentable: the control-flow effect (a class-level property is
# discovered/documented at all) is tied to the discovery step, not to a copyable
# flag nor an answer-key oracle on the result.
@ContractOnly
@Predicate
def documented_as_property(member_id: int) -> bool:
    pass


@ContractOnly
def establish_documented(member_id: int) -> None:
    """The abstract "register this member as documentable" effect. It is the
    SOLE producer of the `documented_as_property` capability for `member_id`;
    the discovery decision performs it exactly on its qualifying branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(documented_as_property(member_id))


# `retained_in_class_walk` is a second abstract, unforgeable capability (a
# `@ContractOnly @Predicate` with no body) recording that a member has been
# RETAINED by the enclosing-class member walk -- i.e. its descriptive text was
# resolvable, so it survived the walk's drop-the-undocumented filter. As with
# `documented_as_property`, an implementation cannot `Fold` it into existence
# and it names the specific member, so a capability for another member does not
# discharge it. Its SOLE producer is `establish_retained` below -- the abstract
# "keep this walked member" step the retention decision performs exactly on its
# retain branch. The enclosing-class walk's option-block emission REQUIRES it,
# so that block is produced only for a member the walk actually retained: the
# control-flow effect (a class-level property survives the walk and is documented
# at all) is tied to the retention step, not to a copyable flag nor an answer-key
# oracle on the result.
@ContractOnly
@Predicate
def retained_in_class_walk(member_id: int) -> bool:
    pass


@ContractOnly
def establish_retained(member_id: int) -> None:
    """The abstract "keep this walked member" effect. It is the SOLE producer of
    the `retained_in_class_walk` capability for `member_id`; the retention
    decision performs it exactly on its retain branch.
    It is a single bounded registration step; the strictly smaller measure
    (1 < 2) lets a contracted caller holding MustTerminate(2) invoke it
    without leaking its own termination obligation."""
    Requires(MustTerminate(1))
    Ensures(retained_in_class_walk(member_id))
# axioms-end


# pure-start
@Pure
def word_abstract() -> PSeq[int]:
    # 'abstract'
    return PSeq(97, 98, 115, 116, 114, 97, 99, 116)


@Pure
def word_class() -> PSeq[int]:
    # 'class'
    return PSeq(99, 108, 97, 115, 115)


@Pure
def word_property() -> PSeq[int]:
    # 'property'
    return PSeq(112, 114, 111, 112, 101, 114, 116, 121)


@Pure
def space() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def line_abstract() -> PSeq[int]:
    # '   :abstractmethod:'
    return PSeq(32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def line_class() -> PSeq[int]:
    # '   :classmethod:'
    return PSeq(32, 32, 32, 58, 99, 108, 97, 115, 115,
                109, 101, 116, 104, 111, 100, 58)


@Pure
def expected_prefix(has_abstract: bool, has_classlevel: bool) -> PSeq[int]:
    """The canonical qualifier prefix as a sequence of code points: each
    present role word, in order, suffixed by one space. `property` always
    present and last; `abstract` then `class` precede it when present."""
    result = space().take(0)  # type: PSeq[int]
    if has_abstract:
        result = result + word_abstract() + space()
    if has_classlevel:
        result = result + word_class() + space()
    return result + word_property() + space()


@Pure
def expected_option_block(is_abstract: bool, is_classlevel: bool) -> PSeq[int]:
    """The canonical option block emitted for a qualifying property member, as a
    sequence of code points: the abstractness option line present iff abstract,
    then the class-level option line present iff the member is a class-level
    property, each in canonical order."""
    result = space().take(0)  # type: PSeq[int]
    if is_abstract:
        result = result + line_abstract()
    if is_classlevel:
        result = result + line_class()
    return result
# pure-end


def property_qualifier_prefix(has_abstract: bool, has_classlevel: bool) -> List[int]:
    # pre-conditions-start
    # TERMINATION: assembling the prefix is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation). Nagini
    # is a partial-correctness verifier by default, so without this obligation
    # a non-terminating implementation (e.g. bare self-recursion) would
    # satisfy every Ensures vacuously; the real assembly always delivers its
    # prefix to the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The assembled prefix is exactly the per-word concatenation, each present
    # role word suffixed by a space, `property` always present and last.
    Ensures(ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if has_abstract:
        result = result + [97, 98, 115, 116, 114, 97, 99, 116]
        result = result + [32]
    if has_classlevel:
        result = result + [99, 108, 97, 115, 115]
        result = result + [32]
    result = result + [112, 114, 111, 112, 101, 114, 116, 121]
    result = result + [32]
    return result
    # impl-end


def qualifies_for_property_doc(is_property: bool,
                               is_classlevel_property: bool,
                               member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the discovery decision is a bounded prologue over two flags
    # and MUST terminate (a total-correctness obligation); otherwise a
    # non-terminating implementation would satisfy every Ensures vacuously.
    # Measure 3 dominates the registration step (1) and the gated emission (2),
    # so the decision may invoke either without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A member qualifies for documentation as a property iff it is a property
    # OR it is a class-level property. Qualification grants the unforgeable
    # `documented_as_property` capability for THIS member, and only then.
    Ensures(Result() == (is_property or is_classlevel_property))
    Ensures(Implies(Result(), documented_as_property(member_id)))
    # post-conditions-end
    # impl-start
    if is_property:
        establish_documented(member_id)
        return True
    if is_classlevel_property:
        establish_documented(member_id)
        return True
    return False
    # impl-end


def property_option_block(is_abstract: bool,
                          is_classlevel_property: bool,
                          member_id: int) -> List[int]:
    # pre-conditions-start
    # The option block is emitted only for a member already established as
    # documentable: holding the `documented_as_property` capability for THIS
    # member is required to emit anything.
    Requires(documented_as_property(member_id))
    # TERMINATION: emitting the option block is a bounded, straight-line
    # computation and MUST terminate (a total-correctness obligation);
    # otherwise a non-terminating implementation would satisfy every Ensures
    # vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The emitted option block is exactly the canonical block: the abstractness
    # line iff abstract, then the class-level line iff the member is a
    # class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end


def member_retained_in_class_walk(is_classlevel_property: bool,
                                  has_descriptive_text: bool,
                                  member_id: int) -> bool:
    # pre-conditions-start
    # TERMINATION: the retention decision is a bounded prologue over the
    # walked member's flags and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously. Measure 3 dominates the registration step (1)
    # and the gated walk emission (2), so the decision may invoke either
    # without leaking its own obligation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # A walked member is retained iff its own descriptive text resolves. For a
    # class-level property the descriptive text DOES resolve (it is the text of
    # the underlying property), so retention depends only on whether the member
    # has descriptive text -- a class-level property is retained on the same
    # footing as an ordinary property, never dropped for being class-level.
    Ensures(Result() == has_descriptive_text)
    # Retention grants the unforgeable `retained_in_class_walk` capability for
    # THIS member, and only on the retain branch.
    Ensures(Implies(Result(), retained_in_class_walk(member_id)))
    # post-conditions-end
    # impl-start
    text_resolves = has_descriptive_text
    if text_resolves:
        establish_retained(member_id)
        return True
    return False
    # impl-end


def class_walk_option_block(is_abstract: bool,
                            is_classlevel_property: bool,
                            member_id: int) -> List[int]:
    # pre-conditions-start
    # The enclosing-class walk emits an option block only for a member it has
    # retained: holding the `retained_in_class_walk` capability for THIS member
    # is required to emit anything in the walk.
    Requires(retained_in_class_walk(member_id))
    # TERMINATION: emitting the walk's option block is a bounded,
    # straight-line computation and MUST terminate (a total-correctness
    # obligation); otherwise a non-terminating implementation would satisfy
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The block emitted in the walk is exactly the canonical block: the
    # abstractness line iff abstract, then the class-level line iff the member
    # is a class-level property.
    Ensures(ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel_property))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if is_abstract:
        result = result + [32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,
                           109, 101, 116, 104, 111, 100, 58]
    if is_classlevel_property:
        result = result + [32, 32, 32, 58, 99, 108, 97, 115, 115,
                           109, 101, 116, 104, 111, 100, 58]
    return result
    # impl-end
