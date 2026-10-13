import Mathlib
-- imports-end

/-!
Collapsing two consecutive option-configuration steps into a single combined
option set.

The first step establishes an initial set of named option settings (a mapping
from option keys to their values). A second, overriding step supplies its own
set of settings that should take effect in place of the first. The combined
result is obtained by overlaying the overriding step's settings on top of the
initial ones (the overriding value wins for any key both mention, and keys only
the overriding step mentions are added).

There is, however, a designated family of *managed* keys: keys whose value is
considered to be owned entirely by the overriding step. For a managed key, the
overriding step is authoritative — if it does NOT mention that key, the key must
be cleared from the combined result, even when the initial step had set it.
Keys outside the managed family are left untouched when the overriding step is
silent about them.

The behavior is stated abstractly as an input→output relation on the combined
option set; the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the combination is
-- spelled out concretely (an overlay of two key→value mappings followed by the
-- clearing of any managed key the overriding mapping is silent about).
-- axioms-end

-- pure-start
/-- Is key `k` present in the key→value mapping `d`? -/
def keyPresent {V : Type} (d : List (String × V)) (k : String) : Bool :=
  d.any (fun p => p.1 == k)

/-- Look up key `k` in `d`, returning the value of the first entry with that key
(`none` if absent). A mapping is read as a dictionary: first match wins. -/
def optLookup {V : Type} (d : List (String × V)) (k : String) : Option V :=
  (d.find? (fun p => p.1 == k)).map (·.2)

/-- Overlay `override` on top of `base`: keep every overriding entry, and keep
each base entry whose key the overriding mapping does not mention. -/
def mergeOpts {V : Type} (base override : List (String × V)) : List (String × V) :=
  override ++ base.filter (fun p => ! keyPresent override p.1)

/-- Remove every entry whose key equals `k`. -/
def dropKey {V : Type} (d : List (String × V)) (k : String) : List (String × V) :=
  d.filter (fun p => p.1 != k)

/-- The value the combined mapping should hold at key `k`:
* if the overriding mapping mentions `k`, its value wins;
* otherwise, if `k` is a managed key, it is cleared (`none`);
* otherwise the base value (if any) survives. -/
def expectedLookup {V : Type} (base override : List (String × V))
    (managedKeys : List String) (k : String) : Option V :=
  match optLookup override k with
  | some v => some v
  | none   => if managedKeys.contains k then none else optLookup base k
-- pure-end

-- post-conditions-start
/-- The combined mapping is a genuine dictionary (its keys are distinct) and
agrees, at every key, with the desired overlay-then-clear-managed behavior. The
key-distinctness conjunct rules out a result that merely shares the right
first-match lookups while hiding shadowed duplicate keys (a Python `dict` has no
duplicate keys); together the two clauses pin the resulting dictionary exactly. -/
def problem_spec_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String)
    (result : List (String × V)) : Prop :=
  (result.map Prod.fst).Nodup ∧
  (∀ k : String, optLookup result k = expectedLookup base override managedKeys k)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the combined mapping is the plain overlay of the
-- two settings, with NO clearing step for managed keys. A managed key that the
-- initial step set but the overriding step is silent about therefore survives,
-- when it should have been cleared.
def implementation_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String) :
    List (String × V) := Id.run do
  let options := mergeOpts base override
  return options
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (the
-- missing managed-key clearing contradicts the `expectedLookup … = none` clause
-- for a managed key the overriding mapping omits).
theorem correct_combineOptions :
    ∀ {V : Type} (base override : List (String × V)) (managedKeys : List String),
      (base.map Prod.fst).Nodup →
      (override.map Prod.fst).Nodup →
      problem_spec_combineOptions base override managedKeys
        (implementation_combineOptions base override managedKeys) := by
  sorry
-- proof-end
