import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An unchanged path-normaliser applied to every retained entry: it turns a raw
   directory entry (a character sequence) into the canonical absolute path that
   gets watched. It is a free function (OPAQUE) because the operation refines the
   collection step around it, never changing the normaliser itself; nothing is
   asserted about its result, so there is nothing for G-AX to validate.
   Provenance: mapping.md §3. -/
opaque normalizePath : List Char → List Char

/- An unchanged predicate that recognises an entry already owned by the
   framework's own bundled-template area; such entries are excluded from the
   watch set. Also OPAQUE (a free boolean function of the entry): the operation
   keeps deferring to it unchanged, asserting nothing about its value.
   Provenance: mapping.md §3. -/
opaque isFrameworkOwned : List Char → Bool
-- axioms-end

-- pure-start
/- Whether a directly-configured directory entry is admissible: an entry is kept
   only when it is non-empty. An empty entry carries no usable location and must
   be dropped before normalisation, so that it can never be expanded into a
   spurious watched location. -/
def keepConfigured (entry : List Char) : Bool :=
  decide (entry ≠ [])

/- Whether a loader-supplied directory entry is admissible: it must be non-empty
   AND not already owned by the framework. Emptiness is checked first and on its
   own, independently of the ownership test. -/
def keepLoader (entry : List Char) : Bool :=
  decide (entry ≠ []) && (!isFrameworkOwned entry)

/- The watched locations contributed by a list of directly-configured entries:
   each admissible entry is normalised, in order; inadmissible entries
   contribute nothing. Front-recursive so a single unfold is available per loop
   step (the Velvet fold pattern). -/
def collectConfigured : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es

/- The watched locations contributed by a list of loader-supplied entries: same
   shape, with the loader admissibility test. -/
def collectLoader : List (List Char) → List (List Char)
  | []      => []
  | e :: es => (if keepLoader e then [normalizePath e] else []) ++ collectLoader es

@[grind] lemma collectConfigured_nil : collectConfigured [] = [] := rfl
@[grind] lemma collectConfigured_cons (e : List Char) (es : List (List Char)) :
    collectConfigured (e :: es) =
      (if keepConfigured e then [normalizePath e] else []) ++ collectConfigured es := rfl

@[grind] lemma collectLoader_nil : collectLoader [] = [] := rfl
@[grind] lemma collectLoader_cons (e : List Char) (es : List (List Char)) :
    collectLoader (e :: es) =
      (if keepLoader e then [normalizePath e] else []) ++ collectLoader es := rfl

/- An empty entry is never admissible at either site. These are the clauses the
   pre-image skeleton (which omits the emptiness test) cannot satisfy. -/
@[grind] lemma keepConfigured_empty : keepConfigured [] = false := by
  unfold keepConfigured; simp
@[grind] lemma keepLoader_empty : keepLoader [] = false := by
  unfold keepLoader; simp

/- Hence an empty entry contributes nothing to either collection, regardless of
   the surrounding entries. -/
@[grind] lemma collectConfigured_cons_empty (es : List (List Char)) :
    collectConfigured ([] :: es) = collectConfigured es := by
  rw [collectConfigured_cons, keepConfigured_empty]; simp

@[grind] lemma collectLoader_cons_empty (es : List (List Char)) :
    collectLoader ([] :: es) = collectLoader es := by
  rw [collectLoader_cons, keepLoader_empty]; simp

/- Nothing is invented: every collected location is the normalisation of some
   admissible entry of the input. Proven by induction; `@[grind]` so the
   corresponding postcondition discharges automatically. -/
@[grind] lemma collectConfigured_mem (es : List (List Char)) :
    ∀ p, p ∈ collectConfigured es →
      ∃ e, e ∈ es ∧ keepConfigured e = true ∧ p = normalizePath e := by
  induction es with
  | nil => intro p h; simp [collectConfigured] at h
  | cons e es ih =>
      intro p h
      rw [collectConfigured_cons] at h
      by_cases hk : keepConfigured e = true
      · rw [if_pos hk] at h
        rw [List.singleton_append, List.mem_cons] at h
        rcases h with hpe | htail
        · exact ⟨e, List.mem_cons_self, hk, hpe⟩
        · obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p htail
          exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
      · rw [if_neg hk, List.nil_append] at h
        obtain ⟨e', hmem, hkeep, hpe'⟩ := ih p h
        exact ⟨e', List.mem_cons_of_mem _ hmem, hkeep, hpe'⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from the directly-configured directory
   entries. The result is exactly the per-entry expansion of the input: each
   non-empty entry is normalised, in order, and every empty entry is skipped.
   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5).

   The behaviour of interest is the emptiness skip: an empty configured entry
   must contribute nothing to the watched locations — pinned by the second
   postcondition. -/
method collectConfiguredDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectConfigured entries
  ensures ∀ es, entries = [] :: es → out = collectConfigured es
  ensures ∀ p, p ∈ out → ∃ e, e ∈ entries ∧ keepConfigured e = true ∧ p = normalizePath e
  do
    -- impl-start
    -- Pre-image skeleton: every configured entry is normalised unconditionally;
    -- there is NO emptiness test before normalisation. An empty entry is thus
    -- expanded into a spurious watched location instead of being skipped. The
    -- frozen spec (`collectConfigured`) drops empty entries, so the loop
    -- invariant is not maintained and `prove_correct` MUST fail — the divergence
    -- is exactly the `entries = [] :: es → out = collectConfigured es` clause
    -- (the reported regression).
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectConfigured (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := [normalizePath e] ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the configured collection: dropping one fewer
   element exposes the entry at `i-1` on the front, so `collectConfigured` peels
   one keep-decision. This is the single goal `loom_solve` leaves for the loop
   body. -/
lemma collectConfigured_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectConfigured (es.drop (i - 1)) =
      (if keepConfigured es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectConfigured (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectConfigured_cons]

prove_correct collectConfiguredDirs by
  loom_solve
  rw [collectConfigured_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectConfigured (entries.drop i)›]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Gather the set of locations to watch from a loader's supplied directory
   entries. Same shape as the configured collection, but an entry is admissible
   only when it is non-empty AND not already owned by the framework. The
   emptiness skip is independent of the ownership test: an empty entry
   contributes nothing even if it would otherwise pass the ownership test
   (pinned by the second postcondition).

   `entries` is read-only (not `mut`); the loop builds a fresh result and never
   mutates its input (directive 5). -/
method collectLoaderDirs (entries : List (List Char)) return (out : List (List Char))
  ensures out = collectLoader entries
  ensures ∀ es, entries = [] :: es → out = collectLoader es
  do
    -- impl-start
    -- Pre-image skeleton: a loader entry is dropped only when it is owned by the
    -- framework; there is NO emptiness test. An empty entry that is not
    -- framework-owned is therefore normalised into a spurious location instead
    -- of being skipped, so `prove_correct` MUST fail against `collectLoader`.
    let mut result : List (List Char) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = collectLoader (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let e := entries[i - 1]!
      result := (if !isFrameworkOwned e then [normalizePath e] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step for the loader collection. -/
lemma collectLoader_drop_step (es : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ es.length) :
    collectLoader (es.drop (i - 1)) =
      (if keepLoader es[i - 1]! then [normalizePath es[i - 1]!] else [])
        ++ collectLoader (es.drop i) := by
  have hlt : i - 1 < es.length := by omega
  have hcons : es.drop (i - 1) = es[i - 1]! :: es.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, collectLoader_cons]

prove_correct collectLoaderDirs by
  loom_solve
  rw [collectLoader_drop_step entries i (by omega) (by omega)]
  rw [‹result = collectLoader (entries.drop i)›]
