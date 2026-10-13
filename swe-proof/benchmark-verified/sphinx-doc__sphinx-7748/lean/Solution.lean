import Mathlib
-- imports-end

/-!
Reading object signatures from the leading text of a documentation comment.

A documentation comment is a list of *blocks*, and each block is a list of text
lines. A line is recognised as a signature line by a given extended-signature
matcher; a recognised line yields a *thing name*, an argument string and an
optional return annotation. A recognised line is accepted only when its thing
name is one of the object's candidate names.

The desired behavior collects **every** signature offered at the start of a
block, in order, rather than only the first one. Within a block the lines are
read top to bottom and stop at the first empty line. A signature line that ends
in a backslash is a *continuation*: another signature follows it on the next
line (the trailing backslash and trailing whitespace are dropped before
matching), so reading proceeds to the next line. A signature line that does NOT
end in a backslash is the last one of the run, so reading of that block stops
there.
Lines that are not recognised, or whose thing name is not a candidate, are
skipped without stopping. Across the list of blocks, the first block that yields
at least one signature provides the whole result (the first such signature is
the primary one and the rest follow it, all in order); later blocks are then
ignored. If no block yields a signature the result is empty.
-/

-- axioms-start
/-- The outcome of matching one line against the extended-signature matcher: the
thing name, the argument string, and the (possibly empty) return annotation. -/
structure SigMatch where
  base : String
  args : String
  retann : String
deriving DecidableEq, Repr

/-- One collected signature: an argument string and a (possibly empty) return
annotation. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Repr

/-- The given extended-signature matcher applied to a single line. It returns
`none` when the line is not a signature line, otherwise the parsed thing name /
arguments / return annotation. This matcher is UNCHANGED by the modeled behavior
and is invoked identically wherever a line must be classified; the modeled
behavior consumes no property of it beyond "it is a deterministic function of
the line". The proof agent may add a `_prop` axiom only if a proof obligation
later needs one. -/
opaque matchSig : String → Option SigMatch
-- axioms-end

-- pure-start
/-- The whitespace codepoints Python's `str.rstrip()` (with no argument)
removes — exactly the characters `str.isspace()` accepts: tab, LF, VT, FF, CR,
FS/GS/RS/US, space, NEL, NBSP, Ogham space mark, the Unicode space separators
U+2000–U+200A, LS, PS, NNBSP, MMSP, and ideographic space. Note this is WIDER
than Lean's `Char.isWhitespace` (which is only space/tab/CR/LF). -/
def pyWhitespaceCodes : List UInt32 :=
  [0x9, 0xA, 0xB, 0xC, 0xD, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]

/-- `str.isspace()` / the character class `str.rstrip()` strips. -/
def isPyWhitespace (c : Char) : Bool :=
  pyWhitespaceCodes.contains c.val

/-- Drop a continuation marker from the end of a line: remove trailing
backslashes, then any trailing whitespace exposed underneath them
(`line.rstrip('\\').rstrip()` — Python's whitespace set). -/
def stripContinuation (s : String) : String :=
  String.mk
    (((s.toList.reverse.dropWhile (· = '\\')).dropWhile isPyWhitespace).reverse)

/-- Read the leading signature run of a single block.

The lines are walked front to back. An empty line ends the run. A line ending in
a backslash is a continuation (matched against its stripped form, then reading
proceeds); any other line is the last candidate of the run. A line that the
matcher rejects, or whose thing name is not among `validNames`, is skipped. The
accepted signatures are returned in order. -/
def scanDoc (validNames : List String) : List String → List Sig
  | [] => []
  | line0 :: rest =>
    if line0 = "" then []
    else
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => scanDoc validNames rest
      | some m =>
        if validNames.contains m.base then
          let s : Sig := ⟨m.args, m.retann⟩
          if multiline then s :: scanDoc validNames rest else [s]
        else
          scanDoc validNames rest

/-- The collected signatures: the first block whose leading run is non-empty
supplies the entire result; otherwise the result is empty. -/
def collectSpec (validNames : List String) : List (List String) → List Sig
  | [] => []
  | doc :: docs =>
    let sigs := scanDoc validNames doc
    if sigs = [] then collectSpec validNames docs else sigs
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered list of signatures collected from the
documentation comment. This pins every component: the result's length, the order
of the signatures, and each signature's argument string and return annotation
are all determined by the input blocks and the candidate names. A correct result
must come from the first block that offers any signature, must include every
signature of that block's leading run (continuations included), and must stop at
the first non-continuation signature line; no signature may be dropped, added,
reordered, or sourced from a later block. -/
def problem_spec_collectSignatures
    (docstrings : List (List String)) (validNames : List String)
    (result : List Sig) : Prop :=
  result = collectSpec validNames docstrings
-- post-conditions-end

-- impl-start
/-- Collect every signature offered at the start of a documentation comment.
The blocks are scanned in order; within a block the lines are read top to bottom
until an empty line, the first signature is kept as the primary one and any
further continuation signatures are appended, and the scan of a block stops at
its first non-continuation signature line. The first block that yields a
signature provides the result. -/
def implementation_collectSignatures
    (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
  let mut result : Option Sig := none
  let mut signatures : List Sig := []
  for doclines in docstrings do
    for line0 in doclines do
      if line0.isEmpty then
        break
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => continue
      | some m =>
        if validNames.contains m.base then
          if result.isNone then
            result := some ⟨m.args, m.retann⟩
          else
            signatures := signatures ++ [⟨m.args, m.retann⟩]
          if multiline then
            continue
          else
            break
        else
          continue
    if result.isSome then
      break
  match result with
  | none => return []
  | some r => return r :: signatures
-- impl-end

-- proof-start
-- ==== module: defs ====

-- @decl:LoopState-start
/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
loops as their `ForInStep` state: `result` holds the primary (first-accepted)
signature once found, `signatures` accumulates the continuation signatures. -/
abbrev LoopState : Type := Option Sig × List Sig
-- @decl:LoopState-end

-- @decl:InnerBody-start
/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
`continue` ↦ `ForInStep.yield`. -/
def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
    ForInStep LoopState :=
  if line0.isEmpty then
    ForInStep.done st
  else
    let multiline := line0.endsWith "\\"
    let line := if multiline then stripContinuation line0 else line0
    match matchSig line with
    | none => ForInStep.yield st
    | some m =>
      if validNames.contains m.base then
        if st.1.isNone then
          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
        else
          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
      else
        ForInStep.yield st
-- @decl:InnerBody-end

-- @decl:OuterBody-start
/-- The desugared body of the outer `for doclines in docstrings` loop: run the
inner loop on the block, then `if result.isSome then break`. -/
def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
    ForInStep LoopState :=
  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
-- @decl:OuterBody-end

-- @decl:innerCharacterization-start
/-- Relation between the inner loop's entry state `entry` and exit state `exit`
over `block`: the leading run collected by `scanDoc` is distributed — its head
fills an empty `result`, its tail is appended to `signatures`; when `result` is
already set, the whole run is appended to `signatures`. -/
def innerCharacterization (validNames : List String) (block : List String)
    (entry exit : LoopState) : Prop :=
  match entry.1 with
  | none =>
    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
  | some r0 =>
    exit = (some r0, entry.2 ++ scanDoc validNames block)
-- @decl:innerCharacterization-end

-- @decl:outerCharacterization-start
/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
the exit state reproduces `collectSpec validNames docstrings` split into its
head (the primary `result`) and tail (the continuation `signatures`). -/
def outerCharacterization (validNames : List String) (docstrings : List (List String))
    (exit : LoopState) : Prop :=
  match collectSpec validNames docstrings with
  | [] => exit = (none, [])
  | r :: rest => exit = (some r, rest)
-- @decl:outerCharacterization-end

-- ==== module: Bridges ====

-- @ns:isEmpty_bridge-start
-- @decl:isEmpty_bridge-start
/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
theorem isEmpty_bridge (line0 : String) :
    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
  refine ⟨String.isEmpty_iff line0, ?_⟩
  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
-- @decl:isEmpty_bridge-end
-- @ns:isEmpty_bridge-end

-- @ns:forIn_step_reduction-start
-- @decl:forIn_step_reduction-start
/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
mapping `ForInStep.done`/`yield` to stop/recurse. -/
theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
    (body : α → β → Id (ForInStep β)) :
    (forIn (a :: as) b body : Id β)
      = (match (body a b : Id (ForInStep β)) with
         | ForInStep.done b' => (pure b' : Id β)
         | ForInStep.yield b' => forIn as b' body) := by
  simp only [List.forIn_cons, bind, pure]
  cases body a b <;> rfl
-- @decl:forIn_step_reduction-end
-- @ns:forIn_step_reduction-end

-- @ns:classification_defeq-start
-- @decl:classification_defeq-start
/-- On a non-empty line, `InnerBody` reduces to the same classification
sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
theorem classification_defeq (validNames : List String) (line0 : String)
    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
    InnerBody validNames line0 (result, sigs)
      = (let multiline := line0.endsWith "\\"
         let line := if multiline then stripContinuation line0 else line0
         match matchSig line with
         | none => ForInStep.yield (result, sigs)
         | some m =>
           if validNames.contains m.base then
             if result.isNone then
               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
             else
               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
           else ForInStep.yield (result, sigs)) := by
  simp only [InnerBody, h, Bool.false_eq_true, if_false]
-- @decl:classification_defeq-end
-- @ns:classification_defeq-end

-- ==== module: InnerLoop ====

-- @ns:inner_loop_characterization-start
-- @decl:inner_loop_characterization-start
/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
doclines` across the threaded `(result, signatures)` state. -/
theorem inner_loop_characterization (validNames : List String) (doclines : List String)
    (result : Option Sig) (sigs : List Sig) :
    innerCharacterization validNames doclines (result, sigs)
      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
  induction doclines generalizing result sigs with
  | nil =>
    cases result with
    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
        List.append_nil, forIn, List.forIn_nil]; rfl
    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
        List.forIn_nil]; rfl
  | cons line0 rest ih =>
    rw [forIn_step_reduction]
    by_cases hEmpty : line0.isEmpty = true
    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
        simp [InnerBody, hEmpty]
      rw [hb]
      cases result with
      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
          List.tail_nil, List.append_nil]; rfl
      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
          List.append_nil]; rfl
    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
      rw [classification_defeq validNames line0 result sigs hEmpty']
      simp only [innerCharacterization]
      rw [scanDoc]
      simp only [if_neg hne]
      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
      | none =>
        simp only [hm]
        cases result with
        | none => simpa [innerCharacterization] using ih none sigs
        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
      | some m =>
        by_cases hc : validNames.contains m.base
        · cases result with
          | none =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
                Option.isNone_none]
              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
              simp only [innerCharacterization] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
              rfl
          | some r0 =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
              simp only [innerCharacterization] at hih
              rw [List.append_assoc] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
              rfl
        · simp only [hm, hc, Bool.false_eq_true, if_false]
          cases result with
          | none => simpa [innerCharacterization] using ih none sigs
          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-- @decl:inner_loop_characterization-end
-- @ns:inner_loop_characterization-end

-- ==== module: OuterLoop ====

-- @ns:outer_result_none_invariant-start
-- @decl:outer_result_none_invariant-start
/-- A block whose leading run is empty leaves the outer state untouched at
`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
guard yields (does not break). -/
theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
    (h : scanDoc validNames doclines = []) :
    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
  have hchar := inner_loop_characterization validNames doclines none []
  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
    List.append_nil] at hchar
  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
-- @decl:outer_result_none_invariant-end
-- @ns:outer_result_none_invariant-end

-- @ns:outer_loop_characterization-start
-- @decl:outer_loop_characterization-start
/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
produces the state reproducing `collectSpec validNames docstrings`. -/
theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
    outerCharacterization validNames docstrings
      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
  induction docstrings with
  | nil =>
    simp only [outerCharacterization, collectSpec]
    rfl
  | cons doc docs ih =>
    rw [forIn_step_reduction]
    have hinner := inner_loop_characterization validNames doc none []
    simp only [innerCharacterization] at hinner
    simp only [OuterBody]
    rw [hinner]
    simp only [outerCharacterization, collectSpec]
    cases hsc : scanDoc validNames doc with
    | nil =>
      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
      simpa only [hsc] using ih
    | cons r rest =>
      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
      rfl
-- @decl:outer_loop_characterization-end
-- @ns:outer_loop_characterization-end

-- ==== module: Bridge to implementation ====

-- @ns:forIn_mprod_eq_prod-start
-- @decl:forIn_mprod_eq_prod-start
/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
implementation threads its two mutable variables as an `MProd (Option Sig)
(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
`OuterBody`/`InnerBody` (`Prod`) normal form. -/
theorem forIn_mprod_eq_prod {α β γ : Type}
    (l : List α) (b0 : β) (c0 : γ)
    (fp : α → (β × γ) → ForInStep (β × γ)) :
    (forIn l (⟨b0, c0⟩ : MProd β γ)
      (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
  induction l generalizing b0 c0 with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.forIn_cons]
    cases h : fp a (b0, c0) with
    | done s => rfl
    | yield s => exact ih s.1 s.2
-- @decl:forIn_mprod_eq_prod-end
-- @ns:forIn_mprod_eq_prod-end

-- @ns:impl_run_bridge-start
-- @decl:impl_run_bridge-start
/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
`break`/`continue`, and an outer `if result.isSome then break`) to the pure
`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
and read the final `match result with | none => [] | some r => r :: sigs`. -/
theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
    implementation_collectSignatures docstrings validNames
      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
            (OuterBody validNames)) : Id LoopState) with
         | (none, _) => []
         | (some r, sigs) => r :: sigs) := by
  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
      (fp : α → (β × γ) → ForInStep (β × γ)),
      (∀ a r, g a r = (match fp a (r.1, r.2) with
                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
    intro α β γ l b0 c0 g fp h
    have hg : g = (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
      funext a r; exact h a r
    rw [hg]
    exact forIn_mprod_eq_prod l b0 c0 fp
  unfold implementation_collectSignatures
  simp only [Id.run, bind, pure]
  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
  case hbody =>
    intro doclines r
    unfold OuterBody
    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
    case hinner =>
      intro line0 s
      unfold InnerBody
      by_cases h1 : line0.isEmpty = true
      · simp only [h1, if_true]
      · simp only [h1, Bool.false_eq_true, if_false]
        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
        | none => rfl
        | some m =>
          by_cases hc : validNames.contains m.base = true
          · simp only [hc, if_true]
            by_cases hn : s.1.isNone = true
            · simp only [hn, if_true]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
            · simp only [hn, Bool.false_eq_true, if_false]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
          · simp only [hc, Bool.false_eq_true, if_false]
    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
    obtain ⟨pa, pb⟩ := p
    by_cases hs : pa.isSome = true
    · simp only [hs, if_true]
    · simp only [hs, Bool.false_eq_true, if_false]
  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
    cases a <;> rfl
-- @decl:impl_run_bridge-end
-- @ns:impl_run_bridge-end


theorem correct_collectSignatures :
    ∀ (docstrings : List (List String)) (validNames : List String),
      problem_spec_collectSignatures docstrings validNames
        (implementation_collectSignatures docstrings validNames) := by
  intro docstrings validNames
  show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
  rw [impl_run_bridge]
  have h := outer_loop_characterization validNames docstrings
  simp only [outerCharacterization] at h
  cases hc : collectSpec validNames docstrings with
  | nil =>
    rw [hc] at h
    rw [h]
  | cons r rest =>
    rw [hc] at h
    rw [h]
-- proof-end
