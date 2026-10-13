import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-argument transformation is modeled
--  deeply: an already-resolved argument is carried through unchanged, and a
--  freshly-built argument's dimension metadata is the spelled-out extent map.
--  Nothing is borrowed from an opaque oracle — every observable is computed
--  from the inputs. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- The dimension metadata of a typed argument: for each axis it records the
   inclusive index bounds `(lower, upper)`. An empty list means the argument
   carries no dimension metadata (a plain scalar); a non-empty list means the
   argument is array-like and must be passed by reference downstream. -/
structure Arg where
  bounds : List (Int × Int)
  deriving Inhabited, DecidableEq

/- A request for one positional argument of the generated function. It records:
   - `alreadyResolved` : whether an argument with this name was already built
     while scanning the expression (in which case its prior form is reused
     verbatim — its metadata was determined there and is not recomputed here);
   - `prior` : that already-built argument (meaningful only when resolved);
   - `arrayLike` : whether the requested symbol is an array-like quantity
     (one that owns a shape), as opposed to a plain scalar;
   - `extents` : the per-axis extents of an array-like symbol (its shape). -/
structure ArgSpec where
  alreadyResolved : Bool
  prior : Arg
  arrayLike : Bool
  extents : List Int
  deriving Inhabited

/- The dimension metadata for an array-like symbol of the given extents: each
   axis `d` becomes the inclusive bound pair `(0, d - 1)`. -/
def extentBounds (extents : List Int) : List (Int × Int) :=
  extents.map (fun d => (0, d - 1))

/- The argument produced for a single request. An already-resolved request
   reuses its prior argument unchanged. A request that must be built fresh is
   array-like ⇒ it carries its extent-derived dimension metadata; otherwise it
   carries none. The behaviour the issue turns on: a freshly-built array-like
   argument must receive dimension metadata (so it is later emitted by
   reference), NOT be left with empty metadata. -/
def argFor (e : ArgSpec) : Arg :=
  if e.alreadyResolved then e.prior
  else { bounds := if e.arrayLike then extentBounds e.extents else [] }

/- The full positional argument list: each request mapped to its argument, in
   order. Front-recursive so a single unfold is available per loop step (the
   Velvet backward-fold pattern). -/
def argList : List ArgSpec → List Arg
  | []      => []
  | e :: es => argFor e :: argList es

@[grind] lemma argList_nil : argList [] = [] := rfl

@[grind] lemma argList_cons (e : ArgSpec) (es : List ArgSpec) :
    argList (e :: es) = argFor e :: argList es := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the generated function's positional argument list from the requested
   sequence.
   The result is exactly the per-request argument map, in the requested order:
   the count and order of the requested sequence are preserved, and each request
   yields its argument under `argFor`. `requests` is read-only (not `mut`); the
   loop constructs a fresh result and never mutates its input (directive 5). -/
method buildArgList (requests : List ArgSpec) return (out : List Arg)
  ensures out = argList requests
  do
    -- impl-start
    let mut result : List Arg := []
    let mut i := requests.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requests.length
      invariant result = argList (requests.drop i)
      done_with i = 0
      decreasing i
    do
      let e := requests[i - 1]!
      result := argFor e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer request exposes the request at
   `i-1` on the front, so `argList` peels one `argFor`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma argList_drop_step (requests : List ArgSpec) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requests.length) :
    argList (requests.drop (i - 1)) = argFor requests[i - 1]! :: argList (requests.drop i) := by
  have hlt : i - 1 < requests.length := by omega
  have hcons : requests.drop (i - 1) = requests[i - 1]! :: requests.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, argList_cons]

prove_correct buildArgList by
  loom_solve
  rw [argList_drop_step requests i (by omega) (by omega)]
  simp_all
