import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec is
   a pure forward scan over an ordered sequence of result-set candidates: locate
   the first candidate the ordering term lines up with, and — when none does —
   decide the term's disposition from the trailing candidate's labelled status.
   Every observable is computed structurally from the candidate sequence; nothing
   is borrowed from an oracle, so there is no consumed axiom. The per-candidate
   alignment test that the scan applies is part of the surrounding, unchanged
   machinery; it is supplied to the model as the candidate's `aligns` flag and is
   exercised structurally by the executable conformance check (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A result-set candidate as seen by the scan: `labelled` records whether this
   candidate carries an explicit output label, and `aligns` records whether the
   ordering term under consideration lines up with this candidate (the outcome of
   the surrounding, unchanged alignment machinery). -/
structure Candidate where
  labelled : Bool
  aligns   : Bool
  deriving DecidableEq, Inhabited, Repr

/- The disposition the scan assigns to one ordering term:
   * `position n` — the term is bound to the 1-based position `n` of an existing
     candidate it lines up with;
   * `appended n` — no existing candidate lines up and the trailing candidate is
     unlabelled, so the term's source is appended to the query's select sequence
     (a sequence tracked SEPARATELY from the scanned candidates — it may be
     shorter or longer) and bound to the resulting 1-based position `n`, i.e.
     one past that sequence's pre-append length;
   * `rejected` — no existing candidate lines up and the trailing candidate is
     labelled, so the term cannot be placed. -/
inductive Disposition where
  | position : Nat → Disposition
  | appended : Nat → Disposition
  | rejected : Disposition
  deriving DecidableEq, Inhabited, Repr

/- The 0-based index of the first candidate the ordering term lines up with, or
   `none` if none does. Front-recursive so a single unfold is available per loop
   step (the scan/fold pattern, plan §5.4). -/
def firstAligned : List Candidate → Option Nat
  | []      => none
  | c :: cs => if c.aligns then some 0 else (firstAligned cs).map (· + 1)

@[grind] lemma firstAligned_nil : firstAligned [] = none := rfl

@[grind] lemma firstAligned_cons (c : Candidate) (cs : List Candidate) :
    firstAligned (c :: cs) =
      (if c.aligns then some 0 else (firstAligned cs).map (· + 1)) := rfl

/- Whether the trailing candidate carries an explicit label (the value the scan's
   fall-through path inspects). Empty sequence ⇒ no trailing candidate. -/
def lastLabelled (cs : List Candidate) : Bool :=
  (cs.getLast?).elim false (·.labelled)

/- The disposition the modeled branch assigns to one ordering term against the
   candidate sequence. When some candidate lines up, the term takes that
   candidate's 1-based position. When none does, the trailing candidate's label
   decides: a labelled trailing candidate ⇒ the term is rejected; an unlabelled
   one ⇒ the term's source is appended to the query's select sequence and the
   term is bound to position `querySelectLen + 1`, where `querySelectLen` is
   that sequence's length BEFORE the append. The query's select sequence is a
   distinct observable from the scanned candidates (the compiler's result-set
   columns); their lengths need not agree, so the appended position is pinned
   to `querySelectLen`, not to `cs.length`. Matched positions are pinned via
   `(firstAligned …).map (· + 1)` so the result is exactly the position the
   scan produces. -/
def disposition (cs : List Candidate) (querySelectLen : Nat) : Disposition :=
  match (firstAligned cs).map (· + 1) with
  | some p => Disposition.position p
  | none   => if lastLabelled cs then Disposition.rejected
              else Disposition.appended (querySelectLen + 1)

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-candidate scan step, carried at the 1-based offset `i + 1`: scanning
   from index `i` either reports the balancing position immediately (when the
   candidate at `i` lines up) or defers to the scan from `i + 1` with the offset
   advanced by one. This is exactly the equation the loop body re-establishes
   each step. -/
lemma firstAligned_shift (xs : List Candidate) (i : Nat) (hi : i < xs.length) :
    (firstAligned (xs.drop i)).map (· + (i + 1)) =
      (if (xs[i]!).aligns then some (i + 1)
       else (firstAligned (xs.drop (i + 1))).map (· + (i + 1 + 1))) := by
  rw [drop_cons_eq xs i hi, firstAligned_cons]
  split
  · simp
  · cases firstAligned (xs.drop (i + 1)) with
    | none => rfl
    | some x => simp; omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine, for one ordering term, how it is bound against the ordered sequence
   of result-set `candidates`. The scan walks the candidates in order and binds
   the term to the first candidate it lines up with; if none lines up, the
   trailing candidate's label decides whether the term is rejected or its source
   is appended to the query's select sequence — whose pre-append length is the
   separately-supplied `querySelectLen` (it is a DISTINCT sequence from the
   scanned candidates and its length may differ) — binding the term to position
   `querySelectLen + 1`. `candidates` is read-only — it is not `mut`; the scan
   reads it and returns a disposition, mutating nothing it is handed
   (directive 5). The sequence is non-empty: a fall-through disposition inspects
   the trailing candidate. -/
method resolveOrderingTerm (candidates : List Candidate) (querySelectLen : Nat)
    return (out : Disposition)
  require candidates ≠ []
  ensures out = disposition candidates querySelectLen
  do
    -- impl-start
    -- Pre-image skeleton: the fall-through path (no candidate lines up) ALWAYS
    -- reports `rejected`, regardless of the trailing candidate's label. The
    -- frozen spec requires `appended (length + 1)` when the trailing candidate
    -- is unlabelled, so prove_correct MUST fail.
    let mut i := 0
    let mut res : Option Nat := none
    while i < candidates.length ∧ res = none
      invariant i ≤ candidates.length
      invariant match res with
                | some p => (firstAligned candidates).map (· + 1) = some p
                | none   => (firstAligned candidates).map (· + 1)
                              = (firstAligned (candidates.drop i)).map (· + (i + 1))
      done_with res ≠ none ∨ i = candidates.length
      decreasing (candidates.length - i) + (if res = none then 1 else 0)
    do
      if (candidates[i]!).aligns then
        res := some (i + 1)
      else
        i := i + 1
    match res with
    | some p => return Disposition.position p
    | none =>
      return Disposition.rejected
    -- impl-end

prove_correct resolveOrderingTerm by
  loom_solve
  all_goals (
    try (rw [firstAligned_shift candidates i (by omega)] at invariant_2)
    simp_all [disposition, lastLabelled, firstAligned_nil, Option.map])
