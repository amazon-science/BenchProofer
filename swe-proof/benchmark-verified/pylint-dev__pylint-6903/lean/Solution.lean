import Mathlib
-- imports-end

/-!
Deriving a usable processor count from control-group accounting.

A containerized process estimates how many processors it may use by reading
control-group accounting values. Two such values may be published:

  * a *quota / period* pair — an absolute allowance, present only when a positive
    quota (other than the "no quota" sentinel `-1`) and a period are both
    available; the count is the quota divided by the period;
  * a relative *share* — a weight published as a multiple of `1024`; the count is
    the share divided by `1024`.

The quota/period pair takes precedence when usable; otherwise the share is used;
if neither value is available the count is *undetermined*.

The integer divisions truncate toward zero, so a small allowance (for example a
share smaller than `1024`, as when only a fraction of a single processor is
granted) can yield a computed count of zero. Because a usable process count must
be at least one, a computed count of zero is reported as one. Any other computed
count — and the *undetermined* result — is reported unchanged.

This is stated abstractly as an input→output relation from the three optional
accounting values to the reported count; the implementation and the correctness
proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the three accounting
-- values enter as plain optional integers (present-with-contents vs absent), and
-- the count derivation is a self-contained integer computation modeled directly
-- (a branch selection, two truncating divisions, and a zero→one adjustment).
-- Hence no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The computed count BEFORE the minimum-of-one adjustment, as a function of the
three optional accounting values (each `some v` when present with contents `v`,
`none` when absent):

  * if a quota and a period are both present and the quota is neither `0` nor the
    "no quota" sentinel `-1`, the count is the quota divided by the period
    (truncating toward zero);
  * otherwise, if a share is present, the count is the share divided by `1024`;
  * otherwise the count is undetermined (`none`).

`Int.tdiv` truncates toward zero, matching the reference integer division
(which divides and then truncates the quotient toward zero) on every pair of
integer operands. -/
def rawCpu (cpuQuotaFile cpuPeriodFile cpuSharesFile : Option Int) : Option Int :=
  match cpuQuotaFile, cpuPeriodFile with
  | some q, some p =>
      if q ≠ 0 ∧ q ≠ -1 then
        some (q.tdiv p)
      else
        match cpuSharesFile with
        | some s => some (s.tdiv 1024)
        | none   => none
  | _, _ =>
      match cpuSharesFile with
      | some s => some (s.tdiv 1024)
      | none   => none
-- pure-end

-- post-conditions-start
/-- The reported count is fully pinned to the three accounting values: it is the
computed count (`rawCpu`) with one adjustment — a computed count of exactly zero
is reported as one. Every other computed count, and the undetermined result, is
reported unchanged. The result is therefore never an available count of zero. -/
def problem_spec_availableCpus
    (cpuQuotaFile cpuPeriodFile cpuSharesFile : Option Int) (result : Option Int) : Prop :=
  result = (if rawCpu cpuQuotaFile cpuPeriodFile cpuSharesFile = some 0
            then some 1
            else rawCpu cpuQuotaFile cpuPeriodFile cpuSharesFile)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
