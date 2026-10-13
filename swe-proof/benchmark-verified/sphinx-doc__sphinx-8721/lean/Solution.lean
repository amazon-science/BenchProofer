import Mathlib
-- imports-end

/-!
Deciding whether a documentation post-processing step publishes the
highlighted-source companion pages prepared for a documentation build.

The step is handed:

  * a flag saying whether any source-module data was collected during the build
    (when none was collected there is nothing to publish);
  * the name of the active output format (builder), e.g. the multi-file web
    format or a member of the e-book format family;
  * a flag saying whether companion source pages are wanted for the e-book
    format family;
  * `generatedPages`, the companion page sequence the active output format
    publishes for this build when the e-book preference does not withhold it.

The desired behavior pins exactly when that sequence is published and when
nothing is published:

  * if no source-module data was collected, publish nothing;
  * if the active format belongs to the e-book family and companion source pages
    are not wanted for that family, publish nothing;
  * otherwise publish the given sequence in full.

`generatedPages` enters as an arbitrary given list: the behavior pinned below is
solely WHICH of the two outcomes — the given sequence, or nothing — is produced
for each combination of the three flags.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The work that prepares
-- the companion source pages for the active output format is modeled as an
-- arbitrary given list `generatedPages : List String`, because the modeled
-- behavior decides only WHETHER that whole sequence is published or suppressed,
-- never what it contains. Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the published sequence is either
-- the full given page list or the empty list, selected by the input flags.
-- pure-end

-- post-conditions-start
/-- The published page sequence is fully pinned to the inputs:

  * it is empty when no source-module data was collected;
  * otherwise empty when the active format is in the e-book family and companion
    source pages are not wanted for that family;
  * otherwise exactly the full given page sequence.

No output component is left free: for every combination of the inputs the result
is determined to be either the empty list or the complete given list. -/
def problem_spec_collectModulePages
    (hasModules : Bool) (builderName : String) (enableEpub : Bool)
    (generatedPages : List String) (result : List String) : Prop :=
  result =
    (if !hasModules then []
     else if builderName.startsWith "epub" && !enableEpub then []
     else generatedPages)
-- post-conditions-end

-- impl-start
def implementation_collectModulePages
    (hasModules : Bool) (builderName : String) (enableEpub : Bool)
    (generatedPages : List String) : List String := Id.run do
  -- No collected source-module data: publish nothing.
  if !hasModules then return []
  -- The e-book family publishes companion pages only when they are wanted there.
  if builderName.startsWith "epub" && !enableEpub then return []
  -- Otherwise publish the full given page sequence.
  return generatedPages
-- impl-end

-- proof-start
theorem correct_collectModulePages :
    ∀ (hasModules : Bool) (builderName : String) (enableEpub : Bool)
      (generatedPages : List String),
      problem_spec_collectModulePages hasModules builderName enableEpub generatedPages
        (implementation_collectModulePages hasModules builderName enableEpub generatedPages) := by
  intro hasModules builderName enableEpub generatedPages
  unfold problem_spec_collectModulePages implementation_collectModulePages
  simp only [Id.run, bind, pure]
-- proof-end
