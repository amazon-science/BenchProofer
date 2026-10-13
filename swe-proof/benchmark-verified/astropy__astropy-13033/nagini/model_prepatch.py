"""Twin-artifact model for astropy__astropy-13033.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular container is allowed to declare an ordered list of column names it
  must begin with. When that leading run is found to disagree with what the
  container actually carries, the container reports the disagreement to the
  user. The report names the full ordered run of names that was demanded AND
  the full ordered run of names that was actually found at those leading
  positions. Concretely:

    (1) A run of names is rendered for the message as follows. A run of exactly
        one name is rendered as that lone name wrapped in apostrophes (e.g. a
        run whose only name is n0 renders as 'n0'). A run of any other length
        is rendered as the ordinary textual list form: an opening bracket, then
        every name in order each wrapped in apostrophes and separated by a
        comma and a space, then a closing bracket (e.g. a run of the names
        n0, n1 renders as ['n0', 'n1']). Thus every name in a multi-name run
        appears in the rendering, in order.

    (2) The full report is the container's class name, the constant connective
        text, the rendering of the demanded run, the constant phrase naming the
        leading position(s) -- pluralised exactly when more than one name is
        demanded -- and the rendering of the run actually found. When more than
        one name is demanded the report therefore shows the entire demanded run
        and the entire found run, so the reader sees every demanded and every
        found name and their order.

    (3) Rendering a run and assembling the report are each something the
        container CARRIES OUT TO COMPLETION: for every run it is allowed to be
        asked about -- of any length, including the multi-name runs of (1) and
        the boundary lengths zero and one -- it finishes in finitely many steps.
        Describing the disagreement is a task the container brings to an end,
        never an activity it embarks on and never finishes: the reader is not
        left waiting on a report the container is still working out, and there
        is no admissible run on which it may work forever. What the container
        must have to show when the task ends is the separate demand (5) makes;
        this clause asks only that the task end. It is demanded of every input
        the surrounding clauses admit, so it is an obligation the container
        discharges rather than a restriction on which runs may be asked about.

    (4) Describing a disagreement only READS what it was handed. Rendering a
        run, and assembling the report, both leave the runs they were given
        exactly as they found them -- every name still present, in the same
        order -- and likewise the class name. So the report describes the runs
        AS GIVEN: the container cannot bring the report into agreement with a
        run it rewrote on the way, and a caller that keeps using those
        collections afterwards (the container's own declared list of names
        among them) still holds the names it held before it asked. This is
        required however the runs were supplied -- including when the demanded
        run and the found run are handed over as one and the same collection,
        the case in which a container able to read both of them at once would
        also be able to write to it.

    (5) Delivering the rendering / the report is moreover the ONLY way either
        task may end. A container that is asked to describe a disagreement may
        not answer with a failure instead of a description: there is no
        admissible run, and no admissible pair of runs, on which rendering or
        assembly is permitted to abandon the request and leave by signalling
        trouble. Note that this says something (3) does not. (3) forbids a task
        that never ends; a task that ends promptly and empty-handed satisfies
        (3), satisfies (4) -- it rewrote nothing, because it did nothing -- and
        still leaves the reader with no idea which names were demanded or which
        were found: the disagreement is signalled and nothing whatever about it
        is said. So (5) is the clause that turns (1) and (2) from an account of
        what a report WOULD say, had one been produced, into an entitlement to
        actually be told. Like (3) it is demanded of every input the surrounding
        clauses admit, so it obliges the container rather than restricting which
        runs may be asked about.

Modelling choices (Nagini fragment):
  * What the specification pins is structural: where the brackets, apostrophes,
    comma-space separators and plural marker fall, and that EVERY name of a
    multi-name run appears in the rendering, in order. The internal spelling of
    each individual name is reproduced verbatim and is therefore irrelevant to
    the structure, so each column name is modelled as one distinct token (an
    `int >= 0`); a run of names is a `List[int]` (carrier) / `PSeq[int]`
    (specification). The rendering is a sequence over a token-and-punctuation
    alphabet: a token `t` denotes that name; the punctuation code points are
    literal (apostrophe NAME_QUOTE, comma+space, brackets). refinement.md /
    mapping.md give the bijection token <-> real name string, and
    axiom_check.py validates the rendering equals the real textual list form
    `str(run)` / the apostrophe form by substituting the real strings for
    tokens. No string indexing is used (Nagini bans it).
  * The rendering and report assembly are modelled DEEPLY (front-recursive
    folds + a verified construction loop), not behind a consumed axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
# Completion obligations (clause (3)): a measure that must strictly decrease at
# every call/iteration, so a function discharges its contract only by actually
# ENDING -- an unfinishable computation cannot satisfy the clauses above by never
# getting to the point of answering. Ending is not yet answering: a computation
# that ends by signalling reaches no return and so satisfies every Ensures
# vacuously, which is why clause (5)'s Exsures stands beside this.
from nagini_contracts.obligations import MustTerminate

# Punctuation code points used by the rendering (literal, never a name token).
# Name tokens are non-negative and are emitted via the dedicated NAME wrapper,
# kept disjoint from these by encoding (see encode_name below).
NAME_QUOTE = 39   # "'"
COMMA = 44        # ","
SPACE = 32        # " "
LBRACK = 91       # "["
RBRACK = 93       # "]"


# axioms-start
# No consumed axioms. The rendering and report assembly are the behaviour under
# specification and are modelled deeply (the pure folds below + the impl loops
# spell them out). The only library behaviour relied on is the ordinary textual
# list form of a list of names and the apostrophe-wrapped single name, both
# validated out-of-band by axiom_check.py (G-AX) as A-references.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def encode_name(t: int) -> int:
    """Encode a name token disjointly from the punctuation code points, so a
    name can never be confused with an apostrophe/comma/bracket in the
    rendering. Names are emitted as (token + 256)."""
    return t + 256


@Pure
def quoted(t: int) -> PSeq[int]:
    """One name token wrapped in apostrophes: 'name'."""
    return PSeq(NAME_QUOTE) + PSeq(encode_name(t)) + PSeq(NAME_QUOTE)


@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The comma-and-space separated apostrophe-wrapped names, in order
    (no surrounding brackets). Front-recursive so a single unfold is available
    per construction step. Empty for an empty run; just the quoted lone name
    for a single-name run."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return quoted(run[0])
    return quoted(run[0]) + PSeq(COMMA, SPACE) + joined(run.drop(1))


@Pure
def render_run(run: PSeq[int]) -> PSeq[int]:
    """The message rendering of a run of names: a single name appears as the
    bare apostrophe-wrapped name; any other length appears as the bracketed
    textual list form [ 'n0', 'n1', ... ]."""
    if len(run) == 1:
        return quoted(run[0])
    return PSeq(LBRACK) + joined(run) + PSeq(RBRACK)


@Pure
def report_seq(cls_name: PSeq[int], demanded: PSeq[int],
               found: PSeq[int]) -> PSeq[int]:
    """The full report: class name, connective text, the rendering of the
    demanded run, the leading-position phrase pluralised when more than one
    name is demanded, and the rendering of the found run."""
    # " object is invalid - expected "
    seg1 = PSeq(32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
                118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
                116, 101, 100, 32)  # type: PSeq[int]
    # " as the first column"
    seg2 = PSeq(32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
                32, 99, 111, 108, 117, 109, 110)  # type: PSeq[int]
    # plural marker: "s" when more than one name is demanded, else ""
    plural = PSeq(115) if len(demanded) > 1 else empty_seq()  # type: PSeq[int]
    # " but found "
    seg3 = PSeq(32, 98, 117, 116, 32, 102, 111, 117, 110, 100,
                32)  # type: PSeq[int]
    return (cls_name + seg1 + render_run(demanded) + seg2 + plural + seg3
            + render_run(found))
# pure-end


def render_name_run(run: List[int]) -> List[int]:
    """Render one run of column names per (1) above: a lone name wrapped in
    apostrophes, any other length as the bracketed textual list form."""
    # pre-conditions-start
    Requires(Acc(list_pred(run), 1 / 2))
    # (3): the rendering of `run` is carried out to completion, for a run of ANY
    # length -- the caller is not left waiting on a rendering that never arrives.
    # That the run ends WITH a rendering is clause (5) below, not this clause: a
    # renderer that stops at once by signalling ends too. The budget grows with
    # the run, so working the run down name
    # by name is allowed; what is ruled out is coming back round to render a run
    # no shorter than this one. Demanded of every admissible run, so this obliges
    # the renderer; it restricts no input.
    Requires(MustTerminate(len(run) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(run), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the run handed in is only READ. Its names, and their order, are the
    # same on the way out as on the way in, so the rendering below is a
    # rendering of the run the caller passed -- not of one the renderer
    # rewrote first -- and the caller still holds what it held.
    Ensures(ToSeq(run) == Old(ToSeq(run)))
    Ensures(ToSeq(Result()) == render_run(ToSeq(run)))
    # (5): the rendering is HANDED BACK, never signalled away. There is no
    # admissible run on which the renderer may abandon the request and leave by
    # the failure exit instead of answering: the only way out of a rendering is
    # WITH a rendering. Together with (3) this is what makes the value clause
    # above an obligation about a rendering the caller ACTUALLY RECEIVES -- (3)
    # rules out never finishing, this rules out finishing without an answer, and
    # neither alone is enough. Demanded on every admissible run, so it obliges
    # the renderer and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    run_s = ToSeq(run)  # type: PSeq[int]
    if len(run) == 1:
        out_single = [NAME_QUOTE, encode_name(run[0]), NAME_QUOTE]  # type: List[int]
        Assert(ToSeq(out_single) == quoted(run_s[0]))
        Assert(ToSeq(out_single) == render_run(run_s))
        return out_single
    # any other length -> bracketed textual list form
    inner = []  # type: List[int]
    i = len(run)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(run), 1 / 2))
        Invariant(Acc(list_pred(inner)))
        Invariant(0 <= i and i <= len(run))
        Invariant(run_s == ToSeq(run))
        Invariant(ToSeq(inner) == joined(run_s.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = run[i - 1]  # type: int
        Assert(run_s.drop(i - 1)[0] == elt)
        Assert(run_s.drop(i - 1).drop(1) == run_s.drop(i))
        if i == len(run):
            # last name: no trailing separator
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE]
            Assert(ToSeq(inner) == quoted(elt))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        else:
            inner = [NAME_QUOTE, encode_name(elt), NAME_QUOTE, COMMA, SPACE] + inner
            Assert(ToSeq(inner) == quoted(elt) + PSeq(COMMA, SPACE)
                   + joined(run_s.drop(i)))
            Assert(ToSeq(inner) == joined(run_s.drop(i - 1)))
        i = i - 1
    result = [LBRACK] + inner + [RBRACK]  # type: List[int]
    Assert(ToSeq(result) == PSeq(LBRACK) + joined(run_s) + PSeq(RBRACK))
    Assert(ToSeq(result) == render_run(run_s))
    return result
    # impl-end


def compose_leading_run_report(cls_name: List[int],
                                 demanded: List[int],
                                 found: List[int]) -> List[int]:
    """Assemble the full disagreement report per (2): the rendering of the
    whole demanded run and the whole found run, with the pluralised
    leading-position phrase."""
    # pre-conditions-start
    Requires(Acc(list_pred(cls_name), 1 / 2))
    Requires(Acc(list_pred(demanded), 1 / 2))
    Requires(Acc(list_pred(found), 1 / 2))
    # (3): the report is assembled to completion, for demanded and found runs of
    # ANY lengths -- the assembly may not go on forever. That it ends WITH a
    # report is clause (5) below, which this clause does not contain.
    # The budget exceeds what rendering either run
    # takes, so assembling a report may render both runs and still be obliged to
    # finish. Demanded of every admissible pair of runs, so this obliges the
    # assembly; it restricts no input.
    Requires(MustTerminate(len(demanded) + len(found) + 6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cls_name), 1 / 2))
    Ensures(Acc(list_pred(demanded), 1 / 2))
    Ensures(Acc(list_pred(found), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (4): the report is assembled by READING what it was given. The class
    # name, the demanded run and the found run each come back carrying the same
    # names in the same order they arrived with, so the report below describes
    # the runs AS GIVEN. This is required of every admissible triple, the
    # aliased one included: when two of the three are one and the same
    # collection the assembly can read them both at once and could therefore
    # write, and a report agreeing with the rewritten names would otherwise
    # count as describing the disagreement.
    Ensures(ToSeq(cls_name) == Old(ToSeq(cls_name)))
    Ensures(ToSeq(demanded) == Old(ToSeq(demanded)))
    Ensures(ToSeq(found) == Old(ToSeq(found)))
    Ensures(ToSeq(Result()) == report_seq(ToSeq(cls_name),
                                           ToSeq(demanded), ToSeq(found)))
    # (5): the report is HANDED BACK, never signalled away. On no admissible
    # triple of runs may the assembly leave by the failure exit instead of
    # delivering the report: the only way out of describing the disagreement is
    # WITH the description. This is the clause the reader's entitlement in (3)
    # actually rests on -- an assembly that stopped promptly, and so satisfied
    # every completion and preservation clause here, but left by the failure exit
    # would tell the reader nothing about which names were demanded and which
    # were found, which is the whole content of the report. Demanded on every
    # admissible triple, so it obliges the assembly and restricts no input.
    Exsures(Exception, False)
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) report assembly: each run is rendered by echoing only
    # its FIRST name, apostrophe-wrapped, regardless of how many names the run
    # actually has. For a multi-name run this drops every name after the first
    # -- exactly the misleading report the change repairs.
    if len(demanded) >= 1:
        expected_field = [NAME_QUOTE, encode_name(demanded[0]), NAME_QUOTE]  # type: List[int]
    else:
        expected_field = []
    if len(found) >= 1:
        found_field = [NAME_QUOTE, encode_name(found[0]), NAME_QUOTE]  # type: List[int]
    else:
        found_field = []
    # " object is invalid - expected "
    seg1 = [32, 111, 98, 106, 101, 99, 116, 32, 105, 115, 32, 105, 110,
            118, 97, 108, 105, 100, 32, 45, 32, 101, 120, 112, 101, 99,
            116, 101, 100, 32]  # type: List[int]
    # " as the first column"
    seg2 = [32, 97, 115, 32, 116, 104, 101, 32, 102, 105, 114, 115, 116,
            32, 99, 111, 108, 117, 109, 110]  # type: List[int]
    if len(demanded) > 1:
        plural = [115]  # type: List[int]
    else:
        plural = []
    # " but found "
    seg3 = [32, 98, 117, 116, 32, 102, 111, 117, 110, 100, 32]  # type: List[int]
    result = (cls_name + seg1 + expected_field + seg2 + plural + seg3
              + found_field)  # type: List[int]
    Assert(ToSeq(result) == report_seq(ToSeq(cls_name),
                                        ToSeq(demanded), ToSeq(found)))
    return result
    # impl-end
