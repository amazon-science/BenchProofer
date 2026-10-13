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
  let mut named : List (Nat × Option V) := []
  for entry in sc.namedCaptures do
    if carriesValue entry then
      named := named ++ [entry]
  let positional := if named.isEmpty then sc.positionalCaptures else []
  return some (path.drop sc.consumed, positional, named)
-- impl-end

-- proof-start
/-- The `forIn`/`mut` loop in `implementation_capture` appends each entry that
`carriesValue` to the accumulator, in order, leaving the rest untouched. So the
whole loop equals the initial accumulator followed by `xs.filter carriesValue`.
Generalized over the accumulator so the cons step's induction hypothesis applies
to the extended accumulator. -/
theorem capture_loop {V : Type} (xs : List (Nat × Option V))
    (init : List (Nat × Option V)) :
    (forIn (m := Id) xs init (fun entry r =>
      (if carriesValue entry then pure (ForInStep.yield (r ++ [entry]))
       else pure (ForInStep.yield r))))
      = init ++ xs.filter carriesValue := by
  induction xs generalizing init with
  | nil => rw [List.forIn_nil, List.filter_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    by_cases h : carriesValue a <;> simp only [h, if_true, ih, List.filter_cons]
    · simp
    · simp

theorem correct_capture {V : Type} :
    ∀ (path : List Char) (outcome : Option (ScanOutcome V)),
      problem_spec_capture path outcome
        (implementation_capture path outcome) := by
  intro path outcome
  unfold problem_spec_capture implementation_capture
  cases outcome with
  | none => rfl
  | some sc =>
    -- The desugared loop body bridges to `capture_loop`'s clean body after
    -- `simp only [bind]`; rewriting it leaves `init = [] ++ filter …` to settle.
    simp only [Option.elim, Id.run, bind, capture_loop]
    rfl
-- proof-end
