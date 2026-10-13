import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model reference to an unchanged callee.
--  The computation under specification — selecting which existing entries a
--  requested entry may share — is modeled DEEPLY below (`eligibleEntries` /
--  `entryEligible` ARE the selection). The only repository semantics it leans
--  on are the two entry-comparison relations, modeled directly as
--  `matchesStructural` / `matchesExact`; their fidelity to the real comparison
--  methods is checked executably by axiom_check.py (G-AX). See mapping.md §3.)
-- axioms-end

-- pure-start
/- A registry entry's observable identity, abstracted to exactly the two
   components the sharing decision inspects:
   * `structKey`  — the structural identity of the entry (everything that makes
                    two entries refer to "the same underlying thing").
   * `refineTag`  — an additional refinement tag that further distinguishes two
                    entries that are otherwise structurally identical. Two
                    entries can share a `structKey` yet carry different
                    `refineTag`s. Only equality of each component is ever
                    observed, so a numeric carrier is faithful (mapping.md §2). -/
structure EntryId where
  structKey : Nat
  refineTag : Nat
  deriving DecidableEq, Inhabited

/- Structural match: two entries agree on their structural identity, IGNORING
   the refinement tag. -/
def matchesStructural (a b : EntryId) : Bool := a.structKey == b.structKey

/- Exact match: two entries agree on BOTH their structural identity AND their
   refinement tag. This is strictly finer than `matchesStructural`: entries that
   differ only in their refinement tag match structurally but NOT exactly. -/
def matchesExact (a b : EntryId) : Bool :=
  a.structKey == b.structKey && a.refineTag == b.refineTag

/- Whether an id is permitted by the allowance. The allowance is either absent
   (`none` — every id permitted) or an explicit list of permitted ids. -/
def allowedMember (allowed : Option (List Nat)) (id : Nat) : Bool :=
  match allowed with
  | none   => false
  | some l => l.contains id

/- Restricted-selection mode is in force only when it is requested AND an
   explicit, non-empty allowance is supplied. An absent or empty allowance falls
   back to the default mode. -/
def restrictedMode (allowed : Option (List Nat)) (restricted : Bool) : Bool :=
  restricted && (match allowed with | none => false | some l => !l.isEmpty)

/- Whether one existing entry `(id, desc)` is eligible to be shared by the
   requested entry `req`, under the allowance and the mode flag.

   * Restricted mode: the entry must be explicitly permitted by the allowance
     AND match the request structurally (refinement tag ignored).
   * Default mode: the entry must be permitted (either the allowance is absent,
     so all are permitted, or it lists this id) AND match the request EXACTLY —
     structural identity AND refinement tag both. In particular, an existing
     entry that matches the request structurally but carries a DIFFERENT
     refinement tag is NOT eligible in default mode. -/
def entryEligible (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool)
    (e : Nat × EntryId) : Bool :=
  if restrictedMode allowed restricted then
    allowedMember allowed e.1 && matchesStructural e.2 req
  else
    (allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req

/- The selection: the ids of all eligible existing entries, in registry order.
   Front-recursive so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def eligibleEntries (req : EntryId) (allowed : Option (List Nat)) (restricted : Bool) :
    List (Nat × EntryId) → List Nat
  | []      => []
  | e :: es =>
      (if entryEligible req allowed restricted e then [e.1] else [])
        ++ eligibleEntries req allowed restricted es

@[grind] lemma eligibleEntries_nil (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) : eligibleEntries req allowed restricted [] = [] := rfl

@[grind] lemma eligibleEntries_cons (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (e : Nat × EntryId) (es : List (Nat × EntryId)) :
    eligibleEntries req allowed restricted (e :: es)
      = (if entryEligible req allowed restricted e then [e.1] else [])
          ++ eligibleEntries req allowed restricted es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute which existing registry entries a requested entry may share.

   `registry` is the ordered list of existing entries, each an `(id, desc)`
   pair. `req` is the requested entry's identity. `allowed` is the allowance
   (`none` = every entry permitted; `some l` = only the ids in `l`). `restricted`
   requests restricted-selection mode.

   The result is the ids of the eligible entries, in registry order, as defined
   by `eligibleEntries`. The behaviour that the selection must honour: in default
   mode an existing entry is eligible only when it matches the request EXACTLY,
   so two existing entries that are structurally identical but carry different
   refinement tags are kept distinct (the request shares only the one with the
   matching tag); in restricted mode the request shares an explicitly-permitted
   entry that matches structurally.

   All four inputs are read-only — none is `mut`; the routine reads them and
   builds a fresh list, mutating nothing it is handed (directive 5). -/
method computeEligible (registry : List (Nat × EntryId)) (req : EntryId)
    (allowed : Option (List Nat)) (restricted : Bool) return (out : List Nat)
  ensures out = eligibleEntries req allowed restricted registry
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i := registry.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ registry.length
      invariant result = eligibleEntries req allowed restricted (registry.drop i)
      done_with i = 0
      decreasing i
    do
      let e := registry[i - 1]!
      let keep := entryEligible req allowed restricted e
      result := (if keep then [e.1] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `eligibleEntries` peels one entry. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma eligibleEntries_drop_step (req : EntryId) (allowed : Option (List Nat))
    (restricted : Bool) (registry : List (Nat × EntryId)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ registry.length) :
    eligibleEntries req allowed restricted (registry.drop (i - 1))
      = (if entryEligible req allowed restricted registry[i - 1]! then [registry[i - 1]!.1] else [])
          ++ eligibleEntries req allowed restricted (registry.drop i) := by
  have hlt : i - 1 < registry.length := by omega
  have hcons : registry.drop (i - 1) = registry[i - 1]! :: registry.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, eligibleEntries_cons]

prove_correct computeEligible by
  loom_solve
  rw [eligibleEntries_drop_step req allowed restricted registry i (by omega) (by omega)]
  simp_all
