import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs a consumed axiom here. The introspection-attribute
   environment that the callable is presented with is decided entirely by values
   observable on its inputs: for each requested attribute name, whether the
   source object carries a value for that name, and if not, whether the base
   object does. That per-name overlay is modeled directly in the `pure` region
   below (`mergeAt` / `mergePlan`) and validated against the real standard-library
   attribute-copy helper by axiom_check.py (G-AX, an A-reference, not a consumed
   axiom). Cross-language soundness of the refinement is also checked mechanically
   by G-CONF (conformance_check.py). -/
-- axioms-end

-- pure-start
/- An attribute environment, modeled as an association list from attribute name
   to value. Lookup returns the value bound to the first matching name, or
   `none` when the environment carries no value for that name (the standard
   "attribute is absent" observation). -/
def lookupAttr : List (String × String) → String → Option String
  | [],            _ => none
  | (k, v) :: rest, n => if k = n then some v else lookupAttr rest n

/- The overlay of one environment over another for a single attribute name: take
   the source object's value when it carries one for this name, otherwise fall
   back to the base object's value. This is the per-name rule a standard-library
   attribute-copy helper applies — it assigns the source's value only for the
   names the source actually defines, leaving the base's value in place
   otherwise. -/
def firstDefined (a b : Option String) : Option String :=
  match a with
  | some v => some v
  | none   => b

/- The value the overlaid environment presents for a single attribute name:
   source value if present, else base value. -/
def mergeAt (src base : List (String × String)) (n : String) : Option String :=
  firstDefined (lookupAttr src n) (lookupAttr base n)

/- The overlaid environment across a whole list of requested attribute names:
   the per-name overlay value for each name. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def mergePlan (src base : List (String × String)) :
    List String → List (String × Option String)
  | []      => []
  | n :: ns => (n, mergeAt src base n) :: mergePlan src base ns

@[grind] lemma mergePlan_nil (src base : List (String × String)) :
    mergePlan src base [] = [] := rfl
@[grind] lemma mergePlan_cons (src base : List (String × String))
    (n : String) (ns : List String) :
    mergePlan src base (n :: ns)
      = (n, mergeAt src base n) :: mergePlan src base ns := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- `methodAttrs` (the source object's attributes) and `baseAttrs` (the bare
   callable's attributes) are read-only inputs; only the loop-local accumulator
   and index are `mut` (directive-5 frame discipline). -/
method buildPresentedAttrs
    (methodAttrs : List (String × String)) (baseAttrs : List (String × String))
    (names : List String)
    return (out : List (String × Option String))
  ensures out = mergePlan methodAttrs baseAttrs names
  do
    -- impl-start
    let mut result : List (String × Option String) := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = mergePlan methodAttrs baseAttrs (names.drop i)
      done_with i = 0
      decreasing i
    do
      let n := names[i - 1]!
      result := (n, mergeAt methodAttrs baseAttrs n) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the name at `i-1`
   on the front, so `mergePlan` peels one `mergeAt`. The single goal `loom_solve`
   leaves for the loop body. -/
lemma mergePlan_drop_step (src base : List (String × String))
    (names : List String) (i : Nat) (hi : 0 < i) (hle : i ≤ names.length) :
    mergePlan src base (names.drop (i - 1))
      = (names[i - 1]!, mergeAt src base names[i - 1]!)
        :: mergePlan src base (names.drop i) := by
  have hlt : i - 1 < names.length := by omega
  have hcons : names.drop (i - 1) = names[i - 1]! :: names.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, mergePlan_cons]

prove_correct buildPresentedAttrs by
  loom_solve
  rw [mergePlan_drop_step methodAttrs baseAttrs names i (by omega) (by omega)]
  simp_all
