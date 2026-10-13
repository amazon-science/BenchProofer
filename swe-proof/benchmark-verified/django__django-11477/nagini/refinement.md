# refinement.md — django__django-11477

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_captures` impl region and the deep `kept_keys`/`kept_vals` folds) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `RegexPattern.match` (`django/urls/resolvers.py:156`)

Gold hunk:
```
- kwargs = match.groupdict()
+ kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
  args = () if kwargs else match.groups()
  return path[match.end():], args, kwargs
```

| # | model.py impl op (`select_captures`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `keys: List[int]`, `vals: List[int]` (parallel) | `match.groupdict()` — `Dict[str, Optional[str]]` | R | a dict of `name -> value-or-None` ↔ two parallel `List[int]`; `value is None` ↔ `vals[i] == absent()` (mapping.md §2). |
| A2 | parameter `positional: List[int]` | `match.groups()` — the positional-capture tuple | R | tuple ↔ `List`, same order (mapping.md §2). |
| A3 | retain the entries with `vals[i] != absent()` (the loop guard `if v != absent()`), producing `(kept_keys(ToSeq(keys),ToSeq(vals)), kept_vals(...))` | `{k: v for k, v in match.groupdict().items() if v is not None}` | A-reference | the changed dict-comprehension filter is modelled **deeply**: `kept_keys`/`kept_vals` (the spelled-out front-recursive folds in the `pure` region) and the verified loop in `select_captures` ARE the retention. There is no consumed filter axiom — the proof never depends on one. The deep model is validated **== the real operation** out-of-band: G-AX (axiom_check.py) runs the real post-patch comprehension over an `re` match and asserts it equals the deep model. `v is not None` ↔ `v != absent()` because `None` ↔ `absent()` (R, mapping.md §2). |
| A4 | `args` chosen by `if len(r_keys) == 0` (positional copied iff the retained mapping is empty) | `args = () if kwargs else match.groups()` | A-reference + I | the truthiness of the (now-filtered) `kwargs` dict is `len(kwargs) != 0`; `() if kwargs else groups()` ↔ `[] if len(r_keys)!=0 else positional`. The selection reads the **filtered** mapping (post-patch), which is the behavioural shift the F2P `regex_optional`/`named_optional_terminated` paths observe (mapping.md §3.1). |
| A5 | (no node) | `path[match.end():]` returned as the path tail | — | the path tail is an unchanged carry-through, identical pre- and post-patch and independent of the change; it is omitted from the model (mapping.md §2). Not a refinement step of the changed behaviour. |

The discriminating content of the change — optional named groups that did NOT
participate (`v is None`) are DROPPED from `kwargs` rather than carried with a
`None` value — lives in the loop guard `if v != absent()` (model) ⇔ the
`if v is not None` filter (real). The pre-patch `kwargs = match.groupdict()`
kept them all; `model_prepatch.py` reproduces that (the unfiltered copy loop,
`ToSeq(r_keys) == ToSeq(keys)`) and **fails** the postcondition
`ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals))`, which is exactly the
spec sensing the change (G-DIFF). It also violates the
`Result()[1][i] != absent()` clause (the prepatch leaks the `None` sentinel into
the reported values) and, when the only named group is a non-participating
optional, the `args` clause (prepatch reports `args=()` because the unfiltered
dict is truthy; spec demands the positional captures because the retained
mapping is empty).

## B. No consumed axioms

There is no `@ContractOnly` in `model.py`. The named-group retention filter and
the keyword/positional choice are the behaviour under specification and are
modelled **deeply**; the only operations the patched code composes are an
absence test (`is not None`), dict comprehension, and tuple/dict construction —
ordinary operations whose real Python `re`/`dict` semantics are validated against
the deep model out-of-band by G-AX (the **A-reference**, §A row A3/A4). Nothing
is axiomatized; there is no dead axiom and nothing to over-claim.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the `None`-dropping filter on the named-group mapping and the
selection it feeds — is modelled **deeply** (the spelled-out front-recursive
folds `kept_keys`/`kept_vals` consumed in `select_captures`, an **A-reference**),
not hidden behind an axiom about the function under change. There is no consumed
axiom of any kind.

## D. verify(model) ⇒ resolved

`select_captures` verifies only if its retained keyword mapping equals the exact
`None`-dropping filter of `groupdict()` (A3: `kept_keys`/`kept_vals`), only if no
absence sentinel survives into the reported values, and only if the positional
report is chosen against that *filtered* mapping (A4). By R (dict ↔ parallel
lists, `None` ↔ `absent()`, tuple ↔ list) the verified function equals the
post-patch `RegexPattern.match` body on the tested inputs; by G-AX the deep model
`kept_keys`/`kept_vals` + the selection equal the real post-patch comprehension
(A-reference) over boundary + fuzz `re` matches. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited reference — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
