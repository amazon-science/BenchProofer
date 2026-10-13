import Mathlib
-- imports-end

/-!
Turning the outcome of scanning a path against a route pattern into the data a
caller consumes: the leftover path, the positional captures, and the named
captures.

Scanning either succeeds or fails. On failure there is no outcome at all. On
success the scan exposes three things:

  * how far into the path it reached (the length of the consumed prefix);
  * the NAMED captures, in declaration order, each paired with an OPTIONAL value
    — a named capture whose segment is OPTIONAL and did not participate in the
    scan carries no value (it is absent), while one that did participate carries
    the captured text;
  * the POSITIONAL captures, each likewise an optional value.

The data handed back is built like this:

  * the leftover path is the portion of the path beyond the consumed prefix;
  * the named-capture mapping lists, in order, exactly the named captures that
    actually carry a value — an absent named capture contributes nothing;
  * the positional captures are reported only when the named-capture mapping is
    empty; when at least one named capture carries a value, no positional
    captures are reported.

So an absent optional named capture neither appears in the named mapping nor
contributes a stray entry: it is simply not there.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The scan itself
-- (pattern search over the path) is taken as already performed: its outcome —
-- consumed length, named captures with their optional values, and positional
-- captures — is supplied as input data (`ScanOutcome`). The logic modeled here
-- only reshapes that data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The outcome of a successful scan of a path against a route pattern.
* `consumed` — the length of the prefix the scan reached (so the leftover path is
  everything beyond it);
* `namedCaptures` — the named captures in declaration order; each is a name
  (modeled as a `Nat` identity — mapping.md gives the name↔`Nat` bijection) paired
  with an OPTIONAL value (`none` when that capture did not participate);
* `positionalCaptures` — the positional captures, each an optional value. -/
structure ScanOutcome (V : Type) where
  consumed : Nat
  namedCaptures : List (Nat × Option V)
  positionalCaptures : List (Option V)

/-- Whether a named capture carries a value (it participated in the scan). -/
def carriesValue {V : Type} (entry : Nat × Option V) : Bool :=
  entry.2.isSome
-- pure-end

-- post-conditions-start
/-- On a failed scan there is no outcome. On a successful scan the result is the
triple of: the leftover path (everything beyond the consumed prefix), the
positional captures (reported only when the named mapping is empty), and the
named mapping (exactly the named captures that carry a value, in order). Every
component is pinned to the input: nothing is invented, reordered, or left
unconstrained, and absent named captures contribute no entry. -/
def problem_spec_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V))
    (result : Option (List Char × List (Option V) × List (Nat × Option V))) : Prop :=
  outcome.elim
    (result = none)
    (fun sc =>
      let named := sc.namedCaptures.filter carriesValue
      let positional := if named.isEmpty then sc.positionalCaptures else []
      result = some (path.drop sc.consumed, positional, named))
-- post-conditions-end

-- impl-start
def implementation_capture {V : Type}
    (path : List Char) (outcome : Option (ScanOutcome V)) :
    Option (List Char × List (Option V) × List (Nat × Option V)) := Id.run do
  let some sc := outcome | return none
  -- The named mapping is taken to be every named capture the scan exposes,
  -- including those that carry no value; an absent optional named capture is
  -- therefore still listed (with its empty value).
  let mut named : List (Nat × Option V) := []
  for entry in sc.namedCaptures do
    named := named ++ [entry]
  let positional := if named.isEmpty then sc.positionalCaptures else []
  return some (path.drop sc.consumed, positional, named)
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: when a named capture is absent, the spec drops it from
-- the mapping (and may then report positional captures), while this impl keeps it
-- — so the desugared loop no longer matches the spec's `filter carriesValue` on
-- the discriminating clause (an outcome with an absent optional named capture).
theorem capture_named_eq {V : Type} (xs : List (Nat × Option V))
    (init : List (Nat × Option V)) :
    (Id.run (forIn xs init (fun entry r =>
        (if carriesValue entry = true then ForInStep.yield (r ++ [entry])
         else ForInStep.yield r : Id (ForInStep (List (Nat × Option V)))))))
    = init ++ xs.filter carriesValue := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.filter_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : carriesValue a = true
    · simp only [h, if_true, ih]
      rw [List.append_assoc, List.singleton_append]
    · simp only [h, Bool.false_eq_true, if_false, ih]

theorem correct_capture {V : Type} :
    ∀ (path : List Char) (outcome : Option (ScanOutcome V)),
      problem_spec_capture path outcome
        (implementation_capture path outcome) := by
  intro path outcome
  unfold problem_spec_capture implementation_capture
  cases outcome with
  | none => rfl
  | some sc =>
    simp only [Option.elim]
    rw [show (Id.run (do
          let mut named := ([] : List (Nat × Option V))
          for entry in sc.namedCaptures do
            if carriesValue entry = true then named := named ++ [entry]
          let positional := if named.isEmpty then sc.positionalCaptures else []
          pure (some (path.drop sc.consumed, positional, named))))
        = (let named := Id.run (forIn sc.namedCaptures ([] : List (Nat × Option V))
              fun entry r =>
                (if carriesValue entry = true then ForInStep.yield (r ++ [entry])
                 else ForInStep.yield r : Id (ForInStep (List (Nat × Option V)))));
           let positional := if named.isEmpty then sc.positionalCaptures else []
           some (path.drop sc.consumed, positional, named)) from rfl]
    rw [capture_named_eq]
    simp
-- proof-end
