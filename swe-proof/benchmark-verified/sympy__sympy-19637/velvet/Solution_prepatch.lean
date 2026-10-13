import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The recoverable failure shape of the marker-presence step: the step is asked
   to report a flag, and on one path the earlier-stage value it consults has
   never been established. Reifying that "value not established" outcome as the
   error leg of `Except` lets the desired behavior insist the step is TOTAL — it
   must always yield a flag and never surface this failure. This is the only
   failure the desired behavior distinguishes. -/
inductive MarkerError where
  | markerUnavailable
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The intended value of the marker-presence flag for a working string `s`:
   `true` exactly when a substitution marker is present in `s`, `false`
   otherwise. The flag is total — defined for every `s` — and is the membership
   of the distinguished marker code point in `s` (mapping.md §2, §3). -/
def markerFlag (s : List Char) : Bool :=
  s.contains ' '
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Report whether a substitution marker is present in a working string, as a
   flag consulted by a later recovery step.

   Desired behavior: the step inspects the working string `s` and decides the
   flag from whether a substitution marker was introduced into it. When a marker
   is present the flag is set accordingly; when no marker is present the flag is
   simply `false`. The step is TOTAL: for every working string it yields a flag
   and never fails — in particular it must still yield `false` (not surface a
   failure) on the path where no marker was ever introduced. The result is the
   success leg carrying the flag (`out = Except.ok (markerFlag s)`); the failure
   leg is never produced.

   `s` is the read-only working string (not `mut`): the step inspects it and
   mutates nothing (directive 5). The string is modeled as a `List Char` (a
   per-code-point string) and the marker as the distinguished space code point
   (mapping.md §2). -/
method markerPresent (s : List Char) return (out : Except MarkerError Bool)
  ensures out = Except.ok (markerFlag s)
  do
    -- impl-start
    -- PRE-PATCH (buggy): the flag is read from the marker value WITHOUT
    -- establishing it on the path where no marker was introduced. When a marker
    -- is present the membership is reported; when none is present the consulted
    -- value was never established and the step surfaces the failure leg instead
    -- of yielding `false` — exactly the defect the problem statement reports.
    let out : Except MarkerError Bool :=
      if s.contains ' ' then Except.ok true
      else Except.error MarkerError.markerUnavailable
    return out
    -- impl-end

prove_correct markerPresent by
  loom_solve
  simp only [markerFlag]
  split <;> simp_all
