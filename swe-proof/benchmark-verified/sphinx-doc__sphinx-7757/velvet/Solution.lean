import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled behaviour is the distribution of default values across
-- the positional parameters of a signature; it is pure data movement with no
-- unchanged outside callee participating in the computation. (The rendering of
-- an individual default expression is a per-element identity under the type
-- refinement — mapping.md §2 — so it introduces no axiom.)
-- axioms-end

-- pure-start
-- The desired distribution of default values across positional parameters.
--
-- A signature has `p` positional parameters in a leading group and `q` in a
-- trailing group, for `n = p + q` positional parameters in declaration order.
-- A list of `d ≤ n` default values is supplied; by the language rule the
-- defaults are RIGHT-ALIGNED across the whole positional list: the last `d`
-- positions receive the `d` defaults (in order) and the leading `n - d`
-- positions have no default.  `none` marks "no default"; `some v` marks the
-- default value `v`.
--
-- `distributed` is the resulting per-position default vector.  It is the
-- canonical right-alignment: `n - d` empties followed by the defaults verbatim.
def distributed (n : Nat) (defaults : List Int) : List (Option Int) :=
  List.replicate (n - defaults.length) none ++ defaults.map (Option.some)

-- Prepending one empty slot in front of a partial right-alignment lengthens the
-- empty prefix by one.  This is the single per-iteration fact the backward loop
-- that builds the alignment needs (the Velvet backward-fold pattern, plan §5.4).
lemma distributed_prepend_step (total k : Nat) (base : List (Option Int))
    (hk : 0 < k) (hkt : k ≤ total) :
    none :: (List.replicate (total - k) none ++ base)
      = List.replicate (total - (k - 1)) none ++ base := by
  have hkk : total - (k - 1) = (total - k) + 1 := by omega
  rw [hkk, List.replicate_succ, List.cons_append]
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; repeats below)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- The default-distribution of a signature whose positional parameters split
-- into a leading group of size `p` and a trailing group of size `q`.
-- `defaults` are the supplied default values, in declaration order; there can
-- be no more defaults than positional parameters.  The result gives, for each
-- of the `p + q` positional parameters in order, its default (`none` = absent).
method distributePositionalDefaults
    (p : Nat) (q : Nat) (defaults : List Int) return (out : List (Option Int))
  require defaults.length ≤ p + q
  ensures out = distributed (p + q) defaults
  do
    -- impl-start
    -- Right-align the defaults across ALL `p + q` positional parameters: start
    -- from the supplied defaults and prepend one empty slot at a time until the
    -- leading `(p + q) - defaults.length` positions are filled with "no default".
    let mut out : List (Option Int) := defaults.map (Option.some)
    let mut k := (p + q) - defaults.length
    while k > 0
      invariant k ≤ (p + q) - defaults.length
      invariant out = List.replicate (((p + q) - defaults.length) - k) none
                        ++ defaults.map (Option.some)
      done_with k = 0
      decreasing k
    do
      out := none :: out
      k := k - 1
    return out
    -- impl-end

prove_correct distributePositionalDefaults by
  loom_solve
  case _ =>  -- loop-body step: prepend one empty slot
    rw [invariant_2]
    exact distributed_prepend_step ((p + q) - defaults.length) k _ (by omega) (by omega)
  case _ =>  -- loop-exit: k = 0, so the invariant already is the postcondition
    simp_all [distributed]
