# mapping.md — django__django-15569

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 884b4c27f506b3c29d58509fc83a35c30ea10d94`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each modeled callee.

Repo file under change: `django/db/models/query_utils.py`. The gold patch adds
one line to `RegisterLookupMixin._unregister_lookup`: after the owned-binding
store is mutated (a name is removed), it re-syncs a derived, cached read-through
view of that store.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `removeBinding` (the modeled `method`) | `RegisterLookupMixin._unregister_lookup(cls, lookup, lookup_name=None)` — `django/db/models/query_utils.py:212` | the modeled changed function |
| `registry : List (String × Nat)` *(mut)* | `cls.class_lookups` — the per-class owned-binding dict (`query_utils.py:207` writes it; `_unregister_lookup` deletes from it at `:219`) | the owned-binding store the operation mutates |
| `cached : List (String × Nat)` *(mut)* | the memoized return of `cls.get_lookups()` (the `functools.lru_cache(maxsize=None)`-wrapped classmethod, `query_utils.py:158-163`); cleared per-subclass by `_clear_cached_lookups` (`:197-200`) | the derived, cached read-through view callers consult |
| `inherited : List (String × Nat)` | the merged bindings contributed by the parent classes in `inspect.getmro(cls)` (every `parent.__dict__['class_lookups']` other than `cls`'s own), as combined by `get_lookups`/`merge_dicts` (`:159-163`, `:185-194`) | the bindings the view exposes underneath the registry's own (read-only here) |
| `name : String` | `lookup_name` (defaulted to `lookup.lookup_name` when `None`, `query_utils.py:217-218`) | the key removed from the store |
| `eraseKey registry name` *(concrete — I)* | `del cls.class_lookups[lookup_name]` (`query_utils.py:219`) | drops the one binding for `name` from the store |
| `recomputeLookups inherited registry` *(deep model — A-reference)* | the value `cls.get_lookups()` recomputes from the now-current `class_lookups` after the cache is cleared: `merge_dicts([parent.__dict__.get('class_lookups', {}) for parent in inspect.getmro(cls)])` (`get_lookups` body, `:159-163`; `merge_dicts`, `:185-194`) | pure spec: the re-derived view; deep model of the unchanged read-through derivation, validated `recomputeLookups == get_lookups()` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `lookupKey`, `hasKey` | (helpers) association-list lookup / membership used to express the overlay and the `require`; no standalone repo symbol | pure helpers for the overlay + precondition |

The gold patch's added line is `cls._clear_cached_lookups()`. In the real code,
`get_lookups` is an `lru_cache`'d classmethod: clearing its cache makes the NEXT
`get_lookups()` recompute the view from the current `class_lookups`. The spec
models the observable net effect — the cached view, after the operation, equals
the view re-derived from the updated registry — as the second `ensures` (rather
than modeling the `lru_cache` machinery). `_clear_cached_lookups` itself iterates
`subclasses(cls)` calling `get_lookups.cache_clear()`; it is unchanged
cache-invalidation plumbing whose only observable effect is that the subsequent
view consultation recomputes (refinement.md §B). `register_lookup` (`:202`) is
the sibling that already does this clear after an insert; `_unregister_lookup`
was simply missing the symmetric clear after a delete.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) and G-AX use to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `dict[str, <lookup class>]` (`class_lookups`; `get_lookups()`'s return; the per-parent `class_lookups`) | `List (String × Nat)` | a Python dict `d` ↔ a `List (String × Nat)` whose pairs are `d.items()` with **unique keys**; equality is **as a key→value mapping** (order-insensitive, since real dicts have unique keys). The *value* is the bound lookup/transform class; G-CONF/G-AX abstract each distinct class to a stable `Nat` id (`Char.ord`-style surrogate — only value *identity*, never the class internals, is observable here), since the operation never inspects values, only adds/removes/exposes keys. `recomputeLookups` lists `registry` first so that, read as "first binding wins", the registry's own bindings shadow the inherited ones — exactly `merge_dicts([*inherited_parents, own])`'s reverse-merge (own wins). |
| a lookup name (Python `str` dict key, e.g. `"exactly"`, `"my_transform"`) | `String` | identity on the character content |
| `lookup_name is None` defaulting to `lookup.lookup_name` | (resolved before the modeled op) | the modeled `method` takes the already-resolved `name : String`; the `if lookup_name is None` defaulting (`:217-218`) is a pure argument-resolution step with no observable effect on the store/view and is not modeled (refinement.md §A, R). |

The `lookup` object argument, `cls`, and `**`-style extras carry no observable
content for the store/view mutation beyond `name`; they are not modeled.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `recomputeLookups` deep model ↔ `get_lookups()` (A-reference)
**Callee:** `RegisterLookupMixin.get_lookups` (`query_utils.py:158-163`,
unchanged by the patch) together with `merge_dicts` (`:185-194`). Body at
`base_commit`:

```python
@classmethod
@functools.lru_cache(maxsize=None)
def get_lookups(cls):
    class_lookups = [
        parent.__dict__.get("class_lookups", {}) for parent in inspect.getmro(cls)
    ]
    return cls.merge_dicts(class_lookups)

@staticmethod
def merge_dicts(dicts):
    merged = {}
    for d in reversed(dicts):
        merged.update(d)
    return merged
```

`inspect.getmro(cls)` lists `cls` first, then its ancestors. `merge_dicts`
iterates in **reverse** and `update`s, so the most-derived class's
`class_lookups` (the owned store, `cls.__dict__['class_lookups']`) is applied
**last** and therefore **wins** on shared keys. As a key→value mapping the
result is exactly "the inherited parents' bindings, overlaid by the owned
registry (owned wins)". The recompute is modeled **deeply** by `recomputeLookups`
(with `lookupKey`) in the `pure` region — `registry ++ inherited.filter (key not
in registry)` — which as a mapping is exactly that overlay. There is **no
consumed axiom** about it; G-AX validates the deep model against the real callee.

**Soundness check (G-AX):** `axiom_check.py` builds a real `RegisterLookupMixin`
subclass hierarchy (a parent contributing `inherited` bindings and a child whose
`class_lookups` is the `registry`), populates `class_lookups` from boundary +
fuzzed key/value sets (empty registry; single owned key; owned key shadowing an
inherited key — the collision case; keys present only inherited; the F2P shape
where the registered name is then removed), clears the cache, calls the **real**
`get_lookups()`, and asserts `dict(recomputeLookups(inherited, registry)) ==
get_lookups()` as a mapping. ≥10⁵ fuzzed configurations. Imports only `django.*`
already present in the instance image. Exit 0 iff sound.

### 3.2 Cache-invalidation plumbing ↔ `_clear_cached_lookups` (A-reference, plumbing)
**Callee:** `RegisterLookupMixin._clear_cached_lookups` (`:197-200`) and
`functools.lru_cache` / `get_lookups.cache_clear()`. Unchanged plumbing. Not
modeled as a separate computation (its only effect is that the next
`get_lookups()` recomputes); its observable consequence — the cached view equals
the re-derived view after the operation — is the second `ensures` of the modeled
`method`, exercised end-to-end by the F2P tests under G-RESOLVE (without the
clear, `field.get_lookups()` still exposes the removed name and the F2P
`assertNotIn` / `get_transform` assertions fail). No consumed axiom.
(refinement.md §B.)

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed their `random.Random` with
**`15569`** so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
`conformance_check.py` builds transliterates the store mutation `eraseKey`
(I-tagged) to a Python dict delete and bridges I/O via this table; for the
recompute it runs the **real** `get_lookups()` (the A-reference → real callee,
not the deep model). The deep model itself is validated separately by
`axiom_check.py` (G-AX).
