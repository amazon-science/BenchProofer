# mapping.md — matplotlib__matplotlib-25332

## Symbol binding (file:line @ base_commit)
Modeled object: the disjoint-set/grouping container `Grouper` in
`lib/matplotlib/cbook.py:753-855` (@ base_commit). Internally it stores its
partition as `self._mapping : dict[weakref.ref, list[weakref.ref]]`
(constructed at `cbook.py:788` `__init__`). The gold patch adds two methods to
this class (inserted after `__init__`, `cbook.py:790-803` post-patch):

```python
def __getstate__(self):
    return {
        **vars(self),
        # Convert weak refs to strong ones.
        "_mapping": {k(): [v() for v in vs] for k, vs in self._mapping.items()},
    }

def __setstate__(self, state):
    vars(self).update(state)
    # Convert strong refs to weak ones.
    self._mapping = {weakref.ref(k): [*map(weakref.ref, vs)]
                     for k, vs in self._mapping.items()}
```

The bug (problem_statement): the container holds weak references, which are not
serializable, so serializing any figure that contains such a container raises
`TypeError: cannot pickle 'weakref.ReferenceType' object`. The fix makes
serialization (a) succeed and (b) round-trip: the serialized form holds the
*referents directly* (strong), and reconstruction re-wraps them as references so
the partition is restored unchanged.

Lean modeled functions (deliberately neutral names — they name the *behavior*,
not the patched method names):
- `serialize`   ↔ `Grouper.__getstate__` (`cbook.py:790-795` post-patch)
- `deserialize` ↔ `Grouper.__setstate__` (`cbook.py:797-803` post-patch)

| Lean symbol | Python binding (file:line @ base / post-patch) |
|---|---|
| `Ref` (`structure` wrapping `val : Int`) | `weakref.ref(x)` — a weak reference to object `x`; equality/identity is by referent (`weakref.ref(x) == weakref.ref(x)`), modeled by structural equality on the identity token `val`. `r.val` ↔ `r()` (deref). |
| `m : List (Ref × List Ref)` | `self._mapping : dict[weakref.ref, list[weakref.ref]]` — the partition: each key maps to the list of members of its set. `cbook.py:788` |
| `toStrong m` | `{k(): [v() for v in vs] for k, vs in self._mapping.items()}` — deref every key and member, `cbook.py:794` |
| `serialize` → `Except String (List (Int × List Int))` | `__getstate__` returns the serializable state (`Except.ok`); pre-patch (no method) serialization raises (`Except.error`). The other `vars(self)` are empty for `Grouper` (only `_mapping`), so the state IS the deref'd mapping. |
| `toWeak s` | `{weakref.ref(k): [*map(weakref.ref, vs)] for k, vs in state.items()}` — re-wrap, `cbook.py:802-803` |
| `deserialize` → `List (Ref × List Ref)` | `__setstate__` rebuilds `self._mapping` from the strong-ref state |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| object identity (`id(x)`) of a grouped object | `Int` identity token |
| `weakref.ref(x)` (key/member; deref `r()` = referent; eq by referent) | `Ref` with `val : Int`; `r.val` = deref; `DecidableEq` = referent eq |
| `self._mapping : dict[weakref.ref, list[weakref.ref]]` | `List (Ref × List Ref)` (assoc list; key order irrelevant — G-CONF compares as a key→memberset map) |
| serialized state `{"_mapping": {obj: [obj,...]}}` (strong) | `List (Int × List Int)` |
| `__getstate__` succeeds / pre-patch pickling raises `TypeError` | `Except.ok state` / `Except.error msg` |
| `__setstate__` result `self._mapping` | `List (Ref × List Ref)` |

### Modeling notes
- `Grouper` carries no instance state other than `_mapping` (its `__init__`
  sets only `self._mapping`), so `{**vars(self), "_mapping": ...}` reduces to the
  deref'd mapping; modeling the state as exactly the deref'd mapping is faithful.
- `weakref.ref` deref/construction is a language builtin modeled DEEPLY as the
  `Ref` structure (`.val` / `Ref.mk`), not an axiomatized repo callee — hence no
  consumed axiom and no A-reference (G-AX is a skip stub).
- `clean()` / dead-reference handling is out of scope: serialization happens on a
  live object graph, so every key/member dereferences to a live referent.
- Identity *sharing* of the Python list objects (several keys pointing at the
  same `list`) is an in-memory optimization the round-trip does not preserve and
  that does not affect the logical partition (`joined`/`get_siblings` read by
  equality); the model uses independent per-key member lists.

## Callee provenance + flag deps
No unchanged repo callee is consumed as an axiom and no deep-model reference of
an unchanged repo callee exists. `weakref.ref`/deref are modeled deeply as
`Ref`. Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub. No flag dependency.

## G-LEAK
Public terms in `problem_statement`: `pickle`, `weakref`, `align_labels`. NOT
public: `Grouper`, `__getstate__`, `__setstate__`, `_mapping`, "disjoint set",
"union-find". The spec view uses only neutral behavioral vocabulary
("serialize", "reference", "grouping", "round-trip") and the modeled-function
identifiers `serialize`/`deserialize` share no patched method/class name as a
substring. Comments describe the abstract desired behavior (serialization must
succeed and round-trip), never the edit (no mention of added methods).

## Pinned G-CONF fuzz seed
`25332`.
