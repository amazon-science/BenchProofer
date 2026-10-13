"""Twin-artifact model for sphinx-doc__sphinx-7889.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an unavailable import must support
  being *subscripted* by an arbitrary index value and, for ANY such index,
  yield a fresh placeholder whose human-readable display name is

      <module> "." <text-of-the-index>

  where <text-of-the-index> is the canonical textual rendering of whatever
  index value was supplied.  The index need NOT already be textual: a
  non-textual index (e.g. a type parameter used to write a parametrised
  generic) is just as valid as a textual one, and the operation must still
  succeed and name the result after the index's textual rendering.

  The helper that fabricates the placeholder subclass is defined ONLY for an
  honest textual name: it builds the display name by textual concatenation and
  uses the name to construct the subclass.  Both require an honest string, and
  constructing the subclass additionally rejects a name carrying a NUL code
  point or a surrogate code point (neither has a valid encoded-text form for a
  class name).

A value is modelled as a pair (is_text, text): `text` is the `List[int]` of
Unicode code points of its canonical textual rendering, and `is_text` records
whether the value is *already* textual.  Textual rendering is total: every
value has a rendering and the rendering is itself textual, so handing the
rendering on always satisfies a string-only consumer, whereas handing a raw
subscript value on only does so when that value was already textual.  The
subclass-fabrication helper is the unchanged callee, modelled by the
`@ContractOnly` contract `display_name`, whose precondition is exactly that its
name argument is an honest textual name (validated == the real helper by
axiom_check.py / G-AX).

Subscripting is bounded work — render the index, fabricate the placeholder,
materialise its display name — and must actually RETURN that placeholder to
its caller.  A partial-correctness reading would let a diverging body satisfy
the display-name postcondition vacuously, so the contract carries an explicit
total-correctness obligation (MustTerminate).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def display_name(name_is_text: bool, name: PSeq[int],
                 module: PSeq[int]) -> PSeq[int]:
    """The unchanged placeholder-subclass fabricator, abstracted to the one
    observable property the subscript behaviour pins: the display name it
    assigns is `module`, a single separator code point, then `name`.

    It is DEFINED ONLY for a textual `name` (`name_is_text`) whose code points
    are all honest scalar values: no NUL (code point 0) and no surrogate code
    point (55296..57343).  The body concatenates `name` onto a string (failing
    for a non-textual argument) AND constructs a class object named `name` --
    class construction rejects a name containing a NUL code point, and it also
    rejects a surrogate code point because a surrogate has no encoded-text
    form for the class name.  All three halves of this precondition are the
    weakest the proof needs and match the real helper -- it claims nothing on
    inputs the real helper rejects.  Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX).
    """
    Requires(name_is_text and not (0 in name))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(name),
        not (55296 <= name[k] and name[k] <= 57343))))
    Ensures(Result() == module + PSeq(46) + name)   # 46 == ord('.')
# axioms-end


# pure-start
@Pure
def render_text(value_text: PSeq[int]) -> PSeq[int]:
    """Canonical textual rendering of a value, as the code-point sequence of
    its text.  Rendering is the identity on the text content (every value
    already carries its canonical textual form here); crucially its result is
    always textual, regardless of whether the value itself was textual."""
    Ensures(Result() == value_text)
    return value_text
# pure-end


def subscript_placeholder(key_is_text: bool, key_text: List[int],
                          module: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(key_text), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The index's textual rendering consists of honest scalar code points: no
    # interior NUL (code point 0) and no surrogate code point (55296..57343).
    # True of the textual rendering of every index the operation must handle
    # (type parameters, types, numbers, ordinary names), and required by the
    # string-only fabricator, which rejects a name carrying either kind of
    # non-scalar code point.
    Requires(not (0 in ToSeq(key_text)))
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(key_text),
        not (55296 <= ToSeq(key_text)[k] and ToSeq(key_text)[k] <= 57343))))
    # TERMINATION: subscripting must actually DELIVER the placeholder -- it is
    # bounded work (render the index, fabricate, materialise the display
    # name).  Nagini is a partial-correctness verifier by default, so without
    # this obligation an implementation that diverges before returning would
    # satisfy the display-name postcondition vacuously yet never produce the
    # placeholder; the real operation always returns one.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(key_text), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The display name of the produced placeholder is the module, a single
    # separator code point, then the textual rendering of the index -- and this
    # holds for EVERY index, textual or not (the postcondition does NOT assume
    # key_is_text).  This is exactly the display name the textual-only fabricator
    # assigns to a name handed to it (its Ensures: module ++ [sep] ++ name); here
    # the name is the index's textual rendering.
    Ensures(ToSeq(Result())
            == ToSeq(module) + PSeq(46) + render_text(ToSeq(key_text)))
    # post-conditions-end
    # impl-start
    # Reduce the index to its textual rendering FIRST, so the string-only
    # fabricator receives an honest string for EVERY index.  The rendering is
    # always textual, so the fabricator's textual precondition (name_is_text)
    # is met unconditionally -- independent of key_is_text.
    name_is_text = True
    name = render_text(ToSeq(key_text))
    # Hand the (now textual) name to the fabricator; its textual precondition
    # name_is_text is discharged here.  This call is the operation that fails
    # for a non-textual name argument.
    produced = display_name(name_is_text, name, ToSeq(module))
    Assert(produced == ToSeq(module) + PSeq(46) + name)
    # Materialise the display name the fabricator describes.
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # Bounded loop: the strictly decreasing, bounded-below measure
        # len(module) - i discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(module) - i + 1))
        # invariants-end
        result = result + [module[i]]
        Assert(ToSeq(module).take(i) + PSeq(module[i]) == ToSeq(module).take(i + 1))
        i = i + 1
    Assert(ToSeq(result) == ToSeq(module))
    result = result + [46]
    j = 0
    while j < len(key_text):
        # invariants-start
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(key_text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(key_text))
        Invariant(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text).take(j))
        # Bounded loop: measure len(key_text) - j, strictly decreasing and
        # bounded below, discharges the caller-held termination obligation.
        Invariant(MustTerminate(len(key_text) - j + 1))
        # invariants-end
        result = result + [key_text[j]]
        Assert(ToSeq(key_text).take(j) + PSeq(key_text[j]) == ToSeq(key_text).take(j + 1))
        j = j + 1
    Assert(ToSeq(result) == ToSeq(module) + PSeq(46) + ToSeq(key_text))
    return result
    # impl-end
