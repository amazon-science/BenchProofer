import Velvet.Std
-- imports-end

/- Total correctness: the real construction/deconstruction paths are
   straight-line dispatches over the field's configuration and always
   terminate, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating branch discharge its
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle: the modeled behavior is
   a pure data-flow over the field's configuration, modeled directly. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A storage backend. Two backends are interchangeable iff they denote the same
   configured location; the distinguished `defaultBackend` is the ambient
   backend used when none is configured. `present` records whether the value
   counts as supplied when the field tests it at construction: a supplied
   value that tests as not-present is treated exactly like no value at all
   (a pre-existing presence test, see `initState`). -/
structure Backend where
  handle : Nat
  present : Bool
deriving DecidableEq, Inhabited, Repr

def defaultBackend : Backend := ⟨0, true⟩

/- A producer: a value that, when consulted, yields a backend. It carries its
   own identity (`handle`) so two producers yielding the same backend remain
   distinguishable — this is the property the deconstruction below must
   preserve. Like a backend, a producer carries `present`: whether it counts
   as supplied when the field tests it; a producer that tests as not-present
   is never consulted and never retained (see `initState`). -/
structure Producer where
  handle : Nat
  yields : Backend
  present : Bool
deriving DecidableEq, Inhabited, Repr

/- How a backend may be supplied to the field, and equally the shape a
   deconstruction may report it back as:
   * `omitted`    — nothing supplied (the ambient backend is used);
   * `concrete b` — a backend value supplied directly;
   * `producer p` — a producer supplied, to be consulted for the backend. -/
inductive BackendArg where
  | omitted
  | concrete (b : Backend)
  | producer (p : Producer)
deriving DecidableEq, Inhabited, Repr

/- The field's retained configuration after construction:
   * `backend`      — the backend in effect (a producer is consulted once, at
                      construction, to obtain it);
   * `origProducer` — the producer it was supplied as, if any, retained so that
                      a later deconstruction can report the producer itself
                      rather than the backend it happened to yield. -/
structure FieldState where
  backend : Backend
  origProducer : Option Producer
deriving DecidableEq, Inhabited, Repr

/- Construction: resolve a supplied argument to the retained configuration.
   The argument is first subjected to the field's pre-existing presence test:
   an argument that does not count as supplied — omitted, or a value that
   tests as not-present — selects the ambient backend and retains nothing.
   A present concrete backend is kept as-is; a present producer is consulted
   once for its backend AND retained. -/
def initState (arg : BackendArg) : FieldState :=
  match arg with
  | .omitted     => { backend := defaultBackend, origProducer := none }
  | .concrete b  =>
      if b.present then { backend := b, origProducer := none }
      else { backend := defaultBackend, origProducer := none }
  | .producer p  =>
      if p.present then { backend := p.yields, origProducer := some p }
      else { backend := defaultBackend, origProducer := none }

/- Deconstruction: report how the backend should be supplied to reproduce this
   field. The ambient backend is reported as `omitted` (nothing to record). A
   field configured from a producer reports that producer; otherwise it reports
   its concrete backend. -/
def emit (st : FieldState) : BackendArg :=
  if st.backend = defaultBackend then BackendArg.omitted
  else match st.origProducer with
       | some p => BackendArg.producer p
       | none   => BackendArg.concrete st.backend
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; no module-level preconditions)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Construction step. Produces the retained configuration for a supplied
   argument: an argument failing the presence test resolves to the ambient
   backend; a present producer is consulted exactly once and retained. -/
method initField (arg : BackendArg) return (st : FieldState)
  ensures st = initState arg
  do
    -- impl-start
    match arg with
    | .omitted     => pure { backend := defaultBackend, origProducer := none }
    | .concrete b  =>
        if b.present then pure { backend := b, origProducer := none }
        else pure { backend := defaultBackend, origProducer := none }
    | .producer p  =>
        if p.present then pure { backend := p.yields, origProducer := some p }
        else pure { backend := defaultBackend, origProducer := none }
    -- impl-end

prove_correct initField by
  loom_solve <;> simp_all [initState]

/- Deconstruction step. Reports the argument that reproduces this field's
   backend configuration: the ambient backend as `omitted`, a producer-backed
   field as its producer, any other as its concrete backend. -/
method deconstructStorage (st : FieldState) return (e : BackendArg)
  ensures e = emit st
  do
    -- impl-start
    if st.backend = defaultBackend then
      pure BackendArg.omitted
    else
      match st.origProducer with
      | some p => pure (BackendArg.producer p)
      | none   => pure (BackendArg.concrete st.backend)
    -- impl-end

prove_correct deconstructStorage by
  loom_solve <;> simp_all [emit]

/- Lifecycle: construct from an argument, then deconstruct. The reported
   argument is `emit (initState arg)` — in particular, an argument supplied as
   a producer (whose yielded backend is not the ambient one) is reported back as
   that same producer, not as the backend it yielded. -/
method roundTripStorage (arg : BackendArg) return (e : BackendArg)
  ensures e = emit (initState arg)
  do
    -- impl-start
    let st ← initField arg
    let e ← deconstructStorage st
    return e
    -- impl-end

prove_correct roundTripStorage by
  loom_solve
