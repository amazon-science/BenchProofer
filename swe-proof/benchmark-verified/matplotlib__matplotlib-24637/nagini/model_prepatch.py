"""Twin-artifact model for matplotlib__matplotlib-24637.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container artist renders itself by emitting markup for its body content
  into the renderer's output stream. When the artist carries a (non-empty)
  group identifier, that identifier must reach the rendered output: the body
  content is enclosed in a grouping element whose id is exactly the artist's
  group identifier. Concretely, the rendered output is

      <opening group element carrying the group id> ++
      <the body content> ++
      <matching closing group element>

  so the group identifier appears, framed as the opening of a group, BEFORE the
  body content and is matched by a group close after it. A reader scanning the
  rendered output therefore finds the artist's group id present in it.

  The markup dialect is XML, and its element-writing rules apply. A start tag
  carries the id as a quoted attribute -- '<g id="' ++ the identifier ++ '"' --
  and is then terminated in one of the two ways XML permits: when body content
  follows, the start tag closes with '>' and a matching end tag '</g>' follows
  the body; when NO body content is emitted at all, the element is written in
  the equivalent self-closing form, whose start tag closes with '/>' and which
  takes no separate end tag. Both forms are the same element, and both carry
  the id attribute; the empty-body case is genuinely reachable, because a
  container whose frame is switched off and whose inner content draws nothing
  emits no body markup between the group's open and close.

  The consequence that matters, and it holds in BOTH forms: an artist whose
  group id has been set can be located in the rendered output by that id,
  because the output begins with the id-carrying attribute of the group's start
  tag. If the body content is emitted with no surrounding group, the group id
  never appears in the output and the artist cannot be located.

  Rendering also COMPLETES. Framing a bounded body with a bounded amount of
  group markup is a finite amount of work, so the render always finishes and
  hands the accumulated stream back to whoever asked for it. A render that
  never finishes -- or that never gets as far as handing its output over --
  has produced no output for a reader to scan, so the group id is just as
  absent as it is when no group is emitted at all.

Modelling choices (Nagini fragment):
  * The renderer's accumulating output stream is a ``List[int]`` of code points
    (Nagini bans ``str`` indexing); the specification is carried by ``PSeq[int]``
    via ``ToSeq``.
  * ``gid`` is the artist's group identifier as a ``List[int]`` of code points,
    non-empty (the observed case). ``children`` is the body content the inner
    artists emit, an opaque ``List[int]`` content blob; rendering does not change
    what the children emit, only whether a group encloses them. Both inputs are
    read-only and held at fractional permission (directive 5): the result is a
    fresh stream, the inputs are not observed mutated.
  * The identifier is required to hold no character that the markup dialect
    must escape or quote-switch to represent (``"``, ``&``, ``<``, ``>``); on
    that domain the id attribute carries the identifier's code points verbatim,
    which is what makes the deep model below an equality rather than an
    approximation.
  * The element markup is modeled DEEPLY as constant code-point sequences
    (``group_open_prefix`` ``<g id="``, ``attr_end`` ``"``, ``tag_end`` ``>``,
    ``selfclose_end`` ``/>``, ``group_close`` ``</g>``); there is NO consumed
    axiom. The deep model is validated == the real renderer's element writing
    out-of-band by axiom_check.py (G-AX), an A-reference (mapping.md section 3.1).
  * Completion is carried as ``MustTerminate`` in the precondition. Nagini is a
    partial-correctness verifier by default, so without that obligation an
    implementation that never reaches its return satisfies every ``Ensures``
    VACUOUSLY while emitting nothing; the behaviour above requires the render to
    actually finish and deliver the stream.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms. The only callee the changed code invokes
#  -- the renderer's element writing -- is modeled deeply in the pure region and
#  validated against the real renderer by axiom_check.py / G-AX as an
#  A-reference, not consumed. See refinement.md.)
# axioms-end


# pure-start
@Pure
def group_open_prefix() -> PSeq[int]:
    # The code points opening the group's start tag, up to the id value: '<g id="'.
    return PSeq(60, 103, 32, 105, 100, 61, 34)


@Pure
def attr_end() -> PSeq[int]:
    # The code point closing the quoted id attribute: '"'.
    return PSeq(34)


@Pure
def tag_end() -> PSeq[int]:
    # The code point terminating a start tag that has body content after it: '>'.
    return PSeq(62)


@Pure
def selfclose_end() -> PSeq[int]:
    # The code points terminating a start tag written in the self-closing form,
    # used when no body content is emitted inside the element: '/>'.
    return PSeq(47, 62)


@Pure
def group_close() -> PSeq[int]:
    # The code points of the end tag matching a non-self-closed start tag: '</g>'.
    return PSeq(60, 47, 103, 62)


@Pure
def id_attribute(gid: PSeq[int]) -> PSeq[int]:
    """The id-carrying attribute of the group's start tag: '<g id="' ++ gid ++ '"'.
    This is the contiguous run a reader scanning the output finds when the group
    id has reached the rendered output. It is common to BOTH tag-termination
    forms, so it is what the group id's presence rests on."""
    return group_open_prefix() + gid + attr_end()


@Pure
def opening_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag when body content follows it: the id attribute
    terminated by '>'."""
    return id_attribute(gid) + tag_end()


@Pure
def self_closing_tag(gid: PSeq[int]) -> PSeq[int]:
    """The group's start tag written in the self-closing form, used when no body
    content is emitted: the id attribute terminated by '/>'. This element takes
    no separate end tag."""
    return id_attribute(gid) + selfclose_end()


@Pure
def xml_safe(gid: PSeq[int]) -> bool:
    """The identifier holds no character the markup dialect must escape or
    quote-switch to represent ('"', '&', '<', '>'), so the id attribute carries
    its code points verbatim."""
    return Forall(int, lambda k: (
        not (0 <= k and k < len(gid)) or
        (gid[k] != 34 and gid[k] != 38 and gid[k] != 60 and gid[k] != 62)))


@Pure
def grouped_output(gid: PSeq[int], children: PSeq[int]) -> PSeq[int]:
    """The rendered output stream for a group-carrying artist. With body content
    the group is the start tag (carrying the id), the body, and the matching end
    tag; with NO body content the element is written self-closed and takes no end
    tag. Either way the output starts with the id-carrying attribute."""
    if len(children) == 0:
        return self_closing_tag(gid)
    return opening_tag(gid) + children + group_close()
# pure-end


def draw_grouped_output(gid: List[int], children: List[int]) -> List[int]:
    # pre-conditions-start
    # Both inputs are read-only (the result is a fresh stream): fractional
    # permission (directive 5). The observed case carries a non-empty group id.
    Requires(Acc(list_pred(gid), 1 / 2))
    Requires(Acc(list_pred(children), 1 / 2))
    Requires(len(gid) > 0)
    # The identifier is representable verbatim in a quoted attribute: it holds
    # none of the characters the markup dialect escapes or quote-switches on.
    Requires(xml_safe(ToSeq(gid)))
    # (0) The render COMPLETES and hands its stream back: framing a bounded body
    #     with a bounded amount of group markup is finite work. Nagini proves
    #     only PARTIAL correctness, so without this obligation an implementation
    #     that diverges -- or whose return is unreachable -- satisfies the
    #     postconditions below VACUOUSLY while emitting NO output, and a reader
    #     scanning that output finds no group id at all. Requiring termination is
    #     what makes clauses (1) and (2) claims about output actually produced.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(gid), 1 / 2))
    Ensures(Acc(list_pred(children), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The rendered output is exactly the body content enclosed in a group
    #     element carrying the group id, written per the dialect's element rules:
    #     with body content, the start tag (with the id), the body, then the
    #     matching end tag; with no body content, the same id-carrying start tag
    #     written self-closed, with no end tag. This pins the full structure --
    #     an impl that drops the group, reorders, or omits the id cannot verify.
    Ensures(ToSeq(Result()) == grouped_output(ToSeq(gid), ToSeq(children)))
    # (2) The id-carrying attribute of the group's start tag occurs as a
    #     contiguous run of the output, positioned before any body content
    #     (witness at index 0). This is the property a reader scanning the output
    #     relies on to locate the artist by its id, and it holds in BOTH
    #     tag-termination forms. An impl that emits the body content with no
    #     surrounding id-bearing group cannot verify (the id is absent).
    Ensures(Exists(int, lambda i: (
        0 <= i and i + len(id_attribute(ToSeq(gid))) <= len(ToSeq(Result())) and
        ToSeq(Result()).drop(i).take(len(id_attribute(ToSeq(gid)))) ==
        id_attribute(ToSeq(gid)))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the body content is drawn directly into the stream
    # with NO surrounding group element -- the artist's group id is never
    # emitted. The rendered output is just the children content.
    result = []  # type: List[int]
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) == ToSeq(children).take(j))
        # The pre-patch draw itself TERMINATES -- it walks the body once. The
        # remaining body code points discharge MustTerminate(2), so the failure
        # below is attributable to the missing group framing (the bug), not to
        # an undischarged termination obligation.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == ToSeq(children))
    return result
    # impl-end
