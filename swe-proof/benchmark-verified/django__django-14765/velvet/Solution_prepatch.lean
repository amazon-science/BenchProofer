import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The only
   sub-steps that are not pinned here are the two PRIMITIVE tests the construction
   performs on the optional argument — "is it absent?" and "is it already a set?".
   Their combined outcome partitions the argument into three mutually-exclusive
   shapes, modeled as a FREE input (`SetArg`, see the method signature): the
   postconditions hold for EVERY value of it, so it is owed no contract — strictly
   weaker than any concrete test (directive 7). The behaviour this bundle pins —
   how each shape becomes the stored collection, and that an argument which is
   neither absent nor already a set is REJECTED rather than silently coerced — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The shape of the optional collection argument, in the three mutually-exclusive
   forms the construction reacts to:
     * `absent`        — no value was supplied (the caller omitted it);
     * `alreadySet xs` — a value was supplied and it is ALREADY a set, whose
                         members are `xs`;
     * `coercible ys`  — a value was supplied that is NOT a set but could be
                         iterated into one whose members would be `ys`.
   These three cases are genuinely different arguments and must stay apart: only
   the test "absent?" and the test "already a set?" distinguish them. -/
inductive SetArg where
  | absent
  | alreadySet (xs : List String)
  | coercible (ys : List String)
  deriving DecidableEq, Inhabited

/- A failure the desired behaviour is REQUIRED to produce: a supplied argument
   that is not already a set is rejected outright (the construction refuses to
   accept it) rather than being quietly turned into one. Carried by
   `Except.error`; a successful construction carries the stored collection in
   `Except.ok`. -/
inductive InitErr where
  | rejected
  deriving DecidableEq, Inhabited

/- The desired stored collection (or rejection) as a function of the argument's
   shape:
     * an absent argument stores the EMPTY collection — the construction supplies
       its own default;
     * an argument that is already a set is stored AS-IS — its members are kept
       exactly and nothing is recomputed;
     * an argument that is not already a set is REJECTED (`Except.error`) — the
       construction will not silently coerce it.
   The result is grounded entirely in the argument: the stored members on the
   accepting branch are exactly the argument's own members (directive 8). -/
def normalizeSpec (a : SetArg) : Except InitErr (List String) :=
  match a with
  | .absent        => Except.ok []
  | .alreadySet xs => Except.ok xs
  | .coercible _   => Except.error .rejected

@[grind] lemma normalizeSpec_absent :
    normalizeSpec .absent = Except.ok [] := rfl
@[grind] lemma normalizeSpec_alreadySet (xs : List String) :
    normalizeSpec (.alreadySet xs) = Except.ok xs := rfl
@[grind] lemma normalizeSpec_coercible (ys : List String) :
    normalizeSpec (.coercible ys) = Except.error .rejected := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize the optional set-typed argument a registry-style object stores at
   construction. `arg` is the read-only shape of that argument (not `mut`); the
   construction builds the stored collection and mutates nothing else
   (directive 5). Desired behaviour:
     * an absent argument is replaced by the empty collection — a sensible
       default the construction supplies itself;
     * an argument that is already a set is stored exactly as given — its members
       are preserved and nothing is recomputed;
     * an argument that is neither absent nor already a set is REJECTED rather
       than silently turned into a set — callers are required to pass a set when
       they pass anything at all.
   In particular a non-set argument must NOT be accepted: the result is an error,
   never a successfully-stored coerced collection. -/
method normalizeSetArg (arg : SetArg)
    return (out : Except InitErr (List String))
  ensures out = normalizeSpec arg
  ensures arg = .absent → out = Except.ok []
  ensures ∀ xs, arg = .alreadySet xs → out = Except.ok xs
  ensures ∀ ys, arg = .coercible ys → out = Except.error .rejected
  do
    -- impl-start
    -- Pre-image skeleton: a supplied argument that is not already a set is
    -- quietly TURNED INTO one (its members iterated into a fresh set and stored,
    -- `Except.ok ys`) instead of being rejected. The frozen spec requires such an
    -- argument to be refused (`Except.error .rejected`), so prove_correct MUST
    -- fail on the `coercible` branch.
    let result : Except InitErr (List String) :=
      match arg with
      | .absent        => Except.ok []
      | .alreadySet xs => Except.ok xs
      | .coercible ys  => Except.ok ys
    return result
    -- impl-end

prove_correct normalizeSetArg by
  loom_solve
  cases arg <;> simp_all
