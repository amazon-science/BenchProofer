# mapping.md — sphinx-doc__sphinx-7889

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ec9af606c6cfa515f946d74da9b51574f2f9b16f`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each modeled callee.

Repo file under change: `sphinx/ext/autodoc/mock.py`.
`spec_provenance: cold` (derived from problem_statement + gold patch + repo
source only).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `subscriptMock (displayName : String) (key : Key)` | `_MockObject.__getitem__(self, key)` — `sphinx/ext/autodoc/mock.py:55` | the modeled changed function (mock subscription) |
| `Key` (`str` / `obj`) | the `key` argument's runtime value (`Any`) | a value that is either already textual (`str`) or a non-textual object carrying a textual form (e.g. a `TypeVar`) |
| `textForm (k : Key)` | the builtin `str(key)` coercion **introduced by the patch** | the textual form of any key; `str` of a string is itself, `str` of a non-textual object is its text rendering |
| `buildSubclass (module : String) (name : Key)` *(deep model — A-reference)* | `_make_subclass(name, module, ...)` — `sphinx/ext/autodoc/mock.py:71` | unchanged callee: constructs a subclass whose `__display_name__` is `module + '.' + name`; **requires `name` to be textual** (else `TypeError`) **and admissible as a class name** — `type(name, ...)` rejects a name containing a NUL byte with `ValueError` (modeled by `nameRejected`/`MockErr.valueError`). Validated `buildSubclass == _make_subclass` by axiom_check.py (G-AX). |

`textForm` is the operation the patch **adds** (`str(key)`); it is an I/R op
modeled deeply (concrete), not an axiom. `buildSubclass` is the **unchanged**
callee `_make_subclass`, modeled deeply (its display-name computation and its
textual-name requirement spelled out) and validated against the real callee by
G-AX — an **A-reference**, not a consumed axiom. There are no consumed axioms.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-AX (§3) and G-CONF (§4.1) use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the key argument (`Any`) | `Key` | a Python `str s` ↔ `Key.str s`; any non-`str` object `o` ↔ `Key.obj (str(o))` carrying its `str()` rendering |
| `str(key)` (the coercion) | `textForm : Key → Key` | `str(s) == s` for a `str` ↔ `textForm (.str s) = .str s`; `str(o)` for a non-str ↔ `textForm (.obj r) = .str r` |
| `self.__display_name__` (a `str`) | `displayName : String` | identity on the string content |
| the constructed subclass's observable `__display_name__` | `String` | `type(result).__display_name__` ↔ the `String` `buildSubclass` returns on success; `module + '.' + name` ↔ `module ++ "." ++ name` |
| a raised `TypeError` (non-textual name) | `Except.error MockErr.typeError` | the callee raising `TypeError` ↔ the `typeError` leg |
| a raised `ValueError` (textual name with a NUL byte, refused by `type()`) | `Except.error MockErr.valueError` | the callee raising `ValueError` ↔ the `valueError` leg |
| no error, a mock subclass produced | `Except.ok name` | the callee returning a class ↔ `Except.ok` carrying its display name |

The instance is then constructed (`_make_subclass(...)()`); instantiation does
not alter `__display_name__`, which is the only field the modeled behavior and
the F2P test's success depend on, so it is identity on the carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `buildSubclass` deep model ↔ `_make_subclass` (A-reference)
**Callee:** `sphinx/ext/autodoc/mock.py:71` (unchanged by the patch):

```python
def _make_subclass(name, module, superclass=_MockObject, attributes=None):
    attrs = {'__module__': module, '__display_name__': module + '.' + name}
    attrs.update(attributes or {})
    return type(name, (superclass,), attrs)
```

Three observable facts the deep model `buildSubclass` encodes:
* when `name` is textual (`str`) **and admissible** (no NUL byte), it succeeds and
  the result's `__display_name__ == module + '.' + name` (modeled
  `Except.ok (module ++ "." ++ s)`);
* when `name` is textual but **inadmissible** — it contains a NUL byte —
  `type(name, ...)` raises `ValueError` ("type name must not contain null
  characters"); this is the ONLY textual rejection (every other textual name,
  incl. empty/accented/whitespace/other control chars, is accepted). Modeled
  `Except.error .valueError` via `nameRejected s = s.contains (Char.ofNat 0)`;
* when `name` is **not** textual, both `module + '.' + name` (str + non-str) and
  `type(name, ...)` (argument 1 must be `str`) raise `TypeError` (modeled
  `Except.error .typeError`).

This requirement is the reason the bug exists: the pre-patch `__getitem__` passed
the raw `key` (which may be non-textual) straight into this callee.

**Soundness check (G-AX):** `axiom_check.py` runs the real `_make_subclass`
(imported from the repo, in-container) on textual names (boundary + fuzz, the
fuzz alphabet now **including NUL and other control bytes**) — asserting
`__display_name__ == module + '.' + name` for admissible names and `ValueError`
for NUL-byte names — and on non-textual names (`TypeVar`, `int`, `type`, `list`,
a NUL-`__str__` object, …) — asserting it raises `TypeError`. It also confirms
`str()` on those objects yields exactly the textual form `textForm` assumes (and
that a coerced NUL-rendering routes to `valueError`). stdlib + repo import only;
exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7889`**. The R/I shadow
transliterates `textForm` (the `str()` coercion, an I op) and leaves the
A-tagged callee `buildSubclass` as the **real** `_make_subclass`; it observes
`type(result).__display_name__` against the patched `__getitem__` oracle over
≥10⁵ fuzzed keys (strings and non-textual objects). Exit 0 iff zero
disagreements.
