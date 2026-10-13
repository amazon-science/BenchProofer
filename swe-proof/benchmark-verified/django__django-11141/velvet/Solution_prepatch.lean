import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A single application's migration source, abstracted to only the observations
   that decide whether the application is treated as carrying migrations.

   * `isPackage`    — the source is an importable package (it exposes a search
                      path over which member modules can be enumerated).
   * `isNamespace`  — the source is an implicit namespace package (it has no
                      single backing file). Carried as an observation only; the
                      classification below does NOT depend on it.
   * `migrationNames` — the migration member modules discovered under the
                      package's search path (already filtered to the migration
                      file names).
   * `ignoreMissing` — the loader is configured to keep a source that exposes no
                      migrations rather than discard it. -/
structure MigrationSource where
  isPackage : Bool
  isNamespace : Bool
  migrationNames : List String
  ignoreMissing : Bool
  deriving Inhabited

/- An application is classified as migrated exactly when its source is a package
   that either has at least one discovered migration, or the loader is told to
   keep sources with none. A source that is not a package is never migrated.
   The decision is a function of package-ness, the discovered migrations, and the
   configuration flag alone — the implicit-namespace observation does not enter
   it. -/
@[grind] def classify (m : MigrationSource) : Bool :=
  if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing) else false

/- The classification of every application, in input order. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def classifyAll : List MigrationSource → List Bool
  | []      => []
  | m :: ms => classify m :: classifyAll ms

@[grind] lemma classifyAll_nil : classifyAll [] = [] := rfl
@[grind] lemma classifyAll_cons (m : MigrationSource) (ms : List MigrationSource) :
    classifyAll (m :: ms) = classify m :: classifyAll ms := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method classifyMigrationSources (sources : List MigrationSource)
    return (out : List Bool)
  ensures out = classifyAll sources
  do
    -- impl-start
    let mut result : List Bool := []
    let mut i := sources.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ sources.length
      invariant result = classifyAll (sources.drop i)
      done_with i = 0
      decreasing i
    do
      let m := sources[i - 1]!
      -- Pre-image skeleton: an implicit namespace package (one with no single
      -- backing file) is short-circuited to NOT migrated before the discovered
      -- migrations are even considered. The frozen spec classifies purely on
      -- package-ness / discovered migrations / configuration, so a namespace
      -- package that exposes migrations diverges and prove_correct MUST fail.
      let c : Bool :=
        if m.isNamespace then false
        else if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing)
        else false
      result := c :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `classifyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma classifyAll_drop_step (sources : List MigrationSource) (i : Nat)
    (hi : 0 < i) (hle : i ≤ sources.length) :
    classifyAll (sources.drop (i - 1))
      = classify sources[i - 1]! :: classifyAll (sources.drop i) := by
  have hlt : i - 1 < sources.length := by omega
  have hcons : sources.drop (i - 1) = sources[i - 1]! :: sources.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, classifyAll_cons]

prove_correct classifyMigrationSources by
  loom_solve
  rw [classifyAll_drop_step sources i (by omega) (by omega)]
  simp_all
