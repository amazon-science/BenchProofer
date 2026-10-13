import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The routine that produces a module for a path that has
-- not been seen before is an UNCHANGED callee whose result the cache decision
-- never inspects; it is taken as a free input `freshMod`, so the spec makes no
-- behavioural claim about it and holds for every value (an R refinement —
-- mapping.md §3, refinement.md §C). The two ways a path may be turned into a
-- cache key are modeled DEEPLY by `Key`/`KeyRepr` below (a deep-model reference,
-- validated against the real path objects by axiom_check.py / G-AX), NOT behind
-- a consumed axiom.
-- axioms-end

-- pure-start
/- A module identity. Only equality is ever observed (whether two lookups return
   the same loaded module), so a bare identifier suffices. -/
abbrev Module := Nat

/- The two ways the same filesystem location can be turned into a key object for
   the module cache. Both denote the same location, yet as cache keys they are
   NOT interchangeable: a cache keyed under one representation does not answer a
   lookup made under the other. `primary` is the representation every consumer
   computes when it probes the cache; `secondary` is an alternative key object
   for the same location. (On the real system the two key objects compare equal
   as strings but hash differently, so they are distinct dictionary keys — the
   distinction `axiom_check.py`/G-AX validates against the real path objects.) -/
inductive KeyRepr where
  | primary
  | secondary
deriving DecidableEq, Inhabited, Repr

/- A cache key: the filesystem location it denotes together with which key
   representation produced it. Two keys answer the same lookup iff BOTH the
   location and the representation match (structural equality = dictionary-key
   identity, mapping.md §2). -/
structure Key where
  loc : Nat
  rep : KeyRepr
deriving DecidableEq, Inhabited, Repr

/- The key every consumer uses to probe the cache for a location: the `primary`
   representation. The cache is correct exactly when an entry registered for a
   location can be found again under this key. -/
def probeKey (loc : Nat) : Key := ⟨loc, KeyRepr.primary⟩

/- Look a key up in the cache (an association list of key→module). Front-recursive
   so a single unfold is available; returns the module of the first matching
   entry, `none` if the key is absent. Matching is full structural key equality. -/
def regLookup : List (Key × Module) → Key → Option Module
  | [],            _ => none
  | (k, m) :: rest, q => if k = q then some m else regLookup rest q

@[grind, simp] lemma regLookup_nil (q : Key) : regLookup [] q = none := rfl
@[grind, simp] lemma regLookup_cons (k : Key) (m : Module)
    (rest : List (Key × Module)) (q : Key) :
    regLookup ((k, m) :: rest) q = if k = q then some m else regLookup rest q := rfl

/- Appending a fresh entry for a key not yet present makes that key resolve to
   the appended module. The single fact the registration branch needs. -/
/- A present cache entry equals `some` of the value read out of it: the
   cache-hit branch returns exactly the module already stored. -/
@[grind] lemma some_getD_of_isSome {α : Type} (o : Option α) (d : α)
    (h : o.isSome = true) : o = some (o.getD d) := by
  cases o with
  | none => simp at h
  | some v => rfl

@[grind] lemma regLookup_append_fresh (reg : List (Key × Module)) (k : Key) (m : Module)
    (h : regLookup reg k = none) :
    regLookup (reg ++ [(k, m)]) k = some m := by
  induction reg with
  | nil => simp
  | cons hd tl ih =>
    obtain ⟨k', m'⟩ := hd
    rw [List.cons_append, regLookup_cons]
    rw [regLookup_cons] at h
    by_cases hk : k' = k
    · rw [if_pos hk] at h; exact absurd h (by simp)
    · rw [if_neg hk] at h; rw [if_neg hk]; exact ih h
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Obtain the module associated with a filesystem location through a shared
   module cache, importing it only once.

   The cache (`registry`) maps a path-derived key to the loaded module. A
   consumer always probes the cache under the location's `primary` key
   (`probeKey loc`). The desired behaviour:

   * if the `primary` key for this location is already registered, return the
     module found there and leave the cache exactly as it was (the import is
     performed at most once per location);
   * otherwise register the freshly produced module under the location's
     `primary` key and return it.

   The post-state is pinned so that, in every case, a subsequent probe of the
   cache under `probeKey loc` finds the returned module — i.e. the entry MUST be
   stored under the same key representation that lookups use, never under a
   merely same-location alternative.

   `loc` and `freshMod` are read-only (not `mut`); `registry` is the only mutated
   state and its post-state is pinned exactly in each branch (directive 5). -/
method registerModule (mut registry : List (Key × Module)) (loc : Nat) (freshMod : Module)
    return (out : Module)
  ensures ∀ m, regLookup registryOld (probeKey loc) = some m →
            (out = m ∧ registry = registryOld)
  ensures regLookup registryOld (probeKey loc) = none →
            (out = freshMod ∧ registry = registryOld ++ [(probeKey loc, freshMod)])
  ensures regLookup registry (probeKey loc) = some out
  do
    -- impl-start
    let k : Key := probeKey loc
    let cached := regLookup registry k
    if cached.isSome then
      return cached.getD freshMod
    else
      registry := registry ++ [(k, freshMod)]
      return freshMod
    -- impl-end

prove_correct registerModule by
  loom_solve
  simp_all [probeKey, regLookup_append_fresh]
