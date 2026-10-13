import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behavior under spec
   is a pure data-flow over a key→value mapping: each value is repackaged as a
   deferred value, and the only behaviour that matters — how a deferred value
   answers a type-dispatching consumer — is modeled directly below. There is
   therefore no consumed axiom and no deep-model reference to a foreign callee
   (mapping.md §3). -/
-- axioms-end

-- pure-start
/- A runtime value. `tag` is its runtime type (an opaque identifier; two values
   share a tag iff they have the same runtime type); `content` is the payload.
   Tags of real values are positive (`1 ≤ tag`) — the sentinel `0` is reserved
   for the distinct "deferred-proxy" type that no real value carries. -/
structure Value where
  tag : Nat
  content : List Char
deriving DecidableEq, Inhabited, Repr

/- A deferred value. When finally consulted it yields `forced`. It also reports
   a runtime type for callers that dispatch on type:
   * `reported = none`   — a distinct proxy type, equal to no real value's type;
   * `reported = some t` — it claims to BE a value of runtime type `t`.
   A faithful deferred value reports `none`: it never claims to be the type of
   the value it defers to, so a type-dispatching consumer coerces it into a
   genuine value rather than handing the wrapper itself through. -/
structure Wrapper where
  forced : Value
  reported : Option Nat
deriving DecidableEq, Inhabited, Repr

/- The result of a type-dispatching consumer asked to produce a value of a
   target runtime type:
   * `genuine v`     — a real value of the target type was produced;
   * `passthrough w` — the consumer believed the wrapper already had the target
                       type and returned it unchanged (a NON-genuine value). -/
inductive Coerced where
  | genuine (v : Value)
  | passthrough (w : Wrapper)
deriving DecidableEq, Inhabited, Repr

/- A type-dispatching consumer (the abstract shape of a downstream coercion that
   guards on runtime type): if the wrapper reports exactly the target type `t`
   it is taken to be genuine already and returned unchanged; otherwise the
   wrapper is consulted and a genuine value of the target type is produced. -/
def coerce (w : Wrapper) (t : Nat) : Coerced :=
  if w.reported = some t then Coerced.passthrough w
  else Coerced.genuine w.forced

/- Defer a single value: it forces back to that value and reports the distinct
   proxy type (`none`), never claiming to be the value's own runtime type. -/
def deferOne (v : Value) : Wrapper := { forced := v, reported := none }

/- Defer every value of a key→value mapping, key (and order) preserved.
   Front-recursive so a single unfold is available per loop step (the Velvet
   fold pattern, plan §5.4). -/
def deferredOf : List (Nat × Value) → List (Nat × Wrapper)
  | []          => []
  | p :: rest   => (p.fst, deferOne p.snd) :: deferredOf rest

@[grind] lemma deferredOf_nil : deferredOf [] = [] := rfl
@[grind] lemma deferredOf_cons (p : Nat × Value) (rest : List (Nat × Value)) :
    deferredOf (p :: rest) = (p.fst, deferOne p.snd) :: deferredOf rest := rfl

/- A deferred value coerces to the genuine underlying value for ANY target
   type: it reports `none`, which is never `some t`, so the consumer always
   takes the produce-a-genuine-value branch. Marked `@[grind]` so `loom_solve`
   discharges the genuineness postcondition automatically. -/
@[grind] lemma coerce_deferOne (v : Value) (t : Nat) :
    coerce (deferOne v) t = Coerced.genuine v := by
  simp [coerce, deferOne]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Repackage a key→value mapping so each value becomes a deferred value (keys
   and order unchanged). The frozen guarantee: every produced deferred value,
   asked by a consumer that dispatches on the underlying value's own runtime
   type, yields the GENUINE underlying value — never the wrapper itself. -/
method deferMapping (entries : List (Nat × Value)) return (out : List (Nat × Wrapper))
  ensures out = deferredOf entries
  ensures ∀ v : Value, coerce (deferOne v) v.tag = Coerced.genuine v
  do
    -- impl-start
    -- Pre-image skeleton: each value is wrapped in a deferred value that
    -- MASQUERADES as the value's own runtime type (`reported := some
    -- p.snd.tag`) instead of reporting the distinct proxy type. A consumer
    -- dispatching on that type then takes the wrapper to be genuine already
    -- and hands it through un-coerced. The frozen spec requires `deferredOf`
    -- (whose `deferOne` reports `none`), so prove_correct MUST fail.
    let mut result : List (Nat × Wrapper) := []
    let mut i := entries.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ entries.length
      invariant result = deferredOf (entries.drop i)
      done_with i = 0
      decreasing i
    do
      let p := entries[i - 1]!
      result := (p.fst, { forced := p.snd, reported := some p.snd.tag }) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the entry at
   `i-1` on the front, so `deferredOf` peels one `deferOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma deferredOf_drop_step (entries : List (Nat × Value)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ entries.length) :
    deferredOf (entries.drop (i - 1))
      = (entries[i - 1]!.fst, deferOne entries[i - 1]!.snd) :: deferredOf (entries.drop i) := by
  have hlt : i - 1 < entries.length := by omega
  have hcons : entries.drop (i - 1) = entries[i - 1]! :: entries.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, deferredOf_cons]

prove_correct deferMapping by
  loom_solve
  · rw [deferredOf_drop_step entries i (by omega) (by omega)]
    simp_all
