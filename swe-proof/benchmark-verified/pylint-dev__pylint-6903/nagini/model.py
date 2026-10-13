"""Twin-artifact model for pylint-dev__pylint-6903.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine determines how many processing units are allotted to the current
  containerised environment by reading, when present, the relevant resource
  files and dividing the configured allowance by its base unit (truncating any
  fractional part downwards). The available files determine which allowance is
  used; when none is present the count is left undetermined.

  The single hard requirement the consumers downstream impose is that, whenever
  a count IS determined, it must be a usable count: a worker pool cannot be
  launched with a fraction of a unit, so a determined count is never zero. When
  the truncated division would yield zero (the allowance is a strictly positive
  but sub-unit fraction), the count is raised to the smallest usable value, one.
  An undetermined count stays undetermined.

The parsed file contents are modelled as plain integers gated by presence
flags; the real routine's truncating TRUE division `int(a / b)` (Python float
division, then truncation toward zero) is modelled as integer floor division
`//`. The two agree exactly on the float-exact operand domain 0 <= a < 2**53,
1 <= b < 2**53, and the model's preconditions bound the domain accordingly
(allowances and unit < 2**53 = 9007199254740992): every cgroup CPU value is
far inside that range, and outside it IEEE-754 rounding could make
`int(a/b) != a//b` — see refinement.md / mapping.md / axiom_check.py. The
undetermined ("no file present") outcome is modelled as the absence of a
result via `Optional[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the routine calls no external opaque callee whose contract the
#  proof consumes. The only modelled operations are integer reads, the
#  truncating division of two non-negative integers, comparisons and the raise
#  to the smallest usable value -- all expressed directly. The fidelity of the
#  truncating-division model `int(a/b) == a // b` on the in-range domain is an
#  out-of-band deep-model check, not a consumed axiom: see axiom_check.py.)
# axioms-end


# pure-start
@Pure
def usable(n: int) -> int:
    """Raise a determined count to the smallest usable value: a sub-unit count
    (which truncated to zero) becomes one; any already-usable count is kept."""
    if n == 0:
        return 1
    return n


@Pure
def determined_count(
    primary_present: bool,
    primary_allowance: int,
    primary_unit_present: bool,
    primary_unit: int,
    fallback_present: bool,
    fallback_allowance: int,
) -> Optional[int]:
    """The fully determined count, given the parsed inputs. Mirrors the routine's
    branch structure: the primary allowance is used when it is present, strictly
    positive (a sentinel of -1 is treated as 'not configured') and its base unit
    is present; otherwise the fallback allowance is used when present; otherwise
    the count is undetermined. The chosen truncated division is then raised to
    the smallest usable value."""
    Requires(primary_unit > 0)
    Requires(fallback_allowance >= 0)
    # Float-exact bounds (2**53): on this domain the real truncating true
    # division int(a/b) coincides with the model's floor division a // b.
    Requires(primary_allowance < 9007199254740992)
    Requires(primary_unit < 9007199254740992)
    Requires(fallback_allowance < 9007199254740992)
    if primary_present and primary_allowance > 0 and primary_unit_present:
        return usable(primary_allowance // primary_unit)
    if fallback_present:
        return usable(fallback_allowance // 1024)
    return None
# pure-end


def query_units(
    primary_present: bool,
    primary_allowance: int,
    primary_unit_present: bool,
    primary_unit: int,
    fallback_present: bool,
    fallback_allowance: int,
) -> Optional[int]:
    # pre-conditions-start
    # The base unit is a strictly positive divisor; the parsed allowances/units
    # are non-negative counts (the only negative the routine ever sees is the
    # -1 'not configured' sentinel, which the primary branch's `> 0` guard
    # already excludes -- so the divisions below are over non-negative operands).
    Requires(primary_unit > 0)
    Requires(primary_allowance >= -1)
    Requires(fallback_allowance >= 0)
    # Float-exact upper bounds: the real routine computes int(a / b) via Python
    # TRUE (float) division; that equals the model's floor division a // b only
    # while the operands stay in the float-exact range (< 2**53). The model is
    # a faithful refinement exactly on this domain, so the preconditions pin it
    # (cgroup CPU quotas/periods/shares are tiny by comparison in reality).
    Requires(primary_allowance < 9007199254740992)
    Requires(primary_unit < 9007199254740992)
    Requires(fallback_allowance < 9007199254740992)
    # TERMINATION: the routine is a bounded, loop-free decision over already-
    # parsed values and always returns; the postconditions alone hold vacuously
    # for a diverging body, so this obligation rejects any implementation that
    # never delivers its result.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the determined count for these inputs: undetermined
    # exactly when the determined count is undetermined, and otherwise equal to
    # it.
    Ensures((Result() is None) == (determined_count(
        primary_present, primary_allowance, primary_unit_present,
        primary_unit, fallback_present, fallback_allowance) is None))
    Ensures(Implies(Result() is not None,
                    Result() == determined_count(
                        primary_present, primary_allowance, primary_unit_present,
                        primary_unit, fallback_present, fallback_allowance)))  # type: ignore[operator]
    # The discriminating guarantee: a determined count is never zero -- it is
    # either undetermined (no file present) or a strictly positive usable count.
    Ensures(Result() is None or Result() > 0)  # type: ignore[operator]
    # Whenever a count is determined it equals the truncated division raised to
    # the smallest usable value (so a strictly-positive sub-unit fraction, which
    # truncates to zero, yields one rather than zero).
    Ensures(Implies(primary_present and primary_allowance > 0 and primary_unit_present,
                    Result() is not None and Result() == usable(primary_allowance // primary_unit)))  # type: ignore[operator]
    Ensures(Implies(not (primary_present and primary_allowance > 0 and primary_unit_present)
                    and fallback_present,
                    Result() is not None and Result() == usable(fallback_allowance // 1024)))  # type: ignore[operator]
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
