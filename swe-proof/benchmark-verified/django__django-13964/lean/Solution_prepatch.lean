import Mathlib
-- imports-end

/-!
Adopting a related object's primary key into a foreign-key field when a model is
saved.

A model instance can hold a foreign-key relation to another, not-yet-persisted
object. The foreign-key field stores a *key value* (the scalar that mirrors the
related object's primary key); separately, the related object carries its own
primary key.

When the owning model is saved and the related object already has a primary key,
the owning model must end up referencing that primary key. The subtlety is the
condition under which the stored key value is (re)adopted from the related
object: it must be adopted whenever the stored key value is still *empty* — both
the absent value and an empty scalar (such as the empty string) count as empty.
A non-empty stored key value is left untouched. This guarantees that a foreign
key to an object whose primary key is a non-numeric (e.g. string) value is
populated with that primary key rather than left holding an empty placeholder.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptiness
-- test on a stored foreign-key value and the adoption of the related object's
-- primary key are both modeled directly (an `Option String` carrier with an
-- explicit emptiness predicate), so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- A stored foreign-key value counts as *empty* when it is absent (`none`) or
is an empty scalar (the empty string). A present, non-empty value is not empty.
This mirrors the membership of a scalar key value in the set of empty values
recognised for a field (the absent value and the empty string being the cases a
foreign-key scalar can take). -/
def fkValueIsEmpty (v : Option String) : Bool :=
  match v with
  | none   => true
  | some s => s.isEmpty
-- pure-end

-- post-conditions-start
/-- After preparing a cached foreign-key relation for save, the stored key value
is the related object's primary key `objPk` when the stored value `fkValue` is
empty, and is `fkValue` itself otherwise.

Directive 5 (frame): the result is pinned entirely to the two inputs — the
stored value `fkValue` and the related object's primary key `objPk`; nothing is
left unconstrained.

The binder precondition (in `correct_*`) is that the related object already has
a primary key, modeled by `objPk : String` always being a present value (the
prepare step only reaches this adoption decision once the related object's
primary key is known to be present). -/
def problem_spec_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) (result : Option String) : Prop :=
  result = (if fkValueIsEmpty fkValue then some objPk else fkValue)
-- post-conditions-end

-- impl-start
def implementation_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) : Option String := Id.run do
  -- start from the foreign-key field's currently stored key value
  let mut result := fkValue
  -- when that stored value is absent, adopt the related object's primary key
  if result.isNone then
    result := some objPk
  return result
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against
-- this impl it cannot close: the spec adopts `objPk` whenever the stored value
-- is empty (absent OR the empty string), but this impl only adopts it when the
-- stored value is absent (`none`). On `fkValue = some ""` the spec requires the
-- result to be `some objPk` while the impl returns `some ""`, so the goal
-- reduces to the unprovable `some "" = some objPk`.
theorem correct_foreignKeyValueOnSave :
    ∀ (fkValue : Option String) (objPk : String),
      problem_spec_foreignKeyValueOnSave fkValue objPk
        (implementation_foreignKeyValueOnSave fkValue objPk) := by
  intro fkValue objPk
  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
  simp only [Id.run, bind, pure]
-- proof-end
