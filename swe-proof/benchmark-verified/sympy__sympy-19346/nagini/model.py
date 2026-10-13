"""Twin-artifact model for sympy__sympy-19346.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An executable textual representation of a symbolic expression must render the
  built-in associative-mapping and unordered-collection containers so that the
  text re-creates the object when read back. Two container kinds are covered.

  (1) Unordered collection. An empty collection is rendered as the literal
      five-character form  set()  . A non-empty collection is rendered as an
      opening brace, then EVERY element rendered in turn -- each element by the
      same executable element representation used for the surrounding object,
      not by the element's plain display form -- separated by a comma and a
      space, then a closing brace. Thus every element appears, and each appears
      via its executable representation.

  (2) Associative mapping. An empty mapping is rendered as the two-character
      form  {}  . A non-empty mapping is rendered as an opening brace, then
      EVERY key/value pair in turn -- the key's executable representation, then
      a colon and a space, then the value's executable representation --
      separated by a comma and a space, then a closing brace. Thus every key
      and every value appears via its executable representation.

Modelling choices (Nagini fragment):
  * What the specification pins is structural: where the braces, the
    comma-and-space separators, the key/value colon-space, and the empty-form
    literals fall, and that EVERY element (resp. key and value) appears,
    rendered by the EXECUTABLE element representation rather than the plain
    display form. The internal spelling of an individual element's executable
    representation is reproduced verbatim and is therefore irrelevant to the
    structure, so each element is modelled as one distinct token (an
    `int >= 0`). A collection is a `List[int]` of element tokens; a mapping is
    a flat `List[int]` of even length carrying alternating key, value tokens
    (positions 2j, 2j+1 are the j-th pair). The specification is carried by
    `PSeq[int]`. The executable representation of one element is an unchanged
    callee `elem_repr` (the recursive representation routine the container
    rendering invokes on each element); its plain display form is the distinct
    callee `elem_str`. refinement.md / mapping.md give the bijection token <->
    real element and the callee provenance; axiom_check.py (G-AX) validates
    `elem_repr` against the real recursive routine and that it is distinct from
    the plain display form on the tested elements. No string indexing is used.
  * The container assembly is modelled DEEPLY (front-recursive folds + verified
    construction loops); the per-element executable representation is the only
    consumed axiom (`elem_repr`, an unchanged callee).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Literal punctuation code points used by the rendering (never an element
# token, which is emitted only through `elem_repr`).
LBRACE = 123   # "{"
RBRACE = 125   # "}"
COMMA = 44     # ","
SPACE = 32     # " "
COLON = 58     # ":"


# axioms-start
@Pure
@ContractOnly
def elem_repr(t: int) -> PSeq[int]:
    """Executable representation of a single element (the unchanged recursive
    representation routine the container rendering invokes per element). Left
    wholly UNINTERPRETED: the spelling is reproduced verbatim into the container
    rendering, so the structure this specification pins does not depend on it,
    and NO constraint on its length or content is assumed. In particular it is
    NOT assumed non-empty -- some elements genuinely render as the empty
    sequence, and such an element must still be rendered, and separated from its
    neighbours, exactly like any other. Used inside the postconditions, so it is
    @Pure. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX). A-consumed (through `doprint_elem`'s value)."""
    Ensures(True)


@Pure
@ContractOnly
def elem_str(t: int) -> PSeq[int]:
    """Plain display form of a single element (the alternative rendering the
    container assembly must NOT use). Modelled as its own uninterpreted callee,
    separate from `elem_repr`; no relation between the two is assumed (their
    spellings only sometimes differ -- the discriminating fact is existential,
    not universal). Provenance + soundness: mapping.md / axiom_check.py."""
    Ensures(True)


@ContractOnly
def doprint_elem(t: int) -> List[int]:
    """Materialise one element's executable representation as a fresh sequence
    (the unchanged recursive routine returns the element's text). Its
    pure-sequence value is exactly `elem_repr`. This is the concrete callee the
    container rendering invokes per element; `elem_repr` is its pure view used
    in the specifications. A-consumed (same callee as `elem_repr`)."""
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == elem_repr(t))


@ContractOnly
def str_elem(t: int) -> List[int]:
    """Materialise one element's plain display form as a fresh sequence (the
    alternative the container assembly must NOT use). Its pure-sequence value
    is `elem_str`."""
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == elem_str(t))
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def joined_elems(elems: PSeq[int]) -> PSeq[int]:
    """The comma-and-space separated executable representations of the
    collection elements, in order (no surrounding braces). Front-recursive so a
    single unfold is available per construction step."""
    if len(elems) == 0:
        return empty_seq()
    if len(elems) == 1:
        return elem_repr(elems[0])
    return elem_repr(elems[0]) + PSeq(COMMA, SPACE) + joined_elems(elems.drop(1))


@Pure
def joined_pairs(flat: PSeq[int]) -> PSeq[int]:
    """The comma-and-space separated key/value renderings of a mapping carried
    as a flat sequence (positions 0,1 are the first pair's key and value). Each
    pair renders as key-repr, colon, space, value-repr. Front-recursive,
    consuming two tokens per step; only even-length sequences arise (the caller
    carries alternating key/value tokens)."""
    if len(flat) < 2:
        return empty_seq()
    if len(flat) == 2:
        return elem_repr(flat[0]) + PSeq(COLON, SPACE) + elem_repr(flat[1])
    return (elem_repr(flat[0]) + PSeq(COLON, SPACE) + elem_repr(flat[1])
            + PSeq(COMMA, SPACE) + joined_pairs(flat.drop(2)))


@Pure
def set_seq(elems: PSeq[int]) -> PSeq[int]:
    """The full rendering of an unordered collection: the five-character empty
    form when there are no elements, else the brace-wrapped comma-and-space
    separated executable element representations."""
    if len(elems) == 0:
        return PSeq(115, 101, 116, 40, 41)  # "set()"
    return PSeq(LBRACE) + joined_elems(elems) + PSeq(RBRACE)


@Pure
def dict_seq(flat: PSeq[int]) -> PSeq[int]:
    """The full rendering of an associative mapping carried as a flat key/value
    sequence: the two-character empty form when there are no pairs, else the
    brace-wrapped comma-and-space separated key/value renderings."""
    if len(flat) == 0:
        return PSeq(LBRACE, RBRACE)  # "{}"
    return PSeq(LBRACE) + joined_pairs(flat) + PSeq(RBRACE)
# pure-end


def render_collection_codepoints(elems: List[int]) -> List[int]:
    """Render an unordered collection of elements per (1): the empty literal
    when there are none, else the brace-wrapped comma-and-space separated
    executable element representations."""
    # pre-conditions-start
    Requires(Acc(list_pred(elems), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == set_seq(ToSeq(elems)))
    # post-conditions-end
    # impl-start
    elems_s = ToSeq(elems)  # type: PSeq[int]
    if len(elems) == 0:
        out_empty = [115, 101, 116, 40, 41]  # type: List[int]  # "set()"
        Assert(ToSeq(out_empty) == set_seq(elems_s))
        return out_empty
    inner = []  # type: List[int]
    i = len(elems)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(elems), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(elems))
        Invariant(elems_s == ToSeq(elems))
        Invariant(ToSeq(inner) == joined_elems(elems_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = elems[i - 1]  # type: int
        Assert(elems_s.drop(i - 1)[0] == elt)
        Assert(elems_s.drop(i - 1).drop(1) == elems_s.drop(i))
        piece = doprint_elem(elt)  # type: List[int]
        Assert(ToSeq(piece) == elem_repr(elt))
        if i == len(elems):
            inner = piece
            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
        else:
            inner = piece + [COMMA, SPACE] + inner
            Assert(ToSeq(inner) == elem_repr(elt) + PSeq(COMMA, SPACE)
                   + joined_elems(elems_s.drop(i)))
            Assert(ToSeq(inner) == joined_elems(elems_s.drop(i - 1)))
        i = i - 1
    result = [LBRACE] + inner + [RBRACE]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACE) + joined_elems(elems_s) + PSeq(RBRACE))
    Assert(ToSeq(result) == set_seq(elems_s))
    return result
    # impl-end


def render_mapping_codepoints(flat: List[int]) -> List[int]:
    """Render an associative mapping per (2): the empty literal when there are
    no pairs, else the brace-wrapped comma-and-space separated key/value
    renderings, each pair's key and value via the executable representation.
    The mapping is carried as a flat even-length [k0, v0, k1, v1, ...] token
    list."""
    # pre-conditions-start
    Requires(Acc(list_pred(flat), 1 / 2))
    Requires(len(flat) % 2 == 0)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flat), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == dict_seq(ToSeq(flat)))
    # post-conditions-end
    # impl-start
    flat_s = ToSeq(flat)  # type: PSeq[int]
    Assert(len(flat_s) == len(flat))
    if len(flat) == 0:
        out_empty = [LBRACE, RBRACE]  # type: List[int]  # "{}"
        Assert(ToSeq(out_empty) == dict_seq(flat_s))
        return out_empty
    inner = []  # type: List[int]
    i = len(flat)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(flat), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(flat))
        Invariant(i % 2 == 0)
        Invariant(flat_s == ToSeq(flat))
        Invariant(len(flat_s) == len(flat))
        Invariant(len(flat_s.drop(i)) % 2 == 0)
        Invariant(ToSeq(inner) == joined_pairs(flat_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        key = flat[i - 2]  # type: int
        val = flat[i - 1]  # type: int
        Assert(len(flat_s.drop(i - 2)) % 2 == 0)
        Assert(flat_s.drop(i - 2)[0] == key)
        Assert(flat_s.drop(i - 2)[1] == val)
        Assert(flat_s.drop(i - 2).drop(2) == flat_s.drop(i))
        piece = doprint_elem(key) + [COLON, SPACE] + doprint_elem(val)  # type: List[int]
        Assert(ToSeq(piece) == elem_repr(key) + PSeq(COLON, SPACE)
               + elem_repr(val))
        if i == len(flat):
            inner = piece
            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
        else:
            inner = piece + [COMMA, SPACE] + inner
            Assert(ToSeq(inner) == elem_repr(key) + PSeq(COLON, SPACE)
                   + elem_repr(val) + PSeq(COMMA, SPACE)
                   + joined_pairs(flat_s.drop(i)))
            Assert(ToSeq(inner) == joined_pairs(flat_s.drop(i - 2)))
        i = i - 2
    result = [LBRACE] + inner + [RBRACE]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACE) + joined_pairs(flat_s) + PSeq(RBRACE))
    Assert(ToSeq(result) == dict_seq(flat_s))
    return result
    # impl-end
