import Mathlib
-- imports-end

/-!
Assigning a primary-key value to an object that participates in a chain of
inheritance.

An object built by inheritance keeps, alongside its own primary-key attribute, a
distinct key attribute for each ancestor it descends from; those ancestor-key
attributes are what tie the object to its inherited parts. When a single
primary-key value is assigned to such an object, the assignment must reach ALL of
those keys at once — both the object's own primary-key attribute and every
ancestor-key attribute that links it to an inherited part — so that the object is
consistently re-keyed (in particular, clearing the primary key clears the whole
key chain). An ancestor link is excluded only when it is absent, or when it
already coincides with the object's own primary-key attribute (so it is covered
by that assignment). Every attribute that is not part of this key chain keeps its
previous value.

The object's attributes are modeled as a total map from attribute name to its
value (absent ⇒ `none`). `store` is the object before the assignment,
`primaryKeyName` its own primary-key attribute name, `ancestorLinks` the list of
ancestor links (each carrying whether it is present, whether it coincides with
the own primary key, and the ancestor-key attribute name it writes to), and
`value` the assigned value. The result is the object after the assignment.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom and none is deep-modeled as
-- an A-reference: the assignment is a concrete sequence of attribute-store
-- updates over metadata that is supplied as INPUT (the ancestor-link list, the
-- own primary-key attribute name, each link's target attribute name). The
-- attribute reads/writes are modeled directly as the `store` map. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- One ancestor link of an inherited object.
  * `linked` — the link is present (a real link field, not absent);
  * `sameAsPrimaryKey` — the link coincides with the object's own primary-key
    attribute (and so is already handled by the own-key assignment);
  * `keyName` — the ancestor-key attribute name this link writes to. -/
structure AncestorLink where
  linked : Bool
  sameAsPrimaryKey : Bool
  keyName : String
deriving DecidableEq, Repr

/-- Update one attribute of the store to `v`, leaving all others unchanged. -/
def setAttr (s : String → Option Int) (k : String) (v : Option Int) :
    String → Option Int :=
  fun n => if n = k then v else s n

/-- Apply the assignment to every qualifying ancestor-key attribute, front to
back: a link writes its ancestor key iff it is present and does not already
coincide with the own primary key; otherwise it is skipped. Front-recursive so it
pairs with the accumulator loop in the implementation. -/
def applyLinks (s : String → Option Int) (links : List AncestorLink)
    (v : Option Int) : String → Option Int :=
  match links with
  | [] => s
  | link :: rest =>
    let s' := if link.linked && !link.sameAsPrimaryKey then setAttr s link.keyName v else s
    applyLinks s' rest v
-- pure-end

-- post-conditions-start
/-- The resulting object is exactly: the input object with every qualifying
ancestor-key attribute set to the assigned value, and then the object's own
primary-key attribute set to the assigned value. The own-key assignment is last,
mirroring that it always takes effect. Every attribute outside this key chain is
pinned to its input value (no result component is left free). -/
def problem_spec_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int)
    (result : String → Option Int) : Prop :=
  result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value
-- post-conditions-end

-- impl-start
def implementation_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int) :
    String → Option Int := Id.run do
  -- Pre-patch (buggy): only the object's OWN primary-key attribute is assigned;
  -- the ancestor-key attributes are never reached, so an inherited object is
  -- left half-keyed (clearing the pk does not clear its ancestor keys).
  let mut s := store
  s := setAttr s primaryKeyName value
  return s
-- impl-end

-- proof-start
theorem correct_setPrimaryKey :
    ∀ (store : String → Option Int) (primaryKeyName : String)
      (ancestorLinks : List AncestorLink) (value : Option Int),
      problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
        (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
  intro store primaryKeyName ancestorLinks value
  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
  simp [Id.run]
  -- carries the gold proof shape; UNCLOSABLE against the buggy impl (G-DIFF):
  -- the buggy impl omits `applyLinks`, so the goal is unprovable whenever a
  -- qualifying ancestor link exists.
  rfl
-- proof-end
