# mapping.md — pytest-dev__pytest-10051

Binds every `model.py` symbol to its repository counterpart at
`base_commit = aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `src/_pytest/logging.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `CaptureBuffer` | `LogCaptureHandler` — `src/_pytest/logging.py:331` | the object owning the captured-items list; minimal model carrying only the touched field |
| `CaptureBuffer.items` | `LogCaptureHandler.records` — declared `src/_pytest/logging.py:337` (`self.records: List[logging.LogRecord] = []`) | the captured-items list the reset empties |
| `discard_captured(buf, view)` | the clear path `LogCaptureFixture.clear` → `LogCaptureHandler` reset — `src/_pytest/logging.py:441` (`LogCaptureFixture.clear`) which calls the handler reset (pre-patch `reset`, `:344`; post-patch the new `clear`) | the modeled changed function: empties the captured-items list while preserving its object identity |
| `view` (parameter) | the per-phase reference handed out at `src/_pytest/logging.py:699` (`item.stash[caplog_records_key][when] = caplog_handler.records`), surfaced to user code via `LogCaptureFixture.get_records(when)` at `:388`/`:399` (`return self._item.stash[caplog_records_key].get(when, [])`) | an external observer's reference that aliases the buffer's captured-items list before the reset |
| `append_then_visible(buf, view, item)` | `LogCaptureHandler.emit` — `src/_pytest/logging.py:339` (`self.records.append(record)`) | a subsequently captured item, observed through the still-aliased reference |
| `empty_in_place(xs)` *(axiom — A-consumed)* | Python builtin `list.clear()` — called post-patch in the new `LogCaptureHandler.clear` (`self.records.clear()`); the unchanged in-place list-emptying primitive | the language builtin the reset is built on; empties the list WITHOUT replacing the object |

The relevant pre-/post-patch repo shapes (for the refinement audit; the consumer
spec view names none of these):

* pre-patch `LogCaptureFixture.clear` (`:441`) calls `self.handler.reset()`;
  `LogCaptureHandler.reset` (`:344-345`) does `self.records = []` — **rebinds**
  `records` to a brand-new list, so the previously-handed-out reference (the
  stash entry / `get_records`) is orphaned.
* post-patch adds `LogCaptureHandler.clear` (`self.records.clear(); self.stream
  = StringIO()`) and changes `LogCaptureFixture.clear` to call
  `self.handler.clear()` — `records.clear()` empties the list **in place**,
  preserving its object identity, so the previously-handed-out reference still
  names the buffer's live list.

(`self.stream = StringIO()` is the formatted-text side of the same reset; it is
not part of the captured-items aliasing behaviour the F2P test
`test_clear_for_call_stage` exercises, and `reset`/`clear` both perform it
identically — it is observationally untouched by the bug→fix delta and is not
modeled. See refinement.md §B.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `List[logging.LogRecord]` (the `records` list) | `List[int]` | each captured `LogRecord` ↔ an `int` identity; the tested behaviour observes only how many items are present and whether the observer's list tracks the buffer's list, not record internals. `len`, indexing, `.append`, and object-identity (`is`) are preserved 1:1 by the abstraction. |
| `LogCaptureHandler` object | `CaptureBuffer` minimal class | only the touched field `records` is modeled; `stream`/`level`/base-class state are observationally untouched by the delta (refinement.md §B). |
| the per-phase reference `stash[caplog_records_key][when]` returned by `get_records(when)` | the `view` parameter (a second `List[int]` name) | both are the SAME list object as `handler.records` from the moment of phase wiring (`:699`); modeled by the precondition `view is buf.items`. Object aliasing (`is`) is the carrier of the tested property. |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `empty_in_place` ↔ `list.clear()` (A-consumed)
**Callee:** the Python builtin `list.clear()` (equivalently `del xs[:]`). The
post-patch `LogCaptureHandler.clear` calls `self.records.clear()`. `list.clear`
removes all elements of the list **in place**: it mutates the existing list
object and does **not** rebind the name to a new object, so `id(xs)` is
unchanged and every other reference to that list (here the per-phase
`get_records` reference) observes the now-empty, still-live list. This is the
exact, documented, version-stable behaviour of `list.clear` across all CPython
3.x. Docs: https://docs.python.org/3/tutorial/datastructures.html (list methods);
`list.clear()` "Remove all items from the list. Equivalent to `del a[:]`."

The axiom encodes the **weakest** contract the reset needs:
* `len(xs) == 0` after the call (the list is empty), and
* `xs is Old(xs)` (object identity preserved) — the crux that distinguishes the
  in-place clear from the buggy rebind `xs = []`, and
* `MustTerminate(1)` — the builtin always returns (a single bounded step; CPython
  `list.clear` is O(n) deallocation and cannot diverge). Its measure 1 sits
  strictly below the modeled functions' measure 2 so they may consume the
  primitive but cannot discharge their own termination obligation by
  self-recursion (see refinement.md §C2).

It does NOT claim anything about element values (there are none afterwards) or
about other objects.

**Soundness check (G-AX):** `axiom_check.py` runs the real `list.clear()` on
boundary inputs (empty, singleton, 100-element, heterogeneous) plus 20 000
randomized fuzz lists and asserts, for every observation: the list is empty,
`id(xs)` is unchanged (identity preserved), an alias taken before the clear
still names the now-empty live object, and an item appended afterwards is
visible through that alias. It additionally exhibits the contrast the bug
embodies — that the rebind `xs = []` does NOT preserve identity and orphans a
previously-taken alias — confirming the identity clause is the discriminating
one. It imports only the standard library (`list.clear` is a builtin); nothing
repo-specific. Exit 0 iff sound.
