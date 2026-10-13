# mapping.md — pytest-dev__pytest-10051

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = aa55975c7d3f6c9f6d7f68accc41bb7cadf0eb9a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `src/_pytest/logging.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clearCapture (mut c : Capture)` | the log-capture clear path: `LogCaptureFixture.clear` (`src/_pytest/logging.py:441`) delegating to the record handler's in-place empty operation (`src/_pytest/logging.py:344`, the method added by the patch) | the modeled changed function — empty the captured record sequence for the current phase |
| `Capture.live` | the record handler's `records` list attribute (`src/_pytest/logging.py:337`, appended to by `emit` at `:341`, exposed by the `records` property at `:409`) | the live buffer the machinery appends to and exposes |
| `Capture.callId` / `Capture.callSnap` | the per-phase reference stored at phase preparation: `item.stash[caplog_records_key][when] = caplog_handler.records` (`src/_pytest/logging.py:699`), read back by `get_records(when)` (`src/_pytest/logging.py:399`) | the per-phase "call" reference and the records it would expose were it detached |
| `Buffer.ident` | Python object identity (`id()`) of the `records` list object | identity token: equal ⇔ same list object |
| `Buffer.contents` | the elements of that `records` list | the captured record sequence |
| `liveRecords` / `callRecords` | the record sequences observed through the live reference / through `get_records(when)` respectively | pure observations the F2P test compares |

The repo symbol the patch's behaviour hinges on (audit only, not in the consumer
spec view): the pre-patch record-buffer empty rebinds the list
(`self.records = []`, `src/_pytest/logging.py:345`); the patched empty mutates in
place (`self.records.clear()`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `LogRecord` instance (only presence/sequence position is observed) | `Rec := Nat` | each captured record ↔ an opaque token; only the *sequence* (length, emptiness, order) is observed, never a record's fields. F2P compares `caplog.get_records("call") == []` / `== caplog.records` — sequence-level. |
| the `records` `list` object | `Buffer` (`ident` = `id(records)`, `contents` = its elements) | a Python list ↔ a `Buffer`; `records.clear()` (in-place) ↔ `{ b with contents := [] }` (same `ident`); `records = []` (rebind) ↔ a `Buffer` with a fresh `ident`. Object identity is the observable that distinguishes the two. |
| the per-phase reference `stash[caplog_records_key][when]` bound to `handler.records` at phase prep | `callId` (the identity it was bound to) + `callSnap` (what it would expose if detached) | `get_records(when)` returns that stored reference; it observes the live records iff it is still the same object (`callId = live.ident`), else its own (stale) contents. The precondition `c.callId = c.live.ident` is the post-setup invariant `stash[...][when] is handler.records`. |
| `caplog.clear()` / handler in-place empty returning `None` | `clearCapture` returning `Unit` | the operation is invoked for its effect on the capture state; no value is produced. |

The precondition `require c.callId = c.live.ident` faithfully encodes the
machine state the F2P test starts from: during phase setup the per-phase "call"
reference is bound to the very list the handler exposes (`stash[...][when] =
handler.records`), so the two references denote the same object on entry. The
spec then demands that the clear preserve that aliasing (identity frame) and
empty the shared sequence.

## 3. Callee provenance (kind-A) — none

There are **no axiomatized callees and no deep-model A-references** in this
bundle (meta.json `axioms = []`, `deep_model_references = []`). The modeled
operation is a self-contained state mutation spelled out directly over the
observable capture state; it consumes no unchanged-callee contract. `axiom_check.py`
is therefore a `status=skip` stub.

The single sub-operation the patch keeps verbatim — replacing the formatted-text
stream with a fresh empty one (`self.stream = StringIO()`) — is identical
pre- and post-patch and is orthogonal to the records-aliasing behaviour the spec
pins; it is not part of the modeled carrier (the F2P clause under test reads
`get_records`/`records`, not `text`), so no callee contract is needed for it.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10051`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `clearCapture` to Python over a real `list` object: it binds the
per-phase "call" reference to the same list the live reference exposes
(`call_ref is live`, the precondition), invokes the in-place empty
(`live.clear()`), and reads back the live/call-reference observation pair. There
are no A-tagged callees in the impl, so the shadow is pure R/I; the oracle is the
real patched handler's in-place empty (patch.diff applied at base_commit).
