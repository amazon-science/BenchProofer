import Mathlib
-- imports-end

/-!
Producing, for a stratified k-fold split, the ORDER in which each class's own
samples are arranged before they are handed out to the folds.

A stratified split treats each class independently: every class has a number of
samples, and that class's local index range is laid out in some order; a per-class
fold splitter then deals those positions out to the folds, preserving the class
balance. This file models how those per-class orders are produced from
  (a seed, whether shuffling is on, the number of folds, the per-class counts)
      ↦ the list of orders, one per class.

* When shuffling is OFF, every class keeps its natural ascending order.
* When shuffling is ON, each class's index range is shuffled. The orders are
  drawn from a SINGLE source of randomness, consumed once per class in class
  order, so that source carries forward from each class to the next. The
  intended, observable consequence is that distinct classes generally receive
  distinct orders, and two distinct seeds generally yield distinct overall
  collections of orders — rather than every class being arranged identically and
  the seed having no real effect.

Each class's index range spans `max(count, n_folds)` positions, matching the
range the per-class fold splitter operates over. The implementation and the
correctness proof are supplied separately.
-/

-- axioms-start
-- The source of randomness is an UNCHANGED routine: a seeded random generator
-- whose internal numeric behavior is irrelevant to what this file pins. We take
-- it OPAQUELY through two signatures — initialising the generator from a seed,
-- and consuming it once to obtain an order of `n` positions together with the
-- generator advanced past that draw. No property of these is asserted (no
-- `_prop` axiom is consumed); the whole point pinned here is the structural way
-- the single generator is THREADED across the classes, which holds for any such
-- generator. Behavioural agreement with the real generator is checked by G-CONF.
abbrev RngState := Nat

/-- Initialise the random generator from an integer seed. -/
opaque seedState : Nat → RngState

/-- Consume the generator once: arrange `n` positions into an order and return
that order together with the generator advanced past this draw. -/
opaque shuffleN : RngState → Nat → (List Nat × RngState)
-- axioms-end

-- pure-start
/-- The orders produced when shuffling is ON, stated front-recursively: the
single generator state `st` is threaded through the classes in order. The first
class consumes `st` (obtaining its order and the advanced state), and every later
class consumes the state left by its predecessor. -/
def perClassShuffleOrders (nFolds : Nat) : List Nat → RngState → List (List Nat)
  | [], _ => []
  | c :: cs, st =>
    let res := shuffleN st (max c nFolds)
    res.1 :: perClassShuffleOrders nFolds cs res.2
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-class orders dictated by the rule:
* shuffling OFF — each class keeps its natural ascending order over
  `max(count, n_folds)` positions;
* shuffling ON — the orders threaded from a single generator seeded by `seed`,
  consumed once per class in class order (`perClassShuffleOrders`). -/
def problem_spec_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
    (result : List (List Nat)) : Prop :=
  result =
    (if shuffle then
      perClassShuffleOrders nFolds counts (seedState seed)
     else
      counts.map (fun c => List.range (max c nFolds)))
-- post-conditions-end

-- impl-start
def implementation_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :
    List (List Nat) := Id.run do
  if !shuffle then
    return counts.map (fun c => List.range (max c nFolds))
  -- Obtain ONE generator from the seed and keep it as we go.
  let mut st : RngState := seedState seed
  let mut orders : List (List Nat) := []
  for c in counts do
    -- Shuffle this class's index range with the current generator, then carry
    -- the advanced generator forward to the next class.
    let res := shuffleN st (max c nFolds)
    orders := orders ++ [res.1]
    st := res.2
  return orders
-- impl-end


-- proof-start
theorem correct_classOrders :
    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat),
      problem_spec_classOrders seed shuffle nFolds counts
        (implementation_classOrders seed shuffle nFolds counts) := by
  intro seed shuffle nFolds counts
  unfold problem_spec_classOrders implementation_classOrders
  cases shuffle
  · simp only [Id.run]; rfl
  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
    -- goal: the forIn loop equals perClassShuffleOrders
    -- generalize the accumulator and state
    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
          (fun c r =>
            (do
              pure PUnit.unit
              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
          = acc ++ perClassShuffleOrders nFolds cs st by
      have := h counts (seedState seed) []
      simpa using this
    intro cs
    induction cs with
    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
    | cons c cs ih =>
      intro st acc
      simp only [List.forIn_cons, perClassShuffleOrders]
      simp only [bind_pure_comp, map_pure, pure_bind] at *
      rw [ih]
      simp [List.append_assoc]

/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
EXACT equality to a total function of the inputs, so ANY result satisfying it
equals `implementation_classOrders`. Consequently no observably wrong same-spec
implementation can verify — a same-spec implementation whose `correct_` closes
is extensionally the gold (threaded-generator) behavior. In particular a
gold-equivalent restatement of the implementation (e.g. one returning the
spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
counterexample: its faithful refined patch is the gold patch and resolves. -/
theorem spec_classOrders_deterministic :
    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
      (r : List (List Nat)),
      problem_spec_classOrders seed shuffle nFolds counts r →
        r = implementation_classOrders seed shuffle nFolds counts := by
  intro seed shuffle nFolds counts r h
  have h2 := correct_classOrders seed shuffle nFolds counts
  unfold problem_spec_classOrders at h h2
  rw [h, h2]

-- proof-end
