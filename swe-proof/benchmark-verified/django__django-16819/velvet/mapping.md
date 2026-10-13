# mapping.md — django__django-16819

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0b0998dc151feb77068e2387c34cc50ef6b356ae`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each free input.

Repo file under change: `django/db/migrations/operations/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceAddIndex (addedName) (next) (inheritedOutcome)` | `AddIndex.reduce(self, operation, app_label)` — added by the gold patch at `django/db/migrations/operations/models.py:864` (immediately after `AddIndex.migration_name_fragment`, line 861-862) | the modeled changed function: the index-addition's combination rule against the following operation |
| `addedName : List Char` | `self.index.name` — the name of the index this `AddIndex` adds (`models.py:821`, `self.index`; an index without a name is rejected at construction, `models.py:816-820`) | the added index's name |
| `next : NextOp` | the `operation` argument of `reduce` — the operation that immediately follows in the plan | the following operation, projected to only the part the decision consults |
| `inheritedOutcome : Reduction` *(free input)* | `super().reduce(operation, app_label)` — `Operation.reduce` (`django/db/migrations/operations/base.py:129-139`), UNCHANGED by the patch | the ordinary reduction decision for every other pairing |
| `removesAddedIndex` | the guard `isinstance(operation, RemoveIndex) and self.index.name == operation.name` (`models.py:865`, post-patch) | pure spec: does the following operation remove the very index just added? |
| `Reduction` (`cancel` / `inherited tag`) | the return type of `reduce`: a `list` of operations OR a `bool` (`base.py:130-133` docstring) | the reduction outcome carrier (see §2) |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.index.name` (a `str`) and `operation.name` (a `str`) | `List Char` | Python `str` ↔ `s.toList`-shaped `List Char`; string equality `==` ↔ `List Char` `=` (`decide (· = ·)`). Names are short ASCII identifiers; the comparison is over code points. |
| the following `operation` | `NextOp` | `isinstance(operation, RemoveIndex)` with `operation.name == n` ↔ `NextOp.removesIndex n.toList`; **anything else** (not a `RemoveIndex`, or a `RemoveIndex` whose `name` differs — the difference is folded into the `removesIndex` payload not matching `addedName`) ↔ `NextOp.other` is NOT used for the name-mismatch case: a `RemoveIndex` with a *different* name is still `NextOp.removesIndex name` with `name ≠ addedName`, and `removesAddedIndex` returns `false` for it. `NextOp.other` covers only non-`RemoveIndex` operations. |
| `reduce`'s return value: `[]` (empty list) | `Reduction.cancel` | the two operations annihilate; the plan keeps nothing in their place. `[]` is the ONLY value the patch's new branch returns. |
| `reduce`'s return value: anything `super().reduce` returns — `[operation]`, `[self]`, `True`, or `False` (`base.py:135-139`) | `Reduction.inherited tag` | the ordinary inherited decision. Its concrete shape is irrelevant to the modeled change (it is UNCHANGED); abstracted as the opaque `inherited tag` so the spec makes no claim about it. The `tag : Nat` keeps the non-cancel outcomes an open domain — distinct inherited results stay distinguishable from each other and, crucially, from `cancel`. |

`isinstance(operation, RemoveIndex)` is a type test on the unchanged
`RemoveIndex` class (`models.py:865`); `operation.name` is `RemoveIndex.name`
(`models.py:869`). Both are pre-existing, unchanged repo facts.

## 3. Callee provenance

There are **no axiomatized callees and no A-references** in this bundle. The only
callee the changed function invokes that it does not itself implement is
`super().reduce(operation, app_label)` (`Operation.reduce`,
`base.py:129-139`) — which the patch does **not** change. Its decision is
abstracted as the free input `inheritedOutcome`: the spec relies on **no**
property of it (it holds for every value `inheritedOutcome` may take), so there
is nothing to validate against a real callee, hence **no G-AX** (axiom_check.py
is omitted; `meta.json gates.G-AX.status = "skip"`).

The pre-existing classes the guard names — `RemoveIndex` (`models.py:865`) and
its `.name` attribute (`models.py:869`) — are unchanged by the patch and are
modeled structurally by the `NextOp` carrier (§2); they carry no relied-on
behaviour beyond the `isinstance` + name-equality test the guard performs.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16819`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `removesAddedIndex` and the `if … then cancel else
inheritedOutcome` decision to Python and runs them against the **real** patched
`AddIndex.reduce` (imported from the repo at base_commit with `patch.diff`
applied). The free input `inheritedOutcome` is bound on the oracle side to the
real `super().reduce(...)` outcome and on the shadow side to the same observed
value, so the differential isolates the new branch (the only thing the patch
adds).
