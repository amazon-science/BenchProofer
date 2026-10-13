# mapping.md — django__django-15569

## Instance
- `base_commit`: 884b4c27f506b3c29d58509fc83a35c30ea10d94
- Changed file: `django/db/models/query_utils.py`
- Changed function: `RegisterLookupMixin._unregister_lookup` (classmethod), lines 211–219 @ base_commit.

## Behavior under spec
`RegisterLookupMixin` maintains, per class:
- `class_lookups : dict[str, lookup]` — the registered lookups for the class
  (`query_utils.py:160`, set in `register_lookup`, `query_utils.py:207`).
- a *memoized* `get_lookups()` (`@functools.lru_cache`, `query_utils.py:157-163`)
  whose result is the merged lookup map; reads go through `_get_lookup` →
  `get_lookups()` (`query_utils.py:154-155`).

`register_lookup` mutates `class_lookups` and then calls `_clear_cached_lookups()`
(`query_utils.py:208`) to invalidate the memo. `_unregister_lookup`
(`query_utils.py:211-219`) deletes the entry from `class_lookups` via
`del cls.class_lookups[lookup_name]` but — pre-fix — did NOT invalidate the memo,
so a stale `get_lookups()` keeps returning the removed lookup. The fix adds the
same `cls._clear_cached_lookups()` call after the `del`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean |
|---|---|
| the per-class `class_lookups: dict[str, lookup]` | `LookupState.classLookups : List (String × Nat)` (assoc list; lookup class identity abstracted to a `Nat` id) |
| the memoized `get_lookups()` value (a dict, or "not yet computed") | `LookupState.cache : Option (List (String × Nat))` (`none` ⇔ lru-cache empty / cleared) |
| `lookup_name : str` | `lookupName : String` |
| `del cls.class_lookups[lookup_name]` | `eraseKey classLookups lookupName` (drop all pairs whose key = `lookupName`) |
| `cls._clear_cached_lookups()` (busts the memo) | `cache := none` |
| `cls.get_lookups()` (read through the memo) | `getLookups s = s.cache.getD s.classLookups` |

Notes / scope of the model:
- The real `_clear_cached_lookups` walks `subclasses(cls)` and calls
  `get_lookups.cache_clear()` on each. The observable behavior that the issue +
  F2P tests pin is single-class: after unregistering, `field.get_lookups()` must
  no longer contain the removed name. The multi-subclass walk is an
  implementation detail of cache invalidation; the bijection models the memo of
  the class under test as one `Option` slot. (A-reference-free: no callee is
  consumed as an axiom.)
- `merge_dicts` over the MRO degenerates to the class's own `class_lookups` for a
  single class with no parent lookups; `getLookups` recompute = `classLookups`.

## Callee provenance
None consumed as an axiom. `_clear_cached_lookups` is the operation the patch
*adds the call to*; its effect (memo invalidation) is modeled DEEPLY as
`cache := none`, so it is neither an A-consumed nor an A-reference callee.
`del` / dict membership are modeled deeply via `eraseKey`.

## G-CONF fuzz seed
seed = 15569 (pinned).
