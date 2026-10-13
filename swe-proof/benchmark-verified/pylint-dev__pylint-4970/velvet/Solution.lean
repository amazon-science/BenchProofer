import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the changed entry point calls only its own unchanged
--  sibling helpers, modeled here as the precomputed read-only report input and
--  the deep copy operation. There is no outside opaque callee whose contract
--  the proof consumes.)
-- axioms-end

-- pure-start
-- (No pure helpers needed: the emitted content is the report sequence itself,
--  written out verbatim and in order.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A duplicate-code search is parameterised by a non-negative threshold giving
   the minimum number of successive lines two chunks must share to count as a
   duplication. A standalone entry point produces a report and writes it to an
   output buffer.

   The threshold acts as an ENABLE switch: a threshold of zero means the search
   is DISABLED, so the entry point produces no report at all — its output buffer
   stays empty. For any positive threshold the search runs and the entry point
   writes the whole report it produces to the output buffer, verbatim and in
   order.

   The report is modeled as a sequence of integers (each integer standing for
   one emitted record); for a positive threshold the report is always non-empty,
   because it always carries a summary record. The report is a read-only input
   describing what the display step would write; the output buffer is the only
   object produced. For a positive threshold the output ends up equal to the
   report. Inputs are read-only (not `mut`): the threshold and the report are
   never mutated (directive 5). The threshold is a `Nat`; the report and the
   output are `List Int`. -/
method emit (minLines : Nat) (report : List Int) return (out : List Int)
  require minLines > 0 → report ≠ []
  ensures minLines = 0 → out = []
  ensures minLines > 0 → out = report
  ensures minLines > 0 → out ≠ []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- The backward-copy step: dropping one fewer element exposes the element at
   `i-1` on the front, so the running copy gains exactly that element. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma drop_copy_step (report : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ report.length) :
    report.drop (i - 1) = report[i - 1]! :: report.drop i := by
  have hlt : i - 1 < report.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

prove_correct emit by
  -- proof elided — supplied by the consumer
