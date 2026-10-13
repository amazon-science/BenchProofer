import Mathlib
-- imports-end

/-!
Resolving a lookup value to its canonical form.

A lookup value is one of four shapes:

  * an *expression* — a value that knows how to resolve itself in the current
    context; resolving the lookup value means asking it to resolve and taking
    the resolved result;
  * a *scalar leaf* — an ordinary value that carries no resolution behavior; it
    resolves to itself, unchanged;
  * an ordered *list* of lookup values;
  * an ordered *tuple* of lookup values.

For a collection (a list or a tuple), the result is a collection OF THE SAME KIND
whose entries are the element-wise resolutions of the original entries, taken in
order. A list resolves to a list and a tuple resolves to a tuple; the arity and
order of the entries are preserved, and each entry — including an entry that is
itself a nested collection or an expression — is resolved by the very same rule.
-/

-- axioms-start
/-- A lookup value: an expression (identified by an opaque tag), a scalar leaf
(an opaque identity), a list of lookup values, or a tuple of lookup values. The
two collection constructors are distinct so the *kind* of collection (list vs
tuple) is part of the value. -/
inductive LV where
  | expr  : Nat → LV
  | plain : Nat → LV
  | lst   : List LV → LV
  | tup   : List LV → LV
  deriving Inhabited

-- Resolving an expression to its canonical form is delegated to a context-driven
-- resolver. Its result is a deterministic function of the expression's identity;
-- the resolution logic here never inspects that result (it returns it, or stores
-- it as a collection entry), so no property of the resolver is consumed — the
-- spec and the implementation invoke it identically. The proof agent adds a
-- `_prop` axiom only if a property is later required.
opaque resolveExpression : Nat → LV
-- axioms-end

-- pure-start
/-- The canonical resolution of a lookup value (the structural "what"):
* an expression resolves via the context resolver;
* a scalar leaf resolves to itself;
* a list resolves to the list of element-wise resolutions (still a list);
* a tuple resolves to the tuple of element-wise resolutions (still a tuple).
Order and arity of collection entries are preserved, and resolution recurses
into nested entries. -/
def resolveSpec : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => LV.lst (xs.map resolveSpec)
  | LV.tup xs  => LV.tup (xs.map resolveSpec)
-- pure-end

-- post-conditions-start
/-- The result is exactly the canonical resolution of the input lookup value.
This pins every component: the kind of the result (expression/scalar/list/tuple)
is the kind dictated by the input, a collection result has the same kind, arity
and order as the input collection, and each entry is the resolution of the
corresponding input entry. Nothing is left unconstrained and no entry's kind may
drift from its input. -/
def problem_spec_resolveLookupValue (value : LV) (result : LV) : Prop :=
  result = resolveSpec value
-- post-conditions-end

-- impl-start
/-- Resolve a lookup value. Expressions are resolved by the context resolver;
scalar leaves are returned unchanged; a list/tuple is rebuilt as a collection of
the SAME kind, walking its entries in order and resolving each one recursively. -/
def implementation_resolveLookupValue : LV → LV
  | LV.expr e  => resolveExpression e
  | LV.plain n => LV.plain n
  | LV.lst xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.lst resolved
  | LV.tup xs  => Id.run do
      let mut resolved : List LV := []
      for sub in xs do
        resolved := resolved ++ [implementation_resolveLookupValue sub]
      return LV.tup resolved
-- impl-end

-- proof-start
/-- The loop `for sub in xs do resolved := resolved ++ [f sub]; return g resolved`
desugars to `g (init ++ xs.map f)`. Generalized over the accumulator `init` and the
final wrapper `g` (so it covers both the `LV.lst`/`LV.tup` return forms). -/
theorem resolveLookupValue_loop_map
    (g : List LV → LV) (f : LV → LV) (xs : List LV) (init : List LV) :
    (Id.run do
      let mut resolved : List LV := init
      for sub in xs do
        resolved := resolved ++ [f sub]
      return g resolved) = g (init ++ xs.map f) := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, bind, pure, List.map_nil, List.append_nil]
  | cons a as ih =>
      simp only [List.forIn_cons, Id.run, bind, pure] at ih ⊢
      simp only [ih]
      simp

theorem correct_resolveLookupValue :
    ∀ (value : LV),
      problem_spec_resolveLookupValue value
        (implementation_resolveLookupValue value) := by
  intro value
  unfold problem_spec_resolveLookupValue
  -- Structural induction on `LV` with a list motive (`motive_2`) carrying the
  -- element-wise IH for the collection cases.
  refine @LV.rec
    (fun v => implementation_resolveLookupValue v = resolveSpec v)
    (fun xs => xs.map implementation_resolveLookupValue = xs.map resolveSpec)
    ?_ ?_ ?_ ?_ ?_ ?_ value
  · intro e; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro n; simp only [implementation_resolveLookupValue, resolveSpec]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec,
      resolveLookupValue_loop_map, List.nil_append]
    rw [ih]
  · intro xs ih
    simp only [implementation_resolveLookupValue, resolveSpec,
      resolveLookupValue_loop_map, List.nil_append]
    rw [ih]
  · rfl
  · intro head tail ih_head ih_tail
    simp only [List.map_cons, ih_head, ih_tail]
-- proof-end
