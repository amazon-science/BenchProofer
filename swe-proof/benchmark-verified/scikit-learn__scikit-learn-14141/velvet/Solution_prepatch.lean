import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The version string reported for one installed third-party dependency — `none`
   when that dependency is absent or exposes no version. This is an unchanged
   environment query (import the module, read its advertised version); it is
   modeled as an uninterpreted function because its result is environment
   dependent and is NOT what this report's contract pins. The contract pins only
   WHICH dependencies the report covers, never the concrete version values.
   Provenance + soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom lookupVersion : List Char → Option (List Char)
-- axioms-end

-- pure-start
/- The set of third-party dependencies the diagnostic version report covers, in
   report order. A definite, stable roster so the report is predictable across
   environments; it includes joblib alongside the other relevant scientific and
   packaging dependencies. -/
def dependencyNames : List (List Char) :=
  [ "pip".toList,
    "setuptools".toList,
    "sklearn".toList,
    "numpy".toList,
    "scipy".toList,
    "Cython".toList,
    "pandas".toList,
    "matplotlib".toList,
    "joblib".toList ]

/- The report entry for one dependency: its name paired with its reported
   version. The whole report is the per-dependency expansion of the roster, in
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
noncomputable def depEntries : List (List Char) → List (List Char × Option (List Char))
  | []      => []
  | n :: ns => (n, lookupVersion n) :: depEntries ns

@[grind] lemma depEntries_nil : depEntries [] = [] := rfl
@[grind] lemma depEntries_cons (n : List Char) (ns : List (List Char)) :
    depEntries (n :: ns) = (n, lookupVersion n) :: depEntries ns := rfl

/- Projecting the names out of the report recovers exactly the roster: every
   dependency in the roster is covered, in order, regardless of its version. -/
@[grind] lemma depEntries_keys (ns : List (List Char)) :
    (depEntries ns).map Prod.fst = ns := by
  induction ns with
  | nil => rfl
  | cons n ns ih => simp [depEntries, ih]

/- joblib is one of the covered dependencies. -/
@[grind] lemma joblib_mem_roster : "joblib".toList ∈ dependencyNames := by decide

/- The non-deterministic choice of one dependency's reported version is
   well-posed: for any target value `v`, the set of values equal to `v` is
   non-empty (`v` itself). This supplies the constructive existence witness so
   the `:|` choice in the loop body elaborates. It does NOT weaken verification:
   under demonic choice the postcondition must hold for every value the predicate
   allows — here exactly `lookupVersion n`. -/
noncomputable instance findableEqOptList (v : Option (List Char)) (n : Lean.Name) :
    Findable (fun e : Option (List Char) => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section
method collectDependencyVersions
    return (out : List (List Char × Option (List Char)))
  ensures out = depEntries dependencyNames
  ensures "joblib".toList ∈ out.map Prod.fst
  do
    -- impl-start
    -- Pre-image skeleton: the roster the report iterates over omits its final
    -- entry (`dependencyNames.dropLast`), so the produced report covers one
    -- fewer dependency than the frozen spec requires. `prove_correct` MUST fail
    -- (the result differs from `depEntries dependencyNames` and the final entry
    -- is absent from the keys).
    let names := dependencyNames.dropLast
    let mut result : List (List Char × Option (List Char)) := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = depEntries (names.drop i)
      done_with i = 0
      decreasing i
    do
      let n := names[i - 1]!
      let ver :| ver = lookupVersion n
      result := (n, ver) :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `depEntries` peels one entry. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma depEntries_drop_step (names : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ names.length) :
    depEntries (names.drop (i - 1))
      = (names[i - 1]!, lookupVersion names[i - 1]!) :: depEntries (names.drop i) := by
  have hlt : i - 1 < names.length := by omega
  have hcons : names.drop (i - 1) = names[i - 1]! :: names.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, depEntries_cons]

prove_correct collectDependencyVersions by
  loom_solve
  rw [depEntries_drop_step (dependencyNames.dropLast) i (by omega) (by omega)]
  simp_all
