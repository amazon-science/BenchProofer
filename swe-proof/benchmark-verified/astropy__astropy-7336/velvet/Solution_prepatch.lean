import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the unit
   re-expression operation `coerceUnit` — is modeled DEEPLY in the `pure` region
   and validated == the real callee by G-AX (an A-reference, mapping.md §3), so
   it carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The result produced by the underlying callable: either a quantity carrying a
   unit (its unit id), or the null value (a callable that produces no value).
   Only the unit of a quantity is observable to the callers here. -/
inductive RetVal where
  | null
  | quantity (unit : Nat)
  deriving DecidableEq

/- The declared result-unit annotation, in three mutually-exclusive shapes:
   `absent` (no annotation given), `nullAnnot` (the annotation is the null
   sentinel — a callable declared to yield no value), or `target u` (a genuine
   unit the result should be expressed in). -/
inductive Annot where
  | absent
  | nullAnnot
  | target (u : Nat)
  deriving DecidableEq

/- Failure of the unit re-expression operation. The operation is undefined on
   the null value (`noConvertOp` — there is no such operation to invoke on it),
   and it rejects a unit that the source cannot be re-expressed in
   (`notCompatible` — the source and target describe different kinds of
   measurement). -/
inductive ConvErr where
  | noConvertOp
  | notCompatible
  deriving DecidableEq

/- The kind of a unit (its measurement family). Two units can be re-expressed
   into one another exactly when they share a kind. Modeled as an opaque total
   tag over the unit ids; its value-by-value identity is pinned against the real
   units by G-AX (axiom_check.py), which is the only thing the model observes
   about it. -/
opaque unitKind : Nat → Nat

/- Two units admit re-expression exactly when they are of the same kind. -/
def compatible (s t : Nat) : Bool := unitKind s == unitKind t

/- The unit re-expression callee (unchanged by this change; A-reference, deep
   model of the real conversion operation — mapping.md §3.1). Re-expressing a
   quantity in a target unit succeeds — yielding a quantity carrying that target
   unit — exactly when the source and target are compatible; otherwise it is
   rejected. The operation does not exist on the null value, so invoking it
   there fails. The magnitude component is irrelevant to the observed behavior
   and is dropped. -/
def coerceUnit : RetVal → Nat → Except ConvErr RetVal
  | .quantity s, t => if compatible s t then Except.ok (.quantity t)
                      else Except.error .notCompatible
  | .null,       _ => Except.error .noConvertOp

/- The unit carried by a genuine unit annotation (0 elsewhere — never consulted
   off the `target` shape). -/
def annotTarget : Annot → Nat
  | .target u => u
  | _         => 0

/- The intended result of post-processing: a genuine unit target re-expresses
   the result in that unit; in every other case — no annotation, or the null
   annotation — the result is handed back unchanged, never re-expressed. -/
def processReturnSpec (annot : Annot) (ret : RetVal) : Except ConvErr RetVal :=
  match annot with
  | .absent    => Except.ok ret
  | .nullAnnot => Except.ok ret
  | .target u  => coerceUnit ret u

@[grind] lemma processReturnSpec_absent (ret : RetVal) :
    processReturnSpec .absent ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_nullAnnot (ret : RetVal) :
    processReturnSpec .nullAnnot ret = Except.ok ret := rfl
@[grind] lemma processReturnSpec_target (u : Nat) (ret : RetVal) :
    processReturnSpec (.target u) ret = coerceUnit ret u := rfl
@[grind] lemma annotTarget_target (u : Nat) : annotTarget (.target u) = u := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method processReturn (annot : Annot) (ret : RetVal) return (out : Except ConvErr RetVal)
  ensures out = processReturnSpec annot ret
  do
    -- impl-start
    -- Pre-image skeleton: the guard fires on EVERY non-absent annotation,
    -- including the null sentinel — so a null-annotated result is fed to the
    -- re-expression op, which is undefined on the null value. The frozen spec
    -- hands such results back unchanged, so prove_correct MUST fail.
    let annotated : Bool :=
      match annot with
      | .absent    => false
      | .nullAnnot => true
      | .target _  => true
    let target : Nat :=
      match annot with
      | .target u  => u
      | _          => 0
    let out := if annotated then coerceUnit ret target else Except.ok ret
    return out
    -- impl-end

prove_correct processReturn by
  loom_solve
