import Mathlib
-- imports-end

-- axioms-start
-- The per-file records produced by the unchanged inner processing pass are taken
-- as INPUTS to the orchestration under spec (it merely consumes and re-reports
-- them). No unchanged callee is invoked inside the modeled orchestration itself,
-- so there is no `opaque` callee and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- A single record reported by one processing pass for one source file:
* `name`       — the original source file name;
* `storedName` — the optional name under which the result was stored;
* `outcome`    — the per-file result, either a normal processed flag
  (`Except.ok`) or a signalled error (`Except.error`);
* `rewrote`    — whether that pass had to rewrite a reference inside the file,
  so that a further pass over the adjustable files would still have work to do. -/
structure PassRecord where
  name : String
  storedName : Option String
  outcome : Except String Bool
  rewrote : Bool

/-- The 3-component item reported to the caller for one file. -/
abbrev OutItem := String × Option String × Except String Bool

/-- What one invocation hands to its caller, split at the one instant the caller
can distinguish: the moment the run's accumulated name mapping is committed to
the shared store the caller reads afterwards.
* `.1` — the items handed over BEFORE that instant. A caller that stops at the
  first item carrying a signalled error has received exactly a prefix of these,
  and the shared store is still what it was when the invocation began;
* `.2` — the items held back and handed over only after every pass has ended and
  the mapping has been committed.
Both components are ordered as the caller receives them. -/
abbrev OutReport := List OutItem × List OutItem

/-- The item a record is reported as (drops the per-pass bookkeeping flag). -/
def PassRecord.toItem (r : PassRecord) : OutItem := (r.name, r.storedName, r.outcome)

/-- Whether a record's outcome signals an error rather than a normal flag. -/
def PassRecord.isError (r : PassRecord) : Bool :=
  match r.outcome with
  | .error _ => true
  | .ok _ => false

/-- Insert-or-update an association list keyed by file name, preserving the
order of first insertion: if `k` already occurs its value is replaced in place;
otherwise the pair is appended at the end. This is the order-preserving
keyed collection used to report each file exactly once. -/
def upsertItem (m : List (String × OutItem)) (k : String) (v : OutItem) :
    List (String × OutItem) :=
  if m.any (fun p => p.1 == k) then
    m.map (fun p => if p.1 == k then (k, v) else p)
  else
    m ++ [(k, v)]

/-- One step of the first pass over the paired state `(handedOver, collected)`:
a file that is not adjustable, or whose outcome is an error, is handed to the
caller immediately; an adjustable file with a normal outcome is set aside in the
order-preserving collection (to be reported once, later). -/
def firstStep (adjustable : List String)
    (st : List OutItem × List (String × OutItem)) (r : PassRecord) :
    List OutItem × List (String × OutItem) :=
  if (! adjustable.contains r.name) || r.isError then
    (st.1 ++ [r.toItem], st.2)
  else
    (st.1, upsertItem st.2 r.name r.toItem)

/-- One step over the further passes, on the paired state
`(collected, unsettled)`: every record of the pass replaces that file's entry in
the order-preserving collection, and the `unsettled` component becomes this
pass's own — it starts each pass cleared and is set by any record of that pass
which rewrote a reference, so after a pass it says whether THAT pass rewrote
anything, and after the last one whether the run was still moving when the
allowance of passes was used up. -/
def laterStep (st : List (String × OutItem) × Bool) (pass : List PassRecord) :
    List (String × OutItem) × Bool :=
  (pass.foldl (fun d r => upsertItem d r.name r.toItem) st.1,
   pass.any (fun r => r.rewrote))

/-- The extra item handed to the caller when the further passes end with the run
still moving: it stands for no single source file, carries no stored name, and
its outcome is a signalled error naming the exhausted allowance. -/
def allowanceItem : OutItem :=
  ("All", none, Except.error "Max post-process passes exceeded.")

/-- The full report of one invocation, given the adjustable file names, the first
pass's records, and the records of each further pass.

Handed over before the mapping is committed: every non-adjustable file and every
signalled error of the first pass, in first-pass order, and then — only when the
last further pass was still rewriting references — the extra item standing for
the exhausted allowance. Handed over after the mapping is committed: each
adjustable file that the first pass processed normally, exactly once, in order of
first appearance, carrying the stored name it has once the passes have finished
(a later pass replaces an earlier value in place). -/
def postProcessModel (adjustable : List String) (firstPass : List PassRecord)
    (laterPasses : List (List PassRecord)) : OutReport :=
  let st := firstPass.foldl (firstStep adjustable) ([], [])
  let lp := laterPasses.foldl laterStep (st.2, false)
  (st.1 ++ (if lp.2 then [allowanceItem] else []), lp.1.map (·.2))
-- pure-end

-- pre-conditions-start
/-- Admissibility: at least one further pass is run. Whether the extra terminal
item belongs in the report is decided from what the last further pass did, so an
invocation allowed no further pass at all has nothing to decide it from and no
report this claim describes. Every allowance of one or more passes is
admissible, including one whose passes report nothing at all. -/
def problem_pre_postProcess (laterPasses : List (List PassRecord)) : Prop :=
  laterPasses ≠ []
-- pre-conditions-end

-- post-conditions-start
/-- The report is exactly the one `postProcessModel` describes: every source file
is handed over at most once, each adjustable file carries the stored name it ends
with, the terminal item is present exactly when the run was still moving as the
allowance ran out — and each item falls on the side of the commit of the shared
mapping that `postProcessModel` puts it on, so what a caller that abandons the
report at the first signalled error has already been handed, and what the store
holds at that moment, are both pinned. -/
def problem_spec_postProcess (adjustable : List String) (firstPass : List PassRecord)
    (laterPasses : List (List PassRecord)) (result : OutReport) : Prop :=
  result = postProcessModel adjustable firstPass laterPasses
-- post-conditions-end

-- impl-start
def implementation_postProcess (adjustable : List String) (firstPass : List PassRecord)
    (laterPasses : List (List PassRecord)) : OutReport := Id.run do
  -- pre-patch orchestration: every record from every pass is handed to the
  -- caller as it is produced, with no order-preserving collection and nothing
  -- held back for after the mapping is committed — so a file processed in more
  -- than one pass is handed over more than once.
  let mut early : List OutItem := []
  let mut unsettled : Bool := false
  for r in firstPass do
    early := early ++ [r.toItem]
  for pass in laterPasses do
    unsettled := pass.any (fun r => r.rewrote)
    for r in pass do
      early := early ++ [r.toItem]
  return (early ++ (if unsettled then [allowanceItem] else []), [])
-- impl-end

-- proof-start
theorem correct_postProcess :
    ∀ (adjustable : List String) (firstPass : List PassRecord)
      (laterPasses : List (List PassRecord)),
      problem_pre_postProcess laterPasses →
      problem_spec_postProcess adjustable firstPass laterPasses
        (implementation_postProcess adjustable firstPass laterPasses) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl (G-DIFF)
-- proof-end
