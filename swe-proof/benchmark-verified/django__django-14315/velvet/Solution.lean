import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Both modeled behaviours are closed decisions over
--  free inputs: whether a set of variable overrides is non-empty, and — when it
--  is — the already-combined set obtained by applying those overrides onto the
--  ambient set. That combination is an UNCHANGED sub-computation, taken as a
--  free input `combined` (an R abstraction, validated against the real combine
--  by conformance_check.py / G-CONF), so the spec makes no behavioural claim
--  about how it is formed and holds for every value of it. Nothing is consumed
--  as an axiom, hence no G-AX. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An ordered set of variable overrides: names paired with their values. Modeled
   as a list of name/value string pairs (mapping.md §2). The empty list models
   "no overrides at all". -/
abbrev Overrides := List (String × String)

/- Whether a (possibly-absent) set of overrides actually carries any override.
   It is considered present only when it exists AND is non-empty: an absent set
   and an empty set are treated alike as "nothing to apply". -/
def hasOverrides (o : Option Overrides) : Bool :=
  match o with
  | none     => false
  | some kvs => !kvs.isEmpty
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The variable set to hand to a launched process.

   The caller receives a (possibly-absent) set of overrides together with the
   set that results from applying those overrides onto the ambient set
   (`combined`). The desired behaviour:

   * when there is at least one override, the process is launched with the
     combined set (`some combined`);
   * when there is no override — the overrides are absent OR present but empty —
     the result is absent (`none`), signalling that the process should inherit
     the ambient set wholesale rather than being launched with an empty set.

   The key obligation pinned here is that an EMPTY set of overrides is treated as
   "absent" (`none`), not as an empty-but-present set, so that the ambient values
   are not silently dropped. Both inputs are read-only — neither is declared
   `mut` (directive 5); the routine inspects them and decides, mutating neither. -/
method effectiveProcessEnv (overrides : Option Overrides) (combined : Overrides)
    return (out : Option Overrides)
  ensures out = (if hasOverrides overrides then some combined else none)
  do
    -- impl-start
    -- Hand over the combined set when there is something to apply; otherwise
    -- hand over "absent" so the ambient set is inherited as-is.
    let result := if hasOverrides overrides then some combined else none
    return result
    -- impl-end

prove_correct effectiveProcessEnv by
  loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The override set to report from an assembly step that builds it up entry by
   entry. The assembled set is reported only when it actually carries an entry;
   an assembled set that ended up empty is reported as absent (`none`) rather
   than as an empty-but-present set — so a downstream consumer that distinguishes
   "absent" from "empty" inherits the ambient values instead of being handed an
   empty set.

   `assembled` is read-only — not declared `mut` (directive 5); the step only
   inspects it to decide what to report. -/
method normalizedEnv (assembled : Overrides)
    return (out : Option Overrides)
  ensures out = (if assembled.isEmpty then none else some assembled)
  do
    -- impl-start
    -- Report the assembled set when it carries an entry; otherwise report
    -- "absent".
    let result := if assembled.isEmpty then none else some assembled
    return result
    -- impl-end

prove_correct normalizedEnv by
  loom_solve
