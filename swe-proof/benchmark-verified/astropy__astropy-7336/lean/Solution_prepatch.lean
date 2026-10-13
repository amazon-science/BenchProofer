import Mathlib
-- imports-end

/-!
Finalizing the result of a unit-validating function wrapper.

A function may declare, via its return annotation, the physical unit its result
should carry. After the wrapped function has produced a value, the wrapper turns
that raw value into the function's final result according to the annotation:

* if the annotation designates a concrete unit, the produced value is converted
  to that unit and the converted value is returned successfully;
* if the annotation is absent, or it explicitly designates *no unit at all*,
  the produced value is returned unchanged, successfully — no conversion is
  attempted.

The "no unit at all" annotation and the "absent" annotation are treated
identically here: both mean "leave the produced value exactly as it is". In
particular, finalizing succeeds for every annotation shape — designating *no
unit* never triggers a conversion (which on a value carrying no convertible
target would be a failure).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Dependency model used while finalizing the result, declared as opaque
-- signatures (the proof needs no property axiom about them — the contract is
-- stated directly over them and discharged by case analysis):
--
-- * `UnitObj`        : an opaque concrete physical unit that an annotation may name.
-- * `RetVal`         : the value the wrapped function produced.
-- * `convertTo r u`  : the value `r` re-expressed under the concrete unit `u`
--                      (the unchanged value conversion the wrapper performs on
--                      the concrete-unit branch only).

/-- An opaque concrete physical unit (e.g. metres, degrees). -/
opaque UnitObj : Type

/-- The value produced by the wrapped function. Its internal structure is opaque
to the contract; modeled as a one-field carrier so it is inhabited/computable. -/
structure RetVal where
  payload : Nat
deriving Inhabited, DecidableEq

/-- A function's declared return annotation. It is one of three shapes:

* `empty`   — no annotation was given;
* `noUnit`  — an annotation was given that explicitly designates *no unit*;
* `unit u`  — an annotation designating the concrete unit `u`. -/
inductive RetAnnotation where
  | empty
  | noUnit
  | unit (u : UnitObj)

/-- A finalization failure: attempting to convert a value to a unit when the
annotation does not actually name one (the value has no convertible target). -/
structure FinalizeError where
deriving Repr, DecidableEq, Inhabited

/-- The unchanged value conversion: re-express the produced value under a
*concrete* unit. Takes a `UnitObj` (never an absent/no-unit annotation), so the
primitive has no impossible states. Modeled as an opaque callee (an A-reference);
its behavior is validated against the real conversion by G-AX. -/
opaque convertTo : RetVal → UnitObj → RetVal
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- Finalizing contract. The result is an `Except` because conversion can fail
when attempted against a non-unit target; a correct finalizer must succeed on
every annotation shape:

* a concrete-unit annotation `unit u` yields success with the produced value
  converted to `u`;
* an absent annotation (`empty`) yields success with the produced value
  unchanged;
* a *no-unit* annotation (`noUnit`) ALSO yields success with the produced value
  unchanged — it must NOT attempt a conversion (which would fail). -/
def problem_spec_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) (result : Except FinalizeError RetVal) : Prop :=
  (∀ u, annot = .unit u → result = .ok (convertTo ret u)) ∧
  (annot = .empty  → result = .ok ret) ∧
  (annot = .noUnit → result = .ok ret)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the guard fires whenever an annotation is PRESENT
-- (i.e. the annotation is not absent), so a conversion is attempted not only for
-- a concrete unit but also for an explicit *no-unit* annotation. Converting a
-- value against a no-unit target has no convertible unit and therefore FAILS
-- (`Except.error`). Only the absent (`empty`) annotation passes the value through.
def implementation_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
  match annot with
  | .empty  => return .ok ret
  | .noUnit => return .error {}
  | .unit u => return .ok (convertTo ret u)
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl. On a
-- `noUnit` annotation the spec demands `result = .ok ret`, but the buggy impl
-- returns `.error {}` (the failed conversion against a no-unit target) — the
-- discriminating clause the carried proof cannot discharge.
theorem correct_applyReturnAnnotation :
    ∀ (annot : RetAnnotation) (ret : RetVal),
      problem_spec_applyReturnAnnotation annot ret
        (implementation_applyReturnAnnotation annot ret) := by
  intro annot ret
  unfold problem_spec_applyReturnAnnotation implementation_applyReturnAnnotation
  refine ⟨?_, ?_, ?_⟩
  · intro u h; subst h; rfl
  · intro h; subst h; rfl
  · intro h; subst h; rfl
-- proof-end
