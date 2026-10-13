import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. A numeric evaluation of
-- an expression is modeled deeply below (`evalSpec`): a number evaluates to
-- itself, a bare atom has no numeric value, and an application evaluates to its
-- implementation applied to the evaluated arguments. There is no `opaque` callee
-- and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- A numeric expression tree.
* `num n`     — a concrete numeric value `n`.
* `atom`      — a bare symbol carrying no numeric value.
* `app f args`— an application of a node whose numeric implementation is `f`
  to the argument subexpressions `args`. -/
inductive Expr where
  | num  : Int → Expr
  | atom : Expr
  | app  : (List Int → Int) → List Expr → Expr

/-- Numeric evaluation of an expression.
* a number evaluates to itself;
* a bare symbol has no numeric value (`none`);
* an application evaluates to its implementation applied to the list of evaluated
  arguments — and has a numeric value exactly when every argument does, the
  arguments being evaluated by the same numeric evaluation (a structural
  recursion over the argument subexpressions). -/
def evalSpec : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => (args.attach.mapM (fun a => evalSpec a.1)).map f
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- pure-end

-- post-conditions-start
/-- The result is the numeric evaluation of the input expression: a number
evaluates to itself, a bare symbol to no value, and an application to its
implementation applied to its evaluated arguments. -/
def problem_spec_evalf (e : Expr) (result : Option Int) : Prop :=
  result = evalSpec e
-- post-conditions-end

-- impl-start
def implementation_evalf : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => Id.run do
      let mut vals : List Int := []
      for a in args.attach do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- impl-end


-- proof-start
/-- Closed form for the app-branch imperative loop started with accumulator `acc`
over the attached argument list `xs`: the `mapM` of `implementation_evalf` over the
subexpressions, threaded through `acc`.  This is the value-level target the loop is
proven equal to before the outer implementation function `f` is applied. -/
def loop_run {p : Expr → Prop} (xs : List {x : Expr // p x}) (acc : List Int) :
    Option (List Int) :=
  Option.map (fun vs => acc ++ vs) (xs.mapM (fun a => implementation_evalf a.1))

/-- The app-branch imperative `Id.run` for-loop (with early `none` short-circuit,
started at accumulator `acc`, and final `some (f vals)`) equals the closed form
`loop_run xs acc` post-composed with `f`. -/
theorem loop_eq_mapM {p : Expr → Prop} (f : List Int → Int)
    (xs : List {x : Expr // p x}) (acc : List Int) :
    (Id.run do
      let mut vals := acc
      for a in xs do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)) = (loop_run xs acc).map f := by
  induction xs generalizing acc with
  | nil => simp [loop_run, Id.run]; rfl
  | cons a as ih =>
      simp only [List.forIn_cons, loop_run, List.mapM_cons]
      cases h : implementation_evalf a.1 with
      | none => simp [Id.run]; rfl
      | some v =>
          have hih := ih (acc ++ [v])
          simp only [loop_run, Id.run] at hih ⊢
          simp at *
          rw [hih]
          cases List.mapM implementation_evalf as.unattach <;> simp

/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the
attached subexpressions using the pointwise induction hypothesis. -/
theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})
    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :
    xs.mapM (fun a => implementation_evalf a.1)
      = xs.mapM (fun a => evalSpec a.1) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)
    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=
      fun a ha => h a (by simp [ha])
    simp only [List.mapM_cons, hx, ih hxs]

theorem correct_evalf : ∀ (e : Expr),
    problem_spec_evalf e (implementation_evalf e) := by
  intro e
  show implementation_evalf e = evalSpec e
  induction e using implementation_evalf.induct with
  | case1 n => rw [implementation_evalf, evalSpec]
  | case2 => rw [implementation_evalf, evalSpec]
  | case3 f args ih =>
    rw [implementation_evalf, evalSpec]
    rw [loop_eq_mapM f args.attach []]
    rw [loop_run]
    rw [mapM_congr_eval args.attach (fun a _ => ih a)]
    simp only [List.nil_append, Option.map_map]
    rfl

-- proof-end
