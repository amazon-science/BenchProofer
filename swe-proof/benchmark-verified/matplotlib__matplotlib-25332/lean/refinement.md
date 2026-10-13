# refinement.md — matplotlib__matplotlib-25332

Maps every operation in `implementation_serialize` / `implementation_deserialize`
to its `patch.diff` counterpart in `Grouper.__getstate__` / `Grouper.__setstate__`
(`lib/matplotlib/cbook.py`). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** deep-modeled changed op validated == real
callee, **I** identical concrete op.

## Patch (post-patch, added to `Grouper`)
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
`Grouper` carries no instance state other than `_mapping` (`__init__` sets only
`self._mapping`), so `{**vars(self), "_mapping": ...}` is exactly the deref'd
mapping, and `vars(self).update(state)` followed by rebuilding `_mapping` is
exactly re-wrapping the deref'd mapping. The modeled values are therefore the two
transforms on the partition table: deref-on-serialize and rewrap-on-deserialize.

## Operation correspondence — `serialize` ↔ `__getstate__`
| # | Lean op (`implementation_serialize`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut acc := []` | start building the new `_mapping` dict | I | accumulator for the serialized table. |
| 2 | `for kv in m do` | `for k, vs in self._mapping.items()` | R | the partition table `dict[ref, list[ref]]` ↔ `List (Ref × List Ref)`; key order irrelevant (G-CONF compares as a map). |
| 3 | `let key := kv.1; … (key.val …)` | `k()` (deref the key) | R | `weakref.ref` deref `k()` ↔ `Ref.val` — both yield the referent (identity token). |
| 4 | `for v in members do derefMembers := derefMembers ++ [v.val]` | `[v() for v in vs]` (deref each member) | R | per-member deref `v()` ↔ `Ref.val`; list comprehension ↔ accumulator `for` (`List.map`). |
| 5 | `acc := acc ++ [(key.val, derefMembers)]` | `k(): [v() for v in vs]` entry | I | one deref'd entry appended. |
| 6 | `return Except.ok acc` | the method RETURNS the state (does not raise) | R | success ↔ `Except.ok`; the central fix is that serialization now produces a value instead of failing. The pre-patch arm raises `TypeError` ↔ `Except.error` (prepatch). |

## Operation correspondence — `deserialize` ↔ `__setstate__`
| # | Lean op (`implementation_deserialize`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 7 | `let mut acc := []` | the rebuilt `self._mapping` dict | I | accumulator for the reconstructed table. |
| 8 | `for kv in s do` | `for k, vs in self._mapping.items()` (over the strong state) | R | state `dict[obj, list[obj]]` ↔ `List (Int × List Int)`. (`vars(self).update(state)` installs the strong mapping first; modeled as iterating the state directly.) |
| 9 | `for v in members do wrapMembers := wrapMembers ++ [Ref.mk v]` | `[*map(weakref.ref, vs)]` (re-wrap members) | R | `weakref.ref(v)` ↔ `Ref.mk` — wrap referent in a fresh reference. |
| 10 | `acc := acc ++ [(Ref.mk kv.1, wrapMembers)]` | `weakref.ref(k): [...]` entry | I | one re-wrapped entry. |
| 11 | `return acc` | assign to `self._mapping` | I | the reconstructed table. |

Every op is R or I; **no A row** — `weakref.ref` deref/construction is modeled
deeply as the `Ref` structure (`.val` / `Ref.mk`), not an axiomatized unchanged
callee. Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
Both impls are all R/I, so `conformance_check.py` mechanically differential-tests
the impl shadows (deref-table / rewrap-table, and the round-trip identity)
against `patch.diff` behavior over ≥10^5 fuzzed partition tables.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, `Grouper` has NO `__getstate__`. Python's default pickling then tries
to serialize `__dict__` directly, which contains `weakref.ref` objects —
unserializable — so `pickle.dumps(fig)` raises
`TypeError: cannot pickle 'weakref.ReferenceType' object` (exactly the issue).
The prepatch impl (`implementation_serialize := return Except.error …`) models
this failure: serialization produces no value. It cannot satisfy
`problem_spec_serialize` (which demands `Except.ok (toStrong m)`) on ANY input,
so `correct_serialize` is unprovable; the carried gold proof fails to typecheck
against the buggy impl (G-DIFF). This is the single independently-observable
fixed behavior — the FAIL_TO_PASS test `test_pickle.py::test_complete[png]` (with
the added `align_ylabels()` populating the `_align_label_groups` Groupers) fails
pre-patch precisely because the figure can no longer be pickled.
`deserialize` is the round-trip counterpart that makes the recovered figure
equivalent; it is not independently observable pre-patch (no state is ever
produced to restore), so one prepatch variant suffices.
