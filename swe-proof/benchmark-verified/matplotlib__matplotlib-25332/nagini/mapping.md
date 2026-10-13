# mapping.md — matplotlib__matplotlib-25332

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 66ba515e671638971bd11a34cff12c107a437e0b`, states the type
abstraction, and gives the provenance of the deep model (the real primitives it
is validated against by axiom_check.py / G-AX).

Repo file under change: `lib/matplotlib/cbook.py` (class `Grouper`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `capture_state(ident, weak)` | `Grouper.__getstate__` — ADDED by the patch at `lib/matplotlib/cbook.py:791` (between `__init__` at 788-789 and `__contains__` at 791) | the modeled changed function: capture the container for serialisation by resolving every stored handle to a direct one |
| `restore_state(ident, state_weak)` | `Grouper.__setstate__` — ADDED by the patch (same hunk) | the modeled changed function: restore the container by wrapping every captured direct handle back into an indirect one |
| `roundtrip_weakness(ident, weak)` | the capture-then-restore composition exercised by the pickle round trip in the F2P test (`__getstate__` followed by `__setstate__`) | the modeled observable round-trip behaviour |
| `ident[i]` (read-only `List[int]`) | the integer identity (`id`) of the target the i-th stored handle points at — a `Grouper` member object (an Artist), the referent of `weakref.ref(x)` | the resolved identity of a handle |
| `weak[i]` (`List[int]`, 0/1) | the directness of the i-th stored handle: `1` = indirect (a `weakref.ref`, NOT picklable), `0` = direct (a plain strong reference / dereferenced object, picklable) | the serialisability discriminator |

`Grouper._mapping` (`lib/matplotlib/cbook.py:789`) is a dict whose KEYS are
`weakref.ref(x)` and whose VALUES are lists of `weakref.ref(x)`. Keys and
value-list elements undergo the IDENTICAL per-handle transform under
`__getstate__`/`__setstate__` (`k()` / `weakref.ref(k)` for keys; `v()` /
`weakref.ref(v)` for each value `v`). The model therefore abstracts the whole
mapping to a single flat list of handles (`ident`/`weak`); refinement.md states
this collapse.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `weakref.ref(x)` handle, or a dereferenced strong reference `x` | one slot `(ident[i], weak[i])` of two parallel `List[int]` | `ident[i]` = `id`/identity of the referent `x`; `weak[i] == 1` ↔ the slot holds a `weakref.ref` (indirect); `weak[i] == 0` ↔ the slot holds the strong object (direct) |
| the dict `_mapping` (keys + per-key value-lists, all handles) | the flat list of all handles `(ident, weak)` | keys and value-list elements are the same per-handle transform; flattening loses only the grouping, which `__getstate__`/`__setstate__` preserve verbatim (the dict comprehension structure is unchanged) and which the directness/identity properties do not depend on |
| `__getstate__` returning a dict of STRONG refs | `capture_state` returning the directness flags (all `0`) over the unchanged `ident` | the captured value's distinguishing property is "no weakref survives" = every flag `0`; identity preservation is the immutability of `ident` (a weakref deref `k()` cannot change the referent's identity) |
| `__setstate__` rebuilding a dict of WEAK refs | `restore_state` returning the directness flags (all `1`) over the unchanged `ident` | the restored value's distinguishing property is "every handle is a weakref again" = every flag `1` |

`weakref` objects, dicts-of-weakrefs and `pickle` are inexpressible in Nagini's
fragment; the directness/identity of a handle is the faithful, tested-relevant
projection and is carried by `List[int]`.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**. The changed operation is modeled
**deeply** (the per-slot directness/identity transform spelled out as the two
verified loops). The real primitives the deep model stands for are validated
out-of-band by `axiom_check.py`:

### 3.1 capture (`capture_state` ↔ `__getstate__`)
**Real primitive:** weakref dereference `ref()` and the directness
discriminator. The gold `__getstate__`:
```python
def __getstate__(self):
    return {
        **vars(self),
        "_mapping": {k(): [v() for v in vs] for k, vs in self._mapping.items()},
    }
```
`k()` / `v()` resolve each `weakref.ref` to its referent (a strong, picklable
reference) **without changing the referent's identity** (`weakref.ref(x)() is
x`). The deep-model claim — *every captured handle is direct (flag 0) and
resolves to the same identity* — is checked by `check_capture`: it asserts the
live weakref handle is NOT picklable, the dereferenced handle IS picklable, and
`h() is o`.

### 3.2 restore (`restore_state` ↔ `__setstate__`)
**Real primitive:** `weakref.ref` construction. The gold `__setstate__`:
```python
def __setstate__(self, state):
    vars(self).update(state)
    self._mapping = {weakref.ref(k): [*map(weakref.ref, vs)]
                     for k, vs in self._mapping.items()}
```
`weakref.ref(k)` / `map(weakref.ref, vs)` wrap each strong reference back into a
weakref. The deep-model claim — *every restored handle is indirect (flag 1) and
resolves to the same identity* — is checked by `check_restore`: the restored
handle is NOT picklable and `h() is s`.

### 3.3 round trip (`roundtrip_weakness` ↔ getstate∘setstate)
`weakref.ref(weakref.ref(x)())` resolves to `x`. `check_roundtrip` builds a
Grouper-shaped `{k(): [v()...]}` then `{weakref.ref(k): [weakref.ref(v)...]}`
and asserts the resolved identities of all keys/values are preserved and every
rebuilt handle is indirect.

**Soundness check (G-AX):** `axiom_check.py` runs the real `weakref.ref`, real
weakref dereference, and real `pickle.dumps` on boundary handle sets (empty,
singleton, equal-identity-value duplicates, larger sets) plus 2000 randomized
fuzz sets, asserting every observation matches the deep model. It imports only
the standard library `weakref`/`pickle` — the very primitives the patch uses.
Exit 0 iff sound.

Flag dependency: none. `pickle` is invoked at `pickle.HIGHEST_PROTOCOL` by the
F2P test, but the directness discriminator (weakref unpicklable, strong ref
picklable) holds at every pickle protocol; `axiom_check.py` uses the default
protocol, which exhibits the same TypeError on weakrefs.
