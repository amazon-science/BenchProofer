#!/usr/bin/env python3
"""G-CONF for django__django-13516.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_flush` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `OutputWrapper.flush`,
over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): a single wrapper flush request, observed through the
underlying stream's state:

  * hasFlush      -- whether the underlying stream supports flushing
                     (hasattr(self._out, 'flush'));
  * flushCount    -- how many times the underlying stream's flush was invoked.

The patched method invokes the underlying stream's flush exactly once iff the
stream supports it; the support flag is never changed.

  * Oracle = the REAL patched `OutputWrapper.flush` wrapping a stand-in stream
             that either exposes a call-counting `flush` (hasFlush=True) or
             exposes no `flush` attribute (hasFlush=False), pre-seeded to
             `initialCount`. We read the resulting (hasFlush, flushCount).
  * Shadow = (hasFlush, initialCount + 1) if hasFlush else (hasFlush, initialCount).

Type bijection (mapping.md): hasFlush<->hasattr(self._out,'flush') (bool),
flushCount<->underlying stream flush invocation count (int).
stdlib-only; no hypothesis required.
"""
import random
import sys

# --- configure Django settings before importing the management base ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django.core.management.base import OutputWrapper


class FlushableStream:
    """Underlying stream that SUPPORTS flushing; counts invocations."""
    def __init__(self, initial_count):
        self.flush_count = initial_count

    def flush(self):
        self.flush_count += 1

    # writing is irrelevant here; provide a benign sink so attribute delegation
    # never surprises us.
    def write(self, msg):
        pass

    def isatty(self):
        return False


class NonFlushableStream:
    """Underlying stream that does NOT support flushing: no `flush` attribute."""
    def __init__(self, initial_count):
        # carried only so the shadow has a comparable observable; not exposed as
        # a `flush` method, so hasattr(self, 'flush') is False.
        self._observed_count = initial_count

    def write(self, msg):
        pass

    def isatty(self):
        return False


def oracle(has_flush, initial_count):
    """Behavior of the patched repo method for these inputs.

    Returns (resulting_has_flush, resulting_flush_count)."""
    if has_flush:
        stream = FlushableStream(initial_count)
        wrapper = OutputWrapper(stream)
        wrapper.flush()
        return (hasattr(stream, "flush"), stream.flush_count)
    else:
        stream = NonFlushableStream(initial_count)
        wrapper = OutputWrapper(stream)
        wrapper.flush()
        # underlying stream supports no flush => count cannot have advanced.
        return (hasattr(stream, "flush"), stream._observed_count)


def shadow(has_flush, initial_count):
    """R/I transliteration of implementation_flush (Lean).

    Op 1: test the support flag. Op 2: invoke the stream's flush once iff
    supported (advancing the count). Op 3: else leave the stream untouched.
    The support flag is carried through unchanged (frame)."""
    if has_flush:
        return (has_flush, initial_count + 1)
    return (has_flush, initial_count)


def main():
    rng = random.Random(13516)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        has_flush = rng.choice([True, False])
        initial_count = rng.randint(0, 1_000_000)
        o = oracle(has_flush, initial_count)
        s = shadow(has_flush, initial_count)
        if o != s:
            disagreements += 1
            if first is None:
                first = (has_flush, initial_count, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
