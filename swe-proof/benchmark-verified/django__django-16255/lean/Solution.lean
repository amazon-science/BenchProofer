import Mathlib
-- imports-end

/-!
Reporting the single "latest timestamp" of a collection of items.

The collection knows two configuration facts:

  * whether a timestamp source is defined at all, and
  * whether the timestamp is computed PER ITEM (a function applied to each item)
    rather than being one constant value for the whole collection.

When the timestamp is computed per item, the report is the greatest of the
per-item timestamps. The collection may be EMPTY, in which case there is no
greatest element and the report is "no latest timestamp". When the timestamp is a
single constant value, the report is exactly that value (which may itself be absent).
When no timestamp source is defined, the report is "no latest timestamp".

The report is TOTAL: it always produces an answer, for every configuration —
including a per-item timestamp over an empty collection. Its value is an optional
timestamp: present (a timestamp) or absent ("no latest timestamp").
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The report is a pure
-- decision over the two configuration booleans, the list of per-item timestamps,
-- and the single constant timestamp. Producing the per-item timestamp list (applying
-- the per-item function across the collection) is abstracted to its result — the
-- list of timestamps — supplied as an input carrier. A timestamp is modeled as a
-- comparable ordinal (the only operation performed on it is the order comparison
-- that selects the greatest), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no extra pure helpers needed: the greatest-of-a-list operation is `List.max?`,
-- which is `none` for the empty list and `some` of the maximum otherwise.)
-- pure-end

-- post-conditions-start
/-- The report is TOTAL and fully pinned to the inputs.

  * `result = some v` always (the report never fails to produce an answer — in
    particular it is defined when the per-item timestamps are taken over an empty
    collection); there is no failing outcome.
  * the reported optional timestamp `v` is:
      - "no latest timestamp" (`none`) when no timestamp source is defined;
      - the greatest of the per-item timestamps (`vals.max?` — `none` exactly when
        the collection is empty) when the timestamp is computed per item;
      - the single constant timestamp otherwise.

No output component is left free: the outcome is `some` of the exact case split
over the inputs. -/
def problem_spec_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int)
    (result : Option (Option Int)) : Prop :=
  result =
    some (if hasM = false then none
          else if callM then vals.max?
          else constM)
-- post-conditions-end

-- impl-start
def implementation_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int) :
    Option (Option Int) := Id.run do
  if hasM = false then
    return some none
  if callM then
    -- greatest of the per-item timestamps; an empty collection has no greatest
    -- element, so the report is "no latest timestamp".
    return some vals.max?
  else
    return some constM
-- impl-end

-- proof-start
theorem correct_latestLastmod :
    ∀ (hasM callM : Bool) (vals : List Int) (constM : Option Int),
      problem_spec_latestLastmod hasM callM vals constM
        (implementation_latestLastmod hasM callM vals constM) := by
  intro hasM callM vals constM
  unfold problem_spec_latestLastmod implementation_latestLastmod
  cases hasM <;> cases callM <;> rfl
-- proof-end
