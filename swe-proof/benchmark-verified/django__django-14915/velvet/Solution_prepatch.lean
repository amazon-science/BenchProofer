import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The standard hashing of the underlying wrapped value. This is an UNCHANGED
   library operation the object defers to when asked for its own hash; it is
   left OPAQUE (a free function of the wrapped value) — nothing is claimed about
   which concrete integers it produces, only that it is a deterministic function
   of the value it is given. Provenance: mapping.md. Because it is a free
   function with no asserted `ensures`, there is nothing to validate against the
   real callee (no axiom_check.py — meta.json G-AX skip). It must be `opaque`
   (not `axiom`) because it is referenced inside the executable `do` block. -/
opaque valueHash : Int → Int
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A lightweight wrapper object carries a single underlying value alongside some
   companion data. The desired behavior: the wrapper participates as a key in
   keyed/uniqued containers, and to do so it must expose a hash that is fully
   DETERMINED BY its underlying value. Concretely, asking the wrapper for its
   hash yields exactly the hash of the value it wraps. This makes any two
   wrappers carrying the same underlying value indistinguishable to a
   container's keying logic (they hash alike), which is precisely the
   consistency a value-based equality demands.

   `value` is the read-only underlying value (not `mut`); the routine computes a
   single hash and mutates nothing (directive 5). The underlying value is
   modeled as `Int`; its hash is deferred to as an opaque function of that value
   (a free function); the result is exactly that hash. -/
method choiceValueHash (value : Int) return (h : Int)
  ensures h = valueHash value
  do
    -- impl-start
    -- Pre-image: the wrapper exposed NO hash determined by its underlying value
    -- (the value-based hash was absent / inconsistent with the wrapped value).
    -- This skeleton returns a constant that ignores the underlying value and
    -- MUST fail the spec whenever the value's hash differs from that constant.
    return 0
    -- impl-end

prove_correct choiceValueHash by
  loom_solve
