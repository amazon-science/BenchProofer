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
    -- PRE-PATCH (buggy) skeleton: the leading group (the positional-only
    -- parameters) is EXCLUDED from the default alignment.  The defaults are
    -- right-aligned across the `q` trailing positions only — at most `q` of
    -- them survive — and the leading `p + (q - kept)` positions are filled with
    -- "no default".  When more defaults are supplied than there are trailing
    -- positions (defaults spill into the leading group), the surplus leading
    -- defaults are DROPPED: the vanished-default bug.  When `defaults.length ≤
    -- q` this coincides with the correct distribution, which is why only
    -- signatures with a defaulted leading-group parameter expose the bug.
    let kept := defaults.drop (defaults.length - min q defaults.length)
    let mut out : List (Option Int) := kept.map (Option.some)
    let mut k := (p + q) - kept.length
    while k > 0
      invariant k ≤ (p + q) - kept.length
      invariant out = List.replicate (((p + q) - kept.length) - k) none
                        ++ kept.map (Option.some)
      done_with k = 0
      decreasing k
    do
      out := none :: out
      k := k - 1
    return out
    -- impl-end

prove_correct distributePositionalDefaults by
  loom_solve
  case _ =>  -- loop-body step: prepend one empty slot (the invariant is sound)
    rw [invariant_2]
    exact distributed_prepend_step _ k _ (by omega) (by omega)
  case _ =>  -- loop-exit: the buggy alignment is over `q`, not `p + q`, so the
             -- postcondition `out = distributed (p + q) defaults` does not hold
             -- whenever a default spills into the leading group.  UNPROVABLE.
    simp_all [distributed]
