# mapping.md — pytest-dev__pytest-10051

## Symbol binding (file:line @ base_commit aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_clear` / `problem_spec_clear` / `correct_clear` | `LogCaptureFixture.clear` → `LogCaptureHandler.clear` (the new method the patch adds and routes `clear` to) | `src/_pytest/logging.py` — `LogCaptureFixture.clear` at 441-443; new `LogCaptureHandler.clear` added at 344 (post-patch) |
| `HandlerState` (structure) | the handler's record storage + the per-phase views onto it | `LogCaptureHandler.records` (337), `item.stash[caplog_records_key][when]` (699) |
| `HandlerState.cells` | the universe of backing `list[LogRecord]` objects that exist | the actual Python list objects |
| `HandlerState.records` | which backing list `handler.records` currently *is* (object identity) | `LogCaptureHandler.records` attribute binding |
| `HandlerState.callView` | which backing list `get_records("call")` was bound to at setup | `item.stash[caplog_records_key]["call"]` |
| `HandlerState.transcript` | the rendered text the handler has emitted, as read back by `caplog.text` | `LogCaptureHandler.stream` (a `StringIO`, 336) read via `LogCaptureFixture.text` → `self.handler.stream.getvalue()` (402-404) |
| `HandlerState.deref` | dereference: read the contents of a backing list given its identity | reading `list` contents |

## What the code does (base_commit) and the bug

At the start of each test phase, `LoggingPlugin._runtest_for` runs:

```python
caplog_handler.reset()
item.stash[caplog_records_key][when] = caplog_handler.records   # line 699
```

So `get_records(when)` (which returns `item.stash[caplog_records_key].get(when, [])`,
line 399) is bound to **the very same list object** as `handler.records`
(property at 407-409). They are two references to one list.

`LogCaptureHandler.emit` (339-342) does `self.records.append(record)` — an
**in-place** mutation — so a record logged during the phase is visible through
both references.

`caplog.clear()` (441-443) calls `self.handler.reset()`, and `reset()` (344-346)
does:

```python
self.records = []          # REBINDS the attribute to a fresh list object
self.stream = StringIO()
```

This **reallocates**: `handler.records` now names a new empty list, while
`get_records("call")` still names the OLD list (which keeps its records). The two
references diverge — `get_records("call")` is frozen on the stale list, no longer
reflecting `caplog.records` and no longer receiving records appended afterwards.

## The fix

The patch adds a dedicated `LogCaptureHandler.clear` (344-346 post-patch):

```python
def clear(self) -> None:
    self.records.clear()       # IN-PLACE empties the existing list object
    self.stream = StringIO()
```

and routes `LogCaptureFixture.clear` to `self.handler.clear()` instead of
`self.handler.reset()`. `list.clear()` empties the list **in place**, so the
backing object's identity is unchanged: every reference still bound to it
(`get_records("call")`) now observes the emptied list, and observes records
appended later, restoring `get_records("call") == caplog.records`.

Note that `clear()` retains the second line of `reset()`, `self.stream =
StringIO()`. That line is not decoration: `caplog.text` is
`_remove_ansi_escape_sequences(self.handler.stream.getvalue())` (402-404), and
`testing/logging/test_fixture.py::test_clear` (144-151) asserts **both**
`not len(caplog.records)` and `not caplog.text` immediately after
`caplog.clear()`. A `clear()` that only emptied the records list would satisfy
the new-behaviour test and break that one, so emptying the collector must be
total: the rendered text must read back empty too. Hence `transcript` is a
modeled component and not an omitted detail.

(The patch's only other change is deleting a stray blank line near the imports —
behaviourally inert.)

## Lean modeling

The observable difference between `reset()` (rebind) and `clear()` (in-place) is
NOT visible in record *values* — both leave the handler holding `[]`. It is
visible only through **object identity / aliasing**: whether a previously-taken
view still tracks the collector. A pure-value Lean model would erase exactly the
property under test. So the heap is modeled explicitly:

- `HandlerState.cells : List (List Nat)` — the heap of backing lists; a log
  record is modeled by its identity (`Nat`), since only presence/identity, never
  record fields, is observed.
- `HandlerState.records : Nat` — an index into `cells`: which cell
  `handler.records` currently *is*.
- `HandlerState.callView : Nat` — the index `get_records("call")` was bound to at
  phase setup.
- `HandlerState.transcript : List Nat` — the rendered text the handler has
  accumulated, as `caplog.text` reads it back. It is a pure write **sink**: no
  Python object retains a reference into it (`caplog.text` calls `getvalue()`
  afresh on each access), so unlike the record cells its identity is not
  observable and only its contents are modeled. Rendered text is abstracted to
  the identities of the records rendered into it, which is all any assertion in
  the test suite distinguishes here (`test_clear` asserts only emptiness).

Reading a backing list by identity is `s.cells[ref]?` (`some contents` when the
object is present, `none` when the reference names no live object) — the spec
addresses cells by `getElem?` precisely so a *present empty* backing list is
never confused with an *absent* one (object identity is preserved, not just
contents).

The setup aliasing `stash[...]["call"] = handler.records` (line 699) is the
precondition `s.callView = s.records` in `correct_clear` (the view is taken onto
the collector's *current* cell). `s.records < s.cells.length` is the precondition
that the collector's reference is live.

The post-patch `clear()` is modeled as `cells := cells.set records []` — edit the
referenced cell **in place**, leaving `records` (and `callView`) pointing where
they were — together with `transcript := []`, the rendered text reading back
empty. Both legs are required by the spec: clauses 1/4/5/6 pin the reference
discipline, clause 7 pins the transcript. The buggy `reset()` is modeled in
`Solution_prepatch.lean` as
`cells := cells ++ [[]]; records := cells.length` — allocate a fresh empty cell
and **repoint** `records` at it, leaving `callView` naming the old (still
populated) cell.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| set of live backing `list` objects | `cells : List (List Nat)` | each cell = one backing list; index = object identity |
| a `LogRecord` (only its identity matters) | `Nat` | identity tag |
| `handler.records` (which object) | `records : Nat` | index of the bound cell |
| `get_records("call")` (which object) | `callView : Nat` | index of the bound cell |
| reading a list by identity | `cells[ref]?` | `some contents` if present, `none` if absent |
| `lst.clear()` (in place) | `cells.set records []` | same index, emptied contents |
| `self.records = []` (rebind) | `cells ++ [[]]; records := old length` | new index, old cell untouched |
| `stash["call"] = handler.records` at setup | precondition `callView = records` | view aliases the collector's cell |
| `handler.stream.getvalue()` (what `caplog.text` reads) | `transcript : List Nat` | rendered text ↔ identities rendered into the sink; contents only, no identity |
| `self.stream = StringIO()` (text reads back empty) | `transcript := []` | sink reads empty; any route to empty is equivalent, since nothing references the sink |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behaviour the patch changes —
  in-place empty vs. reallocate, and its effect on a coupled view — is modeled
  DEEPLY as operations on the explicit heap (`cells.set` vs `cells ++`/repoint).
  SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so the `axioms`
  region is empty and **G-AX skips**.
- `list.append` (in `emit`) and `list.clear` are CPython builtins with in-place
  semantics; modeled directly (append = cons/snoc onto a cell, clear = set cell
  to `[]`), not axiomatized.
- No flag dependence: `clear()` takes no arguments and always empties.

## G-CONF fuzz seed

Pinned LCG seed: **10051** (see `conformance_check.py` `SEED`). The corpus fuzzes
a heap of cells, a live `records` index, a `callView` aliased to it (the setup
invariant), and a transcript sink, then applies the shadow of
`implementation_clear` and an oracle replica of the post-patch semantics,
comparing the full resulting state (the emptied cell, the preserved references,
the view's observed contents, the untouched other cells, and the text read back
from the sink) over ≥1e5 fuzzed inputs. Edge cases pin the F2P scenario: a view
aliased to a non-empty collector, cleared, must still observe the now-empty
collector and see a subsequently appended record; and the P2P scenario: the text
read back after clearing is empty even when the collector had recorded entries.
