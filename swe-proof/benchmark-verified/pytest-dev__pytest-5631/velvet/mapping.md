# mapping.md — pytest-dev__pytest-5631

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = cb828ebe70b4fa35cd5f9a7ee024272237eab351`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `src/_pytest/compat.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `countSentinelArgs (entries : List ArgEntry)` | the function counting how many decorator-installed argument bindings replace a mandatory parameter with a sentinel — `src/_pytest/compat.py:62` (body lines 64–73) | the modeled changed function |
| `ArgEntry` | one element of the `function.patchings` sequence (a `unittest.mock._patch` object) | a structure holding only the three touched fields |
| `ArgEntry.isAttribute` | the truthiness of `p.attribute_name` (`compat.py:71`/post-patch `:70`) | non-empty ⇒ the entry is skipped |
| `ArgEntry.valueId` | the object identity `id(p.new)` of the replacement value | identity carrier for the `is`/`in` comparison |
| `ArgEntry.eqTotal` | whether `p.new.__eq__(x)` is total (always returns a bool, never raises) | distinguishes ordinary values from array-like values (problem statement) |
| `CountResult.err` | whether the scan raises `ValueError` (problem statement) | the observable the bug introduces |
| `CountResult.n` | the `int` returned by the function | the count |
| `markerA` / `markerB` | `getattr(sys.modules.get("mock"), "DEFAULT", object())` / `getattr(sys.modules.get("unittest.mock"), "DEFAULT", object())` (post-patch `compat.py:67–68`) | the two mock sentinels, by identity |
| `sentinelCount` | the post-patch list comprehension `len([p for p in patchings if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)])` (`compat.py:70–78` post-patch) | pure spec: the count, by identity |
| `hitsMarker` | the comprehension predicate `not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)` | per-entry counted-membership test, decided by identity |

The pre-patch repo construct the change removes (refinement audit only, not in the
consumer spec view): the `if any(mock_modules): sentinels = [...]; return len([p
... if not p.attribute_name and p.new in sentinels])` block (`compat.py:67–72`),
whose `p.new in sentinels` evaluates `p.new == sentinel` and aborts for array-like
`p.new`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `function.patchings` (a list/tuple of `_patch` objects); `None`/missing ⇒ empty | `List ArgEntry` | sequence ↔ list, element-wise; `len` ↔ `.length`; a function with no `patchings` ↔ `[]` |
| `bool(p.attribute_name)` (a non-empty attribute name string, else `None`/`""`) | `ArgEntry.isAttribute : Bool` | truthy ↔ `true` |
| `id(p.new)` (object identity) | `ArgEntry.valueId : Nat` | distinct objects ↔ distinct `Nat`; the two sentinels ↔ `markerA`/`markerB` |
| “`p.new` has a total `__eq__`” | `ArgEntry.eqTotal : Bool` | total-equality value ↔ `true`; array-like (raises in a truth context) ↔ `false` |
| the function's `int` result | `CountResult.n : Nat` | identity on ℕ |
| “raises `ValueError`” vs “returns normally” | `CountResult.err : Bool` | raises ↔ `err = true` |

Identity is total in both worlds: Python `is` never invokes `__eq__`, and the
Lean `valueId == marker` inspects only the `Nat` id. This is the whole point of
the fix — the model carries `eqTotal` solely to express that the *equality*
comparison the pre-patch used is NOT total.

## 3. Callee provenance

**None.** `countSentinelArgs` models a self-contained scan: attribute-name
truthiness, object-identity comparison against two module-level sentinels, and a
length count. It calls no unchanged external operation whose contract would have
to be assumed, so there are **no axioms** and **no A-reference deep models**
(refinement.md tags every step R or I). G-AX therefore has nothing to validate
and `axiom_check.py` is a (documented) no-axiom pass.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`5631`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates
`hitsMarker`/`sentinelCount` to Python (identity comparison against the two real
sentinels) and diffs against the patched real `num_mock_patch_args`. The impl
region is all-R/I (no A-tagged callee), so `conf_skip = false`.
