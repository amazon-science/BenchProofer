import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque drawing context: the transient state a placement needs in order to
   measure and position a child. Its internal structure is irrelevant to this
   decision; only whether one is supplied — and, if not, where a substitute is
   obtained — matters. -/
axiom Ctx : Type

/- An opaque host: the container a child is placed against. It always carries a
   figure, hence a retrievable drawing context (`hostContext`). -/
axiom Host : Type

/- An opaque placement region: the computed box a child occupies. Equality of
   regions is equality of their extents (mapping.md §2). -/
axiom Region : Type

/- The host's own drawing context. An UNCHANGED retrieval from the host's
   figure; total (every real host has a figure that yields a context) and left
   fully opaque — the weakest sufficient contract is none (directive 7).
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom hostContext : Host → Ctx

/- The downstream region computation given a CONCRETE context and the host: the
   unchanged measure → offset → transform pipeline. An UNCHANGED callee chain;
   total and deterministic given a concrete context, left fully opaque.
   Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom placeWith : Ctx → Host → Region
-- axioms-end

-- pure-start
/- The outcome shape of a placement. A well-formed placement always yields a
   region (`Except.ok`). The single error constructor records the one outcome a
   correct placement must NEVER produce: attempting to measure with no context
   at all, which on a container-less child is undefined. A correct result is
   always a region, never this error. -/
inductive PlaceErr where
  | noContext
deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the placement region of an anchored child against its host.

   `ctx` and `host` are read-only inputs (neither is `mut`):
     * `ctx`  — the drawing context to measure with, or absent when the caller
                has none to offer;
     * `host` — the container the child is placed against; it always carries a
                retrievable drawing context of its own.

   Desired behaviour: the placement is computed by running the downstream
   measure-and-position pipeline with a CONCRETE context. A context is obtained
   before measuring: when one is supplied it is used directly; when none is
   supplied the host's own context is substituted. An absent context must never
   abandon the placement — every call must produce a region. The three
   postconditions pin this branch-by-branch, grounded directly in the inputs
   and the two opaque unchanged callees (directive 8: no single spec-level
   answer function exists for an implementation to echo):
     * every call yields a region (the never-raise frame);
     * an absent context runs the downstream with the host's own context;
     * a present context is passed through to the downstream unchanged. -/
noncomputable section
method computePlacement (ctx : Option Ctx) (host : Host)
    return (out : Except PlaceErr Region)
  ensures ∃ reg, out = Except.ok reg
  ensures ctx = none → out = Except.ok (placeWith (hostContext host) host)
  ensures ∀ c, ctx = some c → out = Except.ok (placeWith c host)
  do
    -- impl-start
    -- Pre-image skeleton: the downstream measurement is attempted directly on
    -- the supplied context WITHOUT first obtaining a concrete one. When a
    -- context is present it is used; when it is absent there is nothing to
    -- measure with, so the attempt is the undefined-measurement outcome the
    -- frozen spec forbids: the spec requires every input to yield a region (and
    -- an absent context to fall back to the host's context), so prove_correct
    -- MUST fail on those clauses.
    let result : Except PlaceErr Region :=
      match ctx with
      | some c => Except.ok (placeWith c host)
      | none   => Except.error PlaceErr.noContext
    return result
    -- impl-end
end

prove_correct computePlacement by
  loom_solve <;>
    try simp_all
