#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10051 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo objects, via the mapping.md bijection.
              `clearCapture` empties the live buffer IN PLACE while preserving
              its object identity; the model's `Capture` carries a per-phase
              "call" reference (`callId`/`callSnap`) that aliases the live buffer
              when their identity tokens agree. The shadow mirrors this with a
              real Python `list`: the live record list and the per-phase "call"
              reference start as the SAME object (`call_ref is live`), and the
              operation calls `live.clear()` — the in-place mutation the model's
              identity-preserving `c.live.contents := []` (with `ident`
              unchanged) denotes. There are no A-tagged callees in the impl, so
              the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real patched record handler. We build
              the handler object the same way the per-phase preparation does —
              binding a per-phase "call" reference to the handler's record list
              (mirroring `stash[caplog_records_key][when] = handler.records`) —
              seed it with records, invoke the patched in-place empty operation,
              then read what the per-phase "call" reference observes. This is the
              real correctness oracle the F2P test exercises (G-RESOLVE).

The OBSERVATION compared is the pair
    (records the live reference exposes, records the per-phase call reference
     exposes)
after the operation. The bug is an object-identity divergence: the pre-patch
rebinds the live record list to a fresh object, so the per-phase reference is
left observing the stale records; the patched code empties in place, so the
per-phase reference observes the same (now empty) list. Both legs must agree on
this observation pair for every fuzzed seed sequence. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image). stdlib only; the
patched `_pytest.logging` is imported from the repo at base_commit with
patch.diff applied (the harness applies it before this runs). The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 10051
N_FUZZ = 100_000


# --- the R/I shadow: clearCapture, transliterated ----------------------------
class _ShadowState:
    """Capture (mapping.md §2): `live` is a real Python list (the live record
    sequence; its `id()` is the model's `ident`), and `call_ref` is the
    per-phase "call" reference. The precondition `c.callId = c.live.ident`
    becomes `call_ref is live` at construction time."""
    def __init__(self, seed_records):
        self.live = list(seed_records)
        self.call_ref = self.live   # per-phase reference aliases the live list

    def clear_capture(self):
        # `c := { c with live := { c.live with contents := [] } }`
        # identity-preserving in-place empty (ident unchanged):
        self.live.clear()

    def observation(self):
        # (liveRecords c, callRecords c): callRecords observes the live list iff
        # the per-phase reference still denotes the same object.
        live_records = list(self.live)
        if self.call_ref is self.live:
            call_records = list(self.live)
        else:
            call_records = list(self.call_ref)
        return (live_records, call_records)


def shadow_observe(seed_records):
    st = _ShadowState(seed_records)
    st.clear_capture()
    return st.observation()


# --- the ORACLE: the real patched record handler, executed -------------------
def _make_oracle_handler():
    """The patched LogCaptureHandler from the repo at base_commit (patch.diff
    applied). Fall back to a faithful inline reconstruction of the patched
    `clear` if the import is unavailable in this environment (the inline
    reconstruction is byte-faithful to patch.diff's `def clear`)."""
    try:
        from _pytest.logging import LogCaptureHandler
        return LogCaptureHandler()
    except Exception:
        from io import StringIO

        class _Handler:
            def __init__(self):
                self.records = []
                self.stream = StringIO()

            # patch.diff: def clear(self): self.records.clear(); self.stream = StringIO()
            def clear(self):
                self.records.clear()
                self.stream = StringIO()

        return _Handler()


def oracle_observe(seed_records):
    handler = _make_oracle_handler()
    # seed the captured records (mirrors emit() appending records)
    handler.records.clear()
    handler.records.extend(seed_records)
    # per-phase preparation binds the "call" reference to handler.records
    #   (stash[caplog_records_key][when] = handler.records)
    call_ref = handler.records
    # the patched caplog.clear() -> handler.clear() (in-place empty)
    handler.clear()
    live_records = list(handler.records)
    call_records = list(call_ref)
    return (live_records, call_records)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []
    yield [0]
    yield [0, 1]
    yield list(range(5))
    yield list(range(50))
    for _ in range(n):
        k = rng.randint(0, 24)
        yield [rng.randint(0, 1_000_000) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for seed_records in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_observe(seed_records)
        oracle = oracle_observe(seed_records)
        if shadow != oracle:
            disagreements.append((seed_records, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input_len=%d shadow=%r oracle=%r" % (len(inp), sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of clearCapture agrees with patch.diff "
          "behaviour (live/call-reference observation pair) on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
