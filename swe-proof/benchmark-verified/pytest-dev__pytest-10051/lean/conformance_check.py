#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-10051.

The bundle models ONE operation: emptying a record collector without detaching
the views taken onto it — `LogCaptureFixture.clear` rerouted to the new
`LogCaptureHandler.clear` (`self.records.clear()`; in place), as opposed to the
old `reset()` (`self.records = []`; reallocate). (mapping.md / refinement.md.)

The reference discipline that distinguishes the two is visible only through
object *identity* / aliasing, so we model an explicit heap: `cells` is the list
of backing record-lists; `records` and `callView` are indices (object identities)
into it. At phase setup a view is bound to the collector's current cell
(`callView == records`, line 699). `emit` appends in place; `clear` empties the
referenced cell in place, preserving every reference.

The handler's rendered text is modeled too, as `transcript`: `caplog.text` is
`self.handler.stream.getvalue()` (402-404), and emptying the collector must leave
that reading back empty as well (`self.stream = StringIO()`). The sink holds no
inbound references — `getvalue()` is re-read on every access — so only its
contents are compared, never its identity.

ORACLE — a faithful in-process replica of the POST-PATCH semantics: dereference
contents read through `records`/`callView`, with `clear` = empty the referenced
cell in place (CPython `list.clear()`) plus rebind the text sink to a fresh empty
one, references into the heap unchanged.

SHADOW — the op-for-op transliteration of `implementation_clear` (Solution.lean
impl region): `cells.set records []`, then `transcript := []`, references
preserved.

We compare the FULL resulting state: contents of the collector's cell, the
preserved `records`/`callView` references, the contents observed through the view
(the F2P observable), every other cell (frame), and the text read back from the
sink (the P2P observable).

stdlib-only. Pinned seed: 10051 (also in mapping.md).
"""
import random
import sys

SEED = 10051
N = 120_000


def observe(cells, records, callView, sink):
    """The observable projection both legs are compared on: the preserved
    references and the contents read through them, every cell (frame), and the
    text read back from the sink. The sink is projected by its CONTENTS only
    (`getvalue()`), never by identity — no Python object holds a reference into
    it, so its identity is unobservable and pinning it would over-constrain."""
    def deref(ref):
        return list(cells[ref]) if 0 <= ref < len(cells) else []
    return (records, callView, deref(records), deref(callView),
            [list(c) for c in cells], list(sink))


# --- ORACLE: faithful in-process replica of the POST-PATCH `clear` ------------
# `self.records.clear()` empties the existing backing list IN PLACE (object
# identity kept); references unchanged. `self.stream = StringIO()` REBINDS the
# text sink to a fresh empty one, so `getvalue()` reads back nothing.
def oracle2(cells, records, callView, sink):
    cells = [list(c) for c in cells]
    cells[records].clear()
    sink = []                     # rebind to a fresh empty sink
    return observe(cells, records, callView, sink)


# --- SHADOW of implementation_clear (the R legs) ------------------------------
# Mirrors Solution.lean impl region: cells := cells.set records [], then
# transcript := []; refs kept.
def shadow2(cells, records, callView, sink):
    cells = [list(c) for c in cells]
    cells[records] = []
    sink = []
    return observe(cells, records, callView, sink)


def disagree(cells, records, callView, sink):
    got = oracle2(cells, records, callView, sink)
    want = shadow2(cells, records, callView, sink)
    if got != want:
        return (cells, records, callView, sink, got, want)
    return None


def _edge_cases():
    cases = []
    # F2P core: a single cell holding records; the view is aliased to it
    # (callView == records). After clear, both the collector and the view must
    # observe []. (A subsequently appended record would then be seen by both —
    # checked by the post-clear-append edge below.)
    cases.append(([[1, 2, 3]], 0, 0, [1, 2, 3]))
    # multiple phase cells: "setup" cell must be left untouched (frame); the
    # "call" cell is cleared and its view aliased to it.
    cases.append(([[10], [1, 2, 3]], 1, 1, [10, 1, 2, 3]))
    # already-empty collector, and a sink that already reads empty
    cases.append(([[]], 0, 0, []))
    # several cells, clear the middle, views aliased to it
    cases.append(([[1], [2, 3], [4, 5, 6]], 1, 1, [1, 2, 3, 4, 5, 6]))
    # P2P core (`test_clear` asserts `not caplog.text`): the sink has rendered
    # text from entries the collector recorded, and must read back empty after.
    cases.append(([[1, 2, 3]], 0, 0, [9, 9, 9]))
    # sink holding text rendered from cells OTHER than the collector's: the sink
    # is a single accumulating stream, so it reads empty regardless of which cell
    # the text came from.
    cases.append(([[1], [2]], 0, 0, [2, 2, 2]))
    return cases


def _post_clear_append_consistency(rng):
    """Directly exercise the F2P invariant: after clear, a record appended to the
    collector's cell is visible through the aliased view, and the view tracks the
    collector. Also exercises the P2P invariant on the same trace: the text read
    back is empty right after the clear, and thereafter reflects only what was
    emitted AFTER it. Compares oracle vs shadow including the append step."""
    for _ in range(20_000):
        ncells = rng.randint(1, 5)
        cells = [[rng.randint(0, 99) for _ in range(rng.randint(0, 4))]
                 for _ in range(ncells)]
        records = rng.randrange(ncells)
        callView = records                # setup invariant: view aliases collector
        sink = [x for c in cells for x in c]   # text rendered so far

        def run(clear_fn):
            c = [list(x) for x in cells]
            s = list(sink)
            s = clear_fn(c, records, s)
            new_rec = records             # both legs preserve the reference
            text_right_after = list(s)    # `caplog.text` immediately after clear
            c[new_rec].append(777)        # emit after clear (in-place append)
            s.append(777)                 # ...which also renders into the sink
            # view observes the collector's cell iff it still names it
            return (list(c[new_rec]),
                    list(c[callView]) if callView == new_rec else "DETACHED",
                    text_right_after, list(s))

        # both legs ignore the incoming sink: whatever it held, the text reads
        # back empty afterwards (`_s` is taken only to keep the signatures alike)
        def oracle_clear(c, r, _s):
            c[r].clear()
            return []                     # self.stream = StringIO()
        def shadow_clear(c, r, _s):
            c[r] = []
            return []                     # transcript := []
        if run(oracle_clear) != run(shadow_clear):
            return (cells, records, callView, sink)
    return None


def main() -> int:
    checked = 0
    for cells, records, callView, sink in _edge_cases():
        d = disagree(cells, records, callView, sink)
        if d:
            print(f"DISAGREE edge: oracle={d[4]} shadow={d[5]} "
                  f"cells={d[0]} records={d[1]} callView={d[2]} sink={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ncells = rng.randint(1, 6)
        cells = [[rng.randint(0, 99) for _ in range(rng.randint(0, 5))]
                 for _ in range(ncells)]
        records = rng.randrange(ncells)
        # the modeled setup invariant aliases the view to the collector, but we
        # also fuzz independent views (callView != records) to exercise the frame
        # clause (a non-aliased view's cell must be untouched).
        callView = records if rng.random() < 0.6 else rng.randrange(ncells)
        # the sink is fuzzed INDEPENDENTLY of the cells (usually text rendered
        # from what was recorded, sometimes arbitrary or already-empty), so the
        # comparison cannot be satisfied by any relation between the two.
        roll = rng.random()
        if roll < 0.5:
            sink = [x for c in cells for x in c]
        elif roll < 0.8:
            sink = [rng.randint(0, 99) for _ in range(rng.randint(1, 6))]
        else:
            sink = []
        d = disagree(cells, records, callView, sink)
        if d:
            print(f"DISAGREE fuzz: oracle={d[4]} shadow={d[5]} "
                  f"cells={d[0]} records={d[1]} callView={d[2]} sink={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    fail = _post_clear_append_consistency(rng)
    if fail:
        print(f"DISAGREE post-clear-append: {fail}")
        print("status=fail")
        return 1

    print(f"checked={checked} (+post-clear-append) disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
