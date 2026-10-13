import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms: the only unchanged callee whose behaviour the decision
   depends on — the response-status validator — is modeled DEEPLY by `isErrorStatus`
   (an A-reference, validated == the real callee by axiom_check.py / G-AX), not
   assumed behind a consumed axiom. -/
-- axioms-end

-- pure-start
/- The four terminal verdicts a link check can reach in the modeled branch. -/
inductive Status
  | working
  | broken
  | ignored
  | redirected
deriving DecidableEq, Repr

/- The provenance of the human-readable detail attached to a verdict. The
   discriminating payload of this task is which of these is emitted when the
   response carries an error status: the *response-status detail*
   (`httpError`) versus the *fragment-absent* notice (`anchorNotFound`). -/
inductive Detail
  | none
  | httpError       -- the response-status message string
  | anchorNotFound  -- the "fragment not present" notice
  | unauthorized    -- the constant "treated as reachable" note
deriving DecidableEq, Repr

structure Verdict where
  status : Status
  detail : Detail
  code   : Int
deriving DecidableEq, Repr

/- Deep model (A-reference) of the response-status validator: a response is an
   error iff its status is in the 4xx/5xx range. Validated == the real callee
   by axiom_check.py (G-AX). -/
def isErrorStatus (sc : Int) : Bool :=
  decide (400 ≤ sc ∧ sc < 600)

/- The verdict for a response whose status is an error: a couple of statuses
   are reclassified (one treated as reachable, one as deliberately skipped),
   every other error status is a failure carrying the response-status detail.
   This is the unchanged status handler (an identical-op transliteration). -/
def classifyError (sc : Int) : Verdict :=
  if sc = 401 then { status := .working, detail := .unauthorized, code := 0 }
  else
    (if sc = 503 then { status := .ignored, detail := .httpError, code := 0 }
     else { status := .broken, detail := .httpError, code := 0 })

/- The full verdict of the fragment-checking branch on a non-redirected
   response, as a function of the response status `sc` and whether the
   requested fragment is present (`found`). An error status determines the
   outcome via `classifyError` regardless of fragment presence; on a non-error
   response fragment presence decides (present ⇒ reachable, absent ⇒ failure
   carrying the fragment-absent notice). -/
def classify (sc : Int) (found : Bool) : Verdict :=
  if isErrorStatus sc then classifyError sc
  else
    (if found then { status := .working, detail := .none, code := 0 }
     else { status := .broken, detail := .anchorNotFound, code := 0 })
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this method needs no precondition: every
--  Int status / Bool fragment-flag is a legitimate input.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method checkFragmentBranch (statusCode : Int) (found : Bool) return (out : Verdict)
  ensures out = classify statusCode found
  do
    -- impl-start
    -- Fragment-checking branch on a non-redirected response: `statusCode` is the
    -- received HTTP status and `found` records whether the requested fragment is
    -- present. An error status is routed to the status handler; a non-error
    -- response lets fragment presence decide the outcome.
    let out : Verdict :=
      if isErrorStatus statusCode then
        (if statusCode = 401 then { status := .working, detail := .unauthorized, code := 0 }
         else
           (if statusCode = 503 then { status := .ignored, detail := .httpError, code := 0 }
            else { status := .broken, detail := .httpError, code := 0 }))
      else
        (if found then { status := .working, detail := .none, code := 0 }
         else { status := .broken, detail := .anchorNotFound, code := 0 })
    return out
    -- impl-end

prove_correct checkFragmentBranch by
  loom_solve
  simp only [classify, classifyError]
