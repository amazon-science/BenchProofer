import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The only callee is the built-in value-hashing
--  primitive that turns a hashable key into an integer digest; it is UNCHANGED
--  by the modeled behaviour and the spec makes no claim about which integers it
--  returns, so it is taken as a FREE INPUT `pyHash : HashKey → Int` that holds
--  for EVERY hashing function. There is nothing to validate against a real
--  callee, hence no consumed axiom and no A-reference — G-AX is `skip`. The
--  behaviour under spec is purely WHICH key is handed to that primitive, which
--  is modeled deeply below and differential-tested by G-CONF. See refinement.md
--  / mapping.md.)
-- axioms-end

-- pure-start
/- The key a field is hashed by. A field carries an assignment-independent
   intrinsic identity set once when the field object is created. It may also,
   at some later point in its lifetime, become associated with an owning record
   class, gaining association metadata (a pair of name components); before that
   it has none. The two possible shapes of a hash key:
     * `solo id`        — keyed by the intrinsic identity alone;
     * `composite id a` — keyed by the intrinsic identity together with the
                          (optional) association metadata. -/
inductive HashKey where
  | solo (id : Int)
  | composite (id : Int) (assoc : Option (List Char × List Char))
deriving DecidableEq, Inhabited

/- The hash key of a field is built from its intrinsic identity ALONE; any
   association metadata it may have acquired is deliberately excluded. Because
   the key is a function of the intrinsic identity only — and that identity never
   changes after the field is created — the key, and therefore the field's hash,
   is stable across the field's whole lifetime (it does not change when the field
   later becomes associated with a record class). This is exactly the desired
   immutability of the hash. -/
def fieldHashKey (intrinsicId : Int) : HashKey := .solo intrinsicId

/- The hash key of a field at a given point in its lifetime, where `assoc` is the
   association metadata it carries at that point (`none` while standalone, `some
   (app, name)` once associated). Modeled as a function of the lifecycle state so
   that immutability can be stated as a theorem about it. -/
def fieldKeyAt (intrinsicId : Int)
    (_assoc : Option (List Char × List Char)) : HashKey :=
  fieldHashKey intrinsicId

@[grind, simp] theorem fieldKeyAt_eq (intrinsicId : Int)
    (assoc : Option (List Char × List Char)) :
    fieldKeyAt intrinsicId assoc = fieldHashKey intrinsicId := rfl

/- Immutability: the key — hence the digest — is constant across the field's
   lifetime. For any hashing primitive `f`, the digest at lifecycle state `a`
   equals the digest at state `b`, because `fieldKeyAt` does not consult its
   association argument. This is precisely the guarantee the desired behaviour
   demands; an implementation whose key varied with `assoc` would refute it. -/
theorem fieldHash_immutable
    (f : HashKey → Int) (intrinsicId : Int)
    (a b : Option (List Char × List Char)) :
    f (fieldKeyAt intrinsicId a) = f (fieldKeyAt intrinsicId b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The digest used to place a field into hash-based containers.

   `pyHash` is the value-hashing primitive (a free input — the spec holds for
   every hashing function). `intrinsicId` is the field's assignment-independent
   intrinsic identity. `modelAssoc` is the association metadata the field carries
   at the moment of hashing — `none` when the field is standalone, or `some
   (app, name)` once it has been associated with a record class.

   Desired behaviour: the digest is computed from the intrinsic identity ALONE,
   so it is the same whether or not the field is currently associated. Hence
   `modelAssoc` is a read-only reference that the operation must NOT consult: it
   is NOT declared `mut`, and the postcondition pins `out` to a key that does not
   mention it (directive 5 — an unconstrained dependence on `modelAssoc` would be
   the analogue of letting a stale, association-dependent value leak into the
   digest). An implementation that folds `modelAssoc` into the key cannot satisfy
   the postcondition. -/
method fieldHashMethod (pyHash : HashKey → Int) (intrinsicId : Int)
    (modelAssoc : Option (List Char × List Char)) return (out : Int)
  ensures out = pyHash (fieldHashKey intrinsicId)
  ensures out = pyHash (fieldKeyAt intrinsicId modelAssoc)
  ensures ∀ a : Option (List Char × List Char),
            out = pyHash (fieldKeyAt intrinsicId a)
  do
    -- impl-start
    return pyHash (fieldHashKey intrinsicId)
    -- impl-end

prove_correct fieldHashMethod by
  loom_solve
