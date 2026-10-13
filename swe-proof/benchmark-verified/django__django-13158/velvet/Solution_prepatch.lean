import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No unchanged dependency callee is CONSUMED by this specification: the modeled
-- transformation is defined structurally over the input carrier in the `pure`
-- region below, so there is no `axiom`/imperative-stub callee to declare.
-- axioms-end

-- pure-start
/- One constituent sub-query of a set-combined query (the operands a combined
   query is built from). Abstracted to only the observations that decide which
   rows it contributes:

   * `rows`     — the rows this sub-query would contribute on its own.
   * `silenced` — whether this sub-query has been constrained to contribute
                  nothing (its row source has been forced empty). -/
structure Branch where
  rows : List Int
  silenced : Bool
  deriving Inhabited, DecidableEq

/- A set-combined query, abstracted to the observations that decide its rows:

   * `topSilenced` — whether the combined query's own top-level row source has
                     been forced empty.
   * `branches`    — the constituent sub-queries it is combined from. A combined
                     query draws its rows from these constituents, so forcing
                     only the top-level source empty does not stop the
                     constituents from contributing (see `combinedRows`). -/
structure Combined where
  topSilenced : Bool
  branches : List Branch
  deriving Inhabited

/- The rows a single sub-query contributes: none once it has been silenced,
   otherwise its own rows. -/
@[grind] def branchRows (b : Branch) : List Int :=
  if b.silenced then [] else b.rows

/- The rows a combined query yields: the constituents' contributions in order.
   The combined query's own top-level source does not gate the constituents —
   the rows flow from the constituent sub-queries. -/
def combinedRows : List Branch → List Int
  | []      => []
  | b :: bs => branchRows b ++ combinedRows bs

/- Silence a single sub-query: force its row source empty, preserving its rows
   field. -/
@[grind] def silence (b : Branch) : Branch :=
  { b with silenced := true }

/- Silence every constituent, in input order. Front-recursive so a single unfold
   is available per loop step (the fold pattern, plan §5.4). -/
def silenceAll : List Branch → List Branch
  | []      => []
  | b :: bs => silence b :: silenceAll bs

@[grind] lemma silenceAll_nil : silenceAll [] = [] := rfl
@[grind] lemma silenceAll_cons (b : Branch) (bs : List Branch) :
    silenceAll (b :: bs) = silence b :: silenceAll bs := rfl

/- A silenced sub-query contributes no rows. -/
@[grind] lemma branchRows_silence (b : Branch) : branchRows (silence b) = [] := by
  simp [branchRows, silence]

/- After silencing every constituent, a combined query yields no rows. -/
@[grind] lemma combinedRows_silenceAll : ∀ bs, combinedRows (silenceAll bs) = []
  | []      => rfl
  | b :: bs => by
      simp [silenceAll, combinedRows, branchRows_silence, combinedRows_silenceAll bs]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method emptyCombined (q : Combined) return (out : Combined)
  ensures out.topSilenced = true
  ensures out.branches = silenceAll q.branches
  ensures combinedRows out.branches = []
  do
    -- impl-start
    -- PRE-PATCH BEHAVIOR: only the combined query's own top-level row source is
    -- forced empty; the constituent sub-queries it is combined from are left
    -- untouched, so they keep contributing their rows.
    return { topSilenced := true, branches := q.branches }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `silenceAll` peels one `silence`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma silenceAll_drop_step (branches : List Branch) (i : Nat)
    (hi : 0 < i) (hle : i ≤ branches.length) :
    silenceAll (branches.drop (i - 1))
      = silence branches[i - 1]! :: silenceAll (branches.drop i) := by
  have hlt : i - 1 < branches.length := by omega
  have hcons : branches.drop (i - 1) = branches[i - 1]! :: branches.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, silenceAll_cons]

prove_correct emptyCombined by
  loom_solve
  rw [silenceAll_drop_step q.branches i (by omega) (by omega)]
  simp_all
