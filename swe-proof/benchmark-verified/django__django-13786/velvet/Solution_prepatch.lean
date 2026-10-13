import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no consumed axiom. The combined-settings operation
--  is modeled DEEPLY by `mergeMaps`/`pruneFold` below; map union and key removal
--  are language builtins (the analogue of `List.++`), not repo callees. The only
--  repository datum the spec refers to — the prescribed list of managed setting keys
--  bound to the free input `trackedKeys` — is an A-reference validated against the
--  real constant by axiom_check.py (G-AX), NOT a contract the proof consumes.)
-- axioms-end

-- pure-start
/- A settings map is carried as an association list of key→value string pairs (a
   dict of options). Two maps denote the same options iff they have the same set
   of key→value pairs; the operations below preserve that reading. -/
abbrev SettingMap := List (String × String)

/- Whether a key occurs in a settings map. -/
def keyPresent (k : String) (m : SettingMap) : Bool :=
  m.any (fun p => p.1 = k)

/- Drop every entry carrying key `k` from a settings map (a map has at most one
   such entry, so this removes that key's binding entirely). -/
def eraseKey (k : String) (m : SettingMap) : SettingMap :=
  m.filter (fun p => p.1 ≠ k)

/- The override-merge of two settings maps: every binding of the overriding map
   `b`, together with each binding of the base map `a` whose key the overriding
   map does not rebind. On a shared key the overriding value wins. -/
def mergeMaps (a b : SettingMap) : SettingMap :=
  b ++ a.filter (fun p => !(keyPresent p.1 b))

/- Restrict a settings map so that a prescribed set of managed keys reflects ONLY the
   overriding map `newMap`: for each managed key in `keys`, if the overriding map
   does not mention it, clear it from the map. Front-recursive (one unfold per
   loop step — the backward-fold pattern, plan §5.4). -/
def pruneFold (newMap : SettingMap) : List String → SettingMap → SettingMap
  | [],      m => m
  | k :: ks, m =>
      let rest := pruneFold newMap ks m
      if keyPresent k newMap then rest else eraseKey k rest

@[grind] lemma pruneFold_nil (newMap : SettingMap) (m : SettingMap) :
    pruneFold newMap [] m = m := rfl

@[grind] lemma pruneFold_cons (newMap : SettingMap) (k : String)
    (ks : List String) (m : SettingMap) :
    pruneFold newMap (k :: ks) m
      = (if keyPresent k newMap then pruneFold newMap ks m
         else eraseKey k (pruneFold newMap ks m)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combining two settings maps under a managed-key discipline.

   `baseMap` is the existing settings map; `newMap` is an overriding map; both are
   read-only inputs (neither is `mut` — the combination mutates neither, directive
   5). `trackedKeys` is the prescribed set of *managed* setting keys.

   The result is the override-merge `mergeMaps baseMap newMap` further restricted
   so that every managed key NOT mentioned by the overriding map is cleared. Thus
   a managed setting the overriding map omits does not silently persist from the
   base map: it is unset, exactly as the overriding map dictates. The result is a
   freshly built map equal to the deep computation on the inputs, so a combination
   cannot satisfy the postcondition by echoing the plain merge. -/
method combineTrackedSettings (baseMap : SettingMap) (newMap : SettingMap) (trackedKeys : List String) return (out : SettingMap)
  ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
  do
    -- impl-start
    -- Pre-image skeleton: the combination is the plain override-merge only — the
    -- managed-key restriction loop is absent, so a managed setting the overriding
    -- map omits silently persists from the base map. The frozen spec requires the
    -- restricted result (pruneFold), so prove_correct MUST fail.
    let result : SettingMap := mergeMaps baseMap newMap
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer managed key exposes the key at
   `i-1` on the front, so `pruneFold` peels one prune step. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma pruneFold_drop_step (newMap : SettingMap) (keys : List String)
    (m : SettingMap) (i : Nat) (hi : 0 < i) (hle : i ≤ keys.length) :
    pruneFold newMap (keys.drop (i - 1)) m
      = (if keyPresent keys[i - 1]! newMap then pruneFold newMap (keys.drop i) m
         else eraseKey keys[i - 1]! (pruneFold newMap (keys.drop i) m)) := by
  have hlt : i - 1 < keys.length := by omega
  have hcons : keys.drop (i - 1) = keys[i - 1]! :: keys.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, pruneFold_cons]

prove_correct combineTrackedSettings by
  loom_solve
  -- The pre-patch impl returns `mergeMaps baseMap newMap`, leaving the goal
  --   mergeMaps baseMap newMap = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)
  -- which is FALSE whenever a managed key is present in baseMap but absent from
  -- newMap (then the RHS erases it, the LHS keeps it). No tactic can close it;
  -- prove_correct MUST fail — G-DIFF.
  simp_all
