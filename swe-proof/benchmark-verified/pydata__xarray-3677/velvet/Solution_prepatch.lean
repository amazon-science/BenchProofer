import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the core
   combine operation `combineCore`, which fuses two key→value collections — is
   modeled DEEPLY in the `pure` region and validated == the real callee by G-AX
   (an A-reference, mapping.md §3), so it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A key→value collection: a mapping from key identities (modeled as `Nat` tags;
   only key equality/membership is observed) to values (modeled as `Int`; only
   value identity is observed). -/
abbrev KeyedMap := List (Nat × Int)

/- A combine operand, in its two mutually-exclusive shapes:
   `keyed es` — a genuine key→value collection that exposes its entries as
   key/value pairs; `single k v` — a lone keyed value that is NOT itself a
   key→value collection (it does not expose key/value pairs). -/
inductive Operand where
  | keyed  (entries : KeyedMap)
  | single (key : Nat) (value : Int)
  deriving DecidableEq

/- Failure of the core combine operation: it is undefined on an operand that
   does not expose key/value pairs (there is nothing to iterate). -/
inductive CombineErr where
  | notKeyed
  deriving DecidableEq

/- The fused entries of two collections: their union, base first. -/
def combineEntries (a b : KeyedMap) : KeyedMap := a ++ b

/- The core combine callee (unchanged by this change; A-reference, deep model of
   the real fuse-the-collections operation — mapping.md §3.1). It consumes the
   operand's key/value pairs and fuses them with the base. A `keyed` operand
   exposes its pairs, so the fuse succeeds; a `single` operand exposes no
   key/value pairs, so the operation is undefined on it and fails. -/
def combineCore (base : KeyedMap) : Operand → Except CombineErr KeyedMap
  | .keyed es    => Except.ok (combineEntries base es)
  | .single _ _  => Except.error .notKeyed

/- Re-express a lone keyed value as a one-entry key→value collection. -/
def asKeyed (k : Nat) (v : Int) : KeyedMap := [(k, v)]

/- Normalize an operand into a key→value collection: a lone keyed value is
   re-expressed as a one-entry collection so it exposes key/value pairs; an
   operand that is already a collection is left as is. -/
def coerceOperand : Operand → Operand
  | .single k v  => Operand.keyed (asKeyed k v)
  | .keyed es    => Operand.keyed es

/- The intended result: normalize the operand to a key→value collection, then
   hand it to the core combine. Because every normalized operand exposes
   key/value pairs, the combine always succeeds. -/
def combineSpec (base : KeyedMap) (other : Operand) : Except CombineErr KeyedMap :=
  combineCore base (coerceOperand other)

@[grind] lemma coerceOperand_single (k : Nat) (v : Int) :
    coerceOperand (.single k v) = Operand.keyed (asKeyed k v) := rfl
@[grind] lemma coerceOperand_keyed (es : KeyedMap) :
    coerceOperand (.keyed es) = Operand.keyed es := rfl
@[grind] lemma combineCore_keyed (base es : KeyedMap) :
    combineCore base (.keyed es) = Except.ok (combineEntries base es) := rfl
@[grind] lemma combineCore_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineCore base (.single k v) = Except.error .notKeyed := rfl
@[grind] lemma combineSpec_single (base : KeyedMap) (k : Nat) (v : Int) :
    combineSpec base (.single k v)
      = Except.ok (combineEntries base (asKeyed k v)) := rfl
@[grind] lemma combineSpec_keyed (base es : KeyedMap) :
    combineSpec base (.keyed es) = Except.ok (combineEntries base es) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method combineKeyed (base : KeyedMap) (other : Operand)
    return (out : Except CombineErr KeyedMap)
  ensures out = combineSpec base other
  do
    -- impl-start
    -- Pre-image skeleton: the operand is handed straight to the core combine
    -- WITHOUT first re-expressing a lone keyed value as a collection. A `single`
    -- operand exposes no key/value pairs, so the core combine is undefined on it
    -- and fails — the reported crash. The frozen spec re-expresses it and
    -- succeeds, so prove_correct MUST fail on the `single` case.
    let out := combineCore base other
    return out
    -- impl-end

prove_correct combineKeyed by
  loom_solve
