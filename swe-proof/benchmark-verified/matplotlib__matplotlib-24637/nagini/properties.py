# properties.py — PBT falsification battery for matplotlib__matplotlib-24637.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the single # impl-start / # impl-end region — which spec_view elides
# wholesale, nested invariants included — so same_spec holds by construction)
# and are checked by Nagini verify; axiom cases are real-callee probes in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   draw_grouped_output(gid: List[int], children: List[int]) -> List[int]
#     Requires Acc(list_pred(gid), 1/2)        <-- READ-ONLY input (half perm)
#     Requires Acc(list_pred(children), 1/2)   <-- READ-ONLY input (half perm)
#     Requires len(gid) > 0                    <-- the truthy-gid branch (`if gid:`)
#     Requires xml_safe(ToSeq(gid))            <-- the id is representable verbatim
#                                                  in a quoted attribute (no " & < >)
#     Requires MustTerminate(2)                <-- TOTALITY [LB-0]: the render must
#                                                  COMPLETE and deliver its stream
#     Ensures  Acc(list_pred(gid), 1/2)        <-- frame: caller keeps its half
#     Ensures  Acc(list_pred(children), 1/2)   <-- frame: caller keeps its half
#     Ensures  Acc(list_pred(Result()))        <-- a fresh stream is returned
#     Ensures  ToSeq(Result()) == grouped_output(ToSeq(gid), ToSeq(children))  [LB-1]
#     Ensures  Exists(i: id_attribute(gid) occurs as a contiguous run of Result()
#                       starting at i, in-bounds)                              [LB-2]
#
#   grouped_output(gid, children) = self_closing_tag(gid)                if children = []
#                                 = opening_tag(gid) ++ children ++ group_close()  else
#   id_attribute(gid)     = group_open_prefix() ++ gid ++ attr_end()
#   opening_tag(gid)      = id_attribute(gid) ++ tag_end()
#   self_closing_tag(gid) = id_attribute(gid) ++ selfclose_end()
#   with group_open_prefix() = '<g id="', attr_end() = '"', tag_end() = '>',
#        selfclose_end()     = '/>',      group_close() = '</g>'
#   (all @Pure CONSTANT code-point sequences).
#
#   THE TWO TAG-TERMINATION FORMS ARE BOTH REAL. The markup dialect writes an
#   element whose body is empty in the self-closing form ('<g id="GID"/>', no end
#   tag) and an element with body content in the framed form ('<g id="GID">' ++
#   body ++ '</g>'). grouped_output BRANCHES on len(children) accordingly, because
#   the real renderer does: it defers a start tag's terminator until it knows
#   whether any content followed. An always-framed model is UNFAITHFUL on the
#   empty-body class, which is reachable (a container whose frame is off and whose
#   inner content draws nothing emits no body markup). The 'always-framed' reject
#   case below pins exactly that: it is the shape a model that ignored the
#   self-closing form would have, and LB-1 refutes it.
#
#   grouped_output / id_attribute / opening_tag / self_closing_tag are @Pure folds
#   GROUNDED ENTIRELY in the inputs (gid, children) + fixed markup constants —
#   fully unfoldable; NOT an opaque answer-key / marker oracle. The load-bearing
#   equality LB-1 is checked against the fold of the impl's OWN args, so there is
#   no "wrong ungrounded-oracle echo" to build: any value an impl returns must
#   equal grouped_output() of its actual args. The ungrounded-oracle-echo class is
#   therefore N/A (see 'assessment'); the cheapest honest impl IS the gold
#   per-segment append, so its positive control is a reorder / local-reshape
#   (directive 5).
#
#   The BEHAVIOURAL DISCRIMINATOR (the bug fix, issue #20044): the container
#   artist's draw must wrap its children draw in the renderer's group open/close
#   carrying get_gid(), so the artist's gid reaches the SVG output as the group's
#   id attribute. The pre-patch draw drew the children with NO surrounding group,
#   so the gid never appeared (model_prepatch.py reproduces that). LB-1 + LB-2 pin
#   the gid-framed output; the partial-domain rivals below ARE that pre-patch
#   behaviour (and the adjacent near-misses that drop the gid / the end tag).
#
#   LB-2 is stated over id_attribute (the '<g id="GID"' run) rather than over a
#   single termination form ON PURPOSE: that run is what BOTH forms share, so LB-2
#   is the honest "the gid reached the output" property across the whole admitted
#   domain. The form-specific structure lives in LB-1, which is a full equality
#   and therefore still refutes every near-miss below.
#
#   LB-0 (MustTerminate) is what makes LB-1/LB-2 claims about output ACTUALLY
#   PRODUCED. Nagini proves only PARTIAL correctness, so without it an impl whose
#   return is never reached satisfies LB-1/LB-2 VACUOUSLY while emitting nothing —
#   and a faithful patch of that shape (a render that diverges, or returns before
#   emitting) leaves the gid absent from the SVG exactly as the pre-patch bug does.
#   The real patched draw is straight-line (group open, the child draws, group
#   close, return), so totality is TRUE of it; the 'diverge-before-return' rival
#   below is the reject case that pins LB-0.
#
#   No @ContractOnly axioms (meta.axioms == []). The markup constants are an
#   A-reference (deep model) validated == the real renderer's element writing
#   (via XMLWriter.start('g', id=gid) / .end('g'), BOTH termination forms) by
#   axiom_check.py (G-AX). That established real-callee check IS the axiom lane;
#   re-encoding it as a Docker probe would duplicate, not strengthen, it. Hence
#   AXIOM_TESTS = []. See 'assessment'.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24637"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# The SINGLE impl region body (between # impl-start / # impl-end, exclusive of
# the marker lines). The whole impl region — nested # invariants-start/-end
# included — is elided by spec_view, so editing ONLY this text keeps same_spec
# byte-identical. The whole body is a unique anchor.
# ===========================================================================
_IMPL_GOLD = '''    result = []  # type: List[int]
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        # The remaining prefix code points are a strictly decreasing, bounded-
        # below measure, discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        # The remaining id code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        # The remaining attribute-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
    if len(children) == 0:
        # No body content was emitted: the start tag is written in the
        # self-closing form, so it ends with '/>' and there is no separate close.
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(gid), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
            # The remaining self-close code points are the decreasing measure,
            # discharging MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
        Assert(len(ToSeq(children)) == len(children))
        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
        return result
    # Body content was emitted: the start tag ends with '>', the body follows,
    # and a matching close tag '</g>' terminates the group. The self-closing
    # branch above returned, so len(children) > 0 holds from here on -- that is
    # exactly the branch condition grouped_output splits on, so it must be
    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
    Assert(len(children) > 0)
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        # The remaining tag-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        # The remaining body code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result'''

assert _IMPL_GOLD in _BASE, "impl anchor drift: draw_grouped_output body not verbatim"
assert _BASE.count(_IMPL_GOLD) == 1, "impl anchor not unique"

# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Keep every append loop and ALL its loop invariants VERBATIM (so every gold
# proof obligation that closes each take(j) invariant is preserved — directive 2
# / pilot-bug 2), and keep the len(children) branch (it is the real callee's own
# branch, not scaffolding). Only reshape the SCAFFOLDING between the loops:
# restate the inter-loop framing Asserts and introduce two typed local bindings
# (`idattr`, `open_seq`) naming the intermediate sequences (a local-variable
# reshape, directive 5 — NOT a loop-direction flip, so no f(a+b)==f(a)+f(b) fold
# lemma is needed). Same observable value; if a faithful correct impl could NOT
# verify against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = '''    result = []  # type: List[int]
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        # The remaining prefix code points are a strictly decreasing, bounded-
        # below measure, discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        # The remaining id code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        # The remaining attribute-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    # name the completed id attribute (local-variable reshape)
    idattr = id_attribute(ToSeq(gid))  # type: PSeq[int]
    Assert(idattr == group_open_prefix() + ToSeq(gid) + attr_end())
    Assert(ToSeq(result) == idattr)
    if len(children) == 0:
        # No body content was emitted: the start tag is written in the
        # self-closing form, so it ends with '/>' and there is no separate close.
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(gid), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
            # The remaining self-close code points are the decreasing measure,
            # discharging MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
        Assert(len(ToSeq(children)) == len(children))
        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
        return result
    # Body content was emitted: the start tag ends with '>', the body follows,
    # and a matching close tag '</g>' terminates the group. The self-closing
    # branch above returned, so len(children) > 0 holds from here on -- that is
    # exactly the branch condition grouped_output splits on, so it must be
    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
    Assert(len(children) > 0)
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        # The remaining tag-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    # restated framing assert via the named id attribute
    open_seq = opening_tag(ToSeq(gid))  # type: PSeq[int]
    Assert(open_seq == id_attribute(ToSeq(gid)) + tag_end())
    Assert(ToSeq(result) == open_seq)
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        # The remaining body code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result'''

# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# We cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that BOTH half-permission inputs are
# usable (read each via len / ToSeq), that the Requires(len(gid) > 0) branch is
# reachable, and that the xml_safe precondition is usable as a fact — then run
# the gold body to a normal (non-raising) return. If the Requires were vacuous /
# over-strong the impl could not both consume the half-permissions (and the
# len(gid)>0 / xml_safe facts) and return a correct value => PRECOND-TOO-STRONG.
# The gold body (proof obligations intact) follows the admissibility asserts
# verbatim, so BOTH body classes (empty and non-empty) stay admitted.
# ===========================================================================
_IMPL_ADMISS = '''    # admissibility: both half-permission inputs are readable, the
    # Requires(len(gid) > 0) truthy-gid branch is reachable, the XML-safety
    # precondition is usable, and BOTH body cases are admitted by the domain.
    Assert(len(gid) > 0)
    Assert(len(children) >= 0)
    Assert(len(ToSeq(gid)) == len(gid))
    Assert(len(ToSeq(children)) == len(children))
    Assert(xml_safe(ToSeq(gid)))
    result = []  # type: List[int]
    # emit the id-carrying attribute of the group's start tag:
    # '<g id="' ++ gid ++ '"'
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        # The remaining prefix code points are a strictly decreasing, bounded-
        # below measure, discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        # The remaining id code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    Assert(ToSeq(result) == group_open_prefix() + ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        # The remaining attribute-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
    if len(children) == 0:
        # No body content was emitted: the start tag is written in the
        # self-closing form, so it ends with '/>' and there is no separate close.
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(gid), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      id_attribute(ToSeq(gid)) + selfclose_end().take(j))
            # The remaining self-close code points are the decreasing measure,
            # discharging MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        Assert(selfclose_end().take(len(selfclose_end())) == selfclose_end())
        Assert(len(ToSeq(children)) == len(children))
        Assert(ToSeq(result) == self_closing_tag(ToSeq(gid)))
        Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
        return result
    # Body content was emitted: the start tag ends with '>', the body follows,
    # and a matching close tag '</g>' terminates the group. The self-closing
    # branch above returned, so len(children) > 0 holds from here on -- that is
    # exactly the branch condition grouped_output splits on, so it must be
    # carried across the loops below (Nagini havocs unpinned pre-loop facts).
    Assert(len(children) > 0)
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        # The remaining tag-end code points are the decreasing measure,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
    # draw the body content (children) into the stream, unchanged
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        # The remaining body code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children))
    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result'''

# ===========================================================================
# (3) FRAME-MUTATION on `gid` — write to the read-only half-permission input
# (reject). MANDATORY: gid is Acc(list_pred(gid), 1/2). Inside the gid loop the
# index gid[j] is known in-bounds (0 <= j < len(gid) by the loop guard +
# invariant), so the WRITE gid[j] = gid[j] is well-typed and value-NEUTRAL — yet
# a list write needs FULL permission. With only the half-permission the Requires
# grants, Nagini rejects for INSUFFICIENT PERMISSION. Every gold invariant/assert
# is kept VERBATIM so the rejection is attributable to the write, not a spec
# change. A byte-fuzzer never thinks to mutate the read-only input.
# ===========================================================================
_IMPL_FRAME_GID = _IMPL_GOLD.replace(
    "        result.append(gid[j])\n        j = j + 1",
    "        gid[j] = gid[j]  # FRAME MUTATION: write the read-only half-perm input\n"
    "        result.append(gid[j])\n        j = j + 1",
    1,
)
assert _IMPL_FRAME_GID != _IMPL_GOLD, "frame-gid edit did not apply"

# ===========================================================================
# (3b) FRAME-MUTATION on `children` — write to the OTHER read-only half-perm
# input (reject). Supporting case: in the children loop children[j] is in-bounds
# (0 <= j < len(children)); the value-neutral write children[j] = children[j]
# needs FULL permission, which the Acc(list_pred(children), 1/2) Requires does not
# grant => rejected for INSUFFICIENT PERMISSION. Confirms the frame clause guards
# BOTH read-only inputs, not just gid.
# ===========================================================================
_IMPL_FRAME_CHILDREN = _IMPL_GOLD.replace(
    "        result.append(children[j])\n        j = j + 1",
    "        children[j] = children[j]  # FRAME MUTATION: write read-only half-perm input\n"
    "        result.append(children[j])\n        j = j + 1",
    1,
)
assert _IMPL_FRAME_CHILDREN != _IMPL_GOLD, "frame-children edit did not apply"

# ===========================================================================
# (4) PARTIAL-DOMAIN / no-group (reject). THIS IS THE PRE-PATCH BUG (issue
# #20044) and model_prepatch.py: emit the children body content with NO
# surrounding group element — the gid never reaches the output. The result is
# just the body content (children), so the load-bearing LB-1 fails (the output
# has no start tag and no id attribute), and LB-2 (the id-carrying attribute
# occurs in the output) also fails. The children loop + its invariants are kept;
# only the markup loops are removed.
# ===========================================================================
_IMPL_NOGROUP = '''    result = []  # type: List[int]
    # PRE-PATCH BUG: draw the body content with NO surrounding group element.
    # The gid never reaches the output (no start tag, no id attribute).
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) == ToSeq(children).take(j))
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    Assert(ToSeq(result) == ToSeq(children))
    return result'''
assert _IMPL_NOGROUP != _IMPL_GOLD

# ===========================================================================
# (5) PARTIAL-DOMAIN / drop the gid (empty id attribute) (reject). Emit a
# WELL-FORMED group element — in BOTH termination forms, so the branch structure
# matches the spec exactly — but WITHOUT the gid: the loop over `gid` is removed,
# so the id attribute is group_open_prefix() ++ attr_end() (an empty id value).
# Because Requires(len(gid) > 0), ToSeq(gid) is non-empty, so id_attribute(gid)
# differs from the emitted empty-id attribute: LB-1 fails (the result lacks the
# gid run) and LB-2 fails (id_attribute(gid) does not occur). This is the precise
# discriminator the F2P greps for — a group that DROPS the gid. Note the rival
# keeps the self-closing/framed branch, so it cannot be rejected merely for
# getting the tag-termination form wrong: the gid's absence is what refutes it.
# ===========================================================================
_IMPL_EMPTYID = '''    result = []  # type: List[int]
    # emit a group element but DROP the gid: the id attribute is empty
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    # NO gid loop here -> the id attribute is empty
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) == group_open_prefix() + attr_end().take(j))
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix() + attr_end())
    if len(children) == 0:
        j = 0
        while j < len(selfclose_end()):
            # invariants-start
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(selfclose_end()))
            Invariant(ToSeq(result) ==
                      group_open_prefix() + attr_end() + selfclose_end().take(j))
            Invariant(MustTerminate(len(selfclose_end()) - j + 1))
            # invariants-end
            result.append(selfclose_end()[j])
            j = j + 1
        return result
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) ==
                  group_open_prefix() + attr_end() + tag_end().take(j))
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) == group_open_prefix() + attr_end() + tag_end()
                  + ToSeq(children).take(j))
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) == group_open_prefix() + attr_end() + tag_end()
                  + ToSeq(children) + group_close().take(j))
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    return result'''
assert _IMPL_EMPTYID != _IMPL_GOLD

# ===========================================================================
# (6) PARTIAL-DOMAIN / omit the end tag (reject). In the non-empty-body branch,
# emit the start tag (with the gid) and the children, but NEVER emit '</g>'. The
# result is opening_tag(gid) ++ children, so LB-1 (which pins the trailing
# group_close() on that branch) fails. LB-2 would still hold — the id attribute
# occurs — so this isolates the end-tag sub-term of LB-1: an unbalanced-group
# near-miss invisible to a "does the gid appear" proxy but caught by the full
# structural equality. NOTE this is NOT the self-closing form: self-closing is
# legal ONLY when the body is empty, and here the body is non-empty, so dropping
# the end tag yields markup the real renderer never emits.
# ===========================================================================
_IMPL_NOCLOSE = _IMPL_GOLD.replace(
    """    # close the group: emit '</g>'
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(len(children) > 0)
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        # The remaining close code points are the decreasing measure, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    # the self-closing branch returned, so the body is non-empty here: that is
    # the branch condition grouped_output splits on.
    Assert(len(ToSeq(children)) == len(children))
    Assert(len(ToSeq(children)) > 0)
    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result""",
    """    # OMIT the end tag: never emit '</g>'. Output is opening_tag ++ children.
    return result""",
    1,
)
assert _IMPL_NOCLOSE != _IMPL_GOLD

# ===========================================================================
# (6b) WRONG TAG-TERMINATION FORM / always framed (reject). THE FAITHFULNESS
# REJECT CASE. Emit '<g id="GID">' ++ children ++ '</g>' UNCONDITIONALLY, with no
# self-closing branch at all — the shape a model that ignored the dialect's
# empty-body element form would have. It is correct on every non-empty body and
# WRONG on the empty-body class, where the real renderer writes the element
# self-closed ('<g id="GID"/>', no end tag). LB-1's branch on len(children)
# refutes it: on the empty-body class the rival returns
# opening_tag(gid) ++ group_close() while grouped_output returns
# self_closing_tag(gid). This case is why grouped_output branches, and it is the
# control proving the branch is load-bearing rather than decorative — an
# always-framed spec would ADMIT this rival and predict output the real callee
# never produces.
# ===========================================================================
_IMPL_ALWAYS_FRAMED = '''    result = []  # type: List[int]
    j = 0
    while j < len(group_open_prefix()):
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_open_prefix()))
        Invariant(ToSeq(result) == group_open_prefix().take(j))
        Invariant(MustTerminate(len(group_open_prefix()) - j + 1))
        # invariants-end
        result.append(group_open_prefix()[j])
        j = j + 1
    Assert(ToSeq(result) == group_open_prefix())
    j = 0
    while j < len(gid):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(gid))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid).take(j))
        Invariant(MustTerminate(len(gid) - j + 1))
        # invariants-end
        result.append(gid[j])
        j = j + 1
    Assert(ToSeq(gid).take(len(gid)) == ToSeq(gid))
    j = 0
    while j < len(attr_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(attr_end()))
        Invariant(ToSeq(result) == group_open_prefix() + ToSeq(gid) + attr_end().take(j))
        Invariant(MustTerminate(len(attr_end()) - j + 1))
        # invariants-end
        result.append(attr_end()[j])
        j = j + 1
    Assert(ToSeq(result) == id_attribute(ToSeq(gid)))
    j = 0
    while j < len(tag_end()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(tag_end()))
        Invariant(ToSeq(result) == id_attribute(ToSeq(gid)) + tag_end().take(j))
        Invariant(MustTerminate(len(tag_end()) - j + 1))
        # invariants-end
        result.append(tag_end()[j])
        j = j + 1
    Assert(tag_end().take(len(tag_end())) == tag_end())
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)))
    j = 0
    while j < len(children):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(children))
        Invariant(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children).take(j))
        Invariant(MustTerminate(len(children) - j + 1))
        # invariants-end
        result.append(children[j])
        j = j + 1
    Assert(ToSeq(children).take(len(children)) == ToSeq(children))
    j = 0
    while j < len(group_close()):
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(group_close()))
        Invariant(ToSeq(result) ==
                  opening_tag(ToSeq(gid)) + ToSeq(children) + group_close().take(j))
        Invariant(MustTerminate(len(group_close()) - j + 1))
        # invariants-end
        result.append(group_close()[j])
        j = j + 1
    Assert(ToSeq(result) == opening_tag(ToSeq(gid)) + ToSeq(children) + group_close())
    return result'''
assert _IMPL_ALWAYS_FRAMED != _IMPL_GOLD

# ===========================================================================
# (7) NON-TERMINATION / the render never delivers its output (reject). Emits the
# FULL correct grouped output — every markup loop and the body loop are the gold
# ones verbatim, so LB-1 and LB-2 are literally established at the end — and then
# spins forever in a loop with no decreasing measure BEFORE the return. Under
# partial correctness alone this verifies VACUOUSLY (the return is unreachable, so
# the Ensures are never checked). LB-0 (MustTerminate(2) in the precondition) is
# the ONLY clause that rejects it: the added loop cannot supply a decreasing,
# bounded-below measure, so the termination obligation cannot be discharged.
# This case is what makes LB-0 load-bearing rather than decorative.
# ===========================================================================
_IMPL_DIVERGE = _IMPL_GOLD.replace(
    """    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    return result""",
    """    Assert(ToSeq(result) == grouped_output(ToSeq(gid), ToSeq(children)))
    # DIVERGE before handing the stream over: the output is fully built and
    # correct, but the caller never receives it. No decreasing measure exists for
    # this loop, so MustTerminate(2) cannot be discharged.
    while 0 <= j:
        # invariants-start
        Invariant(Acc(list_pred(gid), 1 / 2))
        Invariant(Acc(list_pred(children), 1 / 2))
        Invariant(Acc(list_pred(result)))
        # invariants-end
        j = j + 1
    return result""",
    1,
)
assert _IMPL_DIVERGE != _IMPL_GOLD, "diverge edit did not apply"


SPEC_TESTS = [
    {
        "id": "pos-control-reshape-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: every append loop and ALL "
                     "its loop invariants are kept VERBATIM (every take(j) proof "
                     "obligation preserved), the real callee's own len(children) "
                     "branch is kept, and only the inter-loop scaffolding is reshaped "
                     "— restated framing Asserts plus two typed local bindings "
                     "(idattr = id_attribute(gid), open_seq = opening_tag(gid)) that "
                     "name the intermediate sequences. No loop-direction flip, so no "
                     "f(a+b)=f(a)+f(b) fold lemma is needed (pilot-bug 3 avoided). "
                     "Same observable value; must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-two-readonly-inputs-nonempty-safe-gid",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that both half-permission inputs (gid, "
                     "children) are usable (read via len / ToSeq), that the "
                     "Requires(len(gid) > 0) truthy-gid branch is reachable, and that "
                     "the Requires(xml_safe(ToSeq(gid))) fact is usable — then runs "
                     "the gold body to a normal non-raising return. If any Requires "
                     "were vacuous or over-strong the impl could not both consume the "
                     "permissions/facts and return the correct value => "
                     "PRECOND-TOO-STRONG. Because the gold body follows verbatim, BOTH "
                     "body classes (empty => self-closing, non-empty => framed) remain "
                     "admitted, so this also witnesses that the domain was not narrowed "
                     "to dodge the empty-body case. Source: the two Acc(...,1/2) "
                     "Requires + Requires(len(gid) > 0) + Requires(xml_safe(...)).",
    },
    {
        "id": "frame-mutation-write-gid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME_GID),
        "refinement": "A faithful real patch in which the container artist's draw (or "
                      "the framing it calls) wrote back into the gid it reads — e.g. "
                      "mutating the stored group id / the string returned by the "
                      "accessor while emitting it — would corrupt the artist's group "
                      "id that later draws and the test read. The accessor is the "
                      "unchanged read-only one; the renderer's group open only READS "
                      "the gid (interpolates it into the start tag) and never writes "
                      "it. A mutating variant would change the gid the F2P assertion "
                      "greps for and would not faithfully resolve the test.",
        "rationale": "draw_grouped_output holds only Acc(list_pred(gid), 1/2). The "
                     "write gid[j] = gid[j] (value-neutral, in-bounds via the loop "
                     "guard 0 <= j < len(gid)) needs FULL permission => Nagini rejects "
                     "for INSUFFICIENT PERMISSION. Source: the permission system + the "
                     "Acc(list_pred(gid), 1/2) Requires/Ensures frame clause. All gold "
                     "invariants/asserts kept verbatim so the rejection is "
                     "attributable to the write, not a spec change.",
    },
    {
        "id": "frame-mutation-write-children",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME_CHILDREN),
        "refinement": "A faithful real patch in which the framing wrote back into the "
                      "children's already-emitted content (the body stream) would "
                      "corrupt the body the test reads. The patch inserts only the "
                      "group open/close around the UNCHANGED child draws; it never "
                      "rewrites the body content. A mutating variant would alter the "
                      "enclosed body and would not faithfully resolve the F2P (and "
                      "would regress the P2P SVG-content tests). Supporting case: "
                      "confirms the frame clause guards BOTH read-only inputs.",
        "rationale": "draw_grouped_output holds only Acc(list_pred(children), 1/2). "
                     "The write children[j] = children[j] (value-neutral, in-bounds) "
                     "needs FULL permission, which the Acc(list_pred(children), 1/2) "
                     "Requires does not grant => rejected for INSUFFICIENT PERMISSION. "
                     "Source: the permission system + the frame clause.",
    },
    {
        "id": "partial-domain-no-group",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NOGROUP),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): the "
                      "container artist's draw drew its children with NO surrounding "
                      "group element, so the artist's gid never entered the rendered "
                      "SVG. The F2P test asserts the gid-bearing group start tag is IN "
                      "the saved SVG buffer; with no group emitted the gid is absent, "
                      "so the faithful patch does NOT resolve — exactly the bug the "
                      "gold patch fixes.",
        "rationale": "The result is just the body content (children): no start tag, no "
                     "id attribute, no end tag. LB-1 fails (output is ToSeq(children) "
                     "on both branches of grouped_output), and LB-2 fails (the id "
                     "attribute never appears). Source: both postcondition clauses.",
    },
    {
        "id": "partial-domain-drop-gid-empty-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_EMPTYID),
        "refinement": "A faithful real patch that opened a group but FORGOT to pass "
                      "the gid would emit a group framed with the renderer's "
                      "label-counter id, NOT the artist's gid. The F2P greps for the "
                      "gid-bearing start tag specifically, so the artist's gid still "
                      "would not reach the output as its id and the patch does NOT "
                      "resolve the test. (Modeled here as the strictly-empty id — both "
                      "drop the gid.)",
        "rationale": "The id attribute emitted is group_open_prefix() ++ attr_end() "
                     "(empty id value) — the gid loop is removed. Since "
                     "Requires(len(gid) > 0), ToSeq(gid) is non-empty, so "
                     "id_attribute(gid) differs: LB-1 fails (result lacks the gid run) "
                     "and LB-2 fails (id_attribute(gid) does not occur as a contiguous "
                     "run). The rival KEEPS the self-closing/framed branch, so the "
                     "rejection is attributable to the missing gid, not to a wrong "
                     "tag-termination form. Source: both postcondition clauses, on the "
                     "entire len(gid) > 0 domain.",
    },
    {
        "id": "partial-domain-omit-end-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NOCLOSE),
        "refinement": "A faithful real patch that called the renderer's group open but "
                      "omitted the matching close would leave an unbalanced start tag "
                      "open in the SVG. The output would be malformed (the group is "
                      "never closed before the document end), regressing the P2P "
                      "SVG-structure tests — the patch would not faithfully resolve "
                      "while keeping the suite green. The gid still appears, so a naive "
                      "'does the gid show up' check would miss it; the structural "
                      "equality catches the missing end tag. This is distinct from the "
                      "legal self-closing form, which the dialect permits ONLY when the "
                      "body is empty; here the body is non-empty.",
        "rationale": "The end-tag loop is removed from the non-empty-body branch, so "
                     "the result is opening_tag(gid) ++ children. LB-1 pins the "
                     "trailing group_close() on that branch, so it fails. (LB-2 still "
                     "holds — the id attribute occurs — which is why LB-1's FULL "
                     "structural equality, not just the existential, is load-bearing.) "
                     "Source: the group_close() sub-term of LB-1.",
    },
    {
        "id": "wrong-tag-termination-always-framed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ALWAYS_FRAMED),
        "refinement": "A faithful real patch cannot choose the tag-termination form: "
                      "the renderer decides it, writing the element self-closed when "
                      "NO body markup was emitted between the group's open and close "
                      "and framed otherwise. That empty-body case is REACHABLE for this "
                      "artist (a container whose frame is switched off and whose inner "
                      "content draws nothing emits no body markup), and on it the real "
                      "output carries no end tag. A model asserting the framed form "
                      "unconditionally therefore predicts markup the real callee never "
                      "produces on that class, so an implementation faithful to the "
                      "repo would FAIL such a spec while this rival would pass it. "
                      "This case exists so the branch cannot be silently dropped.",
        "rationale": "Emits opening_tag(gid) ++ children ++ group_close() "
                     "UNCONDITIONALLY, with no self-closing branch. On the empty-body "
                     "class grouped_output(gid, []) = self_closing_tag(gid), while the "
                     "rival returns opening_tag(gid) ++ group_close() — a different "
                     "sequence (it carries '>' then '</g>' where the real form carries "
                     "'/>'), so LB-1 fails. Source: the len(children) branch of "
                     "grouped_output, i.e. exactly the faithfulness content of the "
                     "deep model. Verified: Nagini reports 'Postcondition ... "
                     "ToSeq(Result()) == grouped_output(...) might not hold'.",
    },
    {
        "id": "non-termination-never-delivers-output",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DIVERGE),
        "refinement": "A faithful real patch of this shape — the container artist's "
                      "draw entering an unbounded loop (or otherwise never reaching "
                      "its return) once rendering has begun — never lets the figure "
                      "finish saving, so no SVG buffer is ever produced for the F2P to "
                      "grep. The gid is absent from the output for the same observable "
                      "reason as the pre-patch bug: nothing reached the output stream. "
                      "The REAL patched draw is straight-line (group open, "
                      "update_positions, the child draws, group close, return) with no "
                      "loop at all, so it always completes and delivers — totality is "
                      "TRUE of the gold patch and FALSE of this rival.",
        "rationale": "The full correct grouped output IS built (every gold markup / "
                     "body loop verbatim, so LB-1 and LB-2 are established), then an "
                     "unbounded `while 0 <= j` runs before the return. Under partial "
                     "correctness alone the unreachable return makes LB-1/LB-2 vacuous "
                     "and the impl VERIFIES; LB-0 (MustTerminate(2)) rejects it because "
                     "the added loop admits no strictly decreasing, bounded-below "
                     "measure. Source: the MustTerminate obligation in the "
                     "precondition — this case is the reason it is load-bearing.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom). The markup
# constants (group_open_prefix '<g id="', attr_end '"', tag_end '>',
# selfclose_end '/>', group_close '</g>') are an A-reference (deep model) already
# validated == the REAL renderer's element writing (via XMLWriter.start('g',
# id=gid) / .end('g')) by axiom_check.py (G-AX), which drives BOTH termination
# forms — including the empty-body self-closing form — and asserts the emitted
# bytes equal the deep model's grouped_output, 0 mismatch, matplotlib+stdlib only,
# exit 0. That IS the real-callee axiom lane for this instance; re-encoding it as
# a Docker probe would duplicate, not strengthen, it. See 'assessment' in the
# structured return.
AXIOM_TESTS = []
