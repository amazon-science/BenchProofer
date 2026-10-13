import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element resolution is modeled deeply
--  as an opaque total map `resolveElem` and validated element-wise against the
--  real per-element step — an A-reference, see refinement.md / mapping.md. It
--  is not pinned to any value, so no soundness is borrowed from it.)
-- axioms-end

-- pure-start
/- Two kinds of homogeneous ordered container that an input value may take when
   it is itself a sequence of sub-values. The behavior under spec turns on
   WHICH of the two kinds the input is, so the kind is a first-class tag with
   decidable equality. -/
inductive SeqKind where
  | list
  | tuple
  deriving DecidableEq, Inhabited

/- The per-element resolution of a single sub-value. It is the same map the
   operation already applied to each element before; the behavior under change
   does not touch it, so it is modeled opaquely (its concrete result is never
   relied upon — only that the SAME map is applied to every element). -/
opaque resolveElem : Int → Int

/- A sequence carrier: its kind tag together with its ordered elements. -/
structure SeqVal where
  kind : SeqKind
  elems : List Int
  deriving Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An input value that is a homogeneous ordered sequence is resolved by
   resolving each of its sub-values independently and reassembling them into a
   sequence of the SAME kind as the input. Two guarantees pin the behavior the
   issue demands:

   - the kind of the result equals the kind of the input — a sequence of one
     kind must come back as the same kind (the type of the input sequence is
     preserved, never silently changed to the other kind);
   - the elements of the result are exactly the input elements with the
     per-element resolution applied, in order (an order-preserving element-wise
     map; the count and order are unchanged).

   `value` is read-only (not `mut`); the step constructs a fresh result and
   never mutates its input (directive 5). -/
method resolveSeq (value : SeqVal) return (out : SeqVal)
  ensures out.kind = value.kind
  ensures out.elems = value.elems.map resolveElem
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: each sub-value is resolved element-wise (the
    -- elements are correct), but the result is reassembled into a FIXED kind
    -- regardless of the input kind — the container type of the input is
    -- discarded and forced to the second kind. When the input is of the first
    -- kind, the frozen spec clause `out.kind = value.kind` is violated, so
    -- prove_correct MUST fail.
    let resolvedElems := value.elems.map resolveElem
    return { kind := SeqKind.tuple, elems := resolvedElems }
    -- impl-end

prove_correct resolveSeq by
  loom_solve
