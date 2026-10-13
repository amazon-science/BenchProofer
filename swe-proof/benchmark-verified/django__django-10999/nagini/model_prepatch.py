"""Twin-artifact model for django__django-10999.

Behavioural contract (the result a correct interpretation must produce):

  The operation interprets a colon-separated clock literal into a single
  signed total measured in the smallest unit (seconds). Its inputs are the
  already-extracted carrier of the literal:

    * `fields`  — the 1..3 ordered non-negative field magnitudes;
    * `leading_minus` — whether the literal carried a sign;
    * `inner_sign_seen` — whether the literal's shape is the malformed one
      that has no interpretation.

  The contract on the result, formalised by the `Ensures` clauses below:

    * When the literal has an interpretation, the result equals
      `signed_total(fields, leading_minus)` — the positional base-60
      combination of the fields (`clock_value`) under the sign flag. The
      `clock_value` / `signed_total` helpers spell this arithmetic out so the
      contract is grounded in the inputs, not pinned to an external oracle.

    * When `inner_sign_seen` holds, the literal has no interpretation and the
      result is the absent value.

  The field magnitudes and the two flags are the type-refinement carrier of
  the underlying string literal; the unchanged field-magnitude extraction (a
  run of decimal digits read as a non-negative integer) is the refinement
  boundary documented in mapping.md.

Strings/fields are modelled as `List[int]` of non-negative field magnitudes
(Nagini bans `str` indexing); the specification is carried by `PSeq[int]`. The
absent value is `None`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof: the signed-total
#  interpretation and the validity rule are the changed behaviour and are
#  modelled deeply below. The unchanged decimal-digit field extraction is a
#  type refinement, documented in mapping.md, not an axiom.)
# axioms-end


# pure-start
@Pure
def clock_value(fields: PSeq[int]) -> int:
    """Positional base-60 combination of 1..3 non-negative clock fields, read
    right-to-left: the last field is seconds, the previous minutes, the first
    hours. Front-recursive so a single unfold is available per step.

    For `[H, M, S]` -> `H*3600 + M*60 + S`; `[M, S]` -> `M*60 + S`;
    `[S]` -> `S`; `[]` -> 0.
    """
    if len(fields) == 0:
        return 0
    # The leading field's positional weight is 60**(len-1): hours when 3
    # fields remain, minutes when 2, seconds when 1.
    return fields[0] * pow60(len(fields) - 1) + clock_value(fields.drop(1))


@Pure
def pow60(k: int) -> int:
    """60 ** k for the clock positions k in {0, 1, 2}."""
    Requires(k >= 0)
    Ensures(Result() >= 1)
    if k == 0:
        return 1
    return 60 * pow60(k - 1)


@Pure
def signed_total(fields: PSeq[int], leading_minus: bool) -> int:
    """The signed total: `clock_value(fields)` under the sign flag, i.e.
    `-clock_value(fields)` when `leading_minus` else `clock_value(fields)`."""
    if leading_minus:
        return -clock_value(fields)
    return clock_value(fields)
# pure-end


def parse_clock_seconds(fields: List[int], leading_minus: bool,
                        inner_sign_seen: bool) -> Optional[int]:
    # pre-conditions-start
    # `fields` are the extracted non-negative field magnitudes (read-only);
    # 1..3 of them (seconds; or minutes:seconds; or hours:minutes:seconds).
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(1 <= len(fields) and len(fields) <= 3)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(fields),
                                             fields[k] >= 0), [[fields[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    # The malformed shape has no interpretation: the absent value.
    Ensures(Implies(inner_sign_seen, Result() is None))
    # Otherwise the result is the grounded signed positional total of the
    # fields under the sign flag (clock_value / signed_total).
    Ensures(Implies(not inner_sign_seen,
                    Result() is not None and
                    Result() == signed_total(ToSeq(fields), leading_minus)))
    # post-conditions-end
    # impl-start
    if inner_sign_seen:
        return None
    # Pre-patch skeleton: the leading sign is attached to only the FIRST
    # field's magnitude, not to the whole clock value. We accumulate the
    # positional magnitude right-to-left; the leading field's contribution
    # (hours when 3 fields, minutes when 2, seconds when 1) is captured as it
    # is consumed (last iteration, i == 1) and then sign-flipped on its own,
    # leaving the rest of the value positive.
    total = 0  # type: int
    weight = 1  # type: int
    lead_contrib = 0  # type: int
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(weight == pow60(len(fields) - i))
        Invariant(total == clock_value(ToSeq(fields).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        Assert(len(ToSeq(fields).drop(i - 1)) == len(fields) - (i - 1))
        contrib = fields[i - 1] * weight
        total = contrib + total
        if i == 1:
            lead_contrib = contrib
        weight = weight * 60
        i = i - 1
    Assert(total == clock_value(ToSeq(fields)))
    if leading_minus:
        return total - 2 * lead_contrib
    return total
    # impl-end
