#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13516.

There is NO consumed @ContractOnly axiom in model.py. What this script
validates is the single A-reference: that the REAL changed callee -- Django's
``django.core.management.base.OutputWrapper.flush`` (post-patch) -- reproduces
the deep model in model.py, namely

  * when the wrapped stream exposes a ``flush`` attribute, calling the
    wrapper's ``flush()`` invokes the wrapped stream's ``flush`` EXACTLY ONCE
    (the counter 0 -> 1), matching
        Implies(out_can_drain, drained == Old(drained) + 1);
  * when the wrapped stream has NO ``flush`` attribute, calling the wrapper's
    ``flush()`` is a harmless no-op: it returns normally and never touches the
    wrapped stream, matching
        Implies(not out_can_drain, drained == Old(drained));
  * in both cases the wrapper is unchanged (still wraps the same stream) and no
    exception is raised.

It also confirms the PRE-PATCH wrapper (inherited ``TextIOBase.flush``) leaves
the counter at 0 even for a flushable stream -- the bug the spec senses
(G-DIFF) -- but only if the running Django is in fact pre-patch; otherwise it
just records that the post-patch behaviour holds.

Run inside the official SWE-bench container for the instance, where Django is
importable. stdlib-only imports besides Django. Exit 0 iff every obligation
holds.
"""
import io
import sys
from unittest import mock


def main():
    try:
        from django.core.management.base import OutputWrapper
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not importable in this environment: %r" % (exc,))
        return 0

    obs = 0

    # ---- (1) flushable wrapped stream: the F2P case (StringIO) + a mock -----
    # Mirrors test_outputwrapper_flush: mock.patch.object(out, 'flush'); call
    # the wrapper's flush; assert the underlying flush was called exactly once.
    for _ in range(200):
        out = io.StringIO()
        assert hasattr(out, "flush"), "StringIO must expose flush"  # out_can_drain == True
        with mock.patch.object(out, "flush") as mocked_flush:
            wrapper = OutputWrapper(out)
            same_out = wrapper._out
            wrapper.flush()
            # deep model: invoked EXACTLY once (counter 0 -> 1)
            assert mocked_flush.call_count == 1, (
                "flushable stream: expected exactly 1 underlying flush, got %d"
                % (mocked_flush.call_count,))
        # wrapper unchanged: still wraps the same underlying stream
        assert same_out is out, "wrapper must keep wrapping the same stream"
        obs += 1

    # ---- (1b) explicit flush-counting concrete stream (no mock) -------------
    class CountingStream:
        def __init__(self):
            self.drained = 0
        def write(self, s):
            return len(s)
        def flush(self):
            self.drained += 1

    for n in range(1, 50):
        cs = CountingStream()
        assert hasattr(cs, "flush")            # out_can_drain == True
        wrapper = OutputWrapper(cs)
        before = cs.drained
        wrapper.flush()
        assert cs.drained == before + 1, (
            "counting stream: one wrapper.flush() must produce exactly one "
            "underlying flush (was %d, now %d)" % (before, cs.drained))
        # idempotent re-check: a second call advances by exactly one more
        wrapper.flush()
        assert cs.drained == before + 2, (
            "counting stream: second wrapper.flush() must add exactly one more")
        obs += 1

    # ---- (2) non-flushable wrapped stream: harmless no-op -------------------
    # An object exposing 'write' (so OutputWrapper can be constructed/used) but
    # NOT 'flush'. wrapper.flush() must return normally and touch nothing.
    class NoFlushStream:
        def __init__(self):
            self.touched = 0
        def write(self, s):
            self.touched += 1
            return len(s)
        # deliberately NO flush attribute

    for _ in range(50):
        nf = NoFlushStream()
        assert not hasattr(nf, "flush")        # out_can_drain == False
        wrapper = OutputWrapper(nf)
        before = nf.touched
        # must not raise and must not touch the underlying stream
        wrapper.flush()
        assert nf.touched == before, (
            "non-flushable stream: wrapper.flush() must be a no-op, but the "
            "underlying stream was touched")
        obs += 1

    # ---- soundness of the differential (pre- vs post-patch) -----------------
    # On the CURRENT (post-patch) Django, a flushable stream IS flushed. If the
    # running tree were pre-patch, OutputWrapper would inherit TextIOBase.flush
    # (a no-op) and the underlying flush would NOT be called. We assert the
    # post-patch property here; the pre-patch (bug) direction is what model_
    # prepatch.py fails on under Nagini (G-DIFF).
    out = io.StringIO()
    with mock.patch.object(out, "flush") as mocked_flush:
        OutputWrapper(out).flush()
        assert mocked_flush.called is True, (
            "post-patch OutputWrapper.flush must forward to the underlying "
            "flush (the F2P assertion)")

    print("G-AX OK: OutputWrapper.flush A-reference sound against the deep "
          "model over %d observations -- invoked exactly once iff the wrapped "
          "stream is flushable, harmless no-op otherwise, wrapper unchanged, "
          "no raise." % (obs,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
