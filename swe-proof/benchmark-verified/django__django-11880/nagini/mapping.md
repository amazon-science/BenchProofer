# mapping.md — django__django-11880

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 06909fe084f87a65459a83bd69d7cdbe4fce9a7c`, states the type
abstraction, and gives the provenance of the one callee the deep model is
validated against (the A-reference; there are no consumed axioms).

Repo file under change: `django/forms/fields.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deep_duplicate(self)` | `Field.__deepcopy__(self, memo)` — `django/forms/fields.py:198-203` | the modeled changed function (form-field duplication) |
| `Field` / `self.msg_codes`, `self.msg_values` | the `Field` instance `self` and its `error_messages` attribute — a `dict` from error code to message (`django/forms/fields.py:107-111` in `Field.__init__`, mutated/read across forms) | the per-field message-override mapping the fix copies; modelled as two index-aligned lists |
| `self.validators` | the `Field.validators` attribute — a `list` of validator callables (`django/forms/fields.py:113`) | the per-field validator collection (already copied before the change) |
| `result` / `Result()` | `result` in `__deepcopy__`, the duplicated field (`copy.copy(self)` then re-bound collections), returned at `fields.py:203` | the produced duplicate field |
| `memo` (not modelled) | the `copy.deepcopy` memo dict argument (`fields.py:198,200`) | deep-copy bookkeeping, unchanged by the patch, outside scope |

The gold patch (the one change, `fields.py:202`) inserts, between the
`result.widget = copy.deepcopy(self.widget, memo)` line and
`result.validators = self.validators[:]`, the statement
`result.error_messages = self.error_messages.copy()` — modelled by the
`msg_codes`/`msg_values` copy loop producing a distinct, equal-content
collection. Pre-patch, that statement is absent and `result.error_messages`
remains the dict `copy.copy(self)` aliased from `self`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `Field` instance | `Field` instance | a minimal class carrying only the two touched mutable collections |
| `self.error_messages` (a `dict` code→message) | two index-aligned `List[int]`: `self.msg_codes` (codes) and `self.msg_values` (messages) | entry `code↦message` ↔ a pair `(msg_codes[k], msg_values[k])`; the tested behaviour observes only WHICH codes are present, the value bound to each, and crucially that the duplicate's collection is a SEPARATE object — all faithfully carried by the two parallel lists. `dict.copy()` (distinct object, same entries) ↔ copying both lists into the result's own fresh lists. The actual message/code *strings* are opaque identity tokens (`int`); the F2P assertion is `assertIsNot(...)` (object identity) plus implicit content preservation, never a specific string. |
| `self.validators` (a `list` of validators) | `self.validators: List[int]` | validator identities as `int` tokens; `list[:]` (distinct list, same elements in order) ↔ the element-by-element copy loop into the result's own fresh list |
| `result = copy.copy(self)` (shallow base) then per-collection re-binds | `result = Field()` filled by the copy loops | the change's behaviour is the per-collection re-binding to fresh independent copies; the shallow-shared scalar/immutable attributes (`required`, `label`, `initial`, `widget`, …) are unchanged by the patch and observe no tested behaviour of *this* change, so they are omitted (the model's `result` owns exactly the two collections the change governs) |
| object identity `field_copy.error_messages is not field.error_messages` | `Result().msg_codes is not self.msg_codes` and `Result().msg_values is not self.msg_values` | Python object distinctness ↔ Nagini reference distinctness, provable from the separation of a full `Acc(list_pred(Result().msg_codes))` against the original's retained `Acc(list_pred(self.msg_codes), 1/2)` |

Nagini bans `str` indexing and rich object graphs, and the `error_messages`
dict is observed by the change only as "a separate object holding the same
entries"; two index-aligned `List[int]` are the faithful carrier. This is sound
because `dict.copy()` produces exactly a distinct object with equal entries, and
the F2P test observes precisely object distinctness (`assertIsNot`) — see §3.1
and axiom_check.py.

## 3. Callee provenance (the A-reference — checked by G-AX / axiom_check.py)

### 3.1 `dict.copy()` / `list[:]` — distinct object, equal contents (A-reference)

There is **no consumed `@ContractOnly` axiom**. The duplication is modelled
deeply (the two copy loops). The only callee semantics the refinement relies on
is that the shallow-copy primitives the patch uses —

  * CPython `dict.copy()` (`{...}.copy()`), and
  * CPython list slice `list[:]`

— each return a **distinct object** holding the **same contents** as the source
(same key→value entries / same elements in order), so that mutating the copy
does not reach the original. This is standard, documented CPython behaviour
(`dict.copy()`: "Return a shallow copy of the dictionary";
list slicing returns a new list). It is the **A-reference** the deep model
(`Result().msg_codes/msg_values/validators is not self.*` + per-index content
equality) is validated against, not an axiom the proof consumes.

**Soundness check (G-AX):** `axiom_check.py`
  (a) confirms the A-reference primitives directly: 5000 randomized
      `dict.copy()` and `list[:]` observations, each asserting
      `copy is not original`, `copy == original`, and that mutating the copy
      leaves the original unchanged; then
  (b) executes the REAL post-patch Django `Field.__deepcopy__` (the very method
      the patch lives in) on a spread of field types and explicit
      `error_messages` overrides — including the exact F2P scenario (a
      `CharField` subclass setting `error_messages` in `__init__`) — and asserts
      for every duplicate that `error_messages`/`validators` are DISTINCT
      objects holding equal contents, the original is left untouched, and
      mutating the duplicate's overrides does not reach the original (and vice
      versa). 200 fuzz fields over random override-code subsets. Exit 0 iff
      every obligation holds.

The check is **discriminating**: run against a pre-patch Django (the
`error_messages.copy()` line removed) it fails on the first observation with
`AssertionError: deepcopy shared the error_messages dict (the bug)` (verified
during construction); against post-patch Django it passes over 209 observations.
It imports only `copy`/`random` and Django itself (the module the patch lives
in); nothing test-private. Outside the container Django is absent, so it prints
`G-AX SKIP` (after confirming the primitive A-reference semantics) and returns 0;
the orchestrator runs the full check in-container.

The A-reference is flag-independent: `dict.copy()` and `list[:]` have the same
distinct-object semantics on every supported CPython.
