import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged foreign callee is axiomatized for this bundle. The optimization
   under spec is a pure data-flow over the operations' configuration (a name
   comparison plus a field-by-field reassembly), modeled directly below. There
   is therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A model-creation operation, carrying only the configuration the optimization
   reads or reproduces:
   * `nameLower` — the model's case-folded name (two operations concern the same
                   model iff their case-folded names are equal);
   * `fields`, `options`, `bases`, `managers` — the four independent components
                   of the created model. Their concrete element shapes are
                   immaterial to the optimization (mapping.md §2); only their
                   preservation/replacement under the collapse is observed. -/
structure ModelCreate where
  nameLower : String
  fields    : List Nat
  options   : List (String × Nat)
  bases     : List Nat
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- A manager-alteration operation: it names a model (`nameLower`) and supplies a
   new set of `managers` for it. -/
structure AlterManagers where
  nameLower : String
  managers  : List (String × Nat)
deriving DecidableEq, Inhabited, Repr

/- The outcome of attempting to optimize a creation against a following
   operation, mirroring the three shapes the optimizer's reducer may report:
   * `replace ops` — the two operations collapse into `ops`;
   * `cannotReduce` — the two operations cannot be combined and must both stand;
   * `reduceThrough` — the following operation is independent of this model and
                       the optimizer may freely reorder across it. -/
inductive ReduceResult where
  | replace (ops : List ModelCreate)
  | cannotReduce
  | reduceThrough
deriving DecidableEq, Inhabited, Repr

/- The desired optimization of a model-creation immediately followed by a
   manager-alteration. When both concern the SAME model (equal case-folded
   names) the pair collapses into a single creation that is byte-for-byte the
   original creation EXCEPT that its managers are taken from the alteration —
   the original fields, options and bases are carried through unchanged. When
   the alteration concerns a DIFFERENT model it is independent of this creation,
   so the optimizer may reorder across it (`reduceThrough`). -/
def reduceManagersSpec (self : ModelCreate) (op : AlterManagers) : ReduceResult :=
  if self.nameLower = op.nameLower then
    ReduceResult.replace [{ self with managers := op.managers }]
  else
    ReduceResult.reduceThrough
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; the optimization is total over its inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Optimize a model-creation `self` immediately followed by a manager-alteration
   `op`. The result is determined by `reduceManagersSpec`: a same-model alteration
   collapses into a single creation carrying the altered managers (and the
   creation's original fields, options and bases); a different-model alteration
   is reported as independent (`reduceThrough`).

   `self` and `op` are read-only (neither is `mut`): the step constructs a fresh
   creation and never mutates its inputs (directive 5). -/
method reduceManagers (self : ModelCreate) (op : AlterManagers) return (res : ReduceResult)
  ensures res = reduceManagersSpec self op
  do
    -- impl-start
    if self.nameLower = op.nameLower then
      return ReduceResult.replace [{ self with managers := op.managers }]
    else
      return ReduceResult.reduceThrough
    -- impl-end

prove_correct reduceManagers by
  loom_solve <;> simp_all [reduceManagersSpec]
