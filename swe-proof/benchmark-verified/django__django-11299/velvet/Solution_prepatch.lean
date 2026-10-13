import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only operation that varies with the column-form
--  selection is which column-reference form a single leaf condition receives;
--  that choice is governed ENTIRELY by the column-form selector and is modeled
--  DEEPLY and concretely here (`formOf` / `columnForms`) rather than behind an
--  opaque oracle. Because that deep model stands in for a real, unchanged
--  column-reference operation, its fidelity is checked against that operation
--  by an out-of-band soundness harness; nothing is asserted on faith. The
--  surrounding per-leaf
--  resolution machinery is UNCHANGED and irrelevant to the modeled behavior, so
--  it is abstracted to the resulting column form — a structural value.)
-- axioms-end

-- pure-start
/- The two forms a column reference inside an assembled condition can take: the
   `bare` (unqualified) form, or the table-`qualified` form. Which one a leaf
   condition receives is determined solely by the selector in force when that
   leaf is assembled. -/
inductive ColForm where
  | bare
  | qualified
  deriving DecidableEq, Inhabited

/- A condition as handed to the assembler: either a single leaf condition
   (`atom`), or a nested boolean group of further conditions (`group`). The
   top-level object is always a group; its members may themselves be groups,
   to arbitrary depth. -/
inductive Cond where
  | atom : Cond
  | group : List Cond → Cond
  deriving Inhabited

/- An assembled condition: each leaf now carries the column-reference form it was
   given; the grouping structure is preserved. -/
inductive ResolvedCond where
  | atom : ColForm → ResolvedCond
  | group : List ResolvedCond → ResolvedCond
  deriving Inhabited

/- The column form a leaf receives under a selector: the `bare` (unqualified)
   form exactly when the selector is set, otherwise the `qualified` form. -/
def formOf (bare : Bool) : ColForm :=
  if bare then ColForm.bare else ColForm.qualified

/- The deep model of assembling a forest of conditions under a single selector:
   every leaf — at any nesting depth — receives the column form `formOf bare`,
   and every nested group is assembled under the SAME selector (the selector is
   threaded unchanged into nested groups). Written front-recursively (mutually
   over the forest) so a single unfold is available per recursion step. -/
mutual
def columnForm (bare : Bool) : Cond → ResolvedCond
  | .atom     => ResolvedCond.atom (formOf bare)
  | .group cs => ResolvedCond.group (columnForms bare cs)
def columnForms (bare : Bool) : List Cond → List ResolvedCond
  | []      => []
  | c :: cs => columnForm bare c :: columnForms bare cs
end

@[grind] lemma columnForms_nil (b : Bool) : columnForms b [] = [] := rfl
@[grind] lemma columnForms_cons (b : Bool) (c : Cond) (cs : List Cond) :
    columnForms b (c :: cs) = columnForm b c :: columnForms b cs := rfl
@[grind] lemma columnForm_atom (b : Bool) :
    columnForm b .atom = ResolvedCond.atom (formOf b) := rfl
@[grind] lemma columnForm_group (b : Bool) (cs : List Cond) :
    columnForm b (.group cs) = ResolvedCond.group (columnForms b cs) := rfl

/- Arithmetic fact discharging the structural-recursion measure for descent into
   a group member: the member forest is strictly smaller than the whole forest.
   Content-neutral; supplied so the recursive assembler's termination and the
   correctness proof close automatically. -/
@[simp] lemma sizeOf_group_member (inner rest : List Cond) :
    sizeOf inner < 1 + (1 + sizeOf inner) + sizeOf rest := by omega
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble a forest of conditions, giving every leaf condition a column
   reference and preserving the grouping structure. The column-form selector
   `bare` chosen at the top level must reach EVERY leaf, including those inside
   nested groups: a leaf is given `formOf bare`, and descent into a nested group
   carries the SAME selector. `bare` and `conds` are read-only (directive 5);
   the assembler mutates nothing it is handed. -/
method assignColumnForms (bare : Bool) (conds : List Cond) return (result : List ResolvedCond)
  ensures result = columnForms bare conds
  do
    -- impl-start
    match conds with
    | [] => return []
    | .atom :: rest =>
      let tailR ← assignColumnForms bare rest
      return (ResolvedCond.atom (formOf bare)) :: tailR
    | .group inner :: rest =>
      let innerR ← assignColumnForms false inner  -- BUG: selector dropped on nested-group descent (defaults off)
      let tailR ← assignColumnForms bare rest
      return (ResolvedCond.group innerR) :: tailR
    -- impl-end
  termination_by sizeOf conds
  decreasing_by
    all_goals (try simp_wf)
    all_goals omega

prove_correct assignColumnForms
termination_by sizeOf conds
decreasing_by
  all_goals (try simp_wf)
  all_goals omega
by
  loom_solve
