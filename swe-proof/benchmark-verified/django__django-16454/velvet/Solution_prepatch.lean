import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs: a parent command parser, when it spawns nested parsers for a
--  sub-command, threads its own error-presentation configuration into the
--  nested parsers — but only when the nested parser kind is one that
--  understands that configuration. The "is the nested kind compatible" test is
--  abstracted to the boolean input `nestedAcceptsConfig` (an R refinement of
--  the real kind-compatibility predicate, validated against the real classes by
--  conformance_check.py / G-CONF). Nothing is consumed as an axiom — see
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The error-presentation configuration a freshly-spawned nested parser is
   constructed with.

   The parent carries a configuration value, `config`, that controls whether
   argument errors are rendered as human-facing usage messages (as opposed to
   propagating uncaught). The configuration is three-valued — it may be unset —
   so it is modeled as `Option Bool`.

   The desired behaviour: the parent's configuration is propagated into a nested
   parser exactly when that nested parser is of a kind that understands the
   configuration (`nestedAcceptsConfig`). When the nested kind does not
   understand it, the nested parser is left with the unset configuration —
   propagating it would be meaningless (and, for a foreign kind, impossible).

   Front-and-center: when `nestedAcceptsConfig` holds, the *whole* parent
   configuration passes through unchanged (including the unset case); the model
   does not collapse an unset-but-compatible parent to anything else. -/
@[grind] def inheritedErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) : Option Bool :=
  if nestedAcceptsConfig then config else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the error-presentation configuration that a nested parser, created
   by a parent parser to handle a sub-command, must be constructed with.

   Desired behaviour: the parent threads its own configuration `config` into the
   nested parser whenever the nested parser is of a kind that understands that
   configuration, so that the nested parser presents argument errors the same
   human-facing way the parent does; otherwise the nested parser keeps the unset
   configuration.

   Both inputs are read-only (neither declared `mut`): the routine inspects the
   nested-kind compatibility flag and the parent's configuration and returns the
   configuration for the nested parser; it mutates neither (directive 5). The
   propagation decision is pinned exactly by `inheritedErrorConfig`. -/
method nestedParserErrorConfig
    (nestedAcceptsConfig : Bool) (config : Option Bool) return (out : Option Bool)
  ensures out = inheritedErrorConfig nestedAcceptsConfig config
  do
    -- impl-start
    -- Pre-image skeleton: nested parsers are created without any configuration
    -- threaded through — the parent's configuration is never propagated, so the
    -- nested parser always gets the unset configuration regardless of its kind.
    -- The frozen spec requires the parent's configuration whenever the nested
    -- kind understands it, so prove_correct MUST fail.
    return none
    -- impl-end

prove_correct nestedParserErrorConfig by
  loom_solve
