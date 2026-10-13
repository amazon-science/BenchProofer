import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the roster of documentable entries is produced by an
--  unchanged collector and is consumed here as plain input data (`roster`); the
--  selection decision — full-roster mode vs published-subset mode vs an
--  explicitly-named subset — is a pure function of the inputs, modeled deeply
--  over `List Int`. There is no unchanged library callee the proof must
--  axiomatize.)
-- axioms-end

-- pure-start
/- One returned entry: the entry's name together with whether it has been marked
   to be left out of the rendered documentation. `name` identifies the entry;
   `omitted = true` means the entry is present in the returned roster but flagged
   to be omitted. -/
structure MemberOut where
  name : Int
  omitted : Bool
deriving DecidableEq, Inhabited, Repr

/- The result of deciding what a module documents: a roster of entries together
   with a flag telling the caller whether it must ADDITIONALLY filter the
   implicit entries by their origin. The flag is set only in the one situation
   where the returned roster is the whole implicit set with nothing pre-marked. -/
structure MemberResult where
  checkOrigin : Bool
  entries : List MemberOut
deriving DecidableEq, Inhabited, Repr

/- Full-roster mode with no published list: every entry is returned unmarked and
   the caller is told to filter by origin. Front-recursive over the roster. -/
def markAllExposed : List Int → List MemberOut
  | []      => []
  | n :: ns => { name := n, omitted := false } :: markAllExposed ns

@[grind] lemma markAllExposed_nil : markAllExposed [] = [] := rfl
@[grind] lemma markAllExposed_cons (n : Int) (ns : List Int) :
    markAllExposed (n :: ns) = { name := n, omitted := false } :: markAllExposed ns := rfl

/- Full-roster mode WITH a published list: every entry is returned, but an entry
   is marked omitted exactly when its name is NOT among the published names.
   Decided by membership in the published list — so a published list that names
   nothing marks EVERY entry omitted (nothing is published). Front-recursive. -/
def markByPublished (published : List Int) : List Int → List MemberOut
  | []      => []
  | n :: ns => { name := n, omitted := decide (n ∉ published) } :: markByPublished published ns

@[grind] lemma markByPublished_nil (published : List Int) :
    markByPublished published [] = [] := rfl
@[grind] lemma markByPublished_cons (published : List Int) (n : Int) (ns : List Int) :
    markByPublished published (n :: ns) =
      { name := n, omitted := decide (n ∉ published) } :: markByPublished published ns := rfl

/- Explicit-subset mode: return, unmarked and in request order, each requested
   name that actually exists in the roster (a requested name absent from the
   roster is dropped). Front-recursive over the request list. -/
def selectRequested (roster : List Int) : List Int → List MemberOut
  | []      => []
  | n :: ns =>
      (if n ∈ roster then [{ name := n, omitted := false }] else []) ++ selectRequested roster ns

@[grind] lemma selectRequested_nil (roster : List Int) :
    selectRequested roster [] = [] := rfl
@[grind] lemma selectRequested_cons (roster : List Int) (n : Int) (ns : List Int) :
    selectRequested roster (n :: ns) =
      (if n ∈ roster then [{ name := n, omitted := false }] else []) ++ selectRequested roster ns := rfl

/- The whole decision. `exposeAll` selects the mode:
   * `exposeAll = false` — return only the explicitly requested entries that
     exist in the roster, unmarked; never ask the caller to filter by origin.
   * `exposeAll = true` — implicit mode, governed by the OPTIONAL published list:
       - `none` (no published list): return the full roster unmarked and ask the
         caller to filter by origin;
       - `some published` (a published list IS supplied): return the full roster
         but mark omitted every entry not among the published names, and do NOT
         ask the caller to filter by origin. Crucially this is decided by the
         PRESENCE of the published list, not by whether it lists anything: a
         supplied list that names nothing marks every entry omitted. -/
def decideMembers (exposeAll : Bool) (published : Option (List Int))
    (roster : List Int) (requested : List Int) : MemberResult :=
  if exposeAll then
    match published with
    | none      => { checkOrigin := true,  entries := markAllExposed roster }
    | some pub  => { checkOrigin := false, entries := markByPublished pub roster }
  else
    { checkOrigin := false, entries := selectRequested roster requested }

/- A supplied-but-empty published list marks every roster entry omitted: in
   `markByPublished [] roster` each entry's `omitted` is `decide (n ∉ [])`, which
   is `true`. This is the behaviour the issue demands — an explicitly empty
   published list documents nothing — and the clause on which the pre-image
   skeleton diverges. -/
@[grind] lemma markByPublished_empty (roster : List Int) :
    markByPublished [] roster = roster.map (fun n => { name := n, omitted := true }) := by
  induction roster with
  | nil => rfl
  | cons n ns ih => rw [markByPublished_cons]; simp [ih]

/- Hence: in full-roster mode, a supplied-but-empty published list yields a
   result that asks for no origin filtering and marks every entry omitted. -/
@[grind] lemma decideMembers_empty_published (roster requested : List Int) :
    decideMembers true (some []) roster requested =
      { checkOrigin := false,
        entries := roster.map (fun n => { name := n, omitted := true }) } := by
  simp [decideMembers, markByPublished_empty]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A documentation generator decides which of a module's entries to document.

   `exposeAll` (read-only) chooses the mode. When it is false, only the entries
   the caller explicitly `requested` — and that actually exist in the `roster` —
   are documented, in request order. When it is true, the implicit roster is
   governed by an OPTIONAL `published` list of names:

   - when ABSENT, the full roster is documented and the caller is additionally
     asked to filter the implicit entries by their origin (`checkOrigin = true`);
   - when PRESENT, the full roster is returned but every entry whose name is not
     among the published names is marked omitted, and no origin filtering is
     requested (`checkOrigin = false`).

   The distinction between "no published list" and "a published list that names
   nothing" is the whole point: an explicitly empty published list documents
   nothing — it does NOT fall back to documenting everything.

   The optional published list is modeled as `Option (List Int)` so that
   "absent" and "present but empty" are genuinely different inputs; entry names
   are modeled as distinct `Int` identifiers; the result pairs the
   origin-filter flag with the returned entries (each carrying its omitted mark).

   `exposeAll`, `published`, `roster` and `requested` are read-only (not `mut`);
   the routine builds a fresh result and mutates none of them (directive 5). -/
method selectDocumentedMembers (exposeAll : Bool) (published : Option (List Int))
    (roster : List Int) (requested : List Int) return (out : MemberResult)
  ensures out = decideMembers exposeAll published roster requested
  ensures (exposeAll = true ∧ published = some []) →
            out.checkOrigin = false ∧
            out.entries = roster.map (fun n => { name := n, omitted := true })
  ensures (exposeAll = true ∧ published = none) → out.checkOrigin = true
  do
    -- impl-start
    -- Pre-image skeleton: the published list is treated as ACTIVE only when it
    -- both is present AND names at least one entry (the truthiness short-circuit
    -- `if not <list>`). A present-but-empty published list is therefore handled
    -- like an absent one — the full roster is documented unmarked and origin
    -- filtering is requested — instead of marking everything omitted. The frozen
    -- spec (`decideMembers`) treats a present published list by PRESENCE alone,
    -- so `prove_correct` MUST fail; the divergence is exactly the
    -- `published = some [] → checkOrigin = false ∧ all omitted` clause (the
    -- reported bug — an explicitly empty published list is ignored).
    if exposeAll then
      let r : MemberResult :=
        match published with
        | none =>
            { checkOrigin := true, entries := markAllExposed roster }
        | some pub =>
            if pub.isEmpty then
              { checkOrigin := true, entries := markAllExposed roster }
            else
              { checkOrigin := false, entries := markByPublished pub roster }
      return r
    else
      let mut result : List MemberOut := []
      let mut i := requested.length
      while i > 0
        invariant 0 ≤ i ∧ i ≤ requested.length
        invariant result = selectRequested roster (requested.drop i)
        done_with i = 0
        decreasing i
      do
        let n := requested[i - 1]!
        result := (if n ∈ roster then [{ name := n, omitted := false }] else []) ++ result
        i := i - 1
      return { checkOrigin := false, entries := result }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `selectRequested` peels one membership decision. This
   is the single goal `loom_solve` leaves for the loop body. -/
lemma selectRequested_drop_step (roster : List Int) (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    selectRequested roster (xs.drop (i - 1)) =
      (if xs[i - 1]! ∈ roster then [{ name := xs[i - 1]!, omitted := false }] else [])
        ++ selectRequested roster (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selectRequested_cons]

prove_correct selectDocumentedMembers by
  loom_solve <;>
    first
      | (rw [selectRequested_drop_step roster requested i (by omega) (by omega)];
         rw [‹result = selectRequested roster (requested.drop i)›])
      | (subst done_1; simp_all [decideMembers])
      | simp_all [decideMembers]
