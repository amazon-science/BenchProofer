import Velvet.Std
-- imports-end

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-inline admissibility test — whether a
--  constructed inline survives the access-control checks for this request and
--  object — is taken as a FREE INPUT `admissible`, so the spec makes no behavioural
--  claim about it and holds for every value. The object-construction of each
--  inline and the inherited access-control logic are UNCHANGED; nothing here
--  needs validation against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- An inline registration, identified by which inline class it names. Only its
   identity/order is observable to a consumer of the built instance list (the
   class each built instance is an instance of), so an opaque tagged id is the
   faithful carrier. -/
structure InlineClass where
  id : Nat
deriving DecidableEq, Inhabited

/- The admissible sublist of a sequence of inline registrations: keep, in order,
   exactly those for which the (unchanged) per-inline admissibility test holds.
   Written front-recursively so a single unfold is available per loop step (the
   backward fold pattern, plan §5.4). Empty sequence ⇒ empty result. -/
def kept (admissible : InlineClass → Bool) : List InlineClass → List InlineClass
  | []      => []
  | c :: cs => (if admissible c then [c] else []) ++ kept admissible cs

@[grind] lemma kept_nil (f : InlineClass → Bool) : kept f [] = [] := rfl
@[grind] lemma kept_cons (f : InlineClass → Bool) (c : InlineClass) (cs : List InlineClass) :
    kept f (c :: cs) = (if f c then [c] else []) ++ kept f cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The default selection hook: the per-request / per-object choice of which
   inline registrations apply. By default it yields exactly the statically
   declared set; a subclass may override it to choose a different selection
   based on the request or the edited object. `declared` is read-only
   (directive 5). -/
method getInlines (declared : List InlineClass) return (out : List InlineClass)
  ensures out = declared
  do
    -- impl-start
    return declared
    -- impl-end

prove_correct getInlines by
  loom_solve

/- Build the list of admissible inline instances for a request and object.

   The sequence iterated is the per-request / per-object *selection* of inline
   registrations (`selected` — the value yielded by the selection hook, which a
   subclass may have overridden), NOT the statically declared set (`declared`).
   Each selected registration is materialised and retained iff it passes the
   (unchanged) access-control admissibility test `admissible`; admissible ones are
   collected in their selection order.

   `selected`, `declared`, `admissible` are read-only (directive 5). -/
method getInlineInstances (selected : List InlineClass) (declared : List InlineClass) (admissible : InlineClass → Bool) return (result : List InlineClass)
  ensures result = kept admissible selected
  do
    -- impl-start
    let mut acc : List InlineClass := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant acc = kept admissible (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let c := selected[i - 1]!
      acc := (if admissible c then [c] else []) ++ acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `kept` peels one element. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma kept_drop_step (f : InlineClass → Bool) (xs : List InlineClass) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    kept f (xs.drop (i - 1)) = (if f xs[i - 1]! then [xs[i - 1]!] else []) ++ kept f (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, kept_cons]

prove_correct getInlineInstances by
  loom_solve
  rw [kept_drop_step admissible selected i (by omega) (by omega)]
  simp_all
