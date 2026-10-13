"""Twin-artifact model for sphinx-doc__sphinx-11510.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When textual content that has been gathered for inclusion into a document is
  handed on to the parser, that content first passes through the document-set's
  content-transformation hook, so that any registered transformer observes and
  may rewrite it before it is parsed -- exactly as the content of a primary
  document does.

  The gathered content arrives as a sequence of lines whose final two entries
  are internal book-keeping markers that frame the inserted region; they are
  not part of the authored content. The transformation therefore applies to the
  AUTHORED body only -- every line except the final two -- while the two framing
  markers are carried through unchanged and re-attached, in their original
  positions, after the (possibly rewritten) body. The result is the line
  sequence forwarded to the parser.

  Consequently: the forwarded sequence is the transformed body followed by the
  two original framing markers; the two framing markers are preserved verbatim;
  and the body region is precisely what the transformation hook is offered.

  Offering content to the hook is an EFFECT, seen by the registered transformers
  themselves, and it is NOT recoverable from the forwarded sequence: two steps
  can forward one and the same sequence while having shown the transformers
  different content, or having shown them content more than once. Which content
  is offered, and how many times, is therefore part of the behaviour specified
  here and not an implementation's free choice. A forwarding step is licensed
  for exactly ONE offer, of exactly the authored body region, and forwarding is
  conditional on spending that licence: a step that forwards content it never
  offered, or that offers a region other than the authored body, or that offers
  a second time, is not this behaviour -- whatever sequence it hands back.

  That obligation is carried the standard way effects are carried here. An offer
  is an operation (`hook_offer_io`) parameterised by the region it shows; a step
  receives a token at a place together with the licence naming the one offer
  permitted there, an offer spends licence and token and yields the token at the
  place the licence names, and the step must hand a token at that place back to
  its caller. So the offer cannot be skipped (the token is only obtainable by
  making it), cannot show another region (the licence names the region), and
  cannot happen twice (there is one licence and a step cannot mint one).

Lines are modelled as `List[int]` of opaque per-line identities (the content of
a line is a value; the line-text round trip "join the lines, hand to the hook,
split again" is the identity at line granularity for content with no embedded
line breaks, which is the regime the behaviour concerns). The content
transformation hook is an opaque, uninterpreted pure function on the body line
sequence (`hook`): it stands for arbitrary registered transformer code, so the
specification constrains only WHICH region is offered to it, how often, and that
the framing markers bypass it, never what it computes. The specification is
carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.io_contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def hook(body: PSeq[int]) -> PSeq[int]:
    """The document-set content-transformation hook, applied to the authored
    body line sequence. Uninterpreted: it stands for arbitrary registered
    transformer code, so it carries NO Ensures -- the specification pins only
    that it is offered exactly the body region (framing markers excluded) and
    that its result replaces that region, never what it returns. (mapping.md)"""
    Requires(True)


@IOOperation
def hook_offer_io(t_pre: Place, region: PSeq[int], t_post: Place = Result()) -> bool:
    """The observable EFFECT of the forwarding step: the content-transformation
    hook is shown the line sequence `region` -- one offer -- carrying the step
    from place `t_pre` to place `t_post`. It models the offer itself, not what
    the hook computes from it (`hook` above does that): what it pins is that an
    offer HAPPENED and WHICH region it showed. A step holds one instance of this
    operation per offer it is permitted to make and an offer spends one; a step
    cannot mint an instance, so how many offers are made and which region each
    one shows are settled by the step's contract instead of chosen by its
    implementation. An offer terminates."""
    Terminates(True)


@ContractOnly
def emit_and_collect(t_pre: Place, body: List[int]) -> List[int]:
    """Offer the authored body to the content-transformation hook and collect
    the (possibly rewritten) body it yields. Models the unchanged content-
    dispatch machinery together with the line<->text round trip around it: the
    result is `hook` applied to the body. The body is read at a fractional share
    and returned unchanged; the yielded sequence is a fresh list. Offering is an
    effect, so this also spends one licence to show exactly `body` plus the token
    that reaches it, and hands back the token at the place that licence names: it
    is callable only where the caller's own contract licenses an offer of exactly
    that region. (mapping.md)"""
    IOExists1(Place)(
        lambda t_post: (
        Requires(Acc(list_pred(body), 1 / 2)),
        Requires(token(t_pre, 2) and hook_offer_io(t_pre, ToSeq(body), t_post)),
        Requires(MustTerminate(2)),
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(body), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        Ensures(ToSeq(Result()) == hook(ToSeq(body))),
        )
    )
# axioms-end


# pure-start
@Pure
def transformed(lines: PSeq[int]) -> PSeq[int]:
    """The line sequence forwarded to the parser: the hook-transformed authored
    body (every line but the final two) followed by the two framing markers,
    re-attached verbatim in their original positions. The two framing markers
    are always present in the gathered content; when fewer than two lines are
    present (never, in the modelled regime) the whole sequence is treated as
    body, keeping the function total so the precondition is trivially met."""
    if len(lines) < 2:
        return hook(lines)
    return hook(lines.take(len(lines) - 2)) + lines.drop(len(lines) - 2)
# pure-end


def forward_with_source_read(t_pre: Place, lines: List[int]) -> List[int]:
    IOExists1(Place)(
        lambda t_post: (
        # pre-conditions-start
        # The gathered line sequence is read-only here (it is consumed to build
        # the forwarded sequence, never mutated in place); fractional permission,
        # required and ensured, so no caller may satisfy a postcondition
        # vacuously by overwriting the input. The final two entries are the
        # framing markers, so at least two lines are present.
        Requires(Acc(list_pred(lines), 1 / 2)),
        Requires(len(lines) >= 2),
        # The step arrives holding a token and a licence for exactly ONE offer,
        # of exactly the authored body region (the gathered lines minus the two
        # framing markers). That is the whole effect budget it is given: no
        # second offer, and no offer of any other region, is available to it.
        Requires(token(t_pre, 3) and
                 hook_offer_io(t_pre, ToSeq(lines).take(len(lines) - 2), t_post)),
        Requires(MustTerminate(3)),
        # pre-conditions-end
        # post-conditions-start
        # The licensed offer has been MADE: the token handed back sits at the
        # place the licence names, which is reachable only by showing the hook
        # exactly the authored body region. So content is never forwarded
        # unoffered, and the offer that happened showed that region and no
        # other.
        Ensures(token(t_post)),
        Ensures(Acc(list_pred(lines), 1 / 2)),
        Ensures(Acc(list_pred(Result()))),
        # The forwarded sequence is the hook-transformed authored body followed
        # by the two original framing markers: the body region is exactly what
        # the hook is offered, and the result replaces that region.
        Ensures(ToSeq(Result()) == transformed(ToSeq(lines))),
        # The two framing markers are preserved verbatim, in their original
        # order and position (the last two lines of the output equal the last
        # two lines of the input).
        Ensures(len(Result()) >= 2),
        Ensures(ToSeq(Result()).drop(len(Result()) - 2) == ToSeq(lines).drop(len(lines) - 2)),
        # The authored body region (everything but the final two output lines)
        # is precisely the region offered to and replaced by the hook.
        Ensures(ToSeq(Result()).take(len(Result()) - 2) == hook(ToSeq(lines).take(len(lines) - 2))),
        # post-conditions-end
        )
    )
    # impl-start
    # Pre-patch skeleton: the gathered content is forwarded to the parser
    # exactly as gathered. The content-transformation hook is never offered the
    # body, so the body region is passed through unchanged rather than being
    # replaced by `hook(body)`. (This is the behaviour the patch corrects.)
    n = len(lines)
    result = lines[:n]
    Assert(ToSeq(result) == ToSeq(lines))
    Assert(len(result) >= 2)
    return result
    # impl-end
