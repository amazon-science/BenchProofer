import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no axiomatized callee. The facts the chunk inventory
   consults about each variable — whether its cheap storage descriptor
   advertises a chunk layout and which one, whether reading that advertised
   layout back off the variable delivers it, and (orthogonally) whether forcing
   materialization of its values would succeed — are abstracted as the input
   fields `chunks` / `layoutReadable` / `accessible` of the variable record.
   This is a pure type refinement of the variable carrier (mapping.md §2),
   validated by axiom_check.py (the R-bridge) and conformance_check.py
   (G-CONF); nothing is left as an opaque assumption. -/
-- axioms-end

-- pure-start
/- The ways assembling the inventory can fail:
     * `inconsistent`      — two DIFFERENT variables that are both chunked
                             advertise different block lengths for one shared
                             dimension. Within a single variable a repeated
                             dimension is resolved by overwriting, not by this
                             failure (`dedupeLast`, mapping.md §1.1).
     * `layoutUnavailable` — a variable's descriptor advertises a chunk layout,
                             but reading that layout back off the variable does
                             not deliver one. That read is surfaced through the
                             variable's value view, so it fails when those
                             values cannot be obtained, and equally when what
                             they carry is not a layout (mapping.md §2).
     * `valuesUnavailable` — forcing a variable's values into memory fails.
                             Deciding WHETHER a variable is chunked must never
                             incur this; the outcome is named here only so the
                             twin can express it. -/
inductive ChunkErr where
  | inconsistent
  | layoutUnavailable
  | valuesUnavailable
  deriving DecidableEq, Inhabited

/- One variable, abstracted to exactly the three facts assembling the inventory
   observes:
     * `chunks`         — the per-dimension block layout the variable's cheap
                          storage descriptor advertises, as the (dimension,
                          block-length) pairs the variable's own layout read
                          yields — in that read's order, and NOT necessarily
                          naming distinct dimensions; `none` when the descriptor
                          advertises no layout at all. Which of the two it is is
                          ALWAYS observable, independent of the values.
     * `layoutReadable` — for a variable that DOES advertise a layout, whether
                          reading that layout back off the variable delivers it.
                          The read is surfaced through the variable's value
                          view, so it can fail. Consulted only on the
                          advertising leg: a variable that advertises no layout
                          is never read at all, so on that leg this field is
                          unconstrained and the outcome is independent of it
                          (`mergeVar_unadvertised`, mapping.md §2).
     * `accessible`     — whether forcing the variable's values into memory
                          would succeed. Deciding WHETHER a variable is chunked
                          must NOT depend on this: the advertisement is read off
                          the descriptor. Carried only as an orthogonal
                          observation of the variable (mapping.md §2). -/
structure VarDesc where
  chunks         : Option (List (Int × Int))
  accessible     : Bool
  layoutReadable : Bool := true
  deriving Inhabited, DecidableEq

/- Record one (dimension, block-length) pair into the running inventory: if the
   dimension is already present it must agree (else the inconsistency failure);
   a new dimension is appended. -/
def mergePair (acc : List (Int × Int)) (p : Int × Int) :
    Except ChunkErr (List (Int × Int)) :=
  match acc.lookup p.1 with
  | some sz => if sz = p.2 then Except.ok acc else Except.error ChunkErr.inconsistent
  | none    => Except.ok (acc ++ [p])

/- Merge one variable's per-dimension layout into the running inventory, left to
   right, short circuiting on the first disagreement. Every pair reaching here
   names a distinct dimension (`dedupeLast` below), so each `mergePair` compares
   against dimensions contributed by EARLIER variables — which is the only place
   the repo compares before inserting. -/
def mergePairs : List (Int × Int) → List (Int × Int) → Except ChunkErr (List (Int × Int))
  | acc, []      => Except.ok acc
  | acc, p :: ps =>
      match mergePair acc p with
      | Except.ok acc' => mergePairs acc' ps
      | Except.error e => Except.error e

/- Assemble ONE variable's advertised pairs into the per-dimension mapping its
   own read yields. The read builds a mapping KEYED BY DIMENSION, so a dimension
   the variable advertises more than once is not compared but overwritten: it
   keeps the position of its FIRST occurrence and the block length of its LAST.
   A variable may genuinely advertise a dimension twice — its dimension names
   need not be distinct — and when it does, the two block lengths need not
   agree; resolving that is mapping construction, not a disagreement
   (mapping.md §1.1, §2). The must-agree rule below therefore governs pairs
   coming from DIFFERENT variables only. -/
def dedupeLast (pairs : List (Int × Int)) : List (Int × Int) :=
  pairs.foldl
    (fun acc p =>
      if acc.any (fun q => q.1 == p.1)
      then acc.map (fun q => if q.1 == p.1 then p else q)
      else acc ++ [p])
    []

/- Every dimension a variable advertises twice keeps its LAST block length, and
   the two lengths are never required to agree — the pin that separates
   within-variable mapping construction from the between-variable must-agree
   rule. -/
lemma dedupeLast_repeat_takes_last (d a b : Int) :
    dedupeLast [(d, a), (d, b)] = [(d, b)] := by
  simp [dedupeLast]

/- Fold one variable into the inventory accumulated for the variables BEFORE
   it: a prior failure propagates; a variable whose descriptor advertises no
   layout contributes nothing and is not read at all; a variable that does
   advertise one has that layout read back off it, which either delivers a
   per-dimension mapping — assembled by `dedupeLast`, then merged into the
   inventory — or fails, failing the whole inventory. Whether the variable's
   values could be materialized (`accessible`) is never consulted to decide
   which of those legs applies: the advertisement is read off the descriptor
   alone. -/
def mergeVar (v : VarDesc) (rest : Except ChunkErr (List (Int × Int))) :
    Except ChunkErr (List (Int × Int)) :=
  match rest with
  | Except.error e => Except.error e
  | Except.ok acc =>
      match v.chunks with
      | none       => Except.ok acc
      | some pairs =>
          if v.layoutReadable then mergePairs acc (dedupeLast pairs)
          else Except.error ChunkErr.layoutUnavailable

/- A variable whose descriptor advertises no layout leaves the inventory exactly
   as it found it — at EVERY value of the two value-side observations. This is
   the discriminating content of the desired behaviour (mapping.md §3.1): such a
   variable is passed over silently, so neither the failure of forcing its values
   nor the failure of a layout read it never performs can reach the outcome. -/
lemma mergeVar_unadvertised (a r : Bool) (rest : Except ChunkErr (List (Int × Int))) :
    mergeVar { chunks := none, accessible := a, layoutReadable := r } rest = rest := by
  cases rest <;> rfl

/- On the leg where the layout read does not deliver, the pairs the descriptor
   advertised are not observable, and the outcome does not depend on them (nor on
   materializability). This is what makes the `chunks` payload a don't-care there
   rather than a smuggled extra observation (mapping.md §2). -/
lemma mergeVar_unreadable_independent (p q : List (Int × Int)) (a b : Bool)
    (rest : Except ChunkErr (List (Int × Int))) :
    mergeVar { chunks := some p, accessible := a, layoutReadable := false } rest
      = mergeVar { chunks := some q, accessible := b, layoutReadable := false } rest := by
  cases rest <;> rfl

/- One left-fold step: fold the next variable into the inventory accumulated so
   far (argument order flipped to the `List.foldl` convention). -/
def mergeStep (acc : Except ChunkErr (List (Int × Int))) (v : VarDesc) :
    Except ChunkErr (List (Int × Int)) :=
  mergeVar v acc

/- The whole inventory: fold every variable's advertised chunk layout into the
   running inventory, FIRST variable first — the same left-to-right order in
   which the repo scans the variables, so a dimension is inserted the first
   time some variable advertises it and the insertion order of the resulting
   (dimension, block-length) pairs is the observable insertion order of the
   real assembled mapping (mapping.md §2). Success exactly when every layout a
   variable advertises is delivered by its own read and every chunked variable
   agrees with the others on shared dimensions; failure with `layoutUnavailable`
   or `inconsistent` — whichever the scan meets first — otherwise. In no case
   does the outcome depend on a variable's `accessible` bit. -/
def chunkInventory (vars : List VarDesc) : Except ChunkErr (List (Int × Int)) :=
  vars.foldl mergeStep (Except.ok [])

@[grind] lemma chunkInventory_nil : chunkInventory [] = Except.ok [] := rfl
-- pure-end

/- Folding over a one-longer prefix is the fold over the prefix followed by one
   more step on the newly-exposed element. This is the single fact the loop body
   leaves for `loom_solve`. -/
lemma foldl_take_succ {α β : Type} [Inhabited α] (f : β → α → β) (b : β)
    (l : List α) (i : Nat) (hi : i < l.length) :
    (l.take (i + 1)).foldl f b = f ((l.take i).foldl f b) l[i]! := by
  have happ : l.take (i + 1) = l.take i ++ [l[i]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
    exact List.take_succ_eq_append_getElem hi
  rw [happ, List.foldl_append, List.foldl_cons, List.foldl_nil]

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the chunk inventory of a collection of variables: the per-dimension
   block layout merged across every variable that advertises one, failing when a
   variable's advertised layout cannot be read back off it, and when two chunked
   variables disagree on a shared dimension.

   `vars` is consulted read-only: it is NOT declared `mut` (directive 5). The
   result is pinned to `chunkInventory vars`, which depends on each variable's
   advertised chunk layout (`VarDesc.chunks`) and, where one is advertised, on
   whether reading it back delivers it (`VarDesc.layoutReadable`) — and NEVER on
   whether the variable's values can be materialized (`VarDesc.accessible`). So a
   variable whose values cannot be brought into memory but which advertises no
   chunk layout must be passed over silently — it contributes nothing and causes
   no failure. -/
method buildChunkInventory (vars : List VarDesc)
    return (out : Except ChunkErr (List (Int × Int)))
  ensures out = chunkInventory vars
  do
    -- impl-start
    -- PRE-IMAGE (defective) skeleton: to decide whether a variable is chunked,
    -- this version FORCES the variable's values into memory first (it consults
    -- the materialized values, not the cheap storage descriptor). For a variable
    -- whose values cannot be materialized (`accessible = false`) that force
    -- fails -- modeled as the `valuesUnavailable` error -- even when the
    -- variable advertises NO chunk layout and should simply have been passed
    -- over. Everything downstream of the guard is unchanged from the desired
    -- behaviour (an advertised layout is still read back, and a read that does
    -- not deliver still fails with `layoutUnavailable`), so the ONLY divergence
    -- this twin carries is the value-forcing guard. The frozen spec requires
    -- `chunkInventory vars`, which reads `v.chunks` off the descriptor and never
    -- consults `v.accessible`, so prove_correct MUST fail on any input
    -- containing an inaccessible, un-chunked variable.
    let mut acc : Except ChunkErr (List (Int × Int)) := Except.ok []
    let mut i := 0
    while i < vars.length
      invariant 0 ≤ i ∧ i ≤ vars.length
      invariant acc = (vars.take i).foldl mergeStep (Except.ok [])
      done_with i = vars.length
      decreasing vars.length - i
    do
      let v := vars[i]!
      acc := (match acc with
        | Except.error e => Except.error e
        | Except.ok a =>
            if !v.accessible then Except.error ChunkErr.valuesUnavailable
            else match v.chunks with
              | none       => Except.ok a
              | some pairs =>
                  if v.layoutReadable then mergePairs a (dedupeLast pairs)
                  else Except.error ChunkErr.layoutUnavailable)
      i := i + 1
    return acc
    -- impl-end

prove_correct buildChunkInventory by
  loom_solve
  · rw [foldl_take_succ mergeStep (Except.ok []) vars i (by omega), ← invariant_2]
  · simp_all [chunkInventory, List.take_length]
