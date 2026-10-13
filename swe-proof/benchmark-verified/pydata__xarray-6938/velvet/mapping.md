# mapping.md — pydata__xarray-6938

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c4e40d991c28be51de9ac560ce895ac7f9b14924`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the modeled callees.

Repo file under (behavioural) change: `xarray/core/variable.py`.

## 0. What the change actually is

The patch touches three things. Only ONE is behaviourally observable (and the
only thing the F2P test exercises); the rest are inert type annotations and a
private-attribute rename:

1. **Behavioural fix (modeled):** `IndexVariable.to_index_variable`
   (`xarray/core/variable.py:2882`) changes its body
   `return self` → `return self.copy()`. Pre-patch it returned the SAME object
   (an alias); post-patch it returns a fresh, independent copy. The F2P test
   `TestIndexVariable::test_to_index_variable_copy` constructs an
   `IndexVariable`, calls `.to_index_variable()`, asserts the result `is not`
   the source, mutates the result's `.dims`, and asserts the source's `.dims`
   is unchanged. This is a pure object-identity / heap-aliasing property.
2. **Inert — type annotations only:** return-type hints added to
   `to_base_variable`, `to_index_variable` (base `Variable`), `to_index`,
   `level_names`, `name`, `name.setter`, and the `NoReturn` import. No runtime
   effect (Python does not enforce annotations); not observed by any F2P/P2P.
3. **Inert — private-attribute rename:** in `Variable.to_base_variable` /
   `Variable.to_index_variable` and `Dataset.swap_dims`, `self.dims` →
   `self._dims` / a local annotation. `dims` is a `@property` returning
   `self._dims` (`variable.py:573`), so reading `self.dims` and `self._dims`
   are observationally identical; behaviour-preserving.

The spec models exactly item 1, the bug the issue reports and the F2P test
pins. Items 2–3 are recorded here for the refinement audit; they carry no
behaviour and appear in no `ensures`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reifyIndependent (self : Handle) (mut store) (mut nextFresh)` | `IndexVariable.to_index_variable(self)` — `xarray/core/variable.py:2882` | the modeled changed method: return this object as an (independent) variable |
| `Handle := Int` | the *identity* of a Python object (`id(obj)`) | object address; distinct objects have distinct handles |
| `Store := Handle → Payload` | the heap slice mapping each live object to its mutable per-object state | the explicit store (heap-as-function, per the Velvet memory examples) |
| `Payload := List Int` | the mutable per-object state a caller can later overwrite — concretely `IndexVariable.dims` (a tuple), the field the F2P test mutates | object state observed for aliasing |
| `nextFresh : Handle` | the allocation frontier (a fresh `id` is distinct from every live one) | `self.copy()` allocates a new object ⇒ a new identity |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate between the Lean value
domain and the Python repo. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a Python object's *identity* (`id(obj)`) | `Handle` (`Int`) | each distinct live object ↔ a distinct `Handle`; `a is b` ↔ `handle a = handle b`; a freshly-allocated object ↔ `nextFreshOld` (above every live handle) |
| the object's mutable state (`obj.dims`, a tuple of hashables) | `Payload` (`List Int`) | tuple of dimension names ↔ list of small int tags; the F2P test mutates this slot on the result and reads it on the source |
| the live heap (object → its mutable state) | `Store` (`Handle → Payload`) | `obj.dims` ↔ `store (handle obj)`; assigning `obj.dims = v` ↔ `store := Function.update store (handle obj) v` |
| `self.copy()` (`IndexVariable.copy`, `variable.py:2831`) | allocate fresh + copy: `r := nextFresh; store := update store r (store self); nextFresh := nextFresh+1` | `copy()` returns a NEW object (`self is not self.copy()` is always True) whose `dims` equals the source's at call time; later writes to one do not reach the other |
| `return self` (pre-patch) | `return self` (same handle) | identity: source and result are the SAME object; a write through one is seen through the other |

Why `dims` is the right `Payload` witness: `IndexVariable.copy` (`variable.py:2831`)
calls `self._replace(...)`, constructing a brand-new object; `_replace` copies
`dims`. The F2P test exercises precisely the `dims` slot. Modeling the full
object is unnecessary — the discriminating observable is (identity, dims).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reifyIndependent`'s allocation+copy ↔ `IndexVariable.copy` (A-reference)
**Callee:** `IndexVariable.copy(self, deep=True, data=None)` (`variable.py:2831`),
invoked by the post-patch `to_index_variable` as `self.copy()`. The changed
operation is modeled **deeply** by the `do` block's fresh-allocation + slot-copy;
there is **no consumed `copy` axiom**. G-AX validates the deep model against the
real callee by checking the two properties the model encodes:

  - **distinct identity:** `self.copy() is not self` (the model's `res ≠ self`,
    `res = nextFreshOld`);
  - **independence + copied content:** mutating the copy's `dims` does not change
    the source's `dims`, and the copy's `dims` equals the source's at call time
    (the model's `store res = storeOld self`, `store self = storeOld self`, and
    the disjoint-slot frame).

**Soundness check (G-AX):** `axiom_check.py` imports the real `xarray` in-image,
builds `IndexVariable` objects over boundary + fuzzed dim/data shapes, runs the
real `to_index_variable()` / `copy()`, and asserts (a) the result is a distinct
object, (b) it equals the source dims at call time, (c) mutating the result's
`dims` leaves the source's `dims` unchanged. Exit 0 iff every observation meets
the modeled `ensures`. (It also asserts the pre-patch `return self` would VIOLATE
clause (a) — the discriminator's reality.)

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`6938`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the `do` block (fresh-handle allocation + slot copy via a Python
dict store) and diffs the observable (result-identity-distinct, copied-dims,
source-frame-preserved) against `patch.diff`'s behaviour (the real patched
`to_index_variable`) over ≥10⁵ fuzzed `IndexVariable` states.
