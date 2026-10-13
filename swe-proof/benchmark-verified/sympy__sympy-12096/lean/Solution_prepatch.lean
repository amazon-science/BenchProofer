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
      -- pre-patch behavior: the arguments are taken as-is, without first being
      -- numerically evaluated; a value is obtained only from arguments that are
      -- already concrete numbers, and any non-numeric argument aborts.
      let mut vals : List Int := []
      for a in args do
        match a with
        | .num v => vals := vals ++ [v]
        | _      => return none
      return some (f vals)
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` accumulation, generalized over the
accumulator, equals the post-mapped `mapM` of the per-argument evaluation. -/
theorem loop_lemma {β : Type} (g : β → Option Int) (f : List Int → Int) :
    ∀ (l : List β) (acc : List Int),
      (Id.run do
        let mut vals := acc
        for a in l do
          match g a with
          | some v => vals := vals ++ [v]
          | none   => return none
        return some (f vals))
      = (l.mapM g).map (fun vs => f (acc ++ vs)) := by
  intro l
  induction l with
  | nil => intro acc; simp [Id.run]; rfl
  | cons x xs ih =>
    intro acc
    simp only [Id.run, List.forIn_cons, bind, pure] at ih ⊢
    cases hx : g x with
    | none => simp [hx, List.mapM_cons]
    | some v =>
      simp only [hx]
      rw [ih (acc ++ [v])]
      simp only [List.mapM_cons, hx]
      cases hxs : xs.mapM g with
      | none => simp
      | some vs => simp [List.append_assoc]

theorem impl_app (f : List Int → Int) (args : List Expr) :
    implementation_evalf (.app f args)
      = (args.attach.mapM (fun a => implementation_evalf a.1)).map f := by
  rw [implementation_evalf]
  have h := loop_lemma (fun a : {x // x ∈ args} => implementation_evalf a.1) f args.attach []
  simpa using h

theorem Expr.myrec (motive : Expr → Prop)
    (hnum : ∀ n, motive (.num n)) (hatom : motive .atom)
    (happ : ∀ f args, (∀ a ∈ args, motive a) → motive (.app f args)) :
    ∀ e, motive e :=
  Expr.rec (motive_1 := motive) (motive_2 := fun args => ∀ a ∈ args, motive a)
    hnum hatom (fun f args ih => happ f args ih)
    (by intro a ha; simp at ha)
    (fun x xs ihx ihxs => by
      intro a ha
      rcases List.mem_cons.mp ha with rfl | hmem
      · exact ihx
      · exact ihxs a hmem)

theorem correct_evalf : ∀ (e : Expr),
    problem_spec_evalf e (implementation_evalf e) := by
  intro e
  unfold problem_spec_evalf
  induction e using Expr.myrec with
  | hnum n => rw [implementation_evalf, evalSpec]
  | hatom => rw [implementation_evalf, evalSpec]
  | happ f args ih =>
    rw [impl_app, evalSpec]
    congr 1
    rw [List.mapM_subtype (g := implementation_evalf) (fun _ _ => rfl),
        List.mapM_subtype (g := evalSpec) (fun _ _ => rfl)]
    simp only [List.unattach_attach]
    induction args with
    | nil => rfl
    | cons x xs ihl =>
      simp only [List.mapM_cons]
      rw [ih x (List.mem_cons_self ..)]
      rw [ihl (fun a ha => ih a (List.mem_cons_of_mem _ ha))]
-- proof-end
