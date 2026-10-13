import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one entry of a
--  display configuration and decides how it should be reported. The runtime
--  observations the decision depends on — whether the entry is itself an
--  invokable object, whether it names an attribute of the administrator,
--  whether the model's field registry knows the name, whether plain attribute
--  access on the model class succeeds, and whether the resolved descriptor is
--  a many-to-many relation — are abstracted to the boolean inputs of the
--  method. Each is an R-refinement of a real observation (callable / hasattr /
--  field-registry lookup / attribute access / relation kind), validated
--  against the real objects by conformance_check.py (G-CONF). Nothing is
--  consumed as an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The three ways a single display-configuration entry can be reported:

   * `ok`   — the entry is acceptable, no message is produced (`[]`);
   * `e108` — the entry does not resolve to anything usable on the model
              (`admin.E108`, "refers to '…', which is not a callable, an
              attribute of …, or an attribute or method on …");
   * `e109` — the entry resolves to a many-to-many relation, which is not
              permitted here (`admin.E109`, "must not be a ManyToManyField").

   The error identifiers `admin.E108` / `admin.E109` are part of the public
   problem statement. -/
inductive CheckResult where
  | ok
  | e108
  | e109
  deriving DecidableEq, Inhabited

/- The acceptable / E108 / E109 decision for one display-configuration entry.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is always acceptable.
   2. Otherwise, an entry naming an attribute of the administrator itself
      (`hasAttrObj`) is always acceptable.
   3. Otherwise the entry must resolve to a model field. The model's field
      registry is consulted first; only if that lookup fails (`getFieldRaises`)
      is plain attribute access on the model class attempted, and only if THAT
      also fails (`modelAttrRaises`) is the entry unresolvable and reported
      `e108`. Crucially, a failed registry lookup alone never condemns the
      entry — attribute access is still tried.
   4. Whenever a field IS resolved (by either route), the sole remaining
      question is whether it is a many-to-many relation (`fieldIsM2M`):
      if so the entry is reported `e109`, otherwise it is acceptable.

   `fieldIsM2M` is only consulted on the paths where a field was resolved; on
   the `e108` path no field exists and its value is immaterial. -/
@[grind] def listDisplayItemOutcome
    (isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M : Bool) : CheckResult :=
  if isCallable then CheckResult.ok
  else if hasAttrObj then CheckResult.ok
  else if getFieldRaises then
    (if modelAttrRaises then CheckResult.e108
     else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
  else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's display configuration and
   decide how it is reported: acceptable, E108 (does not resolve to anything
   usable), or E109 (resolves to a many-to-many relation).

   Desired behaviour (the abstract contract; see `listDisplayItemOutcome`):
   an invokable entry, or one naming an attribute of the administrator, is
   acceptable. Otherwise the entry must resolve to a model field. The field
   registry is consulted first; if that fails, attribute access on the model
   class is attempted; the entry is reported E108 only when BOTH resolution
   routes fail. Whenever a field is resolved by either route, the entry is
   reported E109 exactly when that field is a many-to-many relation, and is
   acceptable otherwise.

   All five inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The decision is pinned exactly by
   `listDisplayItemOutcome`. -/
method listDisplayItemCheck
    (isCallable : Bool) (hasAttrObj : Bool) (getFieldRaises : Bool)
    (modelAttrRaises : Bool) (fieldIsM2M : Bool)
    return (out : CheckResult)
  ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
  do
    -- impl-start
    -- An invokable entry, or one that is an attribute of the administrator, is
    -- acceptable outright. Otherwise resolve the entry to a model field: the
    -- field registry first, then attribute access on the model class; only
    -- when both fail is the entry unresolvable (E108). Whenever a field is
    -- resolved by either route, it is acceptable unless it is a many-to-many
    -- relation (E109).
    let result : CheckResult :=
      if isCallable then CheckResult.ok
      else if hasAttrObj then CheckResult.ok
      else if getFieldRaises then
        (if modelAttrRaises then CheckResult.e108
         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
    return result
    -- impl-end

prove_correct listDisplayItemCheck by
  loom_solve
