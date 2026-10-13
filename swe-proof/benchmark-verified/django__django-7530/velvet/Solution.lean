import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The behaviour under specification — which (application
--  label, model) pairs are enumerated for the registry consistency scan — is
--  modeled DEEPLY over the application registry given as input: the per-label
--  pair expansion is spelled out directly in the `pure` region and built by the
--  loop. The proof consumes no callee contract. The fidelity of the registry
--  carrier to the live application registry is a type refinement, audited
--  mechanically by conformance_check.py / G-CONF — see mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- An entry of the application registry: an application's label paired with the
   list of models that application itself owns. (Labels and models are carried
   as opaque `Nat` identifiers; the proof needs no operation on them — see
   mapping.md for the identifier bijection.) -/
abbrev AppEntry := Nat × List Nat

/- The (label, model) pairs contributed by a single application: its own label
   paired with each of its own models, one pair per owned model. -/
def appPairs (a : AppEntry) : List (Nat × Nat) :=
  a.2.map (fun m => (a.1, m))

/- The full enumeration over the registry: concatenate, in registry order, the
   pairs contributed by each application. Front-recursive so a single unfold is
   available per loop step (the fold pattern). Each pair's model is therefore
   one of THAT application's own models — never a model belonging only to some
   other application in the registry. -/
def allPairs : List AppEntry → List (Nat × Nat)
  | []      => []
  | a :: rest => appPairs a ++ allPairs rest

@[grind] lemma allPairs_nil : allPairs [] = [] := rfl
@[grind] lemma allPairs_cons (a : AppEntry) (rest : List AppEntry) :
    allPairs (a :: rest) = appPairs a ++ allPairs rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The (application label, model) pairs the registry consistency scan validates,
   modeled over the application registry `apps` (each entry an application label
   together with the models that application owns). The result is the in-order
   concatenation, across every application, of that application's own (label,
   model) pairs: for every application the enumerated models range over exactly
   that application's own models.

   `apps` is read-only and the operation mutates none of its inputs
   (directive 5). -/
method appModelPairs (apps : List AppEntry) return (out : List (Nat × Nat))
  ensures out = allPairs apps
  do
    -- impl-start
    let mut result : List (Nat × Nat) := []
    let mut i := apps.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ apps.length
      invariant result = allPairs (apps.drop i)
      done_with i = 0
      decreasing i
    do
      let a := apps[i - 1]!
      result := appPairs a ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allPairs` peels one application's `appPairs`. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma allPairs_drop_step (apps : List AppEntry) (i : Nat)
    (hi : 0 < i) (hle : i ≤ apps.length) :
    allPairs (apps.drop (i - 1)) = appPairs apps[i - 1]! ++ allPairs (apps.drop i) := by
  have hlt : i - 1 < apps.length := by omega
  have hcons : apps.drop (i - 1) = apps[i - 1]! :: apps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allPairs_cons]

prove_correct appModelPairs by
  loom_solve
  rw [allPairs_drop_step apps i (by omega) (by omega)]
  simp_all
