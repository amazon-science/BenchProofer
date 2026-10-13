# refinement.md — psf__requests-1921

The operation-by-operation correspondence between `model.py`'s implementation
(the `effective_collection` impl region together with the deep `effective` / `combined`
model in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real operation by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The merge-and-drop site — `merge_setting` (`requests/sessions.py:34`)

Gold hunk (dict-merge branch):
```
      for (k, v) in request_setting.items():
          if v is None:
              del merged_setting[k]
+
+     merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)
+
      return merged_setting
```

| # | model.py impl op (`effective_collection` / `pure`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `session, request: List[int]` over key positions `0..n-1` | `session_setting`, `request_setting` dicts (Mapping branch) | R | dict ↔ `List[int]` indexed by key position; "key absent" ↔ value `absent()` (mapping.md §2). Read-only inputs at `Acc(list_pred(·), 1/2)` (directive 5). |
| A2 | `effective(sv, rv) = rv if rv != absent() else sv` (the `if rv != absent(): ev = rv else ev = sv` loop branch) | `merged_setting = dict_class(to_key_val_list(session_setting)); merged_setting.update(to_key_val_list(request_setting))` (`sessions.py:54-55`) | R | building merged from `session` then `.update(request)` makes the per-request value win on shared keys; absence on one side ↔ `absent()` there. `to_key_val_list` / `OrderedDict.update` are representation/order-only on the per-key value mapping (mapping.md §2; G-AX drives the real callees). |
| A3 | `combined(sv, rv) = absent() if effective(sv, rv) == none_val() else effective(sv, rv)` (the `if ev == none_val(): val = absent() else val = ev` loop branch, building `result` element-wise) | the patched `merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)` (`sessions.py:62`, post-patch) — drop EVERY key whose merged value is `None` | A-reference | the changed combine-and-drop operation is modelled **deeply**: `effective`/`combined` (spelled out in the `pure` region) and the verified loop in `effective_collection` ARE the precedence merge plus the all-sides None-drop. There is no consumed `@ContractOnly` axiom — the proof depends on none. The deep model is validated **== the real operation** out-of-band: G-AX (axiom_check.py) drives the real `merge_setting` machinery (`to_key_val_list`, `OrderedDict.update`, the gold drop) and asserts `combined == real merge_setting` per key, and that a session-side `None` is dropped exactly when the gold drop runs (mapping.md §3.1). |
| A4 | `result` returned (a `List[int]`, no position holding `none_val()`) | `return merged_setting` (no key mapping to `None`) | R | dict ↔ `List[int]`; a position holding `absent()` ↔ the key absent from the returned dict; a position holding a real value ↔ that key present with that value. The F2P test observes only `'Accept-Encoding' not in prep.headers`, i.e. that the dropped key is absent. |

The discriminating content of the change — drop a key whose effective value is
`None` **regardless of which side contributed it** (not only the per-request
side) — lives in `combined` keying off `effective(sv, rv)` (the post-merge
value) rather than off `rv` (the per-request value). The pre-patch repo dropped
only keys whose `request_setting` value was `None`; `model_prepatch.py`
reproduces that (the loop branch keys off `rv == none_val()` instead of
`ev == none_val()`) and **fails** the loop invariant
`result[k] == combined(session[k], request[k])` — which propagates to
postcondition (1) (faithful per-key value) and postcondition (2)
(`Result()[k] != none_val()`). That is exactly the spec sensing the change
(G-DIFF): on the key with `rv == absent()` and `sv == none_val()` the buggy
skeleton produces `none_val()` whereas `combined` requires `absent()`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely *changed*
— the drop of every key whose effective value is `None` — is modelled **deeply**
(the spelled-out per-key `combined` consumed by the verified loop, step A3, an
**A-reference**), not hidden behind an axiom about the function under change:
there is no consumed axiom. The only out-of-band trust point is the A-reference
G-AX validates (`combined` == the real merge-and-drop), which exercises the real
unchanged callees `to_key_val_list` / `OrderedDict.update` together with the
gold drop line.

## C. verify(model) ⇒ resolved

`effective_collection` verifies only if its output equals, per key, the precedence
merge with every `None`-valued key dropped (A3) — in particular no result
position holds `none_val()` (postcondition (2)). By R (dict ↔ `List[int]` over
key positions; `absent()` ↔ key-absent; the per-request-wins update; the
order/representation-only `to_key_val_list`) the verified result equals
`merge_setting(request_setting, session_setting)` post-gold on the tested
inputs; by G-AX the deep model `combined` equals the real merge-and-drop
operation (the A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited
A-reference — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
