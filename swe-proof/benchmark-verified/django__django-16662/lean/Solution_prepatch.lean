import Mathlib
-- imports-end

/-!
Ordering the import statements that head a generated source file.

A generated module begins with a block of import statements. Each statement is
either a plain module import (`import <module>`) or a selective import that
pulls named objects out of a module (`from <module> import <objects>`). The
generator collects these statements and must emit them in a canonical order.

The desired order follows the conventional sectioning of import blocks:

  * every plain module-import statement comes before every selective
    `from ... import ...` statement;
  * within each of those two groups the statements are ordered by the name of
    the module being imported (the token immediately following the leading
    keyword);
  * the same statements are emitted — none added, none dropped, none
    duplicated — only rearranged.

Each statement is carried as its textual line. `firstToken` is the leading
keyword (`import` or `from`); `moduleName` is the following whitespace-delimited
token, i.e. the module a statement refers to. A statement is a selective import
exactly when its leading keyword is `from`.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each import
-- statement is carried as plain textual data; the leading keyword and the
-- module token are extracted by whitespace splitting, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The leading whitespace-delimited token of a statement line (its keyword,
`import` or `from`). -/
def firstToken (line : String) : String := (line.splitOn " ").headD ""

/-- The module token of a statement line: the whitespace-delimited token that
immediately follows the leading keyword (the module being imported). -/
def moduleName (line : String) : String := (line.splitOn " ").getD 1 ""

/-- A statement is a selective import exactly when its leading keyword is
`from`. -/
def isFromStatement (line : String) : Bool := firstToken line == "from"

/-- The canonical ordering on statement lines: plain module imports precede
selective `from ... import ...` statements, and within each group the order is
by module name.

`importLe a b` holds when `a` may appear no later than `b`:

  * a plain import precedes any selective import;
  * a selective import never precedes a plain import;
  * two statements of the same kind are ordered by their module name. -/
def importLe (a b : String) : Bool :=
  match isFromStatement a, isFromStatement b with
  | false, true  => true
  | true,  false => false
  | _,     _     => decide (moduleName a ≤ moduleName b)
-- pure-end

-- post-conditions-start
/-- The emitted statements are exactly the input statements rearranged into the
canonical order:

  * `result` is a permutation of `imports` — the same multiset of statement
    lines, nothing added, dropped, or duplicated (frame: the content is pinned
    to the input);
  * `result` is sorted by `importLe` — consecutively, and hence (because
    `importLe` is a total preorder) globally: every plain import precedes every
    selective import, and within each group statements are by module name.

Together these pin the output for every input. -/
def problem_spec_sortImportStatements (imports result : List String) : Prop :=
  List.Perm result imports ∧ result.Pairwise (fun a b => importLe a b = true)
-- post-conditions-end

-- impl-start
def implementation_sortImportStatements (imports : List String) : List String :=
  Id.run do
    let mut sortedStatements := imports
    sortedStatements := sortedStatements.mergeSort (fun a b => decide (moduleName a ≤ moduleName b))
    return sortedStatements
-- impl-end

-- proof-start
theorem importLe_trans : ∀ a b c : String, importLe a b → importLe b c → importLe a c := by
  intro a b c hab hbc; unfold importLe at *
  rcases hf : isFromStatement a <;> rcases hg : isFromStatement b <;> rcases hh : isFromStatement c <;>
    simp_all <;> exact le_trans hab hbc

theorem importLe_total : ∀ a b : String, (importLe a b || importLe b a) = true := by
  intro a b; unfold importLe
  rcases hf : isFromStatement a <;> rcases hg : isFromStatement b <;> simp <;>
    rcases le_total (moduleName a) (moduleName b) with h|h <;> simp_all

theorem correct_sortImportStatements :
    ∀ imports : List String,
      problem_spec_sortImportStatements imports
        (implementation_sortImportStatements imports) := by
  intro imports
  unfold problem_spec_sortImportStatements implementation_sortImportStatements
  simp only [Id.run, pure]
  exact ⟨List.mergeSort_perm imports importLe,
         List.sorted_mergeSort importLe_trans importLe_total imports⟩
-- proof-end
