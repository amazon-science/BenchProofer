#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-10051 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model's lists are plain Python lists
(List[int]) already, so no PSeq shim is needed. The one @ContractOnly callee,
`empty_in_place`, stands for the unchanged Python builtin `list.clear()`
(mapping.md section 3.1), so the shadow calls that REAL builtin directly.

ORACLE: the REAL patched repo path the model models per mapping.md section 1 —
`_pytest.logging.LogCaptureFixture.clear` routed to the handler-side reset
(`discard_captured`), and `_pytest.logging.LogCaptureHandler.emit`
(`append_then_visible`). The observer reference `view` is realized exactly as
the repo wires it per phase: the stash entry `stash[caplog_records_key][when]`
is set to `handler.records` and surfaced through
`LogCaptureFixture.get_records(when)`. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md section 2): each captured item is an `int` identity in
the model and a `logging.LogRecord` in the repo; the projection carries the
int through the record's message text. `len`, indexing, `.append`, and object
identity (`is`) are preserved 1:1 by the abstraction, and those are the only
observables the spec states, so the comparison is over:
  discard:  (len afterwards, same-object-as-before, view-is-items afterwards,
             projected contents)
  append:   (len afterwards, projected first element, view-is-items,
             len(view), projected view[0])

Input domain: `discard_captured` Requires only that `view` aliases the
buffer's items list (any contents, any length); `append_then_visible`
additionally Requires the list to be empty on entry — which is exactly the
post-state the discard establishes, so each trial composes the two on one
shared handler/buffer pair, mirroring the composed scenario in refinement.md.

>= 1e5 Requires-satisfying inputs: boundary cases + 60000 fuzz trials, each
trial exercising BOTH modeled functions (>= 120000 checked calls total).
Pinned fuzz seed: 10051.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import logging
import random
import sys

SEED = 10051
N_FUZZ = 60_000


# --- shadow: model.py impl region, contracts stripped -------------------------

class CaptureBuffer:
    def __init__(self):
        self.items = []


def empty_in_place(xs):
    # @ContractOnly callee: stands for the REAL unchanged builtin list.clear()
    # (mapping.md section 3.1), so the shadow invokes that builtin itself.
    xs.clear()


def discard_captured(buf, view):
    # buf.items.clear()  -- empty the existing list in place, preserving its
    # object identity (and hence the observer's earlier reference to it).
    empty_in_place(buf.items)
    return


def append_then_visible(buf, view, item):
    buf.items.append(item)
    return


# --- oracle: the real patched repo path ---------------------------------------

def _import_real():
    from _pytest.logging import (
        LogCaptureFixture,
        LogCaptureHandler,
        caplog_handler_key,
        caplog_records_key,
    )
    from _pytest.stash import Stash
    return LogCaptureFixture, LogCaptureHandler, caplog_handler_key, \
        caplog_records_key, Stash


class _FakeItem:
    """Minimal stand-in carrying only the stash the fixture reads; the stash
    entries themselves are the real repo objects (handler + per-phase dict),
    wired exactly the way the plugin wires them for a test phase."""

    def __init__(self, stash):
        self.stash = stash


_RECORD_CACHE = {}


def _make_record(n):
    # one LogRecord per int identity; the message text carries the int so the
    # projection below is a bijection on the identities used in a trial.
    rec = _RECORD_CACHE.get(n)
    if rec is None:
        rec = logging.LogRecord(
            name="conf", level=logging.INFO, pathname=__file__, lineno=1,
            msg=str(n), args=None, exc_info=None)
        _RECORD_CACHE[n] = rec
    return rec


def _proj(rec):
    return int(rec.msg)


def _build_oracle(contents, real):
    """A real LogCaptureHandler holding `contents` (as records), a real
    LogCaptureFixture over it, and the per-phase observer reference obtained
    through the real get_records path."""
    (LogCaptureFixture, LogCaptureHandler, caplog_handler_key,
     caplog_records_key, Stash) = real
    handler = LogCaptureHandler()
    for n in contents:
        handler.records.append(_make_record(n))
    stash = Stash()
    stash[caplog_handler_key] = handler
    # per-phase wiring: the stash entry IS the handler's records list object.
    stash[caplog_records_key] = {"call": handler.records}
    item = _FakeItem(stash)
    try:
        fixture = LogCaptureFixture(item, _ispytest=True)
    except TypeError:
        fixture = LogCaptureFixture(item)
    view = fixture.get_records("call")
    return handler, fixture, view


def _check_trial(contents, new_item, real):
    """Run discard-then-append on shadow and oracle over the same abstract
    input; return an error string on any observable disagreement, else None."""
    # ---- shadow ----
    buf = CaptureBuffer()
    buf.items.extend(contents)
    s_view = buf.items                    # the earlier-handed-out reference
    s_old = buf.items
    discard_captured(buf, s_view)
    s_disc = (len(buf.items), buf.items is s_old, s_view is buf.items,
              list(buf.items))
    append_then_visible(buf, s_view, new_item)
    s_app = (len(buf.items), buf.items[0] if buf.items else None,
             s_view is buf.items, len(s_view),
             s_view[0] if s_view else None)

    # ---- oracle ----
    handler, fixture, o_view = _build_oracle(contents, real)
    o_old = handler.records
    if o_view is not handler.records:
        return ("pre-state wiring broke: get_records view does not alias "
                "handler.records (contents=%r)" % (contents,))
    fixture.clear()
    o_disc = (len(handler.records), handler.records is o_old,
              o_view is handler.records,
              [_proj(r) for r in handler.records])
    # the view identity must also survive through the real get_records path
    o_view_after = fixture.get_records("call")
    handler.emit(_make_record(new_item))
    recs = handler.records
    o_app = (len(recs), _proj(recs[0]) if recs else None,
             o_view is recs, len(o_view),
             _proj(o_view[0]) if o_view else None)

    if s_disc != o_disc:
        return ("discard disagreement on contents=%r:\n  shadow=%r\n  real  =%r"
                % (contents, s_disc, o_disc))
    if o_view_after is not handler.records:
        return ("real get_records after the reset no longer names the live "
                "records list (contents=%r)" % (contents,))
    if s_app != o_app:
        return ("append disagreement on contents=%r item=%r:\n"
                "  shadow=%r\n  real  =%r"
                % (contents, new_item, s_app, o_app))
    return None


def main():
    real = _import_real()
    rng = random.Random(SEED)

    boundary = [
        ([], 0),
        ([], -1),
        ([0], 7),
        ([1, 2, 3], 4),
        (list(range(100)), 100),
        (list(range(5000)), -42),
        ([-1000, 1000, 0, 0, 5], 0),
    ]
    n_checked = 0
    for contents, new_item in boundary:
        err = _check_trial(contents, new_item, real)
        if err:
            print("DISAGREEMENT (boundary): " + err)
            return 1
        n_checked += 2  # both modeled functions exercised

    for _ in range(N_FUZZ):
        n = rng.randint(0, 12)
        contents = [rng.randint(-1000, 1000) for _ in range(n)]
        new_item = rng.randint(-1000, 1000)
        err = _check_trial(contents, new_item, real)
        if err:
            print("DISAGREEMENT (fuzz): " + err)
            return 1
        n_checked += 2

    print("G-CONF OK: shadow == real patched repo path on %d boundary + %d "
          "fuzz trials (%d modeled-function calls, seed %d): reset empties "
          "in place preserving identity, observer view tracks the live list, "
          "and a subsequent capture is visible through it."
          % (len(boundary), N_FUZZ, n_checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
