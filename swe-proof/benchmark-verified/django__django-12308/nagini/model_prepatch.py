"""Twin-artifact model for django__django-12308.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stored structured-data value rendered as text must be shown in its
  CANONICAL DATA-INTERCHANGE encoding, not in the host language's object
  printout. A structured value is a tree: a string token, an ordered array of
  values, or an object whose members are (string-key, value) pairs.

  The interchange encoding serialises that tree STRUCTURALLY:

    * a string token is delimited by the double-quote delimiter U+0022 ( " ),
      so the value  a  renders as  "a" ; INSIDE that pair the token's own code
      points are written in the interchange alphabet rather than spliced in
      raw -- the delimiter U+0022 and the escape character U+005C are each
      written as U+005C followed by themselves, the five control positions
      U+0008, U+0009, U+000A, U+000C, U+000D as U+005C followed by b, t, n, f,
      r, and every other code point outside the printable band
      U+0020..U+007E as the six-code-point form U+005C, U+0075 and four
      lowercase hexadecimal digits (a code point above U+FFFF as the pair of
      such forms for its two surrogate halves); the printable ones stand for
      themselves;
    * an array renders as its elements, comma-and-space separated, between
      square brackets:  [ e1, e2, ... ] ;
    * an object renders as its members, comma-and-space separated, between
      curly braces, each member a double-quoted key, a colon-space, then the
      member value:  { "k1": v1, "k2": v2, ... } .

  So the value  {a: {b: c}}  renders as  {"a": {"b": "c"}}  and the value
  [a, b]  renders as  ["a", "b"] : the structure is laid out exactly, with
  every string token and every key delimited by the double quote U+0022.

  Concretely, for a structured value `value`:

    - a value that is ABSENT -- nothing is stored for it at all -- renders as
      the supplied placeholder text. ABSENCE is not the same thing as
      EMPTINESS: a value that IS stored but is itself empty is not absent, and
      does NOT render as the placeholder;
    - a value that is routed through the interchange encoder, and that the
      encoder can express, renders as its canonical interchange encoding: the
      STRUCTURAL serialisation above (`interchange_form`);
    - EVERY other stored value -- one whose contents the encoder cannot
      express, and equally one that is itself empty and so is never routed
      through the encoder at all -- renders as the general-purpose display
      text supplied for that value (`fallback_form`), shown AS-IS: the
      renderer adds no delimiters of its own. Where that fallback text shows
      string tokens they already carry the host language's single-quote
      U+0027 delimiters internally.

  The discriminating guarantee is STRUCTURAL: a value the encoder can express is
  rendered as the full interchange serialisation of its tree (brackets, braces,
  key/colon layout, double-quote U+0022 delimiters), never as the general-purpose
  display text. A renderer that merely wraps the whole printed value in one pair
  of delimiters does NOT satisfy this: the array  [a, b]  must render as
  ["a", "b"] , not as a single wrapped token.

  Rendering is moreover a TOTAL operation. For every admissible structured
  value the renderer must actually PRODUCE the text described above and hand it
  back to whoever asked for it: the guarantees above are claims about a result
  that genuinely ARRIVES, not merely about the runs that happen to arrive.
  Displaying a stored value is a bounded walk of that value's own contents --
  every step of the walk moves onto a strictly smaller part of the value (into
  something it contains, or on to the next item beside it) and each character of
  a token is consumed once -- so the walk always runs out of value to visit and
  the display appears. A renderer that can walk forever on some admissible
  value, so that the display never appears at all, does NOT meet this
  specification, no matter how its never-reached exit is annotated.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a structured value is modelled as a small recursive node tree
(`JNode`) in sibling/inner linked form. The interchange encoding is modelled
DEEPLY as a single self-recursive serialiser fold over that tree
(`interchange_form`). The general-purpose display fallback is a SEPARATE
renderer with its own dispatch (it lays a sequence out element-by-element
rather than printing it as one object), so the model does NOT re-derive its
text from the value: `fallback_form` is the identity on `content`, the text
THAT renderer produced for this value, which the renderer then hands back with
no delimiters of its own added. Both are validated == their real callees
out-of-band by axiom_check.py (G-AX) on the real structured values, never
consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The two callees the rendered branch invokes are modelled
# DEEPLY: the interchange encoder as a single self-recursive serialiser fold
# over the value tree (interchange_form), and the general-purpose display
# renderer as the text it produced passed through unchanged (fallback_form =
# identity; the renderer adds no delimiters of its own). That renderer has its
# own per-shape dispatch, so its text is CARRIED in `content` rather than
# re-derived from the value here. They are validated == their real callees
# out-of-band by axiom_check.py (G-AX) as A-references on the real structured
# values, never consumed here.
# axioms-end


# pure-start
class JNode:
    """One node in a structured-value tree, in sibling/inner linked form.

    `kind`:
        0 = STRING token  -- contents in `text`;
        1 = ARRAY         -- elements are the sibling list at `inner`;
        2 = OBJECT        -- members are the sibling list at `inner`;
        3 = MEMBER        -- one object member: KEY in `text`, VALUE is the
                             single node at `inner` (the value node carries no
                             siblings, i.e. its own `nxt` is None).
    `text`: STRING contents (kind 0) or MEMBER key (kind 3).
    `inner`: head of the contained sibling list (ARRAY elements / OBJECT
             members) or the member value (kind 3); unused for a STRING.
    `nxt`: the next sibling in the current element / member list (None = last).
    """

    def __init__(self, kind: int, text: List[int], inner: 'Optional[JNode]',
                 nxt: 'Optional[JNode]') -> None:
        Requires(Acc(list_pred(text)))
        Requires(Implies(inner is not None, Acc(j_pred(inner))))
        Requires(Implies(nxt is not None, Acc(j_pred(nxt))))
        # Assembling one node is a single bounded step; measure 1 sits strictly
        # below every walk budget below, so a walk may build a node.
        Requires(MustTerminate(1))
        Ensures(Acc(j_pred(self)))
        # A value assembled with nothing inside it and nothing beside it is one
        # single part, so a walk of it has exactly one step to take.
        Ensures(Implies(inner is None and nxt is None, j_size(self) == 1))
        self.kind = kind
        self.text = text
        self.inner = inner
        self.nxt = nxt
        Fold(j_pred(self))


@Predicate
def j_pred(n: JNode) -> bool:
    return (Acc(n.kind) and Acc(n.text) and Acc(n.inner) and Acc(n.nxt) and
            list_pred(n.text) and
            Implies(n.inner is not None, j_pred(n.inner)) and
            Implies(n.nxt is not None, j_pred(n.nxt)))


@Pure
def empty_seq() -> PSeq[int]:
    return PSeq(0).take(0)


@Pure
def j_size(n: 'Optional[JNode]') -> int:
    """How much VALUE there is to walk at `n`: the number of parts the
    structured value (or the run of values beside it) is made of; 0 when there
    is nothing there. Every step a renderer takes moves onto something the
    current part contains, or on to the next part beside it, and both are
    strictly smaller by this count -- so this is the budget within which the
    display has to appear."""
    Requires(Implies(n is not None, Acc(j_pred(n), 1 / 4)))
    Ensures(Result() >= 0)
    Ensures(Implies(n is None, Result() == 0))
    Ensures(Implies(n is not None, Result() > 0))
    if n is None:
        return 0
    return Unfolding(Acc(j_pred(n), 1 / 4),
                     1 + j_size(n.inner) + j_size(n.nxt))


@Pure
def hex_digit(d: int) -> int:
    """The lowercase hexadecimal digit for 0 <= d < 16, as a code point."""
    return 48 + d if d < 10 else 87 + d


@Pure
def hex_form(c: int) -> PSeq[int]:
    """The six-code-point interchange form of one 16-bit unit: the escape
    character U+005C, the letter u (U+0075), then the unit's four lowercase
    hexadecimal digits, most significant first."""
    return (PSeq(92, 117) + PSeq(hex_digit(c // 4096))
            + PSeq(hex_digit((c // 256) % 16))
            + PSeq(hex_digit((c // 16) % 16)) + PSeq(hex_digit(c % 16)))


@Pure
def esc_char(c: int) -> PSeq[int]:
    """The interchange form of ONE code point of a string token or of a key.

    The interchange alphabet is not the host alphabet, so a token's code
    points are not spliced in raw between the delimiters: the delimiter U+0022
    and the escape character U+005C are each written as U+005C followed by
    themselves; the five control positions U+0008, U+0009, U+000A, U+000C and
    U+000D have their own two-code-point forms (U+005C followed by b, t, n, f
    and r); every other code point outside the printable band U+0020..U+007E
    is written in the six-code-point `hex_form`, and one above U+FFFF as the
    two hex forms of its surrogate halves. The printable code points stand for
    themselves. An int outside U+0000..U+10FFFF is no code point at all, so
    there is no character for it to stand for and it is left as it is."""
    if c == 34:
        return PSeq(92, 34)
    if c == 92:
        return PSeq(92, 92)
    if c == 8:
        return PSeq(92, 98)
    if c == 9:
        return PSeq(92, 116)
    if c == 10:
        return PSeq(92, 110)
    if c == 12:
        return PSeq(92, 102)
    if c == 13:
        return PSeq(92, 114)
    if 32 <= c and c <= 126:
        return PSeq(c)
    if 0 <= c and c <= 65535:
        return hex_form(c)
    if 65536 <= c and c <= 1114111:
        return (hex_form(55296 + (c - 65536) // 1024)
                + hex_form(56320 + (c - 65536) % 1024))
    return PSeq(c)


@Pure
def esc_seq(s: PSeq[int]) -> PSeq[int]:
    """The interchange form of a WHOLE token (or key): each of its code points
    replaced by that code point's own form, in order. The empty token has the
    empty form. This is what sits between the two U+0022 delimiters -- the
    token's code points do NOT pass through unchanged."""
    if len(s) == 0:
        return empty_seq()
    return esc_seq(s.take(len(s) - 1)) + esc_char(s[len(s) - 1])


@Pure
def node_body(head: JNode) -> PSeq[int]:
    """Interchange serialisation of the SINGLE node `head` (no sibling
    separator). Dispatched on kind; the contained sibling list is serialised by
    `ser_list` on `head.inner` (a strictly smaller predicate, so this recurses
    only downward through `Unfolding`)."""
    Requires(Acc(j_pred(head), 1 / 4))
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        # STRING: "text"
        PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
        # ARRAY: [ elements ]
        else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
              # OBJECT: { members }
              else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                    # MEMBER: "key": value
                    else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                    + PSeq(58, 32) + ser_list(head.inner))))


@Pure
def ser_list(head: Optional[JNode]) -> PSeq[int]:
    """Interchange serialisation of the sibling list starting at `head`: each
    node's body, comma-and-space (44,32) separated, with no trailing separator.
    A member value node (kind 3's `inner`) carries no siblings, so `ser_list` on
    it yields exactly that value's body. The head's body is dispatched INLINE
    (same as `node_body`) so that ONE unfold of `j_pred(head)` covers both the
    head body and the tail; the only recursion is `ser_list` on the sub-nodes
    `head.inner` and `head.nxt` (strictly smaller predicates)."""
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 4)))
    if head is None:
        return empty_seq()
    return Unfolding(
        Acc(j_pred(head), 1 / 4),
        (PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34) if head.kind == 0
         else (PSeq(91) + ser_list(head.inner) + PSeq(93) if head.kind == 1
               else (PSeq(123) + ser_list(head.inner) + PSeq(125) if head.kind == 2
                     else PSeq(34) + esc_seq(ToSeq(head.text)) + PSeq(34)
                     + PSeq(58, 32) + ser_list(head.inner)))) +
        (empty_seq() if head.nxt is None
         else PSeq(44, 32) + ser_list(head.nxt)))


@Pure
def interchange_form(node: Optional[JNode]) -> PSeq[int]:
    """Canonical interchange serialisation of a structured value (the deep
    model of `json.dumps`): the single-node serialisation of the tree rooted at
    `node` (the value carries no siblings at the top, so this is `node_body`)."""
    Requires(Implies(node is not None, Acc(j_pred(node), 1 / 4)))
    if node is None:
        return empty_seq()
    return node_body(node)


@Pure
def fallback_form(content: PSeq[int]) -> PSeq[int]:
    """The general-purpose display text for a value, UNCHANGED. Whenever the
    renderer does not route a stored value through the interchange encoder --
    because the encoder cannot express it, or because the value is itself empty
    and so is never offered to the encoder -- the display is whatever that
    general-purpose renderer produced for the value, handed back as-is with no
    delimiters added. That renderer dispatches on the value's own shape (a
    sequence is laid out element-by-element, not printed as a single object),
    so its text is CARRIED here in `content` rather than recomputed from the
    value tree; where it shows string tokens they are single-quote U+0027
    delimited, in contrast to the interchange encoding's structural
    double-quote U+0022."""
    return content
# pure-end


def serialize(node: JNode) -> List[int]:
    """Verified recursive serialiser: builds the interchange encoding of the
    single value `node` (the deep-model skeleton of the canonical interchange
    serialiser), each token and key laid down in its interchange form
    (`esc_seq`) between the U+0022 delimiters. Output pinned to
    `interchange_form` / `node_body`."""
    # pre-conditions-start
    Requires(Acc(j_pred(node), 1 / 2))
    # Total, not merely partial: the encoding must ARRIVE. The walk is bounded
    # by how much value there is to walk, so every descent must land on a
    # strictly smaller part of the value.
    Requires(MustTerminate(j_size(node) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(node), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == node_body(node))
    Ensures(ToSeq(Result()) == interchange_form(node))
    # post-conditions-end
    # impl-start
    Unfold(Acc(j_pred(node), 1 / 2))
    if node.kind == 0:                          # STRING: "text"
        out = [34]  # type: List[int]
        append_escaped(out, node.text)
        out.append(34)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(out) == node_body(node))
        return out
    if node.kind == 1:                          # ARRAY: [ elements ]
        body = serialize_list(node.inner)
        result = [91]  # type: List[int]
        append_all(result, body)
        result.append(93)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result) == node_body(node))
        return result
    if node.kind == 2:                          # OBJECT: { members }
        mbody = serialize_list(node.inner)
        result2 = [123]  # type: List[int]
        append_all(result2, mbody)
        result2.append(125)
        Fold(Acc(j_pred(node), 1 / 2))
        Assert(ToSeq(result2) == node_body(node))
        return result2
    # MEMBER: "key": value
    result3 = [34]  # type: List[int]
    append_escaped(result3, node.text)
    result3.append(34)
    result3.append(58)
    result3.append(32)
    vbody = serialize_list(node.inner)
    append_all(result3, vbody)
    Fold(Acc(j_pred(node), 1 / 2))
    Assert(ToSeq(result3) == node_body(node))
    return result3
    # impl-end


def serialize_list(head: Optional[JNode]) -> List[int]:
    """Verified serialiser for a sibling list: each node's body, comma-and-space
    separated. Output pinned to `ser_list`."""
    # pre-conditions-start
    Requires(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    # Total, not merely partial: the encoding of the run of values must ARRIVE,
    # within the amount of value left to walk.
    Requires(MustTerminate(j_size(head) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(head is not None, Acc(j_pred(head), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ser_list(head))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    if head is None:
        Assert(ToSeq(result) == ser_list(head))
        return result
    Unfold(Acc(j_pred(head), 1 / 2))
    # head body, dispatched INLINE (mirrors ser_list / node_body), recursing
    # into serialize_list on the sub-nodes only -- all while `head` is unfolded.
    if head.kind == 0:                          # STRING: "text"
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
    elif head.kind == 1:                        # ARRAY: [ elements ]
        result.append(91)
        body = serialize_list(head.inner)
        append_all(result, body)
        result.append(93)
    elif head.kind == 2:                        # OBJECT: { members }
        result.append(123)
        mbody = serialize_list(head.inner)
        append_all(result, mbody)
        result.append(125)
    else:                                       # MEMBER: "key": value
        result.append(34)
        append_escaped(result, head.text)
        result.append(34)
        result.append(58)
        result.append(32)
        vbody = serialize_list(head.inner)
        append_all(result, vbody)
    # tail: the rest of the sibling list, comma-and-space separated.
    if head.nxt is not None:
        result.append(44)
        result.append(32)
        rest = serialize_list(head.nxt)
        append_all(result, rest)
    Fold(Acc(j_pred(head), 1 / 2))
    Assert(ToSeq(result) == ser_list(head))
    return result
    # impl-end


def append_esc_char(result: List[int], c: int) -> None:
    """Append the interchange form of the single code point `c`. Output pinned
    to `esc_char`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    # Total: one code point becomes a bounded, fixed-length form, so this
    # always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_char(c))
    # post-conditions-end
    # impl-start
    if c == 34:
        result.append(92)
        result.append(34)
    elif c == 92:
        result.append(92)
        result.append(92)
    elif c == 8:
        result.append(92)
        result.append(98)
    elif c == 9:
        result.append(92)
        result.append(116)
    elif c == 10:
        result.append(92)
        result.append(110)
    elif c == 12:
        result.append(92)
        result.append(102)
    elif c == 13:
        result.append(92)
        result.append(114)
    elif 32 <= c and c <= 126:
        result.append(c)
    elif 0 <= c and c <= 65535:
        result.append(92)
        result.append(117)
        result.append(hex_digit(c // 4096))
        result.append(hex_digit((c // 256) % 16))
        result.append(hex_digit((c // 16) % 16))
        result.append(hex_digit(c % 16))
    elif 65536 <= c and c <= 1114111:
        hi = 55296 + (c - 65536) // 1024
        lo = 56320 + (c - 65536) % 1024
        result.append(92)
        result.append(117)
        result.append(hex_digit(hi // 4096))
        result.append(hex_digit((hi // 256) % 16))
        result.append(hex_digit((hi // 16) % 16))
        result.append(hex_digit(hi % 16))
        result.append(92)
        result.append(117)
        result.append(hex_digit(lo // 4096))
        result.append(hex_digit((lo // 256) % 16))
        result.append(hex_digit((lo // 16) % 16))
        result.append(hex_digit(lo % 16))
    else:
        result.append(c)
    # impl-end


def append_escaped(result: List[int], src: List[int]) -> None:
    """Append the interchange form of the token `src` (read-only): every code
    point of it replaced by that code point's own form. Output pinned to
    `esc_seq`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each code point of `src` is consumed once and turned into a
    # fixed-length form, so this always finishes.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src)))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + esc_seq(ToSeq(src).take(i)))
        Invariant(MustTerminate(len(src) - i + 3))
        # invariants-end
        # one more code point extends the token's form by that code point's
        # own form: esc_seq of a prefix one longer.
        Assert(len(ToSeq(src).take(i + 1)) == i + 1)
        Assert(ToSeq(src).take(i + 1).take(i) == ToSeq(src).take(i))
        Assert(ToSeq(src).take(i + 1)[i] == ToSeq(src)[i])
        Assert(esc_seq(ToSeq(src).take(i + 1))
               == esc_seq(ToSeq(src).take(i)) + esc_char(ToSeq(src)[i]))
        append_esc_char(result, src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def append_all(result: List[int], src: List[int]) -> None:
    """Append every element of `src` (read-only) onto `result`."""
    # pre-conditions-start
    Requires(Acc(list_pred(result)))
    Requires(Acc(list_pred(src), 1 / 2))
    # Total: each character of `src` is consumed once, so this always finishes.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(result)))
    Ensures(Acc(list_pred(src), 1 / 2))
    Ensures(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src))
    # post-conditions-end
    # impl-start
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(0 <= i and i <= len(src))
        Invariant(ToSeq(result) == Old(ToSeq(result)) + ToSeq(src).take(i))
        Invariant(MustTerminate(len(src) - i + 1))
        # invariants-end
        result.append(src[i])
        i = i + 1
    Assert(ToSeq(src).take(len(src)) == ToSeq(src))
    # impl-end


def display_structured_value(value: JNode, empty: List[int], content: List[int],
                             present: bool, encodable: bool) -> List[int]:
    """The rendered dispatch. `value` is the structured value tree; `content`
    is the code points of the general-purpose display text produced for this
    value (used only on the fallback path); `empty` is the placeholder text.

    `present` is TRUE exactly when a value is stored at all, and is FALSE only
    when nothing is stored -- an empty stored value is still present.
    `encodable` is TRUE exactly when the value is both routed through the
    interchange encoder and expressible by it; a stored value that is empty is
    not routed through the encoder, so it takes the fallback arm, NOT the
    placeholder arm."""
    # pre-conditions-start
    # `value`, `empty`, `content` are inputs that are not mutated: fractional
    # permission only.
    Requires(Acc(j_pred(value), 1 / 2))
    Requires(Acc(list_pred(empty), 1 / 2))
    Requires(Acc(list_pred(content), 1 / 2))
    # Rendering is TOTAL: the display must ARRIVE, within a budget set by how
    # much value there is to walk. Every postcondition below is therefore a
    # claim about a result that is genuinely produced; a renderer that can walk
    # forever on an admissible value does not satisfy this contract.
    Requires(MustTerminate(j_size(value) + 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(j_pred(value), 1 / 2))
    Ensures(Acc(list_pred(empty), 1 / 2))
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A value that is not stored at all renders as the placeholder text,
    # unchanged. Being EMPTY is not being absent, so this arm does not claim
    # anything about an empty stored value.
    Ensures(Implies(not present, ToSeq(Result()) == ToSeq(empty)))
    # A stored value the encoder is given and can express renders as the
    # canonical interchange serialisation of its tree -- the STRUCTURAL
    # double-quote-delimited form. THIS is the discriminating clause: the
    # rendered output must be the full structural serialisation
    # (brackets/braces/keys/colons, U+0022 delimiters), never the
    # general-purpose display text.
    Ensures(Implies(present and encodable,
                    ToSeq(Result()) == interchange_form(value)))
    # EVERY other stored value -- not expressible by the encoder, or empty and
    # so never offered to it -- renders as the general-purpose display text
    # produced for that value, unchanged (no added delimiters).
    Ensures(Implies(present and not encodable,
                    ToSeq(Result()) == fallback_form(ToSeq(content))))
    # post-conditions-end
    # impl-start
    if not present:
        result = []  # type: List[int]
        j = 0
        while j < len(empty):
            # invariants-start
            Invariant(Acc(list_pred(empty), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(empty))
            Invariant(ToSeq(result) == ToSeq(empty).take(j))
            Invariant(MustTerminate(len(empty) - j + 1))
            # invariants-end
            result.append(empty[j])
            j = j + 1
        return result

    # PRE-PATCH BUG: there is no structured-data branch, so EVERY present value
    # (encodable or not) falls straight through to the host-language object
    # printout (the printout token, whose string tokens are single-quote
    # delimited), with no special-case for the canonical interchange encoding.
    # An encodable value is therefore rendered as the host-language printout
    # instead of the structural double-quote interchange serialisation --
    # failing the discriminating postcondition.
    out2 = []  # type: List[int]
    m = 0
    while m < len(content):
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(out2)))
        Invariant(0 <= m and m <= len(content))
        Invariant(ToSeq(out2) == ToSeq(content).take(m))
        Invariant(MustTerminate(len(content) - m + 1))
        # invariants-end
        out2.append(content[m])
        m = m + 1
    Assert(ToSeq(content).take(len(content)) == ToSeq(content))
    return out2
    # impl-end
