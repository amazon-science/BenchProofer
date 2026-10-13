#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13516 (nagini).

SHADOW: the impl region of ``drain_buffer`` in model.py, copied VERBATIM below
(the impl region contains no contract calls; the supporting ``Sink`` /
``OutputStream`` classes copy over with their contract calls -- Requires /
Ensures / Fold / Unfold and the @Predicate / @Pure ghost members -- stripped,
leaving the plain-Python state updates). There are no @ContractOnly callees in
this bundle and no PSeq usage, so no sequence shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.core.management.base.OutputWrapper.flush``. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so the plain import below resolves to the patched tree. This script does NOT
apply any patch itself.

Type bridge (mapping.md section 2):
  * ``stream.out_can_drain : bool``  <->  whether the wrapped stream object
    exposes a ``flush`` attribute (probed with ``hasattr`` on the real side);
  * ``stream.out.drained : int`` (monotone invocation counter)  <->  the
    observable number of times the wrapped stream's ``flush`` ran, realised on
    the real side by a concrete counting stream (capability True) or by a
    stream with no ``flush`` attribute plus a touch counter (capability
    False, where the count is frozen by construction);
  * ``stream.out`` (object reference)  <->  the wrapper's wrapped-stream
    reference; "wrapper unchanged" is checked as identity of that reference
    and stability of the capability probe.
  A pre-existing counter value N (the Requires admits any starting count) is
  bridged by pre-charging BOTH counters to the same N.

Input domain: the precondition admits any OutputStream whose Sink predicate
holds, i.e. any (capability bit, starting invocation count) pair, and the
operation may be invoked any number of times in sequence. Generation covers
both capability values, boundary starting counts (0, 1, 2, 2**31-1, 10**18),
call-sequence lengths 1..6, and uniform fuzz over the same space.

>= 1e5 Requires-satisfying inputs (each single drain invocation, i.e. each
pre-state the shadow and the oracle are compared from, counts as one input).
Pinned fuzz seed: 13516 (recorded here and used for all randomness).

Exit 0 iff zero disagreements; on a disagreement, print the input and both
outputs, then exit 1. stdlib only (``random``); no hypothesis needed.
"""
import random
import sys

SEED = 13516
TARGET_INPUTS = 100000


# --- shadow: model.py support classes, contracts stripped --------------------

class Sink(object):
    # model.py Sink with the @Predicate/@Pure ghost members and the
    # Fold/Unfold/Requires/Ensures contract calls stripped; the plain state
    # updates are kept verbatim.

    def __init__(self):
        self.drained = 0

    def do_drain(self):
        self.drained = self.drained + 1


class OutputStream(object):
    # model.py OutputStream with contract calls stripped.

    def __init__(self, out, out_can_drain):
        self.out = out
        self.out_can_drain = out_can_drain


def drain_buffer(stream):
    # impl region of model.py, copied VERBATIM (it contains no contract
    # calls):
    # impl-start
    if stream.out_can_drain:
        stream.out.do_drain()
    # impl-end


# --- oracle-side concrete wrapped streams (the bridge carriers) ---------------

class CountingStream(object):
    """Wrapped stream WITH a flush attribute: capability bit True. Its
    ``drained`` field realises the model's invocation counter."""

    def __init__(self):
        self.drained = 0

    def write(self, s):
        return len(s)

    def flush(self):
        self.drained += 1


class NoFlushStream(object):
    """Wrapped stream WITHOUT a flush attribute: capability bit False. The
    invocation counter is frozen by construction; ``touched`` additionally
    senses any other access to the object."""

    def __init__(self):
        self.drained = 0  # bridge counter; nothing here can advance it
        self.touched = 0

    def write(self, s):
        self.touched += 1
        return len(s)
    # deliberately NO flush attribute


def fail(case, what, shadow_out, real_out):
    print("DISAGREEMENT")
    print("  input      : %r" % (case,))
    print("  aspect     : %s" % (what,))
    print("  shadow out : %r" % (shadow_out,))
    print("  real out   : %r" % (real_out,))
    sys.exit(1)


def run_case(OutputWrapper, can_drain, start_count, n_calls):
    """One trial: pre-charge both counters to start_count, then perform
    n_calls drain requests on the shadow and on the real wrapper, comparing
    the observable state after every single invocation. Returns the number of
    Requires-satisfying inputs exercised (== n_calls)."""
    case = {"can_drain": can_drain, "start_count": start_count,
            "n_calls": n_calls}

    # shadow side
    sink = Sink()
    sink.drained = start_count           # bridge: pre-existing count
    stream = OutputStream(sink, can_drain)

    # real side
    real_out = CountingStream() if can_drain else NoFlushStream()
    real_out.drained = start_count       # bridge: same pre-existing count
    if hasattr(real_out, "flush") != can_drain:
        fail(case, "bridge construction (capability probe)",
             can_drain, hasattr(real_out, "flush"))
    wrapper = OutputWrapper(real_out)
    before_touched = getattr(real_out, "touched", None)

    for i in range(n_calls):
        # shadow invocation
        try:
            drain_buffer(stream)
        except Exception as exc:  # the impl must not raise
            fail(case, "shadow raised on call %d" % (i + 1,), repr(exc), None)
        # real invocation
        try:
            wrapper.flush()
        except Exception as exc:
            fail(case, "real wrapper raised on call %d" % (i + 1,),
                 sink.drained, repr(exc))
        # compare the invocation counter (the modeled observable)
        if sink.drained != real_out.drained:
            fail(case, "invocation counter after call %d" % (i + 1,),
                 sink.drained, real_out.drained)
        # wrapper unchanged: same wrapped stream, same capability
        if stream.out is not sink:
            fail(case, "shadow wrapped-stream reference changed", stream.out,
                 sink)
        if wrapper._out is not real_out:
            fail(case, "real wrapped-stream reference after call %d" % (i + 1,),
                 sink, wrapper._out)
        if stream.out_can_drain != can_drain or \
                hasattr(real_out, "flush") != can_drain:
            fail(case, "capability bit after call %d" % (i + 1,),
                 stream.out_can_drain, hasattr(real_out, "flush"))
        # capability-False leg: the wrapped stream must not be touched at all
        if not can_drain and real_out.touched != before_touched:
            fail(case, "no-capability stream touched on call %d" % (i + 1,),
                 before_touched, real_out.touched)
    return n_calls


def main():
    try:
        from django.core.management.base import OutputWrapper
    except Exception as exc:
        print("ERROR: cannot import the patched repo function: %r" % (exc,))
        return 2

    rng = random.Random(SEED)
    inputs = 0

    # ---- boundary cases ------------------------------------------------------
    boundary_counts = [0, 1, 2, 2 ** 31 - 1, 10 ** 18]
    for can_drain in (True, False):
        for start in boundary_counts:
            for n_calls in range(1, 7):
                inputs += run_case(OutputWrapper, can_drain, start, n_calls)

    # ---- fuzz (pinned seed) --------------------------------------------------
    while inputs < TARGET_INPUTS:
        can_drain = rng.random() < 0.5
        start = rng.choice([0, 0, 1, rng.randrange(0, 10 ** 6),
                            rng.randrange(0, 10 ** 18)])
        n_calls = rng.randrange(1, 7)
        inputs += run_case(OutputWrapper, can_drain, start, n_calls)

    print("G-CONF OK: shadow (verbatim impl region) == real patched repo "
          "function over %d Requires-satisfying inputs (seed %d); "
          "0 disagreements." % (inputs, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
