import Mathlib
-- imports-end

-- axioms-start
/- No unchanged callee needs an opaque signature here: every operation the modeled
behaviors invoke (a keyed registry insert/replace, and releasing a resource) is a
pure value-level transformation, modeled directly in the `pure` region and used
identically on both sides of each refinement. The proof agent therefore consumes
no `_prop` axiom. -/
-- axioms-end

-- pure-start
/-- A managed resource held in a registry. `name` is the key under which the
registry tracks it; `isOpen` records whether the resource is currently live
(`true`) or has been released (`false`). -/
structure Resource where
  name : String
  isOpen : Bool
deriving DecidableEq, Repr

/-- Look the resource up by its key, returning the first entry with that name. -/
def lookupRes (reg : List Resource) (key : String) : Option Resource :=
  reg.find? (fun r => r.name == key)

/-- Insert `r` into the registry under its key: if an entry with the same key
already exists, replace it in place (keeping position); otherwise append it. -/
def setRes (reg : List Resource) (r : Resource) : List Resource :=
  if reg.any (fun d => d.name == r.name) then
    reg.map (fun d => if d.name == r.name then r else d)
  else
    reg ++ [r]

/-- Release a single resource: mark it closed, leaving its key unchanged. -/
def releaseRes (r : Resource) : Resource := { r with isOpen := false }
-- pure-end

-- post-conditions-start
/-- Binding a provided collection into the registry. The result is a registry with
no duplicate keys whose lookup is fully determined: every key the provided
collection mentions resolves to the provided value for that key, and every other
key keeps whatever the registry held before. -/
def problem_spec_bindResources
    (reg provided : List Resource) (result : List Resource) : Prop :=
  result.Pairwise (fun a b => a.name ≠ b.name) ∧
  (∀ key, lookupRes result key =
    match lookupRes provided key with
    | some r => some r
    | none   => lookupRes reg key)
-- post-conditions-end

-- impl-start
def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
  let mut r := reg
  for c in provided do
    r := setRes r c
  return r
-- impl-end

-- proof-start
theorem correct_bindResources :
    ∀ (reg provided : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided
        (implementation_bindResources reg provided) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the buggy release impl (G-DIFF)
-- proof-end

-- post-conditions-start
/-- Releasing the whole registry. The set of keys is preserved exactly (same keys,
same order, none added or dropped), and every resulting resource is closed. -/
def problem_spec_releaseResources
    (reg : List Resource) (result : List Resource) : Prop :=
  result.map (·.name) = reg.map (·.name) ∧
  (∀ r ∈ result, r.isOpen = false)
-- post-conditions-end

-- impl-start
def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
  -- Pre-patch: there is no post-request hook to release the registry's resources,
  -- so each resource is left exactly as found — still open. (This is the actual
  -- bug: live resources accumulate instead of being released.)
  let mut out := []
  for c in reg do
    out := out ++ [c]
  return out
-- impl-end

-- proof-start
theorem correct_releaseResources :
    ∀ (reg : List Resource),
      problem_spec_releaseResources reg (implementation_releaseResources reg) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the buggy release impl (G-DIFF)
-- proof-end
