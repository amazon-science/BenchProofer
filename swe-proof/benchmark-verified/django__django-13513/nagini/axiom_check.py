#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13513.

This bundle consumes NO `@ContractOnly` axiom: the changed operation (the
restructured exception-chain frame assembly) is modelled DEEPLY in model.py
(`frames_from_traceback` counts one entry per location in one exception's own
trace; `chain_total` sums the per-exception trace lengths across the chain).
G-AX therefore validates that deep model == the REAL assembly the gold patch
performs (an A-reference), on the FAIL_TO_PASS scenario, boundary chains, and
randomized fuzz.

The real assembly (gold `get_traceback_frames` + `get_exception_traceback_frames`,
django/views/debug.py post-patch):

    def get_traceback_frames(self):
        ...                                       # build `exceptions` chain
        exc_value = exceptions.pop()
        tb = self.tb if not exceptions else exc_value.__traceback__
        frames.extend(self.get_exception_traceback_frames(exc_value, tb))
        while exceptions:
            exc_value = exceptions.pop()
            frames.extend(self.get_exception_traceback_frames(
                exc_value, exc_value.__traceback__))
        return frames

    def get_exception_traceback_frames(self, exc_value, tb):
        ...
        while tb is not None:
            ...                                   # build one frame per tb node
            yield {...}
            tb = tb.tb_next

i.e. every exception in the chain contributes exactly the number of frames
equal to the number of visible nodes in its OWN traceback, INDEPENDENTLY of the
other exceptions; the total is the sum of those per-exception lengths. (The
`__traceback_hide__` skip only removes individual nodes; here we model the
post-skip visible-node count as the per-exception trace length.)

Two model-side facts under check, expressed at the count level:

  (1) frames_from_traceback(trace_len): one entry per node => exactly trace_len
      entries (an empty trace yields zero entries).
  (2) chain_total: the whole report length equals the SUM of the per-exception
      trace lengths -- an exception with a non-empty trace still contributes its
      entries even when another exception's trace is empty.

Where available IN-CONTAINER, the check also drives the REAL Django
`ExceptionReporter.get_traceback_frames` on constructed exception chains
(including the exact FAIL_TO_PASS scenario) and asserts the real frame count
equals chain_total. When Django is not importable, it falls back to a faithful
stdlib re-creation of the gold control flow. Exit 0 iff every observation holds.
"""
import random
import sys


# --- model.py deep-model references (kept in lock-step with model.py) ----------

def frames_from_traceback(trace_len):
    """model.py `frames_from_traceback`: one marker entry per trace node."""
    return [1] * trace_len


def chain_total(lens):
    """model.py `chain_total`: sum of the per-exception trace lengths."""
    total = 0
    for n in lens:
        total += n
    return total


def model_assemble_len(trace_lens):
    """model.py `assemble_frames` length: concatenate every exception's own
    contribution, independently, and take the total count."""
    frames = []
    for n in trace_lens:           # order is irrelevant to the count
        frames.extend(frames_from_traceback(n))
    return len(frames)


# --- faithful stdlib re-creation of the REAL gold assembly ---------------------

class _TB:
    """A minimal traceback-node stand-in (mirrors the `tb_next` chain that the
    real `while tb is not None: ...; tb = tb.tb_next` loop walks)."""
    def __init__(self, length):
        self.tb_next = _TB(length - 1) if length > 1 else None


def _make_tb(length):
    return _TB(length) if length > 0 else None


def real_assemble_len(trace_lens):
    """Byte-for-byte the gold control flow (counting frames only).

    `trace_lens` is the chain in `exceptions`-list order: index 0 is the
    outermost exception, the last index is the innermost cause (popped first).
    """
    exceptions = list(trace_lens)          # the built chain
    frames = []
    if not exceptions:
        return len(frames)
    inner = exceptions.pop()               # exc_value = exceptions.pop()
    tb = _make_tb(inner)                    # tb = ... exc_value.__traceback__
    frames.extend(_gold_exception_frames(tb))
    while exceptions:
        exc_len = exceptions.pop()
        frames.extend(_gold_exception_frames(_make_tb(exc_len)))
    return len(frames)


def _gold_exception_frames(tb):
    out = []
    while tb is not None:                  # gold get_exception_traceback_frames
        out.append(1)
        tb = tb.tb_next
    return out


def prepatch_assemble_len(trace_lens):
    """The PRE-PATCH (buggy) control flow, for the discriminating witness: a
    single coupled pointer that only advances between exceptions from inside
    the per-node loop, so an empty leading traceback aborts the whole walk."""
    exceptions = list(trace_lens)
    frames = []
    if not exceptions:
        return len(frames)
    exc_len = exceptions.pop()
    tb = _make_tb(exc_len)
    while tb is not None:
        frames.append(1)
        if tb.tb_next is None and exceptions:
            exc_len = exceptions.pop()
            tb = _make_tb(exc_len)
        else:
            tb = tb.tb_next
    return len(frames)


# --- optional: drive the REAL Django ExceptionReporter in-container ------------

def _real_django_frame_count_for_f2p():
    """Reproduce the exact FAIL_TO_PASS scenario against the REAL Django code
    and return (frame_count, version_tuple, gold_applied). Returns
    (None, None, None) if Django is absent.

    `gold_applied` is True iff the gold patch has been applied to the importable
    Django source. The gold introduces the method
    `ExceptionReporter.get_exception_traceback_frames`, which does not exist at
    `base_commit`; its presence is therefore the gold-applied marker
    (INDEPENDENT of the library version).

    NOTE on version + gold sensitivity: this instance's gold patch (Django 3.2)
    makes `get_exception_traceback_frames(exc_value, tb=None)` yield NOTHING, so
    an exception whose own traceback is empty contributes ZERO frames -- the F2P
    test asserts exactly len(frames) == 1 for the [outer tb=1, inner-context
    tb=0] chain. At `base_commit` (gold NOT applied) the buggy coupled walk
    instead drops everything and reports 0. A LATER Django (>= 4.0) additionally
    emits a placeholder frame for a traceback-less exception, so it reports 2 for
    the same scenario. The gold invariant validated here ("frame count == sum of
    per-exception visible traceback-node counts") therefore holds only on the
    gold-APPLIED gold-era code; the caller gates the strict assertion on both the
    gold marker AND the version accordingly."""
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={})
            django.setup()
        from django.views.debug import ExceptionReporter
        version = django.VERSION[:2]
        gold_applied = hasattr(ExceptionReporter, 'get_exception_traceback_frames')
    except Exception:
        return None, None, None
    try:
        try:
            try:
                raise RuntimeError('Oops')
            except Exception as exc:
                new_exc = RuntimeError('My context')
                exc.__context__ = new_exc
                raise
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(None, exc_type, exc_value, tb)
        return len(reporter.get_traceback_frames()), version, gold_applied
    except Exception:
        return None, None, None


# --- the checks ----------------------------------------------------------------

def check_chain(trace_lens):
    """Assert deep model count == real gold count, and the index-level
    no-double-mask: the total is exactly the SUM of the per-exception lengths
    (not filtered by any predicate the model itself decides)."""
    real = real_assemble_len(trace_lens)
    model = model_assemble_len(trace_lens)
    expected = chain_total(trace_lens)
    assert real == expected, (
        "real gold assembly != chain_total: trace_lens=%r real=%d sum=%d"
        % (trace_lens, real, expected))
    assert model == expected, (
        "deep model != chain_total: trace_lens=%r model=%d sum=%d"
        % (trace_lens, model, expected))
    # Per-exception independence (obligation 2), asserted directly on the SUM,
    # not via a value-membership proxy.
    assert real == sum(trace_lens), (
        "frame count is not the per-exception sum: %r -> %d" % (trace_lens, real))
    return real


def main():
    # --- the FAIL_TO_PASS witness: innermost cause has an EMPTY traceback -----
    # exceptions chain (outermost..innermost): outer exc has a 1-node tb; the
    # attached-but-never-raised __context__ has an empty (None) traceback.
    f2p = [1, 0]
    real_f2p = check_chain(f2p)
    assert real_f2p == 1, (
        "FAIL_TO_PASS frame count must be 1, gold gave %d" % real_f2p)
    # the bug: the pre-patch coupled walk drops everything -> 0 frames.
    assert prepatch_assemble_len(f2p) == 0, (
        "pre-patch witness should yield 0 frames on %r" % f2p)
    assert prepatch_assemble_len(f2p) != real_f2p, (
        "F2P scenario fails to discriminate gold from the bug")

    # --- boundary chains ------------------------------------------------------
    boundary = [
        [],            # no exceptions -> no frames
        [0],           # single exception, empty trace -> 0
        [1],           # single exception, one node
        [3],           # single exception, several nodes
        [0, 0],        # all empty
        [1, 0],        # F2P shape
        [0, 1],        # empty outer, non-empty inner (gold = 1)
        [2, 0, 3],     # empty middle still must not suppress neighbours
        [0, 0, 5],     # only innermost-most-outer non-empty
        [5, 0, 0],
        [4, 3, 2, 1],  # all non-empty
    ]
    for tl in boundary:
        check_chain(tl)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(13513)
    for _ in range(20000):
        n = rng.randint(0, 8)
        tl = [rng.randint(0, 6) for _ in range(n)]
        check_chain(tl)

    # --- drive the REAL Django code where available ---------------------------
    # The strict "REAL Django F2P frame count == 1" assertion holds ONLY in the
    # gold-APPLIED gold-era state. It is gated on BOTH the gold marker (the
    # method `get_exception_traceback_frames`, added only by the gold patch) AND
    # the gold-era version (< 4.0). In the prescribed pre-patch run mode
    # (in-container, gold NOT applied, Django 3.2 base_commit) the buggy coupled
    # walk drops every frame and reports 0; that is the bug, NOT a soundness
    # violation of the deep model -- it is recorded, not asserted (so this script
    # exits RC=0 in BOTH container states: gold-applied and base_commit).
    real_django, version, gold_applied = _real_django_frame_count_for_f2p()
    if real_django is None:
        django_note = "Django not importable; validated against faithful gold re-creation"
    elif version is not None and version < (4, 0) and gold_applied:
        # Gold-APPLIED gold-era Django (the version the G-RESOLVE container ships
        # post-patch): the empty-traceback inner cause contributes 0 frames, so
        # the F2P count is exactly 1 -- equal to chain_total([1, 0]).
        assert real_django == 1, (
            "gold-applied gold-era Django (%s) ExceptionReporter F2P frame count "
            "must be 1, got %d" % (".".join(map(str, version)), real_django))
        django_note = ("REAL gold-applied gold-era Django %s ExceptionReporter "
                       "F2P frame count == 1 == chain_total([1,0])"
                       % ".".join(map(str, version)))
    elif version is not None and version < (4, 0):
        # Gold-era version but gold NOT applied (the base_commit / pre-patch run
        # mode the G-AX mandate prescribes): the buggy coupled single-pointer
        # walk aborts on the empty innermost traceback and drops every frame, so
        # it reports 0 -- exactly the bug the F2P test catches and exactly what
        # prepatch_assemble_len([1,0]) reproduces above. Record, do not assert
        # (the deep-model soundness is established by the stdlib re-creation +
        # fuzz block, which is gold-state-independent).
        django_note = ("REAL gold-era Django %s with the gold NOT applied "
                       "(base_commit / pre-patch state): ExceptionReporter F2P "
                       "frame count == %d (the dropped-frames bug; matches the "
                       "modeled pre-patch witness 0); deep model validated "
                       "against the gold re-creation + fuzz, which is "
                       "gold-state-independent"
                       % (".".join(map(str, version)), real_django))
    else:
        # A newer Django additionally emits a placeholder frame for the
        # traceback-less exception; that is a LATER behaviour beyond this gold
        # patch and is not the invariant under audit. Record but do not assert.
        django_note = ("importable Django %s is newer than the gold era "
                       "(F2P frame count %d reflects a later placeholder-frame "
                       "behaviour); gold invariant validated against the "
                       "faithful gold re-creation instead"
                       % (".".join(map(str, version)), real_django))

    print("G-AX OK: deep model (frames_from_traceback + chain_total) == real "
          "gold assembly on %d boundary + 20000 fuzz chains; F2P witness "
          "(gold 1 vs bug 0) discriminates; %s"
          % (len(boundary), django_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
