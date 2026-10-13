import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-component configuration action that is
--  dispatched to each selected component is unchanged by this change and is
--  applied identically to every selected component, so it factors out of the
--  model: the operation is reduced to *which* components are selected to
--  receive it, and that selection is modeled DEEPLY in the `pure` region below.
--  There is no `axiom` declaration and no A-reference deep model of an outside
--  callee.)
-- axioms-end

-- pure-start
/- A sub-component of the composite is either a placeholder marker that is meant
   to be left untouched, or a real component carrying a numeric identity. The
   only distinction the selection reacts to is marker-vs-real. -/
inductive Component where
  | marker
  | real (id : Nat)
  deriving Inhabited, DecidableEq

/- A real component takes part in the configuration broadcast; a placeholder
   marker does not. -/
def isReal : Component → Bool
  | .marker  => false
  | .real _  => true

/- The selection over a list of listed sub-components: keep the real ones, in
   order, dropping the placeholder markers. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def selectReal : List Component → List Component
  | []      => []
  | c :: cs => (if isReal c then [c] else []) ++ selectReal cs

@[grind] lemma selectReal_nil : selectReal [] = [] := rfl
@[grind] lemma selectReal_cons (c : Component) (cs : List Component) :
    selectReal (c :: cs) = (if isReal c then [c] else []) ++ selectReal cs := rfl

/- The complete broadcast target list: the real listed sub-components, in order,
   followed by the designated extra component when it too is real (and never
   when it is a placeholder marker). -/
def broadcastTargets (listed : List Component) (extra : Component) : List Component :=
  selectReal listed ++ (if isReal extra then [extra] else [])
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the ordered list of sub-components that the configuration is
   broadcast to. `listed` and `extra` are read-only inputs (not `mut`); the
   query reads the membership of each and mutates nothing (directive 5). -/
method collectBroadcastTargets (listed : List Component) (extra : Component)
    return (out : List Component)
  ensures out = broadcastTargets listed extra
  ensures isReal extra = true → out = selectReal listed ++ [extra]
  ensures isReal extra = false → out = selectReal listed
  do
    -- impl-start
    -- Walk the listed sub-components, keeping the real ones (placeholder markers
    -- are skipped). Then, after the listed components, also include the
    -- designated extra component when it is a real component — the placeholder
    -- markers are the only values excluded there too.
    let mut result : List Component := []
    let mut i := listed.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ listed.length
      invariant result = selectReal (listed.drop i)
      done_with i = 0
      decreasing i
    do
      let c := listed[i - 1]!
      result := (if isReal c then [c] else []) ++ result
      i := i - 1
    -- Pre-patch skeleton: the designated extra component is NEVER added to the
    -- broadcast target list — only the listed sub-components are walked. The
    -- frozen spec requires broadcastTargets (which appends the extra component
    -- when it is real), so prove_correct MUST fail.
    result := result
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectReal` peels one selection step. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma selectReal_drop_step (listed : List Component) (i : Nat)
    (hi : 0 < i) (hle : i ≤ listed.length) :
    selectReal (listed.drop (i - 1))
      = (if isReal listed[i - 1]! then [listed[i - 1]!] else []) ++ selectReal (listed.drop i) := by
  have hlt : i - 1 < listed.length := by omega
  have hcons : listed.drop (i - 1) = listed[i - 1]! :: listed.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectReal_cons]

prove_correct collectBroadcastTargets by
  loom_solve
  all_goals simp_all [broadcastTargets]
  all_goals (rw [selectReal_drop_step listed i (by omega) (by omega)]; simp_all)
